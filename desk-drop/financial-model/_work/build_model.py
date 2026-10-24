#!/usr/bin/env python3
"""Build 'Desk Drop financial model v1.xlsx' (workstream H) with openpyxl.

Every computed cell is a formula. Inputs live on the Inputs tab (plus the
editable Schedule, the logs and the actuals tabs). No numeric literal other
than 0 or 1 appears in any formula; _work/audit_formulas.py enforces that.

Run:  python3 financial-model/_work/build_model.py
"""
import datetime as dt
import os

import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "Desk Drop financial model v1.xlsx")
D = dt.date

# --------------------------------------------------------------------------
# styles
# --------------------------------------------------------------------------
INK = "1F3A44"
F_TITLE = Font(bold=True, size=15, color=INK)
F_SUB = Font(size=11, color="4A5A60", italic=True)
F_H = Font(bold=True, color="FFFFFF")
FILL_H = PatternFill("solid", fgColor="2E5E6B")
F_SEC = Font(bold=True, color=INK, size=12)
FILL_SEC = PatternFill("solid", fgColor="DCE8EB")
FILL_IN = PatternFill("solid", fgColor="FFF4CC")
F_IN = Font(color="1A3FB5")
F_NOTE = Font(italic=True, color="5A5A5A", size=9)
F_BOLD = Font(bold=True)
FILL_BANNER = PatternFill("solid", fgColor="FCE4D6")
F_BANNER = Font(bold=True, color="7A3A10")
FILL_CALC = PatternFill("solid", fgColor="F3F3F3")
FILL_KEY = PatternFill("solid", fgColor="E2F0D9")
FILL_SCEN = PatternFill("solid", fgColor="DDEBF7")
THIN = Side(style="thin", color="B7C4C8")
BOX = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

USD = '$#,##0;($#,##0);$0'
USD2 = '$#,##0.00;($#,##0.00);$0.00'
PH = '$#,##0.0;($#,##0.0);$0.0'
PCT = '0%'
PCT1 = '0.0%'
HRS = '0.0#'
INT = '0'
DATE = 'yyyy-mm-dd'
DDATE = 'ddd yyyy-mm-dd'

REF = {}          # key -> absolute reference string, e.g. Inputs!$C$12


def R(k):
    return REF[k]


def put(ws, addr, v, fmt=None, font=None, fill=None, align=None, border=None):
    c = ws[addr]
    c.value = v
    if fmt:
        c.number_format = fmt
    if font:
        c.font = font
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = border
    return c


def header_row(ws, row, col0, labels, height=None):
    for i, lab in enumerate(labels):
        put(ws, f"{CL(col0 + i)}{row}", lab, font=F_H, fill=FILL_H, align=CENTER, border=BOX)
    if height:
        ws.row_dimensions[row].height = height


def title(ws, text, sub=None, formula=False):
    put(ws, "A1", text, font=F_TITLE)
    if sub:
        put(ws, "A2", sub, font=F_SUB)


def banner(ws, addr, text, span=None):
    c = put(ws, addr, text, font=F_BANNER, fill=FILL_BANNER, align=Alignment(wrap_text=True, vertical="center"))
    if span:
        ws.merge_cells(f"{addr}:{span}")
    return c


def section(ws, row, text, last_col="K"):
    for col in range(1, openpyxl.utils.column_index_from_string(last_col) + 1):
        ws.cell(row=row, column=col).fill = FILL_SEC
    put(ws, f"A{row}", text, font=F_SEC, fill=FILL_SEC)


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def as_input(c):
    c.fill = FILL_IN
    c.font = F_IN
    c.border = BOX


def add_list_validation(ws, rng, source, allow_blank=True):
    dv = DataValidation(type="list", formula1=source, allow_blank=allow_blank, showDropDown=False)
    dv.error = "Pick a value from the list."
    dv.errorTitle = "Not in the list"
    ws.add_data_validation(dv)
    dv.add(rng)


def status_cf(ws, rng):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"pass"'], fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(color="006100", bold=True)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"miss"'], fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006", bold=True)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"not yet"'], fill=PatternFill("solid", fgColor="EDEDED"), font=Font(color="555555")))


def ok_cf(ws, rng, good='"ok"', bad=None):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[good], fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(color="006100")))
    if bad:
        for b in bad:
            ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[b], fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006")))


wb = openpyxl.Workbook()
wb.remove(wb.active)
TABS = ["README", "Dashboard", "Inputs", "Scenarios", "Schedule", "Calculator", "Drop_PnL", "Cash_Flow",
        "Steady_State", "Sensitivity", "Plan_Check", "Capital", "Hours_Log", "Toggl_Import", "Pipeline",
        "Actuals_Campaigns", "Actuals_DropCosts", "Drop_Actuals", "Cash_Ledger", "Checks", "Lists"]
WS = {t: wb.create_sheet(t) for t in TABS}

# --------------------------------------------------------------------------
# fixed geometry shared across tabs
# --------------------------------------------------------------------------
N_DROPS = 12
DROP0 = 7                         # first drop row on Schedule, Drop_PnL, Drop_Actuals
DROPN = DROP0 + N_DROPS - 1       # 18
N_WEEKS = 26
WK0 = 3                           # Cash_Flow column C is week 1
WKN = WK0 + N_WEEKS - 1           # column AB
WKL = CL(WKN)
REF["horizon_end"] = f"Cash_Flow!${WKL}$6"
AC0, ACN = 5, 204                 # Actuals_Campaigns data rows
DC0, DCN = 5, 104                 # Actuals_DropCosts data rows
HL0, HLN = 5, 1004                # Hours_Log data rows
TG0, TGN = 10, 509                # Toggl_Import data rows
PL0, PLN = 5, 1004                # Pipeline data rows

# ==========================================================================
# Lists
# ==========================================================================
ws = WS["Lists"]
title(ws, "Lists", "Fixed enumerations (CONTRACTS section 4), holidays and blackouts (section 3). Add rows in the blank cells; do not rename keys.")
lists = {
    "A": ("delivery_model", ["founder", "courier", "direct-ship"]),
    "B": ("tier", ["founding", "standard"]),
    "C": ("activity", ["brand_sales", "office_coordination", "receiving_kitting", "drop_day", "checks_pickup", "reporting_debriefs", "admin_invoicing"]),
    "E": ("yes_no", ["Y", "N"]),
    "F": ("scenario", ["Plan base", "A", "B", "C", "D"]),
    "G": ("side", ["office", "brand"]),
    "H": ("event", ["outreach_sent", "conversation", "yes_in_principle", "signed", "paid", "budget_probe", "renewal_answer", "opt_out"]),
    "I": ("would_buy_again", ["yes", "maybe", "no"]),
    "J": ("renewed", ["Y", "N", "pending"]),
    "K": ("storage_choice", ["unit", "home"]),
    "L": ("insurance_billing", ["annual", "monthly"]),
}
for col, (name, vals) in lists.items():
    put(ws, f"{col}3", name, font=F_H, fill=FILL_H)
    for i, v in enumerate(vals):
        put(ws, f"{col}{4 + i}", v)
put(ws, "D3", "activity label", font=F_H, fill=FILL_H)
for i, lab in enumerate(["Brand sales to signature", "Office recruiting or coordination", "Receiving and kitting", "Drop day",
                         "Day 3 and day 5 checks, pickup", "Reporting and debriefs", "Admin and invoicing"]):
    put(ws, f"D{4 + i}", lab)
REF.update({
    "L_models": "Lists!$A$4:$A$6", "L_tiers": "Lists!$B$4:$B$5", "L_acts": "Lists!$C$4:$C$10",
    "L_yn": "Lists!$E$4:$E$5", "L_scen": "Lists!$F$4:$F$8", "L_side": "Lists!$G$4:$G$5",
    "L_event": "Lists!$H$4:$H$11", "L_rebuy": "Lists!$I$4:$I$6", "L_renewed": "Lists!$J$4:$J$6",
    "L_storage": "Lists!$K$4:$K$5", "L_insbill": "Lists!$L$4:$L$5",
})
ACT_KEYS = lists["C"][1]
put(ws, "N3", "us_federal_holiday", font=F_H, fill=FILL_H)
put(ws, "O3", "holiday note", font=F_H, fill=FILL_H)
hols = [(D(2026, 11, 11), "Veterans Day"), (D(2026, 11, 26), "Thanksgiving"), (D(2026, 12, 25), "Christmas"),
        (D(2027, 1, 1), "New Year's Day"), (D(2027, 1, 18), "MLK Day"), (D(2027, 2, 15), "Presidents Day"),
        (D(2027, 5, 31), "Memorial Day"), (D(2027, 6, 18), "Juneteenth (observed)"), (D(2027, 7, 5), "Independence Day (observed)"),
        (D(2027, 9, 6), "Labor Day")]
for i in range(27):
    r = 4 + i
    if i < len(hols):
        put(ws, f"N{r}", hols[i][0], fmt=DATE)
        put(ws, f"O{r}", hols[i][1] + " (CONTRACTS s3)")
    else:
        as_input(ws[f"N{r}"])
        ws[f"N{r}"].number_format = DATE
REF["holidays"] = "Lists!$N$4:$N$30"
put(ws, "Q3", "blackout_start", font=F_H, fill=FILL_H)
put(ws, "R3", "blackout_end", font=F_H, fill=FILL_H)
put(ws, "S3", "blackout note", font=F_H, fill=FILL_H)
bos = [(D(2026, 12, 18), D(2026, 12, 31), "Last two weeks of December 2026 (CONTRACTS s3)"),
       (D(2027, 7, 5), D(2027, 7, 9), "Week of July 4 2027 observed holiday (CONTRACTS s3 rule, derived)"),
       (D(2027, 8, 18), D(2027, 8, 31), "Last two weeks of August 2027 (CONTRACTS s3 rule)"),
       (D(2027, 12, 18), D(2027, 12, 31), "Last two weeks of December 2027 (CONTRACTS s3 rule)")]
for i in range(9):
    r = 4 + i
    if i < len(bos):
        put(ws, f"Q{r}", bos[i][0], fmt=DATE)
        put(ws, f"R{r}", bos[i][1], fmt=DATE)
        put(ws, f"S{r}", bos[i][2])
    else:
        for col in "QR":
            as_input(ws[f"{col}{r}"])
            ws[f"{col}{r}"].number_format = DATE
REF["bo_start"] = "Lists!$Q$4:$Q$12"
REF["bo_end"] = "Lists!$R$4:$R$12"
put(ws, "U3", "weekday (WEEKDAY, Sunday = 1)", font=F_H, fill=FILL_H)
put(ws, "U4", "Tuesday")
put(ws, "V4", 3)
put(ws, "U5", "Wednesday")
put(ws, "V5", 4)
REF["wd_tue"] = "Lists!$V$4"
REF["wd_wed"] = "Lists!$V$5"
widths(ws, {"A": 14, "B": 11, "C": 21, "D": 32, "E": 8, "F": 11, "G": 9, "H": 17, "I": 15, "J": 10, "K": 14, "L": 16,
            "N": 13, "O": 34, "Q": 13, "R": 13, "S": 52, "U": 30, "V": 6})

# ==========================================================================
# Inputs
# ==========================================================================
ws = WS["Inputs"]
title(ws, "Inputs", "Every assumption in one labeled cell. Yellow cells are inputs. Grey cells are calculated; do not type over them.")
banner(ws, "A3", "All defaults are planning estimates from plan.md, never forecasts. 'Plan default' keeps the original figure; 'Changed' flags any cell you edit.", "K3")
INP_HDR = ["key", "Assumption", "Value", "Unit", "Low", "High", "Status", "Source", "Notes", "Plan default", "Changed?"]
row = [5]
CHANGED_CELLS = []


def inp_section(text):
    row[0] += 1
    section(ws, row[0], text)
    row[0] += 1
    header_row(ws, row[0], 1, INP_HDR)
    row[0] += 1


def inp(key, label, value, unit, status, source, notes="", low=None, high=None, fmt=None, calc=False, vlist=None):
    r = row[0]
    put(ws, f"A{r}", key, font=F_NOTE)
    put(ws, f"B{r}", label, align=WRAP)
    c = put(ws, f"C{r}", value, fmt=fmt)
    if calc:
        c.fill = FILL_CALC
        c.border = BOX
    else:
        as_input(c)
        if fmt:
            c.number_format = fmt
    put(ws, f"D{r}", unit)
    if low is not None:
        put(ws, f"E{r}", low, fmt=fmt)
    if high is not None:
        put(ws, f"F{r}", high, fmt=fmt)
    put(ws, f"G{r}", status)
    put(ws, f"H{r}", source, align=WRAP)
    put(ws, f"I{r}", notes, align=WRAP)
    if not calc:
        put(ws, f"J{r}", value, fmt=fmt, font=F_NOTE)
        put(ws, f"K{r}", f'=IF(C{r}&""=J{r}&"","","changed")', font=Font(color="9C0006", bold=True))
        CHANGED_CELLS.append(f"K{r}")
    if vlist:
        add_list_validation(ws, f"C{r}", "=" + REF[vlist])
    for col in "ACDEFGJK":
        ws[f"{col}{r}"].alignment = Alignment(vertical="top", wrap_text=ws[f"{col}{r}"].alignment.wrap_text)
    REF[key] = f"Inputs!$C${r}"
    row[0] += 1
    return r


P_ECON = "plan.md, Economics: hard-cost table"
P_HOURS = "plan.md, Economics: founder-hour table"
P_PRICE = "plan.md, Revised model: Price table"
P_CAP = "plan.md, Economics: Capital to the first six months"
CTR3 = "CONTRACTS.md section 3 (canonical calendar)"

inp_section("1. Company and calendar")
inp("company_name", "Company name (working name, not yet cleared)", "Desk Drop", "text", "working name", "Prompt; CONTRACTS s2 rename-ability",
    "The only cell that holds the company name. Rename here and every tab follows.")
inp("tagline", "Tagline (working, may change)", "Emerging brands. Delivered to your workday.", "text", "working", "Prompt; CONTRACTS s2")
inp("week1_start", "Week 1 starts (Monday)", D(2026, 10, 26), "date", "derived, founder to confirm", CTR3, "Week n starts on this date plus 7 x (n - 1) days.", fmt=DATE)
inp("gate0_date", "Gate 0 review (end of week 3)", D(2026, 11, 13), "date", "derived, founder to confirm", CTR3, fmt=DATE)
inp("gate1_date", "Gate 1 review (end of week 7)", D(2026, 12, 11), "date", "derived, founder to confirm", CTR3, fmt=DATE)
inp("gate2_date", "Gate 2 review (campaign zero report, T+7)", D(2027, 1, 22), "date", "derived, founder to confirm", CTR3,
    "Moved from the plan's week 9 because campaign zero moved to 2027-01-12 (December blackout collision).", fmt=DATE)
inp("gate3_date", "Gate 3 review", D(2027, 3, 12), "date", "derived, founder to confirm", CTR3, "Week 20; replaces the plan's week 16.", fmt=DATE)
inp("decision_date", "Six-month decision (end of week 24)", D(2027, 4, 9), "date", "derived, founder to confirm", CTR3, fmt=DATE)
r_ovr = inp("as_of_override", "As-of date override (blank = today)", None, "date", "setting", "Model setting",
            "Leave blank to use today's date. Type a date to see gates and the next drop as of that day.", fmt=DATE)
inp("as_of", "As-of date in use", f'=IF(C{r_ovr}="",TODAY(),C{r_ovr})', "date", "calculated", "Model", fmt=DATE, calc=True)
inp("days_per_week", "Days per week", 7, "days", "conversion", "Calendar")
inp("weeks_per_year", "Weeks per year", 52, "weeks", "conversion", "Calendar")
inp("months_per_year", "Months per year", 12, "months", "conversion", "Calendar")
inp("weeks_per_month", "Weeks per month", f"={R('weeks_per_year')}/{R('months_per_year')}", "weeks", "calculated", "Weeks per year / months per year", fmt='0.00', calc=True)
inp("hours_per_day", "Hours per day (converts Toggl durations)", 24, "hours", "conversion", "Calendar")
inp("window_bd", "Campaign window", 5, "business days", "planning estimate", "plan.md, What brands buy: 'Five business days'", "T is day 1; the window closes at T+4.")
inp("drop_prefix", "Drop ID prefix", "DRP-", "text", "convention", "CONTRACTS s6.5 (DRP-###)", "Toggl projects named DRP-001 etc. map to drops.")
inp("office_window_days", "An office should get at most one drop in this many days", 28, "days", "derived, founder to confirm",
    "plan.md, What has to be true #4: 'Offices accept one drop a month'", "Four weeks counts as monthly, so drops 28 days apart do not flag. Used for the office-fatigue warning on Schedule.")

inp_section("2. Scenario in force")
inp("active_scenario", "Scenario applied to drops after Gate 3 and to the steady state", "Plan base", "list", "setting",
    "plan.md, After the first standard runs: decision scenarios", "Plan base = the plan's 'What has to be true'. A to D = the plan's four decision situations. See the Scenarios tab.", vlist="L_scen")

inp_section("3. Prices and payment terms")
inp("price_std_office", "Standard price per office", 150, "USD per office", "planning estimate", P_PRICE, "$1,500 for 10 offices. Change this cell to test a price.", fmt=USD)
inp("std_pkg_offices", "Standard package size", 10, "offices", "planning estimate", P_PRICE)
inp("std_pkg_price", "Standard package price", f"={R('price_std_office')}*{R('std_pkg_offices')}", "USD per brand", "calculated", "Price per office x package offices", fmt=USD, calc=True)
inp("price_fnd_office", "Founding price per office", 120, "USD per office", "planning estimate", P_PRICE,
    "$600 for 5 offices. The plan's summary table once said $600 to $900; the decided price is $600 (low end shown as default).", low=120, high=180, fmt=USD)
inp("fnd_pkg_offices", "Founding package size", 5, "offices", "planning estimate", P_PRICE)
inp("fnd_pkg_price", "Founding package price", f"={R('price_fnd_office')}*{R('fnd_pkg_offices')}", "USD per brand", "calculated", "Price per office x package offices", fmt=USD, calc=True)
inp("extra_office_price", "Extra office beyond the package", 150, "USD per office", "planning estimate", P_PRICE,
    "Applies to offices beyond 5 (founding) or 10 (standard). Founding renewals stay at the founding rate per office for any office count.", fmt=USD)
inp("founding_cap", "Founding tier closes after", 3, "brands", "planning estimate", P_PRICE, "'First three brands only'.")
inp("founding_lock", "Founding price locked for", 2, "further campaigns", "planning estimate", P_PRICE)
inp("fnd_upfront_share", "Founding: share paid before product ships", 1, "share", "planning estimate", P_PRICE, "'Paid in full before product ships'.", fmt=PCT)
inp("fnd_pay_lead_bd", "Founding: payment lands this many business days before the drop", 20, "business days", "derived, founder to confirm",
    CTR3, "Campaign zero's payment at Gate 1 (Fri 2026-12-11) is 20 business days before the Tue 2027-01-12 drop.")
inp("std_deposit_share", "Standard: share invoiced at signature", 0.5, "share", "planning estimate", P_PRICE, "50% at signature, 50% at placement confirmation.", fmt=PCT)
inp("std_sign_lead_bd", "Standard: signature (deposit) this many business days before the drop", 10, "business days", "derived, founder to confirm",
    "plan.md, campaign calendar (brand ships at T-10)", "The latest signature that still lets the brand ship at T-10. Later cash is the conservative reading; the plan proposes drop dates three to four weeks out.")
inp("balance_lag_bd", "Standard: balance invoiced this many business days after the drop", 1, "business days", "derived, founder to confirm",
    "plan.md, What brands buy: placement within one business day", "Placement confirmation at T+1.")
inp("payment_lag_days", "Days from invoice to cash", None, "calendar days", "needs founder decision",
    "Not in the plan", "The plan states no invoice-to-cash lag. Blank = cash lands the day it is invoiced. Enter your invoice terms, for example 15.")
inp("processing_rate", "Card processing rate", 0.03, "share of revenue", "planning estimate", P_ECON, "Card fees. Zero by bank transfer.", fmt=PCT1)
inp("processing_on", "Brands pay by card? 1 = yes, 0 = bank transfer", 1, "toggle", "setting", P_ECON,
    "1 is the high end of the plan's 0% to 3% range and matches its scenario rows. 0 is the plan's preferred invoicing (Wave, bank transfer).", low=0, high=1)

inp_section("4. Drop size defaults (feed the derived Schedule rows) and units")
inp("c0_offices", "Offices on campaign zero", 5, "offices", "planning estimate", "plan.md, scenario table: 'Campaign zero: 2 founding brands, 5 offices'")
inp("c0_brands", "Brands on campaign zero", 2, "brands", "planning estimate", "plan.md, scenario table and Gate 1 ('2 brands paid')")
inp("std_offices_drop", "Offices per standard drop", 10, "offices", "planning estimate", "plan.md, 'Standard runs of 10 offices and 3 brands per drop'")
inp("std_brands_drop", "Brands per standard drop", 3, "brands", "planning estimate", "plan.md, What has to be true #1: 'Three brands per drop'", "Feeds the standard Schedule rows and the plan-base scenario.")
inp("units_per_office", "Units per office per brand", 50, "units", "planning estimate", "plan.md, What brands buy", "Sized to Tuesday headcount (floor 30, ceiling 80).")
inp("reserve_share", "Reserve the brand ships on top", 0.1, "share", "planning estimate", "plan.md, What brands buy", fmt=PCT)

inp_section("5. Hard costs and monthly overhead")
inp("kit_per_office", "Display kit per office per drop (card, allergen line, case label)", 8, "USD per office per drop", "planning estimate", P_ECON,
    "Plan reading (a): per office per drop, not per brand. Only this reproduces the scenario hard costs.", fmt=USD)
inp("card_extra", "Extra tent card per additional brand per office", None, "USD per card", "needs founder decision",
    "plan.md, Hardware: tent cards roughly $1 to $2 each", "Reading (a) keeps one $8 kit per office even on a three-brand drop. If each brand needs its own card, enter $1 to $2.", low=1, high=2, fmt=USD)
inp("founder_transport", "Founder delivery (car rides) per drop", 120, "USD per drop", "planning estimate", P_ECON, "'You delivering costs about $120 in car rides.'", fmt=USD)
inp("courier_per_stop", "Courier per stop", 30, "USD per stop", "planning estimate, needs quote", P_ECON,
    "$300 for a ten-stop route is $30 a stop; plan range $25 to $40. No reliable published rate; get three quotes.", low=25, high=40, fmt=USD)
inp("direct_transport", "Transport when brands ship direct", 0, "USD per drop", "planning estimate", "plan.md, scenario table, direct-ship row",
    "Plan reading (c): the $370 direct-ship row carries $0 transport.", fmt=USD)
inp("kit_mail_per_office", "Mailing the display kit ahead (direct-ship)", None, "USD per office", "needs quote",
    "plan.md, Delivery by phase: '... mails the display kit ahead'", "The plan gives no figure. Blank counts as $0.", fmt=USD)
inp("kit_print_bd", "Kits printed this many business days before the drop", 3, "business days", "planning estimate", "plan.md, campaign calendar: T minus 3")
inp("storage_choice", "Storage", "unit", "list", "setting", P_ECON, "unit = small storage unit; home = sealed cases at home, $0.", vlist="L_storage")
inp("storage_monthly", "Storage unit per month", 150, "USD per month", "planning estimate", P_ECON, "Allocation is half: $75 a drop at two drops a month.", fmt=USD)
inp("storage_start", "Storage unit rented from", D(2027, 2, 1), "date", "derived, founder to confirm", "Plan reading (b)",
    "First day of the first standard drop's month. Campaign zero stays at home, which is how its $280 reproduces.", fmt=DATE)
inp("storage_end", "Storage unit released (blank = keep)", None, "date", "setting", "Plan reading (c)",
    "Blank keeps the unit through the window, as the plan's direct-ship row keeps the $75.", fmt=DATE)
inp("software_monthly", "Software per month", 60, "USD per month", "planning estimate", P_CAP + "; Tools table",
    "$360 for six months. Tools table sums to $7 to $81; the plan caps software under $60.", low=7, high=81, fmt=USD)
inp("software_start", "Software paid from", D(2026, 10, 26), "date", "derived, founder to confirm", "plan.md, Week 1 setup", fmt=DATE)
inp("insurance_monthly", "General liability insurance per month", 100, "USD per month", "planning estimate, needs quote", P_ECON,
    "'Roughly $100 a month'. Capital table range $500 to $1,500 a year, shown here per month.", low=500 / 12, high=125, fmt=USD)
inp("insurance_billing", "Insurance billing", "annual", "list", "setting", P_CAP, "annual = one year's premium paid at bind (capital table 'one year').", vlist="L_insbill")
inp("insurance_bind", "Insurance bound on", D(2026, 12, 11), "date", "derived, founder to confirm", "plan.md, setup checklist: 'At Gate 1 pass: Insurance bound'", fmt=DATE)
inp("phone_monthly", "Phone per month", 0, "USD per month", "planning estimate", "plan.md, Tools: 'Your phone', Google Voice $0", fmt=USD)
inp("alloc_drops_month", "Drops per month used to allocate overhead to a drop", 2, "drops per month", "planning estimate", P_ECON,
    "Insurance $100 a month over two drops = $50; software $60 = $30; storage $150 = $75.")

inp_section("6. Founder hours (rates; the plan's table is reproduced on Plan_Check)")
inp("h_first_brand", "Brand sales per first (founding) brand", 10, "hours per brand", "planning estimate", P_HOURS, "'20 (10 per brand, first ones)'.")
inp("close_rate", "Close rate on qualified brand conversations", 0.2, "share", "planning estimate", "plan.md, What has to be true #2", "One close from five.", fmt=PCT)
inp("h_per_conv", "Hours per qualified conversation", 0.75, "hours", "planning estimate", "plan.md, Economics: 'conversations of 45 minutes'")
inp("h_paperwork", "Proposal and paperwork per win", 2.25, "hours", "derived, founder to confirm", P_HOURS,
    "6 - 5 x 0.75, so the plan's six hours per win reproduces at a 20% close rate.")
inp("h_win", "Brand sales per standard win", f"=1/{R('close_rate')}*{R('h_per_conv')}+{R('h_paperwork')}", "hours per brand", "calculated",
    "Conversations per win x hours each + paperwork", "6.0 at plan inputs. Falls as the close rate rises.", fmt=HRS, calc=True)
inp("h_renewal", "Brand sales per renewal", 2, "hours per renewal", "planning estimate", "plan.md, Economics: 'A renewal takes about two hours'")
inp("h_new_office", "Office recruiting per new office", 4, "hours per office", "planning estimate", P_HOURS, "'20 (4 per new office)'.")
inp("h_existing_office", "Office coordination per existing office", 1, "hours per office", "planning estimate", P_HOURS, "'10 (1 per existing office)'.")
inp("rk_per_brand", "Receiving and kitting per brand", 0.5, "hours per brand", "derived, founder to confirm", P_HOURS, "(4 - 3) / (3 - 1): 1-brand drop 3 h, 3-brand drop 4 h.")
inp("rep_per_brand", "Reporting and debriefs per brand", 2, "hours per brand", "planning estimate", P_HOURS, "'6 (2 per brand)'.")
inp("admin_per_drop", "Admin and invoicing per drop", 2, "hours per drop", "planning estimate", P_HOURS)
inp("discovery_hours_week", "Discovery hours per week, weeks 1 to 3 (not tied to a drop)", 15, "hours per week", "planning estimate",
    "plan.md, Time budget: 'Phases 0 and 1 need 10 to 15 hours a week'", "High end. Weeks 4 to 7 selling and recruiting already sit in campaign zero's 57 hours. Used only in the six-month all-in view.", low=10, high=15)
inp("discovery_weeks", "Discovery weeks", 3, "weeks", "planning estimate", "plan.md, Phase 0 (weeks 1 to 3)")

# delivery-model table
row[0] += 1
section(ws, row[0], "7. Costs and hours that depend on the delivery model")
row[0] += 1
header_row(ws, row[0], 1, ["key", "Delivery model", "Transport per drop (USD)", "Transport per stop (USD)", "Kit mailing per office (USD)",
                           "Receiving and kitting base (h)", "Drop day per office (h)", "Checks and pickup per office (h)", "Derivation from the plan's hour table", "", ""], height=45)
row[0] += 1
m0 = row[0]
mrows = [
    ("founder", f"={R('founder_transport')}", 0, 0, 2.0, 1.0, 0.6,
     "Campaign zero column (2 brands, 5 offices): receiving 3 = 2.0 + 0.5 x 2; drop day 5 h / 5 offices; checks 3 h / 5 offices."),
    ("courier", 0, f"={R('courier_per_stop')}", 0, 2.5, 0.8, 0.4,
     "1-brand and 3-brand columns (10 offices): receiving 3 = 2.5 + 0.5 x 1 and 4 = 2.5 + 0.5 x 3; drop day 8 h / 10; checks 4 h / 10."),
    ("direct-ship", f"={R('direct_transport')}", 0, f"={R('kit_mail_per_office')}", 0.5, 0.3, 0.4,
     "Direct-ship column (3 brands, 10 offices): receiving 2 = 0.5 + 0.5 x 3; drop day 3 h / 10; checks 4 h / 10."),
]
for i, m in enumerate(mrows):
    r = m0 + i
    put(ws, f"A{r}", "model_table", font=F_NOTE)
    put(ws, f"B{r}", m[0], font=F_BOLD)
    for j, v in enumerate(m[1:7]):
        col = CL(3 + j)
        c = put(ws, f"{col}{r}", v, fmt=USD if j < 3 else HRS)
        if isinstance(v, str) and v.startswith("="):
            c.fill = FILL_CALC
            c.border = BOX
        else:
            as_input(c)
            c.number_format = USD if j < 3 else HRS
    put(ws, f"I{r}", m[7], align=WRAP)
row[0] = m0 + 3
REF.update({
    "m_keys": f"Inputs!$B${m0}:$B${m0 + 2}", "m_tr_fixed": f"Inputs!$C${m0}:$C${m0 + 2}", "m_tr_stop": f"Inputs!$D${m0}:$D${m0 + 2}",
    "m_mail": f"Inputs!$E${m0}:$E${m0 + 2}", "m_rk_base": f"Inputs!$F${m0}:$F${m0 + 2}", "m_dd": f"Inputs!$G${m0}:$G${m0 + 2}",
    "m_ck": f"Inputs!$H${m0}:$H${m0 + 2}",
})
MODEL_INPUT_ROWS = (m0, m0 + 2)

inp_section("8. Renewal, steady state and founder capital")
inp("renewal_rate_base", "Brands that renew within 90 days", 0.4, "share", "planning estimate", "plan.md, What has to be true #3",
    "Used by the 'Plan base' scenario. Renewals cost 2 hours instead of 6, which is why they matter more than price.", fmt=PCT)
inp("plan_ss_drops", "Drops per month in the plan's monthly picture", 2, "drops per month", "planning estimate", "plan.md, Monthly picture at steady state")
inp("ss_model", "Steady-state delivery model", "courier", "list", "setting", "Plan reading (e)",
    "The plan's monthly picture is two three-brand courier drops. Direct-ship lifts contribution per hour.", vlist="L_models")
inp("ss_offices", "Steady-state offices per drop", f"={R('std_offices_drop')}", "offices", "calculated", "Offices per standard drop (section 4)", calc=True)
inp("founder_cash", "Cash the founder commits to the first six months", None, "USD", "needs founder decision", "plan.md, What I need from you #7",
    "Blank until you decide. The plan's range is $3,360 to $6,510.", fmt=USD)
inp("founder_cash_date", "Founder cash goes in on", D(2026, 10, 26), "date", "setting", "Model setting", fmt=DATE)
inp("reserve_usd", "Reserve held back (not spent)", 1000, "USD", "planning estimate", P_CAP, fmt=USD)

inp_section("9. Gate thresholds, decision rule and six-month goals")
inp("g0_office_yes", "Gate 0: offices yes in principle", 5, "offices", "planning estimate", "plan.md, Gate 0", "Of 15 conversations, with a pantry owner and receiving window named.")
inp("g0_office_conv", "Gate 0: office conversations planned", 15, "conversations", "planning estimate", "plan.md, Phase 0")
inp("g0_brand_yes", "Gate 0: brands that would pay the threshold and control the budget", 3, "brands", "planning estimate", "plan.md, Gate 0")
inp("g0_brand_usd", "Gate 0: brand willingness-to-pay threshold", 500, "USD per campaign", "planning estimate", "plan.md, Gate 0", fmt=USD)
inp("g0_brand_conv", "Gate 0: brand conversations planned", 15, "conversations", "planning estimate", "plan.md, Phase 0")
inp("g1_offices", "Gate 1: signed offices", 5, "offices", "planning estimate", "plan.md, Gate 1")
inp("g1_headcount", "Gate 1: combined Tuesday headcount of signed offices", 350, "people", "planning estimate", "plan.md, Gate 1")
inp("g1_brands_paid", "Gate 1: brands paid in full", 2, "brands", "planning estimate", "plan.md, Gate 1")
inp("g2_drop_id", "Gate 2: drop tested (campaign zero)", "DRP-001", "drop_id", "setting", "plan.md, Gate 2")
inp("g2_placed", "Gate 2: units placed within one business day", 0.8, "share of delivered", "planning estimate", "plan.md, Gate 2", fmt=PCT)
inp("g2_responses", "Gate 2: survey responses per office", 5, "responses", "planning estimate", "plan.md, Gate 2")
inp("g2_report_bd", "Gate 2: report delivered within", 7, "business days", "planning estimate", "plan.md, Gate 2; CONTRACTS s3 (T+7)")
inp("g2_rebuy", "Gate 2: brands that would buy again", 1, "brands", "planning estimate", "plan.md, Gate 2")
inp("g3_renewals", "Gate 3: renewals at the threshold price", 1, "renewals", "planning estimate", "plan.md, Gate 3")
inp("g3_renewal_usd", "Gate 3: renewal price threshold", 1500, "USD", "planning estimate", "plan.md, Gate 3", fmt=USD)
inp("g3_per_hour", "Gate 3: contribution per founder hour", 50, "USD per hour", "planning estimate", "plan.md, Gate 3", fmt=USD)
inp("dr_scale_renewal", "Decision rule: scale if renewal at least", 0.4, "share", "planning estimate", "plan.md, decision rule", fmt=PCT)
inp("dr_switch_offices", "Decision rule: offices that named the office-paid threshold", 5, "offices", "planning estimate", "plan.md, decision rule")
inp("dr_switch_usd", "Decision rule: office-paid threshold", 100, "USD per month", "planning estimate", "plan.md, decision rule", fmt=USD)
inp("dr_switch_renewal", "Decision rule: switch if renewal under", 0.3, "share", "planning estimate", "plan.md, decision rule", fmt=PCT)
inp("dr_extra_drops", "Decision rule: extra drops before switching", 2, "drops", "planning estimate", "plan.md, decision rule")
inp("sc_c_misses", "Scenario C signal: drops with placement under the threshold", 2, "drops", "planning estimate", "plan.md, scenario C: 'Placement under 80% twice'")
inp("goal_campaigns", "Six-month goal: paid campaigns", 6, "campaigns", "planning estimate", "plan.md, business on one page")
inp("goal_renewals", "Six-month goal: renewals", 2, "renewals", "planning estimate", "plan.md, business on one page")
inp("goal_offices", "Six-month goal: active offices", 12, "offices", "planning estimate", "plan.md, business on one page")

inp_section("10. Sensitivity axes")
inp("sens_price_start", "Price per office: first row", 100, "USD per office", "setting", "Model setting", fmt=USD)
inp("sens_price_step", "Price per office: step", 25, "USD per office", "setting", "Model setting", fmt=USD)
inp("sens_brands_start", "Brands per drop: first column", 1, "brands", "setting", "Model setting")
inp("sens_brands_step", "Brands per drop: step", 1, "brands", "setting", "Model setting")
inp("sens_renew_start", "Renewal rate: first row", 0, "share", "setting", "Model setting", fmt=PCT)
inp("sens_renew_step", "Renewal rate: step", 0.1, "share", "setting", "Model setting", fmt=PCT)

# startup outlays table
row[0] += 1
section(ws, row[0], "11. Startup outlays (one-time, paid at their timing in the cash flow). Formation, publication, licence, professional and filing figures come from the legal pack.", last_col="T")
row[0] += 1
header_row(ws, row[0], 1, ["key", "Item", "Working (USD)", "Unit", "Low", "High", "Status", "Source", "Notes", "Plan default", "Changed",
                           "Timing (date)", "Timing basis", "Include (Y/N)", "Actual paid (USD)", "Actual paid date", "Cash amount used", "Cash date used",
                           "Default include", "Default timing"], height=32)
ws[f"K{row[0]}"].value = "Changed?"
row[0] += 1
su0 = row[0]
G_CSV = "desk-drop-legal-pack/figures.csv (read 2026-10-24)"
startup = [
    # key, item, working, low, high, status, source, notes, timing, timing basis, include
    ("su_llc", "LLC Articles of Organization (state filing fee)", 200, 200, 200, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://dos.ny.gov/limited-liability-company-articles-organization", "Plan capital table: $200 plus $50.",
     D(2026, 11, 13), "Day 0 = first verbal brand yes, expected near Gate 0 (legal pack timing)", "Y"),
    ("su_cert", "Certificate of Publication filing", 50, 50, 50, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://dos.ny.gov/certificate-publication-domestic-limited-liability-company-0", "",
     D(2027, 1, 11), "After the sixth weekly run: order by 2026-11-30, six runs (derived from the legal pack's timing; legal limit day 120)", "Y"),
    ("su_pub", "Newspaper publication (two papers, six weeks), county not chosen", 1745, 200, 2000, "needs quote (legal pack)",
     G_CSV + "; https://www.llcpublishers.com/pricing", "Legal pack working figure = New York County ($1,795 all-in less the $50 state fee). $345 if the attorney confirms Albany County. Plan table: $250 to $2,000.",
     D(2026, 11, 30), "Ordered within 10 business days of filing (legal pack): 2026-11-30", "Y"),
    ("su_license", "Food warehouse license (Article 28-D, two years), if required", 400, 0, 400, "fee verified 2026-10-23; need unknown (legal pack)",
     G_CSV + "; https://www.nysenate.gov/legislation/laws/AGM/500-B", "Zero if the state says sealed cases at home need no license, or if brands ship direct.",
     D(2026, 12, 11), "Before any brand ships (legal pack: latest 2026-12-21); plan: Gate 1", "Y"),
    ("su_print", "Printing and materials (hand truck, supplies, first card runs)", 300, 300, 300, "planning estimate", P_CAP,
     "Read as startup supplies; per-drop kits are the $8 per office line.", D(2026, 12, 11), "Gate 1 pass: hand truck, supplies and first card run (plan setup checklist)", "Y"),
    ("su_domain", "Domain and email setup", 100, 100, 100, "planning estimate", P_CAP, "", D(2026, 10, 26), "Week 1, days 1 and 2 (plan)", "Y"),
    ("su_attorney", "Attorney hour (both agreements, name and formation questions)", 400, 300, 500, "plan estimate (legal pack)",
     G_CSV + "; plan.md Legal table", "Not in the plan's capital table. Plan question 8 puts both hours at about $700.", D(2026, 11, 13), "Booked at Gate 0; held before the first invoice (legal pack)", "Y"),
    ("su_accountant", "Accountant hour (sales tax, UBT, estimates)", 300, 200, 400, "plan estimate (legal pack)",
     G_CSV + "; plan.md Legal table", "Not in the plan's capital table.", D(2026, 11, 13), "Booked at Gate 0; held before the first invoice (legal pack)", "Y"),
    ("su_it204", "NYS LLC annual filing fee (IT-204-LL), single-member", 25, 25, 25, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://www.tax.ny.gov/pdf/current_forms/it/it204lli.pdf", "Accountant confirms whether 2026 is owed. Not in the plan.", D(2027, 3, 15), "First possibly Mon 2027-03-15 for 2026 (legal pack)", "Y"),
    ("su_hnoa", "Hired and non-owned auto add-on to the liability policy", None, None, None, "needs quote (legal pack)",
     G_CSV + "; plan.md Legal table ('Small add-on. Ask the carrier.')", "Needed if car rides, a car service or a rented van carry product (campaign zero does). Blank counts as $0.",
     D(2026, 12, 11), "With the general liability bind", "Y"),
    ("su_addl_insured", "Additional-insured endorsements for buildings that require them", None, None, None, "needs quote (legal pack)",
     G_CSV, "Zero if the policy has a blanket additional-insured endorsement. Blank counts as $0.", D(2026, 12, 11), "Before each such building's first drop", "Y"),
    ("su_tm", "Federal trademark application (one class)", 350, 350, 850, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule",
     "Excluded from the six months (Include = N): the legal pack times it after campaign zero passes and outside the first six months, and USPTO refused a prior DESK-DROP filing as descriptive. Set Y to include it at Gate 2.",
     D(2027, 1, 22), "Only after campaign zero passes; attorney advises first (legal pack)", "N"),
]
for i, s in enumerate(startup):
    r = su0 + i
    key, item, working, low, high, status, src, notes, tdate, tbasis, incl = s
    put(ws, f"A{r}", key, font=F_NOTE)
    put(ws, f"B{r}", item, align=WRAP)
    as_input(put(ws, f"C{r}", working))
    ws[f"C{r}"].number_format = USD
    put(ws, f"D{r}", "USD one-time")
    put(ws, f"E{r}", low, fmt=USD)
    put(ws, f"F{r}", high, fmt=USD)
    put(ws, f"G{r}", status)
    put(ws, f"H{r}", src, align=WRAP)
    put(ws, f"I{r}", notes, align=WRAP)
    put(ws, f"J{r}", working, fmt=USD, font=F_NOTE)
    put(ws, f"K{r}", f'=IF(AND(C{r}&""=J{r}&"",N{r}&""=S{r}&"",L{r}&""=T{r}&""),"","changed")', font=Font(color="9C0006", bold=True))
    put(ws, f"S{r}", incl, font=F_NOTE)
    put(ws, f"T{r}", tdate, fmt=DATE, font=F_NOTE)
    CHANGED_CELLS.append(f"K{r}")
    as_input(put(ws, f"L{r}", tdate))
    ws[f"L{r}"].number_format = DATE
    put(ws, f"M{r}", tbasis, align=WRAP)
    as_input(put(ws, f"N{r}", incl))
    as_input(put(ws, f"O{r}", None))
    ws[f"O{r}"].number_format = USD
    as_input(put(ws, f"P{r}", None))
    ws[f"P{r}"].number_format = DATE
    put(ws, f"Q{r}", f'=IF(P{r}<>"",N(O{r}),IF(N{r}="Y",N(C{r}),0))', fmt=USD, fill=FILL_CALC)
    put(ws, f"R{r}", f'=IF(P{r}<>"",P{r},L{r})', fmt=DATE, fill=FILL_CALC)
    REF[key] = f"Inputs!$C${r}"
    REF[key + "_cash"] = f"Inputs!$Q${r}"
sun = su0 + len(startup) - 1
add_list_validation(ws, f"N{su0}:N{sun}", "=" + R("L_yn"))
REF["su_amt"] = f"Inputs!$Q${su0}:$Q${sun}"
REF["su_date"] = f"Inputs!$R${su0}:$R${sun}"
REF["su_working"] = f"Inputs!$C${su0}:$C${sun}"
r = sun + 1
put(ws, f"B{r}", "Total startup outlays (cash amounts used)", font=F_BOLD)
put(ws, f"Q{r}", f"=SUM(Q{su0}:Q{sun})", fmt=USD, font=F_BOLD)
REF["su_total"] = f"Inputs!$Q${r}"
r += 2
put(ws, f"B{r}", "Inputs changed from plan defaults", font=F_BOLD)
put(ws, f"C{r}", f'=COUNTIF(K5:K{sun},"changed")+COUNTIF(Scenarios!$Q$10:$Q$21,"changed")', fmt=INT, font=F_BOLD)
put(ws, f"D{r}", "cells here and on Scenarios (the delivery-model rates in section 7 are not flagged; Plan_Check shows whether they still reproduce the plan)", font=F_NOTE)
REF["changed_count"] = f"Inputs!$C${r}"
widths(ws, {"A": 18, "B": 50, "C": 15, "D": 18, "E": 10, "F": 10, "G": 25, "H": 44, "I": 60, "J": 12, "K": 9,
            "L": 12, "M": 40, "N": 9, "O": 12, "P": 12, "Q": 12, "R": 12, "S": 9, "T": 12})
ws.freeze_panes = "C5"

# ==========================================================================
# Scenarios
# ==========================================================================
ws = WS["Scenarios"]
title(ws, "Scenarios A to D", "The plan's four decision situations as assumption sets. Pick one on Inputs ('Scenario in force'). The Active column feeds drops after Gate 3 and the steady state.")
banner(ws, "A3", "Planning estimates. Where a scenario does not name a figure, it uses the plan base and says so. Nothing here is a forecast of which scenario will happen.", "J3")
header_row(ws, 5, 2, ["Lever", "Plan base", "A", "B", "C", "D", "Active (in force)", "Unit", "Source and reading"], height=30)
put(ws, "B6", "Situation", font=F_BOLD)
for col, t in zip("CDEFG", ["What has to be true", "Both sides work", "Brands pay once, offices love it", "Brands willing, offices unreliable", "Neither converts"]):
    put(ws, f"{col}6", t, align=WRAP, font=F_BOLD)
put(ws, "B7", "What the numbers show", font=F_BOLD)
for col, t in zip("CDEFG", [
        "Three brands per drop, six hours or less per win, 40% renew, $1,500 holds",
        "40% or more of brands renew; placement above 80%; contribution above $50 an hour",
        "Renewal under 30%; offices asking when the next drop is",
        "Placement under 80% twice; photos missing; responses under five",
        "No renewal, weak placement"]):
    put(ws, f"{col}7", t, align=WRAP)
put(ws, "B8", "What to do next (plan)", font=F_BOLD)
for col, t in zip("CDEFG", [
        "Run the plan",
        "Scale: second cluster, roster 20 to 30, price to $1,800 to $2,000, part-time delivery at about $25 an hour above two drops a month, launch-partner tier",
        "Fix the evidence, run two more drops; if renewal is still under 30%, switch to office-paid for offices that named $100 a month or more",
        "Replace the weakest offices, raise the commitment bar; if a third drop misses, stop",
        "Stop; write the post-mortem; keep office relationships warm"]):
    put(ws, f"{col}8", t, align=WRAP)
for rr, h in ((6, 32), (7, 62), (8, 92)):
    ws.row_dimensions[rr].height = h
levers = [
    ("sc_runs", "Post-Gate-3 drops that run in the six months (of the two scheduled)", [2, 2, 2, 1, 0], "drops", INT,
     "Base and A: two drops a month. B: 'run two more drops'. C: 'if a third drop misses, stop', so one more. D: 'Stop'."),
    ("sc_brands", "Brands per drop after Gate 3", [f"={R('std_brands_drop')}", 3, 3, 3, 0], "brands", INT, "Plan: three brands per drop. D stops."),
    ("sc_renewal", "Renewal rate (share of brand slots that are renewals)", [f"={R('renewal_rate_base')}", 0.4, 0, "=C{self}", 0], "share", PCT,
     "A: '40% or more', low end. B: 'under 30%' and 'brands pay once': 0%, the low end of 0% to 29%. C: not named, plan base. D: 'No renewal'."),
    ("sc_new_offices", "New offices recruited per post-Gate-3 drop", [0, 0, 0, None, 0], "offices", INT,
     "C: 'replace the weakest offices'; the plan gives no count. Blank = 0; founder to set."),
    ("sc_price_after", "Standard price per office for drops after the decision date", [f"={R('price_std_office')}", 180, f"={R('price_std_office')}", f"={R('price_std_office')}", f"={R('price_std_office')}"], "USD per office", USD,
     "A: 'raise the standard price to $1,800 to $2,000' = $180 to $200 per office; low end."),
    ("sc_ss_drops", "Steady-state drops per month", [f"={R('plan_ss_drops')}", 2, 2, 2, 0], "drops per month", INT, "Plan monthly picture: two drops a month."),
    ("sc_ss_brands", "Steady-state brands per drop", [f"={R('std_brands_drop')}", 3, 3, 3, 0], "brands", INT, "Plan monthly picture: three-brand drops."),
    ("sc_op_offices", "Offices on an office-paid tier (steady state)", [0, 0, 5, 0, 0], "offices", INT, "B: offices that named $100 a month or more; at least five."),
    ("sc_op_fee", "Office-paid fee per office per month", [None, None, 100, None, None], "USD per month", USD, "B: $100 to $200 a month; low end."),
    ("sc_op_cost", "Cost to serve one office-paid office per month", [None, None, None, None, None], "USD per month", USD,
     "Needs quote. The plan prices no cost for guaranteed twice-monthly curated drops."),
    ("sc_hire_rate", "Part-time delivery hire", [25, 25, None, None, None], "USD per hour", USD,
     "A: 'about $25 an hour once you run more than two drops a month'. It replaces drop-day hours (model reading)."),
    ("sc_hire_threshold", "Hire once steady-state drops per month exceed", [2, 2, 2, 2, 2], "drops per month", INT, "Plan: 'more than two drops a month'."),
]
for i, (key, lab, vals, unit, fmt, note) in enumerate(levers):
    r = 10 + i
    put(ws, f"B{r}", lab, align=WRAP)
    for j, v in enumerate(vals):
        if isinstance(v, str):
            v = v.replace("{self}", str(r))
        c = put(ws, f"{CL(3 + j)}{r}", v, fmt=fmt)
        as_input(c)
        c.number_format = fmt
    put(ws, f"H{r}", f"=INDEX(C{r}:G{r},MATCH({R('active_scenario')},$C$5:$G$5,0))", fmt=fmt, font=F_BOLD, fill=FILL_KEY, border=BOX)
    for j, v in enumerate(vals):
        if isinstance(v, str):
            v = v.replace("{self}", str(r))
        put(ws, f"{CL(12 + j)}{r}", v, fmt=fmt, font=F_NOTE)
    put(ws, f"Q{r}", "=IF(AND(" + ",".join(f'{CL(3 + j)}{r}&""={CL(12 + j)}{r}&""' for j in range(5)) + '),"","changed")', font=Font(color="9C0006", bold=True))
    put(ws, f"I{r}", unit)
    put(ws, f"J{r}", note, align=WRAP)
    ws.row_dimensions[r].height = 30
    REF[key] = f"Scenarios!$H${r}"
header_row(ws, 5, 12, ["default: Plan base", "default: A", "default: B", "default: C", "default: D", "Changed?"], height=30)
REF["scen_changed"] = "Scenarios!$Q$10:$Q$21"
put(ws, "B23", "How it works", font=F_BOLD)
put(ws, "B24", "The two decision-window drops on Schedule (DRP-004, DRP-005) take brands, renewals and new offices from the Active column. "
              "Type over those Schedule cells to replace the scenario with real plans. The steady-state view and the sensitivity tables use the Active column too. "
              "Drops before Gate 3 do not change with the scenario.", align=WRAP)
ws.merge_cells("B24:J24")
ws.row_dimensions[24].height = 48
widths(ws, {"A": 3, "B": 46, "C": 18, "D": 22, "E": 22, "F": 22, "G": 18, "H": 14, "I": 14, "J": 60, "K": 3, "L": 11, "M": 11, "N": 11, "O": 11, "P": 11, "Q": 10})
ws.freeze_panes = "C6"

# ==========================================================================
# Schedule
# ==========================================================================
ws = WS["Schedule"]
title(ws, "Drop schedule", "One row per drop. Edit dates, delivery model, offices, brands and renewals. Rows marked derived are the simplest schedule that meets the plan; founder to confirm.")
banner(ws, "A3", "Drop days are Tuesday or Wednesday only; no window may overlap a blackout (Lists). Set 'Actuals in' to Y once a drop's actuals are pasted, and the model switches that drop from plan to actual.", "T3")
SCH_HDR = ["drop_id", "Label", "Basis", "Post-Gate-3 sequence", "Drop date", "Day", "Delivery model", "Tier", "Offices", "New offices",
           "Brands", "of which renewals", "of which founding-rate renewals", "Actuals in (Y/N)", "Notes",
           "Tue or Wed?", "Window closes (T+4)", "Blackout clash?", "Units brands ship (incl. reserve)", "Row check",
           "Office slots on drops in the last four weeks", "Roster to date (new offices so far)", "Office fatigue", "Changed from the derived default?"]
header_row(ws, 6, 1, SCH_HDR, height=45)
sched = [
    ("DRP-001", "Campaign zero (founding)", "derived: CONTRACTS s3", None, D(2027, 1, 12), "founder", "founding", "=" + R("c0_offices"), "=I7", "=" + R("c0_brands"), 0, 0,
     "Stretch option Tue 2026-12-08 only if both brands pay by 2026-11-20. Brands asked to ship by 2026-12-22."),
    ("DRP-002", "Standard run 1", "derived: CONTRACTS s3", None, D(2027, 2, 9), "courier", "standard", "=" + R("std_offices_drop"), "=MAX(0,I8-SUM(J$7:J7))", "=" + R("std_brands_drop"), 0, 0,
     "Campaigns one and two: founder plus courier (plan). New offices fill the drop: five take the roster from 5 to 10."),
    ("DRP-003", "Standard run 2", "derived: CONTRACTS s3", None, D(2027, 2, 23), "courier", "standard", "=" + R("std_offices_drop"), "=MAX(0,MIN(I9," + R("goal_offices") + "-SUM(J$7:J8)))", "=" + R("std_brands_drop"), 0, 0,
     "New offices reach the six-month goal of 12 active offices (two). Two weeks after run 1, so most offices get two drops in February."),
    ("DRP-004", "Decision window drop 1", "derived: scenario", 1, D(2027, 3, 23), "direct-ship", "standard", "=" + R("std_offices_drop"), "sc", "sc", "sc", 0,
     "Campaign three onward: brands ship direct (plan). Brands, renewals and new offices follow the scenario in force."),
    ("DRP-005", "Decision window drop 2", "derived: scenario", 2, D(2027, 4, 6), "direct-ship", "standard", "=" + R("std_offices_drop"), "sc", "sc", "sc", 0,
     "Second extra drop before the decision (scenario B's 'two more drops'; two drops a month in the base)."),
]
for i in range(N_DROPS):
    r = DROP0 + i
    if i < len(sched):
        s = sched[i]
        vals = {"A": s[0], "B": s[1], "C": s[2], "D": s[3], "E": s[4], "G": s[5], "H": s[6], "I": s[7], "J": s[8], "K": s[9], "L": s[10], "M": s[11], "N": "N", "O": s[12]}
    else:
        vals = {"A": f"DRP-{i + 1:03d}", "B": None, "C": "founder entry", "D": None, "E": None, "G": None, "H": None, "I": None, "J": None, "K": None, "L": None, "M": None, "N": "N", "O": None}
    if vals["K"] == "sc":
        vals["K"] = f"=IF(D{r}<={R('sc_runs')},{R('sc_brands')},0)"
        vals["L"] = f"=ROUND({R('sc_renewal')}*K{r},0)"
        vals["J"] = f"=IF(K{r}>0,N({R('sc_new_offices')}),0)"
    for col, v in vals.items():
        c = put(ws, f"{col}{r}", v)
        if col in "ABCDEGHIJKLMNO":
            as_input(c)
            if isinstance(v, str) and v.startswith("="):
                c.fill = FILL_SCEN
        if col == "E":
            c.number_format = DATE
        if col == "O":
            c.alignment = WRAP
    put(ws, f"F{r}", f'=IF(E{r}="","",TEXT(E{r},"ddd"))')
    put(ws, f"P{r}", f'=IF(E{r}="","",IF(OR(WEEKDAY(E{r})={R("wd_tue")},WEEKDAY(E{r})={R("wd_wed")}),"ok","not Tue/Wed"))')
    put(ws, f"Q{r}", f'=IF(E{r}="","",WORKDAY(E{r},{R("window_bd")}-1,{R("holidays")}))', fmt=DDATE)
    put(ws, f"R{r}", f'=IF(E{r}="","",IF(COUNTIFS({R("bo_start")},"<="&Q{r},{R("bo_end")},">="&E{r})>0,"clash","ok"))')
    put(ws, f"S{r}", f'=IF(E{r}="","",N(K{r})*N(I{r})*{R("units_per_office")}*(1+{R("reserve_share")}))', fmt='#,##0')
    put(ws, f"T{r}", f'=IF(E{r}="",IF(N(K{r})>0,"date missing",""),IF(AND(P{r}="ok",R{r}="ok",N(J{r})<=N(I{r}),N(L{r})<=N(K{r}),N(M{r})<=N(L{r}),OR(N(K{r})=0,N(I{r})>0),G{r}<>"",H{r}<>""),"ok","check"))')
    # office fatigue and change tracking
    put(ws, f"U{r}", f'=IF(OR(E{r}="",N(K{r})=0),"",SUMIFS($I${DROP0}:$I${DROPN},$E${DROP0}:$E${DROPN},">"&E{r}-{R("office_window_days")},$E${DROP0}:$E${DROPN},"<="&E{r},$K${DROP0}:$K${DROPN},">0"))')
    put(ws, f"V{r}", f'=IF(E{r}="","",SUMIFS($J${DROP0}:$J${DROPN},$E${DROP0}:$E${DROPN},"<="&E{r}))')
    put(ws, f"W{r}", f'=IF(U{r}="","",IF(U{r}>V{r},"some offices get a second drop within four weeks","ok"))', align=WRAP)
    dcols = "EGHIJKLM"
    for j, col in enumerate(dcols):
        dv = vals.get(col)
        put(ws, f"{CL(27 + j)}{r}", dv, fmt=DATE if col == "E" else None, font=F_NOTE)
    put(ws, f"X{r}", "=IF(AND(" + ",".join(f'{col}{r}&""={CL(27 + j)}{r}&""' for j, col in enumerate(dcols)) + '),"","changed")', font=Font(color="9C0006", bold=True))
    ws.row_dimensions[r].height = 42
    for col in [CL(k) for k in range(1, 25)]:
        ws[f"{col}{r}"].alignment = Alignment(vertical="top", wrap_text=True)
add_list_validation(ws, f"G{DROP0}:G{DROPN}", "=" + R("L_models"))
add_list_validation(ws, f"H{DROP0}:H{DROPN}", "=" + R("L_tiers"))
add_list_validation(ws, f"N{DROP0}:N{DROPN}", "=" + R("L_yn"))
ok_cf(ws, f"P{DROP0}:P{DROPN}", bad=['"not Tue/Wed"'])
ok_cf(ws, f"R{DROP0}:R{DROPN}", bad=['"clash"'])
ok_cf(ws, f"T{DROP0}:T{DROPN}", bad=['"check"', '"date missing"'])
ok_cf(ws, f"W{DROP0}:W{DROPN}")
ws.conditional_formatting.add(f"W{DROP0}:W{DROPN}", FormulaRule(formula=[f'LEFT(W{DROP0},LEN("some"))="some"'], fill=PatternFill("solid", fgColor="FCE4D6")))
header_row(ws, 6, 27, ["default date", "default model", "default tier", "default offices", "default new offices", "default brands", "default renewals", "default founding renewals"], height=45)
put(ws, "AA5", "Derived defaults (for the 'Changed' flag; do not edit)", font=F_NOTE)
put(ws, "A4", "Yellow = your input. Blue = follows Inputs or the scenario in force; type over it to replace. Red 'changed' = the row no longer matches the derived default.", font=F_NOTE)
REF["sched_fatigue"] = f"Schedule!$W${DROP0}:$W${DROPN}"
REF["sched_changed"] = f"Schedule!$X${DROP0}:$X${DROPN}"
r = DROPN + 1
put(ws, f"B{r}", "Totals", font=F_BOLD)
for col in "IJKLM":
    put(ws, f"{col}{r}", f"=SUM({col}{DROP0}:{col}{DROPN})", font=F_BOLD)
put(ws, f"S{r}", f"=SUM(S{DROP0}:S{DROPN})", fmt='#,##0', font=F_BOLD)
put(ws, f"B{r + 2}", "Offices column counts every office on the drop; New offices counts the ones visiting for the first time (4 hours each instead of 1). "
                     "Brands counts brand campaigns on the drop; renewals are part of that count (2 hours each instead of 6 or 10). "
                     "Tier sets the price of the new brands; founding-rate renewals pay the founding rate per office.", align=WRAP)
ws.merge_cells(f"B{r + 2}:O{r + 2}")
ws.row_dimensions[r + 2].height = 45
REF.update({"sched_ids": f"Schedule!$A${DROP0}:$A${DROPN}", "sched_actuals": f"Schedule!$N${DROP0}:$N${DROPN}",
            "sched_check": f"Schedule!$T${DROP0}:$T${DROPN}", "sched_dates": f"Schedule!$E${DROP0}:$E${DROPN}"})
widths(ws, {"A": 10, "B": 24, "C": 20, "D": 10, "E": 12, "F": 6, "G": 12, "H": 10, "I": 8, "J": 8, "K": 8, "L": 10, "M": 12,
            "N": 9, "O": 50, "P": 11, "Q": 15, "R": 10, "S": 12, "T": 10, "U": 12, "V": 12, "W": 24, "X": 12})
ws.freeze_panes = "C7"

# ==========================================================================
# Engine (shared column layout on Drop_PnL, Plan_Check, Calculator, Steady_State, Sensitivity)
# ==========================================================================
ENGINE = [
    # key, header, fmt
    ("id", "Drop or case", None), ("date", "Drop date", DATE), ("model", "Delivery model", None), ("tier", "Tier", None),
    ("offices", "Offices", INT), ("new_offices", "New offices", INT), ("brands", "Brands", None), ("renewals", "of which renewals", None),
    ("fnd_renewals", "of which founding-rate renewals", None), ("price_std", "Standard price per office", USD), ("price_fnd", "Founding price per office", USD),
    ("storage_on", "Storage allocated (1/0)", INT), ("proc_on", "Card processing (1/0)", INT),
    ("run", "Drop runs (1/0)", INT), ("new_fnd", "New founding brands", None), ("new_std", "New standard brands", None),
    ("rev_fnd", "Revenue at founding rate", USD), ("rev_std", "Revenue at standard rate", USD), ("revenue", "Revenue", USD),
    ("kit", "Display kits", USD), ("transport", "Transport", USD), ("kit_mail", "Kit mailing", USD), ("processing", "Card processing", USD),
    ("storage_alloc", "Storage allocation", USD), ("software_alloc", "Software allocation", USD), ("insurance_alloc", "Insurance allocation", USD),
    ("hard_costs", "Hard costs", USD),
    ("h_brand_sales", "brand_sales (h)", HRS), ("h_office", "office_coordination (h)", HRS), ("h_receiving", "receiving_kitting (h)", HRS),
    ("h_drop_day", "drop_day (h)", HRS), ("h_checks", "checks_pickup (h)", HRS), ("h_reporting", "reporting_debriefs (h)", HRS),
    ("h_admin", "admin_invoicing (h)", HRS), ("hours", "Founder hours", HRS),
    ("contribution", "Contribution", USD), ("per_hour", "Contribution per founder hour", PH),
    ("direct_costs", "Direct costs (kits, transport, mailing, processing)", USD), ("allocations", "Overhead allocations (views of monthly costs)", USD),
]
EC = {k: CL(i + 1) for i, (k, _, _) in enumerate(ENGINE)}
EFMT = {k: f for k, _, f in ENGINE}
ENGINE_INPUT_KEYS = [k for k, _, _ in ENGINE[:13]]
LAST_ENGINE_COL = EC["allocations"]   # AM


def eng_formulas(r):
    c = lambda n: f"{EC[n]}{r}"
    idx = lambda rng: f"INDEX({R(rng)},MATCH({c('model')},{R('m_keys')},0))"
    F = {
        "run": f"=IF({c('brands')}>0,1,0)",
        "new_fnd": f'=IF({c("tier")}="founding",{c("brands")}-{c("renewals")},0)',
        "new_std": f'=IF({c("tier")}="standard",{c("brands")}-{c("renewals")},0)',
        "rev_fnd": (f"={c('new_fnd')}*({c('price_fnd')}*MIN({c('offices')},{R('fnd_pkg_offices')})"
                    f"+{R('extra_office_price')}*MAX({c('offices')}-{R('fnd_pkg_offices')},0))"
                    f"+{c('fnd_renewals')}*{c('price_fnd')}*{c('offices')}"),
        "rev_std": (f"=({c('new_std')}+{c('renewals')}-{c('fnd_renewals')})*({c('price_std')}*MIN({c('offices')},{R('std_pkg_offices')})"
                    f"+{R('extra_office_price')}*MAX({c('offices')}-{R('std_pkg_offices')},0))"),
        "revenue": f"={c('rev_fnd')}+{c('rev_std')}",
        "kit": f"={c('run')}*{c('offices')}*({R('kit_per_office')}+{R('card_extra')}*MAX({c('brands')}-1,0))",
        "transport": f"=IF({c('run')}=0,0,{idx('m_tr_fixed')}+{idx('m_tr_stop')}*{c('offices')})",
        "kit_mail": f"=IF({c('run')}=0,0,{idx('m_mail')}*{c('offices')})",
        "processing": f"={c('revenue')}*{R('processing_rate')}*{c('proc_on')}",
        "storage_alloc": f"={c('run')}*{c('storage_on')}*{R('storage_monthly')}/{R('alloc_drops_month')}",
        "software_alloc": f"={c('run')}*{R('software_monthly')}/{R('alloc_drops_month')}",
        "insurance_alloc": f"={c('run')}*{R('insurance_monthly')}/{R('alloc_drops_month')}",
        "hard_costs": f"=SUM({c('kit')}:{c('insurance_alloc')})",
        "h_brand_sales": f"={c('new_fnd')}*{R('h_first_brand')}+{c('new_std')}*{R('h_win')}+{c('renewals')}*{R('h_renewal')}",
        "h_office": f"={c('run')}*({c('new_offices')}*{R('h_new_office')}+({c('offices')}-{c('new_offices')})*{R('h_existing_office')})",
        "h_receiving": f"=IF({c('run')}=0,0,{idx('m_rk_base')}+{R('rk_per_brand')}*{c('brands')})",
        "h_drop_day": f"=IF({c('run')}=0,0,{idx('m_dd')}*{c('offices')})",
        "h_checks": f"=IF({c('run')}=0,0,{idx('m_ck')}*{c('offices')})",
        "h_reporting": f"={R('rep_per_brand')}*{c('brands')}",
        "h_admin": f"={c('run')}*{R('admin_per_drop')}",
        "hours": f"=SUM({c('h_brand_sales')}:{c('h_admin')})",
        "contribution": f"={c('revenue')}-{c('hard_costs')}",
        "per_hour": f'=IF({c("hours")}>0,{c("contribution")}/{c("hours")},"n/a")',
        "direct_costs": f"={c('kit')}+{c('transport')}+{c('kit_mail')}+{c('processing')}",
        "allocations": f"={c('storage_alloc')}+{c('software_alloc')}+{c('insurance_alloc')}",
    }
    return F


def write_engine_header(ws, row, band_row=None):
    for i, (k, h, _) in enumerate(ENGINE):
        put(ws, f"{CL(i + 1)}{row}", h, font=F_H, fill=FILL_H, align=CENTER, border=BOX)
    ws.row_dimensions[row].height = 58
    if band_row:
        bands = [("id", "model", "Case"), ("offices", "proc_on", "Inputs to the engine"), ("run", "revenue", "Revenue"),
                 ("kit", "hard_costs", "Hard costs"), ("h_brand_sales", "hours", "Founder hours by activity"),
                 ("contribution", "per_hour", "Result"), ("direct_costs", "allocations", "Split")]
        for a, b, lab in bands:
            ws.merge_cells(f"{EC[a]}{band_row}:{EC[b]}{band_row}")
            put(ws, f"{EC[a]}{band_row}", lab, font=F_BOLD, fill=FILL_SEC, align=CENTER)


def write_engine_row(ws, r, inputs, input_style=False):
    """inputs: dict key -> value/formula for the 13 engine input columns."""
    for k in ENGINE_INPUT_KEYS:
        v = inputs.get(k)
        c = put(ws, f"{EC[k]}{r}", v, fmt=EFMT[k])
        if input_style and not (isinstance(v, str) and v.startswith("=")):
            as_input(c)
            if EFMT[k]:
                c.number_format = EFMT[k]
    for k, f in eng_formulas(r).items():
        c = put(ws, f"{EC[k]}{r}", f, fmt=EFMT[k])
        if k in ("revenue", "hard_costs", "hours", "contribution", "per_hour"):
            c.font = F_BOLD


def engine_widths(ws):
    for i, (k, _, _) in enumerate(ENGINE):
        ws.column_dimensions[CL(i + 1)].width = 11
    ws.column_dimensions["A"].width = 40


# ==========================================================================
# Drop_PnL
# ==========================================================================
ws = WS["Drop_PnL"]
title(ws, "Per-drop P&L (plan basis) with cash timing", "One row per Schedule row. Contribution = revenue minus hard costs, as the plan defines it. Overhead allocations are views; the cash flow pays overhead once.")
banner(ws, "A3", "Planning estimates. The 'Live' columns switch to actuals when Schedule says 'Actuals in = Y'. Shared drop costs are split equally across the drop's brands where a per-brand figure is shown.", "AM3")
write_engine_header(ws, 6, band_row=5)
CT = {}  # cash timing columns
ct_cols = [("pay_fnd_date", "Founding payment date", DATE), ("pay_fnd_amt", "Founding payment", USD),
           ("pay_dep_date", "Standard deposit date", DATE), ("pay_dep_amt", "Standard deposit", USD),
           ("pay_bal_date", "Balance date", DATE), ("pay_bal_amt", "Balance", USD),
           ("proc_fnd", "Processing on founding payment", USD), ("proc_dep", "Processing on deposit", USD), ("proc_bal", "Processing on balance", USD),
           ("kit_date", "Kits printed (and mailed)", DATE), ("tr_date", "Transport paid", DATE), ("actuals_in", "Actuals in", None),
           ("live_rev", "Live revenue", USD), ("live_cost", "Live hard costs", USD), ("live_hours", "Live founder hours", HRS),
           ("live_contrib", "Live contribution", USD), ("live_ph", "Live contribution per founder hour", PH), ("basis", "Basis", None),
           ("next_flag", "Upcoming drop (1/0)", INT)]
start = openpyxl.utils.column_index_from_string(LAST_ENGINE_COL) + 2   # AO
for i, (k, h, f) in enumerate(ct_cols):
    CT[k] = CL(start + i)
    put(ws, f"{CT[k]}6", h, font=F_H, fill=FILL_H, align=CENTER, border=BOX)
ws.merge_cells(f"{CT['pay_fnd_date']}5:{CT['tr_date']}5")
put(ws, f"{CT['pay_fnd_date']}5", "Cash timing on the plan's terms (feeds Cash_Flow)", font=F_BOLD, fill=FILL_SEC, align=CENTER)
ws.merge_cells(f"{CT['actuals_in']}5:{CT['next_flag']}5")
put(ws, f"{CT['actuals_in']}5", "Live: actual where Actuals in = Y, otherwise plan", font=F_BOLD, fill=FILL_SEC, align=CENTER)
for i in range(N_DROPS):
    r = DROP0 + i
    s = DROP0 + i  # schedule row
    ins = {
        "id": f"=Schedule!A{s}",
        "date": f'=IF(Schedule!E{s}="","",Schedule!E{s})',
        "model": f'=IF(Schedule!G{s}="","",Schedule!G{s})',
        "tier": f'=IF(Schedule!H{s}="","",Schedule!H{s})',
        "offices": f"=N(Schedule!I{s})", "new_offices": f"=N(Schedule!J{s})", "brands": f"=N(Schedule!K{s})",
        "renewals": f"=N(Schedule!L{s})", "fnd_renewals": f"=N(Schedule!M{s})",
        "price_std": f'=IF(AND(B{r}<>"",B{r}>{R("decision_date")}),{R("sc_price_after")},{R("price_std_office")})',
        "price_fnd": f"={R('price_fnd_office')}",
        "storage_on": f'=IF(AND({R("storage_choice")}="unit",B{r}<>"",B{r}>={R("storage_start")},OR({R("storage_end")}="",B{r}<={R("storage_end")})),1,0)',
        "proc_on": f"={R('processing_on')}",
    }
    write_engine_row(ws, r, ins)
    lag = f"N({R('payment_lag_days')})"
    run = f"{EC['run']}{r}"
    ws[f"{CT['pay_fnd_date']}{r}"] = f'=IF(OR({run}=0,{CT["pay_fnd_amt"]}{r}=0),"",WORKDAY(B{r},-{R("fnd_pay_lead_bd")},{R("holidays")})+{lag})'
    ws[f"{CT['pay_fnd_amt']}{r}"] = f"={EC['rev_fnd']}{r}*{R('fnd_upfront_share')}"
    ws[f"{CT['pay_dep_date']}{r}"] = f'=IF(OR({run}=0,{CT["pay_dep_amt"]}{r}=0),"",WORKDAY(B{r},-{R("std_sign_lead_bd")},{R("holidays")})+{lag})'
    ws[f"{CT['pay_dep_amt']}{r}"] = f"={EC['rev_std']}{r}*{R('std_deposit_share')}"
    ws[f"{CT['pay_bal_date']}{r}"] = f'=IF(OR({run}=0,{CT["pay_bal_amt"]}{r}=0),"",WORKDAY(B{r},{R("balance_lag_bd")},{R("holidays")})+{lag})'
    ws[f"{CT['pay_bal_amt']}{r}"] = f"={EC['rev_fnd']}{r}*(1-{R('fnd_upfront_share')})+{EC['rev_std']}{r}*(1-{R('std_deposit_share')})"
    for a, b in (("proc_fnd", "pay_fnd_amt"), ("proc_dep", "pay_dep_amt"), ("proc_bal", "pay_bal_amt")):
        ws[f"{CT[a]}{r}"] = f"={CT[b]}{r}*{R('processing_rate')}*{EC['proc_on']}{r}"
    ws[f"{CT['kit_date']}{r}"] = f'=IF({run}=0,"",WORKDAY(B{r},-{R("kit_print_bd")},{R("holidays")}))'
    ws[f"{CT['tr_date']}{r}"] = f'=IF({run}=0,"",B{r})'
    ws[f"{CT['actuals_in']}{r}"] = f'=IF(Schedule!N{s}="Y","Y","N")'
    ai = f"{CT['actuals_in']}{r}"
    ws[f"{CT['live_rev']}{r}"] = f'=IF({ai}="Y",Drop_Actuals!D{r},{EC["revenue"]}{r})'
    ws[f"{CT['live_cost']}{r}"] = f'=IF({ai}="Y",Drop_Actuals!J{r},{EC["hard_costs"]}{r})'
    ws[f"{CT['live_hours']}{r}"] = f'=IF({ai}="Y",Drop_Actuals!R{r},{EC["hours"]}{r})'
    ws[f"{CT['live_contrib']}{r}"] = f"={CT['live_rev']}{r}-{CT['live_cost']}{r}"
    ws[f"{CT['live_ph']}{r}"] = f'=IF({CT["live_hours"]}{r}>0,{CT["live_contrib"]}{r}/{CT["live_hours"]}{r},"n/a")'
    ws[f"{CT['basis']}{r}"] = f'=IF(AND({run}=0,{ai}="N"),"",IF({ai}="Y","actual","plan"))'
    ws[f"{CT['next_flag']}{r}"] = f'=IF(AND({run}=1,B{r}>={R("as_of")}),1,0)'
    for k, _, f in ct_cols:
        if f:
            ws[f"{CT[k]}{r}"].number_format = f
rt = DROPN + 1
put(ws, f"A{rt}", "Totals (all scheduled drops)", font=F_BOLD)
for k in ["offices", "new_offices", "brands", "renewals", "revenue", "kit", "transport", "kit_mail", "processing", "storage_alloc", "software_alloc",
          "insurance_alloc", "hard_costs", "h_brand_sales", "h_office", "h_receiving", "h_drop_day", "h_checks", "h_reporting", "h_admin", "hours",
          "contribution", "direct_costs", "allocations"]:
    put(ws, f"{EC[k]}{rt}", f"=SUM({EC[k]}{DROP0}:{EC[k]}{DROPN})", fmt=EFMT[k], font=F_BOLD)
put(ws, f"{EC['per_hour']}{rt}", f'=IF({EC["hours"]}{rt}>0,{EC["contribution"]}{rt}/{EC["hours"]}{rt},"n/a")', fmt=PH, font=F_BOLD)
for k in ["pay_fnd_amt", "pay_dep_amt", "pay_bal_amt", "proc_fnd", "proc_dep", "proc_bal", "live_rev", "live_cost", "live_hours", "live_contrib"]:
    put(ws, f"{CT[k]}{rt}", f"=SUM({CT[k]}{DROP0}:{CT[k]}{DROPN})", fmt=USD if "hours" not in k else HRS, font=F_BOLD)
put(ws, f"{CT['live_ph']}{rt}", f'=IF({CT["live_hours"]}{rt}>0,{CT["live_contrib"]}{rt}/{CT["live_hours"]}{rt},"n/a")', fmt=PH, font=F_BOLD)


def dp(key):
    col = EC.get(key) or CT.get(key)
    return f"Drop_PnL!${col}${DROP0}:${col}${DROPN}"


engine_widths(ws)
for k in CT.values():
    ws.column_dimensions[k].width = 12
ws.column_dimensions["A"].width = 12
ws.freeze_panes = "B7"

# ==========================================================================
# Actuals_Campaigns, Actuals_DropCosts
# ==========================================================================
ws = WS["Actuals_Campaigns"]
title(ws, "Actuals: one row per brand campaign", "Paste campaign-ops/exports/campaign_actuals.csv with its header in row 4 (columns A to Z). Columns AB onward are model helpers; do not paste over them.")
banner(ws, "A3", "Ladder rungs stay separate: delivered, placed, depleted, responded (tried is a survey answer), scanned, purchased (code redemptions). Incremental is not measured. There is no field for sales lift.", "Z3")
AC_COLS = ["campaign_id", "drop_id", "drop_date", "delivery_model", "tier", "brand_id", "offices", "units_received", "units_delivered", "units_placed",
           "units_placed_within_1bd", "units_topped_up", "units_depleted_day5", "survey_responses", "survey_tried_yes", "qr_scans",
           "code_redemptions_day30", "revenue_usd", "invoice_paid_date", "processing_fee_usd", "report_delivered_date", "brand_would_buy_again",
           "renewed", "deposit_usd", "deposit_paid_date", "survey_responses_min_office"]
header_row(ws, 4, 1, AC_COLS, height=45)
ACH = ["drop actuals in?", "balance_usd (revenue less deposit)", "responses per office used", "report due (T+7)", "report late?"]
header_row(ws, 4, 28, ACH, height=45)
for i, col in enumerate(AC_COLS):
    L = CL(i + 1)
    for r in range(AC0, ACN + 1):
        c = ws[f"{L}{r}"]
        c.fill = FILL_IN
        if col.endswith("_date"):
            c.number_format = DATE
        elif col.endswith("_usd"):
            c.number_format = USD
for r in range(AC0, ACN + 1):
    ws[f"AB{r}"] = f'=IF(B{r}="","",IFERROR(INDEX({R("sched_actuals")},MATCH(B{r},{R("sched_ids")},0)),"not in schedule"))'
    ws[f"AC{r}"] = f'=IF(B{r}="","",N(R{r})-N(X{r}))'
    ws[f"AD{r}"] = f'=IF(B{r}="","",IF(Z{r}<>"",Z{r},IF(N(G{r})>0,N(N{r})/G{r},"")))'
    ws[f"AE{r}"] = f'=IF(OR(B{r}="",C{r}=""),"",WORKDAY(C{r},{R("g2_report_bd")},{R("holidays")}))'
    ws[f"AF{r}"] = f'=IF(B{r}="","",IF(U{r}="","missing",IF(U{r}>AE{r},"Y","N")))'
    ws[f"AC{r}"].number_format = USD
    ws[f"AD{r}"].number_format = '0.0'
    ws[f"AE{r}"].number_format = DATE
add_list_validation(ws, f"D{AC0}:D{ACN}", "=" + R("L_models"))
add_list_validation(ws, f"E{AC0}:E{ACN}", "=" + R("L_tiers"))
add_list_validation(ws, f"V{AC0}:V{ACN}", "=" + R("L_rebuy"))
add_list_validation(ws, f"W{AC0}:W{ACN}", "=" + R("L_renewed"))
for i, col in enumerate(AC_COLS):
    REF["AC_" + col] = f"Actuals_Campaigns!${CL(i + 1)}${AC0}:${CL(i + 1)}${ACN}"
REF.update({"AC_flag": f"Actuals_Campaigns!$AB${AC0}:$AB${ACN}", "AC_balance": f"Actuals_Campaigns!$AC${AC0}:$AC${ACN}",
            "AC_rpo": f"Actuals_Campaigns!$AD${AC0}:$AD${ACN}", "AC_late": f"Actuals_Campaigns!$AF${AC0}:$AF${ACN}"})
widths(ws, {CL(i + 1): 13 for i in range(len(AC_COLS))})
widths(ws, {"AA": 3, "AB": 14, "AC": 14, "AD": 12, "AE": 12, "AF": 10})
ws.freeze_panes = "C5"

ws = WS["Actuals_DropCosts"]
title(ws, "Actuals: one row per drop, direct costs only", "Paste campaign-ops/exports/drop_costs.csv with its header in row 4 (columns A to I). Monthly overhead is not here; Cash_Flow pays it once.")
DC_COLS = ["drop_id", "drop_date", "delivery_model", "offices", "brands", "kit_cost_usd", "transport_cost_usd", "other_direct_cost_usd", "notes"]
header_row(ws, 4, 1, DC_COLS, height=32)
header_row(ws, 4, 11, ["drop actuals in?"], height=32)
for i, col in enumerate(DC_COLS):
    L = CL(i + 1)
    for r in range(DC0, DCN + 1):
        c = ws[f"{L}{r}"]
        c.fill = FILL_IN
        if col.endswith("_date"):
            c.number_format = DATE
        elif col.endswith("_usd"):
            c.number_format = USD
    REF["DC_" + col] = f"Actuals_DropCosts!${L}${DC0}:${L}${DCN}"
for r in range(DC0, DCN + 1):
    ws[f"K{r}"] = f'=IF(A{r}="","",IFERROR(INDEX({R("sched_actuals")},MATCH(A{r},{R("sched_ids")},0)),"not in schedule"))'
REF["DC_flag"] = f"Actuals_DropCosts!$K${DC0}:$K${DCN}"
add_list_validation(ws, f"C{DC0}:C{DCN}", "=" + R("L_models"))
widths(ws, {CL(i + 1): 14 for i in range(len(DC_COLS))})
widths(ws, {"I": 40, "J": 3, "K": 16})
ws.freeze_panes = "B5"

# ==========================================================================
# Hours_Log and Toggl_Import
# ==========================================================================
ws = WS["Hours_Log"]
title(ws, "Founder hours log", "Type one row per entry, or paste campaign-ops/exports/hours_log.csv (header in row 4, columns A to F). Leave drop_id blank for time that is not for a drop.")
banner(ws, "A3", "Activity must be one of the seven keys (Lists). Toggl entries add in from the Toggl_Import tab. Totals per drop and per week are on the right.", "F3")
HL_COLS = ["date", "drop_id", "campaign_id", "activity", "hours", "note"]
header_row(ws, 4, 1, HL_COLS, height=30)
for r in range(HL0, HLN + 1):
    for L in "ABCDEF":
        ws[f"{L}{r}"].fill = FILL_IN
    ws[f"A{r}"].number_format = DATE
    ws[f"E{r}"].number_format = HRS
add_list_validation(ws, f"D{HL0}:D{HLN}", "=" + R("L_acts"))
REF.update({"HL_date": f"Hours_Log!$A${HL0}:$A${HLN}", "HL_drop": f"Hours_Log!$B${HL0}:$B${HLN}",
            "HL_act": f"Hours_Log!$D${HL0}:$D${HLN}", "HL_hours": f"Hours_Log!$E${HL0}:$E${HLN}"})
REF.update({"TG_date": f"Toggl_Import!$R${TG0}:$R${TGN}", "TG_drop": f"Toggl_Import!$S${TG0}:$S${TGN}",
            "TG_act": f"Toggl_Import!$T${TG0}:$T${TGN}", "TG_hours": f"Toggl_Import!$U${TG0}:$U${TGN}"})
# per-drop totals H4:P17
put(ws, "H3", "Totals per drop (hand log plus Toggl)", font=F_SEC)
header_row(ws, 4, 8, ["drop_id"] + ACT_KEYS + ["total"], height=30)
for i in range(N_DROPS):
    r = 5 + i
    put(ws, f"H{r}", f"=Schedule!A{DROP0 + i}")
    for j, key in enumerate(ACT_KEYS):
        L = CL(9 + j)
        ws[f"{L}{r}"] = (f"=SUMIFS({R('HL_hours')},{R('HL_drop')},$H{r},{R('HL_act')},{L}$4)"
                         f"+SUMIFS({R('TG_hours')},{R('TG_drop')},$H{r},{R('TG_act')},{L}$4)")
        ws[f"{L}{r}"].number_format = HRS
    put(ws, f"P{r}", f"=SUM(I{r}:O{r})", fmt=HRS, font=F_BOLD)
r_all = 5 + N_DROPS          # 17
put(ws, f"H{r_all}", "All hours")
for j, key in enumerate(ACT_KEYS):
    L = CL(9 + j)
    ws[f"{L}{r_all}"] = f"=SUMIFS({R('HL_hours')},{R('HL_act')},{L}$4)+SUMIFS({R('TG_hours')},{R('TG_act')},{L}$4)"
    ws[f"{L}{r_all}"].number_format = HRS
put(ws, f"P{r_all}", f"=SUM(I{r_all}:O{r_all})", fmt=HRS, font=F_BOLD)
put(ws, f"H{r_all + 1}", "Not linked to a scheduled drop")
for j in range(8):
    L = CL(9 + j)
    ws[f"{L}{r_all + 1}"] = f"={L}{r_all}-SUM({L}5:{L}{r_all - 1})"
    ws[f"{L}{r_all + 1}"].number_format = HRS
REF["HL_all_total"] = f"Hours_Log!$P${r_all}"
REF["HL_unlinked_total"] = f"Hours_Log!$P${r_all + 1}"
# weekly table
w0 = r_all + 4   # 21
put(ws, f"H{w0 - 1}", "Totals per week (hand log plus Toggl)", font=F_SEC)
header_row(ws, w0, 8, ["week", "week starts"] + ACT_KEYS + ["total", "linked to a drop"], height=30)
for i in range(N_WEEKS):
    r = w0 + 1 + i
    put(ws, f"H{r}", i + 1)
    put(ws, f"I{r}", f"={R('week1_start')}" if i == 0 else f"=I{r - 1}+{R('days_per_week')}", fmt=DATE)
    for j, key in enumerate(ACT_KEYS):
        L = CL(10 + j)
        crit = f'{R("HL_date")},">="&$I{r},{R("HL_date")},"<"&$I{r}+{R("days_per_week")}'
        crit_t = f'{R("TG_date")},">="&$I{r},{R("TG_date")},"<"&$I{r}+{R("days_per_week")}'
        ws[f"{L}{r}"] = (f"=SUMIFS({R('HL_hours')},{crit},{R('HL_act')},{L}${w0})"
                         f"+SUMIFS({R('TG_hours')},{crit_t},{R('TG_act')},{L}${w0})")
        ws[f"{L}{r}"].number_format = HRS
    put(ws, f"Q{r}", f"=SUM(J{r}:P{r})", fmt=HRS, font=F_BOLD)
    crit = f'{R("HL_date")},">="&$I{r},{R("HL_date")},"<"&$I{r}+{R("days_per_week")}'
    crit_t = f'{R("TG_date")},">="&$I{r},{R("TG_date")},"<"&$I{r}+{R("days_per_week")}'
    ws[f"R{r}"] = (f'=SUMIFS({R("HL_hours")},{crit},{R("HL_drop")},{R("drop_prefix")}&"*")'
                   f'+SUMIFS({R("TG_hours")},{crit_t},{R("TG_drop")},{R("drop_prefix")}&"*")')
    ws[f"R{r}"].number_format = HRS
wl = w0 + N_WEEKS
put(ws, f"H{wl + 1}", "Six months")
for L in "JKLMNOPQR":
    put(ws, f"{L}{wl + 1}", f"=SUM({L}{w0 + 1}:{L}{wl})", fmt=HRS, font=F_BOLD)
REF["HL_week_total"] = f"Hours_Log!$Q${wl + 1}"
put(ws, f"H{wl + 3}", "Invalid activity keys in the hand log (should be 0)")
put(ws, f"Q{wl + 3}", f"=COUNTA({R('HL_act')})-SUMPRODUCT(COUNTIF({R('HL_act')},{R('L_acts')}))", fmt=INT, font=F_BOLD)
REF["HL_invalid"] = f"Hours_Log!$Q${wl + 3}"
put(ws, f"H{wl + 4}", "Rows whose drop_id is not on Schedule (should be 0)")
put(ws, f"Q{wl + 4}", f'=SUMPRODUCT(({R("HL_drop")}<>"")*(COUNTIF({R("sched_ids")},{R("HL_drop")})=0))', fmt=INT, font=F_BOLD)
REF["HL_badid"] = f"Hours_Log!$Q${wl + 4}"
put(ws, f"H{wl + 5}", "Hours outside the 26 weeks (dated before week 1 or after week 26)")
put(ws, f"Q{wl + 5}", f"=P{r_all}-Q{wl + 1}", fmt=HRS, font=F_BOLD)
widths(ws, {"A": 12, "B": 10, "C": 11, "D": 20, "E": 7, "F": 30, "G": 3, "H": 12, "I": 12})
for j in range(10):
    ws.column_dimensions[CL(10 + j)].width = 11
ws.freeze_panes = "A5"

ws = WS["Toggl_Import"]
title(ws, "Toggl import (optional)", "Paste a Toggl time-entry export with its header row in row 9, columns A to P. Name each Toggl project after the drop (DRP-001) and tag each entry with one activity key.")
banner(ws, "G3", "Toggl's own help says CSV and Excel exports are a paid-plan feature (Starter from $9 per license a month; support.toggl.com, opened 2026-10-23). "
                 "Do not upgrade without a written yes. On the free plan, type hours into Hours_Log instead. The header names in C4:C7 are unverified; edit them to match your export.", "P7")
put(ws, "B3", "Header text in your export for:", font=F_BOLD)
for i, (lab, default) in enumerate([("date", "Start date"), ("duration (hh:mm:ss)", "Duration"), ("project (drop_id)", "Project"), ("activity key", "Tags")]):
    r = 4 + i
    put(ws, f"B{r}", lab)
    as_input(put(ws, f"C{r}", default))
    put(ws, f"D{r}", f'=IFERROR(MATCH(C{r},$A$9:$P$9,0),"")', fmt=INT)
    put(ws, f"E{r}", f'=IF(D{r}="","not found in row 9","column found")', font=F_NOTE)
put(ws, "B8", "Paste area (row 9 = Toggl header)", font=F_BOLD)
for L in [CL(i) for i in range(1, 17)]:
    ws[f"{L}9"].fill = FILL_IN
header_row(ws, 9, 18, ["date", "drop_id", "activity", "hours"], height=30)
for r in range(TG0, TGN + 1):
    row_rng = f"$A{r}:$P{r}"
    ws[f"R{r}"] = (f'=IF($D$4="","",IF(INDEX({row_rng},$D$4)="","",IF(ISNUMBER(INDEX({row_rng},$D$4)),INDEX({row_rng},$D$4),'
                   f'IFERROR(DATEVALUE(INDEX({row_rng},$D$4)),""))))')
    ws[f"S{r}"] = (f'=IF(OR(R{r}="",$D$6=""),"",IF(LEFT(INDEX({row_rng},$D$6),LEN({R("drop_prefix")}))={R("drop_prefix")},INDEX({row_rng},$D$6),""))')
    ws[f"T{r}"] = (f'=IF(OR(R{r}="",$D$7=""),"",TRIM(IFERROR(LEFT(INDEX({row_rng},$D$7),FIND(",",INDEX({row_rng},$D$7))-1),INDEX({row_rng},$D$7))))')
    ws[f"U{r}"] = (f'=IF(OR(R{r}="",$D$5=""),0,IFERROR(IF(ISNUMBER(INDEX({row_rng},$D$5)),INDEX({row_rng},$D$5),TIMEVALUE(INDEX({row_rng},$D$5)))*{R("hours_per_day")},0))')
    ws[f"R{r}"].number_format = DATE
    ws[f"U{r}"].number_format = HRS
put(ws, "W9", "Checks", font=F_BOLD)
put(ws, "W10", "Rows with a date but zero hours")
put(ws, "X10", f'=COUNTIFS({R("TG_date")},">0",{R("TG_hours")},0)', fmt=INT)
put(ws, "W11", "Rows whose activity is not one of the seven keys")
put(ws, "X11", f'=COUNTIF({R("TG_date")},">0")-SUMPRODUCT(COUNTIF({R("TG_act")},{R("L_acts")}))', fmt=INT)
put(ws, "W12", "Total Toggl hours read")
put(ws, "X12", f"=SUM({R('TG_hours')})", fmt=HRS)
REF["TG_zero"] = "Toggl_Import!$X$10"
REF["TG_invalid"] = "Toggl_Import!$X$11"
widths(ws, {"B": 30, "C": 16, "D": 8, "E": 20, "R": 12, "S": 10, "T": 20, "U": 8, "W": 44, "X": 10})
ws.freeze_panes = "A10"

# ==========================================================================
# Pipeline
# ==========================================================================
ws = WS["Pipeline"]
title(ws, "Pipeline log", "One row per event. Paste desk-drop-outreach/exports/pipeline_log.csv with its header in row 4 (columns A to I), or type rows. Keep rows in date order.")
banner(ws, "A3", "value_number: headcount for signed; USD for paid; USD per month for an office budget_probe; USD per campaign for a brand budget_probe (willingness to pay); USD committed for a renewal_answer of yes.", "I3")
PL_COLS = ["date", "side", "org_id", "org_name", "event", "value_number", "value_text", "controls_budget", "notes"]
header_row(ws, 4, 1, PL_COLS, height=30)
header_row(ws, 4, 11, ["first of this org and event", "brand would pay threshold, controls budget", "first such brand",
                       "office named office-paid threshold", "first such office", "renewal at threshold price", "office probe value", "brand probe value"], height=58)
for r in range(PL0, PLN + 1):
    for L in "ABCDEFGHI":
        ws[f"{L}{r}"].fill = FILL_IN
    ws[f"A{r}"].number_format = DATE
    ws[f"K{r}"] = f'=IF(C{r}="","",IF(COUNTIFS(C${PL0}:C{r},C{r},E${PL0}:E{r},E{r})=1,1,0))'
    ws[f"L{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="brand",E{r}="budget_probe",N(F{r})>={R("g0_brand_usd")},H{r}="Y"),1,0))'
    ws[f"M{r}"] = f'=IF(L{r}=1,IF(COUNTIFS(C${PL0}:C{r},C{r},L${PL0}:L{r},1)=1,1,0),0)'
    ws[f"N{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="office",E{r}="budget_probe",N(F{r})>={R("dr_switch_usd")}),1,0))'
    ws[f"O{r}"] = f'=IF(N{r}=1,IF(COUNTIFS(C${PL0}:C{r},C{r},N${PL0}:N{r},1)=1,1,0),0)'
    ws[f"P{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="brand",E{r}="renewal_answer",N(F{r})>={R("g3_renewal_usd")}),1,0))'
    ws[f"Q{r}"] = f'=IF(AND(B{r}="office",E{r}="budget_probe",ISNUMBER(F{r})),F{r},"")'
    ws[f"R{r}"] = f'=IF(AND(B{r}="brand",E{r}="budget_probe",ISNUMBER(F{r})),F{r},"")'
add_list_validation(ws, f"B{PL0}:B{PLN}", "=" + R("L_side"))
add_list_validation(ws, f"E{PL0}:E{PLN}", "=" + R("L_event"))
add_list_validation(ws, f"H{PL0}:H{PLN}", "=" + R("L_yn"))
pr = lambda L: f"Pipeline!${L}${PL0}:${L}${PLN}"
REF.update({"PL_date": pr("A"), "PL_side": pr("B"), "PL_org": pr("C"), "PL_event": pr("E"), "PL_value": pr("F"), "PL_text": pr("G"),
            "PL_first": pr("K"), "PL_g0b_first": pr("M"), "PL_op_first": pr("O"), "PL_g3": pr("P"), "PL_oprobe": pr("Q"), "PL_bprobe": pr("R")})
# summary block at T
put(ws, "T3", "Summary (distinct organisations)", font=F_SEC)
header_row(ws, 4, 20, ["Measure", "Count", "Cut-off"], height=30)
summ = [
    ("pl_g0_office_conv", "Office conversations by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"conversation",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_office_yes", "Offices yes in principle by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"yes_in_principle",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_brand_conv", "Brand conversations by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"conversation",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_brand_yes", "Brands that would pay the threshold and control the budget, by Gate 0", f'=SUMIFS({R("PL_g0b_first")},{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g1_signed", "Offices signed by Gate 1", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g1_headcount", "Combined Tuesday headcount of offices signed by Gate 1", f'=SUMIFS({R("PL_value")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_first")},1,{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g1_paid", "Brands paid by Gate 1", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"paid",{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g3_renewals", "Renewals at the threshold price, by Gate 3", f'=SUMIFS({R("PL_g3")},{R("PL_date")},"<="&{R("gate3_date")})', "gate3_date"),
    ("pl_op_offices", "Offices that named the office-paid threshold, to date", f'=SUMIFS({R("PL_op_first")},{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_signed_all", "Offices signed, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_optout_office", "Offices opted out, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"opt_out",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_paid_all", "Brands paid, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"paid",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_outreach", "Outreach messages sent, to date (events, not distinct)", f'=COUNTIFS({R("PL_event")},"outreach_sent",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_med_office", "Median office budget probe (USD per month)", f'=IF(COUNT({R("PL_oprobe")})>0,MEDIAN({R("PL_oprobe")}),"")', ""),
    ("pl_med_brand", "Median brand willingness to pay (USD per campaign)", f'=IF(COUNT({R("PL_bprobe")})>0,MEDIAN({R("PL_bprobe")}),"")', ""),
    ("pl_bad_event", "Rows with an event not in the list (should be 0)", f'=COUNTA({R("PL_event")})-SUMPRODUCT(COUNTIF({R("PL_event")},{R("L_event")}))', ""),
    ("pl_bad_side", "Rows with a side not in the list (should be 0)", f'=COUNTA({R("PL_side")})-SUMPRODUCT(COUNTIF({R("PL_side")},{R("L_side")}))', ""),
]
for i, (key, lab, f, cut) in enumerate(summ):
    r = 5 + i
    put(ws, f"T{r}", lab, align=WRAP)
    put(ws, f"U{r}", f, fmt=USD if "med" in key else INT, font=F_BOLD)
    put(ws, f"V{r}", f"={R(cut)}" if cut else "", fmt=DATE)
    REF[key] = f"Pipeline!$U${r}"
put(ws, f"T{5 + len(summ)}", "Active offices, to date (signed less opted out)")
put(ws, f"U{5 + len(summ)}", f"={R('pl_signed_all')}-{R('pl_optout_office')}", fmt=INT, font=F_BOLD)
REF["pl_active_offices"] = f"Pipeline!$U${5 + len(summ)}"
widths(ws, {"A": 11, "B": 8, "C": 10, "D": 22, "E": 16, "F": 11, "G": 30, "H": 9, "I": 24, "J": 2,
            "K": 9, "L": 11, "M": 8, "N": 11, "O": 8, "P": 10, "Q": 10, "R": 10, "S": 2, "T": 46, "U": 11, "V": 12})
ws.freeze_panes = "A5"

# ==========================================================================
# Drop_Actuals
# ==========================================================================
ws = WS["Drop_Actuals"]
title(ws, "Actuals rolled up per drop", "Read-only. Sums Actuals_Campaigns, Actuals_DropCosts and the hours logs by drop_id. Ladder rungs stay in separate columns.")
banner(ws, "A3", "Incremental purchases are not measured; the column says so. No column measures sales lift.", "T3")
DA = ["drop_id", "Drop date", "Actuals in", "Revenue", "Card processing", "Display kits", "Transport", "Other direct", "Overhead allocations (same views as plan)",
      "Hard costs"] + [k + " (h)" for k in ACT_KEYS] + ["Founder hours", "Contribution", "Contribution per founder hour",
      "units_received", "units_delivered", "units_placed", "units_placed_within_1bd", "units_topped_up", "units_depleted_day5", "survey_responses",
      "survey_tried_yes", "qr_scans", "code_redemptions_day30", "incremental",
      "Brand campaigns", "Placed within 1 business day (share of delivered)", "Campaigns under the responses-per-office threshold",
      "Reports late or missing", "Brands that would buy again (yes)", "Renewed Y", "Renewed N"]
header_row(ws, 6, 1, DA, height=70)
ladder = ["units_received", "units_delivered", "units_placed", "units_placed_within_1bd", "units_topped_up", "units_depleted_day5", "survey_responses",
          "survey_tried_yes", "qr_scans", "code_redemptions_day30"]
for i in range(N_DROPS):
    r = DROP0 + i
    put(ws, f"A{r}", f"=Drop_PnL!A{r}")
    put(ws, f"B{r}", f"=Drop_PnL!B{r}", fmt=DATE)
    put(ws, f"C{r}", f"=Drop_PnL!{CT['actuals_in']}{r}")
    put(ws, f"D{r}", f"=SUMIFS({R('AC_revenue_usd')},{R('AC_drop_id')},A{r})", fmt=USD)
    put(ws, f"E{r}", f"=SUMIFS({R('AC_processing_fee_usd')},{R('AC_drop_id')},A{r})", fmt=USD)
    put(ws, f"F{r}", f"=SUMIFS({R('DC_kit_cost_usd')},{R('DC_drop_id')},A{r})", fmt=USD)
    put(ws, f"G{r}", f"=SUMIFS({R('DC_transport_cost_usd')},{R('DC_drop_id')},A{r})", fmt=USD)
    put(ws, f"H{r}", f"=SUMIFS({R('DC_other_direct_cost_usd')},{R('DC_drop_id')},A{r})", fmt=USD)
    put(ws, f"I{r}", f"=Drop_PnL!{EC['allocations']}{r}", fmt=USD)
    put(ws, f"J{r}", f"=SUM(E{r}:I{r})", fmt=USD, font=F_BOLD)
    for j in range(7):
        put(ws, f"{CL(11 + j)}{r}", f"=Hours_Log!{CL(9 + j)}{5 + i}", fmt=HRS)
    put(ws, f"R{r}", f"=SUM(K{r}:Q{r})", fmt=HRS, font=F_BOLD)
    put(ws, f"S{r}", f"=D{r}-J{r}", fmt=USD, font=F_BOLD)
    put(ws, f"T{r}", f'=IF(R{r}>0,S{r}/R{r},"n/a")', fmt=PH, font=F_BOLD)
    for j, lk in enumerate(ladder):
        put(ws, f"{CL(21 + j)}{r}", f"=SUMIFS({R('AC_' + lk)},{R('AC_drop_id')},A{r})", fmt='#,##0')
    put(ws, f"AE{r}", "not measured", font=F_NOTE)
    put(ws, f"AF{r}", f"=COUNTIF({R('AC_drop_id')},A{r})", fmt=INT)
    put(ws, f"AG{r}", f'=IF(V{r}>0,X{r}/V{r},"")', fmt=PCT)
    put(ws, f"AH{r}", f'=IF(AF{r}=0,"",COUNTIFS({R("AC_drop_id")},A{r},{R("AC_rpo")},"<"&{R("g2_responses")}))', fmt=INT)
    put(ws, f"AI{r}", f'=IF(AF{r}=0,"",COUNTIFS({R("AC_drop_id")},A{r},{R("AC_late")},"Y")+COUNTIFS({R("AC_drop_id")},A{r},{R("AC_late")},"missing"))', fmt=INT)
    put(ws, f"AJ{r}", f'=IF(AF{r}=0,"",COUNTIFS({R("AC_drop_id")},A{r},{R("AC_brand_would_buy_again")},"yes"))', fmt=INT)
    put(ws, f"AK{r}", f'=COUNTIFS({R("AC_drop_id")},A{r},{R("AC_renewed")},"Y")', fmt=INT)
    put(ws, f"AL{r}", f'=COUNTIFS({R("AC_drop_id")},A{r},{R("AC_renewed")},"N")', fmt=INT)
dar = lambda L: f"Drop_Actuals!${L}${DROP0}:${L}${DROPN}"
REF.update({"DA_ids": dar("A"), "DA_rev": dar("D"), "DA_cost": dar("J"), "DA_hours": dar("R"), "DA_contrib": dar("S"),
            "DA_delivered": dar("V"), "DA_placed1": dar("X"), "DA_share": dar("AG"), "DA_campaigns": dar("AF"), "DA_under": dar("AH"),
            "DA_late": dar("AI"), "DA_rebuy": dar("AJ")})
widths(ws, {CL(i + 1): 11 for i in range(len(DA))})
ws.freeze_panes = "B7"

# ==========================================================================
# Cash_Ledger (overhead payments)
# ==========================================================================
ws = WS["Cash_Ledger"]
title(ws, "Overhead payment schedule", "Monthly costs as they are paid. Cash_Flow reads only these rows for overhead; per-drop allocations never reach the cash flow, so nothing is counted twice.")
header_row(ws, 4, 1, ["line", "payment number", "date", "amount (USD)", "rule"], height=30)
r = 5
LG0 = r
for line, start_ref, amt_rule, rule_text in [
    ("software", "software_start", f"IF(AND(C{{r}}>={R('week1_start')},C{{r}}<={R('horizon_end')}),{R('software_monthly')},0)", "monthly from 'Software paid from'"),
    ("storage", "storage_start", None, "monthly while Storage = unit, from the rental date to the release date"),
    ("insurance", "insurance_bind", f'IF(AND({R("insurance_billing")}="monthly",C{{r}}<={R("horizon_end")}),{R("insurance_monthly")},0)', "monthly when billing = monthly"),
    ("phone", "week1_start", f"IF(C{{r}}<={R('horizon_end')},{R('phone_monthly')},0)", "monthly from week 1"),
]:
    for k in range(1, 13):
        put(ws, f"A{r}", line)
        put(ws, f"B{r}", k)
        if line == "storage":
            put(ws, f"C{r}", f'=IF({R("storage_start")}="","",EDATE({R("storage_start")},B{r}-1))', fmt=DATE)
            put(ws, f"D{r}", f'=IF(C{r}="",0,IF(AND({R("storage_choice")}="unit",C{r}<={R("horizon_end")},OR({R("storage_end")}="",C{r}<={R("storage_end")})),{R("storage_monthly")},0))', fmt=USD)
        else:
            put(ws, f"C{r}", f"=EDATE({R(start_ref)},B{r}-1)", fmt=DATE)
            put(ws, f"D{r}", "=" + amt_rule.format(r=r), fmt=USD)
        put(ws, f"E{r}", rule_text, font=F_NOTE)
        r += 1
    if line == "insurance":
        put(ws, f"A{r}", "insurance")
        put(ws, f"B{r}", "annual")
        put(ws, f"C{r}", f"={R('insurance_bind')}", fmt=DATE)
        put(ws, f"D{r}", f'=IF(AND({R("insurance_billing")}="annual",C{r}<={R("horizon_end")}),{R("insurance_monthly")}*{R("months_per_year")},0)', fmt=USD)
        put(ws, f"E{r}", "one year's premium at bind when billing = annual", font=F_NOTE)
        r += 1
LGN = r - 1
REF.update({"LG_line": f"Cash_Ledger!$A${LG0}:$A${LGN}", "LG_date": f"Cash_Ledger!$C${LG0}:$C${LGN}", "LG_amt": f"Cash_Ledger!$D${LG0}:$D${LGN}"})
put(ws, f"A{r + 1}", "Total inside the six months", font=F_BOLD)
put(ws, f"D{r + 1}", f'=SUMIFS({R("LG_amt")},{R("LG_date")},">="&{R("week1_start")},{R("LG_date")},"<="&{R("horizon_end")})', fmt=USD, font=F_BOLD)
REF["LG_total"] = f"Cash_Ledger!$D${r + 1}"
widths(ws, {"A": 12, "B": 16, "C": 12, "D": 14, "E": 60})
ws.freeze_panes = "A5"

# ==========================================================================
# Cash_Flow
# ==========================================================================
ws = WS["Cash_Flow"]
title(ws, "Six-month cash flow, weekly", "Startup outlays at their timing, brand cash on the plan's terms, overhead paid once from Cash_Ledger. Outflows are negative.")
banner(ws, "A3", "Planning estimates, not a forecast. Drops switch to actual cash when Schedule says Actuals in = Y.", "AC3")
put(ws, "B4", "Week", font=F_BOLD)
put(ws, "B5", "Week starts", font=F_BOLD)
put(ws, "B6", "Week ends", font=F_BOLD)
put(ws, "B7", "Month", font=F_BOLD)
for i in range(N_WEEKS):
    L = CL(WK0 + i)
    put(ws, f"{L}4", i + 1, font=F_H, fill=FILL_H, align=CENTER)
    put(ws, f"{L}5", f"={R('week1_start')}" if i == 0 else f"={CL(WK0 + i - 1)}5+{R('days_per_week')}", fmt='mmm d')
    put(ws, f"{L}6", f"={L}5+{R('days_per_week')}-1", fmt='mmm d')
    put(ws, f"{L}7", f'=TEXT({L}5,"mmm yyyy")', font=F_NOTE)
TOT = CL(WKN + 1)  # AC
put(ws, f"{TOT}4", "Six months", font=F_H, fill=FILL_H, align=CENTER)


def sumifs_window(sum_rng, date_rng, s, e, extra=""):
    return f'SUMIFS({sum_rng},{date_rng},">="&{s},{date_rng},"<="&{e}{extra})'


def cash_lines(s, e):
    """Return dict line -> formula body (no '='), for a window [s, e]."""
    N_ = ',' + dp('actuals_in') + ',"N"'
    Y_ = ',' + R('AC_flag') + ',"Y"'
    YD = ',' + R('DC_flag') + ',"Y"'
    return {
        "rec_plan": "+".join(sumifs_window(dp(a), dp(d), s, e, N_) for a, d in
                             (("pay_fnd_amt", "pay_fnd_date"), ("pay_dep_amt", "pay_dep_date"), ("pay_bal_amt", "pay_bal_date"))),
        "rec_act": sumifs_window(R("AC_deposit_usd"), R("AC_deposit_paid_date"), s, e, Y_) + "+" + sumifs_window(R("AC_balance"), R("AC_invoice_paid_date"), s, e, Y_),
        "kit": "-" + sumifs_window(dp("kit"), dp("kit_date"), s, e, N_),
        "transport": "-" + sumifs_window(dp("transport"), dp("tr_date"), s, e, N_),
        "kit_mail": "-" + sumifs_window(dp("kit_mail"), dp("kit_date"), s, e, N_),
        "proc": "-(" + "+".join(sumifs_window(dp(a), dp(d), s, e, N_) for a, d in
                                (("proc_fnd", "pay_fnd_date"), ("proc_dep", "pay_dep_date"), ("proc_bal", "pay_bal_date"))) + ")",
        "direct_act": "-(" + "+".join(sumifs_window(R(k), R("DC_drop_date"), s, e, YD) for k in ("DC_kit_cost_usd", "DC_transport_cost_usd", "DC_other_direct_cost_usd"))
                      + "+" + sumifs_window(R("AC_processing_fee_usd"), R("AC_invoice_paid_date"), s, e, Y_) + ")",
        "software": "-" + sumifs_window(R("LG_amt"), R("LG_date"), s, e, ',' + R("LG_line") + ',"software"'),
        "insurance": "-" + sumifs_window(R("LG_amt"), R("LG_date"), s, e, ',' + R("LG_line") + ',"insurance"'),
        "storage": "-" + sumifs_window(R("LG_amt"), R("LG_date"), s, e, ',' + R("LG_line") + ',"storage"'),
        "phone": "-" + sumifs_window(R("LG_amt"), R("LG_date"), s, e, ',' + R("LG_line") + ',"phone"'),
        "startup": "-" + sumifs_window(R("su_amt"), R("su_date"), s, e),
    }


CF_ROWS = [  # (row, key or None, label, kind)
    (8, None, "Receipts", "sec"),
    (9, "rec_plan", "Brand receipts, plan (drops without actuals)", "line"),
    (10, "rec_act", "Brand receipts, actual (drops with actuals)", "line"),
    (11, "tot_rec", "Total receipts", "sum:9:10"),
    (12, None, "Direct drop costs", "sec"),
    (13, "kit", "Display kits, plan", "line"),
    (14, "transport", "Transport, plan", "line"),
    (15, "kit_mail", "Kit mailing, plan (needs quote)", "line"),
    (16, "proc", "Card processing, plan", "line"),
    (17, "direct_act", "Direct costs and processing, actual", "line"),
    (18, "tot_direct", "Total direct costs", "sum:13:17"),
    (19, None, "Overhead, paid once here (drop allocations are views of these lines)", "sec"),
    (20, "software", "Software", "line"),
    (21, "insurance", "Insurance", "line"),
    (22, "storage", "Storage", "line"),
    (23, "phone", "Phone", "line"),
    (24, "tot_over", "Total overhead", "sum:20:23"),
    (25, "startup", "Startup outlays (Inputs section 11)", "line"),
    (26, "net", "Net cash flow", "net"),
    (27, "cum", "Cumulative net cash flow, before founder cash", "cum"),
    (28, "fc", "Founder cash in", "fc"),
    (29, "bal", "Cash balance with founder cash", "bal"),
]
for rr, key, lab, kind in CF_ROWS:
    if kind == "sec":
        section(ws, rr, lab, last_col=TOT)
        continue
    put(ws, f"B{rr}", lab, font=F_BOLD if kind != "line" else None)
    for i in range(N_WEEKS):
        L = CL(WK0 + i)
        s, e = f"{L}$5", f"{L}$6"
        if kind == "line":
            f = "=" + cash_lines(s, e)[key]
        elif kind.startswith("sum"):
            _, a, b = kind.split(":")
            f = f"=SUM({L}{a}:{L}{b})"
        elif kind == "net":
            f = f"={L}11+{L}18+{L}24+{L}25"
        elif kind == "cum":
            f = f"={L}26" if i == 0 else f"={CL(WK0 + i - 1)}27+{L}26"
        elif kind == "fc":
            f = f'=IF(AND({R("founder_cash_date")}>={L}$5,{R("founder_cash_date")}<={L}$6),N({R("founder_cash")}),0)'
        elif kind == "bal":
            f = f"={L}27+SUM(${CL(WK0)}28:{L}28)"
        put(ws, f"{L}{rr}", f, fmt=USD, font=F_BOLD if kind != "line" else None)
    if kind in ("cum", "bal"):
        put(ws, f"{TOT}{rr}", f"={WKL}{rr}", fmt=USD, font=F_BOLD)
    else:
        put(ws, f"{TOT}{rr}", f"=SUM({CL(WK0)}{rr}:{WKL}{rr})", fmt=USD, font=F_BOLD)
for rr in (26, 27, 29):
    for i in range(N_WEEKS + 1):
        ws[f"{CL(WK0 + i)}{rr}"].border = Border(top=THIN)
ws.conditional_formatting.add(f"C27:{WKL}27", CellIsRule(operator="lessThan", formula=["0"], font=Font(color="9C0006", bold=True)))
# summary
section(ws, 31, "Lowest point and capital", last_col=TOT)
cfsum = [
    ("cf_low", "Lowest cumulative net cash flow (before founder cash)", f"=MIN(C27:{WKL}27)", USD),
    ("cf_low_week", "Week of the lowest point", f"=INDEX(C4:{WKL}4,MATCH(C32,C27:{WKL}27,0))", INT),
    ("cf_low_date", "That week starts", f"=INDEX(C5:{WKL}5,MATCH(C32,C27:{WKL}27,0))", 'mmm d'),
    ("cf_need", "Peak cash need (the lowest point, as a positive number)", "=-MIN(0,C32)", USD),
    ("cf_reserve", "Reserve held back (plan)", f"={R('reserve_usd')}", USD),
    ("cf_commit", "Capital to commit: peak need plus reserve", "=C35+C36", USD),
    ("cf_plan_cap", "Plan capital figure, high end (Capital tab)", "=Capital!D14", USD),
    ("cf_gap", "Gap: plan capital figure minus capital to commit (positive = headroom)", "=C38-C37", USD),
    ("cf_founder", "Founder cash committed (Inputs)", f'=IF({R("founder_cash")}="","not set",{R("founder_cash")})', USD),
    ("cf_low_bal", "Lowest cash balance with founder cash", f"=MIN(C29:{WKL}29)", USD),
    ("cf_end", "Cumulative net cash at the end of week 26", f"={WKL}27", USD),
]
for i, (key, lab, f, fmt) in enumerate(cfsum):
    rr = 32 + i
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f, fmt=fmt, font=F_BOLD, fill=FILL_KEY if key in ("cf_low", "cf_commit", "cf_gap") else None)
    REF[key] = f"Cash_Flow!$C${rr}"
# monthly block
M0 = 46
section(ws, M0 - 1, "Monthly view (computed directly from the same sources, as a cross-check of the weekly grid)", last_col=TOT)
put(ws, f"B{M0}", "Month starts", font=F_BOLD)
put(ws, f"B{M0 + 1}", "Counted from", font=F_BOLD)
put(ws, f"B{M0 + 2}", "Counted to", font=F_BOLD)
N_MONTHS = 7
for i in range(N_MONTHS):
    L = CL(3 + i)
    put(ws, f"{L}{M0}", f"=DATE(YEAR({R('week1_start')}),MONTH({R('week1_start')}),1)" if i == 0 else f"=EDATE({CL(2 + i)}{M0},1)", fmt='mmm yy', font=F_H, fill=FILL_H)
    put(ws, f"{L}{M0 + 1}", f"=MAX({L}{M0},{R('week1_start')})", fmt='mmm d')
    put(ws, f"{L}{M0 + 2}", f"=MIN(EOMONTH({L}{M0},0),{R('horizon_end')})", fmt='mmm d')
MT = CL(3 + N_MONTHS)  # J
put(ws, f"{MT}{M0}", "Six months", font=F_H, fill=FILL_H)
mrow = M0 + 3
MROW = {}
for rr, key, lab, kind in CF_ROWS:
    if kind == "sec" or kind in ("cum", "fc", "bal"):
        continue
    put(ws, f"B{mrow}", lab, font=F_BOLD if kind != "line" else None)
    MROW[key] = mrow
    for i in range(N_MONTHS):
        L = CL(3 + i)
        s, e = f"{L}${M0 + 1}", f"{L}${M0 + 2}"
        if kind == "line":
            f = "=" + cash_lines(s, e)[key]
        elif kind.startswith("sum"):
            _, a, b = kind.split(":")
            keys_in = [k for (r2, k, _, kd) in CF_ROWS if kd == "line" and int(a) <= r2 <= int(b)]
            f = "=" + "+".join(f"{L}{MROW[k]}" for k in keys_in)
        elif kind == "net":
            f = f"={L}{MROW['tot_rec']}+{L}{MROW['tot_direct']}+{L}{MROW['tot_over']}+{L}{MROW['startup']}"
        put(ws, f"{L}{mrow}", f, fmt=USD, font=F_BOLD if kind != "line" else None)
    put(ws, f"{MT}{mrow}", f"=SUM(C{mrow}:{CL(2 + N_MONTHS)}{mrow})", fmt=USD, font=F_BOLD)
    mrow += 1
put(ws, f"B{mrow + 1}", "Check: monthly six-month net equals the weekly six-month net (difference)", font=F_BOLD)
put(ws, f"C{mrow + 1}", f"={MT}{MROW['net']}-{TOT}26", fmt=USD2, font=F_BOLD)
REF["cf_check_month_week"] = f"Cash_Flow!$C${mrow + 1}"
put(ws, f"B{mrow + 2}", "Overhead allocated to drops in the six months (a view, not paid)")
put(ws, f"C{mrow + 2}", f'=SUMIFS({dp("allocations")},{dp("date")},">="&{R("week1_start")},{dp("date")},"<="&{R("horizon_end")})', fmt=USD)
put(ws, f"B{mrow + 3}", "Overhead paid in the six months (Cash_Ledger)")
put(ws, f"C{mrow + 3}", f"=-{TOT}24", fmt=USD)
put(ws, f"B{mrow + 4}", "Overhead not absorbed by drops (paid less allocated)")
put(ws, f"C{mrow + 4}", f"=C{mrow + 3}-C{mrow + 2}", fmt=USD, font=F_BOLD)
REF["cf_alloc"] = f"Cash_Flow!$C${mrow + 2}"
REF["cf_over_paid"] = f"Cash_Flow!$C${mrow + 3}"
REF["cf_unabsorbed"] = f"Cash_Flow!$C${mrow + 4}"
REF.update({"cf_net_total": f"Cash_Flow!${TOT}$26", "cf_rec_plan_total": f"Cash_Flow!${TOT}$9", "cf_over_total": f"Cash_Flow!${TOT}$24",
            "cf_startup_total": f"Cash_Flow!${TOT}$25", "cf_kit_total": f"Cash_Flow!${TOT}$13", "cf_tr_total": f"Cash_Flow!${TOT}$14",
            "cf_proc_total": f"Cash_Flow!${TOT}$16", "cf_mail_total": f"Cash_Flow!${TOT}$15", "cf_direct_act_total": f"Cash_Flow!${TOT}$17",
            "cf_rec_act_total": f"Cash_Flow!${TOT}$10"})
widths(ws, {"A": 2, "B": 58})
for i in range(N_WEEKS + 1):
    ws.column_dimensions[CL(WK0 + i)].width = 9.5
ws.column_dimensions[TOT].width = 12
ws.freeze_panes = "C8"
ch = LineChart()
ch.title = "Cumulative net cash flow by week, before founder cash"
ch.y_axis.title = "USD"
ch.x_axis.title = "Week"
ch.height, ch.width = 7.5, 24
ch.add_data(Reference(ws, min_col=WK0, max_col=WKN, min_row=27, max_row=27), from_rows=True, titles_from_data=False)
ch.set_categories(Reference(ws, min_col=WK0, max_col=WKN, min_row=4, max_row=4))
ch.legend = None
ch.x_axis.tickLblPos = "low"
ch.series[0].smooth = False
ws.add_chart(ch, f"E{M0 + 20}")

# ==========================================================================
# Capital
# ==========================================================================
ws = WS["Capital"]
title(ws, "Capital to the first six months", "The plan's capital table reproduced line by line, and where the model pays each line. The cash flow never reads this tab, so nothing here is counted twice.")
header_row(ws, 4, 2, ["Item (plan capital table)", "Plan low", "Plan high", "Model working figure", "Where the model pays it", "Model cash inside the six months",
                      "Model less plan high", "Reading", "Legal pack status"], height=45)
G_STATUS = "legal pack figures.csv read 2026-10-24"
lg = lambda line: f'SUMIFS({R("LG_amt")},{R("LG_line")},"{line}",{R("LG_date")},">="&{R("week1_start")},{R("LG_date")},"<="&{R("horizon_end")})'
caprows = [
    ("LLC filing and certificate of publication", 250, 250, f"={R('su_llc')}+{R('su_cert')}", "Startup outlays", f"={R('su_llc_cash')}+{R('su_cert_cash')}", "Reproduces.", "verified 2026-10-23 ($200 and $50, dos.ny.gov)"),
    ("Newspaper publication", 250, 2000, f"={R('su_pub')}", "Startup outlays", f"={R('su_pub_cash')}", "Legal pack working figure for New York County; $345 if Albany County is confirmed.", "needs quote: $200 to $2,000, working $1,745"),
    ("General liability insurance, one year", 500, 1500, f"={R('insurance_monthly')}*{R('months_per_year')}", "Overhead (Cash_Ledger, insurance)", "=" + lg("insurance"),
     "The plan's own working figure, about $100 a month, sits inside the range.", "needs quote: $500 to $1,500, working $1,200; bind by 2026-12-21"),
    ("Food warehouse license, if required", 0, 400, f"={R('su_license')}", "Startup outlays", f"={R('su_license_cash')}", "High end until the state answers.", "fee verified 2026-10-23; whether required is unknown"),
    ("Printing and materials", 300, 300, f"={R('su_print')}", "Startup outlays", f"={R('su_print_cash')}", "Startup supplies; per-drop kits are separate.", "plan estimate"),
    ("Software, six months", 360, 360, f"={R('software_monthly')}*COUNTIFS({R('LG_line')},\"software\",{R('LG_amt')},\">0\")", "Overhead (Cash_Ledger, software)", "=" + lg("software"),
     "Six monthly payments inside the window.", "plan estimate"),
    ("Transport, campaigns zero to two", 600, 600, f"=SUM(Drop_PnL!{EC['transport']}{DROP0}:{EC['transport']}{DROP0 + 2})", "Per drop (Drop_PnL transport, first three drops)",
     f"=SUM(Drop_PnL!{EC['transport']}{DROP0}:{EC['transport']}{DROP0 + 2})",
     "Per-drop rates give $120 + $300 + $300 = $720; the plan's $600 lump does not reconcile to its own rates.", "plan estimate"),
    ("Domain and email", 100, 100, f"={R('su_domain')}", "Startup outlays", f"={R('su_domain_cash')}", "Reproduces.", "plan estimate"),
    ("Reserve", 1000, 1000, f"={R('reserve_usd')}", "Not spent; added to capital to commit", None, "Held back, not an outflow.", "plan estimate"),
]
for i, cr in enumerate(caprows):
    rr = 5 + i
    put(ws, f"B{rr}", cr[0], align=WRAP)
    put(ws, f"C{rr}", cr[1], fmt=USD)
    put(ws, f"D{rr}", cr[2], fmt=USD)
    put(ws, f"E{rr}", cr[3], fmt=USD)
    put(ws, f"F{rr}", cr[4], align=WRAP)
    put(ws, f"G{rr}", cr[5], fmt=USD)
    put(ws, f"H{rr}", f"=G{rr}-D{rr}" if cr[5] is not None else None, fmt=USD)
    put(ws, f"I{rr}", cr[6], align=WRAP)
    put(ws, f"J{rr}", cr[7], align=WRAP)
    ws.row_dimensions[rr].height = 32
rt = 5 + len(caprows)   # 14
put(ws, f"B{rt}", "Total (model cash excludes the reserve)", font=F_BOLD)
for L in "CDEG":
    put(ws, f"{L}{rt}", f"=SUM({L}5:{L}{rt - 1})", fmt=USD, font=F_BOLD)
REF["cap_low"] = f"Capital!$C${rt}"
REF["cap_high"] = f"Capital!$D${rt}"
assert rt == 14
section(ws, rt + 2, "Cash the model spends that the plan's capital table leaves out", last_col="J")
extra = [
    ("Attorney hour", 300, 500, f"={R('su_attorney')}", "Startup outlays", f"={R('su_attorney_cash')}", "Legal pack plan estimate. The plan asks for both hours (about $700) before the first invoice."),
    ("Accountant hour", 200, 400, f"={R('su_accountant')}", "Startup outlays", f"={R('su_accountant_cash')}", "Legal pack plan estimate."),
    ("NYS LLC annual filing fee (IT-204-LL)", 25, 25, f"={R('su_it204')}", "Startup outlays", f"={R('su_it204_cash')}", "Legal pack, verified 2026-10-23; accountant confirms whether 2026 is owed."),
    ("Hired and non-owned auto add-on (needs quote)", None, None, f"={R('su_hnoa')}", "Startup outlays", f"={R('su_hnoa_cash')}", "Legal pack: unknown until quoted. Campaign zero's car rides need it."),
    ("Additional-insured endorsements (needs quote)", None, None, f"={R('su_addl_insured')}", "Startup outlays", f"={R('su_addl_insured_cash')}", "Legal pack: zero with a blanket endorsement."),
    ("Trademark application, one class", 350, 850, f"={R('su_tm')}", "Startup outlays (Include = N)", f"={R('su_tm_cash')}", "Legal pack: after campaign zero passes, not in the first six months."),
    ("Storage unit, months inside the window", None, None, None, "Overhead (Cash_Ledger, storage)", "=" + lg("storage"), "Plan's standard drops carry a $75 storage allocation."),
    ("Display kits on scheduled drops", None, None, None, "Per drop", f"=-{R('cf_kit_total')}", "$8 per office per drop."),
    ("Transport on drops after the first three", None, None, None, "Per drop", f"=-{R('cf_tr_total')}-G11", "Direct-ship drops carry $0."),
    ("Card processing", None, None, None, "Per receipt", f"=-{R('cf_proc_total')}", "3% while the processing toggle is on."),
    ("Kit mailing (needs quote)", None, None, None, "Per drop", f"=-{R('cf_mail_total')}", "Blank until quoted."),
    ("Phone", None, None, None, "Overhead (Cash_Ledger, phone)", "=" + lg("phone"), "$0 in the plan (your own phone)."),
]
for i, cr in enumerate(extra):
    rr = rt + 3 + i
    put(ws, f"B{rr}", cr[0], align=WRAP)
    put(ws, f"C{rr}", cr[1], fmt=USD)
    put(ws, f"D{rr}", cr[2], fmt=USD)
    put(ws, f"E{rr}", cr[3], fmt=USD)
    put(ws, f"F{rr}", cr[4], align=WRAP)
    put(ws, f"G{rr}", cr[5], fmt=USD)
    put(ws, f"I{rr}", cr[6], align=WRAP)
re_ = rt + 3 + len(extra)
put(ws, f"B{re_}", "Total model outflows inside the six months (both tables, excluding the reserve)", font=F_BOLD)
put(ws, f"G{re_}", f"=SUM(G5:G{rt - 1})+SUM(G{rt + 3}:G{re_ - 1})", fmt=USD, font=F_BOLD)
put(ws, f"B{re_ + 1}", "Same total read from Cash_Flow (all outflows, plan basis)", font=F_BOLD)
put(ws, f"G{re_ + 1}", f"=-({R('cf_net_total')}-{R('cf_rec_plan_total')}-{R('cf_rec_act_total')})", fmt=USD, font=F_BOLD)
put(ws, f"B{re_ + 2}", "Difference (should be 0 while no drop has actuals)", font=F_BOLD)
put(ws, f"G{re_ + 2}", f"=G{re_}-G{re_ + 1}", fmt=USD2, font=F_BOLD)
REF["cap_check"] = f"Capital!$G${re_ + 2}"
put(ws, f"B{re_ + 4}", "The plan's $3,360 to $6,510 is a budget to commit, not the model's cash need. The model's need is the lowest point of cumulative cash plus the reserve (Cash_Flow and Dashboard), because brand cash arrives before most drop costs.", align=WRAP)
ws.merge_cells(f"B{re_ + 4}:J{re_ + 4}")
ws.row_dimensions[re_ + 4].height = 45
widths(ws, {"A": 2, "B": 40, "C": 10, "D": 10, "E": 14, "F": 30, "G": 16, "H": 14, "I": 48, "J": 40})

# ==========================================================================
# Steady_State (with break-even)
# ==========================================================================
ws = WS["Steady_State"]
title(ws, "Monthly steady state and break-even", "Engine rows below compute one drop; the monthly view multiplies by drops per month and pays overhead once.")
banner(ws, "A3", "Planning estimates, not a forecast. 'Plan reading (e)' reproduces the plan's monthly picture; 'Active scenario' uses the scenario in force on Inputs.", "AM3")
write_engine_header(ws, 6, band_row=5)
SSR = {"plan": 7, "active": 8, "one": 9, "c1": 10, "c2": 11, "r1": 12, "r2": 13, "d1": 14, "d2": 15, "p1": 16, "p2": 17}
storage_glob = f'IF({R("storage_choice")}="unit",1,0)'
base_in = lambda **kw: dict({"date": None, "model": "courier", "tier": "standard", "offices": f"={R('ss_offices')}", "new_offices": 0, "brands": 3,
                             "renewals": 0, "fnd_renewals": 0, "price_std": f"={R('price_std_office')}", "price_fnd": f"={R('price_fnd_office')}",
                             "storage_on": "=" + storage_glob, "proc_on": f"={R('processing_on')}"}, **kw)
eng_cases = [
    ("plan", base_in(id="Plan reading (e): one three-brand courier drop, all new brands", offices=10, storage_on=1, proc_on=1, price_std=150)),
    ("active", base_in(id="Active scenario: one steady-state drop", model=f"={R('ss_model')}", brands=f"={R('sc_ss_brands')}",
                       renewals=f"={R('sc_renewal')}*{EC['brands']}8", price_std=f"={R('sc_price_after')}")),
    ("one", base_in(id="Break-even: one-brand standard courier drop, new brand", brands=1)),
    ("c1", base_in(id="Crossing: courier, 1 new brand", model=f"={R('ss_model')}", brands=1)),
    ("c2", base_in(id="Crossing: courier, 2 new brands", model=f"={R('ss_model')}", brands=2)),
    ("r1", base_in(id="Crossing at the active renewal rate, 1 brand", model=f"={R('ss_model')}", brands=1, renewals=f"={R('sc_renewal')}*{EC['brands']}12")),
    ("r2", base_in(id="Crossing at the active renewal rate, 2 brands", model=f"={R('ss_model')}", brands=2, renewals=f"={R('sc_renewal')}*{EC['brands']}13")),
    ("d1", base_in(id="Crossing: direct-ship, 1 new brand", model="direct-ship", brands=1)),
    ("d2", base_in(id="Crossing: direct-ship, 2 new brands", model="direct-ship", brands=2)),
    ("p1", base_in(id="Price crossing: 3 brands at the first sensitivity price", model=f"={R('ss_model')}", price_std=f"={R('sens_price_start')}")),
    ("p2", base_in(id="Price crossing: 3 brands at the first price plus one step", model=f"={R('ss_model')}", price_std=f"={R('sens_price_start')}+{R('sens_price_step')}")),
]
for key, ins in eng_cases:
    write_engine_row(ws, SSR[key], ins, input_style=(key == "plan"))
for k in ("model", "tier", "brands"):
    pass
E = lambda key, col: f"{EC[col]}{SSR[key]}"
# monthly view
V0 = 20
section(ws, V0, "Monthly steady state", last_col="F")
header_row(ws, V0 + 1, 2, ["Line", "Plan reading (e)", "Active scenario", "Unit", "How it is built"], height=30)
over_paid = f"({R('software_monthly')}+{R('insurance_monthly')}+{R('phone_monthly')}+{R('storage_monthly')}*{storage_glob})"
mv = [
    ("ss_drops", "Drops per month", f"={R('plan_ss_drops')}", f"={R('sc_ss_drops')}", "drops", INT, "Inputs / Scenarios"),
    ("ss_rev", "Revenue", f"=C{{d}}*{E('plan', 'revenue')}", f"=D{{d}}*{E('active', 'revenue')}", "USD per month", USD, "drops x one drop"),
    ("ss_cost", "Hard costs (incl. overhead allocations)", f"=C{{d}}*{E('plan', 'hard_costs')}", f"=D{{d}}*{E('active', 'hard_costs')}", "USD per month", USD, "drops x one drop"),
    ("ss_hours", "Founder hours", f"=C{{d}}*{E('plan', 'hours')}", f"=D{{d}}*{E('active', 'hours')}", "hours per month", HRS, "drops x one drop"),
    ("ss_contrib", "Contribution (plan definition)", "=C{rev}-C{cost}", "=D{rev}-D{cost}", "USD per month", USD, "revenue less hard costs"),
    ("ss_ph", "Contribution per founder hour", '=IF(C{hours}>0,C{contrib}/C{hours},"n/a")', '=IF(D{hours}>0,D{contrib}/D{hours},"n/a")', "USD per hour", PH, ""),
    ("ss_annual", "Contribution per year at this rate", f"=C{{contrib}}*{R('months_per_year')}", f"=D{{contrib}}*{R('months_per_year')}", "USD per year", USD, "before overhead not absorbed and before tax"),
    ("ss_hpw", "Founder hours per week", f"=C{{hours}}/{R('weeks_per_month')}", f"=D{{hours}}/{R('weeks_per_month')}", "hours per week", HRS, "monthly hours / weeks per month"),
    ("ss_over_paid", "Overhead paid per month", "=" + over_paid, "=" + over_paid, "USD per month", USD, "software + insurance + phone + storage if unit"),
    ("ss_over_alloc", "Overhead allocated to drops per month", f"=C{{d}}*{E('plan', 'allocations')}", f"=D{{d}}*{E('active', 'allocations')}", "USD per month", USD, "drops x allocation per drop"),
    ("ss_unabs", "Overhead not absorbed by drops", "=C{op}-C{oa}", "=D{op}-D{oa}", "USD per month", USD, "paid less allocated; zero at two drops a month"),
    ("ss_op_rev", "Office-paid tier revenue", 0, f"={R('sc_op_offices')}*N({R('sc_op_fee')})", "USD per month", USD, "scenario B only"),
    ("ss_op_cost", "Office-paid tier cost to serve (needs quote)", 0, f"={R('sc_op_offices')}*N({R('sc_op_cost')})", "USD per month", USD, "blank until quoted"),
    ("ss_hire_h", "Drop-day hours handed to a hire", 0, f"=IF(D{{d}}>{R('sc_hire_threshold')},D{{d}}*{E('active', 'h_drop_day')},0)", "hours per month", HRS, "scenario A rule: hire above two drops a month"),
    ("ss_hire_cost", "Delivery hire cost", 0, f"=D{{hh}}*N({R('sc_hire_rate')})", "USD per month", USD, ""),
    ("ss_net", "Net monthly contribution after overhead, office tier and hire", "=C{contrib}-C{unabs}+C{oprev}-C{opcost}-C{hcost}", "=D{contrib}-D{unabs}+D{oprev}-D{opcost}-D{hcost}", "USD per month", USD, ""),
    ("ss_net_hours", "Founder hours net of the hire", "=C{hours}-C{hh}", "=D{hours}-D{hh}", "hours per month", HRS, ""),
    ("ss_net_ph", "Net contribution per founder hour", '=IF(C{nh}>0,C{net}/C{nh},"n/a")', '=IF(D{nh}>0,D{net}/D{nh},"n/a")', "USD per hour", PH, ""),
    ("ss_wins", "New brand wins needed per month", f"=C{{d}}*({E('plan', 'brands')}-{E('plan', 'renewals')})", f"=D{{d}}*({E('active', 'brands')}-{E('active', 'renewals')})", "wins", '0.0', "brand slots less renewals"),
    ("ss_conv", "Qualified brand conversations per month", f"=C{{wins}}/{R('close_rate')}", f"=D{{wins}}/{R('close_rate')}", "conversations", '0', "wins / close rate"),
    ("ss_roster", "Office roster so no office gets more than one drop a month", f"=C{{d}}*{E('plan', 'offices')}", f"=D{{d}}*{E('active', 'offices')}", "offices", INT, "drops x offices per drop"),
]
rows_mv = {}
for i, item in enumerate(mv):
    rows_mv[item[0]] = V0 + 2 + i
names = {"d": "ss_drops", "rev": "ss_rev", "cost": "ss_cost", "hours": "ss_hours", "contrib": "ss_contrib", "op": "ss_over_paid", "oa": "ss_over_alloc",
         "unabs": "ss_unabs", "oprev": "ss_op_rev", "opcost": "ss_op_cost", "hh": "ss_hire_h", "hcost": "ss_hire_cost", "net": "ss_net", "nh": "ss_net_hours", "wins": "ss_wins"}
fmtmap = {k: rows_mv[v] for k, v in names.items()}
for item in mv:
    key, lab, fc, fd, unit, fmt, how = item
    rr = rows_mv[key]
    put(ws, f"B{rr}", lab)
    for col, f in (("C", fc), ("D", fd)):
        if isinstance(f, str):
            f = f.format(**fmtmap)
        put(ws, f"{col}{rr}", f, fmt=fmt, font=F_BOLD if key in ("ss_contrib", "ss_ph", "ss_net", "ss_net_ph") else None)
    put(ws, f"E{rr}", unit)
    put(ws, f"F{rr}", how, font=F_NOTE)
    REF[key + "_plan"] = f"Steady_State!$C${rr}"
    REF[key] = f"Steady_State!$D${rr}"
# break-even
B0 = V0 + 2 + len(mv) + 2
section(ws, B0, "Break-even", last_col="F")
header_row(ws, B0 + 1, 2, ["Measure", "Value", "", "Unit", "How it is built"], height=30)
cross_b = lambda a, b: (f'=IF(({EC["contribution"]}{SSR[b]}-{EC["contribution"]}{SSR[a]})-{R("g3_per_hour")}*({EC["hours"]}{SSR[b]}-{EC["hours"]}{SSR[a]})<=0,"never",'
                        f'MAX(0,1+({R("g3_per_hour")}*{EC["hours"]}{SSR[a]}-{EC["contribution"]}{SSR[a]})/(({EC["contribution"]}{SSR[b]}-{EC["contribution"]}{SSR[a]})-{R("g3_per_hour")}*({EC["hours"]}{SSR[b]}-{EC["hours"]}{SSR[a]}))))')
p1, p2 = SSR["p1"], SSR["p2"]
be = [
    ("be_startup", "Startup outlays to recover (one-time cash, Inputs section 11)", f"={R('su_total')}", "USD", USD, "sum of startup cash amounts"),
    ("be_c_one", "Contribution of a one-brand standard courier drop", f"={E('one', 'contribution')}", "USD per campaign", USD, "engine row 9"),
    ("be_c_three", "Contribution per brand on a three-brand courier drop", f"={E('plan', 'contribution')}/{E('plan', 'brands')}", "USD per campaign", USD, "engine row 7 / 3; shared costs split equally"),
    ("be_n_one", "Campaigns to recover startup cash, one-brand drops", f'=IF(C{{c1}}>0,ROUNDUP(C{{s}}/C{{c1}},0),"never")', "campaigns", INT, "startup / contribution, rounded up"),
    ("be_n_three", "Campaigns to recover startup cash, three-brand drops", f'=IF(C{{c3}}>0,ROUNDUP(C{{s}}/C{{c3}},0),"never")', "campaigns", INT, "startup / contribution per brand, rounded up"),
    ("be_c_pre", "One-brand standard drop: contribution before overhead allocations", f"={E('one', 'contribution')}+{E('one', 'allocations')}", "USD per campaign", USD, "revenue less direct costs"),
    ("be_over", "Overhead paid per month", f"={R('ss_over_paid')}", "USD per month", USD, "Monthly steady state"),
    ("be_n_over", "Standard campaigns a month to cover overhead", f'=IF(C{{cp}}>0,ROUNDUP(C{{ov}}/C{{cp}},0),"never")', "campaigns per month", INT, "overhead / contribution before allocations, rounded up"),
    ("be_b_new", "Brands per drop where contribution per hour reaches the Gate 3 target, new brands", cross_b("c1", "c2"), "brands per drop", '0.00', "linear in brands: solved from engine rows 10 and 11"),
    ("be_b_new_int", "Smallest whole number of brands that clears it", f'=IF(ISNUMBER(C{{bn}}),ROUNDUP(C{{bn}},0),"never")', "brands per drop", INT, ""),
    ("be_b_ren", "Same, at the active renewal rate", cross_b("r1", "r2"), "brands per drop", '0.00', "engine rows 12 and 13"),
    ("be_b_dir", "Same, brands ship direct", cross_b("d1", "d2"), "brands per drop", '0.00', "engine rows 14 and 15"),
    ("be_price", "Standard price per office where a three-brand drop reaches the target",
     f'=IF({EC["revenue"]}{p2}={EC["revenue"]}{p1},"never",{EC["price_std"]}{p1}+({R("g3_per_hour")}*{EC["hours"]}{p1}-{EC["contribution"]}{p1})*({EC["price_std"]}{p2}-{EC["price_std"]}{p1})/({EC["contribution"]}{p2}-{EC["contribution"]}{p1}))',
     "USD per office", USD2, "linear in price: engine rows 16 and 17"),
]
rows_be = {item[0]: B0 + 2 + i for i, item in enumerate(be)}
bmap = {"c1": rows_be["be_c_one"], "c3": rows_be["be_c_three"], "s": rows_be["be_startup"], "cp": rows_be["be_c_pre"], "ov": rows_be["be_over"], "bn": rows_be["be_b_new"]}
for item in be:
    key, lab, f, unit, fmt, how = item
    rr = rows_be[key]
    put(ws, f"B{rr}", lab, align=WRAP)
    put(ws, f"C{rr}", f.format(**bmap), fmt=fmt, font=F_BOLD)
    put(ws, f"E{rr}", unit)
    put(ws, f"F{rr}", how, font=F_NOTE)
    REF[key] = f"Steady_State!$C${rr}"
engine_widths(ws)
widths(ws, {"B": 50, "C": 16, "D": 16, "E": 16, "F": 48})
ws.column_dimensions["A"].width = 44
ws.freeze_panes = "B7"

# ==========================================================================
# Sensitivity
# ==========================================================================
ws = WS["Sensitivity"]
title(ws, "Sensitivity tables", "Plain formulas, no data tables. Reference drop: standard tier, steady-state delivery model and offices, storage and processing as set on Inputs.")
banner(ws, "A3", "Each cell recomputes contribution per founder hour from the inputs. Axis starts and steps are on Inputs section 10. A check cell compares the shortcut with the full engine.", "L3")
put(ws, "B5", "Reference-drop components (from Inputs)", font=F_SEC)
comp = [
    ("sx_n", "Offices per drop", f"={R('ss_offices')}", INT),
    ("sx_net", "Revenue kept after card processing", f"=1-{R('processing_rate')}*{R('processing_on')}", PCT1),
    ("sx_extra", "Revenue per brand from offices beyond the package", f"={R('extra_office_price')}*MAX(C6-{R('std_pkg_offices')},0)", USD),
    ("sx_pk", "Package offices priced at the per-office rate", f"=MIN(C6,{R('std_pkg_offices')})", INT),
    ("sx_fixed", "Fixed cost per drop (kits, transport, mailing, allocations)",
     f"=C6*{R('kit_per_office')}+INDEX({R('m_tr_fixed')},MATCH({R('ss_model')},{R('m_keys')},0))+INDEX({R('m_tr_stop')},MATCH({R('ss_model')},{R('m_keys')},0))*C6"
     f"+INDEX({R('m_mail')},MATCH({R('ss_model')},{R('m_keys')},0))*C6+({storage_glob}*{R('storage_monthly')}+{R('software_monthly')}+{R('insurance_monthly')})/{R('alloc_drops_month')}", USD),
    ("sx_card", "Extra card cost per brand beyond the first", f"=C6*N({R('card_extra')})", USD),
    ("sx_fh", "Fixed hours per drop (existing offices, logistics, admin)",
     f"=C6*{R('h_existing_office')}+INDEX({R('m_rk_base')},MATCH({R('ss_model')},{R('m_keys')},0))+INDEX({R('m_dd')},MATCH({R('ss_model')},{R('m_keys')},0))*C6"
     f"+INDEX({R('m_ck')},MATCH({R('ss_model')},{R('m_keys')},0))*C6+{R('admin_per_drop')}", HRS),
    ("sx_hn", "Hours per new brand", f"={R('h_win')}+{R('rk_per_brand')}+{R('rep_per_brand')}", HRS),
    ("sx_hr", "Hours per renewing brand", f"={R('h_renewal')}+{R('rk_per_brand')}+{R('rep_per_brand')}", HRS),
]
for i, (key, lab, f, fmt) in enumerate(comp):
    rr = 6 + i
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f, fmt=fmt)
    REF[key] = f"Sensitivity!$C${rr}"
SX = {k: f"$C${6 + i}" for i, (k, _, _, _) in enumerate(comp)}


def ph_formula(P, b, rr_):
    """contribution per hour for price P, brands b, renewal share rr_ (cell refs)."""
    rev = f"({b}*({P}*{SX['sx_pk']}+{SX['sx_extra']})*{SX['sx_net']}-{SX['sx_fixed']}-{SX['sx_card']}*MAX({b}-1,0))"
    hrs = f"({SX['sx_fh']}+{b}*((1-{rr_})*{SX['sx_hn']}+{rr_}*{SX['sx_hr']}))"
    return f'=IF({hrs}>0,{rev}/{hrs},"n/a")'


NB, NP, NR = 5, 8, 11
T1 = 17
T2 = T1 + NP + 4
T3 = T2 + NR + 4
T4 = T3 + NR + 4
T4_END = T4 + NP
DC_ = T4_END + 3
SXE = DC_ + 7          # engine row used for the cross-check
# cross-check block
put(ws, "E5", "Cross-check with the full engine (current price, active renewal rate)", font=F_SEC)
put(ws, "E6", "Brands used for the check")
as_input(put(ws, "G6", 3))
put(ws, "E7", "Shortcut formula")
put(ws, "G7", ph_formula(R("price_std_office"), "$G$6", R("sc_renewal")), fmt=PH)
put(ws, "E8", f"Full engine (row {SXE})")
put(ws, "G8", f"={EC['per_hour']}{SXE}", fmt=PH)
put(ws, "E9", "Difference (should be 0)")
put(ws, "G9", "=G7-G8", fmt='0.000000', font=F_BOLD)
REF["sx_check"] = "Sensitivity!$G$9"
put(ws, "E10", "Gate 3 target per founder hour (colours below)")
put(ws, "G10", f"={R('g3_per_hour')}", fmt=USD)
# T1 price x brands
put(ws, f"B{T1 - 1}", "Table 1. Contribution per founder hour: price per office (rows) x brands per drop (columns), all brands new", font=F_SEC)
put(ws, f"B{T1}", "Price per office \\ brands", font=F_H, fill=FILL_H)
for j in range(NB):
    L = CL(3 + j)
    put(ws, f"{L}{T1}", f"={R('sens_brands_start')}" if j == 0 else f"={CL(2 + j)}{T1}+{R('sens_brands_step')}", font=F_H, fill=FILL_H, fmt='0')
for i in range(NP):
    rr = T1 + 1 + i
    put(ws, f"B{rr}", f"={R('sens_price_start')}" if i == 0 else f"=B{rr - 1}+{R('sens_price_step')}", fmt=USD, font=F_BOLD)
    for j in range(NB):
        L = CL(3 + j)
        put(ws, f"{L}{rr}", ph_formula(f"$B{rr}", f"{L}${T1}", "0"), fmt=PH)
T1_RNG = f"C{T1 + 1}:{CL(2 + NB)}{T1 + NP}"
ws.conditional_formatting.add(T1_RNG, CellIsRule(operator="greaterThanOrEqual", formula=["$G$10"], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(T1_RNG, CellIsRule(operator="lessThan", formula=["$G$10"], fill=PatternFill("solid", fgColor="FCE4D6")))
# T2 renewal x brands
put(ws, f"B{T2 - 1}", "Table 2. Contribution per founder hour: renewal rate (rows) x brands per drop (columns), at the standard price on Inputs", font=F_SEC)
put(ws, f"B{T2}", "Renewal rate \\ brands", font=F_H, fill=FILL_H)
for j in range(NB):
    L = CL(3 + j)
    put(ws, f"{L}{T2}", f"={R('sens_brands_start')}" if j == 0 else f"={CL(2 + j)}{T2}+{R('sens_brands_step')}", font=F_H, fill=FILL_H, fmt='0')
for i in range(NR):
    rr = T2 + 1 + i
    put(ws, f"B{rr}", f"={R('sens_renew_start')}" if i == 0 else f"=B{rr - 1}+{R('sens_renew_step')}", fmt=PCT, font=F_BOLD)
    for j in range(NB):
        L = CL(3 + j)
        put(ws, f"{L}{rr}", ph_formula(R("price_std_office"), f"{L}${T2}", f"$B{rr}"), fmt=PH)
T2_RNG = f"C{T2 + 1}:{CL(2 + NB)}{T2 + NR}"
ws.conditional_formatting.add(T2_RNG, CellIsRule(operator="greaterThanOrEqual", formula=["$G$10"], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(T2_RNG, CellIsRule(operator="lessThan", formula=["$G$10"], fill=PatternFill("solid", fgColor="FCE4D6")))
# T3 renewal -> steady state monthly
put(ws, f"B{T3 - 1}", "Table 3. Renewal rate and the monthly steady state (scenario drops per month, brands per drop and post-decision price)", font=F_SEC)
header_row(ws, T3, 2, ["Renewal rate", "New brand wins per month", "Qualified conversations per month", "Founder hours per month", "Contribution per month", "Contribution per founder hour"], height=45)
ssd, ssb, ssp = R("sc_ss_drops"), R("sc_ss_brands"), R("sc_price_after")
for i in range(NR):
    rr = T3 + 1 + i
    put(ws, f"B{rr}", f"={R('sens_renew_start')}" if i == 0 else f"=B{rr - 1}+{R('sens_renew_step')}", fmt=PCT, font=F_BOLD)
    put(ws, f"C{rr}", f"={ssd}*{ssb}*(1-B{rr})", fmt='0.0')
    put(ws, f"D{rr}", f"=C{rr}/{R('close_rate')}", fmt='0')
    put(ws, f"E{rr}", f"={ssd}*IF({ssb}>0,{SX['sx_fh']}+{ssb}*((1-B{rr})*{SX['sx_hn']}+B{rr}*{SX['sx_hr']}),0)", fmt=HRS)
    put(ws, f"F{rr}", f"={ssd}*IF({ssb}>0,{ssb}*({ssp}*{SX['sx_pk']}+{SX['sx_extra']})*{SX['sx_net']}-{SX['sx_fixed']}-{SX['sx_card']}*MAX({ssb}-1,0),0)", fmt=USD)
    put(ws, f"G{rr}", f'=IF(E{rr}>0,F{rr}/E{rr},"n/a")', fmt=PH)
# T4 price -> steady state
put(ws, f"B{T4 - 1}", "Table 4. Price per office and the monthly steady state (scenario drops per month, brands per drop and renewal rate)", font=F_SEC)
header_row(ws, T4, 2, ["Price per office", "Revenue per month", "Contribution per month", "Founder hours per month", "Contribution per founder hour"], height=45)
ssr = R("sc_renewal")
for i in range(NP):
    rr = T4 + 1 + i
    put(ws, f"B{rr}", f"={R('sens_price_start')}" if i == 0 else f"=B{rr - 1}+{R('sens_price_step')}", fmt=USD, font=F_BOLD)
    put(ws, f"C{rr}", f"={ssd}*{ssb}*(B{rr}*{SX['sx_pk']}+{SX['sx_extra']})", fmt=USD)
    put(ws, f"D{rr}", f"={ssd}*IF({ssb}>0,{ssb}*(B{rr}*{SX['sx_pk']}+{SX['sx_extra']})*{SX['sx_net']}-{SX['sx_fixed']}-{SX['sx_card']}*MAX({ssb}-1,0),0)", fmt=USD)
    put(ws, f"E{rr}", f"={ssd}*IF({ssb}>0,{SX['sx_fh']}+{ssb}*((1-{ssr})*{SX['sx_hn']}+{ssr}*{SX['sx_hr']}),0)", fmt=HRS)
    put(ws, f"F{rr}", f'=IF(E{rr}>0,D{rr}/E{rr},"n/a")', fmt=PH)
# direction checks
put(ws, f"B{DC_}", "Direction checks (each should be 0)", font=F_SEC)
viol_price = "+".join(f"SUMPRODUCT(({CL(3 + j)}{T1 + 2}:{CL(3 + j)}{T1 + NP}-{CL(3 + j)}{T1 + 1}:{CL(3 + j)}{T1 + NP - 1}<=0)*1)" for j in range(NB))
viol_brand = "+".join(f"SUMPRODUCT((D{T1 + 1 + i}:{CL(2 + NB)}{T1 + 1 + i}-C{T1 + 1 + i}:{CL(1 + NB)}{T1 + 1 + i}<=0)*1)" for i in range(NP))
viol_renew = "+".join(f"SUMPRODUCT(({CL(3 + j)}{T2 + 2}:{CL(3 + j)}{T2 + NR}-{CL(3 + j)}{T2 + 1}:{CL(3 + j)}{T2 + NR - 1}<0)*({CL(3 + j)}{T2 + 1}:{CL(3 + j)}{T2 + NR - 1}>0))" for j in range(NB))
put(ws, f"B{DC_ + 1}", "Table 1: cells where a higher price does not raise contribution per hour")
put(ws, f"C{DC_ + 1}", "=" + viol_price, fmt=INT, font=F_BOLD)
put(ws, f"B{DC_ + 2}", "Table 1: cells where one more brand does not raise contribution per hour")
put(ws, f"C{DC_ + 2}", "=" + viol_brand, fmt=INT, font=F_BOLD)
put(ws, f"B{DC_ + 3}", "Table 2: cells where a higher renewal rate lowers a positive contribution per hour")
put(ws, f"C{DC_ + 3}", "=" + viol_renew, fmt=INT, font=F_BOLD)
REF.update({"sx_viol_price": f"Sensitivity!$C${DC_ + 1}", "sx_viol_brand": f"Sensitivity!$C${DC_ + 2}", "sx_viol_renew": f"Sensitivity!$C${DC_ + 3}"})
# engine row for the cross-check
put(ws, f"A{SXE - 2}", "Full-engine row used by the cross-check above", font=F_SEC)
write_engine_header(ws, SXE - 1)
write_engine_row(ws, SXE, {"id": "Check: steady-state model, current price, active renewal rate", "date": None, "model": f"={R('ss_model')}",
                           "tier": "standard", "offices": f"={R('ss_offices')}", "new_offices": 0, "brands": "=$G$6",
                           "renewals": f"={R('sc_renewal')}*{EC['brands']}{SXE}", "fnd_renewals": 0, "price_std": f"={R('price_std_office')}",
                           "price_fnd": f"={R('price_fnd_office')}", "storage_on": "=" + storage_glob, "proc_on": f"={R('processing_on')}"})
widths(ws, {"A": 3, "B": 50, "C": 14, "D": 14, "E": 16, "F": 16, "G": 16})
for i in range(8, 40):
    ws.column_dimensions[CL(i)].width = 11

# ==========================================================================
# Plan_Check
# ==========================================================================
ws = WS["Plan_Check"]
title(ws, "Plan check: the plan's figures reproduced by the model", "Each case runs through the same engine as the drops. Plan figures are typed from plan.md for comparison only.")
banner(ws, "A3", "Reproduction holds while inputs equal the plan defaults (Inputs 'Changed' column). If you change an input, a 'differs' here is expected and is not an error.", "AM3")
write_engine_header(ws, 6, band_row=5)
pc_cols = ["Plan revenue", "Plan hard costs", "Plan founder hours", "Plan contribution", "Plan per founder hour", "Money tolerance", "Hours tolerance", "Per-hour tolerance", "Kind", "Status", "Plan reading"]
PCC = {}
st = openpyxl.utils.column_index_from_string(LAST_ENGINE_COL) + 2
for i, h in enumerate(pc_cols):
    PCC[h] = CL(st + i)
    put(ws, f"{CL(st + i)}6", h, font=F_H, fill=FILL_H, align=CENTER, border=BOX)
pc_in = lambda **kw: dict({"date": None, "tier": "standard", "offices": 10, "new_offices": 0, "renewals": 0, "fnd_renewals": 0,
                           "price_std": 150, "price_fnd": 120, "storage_on": 1, "proc_on": 1}, **kw)
PC = [
    ("P1", pc_in(id="1. Campaign zero: 2 founding brands, 5 offices, you deliver", model="founder", tier="founding", offices=5, new_offices=5, brands=2, storage_on=0),
     (1200, 280, 57, 920, 16), (5, 0.01, 0.5), "reproduce", "(b) storage $0 at home, transport $120, processing 3%: $276, which the plan rounds to $280."),
    ("P2", pc_in(id="2. Standard drop, 1 brand, 10 offices, courier", model="courier", brands=1), (1500, 580, 35, 920, 26), (5, 0.01, 0.5), "reproduce", ""),
    ("P3", pc_in(id="3. Standard drop, 3 brands, 10 offices, courier", model="courier", brands=3), (4500, 670, 52, 3830, 74), (5, 0.01, 0.5), "reproduce",
     "(a) kit $8 per office per drop. Per brand it would be $830."),
    ("P4", pc_in(id="4. Standard drop, 3 brands, brands ship direct", model="direct-ship", brands=3), (4500, 370, 45, 4130, 92), (5, 0.01, 0.5), "reproduce",
     "(c) keeps the $75 storage allocation and $0 transport."),
    ("P5", pc_in(id="5. Standard drop, 3 brands at $2,000 each", model="courier", brands=3, price_std=200), (6000, 715, 52, 5285, 102), (5, 0.01, 0.5), "reproduce", ""),
    ("P6", pc_in(id="6. Three-brand drop at $1,000 each, no processing", model="courier", brands=3, price_std=100, proc_on=0), (None, None, 52, None, 47), (5, 0.01, 0.5), "reproduce",
     "(d) $2,465 / 52 h = $47.4. The plan's 'about $47' assumes no card processing."),
    ("P6b", pc_in(id="6b. Same at $1,000 each with 3% processing", model="courier", brands=3, price_std=100, proc_on=1), (None, None, 52, None, 47), (5, 0.01, 0.5), "contrast",
     "(d) with processing it is $45.7, so the plan's $47 is the no-processing reading."),
    ("E1", pc_in(id="Edge: zero brands", model="courier", brands=0), (0, 0, 0, 0, None), (0.01, 0.01, 0.01), "edge", "A drop with no brand does not run: no cost, no hours, per hour 'n/a'."),
    ("E2", pc_in(id="Edge: one office, one brand, courier", model="courier", offices=1, brands=1), (150, 197.5, 15.2, -47.5, -3.125), (0.01, 0.01, 0.01), "edge", "Expected values worked by hand: $8 kit + $30 courier + $4.50 processing + $155 allocations; 15.2 hours. Finite, negative per hour."),
    ("E3", pc_in(id="Edge: 100% renewal, 3 brands", model="courier", brands=3, renewals=3), (4500, 670, 40, 3830, 95.75), (0.01, 0.01, 0.01), "edge", "Expected by hand: brand sales 3 x 2 h = 6 h instead of 18 h, so 40 hours."),
    ("E4", pc_in(id="Edge: new founding brand on a 10-office drop", model="courier", tier="founding", brands=1), (1350, None, None, None, None), (0.01, 0.01, 0.01), "edge",
     "$600 for 5 offices plus 5 extra offices at $150."),
]
PCR = {}
for i, (key, ins, plan, tol, kind, reading) in enumerate(PC):
    rr = 7 + i
    PCR[key] = rr
    write_engine_row(ws, rr, ins, input_style=True)
    for h, v in zip(pc_cols[:5], plan):
        if v is not None:
            put(ws, f"{PCC[h]}{rr}", v, fmt=PH if "hour" in h and "hours" not in h else (HRS if "hours" in h else USD))
    put(ws, f"{PCC['Money tolerance']}{rr}", tol[0], fmt=USD2)
    put(ws, f"{PCC['Hours tolerance']}{rr}", tol[1], fmt='0.00')
    put(ws, f"{PCC['Per-hour tolerance']}{rr}", tol[2], fmt='0.00')
    put(ws, f"{PCC['Kind']}{rr}", kind)
    put(ws, f"{PCC['Plan reading']}{rr}", reading, align=WRAP)
    pr_, pt, ph_ = PCC["Plan revenue"], PCC["Money tolerance"], PCC["Per-hour tolerance"]
    tests = []
    for h, k in (("Plan revenue", "revenue"), ("Plan hard costs", "hard_costs"), ("Plan contribution", "contribution")):
        tests.append(f'IF({PCC[h]}{rr}="",TRUE,ABS({EC[k]}{rr}-{PCC[h]}{rr})<={pt}{rr})')
    tests.append(f'IF({PCC["Plan founder hours"]}{rr}="",TRUE,ABS({EC["hours"]}{rr}-{PCC["Plan founder hours"]}{rr})<={PCC["Hours tolerance"]}{rr})')
    tests.append(f'IF({PCC["Plan per founder hour"]}{rr}="",TRUE,IF(ISNUMBER({EC["per_hour"]}{rr}),ABS({EC["per_hour"]}{rr}-{PCC["Plan per founder hour"]}{rr})<={ph_}{rr},FALSE))')
    allok = "AND(" + ",".join(tests) + ")"
    if kind == "edge":
        put(ws, f"{PCC['Status']}{rr}", f'=IF({allok},"behaves","check")', font=F_BOLD)
    else:
        put(ws, f"{PCC['Status']}{rr}", f'=IF({PCC["Kind"]}{rr}="contrast",IF({allok},"matches","differs, as expected"),IF({allok},"reproduces","differs"))', font=F_BOLD)
    ws.row_dimensions[rr].height = 30
ok_cf(ws, f"{PCC['Status']}7:{PCC['Status']}{7 + len(PC) - 1}", good='"reproduces"', bad=['"differs"', '"check"'])
ok_cf(ws, f"{PCC['Status']}7:{PCC['Status']}{7 + len(PC) - 1}", good='"behaves"')
REF["pc_status"] = f"Plan_Check!${PCC['Status']}$7:${PCC['Status']}${7 + 6}"
# hours table reproduction
H0 = 7 + len(PC) + 2
section(ws, H0, "The plan's founder-hour table, activity by activity", last_col="L")
header_row(ws, H0 + 1, 1, ["Activity", "Plan: campaign zero", "Model", "Plan: 1-brand drop", "Model", "Plan: 3-brand drop", "Model", "Plan: 3-brand, direct ship", "Model", "All match?"], height=40)
put(ws, f"K{H0 + 1}", "Tolerance (h)", font=F_BOLD)
put(ws, f"L{H0 + 1}", 0.01, fmt='0.00')
plan_hours = {"brand_sales": (20, 6, 18, 18), "office_coordination": (20, 10, 10, 10), "receiving_kitting": (3, 3, 4, 2), "drop_day": (5, 8, 8, 3),
              "checks_pickup": (3, 4, 4, 4), "reporting_debriefs": (4, 2, 6, 6), "admin_invoicing": (2, 2, 2, 2)}
hcol = {"brand_sales": "h_brand_sales", "office_coordination": "h_office", "receiving_kitting": "h_receiving", "drop_day": "h_drop_day",
        "checks_pickup": "h_checks", "reporting_debriefs": "h_reporting", "admin_invoicing": "h_admin"}
for i, key in enumerate(ACT_KEYS + ["total"]):
    rr = H0 + 2 + i
    put(ws, f"A{rr}", key, font=F_BOLD if key == "total" else None)
    vals = plan_hours.get(key, (57, 35, 52, 45))
    for j, (case, pv) in enumerate(zip(("P1", "P2", "P3", "P4"), vals)):
        put(ws, f"{CL(2 + 2 * j)}{rr}", pv, fmt=HRS)
        col = EC[hcol[key]] if key != "total" else EC["hours"]
        put(ws, f"{CL(3 + 2 * j)}{rr}", f"={col}{PCR[case]}", fmt=HRS)
    put(ws, f"J{rr}", f'=IF(AND(ABS(B{rr}-C{rr})<=$L${H0 + 1},ABS(D{rr}-E{rr})<=$L${H0 + 1},ABS(F{rr}-G{rr})<=$L${H0 + 1},ABS(H{rr}-I{rr})<=$L${H0 + 1}),"yes","no")', font=F_BOLD)
HT_END = H0 + 2 + len(ACT_KEYS)
ok_cf(ws, f"J{H0 + 2}:J{HT_END}", good='"yes"', bad=['"no"'])
REF["pc_hours_match"] = f"Plan_Check!$J${H0 + 2}:$J${HT_END}"
# reconciliation table
Q0 = HT_END + 3
section(ws, Q0, "Reconciliation: plan figure, model figure, difference, reason", last_col="L")
header_row(ws, Q0 + 1, 1, ["#", "Plan statement (plan.md)", "Plan figure", "Model figure", "Difference", "Tolerance", "Status", "Reason (plan reading, not a fudge)"], height=32)
pcr = lambda case, col: f"={EC[col]}{PCR[case]}"
recon = [
    ("Campaign zero hard costs", 280, pcr("P1", "hard_costs"), 5, "(b) $40 kits + $120 transport + $0 storage + $30 software + $50 insurance + $36 processing = $276; the plan rounds to $280.", USD),
    ("Campaign zero contribution", 920, pcr("P1", "contribution"), 5, "(b) $1,200 - $276 = $924.", USD),
    ("Campaign zero per founder hour", 16, pcr("P1", "per_hour"), 0.5, "(b) $924 / 57 h = $16.2.", PH),
    ("Three-brand courier hard costs", 670, pcr("P3", "hard_costs"), 5, "(a) one $8 kit per office per drop: $80, not $240.", USD),
    ("Three-brand courier per founder hour ('about $74')", 74, pcr("P3", "per_hour"), 0.5, "$3,830 / 52 h = $73.7.", PH),
    ("One-brand drop per founder hour ('about $26')", 26, pcr("P2", "per_hour"), 0.5, "$920 / 35 h = $26.3.", PH),
    ("Direct-ship hard costs", 370, pcr("P4", "hard_costs"), 5, "(c) keeps $75 storage, $0 transport.", USD),
    ("$2,000 each per founder hour", 102, pcr("P5", "per_hour"), 0.5, "$5,285 / 52 h = $101.6.", PH),
    ("At $1,000 'about $47 an hour'", 47, pcr("P6", "per_hour"), 0.5, "(d) no card processing: $2,465 / 52 h = $47.4.", PH),
    ("At $1,000 with processing", 47, pcr("P6b", "per_hour"), 0.5, "(d) with 3% processing: $2,375 / 52 h = $45.7. Shown as a contrast; differs by design.", PH),
    ("Monthly revenue at steady state", 9000, f"={R('ss_rev_plan')}", 25, "(e) 2 x the three-brand courier drop.", USD),
    ("Monthly hard costs ('about $1,350')", 1350, f"={R('ss_cost_plan')}", 25, "(e) 2 x $670 = $1,340; the plan rounds to $1,350.", USD),
    ("Monthly founder hours ('about 104')", 104, f"={R('ss_hours_plan')}", 0.01, "(e) 2 x 52 h.", HRS),
    ("Monthly contribution ('roughly $7,650')", 7650, f"={R('ss_contrib_plan')}", 25, "(e) $9,000 - $1,340 = $7,660; the plan rounds to $7,650.", USD),
    ("A year at that rate ('about $90,000')", 90000, f"={R('ss_annual_plan')}", 5000, "$7,660 x 12 = $91,920, before overhead and tax.", USD),
    ("Brand wins a month ('six')", 6, f"={R('ss_wins_plan')}", 0.01, "All brands new in the plan's picture.", '0.0'),
    ("Qualified conversations a month ('about 30')", 30, f"={R('ss_conv_plan')}", 0.01, "6 wins / 20% close rate.", '0'),
    ("Roster ('about 20 offices')", 20, f"={R('ss_roster_plan')}", 0.01, "2 drops x 10 offices, one drop per office a month.", '0'),
    ("Fixed overhead a month ('$200 to $350'): midpoint, tolerance half the range", 275, f"={R('ss_over_paid_plan')}", 75, "$60 software + $100 insurance + $150 storage + $0 phone = $310, inside the range. With home storage: $160, below it.", USD),
    ("Standard campaigns a month to cover overhead ('one')", 1, f"={R('be_n_over')}", 0.01, "$310 / $1,075 contribution before allocations, rounded up.", '0'),
    ("Hours per brand win ('six')", 6, f"={R('h_win')}", 0.01, "5 conversations x 0.75 h + 2.25 h paperwork at a 20% close rate.", HRS),
    ("Capital, low end", 3360, f"={R('cap_low')}", 0.01, "Sum of the plan's low column.", USD),
    ("Capital, high end", 6510, f"={R('cap_high')}", 0.01, "Sum of the plan's high column.", USD),
    ("Software, six months", 360, "=Capital!G10", 0.01, "Six $60 payments inside the window.", USD),
    ("Transport, campaigns zero to two", 600, "=Capital!G11", 0.01, "Per-drop rates give $720; the plan's lump does not reconcile to its own rates. The model keeps the rates (more conservative by $120).", USD),
]
for i, (lab, plan_v, model_f, tol, reason, fmt) in enumerate(recon):
    rr = Q0 + 2 + i
    put(ws, f"A{rr}", i + 1)
    put(ws, f"B{rr}", lab, align=WRAP)
    put(ws, f"C{rr}", plan_v, fmt=fmt)
    put(ws, f"D{rr}", model_f, fmt=fmt)
    put(ws, f"E{rr}", f"=D{rr}-C{rr}", fmt=fmt)
    put(ws, f"F{rr}", tol, fmt=fmt)
    put(ws, f"G{rr}", f'=IF(ABS(E{rr})<=F{rr},"within tolerance","differs: see reason")', font=F_BOLD)
    put(ws, f"H{rr}", reason, align=WRAP)
    ws.merge_cells(f"H{rr}:N{rr}")
    ws.row_dimensions[rr].height = 30
Q_END = Q0 + 2 + len(recon) - 1
ok_cf(ws, f"G{Q0 + 2}:G{Q_END}", good='"within tolerance"', bad=['"differs: see reason"'])
REF["pc_recon_status"] = f"Plan_Check!$G${Q0 + 2}:$G${Q_END}"
REF["pc_recon_rows"] = (Q0 + 2, Q_END)
engine_widths(ws)
ws.column_dimensions["A"].width = 44
ws.column_dimensions["B"].width = 44
for h in pc_cols:
    ws.column_dimensions[PCC[h]].width = 12
ws.column_dimensions[PCC["Plan reading"]].width = 60
ws.column_dimensions[PCC["Status"]].width = 16
ws.column_dimensions["H"].width = 14
ws.freeze_panes = "B7"
PC_ROWS = PCR

# ==========================================================================
# Calculator
# ==========================================================================
ws = WS["Calculator"]
title(ws, "Drop calculator", "Pick any tier, delivery model, office count and brand count. It runs the same engine as the drops and does not change the model.")
banner(ws, "A3", "To test a price: type it in 'Standard price per office' below (or on Inputs to move the whole model). Read 'Contribution per founder hour'.", "F3")
put(ws, "B5", "Your drop", font=F_SEC)
calc_in = [
    ("tier", "Tier", "standard", "L_tiers"), ("model", "Delivery model", "courier", "L_models"), ("offices", "Offices", 10, None),
    ("new_offices", "of which new offices", 0, None), ("brands", "Brands", 3, None), ("renewals", "of which renewals", 0, None),
    ("fnd_renewals", "of which founding-rate renewals", 0, None), ("price_std", "Standard price per office (blank = Inputs)", None, None),
    ("price_fnd", "Founding price per office (blank = Inputs)", None, None), ("storage", "Storage allocated? Y/N (blank = Inputs choice)", None, "L_yn"),
    ("proc", "Card processing? Y/N (blank = Inputs toggle)", None, "L_yn"),
]
CI = {}
for i, (k, lab, v, vl) in enumerate(calc_in):
    rr = 6 + i
    put(ws, f"B{rr}", lab)
    c = put(ws, f"C{rr}", v, fmt=USD if "price" in k else None)
    as_input(c)
    if "price" in k:
        c.number_format = USD
    if vl:
        add_list_validation(ws, f"C{rr}", "=" + R(vl))
    CI[k] = f"$C${rr}"
ER = 40
put(ws, f"A{ER - 3}", "Engine row: the same formulas as every row on Drop_PnL. Read-only; the result table above reads it.", font=F_SEC)
write_engine_header(ws, ER - 1)
write_engine_row(ws, ER, {
    "id": "Calculator drop", "date": None, "model": f"={CI['model']}", "tier": f"={CI['tier']}", "offices": f"=N({CI['offices']})",
    "new_offices": f"=N({CI['new_offices']})", "brands": f"=N({CI['brands']})", "renewals": f"=N({CI['renewals']})", "fnd_renewals": f"=N({CI['fnd_renewals']})",
    "price_std": f'=IF({CI["price_std"]}="",{R("price_std_office")},{CI["price_std"]})',
    "price_fnd": f'=IF({CI["price_fnd"]}="",{R("price_fnd_office")},{CI["price_fnd"]})',
    "storage_on": f'=IF({CI["storage"]}="",{storage_glob},IF({CI["storage"]}="Y",1,0))',
    "proc_on": f'=IF({CI["proc"]}="",{R("processing_on")},IF({CI["proc"]}="Y",1,0))',
})
put(ws, "E5", "Result", font=F_SEC)
header_row(ws, 6, 5, ["Line", "Whole drop", "Per brand (equal split of shared costs)"], height=30)
res = [("Revenue", "revenue", USD), ("Display kits", "kit", USD), ("Transport", "transport", USD), ("Kit mailing", "kit_mail", USD),
       ("Card processing", "processing", USD), ("Storage allocation", "storage_alloc", USD), ("Software allocation", "software_alloc", USD),
       ("Insurance allocation", "insurance_alloc", USD), ("Hard costs", "hard_costs", USD), ("Contribution", "contribution", USD),
       ("brand_sales (h)", "h_brand_sales", HRS), ("office_coordination (h)", "h_office", HRS), ("receiving_kitting (h)", "h_receiving", HRS),
       ("drop_day (h)", "h_drop_day", HRS), ("checks_pickup (h)", "h_checks", HRS), ("reporting_debriefs (h)", "h_reporting", HRS),
       ("admin_invoicing (h)", "h_admin", HRS), ("Founder hours", "hours", HRS), ("Contribution per founder hour", "per_hour", PH)]
for i, (lab, k, fmt) in enumerate(res):
    rr = 7 + i
    bold = k in ("revenue", "hard_costs", "contribution", "hours", "per_hour")
    put(ws, f"E{rr}", lab, font=F_BOLD if bold else None)
    put(ws, f"F{rr}", f"={EC[k]}{ER}", fmt=fmt, font=F_BOLD if bold else None, fill=FILL_KEY if k == "per_hour" else None)
    if k != "per_hour":
        put(ws, f"G{rr}", f'=IF({EC["brands"]}{ER}>0,F{rr}/{EC["brands"]}{ER},"")', fmt=fmt)
    else:
        put(ws, f"G{rr}", f"=F{rr}", fmt=fmt)
rr = 7 + len(res)
put(ws, f"E{rr}", "Against the Gate 3 target")
put(ws, f"F{rr}", f'=IF(ISNUMBER(F{rr - 1}),IF(F{rr - 1}>={R("g3_per_hour")},"at or above target","below target"),"n/a")', font=F_BOLD)
put(ws, f"E{rr + 1}", "Units each brand ships (incl. reserve)")
put(ws, f"F{rr + 1}", f"={EC['offices']}{ER}*{R('units_per_office')}*(1+{R('reserve_share')})", fmt='#,##0')
put(ws, f"E{rr + 3}", "Per-brand column: revenue and processing are averaged across brands, and shared costs and hours (kits, transport, allocations, office and drop-day time) "
                      "are split equally. Brand sales and reporting hours are per brand already.", align=WRAP)
ws.merge_cells(f"E{rr + 3}:G{rr + 3}")
ws.row_dimensions[rr + 3].height = 60
engine_widths(ws)
widths(ws, {"A": 3, "B": 44, "C": 14, "D": 3, "E": 30, "F": 16, "G": 22})

# ==========================================================================
# Checks
# ==========================================================================
ws = WS["Checks"]
title(ws, "Model checks", "Integrity checks must always pass. Plan-reproduction checks pass while inputs equal the plan defaults. Data checks flag bad rows in the logs.")
header_row(ws, 4, 1, ["#", "Area", "Check", "Value", "Pass (1/0)", "Note"], height=30)
put(ws, "C3", "Tolerance used by the checks below (rounding)", font=F_BOLD)
as_input(put(ws, "D3", 0.01, fmt='0.00'))
REF["ck_tol"] = "Checks!$D$3"
err_rngs = [f"Drop_PnL!A{DROP0}:{CT['basis']}{DROPN + 1}", f"Plan_Check!A7:{LAST_ENGINE_COL}{7 + len(PC) - 1}", f"Steady_State!A7:{LAST_ENGINE_COL}17",
            f"Steady_State!B22:D{B0 + 20}", f"Cash_Flow!C5:{TOT}43", f"Cash_Flow!C{M0}:{MT}{mrow + 4}", f"Sensitivity!B6:G{T4_END}", f"Sensitivity!A{SXE}:{LAST_ENGINE_COL}{SXE}",
            f"Calculator!A{ER}:{LAST_ENGINE_COL}{ER}", "Drop_Actuals!A7:AL18", "Schedule!A7:T18", f"Inputs!A5:R{sun + 3}", "Scenarios!C10:H21",
            "Capital!B5:J36", f"Hours_Log!H5:R{wl + 5}", "Pipeline!T5:V22", "Dashboard!A24:L110"]
n_err = "+".join(f"SUMPRODUCT(ISERROR({r_})*1)" for r_ in err_rngs)
sched_bad = f'COUNTIF({R("sched_check")},"check")+COUNTIF({R("sched_check")},"date missing")'
nf = f"SUMPRODUCT((Drop_PnL!{EC['tier']}{DROP0}:{EC['tier']}{DROPN}=\"founding\")*Drop_PnL!{EC['new_fnd']}{DROP0}:{EC['new_fnd']}{DROPN})"
fr = f"SUM(Drop_PnL!{EC['fnd_renewals']}{DROP0}:{EC['fnd_renewals']}{DROPN})"
dates_asc = "+".join(f'IF(AND(Schedule!E{r_ + 1}<>"",Schedule!E{r_}<>""),IF(Schedule!E{r_ + 1}<Schedule!E{r_},1,0),0)' for r_ in range(DROP0, DROPN))
pr1 = f"Plan_Check!{{c}}{PCR['E1']}"
checks = [
    ("Integrity", "No formula errors anywhere in the model's output ranges", "=" + n_err, "=IF(D{r}=0,1,0)", "Counts #N/A, #VALUE!, #DIV/0! and other errors."),
    ("Integrity", "Weekly and monthly cash flows agree (difference)", f"={R('cf_check_month_week')}", "=IF(ABS(D{r})<=$D$3,1,0)", "Two independent SUMIFS passes over the same sources."),
    ("Integrity", "Overhead paid in the cash flow equals the overhead ledger", f"={R('cf_over_paid')}-{R('LG_total')}", "=IF(ABS(D{r})<=$D$3,1,0)", "Allocations never reach the cash flow."),
    ("Integrity", "Planned receipts in the cash flow equal the drops' payments inside the window",
     f'={R("cf_rec_plan_total")}-(' + "+".join(f'SUMIFS({dp(a)},{dp(d)},">="&{R("week1_start")},{dp(d)},"<="&{R("horizon_end")},{dp("actuals_in")},"N")' for a, d in (("pay_fnd_amt", "pay_fnd_date"), ("pay_dep_amt", "pay_dep_date"), ("pay_bal_amt", "pay_bal_date"))) + ")",
     "=IF(ABS(D{r})<=$D$3,1,0)", ""),
    ("Integrity", "Every scheduled drop is paid in full: payments equal revenue", f"=SUM({dp('pay_fnd_amt')})+SUM({dp('pay_dep_amt')})+SUM({dp('pay_bal_amt')})-SUM({dp('revenue')})", "=IF(ABS(D{r})<=$D$3,1,0)", ""),
    ("Integrity", "Processing on payments equals processing on revenue", f"=SUM({dp('proc_fnd')})+SUM({dp('proc_dep')})+SUM({dp('proc_bal')})-SUM({dp('processing')})", "=IF(ABS(D{r})<=$D$3,1,0)", ""),
    ("Integrity", "Capital tab outflows equal Cash_Flow outflows", f"={R('cap_check')}", '=IF(OR(ABS(D{r})<=$D$3,COUNTIF(' + R("sched_actuals") + ',"Y")>0),1,0)', "Holds while no drop has actuals."),
    ("Integrity", "Sensitivity shortcut equals the full engine", f"={R('sx_check')}", "=IF(ABS(D{r})<=$D$3,1,0)", ""),
    ("Integrity", "Sensitivity: higher price never lowers contribution per hour", f"={R('sx_viol_price')}", "=IF(D{r}=0,1,0)", ""),
    ("Integrity", "Sensitivity: one more brand always raises contribution per hour", f"={R('sx_viol_brand')}", "=IF(D{r}=0,1,0)", ""),
    ("Integrity", "Sensitivity: higher renewal never lowers a positive contribution per hour", f"={R('sx_viol_renew')}", "=IF(D{r}=0,1,0)", ""),
    ("Integrity", "Edge: zero brands gives zero revenue, cost and hours, and 'n/a'",
     f'=ABS({pr1.format(c=EC["revenue"])})+ABS({pr1.format(c=EC["hard_costs"])})+ABS({pr1.format(c=EC["hours"])})+IF({pr1.format(c=EC["per_hour"])}="n/a",0,1)', "=IF(D{r}=0,1,0)", ""),
    ("Integrity", "Edge: one office gives a finite result", f'=IF(ISNUMBER(Plan_Check!{EC["per_hour"]}{PCR["E2"]}),0,1)', "=IF(D{r}=0,1,0)", ""),
    ("Integrity", "Edge: 100% renewal charges renewal hours only", f"=Plan_Check!{EC['h_brand_sales']}{PCR['E3']}-Plan_Check!{EC['brands']}{PCR['E3']}*{R('h_renewal')}", "=IF(ABS(D{r})<=$D$3,1,0)", ""),
    ("Schedule", "Rows failing the schedule rules (Tue/Wed, blackouts, counts)", "=" + sched_bad, "=IF(D{r}=0,1,0)", "See Schedule, Row check."),
    ("Schedule", "Drop dates out of order", "=" + dates_asc, "=IF(D{r}=0,1,0)", ""),
    ("Schedule", "New founding brands beyond the founding cap", f"=MAX(0,{nf}-{R('founding_cap')})", "=IF(D{r}=0,1,0)", "Founding tier: first three brands only."),
    ("Schedule", "Founding-rate renewals beyond the two-campaign lock", f"=MAX(0,{fr}-{R('founding_lock')}*{nf})", "=IF(D{r}=0,1,0)", ""),
    ("Schedule", "Gate 2 drop exists on Schedule", f'=IF(ISNUMBER(MATCH({R("g2_drop_id")},{R("sched_ids")},0)),0,1)', "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: invalid activity keys", f"={R('HL_invalid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: drop_ids not on Schedule", f"={R('HL_badid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Toggl_Import: rows with zero hours or a bad activity", f"={R('TG_zero')}+{R('TG_invalid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Pipeline: rows with a bad event or side", f"={R('pl_bad_event')}+{R('pl_bad_side')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Actuals_Campaigns: rows whose drop_id is not on Schedule", f'=COUNTIF({R("AC_flag")},"not in schedule")', "=IF(D{r}=0,1,0)", ""),
    ("Data", "Actuals_DropCosts: rows whose drop_id is not on Schedule", f'=COUNTIF({R("DC_flag")},"not in schedule")', "=IF(D{r}=0,1,0)", ""),
    ("Plan", "Plan scenario rows 1 to 6 reproduce", f'=COUNTIF({R("pc_status")},"differs")', "=IF(D{r}=0,1,0)", "Expected only at plan defaults."),
    ("Plan", "Plan hour table reproduces cell by cell", f'=COUNTIF({R("pc_hours_match")},"no")', "=IF(D{r}=0,1,0)", "Expected only at plan defaults."),
    ("Plan", "Reconciliation rows within tolerance (the two documented differences excluded)",
     f'=COUNTIF({R("pc_recon_status")},"differs: see reason")-COUNTIF(Plan_Check!G{Q0 + 2 + 9}:G{Q0 + 2 + 9},"differs: see reason")-COUNTIF(Plan_Check!G{Q_END}:G{Q_END},"differs: see reason")',
     "=IF(D{r}=0,1,0)", "Row 10 (processing contrast) and row 25 (transport lump) differ by design."),
]
CK0 = 5
for i, (area, lab, val, pas, note) in enumerate(checks):
    rr = CK0 + i
    put(ws, f"A{rr}", i + 1)
    put(ws, f"B{rr}", area)
    put(ws, f"C{rr}", lab, align=WRAP)
    put(ws, f"D{rr}", val, fmt='#,##0.00')
    put(ws, f"E{rr}", pas.format(r=rr), fmt=INT, font=F_BOLD)
    put(ws, f"F{rr}", note, align=WRAP)
CKN = CK0 + len(checks) - 1
ws.conditional_formatting.add(f"E{CK0}:E{CKN}", CellIsRule(operator="equal", formula=["1"], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(f"E{CK0}:E{CKN}", CellIsRule(operator="equal", formula=["0"], fill=PatternFill("solid", fgColor="FFC7CE")))
rr = CKN + 2
put(ws, f"C{rr}", "Integrity and schedule checks failing", font=F_BOLD)
put(ws, f"D{rr}", f'=COUNTIFS(B{CK0}:B{CKN},"Integrity",E{CK0}:E{CKN},0)+COUNTIFS(B{CK0}:B{CKN},"Schedule",E{CK0}:E{CKN},0)', fmt=INT, font=F_BOLD)
put(ws, f"C{rr + 1}", "Data checks failing", font=F_BOLD)
put(ws, f"D{rr + 1}", f'=COUNTIFS(B{CK0}:B{CKN},"Data",E{CK0}:E{CKN},0)', fmt=INT, font=F_BOLD)
put(ws, f"C{rr + 2}", "Plan-reproduction checks failing", font=F_BOLD)
put(ws, f"D{rr + 2}", f'=COUNTIFS(B{CK0}:B{CKN},"Plan",E{CK0}:E{CKN},0)', fmt=INT, font=F_BOLD)
put(ws, f"C{rr + 3}", "Checks in total", font=F_BOLD)
put(ws, f"D{rr + 3}", f"=COUNT(E{CK0}:E{CKN})", fmt=INT, font=F_BOLD)
REF.update({"ck_integrity": f"Checks!$D${rr}", "ck_data": f"Checks!$D${rr + 1}", "ck_plan": f"Checks!$D${rr + 2}", "ck_total": f"Checks!$D${rr + 3}"})
widths(ws, {"A": 4, "B": 10, "C": 70, "D": 14, "E": 10, "F": 50})
ws.freeze_panes = "A5"

# ==========================================================================
# Dashboard
# ==========================================================================
ws = WS["Dashboard"]
put(ws, "A1", f'={R("company_name")}&" financial model v1"', font=F_TITLE)
put(ws, "A2", f"={R('tagline')}", font=F_SUB)
banner(ws, "A3", "Planning estimates, not a forecast. Gates count real numbers only (pipeline log and actuals). Change assumptions on Inputs; type real numbers into the logs.", "I3")
ws.row_dimensions[3].height = 30
put(ws, "B5", "As of", font=F_BOLD)
put(ws, "C5", f"={R('as_of')}", fmt=DDATE, font=F_BOLD)
put(ws, "D5", "Scenario", font=F_BOLD)
put(ws, "E5", f"={R('active_scenario')}", font=F_BOLD)
put(ws, "F5", "Checks", font=F_BOLD)
put(ws, "G5", f'=IF({R("ck_integrity")}=0,"all integrity checks pass",{R("ck_integrity")}&" integrity check(s) failing")', font=F_BOLD)
ws.merge_cells("G5:J5")
ok_cf(ws, "G5", good='"all integrity checks pass"')
# --- gate rows first, so the headline can point at them
N_HEAD = 14
G0R = 9 + N_HEAD + 1
st_ge = lambda r_: f'=IF(F{r_}="",IF({R("as_of")}>C{r_},"miss","not yet"),IF(F{r_}>=D{r_},"pass",IF({R("as_of")}>C{r_},"miss","not yet")))'
st_le = lambda r_: f'=IF(F{r_}="",IF({R("as_of")}>C{r_},"miss","not yet"),IF(F{r_}<=D{r_},"pass",IF({R("as_of")}>C{r_},"miss","not yet")))'
g2 = lambda rng: f'IFERROR(INDEX({rng},MATCH({R("g2_drop_id")},{R("DA_ids")},0)),"")'
std_plan_c = f'SUMIFS({dp("contribution")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")})'
std_plan_h = f'SUMIFS({dp("hours")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")})'
std_act_c = f'SUMIFS({R("DA_contrib")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("actuals_in")},"Y")'
std_act_h = f'SUMIFS({R("DA_hours")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("actuals_in")},"Y")'
gates = [
    ("Gate 0", "gate0_date", "Office conversations held (context)", "g0_office_conv", "", f"={R('pl_g0_office_conv')}", "info", INT, ""),
    ("Gate 0", "gate0_date", "Offices yes in principle, with owner and receiving window", "g0_office_yes", "", f"={R('pl_g0_office_yes')}", "ge", INT,
     "Fewer than 5 offices: change the cluster or office size band, not the model."),
    ("Gate 0", "gate0_date", "Brand conversations held (context)", "g0_brand_conv", "", f"={R('pl_g0_brand_conv')}", "info", INT, ""),
    ("Gate 0", "gate0_date", "Brands that would pay $500 or more and control the budget", "g0_brand_yes", "", f"={R('pl_g0_brand_yes')}", "ge", INT,
     "Fewer than 3: test the office-paid version for three more weeks before deciding."),
    ("Gate 1", "gate1_date", "Offices signed", "g1_offices", f"=Drop_PnL!{EC['offices']}{DROP0}", f"={R('pl_g1_signed')}", "ge", INT,
     "Offices sign but no brand pays even $600: pivot to office-paid or stop. No free campaign."),
    ("Gate 1", "gate1_date", "Combined Tuesday headcount of signed offices", "g1_headcount", "", f"={R('pl_g1_headcount')}", "ge", '#,##0', ""),
    ("Gate 1", "gate1_date", "Brands paid in full", "g1_brands_paid", f"=Drop_PnL!{EC['brands']}{DROP0}", f"={R('pl_g1_paid')}", "ge", INT,
     "One paid brand is a soft pass: run it, make the second sale first."),
    ("Gate 2", "gate2_date", "Units placed within one business day (share of delivered)", "g2_placed", "", "=" + g2(R("DA_share")), "ge", PCT,
     "Fix the procedure once (card, handoff, Slack post). A second miss is a stop signal."),
    ("Gate 2", "gate2_date", "Brand campaigns under 5 survey responses per office (must be 0)", None, "", f'=IF(N({g2(R("DA_campaigns"))})=0,"",{g2(R("DA_under"))})', "le", INT, ""),
    ("Gate 2", "gate2_date", "Reports late (after T+7) or missing (must be 0)", None, "", f'=IF(N({g2(R("DA_campaigns"))})=0,"",{g2(R("DA_late"))})', "le", INT, ""),
    ("Gate 2", "gate2_date", "Brands that would buy again", "g2_rebuy", "", f'=IF(N({g2(R("DA_campaigns"))})=0,"",{g2(R("DA_rebuy"))})', "ge", INT, ""),
    ("Gate 3", "gate3_date", "Renewals at $1,500 or more, signed by the review date", "g3_renewals",
     f'=SUMIFS({dp("renewals")},{dp("pay_dep_date")},"<="&{R("gate3_date")})-SUMIFS({dp("fnd_renewals")},{dp("pay_dep_date")},"<="&{R("gate3_date")})', f"={R('pl_g3_renewals')}", "ge", INT,
     "No renewal: redesign the evidence (velocity, redemptions), run one more drop. A second miss is a stop."),
    ("Gate 3", "gate3_date", "Contribution per founder hour, standard runs", "g3_per_hour", f'=IF({std_plan_h}>0,{std_plan_c}/{std_plan_h},"")',
     f'=IF({std_act_h}>0,{std_act_c}/{std_act_h},"")', "ge", PH, ""),
]
G3PH = G0R + 2 + len(gates) - 1
# --- headline
section(ws, 7, "Headline", last_col="I")
header_row(ws, 8, 2, ["Measure", "Value", "Detail"], height=22)
nxt = f'MATCH(1,{dp("next_flag")},0)'
live_c = f'SUMIFS({dp("live_contrib")},{dp("date")},"<="&{R("horizon_end")})'
live_h = f'SUMIFS({dp("live_hours")},{dp("date")},"<="&{R("horizon_end")})'
disc_h = f'{R("discovery_hours_week")}*{R("discovery_weeks")}'
head = [
    ("Next scheduled drop", f'=IFERROR(INDEX({dp("id")},{nxt}),"none scheduled")', f'=IFERROR(TEXT(INDEX({dp("date")},{nxt}),"ddd yyyy-mm-dd")&", "&INDEX({dp("model")},{nxt})&", "&INDEX({dp("brands")},{nxt})&" brand(s), "&INDEX({dp("offices")},{nxt})&" offices","")', None),
    ("Its contribution per founder hour (plan)", f'=IFERROR(INDEX({dp("per_hour")},{nxt}),"n/a")', f'=IFERROR("revenue "&TEXT(INDEX({dp("revenue")},{nxt}),"$#,##0")&", "&TEXT(INDEX({dp("hours")},{nxt}),"0")&" founder hours","")', PH),
    ("Standard runs to Gate 3: contribution per founder hour, plan", f"=E{G3PH}", f'="actual: "&IF(F{G3PH}="","not yet",TEXT(F{G3PH},"$#,##0.0"))&"; target "&TEXT({R("g3_per_hour")},"$#,##0")', PH),
    ("Lowest point of cumulative cash (before founder cash)", f"={R('cf_low')}", f'="in week "&{R("cf_low_week")}&", starting "&TEXT({R("cf_low_date")},"ddd yyyy-mm-dd")', USD),
    ("Capital to commit: lowest point plus the reserve", f"={R('cf_commit')}", f'="reserve "&TEXT({R("reserve_usd")},"$#,##0")&" (plan)"', USD),
    ("Plan capital figure (high end of the plan's table)", f"={R('cap_high')}", f'="low end "&TEXT({R("cap_low")},"$#,##0")', USD),
    ("Gap to the plan capital figure (positive = headroom)", f"={R('cf_gap')}", '=IF(C{self}>=0,"the plan figure covers the model need","the model needs more than the plan figure")', USD),
    ("Founder cash committed", f"={R('cf_founder')}", f'=IF({R("founder_cash")}="","set it on Inputs (plan question 7)",IF({R("founder_cash")}>={R("cf_commit")},"covers capital to commit","short of capital to commit by "&TEXT({R("cf_commit")}-{R("founder_cash")},"$#,##0")))', USD),
    ("Overhead paid but not absorbed by drops, six months", f"={R('cf_unabsorbed')}", f'="paid "&TEXT({R("cf_over_paid")},"$#,##0")&", allocated to drops "&TEXT({R("cf_alloc")},"$#,##0")&": the ramp-up months carry overhead with few drops"', USD),
    ("Six months all-in: contribution after all overhead per founder hour", f'=IF({live_h}+{disc_h}>0,({live_c}-{R("cf_unabsorbed")})/({live_h}+{disc_h}),"n/a")',
     f'="includes "&TEXT({disc_h},"0")&" discovery hours; after one-time startup outlays: "&IF({live_h}+{disc_h}>0,TEXT(({live_c}-{R("cf_unabsorbed")}-{R("su_total")})/({live_h}+{disc_h}),"$#,##0.0"),"n/a")&" per hour"', PH),
    ("Steady state, scenario in force: contribution per month", f"={R('ss_contrib')}", f'="per founder hour "&IF(ISNUMBER({R("ss_ph")}),TEXT({R("ss_ph")},"$#,##0.0"),"n/a")&"; net of all overhead "&TEXT({R("ss_net")},"$#,##0")&" a month"', USD),
    ("Office-fatigue warnings on Schedule", f'=COUNTIF({R("sched_fatigue")},"some*")', '=IF(C{self}=0,"no office gets two drops within four weeks","drops where some offices get a second drop within four weeks (plan: one drop a month)")', INT),
    ("Schedule rows changed or added since the derived default", f'=COUNTIF({R("sched_changed")},"changed")', '=IF(C{self}=0,"schedule is the derived default","edited by you")', INT),
    ("Inputs changed from plan defaults", f"={R('changed_count')}", f'=IF({R("ck_plan")}=0,"plan figures reproduce","plan reproduction differs in "&{R("ck_plan")}&" check(s); expected after edits")', INT),
]
assert len(head) == N_HEAD
for i, (lab, v, det, fmt) in enumerate(head):
    rr = 9 + i
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", v, fmt=fmt, font=F_BOLD, fill=FILL_KEY)
    put(ws, f"D{rr}", det.replace("{self}", str(rr)))
    ws.merge_cells(f"D{rr}:I{rr}")
# --- gates
section(ws, G0R, "Gate dashboard (live values are actuals only)", last_col="I")
header_row(ws, G0R + 1, 1, ["Gate", "Test", "Review date", "Threshold", "Model assumes", "Live value", "Status", "If it fails (plan)", "", "", ""], height=30)
ws.merge_cells(f"H{G0R + 1}:K{G0R + 1}")
GR = {}
for i, (g, dkey, test, thr, model_v, live, kind, fmt, fail) in enumerate(gates):
    rr = G0R + 2 + i
    put(ws, f"A{rr}", g, font=F_BOLD)
    put(ws, f"B{rr}", test, align=WRAP)
    put(ws, f"C{rr}", f"={R(dkey)}", fmt=DATE)
    put(ws, f"D{rr}", f"={R(thr)}" if thr else 0, fmt=fmt)
    put(ws, f"E{rr}", model_v if model_v else "", fmt=fmt)
    put(ws, f"F{rr}", live, fmt=fmt, font=F_BOLD)
    put(ws, f"G{rr}", "info" if kind == "info" else (st_ge(rr) if kind == "ge" else st_le(rr)), font=F_BOLD, align=Alignment(horizontal="center"))
    put(ws, f"H{rr}", fail, align=WRAP, font=F_NOTE)
    ws.merge_cells(f"H{rr}:K{rr}")
    ws.row_dimensions[rr].height = 30
    GR.setdefault(g, []).append((rr, kind))
GEND = G3PH
status_cf(ws, f"G{G0R + 2}:G{GEND}")
GS = GEND + 2
header_row(ws, GS, 1, ["Gate", "Review date", "Overall"], height=22)
for i, g in enumerate(["Gate 0", "Gate 1", "Gate 2", "Gate 3"]):
    rr = GS + 1 + i
    rows_ = [r_ for r_, k in GR[g] if k != "info"]
    miss = "+".join(f'IF(G{r_}="miss",1,0)' for r_ in rows_)
    notyet = "+".join(f'IF(G{r_}="not yet",1,0)' for r_ in rows_)
    put(ws, f"A{rr}", g, font=F_BOLD)
    put(ws, f"B{rr}", f"=C{GR[g][0][0]}", fmt=DATE)
    put(ws, f"C{rr}", f'=IF({miss}>0,"miss",IF({notyet}>0,"not yet","pass"))', font=F_BOLD)
    REF["gate_" + g[-1]] = f"Dashboard!$C${rr}"
status_cf(ws, f"C{GS + 1}:C{GS + 4}")
# --- decision rule
DR0 = GS + 6
section(ws, DR0, "Decision rule (plan): scale, switch to office-paid, or stop", last_col="I")
renew_live = f'IF(COUNTIF({R("AC_renewed")},"Y")+COUNTIF({R("AC_renewed")},"N")=0,"",COUNTIF({R("AC_renewed")},"Y")/(COUNTIF({R("AC_renewed")},"Y")+COUNTIF({R("AC_renewed")},"N")))'
drows = [
    ("Brand renewal rate (renewed Y / answered Y or N)", "=" + renew_live, PCT),
    ("Offices that named $100 a month or more", f"={R('pl_op_offices')}", INT),
    ("Drops after Gate 3 with actuals in", f'=COUNTIFS({dp("date")},">"&{R("gate3_date")},{dp("actuals_in")},"Y",{dp("run")},1)', INT),
    ("Gate 3", f"={R('gate_3')}", None),
]
for i, (lab, f, fmt) in enumerate(drows):
    rr = DR0 + 1 + i
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f, fmt=fmt, font=F_BOLD)
rn, op, xd, g3s = (f"C{DR0 + 1}", f"C{DR0 + 2}", f"C{DR0 + 3}", f"C{DR0 + 4}")
rr = DR0 + 5
put(ws, f"B{rr}", "The rule says", font=F_BOLD)
put(ws, f"C{rr}", (f'=IF({rn}="","not yet: no renewal answers",IF(AND({g3s}="pass",{rn}>={R("dr_scale_renewal")}),"Scale",'
                   f'IF(AND({op}>={R("dr_switch_offices")},{rn}<{R("dr_switch_renewal")},{xd}>={R("dr_extra_drops")}),"Switch to office-paid",'
                   f'IF(AND({rn}>={R("dr_switch_renewal")},{rn}<{R("dr_scale_renewal")}),"Rule silent: renewal between "&TEXT({R("dr_switch_renewal")},"0%")&" and "&TEXT({R("dr_scale_renewal")},"0%"),'
                   f'IF({R("as_of")}>{R("decision_date")},"Stop","not yet: stop if nothing changes by the decision date")))))'), font=F_BOLD, fill=FILL_KEY)
ws.merge_cells(f"C{rr}:I{rr}")
put(ws, f"B{rr + 1}", "Stated once (plan)", font=F_NOTE)
put(ws, f"C{rr + 1}", "Scale if Gate 3 passed and renewal is 40% or more. Switch to office-paid if at least five offices named $100 a month or more and brand renewal is under 30% after two extra drops. Stop if both fail.", align=WRAP, font=F_NOTE)
ws.merge_cells(f"C{rr + 1}:I{rr + 1}")
ws.row_dimensions[rr + 1].height = 30
SP = rr + 3
placed_all = f'IF(SUMIFS({R("DA_delivered")},{dp("actuals_in")},"Y")=0,"",SUMIFS({R("DA_placed1")},{dp("actuals_in")},"Y")/SUMIFS({R("DA_delivered")},{dp("actuals_in")},"Y"))'
below = f'COUNTIFS({dp("actuals_in")},"Y",{R("DA_share")},"<"&{R("g2_placed")})'
ph_all = f'IF(SUMIFS({R("DA_hours")},{dp("actuals_in")},"Y")>0,SUMIFS({R("DA_contrib")},{dp("actuals_in")},"Y")/SUMIFS({R("DA_hours")},{dp("actuals_in")},"Y"),"")'
put(ws, f"B{SP}", "Placement within one business day, all drops with actuals")
put(ws, f"C{SP}", "=" + placed_all, fmt=PCT, font=F_BOLD)
put(ws, f"B{SP + 1}", "Drops with actuals below the placement threshold")
put(ws, f"C{SP + 1}", "=" + below, fmt=INT, font=F_BOLD)
put(ws, f"B{SP + 2}", "Contribution per founder hour, all drops with actuals")
put(ws, f"C{SP + 2}", "=" + ph_all, fmt=PH, font=F_BOLD)
put(ws, f"B{SP + 3}", "Scenario the real numbers point to", font=F_BOLD)
pl_, bl_, pa_ = f"C{SP}", f"C{SP + 1}", f"C{SP + 2}"
put(ws, f"C{SP + 3}", (f'=IF({pl_}="","not enough data yet",IF(AND({rn}<>"",N({rn})=0,{pl_}<{R("g2_placed")}),"D: neither converts",'
                       f'IF({bl_}>={R("sc_c_misses")},"C: brands willing, offices unreliable",IF(AND({rn}<>"",N({rn})<{R("dr_switch_renewal")}),"B: brands pay once, offices love it",'
                       f'IF(AND({rn}<>"",N({rn})>={R("dr_scale_renewal")},{pl_}>={R("g2_placed")},N({pa_})>={R("g3_per_hour")}),"A: both sides work","between scenarios: see the rule")))))'),
    font=F_BOLD, fill=FILL_KEY)
ws.merge_cells(f"C{SP + 3}:I{SP + 3}")
REF["dash_rule"] = f"Dashboard!$C${rr}"
REF["dash_pointer"] = f"Dashboard!$C${SP + 3}"
# --- six-month goals
SG = SP + 6
section(ws, SG, "Six-month goals (plan): planned by the schedule against actual", last_col="I")
header_row(ws, SG + 1, 2, ["Goal", "Target", "Planned (Schedule)", "Actual", "Status"], height=22)
goals = [
    ("Paid campaigns", "goal_campaigns", f'=SUMIFS({dp("brands")},{dp("date")},"<="&{R("horizon_end")})', f'=COUNTIF({R("AC_revenue_usd")},">0")'),
    ("Renewals", "goal_renewals", f'=SUMIFS({dp("renewals")},{dp("date")},"<="&{R("horizon_end")})', f'=COUNTIF({R("AC_renewed")},"Y")'),
    ("Active offices", "goal_offices", f'=SUMIFS({dp("new_offices")},{dp("date")},"<="&{R("horizon_end")})', f"={R('pl_active_offices')}"),
    ("Contribution per founder hour, standard runs", "g3_per_hour", f"=E{G3PH}", f"=F{G3PH}"),
]
for i, (lab, tk, pf, af) in enumerate(goals):
    rr = SG + 2 + i
    f_ = PH if "hour" in lab else INT
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f"={R(tk)}", fmt=f_)
    put(ws, f"D{rr}", pf, fmt=f_)
    put(ws, f"E{rr}", af, fmt=f_, font=F_BOLD)
    put(ws, f"F{rr}", f'=IF(E{rr}="",IF({R("as_of")}>{R("decision_date")},"miss","not yet"),IF(E{rr}>=C{rr},"pass",IF({R("as_of")}>{R("decision_date")},"miss","not yet")))', font=F_BOLD)
status_cf(ws, f"F{SG + 2}:F{SG + 5}")
REF["dash_goals"] = (SG + 2, SG + 5)
# --- drop summary
DS = SG + 8
section(ws, DS, "Contribution per founder hour on each drop (live: actual where in, otherwise plan)", last_col="L")
header_row(ws, DS + 1, 1, ["drop_id", "Label", "Drop date", "Basis", "Delivery model", "Brands", "Offices", "Revenue", "Hard costs", "Founder hours", "Contribution", "Per founder hour"], height=30)
for i in range(N_DROPS):
    rr = DS + 2 + i
    s_ = DROP0 + i
    blank = f'Drop_PnL!B{s_}=""'
    put(ws, f"A{rr}", f'=IF({blank},"",Drop_PnL!A{s_})')
    put(ws, f"B{rr}", f'=IF({blank},"",Schedule!B{s_}&"")')
    put(ws, f"C{rr}", f'=IF({blank},"",Drop_PnL!B{s_})', fmt=DATE)
    put(ws, f"D{rr}", f"=Drop_PnL!{CT['basis']}{s_}")
    put(ws, f"E{rr}", f'=IF({blank},"",Drop_PnL!C{s_})')
    for col, src, fmt in (("F", EC["brands"], None), ("G", EC["offices"], INT), ("H", CT["live_rev"], USD), ("I", CT["live_cost"], USD),
                          ("J", CT["live_hours"], HRS), ("K", CT["live_contrib"], USD), ("L", CT["live_ph"], PH)):
        put(ws, f"{col}{rr}", f'=IF({blank},"",Drop_PnL!{src}{s_})', fmt=fmt, font=F_BOLD if col == "L" else None)
DSE = DS + 1 + N_DROPS
rr = DSE + 1
put(ws, f"A{rr}", "Total", font=F_BOLD)
for col in "FGHIJK":
    put(ws, f"{col}{rr}", f"=SUM({col}{DS + 2}:{col}{DSE})", fmt={"F": None, "G": INT, "J": HRS}.get(col, USD), font=F_BOLD)
put(ws, f"L{rr}", f'=IF(J{rr}>0,K{rr}/J{rr},"n/a")', fmt=PH, font=F_BOLD)
put(ws, f"J{DS}", "Target per founder hour", font=F_BOLD, fill=FILL_SEC)
put(ws, f"L{DS}", f"={R('g3_per_hour')}", fmt=USD, font=F_BOLD, fill=FILL_SEC)
ws.conditional_formatting.add(f"L{DS + 2}:L{DSE + 1}", FormulaRule(formula=[f'AND(ISNUMBER(L{DS + 2}),L{DS + 2}>=$L${DS})'], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(f"L{DS + 2}:L{DSE + 1}", FormulaRule(formula=[f'AND(ISNUMBER(L{DS + 2}),L{DS + 2}<$L${DS})'], fill=PatternFill("solid", fgColor="FCE4D6")))
put(ws, f"A{DSE + 3}", "Green: at or above the Gate 3 target per founder hour. Orange: below it. Campaign zero is expected to be below; the plan's own figure for it is $16. "
                     "The total row is per founder hour across all scheduled drops, before overhead that drops do not absorb.", font=F_NOTE)
widths(ws, {"A": 11, "B": 54, "C": 13, "D": 13, "E": 13, "F": 12, "G": 12, "H": 12, "I": 12, "J": 13, "K": 13, "L": 13})
ch2 = LineChart()
ch2.title = "Cumulative net cash flow by week (before founder cash)"
ch2.height, ch2.width = 7, 18
ch2.add_data(Reference(WS["Cash_Flow"], min_col=WK0, max_col=WKN, min_row=27, max_row=27), from_rows=True, titles_from_data=False)
ch2.set_categories(Reference(WS["Cash_Flow"], min_col=WK0, max_col=WKN, min_row=4, max_row=4))
ch2.legend = None
ch2.y_axis.title = "USD"
ch2.x_axis.title = "Week"
ch2.x_axis.tickLblPos = "low"
ch2.series[0].smooth = False
ws.add_chart(ch2, f"B{DSE + 5}")

# ==========================================================================
# README (built from _work/readme_text.py so the text is easy to edit)
# ==========================================================================
import importlib.util
spec = importlib.util.spec_from_file_location("readme_text", os.path.join(HERE, "readme_text.py"))
rt_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt_mod)
ws = WS["README"]
put(ws, "A1", f'={R("company_name")}&" financial model v1: README"', font=F_TITLE)
put(ws, "A2", "Version 1, built 2026-10-23 to 2026-10-24. The company name lives in one cell (Inputs, section 1, 'Company name'); rename it there only.", font=F_SUB)
rr = 4
for kind, text in rt_mod.README:
    if kind == "h":
        rr += 1
        section(ws, rr, text, last_col="B")
    elif kind == "p":
        put(ws, f"A{rr}", text, align=WRAP)
        ws.merge_cells(f"A{rr}:B{rr}")
        ws.row_dimensions[rr].height = max(15, 15 * (len(text) // 120 + 1))
    elif kind == "kv":
        k, v = text
        put(ws, f"A{rr}", k, font=F_BOLD, align=WRAP)
        put(ws, f"B{rr}", v, align=WRAP)
        ws.row_dimensions[rr].height = max(15, 15 * (len(v) // 95 + 1))
    rr += 1
widths(ws, {"A": 30, "B": 125})

# ==========================================================================
# workbook finish
# ==========================================================================
for t in TABS:
    WS[t].sheet_view.zoomScale = 90
WS["Dashboard"].sheet_properties.tabColor = "2E5E6B"
WS["Inputs"].sheet_properties.tabColor = "F2C200"
WS["Schedule"].sheet_properties.tabColor = "F2C200"
for t in ("Hours_Log", "Toggl_Import", "Pipeline", "Actuals_Campaigns", "Actuals_DropCosts"):
    WS[t].sheet_properties.tabColor = "8FB98B"
# top-align every cell that has no vertical alignment yet (mixed alignment reads badly in wrapped rows)
for t in TABS:
    for row_ in WS[t].iter_rows():
        for c in row_:
            if c.value is not None and c.alignment.vertical is None:
                c.alignment = Alignment(horizontal=c.alignment.horizontal, vertical="top", wrap_text=c.alignment.wrap_text)
wb.active = TABS.index("Dashboard")
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
# write the reference map for the audit and test scripts
import json
with open(os.path.join(HERE, "ref_map.json"), "w") as fh:
    json.dump({k: v for k, v in REF.items() if isinstance(v, str)}, fh, indent=1, sort_keys=True)
print("saved", OUT)
