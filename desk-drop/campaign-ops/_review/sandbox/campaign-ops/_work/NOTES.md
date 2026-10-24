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
- R2 generators + first full replay (zero): report (D renderer), exports (H headers exact), kit (D cards/labels; QR decoded from
  the printed PDF, both faces), links (+ local redirect test), route sheet, invoices, messages, SOP calendar + .ics, debriefs.
  Zero replay: 43 days, 0 formula errors, 0 disagreements. Fixes: info: vs actionable checks (dashboard could never reach 0);
  [DOMAIN] in qr_url makes D print no QR -> SAMPLE uses go.example.com; QR decode needs one face cropped; route rule text;
  scenario approvals replies now appear on their reply date.
- R3 standard run + four critics: a declined office blocked the ship release forever (rule now: no approvals pending, >=1
  approved; short of contract = info with the credit); campaign totals (min responses, depleted, photo compliance) now over
  approved offices only; one approval email per office per drop (pantry owner); report email discloses excluded answers
  (finance); route sheet start line, late rule, certificate wording, "front desk or mailroom" (ops); Sheets report tab shows
  top-ups; drop-level Gate 2 columns; customer-facing sales-tax line; survey tab header check; people photos deleted;
  invoice status counts an applied credit; no health wording in samples (privacy); ship-date email per delivery model;
  direct-ship variant (tracking sheet) generated; optional Apps Script + mock test.
- R4 final (the founder typing real rows): a refused or missing drop date turned the checks of its campaigns and approvals
  into #VALUE! (LibreOffice, like Google Sheets, refuses date arithmetic on an empty text result; tested directly) -> N()
  guards, plus new tests/test_edge_rows.py (refused date, no date, typo IDs on seven tabs, invoice without campaign, office
  missing from E's file), each now a plain check; survey-link checks wait until T-4; links only for offices that said yes
  (a declined office had a link pair and the link test expected a card); replay adds each campaign's survey tab from its own
  drop's T-4; intake-mapping test compares categories with the form answer. Both scenarios replayed again on the final code.

## Stage 2, round R5 (2026-10-24, from 08:18 UTC): fresh critics on the finished build
State found: all tests pass; both dry runs and the direct-ship variant replayed on the R4 code (zero 44 days, standard 56,
0 formula errors, 0 disagreements). Not yet done: load exports into a copy of H's workbook; SAMPLE exports under exports/;
form rows as CSV; E's real handoff files (published 07:53) never pasted into the tracker.
Findings to fix (critic: item):
- finance: credit note prints "How to pay" with our bank details (we owe them); report roster skips the letter of an office
  that declined (G on SAMPLE-CMP-004), so "where is G, was it billed?"
- privacy: office summary prints every comment raw (SAMPLE "Asked Priya to save me a bag" reaches the pantry owner unless the
  founder catches it); per-office rating and buy split shown even with 1 or 2 answers (owner can infer one person's answer);
  no retention rule for a pantry owner's name, phone and email after the office leaves; the printed route sheet (owner phones)
  has no return-or-shred line for a courier or backup.
- pantry owner: T-1 text asks "who should I hand it to?" (collects another person's name and contradicts the front-desk rule);
  budget question repeated at every monthly debrief; debrief only as a call; allergen line without a full stop runs into
  "About 40 units" in the approval email.
- ops lead: route sheet's last page holds two orphan lines of "After the route"; that block is for the founder but is not
  labelled so; SAMPLE hours logged on 2026-12-25 and 2027-01-01 (calendar weeks back from signing).
- integration: E's SAMPLE handoff files to paste-test; E needs the ship-to address field named; E's domain-age rule (32 days)
  belongs in the runbook; link test ignores the Short.io import file the founder actually uploads.
Fixes made in R5 (each logged where it lives):
- invoices: a balance invoice lists every credit note taken off it and totals "Amount due"; a credit note says "How this is
  settled" (refund within five business days, or "pay $X on invoice Y instead of $Z"), never "How to pay"; the balance line
  says "placed by T+1 in 9 of 10 offices".
- letters: office_seq/office_label count only offices that have not declined the brand (formulas.py and tracker.py, compared
  0 disagreements); SAMPLE-CMP-004 now runs A to I.
- office summaries: likely names replaced with [name removed] (capitalized words not starting a sentence, except brand,
  product, retailer, office, cluster, weekdays, months); a brand's answers are not broken down where an office gave fewer than
  config office_summary_min_answers (3); brand-report quotes that may hold a name print a warning.
- T-1 text: no longer asks "who should I hand it to?"; it states the agreed rule (front desk, or next morning; for
  direct-ship, ask the carrier for next morning) and who brings it in each model.
- approval email: the package text is quoted and labelled by allergen_source (statement, ingredient list, single ingredient).
- route sheet: pickup address and a pickup time 20 minutes before the first stop (was hard-coded 7:45 am); "N cases in all"
  and a signed pickup count; reserve wording per model; "When the route is done" kept on one page, for a courier or backup
  (send it back, keep no copy) and for the founder (shred once counted); Issue line fits 375 px (scrollWidth 375 = viewport).
- debrief: the budget question at an office's drops 1, 4, 7...; the debrief can be an email reply.
- privacy: config contacts_keep_days_after_leaving (365) plus a dashboard check line; SOP privacy schedule rows for the route
  sheet, office summaries and departed offices; runbook step 23.
- dashboard: "contribution before overhead" with a note on why the financial model's figure is lower.
- exports: dry runs also write exports/SAMPLE-<scenario>/ (SAMPLE rows refused in the live files, real rows refused in a
  SAMPLE folder); tools/dump_forms.py writes every form's rows as CSV per dry run (dry-run/<scenario>/forms/).
- tests: test_e_handoff.py (E's own SAMPLE files pasted, read by name, dashboard checks both ways); test_h_import.py (copy of
  H's workbook loaded, recalculated, compared, negative control, SHA unchanged); test_links.py checks the Short.io import file.
- SAMPLE hours moved off 2026-12-25 and 2027-01-01 (business days back from signing).
- runbook: domain age (32 days, per E's S17) for go.[DOMAIN]: register by Mon 2026-12-07.
- Research 2026-10-24: Dropbox Sign Free = 3 signature requests per 30 days, a bundle counts as one, signed PDF plus audit
  trail (help.dropbox.com/plans/dropbox-sign-free-plan, opened 2026-10-24). Essentials $15/month or $10.05/month billed yearly
  (sign.dropbox.com/products/dropbox-sign/pricing, opened 2026-10-24; the page gives no free-plan limits). PandaDoc pricing
  page returned HTTP 429 (unverified). Decision: offices sign by "I agree" email (file 03 s.10), brands by Dropbox Sign free,
  signed PDF by email beyond the quota (file 10 s.14). Runbook step 12a.
Later in R5 (second critic pass on the brand emails and the direct-ship sheet):
- finance/ops: the ship-date email went stale when a tenth office joined after release (brand told 523 units, 567 needed):
  campaigns gain ship_email_sent_date and ship_email_units; checks say "ship-date email due" and "units changed since the
  ship-date email ... send the revised numbers" (only while nothing is received); make_messages drafts "<cid>-revised-<date>.md"
  ("This replaces my ship-date email of ..."); the replay sends it when the check shows. SAMPLE scenario fixed: Tallgrass's
  -3 per office override is now typed on 2027-01-29 (the short shipment), not at approval time.
- finance: placement confirmation now counts contracted offices ("9 of 10"), explains an office short of the contract and
  its credit, states the amount due today (balance less credit) or the refund and its credit note.
- ops: courier heads-up rule on the route sheet ("Courier for ... about 20 minutes away"); direct-ship sheet says "Shipped
  by the brands straight to the offices"; SAMPLE direct-ship tracking numbers per brand.
- privacy: the office-summary threshold applies to every figure (no rating or would-buy split from fewer than 3 people,
  even where the office gave 3 or more answers); tests/test_office_summary.py.
- legal handoff: e-signature tool decided (runbook 12a).
R5 final state (09:20 UTC): both dry runs replayed on the final code (zero 44 days, standard 57 days; 0 formula errors, 0
disagreements; no tool refused); zero's route sheet (T-1 snapshot) and reports and office summaries (T+7 snapshot)
regenerated after two tool-only fixes, noted in its log; direct-ship variant re-run; tests/run_all.sh ALL PASS in about 2
minutes (calendar, blank build and recalculation, awkward rows, forms script, intake mapping, outreach handoff with E's
09:12 files (5 offices, 1 brand), links and QR 78 links, office summaries, financial-model load, folder rules).
