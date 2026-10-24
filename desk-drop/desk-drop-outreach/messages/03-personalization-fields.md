# 03 · Personalization fields: what each `{token}` is, where it comes from, and its fallback

Version 1.3 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** Every `{token}` in the message files, mapped to a Clay column, with the rule for using it and the fallback when the column is blank, stale or unproven. The machine-readable copy is `03-personalization-fields.csv`; the fill script in `_render/` reads it.

**Which columns.** The Clay tables' stable columns are fixed by CONTRACTS section 6.2. Since review round 3 the few non-stable source columns below are **stable** too: `clay-icp-tables/HANDOFF.md` (published 2026-10-24, section 2) confirms `street_address` and `lease_status` (offices), `product_example`, `category` and `hq_city` (brands) and `hold_before_outreach` with `hold_reason` (both) under these names, says none will be renamed or dropped, and has added E's 13 tracking columns, the six personalization columns and `office_approvals_complete` to both tables. The table of record is the Google Sheet made from `clay-icp-tables/clay-icp-tables.xlsx` until you set up Clay, then Clay (never both; `clay-icp-tables/clay-build-sheet.md`): every "Clay" below means that table.

**What the merge check found in A's and B's real files (2026-10-24).** A's 311 brand research rows write an unconfirmed field as `unknown` (`product_example` "unknown (site unreachable)", `nearest_stocked_retailer` "unknown") and mark doubtful cities "Brooklyn (unverified, founder to confirm)"; some `why_now_date` cells hold a month only (`2026-06`) or nothing. `_render/fill.py` now treats any `unknown` or "unverified, founder to confirm" value as blank, so its fallback is used and the word never reaches a recipient, and reads a month-only date as the 1st of that month (the oldest it can be) for the 120-day rule. `category` values are all CONTRACTS section 4 keys; `nearest_retailer_grade` holds only `store_selector`, `brand_claim` and `unverified`. On B's 168 office addresses the `{area}` rule gives a clean street name every time ("Park Avenue South", "West 23rd Street", "Broadway"). 30 of B's companies are `signed-not-occupied`: see the routing table.

**A's draft tables (checked at the end of the merge, 2026-10-24).** `clay-icp-tables/offices.csv` (308 rows) and `brands.csv` (311 rows) appeared during the merge, still without `HANDOFF.md` or daily views. They carry every CONTRACTS 6.2 stable column under its CONTRACTS name, and the provisional columns above under the names used here (`street_address`, `lease_status`, `product_example`, `category`, `hq_city`), so no `source_column` changes. What they do not carry yet: E's 13 tracking columns and six personalization columns; any verified email (every row is `email_status = none`, `channel = linkedin`); any office contact (all 241 offices that pass the gates have `primary_contact_status = none`); and LinkedIn profile URLs for most brands (2 of the top 60). `hq_city` often carries its evidence in brackets ("Brooklyn (privacy policy: ...)"): the city is now printed without the bracket, and never when the cell says unverified. `lease_status` also takes `moving-out`, `open` and `unverified`; `moving-out` is skipped like `signed-not-occupied`. Run on A's real top ten per side, the draft maker wrote no drafts and said why for each row (no address on the row): the right answer until the contacts exist. With placeholder addresses in a scratch copy, all 20 drafts read correctly ("Question about the pantry at Cognitiv", "offices around Park Avenue South"; "Whole Foods Market NoMad's store page lists Fine & Raw, and that store is near the offices I'm writing to.").

**Columns E adds to the Clay tables.** CONTRACTS 6.2 lists E's conversation-tracking columns (`sequence`, `touch_1_date` ... `referral_from`). For personalization E also adds, to the same tables (never a second store):

| Column | Table | What it holds | Who fills it, when |
| --- | --- | --- | --- |
| `street_short` | Offices | The street name, no number: "Park Avenue South" | A Clay formula on the address column, or you, when the row is queued |
| `why_now_hook` | both | One sentence of plain fact from `why_now`: "Congratulations on the Target launch." | You, when the row is queued (about 15 seconds), after opening `why_now_url`; or a Clay AI column you read before use |
| `product_short` | Brands | The product's own name in two to four words | A Clay formula or you, when queued |
| `call_note_hook` | both | Twelve words or fewer the person said on the call | You, within ten minutes of the call |
| `how_we_know` | both | Fifteen words or fewer, true and checkable | You, for `known_to_founder = Y` rows |
| `referrer_ok_to_name` | both | Y once the referrer agreed to be named | You, from their reply |

All six are optional. Every one has a fallback, so a blank never breaks a message.

**The floor.** A fallback keeps the copy readable; it does not make a message personal. If a touch 1 would go out with nothing about the person or company in it (no name, no company, no street, no store, no why-now), `_render/fill.py` warns "fix the row before sending". In a real daily view that means the row is missing its company or contact and should not have been queued.

---

## The printed fields

| Token | Clay column | Rule | Fallback |
| --- | --- | --- | --- |
| `{greeting}` | `first_name` | "Hi {first_name}," for a real first name | "Hello," (blank, or a role word such as team, office, info, admin, hr) |
| `{company}` | `company` | Trailing Inc, LLC, Corp, Co, Ltd, PBC removed. Sentences are built so the fallback reads: "the pantry at {company}", never "the {company} pantry" | "your office" (offices), "your brand" (brands) |
| `{area}` | `street_short`, else the address column | Street name only, W and E spelled out | the cluster name: "Flatiron, NoMad and Union Square" |
| `{?why_now_hook}` | `why_now_hook` with `why_now_date`, `why_now_url` | Only if filled, under 120 days old on the send date, and you opened the source | left out. If the row has a fresh `why_now` (120 days or less, with its URL) and no hook yet, the draft maker says so on the draft's first line and in its output: write the hook in Clay, or send without it |
| `{product}` | `product_short` (from `product_example`) | Two to four words, the product's own name | the brand name, then "your product" |
| `{?retailer_line}` | `nearest_stocked_retailer`, `nearest_retailer_grade` | By grade, below | left out (grade `unverified` or blank) |
| `{category_phrase}` | `category` (brand intake `category` later) | "a chips and crisps brand" (CONTRACTS section 4 label) | "an emerging brand" |
| `{category_short}`, `{category_only_phrase}` | `category` | "chips and crisps"; "the only chips and crisps brand" | "brand in your category"; "the only brand in your category" |
| `{brand_name}`, `{brand_category_phrase}`, `{?brand_from_city}`, `{?retailer_for_office}` | the brand's row, inside an office email (10, step 7) | so the brand's fields never mix with the office's `{company}` | "the brand"; "an emerging brand"; left out; left out |
| `{first_name_or_founder}` | `first_name` | the founder's first name, in an ask to a connector (08) | "the founder" |
| `{?from_city}` | `hq_city` | " from Queens"; never a value marked unverified | left out |
| `{call_note_hook_line}` | `call_note_hook` | "Thanks again for today, and for the detail about {call_note_hook}." | "Thanks again for the time today." |
| `{referrer_name}` | `referral_from` → that row, plus `referrer_ok_to_name` | Named only with Y | not named; ordinary first touch |
| `[HOW WE KNOW EACH OTHER]` | `how_we_know` | True, checkable | warm template not used |

Config tokens, not from Clay: `{BRAND_NAME}` (from `desk-drop-identity/brand.json`, the one place the name is set), `{CLUSTER}` and `{CLUSTER_SHORT}` (from `04-slot-state.csv`, `cluster_name` and `cluster_short`), `{SIGNATURE}` (file 02).

### The retailer sentence, by evidence grade

The grade decides the verb. A sentence never claims more than its evidence (CONTRACTS section 4).

| `nearest_retailer_grade` | Discovery wording | Selling wording |
| --- | --- | --- |
| `seen_on_shelf` (only you set it, after seeing it) | "I saw {product} on the shelf at {retailer}, near the offices I'm writing to." | "I saw {product} on the shelf at {retailer}, a short walk from them." |
| `store_selector` | "{retailer}'s store page lists {product}, and that store is near the offices I'm writing to." | "{retailer}'s store page lists {product}, a short walk from them." |
| `brand_claim` | "Your store locator lists {retailer}, near the offices I'm writing to." | "Your store locator lists {retailer}, a short walk from them." |
| `unverified` or blank | left out | left out |

`{retailer}` is the part of `nearest_stocked_retailer` before the first comma ("Whole Foods Market Union Square"). "Near" and "a short walk" are true because the Clay table only records a nearest retailer inside or within ten blocks of the cluster (A's gate). In selling copy the retailer sentence comes after the roster sentence, so "them" means the offices.

## The routing fields (never printed)

| Clay column | What it decides |
| --- | --- |
| `channel` | Which file: `email` 05 or 06, `linkedin` 07, `warm-intro` 08 part 1, `walk-in` 08 part 3 |
| `email_status` | `verified`: email allowed. `unverified` or `none`: LinkedIn or walk-in |
| `known_to_founder` | Y with `how_we_know`: the warm direct email (08, 1c) |
| `startup_cpg_member` | Never printed, never used as a hook |
| `do_not_contact` | Y: nothing, on any channel, ever |
| `status` | Touch 1 only from `queued`; touches 2 and 3 only from `contacted` with no reply |
| `onsite_band` | Never printed. `under-40` needs your yes before queueing |
| `lease_status` (from `cluster-1-flatiron/companies.csv`, stable in A's tables) | `signed-not-occupied` (not moved in yet) or `moving-out` (leaving): no first touch until the lobby directory shows the company is there to stay (B's handoff to E); the draft maker skips these rows. `occupancy-unconfirmed`, `open` or `unverified`: send, but the email says "around {area}", never "your new office" |
| `why_now_date` | The 120-day freshness rule |
| `hold_before_outreach` and `hold_reason` (A's tables, stable) | Y: nothing on any channel until you clear it in Clay; the draft maker skips the row and prints the reason (45 office rows on 2026-10-24, most "lease signed, move not confirmed") |
| `opt_out_date` | Filled: an opt-out, never reversed; the draft maker skips the row even if `do_not_contact` was not set |
| `office_approvals_complete` (brands; E adds it) | Y once every office on the brand's route has said yes (10 step 7). Until then no agreement or invoice (11 steps 6 and 7) |

## Two filled examples per sequence

`examples/` holds each sequence filled twice at phone width (390 px): once from a full SAMPLE row and once with every fallback triggered. Their rows are in `examples/SAMPLE-rows.csv`; no real daily view existed on 2026-10-24. `_render/HOW-TO-RUN.md` says how to rebuild them, and how to make paste-ready drafts from a real daily view.

## Changelog

- Round 1 (2026-10-24): mapped every token to the CONTRACTS 6.2 stable columns; six optional E columns added to the same tables; fallbacks for every field; the retailer sentence tied to the evidence grade.
- Round 2 (2026-10-24): after the fallback renders, sentences built so the company fallback reads everywhere ("the pantry at your office"); category and city tokens split; the brand's own tokens inside office emails; capital letters restored where a sentence starts with a fallback.
- Round 3 (2026-10-24): the personalization floor (a warning when a touch 1 prints nothing about the person); CSV regenerated to list every token the fill script implements.
- Merge (2026-10-24): checked the field map against A's research rows, A's draft `offices.csv` and `brands.csv` and B's office addresses (no Clay HANDOFF or daily view yet): `unknown` and "unverified, founder to confirm" values now fall back instead of printing, month-only why-now dates are read as the 1st, and `lease_status` = `signed-not-occupied` rows (and `moving-out`) are not queued (B's handoff to E); the draft maker skips a row with no address for its channel, and sends email only to `email_status = verified`.
- Review round 1 (2026-10-24): three routing columns the draft maker now reads: A's `hold_before_outreach` (with `hold_reason`), `opt_out_date`, and `office_approvals_complete` on brand rows.
- Review round 2 (2026-10-24): the draft maker flags a row whose `why_now` is fresh (120 days or less, with a URL) but whose `why_now_hook` is still blank, so the hook is not silently dropped.
- Review round 3 (2026-10-24): A published `clay-icp-tables/HANDOFF.md`; the provisional source columns are now stable (no `source_column` changed), E's columns are in A's tables, and the table of record is A's Google Sheet until Clay is set up.
