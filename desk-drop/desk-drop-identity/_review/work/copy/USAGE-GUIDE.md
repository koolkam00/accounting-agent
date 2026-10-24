# Usage guide: making, sending and printing every piece yourself

For the founder, or anyone helping. No design software and no designer needed: you need Google Chrome. The terminal commands are optional and only save time on bigger drops.

Version 1.1, 2026-10-24. Part 1 (tent card, case label, logo, colors) and part 2 (documents, email signature, avatar).

**Name and print gate, from the legal pack's name-check log (v0.5, 2026-10-24):** print run **HOLD**, public launch **HOLD**, private discovery calls **go**. A business already trades as "DeskDrop" and the USPTO has called the words descriptive. The legal pack recommends choosing a fallback name by Fri 2026-11-13 (derived, founder to confirm). Until you decide: home and copy-shop test prints are fine, documents sent one to one in discovery are fine, nothing is ordered from a print shop and no public profile goes up. A rename here is one edit (section 16).

**What "the panel" means.** Every template opens in Chrome with a column of boxes on the left (the panel) and the page on the right. You type in a box and the page changes as you type. Box names in this guide are in bold, exactly as the panel shows them.

---

## 0. Which piece, when

| When (plan) | Piece | File | Section |
| --- | --- | --- | --- |
| Once, before anything goes out | Your contact details | `brand.json` | 7 |
| Once | Email signature | `signature/` | 13 |
| Weeks 1 to 3, discovery | Discovery one-pager | `templates/discovery-one-pager/` | 8 |
| After an office says "send me something" | Office one-pager | `templates/office-one-pager/` | 9 |
| After a brand call or reply | Brand one-pager | `templates/brand-one-pager/` | 10 |
| Within 24 hours of a qualifying brand call | Proposal (with mock report page) | `templates/proposal/` | 11 |
| T minus 3 (three business days before the drop) | Tent cards, case labels | `templates/tent-card/`, `templates/case-label/` | 2 to 5 |
| Drop day and day 3 or 5 | Placement and photos | | 6 |
| By T plus 7 | Report | `templates/report/` | 12 |
| After the name is decided | Avatar on a public profile, print-shop orders | `avatar/`, section 17 | 14, 17 |

---

## 1. Seven rules that matter most

1. **Allergen text is copied word for word from the package.** Same words, same spelling, same order, including "Contains" and the "may contain" line. Read it off the package itself, not from the brand's email. Never shorten it. It prints at 14 pt and nothing can make it smaller.
2. **One card per office, never swapped.** Each office's card has its own QR link and its card ID (for example "Card O-003 · CMP-001") in the bottom corner.
3. **No claims anywhere.** No "healthy", "best", "guaranteed", "boosts", no sales, lift or new-customer promises. The templates warn you when they see these words.
4. **Measurement words stay exact.** Delivered, placed, depleted, responded, scanned, purchased, incremental (not measured). Never "conversions", "ROI", "sales lift" or "acquisition".
5. **Yellow means unfinished.** Anything with a yellow highlighter is a placeholder. Nothing yellow leaves the building.
6. **Red SAMPLE banner means practice.** Anything with it is test material.
7. **Print or save at 100% with "Background graphics" on.** "Fit to page" shrinks everything, including the allergen text.

---

## 2. Make one tent card in Chrome (target: under 10 minutes)

You need: the brand's details (from the paid brand row or their email, so you can copy and paste), **the package itself** (for the allergen text), and this office's QR link and office ID (from the operations tracker).

1. Open the folder `desk-drop-identity/templates/tent-card/` and double-click `tent-card.html`. If it opens in another browser, right-click it and choose Open With > Google Chrome.
2. The card appears on the right with yellow placeholders. Grey text inside an empty box is a hint, not a value.
3. **Brand.** Paste into **Brand name** (the short form, as on the package), **Product (optional)**, and **Two sentences: who makes it and why** (under 200 characters, no claims).
4. **Allergens.** Pick up the package. In **Where the package declares allergens**, choose where the package declares them: a "Contains" statement (most packages), only inside the ingredient list, or nowhere. Then type what is printed into **Allergen statement, exactly as on the package**: the "Contains" line, or the whole ingredient list starting with "Ingredients" if there is no "Contains" line, or nothing if you chose "nowhere". Type the "may contain" or shared-facility line into **"May contain" or facility line, exactly as on the package**. Read your typing back against the package, word by word. Tick the box **I read the allergen text against the package itself, word for word**.
5. **Where to buy.** Fill **Retailer and street** (as "Retailer Name, 123 Street Name"), or **Discount code** and **Site for the code**, or all three. The card writes the sentence for you.
6. **QR and IDs.** Paste this office's link into **QR link for THIS office**, then type **Office ID** and **Campaign ID**. Point your phone camera at the QR on screen: it must open this office's link.
7. Read the status box under the buttons. It must say **Ready to print** and nothing in red. Read every yellow "Check:" note. If it says the two sentences were "left off", shorten them until they come back.
8. Press **Save as JSON** so you can reuse the card (for the next office, press **Load JSON**, change only the QR link and the office ID).
9. Press **Print** and set: Destination your printer, Paper Letter, Scale 100 (or "Actual size"), Margins Default, More settings > **Background graphics** on. Load one sheet of cardstock. Print.

For the next office of the same brand: **Load JSON**, change **QR link for THIS office** and **Office ID**, tick the allergen box again (loading a file always unticks it), check the status box, print. About two minutes each.

If the status box shows anything red, or the card looks wrong, see section 18.

---

## 3. Make every card for a drop at once (optional, terminal)

With 10 offices, the operations workstream writes one JSON file with one card per office. From the `desk-drop-identity` folder:

```bash
node render/render.js tent-card path/to/cards.json cards-for-printing.pdf --final
```

One PDF page per office. `--final` refuses to make the PDF while any placeholder or SAMPLE value is left. Field list: `templates/tent-card/FIELDS.md`. First time only: install Node (nodejs.org, free), then in this folder run `npm install` and `npx playwright install chromium`.

---

## 4. Print, cut and fold the tent card

You need white **matte** cardstock, 80 to 110 lb cover (about 216 to 300 gsm), a ruler, a paper trimmer or craft knife and mat, and a bone folder or the back of a butter knife. Check your printer's maximum paper weight first.

1. Print one test on plain paper. Both faces present, text not cut off, QR crisp.
2. Print on cardstock, one sheet per office plus one spare per office.
3. Cut on the four corner marks. The card is 7 x 10 in flat.
4. Lay the ruler between the two FOLD marks and score the line.
5. Fold with the printed side outside. Press the crease flat.
6. Stand it with the feet about 4 in apart. Both faces read the right way up.
7. Check the card ID against the office on the case label before it goes in the case.

Full spec: `specs/tent-card-spec.pdf`.

---

## 5. Case labels

1. Open `templates/case-label/case-label.html` in Chrome. It shows two labels per sheet.
2. Fill the boxes for the first label. For more labels, edit the JSON list in the file or have the operations workstream write it, then run `node render/render.js case-label labels.json labels.pdf --final`.
3. Write the count you actually packed into **Units in this case**, not the planned count.
4. For your reserve bag, set **Label type: office or reserve** to `reserve`.
5. Print on Avery 5126-size half-sheet labels, or on plain paper cut on the dashed line and taped flat with clear tape on all four edges. Same print settings as the card.

Spec: `specs/case-label-spec.pdf`.

---

## 6. Place it and take the two photos

- At eye level beside the existing snacks, never inside a cabinet. Card in front of the product, allergen panel visible. One display per pantry.
- **Wide photo:** step back until the whole pantry is in the frame, with the card and product in it.
- **Close photo:** card and product from about arm's length; the card should span at least a fifth of the photo's width. Zoom in on your phone and check you can read the allergen panel. If not, step closer and take it again.
- No identifiable people in either photo. These two photos go into the report.

---

## 7. Once, before any document goes out: your details

Every document, label and signature reads your details from one file.

1. Open `brand.json` in any text editor (TextEdit, Notepad).
2. Replace `[FOUNDER NAME]`, `[PHONE]`, `[EMAIL]` and `[POSTAL ADDRESS]` inside the quotes. Keep the quotes. Use a business phone and a postal address you are happy to make public: a USPS post office box or a registered private mailbox both work for commercial email (legal pack file 02).
3. Leave `"WEBSITE": "[WEBSITE]"` until the site is public, then put it in. To leave the website off everything until then, set it to `""`.
4. Save. Then, in the `desk-drop-identity` folder, run `node render/build-brand.js` and `node render/build-signature.js` (or `bash render/build-pdfs.sh` for everything). Without the terminal: ask whoever set up the folder to run it; until then your details stay yellow and `--final` refuses to make documents.

Prices live in one file too: `system/dd-offer.js`. Change a price there and in the campaign agreement, then rebuild.

---

## 8. The discovery one-pager (weeks 1 to 3)

The idea in five sentences, with no selling. Send it before or after a research call.

1. Open `templates/discovery-one-pager/discovery-one-pager.html` in Chrome.
2. The five sentences are already written. Change them only if you need to: **Sentence 1: what it is** to **Sentence 5: why you are writing**. Keep one sentence per box. The page refuses two sentences in a box, and warns if a sentence sounds like selling (a price, "offer", "discount", "founding", "sign up").
3. Press **Print or save as PDF**, choose Destination **Save as PDF**, Paper Letter, Scale 100, Margins Default, Background graphics on. Save it as `discovery.pdf`.

`{BRAND_NAME}` in a box prints the name from `brand.json`, so a rename never needs you to touch the sentences.

---

## 9. The office one-pager (after a discovery yes)

Send it the same day the office manager says "send me something", with a specific first-drop week.

1. Open `templates/office-one-pager/office-one-pager.html` in Chrome.
2. Fill **Proposed first drop** with a real week, for example `week of Mon 2027-01-11`. Drops are Tuesday or Wednesday mornings, never in the last two weeks of December or August or the week of July 4.
3. Optional: **Office name (optional)** prints "Prepared for ..." in the header.
4. Optional: to use your own photo of the card on a real shelf instead of the drawing, set **Picture on the page** to the photo and use **Choose picture** under **Photo (if you chose a real photo)**. No identifiable people, never a stock photo.
5. The rest is the copy, in boxes under "Copy (change only if you need to)". One list item per line. Two stars around words (`**like this**`) make them bold.
6. When the status box says **Ready to print**, press **Print or save as PDF** and save as PDF (same settings as section 8).

If you add text and the page no longer fits, a red "does not fit" bar appears and no PDF will be right. Shorten until it goes.

---

## 10. The brand one-pager

1. Open `templates/brand-one-pager/brand-one-pager.html` in Chrome.
2. Fill **Roster today** with only what is true today, from your signed offices: for example "5 founding offices signed in Flatiron and NoMad, about 400 people on a Tuesday; next drop Tue 2027-01-12". If none are signed yet, say so. This line is never left as a guess.
3. Prices come from `system/dd-offer.js`; the measurement ladder and the price box are fixed.
4. Save as PDF (section 8 settings).

---

## 11. The proposal (within 24 hours of a qualifying brand call)

Two pages: the proposal, and a mock report page so the brand sees exactly what it will get. The mock page is marked "Illustrative placeholders, not results" top and side. Never remove it.

1. Open `templates/proposal/proposal.html` in Chrome.
2. **Brand:** **Brand**, **Product and pack size**, **Prepared for (optional)** (their name and title), **Proposal date**, **Category** (for category exclusivity).
3. **Campaign:** **Tier** (founding for the first three brands only, otherwise standard), **Extra offices** (usually 0), **Proposed drop date** (a Tuesday or Wednesday three to four weeks out, as `2027-01-12`). Every date in the timeline is worked out from it with the business-day rules. **Ask them to ship by (optional)**: only if earlier than the latest date, for example to avoid holiday freight.
4. **The offices:** one fold-out row per office: **Neighborhood**, **Industry**, **Tuesday headcount**, **Planned units** (30 to 80, about 50). No company names before the brand signs. The template refuses the wrong number of rows (5 founding, 10 standard, plus extras).
5. **Where to buy nearby:** one row per store that carries the brand near these offices: **Store**, **Street address**, **Distance from the offices**. Only stores you have evidence for. If they sell online only, add no rows and fill **Online store for the code (optional)**.
6. **Retailer map picture:** a landscape picture (about 2.5 to 1) of the cluster with the brand's stores marked, from the cluster-map workstream (`cluster-1-flatiron/`). **No office pins before the brand signs**: a pin on a building can identify the company. The map is shown whole, never cropped; a tall map prints small and the panel warns you. Until a landscape map exists, press **Remove** to leave the map off, or leave the yellow slot (it blocks the final PDF).
7. When the status box says **Ready to print**, save as PDF (section 8 settings), check both pages, and attach it to your email.

---

## 12. The report (by T plus 7)

One page, the same layout every time, plus an evidence page with every photo when photos are attached. The limitations paragraph is fixed and prints on every report. You cannot edit it, and that is the point.

From a terminal, if the operations tracker writes the JSON: `node render/render.js report report.json report.pdf --final`. Photo paths in that file are relative to the JSON file. By hand in Chrome:

1. Open `templates/report/report.html` in Chrome.
2. **Campaign:** **Brand**, **Product (SKU)**, **Tier**, **Campaign ID**, **Drop date (day 1)**. The window, the due date and the day-30 check are worked out for you.
3. **Offices:** one fold-out row per office (press **Add a row** for more). Type counts, whole numbers, from your drop log: **Delivered (drop day)**, **Placed**, **Placed within one business day?**, **Topped up on day 3 (0 if none)**, **Depleted by day 5**, **Survey responses**, **QR scans**. Under **Placement photo (wide shot, day 1)** and **Later photo (close shot)** press **Choose picture**. If an office never sent a photo, press **Remove**: the report says "No photo received". Never hide it.
4. **Survey:** counts, not percentages, from the survey summary: **Said yes to "Did you try it?"**, **Average rating, 1 to 5**, **Number of ratings**, **Would buy: yes (count)**, **Would buy: maybe (count)**, **Would buy: no (count)**. The report works out every share and prints the count beside it.
5. **Comments:** paste three into **Comment 1, word for word**, **Comment 2, word for word** and **Comment 3, word for word**, exactly as written, typos included. The one change you must make: replace any person's name or identifying detail with `[name removed]` (the survey privacy notice promises it, legal pack file 13). Pick comments useful to the brand, including a critical one if there is one. If you must cut a long one, mark the cut with `[...]` and keep every other word. A comment with an email address or phone number is refused: pick another.
6. **Purchases:** **Code redemptions to date**, the number the brand reports. **Retailer velocity (optional)** only if the brand sends store-level sales.
7. **What we learned: three lines**, one per line, and **Recommendation**: renew into which offices, adjust what, or stop.
8. Tick **I checked every photo shows no identifiable people, and every comment is copied word for word**. When it says **Ready to print**, save as PDF (section 8 settings).

The page refuses numbers that cannot be true (placed more than delivered, depleted more than placed plus topped up, more "tried" than responses). Fix the count, never the template.

---

## 13. Email signature (needs your Gmail login)

Files in `signature/`, built from `brand.json` (section 7):

- `signature.html` and `signature.txt`: everyday.
- `signature-outreach.html` and `.txt`: for cold outreach to offices and brands. It adds the legal pack's line "This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again." Commercial email needs your postal address and that opt-out line (legal pack file 02, draft for attorney review).
- `signature-with-logo.html`: only once `wordmark/png/wordmark-light-on-white-600w.png` is on a public web address; set `SIGNATURE_LOGO_URL` in `brand.json` and rebuild.

To set it up in Gmail (about 3 minutes):

1. Open `signature/signature.html` in Chrome. Press Ctrl+A (Cmd+A on a Mac), then Ctrl+C.
2. In Gmail: gear > **See all settings** > **General** > **Signature** > **Create new**, name it "Everyday", paste, and set it as the default for new emails and replies.
3. Do the same with `signature-outreach.html`, named "Outreach". Choose it from the signature menu when you write a cold email.
4. Scroll down and press **Save changes**. Send yourself a test email and look at it on your phone.

If anything shows yellow, a detail in `brand.json` is still a placeholder.

---

## 14. Social avatar (needs your logins; waits for the name decision)

Files in `avatar/`. Use **`avatar-cobalt-1024.png`** for Slack and Gmail and **`avatar-cobalt-400.png`** for a LinkedIn Page. It is the symbol alone, so it survives a rename, and it holds at 40 px on light and dark screens (`avatar/test-sheet.png`). The paper and ink versions are for places where cobalt clashes; the ink one disappears in dark mode.

A public profile under the working name counts as a public launch, which the legal pack holds until the name decision. A Slack profile inside Startup CPG is your call; a company LinkedIn Page waits.

---

## 15. Using the logo and colors on anything else

- Use the files in `wordmark/`. On white: `wordmark-light.svg` (or `png/wordmark-light-on-white-1200w.png` where SVG is not accepted). On dark: `wordmark-dark.svg`. One color: `wordmark-mono-ink.svg`. Small or square: `symbol-light.svg`.
- Keep empty space around the logo of at least half the height of its capital letters. Never stretch, recolor, outline or shadow it, and never retype the name in another font.
- Colors: ink #1F1D1A for text, cobalt #2E47C9 for the one accent, white for paper. On screen the background can be warm paper #F7F3EA.
- Fonts (free on Google Fonts): Bricolage Grotesque ExtraBold for headings and names, Atkinson Hyperlegible Next for everything else.
- **Rebuilding a page in Canva or Google Docs** (if you ever prefer them): Letter portrait, margins 0.55 in top, 0.6 in sides, 0.5 in bottom; the logo top left at 0.32 in tall with a cobalt rule under it; headings in Bricolage Grotesque ExtraBold 12 pt; text in Atkinson Hyperlegible Next 9.5 pt or larger. Upload the two fonts only if your plan allows it (Canva's font upload is a paid feature as far as we know: unverified, founder to confirm). The HTML templates stay the source: they hold the checks (allergen lock, fixed limitations, no claims) that a Canva copy does not.

---

## 16. If the name changes

1. Open `brand.json` in any text editor. Change `BRAND_NAME` (and `TAGLINE` if needed). If `wordmark/wordmark-metrics.json` says the lockup is wider than 7:1 (names over about 11 characters), set `WORDMARK_LINE_BREAK` to the name with a `|` where it should break, for example `"Desk Drop|Collective"`.
2. In the `desk-drop-identity` folder run `bash render/build-pdfs.sh`. It rebuilds the logo files, the signature, every template's name and every PDF.
3. Open `wordmark/png/wordmark-light-on-white-1200w.png` and `pdf/png/proposal-SAMPLE-founding-1.png` and look at them.
4. Find-and-replace the old name in the `.md` guides in this folder. Nothing else holds the name: the documents' copy uses `{BRAND_NAME}`.
5. Re-copy the signature into Gmail (section 13). Old printed cards: recycle them.

The tests in `tests/name-length/` and `tests/rename-documents/` show the system with other names.

---

## 17. Ordering a print run (only after the name is cleared)

Gate today: **HOLD** (legal pack name-check log v0.5, 2026-10-24). When the legal pack's log says the name is cleared, rerun its "day before any print order" checks, then:

1. Make the card PDF with `--final` (section 3) or print-to-PDF from Chrome. Each office's card is its own design (its own QR), so the cheapest route is the same one-card-per-page Letter PDF.
2. Take or upload it to a copy shop that prints 8.5 x 11 in cardstock (for example a FedEx Office or Staples counter; options and prices unverified, founder to confirm). Ask for: 8.5 x 11 in, white matte cover stock 80 to 110 lb, single-sided, 100% scale, no "fit to page". You cut and score, or ask the shop to quote cutting to 7 x 10 in and scoring at 5 in.
3. Online table-tent products are a fixed size with a minimum per design: Vistaprint's are 5 x 7 in, vertical only, from 10 per design (Vistaprint page, opened 2026-10-24). That does not fit one design per office.
4. A print shop that wants bleed: export with `--mode pro` (7.25 x 10.25 in page, 0.125 in bleed, no marks) and tell them the trim is 7 x 10 in with a score across the middle.
5. Labels: Avery 5126-size half sheets from any office-supply shop; print at home.
6. Documents are not printed: they go out as PDFs.

No spending without your written yes: get the quote, then decide. The plan budgets roughly $1 to $2 a card in runs of 20.

---

## 18. If something goes wrong

### Tent card

| You see | Do this |
| --- | --- |
| Red "Fix before printing" | Do what it says. The card will not be right until it is gone. |
| A big red DO NOT PLACE panel on the card | The text cannot fit with the allergen text at 14 pt. Shorten the two sentences, product line or retailer line. |
| "The two sentences were left off" | Same: shorten them, or accept the card without them (tell the brand). |
| "The ingredient list ... prints in full on the other face" | The list is too long for the front; the front now points to the back. Stand the card where both sides can be seen and photograph both faces. |
| Brand name looks squeezed | Use the short brand name (24 characters or fewer reads best across a pantry). |
| No cobalt band on paper | "Background graphics" was off. Print again with it on. |
| Card prints small or off-centre | Scale was not 100. Print again at 100 or "Actual size". |
| Fonts look different from the screen | Open the file from inside the `desk-drop-identity` folder, not a copy elsewhere; the fonts live in `fonts/`. |


### Documents

| You see | Do this |
| --- | --- |
| Red "DOES NOT FIT ON THE PAGE" bar | Shorten the text you last changed. The template has already made everything else as small as it allows. |
| "Still to fill in (yellow on the page): brand.json: PHONE ..." | Your details are not in `brand.json` yet (section 7). |
| "Fix before printing: The route lists 4 offices; a founding campaign ... has 5" | Add or remove office rows, or change **Extra offices**. |
| "... is not a Tuesday or Wednesday" or "overlaps a blackout" | Choose another drop date. Blackouts: 18 to 31 December, 18 to 31 August, the week of July 4. |
| "Comment 2 contains what looks like an email address" | Choose a different comment. Never edit a comment's words. |
| "Office D has 4 survey responses, under the five ..." | A note for you, not an error. The report prints the real number. |
| "To keep the comments whole, the photo thumbnails moved to page 2" | Normal for long comments with six or more offices. Page 1 keeps the count of photos received. |
| A picture does not appear | Use JPEG or PNG. On an iPhone, share the photo as "Most Compatible" or export it as JPEG. |
| The saved PDF has two pages but you expected one | The report adds an evidence page when photos are attached; the proposal always has the mock page. Both are meant. |
