#!/usr/bin/env bash
# Start vLLM OpenAI server for invoice extraction.
# Default model: openai/gpt-oss-120b (Harmony). Requires vLLM >= 0.10.0.
# Do not reuse v0.27.1. Pin image digest at launch in reports/environment.json.
#
# Negative control (second server start):
#   VLLM_BATCH_INVARIANT=0 ./deployment/start_vllm.sh
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-openai/gpt-oss-120b}"
MODEL_REVISION="${MODEL_REVISION:-}"
IMAGE="${VLLM_DOCKER_IMAGE:-vllm/vllm-openai:latest}"
DIGEST="${VLLM_DOCKER_DIGEST:-}"
PORT="${VLLM_PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS:-1024}"
GPU_MEM="${GPU_MEMORY_UTILIZATION:-0.95}"
TP="${TENSOR_PARALLEL_SIZE:-1}"
BATCH_INV="${VLLM_BATCH_INVARIANT:-1}"
# Publish on loopback by default: the inference API is unauthenticated unless
# VLLM_API_KEY is set, and an open port on a rented pod is world-reachable.
BIND_HOST="${VLLM_BIND_HOST:-127.0.0.1}"
API_KEY="${VLLM_API_KEY:-}"
ALLOW_NO_AUTH="${VLLM_ALLOW_NO_AUTH:-0}"

export VLLM_BATCH_INVARIANT="${BATCH_INV}"

if [[ -z "${API_KEY}" || "${API_KEY}" == "not-a-real-key" ]]; then
  if [[ "${ALLOW_NO_AUTH}" != "1" ]]; then
    echo "ERROR: VLLM_API_KEY is unset or still the placeholder." >&2
    echo "       Set a real secret (clients read the same variable), or set" >&2
    echo "       VLLM_ALLOW_NO_AUTH=1 to serve without auth on ${BIND_HOST}." >&2
    exit 1
  fi
  echo "WARNING: serving without API-key auth on ${BIND_HOST}:${PORT}."
  API_KEY=""
fi

if [[ -n "${DIGEST}" ]]; then
  IMAGE_REF="${IMAGE}@${DIGEST}"
else
  IMAGE_REF="${IMAGE}"
  echo "WARNING: VLLM_DOCKER_DIGEST unset. Pin the digest at launch (vLLM >= 0.10.0)."
fi

echo "Pulling ${IMAGE_REF}  (VLLM_BATCH_INVARIANT=${BATCH_INV})"
docker pull "${IMAGE_REF}"

ARGS=(
  --model "${MODEL_NAME}"
  --structured-outputs-config.backend xgrammar
  --max-model-len "${MAX_MODEL_LEN}"
  --max-num-batched-tokens "${MAX_NUM_BATCHED_TOKENS}"
  --gpu-memory-utilization "${GPU_MEM}"
  --tensor-parallel-size "${TP}"
  --dtype auto
)

if [[ -n "${MODEL_REVISION}" ]]; then
  ARGS+=(--revision "${MODEL_REVISION}")
fi

# Qwen3 dense (not 3.5 / 3.6 GDN): disable thinking at the server too.
case "${MODEL_NAME}" in
  *Qwen3.5*|*Qwen3.6*|*GDN*) ;;
  *Qwen3*|*qwen3*)
    ARGS+=(--default-chat-template-kwargs '{"enable_thinking": false}')
    ;;
esac

case "${MODEL_NAME}" in
  *gpt-oss*|*gptoss*)
    ARGS+=(--reasoning-parser openai_gptoss)
    ;;
esac

AUTH_ENV=()
if [[ -n "${API_KEY}" ]]; then
  # Pass via env, not argv: argv is visible to any process that can read /proc.
  AUTH_ENV=(-e "VLLM_API_KEY=${API_KEY}")
fi

docker run --rm --gpus all --ipc=host \
  -p "${BIND_HOST}:${PORT}:8000" \
  "${AUTH_ENV[@]}" \
  -e VLLM_BATCH_INVARIANT="${BATCH_INV}" \
  -e HF_HOME=/root/.cache/huggingface \
  -v "${HF_CACHE:-$HOME/.cache/huggingface}:/root/.cache/huggingface" \
  "${IMAGE_REF}" \
  "${ARGS[@]}"
