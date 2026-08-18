from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.llm_client import MockLLMClient, parse_synthetic_invoice_text


def test_legacy_labeled_layout_extracts_fields_lines_and_evidence():
    text = """Northwind Office Supply LLC
Supplier # V001
Invoice Number: INV-123
PO Number: PO-456
Invoice Date: 2026-01-02
Payment Terms: Net 45
LINE|1|SKU-1001|Copy Paper Case|3|10.00|30.00
LINE|2|SKU-1002|Toner Cartridge Black|2|20.00|40.00
Subtotal: 70.00
Tax: 0.00
Freight: 0.00
Invoice Total: 70.00
"""
    invoice = parse_synthetic_invoice_text(text)

    assert invoice.vendor_name == "Northwind Office Supply LLC"
    assert invoice.vendor_id == "V001"
    assert invoice.invoice_number == "INV-123"
    assert invoice.po_number == "PO-456"
    assert invoice.invoice_date == "2026-01-02"
    assert invoice.payment_terms == "Net 45"
    assert [(line.sku, line.quantity, line.line_total) for line in invoice.line_items] == [
        ("SKU-1001", "3", "30.00"),
        ("SKU-1002", "2", "40.00"),
    ]
    assert invoice.line_items[0].evidence.quote.startswith("LINE|1|")
    assert invoice.evidence["invoice_number"].quote == "INV-123"
    assert invoice.evidence["invoice_total"].quote == "70.00"


def test_messy_layout_normalizes_money_quantity_swaps_and_skips_bad_rows():
    text = """Cedar Ridge Industrial Parts
SKU-1001 Copy Paper Case 2.0 ea USD $1,000.00 $2,000.00
SKU-1002 Toner Cartridge Black 2 ea $50.00 $20.00
SKU-1003 Wrong description 1 ea $3.00 $3.00
SKU-1004 Packing Tape Roll 1 ea $4.00
Invoice Total: $2,020.00
"""
    invoice = parse_synthetic_invoice_text(text)

    assert [(line.sku, line.quantity, line.unit_price, line.line_total) for line in invoice.line_items] == [
        ("SKU-1001", "2", "1000.00", "2000.00"),
        ("SKU-1002", "2", "20.00", "50.00"),
    ]
    assert [line.evidence.quote for line in invoice.line_items] == [
        "SKU-1001 Copy Paper Case 2.0 ea USD $1,000.00 $2,000.00",
        "SKU-1002 Toner Cartridge Black 2 ea $50.00 $20.00",
    ]


def test_distractors_are_ignored_and_labeled_fallbacks_are_used():
    text = """INV-000000 PO-9999
Sold by Blue Harbor Packaging Co
Supplier # V009
Bill No. INV-765
Our order PO-765
Date: 03/04/2026
"""
    invoice = parse_synthetic_invoice_text(text)

    assert invoice.invoice_number == "INV-765"
    assert invoice.po_number == "PO-765"
    assert invoice.vendor_name == "Blue Harbor Packaging Co"
    assert invoice.vendor_id == "V009"
    assert invoice.invoice_date == "2026-03-04"


@pytest.mark.parametrize(
    ("date_text", "expected"),
    [
        ("Invoice Date: 2026-04-05", "2026-04-05"),
        ("posted on 2026-04-06", "2026-04-06"),
        ("issued 04/07/2026", "2026-04-07"),
        ("issued April 8, 2026", "2026-04-08"),
        ("issued 9 April 2026", "2026-04-09"),
    ],
)
def test_date_format_ladder(date_text, expected):
    assert parse_synthetic_invoice_text(date_text).invoice_date == expected


def test_totals_tax_freight_and_terms_branches():
    explicit = parse_synthetic_invoice_text(
        """Merchandise: USD $1,000.00
Tax USD $80.00
Freight USD $20.00
Amount due USD $1,100.00
NET30
"""
    )
    assert explicit.subtotal == "1000.00"
    assert explicit.tax == "80.00"
    assert explicit.freight == "20.00"
    assert explicit.invoice_total == "1100.00"
    assert explicit.payment_terms == "Net 30"

    fallback = parse_synthetic_invoice_text(
        """Net merchandise: $2,000.00
Balance due $2,000.00
tax exempt
freight prepaid
"""
    )
    assert fallback.subtotal == "2000.00"
    assert fallback.invoice_total == "2000.00"
    assert fallback.tax == "0.00"
    assert fallback.freight == "0.00"


def test_ambiguity_marker_adds_vendor_ambiguity():
    invoice = parse_synthetic_invoice_text("Letterhead: Other Corp\nAMBIGUOUS: vendor header")
    assert len(invoice.ambiguities) == 1
    assert invoice.ambiguities[0].field == "vendor_name"


def _write_expected(case_dir: Path, case_id: str) -> dict:
    extraction = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": f"INV-{case_id}",
        "invoice_date": "2026-01-01",
        "po_number": "PO-1",
        "currency": "USD",
        "subtotal": "10.00",
        "tax": "0.00",
        "freight": "0.00",
        "invoice_total": "10.00",
        "payment_terms": "Net 30",
        "line_items": [],
        "ambiguities": [],
        "evidence": {},
    }
    case_dir.mkdir(parents=True)
    (case_dir / "expected.json").write_text(
        json.dumps({"case_id": case_id, "extraction": extraction}), encoding="utf-8"
    )
    return extraction


def test_mock_client_register_and_load_fixture_expected(tmp_path):
    extraction = _write_expected(tmp_path / "case_file", "case_file")
    client = MockLLMClient()
    client.register_expected("registered", {"extraction": extraction})
    assert client.extract_invoice("", case_id="registered").invoice_number == "INV-case_file"

    client.load_fixture_expected(tmp_path / "case_file")
    assert client.extract_invoice("", case_id="case_file").invoice_number == "INV-case_file"
    client.load_fixture_expected(tmp_path / "without_expected")
    assert "without_expected" not in client._expected_by_case


def test_mock_client_scans_fixture_roots_and_falls_back(tmp_path):
    extraction = _write_expected(tmp_path / "development" / "dev_case", "dev_case")
    _write_expected(tmp_path / "difficulty" / "medium" / "medium_case", "medium_case")
    pack_dir = tmp_path / "pack_case"
    pack_extraction = _write_expected(pack_dir, "pack_case")

    client = MockLLMClient(fixture_root=tmp_path)
    assert client.extract_invoice("", case_id="dev_case").invoice_number == "INV-dev_case"
    assert client.extract_invoice("", case_id="medium_case").invoice_number == "INV-medium_case"
    assert client.extract_invoice("", case_id="pack_case").invoice_number == "INV-pack_case"

    root_case_client = MockLLMClient(fixture_root=pack_dir)
    assert root_case_client.extract_invoice("", case_id="anything").invoice_number == "INV-pack_case"

    fallback = client.extract_invoice(
        "Invoice Number: INV-FALLBACK\nSKU-1001 Copy Paper Case 1 ea $2.00 $2.00"
    )
    assert fallback.invoice_number == "INV-FALLBACK"
    assert fallback.line_items[0].sku == "SKU-1001"
