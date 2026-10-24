# Handoff: workstream D (identity and collateral)

Status 2026-10-24: part 1 done (identity system, tent card, case label, specs, tests). Part 2 (documents, signature, avatar) will extend this file. Paths are relative to `desk-drop/`.

## What D consumes

| From | File | What D uses | Status |
| --- | --- | --- | --- |
| Plan | `plan.md`, appendix G (display card copy), Phase 3 per-stop procedure and kit list | Card elements, placement standard, photo standard, case label contents | Used |
| G, legal | `desk-drop-legal-pack/name-check-log.md` | Print-run gate. On 2026-10-23 it says HOLD and recommends choosing a fallback name | Read; D prints nothing commercially. Rename is one edit (below) |
| G, legal | email footer (`desk-drop-legal-pack/10-email-footer-and-checklist.md`) | For the email signature | Part 2 |
| B, cluster map | `cluster-1-flatiron/` retailer map | The proposal's retailer-map slot | Part 2 |
| C, website | a provisional design system, if C attaches one | Audit, then adopt or replace | No `website/` folder existed on 2026-10-24, so there was nothing to audit. D's system stands; C should import it |
| E, outreach to F | `desk-drop-outreach/handoff/paid_brands.csv`, `signed_offices.csv` (CONTRACTS 6.4) | Card and label fields (mapping below) | Not built yet; D's templates take JSON in the shape below |

## What D feeds

### To C (website)

| File | Contents |
| --- | --- |
| `desk-drop-identity/tokens/tokens.css` | CSS custom properties: colors (`--dd-ink`, `--dd-cobalt`, ...), type families and weights, type scale, spacing `--dd-space-0..9`, radii, rules, dark-mode overrides, and `.dd-brand-name` (the one text style for the name). The file's header carries the Google Fonts `<link>` for both families. Import it directly |
| `desk-drop-identity/tokens/tokens.json` | The same tokens as JSON (W3C design-token style `$value`/`$type`, plus the CSS variable name for each) |
| `desk-drop-identity/wordmark/wordmark-light.svg`, `wordmark-dark.svg` | The wordmark, outlined (no font needed). Also mono, stacked and symbol versions, and PNGs in `wordmark/png/` |
| `desk-drop-identity/wordmark/symbol-light.svg` | The name-independent symbol (favicon, avatar base). The avatar PNG comes in part 2 |
| `desk-drop-identity/brand.json` | `BRAND_NAME` and `TAGLINE`. C keeps its own `BRAND_NAME`, but should match this value |
| `desk-drop-identity/SYSTEM.md` | Usage rules (color roles, type roles, clear space, minimum sizes, print versus screen) |

### To F (operations), the templates F fills programmatically

| Template | Field list | Command |
| --- | --- | --- |
| Tent card `desk-drop-identity/templates/tent-card/tent-card.html` | `templates/tent-card/FIELDS.md` | `node render/render.js tent-card cards.json cards.pdf --final [--json]` |
| Case label `desk-drop-identity/templates/case-label/case-label.html` | `templates/case-label/FIELDS.md` | `node render/render.js case-label labels.json labels.pdf --final [--json]` |
| One-page report | part 2 | part 2 |

Run commands from `desk-drop-identity/`. Input: one JSON object or an array (one card per office; two labels per sheet). Exit codes: 0 written, 1 usage or crash, 2 template error (no PDF), 3 `--final` found placeholders or SAMPLE values. `--json` prints `{ ready, errors[], warnings[], sample, placeholders[], fit[], console_errors[], template, records }`.

**Tent card field mapping** (JSON key: source column)

| JSON key | Source |
| --- | --- |
| `brand_name` | `paid_brands.brand_name` |
| `product_name` | `paid_brands.product_sku` |
| `card_sentences` | `paid_brands.card_sentences` |
| `allergen_source` | **new**: `contains_statement` (default), `ingredient_list` or `none_on_label`, set by reading the package |
| `allergen_line_verbatim` | `paid_brands.allergen_line_verbatim` |
| `may_contain_verbatim` | **new**: the package's "may contain" line, verbatim (or append it to `allergen_line_verbatim` after a `\n`) |
| `retailer_line` | `paid_brands.retailer_line` (form "Retailer Name, 123 Street Name") |
| `discount_code` | `paid_brands.discount_code` |
| `code_site` | **derived**: `brand_intake.online_store_url` without `https://` |
| `qr_url` | **F generates**: one short link per office per campaign (scans attributable by office) |
| `qr_display` | optional, F |
| `office_id` | `signed_offices.office_id` |
| `campaign_id` | `campaign_actuals.campaign_id` |

**Case label field mapping**: `office_name` from `signed_offices.company`; `office_address`, `floor_suite`; `deliver_to` from `pantry_owner_name`; `brand_name`; `product_name` from `product_sku`; `units_in_case` (F's packed count); `case_number`, `case_total`; `drop_date`, `office_id`, `campaign_id`, `drop_id`; `phone` (empty uses `brand.json`).

**Operations notes for F**
- Verify `allergen_line_verbatim` against the physical package at receiving (T minus 5), not only against the brand's allergen sheet. The Chrome panel asks for this tick before printing; the command line cannot, so F's kitting checklist should.
- A warning containing "left off" or "other face" means the card changed shape; show it to the founder.
- `units_in_case` is the count packed, which feeds `units_delivered` on the ladder.

### To E (outreach)

Part 2: discovery one-pager, office and brand one-pagers, proposal, email signature.

## Deviations from CONTRACTS

1. Adds three tent-card inputs not in CONTRACTS 6.4: `allergen_source`, `may_contain_verbatim` (both new columns F would add next to `allergen_line_verbatim`; producers may add columns) and `code_site` (derived from `brand_intake.online_store_url`). Without them the template still works: `allergen_source` defaults to `contains_statement`, and the other two may be empty.
2. Placeholders recognized by the templates include bracketed slots with lowercase text after a colon, such as `[DROP DATE: Tue 2027-01-12]`, as CONTRACTS section 3 requires for dates in copy.
3. No other deviations. Folder, README, REPORT, HANDOFF, SAMPLE marking, placeholders, ladder words and `BRAND_NAME` follow CONTRACTS.
