# R3 working notes Sat Oct 24 04:35:32 UTC 2026
- 47/47 builder suite pass in sb/ (tests-run.log), DD_QR_DECODER=work-r2/copy3/qrdec
- REPORT.md still missing at start of R3 (ls). README l.87, HANDOFF dev 6 say pending.
## Tests (R3)
1 allergen 25w+18w may-contain: mixed/caps/short name: all 14.00pt w600 black both faces; caps+wide logo+long buy line REFUSED (exit 2) while same card w/o logo fits (logo floor 0.75in). Error msg blames product/retailer. -> finding
2 downscale 120px: out/downscale-120-x3-sheet.png all names identifiable PASS
3 close photo sim: out/close-*-crop*.png legible 4032/2048, readable zoom 1280 PASS
4 report 10 offices: builder sample both photo rows p1, comments 8.25; my harder fill (83-86w comments, 75w learned, 48w rec, 34w velocity) fits p1 at 8pt floor, photos to p2 (placement row would overflow by 0.09in - checked). PASS
5 swap: 20 actions incl next office; 642-word sec2; status never says "Ready to print" when any yellow Check note (product line dropped) though guide step 7 + spec check 2 require it -> minor
   logo picture field empty text says 'None (prints as "No photo received")' -> minor
6 fonts PASS (css2 200, METADATA OFL, OFL byte-identical, no RFN, CID TrueType)
7 rename PASS (sb2 Shelfwise; details kept; 0 'desk drop' in 20 PDFs; card wordmark follows)
8 claims PASS in shipped text
9 signature PASS 600/360/plain
10 avatar PASS
11 specs PASS; minor: 9pt allergen label line & 8.5pt "Brought to you by" below SYSTEM.md's 10pt floor for sentences employees read; case-label spec says template v1.0
12 tokens PASS
## Findings draft
B R3-01 REPORT.md missing (3rd round)
M R3-02 claims regex misses FDA S/F examples (builds strong bones, maintains bowel regularity, maintain cell integrity), promotes/aids digestion, good for your gut, lowers cholesterol; report misses "Sales rose 20%", "converted 12%", "uplift", "3x return on spend": card + report exit 0 (data/r3-claim-*.json). Docs say templates refuse. False positives: lift the lid, prevents crumbs.
M R3-03 standard proposal 10/12 offices refused with 4 real B stores (v5,v6 by 0.02in; v1 by 0.09) -- builder's set passes. distance 'inside the cluster' wraps; Eden long name. three extra arrangements tested in sb3: worse.
m R3-04 wide logo + caps 25w+18w + long buy line refused; typed name fits; msg misleading
m R3-05 Ready to print only when zero warnings
m R3-06 split face: no QR/Take one toward room
m R3-07 logo empty text "No photo received"
m R3-08 tokens.json lacks light semantic aliases
m R3-09 9pt label/8.5pt brought-to-you below SYSTEM 10pt floor
