# Office one-pager: fields

Template: `templates/office-one-pager/office-one-pager.html` (v1.1, 2026-10-24). One Letter page. Contents from plan.md: the pitch to offices, "What offices get and give", what is never asked, how a drop works from the office's side, the product standard, privacy, the founding-office offer, what they sign.

| Key | Rule |
| --- | --- |
| `prepared_for` | Optional office name, printed "Prepared for ..." in the header. |
| `first_drop` | Required. The specific proposed first-drop week (plan Phase 1, conversion step 2), e.g. `week of Mon 2027-01-11`. Starts as the slot `[FIRST DROP WEEK: week of Mon 2027-01-11]`. |
| `visual` | `card` (default: the drawn display card) or `photo`. |
| `photo`, `photo_caption` | Your own photo of the card on a real pantry shelf, no identifiable people. `[PHOTO]` until attached. Never a stock photo. |
| `headline`, `lead`, `gets`, `gives`, `never`, `steps`, `card_caption`, `product`, `privacy`, `founding`, `sign`, `next` | Copy, editable. One list item per line. `{BRAND_NAME}` prints the name from `brand.json`. `**words**` print bold. Checked for claims words. |

Contacts come from `brand.json` and count as placeholders until filled. Give-way when full: text 9.5 to 9 pt, the card drawing 2.9 to 2.4 in wide. Otherwise no PDF.

```bash
node render/render.js office-one-pager data.json out.pdf --final
```
