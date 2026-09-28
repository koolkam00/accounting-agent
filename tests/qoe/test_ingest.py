"""Tests for qoe.ingest: monthly P&L, management schedule, documents, and load_deal()."""

from __future__ import annotations

import builtins
import hashlib
import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest
from reportlab.pdfgen import canvas

from qoe.ingest import load_deal, read_deal_meta, read_documents, read_monthly_pl, read_schedule
from qoe.money import D, fmt
from qoe.pdf_text import canonicalize_page_text, extract_pdf_pages
from qoe.reconcile import reconcile
from qoe.schemas import AdjustmentCategory, DataQualityCode

# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _xlsx(path: Path, rows: list[list[object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


def _pdf(path: Path, pages: list[list[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), invariant=1)
    for lines in pages:
        y = 720
        for line in lines:
            c.drawString(72, y, line)
            y -= 18
        c.showPage()
    c.save()
    return path


def _text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# A three-month ledger: (date, account, name, memo, doc #, debit-positive amount).
ACCOUNTS = [
    ("4000", "Service Revenue", "Income"),
    ("4900", "Sales Discounts", "Income"),
    ("6200", "Insurance", "Expenses"),
    ("6400", "Legal & Professional Fees", "Expenses"),
    ("7000", "Depreciation Expense", "Expenses"),
    ("8000", "Other Income", "Other Income"),
    ("8100", "Interest Expense", "Other Expense"),
    ("9000", "Income Taxes - State", "Other Expense"),
]
TXNS = [
    ("2024-01-05", "4000", "Acme Corp", "Service - Jan", "1001", "-10000.00"),
    ("2024-01-20", "4900", "Acme Corp", "Early-pay discount", "1001", "200.00"),
    ("2024-01-10", "6200", "Coastal Risk", "Premium - Jan", "POL-11", "800.00"),
    ("2024-01-15", "6400", "Hollis & Crane LLP", "Retainer - Jan", "H-01", "1500.00"),
    ("2024-01-31", "7000", "", "Monthly depreciation", "JE-1", "300.00"),
    ("2024-01-31", "8100", "Gulfstream Bank", "Loan interest", "JE-2", "100.00"),
    ("2024-01-31", "9000", "State DOR", "Estimated tax", "JE-3", "50.00"),
    ("2024-02-05", "4000", "Acme Corp", "Service - Feb", "1002", "-10000.00"),
    ("2024-02-20", "4900", "Acme Corp", "Early-pay discount", "1002", "200.00"),
    ("2024-02-10", "6200", "Coastal Risk", "Premium - Feb", "POL-22", "800.00"),
    ("2024-02-12", "6200", "Coastal Risk", "Premium - Feb", "POL-22", "800.00"),  # planted duplicate
    ("2024-02-15", "6400", "Hollis & Crane LLP", "Retainer - Feb", "H-02", "1500.00"),
    ("2024-02-28", "8000", "Sunshine Mutual", "Insurance proceeds", "", "-400.00"),
    ("2024-02-29", "7000", "", "Monthly depreciation", "JE-4", "300.00"),
    ("2024-02-29", "8100", "Gulfstream Bank", "Loan interest", "JE-5", "100.00"),
    ("2024-02-29", "9000", "State DOR", "Estimated tax", "JE-6", "50.00"),
    ("2024-03-05", "4000", "Acme Corp", "Service - Mar", "1003", "-10000.00"),
    ("2024-03-20", "4900", "Acme Corp", "Early-pay discount", "1003", "200.00"),
    ("2024-03-10", "6200", "Coastal Risk", "Premium - Mar", "POL-33", "800.00"),
    ("2024-03-15", "6400", "Hollis & Crane LLP", "Retainer - Mar", "H-03", "1500.00"),
    ("2024-03-31", "7000", "", "Monthly depreciation", "JE-7", "300.00"),
    ("2024-03-31", "8100", "Gulfstream Bank", "Loan interest", "JE-8", "100.00"),
    ("2024-03-31", "9000", "State DOR", "Estimated tax", "JE-9", "50.00"),
]
MONTHS = ["2024-01", "2024-02", "2024-03"]
PERIODS = [("Q1-24", "2024-01", "2024-03"), ("Feb-Mar 24", "2024-02", "2024-03")]
TOP_SIDE = ("2024-03", "6400", Decimal("250.00"))  # in management's P&L, not in the GL
CREDIT_TYPES = {"Income", "Other Income"}


def _us_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{m}/{d}/{y}"


def _money_text(amount: Decimal) -> str:
    text = f"{abs(amount):,.2f}"
    return f"({text})" if amount < 0 else text


def _qbo_gl(path: Path) -> dict[tuple[str, str, str], int]:
    """Write a QBO GL; returns (date, account, doc) -> physical line number."""
    types = {a: t for a, _, t in ACCOUNTS}
    names = {a: n for a, n, _ in ACCOUNTS}
    lines = ["Test Co (SYNTHETIC)", "General Ledger", '"January 1, 2024 - March 31, 2024"', "",
             ",Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance"]
    rows: dict[tuple[str, str, str], int] = {}
    for number, name, _ in ACCOUNTS:
        lines.append(f"{number} {name},,,,,,,,")
        for when, acct, cp, memo, doc, amount in sorted(t for t in TXNS if t[1] == number):
            natural = -D(amount) if types[acct] in CREDIT_TYPES else D(amount)
            lines.append(f',{_us_date(when)},Journal Entry,{doc},{cp},{memo},Checking,"{_money_text(natural)}",')
            rows[(when, acct, doc)] = len(lines)
        lines.append(f"Total for {number} {names[number]},,,,,,,,")
    lines += ["TOTAL,,,,,,,,", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + "\n".join(lines).encode("utf-8"))
    return rows


def _netsuite_gl(path: Path) -> None:
    names = {a: n for a, n, _ in ACCOUNTS}
    lines = ["Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit,Subsidiary,Department,Class,Location"]
    for i, (when, acct, cp, memo, doc, amount) in enumerate(TXNS):
        y, m, d = when.split("-")
        a = D(amount)
        debit, credit = (f"{a:.2f}", "") if a > 0 else ("", f"{-a:.2f}")
        lines.append(f"{5000 + i},{int(m)}/{int(d)}/{y},,Journal,{doc},{acct} {names[acct]},{cp},{memo},{debit},{credit},Parent,,,")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _xero_gl(path: Path) -> None:
    names = {a: n for a, n, _ in ACCOUNTS}
    rows: list[list[object]] = [["Account Transactions"], ["Test Co (SYNTHETIC)"], ["For the period 1 January 2024 to 31 March 2024"], [],
                                ["Date", "Source", "Description", "Reference", "Debit", "Credit", "Running Balance", "Account Code", "Account"]]
    for when, acct, cp, memo, doc, amount in TXNS:
        a = D(amount)
        y, m, d = (int(x) for x in when.split("-"))
        desc = f"{cp} - {memo}" if cp else memo
        rows.append([datetime(y, m, d), "Manual Journal", desc, doc, float(a) if a > 0 else None, float(-a) if a < 0 else None, None, acct, names[acct]])
    _xlsx(path, rows)


def _gl_by_account_month() -> dict[tuple[str, str], Decimal]:
    out: dict[tuple[str, str], Decimal] = {}
    for when, acct, *_rest, amount in TXNS:
        key = (when[:7], acct)
        out[key] = out.get(key, Decimal(0)) + D(amount)
    return out


def _expected_ebitda(months: list[str]) -> Decimal:
    by_class = {"8100", "9000", "7000"}
    net_income = -sum((D(t[5]) for t in TXNS if t[0][:7] in months), Decimal(0))
    addbacks = sum((D(t[5]) for t in TXNS if t[0][:7] in months and t[1] in by_class), Decimal(0))
    return net_income + addbacks


def _write_pl(path: Path) -> None:
    gl = _gl_by_account_month()
    types = {a: t for a, _, t in ACCOUNTS}
    sections = [("Income", ["4000", "4900"]), ("Expenses", ["6200", "6400", "7000"]),
                ("Other Income", ["8000"]), ("Other Expenses", ["8100", "9000"])]
    rows: list[list[object]] = [["Test Co (SYNTHETIC)"], ["Profit and Loss by Month"], ["January - March, 2024"], [],
                                [None, "Jan 2024", "Feb 2024", "Mar 2024", "Total"]]
    names = {a: n for a, n, _ in ACCOUNTS}
    for section, accts in sections:
        rows.append([section])
        for acct in accts:
            cells: list[object] = []
            for month in MONTHS:
                amount = gl.get((month, acct), Decimal(0))
                if (month, acct) == TOP_SIDE[:2]:
                    amount += TOP_SIDE[2]
                shown = -amount if types[acct] in CREDIT_TYPES else amount
                cells.append(None if amount == 0 else float(shown))
            rows.append([f"{acct} {names[acct]}", *cells, None])
        rows.append([f"Total {section}"])
    rows.append(["Net Income"])
    _xlsx(path, rows)


def _write_schedule(path: Path) -> None:
    labels = [p[0] for p in PERIODS]
    reported, interest, taxes, dep = {}, {}, {}, {}
    for label, start, end in PERIODS:
        months = [m for m in MONTHS if start <= m <= end]
        gl_ebitda = _expected_ebitda(months)
        topside = TOP_SIDE[2] if TOP_SIDE[0] in months else Decimal(0)
        reported[label] = gl_ebitda - topside
        interest[label] = Decimal(100) * len(months)
        taxes[label] = Decimal(50) * len(months)
        dep[label] = Decimal(300) * len(months)
    ni = {k: reported[k] - interest[k] - taxes[k] - dep[k] for k in labels}
    adj = {"Q1-24": Decimal("4500"), "Feb-Mar 24": Decimal("3000")}

    def vals(d: dict[str, Decimal]) -> list[float]:
        return [float(d[k]) for k in labels]

    rows: list[list[object]] = [
        ["Test Co (SYNTHETIC)"], ["Management Adjusted EBITDA"], [],
        ["Ref", "Adjustment", "Category", "GL Account(s)", "Support Ref", "Description", *labels],
        [None, "Net income", None, None, None, None, *vals(ni)],
        [None, "Interest expense", None, None, None, None, *vals(interest)],
        [None, "Income tax expense", None, None, None, None, *vals(taxes)],
        [None, "Depreciation and amortization", None, None, None, None, *vals(dep)],
        [None, "Reported EBITDA", None, None, None, None, *vals(reported)],
        ["A-1", "Litigation legal fees", "Non-recurring", "6400", "DR 4.2", "Hollis & Crane", *vals(adj)],
        [None, "Total management adjustments", None, None, None, None, *vals(adj)],
        [None, "Management adjusted EBITDA", None, None, None, None, *vals({k: reported[k] + adj[k] for k in labels})],
    ]
    _xlsx(path, rows)


DEAL_YAML = """\
deal_id: test_deal
target_name: Test Co (SYNTHETIC)
industry: Services
synthetic: true
currency: USD
periods:
  - {{label: "Q1-24", start: "2024-01", end: "2024-03"}}
  - {{label: "Feb-Mar 24", start: "2024-02", end: "2024-03"}}
data_start: "2024-01"
data_end: 2024-03
gl_format: {gl_format}
files:
  gl: {gl_file}
  chart_of_accounts: gl/chart_of_accounts.csv
  monthly_pl: financials/monthly_pl.xlsx
  adjustments: adjustments/management_adjusted_ebitda.xlsx
  documents_dir: documents
tolerance: 1
"""


def build_deal(root: Path, gl_kind: str = "qbo", gl_format: str = "auto") -> Path:
    gl_file = {"qbo": "gl/general_ledger.csv", "netsuite": "gl/general_ledger.csv", "xero": "gl/general_ledger.xlsx"}[gl_kind]
    _text(root / "deal.yaml", DEAL_YAML.format(gl_format=gl_format, gl_file=gl_file))
    {"qbo": _qbo_gl, "netsuite": _netsuite_gl, "xero": _xero_gl}[gl_kind](root / gl_file)
    _text(root / "gl" / "chart_of_accounts.csv", "Account #,Full name,Type\n" + "\n".join(f"{a},{n},{t}" for a, n, t in ACCOUNTS) + "\n")
    _write_pl(root / "financials" / "monthly_pl.xlsx")
    _write_schedule(root / "adjustments" / "management_adjusted_ebitda.xlsx")
    _text(root / "documents" / "4 Legal" / "4.2 Hollis Crane engagement letter.txt",
          "Hollis & Crane LLP\n\nMatter 2291   Dawson v. Test Co\nRetainer: $1,500 per month\n\nSYNTHETIC\n")
    _pdf(root / "documents" / "4 Legal" / "4.2.1 Hollis Crane Invoice H-03.pdf",
         [["Hollis & Crane LLP", "Invoice H-03    Total due: $1,500.00"], ["Remit to: Tampa, FL", "SYNTHETIC"]])
    _text(root / "README.txt", "SYNTHETIC deal package for tests.\n")
    # The answer key is deliberately unreadable: ingest must never open it.
    _text(root / "ground_truth.json", "{this is not json")
    return root


# ---------------------------------------------------------------------------
# Monthly P&L
# ---------------------------------------------------------------------------


def _pl_fixture(path: Path) -> Path:
    return _xlsx(
        path,
        [
            ["Test Co (SYNTHETIC)"],  # 1
            ["Profit and Loss by Month"],  # 2
            ["January - March 2024"],  # 3
            [],  # 4
            [None, "Jan 2024", datetime(2024, 2, 1), "2024-03", "Total"],  # 5
            ["Income"],  # 6
            ["4000 Service Revenue", 1000, "1,100.00", 1200, 3300],  # 7
            ["4900 · Sales Discounts", -50, None, -25, -75],  # 8
            ["Total Income", 950, 1100, 1175, 3225],  # 9
            ["Cost of Goods Sold"],  # 10
            ["5000 - Materials", 300, 310, 320, 930],  # 11
            ["Total Cost of Goods Sold", 300, 310, 320, 930],  # 12
            ["Gross Profit", 650, 790, 855, 2295],  # 13
            ["Expenses"],  # 14
            ["  6400   Legal & Professional Fees  ", 100, "$(20.00)", None, 80],  # 15
            ["7000: Depreciation Expense", 10, 10, 10, 30],  # 16
            ["Total Expenses", 110, -10, 10, 110],  # 17
            ["Net Operating Income", 540, 800, 845, 2185],  # 18
            ["Other Income"],  # 19
            ["8000 Other Income", 40, 0, 0, 40],  # 20
            ["Total Other Income", 40, 0, 0, 40],  # 21
            ["Other Expenses"],  # 22
            ["8100 Interest Expense", 5, 5, 5, 15],  # 23
            ["Total Other Expenses", 5, 5, 5, 15],  # 24
            ["Net Other Income", 35, -5, -5, 25],  # 25
            ["Net Income", 575, 795, 840, 2210],  # 26
        ],
    )


def test_monthly_pl_sections_signs_and_rows(tmp_path: Path):
    pl = read_monthly_pl(_pl_fixture(tmp_path / "pl.xlsx"), source_label="financials/monthly_pl.xlsx")
    assert pl.source_file == "financials/monthly_pl.xlsx"
    assert pl.months == ["2024-01", "2024-02", "2024-03"]
    lines = {ln.account: ln for ln in pl.lines}
    assert list(lines) == ["4000", "4900", "5000", "6400", "7000", "8000", "8100"]
    # Income is credit-natural: revenue becomes negative, a contra shown negative becomes positive.
    assert lines["4000"].amounts == {"2024-01": "-1000.00", "2024-02": "-1100.00", "2024-03": "-1200.00"}
    assert lines["4900"].amounts == {"2024-01": "50.00", "2024-02": "0.00", "2024-03": "25.00"}
    assert lines["5000"].amounts["2024-03"] == "320.00"
    assert lines["6400"].amounts == {"2024-01": "100.00", "2024-02": "-20.00", "2024-03": "0.00"}
    assert lines["8000"].amounts["2024-01"] == "-40.00"
    assert lines["8100"].amounts["2024-01"] == "5.00"
    assert (lines["4900"].account_name, lines["5000"].account_name, lines["6400"].account_name, lines["7000"].account_name) == (
        "Sales Discounts", "Materials", "Legal & Professional Fees", "Depreciation Expense"
    )
    assert (lines["4000"].section, lines["8000"].section, lines["8100"].section) == ("Income", "Other Income", "Other Expenses")
    assert (lines["4000"].source_row, lines["8100"].source_row) == (7, 23)


def test_monthly_pl_without_month_header_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        read_monthly_pl(_xlsx(tmp_path / "pl.xlsx", [["Income"], ["4000 Revenue", 1, 2]]))


# ---------------------------------------------------------------------------
# Management schedule
# ---------------------------------------------------------------------------

LABELS = ["FY2024", "FY2025", "TTM Jun-26"]


def _schedule_fixture(path: Path) -> Path:
    return _xlsx(
        path,
        [
            ["Test Co (SYNTHETIC)"],  # 1
            ["Management Adjusted EBITDA"],  # 2
            [],  # 3
            ["Ref", "Adjustment", "Category", "GL Account(s)", "Support Ref", "Description", " fy2024 ", "FY2025", "TTM  Jun-26"],  # 4
            [None, "Net income", None, None, None, None, 1000, 2000, 2100],  # 5
            [None, "Interest expense", None, None, None, None, 50, 60, 55],  # 6
            [None, "Income tax expense", None, None, None, None, 10, 20, 15],  # 7
            [None, "Depreciation and amortization", None, None, None, None, 100, 110, 105],  # 8
            [None, "Reported EBITDA", None, None, None, None, 1160, 2190, 2275],  # 9
            ["M-01", "Litigation legal fees", "Non-recurring", "6400", "DR 4.2; DR 4.3", "Dawson matter", 0, 120000, 65500],  # 10
            ["M-02", "Owner compensation", "Owner compensation normalization", "6010", "DR 5.1", "Market salary", 360000, 360000, 360000],  # 11
            ["M-03", "Personal expenses", "Owner / discretionary", "6600, 6650 and 6700", "DR 6.1, DR 6.2", None, None, 48000, "48,000"],  # 12
            ["M-04", "Prior-year true-up", "Out-of-period", "Acct 5200", "DR 7", None, 0, 42000, 0],  # 13
            ["M-05", "Dispatcher savings", "Pro forma", None, None, None, 0, 0, 165000],  # 14
            [3, "Storm recovery", "Other", 8000, None, None, -40000, 0, 0],  # 15
            [None, "Total management adjustments", None, None, None, None, 320000, 570000, 638500],  # 16
            [None, "Management adjusted EBITDA", None, None, None, None, 321160, 572190, 640775],  # 17
            [],  # 18
            ["Note: SYNTHETIC - generated for QoE Evidence Review testing"],  # 19
        ],
    )


def test_schedule_header_labels_and_adjustments(tmp_path: Path):
    sched = read_schedule(_schedule_fixture(tmp_path / "adj.xlsx"), LABELS)
    assert sched.period_labels == LABELS
    assert sched.net_income == {"FY2024": "1000.00", "FY2025": "2000.00", "TTM Jun-26": "2100.00"}
    assert sched.interest["FY2025"] == "60.00"
    assert sched.taxes["TTM Jun-26"] == "15.00"
    assert sched.depreciation_amortization["FY2024"] == "100.00"
    assert sched.reported_ebitda["FY2025"] == "2190.00"
    assert sched.total_adjustments["TTM Jun-26"] == "638500.00"
    assert sched.adjusted_ebitda["FY2024"] == "321160.00"

    adjs = {a.adj_id: a for a in sched.adjustments}
    assert list(adjs) == ["M-01", "M-02", "M-03", "M-04", "M-05", "3"]
    assert [a.category for a in sched.adjustments] == [
        AdjustmentCategory.NON_RECURRING,
        AdjustmentCategory.NORMALIZATION,
        AdjustmentCategory.OWNER_DISCRETIONARY,
        AdjustmentCategory.OUT_OF_PERIOD,
        AdjustmentCategory.PRO_FORMA,
        AdjustmentCategory.OTHER,
    ]
    m01 = adjs["M-01"]
    assert (m01.title, m01.category_raw, m01.description, m01.source_row) == (
        "Litigation legal fees", "Non-recurring", "Dawson matter", 10
    )
    assert m01.gl_accounts == ["6400"] and m01.support_refs == ["DR 4.2", "DR 4.3"]
    assert m01.amounts == {"FY2024": "0.00", "FY2025": "120000.00", "TTM Jun-26": "65500.00"}
    assert adjs["M-03"].gl_accounts == ["6600", "6650", "6700"]
    assert adjs["M-03"].support_refs == ["DR 6.1", "DR 6.2"]
    assert adjs["M-03"].amounts["FY2024"] == "0.00" and adjs["M-03"].amounts["TTM Jun-26"] == "48000.00"
    assert adjs["M-04"].gl_accounts == ["5200"]
    assert adjs["M-05"].gl_accounts == [] and adjs["M-05"].support_refs == []
    assert adjs["3"].gl_accounts == ["8000"] and adjs["3"].amounts["FY2024"] == "-40000.00"


def test_schedule_label_rows_in_ref_column(tmp_path: Path):
    path = _xlsx(
        tmp_path / "adj.xlsx",
        [
            ["#", "Item", "FY2024"],
            ["Net income", None, 900],
            ["EBITDA", None, 1000],
            [1, "Severance", 75],
            ["Adjusted EBITDA", None, 1075],
        ],
    )
    sched = read_schedule(path, ["FY2024"])
    assert sched.net_income == {"FY2024": "900.00"}
    assert sched.reported_ebitda == {"FY2024": "1000.00"}
    assert sched.adjusted_ebitda == {"FY2024": "1075.00"}
    assert [(a.adj_id, a.title) for a in sched.adjustments] == [("1", "Severance")]


def test_schedule_missing_period_label_raises(tmp_path: Path):
    with pytest.raises(ValueError) as err:
        read_schedule(_schedule_fixture(tmp_path / "adj.xlsx"), ["FY2023", "FY2024"])
    assert "FY2023" in str(err.value)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def test_documents_all_types_sorted_and_canonical(tmp_path: Path):
    deal = tmp_path / "deal"
    docs = deal / "documents"
    _text(docs / "b" / "2.1 Memo.md", "# Inventory   memo\r\n\r\n\r\nConsistent with prior years.\n")
    _text(docs / "a" / "1.1 Email.txt", "From: Controller\nSubject: FieldPro\n\nOur   FieldPro subscription\t renews.\n")
    _text(
        docs / "a" / "1.2 Forward.eml",
        "From: COO <coo@example.com>\nTo: CFO <cfo@example.com>\nDate: Tue, 10 Mar 2026 09:00:00 -0500\n"
        "Subject: Dispatch plan\nContent-Type: text/plain; charset=utf-8\n\n"
        "We plan to reduce the dispatch team by three FTEs.\n",
    )
    _pdf(docs / "c" / "3.1 Invoice.pdf", [["Invoice 25-0212    Total due: $14,500.00"], ["Page two text"]])
    _text(docs / "c" / "notes.docx", "binary-ish")
    _text(docs / ".DS_Store", "junk")

    result = read_documents(docs, deal)
    assert [d.doc_id for d in result] == ["1.1 Email.txt", "1.2 Forward.eml", "2.1 Memo.md", "3.1 Invoice.pdf"]
    assert [d.media_type for d in result] == ["txt", "eml", "md", "pdf"]
    email, eml, memo, pdf = result
    assert email.relpath == "documents/a/1.1 Email.txt"
    assert email.sha256 == hashlib.sha256((docs / "a" / "1.1 Email.txt").read_bytes()).hexdigest()
    assert [p.page for p in email.pages] == [1]
    assert "Our FieldPro subscription renews." in email.pages[0].text
    assert memo.pages[0].text == "# Inventory memo\n\nConsistent with prior years."
    assert "From: COO <coo@example.com>" in eml.pages[0].text
    assert "Subject: Dispatch plan" in eml.pages[0].text
    assert "We plan to reduce the dispatch team by three FTEs." in eml.pages[0].text

    assert [p.page for p in pdf.pages] == [1, 2]
    raw = extract_pdf_pages(docs / "c" / "3.1 Invoice.pdf")
    assert [p.text for p in pdf.pages] == [canonicalize_page_text(t) for t in raw]
    assert "Invoice 25-0212 Total due: $14,500.00" in pdf.pages[0].text
    assert "Page two text" in pdf.pages[1].text


def test_documents_duplicate_basename_raises(tmp_path: Path):
    _text(tmp_path / "documents" / "a" / "Invoice.txt", "one")
    _text(tmp_path / "documents" / "b" / "Invoice.txt", "two")
    with pytest.raises(ValueError, match="unique"):
        read_documents(tmp_path / "documents", tmp_path)


# ---------------------------------------------------------------------------
# deal.yaml and load_deal
# ---------------------------------------------------------------------------


def test_read_deal_meta_normalizes_values(tmp_path: Path):
    build_deal(tmp_path)
    meta = read_deal_meta(tmp_path / "deal.yaml")
    assert meta.deal_id == "test_deal"
    assert [(p.label, p.start, p.end) for p in meta.periods] == [("Q1-24", "2024-01", "2024-03"), ("Feb-Mar 24", "2024-02", "2024-03")]
    assert (meta.data_start, meta.data_end, meta.tolerance, meta.gl_format) == ("2024-01", "2024-03", "1.00", "auto")


def test_load_deal_never_opens_ground_truth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    deal = build_deal(tmp_path / "deal")
    opened: list[str] = []
    real_open = io.open

    def spy_open(file, *args, **kwargs):
        opened.append(str(file))
        if Path(str(file)).name == "ground_truth.json":
            raise AssertionError("ingest opened ground_truth.json")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", spy_open)
    monkeypatch.setattr(builtins, "open", spy_open)
    pkg = load_deal(deal)
    monkeypatch.undo()

    assert opened, "spy saw no file opens; the test would prove nothing"
    assert not any(Path(p).name == "ground_truth.json" for p in opened)
    assert "ground_truth.json" not in pkg.input_hashes
    assert len(pkg.gl) == len(TXNS)


def test_load_deal_package_contents(tmp_path: Path):
    deal = build_deal(tmp_path / "deal")
    pkg = load_deal(deal)
    assert pkg.meta.deal_id == "test_deal"
    assert set(pkg.accounts) == {a for a, _, _ in ACCOUNTS}
    assert [d.doc_id for d in pkg.documents] == ["4.2 Hollis Crane engagement letter.txt", "4.2.1 Hollis Crane Invoice H-03.pdf"]
    assert [a.adj_id for a in pkg.schedule.adjustments] == ["A-1"]
    assert pkg.pl.source_file == "financials/monthly_pl.xlsx"
    assert pkg.gl[0].source_file == "gl/general_ledger.csv"

    expected_files = {
        "deal.yaml",
        "gl/general_ledger.csv",
        "gl/chart_of_accounts.csv",
        "financials/monthly_pl.xlsx",
        "adjustments/management_adjusted_ebitda.xlsx",
        "documents/4 Legal/4.2 Hollis Crane engagement letter.txt",
        "documents/4 Legal/4.2.1 Hollis Crane Invoice H-03.pdf",
    }
    assert set(pkg.input_hashes) == expected_files
    assert list(pkg.input_hashes) == sorted(pkg.input_hashes)
    for rel, digest in pkg.input_hashes.items():
        assert digest == hashlib.sha256((deal / rel).read_bytes()).hexdigest()

    notes = "\n".join(pkg.ingest_notes)
    assert "qbo_gl_csv auto-detected" in notes
    assert f"{len(TXNS)} entries" in notes
    assert "total/subtotal rows" in notes
    assert "2 loaded" in notes
    assert str(tmp_path) not in notes  # notes land in the workpaper; no machine paths


def test_load_deal_picks_up_default_overrides_file(tmp_path: Path):
    deal = build_deal(tmp_path / "deal")
    _text(deal / "gl" / "account_mapping_overrides.csv", "account,ebitda_class,basis\n6200,OTHER_EXPENSE,Non-operating\n")
    pkg = load_deal(deal)
    assert pkg.accounts["6200"].mapping_basis == "override: Non-operating"
    assert "gl/account_mapping_overrides.csv" in pkg.input_hashes


def test_gl_account_missing_from_coa_gets_fallback_class_and_sign(tmp_path: Path):
    deal = build_deal(tmp_path / "deal")
    coa = deal / "gl" / "chart_of_accounts.csv"
    coa.write_text("\n".join(line for line in coa.read_text().splitlines() if not line.startswith("8000")) + "\n")
    pkg = load_deal(deal)
    acct = pkg.accounts["8000"]
    assert acct.mapping_basis.startswith("fallback")
    assert acct.ebitda_class.value == "OTHER_INCOME"  # from the P&L section it sits in
    # QBO shows the credit as positive; once the class is known it is re-signed as a credit.
    assert [e.amount for e in pkg.gl if e.account == "8000"] == ["-400.00"]
    issues = reconcile(pkg).issues
    assert [i.account for i in issues if i.code is DataQualityCode.UNMAPPED_ACCOUNT] == ["8000"]


@pytest.mark.parametrize("gl_kind", ["qbo", "netsuite", "xero"])
def test_load_and_reconcile_every_gl_format(tmp_path: Path, gl_kind: str):
    """All three exports of the same ledger ingest to the same debit-positive
    account-months and reconcile with exactly the planted issues."""
    pkg = load_deal(build_deal(tmp_path / "deal", gl_kind))
    rollup: dict[tuple[str, str], Decimal] = {}
    for e in pkg.gl:
        rollup[(e.period, e.account)] = rollup.get((e.period, e.account), Decimal(0)) + D(e.amount)
    assert rollup == _gl_by_account_month()

    recon = reconcile(pkg)
    assert recon.gl_ebitda["Q1-24"].ebitda == fmt(_expected_ebitda(MONTHS))
    assert recon.gl_ebitda["Feb-Mar 24"].ebitda == fmt(_expected_ebitda(MONTHS[1:]))
    assert recon.gl_ebitda["Q1-24"].interest == "300.00"
    assert recon.gl_ebitda["Q1-24"].taxes == "150.00"
    assert recon.gl_ebitda["Q1-24"].depreciation == "900.00"

    codes = sorted((i.code.value, i.month or "", i.account or "", i.period_label or "") for i in recon.issues)
    assert codes == [
        ("DUPLICATE_GL_ENTRY", "2024-02", "6200", ""),
        ("MGMT_EBITDA_DIFFERS_FROM_GL", "", "", "Feb-Mar 24"),
        ("MGMT_EBITDA_DIFFERS_FROM_GL", "", "", "Q1-24"),
        ("RECON_VARIANCE", "2024-03", "6400", ""),
    ]
    variance = next(i for i in recon.issues if i.code is DataQualityCode.RECON_VARIANCE)
    assert variance.amount == "250.00"
    for issue in recon.issues:
        if issue.code is DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL:
            assert issue.amount == "-250.00"
            assert "explains the difference" in issue.message


def test_explicit_gl_format_is_used(tmp_path: Path):
    pkg = load_deal(build_deal(tmp_path / "deal", "netsuite", gl_format="netsuite_csv"))
    assert any("netsuite_csv set in deal.yaml" in n for n in pkg.ingest_notes)
    with pytest.raises(ValueError):
        load_deal(build_deal(tmp_path / "bad", "qbo", gl_format="netsuite_csv"))


def test_qbo_source_rows_point_at_the_physical_line(tmp_path: Path):
    deal = build_deal(tmp_path / "deal")
    rows = _qbo_gl(deal / "gl" / "general_ledger.csv")
    pkg = load_deal(deal)
    for e in pkg.gl:
        assert e.source_row == rows[(e.date, e.account, e.doc_number)]
        assert e.entry_id == f"GL-R{e.source_row}"
