# How to fill the handoff files

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/handoff/` and `desk-drop-outreach/exports/`

**What they are for.** Three files carry outreach results to the two workstreams that act on them:

| File | Read by | One row per | Schema |
| --- | --- | --- | --- |
| `handoff/signed_offices.csv` | Operations (F, `campaign-ops/`) | Signed office | CONTRACTS 6.4: every `office_intake` column (6.3), then the 6.4 columns, then two additions |
| `handoff/paid_brands.csv` | Operations (F) | Paid brand | CONTRACTS 6.4: every `brand_intake` column (6.3), then the 6.4 columns, then additions for payments, the legal pack, the tent card and the founder's own qualification checks |
| `exports/pipeline_log.csv` | Financial model (H, `financial-model/`) | Pipeline event | `financial-model/HANDOFF.md` section 3: exactly nine columns, in date order |

**SAMPLE rows.** As shipped, each file holds SAMPLE rows only (one signed office, one paid brand, 210 pipeline events), so the format can be seen. Every SAMPLE value starts with SAMPLE: illustrative placeholders, not results. **Replace each file the first time you have a real row; never paste the SAMPLE pipeline file into the financial model.** The tracker ignores SAMPLE rows while Config `include_sample` = N, so a real download never carries them.

**Where you fill them.** Not in the CSV files. Each file is a download of one tab of `tracking/conversation-tracker.xlsx` (in Google Sheets): `signed_offices`, `paid_brands` and `pipeline_log`. You type in the first two; the third is built for you.

---

## 1. `signed_offices.csv`

**When.** The day an office's participation agreement is signed by both sides and its intake is complete (the office conversion path, `messages/10-office-post-call-conversion.md`, steps 5 and 6; the agreement is `desk-drop-legal-pack/03-office-participation-agreement.md` and goes out only once the attorney has cleared it).

**How (about 5 minutes).**
1. Open the office's row in the office intake sheet (the website form's sheet, or operations' founder-side copy; both use the CONTRACTS 6.3 columns in the same order).
2. Copy its 21 cells, `submitted_at` to `source`, and paste them into the next empty row of the **signed_offices** tab at column A. They land in the right columns because the order is the same.
3. Type the rest:
   - `office_id`: the next O-### (O-001, O-002, ...). Never reuse one.
   - `clay_row_id`: the office contact's Clay `row_id`, the same one used on Office_Log. This is the key that joins everything (it becomes `org_id` in the pipeline).
   - `agreement_signed_date`, `agreement_file` (the signed PDF's file name), `founding_roster_named` (Y only if the office ticked the roster box in section 6 of the agreement), `public_naming_ok` (Y only if it ticked "publicly"), `agreement_version` (for example 0.8), `owner_can_say_yes_alone`.
   - From the agreement's top table: `pantry_owner_phone` and `pantry_owner_email` (business contacts). From Clay or `cluster-1-flatiron/companies.csv`: `industry` and `building_id`.
   - `budget_probe_verbatim`, `budget_probe_date`, `budget_probe_monthly_usd` fill themselves from Office_Log (the first budget-probe answer for that `clay_row_id`). If the office never had a logged conversation, ask the probe word for word at delivery of the agreement (`calls/office-call-guide.md`, question 6) and type the three cells; `budget_probe_monthly_usd` is a number only if they named one (0 for "no budget"), else blank.
4. In Clay, set the office's `status` to `signed` the same day.
5. File > Download > Comma-separated values (current sheet), saved as `desk-drop-outreach/handoff/signed_offices.csv`, replacing the file.

## 2. `paid_brands.csv`

**When.** Start the row the day the brand's payment lands (founding: the full $600; standard: the 50% deposit). That payment releases the ship date (plan, Phase 2 "Close and collect"). Then keep filling the row as the rest arrives, and re-download after each change.

**How.**
1. Copy the brand's 27 `brand_intake` cells, `submitted_at` to `source`, into the next empty row of **paid_brands** at column A.
2. Type at payment: `brand_id` (next BR-###), `clay_row_id` (as on Brand_Log), `tier`, `price_usd` (600 founding, 1500 standard, plus 150 per extra office), `offices_count`, `payment_terms` (as in the signed agreement), `agreement_signed_date`, `invoice_id`, `invoice_date`, `payment_1_usd`, `payment_1_date`, `agreement_version`, `unused_product_election` (as elected in the agreement), and from the agreement's Part 1 `brand_legal_name`, `billing_address`, `billing_email`. `payment_received_date` fills itself from `payment_1_date`. `campaign_id` waits for operations to assign the CMP-###.
3. Type as each arrives (the request is `messages/11-brand-post-call-conversion.md`, step 8): `coi_received_date` and `coi_policy_end_date` (checked against `desk-drop-legal-pack/11-coi-request-brand-product-liability.md`), `allergen_sheet_received_date`, `logo_received_date`, `card_sentences`, `allergen_line_verbatim` and `may_contain_verbatim` (word for word from the package), `allergen_source`, `retailer_line`, `discount_code`, `code_site` (where the code works, without https://), `landing_url`, `newsletter_option` and `brand_privacy_url`. Two-flavor campaigns only: `flavor_name`, `flavor_name_2` and the `_2` allergen columns.
4. **Your own qualification checks, before any ship date.** The `q1` to `q7` intake columns are the brand's own answers. The `verified_` columns are yours: Y only when you have seen the evidence (a unit or a spec sheet with a best-by date that leaves 60 days at the drop; the label; the store's own site or your own visit; the shipping confirmation in writing; the certificate; the signer's authority; the why-now). `verified_not_excluded` = Y only after checking the excluded list (CONTRACTS section 4). Put the evidence in `verified_notes` and the date in `verified_date`. Operations will not confirm a ship date until every `verified_` column is Y.
5. `office_approvals`: the `office_id`s that said yes to this brand, separated by semicolons (each office approves explicitly for its first three drops, `messages/10`, step 7).
6. Standard brands: when the balance lands, `payment_2_usd` and `payment_2_date`.
7. In Clay, set the brand's `status` to `paid` the day the first payment lands.
8. Download the tab as `desk-drop-outreach/handoff/paid_brands.csv`.

## 3. `exports/pipeline_log.csv`

**You do not type this file.** The **pipeline_log** tab builds it from the logs, the two handoff tabs, `later_events` and the Friday Clay paste, sorted by date, in exactly the nine columns the financial model expects. Every Friday: download it (File > Download > CSV, current sheet), save it as `desk-drop-outreach/exports/pipeline_log.csv`, and paste it into the financial model's **Pipeline** tab with its header in row 4.

What each event row comes from:

| Event | One row for | `date` | `value_number` | `value_text` | `controls_budget` | `notes` |
| --- | --- | --- | --- | --- | --- | --- |
| `outreach_sent` | each touch (1, 2, 3) on a Clay row | the touch date | blank | blank | blank | `touch_1; <sequence>; <channel>` |
| `conversation` | each Office_Log or Brand_Log row | `call_date` | blank | blank | blank | the call type |
| `yes_in_principle` (office) | each office conversation with Y **and** a pantry owner **and** a receiving window (the financial model's rule) | `call_date` | blank | blank | blank | owner title and window |
| `yes_in_principle` (brand) | each brand conversation with Y | `call_date` | blank | blank | Y/N | blank |
| `budget_probe` (office) | each office conversation with a probe answer | `call_date` | USD a month, low end; 0 for no budget; blank if no number | the answer, verbatim | blank | the high end if a range |
| `budget_probe` (brand, before $1,500) | each brand conversation with a before-answer | `call_date` | USD per campaign; blank if no number | verbatim | Y/N | blank, or `before_1500; <unit note>` |
| `budget_probe` (brand, after $1,500) | each brand conversation where $1,500 was said and they answered | `call_date` | USD per campaign | verbatim | Y/N | exactly `after_1500` |
| `signed` | each `signed_offices` row | `agreement_signed_date` | the office's Tuesday headcount | blank | blank | `office_id` |
| `paid` | each payment on a `paid_brands` row (one for founding, two for standard) | the payment date | USD received in that payment | blank | blank | payment number, `brand_id`, tier, invoice |
| `renewal_answer` | each `later_events` row of that type | its date | USD committed if yes, else blank | `yes`, `maybe` or `no` | blank | its notes |
| `opt_out` | each `later_events` row of that type: **a signed office or a paid brand leaving the roster** | its date | blank | the reason | blank | its notes |

`org_id` is always the Clay `row_id` (for signed and paid rows, the `clay_row_id` you typed), so one organization keeps one id from its first touch to its last, as the financial model asks.

**Two rules that matter for the financial model.**
- **An outreach unsubscribe is not a pipeline `opt_out`.** The financial model counts active offices as signed offices minus office `opt_out` events (`financial-model/_work/build_model.py`, Pipeline summary, "Active offices, to date (signed less opted out)"). Exporting every "no thanks" from cold email would push that number down, even below zero. So unsubscribes live only in Clay (`do_not_contact`, `opt_out_date`), and `opt_out` in this file means a signed office or paid brand that left. Log those on the tracker's `later_events` tab.
- **A brand's answer after hearing $1,500 carries `notes = after_1500` exactly,** so the model keeps the two medians apart. The tracker writes it; do not edit that cell.

**Renewal answers and roster exits.** At each brand debrief (T+10) type a `later_events` row: `date`, `side` = brand, `clay_row_id`, `org_name`, `event` = `renewal_answer`, `value_text` = yes, maybe or no, and `value_number` = the USD they committed if yes. An office or brand that leaves: `event` = `opt_out` with the reason in `value_text`.

---

## 4. ID rules

| ID | Form | Assigned | Never |
| --- | --- | --- | --- |
| `row_id` | whatever the Clay tables use (CONTRACTS 6.2) | By the Clay table when a contact is added | Changed or reused |
| `office_id` | O-### | At signing, next number | Reused, even if an office leaves |
| `brand_id` | BR-### | At first payment, next number. A brand keeps it for every later campaign (the financial model counts renewals by it) | A second id for the same brand |
| `org_id` (pipeline) | the Clay `row_id` | Automatically | Typed by hand |

One row per office on `signed_offices` and one per brand on `paid_brands`; the Scorecard flags a duplicate `clay_row_id`. A brand's second campaign is a renewal answer on `later_events` and a new campaign row on operations' side, not a second `paid_brands` row.

## 5. Where these files differ from CONTRACTS

CONTRACTS section 6 lets producers add columns and never rename or drop them. Nothing is renamed or dropped.

- `signed_offices.csv` adds `agreement_version` (suggested by the legal pack, `desk-drop-legal-pack/HANDOFF.md`), `owner_can_say_yes_alone` (plan, Phase 1 targeting rule), and the five columns operations requests (`campaign-ops/tools/trackerdef.py`, `SIGNED_OFFICES_REQUESTED`, read 2026-10-24): `industry`, `pantry_owner_phone`, `pantry_owner_email`, `public_naming_ok`, `building_id`.
- `paid_brands.csv` adds `payment_1_usd`, `payment_1_date`, `payment_2_usd`, `payment_2_date` (so each payment becomes one pipeline `paid` row, as the financial model expects); `agreement_version`, `coi_policy_end_date`, `newsletter_option`, `brand_privacy_url` (legal pack); `allergen_source`, `may_contain_verbatim` and the two-flavor columns (identity, `desk-drop-identity/HANDOFF.md`, tent card); and the founder's `verified_` checks with `verified_date` and `verified_notes`; plus the columns operations requests (`PAID_BRANDS_REQUESTED`, read 2026-10-24) that were not already there: `campaign_id`, `brand_legal_name`, `billing_address`, `billing_email`, `code_site`. Operations reads both files by header name, so column position does not matter to it.
- `payment_received_date` is defined as the date of the payment that releases the ship date: the full price for founding, the 50% deposit for standard.
- `exports/pipeline_log.csv` follows `financial-model/HANDOFF.md` section 3, which publishes exactly CONTRACTS 6.6's nine columns and fixes the brand willingness-to-pay rows as `budget_probe` with `after_1500`. One reading of CONTRACTS 6.6 is narrowed: `opt_out` is used only for roster exits (above).

---

## 6. Column reference

Generated from `tools/build_tracker.py`; the same text is on the tracker's Dictionary tab and in each header's note.

<!-- columns:start (generated by tools/build_handoff_tables.py; do not edit by hand) -->

### signed_offices.csv

| # | Column | Meaning | Source |
| --- | --- | --- | --- |
| 1 | `submitted_at` | Copied from the intake row | CONTRACTS 6.3 |
| 2 | `form_version` | Copied from the intake row | CONTRACTS 6.3 |
| 3 | `company` | Copied from the intake row | CONTRACTS 6.3 |
| 4 | `contact_name` | Copied from the intake row | CONTRACTS 6.3 |
| 5 | `contact_title` | Copied from the intake row | CONTRACTS 6.3 |
| 6 | `contact_email` | Copied from the intake row | CONTRACTS 6.3 |
| 7 | `contact_phone` | Copied from the intake row | CONTRACTS 6.3 |
| 8 | `office_address` | Copied from the intake row | CONTRACTS 6.3 |
| 9 | `floor_suite` | Copied from the intake row | CONTRACTS 6.3 |
| 10 | `tuesday_headcount` | Copied from the intake row | CONTRACTS 6.3 |
| 11 | `pantry_owner_name` | Copied from the intake row | CONTRACTS 6.3 |
| 12 | `pantry_owner_title` | Copied from the intake row | CONTRACTS 6.3 |
| 13 | `pantry_owner_is_contact` | Copied from the intake row | CONTRACTS 6.3 |
| 14 | `receiving_type` | Copied from the intake row | CONTRACTS 6.3 |
| 15 | `receiving_window` | Copied from the intake row | CONTRACTS 6.3 |
| 16 | `coi_required` | Copied from the intake row | CONTRACTS 6.3 |
| 17 | `survey_channel` | Copied from the intake row | CONTRACTS 6.3 |
| 18 | `categories_wanted` | Copied from the intake row | CONTRACTS 6.3 |
| 19 | `vetoes` | Copied from the intake row | CONTRACTS 6.3 |
| 20 | `notes` | Copied from the intake row | CONTRACTS 6.3 |
| 21 | `source` | Copied from the intake row | CONTRACTS 6.3 |
| 22 | `office_id` | O-### assigned at signing (CONTRACTS 6.4). | CONTRACTS 6.4 |
| 23 | `clay_row_id` | The Clay row_id of the office contact. Must match the row_id used in Office_Log. | CONTRACTS 6.4; pipeline org_id |
| 24 | `agreement_signed_date` | Date the participation agreement was signed by both sides. | CONTRACTS 6.4 |
| 25 | `agreement_file` | File name of the signed PDF. | CONTRACTS 6.4 |
| 26 | `founding_roster_named` | Y if the office ticked the box agreeing to be named on the founding roster (agreement section 6). | CONTRACTS 6.4 |
| 27 | `budget_probe_verbatim` | Filled from Office_Log (first budget-probe answer for this clay_row_id). Overwrite only if there is no log row. | CONTRACTS 6.4 |
| 28 | `budget_probe_date` | Filled from Office_Log: the date of that answer. | CONTRACTS 6.4 |
| 29 | `budget_probe_monthly_usd` | Filled from Office_Log: USD per month if they named a number (0 for 'no budget'), else blank. | CONTRACTS 6.4 |
| 30 | `agreement_version` | Version of the participation agreement signed (e.g. 0.8). Added at the legal pack's suggestion. | addition (G) |
| 31 | `owner_can_say_yes_alone` | Y if the pantry owner can approve a brand alone. | addition (plan Phase 1) |
| 32 | `industry` | The office's industry, from Clay or cluster-1-flatiron/companies.csv (industry). Shown in brand proposals by industry, never by name. | addition (requested by operations) |
| 33 | `pantry_owner_phone` | The pantry owner's business phone, from the agreement's top table. | addition (requested by operations) |
| 34 | `pantry_owner_email` | The pantry owner's business email, from the agreement's top table. | addition (requested by operations) |
| 35 | `public_naming_ok` | Y only if the office ticked 'publicly' in section 6 of the agreement. Otherwise reports show it as a letter. | addition (requested by operations; legal pack 03 section 6) |
| 36 | `building_id` | B-B-### from cluster-1-flatiron (companies.csv building_id), if known. | addition (requested by operations) |

### paid_brands.csv

| # | Column | Meaning | Source |
| --- | --- | --- | --- |
| 1 | `submitted_at` | Copied from the intake row | CONTRACTS 6.3 |
| 2 | `form_version` | Copied from the intake row | CONTRACTS 6.3 |
| 3 | `brand_name` | Copied from the intake row | CONTRACTS 6.3 |
| 4 | `website` | Copied from the intake row | CONTRACTS 6.3 |
| 5 | `contact_name` | Copied from the intake row | CONTRACTS 6.3 |
| 6 | `contact_title` | Copied from the intake row | CONTRACTS 6.3 |
| 7 | `contact_email` | Copied from the intake row | CONTRACTS 6.3 |
| 8 | `contact_phone` | Copied from the intake row | CONTRACTS 6.3 |
| 9 | `product_sku` | Copied from the intake row | CONTRACTS 6.3 |
| 10 | `category` | Copied from the intake row | CONTRACTS 6.3 |
| 11 | `hq_city` | Copied from the intake row | CONTRACTS 6.3 |
| 12 | `nyc_retailers` | Copied from the intake row | CONTRACTS 6.3 |
| 13 | `online_store_url` | Copied from the intake row | CONTRACTS 6.3 |
| 14 | `can_issue_discount_code` | Copied from the intake row | CONTRACTS 6.3 |
| 15 | `preferred_timing` | Copied from the intake row | CONTRACTS 6.3 |
| 16 | `budget_approver_is_contact` | Copied from the intake row | CONTRACTS 6.3 |
| 17 | `budget_approver_name_title` | Copied from the intake row | CONTRACTS 6.3 |
| 18 | `q1_sealed_shelf_stable_60d` | Copied from the intake row | CONTRACTS 6.3 |
| 19 | `q2_labeled_ingredients_allergens` | Copied from the intake row | CONTRACTS 6.3 |
| 20 | `q3_buy_path_near_cluster` | Copied from the intake row | CONTRACTS 6.3 |
| 21 | `q4_can_ship_275_in_10bd` | Copied from the intake row | CONTRACTS 6.3 |
| 22 | `q5_product_liability_insurance` | Copied from the intake row | CONTRACTS 6.3 |
| 23 | `q6_contact_can_approve_600` | Copied from the intake row | CONTRACTS 6.3 |
| 24 | `q7_why_now` | Copied from the intake row | CONTRACTS 6.3 |
| 25 | `excluded_category_confirmed` | Copied from the intake row | CONTRACTS 6.3 |
| 26 | `notes` | Copied from the intake row | CONTRACTS 6.3 |
| 27 | `source` | Copied from the intake row | CONTRACTS 6.3 |
| 28 | `brand_id` | BR-### assigned at payment (CONTRACTS 6.4). | CONTRACTS 6.4 |
| 29 | `clay_row_id` | The Clay row_id of the brand contact. Must match the row_id used in Brand_Log. | CONTRACTS 6.4; pipeline org_id |
| 30 | `tier` | founding or standard. | CONTRACTS 6.4 |
| 31 | `price_usd` | Campaign price in USD (600 founding, 1500 standard, plus 150 per extra office). | CONTRACTS 6.4 |
| 32 | `offices_count` | Offices in the campaign (5 founding, 10 standard, more if extra offices). | CONTRACTS 6.4 |
| 33 | `payment_terms` | As in the signed agreement. | CONTRACTS 6.4 |
| 34 | `agreement_signed_date` | Date the campaign agreement was signed by both sides. | CONTRACTS 6.4 |
| 35 | `invoice_id` | Invoice number. | CONTRACTS 6.4 |
| 36 | `invoice_date` | Invoice date. | CONTRACTS 6.4 |
| 37 | `payment_received_date` | Date the payment that releases the ship date landed: founding = the full price; standard = the 50% deposit. Filled from payment_1_date. | CONTRACTS 6.4 |
| 38 | `coi_received_date` | Date the product liability certificate arrived (checked per legal pack file 11). | CONTRACTS 6.4 |
| 39 | `allergen_sheet_received_date` | Date the ingredient and allergen sheet arrived. | CONTRACTS 6.4 |
| 40 | `logo_received_date` | Date the logo files arrived. | CONTRACTS 6.4 |
| 41 | `card_sentences` | The brand's two sentences for the tent card, as sent (no health claims). | CONTRACTS 6.4 |
| 42 | `allergen_line_verbatim` | The allergen statement copied word for word from the label. | CONTRACTS 6.4 |
| 43 | `retailer_line` | 'Find it at <store, street>' line for the card. | CONTRACTS 6.4 |
| 44 | `discount_code` | The campaign discount code. | CONTRACTS 6.4 |
| 45 | `landing_url` | Landing page for the QR, if the brand gave one. | CONTRACTS 6.4 |
| 46 | `unused_product_election` | return or release, as elected in the agreement. | CONTRACTS 6.4 |
| 47 | `office_approvals` | office_ids that said yes to this brand, semicolons. | CONTRACTS 6.4 |
| 48 | `payment_1_usd` | First payment received, USD (founding: 600; standard: the 50% deposit). | addition: pipeline 'paid' rows |
| 49 | `payment_1_date` | Date the first payment landed in the bank. | addition: pipeline 'paid' rows |
| 50 | `payment_2_usd` | Second payment, USD (standard balance at placement confirmation). Blank for founding. | addition: pipeline 'paid' rows |
| 51 | `payment_2_date` | Date the second payment landed. | addition: pipeline 'paid' rows |
| 52 | `agreement_version` | Version of the campaign agreement signed. | addition (G) |
| 53 | `coi_policy_end_date` | End date of the brand's product liability policy, from the certificate. | addition (G) |
| 54 | `newsletter_option` | Y if the brand chose the optional survey email box (agreement Part 1). | addition (G) |
| 55 | `brand_privacy_url` | The brand's privacy policy URL (needed only if newsletter_option = Y). | addition (G) |
| 56 | `allergen_source` | Where the allergen line comes from on the package. | addition (D tent card) |
| 57 | `may_contain_verbatim` | Any 'may contain' line, word for word. | addition (D tent card) |
| 58 | `flavor_name` | Two-flavor campaigns only: flavor 1 name. | addition (D tent card) |
| 59 | `flavor_name_2` | Two-flavor campaigns only: flavor 2 name. | addition (D tent card) |
| 60 | `allergen_source_2` | Two-flavor only: flavor 2 allergen source. | addition (D tent card) |
| 61 | `allergen_line_verbatim_2` | Two-flavor only: flavor 2 allergen line. | addition (D tent card) |
| 62 | `may_contain_verbatim_2` | Two-flavor only: flavor 2 'may contain' line. | addition (D tent card) |
| 63 | `verified_q1_sealed_shelf_stable_60d` | Founder checked: sealed, individually packaged, shelf-stable, 60+ days of shelf life at the drop date. | addition: qualification check 1 |
| 64 | `verified_q2_labeled_ingredients_allergens` | Founder checked the label: ingredients and the nine major allergens. | addition: qualification check 2 |
| 65 | `verified_q3_buy_path_near_cluster` | Founder checked the buy path: a store within ten blocks (evidence grade store_selector, brand_claim or seen_on_shelf) or an online store with a code. | addition: qualification check 3 |
| 66 | `verified_q4_can_ship_275_in_10bd` | Brand confirmed in writing it can ship the units plus reserve to one Manhattan address within ten business days. | addition: qualification check 4 |
| 67 | `verified_q5_product_liability_insurance` | Certificate received and checked (legal pack file 11). | addition: qualification check 5 |
| 68 | `verified_q6_contact_can_approve_600` | The signer approved the price alone. | addition: qualification check 6 |
| 69 | `verified_q7_why_now` | A real reason for New York trial now (new store, launch, local push), noted in verified_notes. | addition: qualification check 7 |
| 70 | `verified_not_excluded` | Not alcohol, cannabis, CBD or THC, supplement, refrigerated, needing preparation, or carrying a health claim (CONTRACTS 4). | addition: excluded list |
| 71 | `verified_date` | Date the founder finished the checks. | addition |
| 72 | `verified_notes` | Evidence for the checks (best-by date seen, certificate details, store and street). | addition |
| 73 | `campaign_id` | CMP-### of this brand's first campaign, from operations. Blank until operations assigns it. | addition (requested by operations) |
| 74 | `brand_legal_name` | The brand's legal name from the signed agreement (Part 1). Printed on invoices. | addition (requested by operations) |
| 75 | `billing_address` | Business billing address from the agreement. | addition (requested by operations) |
| 76 | `billing_email` | Business email for invoices. | addition (requested by operations) |
| 77 | `code_site` | Where the discount code works, short form without https:// (for example example.com). | addition (requested by operations; tent card) |

### pipeline_log.csv

`date, side, org_id, org_name, event, value_number, value_text, controls_budget, notes` (exactly these nine, in this order).
<!-- columns:end -->

## Changelog

Round numbers are part B's rounds; a round that did not change this file is not listed.

- Round 1 (2026-10-24): fill steps for both handoff tabs and the pipeline export; event table checked against `tools/test_tracker.py` (every row of the SAMPLE export matches an independent computation); `opt_out` narrowed to roster exits after reading the financial model's active-office formula; column tables generated from the builder.
- Round 2 (2026-10-24): the SAMPLE export pasted into a scratch copy of the financial model passes H's own header, text and event checks, and H's Gate 0 and Gate 1 counts and medians equal the tracker's (`tools/test_h_compat.py`); added the ten columns operations requests (`campaign-ops/tools/trackerdef.py`, read 2026-10-24).
