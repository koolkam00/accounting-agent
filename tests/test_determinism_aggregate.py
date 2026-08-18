from app.determinism import (
    aggregate_field_disagreements,
    classify_case_records,
    compute_pairwise_field_disagreements,
    flatten_extract_for_disagreement,
    flatten_extract_for_match_fields,
    match_fields_all_equal,
)
from scripts.evaluate_determinism import extraction_hash


def _extract(invoice_number="INV-1", sku="SKU-1"):
    return {
        "vendor_name": "Vendor",
        "invoice_number": invoice_number,
        "line_items": [{"sku": sku, "quantity": "1", "unit_price": "2.00", "line_total": "2.00"}],
        "evidence": {"invoice_number": {"quote": invoice_number, "page": 1}},
    }


def test_aggregate_is_pair_weighted_and_keeps_zero_pair_keys():
    base = _extract()
    changed = _extract(invoice_number="INV-2")
    rates = aggregate_field_disagreements(
        {
            "three_repeats": [base, changed, changed],
            "one_repeat": [base],
            "empty": [],
        }
    )

    assert rates["invoice_number"] == 2 / 3
    assert rates["evidence_quotes"] == 2 / 3
    assert rates["vendor_name"] == 0.0
    assert all(rate == 0.0 for key, rate in rates.items() if key != "invoice_number" and key != "evidence_quotes")


def test_pairwise_empty_and_single_extract_return_all_zeroes():
    empty = compute_pairwise_field_disagreements([])
    single = compute_pairwise_field_disagreements([_extract()])
    assert empty
    assert single.keys() == empty.keys()
    assert set(empty.values()) == {0.0}
    assert set(single.values()) == {0.0}


def test_flatteners_skip_sku_less_lines_and_allow_empty_fields():
    extract = {"line_items": [{"quantity": "9"}, {"sku": "SKU-1", "quantity": "2"}]}
    disagreement = flatten_extract_for_disagreement(extract)
    matching = flatten_extract_for_match_fields(extract)
    assert disagreement["line_skus"] == ["SKU-1"]
    assert disagreement["line_qty_map"] == {"SKU-1": "2"}
    assert matching["line_qty_map"] == {"SKU-1": "2"}
    assert disagreement["evidence_quotes"] == []
    assert flatten_extract_for_disagreement({"line_items": [], "evidence": {}})["line_skus"] is None


def test_classify_unknown_and_material_decision_difference():
    unknown = classify_case_records("none", [{"ok": False}, {"ok": True, "extraction": None}])
    assert unknown.classification == "unknown"
    assert unknown.unique_hashes == 0
    assert unknown.decision_equal is False

    left = _extract()
    right = _extract(invoice_number="INV-2")
    records = [
        {"ok": True, "hash": extraction_hash(left), "extraction": left, "decision": "READY_FOR_DRAFT"},
        {"ok": True, "hash": extraction_hash(right), "extraction": right, "decision": "HUMAN_REVIEW"},
    ]
    material = classify_case_records("material", records)
    assert material.classification == "material"
    assert material.unique_hashes == 2
    assert material.decision_equal is False
    assert material.match_fields_equal is False


def test_match_fields_empty_and_stable_single_hash_classification():
    assert match_fields_all_equal([]) is True
    extract = _extract()
    record = {
        "ok": True,
        "hash": extraction_hash(extract),
        "extraction": extract,
        "decision": "READY_FOR_DRAFT",
    }
    stable = classify_case_records("stable", [record])
    assert stable.classification == "stable"
    assert stable.unique_hashes == 1
