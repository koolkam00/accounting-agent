#!/usr/bin/env bash
# Render the call guides and the note template to one printable PDF (Letter, landscape).
#   bash tools/build_call_print.sh
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=_work/partB/print
mkdir -p "$OUT"
cat > "$OUT/print.css" <<'CSS'
@page { size: Letter landscape; margin: 0.45in 0.5in; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 9.2pt; line-height: 1.32; color: #111; }
h1 { font-size: 15pt; margin: 0 0 4pt; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 11.5pt; margin: 10pt 0 3pt; border-bottom: 1px solid #999; }
h3 { font-size: 10pt; margin: 8pt 0 2pt; }
p { margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 2.5pt 4pt; vertical-align: top; text-align: left; }
th { background: #1f3a5f; color: #fff; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.4pt; }
pre { font-size: 8pt; background: #f4f4f4; padding: 4pt; white-space: pre-wrap; }
blockquote { margin: 4pt 0 4pt 10pt; padding-left: 6pt; border-left: 3px solid #1f3a5f; }
hr { border: 0; border-top: 1px solid #ccc; }
CSS
pandoc calls/office-call-guide.md calls/brand-call-guide.md calls/post-call-note-template.md \
  -f gfm-tex_math_dollars-tex_math_gfm -t html5 --standalone --metadata title="Call guides" --css print.css -o "$OUT/call-guides.html"
node -e '
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto("file://" + process.argv[1], { waitUntil: "load" });
  await p.pdf({ path: process.argv[2], format: "Letter", landscape: true, printBackground: true, preferCSSPageSize: true });
  await b.close();
})();' "$PWD/$OUT/call-guides.html" "$PWD/calls/call-guides-print.pdf"
pdftoppm -png -r 60 calls/call-guides-print.pdf "$OUT/page"
ls "$OUT"
