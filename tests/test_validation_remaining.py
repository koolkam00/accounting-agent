from app.schemas import (
    EvidenceSpan,
    ExtractedInvoice,
    InvoiceLineItem,
    PolicyConfig,
    WorkflowDecision,
)
from app.validation import decision_from_exceptions, validate_invoice


POLICY = PolicyConfig()


def _invoice(**updates):
    invoice = ExtractedInvoice(
        vendor_name="Vendor",
        vendor_id="V1",
        invoice_number="INV-1",
        invoice_date="2026-01-01",
        po_number="PO-1",
        currency="USD",
        line_items=[
            InvoiceLineItem(
                line_number=1,
                sku="SKU-1",
                description="Item",
                quantity="2",
                unit_price="10.00",
                line_total="20.00",
                evidence=EvidenceSpan(quote="line", page=1),
            )
        ],
        subtotal="20.00",
        tax="0.00",
        freight="0.00",
        invoice_total="20.00",
        payment_terms="Net 30",
        evidence={},
    )
    return invoice.model_copy(update=updates)


def test_missing_line_items_is_required_field():
    exceptions, checks, _ = validate_invoice(_invoice(line_items=[]), "line", POLICY)
    assert "MISSING_REQUIRED_FIELD" in exceptions
    assert any(check.code == "REQUIRED_FIELDS" and not check.passed for check in checks)


def test_line_item_evidence_quote_must_be_in_canonical_text():
    exceptions, checks, _ = validate_invoice(_invoice(), "canonical text without quote", POLICY)
    assert "EVIDENCE_VALIDATION_FAILED" in exceptions
    assert any(check.code == "EVIDENCE" and not check.passed for check in checks)


def test_line_arithmetic_and_total_arithmetic_mismatches():
    line_bad = _invoice(line_items=[_invoice().line_items[0].model_copy(update={"line_total": "30.00"})])
    exceptions, _, _ = validate_invoice(line_bad, "line", POLICY)
    assert "INVOICE_MATH_ERROR" in exceptions

    subtotal_bad = _invoice(subtotal="19.00")
    exceptions, _, _ = validate_invoice(subtotal_bad, "line", POLICY)
    assert "INVOICE_MATH_ERROR" in exceptions

    total_bad = _invoice(invoice_total="21.00", tax="0.00", freight="0.00")
    exceptions, _, _ = validate_invoice(total_bad, "line", POLICY)
    assert "INVOICE_MATH_ERROR" in exceptions


def test_normalization_exception_returns_original_invoice():
    invalid = _invoice(
        line_items=[
            _invoice().line_items[0].model_copy(update={"unit_price": "not-a-decimal"})
        ]
    )
    _, _, normalized = validate_invoice(invalid, "line", POLICY)
    assert normalized is invalid


def test_incomplete_totals_leave_math_check_in_pass_branch():
    incomplete = _invoice(subtotal=None)
    exceptions, checks, normalized = validate_invoice(incomplete, "line", POLICY)
    assert "MISSING_REQUIRED_FIELD" in exceptions
    assert "INVOICE_MATH_ERROR" not in exceptions
    assert normalized is not None
    assert normalized.subtotal is None
    assert any(check.code == "INVOICE_MATH" and check.passed for check in checks)


def test_decision_from_exceptions_branches():
    assert decision_from_exceptions([]) == WorkflowDecision.READY_FOR_DRAFT
    assert decision_from_exceptions(["INVOICE_MATH_ERROR"]) == WorkflowDecision.HUMAN_REVIEW
