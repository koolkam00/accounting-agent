# Deterministic AP three-way match

Prototype accounts-payable agent: a vendor invoice PDF goes in, a `READY_FOR_DRAFT` or `HUMAN_REVIEW` decision comes out, with a balanced journal proposal and an audit trail.

The LLM only extracts JSON. Python does every match, Decimal calculation, and decision. That split is the product, not an implementation detail.

## What we measured (2026-08-13)

Live **Qwen3-8B** extraction on pinned vLLM, then the Python control plane:

| Check | Result |
| --- | --- |
| Live accuracy (30 dev + 20 holdout) | **50/50** correct, schema-valid JSON, **0** false `READY_FOR_DRAFT` |
| Same invoice, 10 repeats, concurrency 1 | **500/500**, one hash per case |
| Same, concurrency 8 | **500/500**, same hashes |
| Same, concurrency 32 | **500/500**, same hashes |
| Cross-machine | Those hashes matched a **second H100** (PCIe, US-KS-2 vs SXM, AP-IN-1) on all 50 cases |

1,500 measured extracts + 3 warmup. Synthetic dataset only (seed `20260812`). Full writeup: [`reports/final_report.md`](reports/final_report.md). Per-case CSV: [`reports/results.csv`](reports/results.csv).

### What this does **not** prove

We ran with `VLLM_BATCH_INVARIANT=1` and hashes matched. We did **not** rerun with the flag off.

That missing run is the **negative control**. It is the experiment that should *break*: same invoices, same GPU, batch-invariance disabled, and you would expect some cases to grow a second hash once concurrency hits 8 or 32. Without it, a skeptic can say the workload was just easy and would have been stable anyway. We showed repeatability, not that the flag caused it.

Also not run: a pod restart (process-lifetime invariance) and the original 9,000-extract matrix (50 × 20 × {1,8,32} × 3 restarts).

## Architecture

```
INGEST → EXTRACT → VALIDATE → LOOKUP → MATCH → PROPOSE_JOURNAL → CREATE_DRAFT_OR_REVIEW
```

Decisions are only `READY_FOR_DRAFT` or `HUMAN_REVIEW`. Policy lives in [`config/policy.yaml`](config/policy.yaml) (unit-price tolerance `max(0.5% of PO price, $0.01)`; any non-zero tax goes to review).

Local ERP and the accounting sandbox are SQLite. No production QuickBooks/NetSuite.

## Reproduce locally (no GPU)

```bash
uv python install 3.12
uv sync --python 3.12
cp .env.example .env

make generate-data   # 50 synthetic cases, byte-reproducible PDFs
make init-db
make test            # mock LLM
make evaluate-accuracy
make report
make run-ui          # Streamlit demo
```

Local tests use `MockLLMClient`. They do not call Qwen.

## GPU pins (do not silently change)

- Model: `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218`
- Image: `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`
- `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar structured outputs (`disable_any_whitespace`)
- Sampling: temperature 0, top_p 1, seed 42, n 1

See [`docs/technical_decisions.md`](docs/technical_decisions.md) and [`deployment/`](deployment/).

## Secret sweep

Before you fork this or paste logs elsewhere, run [`docs/SECRET_SWEEP.md`](docs/SECRET_SWEEP.md). `.env` is gitignored. Live vLLM/RunPod keys never belong in this repo.

## License

MIT. Evaluation prototype, fictional vendors, not production ERP-integrated.
