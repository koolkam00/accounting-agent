# Review round 1 fixes: progress log (builder, 2026-10-24)

Working file so nothing is lost on context compaction. Not a deliverable.
Backup of pre-fix outputs: scratchpad b_before/.

## Plan (finding -> fix)
- R1-03 router anchor-to-anchor; R1-04 frontage pins + face test; R1-05 confidence floor; R1-06 hq columns, Normal Computing;
  R1-07 popups; R1-08 brand maps; R1-09/11/12 note edits + build checks; R1-10 coworking dates; R1-13 public map;
  R1-14 ring CCW; R1-15 README phone test; R1-16 near-miss classes; R1-17 route constraints; R1-18 HANDOFF mapping;
  R1-19 marker declutter, tier C hollow; R1-20 unknown normalisation, Synthesia note; R1-01/02 REPORT.md + breach disclosure.

## Status
- [x] Research: CompStak/Empathy/Signal AI own pages confirm (stay high); Simplebet CO 2025-05-22 (stays high);
      Morning Brew/Bombas/accessiBe -> medium; Pumpkin -> low (own site 666 3rd Ave conflict). Built In HQ for 143 slugs
      -> _work/builtin_hq_2026-10-24.csv. Synthesia CO 2025-08-14 245 Fifth current. WFM store coords (3). Amazon/Microsoft Wikipedia counts.
- [x] frontage.py (CSCL side + face test, lot-position frontage); assemble fix_pins rewritten; 43 pin fixes, all pass.
- [x] resolutions.py review-round block; assemble: undated-profile rule, note edits, normalise, hq fields, coworking/retailer fixes.
- [x] router anchor-to-anchor; route constraints (40-75 + 76-150, no CPG), seeded + ILS search; variants recorded.
      Route: 181.3 min, 11:01 (1 over); high+medium 171.8 (10:52).
- [x] near-miss classes; content checks; boundary CCW; map template popups/declutter/diamond stores; maps.py public wording.
- [ ] method_text, xlsx notes, public_map.py (brand mode, footnote, minutes), pin_qa, render.js QA, docs, REPORT, builder response.
