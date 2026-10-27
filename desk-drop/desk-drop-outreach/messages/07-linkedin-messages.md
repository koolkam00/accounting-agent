# 07 · LinkedIn: connection notes and follow-ups, offices and brands

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** The LinkedIn version of the first touch, for rows whose `channel` is `linkedin` (no verified email, or weeks 1 and 2, before cold email from the new domain starts). Discovery and selling versions for both sides.

**The limit that shapes it.** LinkedIn Help, "Personalize invitations to connect" (https://www.linkedin.com/help/linkedin/answer/a563153, opened 2026-10-24, page says "Last updated: 6 months ago"): "You can add a personalized message to up to three connection requests per month. Each message can be up to 200 characters." Premium members can add a note to every request. On a free account, then:

1. **Most rows: send the request with no note.** When they accept, send the "after they accept" message. That message carries the ask.
2. **Three rows a month: send the request with a note.** Use the notes on the three highest-scored LinkedIn-only rows of the month. Every note below is under 200 characters with a 12-letter first name.
3. **One follow-up, five business days after the accepted-request message, if there is no reply.** Then stop. Never a third LinkedIn message in the sequence; the only later message is the month-three recontact (09, "Silence"), at least 60 days on and only with something new to say.

Premium would remove the three-note limit. It is a paid plan: its price was not checked here, and it needs your written yes against the $60-a-month software ceiling. Recommended default: stay on the free account.

**How to fill it in.** Same tokens and slots as 05 and 06 (`03-personalization-fields.csv`, `04-slot-table.csv`). LinkedIn messages carry no email footer, but a "no" on LinkedIn is honored the same way: `do_not_contact = Y` that day, on every channel (desk-drop-legal-pack/02, notes). Record `channel = linkedin`, `sequence` as in 05 and 06 (for example `office-discovery-A`; LinkedIn rows all use variant `A`), the accepted-request message as `touch_1_date` and the follow-up as `touch_2_date`. An invitation on its own is not a touch: while it waits, set `next_action = await_connection` (`tracking/csv/clay_tracking_columns.csv`) and leave `touch_1_date` blank.

**Rules.** No links in any LinkedIn message until someone asks for one. No connection request to anyone with `do_not_contact = Y`. Do not message the same person on LinkedIn and by email in the same week. Weekly invitation limits apply even on free accounts; at ten messages a day across both channels you stay far under them.

---

## Offices · discovery

Until `office_selling_on = Y`. From then the draft maker refuses the note and message 1 ("Questions only, no pitch" is no longer the whole story) and new offices get the selling version below; a discovery thread already begun may finish with message 2.

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
{greeting} thanks for connecting.

I'm researching how offices around {area} stock their pantries. The idea I'm testing: emerging snack brands send sealed product to a few nearby offices, free, and the team says what it thought. Before I build anything, I'd like to hear whether that would help or get in the way at {company}, and I'll share what the other offices tell me, with no names.

Would you have 20 minutes in the next two weeks?
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
ask: accept the request (the note's only job)
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
{greeting} thanks for connecting.

[OFFICE OPENER] Each drop is sealed snacks or drinks from one to three emerging brands, free. You choose the categories and can say no to any brand. In return: out the day it arrives, two photos, a three-question survey for your team with help getting five answers, and ten minutes afterwards.

[OUTLINE ASK]
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

Until `brand_selling_on = Y`. From then the draft maker refuses the note and message 1 ("nothing to sell", "There's nothing to buy yet" would be false) and new brands get the selling version below; a discovery thread already begun may finish with message 2.

```message
id: li-brand-discovery-note
side: brand
stage: discovery
touch: 0
channel: linkedin-note
ask: accept the request (the note's only job)
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
{greeting} thanks for connecting.

I'm asking 15 founders of snack and drink brands how they get people in New York to try their product, and what it costs. The idea I'm testing: sealed product in offices near the stores that carry it, with photos and feedback afterwards. {?retailer_line} There's nothing to buy yet.

Would you give me 20 minutes in the next two weeks?
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
ask: accept the request (the note's only job)
---
{greeting} I'm lining up emerging snack brands for a week in {CLUSTER_SHORT} office pantries, with photos, counts and a report. Happy to share what it costs.
```

```message
id: li-brand-selling-1
side: brand
stage: selling
touch: 1
channel: linkedin
ask: is it worth a 20-minute call
---
{greeting} thanks for connecting.

[ROSTER LINE] [OFFER SHORT] No sales promises.

Is it worth 20 minutes to see whether it fits?
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
- "Questions only, no pitch" is used on LinkedIn, where no commercial-email footer applies. In email the legal footer calls each message a business pitch, so the email copy says "questions only" instead (file 02, "Conflict: the footer and the discovery emails").

## Changelog

- Round 1 (2026-10-24): drafted from plan appendix B and the email sequences; rebuilt around LinkedIn's three-notes-a-month, 200-character limit for free accounts (LinkedIn Help, opened 2026-10-24), which the plan's 300-character message does not fit.
- Round 2 (2026-10-24): paragraph breaks for phone reading; the brand selling note said "I place", untrue before any campaign, now "I'm lining up"; a shorter `[OFFER SHORT]` keeps the brand message under 600 characters.
- Merge (2026-10-24): the brand discovery message now carries the evidence-graded store sentence, as the email does (run on A's real rows it said nothing about the brand beyond a first name); an invitation alone sets `next_action = await_connection` (the tracker's allowed list); the footer conflict is cited by its heading.
- Review round 1 (2026-10-24): the office selling message names the five survey answers; "I'm asking 15 founders"; `[OFFER SHORT]` keeps "paid before you ship", the freight and the founding note term; the stop rule names the month-three recontact.
- Review round 2 (2026-10-24): the office discovery message offers the no-names summary of what the other offices said (05, the promise rule); `[OFFER SHORT]` states the 10% reserve; LinkedIn brand selling stays under 600 characters.
- Review round 3 (2026-10-24): the discovery note and message 1 are refused once that side sells; `[OUTLINE ASK]` in the office selling message.
