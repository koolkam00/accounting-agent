# 05 · Office cold emails: discovery and selling

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Three emails to the person who runs an office's pantry, in two versions. The discovery version (weeks 1 to 3) asks for a 20-minute research call and sells nothing. The selling version (from the office-side Gate 0 pass) asks to send the one-page outline for the founding-office roster.

**When it is used.** Each weekday, for the office rows in today's daily view whose `channel` is `email` and whose `email_status` is `verified`. Not before `domain_ready = Y` in `04-slot-state.csv` (the sending guide in `sending/` decides when the new domain is warm; until then the office side runs on warm intros, LinkedIn and walk-ins, files 07 and 08).

**How to fill it in.** Every `{token}` comes from the Clay Offices row and has a fallback (`03-personalization-fields.csv`). `{?token}` is a sentence that is left out when its field is empty or stale. Every `[SLOT]` is set by the tracker state in `04-slot-state.csv`; `04-slot-table.csv` says which words to use at which state. `[FOUNDER NAME]`, `[PHONE]`, `[EMAIL]` and `[POSTAL ADDRESS]` stay as placeholders until you fill them once in your signature. `{SIGNATURE}` is the outreach signature with the legal pack's footer (file 02). To make ten ready-to-paste drafts from the daily view instead of typing, see `_render/HOW-TO-RUN.md`.

---

## The rules every email here follows

1. One ask per email. The ask is the last sentence and is the only question.
2. No link, no attachment, no picture in touch 1, ever (sending guide). The one-pager goes only to someone who asks for it.
3. Touch 2 is sent 3 business days after touch 1, touch 3 is sent 7 business days after touch 1, both as replies in the same thread (so "Re:" is true). Business days skip weekends and the federal holidays in CONTRACTS section 3. No new first touches on Wed 2026-11-25 (the day before Thanksgiving; follow-ups due that day still go), nothing at all on Fri 2026-11-27, and nothing between Fri 2026-12-18 and Mon 2027-01-04; anything due then goes out on the next sending day (the sending guide's warm-up calendar in `sending/` has the same days).
4. Any reply stops the sequence. The reply playbook (09) takes over.
5. A row keeps one subject variant (`A` or `B`) for all three touches. Record it in Clay as `sequence` = `office-discovery-A`, `office-discovery-B`, `office-selling-A` or `office-selling-B`, and the send dates in `touch_1_date`, `touch_2_date`, `touch_3_date`.
6. Never more than three emails without a reply. After touch 3, silence parks the row (09, "Silence").
7. Nothing is claimed that the tracker does not show today: no offices signed until `offices_signed` says so, no brand named until one qualifies, no drop date called "set" until `drop_date_confirmed = Y`.

**Variants and how the winner is picked.** Give alternate rows variant A and B as they enter the daily view. Bodies are the same; only the touch 1 subject differs. Compare replies, not opens (open tracking is off: it hurts a new domain and Apple Mail inflates it). After 40 touch 1 emails per variant, keep the one with more replies only if it has at least 5 replies and at least twice the other's count; otherwise keep both running. At 75 office emails over three weeks the test is weak, so treat any winner as a hint, not a result.

---

## Part 1 · Discovery version (weeks 1 to 3, Mon 2026-10-26 to Fri 2026-11-13, derived)

| Touch | Sent | Subject | The one ask |
| --- | --- | --- | --- |
| 1 | Day 0 | A or B below | A 20-minute research call |
| 2 | Day 0 + 3 business days | Re: (touch 1 subject) | One line by reply instead of a call |
| 3 | Day 0 + 7 business days | Re: (touch 1 subject) | Who runs the pantry, if not them |

```message
id: office-discovery-1
side: office
stage: discovery
touch: 1
channel: email
subject_A: Question about the pantry at {company}
subject_B: How does the pantry at {company} work?
ask: a 20-minute research call
---
{greeting}

{?why_now_hook}

I'm researching how offices around {area} stock their pantries, and I'd like to hear how it works at {company}.

The idea I'm testing: emerging snack and drink brands send sealed product to a few nearby offices, free, and the team says what it thought. Before I build anything, I want to know whether that would help you or just add to your vendor email.

It's questions only, about 20 minutes. Would you have time in the next two weeks?

{SIGNATURE}
```

```message
id: office-discovery-2
side: office
stage: discovery
touch: 2
channel: email
subject: Re: (touch 1 subject)
ask: one line by reply
---
{greeting}

If a call is too much, one line by reply would help just as much: when a brand offers {company} free product today, what happens to it?

{SIGNATURE}
```

```message
id: office-discovery-3
side: office
stage: discovery
touch: 3
channel: email
subject: Re: (touch 1 subject)
ask: who runs the pantry
---
{greeting}

I'll stop here. If someone else looks after the pantry at {company}, could you point me to them?

{SIGNATURE}
```

---

## Part 2 · Selling version (from `office_selling_on = Y`)

Unlocked by the office-side Gate 0 pass (Fri 2026-11-13, derived, founder to confirm) or your own decision to recruit. Use it for offices that have not had the discovery version. An office that took a discovery call never gets this sequence: it is already in the post-call path (10).

| Touch | Sent | Subject | The one ask |
| --- | --- | --- | --- |
| 1 | Day 0 | A or B below | May I send the one-page outline |
| 2 | Day 0 + 3 business days | Re: (touch 1 subject) | The same ask, with what arrives and what never happens |
| 3 | Day 0 + 7 business days | Re: (touch 1 subject) | Who decides, if not them |

```message
id: office-selling-1
side: office
stage: selling
touch: 1
channel: email
subject_A: Emerging snack brands for the pantry at {company}
subject_B: New snack brands for {company}, you choose what comes
ask: may I send the one-page outline
---
{greeting}

[OFFICE OPENER] {?[OFFICE PROGRESS LINE]}

Each drop is sealed snacks or drinks from one to three emerging brands, free, roughly monthly. You choose the categories and can say no to any brand. What we ask in return: put it out the day it arrives, send two photos, post a three-question survey to your team, and give me ten minutes afterwards.

Could I send you the one-page outline?

{SIGNATURE}
```

```message
id: office-selling-2
side: office
stage: selling
touch: 2
channel: email
subject: Re: (touch 1 subject)
ask: may I send the one-page outline
---
{greeting}

What arrives is one labeled case and a 5 by 7 inch card for the shelf: the brand's name, two sentences about it, the allergen line copied from the package, and a QR code to the survey. Nothing is ever charged to {company}, nothing is asked about your employees, and you can leave with a week's notice.

Shall I send the outline?

{SIGNATURE}
```

```message
id: office-selling-3
side: office
stage: selling
touch: 3
channel: email
subject: Re: (touch 1 subject)
ask: who decides
---
{greeting}

I'll stop here. If the pantry is someone else's call at {company}, who should I ask?

{SIGNATURE}
```

---

## Why the copy reads this way (the three critics)

- **The office manager who deletes forty vendor emails a day** reads the subject and the first line only. So the subject names their company and their pantry, not a product, and the first line says why it is them: a neighbor, researching their street. The selling version lists every ask up front (out the day it arrives, two photos, one survey post, ten minutes), because "what's the catch" is the question that gets an email deleted. It says two photos, not the plan's "one photo": the participation agreement asks for two (desk-drop-legal-pack/03).
- **The deliverability specialist** wants no "free" in a cold subject, no link, attachment or picture in any cold touch, short plain text, replies in-thread, and a hard stop at three. All hold. "Free" appears in the body only, and touch 2 describes the card in words rather than attaching a photo.
- **Honesty.** "Planned for" is used until both brands have paid and all five offices have approved them; the opener changes once five offices have signed; nothing claims a roster, a brand or a date the tracker does not hold.

## Changelog

- Round 1 (2026-10-24): drafted both versions from plan appendix A and the Phase 0 and Phase 1 pitch lines, with the deliverability rules from `sending/` (Part B's note) and the agreement's two photos.
- Round 2 (2026-10-24): subjects rewritten so the company fallback reads ("the pantry at your office", not "the your office pantry", seen in the fallback render); touch 2 says what arrives once instead of twice.
- Round 4 (2026-10-24): send-day rules matched to the sending guide's warm-up calendar (no new first touches on Wed 2026-11-25).
