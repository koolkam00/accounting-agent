import json
import re
from pathlib import Path

import pytest

from app.pilot_match import build_report, read_context, sample_context, sample_pdf
from app.pilot_present import CHECK_LABELS, present_checks


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
    assert checks[0]["detail"] == "SKU-1: invoiced 3 received 0"
    assert checks[1]["detail"] == ""


def test_real_values_and_review_explanation():
    data = json.loads(sample_context())
    context = read_context(sample_context())
    report = build_report(sample_pdf(), context, demo=True)
    checks = report["display_checks"]
    assert any(c["detail"] == "SKU-1001: invoiced 3, ordered 3" for c in checks)
    assert any(c["detail"] == "SKU-1001: invoiced 3, received 3" for c in checks)
    assert any("invoiced unit price 10.00, purchase order unit price 10.00 USD" in c["detail"] for c in checks)
    assert not any(c["detail"] in {"ok", "OPEN"} for c in checks)
    data["receipts"][0]["lines"][0]["quantity_received"] = "0"
    report = build_report(sample_pdf(), read_context(json.dumps(data).encode()), demo=True)
    failed = [c for c in report["display_checks"] if not c["passed"]]
    assert failed == [{"label": "Invoiced quantity exceeds the amount received", "detail": "SKU-1001: invoiced 3, received 0", "passed": False}]
