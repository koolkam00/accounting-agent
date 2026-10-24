# The identity system (v1.0)

Written 2026-10-23 for the founder and for whoever extends it next (part 2 builds the one-pagers, discovery one-pager, proposal, report template, email signature and avatar on top of this). Everything below is a rule unless it says "default".

The working name is "Desk Drop". It is not cleared. It appears in exactly two places that matter: `brand.json` (as text) and the generated `wordmark/` files (as outlines). Everything else reads from those.

---

## 1. Single sources of truth

| What | File | Who reads it |
| --- | --- | --- |
| Name, tagline, founder contact placeholders | `brand.json` (`BRAND_NAME`, `TAGLINE`, `WORDMARK_LINE_BREAK`, `contact.*`) | `render/build-brand.js` writes `system/brand.js` from it; templates read `window.DD_BRAND` |
| Colors, type, spacing, radii, rules | `tokens/tokens.css` and `tokens/tokens.json` (kept equal by `tests/check-tokens.js`) | Templates, spec sheets, the website (workstream C imports `tokens.css`) |
| Wordmark and symbol | `wordmark/*.svg`, generated; never hand-edit | Templates, website, signature |
| Fonts | `fonts/static/*.ttf` (print, offline), `fonts/*-VF.ttf` (variable) and Google Fonts (web) | `fonts/fonts.css` (static instances, so PDFs embed TrueType, not Type 3) for print; `fonts/fonts-variable.css` for anything needing in-between weights; the Google Fonts link in `tokens.css` for the web |
| Template runtime | `system/dd-template.js`, `system/dd-print.css` | Every data-driven template |

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

Print floors: allergen text **14 pt, locked** (tent card); any sentence an employee reads 10 pt; fine print (IDs, sheet notes) 7 pt. The 14 pt lock comes from the close-photo test (`tests/README.md`, test 4) and is enforced in code, not only in CSS.

Print uses static font files, one per width: Bricolage Grotesque ExtraBold at 100%, 87.5% and 75% width (and Bold at 100%), Atkinson Hyperlegible Next Regular, SemiBold, Bold and Italic. Ask templates for nothing in between; the runtime loads every face before it measures anything.

---

## 4. Spacing, radii, rules

Spacing is a 4 px scale: `--dd-space-1` to `--dd-space-9` = 4, 8, 12, 16, 24, 32, 48, 64, 96 px. In print 1 CSS px = 1/96 in, so 16 px = 1/6 in, 24 px = 1/4 in, 48 px = 1/2 in, 96 px = 1 in. Use the scale; do not invent in-between values.

Radii: 0 for everything printed (hand-trimmed corners), 4 px and 8 px on screen, pill for buttons. Rules: 1 px hairline, 2 px rule (the allergen panel border), 4 px heavy.

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
| Letter documents (part 2: one-pagers, proposal, report) | 8.5 x 11 in portrait | default margins 0.6 in sides, 0.55 in top, 0.5 in bottom | Default: 6 columns, 0.2 in gutters. Header: wordmark at 0.32 in height, cobalt 3 px rule under it. See `specs/spec.css` for a working example |

---

## 7. Components (reuse them)

| Component | Where | Rule |
| --- | --- | --- |
| Cobalt band | Top of the card face and labels (0.1 to 0.12 in) | One per piece. Identifies a display as ours in a pantry photo. |
| Allergen panel | Tent card | 2 px ink border, white fill, label line in 9 pt bold, statement in 14 pt semibold black. Never shrinks; everything else gives way. The label line follows `allergen_source`: a "Contains" statement, the whole ingredient list (when that is the package's only declaration; a list too long for the front moves in full to the other face and the front points to it), or a fixed pointer when the package declares none. |
| Take-one block | Tent card | "Take one." in cobalt display, "Tell us what / you think" in bold, arrow to the QR. |
| QR block | Tent card | 4-module quiet zone included; short link printed under it. Generated by `DD.qrSvg(url, px)`. |
| Count box | Case label | 3 px ink border, number in 64 pt display. |
| Kicker | Labels, documents | 10 pt bold caps, 0.08 em tracking, ink-soft. |
| Placeholder mark | Everywhere | `[LIKE THIS]` in brackets with a yellow highlighter, on screen and on paper. Produced automatically by `DD.text()`. |
| SAMPLE banner | Any output built on sample data | Red band, white caps: "Sample. ... Illustrative placeholders, not results." Appears automatically when any value starts with SAMPLE. |
| Image slot (part 2) | Report, proposal | Grey box with the caption "real pantry photo, no identifiable people". Never a stock photo. |

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

**To add a template (part 2 checklist):** copy `templates/case-label/` as a start; rename the folder and file; write `fields`, `render`, `fit`; add a `samples/SAMPLE-*.json` and a `samples/BLANK-placeholders.json`; add a `FIELDS.md`; add its lines to `render/build-pdfs.sh`; render it, look at it, and run the tests. A static page (no data) such as a spec sheet uses `render/render-page.js` instead.

---

## 9. Render pipeline and tests

| Command (run inside `desk-drop-identity/`) | Result |
| --- | --- |
| `node render/build-brand.js` | Wordmark SVG and PNG files and `system/brand.js` from `brand.json` |
| `node render/render.js <template> <data.json> <out.pdf> [--final] [--mode pro] [--png f] [--face-png f] [--dpi n] [--json]` | Print-ready PDF from JSON (exit 0 ok, 2 template errors, 3 placeholders or SAMPLE left under `--final`) |
| `node render/render-page.js <page.html> <out.pdf> [--png f]` | PDF of a static page (spec sheets, guides) |
| `bash render/build-pdfs.sh` | Rebuilds everything in `pdf/` and `specs/` |
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

## 12. Versions

v1.0, 2026-10-23 to 24: identity, tokens, tent card, case label, specs, tests (part 1). Part 2 appends here.
