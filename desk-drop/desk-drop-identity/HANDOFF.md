# Handoff: workstream D (identity and collateral)

Status 2026-10-24: parts 1 and 2 done (v1.1). Paths are relative to `desk-drop/`. Run every command from `desk-drop-identity/`.

## What D consumes

| From | File | What D uses | Status on 2026-10-24 |
| --- | --- | --- | --- |
| Plan | `plan.md`: appendix G (card copy), appendix M and "Measurement and the brand report" (report), Phase 2 "The proposal", revised model and Phases 0 to 2 (one-pagers), Phase 3 kit and per-stop procedure | Contents of every piece | Used |
| CONTRACTS | section 3 calendar, section 4 enumerations, section 6 schemas | `system/dd-dates.js` (business days, holidays to 2027-09-30, blackouts, T offsets), category keys, headcount bands, field names | Used. Calendar output matches section 3 exactly for the campaign-zero drop Tue 2027-01-12 |
| G, legal | `desk-drop-legal-pack/name-check-log.md` (v0.5) | Print-run gate | **HOLD** (print run and public launch); private discovery go. Fallback-name decision recommended by Fri 2026-11-13 |
| G, legal | `desk-drop-legal-pack/02-email-footer-and-checklist.md` | Footer B, read verbatim at build time by `render/build-signature.js` into `signature/signature-outreach.*` | Used. The signature shows name, company, [PHONE] and [POSTAL ADDRESS], as Footer B requires |
| G, legal | `desk-drop-legal-pack/10-brand-campaign-agreement.md` (v0.6; every restated term rechecked 2026-10-24) | Price and terms in the proposal and brand one-pager: founding lock, payment timing, cancellation before or after T-10, slip rule, certificate, card text approved before printing | Used; numbers in `system/dd-offer.js` |
| G, legal | `desk-drop-legal-pack/13-survey-privacy-notice.md` | Office one-pager privacy text; report comment rule D10 (replace names with "[name removed]") | Used |
| B, cluster map | `cluster-1-flatiron/public-map.png`, `retailers.csv` | The proposal's retailer map slot | **Tested, does not fit as is.** The public map is a 1200 x 2140 portrait for all stores; in a proposal column it prints as a thumbnail (`desk-drop-identity/tests/proposal-map/`). **Request to B:** a per-brand landscape export, about 2.5 to 1 (for example 1050 x 420 px, or SVG), showing the cluster boundary and that brand's stores, **with no office pins before the brand signs** (a pin can identify a company). The template shows a map whole and warns on a portrait picture |
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
| Discovery one-pager | `desk-drop-identity/templates/discovery-one-pager/discovery-one-pager.html` | `pdf/discovery-one-pager-BLANK.pdf` once `brand.json` is filled | Weeks 1 to 3. Five sentences, no selling. Attach to discovery emails or send after a call |
| Office one-pager | `templates/office-one-pager/office-one-pager.html` | made per office (`prepared_for`, `first_drop`) | Conversion step 2: "One-pager sent the same day with a specific proposed first-drop week". Status moves to `materials_sent` |
| Brand one-pager | `templates/brand-one-pager/brand-one-pager.html` | general, plus an optional `prepared_for` | `roster_status` must hold what is true that day (from `signed_offices.csv`) |
| Proposal | `templates/proposal/proposal.html` | made per brand | Within 24 hours of a qualifying call. Field mapping below. Status `materials_sent` |
| Email signature | `signature/signature.html` (everyday), `signature/signature-outreach.html` (cold email; includes Footer B) | | Built from `brand.json`; Gmail setup in `USAGE-GUIDE.md` section 13 (founder's login). Use the outreach version on every first touch and follow-up |

**Proposal field mapping** (JSON key: source). `brand_name`: `brand_intake.brand_name`. `product_sku`: `product_sku`. `prepared_for`: `contact_name`, `contact_title`. `category`: `category` (CONTRACTS section 4 key). `tier`: `founding` or `standard`. `extra_offices`: number. `drop_date`: proposed, `YYYY-MM-DD` (copy may use the slot `[DROP DATE: Tue 2027-01-12]`; the proposal then prints every derived date as a highlighted slot). `ship_by_requested`: optional. `offices[]`: one per office on the route from `signed_offices`, with `neighborhood`, `industry`, `headcount_band`, `planned_units`, **no company names**. `retailers[]`: `retailer_name`, `street`, `distance`, only stores with evidence (`retailers.csv` grade `store_selector` or `brand_claim`, or the founder's `seen_on_shelf`). `online_site`: from `online_store_url`. `map_image`, `map_caption`: from B (above). Full rules: `templates/proposal/FIELDS.md`.

### To F (operations): templates F fills programmatically

| Template | Field list | Command |
| --- | --- | --- |
| Tent card `templates/tent-card/tent-card.html` | `templates/tent-card/FIELDS.md` (QR, allergen and retailer fields marked there) | `node render/render.js tent-card cards.json cards.pdf --final --json` |
| Case label `templates/case-label/case-label.html` | `templates/case-label/FIELDS.md` | `node render/render.js case-label labels.json labels.pdf --final --json` |
| Report `templates/report/report.html` | `templates/report/FIELDS.md` | `node render/render.js report report.json report.pdf --final --json` |

Exit codes for all three: 0 written, 1 usage or crash, 2 template refused (no PDF: does not fit, impossible numbers, bad date, missing picture file), 3 `--final` found placeholders, SAMPLE values or unfilled `brand.json` contacts. `--json` prints `{ ready, errors[], warnings[], sample, placeholders[], fit[], console_errors[], template, records }`.

**Report JSON** (one object per campaign). Campaign keys: `brand_name`, `product_sku`, `cluster`, `tier`, `campaign_id`, `drop_date`, `report_date`, `prepared_by`. `offices[]`, one object per office, using CONTRACTS 6.5 names where they exist: `office_label` (A, B... or the name if the office agreed), `industry`, `headcount_band`, `units_delivered`, `units_placed`, `placed_within_1bd` (Y/N), `units_topped_up`, `units_depleted_day5`, `survey_responses`, `qr_scans`, `placement_photo`, `later_photo` (paths relative to the JSON file; empty = "No photo received"), `later_photo_day` (3 or 5). Survey keys: `survey_tried_yes`, `tried_no_didnt_see`, `tried_no_not_for_me`, `tried_no_gone`, `survey_rating_avg`, `survey_rating_n`, `survey_buy_yes`, `survey_buy_maybe`, `survey_buy_no`, `comments_total`, `comment_1` to `comment_3` (verbatim; names replaced with "[name removed]" per legal file 13 D10). Purchases: `code_redemptions_to_date`, `code_redemptions_as_of`, `retailer_velocity`. Founder text: `learned` (three lines), `recommendation`.

**How the report's totals map to `campaign_actuals.csv`:** `units_delivered` = sum of office `units_delivered` plus `units_topped_up` (the ladder's Delivered), `units_placed` = sum of `units_placed`, `units_placed_within_1bd` = sum of `units_placed` where `placed_within_1bd` = Y, `units_topped_up`, `units_depleted_day5`, `survey_responses`, `qr_scans` = sums; `survey_tried_yes` and `code_redemptions_day30` (at day 30) as entered; `report_delivered_date` = `report_date`. F's per-office tracker needs these per-office columns, which CONTRACTS does not yet define: `office_id`, `campaign_id`, `units_delivered`, `units_placed`, `placed_within_1bd`, `units_topped_up`, `units_depleted_day5`, `survey_responses`, `qr_scans`, `placement_photo_file`, `later_photo_file`, `later_photo_day`.

**Tent card field mapping** (unchanged from part 1): `brand_name` from `paid_brands.brand_name`; `product_name` from `product_sku`; `card_sentences`; `allergen_source` (**new**: `contains_statement`, `ingredient_list` or `none_on_label`, read from the package); `allergen_line_verbatim`; `may_contain_verbatim` (**new**); `retailer_line`; `discount_code`; `code_site` (derived from `online_store_url`); `qr_url` (F generates one per office per campaign); `qr_display`; `office_id`; `campaign_id`.

**Case label field mapping** (unchanged): `office_name` from `signed_offices.company`; `office_address`, `floor_suite`; `deliver_to` from `pantry_owner_name`; `brand_name`; `product_name` from `product_sku`; `units_in_case` (F's packed count); `case_number`, `case_total`; `drop_date`, `office_id`, `campaign_id`, `drop_id`; `phone` (empty uses `brand.json`).

**Operations notes for F**
- Verify `allergen_line_verbatim` against the physical package at receiving (T minus 5). The Chrome panel asks for this tick; the command line cannot, so F's kitting checklist should.
- A card warning containing "left off" or "other face" means the card changed shape; show it to the founder.
- A report warning "under the five the office committed to" is a fact for the debrief, not an error.
- Photos must show no identifiable people; the Chrome panel asks for this tick before printing the report.

### To G (legal) and H (financial model)

- G: the proposal and brand one-pager restate agreement v0.6 terms (price, founding lock, payment timing, cancellation, slip). If G changes a term, change `desk-drop-identity/system/dd-offer.js` (numbers) or the proposal's fixed sentence, then `bash render/build-pdfs.sh`.
- H: prices in `dd-offer.js` match the plan ($600 for 5 founding, $1,500 for 10 standard, $150 extra). Print cost assumption unchanged from the plan ($1 to $2 a card in runs of 20; the plan's $8 a kit per office). No new figures from D.

## Deviations from CONTRACTS

1. Tent card: adds `allergen_source` and `may_contain_verbatim` (new columns beside `allergen_line_verbatim`) and `code_site` (derived). Producers may add columns; without them the template still works.
2. Report: needs per-office columns that CONTRACTS section 6.5 does not define (listed above); totals map onto `campaign_actuals.csv` unchanged.
3. Placeholders: templates also recognize bracketed slots with lowercase text after a colon, such as `[DROP DATE: Tue 2027-01-12]`, as section 3 asks; a proposal built on a slot prints every derived date as a slot (`[DATE: Mon 2026-12-28]`).
4. SAMPLE marking: every invented name, ID and free-text value starts with SAMPLE; generic category words in the proposal samples (neighborhood, industry) do not, and the documents carry the SAMPLE banner.
5. No other deviations. Folder, README, REPORT, HANDOFF, ladder words, `BRAND_NAME` and `TAGLINE` follow CONTRACTS.
