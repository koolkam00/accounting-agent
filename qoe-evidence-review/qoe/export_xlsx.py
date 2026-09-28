"""Excel workpaper export for QoE Evidence Review (SPEC §8).

Writes ``QoE_Evidence_Review_<deal_id>.xlsx``: Cover, EBITDA Bridge,
Adjustment Summary, one support sheet per adjustment, Open Questions,
GL-P&L Reconciliation, Data Quality, and Review Log.

Deals workpaper conventions used throughout:

- Arial everywhere. Amounts use ``#,##0;(#,##0);"-"``: whole dollars are
  displayed, cell values keep cents. Every amount header states its sign
  basis: adjustment amounts (claimed, proposed, final, flag effects) are
  EBITDA-signed, so + increases EBITDA; GL and P&L amounts are
  debit-positive. On a support sheet a GL entry's debit-positive amount is
  also its effect on the adjustment, so the two bases agree there.
- Blue font = hard-coded input carried from the workpaper; black = formula;
  green = link to another sheet. Light-yellow cells are sign-off inputs.
- Subtotals, differences, totals, and checks are live Excel formulas built
  only from Excel-2007 functions, so the file recalculates cleanly in Excel
  and in LibreOffice. Every check ("should be zero") rolls up, by area, into
  the Cover's "Workbook checks".
- Audit trail on each support sheet. Every linked GL entry carries a
  tickmark for its role in the adjustment, from ``GLLink.role`` /
  ``claimed`` / ``removed_by``: T supporting, R removed (citing the flag),
  M moved by an out-of-period flag, O recovery / offset, X context only. The
  listing spreads each entry's amount into the analysis periods it counts
  in, and per-period SUMIFS rows above it tie the listing to (b) Traced and
  (d) Tool proposed. A walk built from ``Flag.effects`` takes (a) Claimed to
  (d), one flag per line. Document ticks are vouched per entry (D own
  document, A agreement, S sample, U draft, C correspondence).
- Final amounts follow the review log (the latest decision per adjustment
  wins). An adjustment without a decision carries the tool proposal and is
  marked UNREVIEWED; a REQUEST_INFO item is "Pending" and is excluded from
  diligence adjusted EBITDA. Every sheet says DRAFT while any item is
  unreviewed or the Cover sign-off is open.
- Diligence-identified items (``source == "diligence"``, SPEC §5.7: e.g. a
  duplicate posting to reverse) are not on management's schedule. They get
  their own block in the Adjustment Summary, the Bridge (after the diligence
  revisions to management's items) and the Cover counts, and a support sheet
  like any other item ("Adj D-1"). Their claimed amount is zero, so the final
  amount is the whole adjustment.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE, Cell
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.indexed_list import IndexedList
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.worksheet import Worksheet

from qoe.money import D, fmt, period_map, q2
from qoe.periods import labels_for_month, months_in
from qoe.review_store import bridge_display_rows, bridge_row_adj_id, is_item_row
from qoe.schemas import (
    AdjustmentAssessment,
    AdjustmentCategory,
    AdjustmentClaim,
    BridgeRow,
    DataQualityCode,
    DealPackage,
    DocFacts,
    EvidenceQuote,
    Flag,
    FlagCode,
    GLEntry,
    GLLink,
    ManagementSchedule,
    OpenQuestion,
    QuestionStatus,
    ReviewDecision,
    Severity,
    TOOL_ERROR_CORRECTIONS,
    Treatment,
    Workpaper,
)

__all__ = [
    "SHEET_BRIDGE",
    "SHEET_COVER",
    "SHEET_DATA_QUALITY",
    "SHEET_QUESTIONS",
    "SHEET_RECON",
    "SHEET_REVIEW_LOG",
    "SHEET_SUMMARY",
    "build_workbook",
    "export_workpaper",
    "find_recalc_script",
    "latest_reviews",
    "recalc_and_check",
    "resolve_final_amounts",
    "sanitize_sheet_name",
    "support_sheet_names",
    "workbook_filename",
]

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

FONT_NAME = "Arial"
NUMBER_FORMAT = '#,##0;(#,##0);"-"'
CHECK_FORMAT = '#,##0.00;(#,##0.00);"-"'
DATE_FORMAT = "dd-mmm-yyyy"
MONTH_FORMAT = "mmm-yy"

INPUT_BLUE = "0000FF"
FORMULA_BLACK = "000000"
LINK_GREEN = "008000"
NAVY = "1F3864"
WHITE = "FFFFFF"
MUTED = "595959"
HYPERLINK_BLUE = "0563C1"
BANNER_RED = "C00000"
SUBTOTAL_FILL = "F2F2F2"
FINAL_FILL = "DDEBF7"
SECTION_FILL = "D9E1F2"
FACTS_BAND = "E2EFDA"
JUDGMENT_BAND = "FCE4D6"
CHECK_FAIL_FILL = "FFC7CE"
SIGNOFF_FILL = "FFF2CC"  # light yellow: a sign-off input the reviewer completes

# (fill, font) per treatment: ACCEPT green, REVISE amber, REJECT red, REQUEST_INFO blue-grey.
TREATMENT_STYLES: dict[Treatment, tuple[str, str]] = {
    Treatment.ACCEPT: ("C6EFCE", "006100"),
    Treatment.REVISE: ("FFEB9C", "9C5700"),
    Treatment.REJECT: ("FFC7CE", "9C0006"),
    Treatment.REQUEST_INFO: ("D6DCE4", "333F4F"),
}
TREATMENT_MEANING: dict[Treatment, str] = {
    Treatment.ACCEPT: "Evidence supports management's amount in every period (within tolerance).",
    Treatment.REVISE: "Evidence supports a different amount; the bridge carries the diligence amount.",
    Treatment.REJECT: "Evidence does not support an adjustment; the diligence amount is zero.",
    Treatment.REQUEST_INFO: "Pending information from management; excluded from diligence adjusted EBITDA.",
}
SEVERITY_STYLES: dict[Severity, tuple[str, str]] = {
    Severity.CRITICAL: ("FFC7CE", "9C0006"),
    Severity.WARNING: ("FFEB9C", "9C5700"),
    Severity.INFO: ("F2F2F2", "595959"),
}
_SEVERITY_RANK = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}

# Same vocabulary as the reviewer app (qoe.review_store), upper-cased for the workpaper.
DILIGENCE_SOURCE = "diligence"
DILIGENCE_BLOCK = "Diligence-identified items (not on management's schedule)"

UNREVIEWED = "UNREVIEWED"
AGREED = "AGREED"
OVERRIDDEN = "OVERRIDDEN"
UNREVIEWED_STYLE = ("FFFF00", "000000")  # yellow = needs the reviewer's input
PENDING = "Pending"

# Role of a linked GL entry in the adjustment (GLLink.role) and its tickmark.
ROLE_TICKMARKS: list[tuple[str, str]] = [
    ("T", "Supporting: management claimed the entry and it survives every challenge; carried in (d) Tool proposed."),
    ("R", "Removed: management claimed the entry and the flag cited beside it (e.g. F2) takes it out of (d)."),
    ("M", "Moved: management claimed the entry; an out-of-period flag carries it in the period of the service."),
    ("O", "Offset: a recovery or reimbursement (e.g. insurance proceeds) that (d) deducts from the adjustment."),
    ("X", "Context only: linked for comparison (another period, excess activity); not part of management's claim."),
]
DOC_TICKMARKS: list[tuple[str, str]] = [
    ("D", "Vouched to the entry's own document (its document number, or the same amount, party and month)."),
    ("A", "Agreement-level support only (engagement letter, contract, settlement), not a bill for the entry."),
    ("S", "Sample support only: a document for the same charge in another month or under another number."),
    ("U", "Draft or unsigned document: it does not support the entry until executed."),
    ("C", "Company correspondence or memo: a management representation, not documentary support."),
]
TICKMARKS: list[tuple[str, str]] = [
    *ROLE_TICKMARKS,
    *DOC_TICKMARKS,
    ("F", "Entry is cited by a flag (F1, F2, ...); see the Flags block on the support sheet."),
    ("V", "Quote verified verbatim against the cited page text. Quotes that fail are dropped, never repaired."),
]
_ROLE_TICK = {"supporting": "T", "removed": "R", "moved": "M", "recovery": "O", "context": "X"}
_ROLE_RANK = {"T": 0, "R": 1, "M": 2, "O": 3, "X": 4}
_DOC_TICK_RANK = {"D": 0, "A": 1, "S": 2, "U": 3, "C": 4}
_REMOVED_REASON = re.compile(r"^Removed \(([A-Z_]+)\)")

# Mirrors qoe.trace: document types that set terms, and the company's own representations.
_AGREEMENT_DOC_TYPES = frozenset({
    "engagement_letter", "contract", "settlement_agreement", "separation_agreement", "agreement",
    "employment_agreement", "lease", "insurance",
})
_CORRESPONDENCE_DOC_TYPES = frozenset({"correspondence", "memo", "email"})
_PARTY_STOPWORDS = frozenset({"llc", "inc", "co", "corp", "corporation", "company", "the", "lp", "llp", "pa", "na",
                              "ltd", "and", "of", "plc", "pc"})

SHEET_COVER = "Cover"
SHEET_BRIDGE = "EBITDA Bridge"
SHEET_SUMMARY = "Adjustment Summary"
SHEET_QUESTIONS = "Open Questions"
SHEET_RECON = "GL-P&L Reconciliation"
SHEET_DATA_QUALITY = "Data Quality"
SHEET_REVIEW_LOG = "Review Log"
_FIXED_SHEETS = (
    SHEET_COVER,
    SHEET_BRIDGE,
    SHEET_SUMMARY,
    SHEET_QUESTIONS,
    SHEET_RECON,
    SHEET_DATA_QUALITY,
    SHEET_REVIEW_LOG,
)

# Check areas: each rolls up to one line of the Cover's checks table.
AREA_BRIDGE = "EBITDA Bridge: subtotals and line-by-line ties to the Adjustment Summary"
AREA_SUMMARY = "Adjustment Summary: difference total ties to the EBITDA Bridge"
AREA_SUPPORT = "Support sheets: bridge revision, GL listing ties to (b) and (d), flag walks"
AREA_SOURCE = "Agreement to source data: management's schedule and the GL reconciliation"
_WORKBOOK_AREAS = (AREA_BRIDGE, AREA_SUMMARY, AREA_SUPPORT)

_CATEGORY_LABELS = {
    AdjustmentCategory.NON_RECURRING: "Non-recurring",
    AdjustmentCategory.OWNER_DISCRETIONARY: "Owner / discretionary",
    AdjustmentCategory.NORMALIZATION: "Normalization",
    AdjustmentCategory.OUT_OF_PERIOD: "Out-of-period",
    AdjustmentCategory.PRO_FORMA: "Pro forma",
    AdjustmentCategory.OTHER: "Other",
}
_ACRONYMS = {"gl": "GL", "ebitda": "EBITDA", "doc": "Document"}

# The basis of a question, as management should read it (no internal codes).
_PLAIN_BASIS: dict[str, str] = {
    FlagCode.NO_GL_SUPPORT.value: "Amount not found in the general ledger",
    FlagCode.PARTIAL_GL_SUPPORT.value: "Only part of the amount found in the general ledger",
    FlagCode.EXCESS_GL_ACTIVITY.value: "Which ledger entries make up the amount",
    FlagCode.NO_DOCUMENT_SUPPORT.value: "Supporting documents needed",
    FlagCode.DOC_GL_AMOUNT_MISMATCH.value: "Document and ledger amounts differ",
    FlagCode.PERIOD_MISMATCH.value: "Timing of the costs",
    FlagCode.OUT_OF_PERIOD.value: "Cost relates to a different period",
    FlagCode.RECURRING_PATTERN.value: "Similar costs in other periods",
    FlagCode.CONTINUING_OBLIGATION.value: "Ongoing contract terms",
    FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT.value: "Same cost in more than one adjustment",
    FlagCode.ALREADY_EXCLUDED_FROM_EBITDA.value: "Cost already outside EBITDA (interest, taxes, depreciation)",
    FlagCode.OFFSETTING_RECOVERY.value: "Related recovery or reimbursement",
    FlagCode.CONTRADICTORY_EVIDENCE.value: "Documents describe the cost differently",
    FlagCode.UNSIGNED_OR_DRAFT_SUPPORT.value: "Executed (signed) agreement needed",
    FlagCode.PRO_FORMA_NOT_REALIZED.value: "Evidence the change has happened",
    FlagCode.SIGN_ERROR.value: "Direction of the adjustment",
    FlagCode.DUPLICATE_GL_ENTRY.value: "Possible duplicate posting",
    FlagCode.NORMALIZATION_BENCHMARK_MISSING.value: "Basis for the normalized level",
    DataQualityCode.MISSING_PERIOD.value: "Missing ledger months",
    DataQualityCode.RECON_VARIANCE.value: "Ledger and monthly P&L differ",
    DataQualityCode.UNMAPPED_ACCOUNT.value: "Account classification",
    DataQualityCode.PL_ACCOUNT_NOT_IN_GL.value: "P&L account missing from the ledger",
    DataQualityCode.GL_ACCOUNT_NOT_IN_PL.value: "Ledger account missing from the P&L",
    DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL.value: "Reported EBITDA differs from the ledger",
    DataQualityCode.MGMT_SCHEDULE_ARITHMETIC.value: "Arithmetic of the adjusted EBITDA schedule",
}
_PLAIN_BASIS_PREFIXES = (("ai:", "Follow-up from the document review"), ("reviewer", "Diligence team request"))
# Sentences in tool-drafted questions that describe the workpaper's own conclusions, not a request.
_INTERNAL_SENTENCES = (
    re.compile(r"^Removed\b"),
    re.compile(r"\bcombinations? tie\b", re.I),
    re.compile(r"^Effect:"),
    re.compile(r"^(?:Proposed|Tool proposed)\b"),
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+(?=[A-Z0-9(\"'“])")
_ENUM_CODE = re.compile(r"\b[A-Z][A-Z]+(?:_[A-Z]+)+\b")

# How each data quality amount is signed.
_DQ_SIGN_BASIS: dict[DataQualityCode, str] = {
    DataQualityCode.RECON_VARIANCE: "P&L less GL, debit + (+ = P&L expense higher)",
    DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL: "EBITDA: management less GL (+ = management higher)",
    DataQualityCode.DUPLICATE_GL_ENTRY: "GL amount per posting, debit +",
    DataQualityCode.GL_ACCOUNT_NOT_IN_PL: "GL activity in the data range, debit +",
    DataQualityCode.PL_ACCOUNT_NOT_IN_GL: "P&L amount in the data range, debit +",
}

_THIN = Side(style="thin", color="808080")
_THIN_BLACK = Side(style="thin", color="000000")
_DOUBLE = Side(style="double", color="000000")
_HEADER_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_TOP_BORDER = Border(top=_THIN_BLACK)
_FINAL_BORDER = Border(top=_THIN_BLACK, bottom=_DOUBLE)
_CENTER = Alignment(horizontal="center", vertical="top")

_BAD_SHEET_CHARS = re.compile(r"[\[\]:*?/\\']")
_GL_ROW = re.compile(r"^GL-R(\d+)$")
_MAX_CELL_TEXT = 32000  # Excel's hard limit is 32,767 characters per cell
_MAX_FORMULA = 8000  # Excel's formula length limit is 8,192 characters
_TOL = Decimal("0.005")

# LibreOffice recalculation uses the xlsx skill's recalc.py (found under ~/.claude/skills);
# QOE_RECALC_SCRIPT points at another copy.
_RECALC_ENV = "QOE_RECALC_SCRIPT"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def workbook_filename(wp: Workpaper) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", wp.deal.deal_id).strip("_") or "deal"
    return f"QoE_Evidence_Review_{safe}.xlsx"


def sanitize_sheet_name(name: str, used: Optional[set[str]] = None) -> str:
    """Excel-safe sheet name: no []:*?/\\', at most 31 chars, unique (case-insensitive) within ``used``."""
    s = ILLEGAL_CHARACTERS_RE.sub("", _BAD_SHEET_CHARS.sub("-", name)).strip() or "Sheet"
    s = s[:31].rstrip()
    if s.lower() == "history":  # reserved by Excel
        s = "History-"
    if used is not None:
        base, n = s, 2
        while s.lower() in used:
            suffix = f" ({n})"
            s = base[: 31 - len(suffix)].rstrip() + suffix
            n += 1
        used.add(s.lower())
    return s


def support_sheet_names(wp: Workpaper) -> dict[str, str]:
    """adj_id -> support sheet name ("Adj M-01"), unique and distinct from the fixed sheets."""
    used = {s.lower() for s in _FIXED_SHEETS}
    return {a.adj_id: sanitize_sheet_name(f"Adj {a.adj_id}", used) for a in wp.assessments}


def latest_reviews(wp: Workpaper) -> dict[str, ReviewDecision]:
    """Latest decision per adjustment; the review log is append-only, so list order decides."""
    latest: dict[str, ReviewDecision] = {}
    for rv in wp.reviews:
        latest[rv.adj_id] = rv
    return latest


def _fallback_final_amounts(wp: Workpaper, reviews: dict[str, ReviewDecision]) -> dict[str, dict[str, str]]:
    """Same semantics as qoe.review_store.final_amounts, used when that module is unavailable."""
    out: dict[str, dict[str, str]] = {}
    for a in wp.assessments:
        rv = reviews.get(a.adj_id)
        if rv is not None:
            out[a.adj_id] = {} if rv.treatment == Treatment.REQUEST_INFO else dict(rv.amounts)
        elif a.treatment == Treatment.REQUEST_INFO:
            out[a.adj_id] = {}
        else:
            out[a.adj_id] = dict(a.proposed)
    return out


def resolve_final_amounts(wp: Workpaper) -> dict[str, dict[str, str]]:
    """adj_id -> period -> final amount; ``{}`` means pending (excluded from diligence EBITDA)."""
    reviews = latest_reviews(wp)
    fallback = _fallback_final_amounts(wp, reviews)
    try:
        from qoe.review_store import final_amounts
    except ImportError:
        raw = fallback
    else:
        raw = final_amounts(wp, reviews)
    labels = _period_labels(wp)
    out: dict[str, dict[str, str]] = {}
    for a in wp.assessments:
        amounts = raw.get(a.adj_id, fallback[a.adj_id])
        out[a.adj_id] = period_map(amounts, labels) if amounts else {}
    return out


def find_recalc_script() -> Optional[Path]:
    """Locate the xlsx skill's LibreOffice recalc script, or None."""
    env = os.environ.get(_RECALC_ENV)
    candidates: list[Path] = [Path(env)] if env else []
    skills = Path.home() / ".claude" / "skills"
    if skills.is_dir():
        for pattern in ("*/xlsx/scripts/recalc.py", "*/*/xlsx/scripts/recalc.py"):
            candidates.extend(sorted(skills.glob(pattern)))
    for c in candidates:
        if c.is_file():
            return c
    return None


def recalc_and_check(path: Path, timeout: int = 90) -> dict[str, Any]:
    """Recalculate every formula with LibreOffice (rewrites the file in place) and report errors.

    Returns the recalc script's JSON (``status`` / ``total_errors`` / ``error_summary`` /
    ``total_formulas``), ``{"status": "skipped", "reason": ...}`` when LibreOffice or the
    script is unavailable, or ``{"error": ...}`` when recalculation failed.
    """
    script = find_recalc_script()
    if script is None:
        return {"status": "skipped", "reason": "recalc.py not found (set QOE_RECALC_SCRIPT)"}
    if shutil.which("soffice") is None:
        return {"status": "skipped", "reason": "LibreOffice (soffice) is not on PATH"}
    result = _run_recalc(script, Path(path), timeout)
    if "error" in result:
        # A concurrent LibreOffice start-up occasionally fails or stalls; one retry clears it.
        result = _run_recalc(script, Path(path), timeout)
    return result


def _run_recalc(script: Path, path: Path, timeout: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, str(script), str(path.resolve()), str(timeout)],
            capture_output=True,
            text=True,
            timeout=timeout + 60,
            cwd=str(script.parent),
        )
    except subprocess.TimeoutExpired:
        return {"error": f"recalc timed out after {timeout + 60}s"}
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "recalc produced no JSON", "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    return result if isinstance(result, dict) else {"error": f"unexpected recalc output: {result!r}"}


def export_workpaper(wp: Workpaper, out_path: Path, *, pkg: Optional[DealPackage] = None) -> Path:
    """Write the Excel workpaper and return its path.

    ``out_path`` is either the .xlsx path or a directory (the file is then named
    ``QoE_Evidence_Review_<deal_id>.xlsx``). ``pkg`` is optional: when given, the
    support sheets show management's description and full GL detail (date,
    account, counterparty, doc #, memo) for linked entries, which the
    workpaper itself does not carry.
    """
    out_path = Path(out_path)
    if out_path.is_dir() or out_path.suffix.lower() != ".xlsx":
        out_path = out_path / workbook_filename(wp)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = build_workbook(wp, pkg=pkg)
    tmp = out_path.with_name(out_path.stem + ".partial.xlsx")
    wb.save(tmp)
    os.replace(tmp, out_path)  # a reviewer's open copy is never left half-written
    return out_path


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


@dataclass
class _PrintSpec:
    title_rows: Optional[str] = None  # "6:7"
    title_cols: int = 0  # leading columns repeated on every page across
    last_col: int = 0  # last printed column (0 = every column with a width)
    last_row: int = 0  # last printed row (0 = the whole sheet)


@dataclass
class _Ctx:
    wp: Workpaper
    labels: list[str]
    latest: dict[str, ReviewDecision]
    final: dict[str, dict[str, str]]
    gl_by_id: dict[str, GLEntry]
    claims: dict[str, AdjustmentClaim]
    schedule: Optional[ManagementSchedule]
    doc_facts: dict[str, DocFacts]
    adj_sheets: dict[str, str]
    questions: dict[str, list[OpenQuestion]]
    drafted: dict[str, OpenQuestion]  # pending items with no open question: a request drafted for them
    has_gl_detail: bool
    records_roles: bool  # the workpaper records GLLink.role / claimed (the listing ties can be relied on)
    records_effects: bool  # the workpaper records Flag.effects (the flag walks can be relied on)
    bridge_keys: set[str]
    checks: dict[str, list[str]] = field(default_factory=dict)  # area -> absolute-difference expressions
    prints: dict[str, _PrintSpec] = field(default_factory=dict)  # sheet title -> print setup

    @property
    def currency(self) -> str:
        return self.wp.deal.currency or "USD"

    def status(self, adj_id: str) -> str:
        rv = self.latest.get(adj_id)
        if rv is None:
            return UNREVIEWED
        return OVERRIDDEN if _differs_from_tool(rv.treatment, rv.amounts, rv.tool_treatment, rv.tool_amounts,
                                                self.wp.deal.tolerance) else AGREED

    def stale(self, rv: ReviewDecision) -> bool:
        """The tool's current proposal differs from what the reviewer saw."""
        a = next((x for x in self.wp.assessments if x.adj_id == rv.adj_id), None)
        if a is None:
            return False
        return _differs_from_tool(a.treatment, a.proposed, rv.tool_treatment, rv.tool_amounts, self.wp.deal.tolerance)

    def final_treatment(self, a: AdjustmentAssessment) -> Treatment:
        rv = self.latest.get(a.adj_id)
        return rv.treatment if rv is not None else a.treatment

    def final_pending(self, a: AdjustmentAssessment) -> bool:
        return not self.final.get(a.adj_id)

    @property
    def mgmt_items(self) -> list[AdjustmentAssessment]:
        return [a for a in self.wp.assessments if not _is_diligence(a)]

    @property
    def dil_items(self) -> list[AdjustmentAssessment]:
        return [a for a in self.wp.assessments if _is_diligence(a)]

    @property
    def unreviewed(self) -> list[str]:
        return [a.adj_id for a in self.wp.assessments if a.adj_id not in self.latest]

    def add_check(self, area: str, expr: str) -> None:
        self.checks.setdefault(area, []).append(expr)


def _is_diligence(a: AdjustmentAssessment) -> bool:
    return a.source == DILIGENCE_SOURCE


def _period_labels(wp: Workpaper) -> list[str]:
    return list(wp.bridge.period_labels) or [p.label for p in wp.deal.periods]


def _context(wp: Workpaper, pkg: Optional[DealPackage]) -> _Ctx:
    schedule: Optional[ManagementSchedule] = pkg.schedule if pkg is not None else getattr(wp, "schedule", None)
    claims = {c.adj_id: c for c in schedule.adjustments} if schedule is not None else {}
    gl_by_id = {e.entry_id: e for e in pkg.gl} if pkg is not None else {}
    latest = latest_reviews(wp)
    final = resolve_final_amounts(wp)
    questions = _questions_with_updates(wp)
    drafted: dict[str, OpenQuestion] = {}
    for a in wp.assessments:
        if final.get(a.adj_id) or any(q.status == QuestionStatus.OPEN for q in questions.get(a.adj_id, [])):
            continue
        # SPEC §7: a pending item waits on management, so the request list must ask for something.
        rv = latest.get(a.adj_id)
        tool_reason = re.sub(r"^(?:ACCEPT|REVISE|REJECT|REQUEST_INFO):\s*", "", _first_sentence(a.rationale))
        reason = (rv.rationale if rv is not None else "") or tool_reason
        drafted[a.adj_id] = OpenQuestion(
            q_id=f"Q-{a.adj_id}-P", adj_id=a.adj_id, priority="high",
            basis="reviewer: item on hold pending information",
            text=f"{a.title}: please provide the information needed to resolve this item. {reason.strip()}",
        )
        questions[a.adj_id] = [*questions.get(a.adj_id, []), drafted[a.adj_id]]
    links = [lk for a in wp.assessments for lk in a.gl_links]
    return _Ctx(
        wp=wp,
        labels=_period_labels(wp),
        latest=latest,
        final=final,
        gl_by_id=gl_by_id,
        claims=claims,
        schedule=schedule,
        doc_facts={f.doc_id: f for f in wp.doc_facts},
        adj_sheets=support_sheet_names(wp),
        questions=questions,
        drafted=drafted,
        has_gl_detail=pkg is not None,
        records_roles=any(lk.role for lk in links),
        records_effects=any(f.effects for a in wp.assessments for f in a.flags),
        bridge_keys={r.key for r in bridge_display_rows(wp.bridge.rows, {a.adj_id for a in wp.assessments
                                                                           if _is_diligence(a)})},
    )


def _questions_with_updates(wp: Workpaper) -> dict[str, list[OpenQuestion]]:
    """Open questions per adjustment with reviewer status/response updates applied in log order.

    An update value is a status ("ANSWERED"), a status with a note ("ANSWERED: insurer
    confirmed"), or a free-text response.
    """
    statuses = {s.value for s in QuestionStatus}
    by_id: dict[str, OpenQuestion] = {}
    order: dict[str, list[str]] = {}
    for a in wp.assessments:
        order[a.adj_id] = []
        for q in a.open_questions:
            by_id[q.q_id] = q
            order[a.adj_id].append(q.q_id)
    for rv in wp.reviews:
        for q_id, note in rv.question_updates.items():
            q = by_id.get(q_id)
            if q is None:
                continue
            text = note.strip()
            head, sep, rest = text.partition(":")
            if text.upper() in statuses:
                by_id[q_id] = q.model_copy(update={"status": QuestionStatus(text.upper())})
            elif sep and head.strip().upper() in statuses:
                by_id[q_id] = q.model_copy(
                    update={"status": QuestionStatus(head.strip().upper()), "response": rest.strip()}
                )
            elif text:
                by_id[q_id] = q.model_copy(update={"response": text})
    return {adj: [by_id[q] for q in ids] for adj, ids in order.items()}


# ---------------------------------------------------------------------------
# Cell writing
# ---------------------------------------------------------------------------


def _clean(value: str) -> str:
    text = ILLEGAL_CHARACTERS_RE.sub("", value)
    return text if len(text) <= _MAX_CELL_TEXT else text[: _MAX_CELL_TEXT - 3] + "..."


def _fill(rgb: str) -> PatternFill:
    return PatternFill(fill_type="solid", start_color=rgb, end_color=rgb)


def _quoted(sheet: str) -> str:
    return "'" + sheet.replace("'", "''") + "'"


def _xref(sheet: str, col: int, row: int) -> str:
    return f"{_quoted(sheet)}!{get_column_letter(col)}{row}"


def _a1(col: int, row: int) -> str:
    return f"{get_column_letter(col)}{row}"


def _abs_range(sheet: str, first_col: int, last_col: int, row: int) -> str:
    """SUMPRODUCT(ABS(...)) over one row of check cells: the check's absolute difference."""
    return (f"SUMPRODUCT(ABS({_quoted(sheet)}!${get_column_letter(first_col)}${row}:"
            f"${get_column_letter(last_col)}${row}))")


def _to_date(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return date.fromisoformat(iso[:10])
    except ValueError:
        return None


def _month_date(month: str) -> Optional[date]:
    try:
        y, m = month.split("-")[:2]
        return date(int(y), int(m), 1)
    except (ValueError, AttributeError):
        return None


def _wrapped_lines(text: str, per_line: int) -> int:
    """Lines a wrapped cell needs: greedy word wrap, with over-long tokens (paths, ids) broken by characters."""
    per_line = max(per_line, 4)
    total = 0
    for para in text.split("\n"):
        lines, cur = 1, 0
        for word in para.split(" "):
            n = len(word)
            if cur and cur + 1 + n <= per_line:
                cur += 1 + n
                continue
            if cur:
                lines += 1
            extra, rest = divmod(n, per_line)
            if extra and not rest:
                extra, rest = extra - 1, per_line
            lines += extra
            cur = rest
        total += lines
    return total


class _Sheet:
    """Thin writer over a worksheet: consistent Arial styling, merged spans, row-height fitting."""

    def __init__(self, ws: Worksheet, widths: Sequence[float]):
        self.ws = ws
        self.widths = list(widths)
        for i, w in enumerate(self.widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

    @property
    def last_col(self) -> int:
        return len(self.widths)

    def span_width(self, col: int, span: int) -> float:
        return sum(self.widths[c - 1] if c - 1 < len(self.widths) else 9.0 for c in range(col, col + span))

    def put(
        self,
        row: int,
        col: int,
        value: Any = None,
        *,
        span: int = 1,
        bold: bool = False,
        italic: bool = False,
        color: str = FORMULA_BLACK,
        size: float = 10,
        fill: Optional[str] = None,
        num_fmt: Optional[str] = None,
        wrap: bool = False,
        halign: Optional[str] = None,
        valign: str = "top",
        border: Optional[Border] = None,
        underline: Optional[str] = None,
        indent: int = 0,
    ) -> Cell:
        cell = self.ws.cell(row=row, column=col)
        if isinstance(value, str):
            value = _clean(value)
            cell.value = value
            if value.startswith("="):  # text that merely looks like a formula stays text
                cell.data_type = "s"
        else:
            cell.value = value
        cell.font = Font(name=FONT_NAME, size=size, bold=bold, italic=italic, color=color, underline=underline)
        cell.alignment = Alignment(horizontal=halign, vertical=valign, wrap_text=wrap, indent=indent)
        if num_fmt:
            cell.number_format = num_fmt
        targets = [self.ws.cell(row=row, column=c) for c in range(col, col + span)]
        if fill:
            for t in targets:
                t.fill = _fill(fill)
        if border is not None:
            for t in targets:
                t.border = border
        if span > 1:
            self.ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + span - 1)
        if wrap and isinstance(value, str):
            self.fit(row, value, self.span_width(col, span) - 1.5 * indent, bold=bold, size=size)
        return cell

    def fit(self, row: int, text: str, width: float, *, bold: bool = False, size: float = 10) -> None:
        # Excel never auto-fits merged cells, so wrapped rows get an explicit height. The
        # character estimate is deliberately conservative: a spare line is harmless, a clipped one is not.
        per_line = int(width * (0.92 if bold else 1.0) * 10 / size)
        lines = _wrapped_lines(text, per_line)
        if lines <= 1:
            return
        height = min(409.0, (12.75 * size / 10) * lines + 3)
        current = self.ws.row_dimensions[row].height or 0
        if height > current:
            self.ws.row_dimensions[row].height = height

    def text(self, row: int, col: int, value: Any, **kw: Any) -> Cell:
        kw.setdefault("wrap", True)
        return self.put(row, col, "" if value is None else value, **kw)

    def money(self, row: int, col: int, value: object, **kw: Any) -> Cell:
        kw.setdefault("color", INPUT_BLUE)
        return self.put(row, col, q2(D(value)), num_fmt=NUMBER_FORMAT, halign="right", **kw)

    def pending(self, row: int, col: int, **kw: Any) -> Cell:
        return self.put(row, col, PENDING, italic=True, color=MUTED, halign="right", **kw)

    def formula(
        self, row: int, col: int, text: str, *, link: bool = False, num_fmt: str = NUMBER_FORMAT, **kw: Any
    ) -> Cell:
        kw.setdefault("halign", "right")
        cell = self.put(row, col, None, num_fmt=num_fmt, color=LINK_GREEN if link else FORMULA_BLACK, **kw)
        cell.value = text
        return cell

    def count(self, row: int, col: int, value: int, **kw: Any) -> Cell:
        kw.setdefault("color", INPUT_BLUE)
        return self.put(row, col, value, num_fmt="#,##0", halign="right", **kw)

    def header(self, row: int, cols: Sequence[tuple[str, int]], start_col: int = 1) -> None:
        c = start_col
        for title, span in cols:
            self.put(
                row, c, title, span=span, bold=True, color=WHITE, fill=NAVY, wrap=True,
                halign="center", valign="center", border=_HEADER_BORDER,
            )
            c += span

    def header_at(self, row: int, fields: Sequence[tuple[str, int, int]]) -> None:
        """Header cells at explicit (title, column, span) positions."""
        for title, col, span in fields:
            self.header(row, [(title, span)], start_col=col)

    def header_tall(self, top: int, bottom: int, col: int, title: str) -> None:
        """A header cell merged down across a two-row header band."""
        self.header(top, [(title, 1)], start_col=col)
        for r in range(top + 1, bottom + 1):
            self.put(r, col, None, fill=NAVY, border=_HEADER_BORDER)
        self.ws.merge_cells(start_row=top, start_column=col, end_row=bottom, end_column=col)

    def section(self, row: int, title: str, *, band: Optional[str] = None, color: str = NAVY) -> None:
        self.put(row, 1, title, span=self.last_col if band else 1, bold=True, size=11, color=color, fill=band)
        if band:
            self.ws.row_dimensions[row].height = 18

    def link(self, row: int, col: int, text: str, sheet: str, *, span: int = 1, bold: bool = False) -> Cell:
        cell = self.put(row, col, text, span=span, bold=bold, color=HYPERLINK_BLUE, underline="single")
        cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"{_quoted(sheet)}!A1", display=text)
        return cell

    def treatment(self, row: int, col: int, t: Optional[Treatment], **kw: Any) -> Cell:
        if t is None:
            return self.put(row, col, "", **kw)
        fill, font = TREATMENT_STYLES[t]
        return self.put(row, col, t.value, bold=True, color=font, fill=fill, halign="center", **kw)

    def status(self, row: int, col: int, status: str, **kw: Any) -> Cell:
        if status == UNREVIEWED:
            fill, font = UNREVIEWED_STYLE
            return self.put(row, col, status, bold=True, color=font, fill=fill, halign="center", **kw)
        return self.put(row, col, status, bold=status == OVERRIDDEN, color=NAVY if status == OVERRIDDEN else
                        FORMULA_BLACK, halign="center", **kw)

    def severity(self, row: int, col: int, sev: Severity, **kw: Any) -> Cell:
        fill, font = SEVERITY_STYLES[sev]
        return self.put(row, col, sev.value, bold=True, color=font, fill=fill, halign="center", **kw)

    def signoff_input(self, row: int, col: int, *, is_date: bool = False, span: int = 1) -> Cell:
        """An empty sign-off cell for the preparer or reviewer to complete (input: blue on light yellow)."""
        return self.put(row, col, None, span=span, color=INPUT_BLUE, fill=SIGNOFF_FILL, border=_HEADER_BORDER,
                        num_fmt=DATE_FORMAT if is_date else None, halign="center")

    def check_row(self, row: int, first_col: int, last_col: int) -> None:
        """Red fill on a row of 'should be zero' cells when any is not."""
        rng = f"{_a1(first_col, row)}:{_a1(last_col, row)}"
        self.ws.conditional_formatting.add(
            rng, FormulaRule(formula=[f"ABS({_a1(first_col, row)})>=0.01"], fill=_fill(CHECK_FAIL_FILL))
        )


def _pack(sh: _Sheet, start: int, end: int, desired: Sequence[float]) -> list[tuple[int, int]]:
    """(column, span) for each field laid out left to right over columns start..end, each close to its
    desired width. The last field takes whatever remains, so the fields always fill the band."""
    out: list[tuple[int, int]] = []
    col = start
    k = len(desired)
    for i, want in enumerate(desired):
        room_end = end - (k - i - 1)  # leave a column for each remaining field
        stop = col
        acc = sh.span_width(col, 1)
        while acc < want * 0.9 and stop < room_end:
            stop += 1
            acc += sh.span_width(stop, 1)
        if i == k - 1:
            stop = max(stop, end)
        out.append((col, stop - col + 1))
        col = stop + 1
    return out


def _title_block(sh: _Sheet, ctx: _Ctx, title: str, subtitle: str = "", *, signoff_last: int = 0) -> int:
    deal = ctx.wp.deal
    sh.put(1, 1, title, bold=True, size=14, color=NAVY)
    sh.put(2, 1, f"{deal.target_name}  |  Deal {deal.deal_id}  |  Run {ctx.wp.run_id}", bold=True)
    sh.put(3, 1, _banner_text(ctx), bold=True, color=BANNER_RED)
    if subtitle:
        sh.put(4, 1, subtitle, italic=True, color=MUTED)
    _signoff_row(sh, 5, signoff_last or sh.last_col)
    return 6


def _signoff_row(sh: _Sheet, row: int, last: int) -> None:
    """Prepared by / date and Reviewed by / date for this sheet, at the right of row 5."""
    first = last - 5
    if first < 2:
        return
    for offset, label in ((0, "Prepared by"), (3, "Reviewed by")):
        sh.put(row, first + offset, label, bold=True, halign="right", size=9)
        sh.signoff_input(row, first + offset + 1)
        sh.signoff_input(row, first + offset + 2, is_date=True)


def _draft_status(ctx: _Ctx) -> str:
    total = len(ctx.wp.assessments)
    unreviewed = len(ctx.unreviewed)
    if unreviewed:
        return (f"DRAFT: {unreviewed} of {total} items UNREVIEWED; not final until every item is reviewed and "
                "the Cover sign-off is complete.")
    if total:
        return f"DRAFT until signed off: all {total} items have a reviewer decision; complete the Cover sign-off."
    return "DRAFT: no adjustments in the workpaper."


def _banner_text(ctx: _Ctx) -> str:
    draft = _draft_status(ctx)
    if ctx.wp.deal.synthetic:
        return ("SYNTHETIC: generated for QoE Evidence Review testing. Fictitious company and data; not for "
                "reliance. " + draft)
    return draft


def _units(ctx: _Ctx) -> str:
    return (
        f"{ctx.currency}. Whole dollars displayed; cell values keep cents. Amounts are EBITDA-signed: + increases "
        "EBITDA, (parentheses) reduce it. Blue = input from the workpaper; black = formula; green = link."
    )


def _units_support(ctx: _Ctx) -> str:
    return (
        f"{ctx.currency}. Whole dollars displayed. Adjustment amounts (claimed, proposed, final, flag effects) are "
        "EBITDA-signed: + increases EBITDA. GL entries are debit +, credit (-); in an adjustment a GL entry's amount "
        "is also its effect, e.g. a (credit) recovery reduces the add-back. Blue = input; black = formula; "
        "green = link."
    )


# ---------------------------------------------------------------------------
# Formatting helpers for evidence
# ---------------------------------------------------------------------------


def _gl_row(entry_id: str) -> Optional[int]:
    m = _GL_ROW.match(entry_id)
    return int(m.group(1)) if m else None


def _gl_rows_text(entry_ids: Iterable[str], limit: int = 60) -> str:
    ids = list(dict.fromkeys(entry_ids))
    if not ids:
        return ""
    rows = sorted((r, e) for e in ids if (r := _gl_row(e)) is not None)
    others = [e for e in ids if _gl_row(e) is None]
    parts = [str(r) for r, _ in rows] + others
    more = ""
    if len(parts) > limit:
        more = f" (+{len(parts) - limit} more)"
        parts = parts[:limit]
    noun = "GL row" if len(parts) == 1 and not more else "GL rows"
    return f"{noun} {', '.join(parts)}{more}"


def _flag_label(code: FlagCode) -> str:
    words = [_ACRONYMS.get(w, w) for w in code.value.lower().split("_")]
    text = " ".join(words)
    return text[0].upper() + text[1:]


def _cite(q: EvidenceQuote) -> str:
    return f"{q.doc_id}, p. {q.page}"


def _quote_text(q: EvidenceQuote) -> str:
    return f'"{q.quote}"'


def _dedupe_quotes(quotes: Iterable[EvidenceQuote]) -> list[EvidenceQuote]:
    seen: set[tuple[str, int, str]] = set()
    out: list[EvidenceQuote] = []
    for q in quotes:
        key = (q.doc_id, q.page, q.quote)
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def _key_flags(a: AdjustmentAssessment) -> str:
    seen: dict[FlagCode, Severity] = {}
    for f in sorted(a.flags, key=lambda f: _SEVERITY_RANK[f.severity]):
        seen.setdefault(f.code, f.severity)
    return "; ".join(f"{_flag_label(c)} ({s.value[0]})" for c, s in seen.items())


def _signed_status(facts: Optional[DocFacts]) -> str:
    if facts is None:
        return ""
    if facts.is_draft:
        return "DRAFT"
    if facts.is_signed is True:
        return "Signed"
    if facts.is_signed is False:
        return "Unsigned"
    return "Not stated"


def _differs_from_tool(
    treatment: Treatment, amounts: dict[str, str], tool_treatment: Treatment, tool_amounts: dict[str, str],
    tolerance: object,
) -> bool:
    """Same rule as the reviewer app: a different treatment, or amounts apart by more than the tolerance."""
    if treatment != tool_treatment:
        return True
    if treatment == Treatment.REQUEST_INFO:
        return False
    tol = D(tolerance)
    return any(abs(D(amounts.get(k)) - D(tool_amounts.get(k))) > tol for k in set(amounts) | set(tool_amounts))


def _review_pending(rv: ReviewDecision) -> bool:
    return rv.treatment == Treatment.REQUEST_INFO or not rv.amounts


def _join_sentences(*parts: str) -> str:
    """Join note fragments: a space after a finished sentence, "; " otherwise (never ".;")."""
    out = ""
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        out = p if not out else out + (" " if out[-1] in ".!?" else "; ") + p
    return out


def _first_sentence(text: str) -> str:
    parts = _SENTENCE_SPLIT.split((text or "").strip(), maxsplit=1)
    return parts[0] if parts and parts[0] else ""


def _natural_key(text: str) -> list[Any]:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", text)]


def _plain_basis(basis: str) -> str:
    """A question's basis in words management understands (no internal codes)."""
    out: list[str] = []
    for token in re.split(r"[;,/|]+", basis or ""):
        token = token.strip()
        if not token:
            continue
        label = _PLAIN_BASIS.get(token.upper())
        if label is None:
            low = token.lower()
            label = next((text for prefix, text in _PLAIN_BASIS_PREFIXES if low.startswith(prefix)), None)
        if label is None:
            words = token.replace("_", " ").strip()
            label = words[:1].upper() + words[1:].lower() if words.isupper() else words[:1].upper() + words[1:]
        if label not in out:
            out.append(label)
    return "; ".join(out)


def _management_text(text: str) -> str:
    """A tool-drafted question as management should read it: the workpaper's own conclusions (what the tool
    removed, how many subsets tie) are dropped, and internal codes are replaced by plain words."""
    parts = _SENTENCE_SPLIT.split((text or "").strip())
    kept = [p for p in parts if p and not any(rx.search(p) for rx in _INTERNAL_SENTENCES)]
    out = " ".join(kept) if kept else (text or "").strip()

    def plain(m: re.Match[str]) -> str:
        label = _PLAIN_BASIS.get(m.group(0))
        return label.lower() if label else m.group(0)

    return _ENUM_CODE.sub(plain, out)


def _provisional_from_rationale(rationale: str, labels: Sequence[str]) -> Optional[dict[str, Decimal]]:
    """The provisional amount a REQUEST_INFO rationale states (SPEC §5.5), by period; None if not stated."""
    m = re.search(r"provisional", rationale or "", re.I)
    if not m:
        return None
    tail = rationale[m.start():]
    out: dict[str, Decimal] = {}
    for label in labels:
        hit = re.search(re.escape(label) + r"\s*:?\s*(\(?-?[\d,]+(?:\.\d+)?\)?)", tail)
        if hit is None:
            return None
        try:
            out[label] = D(hit.group(1))
        except ValueError:
            return None
    return out


# ---------------------------------------------------------------------------
# Audit trail: entry roles, document vouching, flag numbering, walk
# ---------------------------------------------------------------------------


@dataclass
class _EntryView:
    link: GLLink
    entry: Optional[GLEntry]
    tick: str  # T / R / M / O / X
    claimed: bool
    removed_by: Optional[FlagCode]
    removed_flag: Optional[int]  # F-number of the flag that removed or moved it
    periods: list[str]  # analysis periods in which the listing counts the entry
    docs: list[tuple[str, str]]  # (doc_id, document tick)

    @property
    def doc_tick(self) -> str:
        ticks = [t for _, t in self.docs if t]
        return min(ticks, key=_DOC_TICK_RANK.__getitem__) if ticks else ""


def _numbered_flags(a: AdjustmentAssessment) -> list[tuple[int, Flag]]:
    """Flags in display order (most severe first), numbered F1, F2, ... on the support sheet."""
    return list(enumerate(sorted(a.flags, key=lambda f: _SEVERITY_RANK[f.severity]), start=1))


def _moves_number(f: Flag) -> bool:
    return any(D(v) != 0 for v in f.effects.values())


def _flag_for(flags: Sequence[tuple[int, Flag]], code: Optional[FlagCode], entry_id: str) -> Optional[int]:
    if code is None:
        return None
    same = [(i, f) for i, f in flags if f.code == code]
    for i, f in same:
        if entry_id in f.entry_ids:
            return i
    return same[0][0] if same else None


def _removed_code(link: GLLink) -> Optional[FlagCode]:
    for reason in link.reasons:
        m = _REMOVED_REASON.match(reason)
        if m and m.group(1) in FlagCode.__members__:
            return FlagCode(m.group(1))
    return None


def _entry_views(ctx: _Ctx, a: AdjustmentAssessment, flags: Sequence[tuple[int, Flag]]) -> list[_EntryView]:
    periods = ctx.wp.deal.periods
    recovery_ids = {e for _, f in flags if f.code == FlagCode.OFFSETTING_RECOVERY for e in f.entry_ids}
    rows: list[tuple[GLLink, str, bool, Optional[FlagCode]]] = []
    for link in a.gl_links:
        if link.role in _ROLE_TICK:
            tick, claimed, removed_by = _ROLE_TICK[link.role], link.claimed, link.removed_by
            if tick == "R" and removed_by is None:
                removed_by = _removed_code(link)
        else:  # a workpaper from before GLLink.role: rebuild the role from supports_claim and the reasons
            removed_by = _removed_code(link)
            if link.supports_claim:
                tick, claimed = "T", True
            elif removed_by is not None:
                tick, claimed = "R", True
            elif link.entry_id in recovery_ids:
                tick, claimed = "O", False
            else:
                tick, claimed = "X", False
        rows.append((link, tick, claimed, removed_by))
    # A diligence-identified item has no management claim: (b) is the entries the item itself rests on.
    traces = [lk for lk, tick, claimed, _ in rows if claimed or (_is_diligence(a) and tick in ("T", "R", "M"))]
    claimed_in = _claimed_periods(ctx, a, traces)
    out: list[_EntryView] = []
    for link, tick, claimed, removed_by in rows:
        cited = removed_by
        if tick == "M" and cited is None:
            cited = FlagCode.OUT_OF_PERIOD
        elif tick == "O" and cited is None:
            cited = FlagCode.OFFSETTING_RECOVERY
        traced = any(link is lk for lk in traces)
        in_periods = claimed_in.get(link.entry_id, []) if traced else labels_for_month(link.period, periods)
        entry = ctx.gl_by_id.get(link.entry_id)
        out.append(_EntryView(
            link=link, entry=entry, tick=tick, claimed=claimed, removed_by=removed_by,
            removed_flag=_flag_for(flags, cited, link.entry_id) if tick in ("R", "M", "O") else None,
            periods=[p for p in ctx.labels if p in in_periods],
            docs=[(d, _vouch(ctx, entry, link, d)) for d in link.doc_ids],
        ))
    out.sort(key=lambda v: (_ROLE_RANK[v.tick], not v.claimed, v.link.period, _gl_row(v.link.entry_id) or 0,
                            v.link.entry_id))
    return out


_CLAIMED_IN = re.compile(r"^Claimed in (.+)$")
_MAX_SUBSET = 28  # entries whose period membership is inferred by an exact subset (meet in the middle)


def _cents(value: object) -> int:
    return int(q2(D(value)) * 100)


def _claimed_periods(ctx: _Ctx, a: AdjustmentAssessment, links: Sequence[GLLink]) -> dict[str, list[str]]:
    """The analysis periods in whose (b) Traced amount each entry is counted.

    ``GLLink.claimed`` does not say which of two overlapping periods (a fiscal year and a TTM) an entry
    is claimed in, and management can claim a month in one and not the other. Membership comes from,
    in order: the trace's "Claimed in ..." reason; the only period with traced activity that contains
    the entry's month; otherwise the exact subset of the undecided entries that makes up the period's
    (b) Traced amount. When nothing ties, every containing period is used and the listing's check
    shows the difference."""
    active = [p for p in ctx.labels if D(a.claimed.get(p)) != 0 or D(a.traced_gl.get(p)) != 0]
    periods = ctx.wp.deal.periods
    hinted: dict[str, set[str]] = {}
    for lk in links:
        for reason in lk.reasons:
            m = _CLAIMED_IN.match(reason)
            if m:
                hinted[lk.entry_id] = {x.strip() for x in m.group(1).split(",")} & set(ctx.labels)
    out: dict[str, list[str]] = {}
    containing = {lk.entry_id: [p for p in labels_for_month(lk.period, periods) if p in active] for lk in links}
    for p in active:
        fixed, open_ = 0, []
        for lk in links:
            if p not in containing[lk.entry_id]:
                continue
            if lk.entry_id in hinted:
                if p in hinted[lk.entry_id]:
                    fixed += _cents(lk.amount)
                    out.setdefault(lk.entry_id, []).append(p)
            elif len(containing[lk.entry_id]) == 1:
                fixed += _cents(lk.amount)
                out.setdefault(lk.entry_id, []).append(p)
            else:
                open_.append(lk)
        chosen = _exact_subset([_cents(lk.amount) for lk in open_], _cents(a.traced_gl.get(p)) - fixed)
        for i, lk in enumerate(open_):
            if chosen is None or i in chosen:
                out.setdefault(lk.entry_id, []).append(p)
    return out


def _exact_subset(values: list[int], target: int) -> Optional[set[int]]:
    """Indexes of values summing exactly to target, preferring the most entries; None if none does
    (or there are too many to search)."""
    if sum(values) == target:
        return set(range(len(values)))
    if not values or len(values) > _MAX_SUBSET:
        return None
    half = len(values) // 2
    left, right = values[:half], values[half:]

    def sums(part: list[int], offset: int) -> dict[int, frozenset[int]]:
        best: dict[int, frozenset[int]] = {}
        for mask in range(1 << len(part)):
            idx = frozenset(offset + i for i in range(len(part)) if mask >> i & 1)
            total = sum(part[i - offset] for i in idx)
            if total not in best or len(idx) > len(best[total]):
                best[total] = idx
        return best

    rights = sums(right, half)
    found: Optional[frozenset[int]] = None
    for total, idx in sums(left, 0).items():
        other = rights.get(target - total)
        if other is not None and (found is None or len(idx) + len(other) > len(found)):
            found = idx | other
    return set(found) if found is not None else None


def _norm_ref(text: Optional[str]) -> str:
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _party_tokens(name: Optional[str]) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (name or "").lower()) if w not in _PARTY_STOPWORDS}


def _same_party(a: Optional[str], b: Optional[str]) -> bool:
    ta, tb = _party_tokens(a), _party_tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.6


def _month_index(month: str) -> Optional[int]:
    d = _month_date(month)
    return d.year * 12 + d.month if d else None


def _near(facts: DocFacts, month: str) -> bool:
    """The document is dated, or covers a service period, close to the entry's month."""
    m = _month_index(month)
    if m is None:
        return True
    start = _month_index((facts.service_period_start or "")[:7])
    end = _month_index((facts.service_period_end or "")[:7])
    doc = _month_index((facts.doc_date or "")[:7])
    if start is None and end is None and doc is None:
        return True
    if start is not None and end is not None and start - 1 <= m <= end + 2:
        return True
    return doc is not None and abs(doc - m) <= 2


def _vouch(ctx: _Ctx, entry: Optional[GLEntry], link: GLLink, doc_id: str) -> str:
    """How a document linked to an entry supports that entry: D / A / S / U / C, or "" when it is not
    specific to the entry (e.g. another invoice under the same matter)."""
    facts = ctx.doc_facts.get(doc_id)
    if facts is None:
        return ""
    dtype = (facts.doc_type or "").strip().lower()
    if dtype in _CORRESPONDENCE_DOC_TYPES:
        return "C"
    refs = {r for r in (_norm_ref(x) for x in facts.reference_numbers) if r}
    number = _norm_ref(entry.doc_number) if entry is not None else ""
    if number and number in refs:
        return "D"
    tol = D(ctx.wp.deal.tolerance)
    amount = abs(D(link.amount))
    stated = (_decimal(x.amount) for x in facts.amounts)
    states_amount = any(v is not None and abs(abs(v) - amount) <= tol for v in stated)
    memo = _norm_ref(entry.memo) if entry is not None else ""
    if states_amount and memo and any(len(r) >= 5 and any(ch.isdigit() for ch in r) and r in memo for r in refs):
        return "D"
    if dtype in _AGREEMENT_DOC_TYPES:
        return "U" if facts.is_draft or facts.is_signed is False else "A"
    if facts.is_draft:
        return "U"
    if not states_amount:
        return ""
    if entry is None:
        return "D"  # without the GL detail, agreeing the amount is the best available
    if number and refs:
        return "S"  # the document carries its own number, and it is not this entry's
    party_ok = not facts.counterparty or not entry.counterparty or _same_party(entry.counterparty, facts.counterparty)
    return "D" if party_ok and _near(facts, link.period) else "S"


def _decimal(value: object) -> Optional[Decimal]:
    """A document-stated amount, or None when the extractor recorded something that is not a number."""
    try:
        return D(value)
    except (ValueError, TypeError):
        return None


def _walk_baseline(a: AdjustmentAssessment, labels: Sequence[str], flags: Sequence[tuple[int, Flag]]) -> str:
    """Whether the flag effects take (a) Claimed or (b) Traced to (d); "a" when they tie from the claim."""
    effects = {p: sum((D(f.effects.get(p)) for _, f in flags), Decimal(0)) for p in labels}

    def residual(base: dict[str, str]) -> list[Decimal]:
        return [abs(D(a.proposed.get(p)) - D(base.get(p)) - effects[p]) for p in labels]

    ra, rb = residual(a.claimed), residual(a.traced_gl)
    if all(v <= _TOL for v in ra):
        return "a"
    if all(v <= _TOL for v in rb):
        return "b"
    return "a" if sum(ra) <= sum(rb) else "b"


def _amount_noted(f: Flag, records_effects: bool) -> tuple[Optional[str], str]:
    """An amount a flag states that is not an effect on (d), and what it is."""
    if f.amount_impact is None or _moves_number(f):
        return None, ""
    where = f" ({f.period_label})" if f.period_label else ""
    if f.code == FlagCode.EXCESS_GL_ACTIVITY:
        return f.amount_impact, f"Unclaimed context activity{where}; not an EBITDA effect"
    if f.code == FlagCode.PARTIAL_GL_SUPPORT:
        return f.amount_impact, f"GL shortfall against the claim{where}: linked less claimed"
    if not records_effects:
        return f.amount_impact, f"Stated by the flag{where}; this workpaper does not record per-period effects"
    return f.amount_impact, f"Stated by the flag{where}; it does not change (d) Tool proposed"


# ---------------------------------------------------------------------------
# Support sheets (SPEC §8.4)
# ---------------------------------------------------------------------------

# Columns right of the period columns, sized for the linked GL listing (the widest block):
# GL amount, date, tick, claimed?, document tick, counterparty, doc #, memo, documents, flags.
_RIGHT_WIDTHS = [13, 11, 6, 9, 6, 22, 13, 36, 24, 28]
_REASONS_WIDTH = 90  # link reasons: kept on screen, outside the print area


@dataclass
class _TieOut:
    sheet: str
    first_col: int
    claimed_row: int
    proposed_row: int
    final_row: int
    revision_row: int
    check_row: int
    check_cell: str  # the sheet's check total (absolute differences), for the Cover
    provisional_row: Optional[int] = None
    supporting: int = 0  # entries ticked T


def _write_support(ws: Worksheet, ctx: _Ctx, a: AdjustmentAssessment) -> _TieOut:
    n = len(ctx.labels)
    widths = [12, 9, 30] + [14] * n + list(_RIGHT_WIDTHS) + [_REASONS_WIDTH]
    sh = _Sheet(ws, widths)
    pc = 4  # first period column (D)
    rc = pc + n  # first column right of the periods
    last = rc + len(_RIGHT_WIDTHS) - 1  # last printed column
    reasons_col = last + 1
    name = ctx.adj_sheets[a.adj_id]
    claim = ctx.claims.get(a.adj_id)
    rv = ctx.latest.get(a.adj_id)
    status = ctx.status(a.adj_id)
    flags = _numbered_flags(a)
    views = _entry_views(ctx, a, flags)
    diligence = _is_diligence(a)
    norm = a.category == AdjustmentCategory.NORMALIZATION and not diligence
    pro_forma = a.category == AdjustmentCategory.PRO_FORMA and not diligence
    pending_tool = a.treatment == Treatment.REQUEST_INFO
    final_pending = ctx.final_pending(a)
    rolled: list[str] = []  # this sheet's checks in its check total
    has_bridge_row = f"dil:{a.adj_id}" in ctx.bridge_keys

    _title_block(sh, ctx, f"{name}: {a.title}", "Support schedule. " + _units_support(ctx), signoff_last=last)
    sh.link(5, 1, "<< EBITDA Bridge", SHEET_BRIDGE, span=2)
    sh.link(5, 3, "<< Adjustment Summary", SHEET_SUMMARY)
    row = 7

    # Conclusion strip.
    sh.section(row, "CONCLUSION")
    row += 1
    sh.put(row, 1, "Tool treatment", span=2, bold=True)
    sh.treatment(row, 3, a.treatment)
    sh.put(row, 4, f"Confidence: {a.confidence}", span=2, italic=True)
    row += 1
    sh.put(row, 1, "Final treatment", span=2, bold=True)
    sh.treatment(row, 3, ctx.final_treatment(a))
    sh.status(row, 4, status, span=2)
    row += 1
    sh.put(row, 1, "Reviewer", span=2, bold=True)
    if rv is not None:
        who = f"{rv.reviewer} at {rv.timestamp}; correction type {rv.correction_type.value}"
        if ctx.stale(rv):
            who += ". NOTE: the tool proposal has changed since this decision; re-review."
        sh.text(row, 3, who, span=last - 2)
    else:
        sh.text(
            row, 3, "No reviewer decision recorded. The tool proposal is carried and marked UNREVIEWED.",
            span=last - 2, bold=True, color=BANNER_RED,
        )
    row += 1
    check_total_row = row
    sh.put(row, 1, "Sheet checks", span=2, bold=True)
    row += 1
    sh.put(row, 1, "Tool rationale", span=2, bold=True)
    sh.text(row, 3, a.rationale or "", span=last - 2)
    row += 1
    if a.adj_id in ctx.drafted:
        sh.put(row, 1, "Open request", span=2, bold=True, color=BANNER_RED)
        sh.text(row, 3, "The item is pending but no question to management is open. A request was drafted from the "
                        f"reviewer's rationale ({ctx.drafted[a.adj_id].q_id}, Open Questions); issue it or record "
                        "one in the reviewer app.", span=last - 2, bold=True, color=BANNER_RED)
        row += 1
    row += 1

    # Management's claim (or, for a diligence-identified item, the tool's basis).
    sh.section(row, DILIGENCE_BLOCK.upper() if diligence else "MANAGEMENT'S CLAIM")
    row += 1
    for label, value in _claim_pairs(a, claim):
        sh.put(row, 1, label, span=2, bold=True)
        sh.text(row, 3, value, span=last - 2)
        row += 1
    row += 1

    # Tie-out.
    sh.section(row, "TIE-OUT BY PERIOD")
    row += 1
    sh.header(row, [(f"{ctx.currency}; + increases EBITDA", 3)] + [(p, 1) for p in ctx.labels]
              + [("Notes", last - rc + 1)])
    row += 1
    rows: dict[str, int] = {}
    final = ctx.final.get(a.adj_id, {})
    final_label = "(e) Final: reviewer decision" if rv is not None else "(e) Final: tool proposal carried (UNREVIEWED)"
    if norm:
        labels_ab = ("(a) Claimed by management: actual cost less the normalized level",
                     "(b) Actual cost in the GL (linked entries)",
                     "(c) Actual cost with document support")
    elif pro_forma:
        labels_ab = ("(a) Claimed by management: run-rate saving",
                     "(b) Cost still in the GL (run-rate saving not yet realized)",
                     "(c) Cost still in the GL with document support")
    else:
        labels_ab = ("(a) Claimed by management" + (" (not on the schedule: zero)" if diligence else ""),
                     "(b) Traced to GL (claimed entries)",
                     "(c) Documented (traced GL with document support)")

    def tie_line(key: str, label: str, values: Optional[dict[str, str]], *, bold: bool = False, note: str = "") -> None:
        nonlocal row
        rows[key] = row
        sh.put(row, 1, label, span=3, bold=bold)
        for i, p in enumerate(ctx.labels):
            if values is None:
                sh.pending(row, pc + i)
            else:
                sh.money(row, pc + i, values.get(p), bold=bold)
        if note:
            sh.text(row, rc, note, span=last - rc + 1, italic=True, color=MUTED)
        row += 1

    tie_line("a", labels_ab[0], a.claimed)
    tie_line("b", labels_ab[1], a.traced_gl)
    if norm:
        rows["level"] = row
        sh.put(row, 1, "Normalized level implied by the claim: (b) - (a)", span=3, italic=True)
        for i in range(n):
            col = pc + i
            sh.formula(row, col, f"={_a1(col, rows['b'])}-{_a1(col, rows['a'])}", italic=True)
        sh.text(row, rc, _normalized_level_source(ctx, a), span=last - rc + 1, italic=True, color=MUTED)
        row += 1
    tie_line("c", labels_ab[2], a.documented)
    tie_line("d", "(d) Tool proposed", None if pending_tool else a.proposed, bold=True,
             note="Pending: the tool proposes no amount (REQUEST_INFO); see the provisional memo below."
             if pending_tool else "")
    provisional_row: Optional[int] = None
    if pending_tool or final_pending:
        provisional_row = row
        amounts, source = _provisional(a, ctx.labels, pending_tool)
        sh.put(row, 1, "Memo: provisional amount while pending (excluded from the bridge)", span=3, italic=True)
        for i, p in enumerate(ctx.labels):
            if amounts is None:
                sh.put(row, pc + i, "Not stated", italic=True, color=MUTED, halign="right")
            else:
                sh.money(row, pc + i, amounts[p], italic=True)
        sh.text(row, rc, source, span=last - rc + 1, italic=True, color=MUTED)
        row += 1
    tie_line("e", final_label, final or None, bold=True)
    row += 1
    diffs: list[tuple[str, str, str, str]] = []
    if not norm:
        diffs.append(("(a) - (b) Claimed saving less cost still in the GL" if pro_forma
                      else "(a) - (b) Claimed less traced to GL", "a", "b", "plain"))
    diffs.append(("(b) - (c) Actual cost without document support" if norm
                  else "(b) - (c) Cost still in the GL without document support" if pro_forma
                  else "(b) - (c) Traced to GL less documented", "b", "c", "plain"))
    diffs.append(("(d) - (a) Tool proposed less claimed", "d", "a", "pending" if pending_tool else "plain"))
    diffs.append(("(e) - (a) Final less claimed (bridge revision; a pending item reverses the claim)", "e", "a",
                  "guard"))
    revision_row = row
    for label, left, right, mode in diffs:
        sh.put(row, 1, label, span=3, italic=True)
        for i in range(n):
            col = pc + i
            border = _TOP_BORDER if row == revision_row else None
            if mode == "pending":
                sh.pending(row, col, border=border)
                continue
            lhs = _a1(col, rows[left])
            # A pending final amount is text; it counts as zero, so the revision reverses the claim.
            lhs_expr = f"IF(ISNUMBER({lhs}),{lhs},0)" if mode == "guard" else lhs
            sh.formula(row, col, f"={lhs_expr}-{_a1(col, rows[right])}", border=border)
        if left == "e":
            revision_row = row
        row += 1
    check_row = row
    sh.put(row, 1, "Check: EBITDA Bridge revision less (e) - (a); should be zero", span=3, italic=True, color=MUTED)
    if has_bridge_row and n:
        rolled.append(f"SUMPRODUCT(ABS({_a1(pc, row)}:{_a1(pc + n - 1, row)}))")
        sh.check_row(row, pc, pc + n - 1)
    row += 2

    # Walk from the claim to the tool's proposal, one flag per line (formulas filled once the flags are placed).
    sh.section(row, "WALK: CLAIMED (a) TO TOOL PROPOSED (d), ONE LINE PER FLAG")
    row += 1
    effect_flags = [(i, f) for i, f in flags if _moves_number(f)]
    walk_refs: list[tuple[int, int]] = []  # (walk row, flag number)
    if pending_tool:
        sh.text(row, 1, "Pending (REQUEST_INFO): the tool proposes no amount, so there is no walk. Any flag effects "
                        "are listed in the Flags block.", span=last, italic=True, color=MUTED)
        row += 2
    else:
        sh.header(row, [(f"{ctx.currency}; + increases EBITDA", 3)] + [(p, 1) for p in ctx.labels]
                  + [("What the line is", last - rc + 1)])
        row += 1
        walk_first = row
        sh.put(row, 1, "(a) Claimed by management", span=3)
        for i in range(n):
            sh.formula(row, pc + i, f"={_a1(pc + i, rows['a'])}")
        row += 1
        baseline = _walk_baseline(a, ctx.labels, effect_flags)
        if baseline == "b" and any(D(a.claimed.get(p)) != D(a.traced_gl.get(p)) for p in ctx.labels):
            sh.put(row, 1, "(b) - (a) Claimed amount not traced to GL entries", span=3, indent=1)
            for i in range(n):
                col = pc + i
                sh.formula(row, col, f"={_a1(col, rows['b'])}-{_a1(col, rows['a'])}")
            sh.text(row, rc, "The flag effects below are measured from the traced GL amount.", span=last - rc + 1,
                    italic=True, color=MUTED)
            row += 1
        for i, f in effect_flags:
            sh.put(row, 1, f"F{i} {_flag_label(f.code)}", span=3, indent=1)
            walk_refs.append((row, i))
            sh.text(row, rc, _effect_note(f), span=last - rc + 1, italic=True, color=MUTED)
            row += 1
        tol = D(ctx.wp.deal.tolerance)
        base = a.traced_gl if baseline == "b" else a.claimed
        residual = [D(a.proposed.get(p)) - D(base.get(p)) - sum((D(f.effects.get(p)) for _, f in effect_flags),
                                                                  Decimal(0)) for p in ctx.labels]
        if any(0 < abs(x) <= tol for x in residual):
            # The engine leaves a gap within the tie-out tolerance to rounding, not to a flag.
            sh.put(row, 1, f"Difference within the tie-out tolerance ({fmt(tol)}), not attributed to a flag",
                   span=3, indent=1, italic=True, wrap=True)
            for i in range(n):
                col = pc + i
                gap = f"{_a1(col, rows['d'])}-SUM({_a1(col, walk_first)}:{_a1(col, row - 1)})"
                sh.formula(row, col, f"=IF(ABS({gap})<={fmt(tol)},{gap},0)", italic=True)
            row += 1
        walk_last = row - 1
        walk_total = row
        sh.put(row, 1, "Proposed per the walk", span=3, bold=True, border=_TOP_BORDER)
        for i in range(n):
            col = pc + i
            sh.formula(row, col, f"=SUM({_a1(col, walk_first)}:{_a1(col, walk_last)})", bold=True, border=_TOP_BORDER)
        row += 1
        sh.put(row, 1, "(d) Tool proposed", span=3)
        for i in range(n):
            sh.formula(row, pc + i, f"={_a1(pc + i, rows['d'])}")
        row += 1
        label = "Check: walk less (d) Tool proposed; should be zero"
        if not ctx.records_effects:
            label += " (memo: this workpaper does not record flag effects, so the walk is not in the checks)"
        sh.put(row, 1, label, span=3, italic=True, color=MUTED, wrap=not ctx.records_effects)
        for i in range(n):
            col = pc + i
            sh.formula(row, col, f"={_a1(col, walk_total)}-{_a1(col, row - 1)}", num_fmt=CHECK_FORMAT, italic=True)
        if ctx.records_effects and n:
            rolled.append(f"SUMPRODUCT(ABS({_a1(pc, row)}:{_a1(pc + n - 1, row)}))")
            sh.check_row(row, pc, pc + n - 1)
        row += 2

    # Flags.
    sh.section(row, f"FLAGS ({len(flags)})")
    row += 1
    flag_rows: dict[int, int] = {}
    if flags:
        amt_f, what_f, msg_f, ev_f, rel_f = _pack(sh, rc, last, [13, 18, 70, 24, 12])
        sh.header(row, [("Severity", 1), ("#", 1), ("Flag", 1)]
                  + [(f"Effect on (d)\n{p}", 1) for p in ctx.labels])
        sh.header_at(row, [("Amount noted (not an effect)", *amt_f), ("What the amount is", *what_f),
                           ("Message", *msg_f), ("Evidence", *ev_f), ("Related adj.", *rel_f)])
        row += 1
        for i, f in flags:
            flag_rows[i] = row
            sh.severity(row, 1, f.severity)
            sh.put(row, 2, f"F{i}", bold=True, halign="center")
            sh.text(row, 3, _flag_label(f.code), bold=True)
            for k, p in enumerate(ctx.labels):
                if p in f.effects:
                    sh.money(row, pc + k, f.effects[p])
            noted, what = _amount_noted(f, ctx.records_effects)
            if noted is not None:
                sh.money(row, amt_f[0], noted, span=amt_f[1], italic=True)
                sh.text(row, what_f[0], what, span=what_f[1], italic=True, color=MUTED)
            sh.text(row, msg_f[0], f.message, span=msg_f[1], indent=1)
            evidence = "; ".join(x for x in (_gl_rows_text(f.entry_ids, limit=20), "; ".join(f.doc_ids)) if x)
            sh.text(row, ev_f[0], evidence, span=ev_f[1])
            sh.text(row, rel_f[0], ", ".join(f.related_adj_ids), span=rel_f[1])
            row += 1
            row = _quote_rows(sh, row, f.quotes, last)
    else:
        sh.put(row, 1, "No flags raised.", italic=True, color=MUTED)
        row += 1
    row += 1
    for walk_row, i in walk_refs:
        for k in range(n):
            sh.formula(walk_row, pc + k, f"={_a1(pc + k, flag_rows[i])}")

    # Documented facts and judgment questions are deliberately separate blocks.
    sh.section(row, "DOCUMENTED FACTS: what the evidence establishes (GL rows and verbatim quotes cited)",
               band=FACTS_BAND)
    row += 1
    if a.facts:
        fact_f, rows_f = _pack(sh, 2, last, [150, 40])
        sh.header(row, [("#", 1)])
        sh.header_at(row, [("Fact", *fact_f), ("GL rows cited", *rows_f)])
        row += 1
        for i, fact in enumerate(a.facts, start=1):
            sh.put(row, 1, f"F{i}", bold=True, halign="center")
            sh.text(row, fact_f[0], fact.text, span=fact_f[1])
            sh.text(row, rows_f[0], _gl_rows_text(fact.entry_ids), span=rows_f[1])
            row += 1
            row = _quote_rows(sh, row, fact.quotes, last)
    else:
        sh.put(row, 1, "No documented facts recorded.", italic=True, color=MUTED)
        row += 1
    row += 1
    sh.section(row, "JUDGMENT QUESTIONS: calls for the reviewer; not established by the evidence", band=JUDGMENT_BAND)
    row += 1
    if a.judgment_questions:
        sh.header(row, [("#", 1), ("Judgment question", last - 1)])
        row += 1
        for i, jq in enumerate(a.judgment_questions, start=1):
            sh.put(row, 1, f"J{i}", bold=True, halign="center")
            sh.text(row, 2, jq, span=last - 1)
            row += 1
    else:
        sh.put(row, 1, "No open judgment questions.", italic=True, color=MUTED)
        row += 1
    row += 1

    # Questions for management.
    questions = ctx.questions.get(a.adj_id, [])
    sh.section(row, f"QUESTIONS FOR MANAGEMENT ({len(questions)})")
    row += 1
    if questions:
        q_f, pr_f, st_f, bs_f = _pack(sh, 2, last, [120, 9, 36, 26])
        sh.header(row, [("Q id", 1)])
        sh.header_at(row, [("Question", *q_f), ("Priority", *pr_f), ("Status / response", *st_f), ("Basis", *bs_f)])
        row += 1
        for q in questions:
            drafted = ctx.drafted.get(a.adj_id) is q
            sh.text(row, 1, q.q_id, bold=drafted, color=BANNER_RED if drafted else FORMULA_BLACK)
            sh.text(row, q_f[0], q.text, span=q_f[1])
            high = q.priority == "high"
            sh.text(row, pr_f[0], q.priority, span=pr_f[1], bold=high, color=BANNER_RED if high else FORMULA_BLACK)
            sh.text(row, st_f[0], q.status.value + (f": {q.response}" if q.response else "")
                    + (" (drafted by the export: not yet issued)" if drafted else ""), span=st_f[1])
            sh.text(row, bs_f[0], _plain_basis(q.basis), span=bs_f[1])
            row += 1
    else:
        sh.put(row, 1, "No questions for management.", italic=True, color=MUTED)
        row += 1
    row += 1

    # Recurrence observations: comparable activity outside the claim, beside what is claimed in the same group.
    sh.section(row, f"RECURRENCE OBSERVATIONS ({len(a.recurrence)})")
    row += 1
    if a.recurrence:
        sh.header(row, [("#", 1), ("Group / line", 2)] + [(f"{p} ({ctx.currency})", 1) for p in ctx.labels]
                  + [("Note / comparable GL rows", last - rc + 1)])
        row += 1
        for i, obs in enumerate(a.recurrence, start=1):
            sh.put(row, 1, f"R{i}", bold=True, halign="center")
            sh.text(row, 2, obs.group, span=2, bold=True)
            sh.text(row, rc, _join_sentences(obs.note, _gl_rows_text(obs.entry_ids)), span=last - rc + 1, indent=1)
            row += 1
            sh.text(row, 2, "Comparable activity outside the claim", span=2, indent=1)
            for j, p in enumerate(ctx.labels):
                sh.money(row, pc + j, obs.amounts_by_period.get(p))
            row += 1
            group = [v for v in views if v.claimed and v.link.group and v.link.group == obs.group]
            if group:
                sh.text(row, 2, "Claimed by management in the same group", span=2, indent=1)
                for j, p in enumerate(ctx.labels):
                    sh.money(row, pc + j, sum((D(v.link.amount) for v in group if p in v.periods), Decimal(0)))
                row += 1
    else:
        sh.put(row, 1, "No recurrence observed.", italic=True, color=MUTED)
        row += 1
    row += 1

    doc_numbers = {dl.doc_id: i for i, dl in enumerate(a.doc_links, start=1)}
    row = _documents_block(sh, ctx, a, row, last, reasons_col)
    row = _decision_block(sh, ctx, a, row, last)

    # Linked GL entries: last, on a new printed page, with its header repeated on every page.
    listing = _gl_table(sh, ctx, a, row, views, flags, flag_rows, rows, pending_tool, doc_numbers,
                        pc=pc, rc=rc, last=last, reasons_col=reasons_col)
    if listing.rolled:
        rolled.extend(listing.rolled)

    # The sheet's check total, near the top.
    total = "+".join(rolled) if rolled else "0"
    sh.formula(check_total_row, 3, f"={total}", num_fmt=CHECK_FORMAT, bold=True)
    cell = sh.formula(check_total_row, 4, f'=IF({_a1(3, check_total_row)}<0.01,"OK","DIFFERENCE: see the check rows")',
                      num_fmt="General", bold=True, halign="left", span=2)
    ws.conditional_formatting.add(cell.coordinate, FormulaRule(formula=[f'{cell.coordinate}<>"OK"'],
                                                              fill=_fill(CHECK_FAIL_FILL)))
    sh.text(check_total_row, 6, "Sum of absolute differences on this sheet's check rows (bridge revision"
            + (", GL listing ties" if ctx.records_roles else "") + (", flag walk" if ctx.records_effects else "")
            + "); rolls up to the Cover.", span=last - 5, italic=True, color=MUTED)

    ws.freeze_panes = "A6"
    ctx.prints[ws.title] = _PrintSpec(
        title_rows=f"{listing.header_row}:{listing.header_row}" if listing.header_row else None, last_col=last,
    )
    return _TieOut(
        sheet=name,
        first_col=pc,
        claimed_row=rows["a"],
        proposed_row=rows["d"],
        final_row=rows["e"],
        revision_row=revision_row,
        check_row=check_row,
        check_cell=f"{_quoted(name)}!$C${check_total_row}",
        provisional_row=provisional_row,
        supporting=sum(1 for v in views if v.tick == "T"),
    )


def _normalized_level_source(ctx: _Ctx, a: AdjustmentAssessment) -> str:
    agreements = []
    for dl in a.doc_links:
        facts = ctx.doc_facts.get(dl.doc_id)
        dtype = (facts.doc_type if facts else "").lower()
        if dl.relation == "agreement" or dtype in _AGREEMENT_DOC_TYPES:
            status = _signed_status(facts)
            agreements.append(f"{dl.doc_id} ({status})" if status else dl.doc_id)
    if agreements:
        return "Source of the normalized level: " + "; ".join(agreements) + ". It is supported only by a signed " \
               "agreement or a benchmark."
    return "No agreement or benchmark in the data room sets the normalized level; it is implied by the claim."


def _provisional(a: AdjustmentAssessment, labels: Sequence[str], pending_tool: bool
                 ) -> tuple[Optional[dict[str, Decimal]], str]:
    if pending_tool:
        amounts = _provisional_from_rationale(a.rationale, labels)
        if amounts is None:
            return None, "The tool rationale states no provisional amount; see the rationale above."
        return amounts, "Provisional amount stated in the tool rationale; excluded until the information is received."
    return ({p: D(a.proposed.get(p)) for p in labels},
            "Tool proposal before the reviewer put the item on hold; excluded until the information is received.")


def _effect_note(f: Flag) -> str:
    rows = _gl_rows_text(f.entry_ids, limit=12)
    head = {
        FlagCode.OFFSETTING_RECOVERY: "Deducts the recovery",
        FlagCode.OUT_OF_PERIOD: "Moves the cost to the period of the service",
        FlagCode.PERIOD_MISMATCH: "Carries only the activity in each period",
    }.get(f.code, "Removes the entries it cites")
    return f"{head}{': ' + rows if rows else ''}. See F-row in the Flags block."


def _claim_pairs(a: AdjustmentAssessment, claim: Optional[AdjustmentClaim]) -> list[tuple[str, str]]:
    """Label / value lines describing the item. Management's schedule (from the deal package or the
    workpaper) is the source when available; otherwise the assessment carries the same fields."""
    category = _CATEGORY_LABELS.get(a.category, a.category.value)
    if _is_diligence(a):
        return [
            ("Item", f"{a.adj_id}: {a.title}"),
            ("Source", "Identified by diligence from the GL and data room; not on management's schedule. The "
                       "claimed amount is zero, so the final amount is the whole diligence adjustment."),
            ("Category", category),
            ("Basis", a.description or "No basis recorded in the workpaper; see the tool rationale and flags."),
            ("GL accounts", ", ".join(a.gl_accounts) or "None recorded"),
            ("Support", "; ".join(a.support_refs) or "See the documents block below"),
        ]
    description = (claim.description if claim is not None else "") or a.description
    if not description:
        description = ("No description provided in the schedule." if claim is not None else
                       "Not carried in the workpaper; see management's adjusted EBITDA schedule.")
    pairs = [
        ("Adjustment", f"{a.adj_id}: {claim.title if claim else a.title}"),
        ("Category", f"{category}" + (f" (as labelled: {claim.category_raw})" if claim and claim.category_raw else "")),
        ("Description", description),
        ("GL accounts", ", ".join(claim.gl_accounts if claim is not None else a.gl_accounts) or "None cited"),
        ("Support refs", "; ".join(claim.support_refs if claim is not None else a.support_refs) or "None cited"),
    ]
    if claim is not None:
        pairs.append(("Schedule row", str(claim.source_row)))
    return pairs


def _quote_rows(sh: _Sheet, row: int, quotes: Iterable[EvidenceQuote], last: Optional[int] = None) -> int:
    last = last or sh.last_col
    for q in _dedupe_quotes(quotes):
        sh.put(row, 1, "V", bold=True, color=LINK_GREEN, halign="center")
        sh.text(row, 2, _cite(q), span=2, color=MUTED)
        sh.text(row, 4, _quote_text(q), span=last - 3, italic=True)
        row += 1
    return row


@dataclass
class _Listing:
    header_row: int = 0
    rolled: list[str] = field(default_factory=list)


def _gl_table(
    sh: _Sheet, ctx: _Ctx, a: AdjustmentAssessment, row: int, views: list[_EntryView],
    flags: Sequence[tuple[int, Flag]], flag_rows: dict[int, int], tie_rows: dict[str, int], pending_tool: bool,
    doc_numbers: dict[str, int], *, pc: int, rc: int, last: int, reasons_col: int,
) -> _Listing:
    n = len(ctx.labels)
    out = _Listing()
    diligence = _is_diligence(a)
    norm = a.category == AdjustmentCategory.NORMALIZATION and not diligence
    if row > 2:
        sh.ws.row_breaks.append(Break(id=row - 1))
    sh.section(row, f"LINKED GL ENTRIES ({len(views)})")
    row += 1
    if not ctx.has_gl_detail and views:
        sh.put(row, 1, "Date, account, counterparty, doc # and memo are blank: the workpaper was exported "
                       "without the source GL.", italic=True, color=MUTED)
        row += 1
    if not views:
        sh.put(row, 1, "No GL entries linked.", italic=True, color=MUTED)
        return out

    # Per-period ties to the tie-out, above the listing (formulas filled once its rows are known).
    sh.header(row, [(f"Listing by period ({ctx.currency})", 3)] + [(p, 1) for p in ctx.labels]
              + [("How it ties", last - rc + 1)])
    row += 1
    oop = [i for i, f in flags if f.code == FlagCode.OUT_OF_PERIOD and _moves_number(f)]
    roles_note = "" if ctx.records_roles else " (memo: this workpaper does not record entry roles, so it is " \
                                               "not in the checks)"
    # (d) needs the out-of-period effects as well as the roles: without them a move cannot be tied.
    has_oop = any(f.code == FlagCode.OUT_OF_PERIOD for _, f in flags)
    d_rolled = ctx.records_roles and not pending_tool and (ctx.records_effects or not has_oop)
    lines: list[tuple[str, str, str]] = [
        ("T", "Supporting: claimed and carried in (d) (T)", ""),
        ("R", "Removed by a flag (R)", "Each R row cites the removing flag."),
        ("M", "Moved by an out-of-period flag (M)", ""),
        ("O", "Recovery or offset applied in (d) (O)", ""),
        ("X", "Context only: not part of the claim (X)", "Comparable periods and excess activity; for reference."),
        ("claimed", "Entries the item rests on (T + R + M)" if diligence else "Claimed by management (Claimed? = Yes)",
         "Should equal (b). Management claims nothing for a diligence-identified item, so (b) is the entries the "
         "item itself traces." if diligence else "Should equal (b): the entries management claimed."),
        ("chk_b", f"Check: {'traced' if diligence else 'claimed'} entries less (b) Traced to GL; should be zero"
         + roles_note, ""),
    ]
    if oop:
        lines.append(("oop", "Out-of-period flag effects (net; see the Flags block)",
                      "The service-period side of a move is not a GL entry in that period."))
    # No exact subset of the linked entries ties to the claim: the tool carries no more than the claim.
    capped = not norm and any(
        (D(a.claimed.get(p)) > 0 and D(a.traced_gl.get(p)) > D(a.claimed.get(p)))
        or (D(a.claimed.get(p)) < 0 and D(a.traced_gl.get(p)) < D(a.claimed.get(p))) for p in ctx.labels)
    if capped:
        lines.append(("cap", "Cap at the claim (no exact subset of the linked entries ties to it)",
                      "Where the traced entries exceed the claim, (d) carries no more than management claimed."))
    if norm:
        lines += [
            ("listing_d", "Actual cost carried per the listing: T + M + O" + (" + out-of-period effects" if oop
                                                                              else ""), ""),
            ("level", "Normalized level deducted in (d): the line above less (d)",
             "The normalized level is not a GL entry, so this line is derived."),
            ("level_diff", "Level deducted less the level the claim implies, (b) - (a)",
             "Zero when the tool uses the level management's claim implies."),
        ]
    else:
        lines += [
            ("listing_d", "Tool proposed per the listing: T + M + O" + (" + out-of-period effects" if oop else "")
             + (" + cap" if capped else ""), ""),
            ("chk_d", "Check: listing less (d) Tool proposed; should be zero"
             + ("" if d_rolled or pending_tool else " (memo: not in the checks for this workpaper)"), ""),
        ]
    lines += [
        ("doc_D", "Claimed entries vouched to their own document (D)", ""),
        ("doc_AS", "Claimed entries with agreement or sample support only (A / S)", ""),
        ("doc_gap", "(c) Documented less the two lines above", "Documents the tool counted that are not specific to "
                                                              "the entry, or are drafts."),
    ]
    at: dict[str, int] = {}
    for key, label, note in lines:
        at[key] = row
        is_check = key.startswith("chk_")
        sh.put(row, 1, label, span=3, italic=is_check or key.startswith("doc_") or key == "X",
               bold=key == "claimed", color=MUTED if is_check else FORMULA_BLACK,
               wrap=len(label) > 60)
        if note:
            sh.text(row, rc, note, span=last - rc + 1, italic=True, color=MUTED)
        row += 1
    row += 1

    header_row = row
    out.header_row = header_row
    cols = [("Entry ID", 1), ("GL row", 1), ("Account", 1)] + [(f"{p}\n({ctx.currency}, debit +)", 1)
                                                            for p in ctx.labels]
    cols += [(f"GL amount\n({ctx.currency}, debit +)", 1), ("Date", 1), ("Tick", 1), ("Claimed by mgmt?", 1),
             ("Doc tick", 1), ("Counterparty", 1), ("Doc #", 1), ("Memo", 1), ("Documents (tick)", 1),
             ("Flags", 1), ("Link reasons (not printed)", 1)]
    sh.header(row, cols)
    row += 1
    first = row
    num = dict(flags)
    for v in views:
        link, e = v.link, v.entry
        sh.text(row, 1, link.entry_id, wrap=False)
        gl_row = _gl_row(link.entry_id) if e is None else e.source_row
        if gl_row is not None:
            sh.put(row, 2, gl_row, num_fmt="0", halign="center", color=INPUT_BLUE)
        sh.text(row, 3, f"{e.account} {e.account_name}" if e else "")
        for k, p in enumerate(ctx.labels):
            if p in v.periods:
                sh.money(row, pc + k, link.amount)
        sh.money(row, rc, link.amount)
        d = _to_date(e.date) if e else None
        if d is not None:
            sh.put(row, rc + 1, d, num_fmt=DATE_FORMAT, halign="center", color=INPUT_BLUE)
        else:
            sh.put(row, rc + 1, _month_date(link.period), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        sh.put(row, rc + 2, v.tick, bold=True, color=LINK_GREEN, halign="center")
        sh.put(row, rc + 3, "Yes" if v.claimed else "No", halign="center", bold=v.claimed)
        sh.put(row, rc + 4, v.doc_tick, bold=True, color=LINK_GREEN, halign="center")
        sh.text(row, rc + 5, e.counterparty if e else "")
        sh.text(row, rc + 6, e.doc_number if e else "")
        sh.text(row, rc + 7, e.memo if e else "")
        sh.text(row, rc + 8, "; ".join(
            f"{'Doc ' + str(doc_numbers[d_id]) if d_id in doc_numbers else d_id} {tick or 'other'}"
            for d_id, tick in v.docs))
        sh.text(row, rc + 9, _entry_flags_text(v, flags, num))
        reasons = list(link.reasons) + ([f"Group: {link.group}"] if link.group else [])
        sh.put(row, reasons_col, " | ".join(reasons), color=MUTED)
        row += 1
    last_row = row - 1

    def rng(col: int) -> str:
        L = get_column_letter(col)
        return f"${L}${first}:${L}${last_row}"

    tick, claimed, doc_tick = rng(rc + 2), rng(rc + 3), rng(rc + 4)
    for k in range(n):
        col = pc + k
        L = get_column_letter(col)
        amt = rng(col)
        for key in ("T", "R", "M", "O", "X"):
            sh.formula(at[key], col, f'=SUMIFS({amt},{tick},"{key}")', italic=key == "X")
        if diligence:
            sh.formula(at["claimed"], col, f"={L}{at['T']}+{L}{at['R']}+{L}{at['M']}", bold=True, border=_TOP_BORDER)
        else:
            sh.formula(at["claimed"], col, f'=SUMIFS({amt},{claimed},"Yes")', bold=True, border=_TOP_BORDER)
        sh.formula(at["chk_b"], col, f"={L}{at['claimed']}-{L}{tie_rows['b']}", num_fmt=CHECK_FORMAT, italic=True)
        if oop:
            sh.formula(at["oop"], col, "=" + "+".join(f"{L}{flag_rows[i]}" for i in oop))
        if capped:
            ta, tb, tt = f"{L}{tie_rows['a']}", f"{L}{tie_rows['b']}", f"{L}{at['T']}"
            sh.formula(at["cap"], col, f"=IF(AND({ta}>0,{tb}>{ta}),MIN({tt},{ta})-{tt},"
                                       f"IF(AND({ta}<0,{tb}<{ta}),MAX({tt},{ta})-{tt},0))")
        listing_d = (f"={L}{at['T']}+{L}{at['M']}+{L}{at['O']}" + (f"+{L}{at['oop']}" if oop else "")
                     + (f"+{L}{at['cap']}" if capped else ""))
        sh.formula(at["listing_d"], col, listing_d, bold=True, border=_TOP_BORDER)
        if norm:
            if pending_tool:
                sh.pending(at["level"], col)
                sh.pending(at["level_diff"], col)
            else:
                sh.formula(at["level"], col, f"={L}{at['listing_d']}-{L}{tie_rows['d']}", italic=True)
                sh.formula(at["level_diff"], col, f"={L}{at['level']}-({L}{tie_rows['b']}-{L}{tie_rows['a']})",
                           italic=True)
        elif pending_tool:
            sh.pending(at["chk_d"], col)
        else:
            sh.formula(at["chk_d"], col, f"={L}{at['listing_d']}-{L}{tie_rows['d']}", num_fmt=CHECK_FORMAT,
                       italic=True)
        sh.formula(at["doc_D"], col, f'=SUMIFS({amt},{claimed},"Yes",{doc_tick},"D")', italic=True)
        sh.formula(at["doc_AS"], col, f'=SUMIFS({amt},{claimed},"Yes",{doc_tick},"A")'
                                      f'+SUMIFS({amt},{claimed},"Yes",{doc_tick},"S")', italic=True)
        sh.formula(at["doc_gap"], col, f"={L}{tie_rows['c']}-{L}{at['doc_D']}-{L}{at['doc_AS']}", italic=True)
    if n and ctx.records_roles:
        out.rolled.append(f"SUMPRODUCT(ABS({_a1(pc, at['chk_b'])}:{_a1(pc + n - 1, at['chk_b'])}))")
        sh.check_row(at["chk_b"], pc, pc + n - 1)
    if n and d_rolled and not norm:
        out.rolled.append(f"SUMPRODUCT(ABS({_a1(pc, at['chk_d'])}:{_a1(pc + n - 1, at['chk_d'])}))")
        sh.check_row(at["chk_d"], pc, pc + n - 1)
    sh.ws.auto_filter.ref = f"A{header_row}:{get_column_letter(reasons_col)}{last_row}"
    return out


def _entry_flags_text(v: _EntryView, flags: Sequence[tuple[int, Flag]], num: dict[int, Flag]) -> str:
    parts: list[str] = []
    verb = {"R": "Removed by", "M": "Moved by", "O": "Offset under"}.get(v.tick)
    if verb:
        if v.removed_flag is not None:
            parts.append(f"{verb} F{v.removed_flag} {_flag_label(num[v.removed_flag].code)}")
        elif v.removed_by is not None:
            parts.append(f"{verb} {_flag_label(v.removed_by)}")
    cited = [f"F{i}" for i, f in flags if v.link.entry_id in f.entry_ids and i != v.removed_flag]
    if cited:
        parts.append(("Also cited by " if parts else "Cited by ") + ", ".join(cited))
    return "; ".join(parts)


def _documents_block(sh: _Sheet, ctx: _Ctx, a: AdjustmentAssessment, row: int, last: int, reasons_col: int) -> int:
    sh.section(row, f"DOCUMENTS AND VERBATIM QUOTES ({len(a.doc_links)})")
    row += 1
    if not a.doc_links:
        sh.put(row, 1, "No documents linked.", italic=True, color=MUTED)
        return row + 2
    fields = _pack(sh, 2, last, [40, 12, 11, 9, 13, 22, 22, 36, 16, 24])
    titles = ["Document", "Type", "Doc date", "Signed?", "Relation", "Counterparty", "Reference #s", "Key terms",
              "Service period", "Linked GL rows"]
    sh.header(row, [("#", 1)])
    sh.header_at(row, [(t, c, s) for t, (c, s) in zip(titles, fields, strict=True)])
    sh.header(row, [("Link reasons (not printed)", 1)], start_col=reasons_col)
    row += 1
    for i, link in enumerate(a.doc_links, start=1):
        facts = ctx.doc_facts.get(link.doc_id)
        (doc_c, doc_s), (type_c, type_s), (date_c, date_s), (sig_c, sig_s), (rel_c, rel_s), (cp_c, cp_s), \
            (ref_c, ref_s), (terms_c, terms_s), (svc_c, svc_s), (gl_c, gl_s) = fields
        sh.put(row, 1, f"Doc {i}", bold=True, halign="center")
        sh.text(row, doc_c, link.doc_id, span=doc_s)
        sh.text(row, type_c, facts.doc_type.replace("_", " ") if facts else "", span=type_s)
        d = _to_date(facts.doc_date) if facts else None
        if d is not None:
            sh.put(row, date_c, d, span=date_s, num_fmt=DATE_FORMAT, halign="center", color=INPUT_BLUE)
        signed = _signed_status(facts)
        sh.text(row, sig_c, signed, span=sig_s, bold=signed in ("DRAFT", "Unsigned"),
                color=BANNER_RED if signed in ("DRAFT", "Unsigned") else FORMULA_BLACK)
        sh.text(row, rel_c, link.relation.replace("_", " "), span=rel_s)
        sh.text(row, cp_c, (facts.counterparty or "") if facts else "", span=cp_s)
        sh.text(row, ref_c, ", ".join(facts.reference_numbers) if facts else "", span=ref_s)
        sh.text(row, terms_c, "; ".join(f"{t.kind}: {t.text}" for t in facts.terms) if facts else "", span=terms_s)
        span = ""
        if facts and (facts.service_period_start or facts.service_period_end):
            span = f"{facts.service_period_start or '?'} to {facts.service_period_end or '?'}"
        sh.text(row, svc_c, span, span=svc_s)
        sh.text(row, gl_c, _gl_rows_text(link.entry_ids, limit=30), span=gl_s)
        sh.put(row, reasons_col, "; ".join(link.reasons), color=MUTED)
        row += 1
    quotes: list[EvidenceQuote] = []
    for link in a.doc_links:
        quotes.extend(link.quotes)
        facts = ctx.doc_facts.get(link.doc_id)
        if facts is not None:
            quotes.extend(t.quote for t in facts.terms)
    quotes = _dedupe_quotes(quotes)
    row += 1
    sh.put(row, 1, "Verbatim quotes (exact text of the cited page)", bold=True)
    row += 1
    if quotes:
        sh.header(row, [("Tick", 1), ("Document, page", 2), ("Quote", last - 3)])
        row += 1
        row = _quote_rows(sh, row, quotes, last)
    else:
        sh.put(row, 1, "No quotes recorded for the linked documents.", italic=True, color=MUTED)
        row += 1
    return row + 1


def _decision_block(sh: _Sheet, ctx: _Ctx, a: AdjustmentAssessment, row: int, last: int) -> int:
    pc = 4
    sh.section(row, "REVIEWER DECISION")
    row += 1
    rv = ctx.latest.get(a.adj_id)
    if rv is None:
        sh.status(row, 1, UNREVIEWED, span=2)
        sh.text(row, 3, "No reviewer decision recorded; the tool proposal is carried in the bridge.", span=last - 2,
                bold=True)
        return row + 2
    sh.header(row, [("", 3)] + [(p, 1) for p in ctx.labels])
    row += 1
    sh.put(row, 1, "Reviewer treatment and amounts", span=3, bold=True)
    for i, p in enumerate(ctx.labels):
        if _review_pending(rv):
            sh.pending(row, pc + i)
        else:
            sh.money(row, pc + i, rv.amounts.get(p), bold=True)
    row += 1
    sh.put(row, 1, "Tool proposal at time of review", span=3, italic=True)
    for i, p in enumerate(ctx.labels):
        if rv.tool_amounts:
            sh.money(row, pc + i, rv.tool_amounts.get(p), italic=True)
        else:
            sh.pending(row, pc + i)
    row += 1
    for label, value in (
        ("Treatment", None),
        ("Reviewer", f"{rv.reviewer} at {rv.timestamp}"),
        ("Correction type", rv.correction_type.value
         + (" (tool error: becomes a regression case)" if rv.correction_type in TOOL_ERROR_CORRECTIONS else "")),
        ("Rationale", rv.rationale),
    ):
        sh.put(row, 1, label, span=2, bold=True)
        if value is None:
            sh.treatment(row, 3, rv.treatment)
            sh.text(row, 4, f"Tool treatment at review: {rv.tool_treatment.value}", span=3, italic=True)
        else:
            sh.text(row, 3, value, span=last - 2)
        row += 1
    history = [r for r in ctx.wp.reviews if r.adj_id == a.adj_id]
    if len(history) > 1:
        row += 1
        sh.put(row, 1, "Decision history (review log order; latest wins)", bold=True)
        row += 1
        ts_f, who_f, tr_f, cur_f, ct_f, rat_f = _pack(sh, 2, last, [20, 14, 14, 11, 22, 80])
        sh.header(row, [("#", 1)])
        sh.header_at(row, [("Timestamp", *ts_f), ("Reviewer", *who_f), ("Treatment", *tr_f), ("Current?", *cur_f),
                           ("Correction type", *ct_f), ("Rationale", *rat_f)])
        row += 1
        for i, h in enumerate(history, start=1):
            sh.put(row, 1, i, halign="center")
            sh.text(row, ts_f[0], h.timestamp, span=ts_f[1])
            sh.text(row, who_f[0], h.reviewer, span=who_f[1])
            sh.treatment(row, tr_f[0], h.treatment, span=tr_f[1])
            sh.text(row, cur_f[0], "Current" if h is rv else "Superseded", italic=h is not rv, span=cur_f[1])
            sh.text(row, ct_f[0], h.correction_type.value, span=ct_f[1])
            sh.text(row, rat_f[0], h.rationale, span=rat_f[1])
            row += 1
    return row + 1


# ---------------------------------------------------------------------------
# Adjustment Summary
# ---------------------------------------------------------------------------


@dataclass
class _SummaryRefs:
    first_row: int  # management items (the Cover's status counts read these ranges)
    last_row: int
    total_row: int  # grand total: management + diligence-identified items
    claimed_col: int
    proposed_col: int
    final_col: int
    diff_col: int
    tool_col: int
    reviewer_col: int
    status_col: int
    rows: dict[str, int] = field(default_factory=dict)
    mgmt_total_row: int = 0  # management items only (== total_row when there are no diligence items)
    dil_first_row: Optional[int] = None
    dil_last_row: Optional[int] = None
    dil_total_row: Optional[int] = None
    recon_rows: dict[str, int] = field(default_factory=dict)  # reconciliation to the bridge (filled later)
    qs_col: int = 0


def _write_summary(ws: Worksheet, ctx: _Ctx, tie: dict[str, _TieOut]) -> _SummaryRefs:
    n = len(ctx.labels)
    claimed_col = 4
    proposed_col = claimed_col + n
    final_col = proposed_col + n
    diff_col = final_col + n
    prov_col = diff_col + n
    tool_col = prov_col + n
    reviewer_col, status_col, corr_col, conf_col, flags_col = (tool_col + i for i in range(1, 6))
    links_col, supp_col, docs_col, qs_col = (flags_col + i for i in range(1, 5))
    widths = [9, 42, 20] + [13] * (5 * n) + [15, 15, 14, 24, 11, 52, 9, 11, 8, 11]
    sh = _Sheet(ws, widths)
    _title_block(sh, ctx, "Adjustment Summary", _units(ctx))
    cur = ctx.currency
    g, h = 6, 7
    # Two header rows: group band over the period columns, then period labels.
    for col, title in ((1, "Ref"), (2, "Title"), (3, "Category")):
        sh.header_tall(g, h, col, title)
    for col, title in (
        (claimed_col, f"Claimed by management ({cur})"),
        (proposed_col, f"Tool proposed ({cur})"),
        (final_col, f"Final: diligence ({cur})"),
        (diff_col, f"Final less claimed ({cur})"),
        (prov_col, f"Memo: provisional, pending items ({cur}; excluded)"),
    ):
        sh.header(g, [(title, n)], start_col=col)
        sh.header(h, [(p, 1) for p in ctx.labels], start_col=col)
    for col, title in (
        (tool_col, "Tool treatment"), (reviewer_col, "Reviewer treatment"), (status_col, "Status"),
        (corr_col, "Correction type"), (conf_col, "Tool confidence"), (flags_col, "Key flags (C/W/I = severity)"),
        (links_col, "# GL links"), (supp_col, "# supporting GL links (T)"), (docs_col, "# docs"),
        (qs_col, "# open questions"),
    ):
        sh.header_tall(g, h, col, title)
    ws.row_dimensions[g].height = 30
    refs_rows: dict[str, int] = {}

    def item_row(row: int, a: AdjustmentAssessment) -> None:
        t = tie[a.adj_id]
        rv = ctx.latest.get(a.adj_id)
        pending = ctx.final_pending(a)
        refs_rows[a.adj_id] = row
        sh.link(row, 1, a.adj_id, t.sheet)
        sh.text(row, 2, a.title)
        sh.text(row, 3, _CATEGORY_LABELS.get(a.category, a.category.value))
        for i in range(n):
            sc = t.first_col + i
            sh.formula(row, claimed_col + i, "=" + _xref(t.sheet, sc, t.claimed_row), link=True)
            sh.formula(row, proposed_col + i, "=" + _xref(t.sheet, sc, t.proposed_row), link=True)
            sh.formula(row, final_col + i, "=" + _xref(t.sheet, sc, t.final_row), link=True, bold=True)
            fin = _a1(final_col + i, row)
            sh.formula(row, diff_col + i, f"=IF(ISNUMBER({fin}),{fin},0)-{_a1(claimed_col + i, row)}")
            if pending and t.provisional_row is not None:
                sh.formula(row, prov_col + i, "=" + _xref(t.sheet, sc, t.provisional_row), link=True, italic=True)
        sh.treatment(row, tool_col, a.treatment)
        sh.treatment(row, reviewer_col, rv.treatment if rv else None)
        sh.status(row, status_col, ctx.status(a.adj_id))
        sh.text(row, corr_col, rv.correction_type.value if rv else "", halign="center")
        sh.text(row, conf_col, a.confidence, halign="center")
        sh.text(row, flags_col, _key_flags(a))
        sh.count(row, links_col, len(a.gl_links))
        if pending:
            sh.put(row, supp_col, "n/a", italic=True, color=MUTED, halign="right")
        else:
            sh.count(row, supp_col, t.supporting)
        sh.count(row, docs_col, len(a.doc_links))
        drafted = a.adj_id in ctx.drafted
        sh.count(row, qs_col, sum(1 for q in ctx.questions.get(a.adj_id, []) if q.status == QuestionStatus.OPEN),
                 bold=drafted, fill=CHECK_FAIL_FILL if drafted else None)

    amount_cols = list(range(claimed_col, tool_col))

    def total_line(row: int, label: str, formula: Any, border: Border) -> None:
        sh.put(row, 2, label, bold=True, border=border)
        sh.put(row, 1, None, border=border)
        sh.put(row, 3, None, border=border)
        for col in amount_cols:
            sh.formula(row, col, formula(get_column_letter(col)), bold=True, border=border)
        # Questions are per item, so they add; GL links and documents are shared between items, so a
        # total would count them twice and is left blank.
        sh.formula(row, qs_col, formula(get_column_letter(qs_col)), bold=True, border=border, num_fmt="#,##0")
        for col in (links_col, supp_col, docs_col):
            sh.put(row, col, None, border=border)

    row = h + 1
    first = row
    mgmt, dil = ctx.mgmt_items, ctx.dil_items
    for a in mgmt:
        item_row(row, a)
        row += 1
    last_row = max(first, row - 1)
    dil_first = dil_last = dil_total = None
    if not dil:
        total_row = row if mgmt else first
        total_line(total_row, "Total", lambda L: f"=SUM({L}{first}:{L}{last_row})", _FINAL_BORDER)
        mgmt_total = total_row
    else:
        # Management items, their subtotal, then the diligence-identified block and its subtotal.
        mgmt_total = row if mgmt else first
        total_line(mgmt_total, "Total management adjustments", lambda L: f"=SUM({L}{first}:{L}{last_row})",
                   _TOP_BORDER)
        row = mgmt_total + 2
        sh.put(row, 1, DILIGENCE_BLOCK + ": management claimed nothing, so the final amount is the adjustment",
               span=qs_col, bold=True, color=NAVY, fill=SECTION_FILL)
        row += 1
        dil_first = row
        for a in dil:
            item_row(row, a)
            row += 1
        dil_last = row - 1
        dil_total = row
        total_line(dil_total, "Total diligence-identified items",
                   lambda L: f"=SUM({L}{dil_first}:{L}{dil_last})", _TOP_BORDER)
        total_row = dil_total + 2
        total_line(total_row, "Total", lambda L: f"={L}{mgmt_total}+{L}{dil_total}", _FINAL_BORDER)

    # Reconciliation of the difference total to the bridge's total diligence adjustments (formulas are
    # filled once the bridge is written).
    row = total_row + 2
    recon_rows: dict[str, int] = {}
    if ctx.wp.assessments and "dil_total" in ctx.bridge_keys:
        sh.put(row, 2, "Reconciliation to the EBITDA Bridge (final less claimed)", bold=True, color=NAVY)
        row += 1
        for key, label in (
            ("items", "Final less claimed, all items (Total row above)"),
            ("recon", "Reverse unsupported reporting difference (EBITDA Bridge; not an adjustment item)"),
            ("bridge", "Total diligence adjustments per the EBITDA Bridge"),
            ("check", "Check: the two lines above less the bridge total; should be zero"),
        ):
            recon_rows[key] = row
            sh.put(row, 2, label, italic=key == "check", color=MUTED if key == "check" else FORMULA_BLACK,
                   bold=key == "bridge")
            row += 1
        row += 1
    note = row
    sh.put(note, 2, "Pending (REQUEST_INFO) items show \"Pending\": they are excluded from Final totals, and the "
                    "bridge reverses their claimed amounts. The memo columns show the provisional amount the "
                    "evidence would support once the information arrives.", italic=True, color=MUTED)
    sh.put(note + 1, 2, "Final = latest reviewer decision; an UNREVIEWED item carries the tool proposal until a "
                        "reviewer signs off.", italic=True, color=MUTED)
    sh.put(note + 2, 2, "# GL links and # docs are per item and are not totalled: an entry or document can support "
                        "more than one item.", italic=True, color=MUTED)
    if ctx.drafted:
        sh.put(note + 3, 2, "Red # open questions: the item is pending but had no open question to management; a "
                            "request was drafted from the reviewer's rationale (Open Questions).", italic=True,
               color=BANNER_RED)
    ws.freeze_panes = _a1(4, h + 1)
    if mgmt:
        ws.auto_filter.ref = f"A{h}:{get_column_letter(qs_col)}{last_row}"
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{g}:{h}", title_cols=3)
    return _SummaryRefs(
        first_row=first, last_row=last_row, total_row=total_row, claimed_col=claimed_col,
        proposed_col=proposed_col, final_col=final_col, diff_col=diff_col, tool_col=tool_col,
        reviewer_col=reviewer_col, status_col=status_col, rows=refs_rows, mgmt_total_row=mgmt_total,
        dil_first_row=dil_first, dil_last_row=dil_last, dil_total_row=dil_total, recon_rows=recon_rows,
        qs_col=qs_col,
    )


def _finish_summary(ws: Worksheet, ctx: _Ctx, srefs: _SummaryRefs, brefs: _BridgeRefs) -> None:
    """Fill the Summary's reconciliation to the bridge (needs the bridge's rows)."""
    rr = srefs.recon_rows
    if not rr or "dil_total" not in brefs.rows:
        return
    sh = _Sheet(ws, [])
    n = len(ctx.labels)
    for k in range(n):
        col = srefs.diff_col + k
        L = get_column_letter(col)
        bcol = brefs.first_col + k
        sh.formula(rr["items"], col, f"={L}{srefs.total_row}")
        if "dil_recon" in brefs.rows:
            sh.formula(rr["recon"], col, "=" + _xref(SHEET_BRIDGE, bcol, brefs.rows["dil_recon"]), link=True)
        else:
            sh.put(rr["recon"], col, 0, num_fmt=NUMBER_FORMAT, color=INPUT_BLUE, halign="right")
        sh.formula(rr["bridge"], col, "=" + _xref(SHEET_BRIDGE, bcol, brefs.rows["dil_total"]), link=True, bold=True)
        sh.formula(rr["check"], col, f"={L}{rr['items']}+{L}{rr['recon']}-{L}{rr['bridge']}", num_fmt=CHECK_FORMAT,
                   italic=True)
    if n:
        sh.check_row(rr["check"], srefs.diff_col, srefs.diff_col + n - 1)
        ctx.add_check(AREA_SUMMARY, _abs_range(SHEET_SUMMARY, srefs.diff_col, srefs.diff_col + n - 1, rr["check"]))


# ---------------------------------------------------------------------------
# EBITDA Bridge (SPEC §5.6)
# ---------------------------------------------------------------------------


def _is_total(r: BridgeRow) -> bool:
    return r.key.endswith("_total") or r.label.strip().lower().startswith("total")


def _plan_subtotals(rows: Sequence[BridgeRow], labels: Sequence[str]) -> dict[int, tuple[list[tuple[int, int]], bool]]:
    """For each subtotal row index: the (row index, sign) terms of its formula, and whether they foot.

    A "total" subtotal sums the adjustment rows since the previous subtotal. An
    EBITDA-level subtotal starts from the previous level and adds the
    intervening total (or rows). Memo rows between levels (the difference to
    management's reported EBITDA) are reconciling items: their sign is chosen
    so the formula reproduces the tool's figure, and an inconsistent bridge is
    reported rather than papered over.
    """
    plans: dict[int, tuple[list[tuple[int, int]], bool]] = {}
    prev_sub: Optional[int] = None
    prev_level: Optional[int] = None
    block: list[int] = []
    for i, r in enumerate(rows):
        if r.kind != "subtotal":
            block.append(i)
            continue
        plain = [(j, 1) for j in block if rows[j].kind != "memo"]
        memo = [j for j in block if rows[j].kind == "memo"]
        candidates: list[list[tuple[int, int]]] = []
        if _is_total(r):
            candidates.append(plain)
        else:
            base: list[tuple[int, int]] = []
            if prev_level is not None:
                base.append((prev_level, 1))
            if prev_sub is not None and prev_sub != prev_level:
                base.append((prev_sub, 1))
            for sign in (1, -1):
                candidates.append(base + plain + [(j, sign) for j in memo])
            if memo:
                candidates.append(base + plain)
        chosen, ok = candidates[0], False
        for terms in candidates:
            if all(
                abs(sum((D(rows[j].amounts.get(p)) * s for j, s in terms), Decimal(0)) - D(r.amounts.get(p)))
                <= Decimal("0.01")
                for p in labels
            ):
                chosen, ok = terms, True
                break
        plans[i] = (chosen, ok)
        prev_sub = i
        if not _is_total(r):
            prev_level = i
        block = []
    return plans


def _terms_formula(terms: list[tuple[int, int]], sheet_rows: dict[int, int], col: int) -> str:
    if not terms:
        return "=0"
    rows = sorted(sheet_rows[j] for j, _ in terms)
    signs = {s for _, s in terms}
    L = get_column_letter(col)
    # A run of added rows reads best as SUM(), but only when no other bridge row
    # (e.g. a memo line) sits inside the range; section and blank rows are harmless.
    others = set(sheet_rows.values()) - set(rows)
    if len(terms) > 2 and signs == {1} and not any(rows[0] < r < rows[-1] for r in others):
        return f"=SUM({L}{rows[0]}:{L}{rows[-1]})"
    parts = []
    for j, s in terms:
        ref = f"{L}{sheet_rows[j]}"
        parts.append(("+" if s > 0 else "-") + ref)
    expr = "".join(parts)
    return "=" + (expr[1:] if expr.startswith("+") else expr)


@dataclass
class _BridgeRefs:
    rows: dict[str, int]
    first_col: int
    footed: bool


@dataclass
class _ReconRefs:
    ni_rows: dict[str, int] = field(default_factory=dict)  # period label -> row of the period summary
    ni_col: int = 0


def _line_by_line(pairs: list[tuple[str, str]]) -> Optional[str]:
    """=ABS(a1-b1)+ABS(a2-b2)+... ; None when empty or too long for one formula."""
    if not pairs:
        return None
    text = "=" + "+".join(f"ABS({x}-{y})" for x, y in pairs)
    return text if len(text) < _MAX_FORMULA else None


def _write_bridge(ws: Worksheet, ctx: _Ctx, srefs: _SummaryRefs, tie: dict[str, _TieOut],
                  rrefs: _ReconRefs) -> _BridgeRefs:
    n = len(ctx.labels)
    pc = 3
    treat_col, status_col, link_col = pc + n, pc + n + 1, pc + n + 2
    sh = _Sheet(ws, [10, 62] + [15] * n + [16, 14, 13])
    ws.sheet_view.showGridLines = False
    _title_block(sh, ctx, "EBITDA Bridge: reported to diligence adjusted", _units(ctx))
    row = 6
    sh.header(row, [("Ref", 1), ("Line item", 1)] + [(f"{p}\n{ctx.currency}", 1) for p in ctx.labels]
              + [("Final treatment", 1), ("Status", 1), ("Support", 1)])
    ws.row_dimensions[row].height = 28
    header_row = row
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{header_row}:{header_row}")
    row += 1
    item_ids = {a.adj_id for a in ctx.dil_items}
    rows = bridge_display_rows(ctx.wp.bridge.rows, item_ids)
    if not rows:
        sh.put(row, 2, "No bridge rows in the workpaper.", italic=True, color=MUTED)
        return _BridgeRefs(rows={}, first_col=pc, footed=True)

    plans = _plan_subtotals(rows, ctx.labels)
    sheet_rows: dict[int, int] = {}
    by_id = {a.adj_id: a for a in ctx.wp.assessments}
    seen_kinds: set[str] = set()
    sections = {
        "component": "Reported EBITDA",
        "mgmt_adjustment": "Management adjustments (as claimed)",
        "diligence_adjustment": "Diligence adjustments (final less claimed; claimed reversed when pending)",
    }
    prev: Optional[BridgeRow] = None
    item_block = False
    for i, r in enumerate(rows):
        if prev is not None and prev.kind == "subtotal" and not _is_total(prev) and r.kind != "subtotal":
            row += 1
        if r.kind in sections and r.kind not in seen_kinds:
            sh.put(row, 1, sections[r.kind], span=link_col, bold=True, color=NAVY, fill=SECTION_FILL)
            row += 1
        seen_kinds.add(r.kind)
        if is_item_row(r, item_ids) and not item_block:
            # A text-only row inside the diligence block; SUM ranges over it are unaffected.
            sh.put(row, 1, DILIGENCE_BLOCK + ": the final amount (management claimed nothing)", span=link_col,
                   bold=True, italic=True, color=NAVY)
            row += 1
            item_block = True
        sheet_rows[i] = row
        is_sub = r.kind == "subtotal"
        level = is_sub and not _is_total(r)
        final_line = r.key == "diligence_adjusted_ebitda"
        memo = r.kind == "memo"
        border = _FINAL_BORDER if final_line else (_TOP_BORDER if is_sub else None)
        fill = FINAL_FILL if final_line else (SUBTOTAL_FILL if level else None)
        sh.put(row, 1, r.adj_id or "", fill=fill, border=border, bold=is_sub)
        sh.text(row, 2, r.label, bold=is_sub, italic=memo, fill=fill, border=border,
                color=MUTED if memo else FORMULA_BLACK,
                indent=0 if (is_sub or r.kind == "component" or memo) else 1)
        for k, p in enumerate(ctx.labels):
            col = pc + k
            if is_sub:
                terms, ok = plans[i]
                cell = sh.formula(row, col, _terms_formula(terms, sheet_rows, col), bold=True, fill=fill, border=border)
                if not ok:
                    cell.font = Font(name=FONT_NAME, size=10, bold=True, color=BANNER_RED)
            else:
                sh.money(row, col, r.amounts.get(p), italic=memo, fill=fill, border=border)
        for col in (treat_col, status_col, link_col):
            sh.put(row, col, None, fill=fill, border=border)
        a = by_id.get(bridge_row_adj_id(r) or "")
        if a is not None and r.kind == "diligence_adjustment":
            sh.treatment(row, treat_col, ctx.final_treatment(a), border=border)
            sh.status(row, status_col, ctx.status(a.adj_id), border=border)
        if a is not None and r.kind in ("mgmt_adjustment", "diligence_adjustment"):
            sh.link(row, link_col, ctx.adj_sheets[a.adj_id], ctx.adj_sheets[a.adj_id]).alignment = _CENTER
        elif r.key in ("dil_recon", "mgmt_recon_diff"):
            sh.link(row, link_col, "Data Quality", SHEET_DATA_QUALITY).alignment = _CENTER
        if final_line and ctx.unreviewed:
            fill_u, font_u = UNREVIEWED_STYLE
            sh.put(row, status_col, "DRAFT", bold=True, color=font_u, fill=fill_u, halign="center", border=border)
            sh.put(row, treat_col, f"{len(ctx.unreviewed)} unreviewed", italic=True, halign="center", border=border,
                   fill=fill)
        row += 1
        prev = r

    key_rows = {rows[i].key: sheet_rows[i] for i in sheet_rows}
    footed = all(ok for _, ok in plans.values())

    # Controls: the bridge must tie to the Adjustment Summary, line by line and in total.
    row += 1
    sh.put(row, 1, "Checks (should be zero)", span=link_col, bold=True, color=NAVY, fill=SECTION_FILL)
    row += 1
    checks: list[tuple[str, Any]] = []
    if ctx.wp.assessments and {"diligence_adjusted_ebitda", "gl_ebitda"} <= key_rows.keys():
        checks.append((
            "Diligence adjusted EBITDA less (GL EBITDA + total final amounts, Adjustment Summary)",
            lambda col, k: (f"={_a1(col, key_rows['diligence_adjusted_ebitda'])}-{_a1(col, key_rows['gl_ebitda'])}"
                            f"-{_xref(SHEET_SUMMARY, srefs.final_col + k, srefs.total_row)}"),
        ))
    if ctx.mgmt_items and "mgmt_total" in key_rows:
        checks.append((
            "Total management adjustments less total claimed, Adjustment Summary",
            lambda col, k: (f"={_a1(col, key_rows['mgmt_total'])}"
                            f"-{_xref(SHEET_SUMMARY, srefs.claimed_col + k, srefs.mgmt_total_row)}"),
        ))
    item_rows = [key_rows[f"dil:{a.adj_id}"] for a in ctx.dil_items if f"dil:{a.adj_id}" in key_rows]
    if srefs.dil_total_row is not None and len(item_rows) == len(ctx.dil_items):
        checks.append((
            "Diligence-identified items less their total final amounts, Adjustment Summary",
            lambda col, k: ("=" + "+".join(_a1(col, r) for r in item_rows)
                            + f"-{_xref(SHEET_SUMMARY, srefs.final_col + k, srefs.dil_total_row)}"),
        ))
    # Line by line: two transposed lines would pass the totals above.
    mgmt_pairs = [(f"mgmt:{a.adj_id}", srefs.rows[a.adj_id]) for a in ctx.mgmt_items
                  if f"mgmt:{a.adj_id}" in key_rows and a.adj_id in srefs.rows]
    if mgmt_pairs:
        checks.append((
            "Each management line less its claimed amount, Adjustment Summary (sum of absolute differences)",
            lambda col, k: _line_by_line([(_a1(col, key_rows[key]), _xref(SHEET_SUMMARY, srefs.claimed_col + k, r))
                                          for key, r in mgmt_pairs]),
        ))
    dil_pairs = [(f"dil:{a.adj_id}", srefs.rows[a.adj_id]) for a in ctx.wp.assessments
                 if f"dil:{a.adj_id}" in key_rows and a.adj_id in srefs.rows]
    if dil_pairs:
        checks.append((
            "Each diligence line less its final less claimed, Adjustment Summary (sum of absolute differences)",
            lambda col, k: _line_by_line([(_a1(col, key_rows[key]), _xref(SHEET_SUMMARY, srefs.diff_col + k, r))
                                          for key, r in dil_pairs]),
        ))
    for label, build in checks:
        formulas = [build(pc + k, k) for k in range(n)]
        if any(f is None for f in formulas):
            continue
        sh.text(row, 2, label, italic=True, color=MUTED)
        for k in range(n):
            sh.formula(row, pc + k, formulas[k], num_fmt=CHECK_FORMAT, italic=True)
        if n:
            sh.check_row(row, pc, pc + n - 1)
            ctx.add_check(AREA_BRIDGE, _abs_range(SHEET_BRIDGE, pc, pc + n - 1, row))
        row += 1
    if not footed:
        sh.put(row, 2, "WARNING: a subtotal in red does not foot from the rows above to the tool's bridge; "
                       "investigate before relying on it.", bold=True, color=BANNER_RED)
        row += 1
    row += 1

    # Agreement to source data: management's own figures entered as inputs, and net income per the
    # reconciliation, so an edited component cannot move "per management" silently.
    row = _bridge_source_agreement(sh, ctx, row, key_rows, pc, link_col, rrefs)
    row += 1
    sh.put(row, 2, "Subtotals are formulas over the rows above; adjustment rows are values from the workpaper. "
                   "Diligence adjusted EBITDA = GL EBITDA + final amounts (pending items excluded).",
           italic=True, color=MUTED)

    # Each support sheet ties its (e) - (a) revision to the bridge.
    for a in ctx.wp.assessments:
        t = tie[a.adj_id]
        dil_row = key_rows.get(f"dil:{a.adj_id}")
        support = ctx.adj_sheets[a.adj_id]
        sup = _Sheet(ws.parent[support], [])
        for k in range(n):
            col = t.first_col + k
            if dil_row is None:
                sup.put(t.check_row, col, "n/a", italic=True, color=MUTED, halign="right")
                continue
            sup.formula(t.check_row, col, f"={_xref(SHEET_BRIDGE, pc + k, dil_row)}-{_a1(col, t.revision_row)}",
                        num_fmt=CHECK_FORMAT, italic=True)
        ctx.add_check(AREA_SUPPORT, f"ABS({t.check_cell})")

    ws.freeze_panes = _a1(pc, header_row + 1)
    return _BridgeRefs(rows=key_rows, first_col=pc, footed=footed)


def _bridge_source_agreement(sh: _Sheet, ctx: _Ctx, row: int, key_rows: dict[str, int], pc: int, link_col: int,
                             rrefs: _ReconRefs) -> int:
    n = len(ctx.labels)
    schedule = ctx.schedule
    reported = dict(schedule.reported_ebitda) if schedule is not None and schedule.reported_ebitda else \
        dict(ctx.wp.reconciliation.mgmt_reported_ebitda)
    adjusted = dict(schedule.adjusted_ebitda) if schedule is not None else {}
    source = schedule.source_file if schedule is not None else "management's schedule"
    lines: list[tuple[str, str, Optional[dict[str, str]], Optional[str]]] = []
    if reported and "mgmt_reported_ebitda" in key_rows:
        lines.append(("input", f"Reported EBITDA per management's schedule ({source}, 'Reported EBITDA' row)",
                      reported, None))
        lines.append(("check", "Check: Reported EBITDA (per management) above less the schedule", None,
                      "mgmt_reported_ebitda"))
    if adjusted and "mgmt_adjusted_ebitda" in key_rows:
        lines.append(("input", f"Management adjusted EBITDA per management's schedule ({source})", adjusted, None))
        lines.append(("check", "Check: Management adjusted EBITDA above less the schedule (a difference is "
                               "management's own arithmetic; see Data Quality)", None, "mgmt_adjusted_ebitda"))
    if rrefs.ni_rows and "net_income" in key_rows and all(p in rrefs.ni_rows for p in ctx.labels):
        lines.append(("recon", "Net income per the GL-P&L Reconciliation (months compared)", None, None))
        lines.append(("check", "Check: Net income (per GL) above less the reconciliation", None, "net_income"))
    if not lines:
        return row
    sh.put(row, 1, "Agreement to source data (should be zero; see the Cover)", span=link_col, bold=True, color=NAVY,
           fill=SECTION_FILL)
    row += 1
    prev = row
    for kind, label, values, key in lines:
        sh.text(row, 2, label, italic=kind == "check", color=MUTED if kind == "check" else FORMULA_BLACK)
        for k, p in enumerate(ctx.labels):
            col = pc + k
            if kind == "input":
                sh.money(row, col, (values or {}).get(p))
            elif kind == "recon":
                sh.formula(row, col, "=" + _xref(SHEET_RECON, rrefs.ni_col, rrefs.ni_rows[p]), link=True)
            else:
                sh.formula(row, col, f"={_a1(col, key_rows[key])}-{_a1(col, prev)}", num_fmt=CHECK_FORMAT,
                           italic=True)
        if kind == "check" and n:
            sh.check_row(row, pc, pc + n - 1)
            ctx.add_check(AREA_SOURCE, _abs_range(SHEET_BRIDGE, pc, pc + n - 1, row))
        prev = row
        row += 1
    return row


# ---------------------------------------------------------------------------
# Open Questions, Reconciliation, Data Quality, Review Log
# ---------------------------------------------------------------------------


def _write_questions(ws: Worksheet, ctx: _Ctx) -> tuple[int, int]:
    """Returns the (first, last) data rows, for the Cover's live counts."""
    sh = _Sheet(ws, [13, 9, 72, 10, 34, 12, 50])
    _title_block(sh, ctx, "Open Questions for Management", "Information requests for management, in reference "
                 "order. Status and responses as recorded by the diligence team.")
    row = 6
    sh.header(row, [("Q id", 1), ("Ref", 1), ("Question", 1), ("Priority", 1), ("Basis", 1), ("Status", 1),
                    ("Response", 1)])
    header = row
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{header}:{header}")
    row += 1
    first = row
    for a in ctx.wp.assessments:
        for q in sorted(ctx.questions.get(a.adj_id, []), key=lambda q: _natural_key(q.q_id)):
            drafted = ctx.drafted.get(a.adj_id) is q
            sh.text(row, 1, q.q_id, wrap=False, bold=drafted)
            sh.link(row, 2, a.adj_id, ctx.adj_sheets[a.adj_id])
            sh.text(row, 3, _management_text(q.text))
            high = q.priority == "high"
            sh.text(row, 4, q.priority, bold=high, color=BANNER_RED if high else FORMULA_BLACK, halign="center")
            sh.text(row, 5, _plain_basis(q.basis))
            is_open = q.status == QuestionStatus.OPEN
            sh.text(row, 6, q.status.value, bold=is_open, halign="center",
                    fill=TREATMENT_STYLES[Treatment.REVISE][0] if is_open else None)
            sh.text(row, 7, q.response or ("Drafted by the diligence team; not yet issued." if drafted else ""),
                    italic=drafted)
            row += 1
    last = max(first, row - 1)
    if row == first:
        sh.put(row, 3, "No open questions.", italic=True, color=MUTED)
    else:
        ws.auto_filter.ref = f"A{header}:G{last}"
    ws.freeze_panes = _a1(3, header + 1)
    return first, last


def _write_recon(ws: Worksheet, ctx: _Ctx) -> _ReconRefs:
    recon = ctx.wp.reconciliation
    cur = ctx.currency
    sh = _Sheet(ws, [13, 17, 17, 17, 17, 12, 44])
    _title_block(sh, ctx, "GL to P&L Reconciliation", f"Management's monthly P&L compared with the GL by account and "
                 f"month. {cur}, debit-positive: expenses +, revenue and other income (in parentheses) -. "
                 "Variance = P&L less GL.")
    row = 6
    for label, value in (
        ("Months compared", recon.months_compared),
        ("Accounts compared", recon.accounts_compared),
        ("Account-months outside tolerance", recon.variance_count),
    ):
        sh.put(row, 1, label, span=2, bold=True)
        sh.count(row, 3, value)
        row += 1
    sh.put(row, 1, f"Tolerance ({cur})", span=2, bold=True)
    sh.put(row, 3, q2(D(ctx.wp.deal.tolerance)), num_fmt="#,##0.00", color=INPUT_BLUE, halign="right")
    row += 2

    items = sorted(recon.items, key=lambda it: (it.month, it.account))
    months = sorted({it.month for it in items})
    variances = [it for it in items if not it.within_tolerance]

    sh.section(row, "SUMMARY BY MONTH")
    row += 1
    month_header = row
    sh.header(row, [("Month", 1), (f"GL total ({cur}, debit +)", 1), (f"P&L total ({cur}, debit +)", 1),
                    (f"Variance: P&L less GL ({cur})", 1), ("# account variances", 1)])
    row += 1
    sum_first = row
    month_rows: list[int] = []
    for m in months:
        sh.put(row, 1, _month_date(m), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        month_rows.append(row)  # SUMIFS formulas are filled once the detail table's rows are known
        row += 1
    if not months:
        sh.put(row, 1, "No account-months compared.", italic=True, color=MUTED)
        row += 1
    sum_last = row - 1
    sh.put(row, 1, "Total", bold=True, border=_FINAL_BORDER)
    for col in range(2, 6):
        L = get_column_letter(col)
        formula = f"=SUM({L}{sum_first}:{L}{sum_last})" if months else "=0"
        sh.formula(row, col, formula, bold=True, border=_FINAL_BORDER, num_fmt="#,##0" if col == 5 else NUMBER_FORMAT)
    row += 2

    # Analysis-period subtotals: net income per the GL here is what the bridge's first line must agree to.
    refs = _ReconRefs(ni_col=5)
    sh.section(row, "SUMMARY BY ANALYSIS PERIOD (months compared)")
    row += 1
    sh.header(row, [("Period", 1), (f"GL total ({cur}, debit +)", 1), (f"P&L total ({cur}, debit +)", 1),
                    (f"Variance ({cur})", 1), (f"Net income per GL ({cur}; + = profit)", 1), ("First month", 1),
                    ("Last month", 1)])
    row += 1
    months_rng = f"$A${sum_first}:$A${sum_last}"
    for p in ctx.wp.deal.periods:
        if p.label not in ctx.labels:
            continue
        refs.ni_rows[p.label] = row
        sh.put(row, 1, p.label, bold=True)
        sh.put(row, 6, _month_date(p.start), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        sh.put(row, 7, _month_date(p.end), num_fmt=MONTH_FORMAT, halign="left", color=INPUT_BLUE)
        for col in (2, 3):
            L = get_column_letter(col)
            if months:
                sh.formula(row, col, f'=SUMIFS(${L}${sum_first}:${L}${sum_last},{months_rng},">="&$F{row},'
                                     f'{months_rng},"<="&$G{row})')
            else:
                sh.formula(row, col, "=0")
        sh.formula(row, 4, f"=C{row}-B{row}")
        sh.formula(row, 5, f"=-B{row}", bold=True)
        row += 1
    row += 1

    sh.section(row, f"VARIANCE DETAIL: OUTSIDE TOLERANCE ({len(variances)})")
    row += 1
    sh.header(row, [("Month", 1), (f"GL ({cur}, debit +)", 1), (f"P&L ({cur}, debit +)", 1),
                    (f"Variance ({cur})", 1), ("Within tolerance?", 1), ("Account", 1), ("Account name", 1)])
    row += 1
    if variances:
        for it in variances:
            _recon_row(sh, row, it)
            row += 1
    else:
        sh.put(row, 1, "None.", italic=True, color=MUTED)
        row += 1
    print_last = row - 1
    row += 1

    sh.section(row, f"ALL ACCOUNT-MONTHS COMPARED ({len(items)}; on screen only, not printed)")
    row += 1
    detail_header = row
    sh.header(row, [("Month", 1), (f"GL ({cur}, debit +)", 1), (f"P&L ({cur}, debit +)", 1),
                    (f"Variance ({cur})", 1), ("Within tolerance?", 1), ("Account", 1), ("Account name", 1)])
    row += 1
    detail_first = row
    for it in items:
        _recon_row(sh, row, it)
        row += 1
    detail_last = max(detail_first, row - 1)

    def rng(col: str) -> str:
        return f"${col}${detail_first}:${col}${detail_last}"

    for r in month_rows:
        sh.formula(r, 2, f"=SUMIFS({rng('B')},{rng('A')},$A{r})")
        sh.formula(r, 3, f"=SUMIFS({rng('C')},{rng('A')},$A{r})")
        sh.formula(r, 4, f"=C{r}-B{r}")
        sh.formula(r, 5, f'=COUNTIFS({rng("A")},$A{r},{rng("E")},"No")', num_fmt="#,##0")
    if items:
        ws.auto_filter.ref = f"A{detail_header}:G{detail_last}"
    ws.freeze_panes = "A6"
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{month_header}:{month_header}", last_row=print_last)
    return refs


def _recon_row(sh: _Sheet, row: int, it: Any) -> None:
    sh.put(row, 1, _month_date(it.month), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
    sh.money(row, 2, it.gl_amount)
    sh.money(row, 3, it.pl_amount)
    sh.formula(row, 4, f"=C{row}-B{row}")
    ok = it.within_tolerance
    sh.put(row, 5, "Yes" if ok else "No", halign="center", bold=not ok, color=BANNER_RED if not ok else FORMULA_BLACK)
    sh.text(row, 6, it.account, wrap=False)
    sh.text(row, 7, it.account_name)


def _write_data_quality(ws: Worksheet, ctx: _Ctx) -> tuple[int, int]:
    """Returns the (first, last) issue rows, for the Cover's live counts."""
    cur = ctx.currency
    sh = _Sheet(ws, [11, 34, 10, 10, 14, 15, 26, 70, 26])
    _title_block(sh, ctx, "Data Quality", "Every reconciliation and ingest issue, most severe first. Each amount "
                 "states its sign basis.")
    row = 6
    issues = sorted(enumerate(ctx.wp.reconciliation.issues), key=lambda t: (_SEVERITY_RANK[t[1].severity], t[0]))
    sh.header(row, [("Severity", 1), ("Code", 1), ("Month", 1), ("Account", 1), ("Period", 1),
                    (f"Amount ({cur})", 1), ("Sign basis of the amount", 1), ("Message", 1), ("GL rows", 1)])
    header = row
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{header}:{header}")
    row += 1
    first = row
    for _, issue in issues:
        sh.severity(row, 1, issue.severity)
        sh.text(row, 2, issue.code.value, wrap=False)
        md = _month_date(issue.month) if issue.month else None
        if md is not None:
            sh.put(row, 3, md, num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        sh.text(row, 4, issue.account or "", halign="center")
        sh.text(row, 5, issue.period_label or "")
        if issue.amount is not None:
            sh.money(row, 6, issue.amount)
            sh.text(row, 7, _DQ_SIGN_BASIS.get(issue.code, "As stated in the message"), italic=True, color=MUTED)
        sh.text(row, 8, issue.message, indent=1)
        sh.text(row, 9, _gl_rows_text(issue.entry_ids))
        row += 1
    issues_last = max(first, row - 1)
    if not issues:
        sh.put(row, 2, "No data quality issues.", italic=True, color=MUTED)
        row += 1
    else:
        ws.auto_filter.ref = f"A{header}:I{row - 1}"
    row += 1

    dropped = [f for f in ctx.wp.doc_facts if f.dropped_quotes]
    sh.section(row, "AI QUOTE VERIFICATION")
    row += 1
    sh.put(row, 1, f"{len(ctx.wp.doc_facts)} documents analysed ({ctx.wp.ai_mode}). Quotes that were not verbatim on "
                   "the cited page were dropped and counted, never repaired.", italic=True, color=MUTED)
    row += 1
    if ctx.wp.ai_fallbacks:
        sh.text(row, 1, f"AI calls that failed and fell back to the rules ({len(ctx.wp.ai_fallbacks)}): "
                        + "; ".join(ctx.wp.ai_fallbacks), span=8, color=BANNER_RED)
        row += 1
    if dropped:
        sh.header(row, [("Document", 2), ("Extractor", 1), ("Dropped", 1)], start_col=1)
        row += 1
        f0 = row
        for f in dropped:
            sh.text(row, 1, f.doc_id, span=2)
            sh.text(row, 3, f.extractor)
            sh.count(row, 4, f.dropped_quotes)
            row += 1
        sh.put(row, 1, "Total dropped", span=3, bold=True, border=_TOP_BORDER)
        sh.formula(row, 4, f"=SUM(D{f0}:D{row - 1})", bold=True, num_fmt="#,##0", border=_TOP_BORDER)
        row += 1
    else:
        sh.put(row, 1, "No quotes dropped.", italic=True, color=MUTED)
        row += 1
    row += 1

    sh.section(row, f"INGEST NOTES ({len(ctx.wp.ingest_notes)})")
    row += 1
    for note in ctx.wp.ingest_notes:
        sh.text(row, 1, note, span=8)
        row += 1
    if not ctx.wp.ingest_notes:
        sh.put(row, 1, "None.", italic=True, color=MUTED)
    ws.freeze_panes = _a1(1, header + 1)
    return first, issues_last


def _write_review_log(ws: Worksheet, ctx: _Ctx) -> None:
    n = len(ctx.labels)
    cur = ctx.currency
    tool_amt, final_amt = 9, 9 + n
    rat_col = final_amt + n
    widths = [5, 22, 16, 9, 15, 15, 24, 10] + [13] * (2 * n) + [54, 34, 12, 14]
    sh = _Sheet(ws, widths)
    _title_block(sh, ctx, "Review Log", "Every reviewer decision in log order (append-only). The latest decision "
                 "per adjustment is Current.")
    g, h = 6, 7
    for col, title in enumerate(("#", "Timestamp", "Reviewer", "Ref", "Tool treatment", "Reviewer treatment",
                                 "Correction type", "Tool error?"), start=1):
        sh.header_tall(g, h, col, title)
    sh.header(g, [(f"Tool amounts at review ({cur})", n)], start_col=tool_amt)
    sh.header(h, [(p, 1) for p in ctx.labels], start_col=tool_amt)
    sh.header(g, [(f"Reviewer amounts ({cur})", n)], start_col=final_amt)
    sh.header(h, [(p, 1) for p in ctx.labels], start_col=final_amt)
    for col, title in ((rat_col, "Rationale"), (rat_col + 1, "Question updates"), (rat_col + 2, "Current?"),
                       (rat_col + 3, "Tool changed since?")):
        sh.header_tall(g, h, col, title)
    ws.row_dimensions[g].height = 30
    ctx.prints[ws.title] = _PrintSpec(title_rows=f"{g}:{h}", title_cols=4)
    row = h + 1
    for i, rv in enumerate(ctx.wp.reviews, start=1):
        current = ctx.latest.get(rv.adj_id) is rv
        sh.put(row, 1, i, halign="center")
        sh.text(row, 2, rv.timestamp, wrap=False)
        sh.text(row, 3, rv.reviewer)
        if rv.adj_id in ctx.adj_sheets:
            sh.link(row, 4, rv.adj_id, ctx.adj_sheets[rv.adj_id])
        else:
            sh.text(row, 4, rv.adj_id)
        sh.treatment(row, 5, rv.tool_treatment)
        sh.treatment(row, 6, rv.treatment)
        sh.text(row, 7, rv.correction_type.value)
        tool_error = rv.correction_type in TOOL_ERROR_CORRECTIONS
        sh.text(row, 8, "Yes" if tool_error else "No", bold=tool_error, halign="center",
                color=BANNER_RED if tool_error else FORMULA_BLACK)
        for k, p in enumerate(ctx.labels):
            if rv.tool_amounts:
                sh.money(row, tool_amt + k, rv.tool_amounts.get(p))
            else:
                sh.pending(row, tool_amt + k)
            if _review_pending(rv):
                sh.pending(row, final_amt + k)
            else:
                sh.money(row, final_amt + k, rv.amounts.get(p), bold=True)
        sh.text(row, rat_col, rv.rationale, indent=1)
        sh.text(row, rat_col + 1, "; ".join(f"{q}: {v}" for q, v in rv.question_updates.items()))
        sh.text(row, rat_col + 2, "Current" if current else "Superseded", italic=not current, halign="center")
        changed = ctx.stale(rv)
        sh.text(row, rat_col + 3, "Yes: re-review" if changed else "No", bold=changed, halign="center",
                color=BANNER_RED if changed else FORMULA_BLACK)
        row += 1
    if not ctx.wp.reviews:
        sh.put(row, 2, "No reviewer decisions recorded: every adjustment is UNREVIEWED.", bold=True,
               color=BANNER_RED)
    else:
        ws.auto_filter.ref = f"A{h}:{get_column_letter(rat_col + 3)}{row - 1}"
    ws.freeze_panes = _a1(5, h + 1)


# ---------------------------------------------------------------------------
# Cover
# ---------------------------------------------------------------------------


_CONTENTS = [
    (SHEET_BRIDGE, "Reported EBITDA (GL) to management adjusted to diligence adjusted EBITDA, with checks."),
    (SHEET_SUMMARY, "One row per adjustment: claimed, tool proposed, final, difference, treatment, and status."),
    ("Adj <ref>", "One support sheet per adjustment: tie-out, flag walk, flags, facts vs judgment, documents, "
                  "decision, and the ticked GL listing tied to the tie-out."),
    (SHEET_QUESTIONS, "Questions for management, with priority, basis, status, and responses."),
    (SHEET_RECON, "GL vs management P&L by month and analysis period, with variance detail."),
    (SHEET_DATA_QUALITY, "Reconciliation and ingest issues; AI quote verification."),
    (SHEET_REVIEW_LOG, "Every reviewer decision, in order, with correction types."),
]


def _write_cover(
    ws: Worksheet,
    ctx: _Ctx,
    srefs: _SummaryRefs,
    brefs: _BridgeRefs,
    q_rows: tuple[int, int],
    dq_rows: tuple[int, int],
) -> None:
    wp = ctx.wp
    deal = wp.deal
    n = len(ctx.labels)
    sh = _Sheet(ws, [40] + [18] * max(n, 4) + [40])
    last = sh.last_col
    ws.sheet_view.showGridLines = False
    sh.put(1, 1, "Quality of Earnings: Evidence Review Workpaper", bold=True, size=16, color=NAVY)
    sh.put(2, 1, deal.target_name, bold=True, size=13)
    sh.put(3, 1, _banner_text(ctx), span=last, bold=True, size=11, color=WHITE, fill=BANNER_RED,
           halign="center", valign="center", wrap=True)
    ws.row_dimensions[3].height = max(ws.row_dimensions[3].height or 0, 30)
    row = 5

    # Sign-off: completed by people, never by the tool.
    sh.section(row, "SIGN-OFF")
    row += 1
    sh.header(row, [("Role", 1), ("Name / initials", 2), ("Date", 1)])
    row += 1
    for role in ("Prepared by", "Reviewed by", "Approved by (engagement manager)"):
        sh.put(row, 1, role, bold=True)
        sh.signoff_input(row, 2, span=2)
        sh.signoff_input(row, 4, is_date=True)
        row += 1
    sh.text(row, 1, f"Generated by QoE Evidence Review {wp.tool_version}, run {wp.run_id}, {wp.created_at}. The tool "
                    "proposes; the reviewer decides. The workpaper is a DRAFT until every item is reviewed and the "
                    "sign-off above is complete.", span=last, italic=True, color=MUTED)
    row += 2

    sh.section(row, "ENGAGEMENT AND RUN")
    row += 1
    mgmt_ids = {a.adj_id for a in ctx.mgmt_items}
    dil_ids = {a.adj_id for a in ctx.dil_items}
    reviewed = f"{len(mgmt_ids & ctx.latest.keys())} of {len(mgmt_ids)} management adjustments reviewed"
    if dil_ids:
        reviewed += f"; {len(dil_ids & ctx.latest.keys())} of {len(dil_ids)} diligence-identified items reviewed"
    info: list[tuple[str, Any]] = [
        ("Target", deal.target_name),
        ("Industry", deal.industry or ""),
        ("Deal ID", deal.deal_id),
        ("Currency", f"{ctx.currency}. Whole dollars displayed; cell values keep cents."),
        ("GL data range", f"{deal.data_start} to {deal.data_end}"),
        ("Tie-out tolerance", f"{fmt(deal.tolerance)} {ctx.currency}"),
        ("Run ID", wp.run_id),
        ("Run created", wp.created_at),
        ("Tool version", wp.tool_version),
        ("AI mode", f"{wp.ai_mode} (AI proposes facts, links and question wording; code computes every amount "
                    "and treatment; the reviewer decides)"),
        ("Documents analysed", f"{len(wp.doc_facts)}; quotes dropped as not verbatim: "
                               f"{sum(f.dropped_quotes for f in wp.doc_facts)}"
                               + (f" (run total: {wp.ai_dropped_quotes})" if wp.ai_dropped_quotes else "")),
        ("Adjustments", f"{len(mgmt_ids)} on management's schedule; {len(dil_ids)} identified by diligence "
                        "(not on the schedule)"),
        ("Reviewer decisions", f"{len(wp.reviews)} logged; {reviewed}"),
    ]
    if wp.ai_fallbacks:
        info.append(("AI fallbacks", f"{len(wp.ai_fallbacks)} AI call(s) failed and fell back to the rules; see "
                                     "Data Quality."))
    for label, value in info:
        sh.put(row, 1, label, bold=True)
        sh.text(row, 2, value, span=last - 1)
        row += 1
    row += 1

    sh.section(row, "ANALYSIS PERIODS")
    row += 1
    sh.header(row, [("Period", 1), ("First month", 1), ("Last month", 1), ("Months", 1)])
    row += 1
    for p in deal.periods:
        sh.put(row, 1, p.label, bold=True)
        sh.put(row, 2, _month_date(p.start), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        sh.put(row, 3, _month_date(p.end), num_fmt=MONTH_FORMAT, halign="center", color=INPUT_BLUE)
        sh.count(row, 4, len(months_in(p)))
        row += 1
    if len({m for p in deal.periods for m in months_in(p)}) < sum(len(months_in(p)) for p in deal.periods):
        sh.put(row, 1, "Periods overlap (e.g. a TTM period shares months with a fiscal year): amounts are "
                       "computed by month and aggregated to each period, so period columns do not add across.",
               span=last, italic=True, color=MUTED, wrap=True)
        row += 1
    row += 1

    headline = [
        ("gl_ebitda", "Reported EBITDA (per GL)"),
        ("mgmt_reported_ebitda", "Reported EBITDA (per management)"),
        ("mgmt_adjusted_ebitda", "Management adjusted EBITDA"),
        ("diligence_adjusted_ebitda", "Diligence adjusted EBITDA"),
    ]
    present = [(k, lab) for k, lab in headline if k in brefs.rows]
    if present:
        sh.section(row, f"HEADLINE EBITDA ({ctx.currency}; + increases EBITDA)")
        row += 1
        sh.header(row, [("", 1)] + [(p, 1) for p in ctx.labels])
        row += 1
        hl_rows: dict[str, int] = {}
        for key, label in present:
            final_line = key == "diligence_adjusted_ebitda"
            sh.put(row, 1, label, bold=final_line, border=_FINAL_BORDER if final_line else None)
            for k in range(n):
                sh.formula(row, 2 + k, "=" + _xref(SHEET_BRIDGE, brefs.first_col + k, brefs.rows[key]), link=True,
                           bold=final_line, border=_FINAL_BORDER if final_line else None)
            if final_line and ctx.unreviewed and 2 + n <= last:
                fill_u, font_u = UNREVIEWED_STYLE
                sh.put(row, 2 + n, f"DRAFT: {len(ctx.unreviewed)} unreviewed", bold=True, color=font_u, fill=fill_u,
                       halign="center")
            hl_rows[key] = row
            row += 1
        if {"diligence_adjusted_ebitda", "mgmt_adjusted_ebitda"} <= hl_rows.keys():
            sh.put(row, 1, "Diligence less management adjusted", italic=True)
            for k in range(n):
                col = 2 + k
                sh.formula(row, col, f"={_a1(col, hl_rows['diligence_adjusted_ebitda'])}"
                                     f"-{_a1(col, hl_rows['mgmt_adjusted_ebitda'])}", italic=True)
            row += 1
        if not brefs.footed:
            sh.put(row, 1, "WARNING: the bridge does not foot to the tool's subtotals; see EBITDA Bridge.",
                   span=last, bold=True, color=BANNER_RED)
            row += 1
        row += 1

    row = _cover_checks(sh, ctx, row, last)

    def rng(sheet: str, col: int, first: int, last_row: int) -> str:
        L = get_column_letter(col)
        return f"{_quoted(sheet)}!${L}${first}:${L}${last_row}"

    def summary_ranges(first: int, last_row: int) -> tuple[str, str, str]:
        return tuple(rng(SHEET_SUMMARY, c, first, last_row)  # type: ignore[return-value]
                     for c in (srefs.tool_col, srefs.reviewer_col, srefs.status_col))

    def status_table(row: int, title: str, ranges: tuple[str, str, str]) -> int:
        tool_r, rev_r, stat_r = ranges
        sh.section(row, title)
        row += 1
        sh.header(row, [("Treatment", 1), ("Tool proposal", 1), ("Reviewer decision", 1), ("Final treatment", 1)])
        row += 1
        count_first = row
        for t in Treatment:
            sh.treatment(row, 1, t)
            crit = f'"{t.value}"'
            sh.formula(row, 2, f"=COUNTIF({tool_r},{crit})", num_fmt="#,##0")
            sh.formula(row, 3, f"=COUNTIF({rev_r},{crit})", num_fmt="#,##0")
            # Reviewed items carry the reviewer's treatment; unreviewed ones carry the tool's.
            sh.formula(row, 4, f'=COUNTIF({rev_r},{crit})+COUNTIFS({stat_r},"{UNREVIEWED}",{tool_r},{crit})',
                       num_fmt="#,##0")
            row += 1
        sh.put(row, 1, "Total", bold=True, border=_FINAL_BORDER)
        for col in (2, 3, 4):
            L = get_column_letter(col)
            sh.formula(row, col, f"=SUM({L}{count_first}:{L}{row - 1})", bold=True, num_fmt="#,##0",
                       border=_FINAL_BORDER)
        row += 1
        sh.text(row, 1, "Final treatment: the reviewer's decision, or the tool's proposal while UNREVIEWED. "
                        "REQUEST_INFO items are pending and excluded from diligence adjusted EBITDA.",
                span=last, italic=True, color=MUTED)
        return row + 2

    mgmt_ranges = summary_ranges(srefs.first_row, srefs.last_row)
    dil_ranges = (summary_ranges(srefs.dil_first_row, srefs.dil_last_row)
                  if dil_ids and srefs.dil_first_row is not None and srefs.dil_last_row is not None else None)
    row = status_table(row, "ADJUSTMENT STATUS: MANAGEMENT ADJUSTMENTS" if dil_ranges else "ADJUSTMENT STATUS",
                       mgmt_ranges)
    if dil_ranges:
        row = status_table(row, DILIGENCE_BLOCK.upper(), dil_ranges)
        sh.header(row, [("Review status", 1), ("Management", 1), ("Diligence-identified", 1)])
        row += 1
    q_range = rng(SHEET_QUESTIONS, 6, *q_rows)
    dq_range = rng(SHEET_DATA_QUALITY, 1, *dq_rows)
    for label, status, style in (
        ("Reviewed: agreed with tool", AGREED, None),
        ("Reviewed: overridden", OVERRIDDEN, None),
        ("UNREVIEWED (tool proposal carried)", UNREVIEWED, UNREVIEWED_STYLE),
    ):
        if style:
            sh.put(row, 1, label, bold=True, fill=style[0], color=style[1])
        else:
            sh.put(row, 1, label, bold=True)
        sh.formula(row, 2, f'=COUNTIF({mgmt_ranges[2]},"{status}")', num_fmt="#,##0", bold=bool(style))
        if dil_ranges:
            sh.formula(row, 3, f'=COUNTIF({dil_ranges[2]},"{status}")', num_fmt="#,##0", bold=bool(style))
        row += 1
    for label, formula in (
        ("Open questions for management", f'=COUNTIF({q_range},"{QuestionStatus.OPEN.value}")'),
        ("Data quality issues: critical", f'=COUNTIF({dq_range},"{Severity.CRITICAL.value}")'),
        ("Data quality issues: warning", f'=COUNTIF({dq_range},"{Severity.WARNING.value}")'),
        ("Data quality issues: info", f'=COUNTIF({dq_range},"{Severity.INFO.value}")'),
    ):
        sh.put(row, 1, label, bold=True)
        sh.formula(row, 2, formula, num_fmt="#,##0")
        row += 1
    sh.put(row, 1, "Pending items with no open question", bold=True,
           color=BANNER_RED if ctx.drafted else FORMULA_BLACK)
    sh.count(row, 2, len(ctx.drafted), bold=bool(ctx.drafted), fill=CHECK_FAIL_FILL if ctx.drafted else None)
    if ctx.drafted:
        sh.text(row, 3, f"{', '.join(ctx.drafted)}: pending with no open request to management. A request was "
                        "drafted from the reviewer's rationale on Open Questions; issue it.", span=last - 2,
                color=BANNER_RED)
    row += 2

    sh.section(row, "LEGEND")
    row += 1
    for t in Treatment:
        sh.treatment(row, 1, t)
        sh.text(row, 2, TREATMENT_MEANING[t], span=last - 1, indent=1)
        row += 1
    for status, meaning in (
        (UNREVIEWED, "No reviewer decision yet: the tool proposal is carried until a reviewer signs off."),
        (AGREED, "Reviewer agreed with the tool's treatment and amounts (within tolerance)."),
        (OVERRIDDEN, "Reviewer changed the tool's treatment or amounts; see the correction type."),
    ):
        sh.status(row, 1, status)
        sh.text(row, 2, meaning, span=last - 1, indent=1)
        row += 1
    for text, color, meaning in (
        ("1,234", INPUT_BLUE, "Blue: hard-coded input carried from the workpaper (GL, documents, tool, reviewer)."),
        ("1,234", FORMULA_BLACK, "Black: formula (subtotals, differences, checks)."),
        ("1,234", LINK_GREEN, "Green: link to another sheet."),
        ("(1,234)", FORMULA_BLACK, "Parentheses: a negative amount; a dash is zero. On EBITDA schedules (bridge, "
                                   "summary, tie-outs, flag effects) a negative reduces EBITDA. On GL listings, the "
                                   "reconciliation and data quality amounts (debit +) it is a credit; each header "
                                   "states its basis."),
    ):
        sh.put(row, 1, text, color=color, halign="right")
        sh.text(row, 2, meaning, span=last - 1, indent=1)
        row += 1
    sh.put(row, 1, "", fill=SIGNOFF_FILL, border=_HEADER_BORDER)
    sh.text(row, 2, "Light yellow: a sign-off cell for the preparer or reviewer to complete.", span=last - 1, indent=1)
    row += 1
    for group, marks in (("Entry role", ROLE_TICKMARKS), ("Document", DOC_TICKMARKS), ("Other", TICKMARKS[-2:])):
        for mark, meaning in marks:
            sh.put(row, 1, mark, bold=True, color=LINK_GREEN, halign="right")
            sh.text(row, 2, f"Tickmark ({group.lower()}): {meaning}", span=last - 1, indent=1)
            row += 1
    sh.put(row, 1, "C / W / I", bold=True, halign="right")
    sh.text(row, 2, "Flag severity: critical / warning / info.", span=last - 1, indent=1)
    row += 2

    sh.section(row, "CONTENTS")
    row += 1
    for sheet, desc in _CONTENTS:
        if sheet in ws.parent.sheetnames:
            sh.link(row, 1, sheet, sheet)
        else:
            sh.put(row, 1, sheet)
        sh.text(row, 2, desc, span=last - 1)
        row += 1
        if sheet.startswith("Adj "):
            for group, items in (("", ctx.mgmt_items), (DILIGENCE_BLOCK, ctx.dil_items)):
                if group and items:
                    sh.put(row, 1, group, span=last, italic=True, color=NAVY)
                    row += 1
                for a in items:
                    cell = sh.link(row, 1, ctx.adj_sheets[a.adj_id], ctx.adj_sheets[a.adj_id])
                    cell.alignment = Alignment(indent=2, vertical="top")
                    sh.text(row, 2, a.title, span=last - 1, color=MUTED)
                    row += 1
    row += 1

    sh.section(row, f"INPUT FILES ({len(wp.input_hashes)}), SHA-256")
    row += 1
    path_span = min(3, last - 1)
    for relpath, digest in sorted(wp.input_hashes.items()):
        sh.text(row, 1, relpath, span=path_span)
        sh.text(row, 1 + path_span, digest, span=last - path_span, color=MUTED, size=9)
        row += 1
    ctx.prints[ws.title] = _PrintSpec()


def _cover_checks(sh: _Sheet, ctx: _Ctx, row: int, last: int) -> int:
    """Workbook checks by area, the overall status, and the separate agreement to source data."""
    areas = [a for a in _WORKBOOK_AREAS if ctx.checks.get(a)]
    source = ctx.checks.get(AREA_SOURCE, [])
    if not areas and not source:
        return row
    sh.section(row, "CHECKS (sum of absolute differences; should be zero)")
    row += 1
    sh.header(row, [("Area", 1), ("Status", 1), ("Difference", 1)])
    row += 1
    overall = row
    area_rows: list[int] = []
    row += 1
    for area in areas:
        parts = _chunks(ctx.checks[area])
        for k, value in enumerate(parts, start=1):
            sh.text(row, 1, area + (f" (part {k})" if len(parts) > 1 else ""), indent=1)
            sh.formula(row, 3, f"={value}", num_fmt=CHECK_FORMAT)
            _status_cell(sh, row, 2, _a1(3, row))
            area_rows.append(row)
            row += 1
    if areas:
        sh.put(overall, 1, "Workbook checks (all areas below)", bold=True)
        sh.formula(overall, 3, "=" + "+".join(_a1(3, r) for r in area_rows), num_fmt=CHECK_FORMAT, bold=True)
        _status_cell(sh, overall, 2, _a1(3, overall), text="DIFFERENCE: see checks")
    if source:
        sh.text(row, 1, AREA_SOURCE, bold=True)
        sh.formula(row, 3, "=" + "+".join(f"({x})" for x in _chunks(source)), num_fmt=CHECK_FORMAT)
        _status_cell(sh, row, 2, _a1(3, row), text="DIFFERENCE: see EBITDA Bridge")
        sh.text(row, 4, "Not part of the workbook checks: a difference here is in the source data (e.g. management's "
                        "own arithmetic), not in this workbook.", span=last - 3, italic=True, color=MUTED)
        row += 1
    return row + 1


def _chunks(exprs: list[str]) -> list[str]:
    """Join check expressions with "+", split so that no formula exceeds Excel's length limit."""
    out: list[str] = []
    cur = ""
    for e in exprs:
        if cur and len(cur) + 1 + len(e) >= _MAX_FORMULA - 10:
            out.append(cur)
            cur = e
        else:
            cur = f"{cur}+{e}" if cur else e
    if cur:
        out.append(cur)
    return out or ["0"]


def _status_cell(sh: _Sheet, row: int, col: int, ref: str, *, text: str = "DIFFERENCE") -> None:
    cell = sh.formula(row, col, f'=IF({ref}<0.01,"OK","{text}")', num_fmt="General", bold=True, halign="left")
    sh.ws.conditional_formatting.add(cell.coordinate, FormulaRule(formula=[f'{cell.coordinate}<>"OK"'],
                                                                  fill=_fill(CHECK_FAIL_FILL)))


# ---------------------------------------------------------------------------
# Workbook assembly
# ---------------------------------------------------------------------------


def _use_arial_default(wb: Workbook) -> None:
    # Unstyled cells (and anything a reviewer types later) inherit the default font.
    arial = Font(name=FONT_NAME, size=10, family=2)
    wb._fonts = IndexedList([arial])
    wb._named_styles["Normal"].font = arial


# Landscape paper sizes (openpyxl code, name) and printable width in inches at 0.5" side margins.
_PAPERS = ((1, 10.0), (5, 13.0), (3, 16.0))  # letter, legal, tabloid
_MIN_SCALE = 0.75  # never print below 75% (7.5pt for the 10pt body text)


def _inches(width: float) -> float:
    return (7 * width + 5) / 96  # Excel column width (characters of Arial 10) to inches at 96 dpi


def _page_setup(ws: Worksheet, ctx: _Ctx) -> None:
    """Landscape, fitted to width at a legible scale: letter, legal or tabloid by the printed width, and
    more than one page across (repeating the leading columns) only when even tabloid would be too small."""
    spec = ctx.prints.get(ws.title, _PrintSpec())
    last_col = spec.last_col or max(1, ws.max_column)
    widths = [ws.column_dimensions[get_column_letter(c)].width or 9.0 for c in range(1, last_col + 1)]
    total = sum(_inches(w) for w in widths)
    title_w = sum(_inches(w) for w in widths[: spec.title_cols])
    ps = ws.page_setup
    ps.orientation = "landscape"
    paper, pages = _PAPERS[-1][0], 1
    for code, printable in _PAPERS:
        if total <= printable / _MIN_SCALE:
            paper = code
            break
    else:
        printable = _PAPERS[-1][1]
        pages = 2
        while (total + title_w * (pages - 1)) / pages > printable / _MIN_SCALE and pages < 6:
            pages += 1
    ps.paperSize = paper
    ps.fitToWidth = pages
    ps.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6, header=0.3, footer=0.3)
    if spec.title_rows:
        ws.print_title_rows = spec.title_rows
    if spec.title_cols and pages > 1:
        ws.print_title_cols = f"A:{get_column_letter(spec.title_cols)}"
    last_row = spec.last_row or ws.max_row
    ws.print_area = f"A1:{get_column_letter(last_col)}{max(1, last_row)}"
    label = ("SYNTHETIC | " if ctx.wp.deal.synthetic else "") + (
        "DRAFT" if ctx.unreviewed else "DRAFT until signed off")
    ws.oddHeader.left.text = f"{ctx.wp.deal.target_name}: &A"
    ws.oddHeader.right.text = "Prepared: ________  Reviewed: ________"
    ws.oddFooter.left.text = f"{label}: QoE Evidence Review, run {ctx.wp.run_id}"
    ws.oddFooter.right.text = "Page &P of &N"


def build_workbook(wp: Workpaper, *, pkg: Optional[DealPackage] = None) -> Workbook:
    """Build the workpaper in memory (see ``export_workpaper``)."""
    ctx = _context(wp, pkg)
    wb = Workbook()
    _use_arial_default(wb)
    cover = wb.active
    cover.title = SHEET_COVER
    bridge = wb.create_sheet(SHEET_BRIDGE)
    summary = wb.create_sheet(SHEET_SUMMARY)
    support = {a.adj_id: wb.create_sheet(ctx.adj_sheets[a.adj_id]) for a in wp.assessments}
    questions = wb.create_sheet(SHEET_QUESTIONS)
    recon = wb.create_sheet(SHEET_RECON)
    dq = wb.create_sheet(SHEET_DATA_QUALITY)
    log = wb.create_sheet(SHEET_REVIEW_LOG)

    # Support sheets are the source; the summary links to them, the bridge checks against the summary and
    # the reconciliation, and the summary reconciles back to the bridge.
    tie = {a.adj_id: _write_support(support[a.adj_id], ctx, a) for a in wp.assessments}
    srefs = _write_summary(summary, ctx, tie)
    rrefs = _write_recon(recon, ctx)
    brefs = _write_bridge(bridge, ctx, srefs, tie, rrefs)
    _finish_summary(summary, ctx, srefs, brefs)
    q_rows = _write_questions(questions, ctx)
    dq_rows = _write_data_quality(dq, ctx)
    _write_review_log(log, ctx)
    _write_cover(cover, ctx, srefs, brefs, q_rows, dq_rows)

    for ws in wb.worksheets:
        _page_setup(ws, ctx)
    wb.active = 0
    wb.calculation.fullCalcOnLoad = True
    label = ("SYNTHETIC, " if wp.deal.synthetic else "") + "DRAFT"
    wb.properties.title = f"QoE Evidence Review: {wp.deal.target_name} ({label})"
    wb.properties.subject = f"Quality of earnings evidence review, deal {wp.deal.deal_id}, run {wp.run_id}"
    wb.properties.creator = f"QoE Evidence Review {wp.tool_version}"
    wb.properties.keywords = label
    return wb
