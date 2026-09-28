"""Streamlit reviewer app for QoE Evidence Review.

Run with ``uv run streamlit run qoe/ui.py``.

Flow: pick a deal package -> run (or reopen) the review -> Overview (bridge,
reconciliation, status counts) -> Adjustment queue -> Adjustment detail (the
evidence, the judgment calls, and the review form) -> Open questions -> Export.

Decisions go to ``<workpapers>/<deal_id>/review_log.jsonl`` (append-only) and
time on task to ``timing.jsonl`` beside it. The top half of this module is pure
helpers (table builders, formatting, the time tracker) that are unit-tested;
Streamlit rendering lives below and only runs under ``streamlit run``.
"""

from __future__ import annotations

import html
import io
import os
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
    STATUS_AGREED,
    STATUS_OVERRIDDEN,
    STATUS_UNREVIEWED,
    TIMING_LOG_NAME,
    DecisionError,
    ReviewStore,
    append_timing,
    apply_question_updates,
    apply_reviews,
    bridge_ties,
    carry_forward_decision,
    check_bridge_identity,
    corrections_summary,
    decision_is_stale,
    decision_problems,
    encode_question_update,
    final_amounts,
    latest_by_adj,
    load_timing,
    make_decision,
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
    GLEntry,
    QuestionStatus,
    ReconciliationResult,
    ReviewDecision,
    Severity,
    Treatment,
    Workpaper,
)

DATA_ROOT = PROJECT_ROOT / "data" / "qoe"
DEAL_SPLITS = ("dev", "holdout")

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
    def timing(self) -> Path:
        return self.root / TIMING_LOG_NAME

    @property
    def xlsx(self) -> Path:
        return self.root / f"QoE_Evidence_Review_{self.deal_id}.xlsx"


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


def discover_deals(root_dir: Optional[Path] = None, splits: Iterable[str] = DEAL_SPLITS) -> list[DealOption]:
    out: list[DealOption] = []
    for split in splits:
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


def flag_html(f: Flag) -> str:
    head = [severity_chip(f.severity), f"<b>{_esc(humanize_code(f.code))}</b>"]
    if f.period_label:
        head.append(f'<span class="qoe-src">{_esc(f.period_label)}</span>')
    if f.amount_impact not in (None, ""):
        head.append(f'<span class="qoe-src">EBITDA effect {_esc(fmt_amount(f.amount_impact))}</span>')
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


def bridge_summary_rows(bridge: EbitdaBridge) -> list[dict[str, Any]]:
    """GL reported / management reported / management adjusted / diligence adjusted."""
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
    return out


def bridge_rows(bridge: EbitdaBridge) -> list[dict[str, Any]]:
    out = []
    for r in bridge.rows:
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


def queue_columns(labels: list[str]) -> list[str]:
    cols = ["Ref", "Title", "Category", "Tool", "Reviewer", "Status", "Bridge"]
    for prefix in ("Claimed", "Proposed", "Final"):
        cols.extend(f"{prefix} {p}" for p in labels)
    return cols + ["Top flags", "Confidence", "GL links", "Docs", "Open Qs"]


def queue_rows(
    wp: Workpaper,
    latest: Mapping[str, ReviewDecision],
    finals: Mapping[str, dict[str, str]],
    tolerance: object = "1.00",
) -> list[dict[str, Any]]:
    labels = [p.label for p in wp.deal.periods]
    out = []
    for a in wp.assessments:
        d = latest.get(a.adj_id)
        final = finals.get(a.adj_id, {})
        status = review_status(a, d, tolerance)
        if d is not None and decision_is_stale(a, d, tolerance):
            status += " (tool proposal changed since review)"
        rec: dict[str, Any] = {
            "Ref": a.adj_id,
            "Title": a.title,
            "Category": category_label(a.category),
            "Tool": TREATMENT_LABELS[a.treatment],
            "Reviewer": TREATMENT_LABELS[d.treatment] if d is not None else "",
            "Status": status,
            "Bridge": "Included" if final else "Pending",
        }
        for p in labels:
            rec[f"Claimed {p}"] = fmt_amount(a.claimed.get(p, "0"))
        for p in labels:
            rec[f"Proposed {p}"] = fmt_amount(a.proposed.get(p, "0")) if a.proposed else "pending"
        for p in labels:
            rec[f"Final {p}"] = fmt_amount(final.get(p)) if final else "pending"
        rec["Top flags"] = top_flags(a)
        rec["Confidence"] = a.confidence
        rec["GL links"] = sum(1 for g in a.gl_links if g.supports_claim)
        rec["Docs"] = len(a.doc_links)
        rec["Open Qs"] = _open_question_count(a)
        out.append(rec)
    return out


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


def gl_link_rows(a: AdjustmentAssessment, gl_by_id: Mapping[str, GLEntry]) -> list[dict[str, Any]]:
    challenged = flags_by_entry(a)

    def sort_key(link: Any) -> tuple:
        e = gl_by_id.get(link.entry_id)
        return (not link.supports_claim, e.date if e else link.period, link.entry_id)

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
                "Supports claim": "Yes" if link.supports_claim else "No (context)",
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


def question_rows(wp: Workpaper) -> list[dict[str, Any]]:
    out = []
    for a in wp.assessments:
        for q in a.open_questions:
            out.append(
                {
                    "Q id": q.q_id,
                    "Ref": q.adj_id or a.adj_id,
                    "Question": q.text,
                    "Priority": q.priority,
                    "Basis": q.basis,
                    "Status": q.status.value,
                    "Response": q.response,
                }
            )
    return out


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
        "open_questions": sum(_open_question_count(a) for a in wp.assessments),
        "stale": sum(
            1 for a in wp.assessments if a.adj_id in latest and decision_is_stale(a, latest[a.adj_id], tolerance)
        ),
    }


def decision_history_rows(decisions: Iterable[ReviewDecision], labels: list[str]) -> list[dict[str, Any]]:
    out = []
    for d in decisions:
        rec: dict[str, Any] = {
            "When (UTC)": d.timestamp,
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


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

_CSS = """
<style>
.qoe-banner{background:#FFF4E5;border:1px solid #E0A458;color:#7A4B00;padding:6px 12px;border-radius:4px;
  font-weight:600;letter-spacing:.03em;font-size:.85rem;margin-bottom:.5rem}
.qoe-chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.78rem;font-weight:600;
  margin-right:6px;border:1px solid rgba(0,0,0,.08);white-space:nowrap}
table.qoe{border-collapse:collapse;width:100%;font-size:.88rem;margin:.25rem 0 .75rem 0}
table.qoe th{text-align:left;border-bottom:2px solid rgba(128,128,128,.55);padding:4px 8px;font-weight:600}
table.qoe td{padding:3px 8px;border-bottom:1px solid rgba(128,128,128,.18)}
table.qoe .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
table.qoe tr.subtotal td{font-weight:600;border-top:1px solid rgba(128,128,128,.6)}
table.qoe tr.memo td{font-style:italic;opacity:.75}
table.qoe tr.component td:first-child,table.qoe tr.mgmt_adjustment td:first-child,
table.qoe tr.diligence_adjustment td:first-child{padding-left:22px}
.qoe-item{padding:6px 0 8px 0;border-bottom:1px solid rgba(128,128,128,.15)}
.qoe-quote{border-left:3px solid rgba(128,128,128,.55);padding:2px 10px;margin:4px 0 2px 0;font-family:Georgia,serif}
.qoe-src{font-size:.78rem;opacity:.72;margin-right:8px}
.qoe-muted{opacity:.7;font-size:.88rem}
.qoe-evidence{border-left:4px solid #5B8C5A;padding-left:12px}
.qoe-judgment{border-left:4px solid #C9A227;padding-left:12px}
.qoe-ask{border-left:4px solid #5B7A99;padding-left:12px}
.qoe-page{white-space:pre-wrap;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;line-height:1.35;
  max-height:460px;overflow:auto;border:1px solid rgba(128,128,128,.3);padding:8px;border-radius:4px}
.qoe-page mark{background:#FFE58F;color:#000;padding:0 1px}
</style>
"""


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
    for kind, text in st.session_state.pop("flash", []):
        getattr(st, kind, st.info)(text)


def _show_error(title: str, exc: BaseException) -> None:
    st.error(f"{title}: {type(exc).__name__}: {exc}")
    with st.expander("Technical details"):
        st.code("".join(traceback.format_exception(exc)), language="text")


def _render_safely(title: str, fn: Any, *args: Any) -> None:
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001 - keep the app up; show what failed
        _show_error(f"{title} could not be displayed", exc)


def _table(
    rows: list[dict[str, Any]],
    numeric: Iterable[str] = (),
    color_cols: Iterable[str] = (),
    height: Any = "auto",
    columns: Optional[list[str]] = None,
) -> None:
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
    st.dataframe(data, hide_index=True, column_config=config, height=height)


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("timer", {})
    ss.setdefault("form_errors", {})
    # Keep the adjustment selection when the detail page is not rendered (Streamlit
    # drops state for widgets that are not drawn in a run).
    if "adj_select" in ss:
        ss["adj_select"] = ss["adj_select"]


def _open_workpaper(deal_dir: Optional[Path], wp_path: Path) -> None:
    st.session_state["deal_dir"] = str(deal_dir) if deal_dir is not None else None
    st.session_state["wp_path"] = str(wp_path)
    st.session_state.pop("_applied", None)


def _goto(page: str, adj_id: Optional[str] = None) -> None:
    st.session_state["page"] = page
    if adj_id is not None:
        st.session_state["adj_select"] = adj_id


def _sidebar() -> None:
    sb = st.sidebar
    sb.markdown("**QoE Evidence Review**")
    sb.caption(f"Tool version {TOOL_VERSION}. Deal packages under data/qoe are SYNTHETIC.")
    deals = discover_deals()
    source = sb.radio("Deal package", ("Library", "Path"), horizontal=True, key="deal_source")
    deal_dir: Optional[Path] = None
    if source == "Library":
        if deals:
            opt = sb.selectbox("Deal", deals, format_func=lambda o: o.label, key="deal_option")
            deal_dir = opt.path if opt is not None else None
        else:
            sb.info("No deal packages under data/qoe/dev or data/qoe/holdout. Enter a path instead.")
    else:
        raw = sb.text_input("Deal directory", key="deal_path", placeholder="data/qoe/dev/<deal_id>")
        if raw.strip():
            deal_dir = resolve_user_path(raw)
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
        with st.spinner(f"Running review on {deal_dir.name} ({ai_mode})..."):
            path = run_and_save(deal_dir, ai_mode, workpapers_root())
    except Exception as exc:  # noqa: BLE001
        _show_error("The review run failed", exc)
        return
    _open_workpaper(deal_dir, path)
    shown = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    _flash("success", f"Review complete. Workpaper saved to {shown}.")
    st.rerun()  # redraw the sidebar with the view selector for the new run


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

    store = ReviewStore(paths.review_log)
    decisions = store.all()
    if store.skipped_lines:
        notes.append(
            f"Review log lines {', '.join(map(str, store.skipped_lines))} could not be read and were skipped "
            "(the log is never rewritten; inspect review_log.jsonl)."
        )

    log_sig = (paths.review_log.stat().st_size, paths.review_log.stat().st_mtime_ns) if paths.review_log.exists() else None
    key = (str(wp_path), wp_path.stat().st_mtime_ns, log_sig, pkg is not None)
    memo = ss.get("_applied")
    if memo is not None and memo[0] == key:
        wp, err = memo[1], memo[2]
    else:
        try:
            wp, err = apply_reviews(base, decisions, schedule=pkg.schedule if pkg is not None else None), None
        except Exception as exc:  # noqa: BLE001
            wp = base.model_copy(deep=True)
            wp.reviews = decisions
            apply_question_updates(wp.assessments, decisions)
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
    )


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
    st.title(meta.target_name)
    periods = ", ".join(f"{p.label} ({p.start} to {p.end})" for p in meta.periods)
    bits = [meta.industry, f"Deal {meta.deal_id}", periods, f"{meta.currency}", f"Tolerance {meta.tolerance}"]
    st.caption(" | ".join(_esc(b) for b in bits if b))


# ----------------------------- Overview -------------------------------------


def _page_overview(ctx: ReviewContext) -> None:
    wp = ctx.wp
    _deal_header(wp)
    st.caption(
        _esc(f"Run {wp.run_id} | created {wp.created_at} | AI {wp.ai_mode} | tool {wp.tool_version}")
    )
    for note in ctx.notes:
        st.warning(note)

    st.subheader("EBITDA bridge")
    st.html(html_table(["Line", *ctx.labels], bridge_summary_rows(wp.bridge), numeric=ctx.labels))
    try:
        diffs = check_bridge_identity(wp)
        if bridge_ties(diffs):
            st.caption("Check: diligence adjusted EBITDA = GL EBITDA + final adjustments (pending excluded). Ties in every period.")
        else:
            st.error("Bridge does not tie: " + ", ".join(f"{p} off by {fmt_amount(v, cents=True)}" for p, v in diffs.items()))
    except ValueError as exc:
        st.warning(f"Bridge check not available: {exc}")
    with st.expander("Full bridge: management adjustments and diligence revisions"):
        st.html(html_table(["Line", *ctx.labels], bridge_rows(wp.bridge), numeric=ctx.labels))

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
                    {"Measure": "Overridden by reviewer", "Count": counts["review"][STATUS_OVERRIDDEN]},
                    {"Measure": "Open questions for management", "Count": counts["open_questions"]},
                ],
                numeric=["Count"],
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


def _page_queue(ctx: ReviewContext) -> None:
    st.subheader("Adjustment queue")
    for note in ctx.notes:
        st.warning(note)
    rows = queue_rows(ctx.wp, ctx.latest, ctx.finals, ctx.tolerance)
    f1, f2, f3 = st.columns([2, 2, 3])
    tool_filter = f1.multiselect("Tool treatment", list(TREATMENT_LABELS.values()), key="q_tool")
    status_filter = f2.multiselect("Status", [STATUS_UNREVIEWED, STATUS_AGREED, STATUS_OVERRIDDEN], key="q_status")
    text = f3.text_input("Search ref, title or flag", key="q_text").strip().lower()
    shown = [
        r
        for r in rows
        if (not tool_filter or r["Tool"] in tool_filter)
        and (not status_filter or r["Status"].split(" (")[0] in status_filter)
        and (not text or text in f"{r['Ref']} {r['Title']} {r['Top flags']}".lower())
    ]
    amount_cols = [c for c in queue_columns(ctx.labels) if c.split(" ")[0] in ("Claimed", "Proposed", "Final")]
    _table(
        shown,
        numeric=amount_cols + ["GL links", "Docs", "Open Qs"],
        color_cols=["Tool", "Reviewer"],
        columns=queue_columns(ctx.labels),
    )
    st.caption("Final = reviewer's amounts where reviewed, otherwise the tool's proposal. Pending items are excluded from diligence adjusted EBITDA.")
    ids = [a.adj_id for a in ctx.wp.assessments]
    if ids:
        c1, c2 = st.columns([3, 1])
        titles = {a.adj_id: a.title for a in ctx.wp.assessments}
        pick = c1.selectbox("Open adjustment", ids, format_func=lambda i: f"{i}: {titles[i]}", key="q_pick")
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
    chips = [
        chip(category_label(a.category), "#E7E9EC", "#3C4650"),
        treatment_chip(a.treatment, prefix="Tool: "),
        chip(f"Confidence: {a.confidence}", "#E7E9EC", "#3C4650"),
    ]
    if decision is not None:
        chips.append(treatment_chip(decision.treatment, prefix="Reviewer: "))
    chips.append(chip(status, "#E7E9EC", "#3C4650"))
    if not final:
        chips.append(chip("Pending: excluded from diligence EBITDA", "#DDE3EA", "#2F3E50"))
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
    st.html("".join(flag_html(f) for f in sorted_flags(a.flags)) or "<div class='qoe-muted'>No flags.</div>")

    history = [d for d in ctx.decisions if d.adj_id == adj_id]
    t_gl, t_docs, t_rec, t_hist = st.tabs(
        [
            f"GL entries ({len(a.gl_links)})",
            f"Documents ({len(a.doc_links)})",
            f"Recurrence ({len(a.recurrence)})",
            f"Decision history ({len(history)})",
        ]
    )
    with t_gl:
        _render_safely("GL entries", _detail_gl, ctx, a)
    with t_docs:
        _render_safely("Documents", _detail_docs, ctx, a)
    with t_rec:
        _table(recurrence_rows(a, ctx.labels), numeric=ctx.labels + ["Entries"])
    with t_hist:
        _table(decision_history_rows(history, ctx.labels), numeric=ctx.labels, color_cols=["Treatment", "Tool"])

    st.divider()
    _render_safely("Review form", _review_form, ctx, a, decision)


def _detail_claim(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    claim = None
    if ctx.pkg is not None:
        claim = next((c for c in ctx.pkg.schedule.adjustments if c.adj_id == a.adj_id), None)
    st.markdown("**Management's claim and basis**")
    if claim is None:
        st.caption("Management's narrative is not stored in the workpaper and the deal package is not loaded.")
        return
    bits = []
    if claim.category_raw:
        bits.append(f"Category as presented: {claim.category_raw}")
    bits.append("GL accounts: " + (", ".join(claim.gl_accounts) if claim.gl_accounts else "none given"))
    bits.append("Support: " + (", ".join(claim.support_refs) if claim.support_refs else "none cited"))
    bits.append(f"Schedule row {claim.source_row}")
    st.html(
        f"<div>{_esc(claim.description) or '<span class=qoe-muted>No description given.</span>'}</div>"
        f"<div class='qoe-src'>{_esc(' | '.join(bits))}</div>"
    )


def _detail_gl(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    gl_by_id = {e.entry_id: e for e in ctx.pkg.gl} if ctx.pkg is not None else {}
    if not gl_by_id:
        st.caption("GL detail (date, account, memo) needs the deal package; showing the links only.")
    supporting = sum(1 for g in a.gl_links if g.supports_claim)
    st.caption(
        f"{supporting} entries support the claim; {len(a.gl_links) - supporting} are linked for context "
        "(comparables in other periods, excess activity, recoveries). 'Challenged by' names flags that remove or question the entry."
    )
    _table(gl_link_rows(a, gl_by_id), numeric=["GL row", "Amount", "Score"])


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


def _form_key(adj_id: str, name: str) -> str:
    return f"f:{adj_id}:{name}"


def _clear_form(adj_id: str) -> None:
    prefix = f"f:{adj_id}:"
    for k in [k for k in st.session_state.keys() if isinstance(k, str) and k.startswith(prefix)]:
        del st.session_state[k]


def _collect_form(a: AdjustmentAssessment, labels: list[str]) -> dict[str, Any]:
    ss = st.session_state
    edits = {}
    for q in a.open_questions:
        status = ss.get(_form_key(a.adj_id, f"q:{q.q_id}:status"), q.status)
        response = ss.get(_form_key(a.adj_id, f"q:{q.q_id}:response"), q.response)
        edits[q.q_id] = (QuestionStatus(status), str(response))
    return {
        "treatment": Treatment(ss.get(_form_key(a.adj_id, "treatment"), a.treatment)),
        "amounts": {p: ss.get(_form_key(a.adj_id, f"amt:{p}"), "") for p in labels},
        "rationale": str(ss.get(_form_key(a.adj_id, "rationale"), "")),
        "correction_type": CorrectionType(ss.get(_form_key(a.adj_id, "correction"), CorrectionType.NONE)),
        "reviewer": str(ss.get("reviewer", "")),
        "question_updates": question_update_values(a.open_questions, edits),
    }


def _record_decision(ctx: ReviewContext, a: AdjustmentAssessment) -> None:
    """Button callback: validate, append to the log, record time on task."""
    form = _collect_form(a, ctx.labels)
    try:
        decision = make_decision(
            a,
            treatment=form["treatment"],
            amounts=form["amounts"],
            rationale=form["rationale"],
            reviewer=form["reviewer"],
            labels=ctx.labels,
            correction_type=form["correction_type"],
            question_updates=form["question_updates"],
            tolerance=ctx.tolerance,
        )
    except DecisionError as exc:
        st.session_state["form_errors"][a.adj_id] = exc.errors
        return
    try:
        ReviewStore(ctx.paths.review_log).append(decision)
    except OSError as exc:
        st.session_state["form_errors"][a.adj_id] = [f"Could not write the review log: {exc}"]
        return
    st.session_state["form_errors"].pop(a.adj_id, None)
    now = datetime.now(timezone.utc)
    opened, seconds = finish_timing(st.session_state["timer"], a.adj_id, now)
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
    labels = ctx.labels
    default_t, default_amounts = form_defaults(a, decision, labels)
    options = list(Treatment)
    treatment = st.radio(
        "Treatment",
        options,
        index=options.index(default_t),
        format_func=lambda t: TREATMENT_LABELS[t],
        horizontal=True,
        key=_form_key(a.adj_id, "treatment"),
    )
    if treatment == Treatment.REVISE:
        st.caption("Diligence amounts by period (EBITDA-signed: + adds back). Prefilled with " + ("your last decision." if decision else "the tool's proposal."))
        cols = st.columns(len(labels) or 1)
        for col, p in zip(cols, labels):
            col.text_input(p, value=default_amounts.get(p, "0.00"), key=_form_key(a.adj_id, f"amt:{p}"))
    else:
        carried = resolve_amounts(a, treatment, {}, labels)
        if treatment == Treatment.REQUEST_INFO:
            st.caption("Request info: the adjustment is pending and excluded from diligence adjusted EBITDA until resolved.")
        else:
            what = "management's claimed amounts" if treatment == Treatment.ACCEPT else "zero in every period"
            st.caption(f"{TREATMENT_LABELS[treatment]} carries {what}.")
            st.html(html_table(labels, [{p: fmt_amount(carried.get(p)) for p in labels}], numeric=labels))

    corrections = list(CorrectionType)
    default_ct = decision.correction_type if decision is not None else CorrectionType.NONE
    c1, c2 = st.columns([2, 3])
    c1.selectbox(
        "Correction type",
        corrections,
        index=corrections.index(default_ct),
        format_func=lambda c: CORRECTION_LABELS[c],
        key=_form_key(a.adj_id, "correction"),
        help="Required when your decision differs from the tool. Tool-error types become regression cases; "
        "judgment differences and new information do not count against the tool.",
    )
    c2.text_area(
        "Rationale",
        value=decision.rationale if decision is not None else "",
        key=_form_key(a.adj_id, "rationale"),
        height=100,
        help="Required when you override the tool or classify a correction.",
    )

    if a.open_questions:
        with st.expander(f"Update questions for management ({len(a.open_questions)})"):
            statuses = list(QuestionStatus)
            for q in a.open_questions:
                st.html(f"<div class='qoe-src'>{_esc(q.q_id)} | {_esc(q.priority)}</div><div>{_esc(q.text)}</div>")
                q1, q2 = st.columns([1, 3])
                q1.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(q.status),
                    format_func=lambda s: s.value.capitalize(),
                    key=_form_key(a.adj_id, f"q:{q.q_id}:status"),
                )
                q2.text_input("Response", value=q.response, key=_form_key(a.adj_id, f"q:{q.q_id}:response"))

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
    )
    for w in warnings:
        st.warning(w)
    if errors:
        st.caption("Before recording: " + " ".join(errors))
    for e in st.session_state["form_errors"].pop(a.adj_id, []):  # shown once, after a failed submit
        st.error(e)
    st.button("Record decision", type="primary", on_click=_record_decision, args=(ctx, a))


# ----------------------------- Questions ------------------------------------


def _record_question_update(ctx: ReviewContext, q_id: str, adj_id: str) -> None:
    ss = st.session_state
    previous = ctx.latest.get(adj_id)
    question = next((q for a in ctx.wp.assessments for q in a.open_questions if q.q_id == q_id), None)
    if previous is None or question is None:
        return
    status_key, response_key = f"oq_status:{q_id}", f"oq_response:{q_id}"
    edits = {q_id: (QuestionStatus(ss.get(status_key, question.status)), str(ss.get(response_key, question.response)))}
    updates = question_update_values([question], edits)
    if not updates:
        _flash("info", f"No change to {q_id}.")
        return
    decision = carry_forward_decision(previous, reviewer=str(ss.get("reviewer", "")), question_updates=updates)
    try:
        ReviewStore(ctx.paths.review_log).append(decision)
    except OSError as exc:
        _flash("error", f"Could not write the review log: {exc}")
        return
    for k in (status_key, response_key):
        ss.pop(k, None)
    _flash("success", f"{q_id} updated ({edits[q_id][0].value.capitalize()}).")


def _page_questions(ctx: ReviewContext) -> None:
    st.subheader("Open questions for management")
    rows = question_rows(ctx.wp)
    if not rows:
        st.info("The tool raised no questions for management.")
        return
    f1, f2, f3 = st.columns(3)
    status_f = f1.multiselect("Status", [s.value for s in QuestionStatus], default=[QuestionStatus.OPEN.value], key="oq_f_status")
    prio_f = f2.multiselect("Priority", ["high", "medium", "low"], key="oq_f_prio")
    order = {a.adj_id: i for i, a in enumerate(ctx.wp.assessments)}
    refs = sorted({r["Ref"] for r in rows}, key=lambda r: (order.get(r, len(order)), r))
    ref_f = f3.multiselect("Adjustment", refs, key="oq_f_ref")
    shown = [
        r
        for r in rows
        if (not status_f or r["Status"] in status_f)
        and (not prio_f or r["Priority"] in prio_f)
        and (not ref_f or r["Ref"] in ref_f)
    ]
    shown.sort(key=lambda r: PRIORITY_ORDER.get(r["Priority"], 9))
    _table(shown)

    import pandas as pd

    buf = io.StringIO()
    pd.DataFrame(shown or rows).to_csv(buf, index=False)
    st.download_button(
        "Download as CSV (information request list)",
        data=buf.getvalue().encode("utf-8"),
        file_name=f"QoE_open_questions_{ctx.wp.deal.deal_id}.csv",
        mime="text/csv",
    )

    st.markdown("**Update a question**")
    q_ids = [r["Q id"] for r in shown] or [r["Q id"] for r in rows]
    by_id = {r["Q id"]: r for r in rows}
    q_id = st.selectbox("Question", q_ids, format_func=lambda q: f"{q}: {by_id[q]['Question'][:90]}", key="oq_pick")
    row = by_id[q_id]
    c1, c2 = st.columns([1, 3])
    statuses = list(QuestionStatus)
    c1.selectbox(
        "Status",
        statuses,
        index=statuses.index(QuestionStatus(row["Status"])),
        format_func=lambda s: s.value.capitalize(),
        key=f"oq_status:{q_id}",
    )
    c2.text_input("Response", value=row["Response"], key=f"oq_response:{q_id}")
    adj_id = row["Ref"]
    if adj_id not in ctx.latest:
        st.caption(
            f"{adj_id} has no reviewer decision yet. Question updates are recorded with a decision: "
            "update this question from the adjustment's review form."
        )
        st.button("Open adjustment", on_click=_goto, args=("Adjustment detail", adj_id))
    else:
        st.caption(f"Recorded as a new log line that re-affirms the current decision on {adj_id}.")
        st.button("Record update", type="primary", on_click=_record_question_update, args=(ctx, q_id, adj_id))


# ----------------------------- Export ---------------------------------------


def _page_export(ctx: ReviewContext) -> None:
    st.subheader("Export")
    counts = status_counts(ctx.wp, ctx.latest, ctx.finals, ctx.tolerance)
    if counts["review"][STATUS_UNREVIEWED]:
        st.warning(
            f"{counts['review'][STATUS_UNREVIEWED]} adjustment(s) are unreviewed. The workpaper carries the tool's "
            "proposal for them and marks them unreviewed."
        )
    for note in ctx.notes:
        st.warning(note)
    if st.button("Build Excel workpaper", type="primary"):
        try:
            import inspect

            from qoe.export_xlsx import export_workpaper

            # SPEC signature is (wp, out_path); pass the deal package too when the exporter accepts it.
            extra = {"pkg": ctx.pkg} if ctx.pkg is not None and "pkg" in inspect.signature(export_workpaper).parameters else {}
            with st.spinner("Writing workbook..."):
                out = export_workpaper(ctx.wp, ctx.paths.xlsx, **extra)
            st.success(f"Written to {out}")
        except Exception as exc:  # noqa: BLE001
            _show_error("Export failed", exc)
    if ctx.paths.xlsx.is_file():
        st.download_button(
            f"Download {ctx.paths.xlsx.name}",
            data=ctx.paths.xlsx.read_bytes(),
            file_name=ctx.paths.xlsx.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    c1, c2 = st.columns(2)
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
        st.caption("Tool errors on: " + ", ".join(summary["tool_error_adj_ids"]))
    if summary["unclassified_overrides"]:
        st.warning("Overrides without a correction type: " + ", ".join(summary["unclassified_overrides"]))

    st.subheader("Time on task")
    timing = timing_summary(load_timing(ctx.paths.timing))
    if not timing["per_adjustment"]:
        st.caption("No timed decisions yet. Time is measured from session timestamps while an adjustment's detail page is open.")
        return
    avg = timing["total_seconds"] // max(1, timing["adjustments"])
    st.caption(
        f"{timing['adjustments']} adjustment(s), {timing['decisions']} decision(s), "
        f"{fmt_duration(timing['total_seconds'])} in total; mean {fmt_duration(avg)} and median "
        f"{fmt_duration(timing['median_seconds_per_adjustment'])} per adjustment. Stored in {ctx.paths.timing.name}."
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
