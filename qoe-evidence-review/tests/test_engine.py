"""Tests for qoe.engine: orchestration, quote verification, determinism, persistence."""

from __future__ import annotations

import sys
import types
from decimal import Decimal
from pathlib import Path

import pytest

from qoe import TOOL_VERSION
from qoe.ai_base import AdjustmentIntent
from qoe.engine import default_run_id, load_workpaper, review_package, run_review, save_workpaper, verify_doc_facts
from qoe.money import ZERO, D, fmt
from qoe.periods import in_period, month_range
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
    EbitdaComponents,
    EvidenceQuote,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PeriodDef,
    ReconciliationResult,
    SourceDocument,
    TermFact,
    Treatment,
)

REPO = Path(__file__).resolve().parents[1]
MERIDIAN = REPO / "data" / "dev" / "meridian_mechanical"

PERIODS = [
    PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
    PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
    PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06"),
]
LABELS = [p.label for p in PERIODS]
ACCOUNTS = {
    n: Account(number=n, name=name, source_type=typ, ebitda_class=cls)
    for n, name, typ, cls in [
        ("4000", "Service Revenue", "Income", EbitdaClass.REVENUE),
        ("6000", "Salaries & Wages", "Expense", EbitdaClass.OPEX),
        ("6010", "Officer Compensation", "Expense", EbitdaClass.OPEX),
        ("6300", "Software & IT", "Expense", EbitdaClass.OPEX),
        ("6450", "Recruiting", "Expense", EbitdaClass.OPEX),
        ("7000", "Depreciation Expense", "Expense", EbitdaClass.DEPRECIATION),
        ("8100", "Interest Expense", "Other Expense", EbitdaClass.INTEREST),
    ]
}


# ---------------------------------------------------------------------------
# A small deal in memory
# ---------------------------------------------------------------------------


def build_package() -> DealPackage:
    rows: list[GLEntry] = []

    def add(date: str, account: str, amount: object, cp: str = "", memo: str = "", num: str = "") -> None:
        row = len(rows) + 6
        rows.append(GLEntry(entry_id=f"GL-R{row}", date=date, period=date[:7], account=account, account_name=ACCOUNTS[account].name,
                            txn_type="Bill", doc_number=num, counterparty=cp, memo=memo, amount=fmt(amount),
                            source_file="gl/general_ledger.csv", source_row=row))

    for m in month_range("2024-01", "2026-06"):
        add(f"{m}-28", "4000", -200000, "Customers", "Service revenue")
        add(f"{m}-28", "6000", 60000, "", "Payroll - staff")
        add(f"{m}-28", "6010", 25000, "J. Varga", "Officer payroll - J. Varga")
        add(f"{m}-28", "7000", 8000, "", "Monthly depreciation")
        add(f"{m}-28", "8100", 2000, "Bayline Bank", "Loan interest")
    for m in month_range("2025-01", "2026-06"):
        add(f"{m}-05", "6300", 3000, "Nimbus Cloud Systems", "ERP managed services")
    add("2025-04-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 1", "PS-101")
    add("2025-05-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 2", "PS-102")
    add("2025-08-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 3", "PS-103")

    texts = {
        "1.1 Pinecrest engagement letter.txt": "Retained search for a CFO.\nFee of $30,000 payable in three installments.",
        "2.1 Nimbus agreement.txt": "Managed Services Agreement.\nMonthly fee of $3,000 per month.\nRenews automatically.",
        "3.1 Draft employment agreement.txt": "DRAFT\nBase salary of $200,000 per year.",
    }
    docs = [SourceDocument(doc_id=k, relpath=f"documents/{k}", media_type="txt", sha256="0" * 64,
                           pages=[DocumentPage(page=1, text=v)]) for k, v in texts.items()]

    def adj(adj_id, title, amounts, accounts, refs, category=AdjustmentCategory.NON_RECURRING):
        return AdjustmentClaim(adj_id=adj_id, title=title, category=category, gl_accounts=accounts, support_refs=refs,
                               amounts={lbl: fmt(a) for lbl, a in zip(LABELS, amounts)}, source_row=10)

    schedule = ManagementSchedule(
        source_file="adjustments/management_adjusted_ebitda.xlsx",
        period_labels=LABELS,
        reported_ebitda={lbl: fmt(v) for lbl, v in zip(LABELS, (1_380_000, 1_344_000, 1_344_000))},
        adjustments=[
            adj("E-1", "CFO search fee", [0, 20000, 10000], ["6450"], ["DR 1"]),
            adj("E-2", "ERP implementation", [0, 36000, 18000], ["6300"], ["DR 2"]),
            adj("E-3", "Owner compensation normalization", [100000, 100000, 100000], ["6010"], ["DR 3"], AdjustmentCategory.NORMALIZATION),
        ],
    )
    meta = DealMeta(
        deal_id="engine_deal", target_name="Engine Co (SYNTHETIC)", periods=PERIODS, data_start="2024-01", data_end="2026-06",
        files=DealFiles(gl="gl/general_ledger.csv", chart_of_accounts="gl/chart_of_accounts.csv", monthly_pl="financials/monthly_pl.xlsx",
                        adjustments="adjustments/management_adjusted_ebitda.xlsx"),
    )
    return DealPackage(
        deal_dir="(memory)", meta=meta, accounts=ACCOUNTS, gl=rows, pl=ManagementPL(source_file="pl.xlsx", months=[], lines=[]),
        schedule=schedule, documents=docs, input_hashes={"gl/general_ledger.csv": "a" * 64, "adjustments/x.xlsx": "b" * 64},
        ingest_notes=["SYNTHETIC test package"],
    )


def gl_recon(pkg: DealPackage) -> ReconciliationResult:
    """EBITDA from the GL per period label, the way reconcile.py defines it (SPEC §6)."""
    comps = {}
    for p in pkg.meta.periods:
        entries = [e for e in pkg.gl if in_period(e.period, p)]
        by_class = {c: sum((D(e.amount) for e in entries if pkg.accounts[e.account].ebitda_class == c), ZERO) for c in EbitdaClass}
        ni = -sum((D(e.amount) for e in entries), ZERO)
        parts = [by_class[EbitdaClass.INTEREST], by_class[EbitdaClass.TAXES], by_class[EbitdaClass.DEPRECIATION], by_class[EbitdaClass.AMORTIZATION]]
        comps[p.label] = EbitdaComponents(net_income=fmt(ni), interest=fmt(parts[0]), taxes=fmt(parts[1]), depreciation=fmt(parts[2]),
                                          amortization=fmt(parts[3]), ebitda=fmt(ni + sum(parts, ZERO)))
    return ReconciliationResult(items=[], issues=[], gl_ebitda=comps, mgmt_reported_ebitda=dict(pkg.schedule.reported_ebitda),
                                months_compared=30, accounts_compared=len(pkg.accounts), variance_count=0)


def q(doc_id: str, text: str) -> EvidenceQuote:
    return EvidenceQuote(doc_id=doc_id, page=1, quote=text)


class FakeAI:
    name = "fake"

    def __init__(self, fail_on: str = ""):
        self.fail_on = fail_on

    def extract_facts(self, doc):
        if doc.doc_id == self.fail_on:
            raise RuntimeError("unreadable scan")
        if doc.doc_id.startswith("1.1"):
            return DocFacts(
                doc_id=doc.doc_id, doc_type="engagement_letter", counterparty="Pinecrest Search Partners", is_signed=True,
                amounts=[
                    AmountFact(label="total_fee", amount="30000", quote=q(doc.doc_id, "Fee of $30,000")),
                    # Paraphrased, not verbatim: must be dropped and counted.
                    AmountFact(label="installment", amount="10000", quote=q(doc.doc_id, "Three installments of $10,000 each")),
                ],
                key_statements=[q(doc.doc_id, "Retained search for a CFO."), q("2.1 Nimbus agreement.txt", "Monthly fee of $3,000 per month.")],
            )
        if doc.doc_id.startswith("2.1"):
            return DocFacts(
                doc_id=doc.doc_id, doc_type="contract", counterparty="Nimbus Cloud Systems", is_signed=True,
                amounts=[AmountFact(label="monthly_fee", amount="3000", quote=q(doc.doc_id, "Monthly fee of $3,000 per month."))],
                terms=[TermFact(kind="auto_renew", text="renews automatically", quote=q(doc.doc_id, "Renews automatically."))],
            )
        return DocFacts(
            doc_id="wrong-id", doc_type="contract", counterparty="J. Varga", is_draft=True, is_signed=False,
            amounts=[AmountFact(label="base_salary", amount="200000", quote=q(doc.doc_id, "Base salary of $200,000 per year."))],
        )

    def parse_intent(self, adj):
        names = {"E-1": ["Pinecrest Search"], "E-2": ["Nimbus Cloud Systems"], "E-3": ["J. Varga"]}[adj.adj_id]
        return AdjustmentIntent(adj_id="garbled", counterparties=names, asserts_nonrecurring=adj.adj_id != "E-3",
                                is_normalization=adj.adj_id == "E-3")

    def find_contradictions(self, adj, intent, facts, entries):
        return []

    def classify_entries(self, adj, intent, entries, facts):
        return []

    def draft_questions(self, adj, flags, facts):
        return ["Please confirm there are no further fees."] if adj.adj_id == "E-1" else []


RUN = {"run_id": "run-test", "created_at": "2026-09-28T12:00:00+00:00"}


@pytest.fixture(scope="module")
def workpaper():
    pkg = build_package()
    return review_package(pkg, FakeAI(), gl_recon(pkg), **RUN)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def test_review_package_produces_one_assessment_per_adjustment(workpaper):
    wp = workpaper
    assert [a.adj_id for a in wp.assessments] == ["E-1", "E-2", "E-3"]
    by_id = {a.adj_id: a for a in wp.assessments}
    # The search fee is fitted by exact subset (installments 1 and 2 in FY2025).
    assert by_id["E-1"].treatment == Treatment.ACCEPT
    assert by_id["E-2"].treatment == Treatment.REJECT  # an auto-renewing monthly fee is not one-time
    assert by_id["E-3"].treatment == Treatment.REQUEST_INFO and by_id["E-3"].proposed == {}
    assert wp.run_id == "run-test" and wp.created_at == RUN["created_at"]
    assert wp.tool_version == TOOL_VERSION and wp.ai_mode == "fake"
    assert wp.deal.deal_id == "engine_deal"
    assert wp.ingest_notes[0] == "SYNTHETIC test package"
    assert [f.doc_id for f in wp.doc_facts] == sorted(d for d in (f.doc_id for f in wp.doc_facts))


def test_quotes_are_verified_and_failures_dropped_and_counted(workpaper):
    facts = {f.doc_id: f for f in workpaper.doc_facts}
    letter = facts["1.1 Pinecrest engagement letter.txt"]
    assert [a.label for a in letter.amounts] == ["total_fee"]
    assert [s.quote for s in letter.key_statements] == ["Retained search for a CFO."]  # the other cites another document
    assert letter.dropped_quotes == 2
    assert any("1.1 Pinecrest engagement letter.txt: 2 AI quote(s)" in n for n in workpaper.ingest_notes)
    draft = facts["3.1 Draft employment agreement.txt"]
    assert draft.doc_id == "3.1 Draft employment agreement.txt"  # the AI's wrong doc_id is not trusted
    for a in workpaper.assessments:
        for f in a.flags:
            for quote in f.quotes:
                page = next(d for d in build_package().documents if d.doc_id == quote.doc_id).pages[0].text
                assert quote.quote in page


def test_verify_doc_facts_keeps_only_verbatim_quotes():
    doc = SourceDocument(doc_id="x.txt", relpath="documents/x.txt", media_type="txt", sha256="0" * 64,
                         pages=[DocumentPage(page=1, text="Total due $5,000.00")])
    facts = DocFacts(doc_id="x.txt", doc_type="invoice", dropped_quotes=1, amounts=[
        AmountFact(label="total_due", amount="5000", quote=q("x.txt", "Total due $5,000.00")),
        AmountFact(label="total_due", amount="5000", quote=EvidenceQuote(doc_id="x.txt", page=2, quote="Total due $5,000.00")),
    ])
    out = verify_doc_facts(facts, doc, {"x.txt": doc})
    assert len(out.amounts) == 1 and out.dropped_quotes == 2


def test_ai_failures_are_recorded_not_fatal():
    pkg = build_package()
    wp = review_package(pkg, FakeAI(fail_on="2.1 Nimbus agreement.txt"), gl_recon(pkg), **RUN)
    assert any("Fact extraction failed for 2.1 Nimbus agreement.txt: unreadable scan" in n for n in wp.ingest_notes)
    assert len(wp.assessments) == 3


def test_bridge_identity_holds_on_the_workpaper(workpaper):
    rows = {r.key: r for r in workpaper.bridge.rows}
    for lbl in LABELS:
        finals = sum((D(a.proposed[lbl]) for a in workpaper.assessments if a.treatment != Treatment.REQUEST_INFO), ZERO)
        assert D(rows["diligence_adjusted_ebitda"].amounts[lbl]) == D(rows["gl_ebitda"].amounts[lbl]) + finals
    pending = sum((D(a.claimed["FY2025"]) for a in workpaper.assessments if a.treatment == Treatment.REQUEST_INFO), ZERO)
    assert D(rows["pending"].amounts["FY2025"]) == pending == Decimal("100000")


# ---------------------------------------------------------------------------
# Determinism and persistence
# ---------------------------------------------------------------------------


def test_same_inputs_give_byte_identical_workpapers(tmp_path, workpaper):
    pkg = build_package()
    again = review_package(pkg, FakeAI(), gl_recon(pkg), **RUN)
    a = save_workpaper(workpaper, tmp_path / "one")
    b = save_workpaper(again, tmp_path / "two")
    assert a == tmp_path / "one" / "engine_deal" / "workpaper.json"
    assert a.read_bytes() == b.read_bytes()
    text = a.read_text(encoding="utf-8")
    assert text.endswith("\n") and '"run_id": "run-test"' in text
    assert load_workpaper(a) == workpaper


_CROSS_PROCESS = """
import hashlib, sys
sys.path.insert(0, {tests!r})
from test_engine import FakeAI, RUN, build_package, gl_recon
from qoe.engine import review_package, workpaper_json
pkg = build_package()
print(hashlib.sha256(workpaper_json(review_package(pkg, FakeAI(), gl_recon(pkg), **RUN)).encode()).hexdigest())
"""


def test_workpaper_bytes_do_not_depend_on_hash_seed(workpaper):
    """Set iteration order varies between processes; nothing in the output may depend on it."""
    import hashlib
    import os
    import subprocess

    from qoe.engine import workpaper_json

    code = _CROSS_PROCESS.format(tests=str(Path(__file__).parent))
    env = {**os.environ, "PYTHONHASHSEED": "4242"}
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == hashlib.sha256(workpaper_json(workpaper).encode()).hexdigest()


def test_default_run_id_is_content_addressed():
    pkg = build_package()
    assert default_run_id(pkg, "rules") == default_run_id(build_package(), "rules")
    assert default_run_id(pkg, "rules") != default_run_id(pkg, "llm:model")
    changed = pkg.model_copy(update={"input_hashes": {"gl/general_ledger.csv": "c" * 64}})
    assert default_run_id(changed, "rules") != default_run_id(pkg, "rules")
    assert default_run_id(pkg, "rules").startswith("run-")


def test_run_review_wires_ingest_reconcile_and_the_default_ai(monkeypatch, tmp_path):
    pkg = build_package()
    seen: dict[str, object] = {}

    def load_deal(path):
        seen["deal_dir"] = path
        return pkg

    def get_ai(mode="rules"):
        seen["mode"] = mode
        return FakeAI()

    monkeypatch.setitem(sys.modules, "qoe.ingest", types.SimpleNamespace(load_deal=load_deal))
    monkeypatch.setitem(sys.modules, "qoe.reconcile", types.SimpleNamespace(reconcile=gl_recon))
    monkeypatch.setitem(sys.modules, "qoe.ai", types.SimpleNamespace(get_ai=get_ai))
    wp = run_review(tmp_path / "deal", **RUN)
    assert seen == {"deal_dir": tmp_path / "deal", "mode": "rules"}
    assert wp.ai_mode == "fake" and len(wp.assessments) == 3
    assert run_review(tmp_path / "deal", ai=FakeAI()).run_id == default_run_id(pkg, "fake")


# ---------------------------------------------------------------------------
# Integration: the generated dev deal, when present
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not (MERIDIAN / "deal.yaml").exists(), reason="dev deal package not generated")
def test_meridian_dev_deal_runs_end_to_end_and_the_bridge_ties(tmp_path):
    pytest.importorskip("qoe.ingest")
    pytest.importorskip("qoe.reconcile")
    pytest.importorskip("qoe.ai")
    wp = run_review(MERIDIAN, **RUN)
    assert len(wp.assessments) == len({a.adj_id for a in wp.assessments}) > 0
    rows = {r.key: r for r in wp.bridge.rows}
    for lbl in wp.bridge.period_labels:
        finals = sum((D(a.proposed.get(lbl)) for a in wp.assessments if a.treatment != Treatment.REQUEST_INFO), ZERO)
        assert D(rows["diligence_adjusted_ebitda"].amounts[lbl]) == D(rows["gl_ebitda"].amounts[lbl]) + finals
    for a in wp.assessments:
        assert (a.proposed == {}) == (a.treatment == Treatment.REQUEST_INFO)
        assert all(oq.q_id.startswith(f"Q-{a.adj_id}-") for oq in a.open_questions)
    path = save_workpaper(wp, tmp_path)
    assert load_workpaper(path) == wp
