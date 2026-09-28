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
data/qoe/
  specs/<deal_id>.yaml    generator input                         [generator]
  dev/<deal_id>/          generated deal packages (committed)
  holdout/<deal_id>/
tests/qoe/                one test module per module above
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
- PDF pages come from `app.pdf_text.extract_pdf_text` (pypdf, plain mode). Page text is canonicalized with `app.canonicalize.canonicalize_page_text`.
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
- An entry is **supporting** if it is claimed and survives every challenge.

`traced_gl[p]` is the sum of claimed entries in period *p*. `proposed[p]` is the sum of supporting entries plus the amount effects of challenges (recoveries and period moves).

### 5.1 Facts and intent

- Run `ai.extract_facts(doc)` on every document, then verify every quote.
- Run `ai.parse_intent(adj)` on every adjustment.

### 5.2 Candidate linking (`trace.py`)

Every P&L entry (class ≠ BALANCE_SHEET) is scored against the adjustment. The score is additive and each signal is recorded in `GLLink.reasons`. Signals:

- **Account.** The account is in `adj.gl_accounts`.
- **Counterparty.** Fuzzy match (normalized token overlap) against `intent.counterparties`, or against the counterparties of documents cited by the support refs or linked by reference.
- **Keywords.** `intent.keywords` appear in the memo.
- **Reference.** `doc_number` or the memo contains a reference number from `intent.reference_numbers`, or from a document's `reference_numbers`.
- **Document.** A document's facts contain the entry's `doc_number`, or they show the same amount (±tolerance) together with a matching counterparty.

Entries above the link threshold are linked.

- Linked entries in periods with a nonzero claim are candidates for **claimed**.
- Linked entries elsewhere are kept for the recurrence and period-mismatch analysis (`supports_claim=False`).

**Grouping.** Linked entries are grouped by normalized counterparty plus a memo theme, which is the memo with dates, amounts, invoice numbers, and month names stripped. If a document reference is present (a matter number, a contract), it wins over the memo theme. For example, litigation invoices under one matter number group separately from retainer invoices from the same law firm.

### 5.3 Claimed-set fit

For each period *p* with a nonzero claim:

- **Linked total too high.** If the linked total in *p* exceeds the claim by more than the tolerance, search for an exact subset (to the cent) of linked entries that sums to the claim. Prefer whole groups first, then entries.
  - The search is bounded to at most 30 entries, using meet-in-the-middle or a cents DP with a cap.
  - If a subset is found, it is the claimed set. The rest are linked with `supports_claim=False`, and `EXCESS_GL_ACTIVITY` (INFO) is raised.
  - If no subset is found, treat all strongly linked entries as claimed and note the gap.
- **Linked total too low.** If it is below the claim by more than the tolerance, raise `PARTIAL_GL_SUPPORT` (WARNING) with `amount_impact = linked − claimed`.
- **Nothing linked.** If no entries link in any period, raise `NO_GL_SUPPORT` (CRITICAL).

### 5.4 Challenges (`challenge.py`)

Each flag has a trigger, an effect on `proposed`, and a severity.

| Flag | Trigger | Effect on proposed |
| --- | --- | --- |
| `ALREADY_EXCLUDED_FROM_EBITDA` | Claimed entries sit in INTEREST, TAXES, DEPRECIATION, or AMORTIZATION accounts. EBITDA already adds them back. | Remove those entries. CRITICAL. |
| `OVERLAP_WITH_OTHER_ADJUSTMENT` | An entry is claimed by more than one adjustment. The adjustment with the highest link score keeps it; ties go to schedule order. The others get this flag, naming the related adj id. | Remove from the others. CRITICAL. |
| `CONTRADICTORY_EVIDENCE` | `ai.find_contradictions` returns a verified conflict, such as a document calling a "one-time" cost a monthly subscription. | Remove the entries the contradiction covers. If it is not entry-specific, remove every group whose documents contain it. WARNING. |
| `CONTINUING_OBLIGATION` | A linked document has a term fact (monthly_fee, retainer, auto_renew, ongoing_services, or a term_end after the last claimed month) that applies to claimed entries. | Remove the entries whose amount equals the recurring fee, or whose group is covered by the term. WARNING. |
| `RECURRING_PATTERN` | A claimed group has comparable activity (same counterparty and theme, or same account and theme) in another fiscal period that the claim does not cover, at ≥ 50% of the claimed group's amount; or it has ≥ 3 similar months outside the event window. Record a `RecurrenceObservation` with amounts by period label. | Remove that group. WARNING. |
| `OUT_OF_PERIOD` | A document linked to a claimed entry has a service period that falls in different months from the booking month, and in a different fiscal period. | For each period label: + the amount if the booking month is in it, − the amount pro rata by the service-period months it contains. WARNING. |
| `PERIOD_MISMATCH` | The claim in *p* is nonzero but no claimed entry falls in *p*, while linked entries exist in other periods. The same applies when the claim in *p* exceeds traced activity in *p* and the excess matches activity in another period. | `proposed[p]` = the supporting total in *p*. WARNING. |
| `OFFSETTING_RECOVERY` | A credit entry in OTHER_INCOME or REVENUE (or a credit in the same account) relates to the same event (counterparty, keyword, or reference, such as a claim number found in a linked document), and management did not adjust it. | − the recovery amount in the periods containing the recovery month. WARNING. |
| `UNSIGNED_OR_DRAFT_SUPPORT` | A linked agreement is `is_draft` or `is_signed is False`. | None by itself; it drives REQUEST_INFO for normalization and pro forma items. WARNING. |
| `NORMALIZATION_BENCHMARK_MISSING` | A normalization item has no signed agreement or benchmark document that supports the normalized level. | None; it drives REQUEST_INFO. WARNING. |
| `PRO_FORMA_NOT_REALIZED` | `intent.is_pro_forma` is set, and the GL shows the cost continuing through `data_end` or no evidence that the event occurred. | None; it drives REQUEST_INFO. CRITICAL. |
| `NO_DOCUMENT_SUPPORT` | More than 25% of the claimed amount in any period has no linked document. | None; it drives REQUEST_INFO when above 25%. WARNING. |
| `DOC_GL_AMOUNT_MISMATCH` | A document linked to an entry states a total that differs from the entry by more than the tolerance. | None; it creates a question. WARNING. |
| `SIGN_ERROR` | The claim's sign conflicts with the claimed entries, for example an add-back made of credits. | None; it creates a question. WARNING. |
| `DUPLICATE_GL_ENTRY` | A claimed entry is part of a duplicate group from reconciliation. | None; it creates a question. WARNING. |

**Entry qualification.** `ai.classify_entries` covers claims where only some of the activity fits management's basis, such as personal versus business travel or litigation versus general matters. Entries marked `qualifies=False` with a verified basis are removed. The removal is recorded with a `CONTRADICTORY_EVIDENCE` flag, or a `RECURRING_PATTERN` flag when recurrence is the reason.

**Normalization items** (`intent.is_normalization`):

- **Claimed** is the actual cost in the linked accounts minus the normalized level.
- **Supported** requires the actual cost in the GL, plus a signed document that sets the normalized level.
- If either is missing, the item goes to REQUEST_INFO.

### 5.5 Treatment (`propose.py`)

This step is deterministic and runs in order:

1. If `PRO_FORMA_NOT_REALIZED` is raised → **REQUEST_INFO**.
2. If this is a normalization item with `UNSIGNED_OR_DRAFT_SUPPORT` or `NORMALIZATION_BENCHMARK_MISSING` → **REQUEST_INFO**.
3. If `NO_GL_SUPPORT` is raised and there is no contradiction → **REQUEST_INFO**.
4. If `NO_DOCUMENT_SUPPORT` is above 25% → **REQUEST_INFO**.
5. Compute `proposed[p]` for every period label, including periods management left at zero. Examples: the −42,000 out-of-period move into FY2024, and the −40,000 recovery.
6. If every `|proposed[p] − claimed[p]|` is within the tolerance → **ACCEPT**.
7. If every `proposed[p]` is 0 → **REJECT**.
8. Otherwise → **REVISE**.

For REQUEST_INFO, `proposed = {}`, and the rationale states the provisional amount the evidence would support.

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
| `dil_total` | Total diligence adjustments | subtotal |
| `diligence_adjusted_ebitda` | Diligence adjusted EBITDA | subtotal |
| `pending` | Memo: management adjustments pending information (excluded) | memo |

**Identity:** `diligence_adjusted_ebitda = gl_ebitda + Σ final amounts (excluding pending)`. Tests assert it.

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
| false_accept_rate | The tool says ACCEPT when the expected treatment is anything else. This is the most dangerous error, and it is reported first. |
| gl_link_precision / recall | Tool claimed-and-supporting links (`supports_claim=True` and not removed by a challenge) vs `supporting_gl_rows`. Also report a surfaced-recall over `supporting ∪ related` using every linked row. |
| doc_link_precision / recall | Tool doc links vs `supporting_docs`. |
| flag_recall | The share of `expected_flags` raised on the right adjustment. |
| missed_contradictions | Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT, or ALREADY_EXCLUDED_FROM_EBITDA flags that were not raised. |
| data_quality_recall | Planted data-quality issues that were detected, matched on code and month or account. |
| ebitda_error | For each period: `abs(tool diligence_adjusted_ebitda − gt.diligence_adjusted_ebitda)`, plus `gl_ebitda` agreement. |
| by_case_type | treatment accuracy grouped by `case_type` |

`scripts/qoe_evaluate.py` writes `reports/qoe/eval_<split>.json` and `reports/qoe/eval_<split>.md`. The markdown leads with false accepts and misses, then the headline accuracy.

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
| M-14 | **Customer bankruptcy write-off** (non-recurring), acct 6950. Claimed 0 / 52,000 / 52,000. | Oct 2025 bad debt of $52,000 for Halvorsen Builders, with a Chapter 7 bankruptcy notice for Halvorsen Builders. Normal bad debt is small ($300–700/mo). | **ACCEPT 0 / 52,000 / 52,000.** Ambiguity is medium: some seniors accept only the excess over normal bad debt. |

**Planted data-quality issues**

| Issue | Detail | Code |
| --- | --- | --- |
| Duplicate posting | One Coastal Risk Insurance premium bill (6200, same Num and same amount) is posted twice, three days apart, in May 2025. The P&L includes both. | `DUPLICATE_GL_ENTRY` |
| Top-side entry | Management's monthly P&L for Dec 2025, account 6000, is $25,000 higher than the GL. It is a top-side bonus accrual that is not in the GL. | `RECON_VARIANCE` |
| Reported EBITDA gap | Management's reported EBITDA for FY2025 and TTM is therefore $25,000 lower than the GL-derived figure. | `MGMT_EBITDA_DIFFERS_FROM_GL` |

**Documents.** These are data-room style file names, for example `4.2.1 Hollis Crane Invoice 25-0212.pdf` and `6.1 Brightline Managed Services Agreement.pdf`. Emails are `.txt` files with From / To / Date / Subject headers. Every document footer reads "SYNTHETIC — generated for QoE Evidence Review testing".

**Management schedule.** The layout is described in §3.6. Refs are `M-01`…`M-14`, and the rows run Net income / Interest expense / Income tax expense / Depreciation and amortization / Reported EBITDA / the adjustments / Total management adjustments / Management adjusted EBITDA. The support-ref column cites data-room folders, for example `DR 4.2`. The GL-account column is filled for every item except M-12.

## 11. Conventions

- Python 3.12 via `uv`, and Pydantic v2 `StrictModel`.
- Tests go in `tests/qoe/test_<module>.py`. Unit tests build small in-memory fixtures and must not depend on generated deal data. Integration tests over `data/qoe/dev` skip if the data is absent.
- Match the repo's style: module docstrings, `from __future__ import annotations`, and type hints. Comments explain *why*, not *what*.
- No network access in tests. The live LLM path is tested against a fake OpenAI client.
