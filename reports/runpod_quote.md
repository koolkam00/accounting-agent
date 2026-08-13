# RunPod Quote Materials (DO NOT CREATE POD YET)

Prepared for user approval. **No GPU has been rented. GPU spend to date: $0.**

## Exact GPU request

| Field | Value |
|-------|-------|
| GPU | **1x NVIDIA H100 80GB** (PCIe preferred; SXM5 acceptable if PCIe unavailable) |
| Cloud | Secure Cloud preferred (SLA); Community Cloud OK for cost if stock is thin |
| Storage | **50 GB** container disk |
| Image (when running vLLM) | `vllm/vllm-openai:v0.27.1@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |
| Model | `Qwen/Qwen3-8B` revision `b968826d9c46dd6066d109eabc6255188de91218` |
| Env | `VLLM_BATCH_INVARIANT=1` |
| Auto-stop | **≤ 10 hours** hard cap |

## Looked-up hourly rates (as of web check 2026-08-12)

Sources consulted: [runpod.io/pricing](https://www.runpod.io/pricing), [runpod.io/gpu-models/h100-pcie](https://www.runpod.io/gpu-models/h100-pcie), secondary roundups.

| Tier | H100 80GB PCIe (approx.) | Confidence |
|------|--------------------------|------------|
| Community Cloud | **~$1.99 / hr** | Medium — marketplace, fluctuates |
| Secure Cloud | **~$2.39 – $2.89 / hr** | Medium — listings vary by page/date |

> If the live RunPod UI shows a different number at pod-create time, **use the live UI price** and treat this table as planning only. Mark any unconfirmed line as **NEEDS_LIVE_QUOTE**.

## Runtime & budget (conservative, under $50, under 10h)

Planned matrix (estimate ~9000 workflow-equivalent units across accuracy + determinism repeats):

| Item | Estimate |
|------|----------|
| Model pull + vLLM cold start | 0.5 – 1.0 h |
| Accuracy pass (50 cases × N samples) | 1.0 – 2.0 h |
| Determinism matrix (same-request / batch / restart) | 2.0 – 4.0 h |
| Buffer / retries | 1.0 h |
| **Max planned runtime** | **8 h** (auto-stop at 8h; never exceed 10h) |

Cost ceiling examples:

| Rate used | 8 h cost | Cap |
|-----------|----------|-----|
| $1.99/hr Community | ~$15.92 | under $50 |
| $2.39/hr Secure | ~$19.12 | under $50 |
| $2.89/hr Secure | ~$23.12 | under $50 |

**Approval ask total ceiling: $50 USD** (includes storage + idle margin). Stop the pod immediately when matrix completes.

## Exact approval ask (copy/paste)

> Please approve renting **one (1) RunPod H100 80GB** pod (Secure Cloud preferred) with **50 GB** disk for a **maximum of 8 hours** (hard auto-stop ≤ 10h), using pinned image `vllm/vllm-openai:v0.27.1@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` and model `Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218`, solely to run the accounting-agent GPU accuracy + determinism matrix. **Do not exceed $50 total spend.** Confirm the **live** hourly rate in the RunPod UI before clicking deploy. No other GPU SKUs, no multi-GPU, no unattended overnight run.

## CLI / UI steps (after approval only)

### UI

1. Open [https://www.runpod.io/console/pods](https://www.runpod.io/console/pods) → **Deploy**.
2. Select **GPU Cloud** → filter **H100 80GB** → prefer **Secure Cloud**.
3. Confirm live $/hr; abort if projected 8h cost > $50.
4. Template / Docker: `vllm/vllm-openai:v0.27.1` **with digest** `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`.
5. Volume/disk: **50 GB**. Set idle/auto-stop ≤ 8–10h.
6. Expose HTTP port **8000**.
7. After start, open a terminal on the pod (or SSH) and set `VLLM_BATCH_INVARIANT=1` before serving (see `deployment/start_vllm.sh`).

### CLI (illustrative — confirm flags against current RunPod CLI docs)

```bash
# NEEDS_LIVE_QUOTE: verify `runpodctl` syntax against current docs before use.
# Example shape only:
runpodctl create pod \
  --name accounting-agent-h100 \
  --gpuType "NVIDIA H100 80GB PCIe" \
  --imageName "vllm/vllm-openai:v0.27.1@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967" \
  --containerDiskSize 50 \
  --ports "8000/http" \
  --env "VLLM_BATCH_INVARIANT=1"
```

Or copy `deployment/start_vllm.sh` onto the pod and run it.

### Health checks

```bash
# Pod up
curl -sf http://127.0.0.1:8000/v1/models | head

# Chat/completions smoke (structured JSON later via client)
curl -sf http://127.0.0.1:8000/health || curl -sf http://127.0.0.1:8000/v1/models
```

From the repo (with `VLLM_BASE_URL` pointed at the pod):

```bash
make evaluate-accuracy   # after switching client off MockLLM
make evaluate-determinism
make report
```

### Shutdown (mandatory)

1. Stop vLLM container / process.
2. **Stop + terminate** the RunPod pod in the console (or `runpodctl remove pod <id>`).
3. Confirm billing shows no running GPU.
4. Record final wall-clock hours and USD in `reports/environment.json` (`gpu_run: true`, `gpu_spend_usd`).

## Out of scope for this quote

- Multi-GPU / H200 / B200
- Unpinned model revisions or unpinned images
- Production ERP connectivity
- Any spend before explicit user approval of the ask above
