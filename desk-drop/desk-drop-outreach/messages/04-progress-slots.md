# 04 · Progress slots: what the copy may claim, and when

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Some sentences are only true once something has happened: an office has signed, a brand has paid, the company exists, the attorney has cleared the agreements, the date is confirmed. In the copy those sentences are bracketed slots. This file says which tracker state unlocks each one and what the words are before and after. Nothing in any message claims progress the tracker does not show on the day it is sent.

**The three files.**
- `04-slot-state.csv`: today's state, one row per switch or count, with how to set it. **On 2026-10-24 every switch is N and every count is 0.** Update it the day anything changes; counts come from the Clay tables and `handoff/`, switches from you.
- `04-slot-table.csv`: every slot, the state that unlocks it, the locked and unlocked words, and the source of truth.
- This file: the rules, in words.

If the tracker workbook in `tracking/` gets a settings tab with the same keys, it should mirror `04-slot-state.csv`; until the merge decides, the CSV wins.

---

## The rules

1. **A slot with a date stays a slot.** Dates are written as `[DROP DATE: Tue 2027-01-12]`, the CONTRACTS section 3 form, and every one is "derived, founder to confirm". Copy says "planned for" until `drop_date_confirmed = Y` (both brands paid and all five offices approved), then "set for".
2. **Every proposed drop date is a Tuesday or a Wednesday,** outside 18 to 31 December, the Monday-to-Friday week holding 4 July (or its observed day), and 18 to 31 August, with the whole five-business-day window clear of them. The ones in the copy: campaign zero Tue 2027-01-12 (window closes Tue 2027-01-19, MLK Day skipped), stretch Tue 2026-12-08 (only if `stretch_drop = Y`), standard runs Tue 2027-02-09 and Tue 2027-02-23. `_render/fill.py` refuses any other drop date that breaks this rule.
3. **A count is printed only from the source named.** Offices signed and the Tuesday headcount come from signed offices' own intake numbers, never from A's onsite estimate. Founding places taken come from paid brands.
4. **A locked sentence is left out or replaced, never softened.** "Five offices have signed" is not written as "five offices are lined up" when two have signed.
5. **Gates that stop a whole message, not just a sentence:** no cold email touch 1 until `domain_ready = Y`; no office selling copy until `office_selling_on = Y`; no brand selling copy until `brand_selling_on = Y` (Gate 0 brand pass recorded and `offices_yes >= 2`); no agreement or invoice until `attorney_cleared = Y` (offices) or `llc_formed = Y` and `attorney_cleared = Y` (brands); no public naming until `name_decided = Y`; no Startup CPG post until `startup_cpg_joined = Y`.

## The slots, by what unlocks them

| Unlocked by | Slot | Before | After |
| --- | --- | --- | --- |
| `offices_signed` | `[OFFICE OPENER]` (office selling, touch 1) | 0 to 4: "I'm signing up five founding offices around {area} for a first drop planned for the [FIRST DROP WEEK: week of Mon 2027-01-11]." | 5 or more: "I'm adding offices around {area} for drops from [NEXT DROP DATE: Tue 2027-02-09]." |
| `offices_signed` | `[OFFICE PROGRESS LINE]` | 0: left out | 1 to 4: "[N] have signed so far." (1: "One has signed so far.") 5+: left out |
| `offices_yes`, `offices_signed`, `tuesday_headcount` | `[ROSTER LINE]` (brand selling, proposal email) | fewer than 2 yes: the brand selling sequence is not used | 2+ yes, 0 signed: "[N] offices around {CLUSTER} have said yes in principle to receiving emerging brands. None has signed yet." 1 to 4 signed: "[N] offices around {CLUSTER} have signed up to receive emerging brands, with about [TUESDAY HEADCOUNT] people in on a Tuesday, by their own count. I'm aiming for five." 5+: "Five offices around {CLUSTER} have signed up ..., by their own count." |
| `founding_taken` | `[OFFER LINE]` | 0 to 2: the founding offer ($600, five offices, paid before you ship, $120 an office for the next two campaigns) | 3: the standard offer ($1,500, ten offices, half on signing, half on placement confirmation) |
| `founding_taken` | `[FOUNDING LINE]` | 0: "The founding price is open to the first three brands that sign." | 1 or 2: "[N] of the three founding places are taken." 3: "The next drop is [NEXT DROP DATE: Tue 2027-02-09]." |
| a qualified brand at yes in principle | `[FIRST BRAND LINE]` (office approval) | "I'm lining up the first brands now. You'll see each one before it comes, and nothing comes unless you say yes." | "The first brand I'd suggest is {brand_name}, {category_phrase}{?from_city}. ..." |
| `gl_bound` | `[INSURANCE LINE]` | "We will carry general liability insurance before your first drop." | "We carry general liability insurance." |
| `llc_formed` and `attorney_cleared` | `[FORMATION LINE]` (brand proposal) | "The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19]. Nothing is due before then." | left out |
| `mock_card_photo_ready` | `[MOCK CARD LINE]` | The card in words: "It's a 5 by 7 inch card: the brand's name, two sentences about it, the allergen line copied from the package, and a QR code to the survey." | Replies and conversion: "Attached is a photo of the card on a real pantry shelf." Cold touch 2 keeps the words (no pictures in cold email). |
| `*_onepager_ready`, `proposal_ready` | `[ONE-PAGER]` | Not offered | Attached, only in a reply or a later touch |
| `intake_form_ready` | `[INTAKE FORM LINK]` | Six questions by reply | The form's address |
| `site_live` and `name_decided` | `[WEBSITE]` | Left out everywhere | In replies, conversion emails and the signature; never in touch 1 |
| `office_hours_per_signing` | `[OFFICE HOURS LINE]` | Left out | "Signing each office has taken me about [H] hours so far." |
| `name_decided` | LinkedIn headline (01) | Version 1, no name | Version 2, with `{BRAND_NAME}` |

The dates in the copy and where they come from are in `04-slot-table.csv` (drop date, first drop week, next drop date, ship-by, cancel-by, materials due, agreement date, report date, code valid through, recontact date).

## Changelog

- Round 1 (2026-10-24): every progress-dependent claim in the copy turned into a slot with its unlocking state, source and before and after wording; today's state recorded (all switches N, all counts 0).
