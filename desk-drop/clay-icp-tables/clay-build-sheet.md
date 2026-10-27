# Clay build sheet: Offices and Brands

Workstream A, 2026-10-24 (updated after independent review round 1). The working name and tagline live in one cell each, `Routine!B1` (`company_name`) and `Routine!B2` in `clay-icp-tables.xlsx`. No data cell holds the name.

**Status.** No Clay or Google login exists, so nothing is in Clay or Google Sheets yet. Everything is here as files: the Google Sheets workbook (the table of record, with live daily views), two Clay import files, the column dictionary, the formulas, the research prompts and the email waterfall spec. Setup takes about 30 minutes with your logins (section 5). No credits were used, and nothing was bought, sent or signed up for. The workbook has been recalculated in LibreOffice 24.2 and 25.8 and checked cell by cell. It has not been opened in Google Sheets itself (no login): unverified, founder to confirm.

| | Offices | Brands |
| --- | --- | --- |
| Rows found | 308 (276 companies, 32 coworking sites) | 311 |
| Passed the hard gates | 243 | 196 |
| Top list | 50 | 60 |
| Primary contact named (top list) | 34: 10 on the employer's page or dated press, 24 only on The Org (`crowd-listed`) | 57: 46 on the brand's page or dated press, 9 only on The Org, 2 first name only |
| Backup contact named (top list) | 23 | 36 (25 of them marketing leads) |
| Person LinkedIn URL, top-list primaries | 0 (you paste them on Friday) | 10 |
| Company LinkedIn URL | 181 of 276 companies (41 of the top 50), linked from the company's own site or its The Org record | not collected |
| Ready for outreach today | 38, plus 13 on the Walk list | 66 (107 passed brands wait on your review) |
| Verified work emails | 0 of 50 (0%) | 0 of 60 (0%) |

Verified emails are 0% because the waterfall runs inside Clay (or Hunter) with your login and credits. Agents never guess an address from a name pattern. A guessed address is not verified, and a bounce costs more on a new domain than a lost message does.

**Supply.** At five office first touches a day from E's first cold day (Monday 2026-11-09), the 38 ready offices last until about Thursday 2026-11-19. Section 4 says how to refill the pool before then.

## 1. Hard gates and scoring, in plain words

**Hard gates come first, before any enrichment spend.** A row that fails any gate scores 0 and keeps `score_raw` for review. It never reaches a daily view, the Clay import or the waterfall.

*Offices fail if:*
- the address is outside the cluster (B's `boundary.geojson`: Flatiron, NoMad and Union Square);
- the company sits inside a coworking space, including a company still in one until a move B reports (Stash, Agentio; re-check after the move);
- there is no staffed office at the address;
- the whole Tuesday estimate is under 30 or over 250 (a range that crosses 30 or 250 passes with a flag);
- for a coworking site, the operator is not shown to control the pantry, or the site may be closed.

*Brands fail if:*
- the category is excluded (alcohol, cannabis or hemp, supplements, needs preparation);
- the brand's own selling copy makes a health claim. This covers the homepage, product pages and descriptions (the Shopify catalog), About, FAQ, ingredient and "why" pages. A claim is wording that says the product or an ingredient affects a body or mental function or a disease ("supports a calm mood", "fights cavities", "feeds your good gut bacteria"), a published testimonial that names a disease, CBD products for sale, or the FDA supplement disclaimer. The rule applies to the whole brand, so one claiming product fails the brand. Nutrient wording ("10g protein") passes. Implied or educational wording (a blog post, product tags, "no crash", a functional ingredient with no claim seen) passes with a blocking founder review;
- it is not shelf-stable (refrigerated, frozen, under 60 days);
- there is no graded store within ten blocks of the cluster and no online store.

**The Tuesday onsite estimate** starts from the sourced headcount. It is multiplied by the New York share (100% for a New York office count; 50% to 100% for a company-wide count with a New York HQ; 5% to 100% otherwise) and by the in-office rate (67% for firms of 500 or fewer, 57% for 501 to 4,999, 46% for 5,000+; Partnership for New York City, March 2025, via plan.md). **Space check:** where the row has a sourced leased square footage for its New York space (100 rows), the high end is at most sf / 125 and the central figure at most sf / 150. Where the headcount math exceeds what the space seats, the range comes from the space (sf / 250 to sf / 125). `onsite_basis` and `onsite_space_check` say which rule applied. The result is a low-to-high range, always labeled an estimate until intake replaces it.

**Office score (0 to 100): how likely this office fits the drop and can say yes, from what is known today.**

| Part | Points | Rule |
| --- | --- | --- |
| Onsite fit | 0 to 30 | 25 x the share of the Tuesday range inside 40 to 250, plus 5 when the count is for the New York office; 7 when no count exists |
| Size | -4 to 15 | 500 or fewer staff 15, 501 to 1,000 6, 1,001 to 4,999 2, 5,000+ 0, unknown 8; minus 4 when a controlling parent is named |
| Attendance | -5 to 15 | On-site 5 days 15, 4 days 12, 3 days 10, days not stated 7, 2 or fewer 5, no signal 6, remote -5; plus 3 when the policy names Tuesday |
| Address | 0 to 15 | Occupied 10, occupancy unconfirmed 5, lease signed but not occupied 2; plus source confidence high 5, medium 3 |
| Title match | 0 to 10 | The contact shown has one of the five target titles (Office Manager, Workplace Experience, Head of Workplace, People Operations, EA to the CEO, or their direct forms), on an opened page, in New York: 10. Any other named person: 5 |
| Known to founder | 0 or 15 | You mark `known_to_founder = Y` (the channel becomes `warm-intro`) |
| Ties | | Names on the employer's own page or in dated press before names only The Org lists, then the share inside 40 to 250, then source confidence |

**Brand score (0 to 100): how likely this brand fits a founding campaign now.** That means buyable near the offices, New York first, a reason to sample now and a reachable owner.

| Part | Points | Rule |
| --- | --- | --- |
| Buy path | 0 to 25 | Store page inside the cluster 25, within ten blocks 20; brand locator inside 17, within ten 13; online store only 6 |
| New York first | 3 to 20 | HQ New York City 20, rest of the state 13, Northeast 8, elsewhere 3, unknown 4; minus 3 if unverified |
| Why-now | 0 to 15 | Press in 180 days 15, in a year 8; own new listing in 180 days 8, in a year 4; a why-now with no link or date earns 0 and its note moves to `notes` |
| Revenue | 0 to 10 | $500k to $10M 10, unknown 5, under $500k 2, over $10M 0 |
| Fit | 0 to 10 | Shelf-stable, individually packaged, online store |
| Contacts | 0 to 10 | Founder named on an opened page 6 (first name only or snippet 3); marketing lead 4 (snippet 2) |
| Known to founder | 0 or 10 | You mark it |
| Founder-review penalty | 0 to -35 | The worst type only: sourced revenue over $10M -35, large-company owner -25, scale signals -12, dormant -12, heritage -10, perishable risk -8, under $500k -5, alcohol-adjacent -5, functional-ingredient wording -4, nutrient wording -4, no single-serve pack -4, other -2 |
| Ties | | Names on the brand's own page or in dated press before The Org-only names, then store grade, then why-now points |

**Founder review (brands).** `founder_review = Y` means there is something to read in `founder_review_reason`. `review_blocking = Y` means you must decide before outreach. That applies to owner, scale, heritage, dormant, perishable risk, alcohol-adjacent, no single-serve pack, and functional-ingredient or implied-effect wording. Such a row waits on the Founder review tab until you set `founder_review_cleared = Y` (or `status = no`). Nutrient wording, under $500k, a single-serve pack not yet shown, an unstated shelf life and a store-only buy path are notes for copy and intake, not blocks. Today 107 passed brands are blocking (29 in the top 60).

Every row's `score_reason` gives its score in one sentence. It is a formula, so it follows `known_to_founder` and `promote_backup`. Weights live in `_build/config.py`. The wording rules for founder-review types live in `_build/build_brands.py`.

**Ready for outreach** (`ready_for_outreach = Y`) means:
- the row passed the gates and is not on hold;
- a contact is named on an opened page (`crowd-listed` counts, but you confirm it on LinkedIn on Friday);
- offices: the Tuesday band is 40 to 250. An `under-40`, `251-500` or `over-500` band needs your `founder_ok_to_queue = Y`, since the prompt makes 30 to 39 your call;
- brands: no blocking review is pending.

**The daily view** (CONTRACTS 6.2) is the ten best-scored rows that meet all of these:
- `status = new`, `do_not_contact = N`, no `opt_out_date`;
- `ready_for_outreach = Y`;
- one row per `company_group`, meaning rows that share a parent, an operator, a name or a named person;
- no other row in the group is in flight (`queued` to `materials_sent`), and none carries a do-not-contact signal: the flag, the status or an opt-out date, whichever is typed (`dnc_any`).

Only the contact shown appears, so two people from one company are never in flight. In the workbook each view cell is an INDEX/MATCH on a numbered slot helper, with no SORT or FILTER. This runs in any spreadsheet app and moves the moment you change status, do-not-contact, a hold, the known flag, a review or your OK. If anyone pastes values over the formula columns of the Offices or Brands tab, a guard blanks every view and its first cell says "The table tab was pasted over and its formulas are gone: undo the paste or restore it (File > Version history)", instead of showing stale rows.

**Two working tabs.** The *Walk list - Offices* tab holds top-50 offices with nobody named (`channel = walk-in`): 13 today, best score first, with address, floor, building, lobby type and its note, COI and the company LinkedIn page. The *Founder review - Brands* tab holds the 30 best-scored brands waiting on a blocking review.

## 2. Column dictionary

The workbook's Dictionary tab and `column-dictionary.csv` hold one row for every column, 240 entries; the build fails if a column has none. Header colors in the workbook:
- **yellow**: you edit;
- **blue**: outreach edits;
- **grey**: formula, never type;
- **white**: researched; fix the source and rebuild.

The one exception to the white rule is an empty `primary_*` or `backup_*` block. You may type a person you or Clay found on a public page there, with its source URL and date, and the formulas and every rebuild follow it.

**Stable columns (CONTRACTS 6.2, both tables, never renamed).**

| Column | Values | Meaning |
| --- | --- | --- |
| `row_id` | AO-C-### (B's company), AO-W-### (coworking site), AB-### (brand); referrals AO-R-### and AB-R-### | Stable key; use it as `org_id` in the pipeline log |
| `company` | text | Company or brand name |
| `first_name`, `last_name`, `title` | text, `unknown` surname | The contact shown (formula): the primary, or the backup once `promote_backup = Y`. Filled only when an opened page shows the name |
| `contact_linkedin_url` | URL or blank | Formula from `primary_linkedin_url` or `backup_linkedin_url`, which you paste on Friday (agents never open LinkedIn) |
| `work_email`, `email_status` | address; `verified`, `unverified`, `none` | Formula: looked up from the Enrichment tab by `row_id`. All `none` today |
| `channel` | `email`, `linkedin`, `warm-intro`, `walk-in`, blank | Formula: `warm-intro` when known; `email` once verified; `linkedin` for a named contact; `walk-in` for a top-50 office with nobody named; blank for a brand with nobody named (E skips it) |
| `score`, `score_reason` | 0 to 100; one sentence | Formulas |
| `onsite_band` | CONTRACTS bands | Offices: band of the central Tuesday estimate (an estimate until intake); blank for brands |
| `nearest_stocked_retailer`, `nearest_retailer_grade` | "Store, street"; `store_selector`, `brand_claim`, `unverified` | Brands: best graded store within ten blocks. Only you set `seen_on_shelf`. Blank for offices |
| `why_now`, `why_now_url`, `why_now_date` | text, URL, date | Brands: dated news or listing in 12 months, linked to the page that shows it; offices: a lease reported since 2025-11 |
| `known_to_founder` | Y/N | You set it |
| `startup_cpg_member` | Y, N, unknown | Public Startup CPG participation; never a hook, no points |
| `do_not_contact` | Y/N | Y the same day anyone opts out; never reversed |
| `status` | CONTRACTS section 4 | Lives here and nowhere else (the cell rejects other words) |
| `source_url`, `found_date` | URL, date | Main source of the row and when it was found |

**Daily-view block** (right after the stable columns, same order in the view): `side`, `daily_view_rank`, `rank`, `top50`/`top60`, `check_before_send` (what is left to check), `contact_role`, `contact_status` (`verified-page`, `crowd-listed`, `first-name-only`, `unverified`, `none`), `contact_evidence`, `contact_source_url`, `contact_source_date`. Offices add `title_match`, `street_address`, `floor`, `lease_status`, `onsite_low`, `onsite_high`, `onsite_confidence` and `attendance_signal`. Brands add `product_example`, `category`, `hq_city`, `online_store_url`, `founder_review` and `founder_review_reason`. Both end with `company_group`, `hold_before_outreach`, `hold_reason` and `opt_out_date`.

**Your controls** (yellow):
- `known_to_founder`.
- `hold_before_outreach`: set N after the lobby check.
- `founder_ok_to_queue`: offices; Y lets an out-of-band office in.
- `promote_backup`: Y after a `wrong_person` reply, and the backup becomes the contact everywhere.
- `primary_linkedin_url` and `backup_linkedin_url`.
- Brands only: `founder_review_cleared`, and `retailer_checked_date`, the date you confirmed the store listing through the one-click `retailer_check_url`.

`ready_for_outreach`, `ready_reason`, `review_blocking` and `onsite_founder_call` are computed.

**Contacts.** Each row has a `primary_*` and a `backup_*` block (`first_name`, `last_name`, `title`, `linkedin_url`, `work_email`, `email_status`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_url`, `contact_source_date`, `title_match`, `check_before_send`). The stable contact columns are computed from them. The extras are `contact_name_as_found`, `contact_record_date` (the source's own date; older than 12 months adds a check), `contact_note`, `contact_ny_base`, `linkedin_status`, `contacts_researched` and the backup equivalents, plus `company_group_reason`. Offices also carry `linkedin_company_url` with `linkedin_company_source`.

**Gates and score parts**: `gate_result`, `gate_reason`, `gate_failed` (brands), `score_raw`, the `score_*` parts, `score_reason_core` and (brands) `score_reason_tail`, `channel_base`, `founder_review_type`, and the estimate's workings: `onsite_central`, `onsite_flags`, `onsite_basis`, `onsite_space_check`, `onsite_label`, `onsite_fit_share`, `size_class`, `leased_sf_mentioned`, `leased_sf_source`.

**Research.** Offices carry B's address, headcount, lease, lobby and coworking fields with their sources and dates, plus `a_corrections` (facts this workstream changed, with sources). `lobby_type` is `unknown` unless a lobby source exists, and `lobby_note` keeps B's unsourced value. Brands carry the gate evidence (`shelf_stable_basis`, `health_claim_flag`, `online_store`, `online_store_note`, `revenue_band` with `revenue_basis`), every store within ten blocks with its grade and distance, the why-now type and age, `notes`, and an `enrichment_log` of every field change with its source.

**Outreach tracking (E's columns, empty).** `sequence`, `touch_1_date` to `touch_3_date`, `last_reply_date`, `reply_type`, `call_date`, `call_notes`, `yes_in_principle`, `next_action`, `next_action_date`, `opt_out_date` and `referral_from`, plus E's personalization columns: `street_short`, `why_now_hook`, `product_short`, `call_note_hook`, `how_we_know`, `referrer_ok_to_name` and `office_approvals_complete`. The rules are in `desk-drop-outreach/tracking/csv/clay_tracking_columns.csv`.

**View helpers (formulas, far right)**: `in_flight`, `dnc_any`, `group_key`, `group_blocked`, `eligible`, `view_pick`, `in_daily_view`, `view_slot`, `walk_ok` and `walk_slot` (offices), `review_ok` and `review_slot` (brands), `intact` (the paste guard), `row_order`. Every formula is filled down to row 1000, so a referral row typed at the bottom works at once.

## 3. The morning routine (about 12 to 13 minutes) and the Friday prep

Ten messages a day is the plan's pace, about five per side. Each view shows ten, so rows 6 to 10 are spares. Research happens on Friday, not at send time. This timing is an estimate from a walk without logins; time it in the first live week.

| Clock | Step | What you do |
| --- | --- | --- |
| 0:00 to 3:00 | Log yesterday | For each reply, bounce or opt-out, set `status` (the cell takes CONTRACTS words only) and E's columns. For any opt-out, in any words, set all three: `status = do_not_contact`, `do_not_contact = Y`, `opt_out_date` = today. The cells turn red if they disagree. Never reverse it. For a wrong person, set `promote_backup = Y` and `status = new`. |
| 3:00 to 4:00 | Open the two daily views | They have already updated. Take the top five of each. |
| 4:00 to 11:00 | Forty seconds a row, ten rows | Read `score_reason` and `check_before_send`. Open the LinkedIn URL you pasted on Friday and confirm the person still holds the title. If a row still says "find ... on LinkedIn", do it or take a spare. Use a brand's store line only if `retailer_checked_date` is this week. If the person has left, set `wrong_person` and `promote_backup = Y`. |
| 11:00 to 12:00 | Export | File > Download > CSV on each daily-view tab. Google names the files "clay-icp-tables - Daily view - Offices.csv" and "... - Brands.csv". Rename them `daily-view-offices.csv` and `daily-view-brands.csv` and save them in `clay-icp-tables/live/`. E's draft maker reads them from there (from `desk-drop-outreach/messages/`: `python3 _render/fill.py drafts --daily ../../clay-icp-tables/live/daily-view-offices.csv ...`). Export first, because queued rows leave the live view. |
| 12:00 to 13:00 | Queue | Set `status = queued` on the rows you send today. Their company group is blocked at once. Sending is E's routine. |

**Friday prep (about 60 to 90 minutes; the first Friday longer)**, all in the Sheet:
1. *LinkedIn batch.* Filter `eligible = Y` and work down the next 25 rows per side. Where `primary_linkedin_url` is blank, find the person on LinkedIn and paste the profile URL. Where a URL came from another page, open it and confirm the name and title. At 60 to 90 seconds a row this is most of the hour, and it shrinks once verified emails arrive.
2. *Store check.* For the next 25 eligible brands with a `store_selector` line, click `retailer_check_url`, which opens the store's own catalog answer with no store picker. If the product is listed, type today's date in `retailer_checked_date`.
3. *Founder review batch.* On the Founder review tab, read each reason, then set `founder_review_cleared = Y` or `status = no` on the Brands tab. The first Friday holds the whole backlog of 107; clear the top 30 first.
4. *Walks and holds.* Plan the lobby walk from the Walk list tab. Copy B's walk notes into `hold_before_outreach` (N once the lobby directory shows the company).
5. *Known, referrals and emails.*
   - Mark `known_to_founder` for anyone you know.
   - Add a row at the bottom for each referral: `row_id` AO-R-### or AB-R-###, `company`, the `primary_*` name and title, `do_not_contact = N`, `status = new`, `referral_from` = the referrer's `row_id`, and the referrer's `company_group` if it is the same company.
   - A referral is warm, so it does not wait in the cold daily view, which only takes rows that passed the researched gates. Write to it yourself with E's referral message (`desk-drop-outreach/messages/08-warm-intro-referral-walk-in.md`, part 2) and set `status = queued` when you do. A queued colleague blocks the rest of that company at once.
   - Paste the week's Clay or Hunter email results on the Enrichment tab. Never paste anything over the Offices or Brands tabs.
6. *Save the live tables.* Download the Offices, Brands and Enrichment tabs into `clay-icp-tables/live/` as `offices-live.csv`, `brands-live.csv` and `enrichment-live.csv`.

Nothing in either routine needs Python.

## 4. Seeding and refresh

**Where the rows came from.**
- *Offices*: every company in B's `companies.csv` (168) and `near_miss.csv` (108), plus B's 32 coworking sites, each with B's address source and date.
- *Brands*: five research slices (311 rows), New York brands first, deduplicated on name and domain. The sources were:
  - the Whole Foods store-scoped catalogs for Union Square, NoMad and Chelsea (the only `store_selector` evidence);
  - brand store locators (Stockist, Storepoint);
  - Startup CPG public pages (newswire, Shelfie finalists and winners, the Summer Fancy Food Show pavilion list);
  - the Summer Fancy Food Show 2026 exhibitor directory and SFA's sofi lists;
  - New York CPG trade press (Snack and Bakery, BevNET, Food Business News).
- *Not used*: Trader Joe's 14th Street was skipped because it sells its own label only. Eataly's online catalog holds its imports, not the Flatiron store's local set. Instagram and LinkedIn were not opened.
- *Contacts*: employer team, about and leadership pages, The Org position pages (labelled `crowd-listed`), and press, event and podcast pages. LinkedIn was never opened.
- *Company LinkedIn pages*: read only from links on the company's own site or its The Org record.

**How it rebuilds** (whoever maintains the files, not the morning routine).
- `python3 -B clay-icp-tables/_build/build_all.py` rebuilds both tables, the views, the Clay import files and the workbook in seconds, offline.
- Researched facts are never typed into the tables. A change goes into a sourced corrections file (`_work/stage3_corrections.csv`, `_work/stage3_contact_fixes.csv`, `_work/contacts_s3_entrants.csv`, `_work/contacts_r9_*.csv`), and the build applies it.
- **Once outreach has started, save the live tables first** (Friday step 6). The build then carries over status, do-not-contact, opt-outs, holds, your OKs, known flags, `promote_backup`, LinkedIn URLs, review clearances, store-check dates, groups, the Enrichment rows, any contact typed into a `primary_*` or `backup_*` block, E's columns and referral rows. A do-not-contact or opt-out is never undone. Without the live files, a rebuild starts every row at `status = new`.
- `python3 -B clay-icp-tables/_build/test_workbook.py` recalculates the workbook in LibreOffice and compares every formula cell and every view with the Python twin in five scenarios: baseline, founder edits, an Enrichment paste, a paste over the Offices tab, and too few ready rows. It also checks that the strict drop-down lists reject typos. Set `A_SOFFICE` to the path of a LibreOffice 25.8 `soffice` to run it on a second version. It passes on 24.2 and 25.8 (`_work/test_workbook/last_run_*.txt`).

**Refresh cadence.**
- Daily: the routine above.
- Weekly: the Friday prep, plus a claims scan (`_build/scan_claims.py`: homepage, catalog, About and FAQ) of brands entering the next week's views.
- **Before Thursday 2026-11-19** (when the 38 ready offices run out at five a day): research contacts for office ranks 51 to 100 with the Claygent office prompt below. Today 49 of the ranks 1 to 100 have a named person. Walk the 13 offices on the Walk list in the first week, so walk-ins top up the pool.
- Monthly: re-run B's seed lists if B publishes new ones, rebuild and re-score.

## 5. Clay setup (about 30 minutes; steps marked LOGIN need yours)

**The Google Sheet is the only table of record.** Status, do-not-contact, opt-outs, holds, reviews and E's columns live there and nowhere else. Clay is the research and email engine. Its import files carry no status, control, formula or tracking column, so nothing Clay exports can overwrite them. Results come back through one door, the Sheet's Enrichment tab, which reads only `work_email`, `email_status`, `backup_work_email` and `backup_email_status` by `row_id`. A contact Clay finds is typed into the row's empty `primary_*` or `backup_*` block with its source URL and date. Never paste a Clay export over the Offices or Brands tab: the views go blank with a warning if anyone does.

1. LOGIN. Open Google Drive, upload `clay-icp-tables.xlsx` and save it as a Google Sheet (File > Save as Google Sheets). Check that the two Daily view tabs show ten rows each, the Walk list 13 and the Founder review 30, and that no view says "pasted over". Google Sheets itself is unverified, founder to confirm.
2. LOGIN. Create a Clay account on the Free plan (no card). Free allows "up to 200 rows per table", 100 data credits and 500 actions a month, multi-provider waterfalls, Claygent and your own API keys ([clay.com/pricing](https://www.clay.com/pricing), opened 2026-10-24).
3. LOGIN. Create a new workbook with two tables, importing `clay-import/offices-clay-import.csv` and `clay-import/brands-clay-import.csv`. Each holds 175 passed rows: every ready row first (38 offices, 66 brands), then the best other passed rows. That leaves 25 rows under the 200-row cap for referrals. Set `row_id` as the unique key and keep dates as text. `score_at_build` and `ready_at_build` are build-day snapshots for sorting only.
4. Run the research prompts and the waterfall below on the top rows only, in the order given, and stop at the free allowance.
5. Each Friday, export the email columns (`row_id`, `work_email`, `email_status`, and the backup pair if run) and paste them at A1 of the Sheet's Enrichment tab, header row included. Column order does not matter. The views pick up verified emails at once, and the channel turns to `email`.

**Claygent research prompts** (Clay's web-research agent; credits per row founder to confirm in Clay). Run them only on rows that passed the gates. Type each answer into the Sheet with its source URL and date, and leave a field `unknown` when no page shows it.

*Office pantry owner* (ranks 51 to 100 first, then any top-50 row with nobody named, then backups):
> Find the person who runs the office, workplace or pantry at {company}'s New York office at {street_address}. Look only at public business pages: the company's own team, about or careers pages, press releases, The Org, and conference or podcast pages. Target titles, best first: Office Manager, Office Coordinator, Workplace Experience Manager, Head of Workplace, Facilities Manager, People Operations, Executive Assistant to the CEO. Return first name, last name, exact title, the URL of the page that names them, that page's date, and whether the page places them in New York. Return "none found" if no page names a person. Do not guess or construct an email address. Do not return phone numbers, home locations or anything personal.

*Office address and attendance check* (any row before the first touch):
> Does {company} have staff working at {street_address}, New York, today? Quote the sentence and give the URL and date of the page that says so. Separately, quote the company's own words on how many days a week staff are in the office, with URL and date. Answer "not found" rather than infer.

*Brand founder and marketing lead* (the 35 top-60 brands without a marketing lead first):
> For the snack or beverage brand {company} ({website}), find the founder or CEO and the person who leads marketing. Use the brand's own site, press releases, trade press, The Org, and podcast or event pages. Return for each: first name, last name, exact title, source URL and date. Return "none found" if no page names them. No emails, phones or personal details.

*Brand why-now and claims check*:
> For {company} ({website}): (1) the most recent dated news in the last 180 days (launch, new retailer, funding, award) with URL and date; (2) quote any wording on the brand's own site, including product pages, About and FAQ, that says the product or an ingredient supports, improves, boosts or regulates a body or mental function, or names a disease or condition, with the page URL; (3) quote the shelf life if the brand states it. Answer "none found" for any part with no page.

**Email waterfall spec** (verified work email, top 50 offices and top 60 brands only).

| Item | Spec |
| --- | --- |
| Rows | `gate_result = pass`, `top50 = Y` or `top60 = Y`, `do_not_contact = N`, a full name (`last_name` not `unknown`) and a website domain. Today: 33 office and 55 brand primaries. Backups only when a primary bounces or leaves. |
| Inputs | `primary_first_name`, `primary_last_name`, `domain` |
| Step 1, find | Clay's work-email waterfall. Put a provider you hold a free key for first: Hunter Free gives 50 credits a month, 1 per email found and 0.5 per verification ([hunter.io/pricing](https://hunter.io/pricing), opened 2026-10-24). Clay charges no data credits on your own key, only actions (Clay pricing FAQ). Then add the Clay-credit providers in the order Clay's panel lists them, and stop at the first email found. Credit cost per provider and lookup: founder to confirm in Clay's panel. Clay does not charge when an enrichment returns nothing (Clay pricing FAQ). |
| Step 2, validate | A validation step (Clay's validator or Hunter's verifier). Map deliverable or valid to `email_status = verified`. Map accept-all, catch-all, risky or unknown to `unverified` (E sends LinkedIn instead). Map invalid or not found to `none` with a blank email. |
| Never | Pattern-guess an address, run the waterfall on gated-out rows, or enrich personal emails or phones. |
| Stop point | When the next run would exceed the free allowance (100 data credits and 500 actions a month on Clay Free, 50 Hunter credits), stop and decide. Two months of free allowances cover the 88 primaries. One month of Hunter Starter covers them at once (below). |

## 6. Running cost

| Item | Cost | Recommendation |
| --- | --- | --- |
| Google Sheets | $0 (inside the Google Workspace seat the plan already budgets) | Use |
| Clay Free | $0 | Use for research and the waterfall within its allowance |
| Hunter Free (own key in Clay) | $0 | Use first in the waterfall |
| Clay Launch | $185 a month billed monthly, $167 a month billed yearly; 2,500 data credits and 15,000 actions a month ([clay.com/pricing](https://www.clay.com/pricing), 2026-10-24) | Not recommended: on its own it is over the plan's $60 a month software cap |
| Hunter Starter | $49 a month billed monthly, $34 a month billed yearly; 2,000 credits a month ([hunter.io/pricing](https://hunter.io/pricing), 2026-10-24) | Only with your written yes, for one month, if you want all 88 emails at once. It fits the cap only if the rest of the stack stays under $11 that month |
| Clay data credits, if topped up | From $0.05 each (Clay pricing FAQ); top-ups are a paid-plan feature | Not needed for the free route |

Recommended running cost for this workstream: **$0 a month.** Credits used so far: none.
