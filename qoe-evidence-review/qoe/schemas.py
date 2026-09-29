"""Strict Pydantic v2 schemas for QoE Evidence Review.

Conventions (see docs/SPEC.md):
- Money is a normalized decimal string ("12345.67"), never a float.
- GL amounts are signed debit-positive: expenses and costs are positive,
  revenue and other income are negative.
- Adjustment amounts are signed from EBITDA's point of view: a positive
  amount increases EBITDA (an add-back), a negative amount reduces it.
- Months are "YYYY-MM". Analysis periods have a label ("FY2024",
  "TTM Jun-26") and an inclusive month range.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EbitdaClass(str, Enum):
    REVENUE = "REVENUE"
    COGS = "COGS"
    OPEX = "OPEX"
    OTHER_INCOME = "OTHER_INCOME"
    OTHER_EXPENSE = "OTHER_EXPENSE"
    INTEREST = "INTEREST"
    TAXES = "TAXES"
    DEPRECIATION = "DEPRECIATION"
    AMORTIZATION = "AMORTIZATION"
    BALANCE_SHEET = "BALANCE_SHEET"


# Classes added back to net income to reach EBITDA.
EBITDA_EXCLUDED_CLASSES = frozenset(
    {EbitdaClass.INTEREST, EbitdaClass.TAXES, EbitdaClass.DEPRECIATION, EbitdaClass.AMORTIZATION}
)


class AdjustmentCategory(str, Enum):
    NON_RECURRING = "NON_RECURRING"
    OWNER_DISCRETIONARY = "OWNER_DISCRETIONARY"
    NORMALIZATION = "NORMALIZATION"
    OUT_OF_PERIOD = "OUT_OF_PERIOD"
    PRO_FORMA = "PRO_FORMA"
    OTHER = "OTHER"


class Treatment(str, Enum):
    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"
    REQUEST_INFO = "REQUEST_INFO"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FlagCode(str, Enum):
    NO_GL_SUPPORT = "NO_GL_SUPPORT"
    PARTIAL_GL_SUPPORT = "PARTIAL_GL_SUPPORT"
    EXCESS_GL_ACTIVITY = "EXCESS_GL_ACTIVITY"
    NO_DOCUMENT_SUPPORT = "NO_DOCUMENT_SUPPORT"
    DOC_GL_AMOUNT_MISMATCH = "DOC_GL_AMOUNT_MISMATCH"
    PERIOD_MISMATCH = "PERIOD_MISMATCH"
    OUT_OF_PERIOD = "OUT_OF_PERIOD"
    RECURRING_PATTERN = "RECURRING_PATTERN"
    CONTINUING_OBLIGATION = "CONTINUING_OBLIGATION"
    OVERLAP_WITH_OTHER_ADJUSTMENT = "OVERLAP_WITH_OTHER_ADJUSTMENT"
    ALREADY_EXCLUDED_FROM_EBITDA = "ALREADY_EXCLUDED_FROM_EBITDA"
    OFFSETTING_RECOVERY = "OFFSETTING_RECOVERY"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    UNSIGNED_OR_DRAFT_SUPPORT = "UNSIGNED_OR_DRAFT_SUPPORT"
    PRO_FORMA_NOT_REALIZED = "PRO_FORMA_NOT_REALIZED"
    SIGN_ERROR = "SIGN_ERROR"
    DUPLICATE_GL_ENTRY = "DUPLICATE_GL_ENTRY"
    NORMALIZATION_BENCHMARK_MISSING = "NORMALIZATION_BENCHMARK_MISSING"


class DataQualityCode(str, Enum):
    DUPLICATE_GL_ENTRY = "DUPLICATE_GL_ENTRY"
    MISSING_PERIOD = "MISSING_PERIOD"
    RECON_VARIANCE = "RECON_VARIANCE"
    UNMAPPED_ACCOUNT = "UNMAPPED_ACCOUNT"
    PL_ACCOUNT_NOT_IN_GL = "PL_ACCOUNT_NOT_IN_GL"
    GL_ACCOUNT_NOT_IN_PL = "GL_ACCOUNT_NOT_IN_PL"
    MGMT_EBITDA_DIFFERS_FROM_GL = "MGMT_EBITDA_DIFFERS_FROM_GL"
    MGMT_SCHEDULE_ARITHMETIC = "MGMT_SCHEDULE_ARITHMETIC"


class CorrectionType(str, Enum):
    """Why a reviewer's final treatment differs from the tool's proposal.

    Tool-error types become regression eval cases; JUDGMENT_DIFFERENCE and
    NEW_INFORMATION do not count against the tool.
    """

    NONE = "NONE"
    TOOL_WRONG_LINK = "TOOL_WRONG_LINK"
    TOOL_MISSED_EVIDENCE = "TOOL_MISSED_EVIDENCE"
    TOOL_WRONG_AMOUNT = "TOOL_WRONG_AMOUNT"
    TOOL_WRONG_FLAG = "TOOL_WRONG_FLAG"
    TOOL_WRONG_TREATMENT = "TOOL_WRONG_TREATMENT"
    JUDGMENT_DIFFERENCE = "JUDGMENT_DIFFERENCE"
    NEW_INFORMATION = "NEW_INFORMATION"


TOOL_ERROR_CORRECTIONS = frozenset(
    {
        CorrectionType.TOOL_WRONG_LINK,
        CorrectionType.TOOL_MISSED_EVIDENCE,
        CorrectionType.TOOL_WRONG_AMOUNT,
        CorrectionType.TOOL_WRONG_FLAG,
        CorrectionType.TOOL_WRONG_TREATMENT,
    }
)


class QuestionStatus(str, Enum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    CLOSED = "CLOSED"


# ---------------------------------------------------------------------------
# Deal inputs
# ---------------------------------------------------------------------------


class PeriodDef(StrictModel):
    label: str  # e.g. "FY2024", "TTM Jun-26"; must match schedule column headers
    start: str  # "YYYY-MM" inclusive
    end: str  # "YYYY-MM" inclusive


class DealFiles(StrictModel):
    """Paths relative to the deal directory."""

    gl: str
    chart_of_accounts: str
    monthly_pl: str
    adjustments: str
    documents_dir: str = "documents"
    account_mapping_overrides: Optional[str] = None


class DealMeta(StrictModel):
    # Used in file and sheet names, so it must be a plain, safe token.
    deal_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    target_name: str
    industry: str = ""
    synthetic: bool = True
    currency: str = "USD"
    periods: list[PeriodDef]
    data_start: str  # first month the GL is expected to cover
    data_end: str  # last month the GL is expected to cover
    gl_format: str = "auto"  # auto | qbo_gl_csv | netsuite_csv | xero_xlsx
    files: DealFiles
    tolerance: str = "1.00"  # tie-out tolerance in currency units


class Account(StrictModel):
    number: str
    name: str
    source_type: str  # account type as the source system labels it
    ebitda_class: EbitdaClass
    mapping_basis: str = ""  # how ebitda_class was decided (type rule, name rule, override)


class GLEntry(StrictModel):
    entry_id: str  # "GL-R{source_row}"
    date: str  # YYYY-MM-DD
    period: str  # YYYY-MM
    account: str  # account number
    account_name: str
    txn_type: str = ""
    doc_number: str = ""
    counterparty: str = ""
    memo: str = ""
    amount: str  # debit-positive signed decimal string
    source_file: str
    source_row: int  # 1-based row as a spreadsheet app displays it
    dimensions: dict[str, str] = Field(default_factory=dict)


class PLAccountLine(StrictModel):
    """One account row from management's monthly P&L (account-level)."""

    account: str
    account_name: str
    section: str  # section heading the row sat under, e.g. "Income", "Expenses"
    amounts: dict[str, str]  # month -> debit-positive signed amount
    source_row: int


class ManagementPL(StrictModel):
    source_file: str
    months: list[str]
    lines: list[PLAccountLine]


class AdjustmentClaim(StrictModel):
    adj_id: str  # as management labels it: "M-01", "3", "A-1"
    title: str
    category_raw: str = ""
    category: AdjustmentCategory = AdjustmentCategory.OTHER
    description: str = ""
    gl_accounts: list[str] = Field(default_factory=list)
    support_refs: list[str] = Field(default_factory=list)
    amounts: dict[str, str]  # period label -> claimed amount (+ increases EBITDA)
    source_row: int


class ManagementSchedule(StrictModel):
    source_file: str
    period_labels: list[str]
    net_income: dict[str, str] = Field(default_factory=dict)
    interest: dict[str, str] = Field(default_factory=dict)
    taxes: dict[str, str] = Field(default_factory=dict)
    depreciation_amortization: dict[str, str] = Field(default_factory=dict)
    reported_ebitda: dict[str, str] = Field(default_factory=dict)
    adjustments: list[AdjustmentClaim] = Field(default_factory=list)
    total_adjustments: dict[str, str] = Field(default_factory=dict)
    adjusted_ebitda: dict[str, str] = Field(default_factory=dict)


class DocumentPage(StrictModel):
    page: int = Field(ge=1)
    text: str


class SourceDocument(StrictModel):
    doc_id: str  # filename within the documents dir (unique per deal)
    relpath: str  # path relative to the deal directory
    media_type: str  # pdf | txt | md | eml
    sha256: str
    pages: list[DocumentPage]

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)


class DealPackage(StrictModel):
    deal_dir: str
    meta: DealMeta
    accounts: dict[str, Account]
    gl: list[GLEntry]
    pl: ManagementPL
    schedule: ManagementSchedule
    documents: list[SourceDocument]
    input_hashes: dict[str, str] = Field(default_factory=dict)  # relpath -> sha256
    ingest_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evidence (AI-proposed, code-validated)
# ---------------------------------------------------------------------------


class EvidenceQuote(StrictModel):
    """A quote that must be an exact substring of the cited page's text."""

    doc_id: str
    page: int = Field(ge=1)
    quote: str


class AmountFact(StrictModel):
    label: str  # "total_due", "monthly_fee", "settlement_amount", "line", ...
    amount: str
    quote: EvidenceQuote


class TermFact(StrictModel):
    kind: str  # monthly_fee | retainer | auto_renew | term_end | installments | ongoing_services | one_time | other
    text: str  # short normalized description
    quote: EvidenceQuote


class DocFacts(StrictModel):
    doc_id: str
    doc_type: str  # invoice | engagement_letter | contract | settlement_agreement | separation_agreement | insurance | correspondence | payroll | memo | benchmark | other
    title: str = ""
    counterparty: Optional[str] = None
    doc_date: Optional[str] = None  # YYYY-MM-DD
    reference_numbers: list[str] = Field(default_factory=list)  # invoice / matter / claim numbers
    amounts: list[AmountFact] = Field(default_factory=list)
    service_period_start: Optional[str] = None  # YYYY-MM-DD
    service_period_end: Optional[str] = None
    is_draft: bool = False
    is_signed: Optional[bool] = None
    terms: list[TermFact] = Field(default_factory=list)
    key_statements: list[EvidenceQuote] = Field(default_factory=list)
    extractor: str = "rules"  # "rules" or "llm:<model>"
    dropped_quotes: int = 0  # AI quotes rejected because they were not verbatim


# ---------------------------------------------------------------------------
# Tool outputs
# ---------------------------------------------------------------------------


class GLLink(StrictModel):
    entry_id: str
    period: str  # month of the entry
    amount: str  # entry amount (debit-positive)
    score: float
    reasons: list[str] = Field(default_factory=list)
    group: str = ""  # cluster key (vendor + matter / memo theme)
    supports_claim: bool = True  # False = linked for context only (e.g. prior-period comparable)
    doc_ids: list[str] = Field(default_factory=list)
    # Audit-trail role of the entry in this adjustment:
    #   supporting (claimed and carried) | removed (claimed, taken out by a flag) |
    #   moved (claimed, carried in another period by an OUT_OF_PERIOD effect) |
    #   recovery (offset applied in the proposal) | context (not part of the claim).
    role: str = ""
    claimed: bool = False  # management's claimed amount includes this entry (in any period)
    claimed_in: list[str] = Field(default_factory=list)  # period labels whose claim includes it (FY and TTM can differ)
    removed_by: Optional[FlagCode] = None  # the flag that removed it, when role == "removed"


class DocLink(StrictModel):
    doc_id: str
    relation: str  # invoice_for_entry | agreement | correspondence | recovery | other
    entry_ids: list[str] = Field(default_factory=list)
    score: float
    reasons: list[str] = Field(default_factory=list)
    quotes: list[EvidenceQuote] = Field(default_factory=list)


class Flag(StrictModel):
    code: FlagCode
    severity: Severity
    message: str
    period_label: Optional[str] = None
    amount_impact: Optional[str] = None  # signed EBITDA effect the flag argues for, if quantifiable
    # Period label -> signed change this flag drives in the proposed amount (EBITDA-signed).
    # Empty for flags that do not move the number (questions, context-only activity).
    effects: dict[str, str] = Field(default_factory=dict)
    entry_ids: list[str] = Field(default_factory=list)
    doc_ids: list[str] = Field(default_factory=list)
    quotes: list[EvidenceQuote] = Field(default_factory=list)
    related_adj_ids: list[str] = Field(default_factory=list)


class RecurrenceObservation(StrictModel):
    group: str
    amounts_by_period: dict[str, str]  # period label -> amount of comparable activity
    entry_ids: list[str] = Field(default_factory=list)
    note: str = ""


class OpenQuestion(StrictModel):
    q_id: str  # "Q-M-01-1"
    adj_id: Optional[str] = None
    text: str
    priority: str = "medium"  # high | medium | low
    basis: str = ""  # why the question is being asked (flag code / fact)
    status: QuestionStatus = QuestionStatus.OPEN
    response: str = ""


class Fact(StrictModel):
    """A documented fact: something the evidence shows, with its references."""

    text: str
    entry_ids: list[str] = Field(default_factory=list)
    quotes: list[EvidenceQuote] = Field(default_factory=list)


class AdjustmentAssessment(StrictModel):
    adj_id: str
    title: str
    category: AdjustmentCategory
    source: str = "management"  # management (on the seller's schedule) | diligence (identified by the tool)
    description: str = ""  # management's stated basis, carried so the workpaper stands alone
    gl_accounts: list[str] = Field(default_factory=list)
    support_refs: list[str] = Field(default_factory=list)
    claimed: dict[str, str]  # period label -> amount
    traced_gl: dict[str, str]  # period label -> GL amount linked in support of the claim
    documented: dict[str, str]  # period label -> portion of traced GL with document support
    proposed: dict[str, str]  # period label -> tool's proposed diligence amount (empty for REQUEST_INFO)
    treatment: Treatment
    confidence: str = "medium"  # high | medium | low
    gl_links: list[GLLink] = Field(default_factory=list)
    doc_links: list[DocLink] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    recurrence: list[RecurrenceObservation] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)  # documented facts
    judgment_questions: list[str] = Field(default_factory=list)  # unresolved judgment calls
    open_questions: list[OpenQuestion] = Field(default_factory=list)  # questions for management
    rationale: str = ""


class ReconciliationItem(StrictModel):
    month: str
    account: str
    account_name: str
    gl_amount: str
    pl_amount: str
    variance: str  # pl - gl
    within_tolerance: bool


class DataQualityIssue(StrictModel):
    code: DataQualityCode
    severity: Severity
    message: str
    month: Optional[str] = None
    account: Optional[str] = None
    period_label: Optional[str] = None
    amount: Optional[str] = None
    entry_ids: list[str] = Field(default_factory=list)


class EbitdaComponents(StrictModel):
    net_income: str
    interest: str
    taxes: str
    depreciation: str
    amortization: str
    ebitda: str


class ReconciliationResult(StrictModel):
    items: list[ReconciliationItem]  # every (month, account) compared
    issues: list[DataQualityIssue]
    gl_ebitda: dict[str, EbitdaComponents]  # period label -> components derived from GL
    mgmt_reported_ebitda: dict[str, str]  # period label -> per management schedule
    months_compared: int
    accounts_compared: int
    variance_count: int


class ReviewDecision(StrictModel):
    adj_id: str
    reviewer: str
    timestamp: str  # ISO 8601
    treatment: Treatment
    amounts: dict[str, str]  # final diligence amounts (empty for REQUEST_INFO)
    rationale: str
    tool_treatment: Treatment
    tool_amounts: dict[str, str]
    correction_type: CorrectionType = CorrectionType.NONE
    question_updates: dict[str, str] = Field(default_factory=dict)  # q_id -> status or response note


class BridgeRow(StrictModel):
    key: str  # stable row key: "net_income", "gl_ebitda", "mgmt:M-01", "dil:M-01", ...
    label: str
    kind: str  # component | subtotal | mgmt_adjustment | diligence_adjustment | memo
    adj_id: Optional[str] = None
    amounts: dict[str, str]


class EbitdaBridge(StrictModel):
    period_labels: list[str]
    rows: list[BridgeRow]


class Workpaper(StrictModel):
    """Everything one review run produced; persisted as JSON."""

    run_id: str
    tool_version: str
    created_at: str
    ai_mode: str  # "rules" or "llm:<model>"
    deal: DealMeta
    input_hashes: dict[str, str]
    ingest_notes: list[str] = Field(default_factory=list)
    reconciliation: ReconciliationResult
    doc_facts: list[DocFacts] = Field(default_factory=list)
    assessments: list[AdjustmentAssessment]  # management items in schedule order, then diligence items
    reviews: list[ReviewDecision] = Field(default_factory=list)
    bridge: EbitdaBridge
    schedule: Optional[ManagementSchedule] = None
    ai_fallbacks: list[str] = Field(default_factory=list)  # AI calls that failed and fell back to rules
    ai_dropped_quotes: int = 0  # AI quotes rejected because they were not verbatim  # management's schedule as presented (needed to rebuild the bridge)


# ---------------------------------------------------------------------------
# Ground truth (evaluation only; the pipeline must never read it)
# ---------------------------------------------------------------------------


class ExpectedAdjustment(StrictModel):
    adj_id: str
    case_type: str  # ADEQUATE | PARTIAL | OVERLAP | EBITDA_EXCLUDED | CONTRADICTED | RECURRING | RECOVERY_OFFSET | OUT_OF_PERIOD | WRONG_PERIOD | NEEDS_INFO | UNDERSTATED | SIGN_ERROR | DUPLICATE_POSTING | SUPPORTED_TOPSIDE | MISSING_GL_MONTH
    treatment: Treatment
    amounts: dict[str, str] = Field(default_factory=dict)  # final diligence amounts; empty for REQUEST_INFO
    supporting_gl_rows: list[int] = Field(default_factory=list)  # GL source rows that support the claim
    related_gl_rows: list[int] = Field(default_factory=list)  # rows a good review should surface but that do not support it
    supporting_docs: list[str] = Field(default_factory=list)  # doc_ids that support the amount carried
    related_docs: list[str] = Field(default_factory=list)  # doc_ids a good review surfaces as evidence against / context
    expected_flags: list[FlagCode] = Field(default_factory=list)  # flags a correct review must raise
    question_topics: list[str] = Field(default_factory=list)  # topics an open-questions list should cover
    rationale: str
    ambiguity: str = "low"  # low | medium | high
    reviewer_note: str = ""


class ExpectedDataQuality(StrictModel):
    code: DataQualityCode
    month: Optional[str] = None
    account: Optional[str] = None
    gl_rows: list[int] = Field(default_factory=list)
    note: str = ""


class GroundTruth(StrictModel):
    deal_id: str
    authored_by: str
    split: str  # dev | holdout
    adjustments: list[ExpectedAdjustment]
    data_quality: list[ExpectedDataQuality] = Field(default_factory=list)
    # Diligence-identified items not on management's schedule (e.g. reversing a duplicate
    # posting). Matched to tool items with source="diligence" by supporting_gl_rows overlap.
    diligence_items: list[ExpectedAdjustment] = Field(default_factory=list)
    gl_ebitda: dict[str, str] = Field(default_factory=dict)  # period label -> reported EBITDA per GL
    # gl_ebitda + non-REQUEST_INFO management finals + diligence items
    diligence_adjusted_ebitda: dict[str, str] = Field(default_factory=dict)
    notes: str = ""
