# Campaign report: field list and render command

Template: `templates/report/report.html` (v1.1, 2026-10-24). Renderer: `system/dd-report.js` (the same code draws the proposal's mock page). One JSON object is one report. Layout: plan.md appendix M and "Measurement and the brand report".

The operations workstream (F) fills this from its tracker. Keys use the CONTRACTS section 6.5 column names wherever one exists.

## Campaign fields

| Key | Required | Source | Rule |
| --- | --- | --- | --- |
| `brand_name` | yes | `paid_brands.brand_name` | |
| `product_sku` | no | `paid_brands.product_sku` | |
| `cluster` | no | | Defaults to "Flatiron, NoMad and Union Square". |
| `tier` | no | `campaign_actuals.tier` | `founding` or `standard`. |
| `campaign_id` | yes | `campaign_actuals.campaign_id` | |
| `drop_date` | yes | `campaign_actuals.drop_date` | `YYYY-MM-DD`, Tuesday or Wednesday, window clear of blackouts (checked with the CONTRACTS section 3 rules). The window (T to T+4), report due date (T+7) and day-30 check are worked out from it. A slot such as `[DROP DATE: Tue 2027-01-12]` prints every derived date as a highlighted slot. |
| `report_date` | no | `campaign_actuals.report_delivered_date` | Empty prints the due date, T+7. |
| `prepared_by` | no | | Empty prints `FOUNDER_NAME` from `brand.json`. |

## Office rows: `offices` (array, one object per office, 1 to 12)

| Key | Required | Source | Rule |
| --- | --- | --- | --- |
| `office_label` | no | | `A`, `B`, `C`... (default by position), or the office's name only if it agreed to be named. |
| `industry` | yes | `signed_offices` (F's office record) | |
| `headcount_band` | yes | from `signed_offices.tuesday_headcount` | One of `40-75`, `76-150`, `151-250`, `under-40`, `251-500`, `unknown` (CONTRACTS section 4). Prints "40 to 75". |
| `units_delivered` | yes | per-office `units_delivered` | Whole number. Units handed over at the office on drop day. |
| `units_placed` | yes | per-office `units_placed` | Whole number. Units visible in the placement photo. Error if more than delivered. |
| `placed_within_1bd` | yes | per-office placement lag | `Y` or `N`. `N` prints an asterisk and "placed after the first business day". Sum of `units_placed` where `Y` = `campaign_actuals.units_placed_within_1bd`. |
| `units_topped_up` | no | per-office `units_topped_up` | Whole number, empty = 0. Reserve units added on day 3. |
| `units_depleted_day5` | yes | per-office `units_depleted_day5` | Whole number. Error if more than placed plus topped up. |
| `survey_responses` | yes | per-office `survey_responses` | Whole number. Under 5 warns (the office's commitment); it is reported as it is. |
| `qr_scans` | yes | per-office `qr_scans` | Whole number, from the office's short link. |
| `placement_photo` | yes | photo file | Path relative to the JSON file, or a picture chosen in the panel. `[PHOTO]` = not attached yet (blocks `--final`). Empty = the office sent none: prints "No photo received". |
| `later_photo` | yes | photo file | Same rules. |
| `later_photo_day` | no | | `5` (default) or `3`. |

## Survey and purchase fields

| Key | Source | Rule |
| --- | --- | --- |
| `survey_tried_yes` | survey export; `campaign_actuals.survey_tried_yes` | Count. Error if more than the total responses (the sum of the office rows). |
| `tried_no_didnt_see`, `tried_no_not_for_me`, `tried_no_gone` | survey export, question 1 follow-up | Optional counts. Printed as "Did not try: ...". |
| `survey_rating_avg`, `survey_rating_n` | survey export | Average of the 1-to-5 question, one decimal, and how many ratings. |
| `survey_buy_yes`, `survey_buy_maybe`, `survey_buy_no` | survey export | Counts. Shares are worked out and printed beside the counts; if fewer people answered than responded, it says "of N who answered". |
| `comments_total` | survey export | Optional. "Three of N comments". |
| `comment_1`, `comment_2`, `comment_3` | survey export, free text | **Word for word.** Never reword or fix spelling. Replace any name or identifying detail with `[name removed]` (legal pack file 13, rule D10); mark any cut with `[...]`. Neither is read as a placeholder. A comment containing an email address or phone number is refused. |
| `code_redemptions_to_date` | the brand; `campaign_actuals.code_redemptions_day30` at day 30 | Count the brand reports. |
| `code_redemptions_as_of` | | Date of the brand's count. Empty prints the report date. |
| `retailer_velocity` | the brand | Optional text: only store-level sales the brand shares, with its source. Labelled "suggestive only". |
| `learned` | founder | Three lines, one bullet each. Checked for claims and soft-ladder words. |
| `recommendation` | founder | Renew into which offices, adjust what, or stop. |

## Fixed parts (not fields)

- The ladder strip: Delivered, Placed, Depleted, Responded, Scanned, Purchased, Incremental (not measured). Totals are computed from the office rows.
- The limitations paragraph: `DDReport.LIMITATIONS` in `system/dd-report.js`. The render checks it is present and unchanged on every report.

## Give-way order when the page is full

Thumbnails shrink to 0.46 in, comments go from 8.75 to 8.25 pt, spacing tightens, the "learned" lines go from 9.5 to 8.5 pt. With six or more offices, the thumbnails then move to the evidence page and page 1 keeps the count of photos received. Last, the comments go to 8 pt. Never changed: the numbers, the ladder, the comments' words, the limitations paragraph. If it still does not fit, no PDF is written (exit 2).

## Render command

```bash
node render/render.js report path/to/report.json out/report.pdf --final --json
```

Exit codes: 0 written, 1 usage or crash, 2 template error (no PDF), 3 `--final` found placeholders, SAMPLE values or unfilled `brand.json` contacts. The PDF is one page, plus an evidence page when any photo is attached.

Samples: `samples/BLANK-placeholders.json`, `samples/SAMPLE-5-offices.json`, `samples/SAMPLE-10-offices-long-comments.json` (the brief's test: ten offices, three long comments, photos, one office with no later photo and four responses).
