"""Challenges (SPEC §5.4): test each traced adjustment against the evidence.

A challenge can remove claimed entries, add an amount effect (an offsetting
recovery, an out-of-period move), or raise a flag that drives a question or
REQUEST_INFO. Challenges never choose a treatment; propose.py does that from
what is left here. AI output (contradictions, entry classifications) is used
only after its quotes or cited documents are verified, and every amount is
computed from GL entries with Decimal arithmetic.

The cross-adjustment pass (``resolve_overlaps``) runs once over all traces
before the per-adjustment ``run_challenges``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Optional, Sequence

from qoe.ai_base import EvidenceAI, verify_quote
from qoe.money import ZERO, D, fmt, q2
from qoe.periods import add_months
from qoe.schemas import (
    EBITDA_EXCLUDED_CLASSES,
    AdjustmentCategory,
    DocFacts,
    EbitdaClass,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    RecurrenceObservation,
    Severity,
    TermFact,
)
from qoe.trace import (
    AGREEMENT_DOC_TYPES,
    ENTRY_ABOUT_BASES,
    ENTRY_SPECIFIC_BASES,
    W_COUNTERPARTY,
    W_KEYWORD,
    W_KEYWORD_EXTRA,
    W_KEYWORD_EXTRA_CAP,
    W_REFERENCE,
    AdjustmentTrace,
    Effect,
    EntryInfo,
    NormalizationInfo,
    MAX_MESSAGE,
    _short_sentence,
    cents,
    find_subset,
    join_limited,
    keyword_hits,
    keyword_list,
    money,
    month_label,
    month_range_safe,
    month_span,
    name_in_text,
    name_mentioned,
    name_tokens,
    names_match,
    norm_text,
    periods_text,
    ref_tokens,
    theme_similarity,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Comparable activity in a period management left unclaimed, at half the size
# of the claimed group, means the "non-recurring" cost is part of the run-rate.
RECURRENCE_SHARE = Decimal("0.5")
# Three similar months outside the event window is a pattern, not an event.
RECURRENCE_MIN_MONTHS = 3
# A month counts toward that test only when its comparable activity is at least a quarter of
# the group's average claimed month, so routine small charges do not make a large event recur.
RECURRENCE_MONTH_FLOOR = Decimal("0.25")
# Memo themes must share half their words to count as the same kind of cost.
THEME_SIM_SAME_PARTY = 0.5
THEME_SIM_SAME_ACCOUNT = 0.5
# A credit needs two signals (or a reference) before it is netted as a
# recovery: sharing one keyword with the claim is not enough.
RECOVERY_THRESHOLD = 2.0
# SPEC §5.5 rule 4: more than this share of a period's claim without a document -> REQUEST_INFO.
UNDOCUMENTED_SHARE_LIMIT = Decimal("0.25")

# Words shared by a memo and a document that tie them to the same event; one shared
# word (an owner's surname) is not enough, and generic cost words never count.
MIN_SHARED_EVENT_WORDS = 2
_GENERIC_MEMO_WORDS = frozenset(
    """travel services service fee fees payment monthly invoice expense expenses cost costs air hotel
    registration company business personal general office admin""".split()
)

_UNSIGNABLE_DOC_TYPES = frozenset({"invoice", "correspondence", "email", "memo", "payroll"})
BENCHMARK_DOC_TYPES = frozenset(
    {"benchmark", "compensation_survey", "market_study", "survey", "report", "appraisal", "valuation"}
)
_CONTINUING_KINDS = frozenset({"monthly_fee", "ongoing_services", "auto_renew"})
_FEELESS_KINDS = frozenset({"ongoing_services", "auto_renew", "term_end"})
_FEE_LABELS = frozenset({"monthly_fee", "retainer", "recurring_fee", "monthly_retainer"})

_RECURRENCE_REASON = re.compile(
    r"recurr|routine|ongoing|every (?:month|year)|monthly|annual|retainer|prior[- ]year|"
    r"consistent with prior|run[- ]rate|normal course",
    re.IGNORECASE,
)
_PERIODIC = re.compile(
    r"per\s+month|monthly|each\s+month|every\s+month|per\s+(?:quarter|year|annum)|quarterly|annual|"
    r"until\s+terminated|ongoing|recurring|renew",
    re.IGNORECASE,
)
# "payable in three installments" describes a finite fee, not a continuing obligation.
_FINITE = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s+(?:\(\d{1,2}\)\s+)?"
    r"(?:equal\s+)?(?:consecutive\s+)?(?:monthly\s+)?(?:installments?|instalments?|payments?)\b",
    re.IGNORECASE,
)
# A retainer or fee tied to one transaction or one search ends with it (SPEC §5.4).
_ONE_OFF_TERM = re.compile(
    r"one[- ]time|creditable|success fee|upon (?:closing|completion|placement)|(?:payable |due )?(?:up)?on signing|"
    r"retained search|search fee|single (?:transaction|search|engagement)",
    re.IGNORECASE,
)
_MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:\.\d{2})?)")
# A period written right after an amount: "$2,500 per month", "$26,000 a quarter", "$1,200 monthly".
_PERIOD_AFTER = re.compile(r"\s*(?:(?:per|a|each|every)\s+(?:month|quarter|year|annum)|monthly|quarterly|annually)\b", re.I)
_TOTAL_LABEL = re.compile(r"total|due|balance|invoice|amount", re.IGNORECASE)
_MONTH_NAMES = {
    name: i + 1
    for i, names in enumerate(
        [
            ("january", "jan"),
            ("february", "feb"),
            ("march", "mar"),
            ("april", "apr"),
            ("may",),
            ("june", "jun"),
            ("july", "jul"),
            ("august", "aug"),
            ("september", "sep", "sept"),
            ("october", "oct"),
            ("november", "nov"),
            ("december", "dec"),
        ]
    )
    for name in names
}
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})(?:-(\d{2}))?\b")
_US_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_LONG_DATE = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})\b")
# A term length as documents write it: "36-month", "thirty-six (36) months", "3-year", "twelve months".
_TERM_LENGTH = re.compile(
    r"\b(\d{1,3}|[a-z]+(?:-[a-z]+)?)\s*(?:\(\s*(\d{1,3})\s*\))?[\s-]*(month|year)s?\b", re.IGNORECASE
)
_LENGTH_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "eighteen": 18, "twenty-four": 24, "thirty-six": 36, "forty-eight": 48, "sixty": 60,
}
_TERM_START = re.compile(r"(?:commenc\w*|beginning|effective|starting|from)\s+(?:on\s+)?", re.IGNORECASE)
_VALID_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass
class ChallengeContext:
    """What a challenge may need beyond its own trace."""

    ai: Optional[EvidenceAI] = None
    traces: Sequence[AdjustmentTrace] = ()
    claimed_by: dict[str, list[str]] = field(default_factory=dict)  # entry_id -> adj ids that claim it
    # adj_id -> recoveries it nets: (entry_id, score, reasons, doc_ids). Each credit goes to one adjustment.
    recoveries: dict[str, list[tuple[str, float, list[str], list[str]]]] = field(default_factory=dict)

    @classmethod
    def build(cls, ai: Optional[EvidenceAI], traces: Sequence[AdjustmentTrace]) -> "ChallengeContext":
        claimed_by: dict[str, list[str]] = {}
        for t in traces:
            for e in t.claimed_ids():
                claimed_by.setdefault(e, []).append(t.adj.adj_id)
        ctx = cls(ai=ai, traces=traces, claimed_by=claimed_by)
        best: dict[str, tuple[float, int, AdjustmentTrace, list[str], list[str]]] = {}
        for t in traces:
            for eid, score, reasons, docs in _recovery_candidates(t, claimed_by):
                cur = best.get(eid)
                # The strongest relation keeps the recovery; ties go to schedule order.
                if cur is None or (score, -t.order) > (cur[0], -cur[1]):
                    best[eid] = (score, t.order, t, reasons, docs)
        for eid, (score, _, t, reasons, docs) in sorted(best.items()):
            ctx.recoveries.setdefault(t.adj.adj_id, []).append((eid, score, reasons, docs))
        return ctx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _flag(
    t: AdjustmentTrace,
    code: FlagCode,
    severity: Severity,
    message: str,
    *,
    entry_ids: Iterable[str] = (),
    doc_ids: Iterable[str] = (),
    quotes: Iterable[Optional[EvidenceQuote]] = (),
    related: Iterable[str] = (),
    impact: Optional[dict[str, Decimal]] = None,
    label: Optional[str] = None,
    amount_impact: Optional[Decimal] = None,
) -> Flag:
    """Raise a flag. An impact touching one period sets period_label / amount_impact;
    the message states the effect in words either way (see ``_effect``). Quotes go in
    ``Flag.quotes``, never into the message."""
    period_label = label
    impact_str = fmt(amount_impact) if amount_impact is not None else None
    if impact is not None:
        nonzero = {k: v for k, v in impact.items() if v != 0}
        if len(nonzero) == 1:
            period_label, v = next(iter(nonzero.items()))
            impact_str = fmt(v)
    picked: list[EvidenceQuote] = []
    for q in quotes:
        if q is not None and len(picked) < 3 and all((q.doc_id, q.page, q.quote) != (p.doc_id, p.page, p.quote) for p in picked):
            picked.append(q)
    flag = Flag(
        code=code,
        severity=severity,
        message=_short_sentence(message),
        period_label=period_label,
        amount_impact=impact_str,
        entry_ids=t.index.sort_ids(entry_ids),
        doc_ids=sorted(set(doc_ids)),
        quotes=picked,
        related_adj_ids=sorted(set(related)),
    )
    return t.add_flag(flag)


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _sentence(text: str) -> str:
    text = " ".join((text or "").split())
    return text if not text or text[-1] in ".!?" else text + "."


def _quoted(text: str, end: bool = True) -> str:
    """A quote with collapsed whitespace; with ``end`` it closes a sentence exactly once."""
    text = " ".join((text or "").split())
    if not end:
        return f"\"{text}\""
    return f"\"{text}\"" if text[-1:] in ".!?" else f"\"{text}\"."


def _short(text: str, limit: int = 90) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _effect(t: AdjustmentTrace, impact: Optional[dict[str, Decimal]], removed: Iterable[str] = ()) -> str:
    """' Removed <items>: (35,500) in FY2025 and TTM Jun-26.' or ' Effect: ...' ('' when nothing changes)."""
    if not impact or not any(impact.get(lbl) for lbl in t.labels):
        return ""
    removed = list(removed)
    if removed:
        return f" Removed {t.items_text(removed)}: {periods_text(impact, t.labels)}."
    return f" Effect: {periods_text(impact, t.labels)}."


# How a flag that finds its entries already gone names the earlier removal.
_REMOVED_AS = {
    FlagCode.ALREADY_EXCLUDED_FROM_EBITDA: "as already below EBITDA",
    FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT: "as claimed in another adjustment",
    FlagCode.CONTRADICTORY_EVIDENCE: "as contradicted by the documents",
    FlagCode.CONTINUING_OBLIGATION: "as a continuing obligation",
    FlagCode.RECURRING_PATTERN: "as recurring",
}


def _removal_tail(t: AdjustmentTrace, scope: Sequence[str], newly: Sequence[str]) -> str:
    """What a removing flag takes out of the proposal, stated only once per entry.

    The first challenge to remove an entry carries its effect (``AdjustmentTrace.remove``);
    a later flag over the same entries corroborates it, and says so instead of repeating
    an amount that would count twice in the walk from claimed to proposed."""
    new_set = set(newly)
    already = [e for e in scope if e not in new_set]
    text = _effect(t, t.impact_of_removing(newly), newly) if newly else ""
    if already:
        causes = " and ".join(dict.fromkeys(_REMOVED_AS.get(t.removals[e].code, "on other grounds") for e in already))
        if newly:
            subject = t.items_text(already)
            text += f" {subject} {'were' if ' and ' in subject else 'was'} already removed {causes}."
        else:
            text += f" Already removed {causes}; no further effect."
    return text


def _removal_flag(
    t: AdjustmentTrace,
    code: FlagCode,
    severity: Severity,
    message: str,
    scope: Sequence[str],
    newly: Sequence[str],
    corroborating: Sequence[str] = (),
    **kwargs,
) -> Flag:
    """Raise a removing flag (message + the removal tail) and record it as the owner of ``newly``."""
    text = _with_corroboration(message, corroborating, _removal_tail(t, scope, newly))
    flag = _flag(t, code, severity, text, entry_ids=scope, impact=t.impact_of_removing(newly), **kwargs)
    t.attach(newly, flag)
    return flag

def _doc_says(doc_id: str, statement: str, facts: Optional[DocFacts] = None) -> str:
    """'<doc> <what it says>.', naming the document once.

    The AI's statement is either a predicate ('describes the fee as a subscription')
    or a sentence; a sentence that already names the document is used as it is.
    """
    st = _sentence(statement)
    if not st:
        return f"{doc_id} conflicts with management's description."
    title = (facts.title if facts else "") or ""
    if doc_id in st or (len(title) > 8 and title in st):
        return st
    if st[0].islower():
        return f"{doc_id} {st}"
    return f"{doc_id}: {st[0].lower() + st[1:] if st[1:2].islower() else st}"

def _with_corroboration(msg: str, others: Sequence[str], tail: str = "") -> str:
    """Name corroborating documents only while the message stays short; they remain in doc_ids either way."""
    if others:
        longer = f"{msg} Corroborated by {join_limited(list(others), 1)}.{tail}"
        if len(longer) <= MAX_MESSAGE:
            return longer
    return msg + tail


def _term_brief(term: TermFact) -> str:
    """A term's description without parentheticals ('term ends 2027-12-31')."""
    return _short(re.sub(r"\s*\([^)]*\)", "", term.text) or term.text, 50)


def _groups_text(t: AdjustmentTrace, entry_ids: Iterable[str], limit: int = 1) -> str:
    """A compact name for an entry set ('Marlow & Finch LLP · Matter 3002 and 2 more')."""
    return t.items_text(entry_ids, limit)


def _has_verified_content(facts: Optional[DocFacts]) -> bool:
    return bool(facts and (facts.key_statements or facts.amounts or facts.terms))


def _adapter_drops(ai: Optional[EvidenceAI]) -> int:
    """Quotes the AI adapter has rejected so far (an LLM adapter counts them; the rules do not)."""
    value = getattr(ai, "dropped_quotes", 0)
    return value if isinstance(value, int) else 0


_REASON_STOP = frozenset(
    """the and for with this that from were was are not does its their into than because under which
    entry entries cost costs expense expenses document basis management claim claimed""".split()
)


def _content_words(text: str) -> set[str]:
    return {w[:6] for w in norm_text(text).split() if len(w) >= 4 and w not in _REASON_STOP}


def _reason_quote(facts: DocFacts, reason: str) -> Optional[EvidenceQuote]:
    """The document's verified quote that best matches a classification reason, if any shares its words."""
    words = _content_words(reason)
    best: Optional[tuple[int, EvidenceQuote]] = None
    for q in list(facts.key_statements) + [x.quote for x in facts.terms] + [a.quote for a in facts.amounts]:
        shared = len(words & _content_words(q.quote))
        if shared and (best is None or shared > best[0]):
            best = (shared, q)
    return best[1] if best else None


def _first_statement(facts: Optional[DocFacts], pattern: Optional[re.Pattern[str]] = None) -> Optional[EvidenceQuote]:
    if facts is None:
        return None
    for q in facts.key_statements:
        if pattern is None or pattern.search(q.quote):
            return q
    return None


def _amount_is(stated: str, amount: Decimal, tol: Decimal) -> bool:
    try:
        return abs(abs(D(stated)) - abs(amount)) <= tol
    except ValueError:
        return False


def _doc_relates_to_entry(t: AdjustmentTrace, doc_id: str, entry_id: str) -> bool:
    """Code-side check on an AI-proposed (document, entry) pair: the document must demonstrably be about the entry."""
    idx = t.index
    info = idx.by_id.get(entry_id)
    if info is None:
        return False
    dl = t.doc_links.get(doc_id)
    if dl is not None and dl.entry_basis.get(entry_id) in ENTRY_SPECIFIC_BASES | {"reference", "amount_multi"}:
        return True
    doc_cp = idx.doc_cp.get(doc_id, frozenset())
    if names_match(info.cp_tokens, doc_cp) or name_mentioned(doc_cp, info.memo_tokens):
        return True
    if any(d == doc_id for d, _ in idx.docs_with_amount(info.amount)):
        return True
    # The memo and the document name the same event ("AHR Expo", "supplier plant visit").
    facts = idx.facts.get(doc_id)
    doc_words = idx.doc_text_tokens.get(doc_id, frozenset()) | frozenset(
        norm_text(f"{doc_id} {facts.title if facts else ''}").split()
    )
    shared = {w for w in info.theme if len(w) >= 3 and w not in _GENERIC_MEMO_WORDS} & doc_words
    return len(shared) >= MIN_SHARED_EVENT_WORDS


def _valid_months(months: Iterable[str]) -> list[str]:
    return sorted({m for m in months if isinstance(m, str) and _VALID_MONTH.match(m)})


def _median_abs(values: list[Decimal]) -> Decimal:
    vals = sorted(abs(v) for v in values)
    if not vals:
        return ZERO
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


# ---------------------------------------------------------------------------
# Cross-adjustment pass
# ---------------------------------------------------------------------------


def resolve_overlaps(traces: Sequence[AdjustmentTrace]) -> None:
    """An entry claimed by several adjustments stays with the strongest link
    (ties go to schedule order); the others lose it with a CRITICAL flag."""
    by_order = {t.order: t for t in traces}
    claimants: dict[str, list[AdjustmentTrace]] = {}
    for t in traces:
        for e in t.claimed_ids():
            claimants.setdefault(e, []).append(t)
    lost: dict[tuple[int, int], list[str]] = {}
    for e, ts in claimants.items():
        if len(ts) < 2:
            continue
        winner = max(ts, key=lambda x: (x.links[e].score, -x.order))
        for t in ts:
            if t is not winner:
                lost.setdefault((t.order, winner.order), []).append(e)
    for (lo, wo), eids in sorted(lost.items()):
        loser, winner = by_order[lo], by_order[wo]
        eids = loser.index.sort_ids(eids)
        ls = max(loser.links[e].score for e in eids)
        ws = max(winner.links[e].score for e in eids)
        n = len(eids)
        it = _plural(n, "it", "them")
        why = f"links {it} more strongly" if ws != ls else "comes first in the schedule (the links are equally strong)"
        docs = sorted({d for e in eids for d in loser.entry_docs(e) + winner.entry_docs(e)})
        newly = loser.remove(
            eids, FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, f"also claimed in {winner.adj.adj_id}, which {why}", doc_ids=docs
        )
        impact = loser.impact_of_removing(newly)
        flag = _flag(
            loser,
            FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
            Severity.CRITICAL,
            f"{loser.describe_many(eids, 1)} {_plural(n, 'is', 'are')} also claimed in {winner.adj.adj_id} "
            f"({winner.adj.title}), which {why}; removed here so the cost is not added back twice."
            + _effect(loser, impact),
            entry_ids=eids,
            doc_ids=docs,
            related=[winner.adj.adj_id],
            impact=impact,
        )
        loser.attach(newly, flag)
        winner.add_fact(
            Fact(
                text=(
                    f"{winner.describe_many(eids, 1)} {_plural(n, 'is', 'are')} also claimed in {loser.adj.adj_id}; "
                    f"kept here because this adjustment {why}."
                ),
                entry_ids=eids,
            )
        )


# ---------------------------------------------------------------------------
# Per-adjustment challenges
# ---------------------------------------------------------------------------


def run_challenges(t: AdjustmentTrace, ctx: ChallengeContext) -> None:
    """Every §5.4 challenge, in an order where removals are attributed to the
    strongest evidence first (code facts, then verified quotes, then AI
    classifications, then pattern analysis)."""
    already_excluded(t)
    contradictions(t, ctx)
    entry_qualification(t, ctx)
    continuing_obligation(t)
    recurring_pattern(t)
    out_of_period(t)
    offsetting_recovery(t, ctx)
    counterparty_history(t)
    period_mismatch(t)
    sign_error(t)
    duplicate_entries(t)
    doc_gl_amount_mismatch(t)
    unsigned_or_draft(t)
    normalization(t)
    pro_forma(t)
    document_coverage(t)


def already_excluded(t: AdjustmentTrace) -> None:
    idx = t.index
    by_account: dict[str, list[str]] = {}
    for e in t.claimed_ids():
        info = idx.by_id[e]
        if info.klass in EBITDA_EXCLUDED_CLASSES:
            by_account.setdefault(info.entry.account, []).append(e)
    for acct, eids in sorted(by_account.items()):
        info = idx.by_id[eids[0]]
        klass = info.klass.value
        docs = sorted({d for e in eids for d in t.entry_docs(e)})
        newly = t.remove(eids, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, f"{acct} is {klass}, already below EBITDA", doc_ids=docs)
        impact = t.impact_of_removing(newly)
        total = sum((t.amount(e) for e in eids), ZERO)
        n = len(eids)
        flag = _flag(
            t,
            FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
            Severity.CRITICAL,
            f"{n} claimed {_plural(n, 'entry', 'entries')} ({money(total)}) sit in {acct} {info.entry.account_name}, "
            f"classified {klass}, which EBITDA already adds back; adding {_plural(n, 'it', 'them')} back again would "
            f"double count." + _effect(t, impact),
            entry_ids=eids,
            doc_ids=docs,
            impact=impact,
        )
        t.attach(newly, flag)
        account = idx.accounts.get(acct)
        basis = f" ({account.mapping_basis})" if account is not None and account.mapping_basis else ""
        t.add_fact(Fact(text=f"Account {acct} {info.entry.account_name} maps to {klass}{basis}.", entry_ids=eids))
        # Show the add-back management's own schedule already makes for this class.
        mgmt, gl = idx.mgmt_lines.get(info.klass, {}), idx.gl_lines.get(info.klass, {})
        for lbl in t.labels:
            claimed_here = [e for e in eids if e in t.claimed.get(lbl, [])]
            if not claimed_here or lbl not in mgmt or lbl not in gl:
                continue
            here = sum((t.amount(e) for e in claimed_here), ZERO)
            line = klass.lower().replace("_", " ")
            if abs(abs(mgmt[lbl]) - abs(gl[lbl])) <= idx.tolerance:
                text = (
                    f"{lbl}: management's {line} line ({money(abs(mgmt[lbl]))}) equals the GL {line} total, which "
                    f"includes these {money(here)}, so the schedule already adds them back once."
                )
            else:
                text = (
                    f"{lbl}: management's {line} line is {money(abs(mgmt[lbl]))} against a GL {line} total of "
                    f"{money(abs(gl[lbl]))} that includes these {money(here)}."
                )
            t.add_fact(Fact(text=text, entry_ids=claimed_here))


def contradictions(t: AdjustmentTrace, ctx: ChallengeContext) -> None:
    """Verified AI contradictions, deduplicated to one statement per document. The AI
    may name entries; code keeps only those the document demonstrably relates to."""
    idx = t.index
    if ctx.ai is None or not t.doc_links:
        return
    facts = [idx.facts[d] for d in t.evidence_docs() if d in idx.facts]
    claimed = t.in_play_ids()
    if not claimed or not facts:
        return
    before = _adapter_drops(ctx.ai)
    try:
        found = ctx.ai.find_contradictions(t.adj, t.intent, facts, [idx.by_id[e].entry for e in claimed])
    except Exception as exc:  # an AI failure must not stop the review; it is recorded
        t.notes.append(f"find_contradictions failed: {exc}")
        return
    finally:
        t.ai_dropped_quotes += max(0, _adapter_drops(ctx.ai) - before)
    by_doc: dict[str, list] = {}
    for c in found:
        if c.quote.doc_id != c.doc_id or not verify_quote(c.quote, idx.docs):
            t.dropped_quotes += 1
            continue
        by_doc.setdefault(c.doc_id, []).append(c)
    claimed_set = set(claimed)
    claimed_groups = {t.group_of[e] for e in claimed if e in t.group_of}
    removable = not (t.is_normalization or t.is_pro_forma)
    # One statement per document (the AI lists its strongest first); documents that
    # contradict the same entries share one flag.
    merged: dict[tuple[str, ...], list[tuple[str, list[EvidenceQuote], str]]] = {}
    for doc_id, items in by_doc.items():
        quotes: list[EvidenceQuote] = []
        for c in items:
            if all((c.quote.page, c.quote.quote) != (x.page, x.quote) for x in quotes) and len(quotes) < 2:
                quotes.append(c.quote)
        statement = next((c.statement for c in items if c.statement.strip()), "")
        proposed = {e for c in items for e in c.entry_ids if e in claimed_set}
        scope = [e for e in claimed if e in proposed and _doc_relates_to_entry(t, doc_id, e)]
        if not scope and not proposed:
            groups = [g for g in t.groups_for_doc(doc_id) if g in claimed_groups]
            scope = [e for e in claimed if t.group_of.get(e) in groups]
            if not scope and len(claimed_groups) == 1:
                # One kind of activity is claimed, so a document contradicting the claim covers all of it.
                scope = list(claimed)
        merged.setdefault(tuple(scope), []).append((doc_id, quotes, statement))
    for scope_key, docs in merged.items():
        scope = list(scope_key)
        doc_ids = [d for d, _, _ in docs]
        quotes = [q for _, qs, _ in docs for q in qs][:3]
        lead, _, statement = docs[0]
        msg = _doc_says(lead, statement, idx.facts.get(lead))
        if scope and removable:
            newly = t.remove(scope, FlagCode.CONTRADICTORY_EVIDENCE, f"contradicted by {lead}", doc_ids=doc_ids)
            _removal_flag(
                t, FlagCode.CONTRADICTORY_EVIDENCE, Severity.WARNING, msg, scope, newly,
                corroborating=doc_ids[1:], doc_ids=doc_ids, quotes=quotes,
            )
        else:
            tail = ""
            if not scope:
                tail = " It could not be tied to specific GL entries, so nothing was removed."
                t.add_judgment(
                    f"Does {lead} undermine the {t.adj.title} adjustment as a whole? It could not be tied to specific "
                    "GL entries, so nothing was removed.",
                    key=f"doc:{lead}",
                )
            _flag(
                t,
                FlagCode.CONTRADICTORY_EVIDENCE,
                Severity.WARNING,
                _with_corroboration(msg, doc_ids[1:], tail),
                entry_ids=scope,
                doc_ids=doc_ids,
                quotes=quotes,
            )
        for doc_id, qs, stmt in docs:
            t.add_fact(Fact(text=_doc_says(doc_id, stmt, idx.facts.get(doc_id)), entry_ids=scope, quotes=qs), key=f"doc:{doc_id}")


def entry_qualification(t: AdjustmentTrace, ctx: ChallengeContext) -> None:
    """Remove entries an AI classification says do not fit management's basis,
    but only when it cites a document with verified content."""
    idx = t.index
    if ctx.ai is None or t.is_normalization or t.is_pro_forma:
        return
    remaining = t.supporting_ids()
    if not remaining:
        return
    facts = [idx.facts[d] for d in t.evidence_docs() if d in idx.facts]
    before = _adapter_drops(ctx.ai)
    try:
        results = ctx.ai.classify_entries(t.adj, t.intent, [idx.by_id[e].entry for e in remaining], facts)
    except Exception as exc:  # an AI failure must not stop the review; it is recorded
        t.notes.append(f"classify_entries failed: {exc}")
        return
    finally:
        t.ai_dropped_quotes += max(0, _adapter_drops(ctx.ai) - before)
    remaining_set = set(remaining)
    # Recurrence is the premise of owner and normalization items, so it is never the removal code there.
    recurrence_applies = not _recurrence_is_premise(t)
    buckets: dict[tuple[FlagCode, str, tuple[str, ...]], list[str]] = {}
    unverified: list[str] = []
    for c in results:
        if c.qualifies or c.entry_id not in remaining_set:
            continue
        docs = sorted(
            {
                d
                for d in c.doc_ids
                if d in idx.docs and _has_verified_content(idx.facts.get(d)) and _doc_relates_to_entry(t, d, c.entry_id)
            }
        )
        if not docs:
            unverified.append(c.entry_id)
            continue
        recurring = recurrence_applies and _RECURRENCE_REASON.search(c.reason)
        code = FlagCode.RECURRING_PATTERN if recurring else FlagCode.CONTRADICTORY_EVIDENCE
        buckets.setdefault((code, " ".join(c.reason.split()), tuple(docs)), []).append(c.entry_id)
    for (code, reason, docs), eids in sorted(buckets.items(), key=lambda kv: idx.by_id[kv[1][0]].pos):
        newly = t.remove(eids, code, f"does not fit management's basis per {docs[0]}", source="ai", doc_ids=docs)
        impact = t.impact_of_removing(newly)
        for d in docs:
            for e in eids:
                t.associate(d, e, "classification", 0.0, "")
        # Cite the passage the reason rests on, not whatever the document happens to say first.
        quotes = [q for d in docs if (q := _reason_quote(idx.facts[d], reason)) is not None]
        quotes = quotes or [q for d in docs for q in idx.facts[d].key_statements[:1]]
        n = len(eids)
        flag = _flag(
            t,
            code,
            Severity.WARNING,
            f"{_groups_text(t, eids)} {_plural(n, 'does', 'do')} not fit management's basis per "
            f"{join_limited(list(docs), 1)}: {_sentence(_short(reason, 140))}" + _effect(t, impact),
            entry_ids=eids,
            doc_ids=list(docs),
            quotes=quotes,
            impact=impact,
        )
        t.attach(newly, flag)
    if unverified:
        t.add_judgment(
            f"The AI suggested that {t.describe_many(unverified, 2)} may not fit management's basis but cited no "
            "verifiable document that relates to them, so they were kept. Should they be removed?",
            key="ai:unverified",
        )


def _money_in(text: str) -> list[Decimal]:
    out: list[Decimal] = []
    for m in _MONEY.finditer(text or ""):
        try:
            out.append(D(m.group(1)))
        except ValueError:
            continue
    return out


def _term_fee(term: TermFact) -> Optional[Decimal]:
    """The fee a term states, read from its verified quote.

    ``term.text`` is the extractor's own description (free text when an LLM wrote it), so it
    may only pick which of the quote's amounts is the fee, never supply an amount itself.
    Otherwise the amount written next to a periodic cue ("$8,000 per month") is the fee."""
    text = term.quote.quote
    in_quote = _money_in(text)
    for amount in _money_in(term.text):
        if amount in in_quote:
            return amount
    for m in _MONEY.finditer(text):
        if _PERIODIC.search(text[max(0, m.start() - 25) : m.start()]) or _PERIOD_AFTER.match(text, m.end()):
            return D(m.group(1))
    return in_quote[0] if in_quote else None


def _dates_in(text: str) -> list[str]:
    """Months ('YYYY-MM') of the dates written in a text, in order of appearance."""
    found: list[tuple[int, str]] = []
    for m in _ISO_DATE.finditer(text):
        if 1 <= int(m.group(2)) <= 12:
            found.append((m.start(), f"{m.group(1)}-{m.group(2)}"))
    for m in _US_DATE.finditer(text):
        if 1 <= int(m.group(1)) <= 12:
            found.append((m.start(), f"{m.group(3)}-{int(m.group(1)):02d}"))
    for m in _LONG_DATE.finditer(text):
        mon = _MONTH_NAMES.get(m.group(1).lower())
        if mon:
            found.append((m.start(), f"{m.group(3)}-{mon:02d}"))
    return [month for _, month in sorted(found)]


def _term_months(text: str) -> Optional[int]:
    """The first term length the text states, in months."""
    for m in _TERM_LENGTH.finditer(text):
        raw = m.group(2) or m.group(1)
        n = int(raw) if raw.isdigit() else _LENGTH_WORDS.get(raw.lower())
        if n:
            return n * 12 if m.group(3).lower() == "year" else n
    return None


def _term_end_month(term: TermFact, facts: DocFacts) -> Optional[str]:
    # Lengths and dates come from the verified quote only: the extractor's description of the
    # term (free text when an LLM wrote it) is not evidence of when the obligation ends.
    text = term.quote.quote
    n = _term_months(text)
    start = _TERM_START.search(text)
    if n and start:
        after = _dates_in(text[start.end() :])
        if after:
            return add_months(after[0], n - 1)
    dates = _dates_in(text)
    if dates:
        return max(dates)
    if facts.service_period_end and _VALID_MONTH.match(facts.service_period_end[:7]):
        return facts.service_period_end[:7]
    return None


def _recurrence_is_premise(t: AdjustmentTrace) -> bool:
    """Owner and normalization items recur by design (SPEC §5.4): recurrence cannot undercut them."""
    return t.is_normalization or t.adj.category in (
        AdjustmentCategory.OWNER_DISCRETIONARY,
        AdjustmentCategory.NORMALIZATION,
    )

def _one_off(text: str) -> bool:
    return bool(_ONE_OFF_TERM.search(text or ""))


def continuing_obligation(t: AdjustmentTrace) -> None:
    """A document term that carries the cost into the go-forward cost base (SPEC §5.4):
    a periodic fee, 'until terminated', auto-renewal, ongoing services, or a service
    term ending after the last claimed month. A one-time retainer or fee tied to a
    single transaction or search does not qualify, whatever the letter calls it."""
    idx = t.index
    if not t.asserts_nonrecurring:
        return
    claimed = t.in_play_ids()
    if not claimed:
        return
    tol = idx.tolerance
    last = max(idx.by_id[e].month for e in claimed)
    by_scope: dict[tuple[str, ...], list[tuple[str, list[TermFact]]]] = {}
    claimed_groups = {t.group_of[e] for e in claimed if e in t.group_of}
    for doc_id in t.evidence_docs():
        facts = idx.facts.get(doc_id)
        if facts is None or not facts.terms:
            continue
        # A letter that frames its retainer as one-time or creditable against a success fee
        # describes a single engagement, even where a term on its own reads as a retainer.
        # Only verified quotes decide: a term's description is the extractor's paraphrase (an LLM's
        # free text in LLM mode), so "one-time" or "three installments" written there proves nothing.
        doc_one_off = any(_one_off(q.quote) for q in facts.key_statements) or any(
            _one_off(x.quote.quote) for x in facts.terms
        )
        terms: list[TermFact] = []
        fees: list[Decimal] = []
        feeless = False
        for term in facts.terms:
            kind = term.kind.strip().lower()
            text = term.quote.quote
            if _FINITE.search(text):
                continue
            if kind in ("auto_renew", "ongoing_services"):
                ok = True
            elif _one_off(text) or (doc_one_off and kind in ("retainer", "term_end")):
                ok = False
            elif kind == "monthly_fee":
                ok = True
            elif kind == "retainer":
                ok = bool(_PERIODIC.search(text))
            elif kind == "term_end":
                end = _term_end_month(term, facts)
                ok = end is not None and end > last
            else:
                ok = False
            if not ok:
                continue
            terms.append(term)
            fee = _term_fee(term)
            if fee is not None and fee > 0:
                fees.append(fee)
            elif kind in _FEELESS_KINDS or kind == "retainer":
                feeless = True
        if not terms:
            continue
        for a in facts.amounts:
            if a.label.strip().lower() in _FEE_LABELS:
                try:
                    fees.append(abs(D(a.amount)))
                except ValueError:
                    pass
        doc_groups = set(t.groups_for_doc(doc_id)) & claimed_groups
        doc_cp = idx.doc_cp.get(doc_id, frozenset())
        fee_hits = [
            e
            for e in claimed
            if any(abs(abs(t.amount(e)) - fee) <= tol for fee in fees)
            and (t.group_of.get(e) in doc_groups or names_match(idx.by_id[e].cp_tokens, doc_cp))
        ]
        covered = {t.group_of[e] for e in fee_hits}
        if feeless:
            covered |= doc_groups
        scope = [e for e in claimed if t.group_of.get(e) in covered]
        if scope:
            by_scope.setdefault(tuple(scope), []).append((doc_id, terms))
    # Several documents evidencing the same obligation (an engagement letter and a retainer invoice) share one flag.
    for scope_key, docs in by_scope.items():
        scope = list(scope_key)
        doc_ids = [d for d, _ in docs]
        lead, lead_terms = docs[0]
        newly = t.remove(scope, FlagCode.CONTINUING_OBLIGATION, f"{lead} sets a continuing obligation", doc_ids=doc_ids)
        described = "; ".join(dict.fromkeys(_term_brief(term) for term in lead_terms[:2]))
        msg = f"{lead} sets a continuing obligation ({described}) that runs past the last claimed month ({month_label(last)})."
        _removal_flag(
            t, FlagCode.CONTINUING_OBLIGATION, Severity.WARNING, msg, scope, newly,
            corroborating=doc_ids[1:], doc_ids=doc_ids, quotes=[term.quote for _, ts in docs for term in ts][:3],
        )
        for doc_id, ts in docs:
            t.add_fact(
                Fact(
                    text=f"{doc_id} sets {'; '.join(dict.fromkeys(_short(x.text, 60) for x in ts[:2]))}.",
                    entry_ids=scope,
                    quotes=[x.quote for x in ts[:2]],
                ),
                key=f"doc:{doc_id}",
            )


@dataclass
class _Profile:
    cp: frozenset[str]
    ref: str
    theme: tuple[str, ...]
    accounts: frozenset[str]


def _comparable_reason(info: EntryInfo, p: _Profile) -> str:
    if p.ref and p.ref in info.refs and (not p.cp or not info.cp_tokens or names_match(info.cp_tokens, p.cp)):
        return f"same reference {p.ref}"
    sim = theme_similarity(info.theme, p.theme)
    if p.cp and names_match(info.cp_tokens, p.cp):
        if sim >= THEME_SIM_SAME_PARTY or (not p.theme and not info.theme):
            return "same party and memo theme"
        return ""
    if p.theme and info.entry.account in p.accounts and sim >= THEME_SIM_SAME_ACCOUNT:
        return "same account and memo theme"
    return ""


def recurring_pattern(t: AdjustmentTrace) -> None:
    """Record comparable activity for each claimed group; remove groups that recur (SPEC §5.4).

    Two tests: comparable activity in a period the claim does not cover, at half the
    claimed group's amount or more; or at least three months outside the event
    window (the union of the months of the group's claimed entries) whose comparable
    activity is at least a quarter of the group's average claimed month.
    """
    idx = t.index
    if not t.asserts_nonrecurring or _recurrence_is_premise(t):
        return
    claimed = t.in_play_ids()
    if not claimed:
        return
    tol = idx.tolerance
    # Activity inside this claim (including items lost to another adjustment) is not "elsewhere".
    claimed_set = set(t.claimed_ids())
    uncovered = [lbl for lbl in t.labels if t.claim(lbl) == 0]
    for g in dict.fromkeys(t.group_of[e] for e in claimed if e in t.group_of):
        g_claimed = [e for e in claimed if t.group_of.get(e) == g]
        net = sum((t.amount(e) for e in g_claimed), ZERO)
        s = -1 if net < 0 else 1
        per_label = {lbl: s * sum((t.amount(e) for e in g_claimed if e in t.claimed.get(lbl, [])), ZERO) for lbl in t.labels}
        g_amount = max(per_label.values())
        if g_amount <= tol:
            continue
        first = idx.by_id[g_claimed[0]]
        profile = _Profile(
            cp=first.cp_tokens,
            ref=t.group_ref.get(g, ""),
            theme=first.theme,
            accounts=frozenset(idx.by_id[e].entry.account for e in g_claimed),
        )
        comparables: list[tuple[EntryInfo, str]] = []
        for info in idx.entries:
            # Activity inside this claim is the claim itself, not evidence that it recurs.
            if info.entry_id in claimed_set or s * info.amount <= 0:
                continue
            why = _comparable_reason(info, profile)
            if why:
                comparables.append((info, why))
        if not comparables:
            continue
        by_label = {
            lbl: sum((info.amount for info, _ in comparables if info.month in idx.label_months[lbl]), ZERO)
            for lbl in t.labels
        }
        prior_hits = [lbl for lbl in uncovered if s * by_label[lbl] >= RECURRENCE_SHARE * g_amount]
        window = {idx.by_id[e].month for e in g_claimed}
        floor = RECURRENCE_MONTH_FLOOR * s * net / len(window)
        by_month: dict[str, Decimal] = {}
        for info, _ in comparables:
            if info.month not in window:
                by_month[info.month] = by_month.get(info.month, ZERO) + s * info.amount
        similar_months = sorted(m for m, v in by_month.items() if v >= floor)
        recurring = bool(prior_hits) or len(similar_months) >= RECURRENCE_MIN_MONTHS
        comp_ids = [info.entry_id for info, _ in comparables]
        for info, why in comparables:
            t.add_context_link(info.entry_id, 0.0, f"Comparable to {g} ({why})")

        parts: list[str] = []
        for lbl in prior_hits:
            pct = int((s * by_label[lbl] / g_amount * 100).to_integral_value())
            parts.append(
                f"{money(by_label[lbl])} of comparable activity in {lbl}, where nothing is claimed "
                f"({pct}% of the {money(s * g_amount)} claimed)"
            )
        if len(similar_months) >= RECURRENCE_MIN_MONTHS:
            parts.append(
                f"similar activity in {len(similar_months)} months outside the claimed window "
                f"({month_span(similar_months)})"
            )
        claimed_txt = ", ".join(f"{lbl} {money(s * v)}" for lbl, v in per_label.items() if v)
        seen = ", ".join(f"{lbl} {money(v)}" for lbl, v in by_label.items() if v)
        note = f"Claimed: {claimed_txt}. Comparable activity outside the claim: {seen}."
        t.recurrence.append(
            RecurrenceObservation(
                group=g,
                amounts_by_period={lbl: fmt(v) for lbl, v in by_label.items()},
                entry_ids=idx.sort_ids(comp_ids),
                note=note if recurring else note + " Below the recurrence threshold.",
            )
        )
        if recurring:
            newly = t.remove(g_claimed, FlagCode.RECURRING_PATTERN, "comparable activity outside the claimed window")
            flag = _flag(
                t,
                FlagCode.RECURRING_PATTERN,
                Severity.WARNING,
                f"{t.items_text(g_claimed, 1)} recurs: {'; '.join(parts)}." + _removal_tail(t, g_claimed, newly),
                entry_ids=g_claimed + comp_ids,
                impact=t.impact_of_removing(newly),
            )
            t.attach(newly, flag)
        elif any(by_label[lbl] for lbl in uncovered):
            below = ", ".join(f"{lbl} {money(by_label[lbl])}" for lbl in uncovered if by_label[lbl])
            t.add_judgment(
                f"{g} has comparable activity where nothing is claimed ({below}), below the recurrence threshold. "
                "Should only the excess over that routine level be added back?",
                key=f"group:{g}",
            )


def _service_quote(facts: DocFacts, months: list[str]) -> Optional[EvidenceQuote]:
    years = {m[:4] for m in months}
    pattern = re.compile(r"service|period|" + "|".join(sorted(years)), re.IGNORECASE)
    for q in facts.key_statements + [a.quote for a in facts.amounts] + [x.quote for x in facts.terms]:
        if pattern.search(q.quote):
            return q
    return None


def out_of_period(t: AdjustmentTrace) -> None:
    """Move entries whose documented service period sits in another analysis period.

    The entry leaves the supporting set and is replaced entirely by its effect: + the
    amount in each period containing the booking month, - the amount pro rata by the
    service months each period contains. Service months before ``data_start`` are
    outside the analysis, so no negative side is carried for them (SPEC §5.4).
    """
    idx = t.index
    for e in t.supporting_ids():
        if e in t.moved:
            continue
        info = idx.by_id[e]
        for doc_id in t.entry_docs_by_basis(e, ENTRY_SPECIFIC_BASES):
            facts = idx.facts[doc_id]
            s_months = month_range_safe(facts.service_period_start, facts.service_period_end)
            if not s_months or info.month in s_months:
                continue
            book_labels = set(idx.labels_of(info.month))
            svc_labels = {lbl for m in s_months for lbl in idx.labels_of(m)}
            # Service months outside every analysis period (before data_start, say) are a different
            # fiscal period even when the rest of the service falls in the booking period's labels.
            outside = [m for m in s_months if not idx.labels_of(m)]
            if book_labels == svc_labels and not outside:
                continue
            total_months = len(s_months)
            contrib: dict[str, Decimal] = {}
            realloc: dict[str, Decimal] = {}
            for lbl in t.labels:
                n_in = sum(1 for m in s_months if m in idx.label_months[lbl])
                minus = q2(info.amount * n_in / total_months) if n_in else ZERO
                plus = info.amount if info.month in idx.label_months[lbl] else ZERO
                contrib[lbl] = plus - minus
                realloc[lbl] = contrib[lbl] - (info.amount if e in t.claimed.get(lbl, []) else ZERO)
            t.moved.add(e)
            moves = [Effect(lbl, v, FlagCode.OUT_OF_PERIOD, e) for lbl, v in contrib.items() if v]
            t.effects.extend(moves)
            quote = _service_quote(facts, s_months)
            order = t.labels.index
            belongs = ", ".join(sorted(svc_labels, key=order)) or "months before the analysis periods"
            booked = ", ".join(sorted(book_labels, key=order)) or "the booking month"
            msg = (
                f"{t.entry_ref(e)} ({money(info.amount)}) covers services in {month_span(s_months)} per {doc_id}, so "
                f"the cost belongs to {belongs} and moves out of {booked} pro rata by service month."
            )
            if outside:
                msg += (
                    f" {len(outside)} service {_plural(len(outside), 'month falls', 'months fall')} outside the "
                    "analysis periods, so no negative side is carried for them."
                )
            flag = _flag(
                t,
                FlagCode.OUT_OF_PERIOD,
                Severity.WARNING,
                msg + _effect(t, realloc),
                entry_ids=[e],
                doc_ids=[doc_id],
                quotes=[quote],
                impact=realloc,
            )
            for x in moves:
                x.flag = flag
            t.add_fact(
                Fact(
                    text=f"{doc_id} states a service period of {month_span(s_months)} for {t.describe(e)}.",
                    entry_ids=[e],
                    quotes=[quote] if quote else [],
                ),
                key=f"doc:{doc_id}",
            )
            break


def _recovery_candidates(
    t: AdjustmentTrace, claimed_by: dict[str, list[str]]
) -> list[tuple[str, float, list[str], list[str]]]:
    """Unadjusted credits that relate to the claimed event: (entry_id, score, reasons, doc_ids)."""
    idx = t.index
    if t.is_normalization or t.is_pro_forma:
        return []
    claimed = t.claimed_ids()
    if not claimed:
        return []
    net = sum((t.amount(e) for e in claimed), ZERO)
    if net == 0:
        return []
    direction = 1 if net > 0 else -1
    start = min([idx.by_id[e].month for e in claimed] + _valid_months(t.intent.event_months))
    cost_accounts = {idx.by_id[e].entry.account for e in claimed}
    claimed_set = set(claimed)
    # Only documents about the claim itself: a reference stated in a document that is merely
    # context (a prior-year comparable) must not pull in another event's recovery.
    docs = sorted(
        d
        for d, dl in t.doc_links.items()
        if dl.prelinked or any(e in claimed_set and b in ENTRY_SPECIFIC_BASES for e, b in dl.entry_basis.items())
    )
    refs: dict[str, tuple[str, str]] = {}
    for r in t.intent.reference_numbers:
        for n in sorted(ref_tokens(r)):
            refs.setdefault(n, (r.strip(), ""))
    for doc_id in docs:
        for raw in idx.facts[doc_id].reference_numbers:
            for n in sorted(ref_tokens(raw)):
                refs.setdefault(n, (raw.strip(), doc_id))
    names: list[tuple[str, frozenset[str]]] = [(n, name_tokens(n)) for n in t.intent.counterparties]
    names += [(idx.facts[d].counterparty or "", idx.doc_cp[d]) for d in docs if idx.doc_cp[d]]
    names += [(idx.by_id[e].entry.counterparty, idx.by_id[e].cp_tokens) for e in claimed if idx.by_id[e].cp_tokens]
    names = [(n, toks) for n, toks in names if toks]
    keywords = keyword_list(t.intent.keywords)
    out: list[tuple[str, float, list[str], list[str]]] = []
    for info in idx.entries:
        eid = info.entry_id
        if eid in claimed_by or info.amount == 0 or (info.amount > 0) == (direction > 0) or info.month < start:
            continue
        if not (info.klass in (EbitdaClass.OTHER_INCOME, EbitdaClass.REVENUE) or info.entry.account in cost_accounts):
            continue
        score, reasons, cited = 0.0, [], []
        for n in sorted(info.refs | ({info.doc_number} if info.doc_number else set())):
            if n in refs:
                display, doc_id = refs[n]
                score += W_REFERENCE
                reasons.append(f"the memo cites {display}")
                if doc_id:
                    cited.append(doc_id)
                break
        party: frozenset[str] = frozenset()
        for name, toks in names:
            if names_match(info.cp_tokens, toks) or name_in_text(toks, info.memo_tokens):
                score += W_COUNTERPARTY
                reasons.append(f"the payer is {name}")
                party = toks | info.cp_tokens
                break
        hits = keyword_hits(keywords, info.memo_norm, info.memo_tokens, party)
        if hits:
            score += W_KEYWORD + min(W_KEYWORD_EXTRA * (len(hits) - 1), W_KEYWORD_EXTRA_CAP)
            reasons.append("the memo mentions " + ", ".join(f"'{h}'" for h in hits))
        if score >= RECOVERY_THRESHOLD:
            out.append((eid, score, reasons, cited))
    return out


def offsetting_recovery(t: AdjustmentTrace, ctx: ChallengeContext) -> None:
    """Net an unadjusted credit (insurance proceeds, refunds) that relates to the same event."""
    idx = t.index
    for eid, score, reasons, docs in ctx.recoveries.get(t.adj.adj_id, []):
        info = idx.by_id[eid]
        labels_in = idx.labels_of(info.month)
        offsets = [Effect(lbl, info.amount, FlagCode.OFFSETTING_RECOVERY, eid) for lbl in labels_in]
        t.effects.extend(offsets)
        t.add_context_link(eid, score, "Offsetting recovery: " + "; ".join(reasons))
        quotes: list[EvidenceQuote] = []
        # The claim / settlement letter behind the recovery: any document stating the reference the memo cites.
        for n in sorted(info.refs):
            for d in idx.docs_by_ref.get(n, []) + idx.docs_by_text_ref.get(n, []):
                if d not in docs:
                    docs.append(d)
        docs = sorted(docs)
        claimed_set = set(t.claimed_ids())
        for d in docs:
            stated = [a.quote for a in idx.facts[d].amounts if _amount_is(a.amount, info.amount, idx.tolerance)]
            quotes += stated
            dl = t.doc_links.get(d)
            # A cost invoice that cites the claim number ties the credit to the event (it stays in the
            # flag's documents) but is the invoice for its own entry, not a document about the recovery.
            tied_to_claim = dl is not None and any(
                b in ENTRY_ABOUT_BASES for e, b in dl.entry_basis.items() if e in claimed_set
            )
            if stated or not tied_to_claim:
                t.associate(d, eid, "recovery", 0.0, "")
                t.doc_links[d].relation = "recovery"
        e = info.entry
        who = f" from {e.counterparty}" if e.counterparty else ""
        impact = {lbl: info.amount for lbl in labels_in}
        flag = _flag(
            t,
            FlagCode.OFFSETTING_RECOVERY,
            Severity.WARNING,
            f"{money(abs(info.amount))} received{who} in {month_label(info.month)} ({e.account} {e.account_name}) "
            f"relates to the same event ({reasons[0]}); management did not adjust it, so it offsets the add-back "
            f"in the period received." + _effect(t, impact),
            entry_ids=[eid],
            doc_ids=docs,
            quotes=quotes,
            impact=impact,
        )
        for x in offsets:
            x.flag = flag
        t.add_fact(
            Fact(
                text=f"A recovery of {money(abs(info.amount))}{who} was booked in {month_label(info.month)} to "
                f"{e.account} {e.account_name}, inside EBITDA.",
                entry_ids=[eid],
                quotes=quotes[:1],
            )
        )


# How far back to look for the other side of a claimed relationship (the billings behind a bad debt).
COUNTERPARTY_LOOKBACK_MONTHS = 12


def counterparty_history(t: AdjustmentTrace) -> None:
    """Surface earlier opposite-sign activity with a claimed entry's party (the invoices behind a
    written-off receivable, a vendor's credits). Context only; a fact when it ties to the claim."""
    idx = t.index
    claimed = [e for e in t.in_play_ids() if idx.by_id[e].cp_tokens]
    by_party: dict[str, list[str]] = {}
    for e in claimed:
        by_party.setdefault(" ".join(sorted(idx.by_id[e].cp_tokens)), []).append(e)
    for ids in by_party.values():
        first = idx.by_id[ids[0]]
        total = sum((t.amount(e) for e in ids), ZERO)
        if total == 0:
            continue
        lo = add_months(min(idx.by_id[e].month for e in ids), -COUNTERPARTY_LOOKBACK_MONTHS)
        hi = max(idx.by_id[e].month for e in ids)
        own = set(t.claimed_ids())
        history = [
            info
            for info in idx.entries
            if info.entry_id not in own
            and lo <= info.month <= hi
            and (info.amount > 0) != (total > 0)
            and info.amount != 0
            and names_match(info.cp_tokens, first.cp_tokens)
        ]
        if not history:
            continue
        who = first.entry.counterparty
        for info in history:
            t.add_context_link(info.entry_id, 0.0, f"Earlier activity with {who} (opposite sign to the claim)")
        pick = find_subset([cents(abs(i.amount)) for i in history], cents(abs(total)), cents(idx.tolerance))
        if pick is not None:
            tied = [history[i].entry_id for i in pick]
            t.add_fact(
                Fact(
                    text=f"The {money(abs(total))} claimed for {who} ties to {len(tied)} earlier "
                    f"entr{'y' if len(tied) == 1 else 'ies'}: {t.describe_many(tied)}.",
                    entry_ids=tied + ids,
                )
            )


def period_mismatch(t: AdjustmentTrace) -> None:
    """A claim in a period with no (or too little) activity there, while the activity sits in another period."""
    idx = t.index
    if t.is_normalization:
        return
    tol = idx.tolerance
    for lbl in t.claimed_labels():
        claim = t.claim(lbl)
        s = 1 if claim > 0 else -1
        eff = t.effect(lbl)
        proposed = t.supporting_total(lbl) + eff
        months = idx.label_months[lbl]
        outside = [e for e in t.candidates if idx.by_id[e].month not in months]
        if abs(proposed - claim) <= tol:
            t.drop_flags(FlagCode.PARTIAL_GL_SUPPORT, lbl)
            continue
        if not t.claimed.get(lbl):
            if abs(eff - claim) <= tol or not outside:
                continue
            match = t.fits[lbl].elsewhere if lbl in t.fits and t.fits[lbl].elsewhere else outside
        else:
            # Measured on the fitted (pre-challenge) activity: removals are not a period problem.
            excess = claim - t.traced(lbl)
            if s * excess <= tol or not outside:
                continue
            pick = find_subset([s * cents(t.amount(e)) for e in outside], cents(abs(excess)), cents(tol))
            if pick is None:
                continue
            match = [outside[i] for i in pick]
        t.drop_flags(FlagCode.PARTIAL_GL_SUPPORT, lbl)
        where = sorted({x for e in match for x in idx.labels_of(idx.by_id[e].month)} - {lbl}, key=t.labels.index)
        booked = month_span(idx.by_id[e].month for e in match)
        total = sum((t.amount(e) for e in match), ZERO)
        fit = t.fits.get(lbl)
        if t.claimed.get(lbl):
            what = f"linked activity in the period is only {money(t.traced(lbl))}"
        elif fit is not None and fit.linked_total:
            what = f"the linked activity in the period ({money(fit.linked_total)}) does not tie to it"
        else:
            what = "no linked GL activity falls in the period"
        _flag(
            t,
            FlagCode.PERIOD_MISMATCH,
            Severity.WARNING,
            f"{lbl}: management claims {money(claim)} but {what}; the matching entries ({money(total)}) were booked "
            f"{booked}{', in ' + ', '.join(where) if where else ''}. Diligence carries only the {lbl} activity: "
            f"{money(proposed)}.",
            entry_ids=match,
            label=lbl,
            amount_impact=proposed - claim,
        )


def sign_error(t: AdjustmentTrace) -> None:
    for lbl in t.claimed_labels():
        claim, traced = t.claim(lbl), t.traced(lbl)
        if traced == 0 or (traced > 0) == (claim > 0):
            continue
        t.drop_flags(FlagCode.PARTIAL_GL_SUPPORT, lbl)
        kind = "add-back" if claim > 0 else "deduction"
        nature = "credits" if traced < 0 else "debits"
        _flag(
            t,
            FlagCode.SIGN_ERROR,
            Severity.WARNING,
            f"{lbl}: management's {kind} of {money(claim)} is made of GL entries that net to {money(traced)} "
            f"({nature}), so the sign of the adjustment conflicts with the GL.",
            entry_ids=t.claimed.get(lbl, []),
            label=lbl,
        )


def duplicate_entries(t: AdjustmentTrace) -> None:
    idx = t.index
    claimed = set(t.claimed_ids())
    seen: set[tuple[str, ...]] = set()
    for e in t.claimed_ids():
        group = idx.duplicate_groups.get(e)
        if not group or tuple(group) in seen:
            continue
        seen.add(tuple(group))
        inside = [x for x in group if x in claimed]
        rows = ", ".join(str(idx.by_id[x].entry.source_row) for x in group if x in idx.by_id)
        _flag(
            t,
            FlagCode.DUPLICATE_GL_ENTRY,
            Severity.WARNING,
            f"{t.describe(e)} may be posted {len(group)} times (GL rows {rows}: same account, amount and party); "
            f"{len(inside)} of the {len(group)} postings are in the claimed set.",
            entry_ids=group,
        )


def doc_gl_amount_mismatch(t: AdjustmentTrace) -> None:
    idx = t.index
    tol = idx.tolerance
    claimed = set(t.claimed_ids())
    for doc_id in sorted(t.doc_links):
        facts = idx.facts.get(doc_id)
        if facts is None or not facts.amounts:
            continue
        stated: list[tuple[Decimal, str, EvidenceQuote]] = []
        for a in facts.amounts:
            try:
                stated.append((abs(D(a.amount)), a.label, a.quote))
            except ValueError:
                continue
        for e, basis in sorted(t.doc_links[doc_id].entry_basis.items()):
            if basis != "number" or e not in claimed:
                continue
            amt = abs(t.amount(e))
            if any(abs(x - amt) <= tol for x, _, _ in stated):
                continue
            totals = [x for x in stated if _TOTAL_LABEL.search(x[1])]
            if not totals:
                continue
            x, label, quote = totals[0]
            _flag(
                t,
                FlagCode.DOC_GL_AMOUNT_MISMATCH,
                Severity.WARNING,
                f"{doc_id} states {label.replace('_', ' ')} of {money(x)}, but the GL records {money(t.amount(e))} "
                f"for {t.describe(e)} (difference {money(amt - x)}).",
                entry_ids=[e],
                doc_ids=[doc_id],
                quotes=[quote],
            )


def unsigned_or_draft(t: AdjustmentTrace) -> None:
    idx = t.index
    for doc_id in t.evidence_docs():
        facts = idx.facts.get(doc_id)
        if facts is None or not (facts.is_draft or facts.is_signed is False):
            continue
        if facts.doc_type.strip().lower() in _UNSIGNABLE_DOC_TYPES:
            continue
        state = "a DRAFT" if facts.is_draft else "unsigned"
        quote = _first_statement(facts, re.compile(r"draft|sign", re.IGNORECASE)) or _first_statement(facts)
        _flag(
            t,
            FlagCode.UNSIGNED_OR_DRAFT_SUPPORT,
            Severity.WARNING,
            f"{doc_id} ({facts.doc_type.replace('_', ' ')}) is {state}, so it cannot support the adjustment until "
            "it is executed.",
            doc_ids=[doc_id],
            quotes=[quote],
        )


def _executed(facts: DocFacts) -> bool:
    if facts.is_draft:
        return False
    return facts.is_signed is True or facts.doc_type.strip().lower() in BENCHMARK_DOC_TYPES


def _level_match(stated: Decimal, level: Decimal, tol: Decimal) -> Optional[Decimal]:
    """The annual level a stated amount supports (it may be stated monthly)."""
    band = tol * 12
    if abs(stated - level) <= band:
        return stated
    if abs(stated * 12 - level) <= band:
        return stated * 12
    return None


def normalization(t: AdjustmentTrace) -> None:
    """Normalization: actual GL cost less a normalized level that a signed document or benchmark sets."""
    idx = t.index
    if not t.is_normalization:
        return
    labels = t.claimed_labels()
    if not labels:
        return
    actual = {lbl: t.traced(lbl) for lbl in labels}
    candidates: list[Decimal] = []
    if t.intent.normalized_amount:
        try:
            candidates.append(abs(D(t.intent.normalized_amount)))
        except ValueError:
            pass
    if not candidates:
        for lbl in labels:
            if actual[lbl] != 0:
                level = q2((actual[lbl] - t.claim(lbl)) * 12 / len(idx.label_months[lbl]))
                if level > 0 and level not in candidates:
                    candidates.append(level)
    info = NormalizationInfo(actual=actual, level_candidates=candidates)
    for doc_id in sorted(t.doc_links):
        facts = idx.facts[doc_id]
        for a in facts.amounts:
            try:
                stated = abs(D(a.amount))
            except ValueError:
                continue
            for c in candidates:
                annual = _level_match(stated, c, idx.tolerance)
                if annual is None:
                    continue
                if _executed(facts) and info.supported_by is None:
                    info.level, info.supported_by = annual, doc_id
                    t.add_fact(
                        Fact(text=f"{doc_id} sets the normalized level at {money(annual)} a year.", quotes=[a.quote]),
                        key=f"doc:{doc_id}",
                    )
                elif not _executed(facts) and doc_id not in info.draft_docs:
                    info.draft_docs.append(doc_id)
    t.normalization = info
    for lbl in labels:
        if actual[lbl] == 0:
            _flag(
                t,
                FlagCode.PARTIAL_GL_SUPPORT,
                Severity.WARNING,
                f"{lbl}: no actual cost for the normalized item was found in the GL, so the normalization cannot be "
                "measured for this period.",
                label=lbl,
                amount_impact=-t.claim(lbl),
            )
        else:
            n = len(t.claimed.get(lbl, []))
            t.add_fact(
                Fact(
                    text=f"{lbl}: actual cost in the GL is {money(actual[lbl])} ({n} {_plural(n, 'entry', 'entries')}); "
                    f"management claims {money(t.claim(lbl))}.",
                    entry_ids=t.claimed.get(lbl, []),
                )
            )
    if info.supported_by is None:
        level_txt = money(candidates[0]) if candidates else "the normalized level"
        if info.draft_docs:
            detail = f"the only document stating it, {join_limited(info.draft_docs, 1)}, is not executed"
        else:
            detail = "no linked document states it"
        _flag(
            t,
            FlagCode.NORMALIZATION_BENCHMARK_MISSING,
            Severity.WARNING,
            f"The normalized level of {level_txt} a year is not supported: {detail}, and there is no market benchmark.",
            doc_ids=info.draft_docs,
        )
        t.add_judgment(
            f"Is {level_txt} a year a supportable market level? Management's claim implies it, but no executed "
            "agreement or benchmark sets it.",
            key="normalization:level",
        )


def pro_forma(t: AdjustmentTrace) -> None:
    idx = t.index
    if not t.is_pro_forma:
        return
    last = idx.data_end
    reasons: list[str] = []
    base = t.in_play_ids() or t.candidates
    continuing = [e for e in base if idx.by_id[e].month >= last]
    if continuing:
        reasons.append(f"the GL shows {_groups_text(t, continuing)} continuing through {month_label(last)}")
    executed = [
        d
        for d in sorted(t.doc_links)
        if _executed(idx.facts[d])
        and idx.facts[d].doc_type.strip().lower() in AGREEMENT_DOC_TYPES
        and (not idx.facts[d].doc_date or idx.facts[d].doc_date[:7] <= last)
    ]
    if not executed:
        reasons.append("no executed document shows the event has occurred")
    future = [m for m in _valid_months(t.intent.event_months) if m > last]
    if future:
        reasons.append(f"management dates it to {month_label(future[0])}, after the last GL month")
    if not reasons:
        return
    quotes = [q for d in sorted(t.doc_links) for q in idx.facts[d].key_statements[:1]][:3]
    _flag(
        t,
        FlagCode.PRO_FORMA_NOT_REALIZED,
        Severity.CRITICAL,
        f"The pro forma savings are not realized: {'; '.join(reasons)}.",
        entry_ids=continuing,
        doc_ids=[q.doc_id for q in quotes],
        quotes=quotes,
    )
    t.add_judgment(
        "Should savings that have not yet occurred be carried in diligence EBITDA, or only disclosed as a "
        "run-rate consideration?",
        key="pro_forma",
    )


def document_coverage(t: AdjustmentTrace) -> None:
    """NO_DOCUMENT_SUPPORT per period, measured on what diligence would carry (SPEC §5.4).

    The base is the supporting amount after every removal and period move: entries
    still supporting, plus out-of-period effects (which rest on a document by
    construction). A period that carries nothing cannot trigger it: documents are
    needed for what we carry, not for what we reject. Above 25% undocumented it is
    a WARNING that drives REQUEST_INFO; a smaller gap is an INFO note.
    """
    idx = t.index
    if t.is_normalization or t.is_pro_forma:
        return
    tol = idx.tolerance
    for lbl in t.claimed_labels():
        carried_ids = [e for e in t.supporting(lbl) if e not in t.moved]
        moved = sum((x.amount for x in t.effects if x.label == lbl and x.code == FlagCode.OUT_OF_PERIOD), ZERO)
        base = sum((t.amount(e) for e in carried_ids), ZERO) + moved
        undoc = [e for e in carried_ids if not t.support_docs(e)]
        amount = sum((t.amount(e) for e in undoc), ZERO)
        if abs(amount) <= tol or abs(base) <= tol:
            continue
        share = abs(amount) / abs(base)
        pct = int((min(share, Decimal(1)) * 100).to_integral_value())
        msg = (
            f"{lbl}: {money(abs(amount))} of the {money(abs(base))} carried ({pct}%) has no supporting document "
            f"({_groups_text(t, undoc)})."
        )
        if share > UNDOCUMENTED_SHARE_LIMIT:
            severity = Severity.WARNING
            msg += " That is above the 25% limit, so documents are needed before diligence can carry it."
        else:
            severity = Severity.INFO
        _flag(t, FlagCode.NO_DOCUMENT_SUPPORT, severity, msg, entry_ids=undoc, label=lbl)
