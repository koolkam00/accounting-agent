# How this repo works

This document is the full map: what the system does, how a PDF becomes a decision, and **every file** in git.

Read this before running Qwen. Local tests do not call the GPU. They replay ground truth from `expected.json`.

Jump to **[§8 Every file in the repo](#8-every-file-in-the-repo)** for the complete inventory (root, `app/`, scripts, all 50 fixture cases, reports).

1. [What this is](#1-what-this-is)
2. [How a request flows](#2-how-a-request-flows)
3. [The objects that move through the system](#3-the-objects-that-move-through-the-system)
4. [Policy](#4-policy-what-match-means)
5. [Exception codes](#5-exception-codes)
6. [Synthetic dataset](#6-synthetic-dataset)
7. [Text extraction](#7-text-extraction-no-ocr)
8. [Every file in the repo](#8-every-file-in-the-repo)
9. [How the files call each other](#9-how-the-files-call-each-other)
10. [What “ready for Qwen” means](#10-what-ready-for-qwen-means)
11. [What this repo is not](#11-what-this-repo-is-not)

---

## 1. What this is

An accounts-payable **three-way match** prototype.

1. A vendor sends an **invoice PDF**.
2. The system extracts fields (vendor, PO number, lines, totals).
3. Python looks up the **purchase order** and **goods receipts** in a fake ERP (SQLite).
4. Python checks: does the invoice match the PO and what was received?
5. Outcome is only one of:
   - `READY_FOR_DRAFT` — propose a balanced journal and (optionally) create a draft bill
   - `HUMAN_REVIEW` — stop; list exception codes

The LLM is not the AP clerk. It only turns invoice text into JSON. Matching, money math, policy, idempotency, and the decision are Python.

In production the invoice would still be a PDF/email. The PO and receipt would already live in NetSuite / QuickBooks / SAP. Here they are JSON files loaded into SQLite so tests do not need a real ERP.

---

## 2. How a request flows

```
invoice.pdf
    │
    ▼
[INGEST]     pypdf text layer → canonicalize whitespace → hash
    │          if no text at all → OCR_REQUIRED → HUMAN_REVIEW (no LLM)
    ▼
[EXTRACT]    LLM (or mock / preseeded expected.json) → ExtractedInvoice JSON
    │
    ▼
[VALIDATE]   required fields, evidence quotes must appear in canonical text,
             line math (qty × price, subtotal + tax + freight)
    │
    ▼
[LOOKUP]     ERPAdapter.get_purchase_order(po_number)
             ERPAdapter.get_receipts(po_id)
             vendor by PO, then vendor_id, then name
             duplicate check (vendor_id + invoice_number)
             idempotency key
    │
    ▼
[MATCH]      invoice vs PO vs receipts vs policy  (app/matching.py)
    │
    ▼
[PROPOSE_JOURNAL]  only if no exceptions yet
                   Dr expense GL from PO lines, Cr AP
    │
    ▼
[CREATE_DRAFT_OR_REVIEW]
    evaluate mode     → return WorkflowResult, do not write a draft
    create_draft mode → if READY_FOR_DRAFT, persist draft + processed row
```

Two evaluation modes:

| Mode | What happens |
| --- | --- |
| `evaluate` | Run the pipeline; do not create a draft. Used by tests and accuracy eval. |
| `create_draft` | If `READY_FOR_DRAFT`, write a draft bill id and remember the idempotency key. Re-running the same key returns the cached result. |

Two LLM paths:

| Path | Who extracts | Used by |
| --- | --- | --- |
| Mock / preseed | `expected.json` extraction (or regex parser on upload) | `make test`, `make evaluate-accuracy` (no `--live`), Streamlit, `run_case.py` |
| Live GPU | Qwen3-8B via vLLM, JSON schema | `evaluate_accuracy.py --live`, `evaluate_determinism.py --live` |

`run_case_dir` in `app/pipeline.py` **preseeds** extraction from `expected.json` whenever you run a fixture directory through the mock client. That is why local accuracy stays 50/50 even after the PDFs were made harder: the matcher is scored, not Qwen.

---

## 3. The objects that move through the system

Defined in `app/schemas.py` (Pydantic v2, `extra="forbid"`).

| Object | Role |
| --- | --- |
| `ExtractedInvoice` | LLM output: vendor, invoice number/date, PO, currency, line items, totals, payment terms, ambiguities, evidence quotes |
| `InvoiceLineItem` | SKU, qty, unit price, line total, optional evidence span |
| `EvidenceSpan` | `{quote, page}` — `quote` must be an exact substring of canonical PDF text |
| `PurchaseOrder` / `POLine` | ERP PO: vendor, status, lines with GL accounts |
| `Receipt` / `ReceiptLine` | ERP goods receipt: qty received per SKU |
| `Vendor` | vendor_id, name, active flag |
| `PolicyConfig` | tolerances loaded from `config/policy.yaml` |
| `ControlCheck` | one named pass/fail from validation or matching |
| `ProposedJournal` / `JournalLine` | Dr/Cr lines; `balanced` must be true to draft |
| `WorkflowResult` | the whole outcome: decision, exceptions, extraction, journal, idempotency key |
| `AuditManifest` | hashes of PDF, canonical text, prompt, schema, policy, model revision |

Money and quantities are **decimal strings** (`"12.50"`), never floats.

---

## 4. Policy (what “match” means)

`config/policy.yaml`:

- Currency must be USD.
- Unit price may differ from the PO by at most `max(0.5% of PO price, $0.01)`.
- Invoice qty may not exceed PO qty or received qty (tolerance `0`).
- Invoice total must match line sum ± `$0.01`.
- Any non-zero tax → `HUMAN_REVIEW`.
- Missing or ambiguous required fields → `HUMAN_REVIEW`.

Python enforces this. The model cannot override it.

---

## 5. Exception codes

From `app/schemas.py` `EXCEPTION_CODES`. Any non-empty set forces `HUMAN_REVIEW`.

| Code | Typical cause |
| --- | --- |
| `OCR_REQUIRED` | Image-only PDF; no text layer |
| `MISSING_REQUIRED_FIELD` / `MISSING_INVOICE_NUMBER` | Extraction incomplete |
| `AMBIGUOUS_FIELD` | Model (or fixture) flagged two possible values |
| `EVIDENCE_VALIDATION_FAILED` | Quote not found in canonical text |
| `INVOICE_MATH_ERROR` | qty × price or totals do not add up |
| `PO_NOT_FOUND` | Invoice PO id not in ERP, or PO not OPEN |
| `VENDOR_MISMATCH` / `VENDOR_INACTIVE` | Invoice vendor ≠ PO vendor |
| `DUPLICATE_INVOICE` | Same vendor + invoice number already processed |
| `CURRENCY_MISMATCH` | Invoice / PO / policy currency disagree |
| `SKU_NOT_FOUND` | Invoice SKU not on the PO |
| `PRICE_VARIANCE` | Unit price outside tolerance |
| `QUANTITY_EXCEEDS_PO` / `QUANTITY_EXCEEDS_RECEIPT` | Billed more than ordered or received |
| `NONZERO_TAX_REVIEW` | Tax ≠ 0 |
| `UNBALANCED_JOURNAL` | Debits ≠ credits |

---

## 6. Synthetic dataset

Generator: `scripts/generate_cases.py`. Seed `20260812`. Command: `make generate-data`.

50 cases:

| Split | Cases | Purpose |
| --- | --- | --- |
| `tests/fixtures/development/` | `case_001`–`case_030` | Iterate here |
| `tests/fixtures/holdout/` | `case_031`–`case_050` | Score last; do not hand-edit `expected.json` |

Each case directory:

| File | What it is |
| --- | --- |
| `invoice.pdf` | Fake vendor invoice (ReportLab, `invariant=1` so bytes are reproducible) |
| `po.json` | Seed for the SQLite PO |
| `receipt.json` | Seed for the SQLite receipt |
| `expected.json` | Ground truth: scenario, decision, exception codes, perfect extraction + evidence quotes |

`tests/fixtures/dataset_manifest.json` lists SHA-256 of every generated file.

### Scenarios (50 total)

| Count | Scenario | Expected decision |
| --- | --- | --- |
| 15 | `exact_match` | `READY_FOR_DRAFT` |
| 5 | `price_within` | `READY_FOR_DRAFT` (tiny price delta inside tolerance) |
| 5 | `price_over` | `HUMAN_REVIEW` / `PRICE_VARIANCE` |
| 5 | `qty_exceeds_receipt` | `HUMAN_REVIEW` / `QUANTITY_EXCEEDS_RECEIPT` |
| 5 | `duplicate` | `HUMAN_REVIEW` / `DUPLICATE_INVOICE` (DB pre-seeded) |
| 5 | `missing_po` | `HUMAN_REVIEW` / `PO_NOT_FOUND` (PDF points at `PO-MISSING-N`) |
| 4 | `math_error` | `HUMAN_REVIEW` / `INVOICE_MATH_ERROR` (corrupted total) |
| 3 | `vendor_mismatch` | `HUMAN_REVIEW` / `VENDOR_MISMATCH` |
| 3 | `missing_ambiguous` | `HUMAN_REVIEW` / missing invoice number or two vendor headers |

PO and receipt JSON are **unchanged** when you only restyle the PDF. Matching still uses the same ERP rows.

### How the PDFs are drawn (current harder set)

The GPU never sees pixels. `pypdf` `extract_text(extraction_mode="plain")` reads the text layer in **draw order**.

Five layouts rotate by case index. None of them use the old `LINE|sku|…` machine block.

| Layout | What the text looks like |
| --- | --- |
| `layout_classic` | `Bill No.`, `Customer #`, `$1,234.50`, tax described as exempt |
| `layout_boxed` | `Document` / `Our order`, qty as `10 ea`, amount column before qty |
| `layout_two_column` | Right column drawn first → PO and remit-to appear **before** vendor |
| `layout_modern` | Page 1 = lines; page 2 = totals (`--- PAGE 2 ---` in canonical text) |
| `layout_compact` | Courier, `Ref`, qty `10.000`, `$1234.50` |

Every layout also plants distractors: remit-to Harbor Street Holdings, ship-from Westfield, barcode `INV-000000`, blanket `PO-9999`, coupon `$8,888.00`.

`expected.json` still stores **normalized** fields (`invoice_total: "250.00"`, ISO dates). Evidence quotes store the **source form** (`"$250.00"`, page 2 for modern totals). After drawing, the generator extracts the PDF with the same `pypdf` path and binds quote page numbers so they cannot drift.

Image-only / scanned PDFs are **not** in this dataset. Those would trip `OCR_REQUIRED` and never call the GPU.

---

## 7. Text extraction (no OCR)

`app/pdf_text.py` → `app/canonicalize.py` → LLM.

1. `PdfReader` on the bytes.
2. Each page: `extract_text(extraction_mode="plain")`.
3. If every page is empty → `ocr_required=True` → pipeline stops.
4. Canonicalize: Unicode NFC, `\n` newlines, collapse space runs, squeeze blank lines.
5. Join pages with `\n\n--- PAGE {n} ---\n\n`.
6. Hash the canonical string. That hash goes into the audit manifest.

Live Qwen is prompted with `Invoice text:\n\n{canonical_text}` plus a JSON schema. It does not receive the PDF.

---

## 8. Every file in the repo

Git tracks these paths. This section names **all of them**. Ignored (not in git): `.venv/`, `.env`, `*.db`, `__pycache__/`, pytest/mypy/ruff caches, `.DS_Store`, extra `reports/*.json` that are not in the allow-list below.

---

### 8.1 Root

| File | What it does |
| --- | --- |
| `README.md` | Front door: product one-liner, GPU results (easy invoices), harder-PDF note, local/GPU how-to, pins, link to this doc |
| `Makefile` | Targets: `setup`, `generate-data`, `init-db`, `test`, `run-local`, `run-ui`, `evaluate-accuracy`, `evaluate-determinism`, `capture-env`, `report` |
| `pyproject.toml` | Package `accounting-agent` 0.1.0; Python `>=3.12,<3.13`; deps (pydantic, openai, pypdf, reportlab, pytest, httpx, pyyaml, sqlalchemy, pandas, streamlit, python-dotenv); hatch wheel of `app/`; pytest `pythonpath = ["."]` |
| `uv.lock` | Exact resolved versions for `uv sync`. Do not hand-edit |
| `.env.example` | Template: `VLLM_BASE_URL`, `VLLM_API_KEY=not-a-real-key`, `MODEL_NAME`, `MODEL_REVISION`, docker image/digest, `VLLM_BATCH_INVARIANT`, `DATABASE_URL`, `AP_ACCOUNT=2000`, `PROMPT_VERSION`, `SCHEMA_VERSION`, `POLICY_PATH`, `TEMPERATURE=0`, `TOP_P=1`, `SEED=42`. Copy to `.env` |
| `.gitignore` | Ignores `.venv`, bytecode, `.env`, `*.db`, caches, `*.log`, `.python-version`, Streamlit secrets. Ignores `reports/*.json` **except** the allow-listed GPU artifacts listed in §8.8 |

---

### 8.2 `app/` — runtime code

| File | What it does |
| --- | --- |
| `app/__init__.py` | Empty. Makes `app` a Python package |
| `app/adapters/__init__.py` | Empty. Makes `app.adapters` a package |
| `app/adapters/base.py` | Abstract `ERPAdapter`: `get_vendor`, `get_purchase_order`, `get_receipts`, `check_duplicate_invoice`, `create_draft_bill`, `attach_source_document`, `get_previous_result`, `record_processed`. A real NetSuite/QBO adapter would implement this |
| `app/adapters/local_erp.py` | SQLite `LocalERPAdapter`. Ordered SELECTs for determinism. Draft ids are `DRAFT-` + first 12 of the idempotency key. `attach_source_document` is a no-op (does not store PDF bytes). Extra helpers: `get_vendor_by_name`, `seed_duplicate` |
| `app/schemas.py` | Pydantic v2 models (`extra="forbid"`): `ExtractedInvoice`, line items, evidence, PO/receipt/vendor, policy, journal, `WorkflowResult`, `AuditManifest`, enums `WorkflowDecision` / `PipelineState`, list `EXCEPTION_CODES` |
| `app/settings.py` | `load_dotenv()` then `Settings` from env. `get_settings()` is lru-cached. Resolves `prompt_path` to `prompts/{PROMPT_VERSION}.txt` |
| `app/pdf_text.py` | `extract_pdf_text`: `pypdf.PdfReader`, `extract_text(extraction_mode="plain")` per page. `ocr_required` if no page has text |
| `app/canonicalize.py` | `canonicalize_page_text` (NFC, newlines, collapse spaces), `join_pages` with `--- PAGE n ---`, SHA-256 of bytes/text, `CanonicalDocument` |
| `app/llm_client.py` | `INVOICE_JSON_SCHEMA` for vLLM structured output. `MockLLMClient` returns fixture `expected.json` extraction, else `parse_synthetic_invoice_text`. `VLLMLLMClient` calls OpenAI-compatible vLLM with the prompt + json_schema, thinking off |
| `app/validation.py` | Required fields, ambiguity → exceptions, evidence quotes must be substrings of canonical text, Decimal line/total math, normalize qty/money strings, `decision_from_exceptions` |
| `app/matching.py` | `match_invoice`: duplicate, PO exists/OPEN, vendor active + name/id vs PO, currency, nonzero tax, per-SKU price tolerance, qty vs PO, qty vs receipts |
| `app/journal.py` | `propose_journal`: map invoice SKUs to PO `gl_account`, debit those accounts (freight onto first GL), credit `AP_ACCOUNT`. Unbalanced → `UNBALANCED_JOURNAL` |
| `app/idempotency.py` | `compute_idempotency_key` = SHA-256 of `pdf\|po\|receipts\|prompt\|schema\|policy\|model_revision`. Plus `hash_text` / `hash_bytes` |
| `app/audit.py` | `AuditLog.emit` appends `{event_type, case_id, detail}` in memory; optionally writes `AuditEventRow` if a session factory was passed |
| `app/pipeline.py` | `Pipeline.run` is the state machine (§2). `load_policy` reads YAML. `build_manifest` hashes PDF/text/prompt/schema/policy. `run_case_dir` loads a fixture folder and **preseeds** extraction from `expected.json` when using the mock client |
| `app/database.py` | SQLAlchemy models: `VendorRow`, `PurchaseOrderRow`, `POLineRow`, `ReceiptRow`, `ReceiptLineRow`, `WorkflowRunRow`, `ExtractedInvoiceRow`, `ControlCheckRow`, `JournalDraftRow`, `ProcessedDocumentRow` (unique idempotency key), `AuditEventRow`, `DuplicateSeedRow`. `init_db` / `reset_db`. SQLite gets `PRAGMA foreign_keys=ON` |
| `app/ui.py` | Streamlit app (`make run-ui`). Sidebar: env + evaluate/create_draft. Tab 1: pick fixture, show PO/receipt JSON, run. Tab 2: upload PDF. Result: decision, exceptions, extracted fields, evidence, match checks, journal, audit hashes. Uses `MockLLMClient` only |

---

### 8.3 `config/` and `prompts/`

| File | What it does |
| --- | --- |
| `config/policy.yaml` | `currency: USD`; unit-price tolerance `0.005` (0.5%) with floor `$0.01`; qty tolerance `0`; invoice-total tolerance `$0.01`; `nonzero_tax_requires_review: true`; missing/ambiguous fields → `HUMAN_REVIEW` |
| `prompts/invoice_extraction_v1.txt` | System prompt: extract JSON only, do not invent, null + `ambiguities` if unsure, evidence quotes exact, amounts two decimal places. Hashed into the idempotency key |

---

### 8.4 `scripts/`

| File | What it does |
| --- | --- |
| `scripts/generate_cases.py` | Seed `20260812`. Builds 50 cases: 5 vendors, 8 SKUs, 5 PDF layouts (classic/boxed/two-column/modern/compact), 9 scenarios. Writes PDF + `po.json` + `receipt.json` + `expected.json`. Re-extracts each PDF to bind evidence page numbers. Writes `tests/fixtures/dataset_manifest.json` |
| `scripts/initialize_database.py` | `--reset` drops tables. Inserts V001–V005, then every case’s PO, PO lines, receipt, receipt lines. If `expected.json` has `already_processed`, inserts `DuplicateSeedRow` |
| `scripts/run_case.py` | CLI: `--case case_001 --mode evaluate\|create_draft`. Finds the fixture, mock LLM, prints `WorkflowResult` JSON |
| `scripts/evaluate_accuracy.py` | For each case, run pipeline, compare decision + exception codes to `expected.json`. Default: mock + preseed. `--live`: `VLLMLLMClient`, no preseed. Writes `reports/accuracy_mock.json` or `reports/accuracy_gpu.json` |
| `scripts/evaluate_determinism.py` | Always: local PDF/canonical hash check. `--live`: repeat extracts at concurrency 1/8/32; hash `ExtractedInvoice` JSON with volatile keys stripped. Writes `reports/determinism.json` and optional `determinism_records_*.jsonl` |
| `scripts/capture_environment.py` | Writes `reports/environment.json`: UTC time, Python, platform, package versions, git commit/dirty, model pins |
| `scripts/build_report.py` | Reads accuracy/determinism/env/billing JSON and writes `reports/final_report.md` |

---

### 8.5 `tests/` (code)

| File | What it does |
| --- | --- |
| `tests/test_pipeline.py` | `test_pipeline_exact_match_ready` (case_001), `test_pipeline_price_over_review` (case_021), `test_pipeline_duplicate` (case_031), `test_idempotent_create_draft`, then loops all development and all holdout cases vs `expected.json` |
| `tests/test_matching.py` | No PDFs. `test_exact_ready`, `test_price_within_tolerance`, `test_price_over`, `test_qty_exceeds_receipt`, `test_duplicate`, `test_po_missing`, `test_nonzero_tax`, `test_exceptions_sorted` |
| `tests/test_validation.py` | `test_valid_invoice`, `test_missing_required`, `test_evidence_must_match`, `test_math_error`, `test_ambiguous` |
| `tests/test_journal.py` | `test_balanced_journal` (debits sorted, AP credit), `test_unbalanced_triggers_review` |
| `tests/test_idempotency.py` | `test_key_stable`, `test_key_changes_with_inputs` |
| `tests/test_canonicalization.py` | NFC/newlines, whitespace policy, page separators, hash stability |
| `tests/test_pdf_reproducibility.py` | Same case PDF generated twice → same SHA-256; all 5 layouts invariant; generated text has no `LINE|` / `Vendor:` machine block and includes distractors; every fixture evidence quote appears in canonical text |

---

### 8.6 Fixture file types (four files per case)

Every `tests/fixtures/{development,holdout}/case_NNN/` directory contains **exactly these four files**:

| File | What it is |
| --- | --- |
| `invoice.pdf` | ReportLab invoice, byte-reproducible (`invariant=1`). Text layer only. Layout rotates by case index (see table below) |
| `po.json` | Purchase order seed: `po_id`, vendor, currency, `status: OPEN`, lines (`sku`, qty, unit_price, `gl_account`). Loaded into SQLite by `initialize_database.py` |
| `receipt.json` | Goods receipt seed: `receipt_id`, `po_id`, lines (`sku`, `quantity_received`). Loaded into SQLite |
| `expected.json` | Ground truth: `case_id`, `scenario`, `decision`, `exception_codes`, `layout`, `po_id`, `extraction` (perfect `ExtractedInvoice` including evidence quotes), optional `already_processed` / `duplicate_of` for duplicate cases |

Plus:

| File | What it is |
| --- | --- |
| `tests/fixtures/dataset_manifest.json` | `seed`, `case_count: 50`, split lists, scenario counts, SHA-256 of every generated PDF/JSON |

#### All 50 cases

Layout rotates `classic → boxed → two_column → modern → compact`. `modern` is the two-page layout.

**Development (`tests/fixtures/development/`)** — iterate here.

| Dir | Scenario | Decision | Layout | Exceptions | ERP PO |
| --- | --- | --- | --- | --- | --- |
| `case_001/` | exact_match | READY_FOR_DRAFT | classic | — | PO-1001 |
| `case_002/` | exact_match | READY_FOR_DRAFT | boxed | — | PO-1002 |
| `case_003/` | exact_match | READY_FOR_DRAFT | two_column | — | PO-1003 |
| `case_004/` | exact_match | READY_FOR_DRAFT | modern | — | PO-1004 |
| `case_005/` | exact_match | READY_FOR_DRAFT | compact | — | PO-1005 |
| `case_006/` | exact_match | READY_FOR_DRAFT | classic | — | PO-1006 |
| `case_007/` | exact_match | READY_FOR_DRAFT | boxed | — | PO-1007 |
| `case_008/` | exact_match | READY_FOR_DRAFT | two_column | — | PO-1008 |
| `case_009/` | exact_match | READY_FOR_DRAFT | modern | — | PO-1009 |
| `case_010/` | exact_match | READY_FOR_DRAFT | compact | — | PO-1010 |
| `case_011/` | exact_match | READY_FOR_DRAFT | classic | — | PO-1011 |
| `case_012/` | exact_match | READY_FOR_DRAFT | boxed | — | PO-1012 |
| `case_013/` | exact_match | READY_FOR_DRAFT | two_column | — | PO-1013 |
| `case_014/` | exact_match | READY_FOR_DRAFT | modern | — | PO-1014 |
| `case_015/` | exact_match | READY_FOR_DRAFT | compact | — | PO-1015 |
| `case_016/` | price_within | READY_FOR_DRAFT | classic | — | PO-1016 |
| `case_017/` | price_within | READY_FOR_DRAFT | boxed | — | PO-1017 |
| `case_018/` | price_within | READY_FOR_DRAFT | two_column | — | PO-1018 |
| `case_019/` | price_within | READY_FOR_DRAFT | modern | — | PO-1019 |
| `case_020/` | price_within | READY_FOR_DRAFT | compact | — | PO-1020 |
| `case_021/` | price_over | HUMAN_REVIEW | classic | PRICE_VARIANCE | PO-1021 |
| `case_022/` | price_over | HUMAN_REVIEW | boxed | PRICE_VARIANCE | PO-1022 |
| `case_023/` | price_over | HUMAN_REVIEW | two_column | PRICE_VARIANCE | PO-1023 |
| `case_024/` | price_over | HUMAN_REVIEW | modern | PRICE_VARIANCE | PO-1024 |
| `case_025/` | price_over | HUMAN_REVIEW | compact | PRICE_VARIANCE | PO-1025 |
| `case_026/` | qty_exceeds_receipt | HUMAN_REVIEW | classic | QUANTITY_EXCEEDS_RECEIPT | PO-1026 |
| `case_027/` | qty_exceeds_receipt | HUMAN_REVIEW | boxed | QUANTITY_EXCEEDS_RECEIPT | PO-1027 |
| `case_028/` | qty_exceeds_receipt | HUMAN_REVIEW | two_column | QUANTITY_EXCEEDS_RECEIPT | PO-1028 |
| `case_029/` | qty_exceeds_receipt | HUMAN_REVIEW | modern | QUANTITY_EXCEEDS_RECEIPT | PO-1029 |
| `case_030/` | qty_exceeds_receipt | HUMAN_REVIEW | compact | QUANTITY_EXCEEDS_RECEIPT | PO-1030 |

**Holdout (`tests/fixtures/holdout/`)** — score last; do not hand-edit `expected.json`.

| Dir | Scenario | Decision | Layout | Exceptions | ERP PO |
| --- | --- | --- | --- | --- | --- |
| `case_031/` | duplicate | HUMAN_REVIEW | classic | DUPLICATE_INVOICE | PO-1031 |
| `case_032/` | duplicate | HUMAN_REVIEW | boxed | DUPLICATE_INVOICE | PO-1032 |
| `case_033/` | duplicate | HUMAN_REVIEW | two_column | DUPLICATE_INVOICE | PO-1033 |
| `case_034/` | duplicate | HUMAN_REVIEW | modern | DUPLICATE_INVOICE | PO-1034 |
| `case_035/` | duplicate | HUMAN_REVIEW | compact | DUPLICATE_INVOICE | PO-1035 |
| `case_036/` | missing_po | HUMAN_REVIEW | classic | PO_NOT_FOUND | PO-1036 (PDF cites `PO-MISSING-36`) |
| `case_037/` | missing_po | HUMAN_REVIEW | boxed | PO_NOT_FOUND | PO-1037 (PDF cites `PO-MISSING-37`) |
| `case_038/` | missing_po | HUMAN_REVIEW | two_column | PO_NOT_FOUND | PO-1038 (PDF cites `PO-MISSING-38`) |
| `case_039/` | missing_po | HUMAN_REVIEW | modern | PO_NOT_FOUND | PO-1039 (PDF cites `PO-MISSING-39`) |
| `case_040/` | missing_po | HUMAN_REVIEW | compact | PO_NOT_FOUND | PO-1040 (PDF cites `PO-MISSING-40`) |
| `case_041/` | math_error | HUMAN_REVIEW | classic | INVOICE_MATH_ERROR | PO-1041 |
| `case_042/` | math_error | HUMAN_REVIEW | boxed | INVOICE_MATH_ERROR | PO-1042 |
| `case_043/` | math_error | HUMAN_REVIEW | two_column | INVOICE_MATH_ERROR | PO-1043 |
| `case_044/` | math_error | HUMAN_REVIEW | modern | INVOICE_MATH_ERROR | PO-1044 |
| `case_045/` | vendor_mismatch | HUMAN_REVIEW | compact | VENDOR_MISMATCH | PO-1045 |
| `case_046/` | vendor_mismatch | HUMAN_REVIEW | classic | VENDOR_MISMATCH | PO-1046 |
| `case_047/` | vendor_mismatch | HUMAN_REVIEW | boxed | VENDOR_MISMATCH | PO-1047 |
| `case_048/` | missing_ambiguous | HUMAN_REVIEW | two_column | MISSING_INVOICE_NUMBER, MISSING_REQUIRED_FIELD | PO-1048 |
| `case_049/` | missing_ambiguous | HUMAN_REVIEW | modern | AMBIGUOUS_FIELD (letterhead Other Corp) | PO-1049 |
| `case_050/` | missing_ambiguous | HUMAN_REVIEW | compact | MISSING_INVOICE_NUMBER, MISSING_REQUIRED_FIELD | PO-1050 |

That is 50 × 4 = 200 fixture files, plus `dataset_manifest.json`.

---

### 8.7 `deployment/`

| File | What it does |
| --- | --- |
| `deployment/start_vllm.sh` | Pulls pinned image digest, `docker run --gpus all` Qwen3-8B at the pinned revision, `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar backend, port 8000 |
| `deployment/runpod-template.md` | Same pins for a RunPod H100; client `chat.completions` shape; do not leave the pod idle |
| `deployment/Dockerfile` | CPU image: `python:3.12-slim`, `uv sync --frozen`, copies `app`, `config`, `prompts`, `scripts`. Default CMD is `run_case.py --help`. Not the GPU server |
| `deployment/docker-compose.yml` | Service `accounting-agent` builds that Dockerfile, mounts fixtures read-only and `reports/`. vLLM service is commented out |

Do not silently change model revision or image digest. See `docs/technical_decisions.md`.

---

### 8.8 `docs/`

| File | What it does |
| --- | --- |
| `docs/how_it_works.md` | This file: system map + every-file catalog |
| `docs/technical_decisions.md` | Why 3.12 / uv / Decimal / two-way decision space; GPU pins and sources; why temp=0 is not enough; architecture split; what the 2026-08-13 GPU run did and did not prove |
| `docs/SECRET_SWEEP.md` | Pre-publish checklist: never commit `.env`, tokens, `*.log`, `*.db`, Streamlit secrets; `rg` scan commands; which reports are safe |

---

### 8.9 `reports/`

These are **measured artifacts**, mostly from the 2026-08-13 GPU run on the **old labeled invoices**. Re-running eval scripts overwrites some of them. `.gitignore` keeps most new `reports/*.json` out of git except the allow-listed ones.

| File | What it does |
| --- | --- |
| `reports/final_report.md` | Human writeup: pins, 50/50 accuracy, determinism, spend, caveats. Produced by `scripts/build_report.py` |
| `reports/results.csv` | One row per case for the live GPU accuracy run: split, scenario, expected vs got decision/codes, pass, llm=`VLLMLLMClient` |
| `reports/accuracy_gpu.json` | Structured live-Qwen accuracy (dev + holdout). `--live` eval writes this |
| `reports/accuracy_mock.json` | Same shape for `MockLLMClient` (preseeded). Default `evaluate_accuracy.py` writes this |
| `reports/determinism.json` | Local PDF/canonical stability plus GPU hash matrices (conc 1/8/32) and cross-machine comparison (PCIe US-KS-2 vs SXM AP-IN-1) |
| `reports/determinism_r0_pcie_usks2.json` | First-machine (PCIe) determinism snapshot used as the cross-machine baseline |
| `reports/determinism_records_r0.jsonl` | Per-extract records from restart_id `r0` (PCIe). One JSON object per line |
| `reports/determinism_records_r1.jsonl` | Per-extract records from restart_id `r1` (SXM) |
| `reports/environment.json` | Python/platform/packages/git commit + GPU pins + spend/hours copied in after the GPU run |
| `reports/gpu_runtime.json` | Which determinism cells ran, pod ids, datacenter, skipped cells (negative control, pod restart, full 9000) |
| `reports/billing.json` | RunPod billing: ~$38.34, ~13.0 GPU hours, pod ids `p7tdoz42gtf92g` and `n56so1rkgs0ckh` |
| `reports/runpod_quote.md` | Pre-rental quote notes (written when spend was still $0). Historical planning doc |
| `reports/failures/README.md` | Says there were no accuracy failure artifacts in the last GPU eval. Failed `--live` cases would land in this folder |

`reports/.gitkeep` is mentioned in `.gitignore` but is not a tracked file. Extra JSON from a new local `make report` stays untracked unless you force-add it.

---

## 9. How the files call each other

```
make generate-data
    scripts/generate_cases.py
        ReportLab → invoice.pdf
        po.json, receipt.json, expected.json
        pypdf + canonicalize → bind evidence pages

make init-db
    scripts/initialize_database.py
        app/database.py tables
        load vendors + every po.json / receipt.json
        duplicate_seeds from expected.json

make test / make run-local / Streamlit fixture tab
    app/pipeline.run_case_dir
        reads invoice.pdf + expected.json
        PRESEEDS ExtractedInvoice from expected.json
        Pipeline.run
            pdf_text → canonicalize
            skip LLM extract (preseeded)
            validation → local_erp lookup → matching → journal
        compare decision to expected.json

evaluate_accuracy.py --live
    Pipeline.run WITHOUT preseed
        pdf_text → canonicalize
        VLLMLLMClient.extract_invoice(canonical_text)
            prompts/invoice_extraction_v1.txt
            JSON schema from llm_client.py
            vLLM at VLLM_BASE_URL
        then the same Python control plane
        score decision + exception codes vs expected.json
```

Idempotency key (`app/idempotency.py`) mixes:

`pdf_sha256 | po_id | receipt_snapshot_sha256 | prompt_sha256 | schema_version | policy_sha256 | model_revision`

Same invoice + same ERP snapshot + same prompt/policy/model → same key → `create_draft` returns the stored draft instead of creating a second one.

---

## 10. What “ready for Qwen” means

You already have:

- Harder PDFs on disk
- Ground truth in `expected.json`
- A Python matcher that is independently tested
- A live eval script that **does not** cheat with `expected.json`

You do not have a new GPU accuracy number. The published 50/50 is for the old labeled invoices.

To measure the harder set:

1. Start pinned vLLM (`deployment/start_vllm.sh` or RunPod template).
2. Set `VLLM_BASE_URL` in `.env`.
3. `uv run python scripts/evaluate_accuracy.py --live`
4. Optionally `uv run python scripts/evaluate_determinism.py --live`

Do not tune on holdout. Do not edit holdout `expected.json` after seeing failures.

---

## 11. What this repo is not

- Not a production ERP integration (no QuickBooks/NetSuite adapter beyond the protocol in `adapters/base.py`).
- Not an OCR product. Scanned PDFs stop at ingest.
- Not a vision model. Qwen reads text, not pixels.
- Not a general AP agent. Decision space is two values; policy is one YAML file; vendors are five fictional companies.
