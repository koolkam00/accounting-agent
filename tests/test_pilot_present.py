import json
import re
from pathlib import Path

import pytest

from app.pilot_match import build_report, read_context, sample_context, sample_pdf
from app.pilot_present import CHECK_LABELS, present_checks
from app.matching import match_invoice
from app.schemas import ExtractedInvoice, PolicyConfig, Vendor


@pytest.mark.parametrize("passed", [True, False])
@pytest.mark.parametrize("code", CHECK_LABELS)
def test_every_check_has_readable_success_and_failure(code, passed):
    report = {"control_checks": [{"code": code, "passed": passed, "detail": "ok"}]}
    check = present_checks(report, read_context(sample_context()))[0]
    assert check["label"] == CHECK_LABELS[code][0 if passed else 1]
    assert check["detail"] not in {"ok", "OPEN"}
    assert check["passed"] is passed


def test_all_engine_codes_are_covered():
    root = Path(__file__).parents[1] / "app"
    codes = set()
    for name in ["matching.py", "validation.py", "pipeline.py"]:
        codes.update(re.findall(r'code="([A-Z_]+)"', (root / name).read_text()))
    assert codes <= CHECK_LABELS.keys()


def test_empty_unknown_and_failure_details():
    context = read_context(sample_context())
    assert present_checks({}, context) == []
    checks = present_checks({"control_checks": [
        {"code": "NEW_CHECK", "passed": False, "detail": "Unexpected amount: 12"},
        {"code": "NEW_CHECK", "passed": True},
        {"code": "REQUIRED_FIELDS", "passed": False, "detail": "Missing: invoice_date"},
    ]}, context)
    assert checks[0]["detail"] == "NEW_CHECK: Unexpected amount: 12"
    assert checks[1]["detail"] == ""
    assert checks[2]["detail"] == "Missing: invoice_date"


def test_legacy_report_without_context():
    checks = present_checks({"control_checks": [
        {"code": "QTY_RCV", "passed": False, "detail": "SKU-1: inv=3 received=0"},
        {"code": "PO_STATUS", "passed": True, "detail": "OPEN"},
    ]})
    assert checks[0]["detail"] == "SKU-1: invoiced 3, received 0"
    assert checks[1]["detail"] == ""


def test_real_values_and_review_explanation():
    data = json.loads(sample_context())
    context = read_context(sample_context())
    report = build_report(sample_pdf(), context, demo=True)
    checks = report["display_checks"]
    assert any(c["detail"] == "SKU-1001: within tolerance" for c in checks)
    assert any(c["detail"] == "SKU-1008: within tolerance" for c in checks)
    assert not any(c["detail"] in {"ok", "OPEN"} for c in checks)
    data["receipts"][0]["lines"][0]["quantity_received"] = "0"
    report = build_report(sample_pdf(), read_context(json.dumps(data).encode()), demo=True)
    failed = [c for c in report["display_checks"] if not c["passed"]]
    assert failed == [{"label": "Invoiced quantity exceeds the amount received", "detail": "SKU-1001: invoiced 3, received 0 → 3 units / $30.00 not received", "passed": False}]


@pytest.mark.parametrize("quantities", [("2", "2"), ("4", "-1")], ids=["split-sku", "offset-credit"])
def test_quantity_display_uses_engine_detail_for_multiple_lines(quantities):
    context = read_context(sample_context())
    report = build_report(sample_pdf(), context, demo=True)
    invoice = ExtractedInvoice.model_validate(report["extracted_invoice"])
    original = invoice.line_items[0]
    invoice.line_items = [original.model_copy(update={"quantity": quantity}) for quantity in quantities]
    _, _, engine_checks = match_invoice(
        invoice, context.purchase_order, context.receipts,
        Vendor(vendor_id=context.purchase_order.vendor_id, vendor_name=context.purchase_order.vendor_name),
        PolicyConfig(), False,
    )
    report["extracted_invoice"] = invoice.model_dump()
    report["control_checks"] = [c.model_dump() for c in engine_checks if c.code in {"QTY_PO", "QTY_RCV"}]
    displayed = present_checks(report, context)
    for engine, shown in zip(report["control_checks"], displayed):
        if not engine["passed"]:
            assert engine["detail"] in {"SKU-1001: invoiced 4, ordered 3 → 1 units / $10.00 over PO quantity", "SKU-1001: invoiced 4, received 3 → 1 units / $10.00 not received"}
            assert shown["detail"] == engine["detail"]
        else:
            assert engine["detail"] == "SKU-1001: ok"
            assert shown["detail"] == "SKU-1001: within tolerance"


def test_multiline_price_display_preserves_each_engine_price():
    context = read_context(sample_context())
    report = {"extracted_invoice": {"line_items": [
        {"sku": "SKU-1001", "unit_price": "12.00"},
        {"sku": "SKU-1001", "unit_price": "99.00"},
    ]}, "control_checks": [
        {"code": "PRICE", "passed": False, "detail": "SKU-1001: inv=12.00 po=10.00 tol=0.05"},
        {"code": "PRICE", "passed": False, "detail": "SKU-1001: inv=99.00 po=10.00 tol=0.05"},
        {"code": "PRICE", "passed": True, "detail": "SKU-1001: within tolerance"},
        {"code": "PRICE", "passed": False, "detail": "SKU-1001: price unavailable; tol=0.05"},
    ]}
    checks = present_checks(report, context)
    assert checks[0]["detail"] == "SKU-1001: invoiced unit price 12.00, purchase order unit price 10.00, allowed difference 0.05"
    assert checks[1]["detail"] == "SKU-1001: invoiced unit price 99.00, purchase order unit price 10.00, allowed difference 0.05"
    assert checks[2]["detail"] == "SKU-1001: within tolerance"
    assert checks[3]["detail"] == "SKU-1001: price unavailable; allowed difference 0.05"
