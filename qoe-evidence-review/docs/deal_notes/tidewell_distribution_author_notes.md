# Dev deal 2: Tidewell Distribution Group, LLC (SYNTHETIC) - author notes

Spec: `data/specs/tidewell_distribution.yaml`. Package: `data/dev/tidewell_distribution/` (split `dev`).
Regenerate with `uv run python scripts/qoe_generate_deals.py --spec data/specs/tidewell_distribution.yaml --out data/dev`.
Tests: `tests/test_generator_tidewell.py`. The answer key was written from the planted facts and a
Big-4 senior's judgment. The engine and AI code were not read and the review engine was not run on this deal.

## Profile

- Specialty distributor of foodservice packaging and janitorial and sanitation supplies. It runs a
  Savannah GA distribution center (owner-held, in Pooler) and branches in Jacksonville and Charleston.
- An LLC taxed as an S corporation, with a Georgia PTET election that runs through 9000 (a TAXES account).
  The owner and CEO is Wade A. Carrow. The sale process is code-named Project Marlin, and the buyer is
  Saltmarsh Equity Partners II.
- The GL is a NetSuite saved-search CSV (`netsuite_csv`, detected as `auto`) with 6,027 rows over
  Apr 2024 to Jun 2026 and P&L accounts only. Subsidiary, Department, Class and Location are populated,
  with planted tagging noise.
- The fiscal year ends March 31. The periods are FY2025 (Apr-24 to Mar-25), FY2026 (Apr-25 to Mar-26)
  and TTM Jun-26 (Jul-25 to Jun-26). FY2026 and TTM overlap in Jul-25 to Mar-26.
- Schedule refs are the plain numbers "1" to "16". The data room holds 52 documents, including PDFs and
  `.eml` emails, across 8 folders.

| | FY2025 | FY2026 | TTM Jun-26 |
| --- | ---: | ---: | ---: |
| Revenue (GL) | 72,176,194.04 | 75,697,445.69 | 76,685,508.55 |
| EBITDA per GL | 8,022,682.75 | 7,496,760.71 | 7,517,054.01 |
| Reported EBITDA per management | 7,659,096.28 | 7,310,760.71 | 7,517,054.01 |
| Management adjusted EBITDA (as printed) | 8,307,096.28 | 8,703,760.71 | 9,045,684.19 |
| Management adjusted EBITDA (if the total footed) | 8,307,096.28 | 8,798,760.71 | 9,140,684.19 |
| **Diligence adjusted EBITDA (key)** | **8,139,096.28** | **8,441,360.71** | **8,751,484.19** |

## Catalog

Amounts are FY2025 / FY2026 / TTM Jun-26 and EBITDA-signed. ADEQUATE items (clean ACCEPT) are refs 1,
4, 6, 8, 9, 15 and 16, which is 7 of 16 (44%).

| Ref | Management claim | Planted facts | Truth and reasoning |
| --- | --- | --- | --- |
| 1 | **Owner compensation normalization** (Normalization), 6050. 540,000 / 540,000 / 540,000 | Owner salary of 24 x $37,500 = $900,000 a year in every period. An **executed** post-close employment agreement (signed 5/18/26 and acknowledged by the buyer) sets a $300,000 base plus a 20% target bonus, for $360,000 total target cash with no perks. An independent Holloway benchmark, commissioned by the buyer, puts the peer median total target cash at $358,000. | **ACCEPT 540,000 x 3** (ADEQUATE). The normalization positive control: 900,000 - 12 x 30,000. Must not fire: UNSIGNED_OR_DRAFT_SUPPORT, NORMALIZATION_BENCHMARK_MISSING, RECURRING_PATTERN. Unclaimed employer Medicare of 7,830 a year is noted only. |
| 2 | **Related-party rent** (Normalization), 6200. +48,000 x 3 ("above market; normalize to $20,000/mo") | Rent is $24,000 a month ($6.00/SF NNN, flat since 2019) paid to Pooler Industrial Holdings, which the CEO controls. A **signed** Marsh Point broker opinion (4 comps at $6.95-7.60/SF) puts market at **$7.25/SF NNN = $29,000/mo** and says contract rent is below market. Tenant-paid property taxes confirm the NNN basis. | **REVISE -60,000 x 3** (CONTRADICTED). 288,000 - 348,000 per period, so the sign flips. Flag: CONTRADICTORY_EVIDENCE. Must not fire: NORMALIZATION_BENCHMARK_MISSING, UNSIGNED_OR_DRAFT_SUPPORT, SIGN_ERROR. |
| 3 | **Family office shared services** (Owner / related party), no GL account. 60,000 x 3, "Mgmt estimate" | There is no GL activity with Carrow Family Holdings anywhere, and no invoice, agreement or document. | **REQUEST_INFO** (NEEDS_INFO, ambiguity medium). Flag: NO_GL_SUPPORT. The provisional amount is 0. If the services are free, the adjustment is a *negative* standalone cost. Pre-registered alternative: REJECT 0/0/0. |
| 4 | **Charleston order desk eliminated** (Pro forma), 6030. 0 / 0 / 88,230.18 | Order-desk payroll (a separate cost-center line, about $12.6k a month) runs through the 1/30/26 run and then stops. There are an HR RIF memo, three **signed** separation agreements (2/2-2/4/26), a payroll register extract that ties to the 14 GL rows, and a COO email saying the roles are not backfilled. The Feb-26 severance of $11,850 is booked but not claimed. | **ACCEPT 0 / 0 / 88,230.18** (ADEQUATE). The realized pro forma positive control. FY2026 stays 0 by presentation, so `verify_periods` is TTM only. Must not fire: PRO_FORMA_NOT_REALIZED, EXCESS_GL_ACTIVITY (severance is a separate cost, not an upward revision). |
| 5 | **Purchasing Manager eliminated** (Pro forma), 6040. 0 / 0 / 48,000 | The manager retired 12/31/25 under a signed agreement stating a **current base of $86,400**, and payroll of $3,600 semi-monthly stops after Dec-25. Management used the census **2026 approved salary of $96,000** x 6/12. | **REVISE 0 / 0 / 43,200** (PARTIAL). The contract-salary variant: carry the GL actual (12 x 3,600). Flag: PARTIAL_GL_SUPPORT. Must not fire: PRO_FORMA_NOT_REALIZED. |
| 6 | **Transaction bonuses** (Non-recurring), 6040. 0 / 90,000 / 90,000 | A **signed** Project Marlin Transaction Bonus Plan (11/14/25) pays one-time LOI payments to four executives; payroll ran 3/13/26. Closing payments of $170,000 are seller-funded and not in the GL. | **ACCEPT** (ADEQUATE). The transaction-compensation positive control. Must not fire: RECURRING_PATTERN, CONTINUING_OBLIGATION. The Jun-26 MIP payout in the same account is a different plan (D-2). |
| 7 | **Sprinkler line break** (Non-recurring), 6220. 0 / 100,000 / 100,000 | Invoices booked: $38,500 (Aug-25) + $33,500 (Sep-25) = **$72,000**. The $28,000 is a management **estimate never booked**: the controller's email says it was "not invoiced or booked" and the COO says the repair was done in-house. The insurer paid **$30,000 in May-26, credited to 6220** (contra) and not netted. | **REVISE 0 / 72,000 / 42,000** (RECOVERY_OFFSET). Combines PARTIAL_GL_SUPPORT with a same-account recovery that falls in TTM only (after 3/31/26). Flags: PARTIAL_GL_SUPPORT, OFFSETTING_RECOVERY. |
| 8 | **PFAS molded fiber write-off** (Non-recurring), 5300. 0 / 148,600 / 148,600 | A single Dec-25 entry for 4,929 cases. Customer PFAS-free mandates took effect 1/1/26; the supplier discontinued the line and refused returns; a disposal certificate shows no salvage. Routine cycle counts run about $3.2k a month, and annual counts were $8,940 and $10,420. | **ACCEPT** (ADEQUATE, ambiguity medium). **False-reject trap**: one large write-off among small routine entries. Must not fire: RECURRING_PATTERN. Minority alternative: REJECT as ordinary obsolescence. |
| 9 | **Brightfield arbitration** (Non-recurring), 6400. 0 / 51,000 / 34,200 | Three invoices for Brannock & Vail Matter 2025-014 ($16,800 Jun-25, $21,450 Aug-25, $12,750 Oct-25). The award denied all claims and the file is closed. The same firm bills an **unclaimed $3,500/mo general-counsel retainer** ("continues month to month until either party terminates it"). | **ACCEPT** (ADEQUATE). **False-reject trap**: a one-time matter from a firm that also bills a retainer. Must not fire: RECURRING_PATTERN, CONTINUING_OBLIGATION, OUT_OF_PERIOD (billing periods sit in the same period labels as their bookings). |
| 10 | **KestrelWMS implementation** (Non-recurring), 6600. 0 / 128,400 / 144,600 | The order form splits a **one-time $64,000 implementation fee** (2 x $32,000) from a **$5,400/mo subscription** (36 months, auto-renew). Management claimed all Kestrel activity, including 6 (FY2026) and 9 (TTM) subscription months and **both postings of go-live bill KS-10442**. | **REVISE 0 / 64,000 / 64,000** (CONTRADICTED). An entry-level split. Flags: CONTINUING_OBLIGATION, DUPLICATE_GL_ENTRY. The second KS-10442 posting is carried by **D-1**, not here, so nothing is counted twice. |
| 11 | **Distribution network study** (Non-recurring), 6420. 0 / 54,000 / 54,000 | The engagement letter sets one fixed fee of $84,000 in 3 phases: $30,000 Oct-25, $24,000 Dec-25 and $30,000 Feb-26. Management's own support ref cites the **phase 3 invoice (VDR 6.4.3)**, but the claim includes phases 1 and 2 only. | **REVISE 0 / 84,000 / 84,000** (UNDERSTATED). An upward revision above the claim. Flag: EXCESS_GL_ACTIVITY. Must not pull in the SafePoint EHS quarterly audits in 6420. |
| 12 | **Sunmeadow termination settlement** (Non-recurring), 8000. 0 / +46,500 / +46,500 | A one-time $46,500 **termination fee received**, credited to 8000 Other Income (inside EBITDA), under a signed agreement. | **REVISE 0 / -46,500 / -46,500** (SIGN_ERROR). Removing a one-time gain reduces EBITDA. Flag: SIGN_ERROR. |
| 13 | **Prior-period freight true-up** (Out-of-period), 5400. 0 / 38,400 / 38,400 | Altamaha bill AFL-TU-25-118 was booked 11/14/25. The invoice states a **service period of Apr 1 - Sep 30, 2025** at $6,400 a month. | **REVISE 0 / 0 / 19,200** (OUT_OF_PERIOD). The item straddles the FY2026/TTM overlap. FY2026 contains the booking and all 6 service months, giving 0. TTM holds the booking but only Jul-Sep, so it keeps the Apr-Jun half (+19,200). Flag: OUT_OF_PERIOD. |
| 14 | **Refinancing costs** (Non-recurring), 6400 and 8100. 0 / 69,600 / 69,600 | Marlowe's debt placement fee of $42,000 sits in 6400. The $27,600 write-off of unamortized debt issuance costs sits in **8100 Interest Expense**, which management's interest line already adds back. | **REVISE 0 / 42,000 / 42,000** (EBITDA_EXCLUDED). A partial ALREADY_EXCLUDED case. Flag: ALREADY_EXCLUDED_FROM_EBITDA. |
| 15 | **Prepayment premium** (Non-recurring), 8200. 0 / 18,500 / 18,500 | The payoff letter shows 2.00% of $925,000 prepaid. It is booked in **8200 Other Expense**, which is inside EBITDA. | **ACCEPT** (ADEQUATE). The contrast case to D1 M-07. Must not fire: ALREADY_EXCLUDED_FROM_EBITDA. |
| 16 | **Sale-process professional fees** (Non-recurring), 6400 and 6410. 0 / 95,000 / 95,000 | Cordell Harbor's **one-time retainer of $35,000 is creditable against the success fee**. Whitlock & Rowe's sell-side QoE is a $60,000 fixed fee paid in **2 x $30,000 installments**. Routine CPA fees in 6410 are unclaimed. | **ACCEPT** (ADEQUATE). **False-reject trap**. Must not fire: CONTINUING_OBLIGATION, RECURRING_PATTERN. This is also the row management's total formula omits. |

**Diligence items** (`GroundTruth.diligence_items`):

| Item | Truth | Basis |
| --- | --- | --- |
| D-1 Duplicate Kestrel posting | REVISE 0 / 32,000 / 32,000 | KS-10442 ($32,000, 6600) is posted on 10/3 and again on 10/9/25 with the same document number and different Internal IDs. The invoice shows one charge, and Kestrel's statement shows the second payment as a $32,000 unapplied credit. The first posting stays in ref 10. Flag: DUPLICATE_GL_ENTRY. |
| D-2 FY2026 MIP accrual (supported top-side) | REVISE 0 / -186,000 / 0 | Management's P&L accrues $186,000 in 6040 in Mar-26 and reverses it in Jun-26, when NetSuite payroll pays it (6/12/26). The plan, adopted 4/8/25, earns awards on 3/31/26, and the approved calculation (4/24/26) ties to the payout. Keeping the accrual gives FY2026 = GL - 186,000 and TTM = GL (the payment is already in TTM once). This is the D1 panel's cash-to-accrual contrast, adapted to a March year-end. Encoded as a period move of the payment row to Mar-26. |
| D-3 Aug-2024 GL export gap | REVISE -363,586.47 / 0 / 0 | The Aug-24 GL batch was exported with the 16-account flash search, per the NetSuite administrator's email. Management's P&L, which ties to the trial balance, holds the other 23 accounts' August activity. Keeping management's August amounts (EBITDA accounts only) avoids overstating FY2025. The amount is computed by the generator from the dropped ledger rows, not typed. |

**Expected totals** (FY2025 / FY2026 / TTM):

- Claims are 648,000 / 1,488,000 / 1,623,630.18. The printed total is 648,000 / 1,393,000 / 1,528,630.18 because ref 16 is omitted.
- Management finals are 480,000 / 1,098,600 / 1,202,430.18.
- Pending (ref 3) is 60,000 in each period.
- Diligence items total -363,586.47 / -154,000 / 32,000.
- Diligence adjusted EBITDA is GL + finals + diligence items = 8,139,096.28 / 8,441,360.71 / 8,751,484.19, computed by the generator.

## Planted data-quality issues

| Code | Locator | Detail |
| --- | --- | --- |
| `DUPLICATE_GL_ENTRY` | 2025-10, 6600, both rows | Kestrel bill KS-10442 is posted twice, six days apart. Both postings are inside ref 10's claim, and D-1 reverses the second. |
| `MISSING_PERIOD` | 2024-08 | The GL holds 16 of the 39 accounts active in August (41%, under the 50% threshold). The P&L has the full month. |
| `RECON_VARIANCE` | 2026-03, 6040 | The P&L exceeds the GL by 186,000 because of the MIP accrual top-side. |
| `RECON_VARIANCE` | 2026-06, 6040 | The P&L is 186,000 below the GL because the top-side is reversed when the bonus is paid. |
| `MGMT_EBITDA_DIFFERS_FROM_GL` | none (code only) | Management's reported EBITDA less GL is -363,586.47 in FY2025 (missing month) and -186,000 in FY2026 (MIP). TTM is 0. |
| `MGMT_SCHEDULE_ARITHMETIC` | none (code only) | The total-adjustments row omits ref 16 (95,000 in FY2026 and TTM), so adjusted EBITDA is understated. |
| Dimension noise (not scored) | GL columns | 180 rows have a blank Department, 87 a blank Class, and 265 a blank Location. Some revenue lines carry the wrong Class. Payroll lines carry Department cost centers. |

The Aug-24 gap also produces 23 account-month P&L-vs-GL differences that a tool may list as RECON_VARIANCE. The key records them once, as MISSING_PERIOD.

## Coverage of the D1 panel's case list (D2 items)

| Case | Where |
| --- | --- |
| Normalization positive control (owner comp) | Ref 1 |
| Normalization whose sign flips | Ref 2 |
| Realized pro forma (Feb-26 headcount cut, claim = eliminated payroll Jul-25 to Jan-26) | Ref 4 |
| Contract-salary variant, revised to the GL | Ref 5 |
| PARTIAL_GL_SUPPORT, 100,000 vs 72,000 with an unbooked estimated accrual | Ref 7 (FY2026) |
| Same-account (contra) recovery with a TTM-only effect | Ref 7 (TTM); the recovery is in May-26 because Jan-Mar 2026 also sits in FY2026 under a March year-end |
| NO_GL_SUPPORT (owner-affiliate cost, management estimate) | Ref 3 |
| SIGN_ERROR (vendor settlement in Other Income) | Ref 12 |
| Mixed implementation plus subscription contract | Ref 10 |
| Out-of-period item straddling the overlap (service Apr-Sep 25, booked Nov-25) | Ref 13 |
| Duplicate posting inside a claimed item, plus a diligence duplicate item | Ref 10 and D-1 |
| Partial ALREADY_EXCLUDED (6400 plus 8100) | Ref 14 |
| Contrast: prepayment premium in 8200 | Ref 15 |
| Upward revision (a same-engagement invoice cited in support but unclaimed) | Ref 11 |
| Supported top-side (cash to accrual) | D-2 |
| Transaction bonus under a signed plan, paid in TTM | Ref 6 |
| False-reject traps (at least 2) and ADEQUATE items at 40% or more | Refs 8, 9 and 16 as traps; 7 of 16 items ADEQUATE |
| NetSuite: MISSING_PERIOD, MGMT_SCHEDULE_ARITHMETIC, dimension noise | See the data-quality table |

Two items combine case types so the schedule can keep 16 items with at least 40% ADEQUATE:

- **Ref 7** combines the partial GL support case with the recovery case.
- **Ref 10** combines the mixed contract with the duplicate posting.

Each effect in these two items is entry-level and can be read by period. In ref 7, FY2026 isolates the unbooked estimate and TTM adds the recovery.

## Judgment calls a reviewer should check

1. **D-3 (missing month).** A careful senior would not build FY2025 diligence EBITDA on a GL export that drops 23 accounts for one month. The management P&L ties to the trial balance, and the gap is an export defect explained in writing. The key therefore keeps management's August amounts.
   - This item has **no GL rows**, so matching on `supporting_gl_rows` overlap can never pair it with a tool item.
   - `evaluate.py` needs to match it another way (for example, a code or amount rule), or it counts as a miss for every tool.
   - A tool that reverses the August difference to the GL overstates FY2025 by 363,586.47.
2. **D-2 period adaptation.** The D1 panel described a Dec-25 accrual paid Mar-26, but under a March year-end both dates sit in FY2026 and TTM. The key uses the equivalent year-end pattern instead: an accrual at 3/31/26, paid Jun-26.
3. **Ref 2 applies current market rent to every period**, the usual related-party normalization. The BOV comparables span 2024-25, so FY2025 is also supported.
4. **Ref 7 recovery timing.** The recovery is taken in the period it was booked (May-26), as with D1 M-09. The claim was open and unquantified at 3/31/26, so accruing it into FY2026 is not supported.
5. **Ref 4 FY2026 = 0.** Run-rate savings are presented only in TTM. The rows also fall in FY2026, so `verify_periods: [TTM Jun-26]` limits the tie-out to TTM.
6. **Ref 8** is ACCEPT at medium ambiguity. A minority view treats product obsolescence as a normal distribution cost.

## Generator extensions (additive; Meridian regenerates byte-identically)

- `background[].dimensions` values may be lists, which pick a value per row from a dedicated RNG so amounts are unaffected.
- `data_quality.mgmt_ebitda_note` sets the explanation on the MGMT_EBITDA_DIFFERS entry. Top-side amounts may be negative.
- `schedule.total_excludes` and `schedule.arithmetic_note` plant MGMT_SCHEDULE_ARITHMETIC and emit its key entry.
- Answer-key options:
  - `normalized_level` subtracts a benchmark level per month.
  - `restore_missing_months` keeps activity dropped from the GL.
  - `verify_periods` limits the tie-out for TTM-only pro formas.
  - `related_docs` writes `ExpectedAdjustment.related_docs`.
- `build_ground_truth` takes an optional `accounts` argument, needed to exclude below-EBITDA rows from a restoration.
- These options are documented in `scripts/qoe_synth/SPEC_FORMAT.md` and exercised by `tests/test_generator_tidewell.py`.
