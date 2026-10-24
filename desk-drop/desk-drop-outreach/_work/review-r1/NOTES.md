# Review round 1: builder's fix notes

Started and finished 2026-10-24. Source: `_review/round-1.md` (1 blocker, 5 major, 19 minor; ids R1-01 to R1-25). Per-finding outcome: the "Builder response" section appended to that file.

## What changed, by file

- `sending/sending-setup.md` v1.2, `sending/warmup-schedule.csv`, `sending/dns-records.csv`, `tools/build_warmup.py`: no cold email before Mon 2026-11-09, four conditions, late start Mon 2026-11-16; warm mail from [DOMAIN] from Thu 2026-10-29 (`warm_email_from_domain_target`), `domain_age_days`; week-2 plan; 32-day newly-registered-domain risk (S17, added to `_work/partB/sources.md`); name-neutral domain; reply-rate section on conversation replies and opt-outs; three-touch rule with the month-three exception.
- `messages/04-slot-state.csv`: `domain_ready` definition; new count `warm_threads_from_domain`.
- `messages/_render/fill.py`: signature by `name_decided`; offer wording (founding note and case study, "the drop planned for", paid before you ship and freight in the short offer); `[ROSTER LINE]` with `{CLUSTER_SHORT}`; seven intake questions; gates (brand agreement and invoice need `offices_signed >= 5` and `office_approvals_complete = Y`; agreements need `name_decided = Y`); checks (no cold touch 1 before Mon 2026-11-09; working name before `name_decided`; "from/your [DROP DATE" while not confirmed); broker-block slots filled; LLC name from brand.json, missing brand.json is an error; draft maker refuses no-send days and pre-11-09 cold, caps at the warm-up schedule, rebuilds touch 1 subjects, skips `hold_before_outreach` and `opt_out_date` rows.
- Messages 01, 02, 03, 04, 05 to 12 and `04-slot-table.csv`: copy fixes per finding (see the builder response).
- Tracker: `tools/build_tracker.py` (conversation-reply rate drives the 20% check; opt-out rate and 5% flag; variant table counts conversation replies), `tools/test_tracker.py` (opt-out-heavy test; header-only and SAMPLE- file checks), `tools/sample_data.py` (no email channel before Mon 2026-11-09; recontact date Tue 2027-01-19, not MLK Day).
- Handoff: live `handoff/signed_offices.csv`, `handoff/paid_brands.csv`, `exports/pipeline_log.csv` header-only; SAMPLE rows in `SAMPLE-` files (`tools/export_csv.py`, `tools/test_h_compat.py`).
- Calls: founding term and "who are you with?" answers; call card close; `tools/check_guides.py` checks them.
- `tools/render_scorecard.py`: 150 dpi, half pages. `tools/check_folder.py`: `_review/` and `REPORT.md` excluded; new slot markers.

## Test results (final run, 2026-10-24)

- `fill.py lint`: 67 messages, 0 errors, 11 warnings (9 all-fallback rows, facilities note 187 and 188 words).
- `fill.py examples` + `shoot.js`: 20 pages, 0 error findings, none wider than 390 px; looked at brand selling (full), brand conversion (full), office conversion (full and fallbacks), office discovery drafts.
- `tools/test_tracker.py`: 276 checks, 0 failing. `tools/test_h_compat.py`: pass (and the live export is header-only).
- `tools/check_guides.py`: 0 failing. `tools/build_warmup.py`: both starts pass. `tools/check_folder.py`: 468 checks, 0 failing.
- Reviewer's `_review/r1_gate0_edge_test.py` rerun on the new blank workbook (scratch): same values as in the review, including the one row the reviewer flagged as their own arithmetic (office conversations [1, 6, 8, 9]).
- Draft maker on A's real top office rows, simulated addresses, scratch only: `drafts-test.txt` in this folder.
