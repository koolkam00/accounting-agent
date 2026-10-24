**Draft for attorney review. Not legal advice.**

# Legal and admin pack: report back

Version 0.6 · 2026-10-24 · Workstream G · folder `desk-drop/desk-drop-legal-pack/` · updated after independent review round 1 (`_review/round-1.md`)

Nothing was filed, sent, signed, bound, applied for, bought or published. No connector that writes anywhere was used, and there were no git writes. Every figure below carries a dated source or is marked as a plan estimate, a needed quote or unverified.

## 1 · What is in the pack and where

Thirteen documents, numbered in the plan's order of operations, plus the index. Each opens with "Draft for attorney review. Not legal advice." Each sets the company name once, so a rename is one edit per file. `00-index.md` says what each is for and when it is used, with derived dates.

| # | Document | Used |
| --- | --- | --- |
| 00 | `00-index.md`: what each file is for and when | Start here |
| 01 | `01-name-check-log.md`: USPTO, Department of State and domain searches, verbatim and dated | Week 1 |
| 02 | `02-email-footer-and-checklist.md`: footer with [POSTAL ADDRESS] and opt-out line; three-line checklist | First outreach email, week 1 |
| 03 | `03-office-participation-agreement.md`: one page, no penalties (rendered: 1 page) | An office's yes, once the attorney has cleared the page (hour by Wed 2026-11-18); Phase 1, weeks 3 to 5 |
| 04 | `04-formation-checklist.md`: LLC, EIN, bank, publication, 120-day deadline, six-county cost comparison | First verbal brand yes |
| 05 | `05-llc-operating-agreement.md`: single-member, member-managed (rendered: 4 pages) | Filing day |
| 06 | `06-gl-quote-request-script.md`: honest description, 20 questions, comparison table | Quotes at Gate 0; bind before any brand ships |
| 07 | `07-food-safety-call-script-and-log.md`: exact question, facts, follow-ups, answer log | By Fri 2026-11-20; before any brand ships |
| 08 | `08-attorney-hour-agenda.md`: ranked, time-boxed agenda with send-ahead note (new at merge) | Held by Wed 2026-11-18, before the first office signs |
| 09 | `09-accountant-question-list.md`: sales tax, UBT, estimates and 15 more | Held by Fri 2026-11-20 |
| 10 | `10-brand-campaign-agreement.md`: campaign sheet plus fixed terms (rendered: 3 pages) | A brand's yes, after formation |
| 11 | `11-coi-request-brand-product-liability.md`: to the brand, its broker block, reminder, check | With file 10 |
| 12 | `12-coi-request-own-carrier-building.md`: building requirements, request to our carrier, check | After GL is bound, per building |
| 13 | `13-survey-privacy-notice.md`: short notice, email consent wording, full notice, form settings (rendered: 1 page) | Live at campaign zero |

Also: `name-check-log.md` (pointer at the CONTRACTS 6.7 path, gate status), `figures.csv` (25 cost rows for the financial model), `rendered/` (PDF and DOCX of 03, 05, 10, 13), `README.md` (how to edit), `HANDOFF.md` (what goes to C, D, E, F, H), and `_work/` (raw research, `check_pack.py`, `render_pack.py`, the name-check rerun script, drafting and merge notes).

## 2 · Name-check log: run or not run, with dates

**Gate status: HOLD** for any print run (D) and any public launch (C). Private discovery calls may use the working name. Full log, raw files and rerun steps: `01-name-check-log.md`.

| Search | Run? | When (UTC) | Result, in short (verbatim in file 01) | What it does not prove |
| --- | --- | --- | --- | --- |
| USPTO trademark search (tmsearch.uspto.gov), five spellings plus both-words, pseudo-mark and wildcard queries | **Run** | 2026-10-23 23:31 to 23:35; rerun 2026-10-24 00:04:51 | No live mark with both words. One dead filing: DESK-DROP, serial 99174501 (Elior, Inc.), food ordering and office delivery, refused as "merely descriptive" under Section 2(e)(1) in the Office action of 2025-09-30, abandoned 2026-03-31. Live: DROPDESK, reg. 5782323, co-working office rental (words reversed, different service) | Unregistered (common-law) use; filings in the last few days; state and foreign marks; whether a similar mark would confuse buyers |
| New York Department of State, Public Inquiry web search | **Not run, founder to run** | Tried 2026-10-23 23:37 | The page showed a bot-protection challenge and no search form; it was not bypassed. Five-minute steps in file 01, row 12 | |
| Department of State open data on data.ny.gov (active corporations; all name history; daily filings) | **Run** | 2026-10-23 23:37 to 23:38; rerun 2026-10-24 00:04:51 | No entity named DESK DROP, DESKDROP or DESK-DROP. Only DROPDESK LLC (Nassau County, 2017) | Assumed names; filings after each dataset's cut-off; whether the Department would accept the name |
| .com (Verisign RDAP) | **Run** | 2026-10-23 23:30 | deskdrop.com registered since 2004-01-31, active, no site answered. deskdropnyc.com and desk-drop.com: not found | Who owns it, or whether it is for sale; availability at a registrar |
| .nyc (rdap.nic.nyc) | **Run** | 2026-10-23 23:30 | deskdrop.nyc and deskdropnyc.nyc: "Not found" | Availability; a .nyc residency rule (unverified, founder to confirm at checkout) |
| Related sites and domains | **Run** | 2026-10-23 23:30 to 23:31 | thedeskdrop.com (also reached through deskdrop.co and trydeskdrop.com) is an active "DeskDrop" business selling custom-branded chocolate gifts shipped to business recipients' desks, nationwide | Whether it holds rights (no USPTO filing was found); common-law rights can come from use alone |
| Open web and Instagram, "the name plus snack, office, New York" | **Partly run** (the sites above only); **founder to finish** | | Steps in file 01, "The day before any print order or public launch" | |

Recommended default (file 01): treat the name as taken. Shortlist two fallback names in week 1, preferably coined words, run the log on each with `_work/namecheck/scripts/name_check.py`, and decide by Fri 2026-11-13, before anything is printed or filed. Keep the working name only if the attorney says the risk is acceptable (file 08, item 1, held before filing).

## 3 · Publication cost comparison, with sources

New York requires a copy of the Articles or a notice to run "once in each week for six successive weeks" in two newspapers designated by the clerk of the county where the LLC's office is located, and the Certificate of Publication to be filed within 120 days after the Articles take effect (LLC Law §206, nysenate.gov, opened 2026-10-23). The county named in the Articles therefore sets the cost. Newspaper cost only below; the \$50 state fee is separate. All sources opened 2026-10-23.

| County (borough) | A: newspaper-rate estimate | B: vendor all-in, less \$50 | C: newspaper ballpark | C: vendor all-in, less \$50 | **Working figure** |
| --- | --- | --- | --- | --- | --- |
| New York (Manhattan) | \$1,500 to \$2,000+ | \$1,745 | \$1,000 to \$1,700 | \$448 (promotion, dates unclear; outlier) | **\$1,745** |
| Bronx | not listed | \$1,695 | \$399 to \$600 | not listed | **\$1,695** |
| Kings (Brooklyn) | \$800 to \$1,200 | \$1,425 | \$400 to \$800 | not listed | **\$1,425** |
| Richmond (Staten Island) | not listed | \$1,245 | \$399 to \$600 | not listed | **\$1,245** |
| Queens | \$600 to \$1,000 | \$1,145 | \$399 to \$600 | not listed | **\$1,145** |
| Albany | \$200 to \$300 | \$345 | "Lowest in New York", no figure | \$299 | **\$345** |

- **A.** statebusinesscompliance.com, "New York LLC Publication Requirement 2026 ... County-by-County Fee Breakdown", last updated May 5, 2026, estimates "based on 2026 newspaper advertising rates"; the plan's source, affiliate disclosure in the footer. https://www.statebusinesscompliance.com/blog/new-york-llc-publication-requirement-2026-1-500-manhattan-cost-vs-150-upstate-county-by-county-fee-b
- **B.** LLC Publishers, pricing page (all-in packages including both papers, affidavits, notarization and the \$50 fee; no date on the prices; a vendor). https://www.llcpublishers.com/pricing
- **C.** Cheap NY Publication (Redstone Castle LLC), "NY LLC Publication Cost by County (2026)" (a vendor). https://cheapnypublication.com/llc-publication-cost-by-county
- **State fees, verified 2026-10-23:** Articles \$200 and Certificate of Publication \$50 (dos.ny.gov; LLC Law §1101(f) and (s)).
- **Reading:** the plan's figures hold (New York County about \$1,500 to \$2,000; Albany about \$200 to \$300). Working figures are B less \$50, the only firm all-in price for every county. Albany would save about \$1,400 against New York County, less a registered agent's fee (needs quote), if the attorney confirms the Articles may name it (file 08, item 2). The clerks' designated-paper lists were not confirmed (bot check on nycourts.gov; Albany's old page returns 404): unverified, founder to confirm with the publication service.
- **The 120-day deadline**, explained in file 04 section 5: the clock starts on the effective date; six weekly runs span five weeks, papers need lead time and affidavits take days, so the pack targets ordering by business day 10 and filing by day 100. Missing it suspends the LLC's "authority to carry on, conduct or transact any business" until a certificate is filed; the statute says contracts stay valid and members do not become liable (LLC Law §206). Filed Fri 2026-11-13, day 120 is Sat 2027-03-13; treat Fri 2027-03-12 as the last day.

## 4 · Numbered assumptions

Where the plan was silent or ambiguous, I decided and list it here. Dates are derived from CONTRACTS section 3, founder to confirm.

**Timing**
1. The LLC is filed at the first verbal brand yes, expected between Gate 0 (Fri 2026-11-13) and Gate 1 (Fri 2026-12-11). File 04 gives dates for three filing days.
2. Files are numbered in the plan's order-of-operations sentence. Two steps deliberately start earlier than their place: GL quotes at Gate 0, and the attorney hour before filing.
3. Both professional hours are booked at Gate 0 (the attorney slot is asked for in week 3 and confirmed only if Gate 0 passes). The attorney hour is held early in week 4, by Wed 2026-11-18: before the first office signs, and before filing because the name and county change the filing. The accountant hour is held by Fri 2026-11-20, early because sales tax registration, if needed, must come "at least 20 days before you begin business" (TB-ST-360, opened 2026-10-23).
4. Offices sign only after the attorney has cleared the office page (changed in review round 1). The plan finalizes the page at the Gate 0 pass, so signatures start in week 4 anyway; holding them to Wed 2026-11-18 costs at most two business days and spares pantry owners a page that reads "Draft for attorney review" at the top. If the hour slips, the draft goes out with a one-line cover note (file 03 notes). **Default: wait for the hour.**
5. The state food safety call is recommended by Fri 2026-11-20, earlier than the plan's Gate 1 checklist. Insurance is bound and the state answer logged before any brand ships, latest Mon 2026-12-21 (ship-by Tue 2026-12-22).
6. Storage time stated to brokers, the state and the accountant: "usually two to three weeks, up to about four around the December holidays". Volumes: about 550 units for campaign zero (2 brands × 275), up to about 1,650 later (3 brands × 10 offices × 55).

**Names and drafting**
7. One name approach: the legal name sits in a `[COMPANY NAME: Desk Drop LLC]` slot, once per document; the trading name is `BRAND_NAME = Desk Drop` in files 01, 02 and the pointer.
8. The review heading is on every file and signable block. The footer text pasted into emails does not carry it; the footer is used from week 1 and checked in the attorney hour (item 12).
9. Signing before formation: the founder signs the office page for the Company, the office consents now to the Company taking over, and Schedule B of the operating agreement adopts every such agreement. The brand agreement is sent only after formation; its section 13 is a fallback.

**Office agreement**
10. "Explicit yes for the first three campaigns" is per office: each office's first three drops need a yes; then each brand is emailed at least five business days ahead (five is my number) and comes unless the office says no.
11. The plan's "two misses means removal from the roster" stays an operating rule, not a contract term.
12. The first drop is the slot `[DROP DATE: Tue 2027-01-12]`, not "within four weeks of signing" (section 8 below).
13. An "I agree" email reply counts as signing the office page.
14. The office page promises to name a building's owner and managing agent as additional insureds when the building requires it. If our carrier cannot, we do not deliver there; the plan already puts certificate-only buildings "on the list for later".

**Brand agreement**
15. "Cancellation inside ten days of drop" means ten business days, measured against T−10, the ship-by date: before T−10, a full refund less \$100; on or after T−10, 50% kept. T−10 is about two calendar weeks before a Tuesday drop (campaign zero: Mon 2026-12-28 for Tue 2027-01-12), so a brand cancelling 11 to 13 calendar days out keeps less than under a calendar-day reading. Part 1 now prints the exact cancel-by date, so the brand never counts business days (review round 1). **Default: keep T−10**, because it is the day the brand ships, so 50% is never kept on product that has not left the brand. Question 6 below; attorney item 5.
16. "60 days of shelf life at delivery" is measured on the drop day: a unit placed that day has at least 60 days left (changed in review round 1; it was "on arrival", which left about 53 days at placement).
17. The founding lock ("\$600 for 5 offices (\$120 per office) ... locked for their next two campaigns") is \$120 per office for up to 10 offices, any office beyond 10 at \$150, paid in full before shipping, for the next two campaigns, unconditional and with no end date. Per-office matches the financial model's brief ("renew at the founding rate (\$120 per office)") and D's offer data (`per_office: 120`); the cap at 10 offices is new in review round 1. The plan's "if this one executes as promised" attaches to the statement and case study, not to the lock. **Default: this wording; add a 12-month booking window only after the attorney agrees** (decision D1).
18. The second standard payment is due on placement confirmation, the plan's own term: it is invoiced the day we send the email with every office's placement photo, and the report may wait for it. The earlier "within seven days of" placement confirmation was softer than the plan and contradicted Part 1; it was dropped in review round 1. **Default: the plan's term** (decision D6).
19. Prices exclude sales tax, shown on the invoice if it applies.
20. If an office leaves and cannot be replaced, the brand gets that office's share back (\$120 founding, \$150 standard).
21. A second missed T−3 lets either side treat the campaign as cancelled on or after T−10. Weather, illness or a building closure moves the drop to the next open Tuesday or Wednesday.
22. Unused product is released to the offices if no prepaid return label arrives within ten business days after the window; damaged or short-dated units are returned at the brand's cost or disposed of, as it says.
23. Confidentiality of office identities lasts two years; the non-solicitation lasts six months (plan).
24. The plan's "short shipment: credit the difference on the next campaign" is not in the agreement: "the difference" is undefined and a per-unit credit brings back per-unit pricing (decision D2).
25. Card proofs go to the brand before printing.
26. The plan's "written testimonial" is "a short written statement of your honest experience", published with the disclosure that it came from a founding brand at a founding price (FTC Endorsement Guides, opened 2026-10-23).
27. The indemnity covers third-party product claims, except to the extent our mishandling caused them; the brand controls the defense and cannot settle in our name without consent.
28. Storage follows any instruction on the label, and a unit placed in one office never moves to another.

**Formation, insurance and money**
29. Publication working figure: vendor B's all-in price less the \$50 state fee. New York County (\$1,745) is carried until the county is chosen.
30. Counties compared: the five boroughs (the founder's borough is unknown, plan question 3) and Albany.
31. Day 120 is not assumed to roll forward past a weekend.
32. GL working figure \$1,200 a year, the plan's "roughly \$100 a month"; range \$500 to \$1,500 (plan).
33. Food warehouse license working figure \$400 until the state answers; \$0 if it says no or brands ship direct.
34. Attorney \$400 and accountant \$300: the midpoints of the plan's ranges, together the plan's "about \$700".
35. Operating agreement: member-managed; calendar fiscal year; six-year record retention (my default, accountant to confirm); death does not dissolve the company; a named successor has narrow powers during incapacity.
36. Survey retention: consented emails passed to the brand within seven days after the survey closes, our copy deleted 30 days later, answers deleted after 12 months (the plan sets none).
37. [POSTAL ADDRESS] is a USPS post office box or a registered private mailbox, not a home address. Its cost was not researched (`figures.csv`, `needs quote`).

**Added in review round 1**
38. The brand keeps its product liability cover, with us as additional insured, from its ship date until 12 months after the window closes, or the latest best-by date on the units if later. A claims-made policy needs a retroactive date on or before the ship date, and the brand keeps it in force or buys an extended reporting period for that time. The obligation survives the campaign (section 14). Why: released units stay in pantries and go home with employees, and an occurrence policy covers only injury during its own period (review round 1). **Default: keep** (decision D7; attorney item 16).
39. A slipped drop never puts a window across a blackout: it moves to the first Tuesday or Wednesday whose five-day window is clear (CONTRACTS section 3; review round 1).
40. The office's employer is named in its own `[OFFICE LEGAL NAME]` slot on the office page and in Schedule B of the operating agreement, so "Company" only ever means us (review round 1).
41. Buildings: expect to add each building by name (CG 20 26) and budget the endorsement, because we will have no contract with any building. A reviewer's recollection that New York requires a direct contract for a blanket endorsement's "written contract with you" (Gilbane v. St. Paul, 2018) was not opened: unverified, attorney item 15.

## 5 · Changelog, one line per round

Drafting, part A (files now 02, 03, 05, 10, 11, 12, 13):
- A1, draft: all seven files from the plan's legal table and appendices E and F; the office page rendered to one page.
- A2, attorney: indemnity limited to third-party claims; cancellation restated against T−10; slip, force-majeure and survival terms; the office page's data sentence made consistent with its email exception; operating agreement death clause routed through the estate.
- A3, broker: unverified claims removed from outbound copy; product line, standalone product liability policy and occurrence check added; storage time corrected to "up to about four" weeks.
- A4, inspector: "never open a package or change its label"; the card carries any "may contain" line; "away from heat" and best-by dates; complaints mean removal and telling the brand the same day.
- A5, pantry owner: later photo on day 3 or day 5; debrief after the drop; no direct approach by brands; signature block compacted to one page.
- A6, attorney second pass and render fixes: dollar amounts were being read as math, so a guard now fails any render that loses an amount; category row, blackouts, shelf life on arrival.
- A7, consistency: six-month non-solicit on both agreements; the footer waits on the name check.
- A8, full cold read: photo consent matches the brand agreement; a missing certificate at T−10 follows the slip path; layout fixes.
- A9, full pass: wording only; stop rule met.

Drafting, part B (files now 01, 04, 06, 07, 09 and `figures.csv`):
- B1, draft: name searches run; formation checklist, GL script, food safety script, accountant list and figures from official pages.
- B2, four expert passes: verbatim statute quotes; name default changed to "treat as taken"; the mishandling gap added to the GL questions; the food safety question's three-versus-four-week mismatch fixed; trademark high figure corrected from 750 to 850.
- B3, full read: one deadline rule everywhere ("before any brand ships, latest Mon 2026-12-21"); "I sell no food" replaces "I sell nothing", which contradicted the fee; dollar signs escaped.
- B4, full pass: wording only; stop rule met.

Merge (this step):
- M1, consolidation: 13 files renumbered into order of use, every cross-reference rewritten; one name approach, set once per file; version 0.5 everywhere; new file 08, one attorney agenda from items scattered across nine files; storage time, cancellation summary and professional-hour timing aligned; two cost rows added (mailing address, biennial statement); pack-wide check and render scripts.
- M2, attorney: the office page no longer promises a brand's conduct (it states our requirement on the brand); signer "for the Company", true before and after formation; the indemnity gains defense control and settlement consent; the 50% reason says "kept your category closed", always true, not "turned away other brands"; payment, cap, indemnity and cancellation re-checked line by line against the plan.
- M3, broker: the office page promises in writing to name a building that requires it, which may satisfy a blanket endorsement's written-contract condition (if the carrier says not, it adds the building by name); the GL script and the carrier request point to it; the brand certificate check covers a separate product liability policy.
- M4, inspector: one storage sentence, word for word, in files 06, 07, 10 and 11, now following the label; a placed unit never moves to another office.
- M5, pantry owner: "In short" line; "I agree" reply as a signature; "can say yes to this" in place of a formal authority sentence; the page trimmed back to one Letter page with its signature block (rendered and viewed).
- M6, full four-person pass on the rendered pages and the notes: wording and placement only (the index's name-decision line, the handoff's state-answer line, the company note moved up in 11 and 12); stop rule met.

Independent review (`_review/round-1.md`, 2 blockers, 5 majors, 11 minors; per-finding response at the end of that file):
- R1, review round 1 (2026-10-24, changed files now version 0.6): biennial statement fee corrected to \$9, verified (LLC Law §1101(c), dos.ny.gov); the brand agreement's second standard payment now due at placement confirmation, the plan's term, in Part 1 and section 3 alike; Part 1 prints the T−10 cancel-by date, and the business-day reading of "ten days" is now an attorney question and a founder question; the brand's product liability cover, with us as additional insured, runs to 12 months after the window (or the latest best-by date), with a claims-made rule, and survives the campaign; the office page names the office's employer in its own slot, and offices sign only after the attorney clears the page (hour moved to Wed 2026-11-18); founding lock capped at 10 offices; shelf life counted on the drop day; slips never land a window on a blackout; the certificate note in file 11 follows sections 2(c) and 8 exactly; the Transparency Act's 30-day window now cites LLC Law §1107(d), which also asks an exempt company for an attestation; statute pinpoints in file 07 corrected; plan-sourced figures marked `plan estimate` with their plan section; HANDOFF gains the old-to-new file map; `check_pack.py` now fails when README, REPORT or HANDOFF is missing and warns about stale references in other folders. One finding rejected (R1-17: "eye level" is the plan's own placement standard).
- R1 verification pass (attorney, broker, inspector, pantry owner on the changed text and re-rendered pages): wording only (one repeated phrase in brand section 2(c); office page trimmed by three short phrases to stay on one page).

## 6 · What the attorney hour should cover

One hour, plan estimate \$300 to \$500 (not a quote). Book at Gate 0; hold by Fri 2026-11-20, before filing. Full agenda with facts, send-ahead note and answer log: `08-attorney-hour-agenda.md`.

1. **Before you file, about 20 minutes:** (1) keep or rename the working name, given the DeskDrop chocolate-gifting business and the USPTO's descriptiveness refusal of DESK-DROP, and whether a \$350-per-class federal application is worth it; (2) whether the Articles may name Albany County when the founder works from a borough (about \$1,400 at stake); (3) whether advance consent plus Schedule B releases the founder personally for agreements signed before formation; (4) one line confirming a U.S.-owned New York LLC files nothing under the LLC Transparency Act.
2. **Brand agreement, about 25 minutes:** (5) the \$100 and 50% cancellation terms and the double-slip rule as liquidated damages, not a penalty; (6) whether the cap at fees paid needs carve-outs to hold; (7) the indemnity's mishandling carve-out, and whether offices should be covered too; (8) the founding statement and case study under the Endorsement Guides, whether the FTC's consumer reviews rule applies (not researched), and an end date for the price lock; (9) the six-month non-solicit, two-year confidentiality, and a venue clause.
3. **Office page, privacy notice and footer, about 10 minutes:** (10) anything an office could read as a penalty or a legal conclusion, the "I agree" reply, and the promise to name buildings; (11) whether "anonymous" is the right word, and naming the form and link providers; (12) whether "This is a business pitch, sent one to one." identifies the email well enough.
4. **By email if time runs out:** (13) the operating agreement's death and incapacity clauses, and any bank notarization; (14) counting a weekend day 120, and what suspension blocks; (15) the no-employees statement, and primary and non-contributory or waiver of subrogation later; (16) claims-made product liability certificates.

## 7 · What the accountant hour should cover

One hour, plan estimate \$200 to \$400 (not a quote). Book at Gate 0; hold by Fri 2026-11-20, before the first invoice. Full list with facts checked and an answer log: `09-accountant-question-list.md`.

1. **Sales tax:** whether the campaign fee is a taxable information service, since the report compiles survey answers (Tax Law §1105(c)(1), which excludes advertising agents' services); whether holding the brand's product is taxable storage (§1105(c)(4)); when a Certificate of Authority would be needed (20 days before taxable sales begin); printing and the promotional-materials exemption; how cancellation fees and the founding testimonial are treated; what changes if product is ever sold to offices (candy and soda are taxable).
2. **Income tax:** 2027 federal, state and city estimates (federal threshold \$1,000 of expected tax, irs.gov); NYC Unincorporated Business Tax (4%, full credit if the liability is \$3,400 or less, NYC-202 filing threshold not shown on the city page, estimates, any credit against city income tax); the MCTMT threshold of \$150,000 from 2026; self-employment tax and when an S-corporation election might pay; the \$25 IT-204-LL fee for 2026, due Mon 2027-03-15 if owed.
3. **Books:** start-up and formation costs; cash or accrual, and deposits that straddle year end; records for car services, couriers and storage at home; Wave categories and card fees; W-9, 1099-NEC and 1099-K; a tax set-aside share.
4. **Before leaving:** one confirmed tax calendar for the first 18 months, and the cost of year-end preparation.

## 8 · Conflicts with the plan or CONTRACTS, and how they were resolved

1. **Founding-office offer versus the canonical calendar.** The plan promises offices a "first drop within four weeks of signing"; CONTRACTS moves campaign zero to Tue 2027-01-12. The office page names the drop week as a slot instead. E's copy should do the same.
2. **When to form the LLC.** The legal section says "at the first verbal brand yes"; the setup checklist lists "LLC filed" at the Gate 0 pass. Treated as one event expected around Gate 0, with dates for three filing days.
3. **When to call the state.** The setup checklist lists the call "At Gate 1 pass"; the order of operations says "before the first case arrives". Recommended by Fri 2026-11-20; deadline before any brand ships.
4. **Testimonial.** The plan's "written testimonial" became an honest written statement published with the founding-price disclosure (FTC Endorsement Guides).
5. **Operating rules kept out of the agreements:** "two misses means removal" and "credit the difference on the next campaign".
6. **The brief's office name.** The brief calls it the "Metro New York Food Safety and Inspection office"; the state's page lists the "Metro New York and Long Island Office" at the same number, (718) 722-2876 (verified 2026-10-23). File 07 uses the state's name.
7. **CONTRACTS 6.7 path.** The canonical name-check log is `01-name-check-log.md`; `name-check-log.md` stays at the CONTRACTS path as a pointer (HANDOFF, deviations).
8. **`unknown` in `figures.csv` money columns.** CONTRACTS section 5 asks for numbers, section 2 for `unknown` when a value cannot be confirmed; section 2 was followed.

## 9 · Verification

- `python3 desk-drop-legal-pack/_work/check_pack.py`: "15 documents and figures.csv checked, 0 findings" (heading, version, one name per file, slot form, heading numbers, changelogs, placeholders, ladder words, escaped dollars, every file reference resolves, every weekday matches its date, the shared storage sentence, `figures.csv` columns and statuses).
- `python3 desk-drop-legal-pack/_work/render_pack.py`: office page 1, operating agreement 4, brand agreement 3, privacy notice 1 (Letter). The guard found no dollar amount lost between .md and PDF. Every page image in `_work/png/` was looked at after the final render. The DOCX copies keep the heading, one name each and the dollar amounts.
- The 120-day tables in file 04 were recomputed: day 90, day 100, day 120 and the business-day offsets match for all three filing days.

## 10 · Questions for you, batched last

**Blocking** (each one stops a named step until you answer; my recommended default in bold):

1. **Keep "Desk Drop" or rename before printing and filing?** Blocks D's print run, C's launch and the LLC filing. **Default: treat it as taken. Shortlist two coined fallback names in week 1, run the log on each, and decide by Fri 2026-11-13; keep the working name only if the attorney says the risk is acceptable in the hour before filing.**
2. **Which [POSTAL ADDRESS]?** It goes in every cold email and in the LLC's six-week newspaper notice. Blocks the first outreach email. **Default: a USPS post office box or a registered private mailbox near the cluster, not your home; get a price and give your written yes before paying.**
3. **Which county will the Articles name?** Blocks filing and moves publication by about \$1,400. **Default: your own borough's county unless the attorney confirms Albany; budget New York County (\$1,745) until then.**
4. **Where would cases be stored, and do you have a car?** (Plan questions 2 and 3.) Blocks the GL quote description (file 06) and the state call (file 07). **Default: your apartment, no car; fill the facts sheets with that.**
5. **May I book both professional hours (about \$700 together, plan question 8) for week 4?** Blocks the hours. **Default: yes, book both at Gate 0 for the week of 2026-11-16.**

**Already decided by default** (answer only if you disagree):

- D1. Should the founding price lock expire? **Default: add "booked within 12 months after this campaign's window closes", after the attorney agrees.**
- D2. Short-shipment credit? **Default: leave it out; spread units evenly and tell the brand.**
- D3. Successor in the operating agreement? **Default: "the Member's executor or other legal representative" until you name someone.**
- D4. Survey retention periods (7 days, 30 days, 12 months)? **Default: keep them.**
- D5. Sign offices before the attorney hour? **Default: yes; re-send the page only if the attorney changes it in substance.**
