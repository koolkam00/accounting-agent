# Handoff: Clay ICP tables (workstream A)

2026-10-24, updated after independent review round 1. Paths are relative to `desk-drop/`. CSVs are UTF-8 with one header row, snake_case columns, `Y`/`N` booleans, `YYYY-MM-DD` dates (source dates may be `YYYY-MM` or a year) and semicolon lists (CONTRACTS section 5).

## 1. What A consumes

| From | File | Used for | State |
| --- | --- | --- | --- |
| B, cluster map | `cluster-1-flatiron/companies.csv`, `near_miss.csv`, `coworking.csv`, `buildings.csv` | Every office row: company, website, address with its source and date, `in_boundary`, `blocks_outside`, headcount and its sources, `hq_in_nyc`, `parent_company`, `lease_status`, `move_in_date`, `in_coworking`, `coworking_id`, `pantry_control`, lobby type, COI, confidence, notes | Used as published. B's boundary replaces the provisional 14th to 30th Street box. B's holds (lease signed but move not confirmed, address conflict, still in coworking, possibly closed) become `hold_before_outreach`. A company B notes as still in coworking until a move now fails the coworking gate (Stash, Agentio). B's lobby type without a lobby source is kept in `lobby_note`, and `lobby_type` reads `unknown`. For coworking sites, `website` is the operator's own domain only |
| B | `cluster-1-flatiron/retailers.csv`, `boundary.geojson`, `_build/boundary.py` (imported read-only, no bytecode written) | The ten-block test for brand stores (B's grid measure, 794 m). Stores B did not list were placed with `_shared/geocode.py` | Used |
| B | `cluster-1-flatiron/_build/coldefs.py` (read-only) | B's own column definitions feed A's dictionary for B-derived columns | Used |
| D, identity | `desk-drop-identity/` | Nothing needed: the tables carry no brand marks. The working name sits in one workbook cell, `Routine!B1`, and no data cell holds it | Read, not used |
| G, legal pack | `desk-drop-legal-pack/02-email-footer-and-checklist.md` | The opt-out rule: same day, never reversed. It is encoded as `do_not_contact`, `opt_out_date` and `status = do_not_contact`. Any one of them blocks the row and its company group (`dnc_any`), and a rebuild never undoes a Y | Used |
| H, financial model | `financial-model/HANDOFF.md`, `_work/build_model.py` inputs | `org_id` = A's `row_id` for every pipeline event. Software budget $60 a month (`software_monthly`); the running cost respects it ($0 recommended) | Used |
| E, outreach | `desk-drop-outreach/HANDOFF.md` section 2.1, `tracking/csv/clay_tracking_columns.csv`, `messages/03-personalization-fields.csv` | E's requested columns and daily-view rules (section 2 below) | All honored |

## 2. What A feeds E (outreach engine)

**Files.**
- The founder's daily downloads of the live views: `clay-icp-tables/live/daily-view-offices.csv` and `daily-view-brands.csv`. The founder downloads them from the Sheet each morning, and they have the same columns as the build files.
- Build-day copies: `clay-icp-tables/daily-view-offices.csv` and `daily-view-brands.csv` (ten rows each today).
- The full tables `clay-icp-tables/offices.csv` and `brands.csv`, and the Friday saves `live/offices-live.csv` and `live/brands-live.csv`.
- `clay-icp-tables/walk-list-offices.csv` and the workbook `clay-icp-tables/clay-icp-tables.xlsx`.
- The dictionary, `clay-icp-tables/column-dictionary.csv` (also the workbook's Dictionary tab).

**CONTRACTS 6.2 stable columns: confirmed exactly.** Both tables and both daily views carry all 23, under these names, in this order, as the first 23 columns: `row_id`, `company`, `first_name`, `last_name`, `title`, `contact_linkedin_url`, `work_email`, `email_status`, `channel`, `score`, `score_reason`, `onsite_band`, `nearest_stocked_retailer`, `nearest_retailer_grade`, `why_now`, `why_now_url`, `why_now_date`, `known_to_founder`, `startup_cpg_member`, `do_not_contact`, `status`, `source_url`, `found_date`. None will be renamed or dropped.

**How they are filled today.** In the workbook they are formulas.
- **Contact columns.** `first_name`, `last_name`, `title`, `contact_linkedin_url`, `work_email`, `email_status`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_*`, `title_match` and `check_before_send` show the *contact shown*. That is the row's `primary_*` block, or the `backup_*` block once the founder sets `promote_backup = Y` after a `wrong_person` reply. The CSVs carry the computed values.
  - A name is filled only when an opened page shows it. A snippet-only name stays in `contact_name_as_found` with `contact_status = unverified`, and `first_name` stays blank (E's greeting falls back to "Hello,"). `last_name = unknown` where only a first name is public.
- **`contact_status` values.** `verified-page` means the employer's own page or dated press. `crowd-listed` (new this round) means the only source is The Org, which prints "Unverified" beside each person; this applies to 24 of the 34 named top-50 office primaries and 9 brand primaries. Such a row is ready, but the founder confirms the person on LinkedIn in the Friday prep. E's copy should not say or imply that the person's own company page lists them.
- **`work_email` and `email_status`.** These are looked up by `row_id` from the Enrichment tab, where the founder pastes Clay or Hunter results. Today every row is blank and `none` (0 of 110 top rows verified, 0%).
- **`contact_linkedin_url`.**
  - Brands: filled on 10 of the top-60 primaries (16 brand primaries in all, plus 5 backups).
  - Offices: no primary has one; one top-50 backup does.
  - The founder pastes the rest in the Friday LinkedIn batch.
- **`channel`.**
  - `warm-intro` when `known_to_founder = Y`;
  - else `email` once `email_status = verified`;
  - else `linkedin` for a named contact;
  - else `walk-in` for a top-50 office with nobody named (16 rows; the 13 that are passed, new and not held are on the Walk list);
  - blank for a brand with nobody named, which E's fallback skips.
- **`score_reason`.** It follows `known_to_founder` and `promote_backup`, so it always explains the current score.
- **Retailer and onsite columns.**
  - `onsite_band`: offices only, blank on brands. It now respects the row's own leased square footage (`onsite_space_check`).
  - `nearest_stocked_retailer` and `nearest_retailer_grade`: brands only, blank on offices. No agent sets `seen_on_shelf`.
  - The founder dates a store check in `retailer_checked_date`. E should use the store line in copy only when that date is within the week; the morning routine says the same.
- **`startup_cpg_member`.** `Y` or `unknown` on brands; `unknown` on offices.
- **`why_now`.** A brand why-now always has a link and a date, and the link is the page that shows it (a product page, not a homepage). A why-now without both earns nothing and moves to `notes`.
- **`status` and `do_not_contact`.** `status = new` and `do_not_contact = N` on every row until outreach starts. The workbook's drop-downs for `status`, `do_not_contact`, `known_to_founder`, `hold_before_outreach` and `promote_backup` reject other input.

**Daily views.** They apply CONTRACTS 6.2's rule: the ten highest-scored rows with `status = new` and `do_not_contact = N`, one contact per company, and no company with a contact in flight. At E's request and for outreach-readiness, they also require:
- `ready_for_outreach = Y`:
  - the row passed the hard gates and `hold_before_outreach` is not Y;
  - a contact is named on an opened page;
  - offices: a Tuesday band of 40 to 250, or `founder_ok_to_queue = Y` (E's rule that `under-40` needs the founder's yes; `over-500` is not queued);
  - brands: no blocking founder review pending (`review_blocking = N` or `founder_review_cleared = Y`).
- No opt-out signal on the row or anywhere in its company group: `do_not_contact = Y`, `status = do_not_contact` or a filled `opt_out_date`, whichever was typed (`dnc_any`). E's rule is never to bring back an opted-out row.
- Signed-not-occupied and moving-out offices are held (`hold_before_outreach = Y`) until the founder clears them after the lobby check (E's request).
- One row per `company_group`, and none from a group with a row in flight (`queued` to `materials_sent`). A group is rows that share a parent, an operator, a company name or a named person: Carbyne and Prepared 911 under Axon; the coworking chains; Moshi, Bruce Cost and Brooklyn Crafted; PRETZELIZED and LesserEvil, which share a marketing name.
- Only the contact shown is in the view; the other person stays in the table.
- `side` is carried (E's request).

In the workbook the views are INDEX/MATCH formulas on numbered slot helpers, so they compute in any spreadsheet app. If someone pastes values over the Offices or Brands tab, every view goes blank with a warning instead of showing stale rows. That case is tested.

**Daily-view columns after the 23.**
- Offices: `side`, `daily_view_rank`, `rank`, `top50`, `check_before_send`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_url`, `contact_source_date`, `title_match`, `street_address`, `floor`, `lease_status`, `onsite_low`, `onsite_high`, `onsite_confidence`, `attendance_signal`, `company_group`, `hold_before_outreach`, `hold_reason`, `opt_out_date`.
- Brands: `side`, `daily_view_rank`, `rank`, `top60`, `check_before_send`, `contact_role`, `contact_status`, `contact_evidence`, `contact_source_url`, `contact_source_date`, `product_example`, `category`, `hq_city`, `online_store_url`, `founder_review`, `founder_review_reason`, `company_group`, `hold_before_outreach`, `hold_reason`, `opt_out_date`.

Unchanged from the first handoff.

**Columns E reads that are not in 6.2: stable.** `street_address` and `lease_status` (offices); `product_example`, `category` and `hq_city` (brands); `hold_before_outreach` and `hold_reason` (both; brands are always N); `company_group` (both). `hq_city` can carry a bracketed evidence note, which E's fill already strips. `category` is always a CONTRACTS section 4 key.

**Columns added this round** (after the daily-view block; none renames an old one):
- Founder controls: `promote_backup`, `onsite_founder_call` (offices), `review_blocking`, `founder_review_cleared`, `retailer_checked_date` and `retailer_check_url` (brands).
- The `primary_*` and `backup_*` contact blocks.
- Score text: `score_reason_core`, plus `score_reason_tail` on brands, and `channel_base`.
- Offices only: `onsite_space_check`, `leased_sf_source`, `lobby_note` and `linkedin_company_source`.
- View helpers at the far right: `dnc_any`, `group_key`, `view_slot`, `walk_ok`/`walk_slot`, `review_ok`/`review_slot`, `intact`.

**E's columns: present, empty, on both tables.** The exact names come from `tracking/csv/clay_tracking_columns.csv` and `messages/03-personalization-fields.csv`:
- Tracking: `sequence`, `touch_1_date`, `touch_2_date`, `touch_3_date`, `last_reply_date`, `reply_type`, `call_date`, `call_notes`, `yes_in_principle`, `next_action`, `next_action_date`, `opt_out_date`, `referral_from`.
- Personalization: `street_short` (offices), `why_now_hook`, `product_short` (brands), `call_note_hook`, `how_we_know`, `referrer_ok_to_name`.
- Routing: `office_approvals_complete` (brands).

**Where E writes, and the Friday paste.**
- **The Google Sheet is the only table of record.** E's writes (status, opt-outs, tracking columns) go into its Offices and Brands tabs.
- **Clay holds no status.** It is the research and email engine. Its import files carry no status, control, formula or tracking column, so nothing exported from Clay can overwrite them, and its results come back only through the Sheet's Enrichment tab.
- **For E's Friday paste into the tracker, use the Sheet's tab downloads, not a Clay export.** Those are `live/offices-live.csv` and `live/brands-live.csv`, with the same headers as `offices.csv` and `brands.csv`, all columns. A Clay export has no `status`, `do_not_contact` or tracking columns. E's README and tracker guide still say "or export the Clay tables"; that option no longer applies (open item for E).
- Before anyone rebuilds, the live tabs are saved into `clay-icp-tables/live/`. The build carries over everything the founder and E wrote and never undoes an opt-out (tested on a scratch copy).

**Checked against E's draft maker (2026-10-24, this round).** `desk-drop-outreach/messages/_render/fill.py drafts` was run on the rebuilt daily views in a scratch copy of the repository (E's slot state set to ready in the copy only; nothing written to E's folder).
- Email messages skip every row with "no work_email", as expected at 0% verified.
- LinkedIn messages drafted correctly for rows with a LinkedIn URL, including two office rows given sample URLs in the copy, with the first name, company and retailer line filled.
- Rows without a URL skip with "no contact_linkedin_url", which is exactly what the Friday LinkedIn batch fills.

**Other columns E may use**: `check_before_send`, `contact_evidence`, `contact_record_date`, `founder_review_reason` (brands), `title_match` (offices), `linkedin_company_url` (offices, linked from the company's own site or The Org; LinkedIn itself never opened).

## 3. What A feeds H (financial model) and F (operations)

- **H.** Use `row_id` as `org_id` in `pipeline_log.csv` (H's recommendation). IDs are stable across rebuilds:
  - `AO-C-###` from B's `B-C-###`;
  - `AO-W-###` from `B-W-###`;
  - `AB-###` from `_build/id_registry_brands.json`, keyed on the brand's domain;
  - referral rows the founder adds use `AO-R-###` and `AB-R-###`.
- **F.** Nothing directly. Signed offices and paid brands reach F through E's `handoff/` files, keyed by `clay_row_id` = `row_id`.

## 4. Where A deviates from CONTRACTS

1. **Extra daily-view filters beyond 6.2**: readiness (including blocking founder reviews for brands), holds, any do-not-contact signal in the group, and company groups (section 2). They only remove rows, so every row in a view still meets 6.2's rule.
2. **`channel` can be blank** (a brand with no named person), outside 6.2's four values. E's fallback treats blank as "skip".
3. **`startup_cpg_member` is `unknown`, not N, on offices.** An office could be a CPG company, and no source was checked.
4. **The table of record is the Google Sheet made from `clay-icp-tables.xlsx`, permanently, not the Clay tables.** CONTRACTS says status lives in the Clay tables. Here it lives in the Sheet only, and Clay is used for research and email lookups with no status column (review round 1, R1-02: a Clay export pasted over the Sheet had brought an opted-out row back into the view). "Status lives in these tables and nowhere else" still holds: there is one store.
5. **Clay Free holds 200 rows per table**, so Clay gets 175 passed rows per table (every ready row first) for research and email lookups. Every row stays in the Sheet.
6. **The daily views are spreadsheet formulas** (INDEX/MATCH on slot helpers), not Clay views. The founder saves the daily download as `clay-icp-tables/live/daily-view-*.csv` for E's draft maker.
7. **The health-claim gate is brand-level and reads the brand's own selling copy** (homepage, product catalog, About, FAQ, ingredient pages). Implied wording goes to a blocking founder review rather than failing. Whether a claim on some products should fail a whole brand is open question 2 below.

## 5. Open decisions for the founder (each with the default A applies)

1. **Which Google and Clay accounts should the tables be shared with?** Default: the founder's own business Google account (upload the workbook as a Google Sheet) and a new Clay Free workspace under the same address. Nothing is shared with anyone else.
2. **Health claims on some products: fail the whole brand, or offer only its claim-free products?** Default: the whole brand fails (43 brands), as for Spring & Mulberry. Product-level gating would add an `eligible_skus` column and re-admit some of them.
3. **The 107-brand review backlog.** Default: clear the top 30 on the first Friday (Founder review tab). The other brands stay out of the views until cleared.
4. **Email waterfall spend.** Default: $0, with Clay Free and Hunter Free over two months. One month of Hunter Starter ($49, or $34 a month billed yearly) needs your written yes.
5. **New York share bounds for company-wide headcounts** (50% to 100% with a New York HQ, 5% to 100% otherwise) and the 125 to 250 square feet per person behind the space check. Default: keep them until intake replaces the estimates. They move about a dozen rows across the 30 and 250 lines.
