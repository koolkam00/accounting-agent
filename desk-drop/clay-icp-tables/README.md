# Clay ICP tables (workstream A)

Two outreach tables, Offices and Brands, that hand the founder ten outreach-ready targets each morning. No Clay or Google login was available, so they are built as import-ready files and a Google Sheets workbook with live daily views. Nothing was sent, bought or signed up for. All dates are 2026-10-24 unless stated. The working name lives in one cell, `Routine!B1` (`company_name`) in the workbook.

## Files, in the order you use them

| # | File | What it is for | How to edit |
| --- | --- | --- | --- |
| 1 | `clay-build-sheet.md` | Start here. Hard gates and scoring in plain words, the column dictionary, the 15-minute morning routine, seeding and refresh, Clay setup (import steps, research prompts, the email waterfall spec) and running cost | Text |
| 2 | `clay-icp-tables.xlsx` | The tables to open in Google Sheets: Offices, Brands, Daily view - Offices, Daily view - Brands (live `SORT(FILTER())` views), Dictionary, Scoring, Routine. Score, readiness and the view helpers are formulas, so the views move when you change status, do-not-contact, a hold, the known flag or your OK | Type only in yellow-header columns (yours) and blue-header columns (outreach). Grey headers are formulas. Header row 1; no macros or scripts |
| 3 | `daily-view-offices.csv`, `daily-view-brands.csv` | Today's ten per side as files (CONTRACTS 6.2), for E's draft maker and for anyone without the Sheet | Rebuilt; in daily use, download the Sheet's view tabs instead |
| 4 | `offices.csv`, `brands.csv` | The full tables: 308 office rows (241 passed the gates, top 50 flagged) and 311 brand rows (239 passed, top 60 flagged), every gated-out row kept with its reason | Rebuilt from sources; never hand-edit researched columns |
| 5 | `column-dictionary.csv` | Every column of both tables: group, who edits it, allowed values, meaning (201 entries) | `_build/dictionary.py` |
| 6 | `clay-import/offices-clay-import.csv`, `clay-import/brands-clay-import.csv` | The 175 best passed rows per table for Clay Free (200 rows per table; 25 left for referrals) | Rebuilt |
| 7 | `spot-check-log.md` | The quality loop by round: stage-1 rounds 1 to 5, stage-3 rounds 6 to 8, the health-claim scan and the daily-view audit, with every row, field and source | Text |
| 8 | `HANDOFF.md` | What this workstream takes from B, D, G and H and gives to E and H, with file paths and column names, and where it deviates from CONTRACTS | Text |
| 9 | `REPORT.md` | The report back: counts, error rates, cost, assumptions, changelog, blocking questions | Text |
| 10 | `live/` (create it when outreach starts) | Save the Sheet's Offices and Brands tabs (or the Clay tables) here as `offices-live.csv` and `brands-live.csv` before anyone rebuilds, so status, opt-outs, swapped contacts and referral rows carry over | Downloaded CSVs |
| 11 | `_build/` | The build: `build_all.py` runs `build_offices.py`, `build_brands.py`, `stage3_merge.py`, `build_xlsx.py`. `config.py` holds every weight and threshold; `dictionary.py` the column dictionary; `test_workbook.py` recalculates the workbook in LibreOffice and checks it; `spotcheck_s3.py`, `scan_claims.py`, `recheck_wfm.py`, `peek.py` are the checking tools | Python 3; `python3 -B clay-icp-tables/_build/build_all.py` from `desk-drop/` (seconds, offline) |
| 12 | `_work/` | Research and evidence: the five brand research slices and their enrichment files, stage-2 contact files (`contacts_o1.csv`, `contacts_o2.csv`, `contacts_b1.csv`) with notes, stage-3 sourced corrections (`stage3_corrections.csv`, `stage3_contact_fixes.csv`, `contacts_s3_entrants.csv`), the health-claim scan, the Whole Foods re-check, spot-check samples and evidence printouts, and every page opened (`fetch/`, gzipped) | Corrections go into the `stage3_*` files with a source and date, then rebuild |

## How to change things

- **A researched fact is wrong**: add a row to `_work/stage3_corrections.csv` (table, key, field, new value, source URL, date, reason) or, for a contact, `_work/stage3_contact_fixes.csv`, then rebuild. The table records the change and its source (`a_corrections`, `enrichment_log`, `contact_note`).
- **A weight or threshold**: `_build/config.py`, then rebuild. The workbook's Scoring tab and `clay-build-sheet.md` section 1 describe the same rules; update them together.
- **After outreach starts**: save the live tables into `live/` first (row 10 above). A rebuild without them resets every row to `status = new`.
- **Check the workbook**: `python3 -B clay-icp-tables/_build/test_workbook.py` (LibreOffice recalculation against the CSVs plus an edit scenario; prints PASS).
