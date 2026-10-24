#!/usr/bin/env python3
"""Render the recalculated SAMPLE scorecard to PDF and PNG so it can be looked at.

    python3 tools/render_scorecard.py [recalculated.xlsx] [out_basename]
"""
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_work", "partB", "recalc-SAMPLE.xlsx")
base = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "tracking", "scorecard-SAMPLE")

wb = openpyxl.load_workbook(src, data_only=True)
for name in list(wb.sheetnames):
    if name != "Scorecard":
        del wb[name]
ws = wb["Scorecard"]
for col in "JKLMNOPQR":
    ws.column_dimensions[col].hidden = True
ws.print_area = f"A1:G{ws.max_row}"
ws.page_setup.orientation = "portrait"
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_options.gridLines = False
tmp = tempfile.mkdtemp(prefix="ddsc_")
x = os.path.join(tmp, "scorecard.xlsx")
wb.save(x)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, x], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
pdf = os.path.join(tmp, "scorecard.pdf")
shutil.copy(pdf, base + ".pdf")
subprocess.run(["pdftoppm", "-png", "-r", "80", pdf, os.path.join(tmp, "p")], check=True)
pngs = sorted(f for f in os.listdir(tmp) if f.startswith("p") and f.endswith(".png"))
for i, f in enumerate(pngs, start=1):
    shutil.copy(os.path.join(tmp, f), f"{base}-p{i}.png")
print(base + ".pdf", len(pngs), "pages")
