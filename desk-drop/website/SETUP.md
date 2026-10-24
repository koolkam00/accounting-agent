# Setup guide

Version 1.0 · 2026-10-24 · Workstream C (website). Steps marked **[FOUNDER LOGIN]** need your own account; nothing here has been signed up for, deployed or published. Sources were opened on 2026-10-24 and are listed in section 12.

**Status: build now, publish later.** The name is on HOLD (`desk-drop-legal-pack/name-check-log.md`), the form notices are drafts for attorney review, and the plan keeps the site private until Gate 1. Section 10 is the publish step; `tools/preflight.py` refuses to pass until all of that is done.

## 1. The stack (cost: $0 a month)

| Part | What | Why |
| --- | --- | --- |
| Pages | Plain HTML, CSS and a little JavaScript in `site/`. No framework, no build step | You edit the file that ships. Works from any host or subfolder |
| Settings | `site/site.config.js`: name, tagline, contact details, `STAGING`, form endpoint, founding tier, status line, analytics | One file for everything that changes |
| Look | `site/assets/css/tokens.css` (the identity workstream's tokens, copied) and `site.css`. Fonts self-hosted (Atkinson Hyperlegible Next, Bricolage Grotesque, SIL Open Font License) | No third-party requests; fast |
| Forms | A Google Apps Script web app (`apps-script/Code.gs`) attached to one Google Sheet with tabs `office_intake` and `brand_intake` | Free; one row and one email per submission |
| Visit counts | GoatCounter, called directly (no script from them) | Free for "small-to-medium business" use, no cookies |
| Hosting | Cloudflare Pages, Free plan, drag-and-drop upload of the `site/` folder | Free, custom domains, preview URLs carry `X-Robots-Tag: noindex` by default |

## 2. Own every account from day one

Create each account yourself with the business address [EMAIL]: Google (Sheet and script), Cloudflare, GoatCounter and the domain registrar. Then there is nothing to transfer. If someone else ever sets one up for you:
- **Google Sheet and script:** they share the Sheet with you as editor, then use Share > transfer ownership; the script moves with the Sheet. Redeploy the web app from your account (section 3, step 4) so it runs as you, and paste the new URL into the config. (Ownership transfer rules differ between personal and Workspace accounts: unverified, founder to confirm.)
- **Cloudflare Pages:** do not transfer; create a new project in your account and drag the same `site/` folder in (two minutes), then move the custom domain.
- **GoatCounter:** create your own and change `ANALYTICS.ENDPOINT`; old counts stay behind.
- **Domain:** a registrar-to-registrar or account-to-account push; steps vary by registrar (unverified, founder to confirm).

## 3. Forms: deploy the Apps Script **[FOUNDER LOGIN]** (about 15 minutes)

1. In Google Drive, create a Google Sheet (any name, for example "Website intake").
2. In the Sheet: **Extensions > Apps Script**. Delete the sample code and paste all of `apps-script/Code.gs`. Save.
3. In the toolbar, choose the function **setup** and click **Run**. Approve the permissions. Because the script is your own and unpublished, Google may warn that the app is not verified; choose Advanced and continue. The Sheet now has the tabs `office_intake` and `brand_intake`, each with its header row in the exact CONTRACTS order. Do not rename tabs or headers: the script refuses to write if they change.
4. **Deploy > New deployment**, type **Web app**. Execute as: **Me**. Who has access: **Anyone**. Deploy, and copy the **Web app URL** (it ends in `/exec`).
5. Paste it into `site/site.config.js` as `FORM_ENDPOINT: "https://script.google.com/macros/s/.../exec"`.
6. **Test it.** Open the `/exec` URL in a browser: you should see `{"ok":true,"service":"website-intake",...}`. Then upload the site to a preview (section 4) and send each form once with SAMPLE answers. Check: one new row in the right tab, every column filled in order, one email per form, with Reply-To set to the sender, and the page says "Thanks". Check that a phone like `+1 212 555 0100` and a floor like `3-4` show as typed. Delete the SAMPLE rows. The browser reading the script's reply follows a widely used pattern, not a Google-documented one, so this test is the real check.
7. **Changing the script later:** edit, save, then **Deploy > Manage deployments > Edit > Version: New version > Deploy**. The URL stays the same.
8. Notifications go to the account that deployed it (or set `SETTINGS.NOTIFY_TO` in `Code.gs`). Google's limit is 100 email recipients a day on a personal account and 1,500 on Workspace. The script also caps itself at 30 accepted submissions per 10 minutes and ignores the hidden honeypot field.
9. The operations workstream's tracker reads both tabs (column list in `HANDOFF.md`).

## 4. Staging and hosting **[FOUNDER LOGIN]**

- **Staging now:** a private claude.ai Artifact of `site/` (forms show "staging: submissions are not live yet"; no counting).
- **Cloudflare Pages:** dashboard > Workers & Pages > Create application > Drag and drop your files > name the project > drop the `site/` folder > Deploy. For a staging copy, create a new deployment to the **preview** environment (branch name `staging`): preview URLs get `X-Robots-Tag: noindex` automatically. Drag-and-drop takes up to 1,000 files of 25 MiB each; the site is about 25 files.
- **How staging stays out of search:** while `STAGING` is true every page adds a `noindex, nofollow` robots tag, `robots.txt` disallows everything, and `_headers` sends `X-Robots-Tag: noindex`. Google notes that a robots.txt block also stops it from seeing a noindex tag, so a staging URL that someone links publicly could still appear as a bare link. Do not post or share staging links.

## 5. Editing copy

1. Open the page in any text editor: `site/index.html` (home), `brands.html`, `offices.html`, `privacy.html`, `survey-privacy.html`. Find the sentence, change it, save.
2. Name, tagline, contact details and the "Where things stand" line are in `site/site.config.js`, not the pages.
3. Optional checks: `python3 tests/check_site.py` (claims, prices, links), then `python3 tools/export_copy.py` to refresh `COPY.md`.
4. Upload `site/` again. If you change a price or term, change it in the same words in the brand agreement (`desk-drop-legal-pack/10-…`) and the identity workstream's `system/dd-offer.js`.
5. The store list and map come from the cluster workstream: run `python3 tools/build_map.py` after it updates `map-public.geojson`.

## 6. The shelf photo

The brand page has a labeled slot for one photo: a printed test card on a real pantry shelf, no people in frame (the only product image the plan allows). Take it after the first test print, save it as `site/assets/img/shelf.webp` (about 1200 px wide, under 120 KB), and replace the `<p class="slot staging-only">` line in `brands.html` with `<img src="assets/img/shelf.webp" width="1200" height="900" loading="lazy" alt="A printed display card in front of sealed snacks on an office pantry shelf">`. Until then the slot shows only in staging.

## 7. Renaming

Change `BRAND_NAME` in `site/site.config.js`. That is the whole site: every page, title and notice reads it from there (`tests/e2e.js` proves it). The Apps Script and the favicon contain no name. Then, outside the site: the domain, the email address, and the identity workstream's wordmark (`desk-drop-identity/brand.json`).

## 8. Retiring the founding tier

After the third founding brand: set `FOUNDING_TIER_OPEN: false` in `site/site.config.js`. The $600 card, every "founding price" line and the founding FAQ answer disappear; standard and extra office stay. Brand question 6 still asks about approving $600 because the sheet column is `q6_contact_can_approve_600`; agree any wording change with the operations workstream first.

## 9. Visit counts **[FOUNDER LOGIN]**

1. Sign up at goatcounter.com with a code (for example the new name). Your dashboard is `https://CODE.goatcounter.com`.
2. Set `ANALYTICS.ENDPOINT: "https://CODE.goatcounter.com/count"` in `site.config.js`.
3. **Verify with a real visit (after publish):** open the live site in a normal browser with Do Not Track and Global Privacy Control off (some browsers, such as Brave, send Global Privacy Control by default, and the site then does not count you). Within a few minutes the dashboard should show the page. Start and send a SAMPLE form: the events `office-intake-started` and `office-intake-sent` appear. Delete the SAMPLE row from the Sheet.
4. Reading it: pages appear as `/`, `/brands`, `/offices`; events as `office-intake-started`, `office-intake-sent`, `brand-intake-started`, `brand-intake-sent`. Started against sent shows where people give up. The Sheet, not the counter, is the record of submissions. Automated visits (tests, Lighthouse) are flagged as bots and not counted.

## 10. Publish (only when all of these are true)

Name cleared or replaced (section 7); attorney has cleared the form notices and both privacy pages; Gate 1 reached (plan); domain bought.

1. **DNS [FOUNDER LOGIN].** Recommended: add the domain to Cloudflare (Free plan) and switch the registrar's nameservers to the two Cloudflare gives you; then in Pages > your project > Custom domains, add `DOMAIN` and `www.DOMAIN`. Alternative without moving nameservers: use `www.DOMAIN` only, add it in Pages first, then create a CNAME `www` → `PROJECT.pages.dev` at your registrar (adding the CNAME before the Pages step gives a 522 error). Keep your email's MX records when moving DNS.
2. In `site/site.config.js`: fill `DOMAIN`, `CONTACT_EMAIL`, `POSTAL_ADDRESS`, `FOUNDER_NAME`, `COMPANY_LEGAL_NAME`, `FORM_ENDPOINT`, `ANALYTICS.ENDPOINT`, and a true `ROSTER_STATUS`.
3. Fill `[DATE]` in `privacy.html` and `survey-privacy.html`; remove each "Draft for attorney review" line only once the attorney has cleared that text.
4. Run `python3 tools/make_production.py` (writes the production `robots.txt` and `sitemap.xml`, removes the staging noindex header), then set `STAGING: false`.
5. Run `python3 tools/preflight.py`. It must say `0 blocking`.
6. Upload `site/` to the **production** environment of the Cloudflare Pages project.
7. Check: `curl -I https://DOMAIN` shows no `x-robots-tag`; `https://DOMAIN/robots.txt` says `Allow: /`; do the real-visit check (section 9) and one SAMPLE submission per form (section 3, step 6).
8. Send the outreach workstream the live URL and deep links (`HANDOFF.md`).

## 11. Running the tests

`bash tests/run_all.sh` from `website/` (needs `npm install` once in `tests/`). What each test proves: `QA.md`.

## 12. Sources (opened 2026-10-24)

- Google Apps Script, web apps: https://developers.google.com/apps-script/guides/web (doPost, deploy steps, "Execute as me", reserved parameter names `c` and `sid`); deployments: https://developers.google.com/apps-script/concepts/deployments (new version, same URL); Content service redirects: https://developers.google.com/apps-script/guides/content; quotas: https://developers.google.com/apps-script/guides/services/quotas (email recipients 100 a day personal, 1,500 Workspace).
- Reading the script's JSON reply from a web page: the community pattern in https://raw.githubusercontent.com/jamiewilson/form-to-google-sheets/master/README.md (`fetch(...).then(response => response.json())`). Not Google documentation: verified only by the section 3, step 6 test.
- GoatCounter: https://www.goatcounter.com/ (free for "personal website or small-to-medium business"; no unique identifiers; "doesn't need a GDPR notice" in its own words), https://www.goatcounter.com/help/pixel (`/count` parameters `p`, `t`, `r`, `e`, `s`, `b`, `rnd`; building your own integration "should be safe"), https://www.goatcounter.com/help/events, https://www.goatcounter.com/help/sessions (IP and User-Agent never stored), https://www.goatcounter.com/help/gdpr.
- Cloudflare Pages: direct upload https://developers.cloudflare.com/pages/get-started/direct-upload/; preview noindex https://developers.cloudflare.com/pages/configuration/preview-deployments/; custom domains https://developers.cloudflare.com/pages/configuration/custom-domains/; `_headers` https://developers.cloudflare.com/pages/configuration/headers/; Free plan limits https://developers.cloudflare.com/pages/platform/limits/. The pricing page (https://www.cloudflare.com/plans/developer-platform/) did not render as text: Free plan cost unverified, founder to confirm at sign-up.
- Google Search, noindex and robots.txt: https://developers.google.com/search/docs/crawling-indexing/block-indexing (a robots.txt block stops Google from seeing a noindex tag); JavaScript-added robots meta: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics.
