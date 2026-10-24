# Reviewer working notes, round 1 (started 2026-10-24 01:41 UTC)

## Read so far
- brief D, CONTRACTS, plan (appendix G card copy, M report layout, measurement, Phase 0-3)
- README, USAGE-GUIDE, SYSTEM, HANDOFF, decisions-log, sources, tests/README

## Candidate findings (to verify)
- REPORT.md missing (README says harness refused writing; orchestrator to save). CONTRACTS s1 requires it.
- Report 10-office test: photos moved to page 2 ("Photos received n of N" on p1). Plan layout item 3 "Evidence: two photos per office" on the one page. Check.
- Plan founding tier includes "written testimonial and case-study rights" - check proposal / brand one-pager reflect or omit.
- Plan report layout: "Header: brand, SKU, cluster, drop date, window"; roster columns Office | Industry | Tuesday headcount | Units placed | Gone by day 5 | Responses

## Test results so far (reviewer's own runs, outputs in _review/work/)
- T1 allergen 25w + may contain: PASS. Builder sample + my rv-allergen-max (25w + 25w may-contain, 25-char name, 181-char story, long buy path). Allergen computed 14.00pt both faces, weight 600, #000. Give-way: product line dropped, name 36pt @75% width, story kept at 12pt (priority question: name shrinks before story is dropped; width not re-widened after shrink). tc/rv-allergen-max-face.png
- T2 downscale 120px: PASS all (downscale/sheet-120-x3.png). 60px: worst case marginal.
- T3 close photo sim (123 px/in at 4032, blur, rotate, perspective, noise, JPEG; 2048 and 1280 copies): PASS even at 1280 (close/rv-close-1280-zoom3x.png)
- Ingredient-list split (74 words): reading face shows only a pointer; full list on other face (faces wall/product when standing in front of product). Story kept on front. Give-way inversion -> MAJOR.
- T4 report 10 offices builder sample: page 1 fits at floors (comments 8.25pt, learned 8.5) but ALL photos moved to page 2 -> evidence not on the one page. + retailer velocity line (24 words) -> REFUSED (exit 2). Longer learned/rec -> REFUSED. 11 offices fits at floor; 12 offices REFUSED (report maxRows 12, proposal maxRows 14).
- Ladder Delivered 515 vs roster total Delivered 500 (top-ups) on same page.
- Limitations text: "none of them is a sale" contradicts Purchased rung (code redemptions are purchases).
- Guide s6 says take wide+close on drop day, "these two photos go into the report"; report slots are wide day1 + close day 3/5. Inconsistent.
- pro mode 7.25x10.25 OK; fonts CID TrueType embedded.

## BLOCKERS found (verified, deterministic)
- Brand one-pager refuses (exit 2, "runs past the bottom") when (a) Roster today filled with the guide s10's own example (in builder's original folder), or (b) brand.json contacts filled with any realistic values ("Pat Example", "(212) 555-0100", ...) even with roster blank. Forced render: "Next step" wraps into footer. data/brand-real.json, rename/brand-real-forced-1.png. Only "Al Li"+placeholder roster passes.
- Standard 10-office proposal + 2.5:1 landscape map (exactly what HANDOFF asks B for) refuses (exit 2) in builder's folder with builder's SAMPLE-standard data. Forced: "The report" collides with footer; right column ~2in empty. docs/std-map-forced-1.png. Also 10off+2/4 stores+map, 11/12 offices fail.
- Final proposal (--final passes) mock page prints "Prepared by [FOUNDER NAME]" yellow even with brand.json filled; plus [BRAND],[SKU],[DROP DATE] yellow on page 2 -> guide rule 5 "Nothing yellow leaves the building". docs/final-founding-nomap-2.png
- REPORT.md missing.

## Other
- Proposal + brand one-pager payment trigger "email with every office's placement photo" / "when every placement photo is in" superseded by legal v0.7 (01:49) "email by T+1 listing offices placed, each with its photo; not placed by T+1 refunded".
- Proposal "cancel before the ship-by date": for campaign zero ship-by requested 12-22 vs cancel-by T-10 12-28 (legal says differ).
- Swap test: 14 actions to ready, +4 next office; all guide box names exist. PASS. Estimate ~8 min.
- Fonts PASS (OFL identical to upstream; Google Fonts CSS 200; METADATA OFL).
- Rename PASS (Shelfwise in copy: docs print new name, 0 old). Needs Node.
- contacts need Node (build-brand.js) - Chrome alone insufficient.
