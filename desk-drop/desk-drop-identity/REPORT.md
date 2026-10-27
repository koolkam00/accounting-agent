# Report back: workstream D, identity and collateral (v1.4, 2026-10-24)

Version 1.4, after three independent review rounds (`_review/round-1.md` to `round-3.md`, builder response at the end of each). Paths are relative to `desk-drop/desk-drop-identity/`. Nothing was sent, posted, bought, signed up for or committed.

## 1. Deliverables
- Name and details: `brand.json` (BRAND_NAME, TAGLINE, contact placeholders), `details.html` (fill details in Chrome; saves `system/brand.js`), `system/dd-offer.js` (prices).
- Wordmark: `wordmark/wordmark-light.svg`, `wordmark-dark.svg`, mono, stacked and symbol SVGs; `wordmark/png/` (50 PNGs); `wordmark/wordmark-metrics.json`.
- Color and type specs: `SYSTEM.md`; `tokens/tokens.css` and `tokens/tokens.json` (with light-mode semantic roles since v1.4); `fonts/` (Bricolage Grotesque, Atkinson Hyperlegible Next, OFL licenses).
- Usage guide: `USAGE-GUIDE.md` (sections 0 to 19).
- Tent card: `templates/tent-card/tent-card.html`, `FIELDS.md`, `samples/`; `pdf/tent-card-*.pdf` and PNGs; `specs/tent-card-spec.pdf`.
- Case label: `templates/case-label/case-label.html`, `FIELDS.md`; `pdf/case-label-*.pdf`; `specs/case-label-spec.pdf`.
- Discovery one-pager: `templates/discovery-one-pager/`; `pdf/discovery-one-pager-BLANK.pdf`.
- Office one-pager: `templates/office-one-pager/`; `pdf/office-one-pager-BLANK.pdf`.
- Brand one-pager: `templates/brand-one-pager/`; `pdf/brand-one-pager-BLANK.pdf`.
- Proposal with mock report page: `templates/proposal/`; `pdf/proposal-BLANK.pdf`, `proposal-SAMPLE-founding.pdf`, `proposal-SAMPLE-standard-10-offices.pdf`.
- Report: `templates/report/`; `pdf/report-BLANK.pdf`, `report-SAMPLE-5-offices.pdf`, `report-SAMPLE-10-offices-long-comments.pdf`.
- Documents spec: `specs/documents-spec.pdf`.
- Email signature: `signature/signature.html` and `.txt`, `signature-outreach.html` and `.txt` (legal pack Footer B), `signature-with-logo.html`, previews.
- Avatar: `avatar/avatar-cobalt-*.png` (default), paper and ink variants, SVGs, `avatar/test-sheet.png`.
- Render and build: `render/render.js`, `render-page.js`, `build-brand.js`, `build-signature.js`, `build-avatar.js`, `brand-sync.js`, `build-pdfs.sh`.
- Tests: `tests/run-all.sh` and `tests/README.md` (results and what failed first).
- `README.md` (every file, how to edit, print-run steps, assumptions, decisions), `HANDOFF.md`, this file.

## 2. Tool choice and why
The templates are editable HTML, opened and printed from Google Chrome, with an optional Node and Playwright command for batches. The brief prefers Canva or Figma, but no login for either exists here. A Canva copy also could not hold the rules that matter most, which are code in these templates:
- the allergen text locked at 14 pt and checked word for word;
- the fixed limitations paragraph;
- the claims check;
- impossible numbers refused;
- photo dates checked against the roster;
- pages that refuse rather than shrink below the type floors.

Everything else works from Chrome alone, including the founder's details (`details.html`). A rename needs the terminal once. A rebuild sheet for Canva or Google Docs is in USAGE-GUIDE section 15. Free tools only.

## 3. Numbered assumptions
1. Tool: HTML templates in Chrome, plus optional Node and Playwright (section 2).
2. Card shape: landscape faces, 7 in wide by 5 in tall, tent fold, 7 x 10 in flat on one Letter sheet, printed at home or at a copy shop. Both faces carry the same content.
   - Online table tents do not fit one design per office: they are vertical only, sold from 10 per design (Vistaprint page, opened 2026-10-24).
3. Allergen lock: 14 pt semibold, pure black, in a 2 px ink border.
   - From the close-photo sweep: a 26 mm-equivalent lens at 60 cm; 11 pt failed at 1,280 px, 12 pt was marginal, 14 pt passed with margin.
   - Everything else gives way; a card that still cannot fit is refused.
4. `allergen_source` (Contains statement, whole ingredient list, single-ingredient name) and `may_contain_verbatim` sit beside `allergen_line_verbatim`. There is no "no allergens" option.
5. A long ingredient list moves, whole, to the front face, marked "this side faces the room". Since v1.4 that face keeps "Take one." and the QR when the list leaves room, and the office is flagged when it does not.
6. Two flavors: one card when both statements fit at 14 pt, each under its own flavor's name; otherwise one card per flavor.
7. Claims are an error in every render. The only override is `claims_reviewed` Y with a written reason.
   - The list is a net, not a review: the card and the report each carry a tick box for the founder's own read.
   - Nutrient wording warns (CONTRACTS section 4).
8. Brand logo: optional.
   - A wide logo replaces the typed name and stops at 0.75 in; on a full card it gives way to the typed name (v1.4).
   - A compact logo sits beside the name and stops at 0.55 in.
9. Card exceptions to the type floors: the card ID sits 0.12 in from the trim, the allergen label line is 9 pt bold, and "Brought to you by" is 8.5 pt. Every sentence an employee reads is 10 pt or more.
10. Fonts: Bricolage Grotesque and Atkinson Hyperlegible Next, both SIL Open Font License on Google Fonts, embedded as static instances for print.
11. The wordmark is the name drawn from the font, plus a name-independent symbol (a box on a shelf) that is also the avatar.
12. Report: the plan's one page plus an evidence page with every photo.
    - Delivered is the drop-day handover only; top-ups are shown beside it, never added.
    - Placed prints the Gate 2 unit share.
13. Survey numbers are typed as counts; every share is computed and printed beside its count and denominator.
14. Comments print word for word, except a person's name, which becomes "[name removed]" (legal file 13, D10), and a cut, which is marked "[...]".
15. Photo dates print only when recorded, never worked out from the drop date, and are refused if they contradict "placed within one business day".
16. The founding lock ("locked for the next two campaigns") is read as campaign agreement v0.8 sets it: $120 per office for up to 10 offices, extras at $150.
17. Standard payment: 50% at signature, 50% on the placement confirmation email by T+1. An office not placed comes off the invoice.
18. Proposal privacy: no company names and no office pins before the brand signs.
19. At most 12 offices per proposal (tested); 13 or more is refused.
20. Proposal store names print without a trailing bracket that repeats the street or a store number, or a "formerly" note (v1.4); `display_name` overrides.
21. The proposal's mock page uses the proposal's own route. Only the outcome counts are illustrative, scaled from plan appendix M, under "Illustrative placeholders, not results".
22. Dates follow CONTRACTS section 3. The holiday table runs to 2027-09-30, and a later window warns.
23. The discovery one-pager is exactly five sentences, checked in code, and warns on selling words.
24. Signature: text-only by default. A logo version only once the PNG is hosted. The outreach version carries Footer B word for word.
25. Founder details live in `brand.json`. `details.html` saves the same details to `system/brand.js`, and each terminal build copies them across key by key.
26. SAMPLE marking: every invented name, ID and free-text value starts with SAMPLE. Generic category words do not. Pages built on samples carry the banner.
27. The print run waits for the legal pack's name gate (HOLD). Print costs stay the plan's ($1 to $2 a card in runs of 20). Copy-shop options and prices are unverified, founder to confirm.
28. The swap-test time (8 min 35 s) is a stated model, not a stopwatch on a person.

### Conflicts with plan.md and CONTRACTS
- **Photos:** the plan's fixed office pitch says "you send one photo", while the plan's office commitments and legal file 03 ask for two. The one-pager prints the fixed line and lists both photos under "What we ask". This is question 5 below.
- **First drop:** the plan's "first drop within four weeks of signing" is not printed. Legal file 03 drops it, so the one-pager names a proposed drop week instead.
- **Dates:** campaign zero and Gate 3 follow CONTRACTS section 3 (drop Tue 2027-01-12, Gate 3 Fri 2027-03-12).
- **CONTRACTS deviations:** these are listed in HANDOFF.md. They cover the extra card columns (allergen_source, may_contain_verbatim, brand_logo, code_site, the two-flavor columns, claims_reviewed) and the report's per-office columns. They also cover `map_number` and `display_name` in the proposal, slot placeholders, SAMPLE marking for generic words, and `system/brand.js` as a second home for contacts.

## 4. Changelog
- **Part 1, round 0:** decisions:
  - landscape tent card;
  - the name in `brand.json`;
  - wordmark plus a symbol;
  - Bricolage plus Atkinson;
  - JSON-driven HTML templates with a render script;
  - the allergen block locked;
  - no bleed at home.
- **Part 1, round 1:** first tent card draft. Found:
  - a bad "Tell us what you / think" break;
  - a long name blocked the card;
  - the QR shrank before the spacing did;
  - the product line never gave way;
  - the thin cobalt rule was invisible in the wide photo.
- **Part 1, round 2:**
  - reordered the give-way;
  - cobalt band from 0.07 to 0.12 in;
  - wide and close photo simulations;
  - the size sweep locked 14 pt.
- **Part 1, round 3:**
  - the Vistaprint check kept the card landscape;
  - the allergen lock and a verbatim check enforced in code;
  - case label fixes;
  - wordmark sized by cap height;
  - QR decode test.
- **Part 1, round 4 (food-safety pass):**
  - the built-in default is the blank form, not an unmarked sample;
  - added `allergen_source` and the ingredient face;
  - plain panel hints.
- **Part 1, round 5 (print-shop pass):**
  - static font instances instead of Type 3;
  - fonts load before fitting;
  - correct page size for the pro file;
  - 25 of 25 tests.
- **Part 2, rounds 1 to 2:** the one-pagers, proposal and report drafted and fitted:
  - the report's 300 px overflow fixed;
  - the proposal moved to two columns;
  - the office one-pager cut by 245 px and the brand one-pager by 210 px;
  - a grid margin bug fixed;
  - contact placeholders now counted by `--final`.
- **Part 2, round 3:**
  - signature, avatar (cobalt default), documents spec, guide;
  - swap test 8 min 24 s, then 7 min 27 s after guide fixes;
  - "gone" replaced by the ladder word "depleted".
- **Part 2, round 4:**
  - integration with B (landscape map request, no office pins);
  - legal file 13 rule D10;
  - C has no provisional system, so D's system stands.
- **Review round 1 (v1.2, 18 findings), fixed:**
  - brand one-pager with real details;
  - standard proposal with a map;
  - report photos on page 1 and a photo strip;
  - Delivered as the handover and the Gate 2 share;
  - limitations sentence;
  - mock page without yellow;
  - payment and lock terms per agreement v0.8;
  - cancel-by date printed;
  - the office promise;
  - split card front face;
  - logo slot;
  - name give-way order;
  - "Nowhere" option removed;
  - case label record picker;
  - Chrome-only details (`details.html`);
  - photo guidance.
- **Review round 2 (v1.3, 16 findings, 15 fixed):**
  - recorded photo dates;
  - real store names in the proposal;
  - a rename keeps Chrome-saved details;
  - one blocking claims list;
  - two flavors;
  - B's map and pin numbers;
  - wide-logo floor;
  - card ID margin;
  - `--dd-rule-color`;
  - survey day;
  - the mock roster follows the route;
  - "before you ship";
  - blank polish;
  - `brand.json` keys;
  - Quick card.
  REPORT.md was refused by the harness.
- **Review round 3 (v1.4, 9 findings, 8 fixed):**
  - a wider claims net plus tick boxes;
  - the proposal fits the cluster's own stores (bracket trim, `display_name`, a sized distance column, a fix for hidden-section spacing, a refusal that says what to shorten);
  - a wide logo gives way to the typed name;
  - "Ready to print" with notes listed under it;
  - a split card keeps the QR toward the room or flags it;
  - per-field empty-picture text;
  - semantic roles in `tokens.json` with alias checks;
  - type-floor exceptions named;
  - spec pages refuse to clip.
  REPORT.md was refused a fifth time; this text is returned for the orchestrator.

## 5. Tests run, and what failed before the fix
Suite: `bash tests/run-all.sh`, 59 of 59 pass. The parts:
- `tests/documents/doc-tests.js`: 98 of 98;
- `tests/claims/claims-test.js`: 286 of 286;
- `tests/details/details-test.js`: 9 of 9;
- swap test: 8 min 35 s by the model.

Full table in `tests/README.md`. The main tests:
- **25-word allergen statement plus a "may contain" line:** passes at 14 pt on both faces.
  - Before: the QR shrank before the spacing did; the name shrank before the product line dropped.
- **Wide pantry photo and 120 px downscale:** every name is identifiable, including a 33-character name, the logos and the wide logo that gives way to the type.
  - Before: the simulated packages were drawn too big; the cobalt rule was too thin.
- **Close photo at arm's length:** legible at 4,032 and 2,048 px, readable zoomed at 1,280 px. The QR decodes at 4,032 and 2,048 px.
- **Report for ten offices with long comments, marked SAMPLE:** one page with both photo rows at 8.25 pt. Harder fills move the photos to page 2 and keep the count.
  - Before: a 300 px overflow, quiet false numbers on the blank report, top-ups added to Delivered, invented photo dates.
- **Swap test from the guide alone:** 8 min 35 s for the first card, about 2 min for each next office. A real-value card reaches "Ready to print" with its notes.
  - Before: the guide did not say Load JSON unticks the box; "Ready to print" never showed when a permanent note was present.
- **Fonts:** Google Fonts, OFL files identical to upstream, CID TrueType embedded.
- **Rename:** "Dropp", "Desk Drop Collective", and "Shelfwise" right after a Chrome save. No hard-coded name.
  - Before: spec footers held the name; a rename wiped details saved in Chrome.
- **Claims:**
  - The CONTRACTS examples, FDA's structure or function examples and plain sales sentences are refused. Ordinary copy and every shipped sentence pass.
  - Before: the v1.3 list caught 3 of 32 claims and refused "Lift the lid".
  - Words in shipped PDFs: none.
- **Signature:** works at 600 and 360 px and as plain text, with [PHONE], [WEBSITE] and [POSTAL ADDRESS], and Footer B word for word.
- **Avatar:** legible at 40 px. Cobalt is the default because the ink variant vanishes on dark backgrounds.
- **Print specs:** complete. The specs now refuse to clip; this round's first edits clipped two pages, and they were shortened.
- **Tokens:** CSS and JSON agree, including the semantic roles and dark blocks. Contrast meets WCAG 2.2 AA.
  - Before: the same name was used for a color and a width; the aliases were missing from the JSON.
- **Proposal:** up to 12 offices with a map and four real stores from B's file, including three sets inside the cluster.
  - Before: 0.22 in over, then 0.02 to 0.09 in over; the layout depended on the arrangement tried before.
- **Legal versions:** files 01, 02, 03, 10 and 13 are pinned in HANDOFF. A new version fails the suite until D rechecks it.

## 6. Blocking questions, each with a recommended default
1. **Keep the working name, or a fallback?** This blocks any print run and public profile. Default: follow the legal pack. Check two coined fallbacks by Fri 2026-11-13 and choose at the attorney hour, Wed 2026-11-18 (derived, founder to confirm). A rename is one edit and one command.
2. **Which phone and postal address go on everything?** Default: a business mobile line and a USPS post office box (or a registered private mailbox) near the cluster, entered once in `details.html`.
3. **A map for each brand's proposal.** Default: list the brand's evidenced stores in the proposal's order and ask B for that brand's map with the pins in the same order, or run B's script.
4. **Two flavors: one card or two?** Default: one card when both statements fit at 14 pt; one card per flavor when the card says they do not.
5. **The office pitch says "one photo", but offices commit to two.** Default: change the pitch to "on the shelf the day it arrives, two photos, and three questions for your team", once the founder confirms that the plan's fixed line may change.
