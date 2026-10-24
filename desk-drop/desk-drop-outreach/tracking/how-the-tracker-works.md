# How the tracker works

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/tracking/`

**What it is.** `conversation-tracker.xlsx` is the conversation and notes log for discovery and selling: one row per conversation, keyed by the Clay `row_id` and counted once per organisation (`calc_org`), with the plan's Phase 0 columns (plan, "Tracking sheet columns"). On top of the log sit the Friday scorecard against Gate 0 (and Gate 1 after it), a sync check against the Clay tables, the handoff rows for operations, and the pipeline export for the financial model.

**What it is not.** It is not a status store. Status, touches, replies, next actions and do-not-contact live in the Clay tables and nowhere else (CONTRACTS 6.2; prompt A, "Status lives in these tables and nowhere else"). The tracker reads a copy of Clay once a week to check the two agree.

## Files

| File | What it is |
| --- | --- |
| `conversation-tracker.xlsx` | The blank workbook to use. Import it into Google Sheets once (section 2) |
| `conversation-tracker-SAMPLE.xlsx` | The same workbook filled with SAMPLE rows (16 office and 16 brand conversations, one of them an office withdrawing its yes; 79 Clay rows; five signed offices and one paid brand that all five approved). Every row starts with SAMPLE and the Scorecard carries a red SAMPLE banner. For learning the workbook and for the Google Sheets check in section 2 |
| `scorecard-SAMPLE.pdf`, `scorecard-SAMPLE-p1-top.png`, `-p1-bottom.png`, `-p2-top.png`, `-p2-bottom.png` | The SAMPLE scorecard as LibreOffice calculates it, to look at (PNGs at 150 dpi, each page in two halves) |
| `csv/office_log.csv`, `csv/brand_log.csv` | The log columns as header-only CSV files |
| `csv/clay_tracking_columns.csv` | The 13 conversation-tracking columns to add to both Clay tables, with their rules |
| `csv/scorecard-SAMPLE.csv` | Every SAMPLE scorecard value, for checking the Google Sheets copy |
| `../tools/build_tracker.py` | Builds both workbooks. Change a column or a list here, not by hand, then rebuild |
| `../tools/test_tracker.py` | Builds, recalculates in LibreOffice and checks 315 values against an independent computation, plus four Gate 0 scenarios |
| `../tools/test_h_compat.py` | Pastes `exports/SAMPLE-pipeline_log.csv` (the live file ships header-only) into a temporary copy of the financial model and checks H's own Pipeline checks and Gate 0 and Gate 1 counts against the Scorecard |
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
| Clay yes_in_principle should be Y (or N) | log, latest row per office or brand | The copy was missed, or a later call withdrew a yes | Copy it: Clay carries the latest answer (Y only if the latest Y, N or maybe in the tracker is Y) |
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
5. **(login, Clay)** Make sure both Clay tables carry the 13 conversation-tracking columns in `csv/clay_tracking_columns.csv` (the Clay_Columns tab says the same). Workstream A is building the tables to include them; if they are missing, add them as text or date columns with exactly these names. The message files also add six personalization columns (`street_short`, `why_now_hook`, `call_note_hook`, `referrer_ok_to_name`, `how_we_know`, `product_short`; see `messages/03-personalization-fields.csv`). The tracker does not read those.
6. Rename, if the name changes: Config `company_name`. Every tab title follows.

## 3. After every call

Follow `calls/post-call-note-template.md`: one row on Office_Log or Brand_Log, then the Clay write-back, in ten minutes. The quickest way to the row is the **Note_Office** or **Note_Brand** tab: the same fields top to bottom, with dropdowns, usable on a phone. Fill column B, check the cell above the "row to paste" says "OK to paste", copy that row, click column A of the first empty log row, and paste values only (Ctrl+Shift+V, or Edit > Paste special > Values only). Then clear column B for the next call. The grey `calc_` columns to the right of each log are formulas; most are hidden. Only `calc_sync_issue` stays visible.

## 4. Every Friday (15 minutes)

1. **(login, Clay)** Export the Clay offices table, all columns, as CSV. Open the CSV in Google Sheets (or any spreadsheet), select everything including the header row, copy, then click cell A1 of the tracker's **Clay_Offices** tab and paste. Same for brands on **Clay_Brands**. Paste over the old data; do not delete the tab (the formulas point at it). Columns are found by their header names, so their order does not matter. Type both export dates on Config.
2. Open **Scorecard**. Under Data checks, clear every FIX (section 1 says how).
3. Read the Gate 0 block, the medians, the top three objections per side and the reply rates. If a side's reply-rate check says **UNDER 20%** (conversation replies under 20% of first touches) or its opt-out check says **OPT-OUTS OVER 5%** (at least 3 opt-outs and over 5%), run `sending/sending-setup.md` section 6 before sending more.
4. **Pipeline export.** On the **pipeline_log** tab: File > Download > Comma-separated values (current sheet). Save it as `desk-drop-outreach/exports/pipeline_log.csv`, replacing the file there, and paste it into the financial model's Pipeline tab with its header in row 4 (`financial-model/HANDOFF.md` section 3).
5. **Startup CPG post numbers.** When you are ready to post findings (`messages/12-startup-cpg-posts.md`), the block "Numbers for the Startup CPG posts" gives each counted slot. Quote only rows with `quote_ok_to_share` = Y, never with a name.
6. **Copy-slot counts.** Compare the six values under "Counts for the copy slots" with `messages/04-slot-state.csv` (`offices_yes`, `offices_signed`, `tuesday_headcount`, `founding_taken`, `brands_paid`, `brand_selling_on`) and copy any that differ. That CSV wins and the copy reads only it, so change a count there the same day an office signs, a brand pays or anyone leaves; this Friday step is the check. The switches you set by hand (`domain_ready`, `attorney_cleared`, and the rest) live only there.
7. On Gate 0 day (Fri 2026-11-13, derived, founder to confirm), copy the sentence under "Gate 0 overall" into the one-sentence decision the plan asks for. Each side reads PASS, FAIL or INCOMPLETE. **FAIL** means the plan's test was run (15 conversations held) and the yes count fell short: apply the plan's response in the row "If it fails (plan)". **INCOMPLETE** means fewer than 15 conversations were held and the target was not reached: the test has not been run, so never apply the failure response. Recommended default (founder to confirm, blocking question 4): keep booking discovery calls on that side, and on Fri 2026-11-20 set Config `as_of_date` to 2026-11-20 and read the As of column by the same rule ("stretch the weeks but keep the gates", plan). **The stretch ends at the final read, Fri 2026-11-27** (Config `gate0_final_read`, review round 3): from that date a side still short of its target reads FAIL whatever the number of conversations, and the plan's failure response applies. It ends earlier for a side that reaches 15 conversations first. A side that passed goes ahead meanwhile; brand selling copy waits for a brand PASS (`brand_selling_on`).

## 5. How the Scorecard counts

All counts are **distinct offices or brands**, dated by `call_date`. Since review round 3 an organisation is not a Clay row: every row is counted under `calc_org` (the grey column after `calc_sync_issue` on each log), which is the typed `org_key`, else the Clay `company_group` when A's tables link several rows (`grp-...`, a shared parent, operator or person), else the company name, ignoring case and spaces. So two contacts at one company, the office manager and the workplace lead she named or two founders of one brand, are one office or one brand, and their latest answer, from either, is the one that stands (`calls/post-call-note-template.md`, "Two people at one organisation"). Counts are for four cut-offs: Friday of week 1 (2026-10-30), Friday of week 2 (2026-11-06), Gate 0 (2026-11-13) and the as-of date (Config; default today).

| Measure | Rule |
| --- | --- |
| Conversations | A row with a `row_id` and a real `call_date` (`calls/office-call-guide.md` section 8 says what counts as a conversation), one per organisation (`calc_org`). The data check "Two or more row_ids share one org_key (counted once)" says how many organisations have more than one contact |
| Warm conversations | Office conversations with `channel` = warm-intro (anyone you knew before). Target 5 of the 15 (plan, Phase 0) |
| Shortlist | Offices and brands with `shortlist` = Y on any row. Targets 8 and 6 (plan, Phase 0 deliverables) |
| Office Gate 0 yes | `yes_in_principle` = Y **and** `pantry_owner_named` = Y **and** a `receiving_window`, from the office's first such conversation, **counted only while it stands**: the office's latest answer (Y, N or maybe, by `call_date` then row order) on or before the cut-off must still be Y. A later N or maybe withdraws it; the row "Withdrawn after a yes" shows how many. An office whose latest Tuesday headcount, on any of its rows, is under 30 or over 250 (Config `office_floor`, `office_ceiling`; the plan's hard limits) is shown on its own row and not counted, and the pipeline export leaves out its yes; 30 to 39 is your call, so it counts, with its own row "of the counted yeses: 30 to 39". Target 5 |
| Brand Gate 0 yes | The higher of `wtp_before_usd` and `wtp_after_usd` is $500 or more **and** `controls_budget` = Y, **counted only while it stands**: the brand's latest call on or before the cut-off that gave an answer must still qualify. A later call where `controls_budget` = N, or where every number named is under $500 (for example $0, "budget frozen"), withdraws it; a later call with no number changes nothing. Target 3. A strict read (before $1,500 only) is shown under it, and the withdrawn count below it. The financial model counts any answer of $500 or more, so it still counts a withdrawn brand until it adopts this rule (HANDOFF 2.3) |
| Gate 0 status | PASS when the count reaches the target. Before Gate 0 a shortfall reads "not yet". On or after Gate 0 a shortfall reads FAIL once the side has held its 15 conversations; with fewer, "INCOMPLETE: n of 15 conversations" (the plan's test is 5 of 15 and 3 of 15), until the final read on Fri 2026-11-27 (Config `gate0_final_read`, founder to confirm), from which a shortfall reads FAIL. Overall: PASS needs both sides; FAIL if either side fails; otherwise INCOMPLETE if either is incomplete |
| Median office budget probe | First numeric answer per office (`budget_probe_low_usd`, the low end of a range; "no budget" = 0, counted; no number = left out). The n and the number of zeros are shown with it |
| Median brand number before $1,500 | First numeric `wtp_before_usd` per brand; "nothing" = 0, counted. The after-$1,500 median is shown separately |
| Top three objections | Mentions of each code across `objection_1` to `objection_3`, as of the as-of date; ties go to the code listed first on Lists; the first quote logged for that code is shown beside it |
| Reply rate, all (information only) | Clay rows with `last_reply_date` by the cut-off (bounces and auto-replies excluded, opt-outs and refusals included) over rows with `touch_1_date` by the cut-off. It does not drive the check: a week of "no thanks" would keep it high |
| Conversation-reply rate (drives the 20% check) | Rows whose `reply_type` is `yes`, `maybe`, `needs_approval`, `send_info`, `referral`, `not_now` or an objection (`obj_*`), with `last_reply_date` by the cut-off, over first touches. The plan's 150 messages at 20% is 30 conversations, so a reply here means one that can become a conversation. Judged only after 30 first touches on a side |
| Opt-out rate | Rows with `opt_out_date` by the cut-off over first touches. With 30 or more first touches, at least 3 opt-outs (Config `opt_out_min_count`) **and** over 5% (`opt_out_rate_flag`), both judgment, reads OPT-OUTS OVER 5%: check targeting and copy (sending guide 6.3 to 6.4). Two opt-outs in 39 is noise at this volume, as one bounce in a week is |
| Gate 1 | Offices signed (rows on `signed_offices` dated by the cut-off), their combined Tuesday headcount (target 350), brands paid in full (payments reach `price_usd`); one paid brand reads SOFT PASS on or after Gate 1 (plan Phase 2) |

Rows whose `row_id` starts with SAMPLE are ignored everywhere while Config `include_sample` = N, and the red banner says so if any are present.

## 6. Limits and caveats

- **Capacity:** 200 conversations per side, 600 Clay rows per side in the paste, 50 signed offices and 50 paid brands, 100 later events, 1,000 pipeline events. The Data checks flag an overflow of the pipeline; raise the numbers at the top of `tools/build_tracker.py` and rebuild if the business outgrows them.
- **Do not reorder or delete the input columns.** The handoff tabs mirror CONTRACTS column order so an intake row pastes in one go, and the CSV files must keep their headers. Add a field you need to `notes`, or add it in `tools/build_tracker.py` and rebuild.
- **Downloading a tab from Google Sheets** gives one CSV line per formula row, including empty ones (`,,,,`). Pasted into another sheet they are empty cells, so this is harmless; `tools/export_csv.py --from` drops them if you prefer clean files.
- **Dates and numbers must be real dates and numbers.** A date typed as text drops out of every count, and so does a number typed as text ("$600" counts as nothing). The Data checks count Clay `touch_1_date` cells stored as text, log number cells stored as text, and `call_date` cells that carry a time of day; log rows with a non-date `call_date` show a sync flag. A `call_date` with a time (a paste from a calendar, or "2026-11-13 14:30") still counts on its day, but retype it.
- **`as_of_date = TODAY()`** follows the spreadsheet's time zone (File > Settings in Google Sheets). Type a date over it to read an earlier Friday.
- **Not tested in Google Sheets** (no login); tested in LibreOffice 24.2 (section 2, step 2 is the check).

## 7. How it was tested

`python3 tools/test_tracker.py` builds both workbooks, recalculates them with LibreOffice headless, and compares its values with an independent Python computation from `tools/sample_data.py`: every Gate 0 count and status at all four cut-offs, every median and its n, the top three objections with their quotes, reply rates (all, conversation and opt-out) and both checks, the variant table, every sync flag (seven planted problems, all found, no false alarms), the handoff formulas, the Gate 1 block, the copy-slot counts, the Note_Office round trip (its row to paste equals the log row it came from), and the whole pipeline export row by row (214 events, in date order). It then rewrites the SAMPLE Clay paste so most replies are opt-outs and checks the reply-rate check turns UNDER 20% while the all-reply rate stays above 20%, flips `include_sample` to N and checks every count drops to zero, recalculates the blank workbook to check it has no error cells, and checks that every column operations reads (`campaign-ops/tools/trackerdef.py`) is in the two handoff files, that the live handoff and pipeline files are header-only, and that their `SAMPLE-` copies have the same headers and only SAMPLE rows. Since review round 2 it also checks that a withdrawn yes stops counting at every cut-off (an office in the SAMPLE data and the pipeline export), the INCOMPLETE status, the new data checks, the opt-out minimum (two opt-outs in 39 first touches do not flag), and four scenarios written into a copy of the blank workbook and counted by hand: (A) edge cases, including a withdrawn office and brand, a lower-case "y", a $600 typed as text and a call at 14:30 on Gate 0 day; (B) Gate 0 day with 6 and 5 conversations, which must read INCOMPLETE, not FAIL; (C) a withdrawal that decides the gate, which must not read PASS, with the withdrawn office's yes left out of the pipeline export; (D) 15 conversations and 4 office yeses, which must read FAIL. Review round 3 added the reviewer's scenario E (two contacts at one office and two founders of one brand: 4 offices INCOMPLETE and 6 brands at Gate 0, not 5 and 7; the pipeline gives each organisation one `org_id`), scenario G (a 12-person office's yes is not counted, a 35-person office's is, and an office whose second call corrected 300 to 240 is in the band), a `company_group` scenario (A's group joins two brand names, a row with no Clay row joins by name, and `org_key` splits two brands that share one), the final read (INCOMPLETE in the Gate 0 column; in the As of column, FAIL from Fri 2026-11-27), and a check that the post-call note template lists the log columns in order. 349 checks. Last run: `_work/partB/test_log.txt`. Separately, `tools/test_h_compat.py` pastes the SAMPLE pipeline export into a temporary copy of the financial model: H's header, text and event checks read 0, and H's Gate 0 counts (13 conversations and 5 yeses for offices, 13 and 6 for brands), Gate 1 counts (5 signed offices, 362 people, 1 brand paid in full) and three medians equal the Scorecard's (`_work/partB/h_compat_log.txt`).

## Changelog

Rounds 1 to 6 are the build rounds of the calls, sending, tracking and handoff files; a round that did not change this file is not listed. "Merge" is the step that joined them with the message files.

- Round 1 (2026-10-24): workbook, scorecard, sync check and pipeline export built by script; 189 checks.
- Round 2 (2026-10-24): qualification checks on Brand_Log, Gate 1 block, copy-slot counts for Part A, duplicate-handoff check; SAMPLE data made to obey the calendar and the week-one email rule; 214 checks.
- Round 3 (2026-10-24): critique as an operations lead: a 45-column row is slow to type and impossible on a phone, so Note_Office and Note_Brand were added (vertical form, one row to paste, round trip tested); the plan's "five of fifteen from your own network" and "shortlist of 8 offices and 6 brands" are now counted; the Clay paste step says how to paste without breaking the formulas; scorecard cells centred vertically after the render showed values sitting below their labels; 229 checks.
- Round 4 (2026-10-24): four coded fields and a scorecard block so every counted slot in Part A's Startup CPG posts comes from the tracker, with a per-person `quote_ok_to_share`; 241 checks.
- Round 5 (2026-10-24): the ten columns operations reads but the handoff tabs lacked were added (F's `trackerdef.py`, read 2026-10-24) and the test now checks F's full list; the financial-model compatibility test was added; 245 checks.
- Merge (2026-10-24): copy-slot counts: the CSV wins and changes the same day; the Friday copy is the check; no reference to a "Part A".
- Review round 1 (2026-10-24): the 20% check now reads the conversation-reply rate (replies that can become a conversation), not every reply, so opt-outs can no longer keep it green; the all-reply rate stays as information; an opt-out rate with its own 5% flag; a test that plants an opt-out-heavy week; the variant table counts conversation replies; the live handoff and pipeline files ship header-only, with the SAMPLE rows in `SAMPLE-` files that the test checks; 276 checks.
- Review round 2 (2026-10-24): a yes counts only while it stands (a later N or maybe, or a brand's later "no budget" or lower number, withdraws it), with a withdrawn row per side, a matching Clay rule and a pipeline export that leaves out a withdrawn office's yes; INCOMPLETE replaces FAIL when fewer than 15 conversations were held, with a default for what to do; data checks for numbers typed as text and call dates with a time, and every cut-off reads a date by its day; the opt-out check needs at least 3 opt-outs; the SAMPLE banner repeats on every printed page and is stamped on every PNG; the SAMPLE data has five signed offices that all approve the paid brand; 315 checks and four scenarios.
- Review round 3 (2026-10-24): one organisation counts once (`org_key` input column, `calc_org`, A's `company_group` read from the Clay paste; every Gate 0 count, median and the pipeline `org_id`); offices outside 30 to 250 on a Tuesday are shown, not counted, and 30 to 39 has its own row; the final read on Fri 2026-11-27 ends INCOMPLETE; two data checks; 349 checks.
