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
reported as related_gl_rows; moved rows must also be supporting rows. Diligence
items (adjustments the tool should raise that are not on management's schedule,
such as reversing a duplicate posting) follow the same rules and count toward
diligence_adjusted_ebitda.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from qoe.money import ZERO, D, fmt, q2
from qoe.periods import labels_for_month, month_range
from qoe.schemas import (
    EBITDA_EXCLUDED_CLASSES,
    DataQualityCode,
    ExpectedAdjustment,
    ExpectedDataQuality,
    FlagCode,
    GroundTruth,
    PeriodDef,
    Treatment,
)

from .ledger import GenerationError, Ledger, Txn, resolve_keys
from .spec import DealSpec, TruthAdjustment

TOLERANCE = Decimal("0.005")
ROW_REF = re.compile(r"\{row:([^{}]+)\}")


def row_refs(text: str, key_rows: dict[str, int], where: str) -> str:
    """Replace {row:KEY} with the key's GL source row, so answer-key prose never drifts from the GL."""

    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in key_rows:
            raise GenerationError(f"{where}: {{row:{key}}} names no GL row")
        return str(key_rows[key])

    return ROW_REF.sub(sub, text)


@dataclass
class TruthEffects:
    """Non-pass-through parts of an adjustment's amount, for independent re-checks."""

    recovery_rows: list[int] = field(default_factory=list)
    moves: list[tuple[list[int], str, str]] = field(default_factory=list)  # (rows, service_start, service_end)
    normalized: dict[str, Decimal] = field(default_factory=dict)  # period -> benchmark level subtracted
    restored: dict[str, Decimal] = field(default_factory=dict)  # period -> ledger-only activity kept (EBITDA-signed)


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
    accounts: dict | None = None,
) -> tuple[GroundTruth, dict[str, TruthEffects]]:
    periods = [PeriodDef(label=p.label, start=p.start, end=p.end) for p in spec.periods]
    labels = [p.label for p in periods]
    by_key = ledger.by_key()
    gl_keys = sorted(key_rows, key=lambda k: key_rows[k])
    effects: dict[str, TruthEffects] = {}
    total_final = {l: ZERO for l in labels}

    def rows(keys: list[str]) -> list[int]:
        return sorted(key_rows[k] for k in keys)

    def expected(t: TruthAdjustment) -> ExpectedAdjustment:
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
            if t.normalized_level is not None:
                lvl = t.normalized_level
                window = month_range(lvl.start or spec.data_start, lvl.end or spec.data_end)
                for p in periods:
                    level = q2(D(lvl.monthly) * sum(1 for m in window if p.start <= m <= p.end))
                    eff.normalized[p.label] = level
                    computed[p.label] -= level
            for month in t.restore_missing_months:
                if accounts is None:
                    raise GenerationError(f"{where}: restore_missing_months needs the chart of accounts")
                dropped = [
                    x for x in ledger.txns
                    if not x.in_gl and x.month == month and accounts[x.account].ebitda_class not in EBITDA_EXCLUDED_CLASSES
                ]
                if not dropped:
                    raise GenerationError(f"{where}: no ledger rows were dropped from the GL in {month}")
                for label, total in _period_sums(dropped, periods).items():
                    eff.restored[label] = eff.restored.get(label, ZERO) - total
                    computed[label] -= total
            if t.verify_amounts:
                unknown = set(t.verify_periods) - set(labels)
                if unknown:
                    raise GenerationError(f"{where}: verify_periods names unknown periods {sorted(unknown)}")
                for l in t.verify_periods or labels:
                    if abs(computed[l] - declared[l]) > TOLERANCE:
                        raise GenerationError(
                            f"{where}: declared {l} amount {declared[l]} but the GL rows give {computed[l]}; "
                            "fix the amount, the supporting keys, or set verify_amounts: false"
                        )
            amounts = {l: fmt(declared[l]) for l in labels}
            for l in labels:
                total_final[l] += declared[l]
        effects[t.adj_id] = eff
        return ExpectedAdjustment(
            adj_id=t.adj_id,
            case_type=t.case_type,
            treatment=Treatment(t.treatment),
            amounts=amounts,
            supporting_gl_rows=rows(supporting),
            related_gl_rows=rows(related),
            supporting_docs=[doc_filenames[d] for d in t.supporting_docs],
            related_docs=[doc_filenames[d] for d in t.related_docs],
            expected_flags=[FlagCode(f) for f in t.expected_flags],
            question_topics=[row_refs(q, key_rows, where) for q in t.question_topics],
            rationale=row_refs(t.rationale.strip(), key_rows, where),
            ambiguity=t.ambiguity,
            reviewer_note=row_refs(t.reviewer_note.strip(), key_rows, where),
        )

    adjustments = [expected(t) for t in spec.ground_truth.adjustments]
    diligence_items = [expected(t) for t in spec.ground_truth.diligence_items]
    truth = GroundTruth(
        deal_id=spec.deal_id,
        authored_by=spec.ground_truth.authored_by,
        split=spec.split,
        adjustments=adjustments,
        data_quality=_data_quality(spec, ledger, key_rows, gl_ebitda, mgmt_reported),
        diligence_items=diligence_items,
        gl_ebitda={l: fmt(gl_ebitda[l]) for l in labels},
        diligence_adjusted_ebitda={l: fmt(gl_ebitda[l] + total_final[l]) for l in labels},
        notes=row_refs(spec.ground_truth.notes.strip(), key_rows, "ground_truth notes"),
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
                note=f"{ts.note.strip()} Management P&L less GL: {fmt(D(ts.amount))}.".strip(),
            )
        )
    for mm in spec.data_quality.missing_gl_months:
        out.append(ExpectedDataQuality(code=DataQualityCode.MISSING_PERIOD, month=mm.month, note=mm.note.strip()))
    diffs = {l: mgmt_reported[l] - gl_ebitda[l] for l in gl_ebitda if mgmt_reported[l] != gl_ebitda[l]}
    if diffs:
        detail = "; ".join(f"{l} {fmt(v)}" for l, v in diffs.items())
        why = spec.data_quality.mgmt_ebitda_note.strip() or (
            "The difference is the planted P&L-only entries above; the GL is the diligence starting point."
        )
        out.append(
            ExpectedDataQuality(
                code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL,
                note=f"Management's reported EBITDA less GL-derived EBITDA: {detail}. {why}",
            )
        )
    if spec.schedule.total_excludes:
        labels = [p.label for p in spec.periods]
        left_out = {l: sum((D(a.amounts[l]) for a in spec.schedule.adjustments if a.ref in spec.schedule.total_excludes), ZERO)
                    for l in labels}
        detail = "; ".join(f"{l} {fmt(-left_out[l])}" for l in labels)
        refs = ", ".join(spec.schedule.total_excludes)
        out.append(
            ExpectedDataQuality(
                code=DataQualityCode.MGMT_SCHEDULE_ARITHMETIC,
                note=f"The total-adjustments row omits ref(s) {refs}; printed total less the sum of the listed "
                f"adjustments: {detail}. {spec.schedule.arithmetic_note.strip()}".strip(),
            )
        )
    return out
