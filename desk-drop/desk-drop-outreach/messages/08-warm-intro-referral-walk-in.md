# 08 · Warm introductions, referrals and the lobby walk-in

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** The three ways in that do not depend on cold email: people you already know (the plan wants five of the fifteen office conversations to start warm), names you are given, and a walk into a lobby with nothing to sell. These carry weeks 1 and 2, and from Thu 2026-10-29 their emails are what warms the new domain up.

**When it is used.**
- Part 1, warm: rows with `known_to_founder = Y` (and `how_we_know` filled), or `channel = warm-intro`. From day 1.
- Part 2, referral: whenever someone gives you a name, on a call or by reply (09, "Referral" and "Wrong person").
- Part 3, walk-in: office rows with `channel = walk-in`, or no email and no LinkedIn, in buildings whose lobby you can enter. Tuesday or Wednesday mornings only, during the walk sessions in `cluster-1-flatiron/walk.csv` (8 to 11 am, `sending/sending-setup.md` section 4), when pantry owners are in and the lobby looks as it will on a drop day. Use the first hour to see each lobby and ask for the pantry person from about 9:30, once the arrival rush has passed (assumption).

**Which address sends these.** Emails in this file go to people who know you or who were introduced, and they are the new domain's warm-up. Mon to Wed of week 1, before the new address is authenticated, send them from your existing address. **From Thu 2026-10-29, once a test email shows SPF and DKIM PASS, every one goes from [EMAIL] on [DOMAIN]**: warm asks, introductions, referral emails and walk-in follow-ups, aiming for 3 to 5 real two-way emails a day (`sending/sending-setup.md` sections 0 and 4). Always with the footer from file 02: every email about the business to an office or a brand contact is treated as commercial.

`sequence` values: use the side and stage as in 05 and 06 (`office-discovery-A` and so on). `channel` is `warm-intro` or `walk-in`. A referred contact gets `referral_from` = the referrer's `row_id`.

---

## Part 1 · Warm

These are discovery messages. Once a side's selling switch is Y (`office_selling_on`, `brand_selling_on`), the draft maker refuses 1a, 1c and 2b for that side, because each says nothing is for sale or that the idea is still being tested; write to people you know on that side with the selling version (05 or 06 part 2, or 07) and a first line on how you know them.

### 1a. Asking someone you know for an introduction (double opt-in)

You ask a friend or contact to check with the other person first. Nobody gets an email they did not agree to.

```message
id: warm-ask-office
side: office
stage: discovery
touch: 1
channel: warm-intro
subject: Could you introduce me to whoever runs the pantry at {company}?
ask: will they ask the pantry person first
---
Hi [CONNECTOR FIRST NAME],

I'm researching how offices around {CLUSTER} stock their pantries, before I build anything, and I'd like to talk to whoever looks after the pantry at {company}.

Would you be willing to ask them whether they'd take a 20-minute call with me? If they say yes, you can forward the note below as it is.

Thanks,

---
Note to forward:
[FOUNDER NAME] is researching how offices around {CLUSTER} run their pantries. The idea being tested: emerging snack and drink brands send sealed product to a few nearby offices, free, and the team says what it thought. Nothing is for sale yet. [FOUNDER NAME] would like 20 minutes to hear how it works at {company}: [EMAIL].

{SIGNATURE}
```

```message
id: warm-ask-brand
side: brand
stage: discovery
touch: 1
channel: warm-intro
subject: Could you introduce me to the founder of {company}?
ask: will they ask the founder first
---
Hi [CONNECTOR FIRST NAME],

I'm asking 15 founders of snack and drink brands how they get people in New York to try their product, and I'd like {company} to be one of them.

Would you be willing to ask {first_name_or_founder} whether they'd take a 20-minute call with me? If they say yes, you can forward the note below as it is.

Thanks,

---
Note to forward:
[FOUNDER NAME] is asking founders of snack and drink brands how they get people in New York to try their product, and what it costs. The idea being tested: putting sealed product in offices near the stores that carry it, with photos and employee feedback. There's nothing to buy yet. [FOUNDER NAME] would like 20 minutes: [EMAIL].

{SIGNATURE}
```

### 1b. When the introduction lands

Reply to the introduction email, move the connector to Bcc, and ask for the time. One ask.

```message
id: warm-intro-landed
side: both
stage: discovery
touch: 1
channel: warm-intro
subject: Re: (the introduction)
ask: a time for the call
---
Thanks, [CONNECTOR FIRST NAME] (moving you to Bcc).

{greeting} thank you for saying yes. Would [TIME OPTION 1] or [TIME OPTION 2] work for 20 minutes, by phone or video?

{SIGNATURE}
```

### 1c. Writing directly to someone you know

For `known_to_founder = Y`. The first line must be true and checkable by them (`how_we_know`); if you cannot write that line, use the cold version.

```message
id: warm-direct
side: both
stage: discovery
touch: 1
channel: warm-intro
subject: A question about [PANTRY OR SAMPLING], for some research I'm doing
ask: a 20-minute call
---
{greeting}

[HOW WE KNOW EACH OTHER]

I'm testing an idea before I build it: emerging snack and drink brands send sealed product to a few offices around {CLUSTER}, free, and the brand gets photos and the team's feedback. You're one of the first people I wanted to ask, because [ONE TRUE REASON: you run the pantry at {company} / you have run sampling for {company}].

Would you give me 20 minutes in the next two weeks?

{SIGNATURE}
```

`[PANTRY OR SAMPLING]`: "office pantries" for an office contact, "sampling in New York" for a brand contact.

---

## Part 2 · Referrals

### 2a. Asking for a name after a call

The office call guide ends with "Who else runs a pantry nearby that I should talk to?" (plan, Phase 0, question 7) and the brand debrief ends with "Who else should I be talking to?". If they named someone on the call but you have no way to reach them, ask permission to use their name. One ask.

```message
id: referral-permission
side: both
stage: discovery
touch: reply
channel: email
subject: Re: (your thank-you email after the call)
ask: may I say they suggested it
---
{greeting}

You mentioned that [REFERRED NAME] at [REFERRED COMPANY] [RUNS THE PANTRY THERE / RUNS MARKETING THERE]. Would you be comfortable with me saying you suggested I write to them?

{SIGNATURE}
```

Their yes sets `referrer_ok_to_name = Y` on the new row. A no, or no answer: write to the new person without naming them.

### 2b. Writing to the referred person

```message
id: referral-first-touch
side: both
stage: discovery
touch: 1
channel: email
subject: {referrer_first_name} suggested I write to you
ask: a 20-minute call
---
{greeting}

{referrer_name} suggested I write to you.

[OFFICE: I'm researching how offices around {area} stock their pantries, and the idea I'm testing is emerging snack and drink brands sending sealed product to a few nearby offices, free, with the team saying what it thought.]
[BRAND: I'm talking to founders of snack and drink brands about how they get people in New York to try their product, and the idea I'm testing is putting sealed product in offices near the stores that carry it.]

It's questions only, about 20 minutes. Would you have time in the next two weeks?

{SIGNATURE}
```

Keep the bracketed sentence for their side and delete the other. Without `referrer_ok_to_name = Y` the subject and first line come out; use the ordinary first touch from 05, 06 or 07 instead.

### 2c. Asking for a referral when the answer is no or silence

The plan: "No or silence after two follow-ups: thank them, ask for one referral, move on." Touch 3 in 05 does this for offices. For a brand or office that said no on a call (not an opt-out):

```message
id: referral-after-no
side: both
stage: any
touch: 1
channel: email
subject: Re: (the last thread)
ask: one name
---
{greeting}

Thank you for being straight with me. Is there one person you'd suggest I talk to instead?

{SIGNATURE}
```

Send it the same day when the no was said on a call. When the no comes by email after a conversation, answer with 09, H instead, which thanks them and asks for the name in one reply; never send both.

Never after an opt-out. "No thanks", "not interested" or "stop" is an opt-out (09): no reply at all.

---

## Part 3 · The lobby walk-in (offices only)

**Before you go.** Pick buildings from `cluster-1-flatiron/buildings.csv`: `lobby_type` walk-up first, then security desk; skip loading-dock-only buildings. Bring nothing to sell and no product. Bring plain cards with your name, [PHONE] and [EMAIL] written on them. Printed copies of the discovery one-pager only once it counts as ready (`discovery_onepager_ready = Y` and `name_decided = Y`, or D's name-free version, `04-slot-state.csv`): D's page names the business, and nothing you hand out names it before the decision, the same rule as email (02).

**Never.** Go past a security desk without being sent up. Follow someone through a door. Leave food or anything else in a lobby. Photograph people, desks or screens. Ask for an employee's name or number. Go in where a sign says "no soliciting". Stay after anyone asks you to leave.

### 3a. At a security desk (multi-tenant building)

> "Hi, I'm [FOUNDER NAME]. I'm not delivering anything. I'm researching how offices around here run their pantries. Is there a way to leave a note for the office manager at {company}?"

- **Yes:** hand over the card (or the one-pager, once it counts as ready) with the note below. Thank them. Leave.
- **No, or "they don't take visitors":** "No problem, thank you." Leave. Log it as `walk-in`, note "desk declined" in `call_notes`, and try LinkedIn.
- **"What company are you with?":** before `name_decided = Y`: "It's a small New York business I'm setting up. The working name is {BRAND_NAME}, and it may change. There's nothing to sell yet." After: "{BRAND_NAME}. It's a small New York business I'm setting up; there's nothing to sell yet." (The same answer as the call guides in `calls/`.)

### 3b. At a reception desk (an office on its own floor, or a walk-up)

> "Hi, I'm [FOUNDER NAME]. I'm not selling anything today. I'm talking to offices around here about how their pantries work. Would the person who looks after your pantry have two minutes, or should I leave a note for them?"

- **The person comes out:** use the 30 seconds below, then ask for the call.
- **"Leave a note":** hand over the card (or the ready one-pager) with the note. Thank them. Leave.
- **"We don't do that here":** "Understood, thank you." Leave. Do not ask again at this office. Log it the same day as an opt-out for that office: `status = do_not_contact`, `do_not_contact = Y`, `opt_out_date` = today, `call_notes` = "reception: no solicitation". No email or LinkedIn message follows.

### 3c. Thirty seconds with the person who runs the pantry

> "Thanks for coming out. I'm researching how offices around Flatiron stock their pantries, before I build anything. The idea is that emerging snack brands would send sealed product to a few offices, free, and the team would say what it thought. I'd like to hear how it works here and whether that would help or get in the way. Could I have 20 minutes another day? Whatever suits you."

If they say yes, write down the day and time they give and the best email for them (a business address only). Nothing else.

### 3d. The note to leave (handwritten on the card, or on the back of the one-pager)

> For whoever looks after the pantry at {company}: I stopped by to ask how your pantry works. I'm researching office pantries around Flatiron before building anything. Would you give me 20 minutes? Questions only. [FOUNDER NAME] · [PHONE] · [EMAIL]

### 3e. The same-day follow-up, if you were given an email

```message
id: walk-in-follow-up
side: office
stage: discovery
touch: 2
channel: walk-in
subject: Following up from your front desk today
ask: a time for the call
---
{greeting}

Thank you for coming out to the front desk today. As I said, it's research: how offices around {area} stock their pantries, and whether sealed product from emerging brands would help or get in the way.

Would [TIME OPTION 1] or [TIME OPTION 2] work for 20 minutes?

{SIGNATURE}
```

**Log the walk-in within the hour.** `channel = walk-in`, `status = contacted`, `touch_1_date` = today, `call_notes` = who you spoke to (role only: "receptionist", "security desk") and what they said, `next_action = send_touch_2` with `next_action_date` = +3 business days if you have an email, else `recontact` in a week by LinkedIn.

---

## Changelog

- Round 1 (2026-10-24): drafted the warm, referral and walk-in pieces from plan Phase 0 (five warm of fifteen; walk-ins with nothing to sell; question 7) and Phase 1 step 5 (ask for one referral).
- Round 2 (2026-10-24): the walk-in follow-up subject no longer breaks on the company fallback; the "what company are you with?" answer matches the call guide in `calls/`; the referral permission ask is marked as a reply.
- Merge (2026-10-24): header line unified with the rest of the folder; walk-in times now match the sending guide and B's walk sessions (Tuesday or Wednesday mornings; it said Tuesday to Thursday, 10:00 to 11:30 or 14:00 to 16:00).
- Review round 1 (2026-10-24): from Thu 2026-10-29 every email here goes from [EMAIL] on [DOMAIN], as the domain's warm-up; the forward notes say "nothing is for sale yet" and "nothing to buy yet" (file 02's rule); "I'm asking 15 founders"; reception's "we don't do that here" is written to Clay as an opt-out; the company answer gives the working name as one that may change until the name is decided.
- Review round 2 (2026-10-24): walk-ins hand out plain cards until the discovery one-pager may go (it names the business, so it waits for `name_decided = Y` or a name-free version from D), the same rule as email.
- Review round 3 (2026-10-24): 1a, 1c and 2b are refused for a side once it sells (each says nothing is for sale or the idea is still being tested).
