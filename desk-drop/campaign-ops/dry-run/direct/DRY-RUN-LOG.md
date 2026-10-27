SAMPLE. Test data only: illustrative placeholders, not results. Never send or print for use.

# Dry run: direct

SAMPLE data only. Drop SAMPLE-DRP-004 on 2027-03-23, direct-ship model, campaigns SAMPLE-CMP-007, SAMPLE-CMP-008.
Each day: the tracker is rebuilt with only the rows logged by that day, recalculated (LibreOffice), and read back; the sheet's formulas are compared with tools/tracker.py; then that day's tools run.

## Fri 2027-01-22 
- Logged today: inventory +3, scans +20, redemptions +2, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-01-25 
- Logged today: brands +1, campaigns +1, invoices +1, approvals +10, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Office rows with checks 10
    - approvals row 42 (SAMPLE-CMP-006 SAMPLE-O-001): approval pending;
    - approvals row 43 (SAMPLE-CMP-006 SAMPLE-O-002): approval pending;
    - approvals row 44 (SAMPLE-CMP-006 SAMPLE-O-003): approval pending;
    - approvals row 45 (SAMPLE-CMP-006 SAMPLE-O-004): approval pending;
    - approvals row 46 (SAMPLE-CMP-006 SAMPLE-O-005): approval pending;
    - approvals row 47 (SAMPLE-CMP-006 SAMPLE-O-006): approval pending;
    - approvals row 48 (SAMPLE-CMP-006 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 49 (SAMPLE-CMP-006 SAMPLE-O-008): approval pending;
    - approvals row 50 (SAMPLE-CMP-006 SAMPLE-O-009): approval pending;
    - approvals row 51 (SAMPLE-CMP-006 SAMPLE-O-010): approval pending;
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-020 dry-run/direct/invoices  ->  invoice SAMPLE-INV-020 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-020.pdf

## Tue 2027-01-26 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Office rows with checks 10; Invoices overdue 1
    - approvals row 42 (SAMPLE-CMP-006 SAMPLE-O-001): approval pending;
    - approvals row 43 (SAMPLE-CMP-006 SAMPLE-O-002): approval pending;
    - approvals row 44 (SAMPLE-CMP-006 SAMPLE-O-003): approval pending;
    - approvals row 45 (SAMPLE-CMP-006 SAMPLE-O-004): approval pending;
    - approvals row 46 (SAMPLE-CMP-006 SAMPLE-O-005): approval pending;
    - approvals row 47 (SAMPLE-CMP-006 SAMPLE-O-006): approval pending;
    - approvals row 48 (SAMPLE-CMP-006 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 49 (SAMPLE-CMP-006 SAMPLE-O-008): approval pending;
    - approvals row 50 (SAMPLE-CMP-006 SAMPLE-O-009): approval pending;
    - approvals row 51 (SAMPLE-CMP-006 SAMPLE-O-010): approval pending;

## Wed 2027-01-27 
- Logged today: hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Invoices overdue 1

## Thu 2027-01-28 
- Logged today: inventory +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-01-29 
- Logged today: inventory +1, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-02-01 
- Logged today: inventory +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-02-03 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-02-04 
- Logged today: stops +10, costs +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-02-08 
- Logged today: scans +58, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-02-09 
- Logged today: inventory +26, counts +23, photos +23, issues +1, hours +1, costs +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Office rows with checks 3
    - approvals row 15 (SAMPLE-CMP-003 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 25 (SAMPLE-CMP-004 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 35 (SAMPLE-CMP-005 SAMPLE-O-004): no usable placement photo yet;

## Wed 2027-02-10 
- Logged today: invoices +4, inventory +3, counts +6, photos +6, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-005 dry-run/direct/invoices  ->  invoice SAMPLE-INV-005 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-005.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-007 dry-run/direct/invoices  ->  invoice SAMPLE-INV-007 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-007.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-008 dry-run/direct/invoices  ->  invoice SAMPLE-INV-008 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-008.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-010 dry-run/direct/invoices  ->  invoice SAMPLE-INV-010 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-010.pdf

## Thu 2027-02-11 
- Logged today: inventory +3, counts +29, scans +58, redemptions +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 3

## Fri 2027-02-12 
- Logged today: inventory +1, redemptions +1, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 2

## Tue 2027-02-16 
- Logged today: inventory +11, counts +29, photos +29, scans +58, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 1

## Wed 2027-02-17 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-02-18 
- Logged today: stops +10, costs +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-02-19 
- Logged today: inventory +2, redemptions +3, hours +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-02-22 
- Logged today: drops +1, scans +20, hours +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-02-23 
- Logged today: inventory +9, counts +9, photos +9, issues +1, hours +1, costs +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-02-24 
- Logged today: campaigns +2, invoices +4, approvals +20, hours +4
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 10
    - approvals row 57 (SAMPLE-CMP-007 SAMPLE-O-006): approval pending;
    - approvals row 58 (SAMPLE-CMP-007 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 59 (SAMPLE-CMP-007 SAMPLE-O-008): approval pending;
    - approvals row 60 (SAMPLE-CMP-007 SAMPLE-O-009): approval pending;
    - approvals row 61 (SAMPLE-CMP-007 SAMPLE-O-010): approval pending;
    - approvals row 67 (SAMPLE-CMP-008 SAMPLE-O-006): approval pending;
    - approvals row 68 (SAMPLE-CMP-008 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 69 (SAMPLE-CMP-008 SAMPLE-O-008): approval pending;
    - approvals row 70 (SAMPLE-CMP-008 SAMPLE-O-009): approval pending;
    - approvals row 71 (SAMPLE-CMP-008 SAMPLE-O-010): approval pending;
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-021 dry-run/direct/invoices  ->  invoice SAMPLE-INV-021 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-021.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-022 dry-run/direct/invoices  ->  invoice SAMPLE-INV-022 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-022.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-030 dry-run/direct/invoices  ->  invoice SAMPLE-INV-030 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-030.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-031 dry-run/direct/invoices  ->  invoice SAMPLE-INV-031 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-031.pdf

## Thu 2027-02-25 
- Logged today: inventory +2, counts +9, scans +20, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Invoices overdue 2

## Fri 2027-02-26 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1
- SAMPLE-CMP-008 ship release: RELEASED 2027-02-26: ship by Tue 2027-03-09 (latest Tue 2027-03-09)
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 ship_release dry-run/direct/messages  ->  ship_release: 1 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/ship_release

## Mon 2027-03-01 
- Logged today: inventory +1, counts +9, photos +9, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- SAMPLE-CMP-007 ship release: RELEASED 2027-03-01: ship by Tue 2027-03-09 (latest Tue 2027-03-09)
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 ship_release dry-run/direct/messages  ->  ship_release: 1 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/ship_release

## Tue 2027-03-02  · yes, approvals_ask, building_coi
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-03-03 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-03-04 
- Logged today: redemptions +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-03-09  · paid, coi_check, release, direct_plan, ship
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-03-11 
- Logged today: redemptions +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-03-16  · receive_ds, card_proof
- Logged today: inventory +4, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-03-17  · forms
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_links.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 dry-run/direct/links  ->  links: 40 (20 QR) -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/links

## Thu 2027-03-18  · kit_print, kit_mail
- Logged today: stops +10, hours +1, costs +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_kit.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 dry-run/direct/kit  ->  kit SAMPLE-DRP-004: 20 cards, 22 labels, 10 posts, QR all match
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 t3 dry-run/direct/messages  ->  t3: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/t3

## Fri 2027-03-19  · tracking
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-03-22  · confirm
- Logged today: scans +40
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_route.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 dry-run/direct/route  ->  route SAMPLE-DRP-004 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/route/route-SAMPLE-DRP-004.html ok
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 t1 dry-run/direct/messages  ->  t1: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/t1

## Tue 2027-03-23 T · drop_ds
- Logged today: inventory +36, counts +19, photos +19, issues +2, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-03-24  · placement_confirm
- Logged today: invoices +2, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-032 dry-run/direct/invoices  ->  invoice SAMPLE-INV-032 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-032.pdf
    $ python3 tools/make_invoice.py _work/dryrun-direct/day.xlsx SAMPLE-INV-033 dry-run/direct/invoices  ->  invoice SAMPLE-INV-033 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/invoices/SAMPLE-INV-033.pdf
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 placement_confirmation dry-run/direct/messages  ->  placement_confirmation: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/placement_confirmation

## Thu 2027-03-25  · day3
- Logged today: inventory +2, counts +19, scans +40, redemptions +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 1
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 day3 dry-run/direct/messages  ->  day3: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/day3

## Mon 2027-03-29  · close
- Logged today: inventory +2, counts +19, photos +19, scans +40, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 day5 dry-run/direct/messages  ->  day5: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/day5

## Tue 2027-03-30  · pass_on
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 newsletter dry-run/direct/messages  ->  newsletter: 0 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/newsletter

## Wed 2027-03-31  · report_draft
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-04-01  · report
- Logged today: redemptions +2, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_report.py _work/dryrun-direct/day.xlsx SAMPLE-CMP-007 dry-run/direct/reports --photos dry-run/direct/photos  ->  report SAMPLE-CMP-007 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/reports/SAMPLE-CMP-007/report.pdf (sample=True)
    $ python3 tools/make_report.py _work/dryrun-direct/day.xlsx SAMPLE-CMP-008 dry-run/direct/reports --photos dry-run/direct/photos  ->  report SAMPLE-CMP-008 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/reports/SAMPLE-CMP-008/report.pdf (sample=True)
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 report dry-run/direct/messages --reports dry-run/direct/reports  ->  report: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/report

## Mon 2027-04-05  · office_debrief
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 dry-run/direct/debriefs  ->  debrief notes: 12 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/debriefs

## Tue 2027-04-06  · debrief
- Logged today: hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 dry-run/direct/debriefs  ->  debrief notes: 12 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/debriefs
    $ python3 tools/export_actuals.py _work/dryrun-direct/day.xlsx dry-run/direct/exports/at-2027-04-06  ->  exports: 8 campaigns, 4 drops, 93 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/exports/at-2027-04-06

## Mon 2027-04-12  · return_deadline
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-04-22  · redemption
- Logged today: redemptions +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-direct/day.xlsx SAMPLE-DRP-004 redemption dry-run/direct/messages  ->  redemption: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/messages/redemption
    $ python3 tools/export_actuals.py _work/dryrun-direct/day.xlsx dry-run/direct/exports/at-2027-04-22  ->  exports: 8 campaigns, 4 drops, 93 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/exports/at-2027-04-22

## Thu 2027-04-29  · newsletter_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-05-06  · testimonial
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2028-03-28  · answers_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Final state 2027-04-23
- Sheet: 0 formula errors; 0 disagreements.
- Dashboard checks to fix at the final state: none
    $ python3 tools/export_actuals.py dry-run/direct/SAMPLE-tracker-direct-final.xlsx dry-run/direct/exports  ->  exports: 8 campaigns, 4 drops, 93 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/exports
    $ python3 tools/export_actuals.py dry-run/direct/SAMPLE-tracker-direct-final.xlsx exports/SAMPLE-direct  ->  exports: 8 campaigns, 4 drops, 93 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/exports/SAMPLE-direct
    $ python3 tools/dump_forms.py dry-run/direct/SAMPLE-tracker-direct-final.xlsx direct dry-run/direct/forms  ->  forms: office_intake-website.csv 6, office_form-google.csv 4, office_intake_founder.csv 4, brand_intake-website.csv 5, brand_form-google.csv 1, brand_intake_founder.csv 1, survey-SAMPLE-CMP-001.csv 37, survey-SAMPLE-CMP-002.csv 32, survey-SAMPLE-CMP-003.csv 76, survey-SAMPLE-CMP-004.csv 71, survey-SAMPLE-CMP-005.csv 77, survey-SAMPLE-CMP-006.csv 62, survey-SAMPLE-CMP-007.csv 66, survey-SAMPLE-CMP-008.csv 63, SAMPLE-newsletter-signup-SAMPLE-CMP-001.csv 10, SAMPLE-newsletter-pass-on-SAMPLE-CMP-001.txt 7, SAMPLE-newsletter-signup-SAMPLE-CMP-004.csv 7, SAMPLE-newsletter-pass-on-SAMPLE-CMP-004.txt 4 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/forms
    $ python3 tools/make_calendar.py dry-run/direct/SAMPLE-tracker-direct-final.xlsx SAMPLE-DRP-004 dry-run/direct/sop  ->  sop SAMPLE-DRP-004 2027-03-23 direct-ship: 29 steps -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/direct/sop/sop-SAMPLE-DRP-004.html
- Tools that refused or failed during the replay: none
- Problems in total (formula errors + disagreements + tool refusals + final dashboard checks): 0
