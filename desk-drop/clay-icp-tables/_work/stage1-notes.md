# Stage 1 notes: assemble, gate and score

Workstream A, stage 1 of 3, 2026-10-24. Paths are relative to `desk-drop/`.

**No Clay account was available.** Per the brief's freedom clause, this stage builds import-ready CSVs (and, in later stages, a build sheet the founder imports in about 30 minutes). Nothing was sent, posted, bought or signed up for. No Clay credits were used. No paid enrichment ran on any row. All web reads were free GET requests with a generic User-Agent and no personal identifier; sec.gov and LinkedIn were never opened.

## Files this stage wrote

| File | What it is |
| --- | --- |
| `clay-icp-tables/offices.csv` | Every office row (308), gated-out rows included with `gate_result = fail` and `gate_reason`. CONTRACTS 6.2 stable columns first, then rank, gates, the prompt's columns and the score parts. |
| `clay-icp-tables/brands.csv` | Every brand row (311), gated-out rows included. Same layout. |
| `clay-icp-tables/_work/top50_offices.csv` | The 50 highest-scored offices that passed the gates, ranked, with `row_id` and the contact fields (empty until stage 2). |
| `clay-icp-tables/_work/top60_brands.csv` | The 60 highest-scored brands that passed the gates, ranked, with `row_id` and the contact fields found so far. |
| `clay-icp-tables/_work/brand_store_links.csv` | Every brand-to-store link (441): research grade, re-grade and why, blocks outside the cluster, how the store was placed. |
| `clay-icp-tables/_work/attendance_builtin.csv` | The Built In offices page read for each passed office that cites Built In (105): workplace type, typical days, the employer's policy text, job tags, Tuesday named. |
| `clay-icp-tables/_work/wfm_recheck_2026-10-24.csv` | Every Whole Foods `store_selector` link re-queried on 2026-10-24 against the store's own catalog. |
| `clay-icp-tables/_work/online_store_checks.csv`, `stage1_corrections.csv` | Field updates this stage made, each with its source, date and reason. |
| `clay-icp-tables/_work/store_geocodes.json` | Stores not in B's list, placed with `_shared/geocode.py` (NYC GeoSearch). |
| `clay-icp-tables/_work/spotcheck-log.md` and `spotcheck_r*_sample.csv` | The spot-check log by round and the rows drawn. Pages opened are in `_work/fetch/`. |
| `clay-icp-tables/_build/*.py` | The build: `build_all.py` runs `build_offices.py` and `build_brands.py`; `config.py` holds every weight and rate; `fetch_builtin_attendance.py` and `recheck_wfm.py` are the two free fetch steps; `peek.py` is the spot-check helper; `stage1_counts.py` prints the counts below. |

Rebuild: `python3 -B clay-icp-tables/_build/build_all.py` (seconds; no network unless a new store needs a geocode). Row IDs are stable: offices use B's IDs (`AO-C-###` from `B-C-###`, `AO-W-###` from `B-W-###`); brands use `AB-###` from `_build/id_registry_brands.json`, keyed on domain.

## Offices: method

**Rows.** Every company in B's `companies.csv` (168: 162 candidates, 5 coworking members, 1 not an office) and `near_miss.csv` (108) is a row: 276 companies, over the 200 target, so nothing was added from `cluster-1-flatiron/_work/companies_S*.csv`. The 32 coworking sites in `coworking.csv` are also rows (`org_type = coworking-operator`), because the plan lets an operator join as one office if it controls the pantry. No row is unsourced: every one carries B's address source and date.

**Hard gates, applied before any enrichment.** A row fails if any of these holds; all failing reasons are listed in `gate_reason`.
1. Outside the cluster: B's `in_boundary = N` against `cluster-1-flatiron/boundary.geojson` (6 near-miss rows 0.1 to 1.7 blocks out; 8 coworking sites just outside the line).
2. Inside a coworking space: B's `in_coworking = Y` (5 rows, with the site ID).
3. No staffed office at the address: B's `excluded-not-office` (1 row, Augury).
4. Tuesday estimate under 30: the whole estimated range is below 30.
5. Tuesday estimate over 250: the whole estimated range is above 250.
6. Coworking operator rows only: operator control of the pantry not shown (`pantry_control` is not `operator`), or B marks the site possibly closed.
A range that straddles 30 or 250 passes, with `onsite_flags` saying so ("may be under 30", "may exceed 250"). Unknown headcount is not gated on size.

**Tuesday onsite estimate** (`onsite_low`, `onsite_high`, `onsite_central`, `onsite_band`, `onsite_confidence`, `onsite_basis`, all labelled "estimate until intake replaces it"):
- Headcount: the sourced count(s) in B's row (`headcount_count`, `headcount_second_count`, `company_wide_count_cited`). One count gives low = high; two that disagree give the range between them (so B's 22 "disagree" rows get a wide estimate instead of none). Band edges are used only when a band has no count. No count and no band: onsite `unknown`.
- New York share: 100% when the count is for the New York office (`headcount_scope = nyc-office`). Otherwise the count is company-wide and the share is unknown, so the range widens and confidence is `low`: 50% to 100% when the HQ is New York, 5% to 100% when the HQ is elsewhere or unknown (assumption A3).
- In-office rate (plan.md, Partnership for New York City, March 2025): 67% for firms with 500 or fewer staff; 57% (the all-firm Manhattan figure, since the plan gives none for 500 to 4,999) for 501 to 4,999; 46% for 5,000 or more. Tuesday is the peak day, so these understate Tuesday a little.
- low = smallest count x low share x rate; high = largest count x high share x rate; central = the square root of low x high (the middle of the range on a ratio scale). `onsite_band` is the CONTRACTS band holding the central figure.
- Worked example, Dashlane (AO-C-031): counts 284 (Built In) and 319 (Revelio), HQ New York: 284 x 50% x 67% = 95; 319 x 100% x 67% = 214; central 143, band 76-150, low confidence.

**Attendance signals** (`attendance_signal`, `attendance_evidence`, `attendance_source_url`, `attendance_source_date`, `tuesday_named_in_policy`) come only from sources already in B's rows or a page fetched here: B's notes (for example "on-site 5 days a week", "remote-first"), then, for passed rows only, the Built In offices page the row already cites (105 pages, opened 2026-10-24, cached). Built In shows a workplace type, a "typical time on-site" box, the employer's own policy sentence and recent job tags ("In-Office", "Hybrid", "Remote"). When the policy sentence and the box disagree, the sentence wins (Radar says Monday to Thursday; PlayPlay 3 days; 1stDibs "Flex First"); a range ("2-3 days") uses the lower figure. Anything else is `unknown`. Built In profiles are employer-edited and undated.

**Holds** (`hold_before_outreach`, `hold_reason`) carry B's instructions: a signed-not-occupied lease (check the lobby directory before outreach), an unresolved address conflict (Pumpkin), a tenant still in a coworking space until its move (Stash, Agentio), a possibly-closed site. A held row keeps its score and rank; the daily view will skip it until the walk clears it.

**Office why-now**: a lease reported in leasing press since 2025-11 whose article is about this company (its name in the article's URL), else blank. 51 rows.

**Score (0 to 100) and plain words.** "Score is how likely this office fits the drop and can say yes, from what is known today."

| Part | Points | Rule |
| --- | --- | --- |
| Onsite band | 0 to 30 | 25 x the share of the Tuesday range inside 40 to 250 (ratio scale), plus 5 when the count is for the New York office itself. Unknown headcount: 7. |
| Company size under 500 | 0 to 15 | Largest company-wide count: 500 or fewer 15; 501 to 1,000 6; 1,001 to 4,999 2; 5,000+ 0; unknown 8. Minus 4 when B names a controlling parent. |
| Attendance signals | -5 to 15 | On-site 5 days 15; hybrid 4 days 12; 3 days 10; days not stated 7; 2 days or fewer 5; no signal 6; remote -5. Plus 3 when the policy names Tuesday as an office day (cap 15). |
| Address and occupancy | 0 to 15 | Occupied 10, occupancy-unconfirmed 5, signed-not-occupied 2 (coworking site: open 10, open-unverified 5, unverified 2); 0 with an unresolved address conflict. Plus confidence high 5, medium 3, low 0. |
| Title match | 0 to 10 | Primary contact title in the target family (Office Manager, Workplace Experience Manager, Head of Workplace, People Operations, Executive Assistant to the CEO) 10; adjacent 5. 0 for every row until stage 2 finds contacts. |
| Known to founder | 0 or 15 | `known_to_founder = Y`. N for every row until the founder marks one. |

A gated-out row scores 0 (`score_raw` keeps what it would have scored). Ties break on the share of the range inside 40 to 250, then confidence, then name. `score_reason` is one sentence built from the parts. All weights live in `_build/config.py`.

## Brands: method

**Merge and enrichment.** BR1 to BR5 (311 rows) were merged with each row's slice and line kept (`research_slice`, `slice_row`). Every row of `enrich_BR1_BR2.csv`, `enrich_BR3.csv` and `enrich_BR4.csv` (768) was applied as a field update to the one matching brand in its slice, in file order (later rows win), "(append)" rows appended; each update is logged in `enrichment_log` with its source URL, date and confidence (opened or snippet-unverified). BR5 has no enrichment file. Stage 1 then applied its own checks with sources: online-store evidence for 8 brands that would otherwise fail the buy-path gate (`_work/online_store_checks.csv`) and spot-check corrections (`_work/stage1_corrections.csv`).

**Deduplication** on normalized name and website domain: same domain, or same name with one side lacking a domain, is a duplicate. No duplicates remained (the slices had already deduped); one pair with the same normalized name and different domains ((P)RiND, eatprind.com, and RIND Snacks, rindsnacks.com) are different companies and both stay.

**Hard gates** (`gate_result`, `gate_failed`, `gate_reason`):
1. Excluded category: alcohol, cannabis or hemp, supplements, needs preparation (from the researcher's exclusion reason).
2. Explicit health claim: structure or function wording on the brand's own copy (CONTRACTS section 4). Nutrient-content claims are not a gate; they set `founder_review`.
3. Not shelf-stable: refrigerated, frozen or under 60 days, or `shelf_stable = N`. `likely` and `unknown` pass with `founder_review` ("60-day shelf life not stated").
4. No buy path: no graded store (`store_selector` or `brand_claim`) within ten blocks of the cluster and no online store shown.

**Evidence re-grade (CONTRACTS section 4).** `store_selector` stays only where the retailer's own store-scoped catalog lists the brand at that store (the Whole Foods catalog). Pop Up Grocer's directory lists brands, not SKUs, at 205 Bleecker St, outside the band, so it is `brand_claim` at most and never near-cluster. A listing that "does not confirm this store or item" is `unverified`. Nothing is `seen_on_shelf`. Every Whole Foods `store_selector` link was re-queried on 2026-10-24 (`recheck_wfm.py`): a link the store's catalog no longer shows became `unverified`.

**Within ten blocks** uses B's own definition and code: ten street-block lengths (794 m) of grid walking from the nearest boundary edge (`cluster-1-flatiron/_build/boundary.py`, imported read-only). Stores in B's `retailers.csv` take B's `blocks_outside`; others were geocoded with `_shared/geocode.py` and measured the same way. Chelsea Market (75 9th Ave) is 11.4 blocks out and Whole Foods Manhattan West 13.8, so neither counts.

**`nearest_stocked_retailer`** ("Store, street") is the best graded store within ten blocks: `store_selector` before `brand_claim`, then fewest blocks out. With none, the nearest unverified store within ten blocks is shown with grade `unverified`, else "none found within ten blocks". `retailers_within_ten_blocks` lists every store with grade and distance.

**Why-now.** Kept with its link and date; `why_now_type` is `press` (a third party: trade press, Startup CPG newswire, SFA), `listing` (the brand's own site or store feed, Pop Up Grocer, a store tag), `unverified` (the text says unverified or snippet; no points) or `none`. Older than 365 days does not count.

**Startup CPG flag**: `Y` where a public Startup CPG page shows the brand (newswire release, Shelfie, pavilion, feature), else `unknown`. It records public participation, not membership, and adds no points (no selling inside the community).

**Contacts.** Primary is the founder (the budget owner at a brand this size); backup is the marketing lead, else the next co-founder. Only strings that look like a person fill a slot (not "Guzman family"); each gets the title written for them. `first_name`, `last_name` and `title` are filled only when an opened page supports the name (`contact_status` `verified-page` or `first-name-only`); a snippet-only name stays in `contact_name_as_found` with `contact_status = unverified`. `contact_profile_url` is the opened page that supports the name. A LinkedIn URL from search results sits in `contact_linkedin_url` with `linkedin_status = search result, not opened`.

**Founder review** carries every researcher flag and adds "60-day shelf life not stated" and "no online store". `founder_review_type` sorts the researcher's reason into types; the most severe sets a penalty.

**Score (0 to 100) and plain words.** "Score is how likely this brand fits a founding campaign now: buyable near the offices, New York first, with a reason to sample now and a reachable owner."

| Part | Points | Rule |
| --- | --- | --- |
| Buy path near the cluster | 0 to 25 | Best graded store within ten blocks: store page inside the cluster 25, store page within ten blocks 20, brand locator inside 17, brand locator within ten 13; online store only 6; none 0. |
| New York first | 3 to 20 | HQ New York City 20, rest of New York State 13, Northeast 8, elsewhere 3, unknown 4; minus 3 when a New York HQ is unverified. |
| Why-now | 0 to 15 | Press in the last 180 days 15, 181 to 365 days 8; own listing in 180 days 8, 181 to 365 days 4; none or unverified 0. |
| Revenue band | 0 to 10 | $500k to $10M 10; unknown 5; under $500k 2; over $10M 0. |
| Qualification fit | 0 to 10 | Shelf-stable Y 4, likely 2, unknown 1; individually packaged Y 3, unknown 1; online store Y 3, unknown 1. |
| Contacts | 0 to 10 | Founder named on an opened page 6 (first name only or unverified 3); marketing lead named 4. |
| Known to founder | 0 or 10 | `known_to_founder = Y`. |
| Founder-review penalty | 0 to -35 | Most severe type only: sourced revenue over $10M -35; owned by a large company -25; scale signals above $10M -12; dormant -12; heritage or not emerging -10; perishable risk -8; under the $500k floor -5; alcohol-adjacent -5; borderline claim -4; pack format -4; other -2. |

A gated-out row scores 0. Ties break on grade, then why-now points, then name.

## Counts (2026-10-24, after the last rebuild; `python3 -B clay-icp-tables/_build/stage1_counts.py` reprints them)

### Offices

| Measure | Count |
| --- | --- |
| Found | 308 rows: 276 companies (168 from `companies.csv`, 108 from `near_miss.csv`) and 32 coworking operator sites |
| Passed the hard gates | 241: 222 companies (158 of B's candidates, 64 near-miss firms whose New York office may still fit) and 19 coworking operator sites |
| Gate failures (a row can fail more than one) | Tuesday estimate over 250: 38 (all near-miss firms: HQ New York with 900 or more staff, or HQ elsewhere or unknown with 11,100 or more); outside the cluster: 14 (6 companies, 8 coworking sites); operator control of the pantry not shown: 7; inside a coworking space: 5; Tuesday estimate under 30: 4 (Hanover Park, Instant, Warp, Normal Computing); no staffed office at the address: 1; site possibly closed: 1 |
| Passed, by Tuesday onsite band | unknown 114, 76-150 31, 40-75 24, 151-250 23, under-40 21, 251-500 18, over-500 10 |
| Passed, attendance signal | unknown 136, on-site 5 days 54, hybrid days not stated 27, hybrid 3 days 10, 2 days or fewer 8, remote 4, hybrid 4 days 2; Tuesday named in the policy 5 |
| Passed, held before outreach | 38 (mostly signed-not-occupied leases) |
| Top 50 | 43 of B's candidates and 7 near-miss firms; no coworking site. Bands: 76-150 19, 40-75 13, 151-250 12, under-40 6. Attendance: on-site 5 days 25, hybrid not stated 11, hybrid 3 days 7, unknown 4, other 3. Occupied 36, occupancy-unconfirmed 10, signed-not-occupied 4 (held). Confidence high 29, medium 14, low 7. Scores 46.2 to 70.0 (median of all passed rows 36.0). |
| Contacts | none yet: B opened no LinkedIn and named no person. Title match is 0 on every row until stage 2. |

### Brands

| Measure | Count |
| --- | --- |
| Found | 311 (BR1 64, BR2 64, BR3 79, BR4 59, BR5 45); no duplicates after normalization |
| Passed the hard gates | 244 |
| Gate failures (a row can fail more than one) | explicit health claim 33, no buy path 21, not shelf-stable 18, excluded category 16 |
| Passed, nearest graded store | `store_selector` 88, `brand_claim` 13, none within ten blocks (online store only) 143; a graded store inside the cluster for 94 |
| Passed, HQ | New York City 72 (+9 unverified), rest of New York State 21 (+1), Northeast 54 (+5), elsewhere 69 (+8), unknown 5 |
| Passed, why-now | press 74, own listing 106, unverified 6, none 58 |
| Passed, flags | founder_review Y 219; Startup CPG Y 50 |
| Passed, primary contact | named on an opened page 165, first name only 20, unverified 16, none 43; a backup named for 77 |
| Top 60 | HQ New York City 31 (+2 unverified), New York State 5, Northeast 6 (+3), elsewhere 12 (+1): 38 of 60 are New York. Grade `store_selector` 46, `brand_claim` 3, none within ten blocks 11. Why-now press 30, listing 23, none 7. founder_review Y 49. Startup CPG Y 17. Contacts: named 52, first name only 4, unverified 2, none 2; backup 24; LinkedIn URL 2. Scores 50 to 78 (median of all passed rows 42). |
| Store links | 441 (store_selector 261, brand_claim 157, unverified 23); 361 within ten blocks. Whole Foods re-check 2026-10-24: 272 links, 261 found, 11 not found (now unverified). |

## Assumptions (numbered; each is editable in `_build/config.py` or stated where it applies)

1. No Clay or Google login exists, so the tables are CSVs ready to import; the build sheet and import steps come in a later stage.
2. Office rows are B's companies and near-miss rows plus B's coworking sites; nothing was added from B's raw slices because 276 companies exceed the 200 target.
3. When a headcount is company-wide, the New York office holds 50% to 100% of it if the HQ is New York and 5% to 100% if the HQ is elsewhere or unknown. These are planning bounds, not facts; intake replaces them.
4. In-office rate: 67% (500 or fewer staff), 57% (501 to 4,999, the all-firm figure), 46% (5,000+), from the plan's Partnership for New York City figures; no Tuesday uplift is applied.
5. A hard size gate removes a row only when the whole estimated range is under 30 or over 250; a range that crosses a line passes with a flag.
6. Two disagreeing sourced counts define a range rather than "unknown"; B's own band stays `unknown` in `headcount_band`.
7. The employer's policy sentence on Built In outranks the "typical time on-site" box; a day range uses its lower figure; an unclaimed Built In profile is used as it reads.
8. A coworking site is one office only if the operator controls the pantry; `unknown` control fails the gate until a walk-by or call shows it.
9. B's holds (signed-not-occupied, unresolved address conflict, still in coworking, possibly closed) keep the row ranked but keep it out of outreach until the walk clears it.
10. Office why-now is a lease reported since 2025-11 in an article about the company itself.
11. `store_selector` is kept only for a retailer's own store-scoped catalog (Whole Foods); Pop Up Grocer is `brand_claim` at most and never near-cluster; a link the catalog no longer shows is `unverified`.
12. "Within ten blocks" is B's measure (794 m of grid walking from the boundary), applied to every store, including stores B did not list (geocoded with the project geocoder).
13. An Amazon storefront linked from the brand's own site counts as an online store; whether the brand can issue a discount code there is for intake (q3) to confirm.
14. A company projection or a press quote can set the revenue band, with `revenue_band_type` saying which (Banagua projection, MODA cumulative quote, Tierra Farm 2021).
15. Founder-review types and penalties are sorted from the researcher's own wording by pattern; only the most severe type counts. A sourced revenue over $10M (-35) or a large-company owner (-25) keeps a brand out of the top 60 unless the founder knows it.
16. The primary brand contact is the founder (the likely budget owner at this size); the marketing lead is the backup, else the next co-founder.
17. A name is filled into `first_name` only when an opened page shows it; a title alone in doubt does not unverify a name.
18. Startup CPG participation adds no points and is never a hook (E's rule); it is kept as a flag.
19. New York brands come first: a New York City HQ earns 20 points against 3 for a brand outside the Northeast.

## Changelog (one line per round)

- Round 0 (draft): merged B's 276 companies and 32 coworking sites and the five brand slices with 768 enrichment updates; gates, onsite estimate, ten-block test, re-grades and both scores built; Built In attendance pages read for the 105 passed offices that cite Built In.
- Round 1 (self-critique as an outbound operator): sourced-revenue-over-$10M and big-owner penalties raised so a $100M brand cannot sit in the top 60; remote offices penalized; office why-now limited to the company's own lease article; a duplicate-name false positive ((P)RiND vs RIND) undone; online stores checked for 12 buy-path failures (7 found, 1 confirmed broken).
- Round 2 (spot check 1: offices 4.3%, brands 10.3%): employer policy text overrides the Built In days box; co-founder and marketing lead no longer fill both slots with one person; page spelling kept for names; Strip Jerky why-now re-sourced, Sweet Loren's refrigerated why-now removed.
- Round 3 (spot check 2: offices 2.4%, brands 27.6%): own-site why-nows typed as listings; contacts limited to real names with their own titles and the page that supports them; LinkedIn search results never replace an opened source; Maxine's title fixed; day ranges, "twice a week" and Tuesday named read from policy text; B's holds carried.
- Round 4 (spot check 3: offices 0%, brands 10.0%): a doubtful title no longer unverifies a name; unverified why-nows earn nothing.
- Round 5 (spot check 4: offices 0%, brands 0%): New York weight raised to 20 (fit to 10), so 38 of the top 60 brands are New York.
- Round 6 (spot check 5: brands 2.2%): every Whole Foods link re-queried with strict matching; 11 links that the catalogs no longer show are now unverified.

## Open issues for later stages

1. No contacts for any office (B named none); title match is 0 everywhere, so the office top 50 will re-rank once stage 2 finds titles.
2. The waterfall for verified work emails needs Clay (top 50 offices, top 60 brands); 0 verified so far.
3. 114 passed offices have no sourced headcount and 136 no attendance signal; LinkedIn company URLs are `unknown` on every row (LinkedIn not opened).
4. Store catalogs change daily: a brand's store link must be re-checked before copy uses it (11 links fell away in one day).
5. 143 passed brands have no graded store within ten blocks; they qualify only through an online store and a discount code.
6. Rows that cite sec.gov (`source_note`) rest on a filing agents may not open; the founder can open them in a browser.
7. The over-250 and under-30 gates rest on assumption 3's New York share bounds; a founder decision on those bounds would move about a dozen near-miss rows either way.
