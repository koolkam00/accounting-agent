# Final Report — Accounting Agent (GPU / vLLM)

Generated (UTC): 2026-08-13T14:14:50.950601+00:00
Source commit: `fca77e6141193e146fa1931afc5d46552b4938ad`

## Scope

- Deterministic Python control plane for three-way match.
- Streamlit UI available via `make run-ui` (`app/ui.py`).
- **GPU / vLLM evaluation EXECUTED** on pinned Qwen3-8B + vLLM image (see Pins).
- **GPU spend (from billing artifact, not an estimate unless noted): 31.021492425119504**
- **GPU hours: 10.6816**

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

### GPU determinism matrix — REDUCED

| Dimension | Status | Unique hashes | n | Notes |
|-----------|--------|---------------|---|-------|
| same_request / same_request_repeatability | EXECUTED | 50 | 250 | cases_with_>1_hash=0;  |
| batch_invariance / vllm_batch_invariant_token_stability_conc8 | EXECUTED | 50 | 250 | cases_with_>1_hash=0; Server has VLLM_BATCH_INVARIANT=1. Request order shuffled to mix batch positions. |
| negative_control / batch_invariance_disabled_negative_control | NOT_EXECUTED |  |  | NOT RUN. Accuracy 50/50 and reduced determinism both passed, but negative control requires restart with VLLM_BATCH_INVARIANT=0. Prefer finishing and stopping the GPU over a second server configuration. |
| restart / pod_restart_invariance | NOT_EXECUTED |  |  | NOT RUN. Reduced matrix (conc=1 and conc=8, 50 cases x 5 reps) was clean (0 cases with >1 hash). Same-pod restart skipped to stop GPU billing; restart would cost another ~4 min cold start. Only restart_id=r0 records exist. |
| cross_machine / cross_machine_invariance | NOT_EXECUTED |  |  | Single RunPod H100 PCIe machine (US-KS-2); no second host rented. |
| structured_outputs / vllm_json_schema_xgrammar_stability | EXECUTED |  | 500 |  |
| nonthinking / qwen3_nonthinking_extraction_repeatability | EXECUTED | 50 |  | Client and server set chat_template_kwargs.enable_thinking=false; hashed extraction JSON. |
| batch_invariance / vllm_batch_invariant_token_stability_conc32 | NOT_EXECUTED |  |  | NOT RUN. Optional conc=32 skipped: evaluate_determinism.py always re-runs 250 sequential conc=1 jobs first (~60 min). Reduced conc=8 was already clean. Prefer finishing and stopping the GPU. |

## Environment / spend

- Captured in `reports/environment.json` (source_commit=`fca77e6141193e146fa1931afc5d46552b4938ad`)
- Platform: `Linux-6.12.94+-x86_64-with-glibc2.41`
- GPU run flag: `True`
- GPU hours: `10.6816`
- GPU spend USD: `31.021492425119504`
- Pod id(s): `['p7tdoz42gtf92g']`

## Honest limitations

- Accuracy is live Qwen3-8B extraction + Python match/decision, not MockLLM. Holdout was not tuned.
- Determinism hashes exclude timestamps/request ids; they hash canonical ExtractedInvoice JSON.
- Negative control (VLLM_BATCH_INVARIANT off) is only claimed if that section status is EXECUTED.
- Cross-machine invariance was not rented as a second host unless listed EXECUTED.
- Fictional vendors only; not production ERP-integrated.
- API keys are not written into this report.

- Pod `p7tdoz42gtf92g` was STOPPED then DELETED; `list-pods` returned empty.
- Billing from RunPod get-billing is through 2026-08-13T14:00:00Z ($31.021492425119504 total; GPU $30.869872053619474 + disk $0.15162037150003016). The 14:00–15:00 UTC bucket was not yet in the API after delete (~14:14 UTC stop). No estimate was added for that unbilled tail.
- Optional conc=32, negative-control (VLLM_BATCH_INVARIANT=0), same-pod restart, and full 9000-request matrix were NOT executed (see determinism table). Prefer stop GPU after clean reduced matrix.

## Artifacts

- `reports/final_report.md` (this file)
- `reports/results.csv`
- `reports/environment.json`
- `reports/accuracy_mock.json`
- `reports/accuracy_gpu.json` (if live)
- `reports/determinism.json`
- `reports/failures/`
- `reports/billing.json` (if captured)
