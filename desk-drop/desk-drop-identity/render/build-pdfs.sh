#!/usr/bin/env bash
# build-pdfs.sh: rebuilds every generated file from the templates and brand.json (v1.4, 2026-10-24; a spec page whose text would be cut off now stops the build):
#   wordmark, system/brand.js, signature/, avatar/, every PDF in pdf/, a PNG of every PDF page in
#   pdf/png/, and the spec sheets in specs/.
# Run from anywhere after any change (including a rename):
#   bash render/build-pdfs.sh
# Needs Node 18+ with Playwright, and pdftoppm (poppler) for the page PNGs.
set -euo pipefail
cd "$(dirname "$0")/.."
node render/build-brand.js
node tests/check-tokens.js
node render/build-signature.js
node render/build-avatar.js

T=templates/tent-card/samples; C=templates/case-label/samples
node render/render.js tent-card $T/SAMPLE-basic.json pdf/tent-card-SAMPLE-home-print.pdf --face-png pdf/tent-card-SAMPLE-face.png --png pdf/tent-card-SAMPLE-sheet.png --dpi 150
node render/render.js tent-card $T/SAMPLE-allergen-25-words.json pdf/tent-card-SAMPLE-allergen-25-words.pdf --face-png pdf/tent-card-SAMPLE-allergen-25-words-face.png --dpi 150
node render/render.js tent-card $T/SAMPLE-two-flavors.json pdf/tent-card-SAMPLE-two-flavors.pdf --face-png pdf/tent-card-SAMPLE-two-flavors-face.png --dpi 150
node render/render.js tent-card $T/SAMPLE-basic.json pdf/tent-card-SAMPLE-pro-bleed.pdf --mode pro
node render/render.js tent-card $T/SAMPLE-batch-5-offices.json pdf/tent-card-SAMPLE-batch-5-offices.pdf
# the blank form has no buy path yet, which is an error for a real card, so --force draws it anyway
node render/render.js tent-card $T/BLANK-placeholders.json pdf/tent-card-BLANK.pdf --face-png pdf/tent-card-BLANK-face.png --dpi 150 --force
node render/render.js case-label $C/SAMPLE-office-and-reserve.json pdf/case-label-SAMPLE.pdf --png pdf/case-label-SAMPLE.png --dpi 110
node render/render.js case-label $C/BLANK-placeholders.json pdf/case-label-BLANK.pdf --png pdf/case-label-BLANK.png --dpi 110

# documents (part 2)
doc() { # doc <template> <sample file stem> <pdf name>
  node render/render.js "$1" "templates/$1/samples/$2.json" "pdf/$3.pdf"
}
doc discovery-one-pager DEFAULT discovery-one-pager-BLANK
doc office-one-pager BLANK-placeholders office-one-pager-BLANK
doc brand-one-pager BLANK-placeholders brand-one-pager-BLANK
doc proposal BLANK-placeholders proposal-BLANK
doc proposal SAMPLE-founding proposal-SAMPLE-founding
doc proposal SAMPLE-standard-10-offices proposal-SAMPLE-standard-10-offices
doc report BLANK-placeholders report-BLANK
doc report SAMPLE-5-offices report-SAMPLE-5-offices
doc report SAMPLE-10-offices-long-comments report-SAMPLE-10-offices-long-comments

# a PNG of every page of every PDF, to look at (and for the README and spec sheets)
mkdir -p pdf/png
rm -f pdf/png/*.png
for f in pdf/*.pdf; do
  b=$(basename "$f" .pdf)
  pdftoppm -r 100 -png "$f" "pdf/png/$b"
done
# pdftoppm numbers pages -1, -01 or -001 depending on page count; normalise to -1, -2 ...
for f in pdf/png/*-0*.png; do [ -e "$f" ] && mv "$f" "$(echo "$f" | sed -E 's/-0+([0-9]+)\.png$/-\1.png/')"; done

node render/render-page.js specs/tent-card-spec.html specs/tent-card-spec.pdf --png specs/tent-card-spec.png
node render/render-page.js specs/case-label-spec.html specs/case-label-spec.pdf --png specs/case-label-spec.png
node render/render-page.js specs/documents-spec.html specs/documents-spec.pdf --png specs/documents-spec.png
echo "All PDFs rebuilt."
