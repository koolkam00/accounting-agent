# Report back: financial model (workstream H)
Deliverable: financial-model/Desk Drop financial model v1.xlsx, attached in this folder. It is not shared anywhere. All figures are planning estimates at plan defaults, not forecasts.

## What was built (five lines)
1. One workbook with 21 tabs and 15,472 formulas. No result is typed in, no formula holds a numeric literal other than 0 or 1, and all 37 functions used are on Google's Sheets list.
2. One drop engine (revenue, seven cost lines, seven hour activities, contribution per founder hour) runs every scheduled drop, the Calculator, the plan's scenario rows and the steady state. The plan's figures reproduce within rounding.
3. A 26-week cash flow with startup outlays at their timing, brand cash on the plan's terms and overhead paid once. The lowest point is -$3,871 in week 12 (Mon 2027-01-11), so capital to commit is $4,871 against the plan's $6,510.
4. A gate dashboard (Gates 0 to 3 against live pipeline and actuals, pass, miss or not yet), the decision rule, the scenario the numbers point to, Scenarios A to D as selectable sets, break-even, and four plain-formula sensitivity tables.
5. Hours (by hand or from Toggl), pipeline and actuals tabs in the layouts F and E build to (HANDOFF.md), with the legal pack's figures pulled in. 28 checks and 54 behaviour tests pass, including a SAMPLE actuals run through every gate.

## How to use it (five lines)
1. Import into Google Sheets (README.md steps 1 to 5). Set the locale to US and the time zone to New York, then confirm the Dashboard says "all integrity checks pass".
2. Each week, add hours on Hours_Log and outreach events on Pipeline.
3. After each drop, paste the operations exports into Actuals_Campaigns and Actuals_DropCosts, then set "Actuals in" to Y on Schedule.
4. Read the Dashboard: the next drop's dollars per hour, the lowest cash point and the gap to $6,510, every gate, the rule and the scenario pointer.
5. Change any assumption on Inputs, or the drops on Schedule; "Changed?" keeps each plan default beside your edit. To test a price, use Inputs, "Standard price per office", or the Calculator.

## What the numbers say at plan defaults
- Contribution per founder hour by drop:
  - Campaign zero: $16.2.
  - Standard run 1: $57.2 (it carries five new offices).
  - Standard run 2: $66.0.
  - Each of the two direct-ship decision drops: $100.7.
  - The standard runs to Gate 3 together: $61.3, against the $50 target.
- Six months all-in: $50.3 an hour, once you count 45 discovery hours and $1,310 of overhead that the drops do not absorb. After one-time startup outlays it is $38.9. The margin over $50 is thin.
- Cash: the lowest point is -$3,871 in week 12. Capital to commit is $4,871, leaving $1,639 of headroom against $6,510. Cumulative cash at week 26 is +$12,014.
- Break-even:
  - The $3,520 of startup outlays is recovered by 4 one-brand campaigns, or by 3 campaigns on three-brand drops.
  - One standard campaign a month covers the $310 of monthly overhead.
  - Contribution reaches $50 an hour at 1.81 brands per drop (2 whole brands): 1.68 at 40% renewal, 1.17 when brands ship direct.
  - A three-brand drop reaches $50 an hour at $107.73 per office.
- Steady state:
  - Plan base: $7,660 a month at $81.1 an hour.
  - Scenario A: $9,406 at $99.6.
  - Scenario B: $7,660 plus $500 of office-paid revenue, whose cost is not quoted, at $73.7.
  - Scenario C: cash at week 26 of $7,729.
  - Scenario D: cash at week 26 of $3,444, then -$310 a month.

## Plan readings (each verified on Plan_Check; none is a fudge)
- (a) The display kit is $8 per office per drop, not per brand. Only this gives the three-brand courier drop $670 of hard costs ($830 if per brand).
- (b) Campaign zero reproduces with storage $0, transport $120 and processing 3%: $40 + $120 + $0 + $30 + $50 + $36 = $276, which the plan rounds to $280. Contribution is $924 against the plan's $920, which is $16.2 an hour.
- (c) The direct-ship row ($370) keeps the $75 storage allocation and $0 transport.
- (d) "About $47 an hour at $1,000" assumes no card processing: $2,465 / 52 h = $47.4. With 3% processing it is $45.7.
- (e) The monthly picture is two three-brand courier drops: $9,000 revenue, $1,340 hard costs ("about $1,350"), 104 hours and $7,660 contribution ("roughly $7,650").
- (f) Overhead is $310 a month, inside the plan's $200 to $350, or $160 with home storage.
- (g) The plan's capital line "Transport, campaigns zero to two: $600" does not match its own rates, which give $720. The model uses the rates.
- (h) Six hours per win = five 45-minute conversations at a 20% close rate + 2.25 hours of paperwork.

## Assumptions (numbered)
1. Prices are per office at the tier rate: $150 standard, $120 founding. Offices beyond the package pay the $150 extra-office price. Founding renewals pay $120 per office. A drop smaller than the package is priced pro rata.
2. A drop with zero brands does not run.
3. Hours are rates taken from the plan's table: 10 per first founding brand, 6 per standard win, 2 per renewal, 4 per new office, 1 per existing office, 2 per brand for reporting, 2 per drop for admin, and logistics by delivery model. These reproduce all four columns exactly.
4. A renewal costs 2 hours instead of 6. In the decision-window drops, renewals = rate x brands, rounded.
5. Card processing of 3% applies while the toggle is 1 (the high end of the range). Set it to 0 for bank transfer.
6. Insurance is $100 a month ($1,200 a year, the legal pack's working figure), paid annually at bind on Gate 1 (latest bind date 2026-12-21).
7. Storage: home for campaign zero, then a $150-a-month unit from 2027-02-01. Software $60 a month from week 1. Phone $0.
8. Courier $30 a stop. Founder delivery $120 a drop. Direct-ship $0. Mailing the kit needs a quote.
9. Legal pack figures (read 2026-10-24):
   - Articles $200 and certificate $50, both verified.
   - Publication $1,745, needs quote (New York County).
   - Licence $400: fee verified, whether it is required unknown.
   - Attorney $400 and accountant $300, plan estimates.
   - IT-204-LL filing fee $25, verified.
   - Printing $300 and domain $100 are plan estimates.
10. The trademark ($350) is excluded from the six months, following the legal pack's timing.
11. The hired and non-owned auto add-on and additional-insured endorsements stay blank until quoted.
12. Gates use real numbers only: "not yet" until the review date, then "miss".
13. Gate 2's five responses per office uses survey_responses_min_office if supplied, otherwise the average.
14. The steady state uses the courier model.
15. Not modeled: taxes, cancellations or refunds, unpaid balances, and the founder's pay. Brands supply the product and the freight.
16. The all-in view adds 45 discovery hours (15 a week, the high end of the plan's range).
17. Office fatigue is a warning, not a check.

## Derived items (founder to confirm)
- D1. CONTRACTS calendar: week 1 2026-10-26; Gate 0 2026-11-13; Gate 1 2026-12-11; campaign zero Tue 2027-01-12; Gate 2 2027-01-22; standard runs Tue 2027-02-09 and Tue 2027-02-23; Gate 3 Fri 2027-03-12; decision 2027-04-09. All are editable.
- D2. Two decision-window drops, Tue 2027-03-23 and Tue 2027-04-06, direct-ship with three brands each. This is the simplest schedule that meets the goal of two renewals and scenario B's "two more drops".
- D3. New offices: 5, then 5, then 2, reaching the goal of 12 (these are formulas).
- D4. Founding payment 20 business days before the drop; standard deposit at T-10; balance at T+1.
- D5. Startup timing: domain week 1; filing and professional hours at Gate 0; publication 2026-11-30; insurance, licence and printing at Gate 1; certificate 2027-01-11; IT-204-LL 2027-03-15.
- D6. Logistics hours by delivery model are taken from the plan's table.
- D7. Scenario levers the plan does not name use the plan base. Scenario B renewal is 0% and scenario A's price is $180, the low end of each stated range.
- D8. 28 days counts as one drop a month.
- D9. Courier $30 = $300 / 10 stops; paperwork 2.25 hours.

## Conflicts with CONTRACTS or the plan
1. Office fatigue: the CONTRACTS calendar spaces runs two weeks apart with a 12-office roster, against the plan's one drop per office a month. Two drops are flagged; the CONTRACTS dates are kept.
2. Transport: the plan's $600 lump against its own per-drop rates of $720.
3. Trademark: the plan's checklist puts it after campaign zero; the legal pack puts it outside the six months. The model follows the legal pack.
4. Toggl: CSV export is a paid-plan feature (Starter from $9 per license a month, per Toggl's help, opened 2026-10-23). The export column names are unverified, so the import tab maps columns by header name.
5. Publication: the legal pack's working figure is $1,745, against the plan's $250 to $2,000.

## Changelog (one line per round)
- Round 1: built every tab on one engine, and the plan's figures reproduce. The audit found one literal, a ROW() call, the company name in a source quote and a circular reference; all fixed.
- Round 2: brought in the legal pack's figures. Added fatigue warnings, change tracking, the unabsorbed-overhead and all-in views, Gate 3 renewals counted by signature date, and tolerance cells. Rebuilt the Dashboard layout after a visual check.
- Round 3: moved offices and brands per drop onto Inputs, so the derived Schedule rows are formulas. Unsmoothed the chart, top-aligned every cell, and added driver tests.
- Round 4: verified the last three functions on Google's list, made tolerances consistent, wrote the docs and regenerated the CSVs. Audit 0; checks 28/28; tests 54/54.

## Steps that need the founder's login
1. Google Drive and Sheets: import and check the workbook. A live import was not possible here (unverified, founder to confirm).
2. Toggl: only with a written yes to the paid plan.

## Blocking questions (with recommended defaults)
1. How much cash will you commit? Default: $4,900, which covers the $4,871 capital to commit.
2. Should run 2 go to the same offices two weeks after run 1? Default: keep the dates, let run-1 offices skip run 2, and recruit 2 spares. Going to 20 offices drops run 2 to $46.7 an hour; Gate 3 overall would still be $51.4.
3. Do you have a car for runs 1 and 2? Default: courier at $30 a stop until three quotes. Any car use needs the auto add-on quoted.
4. Which county goes on the Articles? Default: New York County, $1,745. Albany County ($345) cuts capital to commit by $1,400.
5. Can sealed cases stay at home from run 1? Default: rent the unit from 2027-02-01. Home storage saves $450 over the six months, but needs the state's answer on the licence.
