# How this repo works

This document is the full map: what the system does, how a PDF becomes a decision, and what every file is for.

Read this before running Qwen. Local tests do not call the GPU. They replay ground truth from `expected.json`.

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

## 8. File catalog

### Root

| File | Purpose |
| --- | --- |
| `README.md` | Entry point: what it is, measured results, how to run |
| `LICENSE` | MIT |
| `Makefile` | Shortcuts: setup, generate-data, init-db, test, UI, eval, report |
| `pyproject.toml` | Package metadata, Python 3.12 pin, dependencies |
| `uv.lock` | Locked dependency versions |
| `.env.example` | Env template (fake API key). Copy to `.env` (gitignored) |
| `.gitignore` | Drops `.venv`, `.env`, `*.db`, caches, most generated report JSON |

### `app/` — the product

| File | Purpose |
| --- | --- |
| `app/__init__.py` | Empty package marker |
| `app/schemas.py` | All Pydantic models and the exception-code list |
| `app/settings.py` | Loads `.env`: vLLM URL, model pins, DB URL, AP account, prompt/policy paths, sampling |
| `app/pdf_text.py` | pypdf text-layer extraction; OCR flag |
| `app/canonicalize.py` | Stable text normalization + SHA-256 helpers |
| `app/llm_client.py` | `LLMClient` ABC; `MockLLMClient`; `VLLMLLMClient`; JSON schema; fallback regex parser for synthetic text |
| `app/validation.py` | Required fields, evidence substring check, Decimal arithmetic, normalize amounts |
| `app/matching.py` | Three-way match vs PO, receipts, vendor, policy |
| `app/journal.py` | Aggregate invoice lines onto PO GL accounts; credit AP `2000` |
| `app/idempotency.py` | SHA-256 of PDF hash + PO + receipts + prompt + schema + policy + model revision |
| `app/audit.py` | In-memory (and optional DB) event log: STATE, OCR_REQUIRED, COMPLETE, … |
| `app/pipeline.py` | State machine that calls everything above; `run_case_dir` for fixtures |
| `app/database.py` | SQLAlchemy tables: vendors, POs, receipts, drafts, processed docs, duplicates, audit |
| `app/ui.py` | Streamlit demo: pick a fixture or upload a PDF, run mock pipeline |
| `app/adapters/base.py` | `ERPAdapter` protocol (what a real NetSuite adapter would implement) |
| `app/adapters/local_erp.py` | SQLite implementation of that protocol |

### `config/` and `prompts/`

| File | Purpose |
| --- | --- |
| `config/policy.yaml` | Match tolerances (see §4) |
| `prompts/invoice_extraction_v1.txt` | System prompt for Qwen: extract JSON, do not invent, evidence must be exact quotes |

Prompt path is `prompts/{PROMPT_VERSION}.txt`. Changing the prompt changes the prompt hash and therefore the idempotency key.

### `scripts/` — generate, seed, evaluate

| File | Purpose |
| --- | --- |
| `scripts/generate_cases.py` | Build 50 PDFs + JSON + `dataset_manifest.json` |
| `scripts/initialize_database.py` | Load vendors, every `po.json` / `receipt.json`, duplicate seeds into SQLite |
| `scripts/run_case.py` | Run one fixture (`--case case_001`) through the mock pipeline; print JSON |
| `scripts/evaluate_accuracy.py` | Score decisions vs `expected.json`. Default mock (preseeded). `--live` calls vLLM and does **not** preseed |
| `scripts/evaluate_determinism.py` | Local: PDF/canonical hash stability. `--live`: repeat extracts at concurrency 1/8/32 |
| `scripts/capture_environment.py` | Write `reports/environment.json` (Python, packages, git commit, pins) |
| `scripts/build_report.py` | Assemble `reports/final_report.md` from accuracy/determinism/env JSON |

### `tests/`

| File | Purpose |
| --- | --- |
| `tests/test_pipeline.py` | Exact match drafts; price-over reviews; duplicates; idempotent re-run; all 50 fixture decisions |
| `tests/test_matching.py` | Unit tests for price/qty/tax/PO rules without PDFs |
| `tests/test_validation.py` | Required fields, evidence, math, ambiguity |
| `tests/test_journal.py` | Balanced journal shape |
| `tests/test_idempotency.py` | Same inputs → same key; different PDF hash → different key |
| `tests/test_canonicalization.py` | Whitespace / hash stability |
| `tests/test_pdf_reproducibility.py` | Regenerating a PDF is byte-identical; no `LINE|` machine block; evidence quotes exist in canonical text |
| `tests/fixtures/development/case_*/` | 30 labeled training/dev cases |
| `tests/fixtures/holdout/case_*/` | 20 holdout cases |
| `tests/fixtures/dataset_manifest.json` | File hashes for the generated dataset |

### `deployment/`

| File | Purpose |
| --- | --- |
| `deployment/start_vllm.sh` | `docker run` the **pinned** vLLM image + Qwen3-8B + batch invariance + xgrammar |
| `deployment/runpod-template.md` | How to rent an H100 with those same pins |
| `deployment/Dockerfile` | CPU app image (not the GPU server) |
| `deployment/docker-compose.yml` | App service; vLLM service is commented (needs a GPU) |

Do not silently change model revision or image digest. See `docs/technical_decisions.md`.

### `docs/`

| File | Purpose |
| --- | --- |
| `docs/how_it_works.md` | This file |
| `docs/technical_decisions.md` | Why Python 3.12, why temp=0 is not enough, GPU pins, architecture split |
| `docs/SECRET_SWEEP.md` | Checklist so `.env` / API keys never land in git or reports |

### `reports/`

Artifacts from the 2026-08-13 GPU run (easy labeled PDFs) plus local mock eval. Regenerated by `make report` / eval scripts.

| File | Purpose |
| --- | --- |
| `reports/final_report.md` | Human writeup of measured results |
| `reports/results.csv` | Per-case accuracy rows |
| `reports/accuracy_gpu.json` / `accuracy_mock.json` | Structured accuracy |
| `reports/determinism.json` and `determinism_*.json(l)` | Hash-stability matrices |
| `reports/environment.json` | Pins, packages, git commit |
| `reports/gpu_runtime.json` / `billing.json` | Runtime and spend |
| `reports/runpod_quote.md` | Cost notes |
| `reports/failures/README.md` | Placeholder for live-eval failures |

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
