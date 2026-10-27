# Review round 2: builder's fix notes

Started and finished 2026-10-24. Source: `_review/round-2.md` (1 blocker, 2 major, 18 minor; ids R2-01 to R2-21). Per-finding outcome: the "Builder response" section appended to that file.

## What changed, by file (short)
- `messages/_render/fill.py`: `agreement_wait()` drives `[FORMATION LINE]` and the new `[HOLDING LINE]` (a date only once five offices have signed and approved the brand); `[AGREEMENT DATE]` always computed from the send date; `[FOLLOW-UP WEEK]` moves with the send date; lint fails past dates, a non-computed agreement date, a holding note once every gate is met; last proposal Mon 2026-11-30, last verbal yes Thu 2026-12-03; self-tests (384 gate combinations; side shares); `side_cap()` (offices ceil, brands floor); fresh-why_now note in drafts; attachments wait for `name_decided` (or `onepagers_name_free`); conversion drafts accept post-call statuses; `email-update` channel for 10 step 8.
- Copy: 11 steps 1 and 5; 06 touch 2 and the offer lines (250 placed, 275 shipped); 09 J2; 05 and 07 office discovery give-back with the promise rule; 10 step 8 (G's email); 08 walk-ins hand out cards; 02 second attorney question; 01 name rule; slot table and slot state; 03 why_now note.
- Calls: brand check 4 and 5; "asking about fifteen"; card "two shelf photos", withdrawal lines, $1M check; `check_guides.py` checks them.
- Tracker: standing rule for yeses (offices and brands, per cut-off), withdrawn rows, INCOMPLETE status and default, opt-out minimum 3, number-as-text and time-of-day data checks, cut-offs read dates by their day, print titles; SAMPLE data: O-004 withdraws on 11-12, five signed offices, five approvals; pipeline export drops a withdrawn office's yes; scorecard PNGs stamped SAMPLE.
- Sending: Cloudflare DNS rule with S18; domain is a spend (price not checked); opt-out rule; side shares.
- Docs: README (day one box, hour scaling, two spends, Clay credits, question 4, state, checks), HANDOFF (requests to D, G step 8, second attorney question, H section 2.3, departure 20), tracker guide, handoff guide, HOW-TO-RUN.

## Test results (final run, 2026-10-24)
- `fill.py lint`: 68 messages, 0 errors, 11 warnings; self-tests pass (384 combinations; 35 schedule days).
- `fill.py examples` + `shoot.js`: 20 pages, no page wider than 390 px; looked at brand conversion (full and fallbacks, including both step 5 variants), brand selling fallbacks, office discovery full, office conversion full.
- `test_tracker.py`: 315 checks, 0 failing (four scenarios). `test_h_compat.py`: pass. `check_guides.py`: 0 failing. `build_warmup.py`: both starts pass. `check_folder.py`: 532 checks, 0 failing.
- Reviewer's `r2_gate0_test.py` rerun: `reviewer-r2-gate0-rerun.txt`. Draft maker on A's rows (simulated addresses, scratch): `drafts-test.txt`.
- Scorecard PDF: banner on both pages; four PNGs stamped and looked at. Call cards rebuilt and looked at.
