# Assembly progress log (assembler, 2026-10-24)

Working file so nothing is lost on context compaction. Not a deliverable.

## Plan
1. Fetch NYC CSCL street centerlines (data.cityofnewyork.us inkn-q76z) for grid model + SVG basemap. -> _work/geo/
2. _build/grid.py: lat/lon -> (street index, crosstown metres) calibrated on geocoded points.
3. _build/assemble.py: merge S1-S4 companies + buildings, dedupe (bbl / normalized address / name), resolve conflicts, add missing coworking, in_coworking cross-check, boundary, in_boundary, near-miss.
4. Outputs: xlsx (8 tabs), csvs, geojson, kml, html map, public svg/png.
5. README / HANDOFF / REPORT.

## Status
- [ ] 1 streets
- [x] 1 streets fetched (_work/geo/streets_raw.geojson, 2667 segs). grid.py built: theta 29.44 deg, 79.36 m/street, mean resid 0.07 street.
- Boundary decision (draft): main body s 13.5..30.5 (both frontages of 14th & 30th), x -362..+376 (both frontages of Sixth & PAS);
  south notch s 13.0..14.5, x 182 (University Pl)..621 (Third Ave) for Union Sq South (853/841 Bway, WFM, Zero Irving, TJ 14th).
  Refs: Wikipedia NoMad (25th-29th/30th, Sixth-Madison/Lex; edited 2026-09-29), Flatiron District (14th-23rd, Sixth-PAS). Opened 2026-10-24.
- Conflicts resolved (draft): Kaltura->860 Bway (CO 2022-01 moved from 250 PAS; CO 2026-08-07 current), near-miss over-500.
  Adyen 71 Fifth current, signed 111/115 Fifth (CO 2026-04-07) move unknown; near-miss. Superhuman+Grammarly merge -> 360 PAS, near-miss.
  32BJ union + funds merge -> one row 25 W 18th. Instacart low, signed 111 W 33rd, near-miss.
- To verify by web: Cure 345 PAS, WeWork 27 E 28th, Hub Seventeen 114 Fifth, WeWork 18 W 18th floors (WW Intl fl 7),
  K Health 387 PAS vs 298 Fifth, Ziff Davis 360 PAS, Select Office Suites fl 9-12 vs Pilot Fiber fl 12, Industrious 215 PAS floors, NeueHouse 104 vs 110 E 25th.
