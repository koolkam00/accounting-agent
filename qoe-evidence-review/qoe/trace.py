"""Per-adjustment tracing (SPEC §5.2-5.3): link GL entries and documents to a
management adjustment, group the linked activity, and fit the claimed set.

The output is a mutable ``AdjustmentTrace``. challenge.py removes entries from
it and records amount effects; propose.py turns it into an
``AdjustmentAssessment``. Link scores are additive evidence weights, not
probabilities, and every signal that fired is written to the link's reasons in
words a reviewer can check against the GL.

Sign conventions: GL amounts are debit-positive, adjustment amounts are
EBITDA-signed. Removing an entry from the P&L changes EBITDA by
``+entry.amount`` whatever its class, so the EBITDA effect of claiming an
entry is simply its GL amount.
"""

from __future__ import annotations

import re
import unicodedata
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Iterable, Optional, Sequence

from qoe.ai_base import AdjustmentIntent
from qoe.money import ZERO, D, fmt, q2
from qoe.periods import month_range, months_in
from qoe.schemas import (
    Account,
    AdjustmentCategory,
    AdjustmentClaim,
    DataQualityCode,
    DealPackage,
    DocFacts,
    DocLink,
    EbitdaClass,
    EvidenceQuote,
    Fact,
    Flag,
    FlagCode,
    GLEntry,
    GLLink,
    PeriodDef,
    ReconciliationResult,
    RecurrenceObservation,
    Severity,
    SourceDocument,
)

# ---------------------------------------------------------------------------
# Scoring weights and thresholds (SPEC §5.2)
# ---------------------------------------------------------------------------

# Management names whole accounts, and an account usually holds unrelated
# activity too, so the account signal alone must stay below the threshold.
W_ACCOUNT = 1.0
# A named vendor is strong, but vendors bill for more than one thing (a law
# firm's monthly retainer and its litigation matter), so it needs one more signal.
W_COUNTERPARTY = 1.5
# Keywords come from management's narrative. They are cheap to match and easy
# to over-match, so the first hit counts fully and extra hits add little.
W_KEYWORD = 1.0
W_KEYWORD_EXTRA = 0.25
W_KEYWORD_EXTRA_CAP = 0.5
# A matter / claim / contract number is specific enough to link on its own.
W_REFERENCE = 2.5
# So is a document that names the entry's own document number, or that shows
# the same amount for the same counterparty.
W_DOCUMENT = 2.5
LINK_THRESHOLD = 2.0
# When no exact subset explains a claim, only entries with two independent
# signals are treated as claimed: account + party, party + keyword, or a
# reference / document on its own. Account + keyword (2.0) is not enough.
STRONG_LINK = 2.5
# Meet-in-the-middle over 2 x 15 items is ~65k subsets: exact and fast.
MAX_SUBSET_ITEMS = 30

# Document-to-adjustment weights.
DW_SUPPORT_REF = 3.0  # management cited the document (data-room index or name)
DW_COUNTERPARTY = 2.0
DW_REFERENCE = 2.5
DW_TITLE_KEYWORD = 1.0  # per keyword in the document title, capped below
DW_TITLE_KEYWORD_CAP = 2.0
DW_ENTRY_NUMBER = 2.5  # document states a linked entry's doc number
DW_ENTRY_AMOUNT = 2.0  # same amount and counterparty as a linked entry
DW_ENTRY_NAMED = 1.0  # a cited document's text names the entry's counterparty
# A party name alone (2.0) does not pre-link a document: an owner or a bank is
# party to documents about several adjustments. Citation or a shared reference does.
DOC_LINK_THRESHOLD = 2.5

# Token overlap needed for two counterparty names to match, measured against
# the shorter name ("Marlow & Finch" vs "Marlow & Finch LLP" = 1.0).
NAME_OVERLAP_MIN = 0.6

AGREEMENT_DOC_TYPES = frozenset(
    {
        "engagement_letter",
        "contract",
        "settlement_agreement",
        "separation_agreement",
        "agreement",
        "employment_agreement",
        "lease",
        "insurance",
    }
)
CORRESPONDENCE_DOC_TYPES = frozenset({"correspondence", "memo", "email"})

# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_REF_TOKEN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?")
_YEAR = re.compile(r"^(?:19|20)\d\d$")
_INDEX_REF = re.compile(
    r"^\s*(?:dr|data\s*room|vdr|tab|folder|section|ref|index)?\s*[#:]?\s*(\d+(?:\.\d+)*)\s*$", re.IGNORECASE
)
# A document reference written into a memo ("Matter 7710", "claim AM-77-X").
_MEMO_REF = re.compile(
    r"\b(matter|contract|agreement|project|claim|case|policy|job|po|sow|engagement|work order)"
    r"\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Za-z]{0,4}-?\d[A-Za-z0-9\-]*)",
    re.IGNORECASE,
)

_LEGAL_TOKENS = frozenset(
    "llc inc ltd llp lp co corp corporation company pllc pc plc the and of na dba".split()
)
# Words that appear in many unrelated names; a match needs something more distinctive.
_GENERIC_NAME_TOKENS = frozenset(
    """services service systems solutions group partners partner associates consulting holdings
    international enterprises management financial insurance bank construction supply supplies
    contractors contractor builders advisors advisory capital global national american mutual
    technologies technology industries professional professionals law firm office""".split()
)
_WEAK_KEYWORDS = frozenset(
    """fee fees cost costs expense expenses payment payments service services one time one-time non
    nonrecurring non-recurring recurring adjustment adjustments total other misc general amount
    invoice invoices vendor account""".split()
)
_MONTH_WORDS = frozenset(
    """jan january feb february mar march apr april may jun june jul july aug august sep sept
    september oct october nov november dec december""".split()
)
_THEME_STOP = frozenset(
    """and the of for to a an in on at by per re inv invoice bill no ref num payment pmt paid fy ytd
    qtr q1 q2 q3 q4 dated from thru through""".split()
)
_MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def norm_text(value: Optional[str]) -> str:
    """Lowercase ASCII words separated by single spaces ('&' becomes 'and')."""
    s = unicodedata.normalize("NFKD", value or "").lower().replace("&", " and ")
    return " ".join(_NON_ALNUM.sub(" ", s).split())


def name_tokens(name: Optional[str]) -> frozenset[str]:
    """Distinctive tokens of a party name: no legal suffixes, initials, or numbers."""
    return frozenset(t for t in norm_text(name).split() if len(t) > 1 and t not in _LEGAL_TOKENS and not t.isdigit())


def names_match(a: frozenset[str], b: frozenset[str]) -> bool:
    if not a or not b:
        return False
    shared = a & b
    if not (shared - _GENERIC_NAME_TOKENS):
        return False
    return len(shared) / min(len(a), len(b)) >= NAME_OVERLAP_MIN


def name_in_text(name: frozenset[str], text_tokens: frozenset[str]) -> bool:
    """Every distinctive token of the name appears in the text."""
    distinctive = name - _GENERIC_NAME_TOKENS
    return bool(distinctive) and distinctive <= text_tokens


def name_mentioned(name: frozenset[str], text_tokens: frozenset[str]) -> bool:
    """Most of a party's distinctive name appears in the text ('Ridgeway plant visit' names 'Ridgeway Air Systems')."""
    distinctive = name - _GENERIC_NAME_TOKENS
    if not distinctive:
        return False
    shared = len(distinctive & text_tokens)
    return shared >= 1 and shared / len(distinctive) >= NAME_OVERLAP_MIN


def ref_norm(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", value or "").upper()


def _valid_ref(norm: str) -> bool:
    return len(norm) >= 3 and any(c.isdigit() for c in norm) and not _YEAR.match(norm) and norm.strip("0") != ""


def ref_tokens(text: Optional[str]) -> frozenset[str]:
    """Normalized reference-like tokens (containing a digit) in free text."""
    out = set()
    for tok in _REF_TOKEN.findall(text or ""):
        n = ref_norm(tok)
        if _valid_ref(n):
            out.add(n)
    return frozenset(out)


def theme_tokens(memo: str, drop: frozenset[str] = frozenset()) -> tuple[str, ...]:
    """Memo with dates, amounts, invoice numbers, month names, and the party name stripped."""
    seen: list[str] = []
    for t in norm_text(memo).split():
        if len(t) < 2 or any(c.isdigit() for c in t) or t in _MONTH_WORDS or t in _THEME_STOP or t in drop:
            continue
        if t not in seen:
            seen.append(t)
    return tuple(seen)


def theme_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


_SUFFIXES = ("ations", "ation", "ings", "ing", "ers", "er", "ies", "es", "ed", "s")
# Short stems match too much: five letters keeps "dispatch" and "repair" but not "rent" or "fee".
_MIN_STEM = 5


def stem(word: str) -> str:
    """Crude suffix stripping so 'dispatcher' meets 'dispatch' and 'repairs' meets 'repair'."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def keyword_list(keywords: Iterable[str]) -> list[str]:
    out: list[str] = []
    for kw in keywords:
        n = norm_text(kw)
        if len(n) < 3 or n in _WEAK_KEYWORDS or n in out:
            continue
        out.append(n)
    return out


def keyword_hits(
    keywords: Sequence[str], text_norm: str, tokens: frozenset[str], party: frozenset[str] = frozenset()
) -> list[str]:
    """Keywords found in the text. Words that only restate ``party`` (a name that already
    scored as the counterparty signal) are not counted twice."""
    hits: list[str] = []
    padded = f" {text_norm} "
    for kw in keywords:
        if party and set(kw.split()) <= party:
            continue
        if " " in kw:
            ok = f" {kw} " in padded
        else:
            ok = kw in tokens or (len(kw) >= 4 and any(t.startswith(kw) for t in tokens))
            if not ok and len(stem(kw)) >= _MIN_STEM:
                ok = any(stem(t) == stem(kw) for t in tokens)
        if ok:
            hits.append(kw)
    return hits


# ---------------------------------------------------------------------------
# Display helpers (shared by challenge.py and propose.py)
# ---------------------------------------------------------------------------


def money(value: object) -> str:
    """Deals-style amount: thousands separators, no '.00', negatives in parentheses."""
    d = q2(D(value))
    neg = d < 0
    s = f"{abs(d):,.2f}"
    if s.endswith(".00"):
        s = s[:-3]
    return f"({s})" if neg else s


def month_label(month: str) -> str:
    try:
        y, m = month.split("-")
        return f"{_MONTH_ABBR[int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return month


def month_span(months: Iterable[str]) -> str:
    ms = sorted(set(months))
    if not ms:
        return ""
    if len(ms) == 1:
        return month_label(ms[0])
    return f"{month_label(ms[0])}–{month_label(ms[-1])}"


def cents(value: Decimal) -> int:
    return int(q2(value) * 100)


# Reviewer-facing text limits: a flag message is one or two sentences, a rationale a short paragraph.
MAX_MESSAGE = 320
MAX_RATIONALE = 600


def plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def entries_word(n: int) -> str:
    return f"{n} {plural(n, 'entry', 'entries')}"


def join_limited(items: Sequence[str], limit: int = 2, sep: str = ", ") -> str:
    """'a, b and 3 more': names beyond ``limit`` are counted, not listed."""
    items = list(dict.fromkeys(i for i in items if i))
    if len(items) <= limit:
        return " and ".join(items) if len(items) == 2 and sep == ", " else sep.join(items)
    return f"{sep.join(items[:limit])} and {len(items) - limit} more"


def _short_sentence(text: str, limit: int = MAX_MESSAGE) -> str:
    """Collapse whitespace; an over-long text is cut at a word boundary and closed with an ellipsis."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit - 1)
    return text[: cut if cut > limit // 2 else limit - 1].rstrip(" ,;:") + "…"


def periods_text(amounts: dict[str, Decimal], labels: Sequence[str]) -> str:
    """'35,500 in FY2025 and TTM Jun-26' when equal, else 'FY2025 35,500; TTM Jun-26 30,000'."""
    nonzero = [(lbl, amounts[lbl]) for lbl in labels if amounts.get(lbl)]
    if not nonzero:
        return "0"
    if len({v for _, v in nonzero}) == 1:
        return f"{money(nonzero[0][1])} in {' and '.join(lbl for lbl, _ in nonzero)}"
    return "; ".join(f"{lbl} {money(v)}" for lbl, v in nonzero)


# ---------------------------------------------------------------------------
# Deal-wide index (built once per run)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EntryInfo:
    entry: GLEntry
    pos: int  # position in date order; the stable sort key for entry ids
    klass: EbitdaClass
    amount: Decimal
    month: str
    cp_tokens: frozenset[str]
    memo_norm: str
    memo_tokens: frozenset[str]
    refs: frozenset[str]  # reference-like tokens in the memo
    doc_number: str  # normalized doc number
    theme: tuple[str, ...]
    memo_ref: str  # "Matter 7710" when the memo names a document reference
    memo_ref_norm: str

    @property
    def entry_id(self) -> str:
        return self.entry.entry_id


@dataclass
class DealIndex:
    labels: list[str]
    periods: list[PeriodDef]
    tolerance: Decimal
    data_start: str
    data_end: str
    accounts: dict[str, Account]
    entries: list[EntryInfo]
    by_id: dict[str, EntryInfo]
    docs: dict[str, SourceDocument]
    facts: dict[str, DocFacts]
    doc_refs: dict[str, frozenset[str]]
    docs_by_ref: dict[str, list[str]]
    doc_cp: dict[str, frozenset[str]]
    doc_text_tokens: dict[str, frozenset[str]]
    doc_amounts: list[tuple[int, str, Decimal]]  # (cents, doc_id, amount), sorted
    doc_entries: dict[str, frozenset[str]]  # doc_id -> entries whose doc number the document states
    docs_by_text_ref: dict[str, list[str]]  # reference-like token in a document's text -> doc ids
    label_months: dict[str, frozenset[str]]
    duplicate_groups: dict[str, list[str]]
    # Management's own below-EBITDA lines by class and the GL's, per period label, so a
    # claim of already-excluded costs can be shown against the line that adds them back.
    mgmt_lines: dict[EbitdaClass, dict[str, Decimal]] = field(default_factory=dict)
    gl_lines: dict[EbitdaClass, dict[str, Decimal]] = field(default_factory=dict)
    _amount_keys: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._amount_keys = [k for k, _, _ in self.doc_amounts]

    def labels_of(self, month: str) -> list[str]:
        return [lbl for lbl in self.labels if month in self.label_months[lbl]]

    def docs_with_amount(self, amount: Decimal) -> list[tuple[str, Decimal]]:
        """Documents stating ``abs(amount)`` within the tie-out tolerance."""
        c, tol = cents(abs(amount)), cents(self.tolerance)
        lo, hi = bisect_left(self._amount_keys, c - tol), bisect_right(self._amount_keys, c + tol)
        return [(doc_id, amt) for _, doc_id, amt in self.doc_amounts[lo:hi]]

    def sort_ids(self, ids: Iterable[str]) -> list[str]:
        return sorted(set(ids), key=lambda e: (self.by_id[e].pos if e in self.by_id else 1 << 30, e))


def _entry_info(entry: GLEntry, pos: int, klass: EbitdaClass) -> EntryInfo:
    cp = name_tokens(entry.counterparty)
    memo_norm = norm_text(entry.memo)
    m = _MEMO_REF.search(entry.memo or "")
    memo_ref, memo_ref_norm = "", ""
    if m and _valid_ref(ref_norm(m.group(2))):
        memo_ref, memo_ref_norm = f"{m.group(1)} {m.group(2)}", ref_norm(m.group(2))
    return EntryInfo(
        entry=entry,
        pos=pos,
        klass=klass,
        amount=D(entry.amount),
        month=entry.period or entry.date[:7],
        cp_tokens=cp,
        memo_norm=memo_norm,
        memo_tokens=frozenset(memo_norm.split()),
        refs=ref_tokens(entry.memo),
        doc_number=ref_norm(entry.doc_number),
        theme=theme_tokens(entry.memo, cp),
        memo_ref=memo_ref,
        memo_ref_norm=memo_ref_norm,
    )


def build_index(
    pkg: DealPackage, facts: Iterable[DocFacts], recon: Optional[ReconciliationResult] = None
) -> DealIndex:
    """Precompute per-entry and per-document features used by every adjustment."""
    meta = pkg.meta
    ordered = sorted(pkg.gl, key=lambda e: (e.date, e.source_row, e.entry_id))
    entries: list[EntryInfo] = []
    for e in ordered:
        acct = pkg.accounts.get(e.account)
        # An account missing from the chart is treated as P&L so it can still be traced.
        klass = acct.ebitda_class if acct is not None else EbitdaClass.OPEX
        if klass == EbitdaClass.BALANCE_SHEET:
            continue
        entries.append(_entry_info(e, len(entries), klass))

    docs = {d.doc_id: d for d in pkg.documents}
    facts_by_id = {f.doc_id: f for f in facts if f.doc_id in docs}
    for doc_id in docs:
        facts_by_id.setdefault(doc_id, DocFacts(doc_id=doc_id, doc_type="other"))

    doc_refs: dict[str, frozenset[str]] = {}
    docs_by_ref: dict[str, list[str]] = {}
    doc_amounts: list[tuple[int, str, Decimal]] = []
    for doc_id in sorted(docs):
        f = facts_by_id[doc_id]
        refs: set[str] = set()
        for r in f.reference_numbers:
            refs |= ref_tokens(r)
        doc_refs[doc_id] = frozenset(refs)
        for r in sorted(refs):
            docs_by_ref.setdefault(r, []).append(doc_id)
        for a in f.amounts:
            try:
                amt = abs(D(a.amount))
            except (ValueError, ArithmeticError):
                continue
            if amt > 0:
                doc_amounts.append((cents(amt), doc_id, amt))
    doc_amounts.sort(key=lambda x: (x[0], x[1]))

    doc_cp = {d: name_tokens(facts_by_id[d].counterparty) for d in docs}
    by_number: dict[str, list[EntryInfo]] = {}
    for info in entries:
        if info.doc_number:
            by_number.setdefault(info.doc_number, []).append(info)
    doc_entries: dict[str, frozenset[str]] = {}
    for doc_id in sorted(docs):
        hits = set()
        for r in doc_refs[doc_id]:
            for info in by_number.get(r, []):
                # A bare number can collide across vendors; require the party to agree when both are known.
                if not (doc_cp[doc_id] and info.cp_tokens and not names_match(doc_cp[doc_id], info.cp_tokens)):
                    hits.add(info.entry_id)
        doc_entries[doc_id] = frozenset(hits)

    docs_by_text_ref: dict[str, list[str]] = {}
    for doc_id in sorted(docs):
        for r in sorted(ref_tokens(docs[doc_id].full_text)):
            docs_by_text_ref.setdefault(r, []).append(doc_id)

    duplicates: dict[str, list[str]] = {}
    gl_lines: dict[EbitdaClass, dict[str, Decimal]] = {}
    if recon is not None:
        for issue in recon.issues:
            if issue.code == DataQualityCode.DUPLICATE_GL_ENTRY and len(issue.entry_ids) > 1:
                for eid in issue.entry_ids:
                    duplicates[eid] = list(issue.entry_ids)
        for lbl, comp in recon.gl_ebitda.items():
            gl_lines.setdefault(EbitdaClass.INTEREST, {})[lbl] = D(comp.interest)
            gl_lines.setdefault(EbitdaClass.TAXES, {})[lbl] = D(comp.taxes)
            da = D(comp.depreciation) + D(comp.amortization)
            gl_lines.setdefault(EbitdaClass.DEPRECIATION, {})[lbl] = da
            gl_lines.setdefault(EbitdaClass.AMORTIZATION, {})[lbl] = da
    sched = pkg.schedule
    da_line = {k: D(v) for k, v in sched.depreciation_amortization.items()}
    mgmt_lines = {
        EbitdaClass.INTEREST: {k: D(v) for k, v in sched.interest.items()},
        EbitdaClass.TAXES: {k: D(v) for k, v in sched.taxes.items()},
        EbitdaClass.DEPRECIATION: da_line,
        EbitdaClass.AMORTIZATION: da_line,
    }

    return DealIndex(
        labels=[p.label for p in meta.periods],
        periods=list(meta.periods),
        tolerance=D(meta.tolerance),
        data_start=meta.data_start,
        data_end=meta.data_end,
        accounts=dict(pkg.accounts),
        entries=entries,
        by_id={i.entry_id: i for i in entries},
        docs=docs,
        facts=facts_by_id,
        doc_refs=doc_refs,
        docs_by_ref=docs_by_ref,
        doc_cp=doc_cp,
        doc_text_tokens={d: frozenset(norm_text(docs[d].full_text).split()) for d in docs},
        doc_amounts=doc_amounts,
        doc_entries=doc_entries,
        docs_by_text_ref=docs_by_text_ref,
        label_months={p.label: frozenset(months_in(p)) for p in meta.periods},
        duplicate_groups=duplicates,
        mgmt_lines={k: v for k, v in mgmt_lines.items() if v},
        gl_lines=gl_lines,
    )


# ---------------------------------------------------------------------------
# Trace state
# ---------------------------------------------------------------------------


@dataclass
class LinkInfo:
    entry_id: str
    score: float
    reasons: list[str]
    group: str = ""
    context: bool = False  # surfaced by a challenge (recovery, comparable), not by scoring


@dataclass
class DocLinkInfo:
    doc_id: str
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    entry_basis: dict[str, str] = field(default_factory=dict)  # entry_id -> number|amount|group|reference|named|recovery
    relation: str = ""  # set by a challenge to override the doc-type default
    prelinked: bool = False  # related to the adjustment before any GL entry was considered
    cited: bool = False  # named in management's support references
    referenced: bool = False  # states a reference number management named


# Association bases that tie a document to a specific entry (not just its party name).
_SPECIFIC_BASES = frozenset({"number", "amount", "amount_multi", "group", "reference", "mention"})
_MIN_CITED_NUMBER = 5
# Bases that pin a document to one entry: only these may carry a service period onto it.
ENTRY_SPECIFIC_BASES = frozenset({"number", "amount", "group"})


@dataclass
class Removal:
    code: FlagCode
    note: str
    source: str = "code"  # "ai" when an AI entry classification drove it
    doc_ids: list[str] = field(default_factory=list)  # documents the removal rests on


@dataclass
class Effect:
    label: str
    amount: Decimal
    code: FlagCode
    entry_id: str


@dataclass
class PeriodFit:
    label: str
    claim: Decimal
    linked_total: Decimal  # EBITDA-signed total of linked entries in the period
    method: str  # all | groups | entries | strong | elsewhere | normalization
    bounded: bool = False
    ties: int = 1  # exact fits still level when the earliest-entries rule decided (SPEC §5.3)
    cited: int = 0  # chosen entries a support-ref document links to
    elsewhere: list[str] = field(default_factory=list)  # entries outside the period that tie to its claim


@dataclass
class NormalizationInfo:
    actual: dict[str, Decimal]
    level: Optional[Decimal] = None  # annual normalized level the evidence supports
    level_candidates: list[Decimal] = field(default_factory=list)
    supported_by: Optional[str] = None
    draft_docs: list[str] = field(default_factory=list)


@dataclass
class AdjustmentTrace:
    adj: AdjustmentClaim
    intent: AdjustmentIntent
    order: int
    index: DealIndex
    links: dict[str, LinkInfo] = field(default_factory=dict)
    candidates: list[str] = field(default_factory=list)  # linked by score, date order
    groups: dict[str, list[str]] = field(default_factory=dict)  # group label -> linked entry ids
    group_of: dict[str, str] = field(default_factory=dict)
    group_ref: dict[str, str] = field(default_factory=dict)  # group label -> normalized reference
    claimed: dict[str, list[str]] = field(default_factory=dict)  # period label -> claimed entry ids
    fits: dict[str, PeriodFit] = field(default_factory=dict)
    capped: set[str] = field(default_factory=set)
    doc_links: dict[str, DocLinkInfo] = field(default_factory=dict)
    flags: list[Flag] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    judgments: list[str] = field(default_factory=list)
    removals: dict[str, Removal] = field(default_factory=dict)
    moved: set[str] = field(default_factory=set)  # out-of-period entries; effects carry their amount
    effects: list[Effect] = field(default_factory=list)
    recurrence: list[RecurrenceObservation] = field(default_factory=list)
    normalization: Optional[NormalizationInfo] = None
    notes: list[str] = field(default_factory=list)
    dropped_quotes: int = 0  # AI quotes (contradictions) that failed verification
    search_terms: str = ""
    _judgment_keys: set[str] = field(default_factory=set, repr=False)
    _fact_keys: dict[str, int] = field(default_factory=dict, repr=False)

    # -- classification ----------------------------------------------------

    @property
    def is_normalization(self) -> bool:
        return self.intent.is_normalization or self.adj.category == AdjustmentCategory.NORMALIZATION

    @property
    def is_pro_forma(self) -> bool:
        return self.intent.is_pro_forma or self.adj.category == AdjustmentCategory.PRO_FORMA

    @property
    def asserts_nonrecurring(self) -> bool:
        """Recurrence and continuing terms only undercut a 'non-recurring' claim."""
        if self.is_normalization or self.is_pro_forma:
            return False
        if self.adj.category == AdjustmentCategory.NON_RECURRING:
            return True
        return self.adj.category == AdjustmentCategory.OTHER and self.intent.asserts_nonrecurring

    @property
    def asserts_personal(self) -> bool:
        return self.intent.asserts_personal or self.adj.category == AdjustmentCategory.OWNER_DISCRETIONARY

    # -- amounts -----------------------------------------------------------

    @property
    def labels(self) -> list[str]:
        return self.index.labels

    def claim(self, label: str) -> Decimal:
        return D(self.adj.amounts.get(label))

    def claimed_labels(self) -> list[str]:
        return [lbl for lbl in self.labels if self.claim(lbl) != 0]

    def amount(self, entry_id: str) -> Decimal:
        return self.index.by_id[entry_id].amount

    def claimed_ids(self) -> list[str]:
        ids: set[str] = set()
        for v in self.claimed.values():
            ids.update(v)
        return self.index.sort_ids(ids)

    def in_play_ids(self) -> list[str]:
        """Claimed entries that are this adjustment's own items: not lost to another
        adjustment and not already below EBITDA. Evidence challenges look only at these."""
        structural = (FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT, FlagCode.ALREADY_EXCLUDED_FROM_EBITDA)
        return [e for e in self.claimed_ids() if e not in self.removals or self.removals[e].code not in structural]

    def supporting(self, label: str) -> list[str]:
        return [e for e in self.claimed.get(label, []) if e not in self.removals]

    def supporting_ids(self) -> list[str]:
        return [e for e in self.claimed_ids() if e not in self.removals]

    def traced(self, label: str) -> Decimal:
        return sum((self.amount(e) for e in self.claimed.get(label, [])), ZERO)

    def documented(self, label: str) -> Decimal:
        return sum((self.amount(e) for e in self.claimed.get(label, []) if self.support_docs(e)), ZERO)

    def effect(self, label: str) -> Decimal:
        return sum((x.amount for x in self.effects if x.label == label), ZERO)

    def supporting_total(self, label: str) -> Decimal:
        """Supporting entries in the period, without out-of-period entries (effects carry those)."""
        return sum((self.amount(e) for e in self.supporting(label) if e not in self.moved), ZERO)

    def labels_claiming(self, entry_id: str) -> list[str]:
        return [lbl for lbl in self.labels if entry_id in self.claimed.get(lbl, [])]

    def impact_of_removing(self, entry_ids: Iterable[str]) -> dict[str, Decimal]:
        ids = set(entry_ids)
        return {lbl: -sum((self.amount(e) for e in self.claimed.get(lbl, []) if e in ids), ZERO) for lbl in self.labels}

    # -- documents ---------------------------------------------------------

    def evidence_docs(self) -> list[str]:
        """Documents that are evidence about this adjustment's own items: cited by management,
        stating a reference management named, or tied to an entry it still claims."""
        own = set(self.in_play_ids())
        return sorted(
            d
            for d, info in self.doc_links.items()
            if info.cited or info.referenced or any(e in own for e in info.entry_basis)
        )

    def entry_docs(self, entry_id: str) -> list[str]:
        return sorted(d for d, info in self.doc_links.items() if entry_id in info.entry_basis)

    def support_docs(self, entry_id: str) -> list[str]:
        """Documents that evidence an entry. The company's own emails and memos are management
        representations, not documentary support, so they do not count (SPEC §5.4 NO_DOCUMENT_SUPPORT)."""
        return [
            d
            for d in self.entry_docs(entry_id)
            if (self.index.facts[d].doc_type if d in self.index.facts else "other").strip().lower()
            not in CORRESPONDENCE_DOC_TYPES
        ]

    def entry_docs_by_basis(self, entry_id: str, bases: Iterable[str]) -> list[str]:
        wanted = set(bases)
        return sorted(d for d, info in self.doc_links.items() if info.entry_basis.get(entry_id) in wanted)

    def associate(self, doc_id: str, entry_id: str, basis: str, weight: float, reason: str) -> None:
        info = self.doc_links.setdefault(doc_id, DocLinkInfo(doc_id=doc_id))
        if entry_id in info.entry_basis:
            return
        info.entry_basis[entry_id] = basis
        if reason and reason not in info.reasons:
            info.reasons.append(reason)
            info.score += weight

    def groups_for_doc(self, doc_id: str) -> list[str]:
        """Groups a document speaks to.

        Entry-specific ties (doc number, amount, stated total) and a shared
        matter / contract reference come first. Only when there are none does a
        party-name match count, because one vendor can bill several matters.
        """
        idx = self.index
        dl = self.doc_links.get(doc_id)
        refs = idx.doc_refs.get(doc_id, frozenset())
        specific: list[str] = []
        for g, members in self.groups.items():
            tied = dl is not None and any(dl.entry_basis.get(e) in _SPECIFIC_BASES for e in members)
            if tied or (self.group_ref.get(g) and self.group_ref[g] in refs):
                specific.append(g)
        if specific:
            return specific
        cp = idx.doc_cp.get(doc_id, frozenset())
        if not cp:
            return []
        return [g for g, members in self.groups.items() if any(names_match(idx.by_id[e].cp_tokens, cp) for e in members)]

    # -- mutation ----------------------------------------------------------

    def remove(
        self, entry_ids: Iterable[str], code: FlagCode, note: str, source: str = "code", doc_ids: Iterable[str] = ()
    ) -> list[str]:
        newly: list[str] = []
        for e in self.index.sort_ids(entry_ids):
            if e not in self.removals:
                self.removals[e] = Removal(code=code, note=note, source=source, doc_ids=sorted(set(doc_ids)))
                newly.append(e)
        return newly

    def add_flag(self, flag: Flag) -> None:
        key = (flag.code, flag.period_label, tuple(flag.entry_ids), tuple(flag.doc_ids), flag.message)
        for f in self.flags:
            if (f.code, f.period_label, tuple(f.entry_ids), tuple(f.doc_ids), f.message) == key:
                return
        self.flags.append(flag)

    def drop_flags(self, code: FlagCode, label: Optional[str] = None) -> None:
        self.flags = [f for f in self.flags if not (f.code == code and (label is None or f.period_label == label))]

    def has_flag(self, *codes: FlagCode) -> bool:
        return any(f.code in codes for f in self.flags)

    def add_context_link(self, entry_id: str, score: float, reason: str) -> None:
        link = self.links.get(entry_id)
        if link is None:
            info = self.index.by_id[entry_id]
            self.links[entry_id] = LinkInfo(
                entry_id=entry_id, score=round(score, 2), reasons=[reason], group=_group_display(info), context=True
            )
        elif reason not in link.reasons:
            link.reasons.append(reason)

    def add_judgment(self, text: str, key: str = "") -> None:
        """One judgment per topic: a later challenge on the same topic (``key``) does not repeat it."""
        key = key or text
        if text and key not in self._judgment_keys:
            self._judgment_keys.add(key)
            self.judgments.append(text)

    def add_fact(self, fact: Fact, key: str = "") -> None:
        """One fact per topic (``key``, e.g. a document): later evidence on it adds quotes, not lines."""
        if not key:
            if all(f.text != fact.text for f in self.facts):
                self.facts.append(fact)
            return
        if key not in self._fact_keys:
            self._fact_keys[key] = len(self.facts)
            self.facts.append(fact)
            return
        cur = self.facts[self._fact_keys[key]]
        quotes = list(cur.quotes)
        for q in fact.quotes:
            if len(quotes) < 3 and all((q.page, q.quote) != (x.page, x.quote) for x in quotes):
                quotes.append(q)
        ids = self.index.sort_ids(list(cur.entry_ids) + list(fact.entry_ids))
        self.facts[self._fact_keys[key]] = cur.model_copy(update={"quotes": quotes, "entry_ids": ids})

    # -- descriptions (for flag messages and questions) --------------------

    def describe(self, entry_id: str) -> str:
        """'Bill MF-7710-09 (Marlow & Finch LLP, Sep 2025, 8,000; memo cites Matter 7710)'."""
        info = self.index.by_id.get(entry_id)
        if info is None:
            return entry_id
        e = info.entry
        head = f"{e.txn_type or 'Doc'} {e.doc_number}" if e.doc_number else f"GL row {e.source_row}"
        tail = f"; memo cites {info.memo_ref}" if info.memo_ref else ""
        return f"{head} ({e.counterparty or e.account_name}, {month_label(info.month)}, {money(info.amount)}{tail})"

    def entry_ref(self, entry_id: str) -> str:
        """'Bill MF-7710-09 (Marlow & Finch LLP, Sep 2025)': enough to find the entry, without its amount."""
        info = self.index.by_id.get(entry_id)
        if info is None:
            return entry_id
        e = info.entry
        head = f"{e.txn_type or 'Doc'} {e.doc_number}" if e.doc_number else f"GL row {e.source_row}"
        who = e.counterparty or f"{e.account} {e.account_name}"
        return f"{head} ({who}, {month_label(info.month)})"

    def items_text(self, entry_ids: Iterable[str], limit: int = 2) -> str:
        """A compact name for a set of entries: its group when the label is short, else the entries."""
        ids = self.index.sort_ids(entry_ids)
        by_group: dict[str, list[str]] = {}
        for e in ids:
            by_group.setdefault(self.group_of.get(e) or self.entry_ref(e), []).append(e)
        names: list[str] = []
        for g, members in by_group.items():
            label = short_label(g)
            if len(label) <= _SHORT_LABEL:
                names.append(label)
            elif len(members) == 1:
                names.append(self.entry_ref(members[0]))
            else:
                who = g.split(" · ")[0]
                names.append(f"{who} ({entries_word(len(members))}, {month_span(self.index.by_id[e].month for e in members)})")
        return join_limited(names, limit)

    def describe_many(self, entry_ids: Iterable[str], limit: int = 3) -> str:
        ids = self.index.sort_ids(entry_ids)
        text = "; ".join(self.describe(e) for e in ids[:limit])
        return text + (f"; and {len(ids) - limit} more" if len(ids) > limit else "")

    def describe_groups(self, entry_ids: Iterable[str], limit: int = 3) -> str:
        """'Marlow & Finch LLP · Matter 3002 (18 entries, Jan 2025–Jun 2026, 22,000)'."""
        by_group: dict[str, list[str]] = {}
        for e in self.index.sort_ids(entry_ids):
            by_group.setdefault(self.group_of.get(e) or _group_display(self.index.by_id[e]), []).append(e)
        parts = []
        for g, ids in list(by_group.items())[:limit]:
            total = sum((self.amount(e) for e in ids), ZERO)
            span = month_span(self.index.by_id[e].month for e in ids)
            parts.append(f"{g} ({len(ids)} entr{'y' if len(ids) == 1 else 'ies'}, {span}, {money(total)})")
        more = len(by_group) - limit
        return "; ".join(parts) + (f"; and {more} more group(s)" if more > 0 else "")

    # -- output ------------------------------------------------------------

    def gl_links(self) -> list[GLLink]:
        claimed = set(self.claimed_ids())
        out: list[GLLink] = []
        for eid in self.index.sort_ids(self.links):
            link = self.links[eid]
            info = self.index.by_id[eid]
            reasons = list(link.reasons)
            removal = self.removals.get(eid)
            if removal is not None:
                reasons.append(f"Removed ({removal.code.value}): {removal.note}")
            elif eid in claimed:
                reasons.append("Claimed in " + ", ".join(self.labels_claiming(eid)))
            elif not link.context:
                reasons.append(self._context_reason(info))
            out.append(
                GLLink(
                    entry_id=eid,
                    period=info.month,
                    amount=fmt(info.amount),
                    score=round(link.score, 2),
                    reasons=reasons,
                    group=link.group,
                    supports_claim=eid in claimed and removal is None,
                    doc_ids=self.entry_docs(eid),
                )
            )
        return out

    def _context_reason(self, info: EntryInfo) -> str:
        in_labels = self.index.labels_of(info.month)
        claimed_in = [lbl for lbl in in_labels if self.claim(lbl) != 0]
        if not claimed_in:
            where = ", ".join(in_labels) if in_labels else "the months outside the analysis periods"
            return f"Context only: no claim in {where}"
        return "Context only: not needed to tie the claim in " + ", ".join(claimed_in)

    def doc_link_models(self) -> list[DocLink]:
        out: list[DocLink] = []
        for doc_id, info in self.doc_links.items():
            if not info.prelinked and not info.entry_basis:
                continue
            facts = self.index.facts.get(doc_id)
            out.append(
                DocLink(
                    doc_id=doc_id,
                    relation=info.relation or _default_relation(facts, info),
                    entry_ids=self.index.sort_ids(info.entry_basis),
                    score=round(info.score, 2),
                    reasons=list(info.reasons),
                    quotes=_doc_quotes(facts, self, info),
                )
            )
        out.sort(key=lambda d: (-d.score, d.doc_id))
        return out


def _default_relation(facts: Optional[DocFacts], info: DocLinkInfo) -> str:
    doc_type = (facts.doc_type if facts else "other").lower()
    if doc_type == "invoice" or "number" in info.entry_basis.values():
        return "invoice_for_entry"
    if doc_type in AGREEMENT_DOC_TYPES:
        return "agreement"
    if doc_type in CORRESPONDENCE_DOC_TYPES:
        return "correspondence"
    return "other"


_MAX_DOC_QUOTES = 4


def _doc_quotes(facts: Optional[DocFacts], trace: AdjustmentTrace, info: DocLinkInfo) -> list[EvidenceQuote]:
    """The quotes a reviewer needs from a linked document: amounts that tie to the
    linked entries (singly or in total), then terms, then key statements."""
    if facts is None:
        return []
    ids = [e for e in info.entry_basis if e in trace.index.by_id]
    targets = {abs(trace.amount(e)) for e in ids}
    targets.add(abs(sum((trace.amount(e) for e in ids), ZERO)))
    for g in {trace.group_of.get(e, "") for e in ids}:
        targets.add(abs(sum((trace.amount(e) for e in ids if trace.group_of.get(e, "") == g), ZERO)))
    tol = trace.index.tolerance
    picked: list[EvidenceQuote] = []

    def add(q: EvidenceQuote) -> None:
        if len(picked) < _MAX_DOC_QUOTES and all(q.quote != p.quote or q.page != p.page for p in picked):
            picked.append(q)

    for a in facts.amounts:
        try:
            amt = abs(D(a.amount))
        except (ValueError, ArithmeticError):
            continue
        if any(abs(amt - x) <= tol for x in targets):
            add(a.quote)
    for t in facts.terms:
        add(t.quote)
    for q in facts.key_statements:
        add(q)
    return picked


_DISPLAY_SEP = re.compile(r"\s*[-–—:|,/]+\s*(?=[-–—:|,/]|$)|^\s*[-–—:|,/]+\s*")


def memo_display(memo: str) -> str:
    """The memo as written, without dates, amounts, and invoice numbers: 'Club dues - J. Varga'."""
    kept: list[str] = []
    reopen = False
    for tok in (memo or "").split():
        bare = tok.strip("()[]{}.,;:#").lower()
        if any(c.isdigit() for c in tok) or bare in _MONTH_WORDS:
            # Keep the bracket a dropped "(3" opened, so "(3 FTE)" reads "(FTE)".
            reopen = reopen or (tok.startswith("(") and not tok.endswith(")"))
            continue
        if reopen:
            tok, reopen = "(" + tok, False
        kept.append(tok)
    text = " ".join(kept)
    for _ in range(3):
        text = _DISPLAY_SEP.sub("", text).strip()
    if text.count("(") > text.count(")"):
        text += ")"
    # A bracket left holding only a filler word ("(inv 25-0212)" -> "(inv)") says nothing.
    return re.sub(r"\s*\((?:inv|invoice|ref|no|#|pmt|payment)?\.?\)", "", text, flags=re.IGNORECASE).strip()


_SHORT_LABEL = 70


def short_label(group: str) -> str:
    """A group label without an account-number prefix ('5400 Inventory ... · Year-end count' -> 'Year-end count')."""
    who, sep, what = group.partition(" · ")
    if sep and who[:1].isdigit() and what:
        return what
    return group


def _group_display(info: EntryInfo, ref_display: str = "") -> str:
    # Journal entries often have no party; the account says more than "no counterparty".
    who = info.entry.counterparty.strip() or f"{info.entry.account} {info.entry.account_name}"
    what = ref_display or memo_display(info.entry.memo) or info.entry.account_name
    return f"{who} · {what}"


# ---------------------------------------------------------------------------
# Subset search (SPEC §5.3)
# ---------------------------------------------------------------------------


def _half_sums(items: Sequence[tuple[int, int, int]]) -> dict[int, tuple[int, int, int]]:
    """Every subset of ``items`` keyed by sum, keeping the best (weight, -score, -mask).

    Item i sets bit (len - 1 - i), so between equally good subsets the larger
    mask is the one holding the earliest items.
    """
    h = len(items)
    subsets: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]
    for i, (value, weight, score) in enumerate(items):
        bit = 1 << (h - 1 - i)
        subsets += [(s + value, w + weight, sc + score, m | bit) for s, w, sc, m in subsets]
    best: dict[int, tuple[int, int, int]] = {}
    for s, w, sc, m in subsets:
        key = (w, -sc, -m)
        cur = best.get(s)
        if cur is None or key < cur:
            best[s] = key
    return best


def find_subset(
    values: Sequence[int],
    target: int,
    tolerance: int = 0,
    *,
    weights: Optional[Sequence[int]] = None,
    scores: Optional[Sequence[int]] = None,
    max_items: int = MAX_SUBSET_ITEMS,
) -> Optional[list[int]]:
    """Indices of the non-empty subset whose sum is closest to ``target``, within ``tolerance``.

    Values are integer cents. Ranking: exact before approximate, then the
    smallest total weight (entries count as 1; a group weighs its entry
    count), then the highest total score, then the earliest items. The search
    is exact meet-in-the-middle over at most ``max_items`` items; with more,
    only the ``max_items`` highest-scoring items are considered.
    """
    n = len(values)
    weights = list(weights) if weights is not None else [1] * n
    scores = list(scores) if scores is not None else [0] * n
    order = list(range(n))
    if n > max_items:
        order = sorted(order, key=lambda i: (-scores[i], i))[:max_items]
        order.sort()
    items = [(values[i], weights[i], scores[i]) for i in order]
    mid = len(items) // 2
    n_right = len(items) - mid
    left, right = _half_sums(items[:mid]), _half_sums(items[mid:])
    right_sums = sorted(right)
    best: Optional[tuple[tuple[int, int, int, int], int]] = None
    for lsum, (lw, lsc, lm) in left.items():
        lo = bisect_left(right_sums, target - tolerance - lsum)
        hi = bisect_right(right_sums, target + tolerance - lsum)
        for rsum in right_sums[lo:hi]:
            rw, rsc, rm = right[rsum]
            mask = ((-lm) << n_right) | -rm
            if mask == 0:
                continue
            key = (abs(lsum + rsum - target), lw + rw, lsc + rsc, -mask)
            if best is None or key < best[0]:
                best = (key, mask)
    if best is None:
        return None
    mask = best[1]
    total = len(items)
    return [order[i] for i in range(total) if mask >> (total - 1 - i) & 1]


@dataclass(frozen=True)
class ClaimFit:
    """The claimed set chosen by ``fit_claim``."""

    indices: list[int]  # chosen candidates, ascending
    diff: int  # |sum - target| in cents; 0 is an exact fit
    split_groups: int  # groups the fit takes only part of
    cited: int  # chosen entries that a document cited in management's support refs links to
    ties: int  # fits ranked equal before the earliest-entries rule decided (1 = unique)
    bounded: bool  # more candidates than the search could consider


# A half-table row: (-split groups, cited entries, entry mask, number of subsets with that rank).
_Row = list


def _merge_options(table: dict[tuple[int, int], _Row], options: dict[tuple[int, int], _Row]) -> dict[tuple[int, int], _Row]:
    """Combine every row of ``table`` with every option of the next unit, keeping per
    (sum, straddle state) the best rank and how many subsets reach it.

    Every rank component is additive (split count, cited count, and a mask of
    disjoint bits), so keeping only the best row per sum loses nothing: adding the
    same later option to two rows preserves their order.
    """
    out: dict[tuple[int, int], _Row] = {}
    for (s, st), (ns, c, m, n) in table.items():
        for (v, ost), (ons, oc, om, on) in options.items():
            key = (s + v, st or ost)
            rank = (ns + ons, c + oc)
            cur = out.get(key)
            if cur is None or rank > (cur[0], cur[1]):
                out[key] = [rank[0], rank[1], m | om, n * on]
            elif rank == (cur[0], cur[1]):
                cur[3] += n * on
                if m | om > cur[2]:
                    cur[2] = m | om
    return out


def _unit_options(
    members: Sequence[int], values: Sequence[int], cited: Sequence[bool], bits: Sequence[int], whole_ok: bool, straddle: bool
) -> dict[tuple[int, int], _Row]:
    """Every subset of one group's members in one half, reduced to (sum, state) -> best rank.

    For a group wholly inside the half, taking some but not all members splits it.
    For the one group that straddles the halves the split is decided when the
    halves are joined, so each side only records none (0), part (1), or all (2).
    """
    subsets: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]  # (sum, count, cited, mask)
    for i in members:
        subsets += [(s + values[i], k + 1, c + int(cited[i]), m | bits[i]) for s, k, c, m in subsets]
    out: dict[tuple[int, int], _Row] = {}
    size = len(members)
    for s, k, c, m in subsets:
        if straddle:
            state, split = (0 if k == 0 else 2 if k == size else 1), 0
        else:
            state, split = 0, int(0 < k and not (k == size and whole_ok))
        key = (s, state)
        cur = out.get(key)
        rank = (-split, c)
        if cur is None or rank > (cur[0], cur[1]):
            out[key] = [rank[0], rank[1], m, 1]
        elif rank == (cur[0], cur[1]):
            cur[3] += 1
            if m > cur[2]:
                cur[2] = m
    return out


def _half_table(units: Sequence[dict[tuple[int, int], _Row]]) -> dict[tuple[int, int], _Row]:
    table: dict[tuple[int, int], _Row] = {(0, 0): [0, 0, 0, 1]}
    for options in units:
        table = _merge_options(table, options)
    return table


def _join_halves(
    left: dict[tuple[int, int], _Row],
    right: dict[tuple[int, int], _Row],
    target: int,
    tolerance: int,
    straddle_whole_ok: bool,
) -> Optional[tuple[tuple[int, int, int], int, int]]:
    """Best ((-diff, -split, cited), mask, ties) over every pair of half subsets within tolerance."""
    by_state: dict[int, tuple[list[int], list[_Row]]] = {}
    for (s, st), row in sorted(right.items()):
        sums, rows = by_state.setdefault(st, ([], []))
        sums.append(s)
        rows.append(row)
    best: Optional[tuple[int, int, int]] = None
    best_mask, ties = 0, 0
    for (ls, lst), (lns, lc, lm, ln) in left.items():
        for rst, (sums, rows) in by_state.items():
            lo = bisect_left(sums, target - tolerance - ls)
            hi = bisect_right(sums, target + tolerance - ls)
            for k in range(lo, hi):
                rns, rc, rm, rn = rows[k]
                mask = lm | rm
                if mask == 0:
                    continue
                # The straddling group is whole only when both halves take all of it.
                straddle_split = int((lst, rst) != (0, 0) and not ((lst, rst) == (2, 2) and straddle_whole_ok))
                rank = (-abs(ls + sums[k] - target), lns + rns - straddle_split, lc + rc)
                if best is None or rank > best:
                    best, best_mask, ties = rank, mask, ln * rn
                elif rank == best:
                    ties += ln * rn
                    if mask > best_mask:
                        best_mask = mask
    if best is None:
        return None
    return best, best_mask, ties


def fit_claim(
    values: Sequence[int],
    target: int,
    tolerance: int,
    groups: Sequence[str],
    cited: Sequence[bool],
    *,
    scores: Optional[Sequence[float]] = None,
    max_items: int = MAX_SUBSET_ITEMS,
) -> Optional[ClaimFit]:
    """The claimed set for one period (SPEC §5.3), or None when no subset ties.

    ``values`` are EBITDA-signed cents in date order (index = date rank). Among
    fits within ``tolerance`` the ranking is: exact before approximate; then the
    most whole groups, read as the fewest groups the fit splits (a claim is
    normally whole billing streams, not entries picked out of one); then the
    most entries that a document cited in management's support references links
    to; then the earliest entries. ``ties`` counts the fits that were still level
    when the earliest-entries rule decided, so the caller can record the ambiguity.

    The search is exact meet-in-the-middle over at most ``max_items`` entries
    (the strongest links when there are more). With more candidates a second
    search over whole groups keeps whole-group fits reachable; tie counts are
    then approximate.
    """
    n = len(values)
    if n == 0:
        return None
    scores = list(scores) if scores is not None else [0.0] * n
    bits = [1 << (n - 1 - i) for i in range(n)]
    group_members: dict[str, list[int]] = {}
    for i, g in enumerate(groups):
        group_members.setdefault(g, []).append(i)
    kept = list(range(n))
    bounded = n > max_items
    if bounded:
        kept = sorted(sorted(range(n), key=lambda i: (-scores[i], i))[:max_items])
    kept_set = set(kept)
    whole_ok = {g: all(i in kept_set for i in members) for g, members in group_members.items()}

    # Entry-level search: halves cut along group boundaries so wholeness stays additive;
    # at most one group straddles the cut.
    order = sorted(kept, key=lambda i: (min(j for j in group_members[groups[i]] if j in kept_set), i))
    cut = len(order) // 2
    left_items, right_items = order[:cut], order[cut:]
    straddler = groups[order[cut - 1]] if 0 < cut < len(order) and groups[order[cut - 1]] == groups[order[cut]] else None

    def units(items: list[int]) -> list[dict[tuple[int, int], _Row]]:
        by_group: dict[str, list[int]] = {}
        for i in items:
            by_group.setdefault(groups[i], []).append(i)
        return [
            _unit_options(members, values, cited, bits, whole_ok[g] and len(members) == len(group_members[g]), g == straddler)
            for g, members in by_group.items()
        ]

    candidates: list[tuple[tuple[int, int, int], int, int]] = []
    found = _join_halves(
        _half_table(units(left_items)), _half_table(units(right_items)), target, tolerance,
        straddler is not None and whole_ok[straddler],
    )
    if found is not None:
        candidates.append(found)
    if bounded:
        # Whole groups only, over every group (the strongest 30 groups when there are more).
        ranked = sorted(group_members, key=lambda g: (-max(scores[i] for i in group_members[g]), group_members[g][0]))
        chosen_groups = sorted(ranked[:max_items], key=lambda g: group_members[g][0])

        def whole(g: str) -> dict[tuple[int, int], _Row]:
            members = group_members[g]
            mask = 0
            for i in members:
                mask |= bits[i]
            return {
                (0, 0): [0, 0, 0, 1],
                (sum(values[i] for i in members), 0): [0, sum(int(cited[i]) for i in members), mask, 1],
            }

        half = len(chosen_groups) // 2
        found = _join_halves(
            _half_table([whole(g) for g in chosen_groups[:half]]),
            _half_table([whole(g) for g in chosen_groups[half:]]),
            target, tolerance, False,
        )
        if found is not None:
            candidates.append(found)
    if not candidates:
        return None
    best_rank = max(c[0] for c in candidates)
    at_best = [c for c in candidates if c[0] == best_rank]
    mask = max(c[1] for c in at_best)
    # A whole-group fit can be found by both searches; the group search sees every such fit.
    ties = at_best[-1][2] if len(at_best) > 1 and best_rank[1] == 0 else sum(c[2] for c in at_best)
    return ClaimFit(
        indices=[i for i in range(n) if mask & bits[i]],
        diff=-best_rank[0],
        split_groups=-best_rank[1],
        cited=best_rank[2],
        ties=max(ties, 1),
        bounded=bounded,
    )


# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------


_MGMT = "named by management"


@dataclass
class _LinkContext:
    accounts: frozenset[str]
    intent_names: list[tuple[str, frozenset[str]]]
    doc_names: list[tuple[str, str, frozenset[str]]]  # (doc_id, party name, tokens)
    keywords: list[str]
    refs: dict[str, tuple[str, str]]  # normalized ref -> (display, source)
    doc_numbers: dict[str, list[str]]  # normalized ref -> related doc ids stating it
    prelinked: frozenset[str]
    cited: frozenset[str]


def support_ref_matches(ref: str, doc: SourceDocument, facts: Optional[DocFacts] = None) -> bool:
    """Does management's support reference ('DR 4.2', a file name, an invoice number) cite this document?"""
    ref = (ref or "").strip()
    if not ref:
        return False
    parts = [doc.doc_id] + list(PurePosixPath(doc.relpath.replace("\\", "/")).parts)
    m = _INDEX_REF.match(ref)
    if m:
        idx = m.group(1)
        for part in parts:
            if part.startswith(idx) and (len(part) == len(idx) or part[len(idx)] in " ._-"):
                return True
        return False
    n = norm_text(ref)
    if len(n) >= 4:
        hay = [norm_text(p) for p in parts] + ([norm_text(facts.title)] if facts and facts.title else [])
        if any(n in h for h in hay):
            return True
    tokens = ref_tokens(ref)
    if tokens and facts is not None:
        refs: set[str] = set()
        for r in facts.reference_numbers:
            refs |= ref_tokens(r)
        return bool(tokens & refs)
    return False


def _prelink_documents(t: AdjustmentTrace) -> None:
    """Documents that relate to the adjustment before any GL entry is considered."""
    idx, adj, intent = t.index, t.adj, t.intent
    intent_names = [(n, name_tokens(n)) for n in intent.counterparties if name_tokens(n)]
    intent_refs: set[str] = set()
    for r in intent.reference_numbers:
        intent_refs |= ref_tokens(r)
    keywords = keyword_list(intent.keywords)
    for doc_id in sorted(idx.docs):
        doc, facts = idx.docs[doc_id], idx.facts[doc_id]
        score, reasons = 0.0, []
        cited = [r for r in adj.support_refs if support_ref_matches(r, doc, facts)]
        if cited:
            score += DW_SUPPORT_REF
            reasons.append(f"Cited by management's support reference '{cited[0]}'")
        cp = idx.doc_cp[doc_id]
        party: frozenset[str] = frozenset()
        for name, toks in intent_names:
            if names_match(cp, toks):
                score += DW_COUNTERPARTY
                reasons.append(f"Counterparty '{facts.counterparty}' matches '{name}' named by management")
                party = cp | toks
                break
        shared = sorted(intent_refs & idx.doc_refs[doc_id])
        if shared:
            score += DW_REFERENCE
            reasons.append(f"States reference {', '.join(shared)} named by management")
        title_norm = norm_text(f"{facts.title} {doc_id}")
        hits = keyword_hits(keywords, title_norm, frozenset(title_norm.split()), party)
        if hits:
            score += min(DW_TITLE_KEYWORD * len(hits), DW_TITLE_KEYWORD_CAP)
            reasons.append("Title mentions " + ", ".join(f"'{h}'" for h in hits))
        if score >= DOC_LINK_THRESHOLD:
            t.doc_links[doc_id] = DocLinkInfo(
                doc_id=doc_id, score=score, reasons=reasons, prelinked=True, cited=bool(cited), referenced=bool(shared)
            )


def _link_context(t: AdjustmentTrace) -> _LinkContext:
    idx, intent = t.index, t.intent
    refs: dict[str, tuple[str, str]] = {}
    for r in intent.reference_numbers:
        for n in sorted(ref_tokens(r)):
            refs.setdefault(n, (r.strip(), _MGMT))
    doc_names: list[tuple[str, str, frozenset[str]]] = []
    doc_numbers: dict[str, list[str]] = {}
    for doc_id in sorted(t.doc_links):
        facts = idx.facts[doc_id]
        if idx.doc_cp[doc_id]:
            doc_names.append((doc_id, facts.counterparty or "", idx.doc_cp[doc_id]))
        for raw in facts.reference_numbers:
            for n in sorted(ref_tokens(raw)):
                refs.setdefault(n, (raw.strip(), f"from {doc_id}"))
                if doc_id not in doc_numbers.setdefault(n, []):
                    doc_numbers[n].append(doc_id)
    return _LinkContext(
        accounts=frozenset(t.adj.gl_accounts),
        intent_names=[(n, name_tokens(n)) for n in intent.counterparties if name_tokens(n)],
        doc_names=doc_names,
        keywords=keyword_list(intent.keywords),
        refs=refs,
        doc_numbers=doc_numbers,
        prelinked=frozenset(t.doc_links),
        cited=frozenset(d for d, info in t.doc_links.items() if info.cited),
    )


def _score_entry(info: EntryInfo, ctx: _LinkContext, idx: DealIndex) -> tuple[float, list[str]]:
    e = info.entry
    score, reasons = 0.0, []
    if e.account in ctx.accounts:
        score += W_ACCOUNT
        reasons.append(f"Account {e.account} {e.account_name} is on management's schedule")

    cp_reason = ""
    party: frozenset[str] = frozenset()
    for name, toks in ctx.intent_names:
        if names_match(info.cp_tokens, toks):
            same = norm_text(e.counterparty) == norm_text(name)
            cp_reason = f"Counterparty {e.counterparty} " + ("is named by management" if same else f"matches {name}, named by management")
        elif name_in_text(toks, info.memo_tokens):
            cp_reason = f"Memo names {name}, named by management"
        if cp_reason:
            party = toks | info.cp_tokens
            break
    if not cp_reason:
        for doc_id, name, toks in ctx.doc_names:
            if names_match(info.cp_tokens, toks):
                cp_reason = f"Counterparty {e.counterparty} is the party to {doc_id}"
                party = toks | info.cp_tokens
                break
    if cp_reason:
        score += W_COUNTERPARTY
        reasons.append(cp_reason)

    hits = keyword_hits(ctx.keywords, info.memo_norm, info.memo_tokens, party)
    if hits:
        score += W_KEYWORD + min(W_KEYWORD_EXTRA * (len(hits) - 1), W_KEYWORD_EXTRA_CAP)
        reasons.append("Memo mentions " + ", ".join(f"'{h}'" for h in hits))

    # A document stating the entry's own doc number is the Document signal, not a Reference.
    ref_reason = ""
    for n in sorted(info.refs):
        hit = ctx.refs.get(n)
        if hit is None or (n == info.doc_number and hit[1] != _MGMT):
            continue
        # hit[1] is "named by management" or "from <doc id>"
        ref_reason = f"Memo cites {hit[0]}, {hit[1]}" if hit[1] == _MGMT else f"Memo cites {hit[0]}, stated in {hit[1][5:]}"
        break
    if not ref_reason and info.doc_number:
        hit = ctx.refs.get(info.doc_number)
        if hit is not None and hit[1] == _MGMT:
            ref_reason = f"Doc # {e.doc_number} is named by management"
    if ref_reason:
        score += W_REFERENCE
        reasons.append(ref_reason)

    doc_reason = ""
    if info.doc_number and info.doc_number in ctx.doc_numbers:
        doc_reason = f"Doc # {e.doc_number} appears in {ctx.doc_numbers[info.doc_number][0]}"
    else:
        for doc_id, _amt in idx.docs_with_amount(info.amount):
            if doc_id not in ctx.prelinked:
                continue
            if names_match(info.cp_tokens, idx.doc_cp[doc_id]) or (not info.cp_tokens and doc_id in ctx.cited):
                doc_reason = f"{doc_id} states this amount ({money(abs(info.amount))}) for the same party"
                break
    if doc_reason:
        score += W_DOCUMENT
        reasons.append(doc_reason)
    return score, reasons


def _assign_groups(t: AdjustmentTrace, ctx: _LinkContext) -> None:
    """Group linked entries by counterparty plus memo theme; a document reference wins over the theme."""
    idx = t.index
    ref_freq: dict[str, int] = {}
    own_numbers = {idx.by_id[e].doc_number for e in t.candidates}
    for e in t.candidates:
        for n in idx.by_id[e].refs:
            if n in ctx.refs and n not in own_numbers:
                ref_freq[n] = ref_freq.get(n, 0) + 1
    shared_refs = {n for n, c in ref_freq.items() if c >= 2}

    keys: dict[str, str] = {}  # normalized key -> display label (first entry wins)
    for e in t.candidates:
        info = idx.by_id[e]
        cp_key = " ".join(sorted(info.cp_tokens)) or "-"
        ref, ref_display = info.memo_ref_norm, info.memo_ref
        if not ref:
            found = sorted((n for n in info.refs if n in shared_refs), key=lambda n: (-ref_freq[n], n))
            if found:
                ref, ref_display = found[0], f"ref {ctx.refs[found[0]][0]}"
        key = f"{cp_key}|ref:{ref}" if ref else f"{cp_key}|{' '.join(info.theme) or info.entry.account}"
        if key not in keys:
            label = _group_display(info, ref_display)
            n = 2
            while label in keys.values():
                label = f"{_group_display(info, ref_display)} ({n})"
                n += 1
            keys[key] = label
        label = keys[key]
        t.groups.setdefault(label, []).append(e)
        t.group_of[e] = label
        t.links[e].group = label
        if ref:
            t.group_ref[label] = ref


# ---------------------------------------------------------------------------
# Claimed-set fit
# ---------------------------------------------------------------------------


def _fit_claims(t: AdjustmentTrace) -> None:
    idx = t.index
    tol = idx.tolerance
    cands_by_label = {
        lbl: [e for e in t.candidates if idx.by_id[e].month in idx.label_months[lbl]] for lbl in t.claimed_labels()
    }
    if t.is_normalization:
        # The claim is actual cost in the named accounts less a normalized level (SPEC §5.4),
        # so every linked entry in those accounts is actual cost.
        accounts = set(t.adj.gl_accounts)
        for lbl, cands in cands_by_label.items():
            cands = [e for e in cands if not accounts or idx.by_id[e].entry.account in accounts]
            t.claimed[lbl] = list(cands)
            t.fits[lbl] = PeriodFit(lbl, t.claim(lbl), sum((t.amount(e) for e in cands), ZERO), "normalization")
        return
    pending: list[str] = []
    for lbl, cands in cands_by_label.items():
        total = sum((t.amount(e) for e in cands), ZERO)
        if abs(total - t.claim(lbl)) <= tol:
            t.claimed[lbl] = list(cands)
            t.fits[lbl] = PeriodFit(lbl, t.claim(lbl), total, "all")
        else:
            pending.append(lbl)
    for lbl in pending:
        _fit_one(t, lbl, cands_by_label[lbl])


def _fit_one(t: AdjustmentTrace, label: str, cands: list[str]) -> None:
    idx = t.index
    claim = t.claim(label)
    s = 1 if claim > 0 else -1
    target, tol = cents(abs(claim)), cents(idx.tolerance)
    vals = {e: s * cents(t.amount(e)) for e in cands}
    linked_total = sum((t.amount(e) for e in cands), ZERO)
    fit = PeriodFit(label, claim, linked_total, "all")
    if sum(vals.values()) < target - tol and any(v < 0 for v in vals.values()) and any(v > 0 for v in vals.values()):
        # The claim already exceeds the net activity, so an entry running against it (an
        # insurance credit linked by the claim number) cannot be part of it; it stays context.
        # A claim made only of such entries is kept whole: that is a sign error to flag.
        cands = [e for e in cands if vals[e] > 0]
        vals = {e: vals[e] for e in cands}
    chosen = list(cands)
    if abs(sum(vals.values()) - target) <= tol:
        pass
    elif sum(vals.values()) > target + tol:
        cited = _cited_entries(t, cands)
        found = fit_claim(
            [vals[e] for e in cands],
            target,
            tol,
            [t.group_of[e] for e in cands],
            [e in cited for e in cands],
            scores=[t.links[e].score for e in cands],
        )
        if found is not None:
            chosen = [cands[i] for i in found.indices]
            fit.method = "groups" if found.split_groups == 0 else "entries"
            fit.bounded, fit.ties, fit.cited = found.bounded, found.ties, found.cited
        else:
            fit.bounded = len(cands) > MAX_SUBSET_ITEMS
            elsewhere = _claim_elsewhere(t, label, target, tol, s)
            if elsewhere:
                chosen, fit.method, fit.elsewhere = [], "elsewhere", elsewhere
            else:
                strong = [e for e in cands if t.links[e].score >= STRONG_LINK]
                chosen = strong or list(cands)
                fit.method = "strong"
    elif not cands:
        fit.elsewhere = _claim_elsewhere(t, label, target, tol, s)
    t.claimed[label] = chosen
    t.fits[label] = fit


def _cited_entries(t: AdjustmentTrace, cands: Iterable[str]) -> set[str]:
    """Candidates management itself points to: a document cited in its support references
    states the entry's doc number, or its amount for the same party; or management's
    narrative names the entry's own document number."""
    idx = t.index
    cited_docs = sorted(d for d, info in t.doc_links.items() if info.cited)
    named: set[str] = set()
    for r in t.intent.reference_numbers:
        named |= ref_tokens(r)
    out: set[str] = set()
    for e in cands:
        info = idx.by_id[e]
        if info.doc_number and info.doc_number in named:
            out.add(e)
            continue
        stating = {d for d, _ in idx.docs_with_amount(info.amount)}
        for d in cited_docs:
            if e in idx.doc_entries.get(d, frozenset()):
                out.add(e)
                break
            if d in stating and not (idx.doc_entries.get(d) and e not in idx.doc_entries[d]):
                if not info.cp_tokens or names_match(idx.doc_cp.get(d, frozenset()), info.cp_tokens):
                    out.add(e)
                    break
    return out


def _claim_elsewhere(t: AdjustmentTrace, label: str, target: int, tol: int, s: int) -> list[str]:
    """Linked entries outside the period whose total ties to its claim (whole groups first)."""
    months = t.index.label_months[label]
    outside = [e for e in t.candidates if t.index.by_id[e].month not in months]
    if not outside:
        return []
    group_keys = list(dict.fromkeys(t.group_of[e] for e in outside))
    members = {g: [e for e in outside if t.group_of[e] == g] for g in group_keys}
    pick = find_subset(
        [sum(s * cents(t.amount(e)) for e in members[g]) for g in group_keys],
        target,
        tol,
        weights=[len(members[g]) for g in group_keys],
    )
    if pick is not None:
        return [e for e in outside if t.group_of[e] in {group_keys[i] for i in pick}]
    pick = find_subset([s * cents(t.amount(e)) for e in outside], target, tol)
    return [outside[i] for i in pick] if pick is not None else []


# ---------------------------------------------------------------------------
# Document association (after the fit, anchored on linked entries)
# ---------------------------------------------------------------------------


def _associate_documents(t: AdjustmentTrace) -> None:
    idx = t.index
    prelinked = {d for d, info in t.doc_links.items() if info.prelinked}
    support_docs = {d for d, info in t.doc_links.items() if info.cited}
    amount_hits: dict[str, list[str]] = {}
    # Only claimed entries: documents about context-only activity (prior-year comparables,
    # other vendors' invoices in the same account) are not evidence for this claim.
    claimed = t.claimed_ids()
    for e in claimed:
        info = idx.by_id[e]
        entry = info.entry
        if info.doc_number:
            for doc_id in idx.docs_by_ref.get(info.doc_number, []):
                if e in idx.doc_entries[doc_id]:
                    t.associate(doc_id, e, "number", DW_ENTRY_NUMBER, "States the doc # of linked GL entries")
        for doc_id, _amt in idx.docs_with_amount(info.amount):
            if idx.doc_entries[doc_id] and e not in idx.doc_entries[doc_id]:
                continue  # the document is the invoice for a different entry
            dcp = idx.doc_cp[doc_id]
            if names_match(dcp, info.cp_tokens) or (not info.cp_tokens and doc_id in support_docs):
                amount_hits.setdefault(doc_id, []).append(e)
    # Correspondence that cites a claimed entry's doc number discusses that entry. Short
    # numbers ("1001") also occur in addresses, so only distinctive ones count.
    for e in claimed:
        info = idx.by_id[e]
        if len(info.doc_number) >= _MIN_CITED_NUMBER or (info.doc_number[:1].isalpha() and len(info.doc_number) >= 4):
            for doc_id in idx.docs_by_text_ref.get(info.doc_number, []):
                t.associate(doc_id, e, "mention", DW_ENTRY_NUMBER, f"Mentions doc # {info.entry.doc_number}")
    # One matching entry pins the document to it; a monthly fee matching many entries only supports them.
    for doc_id, hits in amount_hits.items():
        basis = "amount" if len(hits) == 1 else "amount_multi"
        for e in hits:
            t.associate(doc_id, e, basis, DW_ENTRY_AMOUNT, "States the amount of linked GL entries for the same party")
    for e in claimed:
        info = idx.by_id[e]
        entry = info.entry
        if info.cp_tokens:
            for doc_id in sorted(prelinked):
                if name_in_text(info.cp_tokens, idx.doc_text_tokens[doc_id]):
                    t.associate(doc_id, e, "named", DW_ENTRY_NAMED, f"Names {entry.counterparty}")
    # A document stating a group's total (an engagement fee paid in installments) supports every entry in it.
    claimed_set = set(claimed)
    for g, all_members in t.groups.items():
        members = [e for e in all_members if e in claimed_set]
        if not members:
            continue
        # The document may state the whole engagement (all installments) even when only some are claimed.
        totals = {sum((t.amount(e) for e in all_members), ZERO), sum((t.amount(e) for e in members), ZERO)}
        for lbl in t.claimed_labels():
            part = [e for e in members if e in t.claimed.get(lbl, [])]
            if len(part) > 1:
                totals.add(sum((t.amount(e) for e in part), ZERO))
        g_cp = idx.by_id[members[0]].cp_tokens
        for total in sorted(totals):
            if len(all_members) < 2 or total == 0:
                continue
            for doc_id, _amt in idx.docs_with_amount(total):
                if names_match(idx.doc_cp[doc_id], g_cp) or (not g_cp and doc_id in support_docs):
                    for e in members:
                        t.associate(doc_id, e, "group", DW_ENTRY_AMOUNT, f"States the {money(abs(total))} total of {g}")
    # A document for the group's matter / contract (an engagement letter for Matter 7710) supports its entries.
    for g, ref in t.group_ref.items():
        for doc_id in idx.docs_by_ref.get(ref, []):
            dcp = idx.doc_cp[doc_id]
            g_cp = idx.by_id[t.groups[g][0]].cp_tokens
            if dcp and g_cp and not names_match(dcp, g_cp):
                continue
            for e in (x for x in t.groups[g] if x in claimed_set):
                if idx.doc_entries[doc_id] and e not in idx.doc_entries[doc_id]:
                    continue  # another entry's invoice under the same matter is not support for this one
                t.associate(doc_id, e, "reference", DW_ENTRY_NUMBER, f"States reference {ref} of {g}")
    for info in t.doc_links.values():
        n = len(info.entry_basis)
        if n and not info.prelinked:
            info.reasons.append(f"Linked through {n} GL entr{'y' if n == 1 else 'ies'}")


# ---------------------------------------------------------------------------
# Fit flags (SPEC §5.3)
# ---------------------------------------------------------------------------


def _fit_flags(t: AdjustmentTrace) -> None:
    idx = t.index
    if not t.claimed_labels():
        return
    if not t.candidates:
        t.add_flag(
            Flag(
                code=FlagCode.NO_GL_SUPPORT,
                severity=Severity.CRITICAL,
                message=_short_sentence(
                    f"No GL entry links to this adjustment in any period (searched {t.search_terms}), so nothing "
                    "can be carried until management identifies the entries."
                ),
            )
        )
        return
    if t.is_normalization:
        return
    tol = idx.tolerance
    for lbl in t.claimed_labels():
        fit = t.fits[lbl]
        claim = fit.claim
        s = 1 if claim > 0 else -1
        chosen = t.claimed.get(lbl, [])
        traced = t.traced(lbl)
        others = [e for e in t.candidates if idx.by_id[e].month in idx.label_months[lbl] and e not in chosen]
        excess = sum((t.amount(e) for e in others), ZERO)
        if fit.method in ("groups", "entries"):
            groups = list(dict.fromkeys(t.group_of[e] for e in chosen))
            what = t.items_text(chosen, 1) if len(groups) == 1 else f"{len(groups)} groups"
            msg = (
                f"{lbl}: linked GL activity of {money(fit.linked_total)} exceeds the {money(claim)} claim, which ties "
                f"to the cent to {entries_word(len(chosen))} ({what}); the other {money(excess)} is context only."
            )
            span = month_span(idx.by_id[e].month for e in chosen)
            if fit.ties > 1:
                msg += f" {fit.ties:,} fits rank equal, so the earliest entries ({span}) were taken."
                t.add_judgment(
                    f"Which entries make up management's {lbl} claim of {money(claim)}? {fit.ties:,} combinations "
                    f"of the linked entries tie; the tool took the earliest ({span}).",
                    key=f"fit:{lbl}",
                )
            elif fit.bounded:
                msg += f" The search considered the {MAX_SUBSET_ITEMS} strongest links only."
            t.add_flag(
                Flag(
                    code=FlagCode.EXCESS_GL_ACTIVITY,
                    severity=Severity.INFO,
                    message=_short_sentence(msg),
                    period_label=lbl,
                    amount_impact=fmt(excess),
                    entry_ids=idx.sort_ids(others),
                )
            )
        elif fit.method == "strong":
            if s * (traced - claim) > tol:
                t.capped.add(lbl)
                t.add_flag(
                    Flag(
                        code=FlagCode.EXCESS_GL_ACTIVITY,
                        severity=Severity.INFO,
                        message=_short_sentence(
                            f"{lbl}: linked GL activity of {money(fit.linked_total)} exceeds the {money(claim)} claim "
                            f"and no combination of linked entries ties to it. The {entries_word(len(chosen))} with "
                            f"strong links ({money(traced)}) are treated as claimed, capped at the claim."
                        ),
                        period_label=lbl,
                        amount_impact=fmt(traced - claim),
                        entry_ids=idx.sort_ids(chosen),
                    )
                )
                t.add_judgment(
                    f"Which GL entries make up management's {lbl} claim of {money(claim)}? No combination of the "
                    f"linked entries ties to it; the {entries_word(len(chosen))} with strong links total {money(traced)}.",
                    key=f"fit:{lbl}",
                )
                continue
        if s * (claim - traced) > tol:
            gap = traced - claim
            t.add_flag(
                Flag(
                    code=FlagCode.PARTIAL_GL_SUPPORT,
                    severity=Severity.WARNING,
                    message=(
                        f"{lbl}: GL entries linked to this adjustment total {money(traced)} against the "
                        f"{money(claim)} claim, so {money(abs(gap))} of the claim is not found in the GL."
                    ),
                    period_label=lbl,
                    amount_impact=fmt(gap),
                    entry_ids=idx.sort_ids(chosen),
                )
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def trace_adjustment(
    index: DealIndex, adj: AdjustmentClaim, intent: AdjustmentIntent, order: int = 0
) -> AdjustmentTrace:
    """Link, group, and fit one adjustment. Flags: NO_GL_SUPPORT, PARTIAL_GL_SUPPORT, EXCESS_GL_ACTIVITY."""
    t = AdjustmentTrace(adj=adj, intent=intent, order=order, index=index)
    _prelink_documents(t)
    ctx = _link_context(t)
    t.search_terms = _describe_search(t, ctx)
    threshold = LINK_THRESHOLD
    if t.is_pro_forma and not adj.gl_accounts:
        # A savings claim names positions or contracts, not accounts, so it cannot earn the
        # account signal; the bar drops by exactly that weight.
        threshold -= W_ACCOUNT
    for info in index.entries:
        score, reasons = _score_entry(info, ctx, index)
        if score >= threshold:
            t.links[info.entry_id] = LinkInfo(entry_id=info.entry_id, score=round(score, 2), reasons=reasons)
            t.candidates.append(info.entry_id)
    _assign_groups(t, ctx)
    _fit_claims(t)
    _associate_documents(t)
    _fit_flags(t)
    return t


def _describe_search(t: AdjustmentTrace, ctx: _LinkContext) -> str:
    parts = []
    if ctx.accounts:
        parts.append("accounts " + ", ".join(sorted(ctx.accounts)))
    if ctx.intent_names:
        parts.append("parties " + join_limited([n for n, _ in ctx.intent_names], 2))
    if ctx.keywords:
        parts.append("keywords " + join_limited(ctx.keywords, 4))
    refs = [d for d, src in ctx.refs.values() if src == "named by management"]
    if refs:
        parts.append("references " + ", ".join(refs))
    if t.doc_links:
        parts.append(f"{len(t.doc_links)} related document(s)")
    return "; ".join(parts) or "no accounts, parties, keywords, or references"


def month_range_safe(start: Optional[str], end: Optional[str]) -> list[str]:
    """Months covered by an ISO date range; [] when either end is missing or malformed."""
    if not start or not end:
        return []
    s, e = start[:7], end[:7]
    if not (re.match(r"^\d{4}-\d{2}$", s) and re.match(r"^\d{4}-\d{2}$", e)) or s > e:
        return []
    return month_range(s, e)
