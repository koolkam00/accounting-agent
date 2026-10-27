# Financial model for Desk Drop

## Context

Desk Drop is a pre-launch, solo-founder business in New York City. It sells emerging snack and beverage brands a measured placement inside a dense cluster of NYC offices, and gives those offices free, curated products through one contact. Nothing is signed, sold, formed or built yet.

The full plan is attached as plan.md. Read it first. Where this prompt is silent, the plan decides. Where the plan is silent, you decide and list the assumption.

Decided so far:
- Paying customer: emerging snack and beverage brands, roughly $500k to $10M in annual revenue, with a sampling or field-marketing budget and a named budget owner. A brand qualifies only if all seven hold: individually packaged, sealed and shelf-stable with 60 or more days of shelf life at delivery; labeled with ingredients and the nine major allergens; stocked in a retailer inside or within ten blocks of the cluster, or sold online with a discount code; able to ship 275 units to one Manhattan address within ten business days; carries product liability insurance; the contact can approve $600 alone; has a reason to want New York trial now. No alcohol, cannabis, supplements, refrigeration or health claims.
- Participating customer (no fee): offices with 40 to 250 people onsite on a Tuesday (hard floor 30; 30 to 39 is the founder's call), a named pantry owner who can say yes alone, inside one walkable cluster. First cluster: Flatiron, NoMad and Union Square, Manhattan. Firms under 500 employees preferred. Companies inside a coworking space are excluded; a coworking operator may join as one office only if it controls the pantry.
- End user: employees. No employee personal data is collected. The survey is anonymous.
- The product, an Office Placement Campaign: 5 offices (founding) or 10 (standard); about 50 units per office sized to Tuesday headcount; a 5 by 7 inch tent card with a QR code and the allergen line; placement within one business day of delivery; a five-business-day window; a placement photo and a depletion photo per office; a three-question employee survey; a one-page report within seven days; a 20-minute debrief.
- Price: founding (first three brands only) $600 for 5 offices, paid in full up front, locked for that brand's next two campaigns. Standard $1,500 for 10 offices ($150 per office), 50% at signature and 50% at placement confirmation. Extra office $150. Brands supply product plus 10% reserve and prepaid inbound freight. No free pilots.
- Offices commit to: placement within one business day, the two photos, one Slack or email post of the survey link, five or more survey responses, a ten-minute debrief, and their Tuesday headcount. Offices may veto any brand and leave on a week's notice.
- Positioning line for brands: "500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report."
- Pitch to offices: "Vetted emerging snacks and drinks, free, roughly monthly. You pick the categories and can veto anything. All we ask: on the shelf the day it arrives, one photo, and three questions for your team."
- Measurement honesty is a core value. Delivered, placed, depleted, tried, scanned, purchased and incremental are different things and are never blurred. Never claim guaranteed sales, customer acquisition or lift.
- Timeline: weeks 1 to 3 discovery (15 office and 15 brand conversations, no selling); weeks 3 to 7 sign five founding offices and two paying brands; weeks 7 to 9 campaign zero, founder-delivered; weeks 9 to 16 standard runs of 10 offices and 3 brands per drop; months 5 to 6 decide to scale, add an office-paid tier, or stop. Deliveries land Tuesday or Wednesday mornings, never Monday or Friday, never in the last two weeks of December, the week of July 4 or the last two weeks of August.
- Name: "Desk Drop" is a working name, not yet cleared. Keep it in one place in anything you build so a rename is one edit. Working tagline, may change: "Emerging brands. Delivered to your workday."
- Tone: plain, specific, honest, warm. Short sentences. No hype, no fake testimonials, no stock-photo gloss, no invented numbers. Natural office imagery.
- Money: bootstrapped. Software under $60 a month in total. Spend nothing without the founder's written yes; if a tool needs a paid plan, stop at the point of spend and state the cost.
- Access: you may not have logins for some tools. Build everything you can as files, specs and numbered setup steps, and list the few steps that need the founder's login. Mark anything you could not verify "unverified, founder to confirm." Placeholders for the founder's details look like [FOUNDER NAME], [PHONE], [EMAIL], [POSTAL ADDRESS].

Working style: you have creative freedom on everything this prompt does not fix. Make decisions and list assumptions rather than asking permission. Work in rounds: draft, critique your own work as the harshest expert in your field would, revise, repeat until you would put your name on it. Keep a one-line changelog per round. Ask the founder only questions that genuinely block you, batched at the end, each with your recommended default.

Facts for this workstream, all planning estimates from the plan's economics section: hard costs per ten-office drop are display kit $8 per office, transport $300 by courier ($25 to $40 a stop) or about $120 if the founder delivers, storage allocation $75, software allocation $30, insurance allocation $50, card processing 3% of revenue or zero by bank transfer. Founder hours per drop by activity (brand sales, office coordination, receiving and kitting, drop day, checks and pickup, reporting and debriefs, admin) are tabled in the plan for campaign zero, a one-brand drop, a three-brand drop and a three-brand direct-ship drop, totaling 57, 35, 52 and 45 hours. A brand win costs about 6 hours; a renewal about 2. Capital to the first six months is tabled at $3,360 to $6,510. Founding brands renew at the founding rate ($120 per office) for their next two campaigns. Gate thresholds: Gate 0 at week 3 (5 of 15 offices yes, 3 of 15 brands would pay $500 or more); Gate 1 at week 7 (5 signed offices with combined Tuesday headcount of 350 or more, 2 brands paid); Gate 2 at week 9 (80% placed within a day, 5 responses per office, report in 7 days, 1 brand would buy again); Gate 3 at week 16 (1 renewal at $1,500 and $50 or more contribution per founder hour). The decision rule: scale if 40% or more of brands renew; switch to office-paid if at least five offices named $100 a month or more and renewal is under 30% after two extra drops; stop if both fail.

## Your mission

Build the workbook the founder opens every week for six months to see whether the business is working: contribution per founder hour on each drop, the lowest point of cumulative cash, and which gate or scenario the real numbers point to. Done means one labeled input cell changes any assumption and every output moves, the plan's scenario figures reproduce within rounding, actuals drop in without rework, and a skeptical accountant would sign off.

## Must include

- An inputs tab with every assumption in a labeled cell with units and source: prices by tier, offices and brands per drop, every hard-cost line, hours by activity, close rate, renewal rate, payment terms and lags, processing toggle, startup cost lines with their timing, and the start date.
- An editable drop schedule (date, delivery model, offices, new offices, brands, renewals, tier). Where the plan gives a goal but no schedule, back out the simplest schedule that meets it and label the rows derived.
- Per-drop P&L for any tier, brand count, office count and delivery model, with contribution per founder hour.
- Monthly steady state and a six-month cash flow with startup outlays at their timing and brand cash on the plan's terms. Do not double count: the per-drop allocations for software, insurance and storage are views of the same monthly costs the cash flow pays once.
- Break-even: campaigns to recover startup cash, standard campaigns a month to cover overhead, and the volume at which contribution per hour crosses $50.
- Sensitivity tables on price per office, brands per drop and renewal rate, built in plain formulas.
- A hours-log tab by the seven activities that totals per drop and per week, fillable by hand or from a Toggl export.
- A pipeline tab for conversations, yeses, signed offices with headcount, brands paid, budget-probe answers and renewal answers, with dates.
- A gate dashboard showing every threshold beside its live value as pass, miss or not yet, the decision rule, and the gap to the $6,510 capital figure.
- Scenarios A to D from the plan's decision section as selectable assumption sets, with a README tab covering how to use the workbook, the assumptions, derived items and the changelog.

## Non-negotiables

- No numeric literal inside a formula except 0 and 1 for logic. Conversions like weeks per month live in input cells.
- Defaults are the plan's figures. For a range, use the plan's working figure where it gives one, otherwise the high end of a cost range or the low end of a revenue range, and show both ends. A figure the plan does not have stays blank and flagged "needs quote". Never invent a number.
- Every default is labeled a planning estimate, never a forecast.
- The measurement ladder stays in separate columns. No field for sales lift.
- Works in Google Sheets with formulas intact. No scripts, macros or paid add-ons.
- The company name sits in one cell.

## Your freedom

- Tab structure, names, layout, charts, how scenarios switch, how sensitivities are built, weekly or monthly cash flow, how shared drop costs split across brands (state it in the README), and any extra output that traces to inputs.

## Quality bar and iteration

Build the whole workbook, then audit it as a CFO who has seen a hundred founder models and as a spreadsheet auditor hunting hidden constants. Check that the plan's five scenario rows reproduce, every output traces to an input, no monthly cost is counted twice, each sensitivity moves the right way, edge cases behave (zero brands, one office, 100% renewal), a Google Sheets import shows no broken formulas, and a founder with no finance training can change the price and read the result in under a minute. Fix, log, repeat until a pass finds nothing you would be embarrassed by.

## Deliverables

One workbook named "Desk Drop financial model v1" as .xlsx that opens in Google Sheets with formulas intact, with the README tab inside it, shared where the founder names or attached to your reply.

## Handoffs

- Needs from "Operations and measurement system": per-campaign actuals. Publish the column layout you expect so it builds to it.
- Needs from "Outreach engine": pipeline counts. Same.
- Needs from "Legal and admin pack": formation, publication and insurance figures as they are verified.
- Feeds nothing; the founder reads it.

## Report back

One message: what was built in five lines; how to use it in five lines; numbered assumptions and derived items; the changelog; blocking questions batched last with your recommended default for each.