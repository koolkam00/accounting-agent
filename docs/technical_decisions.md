# Technical Decisions

Fetched/verified reference notes: 2026-08-13. Local (non-GPU) prototype uses Python 3.12 via `uv`. Local tests use `MockLLMClient`. Live default is `openai/gpt-oss-120b` on vLLM >= 0.10.0.

## Language / tooling

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python | 3.12 (via `uv`) | Spec pin; `requires-python = ">=3.12,<3.13"` |
| Package manager | `uv` + `uv.lock` | Reproducible local installs |
| Money / qty | `decimal.Decimal` + normalized strings in schemas | Avoid float drift in AP matching |
| Decision space | `READY_FOR_DRAFT` \| `HUMAN_REVIEW` only | Bounded control plane |

## Model + serving pins — current default (gpt-oss-120b)

| Item | Pin |
|------|-----|
| Model | `openai/gpt-oss-120b` |
| Revision | optional; pin at launch and record in `reports/environment.json` |
| Docker image | current `vllm/vllm-openai` **>= 0.10.0** (do **not** reuse `v0.27.1`) |
| Digest | pin at launch |
| Serve | 1× H100, `--tp 1`, `--gpu-memory-utilization 0.95`, `--max-num-batched-tokens 1024`, `--max-model-len 8192` |
| Batch invariance | `VLLM_BATCH_INVARIANT=1` (and `=0` only on the negative-control server start) |
| Reasoning | Harmony top-level `extra_body.reasoning_effort=low`. **Not** `chat_template_kwargs.reasoning_effort` (ignored by vLLM Harmony; issues #23015, #41902). |
| Structured outputs | `--structured-outputs-config.backend xgrammar` + client `response_format` `json_schema` |
| Hash | canonical `ExtractedInvoice` JSON from `message.content` only; never reasoning traces |
| Sampling | `seed=42`, `top_p=1`, `n=1`; temperature is an experiment factor |

Qwen3 dense remains supported: when `MODEL_NAME` looks like Qwen3 (not 3.5 / 3.6 GDN), the client still sends `extra_body.chat_template_kwargs.enable_thinking=false`. That kwarg is **not** sent for gpt-oss.

Protocol: [`docs/experiment_temp_difficulty.md`](experiment_temp_difficulty.md).

## Prior pin (Qwen3-8B, 2026-08-13) — do not silently retag

| Item | Pin |
|------|-----|
| Model | `Qwen/Qwen3-8B` |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Docker image | `vllm/vllm-openai:v0.27.1` |
| Manifest digest | `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |
| Batch invariance | `VLLM_BATCH_INVARIANT=1` |
| Thinking | disabled: `chat_template_kwargs: {"enable_thinking": false}` and/or `--default-chat-template-kwargs '{"enable_thinking": false}'` |
| Structured outputs backend | `--structured-outputs-config.backend xgrammar` (**not** `auto`) |
| Client structured output | OpenAI `response_format` with `type: "json_schema"` (`guided_*` removed in vLLM 0.12+) |
| Sampling | `temperature=0`, `top_p=1`, `seed=42`, `n=1` |

Sources:
- https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
- https://docs.vllm.ai/en/v0.26.0/features/batch_invariance/
- https://docs.vllm.ai/en/latest/usage/reproducibility/
- https://docs.vllm.ai/en/latest/features/structured_outputs/
- https://huggingface.co/Qwen/Qwen3-8B
- https://huggingface.co/api/models/Qwen/Qwen3-8B
- Docker Hub tag `v0.27.1` for `vllm/vllm-openai`
- https://docs.vllm.ai/projects/recipes/en/latest/OpenAI/GPT-OSS.html
- https://github.com/vllm-project/vllm/issues/41902 (top-level `reasoning_effort`)
- https://github.com/vllm-project/vllm/issues/23015 (Harmony ignores `chat_template_kwargs`)
- https://huggingface.co/openai/gpt-oss-120b

## Why temp=0 alone is insufficient

Floating-point non-associativity makes reduction order matter. Kernels may be run-to-run deterministic yet **not batch-invariant**: changing batch size / concurrent load changes reduction strategy → different numerics → different tokens at temperature 0. Production path: `VLLM_BATCH_INVARIANT=1` (beta; hardware notes: Hopper/H100 9.0 safe; Ampere 8.x verify before relying).

## Architecture split

- **LLM**: extract structured invoice fields only (JSON schema).
- **Python**: canonicalize, evidence validation, Decimal arithmetic, three-way match, journal proposal, idempotency, audit, draft/review decision.
- Never auto-approve when `OCR_REQUIRED`.

## Local testing

- `MockLLMClient` returns fixture `expected.json` extraction (or deterministic parser for synthetic PDFs).
- GPU evaluate-determinism sections are explicitly `SKIP` until a pinned vLLM pod is run.
- PDF generation uses ReportLab with fixed metadata / no timestamps for byte reproducibility.

## GPU verification (2026-08-13)

Executed on pinned H100 + image above. See `reports/final_report.md`.

- Batch-invariant kernels: hashes stable at conc 1/8/32 (MEDIUM, 50×10). **Negative control (`VLLM_BATCH_INVARIANT=0`) not run.**
- xgrammar + `json_schema` + `disable_any_whitespace`: 50/50 schema-valid live extracts.
- Qwen3 non-thinking path: client and server `enable_thinking=false`.
- Cross-machine: SXM AP-IN-1 hashes matched prior PCIe US-KS-2 on all 50 cases.
- Not run: pod restart, full 9,000-extract matrix.

Full research notes: `/workspace/accounting-agent-refs-summary.md` (copied into repo context; not committed as runtime dependency).
