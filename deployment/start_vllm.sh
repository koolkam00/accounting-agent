#!/usr/bin/env bash
# Start pinned vLLM OpenAI server for deterministic invoice extraction.
# Do not silently change image/model pins — see docs/technical_decisions.md
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-8B}"
MODEL_REVISION="${MODEL_REVISION:-b968826d9c46dd6066d109eabc6255188de91218}"
IMAGE="${VLLM_DOCKER_IMAGE:-vllm/vllm-openai:v0.27.1}"
DIGEST="${VLLM_DOCKER_DIGEST:-sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967}"
PORT="${VLLM_PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"

export VLLM_BATCH_INVARIANT=1

echo "Pulling ${IMAGE}@${DIGEST}"
docker pull "${IMAGE}@${DIGEST}"

docker run --rm --gpus all --ipc=host \
  -p "${PORT}:8000" \
  -e VLLM_BATCH_INVARIANT=1 \
  -e HF_HOME=/root/.cache/huggingface \
  -v "${HF_CACHE:-$HOME/.cache/huggingface}:/root/.cache/huggingface" \
  "${IMAGE}@${DIGEST}" \
  --model "${MODEL_NAME}" \
  --revision "${MODEL_REVISION}" \
  --default-chat-template-kwargs '{"enable_thinking": false}' \
  --structured-outputs-config.backend xgrammar \
  --max-model-len "${MAX_MODEL_LEN}" \
  --dtype auto
