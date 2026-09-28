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
    DW_ENTRY_AMOUNT,
    DW_ENTRY_NUMBER,
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
    is_repeated_bill,
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
# A retainer or fee tied to one transaction or one search ends with it (SPEC §5.4). Being creditable
# says so only when the credit is against the transaction's own fee; a retainer creditable against
# hourly fees is an ordinary standing retainer.
_ONE_OFF_TERM = re.compile(
    r"one[- ]time|creditable against (?:the |any )?(?:success|transaction|completion|closing|placement)\b|success fee"
    r"|upon (?:closing|completion|placement)|(?:payable |due )?(?:up)?on signing|"
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
    FlagCode.DUPLICATE_GL_ENTRY: "as a second posting of the same bill",
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
    if info is None or t.about_other_matter(doc_id, t.group_of.get(entry_id, "")):
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
    duplicate_entries(t)
    contradictions(t, ctx)
    entry_qualification(t, ctx)
    continuing_obligation(t)
    recurring_pattern(t)
    out_of_period(t)
    offsetting_recovery(t, ctx)
    counterparty_history(t)
    period_mismatch(t)
    sign_error(t)
    doc_gl_amount_mismatch(t)
    unsigned_or_draft(t)
    normalization(t)
    pro_forma(t)
    excess_carry(t)
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
    # Entries the documents themselves price as a one-time component: recurrence evidence about the
    # rest of the arrangement does not reach them (see _one_off_component).
    one_off = _one_off_component(t) if t.asserts_nonrecurring else {}
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
        # A document about another engagement of the same party (the letter for one matter against another
        # matter's bills) says nothing about this claim's entries.
        elsewhere = {e for e in proposed if t.about_other_matter(doc_id, t.group_of.get(e, ""))}
        if proposed and proposed <= elsewhere:
            t.add_fact(
                Fact(text=f"{doc_id} concerns a separate engagement with the same party; it does not bear on "
                          f"{t.items_text(proposed, 1)}.", entry_ids=sorted(proposed)),
                key=f"doc:{doc_id}",
            )
            continue
        scope = [e for e in claimed if e in proposed and e not in elsewhere and _doc_relates_to_entry(t, doc_id, e)]
        if not scope and not proposed:
            groups = [g for g in t.groups_for_doc(doc_id) if g in claimed_groups]
            scope = [e for e in claimed if t.group_of.get(e) in groups]
            if not scope and _about_entries_out_of_play(t, doc_id, claimed_set):
                # The document is specifically about claimed entries already taken out on structural grounds
                # (a debt-cost schedule for the part of the claim that sits below EBITDA): it says nothing
                # about the rest of the claim.
                continue
            if not scope and len(claimed_groups) == 1:
                # One kind of activity is claimed, so a document contradicting the claim covers all of it.
                scope = list(claimed)
        spared = [e for e in scope if e in one_off]
        scope = [e for e in scope if e not in one_off]
        if spared:
            t.add_fact(
                Fact(text=f"{one_off[spared[0]]} prices {t.items_text(spared, 1)} as a one-time component, separate "
                          "from the recurring charges; the recurrence evidence does not apply to it.",
                     entry_ids=spared),
                key=f"oneoff:{one_off[spared[0]]}",
            )
            if not scope:
                continue
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


# Words with which a document prices a component as a single, non-repeating charge. How a fee is
# credited ("creditable against the success fee") says nothing about whether it recurs: monthly
# retainers are routinely creditable, so that phrase is not a cue.
_ONE_OFF_PRICE = re.compile(r"one[- ]time|non-?recurring|lump[- ]sum|single payment", re.IGNORECASE)
# A figure is bound to the cue only inside the same clause and a few words away: "one-time
# implementation fee: $64,000" or "a $10,000 one-time setup fee", never "... one-time; support is $1,200".
_CUE_TO_FIGURE = 45
_FIGURE_TO_CUE = 25
_CLAUSE_BREAK = re.compile(r"[;,]|\.(?:\s|$)|\bthen\b|\bthereafter\b|\bplus\b|\bwhile\b|\bwhereas\b", re.IGNORECASE)
# The installments of a one-time fee are one-time too: "invoiced in two milestones of $32,000 each".
_INSTALLMENT_CUE = re.compile(r"install?ments?|milestones?|tranches?|\beach\b", re.IGNORECASE)
_RECURRING_LABELS = frozenset({"monthly_fee", "retainer", "recurring_fee", "monthly_retainer", "rate"})


_PERIOD_BEFORE = re.compile(
    r"(?<!non-)(?<!non)\b(?:monthly|quarterly|annual(?:ly)?|per\s+month|each\s+month|every\s+month)\b[^$\d.;]{0,20}$",
    re.IGNORECASE,
)
_SENTENCE_BREAK = re.compile(r";|\.(?:\s|$)")


def _one_off_amounts(text: str) -> set[Decimal]:
    """Amounts a text itself prices as one-time: the figure bound to a one-time cue, and its installments.

    Sentence by sentence: a figure is bound when it sits in the cue's clause, a few words away, and is
    not written as a periodic amount ("$2,500 per month", "monthly fee $2,000"); a figure in the same
    sentence that splits a bound fee into 2-12 equal parts, beside an installment word, is one of its
    installments.
    """
    text = text or ""
    bound: set[Decimal] = set()
    start = 0
    for brk in list(_SENTENCE_BREAK.finditer(text)) + [None]:
        stop = brk.start() if brk is not None else len(text)
        sentence = text[start:stop]
        start = brk.end() if brk is not None else len(text)
        figures = []
        for m in _MONEY.finditer(sentence):
            if _PERIOD_AFTER.match(sentence, m.end()) or _PERIOD_BEFORE.search(sentence[: m.start()]):
                continue  # a periodic amount is never the one-time component
            try:
                figures.append((m, D(m.group(1))))
            except ValueError:
                continue
        here: set[Decimal] = set()
        for cue in _ONE_OFF_PRICE.finditer(sentence):
            for m, value in figures:
                if cue.end() <= m.start() <= cue.end() + _CUE_TO_FIGURE:
                    between = sentence[cue.end() : m.start()]
                elif cue.start() - _FIGURE_TO_CUE <= m.end() <= cue.start():
                    between = sentence[m.end() : cue.start()]  # "a $10,000 one-time setup fee"
                else:
                    continue
                if not _CLAUSE_BREAK.search(between):
                    here.add(value)
        if here and _INSTALLMENT_CUE.search(sentence):
            for _, value in figures:
                if value > 0 and any(b > value and b % value == 0 and 2 <= b / value <= 12 for b in here):
                    here.add(value)
        bound |= here
    bound.discard(ZERO)
    return bound


def _is_number(value: str) -> bool:
    try:
        D(value)
        return True
    except (ValueError, ArithmeticError):
        return False


def _periodic_amounts(text: str) -> set[Decimal]:
    """Figures a text writes as periodic amounts ("$2,500 per month", "monthly fee $2,000")."""
    text = text or ""
    out: set[Decimal] = set()
    for m in _MONEY.finditer(text):
        if _PERIOD_AFTER.match(text, m.end()) or _PERIOD_BEFORE.search(text[max(0, m.start() - 40) : m.start()]):
            try:
                out.add(D(m.group(1)))
            except ValueError:
                continue
    return out


def _one_off_component(t: AdjustmentTrace) -> dict[str, str]:
    """Claimed entries billed at an amount a related document itself calls one-time -> that document.

    A contract often prices a one-time element (an implementation fee, a transaction retainer)
    separately from a recurring one (a subscription). The recurring terms are evidence against
    adding back the recurring charges, not against the one-time fee the same contract sets
    apart: a practitioner removes only the subscription entries. Only verified quotes count,
    only the figure the one-time cue itself prices (and that fee's installments) is one-time,
    and the document must be the entry's party's (or be tied to the entry specifically).
    """
    idx = t.index
    tol = idx.tolerance
    out: dict[str, str] = {}
    claimed = t.claimed_ids()
    for doc_id in sorted(t.doc_links):
        facts = idx.facts.get(doc_id)
        if facts is None:
            continue
        amounts: set[Decimal] = set()
        for a in facts.amounts:
            if a.label.strip().lower() in _RECURRING_LABELS:
                continue
            try:
                stated = abs(D(a.amount))
            except ValueError:
                continue
            if any(abs(stated - x) <= tol for x in _one_off_amounts(a.quote.quote)):
                amounts.add(stated)
        for q in list(facts.key_statements) + [x.quote for x in facts.terms]:
            amounts.update(_one_off_amounts(q.quote))
        # A figure the same document also states as a periodic charge is not a one-time component.
        periodic = {abs(D(a.amount)) for a in facts.amounts if a.label.strip().lower() in _RECURRING_LABELS
                    and _is_number(a.amount)}
        for q in [a.quote for a in facts.amounts] + list(facts.key_statements) + [x.quote for x in facts.terms]:
            periodic |= _periodic_amounts(q.quote)
        amounts = {x for x in amounts if all(abs(x - p) > tol for p in periodic)}
        amounts.discard(ZERO)
        if not amounts:
            continue
        dcp = idx.doc_cp.get(doc_id, frozenset())
        basis = t.doc_links[doc_id].entry_basis
        for e in claimed:
            info = idx.by_id[e]
            if not (names_match(dcp, info.cp_tokens) or basis.get(e) in ENTRY_SPECIFIC_BASES):
                continue
            if any(abs(abs(info.amount) - a) <= tol for a in amounts):
                out.setdefault(e, doc_id)
    return out


def _about_entries_out_of_play(t: AdjustmentTrace, doc_id: str, in_play: set[str]) -> bool:
    """The document is specifically about claimed entries no longer in play (removed as below
    EBITDA, claimed elsewhere, or a repeated posting) and about no claimed entry still in play, so it
    cannot speak for the rest of the claim. A document about both still speaks to the entries in play."""
    dl = t.doc_links.get(doc_id)
    if dl is None:
        return False
    claimed = set(t.claimed_ids())
    about = {e for e, b in dl.entry_basis.items() if b in ENTRY_ABOUT_BASES and e in claimed}
    return bool(about) and not (about & in_play)


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
    # The one-time component a contract prices separately is not the continuing obligation.
    one_off = _one_off_component(t)
    claimed = [e for e in claimed if e not in one_off]
    if not claimed:
        return
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
            and (
                t.group_of.get(e) in doc_groups
                or (names_match(idx.by_id[e].cp_tokens, doc_cp) and not t.about_other_matter(doc_id, t.group_of.get(e, "")))
            )
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
        # The other bills of one fixed-fee engagement (an executed letter of the same party fixes one fee
        # that the claimed and unclaimed bills make up together) are the same event, billed in phases,
        # not evidence that it recurs.
        same_party = [info for info, _ in comparables if profile.cp and names_match(info.cp_tokens, profile.cp)]
        party_claimed = sum((t.amount(e) for e in claimed if names_match(idx.by_id[e].cp_tokens, profile.cp)), ZERO)
        if same_party and _fixed_fee_letter(
            t, profile.cp, abs(party_claimed + sum((x.amount for x in same_party), ZERO))
        ) is not None:
            engagement = {x.entry_id for x in same_party}
            comparables = [(info, why) for info, why in comparables if info.entry_id not in engagement]
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


# The longest service period an ordinary recurring bill covers: a month or a quarter. A bill for four
# or more months at once is a catch-up whatever its lag.
ARREARS_MAX_SERVICE_MONTHS = 3
# A bill that describes itself as correcting or catching up earlier charges is never ordinary billing. Routine
# line items ("fuel surcharge adjustment", "rate adjustment") are not: they appear on every monthly bill.
_CATCH_UP_BILL = re.compile(
    r"\btrue[- ]?up\b|\bcatch[- ]?up\b|\bretroactive(?:ly)?\b|\bback[- ]?bill(?:ed|ing|s)?\b"
    r"|\b(?:under|over)[- ]?bill(?:ed|ing)\b|\bone[- ]time (?:reconciliation|adjustment|correction|charge)"
    r"|\b(?:billing|invoice) (?:reconciliation|correction)s?\b|\bbill(?:ing)? adjustment\b"
    r"|\bprior[- ]period (?:adjustment|charges?|billing|correction)s?\b",
    re.IGNORECASE,
)


def _months_between(earlier: str, later: str) -> int:
    (y1, m1), (y2, m2) = (int(x) for x in earlier.split("-")), (int(x) for x in later.split("-"))
    return (y2 - y1) * 12 + (m2 - m1)


def _ordinary_arrears(t: AdjustmentTrace, entry_id: str, doc_id: str, s_months: list[str]) -> bool:
    """The bill is one cycle of an ordinary billing series, billed in arrears (SPEC §5.4 OUT_OF_PERIOD).

    A recurring bill for the last month or quarter recurs every cycle, so each period carries a full
    year of it and nothing is out of period. What decides is the billing cadence, not the lag alone:
    the bill covers one ordinary cycle (at most a quarter), is booked within one cycle after it ends,
    does not call itself a correction or catch-up, and belongs to a series of the same party's bills
    (a bill of the same party and series whose service period abuts this one, or the party's previous
    booking in the account at least one cycle earlier, so the bill covers only the time since the last).
    """
    idx = t.index
    info = idx.by_id[entry_id]
    n = len(s_months)
    if n > ARREARS_MAX_SERVICE_MONTHS or not s_months[-1] < info.month:
        return False
    if _months_between(s_months[-1], info.month) > n:
        return False
    doc = idx.docs.get(doc_id)
    if doc is not None and _CATCH_UP_BILL.search(doc.full_text):
        return False
    party = idx.doc_cp.get(doc_id) or info.cp_tokens
    ref = t.group_ref.get(t.group_of.get(entry_id, ""), "")
    before, after = add_months(s_months[0], -1), add_months(s_months[-1], 1)
    for other in idx.docs:
        if other == doc_id or not party or not names_match(idx.doc_cp.get(other, frozenset()), party):
            continue
        if ref and ref not in idx.doc_refs.get(other, frozenset()):
            continue  # another series of the same party (a retainer beside a matter's bills)
        f = idx.facts.get(other)
        months = month_range_safe(f.service_period_start, f.service_period_end) if f else []
        if months and len(months) <= ARREARS_MAX_SERVICE_MONTHS and (months[-1] == before or months[0] == after):
            return True
    if not info.cp_tokens:
        return False
    earlier = [
        x.month
        for x in idx.entries
        if x.entry_id != entry_id
        and x.entry.account == info.entry.account
        and (x.amount > 0) == (info.amount > 0)
        and x.month <= info.month
        and x.pos < info.pos
        and names_match(x.cp_tokens, info.cp_tokens)
        and (not info.memo_ref_norm or x.memo_ref_norm == info.memo_ref_norm)
    ]
    return bool(earlier) and _months_between(max(earlier), info.month) >= n


def out_of_period(t: AdjustmentTrace) -> None:
    """Move entries whose documented service period sits in another analysis period.

    The entry leaves the supporting set and is replaced entirely by its effect: + the
    amount in each period containing the booking month, - the amount pro rata by the
    service months each period contains. Service months before ``data_start`` are
    outside the analysis, so no negative side is carried for them (SPEC §5.4).
    """
    idx = t.index
    declared = t.adj.category == AdjustmentCategory.OUT_OF_PERIOD
    for e in t.supporting_ids():
        if e in t.moved:
            continue
        info = idx.by_id[e]
        for doc_id in t.entry_docs_by_basis(e, ENTRY_SPECIFIC_BASES):
            facts = idx.facts[doc_id]
            s_months = month_range_safe(facts.service_period_start, facts.service_period_end)
            if not s_months or info.month in s_months:
                continue
            # Ordinary billing in arrears (one cycle of a recurring series, billed after it ends) recurs
            # every cycle, so each period carries a full year of it and nothing is out of period. A
            # catch-up (a true-up, a correction, a late or multi-cycle bill) is. When management itself
            # presents the item as out-of-period, the move is measured whatever the cadence.
            if not declared and _ordinary_arrears(t, e, doc_id, s_months):
                continue
            book_labels = set(idx.labels_of(info.month))
            svc_labels = {lbl for m in s_months for lbl in idx.labels_of(m)}
            # Service months outside every analysis period (before data_start, say) are a different
            # fiscal period even when the rest of the service falls in the booking period's labels.
            outside = [m for m in s_months if not idx.labels_of(m)]

            def splits(lbl: str) -> bool:
                """The label holds the booking but not every service month, or service months but not the booking."""
                months = idx.label_months[lbl]
                n_svc = sum(1 for m in s_months if m in months)
                return (info.month in months and n_svc < len(s_months)) or (info.month not in months and n_svc > 0)

            # Tested on every period label: overlapping periods (FY and TTM) can each cut the service
            # differently, so a bill whose service sits wholly inside the fiscal year of booking can still
            # belong partly outside a TTM that starts mid-service.
            if not any(splits(lbl) for lbl in t.labels) and not outside:
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
            if svc_labels == book_labels:
                # Same labels, cut differently: say which period holds only part of the service.
                partial = [lbl for lbl in sorted(book_labels, key=order) if splits(lbl)]
                where = ", ".join(
                    f"{lbl} holds {sum(1 for m in s_months if m in idx.label_months[lbl])} of the "
                    f"{len(s_months)} service months" for lbl in partial
                )
                msg = (
                    f"{t.entry_ref(e)} ({money(info.amount)}) is for services in {month_span(s_months)} per {doc_id}; "
                    f"{where}, so each period carries it pro rata."
                )
            else:
                msg = (
                    f"{t.entry_ref(e)} ({money(info.amount)}) covers services in {month_span(s_months)} per {doc_id}, "
                    f"so the cost belongs to {belongs} and moves out of {booked} pro rata by service month."
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
    """A claimed entry that reconciliation found posted more than once (SPEC §5.4, §5.7).

    When the postings share one document number and the claim includes more than one of them,
    the claim keeps the first posting and loses the others: a bill entered twice is a bookkeeping
    error, reversed once in its own diligence item, and must not also be added back here as a
    non-recurring cost (counting it twice). Other duplicate groups only raise the question.
    """
    idx = t.index
    claimed = set(t.claimed_ids())
    seen: set[tuple[str, ...]] = set()
    for e in t.claimed_ids():
        group = idx.duplicate_groups.get(e)
        if not group or tuple(group) in seen:
            continue
        seen.add(tuple(group))
        ordered = idx.sort_ids(group)
        inside = [x for x in ordered if x in claimed]
        rows = ", ".join(str(idx.by_id[x].entry.source_row) for x in ordered if x in idx.by_id)
        n = len(ordered)
        extras = inside[1:] if len(inside) > 1 and is_repeated_bill(idx, ordered) else []
        if not extras:
            _flag(
                t,
                FlagCode.DUPLICATE_GL_ENTRY,
                Severity.WARNING,
                f"{t.describe(e)} may be posted {n} times (GL rows {rows}: same account, amount and party); "
                f"{len(inside)} of the {n} postings are in the claimed set.",
                entry_ids=ordered,
            )
            continue
        newly = t.remove(extras, FlagCode.DUPLICATE_GL_ENTRY, "a second posting of the same bill; a diligence item reverses it")
        impact = t.impact_of_removing(newly)
        extra_rows = ", ".join(str(idx.by_id[x].entry.source_row) for x in extras)
        flag = _flag(
            t,
            FlagCode.DUPLICATE_GL_ENTRY,
            Severity.WARNING,
            f"{t.entry_ref(inside[0])} is posted {n} times under one document number (GL rows {rows}) and the claim "
            f"includes {len(inside)} of the postings. The claim keeps the first; GL row {extra_rows} is reversed once "
            f"in a diligence item instead of being added back here." + _effect(t, impact),
            entry_ids=ordered,
            impact=impact,
        )
        t.attach(newly, flag)


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
    info.mgmt_level = candidates[0] if candidates else None
    if info.supported_by is None:
        _benchmark_normalization(t, info)
    cost_free = t.cost_free_labels()
    for lbl in labels:
        if actual[lbl] == 0 and lbl in cost_free:
            t.add_fact(
                Fact(
                    text=f"{lbl}: the GL carries no cost for the arrangement, and management's claim is the whole "
                    f"normalized level ({money(t.claim(lbl))}), so the arrangement costs nothing today."
                )
            )
        elif actual[lbl] == 0:
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


_PER_MONTH = re.compile(r"month", re.IGNORECASE)
_PER_QUARTER = re.compile(r"quarter", re.IGNORECASE)
# What a figure measures is read from the words around it, not from its size. A per-unit rate ("$9.00 per
# square foot", "$185 an hour") is not a level for the arrangement, and neither is a company-wide figure
# ("revenue of about $40 million", "companies with revenue of $20 to $60 million").
_SCALE_AFTER = r"\s*(?:million|billion|thousand|mm|bn|k|m)?\b"
_PER_UNIT_AFTER = re.compile(
    _SCALE_AFTER + r"\s*(?:/|per\b|an?\b|each\b)\s*(?:rentable\s+|usable\s+|gross\s+)?"
    r"(?:square\s+f(?:oo|ee)t|sq\.?\s*f(?:ee)?t\.?|s\.?f\.?|hour|hr|day|unit|case|mile|visit|test|seat|user|employee"
    r"|fte|head|bed|patient|pallet|ton|lb|pound|gallon|door|member|participant|shift|load|stop|procedure|rvu)\b"
    r"|\s*(?:psf|/sf|/hr)\b",
    re.IGNORECASE,
)
_COMPANY_FIGURE = re.compile(
    r"\b(?:revenues?|sales|turnover|ebitda|net income|profits?|enterprise value|valuation|purchase price"
    r"|market cap(?:itali[sz]ation)?|total assets|total payroll|headcount)\b[^.;]{0,30}$",
    re.IGNORECASE,
)
_RANGE_TO_SCALE = re.compile(r"\s*(?:to|-|–)\s*\$?\s*[\d.,]+\s*(?:million|billion|mm|bn)\b", re.IGNORECASE)
# A document that is not a benchmark sets a market level only in a sentence that speaks of market.
_MARKET_CUE = re.compile(
    r"\bmarket\b|\bbenchmark|\bcomparables?\b|\bcomparable (?:leases?|rents?|companies|positions)|\bmedian\b"
    r"|\bpercentile\b|\bfair market value\b|\bFMV\b|\bpeer group\b",
    re.IGNORECASE,
)
_AREA = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{3,7})\s*(?:rentable\s+|usable\s+|gross\s+)?"
                   r"(?:square\s+f(?:oo|ee)t|sq\.?\s*f(?:ee)?t\.?|SF)\b", re.IGNORECASE)
_PER_SF_RATE = re.compile(
    r"\$\s?(\d+(?:\.\d{1,2})?)\s*(?:/|per\b|a\b)\s*(?:rentable\s+|usable\s+)?(?:square\s+f(?:oo|ee)t|sq\.?\s*f(?:ee)?t\.?|s\.?f\.?)"
    r"(?P<tail>[^.;]{0,30})",
    re.IGNORECASE,
)


def _annualized(stated: Decimal, label: str, quote: str) -> Decimal:
    """The annual level a stated amount represents: monthly x 12, quarterly x 4, else as stated."""
    if label.strip().lower() in ("monthly_fee", "monthly_retainer"):
        return stated * 12
    for m in _MONEY.finditer(quote):
        try:
            value = D(m.group(1))
        except ValueError:
            continue
        if value != stated:
            continue
        after = _PERIOD_AFTER.match(quote, m.end())
        if after and _PER_MONTH.search(after.group()):
            return stated * 12
        if after and _PER_QUARTER.search(after.group()):
            return stated * 4
        break
    return stated


def _figure_context(t: AdjustmentTrace, quote: EvidenceQuote, stated: Decimal) -> Optional[tuple[str, str]]:
    """(the sentence up to the figure, the words after it) for the figure ``stated`` in a verified quote,
    read from the page so that a quote cut at a line break still shows its sentence."""
    doc = t.index.docs.get(quote.doc_id)
    page_text = next((p.text for p in doc.pages if p.page == quote.page), "") if doc is not None else ""
    at = page_text.find(quote.quote)
    text, base = (page_text, at) if at >= 0 else (quote.quote, 0)
    scales = {"million": Decimal(1_000_000), "billion": Decimal(1_000_000_000), "thousand": Decimal(1000)}
    for m in _MONEY.finditer(text, base, base + len(quote.quote)):
        try:
            value = D(m.group(1))
        except ValueError:
            continue
        word = re.match(r"\s*(million|billion|thousand)\b", text[m.end() :], re.IGNORECASE)
        if value != stated and not (word and value * scales[word.group(1).lower()] == stated):
            continue
        start = max(text.rfind(". ", 0, m.start()) + 2, text.rfind(";", 0, m.start()) + 1, 0)
        return " ".join(text[start : m.start()].split()), text[m.end() : m.end() + 60]
    return None


def _per_unit_or_company(before: str, after: str) -> bool:
    return bool(_PER_UNIT_AFTER.match(after) or _RANGE_TO_SCALE.match(after) or _COMPANY_FIGURE.search(before))


def _rate_times_area(t: AdjustmentTrace, doc_id: str) -> list[tuple[Decimal, EvidenceQuote]]:
    """Annual levels a document states as a rate per square foot and one area, both verbatim."""
    doc = t.index.docs.get(doc_id)
    if doc is None:
        return []
    areas = {D(m.group(1)) for m in _AREA.finditer(doc.full_text)}
    if len(areas) != 1:
        return []
    area = next(iter(areas))
    out: list[tuple[Decimal, EvidenceQuote]] = []
    for page in doc.pages:
        for line in page.text.splitlines():
            for m in _PER_SF_RATE.finditer(line):
                rate = D(m.group(1))
                monthly = re.search(r"month|/mo\b", m.group("tail"), re.IGNORECASE)
                out.append((q2(rate * area * (12 if monthly else 1)), EvidenceQuote(doc_id=doc_id, page=page.page,
                                                                                   quote=line.strip())))
    return out


def _benchmark_normalization(t: AdjustmentTrace, info: NormalizationInfo) -> None:
    """Take the normalized level from an independent market benchmark when nothing supports management's.

    A normalization restates one arrangement at market. When no executed document states the level
    management used, a benchmark for the same arrangement (a broker's opinion of market rent, an
    independent pay study), prepared by someone who is not party to it, is the evidence of market. It
    must state one market level for it (restated monthly and yearly counts once; a rate per square foot
    times the one area the document states counts as that level); the current contract cost it quotes
    for reference is not the market level, and what a figure measures is read from its words, not its
    size: per-unit rates and company-wide figures (revenue, EBITDA) are not levels. A document that is not
    a benchmark sets a level only in a sentence that speaks of market (market, benchmark, comparable,
    median, percentile, fair market value). Diligence then normalizes to that level, whatever management
    used: when market is above what is paid, the normalization reduces EBITDA. The benchmark contradicts
    management's level, so a CONTRADICTORY_EVIDENCE flag carries the change in level. An arrangement that
    costs nothing (rent-free premises) has no actual cost to compare: the level is the whole normalization.
    """
    idx = t.index
    tol12 = idx.tolerance * 12
    annual_actual = [
        abs(v) * 12 / len(idx.label_months[lbl]) for lbl, v in info.actual.items() if v != 0 and idx.label_months[lbl]
    ]
    ref = sorted(annual_actual)[len(annual_actual) // 2] if annual_actual else ZERO
    parties = [idx.by_id[e].cp_tokens for e in t.claimed_ids() if idx.by_id[e].cp_tokens]
    parties += [name_tokens(n) for n in t.intent.counterparties if name_tokens(n)]
    found: list[tuple[Decimal, str, EvidenceQuote]] = []
    for doc_id in sorted(t.doc_links):
        facts = idx.facts.get(doc_id)
        if facts is None or not t.doc_links[doc_id].prelinked or not _executed(facts):
            continue
        dtype = facts.doc_type.strip().lower()
        if dtype in _UNSIGNABLE_DOC_TYPES:
            continue
        dcp = idx.doc_cp.get(doc_id, frozenset())
        if dcp and (any(names_match(dcp, p) for p in parties) or names_match(dcp, idx.company_tokens)):
            continue  # a party to the arrangement (or the company itself) is not an independent view of market
        benchmark = dtype in BENCHMARK_DOC_TYPES
        stated_levels: list[tuple[Decimal, EvidenceQuote]] = []
        for a in facts.amounts:
            try:
                stated = abs(D(a.amount))
            except ValueError:
                continue
            if stated == 0 or a.label.strip().lower() == "rate":
                continue
            context = _figure_context(t, a.quote, stated)
            before, after = context if context is not None else ("", "")
            if _per_unit_or_company(before, after):
                continue  # a rate per unit, or a figure for the whole company
            if not benchmark and not _MARKET_CUE.search(f"{before} {a.quote.quote}"):
                continue
            stated_levels.append((_annualized(stated, a.label, a.quote.quote), a.quote))
        stated_levels += [(v, q) for v, q in _rate_times_area(t, doc_id) if benchmark or _MARKET_CUE.search(q.quote)]
        for annual, quote in stated_levels:
            if any(abs(annual - x) <= tol12 for x in annual_actual):
                continue  # the current cost, quoted for reference
            found.append((annual, doc_id, quote))
    levels: list[Decimal] = []
    for annual, _, _ in found:
        if all(abs(annual - x) > tol12 for x in levels):
            levels.append(annual)
    if len(levels) != 1:
        if len(levels) > 1:
            t.add_judgment(
                f"Which market level applies? {join_limited(sorted({d for _, d, _ in found}), 1)} states several "
                f"({join_limited([money(x) for x in sorted(levels)], 3)} a year), so no level was taken.",
                key="normalization:level",
            )
        return
    level = q2(levels[0])
    doc_id = found[0][1]
    quotes = [q for _, d, q in found if d == doc_id]
    info.level, info.supported_by, info.benchmark = level, doc_id, True
    actual_txt = money(ref)
    mgmt = info.mgmt_level
    direction = "above" if level > ref else "below"
    impact = (
        {lbl: q2((mgmt - level) * len(idx.label_months[lbl]) / 12) for lbl in t.claimed_labels()}
        if mgmt is not None
        else None
    )
    mgmt_txt = f"management's level of {money(mgmt)} a year is not supported" if mgmt is not None else (
        "management's level is not supported")
    flips = level > ref and all(t.claim(lbl) > 0 for lbl in t.claimed_labels())
    paid = (
        f"{direction} the {actual_txt} a year actually paid" if ref else "for an arrangement that costs nothing today"
    )
    msg = (
        f"{doc_id} puts market at {money(level)} a year, {paid}; "
        f"{mgmt_txt}, so diligence normalizes to the benchmark"
        + (", which reduces EBITDA." if flips else ".")
        + _effect(t, impact)
    )
    info.level_flag = _flag(
        t, FlagCode.CONTRADICTORY_EVIDENCE, Severity.WARNING, msg, doc_ids=[doc_id], quotes=quotes, impact=impact,
    )
    t.add_fact(
        Fact(text=f"{doc_id} sets the market level at {money(level)} a year for the arrangement.", quotes=quotes[:2]),
        key=f"doc:{doc_id}",
    )
    t.add_judgment(
        f"Should the arrangement be normalized to the {money(level)} market level in {doc_id}, as proposed, or left "
        "unadjusted if the current terms continue unchanged after closing?",
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


def excess_carry(t: AdjustmentTrace) -> None:
    """SPEC §5.4 EXCESS_GL_ACTIVITY carry rule: diligence carries the rest of a fixed-fee engagement.

    Management's claim is normally the ceiling: unclaimed activity is context, and a buyer-side
    review does not volunteer add-backs. The exception is a claim that covers only part of one
    engagement whose whole cost is established: an executed engagement letter or order form with
    the same party fixes one fee equal to the claimed entries plus the unclaimed ones, management
    cites the unclaimed bill in its own support, and the bill falls in a period management claims.
    The cost is then the same non-recurring project, and leaving part of it in EBITDA would be
    inconsistent. Not for pro forma or normalization items, whose claim defines a run-rate.
    Carried only when every claimed entry of the engagement survived the challenges.
    """
    idx = t.index
    if t.is_pro_forma or t.is_normalization:
        return
    claimed_all = set(t.claimed_ids())

    def cited_bill(e: str) -> list[str]:
        return [d for d in sorted(t.doc_links) if t.doc_links[d].cited and e in idx.doc_entries.get(d, frozenset())]

    for lbl in t.claimed_labels():
        if lbl in t.capped:
            continue
        claim = t.claim(lbl)
        months = idx.label_months[lbl]
        mine = set(t.claimed.get(lbl, []))
        carried: list[str] = []
        # One (letter, fee, quote) per carried entry: each bill is tied to its own engagement's letter only.
        letters_used: list[tuple[str, Decimal, Optional[EvidenceQuote]]] = []
        for e in t.candidates:
            info = idx.by_id[e]
            if info.month not in months or e in mine or e in t.removals or (claim > 0) != (info.amount > 0):
                continue
            own = cited_bill(e)
            if not own or not info.cp_tokens:
                continue
            party = [x for x in claimed_all if names_match(idx.by_id[x].cp_tokens, info.cp_tokens)]
            if not party or any(x in t.removals for x in party) or not mine & set(party):
                continue
            unclaimed = [
                x for x in t.candidates
                if x not in claimed_all and names_match(idx.by_id[x].cp_tokens, info.cp_tokens) and cited_bill(x)
            ]
            total = sum((t.amount(x) for x in set(party) | set(unclaimed)), ZERO)
            letter = _fixed_fee_letter(t, info.cp_tokens, abs(total))
            if letter is None:
                continue
            carried.append(e)
            letters_used.append((letter[0], abs(total), letter[1]))
        if not carried:
            continue
        t.carried.setdefault(lbl, []).extend(idx.sort_ids(carried))
        for e, (letter_id, fee, _) in zip(carried, letters_used):
            for d in cited_bill(e):
                t.associate(d, e, "number", DW_ENTRY_NUMBER, "States the doc # of linked GL entries")
            t.associate(letter_id, e, "group", DW_ENTRY_AMOUNT, f"States the {money(fee)} fixed fee of the engagement")
        t.drop_flags(FlagCode.EXCESS_GL_ACTIVITY, lbl)
        in_label = [e for e in t.candidates if idx.by_id[e].month in months]
        if all(e in mine or e in carried for e in in_label) and lbl in t.fits:
            # Every linked entry of the period is now carried, so which subset made up the claim no longer matters.
            t.fits[lbl].ties = 1
            t.drop_judgment(f"fit:{lbl}")
        letter_id, fee, _ = letters_used[0]
        amount = sum((t.amount(e) for e in carried), ZERO)
        bills = join_limited([t.entry_ref(e) for e in idx.sort_ids(carried)], 1)
        own_docs = sorted({d for e in carried for d in cited_bill(e)})
        letters = list(dict.fromkeys(x[0] for x in letters_used))
        fixes = (
            f"{letter_id} fixes one fee of {money(fee)} for the engagement it completes"
            if len(letters) == 1
            else f"{join_limited(letters, 1)} each fix one fee for the engagement the bill completes"
        )
        _flag(
            t,
            FlagCode.EXCESS_GL_ACTIVITY,
            Severity.WARNING,
            f"{lbl}: {bills} ({money(amount)}) is not claimed, but {fixes}, and management cites the bill. "
            f"Carried: {money(amount)}.",
            entry_ids=carried,
            doc_ids=letters + own_docs,
            quotes=[q for _, _, q in letters_used if q is not None],
            label=lbl,
            amount_impact=amount,
        )
        for letter, letter_fee, letter_quote in {x[0]: x for x in letters_used}.values():
            mine_carried = [e for e, x in zip(carried, letters_used) if x[0] == letter]
            t.add_fact(
                Fact(
                    text=f"{letter} fixes one fee of {money(letter_fee)} for the engagement; the claim includes only "
                    "part of it.",
                    entry_ids=idx.sort_ids(mine_carried),
                    quotes=[letter_quote] if letter_quote is not None else [],
                ),
                key=f"doc:{letter}",
            )
        t.add_judgment(
            f"Should the unclaimed {bills} ({money(amount)}) be added back with the rest of the fixed fee, as "
            "proposed, or held at management's claim?",
            key=f"carry:{','.join(idx.sort_ids(carried))}",
        )


def _fixed_fee_letter(
    t: AdjustmentTrace, party: frozenset[str], total: Decimal
) -> Optional[tuple[str, Optional[EvidenceQuote]]]:
    """An executed engagement letter or order form of ``party``, related to the adjustment, that
    states ``total`` as one amount: (doc_id, the quote stating it)."""
    idx = t.index
    for doc_id in sorted(t.doc_links):
        facts = idx.facts.get(doc_id)
        if facts is None or facts.doc_type.strip().lower() not in AGREEMENT_DOC_TYPES:
            continue
        if facts.is_draft or facts.is_signed is False or not names_match(idx.doc_cp.get(doc_id, frozenset()), party):
            continue
        for a in facts.amounts:
            if _amount_is(a.amount, total, idx.tolerance):
                return doc_id, a.quote
    return None


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
