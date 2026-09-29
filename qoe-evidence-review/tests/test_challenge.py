"""Tests for qoe.challenge: every §5.4 challenge on an in-memory deal, through to treatment.

The deal is synthetic and unrelated to the dev deal catalog: one adjustment per
case type, surrounded by recurring background activity so linking and fitting
have noise to work through.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from qoe.ai_base import AdjustmentIntent, Contradiction, EntryClassification
from decimal import Decimal

from qoe.challenge import ChallengeContext, _term_end_month, _term_fee, resolve_overlaps, run_challenges
from qoe.money import D, fmt
from qoe.periods import month_range
from qoe.propose import compute_proposed, flag_effects, propose
from qoe.schemas import (
    Account,
    AdjustmentCategory,
    AdjustmentClaim,
    AmountFact,
    DataQualityCode,
    DataQualityIssue,
    DealFiles,
    DealMeta,
    DealPackage,
    DocFacts,
    DocumentPage,
    EbitdaClass,
    EvidenceQuote,
    FlagCode,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PeriodDef,
    ReconciliationResult,
    Severity,
    SourceDocument,
    TermFact,
    Treatment,
)
from qoe.trace import build_index, trace_adjustment

# ---------------------------------------------------------------------------
# In-memory fixture kit
# ---------------------------------------------------------------------------

PERIODS = [
    PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
    PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
    PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06"),
]
LABELS = [p.label for p in PERIODS]
FY24, FY25, TTM = LABELS
ACCOUNTS = {
    n: Account(number=n, name=name, source_type=typ, ebitda_class=cls)
    for n, name, typ, cls in [
        ("4000", "Service Revenue", "Income", EbitdaClass.REVENUE),
        ("5200", "Subcontractors", "Cost of Goods Sold", EbitdaClass.COGS),
        ("6000", "Salaries & Wages", "Expense", EbitdaClass.OPEX),
        ("6010", "Officer Compensation", "Expense", EbitdaClass.OPEX),
        ("6100", "Rent & Occupancy", "Expense", EbitdaClass.OPEX),
        ("6150", "Repairs & Maintenance", "Expense", EbitdaClass.OPEX),
        ("6300", "Software & IT", "Expense", EbitdaClass.OPEX),
        ("6400", "Legal Fees", "Expense", EbitdaClass.OPEX),
        ("6450", "Recruiting", "Expense", EbitdaClass.OPEX),
        ("6600", "Travel", "Expense", EbitdaClass.OPEX),
        ("6700", "Dues & Subscriptions", "Expense", EbitdaClass.OPEX),
        ("6950", "Bad Debt Expense", "Expense", EbitdaClass.OPEX),
        ("5300", "Inventory Write-offs", "Cost of Goods Sold", EbitdaClass.COGS),
        ("6420", "Consulting Fees", "Expense", EbitdaClass.OPEX),
        ("8000", "Other Income", "Other Income", EbitdaClass.OTHER_INCOME),
        ("8100", "Interest Expense", "Other Expense", EbitdaClass.INTEREST),
    ]
}


class GL:
    def __init__(self) -> None:
        self.rows: list[GLEntry] = []

    def add(self, date: str, account: str, amount: object, cp: str = "", memo: str = "", num: str = "") -> str:
        row = len(self.rows) + 6
        self.rows.append(
            GLEntry(
                entry_id=f"GL-R{row}",
                date=date,
                period=date[:7],
                account=account,
                account_name=ACCOUNTS[account].name,
                txn_type="Bill",
                doc_number=num,
                counterparty=cp,
                memo=memo,
                amount=fmt(amount),
                source_file="gl/general_ledger.csv",
                source_row=row,
            )
        )
        return f"GL-R{row}"

    def monthly(self, start: str, end: str, account: str, amount: object, cp: str, memo: str) -> list[str]:
        return [self.add(f"{m}-15", account, amount, cp, f"{memo} - {m}") for m in month_range(start, end)]


def q(doc_id: str, text: str) -> EvidenceQuote:
    return EvidenceQuote(doc_id=doc_id, page=1, quote=text)


def claim(adj_id: str, title: str, amounts: Iterable[object], accounts: Iterable[str] = (), refs: Iterable[str] = (),
          category: AdjustmentCategory = AdjustmentCategory.NON_RECURRING) -> AdjustmentClaim:
    return AdjustmentClaim(
        adj_id=adj_id,
        title=title,
        category=category,
        gl_accounts=list(accounts),
        support_refs=list(refs),
        amounts={lbl: fmt(a) for lbl, a in zip(LABELS, amounts)},
        source_row=10,
    )


def package(gl: GL, adjustments: list[AdjustmentClaim], texts: dict[str, str]) -> DealPackage:
    meta = DealMeta(
        deal_id="challenge_deal",
        target_name="Harbor Unit Co (SYNTHETIC)",
        periods=PERIODS,
        data_start="2024-01",
        data_end="2026-06",
        files=DealFiles(gl="gl.csv", chart_of_accounts="coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
    )
    docs = [
        SourceDocument(doc_id=k, relpath=f"documents/{k}", media_type="txt", sha256="0" * 64, pages=[DocumentPage(page=1, text=v)])
        for k, v in texts.items()
    ]
    return DealPackage(
        deal_dir="(memory)",
        meta=meta,
        accounts=ACCOUNTS,
        gl=gl.rows,
        pl=ManagementPL(source_file="pl.xlsx", months=[], lines=[]),
        schedule=ManagementSchedule(source_file="adj.xlsx", period_labels=LABELS, adjustments=adjustments),
        documents=docs,
    )


def recon(issues: Iterable[DataQualityIssue] = ()) -> ReconciliationResult:
    return ReconciliationResult(
        items=[], issues=list(issues), gl_ebitda={}, mgmt_reported_ebitda={}, months_compared=0, accounts_compared=0, variance_count=0
    )


class FakeAI:
    """EvidenceAI with canned outputs; anything not configured is empty."""

    name = "fake"

    def __init__(self, facts=None, intents=None, contradictions=None, classifications=None, questions=None):
        self.facts: dict[str, DocFacts] = facts or {}
        self.intents: dict[str, AdjustmentIntent] = intents or {}
        self.contradictions: dict[str, list[Contradiction]] = contradictions or {}
        self.classifications: dict[str, list[EntryClassification]] = classifications or {}
        self.questions: dict[str, list[str]] = questions or {}

    def extract_facts(self, doc):
        return self.facts.get(doc.doc_id) or DocFacts(doc_id=doc.doc_id, doc_type="other")

    def parse_intent(self, adj):
        return self.intents.get(adj.adj_id) or AdjustmentIntent(adj_id=adj.adj_id)

    def find_contradictions(self, adj, intent, facts, entries):
        return list(self.contradictions.get(adj.adj_id, []))

    def classify_entries(self, adj, intent, entries, facts):
        return list(self.classifications.get(adj.adj_id, []))

    def draft_questions(self, adj, flags, facts):
        return list(self.questions.get(adj.adj_id, []))


def run(pkg: DealPackage, ai: FakeAI, issues: Iterable[DataQualityIssue] = ()):
    facts = [ai.extract_facts(d) for d in pkg.documents]
    index = build_index(pkg, facts, recon(issues))
    traces = [trace_adjustment(index, adj, ai.parse_intent(adj), order=i) for i, adj in enumerate(pkg.schedule.adjustments)]
    resolve_overlaps(traces)
    ctx = ChallengeContext.build(ai, traces)
    for t in traces:
        run_challenges(t, ctx)
    return {t.adj.adj_id: (t, propose(t, ai)) for t in traces}


def amounts(*values: object) -> dict[str, str]:
    return {lbl: fmt(v) for lbl, v in zip(LABELS, values)}


def codes(assessment) -> set[FlagCode]:
    return {f.code for f in assessment.flags}


def the_flag(assessment, code: FlagCode):
    found = [f for f in assessment.flags if f.code == code]
    assert found, f"{code} not raised on {assessment.adj_id}: {[f.code for f in assessment.flags]}"
    return found[0]


# ---------------------------------------------------------------------------
# The deal: one adjustment per case type
# ---------------------------------------------------------------------------


def build_deal():
    gl = GL()
    ids: dict[str, list[str]] = {}
    # Background activity the linker has to ignore.
    gl.monthly("2024-01", "2026-06", "4000", -250000, "Various customers", "Service revenue")
    gl.monthly("2024-01", "2026-06", "6000", 40000, "", "Payroll - office staff")
    ids["dispatch"] = gl.monthly("2024-01", "2026-06", "6000", 5000, "", "Payroll - dispatch team")
    gl.monthly("2024-01", "2026-06", "6100", 9000, "Bayfront Properties", "Warehouse rent")
    gl.monthly("2024-01", "2026-06", "6150", 600, "Coastal HVAC Service", "Filter service")
    gl.monthly("2024-01", "2026-06", "6450", 900, "Jobly", "Job board postings")
    gl.monthly("2024-01", "2026-06", "6600", 700, "Skyway Travel", "Travel - technician training")
    ids["officer"] = gl.monthly("2024-01", "2026-06", "6010", 25000, "J. Varga", "Officer payroll - J. Varga")
    ids["interest"] = gl.monthly("2024-01", "2026-06", "8100", 2000, "Bayline Bank", "Interest - Bayline Bank term loan")
    ids["ridgeway"] = gl.monthly("2024-01", "2026-06", "5200", 5000, "Ridgeway Ductwork LLC", "Ductwork subcontract work")

    # A-01 adequate support: executive search fee in three installments.
    ids["search"] = [
        gl.add("2025-04-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 1", "PS-101"),
        gl.add("2025-05-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 2", "PS-102"),
        gl.add("2025-08-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 3", "PS-103"),
    ]
    # A-02 litigation fees mixed with a general-corporate matter that recurs.
    ids["lit"] = [
        gl.add("2025-03-10", "6400", 12000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-7710-03"),
        gl.add("2025-06-10", "6400", 14000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-7710-06"),
        gl.add("2025-09-10", "6400", 8000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-7710-09"),
    ]
    ids["retainer"] = gl.monthly("2024-01", "2026-06", "6400", 1000, "Marlow & Finch LLP", "Matter 3002 general corporate retainer")
    ids["adhoc"] = [gl.add("2025-08-20", "6400", 4000, "Marlow & Finch LLP", "Matter 3002 employment policy review", "MF-3002-AH")]
    # A-03 owner personal expenses; two trips have a documented business purpose.
    ids["dues"] = gl.monthly("2025-01", "2026-06", "6700", 500, "Harbor Point Yacht Club", "Club dues - J. Varga")
    ids["expo"] = [gl.add("2025-02-20", "6600", 4000, "Skyway Travel", "Travel - J. Varga - AHR Expo")]
    ids["vacation"] = [gl.add("2025-07-10", "6600", 8000, "Skyway Travel", "Travel - J. Varga - family vacation", "SV-8")]
    ids["supplier"] = [gl.add("2025-10-05", "6600", 4000, "Skyway Travel", "Travel - J. Varga - supplier plant visit")]
    # A-04 transaction costs; management also included litigation invoice MF-7710-09 (already in A-02).
    ids["keystone"] = [gl.add("2025-10-12", "6400", 22000, "Keystone Advisors", "Sell-side advisory retainer", "KA-1")]
    # A-05 refinancing costs booked to interest expense.
    ids["refi"] = [
        gl.add("2025-06-30", "8100", 6000, "Bayline Bank", "Write-off unamortized loan fees - Bayline Bank", "JE-601"),
        gl.add("2025-06-30", "8100", 3000, "Bayline Bank", "Prepayment penalty - Bayline Bank", "JE-602"),
    ]
    # A-06 a "one-time" implementation that is a monthly subscription.
    ids["nimbus"] = gl.monthly("2025-01", "2026-06", "6300", 3000, "Nimbus Cloud Systems", "ERP managed services")
    # A-07 flood repairs with an unadjusted insurance recovery.
    ids["flood"] = [
        gl.add("2024-09-20", "6150", 15000, "Gulfline Roofing", "Flood damage - roof replacement", "GR-88"),
        gl.add("2024-10-12", "6150", 10000, "Tidewater Restoration", "Flood damage - water extraction", "TR-12"),
    ]
    ids["insurance"] = [gl.add("2025-03-05", "8000", -12000, "Anchor Mutual Insurance", "Insurance proceeds - flood claim AM-2291-X")]
    # A-08 prior-year subcontractor true-up booked in 2025.
    ids["trueup"] = [gl.add("2025-03-18", "5200", 18000, "Ridgeway Ductwork LLC", "Project closeout true-up - 2024 projects", "RD-5501")]
    # A-09 relocation costs all in Feb-Mar 2025, claimed in TTM as well.
    ids["relocation"] = [
        gl.add("2025-02-10", "6100", 12000, "Swift Movers", "Office relocation - moving services", "SM-7"),
        gl.add("2025-03-22", "6150", 8000, "Keel Build-Out", "Office relocation - build-out", "KB-3"),
    ]

    adjustments = [
        claim("A-01", "Executive search fee", [0, 30000, 10000], ["6450"], ["DR 1"]),
        claim("A-02", "Reyes litigation legal fees", [0, 50000, 24000], ["6400"], ["DR 2"]),
        claim("A-03", "Owner personal expenses", [0, 22000, 18000], ["6600", "6700"], ["DR 3"], AdjustmentCategory.OWNER_DISCRETIONARY),
        claim("A-04", "Transaction costs", [0, 30000, 30000], ["6400"], ["DR 4"]),
        claim("A-05", "Refinancing costs", [0, 9000, 0], ["8100"]),
        claim("A-06", "ERP implementation (one-time)", [0, 36000, 18000], ["6300"], ["DR 6"]),
        claim("A-07", "Flood damage repairs", [25000, 0, 0], ["6150"], ["DR 7"]),
        claim("A-08", "Prior-year subcontractor true-up", [0, 18000, 0], ["5200"], ["DR 8"], AdjustmentCategory.OUT_OF_PERIOD),
        claim("A-09", "Office relocation", [0, 20000, 20000], ["6100", "6150"], ["DR 9"]),
        claim("A-10", "Pro forma dispatch savings", [0, 0, 60000], [], ["DR 10"], AdjustmentCategory.PRO_FORMA),
        claim("A-11", "Owner compensation normalization", [100000, 100000, 100000], ["6010"], ["DR 11"], AdjustmentCategory.NORMALIZATION),
    ]

    texts = {
        "1.1 Pinecrest engagement letter.txt": "Retained search. Fee of $30,000 payable in three installments of $10,000.",
        "1.2 Pinecrest invoice PS-101.txt": "Invoice PS-101. Total due $10,000.00",
        "1.3 Pinecrest invoice PS-102.txt": "Invoice PS-102. Total due $10,000.00",
        "1.4 Pinecrest invoice PS-103.txt": "Invoice PS-103. Total due $10,000.00",
        "2.1 Marlow Finch litigation engagement.txt": "Engagement for Matter 7710, Reyes v. Harbor. Fees billed hourly.",
        "2.2 Marlow Finch general engagement 2023.txt": "Matter 3002. Retainer of $1,000 per month, continuing until terminated by either party.",
        "2.3 Marlow Finch invoice MF-7710-09.txt": "Invoice MF-7710-09 for Matter 7710. Total due $8,000.00",
        "4.1 Keystone engagement letter.txt": "Keystone Advisors sell-side engagement. Retainer of $22,000 due on signing.",
        "3.1 AHR Expo registration.txt": "Registration confirmed for Harbor Unit Co. Attendee: J. Varga. Purpose: HVAC product training.",
        "3.2 Supplier visit agenda.txt": "Supplier plant visit agenda for Harbor Unit Co purchasing review.",
        "3.3 Harbor Point Yacht Club statement.txt": "Member: J. Varga (individual). Monthly dues $500.00.",
        "3.6 Skyway Travel invoice SV-8.txt": "Invoice SV-8. Family vacation package for J. Varga. Total due $8,000.00",
        "6.1 Nimbus managed services agreement.txt": (
            "Managed Services Agreement with Nimbus Cloud Systems. Monthly fee of $3,000 per month. "
            "This agreement renews automatically for successive terms."
        ),
        "6.2 Controller email.txt": "From: Controller\nSubject: ERP\nOur Nimbus subscription renews next month.",
        "7.1 Gulfline invoice GR-88.txt": "Invoice GR-88. Flood damage roof replacement. Total due $15,000.00",
        "7.2 Tidewater invoice TR-12.txt": "Invoice TR-12. Water extraction. Total due $10,000.00",
        "7.3 Anchor Mutual claim letter.txt": "Claim AM-2291-X. Net payment of $12,000.00 after deductible.",
        "8.1 Ridgeway invoice RD-5501.txt": (
            "Invoice RD-5501. Service period: July 1, 2024 - December 31, 2024. Amount due $18,000.00"
        ),
        "9.1 Swift Movers invoice SM-7.txt": "Invoice SM-7. Office move. Total due $12,000.00",
        "9.2 Keel invoice KB-3.txt": "Invoice KB-3. Office build-out. Total due $8,000.00",
        "10.1 COO email.txt": "We plan to reduce the dispatch team by two FTEs once auto-dispatch is live - targeting Q3 2026.",
        "11.1 Draft employment agreement.txt": "DRAFT - Employment Agreement. Base salary of $200,000 per year.",
    }

    def invoice(doc_id: str, cp: str, ref: str, amount: str) -> DocFacts:
        return DocFacts(
            doc_id=doc_id,
            doc_type="invoice",
            counterparty=cp,
            reference_numbers=[ref],
            amounts=[AmountFact(label="total_due", amount=amount, quote=q(doc_id, texts[doc_id].split(". ")[-1]))],
        )

    facts = {
        "1.1 Pinecrest engagement letter.txt": DocFacts(
            doc_id="1.1 Pinecrest engagement letter.txt",
            doc_type="engagement_letter",
            counterparty="Pinecrest Search Partners",
            is_signed=True,
            amounts=[AmountFact(label="total_fee", amount="30000", quote=q("1.1 Pinecrest engagement letter.txt", "Fee of $30,000"))],
            # Worded like a monthly fee but finite: must not read as a continuing obligation.
            terms=[TermFact(kind="monthly_fee", text="$10,000 in three installments",
                            quote=q("1.1 Pinecrest engagement letter.txt", "payable in three installments of $10,000"))],
        ),
        "1.2 Pinecrest invoice PS-101.txt": invoice("1.2 Pinecrest invoice PS-101.txt", "Pinecrest Search Partners", "PS-101", "10000"),
        "1.3 Pinecrest invoice PS-102.txt": invoice("1.3 Pinecrest invoice PS-102.txt", "Pinecrest Search Partners", "PS-102", "10000"),
        "1.4 Pinecrest invoice PS-103.txt": invoice("1.4 Pinecrest invoice PS-103.txt", "Pinecrest Search Partners", "PS-103", "10000"),
        "2.1 Marlow Finch litigation engagement.txt": DocFacts(
            doc_id="2.1 Marlow Finch litigation engagement.txt",
            doc_type="engagement_letter",
            counterparty="Marlow & Finch LLP",
            reference_numbers=["Matter 7710"],
            is_signed=True,
            # A retainer term without periodic language must not cover the litigation matter.
            terms=[TermFact(kind="retainer", text="fees billed hourly",
                            quote=q("2.1 Marlow Finch litigation engagement.txt", "Fees billed hourly."))],
        ),
        "2.2 Marlow Finch general engagement 2023.txt": DocFacts(
            doc_id="2.2 Marlow Finch general engagement 2023.txt",
            doc_type="engagement_letter",
            counterparty="Marlow & Finch LLP",
            reference_numbers=["Matter 3002"],
            is_signed=True,
            terms=[TermFact(kind="retainer", text="$1,000 per month until terminated",
                            quote=q("2.2 Marlow Finch general engagement 2023.txt",
                                    "Retainer of $1,000 per month, continuing until terminated by either party."))],
        ),
        "2.3 Marlow Finch invoice MF-7710-09.txt": DocFacts(
            doc_id="2.3 Marlow Finch invoice MF-7710-09.txt",
            doc_type="invoice",
            counterparty="Marlow & Finch LLP",
            reference_numbers=["MF-7710-09", "Matter 7710"],
            amounts=[AmountFact(label="total_due", amount="8000", quote=q("2.3 Marlow Finch invoice MF-7710-09.txt", "Total due $8,000.00"))],
        ),
        "4.1 Keystone engagement letter.txt": DocFacts(
            doc_id="4.1 Keystone engagement letter.txt",
            doc_type="engagement_letter",
            counterparty="Keystone Advisors",
            is_signed=True,
            amounts=[AmountFact(label="retainer", amount="22000", quote=q("4.1 Keystone engagement letter.txt", "Retainer of $22,000 due on signing."))],
        ),
        "3.1 AHR Expo registration.txt": DocFacts(
            doc_id="3.1 AHR Expo registration.txt",
            doc_type="correspondence",
            key_statements=[q("3.1 AHR Expo registration.txt", "Registration confirmed for Harbor Unit Co.")],
        ),
        "3.2 Supplier visit agenda.txt": DocFacts(
            doc_id="3.2 Supplier visit agenda.txt",
            doc_type="memo",
            key_statements=[q("3.2 Supplier visit agenda.txt", "Supplier plant visit agenda for Harbor Unit Co purchasing review.")],
        ),
        "3.3 Harbor Point Yacht Club statement.txt": DocFacts(
            doc_id="3.3 Harbor Point Yacht Club statement.txt",
            doc_type="other",
            counterparty="Harbor Point Yacht Club",
            amounts=[AmountFact(label="monthly_fee", amount="500",
                                quote=q("3.3 Harbor Point Yacht Club statement.txt", "Monthly dues $500.00."))],
        ),
        "3.6 Skyway Travel invoice SV-8.txt": invoice("3.6 Skyway Travel invoice SV-8.txt", "Skyway Travel", "SV-8", "8000"),
        "6.1 Nimbus managed services agreement.txt": DocFacts(
            doc_id="6.1 Nimbus managed services agreement.txt",
            doc_type="contract",
            counterparty="Nimbus Cloud Systems",
            is_signed=True,
            amounts=[AmountFact(label="monthly_fee", amount="3000", quote=q("6.1 Nimbus managed services agreement.txt", "Monthly fee of $3,000 per month."))],
            terms=[
                TermFact(kind="monthly_fee", text="$3,000 per month",
                         quote=q("6.1 Nimbus managed services agreement.txt", "Monthly fee of $3,000 per month.")),
                TermFact(kind="auto_renew", text="renews automatically",
                         quote=q("6.1 Nimbus managed services agreement.txt", "This agreement renews automatically for successive terms.")),
            ],
        ),
        "6.2 Controller email.txt": DocFacts(
            doc_id="6.2 Controller email.txt",
            doc_type="correspondence",
            key_statements=[q("6.2 Controller email.txt", "Our Nimbus subscription renews next month.")],
        ),
        "7.1 Gulfline invoice GR-88.txt": invoice("7.1 Gulfline invoice GR-88.txt", "Gulfline Roofing", "GR-88", "15000"),
        "7.2 Tidewater invoice TR-12.txt": invoice("7.2 Tidewater invoice TR-12.txt", "Tidewater Restoration", "TR-12", "10000"),
        "7.3 Anchor Mutual claim letter.txt": DocFacts(
            doc_id="7.3 Anchor Mutual claim letter.txt",
            doc_type="insurance",
            counterparty="Anchor Mutual Insurance",
            reference_numbers=["AM-2291-X"],
            amounts=[AmountFact(label="net_payment", amount="12000", quote=q("7.3 Anchor Mutual claim letter.txt", "Net payment of $12,000.00"))],
        ),
        "8.1 Ridgeway invoice RD-5501.txt": DocFacts(
            doc_id="8.1 Ridgeway invoice RD-5501.txt",
            doc_type="invoice",
            counterparty="Ridgeway Ductwork LLC",
            reference_numbers=["RD-5501"],
            service_period_start="2024-07-01",
            service_period_end="2024-12-31",
            amounts=[AmountFact(label="total_due", amount="18000", quote=q("8.1 Ridgeway invoice RD-5501.txt", "Amount due $18,000.00"))],
            key_statements=[q("8.1 Ridgeway invoice RD-5501.txt", "Service period: July 1, 2024 - December 31, 2024.")],
        ),
        "9.1 Swift Movers invoice SM-7.txt": invoice("9.1 Swift Movers invoice SM-7.txt", "Swift Movers", "SM-7", "12000"),
        "9.2 Keel invoice KB-3.txt": invoice("9.2 Keel invoice KB-3.txt", "Keel Build-Out", "KB-3", "8000"),
        "10.1 COO email.txt": DocFacts(
            doc_id="10.1 COO email.txt",
            doc_type="correspondence",
            key_statements=[q("10.1 COO email.txt", "We plan to reduce the dispatch team by two FTEs")],
        ),
        "11.1 Draft employment agreement.txt": DocFacts(
            doc_id="11.1 Draft employment agreement.txt",
            doc_type="contract",
            counterparty="J. Varga",
            is_draft=True,
            is_signed=False,
            amounts=[AmountFact(label="base_salary", amount="200000", quote=q("11.1 Draft employment agreement.txt", "Base salary of $200,000 per year."))],
            key_statements=[q("11.1 Draft employment agreement.txt", "DRAFT - Employment Agreement.")],
        ),
    }
    intents = {
        "A-01": AdjustmentIntent(adj_id="A-01", counterparties=["Pinecrest Search"], keywords=["search"], asserts_nonrecurring=True),
        "A-02": AdjustmentIntent(adj_id="A-02", counterparties=["Marlow & Finch"], keywords=["litigation", "reyes"],
                                 reference_numbers=["7710"], asserts_nonrecurring=True),
        "A-03": AdjustmentIntent(adj_id="A-03", counterparties=["Harbor Point Yacht Club", "J. Varga"], asserts_personal=True),
        "A-04": AdjustmentIntent(adj_id="A-04", counterparties=["Keystone Advisors"], keywords=["sell-side"],
                                 reference_numbers=["MF-7710-09"], asserts_nonrecurring=True),
        "A-05": AdjustmentIntent(adj_id="A-05", counterparties=["Bayline Bank"], keywords=["prepayment", "loan fees"], asserts_nonrecurring=True),
        "A-06": AdjustmentIntent(adj_id="A-06", counterparties=["Nimbus Cloud Systems"], keywords=["implementation"], asserts_nonrecurring=True),
        "A-07": AdjustmentIntent(adj_id="A-07", counterparties=["Gulfline Roofing", "Tidewater Restoration"], keywords=["flood"],
                                 asserts_nonrecurring=True),
        "A-08": AdjustmentIntent(adj_id="A-08", counterparties=["Ridgeway Ductwork"], keywords=["true-up"]),
        "A-09": AdjustmentIntent(adj_id="A-09", counterparties=["Swift Movers", "Keel Build-Out"], keywords=["relocation"],
                                 asserts_nonrecurring=True),
        "A-10": AdjustmentIntent(adj_id="A-10", keywords=["dispatch"], is_pro_forma=True, event_months=["2026-09"]),
        "A-11": AdjustmentIntent(adj_id="A-11", counterparties=["J. Varga"], is_normalization=True),
    }
    contradictions = {
        "A-06": [
            Contradiction(
                doc_id="6.2 Controller email.txt",
                statement="The controller calls the cost a subscription.",
                quote=q("6.2 Controller email.txt", "Our Nimbus subscription renews next month."),
                conflicts_with="description of a one-time implementation",
            ),
            # Not verbatim in the email: must be dropped and counted, never used.
            Contradiction(
                doc_id="6.2 Controller email.txt",
                statement="Invented.",
                quote=q("6.2 Controller email.txt", "This is a permanent monthly cost."),
                conflicts_with="one-time",
            ),
        ]
    }
    classifications = {
        "A-03": [
            EntryClassification(entry_id=ids["expo"][0], qualifies=False, reason="Registration names the company; business training.",
                                doc_ids=["3.1 AHR Expo registration.txt"]),
            EntryClassification(entry_id=ids["supplier"][0], qualifies=False, reason="Supplier visit for company purchasing.",
                                doc_ids=["3.2 Supplier visit agenda.txt"]),
            EntryClassification(entry_id=ids["vacation"][0], qualifies=True, reason="Family vacation."),
            # No document behind it: kept, and left to the reviewer.
            EntryClassification(entry_id=ids["dues"][0], qualifies=False, reason="Club may be used for client events."),
        ]
    }
    questions = {"A-01": ["Please confirm the search is complete and no further fees are due."]}
    pkg = package(gl, adjustments, texts)
    ai = FakeAI(facts=facts, intents=intents, contradictions=contradictions, classifications=classifications, questions=questions)
    return pkg, ai, ids


@pytest.fixture(scope="module")
def deal():
    pkg, ai, ids = build_deal()
    return run(pkg, ai), ids


# ---------------------------------------------------------------------------
# Case types
# ---------------------------------------------------------------------------


def test_adequate_support_is_accepted_with_high_confidence(deal):
    results, ids = deal
    t, a = results["A-01"]
    assert a.treatment == Treatment.ACCEPT
    assert a.proposed == amounts(0, 30000, 10000)
    assert a.confidence == "high"
    assert {x.entry_id for x in a.gl_links if x.supports_claim} == set(ids["search"])
    assert a.documented == a.traced_gl == amounts(0, 30000, 10000)
    # "three installments" is a finite fee, not a continuing obligation.
    assert FlagCode.CONTINUING_OBLIGATION not in codes(a)
    assert not [f for f in a.flags if f.severity != Severity.INFO]


def test_partial_support_recurring_group_is_removed_and_litigation_kept(deal):
    results, ids = deal
    t, a = results["A-02"]
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(0, 34000, 8000)
    assert a.traced_gl == amounts(0, 50000, 24000)
    recurring = the_flag(a, FlagCode.RECURRING_PATTERN)
    assert "Matter 3002" in recurring.message and "FY2024" in recurring.message
    assert set(ids["retainer"][:12]) <= set(recurring.entry_ids)  # the 2024 comparables are cited
    continuing = the_flag(a, FlagCode.CONTINUING_OBLIGATION)
    assert continuing.doc_ids == ["2.2 Marlow Finch general engagement 2023.txt"]
    assert continuing.quotes[0].quote.startswith("Retainer of $1,000 per month")
    # The litigation matter's hourly-fee letter must not remove the litigation invoices.
    assert all(e in t.supporting_ids() for e in ids["lit"])
    (obs,) = [r for r in a.recurrence if "Matter 3002" in r.group]
    assert obs.amounts_by_period[FY24] == "12000.00"
    assert a.confidence == "medium"
    assert any("ongoing cost base" in j for j in a.judgment_questions)


def test_entry_qualification_removes_business_trips_with_a_verified_basis(deal):
    results, ids = deal
    t, a = results["A-03"]
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(0, 14000, 14000)
    flag = the_flag(a, FlagCode.CONTRADICTORY_EVIDENCE)
    assert set(flag.entry_ids) == set(ids["expo"])
    removed = {e for e, r in t.removals.items() if r.source == "ai"}
    assert removed == set(ids["expo"] + ids["supplier"])
    # The unsupported classification is kept and handed to the reviewer.
    assert ids["dues"][0] not in t.removals
    assert any("cited no verifiable document" in j for j in a.judgment_questions)
    # The dues statement and the vacation invoice support what is carried, so nothing blocks it.
    assert not [f for f in a.flags if f.code == FlagCode.NO_DOCUMENT_SUPPORT and f.severity != Severity.INFO]
    assert a.confidence == "low"  # the change rests entirely on an AI classification
    # One consolidated question and one judgment about the business trips, not one per document.
    assert [oq.basis for oq in a.open_questions].count("CONTRADICTORY_EVIDENCE") == 1
    assert any("does not fit management's basis" in j and "AI reading" in j for j in a.judgment_questions)


def test_overlap_goes_to_the_stronger_link_and_revises_the_loser(deal):
    results, ids = deal
    _, loser = results["A-04"]
    _, winner = results["A-02"]
    assert loser.treatment == Treatment.REVISE
    assert loser.proposed == amounts(0, 22000, 22000)
    flag = the_flag(loser, FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT)
    assert flag.severity == Severity.CRITICAL
    assert flag.related_adj_ids == ["A-02"]
    assert flag.entry_ids == [ids["lit"][2]]
    assert "Bill MF-7710-09 (Marlow & Finch LLP, Sep 2025, 8,000; memo cites Matter 7710)" in flag.message
    assert "also claimed in A-02" in flag.message
    assert FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT not in codes(winner)
    assert any("also claimed in A-04" in f.text for f in winner.facts)
    assert loser.confidence == "high"  # the overlap sets the amount; nothing else is in doubt


def test_costs_already_below_ebitda_are_rejected(deal):
    results, ids = deal
    _, a = results["A-05"]
    assert a.treatment == Treatment.REJECT
    assert a.proposed == amounts(0, 0, 0)
    flag = the_flag(a, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA)
    assert set(flag.entry_ids) == set(ids["refi"])  # monthly interest was never claimed
    assert "8100 Interest Expense" in flag.message and "INTEREST" in flag.message
    assert flag.amount_impact == "-9000.00" and flag.period_label == FY25


def test_contradicted_subscription_is_rejected_with_all_three_flags(deal):
    results, ids = deal
    t, a = results["A-06"]
    assert a.treatment == Treatment.REJECT
    assert a.proposed == amounts(0, 0, 0)
    assert {FlagCode.CONTRADICTORY_EVIDENCE, FlagCode.CONTINUING_OBLIGATION, FlagCode.RECURRING_PATTERN} <= codes(a)
    contra = the_flag(a, FlagCode.CONTRADICTORY_EVIDENCE)
    assert contra.quotes[0].quote == "Our Nimbus subscription renews next month."
    assert t.dropped_quotes == 1  # the invented quote never reaches the workpaper
    assert all("permanent monthly cost" not in f.message for f in a.flags)
    assert "failed verification" in a.rationale
    recurring = the_flag(a, FlagCode.RECURRING_PATTERN)
    assert "6 months outside the claimed window (Jan 2026–Jun 2026)" in recurring.message
    assert a.confidence == "medium"


def test_unadjusted_recovery_offsets_the_add_back_in_the_period_received(deal):
    results, ids = deal
    t, a = results["A-07"]
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(25000, -12000, 0)
    flag = the_flag(a, FlagCode.OFFSETTING_RECOVERY)
    assert flag.entry_ids == ids["insurance"]
    assert flag.period_label == FY25 and flag.amount_impact == "-12000.00"
    assert "AM-2291-X" in flag.message
    assert flag.quotes and flag.quotes[0].quote == "Net payment of $12,000.00"
    link = {x.entry_id: x for x in a.gl_links}[ids["insurance"][0]]
    assert link.supports_claim is False
    assert {d.doc_id: d.relation for d in a.doc_links}["7.3 Anchor Mutual claim letter.txt"] == "recovery"


def test_out_of_period_cost_moves_to_its_service_period(deal):
    results, ids = deal
    _, a = results["A-08"]
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(-18000, 18000, 0)
    flag = the_flag(a, FlagCode.OUT_OF_PERIOD)
    assert flag.period_label == FY24 and flag.amount_impact == "-18000.00"
    assert "covers services in Jul 2024–Dec 2024" in flag.message and "moves out of FY2025" in flag.message
    assert "outside the analysis" not in flag.message
    assert flag.quotes[0].quote.startswith("Service period")
    # The routine monthly subcontract invoices from the same vendor are not part of the claim.
    assert {x.entry_id for x in a.gl_links if x.supports_claim} == set(ids["trueup"])


def test_claim_in_a_period_without_activity_is_a_period_mismatch(deal):
    results, ids = deal
    _, a = results["A-09"]
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(0, 20000, 0)
    flag = the_flag(a, FlagCode.PERIOD_MISMATCH)
    assert flag.period_label == TTM and flag.amount_impact == "-20000.00"
    assert "booked Feb 2025–Mar 2025, in FY2025" in flag.message
    assert FlagCode.PARTIAL_GL_SUPPORT not in codes(a)  # the mismatch explains the gap


def test_pro_forma_not_realized_requests_information(deal):
    results, _ = deal
    _, a = results["A-10"]
    assert a.treatment == Treatment.REQUEST_INFO
    assert a.proposed == {}
    flag = the_flag(a, FlagCode.PRO_FORMA_NOT_REALIZED)
    assert flag.severity == Severity.CRITICAL
    assert "no executed document" in flag.message and "Sep 2026" in flag.message
    assert flag.quotes[0].doc_id == "10.1 COO email.txt"
    assert any(oq.priority == "high" and oq.basis == "PRO_FORMA_NOT_REALIZED" for oq in a.open_questions)


def test_normalization_on_a_draft_agreement_requests_information(deal):
    results, ids = deal
    _, a = results["A-11"]
    assert a.treatment == Treatment.REQUEST_INFO
    assert a.proposed == {}
    assert {FlagCode.UNSIGNED_OR_DRAFT_SUPPORT, FlagCode.NORMALIZATION_BENCHMARK_MISSING} <= codes(a)
    assert a.traced_gl == amounts(300000, 300000, 300000)  # actual officer compensation
    assert "200,000" in the_flag(a, FlagCode.NORMALIZATION_BENCHMARK_MISSING).message
    assert "Provisional" in a.rationale and "FY2025 100,000" in a.rationale


def test_every_flag_message_reads_as_a_sentence(deal):
    results, _ = deal
    for _, a in results.values():
        for f in a.flags:
            assert f.message[0].isupper() or f.message[:1].isdigit(), f.message
            assert f.message.rstrip()[-1] in ".)", f.message
            assert "None" not in f.message


def test_reviewer_text_is_short_and_keeps_quotes_structured(deal):
    """Practitioners read every line: one or two sentences, amounts in deals format,
    quotes in Flag.quotes rather than pasted into the message, each document named once."""
    results, _ = deal
    for _, a in results.values():
        for f in a.flags:
            assert len(f.message) <= 320, f.message
            assert all(q.quote not in f.message for q in f.quotes), f.message
            for d in f.doc_ids:
                assert f.message.count(d) <= 1, f.message
            assert ".00" not in f.message.replace("$", "")  # 35,500 not 35500.00
        for text in [x.text for x in a.facts] + a.judgment_questions + [oq.text for oq in a.open_questions]:
            assert len(text) <= 320, text
        for oq in a.open_questions:
            assert oq.text.count("?") <= 1 or oq.text.endswith("?"), oq.text
        assert len(a.rationale) <= 600, a.rationale
        # Contradictions are deduplicated per document.
        docs = [d for f in a.flags if f.code == FlagCode.CONTRADICTORY_EVIDENCE for d in f.doc_ids]
        assert len(docs) == len(set(docs))


# ---------------------------------------------------------------------------
# Smaller cases
# ---------------------------------------------------------------------------


def _small(entries, adjustment, texts=None, facts=None, intent=None, issues=()):
    gl = GL()
    ids = [gl.add(*e) for e in entries]
    pkg = package(gl, [adjustment], texts or {})
    ai = FakeAI(facts=facts or {}, intents={adjustment.adj_id: intent or AdjustmentIntent(adj_id=adjustment.adj_id)})
    return run(pkg, ai, issues)[adjustment.adj_id], ids


def test_sign_error_when_an_add_back_is_made_of_credits():
    texts = {"5.1 Credit memo CM-5.txt": "Credit memo CM-5. Warranty refund $5,000.00"}
    facts = {"5.1 Credit memo CM-5.txt": DocFacts(
        doc_id="5.1 Credit memo CM-5.txt", doc_type="invoice", counterparty="Coastal HVAC Service", reference_numbers=["CM-5"])}
    (t, a), ids = _small(
        [("2025-05-01", "6150", -5000, "Coastal HVAC Service", "Vendor refund - warranty repair", "CM-5")],
        claim("B-1", "Warranty repair", [0, 5000, 0], ["6150"]),
        texts, facts, AdjustmentIntent(adj_id="B-1", counterparties=["Coastal HVAC"]),
    )
    flag = the_flag(a, FlagCode.SIGN_ERROR)
    assert flag.period_label == FY25 and "net to (5,000) (credits)" in flag.message
    assert FlagCode.PARTIAL_GL_SUPPORT not in codes(a)
    assert a.proposed[FY25] == "-5000.00" and a.treatment == Treatment.REVISE


def test_repeated_bill_inside_the_claim_keeps_the_first_posting_only():
    # SPEC §5.7: the same bill number posted twice and claimed twice. The claim keeps the first
    # posting; the second leaves the claim (a diligence item reverses it once).
    entries = [
        ("2025-05-02", "6150", 7000, "Gulfline Roofing", "Roof repair", "GR-9"),
        ("2025-05-05", "6150", 7000, "Gulfline Roofing", "Roof repair", "GR-9"),
    ]
    issue = DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING, message="dup",
                             entry_ids=["GL-R6", "GL-R7"])
    texts = {"4.1 Invoice GR-9.txt": "Invoice GR-9. Amount due $7,000.00"}
    facts = {"4.1 Invoice GR-9.txt": DocFacts(
        doc_id="4.1 Invoice GR-9.txt", doc_type="invoice", counterparty="Gulfline Roofing", reference_numbers=["GR-9"],
        amounts=[AmountFact(label="total_due", amount="7000", quote=q("4.1 Invoice GR-9.txt", "Amount due $7,000.00"))])}
    (t, a), ids = _small(entries, claim("B-2", "Roof repair", [0, 14000, 0], ["6150"]), texts, facts,
                         intent=AdjustmentIntent(adj_id="B-2", counterparties=["Gulfline Roofing"]), issues=[issue])
    flag = the_flag(a, FlagCode.DUPLICATE_GL_ENTRY)
    assert flag.entry_ids == ids and "reversed once in a diligence item" in flag.message
    assert flag.effects == {FY25: "-7000.00"}
    assert a.proposed[FY25] == "7000.00" and a.treatment == Treatment.REVISE
    removed = {l.entry_id: l.removed_by for l in a.gl_links}
    assert removed == {"GL-R6": None, "GL-R7": FlagCode.DUPLICATE_GL_ENTRY}
    assert any(oq.basis == "DUPLICATE_GL_ENTRY" for oq in a.open_questions)
    assert a.judgment_questions and a.judgment_questions[0].startswith("No judgment needed")


def _two_seats(dates: tuple[str, str], bill_total: int):
    entries = [(dates[0], "6300", 1200, "Nimbus Cloud Systems", "Seat licence", "NC-77"),
               (dates[1], "6300", 1200, "Nimbus Cloud Systems", "Seat licence", "NC-77")]
    issue = DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING, message="dup",
                             entry_ids=["GL-R6", "GL-R7"])
    doc = "5.3 Invoice NC-77.txt"
    lines = "Seat licence 1,200.00. Seat licence 1,200.00." if bill_total == 2400 else "Seat licence 1,200.00."
    texts = {doc: f"Invoice NC-77. {lines} Total due ${bill_total:,}.00"}
    facts = {doc: DocFacts(doc_id=doc, doc_type="invoice", counterparty="Nimbus Cloud Systems", reference_numbers=["NC-77"],
                           amounts=[AmountFact(label="line", amount="1200", quote=q(doc, "Seat licence 1,200.00.")),
                                    AmountFact(label="total_due", amount=str(bill_total),
                                               quote=q(doc, f"Total due ${bill_total:,}.00"))])}
    return _small(entries, claim("B-4", "Platform seats", [0, 2400, 0], ["6300"]), texts, facts,
                  intent=AdjustmentIntent(adj_id="B-4", counterparties=["Nimbus Cloud Systems"]), issues=[issue])


def test_two_identical_lines_of_one_bill_are_not_a_repeated_posting():
    # Same number, same day: two seat licences on one invoice that totals twice the line. Nothing is removed;
    # the duplicate check stays a question with no effect.
    (t, a), _ = _two_seats(("2025-05-02", "2025-05-02"), 2400)
    flag = the_flag(a, FlagCode.DUPLICATE_GL_ENTRY)
    assert not flag.effects and t.supporting_total(FY25) == D(2400)
    # Posted on different days but the bill itself charges the line twice: still two charges.
    (t, a), _ = _two_seats(("2025-05-02", "2025-05-09"), 2400)
    assert not the_flag(a, FlagCode.DUPLICATE_GL_ENTRY).effects and t.supporting_total(FY25) == D(2400)
    # Posted on different days and the bill shows one charge: the second posting is the error.
    (t, a), _ = _two_seats(("2025-05-02", "2025-05-09"), 1200)
    assert the_flag(a, FlagCode.DUPLICATE_GL_ENTRY).effects == {FY25: "-1200.00"}


def test_same_memo_duplicates_without_a_shared_number_stay_a_question():
    entries = [
        ("2025-05-02", "6150", 7000, "Gulfline Roofing", "Roof repair", ""),
        ("2025-05-05", "6150", 7000, "Gulfline Roofing", "Roof repair", ""),
    ]
    issue = DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING, message="dup",
                             entry_ids=["GL-R6", "GL-R7"])
    (t, a), ids = _small(entries, claim("B-2", "Roof repair", [0, 14000, 0], ["6150"]),
                         intent=AdjustmentIntent(adj_id="B-2", counterparties=["Gulfline Roofing"]), issues=[issue])
    flag = the_flag(a, FlagCode.DUPLICATE_GL_ENTRY)
    assert "2 of the 2 postings are in the claimed set" in flag.message and not flag.effects
    assert t.supporting_total(FY25) == D(14000)


def test_document_total_that_differs_from_the_gl_entry():
    texts = {"4.1 Invoice PS-9.txt": "Invoice PS-9. Total due $10,500.00"}
    facts = {"4.1 Invoice PS-9.txt": DocFacts(
        doc_id="4.1 Invoice PS-9.txt", doc_type="invoice", counterparty="Pinecrest Search Partners", reference_numbers=["PS-9"],
        amounts=[AmountFact(label="total_due", amount="10500", quote=q("4.1 Invoice PS-9.txt", "Total due $10,500.00"))])}
    (t, a), _ = _small(
        [("2025-05-01", "6450", 10000, "Pinecrest Search Partners", "Search fee", "PS-9")],
        claim("B-3", "Search fee", [0, 10000, 0], ["6450"]),
        texts, facts, AdjustmentIntent(adj_id="B-3", counterparties=["Pinecrest Search"]),
    )
    flag = the_flag(a, FlagCode.DOC_GL_AMOUNT_MISMATCH)
    assert "total due of 10,500" in flag.message and "difference (500)" in flag.message
    assert flag.quotes[0].quote == "Total due $10,500.00"


def test_undocumented_claim_above_25_percent_requests_information():
    (t, a), _ = _small(
        [("2025-05-01", "6150", 9000, "Tidewater Restoration", "Mold remediation"),
         ("2025-06-01", "6150", 1000, "Tidewater Restoration", "Mold remediation")],
        claim("B-4", "Mold remediation", [0, 10000, 0], ["6150"]),
        intent=AdjustmentIntent(adj_id="B-4", counterparties=["Tidewater Restoration"]),
    )
    flag = the_flag(a, FlagCode.NO_DOCUMENT_SUPPORT)
    assert flag.severity == Severity.WARNING and "10,000 of the 10,000 carried (100%)" in flag.message
    assert a.treatment == Treatment.REQUEST_INFO and a.proposed == {}
    assert "Provisional amount the evidence would support: FY2024 0 / FY2025 10,000 / TTM Jun-26 0" in a.rationale


def test_management_move_into_the_service_period_is_accepted():
    """Management already moved the cost: -18,000 in FY2024 is explained by the service period."""
    texts = {"8.1 Ridgeway invoice RD-5501.txt": "Invoice RD-5501. Service period: July 1, 2024 - December 31, 2024."}
    facts = {"8.1 Ridgeway invoice RD-5501.txt": DocFacts(
        doc_id="8.1 Ridgeway invoice RD-5501.txt", doc_type="invoice", counterparty="Ridgeway Ductwork LLC",
        reference_numbers=["RD-5501"], service_period_start="2024-07-01", service_period_end="2024-12-31")}
    (t, a), _ = _small(
        [("2025-03-18", "5200", 18000, "Ridgeway Ductwork LLC", "Project closeout true-up", "RD-5501")],
        claim("B-5", "True-up", [-18000, 18000, 0], ["5200"], category=AdjustmentCategory.OUT_OF_PERIOD),
        texts, facts, AdjustmentIntent(adj_id="B-5", counterparties=["Ridgeway Ductwork"]),
    )
    assert a.proposed == amounts(-18000, 18000, 0)
    assert a.treatment == Treatment.ACCEPT
    assert FlagCode.PARTIAL_GL_SUPPORT not in codes(a) and FlagCode.PERIOD_MISMATCH not in codes(a)


# ---------------------------------------------------------------------------
# AI proposals are checked by code; cross-adjustment effects happen once
# ---------------------------------------------------------------------------


def test_ai_contradiction_scope_keeps_only_entries_the_document_is_about():
    texts = {"3.1 Expo registration.txt": "Registration for Harbor Unit Co at AHR Expo. Business purpose: product training.",
             "3.2 Coastal Auto Leasing statement.txt": "Lessee: J. Varga. Monthly payment $1,500.00."}
    facts = {"3.1 Expo registration.txt": DocFacts(
        doc_id="3.1 Expo registration.txt", doc_type="correspondence",
        key_statements=[q("3.1 Expo registration.txt", "Business purpose: product training.")]),
        "3.2 Coastal Auto Leasing statement.txt": DocFacts(
            doc_id="3.2 Coastal Auto Leasing statement.txt", doc_type="other", counterparty="Coastal Auto Leasing",
            amounts=[AmountFact(label="monthly_fee", amount="1500",
                                quote=q("3.2 Coastal Auto Leasing statement.txt", "Monthly payment $1,500.00."))])}
    gl = GL()
    expo = gl.add("2025-02-20", "6600", 4000, "Skyway Travel", "Travel - J. Varga - AHR Expo")
    lease = gl.add("2025-02-01", "6700", 1500, "Coastal Auto Leasing", "Lease - J. Varga personal vehicle")
    adj = claim("C-1", "Owner personal", [0, 5500, 0], ["6600", "6700"], ["DR 3"], AdjustmentCategory.OWNER_DISCRETIONARY)
    pkg = package(gl, [adj], texts)
    ai = FakeAI(
        facts=facts,
        intents={"C-1": AdjustmentIntent(adj_id="C-1", counterparties=["J. Varga"], asserts_personal=True)},
        # The AI names both February entries; only the trip is what the registration is about.
        contradictions={"C-1": [Contradiction(doc_id="3.1 Expo registration.txt", statement="Business travel.",
                                              quote=q("3.1 Expo registration.txt", "Business purpose: product training."),
                                              conflicts_with="personal expense", entry_ids=[expo, lease])]},
    )
    t, a = run(pkg, ai)["C-1"]
    assert set(t.removals) == {expo}
    assert a.proposed[FY25] == "1500.00"


def test_a_recovery_is_netted_once_and_only_from_documents_about_the_claim():
    gl = GL()
    roof = gl.add("2024-10-01", "6150", 30000, "Gulfline Roofing", "Storm damage - roof", "GR-1")
    gl.add("2024-11-01", "6150", 9000, "Gulfline Roofing", "Storm damage - gutters", "GR-2")
    moved = gl.add("2025-02-01", "6150", 5000, "Gulfline Roofing", "Storm damage - warehouse roof patch", "GR-3")
    proceeds = gl.add("2025-03-01", "8000", -20000, "Anchor Mutual Insurance", "Insurance proceeds - claim AM-77-X")
    texts = {"7.1 Claim letter AM-77-X.txt": "Claim AM-77-X. Net payment of $20,000.00 for storm damage.",
             "7.2 Gulfline invoice GR-3.txt": "Invoice GR-3. Warehouse roof patch. Claim AM-77-X."}
    facts = {
        "7.1 Claim letter AM-77-X.txt": DocFacts(doc_id="7.1 Claim letter AM-77-X.txt", doc_type="insurance",
                                                 counterparty="Anchor Mutual Insurance", reference_numbers=["AM-77-X"],
                                                 amounts=[AmountFact(label="net_payment", amount="20000",
                                                                     quote=q("7.1 Claim letter AM-77-X.txt", "Net payment of $20,000.00"))]),
        "7.2 Gulfline invoice GR-3.txt": DocFacts(doc_id="7.2 Gulfline invoice GR-3.txt", doc_type="invoice",
                                                  counterparty="Gulfline Roofing", reference_numbers=["GR-3", "AM-77-X"]),
    }
    storm = claim("C-1", "Storm repairs", [39000, 0, 0], ["6150"], ["DR 7.1"])
    # A second adjustment claims the Feb 2025 patch; its invoice also cites the claim number.
    patch = claim("C-2", "Warehouse repairs", [0, 5000, 0], ["6150"])
    pkg = package(gl, [storm, patch], texts)
    ai = FakeAI(facts=facts, intents={
        "C-1": AdjustmentIntent(adj_id="C-1", counterparties=["Gulfline Roofing"], keywords=["storm"]),
        "C-2": AdjustmentIntent(adj_id="C-2", keywords=["warehouse"], reference_numbers=["GR-3"]),
    })
    results = run(pkg, ai)
    t1, a1 = results["C-1"]
    t2, a2 = results["C-2"]
    assert roof in t1.claimed_ids() and moved in t2.claimed_ids()
    netted = [(adj, f) for adj, (_, a) in results.items() for f in a.flags if f.code == FlagCode.OFFSETTING_RECOVERY]
    assert len(netted) == 1 and netted[0][1].entry_ids == [proceeds]
    assert t1.effect(FY25) == -20000 and t2.effect(FY25) == 0  # the storm claim (it cites the letter) takes it
    assert "7.1 Claim letter AM-77-X.txt" in netted[0][1].doc_ids


def test_items_lost_to_another_adjustment_are_not_analysed_again():
    gl = GL()
    lit = [gl.add(f"2025-{m:02d}-10", "6400", 10000, "Marlow & Finch LLP", "Matter 7710 litigation", f"MF-{m}") for m in (3, 6, 9)]
    deal_fee = gl.add("2025-10-12", "6400", 22000, "Keystone Advisors", "Sell-side retainer", "KA-1")
    texts = {"8.1 Keystone engagement.txt": "Keystone Advisors sell-side engagement. Retainer $22,000.00",
             "2.1 Litigation invoices.txt": "Matter 7710 invoices MF-3, MF-6, MF-9 at $10,000.00 each."}
    facts = {
        "8.1 Keystone engagement.txt": DocFacts(doc_id="8.1 Keystone engagement.txt", doc_type="engagement_letter",
                                                counterparty="Keystone Advisors",
                                                amounts=[AmountFact(label="retainer", amount="22000",
                                                                    quote=q("8.1 Keystone engagement.txt", "Retainer $22,000.00"))]),
        "2.1 Litigation invoices.txt": DocFacts(doc_id="2.1 Litigation invoices.txt", doc_type="invoice",
                                                counterparty="Marlow & Finch LLP", reference_numbers=["Matter 7710"]),
    }
    pkg = package(gl, [claim("D-1", "Litigation", [0, 30000, 10000], ["6400"]),
                       claim("D-2", "Deal costs", [0, 32000, 32000], ["6400"])], texts)
    ai = FakeAI(facts=facts, intents={
        "D-1": AdjustmentIntent(adj_id="D-1", counterparties=["Marlow & Finch"], keywords=["litigation"], asserts_nonrecurring=True),
        "D-2": AdjustmentIntent(adj_id="D-2", counterparties=["Keystone Advisors"], reference_numbers=["MF-9"], asserts_nonrecurring=True),
    })
    _, a2 = run(pkg, ai)["D-2"]
    assert codes(a2) >= {FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT}
    # The lost invoice's siblings are D-1's business, not evidence that D-2 recurs.
    assert FlagCode.RECURRING_PATTERN not in codes(a2)
    assert a2.proposed == amounts(0, 22000, 22000)
    assert deal_fee in {x.entry_id for x in a2.gl_links if x.supports_claim}
    assert lit[2] not in {x.entry_id for x in a2.gl_links if x.supports_claim}


def test_a_write_off_is_tied_to_the_customer_billings_behind_it():
    gl = GL()
    bills = [gl.add("2025-06-18", "4000", -18400, "Halvorsen Builders", "Progress billing 4", "10972"),
             gl.add("2025-07-16", "4000", -21350, "Halvorsen Builders", "Progress billing 5", "11011"),
             gl.add("2025-08-20", "4000", -12250, "Halvorsen Builders", "Change order 2", "11059")]
    gl.add("2025-08-21", "4000", -9999, "Other Customer", "Service revenue")
    wo = gl.add("2025-10-31", "6150", 52000, "Halvorsen Builders", "Bad debt write-off - Chapter 7")
    texts = {"11.1 Bankruptcy notice.txt": "Notice of Chapter 7 filing. Halvorsen Builders. Claim $52,000.00"}
    facts = {"11.1 Bankruptcy notice.txt": DocFacts(doc_id="11.1 Bankruptcy notice.txt", doc_type="other", counterparty="Halvorsen Builders",
                                                    amounts=[AmountFact(label="claim", amount="52000", quote=q("11.1 Bankruptcy notice.txt", "Claim $52,000.00"))])}
    pkg = package(gl, [claim("E-1", "Customer bankruptcy", [0, 52000, 52000], ["6150"])], texts)
    ai = FakeAI(facts=facts, intents={"E-1": AdjustmentIntent(adj_id="E-1", counterparties=["Halvorsen Builders"])})
    t, a = run(pkg, ai)["E-1"]
    assert a.treatment == Treatment.ACCEPT
    tie = [f for f in a.facts if "ties to 3 earlier entries" in f.text]
    assert tie and set(tie[0].entry_ids) == set(bills + [wo])
    context = {x.entry_id for x in a.gl_links if not x.supports_claim}
    assert set(bills) <= context


# ---------------------------------------------------------------------------
# SPEC §5.4 amendments (answer-key review, §10.1)
# ---------------------------------------------------------------------------


def test_no_document_support_is_measured_on_the_amount_carried():
    """An undocumented entry that a challenge removes cannot force REQUEST_INFO:
    documents are needed for what diligence carries, not for what it rejects."""
    texts = {"7.1 Gulfline invoice GR-77.txt": "Invoice GR-77. Site repair after refinancing. Total due $10,000.00"}
    facts = {"7.1 Gulfline invoice GR-77.txt": DocFacts(
        doc_id="7.1 Gulfline invoice GR-77.txt", doc_type="invoice", counterparty="Gulfline Roofing", reference_numbers=["GR-77"],
        amounts=[AmountFact(label="total_due", amount="10000", quote=q("7.1 Gulfline invoice GR-77.txt", "Total due $10,000.00"))])}
    (t, a), ids = _small(
        [("2025-06-30", "8100", 20000, "Bayline Bank", "Loan fee write-off - Bayline Bank", "JE-9"),
         ("2025-06-15", "6150", 10000, "Gulfline Roofing", "Site repair - refinancing", "GR-77")],
        claim("F-1", "Refinancing costs", [0, 30000, 0], ["8100", "6150"]),
        texts, facts, AdjustmentIntent(adj_id="F-1", counterparties=["Bayline Bank", "Gulfline Roofing"]),
    )
    # Measured on the claim, 20,000 of 30,000 (67%) is undocumented; on what is carried, none is.
    assert FlagCode.ALREADY_EXCLUDED_FROM_EBITDA in codes(a)
    assert FlagCode.NO_DOCUMENT_SUPPORT not in codes(a)
    assert a.treatment == Treatment.REVISE and a.proposed == amounts(0, 10000, 0)


def test_a_period_that_carries_nothing_cannot_lack_documents(deal):
    results, _ = deal
    _, a = results["A-09"]  # TTM is claimed but carries nothing (the relocation sits in FY2025)
    assert not [f for f in a.flags if f.code == FlagCode.NO_DOCUMENT_SUPPORT and f.period_label == TTM]


def test_owner_items_need_documents_for_what_is_carried():
    """No exemption for owner items: a GL description or the company's own email is not documentary support."""
    entries = [(f"2025-{m:02d}-28", "6000", 3000, "K. Varga", "Payroll - K. Varga") for m in range(1, 13)]
    adj = claim("F-2", "Family member on payroll", [0, 36000, 0], ["6000"], ["DR 5"], AdjustmentCategory.OWNER_DISCRETIONARY)
    it = AdjustmentIntent(adj_id="F-2", counterparties=["K. Varga"], asserts_personal=True)
    (t, a), _ = _small(entries, adj, intent=it)
    flag = the_flag(a, FlagCode.NO_DOCUMENT_SUPPORT)
    assert flag.severity == Severity.WARNING and a.treatment == Treatment.REQUEST_INFO
    email = {"5.1 CEO email.txt": "From: CEO\nSubject: Payroll\nK. Varga is on payroll at $3,000 per month and does not work here."}
    email_facts = {"5.1 CEO email.txt": DocFacts(
        doc_id="5.1 CEO email.txt", doc_type="correspondence", counterparty="K. Varga",
        amounts=[AmountFact(label="monthly_fee", amount="3000", quote=q("5.1 CEO email.txt", "$3,000 per month"))])}
    (t, a), _ = _small(entries, adj, email, email_facts, it)
    assert t.doc_links and a.treatment == Treatment.REQUEST_INFO  # linked, but a management representation
    assert a.documented == amounts(0, 0, 0)


def _write_offs(claimed_memo: str, routine: object, months: Iterable[str]):
    rows = [("2025-10-31", "6950", 52000, "Halvor Homes", claimed_memo)]
    rows += [(f"{m}-28", "6950", routine, "Various customers", "Bad debt write-off - small accounts") for m in months]
    texts = {"11.1 Proof of claim.txt": "Proof of claim. Halvor Homes. Amount of claim $52,000.00"}
    facts = {"11.1 Proof of claim.txt": DocFacts(
        doc_id="11.1 Proof of claim.txt", doc_type="other", counterparty="Halvor Homes",
        amounts=[AmountFact(label="claim", amount="52000", quote=q("11.1 Proof of claim.txt", "Amount of claim $52,000.00"))])}
    adj = claim("F-3", "Customer bankruptcy write-off", [0, 52000, 52000], ["6950"], ["DR 11"])
    it = AdjustmentIntent(adj_id="F-3", counterparties=["Halvor Homes"], asserts_nonrecurring=True)
    return _small(rows, adj, texts, facts, it)


def test_recurrence_ignores_routine_months_below_a_quarter_of_the_claimed_month():
    months = [m for m in month_range("2024-01", "2026-06") if m != "2025-10"]
    (t, a), _ = _write_offs("Bad debt write-off - Halvor Homes", 500, months)
    assert FlagCode.RECURRING_PATTERN not in codes(a)
    assert a.treatment == Treatment.ACCEPT
    (obs,) = a.recurrence  # the routine activity is still recorded for the reviewer
    assert "Below the recurrence threshold" in obs.note


def test_recurrence_counts_material_months_outside_the_event_window():
    (t, a), _ = _write_offs("Bad debt write-off - Halvor Homes", 20000, ["2026-02", "2026-04", "2026-06"])
    flag = the_flag(a, FlagCode.RECURRING_PATTERN)
    assert "3 months outside the claimed window" in flag.message
    assert a.treatment == Treatment.REJECT


def test_event_window_is_the_union_of_claimed_months_not_their_range():
    """Comparable activity between two claimed months is outside the event window."""
    rows = [("2025-01-15", "6400", 12000, "Stone Legal", "Arbitration - Stone Legal", "SL-1"),
            ("2025-12-15", "6400", 8000, "Stone Legal", "Arbitration - Stone Legal", "SL-2")]
    rows += [(f"2025-{m:02d}-15", "6400", 9000, "Stone Legal", "Arbitration - Stone Legal") for m in (4, 6, 8)]
    adj = claim("F-4", "Arbitration costs", [0, 20000, 0], ["6400"])
    (t, a), ids = _small(rows, adj, intent=AdjustmentIntent(adj_id="F-4", counterparties=["Stone Legal"], asserts_nonrecurring=True))
    assert set(t.claimed[FY25]) == {ids[0], ids[1]}  # the only exact fit
    flag = the_flag(a, FlagCode.RECURRING_PATTERN)
    assert "3 months outside the claimed window (Apr 2025–Aug 2025)" in flag.message


def test_recurrence_does_not_apply_to_owner_or_normalization_items():
    rows = [(f"{m}-05", "6700", 500, "Harbor Point Yacht Club", "Club dues - J. Varga") for m in month_range("2024-01", "2025-12")]
    texts = {"3.3 Harbor Point Yacht Club statement.txt": "Member: J. Varga (individual). Monthly dues $500.00."}
    facts = {"3.3 Harbor Point Yacht Club statement.txt": DocFacts(
        doc_id="3.3 Harbor Point Yacht Club statement.txt", doc_type="other", counterparty="Harbor Point Yacht Club",
        amounts=[AmountFact(label="monthly_fee", amount="500", quote=q("3.3 Harbor Point Yacht Club statement.txt", "Monthly dues $500.00."))])}
    adj = claim("F-5", "Owner club dues", [0, 6000, 0], ["6700"], ["DR 3"], AdjustmentCategory.OWNER_DISCRETIONARY)
    # Even when the narrative also calls it one-time, recurrence is the premise of an owner item.
    it = AdjustmentIntent(adj_id="F-5", counterparties=["Harbor Point Yacht Club"], asserts_personal=True, asserts_nonrecurring=True)
    (t, a), _ = _small(rows, adj, texts, facts, it)
    assert FlagCode.RECURRING_PATTERN not in codes(a) and not a.recurrence
    assert a.treatment == Treatment.ACCEPT


def _retainer_letter(term_text: str, quote_text: str):
    rows = [("2025-10-02", "6400", 26000, "Keystone Advisors", "Sell-side advisory retainer", "KA-7")]
    texts = {"8.1 Keystone engagement letter.txt": f"Keystone Advisors sell-side engagement. {quote_text}"}
    facts = {"8.1 Keystone engagement letter.txt": DocFacts(
        doc_id="8.1 Keystone engagement letter.txt", doc_type="engagement_letter", counterparty="Keystone Advisors", is_signed=True,
        amounts=[AmountFact(label="retainer", amount="26000", quote=q("8.1 Keystone engagement letter.txt", quote_text))],
        terms=[TermFact(kind="retainer", text=term_text, quote=q("8.1 Keystone engagement letter.txt", quote_text))])}
    adj = claim("F-6", "Transaction advisory fees", [0, 26000, 26000], ["6400"], ["DR 8"])
    it = AdjustmentIntent(adj_id="F-6", counterparties=["Keystone Advisors"], asserts_nonrecurring=True)
    return _small(rows, adj, texts, facts, it)


def test_a_one_time_retainer_tied_to_a_transaction_is_not_a_continuing_obligation():
    (t, a), _ = _retainer_letter(
        "one-time retainer of $26,000 payable on signing, creditable against the success fee",
        "A one-time retainer of $26,000 is payable on signing, creditable against the success fee.",
    )
    assert FlagCode.CONTINUING_OBLIGATION not in codes(a)
    assert a.treatment == Treatment.ACCEPT


def test_a_periodic_retainer_is_a_continuing_obligation():
    (t, a), _ = _retainer_letter(
        "retainer of $26,000 per quarter until terminated",
        "A retainer of $26,000 per quarter is payable until terminated by either party.",
    )
    assert FlagCode.CONTINUING_OBLIGATION in codes(a)
    assert a.treatment == Treatment.REJECT


def test_a_retained_search_is_not_a_continuing_obligation():
    rows = [("2025-04-10", "6450", 15000, "Pinecrest Search Partners", "Retained search - installment 1", "PS-1")]
    quote = "This is a retained search; the fee is payable as the search progresses."
    texts = {"1.1 Pinecrest letter.txt": quote}
    facts = {"1.1 Pinecrest letter.txt": DocFacts(
        doc_id="1.1 Pinecrest letter.txt", doc_type="engagement_letter", counterparty="Pinecrest Search Partners", is_signed=True,
        amounts=[AmountFact(label="retainer", amount="15000", quote=q("1.1 Pinecrest letter.txt", quote))],
        terms=[TermFact(kind="retainer", text="retained search, fee payable monthly as the search progresses",
                        quote=q("1.1 Pinecrest letter.txt", quote))])}
    (t, a), _ = _small(rows, claim("F-7", "CFO search", [0, 15000, 0], ["6450"], ["DR 1"]), texts, facts,
                       AdjustmentIntent(adj_id="F-7", counterparties=["Pinecrest Search"], asserts_nonrecurring=True))
    assert FlagCode.CONTINUING_OBLIGATION not in codes(a) and a.treatment == Treatment.ACCEPT


def _true_up(service_start: str, service_end: str, booked: str, claimed: Iterable[object]):
    texts = {"8.1 Ridgeway invoice RD-9.txt": "Invoice RD-9. Project closeout true-up."}
    facts = {"8.1 Ridgeway invoice RD-9.txt": DocFacts(
        doc_id="8.1 Ridgeway invoice RD-9.txt", doc_type="invoice", counterparty="Ridgeway Ductwork LLC",
        reference_numbers=["RD-9"], service_period_start=service_start, service_period_end=service_end)}
    return _small([(booked, "5200", 18000, "Ridgeway Ductwork LLC", "Project closeout true-up", "RD-9")],
                  claim("F-8", "Prior-period true-up", claimed, ["5200"], category=AdjustmentCategory.OUT_OF_PERIOD),
                  texts, facts, AdjustmentIntent(adj_id="F-8", counterparties=["Ridgeway Ductwork"]))


def test_out_of_period_service_before_the_data_carries_no_negative_side():
    """One-sided case: FY2023 services booked in FY2024; the FY2023 side is outside the analysis."""
    (t, a), _ = _true_up("2023-10-01", "2023-12-31", "2024-02-20", [18000, 0, 0])
    flag = the_flag(a, FlagCode.OUT_OF_PERIOD)
    assert "no negative side is carried" in flag.message
    assert a.proposed == amounts(18000, 0, 0) and a.treatment == Treatment.ACCEPT


def test_an_out_of_period_entry_is_replaced_entirely_by_its_effect():
    """Services Oct 2023-Mar 2024 booked Jun 2024: FY2024 keeps only the pre-2024 half (9,000),
    not the booking plus the move (the double count the review panel found)."""
    (t, a), _ = _true_up("2023-10-01", "2024-03-31", "2024-06-15", [9000, 0, 0])
    assert a.proposed == amounts(9000, 0, 0) and a.treatment == Treatment.ACCEPT
    assert t.supporting_total(FY24) == 0 and t.effect(FY24) == 9000


# ---------------------------------------------------------------------------
# Flag effects: the walk from claimed to proposed (review findings excel-flag-impact-column, ui-08)
# ---------------------------------------------------------------------------


def _unflagged(t, a) -> dict[str, Decimal]:
    provisional = compute_proposed(t)  # the provisional amount for REQUEST_INFO items
    carried = {lbl: sum((D(f.effects[lbl]) for f in a.flags if lbl in f.effects), Decimal(0)) for lbl in LABELS}
    return {lbl: provisional[lbl] - D(a.claimed[lbl]) - carried[lbl] for lbl in LABELS}


def test_flag_effects_walk_from_claimed_to_proposed(deal):
    results, _ = deal
    for adj_id, (t, a) in results.items():
        assert all(abs(v) <= 1 for v in _unflagged(t, a).values()), (adj_id, _unflagged(t, a))
        if a.proposed:
            assert all(D(a.proposed[lbl]) == compute_proposed(t)[lbl] for lbl in LABELS)
        for f in a.flags:
            if f.code == FlagCode.EXCESS_GL_ACTIVITY:
                assert f.effects == {} and f.amount_impact is None  # unclaimed context activity, not an effect
            if len(f.effects) > 1:
                assert f.amount_impact is None
            elif f.effects:
                ((lbl, v),) = f.effects.items()
                assert f.period_label == lbl and f.amount_impact == v


def test_each_removal_counts_once_and_corroborating_flags_say_so(deal):
    results, _ = deal
    _, a = results["A-06"]  # contradicted, continuing and recurring: one removal, three flags
    contra = the_flag(a, FlagCode.CONTRADICTORY_EVIDENCE)
    assert contra.effects and all(D(v) < 0 for v in contra.effects.values())
    assert {lbl: D(v) for lbl, v in contra.effects.items()} == {lbl: -D(a.claimed[lbl]) for lbl in LABELS if D(a.claimed[lbl])}
    for code in (FlagCode.CONTINUING_OBLIGATION, FlagCode.RECURRING_PATTERN):
        f = the_flag(a, code)
        assert f.effects == {} and f.amount_impact is None and f.period_label is None
        assert "Already removed as contradicted by the documents; no further effect." in f.message
    _, a = results["A-02"]
    assert the_flag(a, FlagCode.CONTINUING_OBLIGATION).effects
    recurring = the_flag(a, FlagCode.RECURRING_PATTERN)
    assert recurring.effects == {} and "Already removed as a continuing obligation" in recurring.message


def test_multi_period_removals_carry_an_effect_per_period(deal):
    results, _ = deal
    _, a = results["A-04"]  # the overlap loser: the shared bill sits in FY2025 and TTM
    flag = the_flag(a, FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT)
    assert flag.effects == {FY25: "-8000.00", TTM: "-8000.00"}
    assert flag.period_label is None and flag.amount_impact is None  # no single period: see effects


def test_amount_effects_of_recoveries_moves_and_gaps(deal):
    results, _ = deal
    assert the_flag(results["A-07"][1], FlagCode.OFFSETTING_RECOVERY).effects == {FY25: "-12000.00"}
    assert the_flag(results["A-08"][1], FlagCode.OUT_OF_PERIOD).effects == {FY24: "-18000.00"}
    assert the_flag(results["A-09"][1], FlagCode.PERIOD_MISMATCH).effects == {TTM: "-20000.00"}


def test_the_walk_foots_when_a_capped_claim_is_moved_out_of_period():
    (t, a), _ = _true_up("2023-10-01", "2024-03-31", "2024-06-15", [9000, 0, 0])
    assert all(v == 0 for v in flag_effects(t).values())
    assert all(abs(v) <= 1 for v in _unflagged(t, a).values())


def test_gl_links_carry_their_audit_role(deal):
    # Review finding excel-tick-x-on-claimed-entries: a claimed entry a challenge removed looked like
    # context ("not part of the claim"). Each link now says whether it was claimed, and what removed it.
    results, ids = deal
    roles = {adj: {x.entry_id: x for x in a.gl_links} for adj, (_, a) in results.items()}
    for e in ids["search"]:
        assert (roles["A-01"][e].role, roles["A-01"][e].claimed) == ("supporting", True)
    shared = roles["A-04"][ids["lit"][2]]
    assert (shared.role, shared.claimed, shared.removed_by) == ("removed", True, FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT)
    assert shared.supports_claim is False
    for e in ids["refi"]:
        assert roles["A-05"][e].removed_by == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA and roles["A-05"][e].claimed
    recovery = roles["A-07"][ids["insurance"][0]]
    assert (recovery.role, recovery.claimed, recovery.removed_by) == ("recovery", False, None)
    for e in ids["trueup"]:
        assert roles["A-08"][e].role == "moved" and roles["A-08"][e].claimed and roles["A-08"][e].supports_claim
    for links in roles.values():
        for x in links.values():
            assert x.role in {"supporting", "removed", "moved", "recovery", "context"}
            assert (x.role == "removed") == (x.removed_by is not None)
            assert x.claimed == (x.role in {"supporting", "removed", "moved"})


def test_a_recovery_does_not_relabel_the_cost_invoices_that_cite_the_claim():
    # Review finding ui-10: the repair invoices citing the claim number were relabelled "Recovery" and
    # tied to the insurance proceeds.
    gl = GL()
    roof = gl.add("2024-10-01", "6150", 30000, "Gulfline Roofing", "Storm damage - roof", "GR-1")
    proceeds = gl.add("2025-03-01", "8000", -20000, "Anchor Mutual Insurance", "Insurance proceeds - claim AM-77-X")
    texts = {"7.1 Claim letter AM-77-X.txt": "Claim AM-77-X. Net payment of $20,000.00 for storm damage.",
             "7.2 Gulfline invoice GR-1.txt": "Invoice GR-1. Roof repair, storm damage. Claim AM-77-X. Total $30,000.00"}
    facts = {
        "7.1 Claim letter AM-77-X.txt": DocFacts(
            doc_id="7.1 Claim letter AM-77-X.txt", doc_type="insurance", counterparty="Anchor Mutual Insurance",
            reference_numbers=["AM-77-X"],
            amounts=[AmountFact(label="net_payment", amount="20000", quote=q("7.1 Claim letter AM-77-X.txt", "Net payment of $20,000.00"))]),
        "7.2 Gulfline invoice GR-1.txt": DocFacts(
            doc_id="7.2 Gulfline invoice GR-1.txt", doc_type="invoice", counterparty="Gulfline Roofing",
            reference_numbers=["GR-1", "AM-77-X"]),
    }
    pkg = package(gl, [claim("C-9", "Storm repairs", [30000, 0, 0], ["6150"], ["DR 7"])], texts)
    ai = FakeAI(facts=facts, intents={"C-9": AdjustmentIntent(adj_id="C-9", counterparties=["Gulfline Roofing"],
                                                              keywords=["storm"])})
    t, a = run(pkg, ai)["C-9"]
    links = {d.doc_id: d for d in a.doc_links}
    assert links["7.2 Gulfline invoice GR-1.txt"].relation == "invoice_for_entry"
    assert links["7.2 Gulfline invoice GR-1.txt"].entry_ids == [roof]
    assert links["7.1 Claim letter AM-77-X.txt"].relation == "recovery"
    assert proceeds in links["7.1 Claim letter AM-77-X.txt"].entry_ids
    flag = the_flag(a, FlagCode.OFFSETTING_RECOVERY)
    assert set(flag.doc_ids) == set(texts)  # the invoice still shows why the credit belongs to the event
    assert a.proposed == amounts(30000, -20000, 0)


# ---------------------------------------------------------------------------
# Term reading rests on verified quotes (review finding security-llm-unverified-doc-fields)
# ---------------------------------------------------------------------------


def test_a_term_fee_is_read_from_its_quote_not_its_description():
    doc = "6.1 MSA.txt"
    quote = q(doc, "Client shall pay a one-time setup fee of $500.00 and a monthly fee of $8,000.00.")
    assert _term_fee(TermFact(kind="monthly_fee", text="monthly fee of $1.00", quote=quote)) == Decimal("8000.00")
    assert _term_fee(TermFact(kind="monthly_fee", text="setup fee of $500.00", quote=quote)) == Decimal("500.00")
    assert _term_fee(TermFact(kind="monthly_fee", text="monthly fee of $8,000.00", quote=quote)) == Decimal("8000.00")


def test_a_term_end_is_read_from_its_quote_not_its_description():
    doc = "6.1 MSA.txt"
    facts = DocFacts(doc_id=doc, doc_type="contract")
    term = TermFact(kind="term_end", text="term ends 2030-12-31",
                    quote=q(doc, "This Agreement has a thirty-six (36) month initial term commencing January 1, 2025."))
    assert _term_end_month(term, facts) == "2027-12"
    words = TermFact(kind="term_end", text="term ends 2025-06-30", quote=q(doc, "a three-year term commencing March 1, 2025"))
    assert _term_end_month(words, facts) == "2028-02"


def test_a_description_calling_a_periodic_retainer_one_time_does_not_hide_it():
    (t, a), _ = _retainer_letter(
        "one-time retainer, payable in three installments, creditable against the success fee",
        "A retainer of $26,000 per quarter is payable until terminated by either party.",
    )
    assert FlagCode.CONTINUING_OBLIGATION in codes(a) and a.treatment == Treatment.REJECT


# ---------------------------------------------------------------------------
# Facts vs judgment (review finding ui-09)
# ---------------------------------------------------------------------------


def test_overlap_recovery_and_period_moves_are_put_to_the_reviewer(deal):
    results, _ = deal
    (overlap,) = results["A-04"][1].judgment_questions
    assert overlap.startswith("Which adjustment should carry") and "A-04 or A-02" in overlap
    assert "links it more strongly" in overlap
    recovery = results["A-07"][1].judgment_questions
    assert any("recovery" in j and "netted in FY2025" in j and "FY2024" in j for j in recovery)
    moved = results["A-08"][1].judgment_questions
    assert any("FY2024 cost" in j and "left in FY2025" in j for j in moved)
    for _, (_, a) in results.items():
        assert not {f.text for f in a.facts} & set(a.judgment_questions)


# ---------------------------------------------------------------------------
# Generalization rules (SPEC §5.2-5.4): each one a practitioner principle, tested on its own
# ---------------------------------------------------------------------------


def _facts(doc_id: str, doc_type: str, cp: str = "", refs=(), amounts=(), terms=(), statements=(), signed=None,
           start=None, end=None) -> DocFacts:
    return DocFacts(
        doc_id=doc_id, doc_type=doc_type, counterparty=cp or None, reference_numbers=list(refs),
        amounts=[AmountFact(label=label, amount=str(amount), quote=q(doc_id, text)) for label, amount, text in amounts],
        terms=[TermFact(kind=kind, text=text, quote=q(doc_id, quote)) for kind, text, quote in terms],
        key_statements=[q(doc_id, x) for x in statements], is_signed=signed,
        service_period_start=start, service_period_end=end,
    )


def test_routine_entries_that_only_restate_the_account_name_do_not_pad_the_claim():
    # A casualty claim in a repairs account: the event bill links on its own evidence; routine repairs
    # match only the account's own word ("repair") and must not be used to make up the claim. The part of
    # the claim that is an unbooked estimate stays unsupported, citing the email that states it.
    gl = GL()
    event = gl.add("2025-08-20", "6150", 38500, "Seaboard Restoration", "Water extraction - sprinkler break", "SR-1")
    routine = [gl.add(f"2025-{m:02d}-11", "6150", 1000 + 437.19 * m, "Dockside Electric", "Dock door repair", f"DE-{m}")
               for m in range(1, 13)]
    texts = {"6.1 Seaboard invoice SR-1.txt": "Invoice SR-1. Amount due $38,500.00",
             "6.2 Controller email.txt": "We carried $60,000: $38,500 invoiced plus a $21,500 estimate not yet booked."}
    facts = {
        "6.1 Seaboard invoice SR-1.txt": _facts("6.1 Seaboard invoice SR-1.txt", "invoice", "Seaboard Restoration",
                                               ["SR-1"], [("total_due", 38500, "Amount due $38,500.00")]),
        "6.2 Controller email.txt": _facts("6.2 Controller email.txt", "correspondence", "", (),
                                           [("line", 21500, "We carried $60,000: $38,500 invoiced plus a $21,500 estimate not yet booked.")]),
    }
    (t, a), _ = _small([], claim("C-1", "Sprinkler break", [0, 60000, 0], ["6150"], refs=["DR 6"]), texts, facts,
                       AdjustmentIntent(adj_id="C-1", keywords=["sprinkler", "water", "repairs"]))
    t2, a2 = _run_gl(gl, claim("C-1", "Sprinkler break", [0, 60000, 0], ["6150"], refs=["DR 6"]), texts, facts,
                     AdjustmentIntent(adj_id="C-1", keywords=["sprinkler", "water", "repairs"]))
    assert t2.claimed[FY25] == [event]
    roles = {x.entry_id: x.role for x in a2.gl_links}
    assert all(roles[e] == "context" for e in routine)
    partial = [f for f in a2.flags if f.code == FlagCode.PARTIAL_GL_SUPPORT and f.period_label == FY25]
    assert partial and partial[0].effects == {FY25: "-21500.00"} and "6.2 Controller email.txt" in partial[0].doc_ids
    assert a2.proposed[FY25] == "38500.00" and a2.treatment == Treatment.REVISE
    assert any("down to an amount not booked" in oq.text for oq in a2.open_questions)


def test_a_document_that_merely_states_the_gap_amount_is_cited_neutrally():
    # The engagement letter's retainer happens to equal the gap: it is cited, but nothing says the gap is an
    # unbooked amount, so the question does not claim that it is.
    gl = GL()
    gl.add("2025-08-20", "6400", 20000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-1")
    letter = "4.1 Marlow Finch engagement letter (Matter 7710).txt"
    text = "The Company will pay a retainer of $5,000 on signing."
    facts = {letter: _facts(letter, "engagement_letter", "Marlow & Finch LLP", ["7710"], [("fee", 5000, text)],
                            signed=True)}
    t, a = _run_gl(gl, claim("L-2", "Reyes litigation", [0, 25000, 0], ["6400"], refs=["DR 4.1"]), {letter: text}, facts,
                   AdjustmentIntent(adj_id="L-2", counterparties=["Marlow & Finch"], reference_numbers=["7710"]))
    assert any(f.code == FlagCode.PARTIAL_GL_SUPPORT and letter in f.doc_ids for f in a.flags)
    assert not any("not booked" in oq.text for oq in a.open_questions)
    assert any(f"{letter} states the same 5,000" in oq.text for oq in a.open_questions)


def _run_gl(gl: GL, adjustment, texts, facts, intent, issues=()):
    pkg = package(gl, [adjustment], texts or {})
    ai = FakeAI(facts=facts or {}, intents={adjustment.adj_id: intent})
    return run(pkg, ai, issues)[adjustment.adj_id]


def _related_rent(broker_amounts):
    gl = GL()
    related = gl.monthly("2025-01", "2026-06", "6100", 9000, "Bayfront Holdings", "Rent - main yard")
    other = gl.monthly("2025-01", "2026-06", "6100", 4000, "Harbor Storage", "Rent - overflow site")
    texts = {"2.3 Lease - main yard.txt": "Base Rent: $9,000.00 per month.",
             "2.4 Broker opinion of market rent.txt": " ".join(t for _, _, t in broker_amounts)}
    facts = {
        "2.3 Lease - main yard.txt": _facts("2.3 Lease - main yard.txt", "contract", "Bayfront Holdings", (),
                                           [("monthly_fee", 9000, "Base Rent: $9,000.00 per month.")], signed=True),
        "2.4 Broker opinion of market rent.txt": _facts("2.4 Broker opinion of market rent.txt", "benchmark",
                                                        "Coastline Realty Advisors", (), broker_amounts, signed=True),
    }
    adj = claim("R-1", "Related-party rent", [0, 12000, 12000], ["6100"], refs=["DR 2"],
                category=AdjustmentCategory.NORMALIZATION)
    intent = AdjustmentIntent(adj_id="R-1", counterparties=["Bayfront Holdings"], is_normalization=True,
                              normalized_amount="96000.00", keywords=["rent"])
    return _run_gl(gl, adj, texts, facts, intent), related, other


def test_normalization_uses_the_arrangements_own_cost_and_an_independent_benchmark_level():
    broker = [("line", 126000, "On 14,000 square feet this is $126,000 per year, or $10,500 per month."),
              ("monthly_fee", 10500, "On 14,000 square feet this is $126,000 per year, or $10,500 per month."),
              ("monthly_fee", 9000, "The current contract rent of $9,000 per month is below market."),
              ("line", 9, "We conclude a market rent of $9.00 per square foot per year.")]
    (t, a), related, other = _related_rent(broker)
    # Actual cost is the related-party lease only; the other site's rent is not the arrangement.
    assert t.claimed[FY25] == [e for e in related if t.index.by_id[e].month <= "2025-12"]
    assert not set(other) & set(t.supporting_ids())
    # Market (126,000) is above what is paid (108,000): the normalization reduces EBITDA.
    assert a.proposed == amounts(0, -18000, -18000) and a.treatment == Treatment.REVISE
    flag = the_flag(a, FlagCode.CONTRADICTORY_EVIDENCE)
    assert flag.effects == {FY25: "-30000.00", TTM: "-30000.00"}  # 96,000 used by management -> 126,000
    assert FlagCode.NORMALIZATION_BENCHMARK_MISSING not in codes(a) and FlagCode.SIGN_ERROR not in codes(a)
    assert "126,000" in a.rationale


def test_a_benchmark_that_states_several_levels_sets_none():
    broker = [("monthly_fee", 10000, "Comparable A rents at $10,000 per month."),
              ("monthly_fee", 11500, "Comparable B rents at $11,500 per month.")]
    (t, a), _, _ = _related_rent(broker)
    assert FlagCode.NORMALIZATION_BENCHMARK_MISSING in codes(a) and a.treatment == Treatment.REQUEST_INFO
    assert any("Which market level applies?" in j for j in a.judgment_questions)


def _study(cite_final_bill: bool, category=AdjustmentCategory.NON_RECURRING):
    gl = GL()
    bills = [gl.add("2025-03-10", "6420", 30000, "Ridgeway Consulting", "Network study - phase 1", "RC-1"),
             gl.add("2025-06-10", "6420", 24000, "Ridgeway Consulting", "Network study - phase 2", "RC-2"),
             gl.add("2025-09-10", "6420", 30000, "Ridgeway Consulting", "Network study - phase 3", "RC-3")]
    texts = {"7.1 Ridgeway engagement letter.txt": "Our fixed fee of $84,000 is billed in three phases.",
             "7.2 Invoice RC-1.txt": "Invoice RC-1. Amount due $30,000.00",
             "7.3 Invoice RC-2.txt": "Invoice RC-2. Amount due $24,000.00",
             "8.9 Invoice RC-3.txt": "Invoice RC-3. Amount due $30,000.00"}
    facts = {
        "7.1 Ridgeway engagement letter.txt": _facts("7.1 Ridgeway engagement letter.txt", "engagement_letter",
                                                     "Ridgeway Consulting", (),
                                                     [("fee", 84000, "Our fixed fee of $84,000 is billed in three phases.")],
                                                     signed=True),
        **{k: _facts(k, "invoice", "Ridgeway Consulting", [k.split()[-1][:-4]],
                     [("total_due", v, f"Amount due ${v:,}.00")])
           for k, v in (("7.2 Invoice RC-1.txt", 30000), ("7.3 Invoice RC-2.txt", 24000), ("8.9 Invoice RC-3.txt", 30000))},
    }
    refs = ["DR 7"] + (["8.9"] if cite_final_bill else [])
    adj = claim("E-1", "Network study", [0, 54000, 0], ["6420"], refs=refs, category=category)
    intent = AdjustmentIntent(adj_id="E-1", counterparties=["Ridgeway Consulting"], keywords=["network", "study"])
    return _run_gl(gl, adj, texts, facts, intent), bills


def test_the_rest_of_a_fixed_fee_engagement_is_carried_when_management_cites_its_bill():
    (t, a), bills = _study(cite_final_bill=True)
    assert a.proposed[FY25] == "84000.00" and a.treatment == Treatment.REVISE
    flag = [f for f in a.flags if f.code == FlagCode.EXCESS_GL_ACTIVITY and f.severity == Severity.WARNING]
    assert len(flag) == 1 and flag[0].effects == {FY25: "30000.00"} and flag[0].period_label == FY25
    link = {x.entry_id: x for x in a.gl_links}[bills[2]]
    assert link.supports_claim and not link.claimed and link.claimed_in == [] and link.role == "supporting"
    # TTM Jun-26 has no claim, so nothing is carried there even though phase 3 falls in it.
    assert a.proposed[TTM] == "0.00"


def test_an_unclaimed_bill_is_context_unless_the_fixed_fee_rule_holds():
    (t, a), _ = _study(cite_final_bill=False)  # management does not cite the unclaimed bill
    assert a.proposed[FY25] == "54000.00" and a.treatment == Treatment.ACCEPT
    assert all(f.severity == Severity.INFO for f in a.flags if f.code == FlagCode.EXCESS_GL_ACTIVITY)
    (t, a), _ = _study(cite_final_bill=True, category=AdjustmentCategory.PRO_FORMA)
    assert not t.carried_ids()


def test_each_carried_bill_is_tied_to_its_own_engagement_letter():
    # Two fixed-fee engagements are carried in the same period; each letter supports only its own bill.
    gl = GL()
    gl.add("2025-03-10", "6420", 30000, "Ridgeway Consulting", "Network study - phase 1", "RC-1")
    gl.add("2025-06-10", "6420", 24000, "Ridgeway Consulting", "Network study - phase 2", "RC-2")
    rc3 = gl.add("2025-09-10", "6420", 30000, "Ridgeway Consulting", "Network study - phase 3", "RC-3")
    gl.add("2025-04-10", "6420", 11000, "Keystone Advisors", "Pricing review - stage 1", "KA-1")
    ka2 = gl.add("2025-10-10", "6420", 16000, "Keystone Advisors", "Pricing review - stage 2", "KA-2")
    letters = {"7.1 Ridgeway engagement letter.txt": ("Ridgeway Consulting", 84000),
               "7.5 Keystone engagement letter.txt": ("Keystone Advisors", 27000)}
    bills = {"7.2 Invoice RC-1.txt": ("Ridgeway Consulting", "RC-1", 30000),
             "7.3 Invoice RC-2.txt": ("Ridgeway Consulting", "RC-2", 24000),
             "7.4 Invoice RC-3.txt": ("Ridgeway Consulting", "RC-3", 30000),
             "7.6 Invoice KA-1.txt": ("Keystone Advisors", "KA-1", 11000),
             "7.7 Invoice KA-2.txt": ("Keystone Advisors", "KA-2", 16000)}
    texts = {k: f"Our fixed fee of ${v:,} covers the whole engagement." for k, (_, v) in letters.items()}
    texts |= {k: f"Invoice {n}. Amount due ${v:,}.00" for k, (_, n, v) in bills.items()}
    facts = {k: _facts(k, "engagement_letter", cp, (), [("fee", v, texts[k])], signed=True) for k, (cp, v) in letters.items()}
    facts |= {k: _facts(k, "invoice", cp, [n], [("total_due", v, f"Amount due ${v:,}.00")]) for k, (cp, n, v) in bills.items()}
    adj = claim("E-2", "Consulting projects", [0, 65000, 0], ["6420"], refs=["DR 7"])
    intent = AdjustmentIntent(adj_id="E-2", counterparties=["Ridgeway Consulting", "Keystone Advisors"])
    t, a = _run_gl(gl, adj, texts, facts, intent)
    assert set(t.carried.get(FY25, [])) == {rc3, ka2}
    ridgeway, keystone = t.doc_links["7.1 Ridgeway engagement letter.txt"], t.doc_links["7.5 Keystone engagement letter.txt"]
    assert rc3 in ridgeway.entry_basis and ka2 not in ridgeway.entry_basis
    assert ka2 in keystone.entry_basis and rc3 not in keystone.entry_basis


def _freight(booked: str, start: str, end: str, category=AdjustmentCategory.OUT_OF_PERIOD, claims=(0, 38400, 38400)):
    gl = GL()
    bill = gl.add(booked, "5200", 38400, "Altona Freight", "Fuel surcharge correction", "AF-118")
    texts = {"6.3 Altona invoice AF-118.txt": "Invoice AF-118. Total due $38,400.00"}
    facts = {"6.3 Altona invoice AF-118.txt": _facts("6.3 Altona invoice AF-118.txt", "invoice", "Altona Freight", ["AF-118"],
                                                     [("total_due", 38400, "Total due $38,400.00")], start=start, end=end)}
    adj = claim("O-1", "Freight true-up", list(claims), ["5200"], refs=["DR 6.3"], category=category)
    intent = AdjustmentIntent(adj_id="O-1", counterparties=["Altona Freight"])
    return _run_gl(gl, adj, texts, facts, intent), bill


def test_out_of_period_is_tested_on_every_period_label():
    # Service Apr-Sep 2025, booked Nov 2025: FY2025 holds the booking and every service month (no move),
    # but TTM Jun-26 starts in July and holds only three of the six service months.
    (t, a), bill = _freight("2025-11-14", "2025-04-01", "2025-09-30")
    flag = the_flag(a, FlagCode.OUT_OF_PERIOD)
    assert a.proposed == amounts(0, 0, 19200) and flag.effects == {FY25: "-38400.00", TTM: "-19200.00"}
    assert "TTM Jun-26 holds 3 of the 6 service months" in flag.message


def _quarterly(booked: str, start: str, end: str, *, previous: str = "", text: str = "Invoice LS-9. Total due $9,000.00",
               category=AdjustmentCategory.NON_RECURRING, previous_doc: tuple[str, str] = ("", "")):
    """A quarterly bill (LS-9) for a claim, optionally after the party's previous quarterly bill (LS-8)."""
    gl = GL()
    if previous:
        gl.add(previous, "6150", 9000, "Lakeside Services", "Quarterly site services", "LS-8")
    bill = gl.add(booked, "6150", 9000, "Lakeside Services", "Quarterly site services", "LS-9")
    texts = {"6.4 Lakeside invoice LS-9.txt": text}
    facts = {"6.4 Lakeside invoice LS-9.txt": _facts("6.4 Lakeside invoice LS-9.txt", "invoice", "Lakeside Services",
                                                     ["LS-9"], [("total_due", 9000, "Total due $9,000.00")],
                                                     start=start, end=end)}
    if previous_doc[0]:
        texts["6.3 Lakeside invoice LS-8.txt"] = "Invoice LS-8. Total due $9,000.00"
        facts["6.3 Lakeside invoice LS-8.txt"] = _facts("6.3 Lakeside invoice LS-8.txt", "invoice", "Lakeside Services",
                                                        ["LS-8"], [("total_due", 9000, "Total due $9,000.00")],
                                                        start=previous_doc[0], end=previous_doc[1])
    adj = claim("O-2", "Site services", [0, 9000, 9000], ["6150"], refs=["DR 6.4"], category=category)
    intent = AdjustmentIntent(adj_id="O-2", counterparties=["Lakeside Services"])
    return _run_gl(gl, adj, texts, facts, intent), bill


def test_ordinary_billing_in_arrears_is_keyed_on_cadence_not_on_the_lag():
    # A quarterly bill for Apr-Jun, booked in August (two months after quarter-end), the party's previous
    # quarterly bill booked three months earlier: one cycle of an ordinary series, so nothing moves even
    # though TTM Jun-26 (from July) holds the booking but none of the service months.
    (t, a), _ = _quarterly("2025-08-12", "2025-04-01", "2025-06-30", previous="2025-05-12")
    assert FlagCode.OUT_OF_PERIOD not in codes(a)
    # The same series shown by the bills themselves: the previous bill's service period ends the month before
    # (its booking, paid late, is only two months earlier, so the GL spacing alone would not show the cadence).
    (t, a), _ = _quarterly("2025-08-12", "2025-04-01", "2025-06-30", previous="2025-06-12",
                           previous_doc=("2025-01-01", "2025-03-31"))
    assert FlagCode.OUT_OF_PERIOD not in codes(a)
    # Presented by management as out-of-period: the move is measured whatever the cadence.
    (t, a), _ = _quarterly("2025-08-12", "2025-04-01", "2025-06-30", previous="2025-05-12",
                           category=AdjustmentCategory.OUT_OF_PERIOD)
    assert FlagCode.OUT_OF_PERIOD in codes(a)


def test_a_bill_outside_any_billing_series_is_out_of_period_even_one_month_after_its_service():
    # A lone three-month bill: no earlier bill of the party, no abutting bill in the data room.
    (t, a), _ = _quarterly("2025-07-12", "2025-04-01", "2025-06-30")
    assert FlagCode.OUT_OF_PERIOD in codes(a)
    # A previous bill only one month earlier: this one covers more than the time since the last bill.
    (t, a), _ = _quarterly("2025-07-12", "2025-04-01", "2025-06-30", previous="2025-06-12")
    assert FlagCode.OUT_OF_PERIOD in codes(a)
    # Booked more than one cycle after the service ends: a late bill, not ordinary arrears.
    (t, a), _ = _quarterly("2025-11-12", "2025-04-01", "2025-06-30", previous="2025-08-12")
    assert FlagCode.OUT_OF_PERIOD in codes(a)


def test_a_catch_up_or_multi_cycle_bill_is_never_ordinary_arrears():
    # The bill calls itself a true-up: out of period even inside a series and one month after the service.
    (t, a), _ = _quarterly("2025-07-12", "2025-04-01", "2025-06-30", previous="2025-04-12",
                           text="Quarterly true-up of site services. Total due $9,000.00")
    assert FlagCode.OUT_OF_PERIOD in codes(a)
    # Six months at once, booked the month after they end: a catch-up whatever the lag.
    (t, a), _ = _freight("2025-10-05", "2025-04-01", "2025-09-30", category=AdjustmentCategory.NON_RECURRING)
    assert FlagCode.OUT_OF_PERIOD in codes(a)


def test_recurrence_evidence_removes_only_the_recurring_part_of_a_mixed_contract():
    gl = GL()
    setup = [gl.add("2025-03-05", "6300", 20000, "Nimbus Cloud Systems", "Platform implementation - milestone 1", "NC-1"),
             gl.add("2025-06-05", "6300", 20000, "Nimbus Cloud Systems", "Platform implementation - milestone 2", "NC-2")]
    subs = gl.monthly("2025-06", "2025-12", "6300", 3000, "Nimbus Cloud Systems", "Platform subscription")
    doc = "5.1 Nimbus order form.txt"
    one_time = "One-time implementation fee: $40,000.00, invoiced in two milestones of $20,000.00 each."
    monthly = "Subscription fee: $3,000.00 per month; the subscription renews automatically."
    texts = {doc: f"{one_time} {monthly}"}
    facts = {doc: _facts(doc, "contract", "Nimbus Cloud Systems", ["NC-OF-1"],
                         [("fee", 40000, one_time), ("monthly_fee", 3000, monthly)],
                         [("monthly_fee", "monthly fee of $3,000.00", monthly), ("auto_renew", "renews automatically", monthly)],
                         [one_time, monthly], signed=True)}
    adj = claim("K-1", "Platform implementation", [0, 61000, 0], ["6300"], refs=["DR 5.1"])
    intent = AdjustmentIntent(adj_id="K-1", counterparties=["Nimbus Cloud Systems"], asserts_nonrecurring=True)
    pkg = package(gl, [adj], texts)
    ai = FakeAI(facts=facts, intents={"K-1": intent}, contradictions={"K-1": [Contradiction(
        doc_id=doc, statement="describes the cost as a subscription.", quote=q(doc, monthly),
        conflicts_with="one-time", entry_ids=setup + subs)]})
    t, a = run(pkg, ai)["K-1"]
    assert a.proposed[FY25] == "40000.00"
    removed = {x.entry_id for x in a.gl_links if x.role == "removed"}
    assert removed == set(subs)
    assert any("one-time component" in f.text for f in a.facts)


def test_a_document_about_another_matter_of_the_same_firm_contradicts_nothing():
    gl = GL()
    lit = [gl.add("2025-03-10", "6400", 12000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-7710-03"),
           gl.add("2025-06-10", "6400", 14000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Harbor - litigation", "MF-7710-06")]
    gl.monthly("2025-01", "2025-12", "6400", 1000, "Marlow & Finch LLP", "Matter 3002 general corporate retainer")
    doc = "4.1 Marlow Finch engagement letter (Matter 3002).txt"
    text = "General counsel services under Matter 3002 for a flat monthly fee of $1,000, until either party terminates."
    facts = {doc: _facts(doc, "engagement_letter", "Marlow & Finch LLP", ["3002"], [("monthly_fee", 1000, text)],
                         [("ongoing_services", "continues until terminated", text)], [text], signed=True)}
    adj = claim("L-1", "Reyes litigation", [0, 26000, 0], ["6400"], refs=["DR 4"])
    intent = AdjustmentIntent(adj_id="L-1", counterparties=["Marlow & Finch"], reference_numbers=["7710"],
                              asserts_nonrecurring=True)
    ai = FakeAI(facts=facts, intents={"L-1": intent}, contradictions={"L-1": [Contradiction(
        doc_id=doc, statement="describes the cost as recurring.", quote=q(doc, text), conflicts_with="one-time",
        entry_ids=lit)]})
    t, a = run(package(gl, [adj], {doc: text}), ai)["L-1"]
    assert FlagCode.CONTRADICTORY_EVIDENCE not in codes(a) and FlagCode.CONTINUING_OBLIGATION not in codes(a)
    assert not t.removals and t.supporting_total(FY25) == D(26000)
    assert any("separate engagement" in f.text for f in a.facts)


def test_a_document_about_the_below_ebitda_part_says_nothing_about_the_rest():
    gl = GL()
    fee = gl.add("2026-01-16", "6400", 42000, "Marlowe Capital", "Debt placement fee", "MC-4")
    writeoff = gl.add("2026-01-31", "8100", 27600, "", "Write-off of unamortized debt issuance costs", "JE-9")
    doc = "7.3 Debt cost amortization schedule.txt"
    text = "Amortization: $1,150.00 per month. Unamortized balance written off: $27,600.00."
    facts = {doc: _facts(doc, "other", "", (), [("monthly_fee", 1150, text), ("line", 27600, text)],
                         [("monthly_fee", "monthly fee of $1,150.00", text)], [text])}
    adj = claim("F-1", "Refinancing costs", [0, 0, 69600], ["6400", "8100"], refs=["DR 7"])
    ai = FakeAI(facts=facts, intents={"F-1": AdjustmentIntent(adj_id="F-1", keywords=["refinancing", "debt"])},
                contradictions={"F-1": [Contradiction(doc_id=doc, statement="provides for a monthly fee of $1,150.00.",
                                                     quote=q(doc, text), conflicts_with="one-time", entry_ids=[])]})
    t, a = run(package(gl, [adj], {doc: text}), ai)["F-1"]
    assert FlagCode.CONTRADICTORY_EVIDENCE not in codes(a)
    assert the_flag(a, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA).entry_ids == [writeoff]
    assert t.supporting_total(TTM) == D(42000) and fee in t.supporting_ids()


def test_a_document_about_both_an_out_of_play_entry_and_an_in_play_one_still_speaks():
    # The schedule is about the below-EBITDA write-off and the fee still in play: it is not confined to the
    # removed entry, so its recurrence statement reaches the fee.
    gl = GL()
    fee = gl.add("2026-01-16", "6400", 42000, "Marlowe Capital", "Debt placement fee", "MC-4")
    writeoff = gl.add("2026-01-31", "8100", 27600, "", "Write-off of unamortized debt issuance costs", "JE-9")
    doc = "7.3 Debt cost schedule.txt"
    # The schedule names the fee's party and subject (not its amount) and states the write-off's amount.
    text = ("Marlowe Capital arranged the debt placement. Unamortized balance written off: $27,600.00. "
            "Monthly fee of $1,150.00, recurring.")
    facts = {doc: _facts(doc, "other", "", (), [("line", 27600, text)], (), [text])}
    adj = claim("F-2", "Refinancing costs", [0, 0, 69600], ["6400", "8100"], refs=["DR 7"])
    ai = FakeAI(facts=facts, intents={"F-2": AdjustmentIntent(adj_id="F-2", keywords=["refinancing", "debt"])},
                contradictions={"F-2": [Contradiction(doc_id=doc, statement="describes a recurring monthly fee.",
                                                     quote=q(doc, text), conflicts_with="one-time", entry_ids=[])]})
    t, a = run(package(gl, [adj], {doc: text}), ai)["F-2"]
    assert the_flag(a, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA).entry_ids == [writeoff]
    assert FlagCode.CONTRADICTORY_EVIDENCE in codes(a)
    assert {x.entry_id: x.removed_by for x in a.gl_links}[fee] == FlagCode.CONTRADICTORY_EVIDENCE


def _write_off(with_outside_doc: bool, memo: str = "6.2 Write-off memo.txt", memo_type: str = "memo"):
    gl = GL()
    gl.add("2025-12-31", "5300", 92300, "", "Write-off - discontinued coated board", "IA-44")
    letter = "6.2.1 Mill discontinuation letter.txt"
    texts = {memo: "Total write-off: $92,300.00", letter: "The coated line is discontinued; no returns accepted."}
    facts = {memo: _facts(memo, memo_type, "", (), [("total_due", 92300, "Total write-off: $92,300.00")]),
             letter: _facts(letter, "other", "Brookfield Mill", (), (),
                            statements=["The coated line is discontinued; no returns accepted."], signed=True)}
    if not with_outside_doc:
        texts.pop(letter)
        facts.pop(letter)
    adj = claim("W-1", "Discontinued stock write-off", [0, 92300, 0], ["5300"], refs=["DR 6.2"])
    return _run_gl(gl, adj, texts, facts, AdjustmentIntent(adj_id="W-1", keywords=["discontinued", "coated"]))


def test_a_journal_entry_is_supported_by_its_memo_when_an_outside_document_corroborates_it():
    t, a = _write_off(with_outside_doc=True)
    assert FlagCode.NO_DOCUMENT_SUPPORT not in codes(a) and a.treatment == Treatment.ACCEPT
    assert any("journal entry" in f.text for f in a.facts)
    t, a = _write_off(with_outside_doc=False)  # the company's memo alone is a representation
    assert a.treatment == Treatment.REQUEST_INFO


def test_a_journal_entrys_source_can_be_any_company_calculation_not_only_a_memo():
    # A write-down schedule or reserve analysis (not titled "memo") is the company's own calculation too.
    t, a = _write_off(with_outside_doc=True, memo="6.2 Inventory Write-down Schedule.txt", memo_type="other")
    assert FlagCode.NO_DOCUMENT_SUPPORT not in codes(a) and a.treatment == Treatment.ACCEPT
    # An email stating the amount is a representation, not the entry's source document.
    t, a = _write_off(with_outside_doc=True, memo="6.2 Controller email.txt", memo_type="correspondence")
    assert a.treatment == Treatment.REQUEST_INFO


def test_an_outside_bill_of_another_claimed_entry_is_not_attached_to_the_journal_entry():
    gl = GL()
    journal = gl.add("2025-12-31", "5300", 92300, "", "Write-off - discontinued coated board", "IA-44")
    haul = gl.add("2025-12-20", "5300", 4800, "Chatham Waste", "Disposal - discontinued coated board", "CW-9")
    memo, invoice = "6.2 Write-off memo.txt", "6.2.2 Chatham Waste invoice CW-9.txt"
    texts = {memo: "Total write-off: $92,300.00", invoice: "Invoice CW-9. Disposal of coated board. Total $4,800.00"}
    facts = {memo: _facts(memo, "memo", "", (), [("total_due", 92300, "Total write-off: $92,300.00")]),
             invoice: _facts(invoice, "invoice", "Chatham Waste", ["CW-9"], [("total_due", 4800, "Total $4,800.00")])}
    adj = claim("W-2", "Discontinued stock write-off", [0, 97100, 0], ["5300"], refs=["DR 6.2"])
    t, a = _run_gl(gl, adj, texts, facts, AdjustmentIntent(adj_id="W-2", keywords=["discontinued", "coated"]))
    links = {x.entry_id: x.doc_ids for x in a.gl_links}
    assert invoice in links[haul] and invoice not in links[journal]


def test_one_time_pricing_binds_only_the_figure_the_cue_prices():
    from qoe.challenge import _one_off_amounts
    assert _one_off_amounts("The Company will pay a monthly retainer of $3,500, creditable against hourly fees.") == set()
    assert _one_off_amounts("One-time setup fee of $10,000, then $2,500 per month thereafter.") == {D(10000)}
    assert _one_off_amounts("Implementation is a one-time charge; support is $1,200 monthly.") == set()
    assert _one_off_amounts("Implementation is a one-time charge, while support costs $1,200.") == set()
    assert _one_off_amounts("A $10,000 one-time setup fee applies.") == {D(10000)}
    # The installments of a one-time fee are one-time as well.
    assert _one_off_amounts(
        "One-time implementation fee: $64,000.00, invoiced in two milestones of $32,000.00 each."
    ) == {D(64000), D(32000)}


def _creditable_retainer(text: str, term_text: str):
    gl = GL()
    fees = gl.monthly("2025-01", "2025-12", "6400", 3500, "Pell & Ardent LLP", "Monthly retainer")
    doc = "4.9 Pell Ardent engagement letter.txt"
    facts = {doc: _facts(doc, "engagement_letter", "Pell & Ardent LLP", (), [("retainer", 3500, text)],
                         [("retainer", term_text, text)], [text], signed=True)}
    adj = claim("P-1", "Special counsel fees", [0, 42000, 21000], ["6400"], refs=["DR 4.9"])
    intent = AdjustmentIntent(adj_id="P-1", counterparties=["Pell & Ardent"], asserts_nonrecurring=True)
    return _run_gl(gl, adj, {doc: text}, facts, intent), fees


def test_a_retainer_creditable_against_hourly_fees_is_still_a_continuing_obligation():
    (t, a), fees = _creditable_retainer("The Company will pay a monthly retainer of $3,500, creditable against hourly fees.",
                                        "retainer of $3,500.00 per month")
    assert FlagCode.CONTINUING_OBLIGATION in codes(a)
    assert {x.entry_id for x in a.gl_links if x.role == "removed"} == set(fees)
    assert not any("one-time component" in f.text for f in a.facts)


def test_a_retainer_creditable_against_the_success_fee_belongs_to_the_transaction():
    (t, a), _ = _creditable_retainer(
        "The Company will pay a monthly retainer of $3,500, creditable against the Success Fee payable at closing.",
        "retainer of $3,500.00 per month")
    assert FlagCode.CONTINUING_OBLIGATION not in codes(a)


def _owner_pay(docs: dict, monthly: object = 125000, normalized: str = "400000.00", claims=(0, 1100000, 1100000)):
    """Owner pay normalized to a market level; ``docs`` maps doc_id -> (doc_type, party, [(label, amount, text)], signed)."""
    gl = GL()
    pay = gl.monthly("2025-01", "2026-06", "6010", monthly, "J. Varga", "Officer payroll - J. Varga") if monthly else []
    texts = {d: " ".join(x[2] for x in amts) for d, (_, _, amts, _) in docs.items()}
    facts = {d: _facts(d, typ, party, (), amts, signed=signed) for d, (typ, party, amts, signed) in docs.items()}
    adj = claim("N-1", "Owner compensation normalization", list(claims), ["6010"], refs=["DR 2"],
                category=AdjustmentCategory.NORMALIZATION)
    intent = AdjustmentIntent(adj_id="N-1", counterparties=["J. Varga"], is_normalization=True,
                              normalized_amount=normalized, keywords=["officer"])
    return _run_gl(gl, adj, texts, facts, intent), pay


PAY_STUDY = "2.2 Harbor Pay Advisors - CEO pay study.txt"


def test_a_benchmark_far_below_what_the_owner_draws_still_sets_the_level():
    # The owner draws 1.5m a year; market is 300,000 (a fifth of it). What a figure measures is read from its
    # words: the revenue figure and the hourly fee are not levels, the market median is.
    study = ("benchmark", "Harbor Pay Advisors",
             [("line", 76000000, "Peer companies report revenue of about $76 million."),
              ("line", 185, "Our fee for this study is $185 per hour."),
              ("line", 300000, "The 50th percentile total target cash compensation is $300,000.")], None)
    (t, a), _ = _owner_pay({PAY_STUDY: study})
    assert t.normalization.level == D(300000) and t.normalization.benchmark
    assert a.proposed == amounts(0, 1200000, 1200000) and a.treatment == Treatment.REVISE
    assert FlagCode.NORMALIZATION_BENCHMARK_MISSING not in codes(a)


def test_a_rent_benchmark_stated_as_a_rate_and_an_area_sets_the_level():
    broker = [("line", 9, "We conclude a market rent of $9.00 per square foot per year for the 14,000 square feet.")]
    (t, a), related, other = _related_rent(broker)
    # 9.00 x 14,000 = 126,000 a year, the same level the broker would state as a total.
    assert t.normalization.level == D(126000)
    assert a.proposed == amounts(0, -18000, -18000)


def test_a_non_party_document_without_market_words_is_not_a_market_benchmark():
    # Another executive's signed separation agreement states one salary in range; it is not a view of market.
    other_exec = ("separation_agreement", "R. Alvarez", [("line", 350000, "Executive's annual base salary is $350,000.")],
                  True)
    (t, a), _ = _owner_pay({"3.1 Separation agreement - R. Alvarez.txt": other_exec})
    assert FlagCode.NORMALIZATION_BENCHMARK_MISSING in codes(a) and a.treatment == Treatment.REQUEST_INFO
    # The same kind of document speaking of market does set it.
    fmv = ("other", "Coastline Valuation Group",
           [("line", 350000, "The fair market value of the executive's services is $350,000 a year.")], True)
    (t, a), _ = _owner_pay({"2.5 FMV compensation opinion.txt": fmv})
    assert t.normalization.level == D(350000)


def test_a_rent_free_arrangement_is_normalized_to_the_whole_market_level():
    # The company occupies the owner's building rent-free: no rent in the GL, and management deducts the
    # market rent it would pay. The level is the whole normalization, not a gap in the actual cost.
    broker = ("benchmark", "Coastline Realty Advisors",
              [("monthly_fee", 10500, "We conclude a market rent of $10,500 per month.")], True)
    texts = {"2.4 Broker opinion of market rent.txt": broker[2][0][2]}
    facts = {"2.4 Broker opinion of market rent.txt": _facts("2.4 Broker opinion of market rent.txt", broker[0],
                                                             broker[1], (), broker[2], signed=True)}
    gl = GL()
    gl.monthly("2025-01", "2026-06", "6100", 4000, "Harbor Storage", "Rent - overflow site")
    for level, expected in (("126000.00", Treatment.ACCEPT), ("120000.00", Treatment.REVISE)):
        claimed = -D(level)
        adj = claim("R-2", "Rent-free premises", [0, claimed, claimed], ["6100"], refs=["DR 2.4"],
                    category=AdjustmentCategory.NORMALIZATION)
        intent = AdjustmentIntent(adj_id="R-2", counterparties=["Bayfront Holdings"], is_normalization=True,
                                  normalized_amount=level, keywords=["rent"])
        t, a = _run_gl(gl, adj, texts, facts, intent)
        assert FlagCode.NO_GL_SUPPORT not in codes(a) and FlagCode.PARTIAL_GL_SUPPORT not in codes(a)
        assert a.proposed == amounts(0, -126000, -126000) and a.treatment == expected


def test_normalization_keeps_the_owners_unnamed_payroll_journal_in_the_actual_cost():
    # Xero-style: the owner's salary posts as a manual journal with no contact; only the car allowance names
    # the owner. Another employee's pay in the same account names that employee and is not the arrangement.
    gl = GL()
    salary = gl.monthly("2025-01", "2025-12", "6010", 40000, "", "Salary journal - owner")
    allowance = gl.monthly("2025-01", "2025-12", "6010", 1000, "J. Varga", "Car allowance")
    other = gl.monthly("2025-01", "2025-12", "6010", 9000, "M. Chen", "Salary - M. Chen")
    agreement = "2.1 Varga employment agreement.txt"
    text = "The Executive's total annual compensation is $300,000."
    facts = {agreement: _facts(agreement, "employment_agreement", "Harbor Unit Co", (), [("line", 300000, text)],
                               signed=True)}
    adj = claim("N-2", "Owner compensation normalization", [0, 192000, 0], ["6010"], refs=["DR 2.1"],
                category=AdjustmentCategory.NORMALIZATION)
    intent = AdjustmentIntent(adj_id="N-2", counterparties=["J. Varga"], is_normalization=True,
                              normalized_amount="300000.00", keywords=["salary", "officer"])
    t, a = _run_gl(gl, adj, {agreement: text}, facts, intent)
    assert set(t.claimed[FY25]) == set(salary) | set(allowance)
    assert not set(other) & set(t.claimed[FY25])
    assert a.proposed == amounts(0, 192000, 0) and a.treatment == Treatment.ACCEPT
    assert FlagCode.PARTIAL_GL_SUPPORT not in codes(a)


def test_titles_name_an_engagement_only_by_a_typed_reference():
    from qoe.trace import typed_refs
    assert typed_refs("Lease Agreement - 410 Harbor Road") == frozenset()
    assert typed_refs("Proof of Claim Official Form 410") == frozenset()
    assert typed_refs("FY2026 Management Incentive Plan") == frozenset()
    assert typed_refs("Master Services Agreement dated 2024-03-01") == frozenset()
    assert typed_refs("Invoice Aug-24") == frozenset()
    assert typed_refs("Engagement Letter - General Counsel (Matter 100)") == {("matter", "100")}


def test_a_date_in_an_agreements_title_does_not_make_it_about_another_engagement():
    # The subscription bills cite a purchase order; the agreement's title carries its date. The date names no
    # engagement, so the agreement's auto-renewal still contradicts the "one-time" claim.
    gl = GL()
    subs = gl.monthly("2025-01", "2025-12", "6300", 3000, "Nimbus Cloud Systems", "Platform subscription - PO 4471")
    doc = "5.2 Nimbus Master Services Agreement dated 2024-03-01.txt"
    text = "Subscription fee: $3,000.00 per month; the subscription renews automatically."
    facts = {doc: _facts(doc, "contract", "Nimbus Cloud Systems", (), [("monthly_fee", 3000, text)],
                         [("monthly_fee", "monthly fee of $3,000.00", text), ("auto_renew", "renews automatically", text)],
                         [text], signed=True)}
    adj = claim("K-2", "Platform implementation (one-time)", [0, 36000, 18000], ["6300"], refs=["DR 5.2"])
    intent = AdjustmentIntent(adj_id="K-2", counterparties=["Nimbus Cloud Systems"], asserts_nonrecurring=True)
    ai = FakeAI(facts=facts, intents={"K-2": intent}, contradictions={"K-2": [Contradiction(
        doc_id=doc, statement="describes the cost as a subscription that renews automatically.", quote=q(doc, text),
        conflicts_with="one-time", entry_ids=subs)]})
    t, a = run(package(gl, [adj], {doc: text}), ai)["K-2"]
    assert FlagCode.CONTRADICTORY_EVIDENCE in codes(a) or FlagCode.CONTINUING_OBLIGATION in codes(a)
    assert {x.entry_id for x in a.gl_links if x.role == "removed"} == set(subs)
    assert not any("separate engagement" in f.text for f in a.facts)
