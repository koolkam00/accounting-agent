# Campaign proposal: field list and render command

Template: `templates/proposal/proposal.html` (v1.3, 2026-10-24; review round 2: store table with pin numbers, full-width map arrangements, the mock page follows the route). Two pages: the proposal, then a mock report page drawn by `system/dd-report.js` with illustrative placeholders under "Illustrative placeholders, not results". Contents: plan.md Phase 2 "The proposal". Prices: `system/dd-offer.js`. Dates: `system/dd-dates.js` (CONTRACTS section 3).

| Key | Required | Source (CONTRACTS section 6) | Rule |
| --- | --- | --- | --- |
| `brand_name` | yes | `brand_intake.brand_name` | |
| `product_sku` | no | `brand_intake.product_sku` | Product and pack size: one SKU, or two flavors treated as one (the card then prints each flavor's allergen statement under its own name: `templates/tent-card/FIELDS.md`). Checked with the shared claims list; a claim is an error (v1.3). |
| `prepared_for` | no | `brand_intake.contact_name`, `contact_title` | Business contact only. |
| `proposal_date` | no | | Today. |
| `category` | yes (placeholder until chosen) | `brand_intake.category` | A CONTRACTS section 4 key. Prints the exclusivity line "No other ... brand in the same drop". |
| `tier` | no | | `founding` (default) or `standard`. |
| `extra_offices` | no | | Whole number, default 0. Office rows must equal 5 or 10 plus extras, or the template refuses. |
| `drop_date` | yes | | `YYYY-MM-DD`, Tuesday or Wednesday, window clear of blackouts. Every timeline date comes from it: ship by T-10, receive T-5, day 3 T+2, window close T+4, report T+7, debrief T+10, redemption check T+30 calendar days. A slot such as `[DROP DATE: Tue 2027-01-12]` prints every date as a highlighted `[DATE: ...]` slot (derived, founder to confirm). |
| `ship_by_requested` | no | | Optional earlier ship-by, e.g. 2026-12-22 for campaign zero (CONTRACTS section 3). Refused if later than T-10. |
| `offices[]` | yes | `signed_offices` | `neighborhood`, `industry`, `headcount_band` (CONTRACTS bands), `planned_units` (30 to 80). No company names before signature. Labelled A, B, C... in order. **At most 12** (a standard campaign plus two extra offices): tested with a landscape map and four stores, including the four longest store names in B's `retailers.csv` with a map drawn by B's own script (v1.3). 13 or more is refused: split the route into two campaigns. |
| `retailers[]` | one of retailers or `online_site` | `brand_intake.nyc_retailers`; B's `retailers.csv` | `retailer_name`, `street`, `distance`, optional `map_number` (v1.3). Printed one store per cell, "**Name**, street", with the distance beside it; with a map, a `#` column ties each row to its pin: `map_number`, or the row number when empty (B numbers pins in the order it is given the stores); "-" for a store the map does not show. At most 4. Only stores with evidence (retailer evidence grade `store_selector`, `brand_claim` or the founder's `seen_on_shelf`). With no store, the headline says "with a code for your online store" instead of "within walking distance". |
| `online_site` | see above | `brand_intake.online_store_url` | Short form, no https://. |
| `map_image` | no | B: `cluster-1-flatiron/brand-maps/<slug>.png` (or `.svg`), 2100 x 840, made per brand by B's `_build/public_map.py --brand <slug> --stores <ids>` | About 2.5 to 1, showing the cluster boundary and this brand's stores, **no office pins before signature**. Shown whole (`object-fit: contain`), height from its own shape up to 2.2 in; a portrait picture warns. `[RETAILER MAP]` = slot not filled yet (blocks `--final`). Empty = no map. Tested 2026-10-24 with B's `public-map.png` (1200 x 2140 portrait): legible only as a thumbnail, so B's general map does not fit this slot (`tests/proposal-map/`). |
| `map_caption` | no | | Map attribution, e.g. the map data source. |

Fixed text (not fields): the campaign specification, the price box (from `dd-offer.js`), what the brand sends, the cancellation and slip line (from the campaign agreement, section 8), the report summary and "No sales guarantee".

Fitting (v1.3): thirteen arrangements, each with its own give-way (body text 8.8 to 8.5 pt, then tighter gaps between sections, then the map from its own height, up to 2.2 in, down to 0.95 in). They are: the standard columns; the cancellation note under the price; the cancellation note and "what you send" on the right; four or more offices, the roster across the full width in two halves; nine or more, three narrow tables with the neighborhoods listed once; the timeline as a full-width strip; and (new in v1.3, review round 2) the map and stores across the full width, map left and stores right, one line each with their pin numbers, with the price box moved left where that balances the page. **Every arrangement is tried. Of those that fit, the page keeps the one with the biggest map** (its pins must stay readable), then the one with the fewest give-way steps and the fewest store rows on two lines, then the earlier one. `fit[0].arrangement` names it; `fit[0].tried` lists each one's overflow and map height; `fit[0].map_in`, `tight`, `compact` say what gave way. If none fits, no PDF. Tested with blank, real-length and long founder details (`tests/documents/cases/proposal-*.json`).

The price box and terms restate the campaign agreement v0.8 (`desk-drop-legal-pack/10-brand-campaign-agreement.md`): founding paid in full within five business days of the invoice and before shipping, the lock at $120 per office for up to 10 offices, a refund for any office not placed by the day after the drop; standard 50% on signing and 50% on the placement confirmation email (by T+1, each placed office with its photo; offices not placed come off the invoice); cancel before T−10 (the date is printed) for a full refund less $100, 50% kept from then, full price from the drop day.

The mock page (page 2) takes the brand's name, product and drop date from the proposal, the founder's name from `brand.json`, and **this proposal's own route** (v1.3, R2-12): the same offices, in order, with their industry, headcount band and planned units as delivered. Only placed, depleted, responses, scans, the survey and redemptions are illustrative, scaled from the plan's appendix M pattern. Text slots are grey examples: a finished proposal has nothing yellow on either page.

```bash
node render/render.js proposal path/to/proposal.json out/proposal.pdf --final
```

Samples: `samples/BLANK-placeholders.json`, `samples/SAMPLE-founding.json`, `samples/SAMPLE-standard-10-offices.json` (v1.3: with workstream B's SAMPLE brand map, copied to `samples/maps/SAMPLE-brightside-map-from-B.png` from `cluster-1-flatiron/brand-maps/SAMPLE-brightside.png` on 2026-10-24, and its three stores in B's pin order).
