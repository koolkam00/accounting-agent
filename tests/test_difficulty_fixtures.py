"""Difficulty pack layout, text-layer hard PDFs, byte stability."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.pdf_text import extract_pdf_text
from scripts.generate_difficulty_packs import HARD_LAYOUTS, hard_plan

REPO = Path(__file__).resolve().parents[1]
DIFF = REPO / "tests" / "fixtures" / "difficulty"


@pytest.mark.parametrize("pack", ["easy", "medium", "hard"])
def test_difficulty_pack_layout(pack):
    root = DIFF / pack
    assert root.is_dir(), f"missing {root}; run scripts/generate_cases.py --difficulty all"
    cases = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_"))
    assert len(cases) == 20
    holdout = 0
    for case_dir in cases:
        assert (case_dir / "invoice.pdf").is_file()
        assert (case_dir / "po.json").is_file()
        assert (case_dir / "receipt.json").is_file()
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        assert expected["case_id"] == case_dir.name
        assert "extraction" in expected
        assert expected["decision"] in ("READY_FOR_DRAFT", "HUMAN_REVIEW")
        assert expected.get("difficulty") == pack
        if expected.get("split") == "holdout":
            holdout += 1
        ext = extract_pdf_text((case_dir / "invoice.pdf").read_bytes())
        assert not ext.ocr_required
        assert any(page.strip() for page in ext.pages)
    assert holdout == 10


def test_hard_layouts_cover_messy_text():
    names = {row[2] for row in hard_plan()}
    assert names == set(HARD_LAYOUTS)
    assert {"strikethrough", "extra_fees", "wrapped", "multipage", "odd_spacing"} <= names


def test_hard_layout_byte_reproducible(tmp_path):
    inv = {
        "vendor_name": "Northwind Office Supply LLC",
        "vendor_id": "V001",
        "invoice_number": "INV-H-TEST",
        "invoice_date": "2026-01-15",
        "po_number": "PO-H-1",
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
    }
    for name, layout in HARD_LAYOUTS.items():
        a = tmp_path / f"{name}_a.pdf"
        b = tmp_path / f"{name}_b.pdf"
        layout(a, inv)
        layout(b, inv)
        assert hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest(), name
        ext = extract_pdf_text(a.read_bytes())
        assert not ext.ocr_required, name


def test_easy_cases_are_ready_gold():
    root = DIFF / "easy"
    for case_dir in sorted(root.glob("case_*")):
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        assert expected["decision"] == "READY_FOR_DRAFT"
        assert expected["scenario"] == "exact_match"


def test_hard_ready_and_review_mock_pipeline(tmp_path):
    """Gold hard cases must match the Python matcher (evidence aligned to PDF text)."""
    import subprocess
    import sys

    from app.adapters.local_erp import LocalERPAdapter
    from app.database import init_db
    from app.llm_client import MockLLMClient
    from app.pipeline import run_case_dir

    db_url = f"sqlite:///{tmp_path / 'hard.db'}"
    subprocess.check_call(
        [
            sys.executable,
            str(REPO / "scripts" / "initialize_database.py"),
            "--reset",
            "--database-url",
            db_url,
            "--fixture-root",
            str(DIFF / "hard"),
        ],
        cwd=str(REPO),
    )
    erp = LocalERPAdapter(init_db(db_url))
    llm = MockLLMClient(fixture_root=DIFF / "hard")
    ready = DIFF / "hard" / "case_001"
    review = DIFF / "hard" / "case_011"
    r1 = run_case_dir(ready, erp=erp, llm=llm, mode="evaluate")
    r2 = run_case_dir(review, erp=erp, llm=llm, mode="evaluate")
    assert r1.decision.value == "READY_FOR_DRAFT"
    assert r1.exception_codes == []
    assert r2.decision.value == "HUMAN_REVIEW"
