#!/usr/bin/env python3
"""Dry runs: replay a SAMPLE scenario day by day through the tracker and every generator.

  python3 tools/dryrun.py zero        # campaign zero: 2 brands x 5 offices, founder model
  python3 tools/dryrun.py standard    # first standard run: 3 brands x 10 offices, courier model
  python3 tools/dryrun.py zero --final-only

For each day on the scenario's calendar, the tracker is built with only the rows the founder would
have logged by that day (today_override = that day), recalculated with LibreOffice, read back, and
compared with tools/tracker.py's independent arithmetic. The day's documents are generated from it.
Outputs: dry-run/<scenario>/ (SAMPLE only).
"""
import copy
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tracker as B  # noqa: E402
import common  # noqa: E402
import opscal  # noqa: E402
import recalc as RC  # noqa: E402
import scenarios as S  # noqa: E402
import tracker as TR  # noqa: E402

ROOT = common.ROOT
# The dry runs use reserved example domains so QR codes can be drawn and decoded; real use keeps [DOMAIN].
SAMPLE_CONFIG = {"short_link_domain": "go.example.com", "survey_privacy_url": "https://example.com/survey-privacy"}


def snapshot(scn, day):
    rows = {}
    for tab, lst in scn["rows"].items():
        keep = []
        for r in lst:
            if r.get("_on") and r["_on"] > day:
                continue
            x = {k: v for k, v in r.items() if not k.startswith("_")}
            for f, on in (r.get("_fields_on") or {}).items():
                if on and on > day:
                    x.pop(f, None)
            keep.append(x)
        rows[tab] = keep
    resp = {}
    for cid, (brand, rr) in scn["responses"].items():
        resp[cid] = (brand, [r[:7] for r in rr if r[7] <= day and r[0].date() <= day])
    # Response tabs exist from the day the survey form is made (T-4).
    T = scn["T"]
    if day < opscal.add_bd(T, -4):
        resp = {}
    return rows, resp


def build_snapshot(scn, day, path):
    rows, resp = snapshot(scn, day)
    free = {k: v for k, v in rows.items() if k in ("office_form", "brand_form")}
    tabs = {k: v for k, v in rows.items() if k not in free}
    B.build(path, sample=tabs, response_tabs=resp, today=day, config=SAMPLE_CONFIG)
    if free:
        import openpyxl
        wb = openpyxl.load_workbook(path)
        for tab, lst in free.items():
            ws = wb[tab]
            hdr = [c.value for c in ws[1]]
            for r, row in enumerate(lst, start=2):
                for k, v in row.items():
                    c = ws.cell(row=r, column=hdr.index(k) + 1, value=v)
                    if k == "Timestamp":
                        c.number_format = "yyyy-mm-dd hh:mm:ss"
        wb.save(path)
    return path


def make_photos(scn, out):
    """Stand-in SAMPLE photos: the identity workstream's simulated pantry photos, copied under each file name."""
    src = os.path.join(common.IDENTITY, "templates", "report", "samples", "photos")
    wide = sorted(x for x in os.listdir(src) if "wide" in x)
    close = sorted(x for x in os.listdir(src) if "close" in x)
    n = 0
    for r in scn["rows"].get("photos", []):
        d = os.path.join(out, "photos", r["campaign_id"])
        os.makedirs(d, exist_ok=True)
        pick = (wide if r["photo_type"] == "placement" else close)[n % 2]
        shutil.copy(os.path.join(src, pick), os.path.join(d, r["file_name"]))
        n += 1
    return os.path.join(out, "photos")


def last_day(scn):
    ds = []
    for lst in scn["rows"].values():
        for r in lst:
            if r.get("_on"):
                ds.append(r["_on"])
            ds += [v for v in (r.get("_fields_on") or {}).values() if v]
    return max(ds)


def recalc_and_read(path, out):
    r = RC.recalc(path, out)
    errs, n = RC.errors(r)
    tr = TR.Tracker(r)
    return tr, errs, n


def main(argv):
    name = argv[1] if len(argv) > 1 else "zero"
    scn = getattr(S, name)()
    out = os.path.join(ROOT, "dry-run", name)
    os.makedirs(out, exist_ok=True)
    final = last_day(scn) + dt.timedelta(days=1)
    work = os.path.join(ROOT, "_work", "dryrun-" + name)
    os.makedirs(work, exist_ok=True)
    p = build_snapshot(scn, final, os.path.join(work, "final-in.xlsx"))
    tr, errs, n = recalc_and_read(p, os.path.join(out, "SAMPLE-tracker-%s-final.xlsx" % name))
    print("final %s: formula errors %d %s" % (final, n, errs[:5]))
    bad = TR.compare(tr)
    print("python vs sheet mismatches:", len(bad))
    for b in bad[:60]:
        print("  ", b)
    return 0 if (n == 0 and not bad) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
