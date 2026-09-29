# QoE Evidence Review: build spec

This is the contract every module is built against. `qoe/schemas.py`, `qoe/money.py`, `qoe/periods.py`, and `qoe/ai_base.py` are the shared code contracts. Do not change them without updating this spec.

## 1. What the tool does

**User:** a transaction-advisory associate or manager reviewing management's adjusted EBITDA schedule during a quality-of-earnings (QoE) engagement.

**Job:** for each seller-proposed EBITDA adjustment, answer three questions:

1. Does the general ledger contain the amount?
2. Do the documents support management's explanation?
3. What amount should diligence carry, and what is still open?

The tool records the evidence behind each answer. The reviewer makes the final call.

```
IMPORT → RECONCILE → TRACE → CHALLENGE → PROPOSE → REVIEW → EXPORT
```

| Step | Owner | Output |
| --- | --- | --- |
| Import | code | `DealPackage` (GL, chart of accounts, monthly P&L, management schedule, documents) |
| Reconcile | code | `ReconciliationResult`: GL vs P&L by account-month, missing months, duplicates, EBITDA recomputed from the GL |
| Trace | code with AI proposals | `GLLink` / `DocLink` for each adjustment, per-period tie-out, recurrence scan |
| Challenge | code with AI proposals | `Flag`s: contradictions, overlaps, wrong periods, recoveries, recurring patterns |
| Propose | code | `AdjustmentAssessment`: treatment, amount for each period, documented facts kept separate from open judgment questions, and questions for management |
| Review | person | `ReviewDecision` (append-only log, with rationale and correction type) |
| Export | code | Excel workpaper: EBITDA bridge, support schedules, open questions, reconciliation, review log |

**Non-negotiables**

- **AI boundary.** AI proposes facts, links, contradictions, and question wording. Code computes every amount and every treatment. The reviewer decides.
- **Quotes are verbatim.** Every quote is checked as an exact substring of the cited page (`ai_base.verify_quote`). Anything that fails is dropped and counted, never repaired.
- **Money is `Decimal`.** In schemas it is a 2-dp string. Never use float.
- **Nothing is hard-coded per case.** No vendor names, adjustment ids, account numbers, or amounts from any deal package appear in engine or AI code. Reviewers will grep for this.
- **Ground truth stays out of the pipeline.** `ground_truth.json` is read only by `qoe/evaluate.py`. Ingest must ignore it.
- **Everything is synthetic.** Every generated file carries a visible "SYNTHETIC" label.

## 2. Package layout and ownership

```
qoe/
  __init__.py        TOOL_VERSION                       (shared, fixed)
  schemas.py         all models                         (shared, fixed)
  money.py           Decimal helpers                    (shared, fixed)
  periods.py         month / period helpers             (shared, fixed)
  ai_base.py         EvidenceAI protocol, verify_quote  (shared, fixed)
  gl_formats.py      GL + COA readers, format detection         [ingest]
  ingest.py          load_deal(), P&L + schedule + docs         [ingest]
  reconcile.py       reconcile()                                [ingest]
  ai.py              RuleBasedEvidenceAI, OpenAICompatibleEvidenceAI, get_ai()   [ai]
  trace.py           per-adjustment linking + tie-out           [engine]
  challenge.py       flag generation                            [engine]
  propose.py         treatment + amounts + facts/questions      [engine]
  bridge.py          build_bridge()                             [engine]
  engine.py          run_review() orchestration                 [engine]
  review_store.py    ReviewStore, apply_reviews(), final_amounts()   [ui]
  ui.py              Streamlit reviewer app                     [ui]
  export_xlsx.py     export_workpaper()                         [export]
  evaluate.py        load_ground_truth(), score()               [eval]
  commercial.py      capacity / margin model                    [eval]
scripts/
  qoe_generate_deals.py   deal spec YAML -> deal package          [generator]
  qoe_run.py              run review, write workpaper json + xlsx [eval]
  qoe_evaluate.py         score vs ground truth                   [eval]
  qoe_commercial_model.py write commercial model xlsx             [eval]
  qoe_corrections_to_evals.py  tool-error corrections -> regression cases [eval]
data/
  specs/<deal_id>.yaml    generator input                         [generator]
  dev/<deal_id>/          generated deal packages (committed)
  holdout/<deal_id>/
tests/                one test module per module above
```

## 3. Deal package format (the input contract)

```
<deal_dir>/
  deal.yaml
  gl/general_ledger.csv | gl/general_ledger.xlsx
  gl/chart_of_accounts.csv
  gl/account_mapping_overrides.csv        (optional)
  financials/monthly_pl.xlsx
  adjustments/management_adjusted_ebitda.xlsx
  documents/**/*.pdf|*.txt|*.md|*.eml
  ground_truth.json                       (eval only — pipeline never reads)
  README.txt                              (SYNTHETIC notice)
```

### 3.1 deal.yaml → `DealMeta`

```yaml
deal_id: meridian_mechanical
target_name: Meridian Mechanical Services, LLC
industry: Commercial and residential HVAC / plumbing services
synthetic: true
currency: USD
periods:
  - {label: "FY2024", start: "2024-01", end: "2024-12"}
  - {label: "FY2025", start: "2025-01", end: "2025-12"}
  - {label: "TTM Jun-26", start: "2025-07", end: "2026-06"}
data_start: "2024-01"
data_end: "2026-06"
gl_format: auto
files:
  gl: gl/general_ledger.csv
  chart_of_accounts: gl/chart_of_accounts.csv
  monthly_pl: financials/monthly_pl.xlsx
  adjustments: adjustments/management_adjusted_ebitda.xlsx
  documents_dir: documents
tolerance: "1.00"
```

Periods can overlap. For example, TTM Jun-26 shares Jul–Dec 2025 with FY2025. Every amount is computed per month first and then aggregated to each period label.

### 3.2 Sign convention

`GLEntry.amount` is **debit-positive**: expense, COGS, interest, tax, and D&A debits are positive, and revenue and other-income credits are negative. The P&L is normalized to the same convention on load.

Adjustment amounts are **EBITDA-signed**: `+` increases EBITDA (an add-back) and `−` reduces it.

### 3.3 GL export formats

`GLEntry.entry_id = f"GL-R{source_row}"`. `source_row` is the 1-based row number a spreadsheet app shows when it opens the file, counting title and header rows. For CSV this is the physical line number, because generators never put newlines inside a field. For xlsx it is the worksheet row. Ground truth refers to GL rows by this number.

**`qbo_gl_csv`**: QuickBooks Online "General Ledger" report, exported to CSV.

```
Meridian Mechanical Services, LLC                          <- row 1
General Ledger                                             <- row 2
"January 1, 2024 - June 30, 2026"                          <- row 3
                                                           <- row 4 blank
,Date,Transaction Type,Num,Name,Memo/Description,Split,Amount,Balance   <- row 5 header
4000 Service Revenue - Commercial,,,,,,,,                  <- account section header
,01/03/2024,Invoice,10231,Bayshore Medical Plaza,HVAC service - Jan,Accounts Receivable (A/R),"4,250.00","4,250.00"
...
Total for 4000 Service Revenue - Commercial,,,,,,,"$1,234,567.00",
6400 Legal & Professional Fees,,,,,,,,
,02/14/2025,Bill,25-0212,Hollis & Crane LLP,Matter 2291 ...,Accounts Payable (A/P),"14,500.00",...
...
TOTAL,,,,,,,,
```

- The account comes from the most recent section-header row, as `"<number> <name>"`.
- Dates are `MM/DD/YYYY`.
- `Amount` uses the **natural sign**: positive increases the account's normal balance, so income is shown credit-positive and expense debit-positive. Convert with the account's EBITDA class. For REVENUE and OTHER_INCOME, `debit_positive = -amount`. For every other class it is `+amount`. Accounts with class INTEREST or TAXES whose source type is an income type (for example "Interest Income" typed Other Income) also negate.
- Amounts may carry `$`, commas, and parentheses. `Balance` is ignored.
- Dimensions: none.

**`netsuite_csv`**: a NetSuite saved-search export. The header is on row 1.

```
Internal ID,Date,Period,Type,Document Number,Account,Name,Memo,Debit,Credit,Subsidiary,Department,Class,Location
```

- `Account` is `"<number> <name>"`.
- Dates are `M/D/YYYY`.
- `Debit` and `Credit` are unsigned, and only one of them is populated: `amount = debit - credit`.
- `Period` (for example `"Mar 2025"`) is informational only. Derive the month from `Date`.
- Dimensions: Subsidiary, Department, Class, Location.

**`xero_xlsx`**: a Xero "Account Transactions" export. The sheet name is "Account Transactions".

- Rows 1–3 are titles: `Account Transactions`, the company name, and `For the period 1 January 2024 to 30 June 2026`. Row 4 is blank.
- Row 5 is the header: `Date, Source, Description, Reference, Debit, Credit, Running Balance, Account Code, Account`.
- `Date` is either an Excel date or text like `15 Mar 2025`.
- `Debit` and `Credit` are unsigned numbers: `amount = debit - credit`.
- Map `Source` → `txn_type`, `Reference` → `doc_number`, `Description` → `memo`.
- The counterparty is embedded in `Description` as `"<Contact> - <text>"`. Split on the first `" - "`. If there is no separator, the counterparty is `""`.

**Detection (`gl_format: auto`).** Check signatures in the first 10 rows, in this order:

1. A header row containing `Transaction Type` and `Memo/Description` means **qbo**.
2. A header containing `Internal ID` and `Debit` means **netsuite**.
3. An xlsx with a sheet named `Account Transactions`, or a header containing `Account Code` and `Running Balance`, means **xero**.

Otherwise raise a `ValueError` that names the headers found.

### 3.4 Chart of accounts → `Account`

Header names vary. Match them case-insensitively:

| Field | Header candidates |
| --- | --- |
| number | `Account #`, `Number`, `Code`, `*Code`, `Account Number` |
| name | `Full name`, `Name`, `*Name`, `Account Name` |
| type | `Type`, `*Type`, `Account Type` |

Mapping to `EbitdaClass` happens in this order. The rule that fired goes into `mapping_basis`.

1. **Overrides file.** `account_mapping_overrides.csv` has the columns `account,ebitda_class,basis`.
2. **Name rules (P&L accounts only).**
   - `interest (expense|paid)|loan interest|interest income` → INTEREST.
   - `depreciation` → DEPRECIATION.
   - `amortization` → AMORTIZATION. This rule does not apply when the name contains `loan|debt|financing`; those go to INTEREST.
   - `income tax` → TAXES. This includes state and federal income tax. It does not apply to payroll, sales, property, or franchise tax.
3. **Type rules.**
   - Income, Revenue, Sales → REVENUE.
   - Other Income, OTHERINCOME → OTHER_INCOME.
   - Cost of Goods Sold, COGS, DIRECTCOSTS → COGS.
   - Expense, OVERHEADS → OPEX.
   - Other Expense → OTHER_EXPENSE.
   - DEPRECIATN → DEPRECIATION.
   - Anything else (Bank, AR, AP, Fixed Asset, Equity, CURRENT, …) → BALANCE_SHEET.
4. **Fallback.** An unknown P&L-looking account maps to OPEX and raises an `UNMAPPED_ACCOUNT` issue.

### 3.5 Monthly P&L (management) → `ManagementPL`

The file is an xlsx with an account-level "Profit and Loss by Month" on the first sheet.

- **Title rows** come first.
- **Header row.** The first row where two or more cells parse as months: `Jan 2024`, `January 2024`, `2024-01`, or an Excel date. A trailing `Total` column is ignored.
- **Section rows.** Text in column A with no amounts, such as `Income`, `Cost of Goods Sold`, `Expenses`, `Other Income`, `Other Expenses`. A section whose name contains "income" and does not contain "expense" is *credit-natural*. All others are *debit-natural*.
- **Account rows.** Column A matches `^\s*(\d{3,6})\s*[·\-–:]?\s*(.+?)\s*$`. Convert amounts to debit-positive: negate in credit-natural sections.
- **Rows to skip.** Total and subtotal rows: `Total …`, `Gross Profit`, `Net Operating Income`, `Net Other Income`, `Net Income`.
- **Blank cells** count as 0.

### 3.6 Management adjusted EBITDA schedule → `ManagementSchedule`

The file is an xlsx; use the first sheet. The **header row** is the first row with a cell equal to `Ref`, `#`, or `No.` and cells equal to every period label in deal.yaml, compared case-insensitively after trimming whitespace.

Other columns are found by header, case-insensitively:

| Field | Header candidates |
| --- | --- |
| title | `Adjustment`, `Item`, `Description of adjustment` |
| category | `Category`, `Type` |
| description | `Description`, `Basis`, `Management commentary`, `Rationale` |
| accounts | `GL Account(s)`, `GL Accounts`, `Account(s)`, `GL` |
| support | `Support Ref`, `Support`, `Data room ref`, `DR Ref` |

- **Adjustment rows** have a non-blank Ref. The Ref is kept verbatim as `adj_id`.
- **Label rows** have a blank Ref and a label in the title column. The label is matched case-insensitively:
  - `net income` → net_income.
  - `interest` → interest.
  - `tax` → taxes.
  - `depreciation` or `d&a` → depreciation_amortization.
  - `adjusted ebitda` → adjusted_ebitda. Check this before reported EBITDA.
  - `total … adjustments` → total_adjustments.
  - `ebitda` (reported) → reported_ebitda.
- **Categories** map by keyword:
  - `non-recurring` or `one-time` → NON_RECURRING.
  - `owner`, `discretionary`, or `personal` → OWNER_DISCRETIONARY.
  - `normaliz` → NORMALIZATION.
  - `out-of-period` or `prior period` → OUT_OF_PERIOD.
  - `pro forma` or `run-rate` → PRO_FORMA.
  - Anything else → OTHER.
- **GL accounts** are every 3–6 digit number in the accounts cell.
- **Support refs** are split on `;` or `,`.
- **Amounts.** Blank cells are 0. Negative numbers stay negative.

### 3.7 Documents → `SourceDocument`

- Walk `documents_dir` recursively in sorted order.
- `doc_id` is the file's basename, which must be unique within a deal.
- PDF pages come from `qoe.pdf_text.extract_pdf_pages` (pypdf, plain mode). Page text is canonicalized with `qoe.pdf_text.canonicalize_page_text`. QoE never imports from the AP agent's `app/` package.
- `.txt`, `.md`, and `.eml` files become a single page, also canonicalized.
- Quotes are verified against the canonicalized page text.

### 3.8 ground_truth.json → `GroundTruth`

See `qoe/schemas.py`. The rules:

- Amounts are the diligence amounts a careful senior would carry. REQUEST_INFO items have no amounts.
- `supporting_gl_rows` are the GL source rows that support the final amounts.
- `related_gl_rows` are rows a good review surfaces (comparables, recoveries, overlapped entries) that do not support the claim.
- `expected_flags` are the flags that **must** be raised.
- `diligence_adjusted_ebitda` is `gl_ebitda` plus every non-REQUEST_INFO final amount.

## 4. Module interfaces

```python
# qoe/gl_formats.py
def detect_format(path: Path) -> str
def read_chart_of_accounts(path: Path, overrides: Path | None = None) -> tuple[list[Account], list[str]]  # (accounts, notes)
def read_gl(path: Path, fmt: str, accounts: dict[str, Account]) -> tuple[list[GLEntry], list[str]]

# qoe/ingest.py
def load_deal(deal_dir: Path) -> DealPackage        # never opens ground_truth.json
def read_monthly_pl(path: Path) -> ManagementPL
def read_schedule(path: Path, period_labels: list[str]) -> ManagementSchedule
def read_documents(root: Path, deal_dir: Path) -> list[SourceDocument]

# qoe/reconcile.py
def reconcile(pkg: DealPackage) -> ReconciliationResult
def gl_ebitda(pkg: DealPackage) -> dict[str, EbitdaComponents]
def find_duplicate_entries(gl: list[GLEntry]) -> list[list[str]]   # groups of entry_ids

# qoe/ai.py
class RuleBasedEvidenceAI:  name = "rules"         # deterministic; default; used by tests
class OpenAICompatibleEvidenceAI: name = "llm:<model>"   # live; env QOE_LLM_BASE_URL / QOE_LLM_API_KEY / QOE_LLM_MODEL
def get_ai(mode: str = "rules") -> EvidenceAI

# qoe/engine.py
def run_review(deal_dir: Path, ai: EvidenceAI | None = None, run_id: str | None = None, created_at: str | None = None) -> Workpaper
def save_workpaper(wp: Workpaper, out_dir: Path) -> Path           # <out_dir>/<deal_id>/workpaper.json
def load_workpaper(path: Path) -> Workpaper

# qoe/bridge.py
def build_bridge(pkg_or_meta, recon: ReconciliationResult, schedule: ManagementSchedule,
                 assessments: list[AdjustmentAssessment], final_amounts: dict[str, dict[str, str]] | None = None) -> EbitdaBridge

# qoe/review_store.py
class ReviewStore:   # append-only JSONL at <workpaper_dir>/review_log.jsonl
    def __init__(self, path: Path)
    def append(self, decision: ReviewDecision) -> None
    def all(self) -> list[ReviewDecision]
    def latest(self) -> dict[str, ReviewDecision]
def final_amounts(wp: Workpaper, reviews: dict[str, ReviewDecision]) -> dict[str, dict[str, str]]  # adj_id -> period -> amount ({} = pending/excluded)
def apply_reviews(wp: Workpaper, reviews: list[ReviewDecision]) -> Workpaper  # sets wp.reviews and rebuilds wp.bridge

# qoe/export_xlsx.py
def export_workpaper(wp: Workpaper, out_path: Path) -> Path

# qoe/evaluate.py
def load_ground_truth(deal_dir: Path) -> GroundTruth
def score(wp: Workpaper, gt: GroundTruth) -> dict      # see §9
```

`run_id` and `created_at` are injectable, so runs are reproducible. Given the same inputs and the same values, `workpaper.json` is byte-identical: sort keys, and keep list order stable.

## 5. Engine algorithm

**Terms**

- An entry is **linked** if it relates to the adjustment.
- An entry is **claimed** if management's amount appears to include it.
- An entry is **supporting** if it is claimed and survives every challenge, or if it is **carried** under the EXCESS_GL_ACTIVITY carry rule (§5.4) without being claimed.

`traced_gl[p]` is the sum of claimed entries in period *p*. `proposed[p]` is the sum of supporting entries plus the amount effects of challenges (recoveries and period moves).

`documented[p]` ((c) Documented) is the sum of claimed entries in *p* that one of the documents about the entry (`GLLink.doc_ids`) **vouches to its own document** (tick D), by the per-entry rule the Excel audit trail uses (`trace.vouch_tick`): the document states the entry's document number; or it states the entry's amount and the memo cites one of its references (5+ characters with a digit); or, for a document that is not an agreement or company correspondence, it states the amount for the same party (or either side has no party) and is dated, or covers a service period, near the entry's month (service period −1 to +2 months, or doc date within 2 months). An agreement vouches at A, a draft or unsigned one at U, a document for the same charge under another number or in another month at S, company correspondence and memos at C. "Another number" means a number from the same numbering scheme as the entry's (the same alpha prefix, or the same pattern of letters and digits: INV-88214 against INV-88213), or a number another GL entry carries; an ERP's internal transaction number (BILL00421, VENDBILL-1532) says nothing about the vendor's invoice number, so the amount, party and date test decides. Legal-form words (LLC, Inc, Ltd, Limited, Pty, PLLC, GmbH, BV, dba ...) do not identify a party. *Principle:* a practitioner ticks an entry as vouched only against the document that evidences that very charge; an engagement letter supports the item but does not vouch the entry.

`GLLink.claimed_in` lists the period labels whose claim includes the entry (FY and TTM can differ); it is empty for an entry that is not claimed, including a carried one.

### 5.1 Facts and intent

- Run `ai.extract_facts(doc)` on every document, then verify every quote. The rule-based reader never takes a line of an address block (a city on its own line above "ST ZIP", a "City, ST ZIP" line, the line after a street address) as the document's counterparty; a letterhead line written "Name | 200 Mill Road" gives the name before the separator.
- Run `ai.parse_intent(adj)` on every adjustment.
- Document types include `benchmark`: an independent view of market (a real-estate, property or market appraisal, a broker's opinion of market rent or value, a pay or market study, a compensation survey, a fair-market-value (FMV) opinion, a rate study, an MGMA survey). The rules reader keys the type on market semantics: an HR "Performance Appraisal" or performance review is not a benchmark. It is what the normalization benchmark rule (§5.4) looks for; a signed document of another type can also serve when its sentence speaks of market.

### 5.2 Candidate linking (`trace.py`)

Every P&L entry (class ≠ BALANCE_SHEET) is scored against the adjustment. The score is additive and each signal is recorded in `GLLink.reasons`. Signals:

- **Account.** The account is in `adj.gl_accounts`.
- **Counterparty.** Fuzzy match (normalized token overlap, legal forms dropped) against `intent.counterparties`, or against the counterparties of documents cited by the support refs or linked by reference. When either name has a single distinctive (non-generic) word, one shared word is a coincidence as often as not ("Springfield" the city and "Springfield Grand Hotels"): the distinctive words must be the same, except that the other name's extra words may be the ones the single-word name abbreviates to initials ("J. Varga" and "Jamal B. Varga").
- **Keywords.** `intent.keywords` appear in the memo. A keyword that only restates the entry's account name (every word of it is a word of the account name, its plural or singular, or has the same stem: "repairs" in *Repairs & Maintenance*, "write-off" in *Inventory Adjustments & Write-offs*; but not "rent" in *Rental Income* or "pro" in *Professional Fees*) is **not** an independent signal. *Principle:* every entry in that account is described by those words, so they say nothing about which entries belong to the claimed event; a routine repair in a repairs account is upkeep, not the casualty loss being added back. Such an entry is linked as **context only** (surfaced, never claimed) when another entry **in the same account and period** links on independent evidence (party, reference, document or a distinctive word). When nothing links more specifically in that account and period (a dedicated severance or bad-debt account, even beside another account where the claim names a party), the account-name match is all the evidence there is and the entry stays a candidate with the keyword weight. When the claimed entries fall short of the claim, no related document explains the gap, and context-only entries of this kind in the period tie to the gap (an exact subset within the tolerance), a judgment asks whether they are part of the claimed event; they are not added silently.
- **Reference.** `doc_number` or the memo contains a reference number from `intent.reference_numbers`, or from a document's `reference_numbers`.
- **Document.** A document's facts contain the entry's `doc_number`, or they show the same amount (±tolerance) together with a matching counterparty. When the document's own counterparty is another party, a related document still names the entry's party if the party's name appears **as a phrase, in order** in its body (the whole name, or its distinctive words together, "the Brookline payoff"), outside its address and contact lines, and not only through words that are places in those address lines: scattered words (a town that shares a word with the party, a word of a broker's tagline) never make a name. A document management cites that states the entry's exact amount and whose title names the same street address as a document already tied to the entry by amount (a broker's opinion of market rent for the leased premises, beside the lease) is tied to the entry too. A document of the group's party that states the total of two or more of a group's entries supports each of them; one entry's amount is that entry's own bill, never a "group total" for its siblings.

Entries above the link threshold are linked. Each link records whether the Counterparty signal fired (`LinkInfo.party`); the normalization scope (§5.4) uses it.

- Linked entries in periods with a nonzero claim are candidates for **claimed**.
- Linked entries elsewhere are kept for the recurrence and period-mismatch analysis (`supports_claim=False`).

**Grouping.** Linked entries are grouped by normalized counterparty plus a memo theme, which is the memo with dates, amounts, invoice numbers, and month names stripped. If a document reference is present (a matter number, a contract), it wins over the memo theme. For example, litigation invoices under one matter number group separately from retainer invoices from the same law firm.

### 5.3 Claimed-set fit

For each period *p* with a nonzero claim:

- **Linked total too high.** If the linked total in *p* exceeds the claim by more than the tolerance, search for an exact subset (to the cent) of linked entries that sums to the claim.
  - **Tie-break (deterministic).** Among exact fits, prefer the most whole groups, then entries cited by the support refs (a document named in a support ref that links to the entry), then the earliest entries. If fits are still tied, record the ambiguity in the rationale.
  - The search is bounded to at most 30 entries, using meet-in-the-middle or a cents DP with a cap.
  - If a subset is found, it is the claimed set. The rest are linked with `supports_claim=False`, and `EXCESS_GL_ACTIVITY` (INFO) is raised.
  - If no subset is found, treat all strongly linked entries as claimed and note the gap.
- **Linked total too low.** If it is below the claim by more than the tolerance, raise `PARTIAL_GL_SUPPORT` (WARNING) with `amount_impact = linked − claimed`. A document related to the adjustment that states the missing amount (for example management's own build-up of the claim, showing it includes an estimate that was never invoiced or booked) is cited on the flag (doc_ids and quote) in neutral words ("<doc> states the same <gap>"). The open question says the document puts the gap down to an amount not booked only when a sentence of the document that states the amount also says so (estimate, not invoiced / booked / billed / recorded, accrual, anticipated, to be invoiced); a coincidental match (a retainer equal to the gap) is only cited. *Principle:* diligence carries only what the GL shows; an unbooked estimate is not a cost the business incurred, and the reviewer should see where the gap comes from.
- A fit that ties within the tolerance but not to the cent says so in the EXCESS_GL_ACTIVITY message ("within the 1.00 tolerance"); "to the cent" is reserved for exact fits. The linked activity that "exceeds" the claim counts only entries running the same way as the claim; linked entries running against it (credits beside an expense claim, revenue beside a cost) are context too, reported apart and never netted into the excess.
- **Nothing linked.** If no entries link in any period, raise `NO_GL_SUPPORT` (CRITICAL), except for a normalization of an arrangement that costs nothing (§5.4 *Normalization items*), where no GL cost is the premise.

### 5.4 Challenges (`challenge.py`)

Each flag has a trigger, an effect on `proposed`, and a severity.

| Flag | Trigger | Effect on proposed |
| --- | --- | --- |
| `ALREADY_EXCLUDED_FROM_EBITDA` | Claimed entries sit in INTEREST, TAXES, DEPRECIATION, or AMORTIZATION accounts. EBITDA already adds them back. | Remove those entries, and only those: the rest of the claim (a placement fee in operating expenses) is tested on its own. CRITICAL. A document tied specifically to a removed entry (a debt-cost amortization schedule) cannot be extended to the rest of the claim by any later challenge (see CONTRADICTORY_EVIDENCE). |
| `OVERLAP_WITH_OTHER_ADJUSTMENT` | An entry is claimed by more than one adjustment. The adjustment with the highest link score keeps it; ties go to schedule order. The others get this flag, naming the related adj id. | Remove from the others. CRITICAL. |
| `CONTRADICTORY_EVIDENCE` | `ai.find_contradictions` returns a verified conflict, such as a document calling a "one-time" cost a monthly subscription. Also raised by a normalization benchmark that sets a level other than management's (see *Normalization items*). | Remove the entries the contradiction covers. If it is not entry-specific, remove every group whose documents contain it; when one kind of activity is claimed, it covers all of it. WARNING. Scope limits, each a practitioner rule: (1) **another engagement** — a document whose own title names a typed reference (Matter 12, Contract 40, Project 7, PO 4471, Claim ...) is about that engagement and does not reach entries whose group cites a different reference **of the same kind** that the document never names. Like is compared with like: a date, a fiscal year, a street number or a form number in a title ("Lease Agreement - 12 Dock Street", "Official Form 410", "FY2026 ... Plan", "MSA dated 2024-03-01") names no engagement, and a group whose reference has no kind (a shared token) is never "another engagement"; the conflict is dropped and recorded as a fact ("a separate engagement with the same party"), because a firm's letter for one matter says nothing about its bills for another; (2) **a document about entries out of play** — a document about claimed entries already removed on structural grounds (below EBITDA, claimed elsewhere, a repeated posting) and about no claimed entry still in play is dropped, not extended to the rest of the claim; a document about both still speaks to the entries in play; (3) **one-time component** — for a non-recurring claim, entries billed at an amount that a related document of the same party (or tied to the entry) itself calls one-time are spared. The amount must be bound to the cue ("one-time", "non-recurring", "lump sum", "single payment") in a verified quote: the figure sits in the cue's clause a few words away ("one-time implementation fee: $64,000", "a $10,000 one-time setup fee"), or it splits such a fee into 2–12 equal parts beside an installment word ("two milestones of $32,000 each"). A figure written as periodic ("$2,500 per month", "monthly fee $2,000"), labelled monthly fee, retainer, recurring fee or rate, or stated elsewhere in the same document as periodic is never one-time. How a fee is credited ("creditable against hourly fees") is not a cue; for CONTINUING_OBLIGATION a retainer is tied to one transaction only when it is creditable against that transaction's own fee (success, closing, completion or placement fee): a contract that prices a one-time implementation fee separately from a subscription is evidence against adding back the subscription, not the fee it sets apart. The rule-based reader (§5.1) also ignores a recurrence statement whose recurring activity is the subject of a negated inclusion whose object is the claimed item ("routine maintenance visits are not part of this remediation project", "... are excluded from the write-off"): the object must be a generic item noun (write-off, write-down, adjustment, claim, project, matter, loss, charge, program, remediation, restructuring, reserve, settlement, event) or a word of management's keywords or title. That supports the claim that the item is unusual. Qualifiers such as "other than", "excluding", "apart from" or "separate from" never set a recurrence apart: they qualify a term ("renews for successive terms other than as provided in Section 9"). |
| `CONTINUING_OBLIGATION` | A linked document has a term fact that carries the obligation into the go-forward cost base: a periodic fee (monthly or quarterly), "until terminated", auto-renewal, ongoing services, or a service term_end after the last claimed month. The fact must apply to the claimed entries. A one-time retainer tied to a single transaction or search does **not** qualify. | Remove the entries whose amount equals the recurring fee, or whose group is covered by the term. WARNING. The one-time component of a mixed contract (see CONTRADICTORY_EVIDENCE (3)) is never in scope, and a document about another engagement of the same party (CONTRADICTORY_EVIDENCE (1)) does not cover a group by party name. |
| `RECURRING_PATTERN` | A claimed group has comparable activity (same counterparty and theme, or same account and theme) in another fiscal period that the claim does not cover, at ≥ 50% of the claimed group's amount; or it has ≥ 3 similar months outside the event window. The event window is the union of the months of the group's claimed entries across all period labels. A month counts toward the ≥ 3 test only if its similar activity is at least 25% of the group's average claimed monthly amount. This flag does **not** apply to OWNER_DISCRETIONARY or NORMALIZATION items, where recurrence is the premise. Unclaimed bills of the same fixed-fee engagement are not comparables: when an executed engagement letter or order form of the same party states one fee equal to the party's claimed entries plus those unclaimed bills, they are the same project billed in phases, not evidence that it recurs. Record a `RecurrenceObservation` with amounts by period label. | Remove that group. WARNING. |
| `OUT_OF_PERIOD` | A document linked to a claimed entry has a service period in different months from the booking month, and at least one period label contains the booking month but not every service month, or contains service months but not the booking month. The test runs on **every** period label, not on the set of labels: overlapping periods cut a service period differently, so a bill whose service sits wholly inside its fiscal year of booking can still belong partly outside a TTM that starts mid-service (service Apr–Sep booked Nov: the fiscal year nets to 0, a TTM from July keeps the Apr–Jun half). **Ordinary billing in arrears is exempt:** one cycle of a recurring billing series, billed after it ends, recurs every cycle, so each period carries a full year of it. The test is the billing cadence, not the lag alone. All of: (1) the service period is at most three months (a month or a quarter); (2) the bill is booked after the service ends and within one cycle of it (lag ≤ the number of service months); (3) the document does not describe itself as a correction or catch-up (true-up, catch-up, retroactive, back-billing, under-/over-billing, a one-time reconciliation/adjustment/correction, a billing or invoice reconciliation or correction, a bill adjustment, a prior-period charge; a routine line such as a fuel-surcharge or rate adjustment is not); (4) the bill belongs to a series of the same party: another bill of that party (of the same matter or contract when the entry's group has a reference) whose service period abuts this one, or the party's previous booking in the same account (same sign, same memo reference when there is one) at least as many months earlier as the bill covers, so the bill covers only the time since the last one. *Principle:* only a catch-up (a true-up, a correction, a late or multi-cycle bill) distorts a period; ordinary cadence does not. The exemption does not apply when management itself presents the item as out-of-period (category OUT_OF_PERIOD): the premise is then accepted and the move is measured. | The entry leaves the supporting set and is **replaced entirely** by its effect. For each period label: + the amount if the booking month is in it, − the amount pro rata by the service-period months it contains. Service months before `data_start` are outside the analysis, so no negative side is carried for them. WARNING. |
| `PERIOD_MISMATCH` | The claim in *p* is nonzero but no claimed entry falls in *p*, while linked entries exist in other periods. The same applies when the claim in *p* exceeds traced activity in *p* and the excess matches activity in another period. | `proposed[p]` = the supporting total in *p*. WARNING. |
| `EXCESS_GL_ACTIVITY` | In a period label with a non-zero claim, linked entries outside the claimed set share the claimed entries' counterparty and document series. | INFO by default. Carry the unclaimed entry into the supporting set, raising proposed above the claim, only when all of these hold: (1) the item is not PRO_FORMA or NORMALIZATION; (2) a linked engagement letter or order form fixes one fee for one project covering both the claimed and unclaimed entries — mechanically: an executed (not draft, not unsigned) agreement-type document of the same party states one amount equal, within the tolerance, to the party's claimed entries (all periods) plus its unclaimed linked bills whose own documents management cites; (3) the unclaimed entry's own document (the one stating its document number) is cited in the item's support refs; (4) the entry falls in a period label where the claim is non-zero and the claim there includes part of the same party's engagement; (5) the claim is not capped (§5.3 strong-link case), and none of the party's claimed entries was removed by a challenge (checked after every removing challenge). *Principle:* management's claim is normally the ceiling and a buyer-side review does not volunteer add-backs, but leaving part of one fixed-fee, non-recurring project in EBITDA while adding back the rest is inconsistent. WARNING when carried: one flag per period label, whose effect is + the carried amount; the carried entry is `supports_claim=True`, `role="supporting"`, `claimed=False`, `claimed_in=[]`, and its bill and the letter are tied to it. The INFO flag and the claimed-set tie judgment for that period are withdrawn when every linked entry of the period is claimed or carried. A judgment asks whether to add the bill back or hold management's claim. |
| `OFFSETTING_RECOVERY` | A credit entry in OTHER_INCOME or REVENUE (or a credit in the same account, e.g. insurance proceeds credited to the repairs account) relates to the same event (counterparty, keyword, or reference, such as a claim number found in a linked document), and management did not adjust it. | − the recovery amount in the periods containing the recovery month. WARNING. |
| `UNSIGNED_OR_DRAFT_SUPPORT` | A linked agreement is `is_draft` or `is_signed is False`. | None by itself; it drives REQUEST_INFO for normalization and pro forma items. WARNING. |
| `NORMALIZATION_BENCHMARK_MISSING` | A normalization item has no signed agreement or benchmark document that supports the normalized level. | None; it drives REQUEST_INFO. WARNING. |
| `PRO_FORMA_NOT_REALIZED` | `intent.is_pro_forma` is set, and the GL shows the cost continuing through `data_end` or no evidence that the event occurred. | None; it drives REQUEST_INFO. CRITICAL. |
| `NO_DOCUMENT_SUPPORT` | Measured per period on the **supporting** amount, meaning what diligence would carry after every challenge removal and period move. More than 25% of that amount has no linked document. A period whose supporting total is 0 cannot trigger it; documents are needed for what we carry, not for what we reject. It can also be raised as INFO on the claimed set, to prompt questions. The company's own emails and memos do not count. **Journal entries:** an entry with no counterparty (a write-off, a reserve) has no outside bill; when a company-authored calculation states its amount (a memorandum, a schedule, an analysis, board minutes: any document that is not an agreement, a bill, correspondence, a payroll register, an insurance document or a benchmark, and that is an internal memorandum, has no outside party, has the company as its party, or is on the company's letterhead), the outside documents management cites for the claim (a supplier's discontinuation notice, a disposal certificate — any cited, non-correspondence document whose party is not the company) are the evidence of the event it records, and are tied to the entry as support. An outside document already tied by number or amount to another claimed entry is that entry's bill and is not tied to the journal entry. *Principle:* the source document of a book entry is the company's own calculation, corroborated by third-party evidence of the event. | Drives REQUEST_INFO when above 25% of the supporting amount. WARNING. |
| `DOC_GL_AMOUNT_MISMATCH` | A document linked to an entry states a total that differs from the entry by more than the tolerance. | None; it creates a question. WARNING. |
| `SIGN_ERROR` | The claim's sign conflicts with the claimed entries, for example an add-back made of credits. | None beyond the entries themselves: proposed follows the debit-positive supporting entries, so an add-back made of credits comes out negative. It creates a question. WARNING. |
| `DUPLICATE_GL_ENTRY` | A claimed entry is part of a duplicate group from reconciliation. | When the group shares one non-empty document number, sits inside EBITDA, its postings are separate (different posting dates, or different transaction ids when the export carries them; postings that share a date or a transaction id are lines of one bill), the bill's own document shows one charge (a total equal to one posting and none equal to a multiple of it, or, without a total, the amount stated once; without a document the dates decide), and the claim includes more than one of its postings, the claim keeps the first posting (date order) and the others are removed (structural, like an overlap: evidence challenges skip them); the diligence item of §5.7 reverses them once. Otherwise none; it creates a question. WARNING. |

**Structural removals.** ALREADY_EXCLUDED_FROM_EBITDA, OVERLAP_WITH_OTHER_ADJUSTMENT and the DUPLICATE_GL_ENTRY removal decide *whose* entry it is, not whether the claim is right; the evidence challenges (contradictions, entry qualification, continuing obligation, recurrence) look only at the claimed entries still in play.

**Entry qualification.** `ai.classify_entries` covers claims where only some of the activity fits management's basis, such as personal versus business travel or litigation versus general matters. Entries marked `qualifies=False` with a verified basis are removed. The removal is recorded with a `CONTRADICTORY_EVIDENCE` flag, or a `RECURRING_PATTERN` flag when recurrence is the reason.

**Normalization items** (`intent.is_normalization`):

- **Claimed** is the actual cost in the linked accounts minus the normalized level. `intent.normalized_amount` is annual; a level the narrative states per month or per quarter is restated as a year (read, not estimated).
- **Scope of the actual cost.** When the arrangement's party is known (some linked entries in the named accounts are with a party the claim names — the Counterparty signal: the owner, the related-party landlord — or the narrative names one), a linked entry whose own counterparty is a different party (another landlord, the county's tax bill, another employee) is another arrangement and stays context. Linked entries with no counterparty (a payroll journal, an accrual) stay in the actual cost: many ledgers post salary with no contact, and they linked on the arrangement's own words. *Principle:* a normalization restates one arrangement at market; other leases, property taxes or salaries in the same account are not the arrangement. When no party is known, every linked entry in the accounts counts.
- **An arrangement that costs nothing.** When management's narrative states the annual level, the claim in a period is minus that level pro rata, and the GL traces no cost (rent-free premises, an unpaid owner), the level is the whole normalization: no NO_GL_SUPPORT or PARTIAL_GL_SUPPORT is raised for the missing cost, and a fact records it.
- **Supported** requires the actual cost in the GL (none, for an arrangement that costs nothing), plus a signed document that sets the normalized level (an executed document stating management's level).
- **Benchmark level.** When no executed document states management's level, an independent market benchmark for the arrangement sets it: an executed document (signed, or of type `benchmark`) related to the adjustment (cited, or tied by party or reference), whose own party is not a party to the arrangement, that states **exactly one** market level. Candidate levels are the document's amounts annualized (labelled monthly, or written "per month" / "per quarter" after the figure), excluding the actual annual cost it quotes for reference. What a figure measures is read from the words around it, never from its size: a per-unit rate ("$9.00 per square foot", "$185 an hour", psf, per unit / visit / seat ...) and a company-wide figure ("revenue of about $40 million", a range of company sizes, EBITDA, enterprise value) are not levels. A rate per square foot times the one area the document states ("14,000 square feet"), both verbatim, is a candidate level too. A document that is not of type `benchmark` sets a level only from a sentence that speaks of market (market, benchmark, comparable, median, percentile, fair market value, FMV, peer group): another executive's employment or separation agreement stating a salary is not a view of market. A monthly and a yearly statement of the same level count once. A benchmark applies whatever the actual cost, including an owner paid many times market or an arrangement that costs nothing. Several distinct levels set none (a judgment lists them). *Principle:* market is evidenced by an independent view of market for that arrangement, not by the level management chose; when market is **above** what is paid, the normalization reduces EBITDA (proposed negative). The benchmark raises CONTRADICTORY_EVIDENCE (WARNING), whose `Flag.effects` carry the level change, (management's level − benchmark level) × months ÷ 12 per claimed period; any remaining difference in the actual cost is carried by the period's PARTIAL_GL_SUPPORT flag. A judgment asks whether to normalize to the benchmark or leave the arrangement unadjusted if its terms continue after closing.
- If either the actual cost or a supported level is missing, the item goes to REQUEST_INFO (NORMALIZATION_BENCHMARK_MISSING or UNSIGNED_OR_DRAFT_SUPPORT).
- The rule-based reader does not report a document's base salary as contradicting management's level when the same document also states that level (total target cash = base + bonus).

### 5.5 Treatment (`propose.py`)

This step is deterministic and runs in order:

1. If `PRO_FORMA_NOT_REALIZED` is raised → **REQUEST_INFO**.
2. If this is a normalization item with `UNSIGNED_OR_DRAFT_SUPPORT` or `NORMALIZATION_BENCHMARK_MISSING` → **REQUEST_INFO**.
3. If `NO_GL_SUPPORT` is raised and there is no contradiction → **REQUEST_INFO**.
4. If `NO_DOCUMENT_SUPPORT` (WARNING, measured on the supporting amount) is raised → **REQUEST_INFO**.
5. Compute `proposed[p]` for every period label, including periods management left at zero. Examples: the −42,000 out-of-period move into FY2024, and the −40,000 recovery.
6. If every `|proposed[p] − claimed[p]|` is within the tolerance → **ACCEPT**.
7. If every `proposed[p]` is 0 → **REJECT**.
8. Otherwise → **REVISE**.

For REQUEST_INFO, `proposed = {}`, and the rationale states the provisional amount the evidence would support.

**Flag effects (the walk from claimed to proposed).** `Flag.effects` records, per period label, the signed change each flag drives, so that claimed + Σ effects = proposed. In order: the GL gap (traced − claimed) on the period's PERIOD_MISMATCH, SIGN_ERROR or PARTIAL_GL_SUPPORT flag (else NO_GL_SUPPORT); removals, each on the flag that removed the entry first; entries carried under the EXCESS_GL_ACTIVITY rule, on that period's WARNING flag; out-of-period moves; recoveries. For a normalization item: removals, then the level change on the flag that set a level other than management's (the benchmark's CONTRADICTORY_EVIDENCE), then any gap in the actual cost on PARTIAL_GL_SUPPORT. An INFO EXCESS_GL_ACTIVITY flag has no effect.

**Rationale wording on documents.** "vouched to their own documents" means (c) Documented equals traced; "with supporting documents" means every entry has a supporting document (§5.4 NO_DOCUMENT_SUPPORT) but not all are vouched, and the vouched amount is stated.

**Confidence**

- **high:** no WARNING or CRITICAL flags other than the flags that set the amount.
- **medium:** a recurrence or contradiction drove the result.
- **low:** an AI-only classification drove more than 50% of the amount change.

**Facts vs. judgment.** `facts` are statements the evidence establishes, each with entry ids and/or quotes. `judgment_questions` are the calls a person has to make, such as "is the retainer part of the ongoing cost base?". `open_questions` are requests to management and come from `ai.draft_questions` plus templated questions for each flag. Question ids are `Q-<adj_id>-<n>`.

### 5.6 Bridge (`bridge.py`)

Rows (`key`) for each period label:

| key | label | kind |
| --- | --- | --- |
| `net_income` | Net income (per GL) | component |
| `interest` | Interest expense, net | component |
| `taxes` | Income taxes | component |
| `depreciation` | Depreciation | component |
| `amortization` | Amortization | component |
| `gl_ebitda` | Reported EBITDA (per GL) | subtotal |
| `mgmt_recon_diff` | Difference to management's reported EBITDA | memo |
| `mgmt_reported_ebitda` | Reported EBITDA (per management) | subtotal |
| `mgmt:<adj_id>` | <title> (as claimed) | mgmt_adjustment |
| `mgmt_total` | Total management adjustments | subtotal |
| `mgmt_adjusted_ebitda` | Management adjusted EBITDA | subtotal |
| `dil_recon` | Reverse unsupported reporting difference (to GL) | diligence_adjustment |
| `dil:<adj_id>` | <title>: diligence revision (final − claimed; −claimed if pending) | diligence_adjustment |
| `dil:<item_id>` | Diligence-identified item (e.g. reverse a duplicate posting): the final amount | diligence_adjustment |
| `dil_total` | Total diligence adjustments | subtotal |
| `diligence_adjusted_ebitda` | Diligence adjusted EBITDA | subtotal |
| `pending` | Memo: management adjustments pending information (excluded) | memo |

**Identity:** `diligence_adjusted_ebitda = gl_ebitda + Σ final amounts of management items (excluding pending) + Σ final amounts of diligence-identified items`. Tests assert it.

### 5.7 Diligence-identified items

The tool also proposes adjustments that are not on management's schedule, where the evidence makes the amount mechanical.

- **Scope in v1: duplicate postings only.** Each `DUPLICATE_GL_ENTRY` group matched on a non-empty `doc_number` becomes one item when it is a repeated bill by the test of §5.4 DUPLICATE_GL_ENTRY (separate postings, a one-charge document). Groups matched on memo within 7 days, and same-number postings of one date (two identical lines of one bill), stay questions only.
- **Representation.** The item is an `AdjustmentAssessment` with `source="diligence"`.
  - `adj_id` is `D-<n>`, numbered in order of the group's first GL row.
  - `claimed` is all zeros; `category` is OTHER; `treatment` is REVISE.
  - `proposed` = + every posting except the first, in the periods of those postings, because each extra posting overstates expense.
  - `gl_links` list every posting in the group. The first posting is marked `supports_claim=False`.
- **Nothing counted twice.** When a management item claims more than one posting of a duplicate group:
  - the management item keeps only the first posting;
  - `DUPLICATE_GL_ENTRY` on the management item removes the extra postings;
  - the D item carries those extras.

  A duplicate is a bookkeeping error, not a non-recurring cost, so it belongs in its own line.
- **Other supported reporting differences.** A management P&L top-side that the evidence supports is modeled as a diligence item, for example a signed bonus calculation later paid through the GL. The item carries − the accrual in the period it belongs to, and it offsets the `dil_recon` reversal. The identity still holds: GL EBITDA + management finals + diligence items. `dil_recon` still reverses the whole reporting difference; each supported part is re-added as its own visible line. These items are numbered after the duplicate-posting items (next free `D-<n>`), accrual items first (by account, then month), then export gaps (by month).
  - **Supported top-side accrual (cash to accrual).** *Principle:* a diligence P&L is on an accrual basis; when management accrues a cost in the period it was earned (a year-end bonus pool) and the ledger books it only when paid, the accrual is kept, not reversed. Mechanically, all of: (1) reconciliation shows, in one cost account (COGS, OPEX or other expense), a positive P&L − GL variance (debit-positive: the P&L carries more cost) in one month and an equal and opposite variance (within the tolerance) in a **later** month of the data range, neither month flagged MISSING_PERIOD — the top-side reverses when the ledger catches up, so the cost is counted once. The reverse direction (the GL books the cost first and the P&L moves it to a later month) is a deferral that raises the earlier period's EBITDA: it is not this rule and stays reversed by `dil_recon`, as does any revenue or income top-side; (2) the GL holds, in that account and in the later month, an entry of the same amount (the payment); (3) an executed or approved document that is not company correspondence states the amount (an approved calculation, a plan). Executed means signed; approved means the page stating the amount records an approval that was given ("approved", "ratified", a board resolution or consent) and says who gave it or when (a named approver or approving body, a signature, a date). A page that says the amount is not approved, unapproved, pending or subject to approval, or to be approved, supports nothing even if signed, and a blank "Approved by: ____" records no approval. Never a draft; (4) the document is about that accrual: it is dated no later than the accrual month (the obligation existed by then), or it names a fiscal period label or a date range that holds the accrual month (the period earned), or it names the account. Company correspondence stating the amount is linked as explanation, not support. The item's GL link is the payment entry (`supports_claim=True`, role `moved`); traced_gl is that entry in the period labels containing its month; an OUT_OF_PERIOD flag (WARNING) moves it to the accrual month, so proposed[p] = −amount where *p* holds the accrual month but not the booking month, +amount where it holds the booking month but not the accrual month, 0 where it holds both or neither. documented follows the vouching rule. An accrual that never reverses, or that no executed document states, stays reversed to the GL by `dil_recon` (for example a proposed bonus pool the owner has not approved).
  - **Documented GL-export gap.** When reconciliation raises MISSING_PERIOD for a month and a linked document explains it as an export defect, with the management P&L tying to the trial balance, that month's P&L − GL difference over EBITDA accounts is a supported difference. One item carries −(P&L − GL, debit-positive) in every period label containing the month. It has no GL links and offsets the `dil_recon` reversal. Mechanically: a document in the package states, in one sentence that names the month (e.g. "March 2023", "Mar 2023", "Mar-23", "2023-03", "03/2023"), an export (export, extract, download, data pull or dump, saved search, query, GL detail) **and** an explicit defect in it (missing, incomplete, dropped, omitted, wrong, incorrect, instead, truncated, partial, corrupted, failed, "only has / includes / contains", re-run, replacement file); and, in one sentence that names the month or refers back to it ("the March income statement", "that month"), that the books are complete (trial balance / TB, books, ledger, income statement, P&L or management accounts with "complete", "correct", "accurate", "balanced", "ties", "agrees" or "reconciles", not negated). Words scattered across the document (a data request list that mentions a month, an export and a trial balance) are not an explanation. The flag and rationale state how many of the EBITDA accounts in management's P&L for the month have no GL activity. The difference counts EBITDA accounts only (not INTEREST, TAXES, DEPRECIATION, AMORTIZATION or balance sheet). A PARTIAL_GL_SUPPORT flag (WARNING) carries the whole effect; the open question asks for the replacement export and the trial-balance tie. *Principle:* diligence EBITDA must rest on complete books; reversing a month that the ledger holds but the export dropped would overstate EBITDA by a month of costs.
- **Review.** Diligence items are reviewed like management items: same `ReviewDecision`, same final-amount rules.

## 6. Reconciliation (`reconcile.py`)

- **GL vs P&L.** Roll the GL up by (month, account) and compare with the P&L for every month in `data_start..data_end` and every P&L account. `variance = pl − gl`. A variance greater than the tolerance raises `RECON_VARIANCE`, with the month and account.
- **Missing months.** A month in the data range with no GL entries at all, or with entries in fewer than 50% of the accounts active in its neighboring months, raises `MISSING_PERIOD`.
- **Duplicates.** Two or more entries with the same account, amount, counterparty, and `doc_number` (non-empty), or the same account, amount, counterparty, and memo within 7 days, raise `DUPLICATE_GL_ENTRY`. One issue lists the whole group.
- **Account coverage.** Raise `PL_ACCOUNT_NOT_IN_GL` or `GL_ACCOUNT_NOT_IN_PL` when an account appears on one side and not the other.
- **EBITDA from the GL,** per period label:
  - NI is the negated sum of every P&L entry, because debit-positive expenses reduce NI.
  - Interest, taxes, depreciation, and amortization are the sums of their classes.
  - EBITDA is NI + I + T + D + A.
- **Management's EBITDA.** Compare `schedule.reported_ebitda` with the GL-derived value and raise `MGMT_EBITDA_DIFFERS_FROM_GL` when they differ. `MGMT_SCHEDULE_ARITHMETIC` is raised when management's own totals don't foot.

## 7. Review workflow

- Decisions are appended to `review_log.jsonl`. The latest decision for each adj id wins.
- An unreviewed adjustment uses the tool's proposal and is marked "unreviewed" everywhere.
- A pending item (REQUEST_INFO) is excluded from diligence adjusted EBITDA.
- `correction_type` classifies every override. Tool-error types become regression cases via `scripts/qoe_corrections_to_evals.py`, which is the feedback loop.
- The reviewer can also update the status of open questions and record responses.

## 8. Excel export (`export_xlsx.py`)

Workbook `QoE_Evidence_Review_<deal_id>.xlsx`. Sheets, in this order:

1. **Cover.** Target and a SYNTHETIC banner; periods; run id; tool version; AI mode; input hashes; status counts; a legend of treatment colors and tickmarks.
2. **EBITDA Bridge.** The §5.6 rows, with columns for each period. Subtotals are **Excel formulas** (`=SUM(...)` / references). Adjustment rows are values.
3. **Adjustment Summary.** One row per adjustment:
   - identity: Ref, Title, Category;
   - amounts: Claimed and Tool proposed for each period, then Final for each period, and Difference = Final − Claimed as a formula;
   - review: Tool treatment, Reviewer treatment, Status;
   - evidence: Key flags, # GL links, # docs, # open questions.
   - A totals row uses formulas.
4. **One support sheet per adjustment**, named by the sanitized adj id (for example `Adj M-01`). Each sheet has:
   - management's description;
   - a tie-out table (claimed / traced GL / documented / proposed / final by period, with difference formulas);
   - linked GL entries (entry id, GL row, date, account, counterparty, doc #, memo, amount, supports claim?, docs);
   - documents with verbatim quotes;
   - flags;
   - "Documented facts" and "Judgment questions" as separate blocks;
   - recurrence observations;
   - the reviewer decision and rationale.
5. **Open Questions.** Q id, Ref, Question, Priority, Basis, Status, Response.
6. **GL-P&L Reconciliation.** A summary by month (GL total, P&L total, variance formula), followed by the variance detail rows.
7. **Data Quality.** Every issue.
8. **Review Log.** Every decision, in order.

**Formatting**

- Arial throughout.
- Number format `#,##0;(#,##0);"-"` with header units in USD.
- Frozen panes and sensible column widths.
- Blue font for hard-coded inputs, black for formulas.
- Treatment fills: ACCEPT green, REVISE amber, REJECT red, REQUEST_INFO blue-grey.

**Formula rules**

- No `XLOOKUP`, `FILTER`, `UNIQUE`, `SORT`, `SEQUENCE`, or `XMATCH`.
- The file must recalculate in LibreOffice with zero errors. Tests run the xlsx skill's `recalc.py` when LibreOffice is available.

## 9. Evaluation (`evaluate.py`)

Per deal and overall:

| Metric | Definition |
| --- | --- |
| treatment_accuracy | tool treatment == expected treatment |
| amount_accuracy | For non-REQUEST_INFO expected items where the tool also did not return REQUEST_INFO: every period's `abs(proposed − expected) ≤ 1.00`. Computed over all such items. |
| false_accept_rate | The tool says ACCEPT when the expected treatment is anything else, and either the expected treatment is REQUEST_INFO or the tool's amount exceeds the expected amount by more than 1.00 in at least one period (the accept overstates EBITDA). This is the most dangerous error, and it is reported first. An ACCEPT on an item whose expected amounts are at or above the claim in every period is reported separately as a missed revision. |
| gl_link_precision / recall | Tool claimed-and-supporting links (`supports_claim=True` and not removed by a challenge; a row replaced by its OUT_OF_PERIOD effect counts as supporting) vs `supporting_gl_rows`. Also report a surfaced-recall over `supporting ∪ related` using every linked row. |
| doc_link_precision / recall | Tool doc links vs `supporting_docs`. |
| flag_recall | The share of `expected_flags` raised on the right adjustment. |
| missed_contradictions | Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT, or ALREADY_EXCLUDED_FROM_EBITDA flags that were not raised. |
| data_quality_recall | Planted data-quality issues that were detected. The codes must match, along with every locator both sides carry (month, account, GL rows). A key entry with no locator matches on code alone. |
| diligence_item_accuracy | Expected diligence items (`GroundTruth.diligence_items`) are matched to tool items with `source="diligence"` by overlap of supporting GL rows. An expected item with no supporting_gl_rows matches an unmatched tool item with source=diligence and no supporting GL links whose non-zero periods are the same set of period labels. An item scores correct when every period is within 1.00. |
| ebitda_error | For each period: `abs(tool diligence_adjusted_ebitda − gt.diligence_adjusted_ebitda)`, plus `gl_ebitda` agreement. |
| by_case_type | treatment accuracy grouped by `case_type`. The vocabulary is the list in the `ExpectedAdjustment.case_type` comment in `qoe/schemas.py`. |

`scripts/qoe_evaluate.py` writes `reports/eval_<split>.json` and `reports/eval_<split>.md`. The markdown leads with false accepts and misses, then the headline accuracy.

## 10. Dev deal 1 catalog: Meridian Mechanical Services, LLC (SYNTHETIC)

This is a Florida commercial and residential HVAC and plumbing service contractor.

- Revenue is about $38M per year and reported EBITDA is about $4–5M.
- The GL is a QuickBooks Online CSV export (`qbo_gl_csv`) covering Jan 2024 – Jun 2026.
- The analysis periods are FY2024, FY2025, and TTM Jun-26 (Jul 2025 – Jun 2026).
- The GL contains P&L accounts only.
- Background activity is seeded and realistic: recurring vendors, payroll, rent, fuel, materials, and customer invoices, with seasonality and noise. There are a few thousand rows.

**Chart of accounts (P&L)**

| Range | Accounts |
| --- | --- |
| Revenue (Income) | 4000 Service Revenue – Commercial; 4010 Service Revenue – Residential; 4100 Maintenance Agreement Revenue; 4900 Sales Discounts (contra) |
| COGS | 5000 Materials & Equipment; 5100 Direct Labor – Technicians; 5200 Subcontractors; 5300 Vehicle & Fuel – Field; 5400 Inventory Adjustments & Write-offs |
| Expense | 6000 Salaries & Wages – Office; 6010 Officer Compensation; 6050 Payroll Taxes & Benefits; 6100 Rent & Occupancy; 6150 Repairs & Maintenance – Facilities; 6200 Insurance; 6300 Software & IT Services; 6400 Legal & Professional Fees; 6410 Accounting & Advisory Fees; 6450 Recruiting & HR; 6500 Advertising & Marketing; 6600 Travel, Meals & Entertainment; 6650 Auto Expense – Admin; 6700 Dues & Subscriptions; 6800 Bank & Merchant Fees; 6900 Office & General; 6950 Bad Debt Expense |
| D&A (Expense) | 7000 Depreciation Expense; 7050 Amortization Expense |
| Other Income | 8000 Other Income; 8050 Gain/Loss on Sale of Assets |
| Other Expense | 8100 Interest Expense; 8200 Other Expense; 9000 Income Taxes – State |

**The 14 management adjustments.** Management labels them M-01 … M-14. Amounts are claimed as FY2024 / FY2025 / TTM Jun-26, and the Truth column gives the diligence amounts in the same order.

| Ref | Management claim | Planted facts | Truth |
| --- | --- | --- | --- |
| M-01 | **Dawson litigation legal fees** (non-recurring), acct 6400. Claimed 0 / 120,000 / 65,500. | Hollis & Crane LLP bills two matters. Matter 2291 *Dawson v. Meridian* has five invoices: 25-0212 Feb $14,500; 25-0418 Apr $22,000; 25-0615 Jun $18,000; 25-0910 Sep $21,000; 25-1120 Nov $9,000 (total $84,500). Matter 1004 *General Corporate & Employment* has a monthly retainer of $2,500 every month in 2024–2026, plus ad hoc items: $6,000 in Oct 2024 and $5,500 in Aug 2025 (employment policy review). FY2025 H&C total is 84,500 + 30,000 + 5,500 = 120,000. TTM H&C total is 30,000 (lit) + 30,000 + 5,500 = 65,500. Documents: a 2023 engagement letter for Matter 1004 stating the "$2,500 per month … continuing until terminated by either party"; the Jan 2025 Matter 2291 litigation engagement letter; all five litigation invoices; a sample retainer invoice; the Aug 2025 policy-review invoice; and a settlement agreement dated 2025-11-14 under which the insurer pays the settlement (no GL effect). | **REVISE 0 / 84,500 / 30,000.** Flags: RECURRING_PATTERN (Matter 1004 was $36,000 in FY2024), CONTINUING_OBLIGATION (retainer). Questions: confirm no post-settlement fees or obligations; confirm the insurer paid the settlement. |
| M-02 | **Owner compensation normalization** (normalization), acct 6010. Claimed 360,000 / 360,000 / 360,000. | Owner/CEO R. Castellano is paid $660,000/yr as 24 semi-monthly payroll entries of $27,500 ("Officer payroll – R. Castellano"). The only support is an **unsigned DRAFT** post-close employment agreement at a $300,000 base, watermarked DRAFT. There is no market compensation benchmark. | **REQUEST_INFO.** Flags: UNSIGNED_OR_DRAFT_SUPPORT, NORMALIZATION_BENCHMARK_MISSING. Questions: the executed agreement; the basis for $300k market pay; the payroll-tax and benefits effect. |
| M-03 | **Owner personal expenses** (owner / discretionary), accts 6600, 6650, 6700. Claimed 0 / 48,000 / 48,000. | Pelican Bay Country Club dues of $1,100/mo from Jan 2025 (6700, memo "Club dues – R. Castellano"). BMW Financial Services lease of $1,500/mo from Jan 2025 (6650, memo "Lease – X5 (D. Castellano, personal)"). Business travel in 6600 of $5,600 per trip for the ACCA conference (Mar 2025), a Carrier dealer summit (Sep 2025), a supplier plant visit (Nov 2025), and a Mar 2026 ACCA trip. FY2025 = 13,200 + 18,000 + 16,800; TTM = 13,200 + 18,000 + 16,800 (Sep 2025, Nov 2025, Mar 2026). Documents: conference registration confirmations and a supplier visit agenda, each naming Meridian as the attending company and giving a business purpose. | **REVISE 0 / 31,200 / 31,200.** Flag: CONTRADICTORY_EVIDENCE (the travel has a documented business purpose). |
| M-04 | **CFO search fee** (non-recurring), acct 6450. Claimed 0 / 45,000 / 15,000. | Barrow Search Partners retained search: an engagement letter (fee is one-third of first-year cash compensation of $135,000, payable in three installments) and three invoices of $15,000 each in Apr, May, and Jul 2025. There is also routine job-board spend (Indeed, about $1,200–1,800/mo) in 6450 that is **not** part of the claim. | **ACCEPT 0 / 45,000 / 15,000.** |
| M-05 | **Severance, former VP Sales** (non-recurring), acct 6000. Claimed 0 / 0 / 75,000. | Separation agreement with T. Whitfield signed 2026-01-09: $75,000 severance in three monthly installments. Payroll entries of $25,000 each in Feb, Mar, and Apr 2026, memo "Severance – T. Whitfield". | **ACCEPT 0 / 0 / 75,000.** |
| M-06 | **"One-time" FieldPro implementation** (non-recurring), acct 6300. Claimed 0 / 96,000 / 48,000. | Brightline Systems Group bills $8,000/mo for Jan 2025 – Jun 2026 ("FieldPro managed services – <Mon YYYY>"). The Managed Services Agreement (signed Dec 2024) has a "36-month initial term commencing January 1, 2025", a "monthly fee of $8,000" covering licensing, hosting, and support, and "renews automatically". A Mar 2025 email from the controller calls it "our FieldPro subscription". | **REJECT 0 / 0 / 0.** Flags: CONTRADICTORY_EVIDENCE, CONTINUING_OBLIGATION, RECURRING_PATTERN. |
| M-07 | **Refinancing costs** (non-recurring), acct 8100. Claimed 0 / 35,000 / 0. | Jun 2025 entries in 8100 Interest Expense: "Write-off unamortized loan origination fees – Gulfstream Bank" $22,000 and "Prepayment penalty – Gulfstream Bank term loan payoff" $13,000. There is a payoff letter. | **REJECT 0 / 0 / 0.** Flag: ALREADY_EXCLUDED_FROM_EBITDA. |
| M-08 | **Transaction-related professional fees** (non-recurring), accts 6400, 6410. Claimed 0 / 62,000 / 62,000. | Keel Harbor Advisors sell-side retainer of $26,000 (Oct 2025, 6400). Dunmore & Pike CPAs sell-side readiness of $15,000 (Nov 2025, 6410). Management also included Hollis & Crane invoice **25-0910** ($21,000, Matter 2291 Dawson), which is already in M-01. There are engagement letters for Keel Harbor and Dunmore & Pike, and invoices for both. | **REVISE 0 / 41,000 / 41,000.** Flag: OVERLAP_WITH_OTHER_ADJUSTMENT (with M-01). |
| M-09 | **Storm damage repairs** (non-recurring), acct 6150. Claimed 58,000 / 0 / 0. | Oct–Dec 2024 costs: Gulf Coast Roofing $38,000 and Tampa Bay Restoration $20,000, from an October 2024 hurricane. Sunshine Mutual Insurance paid $40,000 in Feb 2025 on claim #FL-24-88172, booked to 8000 Other Income ("Insurance proceeds – storm claim FL-24-88172"). There is a claim settlement letter showing the $40,000 net payment after a $10,000 deductible. Management did not remove the gain. | **REVISE 58,000 / −40,000 / 0.** Flag: OFFSETTING_RECOVERY. |
| M-10 | **Prior-year subcontractor true-up** (out-of-period), acct 5200. Claimed 0 / 42,000 / 0. | Apex Ductwork LLC invoice AD-3391 booked Mar 2025 for $42,000, memo "Project closeout true-up – 2024 projects". The invoice states "Service period: July 1, 2024 – December 31, 2024". | **REVISE −42,000 / 42,000 / 0.** Flag: OUT_OF_PERIOD. |
| M-11 | **Warehouse relocation** (non-recurring), accts 6100, 6150. Claimed 0 / 80,000 / 80,000. | Suncoast Movers $32,000 (Feb 2025, 6100) and Brandon Build-Out Contractors $48,000 (Mar–Apr 2025 as two $24,000 invoices, 6150), with invoices for each. Nothing in Jul 2025 – Jun 2026. | **REVISE 0 / 80,000 / 0.** Flag: PERIOD_MISMATCH. |
| M-12 | **Pro forma dispatcher savings** (pro forma), acct 6000. Claimed 0 / 0 / 165,000. | Three dispatchers are still on payroll through Jun 2026. The only document is a Mar 2026 email from the COO: "we plan to reduce the dispatch team by three FTEs once FieldPro auto-dispatch is live — targeting Q3 2026". There are no separation agreements. | **REQUEST_INFO.** Flag: PRO_FORMA_NOT_REALIZED. Questions: evidence the reduction happened; severance cost; whether the roles are backfilled. |
| M-13 | **"One-time" inventory write-off** (non-recurring), acct 5400. Claimed 0 / 64,000 / 64,000. | Dec 2025 "Year-end physical count adjustment – obsolete & shrink" of $64,000. Dec 2024 has the same entry at $58,500. The Dec 2025 inventory count memo says: "Consistent with prior years, the year-end count adjustment reflects shrink and obsolete parts." | **REJECT 0 / 0 / 0.** Flags: RECURRING_PATTERN, CONTRADICTORY_EVIDENCE. |
| M-14 | **Customer bankruptcy write-off** (non-recurring), acct 6950. Claimed 0 / 52,000 / 52,000. | Oct 2025 bad debt of $52,000 for Halvorsen Builders, with a Chapter 7 bankruptcy notice for Halvorsen Builders. Normal bad debt is small ($300–700/mo). | **ACCEPT 0 / 52,000 / 52,000.** Ambiguity is medium. The alternative view normalizes 6950 to its 30-month average; it is pre-registered in the benchmark's key alternatives. RECURRING_PATTERN must not fire. |

**Planted data-quality issues**

| Issue | Detail | Code |
| --- | --- | --- |
| Duplicate posting | Coastal Risk Insurance monthly premium installment Num CRI-25-0507, $18,400.00 (6200), is posted twice, three days apart, in May 2025. The P&L includes both. It also becomes diligence item **D-1**: +18,400 in FY2025, 0 in FY2024 and TTM. | `DUPLICATE_GL_ENTRY` |
| Top-side entry | Management's monthly P&L for Dec 2025, account 6000, is $25,000 higher than the GL. It is a top-side accrual for a *proposed* discretionary bonus pool. A Jan 2026 controller email (in the financials folder) says the owner has not approved the pool, nothing has been communicated to employees or paid, and it will not be booked in QuickBooks. No bonus payments appear anywhere in 6000 or 6010. Reversing to the GL (`dil_recon` 0 / +25,000 / +25,000) is therefore correct. | `RECON_VARIANCE` |
| Reported EBITDA gap | Management's reported EBITDA for FY2025 and TTM is therefore $25,000 lower than the GL-derived figure. | `MGMT_EBITDA_DIFFERS_FROM_GL` |

**§10.1 Answer-key review amendments (binding).** An independent review panel (a Deals senior manager, a buy-side investor, and an audit senior, then adjudicated) confirmed every truth treatment and amount above. It required the package changes below so that each answer can be reached from the evidence:

- **M-01.** The litigation engagement letter describes Dawson as a customer property-damage claim. The settlement agreement states a $100,000 self-insured retention for defense costs, so no reimbursement of the $84,500 is expected. Question topics also cover defense coverage and retention, the nature of the claim, and the post-close status of the Matter 1004 retainer.
- **M-02.** The draft agreement is silent on club dues and vehicles. Ambiguity is medium. The rationale states the provisional 360,000 per period (about 365,220 with employer Medicare).
- **M-03.** Add a BMW Financial Services lease statement (lessee D. Castellano, X5, $1,500/mo from Jan 2025) and a Pelican Bay Country Club statement (member R. Castellano, individual membership since Jan 2025, $1,100/mo). Replace the registration confirmations with per-trip **expense reports** of $5,600 each. Each report itemizes registration, airfare, and hotel and states the business purpose, and its report number is the GL Num. supporting_docs = the lease and club statements; the expense reports are related. RECURRING_PATTERN must not fire.
- **M-04.** The Barrow letter keeps its "retained search" wording as a deliberate trap. Must not fire: CONTINUING_OBLIGATION, RECURRING_PATTERN.
- **M-05.** The separation agreement says "three equal monthly installments of $25,000". Must not fire: RECURRING_PATTERN.
- **M-06.** The rationale states that TTM 48,000 = Jul–Dec 2025, the claimed set under the tie-break.
- **M-07.** The rationale cites that management's interest line equals GL 8100 including the 35,000.
- **M-08.** The Support Ref cites the data-room file of H&C invoice 25-0910 (for example `DR 7.1; DR 7.2; DR 4.2.4`), which makes the intended set the unique fit under the §5.3 tie-break. The Keel Harbor letter reads "one-time retainer of $26,000 payable on signing, creditable against the success fee". Must not fire: CONTINUING_OBLIGATION.
- **M-09.** Add Gulf Coast Roofing ($38,000) and Tampa Bay Restoration ($20,000) invoices citing claim FL-24-88172. Add an itemized settlement letter: loss 58,000; non-covered 8,000 (above a sublimit); covered 50,000; deductible 10,000; paid 40,000; claim closed. Ambiguity is medium. The pre-registered alternative is 40,000 / −40,000 / 0.
- **M-10.** There are no other Apex or closeout true-ups anywhere in the GL.
- **M-11.** The two Brandon invoices have distinct numbers and memos ("Progress billing 1 of 2" / "2 of 2") and post more than 7 days apart.
- **M-12.** Dispatcher payroll is 3 × $55,000 = $13,750/mo in 6000 (memo "Payroll – Dispatch") through Jun 2026. Ambiguity is medium. The pre-registered alternative is REJECT 0 / 0 / 0.
- **M-13.** The count memo states the $64,000 current-year adjustment and the $58,500 prior-year adjustment.
- **M-14.** Add an Official Form 410 proof of claim for $52,000 listing Halvorsen invoices dated Jun–Aug 2025. Background 6950 memos must not share the Halvorsen theme.

**Generator constraints**

- There are no unplanted duplicate groups anywhere in the deal.
- 8050, 8200, and 9000 have zero activity; 8000 carries only the M-09 proceeds. The company is an LLC taxed as an S corporation.
- There are no bonus payments in 6000 or 6010.
- **Ground truth:** every item carries a `case_type`, `ambiguity`, `supporting_docs`, and `question_topics`. Must-not flags are recorded in `reviewer_note`. The case types are:
  - M-01 RECURRING; M-02 NEEDS_INFO; M-03 CONTRADICTED;
  - M-04, M-05, and M-14 ADEQUATE;
  - M-06 CONTRADICTED; M-07 EBITDA_EXCLUDED; M-08 OVERLAP;
  - M-09 RECOVERY_OFFSET; M-10 OUT_OF_PERIOD; M-11 WRONG_PERIOD;
  - M-12 NEEDS_INFO; M-13 RECURRING.
- **Expected totals.**
  - Claims: 418,000 / 1,004,000 / 1,034,500.
  - Management finals: 16,000 / 335,700 / 244,200.
  - Plus D-1: 0 / 18,400 / 0.
  - Pending (M-02, M-12): 360,000 / 360,000 / 525,000.

**Documents.** These are data-room style file names, for example `4.2.1 Hollis Crane Invoice 25-0212.pdf` and `6.1 Brightline Managed Services Agreement.pdf`. Emails are `.txt` files with From / To / Date / Subject headers. Every document footer reads "SYNTHETIC — generated for QoE Evidence Review testing".

**Management schedule.** The layout is described in §3.6. Refs are `M-01`…`M-14`, and the rows run Net income / Interest expense / Income tax expense / Depreciation and amortization / Reported EBITDA / the adjustments / Total management adjustments / Management adjusted EBITDA. The support-ref column cites data-room folders, for example `DR 4.2`. The GL-account column is filled for every item except M-12.

## 11. Conventions

- Python 3.12 via `uv`, and Pydantic v2 `StrictModel`.
- Tests go in `tests/test_<module>.py`. Unit tests build small in-memory fixtures and must not depend on generated deal data. Integration tests over `data/dev` skip if the data is absent.
- Match the repo's style: module docstrings, `from __future__ import annotations`, and type hints. Comments explain *why*, not *what*.
- No network access in tests. The live LLM path is tested against a fake OpenAI client.
