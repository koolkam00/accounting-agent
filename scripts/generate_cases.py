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
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.canonicalize import canonicalize_page_text  # noqa: E402
from app.pdf_text import extract_pdf_text  # noqa: E402

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


# --- Harder text-layer invoices (no LINE| machine block; GPU sees pypdf text) ---

DISTRACTOR_REMIT = "Harbor Street Holdings LLC"
DISTRACTOR_SHIP = "Westfield Distribution Center"
DISTRACTOR_INV = "INV-000000"
DISTRACTOR_PO = "PO-9999"
DISTRACTOR_AMOUNT = "8,888.00"
AMBIGUOUS_OTHER = "Other Corp"

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTHS_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PROFILES: dict[str, dict] = {
    "layout_classic": {
        "money": "dollar",
        "qty": "int",
        "date": "us_slash",
        "inv_label": "Bill No.",
        "po_label": "Customer #",
        "vendor_label": "Sold by",
        "terms_text": "Due in 30 days (Net 30)",
        "total_label": "Amount due",
        "subtotal_label": "Merchandise",
        "tax_mode": "exempt_words",
        "freight_mode": "prepaid_words",
        "vendor_id_label": "Supplier #",
        "col_order": ("qty", "description", "sku", "unit_price", "line_total"),
        "headers": ("Qty", "Item", "Code", "Price", "Ext"),
        "multipage": False,
        "reading_order": "normal",
        "barcode": True,
    },
    "layout_boxed": {
        "money": "plain",
        "qty": "ea",
        "date": "iso",
        "inv_label": "Document",
        "po_label": "Our order",
        "vendor_label": "Issuer",
        "terms_text": "Terms Net 30 from invoice date",
        "total_label": "Invoice total",
        "subtotal_label": "Goods",
        "tax_mode": "labeled",
        "freight_mode": "labeled",
        "vendor_id_label": "Acct",
        "col_order": ("sku", "description", "line_total", "qty", "unit_price"),
        "headers": ("SKU", "Description", "Amount", "Qty", "Unit"),
        "multipage": False,
        "reading_order": "normal",
        "barcode": True,
    },
    "layout_two_column": {
        "money": "usd",
        "qty": "int",
        "date": "written",
        "inv_label": "Inv #",
        "po_label": "PO Ref",
        "vendor_label": "Bill From",
        "terms_text": "2/10 N30 — Net 30",
        "total_label": "Balance due",
        "subtotal_label": "Net merchandise",
        "tax_mode": "exempt_words",
        "freight_mode": "labeled",
        "vendor_id_label": "Vendor code",
        "col_order": ("description", "qty", "sku", "unit_price", "line_total"),
        "headers": ("Description", "Qty", "SKU", "Unit", "Amount"),
        "multipage": False,
        "reading_order": "right_first",
        "barcode": True,
    },
    "layout_modern": {
        "money": "dollar",
        "qty": "thousandths",
        "date": "day_mon_year",
        "inv_label": "Invoice",
        "po_label": "Release",
        "vendor_label": "From",
        "terms_text": "Payment terms: Net 30",
        "total_label": "Total due",
        "subtotal_label": "Subtotal",
        "tax_mode": "labeled",
        "freight_mode": "prepaid_words",
        "vendor_id_label": "Internal vendor",
        "col_order": ("qty", "sku", "description", "unit_price", "line_total"),
        "headers": ("Qty", "SKU", "Description", "Unit", "Amount"),
        "multipage": True,
        "reading_order": "normal",
        "barcode": True,
    },
    "layout_compact": {
        "money": "ungrouped_dollar",
        "qty": "thousandths",
        "date": "us_slash",
        "inv_label": "Ref",
        "po_label": "This release",
        "vendor_label": "Remitter",
        "terms_text": "NET30",
        "total_label": "Please pay",
        "subtotal_label": "Lines",
        "tax_mode": "exempt_words",
        "freight_mode": "prepaid_words",
        "vendor_id_label": "ID",
        "col_order": ("sku", "qty", "unit_price", "line_total", "description"),
        "headers": ("SKU", "Qty", "Unit", "Ext", "Description"),
        "multipage": False,
        "reading_order": "normal",
        "barcode": True,
    },
}


def format_date(iso: str, style: str) -> str:
    year_s, month_s, day_s = iso.split("-")
    year, month, day = int(year_s), int(month_s), int(day_s)
    if style == "us_slash":
        return f"{month:02d}/{day:02d}/{year}"
    if style == "written":
        return f"{_MONTHS[month - 1]} {day}, {year}"
    if style == "day_mon_year":
        return f"{day} {_MONTHS_ABBR[month - 1]} {year}"
    return iso


def format_money(amount: str, style: str) -> str:
    q = money(Decimal(amount))
    plain = format(q, "f")
    grouped = format(q, ",.2f")
    if style == "dollar":
        return f"${grouped}"
    if style == "usd":
        return f"USD {plain}"
    if style == "ungrouped_dollar":
        return f"${plain}"
    return plain


def format_qty(qty: str, style: str) -> str:
    d = Decimal(qty)
    if style == "thousandths":
        return format(d.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP), "f")
    if style == "ea":
        whole = str(int(d)) if d == d.to_integral() else format(d, "f")
        return f"{whole} ea"
    if d == d.to_integral():
        return str(int(d))
    return format(d, "f")


def format_row(li: dict, profile: dict) -> str:
    cells = {
        "qty": format_qty(li["quantity"], profile["qty"]),
        "description": li["description"],
        "sku": li["sku"],
        "unit_price": format_money(li["unit_price"], profile["money"]),
        "line_total": format_money(li["line_total"], profile["money"]),
    }
    return " ".join(cells[k] for k in profile["col_order"])


def header_row(profile: dict) -> str:
    return " ".join(profile["headers"])


def build_display(inv: dict, profile: dict) -> dict:
    rows = [format_row(li, profile) for li in inv["line_items"]]
    return {
        "date": format_date(inv["invoice_date"], profile["date"]),
        "invoice_total": format_money(inv["invoice_total"], profile["money"]),
        "subtotal": format_money(inv["subtotal"], profile["money"]),
        "tax": format_money(inv["tax"], profile["money"]),
        "freight": format_money(inv["freight"], profile["money"]),
        "rows": rows,
        "header": header_row(profile),
        "po": inv["po_number"],
        "vendor": inv["vendor_name"],
        "invoice_number": inv["invoice_number"],
        "vendor_id": inv["vendor_id"],
        "terms": profile["terms_text"],
    }


def _profile_and_display(layout_name: str, inv: dict) -> tuple[dict, dict]:
    profile = inv.get("profile") or PROFILES[layout_name]
    display = inv.get("display") or build_display(inv, profile)
    return profile, display


def _setup_canvas(path: Path) -> canvas.Canvas:
    # invariant=1 freezes CreationDate/ModDate/ID for byte-reproducible PDFs
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setTitle("Synthetic Invoice")
    c.setAuthor("Accounting Agent Fixture Generator")
    c.setSubject("Deterministic AP fixture")
    c.setCreator("accounting-agent/generate_cases.py")
    c.setProducer("ReportLab deterministic")
    return c


def _draw_distractors(c: canvas.Canvas, x: float, y: float) -> float:
    c.setFont("Helvetica", 8)
    c.drawString(x, y, f"Remit to: {DISTRACTOR_REMIT}")
    y -= 11
    c.drawString(x, y, f"Ship from: {DISTRACTOR_SHIP}")
    y -= 11
    c.drawString(x, y, f"Scan code {DISTRACTOR_INV}   prior balance ${DISTRACTOR_AMOUNT}")
    y -= 11
    c.drawString(x, y, f"Blanket {DISTRACTOR_PO} — do not pay this reference")
    y -= 11
    c.drawString(x, y, "Amount enclosed: $0.00    Credit limit: $8,888.00")
    return y - 14


def _draw_vendor_block(c: canvas.Canvas, inv: dict, profile: dict, display: dict, x: float, y: float) -> float:
    c.setFont("Helvetica", 9)
    if inv.get("ambiguous_marker"):
        c.drawString(x, y, f"Letterhead: {AMBIGUOUS_OTHER}")
        y -= 12
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, f"{profile['vendor_label']}: {display['vendor']}")
    y -= 14
    c.setFont("Helvetica", 9)
    if display["invoice_number"]:
        c.drawString(x, y, f"{profile['inv_label']} {display['invoice_number']}")
        y -= 12
    c.drawString(x, y, f"Date {display['date']}")
    y -= 12
    c.drawString(x, y, f"{profile['po_label']} {display['po']}")
    y -= 12
    c.drawString(x, y, display["terms"])
    y -= 12
    c.drawString(x, y, f"{profile['vendor_id_label']} {display['vendor_id']}")
    return y - 16


def _draw_table(c: canvas.Canvas, display: dict, x: float, y: float, font: str = "Helvetica") -> float:
    c.setFont(f"{font}-Bold" if font == "Helvetica" else "Courier-Bold", 8)
    c.drawString(x, y, display["header"])
    y -= 12
    c.setFont(font, 8)
    for row in display["rows"]:
        c.drawString(x, y, row)
        y -= 12
    return y - 8


def _draw_totals(c: canvas.Canvas, profile: dict, display: dict, x: float, y: float) -> float:
    c.setFont("Helvetica", 9)
    c.drawString(x, y, f"{profile['subtotal_label']}  {display['subtotal']}")
    y -= 12
    if profile["tax_mode"] == "labeled":
        c.drawString(x, y, f"Tax  {display['tax']}")
        y -= 12
    else:
        c.drawString(x, y, "Tax exempt — no sales tax charged")
        y -= 12
    if profile["freight_mode"] == "labeled":
        c.drawString(x, y, f"Freight  {display['freight']}")
        y -= 12
    else:
        c.drawString(x, y, "Freight prepaid and billed on a separate advice")
        y -= 12
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"{profile['total_label']}  {display['invoice_total']}")
    return y - 16


def _draw_barcode_footer(c: canvas.Canvas, inv: dict, y: float = 48) -> None:
    c.setFont("Courier", 8)
    real = inv.get("invoice_number") or ""
    extra = f"  also {real}" if real else ""
    c.drawString(72, y, f"|| {DISTRACTOR_INV} ||{extra}")


def _draw_terms_noise(c: canvas.Canvas, x: float, y: float) -> float:
    c.setFont("Helvetica", 7)
    lines = [
        "Claims must be made within 10 days of receipt. Title passes FOB origin.",
        "Returned goods require an RMA. Restocking 15% after 30 days.",
        "This is not a packing list. Counts on the bill of lading control.",
        "Payment coupon below is for remittance only and may show a different amount.",
    ]
    for line in lines:
        c.drawString(x, y, line)
        y -= 10
    return y


def layout_classic(path: Path, inv: dict) -> None:
    profile, display = _profile_and_display("layout_classic", inv)
    c = _setup_canvas(path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 740, "STATEMENT / INVOICE")
    y = _draw_vendor_block(c, inv, profile, display, 72, 718)
    y = _draw_distractors(c, 72, y)
    y = _draw_table(c, display, 72, y)
    y = _draw_totals(c, profile, display, 72, y)
    _draw_terms_noise(c, 72, y)
    _draw_barcode_footer(c, inv)
    c.showPage()
    c.save()


def layout_boxed(path: Path, inv: dict) -> None:
    profile, display = _profile_and_display("layout_boxed", inv)
    c = _setup_canvas(path)
    c.rect(50, 420, 512, 340, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, 740, "COMMERCIAL INVOICE")
    y = _draw_vendor_block(c, inv, profile, display, 60, 720)
    y = _draw_table(c, display, 60, y)
    y = _draw_totals(c, profile, display, 60, y)
    y = _draw_distractors(c, 60, min(y, 400))
    _draw_terms_noise(c, 60, y)
    _draw_barcode_footer(c, inv)
    c.showPage()
    c.save()


def layout_two_column(path: Path, inv: dict) -> None:
    """Draw the right column first so pypdf plain-mode emits PO/distractors before vendor."""
    profile, display = _profile_and_display("layout_two_column", inv)
    c = _setup_canvas(path)
    c.setFont("Helvetica", 9)
    c.drawString(320, 740, f"{profile['po_label']} {display['po']}")
    c.drawString(320, 726, f"Date {display['date']}")
    c.drawString(320, 712, f"Pay this stub: ${DISTRACTOR_AMOUNT}")
    c.drawString(320, 698, f"Remit: {DISTRACTOR_REMIT}")
    c.drawString(320, 684, f"Blanket {DISTRACTOR_PO}")
    c.setFont("Helvetica-Bold", 11)
    if inv.get("ambiguous_marker"):
        c.drawString(72, 740, f"Letterhead: {AMBIGUOUS_OTHER}")
        c.drawString(72, 724, f"{profile['vendor_label']}: {display['vendor']}")
        next_y = 708
    else:
        c.drawString(72, 740, f"{profile['vendor_label']}: {display['vendor']}")
        next_y = 724
    c.setFont("Helvetica", 9)
    if display["invoice_number"]:
        c.drawString(72, next_y, f"{profile['inv_label']} {display['invoice_number']}")
        next_y -= 14
    c.drawString(72, next_y, display["terms"])
    next_y -= 14
    c.drawString(72, next_y, f"{profile['vendor_id_label']} {display['vendor_id']}")
    c.line(72, 660, 540, 660)
    y = _draw_table(c, display, 72, 640)
    y = _draw_totals(c, profile, display, 72, y)
    y = _draw_distractors(c, 72, y)
    _draw_terms_noise(c, 72, y)
    _draw_barcode_footer(c, inv)
    c.showPage()
    c.save()


def layout_modern(path: Path, inv: dict) -> None:
    """Line items on page 1; totals and remittance coupon on page 2."""
    profile, display = _profile_and_display("layout_modern", inv)
    c = _setup_canvas(path)
    c.setFillGray(0.9)
    c.rect(0, 700, 612, 92, stroke=0, fill=1)
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 740, "Invoice")
    c.setFont("Helvetica", 8)
    c.drawString(400, 740, "Page 1 of 2 — continued")
    y = _draw_vendor_block(c, inv, profile, display, 72, 718)
    y = _draw_distractors(c, 72, y)
    _draw_table(c, display, 72, y)
    _draw_barcode_footer(c, inv)
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 740, "Page 2 of 2 — remittance advice")
    c.setFont("Helvetica", 9)
    c.drawString(72, 720, f"{profile['vendor_label']}: {display['vendor']}")
    y = _draw_totals(c, profile, display, 72, 700)
    c.setFont("Helvetica", 9)
    c.drawString(72, y, "Detach and return with payment. Coupon amount is not the invoice total.")
    y -= 14
    c.drawString(72, y, f"Coupon amount: ${DISTRACTOR_AMOUNT}")
    y -= 18
    y = _draw_terms_noise(c, 72, y)
    c.drawString(72, y, f"Scan code {DISTRACTOR_INV}")
    c.showPage()
    c.save()


def layout_compact(path: Path, inv: dict) -> None:
    profile, display = _profile_and_display("layout_compact", inv)
    c = _setup_canvas(path)
    c.setFont("Courier-Bold", 11)
    title = display["invoice_number"] or "UNNUMBERED"
    c.drawString(72, 750, f"BILL/{title}")
    c.setFont("Courier", 8)
    y = _draw_vendor_block(c, inv, profile, display, 72, 732)
    y = _draw_table(c, display, 72, y, font="Courier")
    y = _draw_totals(c, profile, display, 72, y)
    y = _draw_distractors(c, 72, y)
    _draw_terms_noise(c, 72, y)
    _draw_barcode_footer(c, inv)
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


def _quote_page(pages: list[str], needle: str) -> int:
    for i, page in enumerate(pages, start=1):
        if needle in canonicalize_page_text(page):
            return i
    raise ValueError(f"evidence quote not found in PDF text: {needle!r}")


def bind_evidence_pages(extraction: dict, pdf_path: Path) -> None:
    pages = extract_pdf_text(pdf_path).pages
    for span in extraction.get("evidence", {}).values():
        span["page"] = _quote_page(pages, span["quote"])
    for li in extraction.get("line_items", []):
        ev = li.get("evidence")
        if ev:
            ev["page"] = _quote_page(pages, ev["quote"])


def make_extraction(inv: dict, ambiguities=None, drop_fields=None) -> dict:
    drop_fields = drop_fields or []
    profile = inv.get("profile") or PROFILES["layout_classic"]
    display = inv.get("display") or build_display(inv, profile)
    evidence = {}
    quote_map = {
        "vendor_name": display["vendor"],
        "invoice_number": display["invoice_number"],
        "po_number": display["po"],
        "invoice_total": display["invoice_total"],
    }
    for field in ("vendor_name", "invoice_number", "po_number", "invoice_total"):
        if field in drop_fields:
            continue
        val = quote_map.get(field) or inv.get(field)
        if val:
            evidence[field] = {"quote": str(val), "page": 1}
    line_items = []
    for li, row in zip(inv["line_items"], display["rows"]):
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
    profile = PROFILES[layout.__name__]
    inv["profile"] = profile
    inv["display"] = build_display(inv, profile)

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
    bind_evidence_pages(case["expected"]["extraction"], pdf_path)
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
