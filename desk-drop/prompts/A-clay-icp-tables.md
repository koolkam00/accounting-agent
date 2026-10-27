# Clay ICP tables for Desk Drop

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

Facts for this workstream: office titles to find are Office Manager, Workplace Experience Manager, Head of Workplace, People Operations, and Executive Assistant to the CEO. Brand seed sources are the Startup CPG community (no cold selling inside it), the local and emerging shelves at Whole Foods Union Square, Trader Joe's on 14th Street and Eataly Flatiron, Summer Fancy Food Show exhibitors, New York CPG trade press, LinkedIn and Instagram. New York brands come first.

## Your mission

Build two Clay tables, Offices and Brands, that hand the founder ten outreach-ready targets every morning from a 15-minute routine, with no research left to do at send time. Done means 200 office candidates scored to a top 50, 200 brand candidates scored to a top 60, every score explainable in one sentence, a daily view per table exported to Google Sheets, and a written routine a stranger could run.

## Must include

- Offices table: company, website, industry, employee count, LinkedIn URL, office address with the source that places it in the cluster, lobby type if findable, attendance signals (hybrid policy posts, job listings saying "in office"), a Tuesday onsite estimate with its basis, labeled as an estimate until intake replaces it. Hard gates, applied before any enrichment spend: outside the cluster, estimate under 30 or over 250, a company inside a coworking space. Weighted score on the rest: onsite band, company size under 500, attendance signals, title match, a "known to founder" flag. One primary and one backup contact per company.
- Brands table: brand, website, HQ city, category, funding stage, shelf-stable flag, online store yes or no, revenue band with basis or "unknown". Retailers within ten blocks of the cluster, each graded: seen on shelf by the founder, retailer website with store selector, or brand claim only. Hard gates: excluded category, an explicit health claim, not shelf-stable, and no retailer within ten blocks plus no online store. A founder-review flag for borderline cases. Founder and marketing lead contacts. A why-now signal with a link and date. A Startup CPG member flag where public.
- Verified work email through a waterfall only for the top 50 offices and top 60 brands; below that, a LinkedIn URL and channel set to LinkedIn. Report the verified share.
- On both tables: source and date found per row, channel, a status column that includes do-not-contact, and a daily view of the ten highest-scored uncontacted companies with one contact each, never two people from one company in flight.
- A column dictionary, the scoring logic in plain words, and the 15-minute daily routine.

## Non-negotiables

- Business contact data only. No personal emails or phones, nothing about employees.
- Invent nothing. A field you cannot confirm says "unknown". A source you cannot open is marked "unverified, founder to confirm", never verified.
- Status lives in these tables and nowhere else. An opt-out from outreach becomes do-not-contact here and never reappears in a daily view.
- Credits and plans: use what the founder's Clay account already allows. The moment a step needs a paid plan or more credits, stop and state the cost. Do not run paid enrichment on rows that have not passed the hard gates.

## Your freedom

- Table structure, column names, title variants, score weights, enrichment providers in the waterfall, research prompt wording, deduplication, tie-breaking, refresh cadence, and how the daily view is built.
- If Clay is not available to you, deliver seed CSVs, a column dictionary, the formulas and the research prompts as a build sheet the founder can import in 30 minutes, and say so.

## Quality bar and iteration

Each round, hand-check ten rows per table: open every source, confirm the address sits in the cluster, confirm titles, gates and evidence grades. Count errors as fields wrong over fields checked. Critique the tables as the most demanding outbound operator you know, then fix. Stop when two consecutive rounds show no fabricated field and under ten percent error, and the daily routine runs in about 15 minutes.

## Deliverables

1. The two tables in Clay, shared with the account the founder names, and the Google Sheets export with both daily views.
2. One short document: hard gates and scoring, column dictionary, daily routine, seeding and refresh method, running cost.
3. The spot-check log by round.

## Handoffs

- Receives from "Cluster map and seed lists": the cluster boundary, 100 candidate companies, coworking operators and the retailer list. If it is not ready, use a provisional boundary of roughly 14th to 30th Street between Sixth Avenue and Park Avenue South, record it, mark it swappable, and source offices yourself.
- Feeds "Outreach engine": both daily views and the column dictionary, with stable personalization columns (first name, company, nearest stocked retailer with its evidence grade, onsite band, why-now, and the known, Startup CPG and do-not-contact flags). The outreach workstream adds its conversation-tracking columns to these tables rather than keeping a second status store.

## Report back

One message: what you built and where; counts (found, passed gates, top 50 and top 60, verified emails and share); spot-check error rate per round; credits used and running cost; numbered assumptions; the changelog; blocking questions batched last, each with your recommended default. The first blocking question is almost certainly which Google and Clay accounts to share with.