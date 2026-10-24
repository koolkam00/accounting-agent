#!/usr/bin/env python3
"""Recalculate a tracker with LibreOffice headless (every formula is computed on load) and
list formula errors. Google Sheets computes the same file on import; this is the offline check.

  python3 tools/recalc.py tracker.xlsx [--out recalculated.xlsx]
"""
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl

ERRORS = ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!", "Err:")


def recalc(path, out=None):
    tmp = tempfile.mkdtemp(prefix="ops_recalc_")
    src = os.path.join(tmp, "in.xlsx")
    shutil.copy(path, src)
    od = os.path.join(tmp, "out")
    os.makedirs(od)
    env = dict(os.environ, HOME=tmp)
    subprocess.run(["soffice", "--headless", "--norestore", "--calc", "--convert-to", "xlsx", "--outdir", od, src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900, env=env)
    res = os.path.join(od, "in.xlsx")
    if out:
        shutil.copy(res, out)
        res = out
    return res


def errors(path, limit=40):
    wb = openpyxl.load_workbook(path, data_only=True)
    found = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERRORS):
                    found.append("%s!%s=%s" % (ws.title, c.coordinate, c.value))
    return found[:limit], len(found)


if __name__ == "__main__":
    p = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    r = recalc(p, out)
    errs, n = errors(r)
    print("recalculated:", r)
    print("formula errors:", n)
    for e in errs:
        print("  ", e)
    sys.exit(1 if n else 0)
