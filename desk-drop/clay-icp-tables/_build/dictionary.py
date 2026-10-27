"""The column dictionary: one entry per column of offices.csv and brands.csv.

Each entry: (column, tables, group, edited_by, values, meaning).
  tables     'both', 'offices' or 'brands'
  group      where the column sits (stable, daily view, control, contact, gate and score, research, E, helper)
  edited_by  who changes it: 'build' (rebuilt from sources; do not hand-edit), 'founder', 'E / founder'
             (written during outreach), 'formula' (computed in the workbook and in Clay; never typed)
Columns that come from workstream B's files take B's own definition (cluster-1-flatiron/_build/coldefs.py,
read-only) unless an entry here says more. dictionary_rows() returns the full list; the build fails if a
table column has no entry.
"""
import os
import sys

sys.dont_write_bytecode = True
_B = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                  "cluster-1-flatiron", "_build")
sys.path.insert(0, _B)
try:
    import coldefs as _bdefs  # noqa: E402
    BDEF = {}
    for _n in ("COMMON", "COMPANIES", "COWORKING", "BUILDINGS"):
        BDEF.update({k: v for k, v in getattr(_bdefs, _n).items() if k not in BDEF})
except Exception:  # B's file is a nicety, not a dependency
    BDEF = {}

STATUS = ("new, queued, contacted, replied, call_booked, call_done, yes_in_principle, materials_sent, "
          "signed (office) or paid (brand); side states not_now, no, wrong_person, do_not_contact")

S, DV, CT, CO, GS, RO, RB, E, H = ("stable (CONTRACTS 6.2)", "daily view", "contact", "control",
                                   "gate and score", "office research", "brand research",
                                   "outreach tracking (E)", "view helper")

D = [
    # ---------------------------------------------------------------- stable personalization and tracking
    ("row_id", "both", S, "build", "AO-C-### (B's company), AO-W-### (B's coworking site), AB-### (brand)",
     "Stable row key. Never reused. Use it as org_id in E's pipeline log."),
    ("company", "both", S, "build", "text", "Company name (offices) or brand name (brands), as the source gives it."),
    ("first_name", "both", S, "formula", "text or blank",
     "First name of the contact the views show (formula: primary_first_name, or backup_first_name once "
     "promote_backup = Y). Filled only when an opened page shows the name; a snippet-only name stays in "
     "contact_name_as_found."),
    ("last_name", "both", S, "formula", "text, 'unknown' or blank",
     "Surname as the page spells it; 'unknown' when only a first name is public. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("title", "both", S, "formula", "text or blank", "Job title as the opened page gives it. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_linkedin_url", "both", S, "formula", "URL or blank",
     "LinkedIn profile of the contact shown: primary_linkedin_url, or backup_linkedin_url once promote_backup = Y. "
     "Agents never open LinkedIn; a URL found on another page is marked in linkedin_status and the founder "
     "confirms it in the Friday prep."),
    ("work_email", "both", S, "formula", "business address or blank",
     "Work email of the contact shown, read from the Enrichment tab by row_id (primary or backup). Blank on every "
     "row today: no waterfall has run. Never guessed from a name pattern."),
    ("email_status", "both", S, "formula", "verified, unverified, none",
     "From the Enrichment tab: verified (the validator returned deliverable), unverified (found but catch-all or "
     "unknown, or any other word), none (no email). E emails only verified rows."),
    ("channel", "both", S, "formula", "email, linkedin, warm-intro, walk-in, or blank",
     "warm-intro when known_to_founder = Y; else email once email_status = verified; else linkedin when a contact "
     "is named; else channel_base (walk-in for a top-50 office with nobody named, linkedin for other offices, "
     "blank for a brand with nobody named, which E skips)."),
    ("score", "both", S, "formula", "0 to 100",
     "Fit score; 0 for a row that failed a hard gate. The sum of the score_ parts (see the Scoring tab). In the "
     "workbook it recomputes when known_to_founder or title_match changes."),
    ("score_reason", "both", S, "formula", "one sentence",
     "The score in one plain sentence: score_reason_core, the contact clause of the contact shown, and 'known to "
     "the founder' when known_to_founder = Y. Follows promote_backup and known_to_founder."),
    ("onsite_band", "both", S, "build", "40-75, 76-150, 151-250, 251-500, under-40, over-500, unknown (offices); blank "
     "(brands)", "Offices: the CONTRACTS band holding the central Tuesday onsite estimate. An estimate until intake "
     "replaces it. Never printed in copy."),
    ("nearest_stocked_retailer", "both", S, "build", "'Store, street' or 'none found within ten blocks' (brands); "
     "blank (offices)", "Brands: the best graded store within ten blocks of the cluster: store_selector before "
     "brand_claim, then fewest blocks out; else the nearest unverified store."),
    ("nearest_retailer_grade", "both", S, "build", "seen_on_shelf, store_selector, brand_claim, unverified",
     "Evidence grade of nearest_stocked_retailer (CONTRACTS section 4). seen_on_shelf is the founder's only; no "
     "agent sets it."),
    ("why_now", "both", S, "build", "text or blank",
     "A dated reason to write now: brands, news or a new listing in the last 12 months; offices, a lease reported "
     "since 2025-11 in an article about the company."),
    ("why_now_url", "both", S, "build", "URL or blank", "Source of why_now. E writes a hook only after opening it."),
    ("why_now_date", "both", S, "build", "YYYY-MM-DD or YYYY-MM", "Date of the why_now source."),
    ("known_to_founder", "both", S, "founder", "Y, N",
     "Y when the founder knows this person. Adds 15 points (offices) or 10 (brands) and makes the channel "
     "warm-intro. N everywhere until the founder marks rows."),
    ("startup_cpg_member", "both", S, "build", "Y, N, unknown",
     "Brands: Y where a public Startup CPG page shows the brand (participation, not proven membership). Never a "
     "hook and no points. Offices: unknown."),
    ("do_not_contact", "both", S, "E / founder", "Y, N",
     "Y the same day anyone opts out, in any words, on any channel. Never reversed. A Y row, and every row in its "
     "company_group, never enters a daily view."),
    ("status", "both", S, "E / founder", STATUS,
     "Outreach status. Lives in these tables and nowhere else. queued means it is in today's daily view and "
     "picked for sending."),
    ("source_url", "both", S, "build", "URL", "Main source for the row: the address source (offices) or the brand's "
     "research source (brands)."),
    ("found_date", "both", S, "build", "YYYY-MM-DD", "Date the row was first found."),
    # ---------------------------------------------------------------- daily view block
    ("side", "both", DV, "build", "office, brand", "Which table the row is from (E asked for it in merged views)."),
    ("daily_view_rank", "both", DV, "formula", "1, 2, ... or blank",
     "Position among rows that can go out today: eligible, best in its company_group, by score (ties by row "
     "order). Ranks 1 to 10 form the daily view."),
    ("rank", "both", DV, "build", "1 to n, blank when gated out", "Rank by score among rows that passed the gates, "
     "as built today."),
    ("top50", "offices", DV, "build", "Y, N", "Y for the 50 best-scored offices that passed the gates: the rows "
     "whose contacts were researched and that get the email waterfall."),
    ("top60", "brands", DV, "build", "Y, N", "Y for the 60 best-scored brands that passed the gates: the rows whose "
     "contacts were researched and that get the email waterfall."),
    ("check_before_send", "both", DV, "formula", "text",
     "The checks left for the morning, for the contact shown: confirm or find the LinkedIn profile, confirm an "
     "old record, a New York base or an adjacent title; brands: use the store line only if this week's Friday "
     "check confirmed it. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_role", "both", DV, "formula", "text",
     "Why this person: pantry or office lead (offices); founder, CEO or owner (not shown as a founder), "
     "marketing lead, or co-founder or executive (brands). Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_status", "both", DV, "formula", "verified-page, crowd-listed, first-name-only, unverified, none",
     "verified-page: the employer's own page or dated press, event or podcast page shows the full name. "
     "crowd-listed: the only page is a crowd-edited directory (The Org, which prints 'Unverified' beside the "
     "person); ready, but confirm on LinkedIn before sending, and ranked below employer-page names at equal "
     "score. first-name-only: an opened page shows the first name. unverified: a search snippet only (name not "
     "in first_name). none: nobody found. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_evidence", "both", DV, "formula",
     "employer's own site, The Org (crowd-edited org chart), The Org and the employer's own page, press, event or "
     "podcast page, LinkedIn (not opened), search snippet only (not opened)",
     "What kind of page supports the name, so the founder can weigh it. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_source_url", "both", DV, "formula", "URL or blank", "The opened page that supports the name and "
     "title. Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("contact_source_date", "both", DV, "formula", "YYYY-MM-DD", "Date that page was opened (or the row's found "
     "date for brands whose contact dates from stage 1). Computed: the primary_ value, or the backup_ value once promote_backup = Y."),
    ("title_match", "offices", DV, "formula", "exact, adjacent, none",
     "exact: one of the five target titles or its direct form (office manager or coordinator, office services, "
     "workplace, facilities, people operations, EA to the CEO), on an opened page, placed in New York: 10 points. "
     "adjacent: any other named person, a target title with no New York base shown, or a snippet-only name: 5. "
     "none: 0. Computed from primary_title_match or backup_title_match (promote_backup); the score follows."),
    ("street_address", "offices", DV, "build", "text", BDEF.get("street_address", "Business street address.")),
    ("floor", "offices", DV, "build", "text or unknown", BDEF.get("floor", "Floor or suite.")),
    ("lease_status", "offices", DV, "build", "occupied, occupancy-unconfirmed, signed-not-occupied, moving-out "
     "(companies); open, open-unverified, unverified, possibly-closed (coworking sites)",
     BDEF.get("lease_status", "") + " Coworking rows carry the site's status."),
    ("onsite_low", "offices", DV, "build", "number or unknown", "Low end of the Tuesday onsite estimate (see "
     "onsite_basis). An estimate until intake replaces it."),
    ("onsite_high", "offices", DV, "build", "number or unknown", "High end of the Tuesday onsite estimate."),
    ("onsite_confidence", "offices", DV, "build", "medium, low, none",
     "medium: the count is for the New York office. low: a company-wide count with an assumed New York share. "
     "none: no count."),
    ("attendance_signal", "offices", DV, "build",
     "in-office-5, hybrid-4, hybrid-3, hybrid-unspecified, hybrid-2-or-less, remote, unknown",
     "Attendance read from the employer's own words (Built In policy text, B's notes). The policy sentence beats "
     "the 'typical time on-site' box; a range uses its lower figure."),
    ("company_group", "both", DV, "build", "the row_id, or grp-...",
     "Rows that share a named parent, an operator, a company name or a named person form one group. The daily view "
     "takes one row per group and skips a group with anyone in flight or opted out."),
    ("hold_before_outreach", "both", DV, "founder", "Y, N",
     "Y keeps the row out of outreach (B: lease signed but move not confirmed, an address conflict, a tenant still "
     "in coworking, a site possibly closed). The founder sets N after the lobby check. Brands: always N today."),
    ("hold_reason", "both", DV, "build", "text", "Why the row is held, and what clears it."),
    ("opt_out_date", "both", DV, "E / founder", "YYYY-MM-DD or blank",
     "E's column (CONTRACTS 6.2): the day someone opted out. Filled means never contacted again, whatever "
     "do_not_contact says."),
    ("product_example", "brands", DV, "build", "text", "A shelf-stable SKU the research found (E's {product} source)."),
    ("category", "brands", DV, "build", "a CONTRACTS section 4 category key", "Brand category."),
    ("hq_city", "both", DV, "build", "text",
     "Brands: HQ city as researched, with any evidence note. Offices: B's HQ city."),
    ("online_store_url", "brands", DV, "build", "URL or blank", "The brand's own online store (buy path for a "
     "discount code)."),
    ("online_store_note", "brands", RB, "build", "text or blank", "What the online store check found when it is "
     "not a plain store (for example 'Shop buttons route to Amazon')."),
    ("founder_review", "brands", DV, "build", "Y, N",
     "Y when there is something for the founder to read (founder_review_reason). review_blocking says whether it "
     "must be cleared before outreach. Not a gate."),
    ("founder_review_reason", "brands", DV, "build", "text", "The researcher's reason, the claims review and build "
     "notes (shelf life not stated, single-serve pack not shown, no online store)."),
    # ---------------------------------------------------------------- control
    ("ready_for_outreach", "both", CO, "formula", "Y, N",
     "Y when the row passed the gates, is not on hold, has a contact named on an opened page, and (offices) its "
     "Tuesday band is 40 to 250 or founder_ok_to_queue = Y, (brands) no blocking founder review is pending. Only "
     "Y rows can enter a daily view."),
    ("ready_reason", "both", CO, "formula", "text", "Why a row is not ready, in words."),
    ("founder_ok_to_queue", "offices", CO, "founder", "Y or blank",
     "Y lets an office whose Tuesday band is under-40, 251-500 or over-500 into the daily view (the prompt makes "
     "30 to 39 the founder's call)."),
    ("promote_backup", "both", CO, "founder", "Y or blank",
     "Y after a wrong_person reply: the backup becomes the contact everywhere (name, title, LinkedIn URL, email, "
     "title_match, score, channel, score_reason, check_before_send). Then set status = new. One cell instead of "
     "copying thirteen."),
    ("review_blocking", "brands", CO, "build", "Y, N",
     "Y when founder_review_type includes a type that needs a decision before outreach (owner, scale, heritage, "
     "dormant, perishable risk, alcohol-adjacent, pack format, functional-ingredient or implied-effect wording). "
     "The row waits on the Founder review tab until founder_review_cleared = Y."),
    ("founder_review_cleared", "brands", CO, "founder", "Y or blank",
     "Y once you have read founder_review_reason and want the brand contacted (Friday batch). Set status = no "
     "instead to drop it."),
    ("retailer_checked_date", "brands", CO, "founder", "YYYY-MM-DD or blank",
     "The Friday date you re-checked the store listing with retailer_check_url. Use the retailer line in copy only "
     "when it is this week."),
    ("retailer_check_url", "brands", CO, "build", "URL or blank",
     "One click: the retailer's own store-scoped catalog answer for nearest_stocked_retailer (Whole Foods' search "
     "for that store; no store picker)."),
    ("onsite_founder_call", "offices", CO, "build", "Y, N",
     "Y when the central Tuesday estimate is outside 40 to 250: the row needs founder_ok_to_queue = Y."),
    # ---------------------------------------------------------------- gates and score
    ("gate_result", "both", GS, "build", "pass, fail", "Whether the row passed every hard gate (applied before any "
     "enrichment spend)."),
    ("gate_reason", "both", GS, "build", "text", "Every gate the row failed, or 'passes all hard gates'."),
    ("gate_failed", "brands", GS, "build", "excluded-category, health-claim, not-shelf-stable, no-buy-path",
     "Machine-readable list of failed brand gates."),
    ("score_raw", "both", GS, "build", "number", "What the row would score if it had passed (gated rows keep it for "
     "review)."),
    ("score_onsite", "offices", GS, "build", "0 to 30", "25 x the share of the Tuesday range inside 40 to 250 (ratio "
     "scale), plus 5 when the count is for the New York office; 7 when headcount is unknown."),
    ("score_size", "offices", GS, "build", "-4 to 15", "Company size: 500 or fewer 15; 501-1,000 6; 1,001-4,999 2; "
     "5,000+ 0; unknown 8; minus 4 when a controlling parent is named."),
    ("score_attendance", "offices", GS, "build", "-5 to 15", "On-site 5 days 15; hybrid 4 days 12; 3 days 10; days not "
     "stated 7; 2 or fewer 5; no signal 6; remote -5; plus 3 when the policy names Tuesday (cap 15)."),
    ("score_address", "offices", GS, "build", "0 to 15", "Occupied 10, occupancy-unconfirmed 5, signed-not-occupied 2 "
     "(coworking site: open 10, open-unverified 5, unverified 2); 0 with an address conflict; plus confidence "
     "high 5, medium 3, low 0."),
    ("score_title", "offices", GS, "formula", "0, 5, 10", "From title_match: exact 10, adjacent 5, none 0."),
    ("score_known", "both", GS, "formula", "0, 15 (offices) or 0, 10 (brands)", "From known_to_founder."),
    ("score_buy", "brands", GS, "build", "0 to 25", "Best graded store within ten blocks: store page inside the "
     "cluster 25, store page within ten blocks 20, brand locator inside 17, brand locator within ten 13; online "
     "store only 6; none 0."),
    ("score_ny", "brands", GS, "build", "0 to 20", "HQ New York City 20, rest of New York State 13, Northeast 8, "
     "elsewhere 3, unknown 4; minus 3 when a New York HQ is unverified."),
    ("score_why", "brands", GS, "build", "0 to 15", "Press in the last 180 days 15, 181 to 365 days 8; own listing in "
     "180 days 8, 181 to 365 days 4; none or unverified 0."),
    ("score_rev", "brands", GS, "build", "0 to 10", "Revenue $500k to $10M 10; unknown 5; under $500k 2; over $10M 0."),
    ("score_fit", "brands", GS, "build", "0 to 10", "Shelf-stable Y 4, likely 2, unknown 1; individually packaged Y "
     "3, unknown 1; online store Y 3, unknown 1."),
    ("score_contact", "brands", GS, "build", "0 to 10", "Founder named on an opened page 6 (first name only or "
     "snippet 3); marketing lead named on an opened page 4 (snippet 2)."),
    ("score_review", "brands", GS, "build", "-35 to 0", "The most severe founder-review type: sourced revenue over "
     "$10M -35; large-company owner -25; scale signals -12; dormant -12; heritage -10; perishable risk -8; under "
     "$500k -5; alcohol-adjacent -5; functional-ingredient wording -4; nutrient wording -4; pack format -4; other "
     "-2; single-serve pack not shown 0."),
    ("founder_review_type", "brands", GS, "build", "owner, scale-reported, scale, dormant, not-emerging, "
     "perishable-risk, under-floor, alcohol-adjacent, format, format-unconfirmed, claim-functional, nutrient-claim, "
     "other", "The founder-review reason sorted into types; the most severe sets score_review; review_blocking "
     "follows the blocking types."),
    ("size_class", "offices", GS, "build", "le500, 501-1000, 1001-4999, 5000+, unknown",
     "Company-wide size class used by score_size."),
    ("onsite_central", "offices", GS, "build", "number or unknown", "Middle of the Tuesday range on a ratio scale "
     "(square root of low x high)."),
    ("onsite_flags", "offices", GS, "build", "text", "may be under 30, may exceed 250, 30 to 39 is the founder's call, "
     "central estimate under 30; under-30 and over-250 mean the row failed the gate."),
    ("onsite_space_check", "offices", GS, "build", "Y, N",
     "Y when the row's leased square footage changed the estimate (review round 1): high at most sf / 125, "
     "central at most sf / 150, or a space-based range (sf / 250 to sf / 125) where the headcount math cannot fit "
     "or the HQ is outside New York."),
    ("onsite_basis", "offices", GS, "build", "text", "The Tuesday estimate's arithmetic in words: count x New York "
     "share x in-office rate, then the space check against the row's own leased square footage."),
    ("onsite_label", "offices", GS, "build", "text", "Always 'estimate until intake replaces it'."),
    ("onsite_fit_share", "offices", GS, "build", "0 to 1 or unknown", "Share of the Tuesday range inside 40 to 250 "
     "(ratio scale); the first tie-break."),
    # ---------------------------------------------------------------- contacts (primary extras and backup)
    ("contact_name_as_found", "both", CT, "build", "text", "The primary contact's name as found, even when it is not "
     "verified enough for first_name."),
    ("contact_record_date", "both", CT, "build", "YYYY-MM-DD, YYYY or blank",
     "The source's own date for the contact (The Org 'updated' date, article date). Older than 12 months adds a "
     "check to check_before_send."),
    ("contact_note", "both", CT, "build", "text", "What the page said, where it was found and any doubt."),
    ("contact_ny_base", "offices", CT, "build", "confirmed, likely, unconfirmed",
     "Whether the contact works from the New York office: confirmed (the employer's page or The Org's office "
     "record), likely (New York area or a New York firm's page with no city), unconfirmed."),
    ("linkedin_status", "both", CT, "build", "text", "Where the primary's LinkedIn URL came from (The Org, the "
     "employer's page, a search result). LinkedIn itself was never opened."),
    ("contacts_researched", "both", CT, "build", "Y, N (offices); stage 2, stage 3, review round 1, stage 1 only "
     "(brands)", "Whether contact research beyond the first pass covered this row."),
    ("primary_first_name", "both", CT, "build", "text or blank", "Researched primary contact's first name (opened page only)."),
    ("primary_last_name", "both", CT, "build", "text, unknown or blank", "Researched primary contact's surname."),
    ("primary_title", "both", CT, "build", "text or blank", "Researched primary contact's title."),
    ("primary_linkedin_url", "both", CT, "founder", "URL or blank",
     "Primary contact's LinkedIn profile. Prefilled only when another opened page lists it (linkedin_status says "
     "which); the founder pastes or confirms it in the Friday prep."),
    ("primary_work_email", "both", CT, "formula", "address or blank", "work_email for row_id on the Enrichment tab."),
    ("primary_email_status", "both", CT, "formula", "verified, unverified, none", "email_status for row_id on the "
     "Enrichment tab (none when there is no address)."),
    ("primary_contact_role", "both", CT, "build", "text", "Why the researched primary was chosen."),
    ("primary_contact_status", "both", CT, "build", "verified-page, crowd-listed, first-name-only, unverified, none",
     "As contact_status, for the researched primary."),
    ("primary_contact_evidence", "both", CT, "build", "as contact_evidence", "What kind of page supports the primary."),
    ("primary_contact_source_url", "both", CT, "build", "URL or blank", "The page that supports the primary."),
    ("primary_contact_source_date", "both", CT, "build", "YYYY-MM-DD", "Date that page was opened."),
    ("primary_title_match", "offices", CT, "build", "exact, adjacent, none", "title_match for the primary."),
    ("primary_check_before_send", "both", CT, "build", "text", "check_before_send when the primary is shown."),
    ("primary_reason_who", "both", CT, "build", "text", "The contact clause of score_reason for the primary."),
    ("backup_contact_source_date", "both", CT, "build", "YYYY-MM-DD or blank", "Date the backup's page was opened."),
    ("backup_title_match", "offices", CT, "build", "exact, adjacent, none", "title_match for the backup."),
    ("backup_check_before_send", "both", CT, "build", "text", "check_before_send when the backup is shown."),
    ("backup_reason_who", "both", CT, "build", "text", "The contact clause of score_reason for the backup."),
    ("backup_contact_ny_base", "offices", CT, "build", "confirmed, likely, unconfirmed or blank",
     "As contact_ny_base, for the backup."),
    ("score_reason_core", "both", CT, "build", "text", "score_reason without its contact clause (or the whole "
     "gated-out sentence)."),
    ("score_reason_tail", "brands", CT, "build", "text or blank", "The founder-review clause that follows the "
     "contact clause in score_reason."),
    ("channel_base", "both", CT, "build", "walk-in, linkedin or blank", "The channel when nobody is named and no "
     "email or known flag applies."),
    ("backup_first_name", "both", CT, "build", "text or blank", "Backup contact's first name (opened page only)."),
    ("backup_last_name", "both", CT, "build", "text, unknown or blank", "Backup contact's surname."),
    ("backup_title", "both", CT, "build", "text or blank", "Backup contact's title."),
    ("backup_linkedin_url", "both", CT, "founder", "URL or blank", "Backup contact's LinkedIn profile (as "
     "primary_linkedin_url)."),
    ("backup_work_email", "both", CT, "formula", "address or blank", "backup_work_email for row_id on the "
     "Enrichment tab."),
    ("backup_email_status", "both", CT, "formula", "verified, unverified, none", "backup_email_status for row_id on "
     "the Enrichment tab."),
    ("backup_contact_role", "both", CT, "build", "text", "Why the backup: pantry or office lead (offices); marketing "
     "lead or co-founder or executive (brands)."),
    ("backup_contact_name_as_found", "both", CT, "build", "text", "Backup's name as found."),
    ("backup_contact_status", "both", CT, "build", "verified-page, crowd-listed, first-name-only, unverified, none",
     "As contact_status, for the backup."),
    ("backup_contact_evidence", "both", CT, "build", "as contact_evidence", "What kind of page supports the backup."),
    ("backup_contact_source_url", "both", CT, "build", "URL or blank", "The page that supports the backup."),
    ("backup_contact_record_date", "both", CT, "build", "date or blank", "The backup source's own date."),
    ("backup_contact_note", "both", CT, "build", "text", "Notes on the backup."),
    ("backup_linkedin_status", "both", CT, "build", "text", "Where the backup's LinkedIn URL came from."),
    ("company_group_reason", "both", CT, "build", "text", "What the group's rows share (parent, operator, name or "
     "person)."),
    # ---------------------------------------------------------------- office research (B and A)
    ("org_type", "offices", RO, "build", "company, coworking-operator", "A company office, or a coworking site that "
     "may join as one office if the operator controls the pantry."),
    ("b_id", "offices", RO, "build", "B-C-### or B-W-###", "The row's ID in B's files."),
    ("website", "both", RO, "build", "URL or unknown", "Company or brand website (the domain the email waterfall "
     "uses)."),
    ("industry", "offices", RO, "build", "text", BDEF.get("industry", "Industry.")),
    ("employee_count", "offices", RO, "build", "number as sourced or unknown",
     "The sourced headcount the estimate starts from (B's headcount_count, else the company-wide count cited)."),
    ("employee_count_second", "offices", RO, "build", "number or blank", "B's second, independent count."),
    ("headcount_band", "offices", RO, "build", "CONTRACTS band", BDEF.get("headcount_band", "")),
    ("headcount_scope", "offices", RO, "build", "whole-company, nyc-office, unknown", BDEF.get("headcount_scope", "")),
    ("headcount_check", "offices", RO, "build", "agree, disagree, single-source, scope-differs, no-count, "
     "over-500-second-source", BDEF.get("headcount_check", "")),
    ("headcount_source_url", "offices", RO, "build", "URL", BDEF.get("headcount_source_url", "")),
    ("headcount_second_source_url", "offices", RO, "build", "URL", BDEF.get("headcount_second_source_url", "")),
    ("hq_in_nyc", "offices", RO, "build", "Y, N, unknown", BDEF.get("hq_in_nyc", "")),
    ("parent_company", "offices", RO, "build", "text or unknown",
     BDEF.get("parent_company", "") + " Stage 3 added Axon (Carbyne, Prepared 911) and DraftKings (Simplebet) "
     "with sources in a_corrections."),
    ("linkedin_company_url", "offices", RO, "build", "URL or unknown", "Company LinkedIn page, as linked from the "
     "company's own website (linkedin_company_source); unknown where the site links none. LinkedIn not opened."),
    ("linkedin_company_source", "offices", RO, "build", "text or blank", "The page that links linkedin_company_url "
     "and the date it was opened."),
    ("zip", "offices", RO, "build", "5 digits", BDEF.get("zip", "")),
    ("lat", "offices", RO, "build", "decimal degrees", BDEF.get("lat", "")),
    ("lon", "offices", RO, "build", "decimal degrees", BDEF.get("lon", "")),
    ("in_boundary", "offices", RO, "build", "Y, N", BDEF.get("in_boundary", "")),
    ("blocks_outside", "offices", RO, "build", "number", BDEF.get("blocks_outside", "")),
    ("building_id", "offices", RO, "build", "B-B-### or blank", BDEF.get("building_id", "")),
    ("building_name", "offices", RO, "build", "text or unknown", BDEF.get("building_name", "")),
    ("address_source_url", "offices", RO, "build", "URL", BDEF.get("address_source_url", "")),
    ("address_source_date", "offices", RO, "build", "date", BDEF.get("address_source_date", "")),
    ("address_source_type", "offices", RO, "build", "company-site, leasing-press, builtin, building-site, "
     "press-release, wikipedia, other, operator-site", BDEF.get("address_source_type", "")),
    ("second_source_url", "offices", RO, "build", "URL or blank", BDEF.get("second_source_url", "")),
    ("second_source_date", "offices", RO, "build", "date or blank", BDEF.get("second_source_date", "")),
    ("source_note", "offices", RO, "build", "text", "Set when a source is a sec.gov filing agents do not open (the "
     "founder may open it in a browser)."),
    ("confidence", "offices", RO, "build", "high, medium, low", BDEF.get("confidence", "")),
    ("move_in_date", "offices", RO, "build", "YYYY-MM, unknown or blank", BDEF.get("move_in_date", "")),
    ("in_coworking", "offices", RO, "build", "Y, N", BDEF.get("in_coworking", "")),
    ("coworking_id", "offices", RO, "build", "B-W-### or blank", BDEF.get("coworking_id", "")),
    ("pantry_control", "offices", RO, "build", "operator, tenant, unknown (coworking rows)", BDEF.get("pantry_control", "")),
    ("lobby_type", "offices", RO, "build", "walk-up, security desk, loading dock, unknown", BDEF.get("lobby_type", "")),
    ("lobby_source_url", "offices", RO, "build", "URL or blank", BDEF.get("lobby_source_url", "")),
    ("lobby_note", "offices", RO, "build", "text or blank", "Set when B lists a lobby type with no source: the type "
     "stays unknown until the walk."),
    ("coi_required", "offices", RO, "build", "yes, no, unknown", BDEF.get("coi_required", "")),
    ("tuesday_named_in_policy", "offices", RO, "build", "Y, N", "Y when the employer's own policy text names Tuesday "
     "as an office day."),
    ("attendance_evidence", "offices", RO, "build", "text", "The words the attendance signal rests on."),
    ("attendance_source_url", "offices", RO, "build", "URL", "Page the attendance signal comes from (Built In offices "
     "page, opened 2026-10-24, or B's source)."),
    ("attendance_source_date", "offices", RO, "build", "date", "Date that page was opened."),
    ("b_candidate_status", "offices", RO, "build", "candidate, excluded-coworking, excluded-not-office, near-miss, "
     "coworking-operator", BDEF.get("candidate_status", "")),
    ("near_miss_class", "offices", RO, "build", "text or blank", BDEF.get("near_miss_class", "")),
    ("nyc_office_may_fit", "offices", RO, "build", "Y or blank", BDEF.get("nyc_office_may_fit", "")),
    ("leased_sf_mentioned", "offices", RO, "build", "numbers", BDEF.get("leased_sf_mentioned", "")),
    ("leased_sf_source", "offices", RO, "build", "text or blank", "Where leased_sf_mentioned comes from: B's "
     "sources, or (review round 1) the row's own lease article, quoted, when B recorded none."),
    ("b_notes", "offices", RO, "build", "text", "B's research notes for the row, with sources."),
    ("a_corrections", "offices", RO, "build", "text", "Facts this workstream changed after B, each with its source "
     "and date (_work/stage3_corrections.csv)."),
    # ---------------------------------------------------------------- brand research
    ("hq_state", "brands", RB, "build", "two-letter state, country or unknown", "Brand HQ state."),
    ("hq_class", "brands", RB, "build", "nyc, nys, northeast, elsewhere, unknown, with '(unverified)'",
     "HQ class used by score_ny (New York brands come first)."),
    ("funding_stage", "brands", RB, "build", "text or unknown", "Funding stage as researched."),
    ("funding_source_url", "brands", RB, "build", "URL or blank", "Source of funding_stage."),
    ("shelf_stable", "brands", RB, "build", "Y, likely, unknown, N", "Sealed and shelf-stable; N fails the gate; "
     "likely or unknown pass with founder_review (the 60-day shelf life is asked at intake, q1)."),
    ("shelf_stable_basis", "brands", RB, "build", "text", "The page and words shelf_stable rests on."),
    ("individually_packaged", "brands", RB, "build", "Y, unknown, N", "Single-serve, individually packaged SKU."),
    ("online_store", "brands", RB, "build", "Y, N, unknown", "The brand sells online (its own store, or Amazon linked "
     "from its site)."),
    ("revenue_band", "brands", RB, "build", "under-500k, 500k-10m, over-10m, unknown",
     "Revenue band with basis, or unknown. Over $10M sets the -35 review penalty."),
    ("revenue_band_type", "brands", RB, "build", "text", "reported, company projection, press quote, and its age."),
    ("revenue_basis", "brands", RB, "build", "text", "The figure and its source, or unknown."),
    ("health_claim_flag", "brands", RB, "build", "text", "Researcher's note on claims (nutrient-content claims are "
     "allowed with founder_review; structure or function claims fail the gate)."),
    ("research_excluded", "brands", RB, "build", "Y, N", "The researcher's own exclusion call."),
    ("research_exclusion_reason", "brands", RB, "build", "text", "Why the researcher excluded it."),
    ("nearest_retailer_blocks_outside", "brands", RB, "build", "number or blank", "Street blocks from the boundary to "
     "nearest_stocked_retailer (B's grid measure); 0 is inside."),
    ("nearest_retailer_inside_cluster", "brands", RB, "build", "Y, N", "The nearest graded store is inside the line."),
    ("graded_retailer_count_within_ten", "brands", RB, "build", "number", "Stores within ten blocks graded "
     "store_selector or brand_claim."),
    ("retailers_within_ten_blocks", "brands", RB, "build", "list", "Every store within ten blocks with grade and "
     "distance."),
    ("stores_beyond_ten_or_unplaced", "brands", RB, "build", "list", "Stores further out or with no address."),
    ("retailers_claimed", "brands", RB, "build", "text", "Retailers the researcher found (any distance)."),
    ("retailer_evidence_urls", "brands", RB, "build", "URLs", "Pages behind the store links (store catalog, "
     "locator)."),
    ("why_now_type", "brands", RB, "build", "press, listing, unverified, none, stale (over 12 months)",
     "press: a third party; listing: the brand's own site or store feed; unverified earns nothing."),
    ("why_now_age_days", "brands", RB, "build", "number", "Days from why_now_date to 2026-10-24."),
    ("startup_cpg_evidence_url", "brands", RB, "build", "URL or blank", "The public Startup CPG page behind "
     "startup_cpg_member = Y."),
    ("instagram_url", "brands", RB, "build", "URL or blank", "Brand Instagram (not opened)."),
    ("research_slice", "brands", RB, "build", "BR1 to BR5", "Which research slice found the brand."),
    ("slice_row", "brands", RB, "build", "BRn:line", "The line in that slice file."),
    ("notes", "brands", RB, "build", "text", "Research notes with sources, then build notes after ' | '."),
    ("enrichment_log", "brands", RB, "build", "text", "Every field update applied to the row, with source, date and "
     "confidence."),
    # ---------------------------------------------------------------- E's columns
    ("sequence", "both", E, "E / founder", "<side>-<stage>-<variant>, e.g. office-discovery-A",
     "E: the sequence started (desk-drop-outreach/tracking/csv/clay_tracking_columns.csv)."),
    ("touch_1_date", "both", E, "E / founder", "YYYY-MM-DD", "E: day the first message with the ask was sent."),
    ("touch_2_date", "both", E, "E / founder", "YYYY-MM-DD", "E: day touch 2 was sent."),
    ("touch_3_date", "both", E, "E / founder", "YYYY-MM-DD", "E: day touch 3 was sent (last touch)."),
    ("last_reply_date", "both", E, "E / founder", "YYYY-MM-DD", "E: the latest reply."),
    ("reply_type", "both", E, "E / founder", "E's list", "E: the latest meaningful reply type."),
    ("call_date", "both", E, "E / founder", "YYYY-MM-DD", "E: the latest conversation."),
    ("call_notes", "both", E, "E / founder", "one line", "E: one line plus 'see tracker <call_date>'."),
    ("yes_in_principle", "both", E, "E / founder", "Y, N", "E: Y if any conversation said yes in principle."),
    ("next_action", "both", E, "E / founder", "E's list", "E: the next step (drives the follow-up view)."),
    ("next_action_date", "both", E, "E / founder", "YYYY-MM-DD", "E: when the next step is due."),
    ("referral_from", "both", E, "E / founder", "row_id", "E: the row that referred this person (a new row E adds)."),
    ("street_short", "offices", E, "E / founder", "text", "E: the street name with no number, for {area}."),
    ("why_now_hook", "both", E, "E / founder", "one sentence", "E: the hook written after opening why_now_url."),
    ("product_short", "brands", E, "E / founder", "two to four words", "E: the product's own name for {product}."),
    ("call_note_hook", "both", E, "E / founder", "twelve words or fewer", "E: what they said on the call."),
    ("how_we_know", "both", E, "E / founder", "fifteen words or fewer", "E: how the founder knows them (warm "
     "templates)."),
    ("referrer_ok_to_name", "both", E, "E / founder", "Y, N", "E: the referrer agreed to be named."),
    ("office_approvals_complete", "brands", E, "E / founder", "Y, N", "E: every office on the brand's route said yes "
     "(gates the agreement and invoice)."),
    # ---------------------------------------------------------------- helpers
    ("in_flight", "both", H, "formula", "Y, N", "Y when status is queued, contacted, replied, call_booked, call_done, "
     "yes_in_principle or materials_sent."),
    ("dnc_any", "both", H, "formula", "Y, N", "Y when do_not_contact = Y, status = do_not_contact or opt_out_date "
     "is filled: any one of the three blocks the row and its group."),
    ("group_key", "both", H, "formula", "text", "company_group, or the row_id when company_group is blank (a row "
     "added by hand)."),
    ("group_blocked", "both", H, "formula", "Y, N", "Y when any row with the same group_key is in flight or has any "
     "do-not-contact signal (dnc_any)."),
    ("eligible", "both", H, "formula", "Y, N", "Y when status = new, do_not_contact = N, dnc_any = N, "
     "ready_for_outreach = Y and the group is not blocked."),
    ("view_pick", "both", H, "formula", "Y, N", "Y for the best-scored eligible row of its group (one contact per "
     "company)."),
    ("in_daily_view", "both", H, "formula", "Y, N", "Y when the row is eligible, best in its group and "
     "daily_view_rank is 1 to 10 (a pasted rank alone cannot put a row in the view)."),
    ("view_slot", "both", H, "formula", "1 to 10 or blank", "The row's line on the Daily view tab."),
    ("walk_ok", "offices", H, "formula", "Y, N", "Y for a passed, new, unblocked, unheld office whose channel is "
     "walk-in."),
    ("walk_slot", "offices", H, "formula", "1 to 25 or blank", "The row's line on the Walk list tab."),
    ("review_ok", "brands", H, "formula", "Y, N", "Y for a passed, new brand with a blocking founder review not "
     "yet cleared."),
    ("review_slot", "brands", H, "formula", "1 to 30 or blank", "The row's line on the Founder review tab."),
    ("intact", "both", H, "formula", "Y, N", "N when this row's formulas were pasted over (the views then show a "
     "warning instead of rows)."),
    ("row_order", "both", H, "formula", "number", "The row's position (the workbook uses ROW()); the last tie-break."),
]


def dictionary_rows():
    seen = set()
    out = []
    for col, tables, group, who, values, meaning in D:
        if col in seen:
            raise SystemExit(f"dictionary: duplicate entry {col}")
        seen.add(col)
        out.append(dict(column=col, tables=tables, group=group, edited_by=who, values=values,
                        meaning=meaning.strip() or "See B's HANDOFF.md."))
    return out


def check(columns, table):
    have = {r["column"]: r for r in dictionary_rows()}
    missing = [c for c in columns if c not in have]
    wrong = [c for c in columns if c in have and have[c]["tables"] not in ("both", table)]
    if missing or wrong:
        raise SystemExit(f"dictionary: {table} columns missing {missing}, table mismatch {wrong}")
    extra = [r["column"] for r in dictionary_rows() if r["tables"] in ("both", table) and r["column"] not in columns]
    return extra
