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

# Paste areas and their helper blocks. Every helper block sits at least ten blank columns to the right of its
# paste area, so an extra column in a pasted file lands in blank cells and is flagged on Checks (review R1-06).
BUF = 10
AC_COLS = ["campaign_id", "drop_id", "drop_date", "delivery_model", "tier", "brand_id", "offices", "units_received", "units_delivered", "units_placed",
           "units_placed_within_1bd", "units_topped_up", "units_depleted_day5", "survey_responses", "survey_tried_yes", "qr_scans",
           "code_redemptions_day30", "revenue_usd", "invoice_paid_date", "processing_fee_usd", "report_delivered_date", "brand_would_buy_again",
           "renewed", "deposit_usd", "deposit_paid_date", "survey_responses_min_office"]
DC_COLS = ["drop_id", "drop_date", "delivery_model", "offices", "brands", "kit_cost_usd", "transport_cost_usd", "other_direct_cost_usd", "notes"]
HL_COLS = ["date", "drop_id", "campaign_id", "activity", "hours", "note"]
PL_COLS = ["date", "side", "org_id", "org_name", "event", "value_number", "value_text", "controls_budget", "notes"]
AC_H0 = len(AC_COLS) + BUF + 2    # 38 = AL: first Actuals_Campaigns helper (AA to AK stay blank)
DC_H0 = len(DC_COLS) + BUF + 2    # 21 = U: Actuals_DropCosts helper (J to T stay blank)
HT0 = len(HL_COLS) + BUF + 1      # 17 = Q: Hours_Log totals (G to P stay blank)
PLH0 = len(PL_COLS) + BUF + 1     # 20 = T: Pipeline helpers (J to S stay blank)
TG_LAST = 30                      # Toggl_Import paste area A:AD
TGH0 = TG_LAST + 2                # 32 = AF: Toggl helpers
PLC = {k: CL(PLH0 + i) for i, k in enumerate(["first", "g0b", "g0b_first", "op", "op_first", "g3", "g3_first", "probe_ok", "oprobe", "bprobe", "bprobe_after",
                                             "paid_full"])}
PLS = PLH0 + len(PLC) + 1         # 30 = AD: Pipeline summary block
pr = lambda L: f"Pipeline!${L}${PL0}:${L}${PLN}"
REF.update({"PL_date": pr("A"), "PL_side": pr("B"), "PL_org": pr("C"), "PL_event": pr("E"), "PL_value": pr("F"), "PL_text": pr("G"),
            "PL_first": pr(PLC["first"]), "PL_g0b_first": pr(PLC["g0b_first"]), "PL_op_first": pr(PLC["op_first"]),
            "PL_g3_first": pr(PLC["g3_first"]), "PL_oprobe": pr(PLC["oprobe"]), "PL_bprobe": pr(PLC["bprobe"]),
            "PL_bprobe_after": pr(PLC["bprobe_after"]), "PL_paid_full": pr(PLC["paid_full"])})
sr = lambda L: f"Schedule!${L}${DROP0}:${L}${DROPN}"
REF.update({"sched_ids": sr("A"), "sched_dates": sr("E"), "sched_tiers": sr("H"), "sched_actuals": sr("N"), "sched_check": sr("T"),
            "sched_debrief": sr("AF"), "sched_std_run": sr("AJ")})   # AJ: date of each standard drop that runs (review R2-06)

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
# Pipeline: the notes value that marks a budget_probe answer given after hearing the $1,500 price (review R2-05; HANDOFF section 3)
put(ws, "X3", "budget_probe notes marker", font=F_H, fill=FILL_H)
put(ws, "X4", "after_1500")
put(ws, "Y4", "notes value on a budget_probe row given after hearing $1,500 (HANDOFF section 3)", font=F_NOTE)
REF["L_after"] = "Lists!$X$4"
# expected header rows of the four paste files (HANDOFF.md); Checks compares each paste tab's row 4 with these
put(ws, "A33", "Expected header row of each pasted file (HANDOFF.md). Checks compares row 4 of each paste tab with these. Do not edit.", font=F_BOLD)
HDR_ROW = {}
for i, (fname, cols) in enumerate([("campaign_actuals.csv", AC_COLS), ("drop_costs.csv", DC_COLS), ("hours_log.csv", HL_COLS), ("pipeline_log.csv", PL_COLS)]):
    r = 34 + i
    put(ws, f"A{r}", fname, font=F_BOLD)
    for j, h in enumerate(cols):
        put(ws, f"{CL(2 + j)}{r}", h, font=F_NOTE)
    HDR_ROW[fname] = f"Lists!$B${r}:${CL(1 + len(cols))}${r}"
widths(ws, {"A": 14, "B": 11, "C": 21, "D": 32, "E": 8, "F": 11, "G": 9, "H": 17, "I": 15, "J": 10, "K": 14, "L": 16,
            "N": 13, "O": 34, "Q": 13, "R": 13, "S": 52, "U": 30, "V": 6, "X": 24, "Y": 60})

# ==========================================================================
# Inputs
# ==========================================================================
ws = WS["Inputs"]
title(ws, "Inputs", "Every assumption in one labeled cell. Yellow cells are inputs. Blue cells are inputs that follow another cell by default; type over them to replace. Grey cells are calculated; do not type over them.")
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


def inp(key, label, value, unit, status, source, notes="", low=None, high=None, fmt=None, calc=False, vlist=None, track=True, follows=False):
    """track=False: no 'Plan default' copy (the company name and tagline must live in one cell only).
    follows=True: the default is a formula that follows another cell (blue); typing over it is flagged 'changed'."""
    r = row[0]
    put(ws, f"A{r}", key, font=F_NOTE)
    put(ws, f"B{r}", label, align=WRAP)
    c = put(ws, f"C{r}", value, fmt=fmt)
    if calc:
        c.fill = FILL_CALC
        c.border = BOX
    else:
        as_input(c)
        if follows:
            c.fill = FILL_SCEN
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
    if not calc and track:
        put(ws, f"J{r}", value, fmt=fmt, font=F_NOTE)
        put(ws, f"K{r}", f'=IF(C{r}&""=J{r}&"","","changed")', font=Font(color="9C0006", bold=True))
        CHANGED_CELLS.append(f"K{r}")
    elif not calc:
        put(ws, f"J{r}", "not tracked", font=F_NOTE)
        put(ws, f"K{r}", f'=IF(C{r}="","missing","")', font=Font(color="9C0006", bold=True))
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
# the legal pack's figures.csv changed at 01:52 (review R2-07) and again at 02:33 on 2026-10-24, after the round-2 build; re-read in full (review R3-02)
G_CSV = "desk-drop-legal-pack/figures.csv (re-read 2026-10-24, after its 02:33 update)"

inp_section("1. Company and calendar")
inp("company_name", "Company name (working name, not yet cleared)", "Desk Drop", "text", "working name", "Prompt; CONTRACTS s2 rename-ability",
    "The only cell that holds the company name. Rename here and every tab follows. Not counted as a change.", track=False)
inp("tagline", "Tagline (working, may change)", "Emerging brands. Delivered to your workday.", "text", "working", "Prompt; CONTRACTS s2",
    "The only cell that holds the tagline.", track=False)
inp("week1_start", "Week 1 starts (Monday)", D(2026, 10, 26), "date", "derived, founder to confirm", CTR3,
    "Week n starts on this date plus 7 x (n - 1) days. Moving it moves the cash-flow weeks, software, the domain and any mailbox only. "
    "The gate dates below and the drop dates on Schedule are typed CONTRACTS dates: move them too. Checks flags week 1 moved on its own (review R3-09).", fmt=DATE)
inp("gate0_date", "Gate 0 review (end of week 3)", D(2026, 11, 13), "date", "derived, founder to confirm", CTR3, fmt=DATE)
inp("gate1_date", "Gate 1 review (end of week 7)", D(2026, 12, 11), "date", "derived, founder to confirm", CTR3, fmt=DATE)
r_g2 = inp("gate2_date", "Gate 2 review (campaign zero report, T+7)", None, "date", "derived, founder to confirm", CTR3,
           "Follows the Gate 2 drop on Schedule: its date plus the report deadline (T+7, 2027-01-22 by default). Moved from the plan's week 9 because campaign zero moved to 2027-01-12 (December blackout collision).",
           fmt=DATE, follows=True)
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
inp("debrief_bd", "Debrief this many business days after the drop (T+10)", 10, "business days", "planning estimate", CTR3 + " (debrief at T+10)",
    "Used to flag a decision-window drop whose results land after the decision date (Schedule, Dashboard).")
inp("llc_filing_bd", "LLC Articles filed this many business days after Gate 0", 4, "business days", "derived, founder to confirm",
    G_CSV + ", Articles timing: 'never before the attorney hour; earliest Thu 2026-11-19'",
    "Sets the filing date in section 11: Fri 2026-11-13 plus 4 business days is Thu 2026-11-19, the day after the attorney hour.")
inp("attorney_bd", "Attorney hour held this many business days after Gate 0", 3, "business days", "derived, founder to confirm",
    G_CSV + ", attorney_hour timing: 'booked at Gate 0 ... held early in week 4, by Wed 2026-11-18'", "Sets the attorney payment date in section 11 (Wed 2026-11-18).")
inp("accountant_bd", "Accountant hour held this many business days after Gate 0", 5, "business days", "derived, founder to confirm",
    G_CSV + ", accountant_hour timing: 'held in week 4, by Fri 2026-11-20'", "Sets the accountant payment date in section 11 (Fri 2026-11-20).")
inp("pub_order_bd", "Newspaper publication ordered this many business days after the LLC filing", 10, "business days", "derived, founder to confirm",
    G_CSV + ", publication timing: 'Order within 10 business days of filing'", "Sets the publication payment date in section 11 (Fri 2026-12-04, skipping Thanksgiving).")
inp("pub_weeks", "Weekly newspaper runs before the Certificate of Publication is filed", 6, "weeks", "planning estimate",
    "plan.md, Legal table: 'publish in two newspapers for six weeks'", "Sets the certificate's payment date in section 11.")
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
# the unit starts with the first standard drop that actually runs (brands > 0), so a schedule with no standard drop rents nothing (review R2-06)
inp("storage_start", "Storage unit rented from", f'=IF(COUNT({R("sched_std_run")})=0,"",EOMONTH(MIN({R("sched_std_run")}),-1)+1)',
    "date", "derived, founder to confirm", "Plan reading (b)",
    "Follows Schedule: the first day of the month of the first standard drop that runs (2027-02-01 by default). Blank when no standard drop runs. "
    "Campaign zero stays at home, which is how its $280 reproduces.",
    fmt=DATE, follows=True)
inp("storage_end", "Storage unit released (blank = keep)", None, "date", "setting", "Plan reading (c)",
    "Blank keeps the unit through the window, as the plan's direct-ship row keeps the $75.", fmt=DATE)
inp("software_monthly", "Software per month", 60, "USD per month", "planning estimate", P_CAP + "; Tools table",
    "$360 for six months. Tools table sums to $7 to $81; the plan caps software under $60.", low=7, high=81, fmt=USD)
inp("software_start", "Software paid from", f"={R('week1_start')}", "date", "derived, founder to confirm", "plan.md, Week 1 setup", "Follows week 1.", fmt=DATE, follows=True)
inp("insurance_monthly", "General liability insurance per month", 100, "USD per month", "plan estimate (legal pack); three quotes before binding", P_ECON + "; " + G_CSV,
    "'Roughly $100 a month'. Capital table range $500 to $1,500 a year, shown here per month. The legal pack carries $1,200 a year as a plan estimate and asks for a quote before binding.",
    low=500 / 12, high=125, fmt=USD)
inp("insurance_billing", "Insurance billing", "annual", "list", "setting", P_CAP, "annual = one year's premium paid at bind (capital table 'one year').", vlist="L_insbill")
inp("insurance_bind", "Insurance bound on", f"={R('gate1_date')}", "date", "derived, founder to confirm", "plan.md, setup checklist: 'At Gate 1 pass: Insurance bound'",
    "Follows Gate 1. The legal pack's latest bind date is 2026-12-21.", fmt=DATE, follows=True)
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
inp("founder_cash_date", "Founder cash goes in on", f"={R('week1_start')}", "date", "setting", "Model setting", "Follows week 1.", fmt=DATE, follows=True)
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
# Gate 2 follows its drop on Schedule (review R1-14): drop date plus the report deadline in business days
_g2f = f'=IFERROR(WORKDAY(INDEX({R("sched_dates")},MATCH({R("g2_drop_id")},{R("sched_ids")},0)),{R("g2_report_bd")},{R("holidays")}),"")'
ws[f"C{r_g2}"].value = _g2f
ws[f"J{r_g2}"].value = _g2f

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
SU_KEYS = ["su_llc", "su_cert", "su_pub", "su_reg_agent", "su_license", "su_print", "su_domain", "su_mailbox", "su_attorney", "su_accountant", "su_it204",
           "su_hnoa", "su_addl_insured", "su_tm"]
SUR = {k: su0 + i for i, k in enumerate(SU_KEYS)}
g0, g1 = f"={R('gate0_date')}", f"={R('gate1_date')}"
startup = [
    # key, item, working, low, high, status, source, notes, timing (date or formula), timing basis, include
    ("su_llc", "LLC Articles of Organization (state filing fee)", 200, 200, 200, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://dos.ny.gov/limited-liability-company-articles-organization", "Plan capital table: $200 plus $50.",
     f"=WORKDAY({R('gate0_date')},{R('llc_filing_bd')},{R('holidays')})",
     "Follows Gate 0: earliest Thu 2026-11-19, never before the attorney hour (legal pack). Day 0 = first verbal brand yes", "Y"),
    ("su_cert", "Certificate of Publication filing", 50, 50, 50, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://dos.ny.gov/certificate-publication-domestic-limited-liability-company-0", "",
     f"=L{SUR['su_pub']}+{R('pub_weeks')}*{R('days_per_week')}", "Follows publication: after the sixth weekly run (2027-01-15 by default; legal limit day 120)", "Y"),
    ("su_pub", "Newspaper publication (two papers, six weeks), county not chosen", 2000, 250, 2000, "needs quote (plan high end until quoted)",
     "plan.md, Economics: Capital table ($250 to $2,000, no working figure); " + G_CSV + "; https://www.llcpublishers.com/pricing",
     "Default = the plan's high end, because the plan gives a range and no working figure; it stays until a quote or a verified figure arrives. "
     "Alternative: the legal pack's working figure $1,745 for New York County (LLC Publishers $1,795 all-in less the $50 state fee; needs quote), or $345 if the attorney confirms Albany County.",
     f"=WORKDAY(L{SUR['su_llc']},{R('pub_order_bd')},{R('holidays')})", "Follows the LLC filing: ordered within 10 business days (legal pack), 2026-12-04 by default", "Y"),
    ("su_reg_agent", "Registered agent, only if the Articles name Albany County", None, None, None, "needs quote (legal pack)",
     G_CSV + " (registered_agent_albany_if_used)",
     "Optional in New York, where the Secretary of State is the agent for service of process. The legal pack adds it only on the Albany County route and invents no figure. "
     "Include = N; if the attorney confirms Albany, type the quote and set Y. Yearly; the model books the first year.",
     f"=L{SUR['su_llc']}", "Follows the LLC filing (the Articles name the agent)", "N"),
    ("su_license", "Food warehouse license (Article 28-D, two years), if required", 400, 0, 400, "fee verified 2026-10-23; need unknown (legal pack)",
     G_CSV + "; https://www.nysenate.gov/legislation/laws/AGM/500-B", "Zero if the state says sealed cases at home need no license, or if brands ship direct.",
     g1, "Follows Gate 1. Before any brand ships (legal pack: latest 2026-12-21)", "Y"),
    ("su_print", "Printing and materials (hand truck, supplies, first card runs)", 300, 300, 300, "planning estimate", P_CAP,
     "Read as startup supplies; per-drop kits are the $8 per office line. Campaign zero also pays $40 of kits on its drop: if the first card run is those kits, $40 is counted twice (conservative). Both are plan figures.",
     g1, "Follows Gate 1: hand truck, supplies and first card run (plan setup checklist)", "Y"),
    ("su_domain", "Domain and email setup", 100, 100, 100, "planning estimate", P_CAP, "", f"={R('week1_start')}", "Follows week 1: days 1 and 2 (plan)", "Y"),
    ("su_mailbox", "Mailing address for email footers and the LLC notice (PO box or private mailbox), first year", None, None, None, "needs quote (legal pack)",
     G_CSV + " (mailing_address_mailbox_annual); https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business",
     "CAN-SPAM needs a postal address in every commercial email, and the LLC's newspaper notice prints one. Needed only if you will not use a home address. "
     "The legal pack did not research the cost and invents no figure. Blank counts as $0.",
     f"={R('week1_start')}", "Follows week 1: before the first outreach email (legal pack)", "Y"),
    ("su_attorney", "Attorney hour (both agreements, name and formation questions)", 400, 300, 500, "plan estimate (legal pack)",
     G_CSV + "; plan.md Legal table", "Not in the plan's capital table. Plan question 8 puts both hours at about $700; $400 plus the accountant's $300 keeps that figure.",
     f"=WORKDAY({R('gate0_date')},{R('attorney_bd')},{R('holidays')})", "Follows Gate 0: booked then, held by Wed 2026-11-18, before the filing (legal pack)", "Y"),
    ("su_accountant", "Accountant hour (sales tax, UBT, estimates)", 300, 200, 400, "plan estimate (legal pack)",
     G_CSV + "; plan.md Legal table", "Not in the plan's capital table. See the attorney line for the $700 pair.",
     f"=WORKDAY({R('gate0_date')},{R('accountant_bd')},{R('holidays')})", "Follows Gate 0: booked then, held by Fri 2026-11-20, before the first invoice (legal pack)", "Y"),
    ("su_it204", "NYS LLC annual filing fee (IT-204-LL), single-member", 25, 25, 25, "verified 2026-10-23 (legal pack)",
     G_CSV + "; https://www.tax.ny.gov/pdf/current_forms/it/it204lli.pdf", "Accountant confirms whether 2026 is owed. Not in the plan.", D(2027, 3, 15),
     "Statutory date: first possibly Mon 2027-03-15 for 2026 (legal pack)", "Y"),
    ("su_hnoa", "Hired and non-owned auto add-on to the liability policy", None, None, None, "needs quote (legal pack)",
     G_CSV + "; plan.md Legal table ('Small add-on. Ask the carrier.')", "Needed if car rides, a car service or a rented van carry product (campaign zero does). Blank counts as $0.",
     f"={R('insurance_bind')}", "Follows the insurance bind date", "Y"),
    ("su_addl_insured", "Additional-insured endorsements for buildings that require them", None, None, None, "needs quote (legal pack)",
     G_CSV, "The legal pack expects one per building that requires it, because there is no contract with any building; zero only if the carrier confirms its blanket endorsement covers buildings. "
     "Blank counts as $0.", f"={R('insurance_bind')}", "Follows the insurance bind date; before each such building's first drop", "Y"),
    ("su_tm", "Federal trademark application (one class)", 350, 350, 850, "verified 2026-10-23 (legal pack)",
     G_CSV + "; plan.md setup checklist, 'After campaign zero: Trademark application, if the campaign was a pass'; https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule",
     "In the six months at Gate 2 pass (review R3-02): the plan's setup checklist files it after campaign zero if it was a pass, and the legal pack now times it from about Mon 2027-01-25, inside the six months. "
     "The plan's capital table has no line for it. The model books it on the Gate 2 day, the earliest and most cautious date. USPTO refused a prior DESK-DROP application as merely descriptive: "
     "set Include = N if the attorney advises against filing.",
     f"={R('gate2_date')}", "Follows Gate 2: after campaign zero passes (plan setup checklist; legal pack: from about Mon 2027-01-25); attorney advises first", "Y"),
]
assert [s[0] for s in startup] == SU_KEYS
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
    if isinstance(tdate, str):
        ws[f"L{r}"].fill = FILL_SCEN
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
# cost lines with no figure yet count as $0 in the cash flow; the Dashboard's cash need says how many (review R3-06)
r += 1
put(ws, f"B{r}", "Unpriced cost lines counted as $0 (status 'needs quote' or 'needs founder decision', value blank, included)", font=F_BOLD, align=WRAP)
put(ws, f"C{r}", (f'=SUMPRODUCT((LEFT(G{su0}:G{sun},LEN("needs"))="needs")*(C{su0}:C{sun}="")*(N{su0}:N{sun}="Y"))'
                  f'+IF({R("card_extra")}="",1,0)+IF({R("kit_mail_per_office")}="",1,0)'), fmt=INT, font=F_BOLD)
put(ws, f"D{r}", "startup lines in section 11 plus extra tent cards and kit mailing (section 5). Each adds $0 to the low point and the capital to commit until you type a figure.", font=F_NOTE)
REF["unpriced_count"] = f"Inputs!$C${r}"
widths(ws, {"A": 18, "B": 50, "C": 15, "D": 18, "E": 10, "F": 10, "G": 25, "H": 44, "I": 60, "J": 12, "K": 9,
            "L": 12, "M": 40, "N": 9, "O": 12, "P": 12, "Q": 12, "R": 12, "S": 9, "T": 12})
ws.freeze_panes = "C5"

# ==========================================================================
# Scenarios
# ==========================================================================
ws = WS["Scenarios"]
title(ws, "Scenarios A to D", "The plan's four decision situations as assumption sets. Pick one on Inputs ('Scenario in force'). The Active column feeds drops after Gate 3 and the steady state.")
banner(ws, "A3", "Planning estimates. Where a scenario does not name a figure, it follows the plan base (blue cells) and says so. Nothing here is a forecast of which scenario will happen.", "J3")
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
    # a lever a scenario does not name follows the plan base (=$C), so one Inputs cell still moves every scenario (review R3-04)
    ("sc_brands", "Brands per drop after Gate 3", [f"={R('std_brands_drop')}", "=$C{self}", "=$C{self}", "=$C{self}", 0], "brands", INT,
     "Plan: three brands per drop (Inputs, 'Brands per standard drop'). A, B and C do not name a figure, so they follow the plan base. D stops."),
    ("sc_renewal", "Renewal rate (share of brand slots that are renewals)", [f"={R('renewal_rate_base')}", 0.4, 0, "=C{self}", 0], "share", PCT,
     "A: '40% or more', low end. B: 'under 30%' and 'brands pay once': 0%, the low end of 0% to 29%. C: not named, plan base. D: 'No renewal'."),
    ("sc_new_offices", "New offices recruited per post-Gate-3 drop", [0, 4, 0, None, 0], "offices", INT,
     "A: 'Grow the roster to 20 to 30 offices': 4 new offices on each of the two decision-window drops take the 12-office roster to 20, the low end "
     "(derived, founder to confirm; review R3-08). C: 'replace the weakest offices'; the plan gives no count. Blank = 0; founder to set."),
    ("sc_price_after", "Standard price per office for drops after the decision date", [f"={R('price_std_office')}", 180, f"={R('price_std_office')}", f"={R('price_std_office')}", f"={R('price_std_office')}"], "USD per office", USD,
     "A: 'raise the standard price to $1,800 to $2,000' = $180 to $200 per office; low end."),
    ("sc_ss_drops", "Steady-state drops per month", [f"={R('plan_ss_drops')}", "=$C{self}", "=$C{self}", "=$C{self}", 0], "drops per month", INT,
     "Plan monthly picture: two drops a month (Inputs section 8). A, B and C follow the plan base. D stops."),
    ("sc_ss_brands", "Steady-state brands per drop", [f"={R('std_brands_drop')}", "=$C{self}", "=$C{self}", "=$C{self}", 0], "brands", INT,
     "Plan monthly picture: three-brand drops (Inputs, 'Brands per standard drop'). A, B and C follow the plan base. D stops."),
    ("sc_op_offices", "Offices on an office-paid tier (steady state)", [0, 0, 5, 0, 0], "offices", INT, "B: offices that named $100 a month or more; at least five."),
    ("sc_op_fee", "Office-paid fee per office per month", [None, None, 100, None, None], "USD per month", USD, "B: $100 to $200 a month; low end."),
    ("sc_op_cost", "Cost to serve one office-paid office per month", [None, None, None, None, None], "USD per month", USD,
     "Needs quote. The plan prices no cost for guaranteed twice-monthly curated drops."),
    ("sc_hire_rate", "Part-time delivery hire", [25, 25, None, None, None], "USD per hour", USD,
     "A: 'about $25 an hour once you run more than two drops a month'. It replaces drop-day hours (model reading)."),
    ("sc_hire_threshold", "Hire once steady-state drops per month exceed", [2, "=$C{self}", "=$C{self}", "=$C{self}", "=$C{self}"], "drops per month", INT,
     "Plan: 'more than two drops a month'. One rule for every scenario, so A to D follow the plan base."),
]
for i, (key, lab, vals, unit, fmt, note) in enumerate(levers):
    r = 10 + i
    put(ws, f"B{r}", lab, align=WRAP)
    for j, v in enumerate(vals):
        if isinstance(v, str):
            v = v.replace("{self}", str(r))
        c = put(ws, f"{CL(3 + j)}{r}", v, fmt=fmt)
        as_input(c)
        if isinstance(v, str) and v.startswith("="):
            c.fill = FILL_SCEN
        c.number_format = fmt
    put(ws, f"H{r}", f"=INDEX(C{r}:G{r},1,MATCH({R('active_scenario')},$C$5:$G$5,0))", fmt=fmt, font=F_BOLD, fill=FILL_KEY, border=BOX)
    for j, v in enumerate(vals):
        if isinstance(v, str):
            v = v.replace("{self}", str(r))
        put(ws, f"{CL(12 + j)}{r}", v, fmt=fmt, font=F_NOTE)
    put(ws, f"Q{r}", "=IF(AND(" + ",".join(f'{CL(3 + j)}{r}&""={CL(12 + j)}{r}&""' for j in range(5)) + '),"","changed")', font=Font(color="9C0006", bold=True))
    put(ws, f"I{r}", unit)
    put(ws, f"J{r}", note, align=WRAP)
    # 1 when the scenario in force leaves this lever blank (a 'needs quote' or 'founder to set' figure)
    put(ws, f"R{r}", f'=IF(INDEX(C{r}:G{r},1,MATCH({R("active_scenario")},$C$5:$G$5,0))="",1,0)', fmt=INT)
    ws.row_dimensions[r].height = 30
    REF[key] = f"Scenarios!$H${r}"
    REF[key + "_blank"] = f"Scenarios!$R${r}"
header_row(ws, 5, 12, ["default: Plan base", "default: A", "default: B", "default: C", "default: D", "Changed?", "Blank in force? (1 = needs a figure)"], height=30)
REF["scen_changed"] = "Scenarios!$Q$10:$Q$21"
put(ws, "B23", "How it works", font=F_BOLD)
put(ws, "B24", "The two decision-window drops on Schedule (DRP-004, DRP-005) take brands, renewals and new offices from the Active column. "
              "Type over those Schedule cells to replace the scenario with real plans. The steady-state view and the sensitivity tables use the Active column too. "
              "Drops before Gate 3 do not change with the scenario. A lever left blank in the scenario in force counts as zero, and column R flags it: "
              "scenario B's office-paid revenue is left out of the steady-state net until its cost to serve is quoted.", align=WRAP)
ws.merge_cells("B24:J24")
ws.row_dimensions[24].height = 62
widths(ws, {"A": 3, "B": 46, "C": 18, "D": 22, "E": 22, "F": 22, "G": 18, "H": 14, "I": 14, "J": 60, "K": 3, "L": 11, "M": 11, "N": 11, "O": 11, "P": 11, "Q": 10, "R": 14})
ws.freeze_panes = "C6"

# ==========================================================================
# Schedule
# ==========================================================================
ws = WS["Schedule"]
title(ws, "Drop schedule", "One row per drop. Edit dates, delivery model, offices, brands and renewals. Rows marked derived are the simplest schedule that meets the plan; founder to confirm.")
banner(ws, "A3", "Planning estimates, not a forecast. Drop days are Tuesday or Wednesday only; no window may overlap a blackout (Lists). Set 'Actuals in' to Y once a drop's actuals are pasted, and the model switches that drop from plan to actual.", "T3")
SCH_HDR = ["drop_id", "Label", "Basis", "Post-Gate-3 sequence", "Drop date", "Day", "Delivery model", "Tier", "Offices", "New offices",
           "Brands", "of which renewals", "of which founding-rate renewals", "Actuals in (Y/N)", "Notes",
           "Tue or Wed?", "Window closes (T+4)", "Blackout clash?", "Units brands ship (incl. reserve)", "Row check",
           "Office slots on drops in the last four weeks", "Roster to date (new offices so far)", "Office fatigue", "Changed from the derived default?",
           # brand wins the schedule needs, beside the pipeline's actual counts (review R1-07)
           "Sign by (latest deposit or full payment)", "New brand wins needed (brands less renewals)", "Qualified brand conversations implied (wins / close rate)",
           "Wins needed, cumulative to this sign-by date", "Conversations implied, cumulative", "Actual: brands paid by this sign-by date (Pipeline)",
           "Actual: brand conversations by this sign-by date (Pipeline)",
           # results timing against the decision date (review R1-04)
           "Debrief (T+10)", "Results after the decision date?", "Debrief date, if after the decision",
           # roster that avoids a second drop within four weeks (review R1-16)
           "Offices to add so none gets two drops within four weeks",
           # the storage unit starts with the first of these (review R2-06)
           "Standard drop that runs: its date (sets the storage start)"]
assert CL(len(SCH_HDR)) == "AJ"
header_row(ws, 6, 1, SCH_HDR, height=70)
DEF0 = len(SCH_HDR) + 2      # derived-default copies start two columns after the last column
gm = R("goal_offices")
sched = [
    ("DRP-001", "Campaign zero (founding)", "derived: CONTRACTS s3", None, D(2027, 1, 12), "founder", "founding", "=" + R("c0_offices"), "=IF(N(K7)=0,0,I7)", "=" + R("c0_brands"), 0, 0,
     "Stretch option Tue 2026-12-08 only if both brands pay by 2026-11-20. Brands asked to ship by 2026-12-22."),
    ("DRP-002", "Standard run 1", "derived: CONTRACTS s3", None, D(2027, 2, 9), "courier", "standard", "=" + R("std_offices_drop"), "=IF(N(K8)=0,0,MAX(0,I8-SUM(J$7:J7)))", "=" + R("std_brands_drop"), 0, 0,
     "Campaigns one and two: founder plus courier (plan). New offices fill the drop: five take the roster from 5 to 10. No founding renewal: its latest signature (T-10, 2027-01-26) is two business days after the campaign-zero report."),
    ("DRP-003", "Standard run 2", "derived: CONTRACTS s3", None, D(2027, 2, 23), "courier", "standard", "=" + R("std_offices_drop"), f"=IF(N(K9)=0,0,MAX(0,MIN(I9,{gm}-SUM(J$7:J8))))", "=" + R("std_brands_drop"), 0, 0,
     "New offices reach the six-month goal of 12 active offices (two). Two weeks after run 1, so most offices get two drops in February. No founding renewal by default (README assumption 18)."),
    ("DRP-004", "Decision window drop 1", "derived: scenario", 1, D(2027, 3, 23), "direct-ship", "standard", "=" + R("std_offices_drop"), "sc", "sc", "sc", 0,
     "Campaign three onward: brands ship direct (plan). Brands, renewals and new offices follow the scenario in force. Not in the plan's roadmap table; derived from the decision rule's 'two extra drops'."),
    ("DRP-005", "Decision window drop 2", "derived: scenario", 2, D(2027, 4, 6), "direct-ship", "standard", "=" + R("std_offices_drop"), "sc", "sc", "sc", 0,
     "Second extra drop (scenario B's 'two more drops'; two drops a month in the base). Its debrief (T+10) lands after the 2027-04-09 decision: see REPORT.md, question 1."),
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
    # brand wins needed and conversations implied, beside the pipeline's actual counts
    put(ws, f"Y{r}", f'=IF(OR(E{r}="",N(K{r})=0),"",WORKDAY(E{r},-IF(H{r}="founding",{R("fnd_pay_lead_bd")},{R("std_sign_lead_bd")}),{R("holidays")}))', fmt=DATE)
    put(ws, f"Z{r}", f'=IF(Y{r}="","",N(K{r})-N(L{r}))', fmt=INT)
    put(ws, f"AA{r}", f'=IF(Z{r}="","",Z{r}/{R("close_rate")})', fmt='0')
    put(ws, f"AB{r}", f'=IF(Y{r}="","",SUMIFS($Z${DROP0}:$Z${DROPN},$Y${DROP0}:$Y${DROPN},"<="&Y{r}))', fmt=INT)
    put(ws, f"AC{r}", f'=IF(AB{r}="","",AB{r}/{R("close_rate")})', fmt='0')
    put(ws, f"AD{r}", f'=IF(Y{r}="","",SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"paid",{R("PL_date")},"<="&Y{r}))', fmt=INT)
    put(ws, f"AE{r}", f'=IF(Y{r}="","",SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"conversation",{R("PL_date")},"<="&Y{r}))', fmt=INT)
    # results timing against the decision date
    put(ws, f"AF{r}", f'=IF(Y{r}="","",WORKDAY(E{r},{R("debrief_bd")},{R("holidays")}))', fmt=DDATE)
    put(ws, f"AG{r}", f'=IF(AF{r}="","",IF(AND(E{r}>{R("gate3_date")},E{r}<={R("decision_date")},AF{r}>{R("decision_date")}),"after the decision","ok"))', align=WRAP)
    put(ws, f"AH{r}", f'=IF(AG{r}="after the decision",AF{r},"")', fmt=DDATE)
    put(ws, f"AI{r}", f'=IF(U{r}="","",MIN(N(I{r})-N(J{r}),MAX(0,U{r}-V{r})))', fmt=INT)
    put(ws, f"AJ{r}", f'=IF(AND(H{r}="standard",N(K{r})>0,E{r}<>""),E{r},"")', fmt=DATE)
    dcols = "EGHIJKLM"
    for j, col in enumerate(dcols):
        dv = vals.get(col)
        put(ws, f"{CL(DEF0 + j)}{r}", dv, fmt=DATE if col == "E" else None, font=F_NOTE)
    put(ws, f"X{r}", "=IF(AND(" + ",".join(f'{col}{r}&""={CL(DEF0 + j)}{r}&""' for j, col in enumerate(dcols)) + '),"","changed")', font=Font(color="9C0006", bold=True))
    ws.row_dimensions[r].height = 56
    for col in [CL(k) for k in range(1, len(SCH_HDR) + 1)]:
        ws[f"{col}{r}"].alignment = Alignment(vertical="top", wrap_text=True)
add_list_validation(ws, f"G{DROP0}:G{DROPN}", "=" + R("L_models"))
add_list_validation(ws, f"H{DROP0}:H{DROPN}", "=" + R("L_tiers"))
add_list_validation(ws, f"N{DROP0}:N{DROPN}", "=" + R("L_yn"))
ok_cf(ws, f"P{DROP0}:P{DROPN}", bad=['"not Tue/Wed"'])
ok_cf(ws, f"R{DROP0}:R{DROPN}", bad=['"clash"'])
ok_cf(ws, f"T{DROP0}:T{DROPN}", bad=['"check"', '"date missing"'])
ok_cf(ws, f"W{DROP0}:W{DROPN}")
ws.conditional_formatting.add(f"W{DROP0}:W{DROPN}", FormulaRule(formula=[f'LEFT(W{DROP0},LEN("some"))="some"'], fill=PatternFill("solid", fgColor="FCE4D6")))
ok_cf(ws, f"AG{DROP0}:AG{DROPN}")
ws.conditional_formatting.add(f"AG{DROP0}:AG{DROPN}", CellIsRule(operator="equal", formula=['"after the decision"'], fill=PatternFill("solid", fgColor="FCE4D6")))
header_row(ws, 6, DEF0, ["default date", "default model", "default tier", "default offices", "default new offices", "default brands", "default renewals", "default founding renewals"], height=70)
put(ws, f"{CL(DEF0)}5", "Derived defaults (for the 'Changed' flag; do not edit)", font=F_NOTE)
put(ws, "A4", "Yellow = your input. Blue = follows Inputs or the scenario in force; type over it to replace. Red 'changed' = the row no longer matches the derived default.", font=F_NOTE)
put(ws, "Y5", "Brand wins the schedule needs, beside the pipeline's actual counts", font=F_BOLD)
put(ws, "AF5", "Results against the decision date", font=F_BOLD)
REF["sched_fatigue"] = f"Schedule!$W${DROP0}:$W${DROPN}"
REF["sched_changed"] = f"Schedule!$X${DROP0}:$X${DROPN}"
REF["sched_after"] = f"Schedule!$AG${DROP0}:$AG${DROPN}"
REF["sched_after_date"] = f"Schedule!$AH${DROP0}:$AH${DROPN}"
REF["sched_add_offices"] = f"Schedule!$AI${DROP0}:$AI${DROPN}"
r = DROPN + 1
put(ws, f"B{r}", "Totals", font=F_BOLD)
for col in "IJKLM":
    put(ws, f"{col}{r}", f"=SUM({col}{DROP0}:{col}{DROPN})", font=F_BOLD)
put(ws, f"S{r}", f"=SUM(S{DROP0}:S{DROPN})", fmt='#,##0', font=F_BOLD)
put(ws, f"Z{r}", f"=SUM(Z{DROP0}:Z{DROPN})", fmt=INT, font=F_BOLD)
put(ws, f"AA{r}", f"=SUM(AA{DROP0}:AA{DROPN})", fmt='0', font=F_BOLD)
put(ws, f"B{r + 2}", "Offices column counts every office on the drop; New offices counts the ones visiting for the first time (4 hours each instead of 1). "
                     "Brands counts brand campaigns on the drop; renewals are part of that count (2 hours each instead of 6 or 10). "
                     "Tier sets the price of the new brands; founding-rate renewals pay the founding rate per office.", align=WRAP)
ws.merge_cells(f"B{r + 2}:O{r + 2}")
ws.row_dimensions[r + 2].height = 45
put(ws, f"B{r + 3}", "Columns Y to AE: the new brand wins each drop needs and the qualified conversations they imply at the close rate on Inputs, cumulated to each drop's sign-by date, "
                     "beside the Pipeline's actual distinct brands paid and brand conversations by that date. Columns AF to AH: each drop's debrief date; a drop in the decision window "
                     "whose debrief lands after the decision date is flagged, because its results cannot count toward the decision rule. Column AI: offices to add so no office gets a "
                     "second drop within four weeks (the Dashboard shows the Gate 3 rate with them). Column AJ: the date of each standard drop that runs; "
                     "the storage unit is rented from the first of the month of the earliest one.", align=WRAP)
ws.merge_cells(f"B{r + 3}:O{r + 3}")
ws.row_dimensions[r + 3].height = 60
widths(ws, {"A": 10, "B": 24, "C": 20, "D": 10, "E": 12, "F": 6, "G": 12, "H": 10, "I": 8, "J": 8, "K": 8, "L": 10, "M": 12,
            "N": 9, "O": 50, "P": 11, "Q": 15, "R": 10, "S": 12, "T": 10, "U": 12, "V": 12, "W": 24, "X": 12,
            "Y": 12, "Z": 11, "AA": 13, "AB": 12, "AC": 13, "AD": 13, "AE": 13, "AF": 15, "AG": 14, "AH": 15, "AI": 14, "AJ": 13})
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
           ("next_flag", "Upcoming drop (1/0)", INT),
           ("cash_plan", "Net cash inside the six months, plan (receipts less direct costs)", USD),
           ("cash_live", "Net cash inside the six months, live", USD),
           # the Dashboard's next drop is the earliest upcoming date, not the first matching row (review R3-03)
           ("next_date", "Upcoming drop: its date (the Dashboard takes the earliest)", DATE)]
start = openpyxl.utils.column_index_from_string(LAST_ENGINE_COL) + 2   # AO
for i, (k, h, f) in enumerate(ct_cols):
    CT[k] = CL(start + i)
    put(ws, f"{CT[k]}6", h, font=F_H, fill=FILL_H, align=CENTER, border=BOX)
ws.merge_cells(f"{CT['pay_fnd_date']}5:{CT['tr_date']}5")
put(ws, f"{CT['pay_fnd_date']}5", "Cash timing on the plan's terms (feeds Cash_Flow)", font=F_BOLD, fill=FILL_SEC, align=CENTER)
ws.merge_cells(f"{CT['actuals_in']}5:{CT['next_flag']}5")
put(ws, f"{CT['actuals_in']}5", "Live: actual where Actuals in = Y, otherwise plan", font=F_BOLD, fill=FILL_SEC, align=CENTER)
ws.merge_cells(f"{CT['cash_plan']}5:{CT['cash_live']}5")
put(ws, f"{CT['cash_plan']}5", "Per-drop cash inside the 26 weeks", font=F_BOLD, fill=FILL_SEC, align=CENTER)
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
        "storage_on": f'=IF(AND({R("storage_choice")}="unit",B{r}<>"",{R("storage_start")}<>"",B{r}>={R("storage_start")},OR({R("storage_end")}="",B{r}<={R("storage_end")})),1,0)',
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
    # the same cash the Cash_Flow tab books for this drop, inside the 26 weeks (checked on Checks)
    inwin = lambda dc: f'AND({CT[dc]}{r}<>"",{CT[dc]}{r}>={R("week1_start")},{CT[dc]}{r}<={R("horizon_end")})'
    ws[f"{CT['cash_plan']}{r}"] = (f"=IF({inwin('pay_fnd_date')},{CT['pay_fnd_amt']}{r}-{CT['proc_fnd']}{r},0)"
                                   f"+IF({inwin('pay_dep_date')},{CT['pay_dep_amt']}{r}-{CT['proc_dep']}{r},0)"
                                   f"+IF({inwin('pay_bal_date')},{CT['pay_bal_amt']}{r}-{CT['proc_bal']}{r},0)"
                                   f"-IF({inwin('kit_date')},{EC['kit']}{r}+{EC['kit_mail']}{r},0)"
                                   f"-IF({inwin('tr_date')},{EC['transport']}{r},0)")
    ws[f"{CT['cash_live']}{r}"] = f'=IF({ai}="Y",Drop_Actuals!AM{r},{CT["cash_plan"]}{r})'
    ws[f"{CT['next_date']}{r}"] = f'=IF({CT["next_flag"]}{r}=1,B{r},"")'
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
for k in ["pay_fnd_amt", "pay_dep_amt", "pay_bal_amt", "proc_fnd", "proc_dep", "proc_bal", "live_rev", "live_cost", "live_hours", "live_contrib", "cash_plan", "cash_live"]:
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
_ac_last, _ach = CL(len(AC_COLS)), [CL(AC_H0 + k) for k in range(7)]   # helpers AL to AR
title(ws, "Actuals: one row per brand campaign",
      f"Paste campaign-ops/exports/campaign_actuals.csv with its header in row 4: exactly these {len(AC_COLS)} columns, A to {_ac_last}. "
      f"Columns {CL(len(AC_COLS) + 1)} to {CL(AC_H0 - 1)} stay blank (Checks flags anything pasted there). Columns {_ach[0]} onward are model helpers; do not paste over them.")
banner(ws, "A3", "Ladder rungs stay separate: delivered, placed, depleted, responded (tried is a survey answer), scanned, purchased (code redemptions). Incremental is not measured. There is no field for sales lift.", f"{_ac_last}3")
header_row(ws, 4, 1, AC_COLS, height=45)
ACH = ["drop actuals in?", "balance_usd (revenue less deposit)", "responses per office used", "report due (T+7)", "report late?",
       # the renewal rate counts brands, not campaigns (review R3-07): 1 on a brand's first Y or N answer, and on its first Y
       "brand's first Y or N renewal answer (1/0)", "brand's first Y renewal answer (1/0)"]
header_row(ws, 4, AC_H0, ACH, height=45)
for i, col in enumerate(AC_COLS):
    L = CL(i + 1)
    for r in range(AC0, ACN + 1):
        c = ws[f"{L}{r}"]
        c.fill = FILL_IN
        if col.endswith("_date"):
            c.number_format = DATE
        elif col.endswith("_usd"):
            c.number_format = USD
fl, bal, rpo, due, late, b_ans, b_ren = _ach
for r in range(AC0, ACN + 1):
    yn = f'COUNTIFS(F${AC0}:F{r},F{r},W${AC0}:W{r},"Y")+COUNTIFS(F${AC0}:F{r},F{r},W${AC0}:W{r},"N")'
    ws[f"{b_ans}{r}"] = f'=IF(OR(W{r}="Y",W{r}="N"),IF(F{r}="",1,IF({yn}=1,1,0)),0)'
    ws[f"{b_ren}{r}"] = f'=IF(W{r}="Y",IF(F{r}="",1,IF(COUNTIFS(F${AC0}:F{r},F{r},W${AC0}:W{r},"Y")=1,1,0)),0)'

    ws[f"{fl}{r}"] = f'=IF(B{r}="","",IFERROR(INDEX({R("sched_actuals")},MATCH(B{r},{R("sched_ids")},0)),"not in schedule"))'
    ws[f"{bal}{r}"] = f'=IF(B{r}="","",N(R{r})-N(X{r}))'
    ws[f"{rpo}{r}"] = f'=IF(B{r}="","",IF(Z{r}<>"",Z{r},IF(N(G{r})>0,N(N{r})/G{r},"")))'
    ws[f"{due}{r}"] = f'=IF(OR(B{r}="",C{r}=""),"",WORKDAY(C{r},{R("g2_report_bd")},{R("holidays")}))'
    ws[f"{late}{r}"] = f'=IF(B{r}="","",IF(U{r}="","missing",IF(U{r}>{due}{r},"Y","N")))'
    ws[f"{bal}{r}"].number_format = USD
    ws[f"{rpo}{r}"].number_format = '0.0'
    ws[f"{due}{r}"].number_format = DATE
add_list_validation(ws, f"D{AC0}:D{ACN}", "=" + R("L_models"))
add_list_validation(ws, f"E{AC0}:E{ACN}", "=" + R("L_tiers"))
add_list_validation(ws, f"V{AC0}:V{ACN}", "=" + R("L_rebuy"))
add_list_validation(ws, f"W{AC0}:W{ACN}", "=" + R("L_renewed"))
for i, col in enumerate(AC_COLS):
    REF["AC_" + col] = f"Actuals_Campaigns!${CL(i + 1)}${AC0}:${CL(i + 1)}${ACN}"
REF.update({"AC_brand_answered": f"Actuals_Campaigns!${b_ans}${AC0}:${b_ans}${ACN}", "AC_brand_renewed": f"Actuals_Campaigns!${b_ren}${AC0}:${b_ren}${ACN}"})
REF.update({"AC_flag": f"Actuals_Campaigns!${fl}${AC0}:${fl}${ACN}", "AC_balance": f"Actuals_Campaigns!${bal}${AC0}:${bal}${ACN}",
            "AC_rpo": f"Actuals_Campaigns!${rpo}${AC0}:${rpo}${ACN}", "AC_late": f"Actuals_Campaigns!${late}${AC0}:${late}${ACN}"})
# dates and amounts that arrived as text (review R3-01): filled cells in date or number columns that are not numbers
REF["AC_text_bad"] = "+".join(f"COUNTA(Actuals_Campaigns!{a})-COUNT(Actuals_Campaigns!{a})" for a in
                              (f"$C${AC0}:$C${ACN}", f"$G${AC0}:$U${ACN}", f"$X${AC0}:$Z${ACN}"))
# header check (review R1-06): row 4 must match HANDOFF and the buffer columns must stay empty
REF["AC_hdr_bad"] = (f'SUMPRODUCT((Actuals_Campaigns!$A$4:${_ac_last}$4<>{HDR_ROW["campaign_actuals.csv"]})*1)'
                     f'+COUNTA(Actuals_Campaigns!${CL(len(AC_COLS) + 1)}$4:${CL(AC_H0 - 1)}${ACN})')
widths(ws, {CL(i + 1): 13 for i in range(len(AC_COLS))})
widths(ws, {CL(k): 3 for k in range(len(AC_COLS) + 1, AC_H0)})
widths(ws, {fl: 14, bal: 14, rpo: 12, due: 12, late: 10, b_ans: 13, b_ren: 13})
ws.freeze_panes = "C5"

ws = WS["Actuals_DropCosts"]
_dc_last, _dch = CL(len(DC_COLS)), CL(DC_H0)
title(ws, "Actuals: one row per drop, direct costs only",
      f"Paste campaign-ops/exports/drop_costs.csv with its header in row 4: exactly these {len(DC_COLS)} columns, A to {_dc_last}. Columns {CL(len(DC_COLS) + 1)} to {CL(DC_H0 - 1)} stay blank. "
      "Monthly overhead is not here; Cash_Flow pays it once.")
header_row(ws, 4, 1, DC_COLS, height=32)
header_row(ws, 4, DC_H0, ["drop actuals in?"], height=32)
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
    ws[f"{_dch}{r}"] = f'=IF(A{r}="","",IFERROR(INDEX({R("sched_actuals")},MATCH(A{r},{R("sched_ids")},0)),"not in schedule"))'
REF["DC_flag"] = f"Actuals_DropCosts!${_dch}${DC0}:${_dch}${DCN}"
REF["DC_text_bad"] = "+".join(f"COUNTA(Actuals_DropCosts!{a})-COUNT(Actuals_DropCosts!{a})" for a in (f"$B${DC0}:$B${DCN}", f"$D${DC0}:$H${DCN}"))
REF["DC_hdr_bad"] = (f'SUMPRODUCT((Actuals_DropCosts!$A$4:${_dc_last}$4<>{HDR_ROW["drop_costs.csv"]})*1)'
                     f'+COUNTA(Actuals_DropCosts!${CL(len(DC_COLS) + 1)}$4:${CL(DC_H0 - 1)}${DCN})')
add_list_validation(ws, f"C{DC0}:C{DCN}", "=" + R("L_models"))
widths(ws, {CL(i + 1): 14 for i in range(len(DC_COLS))})
widths(ws, {CL(k): 3 for k in range(len(DC_COLS) + 1, DC_H0)})
widths(ws, {"I": 40, _dch: 16})
ws.freeze_panes = "B5"

# ==========================================================================
# Hours_Log and Toggl_Import
# ==========================================================================
ws = WS["Hours_Log"]
_hl_last = CL(len(HL_COLS))
title(ws, "Founder hours log", f"Type one row per entry, or paste campaign-ops/exports/hours_log.csv (header in row 4: exactly these {len(HL_COLS)} columns, A to {_hl_last}). "
      f"Leave drop_id blank for time that is not for a drop. Totals per drop and per week start in column {CL(HT0)}.")
banner(ws, "A3", "Activity must be one of the seven keys (Lists). Toggl entries add in from the Toggl_Import tab.", f"{_hl_last}3")
header_row(ws, 4, 1, HL_COLS, height=30)
for r in range(HL0, HLN + 1):
    for L in [CL(k) for k in range(1, len(HL_COLS) + 1)]:
        ws[f"{L}{r}"].fill = FILL_IN
    ws[f"A{r}"].number_format = DATE
    ws[f"E{r}"].number_format = HRS
add_list_validation(ws, f"D{HL0}:D{HLN}", "=" + R("L_acts"))
REF.update({"HL_date": f"Hours_Log!$A${HL0}:$A${HLN}", "HL_drop": f"Hours_Log!$B${HL0}:$B${HLN}",
            "HL_act": f"Hours_Log!$D${HL0}:$D${HLN}", "HL_hours": f"Hours_Log!$E${HL0}:$E${HLN}"})
REF["HL_text_bad"] = "+".join(f"COUNTA(Hours_Log!{a})-COUNT(Hours_Log!{a})" for a in (f"$A${HL0}:$A${HLN}", f"$E${HL0}:$E${HLN}"))
REF["HL_hdr_bad"] = (f'SUMPRODUCT((Hours_Log!$A$4:${_hl_last}$4<>{HDR_ROW["hours_log.csv"]})*1)'
                     f'+COUNTA(Hours_Log!${CL(len(HL_COLS) + 1)}$4:${CL(HT0 - 1)}${HLN})')
TGC = {k: CL(TGH0 + i) for i, k in enumerate(["date", "drop", "act", "hours"])}
REF.update({"TG_date": f"Toggl_Import!${TGC['date']}${TG0}:${TGC['date']}${TGN}", "TG_drop": f"Toggl_Import!${TGC['drop']}${TG0}:${TGC['drop']}${TGN}",
            "TG_act": f"Toggl_Import!${TGC['act']}${TG0}:${TGC['act']}${TGN}", "TG_hours": f"Toggl_Import!${TGC['hours']}${TG0}:${TGC['hours']}${TGN}"})
HC = lambda k: CL(HT0 + k)       # Hours_Log totals block columns
# per-drop totals
put(ws, f"{HC(0)}3", "Totals per drop (hand log plus Toggl)", font=F_SEC)
header_row(ws, 4, HT0, ["drop_id"] + ACT_KEYS + ["total"], height=30)
for i in range(N_DROPS):
    r = 5 + i
    put(ws, f"{HC(0)}{r}", f"=Schedule!A{DROP0 + i}")
    for j, key in enumerate(ACT_KEYS):
        L = HC(1 + j)
        ws[f"{L}{r}"] = (f"=SUMIFS({R('HL_hours')},{R('HL_drop')},${HC(0)}{r},{R('HL_act')},{L}$4)"
                         f"+SUMIFS({R('TG_hours')},{R('TG_drop')},${HC(0)}{r},{R('TG_act')},{L}$4)")
        ws[f"{L}{r}"].number_format = HRS
    put(ws, f"{HC(8)}{r}", f"=SUM({HC(1)}{r}:{HC(7)}{r})", fmt=HRS, font=F_BOLD)
r_all = 5 + N_DROPS          # 17
put(ws, f"{HC(0)}{r_all}", "All hours")
for j, key in enumerate(ACT_KEYS):
    L = HC(1 + j)
    ws[f"{L}{r_all}"] = f"=SUMIFS({R('HL_hours')},{R('HL_act')},{L}$4)+SUMIFS({R('TG_hours')},{R('TG_act')},{L}$4)"
    ws[f"{L}{r_all}"].number_format = HRS
put(ws, f"{HC(8)}{r_all}", f"=SUM({HC(1)}{r_all}:{HC(7)}{r_all})", fmt=HRS, font=F_BOLD)
put(ws, f"{HC(0)}{r_all + 1}", "Not linked to a scheduled drop")
for j in range(8):
    L = HC(1 + j)
    ws[f"{L}{r_all + 1}"] = f"={L}{r_all}-SUM({L}5:{L}{r_all - 1})"
    ws[f"{L}{r_all + 1}"].number_format = HRS
REF["HL_all_total"] = f"Hours_Log!${HC(8)}${r_all}"
REF["HL_unlinked_total"] = f"Hours_Log!${HC(8)}${r_all + 1}"
REF["HL_drop_cols"] = HC(1)    # first activity column of the per-drop table (row 5 = first Schedule row)
# weekly table
w0 = r_all + 4   # 21
put(ws, f"{HC(0)}{w0 - 1}", "Totals per week (hand log plus Toggl)", font=F_SEC)
header_row(ws, w0, HT0, ["week", "week starts"] + ACT_KEYS + ["total", "linked to a drop"], height=30)
for i in range(N_WEEKS):
    r = w0 + 1 + i
    put(ws, f"{HC(0)}{r}", i + 1)
    put(ws, f"{HC(1)}{r}", f"={R('week1_start')}" if i == 0 else f"={HC(1)}{r - 1}+{R('days_per_week')}", fmt=DATE)
    crit = f'{R("HL_date")},">="&${HC(1)}{r},{R("HL_date")},"<"&${HC(1)}{r}+{R("days_per_week")}'
    crit_t = f'{R("TG_date")},">="&${HC(1)}{r},{R("TG_date")},"<"&${HC(1)}{r}+{R("days_per_week")}'
    for j, key in enumerate(ACT_KEYS):
        L = HC(2 + j)
        ws[f"{L}{r}"] = (f"=SUMIFS({R('HL_hours')},{crit},{R('HL_act')},{L}${w0})"
                         f"+SUMIFS({R('TG_hours')},{crit_t},{R('TG_act')},{L}${w0})")
        ws[f"{L}{r}"].number_format = HRS
    put(ws, f"{HC(9)}{r}", f"=SUM({HC(2)}{r}:{HC(8)}{r})", fmt=HRS, font=F_BOLD)
    ws[f"{HC(10)}{r}"] = (f'=SUMIFS({R("HL_hours")},{crit},{R("HL_drop")},{R("drop_prefix")}&"*")'
                          f'+SUMIFS({R("TG_hours")},{crit_t},{R("TG_drop")},{R("drop_prefix")}&"*")')
    ws[f"{HC(10)}{r}"].number_format = HRS
wl = w0 + N_WEEKS
put(ws, f"{HC(0)}{wl + 1}", "Six months")
for k in range(2, 11):
    L = HC(k)
    put(ws, f"{L}{wl + 1}", f"=SUM({L}{w0 + 1}:{L}{wl})", fmt=HRS, font=F_BOLD)
REF["HL_week_total"] = f"Hours_Log!${HC(9)}${wl + 1}"
put(ws, f"{HC(0)}{wl + 3}", "Invalid activity keys in the hand log (should be 0)")
put(ws, f"{HC(9)}{wl + 3}", f"=COUNTA({R('HL_act')})-SUMPRODUCT(COUNTIF({R('HL_act')},{R('L_acts')}))", fmt=INT, font=F_BOLD)
REF["HL_invalid"] = f"Hours_Log!${HC(9)}${wl + 3}"
put(ws, f"{HC(0)}{wl + 4}", "Rows whose drop_id is not on Schedule (should be 0)")
put(ws, f"{HC(9)}{wl + 4}", f'=SUMPRODUCT(({R("HL_drop")}<>"")*(COUNTIF({R("sched_ids")},{R("HL_drop")})=0))', fmt=INT, font=F_BOLD)
REF["HL_badid"] = f"Hours_Log!${HC(9)}${wl + 4}"
put(ws, f"{HC(0)}{wl + 5}", "Hours outside the 26 weeks (dated before week 1 or after week 26)")
put(ws, f"{HC(9)}{wl + 5}", f"={HC(8)}{r_all}-{HC(9)}{wl + 1}", fmt=HRS, font=F_BOLD)
# hours inside the 26 weeks that no drop owns (discovery, general admin); the Dashboard's all-in rate uses the larger of this and the plan's discovery hours (review R2-03)
put(ws, f"{HC(0)}{wl + 6}", "Hours inside the 26 weeks not linked to a drop (feeds the Dashboard's six-month all-in rate)")
put(ws, f"{HC(9)}{wl + 6}", f"={HC(9)}{wl + 1}-{HC(10)}{wl + 1}", fmt=HRS, font=F_BOLD)
REF["HL_unlinked_6m"] = f"Hours_Log!${HC(9)}${wl + 6}"
HL_END = wl + 6
widths(ws, {"A": 12, "B": 10, "C": 11, "D": 20, "E": 7, "F": 30})
widths(ws, {CL(k): 3 for k in range(len(HL_COLS) + 1, HT0)})
widths(ws, {HC(0): 12, HC(1): 12})
for j in range(2, 11):
    ws.column_dimensions[HC(j)].width = 11
ws.freeze_panes = "A5"

ws = WS["Toggl_Import"]
_tg_last = CL(TG_LAST)
title(ws, "Toggl import (optional)", f"Paste a Toggl time-entry export with its header row in row 9, columns A to {_tg_last}. Name each Toggl project after the drop (DRP-001) and tag each entry with one activity key.")
banner(ws, "G3", "Toggl's own help says CSV and Excel exports are a paid-plan feature (Starter from $9 per license a month; support.toggl.com, opened 2026-10-23). "
                 "Do not upgrade without a written yes. On the free plan, type hours into Hours_Log instead. The header names in C4:C7 are unverified; edit them to match your export.", "P7")
put(ws, "B3", "Header text in your export for:", font=F_BOLD)
for i, (lab, default) in enumerate([("date", "Start date"), ("duration (hh:mm:ss)", "Duration"), ("project (drop_id)", "Project"), ("activity key", "Tags")]):
    r = 4 + i
    put(ws, f"B{r}", lab)
    as_input(put(ws, f"C{r}", default))
    put(ws, f"D{r}", f'=IFERROR(MATCH(C{r},$A$9:${_tg_last}$9,0),"")', fmt=INT)
    put(ws, f"E{r}", f'=IF(D{r}="","not found in row 9","column found")', font=F_NOTE)
put(ws, "B8", "Paste area (row 9 = Toggl header)", font=F_BOLD)
for L in [CL(i) for i in range(1, TG_LAST + 1)]:
    ws[f"{L}9"].fill = FILL_IN
header_row(ws, 9, TGH0, ["date", "drop_id", "activity", "hours"], height=30)
for r in range(TG0, TGN + 1):
    row_rng = f"$A{r}:${_tg_last}{r}"
    ws[f"{TGC['date']}{r}"] = (f'=IF($D$4="","",IF(INDEX({row_rng},1,$D$4)="","",IF(ISNUMBER(INDEX({row_rng},1,$D$4)),INDEX({row_rng},1,$D$4),'
                               f'IFERROR(DATEVALUE(INDEX({row_rng},1,$D$4)),""))))')
    ws[f"{TGC['drop']}{r}"] = (f'=IF(OR({TGC["date"]}{r}="",$D$6=""),"",IF(LEFT(INDEX({row_rng},1,$D$6),LEN({R("drop_prefix")}))={R("drop_prefix")},INDEX({row_rng},1,$D$6),""))')
    ws[f"{TGC['act']}{r}"] = (f'=IF(OR({TGC["date"]}{r}="",$D$7=""),"",TRIM(IFERROR(LEFT(INDEX({row_rng},1,$D$7),FIND(",",INDEX({row_rng},1,$D$7))-1),INDEX({row_rng},1,$D$7))))')
    ws[f"{TGC['hours']}{r}"] = (f'=IF(OR({TGC["date"]}{r}="",$D$5=""),0,IFERROR(IF(ISNUMBER(INDEX({row_rng},1,$D$5)),INDEX({row_rng},1,$D$5),TIMEVALUE(INDEX({row_rng},1,$D$5)))*{R("hours_per_day")},0))')
    ws[f"{TGC['date']}{r}"].number_format = DATE
    ws[f"{TGC['hours']}{r}"].number_format = HRS
_tk, _tv = CL(TGH0 + 5), CL(TGH0 + 6)
put(ws, f"{_tk}9", "Checks", font=F_BOLD)
put(ws, f"{_tk}10", "Rows with a date but zero hours")
put(ws, f"{_tv}10", f'=COUNTIFS({R("TG_date")},">0",{R("TG_hours")},0)', fmt=INT)
put(ws, f"{_tk}11", "Rows whose activity is not one of the seven keys")
put(ws, f"{_tv}11", f'=COUNTIF({R("TG_date")},">0")-SUMPRODUCT(COUNTIF({R("TG_act")},{R("L_acts")}))', fmt=INT)
put(ws, f"{_tk}12", "Total Toggl hours read")
put(ws, f"{_tv}12", f"=SUM({R('TG_hours')})", fmt=HRS)
REF["TG_zero"] = f"Toggl_Import!${_tv}$10"
REF["TG_invalid"] = f"Toggl_Import!${_tv}$11"
REF["TG_total"] = f"Toggl_Import!${_tv}$12"
widths(ws, {"B": 30, "C": 16, "D": 8, "E": 20, TGC["date"]: 12, TGC["drop"]: 10, TGC["act"]: 20, TGC["hours"]: 8, _tk: 44, _tv: 10})
ws.freeze_panes = "A10"

# ==========================================================================
# Pipeline
# ==========================================================================
ws = WS["Pipeline"]
_pl_last = CL(len(PL_COLS))
title(ws, "Pipeline log", f"One row per event. Paste desk-drop-outreach/exports/pipeline_log.csv with its header in row 4 (exactly these {len(PL_COLS)} columns, A to {_pl_last}), or type rows. "
      f"Keep rows in date order. Columns {CL(len(PL_COLS) + 1)} to {CL(PLH0 - 1)} stay blank; helpers start in column {CL(PLH0)}.")
banner(ws, "A3", "value_number: headcount for signed; USD received in this payment for paid (Gate 1 counts a brand once its payments add up to the founding package price); "
                 "USD per month for an office budget_probe; USD per campaign for a brand budget_probe, named before hearing $1,500 (log a later answer as a second row with notes = after_1500); "
                 "USD committed for a renewal_answer, with value_text yes, maybe or no.", f"{_pl_last}3")
header_row(ws, 4, 1, PL_COLS, height=30)
header_row(ws, 4, PLH0, ["first of this org and event", "brand would pay threshold, controls budget", "first such brand",
                         "office named office-paid threshold", "first such office", "renewal 'yes' at threshold price", "first such renewing brand",
                         "budget_probe with a number, before the $1,500 anchor", "office probe value (first per office)", "brand probe value before $1,500 (first per brand)",
                         "brand probe value after $1,500 (first per brand)", "brand paid in full on this row (payments reach the founding package price)"], height=70)
c_ = PLC
for r in range(PL0, PLN + 1):
    for L in [CL(k) for k in range(1, len(PL_COLS) + 1)]:
        ws[f"{L}{r}"].fill = FILL_IN
    ws[f"A{r}"].number_format = DATE
    ws[f"{c_['first']}{r}"] = f'=IF(C{r}="","",IF(COUNTIFS(C${PL0}:C{r},C{r},E${PL0}:E{r},E{r})=1,1,0))'
    ws[f"{c_['g0b']}{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="brand",E{r}="budget_probe",N(F{r})>={R("g0_brand_usd")},H{r}="Y"),1,0))'
    ws[f"{c_['g0b_first']}{r}"] = f'=IF({c_["g0b"]}{r}=1,IF(COUNTIFS(C${PL0}:C{r},C{r},{c_["g0b"]}${PL0}:{c_["g0b"]}{r},1)=1,1,0),0)'
    ws[f"{c_['op']}{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="office",E{r}="budget_probe",N(F{r})>={R("dr_switch_usd")}),1,0))'
    ws[f"{c_['op_first']}{r}"] = f'=IF({c_["op"]}{r}=1,IF(COUNTIFS(C${PL0}:C{r},C{r},{c_["op"]}${PL0}:{c_["op"]}{r},1)=1,1,0),0)'
    # a renewal counts only when the answer is yes and the committed amount clears the threshold, once per brand (review R1-08)
    ws[f"{c_['g3']}{r}"] = f'=IF(C{r}="",0,IF(AND(B{r}="brand",E{r}="renewal_answer",TRIM(G{r})="yes",N(F{r})>={R("g3_renewal_usd")}),1,0))'
    ws[f"{c_['g3_first']}{r}"] = f'=IF({c_["g3"]}{r}=1,IF(COUNTIFS(C${PL0}:C{r},C{r},{c_["g3"]}${PL0}:{c_["g3"]}{r},1)=1,1,0),0)'
    # medians use one answer per organisation: its first numeric budget_probe given before the $1,500 anchor (review R2-05)
    pk = c_["probe_ok"]
    ws[f"{pk}{r}"] = f'=IF(AND(E{r}="budget_probe",ISNUMBER(F{r}),I{r}<>{R("L_after")}),1,0)'
    first_ok = f'COUNTIFS(C${PL0}:C{r},C{r},{pk}${PL0}:{pk}{r},1)=1'
    ws[f"{c_['oprobe']}{r}"] = f'=IF(AND(B{r}="office",{pk}{r}=1,{first_ok}),F{r},"")'
    ws[f"{c_['bprobe']}{r}"] = f'=IF(AND(B{r}="brand",{pk}{r}=1,{first_ok}),F{r},"")'
    ws[f"{c_['bprobe_after']}{r}"] = (f'=IF(AND(B{r}="brand",E{r}="budget_probe",ISNUMBER(F{r}),I{r}={R("L_after")}),'
                                      f'IF(COUNTIFS(C${PL0}:C{r},C{r},E${PL0}:E{r},"budget_probe",I${PL0}:I{r},{R("L_after")})=1,F{r},""),"")')
    # Gate 1 'paid in full': the row on which a brand's payments first add up to the founding package price (review R2-04); rows in date order
    cum = f'SUMIFS(F${PL0}:F{r},B${PL0}:B{r},"brand",C${PL0}:C{r},C{r},E${PL0}:E{r},"paid")'
    ws[f"{c_['paid_full']}{r}"] = (f'=IF(AND(B{r}="brand",E{r}="paid",ISNUMBER(F{r})),'
                                   f'IF(AND({cum}>={R("fnd_pkg_price")},{cum}-F{r}<{R("fnd_pkg_price")}),1,0),0)')
add_list_validation(ws, f"B{PL0}:B{PLN}", "=" + R("L_side"))
add_list_validation(ws, f"E{PL0}:E{PLN}", "=" + R("L_event"))
add_list_validation(ws, f"H{PL0}:H{PLN}", "=" + R("L_yn"))
REF["PL_text_bad"] = "+".join(f"COUNTA(Pipeline!{a})-COUNT(Pipeline!{a})" for a in (f"$A${PL0}:$A${PLN}", f"$F${PL0}:$F${PLN}"))
REF["PL_hdr_bad"] = (f'SUMPRODUCT((Pipeline!$A$4:${_pl_last}$4<>{HDR_ROW["pipeline_log.csv"]})*1)'
                     f'+COUNTA(Pipeline!${CL(len(PL_COLS) + 1)}$4:${CL(PLH0 - 1)}${PLN})')
# summary block
SM, SV, SC = CL(PLS), CL(PLS + 1), CL(PLS + 2)
put(ws, f"{SM}3", "Summary (distinct organisations)", font=F_SEC)
header_row(ws, 4, PLS, ["Measure", "Count", "Cut-off"], height=30)
summ = [
    ("pl_g0_office_conv", "Office conversations by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"conversation",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_office_yes", "Offices yes in principle by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"yes_in_principle",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_brand_conv", "Brand conversations by Gate 0", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"conversation",{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g0_brand_yes", "Brands that would pay the threshold and control the budget, by Gate 0", f'=SUMIFS({R("PL_g0b_first")},{R("PL_date")},"<="&{R("gate0_date")})', "gate0_date"),
    ("pl_g1_signed", "Offices signed by Gate 1", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g1_headcount", "Combined Tuesday headcount of offices signed by Gate 1", f'=SUMIFS({R("PL_value")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_first")},1,{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g1_paid", "Brands paid in full by Gate 1 (payments add up to the founding package price)", f'=SUMIFS({R("PL_paid_full")},{R("PL_date")},"<="&{R("gate1_date")})', "gate1_date"),
    ("pl_g3_renewals", "Brands that renewed at the threshold price (answer yes), by Gate 3", f'=SUMIFS({R("PL_g3_first")},{R("PL_date")},"<="&{R("gate3_date")})', "gate3_date"),
    ("pl_op_offices", "Offices that named the office-paid threshold, to date", f'=SUMIFS({R("PL_op_first")},{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_signed_all", "Offices signed, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"signed",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_optout_office", "Offices opted out, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"office",{R("PL_event")},"opt_out",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_paid_all", "Brands with any payment, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"paid",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_brand_conv_all", "Brand conversations, to date", f'=SUMIFS({R("PL_first")},{R("PL_side")},"brand",{R("PL_event")},"conversation",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_outreach", "Outreach messages sent, to date (events, not distinct)", f'=COUNTIFS({R("PL_event")},"outreach_sent",{R("PL_date")},"<="&{R("as_of")})', "as_of"),
    ("pl_med_office", "Median office budget probe (USD per month; first answer per office)", f'=IF(COUNT({R("PL_oprobe")})>0,MEDIAN({R("PL_oprobe")}),"")', ""),
    ("pl_med_brand", "Median brand willingness to pay before hearing $1,500 (USD per campaign; first answer per brand)", f'=IF(COUNT({R("PL_bprobe")})>0,MEDIAN({R("PL_bprobe")}),"")', ""),
    ("pl_med_brand_after", "Median brand answer after hearing $1,500 (notes = after_1500; first per brand)", f'=IF(COUNT({R("PL_bprobe_after")})>0,MEDIAN({R("PL_bprobe_after")}),"")', ""),
    ("pl_bad_event", "Rows with an event not in the list (should be 0)", f'=COUNTA({R("PL_event")})-SUMPRODUCT(COUNTIF({R("PL_event")},{R("L_event")}))', ""),
    ("pl_bad_side", "Rows with a side not in the list (should be 0)", f'=COUNTA({R("PL_side")})-SUMPRODUCT(COUNTIF({R("PL_side")},{R("L_side")}))', ""),
]
for i, (key, lab, f, cut) in enumerate(summ):
    r = 5 + i
    put(ws, f"{SM}{r}", lab, align=WRAP)
    put(ws, f"{SV}{r}", f, fmt=USD if "med" in key else INT, font=F_BOLD)
    put(ws, f"{SC}{r}", f"={R(cut)}" if cut else "", fmt=DATE)
    REF[key] = f"Pipeline!${SV}${r}"
r = 5 + len(summ)
put(ws, f"{SM}{r}", "Active offices, to date (signed less opted out)")
put(ws, f"{SV}{r}", f"={R('pl_signed_all')}-{R('pl_optout_office')}", fmt=INT, font=F_BOLD)
REF["pl_active_offices"] = f"Pipeline!${SV}${r}"
PL_SUM_END = r
widths(ws, {"A": 11, "B": 8, "C": 10, "D": 22, "E": 16, "F": 11, "G": 30, "H": 9, "I": 24})
widths(ws, {CL(k): 2 for k in range(len(PL_COLS) + 1, PLH0)})
widths(ws, {c_["first"]: 9, c_["g0b"]: 11, c_["g0b_first"]: 8, c_["op"]: 11, c_["op_first"]: 8, c_["g3"]: 11, c_["g3_first"]: 9,
            c_["probe_ok"]: 10, c_["oprobe"]: 10, c_["bprobe"]: 10, c_["bprobe_after"]: 10, c_["paid_full"]: 12, CL(PLS - 1): 2, SM: 46, SV: 11, SC: 12})
ws.freeze_panes = "A5"

# ==========================================================================
# Drop_Actuals
# ==========================================================================
ws = WS["Drop_Actuals"]
title(ws, "Actuals rolled up per drop", "Read-only. Sums Actuals_Campaigns, Actuals_DropCosts and the hours logs by drop_id. Ladder rungs stay in separate columns.")
banner(ws, "A3", "Actual figures, except the overhead allocations in column I, which are planning estimates (the same views as the plan). Incremental purchases are not measured; "
                 "the column says so. No column measures sales lift. A drop with no actual data shows no allocation and a blank contribution.", "T3")
DA = ["drop_id", "Drop date", "Actuals in", "Revenue", "Card processing", "Display kits", "Transport", "Other direct", "Overhead allocations (same views as plan; shown once the drop has actual data)",
      "Hard costs"] + [k + " (h)" for k in ACT_KEYS] + ["Founder hours", "Contribution", "Contribution per founder hour",
      "units_received", "units_delivered", "units_placed", "units_placed_within_1bd", "units_topped_up", "units_depleted_day5", "survey_responses",
      "survey_tried_yes", "qr_scans", "code_redemptions_day30", "incremental",
      "Brand campaigns", "Placed within 1 business day (share of delivered)", "Campaigns under the responses-per-office threshold",
      "Reports late or missing", "Brands that would buy again (yes)", "Renewed Y", "Renewed N",
      "Actual cash inside the six months (receipts less direct costs)"]
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
    # a drop with no actual data shows no allocation and a blank contribution (review R1-18c)
    has = f'OR(C{r}="Y",AF{r}>0,F{r}+G{r}+H{r}>0)'
    put(ws, f"I{r}", f"=IF({has},Drop_PnL!{EC['allocations']}{r},0)", fmt=USD)
    put(ws, f"J{r}", f"=SUM(E{r}:I{r})", fmt=USD, font=F_BOLD)
    for j in range(7):
        put(ws, f"{CL(11 + j)}{r}", f"=Hours_Log!{CL(HT0 + 1 + j)}{5 + i}", fmt=HRS)
    put(ws, f"R{r}", f"=SUM(K{r}:Q{r})", fmt=HRS, font=F_BOLD)
    put(ws, f"S{r}", f'=IF(AND(NOT({has}),R{r}=0),"",D{r}-J{r})', fmt=USD, font=F_BOLD)
    put(ws, f"T{r}", f'=IF(S{r}="","",IF(R{r}>0,S{r}/R{r},"n/a"))', fmt=PH, font=F_BOLD)
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
    w1, he = R("week1_start"), R("horizon_end")
    win = lambda rng: f'{rng},">="&{w1},{rng},"<="&{he}'
    put(ws, f"AM{r}", (f"=SUMIFS({R('AC_deposit_usd')},{R('AC_drop_id')},A{r},{win(R('AC_deposit_paid_date'))})"
                       f"+SUMIFS({R('AC_balance')},{R('AC_drop_id')},A{r},{win(R('AC_invoice_paid_date'))})"
                       f"-SUMIFS({R('AC_processing_fee_usd')},{R('AC_drop_id')},A{r},{win(R('AC_invoice_paid_date'))})"
                       + "".join(f"-SUMIFS({R(k)},{R('DC_drop_id')},A{r},{win(R('DC_drop_date'))})" for k in ("DC_kit_cost_usd", "DC_transport_cost_usd", "DC_other_direct_cost_usd"))),
        fmt=USD)
dar = lambda L: f"Drop_Actuals!${L}${DROP0}:${L}${DROPN}"
REF.update({"DA_ids": dar("A"), "DA_rev": dar("D"), "DA_cost": dar("J"), "DA_hours": dar("R"), "DA_contrib": dar("S"),
            "DA_delivered": dar("V"), "DA_placed1": dar("X"), "DA_share": dar("AG"), "DA_campaigns": dar("AF"), "DA_under": dar("AH"),
            "DA_late": dar("AI"), "DA_rebuy": dar("AJ"), "DA_cash": dar("AM")})
widths(ws, {CL(i + 1): 11 for i in range(len(DA))})
ws.freeze_panes = "B7"

# ==========================================================================
# Cash_Ledger (overhead payments)
# ==========================================================================
ws = WS["Cash_Ledger"]
title(ws, "Overhead payment schedule", "Monthly costs as they are paid. Cash_Flow reads only these rows for overhead; per-drop allocations never reach the cash flow, so nothing is counted twice.")
banner(ws, "A3", "Planning estimates, not a forecast. Every amount and start date follows Inputs section 5 (software, storage, insurance, phone).", "E3")
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
REF.update({"LG_line": f"Cash_Ledger!$A${LG0}:$A${LGN}", "LG_num": f"Cash_Ledger!$B${LG0}:$B${LGN}", "LG_date": f"Cash_Ledger!$C${LG0}:$C${LGN}",
            "LG_amt": f"Cash_Ledger!$D${LG0}:$D${LGN}"})
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
# optional bank reconciliation (review R1-18): type the actual balance at week end, read the variance
put(ws, "B30", "Actual bank balance at week end (optional; type it)", font=F_BOLD)
put(ws, "B31", "Variance: actual less the model balance with founder cash")
for i in range(N_WEEKS):
    L = CL(WK0 + i)
    as_input(put(ws, f"{L}30", None, fmt=USD))
    ws[f"{L}30"].number_format = USD
    put(ws, f"{L}31", f'=IF({L}30="","",{L}30-{L}29)', fmt=USD)
# summary
S0 = 33
section(ws, S0, "Lowest point and capital", last_col=TOT)
CFK = ["cf_low", "cf_low_week", "cf_low_date", "cf_need", "cf_reserve", "cf_commit", "cf_plan_cap", "cf_gap", "cf_founder", "cf_low_bal", "cf_end",
       "cf_bank_week", "cf_bank_var"]
CFR = {k: S0 + 1 + i for i, k in enumerate(CFK)}
c = lambda k: f"C{CFR[k]}"
cfsum = [
    ("cf_low", "Lowest cumulative net cash flow (before founder cash)", f"=MIN(C27:{WKL}27)", USD),
    ("cf_low_week", "Week of the lowest point", f"=INDEX(C4:{WKL}4,1,MATCH({c('cf_low')},C27:{WKL}27,0))", INT),
    ("cf_low_date", "That week starts", f"=INDEX(C5:{WKL}5,1,MATCH({c('cf_low')},C27:{WKL}27,0))", 'mmm d'),
    ("cf_need", "Peak cash need (the lowest point, as a positive number)", f"=-MIN(0,{c('cf_low')})", USD),
    ("cf_reserve", "Reserve held back (plan)", f"={R('reserve_usd')}", USD),
    ("cf_commit", "Capital to commit: peak need plus reserve", f"={c('cf_need')}+{c('cf_reserve')}", USD),
    ("cf_plan_cap", "Plan capital figure, high end (Capital tab)", "=Capital!D14", USD),
    ("cf_gap", "Gap: plan capital figure minus capital to commit (positive = headroom)", f"={c('cf_plan_cap')}-{c('cf_commit')}", USD),
    ("cf_founder", "Founder cash committed (Inputs)", f'=IF({R("founder_cash")}="","not set",{R("founder_cash")})', USD),
    ("cf_low_bal", "Lowest cash balance with founder cash", f"=MIN(C29:{WKL}29)", USD),
    ("cf_end", "Cumulative net cash at the end of week 26", f"={WKL}27", USD),
    ("cf_bank_week", "Latest week with an actual bank balance typed (row 30)", f'=IF(COUNT(C30:{WKL}30)=0,"",SUMPRODUCT(MAX((C30:{WKL}30<>"")*C4:{WKL}4)))', INT),
    ("cf_bank_var", "Variance that week (actual less model)", f'=IF({c("cf_bank_week")}="","",INDEX(C31:{WKL}31,1,{c("cf_bank_week")}))', USD),
]
assert [k for k, *_ in cfsum] == CFK
for key, lab, f, fmt in cfsum:
    rr = CFR[key]
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f, fmt=fmt, font=F_BOLD, fill=FILL_KEY if key in ("cf_low", "cf_commit", "cf_gap") else None)
    REF[key] = f"Cash_Flow!$C${rr}"
CF_SUM_END = CFR[CFK[-1]]
# monthly block
M0 = CF_SUM_END + 3
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
put(ws, f"B{mrow + 1}", "Check: monthly six-month net less weekly six-month net", font=F_BOLD)
put(ws, f"C{mrow + 1}", f"={MT}{MROW['net']}-{TOT}26", fmt=USD2, font=F_BOLD)
REF["cf_check_month_week"] = f"Cash_Flow!$C${mrow + 1}"
put(ws, f"B{mrow + 2}", "Overhead allocated to drops in the six months (a view, not paid)")
put(ws, f"C{mrow + 2}", f'=SUMIFS({dp("allocations")},{dp("date")},">="&{R("week1_start")},{dp("date")},"<="&{R("horizon_end")})', fmt=USD)
put(ws, f"B{mrow + 3}", "Overhead paid in the six months (Cash_Ledger)")
put(ws, f"C{mrow + 3}", f"=-{TOT}24", fmt=USD)
put(ws, f"B{mrow + 4}", "Overhead not absorbed by drops (paid less allocated)")
put(ws, f"C{mrow + 4}", f"=C{mrow + 3}-C{mrow + 2}", fmt=USD, font=F_BOLD)
# insurance expensed by cover month inside the window, so the all-in rate does not charge cover beyond it (review R1-11)
w1, he = R("week1_start"), R("horizon_end")
put(ws, f"B{mrow + 5}", "Insurance cover months starting inside the six months")
put(ws, f"C{mrow + 5}", f'=COUNTIFS({R("LG_line")},"insurance",{R("LG_num")},">0",{R("LG_date")},">="&{w1},{R("LG_date")},"<="&{he})', fmt=INT)
put(ws, f"B{mrow + 6}", "Insurance expensed in the six months (months x premium)")
put(ws, f"C{mrow + 6}", f"=C{mrow + 5}*{R('insurance_monthly')}", fmt=USD)
put(ws, f"B{mrow + 7}", "Insurance prepaid beyond the six months (paid less expensed)")
put(ws, f"C{mrow + 7}", f"=MAX(0,-{TOT}21-C{mrow + 6})", fmt=USD)
put(ws, f"B{mrow + 8}", "Overhead expensed in the six months (paid less prepaid)")
put(ws, f"C{mrow + 8}", f"=C{mrow + 3}-C{mrow + 7}", fmt=USD)
put(ws, f"B{mrow + 9}", "Overhead not absorbed by drops, expensed basis")
put(ws, f"C{mrow + 9}", f"=C{mrow + 8}-C{mrow + 2}", fmt=USD, font=F_BOLD)
CF_M_END = mrow + 9
REF["cf_alloc"] = f"Cash_Flow!$C${mrow + 2}"
REF["cf_over_paid"] = f"Cash_Flow!$C${mrow + 3}"
REF["cf_unabsorbed"] = f"Cash_Flow!$C${mrow + 4}"
REF["cf_prepaid_ins"] = f"Cash_Flow!$C${mrow + 7}"
REF["cf_over_exp"] = f"Cash_Flow!$C${mrow + 8}"
REF["cf_unabs_exp"] = f"Cash_Flow!$C${mrow + 9}"
REF.update({"cf_net_total": f"Cash_Flow!${TOT}$26", "cf_rec_plan_total": f"Cash_Flow!${TOT}$9", "cf_over_total": f"Cash_Flow!${TOT}$24",
            "cf_startup_total": f"Cash_Flow!${TOT}$25", "cf_kit_total": f"Cash_Flow!${TOT}$13", "cf_tr_total": f"Cash_Flow!${TOT}$14",
            "cf_proc_total": f"Cash_Flow!${TOT}$16", "cf_mail_total": f"Cash_Flow!${TOT}$15", "cf_direct_act_total": f"Cash_Flow!${TOT}$17",
            "cf_rec_act_total": f"Cash_Flow!${TOT}$10", "cf_rec_total": f"Cash_Flow!${TOT}$11", "cf_direct_total": f"Cash_Flow!${TOT}$18"})
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
ws.add_chart(ch, f"E{mrow + 1}")

# ==========================================================================
# Capital
# ==========================================================================
ws = WS["Capital"]
title(ws, "Capital to the first six months", "The plan's capital table reproduced line by line, and where the model pays each line. The cash flow never reads this tab, so nothing here is counted twice.")
banner(ws, "B3", "Planning estimates, not a forecast. Plan columns are typed from plan.md for comparison; model columns follow Inputs.", "J3")
header_row(ws, 4, 2, ["Item (plan capital table)", "Plan low", "Plan high", "Model working figure", "Where the model pays it", "Model cash inside the six months",
                      "Model less plan high", "Reading", "Legal pack status"], height=45)
lg = lambda line: f'SUMIFS({R("LG_amt")},{R("LG_line")},"{line}",{R("LG_date")},">="&{R("week1_start")},{R("LG_date")},"<="&{R("horizon_end")})'
caprows = [
    ("LLC filing and certificate of publication", 250, 250, f"={R('su_llc')}+{R('su_cert')}", "Startup outlays", f"={R('su_llc_cash')}+{R('su_cert_cash')}", "Reproduces.", "verified 2026-10-23 ($200 and $50, dos.ny.gov)"),
    ("Newspaper publication", 250, 2000, f"={R('su_pub')}", "Startup outlays", f"={R('su_pub_cash')}",
     "Plan high end until quoted; the plan gives no working figure. Legal pack working figures: $1,745 New York County, $345 Albany County.",
     "needs quote: legal pack range $200 to $2,000, working $1,745"),
    ("General liability insurance, one year", 500, 1500, f"={R('insurance_monthly')}*{R('months_per_year')}", "Overhead (Cash_Ledger, insurance)", "=" + lg("insurance"),
     "The plan's own working figure, about $100 a month, sits inside the range.", "plan estimate in the legal pack: $500 to $1,500, working $1,200; three quotes before binding, latest 2026-12-21"),
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
    ws.row_dimensions[rr].height = 48 if len(cr[6] or "") > 100 else 32
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
    ("Additional-insured endorsements (needs quote)", None, None, f"={R('su_addl_insured')}", "Startup outlays", f"={R('su_addl_insured_cash')}",
     "Legal pack: expect one per building that requires it; zero only if the carrier confirms its blanket endorsement covers buildings."),
    ("Mailing address, PO box or private mailbox (needs quote)", None, None, f"={R('su_mailbox')}", "Startup outlays", f"={R('su_mailbox_cash')}",
     "Legal pack: only if you will not use a home address in email footers and the LLC notice (CAN-SPAM)."),
    ("Registered agent, Albany County route only (needs quote)", None, None, f"={R('su_reg_agent')}", "Startup outlays (Include = N)", f"={R('su_reg_agent_cash')}",
     "Legal pack: optional in New York; only if the Articles name Albany County."),
    ("Trademark application, one class", 350, 850, f"={R('su_tm')}", "Startup outlays (at Gate 2)", f"={R('su_tm_cash')}",
     "Plan setup checklist and legal pack: after campaign zero, if it was a pass, inside the six months. The plan's capital table has no line for it. Include = N if the attorney advises against filing."),
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
CAP_END = re_ + 4
put(ws, f"B{re_ + 4}", "The plan's $3,360 to $6,510 is a budget to commit, not the model's cash need. The model's need is the lowest point of cumulative cash plus the reserve (Cash_Flow and Dashboard), because brand cash arrives before most drop costs.", align=WRAP)
ws.merge_cells(f"B{re_ + 4}:J{re_ + 4}")
ws.row_dimensions[re_ + 4].height = 45
widths(ws, {"A": 2, "B": 40, "C": 10, "D": 10, "E": 14, "F": 30, "G": 16, "H": 14, "I": 48, "J": 40})

# ==========================================================================
# Steady_State (with break-even)
# ==========================================================================
ws = WS["Steady_State"]
title(ws, "Monthly steady state and break-even", "Engine rows below compute one drop; the monthly view multiplies by drops per month and pays overhead once.")
banner(ws, "A3", "Planning estimates, not a forecast. Row 7, 'Plan reading (e), fixed for comparison', holds the plan's own figures and does not move with Inputs. "
                 "Every other row, the 'Active scenario' column and every break-even line follow Inputs.", "AM3")
write_engine_header(ws, 6, band_row=5)
SSR = {"plan": 7, "std": 8, "active": 9, "one": 10, "c1": 11, "c2": 12, "r1": 13, "r2": 14, "d1": 15, "d2": 16, "p1": 17, "p2": 18}
SS_LAST = max(SSR.values())
storage_glob = f'IF({R("storage_choice")}="unit",1,0)'
base_in = lambda **kw: dict({"date": None, "model": f"={R('ss_model')}", "tier": "standard", "offices": f"={R('ss_offices')}", "new_offices": 0,
                             "brands": f"={R('std_brands_drop')}", "renewals": 0, "fnd_renewals": 0, "price_std": f"={R('price_std_office')}",
                             "price_fnd": f"={R('price_fnd_office')}", "storage_on": "=" + storage_glob, "proc_on": f"={R('processing_on')}"}, **kw)
eng_cases = [
    ("plan", base_in(id="Plan reading (e), fixed for comparison: one three-brand courier drop at the plan's figures", model="courier", offices=10, brands=3,
                     storage_on=1, proc_on=1, price_std=150)),
    ("std", base_in(id="Standard drop on Inputs today: brands per drop, steady-state model and offices, all new brands")),
    ("active", base_in(id="Active scenario: one steady-state drop", brands=f"={R('sc_ss_brands')}",
                       renewals=f"={R('sc_renewal')}*{EC['brands']}{SSR['active']}", price_std=f"={R('sc_price_after')}")),
    ("one", base_in(id="Break-even: one-brand standard drop, new brand (steady-state model)", brands=1)),
    ("c1", base_in(id="Crossing: 1 new brand", brands=1)),
    ("c2", base_in(id="Crossing: 2 new brands", brands=2)),
    ("r1", base_in(id="Crossing at the active renewal rate, 1 brand", brands=1, renewals=f"={R('sc_renewal')}*{EC['brands']}{SSR['r1']}")),
    ("r2", base_in(id="Crossing at the active renewal rate, 2 brands", brands=2, renewals=f"={R('sc_renewal')}*{EC['brands']}{SSR['r2']}")),
    ("d1", base_in(id="Crossing: direct-ship, 1 new brand", model="direct-ship", brands=1)),
    ("d2", base_in(id="Crossing: direct-ship, 2 new brands", model="direct-ship", brands=2)),
    ("p1", base_in(id="Price crossing: standard drop at the first sensitivity price", price_std=f"={R('sens_price_start')}")),
    ("p2", base_in(id="Price crossing: standard drop at the first price plus one step", price_std=f"={R('sens_price_start')}+{R('sens_price_step')}")),
]
for key, ins in eng_cases:
    write_engine_row(ws, SSR[key], ins)
for k in ENGINE_INPUT_KEYS:
    ws[f"{EC[k]}{SSR['plan']}"].font = F_NOTE       # typed plan figures: grey italic, not inputs
E = lambda key, col: f"{EC[col]}{SSR[key]}"
REF["std_row"] = str(SSR["std"])
# monthly view
V0 = SS_LAST + 3
section(ws, V0, "Monthly steady state", last_col="F")
header_row(ws, V0 + 1, 2, ["Line", "Plan reading (e)", "Active scenario", "Unit", "How it is built"], height=30)
over_paid = f"({R('software_monthly')}+{R('insurance_monthly')}+{R('phone_monthly')}+{R('storage_monthly')}*{storage_glob})"
opb = R("sc_op_cost_blank")
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
    ("ss_op_rev", "Office-paid tier revenue (gross)", 0, f"={R('sc_op_offices')}*N({R('sc_op_fee')})", "USD per month", USD, "scenario B only"),
    ("ss_op_cost", "Office-paid tier cost to serve (needs quote)", 0, f"={R('sc_op_offices')}*N({R('sc_op_cost')})", "USD per month", USD, "blank until quoted"),
    ("ss_op_in", "Office-paid tier counted in the net?", "no office-paid tier",
     f'=IF(N({R("sc_op_offices")})=0,"no office-paid tier",IF({opb}=1,"no: cost to serve needs quote","yes"))', "", None,
     "left out until its cost to serve is quoted, so an unpriced cost never flatters the net"),
    ("ss_hire_h", "Drop-day hours handed to a hire", 0, f"=IF(D{{d}}>{R('sc_hire_threshold')},D{{d}}*{E('active', 'h_drop_day')},0)", "hours per month", HRS, "scenario A rule: hire above two drops a month"),
    ("ss_hire_cost", "Delivery hire cost", 0, f"=D{{hh}}*N({R('sc_hire_rate')})", "USD per month", USD, ""),
    ("ss_net", "Net monthly contribution after overhead, office tier and hire", "=C{contrib}-C{unabs}+C{oprev}-C{opcost}-C{hcost}",
     '=D{contrib}-D{unabs}+IF(D{opin}="yes",D{oprev}-D{opcost},0)-D{hcost}', "USD per month", USD, "office tier only when 'counted in the net' says yes"),
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
         "unabs": "ss_unabs", "oprev": "ss_op_rev", "opcost": "ss_op_cost", "opin": "ss_op_in", "hh": "ss_hire_h", "hcost": "ss_hire_cost", "net": "ss_net",
         "nh": "ss_net_hours", "wins": "ss_wins"}
fmtmap = {k: rows_mv[v] for k, v in names.items()}
for item in mv:
    key, lab, fc, fd, unit, fmt, how = item
    rr = rows_mv[key]
    put(ws, f"B{rr}", lab)
    for col, f in (("C", fc), ("D", fd)):
        if isinstance(f, str) and f.startswith("="):
            f = f.format(**fmtmap)
        put(ws, f"{col}{rr}", f, fmt=fmt, font=F_BOLD if key in ("ss_contrib", "ss_ph", "ss_net", "ss_net_ph") else None)
    put(ws, f"E{rr}", unit)
    put(ws, f"F{rr}", how, font=F_NOTE)
    REF[key + "_plan"] = f"Steady_State!$C${rr}"
    REF[key] = f"Steady_State!$D${rr}"
MV_END = V0 + 1 + len(mv)
# break-even
B0 = MV_END + 2
section(ws, B0, "Break-even (every line follows Inputs)", last_col="F")
header_row(ws, B0 + 1, 2, ["Measure", "Value", "", "Unit", "How it is built"], height=30)
cross_b = lambda a, b: (f'=IF(({EC["contribution"]}{SSR[b]}-{EC["contribution"]}{SSR[a]})-{R("g3_per_hour")}*({EC["hours"]}{SSR[b]}-{EC["hours"]}{SSR[a]})<=0,"never",'
                        f'MAX(0,1+({R("g3_per_hour")}*{EC["hours"]}{SSR[a]}-{EC["contribution"]}{SSR[a]})/(({EC["contribution"]}{SSR[b]}-{EC["contribution"]}{SSR[a]})-{R("g3_per_hour")}*({EC["hours"]}{SSR[b]}-{EC["hours"]}{SSR[a]}))))')
p1, p2 = SSR["p1"], SSR["p2"]
be = [
    ("be_startup", "Startup outlays to recover (one-time cash, Inputs section 11)", f"={R('su_total')}", "USD", USD, "sum of startup cash amounts"),
    ("be_c_one", "Contribution of a one-brand standard drop", f"={E('one', 'contribution')}", "USD per campaign", USD, f"engine row {SSR['one']}"),
    ("be_c_three", "Contribution per brand on a standard drop (price, brands per drop and delivery model on Inputs)",
     f'=IF({E("std", "brands")}>0,{E("std", "contribution")}/{E("std", "brands")},0)', "USD per campaign", USD,
     f"engine row {SSR['std']} / its brands; shared costs split equally"),
    ("be_n_one", "Campaigns to recover startup cash, one-brand drops", f'=IF(C{{c1}}>0,ROUNDUP(C{{s}}/C{{c1}},0),"never")', "campaigns", INT, "startup / contribution, rounded up"),
    ("be_n_three", "Brand campaigns on standard drops to recover startup cash (brands per drop on Inputs)", f'=IF(C{{c3}}>0,ROUNDUP(C{{s}}/C{{c3}},0),"never")', "brand campaigns", INT,
     "startup / contribution per brand, rounded up"),
    ("be_n_std_drops", "Standard drops to recover startup cash (brands per drop on Inputs)",
     f'=IF({E("std", "contribution")}>0,ROUNDUP(C{{s}}/{E("std", "contribution")},0),"never")', "drops", INT,
     f"startup / contribution of the whole standard drop (engine row {SSR['std']}), rounded up"),
    ("be_c_pre", "One-brand standard drop: contribution before overhead allocations", f"={E('one', 'contribution')}+{E('one', 'allocations')}", "USD per campaign", USD, "revenue less direct costs"),
    ("be_over", "Overhead paid per month", f"={R('ss_over_paid')}", "USD per month", USD, "Monthly steady state"),
    ("be_n_over", "Standard campaigns a month to cover overhead", f'=IF(C{{cp}}>0,ROUNDUP(C{{ov}}/C{{cp}},0),"never")', "campaigns per month", INT, "overhead / contribution before allocations, rounded up"),
    ("be_b_new", "Brands per drop where contribution per hour reaches the Gate 3 target, new brands", cross_b("c1", "c2"), "brands per drop", '0.00',
     f"linear in brands: solved from engine rows {SSR['c1']} and {SSR['c2']}"),
    ("be_b_new_int", "Smallest whole number of brands that clears it", f'=IF(ISNUMBER(C{{bn}}),ROUNDUP(C{{bn}},0),"never")', "brands per drop", INT, ""),
    ("be_b_ren", "Same, at the active renewal rate", cross_b("r1", "r2"), "brands per drop", '0.00', f"engine rows {SSR['r1']} and {SSR['r2']}"),
    ("be_b_dir", "Same, brands ship direct", cross_b("d1", "d2"), "brands per drop", '0.00', f"engine rows {SSR['d1']} and {SSR['d2']}"),
    ("be_price", "Standard price per office where a standard drop reaches the target (brands per drop on Inputs)",
     f'=IF({EC["revenue"]}{p2}={EC["revenue"]}{p1},"never",{EC["price_std"]}{p1}+({R("g3_per_hour")}*{EC["hours"]}{p1}-{EC["contribution"]}{p1})*({EC["price_std"]}{p2}-{EC["price_std"]}{p1})/({EC["contribution"]}{p2}-{EC["contribution"]}{p1}))',
     "USD per office", USD2, f"linear in price: engine rows {p1} and {p2}"),
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
BE_END = B0 + 1 + len(be)
engine_widths(ws)
widths(ws, {"B": 50, "C": 16, "D": 16, "E": 16, "F": 48})
ws.column_dimensions["A"].width = 44
ws.freeze_panes = "B7"

# ==========================================================================
# Sensitivity
# ==========================================================================
ws = WS["Sensitivity"]
title(ws, "Sensitivity tables", "Plain formulas, no data tables. Reference drop: standard tier, steady-state delivery model and offices, storage and processing as set on Inputs.")
banner(ws, "A3", "Planning estimates, not a forecast. Each cell recomputes contribution per founder hour from the inputs. Axis starts and steps are on Inputs section 10. A check cell compares the shortcut with the full engine.", "L3")
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
banner(ws, "A3", "Planning estimates, not a forecast. Reproduction holds while inputs equal the plan defaults (Inputs 'Changed' column). If you change an input, a 'differs' here is expected and is not an error.", "AM3")
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
ok_cf(ws, f"{PCC['Status']}7:{PCC['Status']}{7 + len(PC) - 1}", good='"matches"')
# an expected difference (the processing contrast row) is amber, not red and not blank (review R1-18a)
ws.conditional_formatting.add(f"{PCC['Status']}7:{PCC['Status']}{7 + len(PC) - 1}",
                              CellIsRule(operator="equal", formula=['"differs, as expected"'], fill=PatternFill("solid", fgColor="FFEB9C"), font=Font(color="7A5A00")))
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
banner(ws, "A3", "Planning estimates, not a forecast. To test a price: type it in 'Standard price per office' below (or on Inputs to move the whole model). Read 'Contribution per founder hour'.", "F3")
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
# Dashboard ranges are added after the Dashboard is laid out (its gate rows start below the headline); see DASH_ERR below.
err_rngs = [f"Drop_PnL!A{DROP0}:{CT['next_date']}{DROPN + 1}", f"Plan_Check!A7:{LAST_ENGINE_COL}{7 + len(PC) - 1}", f"Steady_State!A7:{LAST_ENGINE_COL}{SS_LAST}",
            f"Steady_State!B{V0 + 2}:D{BE_END}", f"Cash_Flow!C5:{TOT}{CF_SUM_END}", f"Cash_Flow!C{M0}:{MT}{CF_M_END}", f"Sensitivity!B6:G{T4_END}", f"Sensitivity!A{SXE}:{LAST_ENGINE_COL}{SXE}",
            f"Calculator!A{ER}:{LAST_ENGINE_COL}{ER}", f"Drop_Actuals!A{DROP0}:AM{DROPN}", f"Schedule!A{DROP0}:AJ{DROPN}", f"Inputs!A5:R{sun + 4}", "Scenarios!C10:R21",
            f"Capital!B5:J{CAP_END}", f"Hours_Log!{CL(HT0)}5:{CL(HT0 + 10)}{HL_END}", f"Pipeline!{CL(PLS)}5:{CL(PLS + 2)}{PL_SUM_END}",
            "DASH_HEAD", "DASH_BODY"]
n_err = "+".join(f"SUMPRODUCT(ISERROR({r_})*1)" for r_ in err_rngs)   # DASH_HEAD / DASH_BODY replaced after the Dashboard is built
sched_bad = f'COUNTIF({R("sched_check")},"check")+COUNTIF({R("sched_check")},"date missing")'
nf = f"SUMPRODUCT((Drop_PnL!{EC['tier']}{DROP0}:{EC['tier']}{DROPN}=\"founding\")*Drop_PnL!{EC['new_fnd']}{DROP0}:{EC['new_fnd']}{DROPN})"
fr = f"SUM(Drop_PnL!{EC['fnd_renewals']}{DROP0}:{EC['fnd_renewals']}{DROPN})"
dates_asc = "+".join(f'IF(AND(Schedule!E{r_ + 1}<>"",Schedule!E{r_}<>""),IF(Schedule!E{r_ + 1}<Schedule!E{r_},1,0),0)' for r_ in range(DROP0, DROPN))
pr1 = f"Plan_Check!{{c}}{PCR['E1']}"
# week 1 moved while every gate date and campaign zero's date still sit on their CONTRACTS defaults (review R3-09)
jd = lambda k: R(k).replace("$C$", "$J$")
wk1_alone = (f'=IF(AND({R("week1_start")}&""<>{jd("week1_start")}&""'
             + "".join(f',{R(k)}&""={jd(k)}&""' for k in ("gate0_date", "gate1_date", "gate3_date", "decision_date"))
             + f',Schedule!$E${DROP0}&""=Schedule!${CL(DEF0)}${DROP0}&""),1,0)')
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
    ("Integrity", "Break-even per-brand contribution follows Inputs: engine row equals the shortcut at today's price and brands per drop",
     f"={R('be_c_three')}-IF({R('std_brands_drop')}>0,({R('std_brands_drop')}*({R('price_std_office')}*{R('sx_pk')}+{R('sx_extra')})*{R('sx_net')}"
     f"-{R('sx_fixed')}-{R('sx_card')}*MAX({R('std_brands_drop')}-1,0))/{R('std_brands_drop')},0)", "=IF(ABS(D{r})<=$D$3,1,0)",
     "Review R1-03: the break-even lines no longer read the fixed plan row."),
    ("Integrity", "Per-drop cash inside the six months adds up to the cash flow's receipts and direct costs",
     f"=SUM({dp('cash_live')})-({R('cf_rec_total')}+{R('cf_direct_total')})", "=IF(ABS(D{r})<=$D$3,1,0)",
     "Feeds the Dashboard's week-26 cash with and without the decision-window drops."),
    ("Schedule", "Rows failing the schedule rules (Tue/Wed, blackouts, counts)", "=" + sched_bad, "=IF(D{r}=0,1,0)", "See Schedule, Row check."),
    # information only (review R3-03): a drop the founder adds takes the next spare row, so rows may sit out of date order; the model reads dates
    ("Info", "Drop rows out of date order (information only; not counted)", "=" + dates_asc, "info",
     "Fine: an added drop takes the next spare drop_id, and every total, the cash flow and the Dashboard's next drop read dates, not row order. The Dashboard's drop table lists rows in Schedule order."),
    ("Schedule", "Week 1 moved but no gate date and not campaign zero's date moved with it", wk1_alone, "=IF(D{r}=0,1,0)",
     "The gate dates on Inputs and the drop dates on Schedule are typed CONTRACTS dates. Move them with week 1, or the gate labels ('end of week 3') no longer hold."),
    ("Schedule", "New founding brands beyond the founding cap", f"=MAX(0,{nf}-{R('founding_cap')})", "=IF(D{r}=0,1,0)", "Founding tier: first three brands only."),
    ("Schedule", "Founding-rate renewals beyond the two-campaign lock", f"=MAX(0,{fr}-{R('founding_lock')}*{nf})", "=IF(D{r}=0,1,0)", ""),
    ("Schedule", "Gate 2 drop exists on Schedule", f'=IF(ISNUMBER(MATCH({R("g2_drop_id")},{R("sched_ids")},0)),0,1)', "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: invalid activity keys", f"={R('HL_invalid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: drop_ids not on Schedule", f"={R('HL_badid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Toggl_Import: rows with zero hours or a bad activity", f"={R('TG_zero')}+{R('TG_invalid')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Pipeline: rows with a bad event or side", f"={R('pl_bad_event')}+{R('pl_bad_side')}", "=IF(D{r}=0,1,0)", ""),
    ("Data", "Actuals_Campaigns: rows whose drop_id is not on Schedule", f'=COUNTIF({R("AC_flag")},"not in schedule")', "=IF(D{r}=0,1,0)", ""),
    ("Data", "Actuals_DropCosts: rows whose drop_id is not on Schedule", f'=COUNTIF({R("DC_flag")},"not in schedule")', "=IF(D{r}=0,1,0)", ""),
    ("Data", "Actuals_Campaigns: header row differs from HANDOFF, or something is pasted in the blank buffer columns", "=" + R("AC_hdr_bad"), "=IF(D{r}=0,1,0)",
     "Paste exactly the HANDOFF columns in order; extra fields go in a separate file."),
    ("Data", "Actuals_DropCosts: header row differs from HANDOFF, or something is pasted in the blank buffer columns", "=" + R("DC_hdr_bad"), "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: header row differs from HANDOFF, or something is pasted in the blank buffer columns", "=" + R("HL_hdr_bad"), "=IF(D{r}=0,1,0)", ""),
    ("Data", "Pipeline: header row differs from HANDOFF, or something is pasted in the blank buffer columns", "=" + R("PL_hdr_bad"), "=IF(D{r}=0,1,0)", ""),
    # a date or amount stored as text drops out of every SUMIFS with no error (review R3-01)
    ("Data", "Actuals_Campaigns: dates or numbers stored as text (columns C, G to U, X to Z)", "=" + R("AC_text_bad"), "=IF(D{r}=0,1,0)",
     "Text drops out of the cash flow and the gates with no error. Fix: README tab, 'Dates and amounts must be real dates and numbers'."),
    ("Data", "Actuals_DropCosts: dates or numbers stored as text (columns B, D to H)", "=" + R("DC_text_bad"), "=IF(D{r}=0,1,0)", ""),
    ("Data", "Hours_Log: dates or hours stored as text (columns A and E)", "=" + R("HL_text_bad"), "=IF(D{r}=0,1,0)", ""),
    ("Data", "Pipeline: dates or value_number stored as text (columns A and F)", "=" + R("PL_text_bad"), "=IF(D{r}=0,1,0)", ""),
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
    put(ws, f"E{rr}", pas.format(r=rr), fmt=INT, font=F_BOLD, align=Alignment(horizontal="center", vertical="top") if pas == "info" else None)
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
put(ws, f"C{rr + 3}", "Checks in total (the information row is not a check)", font=F_BOLD)
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
# the banner names data failures too, so text dates or a bad paste never sit behind a green banner (review R3-01)
put(ws, "G5", (f'=IF({R("ck_integrity")}>0,{R("ck_integrity")}&" integrity check(s) failing: see Checks",'
               f'IF({R("ck_data")}>0,{R("ck_data")}&" data check(s) failing: pasted rows are ignored or misread (see Checks)","all integrity and data checks pass"))'),
    font=F_BOLD, align=Alignment(wrap_text=True, vertical="top"))
ws.merge_cells("G5:J5")
ok_cf(ws, "G5", good='"all integrity and data checks pass"')
ws.conditional_formatting.add("G5", FormulaRule(formula=['AND(G5<>"",G5<>"all integrity and data checks pass")'], fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006", bold=True)))
ws.row_dimensions[5].height = 30
# --- gate rows first, so the headline can point at them
N_HEAD = 21
CR0 = 9 + N_HEAD + 1          # cash at each stop point (review R2-08)
CR_ROWS = [("Gate 0", "gate0_date"), ("Gate 1", "gate1_date"), ("Gate 2", "gate2_date"), ("Gate 3", "gate3_date"), ("Six-month decision", "decision_date")]
G0R = CR0 + 2 + len(CR_ROWS) + 2
st_ge = lambda r_: f'=IF(F{r_}="",IF({R("as_of")}>C{r_},"miss","not yet"),IF(F{r_}>=D{r_},"pass",IF({R("as_of")}>C{r_},"miss","not yet")))'
st_le = lambda r_: f'=IF(F{r_}="",IF({R("as_of")}>C{r_},"miss","not yet"),IF(F{r_}<=D{r_},"pass",IF({R("as_of")}>C{r_},"miss","not yet")))'
g2 = lambda rng: f'IFERROR(INDEX({rng},MATCH({R("g2_drop_id")},{R("DA_ids")},0)),"")'
std_plan_c = f'SUMIFS({dp("contribution")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")})'
std_plan_h = f'SUMIFS({dp("hours")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")})'
std_act_c = f'SUMIFS({R("DA_contrib")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("actuals_in")},"Y")'
std_act_h = f'SUMIFS({R("DA_hours")},{dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("actuals_in")},"Y")'
# coverage of the Gate 3 rate: standard runs that run and are dated by the review date, and how many of them have actuals in (review R2-02)
std_runs_m = f'COUNTIFS({dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("run")},1)'
std_runs_n = f'COUNTIFS({dp("tier")},"standard",{dp("date")},"<="&{R("gate3_date")},{dp("run")},1,{dp("actuals_in")},"Y")'
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
     f'=IF({std_act_h}>0,{std_act_c}/{std_act_h},"")', "ge", PH,
     "Not yet until every standard run dated by the review date has actuals in (next row)."),
    ("Gate 3", "gate3_date", "Standard runs dated by the review date with actuals in (the rate above uses only these; threshold = all of them)", "=" + std_runs_m, "",
     "=" + std_runs_n, "cov", INT, "Set Actuals in = Y by T+10; code_redemptions_day30 can follow later (HANDOFF 2.4)."),
]
G3PH = G0R + 2 + len(gates) - 2
G3COV = G3PH + 1
# --- headline
section(ws, 7, "Headline", last_col="I")
header_row(ws, 8, 2, ["Measure", "Value", "Detail"], height=22)
nxt = f'MATCH(MIN({dp("next_date")}),{dp("next_date")},0)'
# hours no drop owns: the plan's discovery hours until the log holds more hours not tied to a drop, then the log (review R2-03)
disc_plan = f'{R("discovery_hours_week")}*{R("discovery_weeks")}'
disc_h = f'MAX({disc_plan},{R("HL_unlinked_6m")})'
disc_txt = (f'IF({R("HL_unlinked_6m")}>{disc_plan},TEXT({R("HL_unlinked_6m")},"0")&" logged hours not tied to a drop",'
            f'TEXT({disc_plan},"0")&" planned discovery hours")')
g3d, hz, w1 = R("gate3_date"), R("horizon_end"), R("week1_start")
live_c = lambda d: f'SUMIFS({dp("live_contrib")},{dp("date")},"<="&{d})'
live_h = lambda d: f'SUMIFS({dp("live_hours")},{dp("date")},"<="&{d})'
alloc = lambda d: f'SUMIFS({dp("allocations")},{dp("date")},">="&{w1},{dp("date")},"<="&{d})'
allin_num = lambda d: f'({live_c(d)}+{alloc(d)}-{R("cf_over_exp")})'
allin_den = lambda d: f'({live_h(d)}+{disc_h})'
allin = lambda d: f'=IF({allin_den(d)}>0,{allin_num(d)}/{allin_den(d)},"n/a")'
allin_su = lambda d: f'IF({allin_den(d)}>0,TEXT(({allin_num(d)}-{R("su_total")})/{allin_den(d)},"$#,##0.0"),"n/a")'
dw_cash = f'SUMIFS({dp("cash_live")},{dp("date")},">"&{g3d})'
dw_drops = f'COUNTIFS({dp("date")},">"&{g3d},{dp("date")},"<="&{hz},{dp("run")},1)'
sr_ = SSR["std"]
std = lambda k: f"Steady_State!${EC[k]}${sr_}"
add_off = f'SUMIFS({R("sched_add_offices")},{R("sched_tiers")},"standard",{R("sched_dates")},"<="&{g3d})'
add_h = f'({add_off})*({R("h_new_office")}-{R("h_existing_office")})'
opb = R("sc_op_cost_blank")
head = [
    ("next", "Next scheduled drop", f'=IFERROR(INDEX({dp("id")},{nxt}),"none scheduled")',
     f'=IFERROR(TEXT(INDEX({dp("date")},{nxt}),"ddd yyyy-mm-dd")&", "&INDEX({dp("model")},{nxt})&", "&INDEX({dp("brands")},{nxt})&" brand(s), "&INDEX({dp("offices")},{nxt})&" offices, "&INDEX({dp("tier")},{nxt})&" tier","")', None),
    ("next_ph", "Its contribution per founder hour (plan)", f'=IFERROR(INDEX({dp("per_hour")},{nxt}),"n/a")',
     f'=IFERROR("revenue "&TEXT(INDEX({dp("revenue")},{nxt}),"$#,##0")&", "&TEXT(INDEX({dp("hours")},{nxt}),"0")&" founder hours; campaign zero is at the founding rate, so the standard price does not move it","")', PH),
    ("price", "Price in force: standard price per office (Inputs, section 3)", f"={R('price_std_office')}",
     f'="standard package "&TEXT({R("std_pkg_price")},"$#,##0")&" for "&{R("std_pkg_offices")}&" offices; founding "&TEXT({R("price_fnd_office")},"$#,##0")&" per office. Change the price on Inputs and read the next row."', USD),
    ("std_ph", "A standard drop at that price: contribution per founder hour", f"={std('per_hour')}",
     f'={std("brands")}&" new brands, "&{std("offices")}&" offices, "&{std("model")}&": revenue "&TEXT({std("revenue")},"$#,##0")&", contribution "&TEXT({std("contribution")},"$#,##0")&", "&TEXT({std("hours")},"0")&" founder hours"', PH),
    ("g3_rate", "Standard runs to Gate 3: contribution per founder hour, plan", f'=IF(E{G3PH}="","n/a",E{G3PH})',
     f'="actual: "&IF(F{G3PH}="","not yet",TEXT(F{G3PH},"$#,##0.0"))&" ("&F{G3COV}&" of "&D{G3COV}&" standard runs with actuals in); target "&TEXT({R("g3_per_hour")},"$#,##0")', PH),
    ("g3_roster", "Same, if the roster grows so no office gets two drops within four weeks", f'=IF({std_plan_h}+{add_h}>0,{std_plan_c}/({std_plan_h}+{add_h}),"n/a")',
     f'="adds "&TEXT({add_off},"0")&" new offices and "&TEXT({add_h},"0")&" founder hours to the standard runs; the plan wants one drop per office a month (a roster of about 20)"', PH),
    ("low", "Lowest point of cumulative cash (before founder cash)", f"={R('cf_low')}",
     f'="in week "&{R("cf_low_week")}&", starting "&TEXT({R("cf_low_date")},"ddd yyyy-mm-dd")', USD),
    # unpriced lines count as $0 here; say how many (review R3-06)
    ("commit", "Capital to commit: lowest point plus the reserve", f"={R('cf_commit')}",
     f'="reserve "&TEXT({R("reserve_usd")},"$#,##0")&" (plan)"&IF({R("unpriced_count")}>0,"; counts "&{R("unpriced_count")}&" unpriced cost line(s) as $0 until quoted (Inputs, status needs quote or needs founder decision)","")', USD),
    ("cap_high", "Plan capital figure (high end of the plan's table)", f"={R('cap_high')}", f'="low end "&TEXT({R("cap_low")},"$#,##0")', USD),
    ("gap", "Gap to the plan capital figure (positive = headroom)", f"={R('cf_gap')}",
     '=IF(C{self}>=0,"the plan figure covers the model need","the model needs more than the plan figure")', USD),
    ("founder", "Founder cash committed", f"={R('cf_founder')}",
     f'=IF({R("founder_cash")}="","set it on Inputs (plan question 7)",IF({R("founder_cash")}>={R("cf_commit")},"covers capital to commit","short of capital to commit by "&TEXT({R("cf_commit")}-{R("founder_cash")},"$#,##0")))', USD),
    ("unabs", "Overhead paid but not absorbed by drops, six months (cash)", f"={R('cf_unabsorbed')}",
     f'="paid "&TEXT({R("cf_over_paid")},"$#,##0")&", allocated to drops "&TEXT({R("cf_alloc")},"$#,##0")&"; of that gap, "&TEXT({R("cf_prepaid_ins")},"$#,##0")&" is insurance prepaid beyond the six months and the rest is ramp-up months with few drops"', USD),
    ("allin_road", "Six months all-in per founder hour: roadmap drops only (to Gate 3)", allin(g3d),
     f'="campaign zero and the standard runs, with all six months of overhead (expensed basis) and "&{disc_txt}&"; after one-time startup outlays: "&{allin_su(g3d)}&" per hour"', PH),
    ("allin_all", "Six months all-in per founder hour: with the decision-window drops (derived, not in the plan's roadmap)", allin(hz),
     f'="adds "&{dw_drops}&" drop(s) after Gate 3, with "&{disc_txt}&"; insurance prepaid beyond the window ("&TEXT({R("cf_prepaid_ins")},"$#,##0")&") is left out; after one-time startup outlays: "&{allin_su(hz)}&" per hour"', PH),
    ("cash_road", "Cumulative cash at week 26: roadmap drops only", f"={R('cf_end')}-{dw_cash}",
     '="the decision-window drops add "&TEXT(C{next_row}-C{self},"$#,##0")&" by week 26"', USD),
    ("cash_all", "Cumulative cash at week 26: with the decision-window drops (derived)", f"={R('cf_end')}",
     f'="before founder cash; lowest balance with founder cash "&IF({R("founder_cash")}="","(founder cash not set)",TEXT({R("cf_low_bal")},"$#,##0"))', USD),
    ("ss", "Steady state, scenario in force: contribution per month", f"={R('ss_contrib')}",
     f'="per founder hour "&IF(ISNUMBER({R("ss_ph")}),TEXT({R("ss_ph")},"$#,##0.0"),"n/a")&"; net of all overhead "&TEXT({R("ss_net")},"$#,##0")&" a month"'
     f'&IF(AND(N({R("sc_op_offices")})>0,{opb}=1),"; office-paid revenue left out of the net until its cost to serve is quoted","")', USD),
    ("fatigue", "Office-fatigue warnings on Schedule", f'=COUNTIF({R("sched_fatigue")},"some*")',
     '=IF(C{self}=0,"no office gets two drops within four weeks","drops where some offices get a second drop within four weeks (plan: one drop a month); see the Gate 3 rate with a bigger roster above")', INT),
    ("after_dec", "Decision-window drops whose debrief (T+10) lands after the decision date", f'=COUNTIF({R("sched_after")},"after the decision")',
     f'=IF(C{{self}}=0,"every decision-window drop reports by the decision date","last debrief "&TEXT(MAX({R("sched_after_date")}),"ddd yyyy-mm-dd")&", after the "&TEXT({R("decision_date")},"ddd yyyy-mm-dd")&" decision: the switch test cannot finish in time (REPORT.md, question 1)")', INT),
    ("sched_changed", "Schedule rows changed or added since the derived default", f'=COUNTIF({R("sched_changed")},"changed")',
     '=IF(C{self}=0,"schedule is the derived default","edited by you")', INT),
    ("inputs_changed", "Inputs changed from plan defaults", f"={R('changed_count')}",
     f'=IF({R("ck_plan")}=0,"plan figures reproduce","plan reproduction differs in "&{R("ck_plan")}&" check(s); expected after edits")', INT),
]
assert len(head) == N_HEAD
for i, (key, lab, v, det, fmt) in enumerate(head):
    rr = 9 + i
    put(ws, f"B{rr}", lab, align=WRAP)
    put(ws, f"C{rr}", v, fmt=fmt, font=F_BOLD, fill=FILL_KEY)
    put(ws, f"D{rr}", det.replace("{self}", str(rr)).replace("{next_row}", str(rr + 1)), align=WRAP)
    ws.merge_cells(f"D{rr}:I{rr}")
    ws.row_dimensions[rr].height = 30
    REF["dash_" + key] = f"Dashboard!$C${rr}"
# --- cash at each stop point (review R2-08): the gates are stop points, so show what is spent if you stop at each one
section(ws, CR0, "Cash at each stop point (before founder cash)", last_col="I")
header_row(ws, CR0 + 1, 2, ["Review", "Date", "Paid out before the review day (gross; no brand money)", "Brand cash received by the review day",
                            "Refunds owed if you stop: payments received for drops not yet run", "Net if you stop here: paid out + received - refunds",
                            "Cumulative net cash at the end of that week, if every gate passes"], height=70)
_out_keys = ["kit", "transport", "kit_mail", "proc", "direct_act", "software", "insurance", "storage", "phone", "startup"]
for i, (lab, dkey) in enumerate(CR_ROWS):
    rr = CR0 + 2 + i
    gd = R(dkey)
    before = cash_lines(R("week1_start"), f"({gd}-1)")
    by_day = cash_lines(R("week1_start"), gd)
    # refunds owed on paid campaigns whose drop has not run by the review day (review R3-05): plan payments of drops without actuals,
    # plus actual deposits and balances of campaigns with actuals in, received by that day for a drop dated after it
    refund = ("+".join(f'SUMIFS({dp(a)},{dp(d)},"<="&{gd},{dp("date")},">"&{gd},{dp("actuals_in")},"N")' for a, d in
                       (("pay_fnd_amt", "pay_fnd_date"), ("pay_dep_amt", "pay_dep_date"), ("pay_bal_amt", "pay_bal_date")))
              + f'+SUMIFS({R("AC_deposit_usd")},{R("AC_deposit_paid_date")},"<="&{gd},{R("AC_drop_date")},">"&{gd},{R("AC_flag")},"Y")'
              + f'+SUMIFS({R("AC_balance")},{R("AC_invoice_paid_date")},"<="&{gd},{R("AC_drop_date")},">"&{gd},{R("AC_flag")},"Y")')
    put(ws, f"B{rr}", lab, font=F_BOLD)
    put(ws, f"C{rr}", f"={gd}", fmt=DATE)
    put(ws, f"D{rr}", "=" + "".join(before[k] for k in _out_keys), fmt=USD)
    put(ws, f"E{rr}", f"={by_day['rec_plan']}+{by_day['rec_act']}", fmt=USD)
    put(ws, f"F{rr}", "=" + refund, fmt=USD)
    put(ws, f"G{rr}", f"=D{rr}+E{rr}-F{rr}", fmt=USD, font=F_BOLD, fill=FILL_KEY)
    put(ws, f"H{rr}", f'=SUMIFS(Cash_Flow!$C$26:${WKL}$26,Cash_Flow!$C$5:${WKL}$5,"<="&{gd})', fmt=USD)
    ws.row_dimensions[rr].height = 18
    REF["dash_cr_out_" + dkey] = f"Dashboard!$D${rr}"
    REF["dash_cr_rec_" + dkey] = f"Dashboard!$E${rr}"
    REF["dash_cr_ref_" + dkey] = f"Dashboard!$F${rr}"
    REF["dash_cr_net_" + dkey] = f"Dashboard!$G${rr}"
    REF["dash_cr_cum_" + dkey] = f"Dashboard!$H${rr}"
CR_END = CR0 + 2 + len(CR_ROWS) - 1
put(ws, f"B{CR_END + 1}", "Paid out counts every outflow dated before the review day (startup outlays, overhead, drop costs, card fees) and no brand money: at Gate 1 it is what you are out "
                          "if no brand pays. Spending the plan makes on the review day itself is left out, because you make it only if the gate passes (at Gate 1: insurance, the licence "
                          "and printing; at Gate 2: the trademark). Net if you stop here adds the brand cash received by that day and takes off what you would refund: payments for "
                          "campaigns whose drop has not run yet (founding payments, deposits). Card fees on refunded payments are not recovered. Founding brands pay on Gate 1 day by default.",
    align=WRAP, font=F_NOTE)
ws.merge_cells(f"B{CR_END + 1}:I{CR_END + 1}")
ws.row_dimensions[CR_END + 1].height = 58
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
    put(ws, f"D{rr}", (thr if thr.startswith("=") else f"={R(thr)}") if thr else 0, fmt=fmt)
    put(ws, f"E{rr}", model_v if model_v else "", fmt=fmt)
    put(ws, f"F{rr}", live, fmt=fmt, font=F_BOLD)
    if kind == "info":
        stat = "info"
    elif kind == "cov":
        stat = f'=IF(D{rr}=0,"",IF(F{rr}>=D{rr},"complete",(D{rr}-F{rr})&" without actuals"))'
    elif rr == G3PH:
        # the Gate 3 rate cannot pass on part of the evidence (review R2-02)
        stat = (f'=IF(AND(D{G3COV}>0,F{G3COV}<D{G3COV}),"not yet: "&(D{G3COV}-F{G3COV})&" standard run(s) without actuals",' + st_ge(rr)[1:] + ")")
    else:
        stat = st_ge(rr) if kind == "ge" else st_le(rr)
    put(ws, f"G{rr}", stat, font=F_BOLD, align=Alignment(horizontal="center", wrap_text=True))
    put(ws, f"H{rr}", fail, align=WRAP, font=F_NOTE)
    ws.merge_cells(f"H{rr}:K{rr}")
    ws.row_dimensions[rr].height = 48 if rr in (G3PH, G3COV) else 30
    GR.setdefault(g, []).append((rr, kind))
GEND = G3COV
status_cf(ws, f"G{G0R + 2}:G{GEND}")
ws.conditional_formatting.add(f"G{G0R + 2}:G{GEND}", FormulaRule(formula=[f'LEFT(G{G0R + 2},LEN("not yet"))="not yet"'], fill=PatternFill("solid", fgColor="EDEDED"), font=Font(color="555555")))
ok_cf(ws, f"G{G0R + 2}:G{GEND}", good='"complete"')
ws.conditional_formatting.add(f"G{G3COV}", FormulaRule(formula=[f'AND(G{G3COV}<>"",G{G3COV}<>"complete")'], fill=PatternFill("solid", fgColor="FCE4D6")))
REF["dash_gate_rows"] = f"Dashboard!$A${G0R + 2}:$G${GEND}"
GS = GEND + 2
header_row(ws, GS, 1, ["Gate", "Review date", "Overall"], height=22)
for i, g in enumerate(["Gate 0", "Gate 1", "Gate 2", "Gate 3"]):
    rr = GS + 1 + i
    rows_ = [r_ for r_, k in GR[g] if k not in ("info", "cov")]
    miss = "+".join(f'IF(G{r_}="miss",1,0)' for r_ in rows_)
    notyet = "+".join(f'IF(LEFT(G{r_},LEN("not yet"))="not yet",1,0)' for r_ in rows_)
    put(ws, f"A{rr}", g, font=F_BOLD)
    put(ws, f"B{rr}", f"=C{GR[g][0][0]}", fmt=DATE)
    put(ws, f"C{rr}", f'=IF({miss}>0,"miss",IF({notyet}>0,"not yet","pass"))', font=F_BOLD)
    REF["gate_" + g[-1]] = f"Dashboard!$C${rr}"
status_cf(ws, f"C{GS + 1}:C{GS + 4}")
REF["dash_gate_overall"] = f"Dashboard!$A${GS + 1}:$C${GS + 4}"
# --- decision rule
DR0 = GS + 6
section(ws, DR0, "Decision rule (plan): scale, switch to office-paid, or stop", last_col="I")
# the plan's test is the share of brands that renew, so each brand counts once (review R3-07): brands with a Y / brands with a Y or N answer
renew_live = f'IF(SUM({R("AC_brand_answered")})=0,"",SUM({R("AC_brand_renewed")})/SUM({R("AC_brand_answered")}))'
drows = [
    ("Brand renewal rate, each brand once (renewed Y / answered Y or N)", "=" + renew_live, PCT),
    ("Offices that named $100 a month or more", f"={R('pl_op_offices')}", INT),
    ("Drops after Gate 3 with actuals in", f'=COUNTIFS({dp("date")},">"&{R("gate3_date")},{dp("actuals_in")},"Y",{dp("run")},1)', INT),
    ("Gate 3", f"={R('gate_3')}", None),
]
for i, (lab, f, fmt) in enumerate(drows):
    rr = DR0 + 1 + i
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f, fmt=fmt, font=F_BOLD)
rn, op, xd, g3s = (f"C{DR0 + 1}", f"C{DR0 + 2}", f"C{DR0 + 3}", f"C{DR0 + 4}")
REF["dash_renewal"] = f"Dashboard!$C${DR0 + 1}"
rr = DR0 + 5
sc_, sw_, so_, xr_ = R("dr_scale_renewal"), R("dr_switch_renewal"), R("dr_switch_offices"), R("dr_extra_drops")
put(ws, f"B{rr}", "The rule says", font=F_BOLD)
# 'Stop' only when both tests have failed; while renewal is under the switch bar and fewer than the extra drops have actuals,
# the switch test is still running (review R1-04)
put(ws, f"C{rr}", (f'=IF({rn}="","not yet: no renewal answers",IF(AND({g3s}="pass",{rn}>={sc_}),"Scale",'
                   f'IF(AND({op}>={so_},{rn}<{sw_},{xd}>={xr_}),"Switch to office-paid",'
                   f'IF(AND({rn}>={sw_},{rn}<{sc_}),"Rule silent: renewal between "&TEXT({sw_},"0%")&" and "&TEXT({sc_},"0%"),'
                   f'IF(AND({rn}<{sw_},{xd}<{xr_}),"not yet: the switch test needs "&({xr_}-{xd})&" more extra drop(s) with actuals (plan: run two more drops first)",'
                   f'IF(AND({rn}>={sc_},{g3s}="not yet"),"not yet: renewal clears the scale bar; Gate 3 is still open",'
                   f'IF({R("as_of")}>{R("decision_date")},"Stop: both tests fail","not yet: stop if nothing changes by the decision date")))))))'), font=F_BOLD, fill=FILL_KEY)
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
# coverage: drops whose results are due (debrief T+10 on or before the as-of date) and how many have actuals in (review R2-02)
due_m = f'COUNTIFS({R("sched_debrief")},"<="&{R("as_of")})'
due_n = f'COUNTIFS({R("sched_debrief")},"<="&{R("as_of")},{R("sched_actuals")},"Y")'
put(ws, f"B{SP + 3}", "Drops whose results are due (debrief T+10 by the as-of date) with actuals in")
put(ws, f"C{SP + 3}", f'={due_n}&" of "&{due_m}', font=F_BOLD)
put(ws, f"D{SP + 3}", f'=IF({due_m}>{due_n},"the three lines above and the pointer below leave out "&({due_m}-{due_n})&" drop(s) whose results are due","every drop whose results are due is in")', font=F_NOTE)
ws.merge_cells(f"D{SP + 3}:I{SP + 3}")
put(ws, f"B{SP + 4}", "Scenario the real numbers point to", font=F_BOLD)
pl_, bl_, pa_ = f"C{SP}", f"C{SP + 1}", f"C{SP + 2}"
put(ws, f"C{SP + 4}", (f'=IF({pl_}="","not enough data yet",IF(AND({rn}<>"",N({rn})=0,{pl_}<{R("g2_placed")}),"D: neither converts",'
                       f'IF({bl_}>={R("sc_c_misses")},"C: brands willing, offices unreliable",'
                       f'IF({rn}="","not enough data: no renewal answers yet",'
                       f'IF(N({rn})<{sw_},"B: brands pay once, offices love it",'
                       f'IF(AND(N({rn})>={sc_},{pl_}>={R("g2_placed")},N({pa_})>={R("g3_per_hour")}),"A: both sides work","between scenarios: see the rule"))))))'
                       f'&IF({due_m}>{due_n},"; "&({due_m}-{due_n})&" drop(s) with results due have no actuals yet, so this can change","")'),
    font=F_BOLD, fill=FILL_KEY)
ws.merge_cells(f"C{SP + 4}:I{SP + 4}")
REF["dash_rule"] = f"Dashboard!$C${rr}"
REF["dash_pointer"] = f"Dashboard!$C${SP + 4}"
REF["dash_due_cov"] = f"Dashboard!$C${SP + 3}"
# --- six-month goals
SG = SP + 7
section(ws, SG, "Six-month goals (plan): planned by the schedule against actual", last_col="I")
header_row(ws, SG + 1, 2, ["Goal", "Target", "Planned (Schedule)", "Actual", "Status"], height=22)
goals = [
    ("Paid campaigns", "goal_campaigns", f'=SUMIFS({dp("brands")},{dp("date")},"<="&{R("horizon_end")})', f'=COUNTIF({R("AC_revenue_usd")},">0")'),
    ("Renewals", "goal_renewals", f'=SUMIFS({dp("renewals")},{dp("date")},"<="&{R("horizon_end")})', f'=COUNTIF({R("AC_renewed")},"Y")'),
    ("Active offices", "goal_offices", f'=SUMIFS({dp("new_offices")},{dp("date")},"<="&{R("horizon_end")},{dp("run")},1)', f"={R('pl_active_offices')}"),
    ("Contribution per founder hour, standard runs", "g3_per_hour", f"=E{G3PH}", f"=F{G3PH}"),
]
for i, (lab, tk, pf, af) in enumerate(goals):
    rr = SG + 2 + i
    f_ = PH if "hour" in lab else INT
    put(ws, f"B{rr}", lab)
    put(ws, f"C{rr}", f"={R(tk)}", fmt=f_)
    put(ws, f"D{rr}", pf, fmt=f_)
    put(ws, f"E{rr}", af, fmt=f_, font=F_BOLD)
    goal_st = f'IF(E{rr}="",IF({R("as_of")}>{R("decision_date")},"miss","not yet"),IF(E{rr}>=C{rr},"pass",IF({R("as_of")}>{R("decision_date")},"miss","not yet")))'
    if tk == "g3_per_hour":   # the same coverage rule as the Gate 3 rate (review R2-02)
        goal_st = f'IF(AND(D{G3COV}>0,F{G3COV}<D{G3COV}),"not yet: "&(D{G3COV}-F{G3COV})&" standard run(s) without actuals",{goal_st})'
    put(ws, f"F{rr}", "=" + goal_st, font=F_BOLD, align=Alignment(wrap_text=True))
    if tk == "g3_per_hour":
        ws.row_dimensions[rr].height = 45
    REF["dash_goal_" + tk] = f"Dashboard!$D${rr}"
    REF["dash_goal_status_" + tk] = f"Dashboard!$F${rr}"
status_cf(ws, f"F{SG + 2}:F{SG + 5}")
ws.conditional_formatting.add(f"F{SG + 2}:F{SG + 5}", FormulaRule(formula=[f'LEFT(F{SG + 2},LEN("not yet"))="not yet"'], fill=PatternFill("solid", fgColor="EDEDED"), font=Font(color="555555")))
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
                     "The total row is per founder hour across all scheduled drops, before overhead that drops do not absorb. Rows follow Schedule's row order, so a drop you add "
                     "sits at the bottom whatever its date.", font=F_NOTE)
widths(ws, {"A": 11, "B": 54, "C": 13, "D": 13, "E": 13, "F": 14, "G": 17, "H": 12, "I": 12, "J": 13, "K": 13, "L": 13})
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
# the error scan on Checks covers the Dashboard's headline values and everything from the gates down
# (the headline detail column and G5 read Checks, so they stay out of the scan to avoid a circular reference)
_ck = WS["Checks"][f"D{CK0}"]
_ck.value = _ck.value.replace("DASH_HEAD", f"Dashboard!C9:C{8 + N_HEAD}").replace("DASH_BODY", f"Dashboard!A{CR0}:L{DSE + 1}")

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
        if isinstance(v, list):
            # live text: plain parts become quoted literals (each under 255 characters), ("ref", key, fmt) parts read Inputs (review R2-09a)
            parts, plain = [], ""
            for part in v:
                if isinstance(part, tuple):
                    parts.append(f'TEXT({R(part[1])},"{part[2]}")')
                    plain += "$000"
                else:
                    for i0 in range(0, len(part), 200):
                        parts.append('"' + part[i0:i0 + 200].replace('"', '""') + '"')
                    plain += part
            put(ws, f"B{rr}", "=" + "&".join(parts), align=WRAP)
            v = plain
        else:
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
# merged banners do not grow with their text in Sheets: give every row-3 banner room for two lines
for t in TABS:
    if WS[t]["A3"].value or WS[t]["B3"].value:
        WS[t].row_dimensions[3].height = max(WS[t].row_dimensions[3].height or 0, 30)
wb.active = TABS.index("Dashboard")
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
# write the reference map for the audit and test scripts
import json
with open(os.path.join(HERE, "ref_map.json"), "w") as fh:
    json.dump({k: v for k, v in REF.items() if isinstance(v, str)}, fh, indent=1, sort_keys=True)
print("saved", OUT)
