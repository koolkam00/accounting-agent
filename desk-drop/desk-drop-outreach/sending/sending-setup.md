# Sending setup

Version 1.4 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/sending/`

**What it is for.** Getting outreach email from a brand-new domain into inboxes without burning the domain, and keeping the first three weeks on schedule while the domain is too new for cold email. It covers: which domain to buy and when; SPF, DKIM and DMARC for Google Workspace on [DOMAIN]; a warm-up schedule with daily volumes; two weeks that do not depend on cold email; plain Gmail versus a sequencer, with costs; and what to change if the reply rate falls below 20%.

**Files.** This guide; `dns-records.csv` (the seven DNS records, in order, with checks); `warmup-schedule.csv` (every weekday from Mon 2026-10-26 to Fri 2026-12-11 with its email volumes, built and checked by `tools/build_warmup.py`). Sources are numbered S1 to S20 in `_work/partB/sources.md`, all opened 2026-10-24.

**Researched facts versus judgment.** Google's records, waits and limits below are quoted from Google's pages (sources given), and the 32-day "newly registered" window from Palo Alto Networks' documentation (S17). The day-by-day volumes, the caps, the four conditions for the first cold email and the stop rules are my judgment for a one-person, ten-a-day sender. No published standard sets them, and they are labeled that way.

---

## 0. The decisions, on one screen

| Question | Decision |
| --- | --- |
| Which domain | **One domain you will keep whatever name you choose, bought Mon 2026-10-26.** The working name is on hold (`desk-drop-legal-pack/01-name-check-log.md`: another business trades as "DeskDrop", and the USPTO called the words descriptive), and the name is chosen by Wed 2026-11-18. A domain bought for "Desk Drop" and dropped on 11-18 would restart the warm-up in the middle of selling and strand every thread. **Recommended default:** a name-neutral domain (for example one built from your own name; never "deskdrop" or a lookalike of another business). It stays your mail domain after the name is decided; the website can have its own address once the name is cleared ([WEBSITE], workstream C). Alternative: if by Tue 2026-10-27 you have run the legal pack's check on a fallback name and will keep it, buy that name's domain instead |
| What the signature says before the name is decided | "[FOUNDER NAME]", then "Setting up an office sampling service in {CLUSTER_SHORT}" in place of "Founder, {BRAND_NAME}", until `name_decided = Y` (`messages/02-commercial-footer.md`). The footer line stays exactly as the legal pack wrote it |
| Which mailbox | One Google Workspace Business Starter seat on [DOMAIN]: [FOUNDER NAME] <[EMAIL]>. A person's name, not hello@ or info@ |
| Cold email from [DOMAIN] in weeks 1 and 2 | **None.** The domain is days old, DKIM works from about Thursday of week 1, and the address first needs a history of real mail |
| Warm email from [DOMAIN] | **From Thu 2026-10-29**, once a test email shows SPF and DKIM PASS: every warm ask, every walk-in follow-up, every reply to a LinkedIn contact who asks for email, and every post-call email goes from [EMAIL]. Aim for 3 to 5 genuine two-way emails a day (`warmup-schedule.csv`, `warm_email_from_domain_target`). Mon to Wed of week 1, warm asks go from your existing address |
| First cold email | **Mon 2026-11-09 at the earliest**, at 3 a day, and only if all four hold on Fri 2026-11-06: (1) a test email shows SPF, DKIM and DMARC PASS; (2) DMARC was published at least 3 business days earlier (by Wed 2026-11-04); (3) test emails from [EMAIL] to your own Gmail and Outlook.com accounts land in the inbox; (4) at least 10 two-way threads from [EMAIL] (you wrote, they replied: `warm_threads_from_domain` in `messages/04-slot-state.csv`). If any fails, start **Mon 2026-11-16** instead (`python3 tools/build_warmup.py --first-cold 2026-11-16`), and if one still fails then, wait a week at a time. `domain_ready` stays N until then |
| Ramp | New cold first touches: 3 to 5 a day in the first week of cold email, 6 to 8 in the second, 8 to 10 in the third, 10 after that. All cold email in a day (new plus follow-ups, worst case): at most 20 in the first two weeks, 30 in the next two, 40 after that |
| Ten touches a day in weeks 1 to 3 | Made up with LinkedIn, warm introductions, lobby walk-ins and Startup CPG contacts. 145 first touches by Gate 0 in `warmup-schedule.csv` (five short of the plan's 150 because Monday of week 1 is a setup day), 17 of them by cold email on the default start, none on the late start |
| Tool | Plain Gmail with templates and scheduled send. No sequencer before Gate 1. Extra cost: $0 |
| What every cold email looks like | Plain text. No link, no attachment, no image, no tracking pixel, no link shortener in a first touch. The outreach signature (`messages/02`) with [WEBSITE] removed until the site is public, and the footer from `desk-drop-legal-pack/02-email-footer-and-checklist.md` |
| Stop rules | Pause all cold email from [DOMAIN] for five business days on two or more bounces in a week (or over 2% once 100 email first touches have gone out), on any spam signal, or if a test email lands in spam (section 3.4). Pause office cold email until Mon 2026-11-30 on a bounce from an office that names policy, reputation or a block (section 3.2) |

---

## 1. Accounts and money

| Item | Cost | Needs your login | Note |
| --- | --- | --- | --- |
| Domain [DOMAIN] | Price **not checked** (it depends on the registrar and the ending); plan budget: $100 for domain and email for six months (plan, capital table). **Stop at the checkout page and decide; this is a spend** | Yes: the registrar you choose | Name-neutral, bought Mon 2026-10-26 (section 0). Keep its DNS at the registrar, not on Cloudflare's free name servers (section 3.2, S18). Every day earlier it is bought is a day older at the first cold email. Buy one domain. A second "sending" domain is not recommended: at 10 to 30 emails a day it adds cost and a lookalike address that reads like automation |
| Google Workspace Business Starter, one seat | $7 a user a month on a one-year commitment, or $8.40 billed monthly (third-party listing dated 2026-06-22, S8; Google's own pricing page did not show prices from this location: **unverified, founder to confirm at checkout**) | Yes: Google | Google's own pricing page offers a 14-day trial (noted under S8). Trial accounts can send 500 messages a day (S6): far above this plan. **Stop at the checkout page and decide; this is a spend.** Monthly billing keeps the exit open |
| Mailing address for [POSTAL ADDRESS] | Price **not checked** (legal pack `figures.csv`, `mailing_address_mailbox_annual`: "needs quote"; the financial model times it in week 1). **Stop at the payment step and decide; this is a spend** | Yes: USPS or the mailbox agency, in person with ID | Every email carries [POSTAL ADDRESS] (`messages/02`). A USPS post office box (PS Form 1093, online or at a Post Office, two current IDs) or a private mailbox at a commercial mail receiving agency (PS Form 1583 and two IDs): USPS mailing standards, DMM 508.4.2.1 and 508.1.8 (S20). Default: rent one on Mon 2026-10-26 (README, decision 5). Until it exists, no email goes: day-one warm asks go by phone or LinkedIn. A home address works only if you accept it being printed on every cold email (legal pack 02) |
| Gmail templates, scheduled send | $0 | No | Built into Gmail (S9, S10) |
| Postmaster Tools | $0 | Yes: Google | Optional. It will likely show no data at this volume (S5) |

Software total from this guide: about $8.40 a month, plus the domain (a yearly fee, price not checked) and the mailbox (price not checked; not software, so outside the $60 software ceiling, but a spend all the same). Keep the whole stack (Clay, forms, e-signature, and the rest) under the plan's $60 a month.

---

## 2. SPF, DKIM and DMARC for Google Workspace on [DOMAIN]

Do these in order. Every step changes DNS at your registrar or settings in the Workspace Admin console, so every step needs your login. The exact records are in `dns-records.csv`.

1. **Mon 2026-10-26. Sign up for Workspace** with [DOMAIN] and verify the domain with the TXT record the setup wizard shows.
2. **Mon 2026-10-26. MX record.** One record: host `@`, value `smtp.google.com`, priority `1`. "Remove any other MX records." It "can take up to 72 hours" to be recognized (S16). Send yourself an email from a personal account to [EMAIL] to check it arrives.
3. **Mon 2026-10-26. SPF.** One TXT record on `@`: `v=spf1 include:_spf.google.com ~all` (S1). If the registrar already put an SPF record there, edit that record rather than adding a second one: two SPF records on one name make SPF fail. Up to 48 hours to work (S1).
4. **Wed 2026-10-28 or Thu 2026-10-29. DKIM.** Google: "after you turn on Gmail for your organization, you must wait 24–72 hours" before you can get the key (S2). Then, signed in as super administrator: Admin console > Apps > Google Workspace > Gmail > **Authenticate email** > Generate new record, key length **2048** (1024 only if the registrar refuses long records), prefix selector **google** (S2). Publish the TXT record at `google._domainkey` with the value Google shows (`v=DKIM1; k=rsa; p=...`). Only then click **Start authentication**. Up to 48 hours to work (S2).
5. **Test.** From [EMAIL], send a short email to a personal Gmail account you own. Open it, More (three dots) > **Show original**. You want `SPF: PASS` and `DKIM: PASS` with `d=[DOMAIN]`. From the day this passes (planned Thu 2026-10-29), every new warm email thread goes from [EMAIL] (section 4).
6. **Fri 2026-10-30, and no later than Wed 2026-11-04. DMARC.** Google: "Allow 48 hours after setting up SPF and/or DKIM before setting up DMARC" (S3). One TXT record at `_dmarc`: `v=DMARC1; p=none; rua=mailto:[EMAIL]`. Google recommends starting at `p=none` and always including `rua` (S3). Reports come to your own address; a Gmail filter on the subject words "Report domain" labels them and keeps them out of the inbox. Wed 2026-11-04 is three business days before the earliest first cold email (condition 2).
7. **Test again** (step 5). You want `DMARC: PASS` as well. Then, on Thu 2026-11-05, send one email from [EMAIL] to a personal Outlook.com account and one to a personal Gmail account you own: both must land in the inbox, not spam (condition 3).
8. **After Gate 1 (Fri 2026-12-11).** If two weeks of reports show only Google sending as [DOMAIN] and everything passing, change the DMARC record to `p=quarantine` (Google: raise the policy as you learn, S3; the timing is judgment). If any other tool later sends as [DOMAIN] (a form tool's notification, an invoicing tool), add it to SPF and DKIM first.

Why `p=none` is enough to start: for mail to personal Gmail accounts, Google requires SPF or DKIM from every sender, and DMARC (which "can be set to none") only from senders of 5,000 or more a day (S4). DMARC still matters here because it proves the From address is yours, which receiving servers weigh for a new domain.

---

## 3. Warm-up schedule

### 3.1 The daily volumes

The full table is `warmup-schedule.csv` (35 weekdays). The columns: the domain's age in days (bought Mon 2026-10-26); new cold first touches by email; touch 2 and touch 3 due that day (touch 2 at +3 business days and touch 3 at +7, the timing in `messages/`, assuming nobody replies, which is the worst case); the day's total cold email; the cap; the warm emails from [DOMAIN] to aim for (part of the day's ten or a reply, never on top of the cap); and, in weeks 1 to 3, the first touches to make by other channels so the day still reaches ten.

Default start, first cold email Mon 2026-11-09 (all dates derived, founder to confirm):

| Week | Dates | New cold first touches by email, per day | Most cold email in one day (worst case) | Cap | Warm email from [DOMAIN] per day | Other channels per day |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Mon 2026-10-26 to Fri 2026-10-30 | 0 | 0 | 0 | 0 to Wednesday (existing address), 3 from Thursday | 5 on Monday (setup day), then 10 |
| 2 | Mon 2026-11-02 to Fri 2026-11-06 | 0 | 0 | 0 | 5 | 10 |
| 3 | Mon 2026-11-09 to Fri 2026-11-13 | 3, 4, 0 (Wed 11-11 is a federal holiday), 5, 5 | 8 | 20 | 3 | 7, 6, 10 on the holiday, 5, 5 |
| 4 | Mon 2026-11-16 to Fri 2026-11-20 | 6, 7, 8, 8, 8 | 19 | 20 | 3 | as needed for selling |
| 5 | Mon 2026-11-23 to Fri 2026-11-27 | 8, 8, 0, 0 (Thanksgiving), 0 (no email that Friday) | 21 | 30 | 3 | |
| 6 | Mon 2026-11-30 to Fri 2026-12-04 | 10 | 28 | 30 | 3 | |
| 7 | Mon 2026-12-07 to Fri 2026-12-11 | 10 | 30 | 40 | 3 | |

Late start (first cold email Mon 2026-11-16, if a condition fails on Fri 2026-11-06): week 3 has no cold email and 5 warm emails a day; week 4 runs 3, 4, 5, 5, 5 (worst case 9, cap 20); week 5 runs 6, 7 and then Thanksgiving (worst case 12, cap 20); week 6 runs 8, 8, 9, 9, 10 (worst case 24, cap 30); week 7 runs 10 a day (worst case 29, cap 30). Rebuild the CSV with `python3 tools/build_warmup.py --first-cold 2026-11-16`.

Ten new first touches a day is about five offices and five brands. In weeks 1 to 3 that gives 145 first touches by Gate 0 (Fri 2026-11-13): 17 by cold email on the default start, none on the late start. The rest come from LinkedIn, warm asks, walk-ins and Startup CPG contacts.

`tools/build_warmup.py` fails if any day goes over its cap, if anything is scheduled on a weekend, a federal holiday or a no-send day, if cold email is scheduled before the first cold day, if the first cold day is before Mon 2026-11-09 or not a Monday, or if warm mail from [DOMAIN] is scheduled before Thu 2026-10-29. It checks both the default and the late start every time it runs. On Fri 2026-11-27 (a business day under CONTRACTS, but the day after Thanksgiving) nothing is sent and the follow-ups due roll to Monday; that is the only day this calendar departs from the business-day count the copy uses.

### 3.2 Why cold email waits for week 3, and the risk that remains

A domain bought on Mon 2026-10-26 is 14 days old on Mon 2026-11-09. Receiving filters have no history to judge it by, and a domain whose first mail is cold mail teaches them the wrong pattern. So weeks 1 and 2 give [DOMAIN] a history of real mail, warm asks and replies that get answered (section 3.3), and cold email starts only once that history exists (the four conditions in section 0). The day's ten touches do not wait for it: they run on LinkedIn, warm introductions, walk-ins and Startup CPG contacts (section 4).

What remains is the domain's age. Some corporate security products treat any domain under about a month old as risky: Palo Alto Networks' firewall documentation defines its "Newly-Registered Domains" category as sites "registered within the last 32 days" and gives "Recommended Policy Action: Block" (S17, opened 2026-10-24). That category filters links and web pages, not mail. Email gateways can score domain age too: one email-security product's published rule, "Spam: Cold outreach from Cloudflare-hosted newly registered domain", flags inbound mail whose sender domain was registered fewer than 365 days ago, uses exactly two Cloudflare name servers, and reads as B2B cold outreach (Sublime Security, via detection.fyi, page dated 2026-08-17, S18, opened 2026-10-24). Whether any office in the cluster uses that product is **unknown**; it shows the kind of signal a new domain carries for a full year, not just a month. For [DOMAIN] bought on Mon 2026-10-26, the 32 days end on Fri 2026-11-27. What follows (judgment):
- **Buy [DOMAIN] at a registrar and use that registrar's own DNS, not Cloudflare's free name servers.** It costs nothing extra, and it keeps the domain out of the one rule above that this sender would otherwise match on every cold email for its first year.
- **No link to [DOMAIN] in any email before Mon 2026-11-30.** First touches never carry a link anyway. A website, form or survey on [DOMAIN] may be blocked on an office's network before then; until it is public, outreach uses the one-pager PDFs and no link.
- **Watch office bounces.** A bounce from an office that names policy, reputation, a block or "not accepted" stops office cold email until Mon 2026-11-30; brands carry on. Offices go back to walk-ins and LinkedIn meanwhile.
- **If the first cold emails are not working** (section 3.4), the plan still holds: the day's ten stay on LinkedIn, warm introductions and walk-ins, which carry weeks 1 and 2 on their own.

### 3.3 What makes the warm-up work

Google's only published guidance is "Start with a low sending volume to engaged users, and slowly increase the volume over time" and "Avoid introducing sudden volume spikes" (S4). For a person sending one to one, that means:

- **Early mail gets replies.** From Thu 2026-10-29, the new address writes only to people who know you or who asked to hear from you: warm asks and introductions, walk-in follow-ups, LinkedIn contacts who asked for email, and post-call emails, 3 to 5 a day. Real back-and-forth is the best signal a new domain can send. Count the threads where the other person wrote back and keep `warm_threads_from_domain` in `messages/04-slot-state.csv` up to date: it is condition 4.
- **Every cold email is written to one person** from the day's list, with the fields in `messages/03-personalization-fields.csv`. No list blasts, no BCC.
- **Plain text, no link, no attachment, no image, no pixel in a first touch.** The one-pager goes as an attachment only after they reply (`messages/04-progress-slots.md`, `[ONE-PAGER]`).
- **Verified addresses only.** Email only rows with `email_status = verified` (Clay). Everything else goes to LinkedIn or a walk-in. A bounce costs more on a new domain than one lost message.
- **No warm-up services.** Paid tools that trade automated emails between inboxes to fake engagement are not used: they cost money, and they teach the filters a pattern that is not yours.
- **Spread the day.** Write the ten in one sitting, then use scheduled send (Gmail allows up to 100 scheduled emails, S10) to release them a few minutes apart between 8 and 11 am on the recipient's weekday. The timing is judgment, not a measured best. The draft maker (`messages/_render/fill.py drafts`) writes no more cold first touches for a day than this schedule allows: offices get half the day's number rounded up and brands the rest, so the two runs together never pass it (review round 2).

### 3.4 Hold or advance (judgment rules)

Check these every Friday on the tracker's Scorecard ("Email bounces to date" and the reply rates) and in Gmail.

| Signal | Do |
| --- | --- |
| Two or more bounces in one week, or more than 2% of email first touches once 100 have gone out | Stop cold email from [DOMAIN] for five business days (`domain_ready = N`). Re-check the list: unverified addresses, typos, people who left. Restart at the previous week's volume. (A percentage alone is too jumpy at 20 emails a week: one bounce in a week of 22 is 4.5%) |
| A bounce from an office that names policy, reputation, a block or "not accepted" | Stop office cold email until Mon 2026-11-30 (section 3.2); brands carry on |
| Anyone marks a message as spam (you will rarely know; a reply saying "spam" counts) | Same as the first row: five business days off, read the message again for anything that looks like a blast |
| A test email to your own Gmail or Outlook.com account lands in spam | Same, and re-run section 2 step 5 for PASS on all three |
| Week's conversation-reply rate on email under 10% after 30 first touches | Assume delivery first (section 6.2), not copy |
| Clean week (fewer than two bounces, no spam signal, test emails in the inbox) | Advance to the next week's row |

---

## 4. Weeks 1 and 2 without cold email

The domain is bought on Monday, the DKIM key can only be generated 24 to 72 hours after Gmail is turned on (Tuesday to Thursday), DMARC waits 48 hours after SPF and DKIM pass (S2, S3), and cold email waits for a history of real mail (section 3.2). So weeks 1 and 2 run on channels that do not depend on cold email. Totals match `warmup-schedule.csv`: 5 first touches on Monday of week 1, then 10 a day.

**Which address.** Mon to Wed of week 1: your existing address, phone or LinkedIn, because the new address is not authenticated yet. **From Thu 2026-10-29, once a test email shows SPF and DKIM PASS: every new email thread goes from [EMAIL] on [DOMAIN]**: warm asks, introductions, walk-in follow-ups, LinkedIn contacts who ask for email, post-call emails. That is the warm-up. Leave threads already started where they are. Every email, from either address, carries the footer (`messages/02`), so **no email goes until [POSTAL ADDRESS] is real** (section 1, the mailing address row): until the mailbox exists, Monday's warm asks go by phone or LinkedIn.

### Week 1

| Day | Offices | Brands | Setup |
| --- | --- | --- | --- |
| **Mon 2026-10-26** | 3 warm asks to people you know by name (office managers, workplace leads, executive assistants), by phone or LinkedIn, or from your existing email once [POSTAL ADDRESS] is real (`messages/08-warm-intro-referral-walk-in.md` 1a or 1c) | 2 warm asks to founders you know | Mailing address for [POSTAL ADDRESS] (section 1; a spend); domain (name-neutral, section 0); Workspace; MX; SPF; tracker into Google Sheets; join the Startup CPG Slack and list its New York events for the next six weeks (plan, week 1 setup) |
| **Tue 2026-10-27** | Walk sessions 1 and 2 from `cluster-1-flatiron/walk.csv`, 8 to 11 am: ask for the person who runs the pantry at the candidate offices on the route (08 part 3). About 6 asks. Fill the walk's grey columns as you go | 2 LinkedIn messages to people already connected to you; 2 warm or Startup CPG contacts; send LinkedIn invitations **without a note** to the next week's LinkedIn contacts (both sides), no more than about 20 a day | Update the LinkedIn headline (`messages/01-founder-linkedin-profile.md`, version 1 until the name is decided). If you choose a fallback name instead of a neutral domain, run the legal pack's check on it today |
| **Wed 2026-10-28** | Walk sessions 3 and 4, 8 to 11 am. About 6 asks | 2 LinkedIn messages; 2 warm or Startup CPG contacts (research conversations only, never a pitch inside the community) | DKIM key (section 2 step 4) |
| **Thu 2026-10-29** | 3 LinkedIn messages to accepted invitations (07 follow-up); walk-in follow-ups from [EMAIL] | 3 LinkedIn messages; 2 warm asks from [EMAIL]; 2 messages to brands' own business accounts on Instagram, where the brand lists that as its contact route (optional; Instagram's limits were not checked) | Test email: SPF and DKIM PASS. From now, new email threads from [EMAIL] |
| **Fri 2026-10-30** | 3 LinkedIn messages; 2 warm follow-ups from [EMAIL] | 3 LinkedIn messages; 2 warm or community | DMARC if DKIM has passed for 48 hours; first Friday scorecard (`tracking/how-the-tracker-works.md`); count two-way threads |

### Week 2

| Day | Offices | Brands | Setup |
| --- | --- | --- | --- |
| **Mon 2026-11-02** | 3 LinkedIn messages to accepted invitations; 2 warm asks or referrals from [EMAIL] | 3 LinkedIn messages; 2 warm asks from [EMAIL] or Startup CPG contacts | DMARC, if not done Friday; keep sending invitations without a note for week 3's LinkedIn rows |
| **Tue 2026-11-03** | Walk sessions 5 and 6, 8 to 11 am. About 6 asks; the follow-up note goes from [EMAIL] the same day | 2 LinkedIn messages; 2 warm or community | |
| **Wed 2026-11-04** | Walk sessions 7 and 8, 8 to 11 am. About 6 asks | 2 LinkedIn messages; 2 warm or community | DMARC published by today (condition 2) |
| **Thu 2026-11-05** | 3 LinkedIn messages; 2 referral emails from [EMAIL] (08, 2b) | 3 LinkedIn messages; 2 warm asks from [EMAIL] | Inbox test at Gmail and Outlook.com (condition 3) |
| **Fri 2026-11-06** | 3 LinkedIn messages; 2 warm follow-ups from [EMAIL] | 3 LinkedIn messages; 2 warm or community | **Decision:** all four conditions (section 0)? Yes: set `domain_ready = Y` on Mon 2026-11-09 and send the first 3. No: rebuild for Mon 2026-11-16. Friday scorecard |

Rules for weeks 1 and 2:
- **LinkedIn notes are rationed.** On a free account LinkedIn allows "a personalized message to up to three connection requests per month", each "up to 200 characters" (S14). Use the three on the three best contacts who have no email and no walk-in route. Every other invitation goes without a note; the message with the ask (`messages/07-linkedin-messages.md`) goes once they accept, and that is touch 1. An invitation alone is not a touch: in Clay set `next_action = await_connection`. LinkedIn Premium lifts the note limit but is a paid plan whose price was not checked; it is not recommended inside the budget, and if you consider it, stop at checkout.
- **Walk-ins only on Tuesday or Wednesday mornings**, when pantry owners are in and the lobby looks as it will on a drop day (B's walk notes). Bring nothing to sell (plan). B's `walk.csv` has 11 sessions; weeks 1 and 2 use sessions 1 to 8. If the walk sessions run short, log what you saw on the walk sheet anyway; it feeds the building columns.
- **If invitations are not accepted by Thursday,** make the LinkedIn share up with warm asks and Startup CPG contacts that day; walk-ins stay on Tuesday and Wednesday mornings.
- **If the warm list is short,** move its share to walk-ins (offices) and to Startup CPG events and LinkedIn (brands). A day that falls short of ten falls short: log it. Do not fill the gap with cold email from [DOMAIN] before the first cold day, and do not use a personal or another business's domain for cold email.
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

The plan's arithmetic: 150 messages at 20% is 30 conversations (Phase 0, cadence), so a reply that counts is one that can become a conversation. Every Friday the tracker's Scorecard shows, per side: the **conversation-reply rate** (`reply_type` yes, maybe, needs_approval, send_info, referral, not_now or an objection, over first touches), which drives the **"UNDER 20%"** check once a side has at least 30 first touches; the **all-reply rate** (any human reply, opt-outs included, bounces and auto-replies excluded), for information only, because a week of "no thanks" would keep it high; and the **opt-out rate**, which reads **"OPT-OUTS OVER 5%"** when there are at least 3 opt-outs and they are above 5% of first touches (judgment; at this volume 2 opt-outs in 39 is noise, as one bounce in a week is, section 3.4): then go straight to 6.3 and 6.4. It also shows conversations per first touch, which is what Gate 0 actually needs.

Change one thing at a time, in this order, and give each change a week or 30 first touches before judging it.

### 6.1 Check the measure (5 minutes)
- Are touches logged? A reply that came on LinkedIn but was never written to Clay looks like silence.
- Are follow-ups going out? Touches 2 and 3 are part of the sequence the rate assumes; if they are not being sent on time, fix that before judging the copy.
- Is the sample big enough? Under 30 first touches on a side, one reply moves the rate by more than three points.

### 6.2 Check delivery (30 minutes)
- Send the current touch 1 to a personal Gmail and a personal Outlook.com account you own. Inbox or spam? In Gmail, Show original: SPF, DKIM and DMARC all PASS?
- Bounces above 2%? Then the list, not the copy, is the problem. Office bounces naming policy or reputation: section 3.2.
- Optionally run one message through mail-tester.com (S15; its free allowance was not confirmed).
- If anything fails: stop cold email from [DOMAIN] for five business days, fix it, and put that side's touches on LinkedIn and walk-ins meanwhile.

### 6.3 Check who you are writing to
- Look at the replies you did get: which titles, company sizes, channels and `known_to_founder` values? Move the next week's list toward them (in Clay, A's scoring).
- Offices: is the person really the pantry owner? At 40 to 150 people that is usually the office manager or an executive assistant; a "head of workplace" at a larger firm often is not (judgment; check it against who actually replied). Brands: founders at the smaller end of $500k to $10M answer more of their own email than marketing leads at the top end (judgment; check against your own replies).
- Is the why-now line true and recent (under 120 days, `messages/03`)? A stale hook reads like a template.
- Many opt-outs from one kind of row (a title, an industry, a size band) mean that kind of row is the wrong target: score it down in Clay.

### 6.4 Change the copy, one variable at a time
- Swap the subject line first (variants A and B in `messages/05` and `06`). Compare variants only after about 40 first touches each, and switch only if one has at least twice the conversation replies of the other and at least four more in absolute terms (`messages/05`, "Variants and how the winner is picked", uses the same rule). Smaller gaps at this volume are noise. The Scorecard's "By sequence variant" table counts this for you.
- Then shorten: under 90 words, one ask, the specific line (their street, their store) in the first two sentences.
- Then make the ask smaller: "Who runs the pantry there?" for offices; "Would a 15-minute call next week be useful?" for brands.
- Never add urgency, a link, an attachment or a claim the tracker does not support (`messages/04-progress-slots.md`).

### 6.5 Change the mix
- Offices: move up to half of the daily ten to lobby walk-ins (Tuesday and Wednesday mornings) and referrals from the offices already talked to.
- Brands: Startup CPG events and the shelf approach ("you are already on the shelf three blocks from these offices", plan Phase 2, only where the grade is `seen_on_shelf`) usually beat cold email for founders (judgment).

### 6.6 What not to do
- Do not raise email volume to make up for a low rate. That is how new domains get burned.
- Do not buy a list, a warm-up service, or a second domain.
- Do not chase: three touches per sequence, then silence. The one exception is the plan's "keep them on a list for month three": a row that never replied may get one recontact, no earlier than 60 days after its last touch and only with something new and true to say (`messages/09`, "Silence"). Nothing after that.

### 6.7 When it is not the email
If the reply rate is fine but conversations are not turning into yeses, the problem is the offer or the target, and the plan's Gate 0 responses apply: fewer than 5 offices interested, change the cluster or the office size band, not the model; fewer than 3 brands would pay, test the office-paid version for three more weeks (plan, "If a gate fails").

---

## 7. Opt-outs and the law, in three lines

The legal pack's footer and checklist (`desk-drop-legal-pack/02-email-footer-and-checklist.md`) govern: every outreach email carries [POSTAL ADDRESS] and the reply-to-opt-out line; nothing in the header or subject misleads; every opt-out, in any words, on any channel, is written to Clay the same day (`do_not_contact = Y`, `status = do_not_contact`, `opt_out_date`) and never reversed. The tracker never exports these as pipeline `opt_out` events; those are reserved for signed offices or paid brands leaving the roster (`handoff/how-to-fill-handoff-files.md`).

## Changelog

Rounds 1 to 6 are the build rounds of the calls, sending, tracking and handoff files; a round that did not change this file is not listed. "Merge" is the step that joined them with the message files.

- Round 1 (2026-10-24): DNS steps from Google's pages (S1 to S3, S16); warm-up schedule generated and checked by script; week-one plan built on B's walk sessions, warm asks and LinkedIn; tool comparison from vendors' pricing pages (S11 to S13); under-20% playbook.
- Round 2 (2026-10-24): unsourced lines reworded as judgment or removed (follow-up reply share, "pixel by default"); the Gmail rule narrowed to what Google's page says (mail to personal Gmail accounts); the day after Thanksgiving made a no-send day after the schedule showed 18 follow-ups landing on it; caps re-checked by script.
- Round 3 (2026-10-24): critique as a deliverability specialist who has watched new domains get burned: the one-week-old-domain risk is now stated with the safer alternative (start email on Mon 2026-11-09); the 2% bounce rule tripped on a single bounce at week-2 volumes, so it is now "two bounces in a week, or 2% after 100"; the Scorecard text matches.
- Round 4 (2026-10-24): read-through: week-one Tuesday added up to 8 touches (now 10); DKIM timing restated as Google's 24 to 72 hours; the clean-week rule now uses the new bounce rule; a fallback for unaccepted LinkedIn invitations; one unlabeled judgment labeled; the trial's source cited correctly.
- Merge (2026-10-24): variant rule cross-referenced to `messages/05`; no reference to a "Part A".
- Review round 1 (2026-10-24): no cold email before Mon 2026-11-09, and then only on four conditions (else Mon 2026-11-16); from Thu 2026-10-29 every warm email goes from [EMAIL], with a daily warm target in the schedule, so the domain has real two-way history before its first cold email; a week-2 plan without cold email; the 32-day "newly registered" risk stated with its source (S17) and an office-bounce rule; a name-neutral domain so the name decision on Wed 2026-11-18 cannot restart the warm-up; the 20% check now reads conversation replies, with an opt-out rate beside it; the month-three recontact stated as the one exception to three touches.
- Review round 2 (2026-10-24): the domain is a spend with its price not checked (stop at checkout); keep its DNS at the registrar, not on Cloudflare's free name servers, with the email-gateway rule that scores Cloudflare-hosted new domains for a year (S18); the opt-out check needs at least 3 opt-outs as well as 5%; the draft maker's side shares now add up to the day's number.
- Review round 3 (2026-10-24): the mailing address for [POSTAL ADDRESS] is a row in section 1 (a spend, price not checked; USPS forms and ID from its mailing standards, S20), and no email goes until it exists, so the Monday warm asks go by phone or LinkedIn until then.
