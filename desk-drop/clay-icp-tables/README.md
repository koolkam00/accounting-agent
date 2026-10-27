# Clay ICP tables (workstream A)

These are two outreach tables, Offices and Brands, that hand the founder ten outreach-ready targets per side each morning. No Clay or Google login was available, so they are built as a Google Sheets workbook with live views plus Clay import files.
- Nothing was sent, bought or signed up for. No credits were used, and the running cost is $0.
- All dates are 2026-10-24 unless stated.
- The working name lives in one cell, `Routine!B1` (`company_name`) in the workbook.
- The Sheet is the only table of record. Clay is the research and email engine.

## Files, in the order you use them

| # | File | What it is for | How to edit |
| --- | --- | --- | --- |
| 1 | `clay-build-sheet.md` | Start here. It covers the hard gates and scoring in plain words, the column dictionary, the morning routine and the Friday prep, seeding and refresh, Clay setup (import, research prompts, email waterfall spec) and running cost | Text |
| 2 | `clay-icp-tables.xlsx` | The workbook to open in Google Sheets. Its tabs are Offices and Brands; Daily view - Offices and Daily view - Brands; Walk list - Offices (top-50 offices with nobody named); Founder review - Brands; Enrichment (the one place Clay or Hunter results are pasted); Dictionary; Scoring; and Routine. Contacts shown, emails, channel, score, `score_reason`, readiness and every view are formulas, filled to row 1000, so the views move the moment you edit status, do-not-contact, a hold, the known flag, `promote_backup`, a review or your OK | Type only in yellow-header columns (yours) and blue-header columns (outreach). Grey headers are formulas. Never paste over the Offices or Brands tab: the views go blank with a warning if you do. No macros or scripts |
| 3 | `daily-view-offices.csv`, `daily-view-brands.csv` | Today's ten per side as files (CONTRACTS 6.2), for E's draft maker and for anyone without the Sheet | Rebuilt. In daily use, download the Sheet's view tabs into `live/` instead (routine step 4) |
| 4 | `walk-list-offices.csv`, `founder-review-brands.csv` | The Walk list (13 offices) and the Founder review list (the 30 best of 107 brands waiting on a blocking review) as files | Rebuilt |
| 5 | `offices.csv`, `brands.csv` | The full tables: 308 office rows (243 passed the gates, top 50 flagged) and 311 brand rows (196 passed, top 60 flagged). Every gated-out row is kept with its reason | Rebuilt from sources; never hand-edit researched columns |
| 6 | `column-dictionary.csv` | Every column of both tables: group, who edits it, allowed values and meaning (240 entries) | `_build/dictionary.py` |
| 7 | `clay-import/offices-clay-import.csv`, `clay-import/brands-clay-import.csv` | 175 passed rows per table for Clay Free (200 rows per table, leaving 25 for referrals): every ready row first, then the best others. Research and contact columns only, with no status, control, formula or tracking column | Rebuilt |
| 8 | `spot-check-log.md` | The quality loop by round: stage-1 rounds 1 to 5, stage-3 rounds 6 to 8, the daily-view audit, the independent review's sample, rounds 9 and 10 after the review fixes, the two health-claim scans (homepages, then catalogs, About and FAQ), and the re-timed routine | Text |
| 9 | `HANDOFF.md` | What this workstream takes from B, D, G and H and gives to E and H, with file paths and column names, and where it deviates from CONTRACTS | Text |
| 10 | `_review/` | The independent review (`round-1.md`, with the builder response at the end) and its evidence | Reviewer's folder |
| 11 | `live/` (create it when outreach starts) | Save the Sheet's Offices, Brands and Enrichment tabs here every Friday as `offices-live.csv`, `brands-live.csv` and `enrichment-live.csv`, and today's view downloads as `daily-view-offices.csv` and `daily-view-brands.csv`. A rebuild then carries status, opt-outs, holds, OKs, reviews, LinkedIn URLs, emails, swapped or added contacts, E's columns and referral rows | Downloaded CSVs |
| 12 | `_build/` | The build (next section) | Python 3 |
| 13 | `_work/` | Research and evidence (see the last section) | Corrections go into the `stage3_*` or `contacts_r9_*` files with a source and date, then rebuild |

## The build (`_build/`)

`python3 -B clay-icp-tables/_build/build_all.py` from `desk-drop/` runs the steps in order, in seconds and offline:
- `build_offices.py`: gates and the Tuesday estimate with its space check;
- `build_brands.py`: gates, retailer grades and founder-review types;
- `stage3_merge.py`: contacts, the Python twin of every workbook formula, views, Clay import files and live carry-over;
- `build_xlsx.py`: the workbook.

Supporting files:
- `config.py`: every weight and threshold.
- `dictionary.py`: the column dictionary.
- `common.py`: shared paths and helpers.
- `id_registry_brands.json`: stable brand IDs.

Research and checking tools:
- `fetch_builtin_attendance.py`: Built In attendance pages.
- `scan_claims.py`: the health-claim scan of homepages, Shopify catalogs, About and FAQ pages.
- `recheck_wfm.py`: the Whole Foods store re-check.
- `spotcheck_s3.py`: draws and prints spot-check rows.
- `stage1_counts.py`: prints the counts.
- `peek.py`: opens one page for a spot check and prints snippets around the search terms (never sec.gov or LinkedIn).
- `test_workbook.py`: recalculates the workbook in LibreOffice and compares every formula cell and view with the Python twin in five scenarios. Run it with `A_SOFFICE=<path to soffice>` to test a second version; it passes on 24.2 and 25.8.

## Coverage today, and when the office pool runs out

- **Offices.**
  - 34 of the top 50 name a contact: 10 on the employer's own page or dated press, and 24 only on The Org, which marks them "Unverified" (`contact_status = crowd-listed`; confirm on LinkedIn).
  - 23 have a backup, and 13 are on the Walk list.
  - 181 of 276 companies have a company LinkedIn URL. No person LinkedIn URL is filled; you paste them in the Friday prep.
  - 38 rows are ready. At five a day from E's first cold day (Monday 2026-11-09) they run out around Thursday 2026-11-19. Before then, research ranks 51 to 100 with the Claygent office prompt (49 of ranks 1 to 100 name a person today) and walk the Walk list.
- **Brands.**
  - 57 of the top 60 name a founder or owner. 25 have a marketing lead, 36 have any backup, and 10 have a LinkedIn URL.
  - 66 rows are ready. 107 passed brands wait on your review; the first Friday clears the top 30.
- **Emails.** 0 of 110 verified (0%) until you run the waterfall in Clay or Hunter.

## How to change things

- **A researched fact is wrong.** Add a row to `_work/stage3_corrections.csv` (table, key, field, new value, source URL, date, reason) or, for a contact, `_work/stage3_contact_fixes.csv`. Then rebuild. The table records the change and its source (`a_corrections`, `enrichment_log`, `contact_note`).
- **A weight or threshold.** Edit `_build/config.py`, then rebuild. The workbook's Scoring tab and `clay-build-sheet.md` section 1 describe the same rules, so update them together.
- **After outreach starts.** Save the live tables into `live/` first (row 11). A rebuild without them resets every row to `status = new`.
- **Check the workbook.** Run `python3 -B clay-icp-tables/_build/test_workbook.py` (prints PASS). The last runs are in `_work/test_workbook/last_run_lo242.txt` and `last_run_lo258.txt`.

## Assumptions, deviations and open questions

- The numbered assumptions behind the gates and estimates are in `_work/stage1-notes.md`, section "Assumptions". Those added in stage 3 and this review round (The Org names are crowd-listed, the space check at 125 to 250 sf per person, the brand-level claims rule, review blocking) are in `clay-build-sheet.md` section 1 and the dictionary.
- Where this workstream departs from CONTRACTS is in `HANDOFF.md` section 4.
- The founder's open decisions are listed at the end of `HANDOFF.md`. In order:
  1. which Google and Clay accounts to share with;
  2. whether a claim on some products fails a whole brand;
  3. the review backlog;
  4. the waterfall spend;
  5. the New York share bounds.

## `_work/` at a glance

- **Brands**: research slices `brands_BR1.csv` to `BR5.csv` with their notes and enrichment files.
- **Stage-1 tables and notes**: `stage1_*.csv`, `stage1-notes.md`.
- **Contacts**:
  - stage 2: `contacts_o1.csv`, `contacts_o2.csv`, `contacts_b1.csv` with notes;
  - stage 3: `contacts_s3_entrants.csv`;
  - review round: `contacts_r9_offices.csv` (26 rows), `contacts_r9_brands.csv` (29 rows), with candidates in `r9_*_candidates.csv`.
- **Company LinkedIn links**: `linkedin_company_r9.csv`.
- **Leased square footage** B had not recorded: `space_r9.csv`, each figure with its sentence.
- **Sourced corrections**: `stage3_corrections.csv`, `stage3_contact_fixes.csv`.
- **Health-claim scans**: `claims_scan_2026-10-24.csv`, `claims_scan_v2_2026-10-24.csv` with `_hits.csv`, and the verdicts in `claims_verdicts_2026-10-24.csv`.
- **Other evidence**: the Whole Foods re-check, online-store checks, and spot-check samples and evidence printouts (`spotcheck_r*`).
- **Workbook test runs**: `test_workbook/`.
- **The review round's research scripts**: `r9_tools/`.
- **Every page opened**: `fetch/`, gzipped.
