#!/usr/bin/env bash
# build-pdfs.sh: rebuilds every PDF and PNG proof in pdf/ and specs/ from the templates.
# Run from the desk-drop-identity folder after any change (including a rename):
#   bash render/build-pdfs.sh
set -euo pipefail
cd "$(dirname "$0")/.."
node render/build-brand.js
node tests/check-tokens.js
T=templates/tent-card/samples; C=templates/case-label/samples
node render/render.js tent-card $T/SAMPLE-basic.json pdf/tent-card-SAMPLE-home-print.pdf --face-png pdf/tent-card-SAMPLE-face.png --png pdf/tent-card-SAMPLE-sheet.png --dpi 150
node render/render.js tent-card $T/SAMPLE-allergen-25-words.json pdf/tent-card-SAMPLE-allergen-25-words.pdf --face-png pdf/tent-card-SAMPLE-allergen-25-words-face.png --dpi 150
node render/render.js tent-card $T/SAMPLE-basic.json pdf/tent-card-SAMPLE-pro-bleed.pdf --mode pro
node render/render.js tent-card $T/SAMPLE-batch-5-offices.json pdf/tent-card-SAMPLE-batch-5-offices.pdf
# the blank form has no buy path yet, which is an error for a real card, so --force draws it anyway
node render/render.js tent-card $T/BLANK-placeholders.json pdf/tent-card-BLANK.pdf --face-png pdf/tent-card-BLANK-face.png --dpi 150 --force
node render/render.js case-label $C/SAMPLE-office-and-reserve.json pdf/case-label-SAMPLE.pdf --png pdf/case-label-SAMPLE.png --dpi 110
node render/render.js case-label $C/BLANK-placeholders.json pdf/case-label-BLANK.pdf --png pdf/case-label-BLANK.png --dpi 110
node render/render-page.js specs/tent-card-spec.html specs/tent-card-spec.pdf --png specs/tent-card-spec.png
node render/render-page.js specs/case-label-spec.html specs/case-label-spec.pdf --png specs/case-label-spec.png
echo "All PDFs rebuilt."
