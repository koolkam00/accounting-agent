"""Tests for qoe.ai: the rule-based evidence reader and the OpenAI-compatible LLM wrapper.

Documents are written inline and canonicalized the way ingest does it, so every
quote is checked against the same text the engine will verify against. Vendor
names here are invented and differ from the dev deal catalog on purpose: the
rules must be general.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from qoe.ai import (
    CLASSIFY_ENTRIES_SCHEMA,
    OpenAICompatibleEvidenceAI,
    RuleBasedEvidenceAI,
    _Evidence,
    get_ai,
    load_prompt,
)
from qoe.ai_base import MIN_QUOTE_CHARS, AdjustmentIntent, EvidenceAI, verify_quote
from qoe.pdf_text import canonicalize_page_text
from qoe.schemas import (
    AdjustmentCategory,
    AdjustmentClaim,
    DocFacts,
    EvidenceQuote,
    Flag,
    FlagCode,
    GLEntry,
    Severity,
    SourceDocument,
    DocumentPage,
)

REPO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Sample documents
# ---------------------------------------------------------------------------

LIT_INVOICE = """HARROW & VALE LLP
Attorneys at Law
501 E. Kennedy Blvd., Suite 1400
Tampa, FL 33602

INVOICE

Bill To:
Coastline Climate Services, LLC
88 Industrial Way
Clearwater, FL 33760

Invoice No.: 25-0317
Invoice Date: March 14, 2025
Matter: 3310 – Brennan v. Coastline Climate Services, LLC

For professional services rendered through February 28, 2025
Service period: February 1, 2025 – February 28, 2025

Date        Description                                        Hours     Amount
02/04/2025  Review amended complaint; strategy call with client  6.5   4,225.00
02/19/2025  Draft motion to dismiss                              11.0   7,150.00
02/26/2025  Deposition preparation                                4.9   3,125.00

Total fees                                                              14,500.00
Total Due: $14,500.00

Payment is due within 30 days. Please reference Invoice No. 25-0317 and Matter 3310 with your remittance.

SYNTHETIC — generated for QoE Evidence Review testing
"""

RETAINER_LETTER = """HARROW & VALE LLP
501 E. Kennedy Blvd., Suite 1400, Tampa, FL 33602

March 1, 2023

Mr. D. Okafor
Chief Executive Officer
Coastline Climate Services, LLC
88 Industrial Way
Clearwater, FL 33760

Re: Engagement Letter – General Corporate & Employment Matters
Client-Matter No. 40211-1187

Dear Mr. Okafor:

Thank you for selecting Harrow & Vale LLP to serve as general corporate and employment counsel to Coastline Climate Services, LLC (the "Company"). This letter confirms the terms of our engagement, which we have opened as Matter 1187.

Scope. We will advise the Company on general corporate, contract and employment matters. Litigation is outside the scope of this engagement and will be the subject of a separate engagement letter.

Fees. The Company will pay a fixed retainer of $2,500 per month, billed on the first business day of each month, continuing until terminated by either party on thirty days' written notice. Work outside the retainer scope will be billed at our standard hourly rates.

Very truly yours,
HARROW & VALE LLP
By: /s/ Margaret Vale
Margaret Vale, Partner

ACCEPTED AND AGREED:
Coastline Climate Services, LLC
By: /s/ D. Okafor
Date: March 3, 2023

SYNTHETIC — generated for QoE Evidence Review testing
"""

MSA = """MANAGED SERVICES AGREEMENT

This Managed Services Agreement (the "Agreement") is entered into as of December 12, 2024 (the "Effective Date") by and between Coastline Climate Services, LLC ("Client") and Northgate Systems Group, Inc. ("Provider").

1. Services. Provider will deliver RouteWise licensing, hosting and support services as described in Schedule A.

2. Term. This Agreement has a 36-month initial term commencing January 1, 2025. Thereafter the Agreement renews automatically for successive twelve-month renewal terms unless either party gives ninety days' written notice of non-renewal.

3. Fees. Client shall pay Provider a monthly fee of $8,000.00, invoiced monthly in advance, covering licensing, hosting and support.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.

NORTHGATE SYSTEMS GROUP, INC.
By: /s/ Alan Pierce
Title: Chief Executive Officer

COASTLINE CLIMATE SERVICES, LLC
By: /s/ D. Okafor
Title: CEO

SYNTHETIC — generated for QoE Evidence Review testing
"""

SETTLEMENT = """SETTLEMENT AGREEMENT AND RELEASE

This Settlement Agreement and Release is made and entered into as of November 14, 2025, by and between Jordan Brennan ("Plaintiff") and Coastline Climate Services, LLC ("Defendant") in Brennan v. Coastline Climate Services, LLC, Case No. 24-CA-008812.

1. Settlement Payment. In full and final settlement of all claims, Bayfront Casualty Insurance Company, as Defendant's liability insurer, shall pay Plaintiff the sum of $185,000.00 (the "Settlement Amount") within thirty days of the date of this Agreement. Defendant shall make no payment.

2. Release. Plaintiff releases Defendant from all claims arising from Plaintiff's employment.

Signed: /s/ Jordan Brennan Date: November 14, 2025
Signed: /s/ D. Okafor Date: November 14, 2025

SYNTHETIC — generated for QoE Evidence Review testing
"""

DRAFT_EMPLOYMENT = """DRAFT — FOR DISCUSSION PURPOSES ONLY

EXECUTIVE EMPLOYMENT AGREEMENT

This Executive Employment Agreement is entered into between Coastline Climate Services, LLC (the "Company") and Daniel Okafor (the "Executive"), effective as of the closing of the transaction.

2. Base Salary. The Company shall pay the Executive an annual base salary of $300,000, payable in accordance with the Company's regular payroll practices.

3. Term. Employment is at will.

COMPANY: ______________________
EXECUTIVE: ______________________

SYNTHETIC — generated for QoE Evidence Review testing
"""

INSURANCE_LETTER = """Gulf Harbor Mutual Insurance Company
Claims Department
P.O. Box 4410, Jacksonville, FL 32201

January 28, 2025

Coastline Climate Services, LLC
88 Industrial Way
Clearwater, FL 33760

Re: Claim Settlement – Claim No. HM-24-55120
Policy No. CPP-7781203
Date of Loss: October 9, 2024

Dear Policyholder:

We have completed our review of the above claim for wind and water damage to your warehouse roof. The claim has been settled as follows:

Gross covered loss: $50,000.00
Less deductible: ($10,000.00)
Net payment: $40,000.00

A check for the net payment of $40,000.00 will be issued within ten business days.

Sincerely,
Dana Pruitt
Senior Claims Adjuster

SYNTHETIC — generated for QoE Evidence Review testing
"""

INVENTORY_MEMO = """MEMORANDUM

To: File
From: K. Ostrander, Controller
Date: January 12, 2026
Re: December 2025 year-end physical inventory count

The year-end physical count was completed on December 30, 2025. The count adjustment of $64,000.00 was recorded in December 2025. Consistent with prior years, the year-end count adjustment reflects shrink and obsolete parts identified during the count.

SYNTHETIC — generated for QoE Evidence Review testing
"""

REGISTRATION = """Registration Confirmation
Southeast Mechanical Contractors Summit 2025
Hosted by: Florida Mechanical Contractors Association
Confirmation #: SMCS-25-10442
Date: February 3, 2025

Attendee: D. Okafor, Chief Executive Officer
Company: Coastline Climate Services, LLC
Event dates: March 18, 2025 – March 20, 2025
Location: Orlando, FL

Registration fee: $1,295.00 (paid)
Business purpose: Attending on behalf of Coastline Climate Services, LLC for contractor licensing and new-equipment training sessions.

SYNTHETIC — generated for QoE Evidence Review testing
"""

COO_EMAIL = """From: Lena Park <lpark@coastline-climate.example>
To: D. Okafor <dokafor@coastline-climate.example>
Date: Tue, 10 Mar 2026 08:42:00 -0400
Subject: Dispatch staffing after auto-dispatch go-live

Dan,

Once RouteWise auto-dispatch is live, we plan to reduce the dispatch team by three FTEs, targeting Q3 2026. We have not started any separation conversations yet.

Lena

SYNTHETIC — generated for QoE Evidence Review testing
"""

CONTROLLER_EMAIL = """From: K. Ostrander <kostrander@coastline-climate.example>
To: Finance Team <finance@coastline-climate.example>
Date: March 5, 2025
Subject: RouteWise invoices

Team - please code the Northgate invoices to 6300. This is our RouteWise subscription, billed monthly under the managed services agreement.

Thanks,
K.

SYNTHETIC — generated for QoE Evidence Review testing
"""

SEPARATION = """SEPARATION AGREEMENT AND GENERAL RELEASE

This Separation Agreement is entered into as of January 9, 2026 between Coastline Climate Services, LLC (the "Company") and Taylor Whitfield (the "Employee").

1. Separation Date. The Employee's last day of employment was December 31, 2025.

2. Severance. The Company shall pay the Employee severance of $75,000.00, payable in three monthly installments of $25,000.00 beginning February 2026.

Signed: /s/ Taylor Whitfield
Signed: /s/ D. Okafor

SYNTHETIC — generated for QoE Evidence Review testing
"""


LIT_ENGAGEMENT = """HARROW & VALE LLP
January 10, 2025

Coastline Climate Services, LLC
Attn: D. Okafor

Re: Engagement – Brennan v. Coastline Climate Services, LLC (Matter No. 3310)

Dear Mr. Okafor:

We are pleased to confirm that Coastline Climate Services, LLC (the "Company") has engaged Harrow & Vale LLP to defend the Company in the lawsuit captioned Brennan v. Coastline Climate Services, LLC. Our fees will be based on hourly rates, currently $450 to $650 per hour for partners. We will bill you monthly for services rendered in the prior month.

This engagement is limited to the Brennan matter and is separate from our general corporate engagement under Matter 1187.

Very truly yours,
Harrow & Vale LLP
/s/ Margaret Vale

SYNTHETIC — generated for QoE Evidence Review testing
"""

# Line breaks as a PDF text layer produces them: sentences wrap mid-phrase.
WRAPPED_MEMO = """MEMORANDUM
To: File
From: Controller
Date: January 8, 2026
Re: FY2025 year-end inventory count
The physical inventory count was performed on December 30, 2025, and the resulting count
adjustment of $64,000.00 was recorded to Inventory Adjustments & Write-offs. Consistent with prior
years, the year-end count adjustment reflects shrink and obsolete parts identified during the count.
SYNTHETIC — generated for QoE Evidence Review testing
"""

AGENDA = """Supplier Visit Agenda
Carrier Residential Manufacturing – Tyler, Texas plant
November 12–13, 2025
Attending company: Coastline Climate Services, LLC
Attendees: D. Okafor (CEO), M. Diaz (Operations Manager)
Purpose: Plant tour, new-product training for the 2026 residential line and dealer pricing review.
SYNTHETIC — generated for QoE Evidence Review testing
"""

ADVISOR_LETTER = """KEEL POINT ADVISORS LLC
September 22, 2025

Re: Engagement Letter – Sell-Side Advisory Services

Keel Point Advisors LLC will act as exclusive financial advisor to the Company in connection with a potential sale. The Company will pay a non-refundable retainer of $26,000 upon execution of this letter and a success fee at closing.

Accepted and agreed: /s/ D. Okafor
SYNTHETIC — generated for QoE Evidence Review testing
"""


def _doc(doc_id: str, text: str, media_type: str = "pdf") -> SourceDocument:
    page = canonicalize_page_text(text)
    return SourceDocument(
        doc_id=doc_id,
        relpath=f"documents/{doc_id}",
        media_type=media_type,
        sha256=hashlib.sha256(page.encode()).hexdigest(),
        pages=[DocumentPage(page=1, text=page)],
    )


DOCS = {
    "4.2.1 Harrow Vale Invoice 25-0317.pdf": LIT_INVOICE,
    "4.1 Harrow Vale Engagement Letter Matter 1187.pdf": RETAINER_LETTER,
    "6.1 Northgate Managed Services Agreement.pdf": MSA,
    "4.3 Brennan Settlement Agreement.pdf": SETTLEMENT,
    "2.1 Executive Employment Agreement DRAFT.pdf": DRAFT_EMPLOYMENT,
    "7.2 Gulf Harbor Claim Settlement Letter.pdf": INSURANCE_LETTER,
    "8.1 Year-end Inventory Count Memo.pdf": INVENTORY_MEMO,
    "3.4 SMCS 2025 Registration Confirmation.pdf": REGISTRATION,
    "9.1 COO email dispatch staffing.txt": COO_EMAIL,
    "6.2 Controller email RouteWise.txt": CONTROLLER_EMAIL,
    "5.1 Whitfield Separation Agreement.pdf": SEPARATION,
    "4.1.2 Harrow Vale Litigation Engagement Matter 3310.pdf": LIT_ENGAGEMENT,
    "8.2 Inventory memo wrapped.pdf": WRAPPED_MEMO,
    "3.5 Supplier Visit Agenda.pdf": AGENDA,
    "10.1 Keel Point Engagement Letter.pdf": ADVISOR_LETTER,
}


@pytest.fixture(scope="module")
def docs() -> dict[str, SourceDocument]:
    return {
        doc_id: _doc(doc_id, text, "txt" if doc_id.endswith(".txt") else "pdf") for doc_id, text in DOCS.items()
    }


@pytest.fixture(scope="module")
def ai_and_facts(docs) -> tuple[RuleBasedEvidenceAI, dict[str, DocFacts]]:
    ai = RuleBasedEvidenceAI()
    return ai, {doc_id: ai.extract_facts(doc) for doc_id, doc in docs.items()}


def _all_quotes(f: DocFacts) -> list[EvidenceQuote]:
    return [a.quote for a in f.amounts] + [t.quote for t in f.terms] + list(f.key_statements)


def _amount(f: DocFacts, label: str) -> list[str]:
    return [a.amount for a in f.amounts if a.label == label]


def _terms(f: DocFacts, kind: str) -> list[str]:
    return [t.text for t in f.terms if t.kind == kind]


def _gl(entry_id: str, date: str, account: str, counterparty: str, memo: str, amount: str, doc_number: str = "") -> GLEntry:
    return GLEntry(
        entry_id=entry_id,
        date=date,
        period=date[:7],
        account=account,
        account_name="",
        txn_type="Bill",
        doc_number=doc_number,
        counterparty=counterparty,
        memo=memo,
        amount=amount,
        source_file="gl.csv",
        source_row=int(entry_id.split("R")[-1]),
    )


def _claim(adj_id: str, title: str, category: AdjustmentCategory, description: str = "", raw: str = "",
           accounts: list[str] | None = None, amounts: dict[str, str] | None = None) -> AdjustmentClaim:
    return AdjustmentClaim(
        adj_id=adj_id,
        title=title,
        category_raw=raw or category.value.replace("_", " ").lower(),
        category=category,
        description=description,
        gl_accounts=accounts or [],
        support_refs=[],
        amounts=amounts or {"FY2024": "0.00", "FY2025": "96000.00", "TTM Jun-26": "48000.00"},
        source_row=10,
    )


# ---------------------------------------------------------------------------
# extract_facts
# ---------------------------------------------------------------------------


def test_every_quote_is_verbatim_and_nothing_dropped(docs, ai_and_facts):
    _, facts = ai_and_facts
    for doc_id, f in facts.items():
        assert f.extractor == "rules"
        assert f.dropped_quotes == 0, doc_id
        quotes = _all_quotes(f)
        assert quotes, doc_id
        for q in quotes:
            assert q.doc_id == doc_id
            assert verify_quote(q, docs), (doc_id, q.quote)
            assert "SYNTHETIC" not in q.quote


def test_litigation_invoice_facts(ai_and_facts):
    f = ai_and_facts[1]["4.2.1 Harrow Vale Invoice 25-0317.pdf"]
    assert f.doc_type == "invoice"
    assert f.counterparty == "HARROW & VALE LLP"
    assert f.doc_date == "2025-03-14"
    assert f.reference_numbers[:2] == ["25-0317", "3310"]
    assert _amount(f, "total_due") == ["14500.00"]
    assert (f.service_period_start, f.service_period_end) == ("2025-02-01", "2025-02-28")
    assert f.is_draft is False and f.is_signed is None
    assert f.terms == []
    total = next(a for a in f.amounts if a.label == "total_due")
    assert "14,500.00" in total.quote.quote


def test_retainer_engagement_letter_facts(ai_and_facts):
    f = ai_and_facts[1]["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"]
    assert f.doc_type == "engagement_letter"
    assert f.counterparty == "HARROW & VALE LLP"
    assert f.doc_date == "2023-03-01"
    assert "1187" in f.reference_numbers
    assert _terms(f, "retainer") == ["retainer of $2,500.00 per month"]
    assert _terms(f, "ongoing_services")
    assert "continuing until terminated" in next(t for t in f.terms if t.kind == "ongoing_services").quote.quote
    assert _amount(f, "retainer") == ["2500.00"]
    assert f.is_signed is True and f.is_draft is False


def test_managed_services_agreement_terms(ai_and_facts):
    f = ai_and_facts[1]["6.1 Northgate Managed Services Agreement.pdf"]
    assert f.doc_type == "contract"
    assert f.counterparty == "Northgate Systems Group, Inc."
    assert f.doc_date == "2024-12-12"
    kinds = {t.kind for t in f.terms}
    assert {"monthly_fee", "auto_renew", "term_end"} <= kinds
    term_end = next(t for t in f.terms if t.kind == "term_end")
    assert term_end.text.startswith("term ends 2027-12-31")
    assert "36-month initial term commencing January 1, 2025" in term_end.quote.quote
    assert _terms(f, "monthly_fee") == ["monthly fee of $8,000.00"]
    assert _amount(f, "monthly_fee") == ["8000.00"]
    assert f.is_signed is True


def test_settlement_agreement_facts(ai_and_facts):
    f = ai_and_facts[1]["4.3 Brennan Settlement Agreement.pdf"]
    assert f.doc_type == "settlement_agreement"
    assert f.doc_date == "2025-11-14"
    assert "24-CA-008812" in f.reference_numbers
    assert _amount(f, "settlement_amount") == ["185000.00"]
    assert _terms(f, "one_time")
    assert f.is_signed is True
    assert f.counterparty == "Jordan Brennan"
    assert any("insurer" in q.quote for q in f.key_statements)


def test_draft_unsigned_employment_agreement(ai_and_facts):
    f = ai_and_facts[1]["2.1 Executive Employment Agreement DRAFT.pdf"]
    assert f.doc_type == "contract"
    assert f.is_draft is True
    assert f.is_signed is False
    assert f.counterparty == "Daniel Okafor"
    assert _amount(f, "base_salary") == ["300000.00"]
    assert f.title == "EXECUTIVE EMPLOYMENT AGREEMENT"


def test_insurance_claim_settlement_letter(ai_and_facts):
    f = ai_and_facts[1]["7.2 Gulf Harbor Claim Settlement Letter.pdf"]
    assert f.doc_type == "insurance"
    assert f.counterparty == "Gulf Harbor Mutual Insurance Company"
    assert f.doc_date == "2025-01-28"  # not the date of loss
    assert f.reference_numbers[:2] == ["HM-24-55120", "CPP-7781203"]
    assert _amount(f, "net_payment") == ["40000.00"]
    assert _amount(f, "deductible") == ["10000.00"]
    assert _amount(f, "gross_loss") == ["50000.00"]


def test_inventory_memo_recurrence_statement(ai_and_facts):
    f = ai_and_facts[1]["8.1 Year-end Inventory Count Memo.pdf"]
    assert f.doc_type == "memo"
    assert f.doc_date == "2026-01-12"
    assert any(q.quote.startswith("Consistent with prior years") for q in f.key_statements)
    assert "64000.00" in [a.amount for a in f.amounts]


def test_registration_confirmation(ai_and_facts):
    f = ai_and_facts[1]["3.4 SMCS 2025 Registration Confirmation.pdf"]
    assert f.doc_type == "other"
    assert f.counterparty == "Florida Mechanical Contractors Association"
    assert f.doc_date == "2025-02-03"
    assert "SMCS-25-10442" in f.reference_numbers
    assert (f.service_period_start, f.service_period_end) == ("2025-03-18", "2025-03-20")
    assert any("Business purpose" in q.quote for q in f.key_statements)


def test_emails_are_correspondence_with_statements(ai_and_facts):
    coo = ai_and_facts[1]["9.1 COO email dispatch staffing.txt"]
    assert coo.doc_type == "correspondence"
    assert coo.title == "Dispatch staffing after auto-dispatch go-live"
    assert coo.counterparty == "Lena Park"
    assert coo.doc_date == "2026-03-10"
    assert coo.is_draft is False and coo.is_signed is None
    plan = [q.quote for q in coo.key_statements if "we plan to" in q.quote]
    assert plan and "targeting Q3 2026" in plan[0]
    ctrl = ai_and_facts[1]["6.2 Controller email RouteWise.txt"]
    assert any("subscription" in q.quote for q in ctrl.key_statements)


def test_separation_agreement_installments_not_monthly_fee(ai_and_facts):
    f = ai_and_facts[1]["5.1 Whitfield Separation Agreement.pdf"]
    assert f.doc_type == "separation_agreement"
    assert f.doc_date == "2026-01-09"
    assert _amount(f, "severance") == ["75000.00"]
    assert _terms(f, "installments") == ["payable in 3 installments"]
    assert not _terms(f, "monthly_fee") and not _terms(f, "retainer")
    assert f.counterparty == "Taylor Whitfield"


def test_wrapped_pdf_lines_still_match_phrases(docs, ai_and_facts):
    f = ai_and_facts[1]["8.2 Inventory memo wrapped.pdf"]
    stmt = [q for q in f.key_statements if q.quote.startswith("Consistent with prior\nyears")]
    assert stmt and verify_quote(stmt[0], docs)
    assert "obsolete parts" in stmt[0].quote


def test_agenda_dates_and_upfront_retainer(ai_and_facts):
    agenda = ai_and_facts[1]["3.5 Supplier Visit Agenda.pdf"]
    assert (agenda.service_period_start, agenda.service_period_end) == ("2025-11-12", "2025-11-13")
    assert agenda.counterparty != "Coastline Climate Services, LLC"
    assert any("Plant tour" in q.quote for q in agenda.key_statements)
    advisor = ai_and_facts[1]["10.1 Keel Point Engagement Letter.pdf"]
    assert advisor.doc_type == "engagement_letter"
    assert [(a.label, a.amount) for a in advisor.amounts] == [("fee", "26000.00")]
    assert not [t for t in advisor.terms if t.kind in ("retainer", "monthly_fee", "ongoing_services")]


def test_hourly_rates_and_monthly_billing_are_not_recurring_fees(ai_and_facts):
    f = ai_and_facts[1]["4.1.2 Harrow Vale Litigation Engagement Matter 3310.pdf"]
    assert f.doc_type == "engagement_letter"
    assert f.reference_numbers == ["3310", "1187"]
    assert not [t for t in f.terms if t.kind in ("retainer", "monthly_fee", "ongoing_services")]
    assert "rate" in [a.label for a in f.amounts]


def test_layout_variants_seen_in_pdf_text_layers():
    ai = RuleBasedEvidenceAI()
    invoice = ai.extract_facts(_doc("inv.pdf", """Harrow & Vale LLP
INVOICE
Invoice No.: 25-0418
Client-Matter: 40211-3310
Billing Period: February 1 - March 31, 2025
Description Hours Rate Amount
J. Park, Associate - closing the file 3.00 325.00 975.00
Employment policy review (outside the scope of the monthly retainer) 5,500.00
Total Due This Invoice: $6,475.00
"""))
    assert (invoice.service_period_start, invoice.service_period_end) == ("2025-02-01", "2025-03-31")
    assert "3.00" not in invoice.reference_numbers and "40211-3310" in invoice.reference_numbers
    assert not [t for t in invoice.terms if t.kind in ("retainer", "monthly_fee")]
    confirmation = ai.extract_facts(_doc("conf.pdf", """Southeast Travel Partners
Conference Registration & Travel Confirmation
Confirmation No. STP-250214-3381 | Issued February 14
2025
Event dates: March 10-12, 2025
Total charged to company card 5,600.00
"""))
    assert confirmation.doc_date == "2025-02-14"
    assert confirmation.title == "Conference Registration & Travel Confirmation"
    assert (confirmation.service_period_start, confirmation.service_period_end) == ("2025-03-10", "2025-03-12")
    assert [(a.label, a.amount) for a in confirmation.amounts] == [("amount_paid", "5600.00")]
    letter = ai.extract_facts(_doc("lit.pdf", """Harrow & Vale LLP
Litigation services will be billed monthly at our standard hourly rates ($525 partner, $325 associate).
"""))
    assert letter.terms == [] and {a.label for a in letter.amounts} == {"rate"}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Date: 3 Mar 2025\n", "2025-03-03"),
        ("Date: 03/03/2025\n", "2025-03-03"),
        ("Date: 2025-03-03\n", "2025-03-03"),
        ("Invoice Date: Mar. 3, 2025\n", "2025-03-03"),
    ],
)
def test_date_formats(text, expected):
    doc = _doc("note.txt", "INVOICE\n" + text + "Total Due: $100.00\n", "txt")
    assert RuleBasedEvidenceAI().extract_facts(doc).doc_date == expected


def test_extraction_is_deterministic(docs):
    a = [RuleBasedEvidenceAI().extract_facts(d).model_dump() for d in docs.values()]
    b = [RuleBasedEvidenceAI().extract_facts(d).model_dump() for d in docs.values()]
    assert a == b


def test_empty_document_is_safe():
    doc = SourceDocument(doc_id="empty.pdf", relpath="documents/empty.pdf", media_type="pdf", sha256="x", pages=[])
    f = RuleBasedEvidenceAI().extract_facts(doc)
    assert f.doc_type == "other" and f.amounts == [] and f.dropped_quotes == 0


# ---------------------------------------------------------------------------
# parse_intent
# ---------------------------------------------------------------------------


def test_intent_litigation():
    adj = _claim(
        "A-1",
        "Brennan litigation legal fees",
        AdjustmentCategory.NON_RECURRING,
        "Outside counsel fees (Harrow & Vale LLP) defending Brennan v. Coastline, Matter 3310; the case settled in "
        "November 2025. Non-recurring.",
    )
    intent = RuleBasedEvidenceAI().parse_intent(adj)
    assert intent.event_type == "litigation"
    assert intent.asserts_nonrecurring and not intent.asserts_personal
    assert "Harrow & Vale LLP" in intent.counterparties
    assert {"brennan", "litigation"} <= set(intent.keywords)
    assert "fees" not in intent.keywords and "non-recurring" not in intent.keywords
    assert intent.reference_numbers == ["3310"]
    assert intent.event_months == ["2025-11"]


def test_intent_owner_comp_normalization():
    adj = _claim(
        "A-2",
        "Owner compensation normalization",
        AdjustmentCategory.NORMALIZATION,
        "Normalize CEO D. Okafor's compensation of $660,000 to a market rate of $300,000 per the post-close "
        "employment agreement.",
        raw="Normalization",
    )
    intent = RuleBasedEvidenceAI().parse_intent(adj)
    assert intent.is_normalization and not intent.asserts_personal and not intent.is_pro_forma
    assert intent.normalized_amount == "300000.00"
    assert intent.event_type == "owner_comp"
    assert "D. Okafor" in intent.counterparties


def test_intent_personal_expenses():
    adj = _claim(
        "A-3",
        "Owner personal expenses",
        AdjustmentCategory.OWNER_DISCRETIONARY,
        "Country club dues, a family vehicle lease and owner travel paid by the Company.",
        raw="Owner / discretionary",
    )
    intent = RuleBasedEvidenceAI().parse_intent(adj)
    assert intent.asserts_personal
    assert intent.event_type == "owner_expense"
    assert not intent.asserts_nonrecurring


def test_intent_pro_forma_and_title_case_vendor():
    ai = RuleBasedEvidenceAI()
    pro = ai.parse_intent(_claim(
        "A-4", "Pro Forma Dispatcher Savings", AdjustmentCategory.PRO_FORMA,
        "Run-rate savings from the planned elimination of three dispatcher positions once auto-dispatch is live.",
    ))
    assert pro.is_pro_forma and pro.event_type == "pro_forma_savings"
    assert "dispatcher" in pro.keywords
    search = ai.parse_intent(_claim(
        "A-5", "CFO Search Fee", AdjustmentCategory.NON_RECURRING,
        "Retained search fee paid to Barrow Search Partners for the CFO hire, payable in three installments.",
    ))
    assert search.event_type == "recruiting"
    assert search.counterparties == ["Barrow Search Partners"]
    assert search.asserts_nonrecurring


def test_intent_casualty_and_out_of_period():
    ai = RuleBasedEvidenceAI()
    storm = ai.parse_intent(_claim(
        "A-6", "Storm damage repairs", AdjustmentCategory.NON_RECURRING,
        "Hurricane repairs to the warehouse roof, October–December 2024; insurance claim HM-24-55120.",
    ))
    assert storm.event_type == "casualty"
    assert storm.reference_numbers == ["HM-24-55120"]
    assert storm.event_months == ["2024-10", "2024-11", "2024-12"]
    oop = ai.parse_intent(_claim(
        "A-7", "Prior-year subcontractor true-up", AdjustmentCategory.OUT_OF_PERIOD,
        "Invoice AD-3391 booked in March 2025 relates to 2024 projects.", accounts=["5200"],
    ))
    assert oop.event_type == "out_of_period"
    assert "AD-3391" in oop.reference_numbers
    assert "true-up" in oop.keywords


def test_intent_keywords_never_restate_a_party_name():
    ai = RuleBasedEvidenceAI()
    search = ai.parse_intent(_claim(
        "A-5b", "CFO search fee", AdjustmentCategory.NON_RECURRING,
        "Retained search fee paid to Barrow Search Partners for the CFO hire.",
    ))
    assert search.counterparties == ["Barrow Search Partners"]
    assert "barrow" not in search.keywords and "search" in search.keywords
    lit = ai.parse_intent(_claim(
        "A-1b", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
        "Outside counsel fees (Harrow & Vale LLP) defending Brennan v. Coastline.",
    ))
    assert "Harrow & Vale LLP" in lit.counterparties
    assert not {"harrow", "vale"} & set(lit.keywords)
    assert {"brennan", "litigation"} <= set(lit.keywords)  # a case name is the event, not a vendor


def test_a_document_never_ties_to_an_entry_by_date_alone(ai_and_facts):
    """The inventory memo is dated in December; a same-month entry it does not describe stays untied."""
    ai, facts = ai_and_facts
    adj = _claim("A-9b", "One-time inventory write-off", AdjustmentCategory.NON_RECURRING,
                 "Year-end obsolete inventory write-off.")
    entries = [
        _gl("GL-R310", "2025-12-30", "5400", "Metro Freight", "Freight on parts returns", "1250.00"),
        _gl("GL-R311", "2025-12-31", "5400", "", "Year-end physical count adjustment – obsolete & shrink", "64000.00"),
    ]
    found = ai.find_contradictions(adj, ai.parse_intent(adj), [facts["8.1 Year-end Inventory Count Memo.pdf"]], entries)
    assert found and all("GL-R310" not in c.entry_ids for c in found)


# ---------------------------------------------------------------------------
# find_contradictions
# ---------------------------------------------------------------------------


def _routewise_entries() -> list[GLEntry]:
    months = ["2025-01", "2025-02", "2025-03", "2025-04"]
    out = [_gl(f"GL-R{100 + i}", f"{m}-05", "6300", "Northgate Systems Group", f"RouteWise managed services – {m}",
               "8000.00", f"NG-{i}") for i, m in enumerate(months)]
    out.append(_gl("GL-R200", "2025-02-10", "6300", "Office Depot", "Laptop", "1200.00"))
    return out


def test_one_time_claim_contradicted_by_monthly_fee_agreement(docs, ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-8", "One-time RouteWise implementation", AdjustmentCategory.NON_RECURRING,
                 "One-time implementation of the RouteWise dispatch system.")
    intent = ai.parse_intent(adj)
    entries = _routewise_entries()
    linked = [facts["6.1 Northgate Managed Services Agreement.pdf"], facts["6.2 Controller email RouteWise.txt"]]
    found = ai.find_contradictions(adj, intent, linked, entries)
    assert found
    for c in found:
        assert verify_quote(c.quote, docs)
        assert c.conflicts_with
    msa = [c for c in found if c.doc_id.startswith("6.1")]
    assert msa and all(c.entry_ids == ["GL-R100", "GL-R101", "GL-R102", "GL-R103"] for c in msa)
    assert any("monthly fee" in c.quote.quote for c in msa)
    email = [c for c in found if c.doc_id.startswith("6.2")]
    # The email names the RouteWise service the memos name, so it ties to those entries, not the laptop.
    assert email and "subscription" in email[0].quote.quote
    assert email[0].entry_ids == ["GL-R100", "GL-R101", "GL-R102", "GL-R103"]
    # Statements complete "<document> ...": the engine names the document once.
    assert all(c.statement[:1].islower() and c.doc_id not in c.statement for c in found)


def test_recurrence_memo_contradiction_is_entry_specific(docs, ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-9", "One-time inventory write-off", AdjustmentCategory.NON_RECURRING,
                 "Year-end obsolete inventory write-off.")
    entries = [
        _gl("GL-R302", "2025-12-15", "5400", "", "Scrap sale credit", "300.00"),
        _gl("GL-R300", "2025-12-31", "5400", "", "Year-end physical count adjustment – obsolete & shrink", "64000.00"),
        _gl("GL-R301", "2024-12-31", "5400", "", "Year-end physical count adjustment – obsolete & shrink", "58500.00"),
    ]
    found = ai.find_contradictions(adj, ai.parse_intent(adj), [facts["8.1 Year-end Inventory Count Memo.pdf"]], entries)
    assert len(found) == 1
    assert found[0].quote.quote.startswith("Consistent with prior years")
    # tied by amount and date to the Dec 2025 entry, then to the same series (the memo says it recurs)
    assert found[0].entry_ids == ["GL-R300", "GL-R301"]


def test_personal_claim_contradicted_by_business_purpose(docs, ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-10", "Owner personal expenses", AdjustmentCategory.OWNER_DISCRETIONARY,
                 "Owner travel and club dues run through the Company.")
    entries = [
        _gl("GL-R400", "2025-03-21", "6600", "Delta Air Lines", "Travel – SMCS summit Orlando – D. Okafor", "5600.00"),
        _gl("GL-R401", "2025-03-01", "6700", "Palm Harbor Country Club", "Club dues – D. Okafor", "1100.00"),
        _gl("GL-R402", "2025-09-15", "6600", "Delta Air Lines", "Travel – Atlanta", "5600.00"),
    ]
    found = ai.find_contradictions(adj, ai.parse_intent(adj),
                                   [facts["3.4 SMCS 2025 Registration Confirmation.pdf"]], entries)
    assert found
    assert all(c.entry_ids == ["GL-R400"] for c in found)
    assert all(verify_quote(c.quote, docs) for c in found)


def test_retainer_contradiction_applies_only_to_the_retainer_matter(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-11", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Legal fees defending Brennan v. Coastline. Non-recurring.")
    entries = [
        _gl("GL-R500", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – Brennan v. Coastline – litigation",
            "14500.00", "25-0317"),
        _gl("GL-R501", "2025-03-01", "6400", "Harrow & Vale LLP", "Matter 1187 – monthly retainer – Mar 2025",
            "2500.00", "25-0301"),
        _gl("GL-R502", "2025-04-01", "6400", "Harrow & Vale LLP", "Matter 1187 – monthly retainer – Apr 2025",
            "2500.00", "25-0401"),
    ]
    linked = [facts["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"], facts["4.2.1 Harrow Vale Invoice 25-0317.pdf"],
              facts["4.3 Brennan Settlement Agreement.pdf"]]
    found = ai.find_contradictions(adj, ai.parse_intent(adj), linked, entries)
    assert found
    assert {c.doc_id for c in found} == {"4.1 Harrow Vale Engagement Letter Matter 1187.pdf"}
    assert all(c.entry_ids == ["GL-R501", "GL-R502"] for c in found)


def test_installment_severance_is_not_a_contradiction(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-12", "Severance, former VP Sales", AdjustmentCategory.NON_RECURRING,
                 "Severance paid to T. Whitfield under a separation agreement.")
    entries = [_gl(f"GL-R60{i}", f"2026-0{i + 2}-15", "6000", "", "Severance – T. Whitfield", "25000.00")
               for i in range(3)]
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [facts["5.1 Whitfield Separation Agreement.pdf"]],
                                  entries) == []


def test_normalization_level_mismatch(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-13", "Owner compensation normalization", AdjustmentCategory.NORMALIZATION,
                 "Normalize owner compensation to a market rate of $250,000.")
    found = ai.find_contradictions(adj, ai.parse_intent(adj),
                                   [facts["2.1 Executive Employment Agreement DRAFT.pdf"]], [])
    assert len(found) == 1 and "$300,000" in found[0].statement
    matching = _claim("A-14", "Owner compensation normalization", AdjustmentCategory.NORMALIZATION,
                      "Normalize owner compensation to a market rate of $300,000.")
    assert ai.find_contradictions(matching, ai.parse_intent(matching),
                                  [facts["2.1 Executive Employment Agreement DRAFT.pdf"]], []) == []


# ---------------------------------------------------------------------------
# classify_entries
# ---------------------------------------------------------------------------


def test_classify_litigation_vs_general_matter(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-15", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Legal fees defending Brennan v. Coastline. Non-recurring.")
    intent = ai.parse_intent(adj)
    entries = [
        _gl("GL-R700", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – Brennan v. Coastline",
            "14500.00", "25-0317"),
        _gl("GL-R701", "2025-06-12", "6400", "Harrow & Vale LLP", "Matter 3310 – deposition and motions",
            "18000.00", "25-0612"),
        _gl("GL-R702", "2025-03-01", "6400", "Harrow & Vale LLP", "Matter 1187 – monthly retainer – Mar 2025",
            "2500.00", "25-0301"),
        _gl("GL-R703", "2025-08-20", "6400", "Harrow & Vale LLP", "Matter 1187 – employment policy review",
            "5500.00", "25-0820"),
        _gl("GL-R704", "2025-09-01", "6400", "Harrow & Vale LLP", "Monthly retainer – Sep 2025", "2500.00", "25-0901"),
    ]
    linked = [facts["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"], facts["4.2.1 Harrow Vale Invoice 25-0317.pdf"]]
    result = {c.entry_id: c for c in ai.classify_entries(adj, intent, entries, linked)}
    assert [result[e.entry_id].qualifies for e in entries] == [True, True, False, False, False]
    assert "1187" in result["GL-R702"].reason and "3310" in result["GL-R702"].reason
    assert all(c.reason for c in result.values())
    # the engine only acts on a classification that cites a document about the entry
    assert "4.1 Harrow Vale Engagement Letter Matter 1187.pdf" in result["GL-R702"].doc_ids
    assert result["GL-R700"].doc_ids == ["4.2.1 Harrow Vale Invoice 25-0317.pdf"]


def test_classify_ignores_other_matters_mentioned_in_event_letter(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-15b", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Legal fees defending Brennan v. Coastline.")
    entries = [
        _gl("GL-R710", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – litigation", "14500.00", "25-0317"),
        _gl("GL-R711", "2025-03-01", "6400", "Harrow & Vale LLP", "Matter 1187 – Mar 2025", "2500.00", "25-0301"),
    ]
    linked = [facts["4.1.2 Harrow Vale Litigation Engagement Matter 3310.pdf"],
              facts["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"]]
    result = ai.classify_entries(adj, ai.parse_intent(adj), entries, linked)
    assert [c.qualifies for c in result] == [True, False]
    found = ai.find_contradictions(adj, ai.parse_intent(adj), linked, entries)
    assert found and all(c.entry_ids == ["GL-R711"] for c in found)


def test_classify_personal_vs_business_travel(ai_and_facts):
    ai, facts = ai_and_facts
    adj = _claim("A-16", "Owner personal expenses", AdjustmentCategory.OWNER_DISCRETIONARY,
                 "Owner travel, club dues and family vehicle lease.")
    entries = [
        _gl("GL-R800", "2025-03-01", "6700", "Palm Harbor Country Club", "Club dues – D. Okafor", "1100.00"),
        _gl("GL-R801", "2025-03-05", "6650", "Harbor Auto Finance", "Lease – SUV (M. Okafor, personal)", "1500.00"),
        _gl("GL-R802", "2025-03-21", "6600", "Delta Air Lines", "Travel – SMCS summit Orlando – D. Okafor", "5600.00"),
        _gl("GL-R803", "2025-11-10", "6600", "Delta Air Lines", "Travel – supplier plant visit, Tyler TX", "5600.00"),
        _gl("GL-R804", "2025-03-19", "6600", "Hilton Orlando", "Hotel – D. Okafor", "900.00"),
    ]
    result = {c.entry_id: c for c in ai.classify_entries(
        adj, ai.parse_intent(adj), entries, [facts["3.4 SMCS 2025 Registration Confirmation.pdf"]])}
    # The Orlando hotel falls in the summit week, but nothing else ties it to the registration:
    # date proximity alone is not evidence, so it is left to the reviewer as a personal item.
    assert [result[e.entry_id].qualifies for e in entries] == [True, True, False, False, True]
    assert result["GL-R802"].doc_ids == ["3.4 SMCS 2025 Registration Confirmation.pdf"]
    assert result["GL-R803"].doc_ids == []  # business memo, but no document to verify it against
    assert all('"' not in c.reason for c in result.values())  # reasons cite documents; they do not paste quotes


def test_classify_leaves_clean_claims_alone(ai_and_facts):
    ai, _ = ai_and_facts
    adj = _claim("A-17", "CFO search fee", AdjustmentCategory.NON_RECURRING,
                 "Retained search fee paid to Barrow Search Partners for the CFO hire.")
    entries = [
        _gl(f"GL-R90{i}", d, "6450", "Barrow Search Partners", f"Retained search – CFO – installment {i + 1} of 3",
            "15000.00") for i, d in enumerate(["2025-04-10", "2025-05-10", "2025-07-10"])
    ]
    result = ai.classify_entries(adj, ai.parse_intent(adj), entries, [])
    assert all(c.qualifies for c in result)


# ---------------------------------------------------------------------------
# draft_questions
# ---------------------------------------------------------------------------


def test_draft_questions_are_follow_ups_the_flags_do_not_cover(ai_and_facts):
    """The engine asks one templated question per flag; the AI adds what the documents raise."""
    ai, facts = ai_and_facts
    adj = _claim("A-18", "Storm damage repairs", AdjustmentCategory.NON_RECURRING,
                 amounts={"FY2024": "58000.00", "FY2025": "0.00", "TTM Jun-26": "0.00"})
    flags = [
        Flag(code=FlagCode.OFFSETTING_RECOVERY, severity=Severity.WARNING, message="recovery",
             period_label="FY2025", amount_impact="-40000.00", entry_ids=["GL-R1"],
             doc_ids=["7.2 Gulf Harbor Claim Settlement Letter.pdf"]),
        Flag(code=FlagCode.UNSIGNED_OR_DRAFT_SUPPORT, severity=Severity.WARNING, message="draft",
             doc_ids=["2.1 Executive Employment Agreement DRAFT.pdf"]),
    ]
    questions = ai.draft_questions(adj, flags, list(facts.values()))
    settlement = [q for q in questions if "settlement" in q.lower()]
    assert settlement and "4.3 Brennan Settlement Agreement.pdf" in settlement[0] and "November 14, 2025" in settlement[0]
    assert any("5.1 Whitfield Separation Agreement.pdf" in q and "backfilled" in q for q in questions)
    assert any("10.1 Keel Point Engagement Letter.pdf" in q and "success fee" in q for q in questions)
    # Nothing restates a flag: no recovery or executed-version questions from the AI.
    assert not any("recover" in q.lower() or "executed version" in q.lower() for q in questions)
    for q in questions:
        assert q.endswith("?") and q.count("?") == 1 and len(q) <= 320
    assert questions == list(dict.fromkeys(questions))


def test_draft_questions_no_flags():
    adj = _claim("A-19", "CFO search fee", AdjustmentCategory.NON_RECURRING)
    assert RuleBasedEvidenceAI().draft_questions(adj, [], []) == []


# ---------------------------------------------------------------------------
# LLM path with a fake OpenAI client
# ---------------------------------------------------------------------------


class _FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        content = item if isinstance(item, str) else json.dumps(item)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _fake_client(*responses: object) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=_FakeCompletions(list(responses))))


def _llm_facts_payload() -> dict:
    return {
        "doc_type": "invoice",
        "title": "INVOICE",
        "counterparty": "Harrow & Vale LLP",
        "doc_date": "2025-03-14",
        "reference_numbers": ["25-0317", "3310", "99-9999"],
        "amounts": [
            {"label": "total_due", "amount": "14500.00", "page": 1, "quote": "Total Due: $14,500.00"},
            {"label": "total_due", "amount": "15000.00", "page": 1, "quote": "Total Due: $14,500.00"},
        ],
        "service_period_start": "2025-02-01",
        "service_period_end": "not stated",
        "is_draft": False,
        "is_signed": None,
        "terms": [],
        "key_statements": [
            {"page": 1, "quote": "Payment is due within 30 days."},
            {"page": 1, "quote": "Harrow & Vale guarantees this matter will never recur."},
        ],
    }


def test_llm_extract_facts_verifies_quotes(docs):
    client = _fake_client(_llm_facts_payload())
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    doc = docs["4.2.1 Harrow Vale Invoice 25-0317.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    f = ai.extract_facts(doc)
    assert f.extractor == "llm:fake-model" and ai.name == "llm:fake-model"
    amounts = [a.amount for a in f.amounts]
    assert "14500.00" in amounts and "15000.00" not in amounts  # an amount not in its quote is dropped
    statements = [q.quote for q in f.key_statements]
    assert "Payment is due within 30 days." in statements
    assert not any("guarantees" in q for q in statements)
    assert f.dropped_quotes == 2  # hallucinated statement + unsupported amount
    assert "99-9999" not in f.reference_numbers and {"25-0317", "3310"} <= set(f.reference_numbers)
    # The model gave only a start date; the rules read the stated service period, which stands.
    assert (f.service_period_start, f.service_period_end) == (rules.service_period_start, rules.service_period_end)
    assert all(verify_quote(q, {doc.doc_id: doc}) for q in _all_quotes(f))
    assert ai.fallbacks == []
    call = client.chat.completions.calls[0]
    assert call["temperature"] == 0 and call["seed"] == 42
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["messages"][0]["content"] == load_prompt("extract_facts")
    assert "not stated" in call["messages"][0]["content"]


def test_llm_invalid_json_falls_back_to_rules(docs):
    client = _fake_client("{not json", RuntimeError("connection reset"))
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    doc = docs["6.1 Northgate Managed Services Agreement.pdf"]
    f = ai.extract_facts(doc)
    assert f.extractor == "rules"
    assert f == RuleBasedEvidenceAI().extract_facts(doc)
    adj = _claim("A-20", "One-time RouteWise implementation", AdjustmentCategory.NON_RECURRING)
    intent = ai.parse_intent(adj)
    assert intent == RuleBasedEvidenceAI().parse_intent(adj)
    assert len(ai.fallbacks) == 2
    assert ai.fallbacks[0].startswith("extract_facts[6.1 Northgate Managed Services Agreement.pdf]: JSONDecodeError")
    assert "RuntimeError" in ai.fallbacks[1]


def test_llm_missing_fields_fall_back():
    client = _fake_client({"questions_typo": []})
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    adj = _claim("A-21", "CFO search fee", AdjustmentCategory.NON_RECURRING)
    flag = Flag(code=FlagCode.NO_DOCUMENT_SUPPORT, severity=Severity.WARNING, message="x", period_label="FY2025")
    questions = ai.draft_questions(adj, [flag], [])
    assert questions == RuleBasedEvidenceAI().draft_questions(adj, [flag], [])
    assert ai.fallbacks and "missing fields" in ai.fallbacks[0]


def test_llm_parse_intent_rejects_unstated_values():
    client = _fake_client({
        "counterparties": ["Harrow & Vale LLP", "Invented Partners LLC"],
        "keywords": ["Litigation", "brennan", "Harrow & Vale"],
        "reference_numbers": ["3310", "7777", "331", "33"],
        "event_type": "litigation",
        "asserts_nonrecurring": True,
        "asserts_personal": False,
        "is_pro_forma": False,
        "is_normalization": False,
        "normalized_amount": "123456.00",
        "event_months": ["2025-11", "November"],
        "notes": "clear",
    })
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    adj = _claim("A-22", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Harrow & Vale LLP fees for Matter 3310, settled November 2025.")
    intent = ai.parse_intent(adj)
    assert intent.counterparties == ["Harrow & Vale LLP"]
    assert intent.reference_numbers == ["3310"]
    assert intent.keywords[:2] == ["litigation", "brennan"]  # the firm's name is a counterparty, not a keyword
    assert not any("harrow" in k or "vale" in k for k in intent.keywords)
    assert set(RuleBasedEvidenceAI().parse_intent(adj).keywords) <= set(intent.keywords)  # the rules' terms stay
    assert intent.normalized_amount is None
    assert intent.event_months == ["2025-11"]
    assert intent.notes.startswith("llm:fake-model")


def test_llm_contradictions_drop_hallucinated_quotes(docs):
    msa = docs["6.1 Northgate Managed Services Agreement.pdf"]
    good = "Client shall pay Provider a monthly fee of $8,000.00, invoiced monthly in advance, covering licensing, hosting and support."
    assert good in msa.pages[0].text
    rules_facts = RuleBasedEvidenceAI().extract_facts(msa)
    client = _fake_client(
        _llm_facts_payload() | {"doc_type": "contract", "amounts": [], "key_statements": [], "reference_numbers": [],
                                "counterparty": None, "title": "MANAGED SERVICES AGREEMENT"},
        {"contradictions": [
            {"doc_id": msa.doc_id, "statement": "The MSA charges a monthly fee.", "page": 1, "quote": good,
             "conflicts_with": "one-time", "entry_ids": ["GL-R100", "GL-R999"]},
            {"doc_id": msa.doc_id, "statement": "Invented.", "page": 1, "quote": "This is a one-time fee.",
             "conflicts_with": "one-time", "entry_ids": []},
        ]},
    )
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    ai.extract_facts(msa)  # caches the page text used for verification
    adj = _claim("A-23", "One-time RouteWise implementation", AdjustmentCategory.NON_RECURRING)
    intent = AdjustmentIntent(adj_id="A-23", asserts_nonrecurring=True)
    found = ai.find_contradictions(adj, intent, [rules_facts], _routewise_entries())
    # GL-R999 is unknown; GL-R100 is kept because code sees the tie (monthly fee amount, same vendor).
    assert found[0].quote.quote == good and found[0].entry_ids == ["GL-R100"]
    assert all(c.statement != "Invented." for c in found)
    assert ai.dropped_quotes == 1
    # The rules' own findings are the floor, whatever the model reports.
    rules_found = RuleBasedEvidenceAI().find_contradictions(adj, intent, [rules_facts], _routewise_entries())
    assert {(c.doc_id, c.quote.quote) for c in rules_found} <= {(c.doc_id, c.quote.quote) for c in found}
    sent = json.loads(client.chat.completions.calls[1]["messages"][1]["content"])
    assert sent["documents"][0]["pages"][0]["text"] == msa.pages[0].text


def test_llm_classify_fills_gaps_from_rules():
    entries = [
        _gl("GL-R950", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – Brennan v. Coastline", "14500.00"),
        _gl("GL-R951", "2025-03-01", "6400", "Harrow & Vale LLP", "Matter 1187 – monthly retainer", "2500.00"),
    ]
    client = _fake_client({"classifications": [
        {"entry_id": "GL-R950", "qualifies": True, "reason": "Cites Matter 3310.", "doc_ids": ["nope.pdf"]},
        {"entry_id": "GL-R000", "qualifies": False, "reason": "Unknown entry.", "doc_ids": []},
    ]})
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    adj = _claim("A-24", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING)
    out = ai.classify_entries(adj, RuleBasedEvidenceAI().parse_intent(adj), entries, [])
    assert [c.entry_id for c in out] == ["GL-R950", "GL-R951"]
    assert out[0].reason == "Cites Matter 3310." and out[0].doc_ids == []
    assert out[1].qualifies is False  # filled by the rules: different matter


def test_llm_questions_happy_path():
    client = _fake_client({"questions": ["Please send the executed agreement.", "  ", "Please send the executed agreement."]})
    ai = OpenAICompatibleEvidenceAI("fake-model", client=client)
    adj = _claim("A-25", "Owner compensation normalization", AdjustmentCategory.NORMALIZATION)
    flag = Flag(code=FlagCode.UNSIGNED_OR_DRAFT_SUPPORT, severity=Severity.WARNING, message="draft")
    assert ai.draft_questions(adj, [flag], []) == ["Please send the executed agreement."]
    payload = json.loads(client.chat.completions.calls[0]["messages"][1]["content"])
    assert payload["flags"][0]["code"] == "UNSIGNED_OR_DRAFT_SUPPORT"


def _rules_payload(f: DocFacts) -> dict:
    """The rule-based reading of a document in the LLM schema (what an honest model might return)."""
    return {
        "doc_type": f.doc_type, "title": f.title, "counterparty": f.counterparty, "doc_date": f.doc_date,
        "reference_numbers": list(f.reference_numbers),
        "amounts": [{"label": a.label, "amount": a.amount, "page": a.quote.page, "quote": a.quote.quote} for a in f.amounts],
        "service_period_start": f.service_period_start, "service_period_end": f.service_period_end,
        "is_draft": f.is_draft, "is_signed": f.is_signed,
        "terms": [{"kind": t.kind, "text": t.text, "page": t.quote.page, "quote": t.quote.quote} for t in f.terms],
        "key_statements": [{"page": q.page, "quote": q.quote} for q in f.key_statements],
    }


def test_llm_cannot_mark_a_draft_agreement_signed(docs):
    # Review finding security-llm-unverified-doc-fields (A): a model (or text planted for it) flips the
    # execution status of a DRAFT, and retypes it as an invoice to escape the draft check.
    doc = docs["2.1 Executive Employment Agreement DRAFT.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    assert rules.is_draft and rules.is_signed is False
    payload = _rules_payload(rules) | {"is_draft": False, "is_signed": True, "doc_type": "invoice"}
    f = OpenAICompatibleEvidenceAI("fake-model", client=_fake_client(payload)).extract_facts(doc)
    assert f.is_draft is True and f.is_signed is False
    assert f.doc_type == rules.doc_type


def test_llm_signed_needs_the_rules_or_a_quoted_signature_mark(docs):
    # The rules read no execution status here (no signature block): "signed" needs a verbatim mark.
    doc = docs["3.4 SMCS 2025 Registration Confirmation.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    assert rules.is_signed is None
    claimed = _rules_payload(rules) | {"is_signed": True}
    assert OpenAICompatibleEvidenceAI("m", client=_fake_client(claimed)).extract_facts(doc).is_signed is None
    invented = claimed | {"key_statements": [{"page": 1, "quote": "Signed: /s/ D. Okafor"}]}
    assert OpenAICompatibleEvidenceAI("m", client=_fake_client(invented)).extract_facts(doc).is_signed is None
    approved = _doc("7.9 Approved Invoice.pdf", "INVOICE\nInvoice No.: 77-100\nTotal Due: $1,000.00\nApproved: /s/ Dana Pruitt\n")
    rules = RuleBasedEvidenceAI().extract_facts(approved)
    assert rules.is_signed is None  # the rules read execution status only on agreements
    marked = _rules_payload(rules) | {"is_signed": True, "key_statements": [{"page": 1, "quote": "Approved: /s/ Dana Pruitt"}]}
    assert OpenAICompatibleEvidenceAI("m", client=_fake_client(marked)).extract_facts(approved).is_signed is True


def test_llm_service_period_and_date_must_be_written_in_the_document(docs):
    # Finding security-llm-unverified-doc-fields (B): a service period the text never states moved M-10.
    doc = docs["4.1.2 Harrow Vale Litigation Engagement Matter 3310.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    assert rules.service_period_start is None and rules.service_period_end is None
    invented = _rules_payload(rules) | {"service_period_start": "2025-03-01", "service_period_end": "2025-03-31",
                                        "doc_date": "2025-02-02"}
    f = OpenAICompatibleEvidenceAI("m", client=_fake_client(invented)).extract_facts(doc)
    assert (f.service_period_start, f.service_period_end) == (None, None)
    assert f.doc_date == rules.doc_date
    stated = _rules_payload(rules) | {"service_period_start": "2025-01-10", "service_period_end": None}
    f = OpenAICompatibleEvidenceAI("m", client=_fake_client(stated)).extract_facts(doc)
    assert f.service_period_start == "2025-01-10"  # "January 10, 2025" is written in the letter


def test_llm_rewritten_terms_and_labels_do_not_replace_the_rules_reading(docs):
    # Finding security-llm-unverified-doc-fields (C): kinds, descriptions and labels rewritten while the
    # quotes stay verbatim dropped CONTINUING_OBLIGATION on M-06.
    doc = docs["6.1 Northgate Managed Services Agreement.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    payload = _rules_payload(rules)
    for t in payload["terms"]:
        t["kind"], t["text"] = "other", "monthly fee of $1.00"
    for a in payload["amounts"]:
        a["label"] = "line"
    f = OpenAICompatibleEvidenceAI("m", client=_fake_client(payload)).extract_facts(doc)
    rule_terms = {(t.kind, t.quote.quote) for t in rules.terms}
    assert rule_terms <= {(t.kind, t.quote.quote) for t in f.terms}
    assert {(a.label, a.amount) for a in rules.amounts} <= {(a.label, a.amount) for a in f.amounts}
    # A description may not carry a figure its quote does not state.
    assert not any("$1.00" in t.text for t in f.terms)


def test_llm_titles_and_references_are_checked_against_the_text(docs):
    doc = docs["4.2.1 Harrow Vale Invoice 25-0317.pdf"]
    rules = RuleBasedEvidenceAI().extract_facts(doc)
    payload = _rules_payload(rules) | {"title": "One-time retainer invoice", "reference_numbers": ["331", "ab", "3310"]}
    f = OpenAICompatibleEvidenceAI("m", client=_fake_client(payload)).extract_facts(doc)
    assert f.title == rules.title  # an unstated title would steer document linking
    assert "331" not in f.reference_numbers and "ab" not in f.reference_numbers  # whole tokens, 3+ characters
    assert "3310" in f.reference_numbers


def test_llm_omissions_keep_the_rules_floor(docs, ai_and_facts):
    # Finding security-llm-omission-no-rules-floor: a valid but empty answer ("report nothing") removed
    # challenges. The rules' terms, statements, contradictions and removals now always stand.
    rules_ai, facts = ai_and_facts
    doc = docs["6.1 Northgate Managed Services Agreement.pdf"]
    empty = _rules_payload(facts[doc.doc_id]) | {"terms": [], "key_statements": [], "amounts": []}
    ai = OpenAICompatibleEvidenceAI("m", client=_fake_client(empty, {"contradictions": []}))
    f = ai.extract_facts(doc)
    assert f.terms == facts[doc.doc_id].terms and f.key_statements == facts[doc.doc_id].key_statements
    adj = _claim("A-30", "One-time RouteWise implementation", AdjustmentCategory.NON_RECURRING,
                 "One-time implementation of the RouteWise dispatch system.")
    intent = rules_ai.parse_intent(adj)
    found = ai.find_contradictions(adj, intent, [f], _routewise_entries())
    assert found == rules_ai.find_contradictions(adj, intent, [f], _routewise_entries()) and found

    lit = _claim("A-31", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Legal fees defending Brennan v. Coastline. Non-recurring.")
    entries = [
        _gl("GL-R700", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – Brennan v. Coastline", "14500.00", "25-0317"),
        _gl("GL-R702", "2025-03-01", "6400", "Harrow & Vale LLP", "Matter 1187 – monthly retainer – Mar 2025", "2500.00", "25-0301"),
    ]
    linked = [facts["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"], facts["4.2.1 Harrow Vale Invoice 25-0317.pdf"]]
    all_qualify = {"classifications": [
        {"entry_id": e.entry_id, "qualifies": True, "reason": "fits the basis", "doc_ids": [], "page": None, "quote": ""}
        for e in entries]}
    ai = OpenAICompatibleEvidenceAI("m", client=_fake_client(all_qualify))
    out = {c.entry_id: c for c in ai.classify_entries(lit, rules_ai.parse_intent(lit), entries, linked)}
    assert out["GL-R702"].qualifies is False and "1187" in out["GL-R702"].reason

    intent_payload = {"counterparties": [], "keywords": [], "reference_numbers": [], "event_type": "other",
                      "asserts_nonrecurring": False, "asserts_personal": False, "is_pro_forma": False,
                      "is_normalization": False, "normalized_amount": None, "event_months": [], "notes": ""}
    merged = OpenAICompatibleEvidenceAI("m", client=_fake_client(intent_payload)).parse_intent(lit)
    floor = RuleBasedEvidenceAI().parse_intent(lit)
    assert merged.asserts_nonrecurring and set(floor.keywords) <= set(merged.keywords)
    assert set(floor.counterparties) <= set(merged.counterparties)


def test_llm_trivial_or_unbacked_contradiction_quotes_are_dropped(docs, ai_and_facts):
    # Finding security-trivial-quote-verification: a one-character quote "verified" a contradiction
    # that turned M-04 from ACCEPT to REJECT. Quotes need MIN_QUOTE_CHARS and must back the statement.
    rules_ai, facts = ai_and_facts
    letter = docs["10.1 Keel Point Engagement Letter.pdf"]
    good = "The Company will pay a non-refundable retainer of $26,000 upon execution of this letter and a success fee at closing."
    assert good in letter.pages[0].text
    items = [
        {"doc_id": letter.doc_id, "statement": "shows the search fee is a recurring monthly retainer.", "page": 1,
         "quote": "a", "conflicts_with": "non-recurring", "entry_ids": []},
        {"doc_id": letter.doc_id, "statement": "sets a retainer of $99,000 a month.", "page": 1, "quote": good,
         "conflicts_with": "non-recurring", "entry_ids": []},
        {"doc_id": letter.doc_id, "statement": "describes the payroll as owner compensation.", "page": 1, "quote": good,
         "conflicts_with": "non-recurring", "entry_ids": []},
        {"doc_id": letter.doc_id, "statement": "adds a success fee payable at closing.", "page": 1, "quote": good,
         "conflicts_with": "non-recurring", "entry_ids": []},
    ]
    ai = OpenAICompatibleEvidenceAI("m", client=_fake_client(_rules_payload(facts[letter.doc_id]), {"contradictions": items}))
    ai.extract_facts(letter)
    adj = _claim("A-32", "Sell-side advisory retainer", AdjustmentCategory.NON_RECURRING)
    found = ai.find_contradictions(adj, AdjustmentIntent(adj_id="A-32"), [facts[letter.doc_id]], [])
    assert [c.statement for c in found] == ["adds a success fee payable at closing."]
    assert ai.dropped_quotes == 3  # too short; a figure the quote lacks; nothing in common with the quote


def test_llm_only_removals_must_quote_their_basis(docs, ai_and_facts):
    # Finding security-trivial-quote-verification: qualifies=False with a free-text reason and no quote
    # removed every M-04 entry. Without a verified passage that backs the reason, nothing is removed.
    rules_ai, facts = ai_and_facts
    invoice = docs["4.2.1 Harrow Vale Invoice 25-0317.pdf"]
    adj = _claim("A-33", "Brennan litigation legal fees", AdjustmentCategory.NON_RECURRING,
                 "Legal fees defending Brennan v. Coastline.")
    entries = [
        _gl("GL-R720", "2025-03-14", "6400", "Harrow & Vale LLP", "Matter 3310 – Brennan v. Coastline", "14500.00", "25-0317"),
        _gl("GL-R721", "2025-03-20", "6400", "Harrow & Vale LLP", "Matter 3310 – deposition preparation", "3125.00", "25-0320"),
        _gl("GL-R722", "2025-03-25", "6400", "Harrow & Vale LLP", "Matter 3310 – motion to dismiss", "7150.00", "25-0325"),
    ]
    reply = {"classifications": [
        {"entry_id": "GL-R720", "qualifies": False, "reason": "owner personal expense", "doc_ids": [invoice.doc_id],
         "page": None, "quote": ""},
        {"entry_id": "GL-R721", "qualifies": False, "reason": "Deposition preparation belongs to a different case.",
         "doc_ids": [invoice.doc_id], "page": 1, "quote": "Deposition preparation"},
        {"entry_id": "GL-R722", "qualifies": False, "reason": "Motion practice is outside the claim.",
         "doc_ids": [invoice.doc_id], "page": 1, "quote": "Motion practice is outside the claim."},
    ]}
    ai = OpenAICompatibleEvidenceAI("m", client=_fake_client(_rules_payload(facts[invoice.doc_id]), reply))
    ai.extract_facts(invoice)
    out = {c.entry_id: c for c in ai.classify_entries(adj, rules_ai.parse_intent(adj), entries, [facts[invoice.doc_id]])}
    assert out["GL-R720"].qualifies is False and out["GL-R720"].doc_ids == []  # kept: the engine asks instead
    assert out["GL-R721"].doc_ids == [invoice.doc_id]  # a verbatim passage that carries the reason's subject
    assert out["GL-R722"].doc_ids == []  # the "quote" is not in the document
    assert ai.dropped_quotes == 1


def test_rule_quotes_are_never_shorter_than_verification_accepts():
    doc = _doc("9.9 Short Lines.pdf", "INVOICE\nRef: Q-100\nAmount due\n$950\nThank you\n")
    f = RuleBasedEvidenceAI().extract_facts(doc)
    assert f.dropped_quotes == 0
    for q in _all_quotes(f):
        assert len(q.quote.strip()) >= MIN_QUOTE_CHARS and verify_quote(q, {doc.doc_id: doc})


def test_quotes_checked_against_facts_also_need_the_minimum_length(ai_and_facts):
    _, facts = ai_and_facts
    f = facts["6.1 Northgate Managed Services Agreement.pdf"]
    evidence = _Evidence({})  # no page text cached: checked against the extracted facts' quotes
    assert not evidence.verified(EvidenceQuote(doc_id=f.doc_id, page=1, quote="a"), {f.doc_id: f})
    assert evidence.verified(f.terms[0].quote, {f.doc_id: f})


def test_contradiction_statements_state_facts_not_conclusions(ai_and_facts):
    # Review finding ui-09: "records a business purpose ..., so it is not a personal cost" answered the
    # judgment question inside the facts panel. Statements say what the document says; nothing more.
    ai, facts = ai_and_facts
    personal = _claim("A-34", "Owner personal expenses", AdjustmentCategory.OWNER_DISCRETIONARY,
                      "Owner travel run through the Company.")
    trip = [_gl("GL-R730", "2025-03-21", "6600", "Delta Air Lines", "Travel – SMCS summit Orlando – D. Okafor", "5600.00")]
    found = ai.find_contradictions(personal, ai.parse_intent(personal),
                                   [facts["3.4 SMCS 2025 Registration Confirmation.pdf"]], trip)
    one_time = _claim("A-35", "One-time RouteWise implementation", AdjustmentCategory.NON_RECURRING)
    found += ai.find_contradictions(one_time, ai.parse_intent(one_time),
                                    [facts["6.1 Northgate Managed Services Agreement.pdf"],
                                     facts["4.1 Harrow Vale Engagement Letter Matter 1187.pdf"]], _routewise_entries())
    assert found
    for c in found:
        for inference in ("so it is not", "rather than", "not a one-time", "not one-time", "so the cost"):
            assert inference not in c.statement, c.statement


# ---------------------------------------------------------------------------
# get_ai and prompts
# ---------------------------------------------------------------------------


def test_get_ai_modes(monkeypatch):
    rules = get_ai()
    assert isinstance(rules, RuleBasedEvidenceAI) and isinstance(rules, EvidenceAI) and rules.name == "rules"
    for var in ("QOE_LLM_BASE_URL", "QOE_LLM_API_KEY", "QOE_LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError, match="QOE_LLM_BASE_URL.*QOE_LLM_API_KEY.*QOE_LLM_MODEL"):
        get_ai("llm")
    monkeypatch.setenv("QOE_LLM_BASE_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("QOE_LLM_API_KEY", "EMPTY")
    monkeypatch.setenv("QOE_LLM_MODEL", "qwen-test")
    llm = get_ai("llm")
    assert isinstance(llm, OpenAICompatibleEvidenceAI) and llm.name == "llm:qwen-test"
    assert isinstance(llm, EvidenceAI)
    assert get_ai("llm:other-model").name == "llm:other-model"
    with pytest.raises(ValueError):
        get_ai("magic")


def test_prompts_state_the_boundary():
    for task in ("extract_facts", "parse_intent", "contradictions", "classify_entries", "questions"):
        text = load_prompt(task).lower()
        assert "never compute" in text, task
        assert "not stated" in text, task
        assert "verbatim" in text or task == "parse_intent", task
        # Document text is data, never instructions (finding security-llm-unverified-doc-fields).
        assert "untrusted content" in text and "never instructions" in text, task


def test_classification_schema_asks_for_the_backing_quote():
    props = CLASSIFY_ENTRIES_SCHEMA["properties"]["classifications"]["items"]["properties"]
    assert {"quote", "page"} <= set(props)
    assert "quote" in load_prompt("classify_entries")


def test_no_ap_imports_or_hardcoded_root():
    source = (REPO / "qoe" / "ai.py").read_text()
    assert "from app" not in source and "import app" not in source
    assert "/home/" not in source


# ---------------------------------------------------------------------------
# Rules added for generalization (SPEC §5.2, §5.4)
# ---------------------------------------------------------------------------


def test_intent_normalized_level_stated_per_month_is_annualized():
    # AdjustmentIntent.normalized_amount is an annual level; the narrative states it per month.
    adj = _claim("N-1", "Related-party rent", AdjustmentCategory.NORMALIZATION,
                 "The yard is leased from an owner entity at $9,000 a month; normalized to a market rent of "
                 "$8,500 a month.", raw="Normalization")
    assert RuleBasedEvidenceAI().parse_intent(adj).normalized_amount == "102000.00"
    quarterly = _claim("N-2", "Related-party rent", AdjustmentCategory.NORMALIZATION,
                       "Normalized to a market rent of $25,500 per quarter.", raw="Normalization")
    assert RuleBasedEvidenceAI().parse_intent(quarterly).normalized_amount == "102000.00"


WRITE_OFF_MEMO = """Brookfield Paper Supply, Inc.
MEMORANDUM
TO: CFO
DATE: January 9, 2026
RE: Write-off of discontinued coated-board stock - December 31, 2025
The mill discontinued the coated line and will not take returns, so the remaining stock was scrapped.
Total write-off: $92,300.00, recorded to 5300 on December 31, 2025.
Routine cycle count adjustments (about $2,000 a month) and the annual physical count adjustment are not
part of this write-off.
SYNTHETIC — generated for QoE Evidence Review testing
"""


def test_a_statement_that_sets_routine_activity_apart_is_not_a_contradiction():
    # The memo mentions routine (recurring) adjustments only to exclude them from the write-off it
    # describes: that supports the claim that the write-off is unusual.
    ai = RuleBasedEvidenceAI()
    doc = _doc("6.2 Write-off memo.pdf", WRITE_OFF_MEMO)
    facts = ai.extract_facts(doc)
    adj = _claim("W-1", "Discontinued stock write-off", AdjustmentCategory.NON_RECURRING,
                 "Write-off of discontinued coated-board stock.")
    entries = [_gl("GL-R500", "2025-12-31", "5300", "", "Write-off - discontinued coated-board stock", "92300.00")]
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [facts], entries) == []


@pytest.mark.parametrize(
    "sentence",
    [
        "This agreement automatically renews for successive one-year terms other than as provided in Section 9.",
        "Subscription fees recur monthly for 36 months, excluding the one-time implementation fee.",
        "Recurring monthly subscription per Order Form, apart from implementation services.",
        "Annual maintenance is billed every year, other than in the first year.",
    ],
)
def test_a_qualifier_on_a_recurring_term_does_not_set_the_recurrence_apart(sentence):
    # "other than", "excluding", "apart from" qualify the term; they do not say the recurring activity is
    # not part of the claimed item, so the recurrence still contradicts a one-time claim.
    ai = RuleBasedEvidenceAI()
    doc = _doc("5.2 Platform agreement.pdf", f"PLATFORM SERVICES AGREEMENT\n{sentence}\n"
                                              "SYNTHETIC — generated for QoE Evidence Review testing\n")
    adj = _claim("S-2", "One-time platform implementation", AdjustmentCategory.NON_RECURRING,
                 "One-time implementation of the platform.")
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [ai.extract_facts(doc)], [])


def test_routine_activity_set_apart_from_another_kind_of_item_is_recognised():
    # The negated inclusion names the claimed item with a generic noun ("project"), not the memo's own words.
    ai = RuleBasedEvidenceAI()
    doc = _doc("9.1 Remediation memo.pdf", "MEMORANDUM\nRE: Roof remediation\nThe roof was replaced after the storm.\n"
                                           "Routine annual maintenance visits are not part of this remediation project.\n"
                                           "SYNTHETIC — generated for QoE Evidence Review testing\n")
    adj = _claim("W-2", "Storm roof remediation", AdjustmentCategory.NON_RECURRING, "Roof replacement after the storm.")
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [ai.extract_facts(doc)], []) == []


def test_market_benchmarks_are_classified_as_benchmarks():
    ai = RuleBasedEvidenceAI()
    opinion = _doc("2.4 Broker Opinion of Market Rent - 12 Dock St.pdf",
                   "Harbor Commercial Advisors\nRe: Broker Opinion of Market Rent - 12 Dock Street\n"
                   "We conclude a market rent of $10,500 per month.\nSYNTHETIC — generated for QoE Evidence Review testing\n")
    lease = _doc("2.3 Lease Agreement - 12 Dock St.pdf",
                 "INDUSTRIAL LEASE AGREEMENT\nBase Rent: $9,000.00 per month.\nRent was not the subject of an "
                 "independent appraisal.\nSYNTHETIC — generated for QoE Evidence Review testing\n")
    assert ai.extract_facts(opinion).doc_type == "benchmark"
    assert ai.extract_facts(lease).doc_type == "contract"


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Performance Appraisal - J. Smith 2025", False),
        ("Employee Appraisal Form - Q4", False),
        ("Annual Performance Review - K. Brooks", False),
        ("Fair Market Value Compensation Opinion - Medical Director", True),
        ("FMV Report - Physician Services", True),
        ("MGMA Physician Compensation Survey 2025", True),
        ("Real Estate Appraisal - 12 Dock Street", True),
    ],
)
def test_benchmark_titles_are_read_by_market_meaning(title, expected):
    ai = RuleBasedEvidenceAI()
    doc = _doc(f"2.9 {title}.pdf", f"{title}\nPrepared January 2026.\nSYNTHETIC — generated for QoE Evidence Review testing\n")
    assert (ai.extract_facts(doc).doc_type == "benchmark") is expected


def test_a_city_in_a_letterhead_address_block_is_never_the_counterparty():
    ai = RuleBasedEvidenceAI()
    doc = _doc("6.9 Certificate of Disposal - Brookline Waste.pdf",
               "CERTIFICATE OF DISPOSAL\nBrookline Waste & Recycling | 200 Mill Road\nSpringfield\nGA 31408\n"
               "Pickup date: January 6, 2026\nWe certify that the material was received and disposed of.\n"
               "Signed: /s/ D. Hughes, Site Supervisor\nSYNTHETIC — generated for QoE Evidence Review testing\n")
    assert ai.extract_facts(doc).counterparty == "Brookline Waste & Recycling"


@pytest.mark.parametrize(
    "sentence",
    [
        "Assuming the pilot goes well, we plan to reduce the dispatch team by three FTEs.",
        "If the pilot is successful, the plan is to cut three FTEs from the dispatch team.",
        "The plan is to consolidate the two warehouses next year.",
        "Go-live of the new routing tool: target is Q3 2026.",
        "We haven't said anything to the team yet.",
        "Nothing has been decided on severance.",
        "Once the new system goes live, the order desk will close.",
    ],
)
def test_plan_statements_are_read_in_their_common_paraphrases(sentence):
    from qoe.ai import _PLAN_RE
    assert _PLAN_RE.search(sentence)


@pytest.mark.parametrize(
    "sentence",
    ["Performance targets for the plan year are set by the Board.", "Target annual bonus is 20% of base salary."],
)
def test_targets_that_are_not_plan_dates_are_not_plan_statements(sentence):
    from qoe.ai import _PLAN_RE
    assert not _PLAN_RE.search(sentence)


@pytest.mark.parametrize(
    "sentence",
    [
        "The retainer stays in place until either party ends it on thirty days' written notice.",
        "This agreement remains in effect until either party terminates it.",
        "There is no end date for this engagement.",
        "We will keep billing the monthly retainer until one of us ends it in writing.",
    ],
)
def test_continuing_terms_are_read_in_their_common_paraphrases(sentence):
    from qoe.ai import _ONGOING_RE, _RECURRENCE_RE
    assert _RECURRENCE_RE.search(sentence) and _ONGOING_RE.search(sentence)


def test_the_company_not_being_required_to_fund_is_a_recovery_statement():
    from qoe.ai import _RECOVERY_RE
    assert _RECOVERY_RE.search("The Company is not required to fund any part of the Settlement Payment.")
    assert _RECOVERY_RE.search("The Company has no obligation to fund any part of the Settlement Payment.")


def test_a_rate_review_is_not_quoted_as_recurrence():
    ai = RuleBasedEvidenceAI()
    doc = _doc("4.9 Engagement letter - special counsel.pdf",
               "ENGAGEMENT LETTER\nWe will represent the Company in the arbitration.\nRates are reviewed annually.\n"
               "SYNTHETIC — generated for QoE Evidence Review testing\n")
    adj = _claim("L-9", "Arbitration legal fees", AdjustmentCategory.NON_RECURRING, "One-time arbitration costs.")
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [ai.extract_facts(doc)], []) == []


def test_an_agreement_stating_the_total_level_does_not_contradict_its_base_salary():
    ai = RuleBasedEvidenceAI()
    doc = _doc("2.1 Executive Employment Agreement.pdf",
               "EXECUTIVE EMPLOYMENT AGREEMENT\nThe Company will pay the Executive an annual base salary of $250,000.\n"
               "Target bonus is 20% of base salary. Total target cash compensation is $300,000.\n"
               "By: /s/ A. Lindqvist\nSYNTHETIC — generated for QoE Evidence Review testing\n")
    adj = _claim("N-3", "Owner compensation normalization", AdjustmentCategory.NORMALIZATION,
                 "Owner pay normalized to the $300,000 total target cash in the executed agreement.")
    assert ai.find_contradictions(adj, ai.parse_intent(adj), [ai.extract_facts(doc)], []) == []


def test_a_recurrence_contradiction_quotes_the_priced_term_not_a_heading():
    ai = RuleBasedEvidenceAI()
    doc = _doc("5.1 Order Form OF-88.pdf",
               "ORDER FORM AND SUBSCRIPTION TERMS\nOne-time setup fee: $12,000.00.\n"
               "Subscription fee: $3,000.00 per month, invoiced monthly in advance.\n"
               "SYNTHETIC — generated for QoE Evidence Review testing\n")
    adj = _claim("S-1", "One-time platform setup", AdjustmentCategory.NON_RECURRING, "One-time setup of the platform.")
    found = ai.find_contradictions(adj, ai.parse_intent(adj), [ai.extract_facts(doc)], [])
    assert found and "$3,000.00 per month" in found[0].quote.quote


# ---------------------------------------------------------------------------
# Integration over generated deal packages (skipped when absent)
# ---------------------------------------------------------------------------


def test_dev_deal_documents_quote_verbatim():
    ingest = pytest.importorskip("qoe.ingest")
    deal_dirs = sorted(p for p in (REPO / "data" / "dev").glob("*") if (p / "documents").is_dir())
    if not deal_dirs:
        pytest.skip("no generated dev deals")
    ai = RuleBasedEvidenceAI()
    checked = 0
    for deal_dir in deal_dirs:
        try:
            documents = ingest.read_documents(deal_dir / "documents", deal_dir)
        except Exception as exc:  # pragma: no cover - ingest is built concurrently
            pytest.skip(f"read_documents unavailable: {exc}")
        by_id = {d.doc_id: d for d in documents}
        for doc in documents:
            f = ai.extract_facts(doc)
            assert f.dropped_quotes == 0, doc.doc_id
            assert all(verify_quote(q, by_id) for q in _all_quotes(f)), doc.doc_id
            checked += 1
    assert checked
