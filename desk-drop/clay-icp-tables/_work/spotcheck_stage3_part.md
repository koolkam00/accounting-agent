# Spot-check log, by round

Workstream A, Clay ICP tables. Every round hand-checks ten random rows per table from the top lists (top 50 offices, top 60 brands), re-opens every source each row cites, and compares field by field: the address and that it sits in the cluster, headcount, attendance, the gate arithmetic, contact names and titles, the New York base and title grade, retailer grades (the Whole Foods store catalog re-queried live), the health-claim, shelf-life and buy-path gates, why-now, HQ and online store. **Error rate = fields wrong / fields checked.** A field counts as checked only when its source was opened in that round; sec.gov and LinkedIn are never opened (privacy rule; EDGAR demands a contact email), and a page that returned 403 that day is not counted. "Fabricated" means a value no opened source supports and no note marks as unverified. **Stop rule (prompt): two consecutive rounds with nothing fabricated and under 10% error.**

Pages are saved gzipped under `_work/fetch/spotcheck/<round>/`; the evidence printouts are `_work/spotcheck_<round>_evidence.txt`; the rows drawn are `_work/spotcheck_<round>_{offices,brands}_sample.csv`. Tool: `_build/spotcheck_s3.py` (curl GET, generic User-Agent, one request at a time, no personal identifier).

## Summary

| Round | Date, seed | Offices: checked, wrong, rate | Brands: checked, wrong, rate | Fabricated |
| --- | --- | --- | --- | --- |
| 1 | 2026-10-24, 20261024 | 46, 2, 4.3% | 39, 4, 10.3% | none |
| 2 | 2026-10-24, 20261025 | 42, 1, 2.4% | 29, 8, 27.6% | none |
| 3 | 2026-10-24, 20261026 | 39, 0, 0% | 30, 3, 10.0% | none |
| 4 | 2026-10-24, 20261027 | 38, 0, 0% | 41, 0, 0% | none |
| 5 | 2026-10-24, 20261028 | not run (offices met the rule at round 4) | 46, 1, 2.2% | none |
| 6 (stage 3, contacts merged) | 2026-10-24, 20261106 | 90, 1, 1.1% | 97, 5, 5.2% | none |
| 7 | 2026-10-24, 20261107 | 73, 1, 1.4% | 89, 2, 2.2% | none |
| 8 | 2026-10-24, 20261108 | 81, 0, 0% | 90, 1, 1.1% | none |
| Daily-view audit | 2026-10-24 | 29, 0, 0% (3 rows) | 56, 0, 0% (7 rows) | none |

Stage 1 met the stop rule before contacts existed (offices rounds 3 and 4, brands rounds 4 and 5). Stage 3 merged 210 contact rows and changed scores, so the loop restarted on the merged tables: rounds 6, 7 and 8 are each under 10% with nothing fabricated, so the rule is met twice over (6 and 7, 7 and 8). Round 7 also exposed a missed hard gate, which led to a scan of every passed brand (below), so round 8 ran after that fix as the confirming round. The daily-view audit then covered every row in today's two views that no stage-3 round had drawn.

## Round 6 (stage 3; seed 20261106)

### Offices (10 rows from the top 50)

| Row | Company | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AO-C-034 | Cognitiv | address (own contact page: 215 Park Ave S, Floor 16), in cluster (pin inside; re-geocoded 26 m away, also inside), headcount 170 (Built In), attendance (hybrid 3 days: "in person Monday through Wednesday"), gate arithmetic (56 to 114), primary name and title (Jason Pellegrino, SVP, People, own About page), New York base, title grade (adjacent), backup (Rebecca Aliab D., VP Business Operations, The Org) | 10 of 10 |
| AO-C-085 | Empathy | address (CO 2024-03: 56 West 22nd Street), in cluster, headcount 200, attendance (3 days; "onsite Tuesdays and Thursdays"), gate, primary (Nafissatou Babylas Ndiaye, Head of People, US, The Org), New York base (Brooklyn, New York), title grade | 9 of 9 |
| AO-C-052 | Bombas | address (Built In: 881 Broadway; CO 2019), in cluster, headcount 223, attendance (on-site 5 days), gate, primary (Carlos Arellano, Workplace Coordinator, The Org, New York City), New York base, title grade (exact), backup (Melissa King, Executive Assistant) | 10 of 10. The Org record dates from 2024-11-14; `check_before_send` asks to confirm. |
| AO-C-050 | Global Trading Systems | address (CO 2024-11: 35,156 sf at 625 Avenue of the Americas), in cluster, headcount 420, attendance (on-site 5 days), gate | 5 of 5. Observation: Built In still lists HQ at 545 Madison Ave and GTS's own locations page returned 403. No contact is named (walk-in), so the walk-in confirms the address. |
| AO-C-151 | Carbyne | address (Connect CRE: second floor of 45 West 27th Street; Built In agrees), in cluster, headcount 180, attendance (hybrid, flexible), gate, parent (Axon, stage-3 correction), primary (Tami Golan, Chief People Officer, carbyne.com Our Team), New York base (unconfirmed: no city on the page), title grade | 10 of 10 |
| AO-C-061 | Daily Harvest | address (Built In: 37 West 20th Street), in cluster, headcount 267, attendance (offices page: 5 days), gate, primary (Jessica Lawson, Chief of Staff, The Org, record 2024-03-04, flagged), New York base, title grade | 9 of 9 |
| AO-C-155 | Primary Wave | address (own contact page: 1165 Broadway, 5th Floor; CO 2026-03), in cluster, headcount 109, attendance (Built In says Remote Workplace on an unclaimed profile), gate, primary (Sophia Popovits, NY Facilities and Culture Manager, own team page), New York base, title grade (exact), backup (Shevonne James, Senior HR Manager) | 10 of 10 |
| AO-C-030 | Prepared 911 | address (CO 2025-08: 7K sf at 101 Fifth Avenue), in cluster, headcount 77, attendance (on-site 5 days), gate, parent (Axon), primary (Miranda Lee, Chief of Staff, The Org, New York), New York base, title grade | 10 of 10. Observation: Built In lists HQ at 575 Lexington Ave; the row is already occupancy-unconfirmed. |
| AO-C-001 | HUMAN Security | address (CO 2024-06 and Built In: 841 Broadway), in cluster, headcount 393, attendance (hybrid, not specified), gate, primary (Jackie Orris, Chief People Officer, The Org, New York City), New York base, title grade | 9 of 9 |
| AO-C-013 | Rockwell Group | address (own About page: 5 Union Square West, 8th Floor), in cluster, headcount 350 ("350-person firm"), gate, primary (Yazmin Ramirez, Director of Human Resources, own People page), New York base, title grade | **7 of 8. 1 error:** `contact_ny_base` read "confirmed" from the note's mention of the New York office; the page gives no city for her, so it is "likely". |

Offices: 90 fields, 1 wrong, **1.1%**. Nothing fabricated.

### Brands (10 rows from the top 60)

| Row | Brand | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AB-071 | Fine & Raw | retailer and grade (Whole Foods NoMad catalog, live: 4 bars), ten blocks (inside), shelf-stable "likely" (no figure published, as recorded), health gate (no structure or function wording on the homepage), primary name and title (Daniel Sklaar: "established ... by Daniel Sklaar"), why-now (Josh Cellars pairing, published 2026-10-15 in the store feed), HQ Brooklyn, online store | 9 of 9 |
| AB-002 | Zack's Mighty | retailer (3 chips), ten blocks, shelf-stable, health gate, primary name (Snack and Bakery), primary title, backup (Kate Scofield, Senior Brand Manager, The Org), why-now (variety pack page), HQ Brooklyn (CB Insights), online store | **9 of 10. 1 error:** title "Founder and CEO"; the opened article says only "founded by"; "CEO" came from a search result. Now "Founder". |
| AB-077 | Fruition Chocolate Works | retailer (3 bars), ten blocks, shelf-stable, health gate, primary (Bryan Graham, founder, own Our Story page), title, backup name (Dahlia, Boston Globe), backup title, why-now (Boston Globe 2026-02-24 pop-up), HQ Shokan NY, online store | **10 of 11. 1 error:** backup title "Co-owner"; the Globe says only "With his wife, Dahlia, they craft chocolate". Now "Title not stated". |
| AB-266 | Gigantic (Candy Deluxe) | retailer and grade (the brand's Stockist locator: Fairway Market, 766 6th Avenue, brand_claim), ten blocks (B-R-003, inside), shelf-stable, health gate, primary (Stu Davidoff: "founded by", Grit Daily), title, why-now (Startup CPG pavilion list), HQ state (SFFS directory: "State: New York"), online store | 9 of 9 |
| AB-001 | BjornQorn | retailer (3), ten blocks, shelf-stable ("best by" on each bag), health gate, primary name and title, backup, why-now (BjornQorn Ruby page), online store | 9 of 9. The cited 2019 article calls the pair "popcorn makers"; the brand's own About page ("BJORN & JAMIE") now backs the co-founder titles. |
| AB-207 | Stiller's Soda | retailer (2), ten blocks, shelf-stable, health gate, primary (Alex Doman, "co-launched", Food Business News), title, why-now (Beverage Industry 2026-03-30), HQ Brooklyn (privacy policy), online store URL | **8 of 9. 1 error (format):** `online_store_url` held a note ("(Shop buttons route to Amazon)"), so the URL did not open. Notes now sit in `online_store_note` (4 rows fixed). |
| AB-032 | Firehook | retailer (7), ten blocks, shelf-stable (FAQ: "six-month shelf life"), health gate, primary (Maura Mottolese, CEO), title, contact role, backup (Ellen Howse, CMO, FoodNavigator), why-now (Snack and Bakery 2026-07-10), HQ Chantilly VA (FAQ) | **9 of 10. 1 error:** `contact_role` said "founder"; she is CEO and not shown as a founder. The role now follows the title. |
| AB-048 | FitJoy Foods | retailer (Union Square: 3), ten blocks, shelf-stable, health gate, primary (Norman Taliaferro, CEO and Founding Partner, own page), title, backup (Micah Mills, Director of Marketing), why-now, HQ Austin (The Org), online store | 10 of 10 |
| AB-174 | OOSO Sparkling Tea | buy path (online store only), shelf-stable (FAQ: 18 months), health gate, primary (Oliver Spring, CEO and Co-founder, The Org), title, backup (Sophia Racciatti, Co-Founder, "a marketing genius"), why-now (Mint Limeade published 2026-09-17), HQ Brooklyn (terms), online store | 9 of 9 |
| AB-034 | Reelie | retailer (6), ten blocks, shelf-stable, health gate, primary (Juan Nino, Director of Marketing, Target Takeoff 2021), title, contact record date, backup (Jose Nino), why-now (Serrano Lime page), HQ Charlotte NC (About page), online store | **10 of 11. 1 error:** the source is a 2021 interview but `contact_record_date` was blank, so `check_before_send` did not ask to confirm he is still there. Year-only dates are now read. |

Brands: 97 fields, 5 wrong, **5.2%**. Nothing fabricated: the two over-read titles came from a search result and an inference, both written down in the stage-2 notes.

**Fixes after round 6:** New York base from a firm's page with no city is "likely", not "confirmed" (Rockwell, Valon, Primary Venture Partners); year-only and "(2021)"-style source dates are read; notes moved out of `online_store_url` into `online_store_note`; the brand primary's role follows the title ("CEO or owner (not shown as a founder)"); Zack's title, Fruition's backup title and BjornQorn's source corrected in `_work/stage3_contact_fixes.csv`; a live page that replaces a dated one clears the old date.

## Round 7 (seed 20261107)

### Offices

| Row | Company | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AO-C-083 | CompStak | address (CO 2022-12: 675 Avenue of the Americas; Built In: 4th Floor), in cluster, headcount 150, attendance ("3-days in the office and 2 days at home"), gate, primary (Maxine Swick, VP, Head of People, The Org, New York), New York base, title grade, backup (Alyssa Murrett, VP Operations) | 10 of 10 |
| AO-C-047 | The Vita Coco Company | address (CO 2024-09: 23K sf at 111 Fifth Avenue), in cluster, gate, contact status (unverified: the name is only in a search snippet and the cited Datanyze page returned 403, so `first_name` is blank and the row is not ready) | 4 of 4 (the headcount source is sec.gov) |
| AO-C-129 | Activate Consulting | address (CO 2025-09: 11 East 26th Street; Built In: "11 Madison Square North", same building), in cluster, headcount 76, attendance (on-site 5 days), gate (25 to 51, band under-40, so the founder's call), primary (Laura Miller, Chief of Staff, The Org), New York base, title grade, backup (Frank Noto, Chief Administrative Officer) | 10 of 10 |
| AO-C-095 | Foursquare | address (Built In: 50 West 23rd Street; NYREJ tenant list), in cluster, headcount 350, attendance (flexible), gate (HQ unknown by B's rule: Built In says New York, Revelio says San Francisco), primary (Kristin Vera, Senior Manager, Executive & Office Operations, EA to the CEO, The Org), New York base, title grade (exact), backup (Pam Thomas, Chief of Staff) | 10 of 10 |
| AO-C-059 | Christie's International Real Estate Group | address (CO 2024-08: "a 75-person office" on the ninth floor of 156 Fifth Avenue), in cluster, headcount 75 (New York office), gate (75 x 67% = 50), primary (Melissa True, "Team Leader, Christie's Flatiron Office", Mann Report 2025-09-15), New York base, title grade, backup (Brett Forman, Managing Director, Manhattan, CO 2024-08) | **8 of 9. 1 error:** New York base "likely" though her title names the Flatiron office. A title that names the New York office now confirms it. |
| AO-C-109 | Green Mountain Energy | address (CO 2026-01: "the New York City offices of Green Mountain Energy" at 16 Madison Square West), in cluster, headcount 334, attendance, gate | 5 of 5 |
| AO-C-033 | Baseten | in cluster, headcount 350, attendance (hybrid 3 days), gate | 4 of 4 (the address source is sec.gov; Built In gives no New York street) |
| AO-C-028 | Valon | address (CO 2026-08 and REBusiness: the entire fourth floor of 860 Broadway), in cluster, headcount 529 (Revelio), attendance, gate (57% rate for 501 to 4,999), primary (Marisa Rackson, Head of People, own About page), New York base ("likely" after the round-6 fix), title grade, backup (Ariel Brito, Chief of Staff) | 10 of 10 |
| AO-C-079 | PlayPlay | address (CO 2025-05 names PlayPlay a tenant of 53-55 West 21st Street), in cluster, headcount 230, attendance (policy: "3 days at the office"), gate | 5 of 5 |
| AO-C-213 | Fenwick & West | address (CO 2026-06: 73K sf at 902 Broadway; Built In: 18th Floor), in cluster, headcount 1,176, attendance, gate (34 to 670 crosses 250, passes with the flag), why-now (CO 2026-06-16) | 6 of 6 |

Offices: 73 fields, 1 wrong, **1.4%**. Nothing fabricated.

### Brands

| Row | Brand | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AB-075 | Eleni's New York | retailer (NoMad: 3 Crisp cookies), ten blocks, shelf-stable (FAQ: 9 and 6 months), health gate, primary name (The Org), title, online store | 7 of 7 (the why-now page returned 403 today: not counted) |
| AB-082 | Steve & Andy's | retailer (3), ten blocks, shelf-stable (FAQ: "270 days from date of production"), health gate, primary and backup ("Founders Steve Marino and Arjan 'Andy' Khiani"), titles, why-now (Ginger Snap on the homepage), HQ New York, online store | 10 of 10 |
| AB-027 | Biena | retailer (7), ten blocks, shelf-stable, health gate (nutrient wording only), primary (Poorvi Patodia, Founder and CEO), title, backup (Samantha Sieloff, The Org), why-now (single-serve 9-pack page), HQ Boston, online store | 10 of 10 |
| AB-106 | Taza Chocolate | retailer (6), ten blocks, shelf-stable "likely", health gate, primary (Alex Whitmore, founder and CEO), title, backup status (unverified: LinkedIn only), why-now (store feed items published 2026-09-04), online store | 9 of 9 |
| AB-096 | Magic Spoon | retailer (cereal only, as noted), ten blocks, shelf-stable "likely", health gate, primary (Gabi Lewis, Co-Founder, The Org), title, backup status, why-now, HQ, online store | **9 of 10. 1 error:** HQ "New York" rested on the terms of service, which give only an arbitration venue. The Org shows "Headquarters New York" and is now the source. |
| AB-073 | Seed + Mill | retailer (Pistachio Halva), ten blocks, shelf-stable (FAQ: 4 to 6 months, no refrigeration), health gate, primary (Rachel Simons, CEO and Co-Founder, press kit), title, backup (Lisa Mendelson: "the three co-founders"), HQ, online store | 9 of 9 |
| AB-278 | Doosra | buy path (online), shelf-stable, health gate, primary (Kartik Das signs the brand's story), title, why-now (The Gift Box in the store feed), online store | 7 of 7 |
| AB-088 | Jonesbar | retailer (5 bars), ten blocks, shelf-stable "likely", health gate, primary ("taylor jones - founder/ceo"), title, HQ Wall Township NJ, online store | 8 of 8 |
| AB-090 | Maxine's Heavenly | retailer (2), ten blocks, shelf-stable (FAQ: about 11 months), health gate, primary (press page: "Its founder Robert Petrarca", "our CEO"), title, why-now (Gingerbread published 2026-10-13), HQ Los Angeles, online store | 9 of 9 |
| AB-080 | Spring & Mulberry | retailer (4 bars), ten blocks, shelf-stable (FAQ: 12 to 16 months), health-claim gate, primary (Kathryn, Founders page), title, backup (Sarah), why-now (Salted Almond on the homepage), HQ Raleigh, online store | **9 of 10. 1 error (gate):** the homepage says dates "help regulate digestion, slow the absorption of naturally occurring sugars, and improve gut health", calls the bars "Gut Friendly", and the footer carries the FDA structure/function disclaimer. That is an explicit health claim: the brand now fails the gate. |

Brands: 89 fields, 2 wrong, **2.2%**. Nothing fabricated (the health-claim miss was a researcher's founder-review call, not an invented value).

**Fixes after round 7:** the Spring & Mulberry gate; a title naming the New York office confirms the New York base; Magic Spoon's HQ source. The gate miss was systemic (the gate relied on researcher flags), so every passed brand's homepage was scanned (next section).

### Health-claim scan of every passed brand (after round 7)

`_build/scan_claims.py` opened the homepage of all 244 brands that had passed (241 returned 200; 2 returned 403 and 1 returned 429) and listed every phrase that ties a product to a body function or a condition, with its context (`_work/claims_scan_2026-10-24.csv`). Each hit got a human verdict:

| Verdict | Brands | Why |
| --- | --- | --- |
| Fail the health-claim gate | Spring & Mulberry; CHUH Matcha ("support your immune system daily"); NuGo Nutrition (bars sold in Diabetes, Dialysis, GLP-1, Digestive Health and Gut Health collections); Joolies ("fiber to support digestion and keep things moving"); Maine Crisp Co. ("anti-inflammatory") | The brand's own copy states an effect on the body or targets a medical condition |
| Founder review, quote added | Harken Sweets and Magic Spoon ("gut-friendly"), Laurel's ("Gut Friendly"), Bobo's and Kate's Real Food (blog posts on digestion and prebiotic fiber), Taply (a customer review mentions prebiotics) | Implied, not stated; blog or review copy rather than the brand's product claim |
| False positive | Saffron Road ("reduce stress" for chickens), Spirited Zero Proof ("No Adaptogens") | Not a product claim |

Passed brands fell from 244 to 239. Vermont Nut Free Chocolates entered the top 60; its contacts were re-opened that day (About page: "founders Mark and Gail Elvidge").

## Round 8 (seed 20261108, after the scan)

### Offices

| Row | Company | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AO-C-160 | K Health | address (K Health terms: "387 Park Ave South, 9th Floor"), in cluster, headcount 363, attendance (on-site 5 days), gate, primary (Naomy Ambroise, People Operations Generalist, The Org, New York City), New York base, title grade (exact), backup (Ana Ramos, VP of Operations) | 10 of 10. Built In still shows 298 5th Ave; B resolved the conflict to 387 Park Ave S. |
| AO-C-091 | 1stDibs | address (user agreement: 300 Park Avenue South, 10th Floor), in cluster, headcount 455, attendance (policy text: teams set days), gate, primary (Lindsay Cusatis, EA to the CEO; Manager, The Org, New York), New York base, title grade (exact), backup (Maura Bermingham, People Business Partner) | 10 of 10 |
| AO-C-096 | Inspiren | address (CO 2026-09: a full floor at 61 West 23rd Street), in cluster, headcount 150, attendance, gate, primary (Jared Zimmer, Chief of Staff to CCO, The Org, New York City), New York base, title grade, why-now (CO 2026-09-21) | 10 of 10 |
| AO-C-048 | Aterian | address (Built In: 37 E 18th Street), in cluster, headcount 122, attendance (on-site 5 days), gate | 5 of 5 |
| AO-C-007 | Personetics | address (NYREJ: 7,004 sf at 853 Broadway), in cluster, headcount 371, attendance, gate | 5 of 5 (Built In still lists 1216 Broadway; already occupancy-unconfirmed) |
| AO-C-098 | BrainPOP | address (terms of use: "71 W 23rd St., 17th Fl."), in cluster, headcount 225, attendance (flexible), gate, primary (Lilly Santiago, EA to the CEO and Office Coordinator, The Org, no location), New York base (unconfirmed), title grade (adjacent: a target title without a New York base), backup (Crystal Spence, Operations Lead, Office of CEO) | 10 of 10 |
| AO-C-111 | Wellcom Worldwide | address (CO 2024-08: 24K sf at 16 Madison Square West), in cluster, headcount 336, attendance, gate, primary (Jillian Cruz, EA to Global CEO, The Org, no location), New York base, title grade | 9 of 9 (Built In lists 1115 Broadway; occupancy-unconfirmed already) |
| AO-C-133 | Order.co | address (CO 2026-02: 12K sf sublease at 11 East 26th Street), lease status (signed, not occupied: held), in cluster, headcount 165, attendance, gate, primary (Karen Bedell, VP, People, The Org, New York), New York base, title grade, backup (Ali Sardinia), why-now | 11 of 11 |
| AO-C-072 | Actively AI | address (CO 2025-04 and own site: 30 West 21st Street, 9th Floor), in cluster, headcount 65, attendance, gate (22 to 56: founder's call) | 5 of 5 |
| AO-C-055 | Stash | address (CO 2026-09: 12K sf at 641 Avenue of the Americas), in cluster, headcount 380, attendance, gate, why-now (CO 2026-09-02) | 6 of 6 (held: still in a WeWork until the move; Built In lists 75 Varick Street) |

Offices: 81 fields, 0 wrong, **0%**. Nothing fabricated.

### Brands

| Row | Brand | Fields re-checked (source) | Result |
| --- | --- | --- | --- |
| AB-070 | Raaka Chocolate | retailer (Union Square: 9), ten blocks, shelf-stable (wholesale FAQ: 9 and 16 months), health gate, primary (Nathan Hodge: The Org CEO, earlier "Head Chocolate Maker, Co-Founder"), title, backup (William Mullan, Brand Manager), why-now (Fall Collection, Limited Batch), online store | 9 of 9 |
| AB-003 | PRETZELIZED | retailer (4), ten blocks, shelf-stable, health gate, primary (Sammy Kestenbaum: press page "CEO"; podcast page "Co-Founder & CEO"), title, backup status (unverified), why-now (Snack and Bakery 2026-08-05), online store N (product pages route to Amazon) | 9 of 9 |
| AB-210 | Treat House | retailer (3), ten blocks, shelf-stable (store feed: "6 month shelf life"), health gate, primary (Chris Russell, DNAinfo 2015: "the owners of Treat House, Chris and Jennifer Russell"), title, contact record date, backup (Jennifer Russell: "co-founder and co-creator"), HQ Woodside (privacy policy), online store | **9 of 10. 1 error:** the sources are 2015 to 2017 but `contact_record_date` was blank, so there was no "confirm still there" check. Publisher-year dates are now read. |
| AB-058 | Jack & Friends | retailer (3), ten blocks, shelf-stable, health gate, primary (About: "our founder, Jessica Kwong"; The Org: Founder & CEO, 2026-06-12), title, HQ New York | 7 of 7 |
| AB-172 | Explorer Cold Brew | buy path (online), shelf-stable "unknown" (no storage statement, as recorded), health gate, primary (Cason Crane, Founder & CEO, team page), title, backup (Michael O'Hagan, The Org), why-now (2026 Shelfie finalists), HQ Brooklyn, online store | 9 of 9 |
| AB-117 | GoMacro | retailer (34), ten blocks, shelf-stable "likely", health gate, primary (Jola Sonkin, CEO and Co-Founder, The Org), title, backup (Dan Hickle, SVP, Head of Marketing), why-now (Snack and Bakery 2026-06-09), HQ Viola WI, online store | 10 of 10 |
| AB-217 | UMAMI GRANOLA | buy path (online), shelf-stable, health gate, primary (Cindy Lam, Founder, Startup CPG release), title, why-now (2026-08-20 retail debut at Chelsea Market, outside the ten blocks as recorded), HQ Brooklyn, online store | 8 of 8 |
| AB-286 | Vermont Nut Free Chocolates | retailer (Union Square: 2), ten blocks, shelf-stable, health gate, primary and backup (About: "founders Mark and Gail Elvidge"), titles, why-now (Snack Packs published 2026-09-11), online store | 9 of 9 |
| AB-220 | Unhinged | buy path (online), shelf-stable "unknown", health gate, primary (Byron Sorrells, co-founder, Startup CPG release), title, backup status (unverified; the directory page returned 403), why-now (2026-10-09 pre-seed), HQ (New York, unverified: a mailbox suite), online store | 9 of 9 |
| AB-105 | Unreal | retailer (16), ten blocks, shelf-stable (FAQ: 12 to 18 months), health gate, primary (Michael Bronner, Wikipedia founders), title, backup (Kevin McCarthy, CEO), why-now (Snack and Bakery 2026-03-18), HQ Boston, online store | 10 of 10 |

Brands: 90 fields, 1 wrong, **1.1%**. Nothing fabricated.

## Daily-view audit (every row in today's views that no stage-3 round drew)

| Row | Name | Fields re-checked | Result |
| --- | --- | --- | --- |
| AO-C-035 | Global Strategy Group | address (own locations page: 215 Park Avenue South, 15th Floor), in cluster, headcount 187, attendance (on-site 5), gate, primary (Joan McHugh-Ward, "Manager, HQ-Office Services", own team page), New York base, title grade (exact), backup (Liana Kane, Senior Executive Assistant to CEO, own page) | 10 of 10 |
| AO-C-037 | Nayya | address (NYREJ: 29,915 sf at 215 Park Ave South), in cluster, headcount 150, attendance (3 days), gate, primary (Phoebe Waxman, Senior People Operations Analyst, The Org, New York City), New York base, title grade (exact), backup (Amber Hewko, Executive Assistant) | 10 of 10 |
| AO-C-031 | Dashlane | address (terms: "44 West 18th Street"; CO 2019), in cluster, headcount 284, attendance (flexible), gate, primary (Caroline Lee, Workplace Experience Specialist, The Org, New York), New York base, title grade (exact) | 9 of 9 |
| AB-219 | The Lucky Ox | retailer (NoMad: Pandan Coconut Sparkler), ten blocks, shelf-stable (canned), health gate, primary (Fane He, Co-founder, The Org), title, backup (Kyle Nguyen), why-now (Startup CPG 2026-05-01), online store | 9 of 9 |
| AB-216 | The Matzo Project | retailer (Union Square: 2), ten blocks, shelf-stable, health gate, primary (Kevin Rodriguez, "Co-Founder", Startup CPG release), title, backup (Crystal Bennett, "a spokeswoman", FoodNavigator; partner per the brand's homepage), why-now (Passover release 2026-02-18) | 8 of 8 |
| AB-111 | Harken Sweets | retailer (NoMad: 1), ten blocks, shelf-stable "likely", health gate (founder review: "gut-friendly"), primary (Katie Lefkowitz, Startup CPG "Founder Feature"), title, why-now (Snack and Bakery 2026-05-14), HQ New York, online store | 9 of 9 |
| AB-249 | Häppy Candy | retailer (NoMad: 2 gummies), ten blocks, health gate, primary (Maxi Heidenblut, "Founder & CEO", Startup CPG release), title, why-now (Target launch 2026-09-10), HQ (terms: "P.O. Box 4, NYC"), online store | 8 of 8 |
| AB-097 | Beyond Good | retailer (NoMad: 7), ten blocks, shelf-stable "likely", health gate, primary (Tim McCollum, Founder and CEO, The Org), title, backup (Kristine Ford, Head of Marketing), why-now (store listing), HQ Brooklyn (Wikipedia), online store | 10 of 10 |
| AB-081 | Mezcla | retailer (NoMad: 13 bars), ten blocks, shelf-stable "likely", health gate, primary (Griffin Spolansky, Co-Founder and CEO, The Org), title, backup (Michelle Brintnall Chester, VP Marketing), why-now (Green Queen: $9.5M Series B), HQ ("New York-based"; terms: 885 Third Avenue), online store | 10 of 10 |
| AB-233 | Simply Gum | retailer (NoMad: 5), primary (About: "Our founder, Caron") | 2 of 2 |

Offices 29 of 29, brands 56 of 56: **0%**.

**Outbound critique after the audit (no data error, a scoring gap):** the stage-1 scale rules read only the researcher's founder-review note, so scale signals written into a why-now ("in 9,000+ US stores", a Series B, Costco) earned no penalty. The rules now also read the why-now: 4,000 or more doors or stores, a Series B or later, or Costco take the existing scale type (-12); a national Target or Walmart launch below that adds a founder-review note only. Mezcla (72 to 64) and Harken Sweets (77 to 69) left the brand daily view; Zack's Mighty (checked in round 6) and Simply Gum (audited above) entered.

