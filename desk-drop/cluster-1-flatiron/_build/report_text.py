#!/usr/bin/env python3
"""The report-back text (CONTRACTS section 1, the brief's "Report back"), built from stats.json and
method_text.py so its numbers, assumptions, questions and changelog match the Method tab.

Usage: python3 _build/report_text.py > <draft path>   (prints Markdown; it writes no file itself)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import method_text as M  # noqa: E402


def report(S):
    B, R, Wk = S["boundary"], S["route"], S["walk"]
    cb = S["candidates_by_conf"]
    ls = S["candidates_by_lease"]
    ck = S["candidates_by_check"]
    v = R["variants"]["high_or_medium"]
    out = []
    w = out.append
    w("# Report back: cluster 1, Flatiron, NoMad and Union Square (workstream B)")
    w("")
    w("Desk research baseline as of 2026-10-24, after three independent review rounds (`_review/round-1.md` to `round-3.md`). "
      "Nothing has been checked on foot, no company has been contacted, and nothing has been published.")
    w("")
    w("## What I built, and the boundary")
    w("")
    w(f"- A private phone map (`map-private.html`, plus KML layers for Google My Maps) of every building, coworking site, store, the model route "
      f"and the walk; a public map of the boundary and {S['retailers_public']} stores only (`public-map.svg` and `.png`, `map-public.geojson` and `.kml`); "
      "per-brand store maps for the proposal (`brand-maps/`); one workbook with the eight tabs the brief names; and the seed CSVs for the Clay tables.")
    w(f"- The boundary runs from 14th St to 30th St and from Sixth Ave to Park Ave S, with both frontages of every edge street and avenue inside, plus the "
      f"Union Square frame (University Pl to Third Ave, 13th to 15th St). It is {B['area_km2']} km2, {B['north_south_m']} m north to south and "
      f"{B['east_west_m']} m across. It follows Wikipedia's Flatiron District and NoMad, holds {S['company_rows_inside']} of the {S['company_rows_total']} "
      f"sourced company rows and {S['retailers_inside']} of the {S['retailers']} stores, and puts every candidate building within "
      f"{S['cand_bldg_to_public_store_blocks']['max']} blocks of a public-map store (median {S['cand_bldg_to_public_store_blocks']['median']}). "
      "What was left out and why (Chelsea, Gramercy and Kips Bay, north of 30th St, the Village) is on the Method tab.")
    w("")
    w("## Counts by tab")
    w("")
    w("| Tab | Rows | Notes |")
    w("| --- | --- | --- |")
    sc = S["status_counts"]
    w(f"| Companies | {S['candidates'] + sc.get('excluded-coworking', 0) + sc.get('excluded-not-office', 0)} | {S['candidates']} candidates, "
      f"{sc.get('excluded-coworking', 0)} coworking members (excluded), {sc.get('excluded-not-office', 0)} not an office |")
    w(f"| Buildings | {S['buildings']} | {S['buildings_with_candidates']} with a candidate; lobby: " + ", ".join(f"{k} {n}" for k, n in S["buildings_lobby"].items())
      + f"; certificate of insurance unknown on all {S['buildings']} |")
    w(f"| Coworking | {S['coworking']} | {S['coworking_inside']} inside, {S['coworking'] - S['coworking_inside']} just outside; pantry_control operator "
      f"{S['coworking_pantry'].get('operator', 0)}, unknown {S['coworking_pantry'].get('unknown', 0)}; confidence " + ", ".join(f"{k} {n}" for k, n in S["coworking_by_conf"].items()) + " |")
    w(f"| Retailers | {S['retailers']} | {S['retailers_inside']} inside, the rest within {S['retailers_max_blocks']} blocks; tier " + ", ".join(f"{k} {n}" for k, n in sorted(S["retailers_by_tier"].items()))
      + f"; {S['retailers_public']} on the public map |")
    w(f"| Route | {R['stops']} | model ten-stop Tuesday route, estimates |")
    w(f"| Walk | {Wk['stops']} | {Wk['sessions']} sessions |")
    w(f"| Near-miss | {S['company_rows_total'] - S['candidates'] - sc.get('excluded-coworking', 0) - sc.get('excluded-not-office', 0)} | "
      + "; ".join(f"{k} {n}" for k, n in S["near_classes"].items()) + f"; nyc_office_may_fit = Y on {S['near_nyc_may_fit']} |")
    w("| Method | | definitions of every column, the confidence scale, sources, boundary, spot checks, assumptions, questions, changelog |")
    w("")
    w(f"Candidates by confidence: high {cb.get('high', 0)}, medium {cb.get('medium', 0)}, low {cb.get('low', 0)}. By lease status: "
      + ", ".join(f"{k} {n}" for k, n in ls.items()) + ".")
    w("")
    w("## Companies by confidence and band (the 162 candidates)")
    w("")
    w("| Headcount band | high | medium | low | total |")
    w("| --- | --- | --- | --- | --- |")
    for x in S["conf_band_table"]:
        w(f"| {x['band']} | {x['high']} | {x['medium']} | {x['low']} | {x['total']} |")
    w("")
    w(f"- {S['candidates_banded']} candidates carry a band ({S['candidates_banded_4']} in the four bands plus Normal Computing's under-40, the brief's 30-to-39 "
      f"founder's call). Only {ck.get('agree', 0)} bands are confirmed by a second count; {ck.get('single-source', 0)} rest on one count. "
      f"{ck.get('disagree', 0)} candidates whose two counts disagree are unknown, with both counts shown.")
    w(f"- Bands are whole-company unless a source counts the New York office (2 rows). {S['banded_hq_not_nyc']} banded candidates are based outside New York "
      f"and {S['banded_hq_unknown']} have an unknown HQ, so their New York office may be far smaller than the band.")
    w(f"- {S['candidates_occupied_banded']} candidates are occupied and carry a band. {S['candidates_with_parent']} candidates name a parent company.")
    w("")
    w("## Route total time")
    w("")
    w(f"- Ten stops do not fit 8 to 11 am on one loop with drinks. The model route takes about {R['total_minutes']:.0f} min with one "
      f"{R['reload_minutes']:.0f}-minute reload ({R['cases_per_load']} cases a load), finishing about {R['end']}, {R['over_minutes']} min over. Its stops are "
      f"high-confidence, occupied offices with a sourced band, covering {R['rule'].split(' (')[0]}, with walk-up and unknown lobbies first and the two security desks last. "
      "No high-confidence, occupied 40-75 office with a sourced band remains, so the route has none; the high-or-medium variant below does.")
    w("- Stops: " + "; ".join(R["stop_list"]) + ".")
    w(f"- On one loop with light snacks it takes about {R['total_one_load']:.0f} min ({R['end_one_load']}), {R['over_one_load']} min over. With medium-confidence "
      f"offices allowed, the most compact set found takes about {v['total_minutes']:.0f} min with the reload ({v.get('total_one_load', 0):.0f} on one loop).")
    w(f"- Walking is {R['walking_minutes']} min over {R['metres']} m. No leg is faster by car (the longest is {R['longest_leg_min']} min). None of the ten lobbies is a "
      "sourced walk-up, so the 08:00 handover at stop 1 is untested.")
    w("- Default: split ten offices across Tuesday and Wednesday, five a morning on one load each, or hand the second loop to a courier (Q1).")
    w("")
    w("## Walk plan")
    w("")
    w(f"{Wk['sessions']} sessions of {min(t['minutes'] for t in Wk['table'])} to {max(t['minutes'] for t in Wk['table'])} min, {Wk['stops']} stops, about "
      f"{Wk['total_minutes']} min in all. Sessions 1 to {Wk['core_sessions']} ({Wk['core_minutes']} min) cover everything inside the boundary; sessions "
      f"{Wk['core_sessions'] + 1} to {Wk['sessions']} ({Wk['outer_minutes']} min) cover the stores outside it and the {S['coworking'] - S['coworking_inside']} "
      "coworking sites just outside the line. Each session starts and ends near a named subway station. Walk the core on Tuesday or Wednesday mornings, "
      "8 to 11 am, two sessions a morning, so lobby observations match drop day.")
    w("")
    w("| Session | Stops | Minutes | Start | End |")
    w("| --- | --- | --- | --- | --- |")
    for t in Wk["table"]:
        w(f"| {t['session']} | {t['stops']} | {t['minutes']} | {t['start']} | {t['end']} |")
    w("")
    w("## Assumptions (numbered)")
    w("")
    for i, t in enumerate(M.ASSUMPTIONS, 1):
        w(f"{i}. {t}")
    w("")
    w("**Gaps shipped (the brief's three cycles are used):**")
    w("")
    w(f"- No lobby is verified on foot: {S['buildings_lobby'].get('unknown', 0)} of {S['buildings']} buildings have an unknown lobby type, and every building's "
      "certificate-of-insurance rule is unknown.")
    w(f"- Headcounts are the weakest field: {S['conf_band_table'][-2]['total']} of {S['candidates']} candidates have an unknown band, and each row says why.")
    w("- LinkedIn company URLs are blank: LinkedIn was not opened.")
    w("- No store row claims a store carries a named brand; brand-to-store evidence belongs in the Clay brand table.")
    w("- The phone map is untested on a real phone (README, one-minute phone test).")
    w("")
    w("## Changelog")
    w("")
    for a, b in M.CHANGELOG:
        w(f"- **{a}.** {b}")
    w("")
    w("## Rule breaches")
    w("")
    w("- **A privacy rule was broken during research.** On 2026-10-23 or 24 (the exact time was not logged), research slice S1 sent the account owner's "
      "email address in the User-Agent header of a request to www.sec.gov. It was downloading the 215 Park Ave S loan prospectus, and SEC EDGAR refuses "
      "requests without a contact email (`_work/notes_S1.md`, line 51).")
    w("- Slice S2 also used EDGAR and data.sec.gov and did not record what it sent, so it may have done the same. Its session has ended, so this cannot be confirmed.")
    w("- The assembler opened one EDGAR page with no personal identifier. No file here stores the owner's identifiers.")
    w("- The 12 rows that cite sec.gov say so in their notes (B-C-033 to 039, B-C-047, B-C-192, 196, 197 and 203), and since review round 3 the coworking row "
      "for Industrious 215 Park Ave S cites the same rent roll. You may open those links in a browser. No build script calls sec.gov, and no agent will open it again.")
    w("- No other rule was broken: nothing was sent, posted, bought or published, no connector wrote anywhere, and no git command was run.")
    w("")
    w("## Questions for you (each with my recommended default)")
    w("")
    for i, (q, d) in enumerate(M.QUESTIONS, 1):
        w(f"{i}. **Q{i}.** {q} *Default:* {d}")
    w("")
    return "\n".join(out)


if __name__ == "__main__":
    S = json.load(open(os.path.join(HERE, "out", "stats.json")))
    sys.stdout.write(report(S))
