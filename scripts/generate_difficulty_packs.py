#!/usr/bin/env python3
"""Generate easy / medium / hard 20-case packs (text-layer ReportLab only).

Does not touch the legacy 50-case seed-20260812 fixtures.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.hashing import sha256_file  # noqa: E402
from app.jsonio import write_json  # noqa: E402
from scripts.generate_cases import (  # noqa: E402
    INACTIVE_VENDOR,
    LAYOUTS,
    VENDORS,
    _setup_canvas,
    build_case,
    layout_classic,
    write_case,
)

DIFF_ROOT = REPO / "tests" / "fixtures" / "difficulty"

SEED_EASY = 2026081201
SEED_MEDIUM = 20260812
SEED_HARD = 2026081203


def _ids(pack: str, idx: int) -> dict:
    letter = {"easy": "E", "medium": "M", "hard": "H"}[pack]
    return {
        "case_id": f"case_{idx:03d}",
        "po_id": f"PO-{letter}-{1000 + idx}",
        "invoice_number": f"INV-{letter}-{2026000 + idx}",
    }


def medium_plan() -> list[tuple[str, str]]:
    """Scaled current-mix: mismatches, tax, duplicates, inactive vendor."""
    plan: list[tuple[str, str]] = []
    plan += [("exact_match", "READY_FOR_DRAFT")] * 5
    plan += [("price_within", "READY_FOR_DRAFT")] * 2
    plan += [("price_over", "HUMAN_REVIEW")] * 2
    plan += [("qty_exceeds_receipt", "HUMAN_REVIEW")] * 2
    plan += [("duplicate", "HUMAN_REVIEW")] * 2
    plan += [("missing_po", "HUMAN_REVIEW")] * 2
    plan += [("math_error", "HUMAN_REVIEW")] * 1
    plan += [("vendor_mismatch", "HUMAN_REVIEW")] * 1
    plan += [("missing_ambiguous", "HUMAN_REVIEW")] * 1
    plan += [("nonzero_tax", "HUMAN_REVIEW")] * 1
    plan += [("inactive_vendor", "HUMAN_REVIEW")] * 1
    assert len(plan) == 20
    return plan


def hard_plan() -> list[tuple[str, str, str]]:
    """(scenario, decision, layout_name). Last 10 are holdout."""
    return [
        ("exact_match", "READY_FOR_DRAFT", "strikethrough"),
        ("exact_match", "READY_FOR_DRAFT", "strikethrough"),
        ("exact_match", "READY_FOR_DRAFT", "multipage"),
        ("exact_match", "READY_FOR_DRAFT", "multipage"),
        ("exact_match", "READY_FOR_DRAFT", "odd_spacing"),
        ("exact_match", "READY_FOR_DRAFT", "odd_spacing"),
        ("exact_match", "READY_FOR_DRAFT", "wrapped"),
        ("price_within", "READY_FOR_DRAFT", "strikethrough"),
        ("price_within", "READY_FOR_DRAFT", "multipage"),
        ("exact_match", "READY_FOR_DRAFT", "wrapped"),
        ("extra_fees", "HUMAN_REVIEW", "extra_fees"),
        ("extra_fees", "HUMAN_REVIEW", "extra_fees"),
        ("extra_fees", "HUMAN_REVIEW", "wrapped"),
        ("missing_po", "HUMAN_REVIEW", "wrapped"),
        ("missing_po", "HUMAN_REVIEW", "multipage"),
        ("missing_po", "HUMAN_REVIEW", "odd_spacing"),
        ("math_error", "HUMAN_REVIEW", "strikethrough"),
        ("math_error", "HUMAN_REVIEW", "odd_spacing"),
        ("vendor_mismatch", "HUMAN_REVIEW", "multipage"),
        ("price_over", "HUMAN_REVIEW", "wrapped"),
    ]


# --- Hard layouts: text-layer only, no machine-readable LINE| block ---
# Gold lives in expected.json. Live LLM must read the messy presentation.


def _header(c: canvas.Canvas, inv: dict, title: str) -> None:
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 740, title)
    c.setFont("Helvetica", 10)
    c.drawString(72, 722, inv["vendor_name"])
    c.drawString(72, 708, f"Vendor ID {inv['vendor_id']}")
    c.drawString(320, 722, f"Invoice {inv['invoice_number']}")
    c.drawString(320, 708, f"Date {inv['invoice_date']}")


def layout_strikethrough(path: Path, inv: dict) -> None:
    """Struck-through decoy totals; true amounts remain as text."""
    c = _setup_canvas(path)
    _header(c, inv, "INVOICE (REVISED)")
    y = 680
    c.setFont("Helvetica", 10)
    fields = [
        ("PO Number", inv["po_number"]),
        ("Currency", inv["currency"]),
        ("Payment Terms", inv["payment_terms"]),
    ]
    for label, val in fields:
        c.drawString(72, y, f"{label}: {val}")
        y -= 16
    y -= 8
    c.setFont("Helvetica-Bold", 9)
    c.drawString(72, y, "SKU")
    c.drawString(160, y, "Description")
    c.drawString(340, y, "Qty")
    c.drawString(390, y, "Price")
    c.drawString(460, y, "Total")
    y -= 14
    c.setFont("Helvetica", 9)
    for li in inv["line_items"]:
        c.drawString(72, y, li["sku"])
        c.drawString(160, y, li["description"])
        c.drawString(340, y, li["quantity"])
        c.drawString(390, y, li["unit_price"])
        c.drawString(460, y, li["line_total"])
        y -= 14
    y -= 10
    # decoy struck total
    c.setFillGray(0.45)
    decoy = f"Invoice Total: {inv['invoice_total']}.99"
    c.setFont("Helvetica", 10)
    c.drawString(72, y, decoy)
    c.line(72, y + 3, 72 + 180, y + 3)
    c.setFillGray(0)
    y -= 16
    c.drawString(72, y, f"Subtotal: {inv['subtotal']}")
    y -= 14
    c.drawString(72, y, f"Tax: {inv['tax']}")
    y -= 14
    c.drawString(72, y, f"Freight: {inv['freight']}")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, f"Invoice Total: {inv['invoice_total']}")
    c.showPage()
    c.save()


def layout_extra_fees(path: Path, inv: dict) -> None:
    """Extra fee lines plus a handling note that is not a PO SKU."""
    c = _setup_canvas(path)
    _header(c, inv, "COMMERCIAL INVOICE")
    y = 680
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"PO: {inv['po_number']}    Currency: {inv['currency']}")
    y -= 18
    c.drawString(72, y, f"Terms: {inv['payment_terms']}")
    y -= 22
    c.setFont("Helvetica", 9)
    for li in inv["line_items"]:
        c.drawString(72, y, f"{li['line_number']}. {li['sku']}  {li['description']}")
        y -= 12
        c.drawString(90, y, f"qty {li['quantity']} @ {li['unit_price']}  line {li['line_total']}")
        y -= 16
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(72, y, "Note: rush / handling fees are billed as FEE-RUSH and are not on the PO.")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Subtotal: {inv['subtotal']}")
    y -= 14
    c.drawString(72, y, f"Tax: {inv['tax']}   Freight: {inv['freight']}")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, f"Invoice Total: {inv['invoice_total']}")
    c.showPage()
    c.save()


def layout_wrapped(path: Path, inv: dict) -> None:
    """Wrapped descriptions and irregular column breaks."""
    c = _setup_canvas(path)
    _header(c, inv, "INVOICE")
    y = 680
    c.setFont("Courier", 8)
    c.drawString(72, y, f"PO Number: {inv['po_number']}")
    y -= 12
    c.drawString(72, y, f"Currency: {inv['currency']}   Payment Terms: {inv['payment_terms']}")
    y -= 20
    for li in inv["line_items"]:
        desc = li["description"] + " — packaged per contract; see packing list for lot codes"
        c.drawString(72, y, f"Item {li['line_number']} SKU {li['sku']}")
        y -= 11
        # wrap description
        while desc:
            chunk, desc = desc[:48], desc[48:]
            c.drawString(84, y, chunk)
            y -= 11
        c.drawString(
            84,
            y,
            f"quantity={li['quantity']} unit_price={li['unit_price']} line_total={li['line_total']}",
        )
        y -= 18
    c.drawString(72, y, f"Subtotal: {inv['subtotal']}")
    y -= 11
    c.drawString(72, y, f"Tax: {inv['tax']}")
    y -= 11
    c.drawString(72, y, f"Freight: {inv['freight']}")
    y -= 11
    c.setFont("Courier-Bold", 9)
    c.drawString(72, y, f"Invoice Total: {inv['invoice_total']}")
    c.showPage()
    c.save()


def layout_multipage(path: Path, inv: dict) -> None:
    """Header on page 1, line items and totals on page 2."""
    c = _setup_canvas(path)
    _header(c, inv, "INVOICE — PAGE 1 OF 2")
    c.setFont("Helvetica", 10)
    c.drawString(72, 680, f"PO Number: {inv['po_number']}")
    c.drawString(72, 664, f"Currency: {inv['currency']}")
    c.drawString(72, 648, f"Payment Terms: {inv['payment_terms']}")
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(72, 620, "Line items continue on the following page.")
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 740, "INVOICE — PAGE 2 OF 2")
    c.setFont("Helvetica", 9)
    y = 710
    for li in inv["line_items"]:
        c.drawString(
            72,
            y,
            f"{li['line_number']}  {li['sku']}  {li['description']}  "
            f"{li['quantity']} x {li['unit_price']} = {li['line_total']}",
        )
        y -= 16
    y -= 10
    c.drawString(72, y, f"Subtotal: {inv['subtotal']}")
    y -= 14
    c.drawString(72, y, f"Tax: {inv['tax']}")
    y -= 14
    c.drawString(72, y, f"Freight: {inv['freight']}")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, f"Invoice Total: {inv['invoice_total']}")
    c.showPage()
    c.save()


def layout_odd_spacing(path: Path, inv: dict) -> None:
    """Irregular spacing and split labels (still extractable text)."""
    c = _setup_canvas(path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 760, "I N V O I C E")
    c.setFont("Helvetica", 9)
    y = 730
    pairs = [
        (f"Vendor:    {inv['vendor_name']}", 40),
        (f"Vendor   ID:  {inv['vendor_id']}", 50),
        (f"Invoice Number:     {inv['invoice_number']}", 36),
        (f"Invoice    Date: {inv['invoice_date']}", 80),
        (f"PO Number: {inv['po_number']}", 120),
        (f"Currency:   {inv['currency']}", 44),
        (f"Payment Terms: {inv['payment_terms']}", 60),
    ]
    for line, x in pairs:
        c.drawString(x, y, line)
        y -= 18
    y -= 8
    for li in inv["line_items"]:
        c.drawString(50, y, li["sku"])
        c.drawString(160, y, li["description"])
        y -= 13
        c.drawString(70, y, f"qty   {li['quantity']}")
        c.drawString(160, y, f"unit   {li['unit_price']}")
        c.drawString(300, y, f"line total {li['line_total']}")
        y -= 20
    c.drawString(200, y, f"Subtotal: {inv['subtotal']}")
    y -= 15
    c.drawString(40, y, f"Tax: {inv['tax']}          Freight: {inv['freight']}")
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(90, y, f"Invoice Total: {inv['invoice_total']}")
    c.showPage()
    c.save()


HARD_LAYOUTS = {
    "strikethrough": layout_strikethrough,
    "extra_fees": layout_extra_fees,
    "wrapped": layout_wrapped,
    "multipage": layout_multipage,
    "odd_spacing": layout_odd_spacing,
}


def _annotate(expected: dict, pack: str, idx: int, layout_name: str) -> dict:
    expected["difficulty"] = pack
    expected["split"] = "development" if idx <= 10 else "holdout"
    expected["layout"] = layout_name
    return expected



def align_evidence_to_pdf(case_dir: Path, expected: dict) -> dict:
    """Rewrite gold evidence quotes so they appear in the rendered PDF text.

    Hard layouts omit the LINE| machine block; validation requires exact quotes.
    """
    from app.canonicalize import canonicalize_document
    from app.pdf_text import extract_pdf_text

    pdf = (case_dir / "invoice.pdf").read_bytes()
    pages = extract_pdf_text(pdf).pages
    canon = canonicalize_document(pdf, pages).canonical_text
    ext = expected["extraction"]
    evidence = {}
    for field in ("vendor_name", "invoice_number", "po_number", "invoice_total"):
        val = ext.get(field)
        if val and str(val) in canon:
            page = 1
            if field == "invoice_total" and "PAGE 2" in canon:
                page = 2
            evidence[field] = {"quote": str(val), "page": page}
    ext["evidence"] = evidence
    for li in ext.get("line_items") or []:
        candidates = [
            li.get("sku", ""),
            li.get("description", ""),
            li.get("line_total", ""),
            li.get("unit_price", ""),
        ]
        quote = next((c for c in candidates if c and c in canon), None)
        if quote:
            page = 2 if "PAGE 2" in canon else 1
            li["evidence"] = {"quote": quote, "page": page}
        else:
            li.pop("evidence", None)
    expected["extraction"] = ext
    write_json(case_dir / "expected.json", expected)
    return expected


def generate_easy() -> dict:
    rng = random.Random(SEED_EASY)
    root = DIFF_ROOT / "easy"
    if root.exists():
        for child in root.iterdir():
            if child.is_dir():
                for f in child.iterdir():
                    f.unlink()
                child.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    splits = {"development": [], "holdout": []}
    for idx in range(1, 21):
        ids = _ids("easy", idx)
        case = build_case(
            idx,
            "exact_match",
            "READY_FOR_DRAFT",
            rng,
            layout=layout_classic,
            **ids,
        )
        case["expected"] = _annotate(case["expected"], "easy", idx, "layout_classic")
        written = write_case(case, root)
        files.update({f"easy/{k}": v for k, v in written.items()})
        splits["development" if idx <= 10 else "holdout"].append(ids["case_id"])
        print(f"wrote easy/{ids['case_id']} exact_match READY_FOR_DRAFT")
    return {"seed": SEED_EASY, "files": files, "splits": splits, "count": 20}


def generate_medium() -> dict:
    rng = random.Random(SEED_MEDIUM)
    root = DIFF_ROOT / "medium"
    if root.exists():
        for child in root.iterdir():
            if child.is_dir():
                for f in child.iterdir():
                    f.unlink()
                child.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    splits = {"development": [], "holdout": []}
    for idx, (scenario, decision) in enumerate(medium_plan(), start=1):
        ids = _ids("medium", idx)
        vendor = dict(INACTIVE_VENDOR) if scenario == "inactive_vendor" else None
        case = build_case(
            idx,
            scenario,
            decision,
            rng,
            vendor=vendor,
            **ids,
        )
        case["expected"] = _annotate(case["expected"], "medium", idx, case["layout"].__name__)
        written = write_case(case, root)
        files.update({f"medium/{k}": v for k, v in written.items()})
        splits["development" if idx <= 10 else "holdout"].append(ids["case_id"])
        print(f"wrote medium/{ids['case_id']} scenario={scenario} decision={decision}")
    return {"seed": SEED_MEDIUM, "files": files, "splits": splits, "count": 20}


def generate_hard() -> dict:
    rng = random.Random(SEED_HARD)
    root = DIFF_ROOT / "hard"
    if root.exists():
        for child in root.iterdir():
            if child.is_dir():
                for f in child.iterdir():
                    f.unlink()
                child.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    splits = {"development": [], "holdout": []}
    for idx, (scenario, decision, layout_name) in enumerate(hard_plan(), start=1):
        ids = _ids("hard", idx)
        layout = HARD_LAYOUTS[layout_name]
        case = build_case(idx, scenario, decision, rng, layout=layout, **ids)
        case["expected"] = _annotate(case["expected"], "hard", idx, layout_name)
        written = write_case(case, root)
        case_dir = root / ids["case_id"]
        case["expected"] = align_evidence_to_pdf(case_dir, case["expected"])
        written[f"{ids['case_id']}/expected.json"] = sha256_file(case_dir / "expected.json")
        files.update({f"hard/{k}": v for k, v in written.items()})
        splits["development" if idx <= 10 else "holdout"].append(ids["case_id"])
        print(f"wrote hard/{ids['case_id']} scenario={scenario} layout={layout_name} decision={decision}")
    return {"seed": SEED_HARD, "files": files, "splits": splits, "count": 20}


def generate_all(which: str = "all") -> dict:
    DIFF_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "packs": {},
        "notes": {
            "legacy_50_case_seed": 20260812,
            "legacy_untouched": True,
            "ocr": False,
            "text_layer_only": True,
        },
    }
    gens = {
        "easy": generate_easy,
        "medium": generate_medium,
        "hard": generate_hard,
    }
    targets = ["easy", "medium", "hard"] if which == "all" else [which]
    files: dict[str, str] = {}
    for name in targets:
        pack = gens[name]()
        manifest["packs"][name] = {k: v for k, v in pack.items() if k != "files"}
        files.update(pack["files"])
    manifest["files"] = files
    out = write_json(DIFF_ROOT / "manifest.json", manifest)
    print(f"manifest -> {out}")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "all"], default="all")
    args = parser.parse_args(argv)
    generate_all(args.difficulty)


if __name__ == "__main__":
    main()
