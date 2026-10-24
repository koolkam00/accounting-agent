# Handoff: workstream B (cluster map and seed lists)

Status 2026-10-24: complete for this round. Paths are relative to `desk-drop/`. All files are UTF-8 CSV with one header row, snake_case columns, `Y`/`N` booleans, `YYYY-MM-DD` dates (source dates may be `YYYY-MM`), WGS84 `lat`/`lon` and semicolon-separated lists (CONTRACTS section 5).

## What B consumes

| From | File | What B uses |
| --- | --- | --- |
| Brief and plan | `prompts/B-cluster-map.md`, `plan.md`, `CONTRACTS.md` | Scope, hard rules, enumerations, file formats |
| B's research slices | `cluster-1-flatiron/_work/companies_S1..S4.csv`, `buildings_S1..S4.csv`, `coworking_research.csv`, `retailers_research.csv`, `notes_*.md` | Every row (merged, deduplicated, resolved) |
| D, identity | `desk-drop-identity/tokens/tokens.css` (colours), `desk-drop-identity/fonts/static/*.ttf` (Bricolage Grotesque, Atkinson Hyperlegible Next; SIL OFL) | The public map uses D's ink, cobalt, cobalt tint, paper and stone colours and D's two families (subset and embedded in the SVG). The private map uses the same colours. |
| G, legal | `desk-drop-legal-pack/name-check-log.md` | Gates any public use of the public map. `desk-drop-legal-pack/12-coi-request-own-carrier-building.md` (building certificate requests) applies once a building's `coi_required` is `yes` or `unsure` at intake. |
| H, financial model | none | No input needed |
| Shared | `_shared/geocode.py` | Every pin (run sequentially; cache in `_shared/geocode_cache.json`) |

## B feeds A (Clay ICP tables): the seed lists

Import these unchanged. CONTRACTS 6.1 columns come first, in contract order. Columns after them are additions; producers may add columns.

### `cluster-1-flatiron/companies.csv` (178 rows): the Offices seed

`company_id, company_name, website, industry, building_id, street_address, floor, zip, lat, lon, in_boundary, headcount_band, headcount_scope, headcount_source_url, address_source_url, address_source_date, second_source_url, confidence, in_coworking, coworking_id, linkedin_company_url, notes, found_date` (contract), then `building_lobby_type, candidate_status, lease_status, move_in_date, headcount_source_date, headcount_unknown_reason, address_source_type, second_source_date, coworking_check, bbl, blocks_outside, leased_sf_mentioned, research_slice`.

- **Seed filter:** `candidate_status = candidate` gives 172 rows. All are `in_boundary = Y` and `in_coworking = N`, with band `40-75`, `76-150`, `151-250`, `251-500` or `unknown`. The other six rows are 5 `excluded-coworking` and 1 `excluded-not-office`. They are listed so A's hard gate "inside a coworking space" has evidence.
- **Headcount:** `headcount_band` is from a sourced count only, mostly Built In "Total Employees". `headcount_scope` is `whole-company` on 76 candidates and `nyc-office` on 2; it is `unknown` where the band is unknown. A's Tuesday onsite estimate is A's to make and label; B made none.
- **Freshness:** check `lease_status` and `move_in_date` before scoring. 36 candidates are `signed-not-occupied` and 44 are `occupancy-unconfirmed`. Suggested scoring: occupied above occupancy-unconfirmed above signed-not-occupied, and `confidence` high above medium above low.
- **Lobby:** `building_lobby_type` copies the building's `lobby_type` (walk-up, security desk, loading dock, unknown) for A's "lobby type if findable" field.
- `linkedin_company_url` is blank on every row (LinkedIn was not opened). A or the founder fills it.
- **IDs:** IDs are stable. `company_id` (B-C-###) is unique across `companies.csv` and `near_miss.csv`. `_build/id_registry.json` keeps IDs fixed across rebuilds; new rows get new numbers.

### `cluster-1-flatiron/near_miss.csv` (98 rows)

Same columns as `companies.csv` plus `near_miss_reason`. There are 92 `near-miss-over-500` rows (in the boundary, over 500 company-wide) and 6 `near-miss-outside` rows (0.1 to 1.7 blocks outside the line). Eight reasons say the NYC office alone may fit the band; those are worth a founder look, not a seed.

### `cluster-1-flatiron/coworking.csv` (32 rows): the coworking operator seed

`coworking_id, operator, location_name, street_address, lat, lon, pantry_control, pantry_source_url, source_url, source_date, confidence, notes` (contract), then `in_boundary, blocks_outside, status, floors, building_id, bbl, tenant_company_ids, second_source_url, exclusive_food_contract_signal, research_id, found_date`.

- An operator is one potential office, and only if it controls the pantry. Seed from `in_boundary = Y` and `pantry_control = operator`: 19 of the 24 sites inside qualify.
- `status` is `open`, `open-unverified`, `unverified` or `possibly-closed`. The four IWG rows and WeWork 27 E 28th St need a walk-by first.
- `tenant_company_ids` lists the excluded member companies.

### `cluster-1-flatiron/retailers.csv` (30 rows): the retailer seed for the brand table

`retailer_id, retailer_name, street_address, lat, lon, inside_boundary, blocks_outside, shelf_set, source_url, source_date, confidence, notes` (contract), then `buy_path_tier, public_map, public_map_reason, candidates_within_5_blocks, nearest_candidate_building_id, nearest_candidate_blocks, emerging_brand_evidence, operating_evidence_url, bbl, research_id, found_date`.

- `confidence` grades whether the **store exists and operates at that address**. It says nothing about which brands it carries.
- No row grades a brand-to-store link. A's `nearest_stocked_retailer` and `nearest_retailer_grade` come from each brand's locator or the retailer's store selector (`store_selector`, `brand_claim`), and `seen_on_shelf` comes only from the founder.
- `blocks_outside` is 0 to 7; all 30 are within ten blocks, as defined on the Method tab.

### `cluster-1-flatiron/buildings.csv` (82 rows)

`building_id, street_address, building_name, lat, lon, lobby_type, lobby_source_url, coi_required, coi_source_url, candidate_company_count, verified_on_foot, notes` (contract), then `bbl, also_known_as, zip, in_boundary, candidate_company_ids, other_company_count, coworking_ids, retailer_ids, pluto_numfloors, pluto_yearbuilt, pluto_bldgclass, pluto_office_sqft, pluto_address, pin_check, research_slices`. `verified_on_foot` is blank and only the founder fills it.

### Boundary

`cluster-1-flatiron/boundary.geojson`: one WGS84 polygon, 9 vertices. This replaces A's provisional "14th to 30th St, Sixth Ave to Park Ave S"; the difference is the frontage rule and the Union Square frame.

## B feeds C (website): the public map only

| File | Contents |
| --- | --- |
| `cluster-1-flatiron/public-map.svg` | 1200 x 2048 vector map: the boundary, 16 numbered stores and a numbered list. Fonts are embedded as subsets, so it works as an `<img>` or inline. It has a `<title>` and `<desc>` for accessibility. No company names and no business name. |
| `cluster-1-flatiron/public-map.png` | The same at 1200 x 2048 pixels. |
| `cluster-1-flatiron/map-public.geojson` | The boundary plus the 16 stores: `retailer_id, name, address, buy_path_tier, shelf_set, inside_boundary, blocks_outside, as_of, map_number`. `map_number` matches the numbers on the SVG, so the site can render the list as real text on phones. |
| `cluster-1-flatiron/map-public.kml` | The same for any map tool. |

Suggested alt text: "Map of the Flatiron, NoMad and Union Square office cluster, 14th to 30th Street between Sixth Avenue and Park Avenue South, with 16 natural and specialty food stores within about ten blocks." Keep the map's own footnote: being on the map is not an endorsement and does not mean a store carries any brand. Publish only after G's name check clears. Never use any file with "private" in its name, and never use the CSVs or the workbook.

## B feeds D, E and F

- **D:** `public-map.svg` for the proposal's retailer-map slot. For a brand-specific map, filter `retailers.csv` to the brand's stores and re-run `_build/public_map.py`.
- **E:** `companies.csv` through A's tables. Do not pitch `signed-not-occupied` rows before the lobby directory confirms the move.
- **F:** `route.csv` and `route-private.png` as the drop-day model. The Route tab parameters (pace, waits, 15 minutes per stop) are where F's measured stop times go. `buildings.csv` `lobby_type` and `coi_required` seed the intake questions `receiving_type` and `coi_required`.

## Deviations from CONTRACTS (none rename or drop a contract column)

1. `companies.csv` holds the Companies tab: candidates plus the coworking and not-an-office exclusions. Near-miss rows are in `near_miss.csv`, with the same columns plus `near_miss_reason`, so A's seed file needs no pre-filtering. Both share one `company_id` sequence.
2. `buildings.csv` holds only buildings inside the boundary with at least one candidate or a coworking site (82 rows). Researched buildings with neither are in `cluster-1-flatiron/_work/buildings_no_candidate.csv`.
3. `coworking.csv` includes 8 sites just outside the line, with `in_boundary = N`, because an operator near the edge may still be one office.
4. `coworking_id` on a company row is set only when the company is inside that site (`in_coworking = Y`). Sharing a building without membership is recorded in `coworking_check`.
5. `retailers.csv` uses CONTRACTS' `inside_boundary`, while the other tabs use `in_boundary`. Both spellings follow section 6.1.
