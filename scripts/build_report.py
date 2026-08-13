#!/usr/bin/env python3
"""Build reports/final_report.md + results.csv + failures/ from local artifacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _redact(s: str) -> str:
    # belt-and-suspenders: never echo API keys if they leaked into artifacts
    for needle in ("VLLM_API_KEY", "api-key", "api_key", "Bearer "):
        if needle.lower() in s.lower():
            return "[REDACTED]"
    return s


def main() -> None:
    reports = REPO / "reports"
    reports.mkdir(exist_ok=True)
    failures_dir = reports / "failures"
    failures_dir.mkdir(exist_ok=True)

    accuracy_gpu = _load(reports / "accuracy_gpu.json")
    accuracy_mock = _load(reports / "accuracy_mock.json")
    accuracy = accuracy_gpu or accuracy_mock
    determinism = _load(reports / "determinism.json")
    environment = _load(reports / "environment.json")
    billing = _load(reports / "billing.json")

    csv_path = reports / "results.csv"
    rows_out = []
    fail_count = 0
    # clear previous failure jsons (keep README until we rewrite)
    for p in failures_dir.glob("*.json"):
        p.unlink()

    if accuracy:
        for split in ("development", "holdout"):
            block = accuracy.get(split) or {}
            for r in block.get("rows") or []:
                rows_out.append(
                    {
                        "split": split,
                        "case_id": r.get("case_id"),
                        "scenario": r.get("scenario"),
                        "expected_decision": r.get("expected_decision"),
                        "got_decision": r.get("got_decision"),
                        "expected_codes": "|".join(r.get("expected_codes") or []),
                        "got_codes": "|".join(r.get("got_codes") or []),
                        "pass": r.get("pass"),
                        "llm": accuracy.get("llm"),
                        "gpu": accuracy.get("gpu"),
                    }
                )
                if not r.get("pass"):
                    fail_count += 1
                    fail_path = failures_dir / f"{split}_{r.get('case_id')}.json"
                    slim = {k: v for k, v in r.items()}
                    fail_path.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if accuracy and fail_count == 0:
        gpu = bool(accuracy.get("gpu"))
        (failures_dir / "README.md").write_text(
            "# Failures\n\nNo accuracy failures in the latest "
            + ("GPU/vLLM" if gpu else "MockLLM")
            + " evaluate-accuracy run.\n",
            encoding="utf-8",
        )
    elif not list(failures_dir.glob("*")):
        (failures_dir / "README.md").write_text(
            "# Failures\n\nNo failure artifacts yet. Run `make evaluate-accuracy` or `--live`.\n",
            encoding="utf-8",
        )

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        fields = [
            "split",
            "case_id",
            "scenario",
            "expected_decision",
            "got_decision",
            "expected_codes",
            "got_codes",
            "pass",
            "llm",
            "gpu",
        ]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows_out:
            w.writerow(row)

    commit = (environment or {}).get("source_commit") or "unknown"
    gpu_run = bool((environment or {}).get("gpu_run") or (accuracy and accuracy.get("gpu")))
    spend = (environment or {}).get("gpu_spend_usd")
    hours = (environment or {}).get("gpu_hours")
    if billing:
        spend = billing.get("gpu_spend_usd", spend)
        hours = billing.get("gpu_hours", hours)

    title = "Final Report — Accounting Agent (GPU / vLLM)" if gpu_run else "Final Report — Accounting Agent (Local / Non-GPU Dispatch)"
    lines = [
        f"# {title}",
        "",
        f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"Source commit: `{commit}`",
        "",
        "## Scope",
        "",
        "- Deterministic Python control plane for three-way match.",
        "- Streamlit UI available via `make run-ui` (`app/ui.py`).",
    ]
    if gpu_run:
        lines += [
            "- **GPU / vLLM evaluation EXECUTED** on pinned Qwen3-8B + vLLM image (see Pins).",
            f"- **GPU spend (from billing artifact, not an estimate unless noted): {spend}**",
            f"- **GPU hours: {hours}**",
        ]
    else:
        lines += [
            "- LLM extraction mocked locally via `MockLLMClient`.",
            "- **GPU / vLLM evaluation NOT executed** in this dispatch.",
            "- **GPU spend: $0**.",
        ]

    lines += [
        "",
        "## Pins",
        "",
        "- Model: `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218`",
        "- Served name: `ap-extractor-v1`",
        "- Image: `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`",
        "- `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar structured outputs",
        "- Sampling: temperature=0, top_p=1, seed=42, n=1",
        "",
        "## Dataset",
        "",
        "- 50 synthetic cases (seed 20260812), development 001–030, holdout 031–050",
        "- See `tests/fixtures/dataset_manifest.json`",
        "- Holdout was not used for prompt/policy tuning.",
        "",
        "## Accuracy",
        "",
    ]

    if accuracy_mock:
        md = accuracy_mock.get("development") or {}
        mh = accuracy_mock.get("holdout") or {}
        lines.append(
            f"- **MockLLM development**: {md.get('correct')}/{md.get('total')} "
            f"(accuracy={md.get('accuracy')})"
        )
        lines.append(
            f"- **MockLLM holdout**: {mh.get('correct')}/{mh.get('total')} "
            f"(accuracy={mh.get('accuracy')})"
        )
    if accuracy_gpu:
        gd = accuracy_gpu.get("development") or {}
        gh = accuracy_gpu.get("holdout") or {}
        lines.append(
            f"- **Live Qwen3-8B development**: {gd.get('correct')}/{gd.get('total')} "
            f"(accuracy={gd.get('accuracy')}) schema_valid={gd.get('schema_valid')} "
            f"false_READY_FOR_DRAFT={gd.get('false_ready_for_draft')}"
        )
        lines.append(
            f"- **Live Qwen3-8B holdout**: {gh.get('correct')}/{gh.get('total')} "
            f"(accuracy={gh.get('accuracy')}) schema_valid={gh.get('schema_valid')} "
            f"false_READY_FOR_DRAFT={gh.get('false_ready_for_draft')}"
        )
        if (gh.get("accuracy") or 0) < 1.0:
            lines.append("- Holdout is **not** 100%. See `reports/failures/` — expected.json was not edited.")
        lines.append(f"- Live LLM: `{accuracy_gpu.get('llm')}`; preseeded_from_expected={accuracy_gpu.get('preseeded_from_expected')}")
    elif accuracy:
        for split in ("development", "holdout"):
            s = accuracy.get(split) or {}
            lines.append(
                f"- **{split}**: {s.get('correct')}/{s.get('total')} "
                f"(accuracy={s.get('accuracy')})"
            )
    else:
        lines.append("- Not yet generated. Run `make evaluate-accuracy`.")

    lines.append(f"- Per-case CSV: `reports/results.csv` ({len(rows_out)} rows)")
    lines.append(f"- Failure artifacts: `reports/failures/` ({fail_count} files)")

    lines += [
        "",
        "## Determinism",
        "",
        "### Local (executed)",
        "",
    ]
    if determinism:
        for item in determinism.get("local", []):
            lines.append(f"- `{item.get('name')}`: pass={item.get('pass')}")
        lines.append("")
        label = determinism.get("matrix_label") or (
            "EXECUTED" if determinism.get("gpu_determinism_matrix_executed") else "NOT EXECUTED"
        )
        lines.append(f"### GPU determinism matrix — {label}")
        lines.append("")
        lines.append("| Dimension | Status | Unique hashes | n | Notes |")
        lines.append("|-----------|--------|---------------|---|-------|")
        for g in determinism.get("gpu", []):
            notes = g.get("reason") or g.get("note") or ""
            if g.get("cases_with_more_than_one_hash") is not None:
                notes = f"cases_with_>1_hash={g.get('cases_with_more_than_one_hash')}; " + notes
            if g.get("cases_with_hash_change_across_restarts") is not None:
                notes = f"cross_restart_changes={g.get('cases_with_hash_change_across_restarts')}; " + notes
            notes = notes.replace("|", "/").replace("\n", " ")
            lines.append(
                f"| {g.get('dimension')} / {g.get('name')} | {g.get('status')} | "
                f"{g.get('unique_hashes_global', '')} | {g.get('n_requests', '')} | {notes} |"
            )
    else:
        lines.append("- Run `make evaluate-determinism`.")

    lines += [
        "",
        "## Environment / spend",
        "",
        f"- Captured in `reports/environment.json` (source_commit=`{commit}`)",
        f"- Platform: `{(environment or {}).get('platform', 'n/a')}`",
        f"- GPU run flag: `{gpu_run}`",
        f"- GPU hours: `{hours}`",
        f"- GPU spend USD: `{spend}`",
        f"- Pod id(s): `{(environment or {}).get('pod_ids', 'n/a')}`",
        "",
        "## Honest limitations",
        "",
    ]
    if gpu_run:
        lines += [
            "- Accuracy is live Qwen3-8B extraction + Python match/decision, not MockLLM. Holdout was not tuned.",
            "- Determinism hashes exclude timestamps/request ids; they hash canonical ExtractedInvoice JSON.",
            "- Negative control (VLLM_BATCH_INVARIANT off) is only claimed if that section status is EXECUTED.",
            "- Cross-machine invariance was not rented as a second host unless listed EXECUTED.",
            "- Fictional vendors only; not production ERP-integrated.",
            "- API keys are not written into this report.",
        ]
    else:
        lines += [
            "- Token-level extraction determinism under load is **unverified** until the pinned vLLM image is exercised on suitable GPU hardware.",
            "- GPU determinism matrix (same-request / batch invariance / restart / cross-machine) is **explicitly not executed** — zero GPU spend.",
            "- Local path uses MockLLMClient; real Qwen3-8B extraction quality is pending GPU quote approval.",
            "- Fictional vendors only; not production ERP-integrated.",
        ]

    lines += [
        "",
        "## Artifacts",
        "",
        "- `reports/final_report.md` (this file)",
        "- `reports/results.csv`",
        "- `reports/environment.json`",
        "- `reports/accuracy_mock.json`",
        "- `reports/accuracy_gpu.json` (if live)",
        "- `reports/determinism.json`",
        "- `reports/failures/`",
        "- `reports/billing.json` (if captured)",
        "",
    ]
    path = reports / "final_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path}")
    print(f"wrote {csv_path} rows={len(rows_out)} failures={fail_count}")


if __name__ == "__main__":
    main()
