# Spot-check log (by round)

Method, every round: draw ten rows per table at random from the current top list (Python `random.sample`, seed named per round), re-open every source the row cites (curl GET with a generic User-Agent; pages saved in `_work/fetch/spotcheck/<round>/`), and compare field by field. Count errors as fields wrong over fields actually re-checked. A field counts as checked only if its source was opened in this round. sec.gov and LinkedIn are never opened (privacy rule and bot block); a row resting on them is checked on its other sources. "Fabricated" means a value no opened source supports and no note marks as unverified.

## Round 1 (2026-10-24, seed 20261024; samples in `_work/spotcheck_r1_offices_sample.csv` and `_work/spotcheck_r1_brands_sample.csv`)

### Offices (10 rows from the top 50)

| Row | Company | Fields re-checked | Result |
| --- | --- | --- | --- |
| AO-C-197 | Rakuten USA | address (NYREJ 2026-02 lists Rakuten USA as a 215 Park Ave S tenant; Built In New York office 215 Park Ave S), headcount 980 (Built In), attendance (Built In OnSite, 5 days), gate arithmetic | 4 of 4 correct. The primary address source is a sec.gov rent roll and was not opened. Observation: no parent is recorded although the name points to Rakuten Group; left `unknown` because no opened source states it. |
| AO-C-031 | Dashlane | address (terms page: 44 West 18th Street, NY 10011), headcount 284 (Built In), attendance (Hybrid, "Flexible"), HQ New York, gate arithmetic | 5 of 5 correct |
| AO-C-013 | Rockwell Group | address (own About page footer: 5 Union Square West, 8th Floor), headcount 350 ("350-person firm", firm-wide), attendance unknown (no Built In URL in the row), gate arithmetic | 4 of 4 correct |
| AO-C-034 | Cognitiv | address (contact page: 215 Park Ave S, Floor 16), headcount 170 (Built In), attendance (Hybrid 3 days; "in person Monday through Wednesday"), HQ, gate | 5 of 5 correct |
| AO-C-130 | Butterfly Network | address (CO 2025-09-30 tenant list; Built In New York office 11 E 26th St floors 7 and 8), headcount 443, attendance (OnSite 5 days), HQ Burlington MA, gate | 5 of 5 correct |
| AO-C-046 | Radar | address (CO 2026-04-07 names Radar Labs at 111 Fifth Ave), headcount 64, attendance, gate | **1 error:** attendance read as on-site 5 days from Built In's "typical time" box, but the employer's own text says "Monday-Thursday, WFH on Fridays" (4 days). |
| AO-C-160 | K Health | address (Connect CRE: long-term renewal at 387 Park Ave S, late 2025), headcount 363, attendance (OnSite 5 days), HQ New York, gate | 5 of 5 correct. Built In still shows 298 5th Ave; B resolved the conflict to 387 Park Ave S. |
| AO-C-096 | Inspiren | address (CO 2026-09: full-floor lease at 61 W 23rd St), headcount 150, attendance (Hybrid, "Flexible"), why-now (own lease, 2026-09), gate | 5 of 5 correct |
| AO-C-133 | Order.co | address (CO 2026-02-05: 12,134 sf sublease at 11 E 26th St), headcount 165, attendance (Hybrid, "Flexible"), gate | 4 of 4 correct (signed-not-occupied, as B says) |
| AO-C-091 | 1stDibs | address (user agreement: 300 Park Avenue South, 10th Floor), headcount 455, attendance, HQ, gate | **1 error:** attendance read as on-site 5 days from the box, but the policy text says "Flex First ... individual teams set the parameters". Built In's office address is stale (51 Astor Place). |

Offices: 46 fields checked, 2 wrong, **4.3%**. No fabricated field.

### Brands (10 rows from the top 60)

| Row | Brand | Fields re-checked | Result |
| --- | --- | --- | --- |
| AB-006 | Strip Jerky | HQ New York (Entrepreneur: "based in New York City"), gates, retailer (none within ten blocks; Pop Up Grocer capped and outside), contact (Nicole Schlesinger, founder), online store, why-now | **1 error:** the why-now cited Forbes, which returned HTTP 403, so it could not be confirmed. Re-sourced to the opened Entrepreneur Q&A (2026-07-06: Hot Honey Date drop, 1,800+ pre-order bags). |
| AB-032 | Firehook | retailer and grade (WFM NoMad catalog lists 7 Firehook items), why-now (S&FWB 2026-07-10), contact (Maura Mottolese, CEO), category | 4 of 4 correct |
| AB-087 | Mayana Chocolate | retailer (WFM NoMad lists Mini Fix Bar and others), contact (Daniel and Tamara Herskovic, "husband and wife team"), why-now products on homepage, HQ as written ("Spooner, Mayana's future home") | 4 of 4 correct |
| AB-075 | Eleni's New York | retailer (WFM NoMad lists Crisp cookies), why-now (Licensing International, 2026-04-06), first name, last name | **1 error:** the last name was recorded as "Gianopulos"; the cited page spells it "Gianopulous". Now the page spelling, with the discrepancy in `contact_note`. |
| AB-226 | B-SIDES | retailer and grade (Stockist: Westside Market NYC, 84 3rd Ave, brand_claim), why-now ($500K seed, 2026-05-19), contact (Yousuf Ahmed, founder), online store | 4 of 4 correct |
| AB-069 | Sweet Loren's | retailer (WFM NoMad lists Breakfast Biscuits 5 count), contact (Loren, first name only), shelf-stable basis (story: "shelf-stable breakfast biscuits", 2023), HQ (NYC origin) | **1 error (judgement):** the why-now was a June 2026 launch of refrigerated items, the excluded line. Removed; no why-now now. |
| AB-222 | Shinzo Matcha | contact (co-founder Zach Hayworth), why-now (sparkling matcha soda at 30+ NYC grocers, 2026-05-01), HQ (New York dateline) | 3 of 3 correct |
| AB-174 | OOSO Sparkling Tea | primary contact (Co-Founder Sophia Racciatti), backup contact | **1 error:** the backup slot repeated Sophia (she is both co-founder and marketing lead). Now the backup is co-founder Oliver Spring. |
| AB-172 | Explorer Cold Brew | contact (Cason Crane, Founder & CEO), backup (Matt Adams, COO), why-now (2026 Shelfie finalist, Coffee) | 3 of 3 correct |
| AB-004 | Daily Crunch | retailer (WFM NoMad lists sprouted almonds), why-now (S&FWB 2026-10-19), contact (co-founder Laurel Orley), HQ Nashville, Startup CPG release | 5 of 5 correct |

Brands: 39 fields checked, 4 wrong, **10.3%**. No fabricated field (the Forbes citation may have been opened by the researcher; it could not be re-opened, so it is now marked unverified).

### Fixes made after round 1
1. Built In parser: the employer's own policy sentence now overrides the "typical time on-site" box when they disagree (Radar to hybrid 4 days, PlayPlay to hybrid 3 days, 1stDibs to hybrid, days not stated). All 105 cached pages re-parsed.
2. Brands: a person who is both co-founder and marketing lead fills one slot; the backup is the next co-founder. Titles are singular per slot ("Co-founder", "Owner").
3. Brands: a researcher's parenthetical about a name (spelling, first name only) is kept in `contact_note`; where it records the page spelling, the page spelling is used.
4. Corrections with sources in `_work/stage1_corrections.csv` (Strip Jerky why-now re-sourced; Sweet Loren's refrigerated why-now removed).

## Round 2 (2026-10-24, seed 20261025, round-1 rows excluded; samples in `_work/spotcheck_r2_*_sample.csv`)

### Offices (10 rows from the top 50)

| Row | Company | Fields re-checked | Result |
| --- | --- | --- | --- |
| AO-C-033 | Baseten | headcount 350 (Built In), attendance (Hybrid, 3 days), HQ San Francisco, gate | 4 of 4 correct. Address rests on a sec.gov rent roll (not opened) and Built In gives no NYC street, so the address was not re-checked this round. |
| AO-C-129 | Activate Consulting | address (CO 2025-09-30: 24,144 sf at 11 E 26th St), headcount 76, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-171 | Signal AI | address (own site: 440 Park Avenue South, 14th floor), headcount 226, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-052 | Bombas | address (Built In: 881 Broadway), headcount 223, attendance (OnSite 5 days), HQ, gate | 5 of 5 correct (B keeps it low: the only current source is an undated profile) |
| AO-C-095 | Foursquare | address (Built In HQ 50 W 23rd St; NYREJ tenant list), headcount 350, attendance (Hybrid, Flexible), gate | 4 of 4 correct |
| AO-C-055 | Stash | address (CO 2026-09: 12K sf at 641 Avenue of the Americas, move date unclear), headcount 380, attendance (Hybrid, Flexible), gate | 4 of 4 correct. Observation: CO says Stash still sits in a WeWork at 450 Park Ave S until the move, so it is a coworking tenant today. |
| AO-C-037 | Nayya | address (NYREJ: 29,915 sf lease, floors 4 and 18, 215 Park Ave S), headcount 150, attendance (Hybrid, 3 days), HQ, gate | 5 of 5 correct |
| AO-C-169 | Pumpkin Pet Insurance | address (Built In 432 Park Ave S; CO 2023 lease), headcount 175, attendance, gate | **1 error:** attendance recorded as "hybrid, days not stated"; the policy text says "Most colleagues work 2-3 days in-person". Observation: B records an address conflict (own homepage gives 666 Third Ave, outside the cluster) and asks for a lobby check before outreach; the table did not carry that hold. |
| AO-C-072 | Actively AI | address (CO 2025-04: 10,722 sf, floors 9 and 10, 30 W 21st St), headcount 65, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-128 | Simplebet | address (CO 2025-05 tenant list; Built In 373 Park Ave S, floor 9), headcount 95, attendance (OnSite 5 days), gate | 4 of 4 correct |

Offices: 42 fields checked, 1 wrong, **2.4%**. No fabricated field.

### Brands (10 rows from the top 60)

| Row | Brand | Fields re-checked | Result |
| --- | --- | --- | --- |
| AB-105 | Unreal | retailer (WFM NoMad lists Unreal gems), why-now (S&FWB 2026-03-18), contact source | **1 error:** the founder names come from Wikipedia (the enrichment source) but the row cited the brand's About page, which does not name them. |
| AB-088 | Jonesbar | retailer (WFM NoMad lists Jonesbar bars), contact (Taylor Jones, founder/CEO) | 2 of 2 correct |
| AB-003 | PRETZELIZED | retailer (WFM NoMad lists Pretzelized crackers), why-now (S&FWB 2026-08-05), contact source, backup contact | **2 errors:** the contact source had been replaced by a LinkedIn URL seen only in search results (never opened); the backup name read "Caitlin Mack . Also Dylan Lipari". |
| AB-111 | Harken Sweets | retailer (WFM NoMad), why-now (S&FWB 2026-05-14), contact (Katie Lefkowitz, Founder & CEO) | 3 of 3 correct |
| AB-034 | Reelie | retailer (WFM NoMad lists Artisan Tropic Reelie crackers), why-now fact, why-now type, primary contact | **2 errors:** the why-now (own product page) was typed as press; the primary contact was "Guzman family", which is not a person. |
| AB-072 | Blue Stripes | contact (Oded Brenner, founder), why-now (S&FWB 2026-01-09) | 2 of 2 correct |
| AB-090 | Maxine's Heavenly | contact name, contact title, why-now fact, why-now type | **2 errors:** Robert Petrarca is the CEO (press page); the founder is Tim Miller (story page), so "Founder and CEO" was wrong; the why-now (own homepage) was typed as press. |
| AB-107 | Solely | why-now (S&FWB 2026-08-19, Walmart nationwide), contact (Simon Sacal, CEO) | 2 of 2 correct |
| AB-070 | Raaka Chocolate | contact (founders "Ryan and Nate" on the story page; surnames unverified, as flagged), why-now fact, why-now type | **1 error:** own-homepage why-now typed as press. |
| AB-239 | Hella Cocktail Co. | contact (Tobin Ludwig, Co-Founder & COO), backup (Eddie Simeón, Co-Founder & CMO) | 2 of 2 correct |

Brands: 29 fields checked, 8 wrong, **27.6%**. No fabricated field; seven of the eight errors were assembly logic (type labels, contact selection, source carry-over), one was a researcher's title.

### Fixes made after round 2
1. Why-now type: a why-now on the brand's own domain (product page, homepage, own press page) is now a "listing", never "press". 112 passed rows are listings, 74 press.
2. Contacts: only strings that look like a person's name fill a contact slot (no "family", "team", roles or phrases); "Also" and stray punctuation split names; each person gets the title written for them ("Name: Title; Name2: Title2" cells); the contact source is the page that supports the name (the enrichment source when the name came from enrichment); a LinkedIn URL seen only in search results goes to `contact_linkedin_url` with `linkedin_status = search result, not opened` and never replaces the opened source; a name whose only page is LinkedIn is `unverified`.
3. Maxine's Heavenly title corrected to CEO (`_work/stage1_corrections.csv`).
4. Built In parser: "2-3 days" (lower figure), "twice a week", "3 in-office days", "hybrid 3 days" and named weekdays are read from the policy text; `tuesday_named_in_policy` = Y where the employer names Tuesday as an office day (+3 attendance points, capped at 15).
5. Offices: `hold_before_outreach` and `hold_reason` carry B's instructions: signed-not-occupied (check the lobby directory), an unresolved address conflict (address points 0), a coworking tenant until its move, a possibly-closed site.

## Round 3 (2026-10-24, seed 20261026, rounds 1 and 2 excluded; samples in `_work/spotcheck_r3_*_sample.csv`)

### Offices (10 rows from the top 50)

| Row | Company | Fields re-checked | Result |
| --- | --- | --- | --- |
| AO-C-083 | CompStak | address (Built In HQ 675 6th Ave, 4th floor; own About page returned 403), headcount 150, attendance (3 days in office, 2 at home), gate | 4 of 4 correct |
| AO-C-155 | Primary Wave | address (CO 2026-03 tenant list; own contact page 1165 Broadway, 5th Floor), headcount 109, attendance (Built In: Remote Workplace), gate | 4 of 4 correct as sourced. Observation: the Built In profile is unclaimed ("Claim Profile") while the company's own page shows a staffed office, so "remote" is a weak signal. |
| AO-C-038 | Stellar Health | address (Built In HQ 215 Park Ave South; NYREJ tenant list), headcount 165, attendance (Hybrid, not specified), gate | 4 of 4 correct |
| AO-C-001 | HUMAN Security | address (CO 2024-06: relocated to 841 Broadway, 13,809 sf; Built In HQ 841 Broadway), attendance (Hybrid, not specified), gate | 3 of 3 correct |
| AO-C-048 | Aterian | address (Built In 37 E 18th St; CO 2026-06 names Mohawk Group, Aterian's former name, as a tenant), headcount 122, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-009 | Alpine Investors | address (own contact page: Zero Irving, 124 East 14th St, 12th Floor), headcount 203, attendance (OnSite 5 days, HQ San Francisco), gate | 4 of 4 correct |
| AO-C-061 | Daily Harvest | address (Built In HQ 37 West 20th Street), headcount 267, attendance (OnSite 5 days), gate | 4 of 4 correct (B keeps it low: undated profile only) |
| AO-C-105 | Orbital | address (CO 2026-09: 11,185 sf, entire 6th floor, 40 W 25th St, moving from 18 W 18th St), attendance (OnSite 5 days), hold flag (signed-not-occupied), gate | 4 of 4 correct |
| AO-C-050 | Global Trading Systems | address (CO 2024-11: 35,156 sf at 625 Avenue of the Americas; locations page now 403), headcount 420, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-035 | Global Strategy Group | address (own locations page: 215 Park Avenue South, 15th Floor), headcount 187, attendance (OnSite 5 days), gate | 4 of 4 correct |

Offices: 39 fields checked, 0 wrong, **0%**. No fabricated field.

### Brands (10 rows from the top 60)

| Row | Brand | Fields re-checked | Result |
| --- | --- | --- | --- |
| AB-130 | Moshi | retailer and grade (Storepoint: Dainobu, 498 6th Ave, 0.9 blocks out, brand_claim), why-now (DAN DA DAN listing on own store), contact (Founder Alton But, Expo West page), backup (Horin Yip, Brand Marketing Manager) | 5 of 5 correct |
| AB-080 | Spring & Mulberry | retailer (WFM NoMad lists the bars), contact (Kathryn, first name only), HQ (FAQ: "based in Raleigh, North Carolina") | 3 of 3 correct |
| AB-207 | Stiller's Soda | retailer (WFM NoMad lists Stillers Soda), why-now (Beverage Industry 2026-03-30), contact status | **1 error:** Alex Doman was marked unverified because the title cell said "CEO title seen only in a snippet"; Food Business News (opened) names him as co-founder, so the name is verified. |
| AB-047 | Go Raw | retailer (WFM NoMad API lists Go Raw seeds), why-now (S&FWB 2026-05-06), contact (Maggie Quinn, brand manager), HQ (Freeland Foods, Northbrook IL) | 4 of 4 correct |
| AB-104 | 88 Acres | retailer (WFM NoMad), contact (Co-founder Nicole Ledoux) | 2 of 2 correct |
| AB-106 | Taza Chocolate | retailer (WFM NoMad), contact (founder and CEO Alex Whitmore), HQ Somerville MA | 3 of 3 correct |
| AB-027 | Biena | retailer (WFM NoMad), contact (Poorvi Patodia, Founder & CEO), why-now (9-pack listing on own store) | 3 of 3 correct |
| AB-182 | OOZ Birch Water | retailer and grade (own stockists file: Fairway Market Chelsea, 766 6th Ave), contact status (first name "Christina" on the story page; surname unverified), why-now | **1 error:** the why-now text says "(unverified, founder to confirm)" and the cited Pop Up Grocer page does not support it, yet it earned listing points. |
| AB-118 | Good Word Foods | retailer (WFM NoMad lists the protein cookie), why-now (About page: "This year we're finally launching something new") | 2 of 2 correct. The full-name source (commercialbaking.com) returned 403, so the surname was not re-checked. |
| AB-096 | Magic Spoon | retailer (WFM NoMad lists cereal only, as noted), contact status | **1 error:** Gabi Lewis was marked unverified for the same title-cell reason; S&FWB (opened) names him as co-founder. |

Brands: 30 fields checked, 3 wrong, **10.0%**. No fabricated field.

### Fixes made after round 3
1. Contact status now depends only on the name: the name cell, its note and whether the name itself came from a snippet. Doubt about a title alone no longer blanks a verified name (Stiller's, Magic Spoon and Beyond Good now verified; their sources are opened pages).
2. A why-now whose text says unverified, snippet or not opened is typed `unverified` and earns no points (6 passed rows).

## Round 4 (2026-10-24, seed 20261027, rounds 1 to 3 excluded; samples in `_work/spotcheck_r4_*_sample.csv`)

### Offices (10 rows from the top 50)

| Row | Company | Fields re-checked | Result |
| --- | --- | --- | --- |
| AO-C-082 | Candid Health | address (CO 2026-01: 29K sf lease at 675 Avenue of the Americas), headcount 256, attendance (OnSite 5 days), hold flag (signed-not-occupied) | 4 of 4 correct |
| AO-C-007 | Personetics | address (NYREJ 2025-04: three-year lease, 7,004 sf, entire 19th floor of 853 Broadway), headcount 371, attendance (OnSite 5 days), gate | 4 of 4 correct (Built In still lists 1216 Broadway; B keeps it occupancy-unconfirmed) |
| AO-C-253 | Optiver | address (CO 2025-05: first NYC office, 23K sf at 360 Park Ave S; Built In Suite 1200), headcount 1,600 company-wide, attendance (OnSite 5 days), gate | 4 of 4 correct |
| AO-C-098 | BrainPOP | address (terms of use: 71 W 23rd St, 17th Fl), headcount 225, attendance (Hybrid, Flexible), gate | 4 of 4 correct |
| AO-C-153 | Seedtag | address (own contact page: US HQ 15 West 27th Street, 3rd Floor), attendance (OnSite 5 days, company profile), gate | 3 of 3 correct |
| AO-C-059 | Christie's International Real Estate Group | address and count (CO 2024-08: 8,000 sf "to open a 75-person office" at 156 Fifth Ave), NYC-office scope, estimate (75 x 67% = 50) | 3 of 3 correct |
| AO-C-263 | PMG Worldwide | address (CO 2026-08: expanded at 387 Park Ave S to 38,744 sf; Built In 2nd Fl), headcount 1,000, attendance (Hybrid, 3 days), gate | 4 of 4 correct |
| AO-C-047 | The Vita Coco Company | address (CO 2024-09: 23K sf lease at 111 Fifth Ave), attendance unknown (no Built In URL), gate | 3 of 3 correct (the headcount rests on sec.gov, not opened) |
| AO-C-085 | Empathy | address (own site schema: 56 W 22nd Street; CO 2024-03), headcount 200, attendance (3 days; "onsite Tuesdays and Thursdays"), Tuesday flag, gate | 5 of 5 correct |
| AO-C-216 | Reaktor | address (Built In 30 W 21st St, 14th floor; CO 2025-04 tenant list), headcount 644, attendance (OnSite 5 days), gate | 4 of 4 correct |

Offices: 38 fields checked, 0 wrong, **0%**. No fabricated field. Offices have now had three consecutive rounds under 10% (2.4%, 0%, 0%) with nothing fabricated: the stop rule is met for this table.

### Brands (10 rows from the top 60)

| Row | Brand | Fields re-checked | Result |
| --- | --- | --- | --- |
| AB-237 | Z Crackers | retailer (WFM NoMad lists Everything Crackers, local), contact ("Pam and Keith Pollack, Founders"; "Keith Pollack, Z President"), HQ (Savory Pie Company, 215 Stratford Road, Brooklyn) | 4 of 4 correct |
| AB-124 | Goodio | retailer (WFM NoMad lists Goodio bars), contact (Jukka Peltola, Founder), HQ Helsinki, why-now and type (Cranberry & Rosemary bar in the store feed; listing) | 5 of 5 correct |
| AB-281 | Cirrus 9 Candy | why-now and type (SFA 2027 sofi finalists, 2026-10-19; press), contact (Morganne, Founder), backup (Makenna, Co-founder & tech) | 4 of 4 correct |
| AB-084 | Elements Truffles | retailer (WFM NoMad lists the bars), contact (Alak Vasa, founder), why-now and type (Diwali Gift Box on own site; listing), HQ (terms: Jersey City NJ) | 5 of 5 correct |
| AB-173 | JONI | why-now and type (2026 Shelfie finalist, Non-Alcoholic; press), contact (Claire Matern launched JONI) | 3 of 3 correct |
| AB-249 | Häppy Candy | why-now and type (Startup CPG release 2026-09-10, Target nationwide; press), retailer (WFM NoMad lists Big Apple Gummies), contact (Maxi Heidenblut) | 4 of 4 correct |
| AB-219 | The Lucky Ox | why-now and type (Startup CPG release 2026-05-01; press), contact (co-founders Fane He and Kyle Nguyen), retailer (WFM NoMad, local) | 4 of 4 correct |
| AB-073 | Seed + Mill | contact and backup (Goldbelly: Lisa Mendelson, Monica Molenaar and Rachel Simons), retailer (WFM NoMad lists Pistachio Halva 8 oz) | 3 of 3 correct |
| AB-048 | FitJoy Foods | retailer (WFM Union Square), contact (Norman Taliaferro, CEO & Founding Partner), backup (Micah Mills, Director of Marketing), why-now and type (Classic Cracker Squares on own store; listing) | 5 of 5 correct |
| AB-235 | Issa's | retailer (WFM NoMad lists Issas pita chips), contact (WKBW: Andrew and James Issa co-founded it in 2016), why-now and type (own store feed; listing) | 4 of 4 correct |

Brands: 41 fields checked, 0 wrong, **0%**. No fabricated field. Round 3 was 10.0%, not under 10%, so one more brand round follows.

## Round 5 (2026-10-24, seed 20261028, brands only, rounds 1 to 4 excluded; sample in `_work/spotcheck_r5_brands_sample.csv`)

| Row | Brand | Fields re-checked | Result |
| --- | --- | --- | --- |
| AB-086 | Joyride | retailer (WFM NoMad lists Peach Rings), contact (founder Tyler Merrick), HQ ("JOYRIDE is based in Austin"), why-now and type (S&FWB 2026-09-18; press), backup (Ryan Trahan, chief creative officer and co-owner) | 6 of 6 correct |
| AB-091 | Mavericks Snacks | retailer (WFM NoMad), why-now and type (S&FWB 2026-03-27; press), contact (Livio Bisterzo founded it), HQ (Santa Monica dateline) | 5 of 5 correct |
| AB-025 | Nantucket Crisps | why-now and type (Startup CPG release 2026-07-10; press), contact (Founders: Hayden Arnot), backup (Paul Nardone named CEO) | 4 of 4 correct |
| AB-097 | Beyond Good | retailer (WFM NoMad, local), contacts (Wikipedia: founders Tim McCollum, Brett Beach), HQ Brooklyn, why-now and type (Pistachio Crunch bar published 2026-10-02 on own store; listing) | 6 of 6 correct |
| AB-278 | Doosra | contact (Kartik Das), HQ ("made in Queens"), why-now and type (Gift Box published 2026-10-16; listing) | 4 of 4 correct |
| AB-016 | Ella's Flats | why-now and type (Boston Globe 2026-06-30; press), contact (Ellen Macks), retailer (WFM NoMad), HQ state (Globe: "a Florida company") | 5 of 5 correct |
| AB-023 | SuperSeedz | why-now and type (1 oz pack of 12 on own store; listing), HQ (PO Box, Guilford CT), retailer | **1 error:** WFM NoMad listed it on 2026-10-23 but not on 2026-10-24; WFM Chelsea still does. Now nearest = WFM Chelsea, 3 blocks out. |
| AB-285 | Effie's Homemade | why-now and type (SFA 2027 sofi finalists, Gruyere Biscuits; press), contacts (Effie's daughter Joan and her friend Irene), retailer (WFM NoMad lists Oatcakes) | 5 of 5 correct |
| AB-233 | Simply Gum | why-now and type (own blog, Simply Sours, 2026-02-25; listing), contact (Caron Proschan, founder and CEO), retailer (WFM NoMad, local) | 4 of 4 correct |
| AB-266 | Gigantic (Candy Deluxe) | retailer and grade (Stockist: Fairway Market, 766 6th Ave, brand_claim), why-now and type (Startup CPG pavilion at SFFS 2026; press) | 3 of 3 correct |

Brands: 46 fields checked, 1 wrong, **2.2%**. No fabricated field. Brands have now had two consecutive rounds under 10% (0%, 2.2%) with nothing fabricated: the stop rule is met for this table.

### Fix made after round 5: automated re-check of every Whole Foods link
Because a catalog listing moved between 2026-10-23 and 2026-10-24, every Whole Foods `store_selector` link (272, across 4 stores) was re-queried on 2026-10-24 with the same public store-scoped endpoint (`_build/recheck_wfm.py`; results in `_work/wfm_recheck_2026-10-24.csv`). Matching is strict (all of one name's distinctive words in the other's; a first pass that matched on one shared word, for example "Vermont", was re-run), and a link not found is retried by brand name and alias. Result: 261 found, 11 not found (Mamame 2, MASA Chips 3, SuperSeedz NoMad, Maine Crisp Co., Pip's Heirloom Snacks 4). Those 11 links are now `unverified` with the reason in `brand_store_links.csv`; the brand's nearest store moved to the next graded store where one exists. Catalogs change daily, so the daily routine re-checks a brand's store link before it is used in copy.

## Summary by round

| Round | Offices: fields checked, wrong, rate | Brands: fields checked, wrong, rate | Fabricated |
| --- | --- | --- | --- |
| 1 | 46, 2, 4.3% | 39, 4, 10.3% | none |
| 2 | 42, 1, 2.4% | 29, 8, 27.6% | none |
| 3 | 39, 0, 0% | 30, 3, 10.0% | none |
| 4 | 38, 0, 0% | 41, 0, 0% | none |
| 5 | not run (offices met the stop rule at round 4) | 46, 1, 2.2% | none |
