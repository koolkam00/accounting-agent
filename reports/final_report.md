# Final Report — Accounting Agent (GPU / vLLM)

Generated (UTC): 2026-08-13T16:50:00.482292+00:00
Source commit: `c25abe0b342179b994cd3b1cd0bdc856c8244f16`

## Scope

- Deterministic Python control plane for three-way match.
- Streamlit UI available via `make run-ui` (`app/ui.py`).
- **GPU / vLLM evaluation EXECUTED** on pinned Qwen3-8B + vLLM image (see Pins).
- **GPU spend (from billing artifact, not an estimate unless noted): 38.34293123660609**
- **GPU hours: 13.0179**

## Pins

- Model: `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218`
- Served name: `ap-extractor-v1`
- Image: `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`
- `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar structured outputs
- Sampling: temperature=0, top_p=1, seed=42, n=1

## Dataset

- 50 synthetic cases (seed 20260812), development 001–030, holdout 031–050
- See `tests/fixtures/dataset_manifest.json`
- Holdout was not used for prompt/policy tuning.

## Accuracy

- **MockLLM development**: 30/30 (accuracy=1.0)
- **MockLLM holdout**: 20/20 (accuracy=1.0)
- **Live Qwen3-8B development**: 30/30 (accuracy=1.0) schema_valid=30 false_READY_FOR_DRAFT=0
- **Live Qwen3-8B holdout**: 20/20 (accuracy=1.0) schema_valid=20 false_READY_FOR_DRAFT=0
- Live LLM: `VLLMLLMClient`; preseeded_from_expected=False
- Per-case CSV: `reports/results.csv` (50 rows)
- Failure artifacts: `reports/failures/` (0 files)

## Determinism

### Local (executed)

- `local_pdf_canonical_stability`: pass=True

### GPU determinism matrix — MEDIUM

| Dimension | Status | Unique hashes | n | Notes |
|-----------|--------|---------------|---|-------|
| same_request / same_request_repeatability | EXECUTED | 50 | 500 | cases_with_>1_hash=0;  |
| batch_invariance / vllm_batch_invariant_token_stability_conc8 | EXECUTED | 50 | 500 | cases_with_>1_hash=0; Server has VLLM_BATCH_INVARIANT=1. Request order shuffled to mix batch positions. |
| batch_invariance / vllm_batch_invariant_token_stability_conc32 | EXECUTED | 50 | 500 | cases_with_>1_hash=0; Server has VLLM_BATCH_INVARIANT=1. Request order shuffled to mix batch positions. |
| negative_control / batch_invariance_disabled_negative_control | NOT_EXECUTED |  |  | NOT RUN. Disabling VLLM_BATCH_INVARIANT requires a pod restart and a second server configuration. This run kept VLLM_BATCH_INVARIANT=1. Do not interpret batch-invariant uniqueness as a negative-control result. |
| restart / pod_restart_invariance | NOT_EXECUTED |  |  | NOT RUN. Pod restart was skipped to stay inside the ~3h MEDIUM window and remaining GPU budget. restart_id=r1 labels this process only; no stop/start of vLLM was performed. Do not treat PARTIAL as a restart result. |
| cross_machine / cross_machine_invariance | EXECUTED |  |  | Hashes matched on all 50 cases vs prior PCIe/US-KS-2 reduced run. Prior run used 5 reps at conc 1 and 8; this run used 10 reps at conc 1, 8, and 32. |
| structured_outputs / vllm_json_schema_xgrammar_stability | EXECUTED |  | 1500 |  |
| nonthinking / qwen3_nonthinking_extraction_repeatability | EXECUTED | 50 |  | Client and server set chat_template_kwargs.enable_thinking=false; hashed extraction JSON. |

## Environment / spend

- Captured in `reports/environment.json` (source_commit=`c25abe0b342179b994cd3b1cd0bdc856c8244f16`)
- Platform: `Linux-6.12.94+-x86_64-with-glibc2.41`
- GPU run flag: `True`
- GPU hours: `13.0179`
- GPU spend USD: `38.34293123660609`
- Pod id(s): `['p7tdoz42gtf92g', 'n56so1rkgs0ckh']`

## Honest limitations

- Accuracy is live Qwen3-8B extraction + Python match/decision, not MockLLM. Holdout was not tuned.
- Determinism hashes exclude timestamps/request ids; they hash canonical ExtractedInvoice JSON.
- Negative control (VLLM_BATCH_INVARIANT off) is only claimed if that section status is EXECUTED.
- Cross-machine invariance was not rented as a second host unless listed EXECUTED.
- Fictional vendors only; not production ERP-integrated.
- API keys are not written into this report.
- MEDIUM matrix is 50 cases × 10 reps × conc {1,8,32} = 1500 extracts (+ 3 warmup), not the full 9000-extract matrix.
- Accuracy was not rerun (already 50/50 live). Negative-control and pod-restart were skipped.
- Billing totals are API-billed through 16:00Z; the ~16:00–16:48Z tail after this H100 SXM pod stopped is not included.

## Artifacts

- `reports/final_report.md` (this file)
- `reports/results.csv`
- `reports/environment.json`
- `reports/accuracy_mock.json`
- `reports/accuracy_gpu.json` (if live)
- `reports/determinism.json`
- `reports/failures/`
- `reports/billing.json` (if captured)
