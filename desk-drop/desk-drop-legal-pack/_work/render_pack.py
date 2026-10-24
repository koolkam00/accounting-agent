#!/usr/bin/env python3
"""Render the signable blocks of the pack (files 03, 05, 10, 13) to PDF and DOCX.

Run from anywhere:  python3 desk-drop-legal-pack/_work/render_pack.py
Source of truth is always the .md file. Edit the .md, then re-run this.
Outputs go to desk-drop-legal-pack/rendered/ (PDF, DOCX) and
desk-drop-legal-pack/_work/png/ (page images for visual checks).

Needs: pandoc, node with playwright, pdftoppm, pdfinfo.
"""
import pathlib, re, subprocess, sys, json, tempfile

PACK = pathlib.Path(__file__).resolve().parent.parent
OUT = PACK / "rendered"
PNG = PACK / "_work" / "png"
OUT.mkdir(exist_ok=True)
PNG.mkdir(parents=True, exist_ok=True)

# (source file, block marker, output basename, CSS density)
JOBS = [
    ("03-office-participation-agreement.md", "AGREEMENT", "03-office-participation-agreement", "tight"),
    ("05-llc-operating-agreement.md", "AGREEMENT", "05-llc-operating-agreement", "normal"),
    ("10-brand-campaign-agreement.md", "AGREEMENT", "10-brand-campaign-agreement", "normal"),
    ("13-survey-privacy-notice.md", "NOTICE", "13-survey-privacy-notice", "normal"),
]

CSS = {
"normal": """
@page { size: Letter; margin: 0.6in 0.7in 0.6in 0.7in; }
body { font-family: Inter, 'DejaVu Sans', sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1a1a1a; }
h1 { font-size: 15pt; margin: 4pt 0 8pt; font-weight: 700; }
h2 { font-size: 11.5pt; margin: 12pt 0 4pt; font-weight: 700; }
h3 { font-size: 11pt; margin: 10pt 0 4pt; }
h4 { font-size: 10pt; margin: 8pt 0 2pt; font-weight: 700; }
h1, h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
table, tr { break-inside: avoid; page-break-inside: avoid; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 6pt 16pt; padding: 0; } li { margin: 0 0 2pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 9.2pt; }
th, td { border: 0.6pt solid #9a9a9a; padding: 3pt 5pt; vertical-align: top; text-align: left; }
thead th { background: #f0f0f0; }
.draft { font-size: 9pt; font-weight: 700; letter-spacing: .02em; border: 1pt solid #1a1a1a; display: inline-block; padding: 2pt 6pt; margin-bottom: 4pt; }
.sig { break-inside: avoid; table-layout: fixed; } .sig td, .sig th { width: 50%; } .sig td { height: 18pt; }
""",
"tight": """
@page { size: Letter; margin: 0.45in 0.55in 0.45in 0.55in; }
body { font-family: Inter, 'DejaVu Sans', sans-serif; font-size: 9.2pt; line-height: 1.31; color: #1a1a1a; }
h1 { font-size: 13.5pt; margin: 2pt 0 3pt; font-weight: 700; }
p { margin: 0 0 4.2pt; }
table { border-collapse: collapse; width: 100%; margin: 2pt 0 5pt; font-size: 9pt; }
th, td { border: 0.6pt solid #9a9a9a; padding: 2pt 4pt; vertical-align: top; text-align: left; }
thead th { background: #f0f0f0; }
.draft { font-size: 8.5pt; font-weight: 700; letter-spacing: .02em; border: 1pt solid #1a1a1a; display: inline-block; padding: 1pt 5pt; margin-bottom: 2pt; }
.sig { break-inside: avoid; table-layout: fixed; } .sig td, .sig th { width: 50%; } .sig td { height: 16pt; }
""",
}

def extract(md_text, marker):
    m = re.search(rf"<!-- {marker} START -->(.*?)<!-- {marker} END -->", md_text, re.S)
    if not m:
        sys.exit(f"marker {marker} not found")
    return m.group(1).strip() + "\n"

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr}")
    return r.stdout

def main():
    report = {}
    for src, marker, base, density in JOBS:
        block = extract((PACK / src).read_text(), marker)
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            mdf = td / f"{base}.md"
            mdf.write_text(block)
            frag = run(["pandoc", str(mdf), "-f", "gfm-tex_math_dollars", "-t", "html5"])
            # style the review heading and the signature table
            frag = frag.replace("<p><strong>Draft for attorney review. Not legal advice.</strong></p>",
                                '<p class="draft">Draft for attorney review. Not legal advice.</p>', 1)
            frag = re.sub(r"<table>(\s*(?:<colgroup>.*?</colgroup>\s*)?<thead>\s*<tr>\s*<th[^>]*>(?:For the|Signed by))", r'<table class="sig">\1', frag, flags=re.S)
            frag = re.sub(r"<thead>\s*<tr>(\s*<th[^>]*>\s*</th>)+\s*</tr>\s*</thead>", "", frag)
            title = re.search(r"<h[123][^>]*>(.*?)</h[123]>", frag, re.S).group(1)
            html = f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS[density]}</style></head><body>{frag}</body></html>"
            htmlf = td / f"{base}.html"
            htmlf.write_text(html)
            pdf = OUT / f"{base}.pdf"
            js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://{htmlf}');
  await p.pdf({{ path: '{pdf}', format: 'Letter', preferCSSPageSize: true, printBackground: true }});
  await b.close();
}})();
"""
            jsf = td / "r.js"
            jsf.write_text(js)
            run(["node", str(jsf)])
            # DOCX for attorney redlines
            run(["pandoc", str(mdf), "-f", "gfm-tex_math_dollars", "-o", str(OUT / f"{base}.docx")])
        pages = int(re.search(r"Pages:\s+(\d+)", run(["pdfinfo", str(pdf)])).group(1))
        # guard: every dollar amount in the source must survive into the PDF text
        pdftext = re.sub(r"\s+", " ", run(["pdftotext", str(pdf), "-"]))
        for amt in sorted(set(re.findall(r"\$\[?[0-9A-Z][0-9A-Z,]*\]?", block))):
            if amt not in pdftext:
                sys.exit(f"{base}: amount {amt} missing from PDF text (markdown mangled it?)")
        for old in PNG.glob(f"{base}-*.png"):
            old.unlink()
        run(["pdftoppm", "-r", "80", "-png", str(pdf), str(PNG / base)])
        report[base] = pages
    print(json.dumps(report, indent=1))

if __name__ == "__main__":
    main()
