# Cluster 1: Flatiron, NoMad and Union Square

Workstream B, "Cluster map and seed lists". Desk research baseline as of 2026-10-24, revised after independent review round 1 (`_review/round-1.md`). Nothing here has been checked on foot yet, and no company has been contacted. The counts, assumptions and open questions are in `REPORT.md`.

> **The private map is never published, not even as an unlisted or "anyone with the link" page.** That covers `map-private.html`, `map-private.geojson`, `map-private.kml`, everything in `kml/`, `route-private.png`, the workbook and the CSVs: they name companies. Only `public-map.svg`, `public-map.png`, `map-public.geojson`, `map-public.kml` and the per-brand maps in `brand-maps/` may leave this folder, and only after the name check in `desk-drop-legal-pack/name-check-log.md` clears.

## The boundary in one paragraph

The boundary runs from 14th St to 30th St and from Sixth Ave to Park Ave S. Both frontages of each edge street and avenue are inside. It also takes in the Union Square frame: University Place to Third Ave, between 13th and 15th St. That holds Whole Foods Union Square, 841-853 Broadway, Zero Irving, Trader Joe's 14th St and the Target block. The area is about 1 km², 1.4 km north to south and 0.74 km across. It holds 270 of the 276 sourced company rows and 11 of the 30 stores. It follows the Wikipedia definitions of the Flatiron District and NoMad. The reasoning, and what was left out and why, are on the Method tab.

## Files, in the order you use them

| # | File | What it is for | How to use or edit it |
| --- | --- | --- | --- |
| 1 | `REPORT.md` | The report back: what was built, counts, route and walk times, numbered assumptions, the changelog, a rule breach you need to know about, and the questions for you with a default for each. | Read it first. |
| 2 | `map-private.html` | The phone map: boundary, every building (coloured by lobby type, sized by candidate count), coworking sites (purple squares), stores (diamonds; tier C hollow), the model route and the walk sessions. Tap a building for its candidate offices, floors, bands, HQ city when it is not New York, confidence, lease status and source links; the list scrolls under a fixed heading, and non-candidates fold under "N more here". **Find** searches by name or address. **Key** explains the symbols. The ◎ button shows where you are. Numbers that would overlap fan out with a thin line to the true spot. | Do the one-minute phone test below first. Then put the file in private cloud storage or send it to yourself, and open it in the phone's browser. Never host it on a public site. It loads Leaflet from cdnjs and OpenStreetMap tiles, so it needs a data connection. |
| 3 | `cluster-1-flatiron.xlsx`, tab **Walk** (also `walk.csv`) | The verification walk: 10 sessions of 79 to 83 minutes, 117 stops, about 806 minutes in all. Sessions 1 to 7 cover everything inside the boundary. Sessions 8 to 10 are the stores outside it. Each row has a verify checklist and grey columns for what you observe. | **Walk sessions 1 to 7 on Tuesday or Wednesday mornings between 8 and 11 am, two sessions a morning, so what you see in the lobby (is the security desk staffed? when are deliveries taken?) matches drop day.** Each session starts and ends near a named subway station. Fill the grey columns on foot, then set `verified_on_foot` to `Y` on the Buildings tab, which only you fill. On the map, use Find, then Walk sessions, to see one session at a time. |
| 4 | `cluster-1-flatiron.xlsx` (the other seven tabs) | Companies (178 rows: 172 candidates, 5 coworking members, 1 not an office), Buildings (82), Coworking (32), Retailers (30), Route, Near-miss (98) and Method (definitions, confidence scale, sources, boundary rationale, spot checks, changelog). | It opens in Google Sheets with formulas intact. The yellow cells on Route are editable parameters, and every time recalculates. To rename the business, edit `Method!B3` (`company_name`) once. Filter Companies on `candidate_status = candidate`. |
| 5 | `route-private.png` and tab **Route** (also `route.csv`) | A model ten-stop Tuesday route, 8 to 11 am, on foot from the first stop. All times are estimates: about 181 minutes, finishing around 11:01, **one minute over**, which is inside the model's error. With medium-confidence offices allowed, the best set found sits within three blocks (21st to 23rd St, Fifth to Sixth Ave) and takes about 172 minutes (10:52). With 12-minute stops the model route takes 151. No leg is faster by car. | It is a model: the real route comes from the signed roster. Pick founding offices that sit close together. Re-order the stops by the receiving windows you collect at intake. Walk-up lobbies go first and security desks last. |
| 6 | `kml/1-boundary.kml` … `kml/6-private-walk.kml` | The same private layers for Google My Maps (free). | See "Import into Google My Maps" below. Keep that map **private**. |
| 7 | `companies.csv`, `coworking.csv`, `retailers.csv`, `buildings.csv`, `near_miss.csv` | Seed lists for the Clay tables (workstream A), named per CONTRACTS 6.1. | Import unchanged. Columns are defined on the Method tab and in `HANDOFF.md`. |
| 8 | `public-map.svg`, `public-map.png`, `map-public.geojson`, `map-public.kml` | The public map for the website: the boundary and 14 stores only, each with its walking minutes from the cluster edge. It carries no company names and no business name, so a rename never touches it. | Workstream C uses these. The SVG carries its own subset fonts. Do not publish before the name check clears. |
| 9 | `brand-maps/` | Per-brand landscape maps (1050 x 420, about 2.5 to 1) for the retailer-map slot in D's proposal: the boundary and that brand's stores only, numbered in the order you give, with no office pins and no business name. `SAMPLE-brightside.*` is a layout test with a SAMPLE banner, not a real brand. | Make one with `python3 _build/public_map.py <python-with-fontTools> --brand <slug> --stores B-R-011,B-R-010` and then `node _build/render.js .` for the PNG (step-by-step in "Make a map for one brand" below). This never touches the public files. |
| 10 | `boundary.geojson`, `map-private.geojson`, `map-private.kml` | The standard geographic files (WGS84; the boundary ring is counter-clockwise, as RFC 7946 asks). `map-private.kml` is one combined file for Google Earth. | Use them in any GIS tool. Same never-publish rule for the private ones. |
| 11 | `_review/` | The independent review (`round-1.md`) with the builder's response at the end, and the reviewer's evidence. | Read-only record. |
| 12 | `_work/` | The raw research: four slice files, the places file, their notes, the street and park data, `builtin_hq_2026-10-24.csv` (HQ city per Built In page), spot-check images (`_work/spot_check/`), `buildings_no_candidate.csv` (buildings researched but holding no candidate) and the progress logs. | Read it for evidence. Edit the research here if you rebuild. |
| 13 | `_build/` | The code that turns `_work/` into every file above. `resolutions.py` holds every manual decision with its evidence; `frontage.py` holds the block-face pin test; `out/qa/` holds the phone screenshots, popup checks, pin contact sheets and the proposal test. | Run `_build/run_all.sh <python-with-fontTools>` (about 6 minutes; the route search is the slow part). IDs are held in `_build/id_registry.json`, so a rebuild never renumbers existing rows. The build stops if a note guesses at size or names the business. |

## One-minute phone test (do this before the walk)

Untested on a real phone so far: unverified, founder to confirm. Some phone previews (iOS Mail, the Files preview, some cloud-drive previews) show HTML without running its JavaScript.

1. Send `map-private.html` to yourself privately and open it on the phone.
2. If you see the map with coloured dots, tap **Find**, type "853", tap the building, and check the popup list scrolls. Done.
3. If you see only the black bar and no map, try "Open in" and choose Safari or Chrome. If that still fails, use Google My Maps (below) on the walk instead. Its layers hold the same buildings, stores, route and walk.

## Import into Google My Maps (free; needs your Google login)

1. **[Founder login]** Sign in to Google and open My Maps at google.com/maps/d. Click **Create a new map** and name it "Cluster 1 private".
2. In the first layer, click **Import** and upload `kml/1-boundary.kml`.
3. Click **Add layer**, then **Import**, and upload `kml/2-private-buildings.kml`. Repeat for `3-private-coworking.kml`, `4-private-retailers.kml`, `5-private-route.kml` and `6-private-walk.kml` (six layers in all). Each import becomes one layer. The largest file is about 50 KB with 117 placemarks.
4. Leave sharing as **Private** (restricted to you). Never choose "Anyone with the link" or "Public on the web".
5. On your phone, open the Google Maps app, then **Saved**, then **Maps**, to see it on the walk.
6. Optional: a second, separate My Map from `map-public.kml` is safe to share.

## Make a map for one brand

1. Find the brand's stores in `retailers.csv` (use the brand's own store locator or the retailer's store selector; never guess). Note their `retailer_id`s in the order the proposal's store table lists them.
2. If a store is missing, add it to `_work/retailers_research.csv` with a source and date, then run `_build/run_all.sh` once.
3. Run `python3 _build/public_map.py <python-with-fontTools> --brand <brand-slug> --stores <id1>,<id2>`, then `NODE_PATH="$(npm root -g)" node _build/render.js .` from this folder. The map lands in `brand-maps/<brand-slug>.png` and `.svg`.
4. In D's proposal, set the map picture to that PNG.

## Who reads what

- **Founder:** `REPORT.md`, then the map and Walk, then Companies for the discovery calls.
- **Workstream A (Clay):** the CSVs; see `HANDOFF.md`.
- **Workstream C (website):** the public map files only. The store count changed from 16 to 14, so the numbers changed: re-run C's map build.
- **Workstream D (proposal):** `brand-maps/<slug>.png` for the proposal's retailer-map slot.

## What is not done (also in REPORT.md)

- **A privacy rule was broken during research:** one research slice sent the account owner's email to sec.gov in a request header. Details are in REPORT.md under "Rule breaches". No build script calls sec.gov, and the agent will not open it again.
- No lobby is verified on foot. 65 of 82 buildings have an unknown lobby type, and every building's certificate-of-insurance rule is unknown.
- 44 of the 172 candidates are occupied and carry a sourced band. The rest need intake or a walk-by. 95 have an unknown band, and each row says why.
- Bands are whole-company unless a source counts the New York office (3 rows). 17 banded candidates are based outside New York (`hq_in_nyc = N`), so their New York office may be much smaller than the band.
- LinkedIn company URLs are blank: LinkedIn was not opened.
- No store row claims a store carries a named brand. Brand-to-store evidence belongs in the Clay brand table.
