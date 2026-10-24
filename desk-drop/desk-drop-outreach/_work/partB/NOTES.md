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
