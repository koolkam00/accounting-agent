#!/usr/bin/env python3
"""Recalculate a workbook with LibreOffice headless and report key values.

Usage:
  python3 recalc.py [path.xlsx] [--csv OUTDIR] [--quiet]
  --csv writes clean one-header CSV tables to OUTDIR and human-readable tab snapshots to OUTDIR/snapshots.

Converts the workbook to xlsx in a temp folder (LibreOffice computes every
formula on load), reads it with openpyxl data_only=True, prints the checks
and key outputs, and returns the values dict for test scripts.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(os.path.dirname(HERE), "Desk Drop financial model v1.xlsx")
ERRORS = ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!", "Err:")


def recalc(path):
    tmp = tempfile.mkdtemp(prefix="ddfm_")
    src = os.path.join(tmp, "in.xlsx")
    shutil.copy(path, src)
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", out, src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    res = os.path.join(out, "in.xlsx")
    return openpyxl.load_workbook(res, data_only=True), res


def val(wb, ref):
    sh, cell = ref.split("!")
    return wb[sh][cell.replace("$", "")].value


def find_errors(wb):
    errs = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERRORS):
                    errs.append(f"{ws.title}!{c.coordinate}={c.value}")
    return errs


def report(wb, quiet=False):
    refs = json.load(open(os.path.join(HERE, "ref_map.json")))
    ck = wb["Checks"]
    rows = []
    for r in range(5, 200):
        if ck[f"A{r}"].value is None:
            break
        rows.append((ck[f"A{r}"].value, ck[f"B{r}"].value, ck[f"C{r}"].value, ck[f"D{r}"].value, ck[f"E{r}"].value))
    fails = [x for x in rows if x[4] not in (1, "info")]   # an 'info' row is not a check (review R3-03)
    errs = find_errors(wb)
    if not quiet:
        print(f"checks: {len(rows)} total, {len(fails)} failing")
        for f in fails:
            print("  FAIL", f)
        print(f"error cells: {len(errs)}")
        for e in errs[:40]:
            print("  ", e)
        keys = ["cf_low", "cf_low_week", "cf_low_date", "cf_commit", "cf_gap", "cf_end", "ss_contrib", "ss_ph", "ss_net", "ss_contrib_plan",
                "ss_cost_plan", "be_n_one", "be_n_three", "be_n_over", "be_b_new", "be_b_ren", "be_b_dir", "be_price", "su_total", "cap_low", "cap_high",
                "changed_count", "h_win", "dash_rule", "dash_pointer", "ck_integrity", "ck_data", "ck_plan"]
        for k in keys:
            if k in refs:
                print(f"  {k:18s} {val(wb, refs[k])}")
    return rows, fails, errs


def export_csv(wb, outdir, sheets):
    import csv
    os.makedirs(outdir, exist_ok=True)
    for name in sheets:
        ws = wb[name]
        fn = os.path.join(outdir, name.lower() + ".csv")
        with open(fn, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            maxc = ws.max_column
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=maxc, values_only=True):
                vals = []
                for v in row:
                    if hasattr(v, "strftime"):
                        v = v.strftime("%Y-%m-%d")
                    elif isinstance(v, float):
                        v = round(v, 4)
                    vals.append("" if v is None else v)
                while vals and vals[-1] == "":
                    vals.pop()
                w.writerow(vals)


if __name__ == "__main__":
    args = sys.argv[1:]
    path = DEFAULT
    csvdir = None
    quiet = "--quiet" in args
    if args and not args[0].startswith("--"):
        path = args[0]
    if "--csv" in args:
        csvdir = args[args.index("--csv") + 1]
    wb, res = recalc(path)
    rows, fails, errs = report(wb, quiet)
    if csvdir:
        # human-readable tab dumps (titles, banners, several header rows) go to snapshots/; clean one-header tables to csvdir
        export_csv(wb, os.path.join(csvdir, "snapshots"), ["Dashboard", "Inputs", "Scenarios", "Schedule", "Drop_PnL", "Cash_Flow", "Steady_State",
                                                           "Sensitivity", "Plan_Check", "Capital", "Checks"])
        import export_clean
        for name, n in export_clean.export(wb, csvdir):
            print(f"  {name:34s} {n} rows")
        print("csv written to", csvdir, "(clean tables) and", os.path.join(csvdir, "snapshots"), "(tab snapshots)")
    sys.exit(1 if (fails or errs) else 0)
