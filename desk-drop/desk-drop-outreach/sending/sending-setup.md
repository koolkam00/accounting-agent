# Sending setup

Version 1.0 · 2026-10-24 · workstream E, part B · `desk-drop-outreach/sending/`

**What it is for.** Getting outreach email from a brand-new domain into inboxes without burning the domain, and keeping the first three weeks on schedule while the domain is too new to use for cold email. It covers: SPF, DKIM and DMARC for Google Workspace on [DOMAIN]; a warm-up schedule with daily volumes; a week-one plan that does not depend on the domain; plain Gmail versus a sequencer, with costs; and what to change if the reply rate falls below 20%.

**Files.** This guide; `dns-records.csv` (the seven DNS records, in order, with checks); `warmup-schedule.csv` (every weekday from Mon 2026-10-26 to Fri 2026-12-11 with its email volumes, built and checked by `tools/build_warmup.py`). Sources are numbered S1 to S16 in `_work/partB/sources.md`, all opened 2026-10-24.

**Researched facts versus judgment.** Google's records, waits and limits below are quoted from Google's pages (sources given). The day-by-day volumes, the caps and the stop rules are my judgment for a one-person, ten-a-day sender. No published standard sets them, and they are labeled that way.

---

## 0. The decisions, on one screen

| Question | Decision |
| --- | --- |
| Which mailbox | One Google Workspace Business Starter seat on [DOMAIN]: [FOUNDER NAME] <[EMAIL]>. A person's name, not hello@ or info@ |
| Cold email from [DOMAIN] in week 1 | **None.** The domain is days old and DKIM is not working until midweek |
| First cold email | **Mon 2026-11-02**, at 3, after SPF, DKIM and DMARC all show PASS on a test email |
| Ramp | New cold first touches: 3 to 5 a day in week 2, 6 to 8 in week 3, 8 to 10 from week 4. All cold email in a day (new plus follow-ups, worst case): at most 20 in weeks 2 and 3, 30 in weeks 4 and 5, 40 after that |
| Ten touches a day in weeks 1 to 3 | Made up with LinkedIn, warm introductions and lobby walk-ins while email ramps (145 first touches by Gate 0 in `warmup-schedule.csv`, five short of the plan's 150 because Monday of week 1 is a setup day) |
| Tool | Plain Gmail with templates and scheduled send. No sequencer before Gate 1. Extra cost: $0 |
| What every cold email looks like | Plain text. No link, no attachment, no image, no tracking pixel, no link shortener in a first touch. The outreach signature (`desk-drop-identity/signature/signature-outreach.txt`) with [WEBSITE] removed until the site is public, and the footer from `desk-drop-legal-pack/02-email-footer-and-checklist.md` |
| Stop rules | Pause all cold email from [DOMAIN] for five business days on two or more bounces in a week (or over 2% once 100 email first touches have gone out), on any spam signal, or if a test email lands in spam (section 3.4) |

---

## 1. Accounts and money

| Item | Cost | Needs your login | Note |
| --- | --- | --- | --- |
| Domain [DOMAIN] | Plan budget: $100 for domain and email for six months (plan, capital table) | Yes: the registrar you choose | Choose it after the name check (`desk-drop-legal-pack/01-name-check-log.md`). Buy one domain. A second "sending" domain is not recommended: at 10 to 30 emails a day it adds cost and a lookalike address that reads like automation |
| Google Workspace Business Starter, one seat | $7 a user a month on a one-year commitment, or $8.40 billed monthly (third-party listing dated 2026-06-22, S8; Google's own pricing page did not show prices from this location: **unverified, founder to confirm at checkout**) | Yes: Google | Google offers a 14-day trial (S8). Trial accounts can send 500 messages a day (S6): far above this plan. **Stop at the checkout page and decide; this is a spend.** Monthly billing keeps the exit open |
| Gmail templates, scheduled send | $0 | No | Built into Gmail (S9, S10) |
| Postmaster Tools | $0 | Yes: Google | Optional. It will likely show no data at this volume (S5) |

Software total from this guide: about $8.40 a month. Keep the whole stack (Clay, forms, e-signature, and the rest) under the plan's $60 a month.

---

## 2. SPF, DKIM and DMARC for Google Workspace on [DOMAIN]

Do these in order. Every step changes DNS at your registrar or settings in the Workspace Admin console, so every step needs your login. The exact records are in `dns-records.csv`.

1. **Mon 2026-10-26. Sign up for Workspace** with [DOMAIN] and verify the domain with the TXT record the setup wizard shows.
2. **Mon 2026-10-26. MX record.** One record: host `@`, value `smtp.google.com`, priority `1`. "Remove any other MX records." It "can take up to 72 hours" to be recognized (S16). Send yourself an email from a personal account to [EMAIL] to check it arrives.
3. **Mon 2026-10-26. SPF.** One TXT record on `@`: `v=spf1 include:_spf.google.com ~all` (S1). If the registrar already put an SPF record there, edit that record rather than adding a second one: two SPF records on one name make SPF fail. Up to 48 hours to work (S1).
4. **Wed 2026-10-28 or Thu 2026-10-29. DKIM.** Google: "after you turn on Gmail for your organization, you must wait 24–72 hours" before you can get the key (S2). Then, signed in as super administrator: Admin console > Apps > Google Workspace > Gmail > **Authenticate email** > Generate new record, key length **2048** (1024 only if the registrar refuses long records), prefix selector **google** (S2). Publish the TXT record at `google._domainkey` with the value Google shows (`v=DKIM1; k=rsa; p=...`). Only then click **Start authentication**. Up to 48 hours to work (S2).
5. **Test.** From [EMAIL], send a short email to a personal Gmail account you own. Open it, More (three dots) > **Show original**. You want `SPF: PASS` and `DKIM: PASS` with `d=[DOMAIN]`.
6. **Fri 2026-10-30, or Mon 2026-11-02 before the first cold send. DMARC.** Google: "Allow 48 hours after setting up SPF and/or DKIM before setting up DMARC" (S3). One TXT record at `_dmarc`: `v=DMARC1; p=none; rua=mailto:[EMAIL]`. Google recommends starting at `p=none` and always including `rua` (S3). Reports come to your own address; a Gmail filter on the subject words "Report domain" labels them and keeps them out of the inbox.
7. **Test again** (step 5). You want `DMARC: PASS` as well. Do not send cold email until all three pass.
8. **After Gate 1 (Fri 2026-12-11).** If two weeks of reports show only Google sending as [DOMAIN] and everything passing, change the DMARC record to `p=quarantine` (Google: raise the policy as you learn, S3; the timing is judgment). If any other tool later sends as [DOMAIN] (a form tool's notification, an invoicing tool), add it to SPF and DKIM first.

Why `p=none` is enough to start: for mail to personal Gmail accounts, Google requires SPF or DKIM from every sender, and DMARC (which "can be set to none") only from senders of 5,000 or more a day (S4). DMARC still matters here because it proves the From address is yours, which receiving servers weigh for a new domain.

---

## 3. Warm-up schedule

### 3.1 The daily volumes

The full table is `warmup-schedule.csv` (35 weekdays). The columns: new cold first touches by email; touch 2 and touch 3 due that day (touch 2 at +3 business days and touch 3 at +7, the timing in `messages/`, assuming nobody replies, which is the worst case); the day's total cold email; the cap; and, in weeks 1 to 3, the first touches to make by other channels so the day still reaches ten.

| Week | Dates (derived, founder to confirm) | New cold first touches by email, per day | Most cold email in one day (worst case) | Cap | Other channels per day |
| --- | --- | --- | --- | --- | --- |
| 1 | Mon 2026-10-26 to Fri 2026-10-30 | 0 | 0 | 0 | 5 on Monday (setup day), then 10 |
| 2 | Mon 2026-11-02 to Fri 2026-11-06 | 3, 4, 5, 5, 5 | 9 | 20 | 7 falling to 5 |
| 3 | Mon 2026-11-09 to Fri 2026-11-13 | 6, 7, 0 (Wed 11-11 is a federal holiday), 8, 8 | 18 | 20 | 4 falling to 2; 10 on the holiday |
| 4 | Mon 2026-11-16 to Fri 2026-11-20 | 8, 8, 9, 9, 10 | 25 | 30 | as needed for selling |
| 5 | Mon 2026-11-23 to Fri 2026-11-27 | 8, 8, 0, 0 (Thanksgiving), 0 (no email that Friday) | 25 | 30 | |
| 6 | Mon 2026-11-30 to Fri 2026-12-04 | 8, 10, 10, 10, 10 | 28 | 40 | |
| 7 | Mon 2026-12-07 to Fri 2026-12-11 | 10 | 30 | 40 | |

Ten new first touches a day is about five offices and five brands. In weeks 1 to 3 that gives 145 first touches by Gate 0 (Fri 2026-11-13), 51 of them by email.

`tools/build_warmup.py` fails if any day goes over its cap, if anything is scheduled on a weekend or a federal holiday, or if cold email starts before Mon 2026-11-02. On Fri 2026-11-27 (a business day under CONTRACTS, but the day after Thanksgiving) nothing is sent and the follow-ups due roll to Monday; that is the only day this calendar departs from the business-day count the copy uses.

### 3.2 The risk you are taking in week 2

On Mon 2026-11-02 [DOMAIN] is one week old. A young domain sending cold email is a known risk: receiving filters have no history to judge it by. What keeps the risk small here is everything else about the mail: three to five a day, each written to one person at a verified business address, plain text, no links or attachments, a real person's name, and replies coming back. If the first two weeks of email are not working (section 3.4), the plan still holds: the day's ten touches move back to LinkedIn, warm introductions and walk-ins, which carry all of week 1 on their own. Starting email a week later (Mon 2026-11-09) is the safer choice if your warm list and the walk-ins are filling the days anyway; the only cost is that fewer of the 150 discovery touches go by email.

### 3.3 What makes the warm-up work

Google's only published guidance is "Start with a low sending volume to engaged users, and slowly increase the volume over time" and "Avoid introducing sudden volume spikes" (S4). For a person sending one to one, that means:

- **Early mail gets replies.** In week 1, the new address writes only to people who know you or who just replied (warm introductions, accepted LinkedIn invitations who asked for email). Real back-and-forth is the best signal a new domain can send.
- **Every cold email is written to one person** from the day's list, with the fields in `messages/03-personalization-fields.csv`. No list blasts, no BCC.
- **Plain text, no link, no attachment, no image, no pixel in a first touch.** The one-pager goes as an attachment only after they reply (`messages/04-progress-slots.md`, `[ONE-PAGER]`).
- **Verified addresses only.** Email only rows with `email_status = verified` (Clay). Everything else goes to LinkedIn or a walk-in. A bounce costs more on a new domain than one lost message.
- **No warm-up services.** Paid tools that trade automated emails between inboxes to fake engagement are not used: they cost money, and they teach the filters a pattern that is not yours.
- **Spread the day.** Write the ten in one sitting, then use scheduled send (Gmail allows up to 100 scheduled emails, S10) to release them a few minutes apart between 8 and 11 am on the recipient's weekday. The timing is judgment, not a measured best.

### 3.4 Hold or advance (judgment rules)

Check these every Friday on the tracker's Scorecard ("Email bounces to date" and the reply rates) and in Gmail.

| Signal | Do |
| --- | --- |
| Two or more bounces in one week, or more than 2% of email first touches once 100 have gone out | Stop cold email from [DOMAIN] for five business days. Re-check the list: unverified addresses, typos, people who left. Restart at the previous week's volume. (A percentage alone is too jumpy at 20 emails a week: one bounce in week 2 is 4.5%) |
| Anyone marks a message as spam (you will rarely know; a reply saying "spam" counts) | Same: five business days off, read the message again for anything that looks like a blast |
| A test email to your own Gmail or Outlook.com account lands in spam | Same, and re-run section 2 step 5 for PASS on all three |
| Week's reply rate on email under 10% after 30 first touches | Assume delivery first (section 6.2), not copy |
| Clean week (no bounces over 2%, no spam signal) | Advance to the next week's row |

---

## 4. Week one without the new domain

The domain is bought on Monday, DKIM cannot be generated until Wednesday at the earliest, and DMARC waits 48 hours after that (S2, S3). So week 1 runs on channels that do not depend on [DOMAIN]. Totals match `warmup-schedule.csv`: 5 first touches on Monday, then 10 a day.

| Day | Offices | Brands | Setup |
| --- | --- | --- | --- |
| **Mon 2026-10-26** | 3 warm asks to people you know by name (office managers, workplace leads, executive assistants), from your existing email, phone or LinkedIn (`messages/08-warm-intro-referral-walk-in.md` 1a or 1c) | 2 warm asks to founders you know | Name check (`desk-drop-legal-pack/01`); domain; Workspace; MX; SPF; tracker into Google Sheets; join the Startup CPG Slack and list its New York events for the next six weeks (plan, week 1 setup) |
| **Tue 2026-10-27** | Walk sessions 1 and 2 from `cluster-1-flatiron/walk.csv`, 8 to 11 am: ask for the person who runs the pantry at the candidate offices on the route (08 part 3). About 6 asks. Fill the walk's grey columns as you go | 2 LinkedIn messages to people already connected to you; send LinkedIn invitations **without a note** to the next week's LinkedIn contacts (both sides), no more than about 20 a day | Update the LinkedIn headline (`messages/01-founder-linkedin-profile.md`, version 1 until the name is decided) |
| **Wed 2026-10-28** | Walk sessions 3 and 4, 8 to 11 am. About 6 asks | 2 LinkedIn messages; 2 warm or Startup CPG contacts (research conversations only, never a pitch inside the community) | DKIM key (section 2 step 4) |
| **Thu 2026-10-29** | 3 LinkedIn messages to accepted invitations (07 follow-up) | 3 LinkedIn messages; 2 warm or community; 2 messages to brands' own business accounts on Instagram, where the brand lists that as its contact route (optional; Instagram's limits were not checked) | Test email: SPF and DKIM PASS |
| **Fri 2026-10-30** | 3 LinkedIn messages; 2 warm follow-ups | 3 LinkedIn messages; 2 warm or community | DMARC if DKIM has passed for 48 hours; first Friday scorecard (`tracking/how-the-tracker-works.md`) |

Rules for week one:
- **LinkedIn notes are rationed.** On a free account LinkedIn allows "a personalized message to up to three connection requests per month", each "up to 200 characters" (S14). Use the three on the three best contacts who have no email and no walk-in route. Every other invitation goes without a note; the message with the ask (`messages/07-linkedin-messages.md`) goes once they accept, and that is touch 1. An invitation alone is not a touch: in Clay set `next_action = await_connection`. LinkedIn Premium lifts the note limit but is a paid plan whose price was not checked; it is not recommended inside the budget, and if you consider it, stop at checkout.
- **Warm messages from your existing address carry the footer too** (`messages/08`, "Which address sends these"). Once [DOMAIN] passes all three checks, start new threads from [EMAIL]; leave old threads where they are.
- **Walk-ins only on Tuesday or Wednesday mornings**, when pantry owners are in and the lobby looks as it will on a drop day (B's walk notes). Bring nothing to sell (plan). If the walk sessions run short, log what you saw on the walk sheet anyway; it feeds the building columns.
- **If the warm list is short,** move its share to walk-ins (offices) and to Startup CPG events and LinkedIn (brands). Do not fill the gap with cold email from [DOMAIN] in week 1, and do not use a personal or another business's domain for cold email.
- **Log every touch the same day** in Clay: `touch_1_date`, `channel`, `sequence`, `status = contacted`.

---

## 5. Plain Gmail or a sequencer

**Recommendation: plain Gmail until at least Gate 1 (Fri 2026-12-11).** Extra cost $0.

How it runs: the day's ten from the Clay daily view; Gmail templates for each sequence step (Settings > See all settings > Advanced > Templates > Enable, then Compose > More options > Templates, S9), personalized by hand; scheduled send to space them out (S10); follow-ups from Clay's `next_action_date` view each morning. At 10 new and up to 30 total a day, that is the plan's "ten honest, personalized messages in under an hour".

Why not a sequencer yet:
- Volume is far too low to need one, and every message is edited for one person.
- A follow-up must stop the moment someone replies on any channel (a LinkedIn reply, a hallway yes). By hand, you see that. A sequencer only sees its own inbox.
- Mail-merge tools sell open tracking (Mailmeteor and YAMM list it on every plan, S11, S12), which works by loading a hidden image. On a new domain that is one more thing that looks like bulk mail, and an open is not a reply anyway.
- It adds a third-party app with access to your mailbox.

| Option | Cost a month | Daily limit | Automatic follow-ups | Verdict |
| --- | --- | --- | --- | --- |
| **Plain Gmail (Workspace Business Starter)** | $7 annual / $8.40 monthly (S8, unverified, founder to confirm) | 2,000 a day (S6) | No; by hand from Clay | **Use this** |
| Gmail built-in mail merge | Needs Business Standard: $14 annual / $16.80 monthly (S7, S8) | 1,500 a day (S7) | No | Not needed; it also adds its own unsubscribe link to every message (S7) |
| Mailmeteor Free | $0 | 50 a day, 500 a month (S11) | No | Fine for a one-off merge; no follow-ups |
| Mailmeteor Premium | $17.99 per user (S11) | 1,000 a day | Up to 5 | First choice **if** you ever switch (below) |
| YAMM (Yet Another Mail Merge) | Free tier: 20 recipients a day; paid price not shown (S12) | 1,500 a day on Workspace | Follow-up campaigns | Price unknown |
| GMass Premium | $39.95 billed monthly, or $349 a year (S13) | Not stated | Yes | Takes most of the $60 software budget |

**When to reconsider:** from week 4, if sending and follow-ups take more than 60 minutes a day for a week, or more than two follow-ups a week are sent late. Then try Mailmeteor Premium at $17.99 a month (S11): **stop at the payment page and decide in writing**, switch tracking off if the tool allows it (not checked), and keep the volumes in `warmup-schedule.csv`.

---

## 6. If the reply rate is under 20%

The plan's arithmetic: 150 messages at 20% is 30 conversations (Phase 0, cadence). The tracker's Scorecard shows the reply rate per side every Friday, counts any human reply (opt-outs included, bounces and auto-replies excluded), and prints **"UNDER 20%"** once a side has at least 30 first touches. It also shows conversations per first touch, which is what Gate 0 actually needs.

Change one thing at a time, in this order, and give each change a week or 30 first touches before judging it.

### 6.1 Check the measure (5 minutes)
- Are touches logged? A reply that came on LinkedIn but was never written to Clay looks like silence.
- Are follow-ups going out? Touches 2 and 3 are part of the sequence the rate assumes; if they are not being sent on time, fix that before judging the copy.
- Is the sample big enough? Under 30 first touches on a side, one reply moves the rate by more than three points.

### 6.2 Check delivery (30 minutes)
- Send the current touch 1 to a personal Gmail and a personal Outlook.com account you own. Inbox or spam? In Gmail, Show original: SPF, DKIM and DMARC all PASS?
- Bounces above 2%? Then the list, not the copy, is the problem.
- Optionally run one message through mail-tester.com (S15; its free allowance was not confirmed).
- If anything fails: stop cold email from [DOMAIN] for five business days, fix it, and put that side's touches on LinkedIn and walk-ins meanwhile.

### 6.3 Check who you are writing to
- Look at the replies you did get: which titles, company sizes, channels and `known_to_founder` values? Move the next week's list toward them (in Clay, A's scoring).
- Offices: is the person really the pantry owner? At 40 to 150 people that is usually the office manager or an executive assistant; a "head of workplace" at a larger firm often is not. Brands: founders at the smaller end of $500k to $10M answer more of their own email than marketing leads at the top end (judgment; check against your own replies).
- Is the why-now line true and recent (under 120 days, `messages/03`)? A stale hook reads like a template.

### 6.4 Change the copy, one variable at a time
- Swap the subject line first (Part A's variants A and B). Compare variants only after about 40 first touches each, and switch only if one has at least twice the replies of the other and at least four more in absolute terms. Smaller gaps at this volume are noise. The Scorecard's "By sequence variant" table counts this for you.
- Then shorten: under 90 words, one ask, the specific line (their street, their store) in the first two sentences.
- Then make the ask smaller: "Who runs the pantry there?" for offices; "Would a 15-minute call next week be useful?" for brands.
- Never add urgency, a link, an attachment or a claim the tracker does not support (`messages/04-progress-slots.md`).

### 6.5 Change the mix
- Offices: move up to half of the daily ten to lobby walk-ins (Tuesday and Wednesday mornings) and referrals from the offices already talked to.
- Brands: Startup CPG events and the shelf approach ("you are already on the shelf three blocks from these offices", plan Phase 2, only where the grade is `seen_on_shelf`) usually beat cold email for founders (judgment).

### 6.6 What not to do
- Do not raise email volume to make up for a low rate. That is how new domains get burned.
- Do not buy a list, a warm-up service, or a second domain.
- Do not chase with more than three touches.

### 6.7 When it is not the email
If the reply rate is fine but conversations are not turning into yeses, the problem is the offer or the target, and the plan's Gate 0 responses apply: fewer than 5 offices interested, change the cluster or the office size band, not the model; fewer than 3 brands would pay, test the office-paid version for three more weeks (plan, "If a gate fails").

---

## 7. Opt-outs and the law, in three lines

The legal pack's footer and checklist (`desk-drop-legal-pack/02-email-footer-and-checklist.md`) govern: every outreach email carries [POSTAL ADDRESS] and the reply-to-opt-out line; nothing in the header or subject misleads; every opt-out, in any words, on any channel, is written to Clay the same day (`do_not_contact = Y`, `status = do_not_contact`, `opt_out_date`) and never reversed. The tracker never exports these as pipeline `opt_out` events; those are reserved for signed offices or paid brands leaving the roster (`handoff/how-to-fill-handoff-files.md`).

## Changelog

- Round 1 (2026-10-24): DNS steps from Google's pages (S1 to S3, S16); warm-up schedule generated and checked by script; week-one plan built on B's walk sessions, warm asks and LinkedIn; tool comparison from vendors' pricing pages (S11 to S13); under-20% playbook.
- Round 2 (2026-10-24): unsourced lines reworded as judgment or removed (follow-up reply share, "pixel by default"); the Gmail rule narrowed to what Google's page says (mail to personal Gmail accounts); the day after Thanksgiving made a no-send day after the schedule showed 18 follow-ups landing on it; caps re-checked by script.
- Round 3 (2026-10-24): critique as a deliverability specialist who has watched new domains get burned: the one-week-old-domain risk is now stated with the safer alternative (start email on Mon 2026-11-09); the 2% bounce rule tripped on a single bounce at week-2 volumes, so it is now "two bounces in a week, or 2% after 100"; the Scorecard text matches.
