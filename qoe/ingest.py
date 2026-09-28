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
from datetime import date
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Optional

import yaml

from qoe.gl_formats import (
    FALLBACK_BASIS,
    GL_FORMATS,
    QBO,
    classify_account,
    clean_text,
    detect_format,
    is_blank,
    is_credit_natural,
    load_table_rows,
    norm_key,
    parse_money,
    parse_month,
    read_chart_of_accounts,
    read_gl,
)
from qoe.money import fmt
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

_PL_ACCOUNT = re.compile(r"^\s*(\d{3,6})\s*[·\-–:]?\s*(.+?)\s*$")
_PL_SUBTOTAL = re.compile(
    r"^\s*(total\b|gross (profit|margin)\b|net (operating|ordinary|other) income\b|net income\b|net (profit|loss)\b)",
    re.I,
)


def section_is_credit_natural(section: str) -> bool:
    """Income-type sections show credits as positive (SPEC §3.5).

    Revenue / sales headings count as income too, so a Xero-style "Revenue"
    section is not read with the wrong sign.
    """
    s = section.casefold()
    return bool(re.search(r"income|revenue|sales", s)) and not re.search(r"expense|cost", s)


def _parse_monthly_pl(path: Path, source_label: Optional[str]) -> tuple[ManagementPL, list[str]]:
    rows = load_table_rows(path)
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
        raise ValueError(f"{source}: no header row with month columns (e.g. 'Jan 2024') found")

    first_month_col = min(month_cols)
    notes: list[str] = []
    skipped: list[str] = []
    bad_cells: list[str] = []
    lines: list[PLAccountLine] = []
    section = ""
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
        m = _PL_ACCOUNT.match(label)
        if m is None:
            if _PL_SUBTOTAL.match(label):
                continue
            if has_amounts:
                skipped.append(f"row {rowno} {label!r} (amounts but no account number)")
                continue
            section = label
            continue
        credit_natural = section_is_credit_natural(section)
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
        if not section:
            notes.append(f"P&L {source}: row {rowno} account {m.group(1)} sits above any section heading; read as debit-natural")
        lines.append(
            PLAccountLine(
                account=m.group(1),
                account_name=m.group(2),
                section=section,
                amounts=amounts,
                source_row=rowno,
            )
        )
    months = list(month_cols.values())
    sections = sorted({ln.section for ln in lines if ln.section})
    credit = [s for s in sections if section_is_credit_natural(s)]
    head = (
        f"P&L {source}: {len(lines)} account rows x {len(months)} months ({months[0]}..{months[-1]}); "
        f"credit-natural sections negated: {credit}"
    )
    notes.insert(0, head)
    if skipped:
        notes.append(f"P&L {source}: skipped {len(skipped)} rows: " + "; ".join(skipped[:10]))
    if bad_cells:
        notes.append(f"P&L {source}: {len(bad_cells)} non-numeric amount cells read as 0: " + ", ".join(bad_cells[:10]))
    return ManagementPL(source_file=source, months=months, lines=lines), notes


def read_monthly_pl(path: Path, *, source_label: Optional[str] = None) -> ManagementPL:
    """Management's account-level monthly P&L, normalized to debit-positive (SPEC §3.5)."""
    return _parse_monthly_pl(Path(path), source_label)[0]


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


def _ref_text(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return clean_text(value)


def _parse_schedule(path: Path, period_labels: list[str], source_label: Optional[str]) -> tuple[ManagementSchedule, list[str]]:
    rows = load_table_rows(path)
    source = source_label or path.name
    wanted = [norm_key(label) for label in period_labels]
    header_idx: Optional[int] = None
    cols: dict[str, int] = {}
    for i, row in enumerate(rows):
        keys = [norm_key(v) for v in row]
        if not any(k in _REF_HEADERS for k in keys) or not all(w in keys for w in wanted):
            continue
        header_idx = i
        for c, k in enumerate(keys):
            if k and k not in cols:
                cols[k] = c
        break
    if header_idx is None:
        raise ValueError(
            f"{source}: no header row with a Ref/#/No. column and every period label {period_labels}"
        )

    ref_col = next(cols[k] for k in _REF_HEADERS if k in cols)
    period_cols = {label: cols[norm_key(label)] for label in period_labels}
    used = {ref_col, *period_cols.values()}
    field_cols: dict[str, Optional[int]] = {}
    for field, candidates in _SCHEDULE_COLUMNS.items():
        field_cols[field] = None
        for cand in candidates:
            c = cols.get(cand)
            if c is not None and c not in used:
                field_cols[field] = c
                used.add(c)
                break
    notes: list[str] = []
    if field_cols["title"] is None:
        # Without a recognised title header, the column right of Ref holds the title.
        field_cols["title"] = ref_col + 1
        notes.append(f"schedule {source}: no Adjustment/Item column header; using column {ref_col + 2} for titles")

    def text_at(row: list[object], field: str) -> str:
        c = field_cols[field]
        return clean_text(row[c]) if c is not None and c < len(row) else ""

    sched: dict[str, dict[str, str]] = {}
    adjustments: list[AdjustmentClaim] = []
    bad_cells: list[str] = []
    ignored: list[str] = []
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
        ref = _ref_text(row[ref_col] if ref_col < len(row) else None)
        title = text_at(row, "title")
        if ref and not title and schedule_label_key(ref) is not None:
            # Some schedules put "Net income" / "Reported EBITDA" in the first column.
            ref, title = "", ref
        if ref:
            if not title and not has_amount:
                ignored.append(f"row {rowno} {ref[:40]!r}")
                continue
            raw_category = text_at(row, "category")
            accounts_cell = text_at(row, "accounts")
            gl_accounts = list(dict.fromkeys(_ACCOUNT_NUMBER.findall(accounts_cell)))
            support = [s.strip() for s in re.split(r"[;,\n]", text_at(row, "support")) if s.strip()]
            adjustments.append(
                AdjustmentClaim(
                    adj_id=ref,
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
        if key in sched:
            notes.append(f"schedule {source}: row {rowno} {title!r} repeats {key}; first occurrence kept")
            continue
        sched[key] = amounts

    missing = [k for k in ("net_income", "reported_ebitda", "total_adjustments", "adjusted_ebitda") if k not in sched]
    notes.insert(
        0,
        f"schedule {source}: {len(adjustments)} adjustments ({', '.join(a.adj_id for a in adjustments)}); "
        f"label rows found: {sorted(sched)}" + (f"; not found: {missing}" if missing else ""),
    )
    if ignored:
        notes.append(f"schedule {source}: ignored {len(ignored)} note rows with a Ref but no title or amounts: " + "; ".join(ignored))
    if bad_cells:
        notes.append(f"schedule {source}: {len(bad_cells)} non-numeric amount cells read as 0: " + ", ".join(bad_cells[:10]))
    schedule = ManagementSchedule(source_file=source, period_labels=list(period_labels), adjustments=adjustments, **sched)
    return schedule, notes


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


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


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


def _scan_documents(root: Path, deal_dir: Path) -> tuple[list[SourceDocument], list[str]]:
    rel_root = _relpath(root, deal_dir)
    if not root.is_dir():
        return [], [f"documents: directory {rel_root!r} not found; no documents loaded"]
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    docs: list[SourceDocument] = []
    notes: list[str] = []
    unsupported: list[str] = []
    no_text: list[str] = []
    seen: dict[str, str] = {}
    for path in files:
        rel = _relpath(path, deal_dir)
        if path.name.startswith(".") or path.name == GROUND_TRUTH_FILENAME:
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


def load_deal(deal_dir: Path) -> DealPackage:
    """Load a deal package directory (SPEC §3). Never opens ground_truth.json."""
    deal_dir = Path(deal_dir)
    hashes: dict[str, str] = {}
    notes: list[str] = []

    def input_file(rel: str, what: str) -> Path:
        rel_posix = PurePosixPath(os.path.normpath(rel).replace(os.sep, "/")).as_posix()
        path = deal_dir / rel_posix
        if path.name == GROUND_TRUTH_FILENAME:
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
    pl, pl_notes = _parse_monthly_pl(pl_path, _relpath(pl_path, deal_dir))

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

    docs_root = deal_dir / files.documents_dir
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
