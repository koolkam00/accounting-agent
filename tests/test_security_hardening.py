"""Hardening of untrusted-input paths: identifiers, decimals, PDF bounds."""

from __future__ import annotations

from decimal import InvalidOperation
from pathlib import Path

import pytest

from app.identifiers import is_safe_case_id, require_safe_case_id
from app.llm_client import MockLLMClient
from app.matching import match_invoice
from app.pdf_text import MAX_PDF_PAGES, PdfTooLargeError, extract_pdf_text
from app.schemas import (
    ExtractedInvoice,
    InvoiceLineItem,
    POLine,
    PolicyConfig,
    PurchaseOrder,
    Vendor,
    WorkflowDecision,
)
from app.validation import to_decimal

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "case_id",
    ["case_001", "upload_001", "a.b-c_d"],
)
def test_safe_case_ids_accepted(case_id: str) -> None:
    assert is_safe_case_id(case_id)
    assert require_safe_case_id(case_id) == case_id


@pytest.mark.parametrize(
    "case_id",
    ["", "..", "../../etc/passwd", "case/../../x", "/abs/path", "a" * 65, ".hidden"],
)
def test_unsafe_case_ids_rejected(case_id: str) -> None:
    assert not is_safe_case_id(case_id)
    with pytest.raises(ValueError):
        require_safe_case_id(case_id)


def test_mock_client_ignores_traversing_case_id(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "expected.json").write_text(
        '{"extraction": {"vendor_name": "Leaked", "line_items": []}}', encoding="utf-8"
    )
    fixture_root = tmp_path / "fixtures" / "development"
    fixture_root.mkdir(parents=True)

    client = MockLLMClient(fixture_root=tmp_path / "fixtures")
    invoice = client.extract_invoice("Invoice text", case_id="../../outside")
    assert invoice.vendor_name != "Leaked"


@pytest.mark.parametrize("value", ["NaN", "-NaN", "sNaN", "Infinity", "-Infinity"])
def test_non_finite_decimals_rejected(value: str) -> None:
    with pytest.raises(InvalidOperation):
        to_decimal(value)


def _po() -> PurchaseOrder:
    return PurchaseOrder(
        po_id="PO-1",
        vendor_id="V1",
        vendor_name="Vendor One",
        currency="USD",
        status="OPEN",
        lines=[
            POLine(
                line_number=1,
                sku="SKU-1001",
                description="d",
                quantity="10",
                unit_price="10.00",
                gl_account="5000",
            )
        ],
    )


def _invoice(quantity: str, unit_price: str = "10.00") -> ExtractedInvoice:
    return ExtractedInvoice(
        vendor_name="Vendor One",
        vendor_id="V1",
        invoice_number="INV-1",
        invoice_date="2026-01-01",
        po_number="PO-1",
        currency="USD",
        subtotal="10.00",
        tax="0.00",
        freight="0.00",
        invoice_total="10.00",
        line_items=[
            InvoiceLineItem(
                line_number=1,
                sku="SKU-1001",
                description="d",
                quantity=quantity,
                unit_price=unit_price,
                line_total="10.00",
            )
        ],
    )


@pytest.mark.parametrize(
    ("quantity", "unit_price"),
    [("NaN", "10.00"), ("1", "NaN"), ("1", "not-a-number"), ("Infinity", "10.00")],
)
def test_match_flags_unparseable_amounts_instead_of_raising(
    quantity: str, unit_price: str
) -> None:
    decision, exceptions, _ = match_invoice(
        invoice=_invoice(quantity, unit_price),
        po=_po(),
        receipts=[],
        vendor=Vendor(vendor_id="V1", vendor_name="Vendor One"),
        policy=PolicyConfig(),
        is_duplicate=False,
    )
    assert decision is WorkflowDecision.HUMAN_REVIEW
    assert "INVOICE_MATH_ERROR" in exceptions


def test_pdf_byte_limit_enforced() -> None:
    pdf = (FIXTURE_ROOT / "development" / "case_001" / "invoice.pdf").read_bytes()
    with pytest.raises(PdfTooLargeError):
        extract_pdf_text(pdf, max_bytes=len(pdf) - 1)


def test_pdf_page_limit_enforced() -> None:
    pdf = (FIXTURE_ROOT / "development" / "case_001" / "invoice.pdf").read_bytes()
    assert extract_pdf_text(pdf).page_count <= MAX_PDF_PAGES
    with pytest.raises(PdfTooLargeError):
        extract_pdf_text(pdf, max_pages=0)
