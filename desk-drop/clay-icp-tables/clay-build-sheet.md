# Clay build sheet: Offices and Brands

Workstream A, 2026-10-24. The working name and tagline live in one cell, `Routine!B1` (`company_name`) and `Routine!B2` in `clay-icp-tables.xlsx`; nothing in the tables depends on them.

**Status.** No Clay or Google login exists, so nothing is in Clay yet. Everything Clay needs is here as files: two import-ready tables, a Google Sheets workbook whose daily views update by themselves, the column dictionary, the formulas, the research prompts and the email waterfall spec. Setup takes about 30 minutes with your logins (section 5). No credits were used and nothing was bought, sent or signed up for.

| | Offices | Brands |
| --- | --- | --- |
| Rows found | 308 (276 companies, 32 coworking sites) | 311 |
| Passed the hard gates | 241 | 239 |
| Top list (contacts researched) | 50 | 60 |
| Primary contact named on an opened page (top list) | 31 | 59 |
| Ready for outreach today | 26 | 183 |
| Verified work emails | 0 of 50 (0%) | 0 of 60 (0%) |

Verified emails are 0% because the waterfall runs inside Clay (or a provider like Hunter) with your login and credits. Agents never guess an address from a name pattern: a guessed address is not verified, and a bounce costs more on a new domain than a lost message.

## 1. Hard gates and scoring, in plain words

**Hard gates come first, before any enrichment spend.** A row that fails any gate scores 0, keeps `score_raw` for review, and never reaches a daily view or the waterfall.

*Offices fail if:* the address is outside the cluster (B's `boundary.geojson`: Flatiron, NoMad and Union Square); the company sits inside a coworking space; there is no staffed office at the address; the whole Tuesday estimate is under 30 or over 250; or, for a coworking site, the operator is not shown to control the pantry or the site may be closed. A range that crosses 30 or 250 passes with a flag.

*Brands fail if:* the category is excluded (alcohol, cannabis or hemp, supplements, needs preparation); the brand's own copy makes an explicit health claim (structure or function wording such as "supports gut health"; nutrient wording such as "10g protein" passes with a founder-review flag); it is not shelf-stable (refrigerated, frozen, under 60 days); or there is no graded store within ten blocks of the cluster and no online store.

**The Tuesday onsite estimate** is the sourced headcount x the New York share (100% for a New York office count; 50% to 100% for a company-wide count with a New York HQ; 5% to 100% otherwise) x the in-office rate (67% for firms of 500 or fewer, 57% for 501 to 4,999, 46% for 5,000+; Partnership for New York City, March 2025, via plan.md). It is a low-to-high range, always labeled an estimate until intake replaces it.

**Office score (0 to 100): how likely this office fits the drop and can say yes, from what is known today.**

| Part | Points | Rule |
| --- | --- | --- |
| Onsite fit | 0 to 30 | 25 x the share of the Tuesday range inside 40 to 250, plus 5 when the count is for the New York office; 7 when no count exists |
| Size | -4 to 15 | 500 or fewer staff 15, 501 to 1,000 6, 1,001 to 4,999 2, 5,000+ 0, unknown 8; minus 4 when a controlling parent is named |
| Attendance | -5 to 15 | On-site 5 days 15, 4 days 12, 3 days 10, days not stated 7, 2 or fewer 5, no signal 6, remote -5; plus 3 when the policy names Tuesday |
| Address | 0 to 15 | Occupied 10, occupancy unconfirmed 5, lease signed but not occupied 2; plus source confidence high 5, medium 3 |
| Title match | 0 to 10 | Primary contact in the five target titles (Office Manager, Workplace Experience, Head of Workplace, People Operations, EA to the CEO, or their direct forms), on an opened page, in New York: 10. Any other named person: 5 |
| Known to founder | 0 or 15 | You mark `known_to_founder = Y` |

**Brand score (0 to 100): how likely this brand fits a founding campaign now: buyable near the offices, New York first, a reason to sample now, a reachable owner.**

| Part | Points | Rule |
| --- | --- | --- |
| Buy path | 0 to 25 | Store page inside the cluster 25, within ten blocks 20; brand locator inside 17, within ten 13; online store only 6 |
| New York first | 3 to 20 | HQ New York City 20, rest of the state 13, Northeast 8, elsewhere 3, unknown 4; minus 3 if unverified |
| Why-now | 0 to 15 | Press in 180 days 15, in a year 8; own new listing in 180 days 8, in a year 4 |
| Revenue | 0 to 10 | $500k to $10M 10, unknown 5, under $500k 2, over $10M 0 |
| Fit | 0 to 10 | Shelf-stable, individually packaged, online store |
| Contacts | 0 to 10 | Founder named on an opened page 6 (first name only or snippet 3); marketing lead 4 (snippet 2) |
| Known to founder | 0 or 10 | You mark it |
| Founder-review penalty | 0 to -35 | The worst type only: sourced revenue over $10M -35, large-company owner -25, scale signals -12 (including 4,000+ doors, a Series B or Costco in the why-now), dormant -12, heritage -10, perishable risk -8, under $500k -5, alcohol-adjacent -5, borderline claim -4, pack format -4, other -2 |

Every row's `score_reason` says its score in one sentence. Weights live in `_build/config.py`; the wording rules for founder-review types (including the why-now scale rule) in `_build/build_brands.py`.

**Ready for outreach** (`ready_for_outreach = Y`): passed the gates, not on hold, a contact named on an opened page, and for offices a Tuesday band of 40 to 250 (an `under-40`, `251-500` or `over-500` band needs your `founder_ok_to_queue = Y`; the prompt makes 30 to 39 your call).

**The daily view** (CONTRACTS 6.2): the ten best-scored rows with `status = new`, `do_not_contact = N`, `ready_for_outreach = Y` and no `opt_out_date`. It takes one row per `company_group` (rows that share a parent, an operator, a name or a named person) and skips any group with a row in flight (`queued` to `materials_sent`) or a do-not-contact row. Only the primary contact appears, so two people from one company are never in flight. In the workbook it is a live `SORT(FILTER())` formula that moves the moment you change status, do-not-contact, a hold, the known flag or your OK.

## 2. Column dictionary

Every column, one row each, is in the workbook's Dictionary tab and `column-dictionary.csv` (201 entries; the build fails if a column has none). Header colors in the workbook: yellow you edit, blue outreach edits, grey formula (never type), white researched (fix the source and rebuild).

**Stable columns (CONTRACTS 6.2, both tables, never renamed).**

| Column | Values | Meaning |
| --- | --- | --- |
| `row_id` | AO-C-### (B's company), AO-W-### (coworking site), AB-### (brand) | Stable key; use it as `org_id` in the pipeline log |
| `company` | text | Company or brand name |
| `first_name`, `last_name`, `title` | text, `unknown` surname | Primary contact, filled only when an opened page shows the name |
| `contact_linkedin_url` | URL or blank | You paste it in the routine (agents never open LinkedIn) |
| `work_email`, `email_status` | address; `verified`, `unverified`, `none` | From the waterfall only; all `none` today |
| `channel` | `email`, `linkedin`, `warm-intro`, `walk-in`, blank | linkedin for a named contact until an email is verified; walk-in for a top-50 office with nobody named; blank for a brand with nobody named |
| `score`, `score_reason` | 0 to 100; one sentence | Formula in the workbook |
| `onsite_band` | CONTRACTS bands | Offices: band of the central Tuesday estimate (estimate until intake); blank for brands |
| `nearest_stocked_retailer`, `nearest_retailer_grade` | "Store, street"; `store_selector`, `brand_claim`, `unverified` | Brands: best graded store within ten blocks; `seen_on_shelf` is yours only; blank for offices |
| `why_now`, `why_now_url`, `why_now_date` | text, URL, date | Brands: dated news or listing in 12 months; offices: a lease reported since 2025-11 |
| `known_to_founder` | Y/N | You set it; adds points and makes the channel warm-intro |
| `startup_cpg_member` | Y, N, unknown | Public Startup CPG participation; never a hook, no points |
| `do_not_contact` | Y/N | Y the same day anyone opts out; never reversed |
| `status` | CONTRACTS section 4 | Lives here and nowhere else |
| `source_url`, `found_date` | URL, date | Main source of the row and when it was found |

**Daily-view block** (right after the stable columns, same order in the view): `side`, `daily_view_rank`, `rank`, `top50`/`top60`, `check_before_send` (the one-minute checks left), `contact_role`, `contact_status` (`verified-page`, `first-name-only`, `unverified`, `none`), `contact_evidence` (employer's own site, The Org, press or podcast page, snippet), `contact_source_url`, `contact_source_date`; offices also `title_match`, `street_address`, `floor`, `lease_status`, `onsite_low`, `onsite_high`, `onsite_confidence`, `attendance_signal`; brands also `product_example`, `category`, `hq_city`, `online_store_url`, `founder_review`, `founder_review_reason`; both `company_group`, `hold_before_outreach`, `hold_reason`, `opt_out_date`.

**Your controls**: `ready_for_outreach` and `ready_reason` (formulas), `founder_ok_to_queue` (Y lets an out-of-band office in), `hold_before_outreach` (set N after the lobby check), `title_match` (reset it when you swap a contact; the score follows), `known_to_founder`.

**Contacts**: the primary's extras (`contact_name_as_found`, `contact_record_date` (the source's own date; older than 12 months adds a check), `contact_note`, `contact_ny_base`, `linkedin_status`, `contacts_researched`) and a full backup set (`backup_first_name`, `backup_last_name`, `backup_title`, `backup_linkedin_url`, `backup_work_email`, `backup_email_status`, `backup_contact_role`, `backup_contact_name_as_found`, `backup_contact_status`, `backup_contact_evidence`, `backup_contact_source_url`, `backup_contact_record_date`, `backup_contact_note`), plus `company_group_reason`.

**Gates and score parts**: `gate_result`, `gate_reason`, `gate_failed` (brands), `score_raw`, the `score_*` parts above, `founder_review_type`, and the estimate's workings (`onsite_central`, `onsite_flags`, `onsite_basis`, `onsite_label`, `onsite_fit_share`, `size_class`).

**Research**: offices carry B's address, headcount, lease, lobby and coworking fields with their sources and dates (`address_source_url`, `headcount_source_url`, `lease_status`, `lobby_type`, `in_coworking`, `confidence`, `b_notes` and the rest) plus `a_corrections` (facts this workstream changed, with sources). Brands carry the gate evidence (`shelf_stable_basis`, `health_claim_flag`, `online_store`, `online_store_note`, `revenue_band` with `revenue_basis`), every store within ten blocks with its grade and distance, the why-now type and age, `notes` and an `enrichment_log` of every field change with its source.

**Outreach tracking (E's columns, empty)**: `sequence`, `touch_1_date` to `touch_3_date`, `last_reply_date`, `reply_type`, `call_date`, `call_notes`, `yes_in_principle`, `next_action`, `next_action_date`, `opt_out_date`, `referral_from`, and E's personalization columns (`street_short`, `why_now_hook`, `product_short`, `call_note_hook`, `how_we_know`, `referrer_ok_to_name`, `office_approvals_complete`). Rules: `desk-drop-outreach/tracking/csv/clay_tracking_columns.csv`.

**View helpers (formulas)**: `in_flight`, `group_blocked`, `eligible`, `view_pick`, `in_daily_view`, `row_order`.

## 3. The 15-minute morning routine

Ten messages a day is the plan's pace, about five per side. Each view shows ten, so rows 6 to 10 are spares.

| Clock | Step | What you do |
| --- | --- | --- |
| 0:00 to 2:00 | Log yesterday | For each reply, bounce or opt-out, set `status` (CONTRACTS words) and E's columns. Any opt-out in any words: `do_not_contact = Y`, `status = do_not_contact`, `opt_out_date` = today. Never reverse it. A "wrong person": copy the backup into the primary columns, reset `title_match`, set `status = new`. |
| 2:00 to 3:00 | Clear what you checked | A walk-by showed a held company on the lobby directory: `hold_before_outreach = N`. An out-of-band office you want in anyway: `founder_ok_to_queue = Y`. |
| 3:00 to 4:00 | Open the two daily views | They have already updated. Work the top five of each. |
| 4:00 to 13:00 | One minute per row, ten rows | Read `score_reason` and `check_before_send`, and do only what it says: find the person on LinkedIn and paste `contact_linkedin_url` (this confirms the name and role); confirm an old record; re-open a brand's store page before you use the retailer line; read a founder-review note. A row that fails: set `wrong_person` or `no` and take the next spare. |
| 13:00 to 14:00 | Export | Download each daily-view tab as CSV (`daily-view-offices.csv`, `daily-view-brands.csv`) for E's draft maker. Export first: queued rows leave the live view. |
| 14:00 to 15:00 | Queue | `status = queued` on the rows you send today. Their company group is blocked at once. Sending is E's routine. |

**Fridays, 10 minutes, all in the Sheet (or Clay)**: copy B's walk notes into `hold_before_outreach` (N once the lobby directory shows the company), mark `known_to_founder` for anyone you know, and add a row for each referral (`status = new`, `referral_from` = the referrer's `row_id`). Nothing in the routine needs Python.

## 4. Seeding and refresh

**Where the rows came from.** Offices: every company in B's `companies.csv` (168) and `near_miss.csv` (108), plus B's 32 coworking sites, each with B's address source and date. Brands: five research slices (311 rows), New York brands first, deduplicated on name and domain. Sources: the Whole Foods store-scoped catalogs for Union Square, NoMad and Chelsea (the only `store_selector` evidence); brand store locators (Stockist, Storepoint); Startup CPG public pages (newswire, Shelfie finalists and winners, the Summer Fancy Food Show pavilion list); the Summer Fancy Food Show 2026 exhibitor directory and SFA's sofi lists; New York CPG trade press (Snack and Bakery, BevNET, Food Business News). Trader Joe's 14th Street was skipped (own label only) and Eataly's online catalog holds its imports, not the Flatiron store's local set, so neither yielded rows; Instagram and LinkedIn were not opened. Contacts: employer team pages, The Org position pages, press, event and podcast pages; LinkedIn was never opened.

**How it rebuilds (whoever maintains the files, not the morning routine).** `python3 -B clay-icp-tables/_build/build_all.py` rebuilds both tables, the daily views, the Clay import files and the workbook in seconds, offline. Researched facts are never typed into the tables: a change goes into a sourced corrections file (`_work/stage3_corrections.csv`, `_work/stage3_contact_fixes.csv`, `_work/contacts_s3_entrants.csv`) and the build applies it. **Once outreach has started, save the live tables first**: download the Offices and Brands tabs (or export the Clay tables) as `clay-icp-tables/live/offices-live.csv` and `brands-live.csv`. The build then carries over status, do-not-contact, opt-outs, holds, your OKs, known flags, LinkedIn URLs, emails, any contact you swapped, E's tracking columns and referral rows. A do-not-contact or opt-out is never undone. Without the live files a rebuild starts every row at `status = new`. `python3 -B clay-icp-tables/_build/test_workbook.py` recalculates the workbook in LibreOffice and checks it against the CSVs and an edit scenario.

**Refresh cadence.**
- Daily: the routine above.
- Weekly: Whole Foods store re-check; one health-claim scan of brands entering the next week's views (`_build/scan_claims.py`); walk notes into holds.
- When the office ready pool runs low (26 ready offices last about a week at five a day): research contacts for the next block of ranks (51 to 100) with the Claygent office prompt below, and walk the 19 top-50 offices with no named contact.
- Monthly: re-run B's seed lists if B publishes new ones; rebuild; re-score.

## 5. Clay setup (about 30 minutes; steps marked LOGIN need yours)

**Choose one table of record on day one.** Until Clay is set up, the Google Sheet made from `clay-icp-tables.xlsx` is the table: status lives there and nowhere else. Once you import into Clay, Clay is the table and the Sheet becomes its export. Never edit status in both.

1. LOGIN. Open Google Drive, upload `clay-icp-tables.xlsx`, open it with Google Sheets (File > Save as Google Sheets). Check the Daily view tabs show ten rows each.
2. LOGIN. Create a Clay account on the Free plan (no card). Free allows "up to 200 rows per table", 100 data credits and 500 actions a month, multi-provider waterfalls, Claygent and your own API keys ([clay.com/pricing](https://www.clay.com/pricing), opened 2026-10-24).
3. LOGIN. New workbook, then two tables: Import CSV `clay-import/offices-clay-import.csv` and `clay-import/brands-clay-import.csv`. Each holds the 175 best passed rows (25 rows left for referrals under the 200-row cap). Set `row_id` as the unique key; keep dates as text.
4. Add formula columns (Clay's formula editor can write these from the plain-English rule; syntax founder to confirm): `ready_for_outreach` = gate passed, hold not Y, first name filled, and (offices) band 40 to 250 or your OK; `in_flight` = status is one of queued, contacted, replied, call_booked, call_done, yes_in_principle, materials_sent.
5. Make a view called Daily view on each table: filter `status = new`, `do_not_contact = N`, `ready_for_outreach = Y`, `opt_out_date` empty; sort by `score` descending. Read the top ten. Group blocking is a manual check in Clay: before queueing a row whose `company_group` starts with `grp-`, filter by that group and skip it if any row there is in flight or do-not-contact. Today that touches Carbyne and Prepared 911 (both Axon), the coworking chains, Moshi and Bruce Cost, and PRETZELIZED.
6. Make a view called Due today: `next_action_date` = today (E's follow-ups).
7. Run the research prompts and the waterfall below on the top rows only, in the order given, stopping at the free allowance.
8. Friday: export each Clay table as CSV and paste it over the Offices and Brands tabs in the Sheet; the Sheet's formulas recompute the views and E's tracker reads it.

**Claygent research prompts** (Clay's web-research agent; credits per row founder to confirm in Clay). Run them only on rows that passed the gates. Paste each answer into the named columns with its source URL and date, and leave a field `unknown` when no page shows it.

*Office pantry owner* (rows ranked 51 to 100 first, then any top-50 row with nobody named):
> Find the person who runs the office, workplace or pantry at {company}'s New York office at {street_address}. Look only at public business pages: the company's own team, about or careers pages, press releases, The Org, and conference or podcast pages. Target titles, best first: Office Manager, Office Coordinator, Workplace Experience Manager, Head of Workplace, Facilities Manager, People Operations, Executive Assistant to the CEO. Return first name, last name, exact title, the URL of the page that names them, that page's date, and whether the page places them in New York. Return "none found" if no page names a person. Do not guess or construct an email address. Do not return phone numbers, home locations or anything personal.

*Office address and attendance check* (any row before the first touch):
> Does {company} have staff working at {street_address}, New York, today? Quote the sentence and give the URL and date of the page that says so. Separately, quote the company's own words on how many days a week staff are in the office, with URL and date. Answer "not found" rather than infer.

*Brand founder and marketing lead*:
> For the snack or beverage brand {company} ({website}), find the founder or CEO and the person who leads marketing. Use the brand's own site, press releases, trade press, The Org, and podcast or event pages. Return for each: first name, last name, exact title, source URL and date. Return "none found" if no page names them. No emails, phones or personal details.

*Brand why-now and claims check*:
> For {company} ({website}): (1) the most recent dated news in the last 180 days (launch, new retailer, funding, award) with URL and date; (2) quote any wording on the brand's own site that says the product supports, improves, boosts or regulates a body function, or names a disease or condition; (3) quote the shelf life if the brand states it. Answer "none found" for any part with no page.

**Email waterfall spec** (verified work email, top 50 offices and top 60 brands only).

| Item | Spec |
| --- | --- |
| Rows | `gate_result = pass`, `top50 = Y` or `top60 = Y`, `do_not_contact = N`, a full name (`last_name` not `unknown`) and a website domain. Today: 30 office and 59 brand primaries. Backups only when a primary bounces or leaves. |
| Inputs | `first_name`, `last_name`, domain of `website` |
| Step 1, find | Clay's work-email waterfall. Put a provider you hold a free key for first: Hunter Free gives 50 credits a month, 1 per email found, 0.5 per verification ([hunter.io/pricing](https://hunter.io/pricing), opened 2026-10-24), and Clay charges no data credits on your own key, only actions (Clay pricing FAQ). Then the Clay-credit providers in the order Clay's panel lists them. Stop at the first email found. Credit cost per provider and lookup: founder to confirm in Clay's panel. Clay does not charge when an enrichment returns nothing (Clay pricing FAQ). |
| Step 2, validate | A validation step (Clay's validator or Hunter's verifier). Map: deliverable or valid to `email_status = verified`; accept-all, catch-all, risky or unknown to `unverified` (E sends LinkedIn instead); invalid or not found to `none` and clear `work_email`. |
| Never | Pattern-guess an address, run it on gated-out rows, or enrich personal emails or phones. |
| Stop point | When the next run would exceed the free allowance (100 data credits and 500 actions a month on Clay Free, 50 Hunter credits), stop and decide. Two months of free allowances cover the 89 primaries; one month of Hunter Starter covers them at once (below). |

## 6. Running cost

| Item | Cost | Recommendation |
| --- | --- | --- |
| Google Sheets | $0 (inside the Google Workspace seat the plan already budgets) | Use |
| Clay Free | $0 | Use for import, research and the waterfall within its allowance |
| Hunter Free (own key in Clay) | $0 | Use first in the waterfall |
| Clay Launch | $185 a month billed monthly, $167 a month billed yearly; 2,500 data credits and 15,000 actions a month ([clay.com/pricing](https://www.clay.com/pricing), 2026-10-24) | Not recommended: over the plan's $60 a month software cap on its own |
| Hunter Starter | $49 a month billed monthly, $34 a month billed yearly; 2,000 credits a month ([hunter.io/pricing](https://hunter.io/pricing), 2026-10-24) | Only with your written yes, for one month, if you want all 89 emails at once; it fits the cap only if the rest of the stack stays under $11 that month |
| Clay data credits, if topped up | From $0.05 each (Clay pricing FAQ); top-ups are a paid-plan feature | Not needed for the free route |

Recommended running cost for this workstream: **$0 a month.** Credits used so far: none.
