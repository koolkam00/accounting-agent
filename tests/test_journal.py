from app.journal import propose_journal
from app.schemas import ExtractedInvoice, InvoiceLineItem, PurchaseOrder, POLine, WorkflowDecision


def test_balanced_journal():
    inv = ExtractedInvoice(
        vendor_name="Acme",
        vendor_id="V1",
        invoice_number="I1",
        invoice_date="2026-01-01",
        po_number="PO1",
        currency="USD",
        line_items=[
            InvoiceLineItem(
                line_number=1, sku="A", description="a", quantity="1", unit_price="10.00", line_total="10.00"
            ),
            InvoiceLineItem(
                line_number=2, sku="B", description="b", quantity="2", unit_price="5.00", line_total="10.00"
            ),
        ],
        subtotal="20.00",
        tax="0.00",
        freight="0.00",
        invoice_total="20.00",
    )
    po = PurchaseOrder(
        po_id="PO1",
        vendor_id="V1",
        vendor_name="Acme",
        currency="USD",
        status="OPEN",
        lines=[
            POLine(line_number=1, sku="A", description="a", quantity="1", unit_price="10.00", gl_account="5100"),
            POLine(line_number=2, sku="B", description="b", quantity="2", unit_price="5.00", gl_account="5200"),
        ],
    )
    journal, exc, decision = propose_journal(inv, po, ap_account="2000")
    assert exc == []
    assert decision == WorkflowDecision.READY_FOR_DRAFT
    assert journal.balanced
    accounts = [ln.account for ln in journal.lines]
    assert accounts == sorted([a for a in accounts if a != "2000"]) + ["2000"] or "2000" in accounts
    # deterministic order: debit accounts sorted then credit
    debit_accounts = [ln.account for ln in journal.lines if ln.debit != "0.00"]
    assert debit_accounts == sorted(debit_accounts)


def test_unbalanced_triggers_review():
    inv = ExtractedInvoice(
        vendor_name="Acme",
        vendor_id="V1",
        invoice_number="I1",
        invoice_date="2026-01-01",
        po_number="PO1",
        currency="USD",
        line_items=[
            InvoiceLineItem(
                line_number=1, sku="A", description="a", quantity="1", unit_price="10.00", line_total="10.00"
            ),
        ],
        subtotal="10.00",
        tax="0.00",
        freight="0.00",
        invoice_total="15.00",  # mismatch vs lines
    )
    po = PurchaseOrder(
        po_id="PO1",
        vendor_id="V1",
        vendor_name="Acme",
        currency="USD",
        status="OPEN",
        lines=[
            POLine(line_number=1, sku="A", description="a", quantity="1", unit_price="10.00", gl_account="5100"),
        ],
    )
    journal, exc, decision = propose_journal(inv, po)
    assert "UNBALANCED_JOURNAL" in exc
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert journal.balanced is False
