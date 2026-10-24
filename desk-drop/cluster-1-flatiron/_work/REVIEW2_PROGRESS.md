# Review round 2 fixes: progress log (builder, 2026-10-24)

Working file so nothing is lost on context compaction. Not a deliverable.
Backup of pre-fix outputs: scratchpad B-r2fix/before/.

## Plan (finding -> fix)
- R2-01 REPORT.md written in the folder (try Write; if refused, Method row 112 says "drafted, not saved").
- R2-02 Mercury, Harvey, Sigma, Synthesia -> near-miss (second count > 500), nyc_office_may_fit Y where lease small.
- R2-03 headcount_second_count / _source_url / _source_date for every banded row; disagreeing bands -> unknown with reason.
- R2-04 medium needs a dated (or own-site) source under 24 months; undated profile only confirms. Rows -> low unless own page/press found.
- R2-05 ten size-guess notes rewritten; banned patterns extended.
- R2-06 route: cases_per_load, reload_minutes, total with reloads, plain statement; REPORT question.
- R2-07 hq fields from notes / own pages; parent_company column.
- R2-08 Method column definitions.
- R2-09 own-avenue crossing; route.csv from the same rounded formulas.
- R2-10 corner pins: move to addressed street or entrance_side note.
- R2-11 BrightTower, Corcoran re-check; move_in_date YYYY-MM or unknown.
- R2-12 TJ note; Kalustyan's medium; Wegmans tier B.
- R2-13 HANDOFF D grade note; README venv step; brand-map scale bar overlap.

## Status
- [!] REPORT.md Write refused again by harness (subagents return text). Not circumvented. Text goes in final response; Method row 112 + README say so; assumptions/questions also on Method tab.
- [x] Research: Revelio Labs pages for 77 banded candidates (sitemap slugs; identity by legal name + description) -> 54 second counts
      (21 agree, 21 disagree -> unknown, 11 over-500 -> near-miss; Normal Computing scope differs). Own pages: Candid 130+ (2025), Orbital 150+.
      Floor rescue for 7 medium rows: no own page / dated press places them (Retool, DH, Wellcom, Bombas 429, Ellevest, MB, accessiBe) -> low.
      Farmacy parent P&G (Happi 2021-11-15 + own page P&G terms). BrightTower, Corcoran: no confirmation -> occupancy-unconfirmed.
- [x] Code: resolutions REVIEW2 block; assemble (floor, headcount_second, hq, parent, move_in, corner pins, building notes, retailers);
      router own-avenue crossing; build (columns, near-miss count/fit, route rounding + reloads, entrance notes); stats; xlsx Route tab.
- [ ] Run pipeline; method_text + coldefs; maps popup entrance note; brand-map scale bar; README/HANDOFF; builder response.
- [x] Pipeline green (run_all 3x): content checks pass, 419 pins 0 issues, LibreOffice recalc 0 errors, route.csv == tab, phone popups OK.
      Route 207 min with 1 reload (11:27), 187 one loop; hi/med 195/175. Walk 10 sessions 116 stops 782 min.
      Candidates 162 (51/80/31); banded 45; near-miss 108; buildings 81.
- [x] Method text (headcount section, assumptions A1-13, questions Q1-6, changelog r5), coldefs complete (asserted), popups + KML entrance notes,
      brand-map label fix (tested in scratch copy), render.js relative path, README + HANDOFF, builder response appended to _review/round-2.md.
- [!] REPORT.md: text returned in the round result (harness refuses the write).
