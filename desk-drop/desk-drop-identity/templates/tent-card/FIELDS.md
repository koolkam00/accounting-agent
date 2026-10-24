# Tent card: field list and render command

Template: `templates/tent-card/tent-card.html` (v1.0, 2026-10-23). One JSON object = one card (one office). A JSON array = one card per Letter sheet, in order. Both faces of each card carry the same content.

Workstream F (operations) fills this programmatically. The founder can also type into the boxes on screen in Chrome.

## Fields

| Key | Required | Source column (CONTRACTS section 6.4 unless noted) | Rule |
| --- | --- | --- | --- |
| `brand_name` | yes | `paid_brands.brand_name` | As the brand writes it. 24 characters or fewer reads best in the wide photo; the panel warns above 28. Use the short brand name, not the company name. |
| `product_name` | no | `paid_brands.product_sku` | Flavor or product, for example "Sea Salt Lentil Crisps". 40 characters or fewer. First thing left off if the card is full. |
| `card_sentences` | yes | `paid_brands.card_sentences` | Two sentences: who makes it, why it exists. 200 characters or fewer. No health claims, no "best", no "guaranteed", no sales or lift language. The template warns on common claim words; you still read it. |
| `allergen_line_verbatim` | yes | `paid_brands.allergen_line_verbatim` | **Word for word from the package**, including the word "Contains" if the package has it, same spelling and capitals. Never shortened or reworded. If the package has no allergen statement, enter exactly: `No allergen statement on the package.` Line breaks (`\n`) are kept. |
| `may_contain_verbatim` | no | new column F adds next to `allergen_line_verbatim` (or put it in `allergen_line_verbatim` after a `\n`) | The package's "may contain" or shared-facility line, word for word. Empty only if the package has none. |
| `retailer_line` | one of the buy paths | `paid_brands.retailer_line` | Retailer and street, in the form "Retailer Name, 123 Street Name". |
| `discount_code` | with `code_site` | `paid_brands.discount_code` | The campaign code. A code without a site is an error. |
| `code_site` | with `discount_code` | `brand_intake.online_store_url`, shortened | Short form without `https://`, for example `brightside.com`. |
| `qr_url` | yes | F's per-office, per-campaign short link | The QR encodes exactly this string. One unique link per office per campaign so scans are attributable by office. Keep it short (under about 40 characters) so the QR stays coarse and easy to scan. |
| `qr_display` | no | F | Text printed under the QR. Empty prints `qr_url` without `https://`. |
| `office_id` | yes | `signed_offices.office_id` (O-###) | Printed at 7 pt in the corner so cards for different offices never get mixed up while kitting. |
| `campaign_id` | yes | `campaign_actuals.campaign_id` (CMP-###) | Printed beside the office ID. |

The buy-path line is built from whichever halves are filled:

| Filled | Card reads |
| --- | --- |
| retailer, code and site | Find it at {retailer}, or use code **{code}** at {site} |
| retailer only | Find it at {retailer} |
| code and site only | Use code **{code}** at {site} |
| retailer and site, no code | Find it at {retailer}, or online at {site} (warning) |
| site only | Find it online at {site} (warning) |
| nothing | error: the card needs a place to buy |

Placeholders: any value written like `[RETAILER, STREET]` or `[DROP DATE: Tue 2027-01-12]` prints with a yellow highlighter so it cannot be missed. SAMPLE values (starting with `SAMPLE`) print a red SAMPLE banner.

## Render command

Run from the `desk-drop-identity` folder:

```bash
node render/render.js tent-card path/to/cards.json out/tent-cards.pdf --final
```

- `--final` refuses to write a PDF if any placeholder or SAMPLE value remains. Use it for every real print.
- `--mode pro` writes the print-shop file (7.25 x 10.25 in page with 0.125 in bleed, no marks). Only after the name is cleared.
- `--face-png proof.png --dpi 150` also saves the front face as an image, for sending a proof to the brand or checking the 120 px test.
- `--json` prints the status as JSON: `{ ready, errors[], warnings[], sample, placeholders[], fit[], console_errors[], template, records }`. `fit[i]` says what gave way on card *i* (`story_pt`, `qr_px`, `name_px`, `name_width`, `name_lines`, `tight`, `find_pt`, `product_dropped`, `story_dropped`).
- Exit codes: `0` written; `1` usage or crash; `2` template errors, nothing written (for example the allergen text cannot fit at 14 pt); `3` `--final` found placeholders or SAMPLE values.

Errors stop the PDF. Warnings do not, but F should surface them to the founder (especially "left off", which means the two sentences or product line did not fit).

## Example batch (one card per office)

```json
[
  { "brand_name": "SAMPLE Brightside", "product_name": "Sea Salt Lentil Crisps",
    "card_sentences": "SAMPLE Two friends in Queens ...", "allergen_line_verbatim": "Contains: wheat, milk, soy and sesame.",
    "may_contain_verbatim": "May contain peanuts and tree nuts.", "retailer_line": "SAMPLE Retailer, 123 Example Street",
    "discount_code": "SAMPLEDESK15", "code_site": "example.com", "qr_url": "https://example.com/s/SAMPLE-O-001",
    "office_id": "SAMPLE-O-001", "campaign_id": "SAMPLE-CMP-001" }
]
```

Working samples live in `templates/tent-card/samples/`, all marked SAMPLE. `BLANK-placeholders.json` is the empty card.
