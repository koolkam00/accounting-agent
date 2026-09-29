"""Data-room documents: text-layer PDFs (reportlab) and plain-text emails.

Templates (invoice, letter, agreement, memo, form, email) turn a document
spec's ``fields`` into layout blocks; one renderer paginates and draws them.

Two properties matter more than looks:
- Extractable, quotable text. Each visual row is drawn as a single PDF text
  object, so pypdf's plain mode returns it as one line, and phrases listed in
  ``key_phrases`` are never wrapped across lines. After rendering, every key
  phrase is checked verbatim against qoe.pdf_text's canonical page text.
- Byte reproducibility. Canvases use invariant=1 and fixed metadata, so the
  same spec always yields the same bytes.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from qoe.money import D, ZERO, q2
from qoe.pdf_text import canonicalize_page_text, extract_pdf_pages

from .ledger import MONTH_NAME, GenerationError, Txn
from .spec import DealSpec, DocumentSpec, Party

FOOTER = "SYNTHETIC — generated for QoE Evidence Review testing"
DRAFT_BANNER = "DRAFT — FOR DISCUSSION PURPOSES ONLY — NOT FOR EXECUTION"
PAGE_W, PAGE_H = letter
LEFT, RIGHT = 72.0, PAGE_W - 72.0
TOP, BOTTOM = PAGE_H - 66.0, 76.0
WIDTH = RIGHT - LEFT
NBSP = "\u00a0"  # binds key phrases during wrapping
# Document text can cite generated rows, e.g. "{num:halvorsen_inv_1}" or "{amount:halvorsen_inv_1}".
_ROW_REF = re.compile(r"\{(num|amount|date|mdy|memo|counterparty):([^{}:]+)\}")
BODY, BOLD, ITALIC = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


@dataclass
class Cell:
    x: float
    text: str
    align: str = "left"  # left | right | center
    font: str = BODY
    size: float = 10.0


@dataclass
class Row:
    cells: list[Cell]
    height: float
    rule_below: bool = False
    gray: float = 0.0


@dataclass
class Block:
    rows: list[Row] = field(default_factory=list)
    keep: bool = False  # keep every row on one page
    columns: Optional[list[list[Row]]] = None  # side-by-side columns, drawn one column at a time
    keep_with_next: bool = False  # headings never end a page

    def height(self) -> float:
        if self.columns is not None:
            return max(sum(r.height for r in col) for col in self.columns)
        return sum(r.height for r in self.rows)


@dataclass
class Rendered:
    data: bytes
    text: str  # canonical text of every page, "\n\f\n"-joined
    stated_total: Optional[Decimal] = None


def money(value: Decimal, dollar: bool = True) -> str:
    text = format(abs(value), ",.2f")
    text = ("$" + text) if dollar else text
    return f"({text})" if value < 0 else text


# ---------------------------------------------------------------------------
# Layout primitives
# ---------------------------------------------------------------------------


def _check_text(text: str, where: str) -> None:
    try:
        text.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise GenerationError(f"{where}: character {text[exc.start]!r} is not in the standard PDF font encoding") from exc


def wrap(text: str, width: float, font: str, size: float, keep: list[str]) -> list[str]:
    protected = text
    for phrase in sorted(keep, key=len, reverse=True):
        if phrase in protected:
            protected = protected.replace(phrase, phrase.replace(" ", NBSP))
    lines: list[str] = []
    current = ""
    for word in protected.split(" "):
        trial = f"{current} {word}" if current else word
        if not current or stringWidth(trial.replace(NBSP, " "), font, size) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return [line.replace(NBSP, " ") for line in lines]


def spacer(height: float) -> Block:
    return Block([Row([], height)])


def line_rows(lines: list[str], font: str = BODY, size: float = 10.0, leading: float = 13.0, x: float = LEFT, align: str = "left") -> list[Row]:
    return [Row([Cell(x, text, align, font, size)], leading) for text in lines]


def paragraph(text: str, keep: list[str], font: str = BODY, size: float = 10.0, leading: float = 13.5,
              indent: float = 0.0, after: float = 7.0, first_prefix: str = "") -> Block:
    body = first_prefix + text
    lines = wrap(body, WIDTH - indent, font, size, keep)
    rows = [Row([Cell(LEFT + indent, line, "left", font, size)], leading) for line in lines]
    rows[-1].height += after
    return Block(rows)


def heading(text: str, size: float = 10.5, after: float = 4.0) -> Block:
    return Block([Row([Cell(LEFT, text, "left", BOLD, size)], 14.0 + after)], keep=True, keep_with_next=True)


def kv_rows(pairs: list[list[str]], keep: list[str], x: float = LEFT, size: float = 10.0, leading: float = 13.0) -> list[Row]:
    # Label and value share one string so extraction keeps "Invoice No.: 25-0212" intact.
    rows: list[Row] = []
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise GenerationError(f"key-value row must be [label, value], got {pair!r} (quote values that contain commas)")
        label, value = pair
        text = f"{label}: {value}" if label else str(value)
        lines = wrap(text, RIGHT - x, BODY, size, keep)
        rows.append(Row([Cell(x, lines[0], "left", BODY, size)], leading))
        rows += [Row([Cell(x + 12.0, extra, "left", BODY, size)], leading) for extra in lines[1:]]
    return rows


def _party(spec: DealSpec, ref: Any, where: str) -> Optional[Party]:
    if ref is None:
        return None
    if isinstance(ref, str):
        if ref not in spec.parties:
            raise GenerationError(f"{where}: unknown party {ref!r}")
        return spec.parties[ref]
    return Party.model_validate(ref)


def _address_lines(spec: DealSpec, ref: Any, where: str) -> list[str]:
    if isinstance(ref, list):
        return [str(x) for x in ref]
    p = _party(spec, ref, where)
    return [p.name, *p.address] if p else []


def letterhead(p: Party) -> list[Block]:
    rows = [Row([Cell(LEFT, p.name, "left", BOLD, 16.0)], 18.0)]
    if p.tagline:
        rows.append(Row([Cell(LEFT, p.tagline, "left", ITALIC, 9.0)], 12.0))
    if p.address:
        rows.append(Row([Cell(LEFT, " | ".join(p.address), "left", BODY, 8.5)], 11.0))
    contact = " | ".join(x for x in (p.phone, p.email, p.web) if x)
    if contact:
        rows.append(Row([Cell(LEFT, contact, "left", BODY, 8.5)], 11.0))
    rows[-1].rule_below = True
    rows[-1].height += 16.0
    return [Block(rows, keep=True)]


def table(spec_table: dict[str, Any], keep: list[str], where: str) -> Block:
    """columns: [{title, align, width}] left to right. The column without a width
    takes the remaining page width and is the one that wraps."""
    columns = spec_table.get("columns") or []
    if not columns:
        raise GenerationError(f"{where}: table needs columns")
    widths = [float(c.get("width", 0)) for c in columns]
    flex = next((i for i, w in enumerate(widths) if w == 0), 0)
    widths[flex] = WIDTH - sum(w for i, w in enumerate(widths) if i != flex)
    if widths[flex] < 60:
        raise GenerationError(f"{where}: table columns leave {widths[flex]:.0f}pt for the flexible column")
    xs: list[tuple[float, str]] = []
    left = LEFT
    for col, w in zip(columns, widths):
        align = col.get("align", "left")
        xs.append((left + w if align == "right" else left, align))
        left += w
    size = float(spec_table.get("size", 9.5))
    rows = [Row([Cell(x, str(col.get("title", "")), a, BOLD, size) for (x, a), col in zip(xs, columns)], 14.0, rule_below=True)]
    rows[0].height += 3.0
    body_rows = [list(r) for r in spec_table.get("rows", [])]
    total_row = spec_table.get("total")
    for i, raw in enumerate([*body_rows, *([total_row] if total_row else [])]):
        if len(raw) != len(columns):
            raise GenerationError(f"{where}: table row has {len(raw)} cells for {len(columns)} columns: {raw!r}")
        font = BOLD if total_row is not None and i == len(body_rows) else BODY
        cells = [str(v) if v is not None else "" for v in raw]
        wrapped = wrap(cells[flex], widths[flex] - 8.0, font, size, keep) if cells[flex] else [""]
        first = list(cells)
        first[flex] = wrapped[0]
        rows.append(Row([Cell(x, v, a, font, size) for (x, a), v in zip(xs, first) if v], 12.5))
        for extra in wrapped[1:]:
            rows.append(Row([Cell(xs[flex][0], extra, xs[flex][1], font, size)], 12.5))
    rows[-1].height += 8.0
    return Block(rows)


def signature_block(sig: dict[str, Any], where: str) -> Block:
    signed = bool(sig.get("signed", False))
    name = str(sig.get("name", ""))
    rows: list[Row] = []
    if sig.get("party"):
        rows.append(Row([Cell(LEFT, str(sig["party"]), "left", BOLD, 10.0)], 18.0))
    if sig.get("style") == "letter":
        rows.append(Row([Cell(LEFT, f"/s/ {name}" if signed else "", "left", ITALIC, 11.0)], 15.0))
        rows.append(Row([Cell(LEFT, name, "left", BODY, 10.0)], 13.0))
        if sig.get("title"):
            rows.append(Row([Cell(LEFT, str(sig["title"]), "left", BODY, 10.0)], 13.0))
    else:
        by = f"By: /s/ {name}" if signed else "By: ________________________________"
        rows.append(Row([Cell(LEFT, by, "left", ITALIC if signed else BODY, 10.0)], 14.0))
        rows.append(Row([Cell(LEFT, f"Name: {name}", "left", BODY, 10.0)], 13.0))
        rows.append(Row([Cell(LEFT, f"Title: {sig.get('title', '')}", "left", BODY, 10.0)], 13.0))
        date_text = sig.get("date") if signed and sig.get("date") else ("____________________" if not signed else "")
        if date_text:
            rows.append(Row([Cell(LEFT, f"Date: {date_text}", "left", BODY, 10.0)], 13.0))
    rows[-1].height += 14.0
    return Block(rows, keep=True)


def body_items(items: list[Any], keep: list[str], where: str) -> list[Block]:
    blocks: list[Block] = []
    for i, item in enumerate(items or []):
        at = f"{where} body[{i}]"
        if isinstance(item, str):
            blocks.append(paragraph(item, keep))
        elif not isinstance(item, dict) or len(item) != 1:
            raise GenerationError(f"{at}: expected a string or a one-key mapping")
        elif "heading" in item:
            blocks.append(heading(str(item["heading"])))
        elif "kv" in item:
            rows = kv_rows(item["kv"], keep)
            rows[-1].height += 7.0
            blocks.append(Block(rows, keep=True))
        elif "table" in item:
            blocks.append(table(item["table"], keep, at))
        elif "bullets" in item:
            for b in item["bullets"]:
                lines = wrap(str(b), WIDTH - 18.0, BODY, 10.0, keep)
                rows = [Row([Cell(LEFT + 6.0, "•", "left", BODY, 10.0), Cell(LEFT + 18.0, lines[0], "left", BODY, 10.0)], 13.5)]
                rows += [Row([Cell(LEFT + 18.0, extra, "left", BODY, 10.0)], 13.5) for extra in lines[1:]]
                rows[-1].height += 3.0
                blocks.append(Block(rows))
            blocks[-1].rows[-1].height += 4.0
        elif "lines" in item:
            rows = line_rows([str(x) for x in item["lines"]])
            rows[-1].height += 7.0
            blocks.append(Block(rows, keep=True))
        elif "numbered" in item:
            for n, text in enumerate(item["numbered"], start=1):
                blocks.append(paragraph(str(text), keep, indent=18.0, first_prefix=""))
                blocks[-1].rows[0].cells.insert(0, Cell(LEFT, f"({chr(96 + n)})", "left", BODY, 10.0))
        elif "spacer" in item:
            blocks.append(spacer(float(item["spacer"])))
        elif "signatures" in item:
            blocks.extend(signature_block(s, at) for s in item["signatures"])
        else:
            raise GenerationError(f"{at}: unknown body item {sorted(item)}")
    return blocks


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def _invoice(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any], keep: list[str]) -> tuple[list[Block], Decimal]:
    where = f"document {doc.id}"
    issuer = _party(spec, f.get("issuer"), where)
    blocks: list[Block] = letterhead(issuer) if issuer else []
    blocks.append(Block([Row([Cell(LEFT, str(f.get("title", "INVOICE")), "left", BOLD, 18.0)], 26.0)], keep=True))
    left_col = [Row([Cell(LEFT, str(f.get("bill_to_label", "Bill To:")), "left", BOLD, 10.0)], 13.0)]
    left_col += line_rows(_address_lines(spec, f.get("bill_to"), where))
    right_col = kv_rows(f.get("meta", []), keep, x=LEFT + 250.0, size=9.5, leading=12.5)
    blocks.append(Block(columns=[left_col, right_col]))
    blocks.append(spacer(14.0))
    for text in f.get("intro", []) or []:
        blocks.append(paragraph(str(text), keep))

    lines = f.get("lines") or []
    if not lines:
        raise GenerationError(f"{where}: invoice needs lines")
    has_qty = any("qty" in ln for ln in lines)
    labels = f.get("columns", {})
    columns = [{"title": labels.get("description", "Description")}]
    if has_qty:
        columns += [{"title": labels.get("qty", "Qty"), "align": "right", "width": 60},
                    {"title": labels.get("rate", "Rate"), "align": "right", "width": 80}]
    columns.append({"title": labels.get("amount", "Amount"), "align": "right", "width": 90})
    rows: list[list[str]] = []
    subtotal = ZERO
    for ln in lines:
        if "amount" in ln:
            amount = q2(D(ln["amount"]))
        elif "qty" in ln and "rate" in ln:
            amount = q2(D(ln["qty"]) * D(ln["rate"]))
        else:
            raise GenerationError(f"{where}: invoice line needs amount or qty and rate: {ln}")
        subtotal += amount
        row = [str(ln.get("description", ""))]
        if has_qty:
            row += [f"{D(ln['qty']):.2f}" if "qty" in ln else "", money(q2(D(ln["rate"])), dollar=False) if "rate" in ln else ""]
        row.append(money(amount, dollar=False))
        rows.append(row)
    blocks.append(table({"columns": columns, "rows": rows}, keep, where))

    total = subtotal
    totals: list[str] = []
    if len(lines) > 1 or f.get("less"):
        totals.append(f"Subtotal: {money(subtotal)}")
    for adj in f.get("less", []) or []:
        amt = q2(D(adj["amount"]))
        total -= amt
        totals.append(f"{adj['label']}: {money(-amt)}")
    totals.append(f"{f.get('total_label', 'Total Due')}: {money(total)}")
    trows = [Row([Cell(RIGHT, t, "right", BOLD if i == len(totals) - 1 else BODY, 10.5 if i == len(totals) - 1 else 10.0)], 15.0)
             for i, t in enumerate(totals)]
    trows[-1].height += 12.0
    blocks.append(Block(trows, keep=True))
    blocks += body_items(f.get("notes", []), keep, where)
    if f.get("remit"):
        rows_ = [Row([Cell(LEFT, str(f.get("remit_label", "Remit to:")), "left", BOLD, 9.5)], 12.5)]
        rows_ += line_rows([str(x) for x in f["remit"]], size=9.5, leading=12.0)
        rows_[-1].height += 8.0
        blocks.append(Block(rows_, keep=True))
    if f.get("terms"):
        blocks.append(paragraph(str(f["terms"]), keep, size=9.0, leading=12.0))
    return blocks, total


def _letter(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any], keep: list[str]) -> list[Block]:
    where = f"document {doc.id}"
    issuer = _party(spec, f.get("issuer"), where)
    blocks: list[Block] = letterhead(issuer) if issuer else []
    if f.get("delivery"):
        blocks.append(Block(line_rows([str(f["delivery"])], font=BOLD, size=9.0), keep=True))
    if f.get("date"):
        blocks.append(Block([Row([Cell(LEFT, str(f["date"]))], 24.0)], keep=True))
    to = _address_lines(spec, f.get("to"), where)
    if to:
        rows = line_rows(to)
        rows[-1].height += 12.0
        blocks.append(Block(rows, keep=True))
    re_lines = f.get("re")
    if re_lines:
        re_lines = [re_lines] if isinstance(re_lines, str) else list(re_lines)
        rows = [Row([Cell(LEFT, "Re:", "left", BOLD, 10.0), Cell(LEFT + 30.0, str(re_lines[0]), "left", BOLD, 10.0)], 13.0)]
        rows += [Row([Cell(LEFT + 30.0, str(x), "left", BOLD, 10.0)], 13.0) for x in re_lines[1:]]
        rows[-1].height += 10.0
        blocks.append(Block(rows, keep=True))
    if f.get("salutation"):
        blocks.append(Block([Row([Cell(LEFT, str(f["salutation"]))], 20.0)]))
    blocks += body_items(f.get("body", []), keep, where)
    if f.get("closing"):
        blocks.append(Block([Row([Cell(LEFT, str(f["closing"]))], 16.0)], keep=True, keep_with_next=True))
    for sig in f.get("signatures", []) or []:
        blocks.append(signature_block({"style": "letter", **sig}, where))
    if f.get("countersign"):
        cs = f["countersign"]
        blocks.append(heading(str(cs.get("heading", "ACKNOWLEDGED AND AGREED:"))))
        blocks += [signature_block(s, where) for s in cs.get("signatures", [])]
    tail: list[str] = []
    if f.get("enclosures"):
        tail.append("Enclosures: " + "; ".join(f["enclosures"]))
    if f.get("cc"):
        tail.append("cc: " + "; ".join(f["cc"]))
    if tail:
        blocks.append(Block(line_rows(tail, size=9.0, leading=12.0), keep=True))
    return blocks


def _agreement(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any], keep: list[str]) -> list[Block]:
    where = f"document {doc.id}"
    issuer = _party(spec, f.get("issuer"), where)
    blocks: list[Block] = letterhead(issuer) if issuer else []
    title_rows = [Row([Cell(PAGE_W / 2, str(f.get("title", "AGREEMENT")), "center", BOLD, 14.0)], 18.0)]
    title_rows += [Row([Cell(PAGE_W / 2, str(s), "center", BODY, 10.0)], 13.0) for s in f.get("subtitle", []) or []]
    title_rows[-1].height += 12.0
    blocks.append(Block(title_rows, keep=True))
    if f.get("preamble"):
        blocks.append(paragraph(str(f["preamble"]), keep))
    if f.get("recitals"):
        blocks.append(heading("RECITALS"))
        for r in f["recitals"]:
            blocks.append(paragraph(str(r), keep))
        if f.get("recitals_close"):
            blocks.append(paragraph(str(f["recitals_close"]), keep))
    for n, section in enumerate(f.get("sections", []) or [], start=1):
        number = section.get("number", f"{n}.")
        blocks.append(heading(f"{number} {section['heading']}"))
        blocks += body_items(section.get("body", []), keep, f"{where} section {number}")
    if f.get("witness"):
        blocks.append(paragraph(str(f["witness"]), keep))
    blocks += [signature_block(s, where) for s in f.get("signatures", []) or []]
    for ex in f.get("exhibits", []) or []:
        blocks.append(spacer(10.0))
        blocks.append(heading(str(ex["title"])))
        blocks += body_items(ex.get("body", []), keep, where)
    return blocks


def _memo(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any], keep: list[str]) -> list[Block]:
    where = f"document {doc.id}"
    issuer = _party(spec, f.get("issuer"), where)
    blocks: list[Block] = letterhead(issuer) if issuer else []
    blocks.append(Block([Row([Cell(LEFT, str(f.get("title", "MEMORANDUM")), "left", BOLD, 16.0)], 26.0)], keep=True))
    pairs = [[label, f[key]] for key, label in (("to", "TO"), ("from", "FROM"), ("cc", "CC"), ("date", "DATE"), ("re", "RE")) if f.get(key)]
    rows = kv_rows(pairs, keep)
    rows[-1].rule_below = True
    rows[-1].height += 14.0
    blocks.append(Block(rows, keep=True))
    blocks += body_items(f.get("body", []), keep, where)
    return blocks


def _form(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any], keep: list[str]) -> list[Block]:
    where = f"document {doc.id}"
    issuer = _party(spec, f.get("issuer"), where)
    blocks: list[Block] = letterhead(issuer) if issuer else []
    rows = [Row([Cell(LEFT, str(f.get("title", "")), "left", BOLD, 14.0)], 18.0)]
    rows += [Row([Cell(LEFT, str(s), "left", BODY, 10.0)], 13.0) for s in f.get("subtitle", []) or []]
    rows[-1].height += 10.0
    blocks.append(Block(rows, keep=True))
    if f.get("meta"):
        meta = kv_rows(f["meta"], keep)
        meta[-1].height += 10.0
        blocks.append(Block(meta, keep=True))
    blocks += body_items(f.get("body", []), keep, where)
    return blocks


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _paginate(blocks: list[Block]) -> list[list[tuple[str, Any, float]]]:
    pages: list[list[tuple[str, Any, float]]] = [[]]
    y = TOP
    for i, blk in enumerate(blocks):
        if blk.keep_with_next and i + 1 < len(blocks) and pages[-1]:
            nxt = blocks[i + 1]
            need = blk.height() + (nxt.height() if nxt.keep or nxt.columns is not None else nxt.rows[0].height)
            if y - need + (nxt.rows[-1].height if nxt.keep and nxt.rows else 0) < BOTTOM:
                pages.append([])
                y = TOP
        if blk.columns is not None:
            if y - blk.height() < BOTTOM and pages[-1]:
                pages.append([])
                y = TOP
            pages[-1].append(("cols", blk, y))
            y -= blk.height()
            continue
        if blk.keep and y - (blk.height() - blk.rows[-1].height) < BOTTOM and pages[-1]:
            pages.append([])
            y = TOP
        for row in blk.rows:
            if y < BOTTOM:
                pages.append([])
                y = TOP
            if row.cells or pages[-1]:
                pages[-1].append(("row", row, y))
            y -= row.height
    return [p for p in pages if p] or [[]]


def _draw_row(c: canvas.Canvas, row: Row, y: float) -> None:
    placed: list[tuple[float, Cell]] = []
    for cell in row.cells:
        if not cell.text:
            continue
        w = stringWidth(cell.text, cell.font, cell.size)
        x = cell.x - w if cell.align == "right" else cell.x - w / 2 if cell.align == "center" else cell.x
        placed.append((x, cell))
    if placed:
        placed.sort(key=lambda p: p[0])
        t = c.beginText()
        t.setFillGray(row.gray)
        t.setTextOrigin(placed[0][0], y)
        cur = placed[0][0]
        for x, cell in placed:
            if x != cur:
                t.moveCursor(x - cur, 0)
                cur = x
            t.setFont(cell.font, cell.size)
            t.textOut(cell.text)
        c.drawText(t)
    if row.rule_below:
        c.setLineWidth(0.6)
        c.line(LEFT, y - 5, RIGHT, y - 5)


def _draw_page(c: canvas.Canvas, items: list[tuple[str, Any, float]], page_no: int, n_pages: int,
               draft: bool, continuation: str) -> None:
    if draft:
        c.saveState()
        c.setFillGray(0.86)
        c.setFont(BOLD, 110)
        c.translate(PAGE_W / 2, PAGE_H / 2)
        c.rotate(45)
        c.drawCentredString(0, -30, "DRAFT")
        c.restoreState()
        c.setFillColorRGB(0.7, 0.0, 0.0)
        c.setFont(BOLD, 9)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 34, DRAFT_BANNER)
        c.setFillGray(0)
    if page_no > 1 and continuation:
        c.setFont(ITALIC, 8)
        c.drawString(LEFT, PAGE_H - 48, continuation)
    for kind, obj, y in items:
        if kind == "row":
            _draw_row(c, obj, y)
        else:
            for col in obj.columns:
                yy = y
                for row in col:
                    _draw_row(c, row, yy)
                    yy -= row.height
    c.setFillGray(0.35)
    c.setFont(BODY, 7.5)
    c.drawCentredString(PAGE_W / 2, 40, FOOTER)
    c.drawRightString(RIGHT, 28, f"Page {page_no} of {n_pages}")
    c.setFillGray(0)


def _pdf_bytes(spec: DealSpec, doc: DocumentSpec, blocks: list[Block], author: str) -> bytes:
    for blk in blocks:
        for row in [*blk.rows, *[r for col in (blk.columns or []) for r in col]]:
            for cell in row.cells:
                _check_text(cell.text, f"document {doc.id}")
    pages = _paginate(blocks)
    buf = io.BytesIO()
    # invariant=1 freezes CreationDate/ModDate/ID so identical input gives identical bytes.
    c = canvas.Canvas(buf, pagesize=letter, invariant=1)
    c.setTitle(doc.title or doc.filename.rsplit(".", 1)[0])
    c.setAuthor(author)
    c.setSubject("SYNTHETIC document generated for QoE Evidence Review testing")
    c.setCreator("qoe_synth deal generator")
    c.setProducer("ReportLab PDF Library")
    c.setKeywords("SYNTHETIC")
    heading_title = str(doc.fields.get("title", "")).strip()
    continuation = f"{author} — {heading_title} (continued)" if heading_title else f"{author} (continued)"
    for i, items in enumerate(pages, start=1):
        _draw_page(c, items, i, len(pages), doc.draft, continuation)
        c.showPage()
    c.save()
    return buf.getvalue()


def resolve_row_refs(value: Any, rows: dict[str, Txn], where: str) -> Any:
    if isinstance(value, dict):
        return {k: resolve_row_refs(v, rows, where) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_row_refs(v, rows, where) for v in value]
    if not isinstance(value, str) or "{" not in value:
        return value

    def sub(m: re.Match[str]) -> str:
        kind, key = m.group(1), m.group(2)
        t = rows.get(key)
        if t is None:
            raise GenerationError(f"{where}: {m.group(0)} cites unknown row key {key!r}")
        if kind == "amount":
            return money(abs(t.amount), dollar=False)
        if kind == "date":
            return f"{MONTH_NAME[t.date.month - 1]} {t.date.day}, {t.date.year}"
        if kind == "mdy":
            return t.date.strftime("%m/%d/%Y")
        return str(getattr(t, kind))

    return _ROW_REF.sub(sub, value)


def _email(spec: DealSpec, doc: DocumentSpec, f: dict[str, Any]) -> str:
    headers = [("From", f.get("from")), ("To", f.get("to")), ("Cc", f.get("cc")), ("Date", f.get("date")),
               ("Subject", f.get("subject")), ("Attachments", f.get("attachments"))]
    out = [f"{k}: {'; '.join(v) if isinstance(v, list) else v}" for k, v in headers if v]
    body = str(f.get("body", "")).rstrip("\n")
    return "\n".join(out) + "\n\n" + body + "\n\n--\n" + FOOTER + "\n"


TEMPLATES = {"invoice": _invoice, "letter": _letter, "agreement": _agreement, "memo": _memo, "form": _form}


def render_document(spec: DealSpec, doc: DocumentSpec, rows: Optional[dict[str, Txn]] = None) -> Rendered:
    where = f"document {doc.id}"
    doc = doc.model_copy(update={
        "fields": resolve_row_refs(doc.fields, rows or {}, where),
        "key_phrases": resolve_row_refs(list(doc.key_phrases), rows or {}, where),
    })
    keep = list(doc.key_phrases)
    if doc.template == "email":
        if not doc.filename.endswith((".txt", ".eml", ".md")):
            raise GenerationError(f"document {doc.id}: emails are written as .txt/.eml/.md")
        text = _email(spec, doc, doc.fields)
        rendered = Rendered(text.encode("utf-8"), canonicalize_page_text(text))
    else:
        if not doc.filename.endswith(".pdf"):
            raise GenerationError(f"document {doc.id}: template {doc.template} renders a .pdf")
        stated: Optional[Decimal] = None
        if doc.template == "invoice":
            blocks, stated = _invoice(spec, doc, doc.fields, keep)
        else:
            blocks = TEMPLATES[doc.template](spec, doc, doc.fields, keep)
        issuer = _party(spec, doc.fields.get("issuer"), f"document {doc.id}")
        data = _pdf_bytes(spec, doc, blocks, issuer.name if issuer else spec.company.name)
        pages = [canonicalize_page_text(p) for p in extract_pdf_pages(data)]
        for n, page in enumerate(pages, start=1):
            if FOOTER not in page:
                raise GenerationError(f"document {doc.id}: footer missing from page {n}")
        rendered = Rendered(data, "\n\f\n".join(pages), stated)
    for phrase in doc.key_phrases:
        if phrase not in rendered.text:
            raise GenerationError(f"document {doc.id}: key phrase {phrase!r} not found verbatim in extracted text")
    if doc.draft and "DRAFT" not in rendered.text:
        raise GenerationError(f"document {doc.id}: draft marking not extractable")
    return rendered
