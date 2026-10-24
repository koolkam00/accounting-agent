# 06 · Brand cold emails: discovery and selling

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Three emails to a founder or marketing lead at an emerging snack or drink brand, in two versions. The discovery version (weeks 1 to 3) asks for a 20-minute research call and sells nothing: no price, no offer, no roster. The selling version (once two or more offices have said yes) states the offer, the price and what the report can and cannot show, and asks for a 20-minute call.

**When it is used.** Each weekday, for the brand rows in today's daily view whose `channel` is `email` and whose `email_status` is `verified`, once `domain_ready = Y` (`04-slot-state.csv`). Brands that Startup CPG members might recognize get the same email: the community is never named or used as a hook (12, rules).

**How to fill it in.** As in 05: `{token}` from the Clay Brands row with its fallback (`03-personalization-fields.csv`), `{?token}` left out when empty or stale, `[SLOT]` from `04-slot-state.csv` with the words in `04-slot-table.csv`, `{SIGNATURE}` from file 02.

---

## The rules every email here follows

The seven rules at the top of 05 apply unchanged (one ask, nothing linked or attached in touch 1, touches at day 0, +3 and +7 business days in one thread, any reply stops it, one variant per row, three emails at most, nothing claimed the tracker does not show). Two more for brands:

8. **The retailer sentence never outruns its evidence.** `seen_on_shelf` (set only by you, after you have seen it) may say "on the shelf". `store_selector` says the store's own page lists it. `brand_claim` says their locator lists it. `unverified` says nothing.
9. **No sales language in either version.** No guarantee, lift, ROI, conversions, acquisition or "new customers". The selling version says in plain words that the report does not show whether anyone bought because of it.

`sequence` values: `brand-discovery-A`, `brand-discovery-B`, `brand-selling-A`, `brand-selling-B`. The variant rule is the one in 05.

---

## Part 1 · Discovery version (weeks 1 to 3, Mon 2026-10-26 to Fri 2026-11-13, derived)

| Touch | Sent | Subject | The one ask |
| --- | --- | --- | --- |
| 1 | Day 0 | A or B below | A 20-minute research call |
| 2 | Day 0 + 3 business days | Re: (touch 1 subject) | One line by reply instead |
| 3 | Day 0 + 7 business days | Re: (touch 1 subject) | Would they like the anonymous summary |

```message
id: brand-discovery-1
side: brand
stage: discovery
touch: 1
channel: email
subject_A: How do people in New York get to try {company}?
subject_B: 20 minutes on sampling in New York?
ask: a 20-minute research call
---
{greeting}

{?why_now_hook}

I'm talking to 15 founders of snack and drink brands about how they get people in New York to try their product, and what it costs them. {?retailer_line}

The idea I'm testing is putting sealed product in offices near the stores that carry it, with photos and employee feedback afterwards. Before I build it, I want to hear what has worked for you and what hasn't.

There's nothing to buy yet; I'm asking questions. Would you give me 20 minutes in the next two weeks?

{SIGNATURE}
```

```message
id: brand-discovery-2
side: brand
stage: discovery
touch: 2
channel: email
subject: Re: (touch 1 subject)
ask: one line by reply
---
{greeting}

If a call is too much, one line by reply would help: what did your last sampling spend in New York get you that you could actually count?

{SIGNATURE}
```

```message
id: brand-discovery-3
side: brand
stage: discovery
touch: 3
channel: email
subject: Re: (touch 1 subject)
ask: would they like the summary
---
{greeting}

I'll stop writing after this. I'm putting what these founders tell me into a one-page summary, with no names or brands in it. Would you like a copy when it's done?

{SIGNATURE}
```

Touch 3 is a promise. Send it only if you will write and send the summary (the plan's Gate 0 deliverable, "a one-page summary of what you heard", stripped of names). A yes: set `reply_type = yes`, `next_action = recontact`, `next_action_date` = Fri 2026-11-20, and note "wants summary" in `call_notes`.

---

## Part 2 · Selling version (from `brand_selling_on = Y`)

Unlocked when the brand-side Gate 0 pass is recorded and at least two offices have said yes in principle (`offices_yes >= 2`). Before that, brands get the discovery version, because the selling email's main fact is the office roster. A brand that took a discovery call never gets this sequence: it is in the post-call path (11).

| Touch | Sent | Subject | The one ask |
| --- | --- | --- | --- |
| 1 | Day 0 | A or B below | Is it worth a 20-minute call |
| 2 | Day 0 + 3 business days | Re: (touch 1 subject) | May I send the one-page proposal |
| 3 | Day 0 + 7 business days | Re: (touch 1 subject) | When to check back |

```message
id: brand-selling-1
side: brand
stage: selling
touch: 1
channel: email
subject_A: {company} in Flatiron office pantries for a week
subject_B: Office sampling near {CLUSTER_SHORT}: what it costs and what you get
ask: is it worth a 20-minute call
---
{greeting}

{?retailer_line} [ROSTER LINE]

[OFFER LINE] Nothing is promised about sales: the report says what happened, and what it can't show.

Is it worth 20 minutes to see whether it fits?

{SIGNATURE}
```

```message
id: brand-selling-2
side: brand
stage: selling
touch: 2
channel: email
subject: Re: (touch 1 subject)
ask: may I send the proposal
---
{greeting}

In case price is the first question: one in-store demo shift, a single demonstrator for four to eight hours at one store, runs about $300 to $700 (T-ROC's 2026 pricing guide). This is a week in office pantries, seen by the same people each day, with photos, counts and their comments in a one-page report.

Should I send the one-page proposal, with the offices by industry and size and a map of the stores near them?

{SIGNATURE}
```

```message
id: brand-selling-3
side: brand
stage: selling
touch: 3
channel: email
subject: Re: (touch 1 subject)
ask: when to check back
---
{greeting}

Last note from me. [FOUNDING LINE] If the timing is wrong, when would be a better time to check back?

{SIGNATURE}
```

When `founding_taken = 3`, `[FOUNDING LINE]` becomes: "The next drop is [NEXT DROP DATE: Tue 2027-02-09]." and touch 1 carries the standard `[OFFER LINE]` ($1,500 for ten offices). Source for the demo price: T-ROC, "In-store demo services" pricing guide, https://trocglobal.com/in-store-demo-services/, article dated 2026-05-06, opened 2026-10-24: "about $300-700 per 4-8 hour shift with one demonstrator". If that page changes, change the sentence or drop it.

---

## Why the copy reads this way

- **The CPG founder pitched by every sampling vendor** has heard "we work with" and "drive trial" a hundred times. So the discovery email says what it is (research, nothing to buy yet), names a real store near them only when there is evidence, and asks a question they have an opinion on. The selling email puts the price, the unit count, the timing and the limits in the first email, because a founder decides whether to read on from those four facts, and says outright that there is no sales promise.
- **The deliverability specialist**: no link, no attachment, no price in a subject line except as plain words, three touches, in-thread follow-ups. The `$` sign appears only in the body.
- **Honesty**: the roster sentence comes from the tracker in one of three exact forms (said yes, signed so far, five signed), with a headcount only from offices' own intake numbers. The founding price's three places are stated as a count, never as a countdown.

## Changelog

- Round 1 (2026-10-24): drafted both versions from plan appendix C, the Phase 0 brand guide and the Phase 2 objection answers; demo price checked against T-ROC's page (four to eight hours, not the plan's "a few hours").
