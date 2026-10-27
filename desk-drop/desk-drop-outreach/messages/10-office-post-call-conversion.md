# 10 · Office post-call conversion: from a good call to a signed office

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** The emails that take an office from a good call to a signed participation agreement, a completed intake and an approved first brand. This is the plan's Phase 1 conversion path, step by step, with one ask per email.

**When it is used.** The day of any office call that ended with "can I send you a one-pager?" or a yes in principle (the call guide in `calls/` ends that way). Weeks 1 to 5 for the one-pager; agreements only once `attorney_cleared = Y` (the attorney hour is held by Wed 2026-11-18, derived, founder to confirm). Then the brand-approval email for each office, before any brand pays.

**How to fill it in.** Tokens and slots as in 03 and 04. `{call_note_hook}` is the line you wrote within ten minutes of the call. Every email carries `{SIGNATURE}` (file 02). These go to someone who has talked to you, so attachments are fine here.

`sequence` = `office-conversion-A`. Status moves, in Clay: `call_done` → `yes_in_principle` (they said yes and named a pantry owner and a receiving window) → `materials_sent` (one-pager sent) → `signed` (agreement signed, intake complete). A signed office becomes a row in `handoff/signed_offices.csv` (`handoff/how-to-fill-handoff-files.md`, CONTRACTS 6.4).

---

## The path

| Step | When | Email | The one ask | Clay |
| --- | --- | --- | --- | --- |
| 0 | Same day as a call in weeks 1 to 3 (before `office_selling_on = Y`) | Thanks, and the discovery one-pager | May I write again with the details once it's decided? | `next_action = send_one_pager`, `next_action_date` = Mon 2026-11-16 |
| 1 | Same day as a call once `office_selling_on = Y`; or Mon 2026-11-16 for an office that said yes to step 0 | One-pager with the first-drop week | Join as one of the five founding offices (`[JOIN ASK]`)? | `status = materials_sent`, `next_action = send_touch_2` (+3 business days) |
| 2 | +3 business days, no reply | The card, in a photo or in words | The same ask | `next_action = send_touch_3` (+4 business days) |
| 3 | +7 business days, no reply | One last check | The same ask, as yes or not now | `next_action = ask_referral` (+5 business days) |
| 4 | +12 business days, no reply | Thanks and one referral ask | One name | `status = not_now`, `next_action = recontact`, [RECONTACT DATE: Tue 2027-01-19] |
| 5 | On a yes (any step) | Intake | Fill in the intake (or answer seven questions) | `yes_in_principle = Y` if not already |
| 6 | Intake done and `attorney_cleared = Y` | The agreement, filled in | Sign, or reply "I agree" | `status = signed` when it comes back; record `agreement_signed_date`, `agreement_file`, `founding_roster_named` |
| 7 | A brand has said yes and passed the seven checks | Approve this brand? | Yes or no for this brand | record the answer in `office_approvals` on that brand's row; once every office on the route has said yes, `office_approvals_complete = Y` on the brand's Clay row (11, step 5b) |
| 8 | Once, the week `llc_formed` turns Y, to every office whose `agreement_signed_date` is before the formation date | The company takes over the agreement (the legal pack's one-line email) | None: a formality | none; note "section 9 email sent <date>" in `call_notes` |

A "no" at any step: 09, H (or I if it is an opt-out). "I need to ask facilities": 09, C.

---

### Step 0 · Weeks 1 to 3: thanks, and nothing to sell yet

The call guide in `calls/` closes discovery calls with "Can I send you a one-pager?" and proposes no date in weeks 1 to 3. This is that email: the discovery one-pager, an honest "not decided yet", and permission to write again.

```message
id: office-conversion-0
side: office
stage: conversion
touch: 0
channel: email
subject: [STEP 0 SUBJECT]
ask: may I write again once it's decided
---
{greeting}

{call_note_hook_line} [DISCOVERY ONE-PAGER LINE]

I'm still finding out whether this is worth building. If it goes ahead, the first drop is planned for January, and only once five offices and the first brands have signed.

May I write to you again in the [FOLLOW-UP WEEK: week of Mon 2026-11-16] with the details?

{SIGNATURE}
```

`[DISCOVERY ONE-PAGER LINE]`: with `discovery_onepager_ready = Y`, "Attached is the one-page description I mentioned." and the PDF attached; otherwise left out. The PDF names the business, so it counts as ready only once `name_decided = Y` (or D has made a name-free version, `onepagers_name_free = Y`); in weeks 1 to 3 this step normally goes without it. The subject, `[STEP 0 SUBJECT]`, follows the same switch: "Thank you, and the one-pager" with the PDF, "Thank you, and what happens next" without it, so the subject never promises an attachment that is not there. A yes: `next_action = send_one_pager`, `next_action_date` = Mon 2026-11-16, then step 1 that day if `office_selling_on = Y`. Once `office_selling_on = Y` this step is refused ("still finding out whether this is worth building" is no longer true): an office you talk to from then on gets step 1.

### Step 1 · The one-pager with the first-drop week

```message
id: office-conversion-1
side: office
stage: conversion
touch: 1
channel: email
subject: [STEP 1 SUBJECT]
ask: be one of the five founding offices
---
{greeting}

[STEP 1 OPENER]

[OFFICE ONE-PAGER LINE] In short: sealed snacks or drinks from emerging brands, free, roughly monthly. You choose the categories and say yes to each brand before it comes. In return: out the day it arrives, two photos, one survey post, help getting five survey answers (no one has to answer), your Tuesday headcount and ten minutes afterwards.

[JOIN ASK]

{SIGNATURE}
```

`[STEP 1 OPENER]`: on the day of the call, `{call_note_hook_line}`; when this follows step 0 weeks later, "As promised, here are the details." (never "today" for a call that was not today).

`[STEP 1 SUBJECT]` (also the thread subject of steps 2 to 5): "The one-pager, and thank you" with `office_onepager_ready = Y`, "The details, and thank you" without it.

`[JOIN ASK]`: while `offices_signed` is under 5, "Would you like {company} to be one of the five founding offices?"; from 5, "Would you like {company} to join for a later drop?" (the standard runs need ten offices, so the path keeps running after the first five sign).

`[OFFICE ONE-PAGER LINE]`: with `office_onepager_ready = Y` (which also waits for `name_decided = Y` and for D to change the page's lead from "one photo" to "two photos"), "Attached is the one-page outline, with the first drop for {company} planned for the [FIRST DROP WEEK: week of Mon 2027-01-11]." and the office one-pager attached (made from `desk-drop-identity/templates/office-one-pager/` with `prepared_for` = the company and `first_drop` = that week). Without it: "The first drop for {company} would be planned for the [FIRST DROP WEEK: week of Mon 2027-01-11]."

"Planned" stays until `drop_date_confirmed = Y`. It is true: the drop goes ahead only if two brands pay, and you say so if asked.

### Step 2 · The card (+3 business days)

```message
id: office-conversion-2
side: office
stage: conversion
touch: 2
channel: email
subject: Re: [STEP 1 SUBJECT]
ask: be one of the five
---
{greeting}

[MOCK CARD LINE] It sits next to the product so your team knows what it is, who made it and what's in it.

[JOIN ASK SHORT]

{SIGNATURE}
```

With `mock_card_photo_ready = Y`, `[MOCK CARD LINE]` is "Attached is a photo of the card on a real pantry shelf." and the photo goes with it (your own photo, no people in it). `[JOIN ASK SHORT]`: while `offices_signed` is under 5, "Shall I put {company} down as one of the five?"; from 5, "Shall I put {company} down for a later drop?".

### Step 3 · One last check (+7 business days)

```message
id: office-conversion-3
side: office
stage: conversion
touch: 3
channel: email
subject: Re: [STEP 1 SUBJECT]
ask: yes, or not now
---
{greeting}

[LAST CHECK LINE] Either answer is helpful.

{SIGNATURE}
```

`[LAST CHECK LINE]`: while `offices_signed` is under 5, "One last check before I fill the five places: is {company} a yes, or is it a not-now?" From 5: "One last check: is {company} a yes for a later drop, or a not-now?"

### Step 4 · Thanks and one referral (+12 business days)

```message
id: office-conversion-4
side: office
stage: conversion
touch: 4
channel: email
subject: Re: [STEP 1 SUBJECT]
ask: one name
---
{greeting}

Thank you again for your time on the call. I'll leave this here for now. Is there one other office nearby whose pantry person I should talk to?

{SIGNATURE}
```

Then `status = not_now`, `next_action = recontact`, `next_action_date` = [RECONTACT DATE: Tue 2027-01-19].

### Step 5 · On a yes: the intake

```message
id: office-conversion-5
side: office
stage: conversion
touch: 5
channel: email
subject: Re: [STEP 1 SUBJECT]
ask: fill in the intake
---
{greeting}

Thank you, that's great news. [INTAKE PARAGRAPH]

{SIGNATURE}
```

`[INTAKE PARAGRAPH]`, with `intake_form_ready = Y`:

> The next step is a short form, about five minutes, with your Tuesday headcount, receiving window and the categories you want: [INTAKE FORM LINK]. I'll turn it into a one-page agreement for you to check and sign. {?[AGREEMENT TIMING LINE]}
>
> Could you fill it in this week?

With `intake_form_ready = N`:

> The next step is seven quick answers, which I'll turn into a one-page agreement for you to check and sign. {?[AGREEMENT TIMING LINE]}
> 1. Roughly how many people are in on a Tuesday?
> 2. Who looks after the pantry and can say yes to a brand (name and title)?
> 3. Who receives deliveries, on which floor, and in what window (for example, Tuesday 9 to 11)?
> 4. Is it a walk-up, a front desk or a loading dock?
> 5. Does your building need a certificate of insurance for deliveries: yes, no or unsure?
> 6. Slack or email for the survey post?
> 7. Which categories would your team like, and any categories or allergens to avoid?
>
> Could you reply with those this week?

`[AGREEMENT TIMING LINE]`: while `attorney_cleared = N`, "The agreement comes by [AGREEMENT DATE: Thu 2026-11-19]." The date is the later of Thu 2026-11-19 and five business days after you send this, so it is never in the past (the day after the attorney hour; desk-drop-legal-pack/03 notes: record the yes, send the intake now, send the cleared page right after the hour). Once cleared, it is left out.

These cover the intake fields the agreement needs (CONTRACTS 6.3): headcount, pantry owner and title, receiving window and floor, receiving type, certificate, survey channel, categories and vetoes. The company, address and contact details come from the Clay row and the call. The budget probe is not in this email: ask it, word for word, on the call or when you deliver the agreement (the call guide in `calls/` has it).

### Step 6 · The agreement

```message
id: office-conversion-6
side: office
stage: conversion
touch: 6
channel: email
subject: The one-page agreement for {company}
ask: sign, or reply "I agree"
---
{greeting}

Here is the one-page agreement, filled in from your answers. Please check the details at the top, tick the two boxes about naming (either way is fine), and sign. If you'd rather not use the signing link, a reply saying "I agree" works too.

In short: no fees, the office isn't responsible for what employees do with the product, and either of us can end it with a week's notice.

Could you sign it this week?

{SIGNATURE}
```

The agreement is `desk-drop-legal-pack/03-office-participation-agreement.md` (rendered PDF in `desk-drop-legal-pack/rendered/`), sent only after `attorney_cleared = Y`. If the hour slips and the office is ready, G's file gives the one line to add about the draft heading. When it comes back: `status = signed`, then the row in `handoff/signed_offices.csv`.

### Step 7 · Approve the brand (before any brand pays)

For an office's first three drops nothing comes unless it says yes (desk-drop-legal-pack/03 section 2). Gate 1 needs both brands approved by all five offices. The plan's order is the match first, then the brand's agreement and payment ("How a campaign runs", steps 3 and 4), so the brand's agreement and invoice (11, steps 6 and 7) wait until every office on the route has said yes: `_render/fill.py` refuses them until five offices have signed and the brand's row has `office_approvals_complete = Y`.

```message
id: office-conversion-7
side: office
stage: conversion
touch: 7
channel: email
subject: A brand for your planned [DROP DATE: Tue 2027-01-12] drop: yes or no?
ask: yes or no for this brand
---
{greeting}

[FIRST BRAND LINE]

From the package: "[ALLERGEN LINE, VERBATIM FROM THE LABEL]"
It is sealed and shelf-stable{?retailer_for_office}.

Is it a yes for {company}?

{SIGNATURE}
```

`[ALLERGEN LINE, VERBATIM FROM THE LABEL]` is the brand's "Contains" line exactly as printed (or the ingredient list, or the single ingredient), the same text the card will carry; check it against each office's vetoes before you send. `{?retailer_for_office}` is ", and people can buy it at {retailer}" when the brand's retailer grade is `seen_on_shelf` or `store_selector`; otherwise it is left out. Record each office's answer and date on the brand's row (`office_approvals` in `handoff/paid_brands.csv` lists the `office_id`s that said yes). When the last office on the route says yes, set `office_approvals_complete = Y` on the brand's Clay row; a no means that office is not on this brand's route (swap in another signed office and ask it).

### Step 8 · The company takes over the agreement (once, after formation)

Most offices sign before the company exists: you sign for the company before it is formed, and section 9 of the agreement says the company takes your place once it is (desk-drop-legal-pack/03, notes, "Signing before the company exists"). The week `llc_formed` turns Y in `04-slot-state.csv`, send this once to every office whose `agreement_signed_date` in `handoff/signed_offices.csv` is before the formation date. It is the legal pack's email, word for word; do not reword it. It is a relationship message to someone who has signed, so it carries no footer (the legal pack's note) and asks nothing. Offices that sign after formation never get it.

```message
id: office-conversion-8
side: office
stage: conversion
touch: 8
channel: email-update
subject: Our participation agreement: a one-line update
ask: none (a formality)
---
{greeting} a quick formality: the company's New York registration is now complete, so as section 9 of our agreement says, it has taken over our agreement from me. Nothing else changes.

[FOUNDER NAME]
```

`{greeting}` is "Hi" and the pantry owner's first name (G's "Hi [Name],"). Then note "section 9 email sent <date>" in the office's `call_notes` in Clay. If an office replies with a question, answer it; nothing in the agreement changes (G's notes).

---

## Changelog

- Round 1 (2026-10-24): drafted from plan Phase 1 "Conversion path" (one-pager the same day with a first-drop week, the card photo at three days, intake and agreement on a yes, thanks and one referral after silence), the match step (explicit approval for the first three drops) and desk-drop-legal-pack/03's sending rules.
- Round 2 (2026-10-24): the agreement date is computed so it is never past (the fallback render printed Nov 19 in an email of Nov 23); the allergen line is quoted, not followed by a second full stop; agreement email wording simplified.
- Round 3 (2026-10-24): step 0 for calls in weeks 1 to 3 (Part B's call guide proposes no date before Gate 0), and step 1 opens with "As promised" when it follows step 0, not "thanks for today" two weeks later; gates refuse steps 1 to 3 before `office_selling_on = Y`.
- Round 4 (2026-10-24): step 1 no longer thanks the person "for today" when it follows step 0 by two weeks.
- Merge (2026-10-24): step 0 says "planned for January" (it said "January at the earliest", false if the stretch drop happens); subjects no longer promise a one-pager that is not attached (`[STEP 0 SUBJECT]`, `[STEP 1 SUBJECT]`); steps 1 and 2 ask for "a later drop" once five offices have signed (`[JOIN ASK]`, `[JOIN ASK SHORT]`).
- Review round 1 (2026-10-24): step 1 lists every office commitment (five survey answers, the Tuesday headcount); the reply version of the intake asks for the pantry owner, the floor and the categories wanted (seven questions); step 7 says "planned" in its subject and states that the brand's agreement waits for every office's yes (`office_approvals_complete`).
- Review round 2 (2026-10-24): step 8, the legal pack's one-line "the company has taken over our agreement" email, word for word, sent once the week `llc_formed` turns Y to every office that signed before formation (desk-drop-legal-pack/03 notes and HANDOFF "To E"); the one-pagers count as ready only once the name is decided (they print it), and the office one-pager also waits for D to say "two photos" in its lead.
- Review round 3 (2026-10-24): step 0 is refused once `office_selling_on = Y`.
