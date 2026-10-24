#!/usr/bin/env python3
"""Write sop/SOP.md: the written SOP, T-10 to T+30, for the three delivery models.
The step table comes from tools/sop_steps.py, the same list each drop's dated calendar uses.

  python3 tools/make_sop_doc.py
"""
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import opscal  # noqa: E402
import sop_steps as SS  # noqa: E402

ROOT = os.path.dirname(HERE)

HEAD = """# Standard operating procedure: one drop, T-10 to T+30

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

"""

TAIL = """
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
"""


def main():
    T = dt.date(2027, 2, 9)
    rows = ["| Step | When | Models | Who | What | Log it in | Tool |", "| --- | --- | --- | --- | --- | --- | --- |"]
    ds = {m: SS.dates(T, m) for m in ("founder", "courier", "direct-ship")}
    for st in SS.STEPS:
        sid, anchor, off, kind, models, owner, what, log, tool = st
        if anchor == "T":
            when = ("T" if off == 0 else "T%+d" % off) + (" calendar days" if kind == "cal" else "")
        elif anchor == "ship_req":
            when = "the requested ship-by" + ("" if off == 0 else " %+d" % off)
        else:
            when = "%s + %d %s" % (anchor, off, "calendar days" if kind == "cal" else "business days")
        if kind == "by":
            when = "by " + when
        mods = "all" if models == SS.ALL else ", ".join(sorted(models))
        rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (sid, when, mods, owner, what.replace("|", "/"), log, tool))
    ex = ["", "### Worked dates for a standard drop on Tue 2027-02-09", "", "| Step | Founder | Courier | Direct-ship |", "| --- | --- | --- | --- |"]
    for st in SS.STEPS:
        ex.append("| %s | %s | %s | %s |" % (st[0], *[(ds[m][st[0]].strftime("%a %Y-%m-%d") if st[0] in ds[m] else "-") for m in ("founder", "courier", "direct-ship")]))
    open(os.path.join(ROOT, "sop", "SOP.md"), "w", encoding="utf-8").write(HEAD + "\n".join(rows) + "\n" + "\n".join(ex) + "\n" + TAIL)
    print("wrote sop/SOP.md")


if __name__ == "__main__":
    main()
