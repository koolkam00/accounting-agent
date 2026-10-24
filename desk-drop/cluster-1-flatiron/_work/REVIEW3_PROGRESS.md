# Review round 3 fixes: progress log (builder, 2026-10-24)

Working file so nothing is lost on context compaction. Not a deliverable.
Backup of pre-fix outputs: scratchpad B-r3fix/before/.

## Plan (finding -> fix)
- R3-01 REPORT.md: write it (try Write); add confidence-by-band cross-tab to Method + stats.
- R3-02 public_map.py brand mode: --labels numbers|names, collision pass + leader lines, 40 px frame pad; QA PNGs to _build/out/qa/; HANDOFF answers D.
- R3-03 frontage.corner(): clamp pin inside own MapPLUTO lot (frontage midpoint 3 m inside); 26 m rule only if frontage > 35 m; pin_qa lot test.
- R3-04 occupied + only undated profile -> occupancy-unconfirmed (6 rows); assemble rule.
- R3-05 parents GA/Corcoran/BrainPOP + Wikipedia pass on the rest.
- R3-06 Built In not independent: find third-party source or lower 4 highs to medium; re-run route.
- R3-07 three notes reworded; banned patterns.
- R3-08 outside operator coworking sites onto walk sessions 8-10.
- R3-09 six text slips.
- R3-10 year-only dates; list separator ";".

## Status
- [x] R3-03 code: frontage.lots/clamp_to_lot (MapPLUTO 26v2 via planninglabs.carto.com, cache _build/out/lots_cache.json), assemble.clamp_lots
      (skips + notes when the lot is not on the addressed face: 33 E 18th St, a no-candidate building), pin_qa own_lot column. 31 pin moves; 0 outside.
- [x] R3-06 research: Dashlane CO 2019-04-22 (10-yr, 4th fl), CompStak CO 2022-12-20, Empathy CO 2024-03-06, Signal AI CO 2022-12-19, Carbyne
      Connect CRE 2023-08-18 -> stay high with independent second source. TripleLift: no third-party source (search) -> medium. BrainPOP: only CO
      2010-08-10 (15-yr lease, term ends ~2025) -> medium. Seedtag (near-miss): CO 2023 three-year lease ended ~2026-03 -> medium.
      Coworking: operator page + Deskpass/LiquidSpace listing is not independent either -> medium (B-W-003,011,015,021,022,023,027,032);
      B-W-005 keeps high via the 215 PAS rent roll (SEC, 2026-02, not re-opened).
- [x] R3-05: Wikipedia raw wikitext opened 2026-10-24: GA 'purchased by the Adecco Group in 2018' (last edited 2026-10-05); Corcoran
      'parent = Compass, Inc.' (2026-05-27); BrainPop 'owner = Kirkbi' (2026-10-09). Pass over the rest running (scratchpad B-r3fix/wiki).
