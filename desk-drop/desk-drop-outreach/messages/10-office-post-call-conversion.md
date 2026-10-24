# 10 · Office post-call conversion: from a good call to a signed office

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** The emails that take an office from a good call to a signed participation agreement, a completed intake and an approved first brand. This is the plan's Phase 1 conversion path, step by step, with one ask per email.

**When it is used.** The day of any office call that ended with "can I send you a one-pager?" or a yes in principle (the call guide in `calls/` ends that way). Weeks 1 to 5 for the one-pager; agreements only once `attorney_cleared = Y` (the attorney hour is held by Wed 2026-11-18, derived, founder to confirm). Then the brand-approval email for each office, before any brand pays.

**How to fill it in.** Tokens and slots as in 03 and 04. `{call_note_hook}` is the line you wrote within ten minutes of the call. Every email carries `{SIGNATURE}` (file 02). These go to someone who has talked to you, so attachments are fine here.

`sequence` = `office-conversion-A`. Status moves, in Clay: `call_done` → `yes_in_principle` (they said yes and named a pantry owner and a receiving window) → `materials_sent` (one-pager sent) → `signed` (agreement signed, intake complete). A signed office becomes a row in `handoff/signed_offices.csv` (Part B's handoff, CONTRACTS 6.4).

---

## The path

| Step | When | Email | The one ask | Clay |
| --- | --- | --- | --- | --- |
| 1 | Same day as the call | One-pager with the first-drop week | Join as one of the five founding offices? | `status = materials_sent`, `next_action = send_touch_2` (+3 business days) |
| 2 | +3 business days, no reply | The card, in a photo or in words | The same ask | `next_action = send_touch_3` (+4 business days) |
| 3 | +7 business days, no reply | One last check | The same ask, as yes or not now | `next_action = ask_referral` (+5 business days) |
| 4 | +12 business days, no reply | Thanks and one referral ask | One name | `status = not_now`, `next_action = recontact`, [RECONTACT DATE: Tue 2027-01-19] |
| 5 | On a yes (any step) | Intake | Fill in the intake (or answer six questions) | `yes_in_principle = Y` if not already |
| 6 | Intake done and `attorney_cleared = Y` | The agreement, filled in | Sign, or reply "I agree" | `status = signed` when it comes back; record `agreement_signed_date`, `agreement_file`, `founding_roster_named` |
| 7 | A brand has said yes and passed the seven checks | Approve this brand? | Yes or no for this brand | record the answer in `office_approvals` on that brand's paid-brands row |

A "no" at any step: 09, H (or I if it is an opt-out). "I need to ask facilities": 09, C.

---

### Step 1 · The one-pager, the same day

```message
id: office-conversion-1
side: office
stage: conversion
touch: 1
channel: email
subject: The one-pager, and thank you
ask: be one of the five founding offices
---
{greeting}

{call_note_hook_line}

Attached is the one-page outline, with {company}'s first drop planned for the [FIRST DROP WEEK: week of Mon 2027-01-11]. In short: sealed snacks or drinks from emerging brands, free, roughly monthly. You choose the categories and say yes to each brand before it comes. In return: out the day it arrives, two photos, one survey post and ten minutes afterwards.

Would you like {company} to be one of the five founding offices?

{SIGNATURE}
```

Attach the office one-pager (`office_onepager_ready = Y`; made from `desk-drop-identity/templates/office-one-pager/` with `prepared_for` = the company and `first_drop` = the week above). If it is not ready, leave out "Attached is the one-page outline, with" and write "{company}'s first drop would be planned for the [FIRST DROP WEEK]."

"Planned" stays until `drop_date_confirmed = Y`. It is true: the drop goes ahead only if two brands pay, and you can say so if asked.

### Step 2 · The card (+3 business days)

```message
id: office-conversion-2
side: office
stage: conversion
touch: 2
channel: email
subject: Re: The one-pager, and thank you
ask: be one of the five
---
{greeting}

[MOCK CARD LINE] It sits next to the product so your team knows what it is, who made it and what's in it.

Shall I put {company} down as one of the five?

{SIGNATURE}
```

With `mock_card_photo_ready = Y`, `[MOCK CARD LINE]` is "Attached is a photo of the card on a real pantry shelf." and the photo goes with it (your own photo, no people in it).

### Step 3 · One last check (+7 business days)

```message
id: office-conversion-3
side: office
stage: conversion
touch: 3
channel: email
subject: Re: The one-pager, and thank you
ask: yes, or not now
---
{greeting}

One last check before I fill the five places: is {company} a yes, or is it a not-now? Either answer is helpful.

{SIGNATURE}
```

"Before I fill the five places" is true only while fewer than five offices have signed. At five, write "One last check: is {company} a yes for a later drop, or a not-now?"

### Step 4 · Thanks and one referral (+12 business days)

```message
id: office-conversion-4
side: office
stage: conversion
touch: 4
channel: email
subject: Re: The one-pager, and thank you
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
subject: Re: The one-pager, and thank you
ask: fill in the intake
---
{greeting}

Thank you, that's great news. The next step is a short form, about five minutes, with your Tuesday headcount, receiving window and the categories you want: [INTAKE FORM LINK]. I'll turn it into a one-page agreement for you to check and sign.

Could you fill it in this week?

{SIGNATURE}
```

**If `intake_form_ready = N`**, replace the second paragraph and the ask with:

> The next step is six quick answers, which I'll turn into a one-page agreement for you to check and sign:
> 1. Roughly how many people are in on a Tuesday?
> 2. Who receives deliveries, and in what window (for example, Tuesday 9 to 11)?
> 3. Is it a walk-up, a front desk or a loading dock?
> 4. Does your building need a certificate of insurance for deliveries? (yes, no or unsure)
> 5. Slack or email for the survey post?
> 6. Any categories or allergens you want us to avoid?
>
> Could you reply with those this week?

These are the `office_intake` fields (CONTRACTS 6.3). The budget probe is not in this email: ask it, word for word, on the call or when you deliver the agreement (the call guide in `calls/` has it).

**If `attorney_cleared = N`** add one line before the ask: "The agreement comes by [AGREEMENT DATE: Thu 2026-11-19]." (the day after the attorney hour; desk-drop-legal-pack/03 notes: record the yes, send the intake now, send the cleared page right after the hour).

### Step 6 · The agreement

```message
id: office-conversion-6
side: office
stage: conversion
touch: 6
channel: email
subject: {company}'s one-page agreement
ask: sign, or reply "I agree"
---
{greeting}

Here is the one-page agreement, filled in from your answers. Please check the details at the top, tick the two boxes about naming (either way is fine), and sign. If you'd rather not use the signing link, a reply saying "I agree" works too.

It asks no fees of {company}, holds the office responsible for nothing employees do with the product, and either of us can end it with a week's notice.

Could you sign it this week?

{SIGNATURE}
```

The agreement is `desk-drop-legal-pack/03-office-participation-agreement.md` (rendered PDF in `desk-drop-legal-pack/rendered/`), sent only after `attorney_cleared = Y`. If the hour slips and the office is ready, G's file gives the one line to add about the draft heading. When it comes back: `status = signed`, then the row in `handoff/signed_offices.csv`.

### Step 7 · Approve the brand (before any brand pays)

For an office's first three drops nothing comes unless it says yes (desk-drop-legal-pack/03 section 2). Gate 1 needs both brands approved by all five offices.

```message
id: office-conversion-7
side: office
stage: conversion
touch: 7
channel: email
subject: A brand for your [DROP DATE: Tue 2027-01-12] drop: yes or no?
ask: yes or no for this brand
---
{greeting}

[FIRST BRAND LINE]

What's in it, from the package: [ALLERGEN LINE, VERBATIM FROM THE LABEL]. It is sealed and shelf-stable{?retailer_for_office}.

Is it a yes for {company}?

{SIGNATURE}
```

`[ALLERGEN LINE, VERBATIM FROM THE LABEL]` is the brand's "Contains" line exactly as printed (or the ingredient list, or the single ingredient), the same text the card will carry; check it against each office's vetoes before you send. `{?retailer_for_office}` is ", and people can buy it at {retailer}" when the brand's retailer grade is `seen_on_shelf` or `store_selector`; otherwise it is left out. Record each office's answer and date on the brand's row (`office_approvals` in `handoff/paid_brands.csv` lists the `office_id`s that said yes).

---

## Changelog

- Round 1 (2026-10-24): drafted from plan Phase 1 "Conversion path" (one-pager the same day with a first-drop week, the card photo at three days, intake and agreement on a yes, thanks and one referral after silence), the match step (explicit approval for the first three drops) and desk-drop-legal-pack/03's sending rules.
