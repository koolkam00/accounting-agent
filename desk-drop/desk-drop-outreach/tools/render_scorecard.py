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
ws.page_setup.fitToHeight = 2      # two pages (review round 3 added rows)
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_options.gridLines = False
ws.print_title_rows = "1:2"      # the SAMPLE banner repeats on every page (review round 2, R2-15)
tmp = tempfile.mkdtemp(prefix="ddsc_")
x = os.path.join(tmp, "scorecard.xlsx")
wb.save(x)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, x], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
pdf = os.path.join(tmp, "scorecard.pdf")
shutil.copy(pdf, base + ".pdf")
# 150 dpi (about 1240 x 1830 per page as LibreOffice lays it out), each page cut into a top and a bottom half so the text can be
# read on a screen (review round 1, R1-25: at 80 dpi it could not be read)
subprocess.run(["pdftoppm", "-png", "-r", "150", pdf, os.path.join(tmp, "p")], check=True)
pngs = sorted(f for f in os.listdir(tmp) if f.startswith("p") and f.endswith(".png"))
import glob
from PIL import Image
for old in glob.glob(base + "-p*.png"):
    os.remove(old)
from PIL import ImageDraw, ImageFont
STAMP = "SAMPLE · illustrative placeholders, not results"
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
except OSError:
    FONT = ImageFont.load_default()


def stamped(im):
    """Every half-page PNG carries a visible SAMPLE strip across its top (CONTRACTS section 2; review round 2, R2-15)."""
    w, _ = im.size
    strip = 56
    out = Image.new("RGB", (w, im.size[1] + strip), (179, 38, 30))
    out.paste(im.convert("RGB"), (0, strip))
    ImageDraw.Draw(out).text((24, 12), STAMP, fill=(255, 255, 255), font=FONT)
    return out


for i, f in enumerate(pngs, start=1):
    im = Image.open(os.path.join(tmp, f))
    w, h = im.size
    stamped(im.crop((0, 0, w, h // 2 + 40))).save(f"{base}-p{i}-top.png")
    stamped(im.crop((0, h // 2 - 40, w, h))).save(f"{base}-p{i}-bottom.png")
print(base + ".pdf", len(pngs), "pages,", 2 * len(pngs), "PNGs at 150 dpi")
