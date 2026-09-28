# Deal spec format (`data/qoe/specs/<deal_id>.yaml`)

A deal spec describes one synthetic QoE deal completely. The generator turns it into a
deal package in the `docs/qoe/SPEC.md` §3 layout. No Python changes are needed to author
a new deal.

```bash
uv run python scripts/qoe_generate_deals.py --spec data/qoe/specs/<deal_id>.yaml --out data/qoe/dev
uv run python scripts/qoe_generate_deals.py --all      # every spec, into data/qoe/<split>/
```

The output goes to `<out>/<deal_id>/`. Generation is deterministic: the same spec gives
byte-identical files. Randomness comes from `seed`, and each background stream has its own
sub-seed, so adding or editing one stream never changes the rows of another.

Every model rejects unknown keys, so a typo fails loudly. Every consistency check below
raises a `GenerationError` naming the YAML item to fix.

## Conventions

- **Months** are `"YYYY-MM"` and **dates** are `"YYYY-MM-DD"`. Quote both.
- **Planted amounts are debit-positive** (SPEC §3.2): expenses are `+`, and revenue and
  other-income credits are `-`. For example, an insurance recovery is `amount: -40000`.
- **Background amounts are magnitudes.** The sign follows the account's normal balance
  (credit for income types, debit otherwise). Set `direction:` to override it, for example
  `direction: debit` for sales discounts booked to an income account.
- **Keys.** Every GL row has a stable key. Planted rows use the `key` you give them.
  Background rows are keyed `<stream id>/<YYYY-MM>/<n>`. The answer key, documents, and
  claim checks refer to rows by key, or by glob (`hc_lit_*`, `dispatch_pay_2026*`). The
  generator resolves each key to its final GL source row. A glob must match at least one
  row. Choose key prefixes that do not collide with stream ids: `travel_*` would also match
  a stream called `travel_meals`.
- **YAML flow lists split on commas.** Write `["Tampa, FL 33619"]`, not `[Tampa, FL 33619]`.
  Key-value rows must be exactly `[label, value]`, and the generator rejects any other shape.
- **Text is limited to the PDF standard-font character set (cp1252).** En and em dashes,
  curly quotes, and `§` are fine. Arrows and emoji are rejected.

## Top-level keys

| Key | Meaning |
| --- | --- |
| `deal_id`, `split` (`dev` \| `holdout`), `seed`, `package_date` | Identity. `package_date` stamps the xlsx metadata. |
| `company` | `name`, `industry`, `short_name`. |
| `periods`, `data_start`, `data_end`, `tolerance`, `currency` | Copied to `deal.yaml` (SPEC §3.1). |
| `gl_format` | `qbo_gl_csv`, `netsuite_csv`, or `xero_xlsx`. This sets the GL writer and the chart-of-accounts headers. |
| `deal_yaml_gl_format` | The value `deal.yaml` declares. The default is `auto`, which exercises format detection. |
| `accounts` | The chart of accounts, in export order. |
| `sequences` | Shared number sequences, for example `{ar_invoice: 10231}`. |
| `split_defaults` | The QBO `Split` column for each generic transaction type. |
| `txn_types` | Overrides for transaction-type labels: `{bill: {netsuite_csv: "Vendor Bill"}}`. |
| `default_dimensions`, `netsuite_internal_id_start` | NetSuite Subsidiary, Department, Class, and Location, and the first Internal ID. |
| `parties` | Reusable letterheads and address blocks for documents. |
| `background` | Recurring activity streams. |
| `planted` | Explicit rows with stable keys. |
| `data_quality` | Duplicates, top-side P&L entries, and missing GL months. |
| `documents` | The data room. |
| `monthly_pl` | Layout of management's P&L (the QBO layout by default). |
| `schedule` | Management's adjusted EBITDA schedule. |
| `ground_truth` | The answer key. |
| `readme_extra` | Extra lines for `README.txt`. |

## Accounts

```yaml
- {number: "6400", name: Legal & Professional Fees, type: Expense, detail_type: Legal & Professional Fees}
```

`type` is written verbatim to the chart of accounts. It also decides the EBITDA class under
the SPEC §3.4 rules and the account's normal balance. Two keys are optional:

- `ebitda_class` with `override_basis` writes `gl/account_mapping_overrides.csv` when the class
  differs from the rules.
- `natural: debit|credit` sets the normal balance when the type is ambiguous.

The GL may only post to P&L accounts. Balance-sheet accounts can appear in the chart as
context.

The QBO chart headers are `Account #,Full name,Type,Detail type`. NetSuite uses
`Number,Name,Account Type,Description`. Xero uses `*Code,*Name,*Type,*Tax Code,Description`.

## Background streams

```yaml
- id: mat_plumbing                 # also the row-key prefix and RNG sub-seed
  account: "5000"
  txn_type: bill                   # generic type (below) or a literal source label
  mode: allocate                   # allocate (monthly total split over slots) | fixed (fixed amount per slot)
  start: "2024-01"                 # optional active window
  end: "2026-06"
  schedule: {weekdays: [3]}        # exactly one of: days | count | weekdays
  amount: {monthly: 150000, growth: 0.05, noise: 0.07, spread: 0.3}
  counterparties:
    - {name: Suncoast Plumbing Supply Co., num: "SPS{seq}", seq_start: 77104, seq_step: [5, 40]}
  memo: "Weekly statement – plumbing materials & water heaters, week ending {mdy}"
```

**`schedule`** sets when rows post within a month.

- `days: [15, -1]` posts on fixed days. `-1` is the last day of the month.
- `count: [lo, hi]` posts on that many random business days.
- `weekdays: [0..6]` posts on every matching weekday. Monday is 0.
- `months: [3, 6, 9, 12]` filters the calendar months.
- `adjust: prior|next` moves a weekend date to a business day.

**`amount`** depends on the mode.

- **allocate.** `monthly` is the total at `data_start`. Optional terms:
  - `seasonality` is 12 factors, normalized to a mean of 1.
  - `growth` is an annual rate, compounded monthly.
  - `noise` is a uniform ± fraction applied to each month's total.
  - `spread` is the ± dispersion of row weights within a month.
  - `round` is the rounding increment for each month's total.
- **fixed.** Use `fixed`, `by_year: {2024: …}`, or a per-counterparty `amount`. Add
  `escalate_pct` and `escalate_month` to compound the amount annually.

**`counterparties`** accepts plain names or mappings. In allocate mode, each row picks a
counterparty by `weight`. In fixed mode, each counterparty posts a row in every slot. Each
counterparty can set:

- `start` and `end`, its active window;
- `memo`, which overrides the stream memo;
- `num`, `seq_start`, and `seq_step`, its own document-number series.

**Numbers.** A counterparty's `num` format takes precedence. Otherwise the stream's
`num: {format, sequence | start, step}` applies. A named `sequence` is shared with every
other stream that uses it and increases in date order. Planted numbers are never reused.

**`memo`** is a string or a list; the generator picks from the list at random. `choices`
defines extra random placeholders, for example `choices: {unit: [RTU-1, RTU-2]}`.

**Generic `txn_type` values.** `invoice`, `sales_receipt`, `credit_memo`, `bill`,
`vendor_credit`, `expense`, `check`, `deposit`, `journal`, and `payroll`. Each is mapped to
the source system's label. For example, `payroll` becomes QBO "Journal Entry" and Xero
"Manual Journal".

## Placeholders

Memos, keys, numbers, and planted counterparties can use these placeholders:

- `{yyyy}` `{yy}` `{mm}` `{dd}` `{mon}` (Jan) `{month}` (January) `{q}` `{n}`;
- `{mdy}` (MM/DD/YYYY) and `{date}` (ISO);
- `{prev_mon}` `{prev_month}` `{prev_yyyy}` `{prev_month_end_mdy}` `{last_yyyy}`;
- `{job}` (`YY-NNNN`), `{seq}` (number formats only), and any `choices` name.

`{n}` is the slot index within the month, starting at 1. For a repeated planted row it is
the index within `repeat.days`.

## Planted rows

```yaml
- {key: apex_trueup, date: "2025-03-14", account: "5200", counterparty: Apex Ductwork LLC,
   num: AD-3391, amount: 42000, memo: "Project closeout true-up – 2024 projects"}
- key: "hc_retainer_{yyyy}{mm}"            # a series: one row per month and day
  repeat: {start: "2024-01", end: "2026-06", days: [1]}
  account: "6400"
  counterparty: Hollis & Crane LLP
  num: "{yy}-{mm}01"
  amount: 2500
  memo: "Matter 1004 – General corporate & employment – monthly retainer – {mon} {yyyy}"
- {key: halvorsen_inv_1, date: "2025-06-18", account: "4000", txn_type: invoice,
   counterparty: Halvorsen Builders, num_sequence: ar_invoice, amount: -18400, memo: "…"}
```

Each row needs `date` or `repeat`, not both. The default `txn_type` is `bill`.
`num_sequence` draws the number from a shared sequence, so a planted invoice slots into
the company's numbering. Documents can cite that number, as described under Documents.

## Data-quality issues

```yaml
data_quality:
  duplicates: [{key: prem_202505_dup, of: coastal_prem_202505, days_later: 3, note: "…"}]
  topside:    [{month: "2025-12", account: "6000", amount: 25000, note: "…"}]   # in the P&L only
  missing_gl_months: [{month: "2025-08", keep_accounts: [], note: "…"}]         # in the P&L, not the GL
```

The answer key's `data_quality` entries are derived from these items:
`DUPLICATE_GL_ENTRY`, `RECON_VARIANCE`, `MISSING_PERIOD`, and `MGMT_EBITDA_DIFFERS_FROM_GL`.
The last is added automatically whenever management's reported EBITDA differs from the GL.
The generator also rejects any duplicate group, by the SPEC §6 rule, that you did not plant.

## Documents

```yaml
- id: hc_inv_0212                      # used by ground_truth.supporting_docs
  filename: 4.2.1 Hollis Crane Invoice 25-0212.pdf    # doc_id = basename, unique per deal
  folder: 04 Legal                     # sub-folder under documents/
  template: invoice                    # invoice | letter | agreement | memo | form | email (.txt)
  supports: [hc_lit_0212]              # rows this document evidences
  key_phrases: ["Invoice No.: 25-0212", "Total Due This Invoice: $14,500.00"]
  draft: false                         # true: DRAFT watermark and banner on every page
  fields: {issuer: hollis_crane, bill_to: [...], meta: [[Invoice No., 25-0212], ...], lines: [...]}
```

- **`key_phrases`** are never wrapped across lines. After rendering, each one must appear
  verbatim in the canonical text that `qoe.pdf_text.extract_pdf_pages` and
  `canonicalize_page_text` produce. Use them for anything an AI quote should hit.
- **Invoice totals** must equal the sum of the `supports` rows. Set `check_total: false` to
  skip that check.
- **Row references.** `{num:KEY}`, `{amount:KEY}`, `{date:KEY}`, `{mdy:KEY}`, `{memo:KEY}`,
  and `{counterparty:KEY}` in any field are filled from the generated row. This is how a
  proof of claim lists invoice numbers drawn from a sequence.
- **Every page** carries the footer "SYNTHETIC — generated for QoE Evidence Review testing".
  Emails end with it.

Template fields (all optional unless noted):

| Template | Fields |
| --- | --- |
| `invoice` | `issuer` (party), `title`, `bill_to_label`, `bill_to` (party or lines), `meta` ([label, value] rows), `intro` (paragraphs), `columns` (`{qty, rate, amount, description}` labels), **`lines`** (`{description, amount}` or `{description, qty, rate}`), `less` (`{label, amount}` deductions), `total_label`, `notes` (body items), `remit`, `remit_label`, `terms` |
| `letter` | `issuer`, `delivery`, `date`, `to`, `re` (string or lines), `salutation`, `body`, `closing`, `signatures`, `countersign: {heading, signatures}`, `enclosures`, `cc` |
| `agreement` | `issuer`, `title`, `subtitle`, `preamble`, `recitals`, `recitals_close`, `sections: [{heading, number?, body}]`, `witness`, `signatures`, `exhibits: [{title, body}]` |
| `memo` | `issuer`, `title`, `to`, `from`, `cc`, `date`, `re`, `body` |
| `form` | `issuer`, `title`, `subtitle`, `meta`, `body` |
| `email` | `from`, `to`, `cc`, `date`, `subject`, `attachments`, `body` (text). It writes `.txt` with From / To / Date / Subject headers. |

**Body items** are a list. Each item is one of:

- a string, which becomes a wrapped paragraph;
- `{heading: …}`, `{kv: [[label, value], …]}`, `{bullets: […]}`, `{numbered: […]}`,
  `{lines: […]}`, `{spacer: 12}`, or `{signatures: […]}`;
- `{table: {columns: [{title, align, width}], rows: [[…]], total: […]}}`. The column without
  a `width` takes the remaining width and wraps.

**Signatures** take `{party, name, title, signed, date}`. A signed block shows `/s/ Name`.
An unsigned block shows blank `By:` and `Date:` lines. Letter signatures use a closing style.

## Monthly P&L and the management schedule

`monthly_pl` defaults to the QBO "Profit and Loss by Month" layout, with sections Income,
Cost of Goods Sold, Expenses, Other Income, and Other Expenses, total rows, and Gross Profit,
Net Operating Income, and Net Income. You can rename sections and map source types to them.
`month_format` is `mon_yyyy`, `month_yyyy`, `iso`, or `date`. The P&L is built from the
ledger, plus top-side entries, plus any months missing from the GL.

`schedule` writes the SPEC §3.6 workbook: title rows, a header row (Ref, Adjustment,
Category, Description, GL Account(s), Support Ref, then each period label), the rows from
net income through reported EBITDA, the adjustments, the total, and adjusted EBITDA.

- **`basis: pl`** (the default) computes net income, interest, taxes, D&A, and reported
  EBITDA from management's P&L. Top-side entries therefore flow into reported EBITDA.
  `basis: gl` uses the GL instead.
- **`claim_keys`** checks a pass-through claim. The claimed amount in each of
  `claim_periods` (all periods by default) must equal the debit-positive sum of those rows.

## Ground truth

```yaml
ground_truth:
  authored_by: …
  notes: …
  adjustments:                                  # one per schedule ref, same ids
    - adj_id: M-10
      case_type: OUT_OF_PERIOD
      treatment: REVISE                         # ACCEPT | REVISE | REJECT | REQUEST_INFO
      amounts: {FY2024: -42000, FY2025: 42000, TTM Jun-26: 0}   # none for REQUEST_INFO
      supporting: [apex_trueup]                 # keys or globs -> supporting_gl_rows
      related: []                               # -> related_gl_rows
      recoveries: []                            # rows whose removal is part of the amount; reported as related
      period_moves: [{keys: [apex_trueup], service_start: "2024-07", service_end: "2024-12"}]
      supporting_docs: [apex_invoice]           # document ids -> filenames
      expected_flags: [OUT_OF_PERIOD]
      question_topics: [...]
      rationale: >-
        …
      ambiguity: low
      reviewer_note: "Must not fire: …"
  diligence_items: [...]                        # same shape; items not on management's schedule (e.g. D-1)
```

For each period `p`, every non-REQUEST_INFO amount is verified against the GL:

```
amount[p] = Σ supporting rows in p (dp) + Σ recovery rows in p (dp) − Σ moved rows × (service months in p / service months)
```

Here dp is the debit-positive amount. Removing an expense row adds back `+dp`, and removing
an unadjusted gain adds `dp < 0`. Set `verify_amounts: false` only when an amount is a
judgment that the GL cannot reproduce.

`gl_ebitda` is computed from the generated GL using SPEC §6, and `diligence_adjusted_ebitda`
is `gl_ebitda` plus every non-REQUEST_INFO amount, including diligence items. You never type
either value.

## Worked example

A complete minimal deal: one recurring revenue stream, one expense, three planted legal
bills, an insurance recovery, one invoice, and one adjustment.

```yaml
deal_id: tiny_plumbing
split: dev
seed: 7
package_date: "2025-07-10"
company: {name: "Tiny Plumbing Co, LLC", industry: Plumbing}
periods:
  - {label: FY2024, start: "2024-01", end: "2024-12"}
  - {label: TTM Jun-25, start: "2024-07", end: "2025-06"}
data_start: "2024-01"
data_end: "2025-06"
gl_format: qbo_gl_csv
sequences: {ar: 1001}
accounts:
  - {number: "4000", name: Service Revenue, type: Income}
  - {number: "6000", name: Wages, type: Expense}
  - {number: "6400", name: Legal Fees, type: Expense}
  - {number: "8000", name: Other Income, type: Other Income}
background:
  - id: sales
    account: "4000"
    txn_type: invoice
    schedule: {count: [3, 5]}
    amount: {monthly: 90000, growth: 0.05, noise: 0.05}
    counterparties: [{name: Acme Property Mgmt, weight: 2}, Birch Street HOA]
    memo: "Plumbing service – job {job}"
    num: {sequence: ar}
  - id: wages
    account: "6000"
    txn_type: payroll
    schedule: {days: [15, -1], adjust: prior}
    amount: {monthly: 25000, noise: 0.01}
    memo: "Payroll – PPE {mdy}"
planted:
  - key: "legal_{yyyy}{mm}"
    repeat: {start: "2024-10", end: "2024-12", days: [10]}
    account: "6400"
    counterparty: Lawson Legal LLP
    num: "LL-{yy}{mm}"
    amount: 5000
    memo: "Lawsuit defense – {mon} {yyyy}"
  - {key: recovery, date: "2025-02-14", account: "8000", txn_type: deposit,
     counterparty: Test Mutual Insurance, amount: -4000, memo: "Insurance reimbursement – legal costs"}
parties:
  lawson: {name: Lawson Legal LLP, address: [1 Main Street, "Tampa, FL 33602"]}
documents:
  - id: inv
    filename: 1.1 Lawson Invoice LL-2410.pdf
    folder: 01 Legal
    template: invoice
    supports: [legal_202410]
    key_phrases: ["Invoice No.: LL-2410", "Total Due: $5,000.00"]
    fields:
      issuer: lawson
      bill_to: ["Tiny Plumbing Co, LLC"]
      meta: [[Invoice No., LL-2410], [Invoice Date, "October 10, 2024"]]
      lines: [{description: Defense of lawsuit, qty: 10, rate: 500}]
schedule:
  adjustments:
    - {ref: A-1, title: Lawsuit defense, category: Non-recurring, accounts: "6400", support: DR 1.1,
       amounts: {FY2024: 15000, TTM Jun-25: 15000}, claim_keys: ["legal_2024*"]}
ground_truth:
  authored_by: example
  adjustments:
    - adj_id: A-1
      case_type: RECOVERY_OFFSET
      treatment: REVISE
      amounts: {FY2024: 15000, TTM Jun-25: 11000}   # 15,000 of fees less the 4,000 recovery in TTM
      supporting: ["legal_2024*"]
      recoveries: [recovery]
      supporting_docs: [inv]
      expected_flags: [OFFSETTING_RECOVERY]
      rationale: Defense costs are non-recurring; net the unadjusted insurance recovery.
```

`tests/qoe/test_generator.py` builds this deal, in a slightly larger form, in all three GL
formats.

## Checks the generator performs

- Every row key is unique, and every date falls within `data_start..data_end`.
- Every account exists and is a P&L account.
- No field contains a newline, so a CSV source row is its physical line number.
- There are no unplanned duplicate groups.
- Each Xero contact name is free of `" - "`.
- Every key glob matches at least one row.
- Every `claim_keys` claim ties to its rows.
- Every answer-key amount ties under the rule above, and no row is both supporting and
  related.
- Invoice totals equal the rows they support.
- Every key phrase survives PDF text extraction verbatim, and every page carries the
  footer.
- `deal.yaml` validates as `qoe.schemas.DealMeta`, and `ground_truth.json` validates as
  `GroundTruth`.
