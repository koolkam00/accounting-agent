#!/usr/bin/env python3
"""Evaluate decision accuracy on development and holdout.

Default: MockLLMClient (local).
--live: VLLMLLMClient against VLLM_BASE_URL. Does NOT preseed from expected.json.
Does not tune on holdout. Does not edit expected.json.
"""

from __future__ import annotations

import argparse
import copy
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import reset_db
from app.erp_seed import seed_fixture_cases
from app.evaluation import field_exact_match, invariance_label
from app.fixtures import (
    FIXTURE_ROOT,
    canonical_text_for_pdf,
    case_dirs_by_split,
    case_dirs,
    gold_extraction,
    load_expected,
    load_pdf_bytes,
)
from app.jsonio import write_json
from app.llm_client import MockLLMClient, VLLMLLMClient
from app.pipeline import Pipeline, run_case_dir
from app.settings import get_settings


def eval_cases(name: str, cases: list[Path], db_url: str, *, live: bool, llm) -> dict:
    sf = reset_db(db_url)
    seed_fixture_cases(sf, cases)
    erp = LocalERPAdapter(sf)

    rows = []
    correct = 0
    total = 0
    schema_valid = 0
    false_ready = 0
    field_match = 0
    for case_dir in cases:
        expected = load_expected(case_dir)
        gold = gold_extraction(expected)
        error = None
        extraction_dump = None
        fields_ok = False
        # Canonical PDF text actually sent to the model (INGEST text-layer output)
        pdf_bytes = load_pdf_bytes(case_dir)
        canon_text = canonical_text_for_pdf(pdf_bytes)
        try:
            if live:
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
                fields_ok = field_exact_match(extraction_dump, gold)
                field_match += int(fields_ok)
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
                "difficulty": expected.get("difficulty"),
                "canonical_text": canon_text,
                "expected_decision": expected["decision"],
                "got_decision": got_decision,
                "expected_codes": sorted(exp_codes),
                "got_codes": sorted(got_codes),
                "pass": match,
                "field_exact_match": fields_ok,
                "error": error,
                "extraction": extraction_dump,
            }
        )
        print(
            f"  [{name}] {case_dir.name} pass={match} fields={fields_ok} got={got_decision} "
            f"expected={expected['decision']} err={error} "
            f"running={correct}/{total}",
            flush=True,
        )
        slim_rows = [{k: v for k, v in r.items() if k != "extraction"} for r in rows]
        write_json(
            REPO / "reports" / "accuracy_gpu.partial.json",
            {"split": name, "correct": correct, "total": total, "rows": slim_rows},
            sort_keys=False,
        )
    return {
        "split": name,
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "schema_valid": schema_valid,
        "field_exact_match": field_match,
        "field_exact_match_rate": (field_match / total) if total else 0.0,
        "false_ready_for_draft": false_ready,
        "rows": rows,
    }


def eval_split(name: str, root: Path, db_url: str, *, live: bool) -> dict:
    """Backward-compatible wrapper used by older callers."""
    if live:
        get_settings.cache_clear()
        llm = VLLMLLMClient()
    else:
        llm = MockLLMClient(fixture_root=FIXTURE_ROOT)
    return eval_cases(name, case_dirs(root), db_url, live=live, llm=llm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use VLLMLLMClient (no expected.json preseed)")
    parser.add_argument("--temperature", type=float, default=None, help="Per-eval sampling temperature")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default=None)
    parser.add_argument("--label", default=None)
    parser.add_argument(
        "--negative-control",
        action="store_true",
        help="Record invariance=off (caller must have started vLLM with VLLM_BATCH_INVARIANT=0)",
    )
    args = parser.parse_args()
    live = args.live
    get_settings.cache_clear()
    settings = get_settings()
    temp = args.temperature if args.temperature is not None else settings.temperature
    if live:
        llm = VLLMLLMClient(temperature=temp)
    else:
        llm = MockLLMClient(fixture_root=FIXTURE_ROOT)

    splits = case_dirs_by_split(args.difficulty)
    out: dict[str, Any] = {
        "development": None,
        "holdout": None,
        "llm": "VLLMLLMClient" if live else "MockLLMClient",
        "gpu": live,
        "preseeded_from_expected": (not live),
        "temperature": temp,
        "difficulty": args.difficulty,
        "invariance": invariance_label(args.negative_control),
        "model": settings.model_name,
        "model_revision": settings.model_revision,
        "reasoning_effort": settings.reasoning_effort,
        "label": args.label,
    }
    with tempfile.TemporaryDirectory() as td:
        for split, cases in splits.items():
            db_url = f"sqlite:///{Path(td) / (split + '.db')}"
            out[split] = eval_cases(split, cases, db_url, live=live, llm=llm)
            print(
                f"{split}: {out[split]['correct']}/{out[split]['total']} "
                f"accuracy={out[split]['accuracy']:.3f} "
                f"schema_valid={out[split]['schema_valid']} "
                f"field_exact_match={out[split]['field_exact_match']} "
                f"false_READY_FOR_DRAFT={out[split]['false_ready_for_draft']}"
            )
            for f in [r for r in out[split]["rows"] if not r["pass"]][:20]:
                slim = {k: v for k, v in f.items() if k != "extraction"}
                print(" FAIL", slim)

    reports = REPO / "reports"
    if args.difficulty or args.temperature is not None or args.label:
        parts = ["accuracy", "gpu" if live else "mock"]
        if args.difficulty:
            parts.append(args.difficulty)
        if args.temperature is not None:
            parts.append(f"t{args.temperature}")
        if args.label:
            parts.append(args.label)
        path = reports / ("_".join(parts) + ".json")
    else:
        path = reports / ("accuracy_gpu.json" if live else "accuracy_mock.json")
    summary = copy.deepcopy(out)
    for split in ("development", "holdout"):
        if summary.get(split) and summary[split].get("rows"):
            for row in summary[split]["rows"]:
                if row.get("pass"):
                    row.pop("extraction", None)
    write_json(path, summary)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
