"""Treatment, amounts, and the reviewer-facing narrative (SPEC §5.5).

Everything here is deterministic. ``proposed`` is computed from the supporting
GL entries plus the amount effects the challenges recorded; the treatment
follows the ordered rules in the spec; facts (what the evidence shows) are kept
apart from judgment questions (calls a person must make) and from open
questions for management. AI only drafts extra question wording.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

from qoe.ai_base import EvidenceAI
from qoe.money import ZERO, D, fmt, q2
from qoe.schemas import (
    AdjustmentAssessment,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    OpenQuestion,
    Severity,
    Treatment,
)
from qoe.trace import AdjustmentTrace, money, month_span

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

_PRIORITY = {Severity.CRITICAL: "high", Severity.WARNING: "medium", Severity.INFO: "low"}


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
            out[lbl] = t.traced(lbl) - q2(level * months / 12)
        return out
    out = {}
    for lbl in t.labels:
        supported = t.supporting_total(lbl)
        claim = t.claim(lbl)
        # No exact subset ties to the claim: never carry more than management claimed.
        if lbl in t.capped and ((claim > 0 and supported > claim) or (claim < 0 and supported < claim)):
            supported = claim
        out[lbl] = supported + t.effect(lbl)
    return out


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
        return Treatment.REQUEST_INFO, pro_forma, "pro forma savings are not yet realized in the GL"
    if t.is_normalization:
        drivers = _flags(t, FlagCode.UNSIGNED_OR_DRAFT_SUPPORT) + _flags(t, FlagCode.NORMALIZATION_BENCHMARK_MISSING)
        missing_actual = _flags(t, FlagCode.PARTIAL_GL_SUPPORT) + _flags(t, FlagCode.NO_GL_SUPPORT)
        if drivers or missing_actual:
            return (
                Treatment.REQUEST_INFO,
                drivers + missing_actual,
                "the normalized level is not set by an executed agreement or benchmark"
                if drivers
                else "the actual cost is not in the GL for every claimed period",
            )
    no_gl = _flags(t, FlagCode.NO_GL_SUPPORT)
    if no_gl and not t.has_flag(FlagCode.CONTRADICTORY_EVIDENCE):
        return Treatment.REQUEST_INFO, no_gl, "no GL entries support the claim"
    no_doc = _flags(t, FlagCode.NO_DOCUMENT_SUPPORT, Severity.WARNING)
    if no_doc:
        return Treatment.REQUEST_INFO, no_doc, "more than 25% of the claim has no supporting document"
    if all(abs(proposed[lbl] - t.claim(lbl)) <= tol for lbl in t.labels):
        return Treatment.ACCEPT, [], "the GL and documents support the claim"
    if all(proposed[lbl] == 0 for lbl in t.labels):
        return Treatment.REJECT, [], "no part of the claim survives the challenges"
    return Treatment.REVISE, [], "part of the claim is supported, or it belongs in other periods"


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
# Questions for management
# ---------------------------------------------------------------------------


def _norm_q(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _question_for(t: AdjustmentTrace, f: Flag) -> Optional[str]:
    title = t.adj.title
    lbl = f.period_label
    docs = ", ".join(f.doc_ids) or "the supporting document"
    code = f.code
    if code == FlagCode.NO_GL_SUPPORT:
        claims = ", ".join(f"{p} {money(t.claim(p))}" for p in t.claimed_labels())
        return (
            f"Please provide the GL detail (account, date, vendor, amount) that makes up the {title} adjustment "
            f"({claims})."
        )
    if code == FlagCode.PARTIAL_GL_SUPPORT and lbl:
        if t.is_normalization:
            return f"Please identify where the actual {lbl} cost of the normalized item is recorded in the GL."
        return (
            f"For {lbl}, the GL supports {money(t.traced(lbl))} of the {money(t.claim(lbl))} claimed for {title}. "
            f"Please identify the entries or support for the remaining {money(abs(t.claim(lbl) - t.traced(lbl)))}."
        )
    if code == FlagCode.EXCESS_GL_ACTIVITY and lbl and lbl in t.capped:
        return f"Please list the GL entries included in the {lbl} claim of {money(t.claim(lbl))} for {title}."
    if code == FlagCode.NO_DOCUMENT_SUPPORT and lbl:
        if f.severity == Severity.INFO and t.asserts_personal:
            return f"Please provide statements or receipts supporting the personal nature of {t.describe_groups(f.entry_ids, 2)}."
        if f.severity == Severity.INFO:
            return None
        return f"Please provide invoices, contracts, or other support for {t.describe_groups(f.entry_ids, 3)}."
    if code == FlagCode.DOC_GL_AMOUNT_MISMATCH:
        return f"{f.message} Please explain the difference."
    if code == FlagCode.PERIOD_MISMATCH and lbl:
        return (
            f"The {lbl} claim of {money(t.claim(lbl))} for {title} has no matching GL activity in {lbl}. "
            f"Please explain why costs booked {month_span(t.index.by_id[e].month for e in f.entry_ids)} "
            f"are included in {lbl}."
        )
    if code == FlagCode.OUT_OF_PERIOD:
        return (
            f"Please confirm the service period of {t.describe_many(f.entry_ids)} per {docs}, and whether other "
            "prior-period costs were booked in the same period."
        )
    if code == FlagCode.RECURRING_PATTERN:
        return (
            f"{t.describe_groups([e for e in f.entry_ids if e in t.removals], 2)} shows comparable activity in "
            "other periods. Please explain why the claimed amount is non-recurring."
        )
    if code == FlagCode.CONTINUING_OBLIGATION:
        return f"Please confirm whether the obligation under {docs} continues after closing, and its annual cost."
    if code == FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT:
        other = ", ".join(f.related_adj_ids)
        return (
            f"{t.describe_many(f.entry_ids)} {'is' if len(f.entry_ids) == 1 else 'are'} included in both "
            f"{t.adj.adj_id} and {other}. Please confirm which adjustment should carry {'it' if len(f.entry_ids) == 1 else 'them'}."
        )
    if code == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA:
        return (
            f"The {title} entries are recorded in accounts that are already excluded from EBITDA (interest, taxes, "
            "D&A). Please confirm the adjustment should be withdrawn."
        )
    if code == FlagCode.OFFSETTING_RECOVERY:
        return (
            f"Please confirm that {t.describe_many(f.entry_ids)} relates to this event, why it was not adjusted, "
            "and whether further recoveries are expected."
        )
    if code == FlagCode.CONTRADICTORY_EVIDENCE:
        quote = f.quotes[0].quote if f.quotes else ""
        if quote:
            return f"{docs} states \"{quote}\". Please reconcile this with management's description of {title}."
        return f"Please reconcile {docs} with management's description of {title}."
    if code == FlagCode.UNSIGNED_OR_DRAFT_SUPPORT:
        return f"Please provide the executed version of {docs}."
    if code == FlagCode.NORMALIZATION_BENCHMARK_MISSING:
        return (
            f"Please provide the basis for the normalized level used in {title} (an executed agreement or a market "
            "benchmark), and the related payroll tax and benefits effect."
        )
    if code == FlagCode.PRO_FORMA_NOT_REALIZED:
        return (
            f"Please provide evidence that the {title} has occurred (for example executed separation agreements "
            "or payroll changes), the one-time cost to achieve it, and whether the roles or costs will be backfilled."
        )
    if code == FlagCode.SIGN_ERROR and lbl:
        return (
            f"The {lbl} adjustment of {money(t.claim(lbl))} has the opposite sign to the GL entries "
            f"({money(t.traced(lbl))}). Please confirm the direction of the adjustment."
        )
    if code == FlagCode.DUPLICATE_GL_ENTRY:
        return (
            f"{', '.join(f.entry_ids)} appear to be the same posting recorded more than once. Please confirm whether "
            "the duplicate was reversed and whether the claim includes it."
        )
    return None


def build_questions(t: AdjustmentTrace, treatment: Treatment, drivers: list[Flag], ai: Optional[EvidenceAI]) -> list[OpenQuestion]:
    drafted: list[tuple[str, str, str]] = []  # (text, priority, basis)
    driver_codes = {f.code for f in drivers}
    for f in t.flags:
        text = _question_for(t, f)
        if not text:
            continue
        priority = "high" if f.code in driver_codes else _PRIORITY[f.severity]
        drafted.append((text, priority, f.code.value))
    if ai is not None:
        facts = [t.index.facts[d] for d in sorted(t.doc_links) if d in t.index.facts]
        try:
            extra = ai.draft_questions(t.adj, list(t.flags), facts)
        except Exception as exc:  # question wording is optional; the templated questions stand alone
            t.notes.append(f"draft_questions failed: {exc}")
            extra = []
        for text in extra:
            if isinstance(text, str) and text.strip():
                drafted.append((" ".join(text.split()), "medium", "ai:draft_questions"))
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
        docs = sum(1 for e in ids if t.entry_docs(e))
        facts.append(
            Fact(
                text=(
                    f"{lbl}: {len(ids)} GL entr{'y' if len(ids) == 1 else 'ies'} in {', '.join(accounts)} trace to "
                    f"{money(t.traced(lbl))} against a claim of {money(t.claim(lbl))}; {docs} of them tie to a document."
                ),
                entry_ids=ids,
            )
        )
    supporting = t.supporting_ids()
    by_group: dict[str, list[str]] = {}
    for e in supporting:
        by_group.setdefault(t.group_of.get(e, ""), []).append(e)
    for g, ids in by_group.items():
        facts.append(
            Fact(
                text=f"Supported: {t.describe_groups(ids, 1)}.",
                entry_ids=ids,
                quotes=_group_quotes(t, ids),
            )
        )
    for f in t.facts:
        if all(f.text != x.text for x in facts):
            facts.append(f)
    return facts


def _amounts_text(t: AdjustmentTrace, amounts: dict[str, Decimal]) -> str:
    return " / ".join(f"{lbl} {money(amounts.get(lbl, ZERO))}" for lbl in t.labels)


def build_rationale(
    t: AdjustmentTrace,
    treatment: Treatment,
    reason: str,
    proposed: dict[str, Decimal],
    drivers: list[Flag],
) -> str:
    parts = [f"{treatment.value}: {reason}."]
    claimed_ids = t.claimed_ids()
    if claimed_ids:
        traced = {lbl: t.traced(lbl) for lbl in t.labels}
        documented = {lbl: t.documented(lbl) for lbl in t.labels}
        parts.append(
            f"Established: {len(claimed_ids)} GL entries trace to {_amounts_text(t, traced)} "
            f"(documented: {_amounts_text(t, documented)})."
        )
    elif not t.candidates:
        parts.append("Established: no GL entry could be linked to the claim.")
    removed: dict[FlagCode, list[str]] = {}
    for e, r in t.removals.items():
        removed.setdefault(r.code, []).append(e)
    for code, ids in removed.items():
        parts.append(f"Removed ({code.value}): {t.describe_groups(ids, 2)}.")
    effect_codes = sorted({x.code.value for x in t.effects})
    if effect_codes:
        eff = {lbl: t.effect(lbl) for lbl in t.labels}
        parts.append(f"Effects added ({', '.join(effect_codes)}): {_amounts_text(t, eff)}.")
    if treatment == Treatment.REQUEST_INFO:
        pending = "; ".join(sorted({f.code.value for f in drivers}))
        if t.is_normalization and normalization_level(t) is not None:
            n = t.normalization
            basis = "supported" if n is not None and n.level is not None else "implied by the claim, not yet supported"
            parts.append(
                f"Provisional: at a normalized level of {money(normalization_level(t))} a year ({basis}), the GL "
                f"supports {_amounts_text(t, proposed)}."
            )
        else:
            parts.append(f"Provisional amount the evidence would support: {_amounts_text(t, proposed)}.")
        parts.append(f"Pending information ({pending}); excluded from diligence adjusted EBITDA until received.")
    else:
        parts.append(f"Proposed: {_amounts_text(t, proposed)} (claimed: {_amounts_text(t, {lbl: t.claim(lbl) for lbl in t.labels})}).")
    if t.judgments:
        more = f" (+{len(t.judgments) - 1} more)" if len(t.judgments) > 1 else ""
        parts.append(f"Judgment remains: {t.judgments[0]}{more}")
    if t.dropped_quotes:
        parts.append(f"{t.dropped_quotes} AI-proposed quote(s) failed verification and were dropped.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def propose(t: AdjustmentTrace, ai: Optional[EvidenceAI] = None) -> AdjustmentAssessment:
    """Turn a challenged trace into the adjustment's assessment."""
    labels = t.labels
    proposed = compute_proposed(t)
    treatment, drivers, reason = decide_treatment(t, proposed)
    confidence = assess_confidence(t, treatment, proposed, drivers)
    return AdjustmentAssessment(
        adj_id=t.adj.adj_id,
        title=t.adj.title,
        category=t.adj.category,
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
        judgment_questions=list(t.judgments),
        open_questions=build_questions(t, treatment, drivers, ai),
        rationale=build_rationale(t, treatment, reason, proposed, drivers),
    )
