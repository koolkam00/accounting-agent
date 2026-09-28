"""Review orchestration: deal package -> workpaper (SPEC §4-5).

    load_deal -> reconcile -> extract + verify document facts -> parse intent
    -> trace each adjustment -> resolve overlaps -> challenges -> propose -> bridge

``run_review`` works from a deal directory; ``review_package`` does the same
from an in-memory ``DealPackage``. Output is deterministic: the same inputs,
``run_id``, and ``created_at`` give a byte-identical ``workpaper.json``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from qoe import TOOL_VERSION
from qoe.ai_base import AdjustmentIntent, EvidenceAI, verify_quote
from qoe.bridge import build_bridge
from qoe.challenge import ChallengeContext, resolve_overlaps, run_challenges
from qoe.propose import propose
from qoe.schemas import (
    AdjustmentCategory,
    AdjustmentClaim,
    DealPackage,
    DocFacts,
    EvidenceQuote,
    ReconciliationResult,
    SourceDocument,
    Workpaper,
)
from qoe.trace import build_index, trace_adjustment

WORKPAPER_FILENAME = "workpaper.json"


# ---------------------------------------------------------------------------
# AI calls, verified
# ---------------------------------------------------------------------------


def verify_doc_facts(facts: DocFacts, doc: SourceDocument, docs_by_id: dict[str, SourceDocument]) -> DocFacts:
    """Keep only quotes that are verbatim on the cited page of this document; count the rest."""
    dropped = 0

    def ok(q: EvidenceQuote) -> bool:
        nonlocal dropped
        good = q.doc_id == doc.doc_id and verify_quote(q, docs_by_id)
        dropped += 0 if good else 1
        return good

    amounts = [a for a in facts.amounts if ok(a.quote)]
    terms = [t for t in facts.terms if ok(t.quote)]
    statements = [q for q in facts.key_statements if ok(q)]
    return facts.model_copy(
        update={
            "doc_id": doc.doc_id,
            "amounts": amounts,
            "terms": terms,
            "key_statements": statements,
            "dropped_quotes": facts.dropped_quotes + dropped,
        }
    )


def extract_verified_facts(ai: EvidenceAI, docs: list[SourceDocument], notes: list[str]) -> list[DocFacts]:
    docs_by_id = {d.doc_id: d for d in docs}
    out: list[DocFacts] = []
    for doc in sorted(docs, key=lambda d: d.doc_id):
        try:
            raw = ai.extract_facts(doc)
        except Exception as exc:  # one unreadable document must not stop the review
            notes.append(f"Fact extraction failed for {doc.doc_id}: {exc}")
            raw = DocFacts(doc_id=doc.doc_id, doc_type="other", extractor=ai.name)
        facts = verify_doc_facts(raw, doc, docs_by_id)
        if facts.dropped_quotes:
            notes.append(f"{doc.doc_id}: {facts.dropped_quotes} AI quote(s) were not verbatim and were dropped.")
        out.append(facts)
    return out


def _fallback_intent(adj: AdjustmentClaim) -> AdjustmentIntent:
    return AdjustmentIntent(
        adj_id=adj.adj_id,
        asserts_nonrecurring=adj.category == AdjustmentCategory.NON_RECURRING,
        asserts_personal=adj.category == AdjustmentCategory.OWNER_DISCRETIONARY,
        is_pro_forma=adj.category == AdjustmentCategory.PRO_FORMA,
        is_normalization=adj.category == AdjustmentCategory.NORMALIZATION,
    )


def parse_intents(ai: EvidenceAI, adjustments: list[AdjustmentClaim], notes: list[str]) -> list[AdjustmentIntent]:
    out: list[AdjustmentIntent] = []
    for adj in adjustments:
        try:
            intent = ai.parse_intent(adj)
        except Exception as exc:  # fall back to what the schedule's category says
            notes.append(f"Intent parsing failed for {adj.adj_id}: {exc}")
            intent = _fallback_intent(adj)
        if intent.adj_id != adj.adj_id:
            intent = intent.model_copy(update={"adj_id": adj.adj_id})
        out.append(intent)
    return out


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def default_run_id(pkg: DealPackage, ai_name: str) -> str:
    """Content-addressed: the same inputs, tool version, and AI mode give the same id."""
    payload = json.dumps(
        {"deal": pkg.meta.deal_id, "inputs": pkg.input_hashes, "tool": TOOL_VERSION, "ai": ai_name},
        sort_keys=True,
    )
    return "run-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def review_package(
    pkg: DealPackage,
    ai: EvidenceAI,
    recon: Optional[ReconciliationResult] = None,
    run_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Workpaper:
    """Run the engine over an in-memory deal package."""
    if recon is None:
        from qoe.reconcile import reconcile  # lazy: owned by the ingest module

        recon = reconcile(pkg)
    notes = list(pkg.ingest_notes)
    facts = extract_verified_facts(ai, pkg.documents, notes)
    intents = parse_intents(ai, pkg.schedule.adjustments, notes)
    index = build_index(pkg, facts, recon)
    traces = [trace_adjustment(index, adj, intent, order=i) for i, (adj, intent) in enumerate(zip(pkg.schedule.adjustments, intents))]
    resolve_overlaps(traces)
    ctx = ChallengeContext.build(ai, traces)
    for t in traces:
        run_challenges(t, ctx)
    assessments = [propose(t, ai) for t in traces]
    for t in traces:
        notes.extend(f"{t.adj.adj_id}: {n}" for n in t.notes)
    bridge = build_bridge(pkg, recon, pkg.schedule, assessments)
    return Workpaper(
        run_id=run_id or default_run_id(pkg, ai.name),
        tool_version=TOOL_VERSION,
        created_at=created_at or _now_iso(),
        ai_mode=ai.name,
        deal=pkg.meta,
        input_hashes=dict(sorted(pkg.input_hashes.items())),
        ingest_notes=notes,
        reconciliation=recon,
        doc_facts=facts,
        assessments=assessments,
        bridge=bridge,
    )


def run_review(
    deal_dir: Path,
    ai: Optional[EvidenceAI] = None,
    run_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Workpaper:
    """Load a deal directory and review every management adjustment."""
    from qoe.ingest import load_deal  # lazy: owned by the ingest module
    from qoe.reconcile import reconcile

    if ai is None:
        from qoe.ai import get_ai  # lazy: owned by the ai module

        ai = get_ai("rules")
    pkg = load_deal(Path(deal_dir))
    return review_package(pkg, ai, reconcile(pkg), run_id=run_id, created_at=created_at)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def workpaper_json(wp: Workpaper) -> str:
    """Canonical JSON: sorted keys, stable list order, trailing newline."""
    return json.dumps(wp.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def save_workpaper(wp: Workpaper, out_dir: Path) -> Path:
    """Write <out_dir>/<deal_id>/workpaper.json and return its path."""
    path = Path(out_dir) / wp.deal.deal_id / WORKPAPER_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(workpaper_json(wp).encode("utf-8"))
    return path


def load_workpaper(path: Path) -> Workpaper:
    return Workpaper.model_validate_json(Path(path).read_text(encoding="utf-8"))
