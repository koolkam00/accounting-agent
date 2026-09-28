"""Tests for qoe.export_xlsx: workbook structure, Deals formatting rules, formulas, and LibreOffice recalculation."""

from __future__ import annotations

import re
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from qoe.export_xlsx import (
    NUMBER_FORMAT,
    SHEET_BRIDGE,
    SHEET_COVER,
    SHEET_SUMMARY,
    _fallback_final_amounts,
    _plan_subtotals,
    build_workbook,
    export_workpaper,
    find_recalc_script,
    latest_reviews,
    recalc_and_check,
    resolve_final_amounts,
    sanitize_sheet_name,
    support_sheet_names,
    workbook_filename,
)
from qoe.money import D, fmt
from qoe.review_store import bridge_display_rows
from qoe.periods import add_months, month_range
from qoe.schemas import (
    Account,
    AdjustmentAssessment,
    AdjustmentCategory,
    AdjustmentClaim,
    BridgeRow,
    CorrectionType,
    DataQualityCode,
    DataQualityIssue,
    DealFiles,
    DealMeta,
    DealPackage,
    DocFacts,
    DocLink,
    EbitdaBridge,
    EbitdaClass,
    EbitdaComponents,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    GLEntry,
    GLLink,
    ManagementPL,
    ManagementSchedule,
    OpenQuestion,
    PeriodDef,
    ReconciliationItem,
    ReconciliationResult,
    RecurrenceObservation,
    ReviewDecision,
    Severity,
    TermFact,
    Treatment,
    Workpaper,
)

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["FY2024", "FY2025", "TTM Jun-26"]
BANNED = re.compile(r"\b(XLOOKUP|XMATCH|FILTER|UNIQUE|SORT|SEQUENCE)\s*\(", re.I)


# ---------------------------------------------------------------------------
# Fixture: a realistic, fictitious workpaper
# ---------------------------------------------------------------------------


def _pm(*values: object) -> dict[str, str]:
    return {label: fmt(v) for label, v in zip(LABELS, values)}


def _q(doc: str, text: str, page: int = 1) -> EvidenceQuote:
    return EvidenceQuote(doc_id=doc, page=page, quote=text)


LIT_LETTER = "3.1 Harrow Legal Engagement Letter Matter 7781.pdf"
RETAINER_LETTER = "3.2 Harrow Legal General Retainer 2023.pdf"
LIT_INVOICE = "3.3 Harrow Legal Invoice 25-114.pdf"
ERP_MSA = "5.1 Corvid ERP Master Services Agreement.pdf"
ERP_EMAIL = "5.2 Email controller re ERP subscription.txt"
COMP_DRAFT = "6.1 DRAFT CEO Employment Agreement.pdf"
STORM_LETTER = "7.4 Keystone Mutual claim settlement letter.pdf"
SEARCH_LETTER = "4.1 Talbot Search engagement letter.pdf"


def _assessments() -> list[AdjustmentAssessment]:
    retainer_quote = _q(RETAINER_LETTER, "a monthly retainer of $2,500 continuing until terminated by either party")
    lit = AdjustmentAssessment(
        adj_id="A-1",
        title="Litigation legal fees (Matter 7781)",
        category=AdjustmentCategory.NON_RECURRING,
        claimed=_pm(0, 90000, 50000),
        traced_gl=_pm(0, 90000, 50000),
        documented=_pm(0, 60000, "25000.50"),
        proposed=_pm(0, 60000, "25000.50"),
        treatment=Treatment.REVISE,
        confidence="medium",
        gl_links=[
            GLLink(entry_id="GL-R1201", period="2025-02", amount="30000.00", score=4.5,
                   reasons=["account 6400", "reference 7781"], group="harrow legal|7781",
                   doc_ids=[LIT_INVOICE]),
            GLLink(entry_id="GL-R1302", period="2025-09", amount="30000.00", score=4.5,
                   reasons=["account 6400", "reference 7781"], group="harrow legal|7781"),
            GLLink(entry_id="GL-R1410", period="2025-11", amount="25000.50", score=4.0,
                   reasons=["account 6400", "counterparty"], group="harrow legal|7781", doc_ids=[LIT_INVOICE]),
            GLLink(entry_id="GL-R1500", period="2025-08", amount="30000.00", score=3.0,
                   reasons=["account 6400", "counterparty"], group="harrow legal|retainer"),
            GLLink(entry_id="GL-R880", period="2024-06", amount="2500.00", score=2.0,
                   reasons=["counterparty"], group="harrow legal|retainer", supports_claim=False),
        ],
        doc_links=[
            DocLink(doc_id=LIT_LETTER, relation="agreement", entry_ids=["GL-R1201", "GL-R1302"], score=3.0,
                    reasons=["matter 7781"], quotes=[_q(LIT_LETTER, "Matter 7781: Pryor v. Harborview")]),
            DocLink(doc_id=RETAINER_LETTER, relation="agreement", entry_ids=["GL-R1500", "GL-R880"], score=2.5,
                    reasons=["counterparty"], quotes=[retainer_quote]),
            DocLink(doc_id=LIT_INVOICE, relation="invoice_for_entry", entry_ids=["GL-R1201"], score=4.0,
                    reasons=["doc number 25-114"], quotes=[_q(LIT_INVOICE, "Total due: $30,000.00", page=2)]),
        ],
        flags=[
            Flag(code=FlagCode.RECURRING_PATTERN, severity=Severity.WARNING,
                 message="General retainer activity also appears in FY2024 at a comparable level.",
                 period_label="FY2025", amount_impact="-30000.00", entry_ids=["GL-R1500", "GL-R880"],
                 doc_ids=[RETAINER_LETTER]),
            Flag(code=FlagCode.CONTINUING_OBLIGATION, severity=Severity.WARNING,
                 message="The retainer continues until terminated; it is part of the ongoing cost base.",
                 entry_ids=["GL-R1500"], doc_ids=[RETAINER_LETTER], quotes=[retainer_quote]),
        ],
        recurrence=[
            RecurrenceObservation(group="harrow legal|retainer", amounts_by_period=_pm(30000, 30000, 30000),
                                  entry_ids=["GL-R880", "GL-R1500"], note="Retainer billed every month."),
        ],
        facts=[
            Fact(text="Matter 7781 invoices in FY2025 total $60,000.00.", entry_ids=["GL-R1201", "GL-R1302"],
                 quotes=[_q(LIT_INVOICE, "Total due: $30,000.00", page=2)]),
            Fact(text="The general retainer is $2,500 per month and continues until terminated.",
                 entry_ids=["GL-R1500"], quotes=[retainer_quote]),
        ],
        judgment_questions=["Is any post-settlement monitoring cost part of the ongoing cost base?"],
        open_questions=[
            OpenQuestion(q_id="Q-A-1-1", adj_id="A-1", text="Confirm no further fees on Matter 7781 after settlement.",
                         priority="high", basis="CONTINUING_OBLIGATION"),
            OpenQuestion(q_id="Q-A-1-2", adj_id="A-1", priority="medium", basis="documented fact",
                         text="Provide the insurer's confirmation of the settlement payment."),
        ],
        rationale="Litigation invoices under Matter 7781 support $60,000 (FY2025); the general retainer recurs.",
    )
    search = AdjustmentAssessment(
        adj_id="A-2",
        title="Executive search fee",
        category=AdjustmentCategory.NON_RECURRING,
        claimed=_pm(0, 30000, 10000),
        traced_gl=_pm(0, 30000, 10000),
        documented=_pm(0, 30000, 10000),
        proposed=_pm(0, 30000, 10000),
        treatment=Treatment.ACCEPT,
        confidence="high",
        gl_links=[
            GLLink(entry_id="GL-R1601", period="2025-04", amount="10000.00", score=5.0, doc_ids=[SEARCH_LETTER]),
            GLLink(entry_id="GL-R1602", period="2025-05", amount="10000.00", score=5.0, doc_ids=[SEARCH_LETTER]),
            GLLink(entry_id="GL-R1603", period="2025-07", amount="10000.00", score=5.0, doc_ids=[SEARCH_LETTER]),
        ],
        doc_links=[DocLink(doc_id=SEARCH_LETTER, relation="agreement", entry_ids=["GL-R1601"], score=4.0,
                           quotes=[_q(SEARCH_LETTER, "payable in three equal installments")])],
        facts=[Fact(text="Three installments of $10,000 agree to the engagement letter.",
                    entry_ids=["GL-R1601", "GL-R1602", "GL-R1603"])],
        rationale="Retained search fee agrees to the engagement letter and GL.",
    )
    erp = AdjustmentAssessment(
        adj_id="A-3",
        title='"One-time" ERP implementation',
        category=AdjustmentCategory.NON_RECURRING,
        claimed=_pm(0, 72000, 36000),
        traced_gl=_pm(0, 72000, 36000),
        documented=_pm(0, 72000, 36000),
        proposed=_pm(0, 0, 0),
        treatment=Treatment.REJECT,
        confidence="medium",
        gl_links=[GLLink(entry_id=f"GL-R{1700 + i}", period=add_months("2025-01", i), amount="6000.00", score=4.0,
                         doc_ids=[ERP_MSA]) for i in range(12)],
        doc_links=[
            DocLink(doc_id=ERP_MSA, relation="agreement", score=4.0,
                    quotes=[_q(ERP_MSA, "a monthly fee of $6,000"), _q(ERP_MSA, "renews automatically", page=3)]),
            DocLink(doc_id=ERP_EMAIL, relation="correspondence", score=2.0,
                    quotes=[_q(ERP_EMAIL, "our ERP subscription")]),
        ],
        flags=[
            Flag(code=FlagCode.CONTRADICTORY_EVIDENCE, severity=Severity.WARNING,
                 message="The controller calls the cost a subscription.", doc_ids=[ERP_EMAIL],
                 quotes=[_q(ERP_EMAIL, "our ERP subscription")]),
            Flag(code=FlagCode.CONTINUING_OBLIGATION, severity=Severity.WARNING,
                 message="36-month term with automatic renewal.", doc_ids=[ERP_MSA]),
        ],
        facts=[Fact(text="The MSA sets a monthly fee of $6,000.", quotes=[_q(ERP_MSA, "a monthly fee of $6,000")])],
        judgment_questions=["Does any part of the fee relate to one-time configuration work?"],
        open_questions=[OpenQuestion(q_id="Q-A-3-1", adj_id="A-3", text="=Provide the statement of work, if any.",
                                     priority="low", basis="CONTRADICTORY_EVIDENCE")],
        rationale="Documents describe a recurring subscription.",
    )
    comp = AdjustmentAssessment(
        adj_id="A-4",
        title="Owner compensation normalization",
        category=AdjustmentCategory.NORMALIZATION,
        claimed=_pm(250000, 250000, 250000),
        traced_gl=_pm(550000, 550000, 550000),
        documented=_pm(0, 0, 0),
        proposed={},
        treatment=Treatment.REQUEST_INFO,
        confidence="high",
        doc_links=[DocLink(doc_id=COMP_DRAFT, relation="agreement", score=2.0,
                           quotes=[_q(COMP_DRAFT, "DRAFT - FOR DISCUSSION ONLY")])],
        flags=[
            Flag(code=FlagCode.UNSIGNED_OR_DRAFT_SUPPORT, severity=Severity.WARNING,
                 message="Only support is an unsigned draft agreement.", doc_ids=[COMP_DRAFT]),
            Flag(code=FlagCode.NORMALIZATION_BENCHMARK_MISSING, severity=Severity.WARNING,
                 message="No market compensation benchmark."),
        ],
        open_questions=[OpenQuestion(q_id="Q-A-4-1", adj_id="A-4", text="Provide the executed agreement.",
                                     priority="high", basis="UNSIGNED_OR_DRAFT_SUPPORT")],
        rationale="Provisionally $250,000 per year if an executed agreement supports the normalized level.",
    )
    storm = AdjustmentAssessment(
        adj_id="A-5",
        title="Hurricane repairs, net of insurance",
        category=AdjustmentCategory.NON_RECURRING,
        claimed=_pm(45000, 0, 0),
        traced_gl=_pm(45000, 0, 0),
        documented=_pm(45000, 0, 0),
        proposed=_pm(45000, -30000, 0),
        treatment=Treatment.REVISE,
        confidence="high",
        gl_links=[GLLink(entry_id="GL-R400", period="2024-10", amount="45000.00", score=4.0),
                  GLLink(entry_id="GL-R1250", period="2025-02", amount="-30000.00", score=3.5, supports_claim=False,
                         reasons=["claim number KM-24-5521"], doc_ids=[STORM_LETTER])],
        doc_links=[DocLink(doc_id=STORM_LETTER, relation="recovery", entry_ids=["GL-R1250"], score=3.5,
                           quotes=[_q(STORM_LETTER, "net payment of $30,000.00")])],
        flags=[Flag(code=FlagCode.OFFSETTING_RECOVERY, severity=Severity.WARNING,
                    message="Insurance recovery booked to other income was not adjusted.",
                    period_label="FY2025", amount_impact="-30000.00", entry_ids=["GL-R1250"],
                    doc_ids=[STORM_LETTER])],
        rationale="Recovery offsets the add-back in FY2025.",
    )
    refi = AdjustmentAssessment(
        adj_id="A-6",
        title="Refinancing costs",
        category=AdjustmentCategory.NON_RECURRING,
        claimed=_pm(0, 20000, 0),
        traced_gl=_pm(0, 20000, 0),
        documented=_pm(0, 20000, 0),
        proposed=_pm(0, 0, 0),
        treatment=Treatment.REJECT,
        confidence="high",
        gl_links=[GLLink(entry_id="GL-R1330", period="2025-06", amount="20000.00", score=4.0)],
        flags=[Flag(code=FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, severity=Severity.CRITICAL,
                    message="Booked to interest expense, which EBITDA already adds back.",
                    entry_ids=["GL-R1330"])],
        rationale="Already excluded from EBITDA.",
    )
    return [lit, search, erp, comp, storm, refi]


PREMIUM_NOTICE = "9.4 Keystone Risk premium installment notice May 2025.pdf"


def _diligence_item() -> AdjustmentAssessment:
    """SPEC §5.7: a duplicate posting the tool proposes to reverse (not on management's schedule)."""
    return AdjustmentAssessment(
        adj_id="D-1",
        title="Reverse duplicate premium posting (KRI-25-0507)",
        category=AdjustmentCategory.OTHER,
        source="diligence",
        description="Premium installment KRI-25-0507 is posted twice in May 2025; the P&L carries both.",
        gl_accounts=["6200"],
        support_refs=[PREMIUM_NOTICE],
        claimed=_pm(0, 0, 0),
        traced_gl=_pm(0, 0, 0),
        documented=_pm(0, 0, 0),
        proposed=_pm(0, 18400, 0),
        treatment=Treatment.REVISE,
        confidence="high",
        gl_links=[
            GLLink(entry_id="GL-R2210", period="2025-05", amount="18400.00", score=5.0, supports_claim=False,
                   reasons=["first posting: kept"], doc_ids=[PREMIUM_NOTICE]),
            GLLink(entry_id="GL-R2215", period="2025-05", amount="18400.00", score=5.0,
                   reasons=["duplicate of GL row 2210"], doc_ids=[PREMIUM_NOTICE]),
        ],
        doc_links=[DocLink(doc_id=PREMIUM_NOTICE, relation="invoice_for_entry", entry_ids=["GL-R2210", "GL-R2215"],
                           score=4.0, quotes=[_q(PREMIUM_NOTICE, "Installment due: $18,400.00")])],
        flags=[Flag(code=FlagCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING,
                    message="The same bill (KRI-25-0507) is posted twice, three days apart.",
                    entry_ids=["GL-R2210", "GL-R2215"])],
        open_questions=[OpenQuestion(q_id="Q-D-1-1", adj_id="D-1", priority="medium", basis="DUPLICATE_GL_ENTRY",
                                     text="Was installment KRI-25-0507 paid twice, refunded, or applied to a later bill?")],
        rationale="One installment is due; the second posting overstates FY2025 insurance expense.",
    )


def _reviews() -> list[ReviewDecision]:
    return [
        ReviewDecision(adj_id="A-3", reviewer="k.osei", timestamp="2026-09-01T10:00:00Z", treatment=Treatment.REJECT,
                       amounts=_pm(0, 0, 0), rationale="Agree: subscription.", tool_treatment=Treatment.REJECT,
                       tool_amounts=_pm(0, 0, 0)),
        ReviewDecision(adj_id="A-2", reviewer="k.osei", timestamp="2026-09-01T10:05:00Z", treatment=Treatment.ACCEPT,
                       amounts=_pm(0, 30000, 10000), rationale="Agrees to the letter.", tool_treatment=Treatment.ACCEPT,
                       tool_amounts=_pm(0, 30000, 10000),
                       question_updates={"Q-A-1-2": "ANSWERED: insurer letter received"}),
        ReviewDecision(adj_id="A-3", reviewer="m.reyes", timestamp="2026-09-02T09:00:00Z", treatment=Treatment.REVISE,
                       amounts=_pm(0, "12000.25", 0), rationale="SOW shows two months of one-time configuration.",
                       tool_treatment=Treatment.REJECT, tool_amounts=_pm(0, 0, 0),
                       correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
    ]


GL_COMPONENTS = {
    "FY2024": ("3912345.67", "210000.00", "45000.00", "380000.00", "25000.00"),
    "FY2025": ("4125000.10", "195000.00", "52000.00", "395000.00", "25000.00"),
    "TTM Jun-26": ("4200500.00", "180000.00", "50000.00", "401000.00", "25000.00"),
}
MGMT_DIFF = _pm(0, -25000, -25000)


def _build_bridge(assessments: list[AdjustmentAssessment], final: dict[str, dict[str, str]],
                  diff: dict[str, str] = MGMT_DIFF) -> EbitdaBridge:
    """Mirror of SPEC §5.6 so the export test does not depend on qoe.bridge."""

    def per(fn) -> dict[str, str]:
        return {p: fmt(fn(p)) for p in LABELS}

    items = [a for a in assessments if a.source == "diligence"]
    assessments = [a for a in assessments if a.source != "diligence"]
    comp = {p: [D(x) for x in GL_COMPONENTS[p]] for p in LABELS}
    gl = per(lambda p: sum(comp[p], Decimal(0)))
    rows = [BridgeRow(key=k, label=lab, kind="component", amounts=per(lambda p, i=i: comp[p][i]))
            for i, (k, lab) in enumerate([("net_income", "Net income (per GL)"), ("interest", "Interest expense, net"),
                                          ("taxes", "Income taxes"), ("depreciation", "Depreciation"),
                                          ("amortization", "Amortization")])]
    rows.append(BridgeRow(key="gl_ebitda", label="Reported EBITDA (per GL)", kind="subtotal", amounts=gl))
    rows.append(BridgeRow(key="mgmt_recon_diff", label="Difference to management's reported EBITDA", kind="memo",
                          amounts=dict(diff)))
    mgmt_rep = per(lambda p: D(gl[p]) + D(diff[p]))
    rows.append(BridgeRow(key="mgmt_reported_ebitda", label="Reported EBITDA (per management)", kind="subtotal",
                          amounts=mgmt_rep))
    for a in assessments:
        rows.append(BridgeRow(key=f"mgmt:{a.adj_id}", label=f"{a.title} (as claimed)", kind="mgmt_adjustment",
                              adj_id=a.adj_id, amounts=dict(a.claimed)))
    mgmt_total = per(lambda p: sum((D(a.claimed[p]) for a in assessments), Decimal(0)))
    rows.append(BridgeRow(key="mgmt_total", label="Total management adjustments", kind="subtotal", amounts=mgmt_total))
    mgmt_adj = per(lambda p: D(mgmt_rep[p]) + D(mgmt_total[p]))
    rows.append(BridgeRow(key="mgmt_adjusted_ebitda", label="Management adjusted EBITDA", kind="subtotal",
                          amounts=mgmt_adj))
    rows.append(BridgeRow(key="dil_recon", label="Reverse unsupported reporting difference (to GL)",
                          kind="diligence_adjustment", amounts=per(lambda p: -D(diff[p]))))
    dil = {a.adj_id: per(lambda p, a=a: D(final[a.adj_id].get(p)) - D(a.claimed[p])) for a in assessments}
    for a in assessments:
        rows.append(BridgeRow(key=f"dil:{a.adj_id}", label=f"{a.title}: diligence revision",
                              kind="diligence_adjustment", adj_id=a.adj_id, amounts=dil[a.adj_id]))
    for a in items:  # diligence-identified items carry their final amount (claimed is zero)
        dil[a.adj_id] = per(lambda p, a=a: D(final[a.adj_id].get(p)))
        rows.append(BridgeRow(key=f"dil:{a.adj_id}", label=f"Diligence-identified: {a.title}",
                              kind="diligence_adjustment", adj_id=a.adj_id, amounts=dil[a.adj_id]))
    dil_total = per(lambda p: -D(diff[p]) + sum((D(v[p]) for v in dil.values()), Decimal(0)))
    rows.append(BridgeRow(key="dil_total", label="Total diligence adjustments", kind="subtotal", amounts=dil_total))
    rows.append(BridgeRow(key="diligence_adjusted_ebitda", label="Diligence adjusted EBITDA", kind="subtotal",
                          amounts=per(lambda p: D(mgmt_adj[p]) + D(dil_total[p]))))
    pending = [a for a in assessments if not final[a.adj_id]]
    rows.append(BridgeRow(key="pending", label="Memo: management adjustments pending information (excluded)",
                          kind="memo", amounts=per(lambda p: sum((D(a.claimed[p]) for a in pending), Decimal(0)))))
    return EbitdaBridge(period_labels=LABELS, rows=rows)


def _reconciliation() -> ReconciliationResult:
    items: list[ReconciliationItem] = []
    accounts = [("4000", "Service Revenue", "-310000.00"), ("6000", "Salaries & Wages - Office", "118500.25"),
                ("6200", "Insurance", "8200.00")]
    for i, month in enumerate(month_range("2024-01", "2026-06")):
        for acct, name, base in accounts:
            gl = D(base) + (D(-1000) * i if acct == "4000" else D(0))
            pl = gl
            if month == "2025-12" and acct == "6000":
                pl = gl + D(25000)  # top-side accrual not in the GL
            if month == "2024-03" and acct == "6200":
                pl = gl + D("0.40")  # rounding, within tolerance
            items.append(ReconciliationItem(month=month, account=acct, account_name=name, gl_amount=fmt(gl),
                                            pl_amount=fmt(pl), variance=fmt(pl - gl),
                                            within_tolerance=abs(pl - gl) <= D("1.00")))
    issues = [
        DataQualityIssue(code=DataQualityCode.GL_ACCOUNT_NOT_IN_PL, severity=Severity.INFO,
                         message="Account 8050 appears in the GL but not in the P&L.", account="8050"),
        DataQualityIssue(code=DataQualityCode.RECON_VARIANCE, severity=Severity.WARNING,
                         message="P&L exceeds GL by $25,000.00 for account 6000 in Dec 2025.",
                         month="2025-12", account="6000", amount="25000.00"),
        DataQualityIssue(code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL, severity=Severity.CRITICAL,
                         message="Management's reported EBITDA is $25,000.00 below the GL.",
                         period_label="FY2025", amount="-25000.00"),
        DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING,
                         message="Premium bill posted twice.", month="2025-05", account="6200",
                         entry_ids=["GL-R2215", "GL-R2210"]),
    ]
    gl_ebitda = {}
    for p in LABELS:
        ni, i, t, d, am = GL_COMPONENTS[p]
        gl_ebitda[p] = EbitdaComponents(net_income=ni, interest=i, taxes=t, depreciation=d, amortization=am,
                                        ebitda=fmt(sum((D(x) for x in GL_COMPONENTS[p]), Decimal(0))))
    return ReconciliationResult(items=items, issues=issues, gl_ebitda=gl_ebitda,
                                mgmt_reported_ebitda={p: fmt(D(gl_ebitda[p].ebitda) + D(MGMT_DIFF[p])) for p in LABELS},
                                months_compared=30, accounts_compared=3,
                                variance_count=sum(1 for it in items if not it.within_tolerance))


def _meta() -> DealMeta:
    return DealMeta(
        deal_id="harborview_supply",
        target_name="Harborview Plumbing Supply, Inc.",
        industry="Plumbing distribution",
        periods=[PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
                 PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
                 PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06")],
        data_start="2024-01",
        data_end="2026-06",
        files=DealFiles(gl="gl/general_ledger.csv", chart_of_accounts="gl/chart_of_accounts.csv",
                        monthly_pl="financials/monthly_pl.xlsx", adjustments="adjustments/schedule.xlsx"),
    )


def make_workpaper(reviews: list[ReviewDecision] | None = None, diligence: bool = False) -> Workpaper:
    assessments = _assessments() + ([_diligence_item()] if diligence else [])
    reviews = _reviews() if reviews is None else reviews
    wp = Workpaper(
        run_id="run-test-001",
        tool_version="0.1.0",
        created_at="2026-09-28T12:00:00Z",
        ai_mode="rules",
        deal=_meta(),
        input_hashes={"gl/general_ledger.csv": "a" * 64, "documents/3.1 letter.pdf": "b" * 64},
        ingest_notes=["Detected GL format qbo_gl_csv."],
        reconciliation=_reconciliation(),
        doc_facts=[
            DocFacts(doc_id=RETAINER_LETTER, doc_type="engagement_letter", counterparty="Harrow Legal LLP",
                     doc_date="2023-03-01", is_signed=True,
                     terms=[TermFact(kind="retainer", text="$2,500 per month",
                                     quote=_q(RETAINER_LETTER, "a monthly retainer of $2,500 continuing until "
                                                               "terminated by either party"))]),
            DocFacts(doc_id=COMP_DRAFT, doc_type="contract", is_draft=True, is_signed=False, dropped_quotes=2,
                     extractor="rules"),
            DocFacts(doc_id=LIT_INVOICE, doc_type="invoice", counterparty="Harrow Legal LLP", doc_date="2025-02-10",
                     reference_numbers=["25-114", "7781"], service_period_start="2025-01-01",
                     service_period_end="2025-01-31"),
        ],
        assessments=assessments,
        reviews=reviews,
        bridge=EbitdaBridge(period_labels=LABELS, rows=[]),
    )
    final = _fallback_final_amounts(wp, latest_reviews(wp))
    return wp.model_copy(update={"bridge": _build_bridge(assessments, final)})


def make_package(wp: Workpaper) -> DealPackage:
    entries = [
        GLEntry(entry_id="GL-R1201", date="2025-02-14", period="2025-02", account="6400",
                account_name="Legal & Professional Fees", txn_type="Bill", doc_number="25-114",
                counterparty="Harrow Legal LLP", memo="Matter 7781 Pryor v. Harborview - Jan", amount="30000.00",
                source_file="gl/general_ledger.csv", source_row=1201),
        GLEntry(entry_id="GL-R880", date="2024-06-03", period="2024-06", account="6400",
                account_name="Legal & Professional Fees", counterparty="Harrow Legal LLP",
                memo="=General retainer - Jun", amount="2500.00", source_file="gl/general_ledger.csv", source_row=880),
    ]
    claims = [AdjustmentClaim(adj_id=a.adj_id, title=a.title, category_raw="Non-recurring",
                              category=a.category, description=f"Management narrative for {a.title}.",
                              gl_accounts=["6400"], support_refs=["DR 3.1", "DR 3.3"], amounts=dict(a.claimed),
                              source_row=10 + i) for i, a in enumerate(wp.assessments)]
    return DealPackage(
        deal_dir="data/dev/harborview_supply",
        meta=wp.deal,
        accounts={"6400": Account(number="6400", name="Legal & Professional Fees", source_type="Expense",
                                  ebitda_class=EbitdaClass.OPEX)},
        gl=entries,
        pl=ManagementPL(source_file="financials/monthly_pl.xlsx", months=[], lines=[]),
        schedule=ManagementSchedule(source_file="adjustments/schedule.xlsx", period_labels=LABELS, adjustments=claims),
        documents=[],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_row(ws, col: int, predicate) -> int:
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=col).value
        if v is not None and predicate(v):
            return r
    raise AssertionError(f"row not found in {ws.title} col {col}")


def _bridge_rows(ws) -> dict[str, int]:
    """Map bridge row labels to sheet rows (column B, indentation stripped)."""
    return {str(ws.cell(row=r, column=2).value).strip(): r for r in range(7, ws.max_row + 1)
            if ws.cell(row=r, column=2).value}


@pytest.fixture(scope="module")
def wp() -> Workpaper:
    return make_workpaper()


@pytest.fixture(scope="module")
def exported(wp, tmp_path_factory) -> Path:
    return export_workpaper(wp, tmp_path_factory.mktemp("xlsx"))


@pytest.fixture(scope="module")
def recalculated(exported, tmp_path_factory) -> tuple[Path, dict]:
    if find_recalc_script() is None or shutil.which("soffice") is None:
        pytest.skip("LibreOffice recalc not available")
    copy = tmp_path_factory.mktemp("recalc") / exported.name
    shutil.copy(exported, copy)
    return copy, recalc_and_check(copy, timeout=120)


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_filename_and_sheet_order(wp, exported):
    assert exported.name == "QoE_Evidence_Review_harborview_supply.xlsx" == workbook_filename(wp)
    wb = load_workbook(exported)
    assert wb.sheetnames == [
        "Cover", "EBITDA Bridge", "Adjustment Summary",
        "Adj A-1", "Adj A-2", "Adj A-3", "Adj A-4", "Adj A-5", "Adj A-6",
        "Open Questions", "GL-P&L Reconciliation", "Data Quality", "Review Log",
    ]
    assert all(len(n) <= 31 for n in wb.sheetnames)


def test_explicit_file_path(wp, tmp_path):
    out = export_workpaper(wp, tmp_path / "nested" / "custom.xlsx")
    assert out == tmp_path / "nested" / "custom.xlsx" and out.is_file()
    assert not list(out.parent.glob("*.partial.xlsx"))


def test_sanitize_sheet_name():
    used: set[str] = set()
    assert sanitize_sheet_name("Adj A/1:[x]*?", used) == "Adj A-1--x---"
    long = sanitize_sheet_name("Adj " + "Z" * 40, used)
    assert len(long) == 31
    dup = sanitize_sheet_name("Adj " + "z" * 40, used)
    assert len(dup) <= 31 and dup.endswith("(2)") and dup.lower() != long.lower()
    assert sanitize_sheet_name("history") == "History-"
    assert "'" not in sanitize_sheet_name("O'Brien bonus")


def test_support_sheet_names_are_unique():
    wp = make_workpaper()
    a = wp.assessments[0]
    twins = [a.model_copy(update={"adj_id": "1/2"}), a.model_copy(update={"adj_id": "1-2"})]
    names = support_sheet_names(wp.model_copy(update={"assessments": twins}))
    assert len({n.lower() for n in names.values()}) == 2


# ---------------------------------------------------------------------------
# Final amounts
# ---------------------------------------------------------------------------


def test_fallback_final_amounts_semantics(wp):
    latest = latest_reviews(wp)
    assert latest["A-3"].reviewer == "m.reyes"  # later log entry wins
    final = _fallback_final_amounts(wp, latest)
    assert final["A-3"] == _pm(0, "12000.25", 0)  # reviewer override
    assert final["A-2"] == _pm(0, 30000, 10000)  # reviewed
    assert final["A-1"] == _pm(0, 60000, "25000.50")  # unreviewed: tool proposal
    assert final["A-4"] == {}  # REQUEST_INFO: pending
    pending_review = ReviewDecision(adj_id="A-1", reviewer="r", timestamp="t", treatment=Treatment.REQUEST_INFO,
                                    amounts={}, rationale="", tool_treatment=Treatment.REVISE, tool_amounts={})
    assert _fallback_final_amounts(wp, {"A-1": pending_review})["A-1"] == {}
    # A REQUEST_INFO decision is pending even if amounts were recorded with it.
    stray = pending_review.model_copy(update={"amounts": _pm(1, 2, 3)})
    assert _fallback_final_amounts(wp, {"A-1": stray})["A-1"] == {}


def test_resolve_final_amounts_matches_fallback(wp):
    resolved = resolve_final_amounts(wp)
    fallback = _fallback_final_amounts(wp, latest_reviews(wp))
    for adj_id, amounts in fallback.items():
        expected = {p: fmt(amounts.get(p)) for p in LABELS} if amounts else {}
        assert resolved[adj_id] == expected, adj_id


# ---------------------------------------------------------------------------
# Formatting rules
# ---------------------------------------------------------------------------


def test_arial_everywhere_and_no_banned_functions(exported):
    wb = load_workbook(exported)
    formulas = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                assert cell.font.name == "Arial", (ws.title, cell.coordinate)
                if cell.data_type == "f":
                    formulas += 1
                    assert not BANNED.search(cell.value), (ws.title, cell.coordinate, cell.value)
                    # Every cross-sheet reference is quoted.
                    for m in re.finditer(r"('(?:[^']|'')+'|[A-Za-z0-9_.&\-]+)!", cell.value):
                        assert m.group(1).startswith("'"), cell.value
    assert formulas > 100
    assert wb._fonts[0].name == "Arial"  # default font for unstyled cells


def test_merged_ranges_never_overlap(wp):
    # Excel refuses to open ("repair" prompt) a sheet whose merged ranges overlap; LibreOffice does not care.
    wb = build_workbook(wp, pkg=make_package(wp))
    for ws in wb.worksheets:
        seen: set[tuple[int, int]] = set()
        for rng in ws.merged_cells.ranges:
            cells = {(r, c) for r in range(rng.min_row, rng.max_row + 1) for c in range(rng.min_col, rng.max_col + 1)}
            assert not cells & seen, (ws.title, str(rng))
            seen |= cells


def test_bridge_subtotals_are_formulas_and_rows_are_values(wp, exported):
    ws = load_workbook(exported)[SHEET_BRIDGE]
    rows = _bridge_rows(ws)
    by_key = {r.key: r for r in wp.bridge.rows}
    for key, bridge_row in by_key.items():
        r = rows[bridge_row.label]
        for k in range(3):
            cell = ws.cell(row=r, column=3 + k)
            if bridge_row.kind == "subtotal":
                assert cell.data_type == "f" and cell.value.startswith("="), (key, cell.value)
                assert cell.font.color.rgb.endswith("000000")
            else:
                assert isinstance(cell.value, (int, float)), (key, cell.value)
                assert D(cell.value) == D(bridge_row.amounts[LABELS[k]])
                assert cell.font.color.rgb.endswith("0000FF")
            assert cell.number_format == NUMBER_FORMAT
    gl = rows["Reported EBITDA (per GL)"]
    assert ws.cell(row=gl, column=3).value == f"=SUM(C{rows['Net income (per GL)']}:C{rows['Amortization']})"
    mgmt_rep = ws.cell(row=rows["Reported EBITDA (per management)"], column=4).value
    diff_row = rows["Difference to management's reported EBITDA"]
    assert mgmt_rep == f"=D{gl}+D{diff_row}"
    assert ws.freeze_panes == "C7"
    assert ws.cell(row=6, column=3).value == "FY2024\nUSD"


def test_treatment_fills_and_unreviewed_status(exported):
    ws = load_workbook(exported)[SHEET_SUMMARY]
    header = {ws.cell(row=6, column=c).value: c for c in range(1, ws.max_column + 1) if ws.cell(row=6, column=c).value}
    tool_col, status_col, rev_col = header["Tool treatment"], header["Status"], header["Reviewer treatment"]
    fills = {"ACCEPT": "C6EFCE", "REVISE": "FFEB9C", "REJECT": "FFC7CE", "REQUEST_INFO": "D6DCE4"}
    status = {}
    for r in range(8, 14):
        ref = ws.cell(row=r, column=1).value
        t = ws.cell(row=r, column=tool_col)
        assert t.fill.start_color.rgb.endswith(fills[t.value])
        status[ref] = ws.cell(row=r, column=status_col)
    assert {k: v.value for k, v in status.items()} == {
        "A-1": "UNREVIEWED", "A-2": "AGREED", "A-3": "OVERRIDDEN",
        "A-4": "UNREVIEWED", "A-5": "UNREVIEWED", "A-6": "UNREVIEWED",
    }
    assert status["A-1"].font.bold and status["A-1"].fill.start_color.rgb.endswith("FFFF00")
    assert ws.cell(row=10, column=rev_col).value == "REVISE"  # A-3 latest decision
    assert ws.cell(row=8, column=rev_col).value in (None, "")


def test_summary_links_and_difference_formulas(exported):
    ws = load_workbook(exported)[SHEET_SUMMARY]
    # A-1: claimed FY2025 links to the support sheet tie-out, green.
    claimed = ws.cell(row=8, column=5)
    assert claimed.value.startswith("='Adj A-1'!E") and claimed.font.color.rgb.endswith("008000")
    diff = ws.cell(row=8, column=4 + 9)  # first "Final less claimed" column
    assert diff.value == "=IF(ISNUMBER(J8),J8,0)-D8"
    total = _find_row(ws, 2, lambda v: v == "Total")
    assert ws.cell(row=total, column=4).value == "=SUM(D8:D13)"
    assert ws.freeze_panes == "D8"


def test_support_sheet_blocks(exported):
    ws = load_workbook(exported)["Adj A-1"]
    col_a = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
    text = [str(v) for v in col_a if v]
    facts = next(i for i, v in enumerate(text) if v.startswith("DOCUMENTED FACTS"))
    judgment = next(i for i, v in enumerate(text) if v.startswith("JUDGMENT QUESTIONS"))
    assert facts < judgment
    for heading in ("CONCLUSION", "MANAGEMENT'S CLAIM", "TIE-OUT BY PERIOD", "FLAGS (2)", "LINKED GL ENTRIES (5)",
                    "DOCUMENTS AND VERBATIM QUOTES (3)", "RECURRENCE OBSERVATIONS (1)", "REVIEWER DECISION"):
        assert any(v.startswith(heading) for v in text), heading
    values = [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]
    assert '"Total due: $30,000.00"' in values
    assert f"{LIT_INVOICE}, p. 2" in values
    assert "GL rows 1201, 1302" in values
    assert "UNREVIEWED" in values
    # Tie-out differences are formulas; inputs are blue values.
    tie = _find_row(ws, 1, lambda v: str(v).startswith("(a) Claimed"))
    assert ws.cell(row=tie, column=5).font.color.rgb.endswith("0000FF")
    diff = _find_row(ws, 1, lambda v: str(v).startswith("(a) - (b)"))
    assert ws.cell(row=diff, column=4).value == f"=D{tie}-D{tie + 1}"
    check = _find_row(ws, 1, lambda v: str(v).startswith("Check: EBITDA Bridge"))
    assert ws.cell(row=check, column=4).value.startswith("='EBITDA Bridge'!C")


def test_pending_item_and_decision_history(exported):
    wb = load_workbook(exported)
    ws = wb["Adj A-4"]
    proposed = _find_row(ws, 1, lambda v: str(v).startswith("(d) Tool proposed"))
    assert [ws.cell(row=proposed, column=4 + k).value for k in range(3)] == ["Pending"] * 3
    ws3 = wb["Adj A-3"]
    values = [str(c.value) for row in ws3.iter_rows() for c in row if c.value is not None]
    assert "Superseded" in values and "Current" in values
    log = wb["Review Log"]
    assert [log.cell(row=r, column=4).value for r in (8, 9, 10)] == ["A-3", "A-2", "A-3"]
    assert log.cell(row=8, column=log.max_column - 1).value == "Superseded"


def test_stale_review_is_flagged(tmp_path):
    stale = ReviewDecision(adj_id="A-1", reviewer="k.osei", timestamp="2026-08-01T09:00:00Z",
                           treatment=Treatment.ACCEPT, amounts=_pm(0, 90000, 50000), rationale="Looked fine.",
                           tool_treatment=Treatment.ACCEPT, tool_amounts=_pm(0, 90000, 50000))
    wb = build_workbook(make_workpaper(reviews=[stale]))
    log = wb["Review Log"]
    assert log.cell(row=8, column=log.max_column).value == "Yes: re-review"
    values = [str(c.value) for row in wb["Adj A-1"].iter_rows() for c in row if c.value is not None]
    assert any("tool proposal has changed since this decision" in v for v in values)
    summary = wb[SHEET_SUMMARY]
    status_col = next(c for c in range(1, summary.max_column + 1) if summary.cell(row=6, column=c).value == "Status")
    assert summary.cell(row=8, column=status_col).value == "AGREED"


def test_open_questions_apply_review_updates_and_keep_formula_like_text(exported):
    ws = load_workbook(exported)["Open Questions"]
    headers = [ws.cell(row=6, column=c).value for c in range(1, 8)]
    assert headers == ["Q id", "Ref", "Question", "Priority", "Basis", "Status", "Response"]
    rows = {ws.cell(row=r, column=1).value: r for r in range(7, ws.max_row + 1) if ws.cell(row=r, column=1).value}
    assert ws.cell(row=rows["Q-A-1-2"], column=6).value == "ANSWERED"
    assert ws.cell(row=rows["Q-A-1-2"], column=7).value == "insurer letter received"
    q = ws.cell(row=rows["Q-A-3-1"], column=3)
    assert q.data_type == "s" and q.value.startswith("=Provide")


def test_gl_detail_with_package(wp, tmp_path):
    out = export_workpaper(wp, tmp_path, pkg=make_package(wp))
    ws = load_workbook(out)["Adj A-1"]
    values = [c.value for row in ws.iter_rows() for c in row if c.value is not None]
    assert "6400 Legal & Professional Fees" in values
    assert "Management narrative for Litigation legal fees (Matter 7781)." in values
    assert "=General retainer - Jun" in values  # memo stays text, never a formula
    without = load_workbook(export_workpaper(wp, tmp_path / "plain"))["Adj A-1"]
    plain = [str(c.value) for row in without.iter_rows() for c in row if c.value is not None]
    assert any("without the source GL" in v for v in plain)


def test_cover_banner_and_legend(exported):
    ws = load_workbook(exported)[SHEET_COVER]
    banner = ws["A3"]
    assert banner.value.startswith("SYNTHETIC") and banner.font.bold
    values = [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]
    for t in ("ACCEPT", "REVISE", "REJECT", "REQUEST_INFO", "UNREVIEWED"):
        assert t in values
    assert any(v.startswith("Tickmark:") for v in values)
    assert "run-test-001" in values and "a" * 64 in values


# ---------------------------------------------------------------------------
# Bridge planning
# ---------------------------------------------------------------------------


def test_plan_subtotals_standard_bridge(wp):
    plans = _plan_subtotals(wp.bridge.rows, LABELS)
    assert all(ok for _, ok in plans.values())
    keys = [r.key for r in wp.bridge.rows]
    terms = {keys[i]: sorted(keys[j] for j, _ in t) for i, (t, _) in plans.items()}
    assert terms["mgmt_adjusted_ebitda"] == ["mgmt_reported_ebitda", "mgmt_total"]
    assert terms["diligence_adjusted_ebitda"] == ["dil_total", "mgmt_adjusted_ebitda"]
    assert "pending" not in terms


def test_plan_subtotals_handles_opposite_memo_sign(wp):
    rows = list(wp.bridge.rows)
    i = next(k for k, r in enumerate(rows) if r.key == "mgmt_recon_diff")
    rows[i] = rows[i].model_copy(update={"amounts": {p: fmt(-D(v)) for p, v in rows[i].amounts.items()}})
    plans = _plan_subtotals(rows, LABELS)
    j = next(k for k, r in enumerate(rows) if r.key == "mgmt_reported_ebitda")
    terms, ok = plans[j]
    assert ok and (i, -1) in terms


def test_bridge_that_does_not_foot_is_flagged(wp, tmp_path):
    rows = list(wp.bridge.rows)
    i = next(k for k, r in enumerate(rows) if r.key == "gl_ebitda")
    rows[i] = rows[i].model_copy(update={"amounts": {p: fmt(D(v) + 5) for p, v in rows[i].amounts.items()}})
    bad = wp.model_copy(update={"bridge": wp.bridge.model_copy(update={"rows": rows})})
    ws = build_workbook(bad)[SHEET_BRIDGE]
    values = [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]
    assert any(v.startswith("WARNING: a subtotal in red") for v in values)


def test_empty_workpaper_exports(wp, tmp_path):
    empty = wp.model_copy(update={
        "assessments": [], "reviews": [], "doc_facts": [],
        "bridge": EbitdaBridge(period_labels=LABELS, rows=[]),
        "reconciliation": wp.reconciliation.model_copy(update={"items": [], "issues": []}),
    })
    out = export_workpaper(empty, tmp_path)
    wb = load_workbook(out)
    assert wb.sheetnames[:3] == ["Cover", "EBITDA Bridge", "Adjustment Summary"]
    assert wb.sheetnames[3] == "Open Questions"


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.7) and assessment-carried narrative
# ---------------------------------------------------------------------------

D1_TITLE = "Reverse duplicate premium posting (KRI-25-0507)"


@pytest.fixture(scope="module")
def dwp() -> Workpaper:
    agree = ReviewDecision(adj_id="D-1", reviewer="k.osei", timestamp="2026-09-02T10:00:00Z",
                           treatment=Treatment.REVISE, amounts=_pm(0, 18400, 0), rationale="AP shows one payment.",
                           tool_treatment=Treatment.REVISE, tool_amounts=_pm(0, 18400, 0))
    return make_workpaper(reviews=[*_reviews(), agree], diligence=True)


@pytest.fixture(scope="module")
def dexported(dwp, tmp_path_factory) -> Path:
    return export_workpaper(dwp, tmp_path_factory.mktemp("dxlsx"))


def _values(ws) -> list[str]:
    return [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]


def _col_by_header(ws, title: str) -> int:
    return next(c for c in range(1, ws.max_column + 1) if ws.cell(row=6, column=c).value == title)


def test_diligence_item_sheet_and_summary_block(dexported):
    wb = load_workbook(dexported)
    assert wb.sheetnames[3:11] == ["Adj A-1", "Adj A-2", "Adj A-3", "Adj A-4", "Adj A-5", "Adj A-6", "Adj D-1",
                                   "Open Questions"]
    ws = wb[SHEET_SUMMARY]
    labels = {ws.cell(row=r, column=2).value: r for r in range(8, ws.max_row + 1) if ws.cell(row=r, column=2).value}
    mgmt_total, dil_total, total = (labels["Total management adjustments"], labels["Total diligence-identified items"],
                                    labels["Total"])
    d1 = _find_row(ws, 1, lambda v: v == "D-1")
    assert mgmt_total == 14 and ws.cell(row=mgmt_total, column=4).value == "=SUM(D8:D13)"
    assert mgmt_total < d1 < dil_total < total
    assert ws.cell(row=d1 - 1, column=1).value.startswith("Diligence-identified items (not on management's schedule)")
    assert ws.cell(row=d1, column=1).hyperlink.location == "'Adj D-1'!A1"
    assert ws.cell(row=dil_total, column=4).value == f"=SUM(D{d1}:D{d1})"
    assert ws.cell(row=total, column=4).value == f"=D{mgmt_total}+D{dil_total}"
    assert ws.cell(row=d1, column=_col_by_header(ws, "Status")).value == "AGREED"
    assert ws.cell(row=d1, column=_col_by_header(ws, "Tool treatment")).value == "REVISE"


def test_diligence_item_support_sheet_uses_assessment_fields(dexported):
    values = _values(load_workbook(dexported)["Adj D-1"])
    assert any(v.startswith("DILIGENCE-IDENTIFIED ITEMS (NOT ON MANAGEMENT'S SCHEDULE)") for v in values)
    assert "MANAGEMENT'S CLAIM" not in values
    assert "Premium installment KRI-25-0507 is posted twice in May 2025; the P&L carries both." in values
    assert "6200" in values and PREMIUM_NOTICE in values
    assert "(a) Claimed by management (not on the schedule: zero)" in values
    assert "Q-D-1-1" in values


def test_management_claim_falls_back_to_assessment_fields():
    wp = make_workpaper()
    a0 = wp.assessments[0].model_copy(update={"description": "Litigation narrative carried by the run.",
                                               "gl_accounts": ["6400"], "support_refs": ["DR 3.1", "DR 3.3"]})
    wp = wp.model_copy(update={"assessments": [a0, *wp.assessments[1:]]})
    values = _values(build_workbook(wp)["Adj A-1"])
    assert "Litigation narrative carried by the run." in values
    assert "6400" in values and "DR 3.1; DR 3.3" in values
    assert "Schedule row" not in values
    # Without a description anywhere, the sheet says where to look.
    values = _values(build_workbook(make_workpaper())["Adj A-2"])
    assert "Not carried in the workpaper; see management's adjusted EBITDA schedule." in values
    # A schedule stored on the workpaper is the source when present.
    sched = ManagementSchedule(source_file="adjustments/schedule.xlsx", period_labels=LABELS, adjustments=[
        AdjustmentClaim(adj_id="A-1", title=a0.title, description="From the schedule.", gl_accounts=["6410"],
                        amounts=dict(a0.claimed), source_row=12)])
    values = _values(build_workbook(wp.model_copy(update={"schedule": sched}))["Adj A-1"])
    assert "From the schedule." in values and "6410" in values and "Schedule row" in values


def test_bridge_shows_diligence_items_after_management_revisions(dwp, dexported):
    ws = load_workbook(dexported)[SHEET_BRIDGE]
    rows = _bridge_rows(ws)
    d1 = rows[f"Diligence-identified: {D1_TITLE}"]
    last_revision = max(rows[f"{a.title}: diligence revision"] for a in dwp.assessments if a.source != "diligence")
    assert last_revision < d1 < rows["Total diligence adjustments"]
    assert ws.cell(row=d1 - 1, column=1).value.startswith("Diligence-identified items")
    assert ws.cell(row=d1, column=1).value == "D-1"
    assert D(ws.cell(row=d1, column=4).value) == D("18400")
    assert ws.cell(row=d1, column=6).value == "REVISE" and ws.cell(row=d1, column=7).value == "AGREED"
    assert ws.cell(row=d1, column=8).value == "Adj D-1"
    assert not any(k.endswith("(as claimed)") and D1_TITLE in k for k in rows)
    total = ws.cell(row=rows["Total diligence adjustments"], column=3).value
    assert total.startswith("=SUM(C") and total.endswith(f":C{d1})")
    assert "Diligence-identified items less their total final amounts, Adjustment Summary" in rows


def test_bridge_display_rows_reorders_and_drops_zero_claims(dwp):
    rows = list(dwp.bridge.rows)
    # An older bridge: D-1 ahead of the management revisions, plus an all-zero "as claimed" row for it.
    d1 = next(r for r in rows if r.key == "dil:D-1")
    rows.remove(d1)
    rows.insert(next(k for k, r in enumerate(rows) if r.key == "dil:A-1"), d1)
    rows.insert(next(k for k, r in enumerate(rows) if r.key == "mgmt_total"),
                BridgeRow(key="mgmt:D-1", label="D-1 (as claimed)", kind="mgmt_adjustment", amounts=_pm(0, 0, 0)))
    out = bridge_display_rows(rows, {"D-1"})
    keys = [r.key for r in out]
    assert "mgmt:D-1" not in keys
    assert keys.index("dil:D-1") == keys.index("dil_total") - 1
    assert keys.index("dil:A-6") < keys.index("dil:D-1")
    assert all(ok for _, ok in _plan_subtotals(out, LABELS).values())
    # Without diligence items the order is untouched.
    assert bridge_display_rows(dwp.bridge.rows, set()) == list(dwp.bridge.rows)


def test_cover_counts_diligence_items_separately(dexported):
    ws = load_workbook(dexported)[SHEET_COVER]
    values = _values(ws)
    assert "ADJUSTMENT STATUS: MANAGEMENT ADJUSTMENTS" in values
    assert "DILIGENCE-IDENTIFIED ITEMS (NOT ON MANAGEMENT'S SCHEDULE)" in values
    assert "6 on management's schedule; 1 identified by diligence (not on the schedule)" in values
    assert any("2 of 6 management adjustments reviewed; 1 of 1 diligence-identified items reviewed" in v
               for v in values)
    # The diligence table counts the summary's diligence block (row 17), the management table rows 8-13.
    header = _find_row(ws, 1, lambda v: v == "DILIGENCE-IDENTIFIED ITEMS (NOT ON MANAGEMENT'S SCHEDULE)")
    revise = header + 3
    assert ws.cell(row=revise, column=1).value == "REVISE"
    assert ws.cell(row=revise, column=2).value == "=COUNTIF('Adjustment Summary'!$P$17:$P$17,\"REVISE\")"
    mgmt_revise = _find_row(ws, 1, lambda v: v == "REVISE")
    assert ws.cell(row=mgmt_revise, column=2).value == "=COUNTIF('Adjustment Summary'!$P$8:$P$13,\"REVISE\")"


@pytest.fixture(scope="module")
def drecalculated(dexported, tmp_path_factory) -> tuple[Path, dict]:
    if find_recalc_script() is None or shutil.which("soffice") is None:
        pytest.skip("LibreOffice recalc not available")
    copy = tmp_path_factory.mktemp("drecalc") / dexported.name
    shutil.copy(dexported, copy)
    return copy, recalc_and_check(copy, timeout=120)


def test_recalc_with_diligence_item_ties(dwp, drecalculated):
    path, result = drecalculated
    assert result.get("status") == "success", result
    assert result["total_errors"] == 0
    wb = load_workbook(path, data_only=True)
    ws = wb[SHEET_BRIDGE]
    rows = _bridge_rows(ws)
    for r in dwp.bridge.rows:
        for k, p in enumerate(LABELS):
            got = ws.cell(row=rows[r.label], column=3 + k).value
            assert abs(D(got) - D(r.amounts[p])) <= D("0.01"), (r.key, p, got)
    final = resolve_final_amounts(dwp)
    assert final["D-1"] == _pm(0, 18400, 0)
    for k, p in enumerate(LABELS):
        gl = D(ws.cell(row=rows["Reported EBITDA (per GL)"], column=3 + k).value)
        dil = D(ws.cell(row=rows["Diligence adjusted EBITDA"], column=3 + k).value)
        assert abs(dil - (gl + sum((D(v[p]) for v in final.values() if v), Decimal(0)))) <= D("0.01")
    checks = [r for r in range(1, ws.max_row + 1) if str(ws.cell(row=r, column=2).value or "").endswith(
        ("Adjustment Summary", "Adjustment Summary)"))]
    assert len(checks) == 3
    for r in checks:
        for k in range(3):
            assert abs(D(ws.cell(row=r, column=3 + k).value)) < D("0.01")
    cover = wb[SHEET_COVER]
    assert cover.cell(row=_find_row(cover, 1, lambda v: str(v).startswith("Workbook checks")), column=2).value == "OK"
    header = _find_row(cover, 1, lambda v: v == "DILIGENCE-IDENTIFIED ITEMS (NOT ON MANAGEMENT'S SCHEDULE)")
    counts = {cover.cell(row=r, column=1).value: tuple(cover.cell(row=r, column=c).value for c in (2, 3, 4))
              for r in range(header + 2, header + 6)}
    assert counts == {"ACCEPT": (0, 0, 0), "REVISE": (1, 1, 1), "REJECT": (0, 0, 0), "REQUEST_INFO": (0, 0, 0)}
    agreed = _find_row(cover, 1, lambda v: v == "Reviewed: agreed with tool")
    unreviewed = _find_row(cover, 1, lambda v: str(v).startswith("UNREVIEWED ("))
    assert (cover.cell(row=agreed, column=2).value, cover.cell(row=agreed, column=3).value) == (1, 1)
    assert (cover.cell(row=unreviewed, column=2).value, cover.cell(row=unreviewed, column=3).value) == (4, 0)
    summary = wb[SHEET_SUMMARY]
    total = _find_row(summary, 2, lambda v: v == "Total")
    fy25_final = 4 + 6 + 1
    assert D(summary.cell(row=total, column=fy25_final).value) == D("60000") + D("30000") + D("12000.25") - D(
        "30000") + D("18400")
    sws = wb["Adj D-1"]
    check = _find_row(sws, 1, lambda v: str(v).startswith("Check: EBITDA Bridge"))
    assert [abs(D(sws.cell(row=check, column=4 + k).value)) < D("0.01") for k in range(3)] == [True] * 3


# ---------------------------------------------------------------------------
# LibreOffice recalculation
# ---------------------------------------------------------------------------


def test_recalc_has_zero_errors(recalculated):
    _, result = recalculated
    assert result.get("status") == "success", result
    assert result["total_errors"] == 0
    assert result["total_formulas"] > 100


def test_recalculated_bridge_matches_workpaper(wp, recalculated):
    path, _ = recalculated
    ws = load_workbook(path, data_only=True)[SHEET_BRIDGE]
    rows = _bridge_rows(ws)
    for r in wp.bridge.rows:
        for k, p in enumerate(LABELS):
            got = ws.cell(row=rows[r.label], column=3 + k).value
            assert abs(D(got) - D(r.amounts[p])) <= D("0.01"), (r.key, p, got, r.amounts[p])
    # Identity: diligence adjusted = GL EBITDA + final amounts (pending excluded).
    final = resolve_final_amounts(wp)
    for k, p in enumerate(LABELS):
        gl = D(ws.cell(row=rows["Reported EBITDA (per GL)"], column=3 + k).value)
        dil = D(ws.cell(row=rows["Diligence adjusted EBITDA"], column=3 + k).value)
        expected = gl + sum((D(v[p]) for v in final.values() if v), Decimal(0))
        assert abs(dil - expected) <= D("0.01")
    checks = [r for r in range(1, ws.max_row + 1)
              if str(ws.cell(row=r, column=2).value or "").startswith(("Diligence adjusted EBITDA less",
                                                                        "Total management adjustments less"))]
    assert len(checks) == 2
    for r in checks:
        for k in range(3):
            assert abs(D(ws.cell(row=r, column=3 + k).value)) < D("0.01")


def test_recalculated_summary_cover_and_support_checks(wp, recalculated):
    path, _ = recalculated
    wb = load_workbook(path, data_only=True)
    ws = wb[SHEET_SUMMARY]
    total = _find_row(ws, 2, lambda v: v == "Total")
    # Final totals exclude pending A-4; Final less claimed reverses its claim.
    assert D(ws.cell(row=total, column=4 + 6 + 1).value) == D("60000") + D("30000") + D("12000.25") - D("30000")
    a4 = 11
    assert ws.cell(row=a4, column=4 + 6).value == "Pending"
    assert D(ws.cell(row=a4, column=4 + 9).value) == D("-250000")
    cover = wb[SHEET_COVER]
    counts = {}
    for r in range(1, cover.max_row + 1):
        label = cover.cell(row=r, column=1).value
        if label in ("ACCEPT", "REVISE", "REJECT", "REQUEST_INFO") and cover.cell(row=r, column=2).value is not None \
                and label not in counts:
            counts[label] = tuple(cover.cell(row=r, column=c).value for c in (2, 3, 4))
    assert counts == {"ACCEPT": (1, 1, 1), "REVISE": (2, 1, 3), "REJECT": (2, 0, 1), "REQUEST_INFO": (1, 0, 1)}
    unreviewed = _find_row(cover, 1, lambda v: str(v).startswith("UNREVIEWED ("))
    assert cover.cell(row=unreviewed, column=2).value == 4
    open_q = _find_row(cover, 1, lambda v: v == "Open questions for management")
    assert cover.cell(row=open_q, column=2).value == 3
    critical = _find_row(cover, 1, lambda v: v == "Data quality issues: critical")
    assert cover.cell(row=critical, column=2).value == 1
    checks = _find_row(cover, 1, lambda v: str(v).startswith("Workbook checks"))
    assert cover.cell(row=checks, column=2).value == "OK"
    for a in wp.assessments:
        sws = wb[f"Adj {a.adj_id}"]
        check = _find_row(sws, 1, lambda v: str(v).startswith("Check: EBITDA Bridge"))
        for k in range(3):
            assert abs(D(sws.cell(row=check, column=4 + k).value)) < D("0.01"), a.adj_id


def test_recalculated_reconciliation_summary(wp, recalculated):
    path, _ = recalculated
    ws = load_workbook(path, data_only=True)["GL-P&L Reconciliation"]
    first = _find_row(ws, 1, lambda v: v == "Month") + 1
    items = wp.reconciliation.items
    months = sorted({it.month for it in items})
    for i, m in enumerate(months):
        r = first + i
        gl = sum((D(it.gl_amount) for it in items if it.month == m), Decimal(0))
        pl = sum((D(it.pl_amount) for it in items if it.month == m), Decimal(0))
        assert abs(D(ws.cell(row=r, column=2).value) - gl) <= D("0.01"), m
        assert abs(D(ws.cell(row=r, column=4).value) - (pl - gl)) <= D("0.01"), m
        assert ws.cell(row=r, column=5).value == (1 if m == "2025-12" else 0), m


def test_recalculated_checks_catch_a_stale_bridge(wp, tmp_path):
    """A decision logged after the bridge was built must trip the workbook checks, not pass silently."""
    if find_recalc_script() is None or shutil.which("soffice") is None:
        pytest.skip("LibreOffice recalc not available")
    late = ReviewDecision(adj_id="A-1", reviewer="m.reyes", timestamp="2026-09-03T08:00:00Z",
                          treatment=Treatment.REVISE, amounts=_pm(0, 70000, "25000.50"), rationale="Added a fee.",
                          tool_treatment=Treatment.REVISE, tool_amounts=_pm(0, 60000, "25000.50"),
                          correction_type=CorrectionType.TOOL_MISSED_EVIDENCE)
    stale = wp.model_copy(update={"reviews": [*wp.reviews, late]})  # bridge not rebuilt
    out = export_workpaper(stale, tmp_path)
    result = recalc_and_check(out, timeout=120)
    assert result.get("status") == "success" and result["total_errors"] == 0, result
    wb = load_workbook(out, data_only=True)
    cover = wb[SHEET_COVER]
    checks = _find_row(cover, 1, lambda v: str(v).startswith("Workbook checks"))
    assert cover.cell(row=checks, column=2).value.startswith("DIFFERENCE")
    bridge = wb[SHEET_BRIDGE]
    row = _find_row(bridge, 2, lambda v: str(v).startswith("Diligence adjusted EBITDA less"))
    assert abs(D(bridge.cell(row=row, column=4).value) + D("10000")) < D("0.01")


def test_integration_dev_deal_exports_and_ties(tmp_path):
    """End to end on the reference dev deal (other data/dev packages may be mid-authoring)."""
    engine = pytest.importorskip("qoe.engine")
    ingest = pytest.importorskip("qoe.ingest")
    deal_dir = ROOT / "data" / "dev" / "meridian_mechanical"
    if not (deal_dir / "deal.yaml").is_file():
        pytest.skip("no generated dev deal at data/dev/meridian_mechanical")
    wp = engine.run_review(deal_dir, run_id="export-test", created_at="2026-01-01T00:00:00Z")
    out = export_workpaper(wp, tmp_path, pkg=ingest.load_deal(deal_dir))
    result = recalc_and_check(out, timeout=180)
    if result.get("status") == "skipped":
        return
    assert result.get("status") == "success" and result["total_errors"] == 0, result
    ws = load_workbook(out, data_only=True)[SHEET_BRIDGE]
    rows = _bridge_rows(ws)
    labels = wp.bridge.period_labels
    for r in wp.bridge.rows:
        if r.kind != "subtotal":
            continue
        for k, p in enumerate(labels):
            got = ws.cell(row=rows[r.label], column=3 + k).value
            assert abs(D(got) - D(r.amounts.get(p))) <= D("0.01"), (r.key, p, got)
