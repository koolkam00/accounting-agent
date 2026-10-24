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
