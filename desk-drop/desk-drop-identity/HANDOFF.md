# Handoff: workstream D (identity and collateral)

Status 2026-10-24: parts 1 and 2 done, review round 1 answered (v1.2). Paths are relative to `desk-drop/`. Run every command from `desk-drop-identity/`. `tests/documents/doc-tests.js` fails when a legal file below changes version without D rechecking it: recheck the restated terms, then update the version and date in its row.

## What D consumes

| From | File | What D uses | Status on 2026-10-24 |
| --- | --- | --- | --- |
| Plan | `plan.md`: appendix G (card copy), appendix M and "Measurement and the brand report" (report), Phase 2 "The proposal", revised model and Phases 0 to 2 (one-pagers), Phase 3 kit and per-stop procedure | Contents of every piece | Used |
| CONTRACTS | section 3 calendar, section 4 enumerations, section 6 schemas | `system/dd-dates.js` (business days, holidays to 2027-09-30, blackouts, T offsets), category keys, headcount bands, field names | Used. Calendar output matches section 3 exactly for the campaign-zero drop Tue 2027-01-12 |
| G, legal | `desk-drop-legal-pack/01-name-check-log.md` (v0.7; rechecked 2026-10-24), short copy `name-check-log.md` (v0.6) | Print-run gate | **HOLD** (print run and public launch); private discovery go. Recommended: two fallback names checked by Fri 2026-11-13, the name chosen at the attorney hour Wed 2026-11-18 (derived) |
| G, legal | `desk-drop-legal-pack/02-email-footer-and-checklist.md` (v0.6; rechecked 2026-10-24) | Footer B, read verbatim at build time by `render/build-signature.js` into `signature/signature-outreach.*` and `system/signature-footer.js` (for `details.html`) | Used. The signature shows name, company, [PHONE] and [POSTAL ADDRESS], as Footer B requires |
| G, legal | `desk-drop-legal-pack/03-office-participation-agreement.md` (v0.8; rechecked 2026-10-24) | Office one-pager: what the office does (placement, a photo the day it is placed and one on day 3 or 5, the survey post, the debrief, headcount), veto, a week's notice, naming only by tick box, no fees | Used. The one-pager drops the plan's "first drop within four weeks of signing", as file 03 does, and names the drop week instead |
| G, legal | `desk-drop-legal-pack/10-brand-campaign-agreement.md` (v0.8; rechecked 2026-10-24) | Price and terms in the proposal and brand one-pager: founding paid within five business days of the invoice and before shipping; the lock at $120 per office for up to 10 offices (more at $150); standard 50% on signing, 50% on the placement confirmation (our email by T+1 listing each placed office with its photo; an office not placed comes off the invoice); cancellation before T−10 (the date printed), 50% after, full price from the drop day; slip rule; certificate; card text approved before printing; eye level "where the pantry allows" | Used; numbers in `system/dd-offer.js` (`lock_max_offices` added) |
| G, legal | `desk-drop-legal-pack/13-survey-privacy-notice.md` (v0.6; rechecked 2026-10-24) | Office one-pager privacy text; report comment rule D10 (replace names with "[name removed]") | Used |
| B, cluster map | `cluster-1-flatiron/public-map.png` / `.svg`, `retailers.csv` | The proposal's retailer map slot | **Tested, the portrait map does not fit as is.** The public map is a 1200 x 2140 portrait for all stores; in a proposal column it prints as a thumbnail (`desk-drop-identity/tests/proposal-map/`). **Request to B (still open):** a per-brand landscape export, about 2.5 to 1 (for example 1050 x 420 px, or SVG), showing the cluster boundary and that brand's stores, **with no office pins before the brand signs** (a pin can identify a company). B's HANDOFF says a brand-specific map is made by filtering `retailers.csv` and re-running `_build/public_map.py`. A landscape map of that shape now fits with up to 12 offices and four stores (`tests/documents/cases/proposal-*.json`, drawn with D's own SAMPLE map `tests/proposal-map/SAMPLE-landscape-map.png`). The template shows a map whole and warns on a portrait picture |
| C, website | `website/` | A provisional design system to audit | None attached. C's log says it imports D's tokens, wordmark and avatar; nothing to adopt or replace. D's system stands |
| E, outreach; F, operations | `desk-drop-outreach/`, `campaign-ops/` | Rows to fill the templates (CONTRACTS 6.4, 6.5) | Folders empty on 2026-10-24. The templates take JSON in the shapes below |

## What D feeds

### To C (website)

| File | Contents |
| --- | --- |
| `desk-drop-identity/tokens/tokens.css`, `tokens.json` | Colors, type families and weights, type scale, spacing `--dd-space-0..9`, radii, rules, dark mode, `.dd-brand-name`. The Google Fonts link is in the header comment. Import directly |
| `desk-drop-identity/wordmark/wordmark-light.svg`, `wordmark-dark.svg` (and mono, stacked, symbol; PNGs in `wordmark/png/`) | Wordmark, outlined. Size by cap height (`wordmark-metrics.json`) |
| `desk-drop-identity/avatar/avatar-cobalt-*.png` (default), `avatar-*.svg` | Favicon and profile image source: the symbol alone, 40 to 1024 px |
| `desk-drop-identity/brand.json` | `BRAND_NAME`, `TAGLINE`, contact placeholders. C keeps its own `BRAND_NAME` but must match this value |
| `desk-drop-identity/SYSTEM.md` | Color roles, type roles, clear space, minimum sizes, print versus screen |

### To E (outreach)

| Piece | Template | PDF to attach | Notes for E |
| --- | --- | --- | --- |
| Discovery one-pager | `desk-drop-identity/templates/discovery-one-pager/discovery-one-pager.html` | `pdf/discovery-one-pager-BLANK.pdf` once the founder's details are filled (`details.html`) | Weeks 1 to 3. Five sentences, no selling. Attach to discovery emails or send after a call |
| Office one-pager | `templates/office-one-pager/office-one-pager.html` | made per office (`prepared_for`, `first_drop`) | Conversion step 2: "One-pager sent the same day with a specific proposed first-drop week". Status moves to `materials_sent` |
| Brand one-pager | `templates/brand-one-pager/brand-one-pager.html` | general, plus an optional `prepared_for` | `roster_status` must hold what is true that day (from `signed_offices.csv`) |
| Proposal | `templates/proposal/proposal.html` | made per brand | Within 24 hours of a qualifying call. Field mapping below. Status `materials_sent` |
| Email signature | `signature/signature.html` (everyday), `signature/signature-outreach.html` (cold email; includes Footer B); or copied straight from `details.html` | | Built from the founder's details by `system/dd-signature.js` (one builder for the terminal and Chrome paths); Gmail setup in `USAGE-GUIDE.md` section 13 (founder's login). Use the outreach version on every first touch and follow-up |

**Proposal field mapping** (JSON key: source). `brand_name`: `brand_intake.brand_name`. `product_sku`: `product_sku`. `prepared_for`: `contact_name`, `contact_title`. `category`: `category` (CONTRACTS section 4 key). `tier`: `founding` or `standard`. `extra_offices`: number. `drop_date`: proposed, `YYYY-MM-DD` (copy may use the slot `[DROP DATE: Tue 2027-01-12]`; the proposal then prints every derived date as a highlighted slot). `ship_by_requested`: optional. `offices[]`: one per office on the route from `signed_offices`, with `neighborhood`, `industry`, `headcount_band`, `planned_units`, **no company names**; at most 12. `retailers[]`: `retailer_name`, `street`, `distance`, only stores with evidence (`retailers.csv` grade `store_selector` or `brand_claim`, or the founder's `seen_on_shelf`). `online_site`: from `online_store_url`. `map_image`, `map_caption`: from B (above). Full rules: `templates/proposal/FIELDS.md`.

### To F (operations): templates F fills programmatically

| Template | Field list | Command |
| --- | --- | --- |
| Tent card `templates/tent-card/tent-card.html` | `templates/tent-card/FIELDS.md` (QR, allergen and retailer fields marked there) | `node render/render.js tent-card cards.json cards.pdf --final --json` |
| Case label `templates/case-label/case-label.html` | `templates/case-label/FIELDS.md` | `node render/render.js case-label labels.json labels.pdf --final --json` |
| Report `templates/report/report.html` | `templates/report/FIELDS.md` | `node render/render.js report report.json report.pdf --final --json` |

Exit codes for all three: 0 written, 1 usage or crash, 2 template refused (no PDF: does not fit, impossible numbers, bad date, missing picture file), 3 `--final` found placeholders, SAMPLE values or unfilled `brand.json` contacts. `--json` prints `{ ready, errors[], warnings[], sample, placeholders[], fit[], console_errors[], template, records }`.

**Report JSON** (one object per campaign). Campaign keys: `brand_name`, `product_sku`, `cluster`, `tier`, `campaign_id`, `drop_date`, `report_date`, `prepared_by`. `offices[]`, one object per office, using CONTRACTS 6.5 names where they exist: `office_label` (A, B... or the name if the office agreed), `industry`, `headcount_band`, `units_delivered`, `units_placed`, `placed_within_1bd` (Y/N), `units_topped_up`, `units_depleted_day5`, `survey_responses`, `qr_scans`, `placement_photo`, `later_photo` (paths relative to the JSON file; empty = "No photo received"), `later_photo_day` (3 or 5). Survey keys: `survey_tried_yes`, `tried_no_didnt_see`, `tried_no_not_for_me`, `tried_no_gone`, `survey_rating_avg`, `survey_rating_n`, `survey_buy_yes`, `survey_buy_maybe`, `survey_buy_no`, `comments_total`, `comment_1` to `comment_3` (verbatim; names replaced with "[name removed]" per legal file 13 D10). Purchases: `code_redemptions_to_date`, `code_redemptions_as_of`, `retailer_velocity`. Founder text: `learned` (three lines), `recommendation`.

**How the report's totals map to `campaign_actuals.csv`:** `units_delivered` = sum of office `units_delivered`, the drop-day handover only (the ladder's Delivered and the roster total; **v1.2 correction**: top-ups are no longer added, because H uses `units_delivered` as the Gate 2 denominator against `units_placed_within_1bd`), `units_topped_up` = sum of office `units_topped_up`, kept separate, `units_placed` = sum of `units_placed`, `units_placed_within_1bd` = sum of `units_placed` where `placed_within_1bd` = Y (the report prints this over `units_delivered` as the Gate 2 share in the Placed rung), `units_depleted_day5`, `survey_responses`, `qr_scans` = sums; `survey_tried_yes` and `code_redemptions_day30` (at day 30) as entered; `report_delivered_date` = `report_date`. F's per-office tracker needs these per-office columns, which CONTRACTS does not yet define: `office_id`, `campaign_id`, `units_delivered`, `units_placed`, `placed_within_1bd`, `units_topped_up`, `units_depleted_day5`, `survey_responses`, `qr_scans`, `placement_photo_file`, `later_photo_file`, `later_photo_day`.

**Tent card field mapping** (v1.2): `brand_name` from `paid_brands.brand_name`; `brand_logo` (**new in v1.2**: the logo file the brand sends, `logo_received_date`; a path relative to the JSON; optional); `product_name` from `product_sku`; `card_sentences`; `allergen_source` (`contains_statement`, `ingredient_list` or `single_ingredient`, read from the package; **`none_on_label` was removed in v1.2 and is refused**); `allergen_line_verbatim`; `may_contain_verbatim`; `retailer_line`; `discount_code`; `code_site` (derived from `online_store_url`); `qr_url` (F generates one per office per campaign); `qr_display`; `office_id`; `campaign_id`.

**Case label field mapping** (unchanged): `office_name` from `signed_offices.company`; `office_address`, `floor_suite`; `deliver_to` from `pantry_owner_name`; `brand_name`; `product_name` from `product_sku`; `units_in_case` (F's packed count); `case_number`, `case_total`; `drop_date`, `office_id`, `campaign_id`, `drop_id`; `phone` (empty uses `brand.json`).

**Operations notes for F**
- Verify `allergen_line_verbatim` against the physical package at receiving (T minus 5). The Chrome panel asks for this tick; the command line cannot, so F's kitting checklist should.
- A card warning containing "left off", "too long to share a face" or "other side" means the card changed shape; show it to the founder. `fit[i].ingredients_on_front_face = true` means the front carries the whole ingredient list and is marked "this side faces the room": the kitting checklist should say so for that office.
- Messages start with "Card N: " (or "Label N: ") only when a file holds more than one record.
- A report warning "under the five the office committed to" is a fact for the debrief, not an error.
- Photos must show no identifiable people; the Chrome panel asks for this tick before printing the report.

### To G (legal) and H (financial model)

- G: the proposal and brand one-pager restate agreement v0.8 terms (price, founding lock, payment timing and placement confirmation, the per-office refund, cancellation, slip). If G changes a term, change `desk-drop-identity/system/dd-offer.js` (numbers) or the proposal's and brand one-pager's fixed sentences, then `bash render/build-pdfs.sh`, then update the version and date in the "What D consumes" table (the document test enforces it).
- H: prices in `dd-offer.js` match the plan ($600 for 5 founding, $1,500 for 10 standard, $150 extra). Print cost assumption unchanged from the plan ($1 to $2 a card in runs of 20; the plan's $8 a kit per office). No new figures from D.

## Deviations from CONTRACTS

1. Tent card: adds `allergen_source`, `may_contain_verbatim` (new columns beside `allergen_line_verbatim`), `brand_logo` (v1.2) and `code_site` (derived). Producers may add columns; without them the template still works.
2. Report: needs per-office columns that CONTRACTS section 6.5 does not define (listed above); totals map onto `campaign_actuals.csv` unchanged.
3. Placeholders: templates also recognize bracketed slots with lowercase text after a colon, such as `[DROP DATE: Tue 2027-01-12]`, as section 3 asks; a proposal built on a slot prints every derived date as a slot (`[DATE: Mon 2026-12-28]`).
4. SAMPLE marking: every invented name, ID and free-text value starts with SAMPLE; generic category words in the proposal samples (neighborhood, industry) do not, and the documents carry the SAMPLE banner.
5. Founder contacts can also live in `system/brand.js`, saved by `details.html` in Chrome; `render/brand-sync.js` copies them into `brand.json` at the next terminal build, so `brand.json` stays the one place a terminal user edits. `BRAND_NAME` is only ever taken from `brand.json`.
6. `REPORT.md` is pending: the harness refuses report-file writes from the builder, so its full text is in the builder's returned message (review round 1) for the orchestrator to save. Until then, `tests/README.md` holds the test results and `_review/round-1.md` the answers to the review.
7. No other deviations. Folder, README, HANDOFF, ladder words, `BRAND_NAME` and `TAGLINE` follow CONTRACTS.
