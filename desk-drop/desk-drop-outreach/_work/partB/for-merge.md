# Part B input for the merge step (README, HANDOFF)

Written 2026-10-24 by part B for the step that writes `desk-drop-outreach/README.md` and `HANDOFF.md`.
Part B wrote no README, REPORT or HANDOFF. Part B's report text is returned to the orchestrator separately.

## README rows, in the order the founder uses them

| File | What it is for | How to edit |
| --- | --- | --- |
| `sending/sending-setup.md` | Week 1 setup: SPF, DKIM, DMARC on [DOMAIN]; warm-up; week-one plan without the domain; Gmail vs sequencer with costs; what to do under 20% replies | Text. Dates are derived, founder to confirm |
| `sending/dns-records.csv` | The seven DNS records in order, with when and how to check each | Edit values only after Google changes them |
| `sending/warmup-schedule.csv` | Every weekday 2026-10-26 to 2026-12-11: cold email first touches, follow-ups due, cap, other-channel touches | Change `PLAN`/`CAP` in `tools/build_warmup.py`, rerun it (it fails on any broken cap or holiday send) |
| `tracking/conversation-tracker.xlsx` | The tracker to import into Google Sheets: notes log per conversation (keyed by Clay `row_id`), Note entry tabs, Friday scorecard (Gate 0, Gate 1, medians, top objections, reply rates, post numbers, copy-slot counts), Clay sync check, handoff tabs, pipeline export | Type in the logs, Note tabs, handoff tabs, later_events, Config; paste Clay exports on Friday. Structural changes in `tools/build_tracker.py`, then rebuild |
| `tracking/how-the-tracker-works.md` | Setup, the two-store rule (Clay is status, tracker is notes), after-call and Friday routines, how every number is counted, limits, tests | Text |
| `tracking/conversation-tracker-SAMPLE.xlsx` | Same workbook with SAMPLE rows; for learning it and for the one-time Google Sheets check | Rebuilt by `tools/build_tracker.py --sample` |
| `tracking/scorecard-SAMPLE.pdf`, `-p1.png`, `-p2.png` | The SAMPLE scorecard as LibreOffice calculates it | `tools/render_scorecard.py` |
| `tracking/csv/office_log.csv`, `brand_log.csv` | Header-only CSV of the two logs | `tools/export_csv.py` |
| `tracking/csv/clay_tracking_columns.csv` | The 13 conversation-tracking columns for both Clay tables, with rules | `CLAY_TRACKING` in `tools/build_tracker.py` |
| `tracking/csv/scorecard-SAMPLE.csv` | Every SAMPLE scorecard value, to compare with the Google Sheets copy | `tools/export_csv.py` |
| `calls/office-call-guide.md` | 20-minute office discovery call: plan's seven questions verbatim, probes, column map, Gate 0 rule, close, truthful answers, walk-in version | Text; `tools/check_guides.py` checks the plan's questions stay verbatim |
| `calls/brand-call-guide.md` | 20 to 30 minute brand call: seven questions verbatim, the anchor rule, close, truthful answers, the seven qualification checks for weeks 4 to 7 | Same |
| `calls/call-cards.pdf` | One page per side to keep in front of you on a call (questions pulled from plan.md at build time) | `tools/build_call_cards.py` |
| `calls/post-call-note-template.md` | The ten-minute note: fields in tracker column order, number rules, Clay write-back, status table, objection codes, a SAMPLE example | Text; field order checked by script against the tracker |
| `handoff/how-to-fill-handoff-files.md` | When and how to fill `signed_offices`, `paid_brands`, the pipeline export; event rules; ID rules; deviations; column reference | Text; column tables by `tools/build_handoff_tables.py` |
| `handoff/signed_offices.csv` | E to F: signed offices (CONTRACTS 6.4 + additions). Ships with one SAMPLE row | Download of the tracker's signed_offices tab |
| `handoff/paid_brands.csv` | E to F: paid brands (CONTRACTS 6.4 + additions). Ships with one SAMPLE row | Download of the tracker's paid_brands tab |
| `exports/pipeline_log.csv` | E to H: pipeline events, exactly H's nine columns, date order. Ships with 210 SAMPLE rows: replace before the first real paste | Download of the tracker's pipeline_log tab every Friday |
| `tools/` | `build_tracker.py`, `sample_data.py`, `test_tracker.py` (245 checks, LibreOffice), `test_h_compat.py` (pastes the export into a scratch copy of H's model), `export_csv.py`, `render_scorecard.py`, `build_warmup.py`, `build_call_cards.py`, `build_handoff_tables.py`, `check_guides.py` | Python 3 with openpyxl; LibreOffice for tests; node + Playwright for the cards |
| `_work/partB/` | Sources (S1 to S16), notes and changelog, test logs, the recalculated SAMPLE workbook, card renders, the coordination note to part A | Scratch, kept |

## HANDOFF facts (part B)

### Consumes
| From | File | Used for |
| --- | --- | --- |
| A, Clay tables | Both tables (not yet published on 2026-10-24); CONTRACTS 6.2 columns `row_id`, `company`, `status`, `do_not_contact`, `channel` and E's 13 tracking columns | Friday paste on Clay_Offices / Clay_Brands; found by header name; Sync tab and reply rates |
| B, cluster map | `cluster-1-flatiron/walk.csv` (walk sessions 1 to 7), `companies.csv` (`building_lobby_type`, `industry`, `building_id`), `retailers.csv`, `brand-maps/` | Week-one walk-ins; call prep; `industry` and `building_id` on signed_offices |
| D, identity | `desk-drop-identity/signature/signature-outreach.txt` (no images or links; carries `[WEBSITE]`, to be left out until the site is public), `pdf/discovery-one-pager-BLANK.pdf` | Sending rules; the one-pager offered at the end of calls |
| G, legal | `02-email-footer-and-checklist.md` (opt-out rules), `03` agreement sections 2 and 6 (approvals, naming boxes), `11` COI check | Opt-out handling; `founding_roster_named`, `public_naming_ok`, `coi_received_date`, `coi_policy_end_date`; G's suggested `agreement_version`, `newsletter_option`, `brand_privacy_url` |
| H, model | `financial-model/HANDOFF.md` section 3; `_work/build_model.py` Pipeline summary (active offices = signed minus office opt_outs) | Pipeline export layout and event rules |
| F, operations | `campaign-ops/tools/trackerdef.py` `SIGNED_OFFICES_REQUESTED`, `PAID_BRANDS_REQUESTED` (read 2026-10-24) | Ten added handoff columns |
| Part A, copy | `messages/04-slot-state.csv` keys; `messages/03-personalization-fields.csv` (`call_note_hook`, `referrer_ok_to_name`); `messages/12-startup-cpg-posts.md` slots; touch timing +3/+7 business days | Copy-slot counts block; Clay write-back; post numbers block; SAMPLE touch dates |

### Feeds
| To | File | Columns |
| --- | --- | --- |
| F | `handoff/signed_offices.csv` | 21 `office_intake` columns (6.3) in order; 6.4: `office_id`, `clay_row_id`, `agreement_signed_date`, `agreement_file`, `founding_roster_named`, `budget_probe_verbatim`, `budget_probe_date`, `budget_probe_monthly_usd`; additions: `agreement_version`, `owner_can_say_yes_alone`, `industry`, `pantry_owner_phone`, `pantry_owner_email`, `public_naming_ok`, `building_id` (36 columns) |
| F | `handoff/paid_brands.csv` | 27 `brand_intake` columns in order; 6.4's 20; additions: `payment_1_usd`, `payment_1_date`, `payment_2_usd`, `payment_2_date`, `agreement_version`, `coi_policy_end_date`, `newsletter_option`, `brand_privacy_url`, `allergen_source`, `may_contain_verbatim`, `flavor_name`, `flavor_name_2`, `allergen_source_2`, `allergen_line_verbatim_2`, `may_contain_verbatim_2`, seven `verified_q*` checks, `verified_not_excluded`, `verified_date`, `verified_notes`, `campaign_id`, `brand_legal_name`, `billing_address`, `billing_email`, `code_site` (77 columns) |
| H | `exports/pipeline_log.csv` | `date, side, org_id, org_name, event, value_number, value_text, controls_budget, notes`; org_id = Clay row_id; brand after-$1,500 rows `notes = after_1500`; verified against a scratch copy of H's model (`_work/partB/h_compat_log.txt`) |
| A | `tracking/csv/clay_tracking_columns.csv` | The 13 CONTRACTS 6.2 tracking columns with allowed values and write rules |

### Deviations from CONTRACTS (part B)
1. Pipeline `opt_out` is used only for a signed office or paid brand leaving the roster; outreach unsubscribes stay in Clay. Reason: H's active-office count subtracts every office opt_out.
2. `payment_received_date` = the payment that releases the ship date (founding full price, standard deposit); per-payment columns added.
3. `budget_probe_monthly_usd`: "no budget" recorded as 0 (a named number), "don't know" blank. Medians include the zeros and show how many there are.
4. Added columns on both handoff files (above). Nothing renamed or dropped.
5. Tracker log `yes_in_principle` takes Y, N or maybe; Clay's stays Y/N (maybe is N in Clay).
6. Fri 2026-11-27 is a no-send day in the sending calendar though it is a business day under CONTRACTS 3; follow-ups due that day go Monday.
