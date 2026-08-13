# Accounting Agent — Deterministic Three-Way Match

Prototype accounts-payable agent that performs PO / receipt / invoice three-way match with **deterministic Python control logic**. An LLM is used only for structured invoice extraction; matching, Decimal math, journal proposals, and decisions are pure Python.

## Architecture

Bounded state machine:

`INGEST → EXTRACT → VALIDATE → LOOKUP → MATCH → PROPOSE_JOURNAL → CREATE_DRAFT_OR_REVIEW`

Decisions are only `READY_FOR_DRAFT` or `HUMAN_REVIEW`.

## Local setup (Linux / Mac, non-GPU)

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv python install 3.12
uv sync --python 3.12
cp .env.example .env

make generate-data   # 50 synthetic cases + PDFs
make init-db         # load fixtures into SQLite
make test            # unit + integration (mock LLM)
```

Optional:

```bash
make evaluate-accuracy     # development + holdout with MockLLMClient
make evaluate-determinism  # local checks; GPU sections SKIP
make report
make run-ui                # Streamlit stub
```

## GPU / vLLM phase

Real LLM extraction against a pinned vLLM image is **not required** for local tests. Local pipeline tests use `MockLLMClient`.

### GPU pins (do not silently change)
- Model: `Qwen/Qwen3-8B` revision `b968826d9c46dd6066d109eabc6255188de91218`
- Image: `vllm/vllm-openai:v0.27.1` digest `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`
- `VLLM_BATCH_INVARIANT=1`; thinking disabled; `--structured-outputs-config.backend xgrammar`
- Sampling: temperature=0, top_p=1, seed=42, n=1; client `response_format` json_schema

See `deployment/` and `docs/technical_decisions.md`.

## Policy

See `config/policy.yaml`. Unit-price tolerance is `max(0.5% of PO price, $0.01)`. Non-zero tax always requires human review.

## License

Internal prototype / evaluation use.
