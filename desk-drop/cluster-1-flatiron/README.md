# Cluster 1: Flatiron, NoMad and Union Square

Workstream B, "Cluster map and seed lists". Desk research baseline as of 2026-10-24. Nothing here has been checked on foot yet, and no company has been contacted.

> **The private map is never published, not even as an unlisted or "anyone with the link" page.** That covers `map-private.html`, `map-private.geojson`, `map-private.kml`, everything in `kml/`, `route-private.png`, the workbook and the CSVs: they name companies. Only `public-map.svg`, `public-map.png`, `map-public.geojson` and `map-public.kml` may go on the website, and only after the name check in `desk-drop-legal-pack/name-check-log.md` clears.

## The boundary in one paragraph

The boundary runs from 14th St to 30th St and from Sixth Ave to Park Ave S. Both frontages of each edge street and avenue are inside. It also takes in the Union Square frame: University Place to Third Ave, between 13th and 15th St. That holds Whole Foods Union Square, 841-853 Broadway, Zero Irving, Trader Joe's 14th St and the Target block. The area is about 1 km², 1.4 km north to south and 0.74 km across. It holds 270 of the 276 sourced company rows and 11 of the 30 stores. It follows the Wikipedia definitions of the Flatiron District and NoMad, and the reasoning and what was left out are on the Method tab.

## Files, in the order you use them

| # | File | What it is for | How to use or edit it |
| --- | --- | --- | --- |
| 1 | `map-private.html` | The phone map: boundary, every building (coloured by lobby type, sized by candidate count), coworking sites, stores, the model route and the walk sessions. Tap a building for its candidate offices, floors, bands, confidence, lease status and source links. **Find** searches by name or address. **Key** explains the colours. The ◎ button shows where you are. | Open the file in a phone browser: AirDrop or email it to yourself, or put it in private cloud storage and open it from there. Never host it on a public site. It loads Leaflet from cdnjs and OpenStreetMap tiles, so it needs a data connection. |
| 2 | `cluster-1-flatiron.xlsx`, tab **Walk** (also `walk.csv`) | The verification walk: 11 sessions of 67 to 85 minutes, 117 stops, about 865 minutes in all. Sessions 1 to 8 cover everything inside the boundary. Sessions 9 to 11 are the stores outside it. Each row has a verify checklist and grey columns for what you observe. | Do sessions 1 to 8 first. Each session starts and ends near a named subway station. Fill the grey columns on foot. Then set `verified_on_foot` to `Y` on the Buildings tab, which only you fill. On the map, use Find, then Walk sessions, to see one session at a time. |
| 3 | `cluster-1-flatiron.xlsx` (the other seven tabs) | Companies (178 rows: 172 candidates, 5 coworking members, 1 not an office), Buildings (82), Coworking (32), Retailers (30), Route, Near-miss (98) and Method (definitions, confidence scale, sources, boundary rationale, spot checks, changelog). | It opens in Google Sheets with formulas intact. The yellow cells on Route are editable parameters, and every time recalculates. To rename the business, edit `Method!B3` (`company_name`) once. Filter Companies on `candidate_status = candidate`. |
| 4 | `route-private.png` and tab **Route** (also `route.csv`) | A model ten-stop Tuesday route, 8 to 11 am, on foot from the first stop. All times are estimates: about 183 minutes, finishing around 11:03. That is **three minutes over**. Twelve-minute stops (153 min) or nine stops (163 min) fit. | It is a model: the real route comes from the signed roster. Re-order the stops by the receiving windows you collect at intake. Walk-up lobbies go first and security desks last. |
| 5 | `kml/1-boundary.kml` … `kml/6-private-walk.kml` | The same private layers for Google My Maps (free). | See "Import into Google My Maps" below. Keep that map **private**. |
| 6 | `companies.csv`, `coworking.csv`, `retailers.csv`, `buildings.csv`, `near_miss.csv` | Seed lists for the Clay tables (workstream A), named per CONTRACTS 6.1. | Import unchanged. Columns are defined on the Method tab and in `HANDOFF.md`. |
| 7 | `public-map.svg`, `public-map.png`, `map-public.geojson`, `map-public.kml` | The public map for the website: the boundary and 16 stores only. It carries no company names and no business name, so a rename never touches it. | Workstream C uses these. The SVG carries its own subset fonts. Do not publish before the name check clears. |
| 8 | `boundary.geojson`, `map-private.geojson`, `map-private.kml` | The standard geographic files (WGS84). `map-private.kml` is one combined file for Google Earth. | Use them in any GIS tool. Same never-publish rule for the private ones. |
| 9 | `_work/` | The raw research: four slice files, the places file, their notes, the street and park data, spot-check images (`_work/spot_check/`), `buildings_no_candidate.csv` (buildings researched but holding no candidate) and the assembly log. | Read it for evidence. Edit the research here if you rebuild. |
| 10 | `_build/` | The code that turns `_work/` into every file above. `resolutions.py` holds every manual decision with its evidence. | Run `_build/run_all.sh <python-with-fontTools>`. IDs are held in `_build/id_registry.json`, so a rebuild never renumbers existing rows. |

## Import into Google My Maps (free; needs your Google login)

1. **[Founder login]** Sign in to Google and open My Maps at google.com/maps/d. Click **Create a new map** and name it "Cluster 1 private".
2. In the first layer, click **Import** and upload `kml/1-boundary.kml`.
3. Click **Add layer**, then **Import**, and upload `kml/2-private-buildings.kml`. Repeat for `3-private-coworking.kml`, `4-private-retailers.kml`, `5-private-route.kml` and `6-private-walk.kml` (six layers in all). Each import becomes one layer. The largest file is about 50 KB with 117 placemarks.
4. Leave sharing as **Private** (restricted to you). Never choose "Anyone with the link" or "Public on the web".
5. On your phone, open the Google Maps app, then **Saved**, then **Maps**, to see it on the walk.
6. Optional: a second, separate My Map from `map-public.kml` is safe to share.

## Who reads what

- **Founder:** the map and Walk first, then Companies for the discovery calls.
- **Workstream A (Clay):** the CSVs; see `HANDOFF.md`.
- **Workstream C (website):** the public map files only.
- **Workstream D (proposal):** `public-map.svg` for the proposal's retailer-map slot. A brand-specific version can be made by filtering `retailers.csv`.

## What is not done (also in REPORT.md)

- No lobby is verified on foot. 65 of 82 buildings have an unknown lobby type, and every building's certificate-of-insurance rule is unknown.
- 95 of 172 candidates have an unknown headcount band, and each row says why. Bands are whole-company unless a source counts the NYC office.
- LinkedIn company URLs are blank: LinkedIn was not opened.
- No store row claims a store carries a named brand. Brand-to-store evidence belongs in the Clay brand table.
