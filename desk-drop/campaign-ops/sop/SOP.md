# Standard operating procedure: one drop, T-10 to T+30

For the founder, a briefed backup, or a courier's dispatcher. Every step says when, who, what, and where it is logged. The dated version for a real drop is made by `python3 tools/make_calendar.py tracker.xlsx DRP-00X out/` (a checklist PDF and a calendar file to import). Words: **T** is the drop day, always a Tuesday or Wednesday; **T-n** and **T+n** count business days (Monday to Friday, not US federal holidays); the window is T to T+4 (day 1 to day 5); **T+30** is calendar days (CONTRACTS section 3, derived, founder to confirm).

## 0. The drop date (the SOP cannot produce a bad one)

Every tool takes its dates from `tools/opscal.py`, which refuses a drop day that is a Monday, a Friday, a Thursday, a federal holiday, or whose five-day window touches a blackout (18 to 31 December, 18 to 31 August, and the Monday-to-Friday week containing 4 July or its observed holiday). The tracker's `drops` tab refuses the same dates twice over: a data-validation rule rejects the entry, and `date_check` reads REFUSED and blanks every derived date, so nothing downstream can be planned on it.

```
python3 tools/opscal.py check 2027-02-09     # OK, with the window
python3 tools/opscal.py next 2027-08-10 3     # the next three valid drop days
python3 tools/opscal.py slip 2027-02-09       # the slip rule: one week later, or the first clear Tue/Wed after a blackout
python3 tools/opscal.py dates 2027-02-09      # every SOP date
```

Tested on every day from 2026-10-24 to 2028-12-31 (`tests/test_opscal.py`): no valid date is a Monday or Friday or touches a blackout, and campaign zero's dates match CONTRACTS section 3 exactly (ship by Tue 2026-12-22, hard T-10 Mon 2026-12-28, receive by Tue 2027-01-05, window to Tue 2027-01-19 with MLK Day skipped, report Fri 2027-01-22, debrief Wed 2027-01-27, day 30 Thu 2027-02-11).

## 1. The three delivery models

| | Founder (campaign zero) | Courier or van (campaigns one and two) | Direct-ship (campaign three on) |
| --- | --- | --- | --- |
| Brand ships to | the receiving address (your home by default: sealed cases only, legal pack file 07) | the same | each office's own address, arriving on T; the reserve to you |
| Who counts on arrival | you, T-5 | you, T-5 | the office, on T (you check one package of each flavor from the reserve at T-5) |
| Kit (cards, posts) | packed in the cases | packed in the cases | mailed to each office to arrive by T-1 |
| Drop morning | you walk the route with a hand truck and car rides | the courier drives the route from the route sheet; you meet the courier at every office whose first drop it is | the carrier delivers; you visit every office whose first drop it is |
| Delivered count | `founder_count` | `courier_count` (the courier writes it on the route sheet and photographs the case at handover) | `office_count` (the office's reply); `packing_list` only if nobody counted, and the report then says so |
| Top-ups on day 3 | you, from reserve | you, from reserve (walkable cluster) | you, from the reserve you hold |
| Leftovers on day 5 | collected by you (brand chose return) or left with the office (release) | the same | left with the office, or the brand sends a return label to each office |

A consolidation point other than your home is the courier model with a different receiving address; it adds the FDA registration question in legal pack file 07 (follow-up 7).

Every new office gets an in-person visit on its first drop, in every model (plan, "Delivery by phase"). The route sheet marks them FIRST DROP.

## 2. The steps

"By" means the latest day; earlier is fine. The tool column names the command that makes the document for that step (README, "Commands").

| Step | When | Models | Who | What | Log it in | Tool |
| --- | --- | --- | --- | --- | --- | --- |
| yes | by the requested ship-by -5 | all | you | Brand says yes: send the campaign agreement (legal pack file 10, Part 1 from the campaign row), the invoice (tools/make_invoice.py) and the certificate request (file 11), and ask for the allergen sheet, logo, two card sentences, discount code or landing page, the unused-product election and the newsletter choice. Latest date that still leaves five business days to pay before the requested ship date. | campaigns row (tier, offices, terms); invoices row | make_invoice.py |
| approvals_ask | by the requested ship-by -5 | all | you | Ask each office on the route about this brand (template 01). An office's first three drops need its explicit yes; after that, notice at least five business days ahead and it comes unless they say no. | approvals rows: asked_date | make_messages.py approvals |
| building_coi | by T-15 | all | you | Offices whose building wants our certificate (coi_required yes or unsure): request it from our carrier at least 10 business days before that office's first drop (legal pack file 12), only once general liability is bound. | offices: building_coi_status, building_coi_date |  |
| paid | by the requested ship-by | all | brand | Payment lands in the business account: log paid_date and paid_amount on invoices. Founding: due within five business days of the invoice and before shipping; standard: the first 50% on signing. Five business days late: you decide whether to cancel and refund (file 10, section 3). | invoices: paid_date, paid_amount_usd, method, bank_reference |  |
| coi_check | by the requested ship-by | all | you | Brand's certificate in: the five-minute check in legal pack file 11. Tick coi_check_ok on brands. If the policy ends before 12 months after the window, diary the renewal certificate. | campaigns: coi_received_date; brands: coi_check_ok, coi_policy_end_date |  |
| release | by the requested ship-by | all | you | When campaigns shows ship_release RELEASED (pre-ship payment in, agreement signed, certificate checked, every office on the route has answered), send the ship-date email (template 02) the same day and log what it said. Never confirm a ship date on HOLD. An office that said no and cannot be replaced shows as a credit to make ($120 founding, $150 standard), not a hold. If an office joins or leaves the route before the product arrives, the campaign's checks say the units changed: send the revised email the tool drafts, and log it. | campaigns: ship_release; ship_email_sent_date, ship_email_units | make_messages.py ship_release |
| direct_plan | by T-10 | direct-ship | you and brand | Direct-ship: send the brand each office's address and case labels (labels.pdf), ask for a service that delivers on T, one tracking number per office by T-2 (template 02 says it), and the reserve shipped to you by T-5. | stops: carrier_tracking later | make_kit.py |
| ship | T-10 | all | brand | Hard ship-by and cancel-by date (T-10). Approvals due. If T-10 to T-5 crosses 18 to 31 December, brands were asked to ship earlier (ship_by_requested). | approvals: reply, reply_date |  |
| receive | T-5 | courier, founder | you | Receive and count the day cases arrive (by T-5 at the latest): count against the packing list, best-by at least 60 days after T, lot numbers, damage; photograph the cases. Reject what fails and tell the brand the same day. Check the allergen line on the card text word for word against a package in your hand. Short shipment (the campaign's checks say "received X of Y due"): reduce units per office evenly (units_override), log a short_shipment issue and tell the brand the same day. | inventory: received (lot, best_by), rejected; approvals: units_override; issues |  |
| receive_ds | T-5 | direct-ship | you | Direct-ship: receive the reserve and check one package of each flavor: best-by, lot, and the allergen line word for word. | inventory: received (reserve) |  |
| card_proof | T-5 | all | you | Send the brand the card text before printing (brand agreement section 1): two sentences, allergen line, buy line. | campaigns: card_proof_sent_date |  |
| forms | T-4 | all | you | Make each campaign's survey form (forms/survey-form.md) and, if the brand chose it, its newsletter sign-up form. Paste the prefill template into campaigns. Then make the links and QR codes and import them into the link tool. | campaigns: survey_form_url, survey_prefill_template, newsletter_form_url | make_links.py |
| kit_print | T-3 | all | you | Not arrived (founder, courier) = slip exactly one week (tools/opscal.py slip) and tell every office and the brand today (template 12). Otherwise print cards and labels (make_kit.py; qr-check.txt must say all OK), test-scan every card, and send each office its window and Slack post (template 03). | stops: slack_post_sent_date; costs: kit | make_kit.py; make_messages.py t3 |
| kit_mail | T-3 | direct-ship | you | Direct-ship: mail each office its tent cards and the Slack post, to arrive by T-1. | stops: kit_mailed_date; costs: other_direct (postage) |  |
| courier_brief | T-2 | courier | you | Courier: confirm the booking and send the route sheet (make_route.py). Send building certificates ahead to the buildings that require them, and attach the same PDFs to the courier's booking email (the route sheet tells the courier they are there). Tell the courier where cases taken back go: the receiving address, the same day. | drops: courier_or_van | make_route.py |
| tracking | T-2 | direct-ship | brand | Direct-ship: one tracking number per office per brand, delivering on T (stops: carrier_tracking, separated by semicolons). | stops: carrier_tracking |  |
| confirm | T-1 | all | you | Text each pantry owner to confirm (template 04). Pack one labeled case per office per brand against the kit checklist; bag and label the reserve. Print the route sheet. Charge the phone, load the hand truck. Read every link's total after your test scans and log it as the baseline. | stops: confirm_text_sent_date; scans: baseline | make_route.py; make_messages.py t1 |
| drop | T | courier, founder | you or courier | Drop day, 8 to 11 am: route in order; 'on my way' 20 minutes out (template 05); the per-stop procedure on the route sheet. Courier: you meet the courier at every first-drop office. Log everything the same day: the delivered count is the route sheet's 'handed over' count (founder_count or courier_count); an office that declined at the door gets no delivered row. | stops: arrival, departure, handed_to_role, outcome; inventory: delivered; photos; counts: placed; issues; hours: drop_day | make_messages.py on_my_way |
| drop_ds | T | direct-ship | carrier and office | Direct-ship: watch tracking; each office confirms the count and sends the placement photo. Visit every office whose first drop this is. | inventory: delivered (count_source office_count); photos; counts |  |
| placement_confirm | T+1 | all | you | Placement confirmation to each brand (template 06): the offices placed by today, each with its photo. Office not placed by today, or turned away at the door: credit note row and refund or take it off the balance ($120 founding, $150 standard); the campaign's checks say "credit due from T+1" until the credit notes cover it. Standard: issue the balance invoice today. | invoices: credit_note, standard_balance | make_messages.py placement_confirmation; make_invoice.py |
| day3 | T+2 | all | you and office | Day 3: ask each office for a count (template 07); top up from reserve where empty; nudge any office under five responses. Read the links (mid). | counts: remaining_day3; inventory: topped_up; scans: mid | make_messages.py day3 |
| close | T+4 | all | you and office | Day 5: last photo and count (template 08); collect leftovers (brand chose return) or leave them (release). At the end of the day turn off 'Accepting responses' on every campaign survey form and read every link total (close). | counts: remaining_day5; photos: later; inventory: collected or released_to_office; scans: close | make_messages.py day5 |
| pass_on | T+5 | all | you | Newsletter (only where chosen): send the ticked addresses once (template 09), delete the unticked responses today, log the count only. Reconcile stock: reserve and leftovers on hand. Ask for the return label (brand chose return). | campaigns: newsletter_passed_date, newsletter_passed_count, newsletter_unticked_deleted_date | make_messages.py newsletter |
| report_draft | T+6 | all | you | Pick three comments word for word (replace names with [name removed]), write three 'learned' lines and the recommendation on the campaign row. | campaigns: comment_1..3, learned, recommendation |  |
| report | T+7 | all | you | Report (make_report.py) to each brand with template 10 (make_messages.py report --reports, which drafts only where the PDF exists); standard: after the balance is paid. Office summaries to each office that received the product. Log report_delivered_date. | campaigns: report_delivered_date | make_report.py; make_messages.py report --reports |
| office_debrief | by T+9 | all | you and office | Ten-minute debrief with each office (templates/debrief-office.md). Log the date and the one-question answer. | stops: office_debrief_date, office_would_do_again | make_debrief.py |
| debrief | T+10 | all | you and brand | Brand debrief, 20 minutes (templates/debrief-brand.md); send the renewal proposal the same day. Export actuals for the financial model (export_actuals.py) and set Actuals in = Y there once money, costs and hours are final. | campaigns: debrief_date, brand_would_buy_again, renewed; hours: reporting_debriefs | make_debrief.py; export_actuals.py |
| return_deadline | T+14 | all | you | Ten business days after the window: no prepaid return label = unused reserve to roster offices, collected leftovers back to their own office or disposed (brand agreement section 9). Stock on hand must be zero. | inventory: returned_to_brand / given_to_roster_office / released_to_office / disposed |  |
| redemption | T+30 calendar days | all | brand | Day 30 (calendar): ask the brand for code redemptions (template 11). Log them; export actuals again; update renewed. | redemptions; campaigns: renewed | make_messages.py redemption; export_actuals.py |
| newsletter_delete | pass_on + 30 calendar days | all | you | Thirty days after passing the list on: delete every response in the sign-up form, the form itself and the sent email; empty the trash. Log the date. | campaigns: newsletter_deleted_date |  |
| testimonial | debrief + 30 calendar days | all | brand | Founding brands only, if we delivered everything in section 1: the short written statement is due (brand agreement section 3). | campaigns: notes |  |
| answers_delete | close + 365 calendar days | all | you | Twelve months after the campaign: first freeze its totals (tools/freeze_survey.py, then File > Import > Append the CSV to the survey_frozen tab; the campaign's numbers must not change). Then delete the campaign's survey tab, the form's responses and the form. Log the date. | survey_frozen (import); campaigns: answers_deleted_date | freeze_survey.py |

### Worked dates for a standard drop on Tue 2027-02-09

| Step | Founder | Courier | Direct-ship |
| --- | --- | --- | --- |
| yes | Tue 2027-01-19 | Tue 2027-01-19 | Tue 2027-01-19 |
| approvals_ask | Tue 2027-01-19 | Tue 2027-01-19 | Tue 2027-01-19 |
| building_coi | Tue 2027-01-19 | Tue 2027-01-19 | Tue 2027-01-19 |
| paid | Tue 2027-01-26 | Tue 2027-01-26 | Tue 2027-01-26 |
| coi_check | Tue 2027-01-26 | Tue 2027-01-26 | Tue 2027-01-26 |
| release | Tue 2027-01-26 | Tue 2027-01-26 | Tue 2027-01-26 |
| direct_plan | - | - | Tue 2027-01-26 |
| ship | Tue 2027-01-26 | Tue 2027-01-26 | Tue 2027-01-26 |
| receive | Tue 2027-02-02 | Tue 2027-02-02 | - |
| receive_ds | - | - | Tue 2027-02-02 |
| card_proof | Tue 2027-02-02 | Tue 2027-02-02 | Tue 2027-02-02 |
| forms | Wed 2027-02-03 | Wed 2027-02-03 | Wed 2027-02-03 |
| kit_print | Thu 2027-02-04 | Thu 2027-02-04 | Thu 2027-02-04 |
| kit_mail | - | - | Thu 2027-02-04 |
| courier_brief | - | Fri 2027-02-05 | - |
| tracking | - | - | Fri 2027-02-05 |
| confirm | Mon 2027-02-08 | Mon 2027-02-08 | Mon 2027-02-08 |
| drop | Tue 2027-02-09 | Tue 2027-02-09 | - |
| drop_ds | - | - | Tue 2027-02-09 |
| placement_confirm | Wed 2027-02-10 | Wed 2027-02-10 | Wed 2027-02-10 |
| day3 | Thu 2027-02-11 | Thu 2027-02-11 | Thu 2027-02-11 |
| close | Tue 2027-02-16 | Tue 2027-02-16 | Tue 2027-02-16 |
| pass_on | Wed 2027-02-17 | Wed 2027-02-17 | Wed 2027-02-17 |
| report_draft | Thu 2027-02-18 | Thu 2027-02-18 | Thu 2027-02-18 |
| report | Fri 2027-02-19 | Fri 2027-02-19 | Fri 2027-02-19 |
| office_debrief | Tue 2027-02-23 | Tue 2027-02-23 | Tue 2027-02-23 |
| debrief | Wed 2027-02-24 | Wed 2027-02-24 | Wed 2027-02-24 |
| return_deadline | Tue 2027-03-02 | Tue 2027-03-02 | Tue 2027-03-02 |
| redemption | Thu 2027-03-11 | Thu 2027-03-11 | Thu 2027-03-11 |
| newsletter_delete | Fri 2027-03-19 | Fri 2027-03-19 | Fri 2027-03-19 |
| testimonial | Fri 2027-03-26 | Fri 2027-03-26 | Fri 2027-03-26 |
| answers_delete | Wed 2028-02-16 | Wed 2028-02-16 | Wed 2028-02-16 |

## 3. At every stop (plan, per-stop procedure; printed on the route sheet)

1. Arrive inside the receiving window. Security desk: give the pantry owner's name and your ID. Walk-up: straight to the owner.
2. Hand the case to the owner, or place it yourself if they say so: eye level beside the existing snacks where the pantry allows, never inside a cabinet, card in front, allergen line visible. One display per pantry at a time.
3. Two photos: one wide of the pantry, one close of the card and product. No people, faces, screens or whiteboards. Count the visible units.
4. Confirm the owner has the Slack post and will post it today. Thank them. Leave.
5. Log: arrival and departure time, units handed over, who received (a role, not a name), anything that went wrong.

Ten stops is about two and a half hours plus travel. Walk-up lobbies first, then by receiving window.

## 4. When things go wrong (plan, "When things go wrong"; every row is also an issue type)

| Situation | Do this | Log it |
| --- | --- | --- |
| Product not in by T-3 | Slip exactly one week (`opscal.py slip`; a blackout pushes it to the first clear Tuesday or Wednesday). Tell every office and the brand the same day (template 12). A second miss: either side may treat it as cancelled (brand agreement section 8) | issues: late_arrival; drops: change the date, keep the drop_id |
| Short shipment | The campaign's checks say "received X of Y due". Reduce units per office evenly (approvals: units_override). Tell the brand the same day. No money changes: the price is per office and the brand agreement (file 10, section 8) is silent on shortfalls. **This differs from the plan** ("credit the difference on the next campaign"); it is a question for you in the report back, default no credit | issues: short_shipment; approvals: units_override |
| Damaged or under 60 days on the drop day | Photograph, set aside, never place. Send the brand the counts; return or dispose as they say | inventory: rejected; issues |
| Owner absent | Front desk only where the route sheet says Front desk OK: Y. Otherwise take it back (a courier brings it to the receiving address the same day) and deliver next morning (still inside one business day). Never leave food unattended in a lobby | stops: outcome owner_absent_return; inventory: delivered on the day it is handed over; issues |
| Office declines at the door | Take the case back, thank them. It stays in reserve: log **no** delivered row for that office, so nothing needs correcting (if one was logged by mistake, delete it; the stops check says so). The office is then off the drop for that brand: no letter, no day-3 or day-5 ask, not in the report or Gate 2, and a credit note at T+1 (the campaign's checks ask for it). Two declines: the office leaves the roster | stops: outcome declined; issues: declined_at_door; invoices: credit_note |
| Not placed by T+1 | It is off the placement confirmation; refund or credit that office's share ($120 founding, $150 standard) unless another roster office replaces it | invoices: credit_note; issues: placement_late |
| Complaint or reaction reported | Remove the product from that office now, tell the brand the same day, write down what was said and when. No medical advice. No employee names | issues: complaint_or_reaction |
| Brand recall or pull request | Remove from every office within one business day; tell every office the same day; collect what is left, including released units | issues: recall_or_pull; inventory: collected |
| Brand asks for employee contact details | Decline: the agreements say we collect none | issues: brand_asks_employee_data |
| A photo shows a person, a screen or a whiteboard | Never use it; ask for another | photos: no_people_or_screens = N |
| You are ill on drop day | The briefed backup runs the route from the route sheet and the kit; nothing is perishable, so a slip costs a week, not the product (events outside our control: brand agreement section 8) | drops: backup_person |

## 5. What counts as what (the ladder, kept apart everywhere)

| Rung | Counted from | Never |
| --- | --- | --- |
| Delivered | inventory `delivered` rows: units handed over at the office (the route sheet's "handed over" count; the day-3 top-ups are kept separate). An office that declined at the door has none | added to top-ups |
| Placed | the shelf count logged with a usable placement photo (card visible, no people). No usable photo: zero placed, whatever was delivered | estimated |
| Placed within one business day | that photo is dated on or before T+1 (counted from the drop day, also for direct-ship) | counted from a late carrier delivery |
| Depleted | placed plus top-ups minus the day-5 count | inferred without a day-5 count (the report waits for it) |
| Responded | survey answers inside the window whose card code matches an office on the campaign. "Tried" is an answer | counted from answers before T, after T+4, or with an edited code |
| Scanned | the QR link's total at close minus its total after your own test scan | mixed with post-link opens |
| Purchased | code redemptions the brand reports, with the date | never called sales or conversions |
| Incremental | not measured; every report says so | claimed |

## 6. Privacy schedule (legal pack file 13, D7 to D10)

| When | What |
| --- | --- |
| Drop day | The printed route sheet holds owners' names and phones: a courier or backup sends it back with the counts and keeps no copy; you shred it once its counts are in the tracker |
| T+5 | Newsletter list (only ticked boxes, addresses only, alphabetical) to the brand once; unticked addresses deleted the same day |
| T+7 | Office summaries: comments quoted with anything that may be a name taken out by the tool (it over-removes on purpose; read once more for names that start a sentence); no breakdown of a brand's answers where an office gave fewer than five, and no rating or would-buy split drawn from fewer than five people (config `office_summary_min_answers`, the office's own commitment) |
| Pass-on + 30 days | Every sign-up response, the sign-up form and the sent email deleted; trash emptied |
| 12 months after the campaign | First the campaign's totals frozen into `survey_frozen` (`tools/freeze_survey.py`), then the campaign's survey tab, its form's responses and the form deleted |
| 12 months after intake, if nothing proceeded | Intake rows deleted (the website's monthly reminder; website/SETUP.md section 3, step 10) |
| 365 days after an office leaves | Its people's names, emails and phones cleared in `in_signed_offices`, `office_intake` and `office_form`; the company, address and campaign counts stay (config `contacts_keep_days_after_leaving`; a dashboard check line counts any left over) |

## 7. Changing this SOP

Edit `tools/sop_steps.py` (the steps) or this script's text, then run `python3 tools/make_sop_doc.py`. Each drop's calendar picks up the change the next time you make it.
