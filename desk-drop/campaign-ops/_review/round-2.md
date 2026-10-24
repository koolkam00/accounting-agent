# Review round 2: workstream F (operations and measurement), `campaign-ops/`

This is an independent, adversarial review, done on Sat 2026-10-24. The reviewer did not build this folder. Nothing outside `campaign-ops/_review/` was written. Every test ran on fresh copies in `_review/r2/desk-drop/`, made with tar. These were plain copies, not symlinks: `campaign-ops` without `_review`, plus the identity, financial-model, outreach and legal-pack folders and `_shared`. REPORT.md is saved by the orchestrator, so its absence is not a finding. The report-back content was judged from README, HANDOFF and `_work/NOTES.md`.

**Counts: 1 blocker, 2 majors, 6 minors.**

The round-1 fixes hold. Every one I re-tested works (table below). The new problems come from my own third SAMPLE campaign, run on the **direct-ship** model with **two brands**. The builder has never replayed that model past T-1: `tools/dryrun_direct.py` stops at the T-1 snapshot, and no test covers it. The campaign included a short carton at one office and one office refusing one brand's carton at the door. This combination is the plan's model "from campaign three", which is H's DRP-004 (Tue 2027-03-23).

## What I ran, and what holds

- **Builder's suite on the copy:** `bash tests/run_all.sh` ended ALL PASS in 4 min 51 s (`_review/r2/run_all-r2.log`).
- **Third SAMPLE campaign, fresh, replayed day by day.** It ran through the builder's own harness on the copy (`_review/r2/work/scenario_r2.py`; log at `_review/r2/desk-drop/campaign-ops/dry-run/r2direct/DRY-RUN-LOG.md`; output at `_review/r2/dryrun-r2direct.out`). The setup:
  - SAMPLE-DRP-004, Tue 2027-03-23, direct-ship, built on top of the builder's zero, standard and exception rows.
  - SAMPLE-CMP-007 is SAMPLE Brightside: founding_lock = Y, 10 offices, $1,200 paid before shipping.
  - SAMPLE-CMP-008 is SAMPLE Tallgrass: a standard renewal at $750 + $750.
  - **Short shipment:** O-003's Brightside carton arrived with 26 of 50 units. The founder topped up 20 on day 3.
  - **Decline at the door:** O-008 refused the Tallgrass carton and took Brightside. Its owner had already posted the link mailed with the kit at T-3, so two employees answered "Didn't see it".
  - Every step was logged the way `sop/SOP.md` says for direct-ship.
  - Result over 48 days: 0 formula errors and 0 disagreements between the sheet and `tracker.py`. **But the CMP-008 report was refused, and two campaigns are left with permanent checks** (R2-01, R2-02).
- **Independent arithmetic from raw scenario rows** (`_review/r2/work/quick_r2.py` and an inline recompute). These all match the tracker:
  - delivered: 491 and 470;
  - topped up: 20 and 6;
  - depleted by day 5: 474 and 460;
  - CMP-007 responses: 66; tried: 48 and 44.
  - **One number does not match: CMP-008 responses read 63 in the tracker, against 61 from the offices that received the product.**
- **QR codes, decoded with zxing-cpp, a second decoder.** Each code was resolved through the Short.io import CSV, the file the founder uploads:
  - my run: 40 of 40, covering 20 tent cards on both faces and 20 PNGs, each reaching the right campaign's form and the right office's card code;
  - the builder's current kits: zero 20/20, standard 58/58, exception 20/20;
  - all 20 Slack-post `-p` links in my run match their office;
  - all 40 import rows carry the right form, card code and utm_medium.
- **Drop-date validator.** I ran `opscal.py check` with these results:
  - **refused (exit 2):** 2026-12-22, 2027-07-06 and 07, 2026-08-25, 2027-08-17, 18, 24 and 25, Mon 2027-01-11, Fri 2027-01-15, Fri 2027-02-12, 2026-12-15 and 16, 2027-06-29 and 30, 2027-12-14 and 15, and the holiday 2026-11-11;
  - **accepted:** 2027-01-12, 2026-12-08 and 09, 2027-08-11, 2027-07-13, 2027-11-23 and 24 (Thanksgiving skipped), and 2027-06-15 (Juneteenth skipped).
  - The sheet's own `drops!date_check`, recalculated in LibreOffice, agrees with `opscal.py` on 16 dates. Every T offset agrees too (`_review/r2/work/test_sheet_dates_r2.py`).
  - Campaign zero's dates match CONTRACTS section 3: ship by Tue 2026-12-22, T-10 Mon 12-28, T-5 Tue 01-05, T+4 Tue 01-19, T+7 Fri 01-22, T+10 Wed 01-27, T+30 Thu 02-11.
- **Exports against H.** The headers of the live exports and all three SAMPLE export folders are byte-identical to `financial-model/handoff-templates/*.csv`.
  - I loaded two sets into a copy of H's workbook and recalculated in LibreOffice (`_review/work/h_load.py`): the builder's `exports/SAMPLE-exception` and my `SAMPLE-r2direct`.
  - Both gave 0 formula errors and 0 failing Checks rows, and H's SHA-256 was unchanged.
  - The builder's R1-02 claim holds: DRP-003 shows depleted 408, 0 campaigns under five per office, and contribution $815.
- **Name.** "Desk Drop" sits in one tracker cell, config!B2, and nowhere else in the 32 tabs. No path in the folder contains it, and no source or template file contains it either.
  - With config!B2 changed alone, `make_route`, `make_kit`, `make_invoice` and `make_messages` each refuse with exit 2 (R1-04 holds).
- **Ladder.** A grep finds conversion, lift, ROI and acquisition only in sentences that forbid them, and no tracker header uses them.
- **Privacy.** No employee field exists beyond the survey answers and the separate sign-up form.
  - The sign-up form's lifecycle is documented and put on the calendar: unticked addresses deleted at T+5, the pass-on once, everything deleted 30 days later, raw answers deleted at 12 months after a freeze.
  - The time-stamp caveat (R1-08) is now stated honestly.
- **Cost.** The system adds $0 a month on top of the Workspace seat: Short.io free, Dropbox Sign free, Wave Starter, Google Forms and Sheets. That is inside $60.
- **Sources I opened myself (2026-10-24):**
  - **short.io/pricing:** Free gives 1,000 links, 50,000 clicks a month and 5 domains, with "link automation 1,000 (API or Bulk create)".
  - **support.google.com/a/users/answer/9303071:** "By default, access is restricted to people inside your organization." The setting is under Settings > Responses.
  - **help.dropbox.com/plans/dropbox-sign-free-plan:** 3 requests every 30 days, a bundle counts as one, and an audit trail is included.
  - **waveapps.com/pricing:** Starter is free with unlimited invoices; cards cost 2.9% + $0.60; Pro is $19.
  - All of these match what F wrote.
- **What I looked at as rendered pages:**
  - the exception report;
  - the courier route sheet, at PDF resolution;
  - the direct-ship tracking sheet, both the builder's and mine;
  - a tent card;
  - the kit checklist;
  - my CMP-007 report;
  - the founding-lock invoice and a credit note.

## Findings

| id | sev | location | what is wrong | evidence (what I ran or opened) | exact fix |
| --- | --- | --- | --- | --- | --- |
| R2-01 | **Blocker** | `tools/formulas.py` lines 330-344 (campaign `survey_responses`, `tried_no_*`, `survey_tried_yes`, `survey_rating_n`/avg, `survey_buy_*`, `comments_total`, `qr_scans`, `post_link_opens`: SUMIFS over **every** approvals row); `tools/tracker.py` lines 342, 368-378 (`tot()` over all offices); `tools/make_report.py` line 156 (passes those totals to D); `tools/build_tracker.py` line 416 (Sheets `report` tab, "Responded") | **Answers from an office that turned the brand away at the door are counted in the brand's survey totals, and the report then cannot be generated.** R1-02 took such offices out of the roster, Gate 2 and depletion, but not out of the survey and link totals. An office's employees can still answer through the post link: in direct-ship the kit and post are mailed at T-3, and in any model the owner may post before declining. Two things follow. **(a)** The "responded" and "did not try" rungs include people who never had the product, so the report, the debrief and H all overstate "responded". **(b)** D's template checks the reasons against its own roster total and refuses, so there is no report at T+7 (Gate 2's "report within seven days" fails) and the founder gets no hint why. The plan names this exception. | My replay, `dry-run/r2direct/DRY-RUN-LOG.md` (Thu 2027-04-01): `make_report.py ... SAMPLE-CMP-008` gives "REFUSED by the report template (exit 2): The "did not try" reasons add up to more than the people who did not try." The report email is then refused ("no report PDF"). From `reports/SAMPLE-CMP-008/report.json`: the roster sums to 61 responses, 44 tried, and the reasons add up to 7+7+5 = 19, more than the 17 who did not try. The tracker reads `survey_responses` 63 and `tried_no_didnt_see` 7; both include O-008's 2 (approvals row `on_drop` N, `survey_responses` 2). My raw recompute gives 61 at the on-drop offices. The export `campaign_actuals.csv` sends 63 to H, and H's DRP-004 shows survey_responses 129. `debriefs/debrief-brand-SAMPLE-CMP-008.md` shows "Responded 63". D's check is at `desk-drop-identity/system/dd-report.js` line 133. | Count every survey and link total only over `on_drop = "Y"`: add `,{a},"Y"` with `a = approvals!on_drop` to each SUMIFS at formulas.py 330-344. Restrict `tot()` and the `qr_scans`/`post_link_opens` sums in tracker.py to `ondrop`. Add a campaign column `responses_turned_away_office` and show it under "Not counted" on `survey_dashboard` and in the report email and trace: "N answers from an office that turned the brand away were not counted". Keep `responses_unmatched_code` meaning "no office". In `make_report.py`, take quotable comments only from on-drop card codes. Add a `test_exception.py` case with answers at a turned-away office, and assert that the report renders and that headline responses equal the roster sum. |
| R2-02 | Major | `tools/formulas.py` lines 390 (`reserve below zero`), 413-414 (short-shipment checks), 481 (`reserve_delta`), campaign `units_received`; `tools/sop_steps.py` lines 44 (`receive_ds`) and 72 (`drop_ds`) and `sop/SOP.md` lines 49 and 58; `tools/export_actuals.py` (`units_received`); `tools/dryrun_direct.py` (stops at T-1) | **The tracker breaks on the third delivery model.** In direct-ship the SOP has you log `received` for the reserve only and `delivered` (office_count) at T. Four things then go wrong. **(1)** From T-5, both campaigns tell you to "reduce units_override evenly (SOP section 4, short shipment)" and "log a short_shipment issue and tell the brand today", though nothing is short. Following that would cut every office to about 5 units and trigger a false "revised ship-date" email to the brand. **(2)** `reserve_on_hand` goes deeply negative, and "reserve below zero" and "units still on hand after T+14" never clear, so the dashboard can never read 0 for a direct-ship drop. **(3)** H's `units_received` is the reserve only, and H's Drop_Actuals shows received 104 against delivered 961. **(4)** A real short carton at one office (26 of 50) raises no check at all. The brief says the system "must work for all three" models. | Snapshot at T-5 (`_review/r2/work/quick_r2.py 2027-03-16`): both campaigns read "received 52 usable units for 515 allocated: reduce units_override evenly ...; received 52 of 567 due: log a short_shipment issue and tell the brand today". At T+1 the reserve reads -439 and -418. At the final state (DRY-RUN-LOG "Final state 2027-04-23") the reserve reads -491 and -470, plus "units still on hand after T+14", and "Campaigns with checks to read 2" stays on the dashboard. H copy (`_review/r2/h-r2direct/`), DRP-004: units_received 104, units_delivered 961. The approvals check for O-003 is empty, although `units_delivered` 26 is below `units_allocated` 50. A workaround test (`quick_r2.py 2027-04-23 recv`) logged one `received` row per office carton beside each `delivered` row: the reserve then reaches 0 and CMP-007 clears, but CMP-008 still reads "received 522 of 567 due", because the refused carton is counted as due. | SOP rows `receive_ds` and `drop_ds`: log one `received` row per office carton (office_id, the office's count, lot and best-by read off a package) as well as the `delivered` row, and the reserve's own `received` row. In the short-shipment checks, compare `units_received` with `units_to_ship` less the allocation of offices with `on_drop = N`. Add an approvals check: "delivered X of Y allocated: short carton; log a short_shipment issue and tell the brand today (top up from reserve)". Export `units_received` as reserve plus office cartons. Extend `dryrun_direct.py` (or add `dryrun.py direct`) to replay a direct-ship drop to T+30 inside `run_all.sh --dry-runs`, with 0 final checks. |
| R2-03 | Major | `tools/make_route.py` lines 196-199 (the "Founder, the same day" block on the direct-ship tracking sheet); `tools/make_messages.py` lines 206, 209-211 (T-3 and T-1 for direct-ship); `sop/SOP.md` section 4 (no direct-ship rows); `tools/make_report.py` (no delivered-source note) | **The direct-ship documents raise questions a stranger cannot answer, and they misstate how the delivered count was made.** The brief's route-sheet test fails for this model's sheet. **(a)** The tracking sheet tells the founder to log "the handed over count, and who counted (founder_count or courier_count). None for an office that declined: its case stays in reserve". In direct-ship the count source is `office_count`, and a refused carton goes back to the brand with the carrier, not into reserve. **(b)** The T-3 email asks for a photo by "you or the courier"; there is no courier. It never says that a kit of tent cards arrives by post and must be put out, or that the owner must count each carton. **(c)** The T-1 text promises the carrier "in your 9 to 11 am window" (the ship-date email asks only for delivery "on Tuesday") and says "If you're out, it goes to the front desk, as we agreed". A carrier knows nothing of that agreement. For O-009 ("desk will not hold food") the sheet gives no instruction. **(d)** SOP section 4 has no row for a refused or short carrier carton. **(e)** The brand report says "DELIVERED 491 · At handoff" and "Delivered: our count at handoff", but every delivered row is the office's own count. | Builder's `dry-run/standard/direct-ship-variant/route/route-SAMPLE-DRP-002.pdf`, page 4 (viewed). My `dry-run/r2direct/route/route-SAMPLE-DRP-004.pdf` (viewed): stop 9 has no carrier rule. `dry-run/r2direct/messages/t3/SAMPLE-O-008.md`: "(you or the courier)", with no kit or count mentioned. `messages/t1/SAMPLE-O-008.md`: "the carrier delivers ... in your 9 to 11 am window ... it goes to the front desk, as we agreed". `messages/ship_release/SAMPLE-CMP-008.md`: "by a service that delivers on Tuesday March 23". `reports/SAMPLE-CMP-007/report.pdf`, rendered and viewed: the Delivered tile reads "At handoff"; all 20 delivered rows have count_source `office_count`. | Write direct-ship branches. The tracking-sheet block should read: "one delivered row per office per brand with the office's count (office_count); a refused carton: outcome declined, no delivered row, nothing to reserve; the carrier returns it to the brand". T-3 for direct-ship: "A small envelope with the cards arrives by [T-1]: put each card in front of its brand. When the cartons come on [T], count each one and text me the number with the placement photo". T-1: drop the window promise ("the carrier delivers during the day") and replace the front-desk line with "the carrier may leave it at your desk or mailroom; please bring it up the same day". For an office whose desk will not hold food, plan a founder visit or use the courier model. Add SOP section 4 rows "Carton refused at the door (direct-ship)" and "Carton short or damaged (direct-ship)". In `make_report.py`, when any delivered row is `office_count` or `packing_list`, add a trace line and a report-email line ("Delivered: counted by the office on arrival"), and ask D for a delivered-source field. |
| R2-04 | Minor | `tools/build_tracker.py` line 257 (dashboard `B27`, "Tabs over 90% full"); `forms/office-intake-form.md` and `forms/brand-qualification-form.md` step 5; runbook step 8 | B27 refers to `office_form!$A:$A` and `brand_form!$A:$A` directly, inside `IFERROR(...,0)`. The setup steps say to **delete** those placeholder tabs and rename Google's new tab to the same name. In Google Sheets, and in Excel, direct references to a deleted sheet turn into #REF! and do not re-bind to a new sheet with that name. B27 then reads 0 for good, so the capacity warning added for R1-13 dies silently at runbook step 8. `office_intake_founder` uses INDIRECT for exactly this reason, so only this cell was missed. This could not be run in Sheets here; it is standard behaviour of both programs. | The B27 formula in the shipped `tracker/campaign-tracker.xlsx` (read with openpyxl). It is the only direct reference to either tab; the other 3,840 use INDIRECT. | Use `COUNTA(INDIRECT("office_form!A:A"))` and `COUNTA(INDIRECT("brand_form!A:A"))` in B27. Or tell the founder to delete all rows of the placeholder and point the form at it, rather than delete the tab. Add a test that deletes and re-creates `office_form` in openpyxl and checks B27 still counts. |
| R2-05 | Minor | `tools/formulas.py` `offices()` (no checks column; `declines` at line 149 is unused) and `campaigns()` checks; `sop/SOP.md` line 128 | Four roster and product rules from the plan or brief are not guarded. **(1)** Category exclusivity: plan, "What brands buy": "no competing product in the same delivery". Nothing flags two campaigns of one category on one drop. **(2)** "Offices that decline twice leave the roster" (SOP section 4). `offices.declines` is computed but feeds no check. It also counts a stop where the office refused one brand and took another (outcome `declined`), so a good office could be pushed out after two single-brand refusals. **(3)** The brief excludes companies inside a coworking space, unless the operator controls the pantry. **(4)** Offices must be inside the cluster. Neither has a field or check. | `grep -i "exclusiv\|cowork\|boundary"` over `tools/`, `sop/`, `forms/` and `spec/` returns nothing. In my run, O-008's partial refusal counts as `declines` 1. | Add campaign check: "another campaign on this drop has category X". Add an offices `checks` column with: "declined at the door twice: take off the roster (SOP section 4)", counting only stops where every brand was refused; and "in coworking / outside the boundary: confirm" from two requested E fields, `in_coworking` and `in_boundary` (B's `companies.csv` already carries them). List the two fields in HANDOFF "Fields F needs". |
| R2-06 | Minor | `tools/make_debrief.py`; `templates/debrief-brand.md` line 6 | The brand debrief sheet says "The numbers they have in front of them (from the report, <date>)" even when no report PDF exists. Round 1 (A1, item 4) fixed this for the report email only. | `dry-run/r2direct/debriefs/debrief-brand-SAMPLE-CMP-008.md` reads "from the report, Thu 2027-04-01", but the CMP-008 report was refused and no PDF exists (R2-01). | In `make_debrief.py`, check `reports/<cid>/report.pdf`, as `make_messages.py report --reports` does. Without it, write "NO REPORT YET: run make_report.py first" at the top of the brand sheet. |
| R2-07 | Minor | The report PDF (D's template), filled by `tools/make_report.py` | For a 10-office contract where one office declined, the brand's one-page report says "Standard, 9 offices" with no explanation on the page. The roster note lives only in `trace.csv`, the report email and the debrief. The PDF is the document a brand forwards and keeps, and a finance reader will ask where the tenth office went. HANDOFF "To D" offers D a field, but nothing is on the page today. | `dry-run/exception/reports/SAMPLE-CMP-006/report.pdf`, rendered and viewed. | Until D adds a roster-note field, have `make_report.py` prepend the roster note to the `learned` field passed to D (first bullet), or refuse `--final` without it. Ask D to add the field, as HANDOFF suggests. |
| R2-08 | Minor | `README.md` line 184 ("If a tool fails", route sheet) | The no-code fallback for the route sheet lists only `stops` columns. `delivery_point_note` ("4th floor kitchen, left of the coffee machine") lives on `offices`, so the printed fallback loses where to go in the building. `units_here` is the total for all brands, not per brand, so a multi-brand stop has no per-case count. | I read the `stops` tab columns in `tools/trackerdef.py`; `delivery_point_note` is on `offices` only. | Add a grey `delivery_point_note` lookup column to `stops`, and list it in the README fallback. Tell the founder to print the `kit-checklist` rows or the `approvals` tab, filtered to the drop, for per-brand units. |
| R2-09 | Minor | `tools/make_messages.py` line 215 (day-3 nudge) | Grammar: "Also: SAMPLE Brightside and SAMPLE Tallgrass has under five survey answers" should read "have" when more than one brand is listed. | `dry-run/r2direct/messages/day3/SAMPLE-O-010.md`. | Use "have" when the list has more than one brand. |

## Round-1 fixes, checked again (not taken on trust)

| R1 | Claimed | What I found |
| --- | --- | --- |
| R1-01 forms closed to outsiders | fixed | Holds. "Restrict to users ... OFF" appears in survey Parts 1 and 3, both intake pages, the D1 row and runbook steps 8 and 9, with a signed-out test. `build-forms.gs` line 40 has `setRequireLogin(false)` in a try. I opened Google's page myself and its quote matches. |
| R1-02 decline at the door | fixed | Holds for a single-brand drop. In the builder's exception run there are no day-3 or day-5 drafts for O-006, it gets the follow-up template, the report email carries the roster note, and H shows DRP-003 depleted 408 with 0 under five. My partial decline also worked: O-008 refused Tallgrass only, so it gets no Tallgrass letter or asks, and the placement confirmation reads 9 of 10 with a $150 credit. **The fix missed the survey and link totals** (R2-01). |
| R1-03 SOP correction row | fixed | Holds (SOP line 128). The exception run's reserve reaches 0. |
| R1-04 rename | fixed | Holds. Four tools refuse with exit 2 when only config!B2 is changed. |
| R1-05 route sheet | fixed | Holds for the courier sheet (rendered, viewed): certificate source, handed-over count, cases taken back. It does not hold for the direct-ship sheet (R2-03). |
| R1-06 payments counted once | fixed | Holds. `--pipeline` refuses. `test_e_handoff` gives 1 / 0 / 1. E's real headers carry every column F reads, including payment_1/2. |
| R1-07 qualification and billing | fixed | Holds. My founding-lock invoice bills the legal name; `ship_release` holds on "qualification". |
| R1-08 time-stamp caveat | fixed | Holds (survey Part 3 and "For the attorney hour"). |
| R1-09 short shipment at receipt | fixed | Holds for founder and courier. It fires falsely in direct-ship (R2-02). |
| R1-10 SAMPLE banner on text drafts | fixed | Holds. Every draft in my run starts with the banner line. |
| R1-11 top-ups in office summaries | fixed | Holds. |
| R1-12 12-month deletion | fixed | Holds. `test_retention` passes (34, 34, 0). |
| R1-13 size | fixed | Holds: 52,615 formula cells, 6,740 INDIRECT, 32 tabs (counted). But the new "tabs over 90%" line dies at forms setup (R2-04). |
| R1-14 founding limits | fixed | Holds. My founding_lock = Y second campaign priced at $1,200 with no false check. |
| R1-15 link domain neutral | fixed | Holds. E's sending-setup section 0 says "never 'deskdrop'". |
| R1-16 threshold 5 | fixed | Holds (config `office_summary_min_answers` 5). |
| R1-17 no-code fallback | fixed | Present. The route-sheet path is thin (R2-08). |

## Reviewed as the four people in the brief

- **Manhattan sampling operations lead, reading the sheets cold.**
  - The courier route sheet is now complete: windows, owner phones, the certificate source, a handed-over count, and where taken-back cases go.
  - The direct-ship tracking sheet is not. Its closing block is the courier's, and it says nothing about a carton the office refuses or a desk that will not hold food (R2-03).
  - The no-code fallback drops the in-building directions (R2-08).
- **Brand finance lead hunting overstatement.**
  - Money is clean. The founding-lock invoice is $1,200 by bank transfer. A credit note settles against the balance invoice ($600 instead of $750). Revenue is net of credit notes and matches H.
  - Two measurement problems:
    - the "responded" rung counts answers from an office that refused the product (63 against 61; R2-01);
    - the report says delivered counts were "our count at handoff" when the offices counted (R2-03(e)).
  - H also receives `units_received` 52 against 491 delivered for direct-ship (R2-02).
  - A 10-office contract reports "9 offices" with no note on the page (R2-07).
- **Privacy reviewer hunting data that should not exist.**
  - Nothing new found. No employee field exists beyond anonymous answers and the separate sign-up form.
  - The lifecycle is documented and calendared.
  - Office summaries suppress splits under five answers and strip likely names.
  - The T-1 text asks for no one's name.
  - Short.io is named as a processor that sees click details, and only totals are kept.
- **Pantry owner weighing every ask.**
  - The founder and courier asks match the agreement, and a turned-away office now gets a short follow-up rather than "how did it land".
  - In direct-ship the office silently takes on new work: counting each carton, putting out cards that arrive by post, and taking the placement photo. None of it is stated in the T-3 email, and the T-1 text promises a delivery window no carrier keeps (R2-03).
  - Refusing one brand counts toward "two declines and you leave" (R2-05).

## Brief tests, pass or fail

| Test | Result |
| --- | --- |
| Report generates with no retyping; every number traces to a logged row or photo | **Fail** for a brand turned away at the door by an office whose people answered the survey: no report (R2-01). Pass otherwise: CMP-007 and the builder's three runs generate, `trace.csv` covers every figure, and my raw recompute matches. |
| Every QR decodes to the right survey for the right office | **Pass.** 40 of 40 in my run and 98 of 98 in the builder's, decoded independently. |
| SOP validator rejects Mondays, Fridays and blackouts; T offsets per CONTRACTS section 3 | **Pass**, in Python and in the sheet. |
| Ladder rungs separate, no conversions or lift field | **Pass** for the words. The "responded" rung is contaminated by off-drop answers (R2-01). |
| Only employee data is the optional consented email, lifecycle documented | **Pass.** |
| Exports match H exactly and load without errors (LibreOffice recalculation) | **Pass** on headers and load: 0 errors and 0 failing checks, for two sets. Values are wrong for direct-ship `units_received` (R2-02) and off-drop responses (R2-01). |
| Company name in one config cell, in no file, folder or link name | **Pass.** |
| Tools free or near-free, inside $60 a month | **Pass:** $0 on top of Workspace. |
| Route sheet raises no questions for a stranger | Pass for founder and courier. **Fail** for the direct-ship tracking sheet (R2-03). |
| Works for all three delivery models (brief, Facts) | **Fail** for direct-ship past T-1 (R2-02, R2-03). |

Would a demanding operations and measurement lead sign it as it stands? For campaign zero (founder) and the courier runs, yes once R2-01 is fixed. For direct-ship, not until R2-02 and R2-03 are fixed and a direct-ship drop replays to T+30 with 0 final checks.

## Files from this review

- `_review/round-2.md` (this file) and `_review/notes-round-2.md` (working notes)
- `_review/r2/run_all-r2.log` (builder suite on the copy) and `_review/r2/dryrun-r2direct.out` (replay output)
- `_review/r2/work/scenario_r2.py` (the third SAMPLE campaign), `quick_r2.py` (one-day snapshots, plus the `recv` workaround variant), `test_sheet_dates_r2.py`, `snap/` (snapshots), `rename-*`
- `_review/r2/desk-drop/campaign-ops/dry-run/r2direct/` (full replay: log, kit, links, tracking sheet, messages, invoices, reports, debriefs, exports, SOP calendar) and `exports/SAMPLE-r2direct/`
- `_review/r2/h-r2direct/` and `_review/r2/h-exception-builder/` (H workbook copies, recalculated)
- `_review/r2/png/` (every page I looked at)
- `_review/r2/` is about 154 MB, almost all of it sandbox copies. Leave it out of the commit, as with round 1's sandbox.
