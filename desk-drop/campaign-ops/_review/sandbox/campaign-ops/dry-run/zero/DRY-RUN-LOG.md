# Dry run: zero

SAMPLE data only. Drop SAMPLE-DRP-001 on 2027-01-12, founder model, campaigns SAMPLE-CMP-001, SAMPLE-CMP-002.
Each day: the tracker is rebuilt with only the rows logged by that day, recalculated (LibreOffice), and read back; the sheet's formulas are compared with tools/tracker.py; then that day's tools run.

## Mon 2026-11-16 
- Logged today: in_signed_offices +1, offices +1, drops +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2026-11-17 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-11-18 
- Logged today: office_intake +1, in_signed_offices +1, offices +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2026-11-19 
- Logged today: brand_form +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2026-11-24 
- Logged today: in_signed_offices +1, offices +1, brands +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-11-25 
- Logged today: office_form +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2026-11-27 
- Logged today: office_intake +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2026-12-01 
- Logged today: in_signed_offices +1, offices +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-12-02 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2026-12-03 
- Logged today: in_signed_offices +1, offices +1, brands +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2026-12-04 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2026-12-07 
- Logged today: campaigns +1, invoices +1, hours +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1
    $ python3 tools/make_invoice.py _work/dryrun-zero/day.xlsx SAMPLE-INV-001 dry-run/zero/invoices  ->  invoice SAMPLE-INV-001 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/invoices/SAMPLE-INV-001.pdf

## Tue 2026-12-08 
- Logged today: campaigns +1, invoices +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2
    $ python3 tools/make_invoice.py _work/dryrun-zero/day.xlsx SAMPLE-INV-002 dry-run/zero/invoices  ->  invoice SAMPLE-INV-002 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/invoices/SAMPLE-INV-002.pdf

## Thu 2026-12-10 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2

## Fri 2026-12-11 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2

## Mon 2026-12-14 
- Logged today: approvals +10
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 10
    - approvals row 2 (SAMPLE-CMP-001 SAMPLE-O-001): approval pending;
    - approvals row 3 (SAMPLE-CMP-001 SAMPLE-O-002): approval pending;
    - approvals row 4 (SAMPLE-CMP-001 SAMPLE-O-003): approval pending;
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): approval pending;
    - approvals row 6 (SAMPLE-CMP-001 SAMPLE-O-005): approval pending;
    - approvals row 7 (SAMPLE-CMP-002 SAMPLE-O-001): approval pending;
    - approvals row 8 (SAMPLE-CMP-002 SAMPLE-O-002): approval pending;
    - approvals row 9 (SAMPLE-CMP-002 SAMPLE-O-003): approval pending;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): approval pending;
    - approvals row 11 (SAMPLE-CMP-002 SAMPLE-O-005): approval pending;
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 approvals dry-run/zero/messages  ->  approvals: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/approvals

## Tue 2026-12-15  · yes, approvals_ask
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 10
    - approvals row 2 (SAMPLE-CMP-001 SAMPLE-O-001): approval pending;
    - approvals row 3 (SAMPLE-CMP-001 SAMPLE-O-002): approval pending;
    - approvals row 4 (SAMPLE-CMP-001 SAMPLE-O-003): approval pending;
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): approval pending;
    - approvals row 6 (SAMPLE-CMP-001 SAMPLE-O-005): approval pending;
    - approvals row 7 (SAMPLE-CMP-002 SAMPLE-O-001): approval pending;
    - approvals row 8 (SAMPLE-CMP-002 SAMPLE-O-002): approval pending;
    - approvals row 9 (SAMPLE-CMP-002 SAMPLE-O-003): approval pending;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): approval pending;
    - approvals row 11 (SAMPLE-CMP-002 SAMPLE-O-005): approval pending;

## Wed 2026-12-16 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 2
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): approval pending;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): approval pending;

## Fri 2026-12-18  · building_coi
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- SAMPLE-CMP-001 ship release: RELEASED 2026-12-18: ship by Tue 2026-12-22 (latest Mon 2026-12-28)
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 ship_release dry-run/zero/messages  ->  ship_release: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/ship_release
- SAMPLE-CMP-002 ship release: RELEASED 2026-12-18: ship by Tue 2026-12-22 (latest Mon 2026-12-28)
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 ship_release dry-run/zero/messages  ->  ship_release: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/ship_release

## Tue 2026-12-22  · paid, coi_check, release
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2026-12-28  · ship
- Logged today: inventory +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-12-30 
- Logged today: inventory +4, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-01-05  · receive, card_proof
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-01-06  · forms
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_links.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 dry-run/zero/links  ->  links: 20 (10 QR) -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/links

## Thu 2027-01-07  · kit_print
- Logged today: stops +5, costs +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_kit.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 dry-run/zero/kit  ->  kit SAMPLE-DRP-001: 10 cards, 20 labels, 5 posts, QR all match
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 t3 dry-run/zero/messages  ->  t3: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/t3

## Mon 2027-01-11  · confirm
- Logged today: scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_route.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 dry-run/zero/route  ->  route SAMPLE-DRP-001 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/route/route-SAMPLE-DRP-001.html ok
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 t1 dry-run/zero/messages  ->  t1: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/t1

## Tue 2027-01-12 T · drop
- Logged today: inventory +10, counts +8, photos +8, issues +1, hours +1, costs +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Office rows with checks 2
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): no usable placement photo yet;
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 on_my_way dry-run/zero/messages  ->  on_my_way: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/on_my_way

## Wed 2027-01-13  · placement_confirm
- Logged today: invoices +1, counts +1, photos +1, issues +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Office rows with checks 1
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): no usable placement photo yet;
    $ python3 tools/make_invoice.py _work/dryrun-zero/day.xlsx SAMPLE-INV-003 dry-run/zero/invoices  ->  invoice SAMPLE-INV-003 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/invoices/SAMPLE-INV-003.pdf
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 placement_confirmation dry-run/zero/messages  ->  placement_confirmation: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/placement_confirmation

## Thu 2027-01-14  · day3
- Logged today: inventory +2, counts +11, photos +2, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 day3 dry-run/zero/messages  ->  day3: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/day3

## Fri 2027-01-15 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-01-19  · close
- Logged today: inventory +7, counts +10, photos +9, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 day5 dry-run/zero/messages  ->  day5: 5 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/day5

## Wed 2027-01-20  · pass_on
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 newsletter dry-run/zero/messages  ->  newsletter: 1 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/newsletter

## Thu 2027-01-21  · report_draft
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-01-22  · report
- Logged today: inventory +3, scans +20, redemptions +2, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_report.py _work/dryrun-zero/day.xlsx SAMPLE-CMP-001 dry-run/zero/reports --photos dry-run/zero/photos  ->  report SAMPLE-CMP-001 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/reports/SAMPLE-CMP-001/report.pdf (sample=True)
    $ python3 tools/make_report.py _work/dryrun-zero/day.xlsx SAMPLE-CMP-002 dry-run/zero/reports --photos dry-run/zero/photos  ->  report SAMPLE-CMP-002 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/reports/SAMPLE-CMP-002/report.pdf (sample=True)
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 report dry-run/zero/messages  ->  report: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/report

## Mon 2027-01-25 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-01-26  · office_debrief
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 dry-run/zero/debriefs  ->  debrief notes: 7 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/debriefs

## Wed 2027-01-27  · debrief
- Logged today: hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 dry-run/zero/debriefs  ->  debrief notes: 7 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/debriefs
    $ python3 tools/export_actuals.py _work/dryrun-zero/day.xlsx dry-run/zero/exports/at-2027-01-27 --pipeline  ->  exports: 2 campaigns, 1 drops, 37 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/exports/at-2027-01-27

## Mon 2027-02-01 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-02-02  · return_deadline
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-02-11  · redemption
- Logged today: redemptions +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-zero/day.xlsx SAMPLE-DRP-001 redemption dry-run/zero/messages  ->  redemption: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/messages/redemption
    $ python3 tools/export_actuals.py _work/dryrun-zero/day.xlsx dry-run/zero/exports/at-2027-02-11 --pipeline  ->  exports: 2 campaigns, 1 drops, 37 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/exports/at-2027-02-11

## Fri 2027-02-12 
- Logged today: redemptions +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-02-19  · newsletter_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-02-26  · testimonial
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2028-01-19  · answers_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Final state 2027-02-20
- Sheet: 0 formula errors; 0 disagreements.
    $ python3 tools/export_actuals.py dry-run/zero/SAMPLE-tracker-zero-final.xlsx dry-run/zero/exports --pipeline  ->  exports: 2 campaigns, 1 drops, 37 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/exports
    $ python3 tools/export_actuals.py dry-run/zero/SAMPLE-tracker-zero-final.xlsx exports/SAMPLE-zero --pipeline  ->  exports: 2 campaigns, 1 drops, 37 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/exports/SAMPLE-zero
    $ python3 tools/dump_forms.py dry-run/zero/SAMPLE-tracker-zero-final.xlsx zero dry-run/zero/forms  ->  forms: office_intake-website.csv 3, office_form-google.csv 2, office_intake_founder.csv 2, brand_intake-website.csv 1, brand_form-google.csv 1, brand_intake_founder.csv 1, survey-SAMPLE-CMP-001.csv 37, survey-SAMPLE-CMP-002.csv 32, SAMPLE-newsletter-signup-SAMPLE-CMP-001.csv 10, SAMPLE-newsletter-pass-on-SAMPLE-CMP-001.txt 7 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/forms
    $ python3 tools/make_calendar.py dry-run/zero/SAMPLE-tracker-zero-final.xlsx SAMPLE-DRP-001 dry-run/zero/sop  ->  sop SAMPLE-DRP-001 2027-01-12 founder: 26 steps -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/zero/sop/sop-SAMPLE-DRP-001.html

## Regenerated after the replay (same snapshots, final tools)
- Route sheet from `SAMPLE-tracker-zero-2027-01-11.xlsx` (T-1): adds the "about 20 minutes out" rule at every door.
- Both reports and the five office summaries from `SAMPLE-tracker-zero-2027-01-22.xlsx` (T+7): office summaries now show no rating or would-buy split drawn from fewer than three people.
