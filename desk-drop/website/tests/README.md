# Tests

Run everything from `website/`: `bash tests/run_all.sh` (about 10 minutes; `--no-lighthouse` skips the slow part).
Needs python3, node 22, Playwright with Chromium (installed globally here), and once: `cd tests && npm install` (axe-core 4.14.0, Lighthouse 13.5.0, html-validate 11.16.2, all pinned). Outputs go to `tests/out/`; screenshots to `_shots/`.

| File | What it proves (QA.md pass bar) |
| --- | --- |
| `check_site.py` | P13, P15, P17: identical header and footer on every page; every internal link, asset and `#fragment` resolves; no root-absolute URL and no external script, style or font; the working name appears only in `site.config.js`; `tokens.css` equals the identity workstream's file; exact prices and terms; banned words only in approved negations; ladder rungs; review heading under each form; the survey notice equals the legal pack's Part C word for word; form fields, required flags and option values equal the `Code.gs` schema; staging files agree with `STAGING` |
| `test_code_gs.js` | P12: runs the real `apps-script/Code.gs` in Node with fake Google services. Schema columns equal CONTRACTS 6.3 (parsed from `CONTRACTS.md`); one row and one email per submission; derived fields; formula escaping; text formats; honeypot; validation; duplicates; header mismatch; mail failure keeps the row |
| `mock_endpoint.py` | Local stand-in for the web app, same contract and same rules (it reads the schema out of `Code.gs`). Writes `office_intake.csv`, `brand_intake.csv`, `notifications.log`, and logs analytics hits from the GoatCounter-format `/count` stub to `analytics.log` |
| `e2e.js` | P9, P10, P11, P13, P14, P18: serves `site/`, starts the mock on a second origin, and fills both forms by touch at 390 x 844 and by mouse at 1280 x 800. Checks exact columns, one row and one notification each, analytics page views and the four form events, no CORS preflight, no cookies; staging config sends nothing and says so; error summary and focus; rename; founding tier off; `STAGING = false` |
| `quality.js` | P5 to P8, P16, P18: axe-core WCAG 2.1 A/AA on every page at both sizes in light and dark, plus form states; page weight with everything loaded; keyboard order, focus rings, skip link, arrows, Enter; labels and groups; no horizontal scroll at 320/390/768/1280; 44 px tap targets; no third-party requests or storage |
| `lighthouse.js` | P1 to P4: every page, mobile and desktop, as staged and with `STAGING = false` |
| `shoot.js` | Renders every page at phone and desktop width, light and dark, into `_shots/` |
| `.htmlvalidate.json` | HTML validity rules (html-validate recommended, minus style-only rules) |
| `out/sample-run/` | The rows, notifications and analytics hits from the last end-to-end run (SAMPLE data) |
| `out/*.json`, `out/lighthouse/` | Machine-readable results of the last run |
