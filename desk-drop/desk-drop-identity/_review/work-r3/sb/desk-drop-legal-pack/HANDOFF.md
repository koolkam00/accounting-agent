**Draft for attorney review. Not legal advice.**

# Legal and admin pack: handoff

Version 0.8 · 2026-10-24 · Workstream G · folder `desk-drop-legal-pack/`

What this pack takes from other workstreams and what it gives them, with file paths and column names (CONTRACTS section 6.7). Deviations from CONTRACTS are marked **Deviation**.

## What G consumes

G needed nothing to start (prompt, "Handoffs"). It reads:

| From | What | Used in |
| --- | --- | --- |
| `plan.md` | Legal table, order of operations, appendices E and F, price table, setup checklist | Every file |
| `CONTRACTS.md` section 3 | Canonical calendar: week 1 Mon 2026-10-26; Gate 0 Fri 2026-11-13; Gate 1 Fri 2026-12-11; campaign zero drop Tue 2027-01-12, ship-by Tue 2026-12-22, hard T−10 Mon 2026-12-28; blackouts; business-day rule | All dates (each "derived, founder to confirm") |
| `CONTRACTS.md` section 4 | Category keys; the excluded list | `10` Part 1 "Category"; `03` section 4 and `10` section 2 product standard |
| `CONTRACTS.md` section 6.3 | `office_intake` columns `company`, `office_address`, `floor_suite`, `pantry_owner_name`, `pantry_owner_title`, `pantry_owner_is_contact`, `contact_phone`, `contact_email`, `receiving_type`, `receiving_window`, `coi_required` | Filling the top table of `03` |
| `CONTRACTS.md` section 6.4 | `paid_brands` columns (brand-intake columns plus `tier`, `price_usd`, `offices_count`, `payment_terms`, `unused_product_election`, `discount_code`, `landing_url`, `retailer_line`) | Filling Part 1 of `10` |
| H, `financial-model/` (optional) | A 12-month revenue estimate | The `[12-MONTH REVENUE ESTIMATE]` slot in `06` section 1 and `[FROM financial-model/]` in `09` section 1. Not yet read: fill when H publishes it |
| D, `desk-drop-identity/` | The email signature, once built, showing [POSTAL ADDRESS] | `02` footer B (if the signature lacks the address, use footer A) |
| F, `campaign-ops/` | The chosen form, short-link and e-signature tools | Naming the processors in `13` (attorney item 11) |

## What G feeds

### To H (financial model): `desk-drop-legal-pack/figures.csv`

Columns exactly as CONTRACTS 6.7: `item`, `low_usd`, `high_usd`, `working_usd`, `status` (`plan estimate`, `verified YYYY-MM-DD`, `needs quote`), `source_url`, `source_date`, `timing`, `notes`. 26 rows. Money is a plain number or `unknown` where no figure was found (CONTRACTS section 2: "A field you cannot confirm says unknown"); no figure is invented.

Working figures H most likely needs:

| item | working_usd | status | Note |
| --- | --- | --- | --- |
| `llc_articles_of_organization_fee` | 200 | verified 2026-10-23 | One-time, at filing |
| `llc_certificate_of_publication_fee` | 50 | verified 2026-10-23 | One-time, by day 100 |
| `llc_publication_newspapers_county_not_chosen` | 1745 | needs quote | New York County until the county is chosen; 345 if Albany is confirmed (attorney item 2) |
| `general_liability_insurance_annual` | 1200 | plan estimate | Plan's "roughly \$100 a month"; plan range 500 to 1,500; quote needed before binding |
| `food_warehouse_license_28d_two_years` | 400 | verified 2026-10-23 (fee only) | 0 if the state says no or brands ship direct (`07`) |
| `fda_food_facility_registration` | 0 | verified 2026-10-24 | New in review round 3. No fee (21 CFR 1.231(c)); applies only if cases are stored outside the founder's home |
| `attorney_hour` · `accountant_hour` | 400 · 300 | plan estimate | Attorney held by Wed 2026-11-18; accountant by Fri 2026-11-20 |
| `llc_biennial_statement_fee` | 9 | verified 2026-10-24 | Every two years from the filing month; first November 2028, outside the six-month model |
| `nys_llc_annual_filing_fee_it204ll` | 25 | verified 2026-10-23 | Possibly Mon 2027-03-15 for 2026 |

Rows with `unknown` (H should carry a placeholder, not a zero): `mailing_address_mailbox_annual`, `registered_agent_albany_if_used`, `hired_non_owned_auto_addon_annual`, `additional_insured_building_endorsement_each`.

**Changed in review round 3 (2026-10-24), for H to re-read:** `trademark_application_per_class` timing was wrong. It said "only after campaign zero passes; not in the first six months", but campaign zero passes at Gate 2 (Fri 2027-01-22), inside the six months. It now reads: plan setup checklist, after campaign zero if it was a pass (from about Mon 2027-01-25); plan legal table, after campaign one succeeds; the plan's six-month capital table has no trademark line; attorney to advise first. Both plan triggers fall inside H's window, so H's `Include = N` (`financial-model/HANDOFF.md` section 4, which cites "G times it outside the first six months") no longer has that reason: H's call whether to include \$350 as an optional line. New row `fda_food_facility_registration` (\$0). No other money figure changed. Brand terms that touch cash timing: the founding price is now due within five business days of our invoice (and before shipping), and a brand may cancel for a full refund if outside events move a drop more than once or by more than three weeks (`10` sections 3 and 8). Also seen by the round-3 reviewer: H's section 4 still lists `general_liability_insurance_annual` as "needs quote"; G's row has said `plan estimate` since review round 1 (same figures). That line is H's.

**Changed in review round 2 (2026-10-24), for H to re-read:** `llc_articles_of_organization_fee` timing is now "never before the attorney hour; earliest Thu 2026-11-19" (was "near Gate 0 Fri 2026-11-13"). No money figure changed. Two brand terms touch cash timing: the second standard payment is invoiced on our placement confirmation, sent by T+1 (H's `balance_lag_bd = 1` already matches), and an office not placed by T+1 is refunded or credited (\$150 standard, \$120 founding; `10` section 8), which H does not model (H's REPORT, "Not modeled: ... refunds").

**Changed in review round 1 (2026-10-24), for H to re-read:** `llc_biennial_statement_fee` is now 9, verified (was `unknown`); `general_liability_insurance_annual` status is now `plan estimate` (was `needs quote`; same figures); `ny_llc_transparency_act_filing` now cites LLC Law §1107(d) for its 30-day timing; `attorney_hour` timing is now by Wed 2026-11-18; plan rows now name their plan.md section in `source_url`. Totals check against the plan's capital table: state fees 250 (plan 250); publication 200 to 2,000 (plan 250 to 2,000); GL 500 to 1,500 (plan same); license 0 to 400 (plan same).

### To E (outreach engine)

| What | File | How E uses it |
| --- | --- | --- |
| Email footer and three-line checklist | `02-email-footer-and-checklist.md` | Footer A, or footer B under D's signature, on every outreach email and follow-up. Map `{BRAND_NAME}` to E's variable. [POSTAL ADDRESS] is required in every message. An opt-out sets `do_not_contact = Y` the same day. Omit [WEBSITE] until the site is public |
| Office agreement, sent at an office's yes with the intake form, **only once the attorney has cleared it** (hour held by Wed 2026-11-18) | `03-office-participation-agreement.md`, `rendered/03-office-participation-agreement.pdf` | Fill from the `office_intake` row (`company` goes in both [OFFICE LEGAL NAME] slots); record `agreement_signed_date`, `agreement_file` and `founding_roster_named` (Y if the first box in section 6 is ticked) in `signed_offices.csv` |
| The one-line "company is formed" email to every office signed before formation | `03` notes | Send once, the week the LLC is formed |
| Brand agreement and certificate request, sent together with the invoice at a brand's yes | `10-brand-campaign-agreement.md`, `rendered/10-brand-campaign-agreement.pdf`, `11-coi-request-brand-product-liability.md` | **Only after the LLC exists and after the attorney hour.** Record `agreement_signed_date`, `tier`, `price_usd`, `offices_count`, `payment_terms`, `unused_product_election` in `paid_brands.csv`; F records `coi_received_date` |

Suggested new columns (CONTRACTS 6: producers may add, never rename): in `paid_brands.csv`, `newsletter_option` (Y/N, from Part 1 of `10`) and `brand_privacy_url`; in both `signed_offices.csv` and `paid_brands.csv`, `agreement_version` (for example `0.7`), so a later attorney change can be traced to who signed which version; in `paid_brands.csv`, `coi_policy_end_date`, so the renewal certificate can be chased before the brand's cover period ends (`11` check).

**Conflict with plan text for E's copy:** the plan's founding-office offer, "first drop within four weeks of signing", cannot hold under the canonical calendar for offices signed after mid-November, because the first drop is Tue 2027-01-12. Use the slot `[DROP DATE: Tue 2027-01-12]`, as `03` does.

### To F (operations and measurement)

| What | File | What F must do |
| --- | --- | --- |
| Both agreements | `03`, `10` | Run the promises they make (list below) |
| Survey privacy notice and form settings | `13-survey-privacy-notice.md` | Build the form to Part D (D1 to D11): no sign-in, no email collection, office from the link, optional unticked email box only when the brand chose it, email-only export within seven days after T+4, deletion reminders: unticked emails within seven days after T+4 (new in review round 3), consented emails 30 days after they are passed on, answers at 12 months |
| Brand certificate check | `11` | Tick the five-minute check before confirming any ship date; record `coi_received_date`; if the policy ends before 12 months after the window (or the latest best-by date), diary the end date and chase the renewal certificate |
| Building certificate requests | `12` | For any office with `coi_required = yes` or `unsure`: start at least 10 business days before its first drop, only after GL is bound |
| Food safety call log | `07` | Use the logged answer (`yes`, `no`, `unclear`) for the storage decision. `unclear`, or no answer by Fri 2026-12-11, is treated as "license needed" for campaign zero: brands ship straight to each office, or the founder applies. Any storage place other than the founder's home (a storage unit, a consolidation point we run) also needs the FDA answer (follow-up 7): register before the first case arrives, or store at home |

Operating promises in the agreements that F's procedures must carry:
1. Placement within one business day, at eye level where the pantry allows, card in front (ask each office for this; `03` section 3 does); a placement photo from the day each office placed it (taken by us or by the office) and a later photo from day 3 or day 5, sent to the brand; top-up from reserve (`10` section 1).
2. Card text sent to the brand before printing; the allergen statement word for word, including any "may contain" line (`10` section 1).
3. On arrival: count, best-by dates, lot numbers, damage; no unit with under 60 days of shelf life left on the drop day is placed (`10` sections 2 and 5).
4. Storage: sealed cases at room temperature, clean, dry, off the floor, away from heat and as the label directs; units never opened, relabeled or stickered; sealed units may move between shipping cartons (`10` section 5).
5. A unit placed in one office never moves to another (`10` section 9).
6. A complaint: remove the product from that office and tell the brand the same day. A recall or pull request: remove it from every office within one business day, tell every office the same day and collect what is left, including units released to offices; the brand must tell us of a recall until 12 months after the window (`03` section 5, `10` sections 2(d) and 5).
7. Placement confirmation is our email to the brand, sent by T+1, listing the offices where the product was placed, each with its placement photo. The second standard payment is invoiced and due that day (the plan's "at placement confirmation"), and the report may wait for it. Any office not placed by T+1, and not replaced, comes off that invoice or is refunded: \$150 standard, \$120 founding (`10` sections 3 and 8). It can always be sent: an office whose photo has not arrived is not on the list. An office that placed by T+1 but whose photo arrives later is added by a short follow-up email and is not refunded; an office not placed by T+1 is refunded (`10` section 3).
8. Unused product: if the brand chose return and no prepaid label arrives within ten business days after the window, give unused reserve units to roster offices, and give collected leftovers back to the office they came from or dispose of them (`10` section 9; changed in review round 3, because a placed unit never moves to another office and `03` tells the office we collect). So leftovers can be held up to about six weeks in all for campaign zero (from about Tue 2026-12-22 to Tue 2027-02-02): the storage time stated to the insurers, the state and the accountant.
9. Cancellation: none from the drop day on. A brand that cancels after its product reached us has it returned at its cost or released, as it elected in Part 1 (`10` section 8). If outside events (weather, illness, a building closure) move a drop more than once, or by more than three weeks in all, the brand may cancel for a full refund (new in review round 3).
10. Per-office approval: an explicit yes for each office's first three drops, then each brand emailed at least five business days ahead and sent unless the office says no (`03` section 2).
11. If a building requires it, name its owner and managing agent as additional insureds and send the certificate before the first delivery there (`03` section 4).
12. Photos show only the shelf and display; no office is named outside the roster unless it ticked "publicly" (`03` section 6, `10` section 10).
13. Leaving: either side on seven days' notice; offices never store anything for us beyond the drop (`03` section 8).
14. Payment: confirm no ship date until the payment due on signing or before shipping has landed; the founding price is due within five business days of our invoice. If a payment is five business days late, the founder decides whether to cancel and refund (`10` Part 1 and section 3; new in review round 3).
15. Product standard at qualification: no alcohol, cannabis, CBD or THC, no Supplement Facts panel, and no health claim on the label or in the two card sentences, including structure or function wording; edit or decline card sentences that make one (`10` section 2(b); CONTRACTS section 4).

### To C (website)

- **Name gate: HOLD** (`name-check-log.md`, `01-name-check-log.md`). No public launch under the working name until the founder decides. The plan also keeps the site private until Gate 1.
- Host the full privacy notice (Part C of `13`) at `[PRIVACY URL]` if there is a site; otherwise F publishes it from the form tool.
- Never show an office's name unless that office ticked "publicly" in section 6 of `03`.

### To D (identity and collateral)

- **Name gate: HOLD for any commercial print run** (`name-check-log.md`, the path D's `brand.json` already cites). Test prints at home or a copy shop are D's own call.
- Tent card: the allergen statement copied word for word from the label, including any "may contain" line; only the brand's own two sentences (keeps the company inside the vendors endorsement's exclusions, `11`); proof to the brand before printing.
- Email signature: include [POSTAL ADDRESS] so footer B in `02` can be used under it.

### Notes for E and D on the brand terms

- **Cancel-by date.** The brand agreement's Part 1 now prints the cancel-by date (T−10). For standard runs, T−10 is the ship-by date, so D's proposal line "cancel before the ship-by date" (`desk-drop-identity/templates/proposal/proposal.html`) stays true. For campaign zero, brands are *asked* to ship by Tue 2026-12-22 but T−10 is Mon 2026-12-28 (CONTRACTS section 3): the cancel-by date is Mon 2026-12-28. State the date, not "the ship-by date", in campaign-zero copy. Part 1's ship-by row now reads "requested; no later than T−10", and the `10` notes give both campaign-zero dates.
- **Cancellation cut-off (new in review round 2).** No cancellation from the drop day on; the full price is then payable. D's proposal now says so (`desk-drop-identity/templates/proposal/proposal.html` line 265, "from the drop day the full price is due"; checked 2026-10-24). **For the orchestrator:** C's brand-page FAQ still ends "After that, we keep 50%." with no cut-off (`website/site/brands.html` line 313 and `website/COPY.md` line 271); suggested: "After that, we keep 50%, and from the drop day the full price is due." Those are C's files; `_work/check_pack.py` warns until they change.
- **Payment (changed in review rounds 2 and 3).** The second standard payment is still due at placement confirmation, the plan's term, defined as our email, sent by T+1, listing the offices where the product was placed, each with its photo, with any office not placed by T+1 refunded or credited. D's proposal (line 219) and C's `website/site/brands.html` (line 96) now carry this wording (checked 2026-10-24; no change needed). Round 3 adds two details that need no copy change: an office placed by T+1 whose photo arrives late is added by a follow-up email and not refunded, and the founding price is due within five business days of our invoice, before shipping (D's "Paid in full on signing, before you ship" still fits).
- **Name decision date.** Fallback names checked by Fri 2026-11-13; the name chosen by Wed 2026-11-18, at the attorney hour, which always comes before filing. D's `HANDOFF.md` line 11 still says "recommended by Fri 2026-11-13" (D's file; not wrong for the fallbacks, but the decision itself is 2026-11-18).
- **Founding lock.** \$120 per office for up to 10 offices on the next two campaigns (any beyond at \$150), as `desk-drop-identity/system/dd-offer.js` (`per_office: 120`, `locked_campaigns: 2`) and the financial model assume.

## File numbers changed on 2026-10-24

The merge renumbered every file into order of use. Other workstreams must cite the new names. The one stale reference found in review round 1 (D's `HANDOFF.md`, the footer under its old number) has since been fixed by D; on 2026-10-24 `_work/check_pack.py` finds no stale file reference in any other folder. It still lists any it finds as a warning, and since review round 2 it also warns where another folder restates a brand term in its old form.

| Old | New |
| --- | --- |
| `00-index.md` | `00-index.md` |
| `01-name-check-log.md` | `01-name-check-log.md` |
| `10-email-footer-and-checklist.md` | `02-email-footer-and-checklist.md` |
| `11-office-participation-agreement.md` | `03-office-participation-agreement.md` |
| `02-formation-checklist.md` | `04-formation-checklist.md` |
| `30-llc-operating-agreement.md` | `05-llc-operating-agreement.md` |
| `20-gl-quote-request-script.md` | `06-gl-quote-request-script.md` |
| `21-food-safety-call-script-and-log.md` | `07-food-safety-call-script-and-log.md` |
| (new) | `08-attorney-hour-agenda.md` |
| `22-accountant-question-list.md` | `09-accountant-question-list.md` |
| `12-brand-campaign-agreement.md` | `10-brand-campaign-agreement.md` |
| `14-coi-request-brand-product-liability.md` | `11-coi-request-brand-product-liability.md` |
| `15-coi-request-own-carrier-building.md` | `12-coi-request-own-carrier-building.md` |
| `13-survey-privacy-notice.md` | `13-survey-privacy-notice.md` |
| `name-check-log.md` | `name-check-log.md` (kept at the CONTRACTS 6.7 path) |

Because old and new numbers overlap (old 10 is new 02, while new 10 is the brand agreement), check the file's title, not only its number, when updating a reference.

## Deviations from CONTRACTS

- **Deviation, name-check log path.** CONTRACTS 6.7 names `desk-drop-legal-pack/name-check-log.md`. The full log is `01-name-check-log.md` (numbered in order of use, as the prompt requires); `name-check-log.md` stays at the CONTRACTS path as a pointer carrying the gate status. Both status lines must change together.
- **Deviation, `figures.csv` money columns.** `unknown` appears in `low_usd`, `high_usd` and `working_usd` where no figure exists. CONTRACTS section 5 asks for plain numbers; section 2 asks for `unknown` when a value cannot be confirmed. Section 2 wins here because an invented number would be worse.
- **Deviation, the footer is sent without the review heading (review round 2).** CONTRACTS section 2 says legal-adjacent text, footers included, carries "Draft for attorney review. Not legal advice." until an attorney clears it. The footer in `02` is pasted into every cold email from week 1, before the attorney hour, and pasted text cannot carry the heading (it would also tell every recipient the email is a draft). Default: email the three-line footer to the attorney in week 1 and ask them to clear it before the first send; if that is not possible, accept the small risk until the hour (attorney item 12; `REPORT.md`, conflict 13). E: use the footer exactly as written.
- No other deviations. Placeholders, dates, ladder words and the review heading follow CONTRACTS section 2.
