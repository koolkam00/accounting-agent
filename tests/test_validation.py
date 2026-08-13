from app.schemas import ExtractedInvoice, InvoiceLineItem, EvidenceSpan, PolicyConfig, Ambiguity
from app.validation import validate_invoice


POLICY = PolicyConfig()


def _inv(**kwargs):
    base = dict(
        vendor_name="Northwind Office Supply LLC",
        vendor_id="V001",
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
                evidence=EvidenceSpan(quote="LINE|1|SKU-1|Item|2|10.00|20.00", page=1),
            )
        ],
        subtotal="20.00",
        tax="0.00",
        freight="0.00",
        invoice_total="20.00",
        payment_terms="Net 30",
        ambiguities=[],
        evidence={
            "vendor_name": EvidenceSpan(quote="Northwind Office Supply LLC", page=1),
            "invoice_number": EvidenceSpan(quote="INV-1", page=1),
            "po_number": EvidenceSpan(quote="PO-1", page=1),
            "invoice_total": EvidenceSpan(quote="20.00", page=1),
        },
    )
    base.update(kwargs)
    return ExtractedInvoice(**base)


CANON = (
    "Vendor: Northwind Office Supply LLC\n"
    "Invoice Number: INV-1\n"
    "PO Number: PO-1\n"
    "LINE|1|SKU-1|Item|2|10.00|20.00\n"
    "Invoice Total: 20.00\n"
)


def test_valid_invoice():
    exc, checks, norm = validate_invoice(_inv(), CANON, POLICY)
    assert exc == []
    assert norm is not None


def test_missing_required():
    exc, _, _ = validate_invoice(_inv(invoice_number=None), CANON, POLICY)
    assert "MISSING_REQUIRED_FIELD" in exc
    assert "MISSING_INVOICE_NUMBER" in exc


def test_evidence_must_match():
    inv = _inv(evidence={"vendor_name": EvidenceSpan(quote="NOT IN TEXT", page=1)})
    exc, _, _ = validate_invoice(inv, CANON, POLICY)
    assert "EVIDENCE_VALIDATION_FAILED" in exc


def test_math_error():
    inv = _inv(invoice_total="99.00")
    exc, _, _ = validate_invoice(inv, CANON, POLICY)
    assert "INVOICE_MATH_ERROR" in exc


def test_ambiguous():
    inv = _inv(ambiguities=[Ambiguity(field="vendor_name", reason="unclear", candidates=[])])
    exc, _, _ = validate_invoice(inv, CANON, POLICY)
    assert "AMBIGUOUS_FIELD" in exc
