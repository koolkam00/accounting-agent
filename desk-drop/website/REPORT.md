The site is built and tested, but not published, so there is no URL to share yet. Every check in the pass bar passes on the final run (`bash tests/run_all.sh`, exit 0, 2026-10-24). The third independent review found 1 major and 9 minor problems. All 10 are fixed and none was rejected. Two were fixed a little differently from the suggestion; the reasons are in `website/_review/round-3.md`, "Builder response". The fixes from the first two reviews (20 and 15 findings) still hold.

Workstream C (Website) · 2026-10-24 · version 1.3 (after review round 3) · folder `desk-drop/website/`

## 1. What shipped

The site is not published, so there are no URLs. Four things keep it private:
- the name is on HOLD (`desk-drop-legal-pack/name-check-log.md`);
- the form notices and both privacy pages are drafts for attorney review;
- so are the legal pack's brand and office agreements;
- the plan keeps the site private until Gate 1.

Publishing is your step; `SETUP.md` section 10 walks through it.

To look at the site now, run `python3 -m http.server 8000 --directory site` from `website/`, then open http://localhost:8000. Until you follow `SETUP.md` section 4, this local preview is the only staging. That section puts a blank placeholder in Cloudflare's public production slot first and the site in a locked preview, because the first upload to a new Pages project is public.

| What | Where |
| --- | --- |
| The website, staging version: 6 pages (home, for brands, for offices, website privacy notice, survey privacy notice, 404), 21 files, 308 KB on disk. It goes only to a locked preview | `website/site/` |
| The one settings file. The name, contact details, form endpoint, founding tier switch and status line all live here, so a rename is one edit | `website/site/site.config.js` |
| The production copy you upload when you publish. `tools/make_production.py` writes it and refuses to build while anything blocks. With the founding tier retired, it deletes the founding text from the HTML itself. Since this round it also deletes every staging-only line and HTML comment, so link previews and scrapers see no staging wording | `website/publish/` (made at publish time; not stored in the repository) |
| The blank placeholder for Cloudflare's production slot until launch ("Nothing here yet", noindex, no name) | `website/tools/production/placeholder/` |
| Publish preflight. Since this round the name gate checks which name was cleared, and when | `website/tools/preflight.py` |
| The form backend, a Google Apps Script. It writes one row and sends one short email per submission, with the CONTRACTS 6.3 columns in exact order. Since this round the email carries only the company or brand, the contact email and a link to the row. A monthly helper keeps the 12-month deletion promise | `website/apps-script/Code.gs`, `appsscript.json` |
| The setup guide: a one-page quick card at the top, with the detail below it. It covers the stack, owning the accounts, the forms (now including a local test and the deletion steps), staging, DNS, editing copy, renaming, retiring the founding tier, analytics and the publish step. Steps that need your login are marked | `website/SETUP.md` |
| The copy deck: a claims ledger with the source of every claim (57 rows), plus every word on every page | `website/COPY.md` |
| The pass bar, the tests and the results | `website/QA.md`, `website/tests/`, `website/tests/out/run_all.log` |
| Handoffs to and from the other workstreams | `website/HANDOFF.md` |
| Your questions, each with a recommended default, and the numbered assumptions | `website/README.md` |
| Screenshots of every page at 390 px and 1280 px, light and dark, plus form states and the founding-tier-off copy without JavaScript | `website/_shots/` |
| The three independent reviews and my response to each | `website/_review/round-1.md`, `round-2.md`, `round-3.md` |

**Audit of an earlier draft:** no earlier draft was attached, so there was nothing to audit.

**Visual system:** I adopted the identity workstream's tokens, fonts, symbol and avatar as delivered, and made no provisional system. The site's copy of the tokens is still identical to the identity workstream's file.

## 2. Pass bar, tests and results

The pass bar was set before the site was built. Review changes are marked in `QA.md`. They do one of three things:
- make a check stricter (P9, P12, P14, P15, P19, P20);
- correct the bar itself (P11, in review round 1);
- add a check the bar missed (P21, this round).

P21 was written after a first measurement; `QA.md` says so.

| # | Check | Result |
| --- | --- | --- |
| P1 | Speed: Lighthouse mobile performance at least 95 | 99 to 100 on all 6 pages, both on the staging site and on the production copy. Mobile LCP (largest contentful paint) 1.65 to 1.96 s, layout shift 0, blocking time 0 to 7 ms. Desktop 100 everywhere |
| P2 | Accessibility score 100 | 100 on all 24 runs |
| P3 | Best Practices at least 95 | 100 on all 24 runs |
| P4 | SEO at least 95 in production; on staging only the deliberate noindex may fail | Production copy: 100 on all 12 runs. Staging: 63 to 66, and the only failing audit is `is-crawlable`, which is the deliberate noindex |
| P5 | WCAG 2.1 AA (axe-core) | 0 violations in 48 runs: 6 pages × 2 sizes × light and dark, plus form states |
| P6 | Page weight under 300 KB | 113 to 173 KB uncompressed (brand page 173 KB). The brand page is about 88 KB gzipped |
| P7 | Keyboard | Tab order follows the page on every page. The skip link comes first, every stop has a visible focus ring, arrow keys work in radio groups, Enter submits, and error links move focus to the field |
| P8 | Labels | 45 controls on the office form and 41 on the brand form: 0 unlabeled, 0 ungrouped, optional fields all marked |
| P9 | Office form in 90 seconds on a phone (both pantry-owner paths, reading the hero and form intro at 250 words a minute, and scrolling) | "Yes, me": 66 typed characters and 12 taps, **80.6 s**. "Someone else": 81 characters and 13 taps, **88.1 s**. Both include 25.7 s of reading and 7 scroll swipes. This round's two new privacy hints made the form 49 px taller and added one swipe (it was 79.1 s and 86.6 s) |
| P10 | Forms end to end | Each submission writes exactly one row with the exact columns and sends exactly one notification. The analytics events arrive. The honeypot (a hidden spam-trap field) and repeated submissions write nothing, and bad values are refused. With the founding tier closed, brand rows arrive marked `brand-2.0`. New: a headcount under 30 or over 250 shows a note under the field without blocking, and both thank-you messages depend on fit |
| P11 | Staging stays out of search | Every page has a noindex tag written into its HTML, the host sends a noindex header, and robots.txt lets crawlers fetch pages so they can see both. The forms send nothing on staging. The production placeholder is noindexed too |
| P12 | `Code.gs` itself | 17 of 17. New in this round: the notification email carries none of 11 office answers or 6 brand answers, only the company or brand, the contact email and the row link. The monthly retention summary gives each row's Gmail search |
| P13 | Rename in one edit | The old name appears nowhere after one change, including in the production copy viewed with JavaScript off |
| P14 | Founding tier retirement | One setting removes it. Checks 4 and 6 then ask about 550 units and $1,500, and the facts row says 10 offices. The same holds in the production copy with JavaScript off, with no `$600`, `$120` or founding text left in its HTML |
| P15 | Claims and links (`check_site.py`) | 86 of 86 (was 64). New in this round: the brand agreement's terms (the photo on the day of placement, card text seen rather than approved, sales tax, the cancel-for-refund exit after repeated moves); the notices naming the short email; the health hints; conditional thank-you messages; no internal note in any page's text; and the store map equal to the cluster workstream's current file |
| P16 | Layout and tap targets | No horizontal scroll at 320, 390, 768 or 1280 px; no tap target under 44 × 44 px |
| P17 | Links and portability | Every link resolves; no external scripts or fonts; the HTML validator finds 0 problems on `site/` and on the production copy |
| P18 | Analytics privacy | No third-party requests, cookies or browser storage |
| P19 | Publish gate (`test_preflight.py`) | 40 of 40 (was 25). The gate opens only on the exact line `Public launch (C): CLEARED YYYY-MM-DD for "NAME"`, and only when NAME equals the site's `BRAND_NAME` and the identity's `brand.json` name, dated today or earlier. New cases keep it shut: the legal pack clears a fallback name while the site still says "Desk Drop"; a date after today; two different names; `brand.json` on another name; the old line without a name; curly quotes; a lowercase name; a builder note in a page's text; a staging bar left in the production copy. The full rename path opens it. The real preflight today: **20 blocking**, all expected |
| P20 | Production copy with JavaScript off | The name, title, link-preview name, contact details and an extension-less canonical link are written into the HTML. There is no noindex tag. The forms cannot be sent, and they say why. A missing page at a nested path shows a styled 404 with working links. New in this round: the raw HTML has no staging bar, photo slot, staging form note, setup-doc pointer or HTML comment |
| P21 | **New in this round.** A brand founder understands the offer, the price and the report in two minutes on a phone | The path: read the hero (156 words), tap "See the price", read the three price cards and the two lines under them, then scroll on and read the report contents. That is 443 words (106.3 s) plus 1 tap and 7 swipes: **118.3 s**, under 120. Scrolling from the top without the jump link, the same reading takes 124.3 s. That figure is recorded but is not the bar (assumption 22) |

**What could not be tested before publishing**, all in `SETUP.md`:
- a real visit showing up in the analytics;
- the real Apps Script deployment, the Sheet and the Gmail notification. This includes whether Sheets keeps the formula-guard apostrophe and whether the Gmail search printed in each notification finds it (section 3, step 6 checks both). Since this round that test can run from the local preview, so it does not wait for a Cloudflare account;
- Cloudflare's own redirect and 404 behavior;
- whether Cloudflare Access is free on your account and covers the branch preview link (section 4, step 5 tests it in a private window).

## 3. Numbered assumptions

These are also listed in `README.md`, which `COPY.md` cites by number.

1. No earlier website draft was attached, so there is no audit.
2. The stack costs $0 a month: static HTML on the Cloudflare Pages Free plan, a Google Apps Script web app writing to one Google Sheet, and GoatCounter for visit counts. Cloudflare's pricing page did not render as text, so the Free plan cost is unverified; founder to confirm.
3. The report is promised "within seven business days of the drop" (CONTRACTS T+7 and the brand agreement's "by T+7"), not the prompt's "within seven days". This is the looser promise (9 to 11 calendar days); founder to confirm (question 7).
4. The identity workstream's system is used as delivered. The name is set in type rather than shown as the wordmark image, so a rename stays one edit.
5. The site stays private until the name is cleared, the attorney has cleared the notices and both agreements, and Gate 1 is reached.
6. One survey privacy page serves every campaign. Its `[BRAND]` and `[BRAND PRIVACY POLICY URL]` slots stay highlighted until the legal pack rewrites them generically, and the preflight blocks publishing while they remain.
7. Visit counts cover page views plus four form events, with no cookies, and respect Do Not Track and Global Privacy Control. A real visit can only be checked after publishing.
8. An office not placed by the day after the drop comes off the invoice or is refunded. This comes from the legal pack's brand agreement (section 8), not the plan; attorney to confirm.
9. Form answers, and the notification email about them, are deleted within 12 months if nothing goes ahead; attorney to confirm. A monthly helper highlights rows over 365 days old and emails you a list, with a Gmail search that finds each row's notification. You delete the ones that never signed or paid, and their emails. Nothing is deleted automatically. Since this round the notification carries only the company or brand and the contact email, so the Sheet is the one full copy.
10. Offices of 40 to 250 people are welcome. Under 30 or over 250 is stated as "can't take you yet". Offices of 30 to 39 are your call, so the form accepts any headcount. Since this round, a number under 30 or over 250 shows a polite note under the field (it never blocks sending), and the thank-you promises the agreement only "if your office fits".
11. Brand check 6 asks about $600 while the founding tier is open and $1,500 after it closes. $1,500 is what the signer approves; $750 is only the first half-payment. The column name stays `q6_contact_can_approve_600`, and `form_version` (`brand-1.0` or `brand-2.0`) shows which amount was asked.
12. You are named on the brand page, above the office form and in every footer. Setting `PHONE` or `FOUNDER_LINKEDIN` to "" hides that line.
13. The status line "No offices are signed yet and no campaign has run" is true on 2026-10-24. The preflight blocks publishing once its date is more than 14 days old.
14. Office category labels drop CONTRACTS' "shelf-stable" qualifier. The keys are exact, and this is listed as a deviation.
15. The map follows the cluster workstream's public map file dated 2026-10-24 04:55 UTC: 14 stores, 4 of them inside the cluster. That workstream was still revising it. Since this round the tests fail whenever its file would give a different map, so a change cannot slip past.
16. No drop dates appear on the site.
17. Production URLs have no `.html` (for example `/brands`), because Cloudflare Pages redirects to those.
18. The office form's "Your title" and "Pantry owner's title" are optional, to keep both paths under 90 seconds. Titles come up on the first call; the brand form still requires the contact's title.
19. Until Cloudflare Access is confirmed free and the lock passes a private-window test, the local preview is the only staging. Cloudflare's production slot holds a nameless, noindexed placeholder until launch.
20. The brand FAQ says a proposal names a drop date "usually three to four weeks out" (plan, "Close and collect"). It is a typical lead time, not a date.
21. Check 4 and question 4 ask about 275 units while the founding tier is open and 550 once it closes. The column stays `q4_can_ship_275_in_10bd`.
22. **New.** The two-minute brand target is measured along the path the page offers: read the hero, tap "See the price", read the cards and the lines under them, then scroll on to the report contents. P9 counts the office page's "Sign up" link the same way. Scrolling from the top without the jump link takes 124.3 s.
23. **New.** The name gate is tied to the name. The legal pack's line must read `Public launch (C): CLEARED YYYY-MM-DD for "NAME"`, where NAME equals `BRAND_NAME` in `site.config.js` and in the identity's `brand.json`, dated today or earlier. This changes the line the website asked the legal pack for in round 1. The legal pack has not written either form yet; its log says HOLD.

## 4. Deviations and conflicts with CONTRACTS

1. The wordmark file is not used; the name is typeset instead (rename rule).
2. The report timing says business days (assumption 3).
3. Retired in review round 2: the identity tokens' rule-color clash was fixed at the source.
4. The office category labels drop the shelf-stable qualifier (assumption 14).
5. Two placeholders are added to CONTRACTS' list: `[LINKEDIN URL]` (your profile) and `[COMPANY NAME]` (the filed legal name, which fills the legal pack's `[COMPANY NAME: …]` slot). The preflight blocks both until they are filled.

There is no new deviation in this round. One cross-workstream request changed: the exact line the website asks the legal pack to write (assumption 23, `HANDOFF.md`).

## 5. Changelog

- **Round 0:** read the brief, plan, CONTRACTS and the cluster map, identity and legal outputs; set the pass bar; researched Apps Script, GoatCounter, Cloudflare Pages and Google's noindex rules.
- **Round 1 (draft):** built six pages, the settings file, the forms, `Code.gs`, the mock form endpoint, the map builder and all test suites; fixed a 413 px phone width and a radio-spacing clash.
- **Round 2 (three readers):** added "where things stand", the cancellation and per-office refund answers, the founding terms and the "vetted" definition; aligned the terms to the legal pack's v0.7 agreements; found the identity tokens' `--dd-rule` collision.
- **Round 3 (taste):** map and report-mock labels; campaign tags; the preflight blocks while any page is still marked as a draft.
- **Review round 1 (2026-10-24):** fixed all 5 majors and 15 minors:
  - survey notice v0.6, the drop-day cancellation cut-off and "Who runs this";
  - office exclusions stated plainly, and a fail-closed preflight;
  - the `publish/` production copy, a crawlable staging robots.txt, and forms that cannot be sent without JavaScript;
  - unit counts, check 6 following the tier, and the founding terms;
  - the report mock and map at phone width, and the docs;
  - new tests P19 and P20.
- **Review round 2 (2026-10-24):** fixed all 3 majors and 12 minors:
  - an exact name-gate line, and placeholder-first staging steps;
  - founder questions with defaults, and the founding tier written into the production HTML;
  - brand promises matched to the agreements, and exact notices;
  - a monthly retention helper, and a gate that waits for both agreements;
  - optional office titles (P9 restated);
  - the report mock, day numbering and FAQ;
  - the next row found by column A, the apostrophe check, and the SETUP quick card.
- **Review round 3 (2026-10-24):** fixed the 1 major and all 9 minors.
  - The name gate now checks which name was cleared, and when. The legal pack's line must name the site's name, and `brand.json` must carry the same name. A future date blocks. If the legal pack clears a fallback and the site is not renamed, nothing can be published under the old name (11 new gate tests).
  - The notification email now carries only the company or brand, the contact email and the row link. The notices and the privacy page promise to delete the answers and that email. SETUP has a Gmail step for the 12-month check and a new step for requests to see, correct or delete.
  - The office form now asks people not to say who has an allergy, or to give anyone's health details. The office notice says the same.
  - The thank-you messages depend on fit, and an out-of-range headcount gets a gentle note under the field. No reply time is promised, because no source sets one.
  - The production copy drops the staging bar, the photo slot, the forms' staging note and every HTML comment. The preflight blocks any internal note in a page's text, and the survey page's builder note is gone.
  - The brand page now repeats the brand agreement v0.8 exactly:
    - the photo is taken on the day of placement;
    - brands "see the card text before it is printed", and we may edit a sentence that makes a health claim;
    - prices exclude sales tax;
    - a full refund if outside events move a drop more than once, or by more than three weeks.
  - New P21 measures the two-minute brand target: 118.3 s.
  - SETUP shows how to test the real forms from the local preview.
  - The store map was rebuilt from the cluster workstream's newest file: stores 2 to 5 are renumbered, and one store is now 3 blocks outside. The tests now fail whenever that file changes.
  - Side effect: P9 re-measured at 80.6 s and 88.1 s, still under 90.

## 6. Blocking questions, each with my recommended default

1. **Domain.** Recommended default: the `.com` of the name chosen at the legal pack's name decision (Wed 2026-11-18, derived, founder to confirm), bought only after it. Until then it stays `[DOMAIN]` everywhere.
2. **Business email address.** Recommended default: one Google Workspace address on that domain (the plan's $7 to $14 a month line), on the Google account that deploys the form script, so the notifications land there. It stays `[EMAIL]` until then.
3. **Postal address shown in every footer.** Recommended default: a USPS post office box or a registered private mailbox, not your home address. Both qualify for email footers under the FTC's CAN-SPAM guide (legal pack, file 02). The cost was not researched (needs a quote). Use the same address on the site, in email and in your signature. It stays `[POSTAL ADDRESS]` until then.
4. **Name.** Recommended default: the legal pack's advice, which is to treat "Desk Drop" as taken and pick a fallback by Wed 2026-11-18 (derived). The site renames in one edit plus the publish build. The publish gate opens only when the legal pack's CLEARED line names the same name as the site and `brand.json`.
5. **Phone shown publicly.** Recommended default: a separate Google Voice number (the plan's $0 phone line), not your personal number. Set `PHONE` to "" to show none.
6. **LinkedIn link.** Recommended default: show it, because offices and brands check who runs a new vendor before they reply. Set `FOUNDER_LINKEDIN` to "" to hide it.
7. **Report promise.** Recommended default: "within seven business days of the drop", matching the brand agreement's T+7, rather than the prompt's "seven days".
8. **Form-answer retention.** Recommended default: 12 months if nothing goes ahead, covering the Sheet row and its notification email, with the monthly highlight. The attorney confirms the period at the attorney hour.
9. **Staging before Gate 1.** Recommended default: local preview only. Use the locked Cloudflare preview only if Access is free on your account and the private-window test asks for a login. The real form test now works from the local preview too.
10. **Survey notice brand slots (for the legal pack).** Recommended default: generic wording, "the brand named on the card" and "the brand's privacy policy, linked from the survey", so one hosted page fits every campaign.
