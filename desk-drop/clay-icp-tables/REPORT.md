# Report back: Clay ICP tables (workstream A)

2026-10-24, after independent review round 1. Paths are relative to `desk-drop/`. Nothing was sent, posted, bought, signed up for or deployed, and no connector wrote anywhere. LinkedIn and sec.gov were never opened, and every page was fetched with a generic User-Agent and no personal identifier.

## What I built, and where

The review found two blockers:
- the health-claim gate had read only homepages;
- the Friday Clay-to-Sheet paste could bring an opted-out row back into the daily view.

Both are fixed, and the tables were rebuilt and spot-checked twice more.

There was no Clay or Google login, so the tables are a Google Sheets workbook plus Clay import files, with a build sheet to set them up in about 30 minutes.

All files are in `clay-icp-tables/`:

- **`clay-icp-tables.xlsx`**: the table of record, to upload to Google Sheets. Its tabs are:
  - Offices and Brands;
  - Daily view - Offices and Daily view - Brands;
  - Walk list - Offices (top-50 offices with nobody named);
  - Founder review - Brands;
  - Enrichment (the one place Clay or Hunter email results are pasted);
  - Dictionary, Scoring and Routine.
  The contact shown, emails, channel, score, `score_reason`, readiness and every view are formulas, filled to row 1000, and the views use INDEX/MATCH (no SORT or FILTER). If anyone pastes over a table tab, every view goes blank with a warning instead of showing stale rows. The working name lives in one cell, `Routine!B1`.
- **`clay-build-sheet.md`**: the short document. It covers the hard gates and scoring in plain words, the column dictionary, the morning routine and Friday prep, seeding and refresh, Clay setup (import steps, four research prompts, the email waterfall spec) and running cost.
- **`offices.csv`, `brands.csv`**: the full tables, gated-out rows kept with their reasons.
- **`daily-view-offices.csv`, `daily-view-brands.csv`, `walk-list-offices.csv`, `founder-review-brands.csv`**: today's views as files.
- **`clay-import/offices-clay-import.csv`, `clay-import/brands-clay-import.csv`**: 175 passed rows per table for Clay Free, every ready row first. They carry research and contact columns only: no status, founder control, formula or tracking column.
- **`column-dictionary.csv`**: 240 entries.
- **`spot-check-log.md`**: rounds 1 to 10, the daily-view audit, the review's sample, both health-claim scans and the re-timed routine.
- **`README.md`, `HANDOFF.md`**: HANDOFF covers what A takes from B, D, G and H and gives to E and H, its deviations from CONTRACTS, and the open decisions.
- **`_review/round-1.md`**: the review, with a Builder response for every finding.
- **`_build/`**: the build, run with `python3 -B clay-icp-tables/_build/build_all.py`. `test_workbook.py` recalculates the workbook in LibreOffice and compares every formula and view with a Python copy of the same logic in five scenarios. It passes on LibreOffice 24.2 and 25.8 (`_work/test_workbook/last_run_lo242.txt`, `last_run_lo258.txt`).
- **`_work/`**: research, sourced corrections, scans, spot-check evidence and every opened page.

## Counts

| | Offices | Brands |
| --- | --- | --- |
| Found | 308 (276 companies from B's `companies.csv` and `near_miss.csv`, 32 coworking sites) | 311 |
| Passed the hard gates | 243 (224 companies, 19 coworking sites) | 196 |
| Gated out | 65: Tuesday estimate over 250 (34), outside the cluster (14), in coworking (5), in coworking until a move (2), operator pantry control not shown (5), estimate under 30 (4), no staffed office (1) | 115: health claim 81, no buy path 21, not shelf-stable 18, excluded category 18 (some rows fail more than one) |
| Top list | Top 50 | Top 60 |
| Primary contact named, top list | 34: 10 on the employer's own page or dated press, 24 only on The Org (`crowd-listed`) | 57: 46 on the brand's page or dated press, 9 crowd-listed, 2 first name only |
| Backup named, top list | 23 | 36 (25 marketing leads) |
| Person LinkedIn URL | 1 (a top-50 backup); 0 primaries | 10 top-60 primaries (16 primaries and 5 backups in all) |
| Company LinkedIn URL | 181 of 276 companies (41 of the top 50; 159 linked from the company's own site, 22 from its The Org record) | not collected |
| Ready for outreach | 38 (30 in the top 50), plus 13 on the Walk list | 66 (30 in the top 60). 107 passed brands, 29 of them in the top 60, wait on a blocking founder review |
| Top-list retailer grades | n/a | store_selector 37, brand_claim 8, unverified 15 |
| Startup CPG member flag | unknown | Y on 70 rows (17 in the top 60) |
| **Verified work emails** | **0 of 50** | **0 of 60** |

**Verified email share: 0 of 110 (0%).** The waterfall needs your Clay or Hunter login, and agents never guess an address. 33 office and 55 brand primaries have a full name and a domain, ready for the waterfall.

**Office supply.** At five office first touches a day from E's first cold day (Mon 2026-11-09), the 38 ready rows last until about Thu 2026-11-19. 49 of office ranks 1 to 100 name a person today. The build sheet makes refilling the pool (Claygent on ranks 51 to 100, plus the Walk list) a dated task.

## Spot-check error rate, by round

Error rate = fields wrong / fields checked, with every source opened that round.

| Round | Offices | Brands | Fabricated |
| --- | --- | --- | --- |
| 1 (stage 1) | 46 checked, 2 wrong, 4.3% | 39, 4, 10.3% | none |
| 2 | 42, 1, 2.4% | 29, 8, 27.6% | none |
| 3 | 39, 0, 0% | 30, 3, 10.0% | none |
| 4 | 38, 0, 0% | 41, 0, 0% | none |
| 5 | not run (offices met the rule at round 4) | 46, 1, 2.2% | none |
| 6 (stage 3, contacts merged) | 90, 1, 1.1% | 97, 5, 5.2% | none |
| 7 | 73, 1, 1.4% | 89, 2, 2.2% | none |
| 8 | 81, 0, 0% | 90, 1, 1.1% | none |
| Daily-view audit | 29, 0, 0% | 56, 0, 0% | none |
| Independent review, round 1 (reviewer's sample) | 74, 3, 4.1% | 70, 1, 1.4% | none |
| 9 (after the review fixes) | 98, 0, 0% | 82, 2, 2.4% | none |
| 10 | 75, 2, 2.7% | 76, 1, 1.3% | none |

The stop rule (two rounds in a row with nothing fabricated and under 10% error) is met three times:
- in stage 1: offices rounds 3 and 4, brands rounds 4 and 5;
- in stage 3: rounds 6 to 8;
- after the review fixes: rounds 9 and 10.

The routine is now estimated at about 12 to 13 minutes a morning plus a 60-to-90-minute Friday prep. That is an estimate from a walk without logins, so time it in the first live week.

The ten-row rounds could not see that the claims gate read only homepages; the review caught it. Rounds 9 and 10 therefore drew five rows per table from what the fixes changed, and opened product pages for the brand gate.

## Credits used and running cost

- Clay credits: none. Hunter credits: none. Paid plans: none. Web searches this round: none.
- Page requests this round, all free public pages fetched one at a time:
  - the claims scan: 1,309 requests, 957 answered;
  - The Org pages and companies' own sites for contacts and company LinkedIn links;
  - lease articles for square footage;
  - spot-check sources.
- **Recommended running cost: $0 a month**: Google Sheets in the existing Workspace seat, Clay Free, Hunter Free.
- If you give a written yes: one month of Hunter Starter ($49 a month, or $34 a month billed yearly; hunter.io/pricing, 2026-10-24) gets all 88 emails at once.
- Clay Launch ($185 a month, or $167 a month billed yearly; clay.com/pricing, 2026-10-24) is over the plan's $60 software cap and is not recommended.

## Numbered assumptions

1. No Clay or Google login exists. The Google Sheet made from `clay-icp-tables.xlsx` is the only table of record, permanently. Clay is the research and email engine and holds no status. This deviates from CONTRACTS, which puts status in Clay; status still lives in one place only.
2. Office rows are B's companies and near-miss rows plus B's coworking sites. 276 companies exceed the 200 target, so nothing was added from B's raw slices.
3. A company-wide headcount is split by New York share. The New York office holds 50% to 100% of it if the HQ is in New York, and 5% to 100% if the HQ is elsewhere or unknown. These are planning bounds; intake replaces them.
4. In-office rate: 67% for firms of 500 or fewer, 57% for 501 to 4,999, 46% for 5,000+. These are the plan's Partnership for New York City figures, with no Tuesday uplift.
5. The hard size gate removes a row only when the whole estimated range is under 30 or over 250. A range that crosses a line passes with a flag.
6. Space check: the Tuesday estimate never exceeds what the row's own sourced leased square footage seats. The high end is at most sf / 125 and the central figure at most sf / 150. Where the headcount math exceeds the space, the range comes from the space (sf / 250 to sf / 125). A lease article's square footage is taken to be the New York space at that address. Square footage that rests on sec.gov is unverified, founder to confirm.
7. Two disagreeing sourced headcounts define a range rather than "unknown".
8. On Built In, the employer's policy sentence outranks the "typical time on-site" box, and a day range uses its lower figure.
9. A coworking site is one office only if the operator is shown to control the pantry; `unknown` control fails. A company still in coworking until a move fails the coworking gate until the move is confirmed.
10. B's holds (signed-not-occupied, address conflict, moving out, possibly closed) keep the row ranked but out of outreach until the lobby check clears it.
11. Office why-now is a lease reported since 2025-11 in an article about the company itself.
12. Retailer grades:
    - `store_selector` is kept only for a retailer's own store-scoped catalog (Whole Foods). A listing the catalog no longer shows becomes `unverified`.
    - Pop Up Grocer is `brand_claim` at most.
    - Store catalogs change daily, so the store line is re-checked weekly (`retailer_checked_date`).
13. "Within ten blocks" is B's measure (794 m of grid walking from the boundary), applied to every store.
14. An Amazon or retailer storefront linked from the brand's own site counts as an online store. Whether a discount code is possible is for intake.
15. A company projection or a press quote can set the revenue band, and `revenue_band_type` says which.
16. Health-claim gate:
    - It is brand-level and reads the brand's own selling copy: homepage, product pages and catalog descriptions, About, FAQ and ingredient pages.
    - It fails a brand on structure/function or disease wording, a published testimonial that names a disease, CBD products, or the FDA supplement disclaimer.
    - Implied or educational wording, or a functional ingredient with no claim seen, goes to a blocking founder review.
    - Nutrient wording passes.
17. Founder-review types and penalties:
    - Types are sorted by pattern from the researcher's wording and the why-now; only the most severe type sets the penalty.
    - Blocking types: owner, scale, heritage, dormant, perishable risk, alcohol-adjacent, no single-serve pack, functional or implied-effect wording.
    - Information only: nutrient wording, under $500k, a single-serve pack not yet shown, an unstated shelf life, a store-only buy path.
18. The primary brand contact is the founder (the likely budget owner at this size). The backup is the marketing lead, else the next co-founder or executive.
19. A name fills `first_name` only when an opened page shows it. A name whose only source is The Org is `crowd-listed`, because The Org prints "Unverified" beside every person. It counts as ready, ranks below employer-page names at equal score, and is confirmed by the founder on LinkedIn on Friday.
20. A company LinkedIn URL linked from the company's own site or its The Org record is recorded without opening LinkedIn. Person-level URLs are pasted by the founder, never taken from search snippets.
21. Startup CPG participation adds no points and is never a hook (E's rule).
22. New York brands come first: a New York City HQ earns 20 points against 3 for a brand outside the Northeast.
23. Ten rows per view; the founder sends about five per side a day. The Friday prep covers the next 25 eligible rows per side, which is enough for a week at that pace.
24. Referral rows are warm. The founder writes to them directly with E's referral message (08, part 2) and sets `status = queued`; they do not wait in the cold daily view. A queued colleague blocks the rest of that company.
25. E's first cold day is Mon 2026-11-09 (E's sending setup), which sets the office pool's run-out date.

## Changelog (one line per round)

- **Stage 1, round 0** (draft): merged B's 276 companies and 32 coworking sites with the five brand slices and 768 enrichment updates. Built gates, the onsite estimate, the ten-block test, re-grades and both scores. Read Built In attendance for the passed offices that cite it.
- **Stage 1, round 1** (self-critique): raised the penalties for sourced revenue over $10M and for big-company owners. Penalized remote offices. Limited office why-now to the company's own lease article. Undid a duplicate-name false positive. Checked online stores for 12 buy-path failures.
- **Stage 1, round 2** (after spot check 1): employer policy text now overrides the Built In days box. One person can no longer fill both contact slots. Re-sourced two why-nows.
- **Stage 1, round 3** (after spot check 2): own-site why-nows are typed as listings. Contacts are limited to real names on supporting pages. Search results never replace an opened source. Carried B's holds.
- **Stage 1, round 4** (after spot check 3): a doubtful title no longer unverifies a name, and unverified why-nows earn nothing.
- **Stage 1, round 5** (after spot check 4): New York weight raised to 20 points.
- **Stage 1, round 6** (after spot check 5): every Whole Foods link re-queried with strict matching; 11 links became `unverified`.
- **Stage 2** (contacts): researched contacts from employer team pages, The Org, and press and podcast pages; LinkedIn never opened.
- **Stage 3, round 7** (after spot check 6): New York base "likely" when a page shows no city. Read year-only source dates. Moved online-store notes to their own column. Primary role follows the title. Three contact fixes, sourced.
- **Stage 3, round 8** (after spot check 7): failed Spring & Mulberry on the claims gate. A homepage claims scan of every passed brand failed 5 more (244 to 239 passed).
- **Stage 3, round 9** (after spot check 8 and the daily-view audit): scale signals in a why-now (4,000+ doors, Series B, Costco) now take the scale penalty.
- **Review round 1** (independent review, 2 blockers, 8 majors, 9 minors; fixes checked by spot checks 9 and 10):
  - Claims scan of every passed brand's catalog, About and FAQ pages: 43 fail and 20 go to a blocking review.
  - The Sheet is the only table of record, Clay holds no status, emails come back via the Enrichment tab, and the views have a paste guard.
  - Space check on the Tuesday estimate (100 rows; 5 new square-footage sources).
  - `crowd-listed` contact status for The Org-only names.
  - `dnc_any` across company groups, strict drop-downs and a red flag when status and do-not-contact disagree.
  - Formula `score_reason` and `channel` (warm-intro).
  - Company LinkedIn URLs for 181 companies. 18 office primaries and 8 backups researched; ready offices up from 26 to 38.
  - New tabs: Walk list and Founder review.
  - New controls: `promote_backup`, `review_blocking` and `founder_review_cleared`, `retailer_checked_date` with one-click `retailer_check_url`, and the Friday prep.
  - Views rebuilt as INDEX/MATCH, so they compute in any app; tests on LibreOffice 24.2 and 25.8, including a paste-over scenario and referral rows.
  - Coworking websites from the operator's domain only, and source types from the source domain.
  - Lobby type `unknown` without a source; why-nows without a link and date moved to notes; the coworking-until-move gate.
  - 15 why-now links re-pointed to product pages; 8 online stores confirmed; Orbital's and Joe Coffee's contact labels corrected.
  - README, HANDOFF and the build sheet rewritten, and a builder response written for every finding.

## Blocking questions (with my recommended default)

1. **Which Google account and which Clay account or workspace should the tables be shared with?**
   - Default: upload `clay-icp-tables.xlsx` to your own business Google account ([EMAIL]) as a private Google Sheet.
   - Create a Clay Free workspace under the same address and import the two `clay-import/` files.
   - Share with no one else until you say so.
2. **Should a health claim on some of a brand's products fail the whole brand, or only those products?**
   - Default (applied now): the whole brand fails, so 43 brands are out, consistent with Spring & Mulberry.
   - The alternative adds an `eligible_skus` column and re-admits some of them for their claim-free products only.
3. **May I treat the free email waterfall and the Claygent research as approved (no spend), and do you want to pay for Hunter Starter?**
   - Default: Clay Free plus Hunter Free, run on the 88 named top-list primaries over two months, and Claygent on office ranks 51 to 100 before Thu 2026-11-19, all within the free allowances.
   - Hunter Starter ($49, one month) only with your written yes.
4. **How should the founder-review backlog be cleared?**
   - Default: clear the top 30 of the 107 blocking brand reviews on the first Friday (Founder review tab).
   - The rest stay out of the daily view until cleared.
5. **Are the planning bounds for office size right?** These are the New York share (50% to 100% with a New York HQ, 5% to 100% otherwise) and 125 to 250 square feet per person for the space check.
   - Default: keep them until intake replaces the estimates.
   - Changing them moves about a dozen offices across the 30 and 250 lines.
