# 04 · Progress slots: what the copy may claim, and when

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** Some sentences are only true once something has happened: an office has signed, a brand has paid, the company exists, the attorney has cleared the agreements, the date is confirmed. In the copy those sentences are bracketed slots. This file says which tracker state unlocks each one and what the words are before and after. Nothing in any message claims progress the tracker does not show on the day it is sent.

**The three files.**
- `04-slot-state.csv`: today's state, one row per switch or count, with how to set it. **On 2026-10-24 every switch is N and every count is 0.** Update it the day anything changes; counts come from the Clay tables and `handoff/`, switches from you.
- `04-slot-table.csv`: every slot, the state that unlocks it, the locked and unlocked words, and the source of truth.
- This file: the rules, in words.

**Which file wins.** `04-slot-state.csv` wins. The tracker in `tracking/` computes the six counts under "Counts for the copy slots" on its Scorecard (`offices_yes`, `offices_signed`, `tuesday_headcount`, `founding_taken`, `brands_paid`, `brand_selling_on`), but it does not hold the switches and the copy never reads it. Change a count in the CSV **the same day** an office signs, a brand pays or anyone leaves the roster, so no email claims a number the tracker no longer shows; the Friday copy from the Scorecard (`tracking/how-the-tracker-works.md`, Friday step 6) is the check that nothing was missed.

---

## The rules

1. **A slot with a date stays a slot.** Dates are written as `[DROP DATE: Tue 2027-01-12]`, the CONTRACTS section 3 form, and every one is "derived, founder to confirm". Copy says "planned for" (or "your planned ... drop") until `drop_date_confirmed = Y` (both brands paid and all five offices approved), then "set for". `_render/fill.py lint` fails "from [DROP DATE ...]" or "your [DROP DATE ...]" without "planned" while the switch is N, except in the emails after a brand has signed (11, steps 7 to 10), where the date is the signed agreement's.
2. **Every proposed drop date is a Tuesday or a Wednesday,** outside 18 to 31 December, the Monday-to-Friday week holding 4 July (or its observed day), and 18 to 31 August, with the whole five-business-day window clear of them. The ones in the copy: campaign zero Tue 2027-01-12 (window closes Tue 2027-01-19, MLK Day skipped), stretch Tue 2026-12-08 (only if `stretch_drop = Y`), standard runs Tue 2027-02-09 and Tue 2027-02-23. `_render/fill.py` refuses any other drop date that breaks this rule.
3. **A count is printed only from the source named.** Offices signed and the Tuesday headcount come from signed offices' own intake numbers, never from A's onsite estimate. Founding places taken come from paid brands.
4. **A locked sentence is left out or replaced, never softened.** "Five offices have signed" is not written as "five offices are lined up" when two have signed.
5. **Gates that stop a whole message, not just a sentence:** no cold email touch 1 until `domain_ready = Y` (the four conditions in `sending/sending-setup.md` section 0, including `warm_threads_from_domain` of 10 or more, and never before Mon 2026-11-09); no founding-price conversion email once `founding_taken = 3` (11, "Founding only"); no office selling copy until `office_selling_on = Y`; no brand selling copy until `brand_selling_on = Y` (Gate 0 brand pass recorded and `offices_yes >= 2`); no agreement or invoice until `attorney_cleared = Y` and `name_decided = Y` (offices) or `llc_formed = Y`, `attorney_cleared = Y` and `name_decided = Y` (brands); **no brand agreement or invoice until five offices have signed (`offices_signed >= 5`) and every office on the brand's route has approved it (`office_approvals_complete = Y` on the brand's Clay row, 10 step 7 and 11 step 5b)**, which is what makes "No brand is invoiced until five have" true; no business name in any email, profile or post until `name_decided = Y` (the signature reads "Setting up an office sampling service in {CLUSTER_SHORT}" until then, file 02); no Startup CPG post until `startup_cpg_joined = Y`.
6. **Discovery copy stops when that side starts selling** (review round 3). Once `office_selling_on = Y`, the office discovery touch 1, the office discovery LinkedIn note and message 1, the warm asks, the referral first touch and 10 step 0 are refused; once `brand_selling_on = Y`, the same for brands and 11 step 0. Each says nothing is for sale or that the idea is still being tested, which is then false. A discovery thread already begun finishes with its own touches 2 and 3. Attachments are asked for only when they may go: `[OUTLINE ASK]`, `[OUTLINE ASK SHORT]`, `[PROPOSAL ASK]`, `[PROPOSAL ASK REPLY]` and `[INFO PAGE LINE]` offer "the details" until the page counts as ready.
7. **The state must be possible** (review round 3). Every count and switch here obeys the gates: offices signed never exceed offices at yes; an office is signed only once `attorney_cleared` and `name_decided` are Y, and then `tuesday_headcount` is filled; a founding place or a paid brand exists only once five offices have signed and `llc_formed`, `attorney_cleared` and `name_decided` are Y; `brand_selling_on` needs two offices at yes; `drop_date_confirmed` needs two brands paid. `fill.py lint` checks this file, and the draft maker refuses to write from a state that breaks it.

## The slots, by what unlocks them

The exact words before and after each unlock are in `04-slot-table.csv` (column `locked_text` and `unlocked_text`); `_render/fill.py lint` fails if the engine's wording and that file ever differ. In short:

| Unlocked by | Slots |
| --- | --- |
| `offices_signed` | `[OFFICE OPENER]` (five founding offices, then "adding offices"), `[OFFICE PROGRESS LINE]` ("Three have signed so far."), `[JOIN ASK]` and `[JOIN ASK SHORT]` (one of the five, then a later drop), `[LAST CHECK LINE]`, `[ROSTER LINE]`, `[TUESDAY HEADCOUNT]`, LinkedIn headline version 3 |
| `offices_yes` | `brand_selling_on` (two or more), `[ROSTER LINE]` before any office has signed ("said yes in principle; none has signed yet") |
| `founding_taken` | `[OFFER LINE]` and `[OFFER SHORT]` (founding offer, then the standard offer at 3), `[FOUNDING LINE]` |
| a qualified brand at yes in principle | `[FIRST BRAND LINE]` in the office approval email |
| `drop_date_confirmed` | "planned for" becomes "set for" |
| `gl_bound` | `[INSURANCE LINE]` |
| `llc_formed`, `attorney_cleared`, `name_decided`, `offices_signed` and the brand row's `office_approvals_complete` | `[FORMATION LINE]`, `[HOLDING LINE]` (brands: what the agreement still waits for, with a date only once the offices are done), `[AGREEMENT TIMING LINE]` (offices), `[AGREEMENT DATE]`, and whether the agreement emails may go at all |
| `mock_card_photo_ready` | `[MOCK CARD LINE]` (photo in replies and conversion; words in cold email) |
| `office_onepager_ready`, `proposal_ready`, `discovery_onepager_ready` | `[OFFICE ONE-PAGER LINE]`, `[PROPOSAL LINE]`, `[ONE-PAGER]` |
| `intake_form_ready` | `[INTAKE PARAGRAPH]`, `[INTAKE FORM LINK]` |
| `site_live`, `name_decided` | `[WEBSITE]`, LinkedIn headline version 2 |
| `office_hours_per_signing` | `[OFFICE HOURS LINE]` |

**Dates that move with the send date.** `[AGREEMENT DATE]` is the later of Thu 2026-11-19 and five business days after the email is sent, so a slow week never prints a day that has passed. A brand is given that date only once five offices have signed and every office on its route has said yes to it (`[FORMATION LINE]` in 11 step 1, `[HOLDING LINE]` in step 5); until then the copy names what the agreement waits for, not a date, because the offices' pace has no known length. `[FOLLOW-UP WEEK]` is the week of Mon 2026-11-16, or the next week once that has begun. `[CHECK-BACK DATE]`, `[SIGN-BY DATE]` and `[INVOICE DUE]` are five business days after sending. `_render/fill.py lint` fails any printed date earlier than the send date and any agreement date that is not the computed one. `[LAST OFFER DATE: Mon 2026-11-30]` is the last day a brand new to the pipeline is offered the campaign zero drop, and Thu 2026-12-03 the last verbal yes it can take: working back from the asked ship-by date, Tue 2026-12-22, through five business days to pay, five to sign and up to three for the office approvals (derived, founder to confirm). After them the brand is offered [NEXT DROP DATE: Tue 2027-02-09] instead.

**What the reader sees.** The templates keep the bracketed form CONTRACTS section 3 asks for. When you fill a message, write the date in plain words: "Tuesday, January 12" in a body, "January 12" in a subject, "the week of January 11". The draft maker in `_render/` does this for you.

## Changelog

- Round 1 (2026-10-24): every progress-dependent claim in the copy turned into a slot with its unlocking state, source and before and after wording; today's state recorded (all switches N, all counts 0).
- Round 2 (2026-10-24): dates that depend on the send date are computed (the agreement date can no longer print a day that has passed, which the first renders did); recipients read plain dates ("Tuesday, January 12") while templates keep the CONTRACTS slot form.
- Round 3 (2026-10-24): last-offer date for campaign zero (Tue 2026-12-08); step 0 and step 1 opener slots; `04-slot-table.csv` regenerated from the engine's exact wording, and the lint now fails if the two drift (it found five drifted sentences).
- Merge (2026-10-24): the CSV wins over the tracker, and counts change the same day they change (the Friday copy is the check); `domain_ready` defined by the sending guide (PASS on all three records, from Mon 2026-11-02); `[JOIN ASK]`, `[JOIN ASK SHORT]`, `[STEP 0 SUBJECT]`, `[STEP 1 SUBJECT]` added; founding-price emails stop at `founding_taken = 3`.
- Review round 1 (2026-10-24): `domain_ready` needs the four conditions and is never Y before Mon 2026-11-09 (new count `warm_threads_from_domain`); brand agreements and invoices wait for five signed offices and every office's approval (`office_approvals_complete`); agreements wait for `name_decided`; no business name before `name_decided = Y`; the "planned" rule is checked by the lint.
- Review round 2 (2026-10-24): a brand is promised an agreement date only once five offices have signed and approved it (`[FORMATION LINE]`, new `[HOLDING LINE]`); the holding note no longer gives a past date or a reason that is no longer true; the lint fails any printed date earlier than the send date; `[FOLLOW-UP WEEK]` moves with the send date; the last offer for campaign zero is Mon 2026-11-30 and the last verbal yes Thu 2026-12-03, recomputed with the approvals and the sign-by.
- Review round 3 (2026-10-24): rules 6 (discovery copy stops when that side sells; asks follow the attachment state) and 7 (the state must be possible, checked by the lint and the draft maker); `[STEP 0 CAMPAIGN LINE]` says February for a brand step 0 after Mon 2026-11-30.
