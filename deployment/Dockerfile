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
# GPU serving (gpt-oss-120b): vllm/vllm-openai >=0.10.0; pin digest at launch.
# Do not reuse v0.27.1. See deployment/start_vllm.sh.
CMD ["uv", "run", "python", "scripts/run_case.py", "--help"]
