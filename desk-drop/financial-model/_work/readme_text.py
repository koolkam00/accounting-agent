"""Text of the README tab. Kinds: h = heading, p = paragraph, kv = (label, text).
A kv text may be a list of plain strings and ("ref", input_key, number_format) parts: the build writes it as a formula,
so a quoted input (such as the price in force) never goes stale (review R2-09a).
The company name is never written here; the tab title reads it from Inputs."""

README = [
    ("h", "What this workbook is"),
    ("p", "The workbook you open every week for six months to see whether the business is working. It answers three questions: what each drop earns per founder hour, "
          "how low cumulative cash goes and when, and which gate or decision scenario the real numbers point to."),
    ("p", "Every number is a planning estimate from plan.md or the legal pack, never a forecast; fees the legal pack verified say 'verified' and the date on Inputs. Every assumption sits in one labeled cell on Inputs with its unit and source. "
          "Every other number is a formula. Change one input and every output moves. The only typed figures outside Inputs are the plan's own numbers, kept for comparison on purpose: "
          "the Plan_Check cases, the plan columns on Capital, and the 'Plan reading (e), fixed for comparison' row on Steady_State."),

    ("h", "Your weekly routine (about ten minutes)"),
    ("kv", ("1. Log hours", "Add the week's hours on Hours_Log (one row per entry: date, drop_id or blank, activity key, hours). If you use a paid Toggl plan, paste its export on Toggl_Import instead.")),
    ("kv", ("2. Log the pipeline", "Paste or type outreach events on Pipeline: conversations, yeses, signed offices with Tuesday headcount, paid brands, budget-probe answers, renewal answers.")),
    ("kv", ("3. After each drop", "Paste the campaign actuals and drop costs from the operations exports into Actuals_Campaigns and Actuals_DropCosts. Set 'Actuals in' to Y for that drop on Schedule "
                                  "once revenue, payments, direct costs and hours are final (by T+10, the debrief). code_redemptions_day30 (T+30) and renewal answers can be filled in later: "
                                  "they move no money or hours. The Gate 3 rate stays 'not yet' until every standard run dated by the review has actuals in. "
                                  "Dates must arrive as real dates and amounts as numbers: if Checks says 'stored as text', see 'Dates and amounts' below.")),
    ("kv", ("4. Read the Dashboard", "Next to 'Checks' it should say 'all integrity and data checks pass'; if not, open Checks first, because a failing data check means pasted rows are being ignored. Gates show pass, miss or not yet against real numbers only. The headline shows the next drop's contribution per hour, the price in force, the lowest point of cash and the gap to the plan's $6,510.")),
    ("kv", ("5. Check against the bank (optional)", "Type your actual bank balance at the end of the week on Cash_Flow, row 30. Row 31 shows the variance against the model; the summary shows the latest week.")),
    ("kv", ("6. Keep the plan current", "Edit Schedule when a date, delivery model or brand count changes. Edit Inputs when a quote comes in. The 'Changed?' column records every edit against the plan default.")),

    ("h", "Change the price and read the result in under a minute"),
    ("kv", ("Whole model", ["Inputs, section 3, 'Standard price per office' (now ", ("ref", "price_std_office", "$#,##0"), "). Type a new number. On the Dashboard read 'Price in force' (it shows your number), then ",
                            "'A standard drop at that price: contribution per founder hour' (the next row), 'Standard runs to Gate 3' and the drop table at the bottom. ",
                            "'Its contribution per founder hour' does not move: the next drop is campaign zero, at the founding rate."])),
    ("kv", ("One drop only", "Calculator: type a price in 'Standard price per office'. The result column shows revenue, costs, hours and contribution per founder hour. Nothing else changes.")),
    ("kv", ("Many prices at once", "Sensitivity, Table 1: contribution per founder hour for eight prices and one to five brands. Green cells clear the $50 Gate 3 target.")),

    ("h", "Tabs, in the order you use them"),
    ("kv", ("Dashboard", "Headline numbers; cash at each stop point (paid out, brand cash received, refunds owed on campaigns not yet run, and the net if you stop at each gate); every gate threshold beside its live value with pass, miss or not yet; the decision rule, the scenario the numbers point to, six-month goals, and contribution per hour on each drop.")),
    ("kv", ("Inputs", "Every assumption: prices, payment terms and lags, the processing toggle, units, every hard-cost line, monthly overhead, hours by activity, the delivery-model table, renewal, gates, startup outlays with timing, the start date. Yellow cells are inputs.")),
    ("kv", ("Scenarios", "The plan's decision situations A to D as assumption sets, beside the plan base. Pick one on Inputs. It drives the two decision-window drops and the steady state.")),
    ("kv", ("Schedule", "The editable drop schedule: date, delivery model, tier, offices, new offices, brands, renewals, and the switch to actuals. Checks Tuesday or Wednesday and every blackout. "
                         "Columns Y to AE show the brand wins and qualified conversations each drop needs, cumulated to its sign-by date, beside the Pipeline's actual counts; AF to AH flag a "
                         "decision-window drop whose debrief lands after the decision date; AI shows the offices to add so no office gets two drops within four weeks. "
                         "A drop you add takes the next spare drop_id (DRP-006 onward) and may sit out of date order: that is fine, because every total, the cash flow and the "
                         "Dashboard's next drop read dates, not row order. Never re-sort the rows: the drop_id is the key every actuals file uses.")),
    ("kv", ("Calculator", "A single drop of any tier, brand count, office count and delivery model, run through the same engine.")),
    ("kv", ("Drop_PnL", "Per-drop P&L on the plan basis for every scheduled drop, with hours by activity, contribution per founder hour, cash timing on the plan's terms, and live values (actual where in).")),
    ("kv", ("Cash_Flow", "Weekly cash flow for 26 weeks with a monthly cross-check: brand receipts, direct costs, overhead paid once, startup outlays at their timing, cumulative cash and its lowest point. "
                          "Row 30 takes your actual bank balance; row 31 shows the variance. Below the monthly view: overhead not absorbed, and insurance prepaid beyond the six months.")),
    ("kv", ("Steady_State", "The plan's monthly picture reproduced (row 7, fixed for comparison), a standard drop on today's Inputs (row 8), the scenario in force at steady state, and break-even: "
                             "campaigns to recover startup cash, campaigns a month to cover overhead, the brand count and price where contribution per hour crosses $50. Every break-even line follows Inputs.")),
    ("kv", ("Sensitivity", "Four plain-formula tables: price x brands, renewal x brands, renewal against the monthly steady state, price against the monthly steady state. Direction checks at the bottom.")),
    ("kv", ("Plan_Check", "The plan's five scenario rows, the $1,000 reading, edge cases, the founder-hour table cell by cell, and a reconciliation of every plan figure: plan, model, difference, reason.")),
    ("kv", ("Capital", "The plan's capital table line by line, where the model pays each line, and the cash the plan's table leaves out.")),
    ("kv", ("Hours_Log", "The hand-filled hours log by the seven activity keys, with totals per drop and per week.")),
    ("kv", ("Toggl_Import", "Optional paste area for a Toggl export. Toggl says CSV export is a paid-plan feature; do not upgrade without a written yes.")),
    ("kv", ("Pipeline", "The event log from outreach, with distinct counts for every gate. Layout matches desk-drop-outreach/exports/pipeline_log.csv. Gate 1 counts a brand as paid in full once its payments add up to the founding package price. A brand's budget_probe answer given after hearing $1,500 carries notes = after_1500; medians use one answer per organisation.")),
    ("kv", ("Actuals_Campaigns, Actuals_DropCosts", "Paste areas for campaign-ops/exports/campaign_actuals.csv and drop_costs.csv: exactly the HANDOFF columns, in order. Ten or more blank columns "
                                                     "separate each paste area from its helpers; Checks flags a header that differs or anything pasted in the blank columns.")),
    ("kv", ("Drop_Actuals", "Actuals rolled up per drop: revenue, costs, hours, and the measurement ladder in separate columns. Read-only.")),
    ("kv", ("Cash_Ledger", "The monthly overhead payment schedule the cash flow reads. Read-only.")),
    ("kv", ("Checks", "Integrity, schedule, data and plan-reproduction checks. The Dashboard shows the integrity count.")),
    ("kv", ("Lists", "Fixed keys (delivery model, tier, activities, events), federal holidays and blackouts. Add holidays or blackouts in the blank yellow rows.")),

    ("h", "Colours and conventions"),
    ("kv", ("Yellow cell, blue text", "An input. Type here.")),
    ("kv", ("Blue cell", "An input whose default follows another cell (a gate date, Inputs or the scenario in force). Type over it to replace; the 'Changed' flag records it.")),
    ("kv", ("Grey cell", "Calculated on the Inputs tab. Do not type over it.")),
    ("kv", ("Green cell", "A key output.")),
    ("kv", ("Formulas", "No numeric literal other than 0 or 1 appears in any formula; conversions such as days per week sit in input cells. _work/audit_formulas.py checks this.")),
    ("kv", ("Signs", "Cash outflows are negative on Cash_Flow. Costs are positive on the P&L tabs.")),
    ("kv", ("Dates", "YYYY-MM-DD. Week 1 starts Monday 2026-10-26 (CONTRACTS section 3). Moving week 1 does not move the gate or drop dates, which are typed CONTRACTS dates: move them too (Checks flags week 1 moved on its own).")),
    ("kv", ("Dates and amounts must be real dates and numbers", "Every date window and every amount is a SUMIFS, so a date or amount stored as text drops out of the cash flow and the gates with no error. "
                                                             "Checks has one 'stored as text' line per paste tab, and the Dashboard banner turns red. To avoid it: bring the CSV in with File, Import, "
                                                             "'Replace data starting at selected cell', with cell A4 of the tab selected (support.google.com/docs/answer/40608, opened 2026-10-24); "
                                                             "if the dialog offers to convert text to numbers and dates, leave it on (unverified, founder to confirm). To fix a column that is "
                                                             "already text: put =DATEVALUE(cell) for a date or =VALUE(cell) for an amount in a spare column, copy it, paste it back over the original "
                                                             "column as values only, and clear the spare column. A format change alone may leave stored text as text, so read the Checks line again after the fix.")),

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
          "from the Cash_Ledger schedule. Cash_Flow shows how much overhead the drops did not absorb in months with fewer than two drops. "
          "The six-month all-in rate on the Dashboard charges overhead on an expensed basis: the annual insurance premium paid at bind covers about a year, so the part that covers months "
          "after the six months ($700 at defaults) is shown as prepaid and left out of the rate. The cash flow still pays the full premium at bind."),
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
    ("kv", ("6", "General liability insurance is $100 a month (the plan's working figure and the legal pack's $1,200 a year), paid as one annual premium at bind on Gate 1, inside the legal pack's latest bind date of 2026-12-21. Needs three quotes. For the all-in rate, each month of cover is expensed in the month it starts: five months fall inside the window, so $700 of the premium is prepaid beyond it.")),
    ("kv", ("7", "Storage: home for campaign zero, a $150-a-month unit from 2027-02-01 through the six months. Software $60 a month from week 1. Phone $0.")),
    ("kv", ("8", "Courier transport is $30 a stop ($300 for ten stops; range $25 to $40). Founder delivery is $120 a drop. Direct-ship transport is $0; mailing the kit ahead needs a quote.")),
    ("kv", ("9", "Formation, licence, professional-hour and filing figures come from the legal pack (desk-drop-legal-pack/figures.csv, read 2026-10-24 and re-read after its 01:52 and 02:33 updates the same day): Articles $200 and Certificate of Publication $50 (verified 2026-10-23); licence $400 (fee verified, whether required unknown); attorney $400 and accountant $300 (plan estimates that keep the plan's 'about $700' for both hours); IT-204-LL $25 (verified). Newspaper publication is the plan's high end, $2,000 (range $250 to $2,000, no working figure in the plan), because the legal pack's figure is not yet verified: its working $1,745 for New York County and $345 for Albany County both still need a quote. Printing ($300) and domain ($100) are plan estimates.")),
    ("kv", ("10", "The trademark application ($350 per class, verified) is in the six months, paid on the Gate 2 day if campaign zero passes: the plan's setup checklist lists 'Trademark application, if the campaign was a pass' after campaign zero, and the legal pack now times it from about Mon 2027-01-25, inside the six months. The plan's capital table has no line for it. The Gate 2 day is the earliest and most cautious date. USPTO refused a prior DESK-DROP application as merely descriptive: set Include = N if the attorney advises against filing.")),
    ("kv", ("11", "Hired and non-owned auto cover and building additional-insured endorsements are blank (needs quote, legal pack). Campaign zero's car rides need the auto add-on. A mailing address (PO box or private mailbox, only if you will not use a home address) and a registered agent (Albany County route only, Include = N) are blank too; the legal pack invents no figure for either.")),
    ("kv", ("12", "Gate tests use real numbers only: the pipeline log for Gates 0 and 1, campaign actuals for Gates 2 and 3. A gate is 'not yet' until its review date passes, then 'miss' if the threshold is not met.")),
    ("kv", ("13", "Gate 2 tests five responses per office per brand campaign using survey_responses_min_office when operations supplies it, otherwise the average per office.")),
    ("kv", ("14", "The steady state uses the courier model, as the plan's monthly picture does; direct-ship raises contribution per hour.")),
    ("kv", ("15", "Not modeled: sales tax and income tax (the accountant hour decides), brand cancellations and refunds, late or unpaid balances, and the founder's own pay. Every scheduled brand pays in full on the plan's terms. Brands supply product and prepaid inbound freight, so there is no product cost. "
                  "Two brand terms from the legal pack's brand agreement (10, sections 3 and 8) are not modeled either: a founding price is due within five business days of the invoice and before shipping, which fits D4 if the invoice goes out by Fri 2026-12-04; and a brand may cancel for a full refund if outside events move a drop more than once or by more than three weeks in all. An office not placed by T+1 is refunded or credited ($150 standard, $120 founding).")),
    ("kv", ("16", "The six-month all-in view adds the hours that belong to no drop: 45 planned discovery hours (15 a week for weeks 1 to 3, the high end of the plan's 10 to 15), or the hours logged inside the 26 weeks with a blank drop_id once there are more of them. Weeks 4 to 7 of selling and recruiting already sit in campaign zero's 57 hours, so log them against DRP-001.")),
    ("kv", ("17", "Office fatigue is a warning, not a check: the plan wants one drop per office a month, but the CONTRACTS calendar puts standard runs two weeks apart with a 12-office roster. The Dashboard shows its cost: with a roster big enough for one drop per office a month, standard runs to Gate 3 earn $51.4 an hour instead of $61.3, just above the $50 bar.")),
    ("kv", ("18", "No founding-rate renewal is scheduled by default. Campaign zero's report lands 2027-01-22 and its debrief 2027-01-27: after run 1's latest signature (2027-01-26), and for run 2 a founding renewal would have to pay in full by 2027-01-25 (20 business days ahead), before its debrief. The decision-window renewals (renewal rate x brands, rounded) are priced at the standard rate. If one is a founding brand, enter it under 'of which founding-rate renewals': each one costs $300 of revenue against a standard renewal (10 offices x $30) and saves no hours; against a new standard brand it costs $300 and saves 4 hours.")),
    ("kv", ("19", "A renewal counts toward Gate 3 only when the pipeline's renewal_answer says yes and commits $1,500 or more, and each brand counts once, however many rows repeat it.")),
    ("kv", ("20", "Pasted files carry exactly the HANDOFF columns, in order. Each paste area has ten or more blank columns before its helpers, and Checks flags a header that differs or anything pasted in the blank columns. Extra fields go in a separate file.")),
    ("kv", ("21", "Scenario B's office-paid revenue ($500 a month) is shown but left out of the steady-state net until its cost to serve is quoted, so an unpriced cost never makes B look better than the plan base.")),
    ("kv", ("22", "The capital table's $300 'printing and materials' is read as startup supplies (hand truck, supplies, first card run). Campaign zero also pays $40 of display kits on its drop. If the first card run is those kits, $40 is counted twice; the model keeps both plan figures (conservative by $40).")),
    ("kv", ("23", "The decision rule says Stop only when both tests have failed. While renewal is under 30% and fewer than two drops after Gate 3 have actuals, it says the switch test is still running, because the plan's situation B is 'run two more drops' first.")),
    ("kv", ("24", "Gate 1 counts a brand as 'paid in full' once its paid rows by the review date add up to the founding package price ($600 at defaults). A deposit or part payment alone does not count. Each payment is its own row, in date order.")),
    ("kv", ("25", "A brand's budget_probe value is the number it named before hearing $1,500. An answer given after hearing $1,500 is a second budget_probe row with notes = after_1500. Gate 0 counts a brand if any of its answers is $500 or more and it controls the budget. Each median uses one answer per organisation: its first numeric answer before the anchor (brands also get a separate after-anchor median).")),
    ("kv", ("26", "The Gate 3 rate passes only when every standard run that runs and is dated by the review date has actuals in. Until then its status reads 'not yet: N standard run(s) without actuals', whatever the date. The all-drops rate and the scenario pointer say how many drops with results due (T+10 by the as-of date) are still missing.")),
    ("kv", ("27", "The storage unit is rented from the first day of the month of the first standard drop that runs. With no standard drop scheduled, no unit is rented.")),
    ("kv", ("28", "The brand renewal rate counts brands, not campaigns, as the plan's test does ('40% of brands renew'): brands with at least one renewed = Y, over brands with any Y or N answer, each brand_id once. So brand_id must stay the same across a brand's campaigns.")),
    ("kv", ("29", "Cost lines with no figure yet (needs quote or needs founder decision) count as $0 in the cash flow. The Dashboard's capital-to-commit line says how many: 5 at defaults (mailing address, hired and non-owned auto, building endorsements, kit mailing, extra tent cards).")),
    ("kv", ("30", "Cash at each stop point: 'paid out' is gross, with no brand money. 'Net if you stop here' adds brand cash received by the review day and takes off refunds of payments for campaigns whose drop has not run (at Gate 3, the decision-window deposits). Card fees on refunded payments are not recovered.")),

    ("h", "Derived items (founder to confirm)"),
    ("kv", ("D1", "Calendar from CONTRACTS section 3: week 1 2026-10-26; Gate 0 2026-11-13; Gate 1 2026-12-11; campaign zero Tue 2027-01-12 (moved by the December blackout); Gate 2 2027-01-22; standard drops Tue 2027-02-09 and Tue 2027-02-23; Gate 3 Fri 2027-03-12; decision 2027-04-09.")),
    ("kv", ("D2", "Two decision-window drops, Tue 2027-03-23 and Tue 2027-04-06, direct-ship, three brands each. They are not in the plan's roadmap table (campaign zero and two standard runs, 8 paid campaigns against the goal of 6). They come from the decision rule ('after two extra drops'), scenario B ('run two more drops') and scenario A (two drops a month). They carry the schedule's two renewals. The Dashboard shows the six-month all-in rate and week-26 cash with and without them: at defaults $33.8 an hour and $2,839 for the roadmap alone, $52.5 and $11,409 with them. The schedule needs 12 new brand wins by 2027-03-23 (about 60 qualified conversations at a 20% close rate); Schedule columns Y to AE show them by sign-by date beside the Pipeline's actual counts.")),
    ("kv", ("D3", "New offices: five in campaign zero; standard run 1 fills its ten (five new); run 2 adds the two that reach the goal of 12 active offices. These are formulas of Inputs, so changing the drop size or the goal moves them.")),
    ("kv", ("D4", "Founding payment 20 business days before the drop (campaign zero's money at Gate 1). Standard signature at T-10 (the latest that still lets a brand ship). Balance at T+1.")),
    ("kv", ("D5", "Startup timing, each a formula of the date it depends on (legal pack timing, re-read 2026-10-24 after its 02:33 update): domain and any mailbox in week 1; attorney hour Wed 2026-11-18 and accountant hour Fri 2026-11-20 (3 and 5 business days after Gate 0); LLC filing Thu 2026-11-19 (4 business days after Gate 0, the day after the attorney hour); publication 10 business days after filing (Fri 2026-12-04, skipping Thanksgiving); insurance, its add-ons, licence and printing at Gate 1; Certificate of Publication after the sixth weekly run (2027-01-15); trademark at Gate 2; IT-204-LL on its statutory date, 2027-03-15. If Gate 0 or Gate 1 slips, these move with it.")),
    ("kv", ("D6", "Hour rates for receiving and kitting, drop day and checks by delivery model, derived from the plan's table (Inputs section 7).")),
    ("kv", ("D7", "Scenario levers the plan does not name follow the plan base by formula (blue cells on Scenarios), so an Inputs edit reaches every scenario. Scenario B's renewal is 0%, the low end of 'under 30%'. Scenario A's post-decision price is $180, the low end of $1,800 to $2,000. Scenario A recruits 4 new offices on each decision-window drop, taking the 12-office roster to 20, the low end of 'grow the roster to 20 to 30 offices'.")),
    ("kv", ("D8", "One drop per office every 28 days counts as 'one a month' for the office-fatigue warning.")),
    ("kv", ("D9", "Courier $30 a stop is the plan's $300 route divided by ten stops. Proposal and paperwork 2.25 hours make the plan's six hours per win at a 20% close rate.")),
    ("kv", ("D10", "Gate 2 follows its drop on Schedule: the campaign-zero date plus seven business days (2027-01-22). The storage unit starts on the first day of the month of the first standard drop that runs (2027-02-01).")),
    ("kv", ("D11", "DRP-005's debrief (T+10) is Tue 2027-04-20, after the canonical decision date of Fri 2027-04-09 (CONTRACTS section 3). The model keeps the canonical date and warns on the Dashboard; REPORT.md asks whether to move the review to 2027-04-20.")),

    ("h", "Needs a quote or a founder decision (blank or flagged)"),
    ("kv", ("Courier", "Three quotes for a ten-stop route. Default $30 a stop.")),
    ("kv", ("Insurance", "Three general liability quotes, plus hired and non-owned auto and any building endorsements. Default $100 a month; add-ons blank.")),
    ("kv", ("Publication", "A quote once the county named in the Articles is settled. Default $2,000, the plan's high end, until then. The legal pack's working figures: New York County $1,745, Albany County $345 if the attorney confirms it fits.")),
    ("kv", ("Kit mailing", "Postage to mail a display kit ahead of a direct-ship drop. Blank.")),
    ("kv", ("Extra tent cards", "Whether each brand on a drop needs its own card ($1 to $2 each). Blank, per reading (a).")),
    ("kv", ("Payment lag", "Your invoice terms. Blank = paid the day invoiced.")),
    ("kv", ("Founder cash", "What you commit to the six months (plan question 7). Blank.")),
    ("kv", ("Office-paid cost", "Cost to serve an office-paid office (scenario B). Blank.")),
    ("kv", ("Mailing address", "A PO box or private mailbox for email footers and the LLC notice, only if you will not use a home address (legal pack, CAN-SPAM). Blank; Include = Y, so a quote flows in when typed.")),
    ("kv", ("Registered agent", "Only if the attorney confirms the Albany County route for the Articles (legal pack). Blank; Include = N.")),

    ("h", "Measurement honesty"),
    ("p", "The ladder stays in separate columns everywhere: delivered, placed, depleted, responded (tried is a survey answer), scanned, purchased (code redemptions). "
          "Incremental purchases are not measured, and the column says so. There is no field for sales lift, conversions or ROI."),

    ("h", "Google Sheets"),
    ("p", "Built to open in Google Sheets with formulas intact: no macros, scripts, data tables, array formulas, named ranges or add-ons. Every function used (38) appears in Google's "
          "Sheets function list (support.google.com/docs/table/25273, opened 2026-10-23 and 2026-10-24). Every INDEX over a single row names its row and column (INDEX(range, 1, column)), "
          "because Google documents INDEX's second argument as the row. Import: open a blank spreadsheet in Google Sheets, then File, Import, choose the .xlsx, "
          "'Replace spreadsheet', Import (support.google.com/docs/answer/40608, opened 2026-10-24). A live import was not possible from the build "
          "environment, so check after the first import (unverified, founder to confirm): the Dashboard says 'all integrity and data checks pass', Checks shows 0 failing, "
          "Scenarios!H10 shows 2 and Cash_Flow!C35 shows 13 (not #REF!)."),

    ("h", "Changelog"),
] + [("kv", (f"Round {i + 1}", line)) for i, line in enumerate([
    "Draft: built every tab on one shared drop engine; plan rows, hour table, capital table and steady state reproduce. The audit found one numeric literal (a '2' in the scenario pointer), a ROW() call, the company name inside a source quote, and a circular reference between the error scan and Dashboard cells that read Checks. All fixed; 28 of 28 checks pass.",
    "Pulled the legal pack's figures.csv (publication $1,745, attorney $400 and accountant $300, IT-204-LL $25, trademark out of the six months, two needs-quote insurance add-ons). Added office-fatigue warnings, change tracking on Scenarios and Schedule, overhead-not-absorbed and six-month all-in views, Gate 3 planned renewals counted by signature date, and tolerance cells instead of exact equality. Re-laid the Dashboard after a visual check.",
    "Moved offices and brands per drop onto Inputs and made the derived Schedule rows formulas of them (new offices backed out from the 12-office goal). Unsmoothed the cash chart, top-aligned every cell, blanked unused drop rows. Behaviour tests cover a SAMPLE actuals run through every gate.",
    "Final review: verified the last three functions (DATEVALUE, TIMEVALUE, FIND) on Google's Sheets list, made every plan-row tolerance the same, wrote HANDOFF, README and REPORT, and regenerated the CSV snapshots. Audit 0 literals; 28 of 28 checks; 54 of 54 tests.",
    "Independent review round 1 (2026-10-24): publication at the plan's high end ($2,000); break-even and a new Dashboard row follow Inputs; decision rule no longer says Stop while the switch test runs, with a warning that DRP-005 reports after the decision date; paste areas buffered and header-checked; all-in and week-26 cash shown with and without the decision-window drops, insurance expensed by month; Gate 3 renewals need a yes and count once; zero-brand drops recruit no offices; office-paid revenue left out until costed; timing defaults follow their gates; planning-estimate labels on every tab; clean CSV exports. Audit 0 literals; 34 of 34 checks; tests in _work/test_log.txt.",
    "Independent review round 2 (2026-10-24): every INDEX over one row now names row 1 and its column, and the audit fails any that does not (Google Sheets reads INDEX's second argument as the row); the Gate 3 rate cannot pass until every standard run dated by the review has actuals in, and the all-drops rate and pointer show how many drops with results due are missing; the six-month all-in rate counts hours logged outside a drop once they exceed the planned 45; Gate 1 counts a brand only once its payments reach the founding package price; budget-probe medians use one before-anchor answer per organisation (after-anchor answers marked after_1500); the storage unit starts with the first standard drop that runs; legal-pack update (mailbox and registered-agent lines, filing Thu 2026-11-19, attorney 11-18, accountant 11-20, insurance status plan estimate); Dashboard block with cash at each stop point; the README price text is live; break-even shows standard drops as well as brand campaigns; Cash_Ledger banner. Audit and tests in _work/audit_log.txt and _work/test_log.txt.",
    "Independent review round 3 (2026-10-24): Checks counts dates and amounts stored as text on every paste tab, and the Dashboard banner now names data failures; the trademark ($350) is in the six months at Gate 2, as the plan's setup checklist and the legal pack's 02:33 update time it (low point -$4,476 in week 13, capital to commit $5,476); the next scheduled drop is the earliest upcoming date, and drop rows out of date order are information, not a failure; levers a scenario does not name follow the plan base by formula, and scenario A grows the roster to 20; the stop-point block adds refunds owed and the net if you stop; the capital line counts unpriced lines; the renewal rate counts each brand once; a check flags week 1 moved on its own; polish (Drop_Actuals label, one import route, 'n/a' rates).",
])]
