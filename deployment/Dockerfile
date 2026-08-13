# Application image (CPU). vLLM GPU image is pinned by digest in start_vllm.sh / docker-compose.yml.
# App base: python:3.12-slim — resolve digest at build time with:
#   docker pull python:3.12-slim && docker image inspect python:3.12-slim --format '{{index .RepoDigests 0}}'
# and substitute below before production builds (NEEDS_LIVE_DIGEST for app base).
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY config ./config
COPY prompts ./prompts
COPY scripts ./scripts
RUN uv sync --frozen --python 3.12

ENV DATABASE_URL=sqlite:////app/accounting_agent.db
# GPU serving uses (do not change silently):
#   vllm/vllm-openai:v0.27.1@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967
CMD ["uv", "run", "python", "scripts/run_case.py", "--help"]
