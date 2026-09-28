"""GL and chart-of-accounts writers for the three SPEC §3.3 export formats.

Each GL writer returns {row key: source_row}, where source_row is the 1-based
row a spreadsheet app shows (the physical CSV line, or the worksheet row).
The answer key cites GL rows by that number.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from qoe.money import ZERO
from qoe.periods import month_end

from .accounts import AccountInfo
from .ledger import MONTH_ABBR, MONTH_NAME, Txn, sub_rng
from .spec import DealSpec
from .workbooks import save_workbook

GL_PATHS = {
    "qbo_gl_csv": "gl/general_ledger.csv",
    "netsuite_csv": "gl/general_ledger.csv",
    "xero_xlsx": "gl/general_ledger.xlsx",
}

TXN_TYPE_LABELS: dict[str, dict[str, str]] = {
    "qbo_gl_csv": {
        "invoice": "Invoice", "sales_receipt": "Sales Receipt", "credit_memo": "Credit Memo",
        "bill": "Bill", "vendor_credit": "Vendor Credit", "expense": "Expense", "check": "Check",
        "deposit": "Deposit", "journal": "Journal Entry", "payroll": "Journal Entry",
    },
    "netsuite_csv": {
        "invoice": "Invoice", "sales_receipt": "Cash Sale", "credit_memo": "Credit Memo",
        "bill": "Bill", "vendor_credit": "Bill Credit", "expense": "Credit Card", "check": "Check",
        "deposit": "Deposit", "journal": "Journal", "payroll": "Journal",
    },
    "xero_xlsx": {
        "invoice": "Receivable Invoice", "sales_receipt": "Receive Money", "credit_memo": "Receivable Credit Note",
        "bill": "Payable Invoice", "vendor_credit": "Payable Credit Note", "expense": "Spend Money",
        "check": "Spend Money", "deposit": "Receive Money", "journal": "Manual Journal", "payroll": "Manual Journal",
    },
}

QBO_SPLIT_DEFAULTS = {
    "invoice": "Accounts Receivable (A/R)",
    "credit_memo": "Accounts Receivable (A/R)",
    "sales_receipt": "Undeposited Funds",
    "bill": "Accounts Payable (A/P)",
    "vendor_credit": "Accounts Payable (A/P)",
    "expense": "Business Credit Card",
    "check": "Operating Checking",
    "deposit": "Operating Checking",
    "journal": "-Split-",
    "payroll": "Payroll Clearing",
}

COA_HEADERS = {
    "qbo_gl_csv": ["Account #", "Full name", "Type", "Detail type"],
    "netsuite_csv": ["Number", "Name", "Account Type", "Description"],
    "xero_xlsx": ["*Code", "*Name", "*Type", "*Tax Code", "Description"],
}

NETSUITE_HEADER = [
    "Internal ID", "Date", "Period", "Type", "Document Number", "Account", "Name", "Memo",
    "Debit", "Credit", "Subsidiary", "Department", "Class", "Location",
]
XERO_HEADER = ["Date", "Source", "Description", "Reference", "Debit", "Credit", "Running Balance", "Account Code", "Account"]


def txn_type_label(spec: DealSpec, generic: str) -> str:
    override = spec.txn_types.get(generic, {}).get(spec.gl_format)
    if override:
        return override
    return TXN_TYPE_LABELS[spec.gl_format].get(generic, generic)


def natural_amount(t: Txn, acct: AccountInfo) -> Decimal:
    """SPEC §3.3 natural sign: income shown credit-positive, everything else debit-positive."""
    return -t.amount if acct.credit_natural else t.amount


def fmt_amount(value: Decimal, dollar: bool = False) -> str:
    text = format(abs(value), ",.2f")
    if dollar:
        text = "$" + text
    return ("-" + text) if value < 0 else text


def _range_text_long(spec: DealSpec) -> str:
    y0, m0 = (int(x) for x in spec.data_start.split("-"))
    y1, m1 = (int(x) for x in spec.data_end.split("-"))
    return f"{MONTH_NAME[m0 - 1]} 1, {y0} - {MONTH_NAME[m1 - 1]} {month_end(spec.data_end).day}, {y1}"


def _csv_bytes(rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def _ordered(txns: list[Txn], accounts: dict[str, AccountInfo]) -> dict[str, list[Txn]]:
    by_acct: dict[str, list[Txn]] = {}
    for number in accounts:  # chart-of-accounts order
        rows = sorted((t for t in txns if t.account == number), key=lambda t: (t.date, t.seq))
        if rows:
            by_acct[number] = rows
    return by_acct


def write_qbo_gl(path: Path, spec: DealSpec, accounts: dict[str, AccountInfo], txns: list[Txn]) -> dict[str, int]:
    rows: list[list[str]] = [
        [spec.company.name],
        ["General Ledger"],
        [_range_text_long(spec)],
        [],
        ["", "Date", "Transaction Type", "Num", "Name", "Memo/Description", "Split", "Amount", "Balance"],
    ]
    key_rows: dict[str, int] = {}
    blank8 = [""] * 8
    for number, acct_txns in _ordered(txns, accounts).items():
        acct = accounts[number]
        rows.append([acct.label, *blank8])
        balance = ZERO
        for t in acct_txns:
            amount = natural_amount(t, acct)
            balance += amount
            split = t.split or spec.split_defaults.get(t.txn_type) or QBO_SPLIT_DEFAULTS.get(t.txn_type, "-Split-")
            rows.append(
                ["", t.date.strftime("%m/%d/%Y"), txn_type_label(spec, t.txn_type), t.num, t.counterparty,
                 t.memo, split, fmt_amount(amount), fmt_amount(balance)]
            )
            key_rows[t.key] = len(rows)
        rows.append([f"Total for {acct.label}", *[""] * 6, fmt_amount(balance, dollar=True), ""])
    rows.append(["TOTAL", *blank8])
    path.write_bytes(_csv_bytes(rows))
    return key_rows


def write_netsuite_gl(path: Path, spec: DealSpec, accounts: dict[str, AccountInfo], txns: list[Txn]) -> dict[str, int]:
    rows: list[list[str]] = [NETSUITE_HEADER]
    key_rows: dict[str, int] = {}
    rng = sub_rng(spec.seed, "netsuite-internal-id")
    internal_id = spec.netsuite_internal_id_start
    for t in sorted(txns, key=lambda t: (t.date, t.seq)):
        # Saved searches skip ids used by lines on other accounts, so ids are increasing but gapped.
        internal_id += rng.randint(1, 9)
        dims = {**spec.default_dimensions, **t.dimensions}
        debit = f"{t.amount:.2f}" if t.amount > 0 else ""
        credit = f"{-t.amount:.2f}" if t.amount < 0 else ""
        rows.append(
            [str(internal_id), f"{t.date.month}/{t.date.day}/{t.date.year}",
             f"{MONTH_ABBR[t.date.month - 1]} {t.date.year}", txn_type_label(spec, t.txn_type), t.num,
             accounts[t.account].label, t.counterparty, t.memo, debit, credit,
             dims.get("Subsidiary", ""), dims.get("Department", ""), dims.get("Class", ""), dims.get("Location", "")]
        )
        key_rows[t.key] = len(rows)
    path.write_bytes(_csv_bytes(rows))
    return key_rows


def xero_description(t: Txn) -> str:
    if t.counterparty:
        return f"{t.counterparty} - {t.memo}"
    # With no contact, a ' - ' in the text would be read as a contact separator.
    return t.memo.replace(" - ", " – ")


def write_xero_gl(path: Path, spec: DealSpec, accounts: dict[str, AccountInfo], txns: list[Txn]) -> dict[str, int]:
    wb = Workbook()
    ws = wb.active
    ws.title = "Account Transactions"
    y0, m0 = (int(x) for x in spec.data_start.split("-"))
    y1, m1 = (int(x) for x in spec.data_end.split("-"))
    ws.append(["Account Transactions"])
    ws.append([spec.company.name])
    ws.append([f"For the period 1 {MONTH_NAME[m0 - 1]} {y0} to {month_end(spec.data_end).day} {MONTH_NAME[m1 - 1]} {y1}"])
    ws.append([])
    ws.append(XERO_HEADER)
    for cell in ws[1] + ws[5]:
        cell.font = Font(bold=True)
    key_rows: dict[str, int] = {}
    for number, acct_txns in _ordered(txns, accounts).items():
        acct = accounts[number]
        balance = ZERO
        for t in acct_txns:
            balance += t.amount
            ws.append(
                [datetime(t.date.year, t.date.month, t.date.day), txn_type_label(spec, t.txn_type), xero_description(t),
                 t.num, t.amount if t.amount > 0 else None, -t.amount if t.amount < 0 else None, balance,
                 acct.number, acct.name]
            )
            row = ws.max_row
            ws.cell(row=row, column=1).number_format = "d mmm yyyy"
            for col in (5, 6, 7):
                ws.cell(row=row, column=col).number_format = "#,##0.00"
            key_rows[t.key] = row
    for col, width in zip("ABCDEFGHI", (12, 20, 60, 16, 14, 14, 16, 12, 34)):
        ws.column_dimensions[col].width = width
    save_workbook(wb, path, spec.package_date, creator="Xero")
    return key_rows


def write_gl(deal_dir: Path, spec: DealSpec, accounts: dict[str, AccountInfo], txns: list[Txn]) -> tuple[str, dict[str, int]]:
    rel = GL_PATHS[spec.gl_format]
    path = deal_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = {"qbo_gl_csv": write_qbo_gl, "netsuite_csv": write_netsuite_gl, "xero_xlsx": write_xero_gl}[spec.gl_format]
    return rel, writer(path, spec, accounts, txns)


def write_chart_of_accounts(deal_dir: Path, spec: DealSpec, accounts: dict[str, AccountInfo]) -> tuple[str, str | None]:
    """Write gl/chart_of_accounts.csv (and account_mapping_overrides.csv when the spec forces a class)."""
    headers = COA_HEADERS[spec.gl_format]
    rows: list[list[str]] = [headers]
    descriptions = {a.number: a.description for a in spec.accounts}
    for acct in accounts.values():
        extra = acct.detail_type if spec.gl_format == "qbo_gl_csv" else descriptions.get(acct.number, "")
        row = [acct.number, acct.name, acct.source_type, extra]
        if spec.gl_format == "xero_xlsx":
            row = [acct.number, acct.name, acct.source_type, "Tax Exempt (0%)", descriptions.get(acct.number, "")]
        rows.append(row)
    coa_rel = "gl/chart_of_accounts.csv"
    (deal_dir / coa_rel).parent.mkdir(parents=True, exist_ok=True)
    (deal_dir / coa_rel).write_bytes(_csv_bytes(rows))

    overrides = [
        [a.number, a.ebitda_class, a.override_basis or "deal spec override"]
        for a in spec.accounts
        if a.ebitda_class and a.ebitda_class != accounts[a.number].rule_class.value
    ]
    if not overrides:
        return coa_rel, None
    ov_rel = "gl/account_mapping_overrides.csv"
    (deal_dir / ov_rel).write_bytes(_csv_bytes([["account", "ebitda_class", "basis"], *overrides]))
    return coa_rel, ov_rel

