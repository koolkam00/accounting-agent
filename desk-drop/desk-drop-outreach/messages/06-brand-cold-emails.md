# 06 · Brand cold emails: discovery and selling

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** Three emails to a founder or marketing lead at an emerging snack or drink brand, in two versions. The discovery version (weeks 1 to 3) asks for a 20-minute research call and sells nothing: no price, no offer, no roster. The selling version (once two or more offices have said yes) states the offer, the price and what the report can and cannot show, and asks for a 20-minute call.

**When it is used.** Each weekday, for the brand rows in today's daily view whose `channel` is `email` and whose `email_status` is `verified`, once `domain_ready = Y` (`04-slot-state.csv`; Mon 2026-11-09 at the earliest, `sending/sending-setup.md` section 0). Brands that Startup CPG members might recognize get the same email: the community is never named or used as a hook (12, rules).

**How to fill it in.** As in 05: `{token}` from the Clay Brands row with its fallback (`03-personalization-fields.csv`), `{?token}` left out when empty or stale, `[SLOT]` from `04-slot-state.csv` with the words in `04-slot-table.csv`, `{SIGNATURE}` from file 02.

---

## The rules every email here follows

The seven rules at the top of 05 apply unchanged (one ask, nothing linked or attached in touch 1, touches at day 0, +3 and +7 business days in one thread, any reply stops it, one variant per row, three emails at most in a sequence with one month-three recontact as the only exception, nothing claimed the tracker does not show). Two more for brands:

8. **The retailer sentence never outruns its evidence.** `seen_on_shelf` (set only by you, after you have seen it) may say "on the shelf". `store_selector` says the store's own page lists it. `brand_claim` says their locator lists it. `unverified` says nothing.
9. **No sales language in either version.** No guarantee, lift, ROI, conversions, acquisition or "new customers". The selling version says in plain words that the report does not show whether anyone bought because of it (touch 2: "No sales promises"; objection J4).

`sequence` values: `brand-discovery-A`, `brand-discovery-B`, `brand-selling-A`, `brand-selling-B`. The variant rule is the one in 05 (the same rule as `sending/sending-setup.md` section 6.4).

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

I'm asking 15 founders of snack and drink brands how they get people in New York to try their product, and what it costs them.

The idea I'm testing: sealed product in offices near the stores that carry it, with photos and employee feedback afterwards. {?retailer_line}

There's nothing to buy yet; I'm asking questions. Would you give me 20 minutes in the next two weeks to hear what has worked for you?

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

Unlocked when the brand-side Gate 0 pass is recorded and at least two offices have said yes in principle (`offices_yes >= 2`). The roster sentence also says, while fewer than five offices have signed, that no brand is invoiced until five have: the plan builds the offices "before any brand is asked for money" (Phase 1). Before that, brands get the discovery version, because the selling email's main fact is the office roster. From `brand_selling_on = Y` every new brand gets this version: the draft maker refuses the discovery touch 1, whose "There's nothing to buy yet" is then false. A discovery thread already begun finishes with its own touches 2 and 3, which say nothing about buying. A brand that took a discovery call never gets this sequence: it is in the post-call path (11).

| Touch | Sent | Subject | The one ask |
| --- | --- | --- | --- |
| 1 | Day 0 | A or B below | Is it worth a 20-minute call |
| 2 | Day 0 + 3 business days | Re: (touch 1 subject) | May I send the one-page proposal, or the details while the proposal does not count as ready (`[PROPOSAL ASK]`) |
| 3 | Day 0 + 7 business days | Re: (touch 1 subject) | When to check back |

```message
id: brand-selling-1
side: brand
stage: selling
touch: 1
channel: email
subject_A: {company} in {CLUSTER_SHORT} office pantries for a week
subject_B: Office sampling near {CLUSTER_SHORT}: what it costs and what you get
ask: is it worth a 20-minute call
---
{greeting}

[ROSTER LINE] {?retailer_line}

[OFFER LINE]

Is it worth a 20-minute call?

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

One in-store demo (one person, four to eight hours, one store) runs about $300 to $700, per T-ROC's 2026 pricing guide. This is a week in office pantries, in front of the same teams while it lasts, with photos, counts and comments in a report. No sales promises: the report says what it can't show.

[PROPOSAL ASK]

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

After [LAST OFFER DATE: Mon 2026-11-30] a brand new to the pipeline cannot make campaign zero: its yes, the office approvals, a signature and payment cannot all land before the asked ship-by date (11, "The last day to offer"). Put [NEXT DROP DATE: Tue 2027-02-09] in `[OFFER LINE]` instead (the draft maker refuses the January date in a touch 1 after Mon 2026-11-30, and in a follow-up after Thu 2026-12-03). When `founding_taken = 3`, `[FOUNDING LINE]` becomes: "The next drop is [NEXT DROP DATE: Tue 2027-02-09]." and touch 1 carries the standard `[OFFER LINE]` ($1,500 for ten offices). Source for the demo price: T-ROC, "In-store demo services" pricing guide, https://trocglobal.com/in-store-demo-services/, article dated 2026-05-06, opened 2026-10-24: "about $300-700 per 4-8 hour shift with one demonstrator". If that page changes, change the sentence or drop it.

---

## Why the copy reads this way

- **The CPG founder pitched by every sampling vendor** has heard "we work with" and "drive trial" a hundred times. Touch 1 also carries the founding price's one condition (a short note and a case study, only if the campaign runs as promised), because a term first met in the agreement reads as a trick. So the discovery email says what it is (research, nothing to buy yet), names a real store near them only when there is evidence, and asks a question they have an opinion on. The selling email puts the price, the unit count, the timing and the limits in the first email, because a founder decides whether to read on from those four facts, and says outright that there is no sales promise.
- **The deliverability specialist**: no link, no attachment, no price in a subject line except as plain words, three touches, in-thread follow-ups. The `$` sign appears only in the body.
- **Honesty**: the roster sentence comes from the tracker in one of three exact forms (said yes, signed so far, five signed), with a headcount only from offices' own intake numbers. The founding price's three places are stated as a count, never as a countdown.

## Changelog

- Round 1 (2026-10-24): drafted both versions from plan appendix C, the Phase 0 brand guide and the Phase 2 objection answers; demo price checked against T-ROC's page (four to eight hours, not the plan's "a few hours").
- Round 2 (2026-10-24): discovery touch 1 reordered (the idea before the store sentence, which had read as if the founder already had offices); selling touch 1 cut from 148 to 124 words, with "plus your product and freight" stated; touch 2 cut; while fewer than five offices have signed the roster sentence says no brand is invoiced until five have (plan, Phase 1).
- Round 3 (2026-10-24): the last day to offer campaign zero to a new brand, Tue 2026-12-08.
- Merge (2026-10-24): touch 2 no longer says "five office pantries", which would be false under the standard offer; variant rule cross-referenced.
- Review round 1 (2026-10-24): "I'm asking 15 founders" (true from the first send, where "talking to" was not); first cold email Mon 2026-11-09 at the earliest; the founding `[OFFER LINE]` now states the note-and-case-study term and says "the drop planned for".
- Review round 2 (2026-10-24): touch 2 says the product sits "in front of the same teams while it lasts", not "seen by the same teams each day" (about 50 units an office may be gone by day 2); the founding `[OFFER LINE]` states the 10% reserve (about 250 units placed, 275 shipped); the last offer for campaign zero is Mon 2026-11-30.
- Review round 3 (2026-10-24): `[PROPOSAL ASK]` offers "the details" until the proposal counts as ready; the discovery touch 1 ("There's nothing to buy yet") is refused once `brand_selling_on = Y`.
