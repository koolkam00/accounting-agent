# Workstream B review, round 3

Reviewer: independent adversarial review of `cluster-1-flatiron/`, after the builder's round-2 fixes. Date: 2026-10-24 (container clock about 05:00 to 05:30 UTC).

I read:
- `prompts/B-cluster-map.md`, `plan.md` and `CONTRACTS.md`;
- the README and HANDOFF, every deliverable, the Method tab, the `_work/` notes and progress logs, and the `_build/` code;
- `_review/round-1.md` and `round-2.md` with both builder responses;
- the README and HANDOFF of D, G and H.

I fixed nothing. My evidence and scripts are in `_review/evidence-r3/`, with the working log in `NOTES.md` there.

**Counts: 1 blocker, 1 major, 8 minors.**

## What I ran

**Data checks**
- Contract columns, every enumeration, Y/N fields and date formats, on all seven CSVs.
- Every workbook tab against its CSV: headers identical, row counts identical.
- The confidence floor, row by row, on companies, near-miss and coworking (`evidence-r3/floor.py`). An undated Built In, Deskpass or LiquidSpace page never counts as fresh. "Fresh" means dated on or after 2024-10-24, or the company's own live page. Result: 0 violations.

**Spot checks and pins**
- **Ten company rows**, picked with `random.seed(20261024303)` from the 114 candidates that no slice, builder or round-1/2 check had covered. I opened every address source and second source with curl, using a generic browser User-Agent with no personal data. I also opened the Built In or Revelio page wherever a band or second count is given.
- **Ten pins**, picked with the same seed: 7 from the 47 buildings no earlier check covered, plus 3 public-map stores.
  - I re-ran `_shared/geocode.py` on each, one at a time.
  - I wrote my own CSCL block-face test (`face3.py`).
  - I pulled each pin's own tax-lot polygon from NYC MapPLUTO through the public Carto SQL endpoint ZoLa uses (`lots.py`), and drew lot plus pin plus geocoder point on OpenStreetMap at zoom 19 (`pins-r3-lots.png`).
  - I then ran the lot test on all 143 building, store and coworking pins (`pin_in_lot.csv`, `pins-r3-outside.png`).

**Route, map and workbook**
- **Route legs:** three legs recomputed with my own Dijkstra on the CSCL centreline graph (`legs3.py`).
- **Phone map:** `map-private.html` in Playwright Chromium at 390 x 844 (`phone.js`). I checked the default view, Key, Find, a popup for 381 Park Ave S, a popup for 215 Park Ave S, and walk session 5. I looked at every PNG. There were no page or console errors, and `scrollWidth` was 390.
- **Map files:** all 8 KML files parse and all style references resolve. The three GeoJSON rings are closed and counter-clockwise.
- **Public files:** `map-public.geojson`, `map-public.kml`, `public-map.svg` and the brand map scanned for every company, coworking and operator name, every B-C, B-B and B-W ID, and the business name. I looked at `public-map.png`, `route-private.png` and `brand-maps/SAMPLE-brightside.png`.
- **Brand map:** the brand-map command run in a scratch copy, with fontTools in a scratch venv, on D's long-name test set. The public files' md5 sums did not change.
- **Workbook:** recalculated in LibreOffice. 0 formula errors. Method live counts are 162, 51, 80 and 31. Route reads 207 min, finish 11:27, "over by 27 min".
- **Walk:** walk coverage checked against Buildings, Retailers and Coworking.

**Sources**
- Store and coworking sources opened:
  - NYS licences 767591 (Eden Gourmet Gramercy), 742908 (Fairway Kips Bay) and 624652 (Citarella);
  - NYREJ 57154 (Convene Hospitality Group's acquisition of NeueHouse);
  - Whole Foods' 2026 LEAP release;
  - the Whole Foods Union Square page. Its structured data gives 40.7347324, -73.9908921, which is the pin exactly.
- Parent companies checked on Wikipedia, opened 2026-10-24:
  - General Assembly: "purchased by the Adecco Group in 2018" (page last edited 2026-10-05);
  - The Corcoran Group: "Parent Compass, Inc." (last edited 2026-05-27);
  - BrainPOP: "In 2022, Kirkbi A/S ... acquired BrainPop" (last edited 2026-10-09).

**Privacy**
- A local grep for the account owner's identifiers finds none. The only hit is a broker's first name inside a Commercial Observer URL slug.
- No build script calls sec.gov.
- Nothing has been published.

---

## Findings (ranked)

### Blockers

| ID | Location | What is wrong | Evidence | Exact fix |
| --- | --- | --- | --- | --- |
| R3-01 | `cluster-1-flatiron/REPORT.md` (missing). Also `README.md` lines 5, 17, 60, 65 and 73; `HANDOFF.md` line 17; Method row 111 ("the drafted REPORT.md, 'Rule breaches'") | **R1-01 and R2-01 are still open after three rounds.** CONTRACTS section 1 requires `REPORT.md` in every output folder, and the brief's "Report back" is its content. The builder's interim fix is honest: README line 5 says the file is pending, and Method holds A1 to A13, Q1 to Q6 and the changelog. But the founder still has no report-back message. One item asked for in it exists nowhere in the deliverables: **companies by confidence and band**, the cross-tab. It appears only in the round-2 builder response, inside a review file. The "full account" of the SEC privacy breach is promised in a REPORT that does not exist. The builder cannot fix this alone, because the harness refuses its write. | `ls cluster-1-flatiron/` at about 05:00 and again at 05:28 UTC: no REPORT.md. `find desk-drop -name 'REPORT*'` finds only G's and H's (plus copies inside D's review scratch). I grepped Method and README for a band-by-confidence table: none. My own cross-tab of the 162 candidates (high / medium / low): 151-250: 7/3/1; 251-500: 7/4/5; 40-75: 0/8/2; 76-150: 5/2/0; under-40: 0/1/0; unknown: 32/62/23. | **Orchestrator:** save the builder's REPORT text as `cluster-1-flatiron/REPORT.md`, then have the builder bring it to the current numbers and check it against the brief's list. It must contain: built and boundary; counts by tab (168, 81, 32, 30, Route 10, Walk 116, Near-miss 108); the confidence-by-band table above; route 207 min with one reload (11:27), and 187 min on one loop; walk 10 sessions, 116 stops, 782 min; A1 to A13; changelog rounds 1 to 5 (plus 6 for this round); "Rule breaches"; and Q1 to Q6 last, each with its default. Until then, add the cross-tab to the Method tab so the content is at least in a deliverable. |

### Majors

| ID | Location | What is wrong | Evidence | Exact fix |
| --- | --- | --- | --- | --- |
| R3-02 | `_build/public_map.py` lines 349 to 362 (store labels in brand mode); `HANDOFF.md` line 88 (D section); `desk-drop-identity/HANDOFF.md` line 16 | **D's open request to B is unanswered, and the per-brand map is unreadable for a common store set.** D's HANDOFF (04:31 UTC) asks for "a numbers-only label option", because long names collide. B's round-2 fix moved only *street* labels clear of the scale bar. B's HANDOFF (04:59) does not mention D's request, and the script has no label option (argparse: `--brand`, `--stores`, `--layout`, `--sample` only). For a brand stocked at the Third Ave and Gramercy stores (Westside 84 Third, Westside 180 Third, Eden Gramercy), store pins and labels overprint each other and fall on the frame edge. That is exactly the brand founder's "useful or clutter" test, and the proposal map is the plan's "selling tool" (plan.md line 276). | In a scratch copy I ran `python3 _build/public_map.py <venv-python> --brand SAMPLE-longnames --stores B-R-018,B-R-020,B-R-013,B-R-016 --sample`, then `render.js` (`evidence-r3/brand-map-long-names-current-script.png`). Results: pin 2 sits under label 4; label 3 is cut to "Westsid" by pin 4; "Eden Gourmet" sits under the scale bar; the "23rd St" street label is hidden; all four stores sit on the bottom frame edge. D's own test (`desk-drop-identity/tests/proposal-map/B-SAMPLE-long-names-map.png`) shows the same failure. The public files' md5 sums were unchanged. | 1) Add `--labels numbers\|names` (default `names`). With `numbers`, draw only the numbered pin and leave the names to D's store table. 2) In `names` mode, place labels with a simple collision pass: try right, left, above and below in turn, and use a leader line if all four overlap a pin, a label or the scale-bar box. 3) Pad the extent so no pin lies within 40 px of the frame. 4) Re-run D's four-store long-name set and the SAMPLE-brightside set, look at both PNGs, and save them to `_build/out/qa/`. 5) In HANDOFF line 88, answer D's request in words: the option, its default, and that pin order follows `--stores`. |

### Minors

| ID | Location | What is wrong | Evidence | Exact fix |
| --- | --- | --- | --- | --- |
| R3-03 | `_build/frontage.py` `corner()`; `buildings.csv` lines 13 (B-B-011 860 Broadway), 63 (B-B-060 220 Fifth), 73 (B-B-072 386 PAS) and 7 (B-B-005 19 USW); `retailers.csv` line 14 (B-R-015 New Foods of India); `coworking.csv` line 16 (B-W-015 The Yard, 234 Fifth) | **The round-2 corner move pushed some pins off their own lot, onto the neighbour's frontage.** The rule puts a moved pin "at least 26 m from the cross street's centreline". On a corner lot with a short avenue frontage, that lands past the lot line. Every pin is still on the right block face, so the spot check passes and none of the ten route stops is affected. But a walker following the map is pointed at the next door. | My lot test of all 143 pins against their own MapPLUTO polygons: 18 are outside their lot (`pin_in_lot.csv`). On OSM z19 (`pins-r3-outside.png`): 860 Broadway's pin is 9.2 m outside, in front of 862 to 864 Broadway (Chipotle). The Yard's 234 Fifth pin is 9.7 m outside, on 236 Fifth (Ilili). New Foods of India's pin (121 Lexington) is 5.1 m outside, on Kalustyan's building at 123 Lexington. 386 PAS is 3.6 m outside, in front of 394 to 396. 19 USW is 3.1 m outside, at the line with 25 USW (Carlyle Court). 220 Fifth is 2.0 m outside. The rest: 119 Fifth is 3.7 m outside. 287 PAS, 381 PAS, 1115 Broadway, 1216 Broadway, 113 University Pl and Merci Market (59 Fifth) are 0.7 to 2.3 m outside, on the sidewalk at their frontage. Whole Foods Union Square is 17.3 m outside, but that pin is the store's own published coordinate, at the Broadway corner. The coworking rows at 860 Broadway and 386 PAS repeat the building pins. | In `frontage.corner()`, clamp the moved pin inside the lot. Take the lot polygon from MapPLUTO, and put the pin at the midpoint of the lot's frontage on the addressed street, 3 m inside the lot line. Use the 26 m rule only when the frontage is longer than about 35 m. Add "pin inside own lot, or within 3 m of its frontage" to `pin_qa.py`. Keep a store's own published coordinate only if it sits on its own lot or frontage; otherwise note it. |
| R3-04 | `companies.csv` `lease_status` on lines 48 (B-C-052 Bombas), 49 (B-C-051 Morning Brew), 56 (B-C-061 Daily Harvest), 63 (B-C-075 Retool), 105 (B-C-111 Wellcom) and 130 (B-C-127 accessiBe); `HANDOFF.md` line 32; `README.md` line 75 ("30 of those are occupied") | **The broker's stale-tenant test.** Six candidates are `occupied` although their only current source is an undated Built In profile. B's own Method row 48 says such profiles are "often stale", and B's floor rule makes such rows `low`. Method's definition says `occupancy-unconfirmed` means "lease press only", which fits Wellcom (CO 2024-08-27 plus Built In). B's own R2-04 note says Retool's own site gives only its San Francisco address. HANDOFF tells A to score `occupied` first. Four of these rows are inside the README's "30 occupied with a sourced band". | My cross-tab of `lease_status` by `confidence` for candidates: occupied and low = 6, the rows listed. I opened the Daily Harvest Built In page myself: it shows "HQ New York 37 West 20th Street" and "267 Total Employees", undated. | Set these six to `occupancy-unconfirmed` and note "only an undated profile places it here; check the lobby directory". Add a rule to `assemble.py`: `occupied` needs a dated source under 24 months or the company's own live page. Then update HANDOFF line 32 and README line 75 (30 becomes 26 occupied with a band). |
| R3-05 | `companies.csv` `parent_company` on lines 62 (B-C-074 General Assembly), 143 (B-C-150 The Corcoran Group) and 97 (B-C-098 BrainPOP, route stop 4); notes of B-C-150; `HANDOFF.md` line 31 | Parents with a large owner are recorded as `unknown`, although a public source names them. "Firms under 500 preferred" makes this matter, and HANDOFF line 31 says the column "names an owner where a source does". The Corcoran note also says "a large brokerage, check for over-500 before use", which is a size characterisation without a source. | Wikipedia, opened 2026-10-24. General Assembly was "purchased by the Adecco Group in 2018" ($413 million; edited 2026-10-05). The Corcoran Group lists "Parent Compass, Inc." (edited 2026-05-27). BrainPOP: "In 2022, Kirkbi A/S ... acquired BrainPop", with owner Kirkbi in the infobox (edited 2026-10-09). | Fill `parent_company` and `parent_company_source` for the three rows, with those URLs and dates. Reword Corcoran's note to "Parent Compass, Inc. (Wikipedia, opened 2026-10-24); Corcoran's own headcount not sourced; founder to confirm before approach". Run one pass on the other 116 unknown-band candidates for an owner named on Wikipedia or on the company's own site. |
| R3-06 | `companies.csv` lines 36 (B-C-031 Dashlane, route stop 1), 97 (B-C-098 BrainPOP, stop 4), 93 (B-C-101 TripleLift, stop 6) and 144 (B-C-151 Carbyne); Method row 40 | Four `high` rows rest on the company's own page plus its Built In profile, with no third-party dated source. Built In profiles can be claimed and edited by the employer, so they are not clearly "independent". The rows meet the floor only if Built In counts as an independent publisher. The route pool needs `high`, so three route stops depend on this reading. | Every Built In page I opened (Hex, Daily Harvest) carries "Is This Your Company? Manage", which is the employer-claim link. The rows' notes cite no lease press. Contrast CompStak, Empathy and Signal AI, which have a CO article in the notes. | Either state in Method row 40 that Built In counts as an independent publisher even though employers can edit it, and say why. Or require a third-party source (press, a landlord release, a filing) for `high`, lower these four rows to `medium`, and re-run the route search. Its high-or-medium variant already exists: 195 min with the reload. |
| R3-07 | `companies.csv` lines 93 (B-C-101) and 34 (B-C-039) notes; `coworking.csv` line 26 (B-W-025) notes; `_build/build.py` `content_checks()` | R2-05 is not quite closed. Three inferences remain in notes that go into Clay unchanged. TripleLift (a route stop): "so the whole company may be near the top of the band", which is a size inference. Stone Source: "Likely includes a showroom". Resident Union Square: "members are likely emerging CPG founders". | My regex scan of every notes and reason field for likely, probably, may be, suggests and similar words, reading each hit. Everything else is sourced or flagged for the founder. | Reword to source-only statements. For example: "Contact page: '400+ Talented Workers' across 8+ locations (whole company)"; "Use of the space not sourced"; "Positioned for consumer-brand founders (CoworkingCafe 2025-12-12)". Add `near the top of the band`, `likely includes` and `are likely` to the banned list. |
| R3-08 | `coworking.csv` rows with `in_boundary = N` (8 sites, B-W-025 to B-W-032); `walk.csv`; `HANDOFF.md` deviation 3 | HANDOFF keeps 8 sites just outside the line because "an operator near the edge may still be one office". So they are seeds for A. Yet none is on the walk plan, so no lobby, front-desk or pantry check is planned for them. | Walk coverage: 81 of 81 buildings, 30 of 30 stores and 24 of 24 coworking sites inside are covered. The 8 outside are not covered. Four of them are `high` with `pantry_control = operator`: Resident Union Square, Indy by Industrious Gramercy, Resident Madison Park and Corporate Suites Two Park Ave. | Add the outside sites with `pantry_control = operator` to the outer sessions 8 to 10 (each is within about 2 blocks of a store already on them). Or say in HANDOFF that they are not walked and are not seeds until walked. |
| R3-09 | Method row 86 (Route pool); Method rows 52 and 118; `HANDOFF.md` line 70; `README.md` line 43; `_build/map_template.html` line 92 (Key); `companies.csv` line 91 (B-C-095) | Text that is wrong or garbled, though the data is right. 1) Method row 86 repeats itself: "at least three bands with one 76-150 office and at least three bands (...)". 2) Method rows 52 and 118 say 44 candidates carry a band; HANDOFF and README say 45. The difference is Normal Computing's `under-40`. 3) HANDOFF says the boundary has "9 vertices"; it has 8 (9 coordinates with the closing point). 4) README My Maps step 3 says "The largest file is about 50 KB with 117 placemarks". The largest file is `2-private-buildings.kml` (53.7 KB, 81 placemarks); the walk layer has 116. 5) The map Key reads "Model route stop (Tuesday, 8 to 11 am, estimate)", but the model ends at 11:27. 6) Foursquare's `hq_city` is New York (Built In), while the Revelio page the same row cites says HQ San Francisco. | Method dump (openpyxl), KML parse, the HTML template, and the row text. | 1) Write the constraint once: "at least three bands including one 76-150 office". 2) Say "45 (44 plus Normal Computing's under-40)" everywhere. 3) Write "8 vertices". 4) Write "the largest file is about 54 KB (81 placemarks); the walk layer has 116". 5) Key: "Model route stop (Tuesday from 8 am; estimate; does not fit by 11)". 6) Note the conflict in B-C-095 and keep Built In's New York, or set `hq_city` to unknown. |
| R3-10 | `companies.csv` line 2 (B-C-001 `second_source_date` "2023") and line 79 (B-C-082 `headcount_second_source_date` "2025"); `near_miss.csv` lines 29 and 90 (`headcount_source_date` "2025" and "2019"); every list column (`candidate_company_ids`, `coworking_ids`, `retailer_ids`, `tenant_company_ids` and others) | Format nits against CONTRACTS section 5. 1) Four dates are year-only, but source dates must be `YYYY-MM-DD` or `YYYY-MM`. 2) Lists use "; " (semicolon and space), so a plain split on ";" gives " B-C-007" with a leading space. A's import or join would then miss those IDs. | My regex over every `*date*` column. Splitting `buildings.csv` `candidate_company_ids` on ";" gives IDs with leading spaces on 41 buildings. | 1) Use `YYYY-MM` where the month is known; otherwise move the year into notes and leave the date blank with "date not stated" in notes. 2) Join lists with ";" and no space, or say in HANDOFF that A must trim. |

---

## Spot check: ten company rows (none checked before)

Seed 20261024303, from the 114 candidates outside:
- the slices' 21 checks;
- the builder's 10;
- round 1's 10 and its 8 re-confirmations;
- round 2's 10.

Every source was opened on 2026-10-24.

| # | Row | Source opened | Company and address | Source date | Band and scope | Confidence rule | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B-C-061 Daily Harvest, 37 W 20th St | Built In offices page and profile | "HQ New York 37 West 20th Street": matches | 2026-10-23, the date the undated page was opened, as Method defines it | 251-500 whole-company = "267 Total Employees": correct. Revelio slug `daily-harvest` returns 404, so `single-source` is fair | low: only an undated profile. Correct | PASS. `occupied` rests on that profile alone (R3-04) |
| 2 | B-C-042 VidMob, 130 Fifth Ave | CO 2024-12-02; Revelio | "leases — including ... data company VidMob — 130 Fifth Avenue is now 100 percent leased": matches | 2024-12-02: matches | unknown, because Built In 67 and Revelio "approximately 90 ... as of March 2026" disagree: correct | low: Built In gives another address (500 7th Ave), a conflict, so stricter than the floor. Correct | PASS |
| 3 | B-C-055 Stash, 641 Sixth Ave, floor 6 | CO 2026-09-02 | "12,322-square-foot office lease ... part of the building's sixth floor ... signed in mid-August": matches | matches | unknown: Built In 380 against Revelio 174. Correct | medium: one fresh source. Correct. `signed-not-occupied`: correct | PASS |
| 4 | B-C-074 General Assembly, 915 Broadway, floors 2-4 | CO 2021-04-15; Metro Manhattan page (`dateModified` 2025-10-29) | "10-year renewal for its 40,158-square-foot space on the second through fourth floors"; broker page: "Among those occupying ... are General Assembly": matches | matches | unknown, no count: correct | low: old press plus a broker list. Stricter than the floor, allowed | PASS. Parent Adecco not recorded (R3-05) |
| 5 | B-C-113 Clarick Gueron Reisbaum, 41 Madison Ave, floor 23 | CO 2024-06-24 | "11-year lease for the space on the 23rd floor", 13,394 sf, moving from 220 Fifth: matches | 2024-06-24: matches | unknown: correct | low: 4 months past 24. Correct | PASS |
| 6 | B-C-046 Radar, 111 Fifth Ave | CO 2026-04-07 | "a 13-story office building with corporate tenants including geolocation platform Radar Labs": matches | matches | unknown: Built In 64 against Revelio 99. Correct | medium: correct | PASS |
| 7 | B-C-125 OTTO Brand Lab, 25 W 26th St, floor 7 | Own contact page; CO 2022-10-02 | "Main Location 25 W 26th St, 7th Fl."; CO: "a 5,000-square-foot lease": matches | live page; CO 2022-10-02: matches | unknown, no count: correct | high: a fresh own page plus an independent, older publisher. Meets the floor as written | PASS |
| 8 | B-C-150 The Corcoran Group, 381 PAS | CO 2026-04-01 | "11-year, 14,710-square-foot lease ... a full floor ... will occupy the new space sometime in the summer": matches | matches | unknown: correct | medium: correct. `occupancy-unconfirmed` is right now that the summer has passed | PASS on the address. Parent Compass not recorded, and the note guesses at size (R3-05) |
| 9 | B-C-008 Union Square Hospitality Group, 853 Broadway, floor 17 | Own contact page; CO 2018-02-16 | "853 Broadway, 17th Floor, New York, NY 10003"; CO: "the entire 17th and 18th floors": matches | live page; file says 2018-02, article 2018-02-16 | unknown, with the reason stated (restaurant staff would distort any company count): correct | high: meets the floor as written | PASS |
| 10 | B-C-056 Hex Technologies, 250 PAS, floor 7 | CO 2026-01-09; NYREJ 2026-03-10; Built In; Revelio | CO: "five-year lease for 12,000 square feet on the entire seventh floor"; NYREJ repeats the landlord release: matches | matches | 151-250 whole-company: Built In "HQ San Francisco Total Offices: 2 160 Total Employees" and Revelio "approximately 232 ... as of March 2026" agree. `hq_in_nyc = N`: correct | medium: two outlets, one release. Correct | PASS |

**10 of 10 pass.** Every company is placed at its address by the cited source, and every date, band, scope and rating holds as labelled.

## Spot check: ten pins (none checked before)

Seed 20261024303: 7 from the 47 buildings that no earlier check covered, and 3 public-map stores.

How I checked:
- `_shared/geocode.py` re-run sequentially (`evidence-r3/geocode_pins.jsonl`).
- "addr" is the distance from the pin to the addressed street's CSCL centreline.
- "other" is the distance to the nearest other street.
- "Lot" is the pin against its own MapPLUTO polygon.
- OSM sheet: `evidence-r3/pins-r3-lots.png`.

| # | Pin | bbl and label against the geocoder | CSCL side and block | addr / other | Lot | OSM z19 | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B-B-035 149 Fifth Ave | 1008500001, "149 FIFTH AVENUE": match. Pin moved by design (two moves noted in `pin_check`) | east side, 21st–22nd St (range 149–167): OK | 16.8 m / E 21 St 26.6 m | inside, at the lot's north edge | East side of Fifth, north of 21st St; touches 155 Fifth (Scribner) | PASS |
| 2 | B-B-029 156 Fifth Ave | 1008220031: match. Moved by design | west side, 20th–21st (154–160): OK | 16.8 / W 20 St 26.0 | inside | Fifth Ave frontage near "156" | PASS |
| 3 | B-B-033 30 W 21st St | 1008220058: match. lat/lon identical | south side (2–98): OK | 22.4 / W 20 St 52.3 | inside | On the "30" lot | PASS |
| 4 | B-B-044 300 PAS (route stop 8) | 1008510035: match. Moved by design | west side, 22nd–23rd (286–306): OK | 13.1 / E 22 St 26.6 | inside | At "300", on the PAS side | PASS |
| 5 | B-B-068 381 PAS | 1008820085: match. Moved by design | east side, 26th–27th (363–385): OK | 13.2 / E 27 St 26.6 | 0.7 m outside, on its frontage | PAS sidewalk at Sarabeth's (381) | PASS |
| 6 | B-B-030 37 W 20th St | 1008220009: match. Identical | north side (1–99): OK | 21.4 / W 21 St 53.4 | inside, centre | On the lot | PASS |
| 7 | B-B-005 19 Union Square W | 1008430020: match. Moved by design | west side, 15th–16th (17–29): OK | 11.6 / E 15 St 26.8 | 3.1 m outside, at the north end of its frontage | Union Sq W frontage, at the line with Carlyle Court (25 USW) | PASS on block face (see R3-03) |
| 8 | B-R-013 Westside Market, 84 Third Ave | 1005567502: match. Identical | west side (66–86): OK | 25.1 / E 12 St 27.1 (corner) | inside | "Westside Market" label on the lot | PASS |
| 9 | B-R-025 LifeThyme, 410 Sixth Ave | 1005720005: match. Identical | east side (400–418): OK | 26.9 / W 9 St 37.0 | inside | On the narrow lot at "410" | PASS |
| 10 | B-R-017 Westside Market, 170 W 23rd St | 1007987502: match. Moved at round 1 | north side (100–198): OK | 25.4 / Seventh Ave 43.3 | inside | Westside Market lot, W 23rd frontage | PASS |

**10 of 10 pass. Total 20 of 20: the brief's spot check passes.** The wider all-pin lot test found the side effect in R3-03, which does not touch any sampled pin's block face or any route stop.

---

## Verification of the round-2 fixes

| R2 | Builder says | What I found |
| --- | --- | --- |
| R2-01 REPORT.md | Deferred (blocked); interim fix | **Still missing (R3-01).** The interim text is accurate: README line 5 and the Method changelog row say "drafted ... not saved". |
| R2-02 four over-500 bands | Moved to Near-miss | Fixed. B-C-020, 084, 102 and 158 are in `near_miss.csv` with Revelio counts 1279, 774, 1130 and 964 and the right classes. The six extra moves (Clay, Sierra, Seedtag, Valon, GameChanger, Nourish) are there too. |
| R2-03 second counts | 54 second counts | Fixed. The columns exist, and `headcount_check` is consistent. I re-opened Revelio for VidMob (90), Dashlane (319) and Hex (232): all match the file. |
| R2-04 medium floor | Undated profile alone gives low | Fixed. My floor script finds 0 violations on all four files. |
| R2-05 size guesses | 10 notes plus 6 more rewritten | Mostly fixed. Three stragglers remain (R3-07). |
| R2-06 route load | Reload modelled, plain answer | Fixed. Route B33 shows 207, finish 11:27, "over by 27 min". The answer and default are on the tab, in README, in Method and on the route sheet. |
| R2-07 HQ and parent | Filled; `parent_company` added | Done for HQ. The parent column has gaps (R3-05). |
| R2-08 Method definitions | All defined | Fixed. Every column on every tab has a definition, including the Walk summary. Small text slips remain (R3-09). |
| R2-09 crossings | Own-avenue crossing counted | Fixed for the case raised. My leg 2→3 counts 2 street crossings where the file has 3, which is 15 s and immaterial. |
| R2-10 corner pins | Moved to the avenue frontage | Fixed for readability, but it introduced R3-03 (pins past the lot frontage). |
| R2-11 passed moves | BrightTower and Corcoran unconfirmed | Fixed. Both are `occupancy-unconfirmed`. `move_in_date` is `YYYY-MM`, `unknown` or blank. |
| R2-12 TJ, Kalustyan's, Wegmans | Fixed | Fixed. The TJ note is reworded, Kalustyan's is `medium`, and Wegmans is tier B with a hollow marker as #5. |
| R2-13 D grades, venv, scale bar | Fixed | Grades note and venv step: fixed. Street labels: fixed. **Store labels still collide**, and D's request is unanswered (R3-02). |

## Route legs, recomputed

| Leg | My CSCL path | Metres | Crossings | My estimate (64 m/min, 25 s per avenue, 15 s per street) | File | Car faster? |
| --- | --- | --- | --- | --- | --- | --- |
| 7→8, 50 W 23rd St (Foursquare) to 300 PAS (1stDibs) | East on 23rd St across Fifth and Broadway at the Flatiron, on the south side past Madison's end, then south on the west side of PAS | 555 | 2 avenues, 0 streets | 8.7 + 0.8 = **9.5 min** | 541 m, 2 + 0, 9.3 min | No. Car: 8 min overhead + 555 × 1.3 / 260 m/min = 10.8 min, against the file's 10.7 |
| 8→9, 300 PAS to 215 PAS (Cognitiv) | South on PAS from 22nd St to 18th St, crossing PAS once | 367 | 1 avenue, 5 streets | 5.7 + 0.4 + 1.25 = **7.4 min** | 379 m, 1 + 5, 7.6 min | No |
| (extra) 2→3, 625 Sixth Ave (GTS) to 56 W 22nd St (Empathy) | North on Sixth, cross Sixth at 22nd St | 315 | 1 avenue, 2 streets | 4.9 + 0.4 + 0.5 = **5.8 min** | 332 m, 1 + 3, 6.4 min | No |

The walking model holds within 0.6 min a leg. The conclusion does not depend on the legs: ten stops do not fit 8 to 11 am on one loop with drinks.

---

## The three reviewers

**Manhattan leasing broker.** I would sign the address work. All ten rows I opened sit where their sources say, the dates are honest, and old or moving tenants are marked:
- 30 are `signed-not-occupied`;
- 45 are `occupancy-unconfirmed`, including BrightTower and Corcoran after their moves passed;
- 31 are `low`.

The headcount column is now honest rather than strong:
- **What is in place:**
  - Every band was tested against a second count.
  - 22 disagreements are `unknown` with both counts shown.
  - Ten over-500 firms moved out.
  - `hq_in_nyc` flags 12 banded firms based elsewhere.
- **The real picture:** only 45 of 162 candidates carry a band, and only 21 of those are confirmed by two counts.
- **What I would still push back on:**
  - six `occupied` labels that rest on a profile B calls stale-prone (R3-04);
  - three big parents left as `unknown` (R3-05);
  - three route stops whose "independent" confirmation is the company's own Built In profile (R3-06).

None of these is a guessed tenant or an invented headcount.

**Morning courier with a hand truck.** The route answers the question honestly. Ten stops on one loop with drinks take 207 min with one 20-minute reload and finish at 11:27, 27 min over. Light snacks on one loop take 187 min. The default is two mornings of five, or a courier for the second loop.
- My three recomputed legs are within 0.6 min of the file, and no leg favours a car.
- Stops 4 to 7 sit on one block of W 23rd St, which is a good, compact core.
- Security desks come last.
- No lobby is a sourced walk-up, so the 08:00 handover at Dashlane is untested, and the tab says so.
- The phone map at 390 px works: popups scroll under a fixed heading, numbers fan out, and Find works.
- The only map slip is the Key's "8 to 11 am" (R3-09).

**Brand founder.** The public map is useful, not clutter:
- 14 numbered stores, each with its walking minutes;
- filled markers for the four tier A grocers (three Whole Foods, whose chain-level 2026 LEAP release I opened, and LifeThyme) and hollow markers for specialty stores;
- an honest footnote;
- no office or business names.

Five stores have no candidate within five blocks. That is Q2, with the default to keep them. The weak point is the per-brand proposal map. For a brand whose stores are the Third Ave Westside Markets and Eden Gramercy, the labels overprint and the pins sit on the frame edge (R3-02). D asked for a fix and has had no answer.

---

## Checklist

| Check | Result |
| --- | --- |
| Public map files hold only the boundary and retailers, with no company names | PASS. The GeoJSON has 1 polygon and 14 points. The KML, SVG and brand map hold no company, coworking or operator names, no B-C, B-B or B-W IDs, and no business name |
| Confidence ratings follow the floor | PASS, with 0 violations on companies, near-miss and coworking. All 22 high stores have an NYS licence as the independent source. The independence of Built In is questioned in R3-06 |
| No guessed tenants | PASS on the 10 rows I opened |
| No invented headcounts, no Tuesday estimates | PASS. Every band rests on a sourced count, there are no onsite fields, and Normal Computing's NYC figure is sourced. Three inferential notes remain (R3-07) |
| Coworking tenants excluded from Companies | PASS. 5 rows are `excluded-coworking`. All 31 candidates that share a tax lot with a coworking site are `different-floor` or `direct-lease-documented` |
| Columns match CONTRACTS 6.1; A can import unchanged | PASS. Contract columns come first and in order, enumerations are valid, there are no blank lat or lon values, and the workbook tabs equal the CSVs. The list separator and four year-only dates are nits (R3-10) |
| KML and HTML open; HTML usable at 390 px | PASS. 8 KML files parse and their styles resolve. The HTML has no errors and no horizontal scroll; popups, Find, Key and walk sessions work. I looked at the screenshots |
| Walk plan covers every building and retailer | PASS: 81 of 81 buildings, 30 of 30 stores, 24 of 24 coworking sites inside. 10 sessions of 72 to 83 min, 782 min in all. The 8 outside coworking sites are not walked (R3-08) |
| Must include and Deliverables | All present, with one exception: the report-back file, which has the cross-tab missing (R3-01). There are 162 sourced candidates against the brief's 100 |
| Non-negotiables | Prepare-never-execute holds: GET-only scripts, nothing published, no connector writes. The private and public maps are separate. Free tools only. No personal data. The earlier SEC breach is disclosed in the README and Method |
| CONTRACTS conformity | Folder, enumerations, Y/N fields and the SAMPLE banner are fine. Ladder words are clean ("conversion" appears only as condo conversion). Rename-ability holds: `Method!B3`, `BRAND_NAME` in the HTML, and the route sheet's variable. The calendar does not apply. `REPORT.md` is missing (R3-01) |
| Wave 1 handoffs | D: tokens and fonts are used and the brand map is built, but D's open label request is unanswered (R3-02). G: the name-check log and `12-coi-request-own-carrier-building.md` exist and are cited. H: none is needed, and H's founder drop-day rate (1 h per office) is consistent with B's split-morning default |
| Prices and terms match plan.md | No prices appear. The 15-minute stop, the 8 to 11 window, Tuesday/Wednesday drops and 50 units per office all match the plan |
| README lets a stranger use it | Yes: order of use, the phone test, My Maps steps and brand-map steps with setup. It points to a REPORT that is not there (R3-01) |
| Would an expert sign it as it stands? | The research, pins, maps, route model and walk: yes, after R3-02. The folder as a deliverable: not until R3-01 is closed |

---

## Builder response

Builder, 2026-10-24 (container clock about 05:35 to 06:40 UTC). Working log: `_work/REVIEW3_PROGRESS.md`. Pre-fix outputs were backed up outside the folder before any change.

**Re-run after the fixes.**
- Full pipeline (`_build/run_all.sh`): content checks pass, and the render reports no page or console errors.
- Pins: `pin_qa.py` checks 419 pins, finds 0 issues, block-face-tests 415, and finds all 419 inside their own MapPLUTO lot.
- The reviewer's own `floor.py` and `lots.py`, re-run unchanged in a scratch copy: 0 floor violations on companies, near-miss and coworking, and 143 of 143 pins inside their own lot.
- My own check script finds none of these:
  - a high row whose only confirmation of an own page is Built In, Deskpass or LiquidSpace;
  - an `occupied` row without a dated source under 24 months or an own page.
  It also finds contract columns in order, enumerations valid, no blank coordinates, no year-only dates, and no `"; "` in any ID list. Every workbook tab equals its CSV.
- LibreOffice recalculation: 0 formula errors. Route reads 213 min, finish 11:33, "over by 33 min". The Walk total reads 820, and the Method cross-tab matches the CSVs.
- Phone test at 390 x 844 in Playwright: `scrollWidth` is 390 and there are no errors. The Key reads "does not fit by 11", the 860 Broadway popup works, and the walk session list shows 11 sessions.
- I looked at every re-rendered PNG: `public-map.png`, `route-private.png`, `brand-maps/SAMPLE-brightside.png`, the four maps in `_build/out/qa/brand-map/`, and the phone screenshots.
- The public files still hold no company, coworking or operator name, no B-C, B-B or B-W ID and no business name. The only change C sees is Whole Foods Union Square's point, which moved about 21 m (R3-03).

| ID | Response | How |
| --- | --- | --- |
| R3-01 | **Fixed as far as a subagent can; the save is still blocked** | The harness refused my Write of `REPORT.md` a third time: "Subagents should return findings as text, not write report files." I did not work around that refusal with another tool. **What I did:** `_build/report_text.py` prints the complete report-back. It is built from `stats.json` and `method_text.py`, so it cannot disagree with the workbook. It holds: what was built and the boundary; counts by tab (Companies 168, Buildings 81, Coworking 32, Retailers 30, Route 10, Walk 124, Near-miss 108); **companies by confidence and band**; the route at 213 min with one reload (11:33), 193 on one loop; the walk (11 sessions, 124 stops, 820 min, with a session table); assumptions A1 to A17 and the gaps shipped; changelog rounds 1 to 6; "Rule breaches", with the full SEC account; and Q1 to Q6 last, each with a default. **To save it** (orchestrator, or the founder), from `cluster-1-flatiron/`: `python3 _build/report_text.py > REPORT.md`. The same text is in my final response. **Interim fix done:** the cross-tab is on the Method tab ("Candidates by headcount band and confidence") and in `stats.json` (`conf_band_table`). README, HANDOFF and Method no longer say "drafted, not saved"; they give the command. The numbers differ from the reviewer's list where round 3 changed them: Walk is 124 rows (8 outside coworking sites added) and high is 49 (R3-06). |
| R3-02 | **Fixed** | **The option:** `public_map.py --labels numbers\|names` (default `names`). `numbers` draws the numbered pins only. **Names mode** places each name by a collision pass, in this order: right, left, the four diagonals, above, below, then a leader line at growing radius. Label widths are measured from D's font with fontTools. A name is rejected if it overlaps a pin, another name, the north arrow, the scale bar, the SAMPLE banner or the frame, or if it sits nearer another pin than its own (the last rule catches the old "label 4 over pin 3" case). Street and avenue names give way to store names. Next-door pins fan out with a line back to the true spot. **The frame:** the extent is solved so every pin is at least 40 px inside it (`min_pin_edge_to_frame_px`, at least 40 on every QA map). The north arrow and scale bar move to the other corner if a pin sits under them. **New flag:** `--out-dir` for QA runs. **Checked by looking:** D's four-store long-name set (B-R-018, 020, 013, 016) with names and with numbers only, a six-store set, and SAMPLE-brightside both ways, all in `_build/out/qa/brand-map/` (made by `run_all.sh`, placements logged in `brand_map_qa.txt`). D's set now reads: 1 right, 3 left, 2 and 4 by leader lines, nothing on the frame edge. **D's request is answered in words** in HANDOFF, "B feeds D": the option, its default, and that pin order follows `--stores`. The README steps now show the option. |
| R3-03 | **Fixed** | **The lot data:** `frontage.lots()` fetches MapPLUTO 26v2 lot polygons (GET, from the public planninglabs.carto.com endpoint ZoLa uses) and caches them in `_build/out/lots_cache.json`. **The rule:** `frontage.clamp_to_lot()` moves any pin outside its own lot to the lot's frontage on the addressed street, 3 m inside the lot line. On a corner lot with a frontage of 35 m or less, that is the middle of the frontage. On a longer corner frontage, it is the point nearest the old pin that stays 26 m from the cross street. Any other pin goes to the frontage point nearest it. For an address form CSCL cannot test (Union Square South), the pin goes to the nearest point 3 m inside the lot. A moved pin must still pass the block-face test. If it cannot, the pin stays and the row is flagged: that happens once, at 33 E 18th St, a no-candidate building whose recorded lot is across the street. **What moved:** 34 deliverable rows (8 buildings, 7 coworking, 3 stores, 13 companies, 3 near-miss) and 5 no-candidate buildings. Among them are 860 Broadway, 234 Fifth, 121 Lexington, 386 PAS and 19 USW. Whole Foods Union Square's published coordinate sat 17 m outside its lot, so it moved onto the lot; the row's note says so. **QA:** `pin_qa.py` now has an `own_lot` column and flags any pin more than 3 m outside. |
| R3-04 | **Fixed** | **The rule,** in `assemble.audit_confidence`: `occupied` needs a dated source under 24 months or the company's own live page. Otherwise the row becomes `occupancy-unconfirmed`, with "only an undated profile places it here ... check the lobby directory", or "no source under 24 months" where that is the reason. **What changed:** the six named candidates (Bombas, Morning Brew, Daily Harvest, Retool, Wellcom, accessiBe), plus 10 near-miss or excluded rows. Candidates are now 81 occupied, 51 unconfirmed and 30 signed. Occupied with a band is now 26 (HANDOFF and README updated). Method and `coldefs` define the rule. |
| R3-05 | **Fixed** | **The three named parents,** each Wikipedia page opened 2026-10-24 (raw wikitext and the page footer for the last-edit date): General Assembly is owned by The Adecco Group (last edited 2026-10-05), The Corcoran Group by Compass, Inc. (2026-05-27), and BrainPOP by Kirkbi A/S (2026-10-09). **Corcoran's note** is reworded as asked, and the "large brokerage" phrase is now a banned pattern. **The pass over the other 153 candidates** checked Wikipedia raw wikitext (GET, generic User-Agent) for infobox parent or owner, plus acquisition text. I vetted each hit by hand and added seven: Chan Zuckerberg Initiative (Biohub), Boat Rocker Media (Matador), Chobani (Daily Harvest), Kodansha (Kodansha USA), Infillion (Foursquare, announced 2026-09-18), Frasers Group (Everlast) and Sungjoo Group (MCM). Minority stakes are not parents (Exor holds 24% of Louboutin; Blue Owl 6% of ICONIQ), and neither is Vita Coco's former name. That gives 16 candidates with a parent. **Not done:** company sites were not searched for owners (assumption A9). |
| R3-06 | **Fixed, using the stricter option** | **The rule:** an employer-editable Built In profile is not independent of the company's own page. The same holds for an operator-written Deskpass or LiquidSpace listing and the operator's own page. A high row now needs a source the subject does not write. **Press opened 2026-10-24 kept five rows high:** Dashlane (CO 2019-04-22, 10-year lease, fourth floor), CompStak (CO 2022-12-20), Empathy (CO 2024-03-06), Signal AI (CO 2022-12-19) and Carbyne (Connect CRE 2023-08-18). Each source is now in `second_source_url`. **Lowered to medium:** TripleLift (one search found only aggregators) and BrainPOP (its only press is CO 2010-08-10, a 15-year lease whose term ended about 2025; a new assumption says an independent source counts only while its lease can still be running). The same reading lowered Seedtag (near-miss; a three-year lease from 2023). **Coworking, same rule:** eight sites went to medium. Industrious 215 PAS stays high on its CMBS rent roll (sec.gov, cited, not re-opened). **Route re-run:** with BrainPOP and TripleLift out of the high pool it takes 213 min with the reload (11:33), 193 on one loop. The high-or-medium variant is unchanged at 195 / 175. Method row 40, the confidence scale, A5, A6 and `coldefs` state the rule and why. |
| R3-07 | **Fixed** | **The three notes, reworded:** TripleLift ("'400+ Talented Workers' across 8+ locations (whole company)"), Stone Source ("Use of the space not sourced") and Resident Union Square ("designed for consumer-brand founders'. Members are not listed."). **A wider scan** of every text field for likely, probably, may be, suggests and similar words reworded 12 more inferential notes: Hungryroot, Sapien AI, Hunter Point, Vestal Point, Everlast, Augury, Corcoran, Select Office Suites, Regus 41 Madison, WeWork 245 Fifth (two), and NeueHouse's and Cure's food-contract signals. **The banned list now adds** "near the top of the band", "likely includes", "are likely", "probably not or open", "likely stale", "likely a different", "likely needs", "likely ended", "suggests a or stale" and "a large brokerage". The build fails on any of them. Lease-timing flags that lower a row ("may be leaving") stay, because they are conservative and flagged for the founder. |
| R3-08 | **Fixed** | All 8 coworking sites outside the line, the 6 operator sites and the 2 IWG rows, are now in the outer walk phase. The walk is 11 sessions of 64 to 80 min, 124 stops and 820 min. Coverage: 81 of 81 buildings, 30 of 30 stores, 24 of 24 coworking sites inside and 8 of 8 outside. HANDOFF says an outside site is a seed only after its walk-by. |
| R3-09 | **Fixed (all six)** | 1) The route rule is now one string: "at least three bands including one 76-150 office", and the Method text no longer repeats it. 2) Method, HANDOFF and README say "45 (44 in the four bands plus Normal Computing's under-40)"; `stats.py` had two definitions and now has `candidates_banded` and `candidates_banded_4`. 3) HANDOFF says "8 vertices (9 coordinates with the closing point)". 4) README says "about 54 KB (`2-private-buildings.kml`, 81 placemarks); the walk layer has 124". 5) The map Key reads "Model route stop (Tuesday from 8 am; estimate; does not fit by 11)". 6) Foursquare's HQ is `unknown`, with the Built In New York against Revelio San Francisco conflict in the notes. |
| R3-10 | **Fixed** | **Dates:** HUMAN Security's second source date is now 2023-03-23, the Built In article's `datePublished`, which I opened. The Candid Health, Palantir and Kohler dates are blank, with "date not stated" and the year in the notes. **Lists:** every list column is joined with `;` and no space. Building names inside `stops_here` have their own semicolons turned into commas, so `;` only separates items. HANDOFF says so. |

**Also fixed while re-checking (not in the review):**
1. **The route order could come out reversed.** Each lobby class was ordered exactly but alone, so a reversed path of equal internal length could end at the wrong end of its class. One run gave 225 min with a 14-minute K Health to 215 PAS leg. The exact order is now a backward pass over the classes that counts the hop into the next class. The result is deterministic (route.csv is byte-identical across runs) and takes 213 min.
2. **The walk total was computed two ways, and the grid model was not deterministic.** `stats.py` now computes session minutes the way the Walk tab does. `grid.py` picked a street or avenue name out of a Python set, so the grid fit depended on per-process string hashing and walk legs moved by 0.1 min between runs; it now sorts the names. Two full `run_all.sh` runs give byte-identical CSVs and GeoJSON, and the REPORT, README and sheet all say 820.
5. **car_faster on a same-building stop** is now blank in `route.csv`, as on the Route tab, which now equals its CSV cell for cell.
3. **Two Route totals left out the reload.** "If stops took 12 min" and "first nine stops" now include it.
4. **Q2 had a stale claim** ("8 to 11 minutes' walk"). It now names the five public stores with no candidate within five blocks; Fairway Kips Bay is the farthest, at about 8 minutes.

**Remaining open:**
- `REPORT.md` itself needs the one-command save above.
- No lobby is verified on foot.
- The phone map is untested on a real phone.
- LinkedIn URLs are blank.
- Company sites were not searched for parent owners.
