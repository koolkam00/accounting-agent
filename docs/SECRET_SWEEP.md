# Secret sweep checklist

Run this before a public push, a gist, a screenshot of logs, or handing someone the zip.

## Must never ship

- [ ] `.env` (live `VLLM_API_KEY`, pod proxy URLs)
- [ ] RunPod / Hugging Face / GitHub tokens
- [ ] `*.log` (proxy URLs and auth headers can land here)
- [ ] SQLite `*.db` (local ERP sandbox)
- [ ] `.streamlit/secrets.toml`
- [ ] SSH keys, `id_rsa`, `.pem`

`.gitignore` already drops `.env`, `*.db`, `*.log`. Do not `git add -f` those.

## Scan commands

From the repo root:

```bash
# Working tree (skip venv and git)
rg -n --hidden -g '!.git' -g '!.venv' \
  'VLLM_API_KEY=.+|api-key [A-Za-z0-9_-]{8,}|Bearer [A-Za-z0-9._-]{8,}|hf_[A-Za-z0-9]+|rpa_[A-Za-z0-9]+' .

# History
git log -p --all -S 'VLLM_API_KEY=' -- .env ':!.env.example' | head
```

`.env.example` may contain `VLLM_API_KEY=not-a-real-key`. That is fine. A value that looks random is not.

## Reports that are safe to publish

These are supposed to be public:

- `reports/final_report.md`
- `reports/results.csv`
- `reports/determinism.json` (extraction hashes, not prompts with secrets)
- `reports/accuracy_gpu.json` / `accuracy_mock.json`
- `reports/environment.json` (pins, spend, pod ids — not keys)
- `reports/billing.json` (USD totals, not payment instruments)

Still open them and search for `Bearer`, `api-key`, `proxy.runpod.net` if a log got concatenated in.

## After a leak

1. Rotate the key (RunPod API key, vLLM `--api-key`, Hugging Face token).
2. Do not `git rm` and hope. History still has it. Rotate first.
3. Stop any pod whose start command baked the old key.
