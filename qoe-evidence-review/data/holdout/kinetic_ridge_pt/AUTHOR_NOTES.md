# D3 holdout: Kinetic Ridge Physical Therapy Partners, LLC (SYNTHETIC)

SYNTHETIC — generated for QoE Evidence Review testing. Every company, person, amount and document is fictional.

- **Spec:** `data/specs/kinetic_ridge_pt.yaml`
- **Regenerate:** `uv run python scripts/qoe_generate_deals.py --spec data/specs/kinetic_ridge_pt.yaml --out data/holdout`. The output is byte-deterministic, and this file survives regeneration.
- **Split:** holdout. The answer key was written without reading the engine or AI code, the tests other than `tests/test_generator.py`, reports or workpapers, and without running the review engine on this deal.

## Profile

This is a central Indiana outpatient physical therapy group. It had 12 clinics until the Brownsburg clinic closed on Feb 27, 2026. Its headquarters and flagship clinic are in Zionsville. The company is an LLC taxed as a partnership, so there is no income tax line.

- **Owners and people.** Founder and CEO Dr. Adrienne Kowalczyk; CFO Brent Oyelaran; Controller Megan Sato. The CEO's spouse, Thomas Kowalczyk, owns Kowalczyk Family Realty, LLC, which is the landlord of the Zionsville and Noblesville buildings.
- **Books.** Xero. The GL is an Account Transactions xlsx (`xero_xlsx`) with 3,778 rows and P&L accounts only. The chart of accounts uses Xero export type codes (REVENUE, DIRECTCOSTS, EXPENSE, OVERHEADS, DEPRECIATN, OTHERINCOME). Management's monthly P&L is its Excel reporting pack, laid out with Xero's section names and Excel-date month headers.
- **Periods.** FY2024, FY2025 and TTM May-26 (Jun-2025 to May-2026). The data runs from 2024-01 to 2026-05. TTM shares Jun–Dec 2025 with FY2025.
- **Management schedule.** Refs are A-1 to A-16. The header columns are `#`, `Item`, `Type`, `Management commentary`, `Account(s)` and `Data room ref` (all SPEC §3.6 candidates). Support refs look like `VDR 3.2`.

| | FY2024 | FY2025 | TTM May-26 |
| --- | ---: | ---: | ---: |
| Net revenue (GL) | 28,493,513.49 | 29,917,791.36 | 30,392,029.20 |
| GL EBITDA | 4,159,249.00 | 4,333,136.35 | 4,282,125.21 |
| Management reported EBITDA (P&L basis) | 4,137,812.20 | 4,354,573.15 | 4,282,125.21 |
| Management adjustments (claimed) | 254,446.19 | 599,063.29 | 1,152,048.46 |
| Management adjusted EBITDA | 4,392,258.39 | 4,953,636.44 | 5,434,173.67 |
| Diligence finals, management items (excl. pending) | 171,206.19 | 432,961.29 | 543,396.46 |
| Diligence item D-1 (supported cut-off top-side) | (21,436.80) | 21,436.80 | 0.00 |
| **Diligence adjusted EBITDA** = GL EBITDA + finals + D-1 | **4,309,018.39** | **4,787,534.44** | **4,825,521.67** |
| Memo: pending REQUEST_INFO claims (A-4, A-9, A-16) | 51,000.00 | 109,000.00 | 521,000.00 |

The generator computes GL EBITDA and diligence adjusted EBITDA, and verifies every non-REQUEST_INFO amount against the GL rows. The rent normalizations are verified through `normalized_level`. I also recomputed every amount and the identity independently from the xlsx.

**Chart of accounts (P&L).**
- **Revenue:** 4000–4040 patient revenue by payer; 4100 refunds and recoupments (contra); 4200 employer onsite services.
- **Cost of sales:** 5000 clinical wages; 5100 supplies; 5150 contract therapy labor; 5200 billing and RCM.
- **Operating expenses:** 6000 front office and admin wages; 6010 officer; 6050 payroll taxes and benefits; 6100 rent; 6120 utilities; 6150 R&M and facility projects; 6200 insurance; 6300 software, EMR and IT; 6305 patient engagement platform (new Apr-2026); 6400 legal; 6410 accounting and advisory; 6450 recruiting; 6500 marketing; 6600 travel; 6700 dues; 6750 continuing education (typed "Overhead"); 6800 taxes and licenses (including real property tax on the two KFR buildings, paid directly under the absolute-net leases); 6850 bank and merchant; 6900 office, linen and phones; 6950 bad debt; 6995 year-end cut-off adjustments (management P&L only).
- **D&A:** 7000 Depreciation (DEPRECIATN); 7050 Amortization Expense.
- **Other:** 8000 Other Income (no activity); 8050 gain/loss on disposal; 8100 Interest Expense; 8200 Other Expenses. 8100 and 8200 are typed EXPENSE, as Xero has no Other Expense type.

## Catalog

Amounts are EBITDA-signed and shown as FY2024 / FY2025 / TTM May-26. GL rows are worksheet rows of `gl/general_ledger.xlsx`. "Must not" lists flags whose firing is an error; they are also recorded in each `reviewer_note`.

| Ref | Management claim | Planted facts | Truth |
| --- | --- | --- | --- |
| A-1 | **Related-party rent, Zionsville HQ and clinic** (normalization), 6100. Claimed 90,000 / 90,000 / 90,000. | Kowalczyk Family Realty bills $32,000 every month (29 rows, Ref `KFR-Z-yymm`, rows 1932…). The executed 2021 lease: 15,000 RSF, absolute net, fixed rent. Northfield's signed opinion of market rent: $19.60/RSF absolute net = $294,000/yr ($24,500/mo), independent, fee not contingent. The executed first amendment resets rent to $24,500 at closing. The same landlord also bills the $6,000 Noblesville rent. The Company pays the building's real property tax directly (Boone County Treasurer, 6800, May/Nov installments, rows 3386, 3389, 3393, 3396, 3402), so the lease and the benchmark compare like for like. | **ACCEPT 90,000 / 90,000 / 90,000** (384,000 − 294,000). Case ADEQUATE. This is the normalization positive control. Must not: NORMALIZATION_BENCHMARK_MISSING, UNSIGNED_OR_DRAFT_SUPPORT, RECURRING_PATTERN, OVERLAP (the KFR-N rows belong to A-2). |
| A-2 | **Related-party rent, Noblesville (below market)** (normalization), 6100. Claimed −39,000 in each period. | KFR bills $6,000/mo (29 rows, `KFR-N-yymm`). The executed 2019 lease (6,000 SF, absolute net, "not based on a market survey"). Brightwater's MAI appraisal: $18.50/SF = $111,000/yr ($9,250/mo). The executed amendment resets rent to $9,250 at closing. Real property tax is paid directly (Hamilton County Treasurer, 6800, rows 3387, 3390, 3394, 3397, 3403). | **ACCEPT −39,000 / −39,000 / −39,000** (72,000 − 111,000). Case ADEQUATE. Management's own EBITDA-reducing adjustment. Must not: SIGN_ERROR, NORMALIZATION_BENCHMARK_MISSING, RECURRING_PATTERN. |
| A-3 | **Brownsburg clinic closure** (pro forma, closed clinic), accts 4000, 4010, 5000, 6100, 6120, 6150, 6400. Claimed 115,966.19 / 177,787.29 / 213,472.46. | Brownsburg (acquired 2022) posts revenue monthly from a legacy billing system (4000/4010), and has its own payroll journals, Suite 110 rent ($9,400/mo to Eagle Creek) and utility account, 163 rows in all. The board memo says the last patient day is 2/27/26 and two of five clinicians move to Avon. It lists the stranded costs that are excluded: regional director, EMR enterprise fee, billing office, central supplies, and employer taxes and benefits. The lease termination agreement (3/2/26, executed): $38,250 fee, terminates 3/31/26. Closure costs: fee $38,250; Tate Whitcomb Matter 4471 $4,350 (one line of split invoice TW-26-0312, billing period Jan 5 – Mar 6, 2026); HRS equipment move $3,200; final pay and PTO $6,850. The final utility bill is Apr-10-2026, and there are no Brownsburg rows after it. TTM = $160,822.46 operating loss + $52,650 closure costs = $213,472.46. | **ACCEPT as claimed** (115,966.19 / 177,787.29 / 213,472.46). Case ADEQUATE. This is the realized pro forma positive control; ambiguity medium (the transferred clinicians' Avon revenue less their continuing cost is small and of uncertain sign; see the reviewer note). Must not: PRO_FORMA_NOT_REALIZED, SIGN_ERROR (revenue credits inside a net-loss add-back), RECURRING_PATTERN, OVERLAP on A-3. |
| A-4 | **Owner family payroll, T. Kowalczyk** (owner/discretionary), 6000. Claimed 51,000 in each period. | 58 semi-monthly payroll rows of $2,125, memo "(marketing coordinator)". The only support is the CEO's email: he is a full-time student, "doesn't work in the business", and "We don't have anything else to send". | **REQUEST_INFO.** Case NEEDS_INFO. Flag: NO_DOCUMENT_SUPPORT. The provisional amount is 51,000 per period, about 54.9k with employer taxes. It must not be accepted on the representation. |
| A-5 | **Transaction costs, Project Sycamore** (non-recurring), 6400 and 6410. Claimed 0 / 51,000 / 88,800. | Larchmont one-time retainer $30,000 (Oct-25; "fully creditable against the Success Fee", "No monthly or periodic fees"). Brennan Oakes sell-side QoE, $42,000 fixed fee in two $21,000 installments (Nov-25, Jan-26). Tate Whitcomb Matter 4468 $16,800 (engagement letter dated January 5, 2026), the Sycamore line of TW-26-0312 (Mar-26; billing period Jan 5 – Mar 6, 2026, so no service month crosses a fiscal year-end). Tate Whitcomb also bills an unclaimed $1,500/mo Matter 1102 general counsel retainer "continuing until terminated". | **ACCEPT 0 / 51,000 / 88,800.** Case ADEQUATE. These are false-reject traps. Must not: CONTINUING_OBLIGATION, RECURRING_PATTERN, OVERLAP (the split invoice's other line is A-3's). Related rows: the 29 retainer rows. |
| A-6 | **Carmel clinic relocation** (non-recurring), 6100, 6150 and 6300. Claimed 0 / 37,950 / 37,950. | HRS-25-0814 posts as three GL lines: move crews $18,400 and equipment reinstall $9,600 (6150), plus storage for Aug–Oct 2025, $3,450 = 3 × $1,150 (6100). The invoice says storage continues at $1,150/mo "until stored items are released", and HRS bills $1,150 monthly from Nov-2025 (7 unclaimed rows). Monon Trail Networks cabling is $6,500 in the GL, but the invoice totals $6,955.00, including $182 freight and $273 sales tax. | **REVISE 0 / 34,500 / 34,500.** Case PARTIAL. Flags: CONTINUING_OBLIGATION (storage line) and DOC_GL_AMOUNT_MISMATCH (Monon; a question only, and the GL amount is carried). CONTRADICTORY_EVIDENCE via entry qualification is an acceptable extra flag for the storage removal. |
| A-7 | **Fishers clinic water damage** (non-recurring), 6150. Claimed 0 / 0 / 41,850. | Burst pipe 1/24/26. Circle City Restoration $24,600 (Feb-26) and Hamilton County Flooring $17,250 (Mar-26), both citing claim PSM-26-004417. The insurer's letter (4/8/26) confirms coverage and estimates a $31,850 payment after a $10,000 deductible: "The claim remains open." The 5/28/26 email says "Nothing received yet and nothing booked in Xero." | **ACCEPT 0 / 0 / 41,850**, with questions on recovery timing, the working-capital treatment of the receivable, and business income. Case ADEQUATE. This is the pending-recovery trap. Must not: OFFSETTING_RECOVERY. Reducing the add-back by 31,850 understates TTM. |
| A-8 | **Maddox non-compete litigation** (non-recurring), 6400. Claimed 0 / 52,000 / 39,400. | Stanton Reyes invoices $12,600 (Apr-25), $16,400 (Jun), $13,900 (Aug), $9,100 (Oct). Kinetic Ridge v. Pruitt 2024 via Barlow & Finch: $44,400 in four invoices, Mar–Jul 2024. Kinetic Ridge v. Grant 2026 via Hargrove Lindqvist: $20,000 (Feb, Apr-26). Each year uses a different firm, but the account and the non-compete/restrictive-covenant theme are the same. The general counsel's litigation summary says "we expect one to two enforcement matters per year" and that they are not insured. | **REJECT 0 / 0 / 0.** Case RECURRING. Flags: RECURRING_PATTERN (account + theme; FY24 44,400 ≥ 50% of 52,000) and CONTRADICTORY_EVIDENCE (litigation summary). |
| A-9 | **Brand refresh** (non-recurring), 6500. Claimed 0 / 58,000 / 58,000. | Copperline Creative Studio bills $18,500 (Aug-25), $22,000 (Sep), $17,500 (Oct); these are Copperline's only rows. The only document is the CEO's email: a "one-time rebrand" with "I don't think we ever signed a formal SOW". There are no invoices or SOW in the data room. | **REQUEST_INFO.** Case NEEDS_INFO. Flag: NO_DOCUMENT_SUPPORT. This is the clean test: the GL ties 100% and the support is a management representation only. |
| A-10 | **Loss on sale of outreach vans** (non-recurring), 8050. Claimed 0 / 27,600 / 27,600. | 8050 has three rows: an $8,400 gain on two vans (Mar-24), a $27,600 loss on five vans (Oct-25; bill of sale $78,650 vs NBV $106,250) and a $4,900 gain on a dynamometer (Apr-26). The disposal schedule lists all three and says "As in prior years, gains and losses are recorded in 8050". | **REVISE −8,400 / 27,600 / 22,700.** Case NON_OPERATING. Flag: OFFSETTING_RECOVERY (the two gains are carried as recoveries, related rows 3720 and 3722; the loss is row 3721). Must not: RECURRING_PATTERN. |
| A-11 | **Use-tax audit assessment** (prior period), 6800 and 8100. Claimed 0 / 27,876 / 27,876. | Notice NPA-2025-448812 covers the audit period 1/1/24–12/31/24. Tax $23,840 (6800, row 3398), 10% penalty $2,384 (6800, row 3399) and interest $1,652 (8100, row 3768), all booked 11/18/25. | **REVISE −23,840 / 26,224 / 26,224.** Case OUT_OF_PERIOD; ambiguity medium. The tax is two-sided out-of-period (a 2024 cost), the penalty is added back where booked (it is a charge of the 2025 assessment and is not moved), and the interest is already excluded. Flags: OUT_OF_PERIOD, ALREADY_EXCLUDED_FROM_EBITDA. Must not: RECURRING_PATTERN. |
| A-12 | **Q4 2023 contract therapy invoice** (out-of-period), 5150. Claimed 36,480 / 0 / 0. | Crossfield CMS-24-0209R, booked 2/9/24. "Service period: October 2, 2023 – December 29, 2023"; rebilled after a timesheet dispute. This is Crossfield's only row. Routine per diem staffing in 5150 is a different vendor (Summit Allied, 59 rows). | **ACCEPT 36,480 / 0 / 0.** Case OUT_OF_PERIOD. Flag: OUT_OF_PERIOD. The service months fall before data_start, so no negative side is carried (over-adjustment trap). Must not: any negative amount, RECURRING_PATTERN (Summit Allied's per diem work recurs, including Lafayette coverage of $20,980.18 in FY2025, but a cut-off correction is not a non-recurrence claim). |
| A-13 | **Term loan prepayment premium** (non-recurring), 8200. Claimed 0 / 18,500 / 18,500. | The Harvest Plains payoff letter shows a prepayment premium of $18,500 (1.0% of $1.85M). It is booked in 8200 Other Expenses, which is inside EBITDA; it is the only 8200 row (row 3783). Accrued payoff interest of $9,314.24 is in 8100 and not claimed. | **ACCEPT 0 / 18,500 / 18,500.** Case ADEQUATE. This is the contrast case to D1 M-07. Must not: ALREADY_EXCLUDED_FROM_EBITDA. |
| A-14 | **Bad debt, Midstate Employer Health Network** (non-recurring), 6950. Claimed 0 / 46,350 / 46,350. | The employer customer entered receivership 9/22/25, and the receiver expects nothing for unsecured creditors. The claim form lists INV-30208, INV-30214 and INV-30220 (Jun–Aug 2025, $15,450 each), and the write-off is Nov-25. Routine patient write-offs are $1.9k–3.7k a month. | **ACCEPT 0 / 46,350 / 46,350.** Case ADEQUATE; ambiguity medium. This is a false-reject trap: one large write-off (row 3654) among small routine entries. Must not: RECURRING_PATTERN. Pre-registered alternative: REVISE −19,240.17 / 26,101.83 / 27,521.83 (6950 at its 29-month average). |
| A-15 | **Brownsburg lease termination fee** (non-recurring), 6100. Claimed 0 / 0 / 38,250. | This is the same $38,250 row (2251) that A-3 claims. Both A-3 and A-15 cite VDR 3.2 and 3.3 and account 6100, and both descriptions name the fee. {2251} is the only TTM 6100 fit for $38,250 (no subset of the other 150 TTM 6100 rows sums to it). | **REJECT 0 / 0 / 0.** Case OVERLAP; ambiguity medium. Flag: OVERLAP_WITH_OTHER_ADJUSTMENT. A-15's entire claim is inside A-3, so A-15 is the duplicate and the fee stays in A-3. Joint pre-registered alternative: A-15 ACCEPT 0 / 0 / 38,250 with A-3 REVISE 115,966.19 / 177,787.29 / 175,222.46 + OVERLAP, scored as a pair. |
| A-16 | **Pro forma: Wabash Valley Sports Rehab acquisition** (pro forma), no GL accounts. Claimed 0 / 0 / 412,000. | The APA was executed 4/22/26. Closing is "on July 1, 2026", conditioned on Medicare enrollment, payer credentialing, landlord consents and buyer financing (APA §4(c), not addressed in the email); the first three are outstanding per the CFO's 5/29/26 email ("Nothing has been paid and nothing is in our books yet"). The seller's TTM Mar-26 summary is "Not audited or reviewed" and on a cash basis. There is no GL activity. | **REQUEST_INFO.** Case NEEDS_INFO. Flags: NO_GL_SUPPORT, PRO_FORMA_NOT_REALIZED. The pre-registered alternative is REJECT 0/0/0. |

**Case mix.** ADEQUATE items (clean ACCEPT controls) are A-1, A-2, A-3, A-5, A-7, A-13 and A-14: 7 of 16, or 44%. A-12 is also an ACCEPT, but its case type is OUT_OF_PERIOD.

**False-reject traps:**
- A-5: a one-time retainer creditable against the success fee; a fixed fee paid in installments; a law firm that also bills an unclaimed continuing retainer.
- A-7: a pending recovery.
- A-12: a one-sided out-of-period item.
- A-13: an 8200 penalty inside EBITDA.
- A-14: one large write-off among routine write-offs.
- A-2: a negative normalization, which must not be read as a sign error.

## D3 coverage (from the D1 panel's case list)

| Case | Item |
| --- | --- |
| Normalization positive control: related-party rent, executed lease plus independent benchmark → ACCEPT | A-1 |
| Management's own EBITDA-reducing adjustment: below-market rent, appraisal → ACCEPT the negative | A-2 |
| Closed branch, lease terminated Mar-2026, stranded costs excluded → ACCEPT | A-3 |
| Pro forma tuck-in with a signed APA and no GL → REQUEST_INFO | A-16 |
| One-sided out-of-period (FY2023 service booked in FY2024) → ACCEPT, no negative side | A-12 |
| Recovery still pending at data_end → question only, amount unchanged | A-7 |
| Contrast case: prepayment penalty in 8200 (inside EBITDA) → ACCEPT | A-13 |
| Theme-level recurrence across counterparties → REJECT via RECURRING_PATTERN | A-8 |
| Documents limited to a management representation → REQUEST_INFO (NO_DOCUMENT_SUPPORT) | A-9 (also A-4) |
| Partial qualification inside one invoice (continuing storage lines) → REVISE; invoice vs GL freight/tax mismatch → question | A-6 |
| Non-operating 8050 loss added back while gains are ignored → REVISE to net | A-10 |
| Family member on payroll, management representation only → REQUEST_INFO | A-4 |
| Prior-period use-tax assessment: two-sided tax, penalty inside EBITDA, interest in 8100 → REVISE | A-11 |
| Duplicate listing (A-15's whole claim is inside A-3); one invoice split across two adjustments | A-15 / A-3; TW-26-0312 split between A-3 (Matter 4471) and A-5 (Matter 4468) |
| False-reject traps (at least two); ADEQUATE items at 40% or more | see above (7 of 16) |
| Xero data quality: UNMAPPED_ACCOUNT, PL_ACCOUNT_NOT_IN_GL, GL_ACCOUNT_NOT_IN_PL, cut-off misposting across the FY24/FY25 year-end | see below |

## Planted data-quality issues

| Code | Locator | In `ground_truth.json`? | Detail |
| --- | --- | --- | --- |
| RECON_VARIANCE | 2024-12, 6995 | yes | Cut-off top-side of +21,436.80 (management P&L only). |
| RECON_VARIANCE | 2025-01, 6995 | yes | Its reversal, −21,436.80. |
| RECON_VARIANCE | 2026-04, 6305 and 6300; 2026-05, 6305 and 6300 | yes (4 entries) | Reporting-pack mapping: the Stridewise charge of $2,150/mo in Xero account 6305 (rows 2843–2844) is shown inside 6300. It nets to zero in EBITDA. |
| MGMT_EBITDA_DIFFERS_FROM_GL | period level | yes | FY2024 −21,436.80; FY2025 +21,436.80; TTM 0. |
| **Cut-off misposting** across the FY2024/FY2025 year-end | GL row 1511 | via D-1 and the two 6995 RECON_VARIANCE entries | Lakeshore invoice LRC-2412 (services Dec 1–31, 2024; invoice dated 12/31/24; stamped received Jan 08 2025) was entered in Xero on 2025-01-08. As a result, January 2025 has two Lakeshore bills (rows 1511 and 1512) and December 2024 has none. The outside accountant's email documents the fix in the reporting pack. |
| PL_ACCOUNT_NOT_IN_GL | 6995 Year-End Cut-Off Adjustments | **no** (the generator cannot express this code; panel decision: derive it in the generator) | The account is in the chart of accounts and management's P&L but has zero Xero GL activity. |
| GL_ACCOUNT_NOT_IN_PL | 6305 Patient Engagement Platform | **no** (the generator cannot express this code; panel decision: derive it in the generator) | The account has two GL rows (Apr and May 2026), and management's P&L has no 6305 line. |
| UNMAPPED_ACCOUNT | 6750 Continuing Education & Licensure | **no** (the generator cannot express this code; panel decision: derive it in the generator) | Its chart-of-accounts type is "Overhead" (Xero's UI label, hand-edited in the 2023 migration) rather than the export code OVERHEADS that every other account uses. The label is not in the SPEC §3.4 type list, so ingest should fall back to OPEX and raise UNMAPPED_ACCOUNT. There is no EBITDA effect, and there is no overrides file. |

There are no duplicate postings. The generator asserts that no unplanted duplicate group exists. Six pairs of consecutive weekly EMR revenue batches are identical to the cent (rows 114/115, 261/262, 473/474, 489/490, 581/582, 585/586); they are an artifact of the generator's weekly split, not planted, and a panel decision asks for a generator fix (see Panel review). Multi-line Xero invoices (HRS-25-0814 with 3 lines, TW-26-0312 with 2 lines, NPA-2025-448812 with 3 lines, HPB-PAYOFF-0926 with 2 lines) share a Reference, but their lines have different amounts, so they are not duplicates.

## Diligence items (SPEC §5.7)

| Id | What | Amounts | GL rows | Support |
| --- | --- | --- | --- | --- |
| D-1 | Supported management top-side: the Lakeshore December 2024 invoice, moved from Jan-2025 back to Dec-2024 | −21,436.80 / +21,436.80 / 0 | supporting 1511 (period move to 2024-12) | invoice LRC-2412 (service period Dec 1–31, 2024; received Jan 08 2025) and the Whitlock Haas email (1.1) |

With `dil_recon` at +21,436.80 / −21,436.80 / 0, GL EBITDA + `dil_recon` + D-1 equals management's reported EBITDA. The 6305→6300 mapping top-side is EBITDA-neutral, so it is not a diligence item.

## Generator facts the key relies on

These were checked in the generated GL:
- 8000 has no activity. 8200 has exactly one row, the prepayment premium (row 3783). 8050 has exactly the three disposals (rows 3720–3722).
- 6800 has 20 rows: licences, business personal property tax (County Treasurer), the ten real property tax installments on the two KFR buildings (Boone and Hamilton County Treasurers), and the use-tax tax and penalty rows. No use-tax self-assessment appears in 2025–26.
- 5150 has two vendors: Crossfield (1 row, the A-12 invoice) and Summit Allied (59 per diem rows).
- Within EBITDA, the only rows on the non-compete / restrictive-covenant theme are the 10 legal rows for Pruitt, Maddox and Grant; the 29 amortization rows in 7050 (outside EBITDA) also mention non-compete. Tate Whitcomb's retainer memos do not use that theme.
- Every GL description containing "Brownsburg" (163 rows) is in A-3's supporting set. The last one is the final utility bill on 2026-04-10.
- Copperline has only its three rows. Midstate's billing stops after Aug-2025.
- The related-party rent is exactly 29 × $32,000 and 29 × $6,000.
- 6950 totals $125,046.00 over 29 months (30 rows: 29 routine patient write-offs plus the Midstate write-off); FY2024 $32,503.00, FY2025 $77,845.00, TTM $79,265.00.

## Ambiguity and alternatives

| Item | Ambiguity | Note |
| --- | --- | --- |
| A-3 | medium | Two clinicians moved to Avon; their Avon revenue less continuing cost (R − C) is about −$1.5k/month at Brownsburg's ratio, sign uncertain, so no alternative amount is registered beyond the joint A-3/A-15 pair. Unclaimed employer taxes and benefits on the three eliminated positions (about $25k/yr) are seller upside. Realism limitation: Brownsburg revenue is below its clinical payroll (a failing acquired practice, visits down about 10% a year). This makes the transferred-clinician question slightly buyer-adverse. Fix in a later deal. |
| A-4, A-9 | medium | Teams often carry these once HR records or invoices arrive. That counts as new information, not a tool error. |
| A-11 | medium | FY2024 −23,840 is an upper bound (use tax on capitalized equipment belongs in asset cost). Unassessed 2025–26 use tax is a debt-like / indemnity / run-rate question. No alternative registered. |
| A-14 | medium | Pre-registered: REVISE −19,240.17 / 26,101.83 / 27,521.83 (6950 at its 29-month average). Not registered: 0/0/0 netting; buyer run-rate removal of Midstate's TTM revenue of $46,350. |
| A-15 | medium | Joint pre-registered alternative with A-3 (see A-15). |
| A-16 | medium | Pre-registered alternative: REJECT 0/0/0 (same EBITDA effect). |
| All others | low | |

## Generator gaps for this deal (requested changes)

1. **UNMAPPED_ACCOUNT, PL_ACCOUNT_NOT_IN_GL and GL_ACCOUNT_NOT_IN_PL answer-key entries.** All three issues are planted in the package, but `truth._data_quality` only emits DUPLICATE_GL_ENTRY, RECON_VARIANCE, MISSING_PERIOD, MGMT_EBITDA_DIFFERS_FROM_GL and MGMT_SCHEDULE_ARITHMETIC. The fix is to derive them from the spec:
   - GL_ACCOUNT_NOT_IN_PL: accounts with GL rows but no P&L line.
   - PL_ACCOUNT_NOT_IN_GL: P&L accounts with no GL rows.
   - UNMAPPED_ACCOUNT: P&L accounts whose type is outside the SPEC §3.4 list, with no override.

   Expected entries once supported: `{UNMAPPED_ACCOUNT, account 6750}`, `{PL_ACCOUNT_NOT_IN_GL, account 6995}`, `{GL_ACCOUNT_NOT_IN_PL, account 6305}`.
2. **A truly custom account type.** An account type outside the generator's own type list, such as "Clinical Wages (custom)", is treated as balance sheet, and a forced `ebitda_class` writes `account_mapping_overrides.csv`, which suppresses the UNMAPPED issue. A flag such as `unmapped: true` would let a P&L account have a custom type without an override row. Until then, 6750 uses the "Overhead" display label, which the generator maps but SPEC §3.4 does not list.
3. **Flow-list parsing in D1.** In a YAML flow list, a bare `Attn: Name` parses as a mapping and renders as `{'Attn': ...}` in PDFs. I quoted every such entry here. `data/specs/meridian_mechanical.yaml` has the same pattern in four places: the Barrow, Keel Harbor and Dunmore & Pike invoices and the Halvorsen notice. The committed D1 PDFs show `{'Attn': 'Richard Castellano'}`. A generator check that rejects mappings inside address lines would catch it.
4. **Identical consecutive weekly batches.** The allocate-mode weekly split sometimes gives two adjacent slots the same amount to the cent (six pairs in 4000, 4010, 4030 and 4040 here). Requested: a sum-preserving tie break within the month (shift cents between adjacent slots) and an assertion that no two rows in one account within 7 days have identical amounts unless planted. This cannot be done from YAML: changing a stream's `spread` re-draws its monthly totals, and in a trial the tie simply moved to another month.
5. **Claimed-set uniqueness assertion.** A check that each pass-through claim's rows are the unique fit under the SPEC §5.3 tie-break (D1 M-08 precedent) would have caught the A-15 collision at $38,000. This deal now avoids it by amount ($38,250).

## Panel review

The engagement partner adjudicated 43 findings from three reviewers (R1 14, R2 11, R3 18) into 33 decisions: 17 CHANGE, 12 NOTE and 4 REJECT. I applied them on 2026-09-28 under the holdout author's rules: YAML and this file only, no generator code, no SPEC.md or `qoe/schemas.py` edits, no engine, AI code, tests (other than `tests/test_generator.py`), reports or workpapers read, and the review engine not run. Where a decision needs code, SPEC text or the study-folder `key_alternatives.csv`, the deal part is applied and the rest is listed under "Open requests" below.

### Effect on the package and the key

| | FY2024 | FY2025 | TTM May-26 |
| --- | ---: | ---: | ---: |
| GL EBITDA, before | 4,236,342.02 | 4,411,657.27 | 4,361,799.47 |
| Real property tax planted in 6800 (KFR buildings) | (77,093.02) | (78,520.92) | (79,424.26) |
| A-15 fee $38,000 → $38,250 (row 2251) | – | – | (250.00) |
| GL EBITDA, after | 4,159,249.00 | 4,333,136.35 | 4,282,125.21 |
| Management reported EBITDA, after | 4,137,812.20 | 4,354,573.15 | 4,282,125.21 |
| Management claims, after (A-3 and A-15 each +250 in TTM) | 254,446.19 | 599,063.29 | 1,152,048.46 |
| Diligence finals, management items, after | 171,206.19 | 432,961.29 | 543,396.46 |
| Diligence adjusted EBITDA, before | 4,386,111.41 | 4,866,055.36 | 4,904,945.93 |
| Diligence adjusted EBITDA, after | 4,309,018.39 | 4,787,534.44 | 4,825,521.67 |

- **Treatments.** No treatment changed. ACCEPT 8, REVISE 3, REJECT 2, REQUEST_INFO 3; D-1 REVISE. The only amount change is A-3 TTM 213,222.46 → 213,472.46, from the $38,250 fee.
- **Flags.** A-10 now expects OFFSETTING_RECOVERY. Ambiguity rose to medium on A-11 and A-15.
- **The tax plant.** Installments are about $30k (Zionsville) and about $9k (Noblesville), stepping up slightly each year: 29,684.37 / 30,212.56 / 30,948.18 and 8,862.14 / 9,047.90 / 9,215.62. The EBITDA effect is therefore 77,093.02 / 78,520.92 / 79,424.26 rather than the partner's illustrative flat 78,000.
- **Row renumbering.** The GL now has 3,778 rows. Every 6800 row from 3386 on and everything after it shifted:
  - A-1 related: 3386, 3389, 3393, 3396, 3402. A-2 related: 3387, 3390, 3394, 3397, 3403.
  - A-11: supporting 3398, 3399 (were 3390, 3391); related 3768 (was 3758).
  - A-10: supporting 3721 (was 3711); related 3720, 3722 (were 3710, 3712).
  - A-13: supporting 3783 (was 3773); related 3763 (was 3753).
  - A-14: supporting 3654 (was 3644).
  - Unchanged: KFR-Z from 1932, 2251, 1511/1512, 2843–2844, 2881–2882, 921/927/933, 3073/3078/3082.
  - `ground_truth.json` resolves every row reference from keys at generation.
- **Re-run checks, all against the generated xlsx:**
  - GL EBITDA moved by exactly the planted tax plus the $250 fee, and diligence adjusted EBITDA by the tax only.
  - A-15: 208,045 subsets of the 151 TTM 6100 rows summed to $38,000, which confirms R2/R3. At $38,250, no subset of the other 150 rows reaches it.
  - A-11: FY2025 has exactly one 6800/8100 subset summing to $27,876, the three NPA-2025-448812 rows. TTM has eight, the same eight as before the plant, and none uses a new tax row. Every alternative includes a Jan–May 2026 row, so it cannot also sum to $27,876 in FY2025; only the NPA set fits FY2025 and TTM together.
  - 6950 at its 29-month average gives −19,240.17 / 26,101.83 / 27,521.83.
  - Summit Allied Lafayette FY2025 is $20,980.18. 5150 excluding Crossfield is $167,303.28 in FY2025.
  - All 29 rows in 7050 mention non-compete.
  - There are 163 Brownsburg rows, all in A-3, the last on 2026-04-10.
  - xlsx metadata is dated 2026-06-05.
  - `uv run pytest -q tests/test_generator.py`: 30 passed.

### Decision log

| # | Item | Decision | What changed |
| --- | --- | --- | --- |
| 1 | A-1 / A-2 real-estate tax and absolute-net basis | CHANGE | **Applied.**<br>- **Package:** ten planted rows in 6800 (`retax_zville_*`, Boone County Treasurer; `retax_nobles_*`, Hamilton County Treasurer), May 8 and Nov 8 for 2024 and 2025, and May 8, 2026. The 2.7 footnote is reworded as decided. Optional (c) is also applied: the Prairie State Mutual BOP memo (29 rows in 6200, description only) now names the Zionsville and Noblesville buildings.<br>- **Key:** tax rows added to A-1 and A-2 related_gl_rows, and the like-for-like sentence added to both rationales. Treatments, amounts and ambiguity are unchanged. |
| 2 | A-1 straight-line rent; seller-commissioned benchmark | NOTE | **Applied.** A-1 reviewer_note appended (year-1 market cash rent; straight-line about $329.4k a year, about $54.6k on that basis; not pre-registered). |
| 3 | A-3 transferred clinicians, minority-view direction, employer-tax upside | NOTE | **Applied.**<br>- The reviewer_note text after the must-not list is replaced (R and C analysis; joint alternative, see A-15; about $25k a year on the three eliminated positions).<br>- Question topic 1 is replaced.<br>- For consistency with decision 15, the must-not parenthetical now says A-15 is the duplicate instead of citing the schedule-order tie-break. |
| 4 | A-3: R2 buyer amounts, R3 note wording | REJECT | No action. |
| 5 | A-3 Brownsburg clinic economics | NOTE | **Applied.** The realism limitation is recorded in the ambiguity table. A-3 is not regenerated. |
| 6 | A-5 / A-3 TW-26-0312 billing period crossing FY2025 year-end | CHANGE | **Applied.**<br>- 5.7 Billing Period is now "Jan 5 – Mar 6, 2026".<br>- 5.6 is dated January 5, 2026.<br>- Filenames and the key are unchanged. |
| 7 | SPEC §5.4 OUT_OF_PERIOD scope; A-11 penalty | CHANGE | **Key applied:** the A-11 reviewer_note says only the tax row moves (see 17). **SPEC text not applied** (open request 1). |
| 8 | A-4 / A-9 NO_DOCUMENT_SUPPORT reachability | CHANGE | **Key applied:** both reviewer_notes now carry the "reachable under the §5.4 management-representation rule" sentence. **SPEC text not applied** (open request 2). Until it lands, a spec-following tool can still link 4.1 and 8.1 as support. |
| 9 | A-9 provisional amount; sell-side ACCEPT view | NOTE | **Applied.** The rationale's last sentence is replaced ($58.0k is a ceiling) and the reviewer_note is appended (GL corroboration is not support; not pre-registered). |
| 10 | A-4 payee identity | NOTE | **Applied.** Question topic added (payroll register and W-2; "T. Kowalczyk" vs Thomas Kowalczyk). |
| 11 | A-12 (and A-11) RECURRING_PATTERN must-not | CHANGE | **Key applied:** A-12 reviewer_note replaced. **SPEC exemption not applied** (open request 3). The Crossfield memo is not re-themed. A-11's must-not now also relies on the exemption: the literal account leg passes on 6800 (FY2024 $94.0k with the plant, $16.95k before). |
| 12 | A-14 RECURRING_PATTERN must-not determinacy | NOTE | **Applied.** The theme-versus-account sentence is inserted after the must-not. The package is unchanged, and the routine write-offs are not lowered. |
| 13 | A-14 pre-register the 29-month-average alternative | CHANGE | **Key applied:** the reviewer_note alternatives sentence is replaced (pre-registered REVISE plus the unregistered buyer view). The amounts are re-verified; the tax plant does not touch 6950. The key_alternatives row is listed below for lock. |
| 14 | A-14 netting 0/0/0 as an alternative | REJECT | No action. The view stays in the reviewer_note as "not registered". |
| 15 | A-15 / A-3 overlap tie-break | CHANGE | **Applied.**<br>- A-15 ambiguity is now medium.<br>- The rationale's closing sentences are replaced with the partner's sentence. The unverifiable "links are equal, schedule-order tie-break" sentence is dropped.<br>- The reviewer_note is replaced. Its amounts are 38,250 and 175,222.46, per decision 16.<br>- The joint alternative is listed below for lock.<br>- The optional OVERLAP clarification is open request 4. |
| 16 | A-15 $38,000 claimed-set collisions in TTM 6100 | CHANGE | **Fallback applied** (a generator assertion needs code).<br>- The fee is now $38,250 in: the planted row; 3.2 (text and key phrase); 3.3 (line and key phrase); 3.4 (fee line, total, text and key phrase); the schedule's A-3 description and TTM claim (213,472.46); and A-15's description and claim (38,250).<br>- **Key:** A-3 TTM 213,472.46; A-3 rationale ($52.65k closure costs, $213.5k); A-15 rationale and question topic.<br>- Uniqueness is verified as above. |
| 17 | A-11 amounts, ambiguity, capital share, ongoing use tax | NOTE | **Applied.**<br>- Ambiguity is now medium.<br>- The reviewer_note is replaced.<br>- A question topic on the capitalized share of the $340,571.43 is added.<br>- Amounts are unchanged. |
| 18 | A-11 alternatives (one-sided, buyer run-rate, penalty moved) | REJECT | No action. None is registered. |
| 19 | A-10 removal of the gains | CHANGE | **Key applied:** expected_flags is [OFFSETTING_RECOVERY] and the reviewer_note is replaced. Rows are unchanged (supporting 3721; related 3720, 3722). **SPEC extension not applied** (open request 5). |
| 20 | A-10 move gain rows to supporting | REJECT | No action. The recoveries stay in related_gl_rows. |
| 21 | case_type vocabulary | CHANGE | **Not applied.** It needs a `qoe/schemas.py` comment edit and SPEC §3.8 (open request 6). The key already uses NON_OPERATING and SUPPORTED_TOPSIDE, and `case_type` is a free string, so validation is unaffected. |
| 22 | Data quality: UNMAPPED_ACCOUNT 6750, PL_ACCOUNT_NOT_IN_GL 6995, GL_ACCOUNT_NOT_IN_PL 6305 | CHANGE | **Not applied.** The decision requires the generator's truth derivation, which is code, not a hand edit of `ground_truth.json`, because regeneration overwrites it. The "cannot yet encode" sentence in GroundTruth.notes and the "no" column above are kept, now citing the decision, until the generator emits the three entries. Each should have month null, gl_rows [] and the partner's notes. `ground_truth.json` has 7 data_quality entries. |
| 23 | SPEC §3.4 type "Overhead" and gl_ebitda | CHANGE | **Key applied:** GroundTruth.notes now says "gl_ebitda assumes 6750 (type Overhead) maps to OPEX under the §3.4 fallback". **SPEC text not applied** (open request 7). |
| 24 | 6305 RECON_VARIANCE month-level encoding | NOTE | **Kept all four entries**, so no edit. SPEC §6 is outside what I may read, so whether §6 suppresses month variances for a GL_ACCOUNT_NOT_IN_PL account is left to the spec owner. |
| 25 | A-7 loss-recovery wording | NOTE | **Applied.** The rationale is replaced from "Prairie State Mutual confirmed…", and question topic 2 is reworded. |
| 26 | Package date | CHANGE | **Applied.** `package_date` is 2026-06-05. The seed is unchanged, so no row or amount moved; xlsx metadata now reads 2026-06-05. |
| 27 | A-16 financing condition; REQUEST_INFO vs REJECT | NOTE | **Applied.**<br>- An APA §4(c) sentence is added to the rationale.<br>- Question topic 1 now includes buyer financing.<br>- The reviewer_note is appended.<br>- REQUEST_INFO is kept, with REJECT 0/0/0 pre-registered. |
| 28 | Identical consecutive weekly revenue batches | CHANGE | **Not applied.** It needs generator code for the sum-preserving split and the assertion (generator gap 4). The six pairs remain at rows 114/115, 261/262, 473/474, 489/490, 581/582 and 585/586. |
| 29 | Stridewise run-rate | NOTE | **Applied** in GroundTruth.notes. |
| 30 | AUTHOR_NOTES 7050 non-compete statement | CHANGE | **Applied.** The generator-facts bullet is corrected. |
| 31 | SIGN_ERROR trigger on A-2 / A-3 | CHANGE | **SPEC text not applied** (open request 8). The A-2 and A-3 must-nots are unchanged. |
| 32 | Pre-registered alternatives file | CHANGE | **Recorded for lock** below. `key_alternatives.csv` lives in the study folder, outside this package. |
| 33 | D-1 December-in-January lag | NOTE | **Applied.** A question topic is added. D-1 is unchanged. |

### key_alternatives.csv rows to add at lock

| Package | Item | Alternative treatment | Amounts (FY2024 / FY2025 / TTM May-26) | Condition |
| --- | --- | --- | --- | --- |
| kinetic_ridge_pt | A-16 | REJECT | 0 / 0 / 0 | – |
| kinetic_ridge_pt | A-14 | REVISE | −19,240.17 / 26,101.83 / 27,521.83 | 6950 at its 29-month average |
| kinetic_ridge_pt | A-3 | REVISE (+ OVERLAP_WITH_OTHER_ADJUSTMENT) | 115,966.19 / 177,787.29 / 175,222.46 | Joint with the A-15 row; valid only as a pair |
| kinetic_ridge_pt | A-15 | ACCEPT | 0 / 0 / 38,250 | Joint with the A-3 row; A-15 ACCEPT with A-3 unrevised is a double count |

Deliberately not registered: the A-3 buyer amounts, A-4/A-9 ACCEPT, the A-11 alternatives and A-14 0/0/0. The partner's decision text gave the A-15 leg as 38,000, before the fee fallback. At $38,250 the pair still sums to A-3's accepted 213,472.46.

### Open requests (need the spec owner or generator owner; not applied here)

These are generic changes. They belong in SPEC before the freeze, and the engine must not be tuned on this deal.
1. **SPEC §5.4 OUT_OF_PERIOD.**
   - The service period must describe what the entry itself pays for. Penalties and interest on a prior-period liability are charges of the assessment date: they are not moved, and are added back where booked (or treated as ALREADY_EXCLUDED_FROM_EBITDA).
   - Recommended hygiene: a NON_RECURRING or PRO_FORMA entry carried in full whose service period crosses a year-end raises a cut-off question only.
2. **SPEC §5.4 NO_DOCUMENT_SUPPORT.**
   - A document counts as support only if it is independent of the claim: third-party documents, executed agreements, and contemporaneous company records of the transaction or decision.
   - Owner or management correspondence that only asserts the basis of an add-back is a management representation. It may be linked, but the amounts it covers count as undocumented.
   - A management schedule that reconciles to identified GL postings counts as linkage when an independent document evidences the event. Checked: A-3, D-1, A-10 and A-14 still pass.
3. **SPEC §5.4 RECURRING_PATTERN.** The exemption covers OWNER_DISCRETIONARY, NORMALIZATION and OUT_OF_PERIOD items. Checked: no dev-key OUT_OF_PERIOD item (M-10, Tidewell 13) expects the flag.
4. **SPEC §5.4 OVERLAP (recommended).** Before link scores, an adjustment whose entire claimed set, in every period, is claimed by another adjustment is the duplicate and gets the flag.
5. **SPEC §5.4 OFFSETTING_RECOVERY.** For a claim in a non-operating account inside EBITDA, a same-account credit that a linked schedule lists as the same class of event also qualifies. Non-operating results are removed consistently in every period.
6. **`qoe/schemas.py` ExpectedAdjustment.case_type comment and SPEC §3.8.** Add NON_OPERATING, SUPPORTED_TOPSIDE, SIGN_ERROR and UNDERSTATED.
7. **SPEC §3.4.**
   - Type rules match the whole value, case-insensitively.
   - "Anything else → BALANCE_SHEET" applies only to recognized balance-sheet types.
   - Any other type on an account in the management P&L falls to rule 4: OPEX plus UNMAPPED_ACCOUNT.
8. **SPEC §5.4 SIGN_ERROR.** The trigger is judged on the net debit-positive sign of the claimed set (for normalizations, actual cost less the normalized level). Individual credits inside a net-debit set are not a conflict.
9. **Generator.**
   - Derive the three data-quality codes (gap 1, decision 22).
   - Add the sum-preserving weekly split and the tie assertion (gap 4, decision 28).
   - Add the claimed-set uniqueness assertion (gap 5, decision 16).
