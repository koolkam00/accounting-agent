# Merge notes (workstream G, merge step)

Started 2026-10-24. Inputs: parts A and B (see `partA-notes.md`, `partB-notes.md`), plan.md, CONTRACTS.md, prompts/G-legal-admin-pack.md.

## Renumbering (old -> new), so numbers follow the plan's order of operations

| Old | New | Plan step it serves |
| --- | --- | --- |
| 00-index.md | 00-index.md | (index) |
| 01-name-check-log.md | 01-name-check-log.md | Week 1: name check |
| 10-email-footer-and-checklist.md | 02-email-footer-and-checklist.md | Week 1: first outreach email |
| 11-office-participation-agreement.md | 03-office-participation-agreement.md | Phase 1, weeks 3 to 5: an office says yes |
| 02-formation-checklist.md | 04-formation-checklist.md | LLC, EIN, bank at the first verbal brand yes |
| 30-llc-operating-agreement.md | 05-llc-operating-agreement.md | Same day as filing |
| 20-gl-quote-request-script.md | 06-gl-quote-request-script.md | Insurance before the first case arrives (quotes at Gate 0) |
| 21-food-safety-call-script-and-log.md | 07-food-safety-call-script-and-log.md | State storage call before the first case arrives |
| (new) | 08-attorney-hour-agenda.md | Attorney hour before the first invoice |
| 22-accountant-question-list.md | 09-accountant-question-list.md | Accountant hour before the first invoice |
| 12-brand-campaign-agreement.md | 10-brand-campaign-agreement.md | First invoice: brand agreement |
| 14-coi-request-brand-product-liability.md | 11-coi-request-brand-product-liability.md | With the brand agreement; checked before T-10 |
| 15-coi-request-own-carrier-building.md | 12-coi-request-own-carrier-building.md | After GL is bound; per building |
| 13-survey-privacy-notice.md | 13-survey-privacy-notice.md | Live from campaign zero |
| name-check-log.md | name-check-log.md (kept: CONTRACTS 6.7 path) | |
| figures.csv | figures.csv | |

## One company-name approach (pack-wide)

- Legal name: the slot `[COMPANY NAME: Desk Drop LLC]`, set once per document in its definition line. Elsewhere "the Company", "we", "our company", or the bare `[COMPANY NAME]` where the founder types the name into an email, form or certificate.
- Trading name: `BRAND_NAME = Desk Drop`, set once, only in the files that need the trading name (01, 02, name-check-log.md). Elsewhere `{BRAND_NAME}`.
- Check: every numbered document and name-check-log.md contains the working name exactly once (`_work/check_pack.py`).

## Merge to-do (status kept here)

1. Rename files; rewrite cross-references in one pass (old->new map, no chained substitution).
2. Name slot in 03, 05, 10, 11, 12, 13; BRAND_NAME format in 01, name-check-log.md.
3. Version line "Version 0.5 · 2026-10-24" everywhere; drop "part A/part B" wording.
4. Escape every `$` outside code so GitHub and pandoc do not read dollar pairs as math.
5. Align: storage duration wording; cancellation summary in 09; attorney/accountant timing (book at Gate 0, hold in week 4 by Fri 2026-11-20).
6. New 08 attorney-hour agenda, consolidating A's and B's attorney items.
7. figures.csv: new file names, timing, rows for the mailing address and the biennial statement.
8. Four-person review pass; revise; log each round.
9. Re-render 03, 05, 10, 13 (PDF, DOCX, PNG) and look at every page.
10. README.md, HANDOFF.md, REPORT.md; 00-index.md.

## Changelog (merge rounds)

(filled as rounds complete)
