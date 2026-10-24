# 09 · Reply playbook

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Every kind of reply, what it means, what to write back (one ask, at most), and exactly what to change in the Clay row, so a reply takes two minutes and nothing is decided from scratch.

**When it is used.** The moment a reply arrives, on any channel. Read it, find its type below, send the answer (or nothing, for an opt-out), and write the Clay columns in the same sitting. Calls themselves run from the call guides in `calls/`.

**The `reply_type` values and status writes are shared with the tracker** (`_work/partB/FOR-PART-A.md`; the tracker in `tracking/` reads them). Status values are CONTRACTS section 4 only.

---

## The table

| `reply_type` | It looks like | Status to set | `next_action` | Reply? |
| --- | --- | --- | --- | --- |
| `yes` | "Sure, happy to talk", "Tuesday works" | `replied`, then `call_booked` once a time is set | `book_call`, then `run_call` | Yes, A |
| `maybe` | "Possibly", "Tell me more first", "Not sure it's for us" | `replied` | `recontact` | Yes, B |
| `needs_approval` | "I need to ask facilities or HR", "I'd have to run it by our COO" | `replied` (a maybe, not a yes; `yes_in_principle` stays N) | `recontact` | Yes, C |
| `send_info` | "Send me more info", "Do you have a deck?" | `replied` | `book_call` | Yes, D |
| `wrong_person` | "That's not me", "Talk to our office manager" | `wrong_person`; the named person becomes a new row with `referral_from` = this `row_id` | `none` on this row | Yes, E |
| `referral` | "You should talk to X at Y" | `replied`; new row for X with `referral_from` | `ask_referral` (permission) | Yes, F |
| `not_now` | "Ask me in January", "No budget until Q1" | `not_now` with `next_action_date` | `recontact` | Yes, G |
| `no` | A decline after a real conversation that leaves the door open: "Not for us this year, but keep me posted" | `no` | `none` | Yes, H |
| `opt_out` | "No thanks", "Not interested", "Stop", "Unsubscribe", "Remove me", or any reply that says so in other words | `do_not_contact`, `do_not_contact = Y`, `opt_out_date` = today, the same day | `none` | **No reply at all** |
| `obj_seed_ourselves` | "We can seed offices ourselves for free" | `replied` | `book_call` | Yes, J1 |
| `obj_price` | "$600 for 250 units is more than we pay per sample elsewhere" | `replied` | `book_call` | Yes, J2 |
| `obj_free_trial` | "Can we do a free trial first?" | `replied` | `send_proposal` | Yes, J3 |
| `obj_what_we_get` | "What do we actually get out of it?" | `replied` | `book_call` | Yes, J4 |
| `obj_other` | Any other question or worry (list K) | `replied` | as the answer says | Yes, K |
| `out_of_office` | An automatic reply | unchanged (`contacted`) | the next touch, moved to 2 business days after their return date (no date given: +5 business days) | No |
| `bounce` | "Address not found" | unchanged; `email_status = none`; `channel = linkedin` | the LinkedIn first touch (07) | No |
| (blank) | **Silence**: no reply 5 business days after the last touch | see "Silence" below | `recontact` | No |

Write `last_reply_date` for every reply, and the reply's key words, verbatim, at the top of `call_notes` (objections verbatim are a Gate 0 output). **The opt-out rule overrides the rest:** if a reply mixes a question with "stop" or "not interested", it is an opt-out.

**Which is `no` and which is `opt_out`.** The footer on every email says: Reply "no thanks" and I won't email you again (desk-drop-legal-pack/02). So any written "no thanks", "not interested" or "no" to the email itself is an `opt_out`. `no` is only for a decline given in a conversation you were already having (on a call, or after they had said yes to talking), where they did not ask you to stop. When in doubt, treat it as `opt_out`.

---

## The replies

Each answer is short, true today and asks one thing. Fill `{tokens}` and `[SLOTS]` as in 03 and 04. Every email carries `{SIGNATURE}` (file 02). Answers marked *discovery* are for weeks 1 to 3: they never state a price, an offer or a roster.

### A. `yes`: book the call

```message
id: reply-yes
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: pick a time
---
{greeting}

Thank you. Would [TIME OPTION 1] or [TIME OPTION 2] work, by phone or video? If neither does, send me a time that suits you.

{SIGNATURE}
```

Once a time is set: `status = call_booked`, `call_date`, `next_action = run_call`. The day before, one line: "Looking forward to tomorrow at [TIME]. I'll call [PHONE OR LINK]." (no ask). Run the call from `calls/`.

### B. `maybe`: find out what would decide it

```message
id: reply-maybe
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: what would help them decide
---
{greeting}

No rush at all. What would help you decide whether it's worth 20 minutes?

{SIGNATURE}
```

`next_action_date` = [CHECK-BACK DATE] (+5 business days). If they do not answer, one more line on that date ("Happy to leave this here if it's not a fit.") and then treat it as silence.

### C. `needs_approval`: "I need to ask facilities or HR"

The plan: this is a maybe, not a yes. Make their internal ask easy with a note they can forward, then check back once.

```message
id: reply-needs-approval
side: office
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: may I check back on a date
---
{greeting}

That makes sense. Here's a short note you can forward as it is:

What it is: sealed snacks or drinks from one to three emerging brands, free, roughly monthly, delivered on a Tuesday or Wednesday morning in our receiving window. We choose the categories and can say no to any brand.
What it asks of us: put it out the day it arrives, two photos, one Slack or email post of an anonymous three-question survey, and a ten-minute chat afterwards.
What it never involves: any fee, employees' contact details, exclusivity, or storing anything.
Safety: only individually packaged, sealed, shelf-stable products labeled with ingredients and allergens; no alcohol, cannabis, supplements or health claims. Each brand carries product liability insurance of at least $1 million. [INSURANCE LINE] If our building needs a certificate of insurance for deliveries, they arrange it before the first drop. We can leave with a week's notice.

Shall I check back on [CHECK-BACK DATE]?

{SIGNATURE}
```

In discovery the same note works with the first line changed to "What's being tested:" and "would be" in place of "is". Facts in the note: product standard, insurance, building certificate and a week's notice are in desk-drop-legal-pack/03 sections 4 and 8; two photos, the survey post and the debrief in section 3.

### D. `send_info`: send the right page and ask for the call

"Send more info" is often a polite exit. Send one page, say the short version in two lines, and ask once.

```message
id: reply-send-info-discovery
side: both
stage: discovery
touch: reply
channel: email
subject: Re: (their thread)
ask: a 20-minute call
---
{greeting}

Attached is a one-page description of the idea. The short version: [OFFICE: free sealed product from emerging brands, roughly monthly once it runs, and three questions for your team] [BRAND: sealed product in offices near the stores that carry you, with photos, counts and feedback], and I'm still finding out whether it's worth building.

Would 20 minutes on [TIME OPTION 1] or [TIME OPTION 2] work?

{SIGNATURE}
```

Attach the discovery one-pager only if `discovery_onepager_ready = Y`. If not, leave out the first sentence and say "I can explain it better in 20 minutes than in a document."

```message
id: reply-send-info-selling
side: both
stage: selling
touch: reply
channel: email
subject: Re: (their thread)
ask: a 20-minute call
---
{greeting}

Attached is the one-page outline. The short version: [OFFICE: free drops from emerging brands roughly monthly, you choose the categories, and in return it goes out the day it arrives, two photos and three survey questions for your team] [BRAND: five offices for a week, about 250 units, photos, counts, a survey and a one-page report, $600 paid before you ship].

Would 20 minutes on [TIME OPTION 1] or [TIME OPTION 2] work?

{SIGNATURE}
```

Offices get the office one-pager (`office_onepager_ready`, with the first-drop week); brands get the brand one-pager (`brand_onepager_ready`, with today's roster status). Use the bracketed sentence for their side and delete the other. When the founding places are gone, the brand sentence becomes "ten offices for a week, about 500 units, photos, counts, a survey and a one-page report, $1,500, half when you sign".

### E. `wrong_person`: ask who

```message
id: reply-wrong-person
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: who is the right person
---
{greeting}

Thank you, and sorry for the misdirected note. Who would be the right person to ask?

{SIGNATURE}
```

If they name someone: new Clay row (business details only: name, title, business email or LinkedIn), `referral_from` = this `row_id`, and ask permission to use their name only if you want to (F). Write to the new person with 08 part 2b.

### F. `referral`: thank them and ask to use their name

```message
id: reply-referral
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: may I say they suggested it
---
{greeting}

Thank you, that's kind. Would you be comfortable with me saying you suggested I write?

{SIGNATURE}
```

Yes sets `referrer_ok_to_name = Y` on the new row. Then 08 part 2b.

### G. `not_now`: agree a date and keep it

```message
id: reply-not-now
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: none (states the date)
---
{greeting}

Understood, thank you for saying so. I'll check back in [MONTH THEY NAMED, or: January]. If another month is better, just tell me.

{SIGNATURE}
```

`status = not_now`, `next_action = recontact`, `next_action_date` = the first Tuesday of the month they named (none named: [RECONTACT DATE: Tue 2027-01-19]). On that date use the selling or discovery touch 1 that is unlocked then, opening with "You asked me to check back in [MONTH]."

### H. `no` after a conversation

```message
id: reply-no
side: both
stage: any
touch: reply
channel: email
subject: Re: (their thread)
ask: none
---
{greeting}

Thank you for telling me, and for the time you gave this. I won't follow up on it.

{SIGNATURE}
```

`status = no`. Do not ask for a referral in the same email; if you want one, 08 part 2c, once, a week later. Never put a `no` row back in a daily view.

### I. `opt_out`: no reply, same-day write-back

Do not reply. Do not ask why. Do not confirm. Do not send a "sorry to see you go" email (desk-drop-legal-pack/02, notes). The same day:

1. `do_not_contact = Y`, `status = do_not_contact`, `opt_out_date` = today, `reply_type = opt_out` in the Clay row.
2. Stop every channel: withdraw a pending LinkedIn invitation, cancel any scheduled draft, never walk in.
3. If the same company has another contact in Clay, leave that row alone unless the reply said "anyone here".
4. Never re-add the person from a new list. The daily views exclude `do_not_contact = Y` rows (CONTRACTS 6.2).

The legal limit is ten business days; the rule here is the same day.

### J. The four brand objections

These are the plan's four (Phase 2), rewritten so every sentence is true on the day it is sent. Each ends with one ask.

**J1. `obj_seed_ourselves`: "We can seed offices ourselves for free."**

```message
id: reply-obj-seed-ourselves
side: brand
stage: selling
touch: reply
channel: email
subject: Re: (their thread)
ask: would a sample report page help
---
{greeting}

You can, and some brands do. The slow part is finding the person who runs each pantry and getting a yes, then getting the product out the day it arrives and a photo back. [OFFICE HOURS LINE] What you'd be paying for is that work and the report: photos, counts and what employees said, each kept separate.

Would it help to see what a report page looks like?

{SIGNATURE}
```

Attach `desk-drop-identity/pdf/report-SAMPLE-5-offices.pdf` if they say yes. It is marked SAMPLE and its numbers are illustrative placeholders, not results; say so in the email: "The numbers on it are made up, to show the layout."

**J2. `obj_price`: "$600 for 250 units is more than we pay per sample elsewhere."**

```message
id: reply-obj-price
side: brand
stage: selling
touch: reply
channel: email
subject: Re: (their thread)
ask: what would it need to show
---
{greeting}

That's fair, and per unit it is about $2.40 plus your product. For comparison, one in-store demo shift, a single demonstrator for four to eight hours at one store, runs about $300 to $700 (T-ROC's 2026 pricing guide). This is five offices for a week, seen by the same people each day, with photos, counts and their comments in a one-page report. If cost per sample is the measure that matters most to you, this may not be the right fit.

What would it need to show for $600 to be worth it to you?

{SIGNATURE}
```

The answer to the question is Gate 0 and pricing evidence: record it verbatim in `call_notes`.

**J3. `obj_free_trial`: "Can we do a free trial first?"**

```message
id: reply-obj-free-trial
side: brand
stage: selling
touch: reply
channel: email
subject: Re: (their thread)
ask: may I send the proposal
---
{greeting}

I don't run free trials. The founding price is the trial: $600 for five offices, and your next two campaigns stay at $120 an office for up to ten offices. If an office hasn't put your product out by the day after delivery, you get $120 back for that office.

Shall I send the one-page proposal so you can see every term?

{SIGNATURE}
```

Terms as desk-drop-legal-pack/10 v0.8 (sections 3 and 8). When `founding_taken = 3` the founding price is gone: say "There's no free trial. A standard campaign is $1,500 for ten offices, half when you sign and half when we confirm placement, and any office that hasn't put it out by the day after delivery comes off the invoice."

**J4. `obj_what_we_get`: "What do we actually get out of it?"**

```message
id: reply-obj-what-we-get
side: brand
stage: selling
touch: reply
channel: email
subject: Re: (their thread)
ask: would a sample report page help
---
{greeting}

A placement photo from every office, how many units were placed and how many were depleted by day five, an anonymous three-question survey in employees' own words, QR scans, and code redemptions at day 30 if you give us a code. Then a one-page report within seven business days with a recommendation on whether to do it again. What it won't tell you is whether anyone bought because of it, and the report says so.

Would it help to see what a report page looks like?

{SIGNATURE}
```

### K. Other questions (`obj_other`)

Answer in one or two true sentences and ask the open question again.

| They ask | Answer (then repeat the one ask) |
| --- | --- |
| "How did you get my email?" | "From [the public page in `source_url`, in words: your company's website / your LinkedIn profile / a press release]. I'll stop if you'd rather I didn't write." |
| "Who are you? Is this real?" | "Fair question. I'm [FOUNDER NAME], [ONE TRUE LINE ABOUT YOU]. My LinkedIn is [LINKEDIN URL], and I'm happy to talk by phone first: [PHONE]." |
| "Is this a sales call?" (discovery) | "No. There's nothing to buy yet; I'm asking questions before I build it." |
| "What does it cost?" (discovery, brand) | "I have a working number and I'll tell you on the call. I'd like to hear what it would be worth to you first, so I don't anchor you." (Plan: let them name a number before $1,500.) |
| "What does it cost us?" (office) | "Nothing, ever. Brands pay for the placement; offices never pay." |
| "We already have a snack service." (office) | "That's fine: this adds to your pantry, it doesn't replace it. Each drop is one case per brand, sized to your Tuesday headcount, and you can say no to any of it." |
| "Our building needs a certificate of insurance." (office) | "We'll arrange it with the building before the first drop. [INSURANCE LINE]" |
| "What about allergies?" (office) | "Every product is sealed and labeled with ingredients and allergens, and the card repeats the package's allergen line word for word. You can veto any allergen or category." |
| "Will brands email my team?" (office) | "No. We collect nothing about your employees. The survey is anonymous; the only optional box lets someone ask the brand for its newsletter themselves." |
| "Can we pick the offices?" (brand) | "The roster is fixed for each drop, by neighborhood, industry and Tuesday headcount, and each office approves your brand before it goes." |
| "Can we get employees' emails?" (brand) | "No. We don't collect employee data. People who want your newsletter can tick a box on the survey and give it to you themselves." |
| "Can you guarantee placement, or sales?" (brand) | "No guarantees. What the agreement does say: any office that hasn't put it out by the day after delivery comes off the bill. Sales can't be promised, and the report doesn't pretend to measure them." |
| "Who else is in the drop?" (brand) | "Up to two other brands, never one in your category in the same drop." |
| "Do you work with [another vendor]?" | "No." (Never claim a partner, client or relationship that does not exist.) |

---

## Silence

No reply 5 business days after the last touch of a sequence:

- **Cold sequences (05, 06, 07):** `status = not_now`, `next_action = recontact`, `next_action_date` = [RECONTACT DATE: Tue 2027-01-19] for anything parked before Fri 2026-12-11. On that date, one email: the touch 1 that is unlocked then (selling if it is on), opening with "I wrote in [MONTH] about [the pantry at {company} / sampling in New York]." No reply to that: `status = no`. That is four emails in all, the most anyone gets.
- **Conversion sequences (10, 11):** follow their own silence steps (two follow-ups, then thanks and one referral ask, then `not_now`).
- **Never** "just checking in", "bumping this up", "did you see my email?" or a guilt line.

---

## Changelog

- Round 1 (2026-10-24): drafted every reply type in Part B's `reply_type` list, the plan's four objections (rewritten so each is true on the day it is sent, with T-ROC's checked demo price and the agreement's per-office refund), the facilities and HR note and the silence rule.
