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
    EBITDA_EXCLUDED_CLASSES,
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

# The kind of engagement a typed reference names, so that like is compared with like: a document titled
# "Matter 12" is about another matter than bills citing "Matter 2024-07", but a date, a fiscal year, a
# street number or a form number in a title names no engagement at all.
_REF_KINDS = {
    "matter": "matter", "case": "matter", "contract": "contract", "agreement": "contract", "sow": "contract",
    "engagement": "contract", "project": "project", "job": "project", "work order": "project", "claim": "claim",
    "policy": "policy", "po": "po",
}
_STREET_AFTER = re.compile(
    r"^\s+(?:[A-Z][a-z]+\s+){0,2}(?:road|rd|street|st|avenue|ave|boulevard|blvd|drive|dr|lane|ln|way|parkway|pkwy|court"
    r"|ct|place|pl|highway|hwy|suite|ste|circle|cir|terrace|trail|loop)\b\.?",
    re.IGNORECASE,
)


def ref_kind(label: str) -> str:
    return _REF_KINDS.get(" ".join(label.lower().split()), "")


def typed_refs(text: Optional[str]) -> frozenset[tuple[str, str]]:
    """(kind, normalized reference) for each typed reference in a text ("Matter 7710" -> ('matter', '7710'))."""
    out: set[tuple[str, str]] = set()
    text = text or ""
    for m in _MEMO_REF.finditer(text):
        n = ref_norm(m.group(2))
        if not _valid_ref(n) or _STREET_AFTER.match(text[m.end() :]):
            continue
        kind = ref_kind(m.group(1))
        if kind:
            out.add((kind, n))
    return frozenset(out)


_LEGAL_TOKENS = frozenset(
    "llc inc ltd limited llp lllp lp co corp corporation company pllc pc plc pty gmbh bv nv ag sarl srl the and of na dba"
    .split()
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


# An initial ("J." in "J. Varga") is kept in a name's tokens with this mark, so that a surname with an
# initial can be matched to the full name it abbreviates; it never counts as a word of the name.
_INITIAL = "."


def name_tokens(name: Optional[str]) -> frozenset[str]:
    """Tokens of a party name: no legal suffixes or numbers; initials are kept as 'j.' (see ``names_match``)."""
    words = norm_text(name).split()
    out = {t for t in words if len(t) > 1 and t not in _LEGAL_TOKENS and not t.isdigit()}
    out |= {t + _INITIAL for t in words if len(t) == 1 and t.isalpha()}
    return frozenset(out)


def _words(name: frozenset[str]) -> frozenset[str]:
    return frozenset(t for t in name if not t.endswith(_INITIAL))


def names_match(a: frozenset[str], b: frozenset[str]) -> bool:
    """Two party names are the same party.

    Normalized token overlap against the shorter name, with at least one distinctive (non-generic) word
    shared. When either name has a single distinctive word, one shared word is a coincidence as often as not
    ('Springfield' the city and 'Springfield Grand Hotels'), so the distinctive words must be the same, except
    that the other name's extra words may be the ones the single-word name abbreviates to initials ('J.
    Varga' and 'Jamal Varga')."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    shared = wa & wb
    if not (shared - _GENERIC_NAME_TOKENS):
        return False
    if len(shared) / min(len(wa), len(wb)) < NAME_OVERLAP_MIN:
        return False
    da, db = wa - _GENERIC_NAME_TOKENS, wb - _GENERIC_NAME_TOKENS
    if len(da) >= 2 and len(db) >= 2:
        return True
    if da == db:
        return True
    single, other, initials = (da, db, a) if len(da) == 1 else (db, da, b)
    extra = other - single
    marks = {t[0] for t in initials if t.endswith(_INITIAL)}
    return bool(marks) and single <= other and all(w[0] in marks for w in extra)


def name_in_text(name: frozenset[str], text_tokens: frozenset[str]) -> bool:
    """Every distinctive token of the name appears in the text."""
    distinctive = _words(name) - _GENERIC_NAME_TOKENS
    return bool(distinctive) and distinctive <= text_tokens


def name_mentioned(name: frozenset[str], text_tokens: frozenset[str]) -> bool:
    """Most of a party's distinctive name appears in the text ('Ridgeway plant visit' names 'Ridgeway Air Systems')."""
    distinctive = _words(name) - _GENERIC_NAME_TOKENS
    if not distinctive:
        return False
    shared = len(distinctive & text_tokens)
    return shared >= 1 and shared / len(distinctive) >= NAME_OVERLAP_MIN


_ADDRESS_LINE = re.compile(
    r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b|\(\d{3}\)\s*\d{3}-\d{4}|\b\d{3}[-.]\d{3}[-.]\d{4}\b|\bwww\.|https?://|@\S+\.\w"
    r"|^\s*\d{1,6}\s+(?:[A-Z][\w.'-]*\s+){0,4}(?:Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way"
    r"|Parkway|Pkwy|Court|Ct|Place|Pl|Highway|Hwy|Circle|Terrace|Trail|Loop|Plaza|Square)\b",
)
_STREET = re.compile(
    r"\b(\d{1,6})\s+((?:[A-Z][A-Za-z.'-]*\s+){1,4}?)(Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln"
    r"|Way|Parkway|Pkwy|Court|Ct|Place|Pl|Highway|Hwy|Circle|Terrace|Trail|Loop|Plaza|Square)\b"
)
_STREET_SUFFIX = {"rd": "road", "st": "street", "ave": "avenue", "blvd": "boulevard", "dr": "drive", "ln": "lane",
                  "pkwy": "parkway", "ct": "court", "pl": "place", "hwy": "highway"}


def body_words(text: str) -> tuple[str, ...]:
    """The document's words outside address and contact lines, without legal-form words, in order."""
    out: list[str] = []
    for line in (text or "").splitlines():
        if _ADDRESS_LINE.search(line):
            continue
        out += [w for w in norm_text(line).split() if w not in _LEGAL_TOKENS]
    return tuple(out)


def street_addresses(text: str) -> frozenset[str]:
    """Normalized street addresses in a text ('12 Dock Street' -> '12 dock street')."""
    out = set()
    for m in _STREET.finditer(text or ""):
        suffix = m.group(3).lower().rstrip(".")
        out.add(f"{m.group(1)} {norm_text(m.group(2))} {_STREET_SUFFIX.get(suffix, suffix)}")
    return frozenset(out)


def _phrase_in(phrase: Sequence[str], words: Sequence[str]) -> bool:
    n = len(words)
    for i in range(n):
        j, k = i, 0
        while j < n and k < len(phrase):
            want, got = phrase[k], words[j]
            if got == want or (len(want) == 1 and got.startswith(want)):
                j, k = j + 1, k + 1
            elif len(got) == 1 and k > 0:
                j += 1  # a middle initial the name leaves out
            else:
                break
        if k == len(phrase):
            return True
    return False


def place_words(text: str) -> frozenset[str]:
    """Words of a document's address lines (streets, cities, states): place names, never a party's name."""
    out: set[str] = set()
    for line in (text or "").splitlines():
        if _ADDRESS_LINE.search(line):
            out |= set(norm_text(line).split())
    return frozenset(out)


def name_in_body(name: Optional[str], words: Sequence[str], places: frozenset[str] = frozenset()) -> bool:
    """The party's name appears as a phrase, in order, in a document's body words: the whole name, or its
    distinctive words together ('the Brookline payoff' names Brookline National Bank) when none of them is a
    place the document's own address lines name. An initial matches any word it begins, and a middle initial
    in the text may be skipped. Scattered words (a town that shares a word with the party, a word of a broker's
    tagline) never make a name."""
    name_words = [w for w in norm_text(name).split() if w not in _LEGAL_TOKENS]
    distinctive = [w for w in name_words if w not in _GENERIC_NAME_TOKENS and len(w) > 1]
    if not name_words or not distinctive:
        return False
    if _phrase_in(name_words, words):
        return True
    return not (set(distinctive) & places) and _phrase_in(distinctive, words)


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
# Short stems match too much: five letters keeps "install" and "repair" but not "rent" or "fee".
_MIN_STEM = 5


def stem(word: str) -> str:
    """Crude suffix stripping so 'installer' meets 'install' and 'repairs' meets 'repair'."""
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
        names = [lbl for lbl, _ in nonzero]
        where = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
        return f"{money(nonzero[0][1])} in {where}"
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
    memo_ref_kind: str = ""  # "matter", "contract", "project", ... (see ``typed_refs``)

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
    # Typed references (kind, reference) in a document's file name and title: the matter / contract /
    # project it is *about*, as opposed to references its body merely mentions ("separate from Matter 12").
    doc_title_refs: dict[str, frozenset[tuple[str, str]]] = field(default_factory=dict)
    company_tokens: frozenset[str] = frozenset()  # the target company's name: its own documents are not outside evidence
    gl_numbers: frozenset[str] = frozenset()  # normalized doc numbers the GL carries (P&L entries)
    # A document's words outside its address and contact lines (street, "City, ST ZIP", phone, web), with
    # legal-form words dropped, in order: a party is named in a document only as a phrase in these.
    doc_body_words: dict[str, tuple[str, ...]] = field(default_factory=dict)
    doc_places: dict[str, frozenset[str]] = field(default_factory=dict)  # words of a document's address lines
    # Street addresses in a document's title or file name: the property the document is about.
    doc_subjects: dict[str, frozenset[str]] = field(default_factory=dict)
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


# Export columns that identify one transaction; lines of one transaction share it.
_TXN_ID_KEYS = frozenset({"internal id", "transaction id", "transaction number", "journal id", "journal number", "txn id"})
_TOTAL_LABELS = re.compile(r"total|due|balance", re.IGNORECASE)


def _txn_id(entry: GLEntry) -> str:
    return next((v for k, v in entry.dimensions.items() if k.strip().lower() in _TXN_ID_KEYS and v), "")


def _bill_shows_one_charge(index: "DealIndex", number: str, amount: Decimal, postings: int) -> bool:
    """Every document for the bill number shows one charge of ``amount``: its total equals one posting
    (and no total is a multiple of it), or, without a total, it states the amount once. Without a
    document the posting dates decide alone."""
    tol = index.tolerance
    for doc_id in index.docs_by_ref.get(number, []):
        facts = index.facts.get(doc_id)
        if facts is None:
            continue
        stated: list[tuple[str, Decimal]] = []
        for a in facts.amounts:
            try:
                stated.append((a.label, abs(D(a.amount))))
            except (ValueError, ArithmeticError):
                continue
        totals = [v for label, v in stated if _TOTAL_LABELS.search(label)]
        if totals:
            if any(abs(v - amount * k) <= tol for v in totals for k in range(2, postings + 1)):
                return False  # the bill itself charges the amount more than once
            if not any(abs(v - amount) <= tol for v in totals):
                return False
        elif sum(1 for _, v in stated if abs(v - amount) <= tol) != 1:
            return False
    return True


def is_repeated_bill(index: "DealIndex", group: Sequence[str]) -> bool:
    """A duplicate group the GL carries under one document number, inside EBITDA (SPEC §5.7).

    The same bill number posted twice is a bookkeeping error with a mechanical reversal; a
    same-memo pair within a week without a shared number may be two genuine charges, so it
    stays a question. So does a group whose postings share a date (or a transaction id): two
    identical lines of one bill (two seat licences, two installments on one invoice) post
    together, and are one bill charging twice, not a bill entered twice. The bill's own document
    must show one charge.
    """
    if len(group) < 2 or not all(e in index.by_id for e in group):
        return False  # a balance-sheet posting has no EBITDA effect
    infos = [index.by_id[e] for e in group]
    numbers = {i.doc_number for i in infos}
    if len(numbers) != 1 or not next(iter(numbers)):
        return False
    if any(i.klass in EBITDA_EXCLUDED_CLASSES for i in infos):
        return False
    ids = [_txn_id(i.entry) for i in infos]
    if all(ids) and len(set(ids)) < len(ids):
        return False  # lines of one transaction
    dates = [i.entry.date for i in infos]
    if len(set(dates)) < len(dates) and not (all(ids) and len(set(ids)) == len(ids)):
        return False  # posted together: lines of one bill, unless the export shows separate transactions
    return _bill_shows_one_charge(index, next(iter(numbers)), abs(infos[0].amount), len(infos))


def _entry_info(entry: GLEntry, pos: int, klass: EbitdaClass) -> EntryInfo:
    cp = name_tokens(entry.counterparty)
    memo_norm = norm_text(entry.memo)
    m = _MEMO_REF.search(entry.memo or "")
    memo_ref, memo_ref_norm, memo_ref_kind = "", "", ""
    if m and _valid_ref(ref_norm(m.group(2))):
        memo_ref, memo_ref_norm = f"{m.group(1)} {m.group(2)}", ref_norm(m.group(2))
        memo_ref_kind = ref_kind(m.group(1))
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
        memo_ref_kind=memo_ref_kind,
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
        doc_title_refs={d: typed_refs(d) | typed_refs(facts_by_id[d].title) for d in docs},
        company_tokens=name_tokens(meta.target_name),
        gl_numbers=frozenset(by_number),
        doc_body_words={d: body_words(docs[d].full_text) for d in docs},
        doc_places={d: place_words(docs[d].full_text) for d in docs},
        doc_subjects={d: street_addresses(f"{d} {facts_by_id[d].title or ''}") for d in docs},
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
    party: bool = False  # the Counterparty signal fired: the entry is with a party the claim names


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
# Bases on which a document is *about* an entry: it states the entry's doc number, the
# entry's matter / claim reference, or its amount for the same party (SPEC §5.2), or it is
# the claim letter behind a recovery. Only these reach DocLink.entry_ids, GLLink.doc_ids and
# the documented amount. "named" (the document merely names the entry's counterparty) and
# "classification" (an AI said the removal rests on it) stay document-level: a law firm's
# litigation invoice names the firm, which does not make it support for the firm's retainer.
# "event" is a party name plus the entry's own subject (a plant-visit agenda naming the traveller
# and the visit), on a document that is not another entry's bill or another matter's letter.
ENTRY_ABOUT_BASES = frozenset(
    {"number", "amount", "amount_multi", "group", "reference", "mention", "event", "recovery"}
)
_MIN_CITED_NUMBER = 5
# Bases that pin a document to one entry: only these may carry a service period onto it.
ENTRY_SPECIFIC_BASES = frozenset({"number", "amount", "group"})

# GLLink.role values (schemas.GLLink).
ROLE_SUPPORTING = "supporting"
ROLE_REMOVED = "removed"
ROLE_MOVED = "moved"
ROLE_RECOVERY = "recovery"
ROLE_CONTEXT = "context"

# Removals that decide whose item an entry is rather than whether the claim is right: the entry
# belongs to another adjustment, sits below EBITDA already, or is the extra posting of a bill the
# GL carries twice (a diligence item reverses it, SPEC §5.7). Evidence challenges skip these.
STRUCTURAL_REMOVALS = frozenset(
    {
        FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
        FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
        FlagCode.DUPLICATE_GL_ENTRY,
    }
)


@dataclass
class Removal:
    code: FlagCode
    note: str
    source: str = "code"  # "ai" when an AI entry classification drove it
    doc_ids: list[str] = field(default_factory=list)  # documents the removal rests on
    flag: Optional[Flag] = None  # the flag that removed the entry (set by the challenge that raised it)


@dataclass
class Effect:
    label: str
    amount: Decimal
    code: FlagCode
    entry_id: str
    flag: Optional[Flag] = None  # the flag whose effect this is


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
    diff_cents: int = 0  # |chosen total - claim| in cents: 0 is a fit to the cent, else within the tolerance


@dataclass
class NormalizationInfo:
    actual: dict[str, Decimal]
    level: Optional[Decimal] = None  # annual normalized level the evidence supports
    level_candidates: list[Decimal] = field(default_factory=list)
    supported_by: Optional[str] = None
    draft_docs: list[str] = field(default_factory=list)
    mgmt_level: Optional[Decimal] = None  # annual level management used (stated, else implied by the claim)
    benchmark: bool = False  # the level comes from an independent market benchmark, not management's
    level_flag: Optional[Flag] = None  # the flag that set a level other than management's (carries that change)


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
    group_ref_kind: dict[str, str] = field(default_factory=dict)  # group label -> kind of that reference ("" unknown)
    claimed: dict[str, list[str]] = field(default_factory=dict)  # period label -> claimed entry ids
    # Period label -> unclaimed entries diligence carries anyway (SPEC §5.4 EXCESS_GL_ACTIVITY carry
    # rule): the rest of a fixed-fee engagement management claimed only in part.
    carried: dict[str, list[str]] = field(default_factory=dict)
    fits: dict[str, PeriodFit] = field(default_factory=dict)
    capped: set[str] = field(default_factory=set)
    doc_links: dict[str, DocLinkInfo] = field(default_factory=dict)
    flags: list[Flag] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    judgments: list[str] = field(default_factory=list)
    removals: dict[str, Removal] = field(default_factory=dict)
    moved: set[str] = field(default_factory=set)  # out-of-period entries; effects carry their amount
    # Entries linked only because their memo restates the account name, in an account and period where
    # other entries link on independent evidence: context, never claimed.
    echo_context: list[str] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    recurrence: list[RecurrenceObservation] = field(default_factory=list)
    normalization: Optional[NormalizationInfo] = None
    notes: list[str] = field(default_factory=list)
    dropped_quotes: int = 0  # AI quotes (contradictions) that failed verification here
    ai_dropped_quotes: int = 0  # AI quotes the AI adapter itself rejected during this adjustment's calls
    search_terms: str = ""
    _judgment_keys: set[str] = field(default_factory=set, repr=False)
    _judgment_text: dict[str, str] = field(default_factory=dict, repr=False)
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

    def cost_free_labels(self) -> set[str]:
        """Normalization periods where management's own figures say the arrangement costs nothing (rent-free
        premises, an unpaid owner): the claim is minus the stated annual level, pro rata, and the GL traces no
        cost. The level is then the whole normalization, not a gap in the actual cost."""
        if not self.is_normalization or not self.intent.normalized_amount:
            return set()
        try:
            level = abs(D(self.intent.normalized_amount))
        except (ValueError, ArithmeticError):
            return set()
        out: set[str] = set()
        for lbl in self.claimed_labels():
            months = len(self.index.label_months[lbl])
            expected = level * months / 12
            if self.claim(lbl) < 0 and self.traced(lbl) == 0 and abs(-self.claim(lbl) - expected) <= self.index.tolerance * months:
                out.add(lbl)
        return out

    def amount(self, entry_id: str) -> Decimal:
        return self.index.by_id[entry_id].amount

    def claimed_ids(self) -> list[str]:
        ids: set[str] = set()
        for v in self.claimed.values():
            ids.update(v)
        return self.index.sort_ids(ids)

    def in_play_ids(self) -> list[str]:
        """Claimed entries that are this adjustment's own items: not lost to another adjustment,
        not already below EBITDA, and not an extra posting of a duplicated bill (a diligence item
        carries that). Evidence challenges look only at these."""
        return [e for e in self.claimed_ids() if e not in self.removals or self.removals[e].code not in STRUCTURAL_REMOVALS]

    def carried_ids(self) -> list[str]:
        ids: set[str] = set()
        for v in self.carried.values():
            ids.update(v)
        return self.index.sort_ids(ids)

    def supporting(self, label: str) -> list[str]:
        """Entries diligence carries in the period: claimed and not removed, plus carried entries."""
        own = [e for e in self.claimed.get(label, []) if e not in self.removals]
        return own + [e for e in self.carried.get(label, []) if e not in self.removals and e not in own]

    def supporting_ids(self) -> list[str]:
        return self.index.sort_ids(
            [e for e in self.claimed_ids() if e not in self.removals]
            + [e for e in self.carried_ids() if e not in self.removals]
        )

    def traced(self, label: str) -> Decimal:
        return sum((self.amount(e) for e in self.claimed.get(label, [])), ZERO)

    def documented(self, label: str) -> Decimal:
        """(c) Documented: claimed entries vouched to their own document (tick D), by the same
        per-entry rule the workpaper's audit trail uses (``vouch_tick``), so the two agree."""
        return sum((self.amount(e) for e in self.claimed.get(label, []) if self.vouched(e)), ZERO)

    def vouched(self, entry_id: str) -> bool:
        info = self.index.by_id[entry_id]
        return any(
            vouch_tick(self.index.facts.get(d), info.entry, info.amount, self.index.tolerance, self.index.gl_numbers)
            == "D"
            for d in self.entry_docs(entry_id)
        )

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
        """Documents that are about the entry (``ENTRY_ABOUT_BASES``), never a party-name match alone."""
        return sorted(
            d for d, info in self.doc_links.items() if info.entry_basis.get(entry_id) in ENTRY_ABOUT_BASES
        )

    def doc_type(self, doc_id: str) -> str:
        return (self.index.facts[doc_id].doc_type if doc_id in self.index.facts else "other").strip().lower()

    def support_docs(self, entry_id: str) -> list[str]:
        """Documents that evidence an entry. The company's own emails and memos are management
        representations, not documentary support, so they do not count (SPEC §5.4 NO_DOCUMENT_SUPPORT).
        A journal entry's outside corroboration counts (see ``_associate_documents``)."""
        return [d for d in self.entry_docs(entry_id) if self.doc_type(d) not in CORRESPONDENCE_DOC_TYPES]

    def outside_corroboration(self) -> list[str]:
        """Documents management cites that come from someone other than the company under review."""
        company = self.index.company_tokens
        return [
            d
            for d, info in sorted(self.doc_links.items())
            if info.cited
            and self.doc_type(d) not in CORRESPONDENCE_DOC_TYPES
            and self.index.doc_cp.get(d)
            and not (company and names_match(self.index.doc_cp[d], company))
        ]

    def entry_docs_by_basis(self, entry_id: str, bases: Iterable[str]) -> list[str]:
        wanted = set(bases)
        return sorted(d for d, info in self.doc_links.items() if info.entry_basis.get(entry_id) in wanted)

    def associate(self, doc_id: str, entry_id: str, basis: str, weight: float, reason: str) -> None:
        """Tie a document to an entry. The first basis stands, except that a basis on which the
        document is about the entry replaces a weaker one (a party-name match, an AI citation)."""
        info = self.doc_links.setdefault(doc_id, DocLinkInfo(doc_id=doc_id))
        current = info.entry_basis.get(entry_id)
        if current is not None and (current in ENTRY_ABOUT_BASES or basis not in ENTRY_ABOUT_BASES):
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
        return [
            g
            for g, members in self.groups.items()
            if any(names_match(idx.by_id[e].cp_tokens, cp) for e in members) and not self.about_other_matter(doc_id, g)
        ]

    def _other_engagement(self, doc_id: str) -> bool:
        """Every claimed group carries a reference and the document is about another one."""
        groups = {self.group_of.get(e, "") for e in self.claimed_ids()}
        return bool(groups) and all(self.about_other_matter(doc_id, g) for g in groups)

    def about_other_matter(self, doc_id: str, group: str) -> bool:
        """The document is about a different engagement of the same party than the group's.

        A law firm or vendor bills several matters or contracts; a document whose own heading
        names a reference of the same kind as the group's (a matter against a matter, a contract
        against a contract) but a different one is about that other engagement, and does not speak
        to the group, which it never names. Like is compared with like: dates, fiscal years, street
        numbers or form numbers in a title name no engagement.
        """
        ref, kind = self.group_ref.get(group, ""), self.group_ref_kind.get(group, "")
        if not ref or not kind:
            return False
        own = {n for k, n in self.index.doc_title_refs.get(doc_id, frozenset()) if k == kind}
        return bool(own) and ref not in own and ref not in self.index.doc_refs.get(doc_id, frozenset())

    # -- mutation ----------------------------------------------------------

    def remove(
        self, entry_ids: Iterable[str], code: FlagCode, note: str, source: str = "code", doc_ids: Iterable[str] = ()
    ) -> list[str]:
        """Take entries out of the supporting set; returns the ones not already removed.

        The first challenge to remove an entry owns it: a later flag on the same entries
        corroborates the removal but has no further effect on the amount."""
        newly: list[str] = []
        for e in self.index.sort_ids(entry_ids):
            if e not in self.removals:
                self.removals[e] = Removal(code=code, note=note, source=source, doc_ids=sorted(set(doc_ids)))
                newly.append(e)
        return newly

    def attach(self, entry_ids: Iterable[str], flag: Flag) -> None:
        """Record ``flag`` as the flag that removed ``entry_ids`` (see ``remove``)."""
        for e in entry_ids:
            removal = self.removals.get(e)
            if removal is not None and removal.flag is None:
                removal.flag = flag

    def add_flag(self, flag: Flag) -> Flag:
        """Add a flag unless an identical one is already raised; returns the flag held by the trace."""
        key = (flag.code, flag.period_label, tuple(flag.entry_ids), tuple(flag.doc_ids), flag.message)
        for f in self.flags:
            if (f.code, f.period_label, tuple(f.entry_ids), tuple(f.doc_ids), f.message) == key:
                return f
        self.flags.append(flag)
        return flag

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
            self._judgment_text[key] = text
            self.judgments.append(text)

    def drop_judgment(self, key: str) -> None:
        """Withdraw a judgment point a later finding settled (e.g. a claimed-set tie made moot)."""
        text = self._judgment_text.pop(key, None)
        if text is not None:
            self._judgment_keys.discard(key)
            self.judgments = [j for j in self.judgments if j != text]

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

    def group_label(self, entry_id: str) -> str:
        return self.group_of.get(entry_id) or _group_display(self.index.by_id[entry_id])

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

    def role_of(self, entry_id: str) -> str:
        """The entry's audit-trail role in this adjustment (GLLink.role)."""
        if entry_id in self.removals:
            return ROLE_REMOVED
        if any(entry_id in ids for ids in self.claimed.values()):
            return ROLE_MOVED if entry_id in self.moved else ROLE_SUPPORTING
        if any(entry_id in ids for ids in self.carried.values()):
            return ROLE_SUPPORTING
        if any(x.entry_id == entry_id and x.code == FlagCode.OFFSETTING_RECOVERY for x in self.effects):
            return ROLE_RECOVERY
        return ROLE_CONTEXT

    def labels_carrying(self, entry_id: str) -> list[str]:
        return [lbl for lbl in self.labels if entry_id in self.carried.get(lbl, [])]

    def gl_links(self) -> list[GLLink]:
        claimed = set(self.claimed_ids())
        carried = set(self.carried_ids())
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
            elif eid in carried:
                reasons.append(
                    "Not claimed; carried in " + ", ".join(self.labels_carrying(eid))
                    + " as part of the same fixed-fee engagement (EXCESS_GL_ACTIVITY)"
                )
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
                    supports_claim=(eid in claimed or eid in carried) and removal is None,
                    doc_ids=self.entry_docs(eid),
                    role=self.role_of(eid),
                    claimed=eid in claimed,
                    claimed_in=self.labels_claiming(eid),
                    removed_by=removal.code if removal is not None else None,
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
            about = [e for e, basis in info.entry_basis.items() if basis in ENTRY_ABOUT_BASES]
            relation = info.relation or _default_relation(facts, info)
            if relation == "agreement" and not about and self._other_engagement(doc_id):
                relation = "other"  # the agreement for another matter of the same party: context, not support
            out.append(
                DocLink(
                    doc_id=doc_id,
                    relation=relation,
                    entry_ids=self.index.sort_ids(about),
                    score=round(info.score, 2),
                    reasons=list(info.reasons),
                    quotes=_doc_quotes(facts, self, info),
                )
            )
        out.sort(key=lambda d: (-d.score, d.doc_id))
        return out


# ---------------------------------------------------------------------------
# Vouching (the D / A / S / U / C document ticks of the workpaper's audit trail)
# ---------------------------------------------------------------------------

# Legal-form words that do not identify a party when vouching an entry's counterparty.
_VOUCH_PARTY_STOP = frozenset(
    {"llc", "inc", "co", "corp", "corporation", "company", "the", "lp", "llp", "lllp", "pa", "na", "ltd", "limited",
     "and", "of", "plc", "pc", "pllc", "pty", "dba", "gmbh", "bv", "nv", "ag", "sarl", "srl"}
)


def _ref_scheme(ref: str) -> tuple[str, str]:
    """(alpha prefix, shape) of a normalized reference: 'KS10311' -> ('KS', 'AA99999')."""
    prefix = re.match(r"[A-Z]*", ref).group() if ref else ""
    return prefix, re.sub(r"[0-9]", "9", re.sub(r"[A-Z]", "A", ref))


def same_numbering(a: str, b: str) -> bool:
    """Two normalized references look like numbers from one numbering scheme: the same alpha prefix, or the
    same pattern of letters and digits. A NetSuite 'BILL00421' and a vendor's 'INV88213' do not."""
    (pa, sa), (pb, sb) = _ref_scheme(a), _ref_scheme(b)
    return bool(pa and pa == pb) or sa == sb


def _vouch_party(name: Optional[str]) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (name or "").lower()) if w not in _VOUCH_PARTY_STOP}


def _month_no(month: Optional[str]) -> Optional[int]:
    try:
        y, m = (month or "")[:7].split("-")
        return int(y) * 12 + int(m)
    except ValueError:
        return None


def vouch_tick(
    facts: Optional[DocFacts],
    entry: GLEntry,
    amount: Decimal,
    tolerance: Decimal,
    gl_numbers: frozenset[str] = frozenset(),
) -> str:
    """How a document about an entry vouches it: D (its own document: the entry's number, or the
    same amount for the same party near the entry's month), A (agreement only), S (a sample: the
    same charge under another number or in another month), U (draft / unsigned), C (the
    company's own correspondence), or "" (not specific to the entry).

    A practitioner ticks an entry as vouched only against the document that evidences that very
    charge; an engagement letter or a monthly statement for another month supports the item but
    does not vouch the entry. This is the rule the Excel audit trail uses for its D tick, so the
    (c) Documented line and the ticks agree.

    A document whose own number differs from the entry's is another charge (S) only when the two numbers
    come from one numbering scheme, or when the document's number is on another GL entry
    (``gl_numbers``: the normalized doc numbers the GL carries). An ERP's internal transaction number
    ('BILL00421') says nothing about the vendor's invoice number, so the amount, party and date decide.
    """
    if facts is None:
        return ""
    dtype = (facts.doc_type or "").strip().lower()
    if dtype in CORRESPONDENCE_DOC_TYPES:
        return "C"
    refs = {r for r in (ref_norm(x) for x in facts.reference_numbers) if r}
    number = ref_norm(entry.doc_number)
    if number and number in refs:
        return "D"
    states_amount = False
    for a in facts.amounts:
        try:
            states_amount = states_amount or abs(abs(D(a.amount)) - abs(amount)) <= tolerance
        except (ValueError, ArithmeticError):
            continue
    memo = ref_norm(entry.memo)
    if states_amount and memo and any(len(r) >= 5 and any(ch.isdigit() for ch in r) and r in memo for r in refs):
        return "D"
    if dtype in AGREEMENT_DOC_TYPES:
        return "U" if facts.is_draft or facts.is_signed is False else "A"
    if facts.is_draft:
        return "U"
    if not states_amount:
        return ""
    if number and any(same_numbering(number, r) or r in gl_numbers for r in refs if r != number):
        return "S"
    a_party, b_party = _vouch_party(entry.counterparty), _vouch_party(facts.counterparty)
    party_ok = (
        not facts.counterparty
        or not entry.counterparty
        or (bool(a_party and b_party) and len(a_party & b_party) / min(len(a_party), len(b_party)) >= 0.6)
    )
    m = _month_no(entry.period or entry.date)
    start, end, dated = (_month_no(facts.service_period_start), _month_no(facts.service_period_end),
                         _month_no(facts.doc_date))
    if m is None or (start is None and end is None and dated is None):
        near = True
    else:
        near = (start is not None and end is not None and start - 1 <= m <= end + 2) or (
            dated is not None and abs(dated - m) <= 2
        )
    return "D" if party_ok and near else "S"


def _default_relation(facts: Optional[DocFacts], info: DocLinkInfo) -> str:
    doc_type = (facts.doc_type if facts else "other").lower()
    bases = set(info.entry_basis.values())
    if "number" in bases:
        return "invoice_for_entry"
    if doc_type == "invoice":
        # An invoice is only "the invoice for" entries it is about; one that merely names the party
        # (another matter's bill from the same firm) is context.
        return "invoice_for_entry" if bases & ENTRY_ABOUT_BASES else "other"
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
    ids = [e for e, basis in info.entry_basis.items() if basis in ENTRY_ABOUT_BASES and e in trace.index.by_id]
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


def restates_account(keyword: str, account_name: str) -> bool:
    """The keyword only repeats the account's own name ('repairs' in 'Repairs & Maintenance').

    Every entry in that account is described by those words, so they say nothing about which
    entries belong to the claimed event: a routine repair in a repairs account is upkeep, not the
    casualty loss management adds back. A word restates the account only when it is one of the
    account's words, its plural or singular, or has the same stem: 'rent' does not restate
    'Rental Income', nor 'pro' 'Professional Fees'.
    """
    toks = norm_text(account_name).split()
    if not toks:
        return False
    stems = {stem(t) for t in toks}

    def known(w: str) -> bool:
        if w in toks or stem(w) in stems:
            return True
        return any(t in (w + "s", w + "es") or w in (t + "s", t + "es") for t in toks)

    words = [w for w in norm_text(keyword).split() if w not in _THEME_STOP]
    return bool(words) and all(known(w) for w in words)


def _score_entry(info: EntryInfo, ctx: _LinkContext, idx: DealIndex) -> tuple[float, list[str], bool, float]:
    """(score, reasons, party signal fired, weight of keywords that only restate the account name)."""
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

    all_hits = keyword_hits(ctx.keywords, info.memo_norm, info.memo_tokens, party)
    # A keyword that restates the account name is not an independent signal (see restates_account).
    hits = [h for h in all_hits if not restates_account(h, e.account_name)]
    echo = [h for h in all_hits if h not in hits]
    echo_bonus = 0.0
    if hits:
        score += W_KEYWORD + min(W_KEYWORD_EXTRA * (len(hits) - 1), W_KEYWORD_EXTRA_CAP)
        reasons.append("Memo mentions " + ", ".join(f"'{h}'" for h in hits))
    elif echo:
        echo_bonus = W_KEYWORD + min(W_KEYWORD_EXTRA * (len(echo) - 1), W_KEYWORD_EXTRA_CAP)
        reasons.append(
            "Memo mentions " + ", ".join(f"'{h}'" for h in echo) + ", which only restates the account name"
        )

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
    return score, reasons, bool(cp_reason), echo_bonus


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
            t.group_ref_kind[label] = info.memo_ref_kind if ref == info.memo_ref_norm else ""


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
        # The claim is actual cost in the named accounts less a normalized level (SPEC §5.4).
        # A normalization restates one arrangement (the owner's pay, the related-party lease) at
        # market, so the actual cost is that arrangement's entries. An entry with a counterparty of its
        # own that is not the arrangement's party (another landlord, the county's tax bill, another
        # employee) is another arrangement and stays context. Entries without a counterparty (a payroll
        # journal, an accrual) linked on the arrangement's own words stay in: many ledgers post salary
        # with no contact, so the party signal alone would drop the owner's pay.
        accounts = set(t.adj.gl_accounts)
        in_accounts = [e for e in t.candidates if not accounts or idx.by_id[e].entry.account in accounts]
        named = {e for e in in_accounts if t.links[e].party}
        party_known = bool(named) or any(name_tokens(n) for n in t.intent.counterparties)

        def own_arrangement(e: str) -> bool:
            return e in named or not party_known or not idx.by_id[e].cp_tokens

        for lbl, cands in cands_by_label.items():
            cands = [e for e in cands if e in in_accounts and own_arrangement(e)]
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
            fit.bounded, fit.ties, fit.cited, fit.diff_cents = found.bounded, found.ties, found.cited, found.diff
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


# Memo words that name no particular event: a document sharing only these with an entry is not about it.
_EVENT_GENERIC = frozenset(
    """travel services service fee fees payment payments monthly invoice invoices expense expenses cost costs air
    hotel registration company business personal general office admin report reports statement statements agenda
    summary details detail matter matters professional legal""".split()
)


# Distinctive words an entry's memo and a document must share to name the same subject; one
# shared word ("loan", "Carrier") is a coincidence as often as not.
MIN_EVENT_WORDS = 2


def _event_words(text_tokens: Iterable[str]) -> set[str]:
    return {stem(w) for w in text_tokens if len(w) >= 3 and w not in _EVENT_GENERIC and not w.isdigit()}


def _associate_documents(t: AdjustmentTrace) -> None:
    """Tie documents to the claimed entries they are about (SPEC §5.2 Document signal).

    In order of strength: the document states the entry's doc number; it states the entry's
    amount for the same party (named as its counterparty, or in its text when management's
    support references point at it); correspondence cites the entry's number; it states a
    group's total; it states the group's matter / contract reference. A document whose own
    number belongs to another entry, or whose title names another matter of this adjustment,
    is never tied to the entry on amount or party grounds. A related document that merely
    names the entry's party is tied at document level only ("named"), unless it also names
    the entry's subject ("event"), e.g. a plant-visit agenda naming the traveller and the visit.
    """
    idx = t.index
    prelinked = {d for d, info in t.doc_links.items() if info.prelinked}
    support_docs = {d for d, info in t.doc_links.items() if info.cited}
    group_refs = {(t.group_ref_kind.get(g, ""), r) for g, r in t.group_ref.items() if t.group_ref_kind.get(g)}

    def other_matter(doc_id: str, entry_id: str) -> bool:
        """The document's title names a matter (contract, project ...) of this adjustment other than the entry's own."""
        named = idx.doc_title_refs.get(doc_id, frozenset()) & group_refs
        g = t.group_of.get(entry_id, "")
        own = (t.group_ref_kind.get(g, ""), t.group_ref.get(g, ""))
        return bool(named) and own not in named

    def other_entry(doc_id: str, entry_id: str) -> bool:
        """The document is the bill for a different entry (it states that entry's doc number)."""
        own = idx.doc_entries.get(doc_id, frozenset())
        return bool(own) and entry_id not in own

    named_cache: dict[tuple[str, str], bool] = {}

    def names_party(doc_id: str, party: str) -> bool:
        """The document's body names the party as a phrase (see ``name_in_body``); cached per (document, name)."""
        key = (doc_id, party)
        if key not in named_cache:
            named_cache[key] = name_in_body(party, idx.doc_body_words.get(doc_id, ()), idx.doc_places.get(doc_id, frozenset()))
        return named_cache[key]

    amount_hits: dict[str, list[str]] = {}
    # Only claimed entries: documents about context-only activity (prior-year comparables,
    # other vendors' invoices in the same account) are not evidence for this claim.
    claimed = t.claimed_ids()
    for e in claimed:
        info = idx.by_id[e]
        if info.doc_number:
            for doc_id in idx.docs_by_ref.get(info.doc_number, []):
                if e in idx.doc_entries[doc_id]:
                    t.associate(doc_id, e, "number", DW_ENTRY_NUMBER, "States the doc # of linked GL entries")
        for doc_id, _amt in dict.fromkeys(idx.docs_with_amount(info.amount)):
            if other_entry(doc_id, e) or other_matter(doc_id, e):
                continue
            dcp = idx.doc_cp[doc_id]
            if (
                names_match(dcp, info.cp_tokens)
                or (not info.cp_tokens and doc_id in support_docs)
                # A cited notice from a third party (debtor's counsel) naming the customer and the amount.
                or (doc_id in prelinked and names_party(doc_id, info.entry.counterparty))
            ):
                amount_hits.setdefault(doc_id, []).append(e)
    # A document management cites that states the entry's exact amount and is about the same property as a
    # document already tied to the entry (a broker's opinion of market rent for the leased premises, beside
    # the lease) is about the entry too, though it never names the entry's party.
    subject_hits: dict[str, list[tuple[str, str, str]]] = {}
    for e in claimed:
        info = idx.by_id[e]
        tied = [d for d, hits in amount_hits.items() if e in hits and idx.doc_subjects.get(d)]
        if not tied:
            continue
        for doc_id, _amt in dict.fromkeys(idx.docs_with_amount(info.amount)):
            if doc_id not in support_docs or e in amount_hits.get(doc_id, []) or other_entry(doc_id, e) or other_matter(doc_id, e):
                continue
            for d2 in tied:
                shared = sorted(idx.doc_subjects.get(doc_id, frozenset()) & idx.doc_subjects[d2])
                if shared and d2 != doc_id:
                    subject_hits.setdefault(doc_id, []).append((e, shared[0], d2))
                    break
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
    for doc_id, hits in subject_hits.items():
        basis = "amount" if len(hits) == 1 else "amount_multi"
        for e, subject, other in hits:
            t.associate(doc_id, e, basis, DW_ENTRY_AMOUNT,
                        f"States the amount of linked GL entries; about the same property ({subject}) as {other}")
    # A document stating a group's total (an engagement fee paid in installments) supports every entry in it.
    claimed_set = set(claimed)
    for g, all_members in t.groups.items():
        members = [e for e in all_members if e in claimed_set]
        if not members:
            continue
        # The document may state the whole engagement (all installments) even when only some are claimed.
        # A total is made of two or more entries: one entry's amount is that entry's own bill, not a total.
        totals = {sum((t.amount(e) for e in all_members), ZERO)}
        if len(members) > 1:
            totals.add(sum((t.amount(e) for e in members), ZERO))
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
                if other_entry(doc_id, e) or other_matter(doc_id, e):
                    continue  # another entry's invoice, or another matter's letter that mentions this one
                t.associate(doc_id, e, "reference", DW_ENTRY_NUMBER, f"States reference {ref} of {g}")
    # Last and weakest: a related document naming the entry's party.
    for e in claimed:
        info = idx.by_id[e]
        if not info.cp_tokens:
            continue
        subject = _event_words(info.theme)
        for doc_id in sorted(prelinked):
            if not names_party(doc_id, info.entry.counterparty):
                continue
            doc_words = _event_words(idx.doc_text_tokens[doc_id] | frozenset(norm_text(doc_id).split()))
            if len(subject & doc_words) >= MIN_EVENT_WORDS and not other_entry(doc_id, e) and not other_matter(doc_id, e):
                t.associate(doc_id, e, "event", DW_ENTRY_NAMED, f"Names {info.entry.counterparty} and the entry's subject")
            else:
                t.associate(doc_id, e, "named", DW_ENTRY_NAMED, f"Names {info.entry.counterparty}")
    # A journal entry with no counterparty (a write-off, a reserve, an accrual) has no outside bill: its
    # source document is the company's own calculation. When a company-authored document that is not
    # correspondence (a memorandum, a calculation, a schedule, an analysis, board minutes) states the
    # entry's amount, the outside documents management cites for the claim (a supplier's notice, a
    # disposal certificate, a court filing) are the evidence of the event the entry records, and
    # support it. Emails never pin an entry this way, and an outside document that is already another
    # claimed entry's own bill (tied to it by number or amount) is that entry's support, not this one's.
    outside = t.outside_corroboration()
    for e in claimed:
        if idx.by_id[e].cp_tokens or not outside:
            continue
        memos = [d for d in t.entry_docs_by_basis(e, ("number", "amount", "amount_multi", "group")) if _company_authored(t, d)]
        if memos:
            for d in outside:
                other_bill = any(
                    x != e and x in claimed_set and b in ("number", "amount", "amount_multi", "group")
                    for x, b in t.doc_links[d].entry_basis.items()
                )
                if other_bill:
                    continue
                t.associate(d, e, "event", DW_ENTRY_NAMED, f"Outside evidence of the event {memos[0]} records")
            t.add_fact(
                Fact(
                    text=f"{t.describe(e)} is a journal entry with no outside bill; {memos[0]} states its amount and "
                    f"{join_limited(outside, 1)} {'corroborate' if len(outside) > 1 else 'corroborates'} the event.",
                    entry_ids=[e],
                ),
                key=f"journal:{e}",
            )
    for info in t.doc_links.values():
        n = sum(1 for b in info.entry_basis.values() if b in ENTRY_ABOUT_BASES)
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
        if t.is_normalization and set(t.claimed_labels()) <= t.cost_free_labels():
            return  # an arrangement that costs nothing has no GL entries to find; the level is the normalization
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
        # Activity running against the claim (credits beside an expense claim, revenue beside a cost) is
        # not part of what exceeds it: it is reported apart, never netted into the excess.
        same = [e for e in others if s * t.amount(e) > 0]
        against = [e for e in others if s * t.amount(e) < 0]
        excess = sum((t.amount(e) for e in same), ZERO)
        linked_same = traced + excess
        against_txt = (
            f" {entries_word(len(against))} running the other way ({money(sum((t.amount(e) for e in against), ZERO))}) "
            f"{plural(len(against), 'is', 'are')} context only too."
            if against else ""
        )
        if fit.method in ("groups", "entries"):
            groups = list(dict.fromkeys(t.group_of[e] for e in chosen))
            what = t.items_text(chosen, 1) if len(groups) == 1 else f"{len(groups)} groups"
            how = "to the cent" if fit.diff_cents == 0 else f"within the {money(idx.tolerance)} tolerance"
            if s * (linked_same - claim) > 0:
                msg = (
                    f"{lbl}: linked GL activity of {money(linked_same)} exceeds the {money(claim)} claim, which ties "
                    f"{how} to {entries_word(len(chosen))} ({what}); the other {money(excess)} is context only."
                    + against_txt
                )
            else:
                msg = (
                    f"{lbl}: the {money(claim)} claim ties {how} to {entries_word(len(chosen))} ({what})."
                    + against_txt
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
            # The excess is context activity management did not claim, not an EBITDA effect:
            # it stays in the message and never in amount_impact / effects.
            t.add_flag(
                Flag(
                    code=FlagCode.EXCESS_GL_ACTIVITY,
                    severity=Severity.INFO,
                    message=_short_sentence(msg),
                    period_label=lbl,
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
                            f"{lbl}: linked GL activity of {money(traced + excess)} exceeds the {money(claim)} claim "
                            f"and no combination of linked entries ties to it. The {entries_word(len(chosen))} with "
                            f"strong links ({money(traced)}) are treated as claimed, capped at the claim."
                        ),
                        period_label=lbl,
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
            # A related document that states the missing amount (an estimate in management's own
            # build-up of the claim) explains the gap; cite it so the reviewer sees what was never booked.
            explains = _documents_stating(t, abs(gap))
            if not explains:
                _echo_judgment(t, lbl, abs(gap), s)
            why = f" {explains[0][0]} states the same {money(abs(gap))}." if explains else ""
            t.add_flag(
                Flag(
                    code=FlagCode.PARTIAL_GL_SUPPORT,
                    severity=Severity.WARNING,
                    message=_short_sentence(
                        f"{lbl}: GL entries linked to this adjustment total {money(traced)} against the "
                        f"{money(claim)} claim, so {money(abs(gap))} of the claim is not found in the GL.{why}"
                    ),
                    period_label=lbl,
                    amount_impact=fmt(gap),
                    entry_ids=idx.sort_ids(chosen),
                    doc_ids=sorted({d for d, _ in explains}),
                    quotes=[q for _, q in explains][:2],
                )
            )


def _echo_judgment(t: AdjustmentTrace, label: str, gap: Decimal, s: int) -> None:
    """Routine entries held as context (their memo only restates the account name) that tie to a claim's gap:
    they may be part of the claimed event after all, so the reviewer decides rather than the tool dropping them."""
    idx = t.index
    months = idx.label_months[label]
    pool = [e for e in t.echo_context if idx.by_id[e].month in months and s * idx.by_id[e].amount > 0]
    if not pool:
        return
    pick = find_subset([s * cents(t.amount(e)) for e in pool], cents(gap), cents(idx.tolerance))
    if pick is None:
        return
    tied = [pool[i] for i in pick]
    accounts = sorted({f"{idx.by_id[e].entry.account} {idx.by_id[e].entry.account_name}" for e in tied})
    t.add_judgment(
        f"{label}: {entries_word(len(tied))} in {join_limited(accounts, 1)} whose memo only restates the account name "
        f"({t.describe_many(tied, 2)}) total the {money(gap)} the linked entries fall short of the claim. Are they "
        "part of the claimed event, or routine activity left out of it?",
        key=f"echo:{label}",
    )


# Document types that are never the company's own calculation of a book entry: agreements and bills are
# the other side's documents, correspondence is a representation, a payroll register is the source of
# routine wages rather than of an event, and a benchmark is a third party's view of market.
_NOT_CALCULATION_TYPES = AGREEMENT_DOC_TYPES | CORRESPONDENCE_DOC_TYPES.difference({"memo"}) | frozenset(
    {"invoice", "payroll", "benchmark", "insurance"}
)


def _company_authored(t: AdjustmentTrace, doc_id: str) -> bool:
    """The document is the company's own calculation (a memorandum, a schedule, an analysis, minutes): not an
    agreement, bill, correspondence or payroll register, and either an internal memorandum, or with no outside
    party, or with the company as its party, or on the company's letterhead (its name heads the first lines)."""
    idx = t.index
    dtype = t.doc_type(doc_id)
    if dtype in _NOT_CALCULATION_TYPES:
        return False
    if dtype == "memo":
        return True
    cp = idx.doc_cp.get(doc_id, frozenset())
    company = idx.company_tokens
    if not cp or (company and names_match(cp, company)):
        return True
    doc = idx.docs.get(doc_id)
    if doc is None or not doc.pages or not company:
        return False
    head = [line for line in doc.pages[0].text.splitlines() if line.strip()][:3]
    return any(name_in_text(company, frozenset(norm_text(line).split())) for line in head)


def _documents_stating(t: AdjustmentTrace, amount: Decimal) -> list[tuple[str, EvidenceQuote]]:
    """(doc_id, quote) for documents related to the adjustment that state ``amount``."""
    out: list[tuple[str, EvidenceQuote]] = []
    for doc_id, info in sorted(t.doc_links.items()):
        if not info.prelinked:
            continue
        for a in t.index.facts[doc_id].amounts:
            try:
                if abs(abs(D(a.amount)) - amount) <= t.index.tolerance:
                    out.append((doc_id, a.quote))
                    break
            except (ValueError, ArithmeticError):
                continue
    return out


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
    echoes: list[tuple[EntryInfo, float, list[str], bool]] = []
    for info in index.entries:
        score, reasons, party, echo = _score_entry(info, ctx, index)
        if score >= threshold:
            t.links[info.entry_id] = LinkInfo(
                entry_id=info.entry_id, score=round(score, 2), reasons=reasons, party=party
            )
            t.candidates.append(info.entry_id)
        elif echo and score + echo >= threshold:
            echoes.append((info, score + echo, reasons, party))
    # Entries that link only because their memo repeats the account name ('repair' in a repairs
    # account) are routine activity in that account. When other entries in the same account and period
    # link on independent evidence (a party, a reference, a document, a distinctive word), the event is
    # identified by those, and the routine entries are context: surfaced, never claimed (a gap they could
    # close is raised as a judgment, see _fit_flags). When nothing more specific links in that account
    # and period, the account-name match is all the evidence there is (a dedicated severance or bad-debt
    # account), so those entries stay candidates.
    independent: dict[str, set[str]] = {}
    for e in t.candidates:
        info = index.by_id[e]
        independent.setdefault(info.entry.account, set()).update(index.labels_of(info.month) or {"*"})
    promoted: list[str] = []
    for info, score, reasons, party in echoes:
        if independent.get(info.entry.account, set()) & (set(index.labels_of(info.month)) or {"*"}):
            t.links[info.entry_id] = LinkInfo(
                entry_id=info.entry_id,
                score=round(score, 2),
                reasons=reasons + ["Context only: same account, and the memo only restates the account name"],
                group=_group_display(info),
                context=True,
            )
            t.echo_context.append(info.entry_id)
        else:
            t.links[info.entry_id] = LinkInfo(entry_id=info.entry_id, score=round(score, 2), reasons=reasons, party=party)
            promoted.append(info.entry_id)
    t.candidates = index.sort_ids(t.candidates + promoted)
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
