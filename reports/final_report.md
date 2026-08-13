# Final Report — Accounting Agent (Local / Non-GPU Dispatch)

Generated (UTC): 2026-08-13T01:57:08.429861+00:00
Source commit: `bf38836aa6ff12b75fa3c93d8d8c95327fcb091b`

## Scope

- Implemented deterministic Python control plane for three-way match.
- LLM extraction mocked locally via `MockLLMClient`.
- Streamlit UI available via `make run-ui` (`app/ui.py`).
- **GPU / vLLM evaluation NOT executed** in this dispatch.
- **GPU spend: $0**.

## Pins (for upcoming GPU phase)

- Model: `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218`
- Image: `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`
- `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar structured outputs
- Sampling: temperature=0, top_p=1, seed=42, n=1

## Dataset

- 50 synthetic cases (seed 20260812), development 001–030, holdout 031–050
- See `tests/fixtures/dataset_manifest.json`

## Accuracy (Mock LLM)

- **development**: 30/30 (accuracy=1.0)
- **holdout**: 20/20 (accuracy=1.0)
- Per-case CSV: `reports/results.csv` (50 rows)
- Failure artifacts: `reports/failures/` (0 files)

## Determinism

### Local (executed)

- `local_pdf_canonical_stability`: pass=True

### GPU determinism matrix — NOT EXECUTED YET

| Dimension | Status | Notes |
|-----------|--------|-------|
| Same-request repeatability | NOT EXECUTED | Needs pinned vLLM on H100 |
| Batch invariance under load | NOT EXECUTED | Needs `VLLM_BATCH_INVARIANT=1` |
| Restart invariance | NOT EXECUTED | Pod stop/start not run |
| Cross-machine invariance | NOT EXECUTED | Single local host only |

- SKIP `same_request_repeatability`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; would repeat identical extraction requests N times
- SKIP `vllm_batch_invariant_token_stability`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; requires VLLM_BATCH_INVARIANT=1 on pinned image v0.27.1
- SKIP `pod_restart_invariance`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; would stop/start vLLM and compare tokens
- SKIP `cross_machine_invariance`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; single local host only in this dispatch
- SKIP `vllm_json_schema_xgrammar_stability`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; xgrammar + json_schema pending live verification
- SKIP `qwen3_nonthinking_extraction_repeatability`: GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval; model revision b968826d9c46dd6066d109eabc6255188de91218 pending

## Environment

- Captured in `reports/environment.json` (source_commit=`bf38836aa6ff12b75fa3c93d8d8c95327fcb091b`)
- Platform: `Linux-6.12.94+-x86_64-with-glibc2.41`
- GPU run flag: `False`

## Honest limitations

- Token-level extraction determinism under load is **unverified** until the pinned vLLM image is exercised on suitable GPU hardware.
- GPU determinism matrix (same-request / batch invariance / restart / cross-machine) is **explicitly not executed** — zero GPU spend.
- Local path uses MockLLMClient; real Qwen3-8B extraction quality is pending GPU quote approval.
- Fictional vendors only; not production ERP-integrated.

## Artifacts

- `reports/final_report.md` (this file)
- `reports/results.csv`
- `reports/environment.json`
- `reports/accuracy_mock.json`
- `reports/determinism.json`
- `reports/failures/`
- `reports/runpod_quote.md` (prepared; do not rent until approved)
