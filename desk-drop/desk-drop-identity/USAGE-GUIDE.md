# Usage guide: making and printing the pieces yourself

For the founder, or anyone helping on drop day. No design software and no designer needed. You need Google Chrome. The terminal commands are optional and only save time on bigger drops.

Version 1.0, 2026-10-23. Part 1 covers the tent card, the case label, the logo and colors. Part 2 adds the documents (one-pagers, proposal, report, signature).

**Before any commercial print run:** the name must be cleared first (`desk-drop-legal-pack/name-check-log.md`). Printing at home or at a copy shop for a test is fine.

---

## 1. Six rules that matter most

1. **Allergen text is copied word for word from the package.** Same words, same spelling, same order, including "Contains" and the "may contain" line. Read it off the package itself, not from the brand's email. Never shorten it. It prints at 14 pt and nothing can make it smaller.
2. **One card per office, never swapped.** Each office's card has its own QR link and its card ID (for example "Card O-003 · CMP-001") in the bottom corner.
3. **No claims.** The two sentences say who makes it and why. No "healthy", "best", "guaranteed", "boosts", and no sales or lift promises.
4. **Yellow means unfinished.** Anything with a yellow highlighter is a placeholder. Nothing yellow goes into an office.
5. **Red SAMPLE banner means practice.** Anything with it is test material and never goes into an office.
6. **Print at 100% with Background graphics on.** "Fit to page" shrinks everything, including the allergen text.

---

## 2. Make one tent card in Chrome (target: under 10 minutes)

You need: the brand's details (from the paid brand row or their email), the package itself (for the allergen text), and this office's QR link and office ID (from the operations tracker).

1. Open the folder `desk-drop-identity/templates/tent-card/` and double-click `tent-card.html`. If it opens in another browser, right-click it and choose Open With > Google Chrome. (1 minute)
2. The card appears on the right with yellow placeholders; the boxes on the left fill it in, and the card updates as you type. Grey text inside an empty box is a hint, not a value. Under each box, grey small print says where the value comes from.
3. **Brand:** type the brand name (short form, as on the package), the product, and the two sentences. Keep the two sentences under 200 characters. (2 minutes)
4. **Allergens:** pick up the package. First choose where the package declares allergens: a "Contains" line (most packages), only inside the ingredient list, or nowhere. Then type exactly what is printed: the "Contains" line, or the whole ingredient list if there is no "Contains" line, and the "may contain" line in the second box. For "nowhere", leave the box empty; the card prints a fixed line telling people to read the package. Read your typing back against the package, word by word, then tick the box that says you did. (3 minutes)
5. **Where to buy:** fill the retailer and street, or the code and its site, or both. The card writes the sentence for you. (1 minute)
6. **QR and IDs:** paste this office's QR link, then type the office ID and campaign ID. Scan the QR on screen with your phone: it must open this office's link. (1 minute)
7. Look at the status box under the buttons. It must say **Ready to print** and nothing in red. Yellow notes ("Check: ...") are warnings: read each one. If it says the two sentences were "left off", shorten them until they come back. (1 minute)
8. Press **Save as JSON** so you can reuse this card next time (for the next office, load it and change only the QR link and office ID).
9. Press **Print** and set: Destination your printer, Paper Letter, Scale 100 (or "Actual size"), Margins Default, More settings > **Background graphics** on. Load one sheet of cardstock. Print.

For the next office of the same brand: change only the QR link and the office ID, check the status box, print. About one minute each.

**If something goes wrong**

| You see | Do this |
| --- | --- |
| Red "Fix before printing" | Do what it says. The card will not be right until it is gone. |
| A big red DO NOT PLACE panel on the card | The text cannot fit with the allergen text at 14 pt. Shorten the two sentences, product line or retailer line. |
| "The two sentences were left off" | Same: shorten them, or accept the card without them (tell the brand). |
| "The ingredient list ... prints in full on the other face" | The list is too long for the front. The front now points to the back. Stand the card where both sides can be seen (not flat against a wall) and photograph both faces. |
| Brand name looks squeezed | Use the short brand name (24 characters or fewer reads best across a pantry). |
| No cobalt band on paper | Background graphics was off. Print again with it on. |
| Card prints small or off-centre | Scale was not 100. Print again at 100 or "Actual size". |
| Fonts look different from the screen | Open the file from inside the `desk-drop-identity` folder, not from a copy somewhere else; the fonts live in `fonts/`. |

---

## 3. Make every card for a drop at once (optional, terminal)

When you have 10 offices, the operations workstream can write one JSON file with one card per office. Then, from the `desk-drop-identity` folder:

```bash
node render/render.js tent-card path/to/cards.json cards-for-printing.pdf --final
```

One PDF page per office. `--final` refuses to make the PDF while any placeholder or SAMPLE value is left. Field list: `templates/tent-card/FIELDS.md`. First time only: install Node (nodejs.org, free), then in this folder run `npm install` and `npx playwright install chromium`.

---

## 4. Print, cut and fold the tent card

What you need: white **matte** cardstock, 80 to 110 lb cover (about 216 to 300 gsm), a ruler, a paper trimmer or a craft knife and cutting mat, and a bone folder or the back of a butter knife. Check your printer's maximum paper weight first; most home printers take cardstock through a rear or manual feed.

1. Print one test on plain paper. Hold it up: both faces present, text not cut off, QR crisp.
2. Print on cardstock, one sheet per office plus one spare per office.
3. Cut on the four corner marks. The card is 7 x 10 in flat.
4. Lay the ruler between the two FOLD marks and score the line.
5. Fold with the printed side outside. Press the crease flat.
6. Stand it with the feet about 4 in apart. Both faces read the right way up.
7. Check the card ID on the card against the office on the case label before it goes in the case.

The full spec, with dimensions, stock and every type size, is `specs/tent-card-spec.pdf`.

---

## 5. Case labels

1. Open `templates/case-label/case-label.html` in Chrome. It shows two labels per sheet.
2. Fill the boxes for the first label (office, address, hand-to name, brand, product, units in this case, case number, drop date, IDs). For more labels, edit the JSON list in the file or have the operations workstream write it, then run `node render/render.js case-label labels.json labels.pdf --final`.
3. Write the count you actually packed into "Units in this case", not the planned count.
4. For your reserve bag, set label type to `reserve`.
5. Print on Avery 5126-size half-sheet labels, or on plain paper cut on the dashed line and taped flat with clear packing tape on all four edges. Same print settings as the card.
6. Before the label prints for real, put your business phone number in `brand.json` (`PHONE`) and run `node render/build-brand.js`. Until then every label shows a yellow `[PHONE]`.

Spec: `specs/case-label-spec.pdf`.

---

## 6. Place it and take the two photos

From the plan's per-stop procedure:

- Place at eye level beside the existing snacks, never inside a cabinet. Card in front of the product, allergen panel visible. One display per pantry.
- **Wide photo:** step back until the whole pantry is in the frame, with the card and product in it.
- **Close photo:** card and product from about arm's length; the card should span at least a fifth of the photo's width. Zoom in on your phone and check you can read the allergen panel. If not, step closer and take it again.
- No identifiable people in either photo.

---

## 7. Using the logo and colors on anything else

- Use the files in `wordmark/`. On white: `wordmark-light.svg` (or `png/wordmark-light-on-white-1200w.png` where SVG is not accepted). On dark: `wordmark-dark.svg`. One color: `wordmark-mono-ink.svg`. Small or square: `symbol-light.svg`.
- Keep empty space around the logo of at least half the height of its capital letters. Never stretch, recolor, outline or shadow it, and never retype the name in another font.
- Colors, with hex codes: ink #1F1D1A for text, cobalt #2E47C9 for the one accent, white for paper. On screen the background can be warm paper #F7F3EA.
- Fonts (free on Google Fonts): Bricolage Grotesque ExtraBold for headings and names, Atkinson Hyperlegible Next for everything else.

---

## 8. If the name changes

1. Open `brand.json` in any text editor. Change `BRAND_NAME` (and `TAGLINE` if needed). If `wordmark/wordmark-metrics.json` says the lockup is wider than 7:1 (names over about 11 characters), set `WORDMARK_LINE_BREAK` to the name with a `|` where it should break, for example `"Desk Drop|Collective"`.
2. In the `desk-drop-identity` folder run `bash render/build-pdfs.sh`. It rebuilds the logo files, the templates' name and every PDF.
3. Open `wordmark/png/wordmark-light-on-white-1200w.png` and look at it.
4. Find-and-replace the old name in the `.md` guides in this folder.
5. Old printed cards: recycle them.

The test in `tests/name-length/` shows the system with "Dropp" and "Desk Drop Collective"; both work.

---

## 9. Ordering a print run (only after the name is cleared)

Cards for different offices are different designs (each has its own QR), so the cheapest way to get a stack printed is the same PDF you print at home, one card per page:

1. Make the PDF with `--final` (section 3) or print-to-PDF from Chrome.
2. Take or upload it to a copy shop that prints 8.5 x 11 in cardstock (for example a FedEx Office or Staples counter; their options and prices are unverified, founder to confirm). Ask for: 8.5 x 11 in, white matte cover stock 80 to 110 lb, single-sided, 100% scale, no "fit to page". Cutting and scoring can be done by you, or ask the shop for a quote to cut to 7 x 10 in and score at 5 in.
3. Online table-tent products are usually a fixed size and a minimum quantity per design: Vistaprint's table tents are 5 x 7 in, vertical only, from 10 per design (Vistaprint page, opened 2026-10-24). That does not fit one design per office. Use one only if you decide to drop the per-office QR.
4. A print shop that wants bleed: export with `--mode pro` (7.25 x 10.25 in page, 0.125 in bleed, no marks) and tell them the trim is 7 x 10 in with a score across the middle.

No spending without your written yes: get the quote, then decide.
