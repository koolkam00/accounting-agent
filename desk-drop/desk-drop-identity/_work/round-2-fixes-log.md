# Review round 2: builder's working log (kept)

Started 2026-10-24. Findings in `_review/round-2.md`. One line per fix as it lands, so nothing is lost on compaction.

- [ ] R2-01 REPORT.md: harness refused the write again (4th time); not worked around; full text returned to the orchestrator; README now has the tool choice and the decisions waiting
- [x] R2-02 report photo dates: placement_photo_date, later_photo_date (printed only when recorded, checked against placed_within_1bd); captions never say "day 1" without a recorded date; evidence page fit; doc-tests +7 (78 pass)
- [x] R2-03 proposal: stores one cell "Name, street" with a # column; new full-width buy arrangements (map left, stores right; price left); every arrangement tried, the biggest map that fits wins, then fewest give-way steps and unwrapped store rows; text tightens before the map shrinks; a compact step; 4 new cases from B data (longest four names with a map drawn by B's own script in a scratch copy; reviewer's four stores) all fit
- [x] R2-04 rename keeps Chrome-saved details: brand-sync.js per-key rule (no mtime gate), details-test.js +4 checks (fails 4 of 9 with the v1.2 file), guide sections 7 and 16
- [x] R2-05 claims: one list in dd-template.js (DD.claimsIn, DD.checkClaims), structure or function wording added, error unless claims_reviewed Y with a reason; nutrient wording warns; tent card uses it; run-all +5, doc-tests +3
- [x] R2-06 two flavors: flavor_name, flavor_name_2, allergen_source_2, allergen_line_verbatim_2, may_contain_verbatim_2; each statement under its flavor name at 14 pt, verbatim-checked; too long refuses with "one card per flavor"; samples SAMPLE-two-flavors, SAMPLE-two-flavors-too-long-must-block
- [x] R2-07 HANDOFF B row closed and updated; SAMPLE standard proposal with B's map; # column; requests to B (pin order, label collisions)
- [x] R2-08 wide logo floor 0.75 in, logo gives way after story, gaps and find line; SAMPLE-logo-wide-full-card (reviewer rv2-caps-logo) keeps 0.75 in and the story
- [x] R2-09 card ID 0.12 in from trim (spec names it as the one exception), room tag 9 pt bold ink
- [x] R2-10 --dd-rule-color (light and both dark blocks, tokens.json dark-mode rule-color), --dd-rule stays the 2 px width; check-tokens.js fails on a name defined twice or used as color and width (proved on the v1.2 file)
- [x] R2-11 office one-pager: "The survey closes on day 5" (template and BLANK sample); doc-tests check
- [x] R2-12 mock roster built from the proposal's own offices (industry, band, planned units), illustrative counts scaled
- [x] R2-13 brand one-pager founding line adds ", before you ship"; doc-tests check
- [x] R2-14 [HEADCOUNT BAND] (report, proposal, samples), placeholder band cells wrap, proposal roster columns widened for [NEIGHBORHOOD], blank card name keeps its yellow mark
- [x] R2-15 brand.json keys: FOUNDER_TITLE, SIGNATURE_LOGO_URL, _readme notes; details.html keeps an empty title; brand-sync treats an empty title as the default
- [x] R2-16 Quick card box at the top of guide section 2; two-flavor and claims steps; trouble rows
- Tests after round 2: bash tests/run-all.sh 47 of 47 (with DD_QR_DECODER); doc-tests 89 of 89; details 9 of 9; swap 8 min 26 s by the model. Rebuilt every PDF with build-pdfs.sh and looked at the changed pages.
