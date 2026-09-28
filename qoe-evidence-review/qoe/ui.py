"""Streamlit reviewer app for QoE Evidence Review.

Run with ``uv run streamlit run qoe/ui.py``.

Flow: pick a deal package -> run (or reopen) the review -> Overview (bridge,
reconciliation, status counts) -> Adjustment queue -> Adjustment detail (the
evidence, the judgment calls, and the review form) -> Open questions -> Export.

Diligence-identified items (``source == "diligence"``, SPEC §5.7: adjustments
the tool proposes that are not on management's schedule, such as reversing a
duplicate posting) are reviewed exactly like management's items. The queue
lists them as their own group after management's items, and the bridge shows
their rows after the diligence revisions to management's items.

Decisions go to ``<workpapers>/<deal_id>/review_log.jsonl`` (append-only),
question status changes, management responses and reviewer-raised questions to
``question_log.jsonl``, and time on task to ``timing.jsonl`` beside them. A
question update is signed by whoever makes it and never re-records a decision.
The top half of this module is pure helpers (table builders, formatting, the
time tracker) that are unit-tested; Streamlit rendering lives below and only
runs under ``streamlit run``.

Access: the app has no authentication and shows confidential deal data, so it
binds to 127.0.0.1 (``make ui`` passes ``--server.address 127.0.0.1`` and
``.streamlit/config.toml`` sets the same default). Only widen the bind address
behind an authenticating proxy. Held-out deal packages (``data/holdout``) are
not listed, and a holdout path is refused, unless ``QOE_SHOW_HOLDOUT=1`` is set
for a benchmark session (docs/benchmark_protocol.md).
"""

from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import string
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent

if globals().get("__package__") in (None, ""):
    # Executed as a script by `streamlit run qoe/ui.py`: qoe/ is on sys.path, where
    # qoe/trace.py would shadow the stdlib module, and `qoe` must resolve from the root.
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None  # type: ignore[assignment]

from qoe import TOOL_VERSION
from qoe.money import CENT, D, period_map
from qoe.review_store import (
    QUESTION_LOG_NAME,
    STATUS_AGREED,
    STATUS_OVERRIDDEN,
    STATUS_UNREVIEWED,
    TIMING_LOG_NAME,
    ConflictError,
    DecisionError,
    QuestionLogEntry,
    ReviewStore,
    accept_carries_proposal,
    append_timing,
    apply_question_updates,
    apply_reviews,
    bridge_display_rows,
    bridge_row_adj_id,
    bridge_ties,
    check_bridge_identity,
    corrections_summary,
    decision_is_stale,
    decision_problems,
    decision_token,
    encode_question_update,
    final_amounts,
    is_diligence_item,
    is_item_row,
    latest_by_adj,
    load_timing,
    make_decision,
    make_question_update,
    merge_logs,
    question_token,
    questions_after,
    resolve_amounts,
    review_status,
    timing_summary,
)
from qoe.schemas import (
    AdjustmentAssessment,
    AdjustmentCategory,
    CorrectionType,
    DataQualityIssue,
    DealPackage,
    DocFacts,
    EbitdaBridge,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    GLEntry,
    GLLink,
    ManagementSchedule,
    OpenQuestion,
    PeriodDef,
    QuestionStatus,
    ReconciliationResult,
    ReviewDecision,
    Severity,
    Treatment,
    Workpaper,
)

EXPORT_STAMP_NAME = "export_build.json"
DATA_ROOT = PROJECT_ROOT / "data"
DEV_SPLIT = "dev"
HOLDOUT_SPLIT = "holdout"
DEAL_SPLITS = (DEV_SPLIT,)  # holdout is opt-in: see show_holdout()
SHOW_HOLDOUT_ENV = "QOE_SHOW_HOLDOUT"

PAGES = ("Overview", "Adjustment queue", "Adjustment detail", "Open questions", "Export")

TREATMENT_LABELS = {
    Treatment.ACCEPT: "Accept",
    Treatment.REVISE: "Revise",
    Treatment.REJECT: "Reject",
    Treatment.REQUEST_INFO: "Request info",
}
# (background, text) pairs; the same families as the Excel treatment fills.
TREATMENT_COLORS = {
    Treatment.ACCEPT: ("#E2EFDA", "#375623"),
    Treatment.REVISE: ("#FFF2CC", "#7F6000"),
    Treatment.REJECT: ("#F4CCCC", "#842A1C"),
    Treatment.REQUEST_INFO: ("#DDE3EA", "#2F3E50"),
}
SEVERITY_COLORS = {
    Severity.CRITICAL: ("#F4CCCC", "#842A1C"),
    Severity.WARNING: ("#FFF2CC", "#7F6000"),
    Severity.INFO: ("#E7E9EC", "#3C4650"),
}
SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

CATEGORY_LABELS = {
    AdjustmentCategory.NON_RECURRING: "Non-recurring",
    AdjustmentCategory.OWNER_DISCRETIONARY: "Owner / discretionary",
    AdjustmentCategory.NORMALIZATION: "Normalization",
    AdjustmentCategory.OUT_OF_PERIOD: "Out-of-period",
    AdjustmentCategory.PRO_FORMA: "Pro forma",
    AdjustmentCategory.OTHER: "Other",
}

CORRECTION_LABELS = {
    CorrectionType.NONE: "None: agrees with the tool",
    CorrectionType.TOOL_WRONG_LINK: "Tool error: wrong GL or document link",
    CorrectionType.TOOL_MISSED_EVIDENCE: "Tool error: missed evidence",
    CorrectionType.TOOL_WRONG_AMOUNT: "Tool error: wrong amount",
    CorrectionType.TOOL_WRONG_FLAG: "Tool error: wrong or missing flag",
    CorrectionType.TOOL_WRONG_TREATMENT: "Tool error: wrong treatment",
    CorrectionType.JUDGMENT_DIFFERENCE: "Judgment difference (not a tool error)",
    CorrectionType.NEW_INFORMATION: "New information (not available to the tool)",
}

GROUP_MANAGEMENT = "Management adjustments"
GROUP_DILIGENCE = "Diligence-identified items"
DILIGENCE_NOTE = "Not on management's schedule: identified by the tool; management claimed nothing."

BRIDGE_SUMMARY_KEYS = (
    ("gl_ebitda", "Reported EBITDA (per GL)"),
    ("mgmt_reported_ebitda", "Reported EBITDA (per management)"),
    ("mgmt_adjusted_ebitda", "Management adjusted EBITDA"),
    ("diligence_adjusted_ebitda", "Diligence adjusted EBITDA"),
)

_ACRONYMS = {"GL": "GL", "EBITDA": "EBITDA", "PL": "P&L", "MGMT": "management"}


# ---------------------------------------------------------------------------
# Paths and deal discovery
# ---------------------------------------------------------------------------


def _env_path(var: str, default: Path) -> Path:
    env = os.environ.get(var, "").strip()
    if not env:
        return default
    p = Path(env).expanduser()
    return p if p.is_absolute() else PROJECT_ROOT / p


def workpapers_root() -> Path:
    """Where runs are cached; QOE_WORKPAPERS_DIR overrides (relative to the project root)."""
    return _env_path("QOE_WORKPAPERS_DIR", PROJECT_ROOT / "workpapers")


def data_root() -> Path:
    """Deal library root holding dev/ and holdout/; QOE_DATA_DIR overrides."""
    return _env_path("QOE_DATA_DIR", DATA_ROOT)


@dataclass(frozen=True)
class WorkpaperPaths:
    root: Path  # <workpapers>/<deal_id>
    deal_id: str

    @property
    def workpaper(self) -> Path:
        return self.root / "workpaper.json"

    @property
    def review_log(self) -> Path:
        return self.root / "review_log.jsonl"

    @property
    def question_log(self) -> Path:
        return self.root / QUESTION_LOG_NAME

    @property
    def timing(self) -> Path:
        return self.root / TIMING_LOG_NAME

    @property
    def xlsx(self) -> Path:
        return self.root / f"QoE_Evidence_Review_{self.deal_id}.xlsx"

    @property
    def export_stamp(self) -> Path:
        """What the workbook on disk was built from (see ``export_status``)."""
        return self.root / EXPORT_STAMP_NAME


def workpaper_paths(deal_id: str, base: Optional[Path] = None) -> WorkpaperPaths:
    return WorkpaperPaths(root=(base or workpapers_root()) / deal_id, deal_id=deal_id)


@dataclass(frozen=True)
class DealOption:
    split: str
    deal_id: str
    target_name: str
    path: Path

    @property
    def label(self) -> str:
        return f"{self.target_name} ({self.split}: {self.deal_id})"


def read_deal_header(deal_dir: Path) -> tuple[str, str]:
    """(deal_id, target_name) from deal.yaml, falling back to the directory name."""
    import yaml

    try:
        data = yaml.safe_load((Path(deal_dir) / "deal.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        data = None
    if not isinstance(data, dict):
        data = {}
    name = Path(deal_dir).name
    return str(data.get("deal_id") or name), str(data.get("target_name") or name)


def show_holdout() -> bool:
    """Held-out packages are listed only in a benchmark session that opts in with
    QOE_SHOW_HOLDOUT=1: the developer must not see them before code freeze."""
    return os.environ.get(SHOW_HOLDOUT_ENV, "").strip() == "1"


def deal_splits() -> tuple[str, ...]:
    return DEAL_SPLITS + ((HOLDOUT_SPLIT,) if show_holdout() else ())


def is_holdout_path(path: Path, root_dir: Optional[Path] = None) -> bool:
    """True for a directory inside ``<data root>/holdout`` (after resolving symlinks)."""
    holdout = (Path(root_dir or data_root()) / HOLDOUT_SPLIT).resolve()
    try:
        Path(path).resolve().relative_to(holdout)
    except ValueError:
        return False
    return True


def discover_deals(root_dir: Optional[Path] = None, splits: Optional[Iterable[str]] = None) -> list[DealOption]:
    """Deal packages under the data root, dev only unless holdout is opted into."""
    out: list[DealOption] = []
    for split in splits if splits is not None else deal_splits():
        root = Path(root_dir or data_root()) / split
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if (p / "deal.yaml").is_file()):
            deal_id, target = read_deal_header(d)
            out.append(DealOption(split=split, deal_id=deal_id, target_name=target, path=d))
    return out


def find_deal_dir(deal_id: str, root_dir: Optional[Path] = None) -> Optional[Path]:
    for opt in discover_deals(root_dir):
        if opt.deal_id == deal_id:
            return opt.path
    return None


def resolve_user_path(raw: str) -> Path:
    p = Path(raw.strip()).expanduser()
    return p if p.is_absolute() else PROJECT_ROOT / p


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

_WHOLE = Decimal("1")


def fmt_amount(value: object, cents: bool = False) -> str:
    """Workpaper style: 1,234 / (1,234) / "-" for zero; "" for blank."""
    if value is None or value == "":
        return ""
    try:
        d = D(value)
    except (TypeError, ValueError):
        return str(value)
    q = d.quantize(CENT if cents else _WHOLE, rounding=ROUND_HALF_UP)
    if q == 0:
        return "-"
    body = format(abs(q), ",.2f" if cents else ",.0f")
    return f"({body})" if q < 0 else body


def fmt_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


def humanize_code(code: object) -> str:
    """FLAG_CODE -> "Flag code", keeping GL / EBITDA / P&L."""
    raw = getattr(code, "value", code)
    words = [w for w in str(raw).split("_") if w]
    text = " ".join(_ACRONYMS.get(w, w.lower()) for w in words)
    return text[:1].upper() + text[1:]


def gl_row_of(entry_id: str) -> Optional[int]:
    if entry_id.startswith("GL-R") and entry_id[4:].isdigit():
        return int(entry_id[4:])
    return None


def gl_rows_text(entry_ids: Iterable[str]) -> str:
    """ "GL rows 12, 40" for GL-R ids; other ids are listed verbatim."""
    ids = list(entry_ids)
    if not ids:
        return ""
    parts = [str(gl_row_of(e)) if gl_row_of(e) is not None else e for e in ids]
    return ("GL row " if len(parts) == 1 else "GL rows ") + ", ".join(parts)


def category_label(category: AdjustmentCategory) -> str:
    return CATEGORY_LABELS.get(category, str(category.value))


def _esc(text: object) -> str:
    # "$" is escaped too: Streamlit renders $...$ as LaTeX in markdown contexts.
    return html.escape(str(text), quote=True).replace("$", "&#36;")


_MD_SPECIAL = re.compile("([" + re.escape(string.punctuation) + "])")


def md(text: object) -> str:
    """Text made inert for Streamlit's Markdown (st.success / caption / warning / title and
    widget labels): every ASCII punctuation character is backslash-escaped, so seller- or
    model-written text (an adjustment Ref, a question, an exception message) cannot render
    links, images, colour directives, emoji codes or LaTeX. Newlines become spaces."""
    return _MD_SPECIAL.sub(r"\\\1", " ".join(str(text).split()))


# First characters that make Excel / LibreOffice / Sheets read a CSV cell as a formula
# (and their full-width forms, which some spreadsheet apps normalize).
_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\n", "\uff1d", "\uff0b", "\uff0d", "\uff20")


def csv_safe(value: object) -> object:
    """A CSV cell that cannot be evaluated as a formula: text whose first (non-blank)
    character is a formula trigger gets a leading apostrophe (OWASP CSV injection)."""
    if not isinstance(value, str):
        return value
    head = value.lstrip(" ")
    if value.startswith(_FORMULA_TRIGGERS) or head.startswith(_FORMULA_TRIGGERS):
        return "'" + value
    return value


def csv_bytes(rows: Iterable[Mapping[str, Any]], columns: list[str]) -> bytes:
    """UTF-8 CSV of ``columns`` with every cell passed through ``csv_safe``."""
    import csv

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([csv_safe(c) for c in columns])
    for r in rows:
        writer.writerow([csv_safe(r.get(c, "")) for c in columns])
    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# HTML fragments (rendered with st.html)
# ---------------------------------------------------------------------------


def chip(text: str, bg: str, fg: str) -> str:
    return f'<span class="qoe-chip" style="background:{bg};color:{fg}">{_esc(text)}</span>'


def treatment_chip(treatment: Treatment, prefix: str = "") -> str:
    bg, fg = TREATMENT_COLORS[treatment]
    return chip(f"{prefix}{TREATMENT_LABELS[treatment]}", bg, fg)


def severity_chip(severity: Severity) -> str:
    bg, fg = SEVERITY_COLORS[severity]
    return chip(severity.value.capitalize(), bg, fg)


def html_table(
    columns: list[str],
    rows: Iterable[Mapping[str, Any]],
    numeric: Iterable[str] = (),
    class_key: str = "_class",
) -> str:
    """A compact, escaped HTML table; a row's ``_class`` becomes its CSS class."""
    num = set(numeric)
    head = "".join(f'<th class="{"num" if c in num else ""}">{_esc(c)}</th>' for c in columns)
    body = []
    for r in rows:
        cls = _esc(r.get(class_key, ""))
        cells = "".join(f'<td class="{"num" if c in num else ""}">{_esc(r.get(c, ""))}</td>' for c in columns)
        body.append(f'<tr class="{cls}">{cells}</tr>')
    return f'<table class="qoe"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def quote_html(q: EvidenceQuote) -> str:
    return (
        f'<div class="qoe-quote">&ldquo;{_esc(q.quote)}&rdquo;'
        f'<div class="qoe-src">{_esc(q.doc_id)}, p. {q.page}</div></div>'
    )


def facts_html(facts: Iterable[Fact]) -> str:
    items = []
    for f in facts:
        parts = [f'<div class="qoe-item"><div>{_esc(f.text)}</div>']
        if f.entry_ids:
            parts.append(f'<div class="qoe-src">{_esc(gl_rows_text(f.entry_ids))}</div>')
        parts.extend(quote_html(q) for q in f.quotes)
        parts.append("</div>")
        items.append("".join(parts))
    return "".join(items) or '<div class="qoe-muted">The tool recorded no documented facts.</div>'


def sorted_flags(flags: Iterable[Flag]) -> list[Flag]:
    return sorted(flags, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.code.value, f.period_label or ""))


# What a flag's ``amount_impact`` measures when the flag does not move the proposed
# amount (its ``effects`` are empty). Only ``Flag.effects`` is shown as an EBITDA effect.
FLAG_AMOUNT_LABELS = {
    FlagCode.EXCESS_GL_ACTIVITY: "Context activity (not claimed)",
    FlagCode.PARTIAL_GL_SUPPORT: "GL shortfall",
}
FLAG_AMOUNT_DEFAULT_LABEL = "Amount at issue"


def flag_amount_notes(f: Flag, labels: Optional[Iterable[str]] = None) -> list[str]:
    """Amount chips for a flag: "EBITDA effect <period> <amount>" for each period whose
    proposed amount the flag changes (``Flag.effects``), else the flag's ``amount_impact``
    under a label that says what it measures (context activity is not an EBITDA effect)."""
    order = list(labels or [])
    effects = {k: v for k, v in f.effects.items() if D(v) != 0}
    if effects:
        keys = [k for k in order if k in effects] + [k for k in effects if k not in order]
        return [f"EBITDA effect {k} {fmt_amount(effects[k])}" for k in keys]
    if f.amount_impact in (None, "") or D(f.amount_impact) == 0:
        return []
    label = FLAG_AMOUNT_LABELS.get(f.code, FLAG_AMOUNT_DEFAULT_LABEL)
    return [f"{label} {fmt_amount(f.amount_impact)}"]


def flag_html(f: Flag, labels: Optional[Iterable[str]] = None) -> str:
    head = [severity_chip(f.severity), f"<b>{_esc(humanize_code(f.code))}</b>"]
    if f.period_label:
        head.append(f'<span class="qoe-src">{_esc(f.period_label)}</span>')
    for note in flag_amount_notes(f, labels):
        head.append(f'<span class="qoe-src">{_esc(note)}</span>')
    meta = []
    if f.entry_ids:
        meta.append(gl_rows_text(f.entry_ids))
    if f.doc_ids:
        meta.append("Documents: " + ", ".join(f.doc_ids))
    if f.related_adj_ids:
        meta.append("Related: " + ", ".join(f.related_adj_ids))
    parts = [f'<div class="qoe-item">{" ".join(head)}<div>{_esc(f.message)}</div>']
    if meta:
        parts.append(f'<div class="qoe-src">{_esc(" | ".join(meta))}</div>')
    parts.extend(quote_html(q) for q in f.quotes)
    parts.append("</div>")
    return "".join(parts)


def highlight_quotes(page_text: str, quotes: Iterable[str]) -> str:
    """HTML-escaped page text with every occurrence of each quote wrapped in <mark>."""
    spans: list[tuple[int, int]] = []
    for q in quotes:
        if not q:
            continue
        start = 0
        while True:
            i = page_text.find(q, start)
            if i < 0:
                break
            spans.append((i, i + len(q)))
            start = i + len(q)
    spans.sort()
    merged: list[list[int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out, pos = [], 0
    for s, e in merged:
        out.append(_esc(page_text[pos:s]))
        out.append(f"<mark>{_esc(page_text[s:e])}</mark>")
        pos = e
    out.append(_esc(page_text[pos:]))
    return "".join(out)


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------


def _row_map(bridge: EbitdaBridge) -> dict[str, Any]:
    return {r.key: r for r in bridge.rows}


def diligence_ids(wp: Workpaper) -> set[str]:
    return {a.adj_id for a in wp.assessments if is_diligence_item(a)}


def ordered_bridge_rows(bridge: EbitdaBridge, item_ids: Iterable[str] = ()) -> list[Any]:
    """Bridge rows with diligence-identified items as their own block (same order as the workbook)."""
    return bridge_display_rows(bridge.rows, item_ids)


def bridge_summary_rows(bridge: EbitdaBridge, item_ids: Iterable[str] = ()) -> list[dict[str, Any]]:
    """GL reported / management reported / management adjusted / diligence adjusted, then the
    difference, with the diligence-identified items (``dil:<D-n>`` rows) shown beneath it."""
    rows = _row_map(bridge)
    out: list[dict[str, Any]] = []
    for key, label in BRIDGE_SUMMARY_KEYS:
        r = rows.get(key)
        rec: dict[str, Any] = {"Line": label, "_class": "subtotal"}
        for p in bridge.period_labels:
            rec[p] = fmt_amount(r.amounts.get(p)) if r is not None else "n/a"
        out.append(rec)
    mgmt, dil = rows.get("mgmt_adjusted_ebitda"), rows.get("diligence_adjusted_ebitda")
    if mgmt is not None and dil is not None:
        rec = {"Line": "Diligence less management adjusted", "_class": "memo"}
        for p in bridge.period_labels:
            rec[p] = fmt_amount(D(dil.amounts.get(p)) - D(mgmt.amounts.get(p)))
        out.append(rec)
    ids = set(item_ids)
    for r in bridge.rows:
        if is_item_row(r, ids):
            rec = {"Line": f"of which {bridge_row_adj_id(r)}: {r.label}", "_class": "memo"}
            for p in bridge.period_labels:
                rec[p] = fmt_amount(r.amounts.get(p))
            out.append(rec)
    return out


def bridge_rows(bridge: EbitdaBridge, item_ids: Iterable[str] = ()) -> list[dict[str, Any]]:
    """Every bridge row, with diligence-identified items as their own block (a heading row first)."""
    ids = set(item_ids)
    out = []
    heading = False
    for r in ordered_bridge_rows(bridge, ids):
        if is_item_row(r, ids) and not heading:
            out.append({"Line": f"{GROUP_DILIGENCE} (not on management's schedule): final amount", "_class": "group"})
            heading = True
        rec: dict[str, Any] = {"Line": r.label, "_class": r.kind}
        for p in bridge.period_labels:
            rec[p] = fmt_amount(r.amounts.get(p))
        out.append(rec)
    return out


def top_flags(a: AdjustmentAssessment, n: int = 3) -> str:
    seen: list[str] = []
    for f in sorted_flags(a.flags):
        label = humanize_code(f.code)
        if label not in seen:
            seen.append(label)
    more = f" (+{len(seen) - n})" if len(seen) > n else ""
    return ", ".join(seen[:n]) + more


def _open_question_count(a: AdjustmentAssessment) -> int:
    return sum(1 for q in a.open_questions if q.status == QuestionStatus.OPEN)


def queue_columns(labels: list[str], all_columns: bool = True) -> list[str]:
    """Queue columns. The compact set (the default view) keeps what a reviewer scans:
    the item, the treatments, where it stands, the final amounts, flags and questions."""
    if not all_columns:
        return ["Ref", "Title", "Tool", "Reviewer", "Status", "Bridge", *(f"Final {p}" for p in labels), "Top flags", "Open Qs"]
    cols = ["Ref", "Title", "Category", "Tool", "Reviewer", "Status", "Bridge"]
    for prefix in ("Claimed", "Proposed", "Final"):
        cols.extend(f"{prefix} {p}" for p in labels)
    return cols + ["Top flags", "Confidence", "GL links", "Supporting GL links", "Docs", "Open Qs"]


BRIDGE_EXCLUDED = "Excluded (pending)"
BRIDGE_AT_ZERO = "Carried at 0"
BRIDGE_CARRIED = "Carried"
DRAFT_SUFFIX = " (unsent draft)"


def bridge_status(final: Mapping[str, str]) -> str:
    """How the item reaches diligence adjusted EBITDA: excluded while pending, carried at
    zero (rejected), or carried at an amount."""
    if not final:
        return BRIDGE_EXCLUDED
    if all(D(v) == 0 for v in final.values()):
        return BRIDGE_AT_ZERO
    return BRIDGE_CARRIED


def queue_rows(
    wp: Workpaper,
    latest: Mapping[str, ReviewDecision],
    finals: Mapping[str, dict[str, str]],
    tolerance: object = "1.00",
    drafts: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """One row per adjustment. ``drafts`` are adj ids with unsent form edits."""
    labels = [p.label for p in wp.deal.periods]
    drafted = set(drafts)
    out = []
    for a in wp.assessments:
        d = latest.get(a.adj_id)
        final = finals.get(a.adj_id, {})
        status = review_status(a, d, tolerance)
        if d is not None and decision_is_stale(a, d, tolerance):
            status += " (tool proposal changed since review)"
        if a.adj_id in drafted:
            status += DRAFT_SUFFIX
        rec: dict[str, Any] = {
            "_group": GROUP_DILIGENCE if is_diligence_item(a) else GROUP_MANAGEMENT,
            "Ref": a.adj_id,
            "Title": a.title,
            "Category": category_label(a.category),
            "Tool": TREATMENT_LABELS[a.treatment],
            "Reviewer": TREATMENT_LABELS[d.treatment] if d is not None else "",
            "Status": status,
            "Bridge": bridge_status(final),
        }
        for p in labels:
            rec[f"Claimed {p}"] = fmt_amount(a.claimed.get(p, "0"))
        for p in labels:
            rec[f"Proposed {p}"] = fmt_amount(a.proposed.get(p, "0")) if a.proposed else "pending"
        for p in labels:
            rec[f"Final {p}"] = fmt_amount(final.get(p)) if final else "pending"
        rec["Top flags"] = top_flags(a)
        rec["Confidence"] = a.confidence
        # Same two counts, and labels, as the workbook's Adjustment Summary.
        rec["GL links"] = len(a.gl_links)
        rec["Supporting GL links"] = sum(1 for g in a.gl_links if link_role(g)[0] in CARRIED_ROLES)
        rec["Docs"] = len(a.doc_links)
        rec["Open Qs"] = _open_question_count(a)
        out.append(rec)
    return out


def queue_groups(rows: Iterable[Mapping[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    """(group title, rows): management's items first, then diligence-identified items; empty groups dropped
    (management's group is kept, even when empty, so the queue always says what it holds)."""
    groups: dict[str, list[dict[str, Any]]] = {GROUP_MANAGEMENT: [], GROUP_DILIGENCE: []}
    for r in rows:
        groups[r.get("_group", GROUP_MANAGEMENT)].append(dict(r))
    return [(g, rs) for g, rs in groups.items() if rs or g == GROUP_MANAGEMENT]


def claim_details(
    a: AdjustmentAssessment, pkg: Optional[DealPackage], schedule: Optional[ManagementSchedule] = None
) -> dict[str, Any]:
    """Management's narrative for the detail page: the deal package's schedule when loaded, else the
    schedule stored on the workpaper, else the fields the assessment itself carries."""
    if is_diligence_item(a):
        return {
            "heading": "Diligence-identified item: basis",
            "description": a.description,
            "bits": [
                DILIGENCE_NOTE,
                "GL accounts: " + (", ".join(a.gl_accounts) if a.gl_accounts else "none recorded"),
                "Support: " + (", ".join(a.support_refs) if a.support_refs else "see the documents tab"),
            ],
        }
    sched = pkg.schedule if pkg is not None else schedule
    claim = next((c for c in sched.adjustments if c.adj_id == a.adj_id), None) if sched is not None else None
    heading = "Management's claim and basis"
    if claim is None:
        bits: list[str] = []
        if a.description or a.gl_accounts or a.support_refs:
            bits.append("GL accounts: " + (", ".join(a.gl_accounts) if a.gl_accounts else "none given"))
            bits.append("Support: " + (", ".join(a.support_refs) if a.support_refs else "none cited"))
        return {"heading": heading, "description": a.description, "bits": bits}
    bits = []
    if claim.category_raw:
        bits.append(f"Category as presented: {claim.category_raw}")
    bits.append("GL accounts: " + (", ".join(claim.gl_accounts) if claim.gl_accounts else "none given"))
    bits.append("Support: " + (", ".join(claim.support_refs) if claim.support_refs else "none cited"))
    bits.append(f"Schedule row {claim.source_row}")
    return {"heading": heading, "description": claim.description or a.description, "bits": bits}


def tieout_rows(
    a: AdjustmentAssessment, final: Optional[Mapping[str, str]], labels: list[str], reviewed: bool
) -> list[dict[str, Any]]:
    """Claimed / traced GL / documented / proposed / final by period, with the
    differences a reviewer ties out."""

    def amounts(values: Mapping[str, str]) -> dict[str, str]:
        return {p: fmt_amount(values.get(p, "0")) for p in labels}

    def diff(x: Mapping[str, str], y: Mapping[str, str]) -> dict[str, str]:
        return {p: fmt_amount(D(x.get(p)) - D(y.get(p))) for p in labels}

    pending = {p: "pending" for p in labels}
    rows: list[dict[str, Any]] = [
        {"Line": "Claimed by management", **amounts(a.claimed), "_class": "subtotal"},
        {"Line": "Traced to GL", **amounts(a.traced_gl)},
        {"Line": "Traced less claimed", **diff(a.traced_gl, a.claimed), "_class": "memo"},
        {"Line": "Documented (portion of traced)", **amounts(a.documented)},
        {"Line": "Tool proposed", **(amounts(a.proposed) if a.proposed else pending)},
        {
            "Line": "Final (reviewed)" if reviewed else "Final (unreviewed: tool proposal)",
            **(amounts(final) if final else pending),
            "_class": "subtotal",
        },
        {"Line": "Final less claimed", **(diff(final, a.claimed) if final else pending), "_class": "memo"},
    ]
    return rows


def flags_by_entry(a: AdjustmentAssessment) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in sorted_flags(a.flags):
        for e in f.entry_ids:
            label = humanize_code(f.code)
            if label not in out.setdefault(e, []):
                out[e].append(label)
    return out


ROLE_SUPPORTING = "supporting"
ROLE_MOVED = "moved"
ROLE_REMOVED = "removed"
ROLE_RECOVERY = "recovery"
ROLE_CONTEXT = "context"
ROLE_ORDER = {ROLE_SUPPORTING: 0, ROLE_MOVED: 1, ROLE_REMOVED: 2, ROLE_RECOVERY: 3, ROLE_CONTEXT: 4}
CLAIMED_ROLES = (ROLE_SUPPORTING, ROLE_MOVED, ROLE_REMOVED)
CARRIED_ROLES = (ROLE_SUPPORTING, ROLE_MOVED)  # claimed and still carried: the workbook's "supporting"
_REMOVED_REASON = re.compile(r"^Removed \(([A-Z_]+)\)")


def link_role(link: GLLink) -> tuple[str, Optional[FlagCode]]:
    """(role, removing flag) of a GL link: ``GLLink.role`` / ``removed_by`` when the engine
    set them; for an older workpaper, inferred from ``supports_claim`` and the
    "Removed (<FLAG>): ..." reason the engine writes on a claimed entry it took out."""
    if link.role:
        return link.role, link.removed_by
    if link.supports_claim:
        return ROLE_SUPPORTING, None
    for reason in link.reasons:
        m = _REMOVED_REASON.match(reason)
        if m:
            try:
                return ROLE_REMOVED, FlagCode(m.group(1))
            except ValueError:
                return ROLE_REMOVED, None
    return ROLE_CONTEXT, None


def link_is_claimed(link: GLLink) -> bool:
    """Management's claimed amount includes this entry (whether or not the tool carried it)."""
    return link.claimed or link_role(link)[0] in CLAIMED_ROLES


def role_label(role: str, removed_by: Optional[FlagCode] = None) -> str:
    if role == ROLE_SUPPORTING:
        return "Supporting (claimed, carried)"
    if role == ROLE_MOVED:
        return "Claimed, carried in another period"
    if role == ROLE_REMOVED:
        return f"Claimed, removed by {humanize_code(removed_by)}" if removed_by is not None else "Claimed, removed by a challenge"
    if role == ROLE_RECOVERY:
        return "Recovery (offsets the claim)"
    if role == ROLE_CONTEXT:
        return "Context (not part of the claim)"
    return humanize_code(role.upper())


def gl_role_counts(a: AdjustmentAssessment) -> dict[str, int]:
    """Role label -> number of linked entries, in role order."""
    out: dict[str, int] = {}
    for link in sorted(a.gl_links, key=lambda g: ROLE_ORDER.get(link_role(g)[0], 9)):
        label = role_label(*link_role(link))
        out[label] = out.get(label, 0) + 1
    return out


def _month_in(month: str, period: PeriodDef) -> bool:
    return period.start <= month[:7] <= period.end


def claimed_link_tieout(a: AdjustmentAssessment, periods: Iterable[PeriodDef]) -> list[dict[str, Any]]:
    """The GL listing's claimed entries (supporting, moved and removed) summed by GL month
    into each period, against the tie-out's "Traced to GL", so the table ties."""
    periods = list(periods)
    labels = [p.label for p in periods]
    listed = {p.label: sum((D(g.amount) for g in a.gl_links if link_is_claimed(g) and _month_in(g.period, p)), D(0)) for p in periods}
    carried = {
        p.label: sum((D(g.amount) for g in a.gl_links if link_role(g)[0] in CARRIED_ROLES and _month_in(g.period, p)), D(0))
        for p in periods
    }
    return [
        {"Line": "Claimed entries listed (by GL month)", **{p: fmt_amount(listed[p]) for p in labels}},
        {"Line": "of which still carried", **{p: fmt_amount(carried[p]) for p in labels}, "_class": "memo"},
        {"Line": "Traced to GL (tie-out)", **{p: fmt_amount(a.traced_gl.get(p, "0")) for p in labels}, "_class": "subtotal"},
        {"Line": "Difference", **{p: fmt_amount(listed[p] - D(a.traced_gl.get(p))) for p in labels}, "_class": "memo"},
    ]


def gl_link_rows(a: AdjustmentAssessment, gl_by_id: Mapping[str, GLEntry]) -> list[dict[str, Any]]:
    challenged = flags_by_entry(a)

    def sort_key(link: GLLink) -> tuple:
        e = gl_by_id.get(link.entry_id)
        return (ROLE_ORDER.get(link_role(link)[0], 9), e.date if e else link.period, link.entry_id)

    out = []
    for link in sorted(a.gl_links, key=sort_key):
        e = gl_by_id.get(link.entry_id)
        out.append(
            {
                "GL row": e.source_row if e is not None else (gl_row_of(link.entry_id) or ""),
                "Date": e.date if e is not None else link.period,
                "Account": f"{e.account} {e.account_name}" if e is not None else "",
                "Counterparty": e.counterparty if e is not None else "",
                "Doc #": e.doc_number if e is not None else "",
                "Memo": e.memo if e is not None else "",
                "Amount": fmt_amount(link.amount, cents=True),
                "Role": role_label(*link_role(link)),
                "Challenged by": ", ".join(challenged.get(link.entry_id, [])),
                "Group": link.group,
                "Score": f"{link.score:.2f}",
                "Why linked": "; ".join(link.reasons),
                "Documents": ", ".join(link.doc_ids),
            }
        )
    return out


def recurrence_rows(a: AdjustmentAssessment, labels: list[str]) -> list[dict[str, Any]]:
    out = []
    for r in a.recurrence:
        rec: dict[str, Any] = {"Group": r.group}
        keys = labels + [k for k in r.amounts_by_period if k not in labels]
        for p in keys:
            rec[p] = fmt_amount(r.amounts_by_period.get(p, "0"))
        rec["Entries"] = len(r.entry_ids)
        rec["Note"] = r.note
        out.append(rec)
    return out


def quotes_for_doc(a: AdjustmentAssessment, doc_id: str) -> dict[int, list[str]]:
    """page -> quotes cited from this document anywhere in the assessment."""
    quotes: list[EvidenceQuote] = []
    for link in a.doc_links:
        quotes.extend(link.quotes)
    for f in a.facts:
        quotes.extend(f.quotes)
    for f in a.flags:
        quotes.extend(f.quotes)
    out: dict[int, list[str]] = {}
    for q in quotes:
        if q.doc_id == doc_id and q.quote not in out.setdefault(q.page, []):
            out[q.page].append(q.quote)
    return out


def doc_facts_line(df: Optional[DocFacts]) -> str:
    if df is None:
        return ""
    parts = [humanize_code(df.doc_type.upper())]
    if df.doc_date:
        parts.append(f"dated {df.doc_date}")
    if df.counterparty:
        parts.append(df.counterparty)
    if df.reference_numbers:
        parts.append("ref " + ", ".join(df.reference_numbers))
    if df.service_period_start or df.service_period_end:
        parts.append(f"service period {df.service_period_start or '?'} to {df.service_period_end or '?'}")
    if df.is_draft:
        parts.append("DRAFT")
    if df.is_signed is True:
        parts.append("signed")
    elif df.is_signed is False:
        parts.append("unsigned")
    if df.dropped_quotes:
        parts.append(f"{df.dropped_quotes} unverifiable quote(s) dropped")
    return " | ".join(parts)


def question_rows(wp: Workpaper, question_log: Iterable[QuestionLogEntry] = ()) -> list[dict[str, Any]]:
    """Every question for management; "Last update" names who last changed it in the question log."""
    last: dict[str, QuestionLogEntry] = {}
    for e in question_log:
        last[e.q_id] = e
    out = []
    for a in wp.assessments:
        for q in a.open_questions:
            e = last.get(q.q_id)
            out.append(
                {
                    "Q id": q.q_id,
                    "Ref": q.adj_id or a.adj_id,
                    "Question": q.text,
                    "Priority": q.priority,
                    "Basis": q.basis,
                    "Status": q.status.value,
                    "Response": q.response,
                    "Last update": f"{e.reviewer}, {e.timestamp}" if e is not None else "",
                }
            )
    return out


# The information request list sent to management: no internal basis (flag codes,
# "ai:..." provenance) and no reviewer names.
REQUEST_LIST_COLUMNS = ["Q id", "Ref", "Question", "Priority", "Status", "Response"]


def filter_question_rows(
    rows: Iterable[Mapping[str, Any]],
    statuses: Iterable[str] = (),
    priorities: Iterable[str] = (),
    refs: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Rows matching every non-empty filter, high priority first. An empty result stays
    empty: it never falls back to the unfiltered list."""
    st_, pr_, rf_ = set(statuses), set(priorities), set(refs)
    shown = [
        dict(r)
        for r in rows
        if (not st_ or r["Status"] in st_) and (not pr_ or r["Priority"] in pr_) and (not rf_ or r["Ref"] in rf_)
    ]
    shown.sort(key=lambda r: PRIORITY_ORDER.get(r["Priority"], 9))
    return shown


def request_list_csv(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """The management-facing CSV: exactly ``rows``, request columns only, formula-safe."""
    return csv_bytes(rows, REQUEST_LIST_COLUMNS)


def issue_rows(recon: ReconciliationResult) -> list[dict[str, Any]]:
    def key(i: DataQualityIssue) -> tuple:
        return (SEVERITY_ORDER.get(i.severity, 9), i.code.value, i.month or "", i.account or "")

    return [
        {
            "Severity": i.severity.value.capitalize(),
            "Issue": humanize_code(i.code),
            "Month": i.month or "",
            "Account": i.account or "",
            "Period": i.period_label or "",
            "Amount": fmt_amount(i.amount, cents=True) if i.amount not in (None, "") else "",
            "Detail": i.message,
            "GL rows": gl_rows_text(i.entry_ids),
        }
        for i in sorted(recon.issues, key=key)
    ]


def ebitda_check_rows(wp: Workpaper) -> list[dict[str, Any]]:
    """GL-derived vs management-reported EBITDA by period."""
    out = []
    for p in wp.deal.periods:
        comp = wp.reconciliation.gl_ebitda.get(p.label)
        gl = comp.ebitda if comp is not None else None
        mgmt = wp.reconciliation.mgmt_reported_ebitda.get(p.label)
        out.append(
            {
                "Period": p.label,
                "GL EBITDA": fmt_amount(gl) if gl is not None else "n/a",
                "Management reported": fmt_amount(mgmt) if mgmt is not None else "n/a",
                "Management less GL": fmt_amount(D(mgmt) - D(gl)) if gl is not None and mgmt is not None else "n/a",
            }
        )
    return out


def status_counts(
    wp: Workpaper,
    latest: Mapping[str, ReviewDecision],
    finals: Mapping[str, dict[str, str]],
    tolerance: object = "1.00",
) -> dict[str, Any]:
    tool = {t.value: 0 for t in Treatment}
    review = {STATUS_UNREVIEWED: 0, STATUS_AGREED: 0, STATUS_OVERRIDDEN: 0}
    final_treatment = {t.value: 0 for t in Treatment}
    for a in wp.assessments:
        tool[a.treatment.value] += 1
        d = latest.get(a.adj_id)
        review[review_status(a, d, tolerance)] += 1
        final_treatment[(d.treatment if d is not None else a.treatment).value] += 1
    return {
        "total": len(wp.assessments),
        "reviewed": review[STATUS_AGREED] + review[STATUS_OVERRIDDEN],
        "tool": tool,
        "review": review,
        "final_treatment": final_treatment,
        "pending": sum(1 for a in wp.assessments if not finals.get(a.adj_id)),
        "diligence_items": sum(1 for a in wp.assessments if is_diligence_item(a)),
        "open_questions": sum(_open_question_count(a) for a in wp.assessments),
        "stale": sum(
            1 for a in wp.assessments if a.adj_id in latest and decision_is_stale(a, latest[a.adj_id], tolerance)
        ),
        # Pending items with nothing asked of management (e.g. from a log written before
        # Request info required a question): the request list would never unblock them.
        "pending_without_question": [
            a.adj_id for a in wp.assessments if not finals.get(a.adj_id) and not _open_question_count(a)
        ],
    }


KIND_DECISION = "Decision"
KIND_QUESTION_UPDATE = "Question update"
KIND_QUESTION_ADDED = "Question added"


def question_entry_text(e: QuestionLogEntry) -> str:
    if e.kind == "new":
        return f"{e.q_id} ({e.priority}): {e.text}"
    parts = [e.status.value if e.status is not None else "response"]
    if e.response is not None:
        parts.append(f"response {e.response!r}" if e.response else "response cleared")
    return f"{e.q_id}: " + ", ".join(parts)


def decision_history_rows(
    decisions: Iterable[ReviewDecision], labels: list[str], question_log: Iterable[QuestionLogEntry] = ()
) -> list[dict[str, Any]]:
    """Decisions and question-log lines in one time line; question lines are labelled as
    such (they are not decisions and carry no treatment or amounts)."""
    out = []
    for item in merge_logs(list(decisions), list(question_log)):
        if isinstance(item, QuestionLogEntry):
            rec: dict[str, Any] = {
                "When (UTC)": item.timestamp,
                "Kind": KIND_QUESTION_ADDED if item.kind == "new" else KIND_QUESTION_UPDATE,
                "Reviewer": item.reviewer,
                "Treatment": "",
                "Tool": "",
                **{p: "" for p in labels},
                "Correction": "",
                "Rationale": "",
                "Question updates": question_entry_text(item),
            }
            out.append(rec)
            continue
        d = item
        rec = {
            "When (UTC)": d.timestamp,
            "Kind": KIND_DECISION,
            "Reviewer": d.reviewer,
            "Treatment": TREATMENT_LABELS[d.treatment],
            "Tool": TREATMENT_LABELS[d.tool_treatment],
        }
        for p in labels:
            rec[p] = fmt_amount(d.amounts.get(p, "0")) if d.treatment != Treatment.REQUEST_INFO else "pending"
        rec["Correction"] = humanize_code(d.correction_type) if d.correction_type != CorrectionType.NONE else ""
        rec["Rationale"] = d.rationale
        rec["Question updates"] = "; ".join(f"{k}: {v}" for k, v in d.question_updates.items())
        out.append(rec)
    return out


def form_defaults(
    a: AdjustmentAssessment, decision: Optional[ReviewDecision], labels: list[str]
) -> tuple[Treatment, dict[str, str]]:
    """Initial treatment and REVISE amounts for the review form: the reviewer's
    latest decision if there is one, else the tool's proposal (claimed when the
    tool has no amounts, i.e. REQUEST_INFO)."""
    if decision is not None:
        return decision.treatment, period_map(decision.amounts or a.proposed or a.claimed, labels)
    return a.treatment, period_map(a.proposed or a.claimed, labels)


def form_seed(a: AdjustmentAssessment, decision: Optional[ReviewDecision], labels: list[str]) -> dict[str, Any]:
    """Initial review-form values by field name. Treatment and amounts start from the
    latest decision (else the tool's proposal); rationale and correction type always
    start blank, so a re-review cannot pass validation on reasons written for a
    different decision (the previous ones are shown read-only beside the form)."""
    treatment, amounts = form_defaults(a, decision, labels)
    seed: dict[str, Any] = {
        "treatment": treatment,
        "rationale": "",
        "correction": CorrectionType.NONE,
        "newq": "",
        "newq_prio": "high",
    }
    for p in labels:
        seed[f"amt:{p}"] = amounts.get(p, "0.00")
    for q in a.open_questions:
        seed[f"q:{q.q_id}:status"] = q.status
        seed[f"q:{q.q_id}:response"] = q.response
    return seed


def form_is_dirty(state: Mapping[str, Any], adj_id: str) -> bool:
    """True when the review form for ``adj_id`` holds edits that were not recorded."""
    defaults = state.get(f"fd:{adj_id}") or {}
    return any(
        f"f:{adj_id}:{name}" in state and state[f"f:{adj_id}:{name}"] != default for name, default in defaults.items()
    )


def question_update_values(
    current: Iterable[Any], edits: Mapping[str, tuple[QuestionStatus, str]]
) -> dict[str, str]:
    """``question_updates`` entries for the questions whose status or response changed."""
    out: dict[str, str] = {}
    for q in current:
        if q.q_id not in edits:
            continue
        status, response = edits[q.q_id]
        if status != q.status or response.strip() != q.response.strip():
            value = encode_question_update(status, response)
            if response.strip() == "" and q.response.strip():
                value = f"{status.value}:"  # explicit clear of an earlier response
            out[q.q_id] = value
    return out


# ---------------------------------------------------------------------------
# Export freshness
# ---------------------------------------------------------------------------

EXPORT_MISSING = "missing"
EXPORT_CURRENT = "current"
EXPORT_STALE = "stale"
EXPORT_UNKNOWN = "unknown"


def _file_digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing"


def review_state_signature(paths: WorkpaperPaths, has_pkg: bool) -> str:
    """Fingerprint of everything the workbook is built from: the tool's run, the review
    log, the question log, and whether the deal package (GL detail) was loaded."""
    h = hashlib.sha256()
    for part in (paths.workpaper, paths.review_log, paths.question_log):
        h.update(f"{part.name}={_file_digest(part)};".encode())
    h.update(b"pkg=1" if has_pkg else b"pkg=0")
    return h.hexdigest()[:24]


def write_export_stamp(paths: WorkpaperPaths, signature: str, built_at: str) -> None:
    stat = paths.xlsx.stat()
    stamp = {
        "xlsx": paths.xlsx.name,
        "built_at": built_at,
        "signature": signature,
        "xlsx_size": stat.st_size,
        "xlsx_mtime_ns": stat.st_mtime_ns,
    }
    paths.export_stamp.write_text(json.dumps(stamp, indent=2, sort_keys=True), encoding="utf-8")


def export_status(paths: WorkpaperPaths, signature: str) -> tuple[str, Optional[str]]:
    """(status, built_at) of the workbook on disk: missing; current (built by this app
    from the decisions and questions logged now); stale (built before a later change);
    unknown (no build record, or the file was rewritten outside the app)."""
    if not paths.xlsx.is_file():
        return EXPORT_MISSING, None
    try:
        stamp = json.loads(paths.export_stamp.read_text(encoding="utf-8"))
        stat = paths.xlsx.stat()
    except (OSError, ValueError):
        return EXPORT_UNKNOWN, None
    built_at = stamp.get("built_at")
    if stamp.get("xlsx_size") != stat.st_size or stamp.get("xlsx_mtime_ns") != stat.st_mtime_ns:
        return EXPORT_UNKNOWN, built_at
    if stamp.get("signature") != signature:
        return EXPORT_STALE, built_at
    return EXPORT_CURRENT, built_at


# ---------------------------------------------------------------------------
# Time on task (session timestamps; pure so it can be tested with a dict)
# ---------------------------------------------------------------------------


def track_view(state: MutableMapping[str, Any], adj_id: Optional[str], now: datetime) -> None:
    """Close the running segment and start one for ``adj_id`` (None = away from detail).

    Time counts only while an adjustment's detail page is the one on screen, so
    moving between adjustments does not double count.
    """
    active, since = state.get("active"), state.get("since")
    if active == adj_id and (adj_id is None or since is not None):
        return
    if active is not None and since is not None:
        acc = state.setdefault("accum", {})
        acc[active] = acc.get(active, 0.0) + max(0.0, (now - since).total_seconds())
    if adj_id is not None:
        state.setdefault("opened", {}).setdefault(adj_id, now)
    state["active"] = adj_id
    state["since"] = now if adj_id is not None else None


def elapsed_seconds(state: Mapping[str, Any], adj_id: str, now: datetime) -> int:
    total = state.get("accum", {}).get(adj_id, 0.0)
    if state.get("active") == adj_id and state.get("since") is not None:
        total += max(0.0, (now - state["since"]).total_seconds())
    return int(round(total))


def finish_timing(state: MutableMapping[str, Any], adj_id: str, now: datetime) -> tuple[datetime, int]:
    """(opened_at, active seconds) for a decision just recorded; the clock restarts
    so a re-review is timed separately."""
    seconds = elapsed_seconds(state, adj_id, now)
    opened = state.get("opened", {}).pop(adj_id, now)
    state.get("accum", {}).pop(adj_id, None)
    if state.get("active") == adj_id:
        state["since"] = now
        state.setdefault("opened", {})[adj_id] = now
    return opened, seconds


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Loading (no Streamlit)
# ---------------------------------------------------------------------------


def load_workpaper_file(path: Path) -> Workpaper:
    try:
        from qoe.engine import load_workpaper
    except ImportError:
        return Workpaper.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return load_workpaper(Path(path))


def run_and_save(deal_dir: Path, ai_mode: str, out_base: Path) -> Path:
    from qoe.engine import run_review, save_workpaper

    ai = None
    try:
        from qoe.ai import get_ai

        ai = get_ai(ai_mode)
    except ImportError:
        if ai_mode != "rules":
            raise
    wp = run_review(Path(deal_dir), ai=ai)
    return save_workpaper(wp, out_base)


def read_document_pages(deal_dir: Path, doc_id: str, documents_dir: str = "documents") -> list[str]:
    """Canonical page text for one document, read straight from the deal package.

    Used only when the deal package cannot be loaded through ingest; it applies
    the same qoe.pdf_text extraction and canonicalization, so quotes still match.
    """
    from qoe.pdf_text import canonicalize_page_text, extract_pdf_pages

    root = Path(deal_dir) / documents_dir
    matches = sorted(p for p in root.rglob("*") if p.is_file() and p.name == doc_id)
    if not matches:
        return []
    path = matches[0]
    if path.suffix.lower() == ".pdf":
        return [canonicalize_page_text(t) for t in extract_pdf_pages(path)]
    return [canonicalize_page_text(path.read_text(encoding="utf-8", errors="replace"))]


def selected_ref(refs: list[str], event: Any) -> Optional[str]:
    """The adjustment a single-row dataframe selection points at (None when nothing is
    selected). ``event`` is the dataframe's selection state (dict- or attribute-style)."""
    if event is None:
        return None
    selection = event.get("selection") if isinstance(event, Mapping) else getattr(event, "selection", None)
    if selection is None:
        return None
    rows = selection.get("rows") if isinstance(selection, Mapping) else getattr(selection, "rows", None)
    if not rows:
        return None
    i = rows[0]
    return refs[i] if isinstance(i, int) and 0 <= i < len(refs) else None


def treatment_labels_for(a: AdjustmentAssessment) -> dict[Treatment, str]:
    """Treatment option labels for the review form; on a diligence-identified item they
    say what each option carries (management claimed nothing there)."""
    if accept_carries_proposal(a):
        return {
            Treatment.ACCEPT: "Accept (carry the tool's amount)",
            Treatment.REVISE: "Revise",
            Treatment.REJECT: "Reject (do not carry)",
            Treatment.REQUEST_INFO: "Request info",
        }
    return dict(TREATMENT_LABELS)


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

# Contrast (WCAG 2.1): white on #3A6EA5 is 5.3:1 and #3A6EA5 is 3.6:1 against the dark
# theme's background (Streamlit's default red is 3.3:1 with white). Captions carry
# guidance, so they use the body text colour at reduced opacity (>= 4.5:1 in both
# themes) instead of the default grey (3.7:1 on white). The diligence heading row
# inherits the theme's text colour.
PRIMARY_COLOR = "#3A6EA5"
PRIMARY_HOVER = "#2E5A88"

_CSS = f"""
<style>
.qoe-banner{{background:#FFF4E5;border:1px solid #E0A458;color:#7A4B00;padding:6px 12px;border-radius:4px;
  font-weight:600;letter-spacing:.03em;font-size:.85rem;margin-bottom:.5rem}}
.qoe-chip{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.78rem;font-weight:600;
  margin-right:6px;border:1px solid rgba(0,0,0,.08);white-space:nowrap}}
table.qoe{{border-collapse:collapse;width:100%;font-size:.88rem;margin:.25rem 0 .75rem 0}}
table.qoe th{{text-align:left;border-bottom:2px solid rgba(128,128,128,.55);padding:4px 8px;font-weight:600}}
table.qoe td{{padding:3px 8px;border-bottom:1px solid rgba(128,128,128,.18);vertical-align:top}}
table.qoe .num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
table.qoe tr.subtotal td{{font-weight:600;border-top:1px solid rgba(128,128,128,.6)}}
table.qoe tr.memo td{{font-style:italic;opacity:.8}}
table.qoe tr.group td{{font-weight:600;color:inherit;background:rgba(91,122,153,.18);border-top:2px solid #5B7A99}}
table.qoe tr.component td:first-child,table.qoe tr.mgmt_adjustment td:first-child,
table.qoe tr.diligence_adjustment td:first-child{{padding-left:22px}}
.qoe-item{{padding:6px 0 8px 0;border-bottom:1px solid rgba(128,128,128,.15)}}
.qoe-quote{{border-left:3px solid rgba(128,128,128,.55);padding:2px 10px;margin:4px 0 2px 0;font-family:Georgia,serif}}
.qoe-src{{font-size:.78rem;opacity:.8;margin-right:8px}}
.qoe-muted{{opacity:.8;font-size:.88rem}}
.qoe-evidence{{border-left:4px solid #5B8C5A;padding-left:12px}}
.qoe-judgment{{border-left:4px solid #C9A227;padding-left:12px}}
.qoe-ask{{border-left:4px solid #5B7A99;padding-left:12px}}
.qoe-page{{white-space:pre-wrap;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;line-height:1.35;
  max-height:460px;overflow:auto;border:1px solid rgba(128,128,128,.3);padding:8px;border-radius:4px}}
.qoe-page mark{{background:#FFE58F;color:#000;padding:0 1px}}
[data-testid="stCaptionContainer"]{{color:inherit !important;opacity:.85}}
[data-testid="stBaseButton-primary"]{{background-color:{PRIMARY_COLOR};border-color:{PRIMARY_COLOR};color:#FFFFFF}}
[data-testid="stBaseButton-primary"]:hover{{background-color:{PRIMARY_HOVER};border-color:{PRIMARY_HOVER};color:#FFFFFF}}
</style>
"""

# Widget keys whose values must survive runs in which their widget is not drawn:
# review-form drafts (f:<adj>:...), question-page edits and filters (oq_...), and queue
# filters (qf_...). Streamlit otherwise drops them, silently losing unsent input.
PRESERVED_KEY_PREFIXES = ("f:", "oq_", "qf_")


@dataclass
class ReviewContext:
    base: Workpaper  # the tool's run, as saved
    wp: Workpaper  # reviews applied, bridge rebuilt
    labels: list[str]
    decisions: list[ReviewDecision]
    latest: dict[str, ReviewDecision]
    finals: dict[str, dict[str, str]]
    paths: WorkpaperPaths
    deal_dir: Optional[Path]
    pkg: Optional[DealPackage]
    notes: list[str]
    question_log: list[QuestionLogEntry]
    signature: str  # review_state_signature when the logs were read

    @property
    def tolerance(self) -> str:
        return self.wp.deal.tolerance

    def assessment(self, adj_id: str) -> AdjustmentAssessment:
        for a in self.wp.assessments:
            if a.adj_id == adj_id:
                return a
        raise KeyError(adj_id)


def _cache_resource(**kwargs: Any):
    def deco(fn):
        return fn if st is None else st.cache_resource(**kwargs)(fn)

    return deco


@_cache_resource(max_entries=8, show_spinner=False)
def _load_workpaper_cached(path: str, mtime_ns: int) -> Workpaper:
    return load_workpaper_file(Path(path))


@_cache_resource(max_entries=4, show_spinner="Loading deal package (GL and documents)...")
def _load_deal_cached(deal_dir: str, fingerprint: str) -> tuple[Optional[DealPackage], Optional[str]]:
    # Failures are returned, not raised, so a broken package is not re-read on every rerun.
    try:
        from qoe.ingest import load_deal

        return load_deal(Path(deal_dir)), None
    except Exception as exc:  # noqa: BLE001 - shown to the reviewer
        return None, f"{type(exc).__name__}: {exc}"


@_cache_resource(max_entries=64, show_spinner=False)
def _document_pages_cached(deal_dir: str, doc_id: str, documents_dir: str) -> list[str]:
    try:
        return read_document_pages(Path(deal_dir), doc_id, documents_dir)
    except Exception:  # noqa: BLE001 - page text is a convenience view
        return []


def _flash(kind: str, text: str) -> None:
    st.session_state.setdefault("flash", []).append((kind, text))


def _show_flash() -> None:
    # Flash text carries adjustment refs and question ids from the seller's schedule: inert Markdown.
    for kind, text in st.session_state.pop("flash", []):
        getattr(st, kind, st.info)(md(text))


def _show_error(title: str, exc: BaseException) -> None:
    st.error(md(f"{title}: {type(exc).__name__}: {exc}"))
    with st.expander("Technical details"):
        st.code("".join(traceback.format_exception(exc)), language="text")


def _render_safely(title: str, fn: Any, *args: Any) -> None:
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001 - keep the app up; show what failed
        _show_error(f"{title} could not be displayed", exc)


ROW_PX = 35


def table_height(n_rows: int, fit_rows: Optional[int] = 25) -> Any:
    """Dataframe height: every row when there are at most ``fit_rows`` (None = always),
    else a fixed height for ``fit_rows`` rows. Streamlit's default ("auto") shows ten
    rows and hides the rest behind an inner scrollbar."""
    if fit_rows is None or n_rows <= fit_rows:
        return "content"
    return ROW_PX * (fit_rows + 1) + 3


def _table(
    rows: list[dict[str, Any]],
    numeric: Iterable[str] = (),
    color_cols: Iterable[str] = (),
    columns: Optional[list[str]] = None,
    fit_rows: Optional[int] = 25,
    key: Optional[str] = None,
    on_select: Any = None,
) -> None:
    """A dataframe sized to show its rows (up to ``fit_rows``; None = always all), so rows
    are not hidden behind an inner scrollbar. ``on_select``: a callback for a single-row
    selection (the grid's selection state is at ``st.session_state[key]``)."""
    import pandas as pd

    if not rows:
        st.caption("None.")
        return
    df = pd.DataFrame(rows)
    keep = columns or [c for c in df.columns if not str(c).startswith("_")]
    df = df[[c for c in keep if c in df.columns]]
    for c in df.columns:
        # Arrow rejects object columns that mix ints and strings (e.g. a blank GL row).
        if df[c].dtype == object and df[c].map(type).nunique() > 1:
            df[c] = df[c].astype(str)
    config = {c: st.column_config.TextColumn(c, alignment="right") for c in numeric if c in df.columns}
    data: Any = df
    colored = [c for c in color_cols if c in df.columns]
    if colored:
        by_label = {v: TREATMENT_COLORS[k] for k, v in TREATMENT_LABELS.items()}

        def style(v: Any) -> str:
            pair = by_label.get(v)
            return f"background-color:{pair[0]};color:{pair[1]};font-weight:600" if pair else ""

        data = df.style.map(style, subset=colored)
    height = table_height(len(df), fit_rows)
    kwargs: dict[str, Any] = {}
    if on_select is not None:
        kwargs = {"on_select": on_select, "selection_mode": "single-row", "key": key}
    st.dataframe(data, hide_index=True, column_config=config, height=height, **kwargs)


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("timer", {})
    ss.setdefault("form_errors", {})
    # Streamlit drops state for widgets that are not drawn in a run. Re-assigning the keys
    # turns them into session state that persists: the adjustment selection, unsent
    # review-form drafts and page filters survive Previous/Next and page switches.
    for k in [k for k in ss.keys() if isinstance(k, str) and (k == "adj_select" or k.startswith(PRESERVED_KEY_PREFIXES))]:
        ss[k] = ss[k]


def _keep_option(key: str, options: list[Any], default: Any = None) -> None:
    """Before drawing a selectbox: drop a remembered value that is no longer an option."""
    ss = st.session_state
    if key in ss and ss[key] not in options:
        del ss[key]
    if key not in ss and default is not None:
        ss[key] = default


def _open_workpaper(deal_dir: Optional[Path], wp_path: Path) -> None:
    st.session_state["deal_dir"] = str(deal_dir) if deal_dir is not None else None
    st.session_state["wp_path"] = str(wp_path)
    st.session_state.pop("_applied", None)


def _goto(page: str, adj_id: Optional[str] = None) -> None:
    st.session_state["page"] = page
    if adj_id is not None:
        st.session_state["adj_select"] = adj_id


HOLDOUT_HIDDEN_NOTE = (
    "Held-out deal packages are hidden until code freeze (docs/benchmark_protocol.md). "
    f"Set {SHOW_HOLDOUT_ENV}=1 for a benchmark session."
)


def _sidebar() -> None:
    sb = st.sidebar
    sb.markdown("**QoE Evidence Review**")
    sb.caption(f"Tool version {md(TOOL_VERSION)}. Deal packages under data are SYNTHETIC.")
    deals = discover_deals()
    source = sb.radio("Deal package", ("Library", "Path"), horizontal=True, key="deal_source")
    deal_dir: Optional[Path] = None
    if source == "Library":
        if deals:
            opt = sb.selectbox("Deal", deals, format_func=lambda o: o.label, key="deal_option")
            deal_dir = opt.path if opt is not None else None
        else:
            sb.info("No deal packages under data/dev. Enter a path instead.")
        if not show_holdout():
            sb.caption(HOLDOUT_HIDDEN_NOTE)
    else:
        raw = sb.text_input("Deal directory", key="deal_path", placeholder="data/dev/<deal_id>")
        if raw.strip():
            deal_dir = resolve_user_path(raw)
            if not show_holdout() and is_holdout_path(deal_dir):
                sb.warning(HOLDOUT_HIDDEN_NOTE)
                deal_dir = None
    if deal_dir is not None and not (deal_dir / "deal.yaml").is_file():
        sb.warning("That directory has no deal.yaml.")
        deal_dir = None

    if deal_dir is not None:
        deal_id, _ = read_deal_header(deal_dir)
        paths = workpaper_paths(deal_id)
        cached = paths.workpaper.is_file()
        if st.session_state.get("deal_dir") != str(deal_dir):
            # A new selection opens its cached run, or clears the screen until it is run.
            if cached:
                _open_workpaper(deal_dir, paths.workpaper)
            else:
                st.session_state["deal_dir"] = str(deal_dir)
                st.session_state.pop("wp_path", None)
        if cached:
            saved = datetime.fromtimestamp(paths.workpaper.stat().st_mtime, tz=timezone.utc)
            sb.caption(f"Cached run saved {saved:%Y-%m-%d %H:%M} UTC")
        else:
            sb.caption("No cached run for this deal yet.")
        modes = ["rules"] + (["llm"] if os.environ.get("QOE_LLM_MODEL") else [])
        ai_mode = sb.selectbox(
            "Evidence AI",
            modes,
            key="ai_mode",
            help="rules: deterministic extraction (default). llm: uses QOE_LLM_* settings; quotes are still verified verbatim.",
        )
        c1, c2 = sb.columns(2)
        c1.button("Open cached", disabled=not cached, on_click=_open_workpaper, args=(deal_dir, paths.workpaper))
        if c2.button("Run review", type="primary"):
            st.session_state["run_request"] = (str(deal_dir), ai_mode)

    sb.text_input("Reviewer", key="reviewer", placeholder="Your name (recorded on decisions)")
    if st.session_state.get("wp_path"):
        sb.radio("View", PAGES, key="page")


def _handle_run_request() -> None:
    req = st.session_state.pop("run_request", None)
    if req is None:
        return
    deal_dir, ai_mode = Path(req[0]), req[1]
    try:
        with st.spinner(f"Running review on {md(deal_dir.name)} ({md(ai_mode)})..."):
            path = run_and_save(deal_dir, ai_mode, workpapers_root())
    except Exception as exc:  # noqa: BLE001
        _show_error("The review run failed", exc)
        return
    _open_workpaper(deal_dir, path)
    shown = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    _flash("success", f"Review complete. Workpaper saved to {shown}.")
    st.rerun()  # redraw the sidebar with the view selector for the new run


def _file_sig(path: Path) -> Optional[tuple[int, int]]:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_size, stat.st_mtime_ns)


def _build_context() -> ReviewContext:
    ss = st.session_state
    wp_path = Path(ss["wp_path"])
    base = _load_workpaper_cached(str(wp_path), wp_path.stat().st_mtime_ns)
    paths = WorkpaperPaths(root=wp_path.parent, deal_id=base.deal.deal_id)
    notes: list[str] = []

    deal_dir = Path(ss["deal_dir"]) if ss.get("deal_dir") else find_deal_dir(base.deal.deal_id)
    pkg: Optional[DealPackage] = None
    if deal_dir is not None:
        fingerprint = "|".join(f"{k}={v}" for k, v in sorted(base.input_hashes.items()))
        pkg, err = _load_deal_cached(str(deal_dir), fingerprint)
        if err:
            notes.append(f"Deal package could not be loaded ({err}); GL details and management's narrative are limited.")
        elif pkg is not None and pkg.meta.deal_id != base.deal.deal_id:
            notes.append(f"Deal package at {deal_dir} is {pkg.meta.deal_id}, not {base.deal.deal_id}; ignoring it.")
            pkg = None
        elif pkg is not None and any(
            pkg.input_hashes.get(k, v) != v for k, v in base.input_hashes.items()
        ):
            notes.append("The deal package has changed since this run. Re-run the review before relying on GL details.")
            pkg = None
    else:
        notes.append("Deal package not found; GL details and management's narrative are not available.")

    # Fingerprint first: a write that lands while the logs are read makes the export look
    # out of date (safe), never up to date.
    signature = review_state_signature(paths, pkg is not None)
    store = ReviewStore(paths.review_log)
    decisions = store.all()
    question_log = store.questions()
    if store.skipped_lines:
        notes.append(
            f"Review log lines {', '.join(map(str, store.skipped_lines))} could not be read and were skipped "
            "(the log is never rewritten; inspect review_log.jsonl)."
        )
    if store.skipped_question_lines:
        notes.append(
            f"Question log lines {', '.join(map(str, store.skipped_question_lines))} could not be read and were "
            f"skipped (inspect {QUESTION_LOG_NAME})."
        )

    key = (str(wp_path), wp_path.stat().st_mtime_ns, _file_sig(paths.review_log), _file_sig(paths.question_log), pkg is not None)
    memo = ss.get("_applied")
    if memo is not None and memo[0] == key:
        wp, err = memo[1], memo[2]
    else:
        try:
            wp = apply_reviews(base, decisions, schedule=pkg.schedule if pkg is not None else None, question_log=question_log)
            err = None
        except Exception as exc:  # noqa: BLE001
            wp = base.model_copy(deep=True)
            wp.reviews = decisions
            apply_question_updates(wp.assessments, decisions, question_log)
            err = f"The bridge could not be rebuilt with reviewed amounts ({type(exc).__name__}: {exc}); it shows the tool's proposals."
        ss["_applied"] = (key, wp, err)
    if err:
        notes.append(err)

    latest = latest_by_adj(decisions)
    return ReviewContext(
        base=base,
        wp=wp,
        labels=[p.label for p in wp.deal.periods],
        decisions=decisions,
        latest=latest,
        finals=final_amounts(wp, latest),
        paths=paths,
        deal_dir=deal_dir,
        pkg=pkg,
        notes=notes,
        question_log=question_log,
        signature=signature,
    )


def _show_notes(ctx: ReviewContext) -> None:
    for note in ctx.notes:
        st.warning(md(note))


def _landing() -> None:
    st.title("QoE Evidence Review")
    st.markdown(
        "Verify management's adjusted EBITDA adjustments against the general ledger and the data room. "
        "Choose a deal package in the sidebar, then **Run review** (or open a cached run)."
    )
    st.caption(
        "The tool traces each adjustment to GL entries and documents, challenges it, and proposes a treatment. "
        "Amounts and treatments are computed by code; quotes are verified verbatim; the reviewer makes the call."
    )


def _deal_header(wp: Workpaper) -> None:
    meta = wp.deal
    if meta.synthetic:
        st.html('<div class="qoe-banner">SYNTHETIC DATA: generated for QoE Evidence Review testing. Not a real company.</div>')
    st.title(md(meta.target_name))
    periods = ", ".join(f"{p.label} ({p.start} to {p.end})" for p in meta.periods)
    bits = [meta.industry, f"Deal {meta.deal_id}", periods, f"{meta.currency}", f"Tolerance {meta.tolerance}"]
    st.caption(" | ".join(md(b) for b in bits if b))


# ----------------------------- Overview -------------------------------------


def _page_overview(ctx: ReviewContext) -> None:
    wp = ctx.wp
    _deal_header(wp)
    st.caption(md(f"Run {wp.run_id} | created {wp.created_at} | AI {wp.ai_mode} | tool {wp.tool_version}"))
    _show_notes(ctx)

    st.subheader("EBITDA bridge")
    items = diligence_ids(wp)
    st.html(html_table(["Line", *ctx.labels], bridge_summary_rows(wp.bridge, items), numeric=ctx.labels))
    try:
        diffs = check_bridge_identity(wp)
        if bridge_ties(diffs):
            st.caption("Check: diligence adjusted EBITDA = GL EBITDA + final adjustments (pending excluded). Ties in every period.")
        else:
            st.error(md("Bridge does not tie: " + ", ".join(f"{p} off by {fmt_amount(v, cents=True)}" for p, v in diffs.items())))
    except ValueError as exc:
        st.warning(md(f"Bridge check not available: {exc}"))
    with st.expander("Full bridge: management adjustments, diligence revisions and diligence-identified items"):
        st.html(html_table(["Line", *ctx.labels], bridge_rows(wp.bridge, items), numeric=ctx.labels))

    counts = status_counts(wp, ctx.latest, ctx.finals, ctx.tolerance)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Review progress**")
        total = counts["total"] or 1
        st.progress(int(100 * counts["reviewed"] / total), text=f"{counts['reviewed']} of {counts['total']} reviewed")
        st.html(
            html_table(
                ["Status", "Count"],
                [{"Status": k, "Count": v} for k, v in counts["review"].items()],
                numeric=["Count"],
            )
        )
        if counts["stale"]:
            st.caption(f"{counts['stale']} decision(s) were made on an earlier tool proposal.")
    with c2:
        st.markdown("**Tool treatment**")
        st.html(
            "".join(
                f"<div style='margin:4px 0'>{treatment_chip(Treatment(t))} {n}</div>" for t, n in counts["tool"].items()
            )
        )
    with c3:
        st.markdown("**Diligence status**")
        st.html(
            html_table(
                ["Measure", "Count"],
                [
                    {"Measure": "Pending information (excluded)", "Count": counts["pending"]},
                    {"Measure": "Diligence-identified items (not on the schedule)", "Count": counts["diligence_items"]},
                    {"Measure": "Overridden by reviewer", "Count": counts["review"][STATUS_OVERRIDDEN]},
                    {"Measure": "Open questions for management", "Count": counts["open_questions"]},
                ],
                numeric=["Count"],
            )
        )
    if counts["pending_without_question"]:
        st.warning(
            md(
                "Pending with no open question to management: "
                + ", ".join(counts["pending_without_question"])
                + ". Add a question (Open questions page) so the request list asks for what is needed."
            )
        )

    st.subheader("Reconciliation and data quality")
    rec = wp.reconciliation
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Months compared", rec.months_compared)
    m2.metric("Accounts compared", rec.accounts_compared)
    m3.metric("GL vs P&L variances", rec.variance_count)
    m4.metric("Data-quality issues", len(rec.issues))
    st.html(
        html_table(
            ["Period", "GL EBITDA", "Management reported", "Management less GL"],
            ebitda_check_rows(wp),
            numeric=["GL EBITDA", "Management reported", "Management less GL"],
        )
    )
    _table(issue_rows(rec), numeric=["Amount"])
    if wp.ingest_notes:
        with st.expander(f"Ingest notes ({len(wp.ingest_notes)})"):
            for n in wp.ingest_notes:
                st.text(n)


# ----------------------------- Queue ----------------------------------------


def _open_selected(key: str, refs: list[str]) -> None:
    """Dataframe selection callback: open the clicked adjustment."""
    ref = selected_ref(refs, st.session_state.get(key))
    if ref is not None:
        _goto("Adjustment detail", ref)


def _page_queue(ctx: ReviewContext) -> None:
    st.subheader("Adjustment queue")
    _show_notes(ctx)
    ss = st.session_state
    drafts = [a.adj_id for a in ctx.wp.assessments if form_is_dirty(ss, a.adj_id)]
    rows = queue_rows(ctx.wp, ctx.latest, ctx.finals, ctx.tolerance, drafts=drafts)
    f1, f2, f3, f4 = st.columns([2, 2, 3, 1])
    tool_filter = f1.multiselect("Tool treatment", list(TREATMENT_LABELS.values()), key="qf_tool")
    status_filter = f2.multiselect("Status", [STATUS_UNREVIEWED, STATUS_AGREED, STATUS_OVERRIDDEN], key="qf_status")
    text = f3.text_input("Search ref, title or flag", key="qf_text").strip().lower()
    all_columns = f4.toggle("All columns", key="qf_all", help="Show claimed and proposed amounts, category, confidence and link counts.")
    shown = [
        r
        for r in rows
        if (not tool_filter or r["Tool"] in tool_filter)
        and (not status_filter or r["Status"].split(" (")[0] in status_filter)
        and (not text or text in f"{r['Ref']} {r['Title']} {r['Top flags']}".lower())
    ]
    columns = queue_columns(ctx.labels, all_columns=all_columns)
    amount_cols = [c for c in columns if c.split(" ")[0] in ("Claimed", "Proposed", "Final")]
    for n, (group, group_rows) in enumerate(queue_groups(shown)):
        st.markdown(f"**{group}** ({len(group_rows)})")
        if group == GROUP_DILIGENCE:
            st.caption(DILIGENCE_NOTE + " Final = the whole diligence adjustment.")
        key = f"grid:queue:{n}"
        refs = [r["Ref"] for r in group_rows]
        _table(
            group_rows,
            numeric=amount_cols + ["GL links", "Supporting GL links", "Docs", "Open Qs"],
            color_cols=["Tool", "Reviewer"],
            columns=columns,
            fit_rows=None,
            key=key,
            on_select=lambda key=key, refs=refs: _open_selected(key, refs),
        )
    st.caption(
        "Click a row to open it. Final = reviewer's amounts where reviewed, otherwise the tool's proposal. "
        "Bridge: Carried (in diligence adjusted EBITDA), Carried at 0 (rejected), or Excluded (pending)."
    )
    ids = [a.adj_id for a in ctx.wp.assessments]
    if ids:
        c1, c2 = st.columns([3, 1])
        titles = {a.adj_id: a.title for a in ctx.wp.assessments}
        tags = {a.adj_id: " (diligence-identified)" if is_diligence_item(a) else "" for a in ctx.wp.assessments}
        _keep_option("qf_pick", ids)
        pick = c1.selectbox("Open adjustment", ids, format_func=lambda i: f"{i}: {titles[i]}{tags[i]}", key="qf_pick")
        c2.button("Open", on_click=_goto, args=("Adjustment detail", pick), type="primary")


# ----------------------------- Detail ---------------------------------------


def _page_detail(ctx: ReviewContext) -> None:
    ids = [a.adj_id for a in ctx.wp.assessments]
    if not ids:
        st.info("This workpaper has no adjustments.")
        return
    if st.session_state.get("adj_select") not in ids:
        st.session_state["adj_select"] = ids[0]
    titles = {a.adj_id: a.title for a in ctx.wp.assessments}
    nav1, nav2, nav3 = st.columns([6, 1, 1])
    adj_id = nav1.selectbox("Adjustment", ids, format_func=lambda i: f"{i}: {titles[i]}", key="adj_select")
    i = ids.index(adj_id)
    nav2.button("Previous", disabled=i == 0, on_click=_goto, args=("Adjustment detail", ids[max(0, i - 1)]))
    nav3.button("Next", disabled=i == len(ids) - 1, on_click=_goto, args=("Adjustment detail", ids[min(len(ids) - 1, i + 1)]))

    now = datetime.now(timezone.utc)
    track_view(st.session_state["timer"], adj_id, now)

    a = ctx.assessment(adj_id)
    decision = ctx.latest.get(adj_id)
    final = ctx.finals.get(adj_id, {})
    if ctx.wp.deal.synthetic:
        st.html('<div class="qoe-banner">SYNTHETIC DATA</div>')
    status = review_status(a, decision, ctx.tolerance)
    chips = [chip("Diligence-identified", "#DDEBF7", "#1F3864")] if is_diligence_item(a) else []
    chips += [
        chip(category_label(a.category), "#E7E9EC", "#3C4650"),
        treatment_chip(a.treatment, prefix="Tool: "),
        chip(f"Confidence: {a.confidence}", "#E7E9EC", "#3C4650"),
    ]
    if decision is not None:
        chips.append(treatment_chip(decision.treatment, prefix="Reviewer: "))
    chips.append(chip(status, "#E7E9EC", "#3C4650"))
    if not final:
        chips.append(chip("Pending: excluded from diligence EBITDA", "#DDE3EA", "#2F3E50"))
    if form_is_dirty(st.session_state, adj_id):
        chips.append(chip("Unsent draft: not recorded", "#FFF2CC", "#7F6000"))
    st.html(f"<h3 style='margin:0 0 4px 0'>{_esc(a.adj_id)}: {_esc(a.title)}</h3><div>{''.join(chips)}</div>")
    st.caption(f"Time on this adjustment this session: {fmt_duration(elapsed_seconds(st.session_state['timer'], adj_id, now))}")
    if decision is not None and decision_is_stale(a, decision, ctx.tolerance):
        st.warning(
            f"The tool's proposal changed after this decision was recorded (was {TREATMENT_LABELS[decision.tool_treatment]}, "
            f"now {TREATMENT_LABELS[a.treatment]}). Re-confirm the decision."
        )

    _render_safely("Management's claim", _detail_claim, ctx, a)
    st.markdown("**Tie-out**")
    st.html(html_table(["Line", *ctx.labels], tieout_rows(a, final, ctx.labels, decision is not None), numeric=ctx.labels))
    if a.rationale:
        st.html(f"<div class='qoe-muted'><b>Tool's reasoning.</b> {_esc(a.rationale)}</div>")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**What the evidence shows**")
            st.caption("Documented facts: each cites GL rows and/or verbatim quotes.")
            st.html(f'<div class="qoe-evidence">{facts_html(a.facts)}</div>')
    with right:
        with st.container(border=True):
            st.markdown("**What needs judgment**")
            st.caption("Calls the reviewer has to make; the tool does not decide these.")
            items = "".join(f'<div class="qoe-item">{_esc(q)}</div>' for q in a.judgment_questions)
            st.html(f'<div class="qoe-judgment">{items or "<div class=qoe-muted>None recorded.</div>"}</div>')
        with st.container(border=True):
            st.markdown("**Questions for management**")
            qs = "".join(
                f'<div class="qoe-item"><span class="qoe-src">{_esc(q.q_id)} | {_esc(q.priority)} | {_esc(q.status.value)}</span>'
                f"<div>{_esc(q.text)}</div>"
                + (f'<div class="qoe-src">Response: {_esc(q.response)}</div>' if q.response else "")
                + "</div>"
                for q in a.open_questions
            )
            st.html(f'<div class="qoe-ask">{qs or "<div class=qoe-muted>None.</div>"}</div>')

    st.markdown(f"**Flags ({len(a.flags)})**")
    st.html("".join(flag_html(f, ctx.labels) for f in sorted_flags(a.flags)) or "<div class='qoe-muted'>No flags.</div>")

    history = [d for d in ctx.decisions if d.adj_id == adj_id]
    q_history = [e for e in ctx.question_log if e.adj_id == adj_id]
    t_gl, t_docs, t_rec, t_hist = st.tabs(
        [
            f"GL entries ({len(a.gl_links)})",
            f"Documents ({len(a.doc_links)})",
            f"Recurrence ({len(a.recurrence)})",
            f"History ({len(history)} decisions, {len(q_history)} question updates)",
        ]
    )
    with t_gl:
        _render_safely("GL entries", _detail_gl, ctx, a)
    with t_docs:
        _render_safely("Documents", _detail_docs, ctx, a)
    with t_rec:
        _table(recurrence_rows(a, ctx.labels), numeric=ctx.labels + ["Entries"])
    with t_hist:
        _table(decision_history_rows(history, ctx.labels, q_history), numeric=ctx.labels, color_cols=["Treatment", "Tool"])

    st.divider()
    _render_safely("Review form", _review_form, ctx, a, decision)


def _detail_claim(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    info = claim_details(a, ctx.pkg, ctx.wp.schedule)
    st.markdown(f"**{md(info['heading'])}**")
    if not info["description"] and not info["bits"]:
        st.caption("Management's narrative is not stored in this workpaper and the deal package is not loaded.")
        return
    empty = "<span class=qoe-muted>No description recorded.</span>"
    st.html(
        f"<div>{_esc(info['description']) or empty}</div>"
        + (f"<div class='qoe-src'>{_esc(' | '.join(info['bits']))}</div>" if info["bits"] else "")
    )


def _detail_gl(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    gl_by_id = {e.entry_id: e for e in ctx.pkg.gl} if ctx.pkg is not None else {}
    if not gl_by_id:
        st.caption("GL detail (date, account, memo) needs the deal package; showing the links only.")
    counts = gl_role_counts(a)
    st.caption(
        md(
            f"{len(a.gl_links)} linked entries: "
            + "; ".join(f"{label}: {n}" for label, n in counts.items())
            + ". Claimed entries are management's; the tool carries the supporting ones and names the flag that "
            "removed the others. Context entries (comparables, excess activity) are not part of the claim."
        )
    )
    st.html(html_table(["Line", *ctx.labels], claimed_link_tieout(a, ctx.wp.deal.periods), numeric=ctx.labels))
    _table(gl_link_rows(a, gl_by_id), numeric=["GL row", "Amount", "Score"], fit_rows=40)


def _detail_docs(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    if not a.doc_links:
        st.caption("No documents linked.")
        return
    facts_by_doc = {f.doc_id: f for f in ctx.wp.doc_facts}
    docs_by_id = {d.doc_id: d for d in ctx.pkg.documents} if ctx.pkg is not None else {}
    documents_dir = ctx.wp.deal.files.documents_dir
    for link in sorted(a.doc_links, key=lambda l: (-l.score, l.doc_id)):
        with st.container(border=True):
            df = facts_by_doc.get(link.doc_id)
            doc = docs_by_id.get(link.doc_id)
            st.html(
                f"<b>{_esc(link.doc_id)}</b> "
                + chip(humanize_code(link.relation.upper()), "#E7E9EC", "#3C4650")
                + (f"<div class='qoe-src'>{_esc(doc_facts_line(df))}</div>" if df is not None else "")
                + (f"<div class='qoe-src'>{_esc(doc.relpath)}</div>" if doc is not None else "")
                + f"<div class='qoe-src'>Why linked: {_esc('; '.join(link.reasons) or 'n/a')} | score {link.score:.2f}"
                + (f" | {_esc(gl_rows_text(link.entry_ids))}" if link.entry_ids else "")
                + "</div>"
                + "".join(quote_html(q) for q in link.quotes)
            )
            pages: list[tuple[int, str]]
            if doc is not None:
                pages = [(p.page, p.text) for p in sorted(doc.pages, key=lambda p: p.page)]
            elif ctx.deal_dir is not None:
                pages = list(enumerate(_document_pages_cached(str(ctx.deal_dir), link.doc_id, documents_dir), 1))
            else:
                pages = []
            if not pages:
                continue
            quoted = quotes_for_doc(a, link.doc_id)
            with st.expander(f"Document text ({len(pages)} page{'s' if len(pages) != 1 else ''}), quotes highlighted"):
                for n, text in pages:
                    if len(pages) > 1:
                        st.caption(f"Page {n}")
                    st.html(f'<div class="qoe-page">{highlight_quotes(text, quoted.get(n, []))}</div>')


# ----------------------------- Review form ----------------------------------


def _form_key(adj_id: str, name: str) -> str:
    return f"f:{adj_id}:{name}"


def _clear_form(adj_id: str) -> None:
    """Drop the form's draft; the next render starts again from the latest decision."""
    ss = st.session_state
    prefix = f"f:{adj_id}:"
    for k in [k for k in ss.keys() if isinstance(k, str) and k.startswith(prefix)]:
        del ss[k]
    ss.pop(f"fd:{adj_id}", None)
    ss.pop(f"fb:{adj_id}", None)


def _rebase_form(adj_id: str, token: str) -> None:
    """Keep the draft, now based on the newer decision the reviewer has looked at."""
    st.session_state[f"fb:{adj_id}"] = token


def _seed_form(ctx: ReviewContext, a: AdjustmentAssessment, decision: Optional[ReviewDecision]) -> None:
    """Put the form's initial values in session state (widgets are drawn without their own
    defaults, so a draft kept in session state is never overwritten). ``fd:<adj>`` holds the
    values the form started from, ``fb:<adj>`` the decision it was built from."""
    ss = st.session_state
    adj = a.adj_id
    token = decision_token(decision)
    if f"fd:{adj}" in ss and ss.get(f"fb:{adj}") != token and not form_is_dirty(ss, adj):
        _clear_form(adj)  # a newer decision arrived and nothing was typed: start from it
    if f"fd:{adj}" not in ss:
        seed = form_seed(a, decision, ctx.labels)
        ss[f"fd:{adj}"] = dict(seed)
        ss[f"fb:{adj}"] = token
        for name, value in seed.items():
            ss[_form_key(adj, name)] = value
        return
    defaults = ss[f"fd:{adj}"]
    for name, value in form_seed(a, decision, ctx.labels).items():
        key = _form_key(adj, name)
        if name not in defaults or key not in ss:
            defaults[name] = value
            ss[key] = value
        elif name.startswith("q:") and ss[key] == defaults[name] and defaults[name] != value:
            # Untouched question field changed elsewhere (question log): show it as it is now,
            # so recording this form cannot revert a colleague's update.
            defaults[name] = value
            ss[key] = value


def _collect_form(a: AdjustmentAssessment, labels: list[str]) -> dict[str, Any]:
    ss = st.session_state
    adj = a.adj_id
    defaults = ss.get(f"fd:{adj}", {})
    edits: dict[str, tuple[QuestionStatus, str]] = {}
    for q in a.open_questions:
        s_name, r_name = f"q:{q.q_id}:status", f"q:{q.q_id}:response"
        status = ss.get(_form_key(adj, s_name), q.status)
        response = str(ss.get(_form_key(adj, r_name), q.response))
        # Only fields the reviewer changed in this form become question updates.
        if status != defaults.get(s_name, q.status) or response != defaults.get(r_name, q.response):
            edits[q.q_id] = (QuestionStatus(status), response)
    return {
        "treatment": Treatment(ss.get(_form_key(adj, "treatment"), a.treatment)),
        "amounts": {p: ss.get(_form_key(adj, f"amt:{p}"), "") for p in labels},
        "rationale": str(ss.get(_form_key(adj, "rationale"), "")),
        "correction_type": CorrectionType(ss.get(_form_key(adj, "correction"), CorrectionType.NONE)),
        "reviewer": str(ss.get("reviewer", "")),
        "question_edits": edits,
        "question_updates": question_update_values(a.open_questions, edits),
        "new_question": str(ss.get(_form_key(adj, "newq"), "")).strip(),
        "new_question_priority": str(ss.get(_form_key(adj, "newq_prio"), "high")),
        "basis": ss.get(f"fb:{adj}"),
    }


def _form_questions(a: AdjustmentAssessment, form: Mapping[str, Any]) -> list[OpenQuestion]:
    return questions_after(a.open_questions, form["question_updates"], [form["new_question"]])


def _record_decision(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    """Button callback: validate, append to the log (refused if a newer decision was
    recorded since the form was opened), log question edits, record time on task."""
    ss = st.session_state
    form = _collect_form(a, ctx.labels)
    previous = ctx.latest.get(a.adj_id)
    try:
        decision = make_decision(
            a,
            treatment=form["treatment"],
            amounts=form["amounts"],
            rationale=form["rationale"],
            reviewer=form["reviewer"],
            labels=ctx.labels,
            correction_type=form["correction_type"],
            tolerance=ctx.tolerance,
            questions=_form_questions(a, form),
            previous=previous,
        )
    except DecisionError as exc:
        ss["form_errors"][a.adj_id] = exc.errors
        return
    except ArithmeticError as exc:  # defensive: amount_problem() should have caught it
        ss["form_errors"][a.adj_id] = [f"An amount could not be used ({type(exc).__name__}); check the amounts."]
        return
    store = ReviewStore(ctx.paths.review_log)
    basis = form["basis"] if form["basis"] is not None else decision_token(previous)
    try:
        store.append(decision, expected_token=basis)
    except ConflictError as exc:
        ss["form_errors"][a.adj_id] = [str(exc)]
        return
    except OSError as exc:
        ss["form_errors"][a.adj_id] = [f"Could not write the review log: {exc}"]
        return
    ss["form_errors"].pop(a.adj_id, None)
    # Question edits and a raised question go to the question log, signed by this reviewer.
    by_id = {q.q_id: q for q in a.open_questions}
    try:
        for q_id, (status, response) in form["question_edits"].items():
            entry = make_question_update(
                by_id[q_id], adj_id=a.adj_id, status=status, response=response,
                reviewer=decision.reviewer, timestamp=decision.timestamp,
            )
            if entry is not None:
                store.append_question(entry)
        if form["new_question"]:
            added = store.add_question(
                adj_id=a.adj_id,
                text=form["new_question"],
                reviewer=decision.reviewer,
                priority=form["new_question_priority"],
                existing_ids=list(by_id),
                timestamp=decision.timestamp,
            )
            _flash("info", f"Question {added.q_id} added for management.")
    except (OSError, DecisionError) as exc:
        _flash("warning", f"Decision recorded, but the question changes could not be saved ({exc}). Redo them on the Open questions page.")
    now = datetime.now(timezone.utc)
    opened, seconds = finish_timing(ss["timer"], a.adj_id, now)
    try:
        append_timing(
            ctx.paths.timing,
            adj_id=a.adj_id,
            opened_at=_iso(opened),
            decided_at=decision.timestamp,
            seconds=seconds,
            reviewer=decision.reviewer,
            treatment=decision.treatment,
            deal_id=ctx.wp.deal.deal_id,
            run_id=ctx.wp.run_id,
        )
    except OSError as exc:
        _flash("warning", f"Decision recorded, but time on task could not be saved: {exc}")
    _clear_form(a.adj_id)
    _flash(
        "success",
        f"Recorded {TREATMENT_LABELS[decision.treatment]} for {a.adj_id} ({fmt_duration(seconds)} on task). Bridge refreshed.",
    )


def _review_form(ctx: ReviewContext, a: AdjustmentAssessment, decision: Optional[ReviewDecision]) -> None:
    st.subheader("Reviewer decision")
    ss = st.session_state
    labels = ctx.labels
    adj = a.adj_id
    _seed_form(ctx, a, decision)

    if decision is not None:
        correction = CORRECTION_LABELS[decision.correction_type] if decision.correction_type != CorrectionType.NONE else "none"
        st.html(
            "<div class='qoe-muted'><b>Current decision</b> "
            f"({_esc(decision.reviewer)}, {_esc(decision.timestamp)}): {_esc(TREATMENT_LABELS[decision.treatment])}; "
            f"correction type: {_esc(correction)}. Rationale: {_esc(decision.rationale) or '(none)'}</div>"
        )
        st.caption("A re-review starts with a blank rationale and correction type: state the reasons for the decision you record now.")
    current = decision_token(decision)
    if ss.get(f"fb:{adj}") != current:
        who = f"{decision.reviewer} ({TREATMENT_LABELS[decision.treatment]}, {decision.timestamp})" if decision is not None else "another reviewer"
        st.warning(
            md(
                f"{adj} was decided by {who} after you started this draft. Your draft is kept. "
                "Review that decision, then keep your draft (and record it) or discard it."
            )
        )
        b1, b2 = st.columns(2)
        b1.button("Keep my draft: I have reviewed the newer decision", on_click=_rebase_form, args=(adj, current))
        b2.button("Discard my draft", on_click=_clear_form, args=(adj,))

    options = list(Treatment)
    t_labels = treatment_labels_for(a)
    treatment = st.radio(
        "Treatment",
        options,
        format_func=lambda t: t_labels[t],
        horizontal=True,
        key=_form_key(adj, "treatment"),
    )
    if treatment == Treatment.REVISE:
        started = "the decision you are re-reviewing." if decision else "the tool's proposal."
        st.caption("Diligence amounts by period (EBITDA-signed: + adds back). Prefilled with " + started)
        cols = st.columns(len(labels) or 1)
        for col, p in zip(cols, labels):
            col.text_input(md(p), key=_form_key(adj, f"amt:{p}"))
    else:
        carried = resolve_amounts(a, treatment, {}, labels)
        if treatment == Treatment.REQUEST_INFO:
            st.caption(
                "Request info: the adjustment is pending and excluded from diligence adjusted EBITDA until resolved. "
                "It needs at least one open question to management: add one below if none is open."
            )
        else:
            if treatment == Treatment.ACCEPT:
                what = (
                    "the tool's proposed diligence amount (management claimed nothing for this item)"
                    if accept_carries_proposal(a)
                    else "management's claimed amounts"
                )
            else:
                what = "zero in every period"
            st.caption(f"{t_labels[treatment]} carries {what}.")
            st.html(html_table(labels, [{p: fmt_amount(carried.get(p)) for p in labels}], numeric=labels))

    corrections = list(CorrectionType)
    c1, c2 = st.columns([2, 3])
    c1.selectbox(
        "Correction type",
        corrections,
        format_func=lambda c: CORRECTION_LABELS[c],
        key=_form_key(adj, "correction"),
        help="Required when your decision differs from the tool. Tool-error types become regression cases; "
        "judgment differences and new information do not count against the tool.",
    )
    c2.text_area(
        "Rationale",
        key=_form_key(adj, "rationale"),
        height=100,
        help="Required when you override the tool or classify a correction.",
    )

    open_count = sum(1 for q in a.open_questions if q.status == QuestionStatus.OPEN)
    with st.expander(
        f"Questions for management ({len(a.open_questions)}, {open_count} open)",
        expanded=treatment == Treatment.REQUEST_INFO,
    ):
        statuses = list(QuestionStatus)
        for q in a.open_questions:
            st.html(f"<div class='qoe-src'>{_esc(q.q_id)} | {_esc(q.priority)}</div><div>{_esc(q.text)}</div>")
            q1, q2 = st.columns([1, 3])
            q1.selectbox(
                "Status",
                statuses,
                format_func=lambda s: s.value.capitalize(),
                key=_form_key(adj, f"q:{q.q_id}:status"),
            )
            q2.text_input("Response", key=_form_key(adj, f"q:{q.q_id}:response"))
        n1, n2 = st.columns([3, 1])
        n1.text_area(
            "New question for management",
            key=_form_key(adj, "newq"),
            height=70,
            help="Logged with the decision as an open request to management (id Q-<ref>-R<n>).",
        )
        n2.selectbox("Priority", ["high", "medium", "low"], key=_form_key(adj, "newq_prio"))
        st.caption(f"Question changes are logged in {QUESTION_LOG_NAME} under your name when you record the decision.")

    form = _collect_form(a, labels)
    errors, warnings = decision_problems(
        a,
        treatment=form["treatment"],
        amounts=form["amounts"],
        rationale=form["rationale"],
        reviewer=form["reviewer"],
        correction_type=form["correction_type"],
        labels=labels,
        tolerance=ctx.tolerance,
        questions=_form_questions(a, form),
        previous=decision,
    )
    for w in warnings:
        st.warning(md(w))
    if errors:
        st.warning(md("Needed before recording: " + " ".join(errors)))
    for e in ss["form_errors"].pop(adj, []):  # shown once, after a failed submit
        st.error(md(e))
    st.button("Record decision", type="primary", on_click=_record_decision, args=(ctx, a))


# ----------------------------- Questions ------------------------------------


def _find_question(ctx: ReviewContext, q_id: str) -> tuple[Optional[AdjustmentAssessment], Optional[OpenQuestion]]:
    for a in ctx.wp.assessments:
        for q in a.open_questions:
            if q.q_id == q_id:
                return a, q
    return None, None


def _record_question_update(ctx: ReviewContext, q_id: str) -> None:
    """Button callback: log a status / response change as a question update. It is signed
    by the named reviewer and never records or re-signs a review decision."""
    ss = st.session_state
    a, question = _find_question(ctx, q_id)
    if question is None or a is None:
        return
    status_key, response_key = f"oq_status:{q_id}", f"oq_response:{q_id}"
    basis_key, seed_key = f"oq_basis:{q_id}", f"oq_seed:{q_id}"
    try:
        entry = make_question_update(
            question,
            adj_id=a.adj_id,
            status=QuestionStatus(ss.get(status_key, question.status)),
            response=str(ss.get(response_key, question.response)),
            reviewer=str(ss.get("reviewer", "")),
        )
    except DecisionError as exc:
        ss["oq_errors"] = exc.errors
        return
    if entry is None:
        _flash("info", f"No change to {q_id}.")
        return
    expected = ss.get(basis_key, question_token(ctx.question_log, q_id))
    try:
        ReviewStore(ctx.paths.review_log).append_question(entry, expected_token=expected)
    except ConflictError as exc:
        ss["oq_errors"] = [str(exc)]
        for k in (status_key, response_key, basis_key, seed_key):
            ss.pop(k, None)
        return
    except OSError as exc:
        ss["oq_errors"] = [f"Could not write the question log: {exc}"]
        return
    for k in (status_key, response_key, basis_key, seed_key):
        ss.pop(k, None)
    _flash("success", f"{q_id} updated ({entry.status.value.capitalize() if entry.status else 'response'}) by {entry.reviewer}. No review decision was recorded or changed.")


def _add_question(ctx: ReviewContext) -> None:
    """Button callback: log a question the reviewer raises for management."""
    ss = st.session_state
    adj_id = ss.get("oq_new_adj")
    a = next((x for x in ctx.wp.assessments if x.adj_id == adj_id), None)
    if a is None:
        return
    try:
        added = ReviewStore(ctx.paths.review_log).add_question(
            adj_id=a.adj_id,
            text=str(ss.get("oq_new_text", "")),
            reviewer=str(ss.get("reviewer", "")),
            priority=str(ss.get("oq_new_prio", "high")),
            existing_ids=[q.q_id for q in a.open_questions],
        )
    except DecisionError as exc:
        ss["oq_add_errors"] = exc.errors
        return
    except OSError as exc:
        ss["oq_add_errors"] = [f"Could not write the question log: {exc}"]
        return
    ss["oq_new_text"] = ""
    _flash("success", f"Question {added.q_id} added for {a.adj_id}.")


QUESTION_TABLE_COLUMNS = ["Q id", "Ref", "Question", "Priority", "Status", "Response", "Basis", "Last update"]


def _page_questions(ctx: ReviewContext) -> None:
    st.subheader("Open questions for management")
    ss = st.session_state
    rows = question_rows(ctx.wp, ctx.question_log)
    by_id = {r["Q id"]: r for r in rows}
    if not rows:
        st.info("No questions for management yet. Add one below.")
    else:
        f1, f2, f3 = st.columns(3)
        if "oq_f_status" not in ss:
            ss["oq_f_status"] = [QuestionStatus.OPEN.value]
        status_f = f1.multiselect("Status", [s.value for s in QuestionStatus], key="oq_f_status")
        prio_f = f2.multiselect("Priority", ["high", "medium", "low"], key="oq_f_prio")
        order = {a.adj_id: i for i, a in enumerate(ctx.wp.assessments)}
        refs = sorted({r["Ref"] for r in rows}, key=lambda r: (order.get(r, len(order)), r))
        if "oq_f_ref" in ss:
            ss["oq_f_ref"] = [r for r in ss["oq_f_ref"] if r in refs]
        ref_f = f3.multiselect("Adjustment", refs, key="oq_f_ref")
        shown = filter_question_rows(rows, status_f, prio_f, ref_f)
        if shown:
            st.html(html_table(QUESTION_TABLE_COLUMNS, shown))
        else:
            st.caption("No questions match the filters.")
        st.download_button(
            "Download as CSV (information request list)",
            data=request_list_csv(shown),
            file_name=f"QoE_open_questions_{ctx.wp.deal.deal_id}.csv",
            mime="text/csv",
            disabled=not shown,
        )
        st.caption(
            f"The CSV holds exactly the {len(shown)} question(s) shown, without the internal Basis column; "
            "cells that a spreadsheet would read as a formula are prefixed with an apostrophe."
        )

        st.markdown("**Update a question**")
        if not shown:
            st.caption("No question matches the filters above.")
        else:
            q_ids = [r["Q id"] for r in shown]
            _keep_option("oq_pick", q_ids, q_ids[0])
            q_id = st.selectbox("Question", q_ids, format_func=lambda q: f"{q}: {by_id[q]['Question'][:90]}", key="oq_pick")
            _, question = _find_question(ctx, q_id)
            status_key, response_key = f"oq_status:{q_id}", f"oq_response:{q_id}"
            basis_key, seed_key = f"oq_basis:{q_id}", f"oq_seed:{q_id}"
            token = question_token(ctx.question_log, q_id)
            seeded = ss.get(seed_key)
            untouched = seeded is not None and (ss.get(status_key), ss.get(response_key)) == tuple(seeded)
            if seeded is None or status_key not in ss or response_key not in ss or (ss.get(basis_key) != token and untouched):
                # First view, or the question changed elsewhere and nothing was typed: show it as it is now.
                ss[status_key], ss[response_key] = question.status, question.response
                ss[seed_key], ss[basis_key] = (question.status, question.response), token
            c1, c2 = st.columns([1, 3])
            c1.selectbox("Status", list(QuestionStatus), format_func=lambda s: s.value.capitalize(), key=status_key)
            c2.text_input("Response", key=response_key)
            st.caption(
                md(
                    f"Logged in {QUESTION_LOG_NAME} under the reviewer named in the sidebar. It does not record or "
                    f"change a review decision on {by_id[q_id]['Ref']}, reviewed or not."
                )
            )
            for e in ss.pop("oq_errors", []):
                st.error(md(e))
            st.button("Record update", type="primary", on_click=_record_question_update, args=(ctx, q_id))

    with st.expander("Add a question for management"):
        ids = [a.adj_id for a in ctx.wp.assessments]
        if not ids:
            st.caption("This workpaper has no adjustments.")
            return
        titles = {a.adj_id: a.title for a in ctx.wp.assessments}
        _keep_option("oq_new_adj", ids, ids[0])
        st.selectbox("Adjustment", ids, format_func=lambda i: f"{i}: {titles[i]}", key="oq_new_adj")
        st.text_area("Question", key="oq_new_text", height=80)
        _keep_option("oq_new_prio", ["high", "medium", "low"], "high")
        st.selectbox("Priority", ["high", "medium", "low"], key="oq_new_prio")
        for e in ss.pop("oq_add_errors", []):
            st.error(md(e))
        st.button("Add question", on_click=_add_question, args=(ctx,))


# ----------------------------- Export ---------------------------------------


def _page_export(ctx: ReviewContext) -> None:
    st.subheader("Export")
    counts = status_counts(ctx.wp, ctx.latest, ctx.finals, ctx.tolerance)
    if counts["review"][STATUS_UNREVIEWED]:
        st.warning(
            f"{counts['review'][STATUS_UNREVIEWED]} adjustment(s) are unreviewed. The workpaper carries the tool's "
            "proposal for them and marks them unreviewed."
        )
    _show_notes(ctx)
    if st.button("Build Excel workpaper", type="primary"):
        try:
            import inspect

            from qoe.export_xlsx import export_workpaper

            # SPEC signature is (wp, out_path); pass the deal package too when the exporter accepts it.
            extra = {"pkg": ctx.pkg} if ctx.pkg is not None and "pkg" in inspect.signature(export_workpaper).parameters else {}
            with st.spinner("Writing workbook..."):
                out = export_workpaper(ctx.wp, ctx.paths.xlsx, **extra)
            write_export_stamp(ctx.paths, ctx.signature, _iso(datetime.now(timezone.utc)))
            st.success(md(f"Written to {out}"))
        except Exception as exc:  # noqa: BLE001
            _show_error("Export failed", exc)
    status, built_at = export_status(ctx.paths, ctx.signature)
    if status == EXPORT_CURRENT:
        st.caption(md(f"Workbook built {built_at} from the decisions and questions logged now."))
    elif status == EXPORT_STALE:
        st.warning(
            md(
                f"The workbook on disk was built {built_at}, before later review changes (a decision, a question "
                "update or a re-run). Build it again; the download is disabled until then."
            )
        )
    elif status == EXPORT_UNKNOWN:
        st.warning(
            "The workbook on disk was not built by this app from the current review state (it may have been "
            "written from the command line or edited). Build it again; the download is disabled until then."
        )
    if status != EXPORT_MISSING:
        current = status == EXPORT_CURRENT
        st.download_button(
            f"Download {md(ctx.paths.xlsx.name)}",
            data=ctx.paths.xlsx.read_bytes() if current else b"",
            file_name=ctx.paths.xlsx.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=not current,
        )
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "Download reviewed workpaper (JSON)",
        data=ctx.wp.model_dump_json(indent=2).encode("utf-8"),
        file_name=f"workpaper_reviewed_{ctx.wp.deal.deal_id}.json",
        mime="application/json",
    )
    if ctx.paths.review_log.is_file():
        c2.download_button(
            "Download review log (JSONL)",
            data=ctx.paths.review_log.read_bytes(),
            file_name=f"review_log_{ctx.wp.deal.deal_id}.jsonl",
            mime="application/jsonl",
        )
    if ctx.paths.question_log.is_file():
        c3.download_button(
            "Download question log (JSONL)",
            data=ctx.paths.question_log.read_bytes(),
            file_name=f"question_log_{ctx.wp.deal.deal_id}.jsonl",
            mime="application/jsonl",
        )

    st.subheader("Reviewer corrections")
    summary = corrections_summary(ctx.decisions, latest_only=True, tolerance=ctx.tolerance)
    st.caption(
        "Latest decision per adjustment. Tool-error corrections feed scripts/qoe_corrections_to_evals.py as regression "
        "cases; judgment differences and new information do not count against the tool."
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Decisions", summary["decisions"])
    m2.metric("Overridden", summary["overridden"])
    m3.metric("Tool errors", summary["tool_error"])
    m4.metric("Judgment / new info", summary["judgment"] + summary["new_information"])
    st.html(
        html_table(
            ["Correction type", "Count"],
            [{"Correction type": CORRECTION_LABELS[CorrectionType(k)], "Count": v} for k, v in summary["by_type"].items() if v],
            numeric=["Count"],
        )
        if summary["decisions"]
        else "<div class='qoe-muted'>No decisions yet.</div>"
    )
    if summary["tool_error_adj_ids"]:
        st.caption(md("Tool errors on: " + ", ".join(summary["tool_error_adj_ids"])))
    if summary["unclassified_overrides"]:
        st.warning(md("Overrides without a correction type: " + ", ".join(summary["unclassified_overrides"])))

    st.subheader("Time on task")
    timing = timing_summary(load_timing(ctx.paths.timing))
    if not timing["per_adjustment"]:
        st.caption("No timed decisions yet. Time is measured from session timestamps while an adjustment's detail page is open.")
        return
    avg = timing["total_seconds"] // max(1, timing["adjustments"])
    st.caption(
        f"{timing['adjustments']} adjustment(s), {timing['decisions']} decision(s), "
        f"{fmt_duration(timing['total_seconds'])} in total; mean {fmt_duration(avg)} and median "
        f"{fmt_duration(timing['median_seconds_per_adjustment'])} per adjustment. Stored in {md(ctx.paths.timing.name)}."
    )
    _table(
        [
            {
                "Ref": s["adj_id"],
                "Decisions": s["decisions"],
                "Time": fmt_duration(s["seconds"]),
                "Seconds": s["seconds"],
                "Last decided (UTC)": s["last_decided_at"],
            }
            for s in timing["per_adjustment"]
        ],
        numeric=["Decisions", "Time", "Seconds"],
    )


# ----------------------------- Entry point ----------------------------------


def main() -> None:
    if st is None:  # pragma: no cover
        raise SystemExit("streamlit is not installed; run `uv run streamlit run qoe/ui.py`.")
    st.set_page_config(page_title="QoE Evidence Review", layout="wide")
    st.html(_CSS)
    _init_state()
    _sidebar()
    _handle_run_request()
    _show_flash()
    if not st.session_state.get("wp_path"):
        _landing()
        return
    try:
        ctx = _build_context()
    except Exception as exc:  # noqa: BLE001
        _show_error("The workpaper could not be loaded", exc)
        return
    page = st.session_state.get("page", PAGES[0])
    if page != "Adjustment detail":
        track_view(st.session_state["timer"], None, datetime.now(timezone.utc))
    renderers = {
        "Overview": _page_overview,
        "Adjustment queue": _page_queue,
        "Adjustment detail": _page_detail,
        "Open questions": _page_questions,
        "Export": _page_export,
    }
    _render_safely(page, renderers.get(page, _page_overview), ctx)


if __name__ == "__main__":
    main()
