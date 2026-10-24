# Financial model (workstream H)

The workbook the founder opens every week for six months to see whether the business is working: contribution per founder hour on each drop, the lowest point of cumulative cash, and which gate or decision scenario the real numbers point to.

Every figure is a planning estimate from `plan.md`, never a forecast. The working name lives in one cell (Inputs, section 1, "Company name").

## Files, in the order you use them

| File | What it is for | How to edit it |
| --- | --- | --- |
| `Desk Drop financial model v1.xlsx` | The model. 21 tabs; open Dashboard first. Its README tab explains every tab, the assumptions, the derived items and the changelog. | Import into Google Sheets (steps below) and edit there: yellow cells on Inputs and Schedule, plus the log and actuals tabs. Do not type over grey or white formula cells. |
| `HANDOFF.md` | The exact CSV layouts H reads from operations (F), outreach (E) and the legal pack (G), and the drop_id rule. | Edit only if a layout changes; tell F and E. |
| `handoff-templates/` | Header-only CSVs: `campaign_actuals.csv`, `drop_costs.csv`, `hours_log.csv`, `pipeline_log.csv`. | F and E build their exports to these headers. |
| `csv/` | Snapshots of the key tabs at plan defaults, recalculated 2026-10-24 (dashboard, inputs, scenarios, schedule, drop_pnl, cash_flow, steady_state, sensitivity, plan_check, capital, checks). | Read-only. Regenerate with `python3 _work/recalc.py --csv csv` from this folder. |
| `REPORT.md` | The report-back message: what was built, how to use it, assumptions, derived items, changelog, blocking questions. This run's subagent could not write report files, so the text was returned to the orchestrator, which saves it here. | Read. |
| `_work/` | Build and audit scripts, kept for reproducibility (see below). | Only if you rebuild the model from code. |

## Open it in Google Sheets (needs your Google login)

1. Go to drive.google.com and sign in.
2. New, File upload, and pick `Desk Drop financial model v1.xlsx`.
3. Open it with Google Sheets. If Drive asks, choose to convert it to a Google Sheet.
4. File, Settings: set the locale to United States and the time zone to America/New_York, so dates and the as-of date read correctly.
5. Check the Dashboard: next to "Checks" it should say "all integrity checks pass", and the Checks tab should show 0 failing. A live import was not possible from the build environment, so this check is yours (unverified, founder to confirm).

## The weekly routine

1. Hours_Log: add the week's hours (date, drop_id or blank, one of seven activity keys, hours).
2. Pipeline: paste or type outreach events.
3. After a drop: paste the actuals into Actuals_Campaigns and Actuals_DropCosts, then set "Actuals in" to Y on Schedule.
4. Read the Dashboard.
5. When a quote, date or plan changes, edit Inputs or Schedule. The "Changed?" columns keep the plan default beside your edit.

Change the price in under a minute: Inputs, section 3, "Standard price per office". Or try a price on Calculator without moving the model.

## `_work/` (scripts and evidence)

| File | Purpose |
| --- | --- |
| `build_model.py` | Builds the workbook with openpyxl. Rebuilding overwrites the file, so it would erase anything typed into a copy of it. Use it only to change the structure. |
| `readme_text.py` | Text of the README tab. |
| `recalc.py` | Recalculates the workbook with LibreOffice headless and prints checks, errors and key outputs; `--csv DIR` writes the snapshots. |
| `audit_formulas.py` | Lists every formula with a numeric literal other than 0 or 1 (result: 0 of 15,472), every function used against Google's Sheets list (37 functions, all listed), features Sheets would drop, and any cell spelling the company name outside its one input cell. |
| `test_model.py` | 54 behaviour tests on edited copies: price, processing, storage, insurance billing, close rate, drop size, office goal, scenarios A to D, zero brands, one office, 100% renewal, Friday and blackout dates, an added drop, a SAMPLE actuals run through every gate, Toggl import, bad data. The deliverable is never modified; SAMPLE rows never ship. |
| `dump.py` | Prints recalculated ranges, for review. |
| `test_log.txt`, `audit_log.txt` | Output of the last test and audit runs. |
| `ref_map.json` | Where each named input and key output sits (sheet and cell), for the scripts. |
| `NOTES.md` | Working notes: plan readings checked by hand, research with dates, round-by-round findings. |
