**Draft for attorney review. Not legal advice.** (The form's short notice repeats the website's notice; clear both at the attorney hour.)

# Brand qualification (founder copy)

The founder-side copy of the website's brand application: the seven qualification checks, the same CONTRACTS 6.3 columns (`brand_intake`). Use it before the website is public or during a qualifying call. The seven checks are what the brand says; the tracker's `brands` tab marks `qualified` only when all seven are a plain yes and the product is not excluded, and you still check the certificate (legal pack file 11) and the retailer evidence yourself.

Built from `spec/forms.json` by `tools/make_forms_docs.py`. Change the spec, not this page, and rebuild the tracker so its mapping formulas follow.

## Build it once [FOUNDER LOGIN: Google]

1. forms.google.com, Blank form. Drive file name: `Brand qualification (founder copy)` (no company name in a file name).
2. Title: `Brand application: the seven checks`. Description: *About two minutes. Business details only. What this form collects, and why: your contact details and your product's fit, so we can tell you quickly whether a campaign fits. If we do not end up working together, we delete your answers within 12 months. Draft for attorney review. Not legal advice.*
3. Settings > Responses: **Restrict to users in [your domain] and its trusted organizations: OFF.** A Google Workspace form is restricted to your own organization by default, so with this on, an office manager or brand from another company meets a Google sign-in and cannot answer (Google Workspace help, support.google.com/a/users/answer/9303071, opened 2026-10-24: "By default, access is restricted to people inside your organization"). Collect email addresses: **Do not collect** (the form asks for a work email as a question instead); Limit to 1 response: off; Allow response editing: off. Presentation: View results summary: off.
4. Add the questions below, in this order. Google writes them in this column order on the response tab, and the tracker reads them by position.
5. Responses > Link to Sheets > Select existing spreadsheet > the tracker. Google adds a new tab. **Delete the tracker's placeholder tab `brand_form` and rename Google's new tab to exactly `brand_form`.** The tab `brand_intake_founder` then shows each answer in CONTRACTS 6.3 columns, with `source = founder` and `form_version = brand-gform-1.0`.
6. **Test it as an outsider:** open the form's Send link in a private or incognito window, or on a phone signed out of Google. It must open with no sign-in. Signed in to your own Workspace account, the test passes even when outsiders are blocked.
7. Send the form's link to a brand after a first conversation, or fill it in yourself during the qualifying call.

## Questions

| Col | Question | Type | Required | Options | Writes column |
| --- | --- | --- | --- | --- | --- |
| B | Brand name | Short answer | Yes |  | `brand_name` |
| C | Brand website | Short answer | Yes |  | `website` |
| D | Product for the campaign · help: *One SKU, or two flavors treated as one. Include the pack size.* | Short answer | Yes |  | `product_sku` |
| E | Category | Dropdown | Yes | Chips and crisps; Popcorn and puffs; Crackers and pretzels; Bars; Cookies and baked snacks; Chocolate and candy; Nuts, seeds and trail mix; Jerky and meat sticks, shelf-stable only; Dried fruit and fruit snacks; Sparkling water and soda; Tea, juice and other non-carbonated drinks, shelf-stable; Ready-to-drink coffee, shelf-stable; Another kind of snack; Another kind of drink | `category` |
| F | Where is the brand based? | Short answer | Yes |  | `hq_city` |
| G | Your name | Short answer | Yes |  | `contact_name` |
| H | Your title | Short answer | Yes |  | `contact_title` |
| I | Work email | Short answer | Yes |  | `contact_email` |
| J | Work phone (optional) | Short answer | No |  | `contact_phone` |
| K | Who signs off on the budget? | Multiple choice | Yes | I do (writes `Y`); Someone else (writes `N`) | `budget_approver_is_contact` |
| L | Their name and title (only if someone else) | Short answer | No |  | `budget_approver_name_title` |
| M | New York stores that carry you (optional) · help: *Store name and street, one per line.* | Paragraph | No |  | `nyc_retailers` |
| N | Online store (optional) | Short answer | No |  | `online_store_url` |
| O | Can you issue a discount code for the campaign? | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`) | `can_issue_discount_code` |
| P | When would you want a campaign? | Multiple choice | Yes | Next available drop; In 1 to 3 months; In 3 to 6 months; Just exploring | `preferred_timing` |
| Q | 1. Individually packaged, sealed and shelf-stable, with 60 or more days of shelf life left at delivery? | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q1_sealed_shelf_stable_60d` |
| R | 2. Labeled with ingredients and the nine major allergens? | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q2_labeled_ingredients_allergens` |
| S | 3. Sold in a store inside or within ten blocks of the cluster, or online with a discount code? | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q3_buy_path_near_cluster` |
| T | 4. Able to ship 275 units to one Manhattan address within ten business days? · once the founding tier closes: *4. Able to ship 550 units to one Manhattan address within ten business days?* | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q4_can_ship_275_in_10bd` |
| U | 5. Covered by product liability insurance? | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q5_product_liability_insurance` |
| V | 6. Can you approve $600 on your own, without a committee? · once the founding tier closes: *6. Can you approve $1,500 on your own, without a committee?* | Multiple choice | Yes | Yes (writes `Y`); No (writes `N`); Not sure (writes `unsure`) | `q6_contact_can_approve_600` |
| W | 7. Why New York, and why now? | Paragraph | Yes |  | `q7_why_now` |
| X | Not an excluded product | Checkboxes | Yes | My product is none of these: alcohol; cannabis, CBD or THC; a dietary supplement; refrigerated or perishable; needs preparation; makes health claims. (writes `Y`) | `excluded_category_confirmed` |
| Y | Notes (optional) | Paragraph | No |  | `notes` |

Column A is Google's Timestamp; it becomes `submitted_at` (text, `YYYY-MM-DDTHH:MM:SS`), the key you copy into the tracker.

## Notes

- Checks 4 and 6 change wording when the founding tier closes (after the third founding brand): edit those two questions and set `brand_form_version` on the tracker's config tab to `brand-gform-2.0`. The column names stay `q4_can_ship_275_in_10bd` and `q6_contact_can_approve_600`, exactly as on the website (website/HANDOFF.md).
- Website and online store addresses get `https://` added when missing, as on the website.
- "Not an excluded product" is one required checkbox; ticking it writes `excluded_category_confirmed = Y`.
- Nutrient wording such as "10g protein" is allowed but you review it; structure or function wording such as "supports gut health" is a health claim and the brand is excluded (CONTRACTS section 4).
