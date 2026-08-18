# Security review (2026-08-18)

Scope: whole repo (`app/`, `scripts/`, `deployment/`, config, docs, git history).
Threat model: the invoice PDF and everything derived from it (page text, model
output) is untrusted input; the Streamlit UI and the vLLM server are the only
network listeners; SQLite is the ERP and accounting sandbox.

## Fixed in this review

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | High | `deployment/start_vllm.sh` published the vLLM OpenAI API with `-p 8000:8000` (all interfaces) and never passed an API key, so the inference endpoint was open to anyone who could reach the pod. | Publish on `${VLLM_BIND_HOST:-127.0.0.1}`, require a non-placeholder `VLLM_API_KEY` (explicit `VLLM_ALLOW_NO_AUTH=1` to opt out), and pass the key through the container environment instead of argv. |
| 2 | High | `make run-ui` started Streamlit with default settings: bound to all interfaces, no authentication, 200 MB uploads. The UI can create draft bills in the sandbox DB. | `.streamlit/config.toml` pins loopback, XSRF protection, and a 25 MB upload cap; `make run-ui` passes `--server.address=127.0.0.1`; the upload handler rejects oversized files. |
| 3 | High | Extracted amounts are strings from model output. `to_decimal("NaN")` produced a non-finite `Decimal`, and the first comparison in `match_invoice` raised `decimal.InvalidOperation`, aborting the run with no decision and no `COMPLETE` audit event. | `to_decimal` rejects non-finite values; `match_invoice` converts unparseable line amounts into `INVOICE_MATH_ERROR` (→ `HUMAN_REVIEW`); journal construction is guarded the same way. |
| 4 | Medium | The UI's free-text "Case / document id" flowed into `MockLLMClient` fixture path joins (`fixture_root / split / case_id / "expected.json"`), i.e. a path-traversal read primitive. | New `app/identifiers.py` validator; the UI rejects unsafe ids and the mock client only joins validated single-segment ids. |
| 5 | Medium | Ingest had no size or page bound, so a malformed/hostile PDF could exhaust memory or CPU in `pypdf`. | `MAX_PDF_BYTES` (25 MB) and `MAX_PDF_PAGES` (100) enforced in `extract_pdf_text`. |
| 6 | Low | The UI sidebar rendered `database_url`, which embeds credentials for any non-SQLite backend. | Removed from the environment panel. |
| 7 | Low | The app container ran as root. | Runs as uid 10001. |
| 8 | Low | Dependency floors (`pypdf>=4.0`, `streamlit>=1.30`) allowed years-old releases for anyone installing without `uv.lock`. | Floors raised to maintained majors. `pip-audit` against the locked set reports no known vulnerabilities. |

## Checked and clean

- **Hardcoded secrets**: none in the tree or in history (`git log -S 'VLLM_API_KEY='`, plus `hf_`/`rpa_`/`sk-`/`AKIA`/`Bearer`/PEM patterns). `.env`, `*.db`, and `.streamlit/secrets.toml` are gitignored; `.env.example` holds only the `not-a-real-key` placeholder. `scripts/build_report.py` and `scripts/capture_environment.py` already strip key-shaped material from artifacts.
- **SQL injection**: every query goes through SQLAlchemy ORM `select()`/`session.get()` with bound parameters. No raw `text()`, string-formatted SQL, or `executescript`.
- **Code execution sinks**: no `eval`, `exec`, `pickle`, or `yaml.load`; policy is loaded with `yaml.safe_load`. `subprocess` calls use argument lists, never `shell=True`.
- **CORS / debug endpoints**: no HTTP API in the repo (no FastAPI/Flask/Django), so no CORS policy and no debug routes; Streamlit is the only listener and its XSRF/CORS defaults are now pinned.
- **Input validation**: Pydantic models are `extra="forbid"`, the live client requests a strict JSON schema, and evidence quotes must appear verbatim in the canonical page text.

## Residual risks (not addressed here)

- **The UI still has no authentication.** Loopback binding is containment, not access control; put it behind an authenticating proxy before exposing it, and record an approver identity on drafts.
- **Prompt injection.** Invoice text is untrusted and goes into the extraction prompt. The architecture limits the impact (Python owns every match and decision, evidence quotes are verified against the page), but a crafted invoice can still steer extracted values; the three-way match against ERP data is the control that must catch it.
- **No cap on canonical text length** sent to the model — bounded only indirectly by the page limit, so a dense document can still inflate token cost and latency.
- **SQLite ERP has no row-level authorization**, appropriate for the prototype but not for shared use.
