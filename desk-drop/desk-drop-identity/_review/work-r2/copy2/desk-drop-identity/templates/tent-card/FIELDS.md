# Tent card: field list and render command

Template: `templates/tent-card/tent-card.html` (v1.2, 2026-10-24). One JSON object = one card (one office). A JSON array = one card per Letter sheet, in order. Both faces of each card carry the same content, except when a long ingredient list needs a face of its own (below). In Chrome, a file with several cards shows a picker to edit any of them, and **Add a card** copies the current one for the next office.

Workstream F (operations) fills this programmatically. The founder can also type into the boxes on screen in Chrome.

## Fields

| Key | Required | Source column (CONTRACTS section 6.4 unless noted) | Rule |
| --- | --- | --- | --- |
| `brand_name` | yes | `paid_brands.brand_name` | As the brand writes it. 24 characters or fewer reads best in the wide photo; the panel warns above 28. Use the short brand name, not the company name. |
| `brand_logo` | no | F: the logo file from the brand (`logo_received_date` in `paid_brands`) | **New in v1.2.** A picture: SVG best, or a PNG at least 300 px tall, transparent or white background. Path relative to the JSON file. A wide logo (2.2 times wider than tall or more) replaces the typed name; a square or stacked logo prints beside the typed name. Shown 0.9 in tall, down to 0.55 in as the first thing that gives way; never wider than the safe area. Empty: the name prints in type. A raster under 300 px tall warns. |
| `product_name` | no | `paid_brands.product_sku` | Flavor or product, for example "Sea Salt Lentil Crisps". 40 characters or fewer. First thing left off if the card is full. |
| `card_sentences` | yes | `paid_brands.card_sentences` | Two sentences: who makes it, why it exists. 200 characters or fewer. No health claims, no "best", no "guaranteed", no sales or lift language. The template warns on common claim words; you still read it. |
| `allergen_source` | no (default `contains_statement`) | new column F adds beside `allergen_line_verbatim` | Where the package declares its allergens. `contains_statement`: a "Contains" line (most packages). `ingredient_list`: no "Contains" line, so the whole ingredient list is copied. `single_ingredient`: no ingredient list at all (one ingredient, such as water or almonds). Decided by reading the package. **`none_on_label` was removed in v1.2 and is refused**: nobody decides by eye that an ingredient list holds none of the nine allergens (whey is milk, semolina is wheat, tahini is sesame). |
| `allergen_line_verbatim` | yes | `paid_brands.allergen_line_verbatim` | **Word for word from the package**, same spelling and capitals. For `contains_statement`, the "Contains" line including the word "Contains". For `ingredient_list`, the whole ingredient list starting with "Ingredients". For `single_ingredient`, the product's name exactly as printed (e.g. "Dry Roasted Almonds"). Never shortened or reworded. Line breaks (`\n`) are kept. |
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

**Long ingredient lists.** With `ingredient_list`, a list too long to share a face with the story and QR at 14 pt (about 50 words in capitals, more in mixed case) gets a face of its own, and that face is the **front**, marked "this side faces the room" beside the card ID: the brand name (43 to 36 pt), the whole list and the "may contain" line at 14 pt, and where to buy. The other face carries the story, "Take one" and the QR, and its panel says: "This package declares its allergens in its ingredient list. The full list, word for word, is on the other side of this card." If the list is still too long, the "Take one" sentence and then the buy line leave the front (both stay on the other face). The status carries a warning and `fit[i].ingredients_on_front_face = true`. A list too long even for a whole face (roughly 80 words in capitals, counting the "may contain" line) blocks the card.

Placeholders: any value written like `[RETAILER, STREET]` or `[DROP DATE: Tue 2027-01-12]` prints with a yellow highlighter so it cannot be missed. SAMPLE values (starting with `SAMPLE`) print a red SAMPLE banner.

## Render command

Run from the `desk-drop-identity` folder:

```bash
node render/render.js tent-card path/to/cards.json out/tent-cards.pdf --final
```

- `--final` refuses to write a PDF if any placeholder or SAMPLE value remains. Use it for every real print.
- `--mode pro` writes the print-shop file (7.25 x 10.25 in page with 0.125 in bleed, no marks). Only after the name is cleared.
- `--face-png proof.png --dpi 150` also saves the front face as an image, for sending a proof to the brand or checking the 120 px test.
- `--json` prints the status as JSON: `{ ready, errors[], warnings[], sample, placeholders[], fit[], console_errors[], template, records }`. `fit[i]` says what gave way on card *i* (`logo`, `logo_in`, `story_pt`, `qr_px`, `name_px`, `name_width`, `name_lines`, `tight`, `find_pt`, `product_dropped`, `story_dropped`, `ingredients_on_front_face`, and for that case `ingredient_face_name_px` and `ingredient_face_gave_way`). Messages start with "Card N: " only when the file holds more than one card.
- Exit codes: `0` written; `1` usage or crash; `2` template errors, nothing written (for example the allergen text cannot fit at 14 pt); `3` `--final` found placeholders or SAMPLE values.

Errors stop the PDF. Warnings do not, but F should surface them to the founder (especially "left off", which means the two sentences or product line did not fit).

## Example batch (one card per office)

```json
[
  { "brand_name": "SAMPLE Brightside", "product_name": "SAMPLE Sea Salt Lentil Crisps",
    "card_sentences": "SAMPLE Two friends in Queens ...", "allergen_source": "contains_statement",
    "allergen_line_verbatim": "SAMPLE Contains: wheat, milk, soy and sesame.",
    "may_contain_verbatim": "SAMPLE May contain peanuts and tree nuts.", "retailer_line": "SAMPLE Retailer, 123 Example Street",
    "discount_code": "SAMPLEDESK15", "code_site": "example.com", "qr_url": "https://example.com/s/SAMPLE-O-001",
    "office_id": "SAMPLE-O-001", "campaign_id": "SAMPLE-CMP-001" }
]
```

Working samples live in `templates/tent-card/samples/`, all marked SAMPLE. `BLANK-placeholders.json` is the empty card.
