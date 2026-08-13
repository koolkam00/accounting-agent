from app.matching import match_invoice
from app.schemas import (
    ExtractedInvoice,
    InvoiceLineItem,
    PolicyConfig,
    PurchaseOrder,
    POLine,
    Receipt,
    ReceiptLine,
    Vendor,
    WorkflowDecision,
)


POLICY = PolicyConfig()


def _fixture(price="10.00", qty="2", recv="2", tax="0.00"):
    inv = ExtractedInvoice(
        vendor_name="Acme",
        vendor_id="V1",
        invoice_number="I1",
        invoice_date="2026-01-01",
        po_number="PO1",
        currency="USD",
        line_items=[
            InvoiceLineItem(
                line_number=1,
                sku="S1",
                description="X",
                quantity=qty,
                unit_price=price,
                line_total=f"{float(price)*float(qty):.2f}",
            )
        ],
        subtotal=f"{float(price)*float(qty):.2f}",
        tax=tax,
        freight="0.00",
        invoice_total=f"{float(price)*float(qty)+float(tax):.2f}",
    )
    po = PurchaseOrder(
        po_id="PO1",
        vendor_id="V1",
        vendor_name="Acme",
        currency="USD",
        status="OPEN",
        lines=[
            POLine(
                line_number=1,
                sku="S1",
                description="X",
                quantity="2",
                unit_price="10.00",
                gl_account="5000",
            )
        ],
    )
    receipts = [
        Receipt(
            receipt_id="R1",
            po_id="PO1",
            lines=[ReceiptLine(sku="S1", quantity_received=recv)],
        )
    ]
    vendor = Vendor(vendor_id="V1", vendor_name="Acme", active=True)
    return inv, po, receipts, vendor


def test_exact_ready():
    inv, po, receipts, vendor = _fixture()
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.READY_FOR_DRAFT
    assert exc == []


def test_price_within_tolerance():
    inv, po, receipts, vendor = _fixture(price="10.01")  # $0.01 tol
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.READY_FOR_DRAFT
    assert exc == []


def test_price_over():
    inv, po, receipts, vendor = _fixture(price="10.20")
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert "PRICE_VARIANCE" in exc


def test_qty_exceeds_receipt():
    inv, po, receipts, vendor = _fixture(recv="1")
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert "QUANTITY_EXCEEDS_RECEIPT" in exc


def test_duplicate():
    inv, po, receipts, vendor = _fixture()
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, True)
    assert "DUPLICATE_INVOICE" in exc


def test_po_missing():
    inv, po, receipts, vendor = _fixture()
    decision, exc, _ = match_invoice(inv, None, [], vendor, POLICY, False)
    assert "PO_NOT_FOUND" in exc


def test_nonzero_tax():
    inv, po, receipts, vendor = _fixture(tax="1.00")
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert "NONZERO_TAX_REVIEW" in exc


def test_exceptions_sorted():
    inv, po, receipts, vendor = _fixture(price="12.00", recv="1", tax="1.00")
    _, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, True)
    assert exc == sorted(exc)
