# Dry run: standard

SAMPLE data only. Drop SAMPLE-DRP-002 on 2027-02-09, courier model, campaigns SAMPLE-CMP-003, SAMPLE-CMP-004, SAMPLE-CMP-005.
Each day: the tracker is rebuilt with only the rows logged by that day, recalculated (LibreOffice), and read back; the sheet's formulas are compared with tools/tracker.py; then that day's tools run.

## Fri 2026-12-11 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2

## Mon 2026-12-14 
- Logged today: drops +1, approvals +10
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
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 approvals dry-run/standard/messages  ->  approvals: 0 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/approvals

## Tue 2026-12-15 
- Logged today: brand_intake +1
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

## Thu 2026-12-17 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 2
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): approval pending;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): approval pending;

## Fri 2026-12-18 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- SAMPLE-CMP-001 ship release: RELEASED 2026-12-18: ship by Tue 2026-12-22 (latest Mon 2026-12-28)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 0 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release
- SAMPLE-CMP-002 ship release: RELEASED 2026-12-18: ship by Tue 2026-12-22 (latest Mon 2026-12-28)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 0 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release

## Mon 2026-12-21 
- Logged today: brand_intake +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-12-23 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2026-12-24 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2026-12-28 
- Logged today: brand_intake +1, inventory +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2026-12-29 
- Logged today: brands +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2026-12-30 
- Logged today: office_intake +1, inventory +4, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2026-12-31 
- Logged today: office_intake +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-01-01 
- Logged today: office_form +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Sat 2027-01-02 
- Logged today: office_intake +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-01-04 
- Logged today: brands +1, campaigns +1, invoices +1, approvals +5, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Office rows with checks 5
    - approvals row 12 (SAMPLE-CMP-003 SAMPLE-O-001): approval pending;
    - approvals row 13 (SAMPLE-CMP-003 SAMPLE-O-002): approval pending;
    - approvals row 14 (SAMPLE-CMP-003 SAMPLE-O-003): approval pending;
    - approvals row 15 (SAMPLE-CMP-003 SAMPLE-O-004): approval pending;
    - approvals row 16 (SAMPLE-CMP-003 SAMPLE-O-005): approval pending;
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-004 dry-run/standard/invoices  ->  invoice SAMPLE-INV-004 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-004.pdf

## Tue 2027-01-05 
- Logged today: in_signed_offices +1, offices +1, approvals +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Office rows with checks 4; Invoices overdue 1
    - approvals row 13 (SAMPLE-CMP-003 SAMPLE-O-002): approval pending;
    - approvals row 14 (SAMPLE-CMP-003 SAMPLE-O-003): approval pending;
    - approvals row 16 (SAMPLE-CMP-003 SAMPLE-O-005): approval pending;
    - approvals row 17 (SAMPLE-CMP-003 SAMPLE-O-006): approval pending;

## Wed 2027-01-06 
- Logged today: in_signed_offices +1, offices +1, campaigns +1, invoices +1, approvals +8, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 10; Invoices overdue 1
    - approvals row 14 (SAMPLE-CMP-003 SAMPLE-O-003): approval pending;
    - approvals row 17 (SAMPLE-CMP-003 SAMPLE-O-006): approval pending;
    - approvals row 18 (SAMPLE-CMP-003 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 19 (SAMPLE-CMP-004 SAMPLE-O-001): approval pending;
    - approvals row 20 (SAMPLE-CMP-004 SAMPLE-O-002): approval pending;
    - approvals row 21 (SAMPLE-CMP-004 SAMPLE-O-003): approval pending;
    - approvals row 22 (SAMPLE-CMP-004 SAMPLE-O-004): approval pending;
    - approvals row 23 (SAMPLE-CMP-004 SAMPLE-O-005): approval pending;
    - approvals row 24 (SAMPLE-CMP-004 SAMPLE-O-006): approval pending;
    - approvals row 25 (SAMPLE-CMP-004 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-006 dry-run/standard/invoices  ->  invoice SAMPLE-INV-006 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-006.pdf

## Thu 2027-01-07 
- Logged today: office_form +1, in_signed_offices +1, offices +1, approvals +2, stops +5, hours +1, costs +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 2; Office rows with checks 8; Invoices overdue 1
    - approvals row 17 (SAMPLE-CMP-003 SAMPLE-O-006): approval pending;
    - approvals row 19 (SAMPLE-CMP-003 SAMPLE-O-008): approval pending;
    - approvals row 21 (SAMPLE-CMP-004 SAMPLE-O-002): approval pending;
    - approvals row 22 (SAMPLE-CMP-004 SAMPLE-O-003): approval pending;
    - approvals row 24 (SAMPLE-CMP-004 SAMPLE-O-005): approval pending;
    - approvals row 25 (SAMPLE-CMP-004 SAMPLE-O-006): approval pending;
    - approvals row 26 (SAMPLE-CMP-004 SAMPLE-O-007): approval pending; info: read the vetoes against the label;
    - approvals row 27 (SAMPLE-CMP-004 SAMPLE-O-008): approval pending;

## Fri 2027-01-08 
- Logged today: in_signed_offices +1, offices +1, campaigns +1, invoices +1, approvals +11, issues +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 3; Office rows with checks 15; Invoices overdue 1
    - approvals row 19 (SAMPLE-CMP-003 SAMPLE-O-008): approval pending;
    - approvals row 20 (SAMPLE-CMP-003 SAMPLE-O-009): approval pending;
    - approvals row 23 (SAMPLE-CMP-004 SAMPLE-O-003): approval pending;
    - approvals row 26 (SAMPLE-CMP-004 SAMPLE-O-006): approval pending;
    - approvals row 28 (SAMPLE-CMP-004 SAMPLE-O-008): approval pending;
    - approvals row 29 (SAMPLE-CMP-004 SAMPLE-O-009): approval pending;
    - approvals row 30 (SAMPLE-CMP-005 SAMPLE-O-001): approval pending; info: category not on the office's list;
    - approvals row 31 (SAMPLE-CMP-005 SAMPLE-O-002): approval pending; info: category not on the office's list;
    - approvals row 32 (SAMPLE-CMP-005 SAMPLE-O-003): approval pending; info: category not on the office's list;
    - approvals row 33 (SAMPLE-CMP-005 SAMPLE-O-004): approval pending; info: category not on the office's list;
    - approvals row 34 (SAMPLE-CMP-005 SAMPLE-O-005): approval pending; info: category not on the office's list;
    - approvals row 35 (SAMPLE-CMP-005 SAMPLE-O-006): approval pending; info: category not on the office's list;
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-009 dry-run/standard/invoices  ->  invoice SAMPLE-INV-009 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-009.pdf

## Sat 2027-01-09 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 3; Office rows with checks 8; Invoices overdue 2
    - approvals row 20 (SAMPLE-CMP-003 SAMPLE-O-009): approval pending;
    - approvals row 29 (SAMPLE-CMP-004 SAMPLE-O-009): approval pending;
    - approvals row 31 (SAMPLE-CMP-005 SAMPLE-O-002): approval pending; info: category not on the office's list;
    - approvals row 32 (SAMPLE-CMP-005 SAMPLE-O-003): approval pending; info: category not on the office's list;
    - approvals row 34 (SAMPLE-CMP-005 SAMPLE-O-005): approval pending; info: category not on the office's list;
    - approvals row 35 (SAMPLE-CMP-005 SAMPLE-O-006): approval pending; info: category not on the office's list;
    - approvals row 37 (SAMPLE-CMP-005 SAMPLE-O-008): approval pending; info: category not on the office's list;
    - approvals row 38 (SAMPLE-CMP-005 SAMPLE-O-009): approval pending; info: category not on the office's list;

## Sun 2027-01-10 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 3; Office rows with checks 5; Invoices overdue 2
    - approvals row 20 (SAMPLE-CMP-003 SAMPLE-O-009): approval pending;
    - approvals row 29 (SAMPLE-CMP-004 SAMPLE-O-009): approval pending;
    - approvals row 32 (SAMPLE-CMP-005 SAMPLE-O-003): approval pending; info: category not on the office's list;
    - approvals row 35 (SAMPLE-CMP-005 SAMPLE-O-006): approval pending; info: category not on the office's list;
    - approvals row 38 (SAMPLE-CMP-005 SAMPLE-O-009): approval pending; info: category not on the office's list;

## Mon 2027-01-11 
- Logged today: brands +1, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 1; Invoices overdue 1
- SAMPLE-CMP-003 ship release: RELEASED 2027-01-11: ship by Tue 2027-01-26 (latest Tue 2027-01-26)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release
- SAMPLE-CMP-004 ship release: RELEASED 2027-01-11: ship by Tue 2027-01-26 (latest Tue 2027-01-26)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 2 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release

## Tue 2027-01-12 
- Logged today: inventory +10, counts +8, photos +8, issues +1, hours +1, costs +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Office rows with checks 2
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 10 (SAMPLE-CMP-002 SAMPLE-O-004): no usable placement photo yet;
- SAMPLE-CMP-005 ship release: RELEASED 2027-01-12: ship by Tue 2027-01-26 (latest Tue 2027-01-26)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 1 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release

## Wed 2027-01-13 
- Logged today: in_signed_offices +1, offices +1, invoices +1, approvals +3, counts +1, photos +1, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns on ship HOLD 3; Office rows with checks 4
    - approvals row 5 (SAMPLE-CMP-001 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 21 (SAMPLE-CMP-003 SAMPLE-O-010): approval pending;
    - approvals row 31 (SAMPLE-CMP-004 SAMPLE-O-010): approval pending;
    - approvals row 41 (SAMPLE-CMP-005 SAMPLE-O-010): approval pending;
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-003 dry-run/standard/invoices  ->  invoice SAMPLE-INV-003 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-003.pdf

## Thu 2027-01-14 
- Logged today: inventory +2, counts +11, photos +2, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Campaigns with checks to read 3
    - campaigns row 4 (SAMPLE-CMP-003 SAMPLE-DRP-002): units changed since the ship-date email of 2027-01-11 (523, now 567): send the brand the revised numbers (template 02) and log them;
    - campaigns row 5 (SAMPLE-CMP-004 SAMPLE-DRP-002): units changed since the ship-date email of 2027-01-11 (457, now 501): send the brand the revised numbers (template 02) and log them; info: 1 office(s) short of the contract: add a roster office or credit $150 each;
    - campaigns row 6 (SAMPLE-CMP-005 SAMPLE-DRP-002): units changed since the ship-date email of 2027-01-12 (523, now 567): send the brand the revised numbers (template 02) and log them;
- The route changed after a ship-date email: revised email drafted
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 ship_release dry-run/standard/messages  ->  ship_release: 3 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/ship_release

## Fri 2027-01-15 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-01-19  · yes, approvals_ask, building_coi
- Logged today: inventory +7, counts +10, photos +9, scans +20, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-01-20 
- Logged today: hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-01-21 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-01-22 
- Logged today: inventory +3, scans +20, redemptions +2, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-01-25 
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-01-26  · paid, coi_check, release, ship
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-01-27 
- Logged today: hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-01-28 
- Logged today: inventory +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-01-29 
- Logged today: inventory +1, issues +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-02-01 
- Logged today: inventory +1, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Tue 2027-02-02  · receive, card_proof
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2027-02-03  · forms
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_links.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 dry-run/standard/links  ->  links: 58 (29 QR); none for 1 declined -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/links

## Thu 2027-02-04  · kit_print
- Logged today: stops +10, costs +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_kit.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 dry-run/standard/kit  ->  kit SAMPLE-DRP-002: 29 cards, 48 labels, 10 posts, QR all match
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 t3 dry-run/standard/messages  ->  t3: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/t3

## Fri 2027-02-05  · courier_brief
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Mon 2027-02-08  · confirm
- Logged today: scans +58, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_route.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 dry-run/standard/route  ->  route SAMPLE-DRP-002 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/route/route-SAMPLE-DRP-002.html ok
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 t1 dry-run/standard/messages  ->  t1: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/t1

## Tue 2027-02-09 T · drop
- Logged today: inventory +26, counts +23, photos +23, issues +1, hours +1, costs +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Office rows with checks 3
    - approvals row 15 (SAMPLE-CMP-003 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 25 (SAMPLE-CMP-004 SAMPLE-O-004): no usable placement photo yet;
    - approvals row 35 (SAMPLE-CMP-005 SAMPLE-O-004): no usable placement photo yet;
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 on_my_way dry-run/standard/messages  ->  on_my_way: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/on_my_way

## Wed 2027-02-10  · placement_confirm
- Logged today: invoices +4, inventory +3, counts +6, photos +6, hours +2
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-005 dry-run/standard/invoices  ->  invoice SAMPLE-INV-005 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-005.pdf
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-007 dry-run/standard/invoices  ->  invoice SAMPLE-INV-007 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-007.pdf
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-008 dry-run/standard/invoices  ->  invoice SAMPLE-INV-008 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-008.pdf
    $ python3 tools/make_invoice.py _work/dryrun-standard/day.xlsx SAMPLE-INV-010 dry-run/standard/invoices  ->  invoice SAMPLE-INV-010 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/invoices/SAMPLE-INV-010.pdf
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 placement_confirmation dry-run/standard/messages  ->  placement_confirmation: 3 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/placement_confirmation

## Thu 2027-02-11  · day3
- Logged today: inventory +3, counts +29, scans +58, redemptions +1, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 3
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 day3 dry-run/standard/messages  ->  day3: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/day3

## Fri 2027-02-12 
- Logged today: redemptions +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 2

## Tue 2027-02-16  · close
- Logged today: inventory +11, counts +29, photos +29, scans +58, hours +1
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
- Dashboard checks to fix: Invoices overdue 1
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 day5 dry-run/standard/messages  ->  day5: 10 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/day5

## Wed 2027-02-17  · pass_on
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 newsletter dry-run/standard/messages  ->  newsletter: 1 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/newsletter

## Thu 2027-02-18  · report_draft
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-02-19  · report
- Logged today: inventory +2, redemptions +3, hours +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_report.py _work/dryrun-standard/day.xlsx SAMPLE-CMP-003 dry-run/standard/reports --photos dry-run/standard/photos  ->  report SAMPLE-CMP-003 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/reports/SAMPLE-CMP-003/report.pdf (sample=True)
    $ python3 tools/make_report.py _work/dryrun-standard/day.xlsx SAMPLE-CMP-004 dry-run/standard/reports --photos dry-run/standard/photos  ->  report SAMPLE-CMP-004 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/reports/SAMPLE-CMP-004/report.pdf (sample=True)
    $ python3 tools/make_report.py _work/dryrun-standard/day.xlsx SAMPLE-CMP-005 dry-run/standard/reports --photos dry-run/standard/photos  ->  report SAMPLE-CMP-005 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/reports/SAMPLE-CMP-005/report.pdf (sample=True)
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 report dry-run/standard/messages  ->  report: 3 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/report

## Tue 2027-02-23  · office_debrief
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 dry-run/standard/debriefs  ->  debrief notes: 13 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/debriefs

## Wed 2027-02-24  · debrief
- Logged today: hours +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_debrief.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 dry-run/standard/debriefs  ->  debrief notes: 13 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/debriefs
    $ python3 tools/export_actuals.py _work/dryrun-standard/day.xlsx dry-run/standard/exports/at-2027-02-24 --pipeline  ->  exports: 5 campaigns, 2 drops, 68 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/exports/at-2027-02-24

## Tue 2027-03-02  · return_deadline
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Thu 2027-03-11  · redemption
- Logged today: redemptions +3
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.
    $ python3 tools/make_messages.py _work/dryrun-standard/day.xlsx SAMPLE-DRP-002 redemption dry-run/standard/messages  ->  redemption: 3 drafts -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/messages/redemption
    $ python3 tools/export_actuals.py _work/dryrun-standard/day.xlsx dry-run/standard/exports/at-2027-03-11 --pipeline  ->  exports: 5 campaigns, 2 drops, 68 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/exports/at-2027-03-11

## Fri 2027-03-19  · newsletter_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Fri 2027-03-26  · testimonial
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Wed 2028-02-16  · answers_delete
- Logged today: nothing new
- Sheet: 0 formula errors; 0 disagreements with the independent arithmetic.

## Final state 2027-03-20
- Sheet: 0 formula errors; 0 disagreements.
    $ python3 tools/export_actuals.py dry-run/standard/SAMPLE-tracker-standard-final.xlsx dry-run/standard/exports --pipeline  ->  exports: 5 campaigns, 2 drops, 68 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/exports
    $ python3 tools/export_actuals.py dry-run/standard/SAMPLE-tracker-standard-final.xlsx exports/SAMPLE-standard --pipeline  ->  exports: 5 campaigns, 2 drops, 68 hour rows -> /home/user/accounting-agent/desk-drop/campaign-ops/exports/SAMPLE-standard
    $ python3 tools/dump_forms.py dry-run/standard/SAMPLE-tracker-standard-final.xlsx standard dry-run/standard/forms  ->  forms: office_intake-website.csv 6, office_form-google.csv 4, office_intake_founder.csv 4, brand_intake-website.csv 4, brand_form-google.csv 1, brand_intake_founder.csv 1, survey-SAMPLE-CMP-001.csv 37, survey-SAMPLE-CMP-002.csv 32, survey-SAMPLE-CMP-003.csv 76, survey-SAMPLE-CMP-004.csv 71, survey-SAMPLE-CMP-005.csv 77, SAMPLE-newsletter-signup-SAMPLE-CMP-001.csv 10, SAMPLE-newsletter-pass-on-SAMPLE-CMP-001.txt 7, SAMPLE-newsletter-signup-SAMPLE-CMP-004.csv 7, SAMPLE-newsletter-pass-on-SAMPLE-CMP-004.txt 4 -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/forms
    $ python3 tools/make_calendar.py dry-run/standard/SAMPLE-tracker-standard-final.xlsx SAMPLE-DRP-002 dry-run/standard/sop  ->  sop SAMPLE-DRP-002 2027-02-09 courier: 27 steps -> /home/user/accounting-agent/desk-drop/campaign-ops/dry-run/standard/sop/sop-SAMPLE-DRP-002.html
