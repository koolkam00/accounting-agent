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
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional, Sequence

import openpyxl

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
    """Amount cell -> Decimal; None when blank. Raises ValueError for non-numeric text."""
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
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d-%b-%Y",
    "%d-%b-%y",
)
_EXCEL_EPOCH = date(1899, 12, 30)


def parse_date(value: object, *, dayfirst: bool = False) -> Optional[date]:
    """Date cell -> date. Handles Excel dates / serials and common text layouts.

    Slash dates are month-first (US exports) unless ``dayfirst`` (Xero).
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        # Only real spreadsheet numbers reach here; CSV cells are always text.
        if 20000 <= value <= 80000:
            return _EXCEL_EPOCH + timedelta(days=int(value))
        return None
    text = clean_text(value)
    if not text or not any(ch.isdigit() for ch in text):
        return None
    text = re.sub(r"\bSept\b", "Sep", text, flags=re.IGNORECASE)
    slash = _DAYFIRST_DATE_FORMATS if dayfirst else _US_DATE_FORMATS
    for pattern in (*slash, *_OTHER_DATE_FORMATS):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


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


def load_table_rows(path: Path, sheet: Optional[str] = None) -> list[Row]:
    """All rows of a CSV or xlsx sheet; ``rows[i]`` is spreadsheet row ``i + 1``.

    For xlsx the named sheet is used when present (case-insensitive), else the
    first sheet. CSV is decoded as UTF-8 (BOM tolerated), falling back to cp1252.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            ws = _pick_sheet(wb, sheet)
            return [list(r) for r in ws.iter_rows(values_only=True)]
        finally:
            wb.close()
    if suffix in (".csv", ".txt"):
        data = path.read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252")
        # Each csv record is one spreadsheet row, blank lines included.
        return [list(r) for r in csv.reader(io.StringIO(text, newline=""))]
    raise ValueError(f"unsupported table file type: {path.name} (expected .csv or .xlsx)")


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

    def add(self, reason: str, row: int) -> None:
        self._rows.setdefault(reason, []).append(row)

    def notes(self, label: str) -> list[str]:
        out = []
        for reason, rows in self._rows.items():
            sample = ", ".join(str(r) for r in rows[:8]) + (", ..." if len(rows) > 8 else "")
            out.append(f"{label}: skipped {len(rows)} {reason} (rows {sample})")
        return out


# ---------------------------------------------------------------------------
# Account labels and EBITDA classification
# ---------------------------------------------------------------------------

_LABEL = re.compile(r"^(\d+(?:\.\d+)?)(?:\s*[·\-–—:]\s*|\s+)(\S.*)$")
_NUMBER_ONLY = re.compile(r"^\d+(?:\.\d+)?$")


def split_account_label(label: object) -> tuple[str, str]:
    """ "4000 Service Revenue - Commercial" -> ("4000", "Service Revenue - Commercial").

    Hierarchical labels ("700 Overheads : 710 Legal", "Parent:Child") resolve to the
    last segment. Without a leading number the number is "".
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
_DEPRECIATION_NAME = re.compile(r"depreciation", re.I)
_AMORTIZATION_NAME = re.compile(r"amorti[sz]ation", re.I)
_FINANCING_NAME = re.compile(r"loan|debt|financing", re.I)
# Payroll, sales, property and franchise taxes stay operating: their names do not say "income tax".
_INCOME_TAX_NAME = re.compile(r"income\s+tax", re.I)


def _name_rule(name: str) -> Optional[tuple[EbitdaClass, str]]:
    if _INTEREST_NAME.search(name):
        return EbitdaClass.INTEREST, "name rule: interest -> INTEREST"
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
        named = _name_rule(name)
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
    rows = load_table_rows(path)
    notes: list[str] = []
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
    rows = load_table_rows(path)
    h, num_col, name_col, type_col, combined_col = _find_coa_header(rows)
    notes: list[str] = []
    override_map: dict[str, tuple[EbitdaClass, str]] = {}
    if overrides is not None:
        override_map, override_notes = _read_overrides(Path(overrides))
        notes.extend(override_notes)

    accounts: list[Account] = []
    seen: set[str] = set()
    for i in range(h + 1, len(rows)):
        row = rows[i]
        number = clean_text(_cell(row, num_col))
        name = clean_text(_cell(row, name_col))
        if combined_col is not None:
            label_number, label_name = split_account_label(_cell(row, combined_col))
            number = label_number
            name = name or label_name
        if not number and not name:
            continue
        if not number:
            number, name = split_account_label(name)
        if not number:
            notes.append(f"chart of accounts: row {i + 1} {name!r} has no account number; its name is used as the id")
            number = name
        if ":" in name:
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
            head = [list(r) for r in ws.iter_rows(max_row=DETECT_ROWS, values_only=True)]
        finally:
            wb.close()
    else:
        head = load_table_rows(path)[:DETECT_ROWS]
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


class _AccountResolver:
    def __init__(self, accounts: dict[str, Account]) -> None:
        self.accounts = accounts
        self.by_name = {a.name.casefold(): a for a in accounts.values()}
        self.unknown: dict[str, str] = {}

    def resolve(self, number: str, name: str) -> tuple[str, str, Optional[Account]]:
        if number and number in self.accounts:
            acct = self.accounts[number]
            return acct.number, acct.name, acct
        if not number and name.casefold() in self.by_name:
            acct = self.by_name[name.casefold()]
            return acct.number, acct.name, acct
        key = number or name
        self.unknown.setdefault(key, name)
        return key, name, None

    def notes(self, label: str, natural_sign: bool = False) -> list[str]:
        if not self.unknown:
            return []
        listed = "; ".join(f"{k} {v}".strip() if k != v else k for k, v in sorted(self.unknown.items()))
        how = " (natural-sign amounts kept as debit-positive)" if natural_sign else ""
        return [f"{label}: {len(self.unknown)} account(s) not in the chart of accounts{how}: {listed}"]


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
        when = parse_date(raw_date)
        amount_cells = (_cell(row, c_amount),) if not use_debit_credit else (_cell(row, c_debit), _cell(row, c_credit))
        if when is None:
            if first.casefold().startswith("total"):
                label = re.sub(r"^total(\s+for)?\s*", "", first, flags=re.I).casefold()
                if not label:
                    stack.clear()
                elif label in (s.casefold() for s in stack):
                    while stack and stack.pop().casefold() != label:
                        pass
                elif stack:
                    stack.pop()
                skips.add("total/subtotal rows", rowno)
            elif first and is_blank(raw_date) and all(is_blank(c) for c in amount_cells):
                stack.append(first)
            else:
                skips.add("rows without a transaction date (e.g. beginning balance)", rowno)
            continue
        label = first or (stack[-1] if stack else "")
        if not label:
            skips.add("transaction rows outside any account section", rowno)
            continue
        number, name, acct = resolver.resolve(*split_account_label(label))
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
    return entries, skips.notes(source) + resolver.notes(source, natural_sign=not use_debit_credit)


_NETSUITE_DIMENSIONS = ("Subsidiary", "Department", "Class", "Location")


def _read_netsuite(rows: list[Row], accounts: dict[str, Account], source: str) -> tuple[list[GLEntry], list[str]]:
    h, cols = _find_header(rows, NETSUITE)
    c_date, c_acct = _col(cols, "date"), _col(cols, "account")
    c_debit, c_credit = _col(cols, "debit"), _col(cols, "credit")
    c_type = _col(cols, "type", "transaction type")
    c_num = _col(cols, "document number", "document #", "doc number", "number")
    c_name = _col(cols, "name", "entity")
    c_memo = _col(cols, "memo", "memo (main)", "description")
    if c_date is None or c_acct is None or c_credit is None:
        raise ValueError(f"{source}: NetSuite header lacks Date/Account/Credit columns: {list(cols)}")
    dim_cols = [(d, _col(cols, d.casefold())) for d in _NETSUITE_DIMENSIONS]

    resolver = _AccountResolver(accounts)
    skips = _SkipLog()
    entries: list[GLEntry] = []
    for idx in range(h + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(c) for c in row):
            continue
        when = parse_date(_cell(row, c_date))
        if when is None:
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
        number, name, _ = resolver.resolve(*split_account_label(label))
        dims = {d: clean_text(_cell(row, c)) for d, c in dim_cols if c is not None and clean_text(_cell(row, c))}
        entries.append(
            _entry(
                rowno, when, number, name, (debit or Decimal(0)) - (credit or Decimal(0)), source,
                txn_type=_cell(row, c_type), doc_number=_cell(row, c_num),
                counterparty=_cell(row, c_name), memo=_cell(row, c_memo), dimensions=dims,
            )
        )
    return entries, skips.notes(source) + resolver.notes(source)


_XERO_NON_TXN = re.compile(r"^(total\b|opening balance|closing balance|net movement)", re.I)


def _read_xero(rows: list[Row], accounts: dict[str, Account], source: str) -> tuple[list[GLEntry], list[str]]:
    h, cols = _find_header(rows, XERO)
    c_date = _col(cols, "date")
    c_source = _col(cols, "source")
    c_desc = _col(cols, "description")
    c_ref = _col(cols, "reference")
    c_debit, c_credit = _col(cols, "debit"), _col(cols, "credit")
    c_code, c_acct = _col(cols, "account code", "code"), _col(cols, "account")

    resolver = _AccountResolver(accounts)
    skips = _SkipLog()
    entries: list[GLEntry] = []
    section = ""  # grouped layouts put the account in a heading row instead of a column
    for idx in range(h + 1, len(rows)):
        row, rowno = rows[idx], idx + 1
        if all(is_blank(c) for c in row):
            continue
        when = parse_date(_cell(row, c_date), dayfirst=True)
        if when is None:
            first = next((clean_text(c) for c in row if not is_blank(c)), "")
            if _XERO_NON_TXN.match(first):
                skips.add("total/balance rows", rowno)
            elif first and all(is_blank(_cell(row, c)) for c in (c_debit, c_credit)):
                section = first
            else:
                skips.add("rows without a transaction date", rowno)
            continue
        code, acct_name = clean_text(_cell(row, c_code)), clean_text(_cell(row, c_acct))
        if code:
            number, name = split_account_label(code)
            number, name = (number, acct_name or name) if number else (code, acct_name)
        elif acct_name or section:
            number, name = split_account_label(acct_name or section)
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
        number, name, _ = resolver.resolve(number, name)
        description = clean_text(_cell(row, c_desc))
        contact, sep, _rest = description.partition(" - ")
        entries.append(
            _entry(
                rowno, when, number, name, (debit or Decimal(0)) - (credit or Decimal(0)), source,
                txn_type=_cell(row, c_source), doc_number=_cell(row, c_ref),
                counterparty=contact if sep else "", memo=description,
            )
        )
    return entries, skips.notes(source) + resolver.notes(source)


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
    rows = load_table_rows(path, XERO_SHEET if fmt == XERO else None)
    entries, notes = reader(rows, accounts, source)
    if entries:
        rows_used = f"rows {entries[0].source_row}-{entries[-1].source_row}"
        span = f"{min(e.date for e in entries)} to {max(e.date for e in entries)}"
        head = f"GL {source} ({fmt}): {len(entries)} entries read from {rows_used}, dated {span}"
    else:
        head = f"GL {source} ({fmt}): no entries read"
    return entries, [head, *notes]
