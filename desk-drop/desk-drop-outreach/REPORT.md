# Report back: outreach engine (workstream E)

Version 1.3 · Sat 2026-10-24 · `desk-drop-outreach/` · after review round 3. Nothing was sent, posted, bought or signed up for.

## What I built, in five lines

1. Every message the founder needs, with honest subjects and one ask each: three-touch office and brand cold emails in a discovery and a selling version (A and B subjects), LinkedIn notes and follow-ups, warm-introduction, referral and lobby walk-in scripts, a reply playbook for every reply type including the four brand objections, both post-call conversion paths (the brand materials request included), the LinkedIn profile, the legal pack's footer, and three Startup CPG findings posts.
2. A fill engine (`messages/_render/fill.py`, standard library, no network) that maps every `{token}` to A's Clay columns with a fallback, unlocks every progress claim from a single slot-state file, refuses copy the state makes untrue (discovery copy once a side sells, attachments that may not go, dates that have passed, agreements before the gates, an impossible state), checks length, banned words, footer and the calendar, renders 20 phone-width examples and writes paste-ready drafts from A's daily views, capped by the warm-up.
3. The two call guides from the plan word for word, call cards, a ten-minute note template, and a tracker workbook with the plan's columns and a Friday Scorecard that reads Gate 0 per side as PASS, FAIL or INCOMPLETE (one organisation counted once, a yes counted only while it stands, offices outside 30 to 250 people on a Tuesday shown but not counted, a final read on Fri 2026-11-27), plus Gate 1, medians, objections, reply and opt-out rates, and data checks.
4. A sending plan that never sends cold volume from an unwarmed domain: a name-neutral domain, SPF, DKIM and DMARC in order, a day-by-day warm-up with caps, two weeks on warm asks, LinkedIn and walk-ins, plain Gmail at $0 extra, stop rules, the under-20% playbook, and the mailbox [POSTAL ADDRESS] needs before the first email.
5. Handoff files for operations (signed offices and paid brands: CONTRACTS 6.4 plus additions) and the financial model's nine-column pipeline export (one `org_id` per organisation), all header-only with SAMPLE copies beside them, and all built and checked by scripts.

## The folder, one line per file

- `README.md`: every file in the order used, the day-one box, the weekday hour, key dates, login steps, decisions, checks.
- `HANDOFF.md`: what E takes from A, B, C, D, F, G and H and gives to A, F, G and H, with columns, and 23 departures from CONTRACTS or the plan.
- `.gitignore`: keeps `__pycache__/` and `*.pyc` out of the repository.
- `sending/sending-setup.md`: domain, Workspace, mailbox, DNS, warm-up, weeks 1 and 2 without cold email, Gmail versus a sequencer, the under-20% playbook, opt-outs.
- `sending/dns-records.csv`: the seven DNS records in order, with when to add and how to check each.
- `sending/warmup-schedule.csv`: every weekday from Mon 2026-10-26 to Fri 2026-12-11 with caps, cold and warm volumes and the other-channel touches.
- `messages/01-founder-linkedin-profile.md`: headline, About and experience in four versions, by name decision and progress.
- `messages/02-commercial-footer.md`: the two signatures, the legal pack's footer word for word, which messages carry it, opt-outs, and why no email goes before [POSTAL ADDRESS] is real.
- `messages/03-personalization-fields.md`: every token with its Clay column (all stable since A's handoff), rule and fallback, and the routing columns that are never printed.
- `messages/03-personalization-fields.csv`: the same map, machine-readable.
- `messages/04-progress-slots.md`: the seven rules for progress claims, including that discovery copy stops when a side sells and that the state must be possible.
- `messages/04-slot-state.csv`: today's state, one row per switch or count (every switch N and every count 0 on 2026-10-24); the copy reads only this file.
- `messages/04-slot-table.csv`: every slot, what unlocks it, and the words before and after.
- `messages/05-office-cold-emails.md`: office three-touch emails, discovery and selling, subjects A and B.
- `messages/06-brand-cold-emails.md`: brand three-touch emails, discovery (nothing sold) and selling (roster, offer, price, founding term, what the report cannot show).
- `messages/07-linkedin-messages.md`: connection notes and messages, both sides, discovery and selling.
- `messages/08-warm-intro-referral-walk-in.md`: warm introduction asks, writing to people you know, referrals, the lobby walk-in script and note.
- `messages/09-reply-playbook.md`: every reply type with its answer and Clay writes, including the four objections.
- `messages/10-office-post-call-conversion.md`: the office path from call to signed, steps 0 to 8.
- `messages/11-brand-post-call-conversion.md`: the brand path from call to paid, steps 0 to 10, including the materials request (certificate, allergen sheet, logo, two card sentences, discount code).
- `messages/12-startup-cpg-posts.md`: three findings posts with slots from the tracker, a disclosure line, no pitch.
- `messages/_render/HOW-TO-RUN.md`: how to lint, rebuild the examples and make drafts.
- `messages/_render/fill.py`: the engine (fill, check, render, drafts).
- `messages/_render/shoot.js`: HTML to 390 px PNG with Playwright.
- `messages/drafts/.gitignore`: keeps drafts with real contacts out of the repository.
- `messages/examples/SAMPLE-rows.csv`, `SAMPLE-states.json`, `SAMPLE-examples.json`: the examples' inputs (four SAMPLE rows, states that obey the gates, 20 sequences).
- `messages/examples/office-discovery-email-full.html` and `-fallbacks.html`: office discovery emails, first with every field filled, then with every fallback triggered.
- `messages/examples/office-selling-email-full.html` and `-fallbacks.html`: office selling emails, both ways.
- `messages/examples/office-discovery-linkedin-full.html` and `-fallbacks.html`: office discovery LinkedIn messages, both ways.
- `messages/examples/office-selling-linkedin-full.html` and `-fallbacks.html`: office selling LinkedIn messages, both ways.
- `messages/examples/brand-discovery-email-full.html` and `-fallbacks.html`: brand discovery emails, both ways.
- `messages/examples/brand-selling-email-full.html` and `-fallbacks.html`: brand selling emails, both ways.
- `messages/examples/brand-discovery-linkedin-full.html` and `-fallbacks.html`: brand discovery LinkedIn messages, both ways.
- `messages/examples/brand-selling-linkedin-full.html` and `-fallbacks.html`: brand selling LinkedIn messages, both ways.
- `messages/examples/office-conversion-full.html` and `-fallbacks.html`: the office post-call path, both ways.
- `messages/examples/brand-conversion-full.html` and `-fallbacks.html`: the brand post-call path, both ways.
- `messages/examples/png/*.png`: the same 20 pages as 390 px PNGs, one per page.
- `calls/office-call-guide.md`: the 20-minute office call: the plan's seven questions verbatim, the budget probe, where each answer goes, the Gate 0 rule, the close.
- `calls/brand-call-guide.md`: the brand call: the anchor rule, the close, truthful answers, the seven qualification checks.
- `calls/call-cards.pdf`: one card per side to keep in front of you on a call.
- `calls/post-call-note-template.md`: the ten-minute note in the tracker's column order, number rules, two people at one organisation, the Clay write-back, objection codes, a SAMPLE example.
- `tracking/how-the-tracker-works.md`: the two stores, setup, the after-call and Friday routines, how every Scorecard number is counted, limits and tests.
- `tracking/conversation-tracker.xlsx`: the tracker to import into Google Sheets (logs, note tabs, Scorecard, Clay sync, handoff tabs, pipeline export).
- `tracking/conversation-tracker-SAMPLE.xlsx`: the same workbook with SAMPLE rows, to learn it and to check Google Sheets once.
- `tracking/scorecard-SAMPLE.pdf`: the SAMPLE Scorecard as calculated, two pages.
- `tracking/scorecard-SAMPLE-p1-top.png`, `-p1-bottom.png`, `-p2-top.png`, `-p2-bottom.png`: the same Scorecard in four readable halves.
- `tracking/csv/clay_tracking_columns.csv`: the 13 conversation-tracking columns, their allowed values and write rules.
- `tracking/csv/office_log.csv` and `tracking/csv/brand_log.csv`: the log headers.
- `tracking/csv/scorecard-SAMPLE.csv`: every SAMPLE Scorecard value.
- `handoff/how-to-fill-handoff-files.md`: when and how to fill the handoff files and the pipeline export, the event and ID rules, the column reference.
- `handoff/signed_offices.csv` and `handoff/paid_brands.csv`: to operations, header-only.
- `handoff/SAMPLE-signed_offices.csv` and `handoff/SAMPLE-paid_brands.csv`: five SAMPLE offices and one SAMPLE paid brand, to show the format.
- `exports/pipeline_log.csv`: to the financial model, header-only, exactly nine columns.
- `exports/SAMPLE-pipeline_log.csv`: 214 SAMPLE events, to show the format.
- `tools/build_tracker.py` and `tools/sample_data.py`: build both workbooks and the SAMPLE rows.
- `tools/test_tracker.py`: recalculates in LibreOffice and checks 349 values against an independent computation.
- `tools/test_h_compat.py`: pastes the SAMPLE export into a scratch copy of the financial model and checks its counts.
- `tools/export_csv.py`: writes every shipped CSV.
- `tools/render_scorecard.py`: renders the SAMPLE Scorecard to PDF and PNG.
- `tools/build_warmup.py`: builds and checks the warm-up schedule.
- `tools/build_call_cards.py`: builds the call cards from `plan.md`.
- `tools/build_handoff_tables.py`: regenerates the column tables in the handoff guide.
- `tools/check_guides.py`: checks that the guides and cards keep the plan's questions verbatim and in order.
- `tools/check_folder.py`: the whole-folder check (dates, slots, shared values, ladder words, no bytecode, and that the README lists every file).
- `_work/`: kept working notes, sources (S1 to S20) and test logs, by build half and by review round; not needed to run anything.

## Assumptions (numbered)

1. **Dates.** Every date comes from CONTRACTS section 3 and is derived, founder to confirm. CONTRACTS says today is Fri 2026-10-23; this folder was built and checked on Sat 2026-10-24. In copy, dates are slots such as [DROP DATE: Tue 2027-01-12], and they read "planned for" until `drop_date_confirmed = Y`.
2. **No cold email before Mon 2026-11-09.** The domain is bought on Mon 2026-10-26, and warm mail goes from [DOMAIN] from Thu 2026-10-29. Cold email starts Mon 2026-11-09 at 3 a day only if four conditions hold on Fri 2026-11-06; otherwise it starts Mon 2026-11-16. Weeks 1 and 2 run on warm asks, LinkedIn, walk-ins and Startup CPG contacts. That gives 145 first touches by Gate 0 (Monday of week 1 is setup), 17 of them by cold email on the default start.
3. **A name-neutral mail domain.** The working name is on hold and is decided by Wed 2026-11-18 (legal pack), so the mail domain does not depend on it. The signature names no business until `name_decided = Y`, and the website may live at its own [WEBSITE].
4. **Plain Gmail, no sequencer before Gate 1.** Workspace Business Starter is about $7 a month on a yearly plan or $8.40 billed monthly (from a third-party listing; unverified, founder to confirm at checkout). The prices of the domain and the mailbox were not checked. A sequencer such as GMass Premium ($39.95 a month) would take most of the $60 software budget.
5. **Some sending rules are judgment.** The warm-up volumes, the ramp, and the 2% bounce and 0.1% complaint stop rules are not published standards. The sources behind everything else are S1 to S20 in `_work/partB/sources.md`, opened 2026-10-24. DNS stays at the registrar, not on Cloudflare's free name servers (S18). Some corporate filters block domains registered less than 32 days ago (S17).
6. **[POSTAL ADDRESS] is a rented mailbox,** either a USPS post office box or a private mailbox, rented on Mon 2026-10-26 by default. No email goes until it is real, so the day-one warm asks go by phone or LinkedIn.
7. **Discovery until Gate 0, selling after.** Each side's selling switch turns Y with its Gate 0 pass; brand selling also needs two offices at yes in principle. Once a side sells, discovery copy that says nothing is for sale is refused for that side. Discovery threads already begun finish with their own touches 2 and 3.
8. **Gate 0 counts organisations, not Clay rows.** Two contacts at one company count once (by `org_key`, else A's `company_group`, else the company name).
   - An office yes needs a named pantry owner and a receiving window.
   - A brand yes needs $500 or more (the higher of its two numbers) and budget control.
   - Either yes counts only while it stands.
   - An office under 30 or over 250 people on a Tuesday is not counted; 30 to 39 counts, as the founder's call.
9. **INCOMPLETE is not FAIL, until the final read.** A side with fewer than 15 conversations that is short of its target reads INCOMPLETE on the day of Gate 0. It is read again a week later, on Fri 2026-11-20, and from Fri 2026-11-27 it reads FAIL. It also reads FAIL as soon as it reaches 15 conversations and is still short.
10. **Campaign zero is Tue 2027-01-12.** The last offer of it to a brand new to the pipeline is Mon 2026-11-30, and the last verbal yes Thu 2026-12-03. After that, a new brand is offered [NEXT DROP DATE: Tue 2027-02-09]. The stretch drop, Tue 2026-12-08, happens only if both brands have paid by Fri 2026-11-20.
11. **The brand agreement and invoice wait for the offices.** Five offices must sign and every office on the route must approve the brand, as the plan orders it; then the company, the attorney and the name decision come next. No agreement is dated before Thu 2026-11-19, and a brand is promised a date only once the offices are done.
12. **Two photos, not one.** The participation agreement asks for two, so the copy says two. D's office one-pager lead still says "one photo", and the founder may make that one-line edit himself.
13. **D's pages count as ready only once they may name the business** (`name_decided = Y`, or D's name-free versions). Until then the asks offer "the details", and walk-ins hand out plain cards.
14. **LinkedIn on a free account** allows three personalized connection notes a month, 200 characters each (S14). Every other invitation goes without a note, and the ask follows acceptance.
15. **No-send days** are Fri 2026-11-27 and 18 December to 4 January, and no new first touches go out on Wed 2026-11-25. Follow-ups due on those days move to the next sending day.
16. **Pipeline `opt_out` means a signed office or paid brand leaving the roster.** Outreach opt-outs stay in the table of record, so the financial model's active-office count never goes below zero.
17. **Budget probe numbers:** a range counts at its low end, "no budget" is 0 and counted, and "don't know" is blank.
18. **One recontact after silence,** at least 60 days after the last touch and only with something new to say: [RECONTACT DATE: Tue 2027-01-19].
19. **Startup CPG posting rules are unverified, founder to confirm.** Its terms and guidelines pages returned 404 on 2026-10-24. The posts share findings only, carry a disclosure line, and never pitch.
20. **The footer is the legal pack's, word for word,** including "This is a business pitch" on discovery emails. Two questions for the attorney are in HANDOFF 2.4.
21. **The table of record is A's Google Sheet until Clay is set up,** then Clay, never both. Clay Free holds 200 rows per table. Clay's page does not say how many credits the contact waterfall uses per contact.
22. **The price anchor for brands is the plan's:** one in-store demo shift runs about $300 to $700 (T-ROC 2026 pricing guide, as cited in the plan).
23. **Departures from CONTRACTS and the plan** (23 items) are listed in `HANDOFF.md` section 3. The main ones: the header-only handoff files, roster-only `opt_out`, the name-neutral domain, no cold email before Mon 2026-11-09, the withdrawn-yes and INCOMPLETE rules, one `org_id` per organisation, the 30-to-250 band and the final read.

## Changelog

- Part A round 1 (2026-10-24): drafted all twelve message files and the fill script; rendered 20 phone-width examples.
- Part A round 2: read every render as the office manager, the founder and the deliverability specialist; fixed fallback grammar, past slot dates, a 148-word brand email and softened ladder words.
- Part A round 3: step 0 emails and gates before Gate 0; a last-offer date for campaign zero; slot wording checked against the slot table; a personalization floor.
- Part A round 4: a last look; fixed "thanks for today" sent two weeks late, raw slot names, escaped dollar signs and drafts with nothing personal; 67 messages, 0 errors.
- Part B round 1: built the tracker, Scorecard, Clay sync and pipeline export; 189 checks against an independent computation.
- Part B round 2: qualification checks, a Gate 1 block and slot counts; the SAMPLE data obeys the calendar; 214 checks.
- Part B round 3: note entry tabs, call cards and the guide check; critique as office manager, founder, deliverability specialist and operations lead; 229 checks.
- Part B round 4: the Startup CPG numbers block and quote permission; the financial-model compatibility test; 241 checks.
- Part B round 5: operations' requested handoff columns; 245 checks.
- Part B round 6: a full read-through of every Part B document; all builds and tests green.
- Merge rounds 1 to 5 (2026-10-24): fixed 17 consistency and honesty defects across the two halves; wrote README, HANDOFF and the folder check; checked A's draft tables against the field map and the draft maker; composed and checked the report.
- Review round 1 (2026-10-24; 1 blocker, 5 major and 19 minor, all fixed): no cold email before Mon 2026-11-09, and then only on four conditions; warm mail from the domain as the warm-up; a name-neutral domain and a signature without the name; brand agreements wait for five signed offices and their approvals; the founding note-and-case-study term; header-only handoff files; the conversation-reply rate drives the 20% check.
- Review round 2 (2026-10-24; 1 blocker, 2 major and 18 minor, all fixed): no agreement date promised while offices are still signing; a withdrawn yes stops counting; INCOMPLETE instead of FAIL when volume falls short; the last campaign zero offer moved to Mon 2026-11-30; 275 units and the $1 million cover in the offer; attachments wait for the name decision; two spends stated; five SAMPLE signed offices; G's "company is formed" email.
- Review round 3 (2026-10-24; 3 major and 8 minor, all fixed, one narrowed):
  - Gate 0 counts organisations, not Clay rows (`org_key`, `calc_org`, A's `company_group`), and the financial model gets one `org_id` per organisation.
  - Discovery copy is refused once a side sells, and follow-ups keep to their own thread.
  - The mailbox for [POSTAL ADDRESS] is a day-one decision and a spend, and no email goes before it exists.
  - Offices outside 30 to 250 people on a Tuesday are shown, not counted.
  - Asks offer "the details" until a page may go.
  - Every example state obeys the gates, and the lint and the draft maker check the state.
  - The company name prints without brackets, with a NOTE line listing the brackets still to fill.
  - A's handoff read: its columns are stable, and the Sheet is the table of record.
  - A final read of Gate 0 on Fri 2026-11-27; the seven-questions fix; no bytecode ships.

## Checks (last run 2026-10-24, after review round 3)

- `fill.py lint`: 68 message blocks, 0 errors, 11 warnings (all-fallback rows that the draft maker refuses, and one long note meant to be forwarded whole). The self-tests pass: 384 agreement-gate combinations, 64 discovery fills under the selling switches, 35 schedule days, and 76 example steps against the gates and the default calendar.
- `tools/test_tracker.py`: 349 checks, 0 failing. The reviewer's round 3 scenario E reads 4 offices (INCOMPLETE) and 6 brands with a strict read of 4 at Gate 0, as counted by hand; scenario G leaves out the 12-person office.
- `tools/test_h_compat.py`: pass. Gate 0 is 13 and 5 for offices and 13 and 6 for brands; Gate 1 is 5 signed offices, 362 people and 1 brand paid in full; medians are 75, 500 and 850. The SAMPLE pipeline export is unchanged.
- `tools/check_guides.py`: 0 failing. `tools/build_warmup.py`: passes on both start dates. `tools/check_folder.py`: 0 failing.
- The draft maker, run on A's real daily views with simulated addresses in a scratch folder only:
  - discovery copy is refused once that side sells;
  - a step 0 sent in December says February;
  - a follow-up is refused on a row whose sequence is the other kind;
  - the office selling email asks "Could I send you the details?" while the one-pager is not ready;
  - an impossible state is refused;
  - step 8 prints the company name without brackets and carries a NOTE line.
- All 20 examples were rebuilt and rendered at 390 px, and I looked at the changed ones. The SAMPLE Scorecard was rendered to two pages and four PNGs, and I looked at them.

## Blocking questions, each with my recommended default

1. **Which domain do you buy on Mon 2026-10-26?** Default: a name-neutral domain you keep for mail whatever the name (never "deskdrop" or a lookalike), with its DNS kept at the registrar. Stop at checkout: it is a spend, and the price was not checked.
2. **Which [POSTAL ADDRESS]?** Default: rent a USPS post office box or a private mailbox on Mon 2026-10-26 (PS Form 1093 or 1583, with two IDs), and stop at the payment step to decide. Until it exists, make the day-one warm asks by phone or LinkedIn. Use a home address only if you accept it being printed on every cold email.
3. **When does cold email start?** Default: Mon 2026-11-09 if all four conditions hold on Fri 2026-11-06; otherwise Mon 2026-11-16.
4. **Who fills the contacts?** No row has a verified email, and only 31 of 308 office rows name a contact. Default: you set up Clay with A's import files and run the contact waterfall on the top 50 offices and top 60 brands by Fri 2026-10-30. Stop when Clay asks for credits or a plan: the next plan, Launch, is listed at $167 a month, over the $60 ceiling. Rows left without an email go to LinkedIn and walk-ins.
5. **How long may a side stay INCOMPLETE?** Default: no failure response on the day of Gate 0 for a side with fewer than 15 conversations. It is read again a week later, on Fri 2026-11-20, and from Fri 2026-11-27 a side still short reads FAIL and the plan's response applies.

## The first message to send on day one, and to whom

On Mon 2026-10-26, send `warm-direct` (`messages/08-warm-intro-referral-walk-in.md`, 1c) to **three office contacts and two snack or drink founders from your own warm list**: people you already know, added to the table of record with `known_to_founder = Y` and `how_we_know`. That day, send it by phone or as a LinkedIn message; from the day [POSTAL ADDRESS] is real, send it by email with the footer:

> Hi {first_name},
>
> [HOW WE KNOW EACH OTHER]
>
> I'm testing an idea before I build it: emerging snack and drink brands send sealed product to a few offices around Flatiron, NoMad and Union Square, free, and the brand gets photos and the team's feedback. You're one of the first people I wanted to ask, because [ONE TRUE REASON: you run the pantry at {company} / you have run sampling for {company}].
>
> Would you give me 20 minutes in the next two weeks?
>
> [FOUNDER NAME]

Log each one in the table of record the same day: `sequence` (`office-discovery-A` or `brand-discovery-A`), `touch_1_date`, `status = contacted`, `next_action = send_touch_2`, and `next_action_date` three business days later.
