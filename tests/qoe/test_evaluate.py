"""Tests for qoe.evaluate scoring, the eval report, and the corrections-to-regressions script.

Unit tests build small in-memory Workpaper / GroundTruth fixtures; the one
integration test over data/qoe/dev skips when the engine or data is absent.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from qoe.evaluate import (
    aggregate,
    build_report,
    entry_row,
    load_ground_truth,
    regression_cases,
    render_markdown,
    score,
    supporting_entry_ids,
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
    ExpectedAdjustment,
    ExpectedDataQuality,
    Flag,
    FlagCode,
    GLLink,
    GroundTruth,
    PeriodDef,
    RecurrenceObservation,
    ReconciliationResult,
    ReviewDecision,
    Severity,
    Treatment,
    Workpaper,
)

ROOT = Path(__file__).resolve().parents[2]
LABELS = ["FY2024", "FY2025"]


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _meta(deal_id: str = "toy_deal") -> DealMeta:
    return DealMeta(
        deal_id=deal_id,
        target_name="Toy Co (SYNTHETIC)",
        periods=[
            PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
            PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
        ],
        data_start="2024-01",
        data_end="2025-12",
        files=DealFiles(
            gl="gl/general_ledger.csv",
            chart_of_accounts="gl/chart_of_accounts.csv",
            monthly_pl="financials/monthly_pl.xlsx",
            adjustments="adjustments/management_adjusted_ebitda.xlsx",
        ),
    )


def _link(row: int, amount: str = "100.00", supports: bool = True, period: str = "2025-03") -> GLLink:
    return GLLink(entry_id=f"GL-R{row}", period=period, amount=amount, score=1.0, supports_claim=supports)


def _flag(code: FlagCode, rows: tuple[int, ...] = (), severity: Severity = Severity.WARNING) -> Flag:
    return Flag(code=code, severity=severity, message=code.value, entry_ids=[f"GL-R{r}" for r in rows])


def _assessment(
    adj_id: str,
    treatment: Treatment,
    proposed: dict[str, str],
    claimed: Optional[dict[str, str]] = None,
    links: tuple[GLLink, ...] = (),
    docs: tuple[str, ...] = (),
    flags: tuple[Flag, ...] = (),
    recurrence: tuple[RecurrenceObservation, ...] = (),
    confidence: str = "high",
) -> AdjustmentAssessment:
    claimed = claimed if claimed is not None else dict(proposed) or {p: "0.00" for p in LABELS}
    return AdjustmentAssessment(
        adj_id=adj_id,
        title=f"Adjustment {adj_id}",
        category=AdjustmentCategory.NON_RECURRING,
        claimed=claimed,
        traced_gl=claimed,
        documented=claimed,
        proposed=proposed,
        treatment=treatment,
        confidence=confidence,
        gl_links=list(links),
        doc_links=[DocLink(doc_id=d, relation="invoice_for_entry", score=1.0) for d in docs],
        flags=list(flags),
        recurrence=list(recurrence),
    )


def _workpaper(
    assessments: list[AdjustmentAssessment],
    issues: tuple[DataQualityIssue, ...] = (),
    gl_ebitda: Optional[dict[str, str]] = None,
    bridge_dil: Optional[dict[str, str]] = None,
    deal_id: str = "toy_deal",
) -> Workpaper:
    gl_ebitda = gl_ebitda or {"FY2024": "10000.00", "FY2025": "20000.00"}
    comps = {
        label: EbitdaComponents(
            net_income=v, interest="0.00", taxes="0.00", depreciation="0.00", amortization="0.00", ebitda=v
        )
        for label, v in gl_ebitda.items()
    }
    rows = [BridgeRow(key="gl_ebitda", label="Reported EBITDA (per GL)", kind="subtotal", amounts=gl_ebitda)]
    if bridge_dil is not None:
        rows.append(
            BridgeRow(
                key="diligence_adjusted_ebitda", label="Diligence adjusted EBITDA", kind="subtotal", amounts=bridge_dil
            )
        )
    return Workpaper(
        run_id="test-run",
        tool_version="0.0.test",
        created_at="2026-01-01T00:00:00Z",
        ai_mode="rules",
        deal=_meta(deal_id),
        input_hashes={"gl/general_ledger.csv": "abc"},
        reconciliation=ReconciliationResult(
            items=[],
            issues=list(issues),
            gl_ebitda=comps,
            mgmt_reported_ebitda={},
            months_compared=24,
            accounts_compared=10,
            variance_count=0,
        ),
        assessments=assessments,
        bridge=EbitdaBridge(period_labels=LABELS, rows=rows),
    )


def _expected(
    adj_id: str,
    treatment: Treatment,
    amounts: dict[str, str],
    case_type: str = "ADEQUATE",
    supporting: tuple[int, ...] = (),
    related: tuple[int, ...] = (),
    docs: tuple[str, ...] = (),
    flags: tuple[FlagCode, ...] = (),
    ambiguity: str = "low",
) -> ExpectedAdjustment:
    return ExpectedAdjustment(
        adj_id=adj_id,
        case_type=case_type,
        treatment=treatment,
        amounts=amounts,
        supporting_gl_rows=list(supporting),
        related_gl_rows=list(related),
        supporting_docs=list(docs),
        expected_flags=list(flags),
        rationale="test",
        ambiguity=ambiguity,
    )


def _gt(
    adjustments: list[ExpectedAdjustment],
    data_quality: tuple[ExpectedDataQuality, ...] = (),
    dil: Optional[dict[str, str]] = None,
    gl: Optional[dict[str, str]] = None,
    deal_id: str = "toy_deal",
) -> GroundTruth:
    return GroundTruth(
        deal_id=deal_id,
        authored_by="test",
        split="dev",
        adjustments=adjustments,
        data_quality=list(data_quality),
        gl_ebitda=gl or {"FY2024": "10000.00", "FY2025": "20000.00"},
        diligence_adjusted_ebitda=dil or {"FY2024": "10000.00", "FY2025": "21000.00"},
    )


def _row(s: dict[str, Any], adj_id: str) -> dict[str, Any]:
    return next(r for r in s["adjustments"] if r["adj_id"] == adj_id)


# The mixed deal: one example of each scoring situation.
#   A-1 exact match            A-2 false accept (missed recurrence)
#   A-3 wrong amount, partial  A-4 REQUEST_INFO on both sides
#   A-5 tool REQUEST_INFO vs REVISE   A-6 not assessed by the tool
#   X-9 tool-only adjustment (unscored, still in the tool's EBITDA)


def _mixed() -> tuple[Workpaper, GroundTruth]:
    tool = [
        _assessment(
            "A-1",
            Treatment.ACCEPT,
            {"FY2024": "0.00", "FY2025": "1000.00"},
            links=(_link(10), _link(11)),
            docs=("inv1.pdf",),
        ),
        _assessment(
            "A-2",
            Treatment.ACCEPT,
            {"FY2024": "0.00", "FY2025": "500.00"},
            links=(_link(20, supports=False, period="2024-12"), _link(21)),
        ),
        _assessment(
            "A-3",
            Treatment.REVISE,
            {"FY2024": "0.00", "FY2025": "750.00"},
            claimed={"FY2024": "0.00", "FY2025": "900.00"},
            links=(_link(30), _link(31), _link(33)),
            docs=("c.pdf", "x.pdf"),
            flags=(_flag(FlagCode.CONTRADICTORY_EVIDENCE, (33,)),),
            confidence="medium",
        ),
        _assessment(
            "A-4",
            Treatment.REQUEST_INFO,
            {},
            claimed={"FY2024": "0.00", "FY2025": "5000.00"},
            flags=(_flag(FlagCode.PRO_FORMA_NOT_REALIZED, severity=Severity.CRITICAL),),
            confidence="low",
        ),
        _assessment(
            "A-5", Treatment.REQUEST_INFO, {}, claimed={"FY2024": "0.00", "FY2025": "400.00"}, links=(_link(50),)
        ),
        _assessment("X-9", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "100.00"}),
    ]
    issues = (
        DataQualityIssue(
            code=DataQualityCode.DUPLICATE_GL_ENTRY,
            severity=Severity.WARNING,
            message="dup",
            account="6200",
            entry_ids=["GL-R70", "GL-R71"],
        ),
        DataQualityIssue(
            code=DataQualityCode.RECON_VARIANCE,
            severity=Severity.WARNING,
            message="var",
            month="2025-11",
            account="6000",
        ),
        DataQualityIssue(
            code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL,
            severity=Severity.WARNING,
            message="gap",
            period_label="FY2025",
        ),
    )
    wp = _workpaper(tool, issues=issues, bridge_dil={"FY2024": "10000.00", "FY2025": "22350.00"})
    gt = _gt(
        [
            _expected(
                "A-1",
                Treatment.ACCEPT,
                {"FY2024": "0.00", "FY2025": "1000.00"},
                supporting=(10, 11),
                docs=("inv1.pdf",),
            ),
            _expected(
                "A-2",
                Treatment.REJECT,
                {"FY2024": "0.00", "FY2025": "0.00"},
                case_type="RECURRING",
                related=(20, 21),
                flags=(FlagCode.RECURRING_PATTERN,),
            ),
            _expected(
                "A-3",
                Treatment.REVISE,
                {"FY2024": "0.00", "FY2025": "800.00"},
                case_type="CONTRADICTED",
                supporting=(30, 31, 32),
                docs=("c.pdf",),
                flags=(FlagCode.CONTRADICTORY_EVIDENCE, FlagCode.CONTINUING_OBLIGATION),
                ambiguity="medium",
            ),
            _expected(
                "A-4", Treatment.REQUEST_INFO, {}, case_type="NEEDS_INFO", flags=(FlagCode.PRO_FORMA_NOT_REALIZED,)
            ),
            _expected(
                "A-5",
                Treatment.REVISE,
                {"FY2024": "0.00", "FY2025": "200.00"},
                case_type="PARTIAL",
                supporting=(50, 51),
            ),
            _expected("A-6", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "300.00"}, supporting=(60,)),
        ],
        data_quality=(
            ExpectedDataQuality(
                code=DataQualityCode.DUPLICATE_GL_ENTRY, month="2025-05", account="6200", gl_rows=[70, 71]
            ),
            ExpectedDataQuality(code=DataQualityCode.RECON_VARIANCE, month="2025-12", account="6000"),
            ExpectedDataQuality(code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL),
        ),
        dil={"FY2024": "10000.00", "FY2025": "22300.00"},
    )
    return wp, gt


# ---------------------------------------------------------------------------
# Unit tests: scoring
# ---------------------------------------------------------------------------


def test_entry_row_parses_convention_only():
    assert entry_row("GL-R42") == 42
    assert entry_row(" GL-R7 ") == 7
    assert entry_row("JE-42") is None
    assert entry_row("GL-Rx") is None


def test_exact_match_scores_perfectly():
    wp = _workpaper(
        [
            _assessment(
                "A-1",
                Treatment.ACCEPT,
                {"FY2024": "0.00", "FY2025": "1000.00"},
                links=(_link(10), _link(11)),
                docs=("inv.pdf",),
            )
        ],
        bridge_dil={"FY2024": "10000.00", "FY2025": "21000.00"},
    )
    gt = _gt(
        [
            _expected(
                "A-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1000.00"}, supporting=(10, 11), docs=("inv.pdf",)
            )
        ]
    )
    s = score(wp, gt)
    for key in (
        "treatment_accuracy",
        "amount_accuracy",
        "gl_link_precision",
        "gl_link_recall",
        "doc_link_precision",
        "doc_link_recall",
    ):
        assert s[key]["rate"] == 1.0, key
    assert s["false_accept_rate"] == {"num": 0, "den": 0, "rate": None, "adj_ids": []}
    assert s["flag_recall"]["den"] == 0
    row = _row(s, "A-1")
    assert row["verdict"] == "PASS"
    assert row["amount_diffs"] == {"FY2024": "0.00", "FY2025": "0.00"}
    e = s["ebitda_error"]
    assert e["max_abs_error"] == "0.00"
    assert e["by_period"]["FY2025"]["tool_diligence_adjusted_ebitda"] == "21000.00"
    assert e["by_period"]["FY2025"]["bridge_matches_proposals"] is True
    assert e["by_period"]["FY2025"]["gl_ebitda_agrees"] is True


def test_mixed_deal_headline_metrics():
    s = score(*_mixed())
    assert s["n_adjustments"] == 6
    assert s["treatment_accuracy"] == {"num": 3, "den": 6, "rate": 0.5}
    # Scored: A-1 (right), A-2 (ACCEPT 500 vs REJECT 0), A-3 (750 vs 800). A-4/A-5 are REQUEST_INFO, A-6 absent.
    assert s["amount_accuracy"] == {"num": 1, "den": 3, "rate": 0.3333}
    # Denominator: the four adjustments the key does not accept (A-2..A-5).
    assert s["false_accept_rate"]["num"] == 1
    assert s["false_accept_rate"]["den"] == 4
    assert s["false_accept_rate"]["adj_ids"] == ["A-2"]
    assert s["verdicts"] == {"FALSE_ACCEPT": 1, "NOT_ASSESSED": 1, "PASS": 2, "WRONG_AMOUNT": 1, "WRONG_TREATMENT": 1}
    assert s["unscored_tool_adjustments"] == ["X-9"]


def test_false_accept_row_detail():
    s = score(*_mixed())
    row = _row(s, "A-2")
    assert row["false_accept"] is True
    assert row["verdict"] == "FALSE_ACCEPT"
    assert row["amount_correct"] is False
    assert row["flags"]["missing"] == ["RECURRING_PATTERN"]
    assert row["missed_challenge_flags"] == ["RECURRING_PATTERN"]


def test_wrong_amount_row_detail():
    row = _row(score(*_mixed()), "A-3")
    assert row["treatment_correct"] is True
    assert row["amount_correct"] is False
    assert row["amount_diffs"] == {"FY2024": "0.00", "FY2025": "-50.00"}
    assert row["verdict"] == "WRONG_AMOUNT"


def test_amount_tolerance_is_one_dollar():
    def run(proposed: str) -> bool:
        wp = _workpaper([_assessment("A-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": proposed})])
        gt = _gt([_expected("A-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "1000.00"})])
        return _row(score(wp, gt), "A-1")["amount_correct"]

    assert run("1001.00") is True
    assert run("998.99") is False
    # A period the key omits counts as zero.
    wp = _workpaper([_assessment("A-1", Treatment.REVISE, {"FY2024": "5.00", "FY2025": "1000.00"})])
    gt = _gt([_expected("A-1", Treatment.REVISE, {"FY2025": "1000.00"})])
    assert _row(score(wp, gt), "A-1")["amount_diffs"]["FY2024"] == "5.00"


def test_gl_link_precision_recall_math():
    s = score(*_mixed())
    # A-1 tp2; A-2 fp1 (row 21); A-3 tp2 fn1 (row 33 removed by the contradiction);
    # A-5 tp1 fn1; A-6 fn1 (not assessed). tp=5 fp=1 fn=3.
    assert s["gl_link_precision"] == {"num": 5, "den": 6, "rate": 0.8333}
    assert s["gl_link_recall"] == {"num": 5, "den": 8, "rate": 0.625}
    a3 = _row(s, "A-3")["gl_links"]
    assert a3["tool_rows"] == [30, 31]
    assert a3["missing_rows"] == [32]
    assert a3["precision"] == 1.0 and a3["recall"] == 0.6667
    a2 = _row(s, "A-2")["gl_links"]
    assert a2["precision"] == 0.0 and a2["recall"] is None
    assert a2["extra_rows"] == [21]


def test_supporting_rule_excludes_removed_and_context_links():
    a = _assessment(
        "A-1",
        Treatment.REVISE,
        {"FY2024": "0.00", "FY2025": "100.00"},
        links=(_link(1), _link(2), _link(3, supports=False), _link(4), _link(5)),
        flags=(
            _flag(FlagCode.RECURRING_PATTERN, (2,)),
            _flag(FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, (4,)),
            # Amount-moving flags leave their entries supporting.
            _flag(FlagCode.OUT_OF_PERIOD, (5,)),
            _flag(FlagCode.OFFSETTING_RECOVERY, (1,)),
        ),
    )
    assert supporting_entry_ids(a) == {"GL-R1", "GL-R5"}


def test_surfaced_recall_counts_flags_and_recurrence():
    a = _assessment(
        "A-1",
        Treatment.REVISE,
        {"FY2024": "-40.00", "FY2025": "100.00"},
        links=(_link(1),),
        flags=(_flag(FlagCode.OFFSETTING_RECOVERY, (7,)),),
        recurrence=(RecurrenceObservation(group="g", amounts_by_period={"FY2024": "36.00"}, entry_ids=["GL-R8"]),),
    )
    wp = _workpaper([a])
    gt = _gt(
        [
            _expected(
                "A-1", Treatment.REVISE, {"FY2024": "-40.00", "FY2025": "100.00"}, supporting=(1,), related=(7, 8, 9)
            )
        ]
    )
    s = score(wp, gt)
    assert s["gl_surfaced_recall"] == {"num": 3, "den": 4, "rate": 0.75}
    assert _row(s, "A-1")["gl_links"]["unsurfaced_rows"] == [9]


def test_empty_link_sets_count_as_correct():
    wp = _workpaper([_assessment("A-1", Treatment.REQUEST_INFO, {})])
    gt = _gt([_expected("A-1", Treatment.REQUEST_INFO, {})])
    gl = _row(score(wp, gt), "A-1")["gl_links"]
    assert gl["precision"] == 1.0 and gl["recall"] == 1.0


def test_doc_link_precision_recall():
    s = score(*_mixed())
    assert s["doc_link_precision"] == {"num": 2, "den": 3, "rate": 0.6667}
    assert s["doc_link_recall"] == {"num": 2, "den": 2, "rate": 1.0}
    assert _row(s, "A-3")["doc_links"]["extra"] == ["x.pdf"]


def test_flag_recall_and_missed_contradictions():
    s = score(*_mixed())
    # Expected: A-2 RECURRING, A-3 CONTRADICTORY + CONTINUING, A-4 PRO_FORMA. Raised correctly: 2.
    assert s["flag_recall"] == {"num": 2, "den": 4, "rate": 0.5}
    mc = s["missed_contradictions"]
    assert (mc["num"], mc["den"]) == (2, 3)
    assert {(i["adj_id"], i["flag"]) for i in mc["items"]} == {
        ("A-2", "RECURRING_PATTERN"),
        ("A-3", "CONTINUING_OBLIGATION"),
    }
    # PRO_FORMA_NOT_REALIZED is not a challenge flag, so it never counts as a missed contradiction.
    wp = _workpaper([_assessment("A-4", Treatment.REQUEST_INFO, {})])
    gt = _gt([_expected("A-4", Treatment.REQUEST_INFO, {}, flags=(FlagCode.PRO_FORMA_NOT_REALIZED,))])
    s2 = score(wp, gt)
    assert s2["missed_contradictions"]["num"] == 0
    assert _row(s2, "A-4")["verdict"] == "MISSED_FLAG"


def test_flag_on_wrong_adjustment_does_not_count():
    wp = _workpaper(
        [
            _assessment("A-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "50.00"}),
            _assessment(
                "A-2",
                Treatment.REVISE,
                {"FY2024": "0.00", "FY2025": "50.00"},
                flags=(_flag(FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT),),
            ),
        ]
    )
    gt = _gt(
        [
            _expected(
                "A-1",
                Treatment.REVISE,
                {"FY2024": "0.00", "FY2025": "50.00"},
                flags=(FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,),
            ),
            _expected("A-2", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "50.00"}),
        ]
    )
    s = score(wp, gt)
    assert s["flag_recall"]["num"] == 0
    assert _row(s, "A-2")["flags"]["unexpected"] == ["OVERLAP_WITH_OTHER_ADJUSTMENT"]


def test_request_info_handling():
    s = score(*_mixed())
    a4, a5, a6 = _row(s, "A-4"), _row(s, "A-5"), _row(s, "A-6")
    assert a4["treatment_correct"] and a4["amount_scored"] is False and a4["amount_correct"] is None
    assert a4["verdict"] == "PASS"
    # A conservative REQUEST_INFO is a wrong treatment, but never a false accept, and has no amount score.
    assert a5["verdict"] == "WRONG_TREATMENT" and a5["false_accept"] is False and a5["amount_scored"] is False
    assert a6["verdict"] == "NOT_ASSESSED" and a6["tool_treatment"] is None
    # Tool ACCEPT where the key wants information is a false accept.
    wp = _workpaper([_assessment("A-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "10.00"})])
    gt = _gt([_expected("A-1", Treatment.REQUEST_INFO, {})])
    s2 = score(wp, gt)
    assert _row(s2, "A-1")["verdict"] == "FALSE_ACCEPT"
    assert s2["amount_accuracy"]["den"] == 0


def test_data_quality_recall():
    dq = score(*_mixed())["data_quality_recall"]
    # Duplicate matched on account + GL rows (issue has no month); variance month differs; EBITDA gap has no locator.
    assert (dq["num"], dq["den"]) == (2, 3)
    assert [i["detected"] for i in dq["items"]] == [True, False, True]


def test_ebitda_error_per_period():
    e = score(*_mixed())["ebitda_error"]
    fy25 = e["by_period"]["FY2025"]
    # GL 20,000 + A-1 1,000 + A-2 500 + A-3 750 + X-9 100 (REQUEST_INFO items excluded).
    assert fy25["tool_diligence_adjusted_ebitda"] == "22350.00"
    assert fy25["abs_error"] == "50.00"
    assert fy25["within_tolerance"] is False
    assert fy25["bridge_matches_proposals"] is True
    assert e["by_period"]["FY2024"]["abs_error"] == "0.00"
    assert e["max_abs_error"] == "50.00"


def test_gl_ebitda_disagreement_reported():
    wp = _workpaper([], gl_ebitda={"FY2024": "10000.00", "FY2025": "19975.00"})
    gt = _gt([], dil={"FY2024": "10000.00", "FY2025": "20000.00"})
    fy25 = score(wp, gt)["ebitda_error"]["by_period"]["FY2025"]
    assert fy25["gl_ebitda_agrees"] is False
    assert fy25["gl_ebitda_diff"] == "-25.00"
    assert fy25["abs_error"] == "25.00"
    assert fy25["bridge_diligence_adjusted_ebitda"] is None


def test_by_case_type_and_confidence():
    s = score(*_mixed())
    assert s["by_case_type"]["ADEQUATE"] == {"num": 1, "den": 2, "rate": 0.5}
    assert s["by_case_type"]["RECURRING"]["rate"] == 0.0
    assert s["by_case_type"]["NEEDS_INFO"]["rate"] == 1.0
    assert s["by_confidence"]["not_assessed"]["den"] == 1


def test_deal_mismatch_raises():
    wp, _ = _mixed()
    with pytest.raises(ValueError):
        score(wp, _gt([], deal_id="other_deal"))


def test_aggregate_pools_counts_across_deals():
    s1 = score(*_mixed())
    wp2 = _workpaper(
        [_assessment("B-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "10.00"}, links=(_link(5),))],
        deal_id="second",
    )
    gt2 = _gt(
        [_expected("B-1", Treatment.REJECT, {"FY2024": "0.00", "FY2025": "0.00"}, supporting=())],
        deal_id="second",
        dil={"FY2024": "10000.00", "FY2025": "20000.00"},
    )
    s2 = score(wp2, gt2)
    o = aggregate([s1, s2])
    assert o["deals"] == ["toy_deal", "second"]
    assert o["n_adjustments"] == 7
    assert o["treatment_accuracy"] == {"num": 3, "den": 7, "rate": 0.4286}
    assert (o["false_accept_rate"]["num"], o["false_accept_rate"]["den"]) == (2, 5)
    assert {"deal_id": "second", "adj_id": "B-1"} in o["false_accept_rate"]["items"]
    assert (o["gl_link_precision"]["num"], o["gl_link_precision"]["den"]) == (5, 7)
    assert o["ebitda_error"]["max_abs_error"] == "50.00"
    assert o["ebitda_error"]["by_deal"]["second"]["FY2025"] == "10.00"
    assert o["data_quality_recall"]["missed"][0]["code"] == "RECON_VARIANCE"


def test_report_json_and_markdown_order():
    report = build_report("dev", [score(*_mixed())], "rules")
    json.dumps(report, sort_keys=True)  # serializable, no Decimals
    md = render_markdown(report)
    order = [
        md.index(h)
        for h in (
            "## 1. False accepts",
            "## 2. Misses",
            "## 3. Headline accuracy",
            "## 4. Per-case",
            "## 5. Treatment accuracy by case type",
        )
    ]
    assert order == sorted(order)
    assert "not practitioner-timed" in md
    assert "SYNTHETIC" in md
    assert "| toy_deal | A-2 | RECURRING | REJECT |" in md
    assert "22,350" in md


def test_load_ground_truth_reads_only_the_answer_key(tmp_path):
    gt = _gt([_expected("A-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1.00"})])
    (tmp_path / "ground_truth.json").write_text(gt.model_dump_json(), encoding="utf-8")
    assert load_ground_truth(tmp_path) == gt
    with pytest.raises(FileNotFoundError):
        load_ground_truth(tmp_path / "missing")


# ---------------------------------------------------------------------------
# Corrections -> regression cases
# ---------------------------------------------------------------------------


def _decision(
    adj_id: str, ctype: CorrectionType, treatment: Treatment, amounts: dict[str, str], tool: AdjustmentAssessment
) -> ReviewDecision:
    return ReviewDecision(
        adj_id=adj_id,
        reviewer="senior.a",
        timestamp="2026-02-01T10:00:00Z",
        treatment=treatment,
        amounts=amounts,
        rationale=f"{ctype.value} on {adj_id}",
        tool_treatment=tool.treatment,
        tool_amounts=dict(tool.proposed),
        correction_type=ctype,
    )


def _review_fixture() -> tuple[Workpaper, list[ReviewDecision]]:
    wp, _ = _mixed()
    by_id = {a.adj_id: a for a in wp.assessments}
    decisions = [
        _decision("A-1", CorrectionType.NONE, Treatment.ACCEPT, by_id["A-1"].proposed, by_id["A-1"]),
        _decision(
            "A-2",
            CorrectionType.TOOL_WRONG_TREATMENT,
            Treatment.REJECT,
            {"FY2024": "0.00", "FY2025": "0.00"},
            by_id["A-2"],
        ),
        _decision(
            "A-3",
            CorrectionType.JUDGMENT_DIFFERENCE,
            Treatment.REVISE,
            {"FY2024": "0.00", "FY2025": "700.00"},
            by_id["A-3"],
        ),
        _decision(
            "A-5",
            CorrectionType.NEW_INFORMATION,
            Treatment.REVISE,
            {"FY2024": "0.00", "FY2025": "200.00"},
            by_id["A-5"],
        ),
        _decision(
            "A-2", CorrectionType.TOOL_WRONG_FLAG, Treatment.REJECT, {"FY2024": "0.00", "FY2025": "0.00"}, by_id["A-2"]
        ),
        _decision(
            "A-3",
            CorrectionType.TOOL_WRONG_AMOUNT,
            Treatment.REVISE,
            {"FY2024": "0.00", "FY2025": "800.00"},
            by_id["A-3"],
        ),
    ]
    return wp, decisions


def test_regression_cases_only_for_tool_errors():
    wp, decisions = _review_fixture()
    cases, summary = regression_cases(wp, decisions, "data/qoe/dev/toy_deal")
    assert [c["case_id"] for c in cases] == ["toy_deal__A-2__1", "toy_deal__A-2__2", "toy_deal__A-3__1"]
    first = cases[0]
    assert first["inputs"] == {
        "deal_dir": "data/qoe/dev/toy_deal",
        "deal_id": "toy_deal",
        "adj_id": "A-2",
        "run_id": "test-run",
        "tool_version": "0.0.test",
        "ai_mode": "rules",
        "input_hashes": {"gl/general_ledger.csv": "abc"},
    }
    assert first["tool_output"]["treatment"] == "ACCEPT"
    assert first["tool_output"]["supporting_gl_rows"] == [21]
    assert first["expected"] == {"treatment": "REJECT", "amounts": {"FY2024": "0.00", "FY2025": "0.00"}}
    assert first["correction_type"] == "TOOL_WRONG_TREATMENT"
    assert first["tool_output_changed_since_review"] is False
    assert first["review_log_line"] == 2
    assert summary["by_correction_type"] == {
        "JUDGMENT_DIFFERENCE": 1,
        "NEW_INFORMATION": 1,
        "NONE": 1,
        "TOOL_WRONG_AMOUNT": 1,
        "TOOL_WRONG_FLAG": 1,
        "TOOL_WRONG_TREATMENT": 1,
    }
    assert [j["adj_id"] for j in summary["judgment_and_new_information"]] == ["A-3", "A-5"]


def _load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_log(path: Path, decisions: list[ReviewDecision]) -> None:
    try:
        from qoe.review_store import ReviewStore
    except ImportError:
        path.write_text("".join(d.model_dump_json() + "\n" for d in decisions), encoding="utf-8")
        return
    store = ReviewStore(path)
    for d in decisions:
        store.append(d)


def test_corrections_script_writes_cases(tmp_path, capsys):
    wp, decisions = _review_fixture()
    wp_dir = tmp_path / "workpapers" / "toy_deal"
    wp_dir.mkdir(parents=True)
    (wp_dir / "workpaper.json").write_text(wp.model_dump_json(indent=2), encoding="utf-8")
    _write_log(wp_dir / "review_log.jsonl", decisions)
    deal_dir = tmp_path / "deal"
    deal_dir.mkdir()
    out = tmp_path / "regressions"

    script = _load_script("qoe_corrections_to_evals")
    assert script.main(["--workpaper-dir", str(wp_dir), "--deal-dir", str(deal_dir), "--out", str(out)]) == 0
    files = sorted(p.name for p in out.glob("*.json"))
    assert files == ["toy_deal__A-2__1.json", "toy_deal__A-2__2.json", "toy_deal__A-3__1.json"]
    case = json.loads((out / "toy_deal__A-3__1.json").read_text())
    assert case["correction_type"] == "TOOL_WRONG_AMOUNT"
    assert case["expected"]["amounts"]["FY2025"] == "800.00"
    assert case["inputs"]["deal_dir"] == deal_dir.resolve().as_posix()
    printed = capsys.readouterr().out
    assert "Tool-error regression cases: 3" in printed
    assert "Judgment differences / new information (not regression cases): 2" in printed

    # Re-running is idempotent: same files, same bytes.
    before = {p.name: p.read_bytes() for p in out.glob("*.json")}
    script.main(["--workpaper-dir", str(wp_dir), "--deal-dir", str(deal_dir), "--out", str(out)])
    assert {p.name: p.read_bytes() for p in out.glob("*.json")} == before


def test_corrections_script_dry_run_writes_nothing(tmp_path, capsys):
    wp, decisions = _review_fixture()
    wp_dir = tmp_path / "wp"
    wp_dir.mkdir()
    (wp_dir / "workpaper.json").write_text(wp.model_dump_json(), encoding="utf-8")
    _write_log(wp_dir / "review_log.jsonl", decisions)
    out = tmp_path / "regressions"
    script = _load_script("qoe_corrections_to_evals")
    assert script.main(["--workpaper-dir", str(wp_dir), "--out", str(out), "--dry-run"]) == 0
    assert not out.exists()
    assert "toy_deal__A-2__1" in capsys.readouterr().out


def _fake_engine(monkeypatch, wp: Workpaper, calls: list[dict[str, Any]]) -> None:
    """Stand-ins for qoe.engine / qoe.ai so the scripts' plumbing is testable before the engine exists."""

    def run_review(deal_dir, ai=None, run_id=None, created_at=None):
        calls.append({"deal_dir": Path(deal_dir), "run_id": run_id, "created_at": created_at, "ai": ai.name})
        return wp

    def save_workpaper(w: Workpaper, out_dir: Path) -> Path:
        path = Path(out_dir) / w.deal.deal_id / "workpaper.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(w.model_dump_json(indent=2), encoding="utf-8")
        return path

    engine = types.ModuleType("qoe.engine")
    engine.run_review = run_review  # type: ignore[attr-defined]
    engine.save_workpaper = save_workpaper  # type: ignore[attr-defined]
    ai = types.ModuleType("qoe.ai")
    ai.get_ai = lambda mode="rules": SimpleNamespace(name=mode)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "qoe.engine", engine)
    monkeypatch.setitem(sys.modules, "qoe.ai", ai)


def test_evaluate_script_writes_reproducible_reports(tmp_path, monkeypatch, capsys):
    wp, gt = _mixed()
    deal = tmp_path / "data" / "dev" / "toy_deal"
    deal.mkdir(parents=True)
    (deal / "deal.yaml").write_text("deal_id: toy_deal\n", encoding="utf-8")
    (deal / "ground_truth.json").write_text(gt.model_dump_json(), encoding="utf-8")
    (tmp_path / "data" / "dev" / "no_key").mkdir()  # no answer key: skipped
    calls: list[dict[str, Any]] = []
    _fake_engine(monkeypatch, wp, calls)
    script = _load_script("qoe_evaluate")
    out = tmp_path / "out"
    argv = ["--split", "dev", "--data-root", str(tmp_path / "data"), "--out", str(out)]
    assert script.main(argv) == 0
    assert [c["deal_dir"].name for c in calls] == ["toy_deal"]
    assert calls[0]["run_id"] == "eval-dev-toy_deal" and calls[0]["created_at"] == script.EVAL_CREATED_AT
    report = json.loads((out / "eval_dev.json").read_text())
    assert report["overall"]["false_accept_rate"]["num"] == 1
    md = (out / "eval_dev.md").read_text()
    assert md.index("False accepts") < md.index("Headline accuracy")
    assert "not practitioner-timed" in capsys.readouterr().out
    first = (out / "eval_dev.json").read_bytes()
    script.main(argv)
    assert (out / "eval_dev.json").read_bytes() == first
    assert script.main(["--split", "holdout", "--data-root", str(tmp_path / "data"), "--out", str(out)]) == 1


def test_run_script_saves_workpaper_and_prints_summary(tmp_path, monkeypatch, capsys):
    wp, _ = _mixed()
    deal = tmp_path / "toy_deal"
    deal.mkdir()
    (deal / "deal.yaml").write_text("deal_id: toy_deal\n", encoding="utf-8")
    calls: list[dict[str, Any]] = []
    _fake_engine(monkeypatch, wp, calls)
    script = _load_script("qoe_run")
    out = tmp_path / "wp"
    argv = ["--deal", str(deal), "--out", str(out), "--run-id", "r1", "--created-at", "2026-01-01T00:00:00Z"]
    assert script.main(argv) == 0
    assert calls[0]["run_id"] == "r1" and calls[0]["created_at"] == "2026-01-01T00:00:00Z"
    assert (out / "toy_deal" / "workpaper.json").is_file()
    printed = capsys.readouterr().out
    assert "Tool treatments:" in printed and "Top flags" in printed
    assert script.main(["--deal", str(tmp_path / "missing"), "--out", str(out)]) == 2


def test_run_summary_renders_without_engine():
    wp, _ = _mixed()
    script = _load_script("qoe_run")
    text = script.summarize(wp)
    assert "Diligence adjusted EBITDA" in text
    assert "A-2" in text and "unreviewed" in text
    assert "CRITICAL A-4" in text


# ---------------------------------------------------------------------------
# Integration (skips until the engine and dev data exist)
# ---------------------------------------------------------------------------


def _first_dev_deal() -> Optional[Path]:
    base = ROOT / "data" / "qoe" / "dev"
    if not base.is_dir():
        return None
    for d in sorted(base.iterdir()):
        if (d / "deal.yaml").is_file() and (d / "ground_truth.json").is_file():
            return d
    return None


def test_integration_score_dev_deal():
    deal_dir = _first_dev_deal()
    if deal_dir is None:
        pytest.skip("no generated dev deal with ground_truth.json")
    engine = pytest.importorskip("qoe.engine")
    ai = pytest.importorskip("qoe.ai")
    wp = engine.run_review(deal_dir, ai=ai.get_ai("rules"), run_id="test-eval", created_at="2026-01-01T00:00:00Z")
    gt = load_ground_truth(deal_dir)
    s = score(wp, gt)
    assert s["n_adjustments"] == len(gt.adjustments)
    assert set(s["ebitda_error"]["by_period"]) == {p.label for p in wp.deal.periods}
    md = render_markdown(build_report("dev", [s], wp.ai_mode))
    assert "## 1. False accepts" in md
