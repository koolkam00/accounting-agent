# Review round 3: builder's working log (kept)

Started 2026-10-24. Findings in `_review/round-3.md` (1 blocker, 2 majors, 6 minors). One line per fix as it lands, so nothing is lost on compaction.

- [ ] R3-01 REPORT.md: Write refused again by the harness (5th time, same message, tried 2026-10-24 at the start of this round); not worked around; full text returned to the orchestrator; numbered assumptions and plan conflicts now also in README (a stranger needs them in the folder)
- [x] R3-02 claims net (code): CLAIM_RE rebuilt (structure/function verb + body word within 3 words, standalone health words, disease words, sales/lift/return/conversion, superlatives incl. standalone best and #1); bare lift only as a noun, prevents only with disease words, convert not after 'a/an'; negation-after ('Incremental sales are not measured'); nutrient list adds electrolytes, vitamins, zero cholesterol. tests/claims/claims-test.js 280/280 (69 claims, 39 plain, 4 nutrient, 168 shipped sentences). Reviewer's r3-claim-card/report now exit 2. Second tick box on tent card and report (DD.confirmList, cfg.confirms)
- [x] R3-03 proposal (code): store name drops a bracket that repeats the street/store number or a 'formerly' note; display_name ('Shown as'); distance column sized to the longest distance (0.8 to 1.45 in, nowrap); parked unused sections (hidden .sec counted for .sec+.sec margins; result depended on previous arrangement by up to 0.1 in); buy-under-timeline built, tried on 39 proposals, never fit, removed with a note; overflow error says by how much, which stores wrap, longest parts; 6 new cases (v5, v6, v1 x 10/12) + refusal case + names test; doc-tests 98/98. Docs still to update
- [ ] R3-04 wide logo fallback to typed name
- [x] R3-05 (code): Ready to print when no error, placeholder, SAMPLE and all ticks; notes under 'Read these notes first:'; swap test adds a non-SAMPLE run that must say Ready to print with the product-line note
- [ ] R3-06 split face QR toward the room
- [x] R3-07 emptyText per picture field (logo, map, office photo); report photos keep 'No photo received'
- [ ] R3-08 tokens.json semantic group, check-tokens aliases
- [ ] R3-09 9 pt / 8.5 pt vs SYSTEM 10 pt floor
