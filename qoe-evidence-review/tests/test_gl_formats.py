"""Tests for qoe.gl_formats: GL readers (QBO / NetSuite / Xero), detection, chart of accounts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

from qoe.gl_formats import (
    FALLBACK_BASIS,
    NETSUITE,
    QBO,
    XERO,
    classify_account,
    detect_format,
    is_credit_natural,
    parse_date,
    parse_money,
    parse_month,
    read_chart_of_accounts,
    read_gl,
    split_account_label,
)
from qoe.money import D
from qoe.schemas import Account, EbitdaClass

# Physical line numbers matter: GL-R<n> must be the row a spreadsheet shows.
QBO_CSV = "\n".join(
    [
        "Test Mechanical Co (SYNTHETIC),,,,,,,,",  # 1
        "General Ledger,,,,,,,,",  # 2
        '"January 1, 2024 - February 29, 2024",,,,,,,,',  # 3
        "",  # 4
        ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 5
        "4000 Service Revenue - Commercial,,,,,,,,",  # 6
        ',01/03/2024,Invoice,10231,Bayshore Medical Plaza,HVAC service - Jan,Accounts Receivable (A/R),"4,250.00","4,250.00"',  # 7
        ',02/05/2024,Credit Memo,CM-7,Bayshore Medical Plaza,Credit - rework,Accounts Receivable (A/R),"$(250.00)","4,000.00"',  # 8
        'Total for 4000 Service Revenue - Commercial,,,,,,,"$4,000.00",',  # 9
        "4900 Sales Discounts,,,,,,,,",  # 10
        ",01/31/2024,Invoice,10240,  Gulf   Retail  ,Early-pay discount,Accounts Receivable (A/R),-120.00,-120.00",  # 11
        "Total for 4900 Sales Discounts,,,,,,,-120.00,",  # 12
        "6400 Legal & Professional Fees,,,,,,,,",  # 13
        ',02/14/2024,Bill,25-0212,Hollis & Crane LLP,Matter 2291 - Feb,Accounts Payable (A/P),"14,500.00","14,500.00"',  # 14
        ',02/20/2024,Vendor Credit,VC-1,Hollis & Crane LLP,Credit,Accounts Payable (A/P),"(500.00)","14,000.00"',  # 15
        ",02/21/2024,Bill,,Hollis & Crane LLP,No amount,Accounts Payable (A/P),,",  # 16 blank amount
        'Total for 6400 Legal & Professional Fees,,,,,,,"$14,000.00",',  # 17
        "8000 Other Income,,,,,,,,",  # 18
        ',02/10/2024,Deposit,,Sunshine Mutual,Insurance proceeds,Checking,"40,000.00","40,000.00"',  # 19
        'Total for 8000 Other Income,,,,,,,"40,000.00",',  # 20
        "8100 Interest Expense,,,,,,,,",  # 21
        ',01/31/2024,Journal Entry,JE-1,Gulfstream Bank,Loan interest Jan,Checking,"1,200.00","1,200.00"',  # 22
        'Total for 8100 Interest Expense,,,,,,,"1,200.00",',  # 23
        "8150 Interest Income,,,,,,,,",  # 24
        ",01/31/2024,Deposit,,Gulfstream Bank,Interest earned,Checking,15.25,15.25",  # 25
        "Total for 8150 Interest Income,,,,,,,15.25,",  # 26
        ",,,,,,,,",  # 27
        'TOTAL,,,,,,,"$58,345.25",',  # 28
        "",  # 29
        '"Accrual basis Monday, March 4, 2024 10:00 AM GMT-05:00",,,,,,,,',  # 30
    ]
)

COA_CSV = "\n".join(
    [
        "Account #,Full name,Type,Detail type",
        "4000,Service Revenue - Commercial,Income,Service/Fee Income",
        "4900,Sales Discounts,Income,Discounts/Refunds Given",
        "6400,Legal & Professional Fees,Expenses,Legal & Professional Fees",
        "8000,Other Income,Other Income,Other Miscellaneous Income",
        "8100,Interest Expense,Other Expense,Other Miscellaneous Expense",
        "8150,Interest Income,Other Income,Interest Earned",
    ]
)

NETSUITE_CSV = "\n".join(
    [
        "Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit,Subsidiary,Department,Class,Location",
        '1001,3/5/2025,Feb 2025,Invoice,INV-1,4000 Product Revenue,Acme Corp,Widgets,,"1,000.00",Parent Co,Sales,Retail,Tampa',
        '1002,3/15/2025,Mar 2025,Bill,B-7,6100 Rent Expense,Landlord LLC,March rent,"5,000.00",,Parent Co,G&A,,Tampa',
        "1003,12/31/2025,Dec 2025,Journal,JE-9,6000 Operating Expenses : 8100 Interest Expense,Gulfstream Bank,Interest,250.5,,Parent Co,,,",
        ',,,,,,,Total,"6,250.50","1,000.00",,,,',
    ]
)


def _write(path: Path, text: str, bom: bool = False) -> Path:
    path.write_bytes(("\ufeff" if bom else "").encode("utf-8") + text.encode("utf-8"))
    return path


def _xero_workbook(path: Path, sheet_title: str = "Account Transactions") -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(["Account Transactions"])  # 1
    ws.append(["Test Co (SYNTHETIC)"])  # 2
    ws.append(["For the period 1 January 2025 to 31 March 2025"])  # 3
    ws.append([])  # 4
    ws.append(["Date", "Source", "Description", "Reference", "Debit", "Credit", "Running Balance", "Account Code", "Account"])  # 5
    ws.append([datetime(2025, 1, 15), "Receivable Invoice", "Acme Corp - Consulting January", "INV-0001", None, 1500, -1500, "200", "Sales"])  # 6
    ws.append(["15 Mar 2025", "Spend Money", "Office rent March", "RENT-3", 2000, None, 2000, "400", "Rent"])  # 7
    ws.append([datetime(2025, 3, 31), "Payable Invoice", "Hollis & Crane LLP - Matter 2291 - March", "B-1", 3000.5, None, 5000.5, 404, "Legal"])  # 8
    ws.append([None, None, "Total", None, 5000.5, 1500, None, None, None])  # 9
    wb.save(path)
    return path


@pytest.fixture()
def coa(tmp_path: Path) -> dict[str, Account]:
    accounts, _ = read_chart_of_accounts(_write(tmp_path / "coa.csv", COA_CSV))
    return {a.number: a for a in accounts}


# ---------------------------------------------------------------------------
# Cell parsing
# ---------------------------------------------------------------------------


def test_parse_money_handles_real_world_formats():
    assert parse_money("$(1,234.50)") == D("-1234.50")
    assert parse_money(" 4,250.00 ") == D("4250.00")
    assert parse_money("-$12.00") == D("-12.00")
    assert parse_money("\u22125.00") == D("-5.00")
    assert parse_money(3000.5) == D("3000.5")
    assert parse_money("") is None and parse_money(None) is None
    with pytest.raises(ValueError):
        parse_money("n/a")


def test_parse_date_and_month_variants():
    assert parse_date("01/03/2024").isoformat() == "2024-01-03"
    assert parse_date("3/5/2025").isoformat() == "2025-03-05"
    assert parse_date("15 Mar 2025").isoformat() == "2025-03-15"
    assert parse_date("03/04/2025", dayfirst=True).isoformat() == "2025-04-03"
    assert parse_date(datetime(2025, 1, 15)).isoformat() == "2025-01-15"
    assert parse_date(45292).isoformat() == "2024-01-01"  # Excel serial
    assert parse_date("Beginning Balance") is None
    assert parse_month("Jan 2024") == "2024-01"
    assert parse_month("January 2024") == "2024-01"
    assert parse_month("2024-01") == "2024-01"
    assert parse_month(" Sept 2024 ") == "2024-09"
    assert parse_month(datetime(2024, 2, 1)) == "2024-02"
    assert parse_month("Total") is None and parse_month(2024) is None


def test_split_account_label():
    assert split_account_label("4000 Service Revenue - Commercial") == ("4000", "Service Revenue - Commercial")
    assert split_account_label("4900 · Sales Discounts") == ("4900", "Sales Discounts")
    assert split_account_label("6000 Operating Expenses : 8100 Interest Expense") == ("8100", "Interest Expense")
    assert split_account_label("6600 Travel: Meals") == ("6600", "Travel: Meals")
    assert split_account_label("Uncategorized Expense") == ("", "Uncategorized Expense")
    assert split_account_label("200") == ("200", "")


# ---------------------------------------------------------------------------
# QBO
# ---------------------------------------------------------------------------


def test_qbo_rows_signs_and_fields(tmp_path: Path, coa: dict[str, Account]):
    path = _write(tmp_path / "general_ledger.csv", QBO_CSV, bom=True)
    assert detect_format(path) == QBO
    entries, notes = read_gl(path, QBO, coa, source_label="gl/general_ledger.csv")
    by_row = {e.source_row: e for e in entries}
    assert sorted(by_row) == [7, 8, 11, 14, 15, 19, 22, 25]

    lines = QBO_CSV.split("\n")
    for e in entries:
        assert e.entry_id == f"GL-R{e.source_row}"
        assert e.source_file == "gl/general_ledger.csv"
        assert e.memo in lines[e.source_row - 1]  # row number is the physical line

    first = by_row[7]
    assert (first.date, first.period, first.account, first.account_name) == (
        "2024-01-03", "2024-01", "4000", "Service Revenue - Commercial"
    )
    assert (first.txn_type, first.doc_number, first.counterparty) == ("Invoice", "10231", "Bayshore Medical Plaza")
    assert first.dimensions == {}

    # Revenue: natural credit-positive -> debit-positive negative.
    assert first.amount == "-4250.00"
    # A credit memo reduces revenue: natural "$(250.00)" -> debit +250.
    assert by_row[8].amount == "250.00"
    # Contra-revenue under Income shown negative -> debit-positive positive.
    assert by_row[11].amount == "120.00"
    assert by_row[11].counterparty == "Gulf Retail"
    # Expense stays as shown; a vendor credit in parentheses is a credit.
    assert by_row[14].amount == "14500.00"
    assert by_row[15].amount == "-500.00"
    # Other income is credit-natural.
    assert by_row[19].amount == "-40000.00"
    # Interest expense (INTEREST class, expense type) stays debit-positive.
    assert coa["8100"].ebitda_class is EbitdaClass.INTEREST
    assert by_row[22].amount == "1200.00"
    # Interest income: INTEREST class but an income source type -> negated.
    assert coa["8150"].ebitda_class is EbitdaClass.INTEREST
    assert by_row[25].amount == "-15.25"

    joined = "\n".join(notes)
    assert "8 entries" in joined
    assert "total/subtotal rows" in joined
    assert "blank amount (rows 16)" in joined


def test_qbo_sign_follows_source_type_even_with_override(tmp_path: Path):
    overrides = _write(tmp_path / "overrides.csv", "account,ebitda_class,basis\n8000,OPEX,Reclass per controller\n")
    accounts, _ = read_chart_of_accounts(_write(tmp_path / "coa.csv", COA_CSV), overrides)
    by_number = {a.number: a for a in accounts}
    assert by_number["8000"].ebitda_class is EbitdaClass.OPEX
    entries, _ = read_gl(_write(tmp_path / "gl.csv", QBO_CSV), QBO, by_number)
    # QBO shows the account's natural balance by its own type (Other Income), whatever class diligence assigns.
    assert next(e for e in entries if e.source_row == 19).amount == "-40000.00"


def test_qbo_expense_type_overridden_to_other_income_is_credit_natural(tmp_path: Path):
    overrides = _write(tmp_path / "overrides.csv", "account,ebitda_class,basis\n6400,OTHER_INCOME,Rebate account\n")
    accounts, _ = read_chart_of_accounts(_write(tmp_path / "coa.csv", COA_CSV), overrides)
    entries, _ = read_gl(_write(tmp_path / "gl.csv", QBO_CSV), QBO, {a.number: a for a in accounts})
    # SPEC §3.3 converts by EBITDA class: OTHER_INCOME negates.
    assert next(e for e in entries if e.source_row == 14).amount == "-14500.00"


def test_qbo_liability_accounts_are_credit_natural(tmp_path: Path):
    text = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",
            "2000 Accounts Payable (A/P),,,,,,,,",
            ",01/05/2024,Bill,B-1,Vendor,Bill,Rent,500.00,500.00",
            "1000 Operating Checking,,,,,,,,",
            ",01/06/2024,Deposit,,Customer,Deposit,A/R,700.00,700.00",
        ]
    )
    accounts = {
        "2000": Account(number="2000", name="Accounts Payable (A/P)", source_type="Accounts payable (A/P)", ebitda_class=EbitdaClass.BALANCE_SHEET),
        "1000": Account(number="1000", name="Operating Checking", source_type="Bank", ebitda_class=EbitdaClass.BALANCE_SHEET),
    }
    entries, _ = read_gl(_write(tmp_path / "gl.csv", text), QBO, accounts)
    assert [(e.account, e.amount) for e in entries] == [("2000", "-500.00"), ("1000", "700.00")]


def test_qbo_unknown_account_is_noted(tmp_path: Path, coa: dict[str, Account]):
    del coa["6400"]
    entries, notes = read_gl(_write(tmp_path / "gl.csv", QBO_CSV), QBO, coa)
    legal = [e for e in entries if e.account == "6400"]
    assert [e.amount for e in legal] == ["14500.00", "-500.00"]
    assert legal[0].account_name == "Legal & Professional Fees"
    assert any("not in the chart of accounts" in n and "6400" in n for n in notes)


def test_qbo_nested_sections_and_headers_without_numbers(tmp_path: Path):
    text = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 1
            "6000 Payroll Expenses,,,,,,,,",  # 2
            "6010 Officer Compensation,,,,,,,,",  # 3
            ",01/15/2024,Payroll Check,,R. Owner,Officer payroll,Checking,27500.00,",  # 4
            "Total for 6010 Officer Compensation,,,,,,,27500.00,",  # 5
            ",01/31/2024,Journal Entry,,,Payroll accrual,Accrued,100.00,",  # 6 posted to the parent
            "Total for 6000 Payroll Expenses,,,,,,,27600.00,",  # 7
            "Uncategorized Expense,,,,,,,,",  # 8
            ",01/20/2024,Expense,,Vendor,Misc,Checking,42.00,",  # 9
        ]
    )
    accounts = {
        "6000": Account(number="6000", name="Payroll Expenses", source_type="Expenses", ebitda_class=EbitdaClass.OPEX),
        "6010": Account(number="6010", name="Officer Compensation", source_type="Expenses", ebitda_class=EbitdaClass.OPEX),
        "6999": Account(number="6999", name="Uncategorized Expense", source_type="Expenses", ebitda_class=EbitdaClass.OPEX),
    }
    entries, _ = read_gl(_write(tmp_path / "gl.csv", text), QBO, accounts)
    assert [(e.source_row, e.account) for e in entries] == [(4, "6010"), (6, "6000"), (9, "6999")]


# ---------------------------------------------------------------------------
# NetSuite
# ---------------------------------------------------------------------------


def test_netsuite_debit_credit_dates_and_dimensions(tmp_path: Path):
    path = _write(tmp_path / "gl.csv", NETSUITE_CSV, bom=True)
    assert detect_format(path) == NETSUITE
    entries, notes = read_gl(path, "auto", {})
    assert [e.source_row for e in entries] == [2, 3, 4]
    revenue, rent, interest = entries
    assert revenue.amount == "-1000.00"
    # Period column says Feb 2025 but the month comes from Date.
    assert (revenue.date, revenue.period) == ("2025-03-05", "2025-03")
    assert (revenue.account, revenue.account_name, revenue.counterparty, revenue.doc_number, revenue.txn_type) == (
        "4000", "Product Revenue", "Acme Corp", "INV-1", "Invoice"
    )
    assert revenue.dimensions == {"Subsidiary": "Parent Co", "Department": "Sales", "Class": "Retail", "Location": "Tampa"}
    assert rent.amount == "5000.00" and "Class" not in rent.dimensions
    assert (interest.account, interest.amount, interest.date) == ("8100", "250.50", "2025-12-31")
    assert any("rows 5" in n for n in notes)


# ---------------------------------------------------------------------------
# Xero
# ---------------------------------------------------------------------------


def test_xero_rows_dates_and_counterparty(tmp_path: Path):
    path = _xero_workbook(tmp_path / "gl.xlsx")
    assert detect_format(path) == XERO
    entries, _ = read_gl(path, XERO, {})
    assert [e.entry_id for e in entries] == ["GL-R6", "GL-R7", "GL-R8"]
    sales, rent, legal = entries
    assert (sales.date, sales.amount, sales.counterparty, sales.memo) == (
        "2025-01-15", "-1500.00", "Acme Corp", "Acme Corp - Consulting January"
    )
    assert (sales.txn_type, sales.doc_number, sales.account, sales.account_name) == ("Receivable Invoice", "INV-0001", "200", "Sales")
    assert (rent.date, rent.amount, rent.counterparty) == ("2025-03-15", "2000.00", "")
    # Split on the first " - " only; numeric account codes become text.
    assert (legal.counterparty, legal.amount, legal.account) == ("Hollis & Crane LLP", "3000.50", "404")


def test_xero_detected_by_header_when_sheet_renamed(tmp_path: Path):
    path = _xero_workbook(tmp_path / "gl.xlsx", sheet_title="Sheet1")
    assert detect_format(path) == XERO


def test_detect_format_rejects_unknown_headers(tmp_path: Path):
    path = _write(tmp_path / "gl.csv", "Posted,Acct,Value\n2024-01-01,4000,10\n")
    with pytest.raises(ValueError) as err:
        detect_format(path)
    assert "Posted" in str(err.value) and "Acct" in str(err.value)


# ---------------------------------------------------------------------------
# Chart of accounts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, source_type, expected",
    [
        ("Service Revenue", "Income", EbitdaClass.REVENUE),
        ("Sales", "REVENUE", EbitdaClass.REVENUE),
        ("Other Revenue", "OTHERINCOME", EbitdaClass.OTHER_INCOME),
        ("Gain/Loss on Sale of Assets", "Other Income", EbitdaClass.OTHER_INCOME),
        ("Materials", "Cost of Goods Sold", EbitdaClass.COGS),
        ("Purchases", "DIRECTCOSTS", EbitdaClass.COGS),
        ("Office", "OVERHEADS", EbitdaClass.OPEX),
        ("Rent & Occupancy", "Expenses", EbitdaClass.OPEX),
        ("Other Expense", "Other Expense", EbitdaClass.OTHER_EXPENSE),
        ("Depreciation", "DEPRECIATN", EbitdaClass.DEPRECIATION),
        ("Interest Expense", "Other Expense", EbitdaClass.INTEREST),
        ("Interest Income", "Other Income", EbitdaClass.INTEREST),
        ("Loan Interest", "Expense", EbitdaClass.INTEREST),
        ("Depreciation Expense", "Expenses", EbitdaClass.DEPRECIATION),
        ("Amortization Expense", "Expenses", EbitdaClass.AMORTIZATION),
        ("Amortization of Loan Costs", "Other Expense", EbitdaClass.INTEREST),
        ("Income Taxes - State", "Other Expense", EbitdaClass.TAXES),
        ("Federal Income Tax Expense", "Other Expense", EbitdaClass.TAXES),
        ("Payroll Taxes & Benefits", "Expenses", EbitdaClass.OPEX),
        ("Franchise Tax", "Expense", EbitdaClass.OPEX),
        ("Sales Tax Penalties", "Expenses", EbitdaClass.OPEX),
        ("Bank Charges & Interest", "Expenses", EbitdaClass.OPEX),
        ("Office", "Overhead", EbitdaClass.OPEX),
        ("Checking", "Bank", EbitdaClass.BALANCE_SHEET),
        ("Accumulated Depreciation", "Fixed Assets", EbitdaClass.BALANCE_SHEET),
        ("Deferred Revenue", "Deferred Revenue", EbitdaClass.BALANCE_SHEET),
        ("Accrued interest", "Other Current Liabilities", EbitdaClass.BALANCE_SHEET),
        ("Trade debtors", "CURRENT", EbitdaClass.BALANCE_SHEET),
        ("Accounts Receivable (A/R)", "Accounts receivable (A/R)", EbitdaClass.BALANCE_SHEET),
    ],
)
def test_classification_rules(name: str, source_type: str, expected: EbitdaClass):
    cls, basis = classify_account(name, source_type)
    assert cls is expected, basis
    assert not basis.startswith(FALLBACK_BASIS)


@pytest.mark.parametrize(
    "source_type, expected, credit_natural",
    [
        # QBO and NetSuite UI labels, including the plural and "Cost of Sales" forms real exports use.
        ("Expenses", EbitdaClass.OPEX, False),
        ("Expense", EbitdaClass.OPEX, False),
        ("Other Expenses", EbitdaClass.OTHER_EXPENSE, False),
        ("Other Expense", EbitdaClass.OTHER_EXPENSE, False),
        ("Cost of Sales", EbitdaClass.COGS, False),
        ("Cost of sales", EbitdaClass.COGS, False),
        ("Cost of Goods Sold", EbitdaClass.COGS, False),
        ("Other Income", EbitdaClass.OTHER_INCOME, True),
        ("  EXPENSES ", EbitdaClass.OPEX, False),
        # NetSuite internal type ids from saved-search exports.
        ("OthExpense", EbitdaClass.OTHER_EXPENSE, False),
        ("OthIncome", EbitdaClass.OTHER_INCOME, True),
        ("COGS", EbitdaClass.COGS, False),
        ("AcctRec", EbitdaClass.BALANCE_SHEET, False),
        ("AcctPay", EbitdaClass.BALANCE_SHEET, True),
        ("CredCard", EbitdaClass.BALANCE_SHEET, True),
        ("DeferRevenue", EbitdaClass.BALANCE_SHEET, True),
        ("DeferExpense", EbitdaClass.BALANCE_SHEET, False),
        ("OthCurrLiab", EbitdaClass.BALANCE_SHEET, True),
        ("Stat", EbitdaClass.BALANCE_SHEET, False),
    ],
)
def test_real_export_type_labels(source_type: str, expected: EbitdaClass, credit_natural: bool):
    cls, basis = classify_account("Some Account", source_type)
    assert cls is expected, basis
    assert basis.startswith("type rule:")
    account = Account(number="1", name="Some Account", source_type=source_type, ebitda_class=cls, mapping_basis=basis)
    assert is_credit_natural(account) is credit_natural


def test_coa_with_plural_and_cost_of_sales_types_reads_a_qbo_gl(tmp_path: Path):
    coa = _write(
        tmp_path / "coa.csv",
        "\n".join(
            [
                "Account #,Full name,Type,Detail type",
                "4000,Service Revenue,Income,Service/Fee Income",
                "5000,Materials & Equipment,Cost of Sales,Supplies & Materials - COS",
                "6400,Legal & Professional Fees,Expenses,Legal & Professional Fees",
                "8000,Other Income,Other Income,Other Miscellaneous Income",
                "8200,Other Expense,Other Expenses,Other Miscellaneous Expense",
            ]
        ),
    )
    accounts, notes = read_chart_of_accounts(coa)
    by_number = {a.number: a for a in accounts}
    assert {n: a.ebitda_class for n, a in by_number.items()} == {
        "4000": EbitdaClass.REVENUE,
        "5000": EbitdaClass.COGS,
        "6400": EbitdaClass.OPEX,
        "8000": EbitdaClass.OTHER_INCOME,
        "8200": EbitdaClass.OTHER_EXPENSE,
    }
    assert by_number["5000"].mapping_basis == "type rule: Cost of Sales -> COGS"
    assert by_number["8200"].mapping_basis == "type rule: Other Expenses -> OTHER_EXPENSE"
    assert not any(a.mapping_basis.startswith(FALLBACK_BASIS) for a in accounts)
    assert "0 fallback mapping(s)" in notes[0]
    gl = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 1
            "5000 Materials & Equipment,,,,,,,,",  # 2
            ",03/04/2025,Bill,M-1,Ferguson,Copper fittings,Accounts Payable (A/P),\"1,250.00\",",  # 3
            "8000 Other Income,,,,,,,,",  # 4
            ",03/10/2025,Deposit,,Sunshine Mutual,Insurance proceeds,Checking,\"40,000.00\",",  # 5
            "8200 Other Expense,,,,,,,,",  # 6
            ",03/12/2025,Expense,,City of Tampa,Late filing penalty,Checking,75.00,",  # 7
        ]
    )
    entries, _ = read_gl(_write(tmp_path / "gl.csv", gl), QBO, by_number)
    # Natural sign: expense-type accounts stay debit-positive; income-type accounts are negated.
    assert [(e.account, e.amount) for e in entries] == [("5000", "1250.00"), ("8000", "-40000.00"), ("8200", "75.00")]


def test_unrecognized_type_falls_back_to_opex():
    cls, basis = classify_account("Clearing", "Clearing Account")
    assert cls is EbitdaClass.OPEX
    assert basis.startswith(FALLBACK_BASIS)


@pytest.mark.parametrize(
    "header",
    [
        "Account #,Full name,Type",
        "*Code,*Name,*Type",
        "ACCOUNT NUMBER, Account Name ,Account Type",
        "Code,Name,Type",
    ],
)
def test_coa_header_candidates(tmp_path: Path, header: str):
    body = "\n".join(["Chart of Accounts (SYNTHETIC),,", header, "4000,Service Revenue,Income", "8100,Interest Expense,Other Expense", ",,"])
    accounts, notes = read_chart_of_accounts(_write(tmp_path / "coa.csv", body))
    assert [(a.number, a.name, a.source_type, a.ebitda_class) for a in accounts] == [
        ("4000", "Service Revenue", "Income", EbitdaClass.REVENUE),
        ("8100", "Interest Expense", "Other Expense", EbitdaClass.INTEREST),
    ]
    assert accounts[0].mapping_basis == "type rule: Income -> REVENUE"
    assert accounts[1].mapping_basis == "name rule: interest -> INTEREST"
    assert "2 accounts" in notes[0]


def test_coa_overrides_take_precedence_and_bad_rows_are_noted(tmp_path: Path):
    coa = _write(
        tmp_path / "coa.csv",
        "Account #,Full name,Type\n6200,Insurance,Expenses\n6300,Software,Expenses\n7000,Depreciation Expense,Expenses\n",
    )
    overrides = _write(
        tmp_path / "account_mapping_overrides.csv",
        "account,ebitda_class,basis\n"
        "6200,other expense,Non-operating per CFO\n"
        "7000,OPEX,\n"
        "6300,bogus,typo\n"
        "9999,OPEX,not in COA\n",
    )
    accounts, notes = read_chart_of_accounts(coa, overrides)
    by_number = {a.number: a for a in accounts}
    assert by_number["6200"].ebitda_class is EbitdaClass.OTHER_EXPENSE
    assert by_number["6200"].mapping_basis == "override: Non-operating per CFO"
    # Overrides beat name rules.
    assert by_number["7000"].ebitda_class is EbitdaClass.OPEX
    assert by_number["7000"].mapping_basis.startswith("override")
    assert by_number["6300"].mapping_basis == "type rule: Expenses -> OPEX"
    joined = "\n".join(notes)
    assert "row 4 ignored" in joined
    assert "'9999' is not in the chart of accounts" in joined


def test_coa_combined_account_column(tmp_path: Path):
    coa = _write(tmp_path / "coa.csv", "Account,Type\n4000 Service Revenue,Income\n6400 Legal:6410 Accounting,Expenses\n")
    accounts, _ = read_chart_of_accounts(coa)
    assert [(a.number, a.name) for a in accounts] == [("4000", "Service Revenue"), ("6410", "Accounting")]


def test_coa_without_name_column_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        read_chart_of_accounts(_write(tmp_path / "coa.csv", "Foo,Bar\n1,2\n"))


# ---------------------------------------------------------------------------
# Review fixes: loading, labels, dates, sub-accounts, totals, classification
# ---------------------------------------------------------------------------


def _rewrite_sheet_xml(path: Path, edit) -> Path:
    """Rewrite the first worksheet's XML in place (simulates writers other than Excel)."""
    import zipfile

    with zipfile.ZipFile(path) as zf:
        parts = {n: zf.read(n) for n in zf.namelist()}
    name = "xl/worksheets/sheet1.xml"
    parts[name] = edit(parts[name].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(path, "w") as zf:
        for n, data in parts.items():
            zf.writestr(n, data)
    return path


def test_xlsx_stale_dimension_does_not_truncate_rows(tmp_path: Path):
    """Read-only openpyxl trusts <dimension>; a stale one must not drop GL rows silently."""
    import re

    path = _xero_workbook(tmp_path / "gl.xlsx")
    _rewrite_sheet_xml(path, lambda xml: re.sub(r'<dimension ref="[^"]+"', '<dimension ref="A1"', xml))
    assert detect_format(path) == XERO
    entries, notes = read_gl(path, XERO, {})
    assert [e.entry_id for e in entries] == ["GL-R6", "GL-R7", "GL-R8"]
    assert "3 entries read from rows 6-8" in notes[0]


def test_uncached_formula_amounts_stop_the_run_instead_of_reading_zero(tmp_path: Path):
    from qoe.gl_formats import UncachedFormulaError, read_table

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Ref", "Adjustment", "FY2024"])
    ws.append(["M-01", "Legal fees", "=5*4"])  # openpyxl stores the formula without a value
    ws.append(["M-02", "Label", '=IF(1=1,"","x")'])
    path = tmp_path / "sched.xlsx"
    wb.save(path)
    # Excel stores a formula's cached result; an empty-string result is marked t="str".
    _rewrite_sheet_xml(path, lambda xml: xml.replace('<c r="C3"><f>', '<c r="C3" t="str"><f>'))
    table = read_table(path)
    assert "C2 =5*4" in table.notes[0] and "C3" not in table.notes[0]
    assert table.rows[2][2] is None  # cached empty string reads as blank
    with pytest.raises(UncachedFormulaError, match=r"cell C2 holds a formula \(=5\*4\)"):
        parse_money(table.rows[1][2])
    assert str(table.rows[1][2]) == ""


def test_excel_saved_formulas_with_cached_values_are_read(tmp_path: Path):
    from qoe.gl_formats import read_table

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["a", 2, "=B1*2"])
    path = tmp_path / "cached.xlsx"
    wb.save(path)
    _rewrite_sheet_xml(path, lambda xml: xml.replace("<f>B1*2</f><v />", "<f>B1*2</f><v>4</v>").replace("<f>B1*2</f><v></v>", "<f>B1*2</f><v>4</v>"))
    table = read_table(path)
    assert table.rows[0] == ["a", 2, 4] and table.notes == []


def test_utf16_and_mixed_encoding_csv_exports(tmp_path: Path):
    from qoe.gl_formats import read_table

    tsv = NETSUITE_CSV.replace(",", "\t").replace('"1\t000.00"', "1000.00").replace('"5\t000.00"', "5000.00").replace('"6\t250.50"', "6250.50")
    utf16 = tmp_path / "gl_utf16.csv"
    utf16.write_bytes(tsv.encode("utf-16"))  # Excel "Unicode Text": UTF-16 with BOM, tab-delimited
    assert detect_format(utf16) == NETSUITE
    entries, _ = read_gl(utf16, NETSUITE, {})
    assert [e.amount for e in entries] == ["-1000.00", "5000.00", "250.50"]

    mixed = tmp_path / "gl_mixed.csv"
    body = NETSUITE_CSV.replace("Acme Corp", "Café Corp").encode("utf-8").replace("Café".encode("utf-8"), b"Caf\xe9")
    mixed.write_bytes(b"\xef\xbb\xbf" + body.replace("Landlord LLC".encode(), "Landlord – LLC".encode("utf-8")))
    assert detect_format(mixed) == NETSUITE  # header not mangled by a whole-file cp1252 fallback
    table = read_table(mixed)
    assert table.rows[0][0] == "Internal ID"
    assert table.rows[1][6] == "Café Corp" and table.rows[2][6] == "Landlord – LLC"
    assert "1 line(s) are not valid UTF-8" in table.notes[0] and "lines 2" in table.notes[0]


def test_split_account_label_keeps_sub_account_numbers():
    assert split_account_label("4000-10 Service Revenue - Commercial") == ("4000-10", "Service Revenue - Commercial")
    assert split_account_label("4-1000 Sales") == ("4-1000", "Sales")
    assert split_account_label("6000.10 Salaries - Office") == ("6000.10", "Salaries - Office")
    assert split_account_label("4000 - Service Revenue") == ("4000", "Service Revenue")
    assert split_account_label("4000-Service Revenue") == ("4000", "Service Revenue")
    assert split_account_label("4000- Service Revenue") == ("4000", "Service Revenue")
    assert split_account_label("4000-10") == ("4000-10", "")


def test_netsuite_hyphenated_sub_accounts_do_not_collapse_into_the_parent(tmp_path: Path):
    coa = _write(tmp_path / "coa.csv", "Number,Name,Type\n4000,Revenue,Income\n4000-10,Revenue - Commercial,Income\n4000-20,Revenue - Residential,Income\n")
    accounts, _ = read_chart_of_accounts(coa)
    by_number = {a.number: a for a in accounts}
    assert set(by_number) == {"4000", "4000-10", "4000-20"}
    gl = _write(
        tmp_path / "gl.csv",
        "\n".join(
            [
                "Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit",
                "1,1/3/2024,Jan 2024,Invoice,I1,4000-10 Revenue - Commercial,Acme,x,,1000",
                "2,1/4/2024,Jan 2024,Invoice,I2,4000-20 Revenue - Residential,Bob,x,,500",
                "3,1/5/2024,Jan 2024,Invoice,I3,4000 Revenue,Carl,x,,70",
            ]
        ),
    )
    entries, notes = read_gl(gl, NETSUITE, by_number)
    assert [(e.account, e.amount) for e in entries] == [("4000-10", "-1000.00"), ("4000-20", "-500.00"), ("4000", "-70.00")]
    assert not any("not in the chart of accounts" in n for n in notes)


def test_unnumbered_sub_accounts_keep_their_full_path(tmp_path: Path):
    """QBO without account numbers: "Other" under an income parent and under an expense parent
    are different accounts; the expense must not be read as a revenue credit."""
    coa = _write(
        tmp_path / "coa.csv",
        "\n".join(
            [
                "Full name,Type,Detail type",
                "Services,Income,Service/Fee Income",
                "Services:Other,Income,Service/Fee Income",
                "Office Expenses,Expenses,Office/General Administrative Expenses",
                "Office Expenses:Other,Expenses,Office/General Administrative Expenses",
                "Uncategorized Expense,Expenses,Other Miscellaneous Service Cost",
            ]
        ),
    )
    accounts, notes = read_chart_of_accounts(coa)
    by_id = {a.number: a for a in accounts}
    assert by_id["Services:Other"].ebitda_class is EbitdaClass.REVENUE
    assert by_id["Office Expenses:Other"].ebitda_class is EbitdaClass.OPEX
    assert by_id["Office Expenses:Other"].name == "Office Expenses:Other"
    joined = "\n".join(notes)
    assert "full account name is used as the id" in joined
    assert "'other': Services:Other, Office Expenses:Other" in joined
    gl = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 1
            "Services,,,,,,,,",  # 2
            "Other,,,,,,,,",  # 3
            ",01/10/2024,Invoice,1001,Acme,Misc service,A/R,400.00,",  # 4
            "Total for Other,,,,,,,400.00,",  # 5
            "Total for Services,,,,,,,400.00,",  # 6
            "Office Expenses,,,,,,,,",  # 7
            "Other,,,,,,,,",  # 8
            ",01/15/2024,Expense,,Staples,Toner,Checking,250.00,",  # 9
            "Total for Other,,,,,,,250.00,",  # 10
            "Total for Office Expenses,,,,,,,250.00,",  # 11
            "Uncategorized Expense,,,,,,,,",  # 12
            ",01/20/2024,Expense,,Amazon,Misc,Checking,42.00,",  # 13
            "Total for Uncategorized Expense,,,,,,,42.00,",  # 14
            "Other,,,,,,,,",  # 15 a leaf alone, no parent: ambiguous
            ",01/21/2024,Expense,,Somebody,Misc,Checking,5.00,",  # 16
        ]
    )
    entries, gl_notes = read_gl(_write(tmp_path / "gl.csv", gl), QBO, by_id)
    assert [(e.source_row, e.account, e.amount) for e in entries] == [
        (4, "Services:Other", "-400.00"),
        (9, "Office Expenses:Other", "250.00"),
        (13, "Uncategorized Expense", "42.00"),
        (16, "Other", "5.00"),
    ]
    assert any("WARNING" in n and "'Other' could be Services:Other, Office Expenses:Other" in n for n in gl_notes)


def test_qbo_account_named_total_is_a_section_not_a_subtotal(tmp_path: Path):
    text = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 1
            "Totalflex Equipment Rental,,,,,,,,",  # 2
            ",01/21/2024,Bill,B1,Sunbelt,rental,A/P,\"1,234.00\",",  # 3
            "Total for Totalflex Equipment Rental,,,,,,,\"$1,234.00\",",  # 4
            "Total Care Janitorial,,,,,,,,",  # 5
            ",01/22/2024,Bill,B2,Total Care,cleaning,A/P,500.00,",  # 6
            "Total for Total Care Janitorial,,,,,,,$500.00,",  # 7
            "6400 Legal,,,,,,,,",  # 8  QBO Desktop style: "Total <account>"
            ",01/23/2024,Bill,B3,Hollis,fees,A/P,100.00,",  # 9
            "Total 6400 Legal,,,,,,,100.00,",  # 10
            ",01/24/2024,Bill,B4,Nobody,orphan,A/P,1.00,",  # 11 outside any section
            "TOTAL,,,,,,,\"1,835.00\",",  # 12
        ]
    )
    entries, notes = read_gl(_write(tmp_path / "gl.csv", text), QBO, {})
    assert [(e.source_row, e.account) for e in entries] == [(3, "Totalflex Equipment Rental"), (6, "Total Care Janitorial"), (9, "6400")]
    joined = "\n".join(notes)
    assert "total/subtotal rows (rows 4, 7, 10, 12)" in joined
    assert "outside any account section (rows 11)" in joined


def test_parse_date_time_suffixes_and_text_serials():
    assert parse_date("1/7/2024 0:00").isoformat() == "2024-01-07"
    assert parse_date("01/07/2024 12:00:00 AM").isoformat() == "2024-01-07"
    assert parse_date("2024-01-07T00:00:00").isoformat() == "2024-01-07"
    assert parse_date("2024-01-07 13:45").isoformat() == "2024-01-07"
    assert parse_date("45300").isoformat() == "2024-01-09"  # Excel serial written as text (45292 = 2024-01-01)
    assert parse_date("15/01/2024 0:00", dayfirst=True).isoformat() == "2024-01-15"
    assert parse_date("12345") is None


def test_detect_dayfirst_from_the_dates_themselves():
    from qoe.gl_formats import detect_dayfirst

    assert detect_dayfirst(["03/01/2024", "15/01/2024"], False, "gl") is True
    assert detect_dayfirst(["03/01/2024", "01/15/2024"], True, "gl") is False
    assert detect_dayfirst(["03/01/2024", "04/02/2024"], False, "gl") is False  # no proof: default
    with pytest.raises(ValueError, match="mixes day-first"):
        detect_dayfirst(["15/01/2024", "01/15/2024"], False, "gl")


NETSUITE_DAYFIRST = "\n".join(
    [
        "Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit",  # 1
        '1,03/01/2024,Jan 2024,Bill,B1,6400 Legal & Professional Fees,Hollis,Jan fees,"1,000.00",',  # 2  3 Jan
        '2,15/01/2024,Jan 2024,Bill,B2,6400 Legal & Professional Fees,Hollis,Jan fees,"2,000.00",',  # 3
        '3,31/01/2024 0:00,Jan 2024,Bill,B3,6400 Legal & Professional Fees,Hollis,Jan fees,"3,000.00",',  # 4
        '4,Jan 32 2024,Jan 2024,Bill,B4,6400 Legal & Professional Fees,Hollis,bad date,"4,000.00",',  # 5 unreadable
        ',,,,,,,Total,"10,000.00",',  # 6
    ]
)


def test_netsuite_day_first_export_is_read_day_first_and_undated_money_is_a_warning(tmp_path: Path):
    entries, notes = read_gl(_write(tmp_path / "gl.csv", NETSUITE_DAYFIRST), NETSUITE, {})
    assert [(e.source_row, e.date) for e in entries] == [(2, "2024-01-03"), (3, "2024-01-15"), (4, "2024-01-31")]
    joined = "\n".join(notes)
    assert "day-first" in joined
    # The unreadable row carries money: a warning with the amount, not a benign "totals" skip.
    assert "WARNING - dropped 1 row(s) that carry amounts (4000.00" in joined and "5 ('Jan 32 2024')" in joined
    assert "rows without a transaction date (e.g. totals) (rows 6)" in joined


def test_netsuite_ambiguous_dates_follow_the_period_column(tmp_path: Path):
    text = "\n".join(
        [
            "Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit",
            "1,03/01/2024,Jan 2024,Bill,B1,6400 Legal,Hollis,x,100,",
            "2,05/02/2024,Feb 2024,Bill,B2,6400 Legal,Hollis,x,100,",
            "3,07/03/2024,Mar 2024,Bill,B3,6400 Legal,Hollis,x,100,",
        ]
    )
    entries, notes = read_gl(_write(tmp_path / "gl.csv", text), NETSUITE, {})
    assert [e.date for e in entries] == ["2024-01-03", "2024-02-05", "2024-03-07"]
    assert not any("different month than their Period" in n for n in notes)


def test_qbo_rows_with_amounts_but_unreadable_dates_are_warned(tmp_path: Path):
    text = "\n".join(
        [
            ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance",  # 1
            "6400 Legal,,,,,,,,",  # 2
            ",Beginning Balance,,,,,,,\"9,000.00\"",  # 3 balance only: benign
            ",13/13/2024,Bill,B1,Hollis,fees,A/P,\"2,500.00\",",  # 4 unreadable date with money
            ",01/05/2024,Bill,B2,Hollis,fees,A/P,100.00,",  # 5
        ]
    )
    entries, notes = read_gl(_write(tmp_path / "gl.csv", text), QBO, {})
    assert [e.source_row for e in entries] == [5]
    joined = "\n".join(notes)
    assert "WARNING - dropped 1 row(s) that carry amounts (2500.00" in joined
    assert "(e.g. beginning balance) (rows 3)" in joined


@pytest.mark.parametrize(
    "name, source_type, expected",
    [
        ("Interest Earned", "Other Income", EbitdaClass.INTEREST),  # QBO default interest-income account
        ("Bank Interest", "Other Income", EbitdaClass.INTEREST),
        ("Mortgage Interest", "Other Expense", EbitdaClass.INTEREST),
        ("Interest - Line of Credit", "Other Expense", EbitdaClass.INTEREST),
        ("Interest", "Other Expense", EbitdaClass.INTEREST),
        ("Interest", "OthExpense", EbitdaClass.INTEREST),
        ("Taxes - Federal Income", "Other Expense", EbitdaClass.TAXES),
        ("Interest-free loan forgiveness", "Other Income", EbitdaClass.OTHER_INCOME),
        ("Non-controlling interest", "Other Expense", EbitdaClass.OTHER_EXPENSE),
        ("Bank Charges & Interest", "Expenses", EbitdaClass.OPEX),  # operating type keeps its class
        ("State Income", "Income", EbitdaClass.REVENUE),  # not a tax
        ("Federal Unemployment Tax", "Expenses", EbitdaClass.OPEX),  # payroll tax
    ],
)
def test_interest_and_income_tax_name_rules_cover_common_names(name: str, source_type: str, expected: EbitdaClass):
    cls, basis = classify_account(name, source_type)
    assert cls is expected, basis
    assert not basis.startswith(FALLBACK_BASIS)


def test_interest_earned_in_a_qbo_gl_is_a_credit_below_ebitda(tmp_path: Path):
    coa = _write(tmp_path / "coa.csv", "Account #,Full name,Type\n8150,Interest Earned,Other Income\n")
    accounts, _ = read_chart_of_accounts(coa)
    assert accounts[0].ebitda_class is EbitdaClass.INTEREST
    gl = ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance\n8150 Interest Earned,,,,,,,,\n,01/31/2024,Deposit,,Bank,Interest,Checking,15.25,\n"
    entries, _ = read_gl(_write(tmp_path / "gl.csv", gl), QBO, {a.number: a for a in accounts})
    assert entries[0].amount == "-15.25"
