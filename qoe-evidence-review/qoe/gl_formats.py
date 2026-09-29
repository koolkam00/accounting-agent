"""General-ledger and chart-of-accounts readers for QoE deal packages (SPEC §3.3-3.4).

Three GL exports are supported: a QuickBooks Online "General Ledger" CSV
(``qbo_gl_csv``), a NetSuite saved-search CSV (``netsuite_csv``) and a Xero
"Account Transactions" workbook (``xero_xlsx``). Readers work on a generic row
table, so the container (CSV or xlsx) does not have to match the usual one.

Every reader returns debit-positive ``GLEntry`` rows. ``source_row`` is the row
number a spreadsheet app shows for the file (title, blank and header rows
included), because ground truth and reviewers cite GL rows by that number.

The chart of accounts maps each account to an ``EbitdaClass`` with the ordered
rules of SPEC §3.4; the rule that fired is kept in ``Account.mapping_basis``.
Accounts that no rule recognises fall back to OPEX with a basis starting with
``FALLBACK_BASIS`` so reconciliation can raise ``UNMAPPED_ACCOUNT``.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional, Sequence
from xml.etree import ElementTree

import openpyxl
from openpyxl.utils.cell import coordinate_to_tuple, get_column_letter

from qoe.money import D, fmt
from qoe.schemas import Account, EbitdaClass, GLEntry

QBO = "qbo_gl_csv"
NETSUITE = "netsuite_csv"
XERO = "xero_xlsx"
GL_FORMATS = (QBO, NETSUITE, XERO)

XERO_SHEET = "Account Transactions"
FALLBACK_BASIS = "fallback"
DETECT_ROWS = 10

Row = list[object]

# ---------------------------------------------------------------------------
# Cell helpers (shared with qoe.ingest)
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")


def clean_text(value: object) -> str:
    """Cell value as trimmed text with whitespace runs collapsed ("" for blank)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _WS.sub(" ", str(value)).strip()


def norm_key(value: object) -> str:
    """Case- and whitespace-insensitive key for header / label comparison."""
    return clean_text(value).casefold()


def is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def parse_money(value: object) -> Optional[Decimal]:
    """Amount cell -> Decimal; None when blank. Raises ValueError for non-numeric text
    (``UncachedFormulaError`` for a formula saved without its value)."""
    if isinstance(value, UncachedFormula):
        raise value.error()
    if is_blank(value):
        return None
    if isinstance(value, bool):
        raise ValueError(f"not a money value: {value!r}")
    if isinstance(value, (int, float, Decimal)):
        return D(value)
    text = str(value).replace("\u2212", "-").replace("\u00a0", " ").strip()
    if text.upper().startswith("USD"):
        text = text[3:]
    return D(text)


_US_DATE_FORMATS = ("%m/%d/%Y", "%m/%d/%y")
_DAYFIRST_DATE_FORMATS = ("%d/%m/%Y", "%d/%m/%y")
_OTHER_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y%m%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d-%b-%Y",
    "%d-%b-%y",
)
_EXCEL_EPOCH = date(1899, 12, 30)
_EXCEL_SERIAL_RANGE = (20000, 80000)  # 1954-10-03 .. 2119-01-10: any plausible ledger date
# Exports append a time of day: "1/7/2024 0:00", "01/07/2024 12:00:00 AM", "2024-01-07T00:00:00".
_TIME_SUFFIX = re.compile(r"(?:\s+|T)\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:\s*[AaPp]\.?[Mm]\.?)?$")
_SERIAL_TEXT = re.compile(r"^\d{5}(?:\.\d+)?$")
_SLASH_DATE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b")


def parse_date(value: object, *, dayfirst: bool = False) -> Optional[date]:
    """Date cell -> date. Handles Excel dates / serials and common text layouts.

    Slash dates are month-first (US exports) unless ``dayfirst``. A trailing time
    of day is ignored, and a five-digit text cell is read as an Excel serial
    (some exports write the serial as text).
    """
    if isinstance(value, UncachedFormula):
        raise value.error()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if _EXCEL_SERIAL_RANGE[0] <= value <= _EXCEL_SERIAL_RANGE[1]:
            return _EXCEL_EPOCH + timedelta(days=int(value))
        return None
    text = clean_text(value)
    if not text or not any(ch.isdigit() for ch in text):
        return None
    if _SERIAL_TEXT.match(text):
        serial = float(text)
        if _EXCEL_SERIAL_RANGE[0] <= serial <= _EXCEL_SERIAL_RANGE[1]:
            return _EXCEL_EPOCH + timedelta(days=int(serial))
        return None
    text = _TIME_SUFFIX.sub("", text).strip()
    text = re.sub(r"\bSept\b", "Sep", text, flags=re.IGNORECASE)
    slash = _DAYFIRST_DATE_FORMATS if dayfirst else _US_DATE_FORMATS
    for pattern in (*slash, *_OTHER_DATE_FORMATS):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def detect_dayfirst(values: Iterable[object], default: bool, what: str) -> bool:
    """Whether a column of slash dates is day-first (D/M/Y) or month-first (M/D/Y).

    A first component above 12 proves day-first ("15/01/2024"); a second one above
    12 proves month-first ("01/15/2024"). With no proof either way ``default`` is
    kept. A column with both kinds cannot be read safely, so it raises.
    """
    day_first: Optional[str] = None
    month_first: Optional[str] = None
    for value in values:
        if not isinstance(value, str):
            continue
        m = _SLASH_DATE.match(value.strip())
        if not m:
            continue
        first, second = int(m.group(1)), int(m.group(2))
        if first > 31 or second > 31 or (first > 12 and second > 12):
            continue  # not a date either way; proves nothing
        if first > 12 and day_first is None:
            day_first = value.strip()
        if second > 12 and month_first is None:
            month_first = value.strip()
        if day_first and month_first:
            raise ValueError(
                f"{what}: the date column mixes day-first ({day_first!r}) and month-first ({month_first!r}) "
                "dates, so no date can be read safely; re-export the file with one date format"
            )
    if day_first:
        return True
    if month_first:
        return False
    return default


_MONTH_FORMATS = ("%b %Y", "%B %Y", "%Y-%m", "%b-%Y", "%B-%Y", "%b-%y", "%b %y", "%m/%Y", "%b. %Y", "%Y-%m-%d")


def parse_month(value: object) -> Optional[str]:
    """Month header cell ("Jan 2024", "January 2024", "2024-01", Excel date) -> "YYYY-MM"."""
    if isinstance(value, (datetime, date)):
        return f"{value.year:04d}-{value.month:02d}"
    if not isinstance(value, str):
        return None
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"\bSept\b", "Sep", text, flags=re.IGNORECASE)
    for pattern in _MONTH_FORMATS:
        try:
            parsed = datetime.strptime(text, pattern)
        except ValueError:
            continue
        return f"{parsed.year:04d}-{parsed.month:02d}"
    return None


@dataclass
class Table:
    """Rows of one sheet (``rows[i]`` is spreadsheet row ``i + 1``) plus what loading noticed."""

    rows: list[Row]
    notes: list[str] = field(default_factory=list)
    # (row index, column index) -> Excel number format, for numeric cells with a non-General
    # format; only filled when requested (a numeric Ref "1.10" is stored as 1.1).
    number_formats: dict[tuple[int, int], str] = field(default_factory=dict)


def read_table(path: Path, sheet: Optional[str] = None, *, keep_number_formats: bool = False) -> Table:
    """All rows of a CSV or xlsx sheet, with loading notes.

    xlsx: the named sheet is used when present (case-insensitive), else the first
    sheet. The sheet's stored ``<dimension>`` is ignored (read-only openpyxl would
    otherwise stop at a stale one and silently drop rows). A formula cell saved
    without its calculated value becomes an ``UncachedFormula`` placeholder: blank
    as text, an error when read as an amount or a date, and listed in a note.

    CSV / text: UTF-16 (Excel "Unicode Text") and UTF-8 are recognised; lines that
    are not valid UTF-8 fall back to Windows-1252 one line at a time, with a note.
    Tab-delimited text is detected.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        return _read_xlsx(path, sheet, keep_number_formats)
    if suffix in (".csv", ".txt", ".tsv"):
        text, notes = _decode_text_table(path.read_bytes(), path.name)
        delimiter = _sniff_delimiter(text)
        # Each csv record is one spreadsheet row, blank lines included.
        rows = [list(r) for r in csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)]
        return Table(rows=rows, notes=notes)
    raise ValueError(f"unsupported table file type: {path.name} (expected .csv or .xlsx)")


def load_table_rows(path: Path, sheet: Optional[str] = None) -> list[Row]:
    """All rows of a CSV or xlsx sheet; ``rows[i]`` is spreadsheet row ``i + 1`` (see ``read_table``)."""
    return read_table(path, sheet).rows


_FORMULA_TAG = re.compile(rb"<(?:\w+:)?f[\s>/]")


def _sheet_has_formulas(path: Path, worksheet_part: str) -> bool:
    """Cheap pre-check (a byte search, no XML parsing): does the sheet contain a formula element?"""
    try:
        with zipfile.ZipFile(path) as zf:
            return bool(_FORMULA_TAG.search(zf.read(worksheet_part)))
    except (zipfile.BadZipFile, OSError, KeyError):
        return False


class UncachedFormula:
    """Stands in for a formula cell saved without its calculated value.

    Script-written workbooks (openpyxl, some exporters) store the formula but no result,
    so the cell's value is unknown. It reads as blank text, but using it as an amount or a
    date raises ``UncachedFormulaError`` instead of silently becoming 0.
    """

    __slots__ = ("file", "coordinate", "formula")

    def __init__(self, file: str, coordinate: str, formula: str) -> None:
        self.file, self.coordinate, self.formula = file, coordinate, formula

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"UncachedFormula({self.file} {self.coordinate} ={self.formula})"

    def error(self) -> "UncachedFormulaError":
        return UncachedFormulaError(
            f"{self.file}: cell {self.coordinate} holds a formula (={self.formula}) saved without its calculated "
            "value, so its amount is unknown. The file was probably written by a script: open and save it in "
            "Excel or LibreOffice so the values are stored, then rerun."
        )


class UncachedFormulaError(ValueError):
    """An amount or date cell is a formula with no stored value (see ``UncachedFormula``)."""


def _read_xlsx(path: Path, sheet: Optional[str], keep_number_formats: bool) -> Table:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = _pick_sheet(wb, sheet)
        worksheet_part = getattr(ws, "_worksheet_path", None)
        ws.reset_dimensions()
        formats: dict[tuple[int, int], str] = {}
        if keep_number_formats:
            rows = []
            for r_idx, cells in enumerate(ws.iter_rows()):
                row = []
                for c_idx, cell in enumerate(cells):
                    value = cell.value
                    row.append(value)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        number_format = getattr(cell, "number_format", None)
                        if number_format and number_format != "General":
                            formats[(r_idx, c_idx)] = number_format
                rows.append(row)
        else:
            rows = [list(r) for r in ws.iter_rows(values_only=True)]
    finally:
        wb.close()
    notes: list[str] = []
    if worksheet_part and _sheet_has_formulas(path, worksheet_part):
        uncached = _uncached_formula_cells(path, worksheet_part)
        for (r_idx, c_idx), (coordinate, formula) in uncached.items():
            while len(rows) <= r_idx:
                rows.append([])
            row = rows[r_idx] = list(rows[r_idx])
            row.extend([None] * (c_idx + 1 - len(row)))
            row[c_idx] = UncachedFormula(path.name, coordinate, formula)
        if uncached:
            listed = [f"{coord} ={formula}" for coord, formula in uncached.values()]
            sample = "; ".join(listed[:8]) + ("; ..." if len(listed) > 8 else "")
            notes.append(
                f"{path.name}: {len(listed)} formula cell(s) have no stored value ({sample}); they read as blank "
                "text and stop the run if used as an amount or date. Open and save the file in Excel or "
                "LibreOffice so the values are stored."
            )
    return Table(rows=rows, notes=notes, number_formats=formats)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _uncached_formula_cells(path: Path, worksheet_part: str) -> dict[tuple[int, int], tuple[str, str]]:
    """(row index, column index) -> (coordinate, formula) for formula cells without a cached value.

    Read from the sheet XML because openpyxl cannot tell an uncached formula from one whose
    cached result is an empty string: Excel marks the latter ``t="str"``.
    """
    out: dict[tuple[int, int], tuple[str, str]] = {}
    with zipfile.ZipFile(path) as zf, zf.open(worksheet_part) as fh:
        row_no, col_no = 0, 0
        for event, elem in ElementTree.iterparse(fh, events=("start", "end")):
            tag = _local(elem.tag)
            if event == "start":
                if tag == "row":
                    r = elem.get("r")
                    row_no, col_no = (int(r) if r and r.isdigit() else row_no + 1), 0
                continue
            if tag == "c":
                ref = elem.get("r")
                if ref:
                    row_no, col_no = coordinate_to_tuple(ref)
                else:
                    col_no += 1
                formula = value = None
                for child in elem:
                    if _local(child.tag) == "f":
                        formula = child
                    elif _local(child.tag) == "v":
                        value = child
                if formula is not None and elem.get("t") != "str" and (value is None or not (value.text or "").strip()):
                    coordinate = ref or f"{get_column_letter(col_no)}{row_no}"
                    out[(row_no - 1, col_no - 1)] = (coordinate, (formula.text or "").strip())
                elem.clear()
            elif tag == "row":
                elem.clear()
    return out


def _decode_text_table(data: bytes, name: str) -> tuple[str, list[str]]:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), []
    head = data[:400]
    if len(head) >= 4 and head.count(0) * 3 >= len(head):
        # UTF-16 without a byte-order mark: every other byte of ASCII text is NUL.
        odd_nuls = head[1::2].count(0)
        return data.decode("utf-16-le" if odd_nuls >= head[0::2].count(0) else "utf-16-be", errors="replace"), [
            f"{name}: read as UTF-16 text (no byte-order mark)"
        ]
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        return data.decode("utf-8"), []
    except UnicodeDecodeError:
        pass
    # Mixed files (a UTF-8 export with a few Windows-1252 bytes pasted in) are decoded line by
    # line, so one stray byte does not turn every other line, and the header, into mojibake.
    lines: list[str] = []
    fallback: list[int] = []
    for lineno, raw in enumerate(data.split(b"\n"), start=1):
        try:
            lines.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            lines.append(raw.decode("cp1252", errors="replace"))
            fallback.append(lineno)
    sample = ", ".join(str(n) for n in fallback[:10]) + (", ..." if len(fallback) > 10 else "")
    return "\n".join(lines), [f"{name}: {len(fallback)} line(s) are not valid UTF-8 and were decoded as Windows-1252 (lines {sample})"]


def _sniff_delimiter(text: str) -> str:
    sample = [line for line in text.splitlines()[:30] if line.strip()]
    tabs = sum(line.count("\t") for line in sample)
    commas = sum(line.count(",") for line in sample)
    return "\t" if tabs > commas else ","


def _pick_sheet(wb, preferred: Optional[str]):
    if preferred:
        for name in wb.sheetnames:
            if name.strip().casefold() == preferred.casefold():
                return wb[name]
    return wb.worksheets[0]


def _cell(row: Sequence[object], idx: Optional[int]) -> object:
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _header_map(row: Sequence[object]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, value in enumerate(row):
        key = norm_key(value)
        if key and key not in out:
            out[key] = i
    return out


def _col(cols: dict[str, int], *candidates: str) -> Optional[int]:
    for cand in candidates:
        if cand in cols:
            return cols[cand]
    return None


class _SkipLog:
    """Collects skipped rows by reason so ingest notes say what was dropped and where."""

    def __init__(self) -> None:
        self._rows: dict[str, list[int]] = {}
        # Rows that carry money but could not be dated: real transactions, not totals.
        self._undated: list[tuple[int, str]] = []
        self._undated_total = Decimal(0)

    def add(self, reason: str, row: int) -> None:
        self._rows.setdefault(reason, []).append(row)

    def add_undated(self, row: int, raw_date: object, amounts: Sequence[object]) -> None:
        self._undated.append((row, clean_text(raw_date)))
        for cell in amounts:
            try:
                value = parse_money(cell)
            except ValueError:
                continue
            if value is not None:
                self._undated_total += abs(value)

    def notes(self, label: str) -> list[str]:
        out = []
        if self._undated:
            sample = ", ".join(f"{r} ({d!r})" if d else str(r) for r, d in self._undated[:8]) + (", ..." if len(self._undated) > 8 else "")
            out.append(
                f"{label}: WARNING - dropped {len(self._undated)} row(s) that carry amounts "
                f"({fmt(self._undated_total)} in absolute value) but have no readable transaction date "
                f"(rows {sample}); check the Date column format and re-export if these are transactions"
            )
        for reason, rows in self._rows.items():
            sample = ", ".join(str(r) for r in rows[:8]) + (", ..." if len(rows) > 8 else "")
            out.append(f"{label}: skipped {len(rows)} {reason} (rows {sample})")
        return out


# ---------------------------------------------------------------------------
# Account labels and EBITDA classification
# ---------------------------------------------------------------------------

# An account number may carry sub-account segments joined by "." or "-" ("6000.10",
# "4000-10", "4-1000"), so a hyphen directly between digits belongs to the number. The
# name follows whitespace, or a separator ("·", ":", "–", or a hyphen next to a space or
# a letter: "4000 - Revenue", "4000-Revenue").
_ACCOUNT_NUMBER = r"\d+(?:[.\-]\d+)*"
_LABEL = re.compile(rf"^({_ACCOUNT_NUMBER})(?:\s*[·–—:]\s*|\s+-\s*|\s*-\s+|\s*-(?=[^\d\s])|\s+)(\S.*)$")
_NUMBER_ONLY = re.compile(rf"^{_ACCOUNT_NUMBER}$")


def account_path(text: object) -> str:
    """ "Office Expenses : Other" -> "Office Expenses:Other" (a QBO full name without numbers)."""
    return ":".join(s.strip() for s in clean_text(text).split(":") if s.strip())


def split_account_label(label: object) -> tuple[str, str]:
    """ "4000 Service Revenue - Commercial" -> ("4000", "Service Revenue - Commercial").

    Hierarchical labels ("700 Overheads : 710 Legal", "Parent:Child") resolve to the
    last segment. Without a leading number the number is "". Sub-account numbers
    keep their segments: "4000-10 Commercial" -> ("4000-10", "Commercial").
    """
    text = clean_text(label)
    if ":" in text:
        segments = [s.strip() for s in text.split(":") if s.strip()]
        if len(segments) > 1 and not _NUMBER_ONLY.match(segments[0]):
            first_numbered = bool(_LABEL.match(segments[0]))
            last_numbered = bool(_LABEL.match(segments[-1]) or _NUMBER_ONLY.match(segments[-1]))
            # "6600 Travel: Meals" is one account whose name has a colon; only
            # numbered or all-name paths are hierarchies.
            if last_numbered or not first_numbered:
                text = segments[-1]
    if _NUMBER_ONLY.match(text):
        return text, ""
    m = _LABEL.match(text)
    if m:
        return m.group(1), m.group(2).strip()
    return "", text


def _type_key(source_type: str) -> str:
    # Case, spaces and punctuation vary by system and export ("Other Expenses", "OTHER_EXPENSE",
    # "Cost of Sales"), so types are compared on their letters only.
    return re.sub(r"[^a-z]", "", source_type.casefold())


# Exact P&L account types. QBO labels them "Income", "Cost of Goods Sold", "Expenses",
# "Other Income", "Other Expense"; QBO outside the US and Sage say "Cost of Sales"; NetSuite
# shows "Income", "Cost of Goods Sold", "Expense", "Other Income", "Other Expense" in the UI and
# "COGS", "OthIncome", "OthExpense" as internal ids in saved-search exports; Xero uses REVENUE,
# SALES, DIRECTCOSTS, EXPENSE, OVERHEADS, OTHERINCOME, DEPRECIATN.
_TYPE_CLASSES: dict[str, EbitdaClass] = {
    "income": EbitdaClass.REVENUE,
    "revenue": EbitdaClass.REVENUE,
    "sales": EbitdaClass.REVENUE,
    "otherincome": EbitdaClass.OTHER_INCOME,
    "othincome": EbitdaClass.OTHER_INCOME,
    "costofgoodssold": EbitdaClass.COGS,
    "cogs": EbitdaClass.COGS,
    "directcosts": EbitdaClass.COGS,
    "costofsales": EbitdaClass.COGS,
    "costofsale": EbitdaClass.COGS,
    "expense": EbitdaClass.OPEX,
    "expenses": EbitdaClass.OPEX,
    "overheads": EbitdaClass.OPEX,
    "overhead": EbitdaClass.OPEX,
    "otherexpense": EbitdaClass.OTHER_EXPENSE,
    "otherexpenses": EbitdaClass.OTHER_EXPENSE,
    "othexpense": EbitdaClass.OTHER_EXPENSE,
    "depreciatn": EbitdaClass.DEPRECIATION,
    "depreciation": EbitdaClass.DEPRECIATION,
}
_INCOME_TYPES = frozenset({"income", "revenue", "sales", "otherincome", "othincome"})

# NetSuite internal ids for balance-sheet types that the substring hints below would miss.
_BS_EXACT_DEBIT = frozenset({"acctrec", "deferexpense", "unbilledrec"})
_BS_EXACT_CREDIT = frozenset({"acctpay", "credcard", "deferrevenue"})
_BS_EXACT_OTHER = frozenset({"stat"})

# Substrings of normalized source types that identify balance-sheet accounts
# (QBO, NetSuite and Xero vocabularies). Checked only after the exact P&L types,
# so "Deferred Revenue" lands here and not in REVENUE.
_BS_DEBIT_HINTS = ("asset", "bank", "receivable", "fixed", "inventory", "prepayment", "unbilled", "current")
_BS_CREDIT_HINTS = ("liabilit", "payable", "equity", "creditcard", "currliab", "termliab", "deferredrevenue", "accrued", "loan")
_BS_OTHER_HINTS = ("deferred", "noncurrent", "nonposting", "statistical", "retained", "suspense")


def _type_rule(source_type: str) -> tuple[Optional[EbitdaClass], str]:
    key = _type_key(source_type)
    if key in _TYPE_CLASSES:
        cls = _TYPE_CLASSES[key]
        return cls, f"type rule: {clean_text(source_type)} -> {cls.value}"
    if key in _BS_EXACT_DEBIT | _BS_EXACT_CREDIT | _BS_EXACT_OTHER or (
        key and any(h in key for h in (*_BS_CREDIT_HINTS, *_BS_DEBIT_HINTS, *_BS_OTHER_HINTS))
    ):
        return EbitdaClass.BALANCE_SHEET, f"type rule: {clean_text(source_type)} -> BALANCE_SHEET"
    return None, ""


_INTEREST_NAME = re.compile(r"interest\s+(expense|paid)|loan\s+interest|interest\s+income", re.I)
# On a non-operating (Other Income / Other Expense) account any mention of interest is
# financing: QBO's default "Interest Earned", "Mortgage Interest", "Interest - Line of
# Credit", "Bank Interest". Operating-typed names such as "Bank Charges & Interest" keep
# their type class; "interest-free" and ownership interests are not interest.
_INTEREST_WORD = re.compile(r"\binterest\b(?![\s-]*free)", re.I)
_NOT_INTEREST = re.compile(r"non[\s-]?controlling|minority|interest\s+in\b", re.I)
_NON_OPERATING_TYPES = frozenset({"otherincome", "othincome", "otherexpense", "otherexpenses", "othexpense"})
_DEPRECIATION_NAME = re.compile(r"depreciation", re.I)
_AMORTIZATION_NAME = re.compile(r"amorti[sz]ation", re.I)
_FINANCING_NAME = re.compile(r"loan|debt|financing", re.I)
# Payroll, sales, property and franchise taxes stay operating: their names do not say
# "income tax" ("Taxes - Federal Income" is an income tax; "State Income" alone is not a tax).
_INCOME_TAX_NAME = re.compile(r"income\s+tax|\btax(?:es)?\b.*\b(?:federal|state|provincial)\s+income\b", re.I)


def _name_rule(name: str, source_type: str = "") -> Optional[tuple[EbitdaClass, str]]:
    if _INTEREST_NAME.search(name):
        return EbitdaClass.INTEREST, "name rule: interest -> INTEREST"
    if (
        _type_key(source_type) in _NON_OPERATING_TYPES
        and _INTEREST_WORD.search(name)
        and not _NOT_INTEREST.search(name)
    ):
        return EbitdaClass.INTEREST, "name rule: interest on a non-operating (Other Income / Other Expense) account -> INTEREST"
    if _DEPRECIATION_NAME.search(name):
        return EbitdaClass.DEPRECIATION, "name rule: depreciation -> DEPRECIATION"
    if _AMORTIZATION_NAME.search(name):
        if _FINANCING_NAME.search(name):
            return EbitdaClass.INTEREST, "name rule: amortization of loan/debt/financing costs -> INTEREST"
        return EbitdaClass.AMORTIZATION, "name rule: amortization -> AMORTIZATION"
    if _INCOME_TAX_NAME.search(name):
        return EbitdaClass.TAXES, "name rule: income tax -> TAXES"
    return None


def classify_account(name: str, source_type: str) -> tuple[EbitdaClass, str]:
    """EBITDA class and basis from name and source type (rules 2-4 of SPEC §3.4)."""
    type_class, type_basis = _type_rule(source_type)
    if type_class is not EbitdaClass.BALANCE_SHEET:
        named = _name_rule(name, source_type)
        if named is not None:
            return named
    if type_class is None:
        shown = clean_text(source_type) or "(blank)"
        return EbitdaClass.OPEX, f"{FALLBACK_BASIS}: unrecognized account type {shown!r}; defaulted to OPEX"
    return type_class, type_basis


def is_fallback(account: Account) -> bool:
    return account.mapping_basis.startswith(FALLBACK_BASIS)


def is_credit_natural(account: Account) -> bool:
    """Whether a natural-sign export (QBO) shows this account's credits as positive.

    SPEC §3.3: REVENUE and OTHER_INCOME accounts, and any account with an income
    source type (e.g. "Interest Income" typed Other Income, class INTEREST).
    Liability and equity types are credit-natural too; the SPEC formula only
    covers P&L accounts, and a full-GL export shows them credit-positive.
    """
    key = _type_key(account.source_type)
    if key in _INCOME_TYPES or account.ebitda_class in (EbitdaClass.REVENUE, EbitdaClass.OTHER_INCOME):
        return True
    if key in _TYPE_CLASSES:
        return False
    return key in _BS_EXACT_CREDIT or (bool(key) and any(h in key for h in _BS_CREDIT_HINTS))


# ---------------------------------------------------------------------------
# Chart of accounts
# ---------------------------------------------------------------------------

_COA_NUMBER = ("account #", "number", "code", "*code", "account number", "account no.", "account no")
_COA_NAME = ("full name", "name", "*name", "account name")
_COA_TYPE = ("type", "*type", "account type")


def _parse_class(raw: str) -> Optional[EbitdaClass]:
    key = re.sub(r"[^A-Z]+", "_", raw.upper()).strip("_")
    try:
        return EbitdaClass(key)
    except ValueError:
        return None


def _read_overrides(path: Path) -> tuple[dict[str, tuple[EbitdaClass, str]], list[str]]:
    table = read_table(path)
    rows = table.rows
    notes: list[str] = list(table.notes)
    out: dict[str, tuple[EbitdaClass, str]] = {}
    if not rows:
        return out, [f"overrides {path.name}: empty file"]
    cols = _header_map(rows[0])
    acct_col, cls_col, basis_col = _col(cols, "account"), _col(cols, "ebitda_class", "ebitda class"), _col(cols, "basis")
    if acct_col is None or cls_col is None:
        raise ValueError(f"{path.name}: expected columns account,ebitda_class,basis; found {list(cols)}")
    for i, row in enumerate(rows[1:], start=2):
        account, raw_cls = clean_text(_cell(row, acct_col)), clean_text(_cell(row, cls_col))
        if not account and not raw_cls:
            continue
        cls = _parse_class(raw_cls)
        if not account or cls is None:
            notes.append(f"overrides {path.name}: row {i} ignored (account {account!r}, class {raw_cls!r} not recognised)")
            continue
        out[account] = (cls, clean_text(_cell(row, basis_col)))
    return out, notes


def _find_coa_header(rows: list[Row]) -> tuple[int, Optional[int], Optional[int], Optional[int], Optional[int]]:
    """Header row index and columns: (row, number, name, type, combined "Account" label)."""
    for i, row in enumerate(rows[:15]):
        cols = _header_map(row)
        num, name, typ = _col(cols, *_COA_NUMBER), _col(cols, *_COA_NAME), _col(cols, *_COA_TYPE)
        combined = _col(cols, "account") if num is None else None
        if name is not None or (combined is not None and typ is not None):
            return i, num, name, typ, combined
    found = [[clean_text(c) for c in r if not is_blank(c)] for r in rows[:5]]
    raise ValueError(f"chart of accounts: no header row with an account name column; first rows: {found}")


def read_chart_of_accounts(path: Path, overrides: Path | None = None) -> tuple[list[Account], list[str]]:
    """Accounts in file order with their EBITDA class, plus ingest notes."""
    path = Path(path)
    table = read_table(path)
    rows = table.rows
    h, num_col, name_col, type_col, combined_col = _find_coa_header(rows)
    notes: list[str] = list(table.notes)
    override_map: dict[str, tuple[EbitdaClass, str]] = {}
    if overrides is not None:
        override_map, override_notes = _read_overrides(Path(overrides))
        notes.extend(override_notes)

    accounts: list[Account] = []
    seen: set[str] = set()
    unnumbered: list[str] = []
    for i in range(h + 1, len(rows)):
        row = rows[i]
        number = clean_text(_cell(row, num_col))
        name = clean_text(_cell(row, name_col))
        if combined_col is not None:
            label_number, label_name = split_account_label(_cell(row, combined_col))
            number = label_number
            name = name or (label_name if label_number else clean_text(_cell(row, combined_col)))
        if not number and not name:
            continue
        if not number:
            label_number, label_name = split_account_label(name)
            if label_number:
                number, name = label_number, label_name
        if not number:
            # Without numbers the full name is the only unique key: QBO repeats leaf names under
            # different parents ("Services:Other" income, "Office Expenses:Other" expense).
            number = name = account_path(name)
            unnumbered.append(f"{i + 1} {name!r}")
        elif ":" in name:
            name = split_account_label(name)[1] or name
        if number in seen:
            notes.append(f"chart of accounts: duplicate account {number} at row {i + 1} ignored")
            continue
        seen.add(number)
        source_type = clean_text(_cell(row, type_col))
        override = override_map.get(number) or override_map.get(f"{number} {name}") or override_map.get(name)
        if override is not None:
            cls, why = override
            basis = f"override: {why}" if why else "override: account_mapping_overrides.csv"
        else:
            cls, basis = classify_account(name, source_type)
        accounts.append(Account(number=number, name=name, source_type=source_type, ebitda_class=cls, mapping_basis=basis))

    known = {a.number for a in accounts} | {a.name for a in accounts} | {f"{a.number} {a.name}" for a in accounts}
    for key in override_map:
        if key not in known:
            notes.append(f"overrides: account {key!r} is not in the chart of accounts; override ignored")
    if unnumbered:
        sample = "; ".join(unnumbered[:8]) + ("; ..." if len(unnumbered) > 8 else "")
        notes.append(f"chart of accounts: {len(unnumbered)} account(s) have no account number; the full account name is used as the id (rows {sample})")
    leaves: dict[str, list[str]] = {}
    for a in accounts:
        leaves.setdefault(a.name.rsplit(":", 1)[-1].casefold(), []).append(a.number)
    # Only unnumbered accounts are looked up by name, so only they can be confused.
    shared = {leaf: ids for leaf, ids in leaves.items() if len(ids) > 1 and any(not _NUMBER_ONLY.match(n) for n in ids)}
    if shared:
        listed = "; ".join(f"{leaf!r}: {', '.join(ids)}" for leaf, ids in sorted(shared.items()))
        notes.append(
            "chart of accounts: some account names repeat under different parents; a GL or P&L line naming only "
            f"the short name cannot be matched and is reported as not in the chart of accounts ({listed})"
        )
    counts: dict[str, int] = {}
    for a in accounts:
        counts[a.ebitda_class.value] = counts.get(a.ebitda_class.value, 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    n_over = sum(1 for a in accounts if a.mapping_basis.startswith("override"))
    n_fall = sum(1 for a in accounts if a.mapping_basis.startswith(FALLBACK_BASIS))
    notes.insert(0, f"chart of accounts {path.name}: {len(accounts)} accounts ({summary}); {n_over} override(s); {n_fall} fallback mapping(s)")
    for a in accounts:
        if a.mapping_basis.startswith(FALLBACK_BASIS):
            notes.append(f"chart of accounts: {a.number} {a.name}: {a.mapping_basis}")
    return accounts, notes


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


def _signature(cols: Iterable[str]) -> Optional[str]:
    keys = set(cols)
    if {"transaction type", "memo/description"} <= keys:
        return QBO
    if {"internal id", "debit"} <= keys:
        return NETSUITE
    if {"account code", "running balance"} <= keys:
        return XERO
    return None


def detect_format(path: Path) -> str:
    """Identify the GL export by header signature in its first rows (SPEC §3.3)."""
    path = Path(path)
    suffix = path.suffix.lower()
    has_xero_sheet = False
    if suffix in (".xlsx", ".xlsm"):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            has_xero_sheet = any(n.strip().casefold() == XERO_SHEET.casefold() for n in wb.sheetnames)
            ws = _pick_sheet(wb, XERO_SHEET)
            ws.reset_dimensions()  # a stale <dimension> ("A1") would hide the header row
            head = [list(r) for r in ws.iter_rows(max_row=DETECT_ROWS, values_only=True)]
        finally:
            wb.close()
    else:
        head = read_table(path).rows[:DETECT_ROWS]
    for wanted in (QBO, NETSUITE):
        if any(_signature(_header_map(r)) == wanted for r in head):
            return wanted
    if has_xero_sheet or any(_signature(_header_map(r)) == XERO for r in head):
        return XERO
    found = [[clean_text(c) for c in r if not is_blank(c)] for r in head]
    found = [r for r in found if r]
    raise ValueError(f"{path.name}: unrecognized GL export; headers found in the first {DETECT_ROWS} rows: {found}")


# ---------------------------------------------------------------------------
# GL readers
# ---------------------------------------------------------------------------


def _name_key(text: str) -> str:
    return account_path(text).casefold()


class AccountIndex:
    """Finds chart-of-accounts accounts by number, full name, or unambiguous short name.

    Used for labels without an account number (QBO with numbering off, P&L rows by
    name). A short name that several accounts share ("Other" under two parents) is
    never guessed: ``find`` returns no match and the candidates.
    """

    def __init__(self, accounts: Iterable[Account]) -> None:
        self.accounts = {a.number: a for a in accounts}
        self._exact: dict[str, list[Account]] = {}
        self._leaf: dict[str, list[Account]] = {}
        for a in self.accounts.values():
            for key in dict.fromkeys((_name_key(a.number), _name_key(a.name))):
                if key:
                    self._exact.setdefault(key, []).append(a)
            self._leaf.setdefault(_name_key(a.name).rsplit(":", 1)[-1], []).append(a)

    def find(self, number: str, name: str, path: str = "") -> tuple[Optional[Account], list[Account]]:
        """(account, ambiguous candidates). ``path`` is the "Parent:Child" name when known."""
        if number:
            return self.accounts.get(number), []
        for key in dict.fromkeys(k for k in (_name_key(path), _name_key(name)) if k):
            hits = self._exact.get(key, [])
            if len(hits) == 1:
                return hits[0], []
        wanted = _name_key(path or name)
        if not wanted:
            return None, []
        hits = self._leaf.get(wanted.rsplit(":", 1)[-1], [])
        if len(hits) > 1:
            # A longer path narrows it: "Office Expenses:Other" picks the child of that parent.
            narrowed = [a for a in hits if _name_key(a.name).endswith(":" + wanted) or wanted.endswith(":" + _name_key(a.name))]
            if len(narrowed) == 1:
                return narrowed[0], []
            return None, hits
        return (hits[0], []) if hits else (None, [])


class _AccountResolver:
    def __init__(self, accounts: dict[str, Account]) -> None:
        self.accounts = accounts
        self.index = AccountIndex(accounts.values())
        self.unknown: dict[str, str] = {}
        self.ambiguous: dict[str, list[str]] = {}

    def resolve(self, number: str, name: str, path: str = "") -> tuple[str, str, Optional[Account]]:
        acct, candidates = self.index.find(number, name, path)
        if acct is not None:
            return acct.number, acct.name, acct
        key = number or account_path(path) or name
        if candidates:
            self.ambiguous.setdefault(key, [a.number for a in candidates])
        else:
            self.unknown.setdefault(key, name)
        return key, name, None

    def notes(self, label: str, natural_sign: bool = False) -> list[str]:
        out = []
        how = " (natural-sign amounts kept as debit-positive)" if natural_sign else ""
        if self.unknown:
            listed = "; ".join(f"{k} {v}".strip() if k != v else k for k, v in sorted(self.unknown.items()))
            out.append(f"{label}: {len(self.unknown)} account(s) not in the chart of accounts{how}: {listed}")
        if self.ambiguous:
            listed = "; ".join(f"{k!r} could be {', '.join(v)}" for k, v in sorted(self.ambiguous.items()))
            out.append(
                f"{label}: WARNING - {len(self.ambiguous)} account label(s) without a number match more than one "
                f"chart-of-accounts account and were not matched{how}: {listed}. Export the GL with full account "
                "names or account numbers."
            )
        return out


def _find_header(rows: list[Row], fmt_name: str) -> tuple[int, dict[str, int]]:
    for i, row in enumerate(rows[:DETECT_ROWS]):
        cols = _header_map(row)
        if _signature(cols) == fmt_name:
            return i, cols
        if fmt_name == XERO and {"date", "debit", "credit"} <= set(cols) and ("account" in cols or "account code" in cols):
            return i, cols
    raise ValueError(f"no {fmt_name} header row found in the first {DETECT_ROWS} rows")


def _money_or_skip(value: object, rowno: int, skips: _SkipLog) -> tuple[bool, Optional[Decimal]]:
    try:
        return True, parse_money(value)
    except UncachedFormulaError:
        raise
    except ValueError:
        skips.add("rows with an unparseable amount", rowno)
        return False, None


def _entry(
    rowno: int,
    when: date,
    number: str,
    name: str,
    amount: Decimal,
    source: str,
    txn_type: object = None,
    doc_number: object = None,
    counterparty: object = None,
    memo: object = None,
    dimensions: Optional[dict[str, str]] = None,
) -> GLEntry:
    iso = when.isoformat()
    return GLEntry(
        entry_id=f"GL-R{rowno}",
        date=iso,
        period=iso[:7],
        account=number,
        account_name=name,
        txn_type=clean_text(txn_type),
        doc_number=clean_text(doc_number),
        counterparty=clean_text(counterparty),
        memo=clean_text(memo),
        amount=fmt(amount),
        source_file=source,
        source_row=rowno,
        dimensions=dimensions or {},
    )


def _column_values(rows: list[Row], start: int, col: Optional[int]) -> list[object]:
    return [] if col is None else [_cell(r, col) for r in rows[start:]]


_QBO_TOTAL_FOR = re.compile(r"^total\s+for\s+(.*)$", re.I)
_QBO_TOTAL = re.compile(r"^total\s+(.*)$", re.I)


def _qbo_total_target(first: str, stack: list[str], has_amount: bool) -> Optional[str]:
    """Label a QBO subtotal row closes ("" = the grand TOTAL), or None if the row is not a total.

    QBO writes "Total for <account>"; QBO Desktop "Total <account>". An account whose own
    name starts with "Total" ("Total Care Janitorial", "Totalflex Rental") is a section
    header, so a bare "Total <x>" is a subtotal only when <x> is an open section or the
    row carries an amount.
    """
    if first.casefold() == "total":
        return ""
    m = _QBO_TOTAL_FOR.match(first)
    if m:
        return m.group(1).strip()
    m = _QBO_TOTAL.match(first)
    if m and (has_amount or m.group(1).strip().casefold() in (s.casefold() for s in stack)):
        return m.group(1).strip()
    return None


def _qbo_path(stack: list[str]) -> str:
    """ "Office Expenses" > "Other" section headers -> "Office Expenses:Other" (names only)."""
    return ":".join(split_account_label(s)[1] or s for s in stack)


def _read_qbo(rows: list[Row], accounts: dict[str, Account], source: str) -> tuple[list[GLEntry], list[str]]:
    h, cols = _find_header(rows, QBO)
    c_date = _col(cols, "date", "transaction date")
    c_type = _col(cols, "transaction type")
    c_num = _col(cols, "num", "no.", "ref no.", "number")
    c_name = _col(cols, "name")
    c_memo = _col(cols, "memo/description", "memo")
    c_amount = _col(cols, "amount")
    c_debit, c_credit = _col(cols, "debit"), _col(cols, "credit")
    c_acct = _col(cols, "distribution account", "account")
    if c_acct is None:
        c_acct = 0
    if c_date is None or (c_amount is None and c_debit is None):
        raise ValueError(f"{source}: QBO header lacks Date/Amount columns: {list(cols)}")
    use_debit_credit = c_amount is None
    dayfirst = detect_dayfirst(_column_values(rows, h + 1, c_date), False, source)

    resolver = _AccountResolver(accounts)
    skips = _SkipLog()
    entries: list[GLEntry] = []
    # Section headers nest (parent account, then sub-account); "Total for X" closes X.
    stack: list[str] = []
    for idx in range(h + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(c) for c in row):
            continue
        first = clean_text(_cell(row, c_acct))
        raw_date = _cell(row, c_date)
        when = parse_date(raw_date, dayfirst=dayfirst)
        amount_cells = (_cell(row, c_amount),) if not use_debit_credit else (_cell(row, c_debit), _cell(row, c_credit))
        has_amount = any(not is_blank(c) for c in amount_cells)
        if when is None:
            target = _qbo_total_target(first, stack, has_amount)
            if target is not None:
                label = target.casefold()
                if not label:
                    stack.clear()
                elif label in (s.casefold() for s in stack):
                    while stack and stack.pop().casefold() != label:
                        pass
                elif stack:
                    stack.pop()
                skips.add("total/subtotal rows", rowno)
            elif first and is_blank(raw_date) and not has_amount:
                stack.append(first)
            elif has_amount and (
                not is_blank(raw_date) or any(not is_blank(_cell(row, c)) for c in (c_type, c_num, c_name, c_memo) if c is not None)
            ):
                skips.add_undated(rowno, raw_date, amount_cells)
            else:
                skips.add("rows without a transaction date (e.g. beginning balance)", rowno)
            continue
        if first:
            label, path = first, first
        elif stack:
            label, path = stack[-1], _qbo_path(stack)
        else:
            skips.add("transaction rows outside any account section", rowno)
            continue
        number, name = split_account_label(label)
        number, name, acct = resolver.resolve(number, name, "" if number else path)
        if use_debit_credit:
            ok_d, debit = _money_or_skip(_cell(row, c_debit), rowno, skips)
            ok_c, credit = _money_or_skip(_cell(row, c_credit), rowno, skips)
            if not (ok_d and ok_c):
                continue
            if debit is None and credit is None:
                skips.add("transaction rows with a blank amount", rowno)
                continue
            amount = (debit or Decimal(0)) - (credit or Decimal(0))
        else:
            ok, natural = _money_or_skip(_cell(row, c_amount), rowno, skips)
            if not ok:
                continue
            if natural is None:
                skips.add("transaction rows with a blank amount", rowno)
                continue
            amount = -natural if acct is not None and is_credit_natural(acct) else natural
        entries.append(
            _entry(
                rowno, when, number, name, amount, source,
                txn_type=_cell(row, c_type), doc_number=_cell(row, c_num),
                counterparty=_cell(row, c_name), memo=_cell(row, c_memo),
            )
        )
    notes = skips.notes(source) + resolver.notes(source, natural_sign=not use_debit_credit)
    if dayfirst:
        notes.append(f"{source}: slash dates read day-first (D/M/Y): a day above 12 appears in the first position")
    return entries, notes


_NETSUITE_DIMENSIONS = ("Subsidiary", "Department", "Class", "Location")


def _netsuite_dayfirst(rows: list[Row], h: int, c_date: int, c_period: Optional[int], source: str) -> bool:
    dates = _column_values(rows, h + 1, c_date)
    dayfirst = detect_dayfirst(dates, False, source)
    if dayfirst or c_period is None or any(isinstance(d, str) and (m := _SLASH_DATE.match(d.strip())) and int(m.group(2)) > 12 for d in dates):
        return dayfirst
    # Only ambiguous slash dates (both parts <= 12): let the Period column decide.
    month_first_hits = day_first_hits = 0
    for row in rows[h + 1:]:
        raw, period = _cell(row, c_date), parse_month(_cell(row, c_period))
        m = _SLASH_DATE.match(raw.strip()) if isinstance(raw, str) else None
        if not m or period is None or m.group(1) == m.group(2):
            continue
        year = int(m.group(3)) + (2000 if len(m.group(3)) == 2 else 0)
        month_first_hits += f"{year:04d}-{int(m.group(1)):02d}" == period
        day_first_hits += f"{year:04d}-{int(m.group(2)):02d}" == period
    return day_first_hits > month_first_hits


def _read_netsuite(rows: list[Row], accounts: dict[str, Account], source: str) -> tuple[list[GLEntry], list[str]]:
    h, cols = _find_header(rows, NETSUITE)
    c_date, c_acct = _col(cols, "date"), _col(cols, "account")
    c_debit, c_credit = _col(cols, "debit"), _col(cols, "credit")
    c_type = _col(cols, "type", "transaction type")
    c_num = _col(cols, "document number", "document #", "doc number", "number")
    c_name = _col(cols, "name", "entity")
    c_memo = _col(cols, "memo", "memo (main)", "description")
    c_period = _col(cols, "period", "accounting period", "posting period")
    if c_date is None or c_acct is None or c_credit is None:
        raise ValueError(f"{source}: NetSuite header lacks Date/Account/Credit columns: {list(cols)}")
    dim_cols = [(d, _col(cols, d.casefold())) for d in _NETSUITE_DIMENSIONS]
    dayfirst = _netsuite_dayfirst(rows, h, c_date, c_period, source)

    resolver = _AccountResolver(accounts)
    skips = _SkipLog()
    entries: list[GLEntry] = []
    off_period: list[int] = []
    for idx in range(h + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(c) for c in row):
            continue
        raw_date = _cell(row, c_date)
        when = parse_date(raw_date, dayfirst=dayfirst)
        if when is None:
            amount_cells = (_cell(row, c_debit), _cell(row, c_credit))
            is_total = any(clean_text(c).casefold().startswith("total") for c in row)
            has_context = not is_blank(raw_date) or not is_blank(_cell(row, c_acct))
            if not is_total and has_context and any(not is_blank(c) for c in amount_cells):
                skips.add_undated(rowno, raw_date, amount_cells)
            else:
                skips.add("rows without a transaction date (e.g. totals)", rowno)
            continue
        label = clean_text(_cell(row, c_acct))
        if not label:
            skips.add("rows without an account", rowno)
            continue
        ok_d, debit = _money_or_skip(_cell(row, c_debit), rowno, skips)
        ok_c, credit = _money_or_skip(_cell(row, c_credit), rowno, skips)
        if not (ok_d and ok_c):
            continue
        if debit is None and credit is None:
            skips.add("rows with neither debit nor credit", rowno)
            continue
        number, name = split_account_label(label)
        number, name, _ = resolver.resolve(number, name, "" if number else label)
        period = parse_month(_cell(row, c_period)) if c_period is not None else None
        if period is not None and period != when.isoformat()[:7]:
            off_period.append(rowno)
        dims = {d: clean_text(_cell(row, c)) for d, c in dim_cols if c is not None and clean_text(_cell(row, c))}
        entries.append(
            _entry(
                rowno, when, number, name, (debit or Decimal(0)) - (credit or Decimal(0)), source,
                txn_type=_cell(row, c_type), doc_number=_cell(row, c_num),
                counterparty=_cell(row, c_name), memo=_cell(row, c_memo), dimensions=dims,
            )
        )
    notes = skips.notes(source) + resolver.notes(source)
    if dayfirst:
        notes.append(f"{source}: slash dates read day-first (D/M/Y), from the dates themselves or the Period column")
    if off_period:
        sample = ", ".join(str(r) for r in off_period[:10]) + (", ..." if len(off_period) > 10 else "")
        notes.append(
            f"{source}: {len(off_period)} row(s) are dated in a different month than their Period column "
            f"(rows {sample}); the month is taken from Date"
        )
    return entries, notes


_XERO_NON_TXN = re.compile(r"^(total\b|opening balance|closing balance|net movement)", re.I)


def _read_xero(rows: list[Row], accounts: dict[str, Account], source: str) -> tuple[list[GLEntry], list[str]]:
    h, cols = _find_header(rows, XERO)
    c_date = _col(cols, "date")
    c_source = _col(cols, "source")
    c_desc = _col(cols, "description")
    c_ref = _col(cols, "reference")
    c_debit, c_credit = _col(cols, "debit"), _col(cols, "credit")
    c_code, c_acct = _col(cols, "account code", "code"), _col(cols, "account")
    dayfirst = detect_dayfirst(_column_values(rows, h + 1, c_date), True, source)

    resolver = _AccountResolver(accounts)
    skips = _SkipLog()
    entries: list[GLEntry] = []
    section = ""  # grouped layouts put the account in a heading row instead of a column
    for idx in range(h + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(c) for c in row):
            continue
        raw_date = _cell(row, c_date)
        when = parse_date(raw_date, dayfirst=dayfirst)
        if when is None:
            first = next((clean_text(c) for c in row if not is_blank(c)), "")
            amount_cells = (_cell(row, c_debit), _cell(row, c_credit))
            if _XERO_NON_TXN.match(first):
                skips.add("total/balance rows", rowno)
            elif first and all(is_blank(c) for c in amount_cells):
                section = first
            elif any(not is_blank(c) for c in amount_cells):
                skips.add_undated(rowno, raw_date, amount_cells)
            else:
                skips.add("rows without a transaction date", rowno)
            continue
        code, acct_name = clean_text(_cell(row, c_code)), clean_text(_cell(row, c_acct))
        path = ""
        if code:
            number, name = split_account_label(code)
            number, name = (number, acct_name or name) if number else (code, acct_name)
        elif acct_name or section:
            number, name = split_account_label(acct_name or section)
            path = "" if number else (acct_name or section)
        else:
            skips.add("rows without an account", rowno)
            continue
        ok_d, debit = _money_or_skip(_cell(row, c_debit), rowno, skips)
        ok_c, credit = _money_or_skip(_cell(row, c_credit), rowno, skips)
        if not (ok_d and ok_c):
            continue
        if debit is None and credit is None:
            skips.add("rows with neither debit nor credit", rowno)
            continue
        number, name, _ = resolver.resolve(number, name, path)
        description = clean_text(_cell(row, c_desc))
        contact, sep, _rest = description.partition(" - ")
        entries.append(
            _entry(
                rowno, when, number, name, (debit or Decimal(0)) - (credit or Decimal(0)), source,
                txn_type=_cell(row, c_source), doc_number=_cell(row, c_ref),
                counterparty=contact if sep else "", memo=description,
            )
        )
    notes = skips.notes(source) + resolver.notes(source)
    if not dayfirst:
        notes.append(f"{source}: slash dates read month-first (M/D/Y): a day above 12 appears in the second position")
    return entries, notes


_READERS = {QBO: _read_qbo, NETSUITE: _read_netsuite, XERO: _read_xero}


def read_gl(
    path: Path,
    fmt: str,
    accounts: dict[str, Account],
    *,
    source_label: Optional[str] = None,
) -> tuple[list[GLEntry], list[str]]:
    """Debit-positive GL entries in file order, plus ingest notes.

    ``fmt`` is one of ``GL_FORMATS`` or "auto". ``source_label`` becomes
    ``GLEntry.source_file`` (default: the file name); ``load_deal`` passes the
    path relative to the deal directory.
    """
    path = Path(path)
    if fmt == "auto":
        fmt = detect_format(path)
    reader = _READERS.get(fmt)
    if reader is None:
        raise ValueError(f"unknown GL format {fmt!r}; expected one of {GL_FORMATS} or 'auto'")
    source = source_label or path.name
    table = read_table(path, XERO_SHEET if fmt == XERO else None)
    entries, notes = reader(table.rows, accounts, source)
    notes = [*table.notes, *notes]
    if entries:
        rows_used = f"rows {entries[0].source_row}-{entries[-1].source_row}"
        span = f"{min(e.date for e in entries)} to {max(e.date for e in entries)}"
        head = f"GL {source} ({fmt}): {len(entries)} entries read from {rows_used}, dated {span}"
    else:
        head = f"GL {source} ({fmt}): no entries read"
    return entries, [head, *notes]
