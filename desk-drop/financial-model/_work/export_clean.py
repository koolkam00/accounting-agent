#!/usr/bin/env python3
"""Clean CSV exports of the workbook's key tables (CONTRACTS section 5: UTF-8, one header row, snake_case columns,
dates YYYY-MM-DD, money as plain numbers). Each table is found by its header text, so a layout change in
build_model.py does not silently shift the export. Called by recalc.py --csv DIR; it writes DIR/*.csv.

These files are read-only views of a recalculated copy at plan defaults. Nothing reads them back into the model.
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def snake(text):
    s = str(text).strip().lower()
    s = s.replace("%", " pct ").replace("$", " usd ").replace("&", " and ").replace("+", " plus ").replace("#", " num ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "col"


def unique(names):
    seen, out = {}, []
    for n in names:
        if n in seen:
            seen[n] += 1
            n = f"{n}_{seen[n]}"
        else:
            seen[n] = 1
        out.append(n)
    return out


def clean(v):
    if v is None:
        return ""
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, bool):
        return "Y" if v else "N"
    if isinstance(v, float):
        r = round(v, 4)
        return int(r) if r == int(r) else r
    return v


def write(outdir, name, header, rows):
    header = unique([snake(h) for h in header])
    with open(os.path.join(outdir, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            r = [clean(x) for x in r]
            r = (r + [""] * len(header))[:len(header)]
            w.writerow(r)
    return name, len(rows)


def find_row(ws, col, text, start=1, stop=400):
    for r in range(start, stop):
        if ws.cell(r, col).value == text:
            return r
    raise KeyError(f"{ws.title}: '{text}' not found in column {col}")


def export(wb, outdir):
    os.makedirs(outdir, exist_ok=True)
    refs = json.load(open(os.path.join(HERE, "ref_map.json")))
    done = []

    # Inputs: one row per assumption; delivery-model table and startup outlays in their own files
    ws = wb["Inputs"]
    hdr = ["key", "assumption", "value", "unit", "low", "high", "status", "source", "notes", "plan_default", "changed"]
    rows, models, startup = [], [], []
    su_hdr = None
    for r in range(5, ws.max_row + 1):
        k = ws.cell(r, 1).value
        if k == "key" and ws.cell(r, 12).value:          # the startup table's own header row
            su_hdr = [ws.cell(r, c).value for c in range(1, 19)]
            continue
        if not k or k == "key" or ws.cell(r, 2).value in (None, ""):   # section titles carry text in column A only
            continue
        vals = [ws.cell(r, c).value for c in range(1, 12)]
        if k == "model_table":
            models.append([ws.cell(r, c).value for c in range(2, 9)])
        elif str(k).startswith("su_"):
            startup.append([ws.cell(r, c).value for c in range(1, 19)])
        else:
            rows.append(vals)
    done.append(write(outdir, "inputs.csv", hdr, rows))
    done.append(write(outdir, "delivery_models.csv", ["delivery_model", "transport_per_drop_usd", "transport_per_stop_usd", "kit_mailing_per_office_usd",
                                                     "receiving_kitting_base_h", "drop_day_per_office_h", "checks_pickup_per_office_h"], models))
    su_names = ["key", "item", "working_usd", "unit", "low_usd", "high_usd", "status", "source", "notes", "plan_default_usd", "changed",
                "timing_date", "timing_basis", "include", "actual_paid_usd", "actual_paid_date", "cash_amount_used_usd", "cash_date_used"]
    done.append(write(outdir, "startup_outlays.csv", su_names, startup))

    # Scenarios: one row per lever, keyed from ref_map
    ws = wb["Scenarios"]
    rev = {v.replace("$", ""): k for k, v in refs.items() if v.startswith("Scenarios!$H$")}
    rows = []
    for r in range(10, 40):
        lab = ws.cell(r, 2).value
        if not lab or lab == "How it works":
            break
        rows.append([rev.get(f"Scenarios!H{r}", ""), lab] + [ws.cell(r, c).value for c in range(3, 11)] + [ws.cell(r, 17).value, ws.cell(r, 18).value])
    done.append(write(outdir, "scenarios.csv", ["lever", "label", "plan_base", "a", "b", "c", "d", "active_in_force", "unit", "source_and_reading",
                                                "changed", "blank_in_force"], rows))

    # Schedule, Drop_PnL, Drop_Actuals: header row 6, drop rows 7 to 18
    for tab, name in (("Schedule", "schedule.csv"), ("Drop_PnL", "drop_pnl.csv"), ("Drop_Actuals", "drop_actuals.csv")):
        ws = wb[tab]
        cols = [c for c in range(1, ws.max_column + 1) if ws.cell(6, c).value not in (None, "")]
        if tab == "Schedule":   # stop before the derived-default copies
            stop = next(c for c in cols if ws.cell(6, c).value == "default date")
            cols = [c for c in cols if c < stop]
        rows = [[ws.cell(r, c).value for c in cols] for r in range(7, 19)]
        done.append(write(outdir, name, [ws.cell(6, c).value for c in cols], rows))

    # Cash_Flow weekly: one row per week, one column per line
    ws = wb["Cash_Flow"]
    lines = [(r, ws.cell(r, 2).value) for r in range(9, 32) if ws.cell(r, 2).value]   # section rows carry their label in column A
    rows = []
    for c in range(3, 29):
        rows.append([ws.cell(4, c).value, ws.cell(5, c).value, ws.cell(6, c).value] + [ws.cell(r, c).value for r, _ in lines])
    done.append(write(outdir, "cash_flow_weekly.csv", ["week", "week_starts", "week_ends"] + [lab for _, lab in lines], rows))
    # Cash_Flow summary (lowest point, capital, bank variance)
    s0 = find_row(ws, 2, "Lowest cumulative net cash flow (before founder cash)", 20)
    rows = []
    r = s0
    while ws.cell(r, 2).value:
        rows.append([ws.cell(r, 2).value, ws.cell(r, 3).value])
        r += 1
    done.append(write(outdir, "cash_summary.csv", ["measure", "value"], rows))
    # Cash_Flow monthly: one row per month
    m0 = find_row(ws, 2, "Month starts", 30)
    mlines = []
    r = m0 + 3
    while ws.cell(r, 2).value:
        mlines.append((r, ws.cell(r, 2).value))
        r += 1
    rows = []
    for c in range(3, 11):
        rows.append([ws.cell(m0, c).value, ws.cell(m0 + 1, c).value, ws.cell(m0 + 2, c).value] + [ws.cell(rr, c).value for rr, _ in mlines])
    rows[-1][0:3] = ["six months", "", ""]
    done.append(write(outdir, "cash_flow_monthly.csv", ["month_starts", "counted_from", "counted_to"] + [lab for _, lab in mlines], rows))
    # overhead reconciliation lines under the monthly view
    rows = []
    r = m0 + 3 + len(mlines) + 1
    while r < m0 + 3 + len(mlines) + 15:
        if ws.cell(r, 2).value:
            rows.append([ws.cell(r, 2).value, ws.cell(r, 3).value])
        r += 1
    done.append(write(outdir, "overhead_reconciliation.csv", ["measure", "value"], rows))

    # Steady_State monthly view and break-even
    ws = wb["Steady_State"]
    for head, name, hdr_ in (("Line", "steady_state.csv", ["line", "plan_reading_e", "active_scenario", "unit", "how_it_is_built"]),
                             ("Measure", "break_even.csv", ["measure", "value", "", "unit", "how_it_is_built"])):
        r0 = find_row(ws, 2, head, 15)
        rows = []
        r = r0 + 1
        while ws.cell(r, 2).value:
            rows.append([ws.cell(r, c).value for c in range(2, 7)])
            r += 1
        if name == "break_even.csv":
            rows = [[x[0], x[1], x[3], x[4]] for x in rows]
            hdr_ = ["measure", "value", "unit", "how_it_is_built"]
        done.append(write(outdir, name, hdr_, rows))

    # Sensitivity tables 1 and 2, long format
    ws = wb["Sensitivity"]
    for head, name, axis in (("Price per office \\ brands", "sensitivity_price_brands.csv", "price_per_office_usd"),
                             ("Renewal rate \\ brands", "sensitivity_renewal_brands.csv", "renewal_rate")):
        r0 = find_row(ws, 2, head, 10)
        brands = [ws.cell(r0, c).value for c in range(3, 8)]
        rows = []
        r = r0 + 1
        while ws.cell(r, 2).value is not None and ws.cell(r, 3).value is not None:
            for j, b in enumerate(brands):
                rows.append([ws.cell(r, 2).value, b, ws.cell(r, 3 + j).value])
            r += 1
        done.append(write(outdir, name, [axis, "brands_per_drop", "contribution_per_founder_hour_usd"], rows))

    # Capital: the plan's table and the lines it leaves out
    ws = wb["Capital"]
    rows = [[ws.cell(r, c).value for c in range(2, 11)] for r in range(5, 15)]
    done.append(write(outdir, "capital.csv", ["item", "plan_low_usd", "plan_high_usd", "model_working_usd", "where_the_model_pays_it",
                                              "model_cash_in_six_months_usd", "model_less_plan_high_usd", "reading", "legal_pack_status"], rows))

    # Plan_Check reconciliation
    ws = wb["Plan_Check"]
    r0 = find_row(ws, 2, "Plan statement (plan.md)", 20)
    rows = []
    r = r0 + 1
    while ws.cell(r, 1).value is not None:
        rows.append([ws.cell(r, c).value for c in range(1, 9)])
        r += 1
    done.append(write(outdir, "plan_reconciliation.csv", ["num", "plan_statement", "plan_figure", "model_figure", "difference", "tolerance", "status", "reason"], rows))

    # Dashboard headline and gates
    ws = wb["Dashboard"]
    rows = []
    r = 9
    while ws.cell(r, 2).value:
        rows.append([ws.cell(r, 2).value, ws.cell(r, 3).value, ws.cell(r, 4).value])
        r += 1
    done.append(write(outdir, "dashboard_headline.csv", ["measure", "value", "detail"], rows))
    # cash at each stop point (review R2-08)
    r0 = find_row(ws, 2, "Review", 20)
    rows = []
    r = r0 + 1
    while ws.cell(r, 3).value is not None:
        rows.append([ws.cell(r, c).value for c in range(2, 7)])
        r += 1
    done.append(write(outdir, "cash_at_stop_points.csv", ["review", "date", "paid_out_before_review_day_usd", "brand_cash_received_by_review_day_usd",
                                                          "cumulative_net_cash_end_of_review_week_usd"], rows))
    a, b = refs["dash_gate_rows"].split("!")[1].replace("$", "").split(":")
    rows = [[ws.cell(r, c).value for c in range(1, 9)] for r in range(int(a[1:]), int(b[1:]) + 1)]
    done.append(write(outdir, "gates.csv", ["gate", "test", "review_date", "threshold", "model_assumes", "live_value", "status", "if_it_fails_plan"], rows))

    # Checks
    ws = wb["Checks"]
    rows = []
    r = 5
    while ws.cell(r, 1).value is not None:
        rows.append([ws.cell(r, c).value for c in range(1, 7)])
        r += 1
    done.append(write(outdir, "checks.csv", ["num", "area", "check", "value", "pass", "note"], rows))
    return done
