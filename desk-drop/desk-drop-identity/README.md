# Identity and collateral (workstream D)

Everything the founder needs to look consistent from the first discovery call to the first campaign report, without a designer: the identity system, the tent card and case label, the discovery, office and brand one-pagers, the proposal with a mock report page, the one-page report, the email signature and the social avatar. Version 1.3, 2026-10-24 (review rounds 1 and 2 answered: `_review/round-1.md` and `_review/round-2.md`, "Builder response" at the end of each).

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
| `templates/proposal/proposal.html` | One-page proposal plus a mock report page: route roster (no company names), the cluster-map workstream's per-brand map and the stores numbered to its pins, specification, price and terms (agreement v0.8, cancel-by date printed), what the brand sends and by when, timeline worked out from the drop date, the report. Up to 12 offices with a map and four stores, tested with real store names; the page tries 13 layouts and keeps the biggest map that fits. The mock page shows this proposal's own offices and has nothing yellow once your details are in | Chrome panel (guide section 11), or `node render/render.js proposal data.json out.pdf --final` |
| `templates/*/FIELDS.md` | Every field, its source column (CONTRACTS section 6) and its rule | |
| `templates/*/samples/` | `BLANK-placeholders.json` (empty form) and `SAMPLE-*.json` (test data) per template. `templates/proposal/samples/maps/` holds the cluster-map workstream's SAMPLE brand map, copied 2026-10-24 | Copy one as a start |
| `pdf/office-one-pager-BLANK.pdf`, `pdf/brand-one-pager-BLANK.pdf`, `pdf/proposal-BLANK.pdf`, `pdf/proposal-SAMPLE-founding.pdf`, `pdf/proposal-SAMPLE-standard-10-offices.pdf` | The documents as PDFs | Rebuilt by `build-pdfs.sh` |

### Campaign: kitting, drop day, photos

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/tent-card/tent-card.html` | The 5 x 7 in tent card (landscape faces, tent fold, 7 x 10 in flat on Letter), allergen text locked at 14 pt; optional brand logo; a long ingredient list gets the front face ("this side faces the room"); two flavors print each package's statement under its own name (guide section 19); a claim in the sentences refuses the card | Chrome panel (guide section 2), or `render.js tent-card` from JSON (section 3) |
| `templates/tent-card/samples/` | `BLANK-placeholders.json` and SAMPLE cards: basic, 25-word allergen, the round-1 reviewer's maximum card, long and short names, retailer-only, code-only, 5-office batch, 37- and 74-word ingredient lists, single-ingredient, wide and compact logos (`logos/`, our own drawings), a full card with a wide logo (the round-2 reviewer's), two flavors, and two cards that must be refused (over-full; two flavors too long for one card) | Copy one as a start |
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
| `tokens/tokens.css`, `tokens/tokens.json` | Colors, type families and weights, spacing, radii (the website imports `tokens.css`) | Edit both, then `node tests/check-tokens.js` |
| `fonts/` | Bricolage Grotesque and Atkinson Hyperlegible Next (Google Fonts, SIL Open Font License, licenses included); `fonts.css` (print), `fonts-variable.css` | Do not edit |

### For whoever extends the system

| File | What it is |
| --- | --- |
| `SYSTEM.md` | The rules: sources of truth, color, type, spacing, wordmark, grids, components, template mechanics, render pipeline, documents, screen pieces, versions |
| `HANDOFF.md` | What this folder takes from and gives to the website, outreach and operations workstreams, with paths and field names |
| `REPORT.md` | Report back (CONTRACTS section 1): deliverables, tool choice and why, numbered assumptions, changelog by round, tests and what failed first, blocking questions with recommended defaults. **Still pending:** the harness refused the builder's write again in review round 2 ("subagents should return findings as text"), and the builder did not work around it; the full v1.3 text is in the builder's returned message for the orchestrator to save here. Meanwhile the tool choice is at the top of this file, the open questions are under "Decisions waiting on you" below, test results are in `tests/README.md`, and the per-finding answers are in `_review/` |
| `_review/round-1.md`, `_review/round-2.md` | The independent reviews, rounds 1 and 2, each with the builder's response per finding at the end. `_review/work/` and `_review/work-r2/` are the reviewers' own scratch |
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
| `tests/` | Every test and its outputs; `tests/README.md` has the results and what failed first. `bash tests/run-all.sh`. New in v1.2: `tests/documents/cases/` (stress inputs, several from the reviewers' files), `tests/panel/` (record picker), `tests/details/` (the Chrome-only details path, and since v1.3 a rename right after it), `tests/proposal-map/` (our own SAMPLE map; since v1.3 also B's SAMPLE map and a map drawn by B's own script with the four longest store names in B's file) |
| `package.json` | Lists Playwright for the terminal commands |
| `_work/` | Working log (`decisions-log.md`) and sources (`research/sources.md`). Kept, not needed day to day |

## Decisions waiting on you

Each has a recommended default, so nothing here stops discovery calls.

1. **Keep the working name, or pick a fallback?** Blocks any print run and public profile. Default: follow the legal pack (check two coined fallbacks by Fri 2026-11-13, choose at the attorney hour Wed 2026-11-18). A rename here is one edit and one command, and your saved details survive it.
2. **Which phone and postal address go on everything?** Default: a business mobile line and a USPS post office box (or a registered private mailbox) near the cluster, entered once in `details.html`; the website stays off until it is public.
3. **A map for each brand's proposal.** Default: list the brand's evidenced stores in the proposal's order and ask the cluster-map workstream (or run its script) for that brand's map with the pins in the same order.
4. **Two flavors: one card or one per flavor?** Default: one card when both statements fit at 14 pt; one card per flavor when the card says they do not.

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
