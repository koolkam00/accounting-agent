# Places slice: coworking and retailers (methods, closures and gaps)

Slice: coworking locations and emerging-brand retailers for cluster 1 (Flatiron, NoMad, Union Square).
Files written: `coworking_research.csv` (29 rows, W-01 to W-29), `retailers_research.csv` (30 rows, R-01 to R-31; R-23 removed, see below), and this note.
Research dates: 2026-10-23, running past midnight into 2026-10-24. `source_date` is the day the page was opened.
All IDs are temporary. The assembler renumbers them to B-W-### and B-R-###.

## 1. Scope used

- Provisional box: 14th St to 30th St, Sixth Ave to Park Ave South. A building that fronts an edge street or avenue (14th St, Union Square South or East, 30th St, Sixth Ave, Park Ave S) counts as inside.
- Coworking margin: two streets north and south (12th St to 32nd St) and one avenue east (up to Third Ave; Lexington runs only from 21st St north, so Irving Pl or Lexington plus the block to Third was taken as one avenue). No margin to the west, as briefed. Places just west of Sixth Ave are listed as near-misses in section 5.
- Retailer range: the box plus ten blocks in every direction, about 4th St to 40th St, Ninth Ave to First Ave.

## 2. Method

1. Operator location indexes were read first: WeWork NYC (31 locations), Industrious NYC (42), The Yard NYC, Bond Collective (JS bundle), Servcorp NYC, Quest NYC, Resident Company Club, Civic Hall, Select Office Suites, Corporate Suites, Nomadworks, Sage, Luminary, NeueHouse (CHG), and the legacy Regus pages.
2. Discovery: the Deskpass NYC index and neighbourhood pages, plus the public Deskpass listing API (`api.deskpass.com/api/spaces/<slug>`: GET only, no login). It returns active flags, last-updated dates and amenity tags.
3. The Flatiron NoMad Partnership business directory (WordPress REST API, `business_type` 5 = coworking, 18 = grocery) was used for leads only. It still lists closed brands (The Wing, Rise, Knotel, Alley, The Yard Flatiron North), so it is not evidence of operation.
4. Retailers: own store pages (Whole Foods, Trader Joe's, Eataly, Wegmans, Target, Fairway's embedded store records, LifeThyme, Eden Gourmet, Westside Market, Morton Williams, Merci Market). The independent check is the **NYS Department of Agriculture and Markets Retail Food Stores licence list** (data.ny.gov `9a8c-vfzj`, rows updated 2026-10-14). Each retailer row cites its licence-number query URL. I pulled every licence in ZIPs 10001, 10003, 10009-10012, 10014, 10016, 10018 and 10119-10123 (433 stores) and screened them by name and size.
5. Geocoding: `_shared/geocode.py`, one address at a time, sequentially. All 59 rows have lat, lon and bbl from NYC GeoSearch. Labels were spot-checked against row addresses and all 59 match. W-17 shows the alias label "16 Madison Square West", which is the same tax lot as 1115 Broadway.
6. `blocks_outside` (retailers): a local grid helper rotates coordinates 29 degrees onto the Manhattan grid. It fits street numbers from 10 geocoded cross-street addresses (residuals within plus or minus 0.6 of a street; about 77 m per street). It places the Sixth Ave and Park Ave S lines at the mean of geocoded buildings on each avenue. blocks_outside = streets beyond the 14th or 30th St edge, plus crosstown metres beyond the Sixth Ave or Park Ave S line divided by 80 m. One street block is about 80 m, so an avenue block of about 240 m counts as about 3. The two are summed as walking distance and rounded.
   - Hand override: Wegmans (R-06) was set to 6 because its tax-lot centroid sits toward Lafayette St while its Broadway frontage lies inside the box's east-west span.
   - Edge-fronting stores (R-07 Target at Union Square East, R-22 Trader Joe's and R-26 Sunac on Sixth Ave) were set inside = Y and 0, because a deep lot pulls the centroid off the edge line.
   - Greenwich Village streets drift off the grid, so readings south of 8th St are rough.
7. Confidence follows CONTRACTS section 4 and applies to the **location existing and operating at that address**, not to the pantry or shelf fields:
   - high: a source under 24 months old plus one independent confirmation. Examples: operator page plus Deskpass, a press report or a NYS licence.
   - medium: one current source.
   - low: older or conflicting evidence, or a legacy page alone.
8. `pantry_control` takes `operator`, `tenant` or `unknown`. `operator` means the operator's own page or listing says it supplies coffee, drinks or snacks in shared kitchens. Industrious amenity text is brand-standard copy served on each location page, not per-location text. Deskpass tags ("Snacks Available", "Complimentary Coffee & Tea") are the operator's listing on Deskpass. No location showed a `tenant`-run pantry.
9. `exclusive_food_contract_signal`: no exclusive food contract was found anywhere. Named suppliers and in-house F&B are recorded as signals:
   - The Yard: Infinity coffee and Harney & Sons tea.
   - Select Office Suites: Proof Coffee Roasters, a Copake Wine Works wine bar and an on-site cafe.
   - Corporate Suites: Starbucks coffee.
   - Resident: Factor meals for purchase.
   - NeueHouse (CHG): an in-house full-service restaurant and bar.
10. Retailer buy-path tier, written at the start of each retailer `notes` cell so the public map can filter on it:
   - Tier A (5): a documented natural, local or emerging set (the Whole Foods stores, Wegmans, LifeThyme).
   - Tier B (17): specialty, gourmet or natural format, with the emerging set not yet verified.
   - Tier C (8): mass, conventional or private label (Target, Trader Joe's, Morton Williams). These are landmarks or weak buy paths.

## 3. Counts

- Coworking: 29 locations. By operator: WeWork 5, Industrious 7, Regus/Spaces (IWG) 4, The Malin 2, Resident 2, and one each for The Yard, Convene/NeueHouse, Select Office Suites, Le Parc, Luminary, Sage, Nomadworks, Corporate Suites and Civic Hall.
  - Confidence: high 19, medium 6, low 4 (the four IWG rows).
  - pantry_control: operator 24, unknown 5.
- Retailers: 30.
  - Inside the box: 10. Outside: 20, at 1 to 9 blocks.
  - Confidence: high 23, medium 5, low 2.
  - Tiers: A 5, B 17, C 8.

## 4. Closures and status conflicts found

Coworking:
- **Rise New York** (Flatiron, 43 W 23rd St per listings): a Goldmine Substack post of 2025-01-29, citing Banking Dive, says Rise NYC would close its office by mid-2025. Not listed.
- **Bond Collective Flatiron** (115 E 23rd St per search-snippet listings): not on Bond's current location list in its site bundle (opened 2026-10-23). The building now houses Resident Company Club (W-19).
- **The Yard: Flatiron North** (246 Fifth Ave): not on The Yard's current NYC list. Flatiron South (W-13) remains.
- **The Wing Flatiron**: all Wing spaces closed in 2022. This comes from search results only (Time Out, and a Flatiron NoMad roundup of Sept 2022); no successor was found.
- **WeWork**: the 2023 Chapter 11 lease rejections (ABC7, 2023-11-07, opened) include these in or near the margin: 1 Union Square West, 38 W 21st St, 419 Park Ave S, 7 W 18th St, 6 E 32nd St, 130 Madison Ave and 57 E 11th St. None is on WeWork's current NYC index. The WeWork 27 E 28th St page redirects to a generic listing.
- **Knotel**: the Flatiron NoMad directory still carries 10 or more Knotel entries. No current Knotel location was found (Newmark acquired it in 2021, per search snippets).
- **Spaces, 287 Park Ave S**: IWG signed a 2018 lease. Current status unverified; Le Parc (W-18) operates there now.
- **MicroOffice** (36 W 20th St and 902 Broadway): its site copyright is 2003-2009, so status is unknown and it is not listed.
- **Kettlespace, Work Better, Coalition Space (Flatiron), Croissant**: directory names only. Croissant is a pass network, not a location. Not listed.

Retail:
- **Pop Up Grocer**, 205 Bleecker St: NYS licence 756761 still exists, but popupgrocer.com shows Shopify's "This store is currently unavailable" (2026-10-23). It is also about 12 blocks out, so it is excluded. Founder to confirm.
- **Integral Yoga Natural Foods**: its former domain integralyoganaturalfoods.com now redirects to an unrelated gambling page, and the institute's site is bot-gated. No licence was found in the screened list. Status unknown; excluded.
- **Agata & Valentina**: its site lists only Upper East Side stores (1505 and 1513 First Ave). No store in range.
- **Garden of Eden / Eden Gourmet**: the old domain no longer resolves. Eden Gourmet's site lists Union Square (7 E 14th St) and Gramercy Park (275 Third Ave) only. **Conflict:** Gramercy is licensed but 7 E 14th St has no Eden licence. R-14 is kept at low; walk it before use.
- **Elm Health / Elm Wellness**, 56 Seventh Ave: licensed, but the old website is parked. R-28 is low.
- **Westerly Natural Market**: its only store is 911 Eighth Ave at 54th St, out of range.
- **Brooklyn Fare**: licensed at 431 W 37th St and 666 Greenwich St, both outside the ten-block range.
- **Whole Foods Stuytown** (409 E 14th St, a small-format store, licence 766270): open per its store page, but about 11 blocks east, just outside the range. It is the nearest near-miss.
- **Whole Foods Bryant Park** (1095 Sixth Ave) and **Manhattan West** (368 Tenth Ave): open, outside the range.
- R-23, **Trader Joe's Murray Hill** (200 E 32nd St; licence 725759; on the Trader Joe's locations page; 6 blocks out), was dropped to keep the list at 30 and because Trader Joe's is a weak buy path.

## 5. Near-misses (coworking just outside the margin; operating per the source named)

| Location | Address | Why out | Source |
| --- | --- | --- | --- |
| WeWork 154 W 14th St | 154 W 14th St | west of Sixth | wework.com NYC index |
| Industrious Flatiron | 119 W 24th St, 4th fl | west of Sixth | industriousoffice.com NYC index |
| Industrious University Place | 41 E 11th St, 11th fl | 11th St, 3 streets south | industriousoffice.com NYC index |
| Hakibbutz | 151 W 26th St, 6th fl | west of Sixth | Deskpass NYC index |
| Jay Suites Chelsea | 159 W 25th St, 4th fl | west of Sixth | Deskpass NYC index |
| The Malin Chelsea | 270 Seventh Ave | west of Sixth | Deskpass NYC index |
| The Yard Herald Square | 106 W 32nd St, 2nd fl | west of Sixth | theyard.com NYC page |
| Resident Chelsea (launching soon) | 115 W 18th St | west of Sixth; not open | residentcompanyclub.com |

Excluded as not office coworking:
- Blender Workspace, 135 Madison Ave, 8th fl: a meeting and event venue.
- The Farm NoMad Rooftop, 1178 Broadway: an event venue.
- Kew Management, St James Building, 1133 Broadway: landlord suites.
- CORE, 149 Fifth Ave, Suite 1102: a real-estate brokerage renting desks.
- Regus 475 Park Ave S: a search snippet said "Opening May 3, 2027"; not opened.

Retail leads screened out:
- Delis, pharmacies and conventional chains: Gristedes (25 University Pl; 221-229 Eighth Ave), D'Agostino (341 Third Ave; 355 First Ave), Lidl (460 Third Ave, mostly private label), H Mart (38 W 32nd St), Lincoln Market (501 Sixth Ave), Merci Market Chelsea (168 Seventh Ave), Chelsea Market Baskets and Buonitalia (75 Ninth Ave), and Gourmet Square Organic Market (248 Ninth Ave, about 10 blocks).
- All are licensed. They can be added if a brand turns up on their shelves.

## 6. Gaps (founder or a later pass)

1. **Store-level brand evidence is missing.** No retailer row carries a `store_selector` or `brand_claim` proof for a named emerging brand. Store catalogues are JS apps that need a session (LifeThyme's LocalExpress API returned 401), and I did not work around that. Brand-to-store links belong in workstream A, through brand locators and later the founder's shelf photos.
2. **Pharmacies:** none listed. Many CVS and Duane Reade stores are licensed in range (for example 215 Park Ave S, 300 Park Ave S, 401 Park Ave S, 750 Sixth Ave, 1 Union Sq S), but I found no evidence of an emerging set. Target Union Square and Chelsea each contain a CVS.
3. **IWG (Regus/Spaces/HQ):** regus.com, spacesworks.com and hq.com are bot-blocked (Incapsula, 403). The four rows rest on legacy Regus pages, one of which cites a long-closed restaurant, so they are low. Call or walk before use.
4. **Convene:** convene.com returned 403. The only Convene-run site found in the margin is NeueHouse Madison Square (acquired by CHG in 2026). No other Convene workplace in the margin was confirmed.
5. **The Malin:** themalin.co would not connect through the proxy. Its amenity data comes from Deskpass.
6. **Citarella, Union Market, Gristedes and Foods of India** sites were blocked or JS-only. Citarella (R-25) rests on its licence alone. Union Market was not found among licences in the screened ZIPs.
7. **Exclusive food contracts:** none surfaced in any public source. Ask each operator directly; a pantry vendor contract (for example with a snack-delivery service) would not appear on amenity pages.
8. **Pantry decision-maker:** none recorded, by design (no named people).
9. **Web search budget:** the shared WebSearch limit ran out partway through the coworking pass. After that I used direct operator pages, the Deskpass API, the Flatiron NoMad directory and the NYS licence list. No search engine was queried by other means. Some smaller operators that only search would surface may be missing.

## 7. Notes for the assembler

- Coworking rows map to `coworking.csv` in CONTRACTS 6.1. Drop `bbl`, `exclusive_food_contract_signal` and `found_date` if the strict schema is wanted, or keep them, since added columns are allowed.
- Retailer `inside_box` maps to `inside_boundary`. It must be recomputed once the final boundary is drawn; `blocks_outside` is measured from the provisional box.
- Buildings shared with company slices: 860 Broadway, 215 Park Ave S, 386 Park Ave S, 245 Fifth Ave, 200 Fifth Ave and 902 Broadway already appear in `buildings_S*.csv`. Join on `bbl`.
- Resident Union Square (W-20) is a club "designed for consumer-brand founders". Workstream A or E may want it as a brand-side lead source as well as a possible office.
