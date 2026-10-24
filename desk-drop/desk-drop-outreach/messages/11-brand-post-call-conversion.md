# 11 · Brand post-call conversion: from a qualifying call to a paid founding campaign

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** The emails that take a brand from a qualifying call to a signed agreement, a paid invoice and the five things the card and the campaign need: the insurance certificate, the allergen sheet, the logo, two sentences for the card and a discount code. This is the plan's Phase 2 "Close and collect", one ask per email.

**When it is used.** After a brand call where all seven qualification checks are Y or likely (the call guide in `calls/` runs them) and the person can approve $600 alone. Weeks 4 to 7 (Mon 2026-11-16 to Fri 2026-12-11, derived). Two hard gates from the legal pack:
- **No agreement and no invoice before the company is formed and the attorney has cleared the agreement** (`llc_formed = Y` and `attorney_cleared = Y`; desk-drop-legal-pack/10 notes). The plan forms the company at the first verbal brand yes, so step 5 below covers the days in between.
- **The certificate must be in and checked before the product ships** (desk-drop-legal-pack/11).

- **The last day to offer campaign zero to a new brand is [LAST OFFER DATE: Tue 2026-12-08]** (derived, founder to confirm). A verbal yes, five business days to form the company and five more to pay must all land before the asked ship-by date, Tue 2026-12-22. After it, step 1 offers [NEXT DROP DATE: Tue 2027-02-09]; `_render/fill.py` refuses a proposal for Tue 2027-01-12 sent later.

**How to fill it in.** Tokens and slots as in 03 and 04; the campaign facts come from the brand intake and the proposal. Every email carries `{SIGNATURE}` (file 02).

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
| 5 | On a verbal yes, before formation or the attorney hour | Holding note | Can you ship 275 units by the ship-by date? |
| 6 | `llc_formed = Y` and `attorney_cleared = Y` | The agreement | Sign it |
| 7 | On signature | The invoice | Pay by bank transfer by the due date |
| 8 | The same day as step 7 | The five things for the card and the campaign | Send all five by the materials date |
| 9 | 3 business days after step 8, if anything is missing | What is still missing | Send the rest |
| 10 | Payment received | Ship date confirmed | Reply with the tracking number when it ships |

After step 4 with no reply: thanks and one referral (08, 2c), `status = not_now`, `next_action = recontact`, [RECONTACT DATE: Tue 2027-01-19]. A no at any point: 09, H, or I for an opt-out. An objection: 09, J.

---

### Step 0 · Weeks 1 to 3: thanks, and nothing to sell yet

A discovery call sells nothing (plan, Phase 0). A brand that named $500 or more and controls the budget gets this the same day, and the proposal only once two or more offices have said yes.

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

I'm not selling anything yet. If it goes ahead, the first campaign would be in January, and only once the first offices have signed.

May I send you the details then, probably in the [FOLLOW-UP WEEK: week of Mon 2026-11-16]?

{SIGNATURE}
```

`[ONE THING THEY SAID THAT CHANGED YOUR THINKING]`: a true one, from your notes; if nothing did, delete that sentence. A yes: `next_action = send_proposal`, `next_action_date` = Mon 2026-11-16, and step 1 once `brand_selling_on = Y` and you have run the seven checks with them (a short call or by email).

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

[PROPOSAL LINE] [ROSTER LINE] The drop is planned for [DROP DATE: Tue 2027-01-12]. It's $600 for five offices, paid before you ship, and your next two campaigns stay at $120 an office. [FORMATION LINE]

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

One term worth knowing: if an office hasn't put {product} out by the day after delivery, you get $120 back for that office. You pay for placements that happen.

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

### Step 5 · Verbal yes, before the company is formed

The plan forms the company at the first verbal brand yes. This email holds the yes honestly in the days that takes.

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

Thank you, that's great. I've put {company} down for [DROP DATE: Tue 2027-01-12] as {category_only_phrase} in that drop. The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19], once the company's registration is through; nothing is due before then.

One thing to confirm now: can you ship 275 units (250 plus 10% spare) to one Manhattan address by [SHIP-BY DATE: Tue 2026-12-22]?

{SIGNATURE}
```

`{category_only_phrase}` is "the only chips and crisps brand" (the section 4 label in lower case); if the category is unknown, "the only brand in your category". `[AGREEMENT DATE]` is the later of Thu 2026-11-19 and five business days after you send this (filing, the EIN and the bank account; assumption, founder to confirm), so it is never a date that has passed. Category exclusivity within a drop is the plan's rule (revised model, "What brands buy"). `yes_in_principle = Y` if not already set.

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

Here is the campaign agreement, with the details from our call filled in on the first page: five offices, [DROP DATE: Tue 2027-01-12], $600, and your choice for any unused product (returned to you at your cost, or left with the offices). The cancel-by date is [CANCEL-BY DATE: Mon 2026-12-28]: cancel before it and you get everything back less $100; from that date we keep half.

Could you sign it by [SIGN-BY DATE]?

{SIGNATURE}
```

The agreement is `desk-drop-legal-pack/10-brand-campaign-agreement.md` (rendered PDF in `desk-drop-legal-pack/rendered/`), Part 1 filled from the brand intake; only with `llc_formed = Y` and `attorney_cleared = Y`. `[SIGN-BY DATE]`: five business days from sending. The cancellation sentence restates section 8 for campaign zero, where the cancel-by date is T−10, Mon 2026-12-28, not the asked ship-by date (desk-drop-legal-pack/HANDOFF.md, notes for E). From the drop day the full price is due; that is in the agreement, and you say so if asked.

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

1. A certificate of insurance showing your product liability coverage of at least $1,000,000, with [COMPANY NAME: Desk Drop LLC] added as an additional insured. Your broker issues it; everything they need is in the note at the bottom, so you can forward this email to them as it is.
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

- **Item 1** replaces desk-drop-legal-pack/11's Email 1 (the same request, inside this email). Paste G's broker block exactly as it stands in that file; do not reword it. Its slots: [BRAND LEGAL NAME], [BRAND ADDRESS], [COMPANY NAME: …] (the name on the filed Articles), [POSTAL ADDRESS], [PRODUCT NAME AND SKU], [AGREEMENT DATE], [SHIP-BY DATE], [COVER-UNTIL DATE]. Check the certificate with G's five-minute check when it arrives.
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
