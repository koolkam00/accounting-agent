# The identity system (v1.3)

Written 2026-10-23 (v1.0: identity, tent card, case label) and extended 2026-10-24 (v1.1: one-pagers, discovery one-pager, proposal, report, email signature, avatar). For the founder and for whoever extends it next. Everything below is a rule unless it says "default".

The working name is "Desk Drop". It is not cleared. It appears in exactly two places that matter: `brand.json` (as text) and the generated `wordmark/` files (as outlines). Everything else reads from those.

---

## 1. Single sources of truth

| What | File | Who reads it |
| --- | --- | --- |
| Name, tagline, founder contact placeholders | `brand.json` (`BRAND_NAME`, `TAGLINE`, `WORDMARK_LINE_BREAK`, `contact.*`) | `render/build-brand.js` writes `system/brand.js` from it; templates read `window.DD_BRAND`. Contacts can also be set in Chrome with `details.html`, which saves `system/brand.js`; the next build copies them back into `brand.json` |
| Colors, type, spacing, radii, rules | `tokens/tokens.css` and `tokens/tokens.json` (kept equal by `tests/check-tokens.js`) | Templates, spec sheets, the website (workstream C imports `tokens.css`) |
| Wordmark and symbol | `wordmark/*.svg`, generated; never hand-edit | Templates, website, signature |
| Fonts | `fonts/static/*.ttf` (print, offline), `fonts/*-VF.ttf` (variable) and Google Fonts (web) | `fonts/fonts.css` (static instances, so PDFs embed TrueType, not Type 3) for print; `fonts/fonts-variable.css` for anything needing in-between weights; the Google Fonts link in `tokens.css` for the web |
| Template runtime | `system/dd-template.js`, `system/dd-print.css` | Every data-driven template |
| Letter documents | `system/dd-docs.css`, `system/dd-docs.js` | One-pagers, discovery, proposal, report |
| Prices and campaign numbers | `system/dd-offer.js` (`window.DD_OFFER`) | Proposal, brand one-pager. Change here and in the campaign agreement |
| Campaign calendar | `system/dd-dates.js` (CONTRACTS section 3: business days, holidays, blackouts, T offsets) | Proposal, report, tests |
| The report layout and the limitations paragraph | `system/dd-report.js` (`DDReport.LIMITATIONS`, frozen copy in `tests/documents/limitations-frozen.txt`) | Report, the proposal's mock page |

**Rename in one file plus a find-and-replace:** edit `BRAND_NAME` in `brand.json`, run `bash render/build-pdfs.sh` (it rebuilds the wordmark, `system/brand.js` and every PDF), then find-and-replace the old name in the `.md` guides. No file or folder name contains the working name, except the output folder `desk-drop-identity/`, which CONTRACTS fixes.

---

## 2. Color

| Token | Hex | Use | Never |
| --- | --- | --- | --- |
| `--dd-ink` | #1F1D1A | Text, rules, the wordmark on light | |
| `--dd-ink-soft` | #3A3732 | Secondary text, dark fills | |
| `--dd-stone` | #6B675F | Captions, card IDs (5.6:1 on white) | Allergen text, body sentences |
| `--dd-mist` | #E6E1D6 | Hairlines, table rules | Text |
| `--dd-paper` | #FFFFFF | Every printed background is the sheet itself | |
| `--dd-paper-warm` | #F7F3EA | Screen backgrounds | Printed floods (wastes ink, bands on inkjets) |
| `--dd-cobalt` | #2E47C9 | The one signal color: the band, "Take one.", the symbol's box | Large floods behind body text in print |
| `--dd-cobalt-light` | #9AABFF | Signal color on dark backgrounds | On white |
| `--dd-cobalt-tint` | #E3E8FB | Light fills on screen | |
| `--dd-apricot` | #F4B183 | Small warm accents on screen | Text on white |
| `--dd-placeholder` | #FFE45C | Highlighter behind unfilled `[PLACEHOLDERS]` | Decoration |
| `--dd-error`, `--dd-sample` | #B3261E | Template errors, the SAMPLE banner | Brand use |

Why cobalt: snack packaging leans red, orange, yellow, brown and green. Blue stands apart on a pantry shelf, reads as neither "warning" (red, yellow) nor "healthy" (green, which would brush against health-claim territory), and white text on it passes 7:1. All text pairs are checked against WCAG 2.2 AA by `node tests/check-tokens.js` (4.5:1 for text; W3C, opened 2026-10-23).

Print: ink on white, one cobalt element per piece, allergen text pure black. Screen: warm paper background, cobalt for links and buttons. Dark mode (screen only) swaps to ink background, warm-white text and light cobalt; print is always light.

---

## 3. Type

Two families, both on Google Fonts under the SIL Open Font License 1.1, so the website can match and commercial use is free. License files: `fonts/OFL-*.txt`.

| Role | Family | Weights used | Why |
| --- | --- | --- | --- |
| Display: the name, brand names on cards, headings | **Bricolage Grotesque** (Mathieu Triay) | 800 (ExtraBold), 700 | Warm and a little irregular, so it does not read as corporate. Its width axis (75 to 100%) lets a long brand name narrow before it shrinks. Optical size axis set to 96 for display. |
| Text: everything people read, including allergens | **Atkinson Hyperlegible Next** (Braille Institute and others) | 400, 600, 700 | Developed "specifically to increase legibility for readers with low vision" (project README, opened 2026-10-23). Distinct letter shapes (slashed zero, clear I/l/1) survive phone photos and IDs like O-001. |

Fallbacks: display falls back to Arial Narrow, Helvetica Neue, Arial; text to system-ui, Segoe UI, Roboto, Arial.

**The one text style for the name:** CSS class `.dd-brand-name` (Bricolage Grotesque 800, 100% width, -0.01em tracking, opsz 96). Wherever the name is typeset instead of shown as the wordmark image, use this class.

Screen scale (px): 12, 14, 16, 18, 22, 28, 36, 48, 64. Leading: 1.05 display, 1.2 snug, 1.45 body.

Print floors: allergen text **14 pt, locked** (tent card); any sentence an employee reads 10 pt; fine print (IDs, sheet notes) 7 pt. Letter documents (read by office managers and brand founders, mostly on screen): body and tables 8.5 pt, verbatim comments 8 pt, notes and the limitations paragraph 7 to 7.5 pt. The 14 pt lock comes from the close-photo test (`tests/README.md`, test 4) and is enforced in code, not only in CSS.

Print uses static font files, one per width: Bricolage Grotesque ExtraBold at 100%, 87.5% and 75% width (and Bold at 100%), Atkinson Hyperlegible Next Regular, SemiBold, Bold and Italic. Ask templates for nothing in between; the runtime loads every face before it measures anything.

---

## 4. Spacing, radii, rules

Spacing is a 4 px scale: `--dd-space-1` to `--dd-space-9` = 4, 8, 12, 16, 24, 32, 48, 64, 96 px. In print 1 CSS px = 1/96 in, so 16 px = 1/6 in, 24 px = 1/4 in, 48 px = 1/2 in, 96 px = 1 in. Use the scale; do not invent in-between values.

Radii: 0 for everything printed (hand-trimmed corners), 4 px and 8 px on screen, pill for buttons. Rules: 1 px hairline (`--dd-rule-hair`), 2 px rule (`--dd-rule`, the allergen panel border), 4 px heavy (`--dd-rule-heavy`). The rule's color is `--dd-rule-color` (ink on light, warm paper in dark mode). v1.3 (review round 2): that color was also named `--dd-rule`, so one property meant a color and a width and the width won; `tests/check-tokens.js` now fails on any name defined twice or used for two kinds of value.

---

## 5. Wordmark and symbol

- **Construction.** The name set in Bricolage Grotesque 96 pt ExtraBold at -1% tracking, converted to outlines by `render/build-brand.js`, plus the symbol: a cobalt box tilted 12 degrees, dropping onto an ink shelf. The symbol does not depend on the name, so it survives any rename and is the avatar (part 2).
- **Lockups.** Horizontal (symbol height = cap height) for most uses; stacked (symbol above the name) for square spaces; symbol alone for tiny or square spaces. A two-line name (`WORDMARK_LINE_BREAK` in `brand.json`, for example `"Desk Drop|Collective"`) makes a compact block.
- **Versions.** `-light` (ink name, cobalt box) on white or warm paper; `-dark` (warm-white name, light-cobalt box) on ink; `-mono-ink` for one-color print; `-mono-white` on photos or cobalt.
- **Size by cap height, never by box height.** Minimum cap height: 0.1 in in print, 9 px on screen. In templates use `DD.wordmarkImg(capInches)`, which reads the cap fraction from `system/brand.js`.
- **Clear space.** At least half the cap height on every side.
- **When the name is long.** If the horizontal lockup is wider than 7:1 (`wordmark/wordmark-metrics.json` says so), use the stacked lockup or set a line break.
- **Never:** recolor outside the four versions, stretch, add effects, retype the name in another font, or put the light version on a photo.

---

## 6. Layout grids

| Piece | Page | Safe area | Grid |
| --- | --- | --- | --- |
| Tent card face | 7 x 5 in (landscape), flat 7 x 10 in on Letter | 0.25 in from trim and fold | Single column: band, brand name (full width), middle row (sentences left, "Take one" + QR right), allergen panel (full width), footer (buy path left, wordmark right) |
| Case label | 8.5 x 5.5 in, two per Letter | 0.4 in | Two columns: content 1fr, count box 1.9 in, 0.3 in gutter |
| Letter documents (one-pagers, discovery, proposal, report) | 8.5 x 11 in portrait | 0.6 in sides, 0.55 in top, 0.5 in bottom; the report 0.45 in top, 0.4 in bottom | One-pagers: 6 columns, 0.2 in gutters. Proposal: two free-flowing columns, 0.25 in gutter. Header: wordmark by cap height (0.25 in), cobalt 3 px rule under it. `specs/documents-spec.pdf` |

---

## 7. Components (reuse them)

| Component | Where | Rule |
| --- | --- | --- |
| Cobalt band | Top of the card face and labels (0.1 to 0.12 in) | One per piece. Identifies a display as ours in a pantry photo. |
| Allergen panel | Tent card | 2 px ink border, white fill, label line in 9 pt bold, statement in 14 pt semibold black. Never shrinks; everything else gives way. Two flavors (v1.3): each flavor's name in 10 pt bold above its own statement and "may contain" line, both from their own packages, all at 14 pt; if both do not fit, one card per flavor. The label line follows `allergen_source`: a "Contains" statement; the whole ingredient list (when that is the package's only declaration; a list too long to share a face moves in full to the front face, marked "this side faces the room", and the story and QR move to the other face); or, for a single-ingredient product with no ingredient list, its name as printed. There is no "no allergens" option (v1.2): the card always prints the package's own words. |
| Brand logo (optional) | Tent card | The brand's own file, 0.9 in tall, never wider than the safe area. A wide logo (2.2:1 or wider) replaces the typed name and stops at 0.75 in; a compact one sits beside it and stops at 0.55 in. v1.3: it gives way after the story size, the gaps and the find-it line, not first. |
| Take-one block | Tent card | "Take one." in cobalt display, "Tell us what / you think" in bold, arrow to the QR. |
| QR block | Tent card | 4-module quiet zone included; short link printed under it. Generated by `DD.qrSvg(url, px)`. |
| Count box | Case label | 3 px ink border, number in 64 pt display. |
| Kicker | Labels, documents | 10 pt bold caps, 0.08 em tracking, ink-soft. |
| Placeholder mark | Everywhere | `[LIKE THIS]` in brackets with a yellow highlighter, on screen and on paper. Produced automatically by `DD.text()`. |
| SAMPLE banner | Any output built on sample data | Red band, white caps: "Sample. ... Illustrative placeholders, not results." Appears automatically when any value starts with SAMPLE. |
| Image slot | Report, office one-pager | Grey dashed box: "Real pantry photo, no identifiable people". `[PHOTO]` = not attached yet (a placeholder). Empty = the office sent none: a white box "No photo received". Never a stock photo. |
| Ladder strip | Report, brand one-pager | Seven rungs, fixed names: Delivered, Placed, Depleted, Responded, Scanned, Purchased, Incremental (dashed box, "Not measured"). Cobalt top rule on the six measured rungs. |
| Card drawing | Office one-pager | `DDDocs.cardDiagram()`: the tent card drawn to scale with a QR-like pattern that encodes nothing. Not a photo. |
| Mock band | Proposal page 2 | Ink band "Mock report page · Illustrative placeholders, not results" plus the same words in the margin. |
| Price box | Proposal, brand one-pager | Cobalt tint, numbers from `dd-offer.js`. |

---

## 8. Template mechanics (how every data-driven template works)

Each template is one HTML file in `templates/<name>/<name>.html`. It:

1. links `fonts/fonts.css`, `tokens/tokens.css`, `system/dd-print.css`;
2. holds its editable default data in `<script type="application/json" id="dd-data">` (the founder can edit this in a text editor);
3. loads `system/vendor/qrcode-generator-2.0.4.js` (if it needs QR), `system/brand.js`, `system/dd-template.js`;
4. calls `DD.init({ title, fields, render, fit, perSheet, fileStem, printHelp })`.

| Part | What it does |
| --- | --- |
| `fields` | `[{ key, label, required, help, multiline, rows, maxChars, group }]`. Builds the on-screen fill-in panel and the required/length checks. |
| `render(sheet, record, index)` | Writes one printed sheet. With `perSheet: 2`, receives an array of records instead. Use `DD.text()` for every value (escapes HTML, keeps line breaks, highlights placeholders). Add rule checks with `DD.error(i, msg)` (blocks the PDF) and `DD.warn(i, msg)`. |
| `fit(sheet, record, index)` | Runs after fonts load. Adjusts sizes to fit, in a stated give-way order. |
| Status | `window.__DD_STATUS__ = { ready, errors, warnings, sample, placeholders }`, read by the render script and shown in the panel. |
| Headless | The render script sets `__DD_DATA__`, `__DD_HEADLESS__` and `__DD_MODE__` before the page runs. |

**v1.1 field types.** `type: 'table'` (a list of rows, one fold-out group per row in the panel, `columns` are field definitions, `rowLabel`, `summary`, `newRow`, `minRows`, `maxRows`) and `type: 'image'` (a picture: a path relative to the JSON file from the terminal, or a picture chosen in the panel, downscaled to 1600 px JPEG inside the saved JSON). The scan goes into rows for placeholders and SAMPLE values. `DD.contact(key)` reads `brand.json` and counts an unfilled contact as a placeholder, so `--final` refuses a document without your phone or postal address. Editable copy uses `DDDocs.t()`: `{BRAND_NAME}` prints the name, `**words**` print bold.

**v1.2 records.** With `recordLabel` ('Card', 'Label') the panel gets a picker to edit any record, and Add and Remove buttons (`recordName`, `newRecord` optional). Messages carry a "Card 3: " prefix only when more than one record is loaded; one record means no prefix. `DD.placeholder(i, what)` records an unfinished item. `picture: 'logo'` on an image field keeps SVG as is and PNG transparency.

**Your details without a terminal (v1.2).** `details.html` reads `system/brand.js`, shows the signature live (built by `system/dd-signature.js`, the same code `render/build-signature.js` uses, with Footer B from `system/signature-footer.js`), and saves a new `brand.js` marked `details_saved`. `render/brand-sync.js` copies those details into `brand.json` at every terminal build wherever `brand.json` still has the placeholder, even right after a rename (v1.3); where both hold different values, the newer file wins and the build says so. The name is never taken from `brand.js`.

**Every document fits its page or refuses.** `DDDocs.fitPages(sheet, i, steps)` applies the template's stated give-way steps in order; if a page still overflows, it puts a red bar on screen, reports an error and render.js writes no PDF (exit 2). Floors: body 8.5 pt, tables 8.5 pt, verbatim comments 8 pt, notes 7 pt.

**To add a template (checklist):** copy `templates/case-label/` as a start; rename the folder and file; write `fields`, `render`, `fit`; add a `samples/SAMPLE-*.json` and a `samples/BLANK-placeholders.json`; add a `FIELDS.md`; add its lines to `render/build-pdfs.sh`; render it, look at it, and run the tests. A static page (no data) such as a spec sheet uses `render/render-page.js` instead.

---

## 9. Render pipeline and tests

| Command (run inside `desk-drop-identity/`) | Result |
| --- | --- |
| `node render/build-brand.js` | Wordmark SVG and PNG files and `system/brand.js` from `brand.json` |
| `node render/render.js <template> <data.json> <out.pdf> [--final] [--mode pro] [--png f] [--face-png f] [--dpi n] [--json]` | Print-ready PDF from JSON (exit 0 ok, 2 template errors, 3 placeholders or SAMPLE left under `--final`) |
| `node render/render-page.js <page.html> <out.pdf> [--png f]` | PDF of a static page (spec sheets, guides) |
| `node render/build-signature.js` | `signature/` from `brand.json` and the legal pack's Footer B |
| `node render/build-avatar.js` | `avatar/` from the symbol |
| `bash render/build-pdfs.sh` | Rebuilds everything: wordmark, signature, avatar, every PDF in `pdf/`, a PNG of every page in `pdf/png/`, `specs/` |
| `bash tests/run-all.sh` | Every test in `tests/README.md` |

Requirements: Google Chrome for printing by hand. For the commands: Node 18 or newer and Playwright (`npm install` then `npx playwright install chromium` in this folder; both free).

---

## 10. Print versus screen

| | Print | Screen |
| --- | --- | --- |
| Background | The white sheet | Warm paper #F7F3EA (or ink in dark mode) |
| Color | Ink plus one cobalt element; must work in black and white | Cobalt for links and buttons |
| Type floors | 14 pt allergen (locked), 10 pt sentences, 7 pt fine print | 16 px body, 12 px minimum |
| Units | inches and points | px and rem |
| Bleed | None at home; 0.125 in for a print shop | n/a |
| Corners | Square | 4 to 8 px radius |
| Dark mode | Never | Allowed |

---

## 11. Words (applies to every template)

- Measurement words come from the ladder and are never softened: delivered, placed, depleted, responded, scanned, purchased, incremental (not measured; say so). No "conversions", "sales lift", "ROI" or "acquisition".
- No health claims, no "guaranteed", no sales or lift promises, no "best". Nutrient-content statements ("10g protein") need the founder's review.
- No invented numbers, testimonials, customer logos or roster names. Mock values appear only under "Illustrative placeholders, not results."
- Placeholders keep the exact form `[FOUNDER NAME]`, `[PHONE]`, `[EMAIL]`, `[POSTAL ADDRESS]`, `[WEBSITE]`, `[DOMAIN]`. Dates in copy are bracketed slots such as `[DROP DATE: Tue 2027-01-12]`.
- Images: real pantry photos with no identifiable people. No stock photos.

---

## 12. Documents (v1.1)

| Piece | Template | Contents (source) | Fixed parts |
| --- | --- | --- | --- |
| Discovery one-pager | `templates/discovery-one-pager/` | The idea in five sentences, no selling (plan Phase 0) | Exactly five sentences; selling words warn |
| Office one-pager | `templates/office-one-pager/` | Pitch, get and give, never asked, how a drop works, product standard, privacy, founding offer, what they sign (plan Phase 1 and revised model) | Proposed first-drop week required |
| Brand one-pager | `templates/brand-one-pager/` | Positioning line, what brands buy, price, the ladder with methods, the seven-point fit, what they send, no promise (plan revised model and Phase 2) | Price box, ladder rungs, roster line must be filled with what is true today |
| Proposal | `templates/proposal/` | Roster by neighborhood, industry and headcount band; retailer map and stores; specification; price, terms, founding lock; what the brand sends and by when; timeline; the report, with a mock page (plan Phase 2) | Prices, terms, dates computed from the drop date, mock page |
| Report | `templates/report/` | Header, ladder, roster, two photos per office, survey with counts and three verbatim comments, engagement, learned, recommendation, limitations (plan appendix M and measurement section) | Limitations paragraph, ladder, computed totals and shares, impossible numbers refused |

**Measurement rules in code.** Delivered means the units handed over on drop day, everywhere: the ladder, the roster total and `campaign_actuals.units_delivered`. Day-3 top-ups are their own column and are never added to Delivered. The Placed rung prints the Gate 2 share (units placed within one business day out of units delivered). Totals and shares are computed, never typed. Every share prints beside its count and its denominator. Impossible numbers (placed more than delivered, depleted more than placed plus topped up, more "tried" than responses) refuse the PDF. A missing photo prints "No photo received". Comments are printed whole; a comment containing an email address or phone number is refused. Claims and soft-ladder words in the founder's own text are errors (v1.3), from one shared list in `system/dd-template.js` (`DD.claimsIn`, `DD.checkClaims`) that the tent card and every document use, with structure or function wording added; `claims_reviewed` Y with a reason is the only override. A photo's date prints only when it was recorded (`placement_photo_date`, `later_photo_date`), and it must agree with "placed within one business day".

## 13. Screen pieces (v1.1)

- **Email signature** (`signature/`, from `render/build-signature.js`): tables and inline styles only, Atkinson Hyperlegible Next then Arial, 14 px name and 13 px lines, ink and ink-soft text, a 3 px cobalt rule. Carries [FOUNDER NAME], the title and name, [PHONE] · [EMAIL] · [WEBSITE], [POSTAL ADDRESS]. The outreach version adds the legal pack's Footer B line verbatim. Unfilled values print yellow. `WEBSITE: ""` leaves the website out.
- **Avatar** (`avatar/`, from `render/build-avatar.js`): the symbol alone at 50% of the square, centred and nudged up 2%, inside the circle crop. Default cobalt (white symbol on cobalt); paper and ink variants. PNG at 1024, 512, 400, 320, 160, 80 and 40 px, and SVG.

## 14. Versions

v1.0, 2026-10-23 to 24: identity, tokens, tent card, case label, specs, tests (part 1).
v1.3, 2026-10-24 (review round 2): rename keeps details saved in Chrome (`brand-sync.js` rule per key, no file-time gate); report photo dates only where recorded; one claims list that blocks; two-flavor allergen panel; wide-logo floor 0.75 in and later in the give-way; card ID 0.12 in from the trim, 9 pt room tag; `--dd-rule-color`; proposal store table with pin numbers, full-width map arrangements, biggest-map choice, mock page from the proposal's own route; office and brand one-pager wording; `[HEADCOUNT BAND]`; `brand.json` gains `FOUNDER_TITLE` and `SIGNATURE_LOGO_URL`.

v1.2, 2026-10-24 (review round 1): record picker and plain single-record messages; tent card logo slot, single-ingredient option instead of "Nowhere", ingredient face as the front, name give-way after the product line; report photo strip for six to twelve offices, Delivered as the handoff count, Placed with the Gate 2 unit share, run-in headings, limitations first sentence corrected; proposal column arrangements (two-up and three-up roster, timeline strip), 12-office maximum, terms from agreement v0.8, mock page without yellow; brand and office one-pagers fit real-length details; details.html for the Chrome-only path.

v1.1, 2026-10-24: runtime gains table and picture fields, deep scan and contact placeholders; Letter document system; discovery, office and brand one-pagers; proposal with mock report page; report; calendar and offer files; email signature; avatar; documents spec; swap test and document tests (part 2). The tent card and case label are unchanged and pass every part-1 test on the v1.1 runtime.
