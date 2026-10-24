# Campaign proposal: field list and render command

Template: `templates/proposal/proposal.html` (v1.1, 2026-10-24). Two pages: the proposal, then a mock report page drawn by `system/dd-report.js` with illustrative placeholders under "Illustrative placeholders, not results". Contents: plan.md Phase 2 "The proposal". Prices: `system/dd-offer.js`. Dates: `system/dd-dates.js` (CONTRACTS section 3).

| Key | Required | Source (CONTRACTS section 6) | Rule |
| --- | --- | --- | --- |
| `brand_name` | yes | `brand_intake.brand_name` | |
| `product_sku` | no | `brand_intake.product_sku` | Product and pack size. Checked for claims words. |
| `prepared_for` | no | `brand_intake.contact_name`, `contact_title` | Business contact only. |
| `proposal_date` | no | | Today. |
| `category` | yes (placeholder until chosen) | `brand_intake.category` | A CONTRACTS section 4 key. Prints the exclusivity line "No other ... brand in the same drop". |
| `tier` | no | | `founding` (default) or `standard`. |
| `extra_offices` | no | | Whole number, default 0. Office rows must equal 5 or 10 plus extras, or the template refuses. |
| `drop_date` | yes | | `YYYY-MM-DD`, Tuesday or Wednesday, window clear of blackouts. Every timeline date comes from it: ship by T-10, receive T-5, day 3 T+2, window close T+4, report T+7, debrief T+10, redemption check T+30 calendar days. A slot such as `[DROP DATE: Tue 2027-01-12]` prints every date as a highlighted `[DATE: ...]` slot (derived, founder to confirm). |
| `ship_by_requested` | no | | Optional earlier ship-by, e.g. 2026-12-22 for campaign zero (CONTRACTS section 3). Refused if later than T-10. |
| `offices[]` | yes | `signed_offices` | `neighborhood`, `industry`, `headcount_band` (CONTRACTS bands), `planned_units` (30 to 80). No company names before signature. Labelled A, B, C... in order. |
| `retailers[]` | one of retailers or `online_site` | `brand_intake.nyc_retailers`; B's `retailers.csv` | `retailer_name`, `street`, `distance`. Only stores with evidence (retailer evidence grade `store_selector`, `brand_claim` or the founder's `seen_on_shelf`). With no store, the headline says "with a code for your online store" instead of "within walking distance". |
| `online_site` | see above | `brand_intake.online_store_url` | Short form, no https://. |
| `map_image` | no | B: `cluster-1-flatiron/` public map, exported as a picture | `[RETAILER MAP]` = slot not filled yet (blocks `--final`). Empty = no map on the page. |
| `map_caption` | no | | Map attribution, e.g. the map data source. |

Fixed text (not fields): the campaign specification, the price box (from `dd-offer.js`), what the brand sends, the cancellation and slip line (from the campaign agreement, section 8), the report summary and "No sales guarantee".

Give-way when full: the map shrinks from 1.3 to 0.95 in, then body text goes from 8.8 to 8.5 pt. Otherwise no PDF.

```bash
node render/render.js proposal path/to/proposal.json out/proposal.pdf --final
```

Samples: `samples/BLANK-placeholders.json`, `samples/SAMPLE-founding.json`, `samples/SAMPLE-standard-10-offices.json`.
