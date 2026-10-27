# Part A notes: choices, assumptions, open questions, changelog

Workstream G (legal and admin pack), part A of 2. Written 2026-10-23 to 2026-10-24. For the merge step that writes README.md, REPORT.md and HANDOFF.md. Part A wrote nothing outside `desk-drop-legal-pack/`, sent nothing, filed nothing, and made no git writes.

## 1. What part A delivered

Every file opens with "**Draft for attorney review. Not legal advice.**" Every agreement or notice block repeats it inside the block, so the rendered signing copy carries it too. The company name appears exactly once per file (checked by `_work/check_partA.py`).

| File | What it is | When the founder uses it | Feeds |
| --- | --- | --- | --- |
| `10-email-footer-and-checklist.md` | Footer A (no signature), Footer B (under D's signature), HTML version, the three-line CAN-SPAM checklist, notes behind it. Name lives on one `BRAND_NAME = Desk Drop` line, matching E's variable | Week 1, before the first outreach email (Mon 2026-10-26, derived) | E (and D's signature) |
| `11-office-participation-agreement.md` | Founder notes, then the one-page office agreement (10 sections, no penalties), including the pre-formation clause (section 9) | Phase 1, step 4 of the path to signature, weeks 3 to 5 (2026-11-09 to 2026-11-27, derived) | E (send at signature), F (signed copy, fields) |
| `12-brand-campaign-agreement.md` | Founder notes with a plan-term-to-section map, then Part 1 (fill-in campaign sheet) and Part 2 (14 sections of terms) | Phase 2, "close and collect", weeks 4 to 7 (2026-11-16 to 2026-12-11, derived), only after the LLC exists | E, F |
| `13-survey-privacy-notice.md` | Part A short notice for the top of the form (45 words), Part B the optional email question word for word, Part C the full notice, Part D eleven settings that keep it true, open points | Built at Gate 0 pass with the survey; live from campaign zero (drop Tue 2027-01-12, derived) | F (form build), C (hosting) |
| `14-coi-request-brand-product-liability.md` | Email to the brand, a block to forward to its broker, reminder, five-minute certificate check, why the endorsement matters | With the brand agreement and invoice; checked before ship-by (T−10). Campaign zero: send by Tue 2026-12-08, ship-by Tue 2026-12-22 (derived) | F |
| `15-coi-request-own-carrier-building.md` | Email to the pantry owner for the building's requirements, comparison table, request to our carrier or broker, check, no-employees statement | Only after GL is bound; when intake says `coi_required = yes` or `unsure`; at least ten business days before that office's first drop | F |
| `30-llc-operating-agreement.md` | Founder notes, single-member member-managed operating agreement (14 articles), Schedule A (member), Schedule B (first written decision, which also adopts pre-formation agreements) | The day the Articles are filed, at the first verbal brand yes (around Gate 0, Fri 2026-11-13, derived) | H (no figures), founder records |

Supporting files:
- `rendered/` holds PDF (to preview and upload to the e-signature tool) and DOCX (for the attorney's redlines) of the signable blocks only: `11-office-participation-agreement`, `12-brand-campaign-agreement`, `13-survey-privacy-notice` (Part C), `30-llc-operating-agreement`. Page counts: 1, 3, 1, 4 (Letter). Generated; never edit them by hand.
- `_work/render_partA.py` regenerates `rendered/` from the .md files (pandoc, Playwright Chromium, pdftoppm). It fails if any dollar amount in the source is missing from the PDF text.
- `_work/check_partA.py` checks: one company name per file, review heading at the top and inside each block, placeholder case, ladder words (conversion, ROI, lift, acquisition, guarantee outside a negation), stray TODOs.
- `_work/png/` holds page images of the final renders (all were looked at).
- `_work/partA-sources.md` holds the source log S1 to S20 with URLs and dates opened.

Suggested README order (the order of use): 10, 11, 12, 30 (signed the day of filing, which in time comes between 11 and 12), 14, 15, 13. The numbering 10 to 15 and 30 follows the orchestrator's instruction; the README should state each file's "when" explicitly because the operating agreement's date of use falls before the brand agreement's.

## 2. Key choices and why

1. **Signing before the LLC exists.** Offices sign in weeks 3 to 5; the plan forms the LLC at the first verbal brand yes. Chosen: the founder signs for the company in advance, and the office agrees now that the company takes the founder's place once registered (office section 9). The LLC adopts every such agreement in its first written decision (operating agreement Schedule B, item 6), and the founder sends each office a one-line email (template in file 11's notes). Rejected: waiting to sign (stalls the scarce side), or signing personally and re-signing later (five more signatures). The brand agreement is sent only after formation, because it moves money, needs the company's bank account and EIN, and names the company as additional insured. Its section 13 is a fallback with "we will not invoice you until the Company is formed." The operating agreement is signed on the filing date and takes effect on formation (LLC Law 417(c), S1).
2. **Rename-ability.** Agreements define the name once ("**Desk Drop LLC** ("we", "us", the "Company")") and use "we" or "the Company" afterwards. The footer uses a single `BRAND_NAME` line. The COI requests carry the legal name once, on the additional-insured or named-insured line, with "the additional insured above" elsewhere.
3. **The office page has no remedies at all against the office.** Section 7: "You will never owe us money or damages under this agreement." The plan's "two misses = removal from the roster" stays an operating rule, not a contract term, because either side can leave on seven days' notice anyway.
4. **"The office is not liable" became a promise, not a legal conclusion.** "We will not hold you responsible for how anyone uses them" binds us; it does not pretend to bind employees.
5. **The brand indemnity stays the plan's: product claims only, for the company.** I narrowed it to third-party claims and carved out our own mishandling. I did not extend it to offices or to the brand's logo and text; the brand's right to the logo is a warranty instead.
6. **The handling description is written to the ISO vendors endorsement (CG 20 15a 11 10, S14).** Its exclusions cover unauthorized express warranties, intentional change, repackaging, relabeling, demonstrations and the vendor's sole negligence. So units are never opened or stickered, the card uses only the brand's words with a proof sent before printing, and the one real grey area is disclosed to the brand's broker: moving sealed units from brand cartons into per-office boxes. The fallback offered is delivering in the brand's original cartons.
7. **COI requests ask for a standard-form certificate plus the endorsement, never custom certificate wording** (NY Insurance Law 502, S17). The ACORD 25 says a certificate "confers no rights" (S16), so the check requires the endorsement copy.
8. **Privacy design.** Consented emails go to the brand as a bare list, separate from answers, within seven days of the T+4 close; our copy is deleted 30 days later; raw answers are deleted after 12 months. The notice says only what is verified: the form and short-link tools process technical data under their own policies, and we see totals. Tool-specific claims are pushed into Part D as requirements on F, marked "confirm".
9. **The founding testimonial is an honest statement, with the founding price disclosed.** The plan's "written testimonial" became "a short written statement of your honest experience", published with "we will say you were a founding brand at a founding price." This follows the FTC Endorsement Guides: endorsements must be honest, and material connections disclosed (S13).

## 3. Numbered assumptions (where the plan is silent or ambiguous)

1. "Cancellation inside ten days of drop" means ten **business** days, measured against T−10, the brand's ship-by date. Before T−10: refund less $100. On or after T−10: 50% kept.
2. "Explicit yes required for the first three campaigns; opt-out thereafter" is read **per office**: each office's first three drops need a yes, then a brand comes unless the office says no, with at least five business days' notice (five is my number).
3. "60 days of shelf life at delivery" is measured **on arrival** to us (the T−5 check in the plan) or, for brand-direct drops, on arrival at the office.
4. The founding price lock ("next two campaigns") is **$120 per office, paid in full before shipping**, and **unconditional**. The plan's "if this one executes as promised" condition is attached to the testimonial and case study, not the lock, because making a brand lose its discount for our failure would read as a penalty. No time limit is written in: see open question 2.
5. The second standard payment is due **within seven days of placement confirmation**. Placement confirmation means the email sending every office's placement photo. We **may** hold the report until it arrives.
6. **Prices exclude sales tax**, shown on the invoice if it applies (accountant question in part B's file 22).
7. If an office leaves or declines and cannot be replaced, the brand gets **that office's share back** ($120 founding, $150 standard).
8. **Double slip:** if product misses the new T−3 too, either side may treat it as a brand cancellation on or after T−10. **Force majeure:** weather, illness or a building closure moves the drop to the next open Tuesday or Wednesday.
9. **Unused product:** if the brand chose return but sends no prepaid label within ten business days after the window, we release the units to the offices. Damaged or short-dated units are returned at the brand's cost or disposed of, as the brand says.
10. The brand's **confidentiality duty on office identities lasts two years** after the window. The non-solicit lasts six months (plan).
11. The plan's ops-table line "short shipment: credit the difference on the next campaign" is **not** in the brand agreement. It is not in the legal table or appendix F, "the difference" is undefined, and a per-unit credit reintroduces per-unit pricing. Founder to decide.
12. Card proofs go to the brand before printing (a new step for F at about T−5).
13. Operating agreement: member-managed; calendar fiscal year; six-year record retention (my conservative default, accountant to confirm); death does not dissolve the company, and the estate's representative continues it unless it elects to dissolve within 180 days (701(a)(4) allows this); a named Successor may act during incapacity with narrow powers.
14. The office page's "first drop" is a bracketed slot `[DROP DATE: Tue 2027-01-12]`, not the plan's founding-office promise of "first drop within four weeks of signing". Offices signed 2026-11-09 to 11-27 would hit the 18 to 31 December blackout under that promise (see cross-workstream flag 1).
15. Storage time stated to brokers and offices: "usually two to three weeks, up to about four around the December holidays." Campaign zero has ship-by 2026-12-22 and a drop on 2027-01-12.

## 4. Open questions for the founder, each with my recommended default

1. **Which [POSTAL ADDRESS] goes in every cold email?** It becomes public. Default: a USPS post office box or a registered private mailbox, not a home address. Cost not researched: needs quote. Blocks the first send.
2. **Should the founding price lock expire?** Default: add "booked within 12 months after this campaign's window closes", after the attorney agrees.
3. **Short-shipment credit** (assumption 11). Default: leave it out; spread units evenly and tell the brand.
4. **Successor for the operating agreement.** Default: "the Member's executor or other legal representative" until you name someone.
5. **Retention periods in the privacy notice** (7 days, 30 days, 12 months). Default: keep them.
None of these blocks drafting. Only question 1 blocks a step, the first outreach email.

## 5. What the attorney hour should cover for part A's documents

The plan budgets one hour at roughly $300 to $500 (plan figure, not a quote). In priority order:
1. **Office section 9 and brand section 13:** does advance consent to the company taking the founder's place release the founder personally under New York law, and does Schedule B's adoption do what it says?
2. **Brand section 8:** is 50% retention on or after T−10 enforceable as liquidated damages rather than a penalty, given the stated reasons? Same question for the double-slip rule and the release-to-offices default.
3. **Brand section 7:** is the liability cap at fees paid enforceable as written, or does it need carve-outs (gross negligence, willful misconduct) to survive?
4. **Brand section 6:** is the mishandling carve-out right, and should offices also be covered by the brand's indemnity or insurance?
5. **Brand section 3:** the founding statement and case study under the FTC Endorsement Guides; whether the FTC's consumer reviews and testimonials rule also applies (not researched).
6. **Brand section 11:** six-month non-solicit scope; whether to add venue or dispute terms (none now).
7. **Footer:** is "This is a business pitch" a sufficient identification under CAN-SPAM?
8. **Privacy notice:** is "anonymous" right when the office is known and comments are quoted, and should the processors be named?
9. **Operating agreement:** the successor and incapacity clauses against estate law; whether the bank needs anything notarized.
10. **No-employees statement** (file 15) and whether to ask brands for primary and non-contributory coverage or waiver of subrogation later.

## 6. Cross-workstream flags for HANDOFF.md

1. **E (outreach), conflict with plan text:** the plan's founding-office offer, "first drop within four weeks of signing", cannot hold under the canonical calendar for offices signed after about 2026-11-17, because the drop is 2027-01-12. Use `[DROP DATE: Tue 2027-01-12]` instead. The office agreement does.
2. **E:** use footer A or B from file 10 on every outreach email; map `{BRAND_NAME}` to E's variable; omit `[WEBSITE]` until the site is public.
3. **E and F, paid-brands row:** the brand agreement adds a Part 1 "Category" (brand-intake `category`) and an "Optional newsletter sign-up" choice. Suggested new columns in `paid_brands.csv`: `newsletter_option` (Y/N) and `brand_privacy_url`. Producers may add columns (CONTRACTS 6).
4. **F (operations), new steps the agreements promise:**
   - send a card proof to the brand before printing;
   - record best-by dates and lot numbers on arrival;
   - pull product from every office within one business day on a recall request;
   - remove product and tell the brand the same day on a complaint;
   - placement confirmation is the email carrying every office's placement photo, and the second invoice is due seven days after it;
   - release unused product if no return label arrives within ten business days after the window;
   - per-office approval: explicit yes for each office's first three drops, then opt-out with at least five business days' notice;
   - implement privacy Part D (D1 to D11), including the email-only export within seven days of T+4 and the deletion reminders;
   - check the certificate (file 14) before confirming ship dates, and record `coi_received_date`.
5. **D (identity):** the card carries the allergen statement word for word including any "may contain" line, plus only the brand's own two sentences (vendors endorsement exclusion for unauthorized express warranties).
6. **C (website):** host the full privacy notice at `[PRIVACY URL]`; never show an office name unless the office ticked "publicly" in section 6.
7. **H (financial model):** part A adds no cost figures. The FTC penalty ($53,088 per email, S11) is a risk, not a cost. Plan figures used as stated: $1M product liability minimum, $1M/$2M GL target, $300 to $500 attorney hour.
8. **Part B consistency, for the merge step:** part B's food-safety script (file 21) states the same storage facts as files 12 and 14 ("usually two to three weeks, up to about four"). Its exact question says "up to about three weeks". Suggest aligning that to "about four". I did not edit part B's file.

## 7. Changelog (one line per round)

- **Round 1 (draft):** wrote files 10 to 15 and 30 from the plan's legal table and appendices E and F; built `render_partA.py` and `check_partA.py`; the office page rendered to one Letter page.
- **Round 2 (attorney test):**
  - brand agreement: limited the indemnity to third-party claims; reverted the warranty to the plan's "labeling law"; restated cancellation against T−10 so there is no boundary gap; added the weather or illness slip, insurance in force through the window, damaged-product disposal and survival of sections 3 and 9; placement wording now fits office-placed drops;
  - office page: fixed the "no personal data" sentence that contradicted its own email exception; added the first-drop slot and "we add to your pantry";
  - operating agreement: removed the corporate-opportunity line; made the tax sentence an intent rather than a legal conclusion; routed death through the estate under 701(a)(4);
  - privacy notice: name removal before quoting; no impossible "without asking" promise.
- **Round 3 (broker test):** removed unverified claims from outbound copy and notes ("a day or two, usually no charge", "several million dollars", "one-letter rejection"); added a products line, acceptance of a standalone product liability policy and an occurrence or claims-made check; corrected storage time from two weeks to "up to about four"; made the no-employees statement true once couriers deliver.
- **Round 4 (inspector test):** the office page now says "never open a package or change its label" (re-boxing sealed units is not opening); the card carries any "may contain" line; storage adds "away from heat" (plan) and best-by dates; complaints mean removal plus telling the brand the same day.
- **Round 5 (pantry-owner test):** "one later photo" became day 3 or day 5; the debrief is after the drop; brands may not approach the office directly; "New company" wording ending "Nothing else changes for you"; founder phone and email in the signature block; COI row in plain words; signature table compacted to keep one page.
- **Round 6 (attorney, second pass, plus render fixes):**
  - render fixes: pandoc was turning "$1,500 ... ($150" into math and garbling the standard price, so dollar-math was disabled and a guard added that fails the render if any amount is missing from the PDF;
  - brand agreement: category row added; "blackouts" defined; shelf life measured on arrival; confidentiality term reworded; sections 13 and 14 folded into the closing section (back to three pages);
  - notes: removed the overclaim that every blank maps to a column.
- **Round 7 (consistency across documents):** the office non-solicit now matches the brand agreement's six months; the footer gates on the name check and omits `[WEBSITE]` until the site is public.
- **Round 8 (full cold read):** office photo consent now covers our own materials without identifying the office, matching brand section 10; a missing brand certificate at T−10 now follows the agreement's slip and cancellation path; the "ADDL INSD" check covers a separate product liability policy; layout fixes (checkboxes kept with their labels, notice headings, operating agreement signature blocks, Schedule A kept with its table).
- **Round 9 (full pass, wording only, stop condition met):** corrected the short-notice word count (45); pointed cross-references at part B's real files (01, 02, 20); version 0.2.

## 8. Verification evidence

- `python3 desk-drop-legal-pack/_work/check_partA.py` → "7 files checked, 0 findings".
- `python3 desk-drop-legal-pack/_work/render_partA.py` → pages 11: 1, 12: 3, 13: 1, 30: 4. The dollar-amount guard passes.
- DOCX copies opened with python-docx: review heading present, one company name each, $600 and $1,500 intact. One copy was converted through LibreOffice and looked at.
- Every page image in `_work/png/` was viewed after the final render.
