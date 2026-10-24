# Identity and collateral (workstream D)

Everything the founder needs to look consistent from the first discovery call to the first campaign report, without a designer: the identity system, the tent card and case label, the discovery, office and brand one-pagers, the proposal with a mock report page, the one-page report, the email signature and the social avatar. Version 1.1, 2026-10-24.

**Name and print gate** (from `../desk-drop-legal-pack/name-check-log.md`, v0.5, 2026-10-24): print run **HOLD**, public launch **HOLD**, private discovery calls **go**. A business already trades as "DeskDrop", and the USPTO refused DESK-DROP as descriptive. The legal pack recommends choosing a fallback name by Fri 2026-11-13 (derived, founder to confirm). Home and copy-shop test prints are fine. Documents sent one to one are fine. A rename here is one edit to `brand.json` plus one command (see "Rename").

## Start here

1. Read `USAGE-GUIDE.md`. Section 0 says which piece you need when.
2. Put your details in `brand.json` once (guide section 7). Until then they print yellow and `--final` refuses.
3. Open any template in Google Chrome: `templates/<piece>/<piece>.html`. Fill the boxes on the left; the page updates. Press Print (or Print or save as PDF).
4. To see finished examples first, open the PNGs in `pdf/png/`.

## Files, in the order you will use them

### Your details, prices and the name (edit these)

| File | What it is | How to edit |
| --- | --- | --- |
| `brand.json` | The one place the name (`BRAND_NAME`), tagline and your contact details live: `[FOUNDER NAME]`, `[PHONE]`, `[EMAIL]`, `[WEBSITE]`, `[POSTAL ADDRESS]`, `FOUNDER_TITLE` (default "Founder"), optional `SIGNATURE_LOGO_URL` | Text editor, then `bash render/build-pdfs.sh` (or `node render/build-brand.js` and `node render/build-signature.js`) |
| `system/dd-offer.js` | The one place the prices and campaign numbers live ($600 founding for 5 offices, $1,500 standard for 10, $150 extra office, 10% reserve, 30 to 80 units, cancellation terms) | Text editor; change the campaign agreement to match; rebuild |
| `USAGE-GUIDE.md` | Step-by-step guide for every piece, written for a non-designer | Text editor |

### Discovery, weeks 1 to 3

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/discovery-one-pager/discovery-one-pager.html` | The idea in exactly five sentences, no selling | Chrome panel (guide section 8). The template refuses two sentences in a box and warns on selling words |
| `templates/discovery-one-pager/FIELDS.md`, `samples/DEFAULT.json`, `samples/SAMPLE-must-warn.json` | Field rules; the shipped sentences; a sample that proves the checks fire | |
| `pdf/discovery-one-pager-BLANK.pdf` | The page as shipped, your details still yellow | Rebuilt by `build-pdfs.sh` |
| `signature/signature.html`, `signature.txt` | Everyday email signature: name, title, [PHONE] · [EMAIL] · [WEBSITE], [POSTAL ADDRESS] | Generated from `brand.json`. Set up in Gmail: guide section 13 (needs your login) |
| `signature/signature-outreach.html`, `.txt` | The same plus the legal pack's commercial-email line (Footer B), for cold outreach | Generated; the line is read from `../desk-drop-legal-pack/02-email-footer-and-checklist.md` |
| `signature/signature-with-logo.html` | Logo version, only once the wordmark PNG is hosted | Set `SIGNATURE_LOGO_URL` in `brand.json`, rebuild |
| `signature/preview-*.png` | What the signatures look like on desktop, at phone width, and the outreach version | |

### Recruiting offices and selling brands, weeks 3 to 7

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/office-one-pager/office-one-pager.html` | Office one-pager: pitch, what you get and what we ask, never asked, how a drop works, what is in the case, privacy, founding offices, what you sign, with a proposed first-drop week | Chrome panel (guide section 9). All copy is in boxes; `{BRAND_NAME}` prints the name |
| `templates/brand-one-pager/brand-one-pager.html` | Brand one-pager: positioning line, what a campaign includes, price, what we count and what we don't (the ladder), the seven-point fit, what you send, what we never promise | Chrome panel (guide section 10). **Roster today** must say only what is true |
| `templates/proposal/proposal.html` | One-page proposal plus a mock report page: route roster (no company names), retailer map slot and stores, specification, price and terms, what the brand sends and by when, timeline worked out from the drop date, the report | Chrome panel (guide section 11), or `node render/render.js proposal data.json out.pdf --final` |
| `templates/*/FIELDS.md` | Every field, its source column (CONTRACTS section 6) and its rule | |
| `templates/*/samples/` | `BLANK-placeholders.json` (empty form) and `SAMPLE-*.json` (test data) per template | Copy one as a start |
| `pdf/office-one-pager-BLANK.pdf`, `pdf/brand-one-pager-BLANK.pdf`, `pdf/proposal-BLANK.pdf`, `pdf/proposal-SAMPLE-founding.pdf`, `pdf/proposal-SAMPLE-standard-10-offices.pdf` | The documents as PDFs | Rebuilt by `build-pdfs.sh` |

### Campaign: kitting, drop day, photos

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/tent-card/tent-card.html` | The 5 x 7 in tent card (landscape faces, tent fold, 7 x 10 in flat on Letter), allergen text locked at 14 pt | Chrome panel (guide section 2), or `render.js tent-card` from JSON (section 3) |
| `templates/case-label/case-label.html` | Case label, 8.5 x 5.5 in, two per Letter sheet: office, brand, units, [PHONE] | Chrome panel (guide section 5) |
| `specs/tent-card-spec.pdf`, `specs/case-label-spec.pdf` | Print specs: size, bleed, safe area, stock, fold, every type size, give-way order, placement and photo rules | Source `specs/*.html`; rebuild |
| `pdf/tent-card-*.pdf`, `pdf/case-label-*.pdf` and their PNGs | Blank and SAMPLE cards and labels: home print, print-shop bleed file, a 5-office batch, the 25-word allergen test | Rebuilt. Never place a SAMPLE card |

### Reporting, by T plus 7

| File | What it is | How to edit |
| --- | --- | --- |
| `templates/report/report.html` | The one-page report: header, the ladder (delivered, placed, depleted, responded, scanned, purchased, incremental: not measured), roster, two photos per office, survey with counts beside every share and three verbatim comments, engagement, learned, recommendation, the fixed limitations paragraph; an evidence page with every photo | Chrome panel (guide section 12), or `node render/render.js report report.json report.pdf --final` (photo paths relative to the JSON) |
| `templates/report/samples/` | `BLANK-placeholders.json`, `SAMPLE-5-offices.json`, `SAMPLE-10-offices-long-comments.json` (the brief's test), `photos/` (our own simulated pantry photos, SAMPLE) | |
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
| `REPORT.md` | Report back for parts 1 and 2: deliverables, tool choice, assumptions, changelog, tests, questions. This session's file write was refused by the harness (as in part 1), so the full text went to the orchestrator in the returned message; the orchestrator saves it here. Test results are also in `tests/README.md` |
| `system/dd-template.js`, `dd-print.css` | Template runtime: panel, placeholders, SAMPLE banner, table and picture fields, status |
| `system/dd-docs.css`, `dd-docs.js` | Letter documents: header, footer, image slot, card drawing, page fitting, claims check |
| `system/dd-report.js` | The report renderer and the fixed limitations paragraph (also draws the proposal's mock page) |
| `system/dd-dates.js` | CONTRACTS section 3 calendar: business days, holidays to 2027-09-30, blackouts, T offsets |
| `system/dd-offer.js` | Prices and campaign numbers |
| `system/brand.js` | Generated from `brand.json` (Chrome cannot read JSON from a file) |
| `system/vendor/` | qrcode-generator 2.0.4 and opentype.js 1.3.4, MIT, with licenses |
| `render/render.js` | JSON to print-ready PDF for any template (`--final`, `--json`, `--mode pro`, `--png`) |
| `render/render-page.js` | A static page (spec sheets) to PDF |
| `render/build-brand.js`, `build-signature.js`, `build-avatar.js`, `build-pdfs.sh` | Rebuild the wordmark, signature, avatar, or everything |
| `tests/` | Every test and its outputs; `tests/README.md` has the results and what failed first. `bash tests/run-all.sh` |
| `package.json` | Lists Playwright for the terminal commands |
| `_work/` | Working log (`decisions-log.md`) and sources (`research/sources.md`). Kept, not needed day to day |

## Commands (optional; Chrome alone is enough for one piece)

Install once: Node 18 or newer (nodejs.org), then in this folder `npm install` and `npx playwright install chromium`. Both free. For the page PNGs, poppler (`pdftoppm`).

```bash
node render/render.js tent-card cards.json cards.pdf --final       # one card per office
node render/render.js case-label labels.json labels.pdf --final    # two labels per sheet
node render/render.js proposal proposal.json proposal.pdf --final  # proposal plus mock page
node render/render.js report report.json report.pdf --final        # report plus evidence page
bash render/build-pdfs.sh                                          # rebuild everything
bash tests/run-all.sh                                              # run every test
```

Exit codes: 0 written, 1 usage, 2 the template refused (does not fit, impossible numbers, bad date), 3 `--final` found placeholders, SAMPLE values or unfilled `brand.json` contacts.

## Rename

Edit `BRAND_NAME` in `brand.json`, run `bash render/build-pdfs.sh`, then find-and-replace the old name in the `.md` files here and re-copy the signature into Gmail. Nothing else holds the name: the documents' copy uses `{BRAND_NAME}`. Details: `USAGE-GUIDE.md` section 16. Tested with "Dropp" and "Desk Drop Collective" (`tests/name-length/`, `tests/rename-documents/`).

## Ordering a print run

**Not yet: the legal pack's gate is HOLD.** When `../desk-drop-legal-pack/name-check-log.md` clears the name, rerun its day-before-printing checks, then:

1. Make the card PDF with `--final`. Each office's card is its own design (its own QR), so print the one-card-per-page Letter PDF.
2. At a copy shop (for example a FedEx Office or Staples counter; options and prices unverified, founder to confirm): 8.5 x 11 in, white matte cover stock 80 to 110 lb, single-sided, 100% scale, no "fit to page". Cut and score yourself, or ask for a quote to cut to 7 x 10 in and score at 5 in.
3. A shop that wants bleed gets the `--mode pro` file (7.25 x 10.25 in, 0.125 in bleed, trim 7 x 10 in, score across the middle).
4. Online table tents (for example Vistaprint: 5 x 7 in vertical only, from 10 per design; page opened 2026-10-24) do not fit one design per office.
5. Case labels: Avery 5126-size half sheets, printed at home. Documents are sent as PDFs, not printed.

The plan budgets about $1 to $2 a card in runs of 20. No spending without the founder's written yes: get the quote, then decide. Full steps: `USAGE-GUIDE.md` section 17.
