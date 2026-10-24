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

## Rounds 1 to 5 (stage 1, before contacts existed; carried from `_work/spotcheck-log.md`)

Method, every round: draw ten rows per table at random from the current top list (Python `random.sample`, seed named per round), re-open every source the row cites (curl GET with a generic User-Agent; pages saved in `_work/fetch/spotcheck/<round>/`), and compare field by field. Count errors as fields wrong over fields actually re-checked. A field counts as checked only if its source was opened in this round. sec.gov and LinkedIn are never opened (privacy rule and bot block); a row resting on them is checked on its other sources. "Fabricated" means a value no opened source supports and no note marks as unverified.

### Stage 1, round 1 (2026-10-24, seed 20261024; samples in `_work/spotcheck_r1_offices_sample.csv` and `_work/spotcheck_r1_brands_sample.csv`)

#### Offices (10 rows from the top 50)

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

#### Brands (10 rows from the top 60)

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

#### Fixes made after round 1
1. Built In parser: the employer's own policy sentence now overrides the "typical time on-site" box when they disagree (Radar to hybrid 4 days, PlayPlay to hybrid 3 days, 1stDibs to hybrid, days not stated). All 105 cached pages re-parsed.
2. Brands: a person who is both co-founder and marketing lead fills one slot; the backup is the next co-founder. Titles are singular per slot ("Co-founder", "Owner").
3. Brands: a researcher's parenthetical about a name (spelling, first name only) is kept in `contact_note`; where it records the page spelling, the page spelling is used.
4. Corrections with sources in `_work/stage1_corrections.csv` (Strip Jerky why-now re-sourced; Sweet Loren's refrigerated why-now removed).

### Stage 1, round 2 (2026-10-24, seed 20261025, round-1 rows excluded; samples in `_work/spotcheck_r2_*_sample.csv`)

#### Offices (10 rows from the top 50)

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

#### Brands (10 rows from the top 60)

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

#### Fixes made after round 2
1. Why-now type: a why-now on the brand's own domain (product page, homepage, own press page) is now a "listing", never "press". 112 passed rows are listings, 74 press.
2. Contacts: only strings that look like a person's name fill a contact slot (no "family", "team", roles or phrases); "Also" and stray punctuation split names; each person gets the title written for them ("Name: Title; Name2: Title2" cells); the contact source is the page that supports the name (the enrichment source when the name came from enrichment); a LinkedIn URL seen only in search results goes to `contact_linkedin_url` with `linkedin_status = search result, not opened` and never replaces the opened source; a name whose only page is LinkedIn is `unverified`.
3. Maxine's Heavenly title corrected to CEO (`_work/stage1_corrections.csv`).
4. Built In parser: "2-3 days" (lower figure), "twice a week", "3 in-office days", "hybrid 3 days" and named weekdays are read from the policy text; `tuesday_named_in_policy` = Y where the employer names Tuesday as an office day (+3 attendance points, capped at 15).
5. Offices: `hold_before_outreach` and `hold_reason` carry B's instructions: signed-not-occupied (check the lobby directory), an unresolved address conflict (address points 0), a coworking tenant until its move, a possibly-closed site.

### Stage 1, round 3 (2026-10-24, seed 20261026, rounds 1 and 2 excluded; samples in `_work/spotcheck_r3_*_sample.csv`)

#### Offices (10 rows from the top 50)

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

#### Brands (10 rows from the top 60)

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

#### Fixes made after round 3
1. Contact status now depends only on the name: the name cell, its note and whether the name itself came from a snippet. Doubt about a title alone no longer blanks a verified name (Stiller's, Magic Spoon and Beyond Good now verified; their sources are opened pages).
2. A why-now whose text says unverified, snippet or not opened is typed `unverified` and earns no points (6 passed rows).

### Stage 1, round 4 (2026-10-24, seed 20261027, rounds 1 to 3 excluded; samples in `_work/spotcheck_r4_*_sample.csv`)

#### Offices (10 rows from the top 50)

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

#### Brands (10 rows from the top 60)

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

### Stage 1, round 5 (2026-10-24, seed 20261028, brands only, rounds 1 to 4 excluded; sample in `_work/spotcheck_r5_brands_sample.csv`)

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

#### Fix made after round 5: automated re-check of every Whole Foods link
Because a catalog listing moved between 2026-10-23 and 2026-10-24, every Whole Foods `store_selector` link (272, across 4 stores) was re-queried on 2026-10-24 with the same public store-scoped endpoint (`_build/recheck_wfm.py`; results in `_work/wfm_recheck_2026-10-24.csv`). Matching is strict (all of one name's distinctive words in the other's; a first pass that matched on one shared word, for example "Vermont", was re-run), and a link not found is retried by brand name and alias. Result: 261 found, 11 not found (Mamame 2, MASA Chips 3, SuperSeedz NoMad, Maine Crisp Co., Pip's Heirloom Snacks 4). Those 11 links are now `unverified` with the reason in `brand_store_links.csv`; the brand's nearest store moved to the next graded store where one exists. Catalogs change daily, so the daily routine re-checks a brand's store link before it is used in copy.

### Stage 1 summary by round

| Round | Offices: fields checked, wrong, rate | Brands: fields checked, wrong, rate | Fabricated |
| --- | --- | --- | --- |
| 1 | 46, 2, 4.3% | 39, 4, 10.3% | none |
| 2 | 42, 1, 2.4% | 29, 8, 27.6% | none |
| 3 | 39, 0, 0% | 30, 3, 10.0% | none |
| 4 | 38, 0, 0% | 41, 0, 0% | none |
| 5 | not run (offices met the stop rule at round 4) | 46, 1, 2.2% | none |
