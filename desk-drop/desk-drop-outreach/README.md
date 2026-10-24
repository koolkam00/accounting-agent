# Outreach engine

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/`

**What this folder is.** Everything you need to book 30 discovery conversations in three weeks (15 offices, 15 brands, no selling), then turn the best of them into five signed offices and two paid founding brands. Each weekday you take ten names from the day's list, send ten honest, personalized messages in under an hour, answer every reply from a playbook, run each call from a guide, log it in ten minutes, and read a Friday scorecard against Gate 0.

**What it is not.** Nothing here has been sent, posted, bought or signed up for. Every message is a template with fallbacks; every claim that depends on progress is a bracketed slot that the tracker state unlocks. Dates are derived from CONTRACTS section 3 and are **derived, founder to confirm**. Files and IDs that start with SAMPLE are illustrative placeholders, not results.

**The working name** lives in one place: `BRAND_NAME` in `desk-drop-identity/brand.json` (messages, the signature and the LLC name in the insurance request read it; `messages/_render/fill.py` stops if the file is missing). The tracker has its own copy in its Config tab (`company_name`) and in `tools/build_tracker.py` (`COMPANY_NAME`). A rename is those edits plus a rebuild. Until `name_decided = Y`, no email, profile, post, attachment or handout names the business at all (D's one-pagers and proposal print it, so they wait too).

> **State on 2026-10-24 (rechecked in review round 3): there is no one to email yet.** A has published its handoff (`clay-icp-tables/HANDOFF.md`): the 23 stable columns are confirmed, the columns E reads beyond them are now stable, and E's 13 tracking columns, the six personalization columns and `office_approvals_complete` are already in both tables. **The table of record is the Google Sheet made from `clay-icp-tables/clay-icp-tables.xlsx` until you set up Clay, then Clay; never edit status in both** (`clay-icp-tables/clay-build-sheet.md`; Clay Free takes the 175 best rows per table from `clay-icp-tables/clay-import/`). Everywhere this folder says "Clay", read "the table of record". In `offices.csv` (308 rows) and `brands.csv` (311) every row still has `email_status = none`; 31 office rows and 223 brand rows name a contact; no office row and 16 brand rows have a LinkedIn URL; 50 office rows are on `hold_before_outreach = Y`. Both daily views hold ten rows, all `channel = linkedin`; the brand view has 2 LinkedIn URLs and the office view none (you paste them in A's morning routine). Cold email cannot start before Mon 2026-11-09 anyway (below). So **weeks 1 and 2 run on warm asks, LinkedIn, lobby walk-ins and Startup CPG contacts** (`sending/sending-setup.md` section 4), and the daily views become useful once the contact waterfall has filled verified emails and office contacts. Blocking question 3 below asks you to run it by Fri 2026-10-30.

> **Day one, Mon 2026-10-26 (about two hours, half of it setup).**
> 1. **Your warm list, 30 minutes.** Write down about ten people you already know who run an office pantry, assist an executive, lead workplace or facilities, or founded a snack or drink brand. Add each to the table of record (the Google Sheet from `clay-icp-tables/clay-icp-tables.xlsx` until Clay is set up; Offices or Brands) with `known_to_founder = Y`, `how_we_know` (fifteen words or fewer, true) and `channel = warm-intro`. Nobody you know? Then day one is setup plus three LinkedIn invitations without a note, and Tuesday's walk-ins carry the office side.
> 2. **The first messages, 20 minutes.** Send `warm-direct` (`messages/08-warm-intro-referral-walk-in.md`, 1c) to **three office contacts and two founders** from that list, one at a time, each with its `{tokens}` filled from the row. **By phone or a LinkedIn message today**, the same words without the footer: every email carries [POSTAL ADDRESS], and it is not real until the mailbox exists (decision 5). From the day it is, the same message goes by email, from your existing address until Thursday (the new domain is not authenticated before then). Someone who knows the right person but is not it gets `warm-ask-office` or `warm-ask-brand` (1a, 1b) instead.
> 3. **Log each in the table of record, 5 minutes:** `sequence` (`office-discovery-A` or `brand-discovery-A`), `touch_1_date`, `status = contacted`, `next_action = send_touch_2`, `next_action_date` +3 business days.
> 4. **Setup, about an hour:** the mailbox for [POSTAL ADDRESS] (decision 5; stop at the payment step: it is a spend), buy the domain (stop at checkout: a spend) and start Workspace (the third spend), MX and SPF, the tracker into Google Sheets, join the Startup CPG Slack (`sending/sending-setup.md` sections 0 to 2 and 4).

---

## Your weekday hour

| Minutes | Do | Files |
| --- | --- | --- |
| 0 to 5 (weeks 1 to 4); 15 to 20 (weeks 5 to 7) | Open the Clay "due today" view (`next_action_date` = today): send each touch 2, touch 3, check-back and post-call email that is due. They are one or two lines each, but from Mon 2026-11-30 to Fri 2026-12-11 up to 15 to 20 follow-ups fall due on most days (`sending/warmup-schedule.csv`, `email_touch_2_due` and `email_touch_3_due`, worst case with no replies) | `messages/05`, `06`, `07`, `09`, `10`, `11` |
| 5 to 45 | Weeks 1 and 2: your warm list, LinkedIn and the walk sessions (`sending/sending-setup.md` section 4), all email from [EMAIL] from Thu 2026-10-29. From the first cold day: the ten rows in today's daily view (`clay-icp-tables/daily-view-offices.csv` and `daily-view-brands.csv`, about five of each), with no more cold email than `sending/warmup-schedule.csv` allows that day. Pick the file by `channel`, and by stage: the discovery version while that side's selling switch is N, the selling version once it is Y (the draft maker refuses discovery copy then, and a follow-up always continues the row's own `sequence`). Fill every `{token}` from the row (or let `messages/_render/fill.py drafts` do it), read it once at phone width, schedule it | `messages/03`, `05` to `08`, `messages/_render/HOW-TO-RUN.md` |
| 45 to 55 | Log each touch in Clay in the same sitting: `sequence`, `touch_1_date`, `channel`, `status = contacted`, `next_action = send_touch_2`, `next_action_date` (+3 business days by email, +5 on LinkedIn; a LinkedIn invitation alone is `await_connection`) | `tracking/csv/clay_tracking_columns.csv` |
| As they come | Each reply: find its type, send the answer (or nothing, for an opt-out), write the Clay columns. Two minutes | `messages/09-reply-playbook.md` |
| Each call | Run it from the guide, write the note within ten minutes, send the same-day email | `calls/`, `messages/10`, `11` |
| Friday, 15 minutes | Paste the Clay exports into the tracker, clear the Data checks, read Gate 0 (PASS, FAIL or INCOMPLETE per side), the conversation-reply rate and the opt-out rate, check the copy-slot counts, count your two-way threads from [EMAIL], download the pipeline export | `tracking/how-the-tracker-works.md` section 4 |

**The hour grows in weeks 5 to 7.** With 10 new first touches a day and the follow-ups of the two weeks before, a day with no replies is about 75 to 90 minutes: 15 to 20 for follow-ups, 40 for the new ten, 10 to 15 to log, plus replies. Replies shorten it (a reply stops a sequence). If it stays over 60 minutes for a week, `sending/sending-setup.md` section 5 says when a sequencer is worth its cost (stop at the payment page).

Any opt-out, in any words, on any channel: `do_not_contact = Y`, `status = do_not_contact` and `opt_out_date` in Clay the same day, no reply, every channel stopped (`messages/09`, I). A reception desk's "we don't do that here" is logged the same way.

## Key dates (derived, founder to confirm)

| What | Date |
| --- | --- |
| Discovery starts; setup day; mailbox for [POSTAL ADDRESS] rented (decision 5); name-neutral domain bought; first warm asks by phone or LinkedIn (by email once the address is real) | Mon 2026-10-26 |
| SPF and DKIM pass: from today every new email thread goes from [EMAIL] (the warm-up) | Thu 2026-10-29 |
| DMARC published by (3 business days before the earliest cold email) | Wed 2026-11-04 |
| Decision day: are the four conditions for cold email met? | Fri 2026-11-06 |
| Earliest first cold email from [DOMAIN], at 3 a day (else Mon 2026-11-16) | Mon 2026-11-09 |
| Gate 0 (5 of 15 offices yes with owner and window; 3 of 15 brands at $500 or more who control the budget; a withdrawn yes does not count) | Fri 2026-11-13 |
| Second read of a side that was INCOMPLETE on Gate 0 day (fewer than 15 conversations and the target not reached; no pivot yet) | Fri 2026-11-20 |
| Final read of Gate 0: a side still short reads FAIL and the plan's failure response applies (Config `gate0_final_read`, decision 4) | Fri 2026-11-27 |
| Selling copy may unlock; post-call step 1 for discovery yeses | Mon 2026-11-16 |
| Attorney hour and name decision held by; earliest agreement date in copy | Wed 2026-11-18; Thu 2026-11-19 |
| Stretch drop only if both brands have paid by | Fri 2026-11-20 (drop `[DROP DATE: Tue 2026-12-08]`) |
| [DOMAIN] passes the 32-day "newly registered" window some corporate filters use | Fri 2026-11-27 |
| Last day to offer campaign zero to a brand new to the pipeline; last verbal yes it can take | Mon 2026-11-30; Thu 2026-12-03 |
| Gate 1 (5 offices signed, 2 brands paid) | Fri 2026-12-11 |
| Brands asked to ship by; hard limit and cancel-by (T−10) | Tue 2026-12-22; Mon 2026-12-28 |
| Campaign zero drop | `[DROP DATE: Tue 2027-01-12]` |
| Parked rows recontacted (one recontact, at least 60 days after the last touch) | `[RECONTACT DATE: Tue 2027-01-19]` |
| Report due (Gate 2) | Fri 2027-01-22 |
| First standard drop | `[NEXT DROP DATE: Tue 2027-02-09]` |

---

## The files, in the order you use them

### 1. Week 1 setup (Mon 2026-10-26 to Fri 2026-10-30)

| File | What it is for | How to edit it |
| --- | --- | --- |
| `sending/sending-setup.md` | The sending plan: which domain to buy and when (name-neutral, so the name decision cannot restart the warm-up), Workspace on [DOMAIN] (about $8.40 a month, unverified, founder to confirm at checkout; the domain is the other spend, its price not checked), DNS at the registrar rather than on Cloudflare's free name servers, SPF, DKIM and DMARC in order, the warm-up (warm mail from [DOMAIN] from Thu 2026-10-29, cold email from Mon 2026-11-09 at the earliest on four conditions), the stop rules, two weeks that do not use cold email, plain Gmail versus a sequencer with costs, and what to change if conversation replies fall below 20% | Text. Change a date only if CONTRACTS section 3 changes |
| `sending/dns-records.csv` | The seven DNS records in order, with when to add each and how to check it | Change values only if Google's pages change |
| `sending/warmup-schedule.csv` | Every weekday from Mon 2026-10-26 to Fri 2026-12-11: the domain's age, new cold first touches by email, follow-ups due, the day's cap, the warm emails from [DOMAIN] to aim for, and the other-channel touches that keep the day at ten. Ships with the default start (Mon 2026-11-09) | `python3 tools/build_warmup.py` (or `--first-cold 2026-11-16` for the late start). It fails on a broken cap, a weekend, holiday or no-send send, cold email before the first cold day or before Mon 2026-11-09, or warm mail from [DOMAIN] before Thu 2026-10-29, and checks both starts every run |
| `messages/01-founder-linkedin-profile.md` | Your LinkedIn headline, About and experience entry, in four versions: before the name is decided (the business is not named publicly), after, once offices have signed, and after the first drop | Text. Switch versions when `name_decided` and `offices_signed` change in `messages/04-slot-state.csv`, and after the first drop |
| `messages/02-commercial-footer.md` | The signature (two versions: no business name until `name_decided = Y`, then with it) and the legal pack's footer that end every email, which messages carry it, how an opt-out is honored, and why no email goes until [POSTAL ADDRESS] is a real mailbox (decision 5) | Do not reword the footer (the legal pack's text). Set it up once as your Gmail signature; change line 2 when the name is decided |
| `tracking/how-the-tracker-works.md` | How the tracker works: the two-store rule (Clay holds status, the tracker holds what was said), setup, the after-call and Friday routines, how every Scorecard number is counted, limits and tests | Text |
| `tracking/conversation-tracker.xlsx` | The tracker to import into Google Sheets: Office_Log and Brand_Log (one row per conversation, keyed by Clay `row_id`, and counted once per organisation under `calc_org`: the optional `org_key`, else A's `company_group`, else the company name, so two contacts at one company are one office), Note_Office and Note_Brand entry tabs for a phone, the Friday Scorecard (Gate 0 per side as PASS, FAIL or INCOMPLETE until the final read on Fri 2026-11-27, counting a yes only while it stands, with the withdrawn ones shown, and an office under 30 or over 250 on a Tuesday shown but not counted; Gate 1, medians, top objections, the conversation-reply rate and its 20% check, the opt-out rate and its check (3 or more and over 5%), Startup CPG post numbers, copy-slot counts, data checks including numbers typed as text and dates with a time), the Clay sync check, the handoff tabs and the pipeline export | Type in the logs, Note tabs, handoff tabs, `later_events` and Config. Change structure in `tools/build_tracker.py`, then rebuild |
| `tracking/conversation-tracker-SAMPLE.xlsx` | The same workbook filled with SAMPLE rows, to learn it and to run the one-time Google Sheets check | Rebuilt by `tools/build_tracker.py --sample` |
| `tracking/csv/clay_tracking_columns.csv` | The 13 conversation-tracking columns to add to both Clay tables, with their allowed values (`reply_type`, `next_action`) and write rules | `CLAY_TRACKING` in `tools/build_tracker.py` |
| `messages/03-personalization-fields.md` | Every `{token}` in the copy: its Clay column, its rule, its fallback, the routing columns that are never printed (including A's `hold_before_outreach`, `opt_out_date` and the brand row's `office_approvals_complete`), and what the check against A's and B's real files found. Every column name is now stable (A's HANDOFF section 2) | Text; change a `source_column` cell only if A renames a column |
| `messages/03-personalization-fields.csv` | The same map, machine-readable; `messages/_render/fill.py` implements it | Keep in step with the `.md` |
| `messages/04-progress-slots.md` | The rules for every claim that depends on progress: which state unlocks it, the gates that stop a whole message (including no brand agreement or invoice until five offices have signed and approved the brand), what a brand is told about when the agreement comes (a date only once the offices are done), and how dates are written (never one that has passed) | Text |
| `messages/04-slot-state.csv` | Today's state, one row per switch or count, including `warm_threads_from_domain` (condition 4 for cold email) and `onepagers_name_free` (the one-pagers and the proposal print the working name, so they count as ready only once `name_decided = Y` or D has made name-free versions). **This file wins**: the copy reads only it. On 2026-10-24 every switch is N and every count is 0. The lint and the draft maker refuse a state the gates make impossible (for example offices signed before `attorney_cleared` and `name_decided`, or a founding place taken before five offices have signed) | Change a count the same day it changes; set switches by hand; the Friday Scorecard is the check |
| `messages/04-slot-table.csv` | Every slot, what unlocks it, and the exact words before and after | Change a sentence here and in `fill.py` together (`fill.py lint` fails until both agree) |

### 2. Every weekday: the first touch

| File | What it is for | How to edit it |
| --- | --- | --- |
| `messages/08-warm-intro-referral-walk-in.md` | Weeks 1 and 2 and always: warm introduction asks (double opt-in), writing to people you know, asking for and using referrals, and the lobby walk-in script with the note to leave. From Thu 2026-10-29 these emails go from [EMAIL]: they are the domain's warm-up | Text; `{tokens}` per `03` |
| `messages/05-office-cold-emails.md` | Three-touch office emails: the discovery version (a research call) and the selling version (from the office-side Gate 0 pass, the one-page outline), with subject variants A and B and how the winner is picked | Edit inside the ```message blocks; then run `fill.py lint` |
| `messages/06-brand-cold-emails.md` | Three-touch brand emails: discovery (no price, no offer) and selling (the roster, the offer, the price, the founding note-and-case-study term, and what the report cannot show) | Same |
| `messages/07-linkedin-messages.md` | LinkedIn connection notes (three a month on a free account, 200 characters) and the message and one follow-up once a request is accepted, both sides, discovery and selling | Same |
| `messages/_render/HOW-TO-RUN.md` | How to run the fill script: check every message, rebuild the examples, make paste-ready drafts from a real daily view (capped at the day's warm-up number, never on a no-send day) | Text |
| `messages/_render/fill.py` | The engine: fills a message from a Clay row and the slot state, checks it (one ask, length, banned words, legal dates, "planned" dates, the working name, footer, gates), renders the examples and writes drafts. Never sends anything; no network | Python 3, standard library |
| `messages/_render/shoot.js` | Turns the example HTML into 390-pixel PNGs with Playwright | Node |
| `messages/drafts/.gitignore` | Keeps drafts with real contacts out of the repository; drafts go in `messages/drafts/` | Leave as is |

### 3. Replies, calls and the ten-minute note

| File | What it is for | How to edit it |
| --- | --- | --- |
| `messages/09-reply-playbook.md` | Every reply type (yes, maybe, "I need to ask facilities or HR", send more info, wrong person, referral, not now, no, opt-out, the four brand objections, other questions, out of office, bounce, silence): what it means, the answer, and the Clay writes | Edit inside the message blocks; `fill.py lint` |
| `calls/office-call-guide.md` | The 20-minute office call: the plan's seven questions word for word, the budget probe read exactly, probes, which tracker column each answer goes in, the Gate 0 rule, the close, truthful answers, the walk-in version | Text; `tools/check_guides.py` checks the plan's questions stay verbatim |
| `calls/brand-call-guide.md` | The 20 to 30 minute brand call: the seven questions, the anchor rule (their number before $1,500), the close, truthful answers (including the founding term), and the seven qualification checks for weeks 4 to 7 | Same |
| `calls/call-cards.pdf` | One page per side to keep in front of you on a call | `tools/build_call_cards.py` (questions pulled from `plan.md`) |
| `calls/post-call-note-template.md` | The ten-minute note: fields in the tracker's column order, number rules, two people at one organisation (a colleague is a new Clay row with the same `company_group`, counted once), the Clay write-back, the status table, objection codes and a SAMPLE example | Text; `tools/test_tracker.py` checks the field order against the tracker on every run |

### 4. After a good call

| File | What it is for | How to edit it |
| --- | --- | --- |
| `messages/10-office-post-call-conversion.md` | Office path from call to signed: step 0 (weeks 1 to 3, thanks and, once it may go, the discovery one-pager), the one-pager with the first-drop week, the card, a last check, the referral ask, intake (seven questions), the agreement, the brand-approval email, and step 8, the legal pack's one-line "the company has taken over our agreement" email, sent once the week the company is formed to every office that signed before | Edit inside the message blocks; `fill.py lint`. The office one-pager it attaches still says "one photo" in its lead (D's `desk-drop-identity/templates/office-one-pager/office-one-pager.html`, line 57, on 2026-10-24): you may make that one-line edit yourself ("one photo" to "two photos") and rebuild it as D's README says, rather than wait for D; `office_onepager_ready` waits for it |
| `messages/11-brand-post-call-conversion.md` | Brand path from a qualifying call to paid: step 0, the proposal within 24 hours (with the 275 units and the $1 million cover), days 3, 7 and 14, the holding note (it says what the agreement still waits for: offices, approvals or formation), step 5b (every office approves the brand first), the agreement, the invoice, the email that asks for the insurance certificate, allergen sheet, logo, two card sentences and discount code, the reminder, and the ship-date email. Campaign zero's last proposal is Mon 2026-11-30 and its last verbal yes Thu 2026-12-03 | Same. Founding price only; refused once `founding_taken = 3` |

### 5. Fridays

| File | What it is for | How to edit it |
| --- | --- | --- |
| `tracking/scorecard-SAMPLE.pdf` | The SAMPLE Scorecard as LibreOffice calculates it, to see what a Friday looks like | `tools/render_scorecard.py` |
| `tracking/scorecard-SAMPLE-p1-top.png` | Page 1, top half (150 dpi, as are the other three): Gate 0 for both sides, with the withdrawn and out-of-band rows, and the medians | Same |
| `tracking/scorecard-SAMPLE-p1-bottom.png` | Page 1, bottom half: the Gate 0 result and sentence, top objections, reply rates (all, conversation, opt-out) and their checks | Same |
| `tracking/scorecard-SAMPLE-p2-top.png` | Page 2, top half: bounces, variants and channels, Gate 1, the Startup CPG post numbers | Same |
| `tracking/scorecard-SAMPLE-p2-bottom.png` | Page 2, bottom half: the copy-slot counts and the data checks (fix every FIX before reading the numbers) | Same |
| `tracking/csv/scorecard-SAMPLE.csv` | Every SAMPLE Scorecard value, to compare with your Google Sheets copy once | `tools/export_csv.py` |
| `tracking/csv/office_log.csv` | The Office_Log columns, header only | `tools/export_csv.py` |
| `tracking/csv/brand_log.csv` | The Brand_Log columns, header only | `tools/export_csv.py` |
| `exports/pipeline_log.csv` | To the financial model: one row per pipeline event in exactly its nine columns. **Ships header-only**, so nothing fake can be pasted; replace it with your Friday download | Download of the tracker's `pipeline_log` tab |
| `exports/SAMPLE-pipeline_log.csv` | The same file with 214 SAMPLE events, to see the format. Never paste it anywhere | `tools/export_csv.py` |

### 6. Weeks 3 and 4: Startup CPG findings posts

| File | What it is for | How to edit it |
| --- | --- | --- |
| `messages/12-startup-cpg-posts.md` | Three posts for the Startup CPG Slack that share what discovery found (offices from Tue 2026-11-10, brands from Thu 2026-11-12, what founders want counted from Tue 2026-11-17), every number a slot from the tracker, a one-line disclosure that you are researching a sampling service, no pitch, no name, no link, no advice on what to buy | Fill from the Scorecard block "Numbers for the Startup CPG posts" and the verbatims; delete any line you cannot fill |

### 7. At signature and payment

| File | What it is for | How to edit it |
| --- | --- | --- |
| `handoff/how-to-fill-handoff-files.md` | When and how to fill the two handoff files and the pipeline export, the event rules, ID rules, where they differ from CONTRACTS, and the full column reference | Text; column tables by `tools/build_handoff_tables.py` |
| `handoff/signed_offices.csv` | To operations: one row per signed office (the office intake columns, then CONTRACTS 6.4, then additions). **Ships header-only** | Download of the tracker's `signed_offices` tab |
| `handoff/paid_brands.csv` | To operations: one row per paid brand (the brand intake columns, CONTRACTS 6.4, payments, the founder's own qualification checks). **Ships header-only** | Download of the tracker's `paid_brands` tab |
| `handoff/SAMPLE-signed_offices.csv` | Five SAMPLE signed offices, to see the format. Never paste it anywhere | `tools/export_csv.py` |
| `handoff/SAMPLE-paid_brands.csv` | One SAMPLE paid brand, approved by the five SAMPLE offices after they signed (the order the gate requires), to see the format. Never paste it anywhere | `tools/export_csv.py` |
| `HANDOFF.md` | What this folder takes from and gives to the other workstreams, with paths and column names, and every deviation from CONTRACTS | Text |

### 8. Tools and checks (only when something changes)

| File | What it is for |
| --- | --- |
| `tools/check_folder.py` | The whole-folder check: legal dates and weekdays, slot names, shared values (`next_action`, `reply_type`, `status`, `sequence`), state keys, one variant rule, no softened ladder words, no compiled Python bytecode outside `_work/`, and that this README lists every file (the orchestrator's `_review/` and `REPORT.md` excepted). Run `python3 tools/check_folder.py` |
| `.gitignore` | Keeps `__pycache__/` and `*.pyc` out of the repository; every tool also sets `sys.dont_write_bytecode` |
| `tools/build_tracker.py` | Builds both workbooks (columns, lists, formulas, Scorecard) |
| `tools/sample_data.py` | The SAMPLE rows the tests and the SAMPLE workbook use |
| `tools/test_tracker.py` | Builds, recalculates in LibreOffice and checks 349 values against an independent computation, including an opt-out-heavy week that must turn the reply-rate check to UNDER 20%, two opt-outs that must not flag, four Gate 0 scenarios from review round 2 (withdrawn yeses, an incomplete test, text and time inputs, a full test that fails), and review round 3's: two contacts at one office and one brand counted once, the 30-to-250 headcount band, A's `company_group` and a typed `org_key`, the final read, and the note template's field order |
| `tools/test_h_compat.py` | Pastes the SAMPLE pipeline export into a scratch copy of the financial model and checks its own checks and counts, and that the live export is header-only |
| `tools/export_csv.py` | Writes every CSV this folder ships, from the build (live handoff files header-only, SAMPLE rows in the `SAMPLE-` files) or from a workbook downloaded from Google Sheets (`--from`) |
| `tools/render_scorecard.py` | Renders the SAMPLE Scorecard to PDF and to readable 150 dpi half-page PNGs |
| `tools/build_warmup.py` | Builds and checks `sending/warmup-schedule.csv` |
| `tools/build_call_cards.py` | Builds `calls/call-cards.pdf` from `plan.md` |
| `tools/build_handoff_tables.py` | Regenerates the column tables in `handoff/how-to-fill-handoff-files.md` |
| `tools/check_guides.py` | Checks the call guides and cards keep the plan's questions verbatim and in order, that the card's close and founding answer match the guide, plus dates and banned words |

**Examples.** `messages/examples/` holds every sequence filled twice at phone width (390 px): once from a full SAMPLE row and once with every fallback triggered. 20 HTML pages, 20 PNGs in `messages/examples/png/`, and their inputs (`SAMPLE-rows.csv`, `SAMPLE-states.json`, `SAMPLE-examples.json`). Rebuild with `messages/_render/HOW-TO-RUN.md` section 2.

**Working files.** `_work/` is kept: `_work/partA/` and `_work/partB/` are the notes, sources and test logs of the two halves that built this folder (message copy; calls, sending, tracking and handoff), `_work/merge/` is the merge step's notes, `_work/review-r1/` holds the notes and test logs of the first review's fixes, `_work/review-r2/` those of the second, and `_work/review-r3/` the test logs of the third (each with the reviewers' Gate 0 scripts rerun on the new workbook and the draft-maker runs; the fixes themselves are listed in the builder response at the end of `_review/round-3.md`). Nothing in `_work/` is needed to run the system.

**`REPORT.md`** is the report back for this workstream: what was built, the folder, assumptions, the changelog, blocking questions with defaults, and the first message to send on day one.

---

## Steps that need your login

Nothing below has been done. Each is yours.

1. **The mailbox for [POSTAL ADDRESS]** (decision 5, `messages/02`, `sending/sending-setup.md` section 1): a USPS post office box (PS Form 1093, online or at a Post Office, with two current IDs) or a private mailbox at a commercial mail receiving agency (PS Form 1583 with two IDs), per USPS's mailing standards (DMM 508, opened 2026-10-24). **A spend, price not checked** (the legal pack's `mailing_address_mailbox_annual` reads "needs quote"): stop at the payment step and decide. No email goes until it exists.
2. **Domain and Google Workspace** (`sending/sending-setup.md` sections 0 to 2): on Mon 2026-10-26 buy one **name-neutral** domain you will keep whatever name you choose (or, if you have checked and chosen a fallback name by Tue 2026-10-27, that name's domain), keep its DNS at the registrar rather than on Cloudflare's free name servers (section 3.2), and start Workspace Business Starter, one seat. **Two spends:** the domain (price not checked; it depends on the registrar and the ending) and Workspace (about $7 a month on a yearly plan or $8.40 monthly; third-party listing, unverified, founder to confirm at checkout). Stop at each checkout page and decide.
3. **DNS records** at your registrar, in the order of `sending/dns-records.csv`; DKIM from the Workspace Admin console; DMARC by Wed 2026-11-04.
4. **Gmail**: the outreach signature with the footer (`messages/02`, the version without the business name until the name is decided; `desk-drop-identity/USAGE-GUIDE.md` section 13), templates enabled, one template per sequence step.
5. **LinkedIn**: headline and About, version 1 (`messages/01`).
6. **Startup CPG**: join, read the pinned rules, list New York events for the next six weeks. Then set `startup_cpg_joined = Y`.
7. **The table of record (A's Google Sheet, then Clay)**: on day one pick the Google Sheet made from `clay-icp-tables/clay-icp-tables.xlsx` or Clay as the table of record, and never edit status in both (`clay-icp-tables/clay-build-sheet.md`). Check that the 13 tracking columns, the personalization columns and `office_approvals_complete` on Brands are there (A has added them; `tracking/csv/clay_tracking_columns.csv`, `messages/03-personalization-fields.csv`), and add a "due today" view on `next_action_date`. When you set up Clay, import A's `clay-import/` files (Clay Free holds the 175 best rows per table) and run the contact waterfall on the top 50 offices and top 60 brands (blocking question 3); stop when Clay asks for credits or a plan. The Friday paste is the same from either: download the Offices and Brands tabs of the Sheet (or export the Clay tables), all columns, and paste them on the tracker's Clay_Offices and Clay_Brands tabs (`tracking/how-the-tracker-works.md` section 4).
8. **Google Sheets**: import the SAMPLE workbook first and run the one-time check, then the real one (`tracking/how-the-tracker-works.md` section 2).

## Decisions waiting on you (each with the default this folder assumes)

1. **Which domain to buy on Mon 2026-10-26.** The name is chosen on Wed 2026-11-18 (legal pack), after the domain must already be warming. **Default:** a name-neutral domain you keep for mail whatever the name, with the signature naming no business until `name_decided = Y`; the website may get its own address once the name is cleared. Alternative: decide a fallback name by Tue 2026-10-27 using the legal pack's check, then buy its domain.
2. **When cold email starts.** **Default:** Mon 2026-11-09 if all four conditions hold on Fri 2026-11-06 (PASS on SPF, DKIM and DMARC; DMARC published by Wed 2026-11-04; inbox at Gmail and Outlook.com; 10 two-way threads from [EMAIL]); otherwise Mon 2026-11-16.
3. **Who fills the contacts.** On 2026-10-24 no row in A's tables has a verified email, only 31 of the 308 office rows name a contact, and none of those has a LinkedIn URL. **Default:** you set up Clay (importing A's `clay-import/` files) and run its contact waterfall on the top 50 offices and top 60 brands by Fri 2026-10-30, so the first cold day has people to write to; until then weeks 1 and 2 run on warm asks, LinkedIn and walk-ins. **Cost:** Clay's free plan includes 100 data credits and 500 actions a month and up to 200 rows per table (clay.com/pricing, opened 2026-10-24); a waterfall may use more than one credit per contact (not stated on the page), so 110 rows may not fit. Stop when Clay asks for credits or a plan: the next plan, Launch, is listed at $167 a month (the same page's FAQ says "starting at $185/mo"), over the $60 ceiling on its own. Rows left without an email go to LinkedIn and walk-ins.
4. **What to do with a side that reads INCOMPLETE on Gate 0 day, and for how long.** The calendar makes it likely: cold email starts Mon 2026-11-09 at the earliest and asks for a call "in the next two weeks", so many week-3 first touches become calls after Fri 2026-11-13. **Default:** do not apply the plan's failure response to an INCOMPLETE side (fewer than 15 conversations and the target not reached) yet; keep booking discovery calls on that side, and read the Scorecard's As of column again on Fri 2026-11-20 by the same rule (plan: "stretch the weeks but keep the gates"). **The stretch ends on Fri 2026-11-27** (Config `gate0_final_read`), or the day the side reaches 15 conversations if earlier: from then a shortfall reads FAIL and the plan's response applies. A side that passed goes ahead meanwhile; brand selling waits for a brand PASS, and campaign zero's last offer is Mon 2026-11-30.
5. **Which [POSTAL ADDRESS].** Every email prints it, and a home address printed on every cold email becomes public (legal pack 02). Options: a USPS post office box, or a private mailbox at a commercial mail receiving agency (USPS Form 1583). The price was not checked: stop at the payment step, because this is a spend (the financial model's `mailing_address_mailbox_annual`, timed in week 1). **Default:** rent one on Mon 2026-10-26. Until it exists, make the day-one warm asks by phone or LinkedIn, and start email the day the address is real. Use a home address only if you accept it being printed on every cold email.

## Checks (last run 2026-10-24, after review round 3)

`python3 messages/_render/fill.py lint` (from `messages/`): 68 message blocks, 0 errors, 11 warnings (9 messages that print nothing personal on an all-fallback row, which the draft maker refuses, and the facilities note at 187 and 188 words, a note meant to be forwarded whole). Its self-tests: steps 1 and 5 of `messages/11` in all 384 combinations of the agreement gates and four send dates; every discovery-only block under the four combinations of the two selling switches (64 fills), refused exactly when its side sells; the office and brand shares of all 35 schedule days; and the state check on the live `04-slot-state.csv`, the lint state and all 76 example steps on their send dates (review round 3). `python3 tools/test_tracker.py`: 349 checks, 0 failing, including the round 2 scenarios and round 3's: two contacts at one office and two founders of one brand count once (the reviewer's scenario E reads 4 offices, INCOMPLETE, and 6 brands with a strict read of 4 on Gate 0 day, as counted by hand), a 12-person office's yes is not counted (scenario G), A's `company_group` and a typed `org_key` join and split rows as they should, INCOMPLETE turns FAIL at the final read, and the post-call note template lists the log columns in order. `python3 tools/test_h_compat.py`: pass (H's counts equal the Scorecard's: Gate 0 13 and 5 for offices, 13 and 6 for brands; Gate 1 5 signed offices, 362 people, 1 brand paid in full; medians 75, 500 and 850; the SAMPLE pipeline export is unchanged byte for byte). `python3 tools/check_guides.py`: 0 failing. `python3 tools/build_warmup.py`: no day over its cap on either start, no cold email before Mon 2026-11-09. `python3 tools/check_folder.py`: 0 failing (it now also fails on `__pycache__` or `.pyc` outside `_work/`). The reviewers' Gate 0 scripts, rerun on the rebuilt blank workbook in scratch copies (`_work/review-r3/`): round 3's reads 4 offices and 6 brands at Gate 0 in scenario E and 4 offices in scenario G; rounds 1 and 2 name every office "SAMPLE co", which now reads as one organisation, so they were also run on scratch copies with one company per `row_id` and give exactly their earlier results (round 2: 5 and 3 with the "$600" flagged, INCOMPLETE 6 and 5, INCOMPLETE 4 and 2). The draft maker, run on A's real daily views with simulated addresses in a scratch folder (`_work/review-r3/drafts-test.txt`): brand discovery touch 1 and brand step 0 are refused once `brand_selling_on = Y`, office discovery touch 1 once `office_selling_on = Y`; a step 0 sent in December says February; a selling follow-up is refused on a row whose sequence is discovery, while the discovery follow-up finishes the thread; the office selling touch 1 asks "Could I send you the details?" while the one-pager is not ready; the reviewer's state (two offices signed with no attorney or name) is refused; and step 8 prints "Desk Drop LLC" bare with a NOTE line listing [BRAND LEGAL NAME], [BRAND ADDRESS] and [PRODUCT NAME AND SKU] and the check against the filed Articles. All 20 example pages rebuilt and rendered at 390 px; the changed ones looked at (both selling emails, both office conversion paths, the brand LinkedIn selling page). The four SAMPLE Scorecard PNGs rendered (two pages, fitted) and looked at.
