# Experiment protocol — temperature × document difficulty

Status: **design locked, not executed**. No GPU rented for this grid.

Primary citation: He, Horace and Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference", Connectionism, Sep 2025. doi:10.64434/tml.20250910

## Claim

Temperature-0 structured extraction is still load-sensitive unless kernels are batch-invariant. Raising temperature and document difficulty both increase unique extraction hashes, and they interact. Accuracy (schema-valid, field match, `READY_FOR_DRAFT`) is scored separately from determinism.

## Model (locked)

| Item | Pin |
| --- | --- |
| Model | `openai/gpt-oss-120b` |
| Why | Current open-weight; on vLLM's batch-invariance **tested** list; fits 1× H100 80GB |
| Not used | Qwen3-8B (dated). Qwen3.5 / 3.6 GDN (vLLM rejects `VLLM_BATCH_INVARIANT=1`). DeepSeek-V3.1 (frontier, 8-GPU, out of scope for this grid). |
| Image | Current `vllm/vllm-openai` that serves gpt-oss-120b (`>=0.10.0`). **Pin digest at launch.** Do not reuse `v0.27.1`. |
| Serve | 1× H100, `--tensor-parallel-size 1`, `--gpu-memory-utilization 0.95`, `--max-num-batched-tokens 1024` (H100 TP1 OOM otherwise), `--max-model-len 8192` |
| Env | `VLLM_BATCH_INVARIANT=1` (and `=0` only on the negative-control cells) |
| Structured out | Chat Completions `response_format` json_schema + xgrammar. Hash **only** the extracted invoice JSON, never reasoning traces. |
| Reasoning | Pin `reasoning_effort` to `low` (or off if the served API allows). Do not leave default high-reasoning on: it blows tokens, cost, and the hash. |
| Sampling | `seed=42`, `top_p=1`, `n=1`. Temperature is a **factor**. |
| Client | Same Python control plane. LLM extracts JSON only. |

Revision SHA of `openai/gpt-oss-120b` is recorded at launch in `reports/environment.json`. Do not silently retag.

## Factors

| Factor | Levels | Notes |
| --- | --- | --- |
| Temperature | `0, 0.3, 0.7, 1.0` | `0` is the TML greedy setting |
| Difficulty | `easy, medium, hard` | Text-layer PDFs only. **No OCR.** |
| Concurrency | `1, 8` | Load / batch-size (TML mechanism) |
| Batch invariance | `on, off` | `off` is the required negative control |

Difficulty is generated, not labeled after the fact:

- **easy** — one page, clean table, every field explicit, matching PO/receipt.
- **medium** — current 50-case mix (seed `20260812`): mismatches, tax, duplicates, inactive vendor.
- **hard** — still ReportLab text-layer, byte-reproducible: struck-through amounts, extra fee lines, wrapped tables, missing PO, multi-page, odd spacing. Image-only / scanned PDFs are **out**: `pypdf` would set `OCR_REQUIRED` and skip the LLM.

20 cases per difficulty. 10 of the medium set are holdout (never used to tweak prompt/policy). Same schema and matcher for all.

## Matrix

```
20 cases × 3 difficulties × 4 temps × 5 reps × 2 conc × 2 invariance
= 4,800 measured extracts
```

Plus 3 warmup extracts after each server start (invariance on vs off are two server configs → two starts).

Do **not** add a third model on this grid. Optional later: one cheap slice (temp `{0, 0.7}` × `{easy, hard}` × conc `{1, 8}` × invariance on) on a second BIC-tested model.

## Metrics

**Accuracy** (per temp × difficulty, first successful extract per case, conc=1, invariance on):

- schema-valid rate
- field exact-match vs gold
- decision accuracy (`READY_FOR_DRAFT` / `HUMAN_REVIEW`)
- false `READY_FOR_DRAFT` count (must stay 0 on gold-review cases)

**Determinism** (per temp × difficulty × conc × invariance):

- unique extraction hashes per case (canonical `ExtractedInvoice` JSON)
- cases with more than one hash
- pairwise disagreement rate
- first diverging token index when hashes split (TML-style)

Report invariance-off cells as the negative control. Do not claim the flag “caused” stability unless those cells actually split.

## What we will not do

- Real OCR / vision models
- Production QuickBooks / NetSuite
- Changing the Python matcher mid-grid
- Speculative decoding, LoRA, quantization beyond whatever MXFP4 is native to gpt-oss-120b
- The old 9,000-extract Qwen3-8B matrix (already reported separately)

## Paper

Workshop / arXiv note first. Working title:

> Temperature-0 is not determinism: invoice extraction accuracy and hash stability under load, temperature, and document difficulty

Related work: He et al. 2025; vLLM batch-invariance docs; LLM-42 (2026); STED (Amazon, 2025); ExtractBench / LLMStructBench.

## GPU quote (estimate, not a live price)

- Hardware: 1× H100 80GB Secure (~$3.29/hr last live quote; **re-check at deploy**)
- Wall clock: ~12–16 h including two server starts and weight download (120B is slower than Qwen3-8B)
- Estimated compute: **$40–55** plus leftover disk
- Prior Qwen spend already used most of the old $50 cap. **This grid needs a new approved cap (suggest $80, auto-stop 16 h).**

Do not create a pod until that cap is approved in chat.

## Execution order

1. Generate easy/hard PDF packs (same ReportLab invariant path, new seed suffix).
2. Extend `evaluate_accuracy.py` / `evaluate_determinism.py` for `--temperature` and `--difficulty`.
3. Quote live H100, get spend approval.
4. Serve gpt-oss-120b with invariance **on**, run the on-cells.
5. Restart with invariance **off**, run the off-cells.
6. Build `reports/temp_difficulty_report.md` + CSV. Honest SKIP if a cell fails.
7. Draft the paper from that report, not the other way around.


## Implementation notes (client / fixtures)

- Fixtures: `tests/fixtures/difficulty/{easy,medium,hard}/` — 20 cases each, last 10 holdout. Legacy 50-case seed `20260812` fixtures are unchanged.
- Generate: `python scripts/generate_cases.py --difficulty {easy,medium,hard,all}` (or `make generate-difficulty`).
- Client Harmony payload: `extra_body={"reasoning_effort": "low"}` (top-level). `chat_template_kwargs.reasoning_effort` is ignored by vLLM's Harmony path; we do not send it.
- Qwen3 dense path is unchanged and mutually exclusive: `extra_body.chat_template_kwargs.enable_thinking=false` only when `MODEL_NAME` looks like Qwen3 (not 3.5/3.6 GDN).
- Eval: `evaluate_accuracy.py` / `evaluate_determinism.py` accept `--temperature --difficulty --reps --conc --live --label --negative-control`. Reports record temperature, difficulty, invariance, model, and extraction hashes.
- Hard PDFs are ReportLab text-layer (strikethrough, extra fees, wrapped tables, multi-page, odd spacing). Image-only PDFs still set `OCR_REQUIRED` and skip the LLM.
