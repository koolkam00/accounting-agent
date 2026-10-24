# Handoff: workstream C (website)

Version 1.0 · 2026-10-24 · folder `website/`. Paths are relative to `desk-drop/`. Deviations from CONTRACTS are marked **Deviation**.

## What C consumes

| From | File | How C uses it | Status |
| --- | --- | --- | --- |
| D, identity | `desk-drop-identity/tokens/tokens.css` | Copied unchanged to `website/site/assets/css/tokens.css` (the site must work from a subfolder, so it cannot link across folders). `tools/sync_tokens.py` re-copies it; `tests/check_site.py` fails if the copy drifts | Used |
| D | Symbol (`wordmark/symbol-*.svg` geometry), avatar (`avatar/avatar-cobalt.svg`, `avatar-cobalt-1024.png`) | Header symbol drawn inline from the symbol's two shapes (colors from tokens, so it follows dark mode); favicon and Apple touch icon from the cobalt avatar | Used |
| D | Wordmark SVGs | **Deviation (rename rule):** not used. They have the name baked in as outlines, which would make a rename two edits. The header sets the name in Bricolage Grotesque with D's `.dd-brand-name` class beside the symbol, which `SYSTEM.md` section 3 allows ("wherever the name is typeset instead of shown as the wordmark image, use this class") | By design |
| D | Fonts | The same two families, self-hosted as the unmodified latin files Google Fonts serves (Atkinson Hyperlegible Next variable 400 to 700; Bricolage Grotesque at opsz 96, weight 800), OFL files alongside. No request to Google | Used |
| B, cluster map | `cluster-1-flatiron/map-public.geojson` (boundary plus 16 stores with `map_number`) | `tools/build_map.py` draws `site/assets/img/cluster-map.svg` (21 KB, no tiles, no API keys) and writes the numbered store list as real text into `brands.html` and the map into `offices.html`. Store numbers are B's `map_number`, so the site, B's `public-map.svg` and D's proposal agree | Used (data as of 2026-10-24) |
| B | `_work/geo/streets_raw.geojson`, `parks_raw.geojson`, `grid_model.json` (NYC CSCL streets, NYC Parks, B's grid rotation) | Basemap streets, parks and the avenue-up rotation. Optional: the map still builds without them | Used |
| B | `public-map.svg`, `public-map.png` | Not used on the site: 159 KB with embedded fonts, and its store list is part of the image, not text a phone can enlarge | Not used |
| G, legal | `name-check-log.md` | Gate: **HOLD** for a public launch. `tools/preflight.py` blocks publishing while it says HOLD | Enforced |
| G | `13-survey-privacy-notice.md` Part C (v0.5) | Hosted word for word at `site/survey-privacy.html` (checked by `tests/check_site.py`). Its URL is G's `[PRIVACY URL]`: `https://[DOMAIN]/survey-privacy.html` | Used |
| G | `10-brand-campaign-agreement.md` (v0.7), `03-office-participation-agreement.md` | Site terms match: founding lock at $120 per office, the founding honest-statement and case-study term, placement confirmation by T+1, the per-office refund, cancellation before T−10, first three drops need the office's yes | Used; see `COPY.md` claims ledger |
| G | `02-email-footer-and-checklist.md` | Not used on the site (it is for email). The site footer shows `[EMAIL]` and `[POSTAL ADDRESS]` from `site.config.js` | n/a |
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
| `form_version` | `office-1.0` or `brand-1.0` (from `site.config.js`; raised when a form changes). Anything malformed becomes `office-unknown` / `brand-unknown` |
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
- **Deep links once live** (`[DOMAIN]` until chosen): office form `https://[DOMAIN]/offices.html#join`; brand form `https://[DOMAIN]/brands.html#apply`; price `brands.html#price`; report contents `brands.html#report`; measurement ladder `brands.html#ladder`; store map `brands.html#stores`. Campaign tags work: add `?utm_source=email&utm_campaign=<name>` before the `#`; they show in the visit counts as campaigns.
- **Two-line descriptions:**
  - Brands: "500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report. Founding price $600 for 5 offices, first three brands only; standard $1,500 for 10."
  - Offices: "Vetted emerging snacks and drinks for your office, free, roughly monthly. You pick the categories and can veto anything; we ask for one photo and three questions for your team."

### To D (identity)

- **Bug found in `desk-drop-identity/tokens/tokens.css`:** `--dd-rule` is defined twice in `:root`, first as a color (`var(--dd-ink)`, "Semantic aliases") and later as a width (`2px`, "Rules"). In light mode the later `2px` (line 98) wins, so anything that uses `var(--dd-rule)` as a color gets an invalid value and its border disappears; in dark mode the color (lines 111 and 122) wins and the width is lost. D's own templates never use `var(--dd-rule)`, so only consumers are affected. The site works around it (`--s-rule: var(--dd-text)` in `site.css`). Suggested fix for D: rename the width to `--dd-rule-width` (or the color to `--dd-rule-color`) in both `tokens.css` and `tokens.json`, then C re-runs `tools/sync_tokens.py`.
- No provisional visual system was made: D's tokens were in place, so the site adopts D's system as is.

### To G (legal)

- The site's own notices for review at the attorney hour: the two "What this form collects, and why" notices (`site/offices.html`, `site/brands.html`) and `site/privacy.html`. The 12-month retention default for form answers is this workstream's choice.
- **Question:** `survey-privacy.html` is one page for every campaign, but Part C has per-campaign slots (`[BRAND]`, `[BRAND PRIVACY POLICY URL]`). Recommended default: G rewrites those slots generically ("the brand named on the card" and "the brand's privacy policy, linked from the survey") so one hosted page fits every campaign; until then the page shows the slots highlighted.

## Deviations from CONTRACTS

1. **Wordmark file not used** (rename rule); the name is typeset with D's class. See D row above.
2. **Report timing in copy:** "within seven business days of the drop" (CONTRACTS section 3, T+7) rather than the prompt's "within seven days".
3. **Tokens bug worked around** locally rather than edited in D's folder (C writes only in `website/`).
4. No other deviations: folder, README, REPORT (returned to the orchestrator as text), HANDOFF, placeholders, ladder words, SAMPLE data and `BRAND_NAME` follow CONTRACTS.
