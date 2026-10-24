# Brand call guide

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/calls/`

**What it is for.** Running a 20 to 30 minute discovery conversation with a founder or marketing lead at an emerging snack or drink brand, and coming away with what Gate 0 needs: the number they would pay, named before they hear $1,500, and whether the person saying it controls the budget. The seven questions are the plan's (Phase 0, "Brand conversation guide"), word for word and in the plan's order. Section 6 adds the seven qualification checks for the qualifying calls of weeks 4 to 7.

**When it is used.** Discovery: weeks 1 to 3 (Mon 2026-10-26 to Fri 2026-11-13, derived, founder to confirm). Qualifying calls: weeks 4 to 7, once Gate 0 has passed (sections 3 and 6 together).

**No selling in weeks 1 to 3.** You are learning what trial is worth to them. You do not send a proposal, quote the founding offer unprompted, or ask for a commitment. Startup CPG contacts in particular stay research conversations: the community does not allow cold selling (plan, "Brand pipeline").

---

## 1. Before the call (2 minutes)

- Open their Clay brands row and a new row on **Brand_Log** in `tracking/conversation-tracker.xlsx`. Paste the `row_id`, brand, name and title.
- Read `nearest_stocked_retailer` and its `nearest_retailer_grade`. Never say you saw them on a shelf unless the grade is `seen_on_shelf`, which only you set after seeing it. `store_selector` means "the store's own site lists you"; `brand_claim` means "your store locator lists it".
- If B has made a map for them, have it open (`cluster-1-flatiron/brand-maps/<slug>.png`).
- Read `why_now` and open `why_now_url` if you plan to mention it.
- Start a 25-minute timer and open `calls/post-call-note-template.md`.

## 2. Opening (30 seconds)

> "Thanks for the time. I'm [FOUNDER NAME]. I'm testing an idea: putting emerging snack and drink brands into a handful of New York offices for a week, with placement photos and employee feedback, near the stores that carry them. Before I build it I want to know what brands actually need from trial. I'm not asking you to buy anything today. One thing up front: I'm testing price too, so at one point I'll ask what this would be worth to you before I tell you the number I have in mind. OK if I ask seven questions and take notes? About 25 minutes."

## 3. The seven questions (plan wording, plan order)

| # | Ask exactly | Minutes | Listen for, then probe | Goes in (Brand_Log) |
| --- | --- | --- | --- | --- |
| 1 | "How are you getting people to try the product right now? What is working and what is not?" | 4 | Demos, street teams, online sampling, events, influencer boxes. What they say has not worked is the most useful part. | `q1_trial_now_verbatim` |
| 2 | "What do you spend on sampling or field marketing a quarter, and who signs off on it?" | 3 | A number or range per quarter. Then the approver: "you, or someone else?" | `q2_sampling_budget_quarter_low_usd`, `..._high_usd`, `q2_budget_verbatim`, `budget_approver`; `controls_budget` = Y only if this person can approve the spend alone (a joint decision is N) |
| 3 | "Have you ever seeded offices? What happened?" | 2 | Who they tried, what it took, whether anything came back. "We tried, nobody sent photos" is gold. | `q3_seeded_offices` (Y/N), `q3_verbatim` |
| 4 | "If I could put 500 units into 10 Flatiron offices in one week, within walking distance of Whole Foods Union Square, with placement photos and employee feedback, what would that be worth to you?" **Let them name a number before you mention $1,500.** | 5 | See "The anchor rule" below. Write their first number and their exact words before saying anything about price. | `wtp_before_usd`, `wtp_before_verbatim`, `wtp_unit_note`; then `price_1500_mentioned`, `wtp_after_usd`, `wtp_after_verbatim` |
| 5 | "What would the report need to show for you to do it again?" | 3 | Photos, depletion, verbatim feedback, scans, code redemptions, retailer velocity. If they say "sales lift", note it: the report will not claim lift (plan, measurement). | `q5_report_needs_verbatim`; objection `want_sales_data` if lift is a must |
| 6 | "Where can someone buy you within ten blocks of Madison Square Park?" | 2 | A store and street, or "online, with a code". Compare with Clay's `nearest_stocked_retailer`. A store they name that Clay lacks: add it to `notes` for the Clay row, graded `brand_claim`. | `q6_buy_path_type`, `q6_buy_path_verbatim` |
| 7 | "What would stop you: budget timing, inventory, shelf life, something else?" | 3 | Each stopper is an objection code: `budget_timing`, `inventory`, `shelf_life`, or another. | `q7_stoppers_verbatim`, `objection_1` to `objection_3`, `objections_verbatim` |

In question 4 you may name their own nearest store in place of Whole Foods Union Square if Clay's grade for it is `store_selector`, `brand_claim` or `seen_on_shelf` ("within walking distance of [their store]"). Keep the rest of the question as written.

### The anchor rule (question 4)

1. Ask the question as written. Then stop talking, even through a pause.
2. If they ask "what do you charge?": "I'll tell you, but I'd like your number first. It's the main thing I'm testing." Wait again.
3. Write their number and words in `wtp_before_usd` and `wtp_before_verbatim`. Convert to one campaign of 500 units in 10 offices if they gave another unit, and say how in `wtp_unit_note` ("$1 a unit x 500 = 500"; "$150 a store x 10 = 1500"). "Nothing" or "we'd want it free" is 0. "I don't know" is blank, with the words kept.
4. Only then say the price: **"For reference, the standard price I'm testing is $1,500 for ten offices. How does that land?"** Set `price_1500_mentioned` = Y and write the answer in `wtp_after_usd` and `wtp_after_verbatim`.
5. If they still refuse to name a number before hearing a price, say the $1,500 line, leave `wtp_before_usd` blank and write "declined to name a number" in `wtp_before_verbatim`.

**The founding price is not volunteered in discovery.** If they ask whether there is anything smaller or cheaper, the true answer: "The first three brands get five offices for $600, paid up front, and keep $120 an office for their next two campaigns." Note in `notes` that they asked; it is a buying signal.

**What counts for Gate 0.** A brand counts toward the 3 of 15 when the higher of its two numbers is $500 or more and `controls_budget` = Y (the same rule the financial model uses). The scorecard also shows a strict read: $500 or more named before $1,500 was mentioned.

## 4. The close (2 minutes)

1. **Referral:** "Who else should I be talking to?" Brand and title, business contacts only. Ask whether you may say they suggested it (goes in the new Clay row's `referrer_ok_to_name`).
2. **Permission to come back:** in weeks 1 to 3, "Can I come back to you once five offices have signed up?" Set Clay `next_action` = `recontact` and `next_action_date` = Mon 2026-11-16 (the Monday after Gate 0, derived, founder to confirm).
3. **Ask before you ever quote them:** "If I share what founders are telling me, may I quote something you said, without your name or your brand?" `quote_ok_to_share` = Y only on a clear yes.
4. **After the call,** mark `shortlist` = Y if this is one of the brands you would pursue first (the plan's Gate 0 deliverable is a shortlist of 6).
5. **One-pager, if they ask for something in writing:** the discovery one-pager (`desk-drop-identity/pdf/discovery-one-pager-BLANK.pdf`, once your details are filled). No proposal before Gate 0.

## 5. Their questions, answered truthfully

| They ask | Say | Never say |
| --- | --- | --- |
| "Which offices?" | Weeks 1 to 3: "None has signed yet. I'm talking to about fifteen office managers around Flatiron this month." Later, the `[ROSTER LINE]` from `messages/04-slot-table.csv`, which counts only signed offices and their own Tuesday numbers. Company names only after signature (plan, "The proposal") | A count, an industry list or a headcount the tracker does not show |
| "What results have other brands had?" | "None yet. The first campaign is planned for [DROP DATE: Tue 2027-01-12]. I'd rather tell you that than make up a number." | Any number at all |
| "Do you guarantee sales?" | "No. You get placement photos from each office, depletion counts, what employees said in their own words, scans and code redemptions, and a recommendation. Not a sales guarantee." (plan objection 4) | "Lift", "conversions", "ROI", "new customers" |
| "Can we do a free trial first?" | "No. The founding price is the trial." (plan objection 3; only if they ask) | "Maybe for you" |
| "We can seed offices ourselves." | Discovery: write it down, code it `seed_ourselves`, and ask "what would you need to make that work?" Do not argue in weeks 1 to 3. The answer for later is in `messages/09-reply-playbook.md`, J | |
| "Can we pick the offices?" | "The offices approve each brand, and the campaign has a fixed number of them. You'd see them by neighborhood, industry and Tuesday headcount before you pay." | Promising a specific company |
| "Do we get the employees' emails?" | "No. The survey is anonymous. If you want, the survey can carry an unticked box for your newsletter under your own privacy policy, and only people who tick it are passed on." | Any other data |

## 6. Qualifying call add-on (weeks 4 to 7, after Gate 0)

On a call with a brand that named $500 or more and controls the budget, run the plan's seven checks (Phase 2, "Brand qualification checklist") after question 7. Record the brand's own answer: Y, N or unsure. You verify each one yourself before any ship date (`handoff/how-to-fill-handoff-files.md`, the `verified_` columns).

| Check | Ask | Brand_Log column |
| --- | --- | --- |
| 1 | "Is it individually packaged, sealed and shelf-stable, with at least 60 days of shelf life left on the drop date?" | `qual_q1_sealed_shelf_stable_60d` |
| 2 | "Does the label show ingredients and all nine major allergens, sesame included?" | `qual_q2_labeled_ingredients_allergens` |
| 3 | "Which store within about ten blocks of here stocks you, or can you issue a discount code online?" | `qual_q3_buy_path_near_cluster` |
| 4 | "Could you ship 275 units, 250 plus a reserve, to one Manhattan address within ten business days?" | `qual_q4_can_ship_275_in_10bd` |
| 5 | "Do you carry product liability insurance, and could you send a certificate naming us as additional insured?" | `qual_q5_product_liability_insurance` |
| 6 | "Could you approve $600 yourself, without a committee?" | `qual_q6_contact_can_approve_600` |
| 7 | "Why New York, and why now?" (a new store, a launch, a local push) | `qual_q7_why_now` (their words) |
| Excluded | Check yourself: no alcohol, cannabis, CBD or THC, no Supplement Facts panel, nothing refrigerated or needing preparation, no health claim on the pack ("supports gut health" is a health claim; "10g protein" is not, but note it for review) | `qual_not_excluded` |

All seven Y plus `qual_not_excluded` = Y makes the brand "qualified on a call" on the scorecard. Then the proposal goes out within 24 hours (`messages/11-brand-post-call-conversion.md`, step 1). Any N stops it; any unsure is a question in the proposal email, not a guess.

## 7. Lines you do not cross

- No pitching inside the Startup CPG Slack or at its events. A conversation that starts there stays research until they ask what you do.
- Never claim a shelf sighting you did not make, offices that have not signed, or results that do not exist.
- The ladder words stay separate: delivered, placed, depleted, responded, scanned, purchased (code redemptions). Incremental purchases are not measured, and you say so.
- An opt-out in any words ends it the same day: `do_not_contact` = Y, `status` = `do_not_contact`, `opt_out_date` in Clay.

## Changelog

Round numbers are part B's rounds; a round that did not change this file is not listed.

- Round 1 (2026-10-24): plan questions kept verbatim and in order; added prep, opening, probes, column map, the anchor rule, Gate 0 rule, close, truthful answers, the seven-check add-on.
- Round 3 (2026-10-24): critique as a CPG founder pitched by every sampling vendor: "I'm not selling anything" followed by a price question would be seen through, so the opening now says plainly that a price question is coming and that their number comes first; `shortlist` added for the plan's 6 brands.
- Round 4 (2026-10-24): the close asks permission before anyone is quoted (`quote_ok_to_share`), which the Startup CPG posts require.
