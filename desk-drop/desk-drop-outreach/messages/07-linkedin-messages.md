# 07 · LinkedIn: connection notes and follow-ups, offices and brands

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** The LinkedIn version of the first touch, for rows whose `channel` is `linkedin` (no verified email, or week one before the new domain is warm). Discovery and selling versions for both sides.

**The limit that shapes it.** LinkedIn Help, "Personalize invitations to connect" (https://www.linkedin.com/help/linkedin/answer/a563153, opened 2026-10-24, page says "Last updated: 6 months ago"): "You can add a personalized message to up to three connection requests per month. Each message can be up to 200 characters." Premium members can add a note to every request. On a free account, then:

1. **Most rows: send the request with no note.** When they accept, send the "after they accept" message. That message carries the ask.
2. **Three rows a month: send the request with a note.** Use the notes on the three highest-scored LinkedIn-only rows of the month. Every note below is under 200 characters with a 12-letter first name.
3. **One follow-up, five business days after the accepted-request message, if there is no reply.** Then stop. Never a third LinkedIn message.

Premium would remove the three-note limit. It is a paid plan: its price was not checked here, and it needs your written yes against the $60-a-month software ceiling. Recommended default: stay on the free account.

**How to fill it in.** Same tokens and slots as 05 and 06 (`03-personalization-fields.csv`, `04-slot-table.csv`). LinkedIn messages carry no email footer, but a "no" on LinkedIn is honored the same way: `do_not_contact = Y` that day, on every channel (desk-drop-legal-pack/02, notes). Record `channel = linkedin`, `sequence` as in 05 and 06 (for example `office-discovery-A`; LinkedIn rows all use variant `A`), the accepted-request message as `touch_1_date` and the follow-up as `touch_2_date`.

**Rules.** No links in any LinkedIn message until someone asks for one. No connection request to anyone with `do_not_contact = Y`. Do not message the same person on LinkedIn and by email in the same week. Weekly invitation limits apply even on free accounts; at ten messages a day across both channels you stay far under them.

---

## Offices · discovery

```message
id: li-office-discovery-note
side: office
stage: discovery
touch: 0
channel: linkedin-note
ask: accept the request (the note's only job)
---
{greeting} I'm researching how offices around {CLUSTER_SHORT} stock their pantries and would value your view. Questions only, no pitch.
```

```message
id: li-office-discovery-1
side: office
stage: discovery
touch: 1
channel: linkedin
ask: a 20-minute research call
---
{greeting} thanks for connecting. I'm researching how offices around {area} stock their pantries. The idea I'm testing: emerging snack brands send sealed product to a few nearby offices, free, and the team says what it thought. Before I build anything, I'd like to hear whether that would help or get in the way at {company}. Would you have 20 minutes in the next two weeks?
```

```message
id: li-office-discovery-2
side: office
stage: discovery
touch: 2
channel: linkedin
ask: one line by reply
---
{greeting} if a call is too much, one line would help just as much: when a brand offers {company} free product today, what happens to it?
```

## Offices · selling (from `office_selling_on = Y`)

```message
id: li-office-selling-note
side: office
stage: selling
touch: 0
channel: linkedin-note
ask: accept the request
---
{greeting} I'm picking five {CLUSTER_SHORT} offices to get free drops from emerging snack brands, roughly monthly. You choose what comes. Happy to share the details.
```

```message
id: li-office-selling-1
side: office
stage: selling
touch: 1
channel: linkedin
ask: may I send the one-page outline
---
{greeting} thanks for connecting. [OFFICE OPENER] Each drop is sealed snacks or drinks from one to three emerging brands, free. You choose the categories and can say no to any brand. In return: out the day it arrives, two photos, a three-question survey for your team, and ten minutes afterwards. Could I send you the one-page outline?
```

```message
id: li-office-selling-2
side: office
stage: selling
touch: 2
channel: linkedin
ask: who decides
---
{greeting} one last note. If the pantry is someone else's call at {company}, who should I ask?
```

## Brands · discovery

```message
id: li-brand-discovery-note
side: brand
stage: discovery
touch: 0
channel: linkedin-note
ask: accept the request
---
{greeting} I'm asking snack and drink founders how they get New Yorkers to try their product. I'd value 20 minutes of yours. Questions only, nothing to sell.
```

```message
id: li-brand-discovery-1
side: brand
stage: discovery
touch: 1
channel: linkedin
ask: a 20-minute research call
---
{greeting} thanks for connecting. I'm talking to 15 founders of snack and drink brands about how they get people in New York to try their product, and what it costs. The idea I'm testing is putting sealed product in offices near the stores that carry it, with photos and feedback afterwards. There's nothing to buy yet. Would you give me 20 minutes in the next two weeks?
```

```message
id: li-brand-discovery-2
side: brand
stage: discovery
touch: 2
channel: linkedin
ask: one line by reply
---
{greeting} if a call is too much, one line would help: what did your last sampling spend in New York get you that you could actually count?
```

## Brands · selling (from `brand_selling_on = Y`)

```message
id: li-brand-selling-note
side: brand
stage: selling
touch: 0
channel: linkedin-note
ask: accept the request
---
{greeting} I place emerging snack brands in {CLUSTER_SHORT} office pantries for a week, with photos, counts and a report. Could I share what it costs?
```

```message
id: li-brand-selling-1
side: brand
stage: selling
touch: 1
channel: linkedin
ask: is it worth a 20-minute call
---
{greeting} thanks for connecting. [ROSTER LINE] [OFFER LINE] No sales promises: the report says what happened and what it can't show. Is it worth 20 minutes to see whether it fits?
```

```message
id: li-brand-selling-2
side: brand
stage: selling
touch: 2
channel: linkedin
ask: when to check back
---
{greeting} last note from me. [FOUNDING LINE] If the timing is wrong, when would be a better time to check back?
```

---

## Why the copy reads this way

- A note has one job: get the request accepted. So it says who you are and why them in one breath, and asks nothing else. The real ask waits for the accepted-request message.
- A LinkedIn reader sees the first line in the notification, so every message opens with their name and the reason, not with "I hope you're well".
- "Questions only, no pitch" is used on LinkedIn, where no commercial-email footer applies. In email the legal footer calls each message a business pitch, so the email copy says "questions only" instead (file 02, conflict 1).

## Changelog

- Round 1 (2026-10-24): drafted from plan appendix B and the email sequences; rebuilt around LinkedIn's three-notes-a-month, 200-character limit for free accounts (LinkedIn Help, opened 2026-10-24), which the plan's 300-character message does not fit.
