# Office one-pager: fields

Template: `templates/office-one-pager/office-one-pager.html` (v1.2, 2026-10-24). One Letter page. Contents from plan.md: the pitch to offices, "What offices get and give", what is never asked, how a drop works from the office's side, the product standard, privacy, the founding-office offer, what they sign.

| Key | Rule |
| --- | --- |
| `prepared_for` | Optional office name, printed "Prepared for ..." in the header. |
| `first_drop` | Required. The specific proposed first-drop week (plan Phase 1, conversion step 2), e.g. `week of Mon 2027-01-11`. Starts as the slot `[FIRST DROP WEEK: week of Mon 2027-01-11]`. |
| `visual` | `card` (default: the drawn display card) or `photo`. |
| `photo`, `photo_caption` | Your own photo of the card on a real pantry shelf, no identifiable people. `[PHOTO]` until attached. Never a stock photo. |
| `headline`, `lead`, `gets`, `gives`, `never`, `steps`, `card_caption`, `product`, `privacy`, `founding`, `sign`, `next` | Copy, editable. One list item per line. `{BRAND_NAME}` prints the name from `brand.json`. `**words**` print bold. Checked for claims words. |

Contacts come from `brand.json` (or `details.html`) and count as placeholders until filled. The contact line moves under "Next step" when it is long. Give-way when full: text 9.5 to 9 pt, the card drawing 2.9 to 2.4 in wide, tighter gaps. Otherwise no PDF. Tested with real-length and long founder details.

v1.2 copy changes (review round 1): the founding list no longer promises "first drop within four weeks of signing", which the campaign calendar cannot keep for offices signed in November (the legal pack's office agreement, file 03, drops it too); it now says the first drop is in the week named above, with a brand the office approved. "What we ask" names the two photos the way the report and file 03 use them: the pantry the day it is placed, the card and product on day 3 or 5.

```bash
node render/render.js office-one-pager data.json out.pdf --final
```
