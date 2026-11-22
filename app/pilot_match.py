"""Evaluate one invoice with a customer-supplied PO and receipt snapshot."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import Field, ValidationError

from app.adapters.base import ERPAdapter
from app.llm_client import MockLLMClient, VLLMLLMClient
from app.pipeline import Pipeline
from app.schemas import ExtractedInvoice, PurchaseOrder, Receipt, StrictModel, Vendor
from app.settings import REPO_ROOT

SAMPLE = REPO_ROOT / "tests" / "fixtures" / "development" / "case_001"
MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_CONTEXT_BYTES = 128 * 1024


class PilotInputError(ValueError):
    pass


class MatchContext(StrictModel):
    purchase_order: PurchaseOrder
    receipts: list[Receipt] = Field(min_length=1, max_length=30)


class SnapshotERP(ERPAdapter):
    def __init__(self, context: MatchContext):
        self.po = context.purchase_order
        self.receipts = context.receipts

    def get_vendor(self, vendor_id):
        if vendor_id == self.po.vendor_id:
            return Vendor(vendor_id=vendor_id, vendor_name=self.po.vendor_name)
        return None

    def get_purchase_order(self, po_id):
        return self.po if po_id == self.po.po_id else None

    def get_receipts(self, po_id):
        return self.receipts if po_id == self.po.po_id else []

    def check_duplicate_invoice(self, vendor_id, invoice_number):
        return False  # No ledger history. Omitted from the delivered checks.

    def get_previous_result(self, idempotency_key):
        return None

    def create_draft_bill(self, result):
        raise NotImplementedError

    def attach_source_document(self, draft_bill_id, pdf_bytes, filename):
        raise NotImplementedError

    def record_processed(self, idempotency_key, vendor_id, invoice_number, result):
        raise NotImplementedError


def sample_pdf() -> bytes:
    return (SAMPLE / "invoice.pdf").read_bytes()


def sample_context() -> bytes:
    return json.dumps(
        {
            "purchase_order": json.loads((SAMPLE / "po.json").read_text()),
            "receipts": [json.loads((SAMPLE / "receipt.json").read_text())],
        },
        indent=2,
    ).encode()


def read_context(data: bytes) -> MatchContext:
    if len(data) > MAX_CONTEXT_BYTES:
        raise PilotInputError("The PO and receipts JSON must be at most 128 KB.")
    try:
        context = MatchContext.model_validate_json(data)
    except ValidationError as exc:
        raise PilotInputError("Use the PO and receipts JSON format shown in the example.") from exc
    po, receipts = context.purchase_order, context.receipts
    if (
        po.currency != "USD"
        or not po.po_id.strip()
        or not po.vendor_id.strip()
        or not po.vendor_name.strip()
        or po.status not in {"OPEN", "CLOSED"}
        or not 1 <= len(po.lines) <= 100
        or len({line.sku for line in po.lines}) != len(po.lines)
    ):
        raise PilotInputError("Supply one USD PO with a vendor, a status and distinct SKUs.")
    if any(not line.gl_account.strip() for line in po.lines):
        raise PilotInputError("Enter a GL account for every purchase order line.")
    if (
        len({receipt.receipt_id for receipt in receipts}) != len(receipts)
        or any(
            receipt.po_id != po.po_id or not receipt.receipt_id.strip()
            or not 1 <= len(receipt.lines) <= 100
            or len({line.sku for line in receipt.lines}) != len(receipt.lines)
            for receipt in receipts
        )
    ):
        raise PilotInputError("Use distinct receipt IDs for this PO and distinct SKUs per receipt.")
    amounts = [amount for line in po.lines for amount in (line.quantity, line.unit_price)]
    amounts.extend(line.quantity_received for receipt in receipts for line in receipt.lines)
    if any(not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,4})?", value) for value in amounts):
        raise PilotInputError("Use nonnegative decimals for prices and quantities.")
    return context


def build_report(pdf: bytes, context: MatchContext, *, demo: bool) -> dict:
    if len(pdf) > MAX_PDF_BYTES or not pdf.startswith(b"%PDF-"):
        raise PilotInputError("Choose an invoice PDF no larger than 5 MB.")
    if demo and pdf != sample_pdf():
        raise PilotInputError("This private preview only accepts the provided sample PDF.")
    seeded = (
        ExtractedInvoice.model_validate(json.loads((SAMPLE / "expected.json").read_text())["extraction"])
        if demo else None
    )
    client = (
        MockLLMClient()
        if demo else VLLMLLMClient(timeout=30, max_retries=0, max_output_tokens=4096)
    )
    result = Pipeline(erp=SnapshotERP(context), llm=client).run(
        pdf, preseeded_extraction=seeded, max_pdf_pages=12, max_pdf_chars=30_000
    )
    if result.ocr_required:
        raise PilotInputError("Scanned invoices are not supported. Upload a PDF with selectable text.")
    invoice = result.extracted_invoice
    if not invoice or not invoice.line_items or not invoice.invoice_number:
        raise PilotInputError("The invoice number or line items could not be read. No payment is due.")
    report = result.model_dump(mode="json")
    report["control_checks"] = [
        check for check in report["control_checks"] if check["code"] not in {"DUPLICATE_INVOICE", "VENDOR_ACTIVE"}
    ]
    report["scope"] = "Advisory match against supplied documents only; no duplicate or vendor-master checks, ledger posting or vendor payment."
    report["demo"] = demo
    return report
