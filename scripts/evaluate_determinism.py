#!/usr/bin/env python3
"""Determinism evaluation. GPU/vLLM sections are SKIP until a pod is run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.canonicalize import canonicalize_document, sha256_bytes
from app.pdf_text import extract_pdf_text


def local_pdf_determinism() -> dict:
    """Hash existing fixtures twice (read stability) + regenerate check is in pytest."""
    results = []
    root = REPO / "tests" / "fixtures" / "development"
    for case_dir in sorted(root.glob("case_*"))[:5]:
        pdf = (case_dir / "invoice.pdf").read_bytes()
        h1 = sha256_bytes(pdf)
        h2 = sha256_bytes((case_dir / "invoice.pdf").read_bytes())
        pages = extract_pdf_text(pdf).pages
        c1 = canonicalize_document(pdf, pages).canonical_hash
        c2 = canonicalize_document(pdf, pages).canonical_hash
        results.append(
            {
                "case_id": case_dir.name,
                "pdf_stable": h1 == h2,
                "canonical_stable": c1 == c2,
                "sha256": h1,
            }
        )
    return {
        "name": "local_pdf_canonical_stability",
        "results": results,
        "pass": all(r["pdf_stable"] and r["canonical_stable"] for r in results),
    }


def gpu_matrix_not_executed() -> list[dict]:
    """Explicit dimensions the user asked to distinguish — all NOT executed (zero GPU spend)."""
    reason = "GPU determinism matrix NOT executed yet; zero GPU spend; awaiting RunPod quote approval"
    return [
        {
            "dimension": "same_request",
            "name": "same_request_repeatability",
            "status": "NOT_EXECUTED",
            "reason": reason + "; would repeat identical extraction requests N times",
        },
        {
            "dimension": "batch_invariance",
            "name": "vllm_batch_invariant_token_stability",
            "status": "NOT_EXECUTED",
            "reason": reason + "; requires VLLM_BATCH_INVARIANT=1 on pinned image v0.27.1",
        },
        {
            "dimension": "restart",
            "name": "pod_restart_invariance",
            "status": "NOT_EXECUTED",
            "reason": reason + "; would stop/start vLLM and compare tokens",
        },
        {
            "dimension": "cross_machine",
            "name": "cross_machine_invariance",
            "status": "NOT_EXECUTED",
            "reason": reason + "; single local host only in this dispatch",
        },
        {
            "dimension": "structured_outputs",
            "name": "vllm_json_schema_xgrammar_stability",
            "status": "NOT_EXECUTED",
            "reason": reason + "; xgrammar + json_schema pending live verification",
        },
        {
            "dimension": "nonthinking",
            "name": "qwen3_nonthinking_extraction_repeatability",
            "status": "NOT_EXECUTED",
            "reason": reason + "; model revision b968826d9c46dd6066d109eabc6255188de91218 pending",
        },
    ]


def main() -> None:
    report = {
        "local": [local_pdf_determinism()],
        "gpu": gpu_matrix_not_executed(),
        "gpu_determinism_matrix_executed": False,
        "gpu_spend_usd": 0,
    }
    ok = all(x.get("pass", True) for x in report["local"])
    path = REPO / "reports" / "determinism.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"local_pass": ok, "gpu_not_executed": len(report["gpu"])}, indent=2))
    print(f"wrote {path}")
    for g in report["gpu"]:
        print(f"NOT_EXECUTED [{g['dimension']}]: {g['name']}")


if __name__ == "__main__":
    main()
