"""Deal-package ingest (SPEC §3): deal.yaml, GL, chart of accounts, monthly P&L,
management's adjusted-EBITDA schedule, and the document set.

``load_deal`` is the pipeline's single entry point. It never opens
``ground_truth.json``: that file is the answer key and only ``qoe/evaluate.py``
reads it. Every file ingest does read is hashed into ``input_hashes`` so a
workpaper can prove which inputs produced it.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Optional

import yaml

from qoe.gl_formats import (
    FALLBACK_BASIS,
    GL_FORMATS,
    QBO,
    AccountIndex,
    Row,
    classify_account,
    clean_text,
    detect_format,
    is_blank,
    is_credit_natural,
    norm_key,
    parse_money,
    parse_month,
    read_chart_of_accounts,
    read_gl,
    read_table,
    split_account_label,
)
from qoe.money import D, fmt
from qoe.pdf_text import canonicalize_page_text, extract_pdf_pages
from qoe.periods import month_range
from qoe.schemas import (
    Account,
    AdjustmentCategory,
    AdjustmentClaim,
    DealMeta,
    DealPackage,
    DocumentPage,
    EbitdaClass,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PLAccountLine,
    SourceDocument,
)

GROUND_TRUTH_FILENAME = "ground_truth.json"
DEAL_YAML = "deal.yaml"
DEFAULT_OVERRIDES_NAME = "account_mapping_overrides.csv"
DOCUMENT_TYPES = {".pdf": "pdf", ".txt": "txt", ".md": "md", ".eml": "eml"}
# Data-room PDFs can be large scans; anything past this is not a reviewable document and
# would only slow ingestion (text extraction and HTML stripping run over the whole file).
MAX_DOCUMENT_BYTES = 100 * 1024 * 1024

_MONTH = re.compile(r"^\d{4}-\d{2}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relpath(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return Path(os.path.relpath(path, base)).as_posix()


# ---------------------------------------------------------------------------
# deal.yaml
# ---------------------------------------------------------------------------


def _norm_month(value: object, field: str) -> str:
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}"
    text = clean_text(value)
    m = re.match(r"^(\d{4})-(\d{1,2})(?:-\d{1,2})?$", text)
    if not m:
        raise ValueError(f"deal.yaml: {field} must be a YYYY-MM month, got {value!r}")
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"


def _parse_deal_meta(path: Path) -> tuple[DealMeta, list[str]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name}: expected a mapping at the top level")
    notes: list[str] = []
    known = set(DealMeta.model_fields)
    extra = sorted(k for k in raw if k not in known)
    if extra:
        notes.append(f"deal.yaml: ignored unknown keys {extra}")
    data = {k: v for k, v in raw.items() if k in known}
    for key in ("deal_id", "target_name", "industry", "currency", "gl_format"):
        if key in data and data[key] is not None:
            data[key] = str(data[key]).strip()
    if "tolerance" in data:
        data["tolerance"] = fmt(data["tolerance"])
    for key in ("data_start", "data_end"):
        if key in data:
            data[key] = _norm_month(data[key], key)
    periods = []
    for p in data.get("periods") or []:
        if not isinstance(p, dict):
            raise ValueError(f"deal.yaml: each period needs label/start/end, got {p!r}")
        periods.append(
            {
                "label": clean_text(p.get("label")),
                "start": _norm_month(p.get("start"), f"period {p.get('label')!r} start"),
                "end": _norm_month(p.get("end"), f"period {p.get('label')!r} end"),
            }
        )
    data["periods"] = periods
    files = data.get("files")
    if isinstance(files, dict):
        allowed = {"gl", "chart_of_accounts", "monthly_pl", "adjustments", "documents_dir", "account_mapping_overrides"}
        dropped = sorted(k for k in files if k not in allowed)
        if dropped:
            notes.append(f"deal.yaml: ignored unknown files keys {dropped}")
        data["files"] = {k: str(v) for k, v in files.items() if k in allowed and v is not None}
    meta = DealMeta.model_validate(data)
    # deal_id names the workpaper folder, so it must be a single safe path segment.
    if not meta.deal_id or meta.deal_id in (".", "..") or re.search(r"[/\\\x00]", meta.deal_id) or meta.deal_id != meta.deal_id.strip():
        raise ValueError(f"deal.yaml: deal_id must be a plain name without path separators, got {meta.deal_id!r}")

    labels = [p.label for p in meta.periods]
    if not labels:
        raise ValueError("deal.yaml: at least one analysis period is required")
    if len(set(norm_key(x) for x in labels)) != len(labels):
        raise ValueError(f"deal.yaml: period labels must be unique, got {labels}")
    for p in meta.periods:
        if p.start > p.end:
            raise ValueError(f"deal.yaml: period {p.label} starts after it ends")
    if meta.data_start > meta.data_end:
        raise ValueError("deal.yaml: data_start is after data_end")
    if meta.gl_format != "auto" and meta.gl_format not in GL_FORMATS:
        raise ValueError(f"deal.yaml: gl_format must be 'auto' or one of {GL_FORMATS}, got {meta.gl_format!r}")
    return meta, notes


def read_deal_meta(path: Path) -> DealMeta:
    """Parse deal.yaml into ``DealMeta`` (months normalized, unknown keys ignored)."""
    return _parse_deal_meta(Path(path))[0]


# ---------------------------------------------------------------------------
# Monthly P&L
# ---------------------------------------------------------------------------

_PL_SUBTOTAL = re.compile(
    r"^\s*(total\b|gross (profit|margin)\b|net (operating|ordinary|other) income\b|net income\b|net (profit|loss)\b)",
    re.I,
)
_PL_TOTAL_OF = re.compile(r"^\s*total\s+(?:for\s+)?(.+?)\s*$", re.I)
# Headings that name a P&L class. They start a new top-level section and set its sign.
# Any other heading ("Maintenance Agreements", "Payroll Expenses", "Sales & Marketing")
# groups accounts inside the current section and inherits its sign.
_CLASS_HEADING = re.compile(
    r"^(?:less|plus|add|deduct)?\s*:?\s*"
    r"(?:"
    r"(?:ordinary|other|operating|non[\s-]?operating|trading)?\s*(?:income|revenues?|sales|turnover)"
    r"|(?:net|gross)\s+(?:sales|revenues?)"
    r"|cost\s+of\s+(?:goods\s+sold|sales|revenues?|services|goods)|cogs|direct\s+(?:costs?|expenses?)"
    r"|(?:operating|other|non[\s-]?operating|general\s+(?:and|&)\s+administrative)?\s*(?:expenses?|expenditures?|overheads?|costs)"
    r")"
    r"(?:\s*(?:/|and|&|\(|,)\s*\(?\s*(?:other\s+)?(?:income|expenses?|expenditures?|costs?|net|loss(?:es)?)\s*\)?)*"
    r"(?:\s*,?\s*net)?\s*$",
    re.I,
)
# Net-of presentation ("Other Income (Expense)", "Other income and expense", "Other income, net"):
# income shown positive and expense in parentheses, i.e. credit-natural.
_NET_PRESENTATION = re.compile(
    r"\bincome\s*(?:\(\s*(?:expenses?|loss(?:es)?|costs?)\s*\)|/\s*\(?\s*(?:expenses?|loss)|and\s+\(?\s*(?:expenses?|loss)|,\s*net\b)",
    re.I,
)
_INCOME_WORD = re.compile(r"\bincome\b|\brevenues?\b|\bturnover\b|\bsales\b", re.I)
_NOT_INCOME_WORD = re.compile(r"\bexpenses?\b|\bcosts?\b|\bexpenditures?\b|\bcogs\b|marketing|commission|selling|\btax", re.I)


def section_is_credit_natural(section: str) -> bool:
    """Income-type sections show credits as positive (SPEC §3.5).

    Credit-natural: a heading about income, revenue, turnover or sales ("Income",
    "Revenue", "Trading Income", "Net Sales") that does not also name an expense
    ("Cost of Sales", "Income Tax Expense" and "Sales & Marketing" are debit-natural),
    and a net-of heading such as "Other Income (Expense)", where other expense is
    shown in parentheses.
    """
    s = clean_text(section)
    if _NET_PRESENTATION.search(s):
        return True
    return bool(_INCOME_WORD.search(s)) and not _NOT_INCOME_WORD.search(s)


def _pl_account_label(label: str) -> tuple[str, str]:
    """("4000", "Service Revenue") for an account row label, ("", label) otherwise.

    Shares the GL's account-label parsing so "6000.10 Salaries" and "4000-10 Commercial"
    keep their full numbers and pair with the GL; the number needs three or more digits.
    """
    number, name = split_account_label(label)
    if number and sum(ch.isdigit() for ch in number) >= 3:
        return number, name
    return "", clean_text(label)


@dataclass
class _Section:
    heading: str
    credit_natural: bool
    is_class: bool


def _parse_monthly_pl(
    path: Path, source_label: Optional[str], accounts: Optional[dict[str, Account]] = None
) -> tuple[ManagementPL, list[str]]:
    table = read_table(path)
    rows = table.rows
    source = source_label or path.name
    header_idx: Optional[int] = None
    month_cols: dict[int, str] = {}
    for i, row in enumerate(rows):
        found = {c: m for c, m in ((c, parse_month(v)) for c, v in enumerate(row)) if m}
        if len(found) >= 2:
            header_idx = i
            seen: set[str] = set()
            for c in sorted(found):
                if found[c] not in seen:
                    month_cols[c] = found[c]
                    seen.add(found[c])
            break
    if header_idx is None:
        raise ValueError(
            f"{source}: no header row with two or more month columns (e.g. 'Jan 2024', 'January 2024', "
            f"'2024-01' or an Excel date) found; first rows: {_first_rows(rows)}"
        )

    index = AccountIndex(accounts.values()) if accounts else None
    first_month_col = min(month_cols)
    notes: list[str] = list(table.notes)
    skipped: list[str] = []
    bad_cells: list[str] = []
    by_name: list[str] = []
    lines: list[PLAccountLine] = []
    stack: list[_Section] = []
    section_credit: dict[str, bool] = {}
    for idx in range(header_idx + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        # The label may be split over several columns (number | name) left of the months.
        label = " ".join(clean_text(row[c]) for c in range(min(first_month_col, len(row))) if not is_blank(row[c]))
        cells = {c: row[c] if c < len(row) else None for c in month_cols}
        has_amounts = any(not is_blank(v) for v in cells.values())
        if not label:
            if has_amounts:
                skipped.append(f"row {rowno} (amounts without a label)")
            continue
        number, name = _pl_account_label(label)
        if not number:
            if _PL_SUBTOTAL.match(label):
                # "Total <group>" closes that group, so later rows return to the parent's sign.
                m = _PL_TOTAL_OF.match(label)
                target = m.group(1).casefold() if m else ""
                for depth in range(len(stack) - 1, 0, -1):
                    if stack[depth].heading.casefold() == target:
                        del stack[depth:]
                        break
                continue
            if not has_amounts:
                is_class = bool(_CLASS_HEADING.match(label))
                if is_class or not stack:
                    stack = [_Section(label, section_is_credit_natural(label), is_class)]
                else:
                    stack.append(_Section(label, stack[-1].credit_natural, False))
                continue
            acct = None
            if index is not None:
                parents = [s.heading for s in stack if not s.is_class]
                acct, _ = index.find("", label, ":".join([*parents, label]))
            if acct is None:
                skipped.append(f"row {rowno} {label!r} (amounts but no account number or chart-of-accounts name)")
                continue
            number, name = acct.number, acct.name
            by_name.append(f"row {rowno} {label!r} -> {acct.number}")
        credit_natural = stack[-1].credit_natural if stack else False
        amounts: dict[str, str] = {}
        for c, month in month_cols.items():
            try:
                value = parse_money(cells[c])
            except ValueError:
                bad_cells.append(f"row {rowno} {month}")
                value = None
            if value is None:
                value = 0
            amounts[month] = fmt(-value if credit_natural else value)
        if not stack:
            notes.append(f"P&L {source}: row {rowno} account {number} sits above any section heading; read as debit-natural")
        section = " > ".join(s.heading for s in stack)
        section_credit[section] = credit_natural
        lines.append(
            PLAccountLine(
                account=number,
                account_name=name,
                section=section,
                amounts=amounts,
                source_row=rowno,
            )
        )
    months = list(month_cols.values())
    if not lines:
        detail = "; ".join(skipped[:6]) if skipped else "no labelled rows with amounts"
        raise ValueError(
            f"{source}: no account rows found below the month header on row {header_idx + 1}. Account rows need "
            f"an account number ('4000 Service Revenue') or a name that matches the chart of accounts; "
            f"{len(skipped)} row(s) with amounts were skipped: {detail}"
        )
    credit = [s for s, is_credit in section_credit.items() if s and is_credit]
    head = (
        f"P&L {source}: {len(lines)} account rows x {len(months)} months ({months[0]}..{months[-1]}); "
        f"credit-natural sections negated: {credit}"
    )
    notes.insert(0, head)
    if by_name:
        notes.append(f"P&L {source}: {len(by_name)} unnumbered row(s) matched to chart-of-accounts names: " + "; ".join(by_name[:10]))
    if skipped:
        notes.append(f"P&L {source}: skipped {len(skipped)} rows: " + "; ".join(skipped[:10]))
    if bad_cells:
        notes.append(f"P&L {source}: {len(bad_cells)} non-numeric amount cells read as 0: " + ", ".join(bad_cells[:10]))
    return ManagementPL(source_file=source, months=months, lines=lines), notes


def _first_rows(rows: list[Row], limit: int = 10) -> list[list[str]]:
    out = []
    for row in rows:
        cells = [clean_text(c) for c in row if not is_blank(c)]
        if cells:
            out.append(cells[:8])
        if len(out) >= limit:
            break
    return out


def read_monthly_pl(path: Path, *, source_label: Optional[str] = None, accounts: Optional[dict[str, Account]] = None) -> ManagementPL:
    """Management's account-level monthly P&L, normalized to debit-positive (SPEC §3.5).

    ``accounts`` (the chart of accounts) lets rows without an account number be
    matched by account name.
    """
    return _parse_monthly_pl(Path(path), source_label, accounts)[0]


# ---------------------------------------------------------------------------
# Management adjusted EBITDA schedule
# ---------------------------------------------------------------------------

_REF_HEADERS = ("ref", "#", "no.", "ref.", "ref #")
_SCHEDULE_COLUMNS = {
    "title": ("adjustment", "item", "description of adjustment"),
    "category": ("category", "type"),
    "description": ("description", "basis", "management commentary", "rationale"),
    "accounts": ("gl account(s)", "gl accounts", "account(s)", "gl"),
    "support": ("support ref", "support", "data room ref", "dr ref"),
}
_ACCOUNT_NUMBER = re.compile(r"(?<!\d)\d{3,6}(?!\d)")

# Checked in order: "adjusted ebitda" and "total ... adjustments" before plain "ebitda".
_LABEL_RULES = (
    (re.compile(r"adjusted\s+ebitda"), "adjusted_ebitda"),
    (re.compile(r"\btotal\b.*\badjustments?\b"), "total_adjustments"),
    (re.compile(r"net\s+income"), "net_income"),
    (re.compile(r"interest"), "interest"),
    (re.compile(r"\btax"), "taxes"),
    (re.compile(r"depreciation|amorti[sz]ation|\bd\s*&\s*a\b"), "depreciation_amortization"),
    (re.compile(r"ebitda"), "reported_ebitda"),
)

# A row that carries a Ref is still a label row when its title is nothing but a schedule
# line name: QoE schedules letter their subtotals ("A | Reported EBITDA", "A+B | Adjusted
# EBITDA"). Titles are compared after removing letter markers such as "(A)" or "(E+F)".
_QUALIFIER = r"(?:\s*,?\s*(?:as\s+reported|as\s+adjusted|per\s+.+|\(.*\)|\[.*\]))?"
_OWNER = r"(?:(?:management|mgmt|company|seller|diligence)(?:'s)?\s+)?"
_STRUCTURAL_LABELS = (
    (re.compile(rf"^{_OWNER}(?:pro[\s-]?forma\s+)?adjusted\s+ebitda{_QUALIFIER}$"), "adjusted_ebitda"),
    (re.compile(r"^total\b.*\badjustments?\b.*$"), "total_adjustments"),
    (re.compile(rf"^{_OWNER}(?:reported\s+|historical\s+|unadjusted\s+|book\s+)?ebitda{_QUALIFIER}$"), "reported_ebitda"),
    (re.compile(rf"^net\s+(?:income|profit|earnings)(?:\s*\(loss\))?{_QUALIFIER}$"), "net_income"),
)
# Build-up lines between net income and reported EBITDA, recognised with a Ref only
# before the first adjustment row.
_ADD = r"(?:(?:add(?:\s*back)?|plus|less)\s*:?\s*)?"
_BUILDUP_LABELS = (
    (re.compile(rf"^{_ADD}interest(?:\s+(?:expense|income|paid))?(?:\s*,?\s*net)?{_QUALIFIER}$"), "interest"),
    (re.compile(rf"^{_ADD}(?:(?:federal|state|provincial)\s+)?(?:income\s+)?tax(?:es)?(?:\s+expense)?{_QUALIFIER}$"), "taxes"),
    (
        re.compile(rf"^{_ADD}(?:depreciation(?:\s*(?:and|&)\s*amorti[sz]ation)?|amorti[sz]ation|d\s*&\s*a)(?:\s+expense)?{_QUALIFIER}$"),
        "depreciation_amortization",
    ),
)
_LETTER_MARKER = re.compile(r"\s*[\(\[]\s*[a-z](?:\s*[+\-=]\s*[a-z])*\s*[\)\]]\s*")
_TRAILING_FORMULA = re.compile(r"\s*=?\s*[a-z](?:\s*[+\-]\s*[a-z])+\s*$")
# Footnote markers in the Ref column: "(1)", "1)", "(a)", "*", "[2]", "Note 1", "Source:".
_FOOTNOTE_REF = re.compile(r"^(?:\(?\d{1,2}\)|\(?[a-z]\)|\[\d{1,2}\]|[*†‡§]+|notes?\b.*|source\b.*)$", re.I)
# "Total adjustments", "Total management adjustments": the grand total, not "Total <category> adjustments".
_GRAND_TOTAL = re.compile(r"^total\s+(?:(?:management|mgmt|ebitda|all|net|proposed|company|seller)(?:'s)?\s+)*adjustments?\b", re.I)
_TOTAL_FOOT_TOLERANCE = Decimal("1.00")

# More specific categories first: "owner compensation normalization" is a
# normalization, "non-recurring prior-period true-up" is out-of-period.
_CATEGORY_RULES = (
    (re.compile(r"normali[sz]"), AdjustmentCategory.NORMALIZATION),
    (re.compile(r"pro[\s-]?forma|run[\s-]?rate"), AdjustmentCategory.PRO_FORMA),
    (re.compile(r"out[\s-]of[\s-]period|prior[\s-]period"), AdjustmentCategory.OUT_OF_PERIOD),
    (re.compile(r"non[\s-]?recurring|one[\s-]?time"), AdjustmentCategory.NON_RECURRING),
    (re.compile(r"owner|discretionary|personal"), AdjustmentCategory.OWNER_DISCRETIONARY),
)


def map_category(raw: str) -> AdjustmentCategory:
    text = raw.casefold()
    for pattern, category in _CATEGORY_RULES:
        if pattern.search(text):
            return category
    return AdjustmentCategory.OTHER


def schedule_label_key(label: str) -> Optional[str]:
    """Which ``ManagementSchedule`` field a blank-Ref label row fills, if any."""
    text = label.casefold()
    for pattern, key in _LABEL_RULES:
        if pattern.search(text):
            return key
    return None


def _bare_title(title: str) -> str:
    text = clean_text(title).casefold()
    text = _LETTER_MARKER.sub(" ", text)
    text = _TRAILING_FORMULA.sub("", text)
    return text.strip(" :-–—")


def ref_row_label_key(title: str, *, before_adjustments: bool) -> Optional[str]:
    """The schedule line a Ref-carrying row really is ("A | Reported EBITDA"), or None for an adjustment."""
    text = _bare_title(title)
    rules = _STRUCTURAL_LABELS + (_BUILDUP_LABELS if before_adjustments else ())
    for pattern, key in rules:
        if pattern.match(text):
            return key
    return None


def _ref_text(value: object, number_format: Optional[str] = None) -> str:
    """A Ref cell as management shows it. Numeric refs keep the decimals their cell format
    displays ("0.00" shows 1.1 as "1.10")."""
    if isinstance(value, float) and not isinstance(value, bool):
        m = re.fullmatch(r"0(?:\.(0+))?", (number_format or "").strip())
        if m:
            return f"{value:.{len(m.group(1) or '')}f}"
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return clean_text(value)


def _merge_header_rows(upper: Row, lower: Row) -> Row:
    """Two-row header (a merged "Fiscal year ended" over the period labels): lower row wins."""
    width = max(len(upper), len(lower))
    return [
        lower[c] if c < len(lower) and not is_blank(lower[c]) else (upper[c] if c < len(upper) else None)
        for c in range(width)
    ]


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _match_schedule_header(row: Row, wanted: dict[str, str]) -> Optional[tuple[dict[str, int], dict[str, int], list[str]]]:
    keys = [norm_key(v) for v in row]
    if not any(k in _REF_HEADERS for k in keys):
        return None
    cols: dict[str, int] = {}
    for c, k in enumerate(keys):
        if k and k not in cols:
            cols[k] = c
    period_cols: dict[str, int] = {}
    loose: list[str] = []
    for label, key in wanted.items():
        if key in cols:
            period_cols[label] = cols[key]
            continue
        # "FY 2024" for "FY2024": the same label with different spacing.
        hits = [c for c, k in enumerate(keys) if k and _squash(k) == _squash(key)]
        if len(hits) != 1:
            return None
        period_cols[label] = hits[0]
        loose.append(f"{clean_text(row[hits[0]])!r} read as {label!r}")
    return cols, period_cols, loose


def _schedule_header_error(rows: list[Row], period_labels: list[str], source: str) -> ValueError:
    cells = [clean_text(c) for row in rows[:25] for c in row if not is_blank(c)]
    near: list[str] = []
    for label in period_labels:
        digits = set(re.findall(r"\d{2,}", label))
        tokens = {t for t in re.findall(r"[a-z]+", label.casefold()) if len(t) > 1}
        similar = [
            c for c in cells
            if len(c) <= 40 and ((digits and any(d in c for d in digits)) or (tokens and tokens & set(re.findall(r"[a-z]+", c.casefold()))))
        ]
        if similar:
            near.append(f"{label!r}: found {', '.join(repr(s) for s in list(dict.fromkeys(similar))[:4])}")
    hint = ("; closest cells: " + "; ".join(near)) if near else ""
    return ValueError(
        f"{source}: no header row with a Ref/#/No. column and every period label {period_labels} "
        f"(labels must match deal.yaml; a header may span two rows){hint}; first rows: {_first_rows(rows)}"
    )


def _parse_schedule(path: Path, period_labels: list[str], source_label: Optional[str]) -> tuple[ManagementSchedule, list[str]]:
    table = read_table(path, keep_number_formats=True)
    rows = table.rows
    source = source_label or path.name
    wanted = {label: norm_key(label) for label in period_labels}
    header_idx: Optional[int] = None
    matched: Optional[tuple[dict[str, int], dict[str, int], list[str]]] = None
    for i, row in enumerate(rows):
        matched = _match_schedule_header(row, wanted)
        if matched is not None:
            header_idx = i
            break
        if i + 1 < len(rows):
            matched = _match_schedule_header(_merge_header_rows(row, rows[i + 1]), wanted)
            if matched is not None:
                header_idx = i + 1
                break
    if header_idx is None or matched is None:
        raise _schedule_header_error(rows, period_labels, source)
    cols, period_cols, loose = matched

    ref_col = next(cols[k] for k in _REF_HEADERS if k in cols)
    used = {ref_col, *period_cols.values()}
    field_cols: dict[str, Optional[int]] = {}
    for field_name, candidates in _SCHEDULE_COLUMNS.items():
        field_cols[field_name] = None
        for cand in candidates:
            c = cols.get(cand)
            if c is not None and c not in used:
                field_cols[field_name] = c
                used.add(c)
                break
    notes: list[str] = list(table.notes)
    if loose:
        notes.append(f"schedule {source}: period headers matched ignoring spaces: " + "; ".join(loose))
    if field_cols["title"] is None:
        # Without a recognised title header, the column right of Ref holds the title.
        field_cols["title"] = ref_col + 1
        notes.append(f"schedule {source}: no Adjustment/Item column header; using column {ref_col + 2} for titles")

    def text_at(row: Row, field_name: str) -> str:
        c = field_cols[field_name]
        return clean_text(row[c]) if c is not None and c < len(row) else ""

    sched: dict[str, dict[str, str]] = {}
    totals: list[tuple[int, str, dict[str, str]]] = []
    adjustments: list[AdjustmentClaim] = []
    first_row_of: dict[str, int] = {}
    bad_cells: list[str] = []
    ignored: list[str] = []
    relabeled: list[str] = []
    renamed: list[str] = []
    decimal_refs: list[str] = []
    adjusted_seen = False
    for idx in range(header_idx + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(v) for v in row):
            continue
        amounts: dict[str, str] = {}
        has_amount = False
        for label, c in period_cols.items():
            cell = row[c] if c < len(row) else None
            has_amount = has_amount or not is_blank(cell)
            try:
                amounts[label] = fmt(parse_money(cell) or 0)
            except ValueError:
                bad_cells.append(f"row {rowno} {label}")
                amounts[label] = fmt(0)
        raw_ref = row[ref_col] if ref_col < len(row) else None
        ref = _ref_text(raw_ref, table.number_formats.get((idx, ref_col)))
        if isinstance(raw_ref, float) and not raw_ref.is_integer() and (idx, ref_col) not in table.number_formats:
            decimal_refs.append(f"{ref} (row {rowno})")
        title = text_at(row, "title")
        if ref and not title and schedule_label_key(ref) is not None:
            # Some schedules put "Net income" / "Reported EBITDA" in the first column.
            ref, title = "", ref
        raw_category = text_at(row, "category")
        accounts_cell = text_at(row, "accounts")
        if ref:
            key = ref_row_label_key(title, before_adjustments=not adjustments and "reported_ebitda" not in sched) if title else None
            if key is not None:
                relabeled.append(f"row {rowno} ({ref} {title!r}) read as {key}")
                ref = ""
            elif not has_amount and not raw_category and not accounts_cell and (not title or adjusted_seen or _FOOTNOTE_REF.match(ref)):
                # Footnotes and notes: a marker and text, but no amounts, category or accounts.
                ignored.append(f"row {rowno} {ref[:12]!r} {title[:40]!r}".rstrip(" '\""))
                continue
            else:
                adj_id = ref
                if adj_id in first_row_of:
                    n = 2
                    while f"{ref}#{n}" in first_row_of:
                        n += 1
                    adj_id = f"{ref}#{n}"
                    renamed.append(f"row {rowno} repeats Ref {ref!r} of row {first_row_of[ref]} and is kept as {adj_id!r}")
                first_row_of[adj_id] = rowno
                gl_accounts = list(dict.fromkeys(_ACCOUNT_NUMBER.findall(accounts_cell)))
                support = [s.strip() for s in re.split(r"[;,\n]", text_at(row, "support")) if s.strip()]
                adjustments.append(
                    AdjustmentClaim(
                        adj_id=adj_id,
                        title=title,
                        category_raw=raw_category,
                        category=map_category(raw_category),
                        description=text_at(row, "description"),
                        gl_accounts=gl_accounts,
                        support_refs=support,
                        amounts=amounts,
                        source_row=rowno,
                    )
                )
                continue
        key = schedule_label_key(title) if title else None
        if key is None:
            continue
        if key == "total_adjustments":
            totals.append((rowno, title, amounts))
            continue
        if key == "adjusted_ebitda":
            adjusted_seen = True
        if key in sched:
            notes.append(f"schedule {source}: row {rowno} {title!r} repeats {key}; first occurrence kept")
            continue
        sched[key] = amounts

    if totals:
        chosen, total_note = _pick_total_adjustments(totals, adjustments, period_labels)
        sched["total_adjustments"] = chosen[2]
        if total_note:
            notes.append(f"schedule {source}: {total_note}")
    missing = [k for k in ("net_income", "reported_ebitda", "total_adjustments", "adjusted_ebitda") if k not in sched]
    notes.insert(
        0,
        f"schedule {source}: {len(adjustments)} adjustments ({', '.join(a.adj_id for a in adjustments)}); "
        f"label rows found: {sorted(sched)}" + (f"; not found: {missing}" if missing else ""),
    )
    if renamed:
        notes.append(f"schedule {source}: WARNING - duplicate Refs; each row is kept as its own adjustment: " + "; ".join(renamed))
    if decimal_refs:
        notes.append(
            f"schedule {source}: Refs stored as decimal numbers are read as displayed without formatting ("
            + ", ".join(decimal_refs[:10])
            + "); a Ref typed 1.10 is stored as 1.1, so format the Ref column as text if Refs look wrong"
        )
    if relabeled:
        notes.append(f"schedule {source}: rows with a Ref read as schedule lines, not adjustments: " + "; ".join(relabeled))
    if ignored:
        notes.append(f"schedule {source}: ignored {len(ignored)} note rows (a Ref but no amounts, category or accounts): " + "; ".join(ignored))
    if bad_cells:
        notes.append(f"schedule {source}: {len(bad_cells)} non-numeric amount cells read as 0: " + ", ".join(bad_cells[:10]))
    schedule = ManagementSchedule(source_file=source, period_labels=list(period_labels), adjustments=adjustments, **sched)
    return schedule, notes


def _pick_total_adjustments(
    totals: list[tuple[int, str, dict[str, str]]], adjustments: list[AdjustmentClaim], labels: list[str]
) -> tuple[tuple[int, str, dict[str, str]], str]:
    """The grand-total row among "Total ... adjustments" rows, and a note when there was a choice.

    Category subtotals ("Total non-recurring adjustments") precede the grand total, so the
    last row whose amounts equal the sum of every adjustment wins; failing that, the last
    row worded as a grand total ("Total adjustments", "Total management adjustments"),
    else the last total row.
    """
    if len(totals) == 1:
        return totals[0], ""
    sums = {label: sum((D(a.amounts.get(label, 0)) for a in adjustments), Decimal(0)) for label in labels}

    def foots(amounts: dict[str, str]) -> bool:
        return all(abs(D(amounts[label]) - sums[label]) <= _TOTAL_FOOT_TOLERANCE for label in labels)

    footing = [t for t in totals if foots(t[2])]
    grand = [t for t in totals if _GRAND_TOTAL.match(t[1])]
    chosen = (footing or grand or totals)[-1]
    others = ", ".join(f"row {r} {t!r}" for r, t, _ in totals if r != chosen[0])
    why = "it equals the sum of the adjustments" if footing else ("it is worded as the grand total" if grand else "it is the last total row")
    return chosen, f"row {chosen[0]} {chosen[1]!r} used as total adjustments ({why}); {others} read as subtotals"


def read_schedule(path: Path, period_labels: list[str], *, source_label: Optional[str] = None) -> ManagementSchedule:
    """Management's adjusted-EBITDA schedule for the given period labels (SPEC §3.6)."""
    return _parse_schedule(Path(path), period_labels, source_label)[0]


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def _decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


class _TextExtractor(HTMLParser):
    """Visible text of an HTML email body. Linear in the input, unlike a backtracking regex."""

    _BREAKS = frozenset({"br", "p", "div", "tr", "li", "table", "h1", "h2", "h3", "h4", "h5", "h6"})
    _HIDDEN = frozenset({"script", "style", "head", "title"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._HIDDEN:
            self._hidden += 1
        elif tag in self._BREAKS:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        if tag in self._BREAKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._HIDDEN:
            self._hidden = max(0, self._hidden - 1)
        elif tag in self._BREAKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._hidden:
            self.parts.append(data)


_TAG = re.compile(r"<[^<>]*>")


def _strip_html(html: str) -> str:
    """Visible text of an HTML body: script/style dropped, block ends as line breaks, entities decoded."""
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError):
        # Malformed markup html.parser gives up on: drop tags with a linear pattern instead.
        return _TAG.sub("", html)
    return "".join(parser.parts).replace("\xa0", " ")


def _eml_text(data: bytes) -> str:
    """Headers a reviewer cites (From / To / Cc / Date / Subject) plus the readable body."""
    try:
        msg = BytesParser(policy=policy.default).parsebytes(data)
        lines = [f"{h}: {msg[h]}" for h in ("From", "To", "Cc", "Date", "Subject") if msg[h] is not None]
        part = msg.get_body(preferencelist=("plain", "html"))
        body = ""
        if part is not None:
            body = part.get_content()
            if part.get_content_type() == "text/html":
                body = _strip_html(body)
        if lines or body.strip():
            return "\n".join(lines) + "\n\n" + body
    except Exception:  # malformed MIME: fall back to the raw text rather than lose the document
        pass
    return _decode_text(data)


def _inside(path: Path, base: Path) -> bool:
    """Whether ``path``, with every symlink followed, lies inside ``base``."""
    try:
        return path.resolve().is_relative_to(base.resolve())
    except (OSError, RuntimeError):
        return False


def _is_answer_key(path: Path, deal_dir: Path) -> bool:
    """The deal's ground_truth.json by name, by symlink target, or as the same file (hard link).

    Decided from names and file metadata only: the answer key itself is never opened.
    """
    if path.name == GROUND_TRUTH_FILENAME:
        return True
    try:
        if path.resolve().name == GROUND_TRUTH_FILENAME:
            return True
        answer_key = deal_dir / GROUND_TRUTH_FILENAME
        return answer_key.exists() and os.path.samefile(path, answer_key)
    except (OSError, RuntimeError):
        return False


def _scan_documents(root: Path, deal_dir: Path) -> tuple[list[SourceDocument], list[str]]:
    rel_root = _relpath(root, deal_dir)
    if not _inside(root, deal_dir):
        raise ValueError(f"documents directory {rel_root!r} resolves outside the deal directory")
    if not root.is_dir():
        return [], [f"documents: directory {rel_root!r} not found; no documents loaded"]
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    docs: list[SourceDocument] = []
    notes: list[str] = []
    unsupported: list[str] = []
    no_text: list[str] = []
    outside: list[str] = []
    too_big: list[str] = []
    answer_key_links: list[str] = []
    seen: dict[str, str] = {}
    for path in files:
        rel = _relpath(path, deal_dir)
        if path.name.startswith("."):
            continue
        if _is_answer_key(path, deal_dir):
            if path.name != GROUND_TRUTH_FILENAME:
                answer_key_links.append(rel)
            continue
        if not _inside(path, deal_dir):
            # A symlink (or a file under a linked folder) pointing outside the package: reading it
            # would put unrelated files into the workpaper and the AI payload.
            outside.append(rel)
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size > MAX_DOCUMENT_BYTES:
            too_big.append(f"{rel} ({size // (1024 * 1024)} MB)")
            continue
        media_type = DOCUMENT_TYPES.get(path.suffix.lower())
        if media_type is None:
            unsupported.append(rel)
            continue
        if path.name in seen:
            raise ValueError(f"document file names must be unique within a deal: {seen[path.name]!r} and {rel!r}")
        seen[path.name] = rel
        data = path.read_bytes()
        if media_type == "pdf":
            try:
                raw_pages = extract_pdf_pages(data)
            except Exception as exc:  # a corrupt data-room PDF should not stop the review
                notes.append(f"documents: could not read PDF {rel!r} ({type(exc).__name__}: {exc}); skipped")
                continue
            if not raw_pages:
                notes.append(f"documents: PDF {rel!r} has no pages; skipped")
                continue
        elif media_type == "eml":
            raw_pages = [_eml_text(data)]
        else:
            raw_pages = [_decode_text(data)]
        pages = [DocumentPage(page=i, text=canonicalize_page_text(t)) for i, t in enumerate(raw_pages, start=1)]
        empty = [p.page for p in pages if not p.text.strip()]
        if empty:
            no_text.append(f"{rel} (page {', '.join(map(str, empty))})")
        docs.append(
            SourceDocument(
                doc_id=path.name,
                relpath=rel,
                media_type=media_type,
                sha256=hashlib.sha256(data).hexdigest(),
                pages=pages,
            )
        )
    counts: dict[str, int] = {}
    for d in docs:
        counts[d.media_type] = counts.get(d.media_type, 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"
    notes.insert(0, f"documents {rel_root}: {len(docs)} loaded ({summary})")
    if unsupported:
        notes.append(f"documents: skipped {len(unsupported)} unsupported file(s) (not pdf/txt/md/eml): " + "; ".join(unsupported))
    if outside:
        notes.append(f"documents: WARNING - skipped {len(outside)} link(s) that resolve outside the deal directory: " + "; ".join(outside))
    if answer_key_links:
        notes.append(f"documents: WARNING - skipped {len(answer_key_links)} file(s) that are the evaluation answer key under another name: " + "; ".join(answer_key_links))
    if too_big:
        notes.append(f"documents: skipped {len(too_big)} file(s) larger than {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB: " + "; ".join(too_big))
    if no_text:
        notes.append("documents: no text layer (scanned image? needs OCR before quotes can be verified): " + "; ".join(no_text))
    return docs, notes


def read_documents(root: Path, deal_dir: Path) -> list[SourceDocument]:
    """Every pdf / txt / md / eml under ``root`` in sorted order, canonicalized per page (SPEC §3.7)."""
    return _scan_documents(Path(root), Path(deal_dir))[0]


# ---------------------------------------------------------------------------
# load_deal
# ---------------------------------------------------------------------------


def _class_from_pl_section(section: str) -> Optional[EbitdaClass]:
    # A nested path ("Expenses > Sales & Marketing") takes its class from the innermost
    # class heading; group headings only organise accounts inside it.
    parts = [p for p in section.split(" > ") if p]
    if not parts:
        return None
    section = next((p for p in reversed(parts) if _CLASS_HEADING.match(p)), parts[0])
    s = section.casefold()
    if section_is_credit_natural(section):
        return EbitdaClass.OTHER_INCOME if "other" in s else EbitdaClass.REVENUE
    if "cost of" in s or "cogs" in s or "direct cost" in s:
        return EbitdaClass.COGS
    if "other" in s and "expense" in s:
        return EbitdaClass.OTHER_EXPENSE
    if "expense" in s or "overhead" in s:
        return EbitdaClass.OPEX
    return None


def _missing_accounts(gl: list[GLEntry], accounts: dict[str, Account], pl: ManagementPL) -> dict[str, Account]:
    """Fallback accounts for GL accounts absent from the chart of accounts.

    They keep a ``fallback`` basis so reconciliation raises UNMAPPED_ACCOUNT; the
    P&L section the account sits in is the best evidence of its class.
    """
    sections = {ln.account: ln.section for ln in pl.lines}
    out: dict[str, Account] = {}
    for e in gl:
        if e.account in accounts or e.account in out:
            continue
        cls, basis = classify_account(e.account_name, "")
        if basis.startswith(FALLBACK_BASIS):
            from_pl = _class_from_pl_section(sections.get(e.account, ""))
            if from_pl is not None:
                cls = from_pl
                basis = f"{FALLBACK_BASIS}: not in chart of accounts; class from P&L section {sections[e.account]!r}"
            else:
                basis = f"{FALLBACK_BASIS}: not in chart of accounts; defaulted to OPEX"
        else:
            basis = f"{FALLBACK_BASIS}: not in chart of accounts; {basis}"
        out[e.account] = Account(number=e.account, name=e.account_name, source_type="", ebitda_class=cls, mapping_basis=basis)
    return out


def _package_path(deal_dir: Path, rel: str, what: str) -> tuple[Path, str]:
    """``deal_dir / rel`` for a deal.yaml path, refusing anything that leaves the package.

    Absolute paths, ``..`` segments that climb out, and symlinks that resolve outside the
    deal directory are all rejected: ingest reads only the package it was given.
    """
    text = str(rel).strip()
    if not text or text.startswith(("/", "\\")) or PurePosixPath(text).is_absolute() or Path(text).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", text):
        raise ValueError(f"deal.yaml: {what} must be a path relative to the deal directory, got {rel!r}")
    rel_posix = PurePosixPath(os.path.normpath(text.replace("\\", "/")).replace(os.sep, "/")).as_posix()
    path = deal_dir / rel_posix
    if rel_posix == ".." or rel_posix.startswith("../") or not _inside(path, deal_dir):
        raise ValueError(f"deal.yaml: {what} {rel!r} resolves outside the deal directory")
    return path, rel_posix


def load_deal(deal_dir: Path) -> DealPackage:
    """Load a deal package directory (SPEC §3). Never opens ground_truth.json."""
    deal_dir = Path(deal_dir)
    hashes: dict[str, str] = {}
    notes: list[str] = []

    def input_file(rel: str, what: str) -> Path:
        path, rel_posix = _package_path(deal_dir, rel, what)
        if _is_answer_key(path, deal_dir):
            raise ValueError(f"{what} may not point at {GROUND_TRUTH_FILENAME}")
        if not path.is_file():
            raise FileNotFoundError(f"{what} file {rel_posix!r} not found in deal directory {deal_dir}")
        hashes[rel_posix] = _sha256(path)
        return path

    meta, meta_notes = _parse_deal_meta(input_file(DEAL_YAML, "deal.yaml"))
    periods = "; ".join(f"{p.label} {p.start}..{p.end}" for p in meta.periods)
    notes.append(f"deal {meta.deal_id}: periods {periods}; data range {meta.data_start}..{meta.data_end}; tolerance {meta.tolerance} {meta.currency}")
    notes.extend(meta_notes)
    files = meta.files

    coa_path = input_file(files.chart_of_accounts, "chart_of_accounts")
    overrides_path: Optional[Path] = None
    if files.account_mapping_overrides:
        overrides_path = input_file(files.account_mapping_overrides, "account_mapping_overrides")
    elif (coa_path.parent / DEFAULT_OVERRIDES_NAME).is_file():
        overrides_path = input_file(_relpath(coa_path.parent / DEFAULT_OVERRIDES_NAME, deal_dir), "account_mapping_overrides")
    account_list, coa_notes = read_chart_of_accounts(coa_path, overrides_path)
    accounts = {a.number: a for a in account_list}
    notes.extend(coa_notes)
    if overrides_path is not None:
        notes.append(f"account mapping overrides read from {_relpath(overrides_path, deal_dir)}")

    pl_path = input_file(files.monthly_pl, "monthly_pl")
    pl, pl_notes = _parse_monthly_pl(pl_path, _relpath(pl_path, deal_dir), accounts)

    gl_path = input_file(files.gl, "gl")
    gl_rel = _relpath(gl_path, deal_dir)
    if meta.gl_format == "auto":
        gl_format = detect_format(gl_path)
        notes.append(f"GL format {gl_format} auto-detected for {gl_rel}")
    else:
        gl_format = meta.gl_format
        notes.append(f"GL format {gl_format} set in deal.yaml for {gl_rel}")
    gl, gl_notes = read_gl(gl_path, gl_format, accounts, source_label=gl_rel)
    extra_accounts = _missing_accounts(gl, accounts, pl)
    if extra_accounts:
        accounts.update(extra_accounts)
        if gl_format == QBO and any(is_credit_natural(a) for a in extra_accounts.values()):
            # QBO amounts are natural-signed, so re-read once the missing accounts have a class.
            gl, gl_notes = read_gl(gl_path, gl_format, accounts, source_label=gl_rel)
        for a in extra_accounts.values():
            gl_notes.append(f"account {a.number} {a.name}: {a.mapping_basis} ({a.ebitda_class.value})")
    notes.extend(gl_notes)
    in_range = set(month_range(meta.data_start, meta.data_end))
    outside = sorted({e.period for e in gl if e.period not in in_range})
    if outside:
        n = sum(1 for e in gl if e.period not in in_range)
        notes.append(f"GL: {n} entries dated outside the data range {meta.data_start}..{meta.data_end} (months {', '.join(outside)})")
    notes.extend(pl_notes)

    adj_path = input_file(files.adjustments, "adjustments")
    schedule, sched_notes = _parse_schedule(adj_path, [p.label for p in meta.periods], _relpath(adj_path, deal_dir))
    notes.extend(sched_notes)

    docs_root, _ = _package_path(deal_dir, files.documents_dir, "documents_dir")
    documents, doc_notes = _scan_documents(docs_root, deal_dir)
    for doc in documents:
        hashes[doc.relpath] = doc.sha256
    notes.extend(doc_notes)

    return DealPackage(
        deal_dir=str(deal_dir),
        meta=meta,
        accounts=accounts,
        gl=gl,
        pl=pl,
        schedule=schedule,
        documents=documents,
        input_hashes=dict(sorted(hashes.items())),
        ingest_notes=notes,
    )
