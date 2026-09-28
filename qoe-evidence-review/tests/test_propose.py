"""Tests for qoe.propose: treatment rules in order, amounts, confidence, and the narrative."""

from __future__ import annotations

import re
from typing import Iterable

from qoe.ai_base import AdjustmentIntent, EntryClassification
from qoe.challenge import ChallengeContext, run_challenges
from qoe.money import fmt
from qoe.propose import assess_confidence, compute_proposed, decide_treatment, propose
from qoe.schemas import (
    Account,
    AdjustmentCategory,
    AdjustmentClaim,
    AmountFact,
    DealFiles,
    DealMeta,
    DealPackage,
    DocFacts,
    DocumentPage,
    EbitdaClass,
    EvidenceQuote,
    Flag,
    FlagCode,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PeriodDef,
    Severity,
    SourceDocument,
    Treatment,
)
from qoe.trace import build_index, trace_adjustment

# ---------------------------------------------------------------------------
# In-memory fixture kit
# ---------------------------------------------------------------------------

PERIODS = [
    PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
    PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
    PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06"),
]
LABELS = [p.label for p in PERIODS]
FY24, FY25, TTM = LABELS
ACCOUNTS = {
    "6010": Account(number="6010", name="Officer Compensation", source_type="Expense", ebitda_class=EbitdaClass.OPEX),
    "6150": Account(number="6150", name="Repairs & Maintenance", source_type="Expense", ebitda_class=EbitdaClass.OPEX),
    "6600": Account(number="6600", name="Travel", source_type="Expense", ebitda_class=EbitdaClass.OPEX),
}


def entry(row: int, date: str, account: str, amount: object, cp: str, memo: str, num: str = "") -> GLEntry:
    return GLEntry(
        entry_id=f"GL-R{row}", date=date, period=date[:7], account=account, account_name=ACCOUNTS[account].name,
        txn_type="Bill", doc_number=num, counterparty=cp, memo=memo, amount=fmt(amount), source_file="gl.csv", source_row=row,
    )


def claim(adj_id: str, amounts: Iterable[object], accounts: Iterable[str],
          category: AdjustmentCategory = AdjustmentCategory.NON_RECURRING, refs: Iterable[str] = ()) -> AdjustmentClaim:
    return AdjustmentClaim(
        adj_id=adj_id, title=f"Item {adj_id}", category=category, gl_accounts=list(accounts), support_refs=list(refs),
        amounts={lbl: fmt(a) for lbl, a in zip(LABELS, amounts)}, source_row=9,
    )


def package(entries: list[GLEntry], adj: AdjustmentClaim, texts: dict[str, str] | None = None) -> DealPackage:
    meta = DealMeta(
        deal_id="propose_deal", target_name="Propose Co (SYNTHETIC)", periods=PERIODS, data_start="2024-01", data_end="2026-06",
        files=DealFiles(gl="gl.csv", chart_of_accounts="coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
    )
    docs = [
        SourceDocument(doc_id=k, relpath=f"documents/{k}", media_type="txt", sha256="0" * 64, pages=[DocumentPage(page=1, text=v)])
        for k, v in (texts or {}).items()
    ]
    return DealPackage(
        deal_dir="(memory)", meta=meta, accounts=ACCOUNTS, gl=entries, pl=ManagementPL(source_file="pl.xlsx", months=[], lines=[]),
        schedule=ManagementSchedule(source_file="adj.xlsx", period_labels=LABELS, adjustments=[adj]), documents=docs,
    )


class FakeAI:
    name = "fake"

    def __init__(self, classifications=None, questions=None):
        self.classifications = classifications or []
        self.questions = questions or []

    def extract_facts(self, doc):
        return DocFacts(doc_id=doc.doc_id, doc_type="other")

    def parse_intent(self, adj):
        return AdjustmentIntent(adj_id=adj.adj_id)

    def find_contradictions(self, adj, intent, facts, entries):
        return []

    def classify_entries(self, adj, intent, entries, facts):
        return list(self.classifications)

    def draft_questions(self, adj, flags, facts):
        return list(self.questions)


def traced(pkg: DealPackage, it: AdjustmentIntent, facts: list[DocFacts] = (), ai=None, challenge: bool = True):
    index = build_index(pkg, list(facts))
    t = trace_adjustment(index, pkg.schedule.adjustments[0], it)
    if challenge:
        run_challenges(t, ChallengeContext.build(ai, [t]))
    return t


def amounts(*values: object) -> dict[str, str]:
    return {lbl: fmt(v) for lbl, v in zip(LABELS, values)}


def repairs(*months_amounts: tuple[str, object]) -> list[GLEntry]:
    return [entry(10 + i, f"{m}-10", "6150", a, "Tidewater Restoration", "Storm repair", f"TR-{i}") for i, (m, a) in enumerate(months_amounts)]


REPAIR_INTENT = AdjustmentIntent(adj_id="P-1", counterparties=["Tidewater Restoration"])


def documented_repairs(entries: list[GLEntry], adj: AdjustmentClaim):
    """Each repair invoice has its own document, so NO_DOCUMENT_SUPPORT stays out of the way."""
    texts = {f"inv {e.doc_number}.txt": f"Invoice {e.doc_number}" for e in entries}
    facts = [
        DocFacts(doc_id=f"inv {e.doc_number}.txt", doc_type="invoice", counterparty="Tidewater Restoration", reference_numbers=[e.doc_number])
        for e in entries
    ]
    return package(entries, adj, texts), facts


# ---------------------------------------------------------------------------
# Treatment rules, in order
# ---------------------------------------------------------------------------


def test_accept_when_every_period_is_within_tolerance():
    pkg, facts = documented_repairs(repairs(("2025-03", 10000)), claim("P-1", [0, "10000.60", 0], ["6150"]))
    t = traced(pkg, REPAIR_INTENT, facts)
    a = propose(t)
    assert a.treatment == Treatment.ACCEPT
    assert a.proposed == amounts(0, 10000, 0)  # the GL amount, not management's rounding
    assert a.confidence == "high"
    assert a.rationale.startswith("ACCEPT: the GL and documents support the claim.")


def test_revise_when_part_is_supported_and_reject_when_nothing_is():
    pkg, facts = documented_repairs(repairs(("2025-03", 6000)), claim("P-1", [0, 10000, 0], ["6150"]))
    a = propose(traced(pkg, REPAIR_INTENT, facts))
    assert a.treatment == Treatment.REVISE and a.proposed == amounts(0, 6000, 0)
    assert "claims larger than the GL activity" in a.rationale

    t = traced(pkg, REPAIR_INTENT, facts)
    t.remove(t.claimed_ids(), FlagCode.CONTRADICTORY_EVIDENCE, "test")
    treatment, drivers, reason = decide_treatment(t, compute_proposed(t))
    assert treatment == Treatment.REJECT and drivers == [] and "no part of the claim survives" in reason


def test_pro_forma_not_realized_comes_before_everything_else():
    pkg, facts = documented_repairs(repairs(("2025-03", 10000)), claim("P-1", [0, 10000, 0], ["6150"]))
    t = traced(pkg, REPAIR_INTENT, facts)
    t.add_flag(Flag(code=FlagCode.PRO_FORMA_NOT_REALIZED, severity=Severity.CRITICAL, message="Not realized."))
    treatment, drivers, _ = decide_treatment(t, compute_proposed(t))
    assert treatment == Treatment.REQUEST_INFO and [f.code for f in drivers] == [FlagCode.PRO_FORMA_NOT_REALIZED]
    a = propose(t)
    assert a.proposed == {}
    assert "Provisional amount the evidence would support: FY2024 0 / FY2025 10,000 / TTM Jun-26 0" in a.rationale


def test_no_gl_support_requests_info_unless_a_contradiction_was_raised():
    pkg = package([], claim("P-1", [0, 5000, 0], ["6150"]))
    t = traced(pkg, AdjustmentIntent(adj_id="P-1"))
    assert propose(t).treatment == Treatment.REQUEST_INFO
    t.add_flag(Flag(code=FlagCode.CONTRADICTORY_EVIDENCE, severity=Severity.WARNING, message="Contradicted."))
    treatment, _, _ = decide_treatment(t, compute_proposed(t))
    assert treatment == Treatment.REJECT


def test_undocumented_share_drives_request_info_only_above_the_limit():
    entries = repairs(("2025-03", 8000), ("2025-04", 2000))
    pkg, facts = documented_repairs(entries[:1], claim("P-1", [0, 10000, 0], ["6150"]))
    pkg = pkg.model_copy(update={"gl": entries})
    t = traced(pkg, REPAIR_INTENT, facts)
    (flag,) = [f for f in t.flags if f.code == FlagCode.NO_DOCUMENT_SUPPORT]
    assert flag.severity == Severity.INFO and "20% of the claim" in flag.message
    assert propose(t).treatment == Treatment.ACCEPT


def test_normalization_supported_by_an_executed_agreement_is_computed_not_copied():
    officer = [entry(20 + i, f"2025-{i + 1:02d}-15", "6010", 25000, "J. Varga", "Officer payroll - J. Varga") for i in range(12)]
    text = "Executed employment agreement. Base salary of $220,000 per year. Signed by both parties."
    pkg = package(officer, claim("P-1", [0, 100000, 0], ["6010"], AdjustmentCategory.NORMALIZATION, ["DR 2"]), {"2.1 Employment agreement.txt": text})
    facts = [DocFacts(
        doc_id="2.1 Employment agreement.txt", doc_type="employment_agreement", counterparty="J. Varga", is_signed=True,
        amounts=[AmountFact(label="base_salary", amount="220000",
                            quote=EvidenceQuote(doc_id="2.1 Employment agreement.txt", page=1, quote="Base salary of $220,000 per year."))],
    )]
    it = AdjustmentIntent(adj_id="P-1", counterparties=["J. Varga"], is_normalization=True, normalized_amount="220000")
    a = propose(traced(pkg, it, facts))
    # Actual 300,000 less the executed 220,000 level: 80,000, not management's 100,000.
    assert a.treatment == Treatment.REVISE
    assert a.proposed == amounts(0, 80000, 0)
    assert a.traced_gl == amounts(0, 300000, 0)
    assert any("sets the normalized level at 220,000" in f.text for f in a.facts)
    assert not [f for f in a.flags if f.code == FlagCode.NORMALIZATION_BENCHMARK_MISSING]


def test_normalization_without_an_executed_level_requests_info_with_the_provisional_amount():
    officer = [entry(20 + i, f"2025-{i + 1:02d}-15", "6010", 25000, "J. Varga", "Officer payroll - J. Varga") for i in range(12)]
    pkg = package(officer, claim("P-1", [0, 100000, 0], ["6010"], AdjustmentCategory.NORMALIZATION))
    a = propose(traced(pkg, AdjustmentIntent(adj_id="P-1", counterparties=["J. Varga"], is_normalization=True)))
    assert a.treatment == Treatment.REQUEST_INFO and a.proposed == {}
    assert [f.code for f in a.flags] == [FlagCode.NORMALIZATION_BENCHMARK_MISSING]
    assert "normalized level of 200,000 a year (implied by the claim, not yet supported)" in a.rationale
    assert "FY2025 100,000" in a.rationale


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def test_confidence_levels():
    pkg, facts = documented_repairs(repairs(("2025-03", 6000), ("2025-04", 4000)), claim("P-1", [0, 10000, 0], ["6150"]))
    t = traced(pkg, REPAIR_INTENT, facts)
    p = compute_proposed(t)
    assert assess_confidence(t, Treatment.ACCEPT, p, []) == "high"

    # A doubt that does not set the amount lowers confidence.
    t.add_flag(Flag(code=FlagCode.DUPLICATE_GL_ENTRY, severity=Severity.WARNING, message="Possible duplicate."))
    assert assess_confidence(t, Treatment.ACCEPT, p, []) == "medium"

    # A recurrence or contradiction removal is a judgment: medium.
    t2 = traced(pkg, REPAIR_INTENT, facts)
    first = t2.claimed_ids()[0]
    t2.remove([first], FlagCode.RECURRING_PATTERN, "recurs")
    t2.add_flag(Flag(code=FlagCode.RECURRING_PATTERN, severity=Severity.WARNING, message="Recurs."))
    assert assess_confidence(t2, Treatment.REVISE, compute_proposed(t2), []) == "medium"

    # An AI-only classification behind most of the change: low.
    t3 = traced(pkg, REPAIR_INTENT, facts)
    t3.remove([first], FlagCode.CONTRADICTORY_EVIDENCE, "does not qualify", source="ai")
    assert assess_confidence(t3, Treatment.REVISE, compute_proposed(t3), []) == "low"


def test_ai_classification_needs_a_verified_document_to_remove_anything():
    entries = repairs(("2025-03", 6000), ("2025-04", 4000))
    pkg, facts = documented_repairs(entries, claim("P-1", [0, 10000, 0], ["6150"]))
    ai = FakeAI(classifications=[EntryClassification(entry_id=entries[0].entry_id, qualifies=False, reason="Looks routine.")])
    a = propose(traced(pkg, REPAIR_INTENT, facts, ai=ai), ai)
    assert a.treatment == Treatment.ACCEPT
    assert any("cited no verifiable document" in j for j in a.judgment_questions)


# ---------------------------------------------------------------------------
# Questions, facts, judgment
# ---------------------------------------------------------------------------


def test_open_questions_are_numbered_per_adjustment_and_deduplicated():
    pkg = package([], claim("M-07", [0, 5000, 0], ["6150"]))
    ai = FakeAI(questions=["Please confirm the vendor.", "please confirm the vendor", "  Please confirm   the vendor. "])
    t = traced(pkg, AdjustmentIntent(adj_id="M-07"), ai=ai)
    a = propose(t, ai)
    ids = [q.q_id for q in a.open_questions]
    assert ids == [f"Q-M-07-{n}" for n in range(1, len(ids) + 1)]
    assert all(re.fullmatch(r"Q-M-07-\d+", i) for i in ids)
    no_gl = a.open_questions[0]
    assert no_gl.basis == "NO_GL_SUPPORT" and no_gl.priority == "high"  # it drives REQUEST_INFO
    assert "GL detail" in no_gl.text and "FY2025 5,000" in no_gl.text
    assert [q.basis for q in a.open_questions].count("ai:draft_questions") == 1


def test_facts_are_evidenced_and_kept_apart_from_judgment_questions():
    pkg, facts = documented_repairs(repairs(("2024-03", 6000), ("2025-03", 6000)), claim("P-1", [0, 6000, 0], ["6150"]))
    a = propose(traced(pkg, REPAIR_INTENT, facts))
    assert a.facts and all(f.entry_ids or f.quotes for f in a.facts)
    assert any(f.text.startswith("FY2025: 1 GL entry in 6150") for f in a.facts)
    assert a.judgment_questions and all(j.endswith("?") or "?" in j for j in a.judgment_questions)
    assert not {f.text for f in a.facts} & set(a.judgment_questions)
    # The FY2024 twin is recurring: removed, and the reviewer is asked about it.
    assert a.treatment == Treatment.REJECT and any("ongoing cost base" in j for j in a.judgment_questions)
    link = {x.entry_id: x for x in a.gl_links}["GL-R11"]
    assert link.supports_claim is False and link.reasons[-1].startswith("Removed (RECURRING_PATTERN)")


def test_propose_is_deterministic():
    pkg, facts = documented_repairs(repairs(("2024-03", 6000), ("2025-03", 6000), ("2025-08", 4000)), claim("P-1", [0, 10000, 4000], ["6150"]))
    one = propose(traced(pkg, REPAIR_INTENT, facts)).model_dump_json()
    two = propose(traced(pkg, REPAIR_INTENT, facts)).model_dump_json()
    assert one == two
