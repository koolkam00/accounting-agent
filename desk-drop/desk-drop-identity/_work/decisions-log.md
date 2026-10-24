# Working log, workstream D part 1 (scratch, kept)

Started 2026-10-23. This file is my running notebook so nothing is lost on context compaction.

## Early decisions (round 0, before drafting)
- Card orientation: landscape faces, 7 in wide x 5 in tall, tent fold. Flat sheet 7 x 10 in fits one US Letter sheet with margins, so it prints at home. Both faces identical, back rotated 180 deg.
- Name lives in brand.json (BRAND_NAME, TAGLINE). A build script regenerates wordmark SVG/PNG and system/brand.js. File names never contain the working name.
- Wordmark = name outlined to SVG paths + a name-independent symbol ("box on a shelf": square over a bar). Symbol alone is the avatar, so the avatar survives a rename.
- Fonts (to verify on Google Fonts): Bricolage Grotesque (display, has width axis for long names), Atkinson Hyperlegible Next (body, allergen line; designed for low-vision legibility).
- Template mechanics: editable HTML + fill-in panel + inline JSON block; node+Playwright render script takes a JSON path (object or array) -> PDF. QR generated client-side by a vendored MIT library so Chrome printing works offline.
- Allergen block: locked size, never auto-shrinks; other elements shrink to fit; if still too long the template shows a blocking error and the render script exits non-zero.
- Print: no bleed at home; white paper is the background, never a flood of cream. Commercial PDF mode adds 0.125 in bleed.

## Tooling notes
- fontTools not installed; using opentype.js (MIT, vendored) in node for outlining text.
- pypi and npm registry are reachable directly.

## Round 1 (draft tent card) and test results, 2026-10-23
- R1 draft: landscape 7x5 face, name top, story+CTA/QR middle, boxed allergen panel, find-it + "Brought to you by" footer. Fit loop shrinks story, QR, name; allergen locked.
- Critique R1: "Tell us what you / think" bad break; extreme long name blocked even after dropping story; QR shrank before spacing did; product line never gave way; thin cobalt rule invisible in wide photo.
- R2 fixes: forced break "Tell us what / you think"; give-way order story -> tight gaps -> find 10pt -> QR -> two-line name back to one condensed line -> name size -> drop product -> drop story -> block with DO NOT PLACE overlay; cobalt band 0.07 -> 0.12 in.
- Wide pantry sim (24 px/in, card ~112 px tall at native 2880 px): name identifiable for basic and long-name (condensed). At report size (1440 px, card ~56 px) basic name still legible.
- Downscale test: faces at 120 px tall all identifiable; at 60 px, 33-char name marginal -> guide says use the short brand name, 24 chars or fewer ideal.
- Close photo sim (60 cm, 26 mm-eq lens, 123 px/in at 4032 px): allergen 25-word + may-contain at 14 pt semibold legible at 4032, 2048 and (zoomed) 1280 px. Sweep: 11 pt fails at 1280, 12 pt marginal, 13 pt passes, 14 pt passes with margin -> LOCK 14 pt.

## Round 3 (2026-10-24)
- Found: Vistaprint table tents are 5x7 vertical only, min 10 per design. Per-office unique QR means each office's card is a different design, so online tent-card products are a poor fit (10 offices x 10 min = 100 cards). Decision: keep landscape 7x5 for home or copy-shop printing of the Letter PDF (one card per page = variable data for free). Portrait variant listed as an open option, not built.
- Added guards: allergen size lock enforced in code (tamper test: tokens shrunk to 10pt -> exit 2), verbatim check (innerText vs input, special chars and line breaks pass), panel-cut-off check.
- Case label: reserve care text, ID no-wrap, banner inside printable area, [PHONE] from brand.json counted as a placeholder for --final.
- Wordmark sized by cap height everywhere (DD.wordmarkImg) after two-line name test showed tiny letters at fixed box height.
- QR decode (jsQR in scratchpad, test only): decodes from renders and simulated close photos at 4032 and 2048 px; fails at 1280 px and in the wide shot (not required).

## Round 4 (2026-10-24), food-safety pass
- Built-in default data was an unmarked sample (allergen text without SAMPLE): hazard. Default is now the blank form; all sample values start with SAMPLE.
- Added allergen_source (contains_statement | ingredient_list | none_on_label), fixed pointer text for none, ingredients-on-the-other-face fallback for long ingredient-only lists (front capacity ~50 caps words incl. may-contain; back ~85).
- Panel: grey hints instead of bracket text; plain status messages; allergen check tick before Chrome print; select input; "may contain empty" warning.

## Round 5 (2026-10-24), print-shop pass
- Variable fonts embedded as Type 3 -> static instances (CID TrueType). Google Fonts API only serves named widths (75, 87.5, 100), so case label narrows to 87.5% not 80%.
- Lazy font loading made first width measurement use a fallback font -> runtime loads every FontFace before fitting.
- --mode pro page size was Letter -> @page injected for pro (7.25 x 10.25).
- Full suite 25/25 pass. REPORT.md write was refused by the harness (subagents return reports as text), so the part-1 report is returned to the orchestrator in the final message.
