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
    AdjustmentTrace,
    DealIndex,
    _short_sentence,
    entries_word,
    join_limited,
    money,
    month_label,
    month_span,
    periods_text,
    plural,
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
}


def _change_causes(t: AdjustmentTrace) -> str:
    codes = [r.code for r in t.removals.values()] + [x.code for x in t.effects]
    codes += [f.code for f in t.flags if f.code in (FlagCode.PERIOD_MISMATCH, FlagCode.PARTIAL_GL_SUPPORT, FlagCode.SIGN_ERROR)]
    if t.capped:
        codes.append(FlagCode.EXCESS_GL_ACTIVITY)
    return "; ".join(_CAUSE[c] for c in dict.fromkeys(codes) if c in _CAUSE)


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


def build_judgments(t: AdjustmentTrace) -> list[str]:
    """One question per removal basis, citing the groups, amounts and documents, then the
    challenges' own judgment points (ties in the claimed set, levels, unverified AI output)."""
    out: list[str] = []
    by_code: dict[tuple[FlagCode, str], list[str]] = {}
    for e, r in t.removals.items():
        if r.code in (FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA):
            continue  # mechanical: nothing for a reviewer to weigh
        by_code.setdefault((r.code, r.source), []).append(e)
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
            for f in flags:
                lbl = f.period_label
                if not lbl:
                    continue
                if t.is_normalization:
                    add(f"Where is the actual {lbl} cost of the normalized item recorded in the GL?", code, [f])
                else:
                    gap = abs(t.claim(lbl) - t.traced(lbl))
                    add(f"For {lbl}, the GL supports {money(t.traced(lbl))} of the {money(t.claim(lbl))} claimed for "
                        f"{title}; which entries or documents support the remaining {money(gap)}?", code, [f])
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
                add(f"{t.describe(e)} appears to be posted {len(f.entry_ids)} times; was the duplicate reversed, and "
                    "does the claim include it?", code, [f])
    return out


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
    by_group: dict[str, list[str]] = {}
    for e in t.supporting_ids():
        by_group.setdefault(t.group_of.get(e, ""), []).append(e)
    for ids in by_group.values():
        facts.append(Fact(text=f"Supported: {t.describe_groups(ids, 1)}.", entry_ids=ids, quotes=_group_quotes(t, ids)))
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
        if t.is_normalization:
            docs = ""  # the actual cost is payroll; the question is the level, not the invoices
        elif documented == traced:
            docs = ", all with supporting documents" if n > 1 else ", with a supporting document"
        elif not any(documented.values()):
            docs = ", none with a supporting document" if n > 1 else ", without a supporting document"
        else:
            docs = f", of which documented {'; '.join(f'{lbl} {money(documented[lbl])}' for lbl in claimed_labels)}"
        established.append(
            f"{entries_word(n)} {plural(n, 'traces', 'trace')} to "
            f"{'; '.join(f'{lbl} {money(traced[lbl])}' for lbl in claimed_labels)}{docs}."
        )
    elif not t.candidates:
        established.append("No GL entry could be linked to the claim.")
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
        tail.append(f"Judgment: {judgments[0]}{more}")
    if t.dropped_quotes:
        tail.append(f"{t.dropped_quotes} AI quote(s) failed verification and were dropped.")

    def assemble(parts: list[str]) -> str:
        return " ".join(p for p in [head, *parts, outcome, *tail] if p)

    text = assemble(established)
    # Keep the paragraph short: drop the least important established facts first.
    while len(text) > MAX_RATIONALE and len(established) > keep:
        established.pop()
        text = assemble(established)
    if len(text) > MAX_RATIONALE and tail:
        tail = [x for x in tail if not x.startswith("Judgment:")] + (
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
        if not all(e in index.by_id for e in group):
            continue  # a balance-sheet posting has no EBITDA effect
        numbers = {index.by_id[e].doc_number for e in group}
        if len(numbers) != 1 or not next(iter(numbers)):
            continue
        if any(index.by_id[e].klass in EBITDA_EXCLUDED_CLASSES for e in group):
            continue  # below EBITDA: reversing it would not change the bridge
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
        facts.append(Fact(text=f"GL row {index.by_id[e].entry.source_row} is already carried in {carried[e]}.", entry_ids=[e]))
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
