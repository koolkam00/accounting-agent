"""Tests for qoe.challenge: every §5.4 challenge on an in-memory deal, through to treatment.

The deal is synthetic and unrelated to the dev deal catalog: one adjustment per
case type, surrounded by recurring background activity so linking and fitting
have noise to work through.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from qoe.ai_base import AdjustmentIntent, Contradiction, EntryClassification
from qoe.challenge import ChallengeContext, resolve_overlaps, run_challenges
from qoe.money import fmt
from qoe.periods import month_range
from qoe.propose import propose
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


def test_duplicate_posting_inside_the_claim_raises_a_question():
    entries = [
        ("2025-05-02", "6150", 7000, "Gulfline Roofing", "Roof repair", "GR-9"),
        ("2025-05-05", "6150", 7000, "Gulfline Roofing", "Roof repair", "GR-9"),
    ]
    issue = DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING, message="dup",
                             entry_ids=["GL-R6", "GL-R7"])
    (t, a), ids = _small(entries, claim("B-2", "Roof repair", [0, 14000, 0], ["6150"]),
                         intent=AdjustmentIntent(adj_id="B-2", counterparties=["Gulfline Roofing"]), issues=[issue])
    flag = the_flag(a, FlagCode.DUPLICATE_GL_ENTRY)
    assert flag.entry_ids == ids and "2 of the 2 postings are in the claimed set" in flag.message
    assert any(oq.basis == "DUPLICATE_GL_ENTRY" for oq in a.open_questions)


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
