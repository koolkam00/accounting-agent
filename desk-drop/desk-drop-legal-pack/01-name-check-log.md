**Draft for attorney review. Not legal advice.**

# 01 · Name-check log: trademark, state entity and domains

Version 0.6 · 2026-10-24

**The name being checked.** `BRAND_NAME = Desk Drop` (working name, not cleared). This is the only place in this file where the name is set. Every search below used this name and its spellings: "desk drop", "deskdrop", "desk-drop", "desk drops", "deskdrops". To check a new name, change this line, rerun every row of the log, and keep this version as history.

**What it is for.** The plan's week-1 name check (Phase 0, "Week 1, days 1 and 2"): USPTO trademark search, New York Department of State entity search, and .com and .nyc domains. The result gates any print run (workstream D) and any public launch (workstream C). The short copy at `name-check-log.md` points here.

**When it is used.** Week 1, before any card is printed or domain bought (Mon 2026-10-26 to Tue 2026-10-27, derived, founder to confirm). Rerun the USPTO and domain rows on the day before any print order, domain purchase or public launch, because both change daily.

**What a search result can and cannot tell you.** A search shows what a database held on one day. It cannot clear a name. Unregistered businesses can hold rights from use alone, databases lag, and a lawyer judges whether two names are close enough to confuse buyers. Each row below says what it does not prove.

---

## Gate status

| Gate | Status on 2026-10-23 | Meaning |
| --- | --- | --- |
| Print run (D) | **HOLD** | Do not order printed cards, case labels or signage with the working name until the founder decides on the name. See "Decision needed". |
| Public launch (C) | **HOLD** | No public website or social profile under the working name until the same decision. |
| Private discovery calls | Go | Using the working name in one-to-one discovery conversations is low exposure. This is a judgment, not legal advice; the attorney can say otherwise. |

## What the checks found, in plain words

1. **A business already trades as "DeskDrop" in an adjacent market.** The site thedeskdrop.com (deskdrop.co and trydeskdrop.com redirect to it) sells "custom-branded chocolate gifts" in jars, shipped to business recipients' desks, with a \$995 pilot for 25 gifts and "Nationwide shipping". It shows a 312 telephone area code (Chicago) and "© 2026 DeskDrop". Both businesses would deliver food to offices under the same two words. It has no USPTO filing that the searches found, but a business can hold rights from use alone. This is the main risk.
2. **The USPTO has no live mark with both words, and treated them as descriptive.** The one filing with both words, DESK-DROP (serial 99174501, Elior, Inc.), covered online food ordering and "food and drink ... featuring office delivery". The USPTO refused it in a first Office action because the mark "merely describes" the services. Elior asked for more time (granted 2025-12-29), then did not respond, and the application was abandoned on 2026-03-31. The examiner also wrote that a search "found no conflicting marks". In plain terms: the USPTO read "desk drop" as describing delivery to where people work. A federal registration of the working name for this business may meet the same refusal, and a descriptive name is hard to stop others from using.
3. **The .com is taken; the .nyc looks open.** deskdrop.com has been registered since 2004 (no website answered). deskdrop.co is registered and points to the chocolate business above. deskdrop.nyc and deskdropnyc.com returned "not found" in the registries' own lookup services.
4. **No New York entity uses the name.** The Department of State's own open register shows no active or past entity under any of the three spellings searched. The only name with both words is DROPDESK LLC (Nassau County, 2017). The Department's web search could not be run from here; the founder runs it (row 12).

## Decision needed (blocking for D and C, not for discovery)

Keep the working name, or pick a fallback before anything is printed or filed? The plan's own rule is that if the working name is taken, "pick a fallback now rather than after printing cards". Nobody has registered it, but another business uses it for food gifts delivered to offices, and the USPTO has called it descriptive.

**Recommended default:** treat it as taken. In week 1, shortlist two fallback names, preferably coined or unusual words rather than descriptions, and run this whole log on each (about an hour per name; the steps below and `_work/namecheck/scripts/` make it repeatable). Choose by the end of week 3 (Fri 2026-11-13, derived), before the LLC is filed. Keep the working name only if the attorney, shown this log, says the risk is acceptable. The attorney hour (`08-attorney-hour-agenda.md`, item 1) is set for week 4, before the filing day, so that answer arrives before the LLC name is fixed. The LLC name is the costly one to change later: an amendment is \$60 (LLC Law §1101(g), opened 2026-10-23), plus new bank, insurance and agreement paperwork. Until you decide, private discovery calls under the working name can go ahead.

## For the attorney hour

Both questions are item 1 of `08-attorney-hour-agenda.md`, the single agenda for the hour.

1. Does the existing "DeskDrop" chocolate-gifting business (thedeskdrop.com) create a likelihood-of-confusion risk for the working name, used for office snack sampling in New York? What would a fuller clearance search cost?
2. Given the USPTO's descriptiveness refusal of DESK-DROP for office food delivery (serial 99174501, Office action of 2025-09-30), is a federal application for the working name worth \$350 per class (USPTO fee schedule, opened 2026-10-23), or should the business pick a more distinctive name now?

---

## The log

All times UTC on 2026-10-23. Raw responses are saved under `_work/namecheck/` (paths in the last column). "Verbatim" means copied from the response or page, not summarized.

### USPTO trademark search (tmsearch.uspto.gov)

The page sits behind an automated challenge that plain `curl` cannot pass, so headless Chromium typed each query into the search box, the way a person would, and the search request the page sent was saved.

| # | Time | Query (Wordmark field) | Result, verbatim | What it does not prove | Raw file |
| --- | --- | --- | --- | --- | --- |
| 1 | 23:31:52 | `desk drop`, sent as a URL parameter | Page showed "No results found" but sent no search request. **Void: the query never ran.** Kept for the record; superseded by row 2. | Nothing | `uspto/tm_deskdrop_space_page.txt` |
| 2 | 23:32:31 | `desk drop` | "5,032 results for desk drop" (any record with either word). Top result: wordmark "DESK-DROP", status "DEAD" "ABANDONED", serial 99174501, owner "Elior, Inc. (CORPORATION; Delaware, USA)", classes 035 and 043, goods and services "(ABANDONED) IC 035: On-line ordering services featuring food and drink; Online ordering services in the field of restaurant take-out and delivery." and "(ABANDONED) IC 043: ... Providing of food and drink via cafe and restaurants featuring office delivery; ... Catering services; Mobile catering services; Corporate event catering." Filed 2025-05-07, basis 1(b) intent to use, abandoned 2026-03-31. | Unregistered use (common-law rights); marks filed in the last few days; foreign marks; state marks; whether a similar-sounding mark would be held confusing | `uspto/tm_deskdrop_typed_api.json`, `uspto/tm_deskdrop_typed.png` |
| 3 | 23:33:23 | `deskdrop` | "No results found" (search request sent; response `"totalValue":0`) | Same as row 2 | `uspto/tm_deskdrop_oneword_api.json` |
| 4 | 23:33:41 | `desk drops` | "2,756 results for desk drops" (either word); no mark with both words in the top results | Same as row 2 | `uspto/tm_deskdrops_space_api.json` |
| 5 | 23:33:59 | `deskdrops` | "No results found" (`"totalValue":0`) | Same as row 2 | `uspto/tm_deskdrops_oneword_api.json` |
| 6 | 23:34:41 | Both words required, any order, in the wordmark field (same search service, query written by hand) | `total=1`: 99174501 DESK-DROP, dead | Same as row 2 | `uspto/tm_custom_queries.json` |
| 7 | 23:34:41 | Both words required, in the "pseudo mark" field, which spells out run-together words | `total=2`: 99174501 DESK-DROP (dead) and 87516183 "DROPDESK", owner an individual (named in the USPTO record; not copied here), registration 5782323, live, IC 036 "Providing co-working facilities, namely, rental of offices for co-working ..." | Same as row 2. DROPDESK reverses the words and covers co-working office rental, a different service; whether it matters is the attorney's call | `uspto/tm_custom_queries.json`, `uspto/tm_control_queries.json` |
| 8 | 23:34:41 and 23:35:09 | Wildcard `*deskdrop*` (catches DESKDROP inside longer marks), with a control query `*dropdesk*` | `*deskdrop*`: `total=0` in both fields. Control `*dropdesk*`: `total=1` (DROPDESK), so the wildcard works | Same as row 2 | `uspto/tm_custom_queries.json`, `uspto/tm_control_queries.json` |
| 9 | 23:35:31 | TSDR status page for serial 99174501 (tsdr.uspto.gov/statusview/sn99174501) | "Status: Abandoned because the applicant failed to respond or filed a late response to an Office action." "Date Abandoned: Mar. 31, 2026". Prosecution history: "NON-FINAL ACTION E-MAILED" Sep. 30, 2025; "APPLICATION EXTENSION GRANTED/RECEIPT PROVIDED" Dec. 29, 2025; "ABANDONMENT - FAILURE TO RESPOND OR LATE RESPONSE" Apr. 14, 2026 | Whether Elior uses the name in commerce or will refile | `uspto/tsdr_99174501.html` |
| 10 | 23:36:19 | The Office action itself (document NFIN20250930172716, issue date September 30, 2025) | "SUMMARY OF ISSUES: Section 2(e)(1) Merely Descriptive Refusal". "The trademark examining attorney searched the USPTO database of registered and pending marks and found no conflicting marks that would bar registration under Trademark Act Section 2(d)." "... the mark immediately indicates to consumers that the applicant's services features and/or is offered in connection with delivery to the tables, counters, stands or booths at which people work." "... DESK-DROP, is refused registration because it is merely descriptive of the applicant's goods and/or services under Trademark Act Section 2(e)(1)." | How an examiner would treat the working name for this business's services (brand sampling and reporting, not food delivery). It is a strong signal, not a ruling on our application | `uspto/oa/OfficeAction7869279.pdf`, `.txt` |

### New York Department of State entity search

| # | Time | Search | Result, verbatim | What it does not prove | Raw file |
| --- | --- | --- | --- | --- | --- |
| 11 | 23:37:12 | Public Inquiry web search, apps.dos.ny.gov/publicInquiry/ | **Not run.** `curl`: "Empty reply from server". Headless Chromium: HTTP 200, then a bot-protection challenge that reloads without showing the search form. We did not try to get around it. | Nothing | `nydos/dos_home.txt` |
| 12 | Founder | Same web search | **Not run, founder to run.** Steps below. | | |
| 13 | 23:37:53 | Department of State open data, "Active Corporations: Beginning 1800" (data.ny.gov dataset n9v6-gdp6, attribution "New York State Department of State", rows updated 2026-10-23T12:32:32Z), entity names containing `DESK DROP`, `DESKDROP` or `DESK-DROP` | `[]` (0 rows) for each of the three | Inactive entities; assumed names (d/b/a); filings after the dataset's monthly cut-off; whether the Department would accept the name (it decides at filing); out-of-state businesses not registered in New York, such as the chocolate business in finding 1 | `nydos/q_desk_drop.json`, `q_deskdrop.json`, `q_desk-drop.json` |
| 14 | 23:37:53 | Same dataset, names containing both `DESK` and `DROP` | 1 row: `5169826 \| DROPDESK LLC \| 2017-07-13 \| Nassau \| New York \| DOMESTIC LIMITED LIABILITY COMPANY`. Control query `ELIOR%` returned 7 rows, so the query works | Same as row 13 | `nydos/q_desk_and_drop.json`, `q_control_elior.json` |
| 15 | 23:38:24 | "All Filings - Name Status History" (dataset ekwr-p59j: 7,520,527 current and past entity names, active and inactive) | Both words: 1 row, `DROPDESK LLC`, filed 2017-07-13, status A | Assumed names (this table holds entity names only); same limits as row 13 | `nydos/names_desk_drop.json` |
| 16 | 23:38:24 | "Daily Corporation and Other Entity Filing Data" (dataset k4vb-judh; latest filing date in it 2026-10-22), entity or fictitious name with both words | `[]` (0 rows) | Filings on 2026-10-23 or later | `nydos/daily_desk_drop.json` |

### Domains (RDAP, the registries' own lookup service)

RDAP "404 Not found" means the registry holds no record today. It is not a promise the name can be bought: registries reserve or price some names, and someone can register it first.

| # | Time | Domain | Registry server | Result, verbatim | What it does not prove | Raw file |
| --- | --- | --- | --- | --- | --- | --- |
| 17 | 23:30:08 | deskdrop.com | rdap.verisign.com/com/v1 | HTTP 200. `"ldhName":"DESKDROP.COM"`, `"status":["active"]`, registration `2004-01-31T21:33:02Z`, expiration `2027-01-31T21:33:02Z`, registrar `Squarespace Domains II LLC`. A request to https://deskdrop.com got "Connection reset by peer" (no site seen) | Who owns it (registrant details are withheld) or whether it is for sale | `rdap_deskdrop.com.json` |
| 18 | 23:30:08 | deskdropnyc.com | Verisign | HTTP 404, empty body | Availability at a registrar | `rdap_deskdropnyc.com.json` |
| 19 | 23:30:08 | desk-drop.com | Verisign | HTTP 404, empty body | Same | `rdap_desk-drop.com.json` |
| 20 | 23:30:08 | thedeskdrop.com | Verisign | HTTP 200, registered `2026-03-08T21:38:24Z`, registrar `GoDaddy.com, LLC`. Serves the "DeskDrop" chocolate-gifting site in finding 1 | | `rdap_thedeskdrop.com.json`, `sites/thedeskdrop.com.html` |
| 21 | 23:30:08 | getdeskdrop.com | Verisign | HTTP 200, registered `2026-10-15T16:57:36Z`, registrar `Cloudflare, Inc.`. Serves an unrelated desk-lamp waitlist page | | `rdap_getdeskdrop.com.json` |
| 22 | 23:30:56 | trydeskdrop.com | Verisign | HTTP 200, registered `2026-07-06T05:33:09Z`, GoDaddy. Redirects to thedeskdrop.com | | `rdap_trydeskdrop.com.json` |
| 23 | 23:30:56 | deskdropco.com | Verisign | HTTP 200, registered `2026-03-22T14:14:59Z`, registrar `Tucows Domains Inc.`. Page title "Store unavailable" | | `rdap_deskdropco.com.json` |
| 24 | 23:30:56 | deskdrophq.com, mydeskdrop.com | Verisign | HTTP 404 each | Availability at a registrar | `rdap_deskdrophq.com.json`, `rdap_mydeskdrop.com.json` |
| 25 | 23:30:56 | deskdrop.net | rdap.verisign.com/net/v1 | HTTP 404 | Same | `rdap_deskdrop.net.json` |
| 26 | 23:30:25 | deskdrop.nyc | rdap.nic.nyc (from the IANA list data.iana.org/rdap/dns.json, published 2026-10-22T23:00:04Z) | HTTP 404. `"errorCode":404,"title":"Not found","description":["No data found"]`. Control: nic.nyc returned HTTP 200, so the server answers | Availability; .nyc may also require a New York City address (registry rule, unverified, founder to confirm at checkout) | `rdap_deskdrop.nyc.json`, `pc_nic.nyc.json` |
| 27 | 23:30:25 | deskdropnyc.nyc | rdap.nic.nyc | HTTP 404, "No data found" | Same | `rdap_deskdropnyc.nyc.json` |
| 28 | 23:30:45 | deskdrop.co | No .co server is listed by IANA; rdap.nic.co was refused by this session's network. Used a public DNS lookup instead (cloudflare-dns.com) | Name servers `ns03.domaincontrol.com.` and `ns04.domaincontrol.com.`, so the name is registered. https://deskdrop.co redirects to thedeskdrop.com | Registration dates (no RDAP record seen) | `sites/deskdrop.co.html`, `sites/deskdrop_co.png` |

---

**Rerun check, 2026-10-24 00:04:51 UTC.** `_work/namecheck/scripts/name_check.py` with the name above reran rows 3, 6, 7, 8 (USPTO, plus an exact-phrase search: 1 result, DESK-DROP, dead), 13 to 16 (Department of State data) and 17, 18, 19, 25, 26, 27 (domains) in one pass. Every result matched the rows above (raw files in `_work/namecheck/runs/deskdrop-20261024T000451Z/`). To check a fallback name, run the same command with the new name from the `desk-drop/` folder; it prints a table in this log's format and lists what it cannot run.

## Steps for the founder (rows marked "not run")

**Row 12. Department of State web search** (about 5 minutes, no login).
1. Open https://apps.dos.ny.gov/publicInquiry/ in a normal browser.
2. Search by entity name for `DESK DROP`, then `DESKDROP`. If the form offers a choice of "begins with", "contains" or "exact", use "contains". If it offers "active" or "all", choose "all" (labels unverified; the page could not be opened here).
3. If it has an assumed-name search, repeat both searches there.
4. Write the date, the exact query and the result, word for word, into a new row of this log. A screenshot is enough.
5. What it will not prove: that the Department will accept the name when you file. It decides at filing. The written name-availability search costs \$5 per name (dos.ny.gov Articles of Organization page, opened 2026-10-23), and a name can be reserved for \$20 (LLC Law §1101(a), opened 2026-10-23). Neither is needed if the online filing accepts the name.

**Before you buy a domain** (about 10 minutes, needs your registrar login, spend stops for your written yes).
1. Check the exact name at your registrar. Note the price shown, including any "premium" price and the renewal price, and stop there.
2. For .nyc, check the residency rule at checkout (unverified here).
3. Add the result as a row in this log with the date.

**The day before any print order or public launch** (about 20 minutes, no login).
1. Rerun rows 2 to 8 at https://tmsearch.uspto.gov: type each spelling into the Wordmark search and note the result count and any new live mark with both words.
2. Rerun the .com and .nyc rows (17 to 27): paste `https://rdap.verisign.com/com/v1/domain/<name>.com` and `https://rdap.nic.nyc/domain/<name>.nyc` into a browser, or run the script above.
3. Search the open web and Instagram for the name plus "snack", "office" and "New York", and write down any business using it. This is the common-law check that no database covers.

## Changelog

- Round 1 (2026-10-23): ran all searches that can be run from here (USPTO, TSDR and Office action, three Department of State datasets, 13 domains); logged the void first USPTO attempt; marked the Department web search founder-to-run.
- Round 2 (2026-10-24), trademark-attorney pass: recommended default changed from "keep for now" to "treat as taken, shortlist two fallbacks, decide before filing", following the plan's own rule; the name now appears only in its definition line and in the literal search queries; corrected "on office desks" to "to offices"; added rerun scripts.
- Round 3 (2026-10-24), full read: "refused" now says it was a first Office action followed by abandonment; the other business is described as selling "food gifts delivered to offices"; the individual owner of DROPDESK is no longer named (business data only); rerun coverage stated row by row; dollar signs escaped so tables render.
- Round 4 (2026-10-24), final full read: wording only (".nyc may require", "kept for the record", domain count 13, rerun step names the .com and .nyc rows).
- Merge (2026-10-24): version 0.5; the name line now uses the pack-wide `BRAND_NAME` form and the name appears once; the attorney question points to file 08, held in week 4 before filing.
- Review round 1 (2026-10-24), version 0.6: finding 2 now records Elior's granted extension (TSDR, 2025-12-29) before the abandonment, as row 9 already did.
