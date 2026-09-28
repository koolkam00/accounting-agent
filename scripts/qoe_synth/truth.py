"""Answer key (ground_truth.json) assembly.

Row references are resolved from planted keys to final GL source rows, and
every amount the key states is either computed from the generated GL
(gl_ebitda, diligence_adjusted_ebitda) or verified against it (adjustment
amounts), so the key cannot drift from the package it grades.

Amount rule for a verified adjustment, per period label p:

    amount[p] = sum(supporting rows in p)            # removing a row adds back +dp
              + sum(recovery rows in p)             # e.g. an unadjusted insurance gain (dp < 0)
              - sum(moved rows, pro rata by service months in p)

where dp is the row's debit-positive amount. Rows named under recoveries are
reported as related_gl_rows; moved rows must also be supporting rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qoe.money import ZERO, D, fmt, q2
from qoe.periods import labels_for_month, month_range
from qoe.schemas import (
    DataQualityCode,
    ExpectedAdjustment,
    ExpectedDataQuality,
    FlagCode,
    GroundTruth,
    PeriodDef,
    Treatment,
)

from .ledger import GenerationError, Ledger, Txn, resolve_keys
from .spec import DealSpec

TOLERANCE = Decimal("0.005")


@dataclass
class TruthEffects:
    """Non-pass-through parts of an adjustment's amount, for independent re-checks."""

    recovery_rows: list[int] = field(default_factory=list)
    moves: list[tuple[list[int], str, str]] = field(default_factory=list)  # (rows, service_start, service_end)


def _period_sums(txns: list[Txn], periods: list[PeriodDef]) -> dict[str, Decimal]:
    out = {p.label: ZERO for p in periods}
    for t in txns:
        for label in labels_for_month(t.month, periods):
            out[label] += t.amount
    return out


def _move_effect(txns: list[Txn], start: str, end: str, periods: list[PeriodDef]) -> dict[str, Decimal]:
    service = month_range(start, end)
    if not service:
        raise GenerationError(f"period move {start}..{end} has no months")
    total = sum((t.amount for t in txns), ZERO)
    out = {p.label: ZERO for p in periods}
    for p in periods:
        inside = sum(1 for m in service if p.start <= m <= p.end)
        out[p.label] = -q2(total * Decimal(inside) / Decimal(len(service)))
    return out


def build_ground_truth(
    spec: DealSpec,
    ledger: Ledger,
    key_rows: dict[str, int],
    doc_filenames: dict[str, str],
    gl_ebitda: dict[str, Decimal],
    mgmt_reported: dict[str, Decimal],
) -> tuple[GroundTruth, dict[str, TruthEffects]]:
    periods = [PeriodDef(label=p.label, start=p.start, end=p.end) for p in spec.periods]
    labels = [p.label for p in periods]
    by_key = ledger.by_key()
    gl_keys = sorted(key_rows, key=lambda k: key_rows[k])

    def rows(keys: list[str]) -> list[int]:
        return sorted(key_rows[k] for k in keys)

    adjustments: list[ExpectedAdjustment] = []
    effects: dict[str, TruthEffects] = {}
    total_final = {l: ZERO for l in labels}
    for t in spec.ground_truth.adjustments:
        where = f"ground_truth {t.adj_id}"
        supporting = resolve_keys(t.supporting, gl_keys, where + " supporting")
        related = resolve_keys(t.related, gl_keys, where + " related")
        recoveries = resolve_keys(t.recoveries, gl_keys, where + " recoveries")
        related += [k for k in recoveries if k not in related and k not in supporting]
        both = set(supporting) & set(related)
        if both:
            raise GenerationError(f"{where}: rows are both supporting and related: {sorted(both)[:5]}")
        eff = TruthEffects(recovery_rows=rows(recoveries))
        amounts: dict[str, str] = {}
        if t.treatment == "REQUEST_INFO":
            if t.amounts:
                raise GenerationError(f"{where}: REQUEST_INFO items carry no amounts")
        else:
            missing = set(labels) - set(t.amounts)
            if missing:
                raise GenerationError(f"{where}: amounts missing for {sorted(missing)}")
            declared = {l: q2(D(t.amounts[l])) for l in labels}
            computed = _period_sums([by_key[k] for k in supporting + recoveries], periods)
            for move in t.period_moves:
                moved = resolve_keys(move.keys, gl_keys, where + " period_moves")
                if not set(moved) <= set(supporting):
                    raise GenerationError(f"{where}: moved rows must also be supporting rows")
                eff.moves.append((rows(moved), move.service_start, move.service_end))
                for label, delta in _move_effect([by_key[k] for k in moved], move.service_start, move.service_end, periods).items():
                    computed[label] += delta
            if t.verify_amounts:
                for l in labels:
                    if abs(computed[l] - declared[l]) > TOLERANCE:
                        raise GenerationError(
                            f"{where}: declared {l} amount {declared[l]} but the GL rows give {computed[l]}; "
                            "fix the amount, the supporting keys, or set verify_amounts: false"
                        )
            amounts = {l: fmt(declared[l]) for l in labels}
            for l in labels:
                total_final[l] += declared[l]
        effects[t.adj_id] = eff
        adjustments.append(
            ExpectedAdjustment(
                adj_id=t.adj_id,
                case_type=t.case_type,
                treatment=Treatment(t.treatment),
                amounts=amounts,
                supporting_gl_rows=rows(supporting),
                related_gl_rows=rows(related),
                supporting_docs=[doc_filenames[d] for d in t.supporting_docs],
                expected_flags=[FlagCode(f) for f in t.expected_flags],
                question_topics=list(t.question_topics),
                rationale=t.rationale.strip(),
                ambiguity=t.ambiguity,
                reviewer_note=t.reviewer_note.strip(),
            )
        )

    data_quality = _data_quality(spec, ledger, key_rows, gl_ebitda, mgmt_reported)
    truth = GroundTruth(
        deal_id=spec.deal_id,
        authored_by=spec.ground_truth.authored_by,
        split=spec.split,
        adjustments=adjustments,
        data_quality=data_quality,
        gl_ebitda={l: fmt(gl_ebitda[l]) for l in labels},
        diligence_adjusted_ebitda={l: fmt(gl_ebitda[l] + total_final[l]) for l in labels},
        notes=spec.ground_truth.notes.strip(),
    )
    return truth, effects


def _data_quality(
    spec: DealSpec,
    ledger: Ledger,
    key_rows: dict[str, int],
    gl_ebitda: dict[str, Decimal],
    mgmt_reported: dict[str, Decimal],
) -> list[ExpectedDataQuality]:
    out: list[ExpectedDataQuality] = []
    by_key = ledger.by_key()
    notes = {d.key: d.note for d in spec.data_quality.duplicates}
    for orig, dup in ledger.duplicate_pairs:
        t = by_key[dup]
        if not t.in_gl or not by_key[orig].in_gl:
            continue
        out.append(
            ExpectedDataQuality(
                code=DataQualityCode.DUPLICATE_GL_ENTRY,
                month=t.month,
                account=t.account,
                gl_rows=sorted([key_rows[orig], key_rows[dup]]),
                note=notes[dup].strip(),
            )
        )
    for ts in spec.data_quality.topside:
        out.append(
            ExpectedDataQuality(
                code=DataQualityCode.RECON_VARIANCE,
                month=ts.month,
                account=ts.account,
                note=(ts.note.strip() + f" (P&L exceeds GL by {fmt(D(ts.amount))}).").strip(),
            )
        )
    for mm in spec.data_quality.missing_gl_months:
        out.append(ExpectedDataQuality(code=DataQualityCode.MISSING_PERIOD, month=mm.month, note=mm.note.strip()))
    diffs = {l: mgmt_reported[l] - gl_ebitda[l] for l in gl_ebitda if mgmt_reported[l] != gl_ebitda[l]}
    if diffs:
        detail = "; ".join(f"{l} {fmt(v)}" for l, v in diffs.items())
        out.append(
            ExpectedDataQuality(
                code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL,
                note=f"Management's reported EBITDA less GL-derived EBITDA: {detail}. "
                "The difference is the planted P&L-only entries above; the GL is the diligence starting point.",
            )
        )
    return out
