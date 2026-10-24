#!/usr/bin/env bash
# run-all.sh: every automated test for the identity system. Run from anywhere:
#   bash tests/run-all.sh
# Needs Node 18+ with Playwright and ImageMagick (convert, montage). Optional QR decode test
# needs jsQR and pngjs: set DD_QR_DECODER to a folder where `npm install jsqr pngjs` was run.
set -uo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d "${TMPDIR:-/tmp}/dd-tests-XXXX")"
pass=0; fail=0
ok()  { echo "PASS  $1"; pass=$((pass+1)); }
bad() { echo "FAIL  $1"; fail=$((fail+1)); }
expect() { # expect <exit-code> <name> <command...>
  local want=$1 name=$2; shift 2
  "$@" >"$TMP/out.txt" 2>&1; local got=$?
  if [ "$got" = "$want" ]; then ok "$name"; else bad "$name (exit $got, wanted $want)"; sed 's/^/      /' "$TMP/out.txt" | head -8; fi
}
T=templates/tent-card/samples; C=templates/case-label/samples

expect 0 "tokens agree and meet contrast" node tests/check-tokens.js
for s in basic allergen-25-words long-name short-name retailer-only code-only batch-5-offices; do
  expect 0 "tent card renders: $s" node render/render.js tent-card $T/SAMPLE-$s.json "$TMP/tc-$s.pdf"
done
expect 2 "tent card refuses an over-full card (stress)" node render/render.js tent-card $T/SAMPLE-stress-must-block.json "$TMP/stress.pdf"
expect 3 "--final refuses SAMPLE data" node render/render.js tent-card $T/SAMPLE-basic.json "$TMP/final.pdf" --final
sed 's/"retailer_line": ""/"retailer_line": "[RETAILER, STREET]"/' $T/BLANK-placeholders.json > "$TMP/blank.json"
expect 3 "--final refuses placeholders" node render/render.js tent-card "$TMP/blank.json" "$TMP/blank.pdf" --final
cat > "$TMP/clean.json" <<'EOF'
{"brand_name":"Testbrand","product_name":"","card_sentences":"Two people make this. They wanted it.","allergen_line_verbatim":"Contains: milk.","may_contain_verbatim":"","retailer_line":"A Store, 1 A Street","discount_code":"","code_site":"","qr_url":"https://example.com/t","qr_display":"","office_id":"O-999","campaign_id":"CMP-999"}
EOF
expect 0 "--final accepts a complete, non-sample card (temp only, deleted)" node render/render.js tent-card "$TMP/clean.json" "$TMP/clean.pdf" --final
# tamper: shrink the locked allergen size in a throwaway copy
mkdir -p "$TMP/tamper" && cp -r templates tokens fonts system render wordmark "$TMP/tamper/"
sed -i.bak 's/--dd-print-allergen-size: 14pt/--dd-print-allergen-size: 10pt/' "$TMP/tamper/tokens/tokens.css"
expect 2 "allergen lock survives a tokens.css edit (tamper copy)" node "$TMP/tamper/render/render.js" "$TMP/tamper/templates/tent-card/tent-card.html" $T/SAMPLE-basic.json "$TMP/tamper.pdf"
for s in office-and-reserve long-and-edge-cases; do
  expect 0 "case label renders: $s" node render/render.js case-label $C/SAMPLE-$s.json "$TMP/cl-$s.pdf"
done
expect 3 "case label --final flags [PHONE] from brand.json" node render/render.js case-label $C/SAMPLE-office-and-reserve.json "$TMP/clf.pdf" --final

# visual tests (write PNGs for a person to look at)
for s in basic allergen-25-words long-name short-name; do
  node render/render.js tent-card $T/SAMPLE-$s.json "$TMP/f.pdf" --face-png tests/out/tc-$s-face.png --dpi 150 >/dev/null 2>&1
  convert tests/out/tc-$s-face.png -filter Triangle -resize x120 -quality 75 tests/downscale/$s-120px.jpg
  convert tests/out/tc-$s-face.png -filter Triangle -resize x60 -quality 75 tests/downscale/$s-60px.jpg
done
montage -label '%t' tests/downscale/*-120px.jpg -tile 2x -geometry +12+12 -pointsize 12 tests/downscale/contact-120px.png && \
montage -label '%t' tests/downscale/*-60px.jpg -tile 4x -geometry +10+10 -pointsize 10 tests/downscale/contact-60px.png && ok "downscale sheets written (look at tests/downscale/)" || bad "downscale sheets"
for s in allergen-25-words long-name; do
  node render/render.js tent-card $T/SAMPLE-$s.json "$TMP/f.pdf" --face-png tests/out/tc-$s-face-300dpi.png --dpi 300 >/dev/null 2>&1
  expect 0 "photo simulation: $s" node tests/photo-sim/photo-sim.js tests/out/tc-$s-face-300dpi.png tests/photo-sim/out $s
done
if [ -n "${DD_QR_DECODER:-}" ]; then
  for w in 4032 2048; do convert tests/photo-sim/out/close-allergen-25-words-$w.jpg "$TMP/close-$w.png"; done
  NODE_PATH="$DD_QR_DECODER/node_modules" node -e '
    const fs=require("fs"),{PNG}=require("pngjs"),jsQR=require("jsqr");let bad=0;
    for(const f of process.argv.slice(1)){const p=PNG.sync.read(fs.readFileSync(f));const r=jsQR(new Uint8ClampedArray(p.data),p.width,p.height);
      if(!r||r.data!=="https://example.com/s/SAMPLE-O-001"){bad++;console.log("no decode",f)}}process.exit(bad?1:0)' \
    tests/out/tc-allergen-25-words-face-300dpi.png "$TMP/close-4032.png" "$TMP/close-2048.png" && ok "QR decodes from render and simulated close photos (4032, 2048 px)" || bad "QR decode"
else
  echo "SKIP  QR decode (set DD_QR_DECODER to a folder with jsqr and pngjs installed)"
fi
expect 0 "name-length test (Dropp, Desk Drop Collective)" node tests/name-length/run-name-test.js
expect 0 "guide walkthrough (stranger fills the card from USAGE-GUIDE.md section 2)" node tests/guide-walkthrough/walkthrough.js

rm -rf "$TMP"
echo "----"
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
