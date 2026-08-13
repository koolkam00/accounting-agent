# RunPod template (GPU phase — not executed in local dispatch)

## Pins (do not silently change)

| Item | Value |
|------|-------|
| Model | `Qwen/Qwen3-8B` |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Image | `vllm/vllm-openai:v0.27.1` |
| Digest | `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |
| Env | `VLLM_BATCH_INVARIANT=1` |
| Structured outputs | `--structured-outputs-config.backend xgrammar` |
| Thinking | `--default-chat-template-kwargs '{"enable_thinking": false}'` |
| Sampling (client) | `temperature=0`, `top_p=1`, `seed=42`, `n=1` |
| Client schema | `response_format` `json_schema` (not `guided_*`) |

## Suggested pod

- GPU: NVIDIA H100 (compute capability 9.0) — safest for batch invariance docs.
- Container: pin by digest above.
- Start command: see `deployment/start_vllm.sh` (adapt volume mounts for RunPod network volume / HF cache).
- Auto-stop: stop pod after evaluation jobs; do not leave idle GPU rented.

## Client call shape

```python
client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[...],
    temperature=0,
    top_p=1,
    seed=42,
    n=1,
    response_format={"type": "json_schema", "json_schema": {...}},
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

## Status

GPU pod **not rented** in the local/non-GPU dispatch. Determinism under load is pending verification.
