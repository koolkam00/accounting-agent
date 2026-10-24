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

The exact words before and after each unlock are in `04-slot-table.csv` (column `locked_text` and `unlocked_text`); `_render/fill.py lint` fails if the engine's wording and that file ever differ. In short:

| Unlocked by | Slots |
| --- | --- |
| `offices_signed` | `[OFFICE OPENER]` (five founding offices, then "adding offices"), `[OFFICE PROGRESS LINE]` ("Three have signed so far."), `[LAST CHECK LINE]`, `[ROSTER LINE]`, `[TUESDAY HEADCOUNT]`, LinkedIn headline version 3 |
| `offices_yes` | `brand_selling_on` (two or more), `[ROSTER LINE]` before any office has signed ("said yes in principle; none has signed yet") |
| `founding_taken` | `[OFFER LINE]` and `[OFFER SHORT]` (founding offer, then the standard offer at 3), `[FOUNDING LINE]` |
| a qualified brand at yes in principle | `[FIRST BRAND LINE]` in the office approval email |
| `drop_date_confirmed` | "planned for" becomes "set for" |
| `gl_bound` | `[INSURANCE LINE]` |
| `llc_formed`, `attorney_cleared` | `[FORMATION LINE]`, `[AGREEMENT TIMING LINE]`, `[AGREEMENT DATE]`, and whether the agreement emails may go at all |
| `mock_card_photo_ready` | `[MOCK CARD LINE]` (photo in replies and conversion; words in cold email) |
| `office_onepager_ready`, `proposal_ready`, `discovery_onepager_ready` | `[OFFICE ONE-PAGER LINE]`, `[PROPOSAL LINE]`, `[ONE-PAGER]` |
| `intake_form_ready` | `[INTAKE PARAGRAPH]`, `[INTAKE FORM LINK]` |
| `site_live`, `name_decided` | `[WEBSITE]`, LinkedIn headline version 2 |
| `office_hours_per_signing` | `[OFFICE HOURS LINE]` |

**Dates that move with the send date.** `[AGREEMENT DATE]` is the later of Thu 2026-11-19 and five business days after the email is sent, so a slow week never prints a day that has passed. `[CHECK-BACK DATE]`, `[SIGN-BY DATE]` and `[INVOICE DUE]` are five business days after sending. `[LAST OFFER DATE: Tue 2026-12-08]` is the last day a brand new to the pipeline is offered the campaign zero drop: after it, the agreement, payment and certificate cannot all land before the asked ship-by date, so the brand is offered [NEXT DROP DATE: Tue 2027-02-09] instead.

**What the reader sees.** The templates keep the bracketed form CONTRACTS section 3 asks for. When you fill a message, write the date in plain words: "Tuesday, January 12" in a body, "January 12" in a subject, "the week of January 11". The draft maker in `_render/` does this for you.

## Changelog

- Round 1 (2026-10-24): every progress-dependent claim in the copy turned into a slot with its unlocking state, source and before and after wording; today's state recorded (all switches N, all counts 0).
- Round 2 (2026-10-24): dates that depend on the send date are computed (the agreement date can no longer print a day that has passed, which the first renders did); recipients read plain dates ("Tuesday, January 12") while templates keep the CONTRACTS slot form.
- Round 3 (2026-10-24): last-offer date for campaign zero (Tue 2026-12-08); step 0 and step 1 opener slots; `04-slot-table.csv` regenerated from the engine's exact wording, and the lint now fails if the two drift (it found five drifted sentences).
