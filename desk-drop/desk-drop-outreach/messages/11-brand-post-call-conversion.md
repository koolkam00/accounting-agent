# 11 · Brand post-call conversion: from a qualifying call to a paid founding campaign

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** The emails that take a brand from a qualifying call to a signed agreement, a paid invoice and the five things the card and the campaign need: the insurance certificate, the allergen sheet, the logo, two sentences for the card and a discount code. This is the plan's Phase 2 "Close and collect", one ask per email.

**When it is used.** After a brand call where all seven qualification checks are Y or likely (the call guide in `calls/` runs them) and the person can approve $600 alone. Weeks 4 to 7 (Mon 2026-11-16 to Fri 2026-12-11, derived). Three hard gates:
- **No agreement and no invoice before the company is formed and the attorney has cleared the agreement** (`llc_formed = Y` and `attorney_cleared = Y`; desk-drop-legal-pack/10 notes), and before the name is decided (`name_decided = Y`: the agreement names the business). The plan forms the company at the first verbal brand yes, so step 5 below covers the days in between.
- **No agreement and no invoice before the offices approve the brand** (step 5b): five offices signed, and every office on the brand's route has said yes to this brand (`office_approvals_complete = Y` on the brand's Clay row). The plan's order is the match, then the agreement and payment ("How a campaign runs", steps 3 and 4), and the selling copy promises "No brand is invoiced until five have" signed.
- **The certificate must be in and checked before the product ships** (desk-drop-legal-pack/11).

**The founding term, stated before any yes.** The founding price carries one condition (plan, price table; desk-drop-legal-pack/10 section 3): if the campaign is delivered as promised, the brand gives a short written statement of its honest experience within 30 days after the debrief, and lets us publish it with its name and a case study drawn from its report, saying it was a founding brand at a founding price. It is in the selling email's `[OFFER LINE]`, in step 1 and step 6 here, in objection answer J3 and in the brand call guide, so nobody meets it first in the agreement.

- **The last day to offer campaign zero to a new brand is [LAST OFFER DATE: Mon 2026-11-30], and the last verbal yes it can take is Thu 2026-12-03** (derived, founder to confirm). Working back from the asked ship-by date, Tue 2026-12-22: payment is due five business days after the invoice, so the invoice (sent on signature) goes by Tue 2026-12-15; the brand has five business days to sign, so the agreement goes by Tue 2026-12-08; the offices on the route take up to three business days to approve the brand (step 5b), so the verbal yes comes by Thu 2026-12-03; and a proposal needs a few days to get its yes, so the last one goes about Mon 2026-11-30. The no-send days from Fri 2026-12-18 leave no room for a reminder after the due date. After those dates, offer [NEXT DROP DATE: Tue 2027-02-09]: `_render/fill.py` refuses a selling touch 1 or proposal for Tue 2027-01-12 sent after Mon 2026-11-30, and step 2 or a holding note for it sent after Thu 2026-12-03.

**How to fill it in.** Tokens and slots as in 03 and 04; the campaign facts come from the brand intake and the proposal. Every email carries `{SIGNATURE}` (file 02).

**Founding only.** Steps 1, 2 and 4 to 7 carry the founding price ($600, five offices, 275 units). Once `founding_taken = 3` the founding offer is closed and `_render/fill.py` refuses those steps: write the standard terms from the standard `[OFFER LINE]` in `04-slot-table.csv` ($1,500 for ten offices, half on signing and half on the placement confirmation, 550 units). Steps 0, 3, 8, 9 and 10 work for either tier.

`sequence` = `brand-conversion-A`. Status moves: `call_done` → `yes_in_principle` (would pay $500 or more and controls the budget, per Gate 0) → `materials_sent` (proposal sent) → `paid` (payment received). A paid brand becomes a row in `handoff/paid_brands.csv` (CONTRACTS 6.4), with `coi_received_date`, `allergen_sheet_received_date`, `logo_received_date`, `card_sentences`, `allergen_line_verbatim`, `retailer_line`, `discount_code` and `landing_url` filled from step 8's answers.

---

## The path

| Step | When | Email | The one ask |
| --- | --- | --- | --- |
| 0 | Same day as a discovery call in weeks 1 to 3 (before `brand_selling_on = Y`) | Thanks, nothing to sell yet | May I send the details once the first offices have signed? |
| 1 | Within 24 hours of a qualifying call (weeks 4 to 7), or the day `brand_selling_on = Y` for a brand that said yes to step 0 | The proposal, with a drop date | Put {product} down for that drop? |
| 2 | Day 3, no reply | The refund term that takes the risk out | The same ask |
| 3 | Day 7, no reply | Date or idea? | Which one is the problem |
| 4 | Day 14, no reply | A new drop date | Move to the new date? |
| 5 | On a verbal yes, while any gate for the agreement is still open (offices, approvals, formation, attorney, name) | Holding note | Can you ship 275 units by the ship-by date? |
| 5b | Five offices signed; the approval email to each office on the route (10, step 7) | No email to the brand | Wait for every office's yes, then `office_approvals_complete = Y` |
| 6 | `llc_formed`, `attorney_cleared`, `name_decided` and `office_approvals_complete` all Y | The agreement | Sign it |
| 7 | On signature | The invoice | Pay by bank transfer by the due date |
| 8 | The same day as step 7 | The five things for the card and the campaign | Send all five by the materials date |
| 9 | 3 business days after step 8, if anything is missing | What is still missing | Send the rest |
| 10 | Payment received | Ship date confirmed | Reply with the tracking number when it ships |

After step 4 with no reply: thanks and one referral (08, 2c), `status = not_now`, `next_action = recontact`, [RECONTACT DATE: Tue 2027-01-19]. A no at any point: 09, H, or I for an opt-out. An objection: 09, J.

---

### Step 0 · Weeks 1 to 3: thanks, and nothing to sell yet

A discovery call sells nothing (plan, Phase 0). Every brand you talked to gets this the same day. The proposal goes only once `brand_selling_on = Y` (the brand-side Gate 0 pass and two or more offices at yes in principle), and only to a brand that named $500 or more and controls the budget.

```message
id: brand-conversion-0
side: brand
stage: conversion
touch: 0
channel: email
subject: Thank you for the time today
ask: may I send the details later
---
{greeting}

{call_note_hook_line} What you said about [ONE THING THEY SAID THAT CHANGED YOUR THINKING] is going straight into how I design this.

I'm not selling anything yet. [STEP 0 CAMPAIGN LINE]

May I send you the details then, probably in the [FOLLOW-UP WEEK: week of Mon 2026-11-16]?

{SIGNATURE}
```

`[ONE THING THEY SAID THAT CHANGED YOUR THINKING]`: a true one, from your notes; if nothing did, delete that sentence. `[STEP 0 CAMPAIGN LINE]` says January up to the last campaign zero offer, Mon 2026-11-30, and February after it (a brand new to the pipeline can no longer join January). Once `brand_selling_on = Y` step 0 is refused: "I'm not selling anything yet" would be false, so a brand you talk to from then on gets step 1. A yes from a brand that named $500 or more and controls the budget: `next_action = send_proposal`, `next_action_date` = Mon 2026-11-16, and step 1 once `brand_selling_on = Y` and you have run the seven checks with them (a short call or by email). A yes from any other brand: `next_action = recontact` on the same date. If `brand_selling_on` is still N on Mon 2026-11-16, move `next_action_date` to the next Monday; never send step 1 early.

### Step 1 · The proposal, within 24 hours

```message
id: brand-conversion-1
side: brand
stage: conversion
touch: 1
channel: email
subject: Proposal: {company} in five {CLUSTER_SHORT} offices, [DROP DATE: Tue 2027-01-12]
ask: put the product down for that drop
---
{greeting}

[STEP 1 OPENER]

[PROPOSAL LINE] [ROSTER LINE]

The drop is planned for [DROP DATE: Tue 2027-01-12]. It's $600 for five offices, paid before you ship; your next two campaigns stay at $120 an office. You ship 275 units (10% spare), freight prepaid, and send a certificate of product liability cover of $1 million or more per occurrence, naming us as additional insured.

In return for the founding price, if it runs as promised, you write a short note on how it went and we publish it with a case study from your report. [FORMATION LINE]

Shall I put {product} down for that drop?

{SIGNATURE}
```

`[STEP 1 OPENER]`: on the day after the call, `{call_note_hook_line}`; when this follows step 0 weeks later, "As promised, here are the details." (never "today" for a call that was not today).

`[PROPOSAL LINE]`: with `proposal_ready = Y`, "Attached is the one-page proposal for {company}, with a map of the stores near the offices and a mock report page." Without it: "The full proposal follows; here is the short version." The proposal is `desk-drop-identity/templates/proposal/`, made with the brand's name, the roster from `handoff/signed_offices.csv` (industry, neighborhood and headcount band only, never office names) and the brand's map from `cluster-1-flatiron/brand-maps/`. A drop date three to four weeks out is the plan's rule; under the canonical calendar every founding brand's first possible drop is [DROP DATE: Tue 2027-01-12] (stretch Tue 2026-12-08 only if `stretch_drop = Y`), so for a call in weeks 4 to 7 it is six to eight weeks out.

### Step 2 · Day 3

```message
id: brand-conversion-2
side: brand
stage: conversion
touch: 2
channel: email
subject: Re: Proposal: {company} in five {CLUSTER_SHORT} offices, [DROP DATE: Tue 2027-01-12]
ask: the same
---
{greeting}

One term worth knowing: if an office hasn't put {product} out by the day after delivery and I can't move it to another office, you get $120 back for that office. You pay for placements that happen.

Shall I put {company} down for [DROP DATE: Tue 2027-01-12]?

{SIGNATURE}
```

Term from desk-drop-legal-pack/10 v0.8, sections 3 and 8.

### Step 3 · Day 7

```message
id: brand-conversion-3
side: brand
stage: conversion
touch: 3
channel: email
subject: Re: Proposal: {company} in five {CLUSTER_SHORT} offices, [DROP DATE: Tue 2027-01-12]
ask: date or idea
---
{greeting}

A straight question, so I don't keep writing: is it the date that doesn't work, or the idea?

{SIGNATURE}
```

### Step 4 · Day 14, with a new date

```message
id: brand-conversion-4
side: brand
stage: conversion
touch: 4
channel: email
subject: Re: Proposal: {company} in five {CLUSTER_SHORT} offices, [DROP DATE: Tue 2027-01-12]
ask: move to the new date
---
{greeting}

If [DROP DATE: Tue 2027-01-12] was the problem, the next drop is planned for [NEXT DROP DATE: Tue 2027-02-09], and the founding price would still apply while a founding place is open. [FOUNDING LINE]

Would you like me to move {company} to that date?

{SIGNATURE}
```

Assumption (listed in the report): a founding brand that moves takes its five offices in the next drop, at the founding price, while fewer than three founding brands have paid.

### Step 5 · Verbal yes, while the agreement still waits

The plan forms the company at the first verbal brand yes, and the offices on the route approve the brand after it (step 5b). This email holds the yes honestly while either is still open, and says which one.

```message
id: brand-conversion-5
side: brand
stage: conversion
touch: 5
channel: email
subject: Re: Proposal: {company} in five {CLUSTER_SHORT} offices, [DROP DATE: Tue 2027-01-12]
ask: can they ship 275 units by the ship-by date
---
{greeting}

Thank you, that's great. I've put {company} down for [DROP DATE: Tue 2027-01-12] as {category_only_phrase} in that drop. [HOLDING LINE]

One thing to confirm now: can you ship 275 units (250 plus 10% spare) to one Manhattan address by [SHIP-BY DATE: Tue 2026-12-22]?

{SIGNATURE}
```

`{category_only_phrase}` is "the only chips and crisps brand" (the section 4 label in lower case); if the category is unknown, "the only brand in your category". Category exclusivity within a drop is the plan's rule (revised model, "What brands buy"). `yes_in_principle = Y` if not already set.

`[HOLDING LINE]` says what the agreement and invoice still wait for, and promises a date only when the date depends on nothing but the company's own steps (review round 2):
- fewer than five offices signed: "The agreement and invoice come once five offices have signed and each has said yes to {product}; nothing is due before then."
- five signed, not every office on the route has said yes to this brand (step 5b; the usual case, because the approval emails go the day of the verbal yes): "The agreement and invoice come once each of the five offices has said yes to {product}; nothing is due before then."
- the offices are done, the company is not yet formed: "The agreement and invoice come by [AGREEMENT DATE], once the company's registration is through; nothing is due before then." Company formed, attorney or name still pending: the same without the registration clause.
- every gate met: no holding note; `_render/fill.py` refuses step 5 and you send step 6.

`[AGREEMENT DATE]` is the later of Thu 2026-11-19 and five business days after you send the email (filing, the EIN and the bank account; assumption, founder to confirm), so it is never a date that has passed; the lint fails any printed date earlier than the send date. Step 1's `[FORMATION LINE]` follows the same rules (with "Nothing is due before then." as its own sentence, and left out once every gate is met).

### Step 5b · The offices approve the brand (no email to the brand)

Before the agreement goes, every office on the brand's route says yes to it by reply (10, step 7: for an office's first three drops nothing comes without its explicit yes, desk-drop-legal-pack/03 section 2). Send step 7 of file 10 to each signed office on the route the day the brand's verbal yes and its seven checks are in. When the last one says yes, set `office_approvals_complete = Y` on the brand's Clay row and send step 6. If an office says no, swap in another signed office and ask it. If the approvals take more than three business days, the step 5 holding note already covers the wait; do not chase the brand.

### Step 6 · The agreement

```message
id: brand-conversion-6
side: brand
stage: conversion
touch: 6
channel: email
subject: Campaign agreement for {company}, [DROP DATE: Tue 2027-01-12]
ask: sign it
---
{greeting}

Here is the campaign agreement, with the details from our call filled in on the first page: five offices, [DROP DATE: Tue 2027-01-12], $600, and your choice for any unused product (returned to you at your cost, or left with the offices). All five offices have approved {product}. The cancel-by date is [CANCEL-BY DATE: Mon 2026-12-28]: cancel before it and you get everything back less $100; from that date we keep half. In return for the founding price, if we deliver everything promised, you give us a short written note on how it went within 30 days of the debrief, and we may publish it with a case study from your report.

Could you sign it by [SIGN-BY DATE]?

{SIGNATURE}
```

The agreement is `desk-drop-legal-pack/10-brand-campaign-agreement.md` (rendered PDF in `desk-drop-legal-pack/rendered/`), Part 1 filled from the brand intake; only with `llc_formed = Y`, `attorney_cleared = Y` and `name_decided = Y`, five offices signed and `office_approvals_complete = Y` on the brand's row (`_render/fill.py` refuses it otherwise). The last sentence restates section 3's founding term in plain words; the agreement's wording governs. `[SIGN-BY DATE]`: five business days from sending. The cancellation sentence restates section 8 for campaign zero, where the cancel-by date is T−10, Mon 2026-12-28, not the asked ship-by date (desk-drop-legal-pack/HANDOFF.md, notes for E). From the drop day the full price is due; that is in the agreement, and you say so if asked.

### Step 7 · The invoice, on signature

```message
id: brand-conversion-7
side: brand
stage: conversion
touch: 7
channel: email
subject: Invoice [INVOICE ID] for your [DROP DATE: Tue 2027-01-12] campaign
ask: pay by the due date
---
{greeting}

Thank you for signing. Attached is invoice [INVOICE ID] for $600, payable by bank transfer; the details are on the invoice. Your ship date is confirmed the day payment arrives.

Could you arrange payment by [INVOICE DUE: five business days from today]?

{SIGNATURE}
```

The invoice is made in Wave (free invoicing, plan "Tools"); never sent before the company and its bank account exist (desk-drop-legal-pack/10 notes). Founding: within five business days of the invoice and before shipping. Standard: the first half on signing, the second at the placement confirmation.

### Step 8 · The five things for the card and the campaign

Send it the same day as the invoice, as its own email, so each email has one ask. All five items are in this one email, as the plan asks.

```message
id: brand-conversion-8
side: brand
stage: conversion
touch: 8
channel: email
subject: Five things we need from {company} for the [DROP DATE: Tue 2027-01-12] drop
ask: send all five by the materials date
---
{greeting}

These are the five things the card and the campaign need from you:

1. A certificate of insurance showing your product liability coverage of at least $1,000,000, with [COMPANY NAME: the LLC name as filed] added as an additional insured. Your broker issues it; everything they need is in the note at the bottom, so you can forward this email to them as it is.
2. Your ingredient and allergen statement as printed on the package: a spec sheet, or a clear photo of the panel. The card repeats your "Contains" line word for word, and any "may contain" line too.
3. Your logo: an SVG, or a PNG at least 300 pixels tall on a transparent or white background.
4. Two sentences for the card, in your words: who makes it and why it exists, 200 characters or fewer. No health claims (nothing like "supports gut health" or "boosts immunity") and no "best". You'll approve the card proof before it prints.
5. A discount code people can use at your online store, valid through at least [CODE VALID THROUGH: Thu 2027-02-11], when we'll ask how many times it was used. (A landing page works instead of a code if you prefer.)

Could you send all five by [MATERIALS DUE: Thu 2026-12-17]?

---
For your insurance broker or agent:
[PASTE desk-drop-legal-pack/11 "Block to forward" HERE, WORD FOR WORD, WITH ITS SLOTS FILLED]

{SIGNATURE}
```

- **Item 1** replaces desk-drop-legal-pack/11's Email 1 (the same request, inside this email). Paste G's broker block exactly as it stands in that file; do not reword it. The draft maker fills the slots it already knows: [BRAND] (the brand's name from the row), [COMPANY NAME: …] (the `brand.json` name plus "LLC": check it letter for letter against the filed Articles), [AGREEMENT DATE] (the day you send this, which is the signing day), [SHIP-BY DATE] and [COVER-UNTIL DATE] (campaign zero's: Tue 2026-12-22, and Wed 2028-01-19, 12 months after the window closes, or the latest best-by date if later; change both for a later drop). You fill three from the brand intake: [BRAND LEGAL NAME], [BRAND ADDRESS] and [PRODUCT NAME AND SKU]; [POSTAL ADDRESS] is yours. Check the certificate with G's five-minute check when it arrives.
- **Item 2** feeds `allergen_line_verbatim` (and the card's `may_contain_verbatim`); it is checked again against the physical package at receiving.
- **Item 4** feeds `card_sentences`; the card template refuses health claims (desk-drop-identity tent card, claims check).
- **Item 5** feeds `discount_code` and `landing_url`; [CODE VALID THROUGH] is T+30 calendar days, the redemption check (CONTRACTS section 3).
- `[MATERIALS DUE]` is three business days before the asked ship-by date, the date G's file 11 gives for the certificate.

### Step 9 · What is still missing (+3 business days)

```message
id: brand-conversion-9
side: brand
stage: conversion
touch: 9
channel: email
subject: Re: Five things we need from {company} for the [DROP DATE: Tue 2027-01-12] drop
ask: send the rest
---
{greeting}

Thank you for [WHAT ARRIVED]. Still to come: [WHAT IS MISSING, BY NUMBER]. The ship date of [SHIP-BY DATE: Tue 2026-12-22] holds once the certificate is in.

Could you send the rest by [MATERIALS DUE: Thu 2026-12-17]?

{SIGNATURE}
```

If only the certificate is missing, use desk-drop-legal-pack/11's Email 2 instead, as written. If the certificate is not in by T−10 the product does not ship until it is (desk-drop-legal-pack/10 section 2(c), file 11).

### Step 10 · Payment received

```message
id: brand-conversion-10
side: brand
stage: conversion
touch: 10
channel: email
subject: Payment received: please ship by [SHIP-BY DATE: Tue 2026-12-22]
ask: the tracking number when it ships
---
{greeting}

Payment received, thank you. Your campaign is booked for [DROP DATE: Tue 2027-01-12]. Please ship [UNITS TO SHIP: 275] units, freight prepaid, to [SHIP-TO ADDRESS] by [SHIP-BY DATE: Tue 2026-12-22], and the report comes by [REPORT DATE: Fri 2027-01-22].

Could you reply with the tracking number when it ships?

{SIGNATURE}
```

`[SHIP-TO ADDRESS]` comes from the operations workstream (`campaign-ops/`): your receiving address or the consolidation point. Then `status = paid`, `payment_received_date`, and the row in `handoff/paid_brands.csv`. From here the operations system runs the campaign.

---

## Changelog

- Round 1 (2026-10-24): drafted from plan Phase 2 "Close and collect" (proposal within 24 hours, follow-ups at days 3, 7 and 14, agreement and invoice by bank transfer, the five items in one email) and the legal pack's gates (agreement only after formation and the attorney hour; the certificate request and check in file 11; campaign zero's cancel-by date).
- Round 2 (2026-10-24): subjects fixed for the brand-name fallback; unused product returned "at your cost" (agreement); the broker note is at the bottom; "booked" not "confirmed"; the agreement date computed so it is never past; the broker block is pasted from the legal pack's file in the examples.
- Round 3 (2026-10-24): step 0 for discovery calls; the last-offer date (Tue 2026-12-08), after the fallback render showed a verbal yes on Dec 9 that could not be invoiced and paid before ship-by; step 1 opener.
- Round 4 (2026-10-24): step 1 opener as in file 10; the legal pack's broker block is pasted with plain dollar signs.
- Merge (2026-10-24): step 0 goes to every brand the same day, the proposal only to a $500-and-controls-budget brand once `brand_selling_on = Y` (matches the brand call guide); "planned for January"; the refund term carries the agreement's condition; the founding-price steps are refused once `founding_taken = 3`.
- Review round 1 (2026-10-24): the founding testimonial and case-study term is stated in step 1 and step 6 (and in `[OFFER LINE]`, J3 and the call guide), not first met in the agreement; step 5b: no agreement or invoice until five offices have signed and every office on the route has approved the brand, enforced by `_render/fill.py`; the agreement, invoice and insurance request also wait for `name_decided = Y`; the LLC name is filled from `brand.json`, never typed; the broker block arrives with the brand name and campaign zero's dates filled.
- Review round 2 (2026-10-24): the proposal and the holding note promise an agreement date only once five offices have signed and approved the brand (`[FORMATION LINE]`, new `[HOLDING LINE]`, both enforced and tested in `_render/fill.py`); otherwise they say what it waits for. A holding note sent after formation no longer gives a past date or "once the company's registration is through"; with every gate met, `fill.py` refuses step 5 and step 6 goes. Step 1 states the 275 units (10% spare) and the $1 million cover. The last proposal for campaign zero is Mon 2026-11-30 and the last verbal yes Thu 2026-12-03, recomputed with the office approvals and the sign-by.
- Review round 3 (2026-10-24): step 0 is refused once `brand_selling_on = Y`, and says February after Mon 2026-11-30 (`[STEP 0 CAMPAIGN LINE]`); step 8 prints the company name bare once `llc_formed = Y`, and the draft's NOTE line lists the broker slots still to fill.
