# Identity and collateral (workstream D)

Everything the founder needs to look consistent and print the in-office pieces without a designer. Part 1 (this version, 2026-10-24) covers the identity system, the tent card and the case label. Part 2 adds the documents (office and brand one-pagers, discovery one-pager, proposal, report template, email signature, avatar) and completes this README.

**Name status:** "Desk Drop" is a working name. The legal pack (`../desk-drop-legal-pack/name-check-log.md`, 2026-10-23) puts any print run on HOLD and recommends picking a fallback name. Home test prints are fine. A rename here is one edit to `brand.json` plus one command (see "Rename" below).

## Start here

1. Read `USAGE-GUIDE.md` (how to make, print, fold and place a card; labels; logo use; renaming; ordering a print run).
2. Open `templates/tent-card/tent-card.html` in Google Chrome and follow guide section 2.
3. Look at `pdf/tent-card-SAMPLE-face.png` and `pdf/case-label-SAMPLE.png` to see what finished pieces look like.

## Files, in the order you will use them

| File or folder | What it is | How to edit |
| --- | --- | --- |
| `USAGE-GUIDE.md` | Step-by-step guide for a non-designer | Text editor |
| `brand.json` | The one place the name, tagline and your contact placeholders live (`[PHONE]` and so on) | Text editor, then `node render/build-brand.js` |
| `templates/tent-card/tent-card.html` | The 5 x 7 in tent card template, with a fill-in panel | Open in Chrome and type; or edit its JSON block; or render from JSON (below) |
| `templates/tent-card/FIELDS.md` | Every card field, its source column and its rule (for the operations workstream) | |
| `templates/tent-card/samples/` | `BLANK-placeholders.json` (empty card) and `SAMPLE-*.json` test cards | Copy one as a starting point |
| `templates/case-label/case-label.html` | Case label, 8.5 x 5.5 in, two per Letter sheet | Same as the card |
| `templates/case-label/FIELDS.md`, `samples/` | Label fields and samples | |
| `specs/tent-card-spec.pdf` | Print spec: size, fold, bleed, safe area, stock, every type size, give-way order, placement and photo rules, test results | Source `specs/tent-card-spec.html`, rebuild with `bash render/build-pdfs.sh` |
| `specs/case-label-spec.pdf` | Print spec for the label | Same |
| `pdf/tent-card-BLANK.pdf`, `pdf/case-label-BLANK.pdf` | The empty templates as PDFs (placeholders highlighted) | Rebuilt by `build-pdfs.sh` |
| `pdf/tent-card-SAMPLE-*.pdf`, `pdf/case-label-SAMPLE.pdf` | Filled SAMPLE examples: home print (Letter with crop and fold marks), print-shop file with bleed, a 5-office batch, the 25-word allergen test | Same. Never place a SAMPLE card |
| `wordmark/` | Wordmark and symbol: `wordmark-light.svg` (on white), `wordmark-dark.svg` (on dark), `wordmark-mono-ink.svg`, `wordmark-mono-white.svg`, `wordmark-stacked-*.svg`, `symbol-*.svg`; PNGs in `wordmark/png/` at several widths, transparent and on white or ink; `wordmark-metrics.json` | Generated. Never hand-edit; change `brand.json` and rebuild |
| `tokens/tokens.css`, `tokens/tokens.json` | Colors, type, spacing, radii (the website imports `tokens.css`) | Edit both, then `node tests/check-tokens.js` |
| `fonts/` | Bricolage Grotesque and Atkinson Hyperlegible Next with their OFL license files; `fonts.css` (print, static files), `fonts-variable.css` | Do not edit |
| `SYSTEM.md` | The rules of the system: color, type, spacing, wordmark, grids, components, template mechanics, render pipeline | For whoever extends the system |
| `HANDOFF.md` | What this folder feeds the website, outreach and operations workstreams | |
| `REPORT.md` | Report back: deliverables, choices, assumptions, changelog, tests, questions. Part 1's report was returned to the orchestrator as text (this session could not write report files); it saves it here | |
| `render/` | `build-brand.js` (wordmark from `brand.json`), `render.js` (JSON to PDF), `render-page.js` (static page to PDF), `build-pdfs.sh` (rebuild everything) | |
| `system/` | Template runtime (`dd-template.js`, `dd-print.css`), generated `brand.js`, vendored MIT libraries (QR codes, font outlines) with licenses | |
| `tests/` | Every test, its outputs and `tests/README.md` with results | `bash tests/run-all.sh` |
| `package.json` | Lists Playwright for the terminal commands | `npm install` once |
| `_work/` | Working notes and sources (kept, not needed day to day) | |

## Commands (optional; Chrome alone is enough for one card)

Install once: Node 18 or newer (nodejs.org), then in this folder `npm install` and `npx playwright install chromium`. Both free.

```bash
node render/render.js tent-card cards.json cards.pdf --final     # one card per office, print-ready
node render/render.js case-label labels.json labels.pdf --final  # two labels per sheet
bash render/build-pdfs.sh                                        # rebuild every PDF and the wordmark
bash tests/run-all.sh                                            # run the tests
```

## Rename

Edit `BRAND_NAME` in `brand.json`, run `bash render/build-pdfs.sh`, then find-and-replace the old name in the `.md` files here. Details: `USAGE-GUIDE.md` section 8.

## Ordering a print run

Only after the name is cleared. Each office's card is its own design (its own QR), so print the same one-card-per-page Letter PDF at home or at a copy shop on 80 to 110 lb matte cover stock, at 100% scale. A print shop that wants bleed gets the `--mode pro` file. Fixed-size online table tents (for example Vistaprint: 5 x 7 in vertical only, from 10 per design; page opened 2026-10-24) do not fit one design per office. Full steps: `USAGE-GUIDE.md` section 9. No spending without the founder's written yes.
