"""EBITDA bridge (SPEC §5.6): GL net income -> reported -> management adjusted -> diligence adjusted.

The bridge is built so that, for every period label,

    diligence_adjusted_ebitda = gl_ebitda + sum(final amounts, excluding pending items)

Management's reported EBITDA and adjustments are shown as claimed; the
diligence rows first reverse any unsupported reporting difference back to the
GL and then revise each adjustment to its final amount (or reverse it
entirely while it is pending information).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping, Optional, Sequence, Union

from qoe.money import ZERO, D, fmt
from qoe.schemas import (
    AdjustmentAssessment,
    BridgeRow,
    DealMeta,
    DealPackage,
    EbitdaBridge,
    ManagementSchedule,
    ReconciliationResult,
    Treatment,
)

_COMPONENTS = (
    ("net_income", "Net income (per GL)", "net_income"),
    ("interest", "Interest expense, net", "interest"),
    ("taxes", "Income taxes", "taxes"),
    ("depreciation", "Depreciation", "depreciation"),
    ("amortization", "Amortization", "amortization"),
)


def _final(
    adj_id: str,
    assessment: Optional[AdjustmentAssessment],
    final_amounts: Optional[Mapping[str, Mapping[str, str]]],
) -> Optional[dict[str, Decimal]]:
    """Final amounts by period, or None while the item is pending information."""
    if final_amounts is not None and adj_id in final_amounts:
        chosen = final_amounts[adj_id]
        return {k: D(v) for k, v in chosen.items()} if chosen else None
    if assessment is None or assessment.treatment == Treatment.REQUEST_INFO or not assessment.proposed:
        return None
    return {k: D(v) for k, v in assessment.proposed.items()}


def build_bridge(
    pkg_or_meta: Union[DealPackage, DealMeta],
    recon: ReconciliationResult,
    schedule: ManagementSchedule,
    assessments: Sequence[AdjustmentAssessment],
    final_amounts: Optional[Mapping[str, Mapping[str, str]]] = None,
) -> EbitdaBridge:
    """Rows in SPEC §5.6 order. ``final_amounts`` (adj_id -> period -> amount,
    ``{}`` = pending) overrides the tool's proposals; without it, the tool's
    proposal is the final amount and REQUEST_INFO items are pending."""
    meta = pkg_or_meta.meta if isinstance(pkg_or_meta, DealPackage) else pkg_or_meta
    labels = [p.label for p in meta.periods]
    rows: list[BridgeRow] = []

    def add(key: str, label: str, kind: str, values: Mapping[str, Decimal], adj_id: Optional[str] = None) -> None:
        rows.append(
            BridgeRow(
                key=key,
                label=label,
                kind=kind,
                adj_id=adj_id,
                amounts={lbl: fmt(values.get(lbl, ZERO)) for lbl in labels},
            )
        )

    comps = recon.gl_ebitda
    for key, label, attr in _COMPONENTS:
        add(key, label, "component", {lbl: D(getattr(comps[lbl], attr)) for lbl in labels if lbl in comps})
    gl = {lbl: D(comps[lbl].ebitda) if lbl in comps else ZERO for lbl in labels}
    add("gl_ebitda", "Reported EBITDA (per GL)", "subtotal", gl)

    def reported(lbl: str) -> Decimal:
        if lbl in recon.mgmt_reported_ebitda:
            return D(recon.mgmt_reported_ebitda[lbl])
        if lbl in schedule.reported_ebitda:
            return D(schedule.reported_ebitda[lbl])
        return gl[lbl]  # management reported nothing for the period: no difference to reverse

    mgmt_reported = {lbl: reported(lbl) for lbl in labels}
    add("mgmt_recon_diff", "Difference to management's reported EBITDA", "memo", {lbl: mgmt_reported[lbl] - gl[lbl] for lbl in labels})
    add("mgmt_reported_ebitda", "Reported EBITDA (per management)", "subtotal", mgmt_reported)

    by_id = {a.adj_id: a for a in assessments}
    claims: list[tuple[str, str, dict[str, Decimal]]] = [
        (adj.adj_id, adj.title, {lbl: D(adj.amounts.get(lbl)) for lbl in labels}) for adj in schedule.adjustments
    ]
    scheduled = {adj_id for adj_id, _, _ in claims}
    for a in assessments:  # an assessed item missing from the schedule still has to appear
        if a.adj_id not in scheduled:
            claims.append((a.adj_id, a.title, {lbl: D(a.claimed.get(lbl)) for lbl in labels}))

    mgmt_total = {lbl: ZERO for lbl in labels}
    for adj_id, title, claimed in claims:
        add(f"mgmt:{adj_id}", f"{title} (as claimed)", "mgmt_adjustment", claimed, adj_id)
        for lbl in labels:
            mgmt_total[lbl] += claimed[lbl]
    add("mgmt_total", "Total management adjustments", "subtotal", mgmt_total)
    mgmt_adjusted = {lbl: mgmt_reported[lbl] + mgmt_total[lbl] for lbl in labels}
    add("mgmt_adjusted_ebitda", "Management adjusted EBITDA", "subtotal", mgmt_adjusted)

    dil_recon = {lbl: gl[lbl] - mgmt_reported[lbl] for lbl in labels}
    add("dil_recon", "Reverse unsupported reporting difference (to GL)", "diligence_adjustment", dil_recon)
    dil_total = dict(dil_recon)
    pending = {lbl: ZERO for lbl in labels}
    for adj_id, title, claimed in claims:
        final = _final(adj_id, by_id.get(adj_id), final_amounts)
        if final is None:
            revision = {lbl: -claimed[lbl] for lbl in labels}
            label = f"{title}: excluded pending information"
            for lbl in labels:
                pending[lbl] += claimed[lbl]
        else:
            revision = {lbl: final.get(lbl, ZERO) - claimed[lbl] for lbl in labels}
            label = f"{title}: diligence revision"
        add(f"dil:{adj_id}", label, "diligence_adjustment", revision, adj_id)
        for lbl in labels:
            dil_total[lbl] += revision[lbl]
    add("dil_total", "Total diligence adjustments", "subtotal", dil_total)
    add(
        "diligence_adjusted_ebitda",
        "Diligence adjusted EBITDA",
        "subtotal",
        {lbl: mgmt_adjusted[lbl] + dil_total[lbl] for lbl in labels},
    )
    add("pending", "Memo: management adjustments pending information (excluded)", "memo", pending)
    return EbitdaBridge(period_labels=labels, rows=rows)


def bridge_identity_gaps(bridge: EbitdaBridge, final_amounts: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    """Period -> diligence adjusted EBITDA minus (GL EBITDA + final amounts excluding pending). All "0.00" when it ties."""
    rows = {r.key: r for r in bridge.rows}
    out: dict[str, str] = {}
    for lbl in bridge.period_labels:
        expected = D(rows["gl_ebitda"].amounts[lbl]) + sum((D(f.get(lbl)) for f in final_amounts.values() if f), ZERO)
        out[lbl] = fmt(D(rows["diligence_adjusted_ebitda"].amounts[lbl]) - expected)
    return out
