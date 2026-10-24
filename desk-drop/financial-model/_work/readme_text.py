"""Text of the README tab. Kinds: h = heading, p = paragraph, kv = (label, text).
The company name is never written here; the tab title reads it from Inputs."""

README = [
    ("h", "What this workbook is"),
    ("p", "The workbook you open every week for six months to see whether the business is working. It answers three questions: what each drop earns per founder hour, "
          "how low cumulative cash goes and when, and which gate or decision scenario the real numbers point to."),
    ("p", "Every number is a planning estimate from plan.md, never a forecast. Every assumption sits in one labeled cell on Inputs with its unit and source. "
          "Every other number is a formula. Change one input and every output moves."),

    ("h", "Your weekly routine (about ten minutes)"),
    ("kv", ("1. Log hours", "Add the week's hours on Hours_Log (one row per entry: date, drop_id or blank, activity key, hours). If you use a paid Toggl plan, paste its export on Toggl_Import instead.")),
    ("kv", ("2. Log the pipeline", "Paste or type outreach events on Pipeline: conversations, yeses, signed offices with Tuesday headcount, paid brands, budget-probe answers, renewal answers.")),
    ("kv", ("3. After each drop", "Paste the campaign actuals and drop costs from the operations exports into Actuals_Campaigns and Actuals_DropCosts, then set 'Actuals in' to Y for that drop on Schedule.")),
    ("kv", ("4. Read the Dashboard", "Gates show pass, miss or not yet against real numbers only. The headline shows the next drop's contribution per hour, the lowest point of cash and the gap to the plan's $6,510.")),
    ("kv", ("5. Keep the plan current", "Edit Schedule when a date, delivery model or brand count changes. Edit Inputs when a quote comes in. The 'Changed?' column records every edit against the plan default.")),

    ("h", "Change the price and read the result in under a minute"),
    ("kv", ("Whole model", "Inputs, section 3, 'Standard price per office' (now $150). Type a new number. Read Dashboard: 'Its contribution per founder hour' and the drop table at the bottom.")),
    ("kv", ("One drop only", "Calculator: type a price in 'Standard price per office'. The result column shows revenue, costs, hours and contribution per founder hour. Nothing else changes.")),
    ("kv", ("Many prices at once", "Sensitivity, Table 1: contribution per founder hour for eight prices and one to five brands. Green cells clear the $50 Gate 3 target.")),

    ("h", "Tabs, in the order you use them"),
    ("kv", ("Dashboard", "Headline numbers, every gate threshold beside its live value with pass, miss or not yet, the decision rule, the scenario the numbers point to, six-month goals, and contribution per hour on each drop.")),
    ("kv", ("Inputs", "Every assumption: prices, payment terms and lags, the processing toggle, units, every hard-cost line, monthly overhead, hours by activity, the delivery-model table, renewal, gates, startup outlays with timing, the start date. Yellow cells are inputs.")),
    ("kv", ("Scenarios", "The plan's decision situations A to D as assumption sets, beside the plan base. Pick one on Inputs. It drives the two decision-window drops and the steady state.")),
    ("kv", ("Schedule", "The editable drop schedule: date, delivery model, tier, offices, new offices, brands, renewals, and the switch to actuals. Checks Tuesday or Wednesday and every blackout.")),
    ("kv", ("Calculator", "A single drop of any tier, brand count, office count and delivery model, run through the same engine.")),
    ("kv", ("Drop_PnL", "Per-drop P&L on the plan basis for every scheduled drop, with hours by activity, contribution per founder hour, cash timing on the plan's terms, and live values (actual where in).")),
    ("kv", ("Cash_Flow", "Weekly cash flow for 26 weeks with a monthly cross-check: brand receipts, direct costs, overhead paid once, startup outlays at their timing, cumulative cash and its lowest point.")),
    ("kv", ("Steady_State", "The plan's monthly picture reproduced, the scenario in force at steady state, and break-even: campaigns to recover startup cash, campaigns a month to cover overhead, the brand count and price where contribution per hour crosses $50.")),
    ("kv", ("Sensitivity", "Four plain-formula tables: price x brands, renewal x brands, renewal against the monthly steady state, price against the monthly steady state. Direction checks at the bottom.")),
    ("kv", ("Plan_Check", "The plan's five scenario rows, the $1,000 reading, edge cases, the founder-hour table cell by cell, and a reconciliation of every plan figure: plan, model, difference, reason.")),
    ("kv", ("Capital", "The plan's capital table line by line, where the model pays each line, and the cash the plan's table leaves out.")),
    ("kv", ("Hours_Log", "The hand-filled hours log by the seven activity keys, with totals per drop and per week.")),
    ("kv", ("Toggl_Import", "Optional paste area for a Toggl export. Toggl says CSV export is a paid-plan feature; do not upgrade without a written yes.")),
    ("kv", ("Pipeline", "The event log from outreach, with distinct counts for every gate. Layout matches desk-drop-outreach/exports/pipeline_log.csv.")),
    ("kv", ("Actuals_Campaigns, Actuals_DropCosts", "Paste areas for campaign-ops/exports/campaign_actuals.csv and drop_costs.csv. Helper columns on the right; do not paste over them.")),
    ("kv", ("Drop_Actuals", "Actuals rolled up per drop: revenue, costs, hours, and the measurement ladder in separate columns. Read-only.")),
    ("kv", ("Cash_Ledger", "The monthly overhead payment schedule the cash flow reads. Read-only.")),
    ("kv", ("Checks", "Integrity, schedule, data and plan-reproduction checks. The Dashboard shows the integrity count.")),
    ("kv", ("Lists", "Fixed keys (delivery model, tier, activities, events), federal holidays and blackouts. Add holidays or blackouts in the blank yellow rows.")),

    ("h", "Colours and conventions"),
    ("kv", ("Yellow cell, blue text", "An input. Type here.")),
    ("kv", ("Grey cell", "Calculated on the Inputs tab. Do not type over it.")),
    ("kv", ("Green cell", "A key output.")),
    ("kv", ("Formulas", "No numeric literal other than 0 or 1 appears in any formula; conversions such as days per week sit in input cells. _work/audit_formulas.py checks this.")),
    ("kv", ("Signs", "Cash outflows are negative on Cash_Flow. Costs are positive on the P&L tabs.")),
    ("kv", ("Dates", "YYYY-MM-DD. Week 1 starts Monday 2026-10-26 (CONTRACTS section 3).")),

    ("h", "Plan readings (each verified by Plan_Check; none is a fudge)"),
    ("kv", ("(a) Display kit", "$8 per office per drop, not per brand. Only this reproduces the scenario hard costs: a three-brand courier drop is $80 + $300 + $75 + $30 + $50 + $135 = $670. Per brand it would be $830.")),
    ("kv", ("(b) Campaign zero", "Reproduces with storage at $0 (sealed cases at home), transport $120 and processing at 3%: $40 + $120 + $0 + $30 + $50 + $36 = $276, which the plan rounds to $280. Contribution is $924 against the plan's $920, and $16.2 per hour.")),
    ("kv", ("(c) Direct-ship row", "The three-brand direct-ship row ($370) keeps the $75 storage allocation and $0 transport.")),
    ("kv", ("(d) The $1,000 price", "'At $1,000 the three-brand drop drops to about $47 an hour' assumes no card processing: $2,465 / 52 h = $47.4. With processing at 3% it is $45.7.")),
    ("kv", ("(e) Monthly steady state", "$9,000 revenue, about $1,350 hard costs and 104 hours is two three-brand courier drops: $1,340 in hard costs and $7,660 contribution. The plan rounds these.")),
    ("kv", ("(f) Fixed overhead", "$60 software + $100 insurance + $150 storage + $0 phone = $310 a month, inside the plan's $200 to $350. With home storage it is $160.")),
    ("kv", ("(g) Transport lump", "The plan's capital line 'Transport, campaigns zero to two: $600' does not reconcile to its own rates ($120 + $300 + $300 = $720). The model pays transport per drop at the rates; the capital table is reproduced as printed.")),
    ("kv", ("(h) Hours per win", "Six hours per standard brand win = five qualified conversations of 45 minutes (20% close rate) plus 2.25 hours of proposal and paperwork. The close rate on Inputs moves it.")),

    ("h", "How the model counts money (no double counting)"),
    ("p", "Contribution follows the plan: revenue less hard costs, where hard costs include per-drop allocations of storage ($75), software ($30) and insurance ($50). "
          "Those allocations are views of monthly costs (monthly cost / two drops a month). The cash flow never reads them; it pays software, storage, insurance and phone once, "
          "from the Cash_Ledger schedule. Cash_Flow shows how much overhead the drops did not absorb in months with fewer than two drops."),
    ("p", "Startup outlays (formation, publication, licence, printing, domain, professional hours, trademark) are paid once at their timing. Per-drop direct costs (kits, transport, "
          "kit mailing, card processing) are paid on the drop's dates. The plan's capital table is reproduced on Capital for comparison only; the cash flow does not read it."),
    ("p", "Brand cash follows the plan's terms: founding brands pay in full before product ships (20 business days before the drop, so campaign zero's money lands at Gate 1); "
          "standard brands pay 50% at signature (at the latest, T-10) and 50% at placement confirmation (T+1). The invoice-to-cash lag is blank because the plan has none."),

    ("h", "How shared drop costs split across brands"),
    ("p", "A drop's shared costs (display kits, transport, kit mailing, overhead allocations) and shared hours (office coordination, the base of receiving, drop day, checks, admin) "
          "are split equally across the brands on the drop wherever a per-brand figure is shown (Calculator, break-even). Revenue, card processing, brand sales hours, per-brand kitting "
          "and reporting hours belong to each brand. No figure in the model depends on the split except those per-brand views."),

    ("h", "Assumptions (numbered)"),
    ("kv", ("1", "Prices are per office at the tier rate: $150 standard, $120 founding. Offices beyond the package (10 or 5) pay the $150 extra-office price. Founding-rate renewals pay $120 per office for any office count. A drop smaller than the package is priced pro rata; founder to confirm any minimum.")),
    ("kv", ("2", "A drop with zero brands does not run: no cost, no hours.")),
    ("kv", ("3", "Founder hours decompose the plan's table into rates: 10 hours per first (founding) brand, 6 per standard win, 2 per renewal, 4 per new office, 1 per existing office, 2 reporting per brand, 2 admin per drop, and logistics by delivery model (Inputs section 7). The rates reproduce all four columns exactly.")),
    ("kv", ("4", "A renewal fills a brand slot on a later drop at that brand's tier price and costs 2 hours of brand sales instead of 6. In the decision-window drops, renewals = renewal rate x brands, rounded. In the steady state they are not rounded (expected values).")),
    ("kv", ("5", "Card processing applies to every receipt while the toggle is 1 (high end of the 0% to 3% range). Set it to 0 to model bank transfer, the plan's preferred invoicing.")),
    ("kv", ("6", "General liability insurance is $100 a month (the plan's working figure and the legal pack's $1,200 a year), paid as one annual premium at bind on Gate 1, inside the legal pack's latest bind date of 2026-12-21. Needs three quotes.")),
    ("kv", ("7", "Storage: home for campaign zero, a $150-a-month unit from 2027-02-01 through the six months. Software $60 a month from week 1. Phone $0.")),
    ("kv", ("8", "Courier transport is $30 a stop ($300 for ten stops; range $25 to $40). Founder delivery is $120 a drop. Direct-ship transport is $0; mailing the kit ahead needs a quote.")),
    ("kv", ("9", "Formation, publication, licence, professional-hour and filing figures come from the legal pack (desk-drop-legal-pack/figures.csv, read 2026-10-24): Articles $200 and Certificate of Publication $50 (verified 2026-10-23); publication $1,745 for New York County (needs quote; $345 if Albany County is confirmed); licence $400 (fee verified, whether required unknown); attorney $400 and accountant $300 (plan estimates); IT-204-LL $25 (verified). Printing ($300) and domain ($100) are plan estimates.")),
    ("kv", ("10", "The trademark application ($350, verified) is left out of the six months because the legal pack times it after campaign zero passes and outside the first six months, and flags a prior descriptiveness refusal. Inputs keeps the line with Include = N.")),
    ("kv", ("11", "Hired and non-owned auto cover and building additional-insured endorsements are blank (needs quote, legal pack). Campaign zero's car rides need the auto add-on.")),
    ("kv", ("12", "Gate tests use real numbers only: the pipeline log for Gates 0 and 1, campaign actuals for Gates 2 and 3. A gate is 'not yet' until its review date passes, then 'miss' if the threshold is not met.")),
    ("kv", ("13", "Gate 2 tests five responses per office per brand campaign using survey_responses_min_office when operations supplies it, otherwise the average per office.")),
    ("kv", ("14", "The steady state uses the courier model, as the plan's monthly picture does; direct-ship raises contribution per hour.")),
    ("kv", ("15", "Not modeled: sales tax and income tax (the accountant hour decides), brand cancellations and refunds, late or unpaid balances, and the founder's own pay. Every scheduled brand pays in full on the plan's terms. Brands supply product and prepaid inbound freight, so there is no product cost.")),
    ("kv", ("16", "The six-month all-in view adds 45 discovery hours (15 a week for weeks 1 to 3, the high end of the plan's 10 to 15) that belong to no drop. Weeks 4 to 7 of selling and recruiting already sit in campaign zero's 57 hours.")),
    ("kv", ("17", "Office fatigue is a warning, not a check: the plan wants one drop per office a month, but the CONTRACTS calendar puts standard runs two weeks apart with a 12-office roster.")),

    ("h", "Derived items (founder to confirm)"),
    ("kv", ("D1", "Calendar from CONTRACTS section 3: week 1 2026-10-26; Gate 0 2026-11-13; Gate 1 2026-12-11; campaign zero Tue 2027-01-12 (moved by the December blackout); Gate 2 2027-01-22; standard drops Tue 2027-02-09 and Tue 2027-02-23; Gate 3 Fri 2027-03-12; decision 2027-04-09.")),
    ("kv", ("D2", "Two decision-window drops, Tue 2027-03-23 and Tue 2027-04-06, direct-ship, three brands each: the simplest schedule that meets the six-month goal of two renewals and scenario B's 'two more drops'.")),
    ("kv", ("D3", "New offices: five in campaign zero; standard run 1 fills its ten (five new); run 2 adds the two that reach the goal of 12 active offices. These are formulas of Inputs, so changing the drop size or the goal moves them.")),
    ("kv", ("D4", "Founding payment 20 business days before the drop (campaign zero's money at Gate 1). Standard signature at T-10 (the latest that still lets a brand ship). Balance at T+1.")),
    ("kv", ("D5", "Startup timing: domain week 1; LLC filing and both professional hours at Gate 0; publication ordered 2026-11-30 (within 10 business days of filing); insurance, licence and printing at Gate 1; Certificate of Publication 2027-01-11 after the sixth weekly run; IT-204-LL 2027-03-15.")),
    ("kv", ("D6", "Hour rates for receiving and kitting, drop day and checks by delivery model, derived from the plan's table (Inputs section 7).")),
    ("kv", ("D7", "Scenario levers the plan does not name use the plan base and say so (Scenarios, source column). Scenario B's renewal is 0%, the low end of 'under 30%'. Scenario A's post-decision price is $180, the low end of $1,800 to $2,000.")),
    ("kv", ("D8", "One drop per office every 28 days counts as 'one a month' for the office-fatigue warning.")),
    ("kv", ("D9", "Courier $30 a stop is the plan's $300 route divided by ten stops. Proposal and paperwork 2.25 hours make the plan's six hours per win at a 20% close rate.")),

    ("h", "Needs a quote or a founder decision (blank or flagged)"),
    ("kv", ("Courier", "Three quotes for a ten-stop route. Default $30 a stop.")),
    ("kv", ("Insurance", "Three general liability quotes, plus hired and non-owned auto and any building endorsements. Default $100 a month; add-ons blank.")),
    ("kv", ("Publication", "The county named in the Articles. Default New York County, $1,745; Albany County $345 if the attorney confirms it fits.")),
    ("kv", ("Kit mailing", "Postage to mail a display kit ahead of a direct-ship drop. Blank.")),
    ("kv", ("Extra tent cards", "Whether each brand on a drop needs its own card ($1 to $2 each). Blank, per reading (a).")),
    ("kv", ("Payment lag", "Your invoice terms. Blank = paid the day invoiced.")),
    ("kv", ("Founder cash", "What you commit to the six months (plan question 7). Blank.")),
    ("kv", ("Office-paid cost", "Cost to serve an office-paid office (scenario B). Blank.")),

    ("h", "Measurement honesty"),
    ("p", "The ladder stays in separate columns everywhere: delivered, placed, depleted, responded (tried is a survey answer), scanned, purchased (code redemptions). "
          "Incremental purchases are not measured, and the column says so. There is no field for sales lift, conversions or ROI."),

    ("h", "Google Sheets"),
    ("p", "Built to open in Google Sheets with formulas intact: no macros, scripts, data tables, array formulas, named ranges or add-ons. Every function used (37) appears in Google's "
          "Sheets function list (support.google.com/docs/table/25273, opened 2026-10-23 and 2026-10-24). Import: File, Import, Upload, Replace spreadsheet. A live import was not possible from the build "
          "environment, so check Dashboard and Checks after the first import (unverified, founder to confirm)."),

    ("h", "Changelog"),
] + [("kv", (f"Round {i + 1}", line)) for i, line in enumerate([
    "Draft: built every tab on one shared drop engine; plan rows, hour table, capital table and steady state reproduce. The audit found one numeric literal (a '2' in the scenario pointer), a ROW() call, the company name inside a source quote, and a circular reference between the error scan and Dashboard cells that read Checks. All fixed; 28 of 28 checks pass.",
    "Pulled the legal pack's figures.csv (publication $1,745, attorney $400 and accountant $300, IT-204-LL $25, trademark out of the six months, two needs-quote insurance add-ons). Added office-fatigue warnings, change tracking on Scenarios and Schedule, overhead-not-absorbed and six-month all-in views, Gate 3 planned renewals counted by signature date, and tolerance cells instead of exact equality. Re-laid the Dashboard after a visual check.",
    "Moved offices and brands per drop onto Inputs and made the derived Schedule rows formulas of them (new offices backed out from the 12-office goal). Unsmoothed the cash chart, top-aligned every cell, blanked unused drop rows. Behaviour tests cover a SAMPLE actuals run through every gate.",
    "Final review: verified the last three functions (DATEVALUE, TIMEVALUE, FIND) on Google's Sheets list, made every plan-row tolerance the same, wrote HANDOFF, README and REPORT, and regenerated the CSV snapshots. Audit 0 literals; 28 of 28 checks; 54 of 54 tests.",
])]
