# Setup guide

Version 1.3 · 2026-10-24 (review round 3) · Workstream C (website). Steps marked **[FOUNDER LOGIN]** need your own account; nothing here has been signed up for, deployed or published. Sources were opened on 2026-10-24 and are listed in section 12.

**Status: build now, publish later.** The name is on HOLD (`desk-drop-legal-pack/name-check-log.md`), the form notices and the legal pack's brand and office agreements are drafts for attorney review, and the plan keeps the site private until Gate 1. Section 10 is the publish step; `tools/preflight.py` refuses to pass until all of that is done.

## Quick card (the one page; the numbered sections below are the detail)

| You want to | Do this | Detail |
| -------------- | ---------------------------------------------------------- | ---------- |
| Decide first | Domain, business email, postal address for the footer, public phone: each has a recommended default | `README.md`, "Questions for the founder" |
| Know the stack | Static pages in `site/`, one settings file `site/site.config.js`, forms to a Google Sheet by Apps Script, visit counts by GoatCounter, hosting on Cloudflare Pages. $0 a month | §1 |
| Own the accounts | Create Google, Cloudflare, GoatCounter and the registrar yourself, on your business address; then nothing needs transferring | §2 |
| Turn the forms on | Paste `apps-script/Code.gs` into a new Sheet, run `setup`, deploy as a web app, paste the `/exec` URL into `FORM_ENDPOINT`, send one SAMPLE answer per form | §3 |
| Look at the site before launch | `python3 -m http.server 8000 --directory site` from `website/`, open http://localhost:8000. That is the only staging until you follow §4 | §4 |
| Edit copy | Edit the sentence in `site/*.html` (settings in `site.config.js`) | §5 |
| Rename | Change `BRAND_NAME` in `site/site.config.js`, then rebuild the production copy | §7 |
| Retire the founding tier | Set `FOUNDING_TIER_OPEN: false`, then rebuild the production copy | §8 |
| Read the visit counts | `https://CODE.goatcounter.com`: pages and the four form events | §9 |
| Point the domain | Add the domain to Cloudflare, switch nameservers, add it in Pages > Custom domains | §10, step 1 |
| Publish | When the name, the attorney and Gate 1 all say yes: fill the settings, `python3 tools/preflight.py`, `python3 tools/make_production.py`, upload `publish/` to production | §10 |

## 1. The stack (cost: $0 a month)

| Part | What | Why |
| --- | --- | --- |
| Pages | Plain HTML, CSS and a little JavaScript in `site/`. No framework, no build step | You edit the file that ships. Works from any host or subfolder |
| Settings | `site/site.config.js`: name, tagline, contact details, `STAGING`, form endpoint, founding tier, status line, analytics | One file for everything that changes |
| Look | `site/assets/css/tokens.css` (the identity workstream's tokens, copied) and `site.css`. Fonts self-hosted (Atkinson Hyperlegible Next, Bricolage Grotesque, SIL Open Font License) | No third-party requests; fast |
| Forms | A Google Apps Script web app (`apps-script/Code.gs`) attached to one Google Sheet with tabs `office_intake` and `brand_intake` | Free; one row and one short email per submission (the answers stay in the Sheet) |
| Visit counts | GoatCounter, called directly (no script from them) | Free for "small-to-medium business" use, no cookies |
| Hosting | Cloudflare Pages, Free plan, drag-and-drop upload: a blank placeholder in production until launch, the `site/` folder in a locked preview, then the `publish/` folder (written by `tools/make_production.py`) in production (§4, §10) | Free, custom domains, preview URLs carry `X-Robots-Tag: noindex` by default |

## 2. Own every account from day one

Create each account yourself with the business address [EMAIL]: Google (Sheet and script), Cloudflare, GoatCounter and the domain registrar. Then there is nothing to transfer. If someone else ever sets one up for you:
- **Google Sheet and script:** they share the Sheet with you as editor, then use Share > transfer ownership; the script moves with the Sheet. Redeploy the web app from your account (section 3, step 4) so it runs as you, and paste the new URL into the config. (Ownership transfer rules differ between personal and Workspace accounts: unverified, founder to confirm.)
- **Cloudflare Pages:** do not transfer; create a new project in your account and drag the same folder in (two minutes), then move the custom domain.
- **GoatCounter:** create your own and change `ANALYTICS.ENDPOINT`; old counts stay behind.
- **Domain:** a registrar-to-registrar or account-to-account push; steps vary by registrar (unverified, founder to confirm).

## 3. Forms: deploy the Apps Script **[FOUNDER LOGIN]** (about 15 minutes)

1. In Google Drive, create a Google Sheet (any name, for example "Website intake").
2. In the Sheet: **Extensions > Apps Script**. Delete the sample code and paste all of `apps-script/Code.gs`. Save.
3. In the toolbar, choose the function **setup** and click **Run**. Approve the permissions. Because the script is your own and unpublished, Google may warn that the app is not verified; choose Advanced and continue. The Sheet now has the tabs `office_intake` and `brand_intake`, each with its header row in the exact CONTRACTS order. Do not rename tabs or headers: the script refuses to write if they change.
4. **Deploy > New deployment**, type **Web app**. Execute as: **Me**. Who has access: **Anyone**. Deploy, and copy the **Web app URL** (it ends in `/exec`).
5. Paste it into `site/site.config.js` as `FORM_ENDPOINT: "https://script.google.com/macros/s/.../exec"`.
6. **Test it.** Open the `/exec` URL in a browser: you should see `{"ok":true,"service":"website-intake",...}`. Then upload the site to a locked preview (section 4), or, if you keep to the local preview (README question 9, the recommended default), run `python3 -m http.server 8000 --directory site` from `website/` with `FORM_ENDPOINT` set, and open http://localhost:8000/offices.html and http://localhost:8000/brands.html. The forms accept any `https://` endpoint from any page address, so the local test reaches the real script and Sheet. Send each form once with SAMPLE answers. Check: one new row in the right tab, every column filled in order, one short email per form (company or brand, contact email and a link to the row, no other answers), with Reply-To set to the sender, and the page says "Thanks". Paste the Gmail search printed at the bottom of the notification into Gmail's search box: it must find that email (the monthly deletion check relies on it; the `in:anywhere` operator was not tested here, founder to confirm). Check that a phone like `+1 212 555 0100` and a floor like `3-4` show as typed. Delete the SAMPLE rows. The browser reading the script's reply follows a widely used pattern, not a Google-documented one, so this test is the real check.
   - **The apostrophe check.** Text that starts with `+`, `-`, `=` or `@` is written with a leading apostrophe into a plain-text cell, so Sheets never runs it as a formula. Whether Sheets then keeps that apostrophe in the stored value is unverified (founder to confirm). Click the phone cell: the formula bar must show `+1 212 555 0100`. Then File > Download > CSV and open it: the phone must read `+1 212 555 0100`. If either shows `'+1 212 555 0100`, set `APOSTROPHE_GUARD: false` in `SETTINGS` at the top of `Code.gs`, redeploy (step 7), and send the SAMPLE office form again with `=1+1` in "Anything else?": the cell must show `=1+1` as text, not `2`. If it shows `2`, set it back to `true` and tell the operations workstream to strip one leading apostrophe (`HANDOFF.md`).
7. **Changing the script later:** edit, save, then **Deploy > Manage deployments > Edit > Version: New version > Deploy**. The URL stays the same.
8. Notifications go to the account that deployed it (or set `SETTINGS.NOTIFY_TO` in `Code.gs`). Google's limit is 100 email recipients a day on a personal account and 1,500 on Workspace. The script also caps itself at 30 accepted submissions per 10 minutes and ignores the hidden honeypot field.
9. The operations workstream's tracker reads both tabs (column list in `HANDOFF.md`). It may add its own columns after the last contract column; the script finds the next row by `submitted_at` in column A, so formulas filled down those extra columns do no harm. A separate tab is still the tidier place for formulas.
10. **Keep the deletion promise.** The form notices say: "If we do not end up working together, we delete your answers and that email within 12 months." The Sheet is the only full copy of the answers: each notification email carries just the company or brand, the contact email and a link to the row (review round 3). Once, from the editor, run **installRetentionReminder** (approve the extra permission): on the 1st of every month, about 9 am, it runs **markRowsToDelete**, which highlights every row more than 365 days old in both tabs and emails you a list, with a Gmail search for each row's notification (for example `in:anywhere subject:"Office sign-up: SAMPLE Co"`). It deletes nothing. On the first Monday of the month, check each highlighted company in the operations tracker. For offices that never signed and brands that never paid: delete the row, paste its Gmail search into Gmail, delete the notification email it finds, and empty the Trash. Clear the highlight on the rest, and delete the summary email when you are done. You can also run **markRowsToDelete** by hand at any time.
11. **A request to see, correct or delete.** The notices and the privacy page invite this by email. Find the sender's rows with Edit > Find in the Sheet (search their email address). To see: reply with their answers. To correct: edit the cell and reply to confirm. To delete: delete the row, then find the notification email with `in:anywhere subject:"Office sign-up: COMPANY"` or `in:anywhere subject:"Brand application: BRAND"`, delete it, empty the Trash, and reply to confirm that both are gone. If the operations tracker copied anything from the row, remove it there too.

## 4. Staging and hosting **[FOUNDER LOGIN]**

**Until you are ready to follow these steps, the local preview is the only staging.** There is no staging URL yet. To look at the site on your own computer, from `website/`: `python3 -m http.server 8000 --directory site`, then open http://localhost:8000. Outreach uses the one-page PDFs, not a link, so nothing waits on this section.

Why the order below matters: the **first** upload to a new Cloudflare Pages project goes to its **production** environment, at `PROJECT.pages.dev`, and that address is public. Cloudflare Access locks preview deployments only, "and not your *.pages.dev domain or custom domain" (Cloudflare docs, opened 2026-10-24). So the real site goes only into a locked preview, and production holds a blank placeholder until launch.

1. **Name the project neutrally.** Dashboard > Workers & Pages > Create application > Pages > Upload assets (drag and drop). Project name: `site-` plus four random letters (for example `site-qmzv`), never the working name. The name becomes the public address `PROJECT.pages.dev`.
2. **First upload, production: the placeholder.** Drop the folder `tools/production/placeholder/` (one page that says "Nothing here yet", with a noindex tag and an `X-Robots-Tag: noindex` header, and no name) > Deploy.
3. **Lock the previews.** In the project: Settings > General > **Enable access policy**. Preview deployments then open only for your Cloudflare account (Cloudflare Access). Whether Access stays free on your account was not shown on Cloudflare's pricing page: unverified, founder to confirm before you turn it on. **If it is not free, stop here:** keep the local preview and do not upload `site/`.
4. **Upload the site to a preview.** Create a new deployment > choose **Preview** > branch `staging` > drop the `site/` folder > Deploy. Preview URLs also get `X-Robots-Tag: noindex` automatically. Drag-and-drop takes up to 1,000 files of 25 MiB each; the site is about 25 files.
5. **Check the lock before you share anything.** Open the deployment's own link (random characters, like `1a2b3c4d.PROJECT.pages.dev`) in a private window: it must ask for a Cloudflare login. Do the same for the branch link `staging.PROJECT.pages.dev`; Cloudflare's note names "randomly generated preview links", so whether the branch link is covered is unverified (founder to confirm by this test). Share only a link that asked for the login, and only with people on your Cloudflare account.
6. Each later preview: Create a new deployment > Preview > branch `staging` > drop `site/` again. Production keeps the placeholder until section 10.

- **How staging stays out of search:** while `STAGING` is true, every page carries `<meta name="robots" content="noindex, nofollow">` in its HTML (so it holds without JavaScript), `_headers` sends `X-Robots-Tag: noindex`, and `robots.txt` **allows** crawling. That last part is deliberate: Google says a page blocked by robots.txt cannot show it the noindex, and could then appear as a bare link. Still, do not post or share staging links.

## 5. Editing copy

1. Open the page in any text editor: `site/index.html` (home), `brands.html`, `offices.html`, `privacy.html`, `survey-privacy.html`. Find the sentence, change it, save.
2. Name, tagline, contact details and the "Where things stand" line are in `site/site.config.js`, not the pages.
3. Optional checks: `python3 tests/check_site.py` (claims, prices, links), then `python3 tools/export_copy.py` to refresh `COPY.md`.
4. For a preview, upload `site/` again; for production, run `python3 tools/make_production.py` and upload `publish/` (section 10). If you change a price or term, change it in the same words in the brand agreement (`desk-drop-legal-pack/10-…`) and the identity workstream's `system/dd-offer.js`.
5. The store list and map come from the cluster workstream: run `python3 tools/build_map.py` after it updates `map-public.geojson`.

## 6. The shelf photo

The brand page has a labeled slot for one photo: a printed test card on a real pantry shelf, no people in frame (the only product image the plan allows). Take it after the first test print, save it as `site/assets/img/shelf.webp` (about 1200 px wide, under 120 KB), and replace the `<p class="slot staging-only">` line in `brands.html` with `<img src="assets/img/shelf.webp" width="1200" height="900" loading="lazy" alt="A printed display card in front of sealed snacks on an office pantry shelf">`. Until then the slot shows only in staging.

## 7. Renaming

Change `BRAND_NAME` in `site/site.config.js`. That is the whole site: every page, title and notice reads it from there (`tests/e2e.js` proves it). For production, run `python3 tools/make_production.py` again afterwards (you do that at every publish anyway): it writes the new name into the HTML of the upload copy, for link previews and visitors without JavaScript. The Apps Script and the favicon contain no name. Then, outside the site: the domain, the email address, and the identity workstream's wordmark (`desk-drop-identity/brand.json`, then its `node render/build-brand.js`).

The publish preflight checks the rename (review round 3): it blocks unless `BRAND_NAME` is the same, character for character, in `site/site.config.js` and in `desk-drop-identity/brand.json`, and unless the legal pack's log clears that exact name (section 10). So if the legal pack clears a fallback name and you forget this section, nothing can be published under the old name.

## 8. Retiring the founding tier

After the third founding brand: set `FOUNDING_TIER_OPEN: false` in `site/site.config.js`. The $600 card, every "founding price" line and the founding FAQ answer disappear; standard and extra office stay. Check 4 and form question 4 switch from 275 to 550 units, and check 6 and question 6 from "approve $600" to "approve $1,500", by themselves. Those rows arrive with `form_version` `brand-2.0` (the column names `q4_can_ship_275_in_10bd` and `q6_contact_can_approve_600` stay, so the sheet does not change; the operations workstream knows, `HANDOFF.md`). Then run `python3 tools/make_production.py` and upload `publish/` again: the production copy deletes the founding text from the HTML itself, so visitors without JavaScript, link previews and anything reading the raw page see only the standard offer.

## 9. Visit counts **[FOUNDER LOGIN]**

1. Sign up at goatcounter.com with a code (for example the new name). Your dashboard is `https://CODE.goatcounter.com`.
2. Set `ANALYTICS.ENDPOINT: "https://CODE.goatcounter.com/count"` in `site.config.js`.
3. **Verify with a real visit (after publish):** open the live site in a normal browser with Do Not Track and Global Privacy Control off (some browsers, such as Brave, send Global Privacy Control by default, and the site then does not count you). Within a few minutes the dashboard should show the page. Start and send a SAMPLE form: the events `office-intake-started` and `office-intake-sent` appear. Delete the SAMPLE row from the Sheet.
4. Reading it: pages appear as `/`, `/brands`, `/offices`; events as `office-intake-started`, `office-intake-sent`, `brand-intake-started`, `brand-intake-sent`. Started against sent shows where people give up. The Sheet, not the counter, is the record of submissions. Automated visits (tests, Lighthouse) are flagged as bots and not counted.

## 10. Publish (only when all of these are true)

Name cleared or replaced (section 7), with the legal pack's log carrying the line `Public launch (C): CLEARED YYYY-MM-DD for "NAME"` exactly, with nothing else on that line, where NAME is `BRAND_NAME` in straight double quotes (for example `Public launch (C): CLEARED 2026-11-18 for "Pantry Relay"`) and the date is today or earlier; attorney has cleared the form notices, both privacy pages, **and the brand campaign agreement (G 10) and office participation agreement (G 03), whose terms the brand page repeats** (the preflight checks that their draft headings are gone); Gate 1 reached (plan); domain bought. If the attorney changed a term in G 10 or G 03, change the same words on the brand page first (`COPY.md` ledger).

1. **DNS [FOUNDER LOGIN].** Recommended: add the domain to Cloudflare (Free plan) and switch the registrar's nameservers to the two Cloudflare gives you; then in Pages > your project > Custom domains, add `DOMAIN` and `www.DOMAIN`. Alternative without moving nameservers: use `www.DOMAIN` only, add it in Pages first, then create a CNAME `www` → `PROJECT.pages.dev` at your registrar (adding the CNAME before the Pages step gives a 522 error). Keep your email's MX records when moving DNS.
2. In `site/site.config.js`: fill `DOMAIN`, `CONTACT_EMAIL`, `PHONE` (or `""` to show no phone), `POSTAL_ADDRESS`, `FOUNDER_NAME`, `FOUNDER_LINKEDIN` (or `""`), `COMPANY_LEGAL_NAME`, `FORM_ENDPOINT` and `ANALYTICS.ENDPOINT`. Rewrite `ROSTER_STATUS` so it is true today (for example "Five founding offices are signed. No campaign has run yet, so there are no results to show.") and set `ROSTER_STATUS_DATE` to today. Leave `STAGING: true`: the production copy sets it.
3. In the pages: fill `[DATE]` in `privacy.html` and `survey-privacy.html`, and replace the survey notice's `[BRAND]` and `[BRAND PRIVACY POLICY URL]` slots with the legal pack's generic wording once it gives one (`HANDOFF.md`, question to G). Remove each "Draft for attorney review" line only once the attorney has cleared that text.
4. Run `python3 tools/preflight.py`. Fix every `BLOCK` line except the last one ("no production copy yet").
5. Run `python3 tools/make_production.py`. It runs the same checks, refuses to write anything while one blocks, then writes `publish/` and checks it. `site/` is not changed.
6. Upload the **`publish/`** folder (not `site/`) to the **production** environment of the Cloudflare Pages project: Create a new deployment > **Production** > drop `publish/`. It replaces the placeholder at `PROJECT.pages.dev` and goes live on your domain.
7. Check: `curl -I https://DOMAIN` shows no `x-robots-tag`; `https://DOMAIN/robots.txt` says `Allow: /` and names the sitemap; paste `https://DOMAIN/brands` into a Slack or LinkedIn message and see the name in the preview; open `https://DOMAIN/brands/x` and see a styled "Page not found"; do the real-visit check (section 9) and one SAMPLE submission per form (section 3, step 6).
8. Send the outreach workstream the live URL and deep links (`HANDOFF.md`).

Every later change: edit `site/`, run `tools/make_production.py` again, upload `publish/` again.

## 11. Running the tests

`bash tests/run_all.sh` from `website/` (needs `npm install` once in `tests/`; about 10 minutes). What each test proves: `QA.md` and `tests/README.md`.

## 12. Sources (opened 2026-10-24)

- Google Apps Script, web apps: https://developers.google.com/apps-script/guides/web (doPost, deploy steps, "Execute as me", reserved parameter names `c` and `sid`); deployments: https://developers.google.com/apps-script/concepts/deployments (new version, same URL); Content service redirects: https://developers.google.com/apps-script/guides/content; quotas: https://developers.google.com/apps-script/guides/services/quotas (email recipients 100 a day personal, 1,500 Workspace).
- Reading the script's JSON reply from a web page: the community pattern in https://raw.githubusercontent.com/jamiewilson/form-to-google-sheets/master/README.md (`fetch(...).then(response => response.json())`). Not Google documentation: verified only by the section 3, step 6 test.
- GoatCounter: https://www.goatcounter.com/ (free for "personal website or small-to-medium business"; no unique identifiers; "doesn't need a GDPR notice" in its own words), https://www.goatcounter.com/help/pixel (`/count` parameters `p`, `t`, `r`, `e`, `s`, `b`, `rnd`; building your own integration "should be safe"), https://www.goatcounter.com/help/events, https://www.goatcounter.com/help/sessions (IP and User-Agent never stored), https://www.goatcounter.com/help/gdpr.
- Cloudflare Pages: direct upload https://developers.cloudflare.com/pages/get-started/direct-upload/ (re-opened 2026-10-24 in review round 2: the first deployment "and all subsequent deployments" go to production; "choose whether your new deployment will be made to your production or preview environment"); preview noindex and "Enable access policy" for previews https://developers.cloudflare.com/pages/configuration/preview-deployments/ (re-opened 2026-10-24 in review round 1); `.html` redirected to extension-less URLs and the nested 404 lookup ("ending in /404.html") https://developers.cloudflare.com/pages/configuration/serving-pages/ (opened 2026-10-24 in review round 1); Zero Trust plans https://www.cloudflare.com/plans/zero-trust-services/ (opened 2026-10-24; the Access price did not render as text: unverified); custom domains https://developers.cloudflare.com/pages/configuration/custom-domains/; `_headers` https://developers.cloudflare.com/pages/configuration/headers/; Free plan limits https://developers.cloudflare.com/pages/platform/limits/. The pricing page (https://www.cloudflare.com/plans/developer-platform/) did not render as text: Free plan cost unverified, founder to confirm at sign-up.
- Google Search, noindex and robots.txt: https://developers.google.com/search/docs/crawling-indexing/block-indexing ("For the noindex rule to be effective, the page or resource must not be blocked by a robots.txt file"; why staging robots.txt now allows crawling); JavaScript-added robots meta: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics.
