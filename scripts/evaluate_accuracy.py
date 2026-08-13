#!/usr/bin/env python3
"""Evaluate decision accuracy on development and holdout.

Default: MockLLMClient (local).
--live: VLLMLLMClient against VLLM_BASE_URL. Does NOT preseed from expected.json.
Does not tune on holdout. Does not edit expected.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import init_db
from app.llm_client import MockLLMClient, VLLMLLMClient
from app.pipeline import Pipeline, run_case_dir
from app.settings import get_settings


def eval_split(name: str, root: Path, db_url: str, *, live: bool) -> dict:
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
    if live:
        get_settings.cache_clear()
        llm = VLLMLLMClient()
    else:
        llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")

    rows = []
    correct = 0
    total = 0
    schema_valid = 0
    false_ready = 0
    for case_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")):
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        error = None
        extraction_dump = None
        try:
            if live:
                pdf_bytes = (case_dir / "invoice.pdf").read_bytes()
                result = Pipeline(erp=erp, llm=llm).run(
                    pdf_bytes, case_id=case_dir.name, mode="evaluate"
                )
            else:
                result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
            got_decision = result.decision.value
            got_codes = set(result.exception_codes)
            if result.extracted_invoice is not None:
                schema_valid += 1
                extraction_dump = result.extracted_invoice.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001 — record live failures honestly
            error = f"{type(exc).__name__}: {exc}"
            got_decision = "ERROR"
            got_codes = set()
            result = None
            print(f"  ERROR {case_dir.name}: {error}", flush=True)

        ok = result is not None and result.decision.value == expected["decision"]
        exp_codes = set(expected.get("exception_codes") or [])
        if expected["decision"] == "READY_FOR_DRAFT":
            codes_ok = got_codes == set()
        else:
            codes_ok = exp_codes.issubset(got_codes)
        match = bool(ok and codes_ok and error is None)
        if got_decision == "READY_FOR_DRAFT" and expected["decision"] != "READY_FOR_DRAFT":
            false_ready += 1
        correct += int(match)
        total += 1
        rows.append(
            {
                "case_id": case_dir.name,
                "scenario": expected.get("scenario"),
                "expected_decision": expected["decision"],
                "got_decision": got_decision,
                "expected_codes": sorted(exp_codes),
                "got_codes": sorted(got_codes),
                "pass": match,
                "error": error,
                "extraction": extraction_dump,
            }
        )
        print(
            f"  [{name}] {case_dir.name} pass={match} got={got_decision} "
            f"expected={expected['decision']} err={error} "
            f"running={correct}/{total}",
            flush=True,
        )
        # incremental checkpoint so a kill does not lose completed cases
        ck = REPO / "reports" / "accuracy_gpu.partial.json"
        ck.parent.mkdir(exist_ok=True)
        slim_rows = []
        for r in rows:
            s = {k: v for k, v in r.items() if k != "extraction"}
            slim_rows.append(s)
        ck.write_text(
            json.dumps({"split": name, "correct": correct, "total": total, "rows": slim_rows}, indent=2)
            + "\n",
            encoding="utf-8",
        )
    return {
        "split": name,
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "schema_valid": schema_valid,
        "false_ready_for_draft": false_ready,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use VLLMLLMClient (no expected.json preseed)")
    args = parser.parse_args()
    live = args.live
    out = {
        "development": None,
        "holdout": None,
        "llm": "VLLMLLMClient" if live else "MockLLMClient",
        "gpu": live,
        "preseeded_from_expected": (not live),
    }
    with tempfile.TemporaryDirectory() as td:
        for split in ("development", "holdout"):
            db_url = f"sqlite:///{Path(td) / (split + '.db')}"
            root = REPO / "tests" / "fixtures" / split
            out[split] = eval_split(split, root, db_url, live=live)
            print(
                f"{split}: {out[split]['correct']}/{out[split]['total']} "
                f"accuracy={out[split]['accuracy']:.3f} "
                f"schema_valid={out[split]['schema_valid']} "
                f"false_READY_FOR_DRAFT={out[split]['false_ready_for_draft']}"
            )
            for f in [r for r in out[split]["rows"] if not r["pass"]][:20]:
                slim = {k: v for k, v in f.items() if k != "extraction"}
                print(" FAIL", slim)

    reports = REPO / "reports"
    reports.mkdir(exist_ok=True)
    path = reports / ("accuracy_gpu.json" if live else "accuracy_mock.json")
    # Keep extraction dumps only in failure files; strip from summary json to keep it smaller
    summary = json.loads(json.dumps(out))
    for split in ("development", "holdout"):
        for row in summary[split]["rows"]:
            if row.get("pass"):
                row.pop("extraction", None)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
