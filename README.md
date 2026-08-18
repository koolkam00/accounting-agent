# Deterministic AP three-way match

Prototype accounts-payable agent: a vendor invoice PDF goes in, a `READY_FOR_DRAFT` or `HUMAN_REVIEW` decision comes out, with a balanced journal proposal and an audit trail.

The LLM only extracts JSON. Python does every match, Decimal calculation, and decision. That split is the product, not an implementation detail.

**Full walkthrough:** [`docs/how_it_works.md`](docs/how_it_works.md) (Markdown) · [`docs/Accounting_Agent_Guide.docx`](docs/Accounting_Agent_Guide.docx) (Word: folders, every `.py` file, GPU setup, how to read outputs).

## What we measured (2026-08-13)

Live **Qwen3-8B** extraction on pinned vLLM, then the Python control plane. That run used the **original labeled invoices** (`Vendor:`, `LINE|sku|…` machine block).

| Check | Result |
| --- | --- |
| Live accuracy (30 dev + 20 holdout) | **50/50** correct, schema-valid JSON, **0** false `READY_FOR_DRAFT` |
| Same invoice, 10 repeats, concurrency 1 | **500/500**, one hash per case |
| Same, concurrency 8 | **500/500**, same hashes |
| Same, concurrency 32 | **500/500**, same hashes |
| Cross-machine | Those hashes matched a **second H100** (PCIe, US-KS-2 vs SXM, AP-IN-1) on all 50 cases |

1,500 measured extracts + 3 warmup. Synthetic dataset only (seed `20260812`). Full writeup: [`reports/final_report.md`](reports/final_report.md). Per-case CSV: [`reports/results.csv`](reports/results.csv).

### Harder invoices (not yet re-measured on GPU)

Fixtures were regenerated as **messy text-layer PDFs**: no `LINE|` block, inconsistent labels, remit-to / barcode distractors, two-column reading-order traps, multi-page totals, mixed money and date formats. The GPU never sees the page; it sees `pypdf` text. Local mock tests still pass because they preseed from `expected.json`. Live Qwen accuracy on this dataset has **not** been re-run.

### What the GPU run does **not** prove

We ran with `VLLM_BATCH_INVARIANT=1` and hashes matched. We did **not** rerun with the flag off.

That missing run is the **negative control**. It is the experiment that should *break*: same invoices, same GPU, batch-invariance disabled, and you would expect some cases to grow a second hash once concurrency hits 8 or 32. Without it, a skeptic can say the workload was just easy and would have been stable anyway. We showed repeatability, not that the flag caused it.

Also not run: a pod restart (process-lifetime invariance) and the original 9,000-extract matrix (50 × 20 × {1,8,32} × 3 restarts).

## Architecture

```
INGEST → EXTRACT → VALIDATE → LOOKUP → MATCH → PROPOSE_JOURNAL → CREATE_DRAFT_OR_REVIEW
```

Decisions are only `READY_FOR_DRAFT` or `HUMAN_REVIEW`. Policy lives in [`config/policy.yaml`](config/policy.yaml) (unit-price tolerance `max(0.5% of PO price, $0.01)`; any non-zero tax goes to review).

Local ERP and the accounting sandbox are SQLite. No production QuickBooks/NetSuite. Purchase orders and receipts in the repo are JSON **seeds** for that SQLite ERP, not how a real AP system stores them.

## Reproduce locally (no GPU)

```bash
uv python install 3.12
uv sync --python 3.12
cp .env.example .env

make generate-data         # 50 synthetic cases, byte-reproducible PDFs (seed 20260812)
make generate-difficulty   # easy/medium/hard packs, 20 cases each
make init-db
make test            # mock LLM
make evaluate-accuracy
make report
make run-ui          # Streamlit demo
```

Local tests use `MockLLMClient`. They do not call gpt-oss or Qwen.

Live GPU accuracy (after a pinned vLLM pod is up):

```bash
uv run python scripts/evaluate_accuracy.py --live
```

## GPU pins (do not silently change)

**Current default (temperature × difficulty experiment, not yet executed):**

- Model: `openai/gpt-oss-120b` (revision pin-at-launch)
- Image: `vllm/vllm-openai` **>= 0.10.0** (do not reuse `v0.27.1`; pin digest at launch)
- Serve: 1× H100, `--tp 1`, `--gpu-memory-utilization 0.95`, `--max-num-batched-tokens 1024`, `--max-model-len 8192`
- `VLLM_BATCH_INVARIANT=1` (and `=0` only for the negative-control start)
- Harmony: client `extra_body.reasoning_effort=low`; parse `message.content` only
- Sampling: seed 42, top_p 1, n 1; temperature is a factor (`0, 0.3, 0.7, 1.0`)

**Prior Qwen3-8B pin (still supported):** `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218` on `v0.27.1`. Client sends `chat_template_kwargs.enable_thinking=false` only when `MODEL_NAME` looks like Qwen3 (not 3.5 / 3.6 GDN).

See [`docs/technical_decisions.md`](docs/technical_decisions.md), [`docs/experiment_temp_difficulty.md`](docs/experiment_temp_difficulty.md), and [`deployment/`](deployment/).

## Secret sweep

Before you fork this or paste logs elsewhere, run [`docs/SECRET_SWEEP.md`](docs/SECRET_SWEEP.md). `.env` is gitignored. Live vLLM/RunPod keys never belong in this repo.

## Security posture

Findings and fixes: [`docs/security_review.md`](docs/security_review.md). Two defaults matter when you run this: the Streamlit demo is unauthenticated and binds loopback only, and `deployment/start_vllm.sh` refuses to serve unless `VLLM_API_KEY` is a real secret (`VLLM_ALLOW_NO_AUTH=1` overrides) and publishes the port on `VLLM_BIND_HOST`, default `127.0.0.1`.
