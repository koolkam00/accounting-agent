"""Treatment, amounts, and the reviewer-facing narrative (SPEC §5.5, §5.7).

Everything here is deterministic. ``proposed`` is computed from the supporting
GL entries plus the amount effects the challenges recorded; the treatment
follows the ordered rules in the spec; facts (what the evidence shows) are kept
apart from judgment questions (calls a person must make) and from open
questions for management. AI only drafts extra question wording.

Practitioners read every string produced here, so each one is short: a flag
message or question is one or two plain sentences, a rationale states the
established facts and then what remains judgment, and quotes travel as
structured ``EvidenceQuote`` objects rather than being pasted into text.

``propose_duplicate_items`` adds the diligence-identified items of SPEC §5.7:
reversals of postings that the GL carries twice under one document number.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Iterable, Optional, Sequence

from qoe.ai_base import EvidenceAI
from qoe.money import ZERO, D, fmt, q2
from qoe.schemas import (
    EBITDA_EXCLUDED_CLASSES,
    AdjustmentAssessment,
    AdjustmentCategory,
    DataQualityCode,
    ReconciliationResult,
    DocLink,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    GLLink,
    OpenQuestion,
    Severity,
    Treatment,
)
from qoe.trace import (
    MAX_RATIONALE,
    ROLE_CONTEXT,
    ROLE_MOVED,
    ROLE_SUPPORTING,
    AdjustmentTrace,
    DealIndex,
    _short_sentence,
    entries_word,
    is_repeated_bill,
    join_limited,
    money,
    month_label,
    month_span,
    norm_text,
    periods_text,
    plural,
    vouch_tick,
)

# Flags whose effect is already in the proposed amount (or that set the
# treatment): they explain the number rather than cast doubt on it.
AMOUNT_SETTING_FLAGS = frozenset(
    {
        FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
        FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
        FlagCode.OUT_OF_PERIOD,
        FlagCode.OFFSETTING_RECOVERY,
        FlagCode.PERIOD_MISMATCH,
        FlagCode.PARTIAL_GL_SUPPORT,
    }
)
# Removals that rest on reading the evidence against management's story.
JUDGMENT_REMOVAL_FLAGS = frozenset(
    {FlagCode.RECURRING_PATTERN, FlagCode.CONTRADICTORY_EVIDENCE, FlagCode.CONTINUING_OBLIGATION}
)
# SPEC §5.5: an AI-only classification behind more than half the change means low confidence.
AI_SHARE_FOR_LOW_CONFIDENCE = Decimal("0.5")
# An AI-drafted question that mostly repeats a templated one adds nothing.
QUESTION_OVERLAP = 0.6

_PRIORITY = {Severity.CRITICAL: "high", Severity.WARNING: "medium", Severity.INFO: "low"}
DILIGENCE_SOURCE = "diligence"


# ---------------------------------------------------------------------------
# Amounts
# ---------------------------------------------------------------------------


def normalization_level(t: AdjustmentTrace) -> Optional[Decimal]:
    """The supported annual level, else the level management's claim implies."""
    n = t.normalization
    if n is None:
        return None
    if n.level is not None:
        return n.level
    return n.level_candidates[0] if n.level_candidates else None


def compute_proposed(t: AdjustmentTrace) -> dict[str, Decimal]:
    """proposed[p] = supporting entries in p + challenge effects in p, for every period label."""
    if t.is_normalization:
        out = {lbl: ZERO for lbl in t.labels}
        level = normalization_level(t)
        for lbl in t.claimed_labels():
            if level is None:
                continue
            months = len(t.index.label_months[lbl])
            # Actual cost net of entries that belong to another adjustment or sit below EBITDA.
            out[lbl] = t.supporting_total(lbl) - q2(level * months / 12)
        return out
    out = {}
    for lbl in t.labels:
        out[lbl] = _capped(t, lbl, t.supporting_total(lbl)) + t.effect(lbl)
    return out


def _capped(t: AdjustmentTrace, lbl: str, supported: Decimal) -> Decimal:
    """No exact subset ties to the claim: never carry more than management claimed."""
    claim = t.claim(lbl)
    if lbl in t.capped and ((claim > 0 and supported > claim) or (claim < 0 and supported < claim)):
        return claim
    return supported


# ---------------------------------------------------------------------------
# Flag effects: the walk from claimed to proposed
# ---------------------------------------------------------------------------

# Flags that carry the gap between the GL traced in a period and management's claim there,
# in order of preference (period_mismatch and sign_error replace PARTIAL_GL_SUPPORT).
_GAP_FLAGS = (FlagCode.PERIOD_MISMATCH, FlagCode.SIGN_ERROR, FlagCode.PARTIAL_GL_SUPPORT)
# Flags raised for one named period whatever their effect (their period_label is not derived from it).
_PERIOD_FLAGS = frozenset(
    {
        FlagCode.PARTIAL_GL_SUPPORT,
        FlagCode.PERIOD_MISMATCH,
        FlagCode.SIGN_ERROR,
        FlagCode.EXCESS_GL_ACTIVITY,
        FlagCode.NO_DOCUMENT_SUPPORT,
    }
)


def flag_effects(t: AdjustmentTrace, proposed: Optional[dict[str, Decimal]] = None) -> dict[str, Decimal]:
    """Set ``Flag.effects`` (period -> signed change in the proposed amount) on every flag that
    moves the number, and return the part of ``proposed - claimed`` that no flag carries.

    For every period the walk runs from management's claim to ``compute_proposed`` (for a
    REQUEST_INFO item that is the provisional amount the rationale states):

    1. GL gap: traced GL less the claim, carried by the period's PERIOD_MISMATCH, SIGN_ERROR or
       PARTIAL_GL_SUPPORT flag, else by NO_GL_SUPPORT. When no exact subset ties and the strong
       links are capped at the claim, the cap absorbs the excess, so there is no gap.
    2. Removals, in the order the challenges made them. Each belongs to the flag that removed the
       entry first; a later flag on the same entries corroborates it and has no effect.
    3. Unclaimed entries carried under the EXCESS_GL_ACTIVITY rule, on that period's WARNING flag.
    4. Out-of-period moves: the entry leaves its booking period, then returns pro rata by service month.
    5. Offsetting recoveries, in the periods received.

    For a normalization item: removals, then the change in level when a benchmark sets a level
    other than management's (on the flag that set it), then any gap in the actual cost (on the
    period's PARTIAL_GL_SUPPORT flag).

    Differences no flag carries (returned, and noted on the trace when above the tolerance):
    a GL gap within the tolerance, or one a period move offsets so that PARTIAL_GL_SUPPORT is
    dropped; and for a normalization item without such flags the difference between the level
    management's claim implies and the level used. An INFO EXCESS_GL_ACTIVITY flag never has an
    effect: its amount is unclaimed context activity.
    """
    proposed = compute_proposed(t) if proposed is None else proposed
    labels = t.labels
    credited: dict[int, dict[str, Decimal]] = {}
    total: dict[str, Decimal] = {lbl: ZERO for lbl in labels}

    def credit(flag: Optional[Flag], lbl: str, value: Decimal) -> None:
        if flag is None or value == 0:
            return
        by_lbl = credited.setdefault(id(flag), {})
        by_lbl[lbl] = by_lbl.get(lbl, ZERO) + value
        total[lbl] += value

    held = {id(f) for f in t.flags}

    def owner(code: FlagCode, entry_id: str, linked: Optional[Flag]) -> Optional[Flag]:
        if linked is not None and id(linked) in held:
            return linked
        same = [f for f in t.flags if f.code == code]
        return next((f for f in same if entry_id in f.entry_ids), same[0] if same else None)

    def gap_flag(lbl: str) -> Optional[Flag]:
        for code in _GAP_FLAGS:
            for f in t.flags:
                if f.code == code and f.period_label == lbl:
                    return f
        return next((f for f in t.flags if f.code == FlagCode.NO_GL_SUPPORT), None)

    norm = t.normalization
    for lbl in labels:
        claim = t.claim(lbl)
        claimed_here = set(t.claimed.get(lbl, []))
        if t.is_normalization:
            for e, r in t.removals.items():
                if e in claimed_here:
                    credit(owner(r.code, e, r.flag), lbl, -t.amount(e))
            rest = proposed.get(lbl, ZERO) - claim - total[lbl]
            # A level set by a benchmark instead of management's moves the number by the level difference;
            # that change belongs to the flag that set the level. What remains is a gap in the actual cost.
            if (
                norm is not None and norm.level_flag is not None and id(norm.level_flag) in held
                and norm.mgmt_level is not None and norm.level is not None and lbl in t.claimed_labels()
            ):
                level_part = q2((norm.mgmt_level - norm.level) * len(t.index.label_months[lbl]) / 12)
                credit(norm.level_flag, lbl, level_part)
                rest -= level_part
            credit(next((f for f in t.flags if f.code == FlagCode.PARTIAL_GL_SUPPORT and f.period_label == lbl), None),
                   lbl, rest)
            continue
        running = t.traced(lbl)
        carried = _capped(t, lbl, running)
        credit(gap_flag(lbl), lbl, carried - claim)
        for e, r in t.removals.items():
            if e in claimed_here:
                running -= t.amount(e)
                now = _capped(t, lbl, running)
                credit(owner(r.code, e, r.flag), lbl, now - carried)
                carried = now
        # Unclaimed entries carried under the EXCESS_GL_ACTIVITY rule (the rest of a fixed-fee engagement).
        carry_flag = next(
            (f for f in t.flags if f.code == FlagCode.EXCESS_GL_ACTIVITY and f.period_label == lbl
             and f.severity != Severity.INFO), None,
        )
        for e in t.carried.get(lbl, []):
            if e not in t.removals and e not in claimed_here:
                credit(carry_flag, lbl, t.amount(e))
        for e in t.index.sort_ids(t.moved):
            moves = [x for x in t.effects if x.entry_id == e and x.code == FlagCode.OUT_OF_PERIOD]
            flag = owner(FlagCode.OUT_OF_PERIOD, e, next((x.flag for x in moves if x.flag is not None), None))
            if e in claimed_here and e not in t.removals:
                running -= t.amount(e)
                now = _capped(t, lbl, running)
                credit(flag, lbl, now - carried)
                carried = now
            credit(flag, lbl, sum((x.amount for x in moves if x.label == lbl), ZERO))
        for x in t.effects:
            if x.code == FlagCode.OFFSETTING_RECOVERY and x.label == lbl:
                credit(owner(x.code, x.entry_id, x.flag), lbl, x.amount)

    for f in t.flags:
        effects = {lbl: v for lbl in labels if (v := credited.get(id(f), {}).get(lbl, ZERO)) != 0}
        f.effects = {lbl: fmt(v) for lbl, v in effects.items()}
        if f.code in _PERIOD_FLAGS:
            f.amount_impact = fmt(effects[f.period_label]) if f.period_label in effects else None
        elif len(effects) == 1:
            f.period_label, v = next(iter(effects.items()))
            f.amount_impact = fmt(v)
        else:
            f.amount_impact = None
            if effects or f.code in JUDGMENT_REMOVAL_FLAGS | AMOUNT_SETTING_FLAGS:
                f.period_label = None
    residual = {lbl: proposed.get(lbl, ZERO) - t.claim(lbl) - total[lbl] for lbl in labels}
    loose = {lbl: v for lbl, v in residual.items() if abs(v) > t.index.tolerance}
    note = "Difference between claimed and proposed that no flag carries: " + periods_text(loose, labels) + "."
    if loose and note not in t.notes:
        t.notes.append(note)
    return residual


# ---------------------------------------------------------------------------
# Treatment (SPEC §5.5, in order)
# ---------------------------------------------------------------------------


def _flags(t: AdjustmentTrace, code: FlagCode, min_severity: Severity = Severity.INFO) -> list[Flag]:
    order = [Severity.INFO, Severity.WARNING, Severity.CRITICAL]
    return [f for f in t.flags if f.code == code and order.index(f.severity) >= order.index(min_severity)]


def decide_treatment(t: AdjustmentTrace, proposed: dict[str, Decimal]) -> tuple[Treatment, list[Flag], str]:
    """(treatment, flags that drove it, one-line reason)."""
    tol = t.index.tolerance
    pro_forma = _flags(t, FlagCode.PRO_FORMA_NOT_REALIZED)
    if pro_forma:
        return Treatment.REQUEST_INFO, pro_forma, "the pro forma savings are not yet realized in the GL"
    if t.is_normalization:
        drivers = _flags(t, FlagCode.UNSIGNED_OR_DRAFT_SUPPORT) + _flags(t, FlagCode.NORMALIZATION_BENCHMARK_MISSING)
        missing_actual = _flags(t, FlagCode.PARTIAL_GL_SUPPORT) + _flags(t, FlagCode.NO_GL_SUPPORT)
        if drivers or missing_actual:
            return (
                Treatment.REQUEST_INFO,
                drivers + missing_actual,
                "no executed agreement or benchmark sets the normalized level"
                if drivers
                else "the actual cost is not in the GL for every claimed period",
            )
    no_gl = _flags(t, FlagCode.NO_GL_SUPPORT)
    if no_gl and not t.has_flag(FlagCode.CONTRADICTORY_EVIDENCE):
        return Treatment.REQUEST_INFO, no_gl, "no GL entries support the claim"
    no_doc = _flags(t, FlagCode.NO_DOCUMENT_SUPPORT, Severity.WARNING)
    if no_doc:
        return Treatment.REQUEST_INFO, no_doc, "more than 25% of the amount carried has no supporting document"
    if all(abs(proposed[lbl] - t.claim(lbl)) <= tol for lbl in t.labels):
        return Treatment.ACCEPT, [], "the GL and documents support the claim"
    causes = _change_causes(t)
    if all(proposed[lbl] == 0 for lbl in t.labels):
        return Treatment.REJECT, [], "no part of the claim survives" + (f" ({causes})" if causes else "")
    return Treatment.REVISE, [], "the supported amount differs from the claim" + (f" ({causes})" if causes else "")


_CAUSE = {
    FlagCode.ALREADY_EXCLUDED_FROM_EBITDA: "costs already below EBITDA",
    FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT: "entries also claimed in another adjustment",
    FlagCode.CONTRADICTORY_EVIDENCE: "entries contradicted by the documents",
    FlagCode.CONTINUING_OBLIGATION: "a continuing obligation",
    FlagCode.RECURRING_PATTERN: "recurring activity",
    FlagCode.OUT_OF_PERIOD: "costs that belong to other periods",
    FlagCode.OFFSETTING_RECOVERY: "an unadjusted recovery",
    FlagCode.PERIOD_MISMATCH: "claims in periods without matching activity",
    FlagCode.PARTIAL_GL_SUPPORT: "claims larger than the GL activity",
    FlagCode.SIGN_ERROR: "a claim whose sign conflicts with the GL",
    FlagCode.EXCESS_GL_ACTIVITY: "a claim no combination of entries ties to",
    FlagCode.DUPLICATE_GL_ENTRY: "a second posting of the same bill, reversed in a diligence item",
}


def _change_causes(t: AdjustmentTrace) -> str:
    codes = [r.code for r in t.removals.values()] + [x.code for x in t.effects]
    codes += [f.code for f in t.flags if f.code in (FlagCode.PERIOD_MISMATCH, FlagCode.PARTIAL_GL_SUPPORT, FlagCode.SIGN_ERROR)]
    causes = [_CAUSE[c] for c in dict.fromkeys(codes) if c in _CAUSE]
    if t.capped:
        causes.append(_CAUSE[FlagCode.EXCESS_GL_ACTIVITY])
    if t.carried_ids():
        causes.append("unclaimed bills of the same fixed-fee engagement")
    n = t.normalization
    if n is not None and n.benchmark:
        causes.append("a market benchmark instead of management's level")
    return "; ".join(dict.fromkeys(causes))


def assess_confidence(
    t: AdjustmentTrace, treatment: Treatment, proposed: dict[str, Decimal], drivers: list[Flag]
) -> str:
    change = sum((abs(proposed[lbl] - t.claim(lbl)) for lbl in t.labels), ZERO)
    if treatment != Treatment.REQUEST_INFO and change > 0:
        ai_change = ZERO
        for e, removal in t.removals.items():
            if removal.source == "ai":
                ai_change += sum((abs(t.amount(e)) for lbl in t.labels if e in t.claimed.get(lbl, [])), ZERO)
        if ai_change / change > AI_SHARE_FOR_LOW_CONFIDENCE:
            return "low"
    if t.has_flag(*JUDGMENT_REMOVAL_FLAGS):
        return "medium"
    exempt = AMOUNT_SETTING_FLAGS | {f.code for f in drivers}
    if any(f.severity != Severity.INFO and f.code not in exempt for f in t.flags):
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------


def _amounts_text(labels: Sequence[str], amounts: dict[str, Decimal]) -> str:
    return " / ".join(f"{lbl} {money(amounts.get(lbl, ZERO))}" for lbl in labels)


def _removed_by_period(t: AdjustmentTrace, entry_ids: Iterable[str]) -> dict[str, Decimal]:
    ids = set(entry_ids)
    return {lbl: sum((t.amount(e) for e in t.claimed.get(lbl, []) if e in ids), ZERO) for lbl in t.labels}


def _groups(t: AdjustmentTrace, entry_ids: Iterable[str], limit: int = 1) -> str:
    return t.items_text(entry_ids, limit)


def _verb(subject: str, one: str, many: str) -> str:
    """Agreement for a joined subject: 'X indicates' / 'X and 2 more indicate'."""
    return many if " and " in subject else one


def _flag_docs(t: AdjustmentTrace, entry_ids: set[str], codes: Iterable[FlagCode]) -> list[str]:
    wanted = set(codes)
    docs: list[str] = []
    for f in t.flags:
        if f.code in wanted and (not f.entry_ids or entry_ids & set(f.entry_ids)):
            docs += [d for d in f.doc_ids if d not in docs]
    return docs


def _norm_q(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


_Q_STOP = frozenset(
    """please the and for with this that what which from were was are does management adjustment
    whether how why will would there their into about have been confirm provide explain""".split()
)


def _content_words(text: str) -> set[str]:
    return {w for w in _norm_q(text).split() if len(w) >= 4 and w not in _Q_STOP}


def _repeats(text: str, existing: Sequence[str]) -> bool:
    """An AI question that mostly restates a templated one (most of its content words, and
    at least three of them, already asked)."""
    words = _content_words(text)
    if not words:
        return True
    for other in existing:
        shared = words & _content_words(other)
        if len(shared) >= 3 and len(shared) / len(words) >= QUESTION_OVERLAP:
            return True
    return False


# ---------------------------------------------------------------------------
# Judgment questions (calls a reviewer has to make)
# ---------------------------------------------------------------------------


# Judgment lines that only say there is no call to make start with this.
NO_JUDGMENT = "No judgment needed"


def build_judgments(t: AdjustmentTrace) -> list[str]:
    """The calls a reviewer has to make, kept apart from the documented facts (SPEC §5.5).

    One question per removal basis, citing the groups, amounts and documents; one per
    overlap (which adjustment carries the entry), recovery (which period it nets against)
    and out-of-period move (where the cost belongs); then the challenges' own judgment
    points (ties in the claimed set, levels, unverified AI output). When the only change
    is a fixed rule (costs already below EBITDA), the list says so instead of being empty.
    """
    out: list[str] = []
    by_code: dict[tuple[FlagCode, str], list[str]] = {}
    mechanical: list[str] = []
    overlaps: dict[str, list[str]] = {}
    for e, r in t.removals.items():
        if r.code in (FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, FlagCode.DUPLICATE_GL_ENTRY):
            mechanical.append(e)
        elif r.code == FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT:
            overlaps.setdefault(r.note, []).append(e)
        else:
            by_code.setdefault((r.code, r.source), []).append(e)
    for note, ids in overlaps.items():
        others = sorted({a for f in t.flags if f.code == FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT
                         and set(ids) & set(f.entry_ids) for a in f.related_adj_ids})
        other = join_limited(others, 2) or "the other adjustment"
        amounts = periods_text(_removed_by_period(t, ids), t.labels)
        out.append(_short_sentence(
            f"Which adjustment should carry {_groups(t, ids, 2)} ({amounts}): {t.adj.adj_id} or {other}? "
            f"The tool removed {plural(len(ids), 'it', 'them')} here because {plural(len(ids), 'it is', 'they are')} {note}."
        ))
    out += _effect_judgments(t)
    for (code, source), ids in by_code.items():
        idset = set(ids)
        what = _groups(t, ids, 2)
        amounts = periods_text(_removed_by_period(t, ids), t.labels)
        docs = join_limited(sorted({d for e in ids for d in t.removals[e].doc_ids}), 1)
        if source == "ai":
            text = (
                f"Do you agree that {what} ({amounts}) does not fit management's basis? The removal rests on an "
                f"AI reading of {docs or 'the linked documents'}."
            )
        elif code == FlagCode.CONTRADICTORY_EVIDENCE and t.asserts_personal:
            text = (
                f"Were {what} ({amounts}) business costs rather than personal expenses? "
                f"{docs or 'The documents'} {_verb(docs or 'x and y', 'records', 'record')} a business purpose."
            )
        elif code == FlagCode.CONTINUING_OBLIGATION:
            text = (
                f"Is the obligation under {docs or 'the agreement'} part of the ongoing cost base after closing? "
                f"The tool removed {what} ({amounts})."
            )
        elif code == FlagCode.RECURRING_PATTERN:
            seen = [
                ", ".join(f"{lbl} {money(v)}" for lbl, v in obs.amounts_by_period.items() if D(v) != 0)
                for obs in t.recurrence
                if obs.group in {t.group_of.get(e) for e in ids}
            ]
            text = f"Is {what} ({amounts}) part of the ongoing cost base?" + (
                f" Comparable activity outside the claim: {seen[0]}." if seen and seen[0] else ""
            )
        else:
            evidence = join_limited(_flag_docs(t, idset, JUDGMENT_REMOVAL_FLAGS), 1) or docs or "the evidence"
            if t.asserts_nonrecurring:
                text = (
                    f"Is {what} ({amounts}) part of the ongoing cost base, as {evidence} "
                    f"{_verb(evidence, 'indicates', 'indicate')}?"
                )
            else:
                text = f"Does {evidence} outweigh management's description of {what} ({amounts})?"
        out.append(_short_sentence(text))
    for j in t.judgments:
        if j not in out:
            out.append(_short_sentence(j))
    if not out and mechanical:
        amounts = periods_text(_removed_by_period(t, mechanical), t.labels)
        accounts = join_limited(sorted({f"{t.index.by_id[e].entry.account} {t.index.by_id[e].entry.account_name}"
                                        for e in mechanical}), 1)
        what = _groups(t, mechanical, 2)
        excluded = [e for e in mechanical if t.removals[e].code == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA]
        if excluded:
            out.append(_short_sentence(
                f"{NO_JUDGMENT} on the amount: {what} ({amounts}) {_verb(what, 'sits', 'sit')} in {accounts}, which "
                f"EBITDA already excludes, so {_verb(what, 'its', 'their')} removal follows a fixed rule."
            ))
        else:
            out.append(_short_sentence(
                f"{NO_JUDGMENT} on the amount: {what} ({amounts}) {_verb(what, 'is', 'are')} a second posting of a bill "
                "the claim already carries; a separate diligence item reverses it."
            ))
    return out


def _effect_judgments(t: AdjustmentTrace) -> list[str]:
    """Timing calls behind the amount effects: where a recovery nets, where a moved cost belongs."""
    idx = t.index
    out: list[str] = []
    order = t.labels.index
    claimed_in = [lbl for lbl in t.claimed_labels() if t.supporting(lbl)]
    for eid in dict.fromkeys(x.entry_id for x in t.effects if x.code == FlagCode.OFFSETTING_RECOVERY):
        info = idx.by_id[eid]
        received = idx.labels_of(info.month)
        who = f" from {info.entry.counterparty}" if info.entry.counterparty else ""
        what = f"the {money(abs(info.amount))} recovery{who} ({month_label(info.month)})"
        loss = [lbl for lbl in claimed_in if lbl not in received]
        if loss:
            out.append(_short_sentence(
                f"Should {what} be netted in {join_limited(received, 2)}, the period received, as proposed, or "
                f"against the {join_limited(loss, 2)} cost it reimburses?"
            ))
        else:
            out.append(_short_sentence(
                f"Should {what} be netted against the add-back, as proposed? It relates to the same event."
            ))
    for eid in idx.sort_ids(t.moved):
        info = idx.by_id[eid]
        contrib = {lbl: sum((x.amount for x in t.effects if x.entry_id == eid and x.label == lbl
                             and x.code == FlagCode.OUT_OF_PERIOD), ZERO) for lbl in t.labels}
        booked = idx.labels_of(info.month)
        belongs = sorted({lbl for lbl, v in contrib.items() if (v < 0) == (info.amount > 0) and v != 0}, key=order)
        docs = [d for f in t.flags if f.code == FlagCode.OUT_OF_PERIOD and eid in f.entry_ids for d in f.doc_ids]
        if belongs:
            what = f"be treated as a {join_limited(belongs, 2)} cost per the service period in"
        else:
            what = "be spread over its service months per"
        out.append(_short_sentence(
            f"Should {t.entry_ref(eid)} ({money(info.amount)}) {what} {docs[0] if docs else 'its invoice'}, as "
            f"proposed, rather than left in {join_limited(booked, 2) or 'the booking month'} where it was booked?"
        ))
    return out


# ---------------------------------------------------------------------------
# Questions for management
# ---------------------------------------------------------------------------


def _question_texts(t: AdjustmentTrace) -> list[tuple[str, FlagCode, list[Flag]]]:
    """(question, code, flags it answers): one question per issue, consolidated per code."""
    title = t.adj.title
    idx = t.index
    out: list[tuple[str, FlagCode, list[Flag]]] = []
    by_code: dict[FlagCode, list[Flag]] = {}
    for f in t.flags:
        by_code.setdefault(f.code, []).append(f)

    def add(text: Optional[str], code: FlagCode, flags: list[Flag]) -> None:
        if text:
            out.append((_short_sentence(text), code, flags))

    for code, flags in by_code.items():
        first = flags[0]
        if code == FlagCode.NO_GL_SUPPORT:
            claims = "; ".join(f"{p} {money(t.claim(p))}" for p in t.claimed_labels())
            add(f"Please provide the GL detail (account, date, vendor and amount) behind the {title} adjustment "
                f"({claims}).", code, flags)
        elif code == FlagCode.PARTIAL_GL_SUPPORT:
            # One question per distinct gap: FY and TTM often show the same shortfall.
            same: dict[tuple[Decimal, Decimal], list[Flag]] = {}
            for f in flags:
                lbl = f.period_label
                if not lbl:
                    continue
                if t.is_normalization:
                    add(f"Where is the actual {lbl} cost of the normalized item recorded in the GL?", code, [f])
                else:
                    same.setdefault((t.traced(lbl), t.claim(lbl)), []).append(f)
            for (traced, claimed), fs in same.items():
                where = " and ".join(f.period_label or "" for f in fs)
                gap = money(abs(claimed - traced))
                docs = [d for f in fs for d in f.doc_ids]
                if docs and _states_unbooked(idx, docs[0], abs(claimed - traced)):
                    add(f"For {where}, the GL supports {money(traced)} of the {money(claimed)} claimed for {title}; "
                        f"{docs[0]} puts the remaining {gap} down to an amount not booked. Was it incurred, and if so "
                        "where is it recorded?", code, fs)
                elif docs:
                    add(f"For {where}, the GL supports {money(traced)} of the {money(claimed)} claimed for {title}; "
                        f"{docs[0]} states the same {gap}. What is it, and where is it recorded in the GL?", code, fs)
                else:
                    add(f"For {where}, the GL supports {money(traced)} of the {money(claimed)} claimed for {title}; "
                        f"which entries or documents support the remaining {gap}?", code, fs)
        elif code == FlagCode.EXCESS_GL_ACTIVITY:
            for f in flags:
                lbl = f.period_label
                fit = t.fits.get(lbl or "")
                if not lbl or fit is None:
                    continue
                if lbl in t.capped:
                    add(f"Which GL entries make up the {lbl} claim of {money(t.claim(lbl))} for {title}? No "
                        "combination of the linked entries ties to it.", code, [f])
                elif fit.ties > 1:
                    span = month_span(idx.by_id[e].month for e in t.claimed.get(lbl, []))
                    add(f"Which entries make up the {lbl} claim of {money(t.claim(lbl))} for {title}? "
                        f"{fit.ties:,} combinations tie; we assumed {span}.", code, [f])
        elif code == FlagCode.NO_DOCUMENT_SUPPORT:
            warn = [f for f in flags if f.severity != Severity.INFO]
            if warn:
                ids = sorted({e for f in warn for e in f.entry_ids})
                where = ", ".join(f.period_label or "" for f in warn)
                add(f"Please provide invoices, contracts or statements for {_groups(t, ids, 2)}, which the "
                    f"{where} amount carried for {title} relies on without a supporting document.", code, warn)
        elif code == FlagCode.DOC_GL_AMOUNT_MISMATCH:
            for f in flags:
                add(f"{f.message} What explains the difference?", code, [f])
        elif code == FlagCode.PERIOD_MISMATCH:
            for f in flags:
                lbl = f.period_label
                if not lbl:
                    continue
                span = month_span(idx.by_id[e].month for e in f.entry_ids if e in idx.by_id)
                add(f"Why does the {lbl} claim of {money(t.claim(lbl))} for {title} include costs booked {span}, "
                    f"outside {lbl}?", code, [f])
        elif code == FlagCode.OUT_OF_PERIOD:
            for f in flags:
                e = f.entry_ids[0] if f.entry_ids else ""
                doc = f.doc_ids[0] if f.doc_ids else "the invoice"
                add(f"{doc} dates the services behind {t.describe(e)} to another period. Are prior-period "
                    "true-ups like this booked every year, and how are such costs accrued at year-end?", code, [f])
        elif code == FlagCode.RECURRING_PATTERN:
            for f in flags:
                removed = [e for e in f.entry_ids if e in t.removals]
                amounts = periods_text(_removed_by_period(t, removed), t.labels)
                add(f"{_groups(t, removed)} ({amounts}) has comparable activity in periods the claim does not cover; "
                    "why is it non-recurring, and will it continue after closing?", code, [f])
        elif code == FlagCode.CONTINUING_OBLIGATION:
            for f in flags:
                doc = f.doc_ids[0] if f.doc_ids else "the agreement"
                add(f"Does the obligation under {doc} continue after closing, and at what annual cost?", code, [f])
        elif code == FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT:
            for f in flags:
                n = len(f.entry_ids)
                other = ", ".join(f.related_adj_ids)
                add(f"{t.describe_many(f.entry_ids, 1)} {plural(n, 'is', 'are')} included in both {t.adj.adj_id} "
                    f"and {other}; which adjustment should carry {plural(n, 'it', 'them')}?", code, [f])
        elif code == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA:
            ids = sorted({e for f in flags for e in f.entry_ids})
            accounts = join_limited(sorted({f"{idx.by_id[e].entry.account} {idx.by_id[e].entry.account_name}" for e in ids}), 1)
            total = sum((t.amount(e) for e in ids), ZERO)
            if t.supporting_ids():
                add(f"The {money(total)} claimed in {accounts} is already excluded from EBITDA (management's own line "
                    f"adds it back); please confirm it will be taken out of {t.adj.adj_id}, leaving the part recorded "
                    "in operating expenses.", code, flags)
            else:
                add(f"The {money(total)} claimed in {accounts} is already excluded from EBITDA; was any part of "
                    f"{t.adj.adj_id} recorded in operating expenses, or should the adjustment be withdrawn?", code, flags)
        elif code == FlagCode.OFFSETTING_RECOVERY:
            for f in flags:
                info = idx.by_id.get(f.entry_ids[0]) if f.entry_ids else None
                if info is None:
                    continue
                who = f" from {info.entry.counterparty}" if info.entry.counterparty else ""
                add(f"Does the {money(abs(info.amount))} received{who} in {month_label(info.month)} relate to {title}, "
                    "and are further recoveries expected?", code, [f])
        elif code == FlagCode.CONTRADICTORY_EVIDENCE:
            docs = list(dict.fromkeys(d for f in flags for d in f.doc_ids))
            ids = sorted({e for f in flags for e in f.entry_ids})
            norm = t.normalization
            level_flag = norm.level_flag if norm is not None else None
            if level_flag is not None and level_flag in flags and norm.level is not None:
                mgmt = f"the {money(norm.mgmt_level)} a year" if norm.mgmt_level is not None else "the"
                add(f"What supports {mgmt} level used in {title}, when {norm.supported_by} puts market at "
                    f"{money(norm.level)} a year, and will the current arrangement continue after closing?", code,
                    [level_flag])
                flags = [f for f in flags if f is not level_flag]
                if not flags:
                    continue
                first = flags[0]
            if t.asserts_personal and ids:
                amounts = periods_text(_removed_by_period(t, ids), t.labels)
                who = join_limited(docs, 1)
                add(f"{who} {_verb(who, 'records', 'record')} a business purpose for {_groups(t, ids, 2)} ({amounts}); "
                    "why are these included as personal expenses?", code, flags)
            else:
                lead = first.message.split(" Effect:")[0].split(" Corroborated by")[0]
                add(f"{lead} How does management reconcile this with its description of {title}?", code, flags)
        elif code == FlagCode.UNSIGNED_OR_DRAFT_SUPPORT:
            for f in flags:
                add(f"Please provide the executed version of {f.doc_ids[0] if f.doc_ids else 'the agreement'}.", code, [f])
        elif code == FlagCode.NORMALIZATION_BENCHMARK_MISSING:
            level = normalization_level(t)
            what = f"the normalized level of {money(level)} a year" if level is not None else "the normalized level"
            add(f"What supports {what} used in {title} (an executed agreement or a market benchmark), and what is "
                "the payroll tax and benefits effect?", code, flags)
        elif code == FlagCode.PRO_FORMA_NOT_REALIZED:
            add(f"For {t.adj.adj_id} ({title}), what shows the change has happened or is committed (for example "
                "executed separation agreements or payroll changes), what will it cost to achieve, and will the roles "
                "or costs be backfilled?", code, flags)
        elif code == FlagCode.SIGN_ERROR:
            for f in flags:
                lbl = f.period_label or ""
                add(f"The {lbl} adjustment of {money(t.claim(lbl))} has the opposite sign to its GL entries "
                    f"({money(t.traced(lbl))}); which direction is intended?", code, [f])
        elif code == FlagCode.DUPLICATE_GL_ENTRY:
            for f in flags:
                e = next((x for x in f.entry_ids if x in idx.by_id), "")
                if f.effects:
                    add(f"{t.describe(e)} is posted {len(f.entry_ids)} times and the claim includes each posting; "
                        "please confirm the bill was incurred once (the extra posting is reversed separately).", code, [f])
                else:
                    add(f"{t.describe(e)} appears to be posted {len(f.entry_ids)} times; was the duplicate reversed, "
                        "and does the claim include it?", code, [f])
    return out


# Words with which a document says an amount was estimated or never booked.
_UNBOOKED = re.compile(
    r"\bestimat\w*|\bnot (?:yet )?(?:been )?(?:invoiced|booked|billed|recorded|posted|accrued)\b|\baccru\w*"
    r"|\banticipat\w*|\bto be (?:invoiced|billed|booked)\b|\bpending (?:invoice|bill)\b|\bunbooked\b",
    re.IGNORECASE,
)
_FIGURE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:\.\d{2})?)|\b(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)\b")


def _states_unbooked(index: DealIndex, doc_id: str, amount: Decimal) -> bool:
    """A sentence of the document that states ``amount`` also says it was estimated or not booked."""
    doc = index.docs.get(doc_id)
    if doc is None:
        return False
    for page in doc.pages:
        text = page.text
        for m in _FIGURE.finditer(text):
            try:
                value = D(m.group(1) or m.group(2))
            except (ValueError, ArithmeticError):
                continue
            if abs(value - amount) > index.tolerance:
                continue
            start = max(text.rfind(". ", 0, m.start()), text.rfind("\n\n", 0, m.start()), -1) + 1
            stop = text.find(". ", m.end())
            if _UNBOOKED.search(text[start : stop if stop >= 0 else len(text)]):
                return True
    return False


def build_questions(t: AdjustmentTrace, treatment: Treatment, drivers: list[Flag], ai: Optional[EvidenceAI]) -> list[OpenQuestion]:
    drafted: list[tuple[str, str, str]] = []  # (text, priority, basis)
    driver_codes = {f.code for f in drivers}
    order = [Severity.INFO, Severity.WARNING, Severity.CRITICAL]
    for text, code, flags in _question_texts(t):
        worst = max((f.severity for f in flags), key=order.index)
        priority = "high" if code in driver_codes else _PRIORITY[worst]
        drafted.append((text, priority, code.value))
    if ai is not None:
        facts = [t.index.facts[d] for d in t.evidence_docs() if d in t.index.facts]
        try:
            extra = ai.draft_questions(t.adj, list(t.flags), facts)
        except Exception as exc:  # question wording is optional; the templated questions stand alone
            t.notes.append(f"draft_questions failed: {exc}")
            extra = []
        templated = [x[0] for x in drafted]
        for text in extra:
            if not isinstance(text, str) or not text.strip():
                continue
            text = _short_sentence(text)
            if not _repeats(text, templated):
                drafted.append((text, "medium", "ai:draft_questions"))
    out: list[OpenQuestion] = []
    seen: set[str] = set()
    for text, priority, basis in drafted:
        key = _norm_q(text)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            OpenQuestion(
                q_id=f"Q-{t.adj.adj_id}-{len(out) + 1}",
                adj_id=t.adj.adj_id,
                text=text,
                priority=priority,
                basis=basis,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Facts and rationale
# ---------------------------------------------------------------------------


def _group_quotes(t: AdjustmentTrace, entry_ids: list[str], limit: int = 2) -> list[EvidenceQuote]:
    picked: list[EvidenceQuote] = []
    for d in sorted({d for e in entry_ids for d in t.entry_docs_by_basis(e, ("number", "amount", "group"))}):
        facts = t.index.facts.get(d)
        if facts is None:
            continue
        amounts = {abs(t.amount(e)) for e in entry_ids}
        for a in facts.amounts:
            try:
                ok = abs(D(a.amount)) in amounts
            except ValueError:
                ok = False
            if ok and len(picked) < limit and a.quote not in picked:
                picked.append(a.quote)
    return picked


def build_facts(t: AdjustmentTrace) -> list[Fact]:
    facts: list[Fact] = []
    accounts = sorted({t.index.by_id[e].entry.account for e in t.claimed_ids()})
    for lbl in t.claimed_labels():
        ids = t.claimed.get(lbl, [])
        if not ids or t.is_normalization:
            continue
        docs = sum(1 for e in ids if t.support_docs(e))
        n = len(ids)
        if n == 1:
            tie = "it has a supporting document" if docs else "it has no supporting document"
        else:
            tie = f"{docs} of {n} have a supporting document"
        facts.append(
            Fact(
                text=(
                    f"{lbl}: {entries_word(n)} in {', '.join(accounts)} {plural(n, 'traces', 'trace')} to "
                    f"{money(t.traced(lbl))} against the {money(t.claim(lbl))} claim; {tie}."
                ),
                entry_ids=ids,
            )
        )
    # What each group carries, per period label, so the facts tick to the proposed column; the
    # periods overlap (FY vs TTM), so a total across them would tie to nothing. Moved entries are
    # carried by their out-of-period effect, and a normalization item's own facts state its cost.
    by_group: dict[str, list[str]] = {}
    for e in t.supporting_ids():
        if e not in t.moved and not t.is_normalization:
            by_group.setdefault(t.group_label(e), []).append(e)
    for group, ids in by_group.items():
        per_label = {lbl: sum((t.amount(e) for e in ids if e in t.supporting(lbl)), ZERO) for lbl in t.labels}
        span = month_span(t.index.by_id[e].month for e in ids)
        facts.append(
            Fact(
                text=f"Supported: {group}: {periods_text(per_label, t.labels)} ({entries_word(len(ids))}, {span}).",
                entry_ids=ids,
                quotes=_group_quotes(t, ids),
            )
        )
    for f in t.facts:
        if all(f.text != x.text for x in facts):
            facts.append(f)
    return facts


def _fit_notes(t: AdjustmentTrace) -> list[str]:
    """How an ambiguous claimed set was chosen (SPEC §5.3: record residual ties)."""
    out: list[str] = []
    for lbl in t.claimed_labels():
        fit = t.fits.get(lbl)
        if fit is None or fit.ties <= 1:
            continue
        ids = t.claimed.get(lbl, [])
        span = month_span(t.index.by_id[e].month for e in ids)
        out.append(f"The {lbl} claim of {money(t.claim(lbl))} is taken as {span}, the earliest of {fit.ties:,} equal fits.")
    return out


def _excluded_note(t: AdjustmentTrace, ids: list[str]) -> str:
    """For costs already below EBITDA: does management's own line already add them back?"""
    idx = t.index
    for e in ids:
        klass = idx.by_id[e].klass
        if klass not in EBITDA_EXCLUDED_CLASSES:
            continue
        mgmt, gl = idx.mgmt_lines.get(klass, {}), idx.gl_lines.get(klass, {})
        for lbl in t.labels:
            if e in t.claimed.get(lbl, []) and lbl in mgmt and lbl in gl and abs(abs(mgmt[lbl]) - abs(gl[lbl])) <= idx.tolerance:
                line = klass.value.lower()
                return f"; management's {lbl} {line} line ({money(abs(mgmt[lbl]))}) already includes them"
    return ""


def build_rationale(
    t: AdjustmentTrace,
    treatment: Treatment,
    reason: str,
    proposed: dict[str, Decimal],
    drivers: list[Flag],
    judgments: Sequence[str] = (),
) -> str:
    """Established facts first, then what remains judgment; about 600 characters at most."""
    head = f"{treatment.value}: {reason}."
    established: list[str] = []
    claimed_ids = t.claimed_ids()
    claimed_labels = t.claimed_labels() or t.labels
    if claimed_ids:
        traced = {lbl: t.traced(lbl) for lbl in t.labels}
        documented = {lbl: t.documented(lbl) for lbl in t.labels}
        n = len(claimed_ids)
        supported = sum(1 for e in claimed_ids if t.support_docs(e))
        if t.is_normalization:
            docs = ""  # the actual cost is payroll or rent; the question is the level, not the invoices
        elif documented == traced and any(traced.values()):
            docs = ", all vouched to their own documents" if n > 1 else ", vouched to its own document"
        elif supported == n:
            # Supported (an agreement, a register, outside corroboration of a journal entry) but not every
            # entry vouched to its own bill: (c) Documented is the vouched part only.
            docs = (", all with supporting documents" if n > 1 else ", with a supporting document") + (
                f" (vouched to their own: {'; '.join(f'{lbl} {money(documented[lbl])}' for lbl in claimed_labels)})"
                if any(documented.values()) else (", none vouched to their own bills" if n > 1 else ", not vouched to its own bill")
            )
        elif not supported:
            docs = ", none with a supporting document" if n > 1 else ", without a supporting document"
        else:
            docs = f", {supported} of {n} with a supporting document"
        established.append(
            f"{entries_word(n)} {plural(n, 'traces', 'trace')} to "
            f"{'; '.join(f'{lbl} {money(traced[lbl])}' for lbl in claimed_labels)}{docs}."
        )
    elif not t.candidates:
        established.append("No GL entry could be linked to the claim.")
    norm = t.normalization
    if t.is_normalization and norm is not None and norm.level is not None and norm.supported_by:
        mgmt = f" (management: {money(norm.mgmt_level)})" if norm.benchmark and norm.mgmt_level is not None else ""
        established.append(f"Normalized level {money(norm.level)} a year per {norm.supported_by}{mgmt}.")
    fit_notes = _fit_notes(t)
    established += fit_notes
    keep = len(established)  # the tie-out and how the claimed set was chosen always stay
    removed: dict[FlagCode, list[str]] = {}
    for e, r in t.removals.items():
        removed.setdefault(r.code, []).append(e)
    for code, ids in removed.items():
        extra = _excluded_note(t, ids) if code == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA else ""
        established.append(f"Removed {_groups(t, ids, 1)} ({_CAUSE.get(code, code.value)}{extra}).")
    effects: dict[FlagCode, dict[str, Decimal]] = {}
    for x in t.effects:
        effects.setdefault(x.code, {}).setdefault(x.label, ZERO)
        effects[x.code][x.label] += x.amount
    for code, amounts in effects.items():
        if code == FlagCode.OUT_OF_PERIOD:
            # Shown against the booking period: the move takes the entry out and puts it back pro rata.
            moved = {lbl: amounts.get(lbl, ZERO) - sum((t.amount(e) for e in t.claimed.get(lbl, []) if e in t.moved), ZERO)
                     for lbl in t.labels}
            established.append(f"Out-of-period move: {periods_text(moved, t.labels)}.")
        else:
            established.append(f"Effect of {_CAUSE.get(code, code.value)}: {periods_text(amounts, t.labels)}.")
    if treatment == Treatment.REQUEST_INFO:
        pending = ", ".join(sorted({f.code.value for f in drivers}))
        if t.is_normalization and normalization_level(t) is not None:
            n = t.normalization
            basis = "supported" if n is not None and n.level is not None else "implied by the claim, not yet supported"
            outcome = (
                f"Provisional: at a normalized level of {money(normalization_level(t))} a year ({basis}) the GL "
                f"supports {_amounts_text(t.labels, proposed)}, before payroll taxes and benefits."
            )
        else:
            outcome = f"Provisional amount the evidence would support: {_amounts_text(t.labels, proposed)}."
        outcome += f" Excluded until resolved ({pending})."
    else:
        outcome = f"Proposed {_amounts_text(t.labels, proposed)}."
    tail: list[str] = []
    if judgments:
        more = f" (+{len(judgments) - 1} more)" if len(judgments) > 1 else ""
        lead = judgments[0] if judgments[0].startswith(NO_JUDGMENT) else f"Judgment: {judgments[0]}"
        tail.append(f"{lead}{more}")
    dropped = t.dropped_quotes + t.ai_dropped_quotes
    if dropped:
        tail.append(f"{dropped} AI quote(s) failed verification and were dropped.")

    def assemble(parts: list[str]) -> str:
        return " ".join(p for p in [head, *parts, outcome, *tail] if p)

    text = assemble(established)
    # Keep the paragraph short: drop the least important established facts first.
    while len(text) > MAX_RATIONALE and len(established) > keep:
        established.pop()
        text = assemble(established)
    if len(text) > MAX_RATIONALE and tail:
        tail = [x for x in tail if not x.startswith(("Judgment:", NO_JUDGMENT))] + (
            [f"Judgment: {len(judgments)} open point(s) listed separately."] if judgments else []
        )
        text = assemble(established)
    return _short_sentence(text, MAX_RATIONALE)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def propose(t: AdjustmentTrace, ai: Optional[EvidenceAI] = None) -> AdjustmentAssessment:
    """Turn a challenged trace into the adjustment's assessment."""
    labels = t.labels
    proposed = compute_proposed(t)
    flag_effects(t, proposed)
    treatment, drivers, reason = decide_treatment(t, proposed)
    confidence = assess_confidence(t, treatment, proposed, drivers)
    judgments = build_judgments(t)
    return AdjustmentAssessment(
        adj_id=t.adj.adj_id,
        title=t.adj.title,
        category=t.adj.category,
        source="management",
        description=t.adj.description,
        gl_accounts=list(t.adj.gl_accounts),
        support_refs=list(t.adj.support_refs),
        claimed={lbl: fmt(t.claim(lbl)) for lbl in labels},
        traced_gl={lbl: fmt(t.traced(lbl)) for lbl in labels},
        documented={lbl: fmt(t.documented(lbl)) for lbl in labels},
        proposed={} if treatment == Treatment.REQUEST_INFO else {lbl: fmt(proposed[lbl]) for lbl in labels},
        treatment=treatment,
        confidence=confidence,
        gl_links=t.gl_links(),
        doc_links=t.doc_link_models(),
        flags=list(t.flags),
        recurrence=list(t.recurrence),
        facts=build_facts(t),
        judgment_questions=judgments,
        open_questions=build_questions(t, treatment, drivers, ai),
        rationale=build_rationale(t, treatment, reason, proposed, drivers, judgments),
    )


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.7): duplicate postings
# ---------------------------------------------------------------------------


def _duplicate_groups(index: DealIndex) -> list[list[str]]:
    """Reconciliation's duplicate groups matched on a non-empty document number, in order
    of each group's first GL row. Groups matched on memo within 7 days stay questions."""
    out: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for group in index.duplicate_groups.values():
        key = tuple(group)
        if key in seen:
            continue
        seen.add(key)
        # One document number, every posting inside EBITDA (a below-EBITDA reversal would not change the bridge).
        if is_repeated_bill(index, group):
            out.append(index.sort_ids(group))
    return sorted(out, key=lambda g: min(index.by_id[e].entry.source_row for e in g))


def _item_doc_links(index: DealIndex, group: list[str], reversed_ids: list[str]) -> list[DocLink]:
    """Documents stating the posting's document number: the bill both postings record."""
    amount = abs(index.by_id[group[0]].amount)
    out: list[DocLink] = []
    for doc_id in sorted(index.docs):
        linked = [e for e in group if e in index.doc_entries.get(doc_id, frozenset())]
        if not linked:
            continue
        facts = index.facts.get(doc_id)
        quotes: list[EvidenceQuote] = []
        for a in facts.amounts if facts else []:
            try:
                if abs(abs(D(a.amount)) - amount) <= index.tolerance and len(quotes) < 2:
                    quotes.append(a.quote)
            except ValueError:
                continue
        number = index.by_id[group[0]].entry.doc_number
        out.append(
            DocLink(
                doc_id=doc_id,
                relation="invoice_for_entry",
                entry_ids=index.sort_ids(linked),
                score=2.5,
                reasons=[f"States doc # {number}, the number every posting in the group carries"],
                quotes=quotes,
            )
        )
    return out


def propose_duplicate_items(
    index: DealIndex,
    traces: Sequence[AdjustmentTrace],
    taken_ids: Iterable[str] = (),
) -> list[AdjustmentAssessment]:
    """One REVISE item per duplicate group matched on a document number (SPEC §5.7).

    Each extra posting overstates expense, so diligence reverses it: + its amount in
    the periods containing its month. When no management item carries the group, the
    first posting is kept as the genuine charge and the rest are reversed. A posting a
    management item already carries is never reversed again; the other postings then
    are the extras (management's add-back already removes the one it carries).
    """
    carried: dict[str, str] = {}
    for t in traces:
        for e in t.supporting_ids():
            carried.setdefault(e, t.adj.adj_id)
    taken = set(taken_ids)
    labels = index.labels
    out: list[AdjustmentAssessment] = []
    n = 0
    for group in _duplicate_groups(index):
        in_mgmt = [e for e in group if e in carried]
        reverse = [e for e in group if e not in carried] if in_mgmt else group[1:]
        if not reverse:
            continue
        proposed = {lbl: sum((index.by_id[e].amount for e in reverse if index.by_id[e].month in index.label_months[lbl]), ZERO)
                    for lbl in labels}
        if all(v == 0 for v in proposed.values()):
            continue  # outside every analysis period
        n += 1
        adj_id = f"D-{n}"
        while adj_id in taken:
            n += 1
            adj_id = f"D-{n}"
        taken.add(adj_id)
        out.append(_duplicate_item(index, adj_id, group, reverse, in_mgmt, carried, proposed))
    return out


def _times(n: int) -> str:
    return "twice" if n == 2 else f"{n} times"


def _duplicate_item(
    index: DealIndex,
    adj_id: str,
    group: list[str],
    reverse: list[str],
    in_mgmt: list[str],
    carried: dict[str, str],
    proposed: dict[str, Decimal],
) -> AdjustmentAssessment:
    labels = index.labels
    infos = [index.by_id[e] for e in group]
    first = infos[0].entry
    number = first.doc_number
    who = first.counterparty or first.account_name
    amount = abs(infos[0].amount)
    rows = ", ".join(str(i.entry.source_row) for i in infos)
    rev_rows = ", ".join(str(index.by_id[e].entry.source_row) for e in reverse)
    dates = ", ".join(i.entry.date for i in infos)
    account = f"{first.account} {first.account_name}"
    month = month_span(i.month for i in infos)
    doc_links = _item_doc_links(index, group, reverse)
    docs_by_entry = {e: [d.doc_id for d in doc_links if e in d.entry_ids] for e in group}
    effect = periods_text(proposed, labels)
    title = f"Reverse duplicate posting: {who} {number}"

    links: list[GLLink] = []
    for i in infos:
        e = i.entry_id
        if e in reverse:
            reasons = [f"Repeats doc # {number}, amount and party of GL row {first.source_row}", "Reversed: the P&L carries it twice"]
        elif e in in_mgmt:
            reasons = [f"Posting of doc # {number}", f"Already carried in {carried[e]}, so not reversed again"]
        else:
            reasons = [f"First posting of doc # {number}", "Kept as the genuine charge"]
        links.append(
            GLLink(
                entry_id=e,
                period=i.month,
                amount=fmt(i.amount),
                score=2.5,
                reasons=reasons,
                group=f"{who} · {number}",
                supports_claim=e in reverse,
                doc_ids=docs_by_entry[e],
                # Management claims none of the postings; the reversed ones are what the item carries.
                role=ROLE_SUPPORTING if e in reverse else ROLE_CONTEXT,
                claimed=False,
            )
        )

    flag = Flag(
        code=FlagCode.DUPLICATE_GL_ENTRY,
        severity=Severity.WARNING,
        message=_short_sentence(
            f"{who} doc # {number} ({money(amount)}) is posted {_times(len(group))} in {account} (GL rows {rows}), and "
            f"the P&L carries every posting. Reversing GL row {rev_rows} changes EBITDA by {effect}."
        ),
        period_label=next(iter(k for k, v in proposed.items() if v)) if sum(1 for v in proposed.values() if v) == 1 else None,
        amount_impact=fmt(next(v for v in proposed.values() if v)) if sum(1 for v in proposed.values() if v) == 1 else None,
        # Nothing is claimed, so the whole proposal is this flag's effect.
        effects={lbl: fmt(v) for lbl, v in proposed.items() if v},
        entry_ids=list(group),
        doc_ids=sorted({d.doc_id for d in doc_links}),
        quotes=[q for d in doc_links for q in d.quotes][:2],
    )
    facts = [
        Fact(
            text=f"GL rows {rows} post doc # {number} from {who} to {account} for {money(amount)} each ({dates}): "
            "same account, amount, party and document number.",
            entry_ids=list(group),
        )
    ]
    for d in doc_links:
        facts.append(
            Fact(
                text=f"{d.doc_id} is the bill for doc # {number}"
                + (f" and states {money(amount)}." if d.quotes else "."),
                entry_ids=d.entry_ids,
                quotes=d.quotes[:1],
            )
        )
    for e in in_mgmt:
        facts.append(Fact(text=f"GL row {index.by_id[e].entry.source_row} is already carried in management's "
                               f"adjustment {carried[e]}.", entry_ids=[e]))
    documented = {
        lbl: sum((index.by_id[e].amount for e in reverse if docs_by_entry[e] and index.by_id[e].month in index.label_months[lbl]), ZERO)
        for lbl in labels
    }
    question = OpenQuestion(
        q_id=f"Q-{adj_id}-1",
        adj_id=adj_id,
        text=_short_sentence(
            f"Was {who} doc # {number} ({money(amount)}, posted {_times(len(group))} in {month}) paid once or more "
            f"than once, and if more than once, has {who} refunded the extra payment or credited it against a later bill?"
        ),
        priority="medium",
        basis=FlagCode.DUPLICATE_GL_ENTRY.value,
    )
    rationale = _short_sentence(
        f"REVISE: {who} doc # {number} is posted {_times(len(group))} (GL rows {rows}) and the P&L carries each posting, "
        f"so expense is overstated by {money(sum((index.by_id[e].amount for e in reverse), ZERO))}. "
        f"Proposed {_amounts_text(labels, proposed)}, reversing GL row {rev_rows}. "
        "Judgment: none on the amount; whether the bill was paid twice affects payables or a vendor receivable, not EBITDA.",
        MAX_RATIONALE,
    )
    return AdjustmentAssessment(
        adj_id=adj_id,
        title=title,
        category=AdjustmentCategory.OTHER,
        source=DILIGENCE_SOURCE,
        description=(
            f"Diligence-identified: doc # {number} from {who} is posted {_times(len(group))} in {account}; the extra "
            f"{plural(len(reverse), 'posting is', 'postings are')} reversed."
        ),
        gl_accounts=[first.account],
        support_refs=sorted({d.doc_id for d in doc_links}),
        claimed={lbl: fmt(ZERO) for lbl in labels},
        traced_gl={lbl: fmt(v) for lbl, v in proposed.items()},
        documented={lbl: fmt(v) for lbl, v in documented.items()},
        proposed={lbl: fmt(v) for lbl, v in proposed.items()},
        treatment=Treatment.REVISE,
        confidence="high",
        gl_links=links,
        doc_links=doc_links,
        flags=[flag],
        facts=facts,
        judgment_questions=[],
        open_questions=[question],
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.7): supported reporting differences
# ---------------------------------------------------------------------------

# How a document explains a month as an export problem rather than a books problem: in one sentence that
# names the month, an export (the file, extract or search the GL detail came from) and an explicit defect
# in it; and in one sentence that names the month, the books or trial balance, and that they are complete.
_EXPORT_NOUN = re.compile(
    r"\b(?:export(?:ed|s|ing)?|extract(?:ed|s)?|download(?:ed|s)?|data (?:pull|dump|file)|saved search|query|GL detail)\b",
    re.IGNORECASE,
)
_EXPORT_DEFECT = re.compile(
    r"\b(?:missing|incomplete|dropped|omit(?:s|ted)?|wrong|incorrect|instead|truncated|partial|corrupt(?:ed)?|failed"
    r"|only (?:has|have|had|includes?|included|contains?|contained|shows?|carries|carried|pulled)|re-?run|re-?export"
    r"|replacement (?:file|export|extract))\b",
    re.IGNORECASE,
)
_BOOKS = re.compile(
    r"\btrial balance\b|\bTB\b|\bbooks\b|\bledger\b|\bincome statement\b|\bprofit and loss\b|\bP&L\b"
    r"|\bmanagement accounts?\b",
    re.IGNORECASE,
)
_COMPLETE = re.compile(
    r"(?<!in)\b(?:complete|correct|right|accurate|balanced|ties?|agrees?|reconciles?|reconciled)\b", re.IGNORECASE
)
_NOT_COMPLETE = re.compile(r"\b(?:not|never|isn't|aren't|wasn't|weren't|doesn't|don't|no longer)\s+(?:\w+\s+){0,2}?"
                           r"(?:complete|correct|right|accurate|balanced|tie|agree|reconcile)", re.IGNORECASE)
_SENTENCES = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"])")
# An approved calculation or plan need not carry a signature block: a recorded approval makes it
# more than a management estimate. The approval must be given, not pending or refused, and must say who
# gave it or when (a name, a signature, a date): "Approved by: ______" records nothing.
_APPROVAL = re.compile(r"\bapproved\b|\bratified\b|board (?:resolution|consent)", re.IGNORECASE)
_NO_APPROVAL = re.compile(
    r"\b(?:not|never|yet to be|not yet|to be|awaiting|pending|without)\s+(?:\w+\s+){0,2}?(?:approv\w*|ratif\w*)"
    r"|\bunapproved\b|\bsubject to (?:\w+\s+){0,3}?(?:approval|ratification)\b|\bapproval (?:is |remains )?pending\b"
    r"|\b(?:has|have|had|did) not (?:\w+\s+)?approved\b|\bproposed\b[^.\n]{0,40}\bnot approved\b",
    re.IGNORECASE,
)
_APPROVAL_BLANK = re.compile(r"\bapproved(?: by)?\s*[:\-]?\s*(?:_{2,}|\.{3,}|\[\s*\]|$)", re.IGNORECASE | re.MULTILINE)
_APPROVER = re.compile(
    r"/s/|\b(?i:by (?:the )?(?:board|managers|members|directors|shareholders|owners?|sole member|manager))\b"
    r"|\bby:?\s+[A-Z][a-z]+(?: [A-Z][a-z.]+)+",
)
# Accounts whose normal balance is a cost: only a cost accrued before the ledger books it is a
# supported top-side (cash to accrual); a revenue or income top-side is not this rule.
_COST_CLASSES = frozenset({"COGS", "OPEX", "OTHER_EXPENSE"})
_MONTH_NAMES = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
                "november", "december")


def _month_pattern(month: str) -> re.Pattern[str]:
    """A month as documents write it: 'March 2023', 'Mar 2023', 'Mar-23', '2023-03', '03/2023'."""
    y, m = month.split("-")
    name = _MONTH_NAMES[int(m) - 1]
    short = name[:3]
    return re.compile(
        rf"\b(?:{name}|{short}\.?)[\s,-]+(?:{y}|'?{y[2:]})\b|\b{y}-{m}\b|\b0?{int(m)}/{y}\b", re.IGNORECASE
    )


def _ebitda_account(index: DealIndex, account: str) -> bool:
    acct = index.accounts.get(account)
    if acct is None:
        return True
    return acct.ebitda_class not in EBITDA_EXCLUDED_CLASSES and acct.ebitda_class.value != "BALANCE_SHEET"


def propose_reporting_items(
    index: DealIndex,
    recon: Optional[ReconciliationResult],
    taken_ids: Iterable[str] = (),
) -> list[AdjustmentAssessment]:
    """Supported differences between management's P&L and the GL, kept as diligence items (SPEC §5.7).

    The bridge first reverses every difference between management's reported EBITDA and the GL
    (``dil_recon``); these items put back the parts the evidence supports, so the identity (GL
    EBITDA + management finals + diligence items) holds and each supported part is visible:

    - a top-side accrual that the GL books later (cash to accrual), and
    - a month the GL export is missing, where a document explains the gap as an export defect.
    """
    if recon is None:
        return []
    taken = set(taken_ids)
    out: list[AdjustmentAssessment] = []
    missing = sorted({i.month for i in recon.issues if i.code == DataQualityCode.MISSING_PERIOD and i.month})

    def next_id() -> str:
        n = 1
        while f"D-{n}" in taken:
            n += 1
        taken.add(f"D-{n}")
        return f"D-{n}"

    for pair in _reversing_topsides(index, recon, set(missing)):
        item = _topside_item(index, pair, next_id)
        if item is not None:
            out.append(item)
    for month in missing:
        item = _export_gap_item(index, recon, month, next_id)
        if item is not None:
            out.append(item)
    return out


def _reversing_topsides(
    index: DealIndex, recon: ReconciliationResult, skip_months: set[str]
) -> list[tuple[str, str, str, Decimal]]:
    """(account, P&L month, GL month, amount): a P&L-over-GL variance in one month reversed by an
    equal and opposite variance in the same account in a later month, inside the data range."""
    tol = index.tolerance
    by_account: dict[str, list[tuple[str, Decimal]]] = {}
    for item in recon.items:
        if item.within_tolerance or item.month in skip_months or not _cost_account(index, item.account):
            continue
        by_account.setdefault(item.account, []).append((item.month, D(item.variance)))
    out: list[tuple[str, str, str, Decimal]] = []
    for account in sorted(by_account):
        rows = sorted(by_account[account])
        used: set[int] = set()
        for i, (m1, v1) in enumerate(rows):
            if i in used or abs(v1) <= tol:
                continue
            for j in range(i + 1, len(rows)):
                m2, v2 = rows[j]
                if j in used or abs(v1 + v2) > tol:
                    continue
                used.update((i, j))
                # Cash to accrual only: management's P&L carries the cost earlier (P&L above the GL,
                # debit-positive) and the ledger books it later. The reverse, a cost the P&L defers to a
                # later month, raises the earlier period's EBITDA; it is not this rule and stays reversed.
                if v1 > 0:
                    out.append((account, m1, m2, abs(v1)))
                break
    return out


def _cost_account(index: DealIndex, account: str) -> bool:
    acct = index.accounts.get(account)
    return acct is not None and acct.ebitda_class.value in _COST_CLASSES


def _recorded_approval(index: DealIndex, doc_id: str, quote: EvidenceQuote) -> bool:
    """The page stating the amount records an approval that was given: not negated, pending or blank,
    and naming who approved it or carrying a signature or a date."""
    from qoe.challenge import _dates_in

    doc = index.docs.get(doc_id)
    if doc is None:
        return False
    for page in doc.pages:
        if page.page != quote.page or _NO_APPROVAL.search(page.text):
            continue
        lines = page.text.splitlines()
        for i, line in enumerate(lines):
            m = _APPROVAL.search(line)
            if m is None or _APPROVAL_BLANK.search(line):
                continue
            tail = line[m.start():] + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            if _APPROVER.search(tail) or _dates_in(tail):
                return True
    return False


def _states_non_approval(index: DealIndex, doc_id: str, quote: EvidenceQuote) -> bool:
    doc = index.docs.get(doc_id)
    return doc is not None and any(p.page == quote.page and _NO_APPROVAL.search(p.text) for p in doc.pages)


def _concerns_accrual(index: DealIndex, doc_id: str, account: str, pl_month: str) -> bool:
    """The document is about the cost accrued in ``pl_month``: it is dated no later than that month (the
    obligation existed by then), names a fiscal period or a date range that holds it, or names the account."""
    from qoe.challenge import _dates_in

    facts = index.facts.get(doc_id)
    doc = index.docs.get(doc_id)
    if doc is None:
        return False
    text = doc.full_text
    if facts is not None and facts.doc_date and facts.doc_date[:7] <= pl_month:
        return True
    for lbl in index.labels:
        if pl_month in index.label_months[lbl] and re.search(rf"(?<![\w-]){re.escape(lbl)}(?![\w-])", text, re.I):
            return True
    for line in text.splitlines():
        months = _dates_in(line)
        if any(a <= pl_month <= b for a, b in zip(months, months[1:]) if a < b):
            return True
    acct = index.accounts.get(account)
    return acct is not None and len(norm_text(acct.name)) >= 6 and f" {norm_text(acct.name)} " in f" {norm_text(text)} "


def _topside_item(index: DealIndex, pair: tuple[str, str, str, Decimal], next_id) -> Optional[AdjustmentAssessment]:
    """A management top-side accrual the evidence supports (SPEC §5.7).

    Practitioner basis: a diligence P&L is on an accrual basis. When management accrues a cost in the
    period it is earned (a bonus pool at year-end) and the ledger books it only when paid, the accrual
    is kept, not reversed, provided (1) it reverses in management's P&L when the ledger books the
    same amount in the same account, so the cost is counted once, and (2) an executed or approved
    document (a plan, an approved calculation) states that amount. The item moves the ledger entry
    to the month management accrued it: -amount in each period that holds the accrual month but not
    the booking month, +amount in each period that holds the booking month but not the accrual month.
    """
    account, pl_month, gl_month, amount = pair
    tol = index.tolerance
    booked = [
        i for i in index.entries
        if i.entry.account == account and i.month == gl_month and abs(abs(i.amount) - amount) <= tol
    ]
    if not booked:
        return None
    support: list[tuple[str, EvidenceQuote]] = []
    explain: list[tuple[str, EvidenceQuote]] = []
    for doc_id in sorted(index.docs):
        facts = index.facts.get(doc_id)
        if facts is None or facts.is_draft or facts.is_signed is False:
            continue
        quote = next((a.quote for a in facts.amounts if _amount_equal(a.amount, amount, tol)), None)
        if quote is None:
            continue
        dtype = facts.doc_type.strip().lower()
        if dtype in ("correspondence", "memo", "email"):
            explain.append((doc_id, quote))
        elif _states_non_approval(index, doc_id, quote) or not _concerns_accrual(index, doc_id, account, pl_month):
            continue  # a proposal not yet approved, or a document about something else that states the same amount
        elif facts.is_signed is True or _recorded_approval(index, doc_id, quote):
            support.append((doc_id, quote))
    if not support:
        return None
    entry = booked[0]
    sign = 1 if entry.amount > 0 else -1
    labels = index.labels
    proposed: dict[str, Decimal] = {}
    for lbl in labels:
        months = index.label_months[lbl]
        v = ZERO
        if pl_month in months and gl_month not in months:
            v -= sign * amount
        if gl_month in months and pl_month not in months:
            v += sign * amount
        proposed[lbl] = v
    adj_id = next_id()
    acct = index.accounts.get(account)
    acct_name = f"{account} {acct.name}" if acct is not None else account
    effect = periods_text(proposed, labels)
    support_ids = [d for d, _ in support]
    related = _same_subject_docs(index, support_ids)
    doc_links = [
        DocLink(doc_id=d, relation="agreement", entry_ids=[entry.entry_id], score=2.5,
                reasons=[f"Executed or approved; states the {money(amount)} amount"], quotes=[q])
        for d, q in support
    ] + [
        DocLink(doc_id=d, relation="other", entry_ids=[], score=1.0,
                reasons=[f"Same subject as {support_ids[0]}"], quotes=[])
        for d in related
    ] + [
        DocLink(doc_id=d, relation="correspondence", entry_ids=[], score=1.0,
                reasons=[f"Company correspondence stating the {money(amount)} amount"], quotes=[q])
        for d, q in explain
    ]
    e = entry.entry
    # The GL entry is traced where it is booked; the flag moves it to the accrual month, like an
    # out-of-period effect on a management item (the audit trail walks from (b) Traced to (d)).
    traced = {lbl: (entry.amount if gl_month in index.label_months[lbl] else ZERO) for lbl in labels}
    vouched = any(
        vouch_tick(index.facts.get(d), e, entry.amount, tol, index.gl_numbers) == "D" for d in support_ids
    )
    flag = Flag(
        code=FlagCode.OUT_OF_PERIOD,
        severity=Severity.WARNING,
        message=_short_sentence(
            f"Management's P&L accrues {money(amount)} in {acct_name} in {month_label(pl_month)} and reverses it in "
            f"{month_label(gl_month)}, when the GL books it (GL row {e.source_row}); {support_ids[0]} states the "
            f"amount. The accrual is kept, so the cost moves to {month_label(pl_month)}. Carried: {effect}."
        ),
        effects={lbl: fmt(proposed[lbl] - traced[lbl]) for lbl in labels if proposed[lbl] - traced[lbl]},
        entry_ids=[entry.entry_id],
        doc_ids=sorted(set(support_ids + [d for d, _ in explain])),
        quotes=[q for _, q in support][:2],
    )
    facts = [
        Fact(text=f"Reconciliation: management's P&L exceeds the GL by {money(amount)} in {acct_name} in "
                  f"{month_label(pl_month)} and falls short of it by the same amount in {month_label(gl_month)}."),
        Fact(text=f"GL row {e.source_row} books {money(entry.amount)} in {acct_name} on {e.date}"
                  + (f" ({e.memo})" if e.memo else "") + ".", entry_ids=[entry.entry_id]),
    ] + [Fact(text=f"{d} states {money(amount)}.", quotes=[q]) for d, q in support + explain]
    link = GLLink(
        entry_id=entry.entry_id, period=entry.month, amount=fmt(entry.amount), score=2.5,
        reasons=[f"Books the {money(amount)} management's P&L accrues in {month_label(pl_month)}",
                 f"Moved to {month_label(pl_month)}, the month management accrued it"],
        group=f"{acct_name} · top-side accrual", supports_claim=True, doc_ids=support_ids,
        role=ROLE_MOVED, claimed=False,
    )
    rationale = _short_sentence(
        f"REVISE: management accrues {money(amount)} in {month_label(pl_month)} as a top-side and the GL books it on "
        f"payment in {month_label(gl_month)}; {support_ids[0]} states the amount, so the accrual is a supported "
        f"reporting difference and is kept rather than reversed to the GL. Proposed {_amounts_text(labels, proposed)}. "
        "Judgment: whether the accrual month is the period the cost was earned, and what the next period accrues.",
        MAX_RATIONALE,
    )
    return AdjustmentAssessment(
        adj_id=adj_id,
        title=f"Keep management's accrual: {acct_name}, {month_label(pl_month)}",
        category=AdjustmentCategory.OTHER,
        source=DILIGENCE_SOURCE,
        description=(
            f"Diligence-identified: a top-side accrual in management's P&L ({month_label(pl_month)}) that reverses "
            f"when the GL books the same {money(amount)} ({month_label(gl_month)}), supported by {support_ids[0]}."
        ),
        gl_accounts=[account],
        support_refs=support_ids,
        claimed={lbl: fmt(ZERO) for lbl in labels},
        traced_gl={lbl: fmt(v) for lbl, v in traced.items()},
        documented={lbl: fmt(v if vouched else ZERO) for lbl, v in traced.items()},
        proposed={lbl: fmt(v) for lbl, v in proposed.items()},
        treatment=Treatment.REVISE,
        confidence="high",
        gl_links=[link],
        doc_links=doc_links,
        flags=[flag],
        facts=facts,
        judgment_questions=[
            _short_sentence(
                f"Was the {money(amount)} earned in the period that holds {month_label(pl_month)}, as management's "
                f"accrual says, and is the next period's cost accrued the same way?"
            )
        ],
        open_questions=[
            OpenQuestion(
                q_id=f"Q-{adj_id}-1", adj_id=adj_id, priority="medium", basis=FlagCode.OUT_OF_PERIOD.value,
                text=_short_sentence(
                    f"Please confirm the basis for the {money(amount)} accrued in {acct_name} in "
                    f"{month_label(pl_month)} (approval and period earned) and how the following period's cost "
                    "is being accrued."
                ),
            )
        ],
        rationale=rationale,
    )


def _amount_equal(stated: str, amount: Decimal, tol: Decimal) -> bool:
    try:
        return abs(abs(D(stated)) - abs(amount)) <= tol
    except (ValueError, ArithmeticError):
        return False


def _same_subject_docs(index: DealIndex, doc_ids: Sequence[str]) -> list[str]:
    """Other documents whose title is contained in a supporting document's title (a plan and its calculation)."""
    titles = {d: norm_text(index.facts[d].title if d in index.facts else "") for d in index.docs}
    company = index.company_tokens
    out: list[str] = []
    for d in doc_ids:
        mine = titles.get(d, "")
        for other, t in titles.items():
            # A letterhead (the company's own name) is every internal document's "title"; it names no subject.
            if other in doc_ids or other in out or len(set(t.split()) - company) < 3:
                continue
            if f" {t} " in f" {mine} ":
                out.append(other)
    return sorted(out)


def _sentences(text: str) -> list[str]:
    """Sentences of a text, paragraph by paragraph, with line wraps joined."""
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text or ""):
        flat = " ".join(para.split())
        out += [x for x in _SENTENCES.split(flat) if x]
    return out


def _export_gap_statements(text: str, month: str) -> Optional[tuple[str, str]]:
    """(defect sentence, completeness sentence) when the text says the month's export is defective and the
    month's books are complete; else None. The defect sentence names the month in full ('March 2023'); the
    completeness sentence names it too, or refers back to it ('the March income statement', 'that month')."""
    month_rx = _month_pattern(month)
    name = _MONTH_NAMES[int(month[5:]) - 1]
    refers = re.compile(rf"\b(?:{name}|{name[:3]}\.?)(?![a-z])|\b(?:that|the|this) month\b", re.IGNORECASE)
    defect = complete = None
    for sent in _sentences(text):
        if defect is None and month_rx.search(sent) and _EXPORT_NOUN.search(sent) and _EXPORT_DEFECT.search(sent):
            defect = sent
        if (complete is None and refers.search(sent) and _BOOKS.search(sent) and _COMPLETE.search(sent)
                and not _NOT_COMPLETE.search(sent)):
            complete = sent
    return (defect, complete) if defect and complete else None


def _sentence_quote(index: DealIndex, doc_id: str, sentence: str, cue: re.Pattern[str]) -> Optional[EvidenceQuote]:
    """A verbatim line of the document from ``sentence`` that carries ``cue`` (the quote a reviewer ticks)."""
    doc = index.docs.get(doc_id)
    if doc is None:
        return None
    flat = " ".join(sentence.split())
    for page in doc.pages:
        for line in page.text.splitlines():
            if len(line.strip()) < 8:
                continue
            for m in cue.finditer(line):
                around = " ".join(line[max(0, m.start() - 20) : m.end() + 20].split())
                if around in flat:
                    return EvidenceQuote(doc_id=doc_id, page=page.page, quote=line.strip())
    return None


def _export_gap_item(index: DealIndex, recon: ReconciliationResult, month: str, next_id) -> Optional[AdjustmentAssessment]:
    """A GL month the export dropped, where a document explains the gap (SPEC §5.7).

    Practitioner basis: diligence EBITDA must rest on complete books. When reconciliation shows a
    month the GL export is missing (MISSING_PERIOD) and a document explains it as an export defect,
    with management's P&L tying to the trial balance, the P&L for that month is the better record:
    reversing it to the incomplete GL would drop a month of costs. The item carries -(P&L - GL,
    debit-positive) over the EBITDA accounts for the month, in every period that holds it.
    """
    docs: list[str] = []
    statements: dict[str, tuple[str, str]] = {}
    for doc_id in sorted(index.docs):
        found = _export_gap_statements(index.docs[doc_id].full_text, month)
        if found is not None:
            docs.append(doc_id)
            statements[doc_id] = found
    if not docs:
        return None
    diff = ZERO
    accounts: list[tuple[str, Decimal]] = []
    in_pl = missing = 0
    for item in recon.items:
        if item.month != month or not _ebitda_account(index, item.account):
            continue
        v = D(item.variance)
        if D(item.pl_amount) != 0:
            in_pl += 1
            missing += D(item.gl_amount) == 0
        if v != 0:
            diff += v
            accounts.append((item.account, v))
    if abs(diff) <= index.tolerance:
        return None
    labels = index.labels
    proposed = {lbl: (-diff if month in index.label_months[lbl] else ZERO) for lbl in labels}
    adj_id = next_id()
    quotes = [
        q
        for d in docs
        for q in [_sentence_quote(index, d, statements[d][1], _BOOKS), _sentence_quote(index, d, statements[d][0], _EXPORT_DEFECT)]
        if q
    ]
    share = f"{missing} of the {in_pl} EBITDA accounts in management's {month_label(month)} P&L"
    effect = periods_text(proposed, labels)
    n_acct = len(accounts)
    flag = Flag(
        code=FlagCode.PARTIAL_GL_SUPPORT,
        severity=Severity.WARNING,
        message=_short_sentence(
            f"The {month_label(month)} GL export has no activity for {missing} of {in_pl} EBITDA accounts in "
            f"management's P&L (a {money(diff)} difference); {docs[0]} calls it an export defect and says the books "
            f"are complete, so the P&L is kept. Effect: {effect}."
        ),
        effects={lbl: fmt(v) for lbl, v in proposed.items() if v},
        doc_ids=docs,
        quotes=quotes[:2],
    )
    top = sorted(accounts, key=lambda x: -abs(x[1]))[:3]
    facts = [
        Fact(text=f"Reconciliation: for {month_label(month)} management's P&L exceeds the GL by {money(diff)} over "
                  f"{n_acct} EBITDA accounts (largest: "
                  + ", ".join(f"{a} {money(v)}" for a, v in top) + ")."),
    ] + [Fact(text=f"{d} explains the {month_label(month)} gap as an export defect; the books are complete.",
              quotes=[q for q in quotes if q.doc_id == d][:2]) for d in docs]
    rationale = _short_sentence(
        f"REVISE: the GL export has no {month_label(month)} activity for {share}, and {docs[0]} explains it as an "
        f"export defect with the month's books complete. Reversing management's {month_label(month)} P&L to the "
        f"incomplete GL would drop {money(diff)} of net cost, so diligence keeps the P&L amounts. Proposed "
        f"{_amounts_text(labels, proposed)}. Open: the replacement export, to vouch the month.",
        MAX_RATIONALE,
    )
    return AdjustmentAssessment(
        adj_id=adj_id,
        title=f"Keep management's P&L for {month_label(month)} (GL export gap)",
        category=AdjustmentCategory.OTHER,
        source=DILIGENCE_SOURCE,
        description=(
            f"Diligence-identified: the GL export for {month_label(month)} is missing accounts that management's P&L "
            "(tied to the trial balance) carries; the P&L amounts are kept."
        ),
        gl_accounts=sorted(a for a, _ in accounts),
        support_refs=docs,
        claimed={lbl: fmt(ZERO) for lbl in labels},
        traced_gl={lbl: fmt(ZERO) for lbl in labels},
        documented={lbl: fmt(ZERO) for lbl in labels},
        proposed={lbl: fmt(v) for lbl, v in proposed.items()},
        treatment=Treatment.REVISE,
        confidence="medium",
        gl_links=[],
        doc_links=[
            DocLink(doc_id=d, relation="correspondence" if (index.facts[d].doc_type if d in index.facts else "") in
                    ("correspondence", "memo", "email") else "other",
                    entry_ids=[], score=2.5, reasons=[f"Explains the {month_label(month)} GL export gap"],
                    quotes=[q for q in quotes if q.doc_id == d][:2])
            for d in docs
        ],
        flags=[flag],
        facts=facts,
        judgment_questions=[
            _short_sentence(
                f"Is the company's explanation of the {month_label(month)} export gap enough to keep management's P&L "
                "for the month, or should the replacement GL export be obtained and vouched first?"
            )
        ],
        open_questions=[
            OpenQuestion(
                q_id=f"Q-{adj_id}-1", adj_id=adj_id, priority="high", basis="MISSING_PERIOD",
                text=_short_sentence(
                    f"Please provide the complete GL detail export for {month_label(month)} and confirm that the "
                    f"{month_label(month)} P&L agrees to the trial balance."
                ),
            )
        ],
        rationale=rationale,
    )
