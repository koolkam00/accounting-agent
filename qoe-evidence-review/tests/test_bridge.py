"""Tests for qoe.bridge: row layout and the diligence-adjusted EBITDA identity."""

from __future__ import annotations

from decimal import Decimal

import pytest

from qoe.bridge import bridge_identity_gaps, build_bridge
from qoe.money import D, fmt
from qoe.schemas import (
    AdjustmentAssessment,
    AdjustmentCategory,
    AdjustmentClaim,
    DealFiles,
    DealMeta,
    EbitdaComponents,
    ManagementSchedule,
    PeriodDef,
    ReconciliationResult,
    Treatment,
)

PERIODS = [
    PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
    PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
    PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06"),
]
LABELS = [p.label for p in PERIODS]
META = DealMeta(
    deal_id="bridge_deal", target_name="Bridge Co (SYNTHETIC)", periods=PERIODS, data_start="2024-01", data_end="2026-06",
    files=DealFiles(gl="gl.csv", chart_of_accounts="coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
)


def per(*values: object) -> dict[str, str]:
    return {lbl: fmt(v) for lbl, v in zip(LABELS, values)}


def components(ni: int, i: int, t: int, d: int, a: int) -> EbitdaComponents:
    return EbitdaComponents(net_income=fmt(ni), interest=fmt(i), taxes=fmt(t), depreciation=fmt(d), amortization=fmt(a),
                            ebitda=fmt(ni + i + t + d + a))


RECON = ReconciliationResult(
    items=[],
    issues=[],
    gl_ebitda={
        "FY2024": components(3_000_000, 200_000, 50_000, 400_000, 100_000),
        "FY2025": components(3_200_000, 210_000, 55_000, 420_000, 100_000),
        "TTM Jun-26": components(3_300_000, 205_000, 60_000, 430_000, 100_000),
    },
    # Management's FY2025 and TTM figures sit 25,000 below the GL (an unrecorded accrual).
    mgmt_reported_ebitda=per(3_750_000, 3_960_000, 4_070_000),
    months_compared=30,
    accounts_compared=20,
    variance_count=1,
)


def adj(adj_id: str, *amounts: object) -> AdjustmentClaim:
    return AdjustmentClaim(adj_id=adj_id, title=f"Adjustment {adj_id}", category=AdjustmentCategory.NON_RECURRING,
                           amounts=per(*amounts), source_row=10)


SCHEDULE = ManagementSchedule(
    source_file="adj.xlsx",
    period_labels=LABELS,
    reported_ebitda=per(3_750_000, 3_960_000, 4_070_000),
    adjustments=[adj("M-01", 0, 120_000, 65_500), adj("M-02", 360_000, 360_000, 360_000), adj("M-03", 58_000, 0, 0)],
)


def assessment(a: AdjustmentClaim, treatment: Treatment, proposed: dict[str, str]) -> AdjustmentAssessment:
    return AdjustmentAssessment(
        adj_id=a.adj_id, title=a.title, category=a.category, claimed=a.amounts, traced_gl=a.amounts, documented=a.amounts,
        proposed=proposed, treatment=treatment,
    )


ASSESSMENTS = [
    assessment(SCHEDULE.adjustments[0], Treatment.REVISE, per(0, 84_500, 30_000)),
    assessment(SCHEDULE.adjustments[1], Treatment.REQUEST_INFO, {}),
    assessment(SCHEDULE.adjustments[2], Treatment.REVISE, per(58_000, -40_000, 0)),
]


def rows(bridge) -> dict[str, dict[str, Decimal]]:
    return {r.key: {k: D(v) for k, v in r.amounts.items()} for r in bridge.rows}


def test_rows_follow_the_spec_order_and_kinds():
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS)
    keys = [r.key for r in bridge.rows]
    assert keys == [
        "net_income", "interest", "taxes", "depreciation", "amortization", "gl_ebitda", "mgmt_recon_diff",
        "mgmt_reported_ebitda", "mgmt:M-01", "mgmt:M-02", "mgmt:M-03", "mgmt_total", "mgmt_adjusted_ebitda",
        "dil_recon", "dil:M-01", "dil:M-02", "dil:M-03", "dil_total", "diligence_adjusted_ebitda", "pending",
    ]
    kinds = {r.key: r.kind for r in bridge.rows}
    assert kinds["net_income"] == "component" and kinds["gl_ebitda"] == "subtotal" and kinds["mgmt_recon_diff"] == "memo"
    assert kinds["mgmt:M-01"] == "mgmt_adjustment" and kinds["dil:M-01"] == "diligence_adjustment" and kinds["pending"] == "memo"
    labels = {r.key: r.label for r in bridge.rows}
    assert labels["mgmt:M-01"] == "Adjustment M-01 (as claimed)"
    assert labels["dil:M-01"] == "Adjustment M-01: diligence revision"
    assert {r.key: r.adj_id for r in bridge.rows}["dil:M-03"] == "M-03"
    assert bridge.period_labels == LABELS
    assert all(set(r.amounts) == set(LABELS) for r in bridge.rows)


def test_subtotals_foot():
    r = rows(build_bridge(META, RECON, SCHEDULE, ASSESSMENTS))
    for lbl in LABELS:
        comps = sum(r[k][lbl] for k in ("net_income", "interest", "taxes", "depreciation", "amortization"))
        assert comps == r["gl_ebitda"][lbl]
        assert r["gl_ebitda"][lbl] + r["mgmt_recon_diff"][lbl] == r["mgmt_reported_ebitda"][lbl]
        assert r["mgmt_total"][lbl] == sum(r[f"mgmt:M-0{i}"][lbl] for i in (1, 2, 3))
        assert r["mgmt_adjusted_ebitda"][lbl] == r["mgmt_reported_ebitda"][lbl] + r["mgmt_total"][lbl]
        assert r["dil_total"][lbl] == r["dil_recon"][lbl] + sum(r[f"dil:M-0{i}"][lbl] for i in (1, 2, 3))
        assert r["diligence_adjusted_ebitda"][lbl] == r["mgmt_adjusted_ebitda"][lbl] + r["dil_total"][lbl]
    assert r["dil_recon"]["FY2025"] == Decimal("25000")  # reverses management's unsupported difference


def test_identity_with_tool_proposals_excludes_pending_items():
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS)
    r = rows(bridge)
    finals = {"M-01": per(0, 84_500, 30_000), "M-02": {}, "M-03": per(58_000, -40_000, 0)}
    for lbl in LABELS:
        expected = r["gl_ebitda"][lbl] + sum(D(f.get(lbl)) for f in finals.values() if f)
        assert r["diligence_adjusted_ebitda"][lbl] == expected
    assert set(bridge_identity_gaps(bridge, finals).values()) == {"0.00"}
    # The pending normalization is reversed in full and shown as a memo.
    assert r["dil:M-02"] == {lbl: Decimal("-360000") for lbl in LABELS}
    assert r["pending"] == {lbl: Decimal("360000") for lbl in LABELS}
    assert r["diligence_adjusted_ebitda"]["FY2025"] == Decimal("3985000") + Decimal("84500") - Decimal("40000")


@pytest.mark.parametrize(
    "finals",
    [
        {"M-01": per(0, 120_000, 65_500), "M-02": per(300_000, 300_000, 300_000), "M-03": {}},
        {"M-01": {}, "M-02": {}, "M-03": {}},
        {"M-01": per("0.01", "-1.99", "1234567.89"), "M-02": per(0, 0, 0), "M-03": per(58_000, -40_000, 0)},
    ],
)
def test_identity_holds_for_reviewer_final_amounts(finals):
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS, final_amounts=finals)
    assert set(bridge_identity_gaps(bridge, finals).values()) == {"0.00"}
    r = rows(bridge)
    for adj_id, final in finals.items():
        claimed = {lbl: D(v) for lbl, v in next(a for a in SCHEDULE.adjustments if a.adj_id == adj_id).amounts.items()}
        expected = {lbl: (D(final[lbl]) - claimed[lbl]) if final else -claimed[lbl] for lbl in LABELS}
        assert r[f"dil:{adj_id}"] == expected


def test_package_or_meta_and_missing_reported_ebitda():
    recon = RECON.model_copy(update={"mgmt_reported_ebitda": {}})
    schedule = SCHEDULE.model_copy(update={"reported_ebitda": {}})
    r = rows(build_bridge(META, recon, schedule, ASSESSMENTS))
    # Nothing reported by management: no difference to reverse.
    assert all(v == 0 for v in r["mgmt_recon_diff"].values()) and all(v == 0 for v in r["dil_recon"].values())
    assert r["mgmt_reported_ebitda"] == r["gl_ebitda"]


def test_an_assessment_missing_from_the_schedule_still_bridges():
    extra = assessment(adj("X-9", 0, 1_000, 0), Treatment.ACCEPT, per(0, 1_000, 0))
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS + [extra])
    keys = [r.key for r in bridge.rows]
    assert "mgmt:X-9" in keys and "dil:X-9" in keys
    finals = {"M-01": per(0, 84_500, 30_000), "M-02": {}, "M-03": per(58_000, -40_000, 0), "X-9": per(0, 1_000, 0)}
    assert set(bridge_identity_gaps(bridge, finals).values()) == {"0.00"}


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.6, §5.7)
# ---------------------------------------------------------------------------


DUPLICATE = AdjustmentAssessment(
    adj_id="D-1", title="Reverse duplicate posting: Coastal Risk CR-0507", category=AdjustmentCategory.OTHER,
    source="diligence", claimed=per(0, 0, 0), traced_gl=per(0, 18_400, 0), documented=per(0, 18_400, 0),
    proposed=per(0, 18_400, 0), treatment=Treatment.REVISE,
)


def test_diligence_items_get_their_own_rows_before_the_total():
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS + [DUPLICATE])
    keys = [r.key for r in bridge.rows]
    assert "mgmt:D-1" not in keys  # not management's claim
    assert keys.index("dil:M-03") < keys.index("dil:D-1") < keys.index("dil_total")
    row = {r.key: r for r in bridge.rows}["dil:D-1"]
    assert row.kind == "diligence_adjustment" and row.adj_id == "D-1"
    assert row.label == "Reverse duplicate posting: Coastal Risk CR-0507 (diligence-identified)"
    r = rows(bridge)
    assert r["dil:D-1"] == {lbl: D(v) for lbl, v in per(0, 18_400, 0).items()}
    assert r["dil_total"]["FY2025"] == r["dil_recon"]["FY2025"] + sum(r[f"dil:M-0{i}"]["FY2025"] for i in (1, 2, 3)) + 18_400
    # Identity: GL EBITDA + management finals (pending excluded) + diligence items.
    for lbl in LABELS:
        expected = r["gl_ebitda"][lbl] + D(per(0, 84_500, 30_000)[lbl]) + D(per(58_000, -40_000, 0)[lbl]) + D(per(0, 18_400, 0)[lbl])
        assert r["diligence_adjusted_ebitda"][lbl] == expected
    finals = {"M-01": per(0, 84_500, 30_000), "M-02": {}, "M-03": per(58_000, -40_000, 0), "D-1": per(0, 18_400, 0)}
    assert set(bridge_identity_gaps(bridge, finals).values()) == {"0.00"}
    # Without the item in the finals the gap is exactly its amount; the assessments fill it in.
    partial = {k: v for k, v in finals.items() if k != "D-1"}
    assert bridge_identity_gaps(bridge, partial)["FY2025"] == "18400.00"
    assert set(bridge_identity_gaps(bridge, partial, ASSESSMENTS + [DUPLICATE]).values()) == {"0.00"}


def test_a_schedule_rebuilt_from_a_workpaper_does_not_turn_a_diligence_item_into_a_claim():
    listed = SCHEDULE.model_copy(update={"adjustments": SCHEDULE.adjustments + [adj("D-1", 0, 0, 0)]})
    bridge = build_bridge(META, RECON, listed, ASSESSMENTS + [DUPLICATE])
    keys = [r.key for r in bridge.rows]
    assert "mgmt:D-1" not in keys and keys.count("dil:D-1") == 1


def test_a_reviewer_can_hold_or_revise_a_diligence_item():
    held = {"M-01": per(0, 84_500, 30_000), "M-02": {}, "M-03": per(58_000, -40_000, 0), "D-1": {}}
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS + [DUPLICATE], final_amounts=held)
    r = rows(bridge)
    assert all(v == 0 for v in r["dil:D-1"].values())
    assert r["pending"] == {lbl: Decimal("360000") for lbl in LABELS}  # the memo lists management items only
    assert set(bridge_identity_gaps(bridge, held).values()) == {"0.00"}
    revised = dict(held, **{"D-1": per(0, 9_200, 0)})
    bridge = build_bridge(META, RECON, SCHEDULE, ASSESSMENTS + [DUPLICATE], final_amounts=revised)
    assert rows(bridge)["dil:D-1"]["FY2025"] == Decimal("9200")
    assert set(bridge_identity_gaps(bridge, revised).values()) == {"0.00"}
