# Identity and collateral (workstream D)

Everything the founder needs to look consistent from the first discovery call to the first campaign report, without a designer: the identity system, the tent card and case label, the discovery, office and brand one-pagers, the proposal with a mock report page, the one-page report, the email signature and the social avatar. Version 1.4, 2026-10-24 (review rounds 1 to 3 answered: `_review/round-1.md`, `round-2.md` and `round-3.md`, "Builder response" at the end of each).

**Why HTML and not Canva or Figma** (the brief prefers those): there is no login for either here, and a Canva copy could not hold the rules that matter most, which are code in these templates: the allergen text locked at 14 pt and checked word for word, the fixed limitations paragraph, the claims check that refuses a card, impossible numbers refused, photo dates checked against the roster, pages that refuse rather than shrink past the type floors. Everything opens and prints from Chrome; a rebuild sheet for Canva or Google Docs is in `USAGE-GUIDE.md` section 15.

**Name and print gate** (from `../desk-drop-legal-pack/01-name-check-log.md`, v0.7, 2026-10-24; short copy `name-check-log.md` v0.6): print run **HOLD**, public launch **HOLD**, private discovery calls **go**. A business already trades as "DeskDrop", and the USPTO refused DESK-DROP as descriptive. The legal pack recommends checking two fallback names by Fri 2026-11-13 and choosing at the attorney hour, Wed 2026-11-18 (derived, founder to confirm). Home and copy-shop test prints are fine. Documents sent one to one are fine. A rename here is one edit to `brand.json` plus one command (see "Rename").

## Start here

1. Read `USAGE-GUIDE.md`. Section 0 says which piece you need when.
2. Open `details.html` in Chrome and fill in your details once (guide section 7): it saves `system/brand.js` and shows your email signature, ready to copy. No terminal needed. Until then your details print yellow and `--final` refuses.
3. Open any template in Google Chrome: `templates/<piece>/<piece>.html`. Fill the boxes on the left; the page updates. Press Print (or Print or save as PDF).
4. To see finished examples first, open the PNGs in `pdf/png/`.

## Files, in the order you will use them

### Your details, prices and the name (edit these)

| File | What it is | How to edit |
| --- | --- | --- |
| `details.html` | **Your details, in Chrome, no terminal**: name, title, phone, email, website, postal address. Shows both email signatures live, with Copy buttons. **Save brand.js**, then move the file into `system/` | Chrome (guide section 7) |
| `brand.json` | The one place the name (`BRAND_NAME`) and tagline live, and the terminal copy of your contact details: `[FOUNDER NAME]`, `FOUNDER_TITLE` (empty prints "Founder"), `[PHONE]`, `[EMAIL]`, `[WEBSITE]`, `[POSTAL ADDRESS]`, and optional `SIGNATURE_LOGO_URL`. Details saved from `details.html` are copied in at every terminal build wherever `brand.json` still has a placeholder, including right after a rename (v1.3) | Text editor, then `bash render/build-pdfs.sh` (or `node render/build-brand.js` and `node render/build-signature.js`) |
| `system/dd-offer.js` | The one place the prices and campaign numbers live ($600 founding for 5 offices, $1,500 standard for 10, $150 extra office, 10% reserve, 30 to 80 units, cancellation terms) | Text editor; change the campaign agreement to match; rebuild |
| `USAGE-GUIDE.md` | Step-by-step guide for every piece, written for a non-designer | Text editor |

### Discovery, weeks 1 to 3

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/discovery-one-pager/discovery-one-pager.html` | The idea in exactly five sentences, no selling | Chrome panel (guide section 8). The template refuses two sentences in a box and warns on selling words |
| `templates/discovery-one-pager/FIELDS.md`, `samples/DEFAULT.json`, `samples/SAMPLE-must-warn.json` | Field rules; the shipped sentences; a sample that proves the checks fire | |
| `pdf/discovery-one-pager-BLANK.pdf` | The page as shipped, your details still yellow | Rebuilt by `build-pdfs.sh` |
| `signature/signature.html`, `signature.txt` | Everyday email signature: name, title, [PHONE] · [EMAIL] · [WEBSITE], [POSTAL ADDRESS] | Generated from `brand.json` (the same signature is on `details.html`). Set up in Gmail: guide section 13 (needs your login) |
| `signature/signature-outreach.html`, `.txt` | The same plus the legal pack's commercial-email line (Footer B), for cold outreach | Generated; the line is read from `../desk-drop-legal-pack/02-email-footer-and-checklist.md` |
| `signature/signature-with-logo.html` | Logo version, only once the wordmark PNG is hosted | Set `SIGNATURE_LOGO_URL` in `brand.json`, rebuild |
| `signature/preview-*.png` | What the signatures look like on desktop, at phone width, and the outreach version | |

### Recruiting offices and selling brands, weeks 3 to 7

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/office-one-pager/office-one-pager.html` | Office one-pager: pitch, what you get and what we ask, never asked, how a drop works, what is in the case, privacy, founding offices, what you sign, with a proposed first-drop week | Chrome panel (guide section 9). All copy is in boxes; `{BRAND_NAME}` prints the name |
| `templates/brand-one-pager/brand-one-pager.html` | Brand one-pager: positioning line, what a campaign includes, price (agreement v0.8 terms), what we count and what we don't (the ladder), the seven-point fit, what you send, what we never promise | Chrome panel (guide section 10). **Roster today** must say only what is true. Fits real-length details (five give-way steps) |
| `templates/proposal/proposal.html` | One-page proposal plus a mock report page: route roster (no company names), the cluster-map workstream's per-brand map and the stores numbered to its pins, specification, price and terms (agreement v0.8, cancel-by date printed), what the brand sends and by when, timeline worked out from the drop date, the report. Up to 12 offices with a map and four stores, tested with the store sets in `tests/documents/cases/` (real names from the cluster map's `retailers.csv`, including three sets inside the cluster, v1.4); a store's name prints without a bracket that repeats its street, and **Shown as** sets a shorter one. Longer names or distances may need shorter wording: the refusal says by how much and which store. The page tries 13 layouts and keeps the biggest map that fits. The mock page shows this proposal's own offices and has nothing yellow once your details are in | Chrome panel (guide section 11), or `node render/render.js proposal data.json out.pdf --final` |
| `templates/*/FIELDS.md` | Every field, its source column (CONTRACTS section 6) and its rule | |
| `templates/*/samples/` | `BLANK-placeholders.json` (empty form) and `SAMPLE-*.json` (test data) per template. `templates/proposal/samples/maps/` holds the cluster-map workstream's SAMPLE brand map, copied 2026-10-24 | Copy one as a start |
| `pdf/office-one-pager-BLANK.pdf`, `pdf/brand-one-pager-BLANK.pdf`, `pdf/proposal-BLANK.pdf`, `pdf/proposal-SAMPLE-founding.pdf`, `pdf/proposal-SAMPLE-standard-10-offices.pdf` | The documents as PDFs | Rebuilt by `build-pdfs.sh` |

### Campaign: kitting, drop day, photos

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/tent-card/tent-card.html` | The 5 x 7 in tent card (landscape faces, tent fold, 7 x 10 in flat on Letter), allergen text locked at 14 pt; optional brand logo; a long ingredient list gets the front face ("this side faces the room"), with "Take one." and the QR on it too when the list leaves room (v1.4); two flavors print each package's statement under its own name (guide section 19); the claims net refuses common health and sales claims, and a tick box asks you to read the sentences yourself (v1.4); a wide logo gives way to the typed name on a full card (v1.4) | Chrome panel (guide section 2), or `render.js tent-card` from JSON (section 3) |
| `templates/tent-card/samples/` | `BLANK-placeholders.json` and SAMPLE cards: basic, 25-word allergen, the round-1 reviewer's maximum card, long and short names, retailer-only, code-only, 5-office batch, 37-, 50- and 74-word ingredient lists (the 50-word one keeps the QR on the room face, v1.4), single-ingredient, wide and compact logos (`logos/`, our own drawings), a full card with a wide logo (the round-2 reviewer's), the round-3 reviewer's ALL-CAPS card whose wide logo gives way to the typed name, two flavors, and two cards that must be refused (over-full; two flavors too long for one card) | Copy one as a start |
| `templates/case-label/case-label.html` | Case label, 8.5 x 5.5 in, two per Letter sheet: office, brand, units, [PHONE]. The panel edits every label (pick, add, remove) | Chrome panel (guide section 5) |
| `specs/tent-card-spec.pdf`, `specs/case-label-spec.pdf` | Print specs: size, bleed, safe area, stock, fold, every type size, give-way order, placement and photo rules | Source `specs/*.html`; rebuild |
| `pdf/tent-card-*.pdf`, `pdf/case-label-*.pdf` and their PNGs | Blank and SAMPLE cards and labels: home print, print-shop bleed file, a 5-office batch, the 25-word allergen test, a two-flavor card | Rebuilt. Never place a SAMPLE card |

### Reporting, by T plus 7

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/report/report.html` | The one-page report: header, the ladder (delivered, placed, depleted, responded, scanned, purchased, incremental: not measured; Delivered is the drop-day handover, Placed shows the Gate 2 unit share), roster, two photos per office (a strip for six to twelve offices), survey with counts beside every share and three verbatim comments, engagement, learned, recommendation, the fixed limitations paragraph; an evidence page with every photo | Chrome panel (guide section 12), or `node render/render.js report report.json report.pdf --final` (photo paths relative to the JSON) |
| `templates/report/samples/` | `BLANK-placeholders.json`, `SAMPLE-5-offices.json`, `SAMPLE-10-offices-long-comments.json` (the brief's test; both SAMPLEs now record photo dates, except one office each, which shows "date not recorded"), `photos/` (our own simulated pantry photos, SAMPLE) | |
| `pdf/report-BLANK.pdf`, `pdf/report-SAMPLE-5-offices.pdf`, `pdf/report-SAMPLE-10-offices-long-comments.pdf` | The report as PDFs | Rebuilt |
| `specs/documents-spec.pdf` | Spec for every document, the signature and the avatar: page, grid, type floors, marks, give-way orders, fixed text, sizes | Source `specs/documents-spec.html`; rebuild |

### Logo, colors, type, avatar (also for the website)

| File | What it is | How to edit |
| --- | --- | --- |
| `wordmark/*.svg` | `wordmark-light.svg` (on white), `wordmark-dark.svg` (on dark), `wordmark-mono-ink.svg`, `wordmark-mono-white.svg`, `wordmark-stacked-*.svg`, `symbol-*.svg` | Generated from `brand.json`. Never hand-edit |
| `wordmark/png/` | 50 PNGs of the above at 600 to 2400 px, transparent, on white or on ink | Generated |
| `wordmark/wordmark-metrics.json` | Aspect ratio and cap-height fractions; says when a long name needs the stacked lockup | Generated |
| `avatar/avatar-cobalt-*.png` (default), `avatar-paper-*.png`, `avatar-ink-*.png`, `avatar-*.svg` | Social avatar: the symbol alone, at 1024, 512, 400, 320, 160, 80 and 40 px | Generated by `node render/build-avatar.js`. Upload: guide section 14 (needs your logins; public profiles wait for the name decision) |
| `avatar/test-sheet.png` | Every avatar at 40 and 24 px, circle and square, light and dark backgrounds | |
| `tokens/tokens.css`, `tokens/tokens.json` | Colors, type families and weights, spacing, radii (the website imports `tokens.css`). Since v1.4 `tokens.json` also has the light-mode `semantic` roles (`--dd-bg`, `--dd-text`, `--dd-rule-color` and five more) | Edit both, then `node tests/check-tokens.js` (it checks the aliases and both dark blocks too) |
| `fonts/` | Bricolage Grotesque and Atkinson Hyperlegible Next (Google Fonts, SIL Open Font License, licenses included); `fonts.css` (print), `fonts-variable.css` | Do not edit |

### For whoever extends the system

| File | What it is |
| --- | --- |
| `SYSTEM.md` | The rules: sources of truth, color, type, spacing, wordmark, grids, components, template mechanics, render pipeline, documents, screen pieces, versions |
| `HANDOFF.md` | What this folder takes from and gives to the website, outreach and operations workstreams, with paths and field names |
| `REPORT.md` | Report back (CONTRACTS section 1): deliverables, tool choice and why, numbered assumptions, changelog by round, tests and what failed first, blocking questions with recommended defaults. **Still pending:** the harness refused the builder's write a fifth time in review round 3 ("Subagents should return findings as text, not write report files"), and the builder did not work around it; the full v1.4 text is in the builder's returned message for the orchestrator to save here. Meanwhile everything a stranger needs from it is in this folder: the tool choice at the top of this file, the numbered assumptions and the conflicts with plan.md under "Assumptions" below, the open questions under "Decisions waiting on you", test results in `tests/README.md`, and the per-finding answers in `_review/` |
| `_review/round-1.md`, `round-2.md`, `round-3.md` | The independent reviews, rounds 1 to 3, each with the builder's response per finding at the end. `_review/work/`, `work-r2/` and `work-r3/` are the reviewers' own scratch |
| `system/dd-template.js`, `dd-print.css` | Template runtime: panel, placeholders, SAMPLE banner, table and picture fields, status |
| `system/dd-docs.css`, `dd-docs.js` | Letter documents: header, footer, image slot, card drawing, page fitting, claims check |
| `system/dd-report.js` | The report renderer and the fixed limitations paragraph (also draws the proposal's mock page) |
| `system/dd-dates.js` | CONTRACTS section 3 calendar: business days, holidays to 2027-09-30, blackouts, T offsets |
| `system/dd-offer.js` | Prices and campaign numbers |
| `system/brand.js` | Generated from `brand.json` (Chrome cannot read JSON from a file), or saved by `details.html` |
| `system/dd-signature.js` | The email signature builder, shared by `render/build-signature.js` and `details.html` |
| `system/signature-footer.js` | Generated: the legal pack's Footer B, for `details.html` |
| `system/vendor/` | qrcode-generator 2.0.4 and opentype.js 1.3.4, MIT, with licenses |
| `render/render.js` | JSON to print-ready PDF for any template (`--final`, `--json`, `--mode pro`, `--png`) |
| `render/render-page.js` | A static page (spec sheets) to PDF |
| `render/build-brand.js`, `build-signature.js`, `build-avatar.js`, `build-pdfs.sh` | Rebuild the wordmark, signature, avatar, or everything |
| `render/brand-sync.js` | Copies details saved from `details.html` into `brand.json` at every terminal build, key by key, so a rename keeps them (v1.3) |
| `tests/` | Every test and its outputs; `tests/README.md` has the results and what failed first. `bash tests/run-all.sh`. New in v1.2: `tests/documents/cases/` (stress inputs, several from the reviewers' files), `tests/panel/` (record picker), `tests/details/` (the Chrome-only details path, and since v1.3 a rename right after it), `tests/proposal-map/` (our own SAMPLE map; since v1.3 also B's SAMPLE map and a map drawn by B's own script with the four longest store names in B's file). New in v1.4: `tests/claims/claims-test.js` (every claim phrase and plain phrase with its expected result, and every shipped sentence) |
| `package.json` | Lists Playwright for the terminal commands |
| `_work/` | Working logs (`decisions-log.md`, `round-2-fixes-log.md`, `round-3-fixes-log.md`) and sources (`research/sources.md`). Kept, not needed day to day |

## Assumptions (numbered; where the brief and plan were silent, D decided)

1. **Tool:** editable HTML templates opened in Chrome, with an optional Node and Playwright command for batches, instead of Canva or Figma (no logins here, and the rules below must be code). A rebuild sheet for Canva or Google Docs is in guide section 15.
2. **Card shape:** landscape faces, 7 in wide and 5 in tall, tent fold, 7 x 10 in flat on one Letter sheet, printed at home or at a copy shop. Both faces carry the same content (the back turned 180°). Online table tents are vertical only and sold from 10 per design (Vistaprint page, opened 2026-10-24), which does not suit one design per office.
3. **Allergen lock:** 14 pt semibold, pure black, inside a 2 px ink border. The size came from the close-photo sweep (a 26 mm-equivalent phone lens at 60 cm: 11 pt failed at 1,280 px, 12 pt was marginal, 14 pt passed with margin). Everything else gives way; a card that still cannot fit is refused, never shrunk.
4. **Where a package declares allergens** is a field of its own (`allergen_source`: a "Contains" statement, the whole ingredient list, or a single-ingredient name), with `may_contain_verbatim` beside `allergen_line_verbatim`. There is no "no allergens" option: nobody judges an ingredient list by eye.
5. **A long ingredient list** moves, whole, to the front face, marked "this side faces the room"; since v1.4 that face keeps "Take one." and the QR when the list leaves room, and flags the office when it does not.
6. **Two flavors:** one card when both statements fit at 14 pt, each under its own flavor's name; otherwise one card per flavor, same office ID and QR.
7. **Claims** in the founder's or brand's text are an error, not a note, in every render; the founder can override only with `claims_reviewed` Y and a written reason. The list is a net, not a review (v1.4): the card and the report each carry a tick box for the founder's own read. Nutrient wording ("10g protein") warns, per CONTRACTS section 4.
8. **Brand logo:** optional. A wide logo replaces the typed name and stops at 0.75 in; on a card that still does not fit, it gives way to the typed name (v1.4). A compact logo sits beside the name and stops at 0.55 in.
9. **Card exceptions to the type floors:** the card ID sits 0.12 in from the trim (for kitting), the allergen label line is 9 pt bold and "Brought to you by" 8.5 pt (labels, read in the close-photo test). Every sentence an employee reads is 10 pt or more.
10. **Fonts:** Bricolage Grotesque (display; its width axis carries long names) and Atkinson Hyperlegible Next (text and allergen line), both SIL Open Font License on Google Fonts, embedded as static instances for print.
11. **The name and its symbol:** the wordmark is the name drawn from the font by a script, plus a name-independent symbol (a box on a shelf), which is also the avatar, so a rename leaves the avatar as it is.
12. **The report** is the plan's one page plus an evidence page with every photo at a readable size (an addition). Delivered is the drop-day handover only; top-ups are shown beside it, never added; Placed prints the Gate 2 unit share.
13. **Survey numbers** are typed as counts; the report computes every share and prints the count and denominator beside it.
14. **Comments** print word for word, except a person's name, which becomes "[name removed]" (legal pack file 13, rule D10), and a cut, which is marked "[...]".
15. **Photo dates** print only when recorded; the report never works one out from the drop date, and refuses a date that contradicts "placed within one business day".
16. **The founding lock** "locked for that brand's next two campaigns" is read, as the campaign agreement v0.8 sets it, as $120 per office for up to 10 offices, extra offices at $150.
17. **Standard payment:** 50% at signature and 50% on the placement confirmation, an email by T+1 listing each placed office with its photo; an office not placed comes off the invoice (agreement v0.8).
18. **Proposal privacy:** no company names and no office pins on the map before the brand signs; offices appear by neighborhood, industry and headcount band.
19. **Proposal size:** at most 12 offices on one page (tested); 13 or more is refused, and the route splits into two campaigns.
20. **Proposal store names** print without a trailing bracket that repeats the street or a store number, or a "formerly" note (v1.4); `display_name` sets another.
21. **The proposal's mock page** uses this proposal's own route; only the outcome counts are illustrative, scaled from the plan's appendix M pattern, under "Illustrative placeholders, not results".
22. **Dates** follow CONTRACTS section 3 (business days, federal holidays, blackouts, T offsets); the holiday table runs to 2027-09-30, and a later window warns.
23. **The discovery one-pager** is exactly five sentences, checked in code, and warns on selling words.
24. **Signature:** text-only by default (no image hosting needed); a logo version only once the wordmark PNG is on a public address. The outreach version carries the legal pack's Footer B word for word.
25. **Founder details** live in `brand.json`, and `details.html` saves the same details from Chrome into `system/brand.js`; each terminal build copies them across key by key.
26. **SAMPLE marking:** every invented name, ID and free-text value starts with SAMPLE; generic category words (a neighborhood, an industry) do not, and every page built on samples carries the SAMPLE banner.
27. **Printing:** the print run waits for the legal pack's name gate (HOLD today); home and copy-shop test prints are fine. Print costs stay the plan's ($1 to $2 a card in runs of 20); copy-shop options and prices are unverified, founder to confirm.
28. **The swap-test time** (8 min 35 s for a first card) is a stated model, not a stopwatch on a person; the first real card should be timed.

**Where this folder departs from plan.md** (CONTRACTS asks D to list these):
- The office pitch the plan fixes says "you send one photo", and the office one-pager prints it as fixed copy, while the plan's own office commitments, the participation agreement (legal file 03) and the report ask for two (placement and day 3 or 5). The one-pager's "What we ask" says two. Decision 5 below.
- The plan's "first drop within four weeks of signing" is not printed: legal file 03 drops it, so the one-pager names a proposed drop week instead.
- Campaign zero and Gate 3 dates follow CONTRACTS section 3 (drop Tue 2027-01-12, Gate 3 Fri 2027-03-12), not the plan's weeks 7 to 9 and week 16.

## Decisions waiting on you

Each has a recommended default, so nothing here stops discovery calls.

1. **Keep the working name, or pick a fallback?** Blocks any print run and public profile. Default: follow the legal pack (check two coined fallbacks by Fri 2026-11-13, choose at the attorney hour Wed 2026-11-18). A rename here is one edit and one command, and your saved details survive it.
2. **Which phone and postal address go on everything?** Default: a business mobile line and a USPS post office box (or a registered private mailbox) near the cluster, entered once in `details.html`; the website stays off until it is public.
3. **A map for each brand's proposal.** Default: list the brand's evidenced stores in the proposal's order and ask the cluster-map workstream (or run its script) for that brand's map with the pins in the same order.
4. **Two flavors: one card or one per flavor?** Default: one card when both statements fit at 14 pt; one card per flavor when the card says they do not.
5. **The office pitch says "one photo"; offices commit to two.** Default: change the pitch to "on the shelf the day it arrives, two photos, and three questions for your team" (one edit to the **Lead** box, or to the template's default), once you confirm the plan's fixed line may change. Until then the one-pager prints the plan's line and lists both photos under "What we ask".

## Commands (optional; Chrome alone is enough for everything but a rename)

Install once: Node 18 or newer (nodejs.org), then in this folder `npm install` and `npx playwright install chromium`. Both free. For the page PNGs, poppler (`pdftoppm`).

```bash
node render/render.js tent-card cards.json cards.pdf --final       # one card per office
node render/render.js case-label labels.json labels.pdf --final    # two labels per sheet
node render/render.js proposal proposal.json proposal.pdf --final  # proposal plus mock page
node render/render.js report report.json report.pdf --final        # report plus evidence page
bash render/build-pdfs.sh                                          # rebuild everything
bash tests/run-all.sh                                              # run every test
```

Exit codes: 0 written, 1 usage, 2 the template refused (does not fit, impossible numbers, bad date, a claim, photo dates that contradict the roster), 3 `--final` found placeholders, SAMPLE values or unfilled `brand.json` contacts.

## Rename

Edit `BRAND_NAME` in `brand.json`, run `bash render/build-pdfs.sh` (a rename needs the terminal once: the logo files are drawn from the font by a script; details you saved in `details.html` are kept), then find-and-replace the old name in the `.md` files here and re-copy the signature into Gmail. Nothing else holds the name: the documents' copy uses `{BRAND_NAME}`. Details: `USAGE-GUIDE.md` section 16. Tested with "Dropp" and "Desk Drop Collective" (`tests/name-length/`, `tests/rename-documents/`), and with "Shelfwise" right after a Chrome-only save of your details (`tests/details/details-test.js`).

## Ordering a print run

**Not yet: the legal pack's gate is HOLD.** When `../desk-drop-legal-pack/01-name-check-log.md` clears the name, rerun its day-before-printing checks, then:

1. Make the card PDF with `--final`. Each office's card is its own design (its own QR), so print the one-card-per-page Letter PDF.
2. At a copy shop (for example a FedEx Office or Staples counter; options and prices unverified, founder to confirm): 8.5 x 11 in, white matte cover stock 80 to 110 lb, single-sided, 100% scale, no "fit to page". Cut and score yourself, or ask for a quote to cut to 7 x 10 in and score at 5 in.
3. A shop that wants bleed gets the `--mode pro` file (7.25 x 10.25 in, 0.125 in bleed, trim 7 x 10 in, score across the middle).
4. Online table tents (for example Vistaprint: 5 x 7 in vertical only, from 10 per design; page opened 2026-10-24) do not fit one design per office.
5. Case labels: Avery 5126-size half sheets, printed at home. Documents are sent as PDFs, not printed.

The plan budgets about $1 to $2 a card in runs of 20. No spending without the founder's written yes: get the quote, then decide. Full steps: `USAGE-GUIDE.md` section 17.
