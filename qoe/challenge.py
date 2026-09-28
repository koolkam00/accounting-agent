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
    cents,
    find_subset,
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
# A month is "similar" when its amount is within +/-50% of the group's typical entry.
SIMILAR_LOW = Decimal("0.5")
SIMILAR_HIGH = Decimal("1.5")
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
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s+(?:equal\s+)?"
    r"(?:monthly\s+)?(?:installments?|instalments?|payments?)\b",
    re.IGNORECASE,
)
_MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:\.\d{2})?)")
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
_TERM_MONTHS = re.compile(r"\b(\d{1,3})[- ]month", re.IGNORECASE)
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
    """Raise a flag. A per-period impact touching one period sets period_label /
    amount_impact; touching several, it is spelled out in the message instead."""
    period_label = label
    impact_str = fmt(amount_impact) if amount_impact is not None else None
    if impact is not None:
        nonzero = {k: v for k, v in impact.items() if v != 0}
        if len(nonzero) == 1:
            period_label, v = next(iter(nonzero.items()))
            impact_str = fmt(v)
        elif nonzero:
            message += " Effect: " + "; ".join(f"{k} {money(v)}" for k, v in nonzero.items()) + "."
    picked: list[EvidenceQuote] = []
    for q in quotes:
        if q is not None and all((q.doc_id, q.page, q.quote) != (p.doc_id, p.page, p.quote) for p in picked):
            picked.append(q)
    flag = Flag(
        code=code,
        severity=severity,
        message=message,
        period_label=period_label,
        amount_impact=impact_str,
        entry_ids=t.index.sort_ids(entry_ids),
        doc_ids=sorted(set(doc_ids)),
        quotes=picked,
        related_adj_ids=sorted(set(related)),
    )
    t.add_flag(flag)
    return flag


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _sentence(text: str) -> str:
    text = (text or "").strip()
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


def _has_verified_content(facts: Optional[DocFacts]) -> bool:
    return bool(facts and (facts.key_statements or facts.amounts or facts.terms))


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
        if ws != ls:
            why = f"links {_plural(n, 'it', 'them')} more strongly (score {ws:g} vs {ls:g})"
        else:
            why = f"comes first in the schedule (equal link scores of {ws:g})"
        impact = loser.impact_of_removing(eids)
        loser.remove(eids, FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, f"also claimed in {winner.adj.adj_id}")
        docs = sorted({d for e in eids for d in loser.entry_docs(e) + winner.entry_docs(e)})
        _flag(
            loser,
            FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
            Severity.CRITICAL,
            f"{loser.describe_many(eids)} {_plural(n, 'is', 'are')} also claimed in {winner.adj.adj_id} "
            f"({winner.adj.title}), which {why}; removed here so the same cost is not added back twice.",
            entry_ids=eids,
            doc_ids=docs,
            related=[winner.adj.adj_id],
            impact=impact,
        )
        winner.add_fact(
            Fact(
                text=(
                    f"{winner.describe_many(eids)} {_plural(n, 'is', 'are')} also claimed in {loser.adj.adj_id}; "
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
        impact = t.impact_of_removing(eids)
        t.remove(eids, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA, f"{acct} is {klass}, already below EBITDA")
        total = sum((t.amount(e) for e in eids), ZERO)
        n = len(eids)
        _flag(
            t,
            FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
            Severity.CRITICAL,
            f"{n} claimed {_plural(n, 'entry', 'entries')} ({money(total)}) sit in {acct} {info.entry.account_name}, "
            f"which is classified {klass} and is already added back to reach EBITDA; adding "
            f"{_plural(n, 'it', 'them')} back again would double count: {t.describe_many(eids)}.",
            entry_ids=eids,
            impact=impact,
        )
        account = idx.accounts.get(acct)
        basis = f" ({account.mapping_basis})" if account is not None and account.mapping_basis else ""
        t.add_fact(Fact(text=f"Account {acct} {info.entry.account_name} maps to {klass}{basis}.", entry_ids=eids))


def contradictions(t: AdjustmentTrace, ctx: ChallengeContext) -> None:
    """Verified AI contradictions, one flag per document. The AI may name entries;
    code keeps only those the document demonstrably relates to."""
    idx = t.index
    if ctx.ai is None or not t.doc_links:
        return
    facts = [idx.facts[d] for d in t.evidence_docs() if d in idx.facts]
    claimed = t.in_play_ids()
    if not claimed or not facts:
        return
    try:
        found = ctx.ai.find_contradictions(t.adj, t.intent, facts, [idx.by_id[e].entry for e in claimed])
    except Exception as exc:  # an AI failure must not stop the review; it is recorded
        t.notes.append(f"find_contradictions failed: {exc}")
        return
    by_doc: dict[str, list] = {}
    for c in found:
        if c.quote.doc_id != c.doc_id or not verify_quote(c.quote, idx.docs):
            t.dropped_quotes += 1
            continue
        by_doc.setdefault(c.doc_id, []).append(c)
    claimed_set = set(claimed)
    claimed_groups = {t.group_of[e] for e in claimed if e in t.group_of}
    removable = not (t.is_normalization or t.is_pro_forma)
    # Documents that contradict the same entries share one flag.
    merged: dict[tuple[str, ...], list[tuple[str, list[EvidenceQuote], list[str], list[str]]]] = {}
    for doc_id, items in by_doc.items():
        quotes: list[EvidenceQuote] = []
        for c in items:
            if all((c.quote.page, c.quote.quote) != (x.page, x.quote) for x in quotes) and len(quotes) < 2:
                quotes.append(c.quote)
        statements = list(dict.fromkeys(_sentence(c.statement) for c in items if c.statement.strip()))
        conflicts = list(dict.fromkeys(_sentence(c.conflicts_with) for c in items if c.conflicts_with.strip()))
        proposed = {e for c in items for e in c.entry_ids if e in claimed_set}
        scope = [e for e in claimed if e in proposed and _doc_relates_to_entry(t, doc_id, e)]
        if not scope and not proposed:
            groups = [g for g in t.groups_for_doc(doc_id) if g in claimed_groups]
            scope = [e for e in claimed if t.group_of.get(e) in groups]
            if not scope and len(claimed_groups) == 1:
                # One kind of activity is claimed, so a document contradicting the claim covers all of it.
                scope = list(claimed)
        merged.setdefault(tuple(scope), []).append((doc_id, quotes, statements, conflicts))
    for scope_key, docs in merged.items():
        scope = list(scope_key)
        doc_ids = [d for d, _, _, _ in docs]
        quotes = [q for _, qs, _, _ in docs for q in qs][:3]
        parts = []
        for doc_id, qs, statements, _ in docs:
            parts.append(f"{doc_id} states {' '.join(_quoted(q.quote) for q in qs)} {' '.join(statements)}".rstrip())
        conflicts = list(dict.fromkeys(c for _, _, _, cs in docs for c in cs))
        msg = " ".join(parts)
        if conflicts:
            msg += f" Conflicts with: {' '.join(conflicts)}"
        impact = None
        if scope and removable:
            impact = t.impact_of_removing(scope)
            t.remove(scope, FlagCode.CONTRADICTORY_EVIDENCE, f"{doc_ids[0]}: {_quoted(_short(quotes[0].quote, 60), end=False)}")
            msg += f" Removes {t.describe_groups(scope)}."
        elif not scope:
            msg += " It could not be tied to specific GL entries, so nothing was removed."
            t.add_judgment(
                f"Does {doc_ids[0]} ({_quoted(_short(quotes[0].quote), end=False)}) undermine the adjustment as a whole? "
                "The tool could not tie it to specific GL entries."
            )
        _flag(
            t,
            FlagCode.CONTRADICTORY_EVIDENCE,
            Severity.WARNING,
            msg,
            entry_ids=scope,
            doc_ids=doc_ids,
            quotes=quotes,
            impact=impact,
        )
        for q in quotes:
            t.add_fact(Fact(text=f"{q.doc_id}: {_quoted(q.quote, end=False)}", entry_ids=scope, quotes=[q]))
        if scope:
            t.add_judgment(
                f"Does {doc_ids[0]} ({_quoted(_short(quotes[0].quote, 60), end=False)}) outweigh management's description of "
                f"{t.describe_groups(scope, 2)}?"
            )


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
    try:
        results = ctx.ai.classify_entries(t.adj, t.intent, [idx.by_id[e].entry for e in remaining], facts)
    except Exception as exc:  # an AI failure must not stop the review; it is recorded
        t.notes.append(f"classify_entries failed: {exc}")
        return
    remaining_set = set(remaining)
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
        code = FlagCode.RECURRING_PATTERN if _RECURRENCE_REASON.search(c.reason) else FlagCode.CONTRADICTORY_EVIDENCE
        buckets.setdefault((code, " ".join(c.reason.split()), tuple(docs)), []).append(c.entry_id)
    for (code, reason, docs), eids in sorted(buckets.items(), key=lambda kv: idx.by_id[kv[1][0]].pos):
        impact = t.impact_of_removing(eids)
        t.remove(eids, code, f"does not fit management's basis: {reason}", source="ai")
        for d in docs:
            for e in eids:
                t.associate(d, e, "classification", 0.0, "")
        quotes = [q for d in docs for q in idx.facts[d].key_statements[:1]]
        n = len(eids)
        _flag(
            t,
            code,
            Severity.WARNING,
            f"Entry review: {t.describe_many(eids)} {_plural(n, 'does', 'do')} not fit management's basis: "
            f"{_sentence(reason)} Basis: {', '.join(docs)}. Removed.",
            entry_ids=eids,
            doc_ids=list(docs),
            quotes=quotes,
            impact=impact,
        )
        t.add_judgment(
            f"Do you agree that {t.describe_groups(eids)} {_plural(n, 'does', 'do')} not qualify ({_short(reason, 80)})? "
            f"This removal rests on an AI reading of {', '.join(docs)}."
        )
    if unverified:
        t.add_judgment(
            f"The AI suggested that {t.describe_many(unverified)} may not fit management's basis but cited no "
            "verifiable document that relates to them; the entries were kept. Should they be?"
        )


def _term_fee(term: TermFact) -> Optional[Decimal]:
    for text in (term.text, term.quote.quote):
        m = _MONEY.search(text or "")
        if m:
            try:
                return D(m.group(1))
            except ValueError:
                continue
    return None


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


def _term_end_month(term: TermFact, facts: DocFacts) -> Optional[str]:
    text = f"{term.text} {term.quote.quote}"
    n = _TERM_MONTHS.search(text)
    start = _TERM_START.search(text)
    if n and start:
        after = _dates_in(text[start.end() :])
        if after:
            return add_months(after[0], int(n.group(1)) - 1)
    dates = _dates_in(text)
    if dates:
        return max(dates)
    if facts.service_period_end and _VALID_MONTH.match(facts.service_period_end[:7]):
        return facts.service_period_end[:7]
    return None


def continuing_obligation(t: AdjustmentTrace) -> None:
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
        terms: list[TermFact] = []
        fees: list[Decimal] = []
        feeless = False
        for term in facts.terms:
            kind = term.kind.strip().lower()
            text = f"{term.text} {term.quote.quote}"
            if _FINITE.search(text):
                continue
            if kind in _CONTINUING_KINDS:
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
        terms = [term for _, ts in docs for term in ts]
        impact = t.impact_of_removing(scope)
        t.remove(scope, FlagCode.CONTINUING_OBLIGATION, f"{doc_ids[0]} sets a continuing obligation")
        described = "; ".join(dict.fromkeys(_short(term.text, 70) for term in terms[:3]))
        _flag(
            t,
            FlagCode.CONTINUING_OBLIGATION,
            Severity.WARNING,
            f"{' and '.join(doc_ids[:2])} set{'s' if len(doc_ids) == 1 else ''} a continuing obligation ({described}) "
            f"covering {t.describe_groups(scope)}. An obligation that runs past the last claimed month "
            f"({month_label(last)}) is part of the ongoing cost base, not non-recurring.",
            entry_ids=scope,
            doc_ids=doc_ids,
            quotes=[term.quote for term in terms[:3]],
            impact=impact,
        )
        for doc_id, ts in docs:
            for term in ts[:3]:
                t.add_fact(Fact(text=f"{doc_id}: {term.text}", quotes=[term.quote]))
        t.add_judgment(
            f"Is the obligation under {doc_ids[0]} part of the ongoing cost base after closing? "
            f"The tool removed {t.describe_groups(scope, limit=2)} on that basis."
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
    """Record comparable activity for each claimed group; remove groups that recur."""
    idx = t.index
    if not t.asserts_nonrecurring:
        return
    claimed = t.in_play_ids()
    if not claimed:
        return
    tol = idx.tolerance
    # Activity inside this claim (including items lost to another adjustment) is not "elsewhere".
    claimed_set = set(t.claimed_ids())
    event_months = _valid_months(t.intent.event_months)
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
        window = [idx.by_id[e].month for e in g_claimed] + event_months
        lo, hi = min(window), max(window)
        typical = _median_abs([t.amount(e) for e in g_claimed])
        similar_months = sorted(
            {
                info.month
                for info, _ in comparables
                if (info.month < lo or info.month > hi) and SIMILAR_LOW * typical <= abs(info.amount) <= SIMILAR_HIGH * typical
            }
        )
        recurring = bool(prior_hits) or len(similar_months) >= RECURRENCE_MIN_MONTHS
        comp_ids = [info.entry_id for info, _ in comparables]
        for info, why in comparables:
            t.add_context_link(info.entry_id, 0.0, f"Comparable activity for {g}: {why}")

        parts: list[str] = []
        for lbl in prior_hits:
            pct = int((s * by_label[lbl] / g_amount * 100).to_integral_value())
            parts.append(
                f"{money(by_label[lbl])} of comparable activity in {lbl}, where nothing is claimed "
                f"({pct}% of the {money(s * g_amount)} claimed)"
            )
        if len(similar_months) >= RECURRENCE_MIN_MONTHS:
            parts.append(
                f"similar amounts in {len(similar_months)} months outside the claimed window "
                f"({month_span(similar_months)})"
            )
        claimed_txt = ", ".join(f"{lbl} {money(s * v)}" for lbl, v in per_label.items() if v)
        note = (
            f"Claimed: {claimed_txt}. Comparable activity outside the claim: "
            + ", ".join(f"{lbl} {money(v)}" for lbl, v in by_label.items() if v)
            + "."
        )
        t.recurrence.append(
            RecurrenceObservation(
                group=g,
                amounts_by_period={lbl: fmt(v) for lbl, v in by_label.items()},
                entry_ids=idx.sort_ids(comp_ids),
                note=note if recurring else note + " Below the recurrence threshold.",
            )
        )
        if recurring:
            impact = t.impact_of_removing(g_claimed)
            t.remove(g_claimed, FlagCode.RECURRING_PATTERN, f"{g} recurs outside the claimed period")
            _flag(
                t,
                FlagCode.RECURRING_PATTERN,
                Severity.WARNING,
                f"{g} recurs: {'; '.join(parts)}. Management claims it as non-recurring ({claimed_txt}); removed.",
                entry_ids=g_claimed + comp_ids,
                impact=impact,
            )
            t.add_judgment(
                f"Is {g} part of the ongoing cost base? It was removed as recurring; management would need to "
                "show why the claimed activity differs from the comparable activity."
            )
        elif any(by_label[lbl] for lbl in uncovered):
            seen = ", ".join(f"{lbl} {money(by_label[lbl])}" for lbl in uncovered if by_label[lbl])
            t.add_judgment(
                f"{g}: comparable activity ({seen}) is below the recurrence threshold. Should only the excess "
                "over that routine level be added back?"
            )


def _service_quote(facts: DocFacts, months: list[str]) -> Optional[EvidenceQuote]:
    years = {m[:4] for m in months}
    pattern = re.compile(r"service|period|" + "|".join(sorted(years)), re.IGNORECASE)
    for q in facts.key_statements + [a.quote for a in facts.amounts] + [x.quote for x in facts.terms]:
        if pattern.search(q.quote):
            return q
    return None


def out_of_period(t: AdjustmentTrace) -> None:
    """Move entries whose documented service period sits in another analysis period."""
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
            if book_labels == svc_labels:
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
            for lbl, v in contrib.items():
                if v:
                    t.effects.append(Effect(lbl, v, FlagCode.OUT_OF_PERIOD, e))
            quote = _service_quote(facts, s_months)
            belongs = ", ".join(sorted(svc_labels, key=t.labels.index)) or "months before the analysis periods"
            booked = ", ".join(sorted(book_labels, key=t.labels.index)) or "the booking month"
            _flag(
                t,
                FlagCode.OUT_OF_PERIOD,
                Severity.WARNING,
                f"{t.describe(e)} covers services in {month_span(s_months)} per {doc_id}, not the booking month. "
                f"The cost belongs to {belongs}, so it moves out of {booked} pro rata by service month.",
                entry_ids=[e],
                doc_ids=[doc_id],
                quotes=[quote],
                impact=realloc,
            )
            t.add_fact(
                Fact(
                    text=f"{doc_id} states a service period of {month_span(s_months)} for {t.describe(e)}.",
                    entry_ids=[e],
                    quotes=[quote] if quote else [],
                )
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
                reasons.append(f"the memo cites {display}" + (f", stated in {doc_id}" if doc_id else ", named by management"))
                if doc_id:
                    cited.append(doc_id)
                break
        party: frozenset[str] = frozenset()
        for name, toks in names:
            if names_match(info.cp_tokens, toks) or name_in_text(toks, info.memo_tokens):
                score += W_COUNTERPARTY
                reasons.append(f"the payer matches '{name}'")
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
        for lbl in labels_in:
            t.effects.append(Effect(lbl, info.amount, FlagCode.OFFSETTING_RECOVERY, eid))
        t.add_context_link(eid, score, "Offsetting recovery: " + "; ".join(reasons))
        quotes: list[EvidenceQuote] = []
        # The claim / settlement letter behind the recovery: any document stating the reference the memo cites.
        for n in sorted(info.refs):
            for d in idx.docs_by_ref.get(n, []) + idx.docs_by_text_ref.get(n, []):
                if d not in docs:
                    docs.append(d)
        docs = sorted(docs)
        for d in docs:
            t.associate(d, eid, "recovery", 0.0, "")
            t.doc_links[d].relation = "recovery"
            quotes += [a.quote for a in idx.facts[d].amounts if _amount_is(a.amount, info.amount, idx.tolerance)]
        e = info.entry
        who = f" from {e.counterparty}" if e.counterparty else ""
        _flag(
            t,
            FlagCode.OFFSETTING_RECOVERY,
            Severity.WARNING,
            f"{money(abs(info.amount))} received{who} in {month_label(info.month)} ({e.account} {e.account_name}: "
            f"\"{e.memo}\") relates to the same event: {', '.join(reasons)}. Management did not adjust it, so it "
            f"offsets the add-back in the period received.",
            entry_ids=[eid],
            doc_ids=docs,
            quotes=quotes,
            impact={lbl: info.amount for lbl in labels_in},
        )
        t.add_fact(
            Fact(
                text=f"Recovery of {money(abs(info.amount))} booked {month_label(info.month)} to {e.account} "
                f"{e.account_name} (\"{e.memo}\").",
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
            f"{booked}{', in ' + ', '.join(where) if where else ''}. Diligence carries only the activity in "
            f"{lbl}: {money(proposed)}.",
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
            f"({nature}); the sign of the adjustment conflicts with the GL.",
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
        _flag(
            t,
            FlagCode.DUPLICATE_GL_ENTRY,
            Severity.WARNING,
            f"{t.describe(e)} is part of a possible duplicate posting ({', '.join(group)}: same account, amount, "
            f"and party); {len(inside)} of the {len(group)} postings are in the claimed set.",
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
            f"{doc_id} ({facts.doc_type.replace('_', ' ')}) is {state}; it cannot support the adjustment until "
            "executed.",
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
                        Fact(text=f"{doc_id} sets the normalized level at {money(annual)} a year.", quotes=[a.quote])
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
                f"{lbl}: no actual cost for the normalized item was found in the GL; the normalization cannot be "
                "measured for this period.",
                label=lbl,
                amount_impact=-t.claim(lbl),
            )
        else:
            t.add_fact(
                Fact(
                    text=f"{lbl}: actual cost in the GL is {money(actual[lbl])} "
                    f"({len(t.claimed.get(lbl, []))} entries); management claims {money(t.claim(lbl))}.",
                    entry_ids=t.claimed.get(lbl, []),
                )
            )
    if info.supported_by is None:
        level_txt = money(candidates[0]) if candidates else "the normalized level"
        if info.draft_docs:
            detail = f"the only document stating {level_txt} is {', '.join(info.draft_docs)}, which is not executed"
        else:
            detail = f"no linked document states {level_txt}"
        _flag(
            t,
            FlagCode.NORMALIZATION_BENCHMARK_MISSING,
            Severity.WARNING,
            f"The normalized level of {level_txt} a year is not supported: {detail}, and there is no market benchmark.",
            doc_ids=info.draft_docs,
        )
        t.add_judgment(
            f"Is {level_txt} a year a supportable market level? Management's claim implies it, but no executed "
            "agreement or benchmark sets it."
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
        reasons.append(f"the GL shows the cost continuing through {month_label(last)} ({t.describe_groups(continuing, 2)})")
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
        reasons.append(f"management dates the event to {month_label(future[0])}, after the last GL month ({month_label(last)})")
    if not reasons:
        return
    quotes = [q for d in sorted(t.doc_links) for q in idx.facts[d].key_statements[:1]][:3]
    _flag(
        t,
        FlagCode.PRO_FORMA_NOT_REALIZED,
        Severity.CRITICAL,
        f"Pro forma savings not realized: {'; '.join(reasons)}.",
        entry_ids=continuing,
        doc_ids=[q.doc_id for q in quotes],
        quotes=quotes,
    )
    t.add_judgment(
        "Should savings that have not yet occurred be carried in diligence EBITDA, or only disclosed as a "
        "run-rate consideration?"
    )


def document_coverage(t: AdjustmentTrace) -> None:
    """NO_DOCUMENT_SUPPORT per period; above 25% of the claim it drives REQUEST_INFO."""
    idx = t.index
    if t.is_normalization or t.is_pro_forma:
        return
    tol = idx.tolerance
    for lbl in t.claimed_labels():
        claim = t.claim(lbl)
        undoc = [e for e in t.supporting(lbl) if not t.entry_docs(e)]
        amount = sum((t.amount(e) for e in undoc), ZERO)
        if abs(amount) <= tol:
            continue
        share = abs(amount) / abs(claim)
        pct = int((share * 100).to_integral_value())
        msg = f"{lbl}: {money(abs(amount))} ({pct}% of the claim) has no linked document: {t.describe_groups(undoc)}."
        if t.asserts_personal:
            # For owner / personal items the GL description is the primary evidence; the gap is noted, not blocking.
            severity = Severity.INFO
            msg += " The GL descriptions identify the items; no third-party document was provided."
            t.add_judgment(
                f"Are {t.describe_groups(undoc, 2)} personal rather than business costs? The GL description is "
                "the only evidence."
            )
        elif share > UNDOCUMENTED_SHARE_LIMIT:
            severity = Severity.WARNING
            msg += " This is above the 25% limit, so documents are needed before diligence can carry it."
        else:
            severity = Severity.INFO
        _flag(t, FlagCode.NO_DOCUMENT_SUPPORT, severity, msg, entry_ids=undoc, label=lbl)
