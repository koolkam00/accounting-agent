# D1 answer-key review (Meridian Mechanical)

**Who reviewed it:** an AI reviewer panel, not human practitioners. Three independent reviewers each took a lens (Big-4 Deals senior manager, buy-side PE partner, audit senior who recomputes every number), and a fourth AI agent adjudicated their findings. The benchmark protocol still requires a human practitioner to review every answer key before it is used; this record is the pre-screen.

**Outcome:**

- **Truths.** All 14 truth treatments and amounts were confirmed.
- **Answer key.** It changed in two places: a diligence-identified duplicate-posting item was added (D-1, +18,400 in FY2025), and the top-side bonus fact pattern was made determinate.
- **Spec.** Six engine rules changed so the correct answers are reachable (SPEC §5.3, §5.4, §5.5, §5.7).
- **Package.** Package documents were strengthened (SPEC §10.1).

The adjudicator's decisions follow verbatim.

## DQ-DUPLICATE_GL_ENTRY (6200 Coastal Risk, May-2025) [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
I agree with all three reviewers. The P&L carries an exact doc_number duplicate twice, so FY2025 expense is overstated by one posting. If the bill was paid once, AP is overstated; if it was paid twice, a refund is receivable. Either way the P&L effect is the same, so buy-side's 'pending payment confirmation' is not needed and I reject it.

Corrected key:
- New diligence-identified item DQ-D1 'Reverse duplicate Coastal Risk posting': FY2024 0 / FY2025 +X / TTM 0. May-2025 falls before Jul-2025.
- supporting row: the later posting. related row: the first posting.
- X must be stated in §10. I recommend planting the bill as a monthly premium installment (e.g. Num CRI-25-0507, $18,400.00) so there is no prepaid or cut-off confound.

Spec and schema changes:
- Add GroundTruth.diligence_items {id: {period: amount}}.
- Change the §3.8/§5.6 identity to gl_ebitda + Σ non-REQUEST_INFO finals + Σ diligence items.
- Add bridge rows `dil_dq:<issue_id>` (kind diligence_adjustment), generated only for doc_number duplicate groups. Memo-within-7-days groups remain questions only.
- A posting that a management adjustment's final already carries is excluded, so nothing is counted twice.
- evaluate._score_ebitda adds tool dil_dq amounts.

Effect on the key: GT diligence EBITDA FY2025 becomes gl + 335,700 + X. FY2024 and TTM are unchanged.

Question topics: single vs double payment (AP and disbursement detail); vendor credit or refund.

I reject the memo-only alternative. §3.8 says GT amounts are what a careful senior would carry. The answer sheet's DQ and EBITDA_DILIGENCE rows would also mark participants who correctly carry +X as wrong.

## DQ-RECON_VARIANCE / top-side bonus accrual (6000, Dec-2025) [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
On the facts as planted, the key cannot be defended. Nothing shows whether the $25,000 is a real obligation, and reversing it raises EBITDA, which is the aggressive direction.

I reject buy-side's fix (carry −25,000, and make dil_recon reverse only differences that increase EBITDA). It builds a buyer bias into the bridge and still rests on an assumption.

Instead, change the plant so the current key is correct:
- Add a controller email (Jan-2026, in the Monthly P&L folder). It states that the Dec-2025 top-side is a proposed discretionary bonus pool the owner has not approved, that nothing has been communicated to employees or paid, and that it will not be booked to QuickBooks.
- The generator asserts there are no bonus payments in 6000/6010 anywhere in Jan-2024 to Jun-2026, and no Dec-2024 top-side.

With no approval, no past practice and no payment, there is no liability at 31-Dec-2025, so reversing to GL is what a careful senior would carry.

Key amounts unchanged: dil_recon 0 / +25,000 / +25,000.

GroundTruth.notes: ambiguity low. The contrasting fact pattern goes in D2, not here: an approved bonus paid through GL in Q1-2026, where FY2025 = GL − 25,000 and TTM = GL.

Question topics: bonus plan and approval; payment timing; whether the buyer expects to fund bonuses after close.

Recommended: make dil_recon a reviewable line in §7.

## DQ-MGMT_EBITDA_DIFFERS_FROM_GL key encoding [deals-senior-manager, arithmetic-auditor] -> CHANGE
Encode the expected entry as ExpectedDataQuality(code=MGMT_EBITDA_DIFFERS_FROM_GL, month=null, account=null, note='management reported EBITDA below GL by 25,000 in FY2025 and TTM Jun-26; FY2024 0'). qoe/evaluate.py _dq_matches already matches on code alone when the key specifies no locator.

I reject the senior manager's month='2025-12'. The tool's issue is period-level: it carries period_label and no month. A key entry that specifies a locator the issue does not carry returns False, so that encoding could never be detected.

The other two entries:
- RECON_VARIANCE: month '2025-12', account '6000', note 'pl − gl = +25,000 debit-positive'.
- DUPLICATE_GL_ENTRY: month '2025-05', account '6200', gl_rows = both postings.

Change the §9 text from 'code and month or account' to 'code plus every locator both sides carry; a key entry with no locator matches on code'. Adding period_label to ExpectedDataQuality is optional and can come later.

## M-03 [all three lenses] -> CHANGE
Truth stays REVISE 0 / 31,200 / 31,200:
- club dues 12 × 1,100 = 13,200 and lease 12 × 1,500 = 18,000 in each period;
- travel 3 × 5,600 = 16,800 removed in each period (Mar/Sep/Nov-25 for FY2025; Sep/Nov-25 and Mar-26 for TTM).

As planted, the key is unreachable. 31,200 of 48,000 (65%) has no linked document, so §5.5 step 4 forces REQUEST_INFO.

Package additions:
1. BMW Financial Services lease: lessee D. Castellano, X5, $1,500/mo, commencing Jan-2025.
2. Pelican Bay Country Club statement: member R. Castellano, individual membership since Jan-2025, $1,100/mo.
3. Replace the registration confirmations with per-trip expense reports of $5,600 each, itemizing registration, airfare and hotel with the business purpose. Put the report number in the GL Num so they link.

The commencement dates also explain why nothing appears in FY2024.

Generator constraint: the M-02 draft employment agreement must be silent on club dues and vehicles. Otherwise the data room contradicts the add-back.

Key fields:
- supporting_docs: lease and club statement; the expense reports are related.
- expected_flags: [CONTRADICTORY_EVIDENCE]. case_type: CONTRADICTED. ambiguity: low.
- reviewer_note: 'Club may be partly used for customer entertainment; RECURRING_PATTERN must not fire (recurrence is the premise of an owner item).'
- Question topics: who D. Castellano is and how the car is used; whether the membership and lease end or pass to the owner at close; perquisites in the post-close agreement; any FY2024 personal expenses.

I reject buy-side's fallback of changing the truth to REQUEST_INFO. The documents are cheap to plant, and this item exists to test the business vs personal split.

## SPEC §5.4/§5.5 NO_DOCUMENT_SUPPORT gate order [SM M-07/M-13; AU M-07, M-11; all lenses M-03/M-09/M-14] -> CHANGE
Confirmed. Step 4 runs before REJECT and is measured on the claimed amount. That sends several correct REJECT/REVISE keys to REQUEST_INFO:
- M-07: the 22,000 non-cash write-off is 63% of 35,000 and undocumented.
- M-11: the TTM claim of 80,000 has no entries, so it is 100% undocumented.
- M-13: the JE has no counterparty, and the memo states no amount.

Fix the spec, not the truths. Compute NO_DOCUMENT_SUPPORT per period over supporting entries after every challenge removal and period move (ALREADY_EXCLUDED, OVERLAP, CONTRADICTORY, CONTINUING, RECURRING, PERIOD_MISMATCH, OUT_OF_PERIOD). That is, measure it over the amount diligence would carry. A period whose supporting total is 0 cannot trigger it. Documents are needed for what we carry, not for what we reject. It can still be raised as INFO on the claimed set to prompt questions.

This cannot create a false accept, because removals already move the proposal away from the claim.

Package ties are still needed where an amount is carried: M-03 docs, M-09 repair invoices, M-14 claim-amount document and M-05 installment wording (see those entries).

M-07 REJECT 0/0/0 and M-13 REJECT 0/0/0 stand.

## SPEC §5.3/§5.4 claimed-set tie-break and RECURRING_PATTERN scope [SM M-06; AU M-06, M-03, M-08; BS GT-SCHEMA materiality floor] -> CHANGE
Add four rules:
1. Among exact subset fits, prefer the most whole groups, then entries cited by support refs, then the earliest entries. If still tied, record the ambiguity.
2. A group's event window is the union of the months of its claimed entries across all period labels.
3. The '≥3 similar months' leg counts a month only when its similar activity is at least 25% of the group's average claimed monthly amount.
4. RECURRING_PATTERN does not apply to OWNER_DISCRETIONARY or NORMALIZATION categories, where recurrence is the premise.

Effects on deal 1:
- M-06: the TTM claimed set becomes Jul–Dec 2025 (6 × 8,000 = 48,000; otherwise C(12,6) = 924 equal fits). Jan–Jun 2026 are then 6 similar months outside the window, so RECURRING fires deterministically. Keep M-06 flags [CONTRADICTORY_EVIDENCE, CONTINUING_OBLIGATION, RECURRING_PATTERN], and state the TTM composition in the rationale.
- M-03: club dues and lease stop false-firing.
- M-14: routine $300–700/mo write-offs fall below the floor.
- M-01 and M-13 still fire through the ≥50% other-fiscal-period leg (36,000 vs 35,500; 58,500 vs 64,000).

I reject the senior manager's option of dropping RECURRING from M-06. The same-rate billing in 2026 is exactly what a senior would cite.

## SPEC §5.4 CONTINUING_OBLIGATION 'retainer' trigger [BS M-08, M-04; AU M-08, M-04] -> CHANGE
Read literally, a 'retainer' fact would strip Keel Harbor's 26,000 (M-08 falls to 15,000) and Barrow's installments (M-04 becomes REJECT).

Refine the trigger: the term fact must carry the obligation into the go-forward cost base. That means a periodic fee (monthly or quarterly), 'until terminated', auto-renew, or a service term_end after the last claimed month. A one-time retainer tied to a single transaction or search does not qualify.

M-01 Matter 1004 ('$2,500 per month … until terminated') and M-06 (monthly fee, 36-month term, auto-renew) still trigger.

Package wording:
- Keel letter: 'one-time retainer of $26,000 payable on signing, creditable against the success fee'.
- Barrow letter: keep the 'retained search' wording as a deliberate trap.

Record must-not flags in reviewer_note: M-04 CONTINUING_OBLIGATION and RECURRING_PATTERN; M-08 CONTINUING_OBLIGATION.

## M-08 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
Amounts confirmed: Keel 26,000 (Oct-25) + D&P 15,000 (Nov-25) + H&C 25-0910 21,000 (Sep-25) = 62,000 in FY2025 and in TTM. Removing the overlap gives 41,000 / 41,000. REVISE 0 / 41,000 / 41,000 with OVERLAP_WITH_OTHER_ADJUSTMENT: M-01 keeps 25-0910 on link score, and on schedule order if tied.

As planted, the claimed set cannot be derived. My own count is 18 distinct exact 62,000 subsets in FY2025 among the H&C, Keel and D&P entries alone (the auditor said 12; the conclusion is the same) and 2 in TTM.

Package fix: M-08's Support Ref cites the data-room file of H&C invoice 25-0910 (e.g. 'DR 7.1; DR 7.2; DR 4.2.4'). The generator asserts that the intended set is the unique fit under the new §5.3 tie-break.

I reject the auditor's PARTIAL_GL_SUPPORT as an alternative flag.

Must-not flag: CONTINUING_OBLIGATION.

reviewer_note: 'Part of the readiness work (annual audit) may recur under PE ownership; that is a buyer pro forma item.'

Question topics: banker success-fee terms; sale-process fees in Jan–Jun 2026 that were not claimed.

## M-09 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
Truth REVISE 58,000 / −40,000 / 0 is confirmed:
- 38,000 + 20,000 in Oct–Dec 2024;
- the 40,000 recovery in Feb-2025 sits in 8000, which is inside GL EBITDA;
- TTM is 0.
It matches the GAAP route: accrue the probable recovery into FY2024, then remove the 18,000 net loss.

Package additions:
- Gulf Coast Roofing ($38,000) and Tampa Bay Restoration ($20,000) invoices, each citing claim FL-24-88172.
- An itemized settlement letter: loss 58,000; non-covered 8,000 with a stated reason (e.g. above a sublimit); covered 50,000; deductible 10,000; paid 40,000; claim closed.

Key fields:
- supporting_docs: add both invoices. flags: [OFFSETTING_RECOVERY]. case_type: RECOVERY_OFFSET. ambiguity: medium.
- Pre-register the alternative REVISE 40,000 / −40,000 / 0 in key_alternatives.csv. Under that view the 18,000 uninsured storm cost is a recurring cost of operating in Florida, and only the timing of the recovery is corrected.
- reviewer_note: 'REJECT 0/0/0 is not coherent: it leaves the FY2025 recovery gain in EBITDA. The FY2025 −40,000 is a diligence effect in a period management left at 0, shown in dil:M-09.'
- Question topics: storm history and deductibles; storm-driven Q4-2024 revenue; the lease's roof-repair obligation; capex vs repair split.

## M-14 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
Truth ACCEPT 0 / 52,000 / 52,000 is confirmed: Oct-2025 falls in both FY2025 and TTM.

The current ambiguity note is incoherent. Routine $300–700/mo write-offs are not claimed, so 'the excess over normal' is the full 52,000.

Replace reviewer_note with: 'Alternatives: normalize 6950 to the Jan-2024 to Jun-2026 average, giving about −20,800 / +31,200 / +31,200 at roughly $500/mo background (a 2-year average gives −26,000 / +26,000 / +26,000); REJECT as inherent builder credit risk is a minority view.'

Ambiguity medium. Pre-register only the 30-month-average REVISE, with exact amounts computed from the generated 6950 activity. The same incoherent example appears in benchmark_protocol.md §4.2 (line 89) and must be replaced.

Package additions:
- An Official Form 410 proof of claim (or a customer statement) for $52,000, listing Halvorsen invoices dated Jun–Aug 2025. These are FY2025 revenue, so no Dec-2024 allowance question arises.
- Background 6950 memos must not share the Halvorsen theme.

Key fields: supporting_docs = the claim document and the Chapter 7 notice. Must-not flag: RECURRING_PATTERN.

Question topics: invoice dates and aging; lien and payment-bond rights (Fla. Stat. ch. 713); preference exposure; Halvorsen revenue and margin in TTM (lost customer).

Keep the low normal bad-debt level in D1 so this stays the ACCEPT control.

## M-02 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
REQUEST_INFO is correct under rule 2 (unsigned DRAFT, no benchmark).

Arithmetic: 24 × 27,500 = 660,000 in every period, and 660,000 − 300,000 = 360,000. Social Security, FUTA and Florida SUTA are capped below both salaries, so only employer Medicare changes: 1.45% × 360,000 = 5,220.

Ambiguity medium. Do not pre-register ACCEPT: carrying 360,000 on a draft is exactly the false accept this item tests.

The rationale must state the provisional amount: 360,000 per period, or about 365,220 with employer Medicare, before bonus and benefits.

reviewer_note: 'Many teams carry this provisionally on a buyer-negotiated agreement or a comp survey; the benchmark requires executed support.'

Add question topics: bonus, benefits and perquisites in the draft (links to M-03); whether Castellano stays as CEO or a hired replacement is needed; who drafted the agreement; other family members on payroll.

## M-12 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
REQUEST_INFO is correct under rule 1. Ambiguity medium.

Pre-register REJECT 0/0/0 in key_alternatives.csv; the EBITDA effect is the same. I decline buy-side's new acceptable_treatments schema field (see the GT-SCHEMA entry).

Rationale: provisional supported amount 0 / 0 / 0. The reduction is targeted for Q3-2026, after the TTM, so any credit belongs in a pro forma memo net of severance and backfill.

reviewer_note: 'M-12 depends on FieldPro continuing, which contradicts M-06's one-time label and corroborates the M-06 REJECT.'

Spec clarifications:
- In §10, 'acct 6000' names where the dispatcher payroll sits; the schedule's GL column stays blank.
- Plant dispatcher payroll as 3 × $55,000 = $13,750/mo in 6000, memo 'Payroll – Dispatch', through Jun-2026.

Add question topics: FieldPro auto-dispatch go-live status; payroll detail behind the 165,000; timing relative to close.

## M-01 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
REVISE 0 / 84,500 / 30,000 is confirmed:
- litigation: 14,500 + 22,000 + 18,000 + 21,000 + 9,000 = 84,500;
- TTM: Sep + Nov = 30,000;
- recurrence: Matter 1004 was 36,000 in FY2024 vs 35,500 claimed, which is ≥50%.

Ambiguity low.

reviewer_note: 'Alternative 0 / 90,000 / 35,500 (treating the Aug-2025 policy review as litigation remediation) applies only if Dawson were an employment claim. Not pre-registered.'

Package, for determinacy:
- The litigation engagement letter describes Dawson as a customer property-damage claim.
- The settlement agreement states a $100,000 self-insured retention for defense costs. 84,500 is below the retention, so no reimbursement is expected.

Add question topics: defense coverage, the retention and any reimbursement; the nature of the claim and loss runs for 2021–2026; non-monetary settlement terms; the post-close status of the Matter 1004 retainer.

## M-04 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
ACCEPT 0 / 45,000 / 15,000 is confirmed: ⅓ × 135,000 = 45,000 = 3 × 15,000 in Apr, May and Jul 2025, with only Jul in TTM. Ambiguity low.

reviewer_note: 'Buyer run-rate: if the CFO role is new and started in Aug-2025, full-year cost is understated by about 135,000 × 7/12 = 78,750 in FY2025 and 11,250 in TTM. That is a buyer pro forma item outside management's schedule. Must-not flags: CONTINUING_OBLIGATION (retained-search wording) and RECURRING_PATTERN (Indeed spend).'

Question topics: new vs replacement role; start date; interim coverage; any 2026 VP Sales search.

Optional realism change: first-year comp $180,000, making the fee 60,000 (3 × 20,000) and the key 0 / 60,000 / 20,000. Claims would become 418,000 / 1,019,000 / 1,039,500 and truth 16,000 / 350,700 / 249,200; the diligence vs management gap is unchanged. Not required.

## M-05 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
ACCEPT 0 / 0 / 75,000 is confirmed: 3 × 25,000 in Feb–Apr 2026, all in TTM.

Package wording must change so the key is reachable. The separation agreement must say 'three equal monthly installments of $25,000'. Otherwise the payroll entries cannot link by amount and counterparty, and NO_DOCUMENT_SUPPORT forces REQUEST_INFO. Key unchanged.

Must-not flag: RECURRING_PATTERN.

reviewer_note: 'Employer FICA on the severance (about 7.65% × 75,000 = 5,737.50 in 6050) was not claimed. It is immaterial seller upside. A backfilled VP Sales role is a buyer run-rate item.'

Question topics: backfill and replacement comp; COBRA and PTO payout; prior severance history.

## M-06 [deals-senior-manager, arithmetic-auditor] -> NOTE
REJECT 0 / 0 / 0 is confirmed. Brightline bills 8,000 × 18 months (Jan-2025 to Jun-2026): FY2025 is 96,000, and TTM GL activity is also 96,000 against a 48,000 claim.

The flag determinism is handled by the §5.3/§5.4 tie-break and event-window change. Keep all three flags.

The rationale must state that TTM 48,000 = Jul–Dec 2025.

reviewer_note: 'Management's TTM 48,000 is half the TTM GL of 96,000. Jan–Jun 2026 billing at the same rate is the recurrence evidence. M-12 treats FieldPro as an ongoing platform, which corroborates the rejection.'

## M-07 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
REJECT 0 / 0 / 0 with ALREADY_EXCLUDED_FROM_EBITDA is confirmed: 22,000 + 13,000 = 35,000 in Jun-2025, FY2025 only. The NO_DOCUMENT_SUPPORT change makes it reachable.

I reject the senior manager's request for a payoff letter that itemizes the 22,000. A lender's payoff letter does not carry the borrower's unamortized financing costs. If support is wanted, plant the company's own debt-issuance-cost amortization schedule instead (optional).

The rationale must cite that management's 'Interest expense' line equals GL 8100 including the 35,000, so the add-back double counts.

reviewer_note: 'Had these been booked in 8200 Other Expense, which is inside EBITDA, the add-back would be valid.' That contrast case goes in D2/D3.

## M-10 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> CHANGE
REVISE −42,000 / 42,000 / 0 is confirmed: 7,000 × 6 service months (Jul–Dec 2024), booked Mar-2025, with nothing in TTM.

The auditor's double-count is real. §5.4 defines proposed as supporting entries plus effects, and the OUT_OF_PERIOD effect adds the booking-month amount. If the entry also stays supporting, FY2025 comes out at 84,000.

Spec change: an OUT_OF_PERIOD entry leaves the supporting set and is replaced entirely by its effect.

The generator asserts there are no Apex or closeout true-ups in Q1-2024 or Q1-2026. Buy-side's unadjusted 2026 true-up plant moves to D2, not D1.

reviewer_note: 'The FY2024 −42,000 is a diligence effect in a period management left at 0, shown in dil:M-10.'

Question topics: whether closeout true-ups happen every year; the year-end job-cost accrual process.

## M-11 [deals-senior-manager, buy-side-investor, arithmetic-auditor] -> NOTE
REVISE 0 / 80,000 / 0 with PERIOD_MISMATCH is confirmed: 32,000 + 2 × 24,000, all in Feb–Apr 2025. The NO_DOCUMENT_SUPPORT change makes it reachable.

Generator:
- The two Brandon invoices get distinct numbers and memos ('Progress billing 1 of 2' / '2 of 2') and post more than 7 days apart.
- Assert zero unplanted duplicate groups across the deal.

reviewer_note: 'The $48,000 build-out is probably a capitalizable leasehold improvement. The add-back stands, but the amount belongs in the capex analysis.'

Question topics: old vs new rent (run-rate); overlapping rent months; capitalization policy.

## M-13 [deals-senior-manager, buy-side-investor] -> CHANGE
REJECT 0 / 0 / 0 is confirmed: the Dec-2024 58,500 is 91% of the 64,000, so the recurrence test passes. Key unchanged.

Package wording: the count memo must state the $64,000 current-year adjustment and the $58,500 prior-year adjustment. That links the memo to the JE, so the expected CONTRADICTORY_EVIDENCE flag attaches to the entry. Without it the flag can be missed, although REJECT still follows from RECURRING after the NO_DOCUMENT_SUPPORT change.

reviewer_note: 'The seller could argue R-410A-to-A2L obsolescence. The memo says the adjustment is consistent with prior years, and at most the 5,500 excess over the prior year would be arguable.'

## COA 8000/8050/8200 background activity [deals-senior-manager] -> CHANGE
The key has no non-operating removal. Add explicit constraints to §10:
- zero background activity in 8050 and 8200;
- 8000 carries only the M-09 insurance proceeds.

The generator asserts this, and the P&L omits zero-activity accounts consistently on both sides, so PL/GL coverage issues do not fire. Gain or loss on fleet sales moves to D3 as a planted case.

## COA 9000 Income Taxes – State [deals-senior-manager] -> NOTE
This is realism only; it does not affect any adjustment.

The reviewer's inference is only partly right. An LLC can elect C-corp status and pay Florida corporate income tax, and C-corp owners also take W-2 pay. However, a state-only income tax line with no federal line points to a pass-through.

For D1, keep 9000 at zero activity and state 'LLC taxed as an S corporation' in the company profile and README. Use a TAXES-class misclassification (non-income taxes booked as income tax) in a later deal.

## GT-SCHEMA forbidden_flags [buy-side-investor] -> NOTE
Do not add the schema field now. A false CONTINUING or RECURRING flag already shows up as a wrong treatment or amount (for example M-08 falling to 15,000, or M-14 becoming REJECT), and the evaluator already lists extra flags.

Record must-not flags in each reviewer_note instead:
- M-04: CONTINUING_OBLIGATION, RECURRING_PATTERN
- M-05: RECURRING_PATTERN
- M-08: CONTINUING_OBLIGATION
- M-14: RECURRING_PATTERN

Revisit the field once there are several deals. The materiality floor from this finding is adopted in the §5.3/§5.4 entry.

## GT-SCHEMA acceptable_treatments [buy-side-investor] -> REJECT
This is not needed, and it would weaken the metric. benchmark_protocol.md §4.2 already provides pre-registered alternatives through key_alternatives.csv, which I am using for M-09, M-12 and M-14. For the tool-only evaluation, §5.5 returns REQUEST_INFO for M-12 deterministically, so there is nothing to accept.

Related protocol fix: amend §4.2 to allow a pre-registered alternative at ambiguity medium or high. Its own M-14 example is medium.

## GENERAL key completeness [arithmetic-auditor] -> CHANGE
Totals re-verified:
- claims: 418,000 / 1,004,000 / 1,034,500
- truth finals: 16,000 / 335,700 / 244,200
- diligence less management: −402,000 / −643,300 / −765,300, including dil_recon of +25,000 in FY2025 and TTM
- pending: 360,000 / 360,000 / 525,000

After the duplicate change, FY2025 truth is 335,700 + X and the FY2025 gap is −643,300 + X.

Assign case_type to every item:
- M-01 RECURRING; M-02 NEEDS_INFO; M-03 CONTRADICTED
- M-04, M-05 and M-14 ADEQUATE
- M-06 CONTRADICTED; M-07 EBITDA_EXCLUDED; M-08 OVERLAP
- M-09 RECOVERY_OFFSET; M-10 OUT_OF_PERIOD; M-11 WRONG_PERIOD
- M-12 NEEDS_INFO; M-13 RECURRING

Every item also needs ambiguity, supporting_docs and question_topics filled in, as set out in the entries above.

CASE TYPES FOR NEXT DEALS:
 - [D2 dev + D3 holdout] Normalization positive control. D2: owner comp; D3: related-party rent on an owner-held facility. Each has an executed agreement or lease plus an independent benchmark (comp survey, broker opinion or appraisal). Expected: ACCEPT. D1 made every normalization and pro forma REQUEST_INFO, so a tool that always returns REQUEST_INFO scores perfectly today.
 - [D2] Normalization where the sign flips: related-party rent claimed as +X (above market), but the signed broker opinion puts market rent above the rent paid. Expected: REVISE to a negative amount. [D3] Management's own EBITDA-reducing adjustment: below-market rent normalized down by −Y, supported by an appraisal. Expected: ACCEPT the negative amount.
 - [D2] Realized pro forma: headcount cut executed Feb-2026 with signed separation agreements and payroll stopping; the claim is the eliminated payroll for Jul-2025 to Jan-2026. Expected: ACCEPT. Variant using contract salary instead of GL actual: REVISE to GL. [D3] Closed branch with a lease termination in Mar-2026 and stranded costs excluded. Expected: ACCEPT or REVISE.
 - [D2] PARTIAL_GL_SUPPORT: claim of 100,000 against 72,000 traced; management included an estimated accrual that was never booked. Expected: REVISE down to the traced amount.
 - [D2] NO_GL_SUPPORT: an add-back with no GL activity (cost paid by an owner affiliate, or a management estimate). Expected: REQUEST_INFO. [D3] Pro forma tuck-in acquisition EBITDA with a signed APA but no GL. Expected: REQUEST_INFO.
 - [D2] SIGN_ERROR: a one-time vendor settlement credit in Other Income presented as a positive add-back. Expected: REVISE to the negative amount.
 - [D2] One vendor contract that mixes a one-time implementation fee with a monthly subscription, all claimed as one-time. Expected: REVISE to the implementation fee only, with an entry-level split and CONTINUING_OBLIGATION on the subscription.
 - [D2] Out-of-period item straddling the FY2025/TTM overlap: service Apr–Sep 2025, booked Nov-2025, claimed in FY2025 and TTM. Expected: FY2025 0, TTM +X/2 pro rata. [D3] One-sided out-of-period: pre-data_start (FY2023) service booked in FY2024 and claimed in FY2024. Expected: ACCEPT with no negative side inside the data range (an over-adjustment trap).
 - [D2] Recovery variants: a recovery credited to the same expense account (contra) and received in Jan–Jun 2026, so the effect falls in TTM only. Expected: REVISE. [D3] A recovery still pending as a receivable at data_end. Expected: a question only, with the amount unchanged.
 - [D2] DUPLICATE_GL_ENTRY inside a claimed adjustment: management claims both postings of one invoice. Expected: the adjustment is REVISEd to one posting and the new dil_dq duplicate item carries the other; this tests that nothing is counted twice.
 - [D2] Partial ALREADY_EXCLUDED: a refinancing claim spanning a 6400 advisory fee and an 8100 fee write-off. Expected: REVISE to the 6400 portion. [D2 + D3] Contrast case: a prepayment penalty or loss on extinguishment booked in 8200 Other Expense, which is inside EBITDA. Expected: ACCEPT (the counterpart to M-07).
 - [D2] Upward revision: a same-engagement invoice cited in management's own support was left out of the claim. Expected: REVISE above the claim. This needs an engine rule for carrying unclaimed same-event entries; today EXCESS_GL_ACTIVITY is INFO only.
 - [D2] Supported top-side (cash to accrual): a Dec-2025 bonus accrual in management's P&L with a signed bonus calculation, paid through GL payroll in Mar-2026. Expected: keep the accrual, so FY2025 = GL − X and TTM = GL. dil_recon must then keep supported differences instead of always reversing to GL.
 - [D2] Transaction or change-in-control bonus under a signed plan, paid in TTM. Expected: ACCEPT (a non-cash or transaction compensation positive control).
 - [D3] Theme-level recurrence across counterparties: a 'one-time' lawsuit or consulting project every year, each from a different firm. Expected: REJECT, via RECURRING_PATTERN on account plus theme.
 - [D3] Documents limited to management representation: the GL fully ties, but the only support is a management email. Expected: REQUEST_INFO (a clean test of NO_DOCUMENT_SUPPORT).
 - [D3] Partial qualification inside one invoice and DOC_GL_AMOUNT_MISMATCH: a relocation invoice that includes continuing monthly storage lines. Expected: REVISE to the one-time lines. Separately, an invoice total that differs from the GL posting because of freight or tax. Expected: a question.
 - [D3] Non-operating items inside EBITDA: a loss on sale of fleet vehicles (8050) added back while gains in other periods are ignored. Expected: REVISE to the net figure.
 - [D3] Family member on payroll, added back as non-working with only a management representation. Expected: REQUEST_INFO.
 - [D3] Prior-period sales/use-tax assessment mixing prior-year tax (inside EBITDA; two-sided out-of-period), a penalty (inside EBITDA) and interest (8100, already excluded). Expected: REVISE.
 - [D3] Overlap settled by the schedule-order tie-break (equal link scores), plus one invoice split across two adjustments.
 - [D2 + D3] False-reject traps, at least two per deal, with ADEQUATE items at 40% or more of each schedule (D1 had 3 of 14). Examples: a one-time matter from a firm that also bills an unclaimed retainer; one large write-off among small routine entries in the same account; a one-time retainer creditable against a success fee; retained-search installments.
 - [D2 NetSuite] Data-quality plants: MISSING_PERIOD (one month exported with fewer than 50% of active accounts); MGMT_SCHEDULE_ARITHMETIC (the total-adjustments row does not foot); Department/Class dimension noise. [D3 Xero] UNMAPPED_ACCOUNT (a custom account type); PL_ACCOUNT_NOT_IN_GL and GL_ACCOUNT_NOT_IN_PL; a cut-off misposting across the FY2024/FY2025 year-end.
SUMMARY: **Arithmetic.** I read SPEC.md, qoe/schemas.py, the data-quality matching in qoe/evaluate.py and docs/benchmark_protocol.md, and recomputed every number:
- All 14 truth amounts reconcile.
- Totals: claims 418,000 / 1,004,000 / 1,034,500; truth finals 16,000 / 335,700 / 244,200.
- Diligence less management-adjusted EBITDA: −402,000 / −643,300 / −765,300, including dil_recon of +25,000 in FY2025 and TTM.
- Pending: 360,000 / 360,000 / 525,000.
- One reviewer figure is wrong: M-08 has 18 exact 62,000 subsets in FY2025, not 12. The finding still stands.

**Truth treatments and amounts.** None of the 14 changes. The answer key changes in two places:
1. **Duplicate insurance premium.** Carry it as a diligence item: 0 / +X / 0. FY2025 truth becomes gl + 335,700 + X, and X must be stated in §10. This needs a new GroundTruth field, a `dil_dq` bridge row, and an extended identity: GL EBITDA + management finals + diligence items.
2. **Top-side bonus accrual.** As planted, the key cannot be defended. I kept its amounts (dil_recon 0 / +25,000 / +25,000) and fixed the facts instead: a controller email says the pool was never approved or paid, and the GL has no bonus payments in any period. I rejected buy-side's asymmetric dil_recon.

**Spec fixes required** (several keys cannot be reached without them):
- NO_DOCUMENT_SUPPORT should be measured on the post-challenge supporting amount, not the claimed amount. Today it blocks M-07, M-11 and M-13, and M-03, M-09 and M-14 in combination with thin documents.
- Deterministic subset tie-break: most whole groups, then support-ref-cited entries, then earliest.
- Recurrence: the event window is the union of claimed months across periods; add a 25% materiality floor; exempt owner and normalization items.
- CONTINUING_OBLIGATION fires only on periodic or open-ended terms, not on one-time retainers.
- An OUT_OF_PERIOD entry is replaced by its effect, which stops M-10 double-counting to 84,000.
- §9 data-quality matching text should follow evaluate.py. MGMT_EBITDA_DIFFERS goes in with no locator; the proposed month='2025-12' would never match.

**Package fixes:**
- M-03: lease and club statement, plus per-trip expense reports.
- M-09: repair invoices and an itemized settlement letter showing where the $8,000 went.
- M-14: a $52,000 proof of claim.
- M-05: agreement states $25,000 installments.
- M-13: count memo states both amounts.
- M-08: support ref cites invoice 25-0910.
- M-01: Dawson nature and self-insured retention stated.
- Keel letter: a one-time retainer.
- Generator constraints: Brandon invoices not flagged as duplicates; no background in 8050 or 8200; the M-02 draft carries no perquisites; no other closeout true-ups.

**Protocol:**
- Pre-register alternatives in key_alternatives.csv:
  - M-09: 40,000 / −40,000 / 0.
  - M-12: REJECT 0 / 0 / 0.
  - M-14: 30-month bad-debt normalization, about −20,800 / +31,200 / +31,200.
- Replace the incoherent M-14 'excess over normal' example in benchmark_protocol.md §4.2 and SPEC §10.
- Allow alternatives at ambiguity medium.
- M-02 is deliberately not given an ACCEPT alternative, because accepting it is the false accept the item tests.
- Ambiguity goes to medium on M-02, M-09, M-12 and M-14.

**Next two deals.** The case types focus on what D1 cannot measure:
- supported normalizations and realized pro formas that should come out ACCEPT;
- sign errors, and upward or partial revisions;
- items straddling the FY/TTM boundary;
- flag codes and data-quality codes D1 never plants;
- more ADEQUATE items and false-reject traps.

Deferred revenue on maintenance agreements and other balance-sheet items stay out until the tool can carry diligence-identified revenue adjustments.

No files were edited.
