#!/usr/bin/env python3
"""Evaluate decision accuracy on development and holdout with MockLLMClient."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import init_db
from app.llm_client import MockLLMClient
from app.pipeline import run_case_dir


def eval_split(name: str, root: Path, db_url: str) -> dict:
    subprocess.check_call(
        [
            sys.executable,
            str(REPO / "scripts" / "initialize_database.py"),
            "--reset",
            "--database-url",
            db_url,
        ],
        cwd=str(REPO),
    )
    sf = init_db(db_url)
    erp = LocalERPAdapter(sf)
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")

    rows = []
    correct = 0
    total = 0
    for case_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")):
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
        ok = result.decision.value == expected["decision"]
        exp_codes = set(expected.get("exception_codes") or [])
        got_codes = set(result.exception_codes)
        if expected["decision"] == "READY_FOR_DRAFT":
            codes_ok = got_codes == set()
        else:
            codes_ok = exp_codes.issubset(got_codes)
        match = ok and codes_ok
        correct += int(match)
        total += 1
        rows.append(
            {
                "case_id": case_dir.name,
                "scenario": expected.get("scenario"),
                "expected_decision": expected["decision"],
                "got_decision": result.decision.value,
                "expected_codes": sorted(exp_codes),
                "got_codes": sorted(got_codes),
                "pass": match,
            }
        )
    return {
        "split": name,
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "rows": rows,
    }


def main() -> None:
    out = {"development": None, "holdout": None, "llm": "MockLLMClient", "gpu": False}
    with tempfile.TemporaryDirectory() as td:
        for split in ("development", "holdout"):
            db_url = f"sqlite:///{Path(td) / (split + '.db')}"
            root = REPO / "tests" / "fixtures" / split
            out[split] = eval_split(split, root, db_url)
            print(
                f"{split}: {out[split]['correct']}/{out[split]['total']} "
                f"accuracy={out[split]['accuracy']:.3f}"
            )
            for f in [r for r in out[split]["rows"] if not r["pass"]][:20]:
                print(" FAIL", f)

    reports = REPO / "reports"
    reports.mkdir(exist_ok=True)
    path = reports / "accuracy_mock.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
