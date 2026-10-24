# Round 2 review notes (reviewer scratch)
Started 2026-10-24. Working dir desk-drop-identity/_review/work-r2/.

## Initial observations
- REPORT.md still missing (R1-01 deferred; builder says harness refused write). README line 85, HANDOFF deviation 6 say pending.

## Results so far (all run by reviewer, 2026-10-24)
- T1 25-word allergen: PASS. 14.00 pt w600 #000 both faces (scripts/measure-card.js). All-caps 21+21 word case rv2-caps also passes.
- T2 120 px: PASS all 9 variants (downscale/sheet-120-x2.png). Wide logo weakest (rv2-caps-logo-120-x4.png).
- T3 close photo: PASS 4032/2048, readable zoomed at 1280 (close/). QR decodes 4032/2048, not 1280.
- T4 report 10 offices: PASS one page; my 83/79/76-word comments + 96-word learned + velocity -> photos all to p2, comments 8 pt.
- T5 swap: 17 actions, 9 guide steps, ~9 min. PASS.
- T6 fonts: PASS (gf.css 200; OFL identical; METADATA license OFL).
- T7 rename: PASS for outputs (Shelfwise in copy2, 0 "desk drop" in PDFs) BUT Chrome-saved details wiped (major).
- T9 signature: PASS. T10 avatar: PASS. T11 specs: PASS. T12 tokens: PASS with --dd-rule collision.
## Findings
- BLOCKER REPORT.md missing (G and H have one).
- BLOCKER evidence page captions "D · day 1, placement · Tue 2027-02-09" for an office placed late (dd-report.js line 243); shipped SAMPLE PDF shows it.
- MAJOR proposal standard 10/12 offices + 4 realistic stores refused (over 0.22 in); builder test used short names.
- MAJOR details saved via details.html lost on rename (brand-sync mtime rule).
- MAJOR claims words only warn; --final exit 0 with "boosts immunity and supports gut health" on card.
- MAJOR two flavors allowed by proposal, card has one allergen statement.

## Done
Wrote _review/round-2.md: 2 blockers (R2-01, R2-02), 4 majors (R2-03..R2-06), 10 minors (R2-07..R2-16).
