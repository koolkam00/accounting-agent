# Copy deck

Version 1.0 · 2026-10-24 · Workstream C (website)

Every word on the site, page by page, and where each claim comes from. **The pages are the one place copy is edited** (`site/*.html`, plus the few values in `site/site.config.js`). Part 2 below is regenerated from the pages by `python3 tools/export_copy.py`, so this deck cannot drift from the site. Part 1 is written by hand: update it when you change a claim.

Voice: plain, specific, honest, warm. Short sentences. "We" for the business. No hype, no testimonials, no logos, no invented numbers, no dates in copy.

## Part 1. Claims ledger

Each claim on the site and what backs it. "Prompt" is `prompts/C-website.md`, "Decided so far". "G 10" is `desk-drop-legal-pack/10-brand-campaign-agreement.md` (version 0.7, draft for attorney review); "G 03" is the office participation agreement; "G 13" the survey notice. If the attorney changes G 10 or G 03, change the matching line on the site.

| # | Claim on the site | Page | Source |
| --- | --- | --- | --- |
| 1 | "500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report." (word for word) | brands H1, home | Prompt; plan "The revised model" |
| 2 | "Vetted emerging snacks and drinks, free, roughly monthly. You pick the categories and can veto anything. All we ask: on the shelf the day it arrives, one photo, and three questions for your team." (word for word) | offices hero | Prompt |
| 3 | Founding: $600 for 5 offices, first three brands only, paid in full up front, price locked for the next two campaigns | brands price, home | Prompt |
| 4 | The lock is "$120 per office" | brands price | G 10 section 3 and its choice 3 (up to 10 offices). Matches D's `dd-offer.js` and H's model |
| 5 | Founding brands give a short honest statement and case-study rights if everything promised is delivered | brands price | Plan price table; G 10 section 3. Disclosed so no founding term is hidden |
| 6 | Standard: $1,500 for 10 offices ($150 per office), 50% at signature, 50% at placement confirmation | brands price, home | Prompt |
| 7 | Placement confirmation = "our email, by the day after the drop, listing each office where your product was placed, with its photo" | brands price | G 10 section 3 (v0.7 definition, T+1) |
| 8 | Extra office $150, same terms | brands price | Prompt; plan price table |
| 9 | "No free pilots." "The founding price is the trial." | brands price, FAQ | Prompt; plan objection table |
| 10 | Brand supplies product plus 10% reserve and prepaid inbound freight; allergen sheet; product liability certificate, $1M or more, naming us as additional insured; code or landing page; logo and two sentences | brands | Prompt; plan "Brand supplies", legal table; G 11 |
| 11 | 5 or 10 offices in one cluster; no competing product in the same drop | brands | Prompt; plan "What brands buy" (category exclusivity) |
| 12 | About 50 units per office, sized to Tuesday headcount | brands | Prompt |
| 13 | On the shelf within one business day, at eye level, with the card | brands | Prompt; plan per-stop procedure (placement standard) |
| 14 | Five-business-day window starting Tuesday or Wednesday | brands, home | Prompt; CONTRACTS section 3 |
| 15 | Two photos per office: placement on drop day, second on day 3 or 5 | brands, offices | Prompt; plan "What brands buy" |
| 16 | Each office commits to one post of the survey link and five or more responses; "we report the real number" | brands, offices | Prompt (office commitments). Not a promise to the brand |
| 17 | One-page report "within seven business days of the drop" | brands | CONTRACTS section 3 (report at T+7 business days). The prompt says "within seven days"; business days is the stricter reading the calendar supports (assumption 3) |
| 18 | 20-minute debrief | brands | Prompt |
| 19 | The report's eight parts | brands | Plan "The report, one page per campaign" |
| 20 | The seven ladder rungs, each with method and limit; "A scan is never reported as a sale, and we do not claim lift"; incremental not measured | brands, home | CONTRACTS section 2 (ladder words); plan measurement table |
| 21 | Exposure as a range; retailer sales only if the brand's data allows, "suggestive only" | brands | Plan measurement table |
| 22 | Timeline: ship T−10, count and check T−5, drop day, day 3 photo and top-up, day 5 close, report T+7, debrief | brands | Plan campaign calendar; CONTRACTS section 3 |
| 23 | Leftovers returned at the brand's cost or released to the office, as elected at signing | brands | Plan appendix F clause 10; G 10 section 9 |
| 24 | Late product: not arrived by T−3, the drop moves one week and every office hears the same day | brands | Plan "When things go wrong"; G 10 section 8 |
| 25 | Office not placed by the day after the drop: off the invoice or its share refunded, unless replaced | brands FAQ | G 10 section 8 (v0.7). Not in the plan: attorney to confirm (assumption 8) |
| 26 | Cancel by email: before the ship-by date (T−10) full refund less $100; after that 50% kept | brands FAQ | Plan appendix F clause 9; G 10 section 8 and its choice 1 (ten business days) |
| 27 | Each office sees the brand first and can say no; first three drops need a yes, then opt-out | brands, offices, home | Plan "How a campaign runs" step 3; G 03 section 2 |
| 28 | The seven qualification checks | brands fit and form | Prompt |
| 29 | Not for: alcohol; cannabis, CBD or THC; supplements (Supplement Facts panel); refrigerated, perishable or needing preparation; health claims ("supports gut health" is one; "10g protein" is not but is reviewed) | brands, offices | Prompt; CONTRACTS section 4 |
| 30 | Store map and list (16 stores, numbers as on B's map), "not an endorsement", researched 2026-10-24 | brands, offices | `cluster-1-flatiron/map-public.geojson` (as_of 2026-10-24) and B's footnote in `cluster-1-flatiron/HANDOFF.md` |
| 31 | Cluster: about 14th to 30th Street, Sixth Avenue to Park Avenue South, plus the blocks around Union Square | brands, offices | B's boundary (`cluster-1-flatiron/HANDOFF.md`, suggested alt text) |
| 32 | Card: brand name, two sentences, allergen statement word for word, nearest store or code, QR unique per office; card text sent for approval before printing | brands | Plan kit and appendix G; G 10 section 1; D's tent card |
| 33 | No employee personal data; anonymous survey; newsletter only through an unticked box, under the brand's policy | brands FAQ, offices | Prompt; plan "Privacy"; G 13 Part B |
| 34 | Offices with about 40 to 250 people in on a Tuesday; pantry owner who can say yes alone; coworking rule | brands FAQ, offices | Prompt |
| 35 | Proposal lists offices by neighborhood, industry and Tuesday headcount; names after the brand signs | brands FAQ, offices notice, privacy | Plan "The proposal"; G 10 section 13 |
| 36 | One to three brands per drop, never two in the same category | brands FAQ | Plan "Operating unit"; plan "What brands buy" |
| 37 | Sealed cases, room temperature, clean, dry; never opened, repacked or relabeled | brands FAQ | Plan "Storage" and legal table "Food handling scope"; G 10 section 5 |
| 38 | Offices get and give; never asked: payment, employee contact details, exclusivity, storage | offices | Prompt; plan "What offices get and give" |
| 39 | Veto on any brand, category or allergen; labels checked against vetoes | offices | G 03 section 2 |
| 40 | Leave any time with a week's notice; one-page agreement; no fees either way, no penalties | offices | Prompt; plan Phase 1 "What they sign"; G 03 |
| 41 | "Vetted" means: sealed, shelf-stable, 60+ days, labeled, insured, not excluded | offices | Prompt (the seven checks) |
| 42 | Founding offices: on the roster only if they say yes; veto and profile; feedback summary; leave on a week's notice | offices | Plan "The founding-office offer" (its "first drop within four weeks" is left out, per G's calendar conflict note) |
| 43 | "Offices get vetted products free, roughly monthly as supply allows" | home | Plan "What offices get" and risk table (never promise a cadence) |
| 44 | "We are signing our founding offices now. No campaign has run yet, so there are no results to show." | home, brands (`ROSTER_STATUS`) | True on 2026-10-24 (nothing signed). The founder updates it in `site.config.js` |
| 45 | Office form "About 90 seconds" | offices | QA.md, P9 estimate |
| 46 | What each form collects and why; Google Sheet plus one email; seen only by the founder; deleted within 12 months if nothing proceeds | both form notices, privacy | Draft for attorney review. Retention period is this workstream's default (assumption 9) |
| 47 | GoatCounter: no cookies, no IP addresses stored, a random code that cannot be traced back; totals only; Do Not Track and Global Privacy Control respected | privacy | goatcounter.com home, /help/sessions and /help/gdpr, opened 2026-10-24; DNT handling is the site's own code |
| 48 | Survey privacy notice | survey-privacy | G 13 Part C, version 0.5, word for word (checked by `tests/check_site.py`) |

**Deliberately not on the site:** testimonials, logos, "trusted by", results, case studies, any number not in the table above, the revenue band of target brands, any date (the drop dates in CONTRACTS section 3 are still "derived, founder to confirm"), a first-drop timing promise to offices, and anything implying sales, lift, acquisition or conversion.

## Part 2. The deck, page by page

<!-- GENERATED:START -->
Generated by `tools/export_copy.py` from `site/*.html` and `site/site.config.js`. Do not edit here; edit the page, then re-run the script.

### Values from site.config.js

| Key | Value |
| --- | --- |
| `BRAND_NAME` | Desk Drop |
| `TAGLINE` | Emerging brands. Delivered to your workday. |
| `ROSTER_STATUS` | We are signing our founding offices now. No campaign has run yet, so there are no results to show. |
| `CONTACT_EMAIL` | [EMAIL] |
| `POSTAL_ADDRESS` | [POSTAL ADDRESS] |
| `FOUNDER_NAME` | [FOUNDER NAME] |
| `COMPANY_LEGAL_NAME` | [COMPANY NAME] |
| `DOMAIN` | [DOMAIN] |

### On every page

- Staging bar (only while STAGING is true): Staging preview, not public. The name is a working name and not yet cleared.
- Header: {BRAND_NAME}, links For brands, For offices
- Footer: {BRAND_NAME}, {TAGLINE}; For brands, For offices, Privacy, Survey privacy notice; Email: {CONTACT_EMAIL}; Mail: {POSTAL_ADDRESS}

---

### Page: Home (`site/index.html`)

Page title: Emerging snacks for New York offices
Meta description: Emerging snack and drink brands, placed in New York offices around Flatiron, NoMad and Union Square. Free for offices. Brands get photos, an anonymous survey and a one-page report.
Flatiron · NoMad · Union Square
# Emerging snack and drink brands, on the shelf in New York offices.
Offices get vetted products free, roughly monthly as supply allows. Brands pay for a placement we measure: photos, an anonymous three-question survey and a one-page report that says what happened, and what we could not measure.
## Who this is for
For brands
### 500 units into 10 offices in one week
Within walking distance of the stores that carry you, with photos, feedback and a report. $1,500 for 10 offices. Founding price $600 for 5 offices, first three brands only.
How a campaign works
For offices
### Free snacks and drinks, roughly monthly
You pick the categories and can veto anything. All we ask: on the shelf the day it arrives, one photo, and three questions for your team.
What offices give and get
## Where things stand
{ROSTER_STATUS}
## How it works
### Offices sign up
An office tells us its Tuesday headcount, the categories it wants and anything it never wants.
### A brand books a campaign
Each office sees the brand first and can say no.
### Drop day
On a Tuesday or Wednesday morning the product goes on the pantry shelf with a display card, and the office sends a photo.
### The report
After a five-business-day window, the brand gets a one-page report and each office gets its team's feedback.
## What we count, and what we don't
Delivered, placed, depleted, responded, scanned, purchased. Each is counted on its own, with how we know it. Incremental purchases are not measured, and the report says so.
See the measurement ladder

---

### Page: For brands (`site/brands.html`)

Page title: For brands: office placement campaigns in New York
Meta description: 500 units into 10 New York offices in one week, near the stores that carry you, with photos, an anonymous survey and a one-page report. $1,500 for 10 offices. No sales guarantee, no free pilots.
For emerging snack and drink brands
# 500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report.
Trial here, buy there, measured. We place your product in offices that signed up to receive it, around Flatiron, NoMad and Union Square. Then we report what happened, rung by rung, and what we could not measure.
Check fit and apply See the price
- 5 or 10 offices in one walkable cluster
- About 50 units per office
- 5 days on the shelf, counted in business days
- 1 page report within 7 business days
Where things stand: {ROSTER_STATUS}
## What a campaign includes
- 5 offices (founding) or 10 offices (standard), all in one walkable cluster. No other brand in your category in the same drop.
- About 50 units per office, sized to that office's Tuesday headcount. You ship 10% extra as a reserve for top-ups.
- On the shelf within one business day of delivery, at eye level, with a display card: your two sentences, your allergen statement word for word, where to buy you nearby, and a QR code for each office.
- A five-business-day window, starting on a Tuesday or Wednesday morning.
- Two photos per office: the placement on drop day, and a second on day 3 or day 5.
- An anonymous three-question survey for each office's team. Each office commits to posting the link once and to five or more responses. We report the real number, office by office.
- A one-page report within seven business days of the drop, and a 20-minute debrief.
- One contact for the whole campaign.
## Price
Founding · first three brands only
$600
for 5 offices ($120 per office)
- Paid in full up front.
- Price locked for your next two campaigns, at $120 per office.
- If we deliver everything promised, you give us a short, honest written statement and let us publish a case study from your report.
Standard
$1,500
for 10 offices ($150 per office)
- 50% at signature.
- 50% at placement confirmation: our email, by the day after the drop, listing each office where your product was placed, with its photo.
Extra office
$150
per office
- Same terms as the campaign it joins.
No free pilots. The founding price is the trial. On top of the price, you supply the product plus a 10% reserve, with inbound freight prepaid.
### What you send
- The units plus the 10% reserve, freight prepaid, to one Manhattan address.
- An ingredient and allergen sheet.
- A certificate of product liability insurance, $1M or more, naming us as additional insured.
- A discount code or a landing page for the QR code.
- Your logo, and two sentences about the brand for the card.
### What we never promise
Sales, lift or new customers. We commit to the work: placement within one business day, the photos, the survey, the report and the debrief. Results are reported as we observe them.
## What the report contains
One page, as a PDF, within seven business days of the drop.
- Header: your brand and product, the cluster, the drop date and the window.
- Roster: each office by industry and headcount band, with units placed, units gone by day 5, and survey responses.
- Evidence: two photos per office, at placement and on day 3 or 5.
- Survey: the number of responses, how many tried it, the average rating, how many would buy, and three comments word for word.
- Engagement: QR scans by office, and code redemptions to date.
- What we learned: three points, including anything to change, such as flavor, size or card copy.
- Recommendation: renew into which offices, adjust what, or stop.
- Limitations: the same plain paragraph, every time.
Caption: Layout of the one-page report. Brackets mark where your numbers go. Illustrative placeholders, not results.
## What we count, and what we don't
This is why you can trust the report. Each rung is counted on its own, with how we know it and what it cannot tell you. A scan is never reported as a sale, and we do not claim lift.
### Delivered
Counted at handoff, at each office.
Limit: none.
### Placed
The placement photo, card in view, with a count of the units you can see.
Limit: the pantry owner may hold some back for later.
### Depleted
Counts from photos or from the pantry owner on day 3 and day 5.
Limit: one person may take several; sharing and disposal are invisible.
### Responded
Answers to the anonymous three-question survey. "Tried it" is one of the answers.
Limit: self-selected, small samples.
### Scanned
One QR code per office, so scans are counted office by office.
Limit: a scan is curiosity, not intent.
### Purchased
Redemptions of your campaign code, which you report to us at day 30.
Limit: some would have bought anyway.
### Incremental
Not measured. We say so in writing, in every report.
Two more numbers appear when they exist. Exposure: each office's Tuesday headcount, as a range, because not everyone visits the pantry. Retailer sales: if your distributor or data provider can pull store-level sales for the nearest store two weeks before and after, we add them, marked as suggestive only.
## How a campaign runs
- Before anything shipsEach office on the route sees your brand first and can say no. You sign, pay, and approve the card text.
- 10 business days before the dropYou ship the units plus the 10% reserve, freight prepaid, to one Manhattan address.
- 5 business days beforeWe count every case and check best-by dates, lot numbers and damage. Any shortfall goes to you the same day.
- Drop day, Tuesday or Wednesday morningOne labeled case per office, on the shelf within one business day, photographed with the card in view.
- Day 3A second photo. We top up from your reserve where the shelf has run out.
- Day 5The window and the survey close. Leftovers come back to you at your cost, or stay with the office, as you chose when you signed.
- Within 7 business days of the dropYour one-page report, then a 20-minute debrief.
If your product is late: if it has not arrived three business days before the drop, the drop moves one week, and every office hears the same day.
## You fit if all seven are true
- Individually packaged, sealed and shelf-stable, with 60 or more days of shelf life left at delivery.
- Labeled with ingredients and the nine major allergens.
- Sold in a store inside or within ten blocks of the cluster, or online with a discount code.
- Able to ship 275 units to one Manhattan address within ten business days.
- Covered by product liability insurance.
- The person we talk to can approve $600 alone.
- A reason to want New York trial now: a new store, a launch, a local push.
### Not for
- Alcohol.
- Cannabis, CBD or THC.
- Dietary supplements: anything with a Supplement Facts panel.
- Anything refrigerated or perishable, or that needs preparation.
- Products that make health claims. "Supports gut health" is a health claim. "10g protein" is not, though we read it before saying yes.
## Trial here, buy there
The cluster runs from about 14th to 30th Street, between Sixth Avenue and Park Avenue South, plus the blocks around Union Square. These natural and specialty food stores are inside it or within about ten blocks. The card on the shelf names the store nearest the office that carries you, or your code.
- Office cluster
- Grocer with a documented natural, local or emerging set
- Specialty, gourmet or natural-format market
### Grocers with a documented natural, local or emerging set
- 1.LifeThyme Natural Market410 Sixth Avenue · 5 blocks outside
- 2.Wegmans Astor Place770 Broadway · 4 blocks outside
- 3.Whole Foods Market Union Square4 Union Square South · inside the cluster
- 4.Whole Foods Market Chelsea250 Seventh Avenue · 4 blocks outside
- 5.Whole Foods Market NoMad63 Madison Avenue · inside the cluster
### Specialty, gourmet or natural-format markets
- 6.Citarella Greenwich Village424 Sixth Avenue · 4 blocks outside
- 7.Westside Market NYC (84 Third Ave)84 Third Avenue · 1 block outside
- 8.Merci Market Union Square59 Fifth Avenue · 1 block outside
- 9.Westside Market NYC (77 Seventh Ave)77 Seventh Avenue · 2 blocks outside
- 10.Westside Market NYC (180 Third Ave)180 Third Avenue · 2 blocks outside
- 11.Wholesome Organic Market343 Second Avenue · 6 blocks outside
- 12.Eden Gourmet Marketplace Gramercy Park275 Third Avenue · 4 blocks outside
- 13.Westside Market NYC (170 West 23rd St)170 West 23rd Street · 2 blocks outside
- 14.Eataly NYC Flatiron200 Fifth Avenue · inside the cluster
- 15.Fairway Market Chelsea766 Sixth Avenue · inside the cluster
- 16.Fairway Market Kips Bay550 Second Avenue · 7 blocks outside
Store list researched on 2026-10-24 from each store's own website and the New York State retail food store license list. A store on this map is not an endorsement, and being on it does not mean the store carries any particular brand. Streets and parks: NYC Street Centerline and NYC Parks Properties, NYC Open Data.
Open the map full size
## What the card on the shelf says
A 5 by 7 inch tent card stands in front of your product. It carries your brand name, your two sentences, your allergen statement copied word for word from the package, the nearest store or your code, and a QR code unique to each office, so scans are counted office by office.
We send you the card text to approve before anything is printed.
Caption: Layout of the card. Brackets mark where your details go. The QR pattern here is a drawing, not a working code.
Photo slot: a printed card on a real pantry shelf, no people in frame. Founder to add after the first test print (SETUP.md, section 6).
## Straight answers
**Q:** Can we run a free trial first?
A: No. We don't run free pilots. The founding price is the trial, and it stays locked for your next two campaigns.
**Q:** Do you guarantee sales?
A: No. We commit to the work, and we report what we observe. Nothing in the report is counted as a sale unless it is a redemption of your code, and even then some of those people would have bought anyway.
**Q:** Can we have the employees' emails?
A: No. We collect no personal data about employees, and the survey is anonymous. If you choose, the survey can offer your newsletter: anyone who ticks an unticked box is passed to you, under your own privacy policy.
**Q:** Which offices?
A: Offices with about 40 to 250 people in on a Tuesday, each with a pantry owner who can say yes alone. The proposal lists them by neighborhood, industry and Tuesday headcount. You get the office names once you sign.
**Q:** What if an office does not place it?
A: An office that has not placed your product by the day after the drop comes off your invoice, or its share is refunded ($150, or $120 at the founding price), unless we can replace it with another office on the roster.
**Q:** Can we cancel?
A: Yes, by email. Before the ship-by date, 10 business days before the drop: a full refund less $100. After that, we keep 50%. If your product is late, the drop moves one week at no charge.
**Q:** Who else is in the drop?
A: One to three brands per drop, and never two in the same category.
**Q:** How is the product handled?
A: Sealed cases only, kept at room temperature, clean and dry. We never open, repack or relabel anything.
The full terms are in a short campaign agreement, which you see before you pay.
## Check fit and apply
23 questions, 19 of them required, 11 of them one tap. A no on any of the seven checks is useful to know, so answer as things are today.
Staging: submissions are not live yet. This form sends nothing.
### Please check these answers
Field group / question: Your brand
Label: Brand name
Label: Brand website
For example: yourbrand.com
Label: Product for the campaign
One product, or two flavors treated as one. For example: Sea Salt Lentil Crisps, 1 oz bag.
Label: Category
Option: Choose one
Option: Chips and crisps
Option: Popcorn and puffs
Option: Crackers and pretzels
Option: Bars
Option: Cookies and baked snacks
Option: Chocolate and candy
Option: Nuts, seeds and trail mix
Option: Jerky and meat sticks, shelf-stable only
Option: Dried fruit and fruit snacks
Option: Sparkling water and soda
Option: Tea, juice and other non-carbonated drinks, shelf-stable
Option: Ready-to-drink coffee, shelf-stable
Option: Another kind of snack
Option: Another kind of drink
Label: Where is the brand based?
City and state.
Field group / question: You
Label: Your name
Label: Your title
Label: Work email
Label: Work phone (optional)
Field group / question: Who signs off on the budget?
Label: I do
Label: Someone else
Label: Their name and title
Field group / question: Where people can buy it
Label: New York stores that carry you (optional)
Store name and street, one per line.
Label: Online store (optional)
Field group / question: Can you issue a discount code for the campaign?
Label: Yes
Label: No
Field group / question: When would you want a campaign?
Label: Next available drop
Label: In 1 to 3 months
Label: In 3 to 6 months
Label: Just exploring
Field group / question: The seven checks
Field group / question: 1. Individually packaged, sealed and shelf-stable, with 60 or more days of shelf life left at delivery?
Label: Yes
Label: No
Label: Not sure
Field group / question: 2. Labeled with ingredients and the nine major allergens?
Label: Yes
Label: No
Label: Not sure
Field group / question: 3. Sold in a store inside or within ten blocks of the cluster, or online with a discount code?
Label: Yes
Label: No
Label: Not sure
Field group / question: 4. Able to ship 275 units to one Manhattan address within ten business days?
Label: Yes
Label: No
Label: Not sure
Field group / question: 5. Covered by product liability insurance?
Label: Yes
Label: No
Label: Not sure
Field group / question: 6. Can you approve $600 on your own, without a committee?
Label: Yes
Label: No
Label: Not sure
Label: 7. Why New York, and why now?
One line is enough: a new store, a launch, a local push.
Field group / question: Not an excluded product
Label: My product is none of these: alcohol; cannabis, CBD or THC; a dietary supplement; refrigerated or perishable; needs preparation; makes health claims.
Field group / question: Anything else
Label: Notes (optional)
Button: Send my application
### Thanks. We have your answers.
Next step: a 20-minute call about your timing and the offices on the next route. We will email you from {CONTACT_EMAIL} to set it up. No campaign starts until there is a signed agreement and payment.
Draft for attorney review. Not legal advice.
### What this form collects, and why
Your business contact details, so we can reply and send a proposal. Your brand, product, stores, timing, who approves the budget and your answers to the seven checks, so we can tell whether a campaign fits. Nothing about anyone's employees or customers.
Your answers go to a private Google Sheet and one email to our inbox, seen only by {FOUNDER_NAME}. We do not sell them. Offices see your brand and product when we propose your campaign to them, so they can approve it. If we do not end up working together, we delete your answers within 12 months. To see, correct or delete them, email {CONTACT_EMAIL}. More in our privacy notice.

---

### Page: For offices (`site/offices.html`)

Page title: For offices: free emerging snacks and drinks
Meta description: Vetted emerging snacks and drinks for offices around Flatiron, NoMad and Union Square, free, roughly monthly. You pick the categories and can veto anything.
For office and workplace managers
# Vetted emerging snacks and drinks, free, roughly monthly.
You pick the categories and can veto anything. All we ask: on the shelf the day it arrives, one photo, and three questions for your team.
Sign up your office About 90 seconds. No fees, either way.
For offices around Flatiron, NoMad and Union Square with about 40 to 250 people in on a Tuesday.
## What you get and what we ask
### What you get
- One to three vetted emerging brands per drop, free, roughly monthly as supply allows.
- Only the categories you choose, and a veto on any brand, category or allergen. We check each label against your vetoes before offering a brand.
- One contact. Deliveries on Tuesday or Wednesday mornings, in your receiving window.
- A display card, so your team knows what it is and what is in it.
- Your team's feedback, summarized for you after each drop.
### What we ask
- A named pantry owner and a receiving window.
- On the shelf within one business day of delivery.
- One placement photo, then one more on day 3 or 5.
- One Slack or email post of the survey link, and five or more responses.
- A ten-minute debrief, and your Tuesday headcount.
Never asked of you: payment, your employees' contact details, exclusivity, or storing anything beyond the drop. Leave any time with a week's notice.
## How a drop works
### This form
Categories, vetoes, Tuesday headcount, receiving window.
### A brand, proposed
We tell you the brand first. For your first three drops, nothing comes unless you reply yes. After that, it comes unless you say no.
### Drop day
A Tuesday or Wednesday morning: one labeled case and a display card arrive.
### Feedback
Five business days later the survey closes, and you get your team's feedback.
What you sign: a one-page participation agreement listing what each side commits to. No fees either way, no penalties.
## Sign up your office
About 90 seconds: 11 required answers, five of them one tap.
Staging: submissions are not live yet. This form sends nothing.
### Please check these answers
Field group / question: You
Label: Company
Label: Your name
Label: Your title
Label: Work email
Label: Work phone (optional)
Only to confirm delivery days.
Field group / question: Your office
Label: Office street address
Number and street is enough, for example 123 Fifth Avenue.
Label: Floor or suite (optional)
Label: People in the office on a typical Tuesday
A rough count is fine. We size each drop to it.
Field group / question: Are you the pantry owner?
The person who can say yes to a drop alone.
Label: Yes, me
Label: Someone else
Label: Pantry owner's name
Label: Pantry owner's title
Field group / question: Deliveries
Field group / question: How do deliveries reach your office?
Label: Walk-up, straight to us
Label: Front desk
Label: Loading dock
Label: Something else
Field group / question: Best time to receive, on a Tuesday or Wednesday morning
Label: 8 to 10 am
Label: 9 to 11 am
Label: 10 am to noon
Label: Another time
Label: Which time works?
Field group / question: Does your building ask for a certificate of insurance before a delivery?
Label: Yes
Label: No
Label: Not sure
Field group / question: Your team
Field group / question: Where would you post the three-question survey link?
Label: Slack
Label: Email
Label: Other
Field group / question: Which categories do you want?
Label: Any of them
Label: Only some
Label: Chips and crisps
Label: Popcorn and puffs
Label: Crackers and pretzels
Label: Bars
Label: Cookies and baked snacks
Label: Chocolate and candy
Label: Nuts, seeds and trail mix
Label: Jerky and meat sticks
Label: Dried fruit and fruit snacks
Label: Sparkling water and soda
Label: Tea, juice and other still drinks
Label: Ready-to-drink coffee
Label: Other snacks
Label: Other drinks
Label: Anything you never want? (optional)
Brands, ingredients or categories. For example: nothing with peanuts.
Label: Anything else? (optional)
Button: Sign up my office
### Thanks. We have your answers.
Next, we will email you from {CONTACT_EMAIL} with the one-page participation agreement. Nothing starts until you sign it, and you can leave any time with a week's notice.
Draft for attorney review. Not legal advice.
### What this form collects, and why
Your business contact details, so we can reply. Your office's address, Tuesday headcount, pantry owner, receiving details, building rules and preferences, so we can plan deliveries and match brands. Nothing about your employees.
Your answers go to a private Google Sheet and one email to our inbox, seen only by {FOUNDER_NAME}. We do not sell them. A brand sees your office's neighborhood, industry and headcount when we propose a campaign, and learns your company's name only after it signs up for a drop at your office. If we do not end up working together, we delete your answers within 12 months. To see, correct or delete them, email {CONTACT_EMAIL}. More in our privacy notice.
## What is in the case
- Sealed, individually packaged, shelf-stable products, labeled with ingredients and allergens. The display card repeats the allergen statement word for word from the package.
- "Vetted" means each brand has passed our checks: sealed and shelf-stable with at least 60 days of shelf life, fully labeled, carrying product liability insurance, and outside every excluded category below.
- Never alcohol, cannabis or CBD, supplements, anything refrigerated or needing preparation, or products that make health claims.
## Your team's privacy
No personal data about your employees. The survey is anonymous: no login, no email. If a brand offers its newsletter, the box starts unticked, and an email goes to the brand only if someone ticks it.
Read the survey privacy notice
## Who can join
- Offices inside the cluster: about 14th to 30th Street, between Sixth Avenue and Park Avenue South, plus the blocks around Union Square.
- About 40 to 250 people in the office on a Tuesday. Near the edges? Send the form anyway and we will tell you honestly.
- A pantry owner who can say yes alone.
- Inside a coworking space? Companies there cannot join on their own, because the operator runs the pantry. An operator that runs its own pantry can join as one office.
### Founding offices
- Named on the founding roster, which brands see, only if you say yes.
- A standing veto and a category profile you can change any time.
- A summary of your team's feedback after each drop.
- Leave any time with a week's notice.
- Office cluster
- Grocer with a documented natural, local or emerging set
- Specialty, gourmet or natural-format market
Open the map full size

---

### Page: Privacy notice (`site/privacy.html`)

Page title: Privacy notice
Meta description: How this website and its two forms handle your information. Business contact details only; no cookies.
Draft for attorney review. Not legal advice.
# Privacy notice
Last updated [DATE]. This website is run by {COMPANY_LEGAL_NAME}, trading as {BRAND_NAME} ("we", "us"). Questions: {CONTACT_EMAIL}, {POSTAL_ADDRESS}.
This notice covers this website and its two forms. The anonymous employee survey has its own notice: survey privacy notice.
## What the forms collect
- Office form: company, your name, title, work email and (optional) work phone; the office address and floor; the number of people in on a typical Tuesday; the pantry owner's name and title; how deliveries reach you and when; whether the building needs a certificate of insurance; where you would post the survey link; the categories you want and anything you never want; and any notes.
- Brand form: brand name, website, product and category; where the brand is based; your name, title, work email and (optional) work phone; who approves the budget; the stores that carry you and your online store; whether you can issue a discount code; your timing; your answers to the seven checks; and any notes.
Both forms ask for business contact details only. They ask nothing about employees, customers or anyone else.
## Why
To reply to you, to tell whether a campaign or a drop fits, to plan deliveries, and to prepare proposals and agreements.
## Where it goes, and who sees it
- Each submission is saved as one row in a private Google Sheet in our Google account, and one email notification goes to our inbox. Google processes both under its own terms.
- Only {FOUNDER_NAME} reads them. We do not sell them or use them for advertising.
- When we propose a campaign, offices see the brand and product so they can approve or veto it, and brands see each office's neighborhood, industry and headcount. A brand learns an office's company name only after it signs up for a drop at that office.
## How long we keep it
While we work together. If we do not end up working together, we delete your answers within 12 months of your last contact with us.
## Your choices
Email {CONTACT_EMAIL} to see, correct or delete what you sent us.
## Visit counts
We count visits with GoatCounter, an open-source analytics service that does not use cookies and does not store IP addresses. It tells repeat visits apart with a random code that cannot be traced back to you. We see totals only: how many visits each page had, where visitors came from, browser and screen size, country, and how many times a form was started and sent. If your browser sends Do Not Track or Global Privacy Control, we do not count your visit at all.
## Cookies and other storage
This site sets no cookies and stores nothing in your browser. Fonts and images are served from this site, not from other services.
## Hosting
Our web host processes your IP address and browser details to deliver the pages, under its own privacy policy.
## Changes
If we change this notice, we update the date above.

---

### Page: Survey privacy notice (`site/survey-privacy.html`)

Page title: Survey privacy notice
Meta description: How the anonymous employee survey handles answers and the optional newsletter email.
Draft for attorney review. Not legal advice.
# Survey privacy notice
This is the notice the anonymous employee survey links to. Its text is the legal pack's draft notice (version 0.5), unchanged. Brackets are filled per campaign.
Last updated [DATE]. This survey is run by [COMPANY NAME: {BRAND_NAME} LLC] ("we", "us"), which brings products from emerging snack and drink brands to offices. Questions: [EMAIL], [POSTAL ADDRESS].
## What we collect
- Your answers to the survey questions, and your comment if you write one.
- Which office the survey link came from (it is built into the link on the card and in your office's post) and when you answered.
- Your email address, only if you choose to give it for the brand's newsletter.
## What we do not collect
We do not ask for your name, your work email, a login or an employee ID. We do not ask your employer for anything about you, and your employer does not see your individual answers from us except comments, which we may quote word for word in the office summary.
## Technical information
The services that run the survey form and the short link on the card process technical information, such as IP address and device type, to deliver the page, under their own privacy policies. We set them up not to ask you to sign in. From the short link we see only totals, such as how many times it was opened and on which days.
## How we use your answers
To write a one-page report for the brand and a summary for your office, and to improve how we run these drops. We do not sell your answers or use them for advertising to you.
## Who sees what
- The brand gets totals (how many people answered, how many tried it, the average rating, how many would buy) and up to three comments quoted word for word, without any email address.
- Your office gets a summary of your team's answers, which may include comments quoted word for word.
- Comments are quoted as written, except that we remove any name we find. Please leave out your name and anything that identifies you or anyone else.
## If you give your email
We pass it to [BRAND] only if you tick the box. We send the brand those addresses once, as a list kept separate from survey answers, within seven days after the survey closes. After that, [BRAND]'s privacy policy applies ([BRAND PRIVACY POLICY URL]) and you can unsubscribe from [BRAND] at any time. We delete our copy within 30 days after passing it on. If you change your mind, write to [EMAIL]: if we have not passed your email on yet, we delete it; if we have, we ask [BRAND] to delete it too.
## How long we keep answers
We keep survey answers for 12 months after the campaign, then delete them. Reports keep only totals and quoted comments.
## Your choices
The survey is optional. You can skip it, skip any question or stop at any time. Because answers are anonymous, we cannot find yours to change or delete it unless you gave an email address.
## Changes
If we change this notice, we update the date above. We will not use answers already given in a way this notice does not describe.

---

### Page: Page not found (`site/404.html`)

Page title: Page not found
Meta description: Page not found.
# Page not found
That page does not exist. Try one of these:
- Home
- For brands
- For offices
<!-- GENERATED:END -->
