# Operations and measurement system for Desk Drop

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

Facts for this workstream: the plan's Phase 3 section has the campaign calendar from T minus 10 to T plus 10, the per-stop procedure, the kit, the exceptions table and the Gate 2 test (80% of units placed within one business day, five or more responses per office, report within seven days, one brand says it would buy again). The measurement section has the ladder with how each rung is captured, the survey questions, the report layout and the founder's own operating metrics. The delivery model changes over time: campaign zero is founder-carried; campaigns one and two add a courier or rented van; from campaign three brands ship direct to offices or to one consolidation point and the founder coordinates and verifies. The system must work for all three.

## Your mission

Build the operating system the founder runs campaign zero on and keeps through the standard runs. Done means a briefed stranger could run a ten-stop drop from the sheet and the kit, every number in the brand report traces to a logged row or a photo, and contribution per founder hour for a campaign is readable the day after the drop without retyping anything.

## Must include

- Office intake and brand qualification forms that feed the tracker.
- A campaign tracker that relates drops, campaigns, brands, offices, approvals, stops, units received, allocated, placed, topped up and remaining, photos, timestamps, responses, scans, redemptions and issues.
- The kit checklist and a drop-day route sheet with receiving windows and owner phone numbers.
- A QR and short-link scheme with one link per office per campaign and tracking parameters, with a worked example.
- The three-question anonymous survey with the office captured automatically from the link, and a response dashboard.
- A one-page report generator that fills the plan's layout from the tracker.
- A founder hours log by the plan's seven activities, with cost per stop and contribution per hour per campaign.
- Invoice and payment flow by bank transfer, with a payment-received step that releases the ship date.
- Debrief note templates for brands and offices.
- A written SOP covering T minus 10 to T plus 30 (the day-30 redemption check), for each of the three delivery models.
- A numbered setup runbook marking the steps that need the founder's login.

## Non-negotiables

- No personal data about employees except the survey's optional email with its unchecked consent box. Decide and document where consented emails live, how they pass to the brand once, and when they are deleted.
- The ladder's rungs stay separate everywhere. No field called conversions or sales lift.
- Sample data is unmistakable: every sample ID and text starts with SAMPLE, and every output built on it carries a SAMPLE banner. Invent no real results, offices, brands or quotes.
- The SOP cannot produce a Monday, Friday or blackout-week drop date.
- Free or near-free tools inside the $60 a month total.
- The company name sits in one configuration cell and never in a file, folder or link name, so a rename is one edit.

## Your freedom

- The tools (Sheets or Airtable, Forms or Tally, a link shortener as the QR source, Wave, an e-signature free tier, Toggl, or equivalents), the generator mechanics, the dashboard shape, how costs split across brands in a shared drop, and how much automation to add. Prefer what a solo founder can repair at 7 am on drop day.

## Quality bar and iteration

Build end to end, then dry-run campaign zero with SAMPLE data for two brands and five offices through every day of the calendar: fill every form, follow every link, generate both reports, log hours, issue both invoices. Repeat for ten offices and three brands. Critique as four people: a Manhattan sampling operations lead reading the route sheet cold; a brand finance lead hunting overstatement; a privacy reviewer hunting data that should not exist; a pantry owner weighing every ask. Fix, log, repeat. Stop when the report generates with no retyping, every QR resolves to the right survey for the right office, the route sheet raises no questions, and you would sign your name.

## Deliverables

One folder: the tracker and hours log; forms and survey, live or import-ready; the QR scheme with a worked example; the report generator and one SAMPLE output; invoice and debrief templates; the SOP; the setup runbook; a README listing every file in the order a campaign touches them.

## Handoffs

- Needs from "Website": the intake forms, or give that workstream your field spec and build provisional forms.
- Needs from "Brand identity and collateral": the report, tent card and case label layouts; use plain provisional layouts until then.
- Needs from "Outreach engine": signed offices and paid brands. Define the fields they must pass to you.
- Needs from "Legal and admin pack": the agreements and the survey privacy notice. Leave placeholders.
- Feeds "Financial model": per-campaign actuals (hours by activity, hard costs, placement, responses, scans, redemptions, revenue) in an importable layout you publish.

## Report back

One message: what you built and where; what the dry runs and the four critics found; the changelog; numbered assumptions; the handoff fields other workstreams must match; blocking questions batched last with your recommended default for each.