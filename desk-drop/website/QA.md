# QA: pass bar, tests and results

The pass bar below was written on 2026-10-24 **before the first line of the site was built**. It does not move to fit results. Results are filled in by round at the end of this file; the commands that produce them are in `tests/README.md`.

## 1. Pass bar

| # | Check | Tool and method | Pass when |
| --- | --- | --- | --- |
| P1 | Speed, mobile | Lighthouse (npm `lighthouse`, default mobile preset: Moto G Power emulation, simulated slow 4G), Chromium from Playwright via `CHROME_PATH`. Every page: `index`, `brands`, `offices`, `privacy`, `survey-privacy`, `404` | Performance at least **95** |
| P2 | Accessibility score | Same Lighthouse runs | Accessibility **100** on every page |
| P3 | Best Practices | Same | at least **95** |
| P4 | SEO | Same, run twice: as staged (`STAGING = true`) and with a `STAGING = false` override | at least **95** with `STAGING = false`. With `STAGING = true` the only failing SEO audit allowed is `is-crawlable` (the deliberate noindex) |
| P5 | WCAG 2.1 AA | axe-core in Playwright, tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`; every page at 390 x 844 and 1280 x 800, light and dark color schemes, and these form states: empty, error summary shown, conditional fields open, staging notice, sent | **Zero** violations |
| P6 | Page weight | Playwright, cold cache, page scrolled to the end so every lazy image loads; sum of encoded bytes of every response | under **300 KB** per page, all files counted |
| P7 | Keyboard | Playwright: Tab through each page | Skip link is the first stop; every link, button and field is reachable in reading order; focus is always visible (outline at least 2 px); no trap; radio groups work with arrow keys; Enter submits; each error-summary link moves focus to its field |
| P8 | Labels | Playwright DOM check plus axe | Every field has a programmatic label; every radio or checkbox group is a `fieldset` with a `legend`; optional fields say "optional" in the label; errors are tied to fields with `aria-describedby` and `aria-invalid` |
| P9 | Office form in 90 seconds on a phone | Count fields and taps on the 390 x 844 layout; scripted Playwright run with touch; time estimate from stated typing rates | Estimated completion **90 seconds or less** without browser autofill, using the required fields only, at 2.5 typed characters per second plus 1.5 seconds per tap and 10 seconds of reading |
| P10 | Forms end to end | `tests/mock_endpoint.py` (same contract as `apps-script/Code.gs`) and Playwright at 390 x 844 and 1280 x 800 | Each submit writes exactly **one row** with the CONTRACTS 6.3 columns **in exact order** and exactly **one notification line**; the analytics event call reaches the stub; a filled honeypot writes nothing and sends nothing; a bad value is refused by the server; a repeated submission ID writes one row |
| P11 | Staging behavior | Playwright with the real `site.config.js` (`FORM_ENDPOINT` empty) | The form shows "staging: submissions are not live yet", sends **no** request and never shows the sent message; robots meta `noindex` present; `robots.txt` disallows all |
| P12 | Code.gs itself | `tests/test_code_gs.js` runs `Code.gs` in Node with fake Sheets, Mail, Lock, Cache and Content services | Same expectations as P10 against the real Apps Script code |
| P13 | Rename in one edit | Playwright with `BRAND_NAME` changed in a served copy of `site.config.js`; grep of every site file | The working name appears in no rendered text, title or meta after the change; outside `site.config.js` it appears in no site file (docs excepted) |
| P14 | Founding tier retirement | Playwright with `FOUNDING_TIER_OPEN = false` | Founding price and its form option disappear; standard price and extra office stay |
| P15 | Claims | `tests/check_copy.py` over every page | Prices exactly $600 / 5 offices, $1,500 / 10 offices, $150 per extra office; "free pilot" only in "No free pilots"; no "conversion", "ROI", "lift", "acquisition" or "guarantee" except in a negation; the review heading "Draft for attorney review. Not legal advice." under each form and on each privacy page; no testimonials, logos or invented numbers |
| P16 | Layout | Playwright at 320, 390, 768 and 1280 px wide | No horizontal scroll; tap targets at least 44 x 44 px for buttons, radios and checkboxes (label area) |
| P17 | Links and portability | `tests/check_links.py` | Every internal link and asset resolves; no root-absolute (`/...`) URL; no external script or stylesheet (fonts self-hosted), so the site works from any subfolder |
| P18 | Analytics privacy | Playwright request log | No request to any third party with the shipped config; with analytics configured, only the GoatCounter `/count` endpoint is called, with no cookies set; Do Not Track or Global Privacy Control turns it off |

"Verified with a real visit" for analytics cannot be done before publish (no account, no live URL). It is a founder step after publish, in `SETUP.md` section 9.

## 2. Results (final run, 2026-10-24, `bash tests/run_all.sh`; raw output in `tests/out/`)

| # | Result | Pass |
| --- | --- | --- |
| P1 | Lighthouse 13.5.0 mobile Performance: 99 to 100 on all 6 pages as staged, 100 on all 6 with `STAGING = false`. Mobile LCP 1.5 to 1.8 s, CLS 0, TBT 0 ms. Desktop: 100 everywhere, LCP 0.36 to 0.42 s | Yes |
| P2 | Accessibility 100 on all 24 runs (6 pages × mobile and desktop × staged and production) | Yes |
| P3 | Best Practices 100 on all 24 runs | Yes |
| P4 | SEO 100 on all 12 production runs. Staged runs score 63 to 66 and the only failing audit is `is-crawlable` (the deliberate noindex) | Yes |
| P5 | axe-core 4.14.0, tags wcag2a, wcag2aa, wcag21a, wcag21aa: **0 violations in 48 runs** (6 pages × 2 sizes × light and dark, plus conditional fields open, error summary shown and sent panel on both forms) | Yes |
| P6 | Everything loaded, cold cache, measured **uncompressed** (the local test server does not gzip, so these are upper bounds): index 110.2 KB, brands 165.7 KB, offices 127.6 KB, privacy 110.7 KB, survey notice 111.1 KB, 404 107.4 KB; 8 or 9 requests each. Gzipped on a real host the brand page is about 88 KB, 56 KB of it fonts | Yes |
| P7 | Tab order equals DOM order on every page (11, 36, 29, 9, 8 and 11 stops); skip link first and moves focus to the main content; every stop shows a focus ring of at least 2 px (radio and checkbox rings drawn on their label); arrow keys move a radio choice; Enter in a text field submits; error-summary links move focus to the field | Yes |
| P8 | 45 controls on the office page, 41 on the brand page: 0 unlabeled, 0 radio or checkbox outside a `fieldset` with `legend`, 0 optional fields without "(optional)", 0 required fields marked optional, every `aria-describedby` target exists; errors set `aria-invalid` and fill the linked message | Yes |
| P9 | Office form on 390 × 844 by touch: **6 typed fields (80 characters with the SAMPLE test values), 5 one-tap answers, 13 taps in all including the jump link and submit**; categories default to "Any of them" (0 taps). Estimate: 80 ÷ 2.5 = 32 s typing + 13 × 1.5 = 19.5 s tapping + 10 s reading = **61.5 s**; allowing 6 scroll swipes at 1.5 s gives **70.5 s, under 90**. With browser autofill for name, title, email, company and address, about 35 s. (For reference, the brand form: 8 typed fields, 11 one-tap answers, about 2 minutes.) | Yes |
| P10 | Both forms at 390 × 844 and 1280 × 800: each submit wrote **exactly one row** with the CONTRACTS 6.3 columns **in exact order** and **exactly one notification line**; the analytics stub received page views and `office-intake-started`, `office-intake-sent`, `brand-intake-started`, `brand-intake-sent`, with the campaign query; no CORS preflight; no cookies. Direct posts: filled honeypot wrote nothing and sent nothing; a bad `receiving_type` was refused; a repeated `submission_id` wrote one row. Sample output: `tests/out/sample-run/` | Yes |
| P11 | With the shipped config: staging notice above the form, "Staging: submissions are not live yet. Nothing was sent." on submit, no request left the site, no row, no thank-you panel; robots meta `noindex, nofollow`; `robots.txt` disallows all; `_headers` sends `X-Robots-Tag: noindex` | Yes |
| P12 | `test_code_gs.js`: 13 of 13 against the real `Code.gs` (columns parsed from `CONTRACTS.md`, setup, both forms, honeypot, validation, duplicates, repeated-field lists, header mismatch, unknown form, mail failure keeps the row, health check) | Yes |
| P13 | `BRAND_NAME` changed in a served copy of `site.config.js` only: old name absent from text, titles and meta on all 6 pages; static check: the name is in no site file except `site.config.js` | Yes |
| P14 | `FOUNDING_TIER_OPEN = false`: no founding price, $600 card or $120 line on any page; standard and extra office remain; price grid reflows to two cards | Yes |
| P15 | `check_site.py` 41 of 41: exact prices and terms present; money on the site is only $600, $120, $1,500, $150, $100 (cancellation) and $1M (insurance); banned words only in approved negations; seven ladder rungs; review heading under both forms and on both privacy pages; survey notice equals the legal pack's Part C word for word; form fields equal the schema | Yes |
| P16 | 24 runs (6 pages at 320, 390, 768, 1280): no horizontal scroll; no button, radio or checkbox label, nav link or text field under 44 × 44 px | Yes |
| P17 | Every internal link, asset and fragment resolves; no root-absolute URL; no external script, stylesheet or font; html-validate 0 problems | Yes |
| P18 | With the shipped config: 0 third-party requests, no cookies, no local or session storage on any page. With analytics on (test): only the GoatCounter-format `/count` endpoint is called; automated browsers are flagged `b=153` | Yes |

Not testable before publish (founder steps, `SETUP.md`): analytics verified with a real visit (section 9); the real Apps Script deployment, the Sheet and the Gmail notification (section 3, step 6), including the browser reading the script's JSON reply across origins.

## 3. Rounds

| Round | What changed | Found by |
| --- | --- | --- |
| 0 | Read the brief, plan, CONTRACTS and the B, D and G outputs; wrote this pass bar; researched Apps Script, GoatCounter, Cloudflare Pages and Google's noindex rules | |
| 1, draft | Six pages, config, name fill before paint, forms, CSS on D's tokens, `Code.gs` with one schema, mock endpoint, map builder, all test suites. Fixed: 413 px page width on phones (single-column grids sized to content), radio-group spacing lost to a selector clash, off-center intro blocks, honeypot counted as a tap target, a test tapping during smooth scroll | Screenshots, overflow probe, tests |
| 2, three readers | CPG lead: "where things stand" on the brand page, cancellation and per-office refund answers, founding statement and case-study term disclosed, "full terms are in the agreement". Office manager: errors listed in page order with clean punctuation, "Pantry owner's title", cross marks on "Not for" and "Never". Lawyer: placement confirmation and office approvals aligned to the legal pack's v0.7 agreements, "roughly monthly as supply allows", "vetted" defined, GoatCounter wording corrected, when a brand learns an office's name. Also: B's map numbers adopted; D's `--dd-rule` collision found and worked around | Persona review, legal pack re-read |
| 3, taste | Map label spacing; report mock labels; campaign tags passed to visit counts; preflight blocks publishing while any page still says "Draft for attorney review"; full re-run. Only taste changed, so iteration stopped | Final review |
