# Website (workstream C)

Version 1.1 · 2026-10-24 (review round 1). A small, fast static site that explains the offer to brands and to offices, and turns each into a completed intake form. Built, tested and **not published**: the name is on HOLD (`desk-drop-legal-pack/name-check-log.md`), the notices are drafts for attorney review, and the plan keeps the site private until Gate 1. No earlier website draft was attached, so there was nothing to audit.

**No staging URL exists yet.** Publishing, even to a private preview, is the founder's step (`SETUP.md` section 4). To look at the site now, from `website/`: `python3 -m http.server 8000 --directory site`, then open http://localhost:8000. (Opening `site/index.html` straight from disk works, but the browser then blocks the self-hosted fonts.)

**Start here:** `SETUP.md` (one page: stack, accounts, forms, DNS, editing, renaming, founding tier, analytics, the publish step).

## Files, in the order you use them

| File or folder | What it is | How to edit it |
| --- | --- | --- |
| `SETUP.md` | The setup guide. Steps that need your login are marked **[FOUNDER LOGIN]** | Text editor |
| `site/` | **The website, staging version.** Upload this folder for a private preview (Cloudflare Pages drag and drop). Everything inside uses relative links, so it works from any folder. Every page carries a noindex tag | See below |
| `site/site.config.js` | The one settings file: `BRAND_NAME`, `TAGLINE`, `DOMAIN`, contact details (`CONTACT_EMAIL`, `PHONE`, `POSTAL_ADDRESS`, `FOUNDER_NAME`, `FOUNDER_LINKEDIN`, `COMPANY_LEGAL_NAME`), `STAGING`, `FORM_ENDPOINT`, form versions, `FOUNDING_TIER_OPEN`, `ROSTER_STATUS` and its date, `ANALYTICS` | Text editor. A rename is one edit here |
| `site/index.html` | Home: what this is, two doors (brands, offices), where things stand, how it works | Text editor |
| `site/brands.html` | For brands: positioning line, where things stand, who runs this, what a campaign includes, price, what you send, report contents, measurement ladder, timeline, the seven checks, store map, the card, straight answers, brand form | Text editor. The map block between `MAP:START` and `MAP:END` is generated |
| `site/offices.html` | For offices: the pitch, get and give, how a drop works, office form, what is in the case, privacy, who can join and who cannot yet, map | Same |
| `site/privacy.html` | Website privacy notice (forms and visit counts). Draft for attorney review | Same |
| `site/survey-privacy.html` | The legal pack's survey notice, Part C (version 0.6), word for word (G's `[PRIVACY URL]`) | Edit `desk-drop-legal-pack/13-…` first, then copy it here; `tests/check_site.py` fails if they differ |
| `site/404.html` | Page not found | |
| `site/robots.txt`, `site/_headers` | Staging versions: robots.txt lets crawlers fetch pages so they see the noindex; `_headers` adds security headers and `X-Robots-Tag: noindex` on Cloudflare Pages | `tools/make_production.py` writes the production versions into `publish/` |
| `site/assets/` | `css/tokens.css` (identity tokens, copied), `css/site.css`, `js/boot.js` (fills the name and settings before paint), `js/site.js` (forms, counts), `fonts/` (self-hosted, OFL), `img/` (favicon, touch icon, `cluster-map.svg`) | `tokens.css`: never by hand, run `tools/sync_tokens.py` |
| `tools/preflight.py` | Refuses to pass until everything needed for publishing is true: name gate says CLEARED, attorney headings removed, endpoint, contact details, no `[BRACKET]` left on any page, status line dated within 14 days, and a correct production copy | Run before every production upload |
| `tools/make_production.py` | Writes `publish/`, the production copy you upload: name and contact details written into the HTML (for link previews and visitors without JavaScript), no noindex, extension-less canonical links, production `robots.txt` and `sitemap.xml`, a 404 page that works on nested paths. Refuses while the preflight blocks. `site/` is never changed | `SETUP.md` section 10 |
| `publish/` | Not in the repository: created by `tools/make_production.py` at publish time | Never by hand |
| `apps-script/Code.gs`, `appsscript.json` | The form backend: one row per submission in `office_intake` or `brand_intake` (CONTRACTS 6.3 columns, exact order), server validation, honeypot, one email per row | Paste into the Sheet's Apps Script editor (`SETUP.md` section 3). The field rules (`SCHEMA`) live here only |
| `COPY.md` | Copy deck: claims ledger (every claim and its source) plus every word on every page, regenerated from the pages | Part 1 by hand; Part 2 by `tools/export_copy.py` |
| `QA.md` | The pass bar (set before building), the tests and the results by round | |
| `HANDOFF.md` | What this workstream takes from B, D and G, and gives F (sheet columns and values) and E (deep links, two-line descriptions); questions for G; a bug report for D | |
| `tools/build_map.py` | Draws the map and store list from `cluster-1-flatiron/map-public.geojson` | Re-run when B updates the map |
| `tools/export_copy.py` | Regenerates the deck in `COPY.md` from the pages | |
| `tools/sync_tokens.py` | Re-copies the identity tokens | |
| `tools/production/` | Templates for the production `robots.txt` and `sitemap.xml` | |
| `tests/` | Every test, `tests/README.md`, `run_all.sh`; `out/` holds the last results, `out/run_all.log` and a SAMPLE run of both forms | `bash tests/run_all.sh` |
| `_shots/` | Every page at 390 px and 1280 px, light and dark; `states/` holds form states (errors, staging message, sent, founding tier off) | Regenerated by the tests |
| `_review/` | The independent review rounds and the builder's response to each | |
| `_work/` | Working log and the raw source pages behind `SETUP.md` (kept, not needed day to day) | |

`REPORT.md` (the report back) is returned to the orchestrator as text and saved here by it.

## What is decided where

- **Copy:** the `.html` pages. **Settings and the name:** `site/site.config.js`. **Field rules and sheet columns:** `apps-script/Code.gs` (`SCHEMA`), checked against CONTRACTS 6.3 by the tests. **Look:** the identity tokens.
- Nothing here sends, deploys or signs up for anything. Every live step is the founder's, in `SETUP.md`.

## Assumptions (numbered; `COPY.md` and `REPORT.md` cite these numbers)

1. No earlier website draft was attached, so there is no audit.
2. Stack at $0 a month: static HTML on Cloudflare Pages (Free plan; its cost was not shown as text on the pricing page: unverified, founder to confirm at sign-up), a Google Apps Script web app writing to one Google Sheet, and GoatCounter for visit counts.
3. The report is promised "within seven business days of the drop" (CONTRACTS section 3, T+7), not the prompt's "within seven days": business days is what the calendar supports.
4. D's tokens, fonts, symbol and avatar are used as delivered; no provisional visual system was made. The name is typeset with D's class instead of the wordmark SVG, so a rename stays one edit.
5. The site stays private until the name is cleared, the attorney clears the notices and Gate 1 is reached (plan). Until then the only preview is one the founder uploads.
6. One survey privacy page serves every campaign. Its `[BRAND]` and `[BRAND PRIVACY POLICY URL]` slots stay highlighted until G rewrites them generically (question in `HANDOFF.md`); the publish preflight blocks while they remain.
7. Visit counts: page views plus four form events, no cookies, Do Not Track and Global Privacy Control respected. "Verified with a real visit" can only happen after publish (`SETUP.md` section 9).
8. An office not placed by the day after the drop comes off the invoice or is refunded, unless replaced: G 10 section 8. It is not in the plan, so the attorney should confirm it.
9. Form answers are deleted within 12 months if nothing proceeds: this workstream's default, for the attorney to confirm.
10. Offices: 40 to 250 people on a Tuesday; under 30 or over 250 is stated as "can't take you yet" (plan, "Excluded in the first six months"); 30 to 39 is the founder's call, so the form accepts any headcount and the founder decides.
11. Brand check 6 asks about $600 while the founding tier is open and $1,500 once it closes: the standard price is what the signer approves (G 10 section 14), not $750, the first half-payment. The column stays `q6_contact_can_approve_600`; `form_version` tells the two apart (`brand-1.0`, `brand-2.0`).
12. The founder is named on the brand page ("Who runs this"), above the office form and in every footer, with email, phone and LinkedIn. `PHONE` or `FOUNDER_LINKEDIN` set to "" hides that line.
13. The status line "No offices are signed yet and no campaign has run" is true on 2026-10-24 and stays true until the first office signs. It must be rewritten before publishing; the preflight blocks if `ROSTER_STATUS_DATE` is more than 14 days old.
14. Office category labels are CONTRACTS section 4's labels without the "shelf-stable" qualifier (every product is shelf-stable by rule); the keys are exact. Listed as a deviation in `HANDOFF.md`.
15. The map and store list follow B's `map-public.geojson` as it stood at the last `tools/build_map.py` run (14 stores, 4 inside the cluster, on 2026-10-24). B was still revising it; re-run the script when B is final.
16. No drop date appears on the site: the CONTRACTS dates are "derived, founder to confirm".
17. Production URLs are extension-less (`/brands`), because Cloudflare Pages redirects `/brands.html` there (Cloudflare docs, opened 2026-10-24). Links inside the site stay `.html`, which works on any host.
