# Office call guide

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/calls/`

**What it is for.** Running a 20-minute discovery conversation with the person who runs an office pantry, and coming away with the numbers Gate 0 needs: a yes in principle, the pantry owner's name and a receiving window. The seven questions are the plan's (Phase 0, "Office conversation guide"), word for word and in the plan's order. Everything else here is the wrapping: what to have open, what to listen for, which tracker column each answer goes in, and how to answer their questions truthfully.

**When it is used.** Weeks 1 to 3 (Mon 2026-10-26 to Fri 2026-11-13, derived, founder to confirm) on every office call, video call or sit-down. After Gate 0 the same guide runs recruiting calls, with the close in section 5 doing more of the work. A lobby walk-in uses the short version in section 7.

**No selling in weeks 1 to 3.** You are learning how their pantry works. You do not offer a drop date, a brand, or a sign-up. The only things you may ask for are the answers below, a referral, and "can I send you a one-pager?" at the end (plan, Phase 1 conversion path, step 1).

---

## 1. Before the call (2 minutes)

- Open the contact's row in the Clay offices table and a new row on **Office_Log** in `tracking/conversation-tracker.xlsx` (Google Sheets). Paste the `row_id`, company, name and title now, so the note later is only answers.
- Glance at: `onsite_band` (an estimate; never say it to them), the building's lobby type (`cluster-1-flatiron/companies.csv`, `building_lobby_type`), and the two or three nearest stores in `cluster-1-flatiron/retailers.csv`.
- Have the budget probe (question 6) on screen. It is read word for word.
- Have `calls/post-call-note-template.md` open in a second tab. Block ten minutes after the call for it.
- Start a 20-minute timer. The plan says 20 minutes; keep the promise.

## 2. Opening (30 seconds)

Say who you are and what this is, then ask permission to take notes.

> "Thanks for making the time. I'm [FOUNDER NAME]. I'm looking at whether it would help offices around here to get vetted emerging snack and drink brands for free, in exchange for a shelf photo and a three-question team survey. Before I build anything I want to understand how pantries actually work. I'm not selling anything today. Is it OK if I ask about seven questions and take notes? It'll take 20 minutes."

If they ask "who are you with?": the honest answer on the day. Until the company is formed, "I'm setting up a small New York business called {BRAND_NAME}; it isn't formed yet, and nothing would arrive before it's formed and insured." (`{BRAND_NAME}` is the working name, kept in one place in `desk-drop-legal-pack/02-email-footer-and-checklist.md` and `messages/`.)

## 3. The seven questions (plan wording, plan order)

Time boxes add up to about 17 minutes, leaving 3 for the close. Write down their words, not your summary; the tracker columns for each answer are in the right-hand cell.

| # | Ask exactly | Minutes | Listen for, then probe | Goes in (Office_Log) |
| --- | --- | --- | --- | --- |
| 1 | "How does your pantry work today? Who chooses, who delivers, how often, and roughly what does it cost a month?" | 4 | Who decides (that may be the pantry owner: note the name and title). How it arrives (a grocery order, a snack service, a Costco run). Cadence. A cost figure or range. If they won't give a cost, move on: it is optional. | `q1_pantry_today_verbatim`, `pantry_vendor`, `uses_snack_service` (Y if a snack service or vendor stocks it), `monthly_pantry_spend_usd` (a number only if they gave one; a range: its low end), `monthly_pantry_spend_verbatim`; owner name into `pantry_owner_name` / `pantry_owner_title` |
| 2 | "How many people are actually in on a Tuesday?" | 1 | A number or range for Tuesday, not total headcount. If they only know total staff, ask "roughly what share come in on a Tuesday?" and note both. | `tuesday_headcount` (low end of a range), `headcount_verbatim` |
| 3 | "Do brands ever reach out offering free product? What happens when they do?" | 2 | Whether they ignore, accept or block such offers, and why. This tells you how the first email will be read. | `q3_brands_reach_out` (Y/N), `q3_free_product_verbatim` |
| 4 | "If a vetted emerging brand showed up with 50 units and a card explaining it, what would you need to say yes? What would make you say no?" | 4 | Allergens, approvals (facilities, HR, a landlord), building rules (security desk, certificate of insurance, freight hours), where it would sit, categories they would never want. Probe each "no" once: "what would make that OK?" | `q4_yes_needs_verbatim`, `q4_no_triggers_verbatim`, `objection_1` to `objection_3` (codes), `objections_verbatim`, `veto_categories` (category keys), `veto_verbatim`, `receiving_type`, `coi_required`, `security_notes` |
| 5 | "Would you take a photo of it on the shelf and post a three-question survey link in Slack?" | 2 | Yes, no, or "we use email / Teams". A hesitation here is an objection: code it (`commitments_too_much` or `survey_concern`). | `q5_photo_and_survey` (Y, N, maybe), `q5_verbatim` |
| 6 | First one line of framing, so it is not heard as a catch: "One hypothetical question, and it changes nothing about the free drop." Then the budget probe, word for word: **"If this goes well and we offered a guaranteed twice-monthly curated drop of products your team voted for, would that have a budget? Roughly what range per month?"** | 2 | Read it exactly, then stop talking. Do not suggest a number. If they ask "what would it cost?", say "I don't know yet; that's why I'm asking." Write the answer word for word, including "no budget" and "I'd have to ask". | `budget_probe_asked` = Y, `budget_probe_verbatim`, `budget_probe_low_usd` and `budget_probe_high_usd` (USD per month; a range: low and high; "no budget" or "zero": 0 and 0; "don't know" or no number: both blank) |
| 7 | "Who else runs a pantry nearby that I should talk to?" | 1 | Company and title (business contacts only). Then ask: "Would it be all right if I said you suggested I get in touch?" | `referrals_given_count`, `referrals_given` ("Company - Title; ..."). Each name becomes a new Clay row; their answer about being named goes in that row's `referrer_ok_to_name` |

The probe is asked once, at intake (plan, "The budget probe"). If you are speaking to an office for the second time and already have the answer, set `budget_probe_asked` = N and leave the verbatim blank. The first answer is the one that counts.

## 4. A yes, a maybe and a no

**What a yes looks like** (plan, Phase 0): they name a receiving window unprompted, they ask "when", or they introduce you to a colleague before the call ends. Tick which you saw in `yes_signals`.

**What counts for Gate 0.** An office counts toward the 5 of 15 only when all three are in the row: `yes_in_principle` = Y, `pantry_owner_named` = Y, and a `receiving_window`. The scorecard does this check; a Y without the other two shows up as follow-up work ("Offices that said Y but owner or window is missing").

| They say | `yes_in_principle` | Also set |
| --- | --- | --- |
| "Yes, we'd do that. [Name] receives deliveries, mornings are best." | Y | `pantry_owner_named` = Y, `owner_can_say_yes_alone` = Y, the window |
| "Sounds good, but I'd have to ask facilities / HR / the landlord." | maybe | `owner_can_say_yes_alone` = N, `other_approver` (facilities, hr, ceo-or-assistant, landlord-or-building, finance, other), objection `needs_approval`. Plan Phase 1: this is a maybe, not a yes |
| "Interesting, send me something." | maybe | Ask the close questions in section 5 before you hang up |
| "Not for us." | N | Their reason in `objections_verbatim` and a code |

## 5. The close (3 minutes)

1. **If they sounded positive, get the two Gate 0 facts.** "If we did a first drop, who would receive it, and what's a good window on a Tuesday or Wednesday morning?" Write the name, title and window. Do not propose a date in weeks 1 to 3.
2. **Ask the plan's closing question:** "Can I send you a one-pager?" In weeks 1 to 3 that is the discovery one-pager (`desk-drop-identity/pdf/discovery-one-pager-BLANK.pdf`, once your details are filled in). From Gate 0, the office one-pager with a proposed first-drop week (`messages/10-office-post-call-conversion.md`, step 1, sends it the same day).
3. **Ask before you ever quote them:** "When I share what office managers are telling me, with other founders, may I quote something you said, without your name or your company?" Write Y in `quote_ok_to_share` only on a clear yes.
4. **Thank them and stop on time.**
5. After the call, mark `shortlist` = Y if this is one of the offices you would pursue first (the plan's Gate 0 deliverable is a shortlist of 8). Anyone you knew before this call is `channel` = warm-intro; the plan wants five of the fifteen office conversations from your own network.

## 6. Their questions, answered truthfully

Say only what is true on the day. Progress claims (offices signed, brands lined up, a drop date) come from the tracker and `messages/04-slot-state.csv`, never from memory.

| They ask | Say | Never say |
| --- | --- | --- |
| "Which brands?" | "None yet. I'm talking to emerging New York brands this month. You'd see each one before it came, and you could veto any." | A brand name you have not qualified |
| "When would it start?" | Weeks 1 to 3: "Not before January. The first drop is planned for [DROP DATE: Tue 2027-01-12], and only once five offices and the first brands have signed." After that, the slot in `messages/04-slot-table.csv` | A firm date before `drop_date_confirmed = Y` |
| "What does it cost us?" | "Nothing. No fees in either direction. We ask for the shelf placement the day it arrives, two photos, one survey post and a ten-minute chat afterwards." | "Free forever" |
| "Who else is doing it?" | Weeks 1 to 3: "You'd be one of the first. I'm talking to about fifteen office managers around here." | "Lots of offices nearby" |
| "Is it safe? Allergens?" | "Only sealed, shelf-stable, commercially labeled products, and the card repeats the allergen line from the package word for word." | Any health claim about a product |
| "Do you collect our employees' details?" | "No. The survey is anonymous. Nobody signs in." | Anything about collecting emails (the optional brand-newsletter box is the brand's, opt-in, and only if a brand chooses it) |
| "Are you insured?" | Before insurance is bound: "We will carry general liability insurance before your first drop." After `gl_bound = Y`: "We carry general liability insurance." | "Fully insured" before it is bound |
| "What happens to leftovers?" | "Collected at the end of the week or left with you, whichever the brand chose. Nothing is left in a lobby." | |

## 7. The lobby walk-in version (3 minutes, offices only)

Use it when the person who runs the pantry comes down to the lobby or the reception desk after you ask for them (the walk-in words are in `messages/08-warm-intro-referral-walk-in.md`, part 3). Bring nothing to sell; the plan allows walk-ins only on that basis.

1. One sentence on who you are (section 2, shortened).
2. Question 2 ("How many people are actually in on a Tuesday?").
3. Question 4, the yes half only ("what would you need to say yes?").
4. "Could we do the full 20 minutes this week or next? Phone or here, whichever is easier."
5. Log it: on a walk-in, set Clay `touch_1_date` and `channel` = walk-in. It becomes an Office_Log row (`call_type` = walk-in) only if you asked questions 1, 2 and 4 of the person who runs the pantry. Otherwise it is a touch, not a conversation, and the tracker does not count it.

## 8. What counts as a conversation

The scorecard counts a conversation once per office (distinct Clay `row_id`). Log a row on Office_Log when you spoke to the person who runs the pantry, or to someone who could name them, and asked at least questions 1, 2 and 4. A receptionist taking a message is not a conversation; it is a touch, recorded in Clay only.

## 9. Lines you do not cross

- Business contacts only. Never write an employee's name or anything about one. The pantry owner is a business contact; their colleagues are not.
- No photos of people, ever. No photos inside an office unless the pantry owner offers.
- Verbatims are their words. If you could not catch the exact words, start the cell with "paraphrase:".
- An opt-out in any words ("please don't contact me again") ends it: thank them, and the same day set `do_not_contact` = Y, `status` = `do_not_contact` and `opt_out_date` in Clay.

## Changelog

- Round 1 (2026-10-24): plan questions kept verbatim and in order; added prep, opening, probes, column map, Gate 0 rule, close, truthful answers, walk-in version.
- Round 4 (2026-10-24): `uses_snack_service`, `q3_brands_reach_out` and `other_approver` added so the Startup CPG post numbers (`messages/12-startup-cpg-posts.md`) are counts, not guesses; the close now asks permission before anyone is quoted (`quote_ok_to_share`).
- Round 3 (2026-10-24): critique as an office manager who deletes forty vendor emails a day: the budget probe right after "it's free" reads like a bait and switch, so it now gets one line of framing before it (the probe itself is unchanged); `shortlist` added to the close for the plan's 8 offices; `channel` = warm-intro is now defined as "anyone you knew before", which the Scorecard counts against the plan's five warm conversations.
