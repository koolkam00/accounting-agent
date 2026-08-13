import hashlib
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.generate_cases import LAYOUTS, build_case, scenario_plan  # noqa: E402


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("case_idx", [1, 16, 21])
def test_regenerate_pdf_stable(case_idx, tmp_path):
    """Generate the same case PDF twice and compare SHA-256."""
    plan = scenario_plan()
    scenario, decision = plan[case_idx - 1]
    # rebuild with fresh RNGs seeded identically via rebuild from seed path inside build_case
    # Use two independent RNGs advanced the same way by calling build_case with Random(SEED)
    # but build_case consumes rng — so construct twice from Random(SEED) only works if
    # we don't share state across cases. For a single case index, advance a seeded RNG
    # identically by replaying prior draws.
    def case_for(idx: int):
        rng = random.Random(20260812)
        c = None
        for i, (sc, dec) in enumerate(plan, start=1):
            c = build_case(i, sc, dec, rng)
            if i == idx:
                return c
        return c

    case = case_for(case_idx)
    p1 = tmp_path / "a.pdf"
    p2 = tmp_path / "b.pdf"
    case["layout"](p1, case["inv"])
    case["layout"](p2, case["inv"])
    assert _sha(p1.read_bytes()) == _sha(p2.read_bytes())


def test_all_layouts_invariant():
    inv = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": "INV-TEST",
        "invoice_date": "2026-01-15",
        "po_number": "PO-1",
        "currency": "USD",
        "payment_terms": "Net 30",
        "line_items": [
            {
                "line_number": 1,
                "sku": "SKU-1001",
                "description": "Copy Paper Case",
                "quantity": "2",
                "unit_price": "10.00",
                "line_total": "20.00",
            }
        ],
        "subtotal": "20.00",
        "tax": "0.00",
        "freight": "0.00",
        "invoice_total": "20.00",
        "ambiguous_marker": False,
    }
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        root = Path(td)
        for layout in LAYOUTS:
            a = root / f"{layout.__name__}_1.pdf"
            b = root / f"{layout.__name__}_2.pdf"
            layout(a, inv)
            layout(b, inv)
            assert _sha(a.read_bytes()) == _sha(b.read_bytes()), layout.__name__


def test_layouts_have_no_machine_block(tmp_path):
    inv = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": "INV-TEST",
        "invoice_date": "2026-01-15",
        "po_number": "PO-1",
        "currency": "USD",
        "payment_terms": "Net 30",
        "line_items": [
            {
                "line_number": 1,
                "sku": "SKU-1001",
                "description": "Copy Paper Case",
                "quantity": "2",
                "unit_price": "10.00",
                "line_total": "20.00",
            }
        ],
        "subtotal": "20.00",
        "tax": "0.00",
        "freight": "0.00",
        "invoice_total": "20.00",
        "ambiguous_marker": False,
    }
    from app.canonicalize import canonicalize_document
    from app.pdf_text import extract_pdf_text

    for layout in LAYOUTS:
        path = tmp_path / f"{layout.__name__}.pdf"
        layout(path, inv)
        pages = extract_pdf_text(path).pages
        text = canonicalize_document(path.read_bytes(), pages).canonical_text
        assert "LINE|" not in text, layout.__name__
        assert "Vendor:" not in text, layout.__name__
        assert "Invoice Number:" not in text, layout.__name__
        assert "PO Number:" not in text, layout.__name__
        assert "Harbor Street Holdings LLC" in text, layout.__name__
        assert "INV-000000" in text, layout.__name__
        assert "PO-9999" in text, layout.__name__


def test_fixture_evidence_quotes_in_canonical_text():
    from app.canonicalize import canonicalize_document
    from app.pdf_text import extract_pdf_text

    root = REPO / "tests" / "fixtures"
    missing = []
    for split in ("development", "holdout"):
        for case_dir in sorted((root / split).glob("case_*")):
            expected = __import__("json").loads((case_dir / "expected.json").read_text())
            pdf = (case_dir / "invoice.pdf").read_bytes()
            pages = extract_pdf_text(pdf).pages
            text = canonicalize_document(pdf, pages).canonical_text
            assert "LINE|" not in text, case_dir.name
            for key, span in expected["extraction"]["evidence"].items():
                if span["quote"] not in text:
                    missing.append((case_dir.name, key, span["quote"]))
            for li in expected["extraction"]["line_items"]:
                if li.get("evidence") and li["evidence"]["quote"] not in text:
                    missing.append((case_dir.name, f"line {li['line_number']}", li["evidence"]["quote"]))
    assert missing == []
