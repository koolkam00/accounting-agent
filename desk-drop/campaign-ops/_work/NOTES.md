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
- Short links: Bitly Free = 5 links/month, 2 QR/month, no redirect editing; Core $10/mo annual ($120) (bitly.com/pages/pricing, opened 2026-10-24).
  Short.io Free = 1,000 branded links lifetime, 50,000 tracked clicks/month, 5 custom domains, redirects unlimited (short.io/pricing, opened 2026-10-24).
  Dub.co pricing page showed no free plan; cheapest Business $90/mo (dub.co/pricing, opened 2026-10-24; page may hide a free tier: unverified).
  TinyURL pricing page did not render (unverified).
- Google Forms help (support.google.com/docs/answer/2839588, opened 2026-10-24): pre-filled link steps (More > Pre-fill form > Get link);
  "Limit to 1 response" needs sign-in; confirmation message under Settings > Presentation.
- Google Forms help (support.google.com/docs/answer/2917686, opened 2026-10-24): destination existing spreadsheet; Unlink; Delete all responses;
  delete individual responses (Responses > Individual > Delete).
- Wave pricing (waveapps.com/pricing, opened 2026-10-24): Starter free, unlimited invoices; card 2.9% + $0.60; Pro $19/mo.

## Changelog (working)
- R1 build: opscal (calendar, validator) + tests PASS; forms.json; trackerdef/formulas/build_tracker (31 tabs, ~300 formula columns);
  tracker.py independent arithmetic; zero scenario. First compare: 4 mismatches (MIN over "" -> #VALUE!, half-even rounding). Fixed: 0 errors, 0 mismatches.
