# Handoff: financial model (workstream H)

H feeds nothing. The founder reads the workbook. H consumes three things: per-campaign actuals from operations (F), pipeline events from outreach (E), and formation, publication and insurance figures from the legal pack (G).

This file is the layout H expects. Per CONTRACTS section 6.5, where it differs from CONTRACTS, this file wins and F matches it. Header-only templates sit in `financial-model/handoff-templates/`.

General rules (CONTRACTS section 5): UTF-8 CSV, one header row, snake_case columns, dates `YYYY-MM-DD`, money as plain USD numbers with no `$`, booleans `Y` or `N`.

**These four files carry exactly the columns below, in this order, and nothing else.** H's layout wins (CONTRACTS 6.5). Put any extra field in a separate file. The founder pastes each file into a tab of the workbook; every paste area is followed by ten or more blank columns before the model's helper formulas, and the Checks tab flags a header row that differs from this file or anything pasted into the blank columns. This replaces the earlier "producers may add columns at the end" (review round 1, finding R1-06).

## 1. Drop IDs: one rule for F, E and the founder

The workbook's Schedule tab holds the drop list. Its `drop_id` values are the keys every actuals file must use.

| drop_id | Schedule row | Date (derived, founder to confirm) |
| --- | --- | --- |
| DRP-001 | Campaign zero (founding) | Tue 2027-01-12 |
| DRP-002 | Standard run 1 | Tue 2027-02-09 |
| DRP-003 | Standard run 2 | Tue 2027-02-23 |
| DRP-004 | Decision window drop 1 | Tue 2027-03-23 |
| DRP-005 | Decision window drop 2 | Tue 2027-04-06 |
| DRP-006 to DRP-012 | Spare rows for drops the founder adds | blank |

If a drop slips, keep its `drop_id` and change the date. A new drop takes the next spare ID. A row whose `drop_id` is not on Schedule is flagged on Checks ("not in schedule") and ignored.

## 2. From F: `campaign-ops/exports/` (consumed)

### 2.1 `campaign_actuals.csv`, one row per brand campaign

Paste into the workbook tab **Actuals_Campaigns**, header in row 4, columns A to Z (26 columns). Columns AA to AK stay blank; the model's helpers start at AL.

| # | Column | Type | What H does with it |
| --- | --- | --- | --- |
| 1 | `campaign_id` | CMP-### | Label only |
| 2 | `drop_id` | DRP-### | Joins to Schedule (section 1) |
| 3 | `drop_date` | date | Report due date (T+7 business days) |
| 4 | `delivery_model` | `founder`, `courier`, `direct-ship` | Label only |
| 5 | `tier` | `founding`, `standard` | Label only |
| 6 | `brand_id` | BR-### | Label only |
| 7 | `offices` | number | Responses per office when column 26 is blank |
| 8 | `units_received` | number | Count at receipt (not a ladder rung) |
| 9 | `units_delivered` | number | Ladder: delivered; Gate 2 denominator |
| 10 | `units_placed` | number | Ladder: placed |
| 11 | `units_placed_within_1bd` | number | Gate 2 numerator (80% threshold) |
| 12 | `units_topped_up` | number | Ladder |
| 13 | `units_depleted_day5` | number | Ladder: depleted |
| 14 | `survey_responses` | number | Ladder: responded |
| 15 | `survey_tried_yes` | number | Ladder: tried (a survey answer) |
| 16 | `qr_scans` | number | Ladder: scanned |
| 17 | `code_redemptions_day30` | number | Ladder: purchased (code redemptions) |
| 18 | `revenue_usd` | USD | Actual revenue of the campaign |
| 19 | `invoice_paid_date` | date | Cash date of the balance (revenue less deposit), and of the processing fee |
| 20 | `processing_fee_usd` | USD | Actual card fee; 0 for bank transfer |
| 21 | `report_delivered_date` | date | Gate 2: late if after T+7 business days, missing if blank |
| 22 | `brand_would_buy_again` | `yes`, `maybe`, `no` | Gate 2: count of `yes` |
| 23 | `renewed` | `Y`, `N`, `pending` | Decision rule: renewal rate = Y / (Y + N) |
| 24 | `deposit_usd` | USD, optional | **H addition.** Standard brands pay 50% at signature. If filled, the model books it on column 25 and the rest of `revenue_usd` on column 19 |
| 25 | `deposit_paid_date` | date, optional | **H addition.** Cash date of the deposit |
| 26 | `survey_responses_min_office` | number, optional | **H addition.** Fewest responses at any one office in this campaign. Gate 2 needs 5 per office; with this column the test is exact, without it H uses the average per office |

Columns 1 to 23 are CONTRACTS 6.5 unchanged. Columns 24 to 26 are H's additions at the end; the header must still carry them. Blank values in them are allowed: then all of `revenue_usd` is booked on `invoice_paid_date`, and Gate 2 uses the average.

Measurement honesty: these rungs stay in separate columns. No column for sales lift, conversions or ROI. Incremental purchases are not measured; the workbook says so in its own column.

### 2.2 `drop_costs.csv`, one row per drop, direct costs only

Paste into **Actuals_DropCosts**, header in row 4, columns A to I (9 columns). Columns J to T stay blank; the helper is in U.

| # | Column | Type | What H does with it |
| --- | --- | --- | --- |
| 1 | `drop_id` | DRP-### | Joins to Schedule |
| 2 | `drop_date` | date | Cash date of all three cost columns |
| 3 | `delivery_model` | key | Label only |
| 4 | `offices` | number | Label only |
| 5 | `brands` | number | Label only |
| 6 | `kit_cost_usd` | USD | Actual display kits |
| 7 | `transport_cost_usd` | USD | Actual transport (courier, car rides, van) |
| 8 | `other_direct_cost_usd` | USD | Anything else spent for this drop only, such as kit postage |
| 9 | `notes` | text | Label only |

No software, insurance, storage or phone here. Those are monthly overhead and the workbook pays them once, on Cash_Ledger. Putting them here would count them twice.

### 2.3 `hours_log.csv`, one row per entry

Paste into **Hours_Log**, header in row 4, columns A to F (6 columns), or the founder types rows there. Columns G to P stay blank; the totals per drop and per week start at Q.

| # | Column | Type | Rule |
| --- | --- | --- | --- |
| 1 | `date` | date | The day the work was done |
| 2 | `drop_id` | DRP-### or blank | Blank for time not tied to a drop (discovery in weeks 1 to 3, general admin). Selling a brand or recruiting an office for a known drop goes against that drop; weeks 4 to 7 of selling and recruiting go against DRP-001, because they are part of campaign zero's 57 planned hours |
| 3 | `campaign_id` | CMP-### or blank | Optional |
| 4 | `activity` | one of seven keys | `brand_sales`, `office_coordination`, `receiving_kitting`, `drop_day`, `checks_pickup`, `reporting_debriefs`, `admin_invoicing` |
| 5 | `hours` | decimal hours | 1.5, not 1:30 |
| 6 | `note` | text | Optional |

A row with any other activity key is flagged on Checks. The workbook totals hours per drop and per week by activity. Hours inside the 26 weeks with a blank `drop_id` feed the Dashboard's six-month all-in rate once they exceed the plan's 45 discovery hours (review R2-03), so log them honestly.

Toggl (optional): name each Toggl project after the drop (`DRP-001`) and tag each entry with one activity key. Toggl's help says CSV and Excel exports are a paid-plan feature (Starter from $9 per license a month; support.toggl.com, opened 2026-10-23). Toggl's export column names are unverified; the Toggl_Import tab finds the columns by the header text you type in C4:C7, and its paste area is A to AD (30 columns) so a long export fits.

### 2.4 How the switch to actuals works

Actuals change nothing until the founder sets **Actuals in = Y** for that drop on Schedule. Then the drop's P&L, hours, Dashboard row and cash flow use the actual files for that drop, and its planned cash leaves the cash flow.

Set Actuals in = Y once revenue, payments, direct costs and hours are final, by T+10 (the debrief). `code_redemptions_day30` (T+30), `renewed` and `brand_would_buy_again` can be filled in later: they move no money or hours, and the gates read them whether or not the switch is set. Setting Y before costs and hours are final shows part of a drop.

The Gate 3 rate is judged only when every standard run dated on or before the Gate 3 review has Actuals in = Y. Until then its status reads "not yet: N standard run(s) without actuals" and Gate 3 cannot pass (review R2-02). DRP-003's T+10 is Tue 2027-03-09, three days before the Fri 2027-03-12 review, so the default schedule leaves time.

## 3. From E: `desk-drop-outreach/exports/pipeline_log.csv` (consumed)

Paste into **Pipeline**, header in row 4, columns A to I (9 columns). One row per event, in date order. Columns are CONTRACTS 6.6 unchanged. Columns J to S stay blank; the helpers start at T.

| # | Column | Type |
| --- | --- | --- |
| 1 | `date` | date of the event |
| 2 | `side` | `office` or `brand` |
| 3 | `org_id` | stable ID for the organization (see below) |
| 4 | `org_name` | company or brand name |
| 5 | `event` | `outreach_sent`, `conversation`, `yes_in_principle`, `signed`, `paid`, `budget_probe`, `renewal_answer`, `opt_out` |
| 6 | `value_number` | number; meaning depends on the event (table below) |
| 7 | `value_text` | verbatim quote or answer |
| 8 | `controls_budget` | `Y` or `N` on brand rows |
| 9 | `notes` | text |

What H reads from each event (this pins down two points CONTRACTS leaves open):

| side | event | value_number | value_text | Used for |
| --- | --- | --- | --- | --- |
| office | `conversation` | blank | | Gate 0 context (15 planned) |
| office | `yes_in_principle` | blank | | Gate 0: 5 of 15. Log it only when the office named a pantry owner and a receiving window |
| office | `signed` | Tuesday headcount | | Gate 1: 5 signed and combined headcount of 350 or more |
| office | `budget_probe` | USD per month they named, blank if none | the answer, verbatim | Decision rule: offices that named $100 a month or more; median of the first numeric answer per office |
| office | `opt_out` | blank | reason | Active offices = signed less opted out |
| brand | `conversation` | blank | | Gate 0 context (15 planned) |
| brand | `budget_probe` | **USD per campaign the brand said it would pay, named before hearing $1,500.** Leave `notes` blank (or anything but `after_1500`) | the answer, verbatim | Gate 0: brands with any answer of $500 or more and `controls_budget = Y`; median of the first before-anchor answer per brand |
| brand | `budget_probe` (second row) | **USD per campaign the brand said after hearing $1,500**, with `notes = after_1500` exactly | the answer, verbatim | Gate 0 as above; its own median ("after hearing $1,500"). The plan's tracking sheet records both answers |
| brand | `paid` | **USD received in this payment.** One row per payment, in date order | | Gate 1: a brand counts as "paid in full" once its `paid` rows by Gate 1 add up to the founding package price ($600). A part payment alone does not count. Schedule's "brands paid" columns count any payment |
| brand | `renewal_answer` | **USD committed if the answer is yes, else blank** | `yes`, `maybe` or `no` | Gate 3: brands whose answer is `yes` with $1,500 or more committed, by the review date. A `maybe` or `no` never counts, whatever the amount |
| either | `outreach_sent` | blank | | Count only |

`org_id`: the workbook counts distinct organizations, so one organization must keep one ID from its first event to its last. Repeated `budget_probe` rows for one organization feed each median once (review R2-05). Recommendation: use the Clay `row_id` (CONTRACTS 6.2) as `org_id` for every event. The office_id (O-###) and brand_id (BR-###) assigned at signing can go in `notes`. Repeated rows for the same org and event are counted once; this includes Gate 3 renewals (one per brand).

## 4. From G: `desk-drop-legal-pack/figures.csv` (consumed, read 2026-10-24, re-read after its 01:52 update)

The file appeared during this build and was read in full. It changed again at 01:52 on 2026-10-24, after the round-1 build; it was re-read in full for review round 2 (finding R2-07) and the changes below are in the workbook. Each figure used is copied into Inputs section 11 with its status and source. A G figure replaces the plan's default only once G marks it `verified`; until then the plan's figure (or, for a range with no working figure, the plan's high end) stays the default and G's figure sits in the notes. Google Sheets cannot read a local CSV, so when G updates the file, the founder updates those cells by hand (working, low, high, status).

| figures.csv item | Working used | Status in G | Inputs line |
| --- | --- | --- | --- |
| `llc_articles_of_organization_fee` | $200 | verified 2026-10-23 | LLC Articles of Organization, filed Thu 2026-11-19 ("earliest Thu 2026-11-19, never before the attorney hour"); publication follows 10 business days later, Fri 2026-12-04 |
| `llc_certificate_of_publication_fee` | $50 | verified 2026-10-23 | Certificate of Publication |
| `llc_publication_newspapers_county_not_chosen` | **Not used as the default.** The model uses the plan's high end, $2,000 (plan range $250 to $2,000, no working figure), because G's $1,745 is still "needs quote". G's $1,745 (New York County) and $345 (Albany County) are kept in the Inputs notes as the alternatives | needs quote | Newspaper publication |
| `general_liability_insurance_annual` | $1,200 a year ($500 to $1,500) | plan estimate (three quotes before binding, latest Mon 2026-12-21) | Insurance per month, $100, Inputs section 5 |
| `food_warehouse_license_28d_two_years` | $400 ($0 to $400) | fee verified; need unknown | Food warehouse license |
| `attorney_hour` | $400 ($300 to $500) | plan estimate | Attorney hour, paid Wed 2026-11-18 (held by then, before the filing) |
| `accountant_hour` | $300 ($200 to $400) | plan estimate | Accountant hour, paid Fri 2026-11-20 |
| `nys_llc_annual_filing_fee_it204ll` | $25 | verified 2026-10-23 | IT-204-LL |
| `trademark_application_per_class` | $350 ($350 to $850) | verified 2026-10-23 | Trademark, Include = N (G times it outside the first six months) |
| `hired_non_owned_auto_addon_annual` | blank | needs quote | Hired and non-owned auto add-on |
| `additional_insured_building_endorsement_each` | blank | needs quote (G now expects one per building that requires it) | Additional-insured endorsements |
| `mailing_address_mailbox_annual` | blank (G: unknown, not researched) | needs quote; only if the founder will not use a home address | Mailing address, timed in week 1 (before the first outreach email), Include = Y |
| `registered_agent_albany_if_used` | blank (G: unknown, not researched) | needs quote; only on the Albany County route | Registered agent, timed at the filing, Include = N |

Not used: the per-county publication rows (the county-not-chosen row is the budget line), EIN and operating agreement ($0), the optional expedited filing, name-change amendment and Transparency Act filing (each $0 unless a condition applies), and the $9 biennial statement (first due November 2028, outside the six months).

## 5. Deviations from CONTRACTS, in one place

1. Three optional columns added at the end of `campaign_actuals.csv`: `deposit_usd`, `deposit_paid_date`, `survey_responses_min_office`.
2. Brand willingness to pay is logged as `event = budget_probe` on a brand row, with `value_number` in USD per campaign. CONTRACTS 6.6 names the value but not the event.
3. `renewal_answer` carries `yes`, `maybe` or `no` in `value_text` and the committed USD in `value_number`.
4. `org_id` should be the Clay `row_id` for every event, so distinct counts hold across conversation, yes, signed and paid.
5. `drop_id` values follow the workbook's Schedule rows (section 1).
6. The four files carry exactly the columns listed, in order, with no extra columns (CONTRACTS section 6 lets producers add columns; H's layout wins under 6.5). Extra fields go in a separate file.
7. Gate 3 counts a `renewal_answer` only when `value_text` is `yes`, and each brand once.
8. A brand's answer after hearing $1,500 is a second `budget_probe` row with `notes = after_1500`. CONTRACTS events are unchanged.
9. `paid` carries the USD received in that payment; Gate 1's "paid in full" is a brand whose payments add up to the founding package price.
