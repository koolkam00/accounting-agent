#!/usr/bin/env python3
"""Build clay-icp-tables/clay-icp-tables.xlsx: the Google Sheets version of both tables, with live daily views.

Tabs: Offices, Brands, Daily view - Offices, Daily view - Brands, Dictionary, Scoring, Routine.
The score, readiness and view-helper columns are formulas, so a change to status, do_not_contact,
known_to_founder, hold_before_outreach, founder_ok_to_queue or title_match moves the daily views at once.
The daily-view tabs use SORT and FILTER (Google Sheets, Excel 365). LibreOffice 24.2 has neither, so
_build/test_workbook.py checks the helper columns LibreOffice can compute and keeps the static CSVs.
No macros, no scripts.
"""
import os
import re

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula

import common as C
import config as K
import dictionary as DD
import stage3_merge as M

OUT = os.path.join(C.A_DIR, "clay-icp-tables.xlsx")
LAST = 1000  # formula ranges reach row 1000 so added rows are counted
BRAND_NAME = "Desk Drop"   # the working name: change it here or in Routine!B1 (company_name)
TAGLINE = "Emerging brands. Delivered to your workday."

FILL = {"founder": PatternFill("solid", fgColor="FFF2CC"), "formula": PatternFill("solid", fgColor="D9D9D9"),
        "E / founder": PatternFill("solid", fgColor="DDEBF7"), "build": PatternFill("solid", fgColor="FFFFFF")}
HEAD = Font(bold=True)
NUMERIC = {"score", "score_raw", "score_onsite", "score_size", "score_attendance", "score_address", "score_title",
           "score_known", "score_buy", "score_ny", "score_why", "score_rev", "score_fit", "score_contact",
           "score_review", "rank", "onsite_low", "onsite_high", "onsite_central", "onsite_fit_share", "lat", "lon",
           "blocks_outside", "why_now_age_days", "graded_retailer_count_within_ten",
           "nearest_retailer_blocks_outside"}
IN_FLIGHT_ARR = "{" + ",".join(f'"{s}"' for s in M.IN_FLIGHT) + "}"


def load(name):
    return pd.read_csv(os.path.join(C.A_DIR, name), dtype=str, keep_default_na=False)


def val(col, v):
    if col in NUMERIC and v not in ("", None):
        try:
            f = float(v)
            return int(f) if f.is_integer() and col not in ("lat", "lon", "onsite_fit_share") else f
        except ValueError:
            return v
    return v


def formulas(side, L, r):
    """Formula text for row r. L maps column name -> letter."""
    def c(name):
        return f"{L[name]}{r}"

    def rng(name):
        return f"${L[name]}$2:${L[name]}${LAST}"
    f = {}
    if side == "office":
        f["score_title"] = f'=IF({c("title_match")}="exact",{K.P_TITLE["exact"]},IF({c("title_match")}="adjacent",{K.P_TITLE["adjacent"]},0))'
        f["score_known"] = f'=IF({c("known_to_founder")}="Y",{K.W_KNOWN},0)'
        parts = "+".join(c(x) for x in ("score_onsite", "score_size", "score_attendance", "score_address",
                                         "score_title", "score_known"))
        f["score"] = f'=IF({c("gate_result")}="pass",ROUND({parts},1),0)'
        f["ready_for_outreach"] = (f'=IF(AND({c("gate_result")}="pass",{c("hold_before_outreach")}<>"Y",'
                                   f'{c("first_name")}<>"",OR({c("onsite_founder_call")}<>"Y",'
                                   f'{c("founder_ok_to_queue")}="Y")),"Y","N")')
        f["ready_reason"] = (f'=_xlfn.TEXTJOIN("; ",TRUE,IF({c("gate_result")}<>"pass","gated out",""),'
                             f'IF({c("hold_before_outreach")}="Y","on hold: "&{c("hold_reason")},""),'
                             f'IF({c("first_name")}="","no contact named on an opened page",""),'
                             f'IF(AND({c("onsite_founder_call")}="Y",{c("founder_ok_to_queue")}<>"Y"),'
                             f'"Tuesday estimate band "&{c("onsite_band")}&": founder\'s call",""))')
    else:
        f["score_known"] = f'=IF({c("known_to_founder")}="Y",{K.B_KNOWN},0)'
        parts = "+".join(c(x) for x in ("score_buy", "score_ny", "score_why", "score_rev", "score_fit",
                                         "score_contact", "score_known", "score_review"))
        f["score"] = f'=IF({c("gate_result")}="pass",{parts},0)'
        f["ready_for_outreach"] = (f'=IF(AND({c("gate_result")}="pass",{c("hold_before_outreach")}<>"Y",'
                                   f'{c("first_name")}<>""),"Y","N")')
        f["ready_reason"] = (f'=_xlfn.TEXTJOIN("; ",TRUE,IF({c("gate_result")}<>"pass","gated out",""),'
                             f'IF({c("hold_before_outreach")}="Y","on hold: "&{c("hold_reason")},""),'
                             f'IF({c("first_name")}="","no contact named on an opened page",""))')
    f["in_flight"] = f'=IF(ISNUMBER(MATCH({c("status")},{IN_FLIGHT_ARR},0)),"Y","N")'
    f["group_blocked"] = (f'=IF(COUNTIFS({rng("company_group")},{c("company_group")},{rng("in_flight")},"Y")'
                          f'+COUNTIFS({rng("company_group")},{c("company_group")},{rng("do_not_contact")},"Y")>0,"Y","N")')
    f["eligible"] = (f'=IF(AND({c("status")}="new",{c("do_not_contact")}="N",{c("ready_for_outreach")}="Y",'
                     f'{c("opt_out_date")}="",{c("group_blocked")}="N"),"Y","N")')
    f["view_pick"] = (f'=IF({c("eligible")}<>"Y","N",IF(COUNTIFS({rng("company_group")},{c("company_group")},'
                      f'{rng("eligible")},"Y",{rng("score")},">"&{c("score")})+COUNTIFS({rng("company_group")},'
                      f'{c("company_group")},{rng("eligible")},"Y",{rng("score")},{c("score")},{rng("row_order")},'
                      f'"<"&{c("row_order")})=0,"Y","N"))')
    f["daily_view_rank"] = (f'=IF({c("view_pick")}<>"Y","",COUNTIFS({rng("view_pick")},"Y",{rng("score")},'
                            f'">"&{c("score")})+COUNTIFS({rng("view_pick")},"Y",{rng("score")},{c("score")},'
                            f'{rng("row_order")},"<"&{c("row_order")})+1)')
    f["in_daily_view"] = (f'=IF({c("daily_view_rank")}="","N",IF({c("daily_view_rank")}<={K.DAILY_VIEW_SIZE},'
                          f'"Y","N"))')
    f["row_order"] = "=ROW()-1"
    return f


def header_fill(col, ddict):
    who = ddict.get(col, {}).get("edited_by", "build")
    return FILL.get(who, FILL["build"])


def table_sheet(wb, title, df, side, ddict):
    ws = wb.create_sheet(title)
    cols = list(df.columns)
    L = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
    for j, c in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=j, value=c)
        cell.font = HEAD
        cell.fill = header_fill(c, ddict)
    for i, rec in enumerate(df.to_dict("records"), start=2):
        fm = formulas(side, L, i)
        for j, c in enumerate(cols, start=1):
            if c in fm:
                ws.cell(row=i, column=j, value=fm[c])
            else:
                ws.cell(row=i, column=j, value=val(c, rec[c]))
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(df) + 1}"
    for c in cols:
        w = 14
        if c in ("company", "title", "check_before_send", "score_reason", "why_now", "contact_note", "b_notes",
                 "notes", "founder_review_reason", "gate_reason", "ready_reason", "hold_reason", "onsite_basis"):
            w = 40
        ws.column_dimensions[L[c]].width = w
    n = len(df) + 1
    lists = {"status": "new,queued,contacted,replied,call_booked,call_done,yes_in_principle,materials_sent,"
                       + ("signed" if side == "office" else "paid") + ",not_now,no,wrong_person,do_not_contact",
             "do_not_contact": "Y,N", "known_to_founder": "Y,N", "hold_before_outreach": "Y,N",
             "founder_ok_to_queue": "Y", "email_status": "verified,unverified,none",
             "channel": "email,linkedin,warm-intro,walk-in"}
    if side == "office":
        lists["title_match"] = "exact,adjacent,none"
    for c, lst in lists.items():
        dv = DataValidation(type="list", formula1=f'"{lst}"', allow_blank=True)
        dv.add(f"{L[c]}2:{L[c]}{max(n, 2)}")
        ws.add_data_validation(dv)
    return ws, L


def view_sheet(wb, title, src_title, L, side):
    ws = wb.create_sheet(title)
    cols = M.STABLE + M.DV_EXTRA[side]
    first, last = L[cols[0]], L[cols[-1]]
    # the block must be contiguous in the source table, in this order
    idx = [list(L).index(c) for c in cols]
    assert idx == list(range(idx[0], idx[0] + len(cols))), "daily-view block is not contiguous"
    for j, c in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=j, value=c)
        cell.font = HEAD
    k = cols.index("daily_view_rank") + 1
    src = f"'{src_title}'!${first}$2:${last}${LAST}"
    cond = f"'{src_title}'!${L['in_daily_view']}$2:${L['in_daily_view']}${LAST}=\"Y\""
    formula = f'=IFERROR(_xlfn._xlws.SORT(_xlfn._xlws.FILTER({src},{cond}),{k},TRUE),"No row is ready today: see the Routine tab")'
    ref = f"A2:{get_column_letter(len(cols))}{K.DAILY_VIEW_SIZE + 1}"
    ws["A2"] = ArrayFormula(ref, formula)
    ws["A1"].comment = Comment(
        f"Live view: the {K.DAILY_VIEW_SIZE} best-scored rows of {src_title} with status = new, do_not_contact = N, "
        "ready_for_outreach = Y, no opt-out and nobody in their company_group in flight; one row per group. "
        "It updates when you edit those columns. Uses SORT and FILTER (Google Sheets).", "workstream A")
    ws.freeze_panes = "C2"
    for j in range(1, len(cols) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 16
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions[get_column_letter(cols.index("score_reason") + 1)].width = 50
    ws.column_dimensions[get_column_letter(cols.index("check_before_send") + 1)].width = 60
    return ws


def text_sheet(wb, title, rows, widths, wrap_cols=()):
    ws = wb.create_sheet(title)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row, start=1):
            cell = ws.cell(row=i, column=j, value=v)
            if i == 1 or (isinstance(v, str) and v.isupper() and len(v) < 40):
                cell.font = HEAD
            if j in wrap_cols:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A2"
    return ws


SCORING_ROWS = [
    ["table", "part", "points", "rule in plain words"],
    ["Offices", "HARD GATES", "", "Applied before any enrichment spend. A row fails if any one holds; a failed row scores 0."],
    ["Offices", "gate", "fail", "Outside the cluster: B's in_boundary = N against cluster-1-flatiron/boundary.geojson."],
    ["Offices", "gate", "fail", "Inside a coworking space (B's in_coworking = Y), or no staffed office at the address."],
    ["Offices", "gate", "fail", "Tuesday estimate wholly under 30 or wholly over 250. A range that crosses 30 or 250 passes with a flag."],
    ["Offices", "gate", "fail", "Coworking site whose operator is not shown to control the pantry, or a site possibly closed."],
    ["Offices", "SCORE", "0 to 100", "How likely this office fits the drop and can say yes, from what is known today."],
    ["Offices", "score_onsite", "0 to 30", "25 x the share of the Tuesday range inside 40 to 250 (ratio scale), plus 5 when the count is for the New York office; unknown headcount 7."],
    ["Offices", "score_size", "-4 to 15", "500 or fewer staff 15; 501 to 1,000 6; 1,001 to 4,999 2; 5,000+ 0; unknown 8; minus 4 when a controlling parent is named."],
    ["Offices", "score_attendance", "-5 to 15", "On-site 5 days 15; hybrid 4 days 12; 3 days 10; days not stated 7; 2 or fewer 5; no signal 6; remote -5; plus 3 when the policy names Tuesday (cap 15)."],
    ["Offices", "score_address", "0 to 15", "Occupied 10, occupancy-unconfirmed 5, signed-not-occupied 2; 0 with an address conflict; plus source confidence high 5, medium 3, low 0."],
    ["Offices", "score_title", "0 to 10", "Primary contact in the five target titles (or their direct forms), on an opened page, in New York: 10. Any other named person: 5. Nobody: 0."],
    ["Offices", "score_known", "0 or 15", "known_to_founder = Y."],
    ["Offices", "ties", "", "Share of the range inside 40 to 250, then source confidence, then name."],
    ["Offices", "Tuesday estimate", "", "Sourced count x New York share (100% for a New York office count; 50% to 100% for a company-wide count with a New York HQ; 5% to 100% otherwise) x the in-office rate (67% for firms of 500 or fewer, 57% for 501 to 4,999, 46% for 5,000+; Partnership for New York City, March 2025, via plan.md). Low to high, central = square root of low x high. An estimate until intake replaces it."],
    ["Brands", "HARD GATES", "", "A row fails if any one holds; a failed row scores 0."],
    ["Brands", "gate", "fail", "Excluded category: alcohol, cannabis or hemp, supplements, anything needing preparation."],
    ["Brands", "gate", "fail", "An explicit health claim (structure or function wording such as 'supports gut health'). Nutrient-content claims such as '10g protein' pass with founder_review = Y."],
    ["Brands", "gate", "fail", "Not shelf-stable: refrigerated, frozen, under 60 days, or shelf_stable = N."],
    ["Brands", "gate", "fail", "No buy path: no graded store (store_selector or brand_claim) within ten blocks of the cluster and no online store."],
    ["Brands", "SCORE", "0 to 100", "How likely this brand fits a founding campaign now: buyable near the offices, New York first, with a reason to sample now and a reachable owner."],
    ["Brands", "score_buy", "0 to 25", "Store page inside the cluster 25; store page within ten blocks 20; brand locator inside 17; brand locator within ten 13; online store only 6; none 0."],
    ["Brands", "score_ny", "0 to 20", "HQ New York City 20; rest of New York State 13; Northeast 8; elsewhere 3; unknown 4; minus 3 when a New York HQ is unverified."],
    ["Brands", "score_why", "0 to 15", "Press in the last 180 days 15, 181 to 365 days 8; own new listing in 180 days 8, 181 to 365 days 4; none or unverified 0."],
    ["Brands", "score_rev", "0 to 10", "$500k to $10M 10; unknown 5; under $500k 2; over $10M 0."],
    ["Brands", "score_fit", "0 to 10", "Shelf-stable Y 4, likely 2, unknown 1; individually packaged Y 3, unknown 1; online store Y 3, unknown 1."],
    ["Brands", "score_contact", "0 to 10", "Founder named on an opened page 6 (first name only or snippet 3); marketing lead on an opened page 4 (snippet 2)."],
    ["Brands", "score_known", "0 or 10", "known_to_founder = Y."],
    ["Brands", "score_review", "-35 to 0", "The most severe founder-review type: revenue over $10M sourced -35; owned by a large company -25; scale signals -12; dormant -12; heritage -10; perishable risk -8; under $500k -5; alcohol-adjacent -5; borderline claim -4; pack format -4; other -2."],
    ["Brands", "ties", "", "Store grade, then why-now points, then name."],
    ["Both", "DAILY VIEW", "", "The ten best-scored rows with status = new, do_not_contact = N, ready_for_outreach = Y and no opt_out_date, taking one row per company_group and skipping any group with a row in flight (queued to materials_sent) or a do-not-contact row."],
    ["Both", "ready_for_outreach", "Y/N", "Passed the gates, not on hold, a contact named on an opened page, and (offices) a Tuesday band of 40 to 250 or founder_ok_to_queue = Y."],
]


ROUTINE_ROWS = [
    ["minute", "step", "where", "what to do"],
    ["0:00-2:00", "1. Log yesterday", "Offices and Brands tabs (or Clay)",
     "For every reply, bounce and opt-out since yesterday set status (CONTRACTS section 4 words) and E's columns. Any opt-out in any words: do_not_contact = Y, status = do_not_contact, opt_out_date = today. Never reverse it. A wrong_person reply: copy the backup_ contact into the primary columns, reset title_match, set status = new."],
    ["2:00-3:00", "2. Clear holds you checked", "Offices tab",
     "If a walk-by showed a held company on the lobby directory, set hold_before_outreach = N (it may then enter the view). If you want an under-40 or over-250 estimate in anyway, set founder_ok_to_queue = Y."],
    ["3:00-4:00", "3. Open both daily views", "Daily view - Offices, Daily view - Brands",
     "They have already updated. Take the top five of each (ten a day, the plan's pace). Rows 6 to 10 are spares for any row that fails step 4."],
    ["4:00-13:00", "4. One minute per row, ten rows", "check_before_send column",
     "Read score_reason and check_before_send. Do what it says and nothing more: find the person on LinkedIn and paste contact_linkedin_url (this confirms the name and role); confirm an old record; for a brand, re-open the store page before using the retailer line; read a founder-review note. If the person has left or the row is wrong, set status = wrong_person (offices: try the backup) or no, and take the next spare."],
    ["13:00-14:00", "5. Export", "File > Download > CSV (each daily view tab)",
     "Save the two tabs as daily-view-offices.csv and daily-view-brands.csv for E's draft maker (desk-drop-outreach/messages/_render/fill.py drafts --daily; it accepts status new or queued for a first touch). Export before step 6: a queued row leaves the live view at once. Sending is E's routine, not this one."],
    ["14:00-15:00", "6. Queue", "status column",
     "Set status = queued on the rows you will send today (about five per side). They leave the daily view and their company_group is blocked, so no second person from the same company is in flight. Rows you skipped stay new for tomorrow."],
    ["", "", "", ""],
    ["WEEKLY", "", "", ""],
    ["Friday, 10 min", "Refresh", "Offices and Brands tabs",
     "Copy B's walk notes into hold_before_outreach (N once the lobby directory shows the company); mark known_to_founder for anyone you know; add a row for each referral (status = new, referral_from = the referrer's row_id). Before anyone rebuilds the files, save these two tabs as CSV in clay-icp-tables/live/ so status carries over (clay-build-sheet.md, section 4)."],
    ["", "", "", ""],
    ["COLOR KEY", "", "", ""],
    ["yellow header", "you edit", "", "status-side columns the founder sets (known_to_founder, hold_before_outreach, founder_ok_to_queue, title_match, contact_linkedin_url, work_email)"],
    ["blue header", "outreach edits", "", "status, do_not_contact and E's tracking columns, written the same day"],
    ["grey header", "formula", "", "never type here: score, readiness and the view helpers"],
    ["white header", "build", "", "researched facts; change them by fixing the source in _build/ and rebuilding"],
]


def main():
    ddict = {r["column"]: r for r in DD.dictionary_rows()}
    off, br = load("offices.csv"), load("brands.csv")
    DD.check(list(off.columns), "offices")
    DD.check(list(br.columns), "brands")
    wb = Workbook()
    wb.remove(wb.active)
    _, Lo = table_sheet(wb, "Offices", off, "office", ddict)
    _, Lb = table_sheet(wb, "Brands", br, "brand", ddict)
    view_sheet(wb, "Daily view - Offices", "Offices", Lo, "office")
    view_sheet(wb, "Daily view - Brands", "Brands", Lb, "brand")
    rows = [["column", "tables", "group", "edited_by", "values", "meaning"]] + [
        [r["column"], r["tables"], r["group"], r["edited_by"], r["values"], r["meaning"]] for r in DD.dictionary_rows()]
    text_sheet(wb, "Dictionary", rows, [28, 9, 22, 12, 40, 100], wrap_cols=(5, 6))
    text_sheet(wb, "Scoring", SCORING_ROWS, [9, 20, 10, 140], wrap_cols=(4,))
    rt = text_sheet(wb, "Routine", [["company_name", BRAND_NAME, "", "The working name lives in this one cell."],
                                     ["TAGLINE", TAGLINE, "", ""],
                                     ["", "", "", ""]] + [[None] * 4] + ROUTINE_ROWS, [16, 30, 34, 120], wrap_cols=(4,))
    rt["A4"] = '="15-minute morning routine, "&B1&" outreach tables"'
    rt["A4"].font = HEAD
    for cell in rt[5]:
        cell.font = HEAD
    rt.freeze_panes = None
    wb.defined_names["company_name"] = DefinedName("company_name", attr_text="Routine!$B$1")
    wb.save(OUT)
    pd.DataFrame(DD.dictionary_rows()).to_csv(os.path.join(C.A_DIR, "column-dictionary.csv"), index=False)
    print("wrote", OUT, "and column-dictionary.csv")


if __name__ == "__main__":
    main()
