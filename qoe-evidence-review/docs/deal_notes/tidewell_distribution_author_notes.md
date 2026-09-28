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
- The GL is a NetSuite saved-search CSV (`netsuite_csv`, detected as `auto`) with 6,033 rows over
  Apr 2024 to Jun 2026 and P&L accounts only. Subsidiary, Department, Class and Location are populated,
  with planted tagging noise.
- The fiscal year ends March 31. The periods are FY2025 (Apr-24 to Mar-25), FY2026 (Apr-25 to Mar-26)
  and TTM Jun-26 (Jul-25 to Jun-26). FY2026 and TTM overlap in Jul-25 to Mar-26.
- Schedule refs are the plain numbers "1" to "16". The data room holds 52 documents, including PDFs and
  `.eml` emails, across 8 folders.

| | FY2025 | FY2026 | TTM Jun-26 |
| --- | ---: | ---: | ---: |
| Revenue (GL) | 72,176,194.04 | 75,697,445.69 | 76,685,508.55 |
| EBITDA per GL | 8,021,818.36 | 7,418,030.47 | 7,443,814.59 |
| Reported EBITDA per management | 7,658,231.89 | 7,232,030.47 | 7,443,814.59 |
| Management adjusted EBITDA (as printed) | 8,306,231.89 | 8,625,030.47 | 8,972,444.77 |
| Management adjusted EBITDA (if the total footed) | 8,306,231.89 | 8,720,030.47 | 9,067,444.77 |
| **Diligence adjusted EBITDA (key)** | **8,138,231.89** | **8,362,630.47** | **8,678,244.77** |

These figures reflect the panel-review regeneration (vendor rebates restructured; see "Panel review"). Revenue
and every key amount are unchanged; only 5200 Vendor Rebates moved GL EBITDA.

## Catalog

Amounts are FY2025 / FY2026 / TTM Jun-26 and EBITDA-signed. ADEQUATE items (clean ACCEPT) are refs 1,
4, 6, 8, 9, 15 and 16, which is 7 of 16 (44%).

| Ref | Management claim | Planted facts | Truth and reasoning |
| --- | --- | --- | --- |
| 1 | **Owner compensation normalization** (Normalization), 6050. 540,000 / 540,000 / 540,000 | Owner salary of 24 x $37,500 = $900,000 a year in every period. An **executed** post-close employment agreement (signed 5/18/26 and acknowledged by the buyer) sets a $300,000 base plus a 20% target bonus, for $360,000 total target cash with no perks. An independent Holloway benchmark, commissioned by the buyer, puts the peer median total target cash at $358,000. | **ACCEPT 540,000 x 3** (ADEQUATE). The normalization positive control: 900,000 - 12 x 30,000. Must not fire: UNSIGNED_OR_DRAFT_SUPPORT, NORMALIZATION_BENCHMARK_MISSING, RECURRING_PATTERN. Unclaimed employer Medicare of 7,830 a year is noted only. |
| 2 | **Related-party rent** (Normalization), 6200. +48,000 x 3 ("above market; normalize to $20,000/mo") | Rent is $24,000 a month ($6.00/SF NNN, flat since 2019) paid to Pooler Industrial Holdings, which the CEO controls. A **signed** Marsh Point broker opinion (4 comps at $6.95-7.60/SF) puts market at **$7.25/SF NNN = $29,000/mo** and says contract rent is below market. Tenant-paid property taxes confirm the NNN basis. | **REVISE -60,000 x 3** (CONTRADICTED, ambiguity medium). 288,000 - 348,000 per period, so the sign flips. Flag: CONTRADICTORY_EVIDENCE. Must not fire: NORMALIZATION_BENCHMARK_MISSING, UNSIGNED_OR_DRAFT_SUPPORT, SIGN_ERROR. Pre-registered alternative: REJECT 0/0/0 (the 2019 lease binds at $24,000 flat to 3/31/2029; no post-close lease is executed). |
| 3 | **Family office shared services** (Owner / related party), no GL account. 60,000 x 3, "Mgmt estimate" | There is no GL activity with Carrow Family Holdings anywhere, and no invoice, agreement or document. | **REQUEST_INFO** (NEEDS_INFO, ambiguity medium). Flag: NO_GL_SUPPORT. The provisional amount is 0. On management's own description nothing is expensed, so the add-back has nothing to remove; losing free services at closing is a buyer standalone-cost consideration, not carried. Pre-registered alternative: REJECT 0/0/0. |
| 4 | **Charleston order desk eliminated** (Pro forma), 6030. 0 / 0 / 88,230.18 | Order-desk payroll (a separate cost-center line, about $12.6k a month) runs through the 1/30/26 run and then stops. There are an HR RIF memo, three **signed** separation agreements (2/2-2/4/26), a payroll register extract that ties to the 14 GL rows, and a COO email saying the roles are not backfilled. The Feb-26 severance of $11,850 is booked but not claimed. | **ACCEPT 0 / 0 / 88,230.18** (ADEQUATE). The realized pro forma positive control. FY2026 stays 0 by presentation, so `verify_periods` is TTM only. Must not fire: PRO_FORMA_NOT_REALIZED. EXCESS_GL_ACTIVITY may be raised at INFO for FY2026 but must not change any amount; the severance is a separate cost, not an upward revision. |
| 5 | **Purchasing Manager eliminated** (Pro forma), 6040. 0 / 0 / 48,000 | The manager retired 12/31/25 under a signed agreement stating a **current base of $86,400**, and payroll of $3,600 semi-monthly stops after Dec-25. Management used the census **2026 approved salary of $96,000** x 6/12. | **REVISE 0 / 0 / 43,200** (PARTIAL). The contract-salary variant: carry the GL actual (12 x 3,600). Flag: PARTIAL_GL_SUPPORT. Must not fire: PRO_FORMA_NOT_REALIZED. |
| 6 | **Transaction bonuses** (Non-recurring), 6040. 0 / 90,000 / 90,000 | A **signed** Project Marlin Transaction Bonus Plan (11/14/25) pays one-time LOI payments to four executives; payroll ran 3/13/26. Closing payments of $170,000 are seller-funded and not in the GL. | **ACCEPT** (ADEQUATE). The transaction-compensation positive control. Must not fire: RECURRING_PATTERN, CONTINUING_OBLIGATION. The Jun-26 MIP payout in the same account is a different plan (D-2). |
| 7 | **Sprinkler line break** (Non-recurring), 6220. 0 / 100,000 / 100,000 | Invoices booked: $38,500 (Aug-25) + $33,500 (Sep-25) = **$72,000**. The $28,000 is a management **estimate never booked**: the controller's email says it was "not invoiced or booked" and the COO says the repair was done in-house. The insurer paid **$30,000 in May-26, credited to 6220** (contra) and not netted. | **REVISE 0 / 72,000 / 42,000** (RECOVERY_OFFSET). Combines PARTIAL_GL_SUPPORT with a same-account recovery that falls in TTM only (after 3/31/26). Flags: PARTIAL_GL_SUPPORT, OFFSETTING_RECOVERY. |
| 8 | **PFAS molded fiber write-off** (Non-recurring), 5300. 0 / 148,600 / 148,600 | A single Dec-25 entry for 4,929 cases. Customer PFAS-free mandates took effect 1/1/26; the supplier discontinued the line and refused returns; a disposal certificate shows no salvage. Routine cycle counts run about $3.2k a month, and annual counts were $8,940 and $10,420. | **ACCEPT** (ADEQUATE, ambiguity medium). **False-reject trap**: one large write-off among small routine entries. Must not fire: RECURRING_PATTERN. Minority alternative: REJECT as ordinary obsolescence. |
| 9 | **Brightfield arbitration** (Non-recurring), 6400. 0 / 51,000 / 34,200 | Three invoices for Brannock & Vail Matter 2025-014 ($16,800 Jun-25, $21,450 Aug-25, $12,750 Oct-25). The award denied all claims and the file is closed. The same firm bills an **unclaimed $3,500/mo general-counsel retainer** ("continues month to month until either party terminates it"). | **ACCEPT** (ADEQUATE). **False-reject trap**: a one-time matter from a firm that also bills a retainer. Must not fire: RECURRING_PATTERN, CONTINUING_OBLIGATION, OUT_OF_PERIOD (billing periods sit in the same period labels as their bookings). |
| 10 | **KestrelWMS implementation** (Non-recurring), 6600. 0 / 128,400 / 144,600 | The order form splits a **one-time $64,000 implementation fee** (2 x $32,000) from a **$5,400/mo subscription** (36 months, auto-renew). Management claimed all Kestrel activity, including 6 (FY2026) and 9 (TTM) subscription months and **both postings of go-live bill KS-10442**. | **REVISE 0 / 64,000 / 64,000** (CONTRADICTED). An entry-level split. Flags: CONTINUING_OBLIGATION, CONTRADICTORY_EVIDENCE, DUPLICATE_GL_ENTRY. The second KS-10442 posting is carried by **D-1**, not here, so nothing is counted twice. |
| 11 | **Distribution network study** (Non-recurring), 6420. 0 / 54,000 / 54,000 | The engagement letter sets one fixed fee of $84,000 in 3 phases: $30,000 Oct-25, $24,000 Dec-25 and $30,000 Feb-26. Management's own support ref cites the **phase 3 invoice (VDR 6.4.3)**, but the claim includes phases 1 and 2 only. | **REVISE 0 / 84,000 / 84,000** (UNDERSTATED, ambiguity medium). An upward revision above the claim under the SPEC 5.4 EXCESS_GL_ACTIVITY carry rule. Flag: EXCESS_GL_ACTIVITY. Must not pull in the SafePoint EHS quarterly audits in 6420. Pre-registered alternative: ACCEPT 0 / 54,000 / 54,000. |
| 12 | **Sunmeadow termination settlement** (Non-recurring), 8000. 0 / +46,500 / +46,500 | A one-time $46,500 **termination fee received**, credited to 8000 Other Income (inside EBITDA), under a signed agreement. | **REVISE 0 / -46,500 / -46,500** (SIGN_ERROR). Removing a one-time gain reduces EBITDA. Flag: SIGN_ERROR. |
| 13 | **Prior-period freight true-up** (Out-of-period), 5400. 0 / 38,400 / 38,400 | Altamaha bill AFL-TU-25-118 was booked 11/14/25. The invoice states a **service period of Apr 1 - Sep 30, 2025** at $6,400 a month. | **REVISE 0 / 0 / 19,200** (OUT_OF_PERIOD). The item straddles the FY2026/TTM overlap. FY2026 contains the booking and all 6 service months, giving 0. TTM holds the booking but only Jul-Sep, so it keeps the Apr-Jun half (+19,200). Flag: OUT_OF_PERIOD. |
| 14 | **Refinancing costs** (Non-recurring), 6400 and 8100. 0 / 69,600 / 69,600 | Marlowe's debt placement fee of $42,000 sits in 6400. The $27,600 write-off of unamortized debt issuance costs sits in **8100 Interest Expense**, which management's interest line already adds back. | **REVISE 0 / 42,000 / 42,000** (EBITDA_EXCLUDED). A partial ALREADY_EXCLUDED case. Flag: ALREADY_EXCLUDED_FROM_EBITDA. |
| 15 | **Prepayment premium** (Non-recurring), 8200. 0 / 18,500 / 18,500 | The payoff letter shows 2.00% of $925,000 prepaid. It is booked in **8200 Other Expense**, which is inside EBITDA. | **ACCEPT** (ADEQUATE). The contrast case to D1 M-07. Must not fire: ALREADY_EXCLUDED_FROM_EBITDA. |
| 16 | **Sale-process professional fees** (Non-recurring), 6400 and 6410. 0 / 95,000 / 95,000 | Cordell Harbor's **one-time retainer of $35,000 is creditable against the success fee**. Whitlock & Rowe's sell-side QoE is a $60,000 fixed fee paid in **2 x $30,000 installments**. Routine CPA fees in 6410 are unclaimed. | **ACCEPT** (ADEQUATE). **False-reject trap**. Must not fire: CONTINUING_OBLIGATION, RECURRING_PATTERN. This is also the row management's printed total omits. |

**Diligence items** (`GroundTruth.diligence_items`):

| Item | Truth | Basis |
| --- | --- | --- |
| D-1 Duplicate Kestrel posting | REVISE 0 / 32,000 / 32,000 | KS-10442 ($32,000, 6600) is posted on 10/3 and again on 10/9/25 with the same document number and different Internal IDs. The invoice shows one charge, and Kestrel's statement shows the second payment as a $32,000 unapplied credit. The first posting stays in ref 10. Flag: DUPLICATE_GL_ENTRY. |
| D-2 FY2026 MIP accrual (supported top-side) | REVISE 0 / -186,000 / 0 | Management's P&L accrues $186,000 in 6040 in Mar-26 and reverses it in Jun-26, when NetSuite payroll pays it (6/12/26). The plan, adopted 4/8/25, earns awards on 3/31/26, and the calculation the Board of Managers approved (4/24/26) ties to the payout. Keeping the accrual gives FY2026 = GL - 186,000. TTM = GL carries one full plan-year award, which equals a ratable accrual (9/12 of FY2026 plus 3/12 of the FY2027 plan the Board adopted on 4/7/26 on the same terms). This is the D1 panel's cash-to-accrual contrast, adapted to a March year-end. Encoded as a period move of the payment row to Mar-26. |
| D-3 Aug-2024 GL export gap | REVISE -363,586.47 / 0 / 0 | The Aug-24 GL batch was exported with the 16-account flash search, per the NetSuite administrator's email. Management's P&L, which ties to the trial balance, holds the other 23 accounts' August activity. Keeping management's August amounts (the 20 EBITDA accounts, from 5300 3,866.00 to 8000 -806.41) avoids overstating FY2025. This is now a SPEC 5.7 documented GL-export gap, matched under SPEC 9 by its non-zero period labels. The amount is computed by the generator from the dropped ledger rows, not typed. |

**Expected totals** (FY2025 / FY2026 / TTM):

- Claims are 648,000 / 1,488,000 / 1,623,630.18. The printed total is 648,000 / 1,393,000 / 1,528,630.18 because ref 16 is omitted.
- Management finals are 480,000 / 1,098,600 / 1,202,430.18.
- Pending (ref 3) is 60,000 in each period.
- Diligence items total -363,586.47 / -154,000 / 32,000.
- Diligence adjusted EBITDA is GL + finals + diligence items = 8,138,231.89 / 8,362,630.47 / 8,678,244.77, computed by the generator.

## Planted data-quality issues

| Code | Locator | Detail |
| --- | --- | --- |
| `DUPLICATE_GL_ENTRY` | 2025-10, 6600, both rows | Kestrel bill KS-10442 is posted twice, six days apart, under one document number (rows 4046 and 4084). Both postings are inside ref 10's claim, and D-1 reverses the second. The package does not say how the second entry arose. |
| `MISSING_PERIOD` | 2024-08 | The GL holds 16 of the 39 accounts active in August (41%, under the 50% threshold). The P&L has the full month. |
| `RECON_VARIANCE` | 2026-03, 6040 | The P&L exceeds the GL by 186,000 because of the MIP accrual top-side. |
| `RECON_VARIANCE` | 2026-06, 6040 | The P&L is 186,000 below the GL because the top-side is reversed when the bonus is paid. |
| `MGMT_EBITDA_DIFFERS_FROM_GL` | none (code only) | Management's reported EBITDA less GL is -363,586.47 in FY2025 (missing month) and -186,000 in FY2026 (MIP). TTM is 0. |
| `MGMT_SCHEDULE_ARITHMETIC` | none (code only) | The printed total equals the sum of refs 1-15; ref 16 (95,000 in FY2026 and TTM, listed last) is not included, so adjusted EBITDA is understated. The schedule holds values, not formulas. |
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
   - SPEC 9 now matches such an item to an unmatched tool diligence item with no GL links and the same non-zero period labels. Until `evaluate.py` implements that rule, report FY2025 ebitda_error with and without D-3.
   - A tool that reverses the August difference to the GL overstates FY2025 by 363,586.47.
2. **D-2 period adaptation.** The D1 panel described a Dec-25 accrual paid Mar-26, but under a March year-end both dates sit in FY2026 and TTM. The key uses the equivalent year-end pattern instead: an accrual at 3/31/26, paid Jun-26.
3. **Ref 2 applies current market rent to every period**, the usual related-party normalization. The BOV comparables span 2024-25, so FY2025 is also supported. Ambiguity is medium: no post-close lease is executed, so REJECT 0/0/0 is pre-registered.
4. **Ref 7 recovery timing.** The amounts do not depend on recovery timing. Whether the $30,000 is accrued at 3/31/26 as a probable recovery (the 4/30/26 letter is a recognized subsequent event if it precedes issuance) or taken when received in May-26, removing the whole event (cost and recovery) gives FY2026 +72,000 against the GL as booked, and TTM +42,000.
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
- Panel review additions (all opt-in or inert for other specs; Meridian still regenerates byte-identically):
  - top-level `distinct_amount_days` stops allocate-mode streams repeating an exact amount within a month, or for the same counterparty within the window across months, and rejects any other same-account, same-counterparty, same-amount GL pair inside the window;
  - the `{prev_q}` placeholder (quarter of the previous month) for quarterly credits booked after quarter-end;
  - `{row:KEY}` in answer-key prose, replaced with the key's GL source row.
- These options are documented in `scripts/qoe_synth/SPEC_FORMAT.md` and exercised by `tests/test_generator_tidewell.py`.

## Panel review

Three reviewers (R1, R2, R3) critiqued this key, and the engagement partner adjudicated. Nobody found a wrong
answer: no treatment or amount changed anywhere in the key. The decisions below were applied to
`data/specs/tidewell_distribution.yaml`, `docs/SPEC.md`, `qoe/schemas.py` (a comment only),
`scripts/qoe_synth/` (additive options only) and this file, and the package was regenerated. The engine and AI
code were still not read, and the review engine was not run on this deal.

### Decisions and what changed

| # | Item | Decision | What changed |
| --- | --- | --- | --- |
| 1 | Ref 10 expected flags | CHANGE | `expected_flags` is now CONTINUING_OBLIGATION, CONTRADICTORY_EVIDENCE, DUPLICATE_GL_ENTRY. The schedule calls all Kestrel activity "One-time cost of implementing", while KS-SUB-2511 says "Recurring monthly subscription" and the order form sets $5,400 a month for 36 months with auto-renewal. This is the SPEC 5.4 example trigger and the D1 M-06 analog. The reviewer note explains it. Amounts and rows are unchanged. |
| 2 | Ref 10 ASU 2018-15 alternative | NOTE | Ambiguity stays low and nothing is pre-registered. The reviewer note records the GAAP minority view (capitalize and amortize over 36 months: 0 / 53,333.33 / 48,000) and why it is not carried. |
| 3 | Ref 2 related-party rent | NOTE | Ambiguity is now medium, with REJECT 0/0/0 pre-registered in the reviewer note: the 2019 lease binds at $24,000 flat to 3/31/2029 and no post-close lease is executed. The note also records the ASC 842 straight-line figure (about $369,516 a year, -81,516 per period), which is not carried. The first question topic now asks whether the 2019 lease is terminated and replaced at closing. The optional plant of an executed post-close lease was not made, so ambiguity stays medium. |
| 4 | Ref 3 family office | NOTE | REQUEST_INFO stays primary, with REJECT 0/0/0 as the alternative. REVISE -60,000 is recorded as not pre-registered. The rationale now says that on management's own description nothing is expensed, so the add-back runs the wrong way, and that a lost free service is a buyer consideration. New question topic on the reverse direction (Company resources serving the family office). |
| 5 | Ref 11 ambiguity and fit tie | NOTE | Ambiguity is now medium, with ACCEPT 0 / 54,000 / 54,000 pre-registered as a buyer-conservative minority view. The reviewer note records the claimed-set tie ({RSC-2291, RSC-2344} and {RSC-2403, RSC-2344} both fit 54,000; the earliest-entries tie-break picks phases 1 and 2). R1's change to the phase amounts was rejected. |
| 6 | Ref 11 EXCESS_GL_ACTIVITY carry rule | CHANGE | SPEC 5.4 now has an EXCESS_GL_ACTIVITY row: INFO by default, and the unclaimed entry is carried (WARNING) only for a non-pro-forma, non-normalization item with one fixed-fee engagement, the document cited in the support refs, and a non-zero claim in that period. Ref 11's note cites the rule. SPEC 5.5 was not read; the row went into the 5.4 table. Checked against the key: only ref 11 carries anything. |
| 7 | SPEC 9 false_accept_rate | CHANGE | A false accept now needs the expected treatment to be REQUEST_INFO or the accept to overstate EBITDA by more than 1.00 in some period. An ACCEPT on an item whose expected amounts are at or above the claim is a missed revision. Only ref 11 is affected. |
| 8 | Refs 4, 5, 11 EXCESS_GL_ACTIVITY consistency | CHANGE | Ref 4's must-not list drops EXCESS_GL_ACTIVITY: it may be raised at INFO for FY2026 (125,801.84 of order-desk payroll from Apr-25 to Jan-26) but must not change any amount, and the Feb-26 severance must not be folded in. Ref 5 accepts the same INFO flag with FY2026 at 0. `GroundTruth.notes` now states the unclaimed-entry rule used in this key. |
| 9 | Ref 12 sign error reachability | NOTE | The key stays REVISE 0 / -46,500 / -46,500. The SPEC 5.4 SIGN_ERROR effect cell now says proposed follows the debit-positive supporting entries, so an add-back made of credits comes out negative. The reviewer note says the amount is reachable without a special rule. |
| 10 | D-3 scoring and scope | CHANGE | SPEC 5.7 adds "Documented GL-export gap" under other supported reporting differences. SPEC 9 diligence_item_accuracy matches an expected item with no GL rows by its non-zero period labels. The D-3 reviewer note records the practitioner view and asks the evaluation report to show FY2025 ebitda_error with and without D-3 until the rule is implemented. R3's replacement-export option was rejected. |
| 11 | VDR 1.1 account list | CHANGE | The email now reads "sales, product cost, freight, ...", because the export dropped 5300 (also a cost-of-sales account). keep_accounts is unchanged, so D-3 is unchanged. |
| 12 | D-2 TTM basis and approval | CHANGE | VDR 1.2 now says the Board of Managers approved the calculation and adopted the FY2027 MIP on 4/7/26 on the same terms. VDR 1.4's approval line is the Board of Managers (W. Carrow and L. Carrow, Managers). The reviewer note explains that TTM = GL equals a ratable accrual (139,500 + 46,500). The first question topic now covers FY2027 adoption and the Apr-Jun 2026 accrual. Ambiguity stays low. |
| 13 | Ref 7 recovery timing and rationale | CHANGE | The rationale now says only Coastal Empire's invoice cites the claim, and the Palmetto State letter itemizes both invoices. The reviewer note and judgment call 4 say the amounts do not depend on recovery timing. New question topic on the capex treatment of the $17,000 betterment and the replacement racking. The optional sentence was added to VDR 6.1.2 (the branch line was repaired by the fire-protection contractor at no charge). |
| 14 | Ref 13 OUT_OF_PERIOD trigger | CHANGE | The SPEC 5.4 trigger now works on any period label. Ref 13's note says the flag fires on the TTM label only; ref 9 still does not fire. The D1 re-run is still to do (see below). |
| 15 | Ref 13 row in supporting_gl_rows | NOTE | The row stays supporting, as for D1 M-10. `GroundTruth.notes` says a row replaced by its OUT_OF_PERIOD effect stays supporting. SPEC 9 gl_link_precision/recall counts it as supporting. |
| 16 | Ref 4 severance weeks | CHANGE | VDR 3.1 and the three separation agreements now say four weeks' pay. Amounts are unchanged. |
| 17 | Ref 4 B2B portal timeline | CHANGE | VDR 3.1 now says Charleston customers were moved onto the portal in September 2025. New question topic on incremental portal costs to net against the savings. |
| 18 | Ref 6 plan records a later LOI date | CHANGE | Page 2 of VDR 3.3 is now a "CERTIFICATE OF LOI DATE - March 10, 2026" signed by Lena M. Carrow, Manager (not a participant). The plan still carries Exhibit A. The key phrases now point at the certificate. The doc_id and supporting_docs are unchanged. |
| 19 | Ref 16 QoE scope | CHANGE | VDR 8.2 scope is now FY2025 and the nine months to 12/31/25, with the TTM then ended. The invoice and GL row are unchanged. |
| 20 | Ref 8 customer ranking | CHANGE | VDR 6.2 now reads "Three major foodservice customers, including our two largest". After regeneration Coastal Kitchen (3.73M) and Lowcountry (3.71M) still rank first and second in FY2026 account 4000, and Island Grill ranks 10th of 11. |
| 21 | Refs 1 and 2 Holloway wording | CHANGE | VDR 2.2 now says "expected fiscal 2026 revenue" and "as a substitute for distributions". |
| 22 | Refs 1 and 2 re-dating, ref 2 support refs, S-corp year-end | REJECT | No change. This is a deliberate design choice: pre-LOI bidder work is plausible in a second-round auction; citing VDR 2.4 is what links the planted contradiction; and the book year can differ from the tax year. |
| 23 | Ref 1 Medicare alternative | REJECT | No change. The 7,830 stays a note on unclaimed upside, consistent with D1 M-05 and the unclaimed-entry rule. |
| 24 | Ref 5 census footnote | REJECT | No change. The footnote already dates the $96,000 rate to the November 2025 review; adding "never paid" would put the answer in the document. |
| 25 | Refs 14 and 15 refinancing timeline | CHANGE | VDR 7.1.1 now says the facility was funded on January 30, 2026 with the Ogeechee payoff. New ref 14 question topic on use of the Coastal Trust proceeds and distributions (net debt). No GL rows were added. |
| 26 | MGMT_SCHEDULE_ARITHMETIC wording | CHANGE | The arithmetic note, the ref 16 reviewer note and SPEC_FORMAT no longer mention a SUM range. The note says the printed total equals refs 1-15 and the schedule holds values, not formulas. |
| 27 | D-1 duplicate cause | CHANGE | "(AP inbox and vendor portal)" was removed from the DQ note. D-1's question topic now asks about AP duplicate-invoice controls: KS-10442 was entered twice under one number and paid on 10/24 and 10/31/25. |
| 28 | Background GL realism | CHANGE | Vendor rebates: one credit per vendor per calendar quarter, booked the month after quarter-end (Jan, Apr, Jul, Oct, never August), at a steady 3 : 2 : 2 : 1 mix. Greenleaf runs through its Q2-2025 rebate (Jul-25). Repeated amounts: `distinct_amount_days: 7`, and the generator now asserts that the only same-account, same-counterparty, same-amount pair within 7 days is KS-10442. Same-month repeats in 4000, 4100 and 5000 are also gone. GL rows went from 6,027 to 6,033. |
| 29 | case_type vocabulary | CHANGE | The `ExpectedAdjustment.case_type` comment in `qoe/schemas.py` now lists UNDERSTATED, SIGN_ERROR, DUPLICATE_POSTING, SUPPORTED_TOPSIDE and MISSING_GL_MONTH. SPEC 9 by_case_type points to that list. The labels were not remapped. |

### Effect of the regeneration

- **Key amounts.** Every treatment and amount is unchanged, including D-3 at -363,586.47. The regeneration
  holds every stream's monthly totals, and no rebate falls in August.
- **What moved.** Only 5200 Vendor Rebates changed GL EBITDA:

  | | FY2025 | FY2026 | TTM Jun-26 |
  | --- | ---: | ---: | ---: |
  | GL EBITDA, before | 8,022,682.75 | 7,496,760.71 | 7,517,054.01 |
  | GL EBITDA, after | 8,021,818.36 | 7,418,030.47 | 7,443,814.59 |
  | Diligence adjusted EBITDA, before | 8,139,096.28 | 8,441,360.71 | 8,751,484.19 |
  | Diligence adjusted EBITDA, after | 8,138,231.89 | 8,362,630.47 | 8,678,244.77 |

  Management's reported EBITDA moves by the same amounts, and the reported-less-GL differences
  (-363,586.47 / -186,000 / 0) are unchanged.
- **GL rows.** Rows after April 2024 shifted:

  | Item | Before | After |
  | --- | --- | --- |
  | Ref 10 implementation | 3380, 4040 | 3385, 4046 |
  | D-1 | 4078 | 4084 |
  | Kestrel subscriptions | 4043-5858 | 4049-5866 |
  | Ref 11 | 4092, 4549, 5081 | 4098, 4557, 5090 |
  | Ref 12 | 4289 | 4298 |
  | Ref 13 | 4346 | 4355 |
  | Ref 14 | 4818 (4920 related) | 4825 (4929 related) |
  | Ref 15 | 4908 | 4917 |
  | Ref 4 severance | 5027 | 5036 |
  | D-2 | 5908 | 5915 |

  Notes that cite a row now use `{row:KEY}`, so they follow the GL.
- **Background rows.** Background document numbers also changed, because the shared number RNG runs in date
  order. Dimension noise is unchanged (180 / 87 / 265 blank Department / Class / Location).
- **Independent recompute.** From the regenerated GL, P&L and schedule:
  - P&L less GL is non-zero only in Aug-24 (23 accounts) and in 6040 (+186,000 Mar-26, -186,000 Jun-26).
  - The management interest line equals GL 8100 (162,116.94 in FY2026).
  - The schedule holds no formulas and its printed totals are 648,000 / 1,393,000 / 1,528,630.18.

### Still open (outside this deal's files)

- **SPEC 5.4 OUT_OF_PERIOD.** Re-run D1 with the engine to confirm the reworded trigger does not fire on an
  ordinary in-arrears bill at the TTM boundary. That run was not made here: the independence rules forbid running
  the engine.
  - A static read of the D1 spec finds one candidate. H&C invoice 25-0910 was booked 9/10/25 for "professional
    services rendered ... through August 31, 2025", and the prior invoice ran through 5/31/25.
  - If the engine infers a Jun-Aug 2025 service period, TTM (from Jul-25) holds the booking but not June, and the
    new wording would move 7,000 out of M-01's TTM.
  - The partner's fallback (exclude a service period that ends in the month just before booking) covers it. The
    fallback leaves ref 13 (service to Sep-25, booked Nov-25) and D1 M-10 (service to Dec-24, booked Mar-25)
    firing.
- **evaluate.py.** Implement the SPEC 9 changes: the false-accept rule, OUT_OF_PERIOD rows counted as
  supporting links, no-GL-row diligence-item matching, and the case_type vocabulary. Until then, report FY2025
  ebitda_error with and without D-3.
