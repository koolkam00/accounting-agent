#!/usr/bin/env bash
# run-all.sh: every automated test for the identity system (v1.4, 2026-10-24: review round 3 cases added). Run from anywhere:
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
for s in basic allergen-25-words long-name short-name retailer-only code-only batch-5-offices ingredient-list-37-words ingredient-list-50-words ingredient-list-74-words single-ingredient logo-wide logo-compact allergen-max-review two-flavors logo-wide-full-card logo-wide-gives-way; do
  expect 0 "tent card renders: $s" node render/render.js tent-card $T/SAMPLE-$s.json "$TMP/tc-$s.pdf"
done
# v1.2 (review round 1): the removed "Nowhere" option is refused; split mode puts the list on the front face;
# the give-way drops the product line before the name shrinks; a wide logo replaces the typed name
sed 's/"allergen_source": "single_ingredient"/"allergen_source": "none_on_label"/' $T/SAMPLE-single-ingredient.json > "$TMP/nowhere.json"
expect 2 "tent card refuses the removed \"Nowhere\" allergen option (none_on_label)" node render/render.js tent-card "$TMP/nowhere.json" "$TMP/nowhere.pdf"
fitof() { node render/render.js tent-card "$1" "$TMP/fit.pdf" --json 2>/dev/null | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s.slice(s.indexOf("{")));console.log(JSON.stringify(j.fit[0]))})'; }
F=$(fitof $T/SAMPLE-ingredient-list-74-words.json); echo "$F" | grep -q '"ingredients_on_front_face":true' && ok "74-word ingredient list: the whole list is on the front face (the one marked to face the room)" || bad "split mode front face: $F"
F=$(fitof $T/SAMPLE-allergen-max-review.json); echo "$F" | grep -q '"product_dropped":true' && [ "$(echo "$F" | sed -E 's/.*"name_px":([0-9.]+).*/\1/' | cut -d. -f1)" -gt 48 ] && ok "reviewer's max allergen card: product line dropped first, name kept above its 36 pt floor ($F)" || bad "give-way order: $F"
F=$(fitof $T/SAMPLE-logo-wide.json); echo "$F" | grep -q '"logo":"logo-wide"' && ok "a wide brand logo replaces the typed name" || bad "logo: $F"
# v1.3 (review round 2, R2-05): one claims list for every template; a claim is an error, not a note
for c in "Each bite supports gut health." "Each bite boosts immunity." "A healthy snack for your desk." "Guaranteed to be the best you have tried."; do
  sed "s/\"card_sentences\": \"[^\"]*\"/\"card_sentences\": \"SAMPLE Two friends bake these in Queens. $c\"/" $T/SAMPLE-basic.json > "$TMP/claim.json"
  expect 2 "tent card refuses a claim in the two sentences: \"$c\"" node render/render.js tent-card "$TMP/claim.json" "$TMP/claim.pdf"
done
sed 's/"card_sentences": "[^"]*"/"card_sentences": "SAMPLE Two friends bake these in Queens. Each bite supports gut health.", "claims_reviewed": "Y", "claims_review_reason": "SAMPLE test of the override only."/' $T/SAMPLE-basic.json > "$TMP/claim-ok.json"
expect 0 "the founder's claims override (claims_reviewed Y with a reason) turns the error into a warning" node render/render.js tent-card "$TMP/claim-ok.json" "$TMP/claim-ok.pdf"
# v1.3 (review round 2): two flavors print each statement under its own name, both at 14 pt; too long refuses
F=$(fitof $T/SAMPLE-two-flavors.json); echo "$F" | grep -q '"flavors":2' && ok "two flavors: one card, each package's statement under its own flavor name, both locked at 14 pt" || bad "two flavors: $F"
node render/render.js tent-card $T/SAMPLE-two-flavors-too-long-must-block.json "$TMP/tf.pdf" --json > "$TMP/tf.json" 2>/dev/null; [ $? = 2 ] && grep -q "one card per flavor" "$TMP/tf.json" && ok "two long flavor statements are refused with the one-card-per-flavor instruction (exit 2)" || bad "two-flavor refusal"
# v1.3 (review round 2, R2-08): a wide logo stops at 0.75 in and gives way after the story and find-it line
F=$(fitof $T/SAMPLE-logo-wide-full-card.json); L=$(echo "$F" | sed -E 's/.*"logo_in":([0-9.]+).*/\1/'); echo "$F" | grep -q '"story_dropped":false' && python3 -c "import sys; sys.exit(0 if float('$L') >= 0.75 else 1)" && ok "a wide logo on a full card keeps 0.75 in or more ($L in), and the story stays" || bad "wide logo floor: $F"
# v1.4 (review round 3, R3-04): a wide logo at its 0.75 in floor gives way to the typed name before the card is refused
F=$(fitof $T/SAMPLE-logo-wide-gives-way.json); echo "$F" | grep -q '"logo":"logo-wide-replaced-by-typed-name"' && echo "$F" | grep -q '"story_dropped":false' && ok "round-3 reviewer's 25+18-word ALL-CAPS card with a wide logo and both buy halves: the logo gives way to the typed name, the story stays ($F)" || bad "wide logo gives way: $F"
# v1.4 (review round 3, R3-06): a split card keeps "Take one." and the QR on the room face when the list leaves room, and flags it when not
F=$(fitof $T/SAMPLE-ingredient-list-50-words.json); echo "$F" | grep -q '"qr_on_room_face":true' && ok "50-word ingredient list: split card, \"Take one.\" and the QR also on the face toward the room" || bad "split card QR on the room face: $F"
node render/render.js tent-card $T/SAMPLE-ingredient-list-74-words.json "$TMP/s74.pdf" --json > "$TMP/s74.json" 2>/dev/null; grep -q '"qr_off_room_face": true' "$TMP/s74.json" && grep -q "Slack or email post" "$TMP/s74.json" && ok "74-word ingredient list: no room for the QR on the room face, so the card warns and flags qr_off_room_face for the report" || bad "74-word split card flag"
# v1.4 (review round 3, R3-02): the wider claims net, phrase by phrase, and end to end on a card and a report
expect 0 "claims net: FDA structure or function examples, sales and return wording caught; ordinary copy and every shipped sentence pass (tests/claims/claims-test.js)" node tests/claims/claims-test.js
for c in "Calcium builds strong bones." "The fiber maintains bowel regularity and promotes digestion." "Good for your gut." "Our best flavor yet."; do
  sed "s/\"card_sentences\": \"[^\"]*\"/\"card_sentences\": \"SAMPLE Two friends bake these in Queens. $c\"/" $T/SAMPLE-basic.json > "$TMP/claim.json"
  expect 2 "tent card refuses (v1.4): \"$c\"" node render/render.js tent-card "$TMP/claim.json" "$TMP/claim.pdf"
done
sed 's/"card_sentences": "[^"]*"/"card_sentences": "SAMPLE Two friends bake these in Queens. Lift the lid and take one; the resealable bag prevents crumbs."/' $T/SAMPLE-basic.json > "$TMP/plain.json"
expect 0 "tent card accepts ordinary copy the v1.3 list refused (\"Lift the lid\", \"prevents crumbs\")" node render/render.js tent-card "$TMP/plain.json" "$TMP/plain.pdf"
python3 -c "import json,sys; d=json.load(open('templates/report/samples/SAMPLE-5-offices.json')); d['learned']='SAMPLE Sales rose 20% at the Union Square store after the drop.\nSAMPLE The card converted 12% of tasters into buyers.\nSAMPLE We saw clear uplift and a 3x return on spend.'; [o.update(placement_photo='', later_photo='') for o in d['offices']]; json.dump(d,open(sys.argv[1],'w'))" "$TMP/claim-report.json"
expect 2 "report refuses the round-3 reviewer's sales sentences in \"What we learned\"" node render/render.js report "$TMP/claim-report.json" "$TMP/claim-report.pdf"
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
for s in basic allergen-25-words long-name short-name logo-wide logo-compact ingredient-list-50-words ingredient-list-74-words two-flavors logo-wide-full-card logo-wide-gives-way; do
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

# part 2: documents, signature, avatar (v1.1)
expect 0 "swap test: a new brand onto the card from the guide alone, under 10 minutes; every box the guide names exists" node tests/guide-walkthrough/swap-test.js
expect 0 "signature builds with filled SAMPLE details (tests/signature/out-filled/)" node render/build-signature.js --brand tests/signature/SAMPLE-brand-filled.json --out tests/signature/out-filled
expect 0 "documents, report, proposal, signature and avatar (tests/documents/doc-tests.js)" node tests/documents/doc-tests.js
expect 0 "panel: pick, add and remove records (case label); no \"record 1:\" jargon" node tests/panel/records-test.js
expect 0 "details.html: details filled in Chrome alone reach every document; a later terminal build keeps them" node tests/details/details-test.js

rm -rf "$TMP"
echo "----"
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
