#!/usr/bin/env python3
"""Behaviour tests: edit a copy of the workbook, recalculate with LibreOffice, assert.

Every test writes to a temp copy; the deliverable is never modified.
SAMPLE rows used here start with 'SAMPLE' (CONTRACTS s2) and never ship.
Usage: python3 test_model.py   (exit 1 on any failure)
"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile

import openpyxl

import recalc

HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.load(open(os.path.join(HERE, "ref_map.json")))
SRC = recalc.DEFAULT
D = dt.date
RESULTS = []


def cell(ref):
    sh, c = ref.split("!")
    return sh, c.replace("$", "")


def run(edits, label):
    """edits: list of (sheet, cell, value). Returns recalculated workbook."""
    tmp = tempfile.mkdtemp(prefix="ddtest_")
    path = os.path.join(tmp, "t.xlsx")
    wb = openpyxl.load_workbook(SRC)
    for sh, c, v in edits:
        wb[sh][c].value = v
    wb.save(path)
    out, _ = recalc.recalc(path)
    rows, fails, errs = recalc.report(out, quiet=True)
    integ = [f for f in fails if f[1] in ("Integrity", "Schedule", "Data")]
    return out, integ, errs


def v(wb, key):
    sh, c = cell(REF[key])
    return wb[sh][c].value


def at(wb, sheet, c):
    return wb[sheet][c].value


def check(label, cond, detail=""):
    RESULTS.append((label, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + label + (f"  [{detail}]" if detail else ""))


def inp(key, value):
    sh, c = cell(REF[key])
    return (sh, c, value)


# ---------------------------------------------------------------- baseline
base, integ, errs = run([], "baseline")
check("baseline: no integrity failures and no error cells", not integ and not errs, f"{integ[:2]} {errs[:2]}")
b_low, b_end, b_ss = v(base, "cf_low"), v(base, "cf_end"), v(base, "ss_ph")
b_next_ph = at(base, "Dashboard", "C10")
print(f"   baseline low {b_low}, end {b_end}, steady per hour {b_ss:.2f}, next drop per hour {b_next_ph:.2f}")

# ---------------------------------------------------------------- price
wb, integ, errs = run([inp("price_std_office", 180)], "price 180")
check("price $180: standard runs per hour rises", at(wb, "Dashboard", "C11") > at(base, "Dashboard", "C11"),
      f"{at(base, 'Dashboard', 'C11'):.2f} -> {at(wb, 'Dashboard', 'C11'):.2f}")
check("price $180: cash at week 26 rises", v(wb, "cf_end") > b_end, f"{b_end} -> {v(wb, 'cf_end')}")
check("price $180: inputs-changed count = 1 and plan checks still reproduce (scenario rows use plan prices)",
      v(wb, "changed_count") == 1, f"changed {v(wb, 'changed_count')}")
check("price $180: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")

# ---------------------------------------------------------------- processing off
wb, integ, errs = run([inp("processing_on", 0)], "processing off")
check("bank transfer: campaign zero contribution = $960", abs(at(wb, "Drop_PnL", "AJ7") - 960) < 0.01, at(wb, "Drop_PnL", "AJ7"))
check("bank transfer: low point improves", v(wb, "cf_low") > b_low, f"{b_low} -> {v(wb, 'cf_low')}")
check("bank transfer: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")

# ---------------------------------------------------------------- home storage
wb, integ, errs = run([inp("storage_choice", "home")], "home storage")
check("home storage: standard run hard costs = $595", abs(at(wb, "Drop_PnL", "AA8") - 595) < 0.01, at(wb, "Drop_PnL", "AA8"))
check("home storage: no storage paid in the cash flow", at(wb, "Cash_Flow", "AC22") == 0, at(wb, "Cash_Flow", "AC22"))
check("home storage: steady-state overhead = $160", abs(v(wb, "ss_over_paid") - 160) < 0.01, v(wb, "ss_over_paid"))

# ---------------------------------------------------------------- insurance monthly
wb, integ, errs = run([inp("insurance_billing", "monthly")], "insurance monthly")
check("insurance monthly: five payments of $100 inside the window", abs(at(wb, "Cash_Flow", "AC21") + 500) < 0.01, at(wb, "Cash_Flow", "AC21"))
check("insurance monthly: low point improves", v(wb, "cf_low") > b_low, f"{b_low} -> {v(wb, 'cf_low')}")
check("insurance monthly: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")

# ---------------------------------------------------------------- close rate
wb, integ, errs = run([inp("close_rate", 0.1)], "close rate 10%")
check("close rate 10%: hours per win = 9.75", abs(v(wb, "h_win") - 9.75) < 0.001, v(wb, "h_win"))
check("close rate 10%: standard runs per hour falls", at(wb, "Dashboard", "C11") < at(base, "Dashboard", "C11"))

# ---------------------------------------------------------------- drop size drivers
wb, integ, errs = run([inp("std_brands_drop", 2)], "two brands per standard drop")
check("two brands per standard drop: runs 1 and 2 carry 2 brands and per hour falls",
      at(wb, "Schedule", "K8") == 2 and at(wb, "Schedule", "K9") == 2 and at(wb, "Dashboard", "C11") < at(base, "Dashboard", "C11"),
      (at(wb, "Schedule", "K8"), at(wb, "Dashboard", "C11")))
check("two brands per standard drop: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")
wb, integ, errs = run([inp("goal_offices", 20)], "goal of 20 offices")
check("goal of 20 offices: run 2 recruits 10 new offices and its hours rise", at(wb, "Schedule", "J9") == 10 and at(wb, "Drop_PnL", "AI9") > at(base, "Drop_PnL", "AI9"),
      (at(wb, "Schedule", "J9"), at(wb, "Drop_PnL", "AI9")))
check("goal of 20 offices: the run-2 fatigue warning clears", at(wb, "Schedule", "W9") == "ok", at(wb, "Schedule", "W9"))

# ---------------------------------------------------------------- scenarios
for sc in ["A", "B", "C", "D"]:
    wb, integ, errs = run([inp("active_scenario", sc)], f"scenario {sc}")
    k4, k5 = at(wb, "Schedule", "K10"), at(wb, "Schedule", "K11")
    l4, l5 = at(wb, "Schedule", "L10"), at(wb, "Schedule", "L11")
    check(f"scenario {sc}: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")
    print(f"   scenario {sc}: D4 brands {k4} renewals {l4}; D5 brands {k5} renewals {l5}; end cash {v(wb, 'cf_end')}; "
          f"steady contrib {v(wb, 'ss_contrib')}; steady net {v(wb, 'ss_net')}; steady per hour {v(wb, 'ss_ph')}")
    if sc == "A":
        check("A: steady state at $180 per office earns more than base", v(wb, "ss_contrib") > v(base, "ss_contrib"))
    if sc == "B":
        check("B: no renewals scheduled and office-paid revenue $500", l4 == 0 and l5 == 0 and abs(at(wb, "Steady_State", "D33") - 500) < 0.01,
              at(wb, "Steady_State", "D33"))
    if sc == "C":
        check("C: only one decision-window drop runs", k4 == 3 and k5 == 0)
    if sc == "D":
        check("D: no decision-window drops and zero steady state", k4 == 0 and k5 == 0 and v(wb, "ss_contrib") == 0)
        check("D: cash at week 26 below base", v(wb, "cf_end") < b_end)

# ---------------------------------------------------------------- edge cases on the schedule
wb, integ, errs = run([("Schedule", "K8", 0)], "run 1 with zero brands")
check("zero brands on run 1: the drop does not run, cost 0", at(wb, "Drop_PnL", "AA8") == 0 and at(wb, "Drop_PnL", "AK8") == "n/a")
check("zero brands on run 1: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")
wb, integ, errs = run([("Schedule", "I8", 1), ("Schedule", "J8", 1), ("Schedule", "K8", 1)], "one office")
check("one office on run 1: finite per hour", isinstance(at(wb, "Drop_PnL", "AK8"), (int, float)), at(wb, "Drop_PnL", "AK8"))
wb, integ, errs = run([("Schedule", "L10", 3)], "100% renewal on D4")
check("three renewals on D4: brand sales 6 h", abs(at(wb, "Drop_PnL", "AB10") - 6) < 0.001, at(wb, "Drop_PnL", "AB10"))
wb, integ, errs = run([("Schedule", "E8", D(2027, 2, 12))], "Friday drop")
check("a Friday drop is flagged and fails the schedule check", at(wb, "Schedule", "P8") == "not Tue/Wed" and any("schedule rules" in f[2] for f in integ))
wb, integ, errs = run([("Schedule", "E8", D(2026, 12, 22))], "blackout drop")
check("a drop in the December blackout is flagged", at(wb, "Schedule", "R8") == "clash")
wb, integ, errs = run([("Schedule", "A12", "DRP-006"), ("Schedule", "B12", "SAMPLE extra drop"), ("Schedule", "E12", D(2027, 4, 20)),
                       ("Schedule", "G12", "direct-ship"), ("Schedule", "H12", "standard"), ("Schedule", "I12", 10), ("Schedule", "J12", 8),
                       ("Schedule", "K12", 3), ("Schedule", "L12", 0), ("Schedule", "M12", 0)], "added drop")
check("an added drop flows into the cash flow (deposit inside the window)", v(wb, "cf_end") > b_end, f"{b_end} -> {v(wb, 'cf_end')}")
check("an added drop shows as a changed schedule row", at(wb, "Dashboard", "C21") >= 1, at(wb, "Dashboard", "C21"))
check("added drop: no integrity failures", not integ and not errs, f"{integ[:2]} {errs[:2]}")

# ---------------------------------------------------------------- SAMPLE actuals and pipeline, as of 2027-01-29
ed = [inp("as_of_override", D(2027, 1, 29)), ("Schedule", "N7", "Y")]
pl = [  # date, side, org_id, org_name, event, value_number, value_text, controls_budget
    (D(2026, 10, 28), "office", "SAMPLE-O-1", "SAMPLE office 1", "conversation", None, None, None),
    (D(2026, 10, 29), "office", "SAMPLE-O-2", "SAMPLE office 2", "conversation", None, None, None),
    (D(2026, 10, 30), "office", "SAMPLE-O-3", "SAMPLE office 3", "conversation", None, None, None),
    (D(2026, 11, 2), "office", "SAMPLE-O-4", "SAMPLE office 4", "conversation", None, None, None),
    (D(2026, 11, 3), "office", "SAMPLE-O-5", "SAMPLE office 5", "conversation", None, None, None),
    (D(2026, 11, 4), "office", "SAMPLE-O-1", "SAMPLE office 1", "yes_in_principle", None, None, None),
    (D(2026, 11, 5), "office", "SAMPLE-O-2", "SAMPLE office 2", "yes_in_principle", None, None, None),
    (D(2026, 11, 6), "office", "SAMPLE-O-3", "SAMPLE office 3", "yes_in_principle", None, None, None),
    (D(2026, 11, 9), "office", "SAMPLE-O-4", "SAMPLE office 4", "yes_in_principle", None, None, None),
    (D(2026, 11, 10), "office", "SAMPLE-O-5", "SAMPLE office 5", "yes_in_principle", None, None, None),
    (D(2026, 11, 10), "office", "SAMPLE-O-5", "SAMPLE office 5", "yes_in_principle", None, "SAMPLE duplicate row", None),
    (D(2026, 11, 3), "brand", "SAMPLE-B-1", "SAMPLE brand 1", "budget_probe", 800, "SAMPLE quote", "Y"),
    (D(2026, 11, 4), "brand", "SAMPLE-B-2", "SAMPLE brand 2", "budget_probe", 600, "SAMPLE quote", "Y"),
    (D(2026, 11, 5), "brand", "SAMPLE-B-3", "SAMPLE brand 3", "budget_probe", 1000, "SAMPLE quote", "Y"),
    (D(2026, 11, 6), "brand", "SAMPLE-B-4", "SAMPLE brand 4", "budget_probe", 1500, "SAMPLE quote", "N"),
    (D(2026, 11, 20), "office", "SAMPLE-O-1", "SAMPLE office 1", "signed", 60, None, None),
    (D(2026, 11, 23), "office", "SAMPLE-O-2", "SAMPLE office 2", "signed", 55, None, None),
    (D(2026, 11, 24), "office", "SAMPLE-O-3", "SAMPLE office 3", "signed", 110, None, None),
    (D(2026, 11, 30), "office", "SAMPLE-O-4", "SAMPLE office 4", "signed", 95, None, None),
    (D(2026, 12, 2), "office", "SAMPLE-O-5", "SAMPLE office 5", "signed", 190, None, None),
    (D(2026, 12, 9), "brand", "SAMPLE-B-1", "SAMPLE brand 1", "paid", 600, None, "Y"),
    (D(2026, 12, 10), "brand", "SAMPLE-B-2", "SAMPLE brand 2", "paid", 600, None, "Y"),
    (D(2026, 11, 3), "office", "SAMPLE-O-1", "SAMPLE office 1", "budget_probe", 150, "SAMPLE quote", None),
]
for i, row in enumerate(pl):
    for j, val in enumerate(row):
        if val is not None:
            ed.append(("Pipeline", f"{'ABCDEFGH'[j]}{5 + i}", val))
camp = [  # campaign rows for DRP-001
    ["SAMPLE-CMP-001", "DRP-001", D(2027, 1, 12), "founder", "founding", "SAMPLE-BR-001", 5, 275, 250, 245, 240, 5, 160, 31, 24, 40, 3, 600, D(2026, 12, 9), 0, D(2027, 1, 21), "yes", "pending", None, None, 5],
    ["SAMPLE-CMP-002", "DRP-001", D(2027, 1, 12), "founder", "founding", "SAMPLE-BR-002", 5, 275, 250, 238, 210, 0, 140, 27, 20, 33, 1, 600, D(2026, 12, 10), 0, D(2027, 1, 22), "maybe", "pending", None, None, 4],
]
for i, row in enumerate(camp):
    for j, val in enumerate(row):
        if val is not None:
            ed.append(("Actuals_Campaigns", f"{openpyxl.utils.get_column_letter(j + 1)}{5 + i}", val))
for j, val in enumerate(["DRP-001", D(2027, 1, 12), "founder", 5, 2, 45, 95, 20, "SAMPLE"]):
    ed.append(("Actuals_DropCosts", f"{openpyxl.utils.get_column_letter(j + 1)}5", val))
hl = [(D(2026, 11, 2), None, "brand_sales", 6), (D(2026, 11, 25), "DRP-001", "brand_sales", 14), (D(2026, 12, 1), "DRP-001", "office_coordination", 18),
      (D(2027, 1, 7), "DRP-001", "receiving_kitting", 3.5), (D(2027, 1, 12), "DRP-001", "drop_day", 5.5), (D(2027, 1, 19), "DRP-001", "checks_pickup", 3),
      (D(2027, 1, 22), "DRP-001", "reporting_debriefs", 4), (D(2027, 1, 22), "DRP-001", "admin_invoicing", 2)]
for i, (d_, drop, act, h) in enumerate(hl):
    ed += [("Hours_Log", f"A{5 + i}", d_), ("Hours_Log", f"D{5 + i}", act), ("Hours_Log", f"E{5 + i}", h), ("Hours_Log", f"F{5 + i}", "SAMPLE")]
    if drop:
        ed.append(("Hours_Log", f"B{5 + i}", drop))
# Toggl: header row 9 and two entries
for j, h in enumerate(["User", "Project", "Description", "Start date", "Duration", "Tags"]):
    ed.append(("Toggl_Import", f"{'ABCDEF'[j]}9", h))
ed += [("Toggl_Import", "A10", "SAMPLE"), ("Toggl_Import", "B10", "DRP-001"), ("Toggl_Import", "D10", "2027-01-12"), ("Toggl_Import", "E10", "01:30:00"), ("Toggl_Import", "F10", "drop_day"),
       ("Toggl_Import", "A11", "SAMPLE"), ("Toggl_Import", "B11", "admin"), ("Toggl_Import", "D11", "2027-01-13"), ("Toggl_Import", "E11", "00:45:00"), ("Toggl_Import", "F11", "admin_invoicing")]
wb, integ, errs = run(ed, "SAMPLE actuals")
check("SAMPLE: no integrity or data failures", not integ and not errs, f"{integ[:3]} {errs[:3]}")
dash = wb["Dashboard"]
status = {dash[f"B{r}"].value: dash[f"G{r}"].value for r in range(25, 40) if dash[f"B{r}"].value}
gates = {dash[f"A{r}"].value: dash[f"C{r}"].value for r in range(40, 46) if dash[f"A{r}"].value}
print("   gate rows:", json.dumps(status, default=str)[:900])
print("   gate overall:", gates)
check("SAMPLE: Gate 0 passes (5 offices yes, 3 brands at $500+ controlling budget; duplicate row and non-controller ignored)",
      gates.get("Gate 0") == "pass", gates.get("Gate 0"))
check("SAMPLE: Gate 1 passes (5 signed, 510 headcount, 2 paid)", gates.get("Gate 1") == "pass", gates.get("Gate 1"))
check("SAMPLE: Gate 2 misses (one campaign under 5 responses per office)", gates.get("Gate 2") == "miss", gates.get("Gate 2"))
check("SAMPLE: Gate 3 not yet", gates.get("Gate 3") == "not yet", gates.get("Gate 3"))
check("SAMPLE: Drop_Actuals revenue $1,200 and hard costs $160 + $80 allocations",
      at(wb, "Drop_Actuals", "D7") == 1200 and abs(at(wb, "Drop_Actuals", "J7") - 240) < 0.01, (at(wb, "Drop_Actuals", "D7"), at(wb, "Drop_Actuals", "J7")))
check("SAMPLE: actual hours for DRP-001 = 50 hand + 1.5 Toggl", abs(at(wb, "Drop_Actuals", "R7") - 51.5) < 0.001, at(wb, "Drop_Actuals", "R7"))
check("SAMPLE: placement within a day = 450/500", abs(at(wb, "Drop_Actuals", "AG7") - 0.9) < 0.0001, at(wb, "Drop_Actuals", "AG7"))
check("SAMPLE: live basis switches to actual", at(wb, "Drop_PnL", "BF7") == "actual", at(wb, "Drop_PnL", "BF7"))
check("SAMPLE: actual receipts replace plan receipts for DRP-001 (both $1,200, in week 7)",
      at(wb, "Cash_Flow", "I10") == 1200 and at(wb, "Cash_Flow", "I9") == 0, (at(wb, "Cash_Flow", "I9"), at(wb, "Cash_Flow", "I10")))
check("SAMPLE: actual drop costs hit the cash flow on the drop date (week 12)", abs(at(wb, "Cash_Flow", "N17") + 160) < 0.01, at(wb, "Cash_Flow", "N17"))
check("SAMPLE: Toggl hours read = 2.25", abs(at(wb, "Toggl_Import", "X12") - 2.25) < 0.001, at(wb, "Toggl_Import", "X12"))
check("SAMPLE: weekly hours log sums all hand and Toggl hours", abs(v(wb, "HL_week_total") - (56 + 2.25)) < 0.001, v(wb, "HL_week_total"))
check("SAMPLE: scenario pointer has data", v(wb, "dash_pointer") != "not enough data yet", v(wb, "dash_pointer"))
check("SAMPLE: median office probe = 150", v(wb, "pl_med_office") == 150, v(wb, "pl_med_office"))

# ---------------------------------------------------------------- bad data is caught
wb, integ, errs = run([("Hours_Log", "A5", D(2027, 1, 5)), ("Hours_Log", "D5", "kitting"), ("Hours_Log", "E5", 2),
                       ("Pipeline", "A5", D(2026, 11, 1)), ("Pipeline", "B5", "office"), ("Pipeline", "C5", "SAMPLE-O-9"), ("Pipeline", "E5", "meeting")], "bad data")
labels = [f[2] for f in integ]
check("bad activity key and bad event are flagged as data failures", any("invalid activity" in l for l in labels) and any("bad event" in l for l in labels), labels)

n_fail = sum(1 for r in RESULTS if not r[1])
print(f"\n{len(RESULTS) - n_fail} of {len(RESULTS)} tests pass")
sys.exit(1 if n_fail else 0)
