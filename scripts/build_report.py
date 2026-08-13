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


def main() -> None:
    reports = REPO / "reports"
    reports.mkdir(exist_ok=True)
    failures_dir = reports / "failures"
    failures_dir.mkdir(exist_ok=True)

    accuracy = _load(reports / "accuracy_mock.json")
    determinism = _load(reports / "determinism.json")
    environment = _load(reports / "environment.json")

    # results.csv from accuracy rows
    csv_path = reports / "results.csv"
    rows_out = []
    fail_count = 0
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
                    fail_path.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Clear stale failure files when accuracy is perfect
    if accuracy and fail_count == 0:
        for p in failures_dir.glob("*.json"):
            p.unlink()
        (failures_dir / "README.md").write_text(
            "# Failures\n\nNo MockLLM accuracy failures in the latest local evaluate-accuracy run.\n",
            encoding="utf-8",
        )
    elif not list(failures_dir.glob("*")):
        (failures_dir / "README.md").write_text(
            "# Failures\n\nNo failure artifacts yet. Run `make evaluate-accuracy`.\n",
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
    lines = [
        "# Final Report — Accounting Agent (Local / Non-GPU Dispatch)",
        "",
        f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"Source commit: `{commit}`",
        "",
        "## Scope",
        "",
        "- Implemented deterministic Python control plane for three-way match.",
        "- LLM extraction mocked locally via `MockLLMClient`.",
        "- Streamlit UI available via `make run-ui` (`app/ui.py`).",
        "- **GPU / vLLM evaluation NOT executed** in this dispatch.",
        "- **GPU spend: $0**.",
        "",
        "## Pins (for upcoming GPU phase)",
        "",
        "- Model: `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218`",
        "- Image: `vllm/vllm-openai:v0.27.1` @ `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967`",
        "- `VLLM_BATCH_INVARIANT=1`, thinking disabled, xgrammar structured outputs",
        "- Sampling: temperature=0, top_p=1, seed=42, n=1",
        "",
        "## Dataset",
        "",
        "- 50 synthetic cases (seed 20260812), development 001–030, holdout 031–050",
        "- See `tests/fixtures/dataset_manifest.json`",
        "",
        "## Accuracy (Mock LLM)",
        "",
    ]
    if accuracy:
        for split in ("development", "holdout"):
            s = accuracy.get(split) or {}
            lines.append(
                f"- **{split}**: {s.get('correct')}/{s.get('total')} "
                f"(accuracy={s.get('accuracy')})"
            )
        lines.append(f"- Per-case CSV: `reports/results.csv` ({len(rows_out)} rows)")
        lines.append(f"- Failure artifacts: `reports/failures/` ({fail_count} files)")
    else:
        lines.append("- Not yet generated. Run `make evaluate-accuracy`.")

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
        lines.append("### GPU determinism matrix — NOT EXECUTED YET")
        lines.append("")
        lines.append("| Dimension | Status | Notes |")
        lines.append("|-----------|--------|-------|")
        lines.append("| Same-request repeatability | NOT EXECUTED | Needs pinned vLLM on H100 |")
        lines.append("| Batch invariance under load | NOT EXECUTED | Needs `VLLM_BATCH_INVARIANT=1` |")
        lines.append("| Restart invariance | NOT EXECUTED | Pod stop/start not run |")
        lines.append("| Cross-machine invariance | NOT EXECUTED | Single local host only |")
        lines.append("")
        for g in determinism.get("gpu", []):
            lines.append(f"- SKIP `{g['name']}`: {g['reason']}")
    else:
        lines.append("- Run `make evaluate-determinism`.")

    lines += [
        "",
        "## Environment",
        "",
        f"- Captured in `reports/environment.json` (source_commit=`{commit}`)",
        f"- Platform: `{(environment or {}).get('platform', 'n/a')}`",
        f"- GPU run flag: `{(environment or {}).get('gpu_run', False)}`",
        "",
        "## Honest limitations",
        "",
        "- Token-level extraction determinism under load is **unverified** until the pinned vLLM image is exercised on suitable GPU hardware.",
        "- GPU determinism matrix (same-request / batch invariance / restart / cross-machine) is **explicitly not executed** — zero GPU spend.",
        "- Local path uses MockLLMClient; real Qwen3-8B extraction quality is pending GPU quote approval.",
        "- Fictional vendors only; not production ERP-integrated.",
        "",
        "## Artifacts",
        "",
        "- `reports/final_report.md` (this file)",
        "- `reports/results.csv`",
        "- `reports/environment.json`",
        "- `reports/accuracy_mock.json`",
        "- `reports/determinism.json`",
        "- `reports/failures/`",
        "- `reports/runpod_quote.md` (prepared; do not rent until approved)",
        "",
    ]
    path = reports / "final_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path}")
    print(f"wrote {csv_path} rows={len(rows_out)} failures={fail_count}")


if __name__ == "__main__":
    main()
