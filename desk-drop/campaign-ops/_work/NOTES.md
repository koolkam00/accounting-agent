# Workstream F working notes (kept)

Started 2026-10-24. Inputs read: prompts/F-operations-measurement.md, plan.md, CONTRACTS.md,
desk-drop-identity/{README,HANDOFF}.md + templates/{report,tent-card,case-label}/FIELDS.md,
desk-drop-legal-pack/{HANDOFF,README,03,07,10,11,13}, financial-model/HANDOFF.md (+handoff-templates),
website/HANDOFF.md, website/SETUP.md (stack: Cloudflare Pages, GoatCounter, Apps Script intake sheet).

## Decisions so far
- D renderer works here: node desk-drop-identity/render/render.js report <json> <pdf> --json (2.4 s).
- H layout wins: campaign_actuals 26 cols exact (23 CONTRACTS + deposit_usd, deposit_paid_date,
  survey_responses_min_office); drop_costs 9; hours_log 6. Exactly these, nothing else.
- placed_within_1bd counted from the drop day T (placement date <= T+1 business day), matching D's
  template check, H's Gate 2 and G's refund rule (brand agreement s.8). Stricter for direct-ship.
- Survey: Google Forms, one form per campaign copied from a master; office via pre-filled field.
- Newsletter emails: separate per-campaign sign-up form, never in the survey responses or tracker.

## Research log (source, date opened)
