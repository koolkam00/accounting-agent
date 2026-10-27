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

# Part 2 (documents, signature, avatar), started 2026-10-24

## Round 0 decisions (before drafting)
- Every new document is a data-driven HTML template on the part-1 runtime (fill-in panel, JSON block, render.js), so the founder edits in Chrome with no design tool. Canva/Figma: no logins; HTML is the editable source and the PDF is the output.
- Copy blocks of the one-pagers are panel fields (grouped "Copy"), so the founder can change words without touching code; every document checks it still fits on its page and refuses to print if not.
- dd-template.js gains a `table` field type (rows x columns grid with add/remove) for the proposal roster, retailer list and report roster; scan() goes deep into arrays for placeholders and SAMPLE values.
- Shared modules: system/dd-docs.css (Letter document layout), system/dd-dates.js (CONTRACTS section 3 business days, holidays, blackouts), system/dd-report.js (the one report renderer, used by report.html and by the proposal's mock page so the mock is exactly the real layout).
- Report is one page; photo thumbnails on it; full-size photos on an optional evidence appendix page (assumption).
- Survey numbers entered as counts; template computes shares and always prints counts beside percentages.
- Limitations paragraph is fixed in code (not a field), checked present on every render.
- Signature and avatar generated from brand.json and the symbol by build scripts (rename = rebuild). Signature: text-only default (no image hosting needed), logo variant for when [DOMAIN] hosts the PNG; outreach variant appends the legal pack's Footer B line, read from desk-drop-legal-pack/02-email-footer-and-checklist.md at build time.
- Web search budget for the run is exhausted; direct page fetches used: Gmail signature limit 10,000 characters (support.google.com/mail/answer/8395), LinkedIn Page logo 400x400 recommended, 268x268 minimum (linkedin.com/help/linkedin/answer/a563309), Slack profile photo 512x512 minimum, 1024x1024 maximum (slack.com/help/articles/115005506003). All opened 2026-10-24.

## Round 1 (draft) and round 2 (critique and fix), 2026-10-24
- R1 report: blank render showed rung hints claiming "5 of 5 offices within one business day" and "0 of 5 reached five" with no data (quiet false numbers), "Not measured" overflowing, window printed as a plain date though derived from a slot. Fixed: per-office claims only when counts are known; [Y/N] and [PHOTO] placeholders; derived dates shown as slots.
- R1 report, 10 offices + three 75-word comments: overflowed by 300 px. Causes: roster header wrapping to 3 lines, ladder hints 5 lines, title meta 2 lines. R2: fixed-width roster with 2-line headers, compact ladder, tighter fixed limitations paragraph (same rungs, same limits), 0.45/0.4 in margins on the report only, one-line engagement line, last-resort give-way moves thumbnails to the evidence page (page 1 keeps the count of photos received). Never shrunk: numbers, ladder, comment words, limitations. Now fits at comments 8.25 pt.
- Photo slots: "[PHOTO]" = not attached yet (placeholder); empty = "No photo received" (reported, warned, never hidden).
- R1 proposal: grid rows left 2 in of dead space and overflowed 184 px. R2: two free-flowing columns, report summary full width, cancellation/slip terms under the timeline, one-line footer. Timeline slots shortened to [DATE: ...]. Fits for 5 and 10 offices and blank.
- Mock page side label rotated through the content: switched to vertical writing-mode in the margin.
- Office one-pager R1 245 px over (said everything twice). R2: four short steps, card drawing with one-line caption, privacy and product stacked beside the founding box. Found a grid bug: `.sec + .sec` margin applied inside grids, offsetting every second column; fixed in dd-docs.css.
- Brand one-pager R1 210 px over. R2: smaller title, never-promise box beside price, exclusions under "You send", rung texts 3 lines, card drawing removed (described in "includes"; drawn on the office one-pager).
- Prices moved to system/dd-offer.js (one edit for a price change; plan says prices are hypotheses).
- Discovery: exactly-five-sentences check and selling-words warning; negative sample proves both fire.
- Bug: brand.json contact placeholders printed yellow but were not counted, so --final would pass a document with no phone number. DD.contact now counts them.

## Round 3 (2026-10-24): signature, avatar, spec, guide, tests, harsh review
- Signature: separators orphaned at phone width; each item now nowrap with its separator. Footer B read from the legal pack at build time. Placeholders yellow in the HTML.
- Avatar: ink variant vanishes on dark app backgrounds, paper loses its edge on white; cobalt chosen as default after the 40 px test sheet.
- Documents spec first draft overflowed both pages (footer over the last table): split into three pages. Spec footers hard-coded the name: removed.
- Swap test (new brand, ingredient-list-only drink, code-only buy path): passed at 8 min 24 s by the stated model, but showed (a) the guide's "next office" line did not say the allergen box unticks after Load JSON, (b) section 2 carried the trouble table, read only on trouble. Fixed both; 7 min 27 s.
- Doc test suite: first run 9 failures, all in the harness (temp JSON broke relative photo paths, which the missing-picture guard correctly refused; -layout text interleaved columns). Fixed the harness, not the templates. 53 checks pass.
- Harsh review: "gone" used instead of the ladder word "depleted" in the proposal and discovery page: replaced. Brand founder: added "You approve the card text before we print" (campaign agreement section 1). Bullets sat low: sized in em. Blank report showed "No photo received" because its sample predated [PHOTO]: regenerated, and a test now fails if any BLANK sample drifts from its template. Proposal columns rebalanced (terms note moved left) so every variant fits without shrinking type.

## Round 4 (2026-10-24): integration with other workstreams
- B's public-map.png (1200 x 2140 portrait, all stores) tested in the proposal's map slot: prints as a thumbnail. Maps are now shown whole (object-fit contain, height from the picture's own shape, warning on a portrait). Asked B (HANDOFF) for a per-brand landscape export.
- Honest-operator catch: the map slot asked for "these offices marked"; a pin can identify a company before signature. Rule changed: cluster and the brand's stores only, no office pins before signing.
- Legal file 13 rule D10 (names in comments become "[name removed]") contradicted the report's "never edit a comment"; aligned report note, panel help, FIELDS and guide. "[name removed]" is not read as a placeholder.
- C (website) has no provisional system and imports D's tokens: nothing to audit; D's system stands.
- REPORT.md write refused by the harness again; the report goes to the orchestrator in the returned message.

# Review round 1 response (2026-10-24), builder
Reviewer file: _review/round-1.md (3 blockers, 8 majors, 7 minors). Plan of work, in order:
R1-02 brand one-pager fit with real contacts; R1-03 proposal standard+map; R1-04 report photos on page 1;
R1-10/18 Delivered = handoff only, placed share in units; R1-12 limitations sentence; R1-07 mock page;
R1-06 payment trigger and lock per agreement v0.7; R1-13 cancel date; R1-05 office promise;
R1-08 split mode faces; R1-09 logo slot; R1-14 name give-way; R1-15 no "Nowhere"; R1-17 case label picker;
R1-11 Chrome-only contacts (system/details.html); R1-16 guide photos; tests for every case; REPORT.md.
- Done so far (review round 1): runtime v1.2 (record picker, plain single-record messages, DD.placeholder, logo pictures);
  report: Delivered = handoff only, Placed hint unit share (Gate 2), 6+ offices get a photo strip (day 1 row, later row),
  give-way moves later photos to page 2 before the strip, run-in Survey/Evidence/Limitations, learned+rec side by side,
  limitations first sentence now "Each number is a separate step, counted as stated." (frozen file updated);
  proposal: column arrangement fitter (send left/right, two-up roster full width), 12-office max, payment trigger and lock
  per agreement v0.7, cancel date printed (T-10), mock page uses the brand's own name/drop date and grey examples;
  brand one-pager: five give-way steps, contact on its own line, compact "Not for", dates never break;
  office one-pager: four-week promise removed, photo ask aligned with file 03 and the report slots.
  Measured fits: report 10 offices both photo rows (builder sample), 12 offices and 10+velocity keep the day-1 strip,
  longtext/10-max move photos (last resort). Proposal 10/11/12 offices + map + 4 stores fit; founding + map + 4 stores fit.
- Tent card v1.2: logo slot (wide logo replaces the typed name, compact logo sits beside it; logo 0.9 to 0.55 in first in the
  give-way); "Nowhere" removed (single_ingredient copies the product's name; none_on_label is refused); split mode puts the
  whole ingredient list on the FRONT ("this side faces the room"), story and QR on the other face; give-way now drops the
  product line before the name shrinks, and re-widens the name at each size. Case label and tent card get a record picker.
- details.html: Chrome-only details (download brand.js, copy signatures), system/dd-signature.js shared with build-signature,
  render/brand-sync.js copies details saved from Chrome into brand.json on the next terminal build.
- Proposal: tries six arrangements each with its give-way (terms right, two-up roster, three-up roster with neighborhoods
  line for 9+, timeline strip); all 10/11/12-office map cases and founding+map fit with blank, real-length and long details.
  Payment and eye-level wording follow agreement v0.8 (founding paid within five business days of the invoice).
