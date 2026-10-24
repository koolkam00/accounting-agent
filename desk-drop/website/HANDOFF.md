# Handoff: workstream C (website)

Version 1.1 · 2026-10-24 (review round 1) · folder `website/`. Paths are relative to `desk-drop/`. Deviations from CONTRACTS are marked **Deviation**.

## What C consumes

| From | File | How C uses it | Status |
| --- | --- | --- | --- |
| D, identity | `desk-drop-identity/tokens/tokens.css` | Copied unchanged to `website/site/assets/css/tokens.css` (the site must work from a subfolder, so it cannot link across folders). `tools/sync_tokens.py` re-copies it; `tests/check_site.py` fails if the copy drifts | Used |
| D | Symbol (`wordmark/symbol-*.svg` geometry), avatar (`avatar/avatar-cobalt.svg`, `avatar-cobalt-1024.png`) | Header symbol drawn inline from the symbol's two shapes (colors from tokens, so it follows dark mode); favicon and Apple touch icon from the cobalt avatar | Used |
| D | Wordmark SVGs | **Deviation (rename rule):** not used. They have the name baked in as outlines, which would make a rename two edits. The header sets the name in Bricolage Grotesque with D's `.dd-brand-name` class beside the symbol, which `SYSTEM.md` section 3 allows ("wherever the name is typeset instead of shown as the wordmark image, use this class") | By design |
| D | Fonts | The same two families, self-hosted as the unmodified latin files Google Fonts serves (Atkinson Hyperlegible Next variable 400 to 700; Bricolage Grotesque at opsz 96, weight 800), OFL files alongside. No request to Google | Used |
| B, cluster map | `cluster-1-flatiron/map-public.geojson` (boundary plus stores with `map_number`) | `tools/build_map.py` draws `site/assets/img/cluster-map.svg` (20 KB, no tiles, no API keys) and writes the numbered store list as real text into `brands.html` and the map into `offices.html`. Store numbers are B's `map_number`, so the site, B's `public-map.svg` and D's proposal agree | Used. **Changed during review round 1:** B's file went from 16 stores to 14 on 2026-10-24 (Merci Market Union Square and Wholesome Organic Market are no longer in it; numbers 8 to 14 shifted). The site follows B's file as of its last `build_map.py` run; re-run it when B is final, and D should check its proposal's store numbers against B |
| B | `_work/geo/streets_raw.geojson`, `parks_raw.geojson`, `grid_model.json` (NYC CSCL streets, NYC Parks, B's grid rotation) | Basemap streets, parks and the avenue-up rotation. Optional: the map still builds without them | Used |
| B | `public-map.svg`, `public-map.png` | Not used on the site: 159 KB with embedded fonts, and its store list is part of the image, not text a phone can enlarge | Not used |
| G, legal | `name-check-log.md` | Gate: **HOLD** for a public launch. Since review round 1 the gate **fails closed**: `tools/preflight.py` and `tools/make_production.py` block unless the file contains the line `Public launch (C): CLEARED YYYY-MM-DD` (and no HOLD for the public launch). **Request to G:** write exactly that line when the name decision clears the launch | Enforced |
| G | `13-survey-privacy-notice.md` Part C (**v0.6**) | Hosted word for word at `site/survey-privacy.html` (checked by `tests/check_site.py`, which failed until this round: the site had v0.5). The company name, `[EMAIL]` and `[POSTAL ADDRESS]` slots are filled from `site.config.js`; `[DATE]`, `[BRAND]` and `[BRAND PRIVACY POLICY URL]` stay highlighted, and the preflight blocks publishing while they remain. Its URL is G's `[PRIVACY URL]`: `https://[DOMAIN]/survey-privacy` | Used |
| G | `10-brand-campaign-agreement.md` (**v0.8**), `03-office-participation-agreement.md` | Site terms match: founding lock at $120 per office for up to 10 offices (any more at $150), the founding honest-statement and case-study term and the "founding brand at a founding price" disclosure, placement confirmation by T+1, the per-office refund, cancellation by email until the drop day (before T−10 full refund less $100, then 50%, from the drop day the full price is due), first three drops need the office's yes | Used; see `COPY.md` claims ledger. G's `_work/check_pack.py` reports 0 warnings about other folders after this round (run 2026-10-24) |
| G | `02-email-footer-and-checklist.md` | Not used on the site (it is for email). The site footer shows the founder's name, `[EMAIL]`, `[PHONE]` and `[POSTAL ADDRESS]` from `site.config.js` | n/a |
| H, financial model | none | No input needed | n/a |

## What C feeds

### To F (operations and measurement): the two intake sheets

One Google Sheet, made by `setup()` in `website/apps-script/Code.gs`, with two tabs. **Columns exactly as CONTRACTS 6.3, in order, nothing added:**

- **`office_intake`** (21): `submitted_at`, `form_version`, `company`, `contact_name`, `contact_title`, `contact_email`, `contact_phone`, `office_address`, `floor_suite`, `tuesday_headcount`, `pantry_owner_name`, `pantry_owner_title`, `pantry_owner_is_contact`, `receiving_type`, `receiving_window`, `coi_required`, `survey_channel`, `categories_wanted`, `vetoes`, `notes`, `source`.
- **`brand_intake`** (27): `submitted_at`, `form_version`, `brand_name`, `website`, `contact_name`, `contact_title`, `contact_email`, `contact_phone`, `product_sku`, `category`, `hq_city`, `nyc_retailers`, `online_store_url`, `can_issue_discount_code`, `preferred_timing`, `budget_approver_is_contact`, `budget_approver_name_title`, `q1_sealed_shelf_stable_60d`, `q2_labeled_ingredients_allergens`, `q3_buy_path_near_cluster`, `q4_can_ship_275_in_10bd`, `q5_product_liability_insurance`, `q6_contact_can_approve_600`, `q7_why_now`, `excluded_category_confirmed`, `notes`, `source`.

**Values F can rely on** (enforced by the server, tested in `tests/test_code_gs.js`):

| Column | What the website writes |
| --- | --- |
| `submitted_at` | Server time, ISO 8601 with the New York offset, e.g. `2026-10-24T09:14:08-04:00` (stored as text) |
| `form_version` | `office-1.0`; `brand-1.0` while the founding tier is open, `brand-2.0` once `FOUNDING_TIER_OPEN` is false (from `site.config.js`; raised when a form changes). Anything malformed becomes `office-unknown` / `brand-unknown` |
| `q6_contact_can_approve_600` | **New in review round 1:** in `brand-1.x` rows the question asked about approving $600 (the founding price); in `brand-2.x` rows it asked about $1,500 (the standard price). The column name does not change |
| `source` | Always `website`. F's founder-side copy writes `founder` |
| `tuesday_headcount` | Whole number 1 to 10000, stored as a number |
| `pantry_owner_name`, `pantry_owner_title` | When `pantry_owner_is_contact = Y`, copied from `contact_name` and `contact_title`; when `N`, required |
| `budget_approver_name_title` | When `budget_approver_is_contact = Y`, `contact_name, contact_title`; when `N`, required free text |
| `receiving_type` | `walk-up`, `front desk`, `loading dock`, `other` |
| `receiving_window` | `8 to 10 am`, `9 to 11 am`, `10 am to noon`, or the office's own words |
| `coi_required` | `yes`, `no`, `unsure` · `survey_channel`: `slack`, `email`, `other` |
| `categories_wanted` | Category keys (CONTRACTS section 4), semicolons, in CONTRACTS order. "Any of them" writes all 14 keys |
| `category` | One category key |
| `preferred_timing` | `Next available drop`, `In 1 to 3 months`, `In 3 to 6 months`, `Just exploring` |
| `can_issue_discount_code`, `*_is_contact` | `Y` or `N` · `q1` to `q6`: `Y`, `N` or `unsure` · `excluded_category_confirmed`: always `Y` (the form cannot be sent without it) |
| `website`, `online_store_url` | `https://` added when missing |
| Any text starting with `=`, `+`, `-` or `@` | Stored with a leading apostrophe so Sheets never runs it as a formula (for example a phone `+1 212 ...`) |

Also: one email per accepted row (subject `Office sign-up: {company} ({headcount} on Tuesdays)` or `Brand application: {brand_name} ({category})`, Reply-To the sender); the honeypot and repeated submissions write nothing; the script refuses to write if a tab's header row is changed. F may add columns **after** column 21 or 27 only if `Code.gs` `SCHEMA` gets the same columns (otherwise the header check fails): ask C, or edit `SCHEMA` and re-run `tests/test_code_gs.js`.

### To E (outreach engine)

- **Live URL:** none yet. Until publish, outreach uses the one-pager PDFs and no link (prompt), and footers leave `[WEBSITE]` out (G 02).
- **Deep links once live** (`[DOMAIN]` until chosen; extension-less, because Cloudflare Pages redirects `.html` URLs to these): office form `https://[DOMAIN]/offices#join`; brand form `https://[DOMAIN]/brands#apply`; price `https://[DOMAIN]/brands#price`; report contents `https://[DOMAIN]/brands#report`; measurement ladder `https://[DOMAIN]/brands#ladder`; who runs this `https://[DOMAIN]/brands#who`; store map `https://[DOMAIN]/brands#stores`; who can join (offices) `https://[DOMAIN]/offices#area`. Campaign tags work: add `?utm_source=email&utm_campaign=<name>` before the `#`; they show in the visit counts as campaigns. Link previews (Slack, LinkedIn, iMessage) show the page title with the name, because the production copy has the name written into the HTML.
- **Two-line descriptions:**
  - Brands: "500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report. Founding price $600 for 5 offices, first three brands only; standard $1,500 for 10."
  - Offices: "Vetted emerging snacks and drinks for your office, free, roughly monthly. You pick the categories and can veto anything; we ask for one photo and three questions for your team."

### To D (identity)

- **Bug found in `desk-drop-identity/tokens/tokens.css`:** `--dd-rule` is defined twice in `:root`, first as a color (`var(--dd-ink)`, "Semantic aliases") and later as a width (`2px`, "Rules"). In light mode the later `2px` (line 98) wins, so anything that uses `var(--dd-rule)` as a color gets an invalid value and its border disappears; in dark mode the color (lines 111 and 122) wins and the width is lost. D's own templates never use `var(--dd-rule)`, so only consumers are affected. The site works around it (`--s-rule: var(--dd-text)` in `site.css`). Suggested fix for D: rename the width to `--dd-rule-width` (or the color to `--dd-rule-color`) in both `tokens.css` and `tokens.json`, then C re-runs `tools/sync_tokens.py`.
- No provisional visual system was made: D's tokens were in place, so the site adopts D's system as is.

### To G (legal)

- The site's own notices for review at the attorney hour: the two "What this form collects, and why" notices (`site/offices.html`, `site/brands.html`) and `site/privacy.html`. The 12-month retention default for form answers is this workstream's choice.
- **Question:** `survey-privacy.html` is one page for every campaign, but Part C has per-campaign slots (`[BRAND]`, `[BRAND PRIVACY POLICY URL]`). Recommended default: G rewrites those slots generically ("the brand named on the card" and "the brand's privacy policy, linked from the survey") so one hosted page fits every campaign; until then the page shows the slots highlighted and the publish preflight blocks.
- **Request:** when the name decision clears the public launch, write the line `Public launch (C): CLEARED YYYY-MM-DD` in `name-check-log.md` (and remove the HOLD wording for C). The website's publish tools look for exactly that line; any other wording keeps the gate shut.
- **For the attorney hour, new in review round 1:** the brand page now names the founder ("Who runs this") with email, phone and LinkedIn, and states the founding lock and "we say you were a founding brand at a founding price" from G 10 section 3.

## Deviations from CONTRACTS

1. **Wordmark file not used** (rename rule); the name is typeset with D's class. See D row above.
2. **Report timing in copy:** "within seven business days of the drop" (CONTRACTS section 3, T+7) rather than the prompt's "within seven days".
3. **Tokens bug worked around** locally rather than edited in D's folder (C writes only in `website/`).
4. **Office category labels (CONTRACTS section 4).** The office form shows the contract labels without the "shelf-stable" qualifier: "Jerky and meat sticks" (contract: "…, shelf-stable only"), "Tea, juice and other non-carbonated drinks" and "Ready-to-drink coffee" (contract: "…, shelf-stable"). Every product is shelf-stable by rule, so for an office the qualifier is noise on a phone. The **keys are exact**, so F maps by key. `other-snack` and `other-drink` have no contract label; the office form says "Other snacks" and "Other drinks". The brand form uses the contract labels word for word.
5. No other deviations: folder, README, REPORT (returned to the orchestrator as text), HANDOFF, placeholders, ladder words, SAMPLE data and `BRAND_NAME` follow CONTRACTS.
