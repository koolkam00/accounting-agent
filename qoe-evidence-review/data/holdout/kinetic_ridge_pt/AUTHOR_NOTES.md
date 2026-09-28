# D3 holdout: Kinetic Ridge Physical Therapy Partners, LLC (SYNTHETIC)

SYNTHETIC — generated for QoE Evidence Review testing. Every company, person, amount and document is fictional.

- **Spec:** `data/specs/kinetic_ridge_pt.yaml`
- **Regenerate:** `uv run python scripts/qoe_generate_deals.py --spec data/specs/kinetic_ridge_pt.yaml --out data/holdout`. The output is byte-deterministic, and this file survives regeneration.
- **Split:** holdout. The answer key was written without reading the engine or AI code, the tests other than `tests/test_generator.py`, reports or workpapers, and without running the review engine on this deal.

## Profile

This is a central Indiana outpatient physical therapy group. It had 12 clinics until the Brownsburg clinic closed on Feb 27, 2026. Its headquarters and flagship clinic are in Zionsville. The company is an LLC taxed as a partnership, so there is no income tax line.

- **Owners and people.** Founder and CEO Dr. Adrienne Kowalczyk; CFO Brent Oyelaran; Controller Megan Sato. The CEO's spouse, Thomas Kowalczyk, owns Kowalczyk Family Realty, LLC, which is the landlord of the Zionsville and Noblesville buildings.
- **Books.** Xero. The GL is an Account Transactions xlsx (`xero_xlsx`) with 3,768 rows and P&L accounts only. The chart of accounts uses Xero export type codes (REVENUE, DIRECTCOSTS, EXPENSE, OVERHEADS, DEPRECIATN, OTHERINCOME). Management's monthly P&L is its Excel reporting pack, laid out with Xero's section names and Excel-date month headers.
- **Periods.** FY2024, FY2025 and TTM May-26 (Jun-2025 to May-2026). The data runs from 2024-01 to 2026-05. TTM shares Jun–Dec 2025 with FY2025.
- **Management schedule.** Refs are A-1 to A-16. The header columns are `#`, `Item`, `Type`, `Management commentary`, `Account(s)` and `Data room ref` (all SPEC §3.6 candidates). Support refs look like `VDR 3.2`.

| | FY2024 | FY2025 | TTM May-26 |
| --- | ---: | ---: | ---: |
| Net revenue (GL) | 28,493,513.49 | 29,917,791.36 | 30,392,029.20 |
| GL EBITDA | 4,236,342.02 | 4,411,657.27 | 4,361,799.47 |
| Management reported EBITDA (P&L basis) | 4,214,905.22 | 4,433,094.07 | 4,361,799.47 |
| Management adjustments (claimed) | 254,446.19 | 599,063.29 | 1,151,548.46 |
| Management adjusted EBITDA | 4,469,351.41 | 5,032,157.36 | 5,513,347.93 |
| Diligence finals, management items (excl. pending) | 171,206.19 | 432,961.29 | 543,146.46 |
| Diligence item D-1 (supported cut-off top-side) | (21,436.80) | 21,436.80 | 0.00 |
| **Diligence adjusted EBITDA** = GL EBITDA + finals + D-1 | **4,386,111.41** | **4,866,055.36** | **4,904,945.93** |
| Memo: pending REQUEST_INFO claims (A-4, A-9, A-16) | 51,000.00 | 109,000.00 | 521,000.00 |

The generator computes GL EBITDA and diligence adjusted EBITDA, and verifies every non-REQUEST_INFO amount against the GL rows. The rent normalizations are verified through `normalized_level`. I also recomputed every amount and the identity independently from the xlsx.

**Chart of accounts (P&L).**
- **Revenue:** 4000–4040 patient revenue by payer; 4100 refunds and recoupments (contra); 4200 employer onsite services.
- **Cost of sales:** 5000 clinical wages; 5100 supplies; 5150 contract therapy labor; 5200 billing and RCM.
- **Operating expenses:** 6000 front office and admin wages; 6010 officer; 6050 payroll taxes and benefits; 6100 rent; 6120 utilities; 6150 R&M and facility projects; 6200 insurance; 6300 software, EMR and IT; 6305 patient engagement platform (new Apr-2026); 6400 legal; 6410 accounting and advisory; 6450 recruiting; 6500 marketing; 6600 travel; 6700 dues; 6750 continuing education (typed "Overhead"); 6800 taxes and licenses; 6850 bank and merchant; 6900 office, linen and phones; 6950 bad debt; 6995 year-end cut-off adjustments (management P&L only).
- **D&A:** 7000 Depreciation (DEPRECIATN); 7050 Amortization Expense.
- **Other:** 8000 Other Income (no activity); 8050 gain/loss on disposal; 8100 Interest Expense; 8200 Other Expenses. 8100 and 8200 are typed EXPENSE, as Xero has no Other Expense type.

## Catalog

Amounts are EBITDA-signed and shown as FY2024 / FY2025 / TTM May-26. GL rows are worksheet rows of `gl/general_ledger.xlsx`. "Must not" lists flags whose firing is an error; they are also recorded in each `reviewer_note`.

| Ref | Management claim | Planted facts | Truth |
| --- | --- | --- | --- |
| A-1 | **Related-party rent, Zionsville HQ and clinic** (normalization), 6100. Claimed 90,000 / 90,000 / 90,000. | Kowalczyk Family Realty bills $32,000 every month (29 rows, Ref `KFR-Z-yymm`, rows 1932…). The executed 2021 lease: 15,000 RSF, absolute net, fixed rent. Northfield's signed opinion of market rent: $19.60/RSF absolute net = $294,000/yr ($24,500/mo), independent, fee not contingent. The executed first amendment resets rent to $24,500 at closing. The same landlord also bills the $6,000 Noblesville rent. | **ACCEPT 90,000 / 90,000 / 90,000** (384,000 − 294,000). Case ADEQUATE. This is the normalization positive control. Must not: NORMALIZATION_BENCHMARK_MISSING, UNSIGNED_OR_DRAFT_SUPPORT, RECURRING_PATTERN, OVERLAP (the KFR-N rows belong to A-2). |
| A-2 | **Related-party rent, Noblesville (below market)** (normalization), 6100. Claimed −39,000 in each period. | KFR bills $6,000/mo (29 rows, `KFR-N-yymm`). The executed 2019 lease (6,000 SF, absolute net, "not based on a market survey"). Brightwater's MAI appraisal: $18.50/SF = $111,000/yr ($9,250/mo). The executed amendment resets rent to $9,250 at closing. | **ACCEPT −39,000 / −39,000 / −39,000** (72,000 − 111,000). Case ADEQUATE. Management's own EBITDA-reducing adjustment. Must not: SIGN_ERROR, NORMALIZATION_BENCHMARK_MISSING, RECURRING_PATTERN. |
| A-3 | **Brownsburg clinic closure** (pro forma, closed clinic), accts 4000, 4010, 5000, 6100, 6120, 6150, 6400. Claimed 115,966.19 / 177,787.29 / 213,222.46. | Brownsburg (acquired 2022) posts revenue monthly from a legacy billing system (4000/4010), and has its own payroll journals, Suite 110 rent ($9,400/mo to Eagle Creek) and utility account, 163 rows in all. The board memo says the last patient day is 2/27/26 and two of five clinicians move to Avon. It lists the stranded costs that are excluded: regional director, EMR enterprise fee, billing office, central supplies, and employer taxes and benefits. The lease termination agreement (3/2/26, executed): $38,000 fee, terminates 3/31/26. Closure costs: fee $38,000; Tate Whitcomb Matter 4471 $4,350 (one line of split invoice TW-26-0312); HRS equipment move $3,200; final pay and PTO $6,850. The final utility bill is Apr-10-2026, and there are no Brownsburg rows after it. TTM = $160,822.46 operating loss + $52,400 closure costs. | **ACCEPT as claimed.** Case ADEQUATE. This is the realized pro forma positive control; ambiguity medium (a minority view credits the revenue retained at Avon). Must not: PRO_FORMA_NOT_REALIZED, SIGN_ERROR (revenue credits inside a net-loss add-back), RECURRING_PATTERN, OVERLAP on A-3. |
| A-4 | **Owner family payroll, T. Kowalczyk** (owner/discretionary), 6000. Claimed 51,000 in each period. | 58 semi-monthly payroll rows of $2,125, memo "(marketing coordinator)". The only support is the CEO's email: he is a full-time student, "doesn't work in the business", and "We don't have anything else to send". | **REQUEST_INFO.** Case NEEDS_INFO. Flag: NO_DOCUMENT_SUPPORT. The provisional amount is 51,000 per period, about 54.9k with employer taxes. It must not be accepted on the representation. |
| A-5 | **Transaction costs, Project Sycamore** (non-recurring), 6400 and 6410. Claimed 0 / 51,000 / 88,800. | Larchmont one-time retainer $30,000 (Oct-25; "fully creditable against the Success Fee", "No monthly or periodic fees"). Brennan Oakes sell-side QoE, $42,000 fixed fee in two $21,000 installments (Nov-25, Jan-26). Tate Whitcomb Matter 4468 $16,800, the Sycamore line of TW-26-0312 (Mar-26). Tate Whitcomb also bills an unclaimed $1,500/mo Matter 1102 general counsel retainer "continuing until terminated". | **ACCEPT 0 / 51,000 / 88,800.** Case ADEQUATE. These are false-reject traps. Must not: CONTINUING_OBLIGATION, RECURRING_PATTERN, OVERLAP (the split invoice's other line is A-3's). Related rows: the 29 retainer rows. |
| A-6 | **Carmel clinic relocation** (non-recurring), 6100, 6150 and 6300. Claimed 0 / 37,950 / 37,950. | HRS-25-0814 posts as three GL lines: move crews $18,400 and equipment reinstall $9,600 (6150), plus storage for Aug–Oct 2025, $3,450 = 3 × $1,150 (6100). The invoice says storage continues at $1,150/mo "until stored items are released", and HRS bills $1,150 monthly from Nov-2025 (7 unclaimed rows). Monon Trail Networks cabling is $6,500 in the GL, but the invoice totals $6,955.00, including $182 freight and $273 sales tax. | **REVISE 0 / 34,500 / 34,500.** Case PARTIAL. Flags: CONTINUING_OBLIGATION (storage line) and DOC_GL_AMOUNT_MISMATCH (Monon; a question only, and the GL amount is carried). CONTRADICTORY_EVIDENCE via entry qualification is an acceptable extra flag for the storage removal. |
| A-7 | **Fishers clinic water damage** (non-recurring), 6150. Claimed 0 / 0 / 41,850. | Burst pipe 1/24/26. Circle City Restoration $24,600 (Feb-26) and Hamilton County Flooring $17,250 (Mar-26), both citing claim PSM-26-004417. The insurer's letter (4/8/26) confirms coverage and estimates a $31,850 payment after a $10,000 deductible: "The claim remains open." The 5/28/26 email says "Nothing received yet and nothing booked in Xero." | **ACCEPT 0 / 0 / 41,850**, with questions on recovery timing, the working-capital treatment of the receivable, and business income. Case ADEQUATE. This is the pending-recovery trap. Must not: OFFSETTING_RECOVERY. Reducing the add-back by 31,850 understates TTM. |
| A-8 | **Maddox non-compete litigation** (non-recurring), 6400. Claimed 0 / 52,000 / 39,400. | Stanton Reyes invoices $12,600 (Apr-25), $16,400 (Jun), $13,900 (Aug), $9,100 (Oct). Kinetic Ridge v. Pruitt 2024 via Barlow & Finch: $44,400 in four invoices, Mar–Jul 2024. Kinetic Ridge v. Grant 2026 via Hargrove Lindqvist: $20,000 (Feb, Apr-26). Each year uses a different firm, but the account and the non-compete/restrictive-covenant theme are the same. The general counsel's litigation summary says "we expect one to two enforcement matters per year" and that they are not insured. | **REJECT 0 / 0 / 0.** Case RECURRING. Flags: RECURRING_PATTERN (account + theme; FY24 44,400 ≥ 50% of 52,000) and CONTRADICTORY_EVIDENCE (litigation summary). |
| A-9 | **Brand refresh** (non-recurring), 6500. Claimed 0 / 58,000 / 58,000. | Copperline Creative Studio bills $18,500 (Aug-25), $22,000 (Sep), $17,500 (Oct); these are Copperline's only rows. The only document is the CEO's email: a "one-time rebrand" with "I don't think we ever signed a formal SOW". There are no invoices or SOW in the data room. | **REQUEST_INFO.** Case NEEDS_INFO. Flag: NO_DOCUMENT_SUPPORT. This is the clean test: the GL ties 100% and the support is a management representation only. |
| A-10 | **Loss on sale of outreach vans** (non-recurring), 8050. Claimed 0 / 27,600 / 27,600. | 8050 has three rows: an $8,400 gain on two vans (Mar-24), a $27,600 loss on five vans (Oct-25; bill of sale $78,650 vs NBV $106,250) and a $4,900 gain on a dynamometer (Apr-26). The disposal schedule lists all three and says "As in prior years, gains and losses are recorded in 8050". | **REVISE −8,400 / 27,600 / 22,700.** Case NON_OPERATING. The gains are carried as recoveries (related rows). Must not: RECURRING_PATTERN. |
| A-11 | **Use-tax audit assessment** (prior period), 6800 and 8100. Claimed 0 / 27,876 / 27,876. | Notice NPA-2025-448812 covers the audit period 1/1/24–12/31/24. Tax $23,840 (6800), 10% penalty $2,384 (6800) and interest $1,652 (8100), all booked 11/18/25. | **REVISE −23,840 / 26,224 / 26,224.** Case OUT_OF_PERIOD. The tax is two-sided out-of-period (a 2024 cost), the penalty is added back, and the interest is already excluded. Flags: OUT_OF_PERIOD, ALREADY_EXCLUDED_FROM_EBITDA. |
| A-12 | **Q4 2023 contract therapy invoice** (out-of-period), 5150. Claimed 36,480 / 0 / 0. | Crossfield CMS-24-0209R, booked 2/9/24. "Service period: October 2, 2023 – December 29, 2023"; rebilled after a timesheet dispute. This is Crossfield's only row. Routine per diem staffing in 5150 is a different vendor (Summit Allied, 59 rows). | **ACCEPT 36,480 / 0 / 0.** Case OUT_OF_PERIOD. Flag: OUT_OF_PERIOD. The service months fall before data_start, so no negative side is carried (over-adjustment trap). Must not: any negative amount, RECURRING_PATTERN. |
| A-13 | **Term loan prepayment premium** (non-recurring), 8200. Claimed 0 / 18,500 / 18,500. | The Harvest Plains payoff letter shows a prepayment premium of $18,500 (1.0% of $1.85M). It is booked in 8200 Other Expenses, which is inside EBITDA; it is the only 8200 row. Accrued payoff interest of $9,314.24 is in 8100 and not claimed. | **ACCEPT 0 / 18,500 / 18,500.** Case ADEQUATE. This is the contrast case to D1 M-07. Must not: ALREADY_EXCLUDED_FROM_EBITDA. |
| A-14 | **Bad debt, Midstate Employer Health Network** (non-recurring), 6950. Claimed 0 / 46,350 / 46,350. | The employer customer entered receivership 9/22/25, and the receiver expects nothing for unsecured creditors. The claim form lists INV-30208, INV-30214 and INV-30220 (Jun–Aug 2025, $15,450 each), and the write-off is Nov-25. Routine patient write-offs are $1.9k–3.7k a month. | **ACCEPT 0 / 46,350 / 46,350.** Case ADEQUATE; ambiguity medium. This is a false-reject trap: one large write-off among small routine entries. Must not: RECURRING_PATTERN. |
| A-15 | **Brownsburg lease termination fee** (non-recurring), 6100. Claimed 0 / 0 / 38,000. | This is the same $38,000 row (2251) that A-3 claims. Both A-3 and A-15 cite VDR 3.2 and 3.3 and account 6100, and both descriptions name the $38,000 fee, so the link scores are equal by design. | **REJECT 0 / 0 / 0.** Case OVERLAP. Flag: OVERLAP_WITH_OTHER_ADJUSTMENT. The schedule-order tie-break keeps the fee in A-3. |
| A-16 | **Pro forma: Wabash Valley Sports Rehab acquisition** (pro forma), no GL accounts. Claimed 0 / 0 / 412,000. | The APA was executed 4/22/26. Closing is "on July 1, 2026", conditioned on Medicare enrollment, payer credentialing and landlord consents, which are outstanding per the CFO's 5/29/26 email ("Nothing has been paid and nothing is in our books yet"). The seller's TTM Mar-26 summary is "Not audited or reviewed" and on a cash basis. There is no GL activity. | **REQUEST_INFO.** Case NEEDS_INFO. Flags: NO_GL_SUPPORT, PRO_FORMA_NOT_REALIZED. The pre-registered alternative is REJECT 0/0/0. |

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
| Overlap settled by the schedule-order tie-break; one invoice split across two adjustments | A-15 / A-3; TW-26-0312 split between A-3 (Matter 4471) and A-5 (Matter 4468) |
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
| PL_ACCOUNT_NOT_IN_GL | 6995 Year-End Cut-Off Adjustments | **no** (the generator cannot express this code) | The account is in the chart of accounts and management's P&L but has zero Xero GL activity. |
| GL_ACCOUNT_NOT_IN_PL | 6305 Patient Engagement Platform | **no** (the generator cannot express this code) | The account has two GL rows (Apr and May 2026), and management's P&L has no 6305 line. |
| UNMAPPED_ACCOUNT | 6750 Continuing Education & Licensure | **no** (the generator cannot express this code) | Its chart-of-accounts type is "Overhead" (Xero's UI label, hand-edited in the 2023 migration) rather than the export code OVERHEADS that every other account uses. The label is not in the SPEC §3.4 type list, so ingest should fall back to OPEX and raise UNMAPPED_ACCOUNT. There is no EBITDA effect, and there is no overrides file. |

There are no duplicate postings. The generator asserts that no unplanted duplicate group exists. Multi-line Xero invoices (HRS-25-0814 with 3 lines, TW-26-0312 with 2 lines, NPA-2025-448812 with 3 lines, HPB-PAYOFF-0926 with 2 lines) share a Reference, but their lines have different amounts, so they are not duplicates.

## Diligence items (SPEC §5.7)

| Id | What | Amounts | GL rows | Support |
| --- | --- | --- | --- | --- |
| D-1 | Supported management top-side: the Lakeshore December 2024 invoice, moved from Jan-2025 back to Dec-2024 | −21,436.80 / +21,436.80 / 0 | supporting 1511 (period move to 2024-12) | invoice LRC-2412 (service period Dec 1–31, 2024; received Jan 08 2025) and the Whitlock Haas email (1.1) |

With `dil_recon` at +21,436.80 / −21,436.80 / 0, GL EBITDA + `dil_recon` + D-1 equals management's reported EBITDA. The 6305→6300 mapping top-side is EBITDA-neutral, so it is not a diligence item.

## Generator facts the key relies on

These were checked in the generated GL:
- 8000 has no activity. 8200 has exactly one row, the prepayment premium. 8050 has exactly the three disposals.
- 5150 has two vendors: Crossfield (1 row, the A-12 invoice) and Summit Allied (59 per diem rows).
- The only rows on the non-compete / restrictive-covenant theme are the 10 rows for Pruitt, Maddox and Grant. Tate Whitcomb's retainer memos do not use that theme.
- Every GL description containing "Brownsburg" (163 rows) is in A-3's supporting set. The last one is the final utility bill on 2026-04-10.
- Copperline has only its three rows. Midstate's billing stops after Aug-2025.
- The related-party rent is exactly 29 × $32,000 and 29 × $6,000.

## Ambiguity and alternatives

| Item | Ambiguity | Note |
| --- | --- | --- |
| A-3 | medium | A buyer might credit Brownsburg revenue retained at Avon (not pre-registered). Unclaimed employer taxes on Brownsburg wages (about $41k/yr) are seller upside. |
| A-4, A-9 | medium | Teams often carry these once HR records or invoices arrive. That counts as new information, not a tool error. |
| A-14 | medium | Alternatives, not carried: normalize 6950 to its 29-month average; buyer run-rate removal of Midstate's TTM revenue of $46,350. |
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
