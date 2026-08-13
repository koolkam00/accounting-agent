#!/usr/bin/env python3
"""Capture local environment metadata for reports (includes source git commit)."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO),
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return None


def _git_dirty() -> bool | None:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(REPO),
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except Exception:
        return None


def main() -> None:
    try:
        import importlib.metadata as md

        pkgs = {
            name: md.version(name)
            for name in [
                "pydantic",
                "pypdf",
                "reportlab",
                "sqlalchemy",
                "openai",
                "pytest",
                "streamlit",
                "pandas",
            ]
        }
    except Exception as exc:  # pragma: no cover
        pkgs = {"error": str(exc)}

    commit = _git_commit()
    data = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": pkgs,
        "source_commit": commit,
        "source_dirty": _git_dirty(),
        "model_pin": {
            "name": "Qwen/Qwen3-8B",
            "revision": "b968826d9c46dd6066d109eabc6255188de91218",
            "image": "vllm/vllm-openai:v0.27.1",
            "digest": "sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967",
        },
        "gpu_run": False,
        "gpu_spend_usd": 0,
        "determinism_matrix": {
            "same_request": "NOT_EXECUTED_GPU",
            "batch_invariance": "NOT_EXECUTED_GPU",
            "restart": "NOT_EXECUTED_GPU",
            "cross_machine": "NOT_EXECUTED_GPU",
            "local_pdf_sha256": "EXECUTED",
        },
    }
    out = REPO / "reports" / "environment.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} source_commit={commit}")


if __name__ == "__main__":
    main()
