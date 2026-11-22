import pytest

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


def test_split_sku_quantities_cannot_exceed_po_or_receipt():
    inv, po, receipts, vendor = _fixture()
    inv.line_items.append(inv.line_items[0].model_copy(update={"line_number": 2}))
    decision, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert exc == ["QUANTITY_EXCEEDS_PO", "QUANTITY_EXCEEDS_RECEIPT"]
    assert {check.detail for check in checks if not check.passed} == {"S1: invoiced 4, ordered 2 → 2 units / 20.00 USD over PO quantity", "S1: invoiced 4, received 2 → 2 units / 20.00 USD not received"}


def test_quantity_credit_does_not_offset_charged_units():
    inv, po, receipts, vendor = _fixture(qty="3")
    inv.line_items.append(
        inv.line_items[0].model_copy(update={"line_number": 2, "quantity": "-1", "line_total": "-10.00"})
    )
    inv.subtotal = inv.invoice_total = "20.00"
    decision, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert exc == ["QUANTITY_EXCEEDS_PO", "QUANTITY_EXCEEDS_RECEIPT"]
    assert {check.detail for check in checks if not check.passed} == {"S1: invoiced 3, ordered 2 → 1 units / 10.00 USD over PO quantity", "S1: invoiced 3, received 2 → 1 units / 10.00 USD not received"}


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


def test_po_closed():
    inv, po, receipts, vendor = _fixture()
    po.status = "CLOSED"
    decision, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert exc == ["PO_CLOSED"]
    assert any(check.detail == "PO is closed (status=CLOSED)" for check in checks)


def test_unmatched_sku_exposure_wording():
    inv, po, receipts, vendor = _fixture(qty="3")
    inv.line_items[0].sku = "SKU-9"
    _, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert "SKU_NOT_FOUND" in exc
    assert any(check.detail == "SKU-9: not on PO → 30.00 USD billed without a PO line" for check in checks)


@pytest.mark.parametrize("field,value", [("quantity", "unknown"), ("unit_price", "unknown"), ("quantity", "NaN"), ("unit_price", "Infinity")])
def test_unmatched_sku_invalid_amount_remains_reviewable(field, value):
    inv, po, receipts, vendor = _fixture()
    inv.line_items[0].sku = "SKU-9"
    setattr(inv.line_items[0], field, value)
    decision, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert "SKU_NOT_FOUND" in exc
    assert any(check.detail == "SKU-9: not on PO" for check in checks)


def test_split_sku_exposure_uses_weighted_invoice_price():
    inv, po, receipts, vendor = _fixture()
    inv.line_items.append(inv.line_items[0].model_copy(update={"unit_price": "20.00"}))
    _, _, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert any(check.detail == "S1: invoiced 4, received 2 → 2 units / 30.00 USD not received" for check in checks)


def test_zero_quantity_has_no_shortage_exposure():
    inv, po, receipts, vendor = _fixture(qty="0", recv="0")
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.READY_FOR_DRAFT
    assert exc == []


def test_price_credit_exposure_direction():
    inv, po, receipts, vendor = _fixture(price="12.00", qty="-2")
    _, _, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert any(check.detail == "S1: qty -2, invoice 12.00 USD vs PO 10.00 USD (tolerance 0.05 USD) → 4.00 USD under PO" for check in checks)


@pytest.mark.parametrize("currency", ["EUR", "GBP"])
def test_exposure_uses_invoice_currency(currency):
    inv, po, receipts, vendor = _fixture(price="12.00", qty="3", recv="1")
    inv.currency = po.currency = currency
    _, _, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    details = {check.code: check.detail for check in checks}
    assert details["PRICE"] == f"S1: qty 3, invoice 12.00 {currency} vs PO 10.00 {currency} (tolerance 0.05 {currency}) → 6.00 {currency} over PO"
    assert details["QTY_RCV"] == f"S1: invoiced 3, received 1 → 2 units / 24.00 {currency} not received"


def test_currency_mismatch_omits_exposure_amounts():
    inv, po, receipts, vendor = _fixture(price="12.00", qty="3", recv="1")
    inv.currency = "EUR"
    inv.line_items.append(inv.line_items[0].model_copy(update={"sku": "SKU-9"}))
    _, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert "CURRENCY_MISMATCH" in exc
    details = {check.code: check.detail for check in checks}
    assert details["PRICE"] == "S1: qty 3, invoice 12.00 EUR vs PO 10.00 USD (tolerance 0.05 USD)"
    assert details["QTY_PO"] == "S1: invoiced 3, ordered 2 → 1 units over PO quantity"
    assert details["QTY_RCV"] == "S1: invoiced 3, received 1 → 2 units not received"
    assert details["SKU"] == "SKU-9: not on PO"


def test_exceptions_sorted():
    inv, po, receipts, vendor = _fixture(price="12.00", recv="1", tax="1.00")
    _, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, True)
    assert exc == sorted(exc)
