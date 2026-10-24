# Part B working notes (tracking, guides, sending, handoff)

Started 2026-10-24. Part B owns these paths (Part A writes message copy elsewhere in the folder):
- tracking/  (workbook xlsx + CSV exports, clay tracking column spec)
- calls/     (office and brand call guides, post-call note template)
- sending/   (DNS, warm-up, week-one plan, tool choice, under-20% playbook)
- handoff/   (signed_offices.csv, paid_brands.csv, filling guide)
- exports/   (pipeline_log.csv)
- tools/     (build script, export helper)
- _work/partB/ (scratch, sources, test logs)

## Key decisions so far
- Clay = only status store. Workbook = conversation/notes log keyed by row_id. One owner per column.
- pipeline_log: H's 9 columns exactly, in date order. opt_out = signed office/paid brand leaving the roster only
  (H computes active offices = signed - office opt_outs, so outreach opt-outs must NOT be exported).
- brand budget_probe before $1,500: notes blank; after: notes = after_1500 exactly (H).
- office yes_in_principle exported only when pantry owner named AND receiving window named (H + plan Gate 0).
- budget probe ranges: low end goes to value_number (conservative); "no budget" = 0; "don't know"/declined = blank.

## Changelog (one line per round)
- Round 1 (2026-10-24): built tools/build_tracker.py (tracker + scorecard + sync + pipeline export) and tools/test_tracker.py; 189 checks vs independent pandas computation; fixed Clay-side message order (paid/signed without handoff row now named first).
- Round 2 (2026-10-24): added the seven qualification checks to Brand_Log, a Gate 1 block, the derived counts for Part A's slot table, a duplicate-handoff check; SAMPLE data now obeys the calendar (no touches before Mon 2026-10-26, no weekend or holiday dates, no week-1 email); 214 checks pass.
- Round 3 (2026-10-24): critique as office manager, CPG founder, deliverability specialist and ops lead: Q6 framing line, honest price-question opening, domain-age risk and small-number bounce rule, Note_Office/Note_Brand entry tabs, warm-conversation and shortlist counts, two-page call cards, tools/check_guides.py (plan questions verbatim, banned words, weekday/date checks), wtp_conversion_note renamed wtp_unit_note; 229 tracker checks pass.
- Round 4 (2026-10-24): four coded fields + 'Numbers for the Startup CPG posts' block (Part A's messages/12 slots) with per-person quote permission; tools/test_h_compat.py pastes the export into a scratch copy of H's model: H's header, text and event checks pass and H's Gate 0/Gate 1 counts and medians equal the tracker's; 241 tracker checks pass.
- Round 5 (2026-10-24): read campaign-ops/tools/trackerdef.py; added F's 10 requested handoff columns; test_tracker checks F's full column list (245 checks); handoff column tables regenerate in place (tools/build_handoff_tables.py).
