# Part B working notes (workstream G, legal and admin pack)

Agent: Part B. Started 2026-10-23.
Scope: 00 index placeholder, 01 formation checklist, 02 name-check log, 20 GL quote script,
21 food safety call script and log, 22 accountant question list, figures.csv.
Part A owns 10-19 and 30-39. Merge step writes README.md, REPORT.md, HANDOFF.md.

## Status log
- 2026-10-23: read prompt G, plan.md, CONTRACTS.md. Folder had only _work/.

## Research log (URL, date opened, what it said)
(filled below as research proceeds)

## Changelog by round
- Round 1 (2026-10-23): drafted 00, 01 (+ name-check-log.md pointer), 02, 20, 21, 22 and figures.csv from the research below.
- Round 2 (2026-10-24): four expert passes. Attorney (02): verbatim §206 quotes, no legal conclusion on suspension, Transparency Act 30-day window. Trademark attorney (01): default changed to "treat as taken, shortlist two fallbacks, decide before filing"; name only in its definition line; rerun script built and tested. Broker (20): mishandling gap from the brand agreement's carve-out, BOP comparison, bind checklist. Inspector (21): question/facts mismatch (3 vs 4 weeks) fixed, no "never repacked" claim, arrival checks, cleaning/pests. Accountant (22): survey-report risk stated, UBT credit question neutral, non-NYC resident case. figures.csv: trademark high corrected 750 -> 850.
- Round 3 (2026-10-24): full read of every file. Deadline rule made exact everywhere: bind insurance and get the state answer "before any brand ships, latest Mon 2026-12-21" (a brand paid at Gate 1 may ship before the 12-22 ask). Removed unverified claims (what carriers want; "Division of Food Safety and Inspection" naming). Privacy: DROPDESK's individual owner no longer named. Contradiction fixed in 21 ("I sell nothing" vs a paid fee). Statute quotes made exact (Tax Law 1105(c)(1) opening words; TB-ST-740 "Certain food and drinks"). Rendering: dollar pairs were parsed as TeX math by pandoc (and would be by GitHub); all $ escaped in Part B .md files; checked tables render as text (screenshots viewed).
- Round 4 (2026-10-24): final full pass changed wording only (".nyc may require", "kept for the record", domain count 13, rerun step wording, pointer file defines the name once and carries the recommended default). Stop rule met.

### Name check raw results (2026-10-23, UTC times)
Raw files: _work/namecheck/ (rdap_*.json, sites/*.html, uspto/*.json, uspto/*.png, tsdr_*.html)
- 23:30:08Z Verisign RDAP deskdrop.com: HTTP 200, registered 2004-01-31, expires 2027-01-31, registrar Squarespace Domains II LLC, status active, NS Google Domains cloud. Homepage GET: connection reset (no site seen).
- deskdropnyc.com: HTTP 404 (no RDAP record). desk-drop.com: 404. deskdrophq.com: 404. mydeskdrop.com: 404. deskdrop.net: 404 (Verisign .net RDAP).
- thedeskdrop.com: 200, registered 2026-03-08 GoDaddy. trydeskdrop.com: 200, registered 2026-07-06 GoDaddy. getdeskdrop.com: 200, registered 2026-10-15 Cloudflare (serves "Wickline Light Bar" waitlist, unrelated). deskdropco.com: 200, registered 2026-03-22 Tucows (Shopify "Store unavailable", HTTP 402).
- IANA bootstrap (publication 2026-10-22T23:00:04Z): .nyc -> https://rdap.nic.nyc/ ; no .co entry.
- 23:30:25Z rdap.nic.nyc deskdrop.nyc: HTTP 404 errorCode 404 "Not found" "No data found". deskdropnyc.nyc: same. Positive control nic.nyc: 200 (registered 2013-08-09).
- .co: rdap.nic.co and rdap.registry.godaddy refused by proxy. DNS-over-HTTPS (cloudflare-dns.com) 23:30:45Z: deskdrop.co NS = ns03/ns04.domaincontrol.com -> delegated, so registered. deskdrop.co redirects to thedeskdrop.com.
- ACTIVE USER OF THE NAME: thedeskdrop.com (also via deskdrop.co, trydeskdrop.com): "DeskDrop | Stay top of mind with the people who matter most." Custom-branded chocolate jars (30 chocolates) shipped to prospects/clients' desks; pilot $995 for 25 gifts then $35/gift; "Nationwide shipping"; 312 phone (Chicago area code); (c) 2026 DeskDrop. Fetched 2026-10-23.
- USPTO tmsearch (headless Chromium, UI typed search) 23:32Z "desk drop": 5,032 results (any-word match). Top hit: DESK-DROP serial 99174501, Elior, Inc. (Delaware corp, Houston TX address), filed 2025-05-07, ITU 1(b), IC 035 online ordering food and drink; IC 043 food via cafe/restaurants featuring office delivery, catering, corporate event catering. DEAD, ABANDONED 2026-03-31.
- "deskdrop" 0 results; "deskdrops" 0; "desk drops" 2,756 (any word; no both-word marks in top results).
- Custom ES queries in-page 23:34:41Z: both words in WM: 1 (99174501). Both words in PM: 2 (99174501; DROPDESK 87516183 (owner: an individual), reg 5782323, LIVE, IC 036 co-working office rental). Wildcard *deskdrop* WM/PM: 0. Positive control *dropdesk*: 1 (works).
- TSDR statusview sn99174501 at 2026-10-23 19:35:32 EDT: "Abandoned because the applicant failed to respond or filed a late response to an Office action." Status date Apr. 14, 2026; abandoned Mar. 31, 2026. Non-final action e-mailed Sep. 30, 2025; extension granted Dec. 29, 2025. Filed use: No; ITU: Yes.
- 2026-10-23 23:36Z: downloaded the non-final Office action for 99174501 (OfficeAction7869279.pdf, 29 pages extracted; issue date Sep 30, 2025) via TSDR proxy URL https://tsdrsec.uspto.gov/ts/cd/casedocs/webcontent/proxy?url=/casedoc/cms/case/99174501/office-action/OfficeAction7869279.pdf . Verbatim key lines:
  - "SUMMARY OF ISSUES: Section 2(e)(1) Merely Descriptive Refusal"
  - "The trademark examining attorney searched the USPTO database of registered and pending marks and found no conflicting marks that would bar registration under Trademark Act Section 2(d)."
  - "the term “DESK” means "a table, counter, stand, or booth at which a person works", and the term “ DROP” means "to deposit or deliver during a usually brief stop"." ... "the mark immediately indicates to consumers that the applicant’s services features and/or is offered in connection with delivery to the tables, counters, stands or booths at which people work."
  - "the proposed mark, DESK-DROP, is refused registration because it is merely descriptive of the applicant’s goods and/or services under Trademark Act Section 2(e)(1)."
  Implication (not a legal conclusion): a federal registration for "Desk Drop" for office snack placement may meet the same descriptiveness refusal; attorney to advise. Elior did not respond; abandoned.
- NY DOS web search https://apps.dos.ny.gov/publicInquiry/ : curl gets "Empty reply from server"; headless Chromium gets HTTP 200 but an F5 "TSPD" bot-defense challenge that reloads in a loop; no search form rendered (only a hidden _pd input). Did not try to evade bot defense. -> founder to run.
- Substitute (official DOS data on data.ny.gov, Socrata API), 2026-10-23 23:37-23:38Z:
  - n9v6-gdp6 "Active Corporations: Beginning 1800", attribution NYS Department of State, rowsUpdatedAt 2026-10-23T12:32:32Z ("all active corporations as of the last business day of the specified month and year"). LIKE '%DESK DROP%' 0 rows; '%DESKDROP%' 0; '%DESK-DROP%' 0; DESK AND DROP: 1 row, 5169826 DROPDESK LLC, filed 2017-07-13, Nassau, domestic LLC. Control 'ELIOR%' 7 rows (query works).
  - ekwr-p59j "All Filings - Name Status History" (7,520,527 names: name_type A only; status A 4,334,868 / I 3,185,659): DESK AND DROP -> only DROPDESK LLC (active). No assumed names in this table.
  - k4vb-judh "Daily Corporation and Other Entity Filing Data" (max filing_date 2026-10-22): corp_name or fictitious_name with DESK and DROP -> 0 rows.

### Formation research (2026-10-23)
- WebFetch https://dos.ny.gov/certificate-publication-domestic-limited-liability-company-0 (opened 2026-10-23): "$50 filing fee for Certificate of Publication."; "within 120 days after the effectiveness of the initial articles of organization"; "publish in two newspapers a copy of the articles of organization or a notice related to the formation of the LLC."; failure: "will have their authority to carry on, conduct or transact any business suspended." Cites LLC Law §206. (curl gets 403 from dos.ny.gov; WebFetch works.)
- WebFetch https://www.nysenate.gov/legislation/laws/LLC/206 (opened 2026-10-23; revision 2014-09-22): within 120 days after effectiveness; once in each week for six successive weeks; two newspapers of the county where the office is located, one weekly and one daily, designated by the county clerk; in a city of 1M+ designation made as for notice of judicial proceedings; contents list (name, filing date, county, SOS as agent + address, registered agent, dissolution date, purpose); file certificate of publication with affidavits; suspension if not filed in 120 days; annulled on later filing; failure does not impair contracts or make members personally liable.
- WebFetch https://dos.ny.gov/limited-liability-company-articles-organization (opened 2026-10-23): "The fee for filing the Articles of Organization is $200."; online filing available; publication 6 consecutive weeks, Certificate of Publication "$50 filing fee"; written operating agreement required (before, at, or within 90 days after filing); name availability search "$5 per name submitted"; expedited $25 (24h), $75 (same day), $150 (2h).
- WebFetch https://www.nysenate.gov/legislation/laws/LLC/417 (opened 2026-10-23; revision 2014-09-22): members "shall adopt a written operating agreement"; before, at, or within ninety days after filing articles.
- LLC Transparency Act: WebFetch https://dos.ny.gov/beneficial-owner-disclosure (opened 2026-10-23): duty stated for "non-exempt limited liability companies that were formed under the law of a foreign country"; "Effective January 1, 2026"; "$25" statutory fee. Holland & Knight 2026-01-13 https://www.hklaw.com/en/insights/publications/2026/01/new-york-llc-transparency-act-reporting-limited : Gov. Hochul vetoed the decoupling amendment 2025-12-19; U.S.-formed LLCs including NY ones are "exempt" from reporting. -> NY LLC owned by a US person: likely nothing to file; attorney to confirm.
- Publication costs:
  - statebusinesscompliance.com (plan's source), WebFetch 2026-10-23, "Last updated: May 5, 2026", author "Daniel Reyes, CPA"; "estimated ranges based on 2026 newspaper advertising rates": New York (Manhattan) $1,500–$2,000+; Kings $800–$1,200; Queens $600–$1,000; Westchester $600–$900; Suffolk $400–$700; Albany $200–$300; Erie $200–$350; Monroe $200–$350; Rural upstate $100–$200. No Bronx/Richmond/Nassau/Schenectady. Affiliate disclosure link in footer.
  - llcpublishers.com/pricing (vendor "LLC Publishers"), WebFetch 2026-10-23, no date on prices; all-in package incl. both papers 6 weeks, affidavits, notarization AND the $50 state fee: New York $1,795; Bronx $1,745; Kings $1,475; Richmond $1,295; Queens $1,195; Nassau $625; Suffolk $625; Erie $445; Albany $395; Westchester $395; all other counties $425.
  - cheapnypublication.com/llc-publication-cost-by-county (vendor "Cheap NY Publication", operated by Redstone Castle LLC), WebFetch 2026-10-23, (c) 2026: newspaper-only ballparks "from published rates", $50 NOT included: Manhattan $1,000–$1,700; Brooklyn $400–$800; Queens/Bronx/Richmond/Nassau/Suffolk/Westchester/Rockland/Erie/Monroe/Onondaga $399–$600; Albany "Lowest in New York" (no figure). Vendor packages incl. $50: Albany $349 all-in; Manhattan $498 all-in promo "normally $600" "through October 27" (no year). Outlier vs every other source -> founder to get it in writing, confirm it uses the clerk-designated papers.
- Albany County Clerk designation page: old URL https://www.albanycountyny.gov/government/county-clerk/publication-of-legal-notices now 404 (site redesigned, CivicPlus). Not verified. Search snippet said Times Union and Daily Gazette are daily papers on the list (unverified).
- 2026-10-23 ~23:43Z: shared WebSearch budget exhausted (200 per turn across agents). From here: direct fetches of known URLs only; no more searching.
- LLC Law §1101 (WebFetch nysenate, opened 2026-10-23, revision 2015-04-24): (f) articles of organization $200; (s) certificate of publication with affidavits $50; (a) reservation of name $20; (g) certificate of amendment $60; (v) certificate of change $30. Biennial statement fee NOT in §1101.
- LLC Law §203 (opened 2026-10-23, revision 2026-09-04): (e)(2) articles set forth "the county within this state in which the office of the limited liability company is to be located"; (d) formed at filing or a later date stated "not to exceed sixty days from the date of such filing".
- LLC Law §301 (opened 2026-10-23, revision 2023-01-06): (e)(1) biennial statement "in the calendar month during which its articles of organization ... were filed". Fee not stated; dos.ny.gov/biennial-statements 404. Biennial fee: unverified.

### Food safety (2026-10-23)
- WebFetch https://agriculture.ny.gov/food-business-licensing : "This license applies to any food warehouse facility within New York in which food is held for commercial distribution." Warehouses storing or distributing food, excluding raw agricultural commodities, need a 28-D license. No fee on the page. Metro New York and Long Island Office (Bronx, Kings, Nassau, New York, Queens, Richmond, Suffolk): (718) 722-2876; 55 Hanson Place, 3rd Floor, Room 378, Brooklyn, New York 11217-1583. Application form "Application for Food Warehouse License - Article 28-D" downloadable.
- WebFetch https://www.nysenate.gov/legislation/laws/AGM/500-B (revision 2026-02-20; earlier 2025-10-24): subd 1 "No person shall maintain or operate a retail food store, food service establishment or food warehouse" without license; subd 3 verbatim "The license fee shall be two hundred fifty dollars provided, however, that food warehouses shall pay a license fee of four hundred dollars."; two years from issuance; application "on or before December first of every other year for the registration period beginning January first following". Exemptions: registered/permitted/licensed by the department under other provisions; under permit and inspection by state health dept or certified local health agency; subject to USDA inspection.
- AGM §500-a (revision 2026-02-20): "Food warehouse" shall mean any food establishment in which food is held for commercial distribution. "Retail food store" ... "does not include establishments which handle only pre-packaged, non-potentially hazardous foods" (that carve-out is in the retail store definition only, not the warehouse one). "Food establishment" not defined in §500-a.

### Tax (2026-10-23)
- NYC DOF UBT page https://www.nyc.gov/site/finance/business/business-unincorporated-business-tax-ubt.page : "A 4% tax rate is charged for taxable income allocated to New York City."; "A liability of $3,400 or less is allowed a credit for the full amount of the tax." partial credit $3,401-$5,400; NYC-202 "for Individuals, Single-Member LLCs"; NYC-5UBTI individual estimated declaration (2026). Gross-income filing threshold not shown on page -> accountant.
- NYS MCTMT self-employed https://www.tax.ny.gov/pit/file/nyc_yonkers_residents.htm (Updated June 30, 2026): threshold "$50,000 for tax years 2025 and prior." and "$150,000 for tax year 2026 and after." (net earnings from self-employment per zone). Rates not on page.
- IT-204-LL instructions (tax.ny.gov/pdf/current_forms/it/it204lli.pdf, fetched 2026-10-23, saved _work/tax/it204lli.pdf; references calendar-2025 returns): must file if "limited liability company (LLC) that is a disregarded entity for federal income tax purposes that has income, gain, loss, or deduction from New York State sources"; "If your LLC is treated as a disregarded entity for federal income tax purposes and has any income, gain, loss, or deduction from New York sources, the filing fee is $25."; due "on or before the 15th day of the third month following the close of your calendar or fiscal tax year"; no extension.
- TB-ST-360 https://www.tax.ny.gov/pubs_and_bulls/tg_bulletins/st/how_to_register_for_nys_sales_tax.htm (Updated Oct 21, 2026): "you must register with the Tax Department at least 20 days before you begin business."; display Certificate of Authority. No fee mentioned.
- TB-ST-175 (updated Oct 16, 2026): "Sales of services are generally exempt from New York sales tax unless they are specifically taxable."; taxable incl. "certain information services", "storage, except for certain self-storage units"; soda, candy, bottled water taxable TPP. Information services memo TSB-M-10(7)S.
- TB-ST-740 quick reference (footer Updated Sep 30, 2026): information services T; "storing tangible personal property" T; candy and confections T; soda T; bottled water T; certain food E; qualifying promotional materials E (Tax Law 1115(n), TB-ST-692). Advertising not addressed.
- Tax Law §1105 (nysenate, revision 2026-06-05): (c)(1) information services taxable "but excluding the furnishing of information which is personal or individual in nature and which is not or may not be substantially incorporated in reports furnished to other persons, and excluding the services of advertising or other agents, or other persons acting in a representative capacity"; (c)(4) "Storing all tangible personal property not held for sale in the regular course of business".
- IRS EIN page (Page Last Reviewed or Updated: 16-Oct-2026): "Use this tool to get an EIN directly from the IRS in minutes for free." "You never have to pay a fee for an EIN."
- IRS estimated taxes page (updated 25-Sep-2026): individuals "generally have to make estimated tax payments if they expect to owe tax of $1,000 or more when their return is filed."
- USPTO fee schedule https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule ("Effective January 19, 2025 (Last revised August 14, 2026)"): 2.6(a)(1)(iii) Base application, per class 350.00 (electronic); insufficient information per class 100.00; free-form text per class 200.00; each additional 1,000 characters 200.00; AAU/SOU per class 150.00.

### Insurance definitions (IRMI glossary, fetched 2026-10-23)
- vendors endorsement: "a standard commercial general liability endorsement (CG 20 15) that provides vendors coverage." https://www.irmi.com/term/insurance-definitions/vendors-endorsement
- blanket additional insured endorsement: "automatically grants insured status to a person or organization that the named insured is required by contract to add as an insured." 
- primary and noncontributory; waiver of subrogation; bailee coverage: "inland marine coverage on property entrusted to the insured for storage, repair, or servicing."
- Not verified: ISO form numbers for designated-person AI, managers/lessors of premises AI, HNOA. Broker to name forms.

## For the merge step (README, REPORT, HANDOFF)
- Files: 00-index.md (placeholder, Part B rows), 01-name-check-log.md, name-check-log.md (pointer at the CONTRACTS 6.7 path), 02-formation-checklist.md, 20-gl-quote-request-script.md, 21-food-safety-call-script-and-log.md, 22-accountant-question-list.md, figures.csv. Rerun tool: _work/namecheck/scripts/name_check.py.
- Deviation from CONTRACTS 6.7: canonical log is 01-name-check-log.md; name-check-log.md is a pointer with the gate status. Keep both status lines in step.
- Numbering: name check is 01 (week 1) and formation 02 (first verbal brand yes), the order of use. 20-22 follow the task's listed order; the food safety call is recommended earlier than the plan's Gate 1 checklist (by Fri 2026-11-20), which keeps 21 before the first invoice/accountant timing in practice. Assumption logged.
- Handoffs: figures.csv -> H (columns exactly per 6.7; 'unknown' used for unresearched money values). Name gate -> C, D. 21 answer log -> F (storage decision) and figures.csv item food_warehouse_license_28d_two_years. 20 needs F/H's revenue estimate placeholder [12-MONTH REVENUE ESTIMATE].
- Cross-file consistency with Part A: handling description ("from arrival until the campaign ends (usually two to three weeks, up to about four around the December holidays)"; sealed units moved, unopened, into one delivery box per office) is used verbatim in 20 and 21, matching 14. 20 Q13 runs the broker "wording test" on 15's Step 3 request block. 20 Q2 covers the mishandling carve-out in 12 section 6.
- Part A files that hardcode "Desk Drop LLC" (e.g. 15 Step 3 "Named insured: Desk Drop LLC", 14 "Additional insured (vendor): Desk Drop LLC") should take the name from their single definition line; flag to merge.

## What the attorney hour should cover (Part B items)
1. Name: the DeskDrop chocolate-gifting business (thedeskdrop.com) and the USPTO descriptiveness refusal of DESK-DROP (99174501): keep the working name or rename before filing? Is a federal application worth $350/class?
2. Office county: may the Articles name Albany County when the founder works from [BOROUGH]? What must exist there?
3. LLC Transparency Act: confirm a NY LLC with one US individual member files nothing.
4. 120-day rule: weekend day-120 counting; what suspension blocks in practice.
(Plus Part A's agreement review items.)

## What the accountant hour should cover (top items from 22)
1. Is the campaign fee taxable, given the survey-based report (information services, Tax Law §1105(c)(1)) and the storage of brand product (§1105(c)(4))? Certificate of Authority timing (20 days before).
2. 2027 estimated payments: federal ($1,000 threshold), NYS, NYC; dates.
3. NYC UBT: 4%, full credit if liability <= $3,400; filing threshold; NYC-202; estimates.
4. MCTMT threshold $150,000 from 2026: confirm below.
5. IT-204-LL $25 for 2026 if formed Nov 2026 (due 2027-03-15).
6. Start-up costs, deposits across year end, 1099s, Wave setup, tax set-aside, one calendar.

## Assumptions (Part B)
1. Filing happens at the first verbal brand yes, expected near Gate 0 (Fri 2026-11-13); dates for week 5 and Gate 1 also shown.
2. Working publication figure = LLC Publishers all-in package less the $50 state fee (only firm all-in price for every county). Default budget line uses New York County ($1,745) until the county is chosen.
3. Counties compared: the five NYC boroughs (the founder's borough is unknown, plan Q3) plus Albany.
4. Storage and handling facts match Part A's file 14 verbatim; volumes: campaign zero ~550 units (2 brands x 275), later up to ~1,650 (3 x 10 offices x 55).
5. Food safety call recommended by Fri 2026-11-20 (earlier than the plan's Gate 1 checklist); hard deadline before first case can arrive, Mon 2026-12-21.
6. GL bind deadline Mon 2026-12-21, from CONTRACTS ship-by Tue 2026-12-22.
7. GL working figure $1,200/yr = plan's "roughly $100 a month"; range $500-$1,500 from the plan.
8. Food warehouse license working figure $400 (cautious) until the state answers.
9. Attorney $400 and accountant $300 working = plan ranges' midpoints, totalling the plan's "about $700".
10. Day 120 not assumed to roll forward past a weekend.

## Blocking questions (with recommended default)
1. Keep "Desk Drop" or rename before filing? Default: treat as taken; shortlist two fallbacks in week 1, run name_check.py on each, decide by Fri 2026-11-13.
2. Which county will the Articles name? Default: your own borough's county unless the attorney confirms Albany is fine; budget New York County ($1,745) until then.
3. Where would cases be stored (apartment or storage unit, which borough), and do you own a car? Default: apartment, no car; fill the facts sheets in 20 and 21.
4. May the attorney hour (name and county questions) happen before the filing day? Default: yes, book it in week 3.

## Notes for Part A / merge
- Rendering: in Part A's files, lines with two dollar amounts (e.g. "$600 ... $1,500") may render as math in pandoc (and GitHub). Part B escaped every $ as \$; Part A's render script may want the same, or pandoc `-f gfm-tex_math_dollars`.
- Version stamps: Part B files are "Version 0.4 · 2026-10-24".
- Rerun tool: `python3 desk-drop-legal-pack/_work/namecheck/scripts/name_check.py "<name>"` from desk-drop/ (needs node + playwright for the USPTO part). Tested 2026-10-24T00:04:51Z.
