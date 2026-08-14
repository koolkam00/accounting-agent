#!/usr/bin/env python3
"""Determinism evaluation.

Local PDF/canonical hashes always run.
--live runs a GPU matrix against VLLM_BASE_URL (VLLMLLMClient).
Hashes compare ExtractedInvoice JSON with timestamps/request ids stripped.

In live mode:
- Persist enriched per-repeat records including the extracted invoice JSON,
  canonical PDF text sent to the model, and pipeline decision/exception/control-checks.
- Compute cosmetic vs material split counts and field-level pairwise disagreement
  rates so reviewers can explain hash splits.

Default live matrix is REDUCED (documented) unless --full is passed.
"""

from __future__ import annotations

import argparse
import os
import hashlib
import json
import random
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.canonicalize import canonicalize_document, sha256_bytes
from app.determinism import aggregate_field_disagreements, classify_case_records
from app.pdf_text import extract_pdf_text
from app.schemas import ExtractedInvoice

VOLATILE_KEYS = {
    "timestamp",
    "timestamps",
    "request_id",
    "requestid",
    "created_at",
    "createdat",
    "system_fingerprint",
    "systemfingerprint",
    "response_id",
    "responseid",
    "id",
    "finish_reason",
}


def local_pdf_determinism() -> dict:
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


def strip_volatile(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower().replace("-", "_")
            if kl in VOLATILE_KEYS:
                continue
            out[k] = strip_volatile(v)
        return out
    if isinstance(obj, list):
        return [strip_volatile(x) for x in obj]
    return obj


def extraction_hash(data: dict) -> str:
    payload = json.dumps(strip_volatile(data), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def list_cases(difficulty: str | None = None) -> list[Path]:
    cases: list[Path] = []
    if difficulty:
        root = REPO / "tests" / "fixtures" / "difficulty" / difficulty
        cases.extend(sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")))
        return cases
    for split in ("development", "holdout"):
        root = REPO / "tests" / "fixtures" / split
        cases.extend(sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")))
    return cases


def pairwise_disagreement_rate(records: list[dict]) -> float:
    by_case: dict[str, list[str]] = {}
    for rec in records:
        if rec.get("ok") and rec.get("hash"):
            by_case.setdefault(rec["case_id"], []).append(rec["hash"])
    pairs = 0
    disagree = 0
    for hashes in by_case.values():
        n = len(hashes)
        for i in range(n):
            for j in range(i + 1, n):
                pairs += 1
                if hashes[i] != hashes[j]:
                    disagree += 1
    return (disagree / pairs) if pairs else 0.0


def invariance_label(negative_control: bool) -> str:
    if negative_control:
        return "off"
    return "on" if os.getenv("VLLM_BATCH_INVARIANT", "1") == "1" else "off"


def load_canonical(case_dir: Path) -> str:
    pdf = (case_dir / "invoice.pdf").read_bytes()
    pages = extract_pdf_text(pdf).pages
    return canonicalize_document(pdf, pages).canonical_text


def gpu_matrix_not_executed() -> list[dict]:
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
        {
            "dimension": "negative_control",
            "name": "batch_invariance_disabled_negative_control",
            "status": "NOT_EXECUTED",
            "reason": reason + "; disabling VLLM_BATCH_INVARIANT requires a second server/restart",
        },
    ]


def one_extract(
    llm,
    canonical_text: str,
    case_id: str,
    temperature: float | None = None,
    *,
    erp=None,
    pdf_bytes: bytes | None = None,
    gold_extraction: dict | None = None,
) -> dict:
    t0 = time.perf_counter()
    try:
        extracted = llm.extract_invoice(canonical_text, case_id=case_id, temperature=temperature)
        dump = extracted.model_dump(mode="json")
        rec: dict[str, Any] = {
            "ok": True,
            "hash": extraction_hash(dump),
            "latency_s": time.perf_counter() - t0,
            "error": None,
            "schema_valid": True,
            "extraction": dump,
            "canonical_text": canonical_text,
        }
        # Run VALIDATE→LOOKUP→MATCH via Pipeline with pre-seeded extraction
        if erp is not None and pdf_bytes is not None:
            from app.pipeline import Pipeline

            try:
                seeded = ExtractedInvoice.model_validate(dump)
                result = Pipeline(erp=erp, llm=llm).run(
                    pdf_bytes, case_id=case_id, mode="evaluate", preseeded_extraction=seeded
                )
                rec["decision"] = result.decision.value
                rec["exception_codes"] = result.exception_codes
                rec["control_checks"] = [c.model_dump(mode="json") for c in result.control_checks]
            except Exception as exc2:  # noqa: BLE001
                rec["decision"] = "ERROR"
                rec["exception_codes"] = [f"PIPELINE_ERROR:{type(exc2).__name__}"]
                rec["control_checks"] = []
                rec["pipeline_error"] = f"{type(exc2).__name__}: {exc2}"
        else:
            rec["decision"] = None
            rec["exception_codes"] = []
            rec["control_checks"] = []
        if gold_extraction:
            rec["vs_gold_exact_fields"] = _field_exact_match_like_accuracy(dump, gold_extraction)
        return rec
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "hash": None,
            "latency_s": time.perf_counter() - t0,
            "error": f"{type(exc).__name__}: {exc}",
            "schema_valid": False,
        }


def run_jobs(
    llm,
    jobs: list[dict],
    concurrency: int,
    temperature: float | None = None,
    *,
    erp=None,
    pdf_by_case: dict[str, bytes] | None = None,
    gold_by_case: dict[str, dict] | None = None,
) -> list[dict]:
    """jobs: {case_id, canonical, rep, restart_id} shuffled by caller."""
    out: list[dict] = [None] * len(jobs)  # type: ignore[list-item]
    if concurrency <= 1:
        for i, job in enumerate(jobs):
            cid = job["case_id"]
            r = one_extract(
                llm,
                job["canonical"],
                cid,
                temperature=temperature,
                erp=erp,
                pdf_bytes=pdf_by_case.get(cid) if pdf_by_case else None,
                gold_extraction=gold_by_case.get(cid) if gold_by_case else None,
            )
            out[i] = {**job, **r, "concurrency": concurrency}
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  conc={concurrency} {i+1}/{len(jobs)} ok={r['ok']} hash={r['hash']}")
        return out

    def _work(idx_job):
        idx, job = idx_job
        cid = job["case_id"]
        r = one_extract(
            llm,
            job["canonical"],
            cid,
            temperature=temperature,
            erp=erp,
            pdf_bytes=pdf_by_case.get(cid) if pdf_by_case else None,
            gold_extraction=gold_by_case.get(cid) if gold_by_case else None,
        )
        return idx, {**job, **r, "concurrency": concurrency}

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(_work, (i, job)) for i, job in enumerate(jobs)]
        done = 0
        for fut in as_completed(futs):
            idx, rec = fut.result()
            out[idx] = rec
            done += 1
            if done % 10 == 0 or done == len(jobs):
                print(f"  conc={concurrency} completed {done}/{len(jobs)}")
    return out


def summarize_records(records: list[dict], dimension: str, name: str, extra: dict | None = None) -> dict:
    by_case: dict[str, set[str]] = {}
    errors = 0
    schema_valid = 0
    hashes: set[str] = set()
    latencies = []
    for rec in records:
        if rec.get("ok") and rec.get("hash"):
            by_case.setdefault(rec["case_id"], set()).add(rec["hash"])
            hashes.add(rec["hash"])
            schema_valid += 1
        else:
            errors += 1
        if rec.get("latency_s") is not None:
            latencies.append(rec["latency_s"])
        rec.pop("canonical", None)
    unique_per_case = {cid: sorted(h) for cid, h in sorted(by_case.items())}
    n_nonunique = sum(1 for s in by_case.values() if len(s) != 1)
    summary = {
        "dimension": dimension,
        "name": name,
        "status": "EXECUTED",
        "n_requests": len(records),
        "n_ok": len(records) - errors,
        "n_errors": errors,
        "schema_valid": schema_valid,
        "unique_hashes_global": len(hashes),
        "unique_hashes_per_case": {cid: len(h) for cid, h in unique_per_case.items()},
        "cases_with_more_than_one_hash": n_nonunique,
        "deterministic_per_case": n_nonunique == 0 and errors == 0 and len(by_case) > 0,
        "pairwise_disagreement_rate": pairwise_disagreement_rate(records),
        "first_diverging_token_index": None,
        "first_diverging_token_note": (
            "Not recorded: we hash canonical ExtractedInvoice JSON only, never reasoning traces "
            "or token ids."
        ),
        "latency_s_mean": (sum(latencies) / len(latencies)) if latencies else None,
        "latency_s_p50": (sorted(latencies)[len(latencies) // 2] if latencies else None),
        "hashes_by_case": unique_per_case,
    }
    if extra:
        summary.update(extra)
    return summary


def warmup(llm, canonical_by_case: dict[str, str], n: int = 3, temperature: float | None = None) -> None:
    cases = list(canonical_by_case.items())[:n]
    print(f"warmup {len(cases)} structured-output requests...")
    for cid, text in cases:
        r = one_extract(llm, text, cid, temperature=temperature)
        print(f"  warmup {cid} ok={r['ok']} latency={r['latency_s']:.2f}s err={r['error']}")


def live_matrix(args: argparse.Namespace) -> dict:
    from app.llm_client import VLLMLLMClient, is_gpt_oss, is_qwen3_dense
    from app.settings import get_settings
    from app.database import init_db
    from app.adapters.local_erp import LocalERPAdapter

    get_settings.cache_clear()
    settings = get_settings()
    temp = args.temperature if args.temperature is not None else settings.temperature
    inv = invariance_label(args.negative_control)
    llm = VLLMLLMClient(temperature=temp)
    all_cases = list_cases(args.difficulty)
    if args.cases < len(all_cases):
        all_cases = all_cases[: args.cases]
    canonical_by_case = {p.name: load_canonical(p) for p in all_cases}
    pdf_by_case = {p.name: (p / "invoice.pdf").read_bytes() for p in all_cases}
    gold_by_case: dict[str, dict] = {}
    for p in all_cases:
        exp = json.loads((p / "expected.json").read_text(encoding="utf-8"))
        gold = exp.get("extraction") or exp.get("extracted_invoice")
        if gold:
            gold_by_case[p.name] = gold
    print(
        f"loaded {len(canonical_by_case)} cases for GPU determinism "
        f"model={settings.model_name} temp={temp} difficulty={args.difficulty} invariance={inv}"
    )
    warmup(llm, canonical_by_case, n=min(3, len(canonical_by_case)), temperature=temp)

    rng = random.Random(args.seed)
    gpu_sections: list[dict] = []
    all_records: list[dict] = []
    restart_id = args.restart_id
    # Initialize LocalERP with fixtures for LOOKUP/MATCH
    db_path = REPO / "reports" / f"determinism_eval_{args.difficulty or 'all'}.db"
    sf = init_db(f"sqlite:///{db_path}")
    erp = LocalERPAdapter(sf)
    _load_fixtures_into_local_erp(erp, all_cases)

    # 1. same-request repeatability at concurrency 1
    jobs = []
    for cid, text in canonical_by_case.items():
        for rep in range(args.reps):
            jobs.append({"case_id": cid, "canonical": text, "rep": rep, "restart_id": restart_id})
    rng.shuffle(jobs)
    print(f"same_request conc=1 jobs={len(jobs)} reps={args.reps}")
    recs = run_jobs(
        llm,
        jobs,
        concurrency=1,
        temperature=temp,
        erp=erp,
        pdf_by_case=pdf_by_case,
        gold_by_case=gold_by_case,
    )
    all_records.extend(recs)
    gpu_sections.append(
        summarize_records(
            recs,
            "same_request",
            "same_request_repeatability",
            extra={
                "concurrency": 1,
                "reps": args.reps,
                "n_cases": len(canonical_by_case),
                "restart_id": restart_id,
                "matrix_label": args.label,
                "temperature": temp,
                "difficulty": args.difficulty,
                "invariance": inv,
                "model": settings.model_name,
                "model_revision": settings.model_revision,
                "reasoning_effort": settings.reasoning_effort,
            },
        )
    )

    # 2. concurrency 8 / 32 batch-position mix
    for conc in args.conc:
        if conc <= 1:
            continue
        jobs = []
        for cid, text in canonical_by_case.items():
            for rep in range(args.reps):
                jobs.append({"case_id": cid, "canonical": text, "rep": rep, "restart_id": restart_id})
        rng.shuffle(jobs)
        print(f"batch_position conc={conc} jobs={len(jobs)}")
        recs = run_jobs(
            llm,
            jobs,
            concurrency=conc,
            temperature=temp,
            erp=erp,
            pdf_by_case=pdf_by_case,
            gold_by_case=gold_by_case,
        )
        all_records.extend(recs)
        gpu_sections.append(
            summarize_records(
                recs,
                "batch_invariance",
                f"vllm_batch_invariant_token_stability_conc{conc}",
                extra={
                    "concurrency": conc,
                    "reps": args.reps,
                    "n_cases": len(canonical_by_case),
                    "restart_id": restart_id,
                    "matrix_label": args.label,
                    "temperature": temp,
                    "difficulty": args.difficulty,
                    "invariance": inv,
                    "model": settings.model_name,
                    "model_revision": settings.model_revision,
                    "reasoning_effort": settings.reasoning_effort,
                    "note": f"Server invariance={inv}. Request order shuffled to mix batch positions.",
                },
            )
        )

    # 3. negative control — only if explicitly requested
    if args.negative_control:
        gpu_sections.append(
            {
                "dimension": "negative_control",
                "name": "batch_invariance_disabled_negative_control",
                "status": "EXECUTED",
                "invariance": "off",
                "temperature": temp,
                "difficulty": args.difficulty,
                "model": settings.model_name,
                "note": "Caller asserted VLLM_BATCH_INVARIANT was disabled for this run.",
            }
        )
    else:
        gpu_sections.append(
            {
                "dimension": "negative_control",
                "name": "batch_invariance_disabled_negative_control",
                "status": "NOT_EXECUTED",
                "reason": (
                    "NOT RUN. Disabling VLLM_BATCH_INVARIANT requires a pod restart and a second "
                    "server configuration. This run kept VLLM_BATCH_INVARIANT=1. Do not interpret "
                    "batch-invariant uniqueness as a negative-control result."
                ),
            }
        )

    # restart / cross-machine placeholders for this process; merged later if a second restart file exists
    gpu_sections.append(
        {
            "dimension": "restart",
            "name": "pod_restart_invariance",
            "status": "PARTIAL" if restart_id else "NOT_EXECUTED",
            "restart_id": restart_id,
            "reason": (
                "This process is restart_id="
                f"{restart_id}. Cross-restart comparison is merged by the driver after stop/start."
            ),
        }
    )
    gpu_sections.append(
        {
            "dimension": "cross_machine",
            "name": "cross_machine_invariance",
            "status": "NOT_EXECUTED",
            "reason": "Single RunPod H100 PCIe machine (US-KS-2); no second host rented.",
        }
    )
    gpu_sections.append(
        {
            "dimension": "structured_outputs",
            "name": "vllm_json_schema_xgrammar_stability",
            "status": "EXECUTED",
            "schema_valid_total": sum(1 for r in all_records if r.get("schema_valid")),
            "n_requests": len(all_records),
        }
    )
    if is_qwen3_dense(settings.model_name):
        gpu_sections.append(
            {
                "dimension": "nonthinking",
                "name": "qwen3_nonthinking_extraction_repeatability",
                "status": "EXECUTED",
                "model": settings.model_name,
                "note": "Client extra_body chat_template_kwargs.enable_thinking=false; hashed extraction JSON.",
                "unique_hashes_global": len({r["hash"] for r in all_records if r.get("hash")}),
            }
        )
    elif is_gpt_oss(settings.model_name):
        gpu_sections.append(
            {
                "dimension": "reasoning",
                "name": "gpt_oss_reasoning_effort_low",
                "status": "EXECUTED",
                "model": settings.model_name,
                "reasoning_effort": settings.reasoning_effort,
                "note": (
                    "Client extra_body.reasoning_effort (Harmony top-level). "
                    "Hashed ExtractedInvoice JSON only; message.content parsed, traces ignored."
                ),
                "unique_hashes_global": len({r["hash"] for r in all_records if r.get("hash")}),
            }
        )

    records_path = REPO / "reports" / f"determinism_records_{restart_id or 'r0'}.jsonl"
    with records_path.open("w", encoding="utf-8") as fh:
        for rec in all_records:
            slim = {k: v for k, v in rec.items() if k != "canonical"}
            fh.write(json.dumps(slim, sort_keys=True) + "\n")
    print(f"wrote {records_path} n={len(all_records)}")
    enriched_path = REPO / "reports" / f"determinism_records_enriched_{restart_id or 'r0'}.jsonl"
    with enriched_path.open("w", encoding="utf-8") as fh:
        for rec in all_records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print(f"wrote {enriched_path} n={len(all_records)}")

    # Classification and field-level disagreement rollup across all records
    by_case: dict[str, list[dict]] = {}
    for r in all_records:
        by_case.setdefault(r["case_id"], []).append(r)
    classifs = {cid: classify_case_records(cid, rs) for cid, rs in by_case.items()}
    n_cosmetic = sum(1 for c in classifs.values() if c.classification == "cosmetic")
    n_material = sum(1 for c in classifs.values() if c.classification == "material")
    n_stable = sum(1 for c in classifs.values() if c.classification == "stable")
    n_flips = sum(1 for c in classifs.values() if not c.decision_equal and c.unique_hashes > 0)
    # Aggregate field disagreements on extracted invoices (ok records only)
    extracts_by_case: dict[str, list[dict]] = {}
    for cid, rs in by_case.items():
        exs = [r["extraction"] for r in rs if r.get("ok") and r.get("extraction")]
        if exs:
            extracts_by_case[cid] = exs
    field_rates = aggregate_field_disagreements(extracts_by_case)
    gpu_sections.append(
        {
            "dimension": "classification",
            "name": "cosmetic_vs_material_splits",
            "status": "EXECUTED",
            "n_cases": len(by_case),
            "n_stable": n_stable,
            "n_cosmetic_splits": n_cosmetic,
            "n_material_splits": n_material,
            "n_decision_flips": n_flips,
            "field_pairwise_disagreement_rate": field_rates,
        }
    )
    return {
        "gpu": gpu_sections,
        "gpu_determinism_matrix_executed": True,
        "matrix_label": args.label,
        "restart_id": restart_id,
        "n_records": len(all_records),
        "records_path": str(records_path.relative_to(REPO)),
        "records_path_enriched": str(enriched_path.relative_to(REPO)),
        "temperature": temp,
        "difficulty": args.difficulty,
        "invariance": inv,
        "model": settings.model_name,
        "model_revision": settings.model_revision,
        "reasoning_effort": settings.reasoning_effort,
    }


def _field_exact_match_like_accuracy(got: dict | None, gold: dict | None) -> bool:
    """Exact field match function aligned with evaluate_accuracy.field_exact_match."""
    if not got or not gold:
        return False
    field_keys = (
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
    for k in field_keys:
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


def _load_fixtures_into_local_erp(erp, case_dirs: list[Path]) -> None:
    """Populate the LocalERPAdapter database with fixture data for provided cases."""
    from sqlalchemy.orm import Session
    from app.database import (
        VendorRow,
        PurchaseOrderRow,
        POLineRow,
        ReceiptRow,
        ReceiptLineRow,
        DuplicateSeedRow,
    )

    vendors = [
        {"vendor_id": "V001", "vendor_name": "Northwind Office Supply LLC", "active": True, "ap_account": "2000"},
        {"vendor_id": "V002", "vendor_name": "Cedar Ridge Industrial Parts", "active": True, "ap_account": "2000"},
        {"vendor_id": "V003", "vendor_name": "Blue Harbor Packaging Co", "active": True, "ap_account": "2000"},
        {"vendor_id": "V004", "vendor_name": "Summit Ridge Labware Inc", "active": True, "ap_account": "2000"},
        {"vendor_id": "V005", "vendor_name": "Pinecrest Facilities Goods", "active": True, "ap_account": "2000"},
        {"vendor_id": "V006", "vendor_name": "Harbor Closed Supply LLC", "active": False, "ap_account": "2000"},
    ]
    with erp._sf() as session:  # type: ignore[attr-defined]
        assert isinstance(session, Session)
        for v in vendors:
            if session.get(VendorRow, v["vendor_id"]) is None:
                session.add(VendorRow(**v))
        session.commit()
        for case_dir in case_dirs:
            po = json.loads((case_dir / "po.json").read_text(encoding="utf-8"))
            receipt = json.loads((case_dir / "receipt.json").read_text(encoding="utf-8"))
            expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
            if session.get(PurchaseOrderRow, po["po_id"]) is None:
                session.add(
                    PurchaseOrderRow(
                        po_id=po["po_id"],
                        vendor_id=po["vendor_id"],
                        vendor_name=po["vendor_name"],
                        currency=po["currency"],
                        status=po["status"],
                    )
                )
                session.flush()
                for ln in sorted(po["lines"], key=lambda x: x["line_number"]):
                    session.add(
                        POLineRow(
                            po_id=po["po_id"],
                            line_number=ln["line_number"],
                            sku=ln["sku"],
                            description=ln["description"],
                            quantity=ln["quantity"],
                            unit_price=ln["unit_price"],
                            gl_account=ln["gl_account"],
                        )
                    )
            if session.get(ReceiptRow, receipt["receipt_id"]) is None:
                session.add(ReceiptRow(receipt_id=receipt["receipt_id"], po_id=receipt["po_id"]))
                session.flush()
                for ln in receipt["lines"]:
                    session.add(
                        ReceiptLineRow(
                            receipt_id=receipt["receipt_id"],
                            sku=ln["sku"],
                            quantity_received=ln["quantity_received"],
                        )
                    )
            already = expected.get("already_processed")
            if already:
                exists = (
                    session.query(DuplicateSeedRow)
                    .filter_by(
                        vendor_id=already["vendor_id"],
                        invoice_number=already["invoice_number"],
                    )
                    .first()
                )
                if exists is None:
                    session.add(
                        DuplicateSeedRow(
                            vendor_id=already["vendor_id"],
                            invoice_number=already["invoice_number"],
                        )
                    )
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate extraction determinism.\n"
            "Live mode writes two record files:\n"
            "  reports/determinism_records_<restart>.jsonl (legacy hash/ok/latency/schema fields),\n"
            "  reports/determinism_records_enriched_<restart>.jsonl (adds extraction JSON, canonical text, "
            "pipeline decision/exception/control-checks, and vs-gold flags when available).\n"
            "Summaries now include cosmetic vs material split counts and field-level pairwise disagreement rates."
        )
    )
    parser.add_argument("--live", action="store_true", help="Run GPU live matrix (VLLMLLMClient)")
    parser.add_argument("--reps", type=int, default=5)
    parser.add_argument("--cases", type=int, default=50)
    parser.add_argument("--conc", type=int, nargs="*", default=[8])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--restart-id", default="r0")
    parser.add_argument("--label", default="REDUCED", help="Label to include in summary files")
    parser.add_argument(
        "--negative-control",
        action="store_true",
        help="Record invariance=off (caller must have started vLLM with VLLM_BATCH_INVARIANT=0)",
    )
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default=None)
    parser.add_argument(
        "--merge-records",
        nargs="*",
        default=None,
        help="Merge jsonl records across restarts for restart-invariance comparison",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "local": [local_pdf_determinism()],
        "gpu": gpu_matrix_not_executed(),
        "gpu_determinism_matrix_executed": False,
        "gpu_spend_usd": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    if args.live:
        live = live_matrix(args)
        report.update(live)

    if args.merge_records:
        # Merge jsonl record files across restarts for restart-invariance
        merged: list[dict] = []
        for p in args.merge_records:
            path = Path(p)
            if not path.is_absolute():
                path = REPO / path
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    merged.append(json.loads(line))
        by_case: dict[str, dict[str, set[str]]] = {}
        for rec in merged:
            if rec.get("hash"):
                by_case.setdefault(rec["case_id"], {}).setdefault(str(rec.get("restart_id")), set()).add(rec["hash"])
        restart_cmp = {
            cid: {rid: sorted(hs) for rid, hs in rids.items()} for cid, rids in sorted(by_case.items())
        }
        n_mismatch = 0
        for cid, rids in restart_cmp.items():
            union = set()
            for hs in rids.values():
                union.update(hs)
            if len(union) > 1:
                n_mismatch += 1
        # replace restart section
        gpu = [g for g in report.get("gpu", []) if g.get("dimension") != "restart"]
        gpu.append(
            {
                "dimension": "restart",
                "name": "pod_restart_invariance",
                "status": "EXECUTED",
                "n_cases": len(restart_cmp),
                "cases_with_hash_change_across_restarts": n_mismatch,
                "restart_ids": sorted({str(r.get("restart_id")) for r in merged}),
                "hashes_by_case_by_restart": restart_cmp,
            }
        )
        report["gpu"] = gpu

    ok = all(x.get("pass", True) for x in report["local"])
    path = REPO / "reports" / "determinism.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"local_pass": ok, "gpu_executed": report.get("gpu_determinism_matrix_executed")}, indent=2))
    print(f"wrote {path}")
    for g in report.get("gpu", []):
        print(f"{g.get('status')} [{g.get('dimension')}]: {g.get('name')} unique_global={g.get('unique_hashes_global')} n={g.get('n_requests')}")


if __name__ == "__main__":
    main()
