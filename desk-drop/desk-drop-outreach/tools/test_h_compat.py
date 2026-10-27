#!/usr/bin/env python3
"""Paste exports/SAMPLE-pipeline_log.csv into a temporary copy of the financial model and check H's own checks.

    python3 tools/test_h_compat.py        # never writes inside financial-model/

The live exports/pipeline_log.csv ships header-only (review round 1, R1-18); its header is checked too.

Pass: H's Pipeline header check, text check and event/side check read 0, and H's Gate 0 and Gate 1 counts
equal the tracker Scorecard's (Gate 0 column, Gate 1 column) for the same rows.
"""
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True   # no __pycache__ in the deliverable folder (review round 3, R3-11)
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DD = os.path.dirname(ROOT)
H = os.path.join(DD, "financial-model", "Desk Drop financial model v1.xlsx")
REFS = os.path.join(DD, "financial-model", "_work", "ref_map.json")
sys.path.insert(0, HERE)


def main():
    import build_tracker as BT
    import test_tracker as T
    tmp = tempfile.mkdtemp(prefix="ddh_")
    wb = openpyxl.load_workbook(H)
    ws = wb["Pipeline"]
    rows = list(csv.reader(open(os.path.join(ROOT, "exports", "SAMPLE-pipeline_log.csv"), encoding="utf-8")))
    live = list(csv.reader(open(os.path.join(ROOT, "exports", "pipeline_log.csv"), encoding="utf-8")))
    out = []
    ok = [ws.cell(row=4, column=j).value for j in range(1, 10)] == rows[0]
    out.append(f"{'ok  ' if ok else 'FAIL'} header identical to H's Pipeline row 4")
    good = live == [rows[0]]
    ok &= good
    out.append(f"{'ok  ' if good else 'FAIL'} live exports/pipeline_log.csv is header-only, same header")
    for i, r in enumerate(rows[1:], start=5):
        for j, v in enumerate(r, start=1):
            val = None if v == "" else (dt.date.fromisoformat(v) if j == 1 else (float(v) if j == 6 else v))
            ws.cell(row=i, column=j, value=val)
    p = os.path.join(tmp, "h.xlsx")
    wb.save(p)
    os.makedirs(os.path.join(tmp, "out"))
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", os.path.join(tmp, "out"), p],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    r = openpyxl.load_workbook(os.path.join(tmp, "out", "h.xlsx"), data_only=True)
    refs = json.load(open(REFS))
    val = lambda ref: r[ref.split("!")[0]][ref.split("!")[1].replace("$", "")].value
    ck = {row[2]: row[3] for row in r["Checks"].iter_rows(min_row=1, values_only=True) if row[2]}
    for label in ("Pipeline: rows with a bad event or side",
                  "Pipeline: header row differs from HANDOFF, or something is pasted in the blank buffer columns",
                  "Pipeline: dates or value_number stored as text (columns A and F)"):
        good = ck.get(label) == 0
        ok &= good
        out.append(f"{'ok  ' if good else 'FAIL'} H check '{label[:60]}...' = {ck.get(label)}")
    sc, _ = T.recalc(os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx"))
    b = BT.build(True, os.path.join(tmp, "positions.xlsx"))
    s = sc["Scorecard"]
    pairs = [("pl_g0_office_conv", f"D{b.sc['o_conv']}"), ("pl_g0_office_yes", f"D{b.sc['o_yes']}"),
             ("pl_g0_brand_conv", f"D{b.sc['b_conv']}"), ("pl_g0_brand_yes", f"D{b.sc['b_yes']}"),
             ("pl_g1_signed", f"D{b.sc['g1_signed']}"), ("pl_g1_headcount", f"D{b.sc['g1_headcount']}"),
             ("pl_g1_paid", f"D{b.sc['g1_paid']}"), ("pl_med_office", f"E{b.sc['o_bp_med']}"),
             ("pl_med_brand", f"E{b.sc['b_wb_med']}"), ("pl_med_brand_after", f"E{b.sc['b_wa_med']}")]
    for hk, cell in pairs:
        hv, ev = val(refs[hk]), s[cell].value
        good = hv == ev
        ok &= good
        out.append(f"{'ok  ' if good else 'FAIL'} H {hk} = {hv}; tracker {cell} = {ev}")
    out.append(f"RESULT: {'pass' if ok else 'FAIL'}")
    print("\n".join(out))
    open(os.path.join(ROOT, "_work", "partB", "h_compat_log.txt"), "w").write(f"run {dt.datetime.now().isoformat(timespec='seconds')}\n" + "\n".join(out) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
