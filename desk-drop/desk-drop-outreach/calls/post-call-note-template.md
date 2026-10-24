# Post-call note template

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/calls/`

**What it is for.** Turning a call into one tracker row and a Clay update in ten minutes or less, with the person's words intact (plan, Phase 0: "Write notes within ten minutes of each call, with quotes verbatim").

**How it works.** The fields below are in the same order as the columns of **Office_Log** and **Brand_Log** in `tracking/conversation-tracker.xlsx`. Three ways to use them, fastest first:
1. **The Note_Office or Note_Brand tab** of the tracker: the same fields top to bottom with dropdowns, which also works on a phone. Fill column B, copy the "row to paste", and paste it into the log's next empty row as values only (Ctrl+Shift+V). Then clear column B.
2. Type straight across one row of the log.
3. Copy the text block below into a notes app before the call, fill it as you talk, then type it into the Note tab.

---

## The ten minutes

| Minutes | Do | Why this order |
| --- | --- | --- |
| 0 to 4 | Verbatims, while you still hear them: every `..._verbatim` field, the objections in their words, the budget-probe answer. | Words fade first; numbers and codes do not |
| 4 to 7 | Numbers and codes: headcount, spend, probe low and high, willingness to pay, Y/N fields, objection codes, category keys | Dropdowns on the sheet make these quick |
| 7 to 9 | **Clay write-back** (box below), and a new Clay row for each referral | Clay is the status store; the daily view and follow-ups read it |
| 9 to 10 | `note_minutes` (honest), `clay_updated` = Y | The scorecard reports minutes per note, so the ten-minute rule is visible |

If a note runs long, cut the probing notes, never the verbatims.

## Number rules (both sides)

- A range: the low end goes in the `_low_usd` or main field, the high end in `_high_usd` where there is one. "$100 to $200 a month" is 100 and 200.
- "No budget", "zero", "we wouldn't pay": **0**. It counts in the median.
- "I don't know", "I'd have to ask", no number: **blank**, with the words kept in the verbatim.
- Office budget probe: USD per month. Brand willingness to pay: USD for the whole 500-unit, 10-office campaign (convert and write how in `wtp_unit_note`).
- Dates: YYYY-MM-DD. Money: plain numbers, no $ sign.
- A verbatim you could not catch word for word starts with "paraphrase:".

---

## Office note (Office_Log, one row)

```text
row_id:                     (paste from Clay before the call)
company:
contact_name:
contact_title:
source:                     Clay offices table / warm network / walk-in / referral from <row_id>
channel:                    email / linkedin / warm-intro / walk-in
call_date:                  YYYY-MM-DD
call_type:                  phone / video / in-person / walk-in
q1_pantry_today_verbatim:   "..."
pantry_vendor:
uses_snack_service:         Y / N        (a snack delivery service or vendor, not a grocery order)
monthly_pantry_spend_usd:   (number or blank)
monthly_pantry_spend_verbatim: "..."
tuesday_headcount:          (number; low end of a range)
headcount_verbatim:         "..."
q3_brands_reach_out:        Y / N
q3_free_product_verbatim:   "..."
q4_yes_needs_verbatim:      "..."
q4_no_triggers_verbatim:    "..."
q5_photo_and_survey:        Y / N / maybe
q5_verbatim:                "..."
budget_probe_asked:         Y / N        (Y only if read word for word)
budget_probe_verbatim:      "..."
budget_probe_low_usd:       (USD a month; 0 = no budget; blank = no number)
budget_probe_high_usd:
referrals_given_count:
referrals_given:            Company - Title; Company - Title
pantry_owner_named:         Y / N
pantry_owner_name:
pantry_owner_title:
owner_can_say_yes_alone:    Y / N / maybe   ("I need to ask facilities or HR" = N)
other_approver:             facilities / hr / ceo-or-assistant / landlord-or-building / finance / other
receiving_window:           e.g. Tue-Wed 9-11am   (blank if not named)
receiving_type:             walk-up / front desk / security desk / loading dock / other / unknown
coi_required:               yes / no / unsure
security_notes:
veto_categories:            category keys; semicolons
veto_verbatim:              "..."
objection_1:                (code, list below)
objection_2:
objection_3:
objections_verbatim:        "..."
yes_in_principle:           Y / N / maybe
yes_signals:                named_window_unprompted; asked_when; introduced_colleague
shortlist:                  Y / N        (on your list of 8 offices to pursue)
quote_ok_to_share:          Y / N        (Y only if they said yes to being quoted without their name)
note_minutes:
clay_updated:               Y
notes:
```

## Brand note (Brand_Log, one row)

```text
row_id:
company:
contact_name:
contact_title:
source:                     Clay brands table / Startup CPG event / shelf photo / warm network / referral from <row_id>
channel:                    email / linkedin / warm-intro / walk-in
call_date:                  YYYY-MM-DD
call_type:                  phone / video / in-person
q1_trial_now_verbatim:      "..."
q2_sampling_budget_quarter_low_usd:
q2_sampling_budget_quarter_high_usd:
q2_budget_verbatim:         "..."
budget_approver:            (their words: "me", "my cofounder and I")
controls_budget:            Y / N        (Y only if this person approves alone)
q3_seeded_offices:          Y / N
q3_verbatim:                "..."
wtp_before_usd:             (their number BEFORE you said $1,500; 0 = nothing; blank = no number)
wtp_before_verbatim:        "..."
wtp_unit_note:        e.g. "$1 a unit x 500 = 500"
price_1500_mentioned:       Y / N
wtp_after_usd:              (their number AFTER hearing $1,500)
wtp_after_verbatim:         "..."
q5_report_needs_verbatim:   "..."
q6_buy_path_type:           retailer-in-cluster / retailer-within-10-blocks / online-with-code / online-no-code / none / unknown
q6_buy_path_verbatim:       store and street, or the site
q7_stoppers_verbatim:       "..."
qual_q1_sealed_shelf_stable_60d:        Y / N / unsure   (qualifying calls, weeks 4 to 7; else blank)
qual_q2_labeled_ingredients_allergens:  Y / N / unsure
qual_q3_buy_path_near_cluster:          Y / N / unsure
qual_q4_can_ship_275_in_10bd:           Y / N / unsure
qual_q5_product_liability_insurance:    Y / N / unsure
qual_q6_contact_can_approve_600:        Y / N / unsure
qual_q7_why_now:                        "..."
qual_not_excluded:                      Y / N
objection_1:
objection_2:
objection_3:
objections_verbatim:        "..."
yes_in_principle:           Y / N / maybe
shortlist:                  Y / N        (on your list of 6 brands to pursue)
referrals_given_count:
referrals_given:            Brand - Title; Brand - Title
quote_ok_to_share:          Y / N        (Y only if they said yes to being quoted without their name)
note_minutes:
clay_updated:               Y
notes:
```

---

## Clay write-back (minutes 7 to 9)

Clay holds status and next steps; the tracker holds what was said. Write these on the person's Clay row, both sides:

| Clay column | Write | Rule |
| --- | --- | --- |
| `call_date` | the call date | Same as the tracker row |
| `status` | see the table below | CONTRACTS section 4 values only |
| `yes_in_principle` | Y or N | Y if they said Y; a maybe is N in Clay |
| `call_notes` | one line + "see tracker YYYY-MM-DD" | The full note lives in the tracker, not in Clay |
| `call_note_hook` | twelve words or fewer they said, e.g. "the Thursday bagel order" | Used by the post-call email (`messages/03-personalization-fields.csv`). Leave blank if nothing fits |
| `next_action` | one key: `send_one_pager`, `book_call`, `send_proposal`, `recontact`, `ask_referral`, `none` ... | Clay is the only place next actions live |
| `next_action_date` | YYYY-MM-DD | Drives tomorrow's follow-up list |

**Status after the call**

| What happened | Clay `status` |
| --- | --- |
| Office: Y, with the pantry owner and the receiving window named | `yes_in_principle` |
| Brand: Y at a number they named | `yes_in_principle` |
| Anything else that was a real conversation (maybe, interested, undecided, Y without owner or window) | `call_done` |
| "Not now, try me in [month]" | `not_now`, with `next_action` = `recontact` and the date they gave |
| A clear no | `no` (ask for one referral first, `messages/08-warm-intro-referral-walk-in.md` 2c) |
| "Please don't contact me again", in any words | `do_not_contact`, plus `do_not_contact` = Y and `opt_out_date` = today. Same day, never reversed |

**Each referral:** add a Clay row (company, name if given, title) with `referral_from` = this person's `row_id`, `status` = `new`, and `referrer_ok_to_name` = Y only if they said you may use their name.

---

## Objection codes

**Office side** (`objection_1` to `objection_3` on Office_Log)

| Code | Means |
| --- | --- |
| `needs_approval` | I need to ask facilities, HR or someone else |
| `existing_vendor` | We already have a pantry vendor or contract |
| `allergy_policy` | Allergy or food-safety worry |
| `healthy_policy` | We only stock healthy items (wellness policy) |
| `building_receiving` | Building security, receiving or certificate rules |
| `low_attendance` | Not enough people in on a given day |
| `commitments_too_much` | Photos, survey or debrief are too much work |
| `survey_concern` | Survey or employee-data worry |
| `vendor_fatigue` | We don't want vendors or marketing in the office |
| `space` | No shelf or counter space |
| `supply_irregular` | Irregular, roughly monthly supply isn't useful |
| `quality_unknown` | Don't know these brands; quality worry |
| `other` | Anything else (the verbatim says what) |

**Brand side** (`objection_1` to `objection_3` on Brand_Log). The first four are the plan's four objections (Phase 2).

| Code | Means |
| --- | --- |
| `seed_ourselves` | We can seed offices ourselves for free |
| `price_per_sample` | $600 / the price is more than we pay per sample elsewhere |
| `free_trial` | Can we do a free trial first? |
| `what_we_get` | What do we actually get out of it? |
| `budget_timing` | No budget now / budget timing |
| `inventory` | Inventory or shipping the units |
| `shelf_life` | Shelf life |
| `not_our_audience` | Office workers aren't our customer |
| `want_proof` | Show me results from other brands first |
| `want_sales_data` | We need sales or lift data, not feedback |
| `no_buy_path` | No store near the cluster and no online code |
| `insurance` | No product liability certificate |
| `other` | Anything else |

The scorecard ranks these codes, so pick the closest one and keep the exact words in `objections_verbatim`.

---

## A filled example (SAMPLE: illustrative placeholders, not results)

```text
row_id:                     SAMPLE-O-001
company:                    SAMPLE Office 01
contact_name:               SAMPLE Contact O01
contact_title:              Office Manager
source:                     SAMPLE warm network
channel:                    warm-intro
call_date:                  2026-10-27
call_type:                  video
q1_pantry_today_verbatim:   "SAMPLE: I order from a grocery site every Monday, I pick most of it, people ask in Slack."
pantry_vendor:              SAMPLE grocery order
uses_snack_service:         N
monthly_pantry_spend_usd:   800
monthly_pantry_spend_verbatim: "SAMPLE: about $800 a month"
tuesday_headcount:          60
headcount_verbatim:         "SAMPLE: around 60 on a Tuesday, Fridays are dead"
q3_brands_reach_out:        Y
q3_free_product_verbatim:   "SAMPLE: brands email us, we ignore most"
q4_yes_needs_verbatim:      "SAMPLE: allergen info and no work for me"
q4_no_triggers_verbatim:    "SAMPLE: anything with nuts"
q5_photo_and_survey:        Y
q5_verbatim:                "SAMPLE: a photo is fine, we have a #random channel"
budget_probe_asked:         Y
budget_probe_verbatim:      "SAMPLE: maybe $100 to $200 a month"
budget_probe_low_usd:       100
budget_probe_high_usd:      200
referrals_given_count:      1
referrals_given:            SAMPLE Office 30 - Office Manager
pantry_owner_named:         Y
pantry_owner_name:          SAMPLE Owner O01
pantry_owner_title:         Office Manager
owner_can_say_yes_alone:    Y
receiving_window:           SAMPLE Tue-Wed 9-11am
receiving_type:             front desk
coi_required:               no
security_notes:             SAMPLE: sign in at desk
veto_categories:            meat-snacks
veto_verbatim:              "SAMPLE: no jerky"
objection_1:                allergy_policy
objections_verbatim:        "SAMPLE: we have two people with nut allergies"
yes_in_principle:           Y
yes_signals:                asked_when
shortlist:                  Y
quote_ok_to_share:          Y
note_minutes:               9
clay_updated:               Y
```

Clay write-back for it: `call_date` 2026-10-27, `status` `yes_in_principle`, `yes_in_principle` Y, `call_notes` "SAMPLE: yes; owner and window named; nut allergies; see tracker 2026-10-27", `call_note_hook` "SAMPLE: the Monday grocery order", `next_action` `send_one_pager`, `next_action_date` 2026-10-27; one new row for the referral with `referral_from` = SAMPLE-O-001.

## Changelog

Round numbers are part B's rounds; a round that did not change this file is not listed.

- Round 1 (2026-10-24): field order copied from the tracker's columns; ten-minute plan; number rules; Clay write-back; status table; objection codes; a SAMPLE example.
- Round 2 (2026-10-24): checked by script that both blocks list exactly the tracker's columns in the tracker's order (44 office fields, 44 brand fields), so the note types straight across one row; verbatims first, codes second in the ten-minute plan; the qualification checks sit in the brand block, blank outside weeks 4 to 7; added Part A's `call_note_hook` and `referrer_ok_to_name` to the write-back so the post-call emails have what they need without a second pass.
- Round 3 (2026-10-24): critique as an operations lead: 45 columns typed across one row is slow and impossible on a phone, so the tracker gained Note_Office and Note_Brand tabs (vertical form, one row to paste as values, tested); added `shortlist` for the plan's 8 offices and 6 brands; field order re-checked by script (45 and 45).
- Round 4 (2026-10-24): four coded fields so Part A's Startup CPG post numbers come straight from the tracker (`uses_snack_service`, `q3_brands_reach_out`, `other_approver`) and a per-person `quote_ok_to_share`, without which nobody is ever quoted; field order re-checked by script (49 and 46).
