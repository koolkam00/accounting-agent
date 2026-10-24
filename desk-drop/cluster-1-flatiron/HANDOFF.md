# Handoff: workstream B (cluster map and seed lists)

Status 2026-10-24: revised after independent review rounds 1 and 2 (`cluster-1-flatiron/_review/round-1.md` and `round-2.md`, builder response at the end of each). Paths are relative to `desk-drop/`. All files are UTF-8 CSV with one header row, snake_case columns, `Y`/`N` booleans, `YYYY-MM-DD` dates (source dates may be `YYYY-MM`), WGS84 `lat`/`lon` and semicolon-separated lists (CONTRACTS section 5).

## What B consumes

| From | File | What B uses |
| --- | --- | --- |
| Brief and plan | `prompts/B-cluster-map.md`, `plan.md`, `CONTRACTS.md` | Scope, hard rules, enumerations, file formats |
| B's research slices | `cluster-1-flatiron/_work/companies_S1..S4.csv`, `buildings_S1..S4.csv`, `coworking_research.csv`, `retailers_research.csv`, `notes_*.md`, `builtin_hq_2026-10-24.csv`, `headcount_second_2026-10-24.csv` | Every row (merged, deduplicated, resolved); the second headcounts of review round 2 |
| D, identity | `desk-drop-identity/tokens/tokens.css` (colours), `desk-drop-identity/fonts/static/*.ttf` (Bricolage Grotesque, Atkinson Hyperlegible Next; SIL OFL) | The public map and the brand maps use D's ink, cobalt, cobalt tint, paper and stone colours and D's two families (subset and embedded in the SVG). The private map uses the same colours. |
| D, identity | `desk-drop-identity/HANDOFF.md` row "B, cluster map" and `desk-drop-identity/tests/proposal-map/SAMPLE-landscape-map.png` | D's request for a per-brand landscape map (about 2.5 to 1, boundary and that brand's stores, no office pins). Built as `brand-maps/` (below), styled after D's own SAMPLE map. |
| G, legal | `desk-drop-legal-pack/name-check-log.md` | Gates any public use of the public map and the brand maps. `desk-drop-legal-pack/12-coi-request-own-carrier-building.md` (building certificate requests) applies once a building's `coi_required` is `yes` or `unsure` at intake. |
| H, financial model | none | No input needed |
| Shared | `_shared/geocode.py` | Every pin (run sequentially; cache in `_shared/geocode_cache.json`) |

No build script calls sec.gov. `_build/assemble.py` fetches only data.cityofnewyork.us (PLUTO, cached) and `_build/build.py` only data.ny.gov (subway stations, cached). Rows that cite sec.gov say so in their notes; the agent will not re-open those pages (see `README.md`, "What is not done"; `REPORT.md` is pending, because the harness refused the builder's write and the orchestrator holds its text).

## B feeds A (Clay ICP tables): the seed lists

Import these unchanged. CONTRACTS 6.1 columns come first, in contract order. Columns after them are additions; producers may add columns.

### `cluster-1-flatiron/companies.csv` (168 rows): the Offices seed

`company_id, company_name, website, industry, building_id, street_address, floor, zip, lat, lon, in_boundary, headcount_band, headcount_scope, headcount_source_url, address_source_url, address_source_date, second_source_url, confidence, in_coworking, coworking_id, linkedin_company_url, notes, found_date` (contract), then `hq_city, hq_in_nyc, hq_source_url, headcount_count, headcount_check, headcount_second_count, headcount_second_source_url, headcount_second_source_date, parent_company, parent_company_source, building_lobby_type, candidate_status, lease_status, move_in_date, headcount_source_date, headcount_unknown_reason, address_source_type, second_source_date, coworking_check, bbl, blocks_outside, leased_sf_mentioned, research_slice`.

- **Seed filter:** `candidate_status = candidate` gives 162 rows. All are `in_boundary = Y` and `in_coworking = N`, with band `40-75`, `76-150`, `151-250`, `251-500` or `unknown`, plus one `under-40` row (Normal Computing: a source puts its new NYC HQ at about 30 people, the brief's 30 to 39 founder's call). The other six rows are 5 `excluded-coworking` and 1 `excluded-not-office`. They are listed so A's hard gate "inside a coworking space" has evidence.
- **Confidence (candidates):** 51 high, 80 medium, 31 low. An undated Built In, Deskpass or LiquidSpace profile is never the under-24-month source: it only confirms a dated or own-site source, so a row resting on one alone is low (review round 2).
- **Headcount:** every band is whole-company and single-source unless `headcount_check = agree`. `headcount_band` is from a sourced count only, mostly Built In "Total Employees" (undated). At review round 2 every banded candidate was tested against a second public count (`headcount_second_count`, `_source_url`, `_source_date`: Revelio Labs pages as of March 2026, or the company's own page): `agree` 21, `disagree` 22 (band now `unknown`, both counts kept, reason in `headcount_unknown_reason`), `single-source` 23 (no second count found), `scope-differs` 1 (Normal Computing), `no-count` 95. Ten firms whose second count is over 500 moved to `near_miss.csv` (`headcount_check = over-500-second-source`). `headcount_count` is the count the band rests on. `headcount_scope` is `whole-company` on 43 candidates, `nyc-office` on 2 and `unknown` on 117. Weight `agree` above `single-source`. A's Tuesday onsite estimate is A's to make and label; B made none, and the Revelio counts are third-party estimates of the whole company, not onsite counts.
- **Where the company is based:** `hq_city` is the HQ city as the row's Built In offices page prints it (opened 2026-10-24); where Built In is silent, the row's own sources, the company's own page or the Revelio page (review round 2). `hq_in_nyc` is `Y`, `N` or `unknown`, and `hq_source_url` is the page. 12 of the 45 banded candidates have `hq_in_nyc = N` and 2 are unknown: a whole-company band for them can be far larger than the New York office. Weight `nyc-office` bands above `whole-company` bands with `hq_in_nyc = N`.
- **Parent:** `parent_company` names an owner where a source does (6 candidates, for example Farmacy Beauty: Procter & Gamble), else `unknown`. A parent far over 500 matters to "firms under 500 preferred".
- **Freshness:** check `lease_status` and `move_in_date` before scoring. 87 candidates are `occupied`, 45 `occupancy-unconfirmed` and 30 `signed-not-occupied`. 30 are occupied with a sourced band. `move_in_date` is `YYYY-MM` or `unknown` (blank when occupied or occupancy-unconfirmed); a planned season is in the notes. Suggested scoring: occupied above occupancy-unconfirmed above signed-not-occupied, and `confidence` high above medium above low.
- **Lobby:** `building_lobby_type` copies the building's `lobby_type` (walk-up, security desk, loading dock, unknown) for A's "lobby type if findable" field.
- **Unknowns:** a floor or website nobody could confirm says `unknown` (no blanks). `linkedin_company_url` is blank on every row because LinkedIn was not opened; A or the founder fills it.
- **IDs:** IDs are stable. `company_id` (B-C-###) is unique across `companies.csv` and `near_miss.csv`. `_build/id_registry.json` keeps IDs fixed across rebuilds; new rows get new numbers.

### `cluster-1-flatiron/near_miss.csv` (108 rows)

Same columns as `companies.csv` plus `near_miss_reason`, `near_miss_class`, `company_wide_count_cited` and `nyc_office_may_fit`.

- `near_miss_class`: `just-over-500 (501 to 1,000)` 29 rows (the brief's "just over 500"), `over-1,000 (1,001 to 4,999)` 45, `not-near (5,000 or more)` 28, and `outside-line` 6 (0.1 to 1.7 blocks outside the line). `company_wide_count_cited` is the count the class rests on (Built In, Wikipedia, the company's own page or, for the ten rows moved at review round 2, the Revelio page in `headcount_source_url`, as the reason says).
- Moved here at review round 2 (second count over 500): Mercury, Harvey, Sigma Computing, Synthesia, Clay, Sierra, Seedtag, Valon, GameChanger and Nourish. Their Built In count is kept as `headcount_second_count`.
- `nyc_office_may_fit = Y` on 12 rows where a source suggests the New York office alone could fit (six of the moved rows: a small NYC lease against an HQ elsewhere). Those are worth a founder look whatever their class; none is a seed.

### `cluster-1-flatiron/coworking.csv` (32 rows): the coworking operator seed

`coworking_id, operator, location_name, street_address, lat, lon, pantry_control, pantry_source_url, source_url, source_date, confidence, notes` (contract), then `in_boundary, blocks_outside, status, floors, building_id, bbl, tenant_company_ids, second_source_url, exclusive_food_contract_signal, research_id, found_date`.

- An operator is one potential office, and only if it controls the pantry. Seed from `in_boundary = Y` and `pantry_control = operator`: 19 of the 24 sites inside qualify.
- `source_date` is the publication date of a dated article; a live operator page carries the date it was opened. Every `high` row has its independent source in `second_source_url` (19 of 19).
- `status` is `open`, `open-unverified`, `unverified` or `possibly-closed`. The four IWG rows, Le Parc (now `low`) and WeWork 27 E 28th St need a walk-by first.
- `tenant_company_ids` lists the excluded member companies.

### `cluster-1-flatiron/retailers.csv` (30 rows): the retailer seed for the brand table

`retailer_id, retailer_name, street_address, lat, lon, inside_boundary, blocks_outside, shelf_set, source_url, source_date, confidence, notes` (contract), then `buy_path_tier, public_map, public_map_reason, public_description, walk_minutes_from_cluster_edge, candidates_within_5_blocks, nearest_candidate_building_id, nearest_candidate_blocks, emerging_brand_evidence, operating_evidence_url, bbl, research_id, found_date`.

- `confidence` grades whether the **store exists and operates at that address**. It says nothing about which brands it carries. Kalustyan's is now `medium` (one dated source), and Wegmans Astor Place is now tier B (review round 2).
- No row grades a brand-to-store link. A's `nearest_stocked_retailer` and `nearest_retailer_grade` come from each brand's locator or the retailer's store selector (`store_selector`, `brand_claim`), and `seen_on_shelf` comes only from the founder.
- `blocks_outside` is 0 to 7; all 30 are within ten blocks, as defined on the Method tab. `walk_minutes_from_cluster_edge` turns that into minutes at 73 m a minute.

### `cluster-1-flatiron/buildings.csv` (81 rows)

`building_id, street_address, building_name, lat, lon, lobby_type, lobby_source_url, coi_required, coi_source_url, candidate_company_count, verified_on_foot, notes` (contract), then `bbl, also_known_as, zip, in_boundary, candidate_company_ids, other_company_count, coworking_ids, retailer_ids, pluto_numfloors, pluto_yearbuilt, pluto_bldgclass, pluto_office_sqft, pluto_address, pin_check, entrance_note, research_slices`. `verified_on_foot` is blank and only the founder fills it.

- **Pins:** every located row in every file passed a block-face test against NYC street centreline address ranges (the addressed side of the street, and at least 15 m nearer the addressed street than the parallel one). Pins that failed were moved to the addressed frontage and say so in `pin_check` (buildings) or `notes` (other files). At review round 2, corner-lot pins on avenue addresses (they sat nearer the side street) moved to the avenue frontage near the corner; `entrance_note` names both streets. `bbl` never changes. Per-pin results: `cluster-1-flatiron/_build/out/pin_qa.csv`.

### Boundary

`cluster-1-flatiron/boundary.geojson`: one WGS84 polygon, 9 vertices, exterior ring counter-clockwise (RFC 7946). This replaces A's provisional "14th to 30th St, Sixth Ave to Park Ave S"; the difference is the frontage rule and the Union Square frame.

## B feeds C (website): the public map only

| File | Contents |
| --- | --- |
| `cluster-1-flatiron/public-map.svg` | 1200 x 2024 vector map: the boundary, 14 numbered stores and a numbered list with each store's walking minutes from the cluster. Fonts are embedded as subsets, so it works as an `<img>` or inline. It has a `<title>` and `<desc>` for accessibility. No company names and no business name. |
| `cluster-1-flatiron/public-map.png` | The same at 1200 x 2024 pixels. |
| `cluster-1-flatiron/map-public.geojson` | The boundary plus the 14 stores: `retailer_id, name, address, buy_path_tier, shelf_set, inside_boundary, blocks_outside, walk_minutes_from_cluster_edge, as_of, map_number`. `map_number` matches the numbers on the SVG. `shelf_set` now holds plain public wording of the store's format (for example "Natural and organic supermarket"), never research notes. |
| `cluster-1-flatiron/map-public.kml` | The same for any map tool. |

**Changed at review round 2, C must re-run `website/tools/build_map.py`:** Wegmans Astor Place moved from tier A to tier B (hollow marker), so `map_number` changed for four stores (Whole Foods Union Square 3 to 2, Whole Foods Chelsea 4 to 3, Whole Foods NoMad 5 to 4, Wegmans 2 to 5), and five store pins moved a few metres to their addressed frontage. Still 14 stores (review round 1 cut 16 to 14). The property names C reads are unchanged.

Suggested alt text: "Map of the Flatiron, NoMad and Union Square office cluster, 14th to 30th Street between Sixth Avenue and Park Avenue South, with 14 natural and specialty food stores within about ten blocks." Keep the map's own footnote: being on the map is not an endorsement and does not mean a store carries any brand. Publish only after G's name check clears. Never use any file with "private" in its name, and never use the CSVs or the workbook.

## B feeds D, E and F

- **D (proposal store table and grades):** store evidence grades are **not** in `retailers.csv`, by design (it grades whether a store exists, not what it stocks). Take `nearest_stocked_retailer` and `nearest_retailer_grade` (`store_selector`, `brand_claim`, `seen_on_shelf` from the founder only) from A's brand table; use `retailers.csv` only for each store's address, walking minutes and the map. This answers `desk-drop-identity/HANDOFF.md`, which asks for stores "with evidence (`retailers.csv` grade ...)".
- **D (proposal retailer-map slot):** `cluster-1-flatiron/brand-maps/<slug>.png` (2100 x 840 pixels, drawn at 1050 x 420, 2.5 to 1) and `.svg`: the boundary and that brand's stores, numbered in the order given, with no office pins and no business name. Make one with `python3 cluster-1-flatiron/_build/public_map.py v/bin/python --brand <slug> --stores <retailer_ids>` and then `NODE_PATH="$(npm root -g)" node cluster-1-flatiron/_build/render.js cluster-1-flatiron`, where `v/bin/python` is a Python with fontTools (`python3 -m venv v && v/bin/pip install fonttools`; README, "Make a map for one brand"). This mode never touches the public files. `brand-maps/SAMPLE-brightside.png` is a layout test with a SAMPLE banner. It was checked in D's own template: `cluster-1-flatiron/_build/out/qa/proposal-test/SAMPLE-proposal-with-brand-map.png` (rendered with `desk-drop-identity/render/render.js`, output kept in B's folder). It shows whole, but D's fit step shrank it to about 1 in tall on that page, so store names print at about 5 pt. D may want to keep the map at full column height.
- **E:** `companies.csv` through A's tables. Do not pitch `signed-not-occupied` rows before the lobby directory confirms the move. Pumpkin Pet Insurance is `low`: its own site gives 666 Third Ave, not 432 Park Ave S.
- **F:** `route.csv` and `route-private.png` as the drop-day model. The Route tab parameters (pace, waits, 15 minutes per stop, `cases_per_load`, `reload_minutes`) are where F's measured times go. The model's answer: ten stops do not fit one 8 to 11 am loop with drinks (about 207 minutes with one reload); the default is five offices a morning across Tuesday and Wednesday, or a courier for the second loop. `route.csv` adds `load`, `reload_minutes_before`, `entrance_note` and `notes`. `buildings.csv` `lobby_type` and `coi_required` seed the intake questions, but the two enumerations differ (CONTRACTS 6.1 against 6.3), so map them:

| `buildings.csv` `lobby_type` | intake `receiving_type` |
| --- | --- |
| `walk-up` | `walk-up` |
| `security desk` | `front desk` |
| `loading dock` | `loading dock` |
| `unknown` | `other` (ask at intake) |

| `buildings.csv` `coi_required` | intake `coi_required` |
| --- | --- |
| `yes` | `yes` |
| `no` | `no` |
| `unknown` | `unsure` |

## Deviations from CONTRACTS (none rename or drop a contract column)

1. `companies.csv` holds the Companies tab: candidates plus the coworking and not-an-office exclusions. Near-miss rows are in `near_miss.csv`, with the same columns plus four near-miss columns, so A's seed file needs no pre-filtering. Both share one `company_id` sequence.
2. `buildings.csv` holds only buildings inside the boundary with at least one candidate or a coworking site (81 rows). Researched buildings with neither are in `cluster-1-flatiron/_work/buildings_no_candidate.csv`.
3. `coworking.csv` includes 8 sites just outside the line, with `in_boundary = N`, because an operator near the edge may still be one office.
4. `coworking_id` on a company row is set only when the company is inside that site (`in_coworking = Y`). Sharing a building without membership is recorded in `coworking_check`.
5. `retailers.csv` uses CONTRACTS' `inside_boundary`, while the other tabs use `in_boundary`. Both spellings follow section 6.1.
6. One candidate (Normal Computing) has band `under-40`. The brief makes 30 to 39 onsite the founder's call, so it stays a candidate with the reason in its notes.
