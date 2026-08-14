#!/usr/bin/env python3
"""Evaluate decision accuracy on development and holdout.

Default: MockLLMClient (local).
--live: VLLMLLMClient against VLLM_BASE_URL. Does NOT preseed from expected.json.
Does not tune on holdout. Does not edit expected.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import init_db
from app.llm_client import MockLLMClient, VLLMLLMClient
from app.pipeline import Pipeline, run_case_dir
from app.settings import get_settings
from app.canonicalize import canonicalize_document
from app.pdf_text import extract_pdf_text


FIELD_KEYS = (
    "vendor_name",
    "vendor_id",
    "invoice_number",
    "invoice_date",
    "po_number",
    "currency",
    "subtotal",
    "tax",
    "freight",
    "invoice_total",
    "payment_terms",
)


def invariance_label(negative_control: bool) -> str:
    if negative_control:
        return "off"
    return "on" if os.getenv("VLLM_BATCH_INVARIANT", "1") == "1" else "off"


def field_exact_match(got: Optional[dict], gold: Optional[dict]) -> bool:
    if not got or not gold:
        return False
    for k in FIELD_KEYS:
        if (got.get(k) or None) != (gold.get(k) or None):
            return False
    got_lines = got.get("line_items") or []
    gold_lines = gold.get("line_items") or []
    if len(got_lines) != len(gold_lines):
        return False
    line_keys = ("line_number", "sku", "description", "quantity", "unit_price", "line_total")
    for a, b in zip(got_lines, gold_lines):
        for k in line_keys:
            if a.get(k) != b.get(k):
                return False
    return True


def case_dirs_for(difficulty: Optional[str]) -> dict[str, list[Path]]:
    if difficulty:
        root = REPO / "tests" / "fixtures" / "difficulty" / difficulty
        dev: list[Path] = []
        hold: list[Path] = []
        for case_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")):
            expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
            split = expected.get("split")
            if split == "holdout":
                hold.append(case_dir)
            else:
                dev.append(case_dir)
        return {"development": dev, "holdout": hold}
    return {
        "development": sorted(
            p
            for p in (REPO / "tests" / "fixtures" / "development").iterdir()
            if p.is_dir() and p.name.startswith("case_")
        ),
        "holdout": sorted(
            p
            for p in (REPO / "tests" / "fixtures" / "holdout").iterdir()
            if p.is_dir() and p.name.startswith("case_")
        ),
    }


def init_eval_db(db_url: str, difficulty: Optional[str]) -> None:
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "initialize_database.py"),
        "--reset",
        "--database-url",
        db_url,
    ]
    if difficulty:
        cmd.extend(["--fixture-root", str(REPO / "tests" / "fixtures" / "difficulty" / difficulty)])
    subprocess.check_call(cmd, cwd=str(REPO))


def eval_cases(name: str, cases: list[Path], db_url: str, *, live: bool, llm) -> dict:
    roots = sorted({str(c.parent) for c in cases})
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "initialize_database.py"),
        "--reset",
        "--database-url",
        db_url,
    ]
    for r in roots:
        cmd.extend(["--fixture-root", r])
    subprocess.check_call(cmd, cwd=str(REPO))
    sf = init_db(db_url)
    erp = LocalERPAdapter(sf)

    rows = []
    correct = 0
    total = 0
    schema_valid = 0
    false_ready = 0
    field_match = 0
    for case_dir in cases:
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        gold_extraction = expected.get("extraction") or expected.get("extracted_invoice")
        error = None
        extraction_dump = None
        fields_ok = False
        # Canonical PDF text actually sent to the model (INGEST text-layer output)
        pdf_bytes_for_canon = (case_dir / "invoice.pdf").read_bytes()
        canon_text = canonicalize_document(pdf_bytes_for_canon, extract_pdf_text(pdf_bytes_for_canon).pages).canonical_text
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
                fields_ok = field_exact_match(extraction_dump, gold_extraction)
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
        "field_exact_match": field_match,
        "field_exact_match_rate": (field_match / total) if total else 0.0,
        "false_ready_for_draft": false_ready,
        "rows": rows,
    }


def eval_split(name: str, root: Path, db_url: str, *, live: bool) -> dict:
    """Backward-compatible wrapper used by older callers."""
    cases = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_"))
    if live:
        get_settings.cache_clear()
        llm = VLLMLLMClient()
    else:
        llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    return eval_cases(name, cases, db_url, live=live, llm=llm)


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
        llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")

    splits = case_dirs_for(args.difficulty)
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
    reports.mkdir(exist_ok=True)
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
    summary = json.loads(json.dumps(out))
    for split in ("development", "holdout"):
        if summary.get(split) and summary[split].get("rows"):
            for row in summary[split]["rows"]:
                if row.get("pass"):
                    row.pop("extraction", None)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
