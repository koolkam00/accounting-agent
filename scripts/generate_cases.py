#!/usr/bin/env python3
"""Generate 50 deterministic synthetic AP three-way-match cases."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SEED = 20260812
FIX_DEV = REPO / "tests" / "fixtures" / "development"
FIX_HOLD = REPO / "tests" / "fixtures" / "holdout"

VENDORS = [
    {"vendor_id": "V001", "vendor_name": "Northwind Office Supply LLC", "active": True},
    {"vendor_id": "V002", "vendor_name": "Cedar Ridge Industrial Parts", "active": True},
    {"vendor_id": "V003", "vendor_name": "Blue Harbor Packaging Co", "active": True},
    {"vendor_id": "V004", "vendor_name": "Summit Ridge Labware Inc", "active": True},
    {"vendor_id": "V005", "vendor_name": "Pinecrest Facilities Goods", "active": True},
]

SKUS = [
    ("SKU-1001", "Copy Paper Case", "10.00", "5000"),
    ("SKU-1002", "Toner Cartridge Black", "45.50", "5100"),
    ("SKU-1003", "Safety Gloves Box", "12.25", "5200"),
    ("SKU-1004", "Packing Tape Roll", "3.75", "5300"),
    ("SKU-1005", "Widget Assembly A", "100.00", "5400"),
    ("SKU-1006", "Widget Assembly B", "250.00", "5400"),
    ("SKU-1007", "Label Stock Pack", "18.40", "5300"),
    ("SKU-1008", "Cleaning Solvent Gal", "22.00", "5200"),
]


def money(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def mstr(d: Decimal) -> str:
    return format(money(d), "f")


def qstr(d: Decimal) -> str:
    # quantities as plain decimal strings
    return format(d.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize(), "f")


# --- PDF layouts (5 variants), byte-reproducible ---

def _setup_canvas(path: Path) -> canvas.Canvas:
    # invariant=1 freezes CreationDate/ModDate/ID for byte-reproducible PDFs
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setTitle("Synthetic Invoice")
    c.setAuthor("Accounting Agent Fixture Generator")
    c.setSubject("Deterministic AP fixture")
    c.setCreator("accounting-agent/generate_cases.py")
    c.setProducer("ReportLab deterministic")
    return c


def _draw_machine_block(c: canvas.Canvas, inv: dict, y: float) -> float:
    """Machine-readable block used by MockLLMClient parser — identical across layouts."""
    c.setFont("Helvetica", 8)
    lines = [
        f"Vendor: {inv['vendor_name']}",
        f"Vendor ID: {inv['vendor_id']}",
        f"Invoice Number: {inv['invoice_number']}",
        f"Invoice Date: {inv['invoice_date']}",
        f"PO Number: {inv['po_number']}",
        f"Currency: {inv['currency']}",
        f"Payment Terms: {inv['payment_terms']}",
    ]
    for line in lines:
        c.drawString(72, y, line)
        y -= 11
    y -= 6
    for li in inv["line_items"]:
        row = (
            f"LINE|{li['line_number']}|{li['sku']}|{li['description']}|"
            f"{li['quantity']}|{li['unit_price']}|{li['line_total']}"
        )
        c.drawString(72, y, row)
        y -= 11
    y -= 6
    for label in ("Subtotal", "Tax", "Freight", "Invoice Total"):
        key = label.lower().replace(" ", "_")
        c.drawString(72, y, f"{label}: {inv[key]}")
        y -= 11
    if inv.get("ambiguous_marker"):
        c.drawString(72, y, "AMBIGUOUS: vendor_name")
        y -= 11
    return y


def layout_classic(path: Path, inv: dict) -> None:
    c = _setup_canvas(path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, "INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(72, 700, inv["vendor_name"])
    _draw_machine_block(c, inv, 670)
    c.showPage()
    c.save()


def layout_boxed(path: Path, inv: dict) -> None:
    c = _setup_canvas(path)
    c.rect(50, 500, 500, 250, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, 730, "COMMERCIAL INVOICE")
    c.setFont("Helvetica", 9)
    c.drawRightString(540, 730, inv["invoice_number"])
    _draw_machine_block(c, inv, 700)
    c.showPage()
    c.save()


def layout_two_column(path: Path, inv: dict) -> None:
    c = _setup_canvas(path)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 740, inv["vendor_name"])
    c.setFont("Helvetica", 9)
    c.drawString(320, 740, f"Date {inv['invoice_date']}")
    c.line(72, 730, 540, 730)
    _draw_machine_block(c, inv, 710)
    c.showPage()
    c.save()


def layout_modern(path: Path, inv: dict) -> None:
    c = _setup_canvas(path)
    c.setFillGray(0.9)
    c.rect(0, 700, 612, 92, stroke=0, fill=1)
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 740, "Invoice")
    c.setFont("Helvetica", 10)
    c.drawString(72, 720, inv["vendor_name"])
    _draw_machine_block(c, inv, 680)
    c.showPage()
    c.save()


def layout_compact(path: Path, inv: dict) -> None:
    c = _setup_canvas(path)
    c.setFont("Courier-Bold", 11)
    c.drawString(72, 750, f"INV/{inv['invoice_number']}")
    c.setFont("Courier", 8)
    _draw_machine_block(c, inv, 730)
    c.showPage()
    c.save()


LAYOUTS = [layout_classic, layout_boxed, layout_two_column, layout_modern, layout_compact]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_lines(rng: random.Random, n: int = 2, price_factor: Decimal = Decimal("1"), qty_factor: Decimal = Decimal("1")):
    chosen = rng.sample(SKUS, k=n)
    lines = []
    for i, (sku, desc, price, gl) in enumerate(chosen, start=1):
        base_price = Decimal(price)
        qty = Decimal(rng.choice(["1", "2", "3", "5", "10"]))
        inv_price = money(base_price * price_factor)
        inv_qty = qty * qty_factor
        # keep qty as integer-ish string when whole
        if inv_qty == inv_qty.to_integral():
            qty_s = str(int(inv_qty))
        else:
            qty_s = qstr(inv_qty)
        line_total = money(Decimal(qty_s) * inv_price)
        lines.append(
            {
                "line_number": i,
                "sku": sku,
                "description": desc,
                "quantity": qty_s,
                "unit_price": mstr(inv_price),
                "line_total": mstr(line_total),
                "po_unit_price": mstr(base_price),
                "po_quantity": str(int(qty)),
                "gl_account": gl,
            }
        )
    return lines


def totals_from_lines(lines, tax="0.00", freight="0.00", corrupt_total: bool = False):
    subtotal = money(sum(Decimal(li["line_total"]) for li in lines))
    tax_d = money(Decimal(tax))
    freight_d = money(Decimal(freight))
    total = money(subtotal + tax_d + freight_d)
    if corrupt_total:
        total = money(total + Decimal("5.00"))
    return mstr(subtotal), mstr(tax_d), mstr(freight_d), mstr(total)


def make_po(po_id: str, vendor: dict, lines: list, status: str = "OPEN") -> dict:
    return {
        "po_id": po_id,
        "vendor_id": vendor["vendor_id"],
        "vendor_name": vendor["vendor_name"],
        "currency": "USD",
        "status": status,
        "lines": [
            {
                "line_number": li["line_number"],
                "sku": li["sku"],
                "description": li["description"],
                "quantity": li["po_quantity"],
                "unit_price": li["po_unit_price"],
                "gl_account": li["gl_account"],
            }
            for li in lines
        ],
    }


def make_receipt(receipt_id: str, po_id: str, lines: list, qty_scale: Decimal = Decimal("1")) -> dict:
    rlines = []
    for li in lines:
        q = Decimal(li["po_quantity"]) * qty_scale
        if q == q.to_integral():
            qs = str(int(q))
        else:
            qs = qstr(q)
        rlines.append({"sku": li["sku"], "quantity_received": qs})
    return {"receipt_id": receipt_id, "po_id": po_id, "lines": rlines}


def make_extraction(inv: dict, ambiguities=None, drop_fields=None) -> dict:
    drop_fields = drop_fields or []
    evidence = {}
    for field in ("vendor_name", "invoice_number", "po_number", "invoice_total"):
        if field in drop_fields:
            continue
        val = inv.get(field)
        if val:
            evidence[field] = {"quote": str(val), "page": 1}
    line_items = []
    for li in inv["line_items"]:
        row = (
            f"LINE|{li['line_number']}|{li['sku']}|{li['description']}|"
            f"{li['quantity']}|{li['unit_price']}|{li['line_total']}"
        )
        item = {
            "line_number": li["line_number"],
            "sku": li["sku"],
            "description": li["description"],
            "quantity": li["quantity"],
            "unit_price": li["unit_price"],
            "line_total": li["line_total"],
            "evidence": {"quote": row, "page": 1},
        }
        line_items.append(item)

    extraction = {
        "vendor_name": inv["vendor_name"],
        "vendor_id": inv["vendor_id"],
        "invoice_number": inv["invoice_number"],
        "invoice_date": inv["invoice_date"],
        "po_number": inv["po_number"],
        "currency": inv["currency"],
        "line_items": line_items,
        "subtotal": inv["subtotal"],
        "tax": inv["tax"],
        "freight": inv["freight"],
        "invoice_total": inv["invoice_total"],
        "payment_terms": inv["payment_terms"],
        "ambiguities": ambiguities or [],
        "evidence": evidence,
    }
    for f in drop_fields:
        if f == "line_items":
            extraction["line_items"] = []
        else:
            extraction[f] = None
            extraction["evidence"].pop(f, None)
    return extraction


def scenario_plan() -> list[tuple[str, str]]:
    """Return list of (scenario, expected_decision) length 50."""
    plan: list[tuple[str, str]] = []
    plan += [("exact_match", "READY_FOR_DRAFT")] * 15
    plan += [("price_within", "READY_FOR_DRAFT")] * 5
    plan += [("price_over", "HUMAN_REVIEW")] * 5
    plan += [("qty_exceeds_receipt", "HUMAN_REVIEW")] * 5
    plan += [("duplicate", "HUMAN_REVIEW")] * 5
    plan += [("missing_po", "HUMAN_REVIEW")] * 5
    plan += [("math_error", "HUMAN_REVIEW")] * 4
    plan += [("vendor_mismatch", "HUMAN_REVIEW")] * 3
    plan += [("missing_ambiguous", "HUMAN_REVIEW")] * 3
    assert len(plan) == 50
    return plan


def build_case(idx: int, scenario: str, decision: str, rng: random.Random) -> dict:
    case_id = f"case_{idx:03d}"
    vendor = VENDORS[(idx - 1) % len(VENDORS)]
    layout = LAYOUTS[(idx - 1) % len(LAYOUTS)]
    po_id = f"PO-{1000 + idx}"
    invoice_number = f"INV-{2026000 + idx}"
    invoice_date = f"2026-0{(idx % 8) + 1:1d}-{((idx * 3) % 27) + 1:02d}"
    # normalize month
    month = ((idx - 1) % 12) + 1
    day = ((idx * 5) % 27) + 1
    invoice_date = f"2026-{month:02d}-{day:02d}"

    price_factor = Decimal("1")
    qty_factor = Decimal("1")
    receipt_scale = Decimal("1")
    tax = "0.00"
    freight = "0.00"
    corrupt_total = False
    po_status = "OPEN"
    ambiguities = []
    drop_fields: list[str] = []
    duplicate_of = None
    use_po_id = po_id
    vendor_for_invoice = dict(vendor)
    exception_codes: list[str] = []
    already_processed = None

    if scenario == "exact_match":
        pass
    elif scenario == "price_within":
        # within max(0.5%, $0.01) — use +0.01 absolute on mid prices or tiny pct
        price_factor = Decimal("1.002")  # 0.2% < 0.5%
    elif scenario == "price_over":
        price_factor = Decimal("1.02")  # 2% > 0.5%
        exception_codes = ["PRICE_VARIANCE"]
    elif scenario == "qty_exceeds_receipt":
        receipt_scale = Decimal("0.5")  # receive half
        exception_codes = ["QUANTITY_EXCEEDS_RECEIPT"]
    elif scenario == "duplicate":
        # Same vendor+invoice as a prior "already processed" seed
        already_processed = {
            "vendor_id": vendor["vendor_id"],
            "invoice_number": invoice_number,
        }
        exception_codes = ["DUPLICATE_INVOICE"]
        duplicate_of = invoice_number
    elif scenario == "missing_po":
        use_po_id = f"PO-MISSING-{idx}"
        exception_codes = ["PO_NOT_FOUND"]
    elif scenario == "math_error":
        corrupt_total = True
        exception_codes = ["INVOICE_MATH_ERROR"]
    elif scenario == "vendor_mismatch":
        other = VENDORS[idx % len(VENDORS)]
        if other["vendor_id"] == vendor["vendor_id"]:
            other = VENDORS[(idx + 1) % len(VENDORS)]
        vendor_for_invoice = {
            "vendor_id": other["vendor_id"],
            "vendor_name": other["vendor_name"],
            "active": True,
        }
        exception_codes = ["VENDOR_MISMATCH"]
    elif scenario == "missing_ambiguous":
        if idx % 2 == 0:
            drop_fields = ["invoice_number"]
            exception_codes = ["MISSING_INVOICE_NUMBER", "MISSING_REQUIRED_FIELD"]
        else:
            ambiguities = [
                {
                    "field": "vendor_name",
                    "reason": "Multiple vendor headers detected",
                    "candidates": [vendor["vendor_name"], "Other Corp"],
                }
            ]
            exception_codes = ["AMBIGUOUS_FIELD"]

    lines = build_lines(rng, n=2, price_factor=price_factor, qty_factor=qty_factor)
    subtotal, tax, freight, invoice_total = totals_from_lines(
        lines, tax=tax, freight=freight, corrupt_total=corrupt_total
    )

    # For price_within READY cases ensure variance within policy for each line
    if scenario == "price_within":
        for li in lines:
            po_p = Decimal(li["po_unit_price"])
            # set invoice price to po + min(0.01, 0.4% * po)
            delta = max(Decimal("0.01"), money(po_p * Decimal("0.004")))
            # ensure within max(0.5%*po, 0.01)
            tol = max(money(po_p * Decimal("0.005")), Decimal("0.01"))
            if delta > tol:
                delta = Decimal("0.01")
            li["unit_price"] = mstr(po_p + delta)
            li["line_total"] = mstr(Decimal(li["quantity"]) * Decimal(li["unit_price"]))
        subtotal, tax, freight, invoice_total = totals_from_lines(lines)

    inv = {
        "vendor_name": vendor_for_invoice["vendor_name"],
        "vendor_id": vendor_for_invoice["vendor_id"],
        "invoice_number": invoice_number if "invoice_number" not in drop_fields else "",
        "invoice_date": invoice_date,
        "po_number": use_po_id,
        "currency": "USD",
        "payment_terms": "Net 30",
        "line_items": [
            {k: li[k] for k in ("line_number", "sku", "description", "quantity", "unit_price", "line_total")}
            for li in lines
        ],
        "subtotal": subtotal,
        "tax": tax,
        "freight": freight,
        "invoice_total": invoice_total,
        "ambiguous_marker": bool(ambiguities),
    }

    # PO always uses the "true" vendor for the case (except missing_po still has a real PO elsewhere unused)
    po = make_po(po_id, vendor, lines, status=po_status)
    # For missing_po scenario, the invoice references a non-existent PO; still store a PO file for the "real" po_id
    # but expected extraction uses missing id — initialize_database loads po.json as-is.
    if scenario == "missing_po":
        # Store PO with the real po_id but invoice points elsewhere — DB will have PO-xxxx that doesn't match invoice
        pass

    receipt = make_receipt(f"RCV-{1000 + idx}", po_id, lines, qty_scale=receipt_scale)

    extraction = make_extraction(inv, ambiguities=ambiguities, drop_fields=drop_fields)
    if scenario == "missing_po":
        extraction["po_number"] = use_po_id

    expected = {
        "case_id": case_id,
        "scenario": scenario,
        "decision": decision,
        "exception_codes": sorted(set(exception_codes)),
        "extraction": extraction,
        "already_processed": already_processed,
        "duplicate_of": duplicate_of,
        "layout": layout.__name__,
        "po_id": po_id,
    }
    return {
        "case_id": case_id,
        "scenario": scenario,
        "layout": layout,
        "inv": inv,
        "po": po,
        "receipt": receipt,
        "expected": expected,
    }


def write_case(case: dict, root: Path) -> dict[str, str]:
    case_dir = root / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = case_dir / "invoice.pdf"
    case["layout"](pdf_path, case["inv"])
    (case_dir / "po.json").write_text(json.dumps(case["po"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (case_dir / "receipt.json").write_text(
        json.dumps(case["receipt"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (case_dir / "expected.json").write_text(
        json.dumps(case["expected"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files = {
        f"{case['case_id']}/invoice.pdf": sha256_file(pdf_path),
        f"{case['case_id']}/po.json": sha256_file(case_dir / "po.json"),
        f"{case['case_id']}/receipt.json": sha256_file(case_dir / "receipt.json"),
        f"{case['case_id']}/expected.json": sha256_file(case_dir / "expected.json"),
    }
    return files


def main() -> None:
    rng = random.Random(SEED)
    plan = scenario_plan()
    # Shuffle scenarios deterministically but keep case_001.. indexing stable by re-sorting after assign
    # Spec wants case_001..050 with scenario counts — assign in plan order for clarity.
    FIX_DEV.mkdir(parents=True, exist_ok=True)
    FIX_HOLD.mkdir(parents=True, exist_ok=True)

    manifest = {
        "seed": SEED,
        "case_count": 50,
        "splits": {"development": [], "holdout": []},
        "files": {},
        "scenario_counts": {},
    }

    for idx, (scenario, decision) in enumerate(plan, start=1):
        case = build_case(idx, scenario, decision, rng)
        split = "development" if idx <= 30 else "holdout"
        root = FIX_DEV if split == "development" else FIX_HOLD
        files = write_case(case, root)
        for rel, digest in files.items():
            manifest["files"][f"{split}/{rel}"] = digest
        manifest["splits"][split].append(case["case_id"])
        manifest["scenario_counts"][scenario] = manifest["scenario_counts"].get(scenario, 0) + 1
        print(f"wrote {split}/{case['case_id']} scenario={scenario} decision={decision}")

    out = REPO / "tests" / "fixtures" / "dataset_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifest -> {out}")
    print("scenario_counts:", json.dumps(manifest["scenario_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
