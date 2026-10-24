# Case label: field list and render command

Template: `templates/case-label/case-label.html` (v1.0, 2026-10-23). One JSON object = one label. A JSON array prints two labels per US Letter sheet, top then bottom. `{"_skip": true}` leaves a slot blank (to start on the bottom label of a half-used sheet).

## Fields

| Key | Required | Source (CONTRACTS section 6.3 and 6.4) | Rule |
| --- | --- | --- | --- |
| `label_type` | no | | `office` (default) or `reserve`. A reserve label prints RESERVE instead of an office and ignores the office fields. |
| `office_name` | yes for office labels | `signed_offices.company` | The short name people say. Narrows, then shrinks to 26 pt, then wraps. |
| `office_address` | no | `signed_offices.office_address` | Street address. |
| `floor_suite` | no | `signed_offices.floor_suite` | Printed after the address. |
| `deliver_to` | no | `signed_offices.pantry_owner_name` | Printed as "Hand to {name}". Business contact only. |
| `brand_name` | yes | `paid_brands.brand_name` | |
| `product_name` | no | `paid_brands.product_sku` | Include the pack size, for example "Sea Salt Lentil Crisps, 1 oz bags". |
| `units_in_case` | yes | F's kitting count | Whole number: the count you packed into this case. |
| `case_number`, `case_total` | no | F | Printed as "Case 1 of 2". Give both or neither. |
| `drop_date` | yes | `campaign_actuals.drop_date` | `YYYY-MM-DD`. Warns if not a Tuesday or Wednesday. A bracketed slot such as `[DROP DATE: Tue 2027-01-12]` prints highlighted. |
| `office_id` | no | `signed_offices.office_id` | Printed as "Office O-003". |
| `campaign_id` | no | `campaign_actuals.campaign_id` | |
| `drop_id` | no | `campaign_actuals.drop_id` | |
| `phone` | no | | Leave empty to print the `PHONE` value from `brand.json` (now `[PHONE]`). |

Fixed copy on every office label: "Sealed, shelf-stable food. Keep at room temperature. Please hand to the person named above; do not leave it unattended in the lobby." Reserve labels instead say to keep the case clean, dry, off the floor and unopened.

## Render command

```bash
node render/render.js case-label path/to/labels.json out/case-labels.pdf --final
```

Same options, JSON status and exit codes as the tent card (see `templates/tent-card/FIELDS.md`). One office with two cases needs two records, `case_number` 1 and 2.
