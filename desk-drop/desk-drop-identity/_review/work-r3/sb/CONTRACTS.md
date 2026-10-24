# Shared contracts for the eight workstreams

Every workstream agent reads this file after `plan.md` and its own prompt in `prompts/`. Order of authority: your prompt, then `plan.md`, then this file. This file fixes the handoff formats, folders, dates and conventions so the eight workstreams can run in parallel and still connect. If it conflicts with your prompt, follow the prompt and list the conflict in your REPORT.md.

## 1. Folders

All work lives under `desk-drop/` (the repository's `desk-drop` directory). Write only inside your own folder. Read anything.

| ID | Workstream | Prompt file | Output folder |
| --- | --- | --- | --- |
| A | Clay ICP tables | `prompts/A-clay-icp-tables.md` | `clay-icp-tables/` |
| B | Cluster map and seed lists | `prompts/B-cluster-map.md` | `cluster-1-flatiron/` |
| C | Website | `prompts/C-website.md` | `website/` |
| D | Brand identity and collateral | `prompts/D-identity-collateral.md` | `desk-drop-identity/` |
| E | Outreach engine | `prompts/E-outreach-engine.md` | `desk-drop-outreach/` |
| F | Operations and measurement system | `prompts/F-operations-measurement.md` | `campaign-ops/` (no company name in file, folder or link names) |
| G | Legal and admin pack | `prompts/G-legal-admin-pack.md` | `desk-drop-legal-pack/` |
| H | Financial model | `prompts/H-financial-model.md` | `financial-model/` |

Shared helpers live in `_shared/`. Raw research scratch files go in `<your folder>/_work/`, which is kept.

Every output folder must contain:
- `README.md`: every file, what it is for, how to edit it, in the order the founder uses it.
- `REPORT.md`: the exact "Report back" message your prompt asks for, including numbered assumptions, changelog by round and blocking questions, each with a recommended default.
- `HANDOFF.md`: what you consume from and feed to other workstreams, with file paths and column names. Say so where you deviate from this file.

## 2. Hard rules for every agent

- **Prepare, never execute.** Do not send email, post, sign up for accounts, buy, file, call or publish anything. Do not use Gmail, Calendar, Drive, Docs, Vercel, Supabase, PostHog, GitHub or any other connector tool that writes outside this folder. Read-only web research (WebSearch, WebFetch, `curl` GET) is allowed and expected.
- Do not run `git commit`, `git push` or any other git write. The orchestrator commits.
- **Invent nothing.** Every researched fact has a source URL and the date you opened it. A field you cannot confirm says `unknown`. A source you could not open is marked `unverified, founder to confirm`. Never set a field to a value that implies founder action, such as `seen_on_shelf` or `verified_on_foot`.
- Money: free tools only. If a step needs a paid plan, stop there, state the cost, and write the step down for the founder.
- Business contact data only: company names, business addresses, public titles and public business profiles. No personal emails or phones, home addresses, or anything about employees.
- Placeholders keep this exact form: `[FOUNDER NAME]`, `[PHONE]`, `[EMAIL]`, `[POSTAL ADDRESS]`, `[WEBSITE]`, `[DOMAIN]`. Use `[DOMAIN]` wherever a domain would go. The domain is not chosen yet.
- **Rename-ability.** The working name "Desk Drop" lives in one variable or config cell per deliverable (`BRAND_NAME` in code, a `company_name` config cell in sheets, one wordmark file for graphics). The tagline lives beside it as `TAGLINE` ("Emerging brands. Delivered to your workday.").
- **SAMPLE data.** Every sample ID and sample text starts with `SAMPLE`. Every output built on sample data carries a visible "SAMPLE" banner. Mock numbers in templates sit under the label "Illustrative placeholders, not results."
- **Ladder words.** Keep these rungs separate everywhere and never rename them softer: delivered, placed, depleted, responded (survey responses; "tried" is a survey answer), scanned, purchased (code redemptions), incremental (not measured; say so). No field, column or sentence called conversions, sales lift, ROI or acquisition.
- **Draft heading.** Legal-adjacent text (agreements, privacy notes, footers, form notices) carries "Draft for attorney review. Not legal advice." until an attorney clears it.
- **Plain style.** Short sentences, plain words, no hype, no fake testimonials, no invented numbers, no stock photography.

## 3. Canonical calendar (derived; founder to confirm)

Today is Friday 2026-10-23. Week 1 starts Monday 2026-10-26. Week *n* starts on 2026-10-26 plus 7 × (*n* − 1) days.

| Milestone | Plan week | Date |
| --- | --- | --- |
| Discovery starts | 1 | Mon 2026-10-26 |
| Gate 0 | end of 3 | Fri 2026-11-13 |
| Gate 1 (5 offices signed, 2 brands paid) | end of 7 | Fri 2026-12-11 |
| Gate 2 (campaign zero report) | end of 9 in the plan | see collision below |
| Gate 3 | 16 in the plan | see collision below |
| Six-month decision | 24 | week of Mon 2027-04-05 |

**Blackouts. No drop day falls in one, and no five-business-day window overlaps one:**
- the last two weeks of December, 18 to 31 December inclusive;
- the Monday-to-Friday week that contains 4 July or its observed federal holiday;
- the last two weeks of August, 18 to 31 August inclusive.

Drop days are Tuesday or Wednesday only. Never Monday or Friday.

**Business days.** Offsets written T−n and T+n count business days: Monday to Friday, excluding US federal holidays. 2026–27 holidays: 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01, 2027-01-18, 2027-02-15, 2027-05-31, 2027-06-18 (observed), 2027-07-05 (observed), 2027-09-06. T is day 1 of the window. T+2 is "day 3", T+4 is "day 5" and closes the window. The report is due at T+7, the debrief at T+10, and the redemption check at T+30 *calendar* days.

**Collision the plan does not resolve.** Campaign zero is planned for weeks 7 to 9 (7 to 27 December). A five-day window must close by Thursday 17 December, so the latest legal drop is Wednesday 9 December. That needs brand freight by 23 or 24 November, during Thanksgiving week, and both brands paid in week 4. That is not realistic. Canonical resolution:
- **Campaign zero drop: Tuesday 2027-01-12.** Brands are asked to ship by Tuesday 2026-12-22 to avoid holiday freight. The hard T−10 is 2026-12-28. Receive at T−5, 2027-01-05. The window closes at T+4, 2027-01-19 (MLK Day on the 18th is skipped). Report at T+7, 2027-01-22, which is Gate 2. Debrief at T+10, 2027-01-27. Redemption check at T+30, 2027-02-11.
- Stretch option, only if both brands have paid by 2026-11-20: Tuesday 2026-12-08.
- **Standard runs**: first standard drop Tuesday 2027-02-09, second Tuesday 2027-02-23. **Gate 3: Friday 2027-03-12**, which is week 20 and replaces the plan's week 16.
- The decision window stays weeks 17 to 24 and ends on Friday 2027-04-09.
- Label every one of these dates "derived, founder to confirm". Where a date appears in copy (outreach and proposals), write it as a bracketed slot such as `[DROP DATE: Tue 2027-01-12]`.

## 4. Fixed enumerations

**Office categories** (form option, preference profile and brand category; stable keys, display label in parentheses):
`chips-crisps` (Chips and crisps), `popcorn-puffs` (Popcorn and puffs), `crackers-pretzels` (Crackers and pretzels), `bars` (Bars), `cookies-baked` (Cookies and baked snacks), `chocolate-candy` (Chocolate and candy), `nuts-seeds-trail` (Nuts, seeds and trail mix), `meat-snacks` (Jerky and meat sticks, shelf-stable only), `fruit-snacks` (Dried fruit and fruit snacks), `sparkling-soda` (Sparkling water and soda), `tea-juice` (Tea, juice and other non-carbonated drinks, shelf-stable), `coffee-rtd` (Ready-to-drink coffee, shelf-stable), `other-snack`, `other-drink`.

**Excluded outright:** alcohol, cannabis, CBD or THC, dietary supplements (anything with a Supplement Facts panel), refrigerated or perishable products, anything needing preparation, and explicit health claims. Nutrient-content claims such as "10g protein" or "low sugar" are not health claims, but they get `founder_review = Y`. Structure or function wording such as "supports gut health" or "boosts immunity" is an explicit health claim and is excluded.

**Outreach status** (one column, Clay tables only; E and A share it):
`new` → `queued` (in today's daily view) → `contacted` → `replied` → `call_booked` → `call_done` → `yes_in_principle` → `materials_sent` (office one-pager or brand proposal) → `signed` (office) or `paid` (brand). Terminal or side states: `not_now` (with `next_action_date`), `no`, `wrong_person`, `do_not_contact`.

**Retailer evidence grade** (brand to retailer link): `seen_on_shelf` (the founder only, never set by an agent), `store_selector` (the retailer's own site shows the product at that store), `brand_claim` (the brand's site or store locator says so), `unverified`.

**Confidence** (B's rows): `high` (a source under 24 months old plus one independent confirmation), `medium` (one source under 24 months), `low` (anything older, or a map listing alone).

**Headcount band:** `40-75`, `76-150`, `151-250`, `251-500`, `under-40`, `over-500`, `unknown`. **Headcount scope:** `nyc-office`, `whole-company`, `unknown`.

**Delivery model:** `founder`, `courier`, `direct-ship`.
**Tier:** `founding`, `standard`.
**The seven hour activities** (hours logs, actuals and model; these exact keys): `brand_sales`, `office_coordination`, `receiving_kitting`, `drop_day`, `checks_pickup`, `reporting_debriefs`, `admin_invoicing`.

## 5. File conventions

CSV in UTF-8 with one header row. Snake-case column names. Dates as `YYYY-MM-DD` (source dates may be `YYYY-MM` when only the month is known). Money as plain numbers in USD with no `$`. Booleans as `Y` or `N`. Lists separated by semicolons. Coordinates as decimal `lat` and `lon` (WGS84). Spreadsheets as `.xlsx` that open in Google Sheets with formulas intact (no macros or scripts), and the key tabs also exported as CSV.

Geocoding: run `python3 _shared/geocode.py "<street address>"` from `desk-drop/`. It calls NYC Planning GeoSearch, which uses the city's own address database and returns the tax lot (`bbl`, the key for deduplicating buildings). It falls back to Nominatim, bounded to Manhattan. Results are cached and rate limited for the whole project. Do not call geocoders directly and do not geocode in parallel. Keep `bbl` as a column on building rows.

## 6. Handoff schemas

Producers may add columns. They never rename or drop these.

### 6.1 B → A, C: `cluster-1-flatiron/` exports
- `companies.csv`: `company_id` (B-C-###), `company_name`, `website`, `industry`, `building_id`, `street_address`, `floor`, `zip`, `lat`, `lon`, `in_boundary` (Y/N), `headcount_band`, `headcount_scope`, `headcount_source_url`, `address_source_url`, `address_source_date`, `second_source_url`, `confidence`, `in_coworking` (Y/N), `coworking_id`, `linkedin_company_url`, `notes`, `found_date`.
- `buildings.csv`: `building_id` (B-B-###), `street_address`, `building_name`, `lat`, `lon`, `lobby_type` (`walk-up`, `security desk`, `loading dock`, `unknown`), `lobby_source_url`, `coi_required` (`yes`, `no`, `unknown`), `coi_source_url`, `candidate_company_count`, `verified_on_foot` (blank), `notes`.
- `coworking.csv`: `coworking_id` (B-W-###), `operator`, `location_name`, `street_address`, `lat`, `lon`, `pantry_control` (`operator`, `tenant`, `unknown`), `pantry_source_url`, `source_url`, `source_date`, `confidence`, `notes`.
- `retailers.csv`: `retailer_id` (B-R-###), `retailer_name`, `street_address`, `lat`, `lon`, `inside_boundary` (Y/N), `blocks_outside` (0 to 10), `shelf_set`, `source_url`, `source_date`, `confidence`, `notes`.
- `boundary.geojson` (polygon), `map-private.geojson`, and `map-public.geojson`. The public map holds the boundary and retailers only.

### 6.2 A → E: Clay tables (`clay-icp-tables/`)
Both tables carry these **stable personalization and tracking columns**. E maps to them and adds its conversation-tracking columns to the same tables, never to a second status store:
`row_id`, `company` (company or brand name), `first_name`, `last_name`, `title`, `contact_linkedin_url`, `work_email`, `email_status` (`verified`, `unverified`, `none`), `channel` (`email`, `linkedin`, `warm-intro`, `walk-in`), `score`, `score_reason` (one sentence), `onsite_band` (offices; estimate until intake), `nearest_stocked_retailer` (brands: name and street), `nearest_retailer_grade`, `why_now`, `why_now_url`, `why_now_date`, `known_to_founder` (Y/N), `startup_cpg_member` (Y/N/unknown), `do_not_contact` (Y/N), `status` (section 4), `source_url`, `found_date`.
Conversation-tracking columns E adds: `sequence`, `touch_1_date`, `touch_2_date`, `touch_3_date`, `last_reply_date`, `reply_type`, `call_date`, `call_notes`, `yes_in_principle` (Y/N), `next_action`, `next_action_date`, `opt_out_date`, `referral_from`.
Daily views: `daily-view-offices.csv` and `daily-view-brands.csv`. Each holds the ten highest-scored rows with `status = new` and `do_not_contact = N`, one contact per company, and no company with a contact already in flight.

### 6.3 C ↔ F: intake forms (both sheets have these columns, in this order)
**`office_intake`**: `submitted_at`, `form_version`, `company`, `contact_name`, `contact_title`, `contact_email`, `contact_phone`, `office_address`, `floor_suite`, `tuesday_headcount`, `pantry_owner_name`, `pantry_owner_title`, `pantry_owner_is_contact` (Y/N), `receiving_type` (`walk-up`, `front desk`, `loading dock`, `other`), `receiving_window`, `coi_required` (`yes`, `no`, `unsure`), `survey_channel` (`slack`, `email`, `other`), `categories_wanted` (category keys, semicolons), `vetoes`, `notes`, `source` (`website`, `founder`).
**`brand_intake`**: `submitted_at`, `form_version`, `brand_name`, `website`, `contact_name`, `contact_title`, `contact_email`, `contact_phone`, `product_sku`, `category` (category key), `hq_city`, `nyc_retailers`, `online_store_url`, `can_issue_discount_code` (Y/N), `preferred_timing`, `budget_approver_is_contact` (Y/N), `budget_approver_name_title`, `q1_sealed_shelf_stable_60d`, `q2_labeled_ingredients_allergens`, `q3_buy_path_near_cluster`, `q4_can_ship_275_in_10bd`, `q5_product_liability_insurance`, `q6_contact_can_approve_600`, `q7_why_now` (q1 to q6 take `Y`, `N` or `unsure`; q7 is free text), `excluded_category_confirmed` (Y), `notes`, `source`.
C owns the live web forms. F owns the founder-side copy of the same forms and the tracker that reads both sheets.

### 6.4 E → F: signed office and paid brand rows (`desk-drop-outreach/handoff/`)
- `signed_offices.csv`: every `office_intake` column, plus `office_id` (O-###), `clay_row_id`, `agreement_signed_date`, `agreement_file`, `founding_roster_named` (Y/N), `budget_probe_verbatim`, `budget_probe_date`, `budget_probe_monthly_usd` (a number only if they named one, else blank).
- `paid_brands.csv`: every `brand_intake` column, plus `brand_id` (BR-###), `clay_row_id`, `tier`, `price_usd`, `offices_count`, `payment_terms`, `agreement_signed_date`, `invoice_id`, `invoice_date`, `payment_received_date`, `coi_received_date`, `allergen_sheet_received_date`, `logo_received_date`, `card_sentences`, `allergen_line_verbatim`, `retailer_line`, `discount_code`, `landing_url`, `unused_product_election` (`return`, `release`), `office_approvals` (office_ids that said yes, semicolons).

### 6.5 F → H: actuals (`campaign-ops/exports/`)
- `campaign_actuals.csv`, one row per brand campaign: `campaign_id` (CMP-###), `drop_id` (DRP-###), `drop_date`, `delivery_model`, `tier`, `brand_id`, `offices`, `units_received`, `units_delivered`, `units_placed`, `units_placed_within_1bd`, `units_topped_up`, `units_depleted_day5`, `survey_responses`, `survey_tried_yes`, `qr_scans`, `code_redemptions_day30`, `revenue_usd`, `invoice_paid_date`, `processing_fee_usd`, `report_delivered_date`, `brand_would_buy_again` (`yes`, `maybe`, `no`), `renewed` (Y/N/pending).
- `drop_costs.csv`, one row per drop, holding only direct costs: `drop_id`, `drop_date`, `delivery_model`, `offices`, `brands`, `kit_cost_usd`, `transport_cost_usd`, `other_direct_cost_usd`, `notes`. Monthly overhead (software, insurance, storage) is **not** here. It is paid once, in H's cash flow.
- `hours_log.csv`, one row per entry: `date`, `drop_id` (blank for non-drop time), `campaign_id` (optional), `activity` (one of the seven keys), `hours`, `note`.
H publishes the layout it expects in `financial-model/HANDOFF.md`. If H's layout and this section differ, H's wins and F matches it.

### 6.6 E → H: pipeline (`desk-drop-outreach/exports/pipeline_log.csv`)
One row per event: `date`, `side` (`office`, `brand`), `org_id`, `org_name`, `event` (`outreach_sent`, `conversation`, `yes_in_principle`, `signed`, `paid`, `budget_probe`, `renewal_answer`, `opt_out`), `value_number` (headcount for `signed`, USD for `paid`, USD per month for `budget_probe`, USD for a brand's stated willingness to pay), `value_text` (verbatim quote), `controls_budget` (Y/N, brands), `notes`.

### 6.7 G → H, E, F, C, D
- `desk-drop-legal-pack/figures.csv`: `item`, `low_usd`, `high_usd`, `working_usd`, `status` (`plan estimate`, `verified YYYY-MM-DD`, `needs quote`), `source_url`, `source_date`, `timing`, `notes`.
- `desk-drop-legal-pack/name-check-log.md`: gates any print run (D) and any public launch (C).
- The email footer (E), the agreements (E, F), the survey privacy notice (F, C), and the certificate-of-insurance requests (F).

### 6.8 D → C, E, F
- `desk-drop-identity/tokens/tokens.css` and `tokens.json`: colors, type families and weights, spacing scale, radii. C imports `tokens.css` directly.
- The wordmark is an SVG in light and dark versions. The avatar is a PNG.
- Templates with fields marked for the operations generator: tent card, case label and one-page report. The proposal, one-pagers, discovery one-pager and email signature go to E.
