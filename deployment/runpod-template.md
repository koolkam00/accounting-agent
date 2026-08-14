# RunPod template (GPU phase — not executed in local dispatch)

## Current default pins (gpt-oss-120b experiment)

| Item | Value |
|------|-------|
| Model | `openai/gpt-oss-120b` |
| Revision | pin at launch; record in `reports/environment.json` |
| Image | current `vllm/vllm-openai` **>= 0.10.0** (do **not** reuse `v0.27.1`) |
| Digest | pin at launch |
| GPU | 1× H100, `--tensor-parallel-size 1` |
| Serve | `--gpu-memory-utilization 0.95 --max-num-batched-tokens 1024 --max-model-len 8192` |
| Env | `VLLM_BATCH_INVARIANT=1` (and `=0` only on the negative-control start) |
| Reasoning | client `extra_body.reasoning_effort=low` (Harmony top-level; not `chat_template_kwargs`) |
| Structured outputs | `--structured-outputs-config.backend xgrammar` + client `response_format` `json_schema` |
| Sampling | `seed=42`, `top_p=1`, `n=1`; temperature is an experiment factor |

## Prior Qwen3-8B pin (keep working; do not send for gpt-oss)

| Item | Value |
|------|-------|
| Model | `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218` |
| Image | `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |
| Thinking | client `extra_body.chat_template_kwargs.enable_thinking=false` when `MODEL_NAME` looks like Qwen3 (not 3.5 / 3.6 GDN) |

## Suggested pod

- GPU: NVIDIA H100 80GB (compute capability 9.0).
- Start command: `deployment/start_vllm.sh` (adapt volume mounts for RunPod / HF cache).
- Two server starts: invariance on, then invariance off.
- Auto-stop: stop pod after evaluation jobs; do not leave idle GPU rented.

## Client call shape (gpt-oss)

```python
client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[...],
    temperature=0,  # factor: 0, 0.3, 0.7, 1.0
    top_p=1,
    seed=42,
    n=1,
    response_format={"type": "json_schema", "json_schema": {...}},
    extra_body={"reasoning_effort": "low"},
)
# Parse message.content only. Hash ExtractedInvoice JSON, never reasoning traces.
```

## Status

GPU pod **not rented** for the temperature × difficulty grid. Do not create a pod until the spend cap is approved in chat.
