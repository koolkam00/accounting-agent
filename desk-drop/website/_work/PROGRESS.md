# Website (C) working log. Not a deliverable.

## Inputs (read 2026-10-24)
- D tokens/tokens.css, wordmark, symbol, avatar, SYSTEM.md: present. Import tokens (copy into assets/css/tokens.css).
- G: name gate HOLD (USPTO refused DESK-DROP as descriptive; a "DeskDrop" chocolate-gift business exists). Survey notice Part C to host. Footer: postal address.
- B: map-public.geojson NOT present at start (B assembling). Build labeled slot + tools/build_map.py.
- No earlier website draft attached: audit skipped.

## Decisions
- Pages: index, brands, offices, privacy, survey-privacy, 404.
- Name only in site.config.js; filled by MutationObserver in head (no CLS).
- Fonts self-hosted (Google Fonts latin woff2), no third-party requests.
- Analytics: TBD after research (GoatCounter pixel API vs Cloudflare).

## Status
- [ ] research  - [ ] pass bar QA.md  - [ ] build r1  - [ ] tests  - [ ] lighthouse/axe  - [ ] shots  - [ ] docs

## Round 1 (built + tested) 2026-10-24
- Pages, config, boot, site.js, CSS, Code.gs, mock, map builder done. B map-public landed (16 stores, map_number used).
- Tests: Code.gs 13/13, e2e 14/14, quality all pass (axe 48 runs 0), check_site 41/41, Lighthouse all pass (perf 99-100, a11y 100, bp 100, seo 100 prod; staging only is-crawlable).
- Next: persona critique round 2, docs (README, HANDOFF, SETUP, COPY, QA results), report text.
## Round 3 done: all suites pass (see QA.md). Docs written.

## Review round 1 fixes (started 2026-10-24)
Plan: R1-01 survey notice v0.6 (+data-config email/address/company); R1-02 cancel FAQ (drop-day cut-off, G10 v0.8 s8);
R1-03 "Who runs this" (FOUNDER_NAME, PHONE, FOUNDER_LINKEDIN; footer founder+phone); R1-04 office exclusions plain + "Not yet" crosses;
R1-05 preflight blocks any bracket placeholder / .ph outside mocks; R1-06 founding lock up to 10 + founding disclosure;
R1-07 survey wording; R1-08 ROSTER_STATUS true line + ROSTER_STATUS_DATE (preflight blocks >14 days);
R1-09/11/12 make_production.py builds publish/ (stamped name, static meta, extensionless canonical/sitemap, 404 root-absolute);
R1-10 staging robots Allow + static noindex meta; R1-13 method=post + submit disabled until JS; noscript points to footer;
R1-14 unit counts; R1-15 q6 amount follows founding toggle ($1,500 after, not $750) + form_version brand_standard_only;
R1-16 name gate inverted (needs "Public launch (C): CLEARED YYYY-MM-DD"); R1-17 deviation documented + qualifier dropped;
R1-18 report mock phone layout; R1-19 map label/arrow + office map note; R1-20 docs, assumptions list, fresh run log.

## Review round 1 done (2026-10-24): all 20 findings fixed; run_all exit 0; builder response appended to _review/round-1.md.

## Review round 2 fixes (started 2026-10-24)
Previous report text (fix:C:r1) saved at scratchpad C-r2fix/report-r1.md. Plan per finding:
R2-01 exact case-sensitive CLEARED line + negative-word block + 3 tests; R2-02 SETUP s4 numbered steps, placeholder
production folder tools/production/placeholder/ (+_headers), neutral project name; README line; R2-03 README "Questions
for the founder"; R2-04 make_production stamps founding-closed + removes data-founding; e2e JS-off check;
R2-05 check 4 / q4 275 vs 550 spans; Code.gs label; HANDOFF note; R2-06 eye level where pantry allows, help reach 5;
R2-07 notice wording x3; R2-08 SETUP s3 step 10 + markRowsToDelete() + F handoff; R2-09 SETUP s10 + preflight G10/G03 draft;
R2-10 pantry_owner_title optional, P9 both paths; R2-11 mock: What we learned block, column names, photo labels;
R2-12 day numbering; R2-13 HANDOFF extra cols, apostrophe check; R2-14 FAQ lead time + we-cancel refund;
R2-15 P11 bar note, SETUP quick card, ledger 17, deviation 6.
## Review round 2 done (2026-10-24): all 15 findings fixed (3 majors, 12 minors); also "5 or 10" fact follows the tier,
D's --dd-rule-color adopted. run_all exit 0 (64 static, 25 preflight, 17 Code.gs, 19 e2e, quality 48 axe runs 0, Lighthouse all
pass, preflight 20 blocking). P9: 79.1 s / 86.6 s. Builder response appended to _review/round-2.md. Report text in
scratchpad C-r2fix/report-r2.md (returned in the structured output).

## Review round 3 fixes (started 2026-10-24)
Report text working copy: scratchpad C-r3fix/report-r3.md. Plan: R3-01 CLEARED line binds name + date<=today (+brand.json
match) + 3 tests, HANDOFF/SETUP line; R3-02 notification cut to subject/company/email/row link + privacy wording + SETUP
deletion-request step; R3-03 veto/anything-else hints + notice sentence; R3-04 thank-you wording + headcount note;
R3-05 stamp() strips staging bar/staging-only/data-staging-form + check_build block + e2e assert; R3-06 delete muted note +
preflight block; R3-07 brand terms (photo day, card text, tax, outside-events cancel) + ledger; R3-08 P21 brand 2-minute
measure (+ at-a-glance if fails); R3-09 SETUP s3 step 6 localhost; R3-10 re-run build_map + drift check in check_site.
- r3 status: all 10 code/doc fixes made; tests: check_site 86, preflight 40, Code.gs 17, e2e 21 (P21 118.3 s; P9 80.6/88.1 s). Full run_all in progress; then QA results, shots, report.
- r3 done: all fixes in; final run_all exit 0 (86/40/17/21, axe 48/0, LH pass); builder response appended; report returned in structured output.
