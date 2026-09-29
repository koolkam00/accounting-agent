"""Tests for qoe.evaluate scoring, the eval report, and the corrections-to-regressions script.

Unit tests build small in-memory Workpaper / GroundTruth fixtures; the one
integration test over data/dev skips when the engine or data is absent.
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
    CASE_TYPES,
    aggregate,
    build_report,
    entry_row,
    load_ground_truth,
    match_diligence_items,
    normalize_case_type,
    regression_cases,
    render_markdown,
    score,
    supporting_entry_ids,
    surfaced_doc_ids,
    tool_supporting_docs,
)
from qoe.schemas import (
    AdjustmentAssessment,
    AdjustmentCategory,
    AdjustmentClaim,
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
    ManagementSchedule,
    OpenQuestion,
    PeriodDef,
    QuestionStatus,
    RecurrenceObservation,
    ReconciliationResult,
    ReviewDecision,
    Severity,
    Treatment,
    Workpaper,
)

ROOT = Path(__file__).resolve().parents[1]
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
        # Like the engine: each document is linked to the claimed entries it evidences.
        doc_links=[
            DocLink(
                doc_id=d,
                relation="invoice_for_entry",
                entry_ids=[lk.entry_id for lk in links if lk.supports_claim],
                score=1.0,
            )
            for d in docs
        ],
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


def _doc(doc_id: str, rows: tuple[int, ...] = (), relation: str = "invoice_for_entry") -> DocLink:
    return DocLink(doc_id=doc_id, relation=relation, entry_ids=[f"GL-R{r}" for r in rows], score=1.0)


def _flag_docs(code: FlagCode, rows: tuple[int, ...], docs: tuple[str, ...]) -> Flag:
    return Flag(
        code=code,
        severity=Severity.WARNING,
        message=code.value,
        entry_ids=[f"GL-R{r}" for r in rows],
        doc_ids=list(docs),
    )


def test_tool_supporting_docs_follow_what_is_carried():
    # Carried non-zero (REVISE): documents on supporting entries, stand-alone agreements no removing
    # flag cites, and the recovery document; not the documents that argued part of the claim away.
    revise = _assessment(
        "A-1",
        Treatment.REVISE,
        {"FY2024": "58.00", "FY2025": "-40.00"},
        claimed={"FY2024": "58.00", "FY2025": "0.00"},
        links=(_link(1), _link(2), _link(3), _link(9, supports=False)),
        flags=(
            _flag_docs(FlagCode.CONTRADICTORY_EVIDENCE, (3,), ("trip report.pdf",)),
            _flag_docs(FlagCode.CONTINUING_OBLIGATION, (), ("retainer letter.pdf",)),
            _flag_docs(FlagCode.OFFSETTING_RECOVERY, (9,), ("settlement letter.pdf",)),
        ),
    ).model_copy(
        update={
            "doc_links": [
                _doc("invoice 1.pdf", (1,)),
                _doc("statement.pdf", (2, 3)),  # evidences a carried entry, even if it also covers a removed one
                _doc("trip report.pdf", (3,)),
                _doc("engagement letter.pdf", (), "agreement"),
                _doc("retainer letter.pdf", (), "agreement"),
                _doc("settlement letter.pdf", (9,), "recovery"),
                _doc("email.txt", (), "correspondence"),
            ]
        }
    )
    assert tool_supporting_docs(revise) == {
        "invoice 1.pdf",
        "statement.pdf",
        "engagement letter.pdf",
        "settlement letter.pdf",
    }
    assert surfaced_doc_ids(revise) >= {"trip report.pdf", "retainer letter.pdf", "email.txt"}

    # Carried zero (REJECT): the documents the rejection rests on.
    reject = _assessment(
        "A-2",
        Treatment.REJECT,
        {"FY2024": "0.00", "FY2025": "0.00"},
        claimed={"FY2024": "0.00", "FY2025": "96.00"},
        links=(_link(20), _link(21), _link(22, supports=False)),
        flags=(
            _flag(FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, (20,)),
            _flag_docs(FlagCode.CONTRADICTORY_EVIDENCE, (21,), ("controller email.txt",)),
        ),
    ).model_copy(
        update={
            "doc_links": [
                _doc("payoff letter.pdf", (20,), "other"),
                _doc("controller email.txt", (), "correspondence"),
                _doc("comparable invoice.pdf", (22,)),
            ]
        }
    )
    assert tool_supporting_docs(reject) == {"payoff letter.pdf", "controller email.txt"}

    # Pending (REQUEST_INFO): what the request rests on.
    pending = _assessment(
        "A-3",
        Treatment.REQUEST_INFO,
        {},
        claimed={"FY2024": "360.00", "FY2025": "360.00"},
        flags=(_flag_docs(FlagCode.UNSIGNED_OR_DRAFT_SUPPORT, (), ("draft agreement.pdf",)),),
    ).model_copy(update={"doc_links": [_doc("draft agreement.pdf", (), "agreement"), _doc("memo.txt", (), "other")]})
    assert tool_supporting_docs(pending) == {"draft agreement.pdf"}


def test_doc_scores_use_supporting_and_related_docs():
    a = _assessment(
        "A-1",
        Treatment.REVISE,
        {"FY2024": "0.00", "FY2025": "31.00"},
        claimed={"FY2024": "0.00", "FY2025": "48.00"},
        links=(_link(1), _link(2)),
        flags=(_flag_docs(FlagCode.CONTRADICTORY_EVIDENCE, (2,), ("expense report.pdf",)),),
    ).model_copy(update={"doc_links": [_doc("lease.pdf", (1,)), _doc("expense report.pdf", (2,))]})
    exp = _expected("A-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "31.00"}, supporting=(1,))
    exp = exp.model_copy(
        update={"supporting_docs": ["lease.pdf", "club statement.pdf"], "related_docs": ["expense report.pdf"]}
    )
    s = score(_workpaper([a]), _gt([exp]))
    docs = _row(s, "A-1")["doc_links"]
    assert (docs["tool"], docs["missing"], docs["extra"]) == (["lease.pdf"], ["club statement.pdf"], [])
    assert s["doc_link_precision"]["rate"] == 1.0 and s["doc_link_recall"]["rate"] == 0.5
    # Surfaced: lease and expense report are shown; the club statement is not.
    assert s["doc_surfaced_recall"] == {"num": 2, "den": 3, "rate": 0.6667}
    assert docs["unsurfaced"] == ["club statement.pdf"]


# Diligence-identified items (SPEC §5.7): a duplicate posting at rows 4464 / 4465.


def _dup_item(adj_id: str, reversed_row: int, kept_row: int, amount: str = "18400.00", **kw: Any):
    a = _assessment(
        adj_id,
        kw.pop("treatment", Treatment.REVISE),
        {"FY2024": "0.00", "FY2025": amount},
        claimed={"FY2024": "0.00", "FY2025": "0.00"},
        links=(_link(kept_row, "18400.00", supports=False, period="2025-05"), _link(reversed_row, "18400.00", period="2025-05")),
        flags=(_flag(FlagCode.DUPLICATE_GL_ENTRY, (kept_row, reversed_row)),),
    )
    return a.model_copy(update={"source": "diligence", "title": f"Reverse duplicate posting ({adj_id})", **kw})


def _expected_dup(adj_id: str = "D-1") -> ExpectedAdjustment:
    e = _expected(
        adj_id,
        Treatment.REVISE,
        {"FY2024": "0.00", "FY2025": "18400.00"},
        case_type="DUPLICATE_POSTING",
        supporting=(4465,),
        related=(4464,),
        flags=(FlagCode.DUPLICATE_GL_ENTRY,),
    )
    return e.model_copy(update={"supporting_docs": ["premium notice.pdf"]})


def _with_diligence(tool_items: list[AdjustmentAssessment], expected_items: list[ExpectedAdjustment]):
    mgmt = _assessment("A-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1000.00"}, links=(_link(10),))
    wp = _workpaper([mgmt, *tool_items])
    gt = _gt(
        [_expected("A-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1000.00"}, supporting=(10,))],
        dil={"FY2024": "10000.00", "FY2025": "39400.00"},
    )
    return wp, gt.model_copy(update={"diligence_items": expected_items})


def test_diligence_items_are_scored_apart_from_management_items():
    extra = _dup_item("D-2", 5001, 5000, amount="700.00")
    wp, gt = _with_diligence([_dup_item("D-1", 4465, 4464), extra], [_expected_dup(), _expected_dup("D-9")])
    gt = gt.model_copy(
        update={"diligence_items": [_expected_dup(), _expected_dup("D-9").model_copy(update={"supporting_gl_rows": [900]})]}
    )
    s = score(wp, gt)
    # Management metrics see A-1 only.
    assert s["n_adjustments"] == 1 and s["treatment_accuracy"] == {"num": 1, "den": 1, "rate": 1.0}
    assert s["gl_link_precision"] == {"num": 1, "den": 1, "rate": 1.0}
    assert s["unscored_tool_adjustments"] == []
    di = s["diligence_item_accuracy"]
    # D-1 correct; D-9 missed; D-2 extra (counts against accuracy).
    assert (di["num"], di["den"], di["expected"], di["tool"], di["matched"]) == (1, 3, 2, 2, 1)
    assert di["missed"] == ["D-9"] and di["extra"] == ["D-2"]
    items = {(r["key_id"], r["tool_id"]): r for r in di["items"]}
    d1 = items[("D-1", "D-1")]
    assert d1["verdict"] == "CORRECT" and d1["match_basis"] == "supporting_rows"
    assert d1["amount_diffs"] == {"FY2024": "0.00", "FY2025": "0.00"}
    assert d1["gl_links"]["tool_rows"] == [4465] and d1["gl_links"]["surfaced"]["rate"] == 1.0
    assert d1["flags"]["missing"] == []
    assert items[("D-9", None)]["verdict"] == "MISSED"
    assert items[(None, "D-2")]["verdict"] == "EXTRA" and items[(None, "D-2")]["tool_rows"] == [5001]
    # The EBITDA identity carries the diligence items: 20,000 + 1,000 + 18,400 + 700.
    fy25 = s["ebitda_error"]["by_period"]["FY2025"]
    assert fy25["tool_management_adjustments"] == "1000.00"
    assert fy25["tool_diligence_items"] == "19100.00"
    assert fy25["expected_diligence_items"] == "36800.00"
    assert fy25["tool_diligence_adjusted_ebitda"] == "40100.00"
    assert fy25["abs_error"] == "700.00"


def test_diligence_item_wrong_amount_and_other_posting_match():
    # The tool reversed the first posting instead of the second: same item, matched on a shared GL row.
    other = _dup_item("D-1", 4464, 4465)
    s = score(*_with_diligence([other], [_expected_dup()]))
    item = s["diligence_item_accuracy"]["items"][0]
    assert (item["tool_id"], item["match_basis"], item["verdict"]) == ("D-1", "linked_rows", "CORRECT")
    assert item["gl_links"]["extra_rows"] == [4464]
    # A wrong amount is matched but not correct; REQUEST_INFO carries nothing.
    wrong = _dup_item("D-1", 4465, 4464, amount="36800.00")
    item = score(*_with_diligence([wrong], [_expected_dup()]))["diligence_item_accuracy"]["items"][0]
    assert item["verdict"] == "WRONG_AMOUNT" and item["amount_diffs"]["FY2025"] == "18400.00"
    pending = _dup_item("D-1", 4465, 4464, treatment=Treatment.REQUEST_INFO, proposed={})
    item = score(*_with_diligence([pending], [_expected_dup()]))["diligence_item_accuracy"]["items"][0]
    assert item["verdict"] == "WRONG_AMOUNT" and item["amount_diffs"]["FY2025"] == "-18400.00"
    # No expected items and none proposed: nothing to score.
    none = score(*_with_diligence([], []))["diligence_item_accuracy"]
    assert (none["num"], none["den"], none["rate"]) == (0, 0, None)


def test_diligence_items_one_to_one_matching():
    first = _dup_item("D-1", 4465, 4464)
    second = _dup_item("D-2", 4465, 4464)
    pairs = match_diligence_items([_expected_dup()], [first, second])
    assert pairs == [(0, 0, "supporting_rows")]


def test_diligence_items_in_report_and_aggregate():
    s1 = score(*_mixed())
    wp, gt = _with_diligence([_dup_item("D-1", 4465, 4464, amount="9200.00")], [_expected_dup()])
    s2 = score(wp.model_copy(update={"deal": _meta("second")}), gt.model_copy(update={"deal_id": "second"}))
    o = aggregate([s1, s2])
    assert o["n_diligence_items"] == 1
    assert o["diligence_item_accuracy"]["den"] == 1 and o["diligence_item_accuracy"]["num"] == 0
    assert o["diligence_item_accuracy"]["items"][0]["deal_id"] == "second"
    assert o["doc_surfaced_recall"]["den"] >= 1
    md = render_markdown(build_report("dev", [s1, s2], "rules"))
    assert md.index("## 1. False accepts") < md.index("### Diligence-identified items") < md.index("## 3. Headline")
    assert "| second | D-1 | D-1 | supporting rows | 0 / 18,400 | 0 / 9,200 | - | WRONG_AMOUNT |" in md
    assert "| Diligence item accuracy | 0.0% | 0/1 |" in md
    assert "Doc P / R" in md


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


# -- false accepts vs missed revisions (SPEC §9) -------------------------------


def test_accept_on_understated_item_is_a_missed_revision_not_a_false_accept():
    wp = _workpaper(
        [
            # Key revises upward (the claim is understated): accepting leaves EBITDA low, not high.
            _assessment("U-1", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1000.00"}),
            # Key rejects a negative claim: accepting it understates EBITDA too.
            _assessment("U-2", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "-500.00"}),
            # Key revises down in one period only: accepting overstates that period.
            _assessment("O-1", Treatment.ACCEPT, {"FY2024": "300.00", "FY2025": "1000.00"}),
            # Within the 1.00 tolerance of the key: not an overstatement.
            _assessment("U-3", Treatment.ACCEPT, {"FY2024": "0.00", "FY2025": "1000.90"}),
            # The tool challenged it, so no ACCEPT error; its claim still puts it in the false-accept population.
            _assessment("O-2", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "600.00"},
                        claimed={"FY2024": "0.00", "FY2025": "900.00"}),
        ]
    )
    gt = _gt(
        [
            _expected("U-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "1200.00"}, case_type="UNDERSTATED"),
            _expected("U-2", Treatment.REJECT, {"FY2024": "0.00", "FY2025": "0.00"}, case_type="SIGN_ERROR"),
            _expected("O-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "1000.00"}, case_type="WRONG_PERIOD"),
            _expected("U-3", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "1000.00"}),
            _expected("O-2", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "600.00"}),
        ]
    )
    s = score(wp, gt)
    assert (s["false_accept_rate"]["num"], s["false_accept_rate"]["den"]) == (1, 2)
    assert s["false_accept_rate"]["adj_ids"] == ["O-1"]
    assert (s["missed_revisions"]["num"], s["missed_revisions"]["den"]) == (3, 3)
    assert s["missed_revisions"]["adj_ids"] == ["U-1", "U-2", "U-3"]
    o1, u1 = _row(s, "O-1"), _row(s, "U-1")
    assert o1["verdict"] == "FALSE_ACCEPT" and o1["overstated_periods"] == ["FY2024"]
    assert u1["verdict"] == "MISSED_REVISION" and u1["false_accept"] is False and u1["missed_revision"] is True
    assert _row(s, "O-2")["accept_overstates"] is True and _row(s, "O-2")["verdict"] == "PASS"

    o = aggregate([s])
    assert o["missed_revisions"]["items"] == [{"deal_id": "toy_deal", "adj_id": a} for a in ("U-1", "U-2", "U-3")]
    md = render_markdown(build_report("dev", [s], "rules"))
    assert md.index("## 1. False accepts") < md.index("### Missed revisions (3 of 3") < md.index("## 3. Headline")
    fa_section = md[md.index("## 1. False accepts"): md.index("## 2. Misses")]
    assert "| toy_deal | O-1 |" in fa_section and "| toy_deal | U-1 |" not in fa_section
    assert "| Missed revisions | 100.0% | 3/3 |" in md


def test_false_accept_population_uses_the_schedule_claim_for_unassessed_items():
    schedule = ManagementSchedule(
        source_file="adjustments/schedule.xlsx",
        period_labels=LABELS,
        adjustments=[
            AdjustmentClaim(adj_id="N-1", title="Understated", amounts={"FY2024": "0.00", "FY2025": "100.00"},
                            source_row=5),
        ],
    )
    wp = _workpaper([]).model_copy(update={"schedule": schedule})
    gt = _gt(
        [
            _expected("N-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "150.00"}),
            # Not on the schedule and not assessed: the claim is unknown, so it is counted as overstating.
            _expected("N-2", Treatment.REJECT, {"FY2024": "0.00", "FY2025": "0.00"}),
        ]
    )
    s = score(wp, gt)
    assert _row(s, "N-1")["accept_overstates"] is False and _row(s, "N-1")["claimed"]["FY2025"] == "100.00"
    assert _row(s, "N-2")["accept_overstates"] is True
    assert (s["false_accept_rate"]["den"], s["missed_revisions"]["den"]) == (1, 1)
    assert _row(s, "N-1")["verdict"] == "NOT_ASSESSED"


# -- supporting links: audit roles and out-of-period moves ---------------------


def test_supporting_links_follow_audit_roles_and_count_out_of_period_moves():
    moved = GLLink(entry_id="GL-R5", period="2025-03", amount="42000.00", score=4.0, supports_claim=False,
                   role="moved", claimed=True)
    dup_extra = GLLink(entry_id="GL-R6", period="2025-05", amount="100.00", score=3.0, supports_claim=False,
                       role="removed", claimed=True, removed_by=FlagCode.DUPLICATE_GL_ENTRY)
    carried = GLLink(entry_id="GL-R7", period="2025-06", amount="100.00", score=3.0, role="supporting", claimed=True)
    context = GLLink(entry_id="GL-R8", period="2024-06", amount="100.00", score=3.0, role="context")
    # No role recorded, the entry taken out of the supporting set, but the OUT_OF_PERIOD flag cites the claimed entry.
    legacy_oop = GLLink(entry_id="GL-R9", period="2025-03", amount="10.00", score=4.0, supports_claim=False, claimed=True)
    a = _assessment("A-1", Treatment.REVISE, {"FY2024": "-42000.00", "FY2025": "42000.00"},
                    links=(moved, dup_extra, carried, context, legacy_oop),
                    flags=(_flag(FlagCode.OUT_OF_PERIOD, (5, 9)), _flag(FlagCode.DUPLICATE_GL_ENTRY, (6, 7))))
    assert supporting_entry_ids(a) == {"GL-R5", "GL-R7", "GL-R9"}
    exp = _expected("A-1", Treatment.REVISE, {"FY2024": "-42000.00", "FY2025": "42000.00"}, supporting=(5, 7, 9))
    gl = _row(score(_workpaper([a]), _gt([exp])), "A-1")["gl_links"]
    assert (gl["precision"], gl["recall"]) == (1.0, 1.0)


# -- case types (the ExpectedAdjustment.case_type vocabulary) ------------------


def test_case_type_vocabulary_matches_the_schema_comment():
    source = (ROOT / "qoe" / "schemas.py").read_text(encoding="utf-8")
    line = next(ln for ln in source.splitlines() if ln.strip().startswith("case_type: str"))
    assert tuple(t.strip() for t in line.split("#", 1)[1].split("|")) == CASE_TYPES
    assert normalize_case_type(" recovery-offset ") == "RECOVERY_OFFSET"
    assert normalize_case_type("") == "UNSPECIFIED"


def test_by_case_type_lists_the_vocabulary_and_includes_diligence_items():
    wp, gt = _with_diligence([_dup_item("D-1", 4465, 4464)], [_expected_dup()])
    gt = gt.model_copy(update={"adjustments": [
        gt.adjustments[0].model_copy(update={"case_type": "adequate"}),
    ]})
    gt = gt.model_copy(update={"diligence_items": [*gt.diligence_items, _expected_dup("D-2").model_copy(
        update={"case_type": "Topside Accrual", "supporting_gl_rows": [9999], "related_gl_rows": []})]})
    s = score(wp, gt)
    by = s["by_case_type"]
    assert list(by)[: len(CASE_TYPES)] == list(CASE_TYPES)
    assert by["ADEQUATE"] == {"num": 1, "den": 1, "rate": 1.0}
    assert by["DUPLICATE_POSTING"] == {"num": 1, "den": 1, "rate": 1.0}
    assert by["MISSING_GL_MONTH"] == {"num": 0, "den": 0, "rate": None}
    # Outside the vocabulary: still grouped (the missed item is wrong), and named.
    assert by["TOPSIDE_ACCRUAL"] == {"num": 0, "den": 1, "rate": 0.0}
    assert s["case_types_outside_vocabulary"] == ["TOPSIDE_ACCRUAL"]
    o = aggregate([s])
    assert o["by_case_type"]["DUPLICATE_POSTING"]["den"] == 1 and o["case_types_outside_vocabulary"] == ["TOPSIDE_ACCRUAL"]
    md = render_markdown(build_report("dev", [s], "rules"))
    assert "| MISSING_GL_MONTH | - | - |" in md
    assert "| TOPSIDE_ACCRUAL (outside the vocabulary) | 0/1 | 0.0% |" in md
    assert md.index("| ADEQUATE |") < md.index("| DUPLICATE_POSTING |") < md.index("| TOPSIDE_ACCRUAL")


# -- diligence items with no GL rows (e.g. a documented GL-export gap) --------


def _gap_item(adj_id: str, amounts: dict[str, str], links: tuple[GLLink, ...] = ()) -> AdjustmentAssessment:
    a = _assessment(adj_id, Treatment.REVISE, amounts, claimed={"FY2024": "0.00", "FY2025": "0.00"}, links=links)
    return a.model_copy(update={"source": "diligence", "title": f"Supported difference ({adj_id})"})


def test_diligence_item_without_gl_rows_matches_on_the_same_nonzero_periods():
    expected_gap = _expected("D-3", Treatment.REVISE, {"FY2024": "-363586.47", "FY2025": "0.00"},
                             case_type="MISSING_GL_MONTH")
    wrong_period = _gap_item("D-7", {"FY2024": "0.00", "FY2025": "-363586.47"})
    with_links = _gap_item("D-8", {"FY2024": "-363586.47", "FY2025": "0.00"}, links=(_link(77, period="2024-08"),))
    gap = _gap_item("D-9", {"FY2024": "-363000.00", "FY2025": "0.00"})
    pairs = match_diligence_items([expected_gap], [wrong_period, with_links, gap])
    assert pairs == [(0, 2, "period_labels")]
    wp, gt = _with_diligence([wrong_period, with_links, gap], [expected_gap])
    di = score(wp, gt)["diligence_item_accuracy"]
    item = next(r for r in di["items"] if r["key_id"] == "D-3")
    assert (item["tool_id"], item["match_basis"], item["verdict"]) == ("D-9", "period_labels", "WRONG_AMOUNT")
    assert item["amount_diffs"]["FY2024"] == "586.47"
    assert sorted(di["extra"]) == ["D-7", "D-8"]
    # An item that has supporting rows in the key never matches on periods alone.
    keyed = expected_gap.model_copy(update={"supporting_gl_rows": [500]})
    assert match_diligence_items([keyed], [gap]) == []
    md = render_markdown(build_report("dev", [score(wp, gt)], "rules"))
    assert "| toy_deal | D-3 | D-9 | period labels |" in md


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
    cases, summary = regression_cases(wp, decisions, "data/dev/toy_deal")
    assert [c["case_id"] for c in cases] == ["toy_deal__A-2__1", "toy_deal__A-2__2", "toy_deal__A-3__1"]
    first = cases[0]
    assert first["inputs"] == {
        "deal_dir": "data/dev/toy_deal",
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


def test_run_script_exports_with_package_and_reports_recalc(tmp_path, monkeypatch, capsys):
    wp, decisions = _review_fixture()
    deal = tmp_path / "toy_deal"
    deal.mkdir()
    (deal / "deal.yaml").write_text("deal_id: toy_deal\n", encoding="utf-8")
    calls: list[dict[str, Any]] = []
    _fake_engine(monkeypatch, wp, calls)
    pkg = SimpleNamespace(schedule=SimpleNamespace(source_file="adjustments/schedule.xlsx"))
    monkeypatch.setattr("qoe.ingest.load_deal", lambda d: pkg)
    seen: dict[str, Any] = {}

    def fake_apply(w: Workpaper, log: list[ReviewDecision], schedule=None, question_log=None) -> Workpaper:
        seen["schedule"] = schedule
        seen["applied_questions"] = list(question_log or [])
        return w.model_copy(update={"reviews": list(log)})

    def fake_export(w: Workpaper, path: Path, pkg=None, question_log=None) -> Path:
        seen["pkg"] = pkg
        seen["exported_questions"] = question_log
        seen["xlsx"] = Path(path)
        Path(path).write_bytes(b"xlsx")
        return Path(path)

    recalc = {"status": "success", "total_errors": 0, "total_formulas": 321, "error_summary": {}}
    checks: dict[str, Any] = {"Workbook checks": "OK", "EBITDA Bridge: ties": "OK",
                              "Agreement to source data: schedule": "DIFFERENCE: see EBITDA Bridge"}
    monkeypatch.setattr("qoe.review_store.apply_reviews", fake_apply)
    monkeypatch.setattr("qoe.export_xlsx.export_workpaper", fake_export)
    monkeypatch.setattr("qoe.export_xlsx.recalc_and_check", lambda path, timeout=90: dict(recalc, path=str(path)))
    monkeypatch.setattr("qoe.export_xlsx.workbook_check_status", lambda path: dict(checks))
    out = tmp_path / "wp"
    _write_log(out / "toy_deal" / "review_log.jsonl", decisions)
    script = _load_script("qoe_run")
    argv = ["--deal", str(deal), "--out", str(out), "--xlsx"]
    assert script.main(argv) == 0
    assert seen["pkg"] is pkg and seen["schedule"] is pkg.schedule
    assert seen["applied_questions"] == [] and seen["exported_questions"] == []
    assert seen["xlsx"] == out / "toy_deal" / "QoE_Evidence_Review_toy_deal.xlsx"
    printed = capsys.readouterr().out
    assert "Recalculated with LibreOffice: 321 formulas, 0 formula error(s)" in printed
    assert "Workbook checks: OK" in printed
    # Management's own arithmetic is reported, but it is not a workbook check and does not fail the run.
    assert "Agreement to source data: schedule: DIFFERENCE: see EBITDA Bridge (not a workbook check)" in printed
    assert f"Review log applied: {out / 'toy_deal' / 'review_log.jsonl'} (6 decision(s))" in printed
    assert "Question log applied" not in printed

    # A difference in the Workbook checks fails the run and names the area.
    checks.update({"Workbook checks": "DIFFERENCE: see checks", "EBITDA Bridge: ties": "DIFFERENCE"})
    assert script.main(argv) == 1
    printed = capsys.readouterr().out
    assert "Workbook checks: DIFFERENCE: see checks" in printed and "  EBITDA Bridge: ties: DIFFERENCE" in printed
    checks.update({"Workbook checks": "OK", "EBITDA Bridge: ties": "OK"})

    recalc.update(status="errors_found", total_errors=2,
                  error_summary={"#REF!": {"count": 2, "locations": ["EBITDA Bridge!C9", "Cover!B30"]}})
    assert script.main(argv) == 1
    assert "#REF! 2: EBITDA Bridge!C9, Cover!B30" in capsys.readouterr().out
    assert script.main([*argv, "--no-recalc"]) == 0
    assert "Recalculated" not in capsys.readouterr().out

    # A package that cannot be reloaded: export without GL detail, never crash.
    def broken(_):
        raise ValueError("no GL")

    monkeypatch.setattr("qoe.ingest.load_deal", broken)
    assert script.main([*argv, "--no-recalc"]) == 0
    assert seen["pkg"] is None and seen["schedule"] is None
    assert "could not be reloaded" in capsys.readouterr().err


def test_run_script_applies_a_question_log_on_its_own(tmp_path, monkeypatch, capsys):
    wp, _ = _mixed()
    wp = wp.model_copy(update={"assessments": [
        a.model_copy(update={"open_questions": [OpenQuestion(q_id="Q-A-4-1", adj_id="A-4", text="Proof?")]})
        if a.adj_id == "A-4" else a for a in wp.assessments]})
    deal = tmp_path / "toy_deal"
    deal.mkdir()
    (deal / "deal.yaml").write_text("deal_id: toy_deal\n", encoding="utf-8")
    _fake_engine(monkeypatch, wp, [])
    monkeypatch.setattr("qoe.ingest.load_deal", lambda d: (_ for _ in ()).throw(ValueError("no package")))
    from qoe.review_store import QuestionLogEntry, ReviewStore

    out = tmp_path / "wp"
    store = ReviewStore(out / "toy_deal" / "review_log.jsonl")
    store.append_question(QuestionLogEntry(kind="update", q_id="Q-A-4-1", adj_id="A-4", reviewer="m.reyes",
                                           timestamp="2026-02-01T00:00:00Z", status=QuestionStatus.ANSWERED,
                                           response="Signed agreement received"))
    assert not store.path.exists()  # only the question log has entries
    script = _load_script("qoe_run")
    assert script.main(["--deal", str(deal), "--out", str(out)]) == 0
    saved = Workpaper.model_validate_json((out / "toy_deal" / "workpaper.json").read_text(encoding="utf-8"))
    q = next(a for a in saved.assessments if a.adj_id == "A-4").open_questions[0]
    assert (q.status, q.response) == (QuestionStatus.ANSWERED, "Signed agreement received")
    assert saved.reviews == []  # a question update is not a decision
    printed = capsys.readouterr().out
    assert f"Question log applied: {out / 'toy_deal' / 'question_log.jsonl'} (1 entry)" in printed
    assert "Review log applied" not in printed


def test_run_script_never_uses_a_raw_deal_id_in_paths(tmp_path, monkeypatch, capsys):
    script = _load_script("qoe_run")
    # The engine's rule when it has one ...
    engine = pytest.importorskip("qoe.engine")
    if hasattr(engine, "deal_dir_name"):
        assert script.deal_dir_name("../../etc/passwd") == engine.deal_dir_name("../../etc/passwd")
    # ... and the local fallback otherwise: one safe component, never a path or '..'.
    for raw, safe in (("../../etc", "_.._etc"), ("a/b c", "a_b_c"), (".hidden", "hidden"), ("toy_deal", "toy_deal")):
        assert script._local_deal_dir_name(raw) == safe
    with pytest.raises(ValueError):
        script._local_deal_dir_name("../")
    wp, _ = _mixed()
    # model_copy skips validation: a workpaper whose deal id never went through DealMeta's pattern.
    unsafe = wp.model_copy(update={"deal": wp.deal.model_copy(update={"deal_id": "../escape"})})
    deal = tmp_path / "deal"
    deal.mkdir()
    (deal / "deal.yaml").write_text("deal_id: x\n", encoding="utf-8")
    _fake_engine(monkeypatch, unsafe, [])
    out = tmp_path / "out" / "wp"
    seen: dict[str, Path] = {}

    def fake_export(w, path, pkg=None, question_log=None):
        seen["xlsx"] = Path(path)
        return Path(path)

    monkeypatch.setattr("qoe.ingest.load_deal", lambda d: None)
    monkeypatch.setattr("qoe.export_xlsx.export_workpaper", fake_export)
    # A review log under the raw id's path (outside the output root) must not be picked up.
    _write_log(out.parent / "escape" / "review_log.jsonl", _review_fixture()[1])
    assert script.main(["--deal", str(deal), "--out", str(out), "--xlsx", "--no-recalc"]) == 0
    assert seen["xlsx"] == out / "_escape" / "QoE_Evidence_Review__escape.xlsx"
    assert "Review log applied" not in capsys.readouterr().out


def test_run_summary_lists_diligence_items_separately():
    wp, _ = _mixed()
    item = _assessment("D-1", Treatment.REVISE, {"FY2024": "0.00", "FY2025": "18400.00"},
                       claimed={"FY2024": "0.00", "FY2025": "0.00"}).model_copy(update={"source": "diligence"})
    text = _load_script("qoe_run").summarize(wp.model_copy(update={"assessments": [*wp.assessments, item]}))
    assert "Tool treatments: ACCEPT 3, REVISE 1, REJECT 0, REQUEST_INFO 2  (reviewed 0/6)" in text
    head, _, tail = text.partition("Diligence-identified items (not on management's schedule): 1")
    assert tail and "D-1" in tail and "D-1" not in head


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


# Pinned to the reference dev deal: other packages under data/dev may be mid-authoring.
DEV_DEAL = ROOT / "data" / "dev" / "meridian_mechanical"


def _first_dev_deal() -> Optional[Path]:
    if (DEV_DEAL / "deal.yaml").is_file() and (DEV_DEAL / "ground_truth.json").is_file():
        return DEV_DEAL
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
    assert s["diligence_item_accuracy"]["expected"] == len(gt.diligence_items)
    # Diligence-identified items are scored on their own, never as unscored management items.
    diligence_ids = {a.adj_id for a in wp.assessments if a.source == "diligence"}
    assert not diligence_ids & set(s["unscored_tool_adjustments"])
    md = render_markdown(build_report("dev", [s], wp.ai_mode))
    assert "## 1. False accepts" in md and "### Diligence-identified items" in md
