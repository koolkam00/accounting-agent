"""Tests for qoe.review_store (review log, final amounts, bridge rebuild) and the
pure helpers in qoe.ui. Fixtures are small in-memory workpapers; no deal data."""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qoe.money import D, dsum, fmt, period_map
from qoe.review_store import (
    STATUS_AGREED,
    STATUS_OVERRIDDEN,
    STATUS_UNREVIEWED,
    DecisionError,
    ReviewStore,
    append_timing,
    apply_question_updates,
    apply_reviews,
    bridge_ties,
    carry_forward_decision,
    check_bridge_identity,
    corrections_summary,
    decision_is_override,
    decision_is_stale,
    decision_problems,
    encode_question_update,
    final_amounts,
    latest_by_adj,
    load_timing,
    make_decision,
    parse_question_update,
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
    # Accept carries management's claim, which for a diligence item is zero; Reject is zero too.
    accept = make_decision(d1, treatment=Treatment.ACCEPT, amounts={}, correction_type=CorrectionType.JUDGMENT_DIFFERENCE, **kw)
    assert final_amounts(wp, [accept])["D-1"] == _pm("0", "0")
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


def test_carry_forward_decision_keeps_treatment_and_amounts():
    prev = _decision("A-2", Treatment.REVISE, _pm("0", "150"), Treatment.REVISE, _pm("0", "120"), rationale="Retainer excluded.")
    new = carry_forward_decision(prev, reviewer="M. Manager", question_updates={"Q-A-2-1": "CLOSED"}, timestamp="2026-03-01T00:00:00+00:00")
    assert (new.treatment, new.amounts, new.rationale) == (prev.treatment, prev.amounts, prev.rationale)
    assert (new.reviewer, new.question_updates, new.timestamp) == ("M. Manager", {"Q-A-2-1": "CLOSED"}, "2026-03-01T00:00:00+00:00")


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
    info = make_decision(a["A-1"], treatment=Treatment.REQUEST_INFO, amounts={"FY2025": "999"}, **kw)
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
    assert rows["A-2"]["GL links"] == 2 and rows["A-2"]["Docs"] == 1
    assert rows["A-4"]["Bridge"] == "Pending" and rows["A-4"]["Final FY2024"] == "pending"
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
    assert d1["Tool"] == "Revise" and d1["Status"] == STATUS_UNREVIEWED and d1["Bridge"] == "Included"
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
    assert rows[2]["Supports claim"] == "No (context)"


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
    assert any("Recorded Reject for A-2" in s.value for s in at.success)


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
