# Final Report — Accounting Agent (Local / Non-GPU Dispatch)

Generated (UTC): 2026-08-13T01:52:05.458154+00:00

## Scope

- Implemented deterministic Python control plane for three-way match.
- LLM extraction mocked locally via `MockLLMClient`.
- **GPU / vLLM evaluation not run** in this dispatch (no GPU rented).

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

## Determinism

- Local `local_pdf_canonical_stability`: pass=True

### GPU not yet run

- SKIP `vllm_batch_invariant_token_stability`: GPU not rented in this dispatch; requires VLLM_BATCH_INVARIANT=1 on pinned image v0.27.1
- SKIP `vllm_json_schema_xgrammar_stability`: GPU not rented; structured-outputs backend xgrammar pending live verification
- SKIP `qwen3_nonthinking_extraction_repeatability`: GPU not rented; model revision b968826d9c46dd6066d109eabc6255188de91218 pending

## Honest limitations

- Token-level extraction determinism under load is **unverified** until the pinned vLLM image is exercised on suitable GPU hardware.
- Streamlit UI is a minimal stub.
- Fictional vendors only; not production ERP-integrated.
