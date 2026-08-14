import pytest

from app.determinism import classify_case_records, match_fields_all_equal, compute_pairwise_field_disagreements
from scripts.evaluate_determinism import extraction_hash


def _mk_record(case_id: str, extraction: dict, decision: str = "READY_FOR_DRAFT"):
    return {
        "case_id": case_id,
        "ok": True,
        "hash": extraction_hash(extraction),
        "extraction": extraction,
        "decision": decision,
    }


def test_cosmetic_split_payment_terms_and_evidence_only():
    base = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": "INV-1001",
        "invoice_date": "2025-01-20",
        "po_number": "PO-1001",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "sku": "P-001",
                "description": "Pens",
                "quantity": "10",
                "unit_price": "2.50",
                "line_total": "25.00",
                "evidence": {"quote": "Pens x10 @ 2.50", "page": 1},
            }
        ],
        "subtotal": "25.00",
        "tax": "0.00",
        "freight": "0.00",
        "invoice_total": "25.00",
        "payment_terms": "Net 30",
        "evidence": {"invoice_number": {"quote": "INV-1001", "page": 1}},
    }
    # Cosmetic differences: payment_terms and evidence quotes only
    alt = {
        **base,
        "payment_terms": "Net 45",
        "evidence": {"invoice_number": {"quote": "Invoice No. INV-1001", "page": 1}},
        "line_items": [
            {
                **base["line_items"][0],
                "evidence": {"quote": "10 pens @ 2.50", "page": 1},
            }
        ],
    }
    assert extraction_hash(base) != extraction_hash(alt), "hash should differ for cosmetic change"
    recs = [
        _mk_record("case_cosmetic", base, decision="READY_FOR_DRAFT"),
        _mk_record("case_cosmetic", alt, decision="READY_FOR_DRAFT"),
    ]
    cls = classify_case_records("case_cosmetic", recs)
    assert cls.classification == "cosmetic"
    assert cls.decision_equal is True
    assert cls.match_fields_equal is True
    # Field-level disagreements: payment_terms and evidence should disagree, match fields should not
    rates = compute_pairwise_field_disagreements([base, alt])
    assert rates["payment_terms"] == pytest.approx(1.0)
    assert rates["vendor_name"] == pytest.approx(0.0)
    assert rates["line_qty_map"] == pytest.approx(0.0)
    assert rates["evidence_quotes"] == pytest.approx(1.0)


def test_material_split_quantity_change():
    base = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": "INV-2001",
        "invoice_date": "2025-02-10",
        "po_number": "PO-1001",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "sku": "P-001",
                "description": "Pens",
                "quantity": "10",
                "unit_price": "2.50",
                "line_total": "25.00",
            }
        ],
        "subtotal": "25.00",
        "tax": "0.00",
        "freight": "0.00",
        "invoice_total": "25.00",
    }
    # Material change: quantity differs (affects matching)
    alt = {
        **base,
        "line_items": [
            {
                **base["line_items"][0],
                "quantity": "11",
                "line_total": "27.50",
            }
        ],
        "invoice_total": "27.50",
    }
    assert extraction_hash(base) != extraction_hash(alt), "hash should differ for material change"
    recs = [
        _mk_record("case_material", base, decision="READY_FOR_DRAFT"),
        _mk_record("case_material", alt, decision="HUMAN_REVIEW"),
    ]
    cls = classify_case_records("case_material", recs)
    assert cls.classification == "material"
    assert cls.decision_equal is False
    assert cls.match_fields_equal is False
    # Match-field differences should show up
    assert match_fields_all_equal([base, alt]) is False
    rates = compute_pairwise_field_disagreements([base, alt])
    # Disagreement on quantities and totals
    assert rates["line_qty_map"] == pytest.approx(1.0)
    assert rates["line_total_map"] == pytest.approx(1.0)
