#!/usr/bin/env python3
"""Write clean CSV files from the tracker workbook (values only).

    python3 tools/export_csv.py                      # rebuild, recalculate, write every CSV this folder ships
    python3 tools/export_csv.py --from FILE.xlsx     # use a workbook downloaded from Google Sheets instead

Rules (CONTRACTS section 5 and financial-model/HANDOFF.md): UTF-8, one header row, dates YYYY-MM-DD,
numbers plain (no $, no thousands separators), empty rows dropped. When --from is given, the SAMPLE files
are not touched; the real handoff and pipeline files are written from the downloaded workbook.
"""
import argparse
import csv
import datetime as dt
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_tracker as BT   # noqa: E402


def clean(v):
    if v is None:
        return ""
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if (v.hour, v.minute, v.second) == (0, 0, 0) else v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def tab_rows(ws, ncols=None):
    hdr = []
    for c in ws[1]:
        if c.value is None:
            break
        hdr.append(c.value)
    if ncols:
        hdr = hdr[:ncols]
    out = []
    for row in ws.iter_rows(min_row=2, max_col=len(hdr), values_only=True):
        vals = [clean(v) for v in row]
        if any(x != "" for x in vals):
            out.append(vals)
    return hdr, out


def write(path, hdr, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)
    print(f"wrote {os.path.relpath(path, ROOT)} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src")
    a = ap.parse_args()
    if a.src:
        wb = openpyxl.load_workbook(a.src, data_only=True)
        for tab, path in (("signed_offices", "handoff/signed_offices.csv"), ("paid_brands", "handoff/paid_brands.csv"),
                          ("pipeline_log", "exports/pipeline_log.csv")):
            hdr, rows = tab_rows(wb[tab], 9 if tab == "pipeline_log" else None)
            write(os.path.join(ROOT, path), hdr, rows)
        return
    import test_tracker as T
    # header-only templates from the blank workbook
    BT.build(False, os.path.join(ROOT, "tracking", "conversation-tracker.xlsx"))
    write(os.path.join(ROOT, "tracking", "csv", "office_log.csv"), [c[0] for c in BT.OFFICE_COLS], [])
    write(os.path.join(ROOT, "tracking", "csv", "brand_log.csv"), [c[0] for c in BT.BRAND_COLS], [])
    write(os.path.join(ROOT, "tracking", "csv", "clay_tracking_columns.csv"),
          ["column", "type", "allowed_values", "written_when", "rule"], [list(r) for r in BT.CLAY_TRACKING])
    # SAMPLE files from the recalculated SAMPLE workbook
    BT.build(True, os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx"))
    wb, recalced = T.recalc(os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx"))
    for tab, path, n in (("signed_offices", "handoff/signed_offices.csv", None), ("paid_brands", "handoff/paid_brands.csv", None),
                         ("pipeline_log", "exports/pipeline_log.csv", 9)):
        hdr, rows = tab_rows(wb[tab], n)
        write(os.path.join(ROOT, path), hdr, rows)
    # scorecard readout (values), SAMPLE
    ws = wb["Scorecard"]
    rows = []
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=7, values_only=True):
        vals = [clean(v) for v in row]
        if any(x != "" for x in vals):
            rows.append(vals)
    write(os.path.join(ROOT, "tracking", "csv", "scorecard-SAMPLE.csv"),
          ["measure", "fri_wk1", "fri_wk2", "gate0", "as_of", "target", "how_counted"], rows)
    import shutil
    shutil.copy(recalced, os.path.join(ROOT, "_work", "partB", "recalc-SAMPLE.xlsx"))


if __name__ == "__main__":
    main()
