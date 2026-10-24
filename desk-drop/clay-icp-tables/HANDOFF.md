# Handoff: Clay ICP tables (workstream A)

2026-10-24. Paths are relative to `desk-drop/`. CSVs are UTF-8 with one header row, snake_case columns, `Y`/`N` booleans, `YYYY-MM-DD` dates (source dates may be `YYYY-MM` or a year), semicolon lists (CONTRACTS section 5).

## 1. What A consumes

| From | File | Used for | State |
| --- | --- | --- | --- |
| B, cluster map | `cluster-1-flatiron/companies.csv`, `near_miss.csv`, `coworking.csv`, `buildings.csv` | Every office row: company, website, address with its source and date, `in_boundary`, `blocks_outside`, headcount and its sources, `hq_in_nyc`, `parent_company`, `lease_status`, `move_in_date`, `in_coworking`, `coworking_id`, `pantry_control`, lobby type, COI, confidence, notes | Used as published. B's boundary replaces the provisional 14th to 30th Street box. B's holds (lease signed but move not confirmed, address conflict, still in coworking, possibly closed) become `hold_before_outreach` |
| B | `cluster-1-flatiron/retailers.csv`, `boundary.geojson`, `_build/boundary.py` (imported read-only, no bytecode written) | The ten-block test for brand stores (B's grid measure, 794 m); stores B did not list were placed with `_shared/geocode.py` | Used |
| B | `cluster-1-flatiron/_build/coldefs.py` (read-only) | B's own column definitions feed A's dictionary for B-derived columns | Used |
| D, identity | `desk-drop-identity/` | Nothing needed: the tables carry no brand marks. The working name sits in one workbook cell, `Routine!B1` | Read, not used |
| G, legal pack | `desk-drop-legal-pack/02-email-footer-and-checklist.md` | The opt-out rule: same day, never reversed. Encoded as `do_not_contact`, `opt_out_date` and the build's carry-over (a Y is never undone) | Used |
| H, financial model | `financial-model/HANDOFF.md`, `_work/build_model.py` inputs | `org_id` = the Clay `row_id` for every pipeline event; software budget $60 a month (`software_monthly`), which the running cost respects ($0 recommended) | Used |
| E, outreach | `desk-drop-outreach/HANDOFF.md` section 2.1, `tracking/csv/clay_tracking_columns.csv`, `messages/03-personalization-fields.csv` | E's requested columns and daily-view rules (section 2 below) | All honored |

## 2. What A feeds E (outreach engine)

**Files.** `clay-icp-tables/daily-view-offices.csv`, `clay-icp-tables/daily-view-brands.csv` (ten rows each today), `clay-icp-tables/offices.csv`, `clay-icp-tables/brands.csv`, the live views in `clay-icp-tables/clay-icp-tables.xlsx`, and the dictionary in `clay-icp-tables/column-dictionary.csv` (also the workbook's Dictionary tab).

**CONTRACTS 6.2 stable columns: confirmed exactly.** Both tables and both daily views carry all 23, under these names, in this order, as the first 23 columns: `row_id`, `company`, `first_name`, `last_name`, `title`, `contact_linkedin_url`, `work_email`, `email_status`, `channel`, `score`, `score_reason`, `onsite_band`, `nearest_stocked_retailer`, `nearest_retailer_grade`, `why_now`, `why_now_url`, `why_now_date`, `known_to_founder`, `startup_cpg_member`, `do_not_contact`, `status`, `source_url`, `found_date`. None will be renamed or dropped.

How they are filled today:
- `first_name`, `last_name`, `title`: only when an opened page shows the name. A snippet-only name stays in `contact_name_as_found` with `contact_status = unverified`, and `first_name` stays blank (E's greeting falls back to "Hello,"). `last_name = unknown` where only a first name is public.
- `work_email` blank and `email_status = none` on every row: no waterfall has run (0 of 110 top rows verified, 0%). `contact_linkedin_url` is filled on 12 of the top-60 brand primaries (16 brand rows in all) and on no office primary; the founder pastes the rest in the morning routine.
- `channel`: `linkedin` for a named contact until an email is verified; `walk-in` for a top-50 office with nobody named (19 rows); blank for a brand with nobody named (1 top-60 row, Goody's Granola), which E's fallback skips. `warm-intro` appears only when the founder marks `known_to_founder = Y`.
- `onsite_band`: offices only; blank on brands. `nearest_stocked_retailer` and `nearest_retailer_grade`: brands only; blank on offices. No agent sets `seen_on_shelf`.
- `startup_cpg_member`: `Y` or `unknown` on brands; `unknown` on offices.
- `status = new` and `do_not_contact = N` on every row until outreach starts.

**Daily views.** CONTRACTS 6.2's rule (the ten highest-scored rows with `status = new` and `do_not_contact = N`, one contact per company, no company with a contact in flight), plus, at E's request and for outreach-readiness:
- `ready_for_outreach = Y`: passed the hard gates, `hold_before_outreach` not Y, a contact named on an opened page, and for offices a Tuesday band of 40 to 250 or `founder_ok_to_queue = Y` (E's rule that `under-40` needs the founder's yes; `over-500` is not queued).
- `opt_out_date` blank (E: never bring back an opted-out row).
- Signed-not-occupied and moving-out offices are held (`hold_before_outreach = Y`) until the founder clears them after the lobby check (E's request).
- One row per `company_group` (rows that share a parent, an operator, a company name or a named person: Carbyne and Prepared 911 under Axon; coworking chains; Moshi, Bruce Cost and Brooklyn Crafted; PRETZELIZED and LesserEvil, which share a marketing name), and none from a group with a row in flight (`queued` to `materials_sent`) or a do-not-contact row.
- Only the primary contact is in the view; the backup stays in the table.
- `side` is carried (E's request).

Daily-view columns after the 23: offices `side`, `daily_view_rank`, `rank`, `top50`, `check_before_send`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_url`, `contact_source_date`, `title_match`, `street_address`, `floor`, `lease_status`, `onsite_low`, `onsite_high`, `onsite_confidence`, `attendance_signal`, `company_group`, `hold_before_outreach`, `hold_reason`, `opt_out_date`; brands `side`, `daily_view_rank`, `rank`, `top60`, `check_before_send`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_url`, `contact_source_date`, `product_example`, `category`, `hq_city`, `online_store_url`, `founder_review`, `founder_review_reason`, `company_group`, `hold_before_outreach`, `hold_reason`, `opt_out_date`.

**Columns E reads that are not in 6.2: now stable.** `street_address` and `lease_status` (offices), `product_example`, `category` and `hq_city` (brands), `hold_before_outreach` and `hold_reason` (both; brands are always N). `hq_city` can carry a bracketed evidence note, which E's fill already strips. `category` is always a CONTRACTS section 4 key. E can set its `source_column` cells to these names for good.

**E's columns: added, empty, on both tables** (exact names from `tracking/csv/clay_tracking_columns.csv` and `messages/03-personalization-fields.csv`): `sequence`, `touch_1_date`, `touch_2_date`, `touch_3_date`, `last_reply_date`, `reply_type`, `call_date`, `call_notes`, `yes_in_principle`, `next_action`, `next_action_date`, `opt_out_date`, `referral_from`; personalization `street_short` (offices), `why_now_hook`, `product_short` (brands), `call_note_hook`, `how_we_know`, `referrer_ok_to_name`; routing `office_approvals_complete` (brands). The workbook gives `status`, `do_not_contact`, `channel` and `email_status` drop-down lists with CONTRACTS values.

**Writes E makes** go into these tables only (the Sheet until Clay is set up, then Clay; never both). Before anyone rebuilds the files, the live tables are saved as `clay-icp-tables/live/offices-live.csv` and `brands-live.csv`; the build carries `status`, `do_not_contact`, `opt_out_date` (an opt-out forces `do_not_contact = Y`), holds, founder OKs, known flags, LinkedIn URLs, emails, swapped contacts, all of E's columns and E's referral rows. Tested on a scratch copy (`clay-build-sheet.md`, section 4).

**Checked against E's draft maker (2026-10-24).** `desk-drop-outreach/messages/_render/fill.py drafts` was run on both daily views with a scratch copy of E's slot state (`domain_ready` and `name_decided` set to Y in the copy only; output in the scratchpad, nothing written to E's folder). Email messages skip every row ("no work_email", expected at 0% verified). LinkedIn messages drafted correctly for the two brand rows that carry a LinkedIn URL (the warm-up cap that day is two), with the first name, company and the store-page retailer line filled; every other row skipped with "no contact_linkedin_url", which is exactly what step 4 of the morning routine fills.

**Other columns E may use**: `check_before_send` (the one-minute checks left: paste the LinkedIn URL, confirm an old record, re-check the Whole Foods listing with a link, read a founder-review note), `contact_evidence`, `contact_record_date`, `founder_review_reason` (brands), `title_match` (offices).

## 3. What A feeds H (financial model) and F (operations)

- H: use `row_id` as `org_id` in `pipeline_log.csv` (H's recommendation). IDs are stable across rebuilds: `AO-C-###` from B's `B-C-###`, `AO-W-###` from `B-W-###`, `AB-###` from `_build/id_registry_brands.json`, keyed on the brand's domain.
- F: nothing directly. Signed offices and paid brands reach F through E's `handoff/` files, keyed by `clay_row_id` = `row_id`.

## 4. Where A deviates from CONTRACTS

1. Extra daily-view filters beyond 6.2 (readiness, holds, opt-out date, company groups), listed in section 2. They only remove rows; every row in a view still meets 6.2's rule.
2. `channel` can be blank (a brand with no named person), outside 6.2's four values. E's fallback treats blank as "skip".
3. `startup_cpg_member` is `unknown`, not N, on offices: an office could be a CPG company, and no source was checked.
4. The table of record is the Google Sheet made from `clay-icp-tables.xlsx` until the founder sets up Clay (no login exists). CONTRACTS says status lives in the Clay tables only; the Sheet is the same table, and the build sheet tells the founder to pick one on day one and never edit status in both.
5. Clay Free holds 200 rows per table, so Clay gets the 175 best passed rows per table (`clay-import/`); the gated-out and lowest rows stay in the CSVs. Those rows are never contacted, so no status is split.
