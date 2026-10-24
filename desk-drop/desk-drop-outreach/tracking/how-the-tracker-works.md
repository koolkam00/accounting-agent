# How the tracker works

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/tracking/`

**What it is.** `conversation-tracker.xlsx` is the conversation and notes log for discovery and selling: one row per conversation, keyed by the Clay `row_id`, with the plan's Phase 0 columns (plan, "Tracking sheet columns"). On top of the log sit the Friday scorecard against Gate 0 (and Gate 1 after it), a sync check against the Clay tables, the handoff rows for operations, and the pipeline export for the financial model.

**What it is not.** It is not a status store. Status, touches, replies, next actions and do-not-contact live in the Clay tables and nowhere else (CONTRACTS 6.2; prompt A, "Status lives in these tables and nowhere else"). The tracker reads a copy of Clay once a week to check the two agree.

## Files

| File | What it is |
| --- | --- |
| `conversation-tracker.xlsx` | The blank workbook to use. Import it into Google Sheets once (section 2) |
| `conversation-tracker-SAMPLE.xlsx` | The same workbook filled with SAMPLE rows (15 office and 16 brand conversations, 79 Clay rows, one signed office, one paid brand). Every row starts with SAMPLE and the Scorecard carries a red SAMPLE banner. For learning the workbook and for the Google Sheets check in section 2 |
| `scorecard-SAMPLE.pdf`, `scorecard-SAMPLE-p1.png`, `-p2.png` | The SAMPLE scorecard as LibreOffice calculates it, to look at |
| `csv/office_log.csv`, `csv/brand_log.csv` | The log columns as header-only CSV files |
| `csv/clay_tracking_columns.csv` | The 13 conversation-tracking columns to add to both Clay tables, with their rules |
| `csv/scorecard-SAMPLE.csv` | Every SAMPLE scorecard value, for checking the Google Sheets copy |
| `../tools/build_tracker.py` | Builds both workbooks. Change a column or a list here, not by hand, then rebuild |
| `../tools/test_tracker.py` | Builds, recalculates in LibreOffice and checks 245 values against an independent computation |
| `../tools/test_h_compat.py` | Pastes `exports/pipeline_log.csv` into a temporary copy of the financial model and checks H's own Pipeline checks and Gate 0 and Gate 1 counts against the Scorecard |
| `../tools/export_csv.py` | Writes the clean CSV files (also from a workbook downloaded from Google Sheets: `--from FILE.xlsx`) |

## 1. Two stores, one owner per column

| What | Lives in | Written when | Copied to |
| --- | --- | --- | --- |
| `status`, `do_not_contact`, `opt_out_date` | Clay | At send, reply and call time; an opt-out the same day | Nowhere. The tracker reads them on Friday |
| `sequence`, `touch_1_date` to `touch_3_date`, `last_reply_date`, `reply_type` | Clay | At send and reply time | Nowhere. The Scorecard reads them for reply rates |
| `next_action`, `next_action_date`, `referral_from` | Clay | Whenever the next step changes | Nowhere |
| Everything said on a call: verbatims, headcount, spend, the budget probe, willingness to pay, objections, the pantry owner and receiving window, referrals given | Tracker (Office_Log, Brand_Log) | Within ten minutes of the call | Nowhere |
| `call_date`, `yes_in_principle` | **Tracker first**, then Clay | Tracker row first; Clay in the same ten minutes | Clay keeps a copy for the daily views. The Friday sync flags any difference |
| `call_notes`, `call_note_hook` | Clay | In the same ten minutes | `call_notes` is one line plus "see tracker YYYY-MM-DD", never the full note |
| Signed offices, paid brands | Tracker (`signed_offices`, `paid_brands` tabs) | At signature or payment | Downloaded to `handoff/` for operations; Clay `status` set to `signed` or `paid` the same day |

So there is exactly one place to write each fact. The two shared fields (`call_date`, `yes_in_principle`) flow one way, tracker to Clay, and the sync check catches a missed copy.

**How the two stay in sync, in practice.** After every call, the post-call note (`calls/post-call-note-template.md`) has a Clay write-back step and a `clay_updated` column. Every Friday you paste a fresh Clay export into the tracker; the tracker then lists, in red:

| Flag | Where | Means | Fix |
| --- | --- | --- | --- |
| row_id not found in the Clay paste | `calc_sync_issue` on the log | The conversation has no Clay row, or the `row_id` is mistyped | Add the Clay row (walk-ins and referrals often lack one) or fix the id |
| Clay status is `replied` (or earlier): set call_done or later | log | The call was logged but Clay still shows the pre-call state | Set `call_done` or `yes_in_principle` in Clay |
| Clay yes_in_principle should be Y (or N) | log, latest row per office or brand | The copy was missed | Copy it |
| Clay call_date should be YYYY-MM-DD | log, latest row | The copy was missed | Copy it |
| status call_done (or later) but no tracker row | Sync tab | Clay says you talked, the tracker has no notes | Write the note, or fix the status |
| do_not_contact = Y but status is ... (or the reverse) | Sync tab | An opt-out half-recorded | Set both: `status = do_not_contact` and `do_not_contact = Y` |
| status signed but no signed_offices row; status paid but no paid_brands row | Sync tab | The handoff row is missing | Add it (`handoff/how-to-fill-handoff-files.md`) |
| Clay status is ...: set signed / paid | Sync tab, handoff list | A handoff row exists but Clay was not updated | Update Clay |
| status '...' is not a CONTRACTS status | Sync tab | A typo or an invented status | Use a CONTRACTS section 4 value |

The Scorecard's Data checks block counts every one of these and shows FIX until they are cleared.

## 2. Setting it up (once, about 20 minutes)

Steps marked **(login)** need your Google or Clay account.

1. **(login)** In Google Drive, upload `conversation-tracker-SAMPLE.xlsx` first and open it with Google Sheets (File > Save as Google Sheets).
2. **The Google Sheets check.** The workbook was tested in LibreOffice, not in Google Sheets, because no Google login exists here. On the converted SAMPLE copy, open Scorecard and compare a dozen values with `csv/scorecard-SAMPLE.csv` (for example the Gate 0 counts, the medians, the top objections, the reply rates). They should match exactly. If any cell shows an error or a different number, stop and note which; the formulas avoid every function Google Sheets lacks, but this is the proof.
3. **(login)** Upload `conversation-tracker.xlsx` the same way. This is the real one. Leave the SAMPLE copy for reference or delete it.
4. On **Config**, check `include_sample` is N and `as_of_date` is `=TODAY()`. Leave the dates (derived, founder to confirm) unless the calendar changes.
5. **(login, Clay)** Make sure both Clay tables carry the 13 conversation-tracking columns in `csv/clay_tracking_columns.csv` (the Clay_Columns tab says the same). Workstream A is building the tables to include them; if they are missing, add them as text or date columns with exactly these names. Part A of this workstream also adds personalization columns (`street_short`, `why_now_hook`, `call_note_hook`, `referrer_ok_to_name`, `how_we_know`, `product_short`; see `messages/03-personalization-fields.csv`). The tracker does not read those.
6. Rename, if the name changes: Config `company_name`. Every tab title follows.

## 3. After every call

Follow `calls/post-call-note-template.md`: one row on Office_Log or Brand_Log, then the Clay write-back, in ten minutes. The quickest way to the row is the **Note_Office** or **Note_Brand** tab: the same fields top to bottom, with dropdowns, usable on a phone. Fill column B, check the cell above the "row to paste" says "OK to paste", copy that row, click column A of the first empty log row, and paste values only (Ctrl+Shift+V, or Edit > Paste special > Values only). Then clear column B for the next call. The grey `calc_` columns to the right of each log are formulas; most are hidden. Only `calc_sync_issue` stays visible.

## 4. Every Friday (15 minutes)

1. **(login, Clay)** Export the Clay offices table, all columns, as CSV. Open the CSV in Google Sheets (or any spreadsheet), select everything including the header row, copy, then click cell A1 of the tracker's **Clay_Offices** tab and paste. Same for brands on **Clay_Brands**. Paste over the old data; do not delete the tab (the formulas point at it). Columns are found by their header names, so their order does not matter. Type both export dates on Config.
2. Open **Scorecard**. Under Data checks, clear every FIX (section 1 says how).
3. Read the Gate 0 block, the medians, the top three objections per side and the reply rates. If a side says **UNDER 20%**, run `sending/sending-setup.md` section 6 before sending more.
4. **Pipeline export.** On the **pipeline_log** tab: File > Download > Comma-separated values (current sheet). Save it as `desk-drop-outreach/exports/pipeline_log.csv`, replacing the file there, and paste it into the financial model's Pipeline tab with its header in row 4 (`financial-model/HANDOFF.md` section 3).
5. **Startup CPG post numbers.** When you are ready to post findings (`messages/12-startup-cpg-posts.md`), the block "Numbers for the Startup CPG posts" gives each counted slot. Quote only rows with `quote_ok_to_share` = Y, never with a name.
6. **Copy-slot counts.** Copy the six values under "Counts for the copy slots" into `messages/04-slot-state.csv` (`offices_yes`, `offices_signed`, `tuesday_headcount`, `founding_taken`, `brands_paid`, `brand_selling_on`). That CSV wins; the tracker only computes them. The switches you set by hand (`domain_ready`, `attorney_cleared`, and the rest) live only there.
7. On Gate 0 day (Fri 2026-11-13, derived, founder to confirm), copy the sentence under "Gate 0 overall" into the one-sentence decision the plan asks for.

## 5. How the Scorecard counts

All counts are **distinct offices or brands** (Clay `row_id`), dated by `call_date`, for four cut-offs: Friday of week 1 (2026-10-30), Friday of week 2 (2026-11-06), Gate 0 (2026-11-13) and the as-of date (Config; default today).

| Measure | Rule |
| --- | --- |
| Conversations | A row with a `row_id` and a real `call_date` (`calls/office-call-guide.md` section 8 says what counts as a conversation) |
| Warm conversations | Office conversations with `channel` = warm-intro (anyone you knew before). Target 5 of the 15 (plan, Phase 0) |
| Shortlist | Offices and brands with `shortlist` = Y on any row. Targets 8 and 6 (plan, Phase 0 deliverables) |
| Office Gate 0 yes | `yes_in_principle` = Y **and** `pantry_owner_named` = Y **and** a `receiving_window`, from the office's first such conversation. Target 5 |
| Brand Gate 0 yes | The higher of `wtp_before_usd` and `wtp_after_usd` is $500 or more **and** `controls_budget` = Y. Target 3. Same rule as the financial model's Pipeline tab. A strict read (before $1,500 only) is shown under it |
| Gate 0 status | PASS when the count reaches the target. Before Gate 0 a shortfall reads "not yet"; on or after Gate 0 it reads FAIL. Overall PASS needs both sides |
| Median office budget probe | First numeric answer per office (`budget_probe_low_usd`, the low end of a range; "no budget" = 0, counted; no number = left out). The n and the number of zeros are shown with it |
| Median brand number before $1,500 | First numeric `wtp_before_usd` per brand; "nothing" = 0, counted. The after-$1,500 median is shown separately |
| Top three objections | Mentions of each code across `objection_1` to `objection_3`, as of the as-of date; ties go to the code listed first on Lists; the first quote logged for that code is shown beside it |
| Reply rate | Clay rows with `last_reply_date` by the cut-off (bounces and auto-replies excluded) over rows with `touch_1_date` by the cut-off. Judged only after 30 first touches on a side |
| Gate 1 | Offices signed (rows on `signed_offices` dated by the cut-off), their combined Tuesday headcount (target 350), brands paid in full (payments reach `price_usd`); one paid brand reads SOFT PASS on or after Gate 1 (plan Phase 2) |

Rows whose `row_id` starts with SAMPLE are ignored everywhere while Config `include_sample` = N, and the red banner says so if any are present.

## 6. Limits and caveats

- **Capacity:** 200 conversations per side, 600 Clay rows per side in the paste, 50 signed offices and 50 paid brands, 100 later events, 1,000 pipeline events. The Data checks flag an overflow of the pipeline; raise the numbers at the top of `tools/build_tracker.py` and rebuild if the business outgrows them.
- **Do not reorder or delete the input columns.** The handoff tabs mirror CONTRACTS column order so an intake row pastes in one go, and the CSV files must keep their headers. Add a field you need to `notes`, or add it in `tools/build_tracker.py` and rebuild.
- **Downloading a tab from Google Sheets** gives one CSV line per formula row, including empty ones (`,,,,`). Pasted into another sheet they are empty cells, so this is harmless; `tools/export_csv.py --from` drops them if you prefer clean files.
- **Dates must be real dates.** A date typed as text drops out of every count. The Data checks count Clay `touch_1_date` cells stored as text; log rows with a non-date `call_date` show a sync flag.
- **`as_of_date = TODAY()`** follows the spreadsheet's time zone (File > Settings in Google Sheets). Type a date over it to read an earlier Friday.
- **Not tested in Google Sheets** (no login); tested in LibreOffice 24.2 (section 2, step 2 is the check).

## 7. How it was tested

`python3 tools/test_tracker.py` builds both workbooks, recalculates them with LibreOffice headless, and compares 245 values with an independent Python computation from `tools/sample_data.py`: every Gate 0 count and status at all four cut-offs, every median and its n, the top three objections with their quotes, reply and conversation rates, the variant table, every sync flag (seven planted problems, all found, no false alarms), the handoff formulas, the Gate 1 block, the copy-slot counts, the Note_Office round trip (its row to paste equals the log row it came from), and the whole pipeline export row by row (210 events, in date order). It then flips `include_sample` to N and checks every count drops to zero, recalculates the blank workbook to check it has no error cells, and checks that every column operations reads (`campaign-ops/tools/trackerdef.py`) is in the two handoff files. Last run: `_work/partB/test_log.txt`. Separately, `tools/test_h_compat.py` pastes the SAMPLE pipeline export into a temporary copy of the financial model: H's header, text and event checks read 0, and H's Gate 0 counts (13 and 6 per side), Gate 1 counts (1 signed office, 62 people, 1 brand paid in full) and three medians equal the Scorecard's (`_work/partB/h_compat_log.txt`).

## Changelog

Round numbers are part B's rounds; a round that did not change this file is not listed.

- Round 1 (2026-10-24): workbook, scorecard, sync check and pipeline export built by script; 189 checks.
- Round 2 (2026-10-24): qualification checks on Brand_Log, Gate 1 block, copy-slot counts for Part A, duplicate-handoff check; SAMPLE data made to obey the calendar and the week-one email rule; 214 checks.
- Round 3 (2026-10-24): critique as an operations lead: a 45-column row is slow to type and impossible on a phone, so Note_Office and Note_Brand were added (vertical form, one row to paste, round trip tested); the plan's "five of fifteen from your own network" and "shortlist of 8 offices and 6 brands" are now counted; the Clay paste step says how to paste without breaking the formulas; scorecard cells centred vertically after the render showed values sitting below their labels; 229 checks.
- Round 4 (2026-10-24): four coded fields and a scorecard block so every counted slot in Part A's Startup CPG posts comes from the tracker, with a per-person `quote_ok_to_share`; 241 checks.
- Round 5 (2026-10-24): the ten columns operations reads but the handoff tabs lacked were added (F's `trackerdef.py`, read 2026-10-24) and the test now checks F's full list; the financial-model compatibility test was added; 245 checks.
