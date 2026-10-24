# Report back: workstream F, operations and measurement (`campaign-ops/`)

Version 1.2 · Sat 2026-10-24 · after independent review round 1. **Nothing was sent, signed up for, bought or published.** All the results in this report come from SAMPLE data: illustrative placeholders, not results.

## What I built, and where

This is the system campaign zero runs on, kept through the standard runs. It works for all three delivery models: founder-carried, courier or van, and direct-ship to offices or a consolidation point. It costs **$0 a month in software** on top of the Google Workspace seat the plan already has.

Every document is made from one tracker, so nothing is typed twice. Every number in a brand report traces to a logged row or a photo (`trace.csv`). Contribution per founder hour, for each drop and each campaign, is on the dashboard the day after the drop.

Paths below are inside `campaign-ops/`. `README.md` lists every file in the order a campaign touches it.

**Tracker and hours log**
- `tracker/campaign-tracker.xlsx` is a Google-Sheets-ready workbook of 32 tabs with every formula in place and no macros.
- It is built at the six-month size: 52,615 formula cells. A full size of 88,405 cells is one flag away (`python3 tools/build_tracker.py --size full`).
- It relates drops, campaigns, brands (with the seven checks), offices, approvals, stops, inventory, counts, photos, links, survey tabs, scans, redemptions, issues, hours, costs and invoices.
- Each office's approvals row holds its whole ladder: received, allocated, delivered, placed, placed within one business day, topped up, remaining, depleted, responses, tried, scans. Its `on_drop` column marks the offices that actually took the brand.
- **Dashboard**:
  - 21 check lines, each of which should read 0;
  - one row per drop and per campaign, with every rung in its own column;
  - hours by the seven activities;
  - cost per stop, and contribution per founder hour before overhead.
- A `survey_dashboard` tab, and a read-only `report` tab that shows the plan's report layout by formulas.
- Header CSVs of the key tabs are in `tracker/csv/`.
- `tools/tracker.py` recomputes every number from the raw rows. Every generator uses it, and it is compared with the sheet's own formulas on every dry-run day.

**Forms** (one source: `spec/forms.json`)
- **Intake**: founder-side office intake (`forms/office-intake-form.md`) and brand qualification (`forms/brand-qualification-form.md`) Google Forms. They write CONTRACTS 6.3 columns into `office_intake_founder` and `brand_intake_founder`. The website's own forms can write straight into the tracker's `office_intake` and `brand_intake` tabs.
- **Survey**: the three-question survey (`forms/survey-form.md`), one form per campaign. The office rides in the link as a pre-filled card code.
- **Newsletter sign-up**: optional and separate, and the only place a consented email ever lives.
- **Open to outsiders**: every form turns off Google Workspace's default "restrict to your organization" and is tested signed out.
- **Script**: an optional Apps Script (`forms/build-forms.gs`) builds them all in one click. It is tested against a mock only.

**QR and short-link scheme** (`links/QR-AND-LINKS.md`, with a worked example)
- Two links per office per campaign: the QR link on the tent card and the post link in Slack or email.
- Each carries tracking labels and the card code `<campaign>.<office>`.
- Default tool: Short.io's free plan on a name-neutral `go.[DOMAIN]`.
- `tools/make_links.py` writes the import file, QR images, a proof sheet and a fallback redirects file for use without a link tool.

**Kit and route sheet**
- `tools/make_kit.py` makes:
  - tent cards and case labels, from the identity workstream's templates, unchanged;
  - the Slack posts and the kit checklist;
  - a decode of every printed QR, matched against its office.
- `tools/make_route.py` makes the route sheet:
  - pickup point and case count;
  - receiving windows, owner phones and the front-desk rule;
  - where the building certificate is;
  - "handed over" and "on the shelf" counts for each brand;
  - where cases taken back go.
- The route sheet fits a 390 px phone and prints on Letter. Direct-ship drops get a tracking sheet instead.

**Response dashboard**
- The `survey_dashboard` tab shows responses per office, under-5 flags and what was not counted.

**Report generator**
- `tools/make_report.py` fills the identity workstream's one-page report and writes:
  - `trace.csv`, with a roster note for any office that turned the brand away at the door;
  - each office's own summary.
- SAMPLE outputs: two reports in `dry-run/zero/reports/`, three in `dry-run/standard/reports/` and one in `dry-run/exception/reports/`.

**Invoices and payment**
- `tools/make_invoice.py` makes invoices and credit notes, paid by bank transfer, from the `invoices` tab.
- The payment-received date releases the ship date through `campaigns.ship_release`. Release also needs a signed agreement, a checked certificate, a qualified brand and every office answered.

**Debrief templates**
- `templates/debrief-brand.md` and `templates/debrief-office.md` follow plan appendices K and L.
- `templates/debrief-office-declined.md` is for an office that declined at the door.
- `tools/make_debrief.py` fills them with the campaign's numbers.

**SOP**
- `sop/SOP.md` covers T-10 to T+30 for all three models: steps, the per-stop procedure, exceptions, what counts as what, and the privacy schedule.
- It is generated from `tools/sop_steps.py`, which also makes each drop's dated checklist and `.ics` calendar file (`tools/make_calendar.py`).
- It cannot produce a Monday, Friday, holiday or blackout drop: `tools/opscal.py` and the sheet both refuse it.

**Setup runbook**
- `runbook/SETUP-RUNBOOK.md` has 24 numbered steps, marked **[FOUNDER LOGIN]** and **[SPEND]**, plus a "Speed and size" section and a list of what could not be verified.

**Exports for the financial model**
- `tools/export_actuals.py` writes exactly the financial model's columns: `campaign_actuals.csv` (26), `drop_costs.csv` (9) and `hours_log.csv` (6).

**Proof**
- Day-by-day SAMPLE replays: `dry-run/zero/`, `dry-run/standard/` (with `direct-ship-variant/`) and `dry-run/exception/`.
- `tests/run_all.sh` runs every check.
- `tools/freeze_survey.py` keeps a campaign's survey totals through the 12-month deletion of raw answers.

## What the dry runs and the four critics found

**Dry runs.** These are SAMPLE replays on the final system. For every calendar day, the tracker is rebuilt with only the rows logged by then and recalculated in LibreOffice. It is then compared with the independent arithmetic, and that day's tools run.

| Run | What it is | Days replayed | Problems (formula errors + disagreements + tool refusals + final checks) |
| --- | --- | --- | --- |
| `zero` | Campaign zero: 2 founding brands, 5 offices, founder-carried, Tue 2027-01-12 | 44 | 0 |
| `standard` | First standard run: 3 brands, 10 offices (5 new), courier, Tue 2027-02-09 | 57 | 0 |
| `exception` | Second standard run: 1 brand, 10 offices, courier, Tue 2027-02-23. 480 of 567 units arrive, and one office declines at the door | 57 | 0 (second replay; the first counted 6 refusals, all caused by the replay script itself, now fixed) |
| direct-ship variant | The standard drop re-planned as direct-ship, at T-1 | 1 | 0 formula errors. Tracking sheet, per-office ship-date emails, T-3 and T-1 messages, kit, SOP |

Each run fills every form, follows every link, generates the reports, logs hours and issues the invoices. What they show:

**Campaign zero**
- Both founding invoices were issued, plus a $120 refund credit note because office D was placed on day 3.
- 89.6% of units were placed within one business day (448 of 500).
- The fewest responses at one office is 4, so the Gate 2 response test is missed. The SAMPLE story intends this.
- Contribution before overhead is $928, or $16.28 per founder hour.

**First standard run**
- Tallgrass shipped short and every office got 3 fewer units.
- The courier ran the route, with the founder at the five first drops.
- One office vetoed one brand, credited $150.
- An owner was absent and the case was redelivered the next morning, still within one business day.
- Contribution before overhead is $3,760, or $72.31 per founder hour.

**Exception run**
- Each office received 5 fewer units because of the short shipment.
- After the decline at the door, the report generates with 9 offices, lettered A to I, and a roster note.
- The office that declined gets no day-3 or day-5 ask and a short follow-up instead of the usual debrief.
- The placement confirmation shows a $150 credit. The balance invoice nets the credit note: $600 due.
- The export reads 9 offices, 408 units depleted and 5 responses at the fewest office, so Gate 2 passes. Stock reaches zero.
- Contribution before overhead is $970.

**Financial model**
- All three runs' exports load into a copy of the financial model with 0 formula errors and every check passing. The model's own file is unchanged (SHA-256 checked).
- Gate 3 per founder hour reads $61.0 across both standard runs.
- The exception drop now reads 408 units depleted, where review round 1 found 0.

**Tests.** `bash tests/run_all.sh` passes everything in 4 min 37 s:
- calendar; blank build and recalculation; awkward rows;
- forms script; intake mapping;
- outreach handoff, including payment reconciliation;
- exceptions (8 cases); 12-month deletion;
- links and QR: 98 links, every QR decoded and followed to the right survey and office;
- office summaries; financial-model load;
- folder rules (286 text drafts and 84 CSVs checked for SAMPLE marking).

**The four critics** (my own rounds R3 and R5, then independent review round 1)

**Manhattan sampling operations lead, reading the route sheet cold.**
- R3 and R5 found:
  - missing start and pickup lines, a late rule and a 20-minute heads-up text;
  - no case count at pickup, and reserve wording that varied by model;
  - orphan lines at the end of the sheet;
  - an "after the route" block with no stated reader;
  - a hard-coded pickup time.
- Review round 1 found three more questions a courier would have to ask:
  - where is the certificate;
  - where is a handed-over count, when the courier cannot count a shelf;
  - where do cases taken back go.
- All are fixed, and the sheet now answers each one on the page.

**Brand finance lead, hunting overstatement.**
- R3 and R5 found:
  - an excluded-answers line missing from the report email;
  - a stale ship-date email after a tenth office joined;
  - credit notes that printed "How to pay";
  - a placement confirmation that did not show the amount due;
  - report letters that skipped an office that had declined.
- Review round 1 found three more:
  - payments could reach the model twice;
  - an invoice could go out with placeholder billing details;
  - an office that declined at the door understated depletion and failed Gate 2.
- All are fixed. The reviewer found no overstatement: every rung stays separate, and the trace reconciles.

**Privacy reviewer.**
- R3 and R5 found:
  - people visible in photos;
  - raw comments reaching pantry owners;
  - splits drawn from one or two people;
  - no retention rule for departed offices' contacts;
  - route sheets carrying phone numbers;
  - a T-1 text that asked for another person's name.
- Review round 1 found more:
  - the Workspace sign-in default would have broken "no login";
  - the "cannot be joined" claim about sign-up emails was wrong, because time stamps could link them;
  - a three-person split was thin;
  - deleting raw answers at 12 months wiped the record.
- All are fixed or corrected.

**Pantry owner, weighing every ask.**
- R3 and R5 found:
  - the budget question every month (now asked at drops 1, 4, 7 and so on);
  - a debrief only by phone call (email is now allowed);
  - "who should I hand it to?";
  - an allergen line running into the unit count.
- Review round 1 found two more:
  - an office that declined kept getting asks about a product it refused;
  - the summary's unit line did not add up without top-ups.
- Both are fixed.

## Changelog

- **R1, build:**
  - the calendar and drop-date validator;
  - the forms spec;
  - the tracker's definition and formulas (31 tabs then);
  - the independent arithmetic and the zero scenario.
  The first comparison found 4 mismatches; after fixes, 0.
- **R2, generators and first full replay:**
  - the report through the identity workstream's renderer;
  - exports with the financial model's exact headers;
  - the kit, with each QR decoded from the printed PDF;
  - links, route sheet, invoices, messages, the SOP calendar and `.ics`, debriefs.
  The zero replay ended with 0 errors and 0 disagreements.
- **R3, standard run and four critics:**
  - a declined office no longer blocks the ship release;
  - campaign totals are over approved offices only;
  - one approval email per office;
  - route sheet, report email and privacy fixes;
  - the direct-ship variant;
  - an optional Apps Script with a mock test.
- **R4, the founder typing real rows:**
  - a refused or missing drop date no longer turns checks into #VALUE!;
  - an awkward-rows test;
  - links are made only for offices that said yes.
- **R5, fresh critics:**
  - credit notes say how they are settled;
  - letters skip offices that declined;
  - office summaries remove likely names and hide small splits;
  - departed offices' contact details expire;
  - the T-1 text asks for no one's name;
  - a revised ship-date email when the route changes;
  - tests for the outreach workstream's real handoff files, the financial-model load and the Short.io import file.
- **Review round 1** (independent reviewer: 2 blockers, 6 majors, 9 minors; all fixed):
  - forms open to outsiders and tested signed out;
  - `on_drop` for an office that declines at the door, carried through the report, messages, debrief, export and Gate 2, with a credit check;
  - a declined case stays in reserve;
  - the rename check refuses to print two names;
  - the route sheet's certificate line, handed-over count and cases taken back;
  - payments counted once, with a reconciliation line;
  - ship release requires qualification, and invoices refuse blank billing details;
  - the sign-up privacy claim is corrected;
  - a short-shipment check, with the deviation from the plan stated;
  - SAMPLE banners on text drafts, and top-ups in office summaries;
  - survey totals are frozen before the 12-month deletion;
  - the six-month tracker size and a check for nearly full tabs;
  - founding-tier checks, a name-neutral link domain, summary threshold 5, a no-code fallback table;
  - dry runs count tool refusals;
  - the reviewer's exception scenario is replayed as `dry-run/exception`;
  - new tests `test_exception.py` and `test_retention.py`.

## Assumptions

Each is a default you can change.

1. **Tools.** All $0 a month beyond the Workspace seat:
   - Google Sheets and Google Forms, in your existing Workspace account.
   - Short.io free for links: 1,000 lifetime links and 50,000 clicks a month (short.io/pricing, opened 2026-10-24). The first six months need about 260 links.
   - Invoices from the tracker, paid by bank transfer.
   - Wave Starter, optional, as a ledger (free; waveapps.com/pricing, opened 2026-10-24).
   - Signatures: offices reply "I agree" by email; brands sign on Dropbox Sign's free plan, which allows 3 requests every 30 days with a bundle counting as one (help.dropbox.com/plans/dropbox-sign-free-plan, opened 2026-10-24).
   - No Toggl: hours go on the `hours` tab.
2. **Placed within one business day** is counted from the drop day (a photo dated by T+1) in every model. This matches the identity workstream's report check, the financial model's Gate 2 and the agreement's refund rule.
3. **Units, reserve and walking times.**
   - Units per office = 30 + 0.2 × Tuesday headcount, rounded to 5, between 30 and 80.
   - The reserve is 10%, rounded up.
   - Route walking estimates assume 80 m a minute with a hand truck, times a Manhattan grid factor of 1.3. This is a judgment, not a measurement.
4. **Storage.**
   - Sealed cases are stored at your home (config `receiving_address`; legal pack file 07).
   - A consolidation point other than your home is filed as the courier model.
   - If file 07's answer is unclear by Fri 2026-12-11, campaign zero goes direct-ship.
5. **Delivered and scanned.**
   - "Delivered" is the drop-day handover, counted by whoever handed it over. Top-ups are kept separate.
   - "Scanned" is the QR link only: the close reading minus the baseline. Post-link opens are kept apart.
6. **Offices on the drop.** An office "on the drop" approved the brand and did not turn it away at the door. Only these offices get a letter and count for Gate 2, depletion and the financial model's `offices`. Shipping, units and the cost split follow the route as planned.
7. **Credits.** A contracted office not placed by T+1, for any reason, is credited $120 (founding) or $150 (standard), unless a roster office replaces it (agreement section 8).
8. **Short shipments** change no money (question 5).
9. **Cost split and contribution.**
   - Shared costs and hours on a drop are split across its brands by offices approved.
   - The dashboard shows contribution before overhead. The financial model also subtracts its planned overhead allocation.
10. **Dates and IDs.** Drop IDs are the financial model's Schedule keys (DRP-001 is campaign zero, Tue 2027-01-12). All dates are derived from CONTRACTS section 3; founder to confirm.
11. **Consented emails.**
    - They live only in a separate sign-up form for each campaign, never linked to a sheet.
    - The ticked addresses pass to the brand once, at T+5, as an alphabetical list.
    - Unticked responses are deleted at T+5; everything is deleted 30 days after passing on.
    - You never match a sign-up to an answer by time.
12. **Privacy defaults.**
    - Office summaries break a brand's answers down only where that office gave 5 or more.
    - Raw answers are deleted 12 months after the campaign, after the counts are frozen.
    - A departed office's contact details are cleared 365 days after it leaves.
    - Printed route sheets are shredded once their counts are in the tracker.
13. **Budget question.** It is asked at an office's drops 1, 4, 7 and so on.
14. **Tracker size.** The six-month size is the default, with a warning at 90% full.
15. **Link domain.** It is name-neutral: the outreach workstream's default domain, bought Mon 2026-10-26, which also clears the 32-day new-domain rule for the Jan 12 drop.

## Handoff fields other workstreams must match

**C, website → F**
- `office_intake` and `brand_intake` carry exactly the CONTRACTS 6.3 columns, in order, in row 1. The website's script can be bound to the tracker.
- Survey forms link `https://[DOMAIN]/survey-privacy`.

**E, outreach → F**
- `signed_offices.csv`:
  - every 6.3 office column;
  - `office_id`, `clay_row_id`, `agreement_signed_date`, `agreement_file`, `founding_roster_named`, `budget_probe_verbatim`, `budget_probe_date`, `budget_probe_monthly_usd`;
  - requested: `industry`, `pantry_owner_phone`, `pantry_owner_email`, `public_naming_ok`, `agreement_version`, `building_id`.
- `paid_brands.csv`:
  - every 6.3 brand column and the 6.4 columns;
  - requested: `campaign_id`, `newsletter_option`, `brand_privacy_url`, `brand_legal_name`, `billing_address`, `billing_email`, `agreement_version`, `coi_policy_end_date`, `may_contain_verbatim`, `allergen_source`, `code_site`;
  - and `payment_1_usd`, `payment_1_date`, `payment_2_usd`, `payment_2_date`.
- Both files are read by header name, and E carries all of these today.
- **E must fill `campaign_id`** once F assigns it, so the payment reconciliation can run.
- **E's `pipeline_log.csv` is the only source of brand `paid` events** for the financial model. F no longer emits them.

**F → E**
- `[SHIP-TO ADDRESS]` is config `receiving_address`.

**F → H, financial model** (`campaign-ops/exports/`, exactly H's layout)
- `campaign_actuals.csv`: `campaign_id, drop_id, drop_date, delivery_model, tier, brand_id, offices, units_received, units_delivered, units_placed, units_placed_within_1bd, units_topped_up, units_depleted_day5, survey_responses, survey_tried_yes, qr_scans, code_redemptions_day30, revenue_usd, invoice_paid_date, processing_fee_usd, report_delivered_date, brand_would_buy_again, renewed, deposit_usd, deposit_paid_date, survey_responses_min_office`. Here `offices` means offices on the drop.
- `drop_costs.csv`: `drop_id, drop_date, delivery_model, offices, brands, kit_cost_usd, transport_cost_usd, other_direct_cost_usd, notes`.
- `hours_log.csv`: `date, drop_id, campaign_id, activity, hours, note`, where activity is one of the seven keys.
- Dates are YYYY-MM-DD; numbers are plain.

**D, identity → F**
- Tent card, case label and report JSON fields exactly as each template's `FIELDS.md` says.
- `BRAND_NAME` in `brand.json` must equal the tracker's config!B2.
- Suggested to D: an optional roster-note field on the report.

**G, legal → F**
- File 13:
  - Part A on every survey;
  - Part B's question and box on the sign-up form;
  - D1 to D11 met as the tables in `forms/survey-form.md` say;
  - keep Part C's caveat ("unless you gave an email address").
- Files 03 and 10: the 15 operating promises, mapped in HANDOFF.
- Files 11 and 12: the certificate checks.
- Processors to name in the notice: Google (Forms, Sheets, Drive, Gmail) and Short.io.

## Blocking questions

Each has my recommended default, and the default is already built in.

1. **Campaign zero storage.** May sealed cases be received and stored at your home (`receiving_address`) for about two weeks?
   *Default: yes, sealed cases only (legal pack file 07). If the food-safety call's answer is unclear by Fri 2026-12-11, campaign zero goes direct-ship.*
2. **Survey forms open to outsiders.** Will you turn off "Restrict to users in [your domain]" on every form and test each link signed out of Google?
   *Default: yes. Until you test it signed out, it is unverified that employees outside your organization can answer.*
3. **Payments logged in two places.** Do you accept logging each payment twice: in the outreach tracker (it feeds the financial model) and on this tracker's `invoices` tab (it releases the ship date)? A dashboard line flags any difference.
   *Default: yes. The alternative is for the outreach export to read this tracker's invoices, which is a change in that workstream.*
4. **Link tool.** Short.io free on `go.[DOMAIN]`?
   *Default: yes, $0. Bitly Core costs $120 a year (bitly.com/pages/pricing, opened 2026-10-24) and needs your written yes.*
5. **Short shipment.** Should a brand be credited for units it failed to ship, as the plan's exceptions table says ("credit the difference on the next campaign")?
   *Default: no credit. The price is per office, the brand agreement (file 10, section 8) is silent, and each office simply gets fewer units. If you say yes, the SOP row and G's agreement change together.*
6. **Link domain.** Keep the links on the name-neutral domain the outreach plan buys on Mon 2026-10-26?
   *Default: yes. If you buy the working name's own domain instead, the links need a second, name-neutral domain registered by Mon 2026-12-07. That is a [SPEND], and I did not check its price.*
7. **Tracker size.** Start at the six-month size (52,615 formulas) and time a cell edit on your phone (runbook step 4)?
   *Default: yes. Rebuild at full size (88,405 formulas) only if a tab nears 90% full.*
8. **Courier for campaigns one and two.** Get three quotes for a ten-stop morning route before campaign one?
   *Default: yes, quotes only. The plan budgets $25 to $40 a stop, and I found no published rate. Book only with your written yes.*
