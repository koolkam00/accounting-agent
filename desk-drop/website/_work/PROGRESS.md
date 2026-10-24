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
