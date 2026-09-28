"""Evidence readers for QoE Evidence Review: deterministic rules and an OpenAI-compatible LLM.

Both classes implement ``qoe.ai_base.EvidenceAI``. They read source documents and
management's adjustment narrative and *propose* facts, links, contradictions,
entry classifications, and question wording. They never compute an adjustment
amount and never choose a treatment; the engine does the arithmetic and the
reviewer makes the call.

``RuleBasedEvidenceAI`` is the default (tests, evaluation, offline runs). It is
built from general lexicons and regular expressions, never from knowledge of a
particular deal. Every quote it returns is sliced out of the canonical page text
and then checked with ``verify_quote``; the LLM implementation checks every quote
the model returns the same way. Unverifiable quotes are dropped and counted,
never repaired.
"""

from __future__ import annotations

import bisect
import json
import os
import re
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any, Iterable, Optional

from qoe.ai_base import (
    MIN_QUOTE_CHARS,
    AdjustmentIntent,
    Contradiction,
    EntryClassification,
    EvidenceAI,
    verify_quote,
)
from qoe.money import D, fmt, q2, within
from qoe.periods import add_months, month_end
from qoe.schemas import (
    AdjustmentCategory,
    AdjustmentClaim,
    AmountFact,
    DocFacts,
    EvidenceQuote,
    Flag,
    GLEntry,
    SourceDocument,
    TermFact,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts"
PROMPT_VERSION = "v1"

DOC_TYPES = (
    "invoice",
    "engagement_letter",
    "contract",
    "settlement_agreement",
    "separation_agreement",
    "insurance",
    "correspondence",
    "payroll",
    "memo",
    "other",
)
TERM_KINDS = (
    "monthly_fee",
    "retainer",
    "auto_renew",
    "term_end",
    "installments",
    "ongoing_services",
    "one_time",
    "other",
)
EVENT_TYPES = (
    "litigation",
    "severance",
    "recruiting",
    "transaction",
    "relocation",
    "casualty",
    "owner_expense",
    "owner_comp",
    "it_project",
    "inventory",
    "bad_debt",
    "refinancing",
    "out_of_period",
    "pro_forma_savings",
    "other",
)
# Canonical AmountFact labels the rule reader emits (the LLM prompt uses the same list).
AMOUNT_LABELS = (
    "total_due",
    "subtotal",
    "monthly_fee",
    "retainer",
    "installment",
    "settlement_amount",
    "severance",
    "net_payment",
    "deductible",
    "gross_loss",
    "payoff_amount",
    "prepayment_penalty",
    "base_salary",
    "premium",
    "amount_paid",
    "fee",
    "rate",
    "line",
)
# Term kinds that describe a cost that keeps coming back.
RECURRING_TERM_KINDS = frozenset({"monthly_fee", "retainer", "auto_renew", "ongoing_services", "term_end"})

_SIGNABLE_TYPES = frozenset(
    {"contract", "engagement_letter", "settlement_agreement", "separation_agreement", "other"}
)
_MAX_QUOTE = 320
_MAX_KEY_STATEMENTS = 30

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    """
    a about above after again against all also an and any are as at be because been before being below between both
    but by can could did do does doing down during each few for from further had has have having he her here hers him
    his how i if in into is it its itself just me more most my no nor not now of off on once only or our ours out over
    own same she should so some such than that the their theirs them then there these they this those through to too
    under until up upon very was we were what when where which while who whom why will with within without would you
    your yours per via vs etc including include includes included us
    """.split()
)
# Words that describe any adjustment and therefore do not identify a specific event.
_GENERIC_WORDS = frozenset(
    """
    fee fees expense expenses expensed cost costs charge charges charged adjustment adjustments adjusted addback
    add-back addbacks add back related one-time onetime one time non-recurring nonrecurring non recurring normalization
    normalize normalized normalizing normalise normalised pro forma run-rate management company companys business amount
    amounts total totals period periods paid pay payment payments incurred recorded booked reflect reflects reflected
    removed remove eliminate eliminated ebitda fy ttm year years month months monthly annual annually gl account
    accounts
    acct various certain professional operating operations item items entry entries represents represent associated
    primarily pursuant reported net gross former new prior current other misc miscellaneous general ledger schedule
    basis based claimed claim claims owner owners services service savings level market rate actual actuals portion
    expected full due relates relating incurred remainder see note notes adjust agreement agreements signed executed
    invoice invoices invoiced document documents documented letter support supporting sales tax taxes
    """.split()
)
_STREET_WORDS = frozenset(
    """
    street st avenue ave boulevard blvd road rd drive dr way lane ln parkway pkwy highway hwy suite ste court ct place
    pl circle cir plaza floor
    """.split()
)
# Account-category nouns: fine for linking, too broad to separate one event from another.
_WEAK_KEYWORDS = frozenset(
    """
    legal travel meals entertainment consulting repairs repair maintenance software payroll salary salaries wages
    insurance rent professional advisory compensation personal subscriptions dues vehicle auto office supplies
    """.split()
)
_MONTH_WORDS = frozenset(
    """
    january february march april may june july august september october november december jan feb mar apr jun jul aug
    sep sept oct nov dec monday tuesday wednesday thursday friday saturday sunday
    """.split()
)
_ROLE_WORDS = frozenset(
    """
    ceo cfo coo cto cio vp svp evp president controller founder director manager officer executive chief head sales
    operations finance employee employees staff team partner principal chairman treasurer secretary counsel
    """.split()
)

# Legal-form suffixes close an entity name; organisational words can end one but may continue ("Group, Inc.").
_HARD_SUFFIXES = frozenset(
    {"llp", "l.l.p.", "llc", "l.l.c.", "pllc", "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
     "co.", "ltd", "ltd.", "limited", "lp", "l.p.", "p.c.", "p.a.", "n.a.", "plc"}
)
_SOFT_SUFFIXES = frozenset(
    {"company", "partners", "partnership", "group", "holdings", "associates", "advisors", "advisers", "consultants",
     "cpas", "bank", "insurance", "mutual", "trust", "club", "foundation", "association", "society"}
)
# Organisation suffixes that say nothing about the event ("Club" and "Insurance" do, so they stay keywords).
_NAME_SUFFIX_KEYWORDS = frozenset(
    {"partners", "partnership", "group", "holdings", "associates", "advisors", "advisers", "consultants", "cpas",
     "company", "bank", "mutual", "trust"}
)
_ENTITY_FORM_WORDS = frozenset(
    {"llp", "llc", "pllc", "inc", "incorporated", "corp", "corporation", "co", "company", "ltd", "limited", "lp",
     "pc", "pa", "na", "plc", "group", "holdings", "the", "and", "of", "l", "p", "c"}
)
_NAME_CONNECTORS = frozenset({"&", "and", "of", "de", "la", "du", "van", "von", "der"})
# Capitalised words that can precede a name on a line but are never part of it.
_NAME_STOP = frozenset(
    {"to", "for", "from", "by", "with", "at", "in", "on", "paid", "per", "re", "via", "between", "dear", "attn",
     "attention", "invoice", "bill", "remit", "payable", "pay", "issued", "prepared", "billed", "engaged", "retained",
     "the", "this", "our", "your", "subject", "cc", "sincerely", "regards", "signed", "accepted", "agreed", "and",
     "or", "including", "includes", "a", "an", "is", "was", "are", "were", "as", "if", "that", "which"}
)
_HONORIFICS = frozenset({"mr", "mr.", "mrs", "mrs.", "ms", "ms.", "dr", "dr.", "mx", "mx."})
_CLIENT_ROLES = frozenset(
    {"company", "client", "customer", "employer", "insured", "buyer", "purchaser", "borrower", "licensee", "tenant",
     "lessee", "policyholder", "recipient", "member", "defendant", "releasee", "creditor", "owner"}
)
_VENDOR_ROLES = frozenset(
    {"provider", "service provider", "vendor", "consultant", "contractor", "supplier", "firm", "licensor", "landlord",
     "lessor", "insurer", "carrier", "lender", "executive", "employee", "advisor", "adviser", "agent", "plaintiff",
     "claimant", "releasor", "counsel", "search firm", "debtor"}
)
_ABBREVIATIONS = frozenset(
    {"inc", "co", "corp", "ltd", "llc", "llp", "no", "nos", "mr", "mrs", "ms", "dr", "st", "jr", "sr", "vs", "v",
     "e.g", "i.e", "etc", "approx", "dept", "est", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept",
     "oct", "nov", "dec", "u.s", "p.c", "p.a", "n.a", "fig", "ext", "attn", "l.l.c", "l.p", "p.o", "ave", "blvd",
     "ste", "tel", "ref", "inv", "acct"}
)
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "eighteen": 18, "twenty": 20, "twenty-four": 24, "thirty": 30,
    "thirty-six": 36, "forty-two": 42, "forty-eight": 48, "sixty": 60, "seventy-two": 72,
}

# ---------------------------------------------------------------------------
# Regular expressions
# ---------------------------------------------------------------------------

def _lex(pattern: str, flags: int = re.IGNORECASE) -> re.Pattern[str]:
    """Compile a phrase lexicon so that a space also matches a PDF line wrap."""
    out: list[str] = []
    in_class = escaped = False
    for i, ch in enumerate(pattern):
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif in_class:
            in_class = ch != "]"
        elif ch == "[":
            in_class = True
        elif ch == " ":
            out.append(r"\s" if pattern[i + 1 : i + 2] in ("?", "*", "{") else r"\s+")
            continue
        out.append(ch)
    return re.compile("".join(out), flags)


_MON = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_MONTH_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
    "nov": 11, "dec": 12,
}
_DATE_RE = re.compile(
    rf"\b(?:(?P<m1>{_MON})\.?\s+(?P<d1>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<y1>\d{{4}})"
    rf"|(?P<d2>\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?(?:\s+|-)(?P<m2>{_MON})\.?,?(?:\s+|-)(?P<y2>\d{{4}})"
    rf"|(?P<y3>\d{{4}})-(?P<m3>\d{{1,2}})-(?P<d3>\d{{1,2}})"
    rf"|(?P<m4>\d{{1,2}})/(?P<d4>\d{{1,2}})/(?P<y4>\d{{4}}|\d{{2}}))\b",
    re.IGNORECASE,
)
_MONTH_YEAR_RE = re.compile(rf"\b(?P<m>{_MON})\.?,?\s+(?P<y>(?:19|20)\d{{2}})\b", re.IGNORECASE)
_MONTH_SPAN_RE = re.compile(
    rf"\b(?P<m1>{_MON})\.?\s*(?:–|—|-|through|thru|to)\s*(?P<m2>{_MON})\.?,?\s+(?P<y>(?:19|20)\d{{2}})\b",
    re.IGNORECASE,
)
_DAY_SPAN_RE = re.compile(
    rf"\b(?P<m>{_MON})\.?\s+(?P<d1>\d{{1,2}})\s*(?:–|—|-|through|to)\s*(?P<d2>\d{{1,2}}),?\s+(?P<y>\d{{4}})\b",
    re.IGNORECASE,
)
_CROSS_SPAN_RE = re.compile(
    rf"\b(?P<m1>{_MON})\.?\s+(?P<d1>\d{{1,2}})(?:,?\s+(?P<y1>\d{{4}}))?\s*(?:–|—|-|through|thru|to)\s*"
    rf"(?P<m2>{_MON})\.?\s+(?P<d2>\d{{1,2}}),?\s+(?P<y2>\d{{4}})\b",
    re.IGNORECASE,
)
_WEEKDAY_RE = re.compile(r"\b(?:mon|tues?|wed(?:nes)?|thu(?:rs)?|fri|sat(?:ur)?|sun)(?:day)?\b\.?,?", re.IGNORECASE)
_QUARTER_RE = re.compile(r"\bQ(?P<q>[1-4])\s*(?:FY)?\s*'?(?P<y>(?:19|20)\d{2}|\d{2})\b")
_MONTH_WORD_RE = re.compile(rf"\b{_MON}\b\.?", re.IGNORECASE)

_CUR_MONEY_RE = re.compile(
    r"(?:\$|\bUSD\s?)\s?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\d,]*\d)"
    r"(?:\s?(?P<mult>million|thousand|mm|k)\b)?",
    re.IGNORECASE,
)
_BARE_MONEY_RE = re.compile(r"(?<![\w$.,/-])(?P<num>\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2})(?![\w.%/-]|,\d)")

_AMOUNT_LABEL_RES: list[tuple[str, re.Pattern[str]]] = [
    (label, _lex(pattern, re.IGNORECASE))
    for label, pattern in (
        ("net_payment", r"net (?:claim )?payment|net amount (?:payable|paid)|amount of (?:this|the) (?:payment|check)"
                        r"|net (?:settlement|recovery|proceeds)|payment amount"),
        ("deductible", r"deductible"),
        ("gross_loss", r"gross (?:covered )?(?:loss|claim)|(?:total|adjusted|covered) (?:covered )?loss"
                       r"|amount of (?:the )?loss|replacement cost"),
        ("settlement_amount", r"settlement (?:amount|payment|sum)|in settlement of|\bsum of\b"),
        ("severance", r"severance"),
        ("payoff_amount", r"payoff (?:amount|balance)|total payoff|amount required to (?:pay off|satisfy)"),
        ("prepayment_penalty", r"prepayment (?:penalty|premium|fee)"),
        ("retainer", r"retainer"),
        ("monthly_fee", r"monthly (?:fee|charge|subscription|service fee|payment|dues|rent|license)|fee per month"),
        ("base_salary", r"base salary|annual salary|base compensation|\bsalary\b"),
        ("installment", r"installments?"),
        ("subtotal", r"sub-?total"),
        ("total_due", r"total (?:amount )?due|amount due|balance due|amount payable|please remit|invoice total"
                      r"|total (?:this )?invoice|total charges|total fees|grand total|total amount|\btotal\b"),
        ("premium", r"premium"),
        ("amount_paid", r"amount paid|total paid|\bpaid\b|registration fee|\bcharged\b"),
        ("fee", r"\bfees?\b"),
    )
]
_MONTHLY_AFTER_RE = _lex(r"^[ \t]*(?:per month|/\s?mo(?:nth)?\b|a month\b|each month|every month|monthly\b)", re.I)
_HOURLY_AFTER_RE = _lex(r"^[ \t]*(?:per hour|/\s?h(?:ou)?r\b|an hour|hourly)", re.I)
_SETTLEMENT_AFTER_RE = _lex(r"^[ \t]*\)?[ \t]*\(?[ \t]*(?:the\s+)?[\"“]settlement (?:amount|payment)", re.I)
_INSTALLMENT_WORD_RE = _lex(r"\binstall?ments?\b", re.I)
_MONTHLY_CUE_RE = _lex(r"per month|/\s?mo(?:nth)?\b|a month\b|each month|every month|\bmonthly\b", re.I)

_AUTO_RENEW_RE = _lex(
    r"renews? automatically|automatically renew(?:s|ed)?|auto-?renew(?:s|al|ing)?"
    r"|shall renew for (?:successive|additional)"
    r"|evergreen",
    re.I,
)
_ONGOING_RE = _lex(
    r"until terminated|continu(?:e|es|ing) (?:in effect )?until (?:terminated|cancell?ed)|month-to-month"
    r"|on an ongoing basis|ongoing (?:services|support|basis)|remain in (?:full force and )?effect until"
    r"|until (?:either party )?(?:terminates|cancels)",
    re.I,
)
_ONE_TIME_RE = _lex(
    r"one-time|one time (?:fee|payment|charge|cost)|non-?recurring|single payment|lump[- ]sum"
    r"|in full and final settlement|full and final|in full settlement|in full satisfaction|fully and finally",
    re.I,
)
_INSTALLMENTS_RE = _lex(
    r"(?:payable|paid|made|due|payment)\s+(?:\w+\s+){0,3}?in\s+(?P<n>[a-z]+(?:-[a-z]+)?|\d+)\s*(?:\(\d+\)\s*)?"
    r"(?:equal\s+)?(?:consecutive\s+)?(?:monthly\s+|quarterly\s+|annual\s+|semi-monthly\s+)?install?ments"
    r"|\binstall?ments?\b",
    re.I,
)
_TERM_LENGTH_RE = _lex(
    r"(?:(?:\b[a-z]+(?:-[a-z]+)?\s*\(\s*)?\b(?P<n1>\d{1,3}|[a-z]+(?:-[a-z]+)?)\s*\)?[\s-]*(?P<u1>month|year)s?\b"
    r"[^.;]{0,40}?\bterm\b"
    r"|\bterm(?:\s+of|\s*[:\-])?\s+(?:[a-z]+(?:-[a-z]+)?\s*\(\s*)?(?P<n2>\d{1,3}|[a-z]+(?:-[a-z]+)?)\s*\)?\s*"
    r"(?P<u2>month|year)s?\b)"
    r"[^.;]{0,40}?\b(?:commencing|beginning|starting|effective|from)\s+(?:on\s+)?",
    re.I,
)
_TERM_EXPIRY_RE = _lex(
    r"\b(?:term|agreement)\b[^.;]{0,80}?\b(?:expires?|ends?|terminates?|shall end|will end)\s+on\s+"
    r"|\bexpiration date\s*[:\-]?\s*",
    re.I,
)

_TERM_WORD_RE = re.compile(r"\b(?:initial |renewal |lease |agreement |contract )?term\b(?! of payment)(?!s\b)", re.I)
_RECURRENCE_RE = _lex(
    r"consistent with (?:the )?(?:prior|previous) (?:years?|periods?)|as in (?:prior|previous) (?:years|periods)"
    r"|(?:each|every) (?:year|quarter)|year after year|\bannually\b|\brecurring\b|\brecurs\b|subscription"
    r"|\bmonthly fee\b|\bmonth \d+ of \d+\b"
    r"|annual (?:subscription|fee|renewal|license|licence|maintenance|contract|service|retainer|charge|count"
    r"|physical|inventory|review|program)"
    r"|renews? automatically|automatically renew|auto-?renew|evergreen|month-to-month|on an ongoing basis"
    r"|ongoing (?:basis|services?|support)|until terminated|\broutine\b|in the (?:normal|ordinary) course",
    re.I,
)
_ONE_TIME_STMT_RE = _lex(
    r"one-time|one time|non-?recurring|isolated|unusual|will not recur|not expected to recur"
    r"|full and final settlement|in full satisfaction",
    re.I,
)
_BUSINESS_PURPOSE_RE = _lex(
    r"business purpose|on behalf of|attending (?:company|organi[sz]ation)|registered (?:company|attendee)|attendee"
    r"|conference|summit|trade ?show|\bexpo\b|convention|seminar|training|certification|supplier|vendor visit"
    r"|(?:plant|factory|facility|site) (?:visit|tour)|customer (?:visit|meeting)|client (?:visit|meeting)"
    r"|dealer (?:meeting|summit|conference)|sales meeting|board meeting|agenda",
    re.I,
)
_PLAN_RE = _lex(
    r"\bwe (?:plan|intend|expect|anticipate) to\b|\btargeting\b|\bplanned\b"
    r"|\bwill be (?:eliminated|reduced|implemented)\b"
    r"|\bprojected\b|\bexpected to (?:save|reduce)\b|\bhave not (?:yet )?(?:started|begun|been)\b|\bnot yet\b",
    re.I,
)
_RECOVERY_RE = _lex(
    r"(?:insurer|carrier) (?:shall|will) (?:pay|fund|reimburse)"
    r"|(?:paid|funded) (?:directly )?by [^.;]{0,60}?\b(?:insurer|carrier|insurance)"
    r"|on the company'?s behalf|no obligation to fund|net (?:claim )?payment|deductible|proceeds|reimburse",
    re.I,
)
_PERSONAL_RE = _lex(
    r"\bpersonal\b|\bfamily\b|\bspouse\b|\bwife\b|\bhusband\b|\bvacation\b|country club|club dues|\bhousehold\b",
    re.I,
)
_TERMINATION_RE = _lex(
    r"separation date|last day of employment|terminat(?:ed|ion) of (?:employment|the executive)|\bresign", re.I
)
_KEY_STATEMENT_RES = (
    _RECURRENCE_RE,
    _ONE_TIME_STMT_RE,
    _BUSINESS_PURPOSE_RE,
    _PLAN_RE,
    _RECOVERY_RE,
    _PERSONAL_RE,
    _TERMINATION_RE,
)
# Recurrence cues that come from payment mechanics rather than from the cost itself.
_INSTALLMENT_CONTEXT_RE = _lex(r"install?ments?|severance|settlement|separation", re.I)
# Statements that state the purpose outright rank ahead of mere mentions of an event.
_BUSINESS_STRONG_RE = _lex(
    r"business purpose|purpose of (?:the )?(?:visit|trip|travel|attendance)|attending (?:company|organi[sz]ation)"
    r"|visiting company|on behalf of|registered company"
)
_RECURRENCE_STRONG_RE = _lex(
    r"consistent with (?:the )?(?:prior|previous)|subscription|renews? automatically|automatically renew|monthly fee"
    r"|until terminated|each year|every year|month \d+ of \d+"
)
_BUSINESS_MEMO_RE = _lex(
    r"conference|summit|trade ?show|\bexpo\b|convention|seminar|training|certification|supplier|vendor visit"
    r"|(?:plant|factory|facility|site|customer|client|job ?site) (?:visit|tour|meeting)|dealer|sales (?:call|meeting)"
    r"|association meeting|board meeting|business (?:trip|travel|meeting)|recruiting (?:trip|fair)|job fair",
    re.I,
)
_CONTRARY_THEME_RE = _lex(
    r"monthly (?:retainer|fee|service|subscription)|general (?:corporate|retainer|matters?)|subscription|\broutine\b"
    r"|\brecurring\b|\bongoing\b",
    re.I,
)
_COMPLETED_CLAIM_RE = _lex(
    r"(?:were|was|have been|has been) (?:eliminated|terminated|reduced|completed|let go|laid off)"
    r"|(?:eliminated|completed|terminated) (?:in|during|on) ",
    re.I,
)

_REF_LABEL = (
    r"(?:invoice|inv\.?|matter|claim|policy|case|file|agreement|contract|msa|sow|purchase order|order|po|p\.o\."
    r"|reference|ref\.?|loan|confirmation|registration|project|job|work order|statement|check|cheque|bill"
    r"|quote|estimate|proposal|certificate|permit|ticket)"
)
_REF_RE = re.compile(
    rf"\b(?P<label>{_REF_LABEL})\s*(?P<marker>(?:no\.?|nos\.?|number|num\.?|#|id)\s*)?[:#]?\s*"
    r"(?P<val>(?=[A-Z0-9/.:-]*\d)[A-Z0-9][A-Z0-9/.:-]*[A-Z0-9]|\d)",
    re.IGNORECASE,
)
# Everyday words that only introduce a reference when followed by "No." / "#" ("file 3.00" is not one).
_WEAK_REF_LABELS = frozenset(
    {"file", "statement", "check", "cheque", "bill", "order", "reference", "ref", "registration", "confirmation",
     "document", "permit", "ticket", "certificate", "quote", "estimate", "proposal"}
)
_CODE_RE = re.compile(r"\b[A-Z]{2,6}-\d{2,}(?:-[A-Z0-9]+)*\b")
_REF_KIND = {
    "invoice": "invoice", "inv": "invoice", "inv.": "invoice", "bill": "invoice", "statement": "invoice",
    "matter": "matter", "claim": "claim", "policy": "policy", "case": "case", "file": "case",
    "agreement": "contract", "contract": "contract", "msa": "contract", "sow": "contract",
    "order": "order", "purchase order": "order", "po": "order", "p.o.": "order",
    "reference": "reference", "ref": "reference", "ref.": "reference", "loan": "loan",
    "confirmation": "confirmation", "registration": "confirmation", "project": "project", "job": "project",
    "work order": "project", "check": "check", "cheque": "check", "quote": "quote", "estimate": "quote",
    "proposal": "quote", "certificate": "other", "permit": "other", "ticket": "other",
}
# Reference kinds that name an event or arrangement (as opposed to a single bill).
_EVENT_REF_KINDS = frozenset({"matter", "claim", "case", "project", "contract", "policy", "loan", "order"})

_TYPE_TITLE_RULES: list[tuple[str, re.Pattern[str]]] = [
    (doc_type, _lex(pattern, re.IGNORECASE))
    for doc_type, pattern in (
        ("settlement_agreement", r"settlement (?:agreement|and (?:mutual )?release)|release and settlement"
                                 r"|settlement & release|agreement of settlement"),
        ("separation_agreement", r"separation (?:agreement|and (?:general )?release)|severance agreement"
                                 r"|separation & release"),
        ("engagement_letter", r"engagement letter|letter of engagement|engagement agreement|terms of engagement"
                              r"|\bengagement of\b"),
        ("insurance", r"claim (?:settlement|payment|determination|closing|summary)|proof of loss|statement of loss"
                      r"|insurance claim|explanation of benefits|certificate of insurance"
                      r"|policy (?:declarations|renewal)"),
        ("payroll", r"payroll (?:register|summary|journal|report)|pay ?stub|earnings statement|pay statement"),
        ("memo", r"\bmemo(?:randum)?\b"),
        ("invoice", r"\binvoice\b|\bbill\b|statement of account|\breceipt\b|billing statement|member statement"
                    r"|account statement"),
        ("contract", r"agreement|contract|statement of work|\bsow\b|terms and conditions|\blease\b|order form"
                     r"|addendum|amendment"),
    )
]
_TYPE_BODY_RULES: list[tuple[str, re.Pattern[str]]] = [
    (doc_type, _lex(pattern, re.IGNORECASE))
    for doc_type, pattern in (
        ("invoice", r"invoice (?:no|number|#|date)|amount due|total due|balance due|\bremit\b|bill to"),
        ("insurance", r"deductible|\binsured\b|policy (?:no|number|#)|adjuster|date of loss"),
        ("engagement_letter", r"scope of (?:services|engagement|work)|we are pleased to|engagement"),
        ("contract", r"hereby agree|terms and conditions|in witness whereof|the parties|this agreement"),
        ("payroll", r"gross pay|net pay|pay period|withholding"),
    )
]
_TITLE_WORD_RE = _lex(
    r"\b(?:invoice|statement|agreement|contract|letter|memo(?:randum)?|notice|confirmation|registration|agenda|release"
    r"|proposal|order|receipt|report|summary|register|addendum|amendment|engagement|itinerary|policy|claim|settlement"
    r"|payoff|quote|estimate)\b",
    re.IGNORECASE,
)
_TITLE_NOUNS = frozenset(
    {"invoice", "statement", "agreement", "contract", "letter", "memo", "memorandum", "notice", "confirmation",
     "agenda", "release", "proposal", "order", "receipt", "report", "summary", "register", "addendum", "amendment",
     "itinerary", "policy", "settlement", "estimate", "quote", "bankruptcy"}
)
_FIELD_LINE_RE = re.compile(r"^\s*[A-Za-z][\w .#/&'()-]{0,40}:\s*\S")
_BULLET_RE = re.compile(r"^\s*(?:[-•*▪·]\s|\d{1,2}[.)]\s|\(?[a-z]\)\s)")
_EMAIL_HEADER_RE = re.compile(r"^\s*(from|to|subject|date|sent|cc)\s*:\s*\S", re.IGNORECASE)
_MEMO_HEAD_RE = re.compile(r"^\s*(?:internal\s+|interoffice\s+)?memo(?:randum)?\b", re.IGNORECASE)
_SUBJECT_RE = re.compile(r"^\s*(?:re|subject|title)\s*:\s*(?P<val>.+)$", re.IGNORECASE)
_RECIPIENT_LABEL_RE = re.compile(
    r"^\s*(?:bill(?:ed)? to|sold to|ship to|invoice to|to|attn|attention|client|customer|insured|named insured"
    r"|policyholder|prepared for|attendees?|attending company|registrant|registered company|company|member|lessee"
    r"|borrower|creditor|account name)\s*[:\-]\s*(?P<val>.*)$",
    re.IGNORECASE,
)
_ISSUER_LABEL_RE = re.compile(
    r"^\s*(?:from|vendor|supplier|payee|remit(?:tance)? to|issued by|insurer|carrier|insurance company|provider"
    r"|firm|consultant|contractor|lender|servicer|hosted by|organi[sz]er|organi[sz]ed by|presented by|sponsor"
    r"|landlord|lessor|pay to|debtor)\s*[:\-]\s*(?P<val>.+)$",
    re.IGNORECASE,
)
_ROLE_RE = re.compile(
    r"\(\s*(?:the\s+|each\s+a\s+|hereinafter\s+(?:referred\s+to\s+as\s+)?)?[\"“]([A-Z][A-Za-z ]{1,30}?)[\"”]\s*\)"
)
_SIGNOFF_RE = re.compile(r"^\s*(?:sincerely|very truly yours|regards|best regards|yours truly|respectfully)\b", re.I)
_DOC_DATE_LABEL_RE = re.compile(
    r"^\s*(?:(?:invoice|statement|issue|letter|notice|document|memo|bill|effective|agreement|report|confirmation)\s+)?"
    r"(?:date|dated|sent)\s*[:\-]?\s*",
    re.IGNORECASE,
)
_ISSUED_RE = re.compile(r"\b(?:issued(?: on)?|issue date|date issued|dated)\s*[:\-]?\s*", re.IGNORECASE)
_DATED_RE = _lex(
    r"(?:\bdated|entered into|made(?: and entered into)?|executed|effective)\s+(?:as of\s+|on\s+)?(?:this\s+)?$",
    re.IGNORECASE,
)
_NON_DOC_DATE_CONTEXT_RE = _lex(
    r"(?:due|through|thru|period|from|until|loss|term|commenc\w*|expir\w*|birth|hire|separation|start|end)\W*$",
    re.IGNORECASE,
)
_SP_CUE_RE = _lex(
    r"service period|period of (?:service|performance)|services? (?:rendered|performed|provided)|billing period"
    r"|coverage period|policy period|for the period|period covered|work performed|event dates?|conference dates?"
    r"|travel dates?|dates? of (?:service|travel|visit|event|attendance)|visit dates?|\bperiod\b\s*:",
    re.IGNORECASE,
)
_SP_END_ONLY_RE = _lex(r"services? (?:rendered|performed|provided) (?:through|thru|to|until|up to)\s+$", re.I)
_SP_MONTH_ONLY_RE = _lex(
    r"(?:for the month of|services? (?:rendered|performed|provided) (?:in|during)|billing period\s*:?"
    r"|service month\s*:?)\s+$",
    re.IGNORECASE,
)
_SINGLE_EVENT_DATE_RE = _lex(
    r"(?:(?:event|conference|visit|travel|trip|meeting) dates?|dates? of (?:the )?(?:event|visit|travel|attendance"
    r"|meeting))\s*[:\-]?\s*$"
)
_RANGE_SEP_RE = re.compile(r"^\s*(?:–|—|-|to|through|thru|until|and)\s*$", re.IGNORECASE)
_DRAFT_MARK_RE = re.compile(r"\bDRAFT\b")
_DRAFT_PHRASE_RE = _lex(
    r"not (?:yet )?executed|unexecuted|for discussion purposes only|draft for discussion"
    r"|subject to (?:further )?revision"
    r"|preliminary draft",
    re.IGNORECASE,
)
_SIGNED_RE = _lex(
    r"/s/|^\s*(?:signed|signature|executed)(?: by)?\s*:\s*(?!_)[A-Za-z]|electronically signed|docusign envelope",
    re.IGNORECASE | re.MULTILINE,
)
_BLANK_SIGNATURE_RE = re.compile(
    r"^\s*(?:(?!(?:date|title|name|print(?:ed)? name)\s*:)[A-Za-z][A-Za-z .'/&,-]{0,40}:\s*)?_{4,}\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_UNSIGNED_RE = _lex(r"\bunsigned\b|\bnot (?:been )?signed\b|\bnot (?:yet )?(?:been )?executed\b|\bunexecuted\b", re.I)

_NONRECURRING_CLAIM_RE = _lex(
    r"one[- ]time|non[- ]?recurring|nonrecurring|will not recur|not expected to recur|\bisolated\b|\binfrequent\b"
    r"|\bunusual\b",
    re.IGNORECASE,
)
_PERSONAL_CLAIM_RE = _lex(
    r"\bpersonal\b|non-?business|not business[- ]related|owner(?:'s|’s)? (?:family|household)|family members?"
    r"|\bspouse\b|\bperquisites?\b|\bperks?\b|discretionary",
    re.IGNORECASE,
)
_PRO_FORMA_CLAIM_RE = _lex(
    r"pro[- ]forma|run[- ]rate|\bplanned\s+(?:\w+\s+){0,3}?(?:reduction|savings?|elimination|headcount|cuts?|synerg\w*"
    r"|consolidation)|\b(?:expected|anticipated|projected)\s+(?:cost\s+)?savings",
    re.IGNORECASE,
)
_NORMALIZATION_CLAIM_RE = _lex(
    r"normali[sz]|\bto market\b|market (?:rate|level|salary|compensation|pay)", re.IGNORECASE
)
_NORMALIZED_CUE_RE = _lex(
    r"market(?:[- ]based)?(?:\s+(?:rate|level|salary|compensation|pay))?|normali[sz]\w*|reduced|reset", re.IGNORECASE
)
_INITIAL_NAME_RE = re.compile(r"\b[A-Z]\.(?:\s?[A-Z]\.)?\s?[A-Z][a-z]+(?:[-'’][A-Z][a-z]+)?\b")
_AMPERSAND_NAME_RE = re.compile(r"\b[A-Z][a-z]+ (?:&|and) [A-Z][a-z]+\b")
_CAP_RUN_RE = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}\b")

_EVENT_LEXICON: list[tuple[str, re.Pattern[str]]] = [
    (event, _lex(pattern, re.IGNORECASE))
    for event, pattern in (
        ("refinancing", r"refinanc|loan (?:payoff|origination|fees?)|prepayment (?:penalty|premium)"
                        r"|debt (?:extinguishment|issuance)|unamortized (?:loan|debt|financing)|payoff of (?:the )?"
                        r"(?:term )?loan"),
        ("litigation", r"litigation|lawsuit|\bsuit\b|legal (?:settlement|dispute|defen[cs]e)|\bdispute\b|arbitration"
                       r"|\bv\.\s|\bvs\.?\s|plaintiff|defendant|wrongful"),
        ("severance", r"severance|separation (?:agreement|pay|payment)|termination (?:pay|benefits)|\bseparated\b"),
        ("recruiting", r"recruit|search fee|executive search|retained search|placement fee|headhunt|search firm"),
        ("transaction", r"transaction|sell-side|sale process|due diligence|\bm&a\b|quality of earnings"
                        r"|investment bank|deal (?:costs?|fees?)|exit (?:readiness|process)|banker"),
        ("relocation", r"relocat|\bmov(?:e|ing)\b|build-?out|new (?:facility|warehouse|office|location)"),
        ("casualty", r"storm|hurricane|flood|fire damage|\bfire\b|casualty|natural disaster|tornado|insurance claim"
                     r"|water damage|wind damage"),
        ("owner_comp", r"(?:owner|officer|executive|ceo|founder)(?:'s|’s)? (?:compensation|salary|pay|wages)"
                       r"|compensation normali|market (?:rate )?(?:compensation|salary)"),
        ("owner_expense", r"personal|owner(?:'s|’s)? (?:expenses?|perquisites|perks)|discretionary|country club"
                          r"|club dues|\bfamily\b"),
        ("it_project", r"implementation|software|\berp\b|system (?:conversion|migration|implementation)|go-?live"
                       r"|it project|conversion|migration"),
        ("inventory", r"inventory|obsolete|obsolescence|shrink|physical count|write-?down of (?:stock|inventory)"),
        ("bad_debt", r"bad debt|bankrupt|uncollectible|doubtful accounts?|customer (?:default|insolvency)"
                     r"|chapter (?:7|11)"),
        ("out_of_period", r"prior[- ](?:year|period)|out[- ]of[- ]period|true-?up|catch-?up"),
        ("pro_forma_savings", r"pro[- ]forma|run[- ]rate|savings|headcount reduction|synerg|cost reduction"
                              r"|eliminat(?:e|ion) of (?:\w+ )?(?:positions|roles|ftes?)"),
    )
]
_EVENT_LABEL = {
    "litigation": "litigation", "severance": "severance", "recruiting": "recruiting", "transaction": "transaction",
    "relocation": "relocation", "casualty": "casualty loss", "owner_expense": "owner expense",
    "owner_comp": "owner compensation", "it_project": "IT project", "inventory": "inventory",
    "bad_debt": "bad debt", "refinancing": "refinancing", "out_of_period": "prior-period",
    "pro_forma_savings": "pro forma savings", "other": "other",
}


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------


def _month_number(name: str) -> Optional[int]:
    return _MONTH_NUM.get(name.lower().rstrip(".")[:3])


def _safe_date(y: int, m: int, d: int) -> Optional[date]:
    try:
        return date(y, m, d)
    except ValueError:
        return None


@dataclass(frozen=True)
class _DateHit:
    start: int
    end: int
    iso: str


def _find_dates(text: str, pos: int = 0, endpos: Optional[int] = None) -> list[_DateHit]:
    hits: list[_DateHit] = []
    for m in _DATE_RE.finditer(text, pos, len(text) if endpos is None else endpos):
        g = m.groupdict()
        if g["m1"]:
            y, mo, d = int(g["y1"]), _month_number(g["m1"]), int(g["d1"])
        elif g["m2"]:
            y, mo, d = int(g["y2"]), _month_number(g["m2"]), int(g["d2"])
        elif g["y3"]:
            y, mo, d = int(g["y3"]), int(g["m3"]), int(g["d3"])
        else:
            yy = int(g["y4"])
            y, mo, d = (yy + 2000 if yy < 100 else yy), int(g["m4"]), int(g["d4"])
        dt = _safe_date(y, mo, d) if mo else None
        if dt is not None and 1900 <= dt.year <= 2100:
            hits.append(_DateHit(m.start(), m.end(), dt.isoformat()))
    return hits


def _parse_date(value: str) -> Optional[str]:
    hits = _find_dates(value)
    return hits[0].iso if hits else None


def _month_year_hits(text: str, dates: list[_DateHit]) -> list[tuple[int, int, str]]:
    """(start, end, 'YYYY-MM') for month-year mentions not inside a full date."""
    out: list[tuple[int, int, str]] = []
    for m in _MONTH_YEAR_RE.finditer(text):
        if any(h.start <= m.start() < h.end or m.start() <= h.start < m.end() for h in dates):
            continue
        mo = _month_number(m.group("m"))
        if mo:
            out.append((m.start(), m.end(), f"{int(m.group('y')):04d}-{mo:02d}"))
    return out


def _iso_month_start(month: str) -> str:
    return f"{month}-01"


def _iso_month_end(month: str) -> str:
    return month_end(month).isoformat()


def _term_end(start: date, n: int, unit: str) -> date:
    months = n * 12 if unit.lower().startswith("year") else n
    ym = add_months(f"{start.year:04d}-{start.month:02d}", months)
    last_day = month_end(ym).day
    anniversary = date(int(ym[:4]), int(ym[5:7]), min(start.day, last_day))
    return anniversary - timedelta(days=1)


def _number(word: str) -> Optional[int]:
    word = word.lower()
    if word.isdigit():
        return int(word)
    return _NUMBER_WORDS.get(word)


def _money_hits(text: str, pos: int = 0, endpos: Optional[int] = None, *, bare: bool = False):
    """Yield (start, end, magnitude, has_currency) for money; bare 2-dp numbers only when asked."""
    end_limit = len(text) if endpos is None else endpos
    for m in _CUR_MONEY_RE.finditer(text, pos, end_limit):
        value = D(m.group("num"))
        mult = (m.group("mult") or "").lower()
        if mult in ("k", "thousand"):
            value *= 1000
        elif mult in ("million", "mm"):
            value *= 1000000
        yield m.start(), m.end(), abs(value), True
    if bare:
        for m in _BARE_MONEY_RE.finditer(text, pos, end_limit):
            if m.start() > 0 and text[m.start() - 1] in "$":
                continue
            yield m.start(), m.end(), abs(D(m.group("num"))), False


def _usd(value: object) -> str:
    """Human money format for question text: $84,500 / $1,234.56."""
    d = abs(q2(D(value)))
    s = f"{d:,.2f}"
    if s.endswith(".00"):
        s = s[:-3]
    return f"${s}"


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _token_in(needle: str, haystack: str) -> bool:
    if not needle or not haystack:
        return False
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(needle)}(?![A-Za-z0-9])", haystack, re.IGNORECASE) is not None


def _name_tokens(name: Optional[str]) -> set[str]:
    if not name:
        return set()
    toks = re.findall(r"[a-z0-9]+", name.lower().replace("&", " and "))
    return {t for t in toks if t not in _ENTITY_FORM_WORDS and len(t) >= 2}


def _cp_match(a: Optional[str], b: Optional[str]) -> bool:
    """Normalized token overlap between two counterparty names."""
    ta, tb = _name_tokens(a), _name_tokens(b)
    if not ta or not tb:
        return False
    overlap = ta & tb
    return bool(overlap) and len(overlap) / min(len(ta), len(tb)) >= 0.5


def _distinct_tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z][a-z0-9'’-]{3,}", text.lower())
        if t not in _STOPWORDS and t not in _GENERIC_WORDS and t not in _MONTH_WORDS
    }


def _filename_title(doc_id: str) -> str:
    stem = Path(doc_id).stem
    stem = re.sub(r"^[\d.]+\s+", "", stem)
    return _norm_space(stem.replace("_", " "))


def _labeled_refs(text: str) -> list[tuple[str, str]]:
    """(kind, value) reference numbers introduced by a label ("Matter 4410", "Claim No. XY-00-123")."""
    out: list[tuple[str, str]] = []
    for m in _REF_RE.finditer(text):
        label = re.sub(r"\s+", " ", m.group("label").lower())
        value = m.group("val").rstrip(".:-/")
        marker = bool(m.group("marker"))
        if len(value) < 3 and not (marker and value.isdigit()):
            continue
        if re.fullmatch(r"\d+\.\d+", value) or (label.rstrip(".") in _WEAK_REF_LABELS and not marker):
            continue
        if _parse_date(value) is not None or re.fullmatch(r"\d{1,2}/\d{1,2}", value):
            continue
        if not marker and re.fullmatch(r"(?:19|20)\d{2}", value):
            continue
        kind = _REF_KIND.get(label, _REF_KIND.get(label.rstrip("."), "reference"))
        out.append((kind, value))
    return out


def _reference_values(text: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for _, value in _labeled_refs(text):
        if value.lower() not in seen:
            seen.add(value.lower())
            values.append(value)
    for m in _CODE_RE.finditer(text):
        value = m.group()
        if re.fullmatch(r"(?:FY|Q[1-4]|TTM|H[12])-\d+", value) or value.lower() in seen:
            continue
        if any(value.lower() in v.lower() or v.lower() in value.lower() for v in values):
            continue
        seen.add(value.lower())
        values.append(value)
    return values


# ---------------------------------------------------------------------------
# Page model: segments and verbatim quotes
# ---------------------------------------------------------------------------


def _line_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"[^\n]+", text):
        s, e = m.start(), m.end()
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if e > s:
            spans.append((s, e))
    return spans


def _continues(prev: str, nxt: str) -> bool:
    """Whether a line is a wrapped continuation of the previous line's sentence."""
    if _FIELD_LINE_RE.match(nxt) or _BULLET_RE.match(nxt) or _EMAIL_HEADER_RE.match(nxt):
        return False
    if prev.endswith((".", "!", "?", ":", ";")) or _FIELD_LINE_RE.match(prev):
        return False
    if prev[-1:].isdigit() and nxt[:1].isupper():
        return False  # a table row ends in a figure; the next capitalised line starts something new
    if nxt[:1].islower():
        return True
    if _core(prev.split()[-1]) in _TITLE_NOUNS:
        return False  # a heading such as "... Travel Confirmation" is not wrapped prose
    return len(prev) >= 45


_SENT_END_RE = re.compile(r"[.!?][\"”’)\]]*(?=\s+[\"“(\[]?[A-Z0-9$])")


def _split_sentences(text: str, start: int, end: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    cur = start
    for m in _SENT_END_RE.finditer(text, start, end):
        if text[m.start()] == ".":
            before = re.search(r"(\S+)$", text[cur : m.start()])
            token = before.group(1).lstrip("(\"“'").lower() if before else ""
            if token in _ABBREVIATIONS or (len(token) == 1 and token.isalpha()):
                continue
        out.append((cur, m.end()))
        cur = m.end()
    out.append((cur, end))
    trimmed: list[tuple[int, int]] = []
    for s, e in out:
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if e > s:
            trimmed.append((s, e))
    return trimmed


def _segments(text: str, lines: list[tuple[int, int]]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    cur: Optional[tuple[int, int]] = None
    last: Optional[tuple[int, int]] = None
    for s, e in lines:
        if (
            cur is not None
            and last is not None
            and text.count("\n", last[1], s) == 1
            and _continues(text[last[0] : last[1]], text[s:e])
        ):
            cur = (cur[0], e)
        else:
            if cur is not None:
                blocks.append(cur)
            cur = (s, e)
        last = (s, e)
    if cur is not None:
        blocks.append(cur)
    segments: list[tuple[int, int]] = []
    for bs, be in blocks:
        segments.extend(_split_sentences(text, bs, be))
    return segments


class _Page:
    """One canonical page with line/sentence spans; every quote is a slice of ``text``."""

    def __init__(self, doc_id: str, number: int, text: str) -> None:
        self.doc_id = doc_id
        self.number = number
        self.text = text
        self.lines = _line_spans(text)
        self.segments = _segments(text, self.lines)
        self._line_starts = [s for s, _ in self.lines]
        self._seg_starts = [s for s, _ in self.segments]

    def line_texts(self) -> list[str]:
        return [self.text[s:e] for s, e in self.lines]

    def _span_at(self, spans: list[tuple[int, int]], starts: list[int], pos: int) -> Optional[tuple[int, int]]:
        i = bisect.bisect_right(starts, pos) - 1
        if 0 <= i < len(spans) and spans[i][0] <= pos < spans[i][1]:
            return spans[i]
        return None

    def line_at(self, pos: int) -> tuple[int, int]:
        return self._span_at(self.lines, self._line_starts, pos) or (pos, pos)

    def segment_at(self, pos: int) -> tuple[int, int]:
        return self._span_at(self.segments, self._seg_starts, pos) or self.line_at(pos)

    def quote(self, start: int, end: int, *, prefer_line: bool = False, max_len: int = _MAX_QUOTE) -> EvidenceQuote:
        """Smallest natural unit (line or sentence) containing [start, end), sliced verbatim."""
        candidates = [self.line_at(start), self.segment_at(start)]
        if not prefer_line:
            candidates.reverse()
        for s, e in candidates:
            if s <= start and end <= e and e - s <= max_len:
                return self._q(s, e)
        base_s, base_e = self.segment_at(start)
        if not (base_s <= start and end <= base_e):
            base_s, base_e = min(start, base_s), max(end, base_e)
        s = max(base_s, start - 140)
        e = min(base_e, end + 140)
        if s > base_s:
            space = self.text.find(" ", s, start)
            s = space + 1 if space != -1 else s
        if e < base_e:
            space = self.text.rfind(" ", end, e)
            e = space if space != -1 else e
        while s < start and self.text[s].isspace():
            s += 1
        while e > end and self.text[e - 1].isspace():
            e -= 1
        return self._q(s, e)

    def _q(self, s: int, e: int) -> EvidenceQuote:
        # A unit shorter than verify_quote accepts ("$950" alone on a line) is widened to the
        # neighbouring lines until it proves something.
        while len(self.text[s:e].strip()) < MIN_QUOTE_CHARS and (s > 0 or e < len(self.text)):
            if e < len(self.text):
                nxt = self.text.find("\n", e + 1)
                e = len(self.text) if nxt == -1 else nxt
            else:
                prev = self.text.rfind("\n", 0, max(s - 1, 0))
                s = 0 if prev == -1 else prev + 1
        return EvidenceQuote(doc_id=self.doc_id, page=self.number, quote=self.text[s:e])


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


def _core(token: str) -> str:
    return token.strip(",;:()[]\"“”'’").lower()


def _is_suffix(token: str) -> bool:
    if not token[:1].isupper():
        return False
    core = _core(token)
    return core in _HARD_SUFFIXES or core.rstrip(".") in _HARD_SUFFIXES or core in _SOFT_SUFFIXES


def _is_hard_suffix(token: str) -> bool:
    core = _core(token)
    return core in _HARD_SUFFIXES or core.rstrip(".") in _HARD_SUFFIXES


def _name_like(token: str) -> bool:
    if token in ("&",):
        return True
    if token.lower() in _NAME_CONNECTORS:
        return True
    return re.fullmatch(r"[(\"“]?[A-Z0-9][A-Za-z0-9'’.&-]*,?", token) is not None


def _opens(token: str) -> bool:
    return token[:1] in "(\"“"


def _clean_entity(name: str) -> str:
    name = _norm_space(name).strip(" ,;:(\"“”")
    if name.endswith(")") and "(" not in name:
        name = name[:-1]
    if name.endswith(".") and not _is_hard_suffix(name.split()[-1]):
        name = name[:-1]
    return name.rstrip(" ,")


def _line_entities(line: str) -> list[tuple[int, int, str]]:
    """Organisation names ending in a legal-form or organisational suffix."""
    toks = [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", line)]
    out: list[tuple[int, int, str]] = []
    consumed = -1
    for i, (_, _, tok) in enumerate(toks):
        if i <= consumed or not _is_suffix(tok):
            continue
        j = i
        while j - 1 > consumed:
            prev = toks[j - 1][2]
            if prev.endswith(":") or not _name_like(prev) or _core(prev) in _NAME_STOP:
                break
            if _is_hard_suffix(prev) or prev.endswith((")", ";")):
                break
            j -= 1
            if _opens(prev):
                break
        while j < i and (toks[j][2].lower() in _NAME_CONNECTORS or toks[j][2] == "&"):
            j += 1
        if j == i:
            continue
        k = i
        while not _is_hard_suffix(toks[k][2]) and k + 1 < len(toks) and _is_suffix(toks[k + 1][2]):
            if toks[k][2].endswith((")", ";")):
                break
            k += 1
        consumed = k
        name = _clean_entity(line[toks[j][0] : toks[k][1]])
        if name and any(ch.isalpha() for ch in name):
            out.append((toks[j][0], toks[k][1], name))
    return out


def _role_parties(line: str) -> list[tuple[str, str]]:
    """(name, role) pairs from party clauses: 'Acme, Inc. ("Provider")'."""
    out: list[tuple[str, str]] = []
    for m in _ROLE_RE.finditer(line):
        role = m.group(1).strip().lower()
        prefix = line[: m.start()].rstrip(" ,")
        toks = prefix.split(" ")
        name_toks: list[str] = []
        for tok in reversed(toks):
            if not tok:
                break
            core = _core(tok)
            if tok.endswith((")", ":")) or core in _NAME_STOP or core in _HONORIFICS:
                break
            if not (_name_like(tok) or re.fullmatch(r"[A-Z]\.", tok)):
                break
            name_toks.append(tok)
            if _opens(tok):
                break
        name_toks.reverse()
        while name_toks and (name_toks[0].lower() in _NAME_CONNECTORS or name_toks[0] == "&"):
            name_toks.pop(0)
        name = _clean_entity(" ".join(name_toks))
        if name and any(ch.isalpha() for ch in name) and not _parse_date(name):
            out.append((name, role))
    return out


def _label_value_name(value: str) -> Optional[str]:
    value = value.strip()
    if not value or set(value) <= {"_", " "}:
        return None
    ents = _line_entities(value)
    if ents:
        return ents[0][2]
    head = re.split(r"\s*(?:<|\(|,|\s-\s|\s–\s|\s—\s|\|)", value, maxsplit=1)[0].strip()
    head = head.strip("\"“” ")
    if not head:
        m = re.search(r"[\w.+-]+@[\w.-]+", value)
        return m.group() if m else None
    return head


def _looks_like_org_line(line: str) -> bool:
    toks = line.split()
    if not 1 <= len(toks) <= 7:
        return False
    if any(ch.isdigit() for ch in line) or ":" in line or "@" in line:
        return False
    if _TITLE_WORD_RE.search(line) or "SYNTHETIC" in line.upper() or _DRAFT_MARK_RE.search(line):
        return False
    if _core(toks[0]) in _HONORIFICS:
        return False
    words = [t for t in toks if t.lower() not in _NAME_CONNECTORS and t != "&"]
    if not words or not all(w[:1].isupper() for w in words):
        return False
    return not all(_core(w) in _GENERIC_WORDS or _core(w) in _ROLE_WORDS or _core(w) in _STOPWORDS for w in words)


# ---------------------------------------------------------------------------
# Rule-based fact extraction
# ---------------------------------------------------------------------------


_MONTHLY_PHRASE_RE = _lex(
    r"\bmonthly (?:[a-z]+ ){0,2}?(?:fee|charge|subscription|payment|dues|rent|license|licence|retainer)\b"
    r"|\bretainer (?:fee )?per month\b"
)
_NEGATED_SCOPE_RE = _lex(
    r"(?:outside|beyond|excluded from|not (?:included in|covered by|part of)|in addition to|separate from"
    r"|over and above)(?: the)?(?: scope of)?(?: the| our| your| its)?\s*$"
)
_RATE_CONTEXT_RE = _lex(r"\b(?:hourly|rates?|per hour)\b\W*(?:\w+\W+){0,6}$")


def _monthly_amount(text: str, start: int, end: int) -> Optional[tuple[int, int]]:
    """Span of a fee the sentence states as monthly: "$1,200 per month" or "monthly fee of $1,200".

    A billing frequency ("billed monthly at our hourly rates ($400 ...)") is not a monthly fee, and a
    mention without an amount ("outside the scope of the monthly retainer") is not a term.
    """
    for ms, me, _, _ in _money_hits(text, start, end, bare=True):
        if _RATE_CONTEXT_RE.search(text[max(start, ms - 40) : ms]) or _HOURLY_AFTER_RE.match(text[me : me + 20]):
            continue
        if _MONTHLY_AFTER_RE.match(text[me : me + 20]):
            return ms, me
        line_start = text.rfind("\n", start, ms) + 1
        before = text[max(start, line_start, ms - 90) : ms]
        phrases = list(_MONTHLY_PHRASE_RE.finditer(before))
        if not phrases:
            continue
        phrase = phrases[-1]
        between = before[phrase.end() :]
        # "(outside the scope of the monthly retainer) 1,750.00" names the retainer to exclude the amount from it
        lead = before[: phrase.start()]
        enclosed = lead.count("(") > lead.count(")") and ")" in between
        if re.search(r"[.;]\s", between) or enclosed or _NEGATED_SCOPE_RE.search(lead):
            continue
        return ms, me
    return None


class _DocReader:
    """Builds ``DocFacts`` for one document from lexicons and regexes."""

    def __init__(self, doc: SourceDocument) -> None:
        self.doc = doc
        self.pages = [_Page(doc.doc_id, p.page, p.text) for p in doc.pages]
        self.first = self.pages[0] if self.pages else None
        self.first_lines = self.first.line_texts() if self.first else []
        self.stem = _filename_title(doc.doc_id)
        self.is_email = self._detect_email()
        self.title_line, self.title = self._detect_title()
        self.doc_type = self._classify()

    # -- layout -----------------------------------------------------------

    def _detect_email(self) -> bool:
        if self.doc.media_type.lower() == "eml":
            return True
        head = self.first_lines[:14]
        if any(_MEMO_HEAD_RE.match(line) for line in head[:3]):
            return False
        labels = {m.group(1).lower() for line in head if (m := _EMAIL_HEADER_RE.match(line))}
        return "from" in labels and "subject" in labels and ("to" in labels or "date" in labels or "sent" in labels)

    def _is_skippable(self, line: str) -> bool:
        if "SYNTHETIC" in line.upper():
            return True
        stripped = _DRAFT_PHRASE_RE.sub("", _DRAFT_MARK_RE.sub("", line))
        return not re.search(r"[A-Za-z]{2,}", stripped)

    def _detect_title(self) -> tuple[Optional[int], str]:
        if self.is_email:
            for i, line in enumerate(self.first_lines[:14]):
                m = re.match(r"^\s*subject\s*:\s*(.+)$", line, re.IGNORECASE)
                if m:
                    return i, m.group(1).strip()
        # A "Re:" line beats a line ending in a document noun ("... Confirmation"), which beats a line that
        # merely contains one (a letterhead tagline such as "Event Registration Services").
        best: Optional[tuple[int, int, str]] = None
        for i, line in enumerate(self.first_lines[:14]):
            if self._is_skippable(line):
                continue
            sub = _SUBJECT_RE.match(line)
            if sub:
                score, text = 3, sub.group("val").strip()
            elif _FIELD_LINE_RE.match(line) or len(line) > 110 or not _TITLE_WORD_RE.search(line):
                continue
            else:
                last = _core(line.split()[-1])
                score, text = (2 if last in _TITLE_NOUNS else 1), line.strip()
            if best is None or score > best[0]:
                best = (score, i, text)
        found: Optional[tuple[int, str]] = (best[1], best[2]) if best else None
        if found is None:
            for i, line in enumerate(self.first_lines[:3]):
                if not self._is_skippable(line) and not _FIELD_LINE_RE.match(line):
                    found = (i, line.strip())
                    break
        if found is None:
            return None, self.stem
        idx, title = found
        if len(title.split()) < 3 and len(self.stem.split()) >= 3:
            return idx, self.stem
        return idx, title

    def _classify(self) -> str:
        head = self.first_lines[:3]
        if any(_MEMO_HEAD_RE.match(line) for line in head):
            return "memo"
        if self.is_email:
            return "correspondence"
        for hay in (self.title, self.stem):
            for doc_type, rx in _TYPE_TITLE_RULES:
                if rx.search(hay):
                    return doc_type
        body = self.doc.full_text
        best, best_count = "other", 1
        for doc_type, rx in _TYPE_BODY_RULES:
            count = len(rx.findall(body))
            if count > best_count:
                best, best_count = doc_type, count
        return best

    # -- counterparty -----------------------------------------------------

    def counterparty(self) -> Optional[str]:
        if self.first is None:
            return None
        lines = self.first_lines
        recipients: list[str] = []
        recipient_idx: set[int] = set()
        for i, line in enumerate(lines[:40]):
            m = _RECIPIENT_LABEL_RE.match(line)
            if not m:
                continue
            if self.is_email and not line.lower().lstrip().startswith("to"):
                continue
            value = m.group("val").strip()
            if value:
                name = _label_value_name(value)
                if name:
                    recipients.append(name)
                recipient_idx.add(i)
            else:
                recipient_idx.update({i + 1, i + 2})
                for j in (i + 1, i + 2):
                    if j < len(lines):
                        recipients.extend(e[2] for e in _line_entities(lines[j]))
                        if j == i + 1 and _looks_like_org_line(lines[j]):
                            recipients.append(lines[j].strip())
        excluded = list(recipients)
        scored: list[tuple[int, int, str]] = []  # (score, order, name)
        order = 0

        def add(score: int, name: Optional[str]) -> None:
            nonlocal order
            if name:
                scored.append((score, order, _clean_entity(name)))
                order += 1

        for line in lines:
            for name, role in _role_parties(line):
                if role in _CLIENT_ROLES:
                    excluded.append(name)
                elif role in _VENDOR_ROLES:
                    add(8, name)
        for line in lines[:40]:
            m = _ISSUER_LABEL_RE.match(line)
            if m and not (self.is_email and not line.lower().lstrip().startswith("from")):
                add(10 if self.is_email else 9, _label_value_name(m.group("val")))
        letterhead_seen = 0
        for i, line in enumerate(lines[:8]):
            if self._is_skippable(line) or i == self.title_line or i in recipient_idx:
                continue
            if _find_dates(line) or _FIELD_LINE_RE.match(line):
                break
            ents = _line_entities(line)
            if ents:
                add(7, ents[0][2])
            elif _looks_like_org_line(line):
                add(5, line.strip())
            letterhead_seen += 1
            if letterhead_seen >= 3:
                break
        signoff = False
        for i, line in enumerate(lines):
            if _SIGNOFF_RE.match(line) or "/s/" in line or line.lower().lstrip().startswith("by:"):
                signoff = True
            if i in recipient_idx:
                continue
            for _, _, name in _line_entities(line):
                add(3 if signoff else 2, name)
        best: Optional[tuple[int, int, str]] = None
        for score, idx, name in scored:
            if any(_cp_match(name, ex) for ex in excluded):
                continue
            if best is None or score > best[0] or (score == best[0] and idx < best[1]):
                best = (score, idx, name)
        return best[2] if best else None

    # -- dates ------------------------------------------------------------

    def doc_date(self) -> Optional[str]:
        if self.first is None:
            return None
        page = self.first
        text = page.text
        head = page.lines[:15]

        def labeled(spans: list[tuple[int, int]]) -> Optional[str]:
            for s, e in spans:
                m = _DOC_DATE_LABEL_RE.match(text, s, e)
                if not m:
                    continue
                for hit in _find_dates(text, m.end(), e):
                    gap = text[m.end() : hit.start]
                    if re.fullmatch(r"(?:[A-Za-z]{3,9},?\s*)?", gap):
                        return hit.iso
                    break
            return None

        found = labeled(head)
        if found:
            return found
        if head:
            region_start, region_end = head[0][0], head[-1][1]
            for m in _ISSUED_RE.finditer(text, region_start, region_end):
                hits = _find_dates(text, m.end(), min(len(text), m.end() + 40))
                if hits and hits[0].start == m.end():
                    return hits[0].iso
        for s, e in head:
            hits = _find_dates(text, s, e)
            if hits and hits[-1].end == e and (e - s) <= (hits[-1].end - hits[-1].start) + 30:
                if not _NON_DOC_DATE_CONTEXT_RE.search(text[s : hits[-1].start]):
                    return hits[-1].iso
        for p in self.pages:
            for hit in _find_dates(p.text):
                if _DATED_RE.search(p.text[max(0, hit.start - 60) : hit.start]):
                    return hit.iso
        for p in self.pages:
            found = labeled(p.lines)
            if found:
                return found
        for s, e in head:
            for hit in _find_dates(text, s, e):
                if not _NON_DOC_DATE_CONTEXT_RE.search(text[max(s, hit.start - 25) : hit.start]):
                    return hit.iso
        return None

    def service_period(self) -> tuple[Optional[str], Optional[str]]:
        end_only: Optional[str] = None
        single: Optional[str] = None
        header_lines = set(self.first.lines[:15]) if self.first else set()
        for page in self.pages:
            text = page.text
            dates = _find_dates(text)
            for m in _DAY_SPAN_RE.finditer(text):
                s0 = page.segment_at(m.start())[0]
                line = page.line_at(m.start())
                # an agenda or itinerary often opens a header line with its dates
                lead = _WEEKDAY_RE.sub("", text[line[0] : m.start()])
                standalone = page is self.first and line in header_lines and not re.search(r"[A-Za-z]{2,}", lead)
                if standalone or _SP_CUE_RE.search(text[max(s0, m.start() - 100) : m.start()]):
                    mo = _month_number(m.group("m"))
                    y = int(m.group("y"))
                    d1 = _safe_date(y, mo or 0, int(m.group("d1"))) if mo else None
                    d2 = _safe_date(y, mo or 0, int(m.group("d2"))) if mo else None
                    if d1 and d2 and d1 <= d2:
                        return d1.isoformat(), d2.isoformat()
            for m in _CROSS_SPAN_RE.finditer(text):
                s0 = page.segment_at(m.start())[0]
                if not _SP_CUE_RE.search(text[max(s0, m.start() - 100) : m.start()]):
                    continue
                m1, m2 = _month_number(m.group("m1")), _month_number(m.group("m2"))
                y2 = int(m.group("y2"))
                # "December 1 - January 31, 2025" starts in the prior year
                y1 = int(m.group("y1")) if m.group("y1") else (y2 if (m1 or 0) <= (m2 or 0) else y2 - 1)
                d1 = _safe_date(y1, m1, int(m.group("d1"))) if m1 else None
                d2 = _safe_date(y2, m2, int(m.group("d2"))) if m2 else None
                if d1 and d2 and d1 <= d2:
                    return d1.isoformat(), d2.isoformat()
            points: list[tuple[int, int, str, str]] = [(h.start, h.end, h.iso, h.iso) for h in dates]
            points += [(s, e, _iso_month_start(mo), _iso_month_end(mo)) for s, e, mo in _month_year_hits(text, dates)]
            points.sort()
            for a, b in pairwise(points):
                if not _RANGE_SEP_RE.match(text[a[1] : b[0]]):
                    continue
                seg_start = page.segment_at(a[0])[0]
                line_start = page.line_at(a[0])[0]
                window = text[max(min(seg_start, line_start), a[0] - 100) : a[0]]
                if _SP_CUE_RE.search(window) and a[2] <= b[3]:
                    return a[2], b[3]
            for m in _MONTH_SPAN_RE.finditer(text):
                if _SP_CUE_RE.search(text[max(0, m.start() - 100) : m.start()]):
                    m1, m2 = _month_number(m.group("m1")), _month_number(m.group("m2"))
                    y = int(m.group("y"))
                    if m1 and m2 and m1 <= m2:
                        return f"{y:04d}-{m1:02d}-01", _iso_month_end(f"{y:04d}-{m2:02d}")
            for hit in dates:
                before = text[max(0, hit.start - 60) : hit.start]
                if end_only is None and _SP_END_ONLY_RE.search(before):
                    end_only = hit.iso
                if single is None and _SINGLE_EVENT_DATE_RE.search(before):
                    single = hit.iso
            for s, _, mo in _month_year_hits(text, dates):
                if _SP_MONTH_ONLY_RE.search(text[max(0, s - 60) : s]):
                    return _iso_month_start(mo), _iso_month_end(mo)
        if single is not None and end_only is None:
            return single, single
        return None, end_only

    # -- references, amounts, terms ---------------------------------------

    def reference_numbers(self) -> list[str]:
        values: list[str] = []
        for page in self.pages:
            for v in _reference_values(page.text):
                if v.lower() not in {x.lower() for x in values}:
                    values.append(v)
        return values

    def amounts(self) -> list[AmountFact]:
        out: list[AmountFact] = []
        seen: set[tuple[str, str]] = set()
        for page in self.pages:
            text = page.text
            prev_end_by_line: dict[int, int] = {}
            hits = sorted(_money_hits(text, bare=True), key=lambda h: h[0])
            taken: list[tuple[int, int]] = []
            for start, end, value, has_currency in hits:
                if any(s <= start < e for s, e in taken):
                    continue
                taken.append((start, end))
                ls, le = page.line_at(start)
                left_from = max(ls, prev_end_by_line.get(ls, ls), start - 60)
                prev_end_by_line[ls] = end
                label = self._amount_label(page, text[left_from:start], start, end)
                if not has_currency and label == "line":
                    continue
                amount = fmt(value)
                if D(amount) == 0 or (label, amount) in seen:
                    continue
                seen.add((label, amount))
                out.append(AmountFact(label=label, amount=amount, quote=page.quote(start, end, prefer_line=True)))
        return out

    def _amount_label(self, page: _Page, left: str, start: int, end: int) -> str:
        text = page.text
        right = text[end : end + 45]
        seg_s, seg_e = page.segment_at(start)
        sentence = text[seg_s:seg_e]
        installment_ctx = bool(_INSTALLMENT_WORD_RE.search(sentence)) or self.doc_type in (
            "separation_agreement",
            "settlement_agreement",
        )
        if _HOURLY_AFTER_RE.match(right):
            return "rate"
        if _SETTLEMENT_AFTER_RE.match(right):
            return "settlement_amount"
        if _MONTHLY_AFTER_RE.match(right):
            if installment_ctx:
                return "installment"
            return "retainer" if re.search(r"\bretainer\b", sentence, re.I) else "monthly_fee"
        line_start = page.line_at(start)[0]
        # a rate list ("hourly rates ($400 partner, $250 associate)") spans several amounts on one line
        if _RATE_CONTEXT_RE.search(text[max(line_start, start - 60) : start]):
            return "rate"
        best_label, best_end = "line", -1
        for label, rx in _AMOUNT_LABEL_RES:
            for m in rx.finditer(left):
                if m.end() > best_end:
                    best_label, best_end = label, m.end()
        if best_label == "retainer" and not _MONTHLY_CUE_RE.search(sentence):
            # an upfront retainer is a one-off fee, not a standing monthly charge
            best_label = "fee"
        if best_label in ("line", "total_due", "fee") and self.doc_type == "separation_agreement":
            if re.search(r"severance", sentence, re.I) and not _INSTALLMENT_WORD_RE.search(left[-25:]):
                return "severance"
        if best_label == "line" and self.doc_type == "settlement_agreement" and re.search(r"settle", sentence, re.I):
            return "settlement_amount"
        return best_label

    def terms(self) -> list[TermFact]:
        out: list[TermFact] = []
        seen: set[tuple[str, str]] = set()

        def add(kind: str, text: str, quote: EvidenceQuote) -> None:
            # one fact per kind is enough for the qualitative terms; fees and dates can differ
            key = (kind, text.lower()) if kind in ("monthly_fee", "retainer", "term_end") else (kind, "")
            if key not in seen:
                seen.add(key)
                out.append(TermFact(kind=kind, text=text, quote=quote))

        for page in self.pages:
            text = page.text
            for s, e in page.segments:
                sent = text[s:e]
                if "SYNTHETIC" in sent.upper():
                    continue
                installment_ctx = bool(_INSTALLMENT_CONTEXT_RE.search(sent)) or self.doc_type in (
                    "separation_agreement",
                    "settlement_agreement",
                )
                fee = None if installment_ctx else _monthly_amount(text, s, e)
                if fee is not None:
                    ms, me = fee
                    # the description repeats the stated figure in one format so consumers can read it back
                    raw = f"${next(v for _, _, v, _ in _money_hits(text, ms, me, bare=True)):,.2f}"
                    is_retainer = re.search(r"\bretainer\b", sent, re.I) is not None
                    kind = "retainer" if is_retainer else "monthly_fee"
                    desc = f"retainer of {raw} per month" if is_retainer else f"monthly fee of {raw}"
                    add(kind, desc, page.quote(s, e))
                for m in _AUTO_RENEW_RE.finditer(sent):
                    add("auto_renew", "renews automatically", page.quote(s + m.start(), s + m.end()))
                    break
                for m in _ONGOING_RE.finditer(sent):
                    add("ongoing_services", f"continues {_norm_space(m.group()).lower()}"
                        if m.group().lower().startswith("until") else _norm_space(m.group()).lower(),
                        page.quote(s + m.start(), s + m.end()))
                    break
                for m in _ONE_TIME_RE.finditer(sent):
                    add("one_time", _norm_space(m.group()).lower(), page.quote(s + m.start(), s + m.end()))
                    break
                for m in _INSTALLMENTS_RE.finditer(sent):
                    n = m.group("n")
                    count = _number(n) if n else None
                    desc = f"payable in {count} installments" if count else "paid in installments"
                    add("installments", desc, page.quote(s + m.start(), s + m.end()))
                    break
                for m in _TERM_LENGTH_RE.finditer(sent):
                    n_word = m.group("n1") or m.group("n2")
                    unit = m.group("u1") or m.group("u2")
                    n = _number(n_word) if n_word else None
                    hits = _find_dates(text, s + m.end(), e)
                    starts = [(h.end, h.iso) for h in hits if h.start == s + m.end()]
                    starts += [(me_, f"{mo}-01") for ms_, me_, mo in _month_year_hits(text[: e], hits)
                               if ms_ == s + m.end()]
                    if n and starts:
                        start_end, start_iso = starts[0]
                        start_d = date.fromisoformat(start_iso)
                        end_d = _term_end(start_d, n, unit)
                        add(
                            "term_end",
                            f"term ends {end_d.isoformat()} ({n}-{unit.lower()} term commencing {start_d.isoformat()})",
                            page.quote(s + m.start(), start_end),
                        )
                        break
                for m in _TERM_EXPIRY_RE.finditer(sent):
                    hits = _find_dates(text, s + m.end(), e)
                    if hits and hits[0].start == s + m.end():
                        add("term_end", f"term ends {hits[0].iso}", page.quote(s + m.start(), hits[0].end))
                        break
                if _TERM_WORD_RE.search(sent):
                    hits = _find_dates(text, s, e)
                    for a, b in pairwise(hits):
                        if _RANGE_SEP_RE.match(text[a.end : b.start]) and a.iso < b.iso:
                            add("term_end", f"term ends {b.iso} (term from {a.iso})", page.quote(a.start, b.end))
                            break
        return out

    # -- execution status and statements -----------------------------------

    def is_draft(self) -> bool:
        if self.doc_type == "correspondence":
            return False
        text = self.doc.full_text
        if _DRAFT_MARK_RE.search(text) or _DRAFT_PHRASE_RE.search(text):
            return True
        return bool(re.search(r"\bdraft\b", f"{self.title} {self.stem}", re.IGNORECASE))

    def is_signed(self) -> Optional[bool]:
        text = self.doc.full_text
        # Execution status only means something for agreements; a blank "authorized signature" line on an
        # invoice is not an unsigned contract.
        if self.doc_type not in _SIGNABLE_TYPES:
            return None
        if _UNSIGNED_RE.search(text):
            return False
        signed = len(_SIGNED_RE.findall(text))
        blank = len(_BLANK_SIGNATURE_RE.findall(text))
        if blank:
            return False
        if signed:
            return True
        return None

    def key_statements(self) -> list[EvidenceQuote]:
        out: list[EvidenceQuote] = []
        seen: set[tuple[int, str]] = set()
        for page in self.pages:
            text = page.text
            for s, e in page.segments:
                sent = text[s:e]
                if "SYNTHETIC" in sent.upper() or _EMAIL_HEADER_RE.match(sent):
                    continue
                for rx in _KEY_STATEMENT_RES:
                    m = rx.search(sent)
                    if m:
                        q = page.quote(s + m.start(), s + m.end())
                        key = (q.page, q.quote)
                        if key not in seen:
                            seen.add(key)
                            out.append(q)
                        break
                if len(out) >= _MAX_KEY_STATEMENTS:
                    return out
        return out

    def facts(self) -> DocFacts:
        sp_start, sp_end = self.service_period()
        return DocFacts(
            doc_id=self.doc.doc_id,
            doc_type=self.doc_type,
            title=self.title,
            counterparty=self.counterparty(),
            doc_date=self.doc_date(),
            reference_numbers=self.reference_numbers(),
            amounts=self.amounts(),
            service_period_start=sp_start,
            service_period_end=sp_end,
            is_draft=self.is_draft(),
            is_signed=self.is_signed(),
            terms=self.terms(),
            key_statements=self.key_statements(),
            extractor="rules",
        )


def _verify_facts(facts: DocFacts, docs_by_id: dict[str, SourceDocument]) -> DocFacts:
    """Drop every amount / term / statement whose quote is not verbatim; count the drops."""
    dropped = 0
    amounts: list[AmountFact] = []
    for a in facts.amounts:
        if verify_quote(a.quote, docs_by_id) and a.quote.doc_id == facts.doc_id:
            amounts.append(a)
        else:
            dropped += 1
    terms: list[TermFact] = []
    for t in facts.terms:
        if verify_quote(t.quote, docs_by_id) and t.quote.doc_id == facts.doc_id:
            terms.append(t)
        else:
            dropped += 1
    statements: list[EvidenceQuote] = []
    for q in facts.key_statements:
        if verify_quote(q, docs_by_id) and q.doc_id == facts.doc_id:
            statements.append(q)
        else:
            dropped += 1
    return facts.model_copy(
        update={
            "amounts": amounts,
            "terms": terms,
            "key_statements": statements,
            "dropped_quotes": facts.dropped_quotes + dropped,
        }
    )


# ---------------------------------------------------------------------------
# Rule-based intent parsing
# ---------------------------------------------------------------------------


def _event_type(title: str, description: str, category: AdjustmentCategory) -> str:
    scores: dict[str, int] = {}
    for event, rx in _EVENT_LEXICON:
        score = 2 * len(rx.findall(title)) + len(rx.findall(description))
        if score:
            scores[event] = score
    if category == AdjustmentCategory.OUT_OF_PERIOD:
        scores["out_of_period"] = scores.get("out_of_period", 0) + 3
    elif category == AdjustmentCategory.PRO_FORMA:
        scores["pro_forma_savings"] = scores.get("pro_forma_savings", 0) + 3
    elif category == AdjustmentCategory.OWNER_DISCRETIONARY and "owner_comp" not in scores:
        scores["owner_expense"] = scores.get("owner_expense", 0) + 1
    if not scores:
        return "other"
    order = [e for e, _ in _EVENT_LEXICON]
    return max(scores, key=lambda e: (scores[e], -order.index(e)))


def _narrative_counterparties(title: str, description: str) -> list[str]:
    names: list[str] = []

    def add(name: str) -> None:
        name = _clean_entity(re.sub(r"(?:'s|’s)$", "", name))
        toks = _name_tokens(name)
        if not toks or all(t in _GENERIC_WORDS or t in _STOPWORDS or t in _ROLE_WORDS for t in toks):
            return
        for i, existing in enumerate(names):
            et = _name_tokens(existing)
            if toks <= et:
                return
            if et <= toks:
                names[i] = name
                return
        names.append(name)

    for text in (title, description):
        for line in text.splitlines():
            for _, _, ent in _line_entities(line):
                add(ent)
        for m in _INITIAL_NAME_RE.finditer(text):
            add(m.group())
    for m in _AMPERSAND_NAME_RE.finditer(description):
        parts = [p.lower() for p in re.split(r" (?:&|and) ", m.group())]
        if not any(p in _GENERIC_WORDS or p in _WEAK_KEYWORDS or p in _STOPWORDS for p in parts):
            add(m.group())
    for m in _CAP_RUN_RE.finditer(description):
        words = m.group().split()
        if any(w.lower() in _STOPWORDS or w.lower() in _GENERIC_WORDS or w.lower() in _ROLE_WORDS
               or w.lower() in _MONTH_WORDS or w.lower() in _WEAK_KEYWORDS or w.lower() in _STREET_WORDS
               for w in words):
            continue
        prefix = description[: m.start()].rstrip()
        if prefix.endswith(("&", " and", " of")):
            continue
        add(m.group())
    return names


def _narrative_keywords(title: str, description: str, limit: int = 15) -> list[str]:
    out: list[str] = []
    for text in (title, description):
        for raw in re.findall(r"[A-Za-z][A-Za-z0-9&'’-]*[A-Za-z0-9]", text):
            tok = re.sub(r"(?:'s|’s)$", "", raw.lower()).strip("-'’")
            candidates = [tok]
            if "-" in tok:
                parts = [p for p in tok.split("-") if p]
                generic_parts = [p for p in parts if p in _GENERIC_WORDS
                                 or p in {"related", "based", "driven", "specific", "level", "wide"}]
                if tok in _GENERIC_WORDS:
                    candidates = []
                elif generic_parts:
                    candidates = [p for p in parts if p not in generic_parts]
            for cand in candidates:
                if (
                    len(cand) < 3
                    or cand in _STOPWORDS
                    or cand in _GENERIC_WORDS
                    or cand in _MONTH_WORDS
                    or cand in _STREET_WORDS
                    or cand in _ENTITY_FORM_WORDS
                    or cand in _NAME_SUFFIX_KEYWORDS
                    or cand.isdigit()
                    or re.fullmatch(r"(?:fy|q[1-4]|h[12])\d*", cand)
                ):
                    continue
                if cand not in out:
                    out.append(cand)
                if len(out) >= limit:
                    return out
    return out


def _without_names(keywords: Iterable[str], names: Iterable[str], narrative: str) -> list[str]:
    """Keywords that are not a party's name. A vendor or person is matched as a counterparty;
    as a keyword it would link every charge that party makes, whatever the event. A word
    that also describes the event outside the name ("search" in "retained search fee paid
    to Pinecrest Search Partners") stays a keyword."""
    names = [n for n in names if n and n.strip()]
    name_words = {t for n in names for t in _name_tokens(n)}
    outside = narrative
    for n in sorted(names, key=len, reverse=True):
        outside = re.sub(re.escape(n), " ", outside, flags=re.IGNORECASE)
    outside_words = set(re.findall(r"[a-z0-9]+", outside.lower()))
    out: list[str] = []
    for kw in keywords:
        words = [w for w in re.findall(r"[a-z0-9]+", kw.lower().replace("&", " and ")) if w not in _ENTITY_FORM_WORDS]
        if words and all(w in name_words for w in words) and not all(w in outside_words for w in words):
            continue
        if kw not in out:
            out.append(kw)
    return out


def _narrative_refs(text: str, gl_accounts: Iterable[str]) -> list[str]:
    accounts = {a.strip() for a in gl_accounts}
    out: list[str] = []
    for value in _reference_values(text):
        if value in accounts:
            continue
        if value.lower() not in {v.lower() for v in out}:
            out.append(value)
    for m in re.finditer(r"#\s?(\d{3,})\b", text):
        value = m.group(1)
        if value not in accounts and value not in out:
            out.append(value)
    return out


def _normalized_amount(text: str) -> Optional[str]:
    for cue in _NORMALIZED_CUE_RE.finditer(text):
        sentence_end = re.search(r"[.;](?:\s|$)", text[cue.end() :])
        stop = cue.end() + (sentence_end.start() if sentence_end else len(text) - cue.end())
        for start, _, value, _ in _money_hits(text, cue.end(), stop):
            lead = text[max(cue.end(), start - 14) : start].lower()
            if re.search(r"\b(?:to|of|at)\b|=", lead) or start - cue.end() <= 6:
                return fmt(value)
            break
    return None


def _event_months(text: str) -> list[str]:
    months: set[str] = set()
    dates = _find_dates(text)
    for h in dates:
        months.add(h.iso[:7])
    for _, _, mo in _month_year_hits(text, dates):
        months.add(mo)
    for m in _MONTH_SPAN_RE.finditer(text):
        m1, m2 = _month_number(m.group("m1")), _month_number(m.group("m2"))
        y = int(m.group("y"))
        if m1 and m2 and m1 <= m2:
            months.update(f"{y:04d}-{k:02d}" for k in range(m1, m2 + 1))
    for m in _QUARTER_RE.finditer(text):
        y = int(m.group("y"))
        y = y + 2000 if y < 100 else y
        q = int(m.group("q"))
        months.update(f"{y:04d}-{k:02d}" for k in range(3 * q - 2, 3 * q + 1))
    return sorted(months)


def _parse_intent_rules(adj: AdjustmentClaim) -> AdjustmentIntent:
    title = adj.title or ""
    description = adj.description or ""
    raw_category = adj.category_raw or ""
    narrative = "\n".join(x for x in (title, description) if x)
    assertion_text = "\n".join(x for x in (title, description, raw_category) if x)
    event_type = _event_type(title, description, adj.category)
    is_normalization = adj.category == AdjustmentCategory.NORMALIZATION or bool(
        _NORMALIZATION_CLAIM_RE.search(narrative)
    )
    is_pro_forma = adj.category == AdjustmentCategory.PRO_FORMA or bool(_PRO_FORMA_CLAIM_RE.search(assertion_text))
    asserts_personal = bool(_PERSONAL_CLAIM_RE.search(assertion_text))
    if (
        adj.category == AdjustmentCategory.OWNER_DISCRETIONARY
        and event_type != "owner_comp"
        and not is_normalization
    ):
        asserts_personal = True
    if event_type == "owner_comp" or is_normalization:
        # compensation normalisation is a level argument, not a claim that the cost is personal
        asserts_personal = asserts_personal and bool(re.search(r"\bpersonal\b", assertion_text, re.I))
    asserts_nonrecurring = adj.category == AdjustmentCategory.NON_RECURRING or bool(
        _NONRECURRING_CLAIM_RE.search(assertion_text)
    )
    normalized = _normalized_amount(narrative) if is_normalization else None
    notes = [f"rules: event_type={event_type}"]
    if adj.category != AdjustmentCategory.OTHER:
        notes.append(f"category={adj.category.value}")
    counterparties = _narrative_counterparties(title, description)
    return AdjustmentIntent(
        adj_id=adj.adj_id,
        counterparties=counterparties,
        keywords=_without_names(_narrative_keywords(title, description), counterparties, narrative),
        reference_numbers=_narrative_refs(narrative, adj.gl_accounts),
        event_type=event_type,
        asserts_nonrecurring=asserts_nonrecurring,
        asserts_personal=asserts_personal,
        is_pro_forma=is_pro_forma,
        is_normalization=is_normalization,
        normalized_amount=normalized,
        event_months=_event_months(narrative),
        notes="; ".join(notes),
    )


# ---------------------------------------------------------------------------
# Evidence-to-entry ties (shared by contradictions and classification)
# ---------------------------------------------------------------------------


def _fact_quotes(fact: DocFacts) -> list[EvidenceQuote]:
    return [a.quote for a in fact.amounts] + [t.quote for t in fact.terms] + list(fact.key_statements)


def _doc_label(fact: DocFacts) -> str:
    title = (fact.title or "").strip()
    if title and title != fact.doc_id and title != _filename_title(fact.doc_id):
        return f"{title} ({fact.doc_id})"
    return fact.doc_id


def _entry_date(entry: GLEntry) -> Optional[date]:
    try:
        return date.fromisoformat(entry.date[:10])
    except ValueError:
        return None


def _amount_matches(entry: GLEntry, amounts: Iterable[str]) -> bool:
    value = abs(D(entry.amount))
    return any(within(value, abs(D(a))) for a in amounts)


def _entry_cites(entry: GLEntry, refs: Iterable[str]) -> bool:
    return any(len(r) >= 3 and (_token_in(r, entry.doc_number) or _token_in(r, entry.memo)) for r in refs)


def _entry_event_refs(entry: GLEntry) -> list[tuple[str, str]]:
    return [(k, v) for k, v in _labeled_refs(entry.memo) if k in _EVENT_REF_KINDS]


def _recurring_fee_amounts(fact: DocFacts) -> list[str]:
    return [a.amount for a in fact.amounts if a.label in ("monthly_fee", "retainer")]


class _Evidence:
    """Text of a document as the rules can see it (full text when cached, else the facts)."""

    def __init__(self, docs: dict[str, SourceDocument]) -> None:
        self.docs = docs

    def text(self, fact: DocFacts) -> str:
        doc = self.docs.get(fact.doc_id)
        parts = [fact.title or "", fact.counterparty or "", " ".join(fact.reference_numbers)]
        if doc is not None:
            parts.append(doc.full_text)
        else:
            parts.extend(q.quote for q in _fact_quotes(fact))
        return "\n".join(parts)

    def verified(self, quote: EvidenceQuote, facts_by_id: dict[str, DocFacts]) -> bool:
        if quote.doc_id in self.docs:
            return verify_quote(quote, self.docs)
        fact = facts_by_id.get(quote.doc_id)
        if fact is None or len(quote.quote.strip()) < MIN_QUOTE_CHARS:
            return False
        return any(q.page == quote.page and quote.quote in q.quote for q in _fact_quotes(fact))


def _header_end(doc: SourceDocument) -> int:
    """Offset on page 1 where the body starts: the first prose sentence (long, mostly lower-case words)."""
    page = doc.pages[0]
    text = page.text
    for s, e in _segments(text, _line_spans(text)):
        chunk = text[s:e]
        if len(chunk) >= 60 and len(re.findall(r"\b[a-z]{2,}\b", chunk)) >= 6 and not _FIELD_LINE_RE.match(chunk):
            return s
    return len(text)


def _primary_refs(fact: DocFacts, evidence: _Evidence) -> list[str]:
    """The references a document is *about*: those in its header block and its own bill numbers.

    A letter for one matter often mentions another in the body ("separate from our retainer under
    Matter 4410"); such mentions must not tie the document to the other matter's entries.
    """
    doc = evidence.docs.get(fact.doc_id)
    known = {r.lower(): r for r in fact.reference_numbers}
    if doc is None or not doc.pages:
        heading = f"{fact.title}\n{_filename_title(fact.doc_id)}"
        out = [r for r in fact.reference_numbers if _token_in(r, heading)]
        return out or fact.reference_numbers[:1]
    header = doc.pages[0].text[: _header_end(doc)]
    out: list[str] = []
    for value in _reference_values(header):
        if value not in out:
            out.append(value)
    for kind, value in _labeled_refs(doc.full_text):
        if kind in ("invoice", "confirmation", "check") and value not in out:
            out.append(value)
    if not any(k in _EVENT_REF_KINDS for k, v in _labeled_refs(header)):
        first_event = next((v for k, v in _labeled_refs(doc.full_text) if k in _EVENT_REF_KINDS), None)
        if first_event is not None and first_event not in out:
            out.append(first_event)
    # "Matter 4410" is the same reference as client-matter "10001-4410"
    for r in fact.reference_numbers:
        if r not in out and any(r in re.split(r"[-/.]", p) for p in out):
            out.append(r)
    return [known.get(r.lower(), r) for r in out]


# Distinctive words a memo and a document must share to name the same event.
_SHARED_EVENT_WORDS = 2
_TIE_NOISE_WORDS = frozenset({"report", "reports", "statement", "statements", "agenda", "summary", "details", "detail"})


def _event_tokens(text: str) -> set[str]:
    """Words that can identify an event: not generic, not an account-category noun."""
    return {t for t in _distinct_tokens(text) if t not in _WEAK_KEYWORDS and t not in _TIE_NOISE_WORDS}


def _tie_entries(
    fact: DocFacts,
    entries: list[GLEntry],
    evidence: _Evidence,
    mode: str,
) -> list[str]:
    """Entries a document's statement applies to; [] means the statement is not entry-specific.

    A tie needs a reference (the document's own number, or a matter or claim number the
    memo cites), the same amount for the same counterparty, or a memo that names the
    document's event. Date proximity alone never ties a document to an entry.

    mode "fee": a recurring-fee term; "statement": a recurrence statement; "business": a business-purpose record.
    """
    refs = [r for r in _primary_refs(fact, evidence) if len(r) >= 3]
    ref_hits = [e for e in entries if _entry_cites(e, refs)]
    fee_amounts = _recurring_fee_amounts(fact)
    doc_amounts = [a.amount for a in fact.amounts if a.label not in ("rate", "deductible")]

    def cp_ok(e: GLEntry) -> Optional[bool]:
        if not fact.counterparty or not e.counterparty:
            return None
        return _cp_match(fact.counterparty, e.counterparty)

    if mode == "fee":
        chosen = list(ref_hits)
        if fee_amounts:
            for e in entries:
                if e in chosen or cp_ok(e) is False or _entry_event_refs(e):
                    continue
                if _amount_matches(e, fee_amounts):
                    chosen.append(e)
        elif not chosen:
            cp_entries = [e for e in entries if cp_ok(e)]
            if cp_entries and not any(_entry_event_refs(e) for e in cp_entries):
                chosen = cp_entries
        return [e.entry_id for e in entries if e in chosen]

    if ref_hits:
        # A numbered document (an invoice, an expense report) is about the entries carrying its number.
        return [e.entry_id for e in entries if e in ref_hits]
    doc_text = evidence.text(fact)
    # Person names (the owner, the attendee) appear on personal and business items alike.
    person_tokens = {t for m in _INITIAL_NAME_RE.finditer(doc_text) for t in _name_tokens(m.group())}
    doc_tokens = _event_tokens(doc_text) - person_tokens
    chosen: list[GLEntry] = []
    for e in entries:
        amount = bool(doc_amounts) and _amount_matches(e, doc_amounts)
        cp = cp_ok(e)
        memo_tokens = _event_tokens(e.memo) - {t for m in _INITIAL_NAME_RE.finditer(e.memo) for t in _name_tokens(m.group())}
        shared = len(memo_tokens & doc_tokens)
        if amount and cp is True:
            chosen.append(e)  # the same amount for the same counterparty
        elif shared >= _SHARED_EVENT_WORDS:
            chosen.append(e)  # the memo names the document's event ("Dixon plant visit", "SMCS summit")
        elif amount and cp is None and not e.counterparty and shared >= 1:
            chosen.append(e)  # a journal entry has no party: its amount plus the document's subject
    return [e.entry_id for e in entries if e in chosen]


# ---------------------------------------------------------------------------
# Rule-based contradictions
# ---------------------------------------------------------------------------

_NONRECURRING_CONFLICT = "Management describes the cost as one-time / non-recurring."
_PERSONAL_CONFLICT = "Management describes the cost as a personal (non-business) owner expense."


def _ranked(quotes: list[EvidenceQuote], strong: re.Pattern[str]) -> list[EvidenceQuote]:
    return sorted(quotes, key=lambda q: 0 if strong.search(q.quote) else 1)


def _theme_key(entry: GLEntry) -> tuple[str, str]:
    return " ".join(sorted(_name_tokens(entry.counterparty))), _memo_theme(entry.memo)


def _extend_by_theme(entry_ids: list[str], entries: list[GLEntry]) -> list[str]:
    if not entry_ids:
        return entry_ids
    chosen = set(entry_ids)
    themes = {_theme_key(e) for e in entries if e.entry_id in chosen}
    themes = {t for t in themes if t[1]}
    return [e.entry_id for e in entries if e.entry_id in chosen or _theme_key(e) in themes]


def _term_statement(term: TermFact) -> str:
    """What the term says, as a clause that completes '<document> ...' (the engine names the document).

    Only what the document states: whether that makes the cost part of the ongoing cost base is
    the reviewer's call, which the engine asks as a judgment question (SPEC §5.5)."""
    if term.kind == "monthly_fee":
        return f"provides for a {term.text}."
    if term.kind == "retainer":
        return f"sets a standing {term.text}."
    if term.kind == "auto_renew":
        return "states that the agreement renews automatically."
    if term.kind == "ongoing_services":
        return "provides for services that continue until terminated."
    return f"sets a multi-period term ({term.text})."


def _is_multi_period_term(term: TermFact) -> bool:
    m = re.search(r"\((\d+)-(month|year) term", term.text)
    if m:
        n = int(m.group(1))
        return n > 12 or m.group(2) == "year"
    return term.kind != "term_end"


def _find_contradictions_rules(
    adj: AdjustmentClaim,
    intent: AdjustmentIntent,
    facts: list[DocFacts],
    entries: list[GLEntry],
    evidence: _Evidence,
) -> list[Contradiction]:
    out: list[Contradiction] = []
    seen: set[tuple[str, int, str]] = set()
    facts_by_id = {f.doc_id: f for f in facts}
    narrative = f"{adj.title}\n{adj.description}"

    def add(fact: DocFacts, quote: EvidenceQuote, statement: str, conflicts_with: str, entry_ids: list[str]) -> bool:
        key = (quote.doc_id, quote.page, quote.quote)
        if key in seen or not evidence.verified(quote, facts_by_id):
            return False
        seen.add(key)
        out.append(
            Contradiction(
                doc_id=fact.doc_id,
                statement=statement,
                quote=quote,
                conflicts_with=conflicts_with,
                entry_ids=entry_ids,
            )
        )
        return True

    for fact in facts:
        per_doc = 0
        if intent.asserts_nonrecurring and not intent.is_pro_forma:
            for q in _ranked(fact.key_statements, _RECURRENCE_STRONG_RE):
                if per_doc >= 3:
                    break
                m = _RECURRENCE_RE.search(q.quote)
                if not m or _INSTALLMENT_CONTEXT_RE.search(q.quote):
                    continue
                phrase = _norm_space(m.group())
                entry_ids = _tie_entries(fact, entries, evidence, "statement")
                is_term_like = _AUTO_RENEW_RE.search(q.quote) or _ONGOING_RE.search(q.quote)
                if is_term_like:
                    entry_ids = _tie_entries(fact, entries, evidence, "fee")
                # a statement that the cost recurs covers the whole series, not just the entries near its date
                entry_ids = _extend_by_theme(entry_ids, entries)
                statement = f"describes the cost as recurring (\"{phrase}\")."
                if add(fact, q, statement, _NONRECURRING_CONFLICT, entry_ids):
                    per_doc += 1
            for term in fact.terms:
                if per_doc >= 3:
                    break
                if term.kind not in RECURRING_TERM_KINDS or not _is_multi_period_term(term):
                    continue
                if _INSTALLMENT_CONTEXT_RE.search(term.quote.quote):
                    continue
                entry_ids = _tie_entries(fact, entries, evidence, "fee")
                if add(fact, term.quote, _term_statement(term), _NONRECURRING_CONFLICT, entry_ids):
                    per_doc += 1
        if intent.asserts_personal:
            for q in _ranked(fact.key_statements, _BUSINESS_STRONG_RE):
                if per_doc >= 3:
                    break
                if not _BUSINESS_PURPOSE_RE.search(q.quote) or _PERSONAL_RE.search(q.quote):
                    continue
                entry_ids = _tie_entries(fact, entries, evidence, "business")
                statement = "records a business purpose for the expense."
                if add(fact, q, statement, _PERSONAL_CONFLICT, entry_ids):
                    per_doc += 1
        if intent.is_normalization and intent.normalized_amount:
            salaries = [a for a in fact.amounts if a.label == "base_salary"]
            if salaries and not any(within(a.amount, intent.normalized_amount) for a in salaries):
                a = salaries[0]
                add(
                    fact,
                    a.quote,
                    f"states a base salary of {_usd(a.amount)}, not the {_usd(intent.normalized_amount)} "
                    f"normalized level used in the adjustment.",
                    "The normalized compensation level management used.",
                    [],
                )
        if _COMPLETED_CLAIM_RE.search(narrative):
            for q in fact.key_statements:
                if _PLAN_RE.search(q.quote):
                    add(
                        fact,
                        q,
                        "describes the change as planned, not completed.",
                        "Management describes the change as already made.",
                        [],
                    )
                    break
    return out


# ---------------------------------------------------------------------------
# Rule-based entry classification
# ---------------------------------------------------------------------------


def _memo_theme(memo: str) -> str:
    text = _DATE_RE.sub(" ", memo)
    text = _MONTH_WORD_RE.sub(" ", text)
    text = re.sub(r"\$?\d[\d,./-]*", " ", text.lower())
    text = re.sub(r"[^a-z&]+", " ", text)
    return " ".join(w for w in text.split() if w not in _STOPWORDS)


def _docs_for_entry(entry: GLEntry, facts: list[DocFacts], primary: dict[str, list[str]]) -> list[str]:
    """Documents that are demonstrably about an entry: its bill, a reference its memo cites, or vendor + amount."""
    memo_refs = {v.lower() for _, v in _labeled_refs(entry.memo)}
    out: list[str] = []
    for f in facts:
        if (
            _entry_cites(entry, primary.get(f.doc_id, []))
            or memo_refs & {r.lower() for r in f.reference_numbers}
            or (_cp_match(f.counterparty, entry.counterparty) and _amount_matches(entry, [a.amount for a in f.amounts]))
        ):
            out.append(f.doc_id)
    return out


def _classify_personal(
    entries: list[GLEntry], facts: list[DocFacts], evidence: _Evidence
) -> list[EntryClassification]:
    business_docs = [
        (f, q) for f in facts for q in f.key_statements
        if _BUSINESS_PURPOSE_RE.search(q.quote) and not _PERSONAL_RE.search(q.quote)
    ]
    # Ties are decided per document over all entries at once, so a numbered document (an
    # expense report) ties only to the entry carrying its number, not to every same-sized trip.
    tied_by_doc = {f.doc_id: set(_tie_entries(f, entries, evidence, "business")) for f, _ in business_docs}
    out: list[EntryClassification] = []
    for e in entries:
        personal = _PERSONAL_RE.search(e.memo)
        business = _BUSINESS_MEMO_RE.search(e.memo)
        tied = [(f, q) for f, q in business_docs if e.entry_id in tied_by_doc[f.doc_id]]
        tied_docs = list(dict.fromkeys(f.doc_id for f, _ in tied))
        if personal:
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason=f"The GL memo identifies the cost as personal ({personal.group()}).",
            ))
        elif business:
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"The GL memo shows a business purpose ({business.group()}), so it is not a personal expense.",
                doc_ids=tied_docs,
            ))
        elif tied:
            fact, q = tied[0]
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"{fact.doc_id} records a business purpose for it.",
                doc_ids=tied_docs,
            ))
        else:
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason="No business-purpose evidence in the memo or linked documents.",
            ))
    return out


def _classify_event(
    adj: AdjustmentClaim,
    intent: AdjustmentIntent,
    entries: list[GLEntry],
    facts: list[DocFacts],
    evidence: _Evidence,
) -> list[EntryClassification]:
    # A vendor can bill several matters, so its name never identifies the event.
    cp_tokens = {t for name in intent.counterparties for t in _name_tokens(name)}
    title_kw = {k for k in _narrative_keywords(adj.title, "") if k not in _WEAK_KEYWORDS} - cp_tokens
    all_kw = {k for k in intent.keywords if k not in _WEAK_KEYWORDS and len(k) >= 4} - cp_tokens
    primary = (title_kw & all_kw) or title_kw
    secondary = all_kw - primary

    def kw_hits(text: str) -> list[str]:
        low = text.lower()
        hits_p = [k for k in sorted(primary) if _token_in(k, low)]
        hits_s = [k for k in sorted(secondary) if _token_in(k, low)]
        if hits_p:
            return hits_p + hits_s
        return hits_s if len(hits_s) >= 2 else []

    narrative_refs = _labeled_refs(f"{adj.title}\n{adj.description}")
    event_labeled: list[tuple[str, str]] = [(k, v) for k, v in narrative_refs if k in _EVENT_REF_KINDS]
    for e in entries:
        if kw_hits(e.memo):
            event_labeled.extend(_entry_event_refs(e))
    event_values = {v.lower() for _, v in event_labeled} | {r.lower() for r in intent.reference_numbers}
    event_docs: list[DocFacts] = []
    primary_by_doc_list = {f.doc_id: _primary_refs(f, evidence) for f in facts}
    primary_by_doc = {d: {r.lower() for r in refs} for d, refs in primary_by_doc_list.items()}
    for f in facts:
        refs = primary_by_doc[f.doc_id]
        if refs & event_values or kw_hits(f"{f.title}\n{_filename_title(f.doc_id)}"):
            event_docs.append(f)
    for f in event_docs:
        event_values |= primary_by_doc[f.doc_id]
    event_kinds = {k for k, _ in event_labeled}
    event_doc_ids = {f.doc_id for f in event_docs}

    decided: dict[str, EntryClassification] = {}
    undecided: list[GLEntry] = []
    for e in entries:
        refs = _entry_event_refs(e)
        cited = [v for _, v in refs if v.lower() in event_values] + (
            [e.doc_number] if e.doc_number and e.doc_number.lower() in event_values else []
        )
        hits = kw_hits(e.memo)
        if cited:
            doc_ids = sorted(f.doc_id for f in event_docs if primary_by_doc[f.doc_id] & {c.lower() for c in cited})
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason=f"Cites {cited[0]}, which is tied to the claimed event.", doc_ids=doc_ids,
            )
            continue
        conflicting = [(k, v) for k, v in refs if k in event_kinds and v.lower() not in event_values]
        if conflicting and not hits:
            kind, value = conflicting[0]
            claimed = sorted({v for k, v in event_labeled if k == kind})
            claimed_txt = f" ({kind.title()} {', '.join(claimed)})" if claimed else ""
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"Memo cites {kind.title()} {value}, a different {kind} from the claimed event{claimed_txt}.",
            )
            continue
        if hits:
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason=f"Memo refers to the claimed event (\"{hits[0]}\").",
            )
            continue
        contrary = _CONTRARY_THEME_RE.search(e.memo)
        has_event_group = any(kw_hits(x.memo) or _entry_cites(x, event_values) for x in entries if x is not e)
        if contrary and has_event_group:
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"Memo describes a recurring or general charge (\"{contrary.group()}\"), not the claimed "
                f"{_EVENT_LABEL.get(intent.event_type, 'event')} event.",
            )
            continue
        tied_docs = [
            f for f in facts
            if f.doc_id not in event_doc_ids
            and (_entry_cites(e, primary_by_doc[f.doc_id]) or (
                _cp_match(f.counterparty, e.counterparty) and _amount_matches(e, _recurring_fee_amounts(f))))
        ]
        recurring_doc = next((f for f in tied_docs if any(t.kind in ("retainer", "monthly_fee", "ongoing_services")
                                                          for t in f.terms)), None)
        if recurring_doc is not None and event_docs:
            term = next(t for t in recurring_doc.terms if t.kind in ("retainer", "monthly_fee", "ongoing_services"))
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"Billed under {recurring_doc.doc_id}, a standing arrangement ({term.text}), not the claimed event.",
                doc_ids=[recurring_doc.doc_id],
            )
            continue
        memo_event = _event_type(e.memo, "", AdjustmentCategory.OTHER)
        if intent.event_type != "other" and memo_event not in ("other", intent.event_type):
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"Memo describes {_EVENT_LABEL[memo_event]} activity, not the claimed "
                f"{_EVENT_LABEL.get(intent.event_type, 'event')} event.",
            )
            continue
        undecided.append(e)

    by_theme: dict[tuple[str, str], EntryClassification] = {}
    for e in entries:
        if e.entry_id in decided:
            key = (" ".join(sorted(_name_tokens(e.counterparty))), _memo_theme(e.memo))
            by_theme.setdefault(key, decided[e.entry_id])
    for e in undecided:
        key = (" ".join(sorted(_name_tokens(e.counterparty))), _memo_theme(e.memo))
        match = by_theme.get(key) if key[1] else None
        if match is not None:
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=match.qualifies,
                reason=f"Same counterparty and memo theme as {match.entry_id}: {match.reason}",
                doc_ids=list(match.doc_ids),
            )
        else:
            decided[e.entry_id] = EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason="No evidence separates this entry from the claimed event.",
            )
    out: list[EntryClassification] = []
    for e in entries:
        c = decided[e.entry_id]
        if not c.doc_ids and not c.reason.startswith("No evidence"):
            c = c.model_copy(update={"doc_ids": _docs_for_entry(e, facts, primary_by_doc_list)})
        out.append(c)
    return out


# ---------------------------------------------------------------------------
# Rule-based questions
# ---------------------------------------------------------------------------


def _long_date(iso: Optional[str]) -> str:
    """'2025-04-01' -> 'April 1, 2025' for text written to management."""
    try:
        d = date.fromisoformat(iso or "")
    except ValueError:
        return iso or ""
    return f"{d.strftime('%B')} {d.day}, {d.year}"


_SUCCESS_FEE_RE = _lex(r"\bsuccess fee\b|\btransaction fee\b|\bpayable (?:up)?on (?:closing|completion)\b", re.I)


def _followup_questions(adj: AdjustmentClaim, facts: list[DocFacts]) -> list[str]:
    """Questions the documents raise that no review flag covers.

    The engine already asks one templated question per flag; these are the follow-ups a
    senior would add from the documents themselves (who funded a settlement, whether a
    vacated role is backfilled, what a success fee will cost at closing).
    """
    out: list[str] = []
    for fact in facts:
        doc_type = (fact.doc_type or "").lower()
        if doc_type == "settlement_agreement":
            dated = f" (dated {_long_date(fact.doc_date)})" if fact.doc_date else ""
            out.append(
                f"Who funded the settlement under {fact.doc_id}{dated}, was any insurer payment received in full, and "
                "do any fees or obligations continue after it?"
            )
        elif doc_type == "separation_agreement":
            out.append(f"Has the role vacated under {fact.doc_id} been backfilled, and at what annual cost?")
        quotes = [q.quote for q in fact.key_statements] + [t.quote.quote for t in fact.terms] + [t.text for t in fact.terms]
        quotes += [a.quote.quote for a in fact.amounts]
        if any(_SUCCESS_FEE_RE.search(q) for q in quotes):
            out.append(
                f"What success fee is payable under {fact.doc_id} at closing, and were other sale-process fees "
                f"incurred but left out of {adj.adj_id}?"
            )
    return list(dict.fromkeys(out))


def _draft_questions_rules(adj: AdjustmentClaim, flags: list[Flag], facts: list[DocFacts]) -> list[str]:
    return _followup_questions(adj, facts)


# ---------------------------------------------------------------------------
# Rule-based implementation
# ---------------------------------------------------------------------------


class RuleBasedEvidenceAI:
    """Deterministic, offline evidence reader built from general lexicons and regexes."""

    name = "rules"

    def __init__(self) -> None:
        # Documents seen by extract_facts, so later calls can verify quotes and read full text.
        self._docs: dict[str, SourceDocument] = {}

    def remember(self, doc: SourceDocument) -> None:
        self._docs[doc.doc_id] = doc

    def extract_facts(self, doc: SourceDocument) -> DocFacts:
        self.remember(doc)
        if not doc.pages:
            stem = _filename_title(doc.doc_id)
            doc_type = next((t for t, rx in _TYPE_TITLE_RULES if rx.search(stem)), "other")
            return DocFacts(doc_id=doc.doc_id, doc_type=doc_type, title=stem, extractor=self.name)
        facts = _DocReader(doc).facts()
        return _verify_facts(facts, {doc.doc_id: doc})

    def parse_intent(self, adj: AdjustmentClaim) -> AdjustmentIntent:
        return _parse_intent_rules(adj)

    def find_contradictions(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        facts: list[DocFacts],
        entries: list[GLEntry],
    ) -> list[Contradiction]:
        return _find_contradictions_rules(adj, intent, facts, entries, _Evidence(self._docs))

    def classify_entries(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        entries: list[GLEntry],
        facts: list[DocFacts],
    ) -> list[EntryClassification]:
        evidence = _Evidence(self._docs)
        if intent.asserts_personal:
            return _classify_personal(entries, facts, evidence)
        return _classify_event(adj, intent, entries, facts, evidence)

    def draft_questions(self, adj: AdjustmentClaim, flags: list[Flag], facts: list[DocFacts]) -> list[str]:
        """Follow-up questions the documents raise. The engine already templates one question per
        flag (qoe/propose.py), so repeating them here would only duplicate the list."""
        return _draft_questions_rules(adj, flags, facts)


# ---------------------------------------------------------------------------
# OpenAI-compatible LLM implementation
# ---------------------------------------------------------------------------


def _verified_entry_ids(
    fact: DocFacts, proposed: list[str], entries: dict[str, GLEntry], evidence: _Evidence
) -> list[str]:
    """Entry ids the model tied to a document, kept only when code can see the tie: a
    reference or document number, the same amount for the same counterparty, or a memo
    naming the document's event. Date proximity alone is not a tie."""
    candidates = [entries[x] for x in dict.fromkeys(proposed)]
    tied = set(_tie_entries(fact, candidates, evidence, "statement"))
    return [e.entry_id for e in candidates if e.entry_id in tied]


def _nullable(kind: str) -> dict[str, Any]:
    return {"type": [kind, "null"]}


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "properties": properties, "required": list(properties)}


_QUOTE_ITEM = _obj({"page": {"type": "integer"}, "quote": {"type": "string"}})
EXTRACT_FACTS_SCHEMA = _obj(
    {
        "doc_type": {"type": "string", "enum": list(DOC_TYPES)},
        "title": {"type": "string"},
        "counterparty": _nullable("string"),
        "doc_date": _nullable("string"),
        "reference_numbers": {"type": "array", "items": {"type": "string"}},
        "amounts": {
            "type": "array",
            "items": _obj({"label": {"type": "string"}, "amount": {"type": "string"}, "page": {"type": "integer"},
                           "quote": {"type": "string"}}),
        },
        "service_period_start": _nullable("string"),
        "service_period_end": _nullable("string"),
        "is_draft": {"type": "boolean"},
        "is_signed": _nullable("boolean"),
        "terms": {
            "type": "array",
            "items": _obj({"kind": {"type": "string", "enum": list(TERM_KINDS)}, "text": {"type": "string"},
                           "page": {"type": "integer"}, "quote": {"type": "string"}}),
        },
        "key_statements": {"type": "array", "items": _QUOTE_ITEM},
    }
)
PARSE_INTENT_SCHEMA = _obj(
    {
        "counterparties": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "reference_numbers": {"type": "array", "items": {"type": "string"}},
        "event_type": {"type": "string", "enum": list(EVENT_TYPES)},
        "asserts_nonrecurring": {"type": "boolean"},
        "asserts_personal": {"type": "boolean"},
        "is_pro_forma": {"type": "boolean"},
        "is_normalization": {"type": "boolean"},
        "normalized_amount": _nullable("string"),
        "event_months": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    }
)
CONTRADICTIONS_SCHEMA = _obj(
    {
        "contradictions": {
            "type": "array",
            "items": _obj({"doc_id": {"type": "string"}, "statement": {"type": "string"}, "page": {"type": "integer"},
                           "quote": {"type": "string"}, "conflicts_with": {"type": "string"},
                           "entry_ids": {"type": "array", "items": {"type": "string"}}}),
        }
    }
)
CLASSIFY_ENTRIES_SCHEMA = _obj(
    {
        "classifications": {
            "type": "array",
            "items": _obj({"entry_id": {"type": "string"}, "qualifies": {"type": "boolean"},
                           "reason": {"type": "string"}, "doc_ids": {"type": "array", "items": {"type": "string"}},
                           "page": _nullable("integer"), "quote": {"type": "string"}}),
        }
    }
)
QUESTIONS_SCHEMA = _obj({"questions": {"type": "array", "items": {"type": "string"}}})

_PROMPT_FILES = {
    "extract_facts": "qoe_extract_facts_v1.txt",
    "parse_intent": "qoe_parse_intent_v1.txt",
    "contradictions": "qoe_contradictions_v1.txt",
    "classify_entries": "qoe_classify_entries_v1.txt",
    "questions": "qoe_questions_v1.txt",
}
_NOT_STATED = {"", "not stated", "n/a", "none", "null", "unknown"}


def load_prompt(task: str) -> str:
    """System prompt text for an LLM task (prompts/qoe_<task>_v1.txt)."""
    return (PROMPTS_DIR / _PROMPT_FILES[task]).read_text(encoding="utf-8")


def _stated(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in _NOT_STATED else text


def _iso_or_none(value: Any) -> Optional[str]:
    text = _stated(value)
    if text is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text


def _amount_in_quote(amount: str, quote: str) -> bool:
    """The model may only report an amount that is written inside its own quote."""
    target = abs(D(amount))
    for _, _, value, _ in _money_hits(quote, bare=True):
        if value == target:
            return True
    if target != target.to_integral_value():
        return False
    whole = str(int(target))
    for written in (f"{int(target):,}", whole):
        # a whole amount may be written without cents ("120,000"), but not as the start of "120,000.50"
        if re.search(rf"(?<![\d,.]){re.escape(written)}(?![\d,]|\.\d*[1-9])", quote):
            return True
    return False


def _figures_in_quote(text: str, quote: str) -> bool:
    """Every money figure a description names is written in its quote."""
    for _, _, value, _ in _money_hits(text, bare=True):
        if not _amount_in_quote(fmt(value), quote):
            return False
    return True


def _stated_dates(doc: SourceDocument) -> tuple[set[str], set[str], set[str]]:
    """(dates, first days of stated months, last days of stated months) written in a document, ISO."""
    days: set[str] = set()
    starts: set[str] = set()
    ends: set[str] = set()
    for page in doc.pages:
        hits = _find_dates(page.text)
        days.update(h.iso for h in hits)
        for _, _, month in _month_year_hits(page.text, hits):
            starts.add(_iso_month_start(month))
            ends.add(_iso_month_end(month))
    return days, starts, ends


def _merge_signed(llm: Any, rules: Optional[bool], llm_quotes: list[EvidenceQuote]) -> Optional[bool]:
    """Execution status from two readers, conservatively: unsigned if either says so."""
    llm_value = llm if isinstance(llm, bool) else None
    if llm_value is False or rules is False:
        return False
    if rules is True:
        return True
    if llm_value is True and any(_SIGNED_RE.search(q.quote) for q in llm_quotes):
        return True  # the model showed a verbatim signature mark
    return None


# Types that exempt a document from the draft / unsigned challenge (qoe/challenge.py).
_UNSIGNABLE = frozenset({"invoice", "correspondence", "memo", "payroll"})


def _merge_doc_type(llm: str, rules: str, is_draft: bool, is_signed: Optional[bool]) -> str:
    """The rules' document type; the model's only where the rules found none, and never one that
    would take a draft or unsigned document out of the execution check."""
    if llm not in DOC_TYPES or llm == rules or rules != "other":
        return rules
    if llm in _UNSIGNABLE and (is_draft or is_signed is False):
        return rules
    return llm


_CONTENT_STOP = frozenset(
    """that this with from have been were will would shall which their there they them than then into
    about under over also only such other more most some each does document documents letter states shows
    says management company entry entries adjustment cost costs expense expenses""".split()
)


def _content_words(text: str) -> set[str]:
    """Distinctive words (first six letters, so 'recurring' meets 'recurs') for overlap tests."""
    return {w[:6] for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _CONTENT_STOP}


def _statement_backed(statement: str, quote: str) -> bool:
    """An AI statement may only assert what its quote shows: every figure and date it names is
    in the quote, and it shares at least one distinctive word with it."""
    if not _figures_in_quote(statement, quote):
        return False
    quote_dates = {h.iso for h in _find_dates(quote)}
    if any(h.iso not in quote_dates for h in _find_dates(statement)):
        return False
    return bool(_content_words(statement) & _content_words(quote))


def _merge_intent(llm: AdjustmentIntent, rules: AdjustmentIntent) -> AdjustmentIntent:
    """The model's reading of the narrative on top of the rules': search terms are the union and
    each assertion holds if either reader finds it, so an omission cannot narrow the review."""

    def union(a: list[str], b: list[str]) -> list[str]:
        out: list[str] = []
        for x in a + b:
            if x.lower() not in {y.lower() for y in out}:
                out.append(x)
        return out

    return llm.model_copy(
        update={
            "counterparties": union(llm.counterparties, rules.counterparties),
            "keywords": union(llm.keywords, rules.keywords),
            "reference_numbers": union(llm.reference_numbers, rules.reference_numbers),
            "event_type": llm.event_type if llm.event_type != "other" else rules.event_type,
            "asserts_nonrecurring": llm.asserts_nonrecurring or rules.asserts_nonrecurring,
            "asserts_personal": llm.asserts_personal or rules.asserts_personal,
            "is_pro_forma": llm.is_pro_forma or rules.is_pro_forma,
            "is_normalization": llm.is_normalization or rules.is_normalization,
            "normalized_amount": llm.normalized_amount or rules.normalized_amount,
            "event_months": sorted(set(llm.event_months) | set(rules.event_months)),
        }
    )


def _require_keys(data: Any, schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("response is not a JSON object")
    missing = [k for k in schema["required"] if k not in data]
    if missing:
        raise ValueError(f"response is missing fields: {', '.join(missing)}")
    return data


def _entry_payload(e: GLEntry) -> dict[str, Any]:
    return {
        "entry_id": e.entry_id,
        "date": e.date,
        "account": f"{e.account} {e.account_name}".strip(),
        "counterparty": e.counterparty,
        "doc_number": e.doc_number,
        "memo": e.memo,
        "amount": e.amount,
    }


def _claim_payload(adj: AdjustmentClaim) -> dict[str, Any]:
    return {
        "adj_id": adj.adj_id,
        "title": adj.title,
        "category": adj.category.value,
        "category_raw": adj.category_raw,
        "description": adj.description,
        "gl_accounts": adj.gl_accounts,
        "support_refs": adj.support_refs,
        "amounts": adj.amounts,
    }


class OpenAICompatibleEvidenceAI:
    """Evidence reader backed by an OpenAI-compatible chat-completions endpoint.

    Every call uses a strict JSON schema, temperature 0 and a fixed seed. The
    output is validated: quotes must be verbatim, amounts must appear in their
    quote, references and names must appear in the source. Any failed call
    (exception, invalid JSON, missing fields) falls back to the rule-based
    reader for that call and is recorded in ``fallbacks``.
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Any = None,
        *,
        timeout: float = 120.0,
        max_doc_chars: int = 60000,
    ) -> None:
        if not model:
            raise ValueError("OpenAICompatibleEvidenceAI needs a model name")
        self.model = model
        self.name = f"llm:{model}"
        if client is None:
            from openai import OpenAI

            client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.client = client
        self.rules = RuleBasedEvidenceAI()
        self.fallbacks: list[str] = []
        self.dropped_quotes = 0  # quotes dropped outside DocFacts (contradictions)
        self.max_doc_chars = max_doc_chars
        self._docs: dict[str, SourceDocument] = {}
        self._prompts: dict[str, str] = {}

    # -- plumbing ---------------------------------------------------------

    def _prompt(self, task: str) -> str:
        if task not in self._prompts:
            self._prompts[task] = load_prompt(task)
        return self._prompts[task]

    def _call(self, task: str, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._prompt(task)},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": f"qoe_{task}", "strict": True, "schema": schema},
            },
            temperature=0,
            seed=42,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("empty response")
        return _require_keys(json.loads(content), schema)

    def _fallback(self, call: str, key: str, exc: Exception) -> None:
        self.fallbacks.append(f"{call}[{key}]: {type(exc).__name__}: {str(exc)[:200]}")

    def _pages_payload(self, doc: SourceDocument) -> list[dict[str, Any]]:
        budget = self.max_doc_chars
        pages: list[dict[str, Any]] = []
        for p in doc.pages:
            if budget <= 0:
                break
            pages.append({"page": p.page, "text": p.text[:budget]})
            budget -= len(p.text)
        return pages

    def _doc_summary(self, fact: DocFacts, with_text: bool) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "doc_id": fact.doc_id,
            "title": fact.title,
            "doc_type": fact.doc_type,
            "counterparty": fact.counterparty,
            "doc_date": fact.doc_date,
            "reference_numbers": fact.reference_numbers,
            "service_period": [fact.service_period_start, fact.service_period_end],
            "is_draft": fact.is_draft,
            "is_signed": fact.is_signed,
            "amounts": [{"label": a.label, "amount": a.amount, "page": a.quote.page, "quote": a.quote.quote}
                        for a in fact.amounts],
            "terms": [{"kind": t.kind, "text": t.text, "page": t.quote.page, "quote": t.quote.quote}
                      for t in fact.terms],
            "key_statements": [{"page": q.page, "quote": q.quote} for q in fact.key_statements],
        }
        doc = self._docs.get(fact.doc_id)
        if with_text and doc is not None:
            summary["pages"] = self._pages_payload(doc)
        return summary

    # -- EvidenceAI -------------------------------------------------------

    def extract_facts(self, doc: SourceDocument) -> DocFacts:
        self._docs[doc.doc_id] = doc
        self.rules.remember(doc)
        payload = {
            "doc_id": doc.doc_id,
            "file_name": doc.relpath,
            "media_type": doc.media_type,
            "pages": self._pages_payload(doc),
        }
        try:
            data = self._call("extract_facts", payload, EXTRACT_FACTS_SCHEMA)
            return self._facts_from_response(doc, data)
        except Exception as exc:  # noqa: BLE001 - any failure falls back to rules for this call
            self._fallback("extract_facts", doc.doc_id, exc)
            return self.rules.extract_facts(doc)

    def _facts_from_response(self, doc: SourceDocument, data: dict[str, Any]) -> DocFacts:
        """The model's reading, checked against the page text and reconciled with the rules.

        Quotes must be verbatim (and long enough to prove something); an amount must be written
        in its own quote; references and names must appear in the text. Fields the model states
        without a quote cannot be checked that way, so they are reconciled with the rule-based
        reading of the same pages, which is the floor: the model may add facts the rules missed
        but never remove one or overrule it (SPEC §1: AI proposes, code decides).

        - is_draft: draft if either reader says so. is_signed: unsigned if either says so;
          signed only if the rules agree or a verified quote shows a signature mark.
        - doc_type: the rules' type; the model's only when the rules could not classify the
          document, and never a type that would exempt a draft or unsigned document.
        - service period and document date: the rules' reading; the model's only when the
          rules found none and every date it gives is written in the document.
        - amounts: the rules' labels for amounts both read; the model's other amounts are added.
        - terms: a term's description may not name an amount its quote does not contain; the
          rules' terms and key statements are always kept.
        """
        docs_by_id = {doc.doc_id: doc}
        full_text = doc.full_text
        full_lower = _norm_space(full_text).lower()
        rules = self.rules.extract_facts(doc)
        dropped = 0

        def quote(item: dict[str, Any]) -> Optional[EvidenceQuote]:
            nonlocal dropped
            try:
                q = EvidenceQuote(doc_id=doc.doc_id, page=int(item["page"]), quote=str(item["quote"]))
            except (KeyError, ValueError, TypeError):
                dropped += 1
                return None
            if not verify_quote(q, docs_by_id):
                dropped += 1
                return None
            return q

        rule_values = {a.amount for a in rules.amounts}
        amounts: list[AmountFact] = list(rules.amounts)
        for item in data.get("amounts") or []:
            q = quote(item)
            if q is None:
                continue
            try:
                amount = fmt(abs(D(item.get("amount"))))
            except (ValueError, TypeError):
                dropped += 1
                continue
            if D(amount) == 0 or not _amount_in_quote(amount, q.quote):
                dropped += 1
                continue
            if amount in rule_values:
                continue  # the rules read this amount: their label (and quote) stand
            label = str(item.get("label") or "line").strip().lower().replace(" ", "_")
            amounts.append(AmountFact(label=label if label in AMOUNT_LABELS else "line", amount=amount, quote=q))
            rule_values.add(amount)
        terms: list[TermFact] = list(rules.terms)
        seen_terms = {(t.kind, t.quote.page, t.quote.quote) for t in terms}
        for item in data.get("terms") or []:
            q = quote(item)
            if q is None:
                continue
            kind = str(item.get("kind") or "other")
            kind = kind if kind in TERM_KINDS else "other"
            text = _norm_space(str(item.get("text") or ""))
            if not text or not _figures_in_quote(text, q.quote):
                text = kind.replace("_", " ")  # a description may not carry a figure the document does not state
            if (kind, q.page, q.quote) not in seen_terms:
                seen_terms.add((kind, q.page, q.quote))
                terms.append(TermFact(kind=kind, text=text, quote=q))
        statements: list[EvidenceQuote] = list(rules.key_statements)
        llm_statements: list[EvidenceQuote] = []
        for item in data.get("key_statements") or []:
            q = quote(item)
            if q is None:
                continue
            llm_statements.append(q)
            if all((q.page, q.quote) != (x.page, x.quote) for x in statements):
                statements.append(q)
        refs = list(rules.reference_numbers)
        for r in (_stated(x) for x in data.get("reference_numbers") or []):
            # A reference must be a whole token of the text and long enough to identify something.
            if r and len(re.sub(r"[^0-9A-Za-z]", "", r)) >= 3 and _token_in(r, full_text):
                if r.lower() not in {x.lower() for x in refs}:
                    refs.append(r)
        counterparty = _stated(data.get("counterparty"))
        if counterparty and _norm_space(counterparty).lower() not in full_lower:
            counterparty = None
        title = _stated(data.get("title"))
        if title and _norm_space(title).lower() not in full_lower:
            title = None  # an unstated title would steer document linking
        is_draft = bool(data.get("is_draft")) or rules.is_draft
        is_signed = _merge_signed(data.get("is_signed"), rules.is_signed, llm_statements)
        doc_type = _merge_doc_type(str(data.get("doc_type") or "other"), rules.doc_type, is_draft, is_signed)
        stated = _stated_dates(doc)
        sp_start, sp_end = rules.service_period_start, rules.service_period_end
        if sp_start is None and sp_end is None:
            llm_start = _iso_or_none(data.get("service_period_start"))
            llm_end = _iso_or_none(data.get("service_period_end"))
            if (llm_start or llm_end) and (llm_start is None or llm_start in stated[0] | stated[1]) and (
                llm_end is None or llm_end in stated[0] | stated[2]
            ):
                sp_start, sp_end = llm_start, llm_end
        doc_date = rules.doc_date
        if doc_date is None:
            llm_date = _iso_or_none(data.get("doc_date"))
            doc_date = llm_date if llm_date in stated[0] else None
        return DocFacts(
            doc_id=doc.doc_id,
            doc_type=doc_type,
            title=title or rules.title or _filename_title(doc.doc_id),
            counterparty=counterparty or rules.counterparty,
            doc_date=doc_date,
            reference_numbers=refs,
            amounts=amounts,
            service_period_start=sp_start,
            service_period_end=sp_end,
            is_draft=is_draft,
            is_signed=is_signed,
            terms=terms,
            key_statements=statements,
            extractor=self.name,
            dropped_quotes=dropped + rules.dropped_quotes,
        )

    def parse_intent(self, adj: AdjustmentClaim) -> AdjustmentIntent:
        try:
            data = self._call("parse_intent", {"adjustment": _claim_payload(adj)}, PARSE_INTENT_SCHEMA)
            narrative = f"{adj.title}\n{adj.description}\n{adj.category_raw}"
            low = _norm_space(narrative).lower()
            counterparties = [c for c in (_stated(x) for x in data.get("counterparties") or [])
                              if c and _norm_space(c).lower() in low]
            refs = [r for r in (_stated(x) for x in data.get("reference_numbers") or []) if r and r.lower() in low]
            keywords = [k.lower() for k in (_stated(x) for x in data.get("keywords") or []) if k]
            keywords = _without_names(keywords, counterparties, narrative)
            normalized = _stated(data.get("normalized_amount"))
            if normalized is not None:
                try:
                    normalized = fmt(abs(D(normalized)))
                except ValueError:
                    normalized = None
            if normalized is not None and not _amount_in_quote(normalized, narrative):
                normalized = None  # the model may not compute a level the narrative does not state
            months = [
                m for m in data.get("event_months") or [] if isinstance(m, str) and re.fullmatch(r"\d{4}-\d{2}", m)
            ]
            event_type = str(data.get("event_type") or "other")
            llm = AdjustmentIntent(
                adj_id=adj.adj_id,
                counterparties=list(dict.fromkeys(counterparties)),
                keywords=list(dict.fromkeys(keywords)),
                reference_numbers=list(dict.fromkeys(refs)),
                event_type=event_type if event_type in EVENT_TYPES else "other",
                asserts_nonrecurring=bool(data.get("asserts_nonrecurring")),
                asserts_personal=bool(data.get("asserts_personal")),
                is_pro_forma=bool(data.get("is_pro_forma")),
                is_normalization=bool(data.get("is_normalization")),
                normalized_amount=normalized,
                event_months=sorted(set(months)),
                notes=f"{self.name}: {_norm_space(str(data.get('notes') or ''))}".strip(),
            )
        except Exception as exc:  # noqa: BLE001
            self._fallback("parse_intent", adj.adj_id, exc)
            return self.rules.parse_intent(adj)
        return _merge_intent(llm, self.rules.parse_intent(adj))

    def find_contradictions(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        facts: list[DocFacts],
        entries: list[GLEntry],
    ) -> list[Contradiction]:
        payload = {
            "adjustment": _claim_payload(adj),
            "intent": intent.model_dump(mode="json"),
            "documents": [self._doc_summary(f, with_text=True) for f in facts],
            "entries": [_entry_payload(e) for e in entries],
        }
        try:
            data = self._call("contradictions", payload, CONTRADICTIONS_SCHEMA)
        except Exception as exc:  # noqa: BLE001
            self._fallback("find_contradictions", adj.adj_id, exc)
            return self.rules.find_contradictions(adj, intent, facts, entries)
        evidence = _Evidence(self._docs)
        facts_by_id = {f.doc_id: f for f in facts}
        known_entries = {e.entry_id: e for e in entries}
        out: list[Contradiction] = []
        for item in data.get("contradictions") or []:
            try:
                q = EvidenceQuote(doc_id=str(item["doc_id"]), page=int(item["page"]), quote=str(item["quote"]))
            except (KeyError, ValueError, TypeError):
                self.dropped_quotes += 1
                continue
            if q.doc_id not in facts_by_id or not evidence.verified(q, facts_by_id):
                self.dropped_quotes += 1
                continue
            statement = _norm_space(str(item.get("statement") or ""))
            if not statement:
                continue
            if not _statement_backed(statement, q.quote):
                # The engine shows the statement as what the document says: a quote that does not
                # carry its figures, dates or subject cannot stand behind it.
                self.dropped_quotes += 1
                continue
            out.append(
                Contradiction(
                    doc_id=q.doc_id,
                    statement=statement,
                    quote=q,
                    conflicts_with=_norm_space(str(item.get("conflicts_with") or "")) or "management's explanation",
                    entry_ids=_verified_entry_ids(
                        facts_by_id[q.doc_id], [x for x in item.get("entry_ids") or [] if x in known_entries],
                        known_entries, evidence,
                    ),
                )
            )
        # The rule-based detectors are the floor: an answer that leaves out a conflict they find
        # (a model obeying "report nothing" planted in a document) cannot remove the challenge.
        seen = {(c.doc_id, c.quote.page, c.quote.quote) for c in out}
        for c in self.rules.find_contradictions(adj, intent, facts, entries):
            if (c.doc_id, c.quote.page, c.quote.quote) not in seen:
                seen.add((c.doc_id, c.quote.page, c.quote.quote))
                out.append(c)
        return out

    def classify_entries(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        entries: list[GLEntry],
        facts: list[DocFacts],
    ) -> list[EntryClassification]:
        payload = {
            "adjustment": _claim_payload(adj),
            "intent": intent.model_dump(mode="json"),
            "entries": [_entry_payload(e) for e in entries],
            "documents": [self._doc_summary(f, with_text=False) for f in facts],
        }
        try:
            data = self._call("classify_entries", payload, CLASSIFY_ENTRIES_SCHEMA)
        except Exception as exc:  # noqa: BLE001
            self._fallback("classify_entries", adj.adj_id, exc)
            return self.rules.classify_entries(adj, intent, entries, facts)
        known_docs = {f.doc_id for f in facts}
        facts_by_id = {f.doc_id: f for f in facts}
        evidence = _Evidence(self._docs)
        # The rules classify every entry (they need the whole event group); a removal they make is
        # the floor, and one only the model proposes must show the passage it rests on.
        rules = {c.entry_id: c for c in self.rules.classify_entries(adj, intent, entries, facts)}
        by_id: dict[str, EntryClassification] = {}
        for item in data.get("classifications") or []:
            entry_id = str(item.get("entry_id") or "")
            reason = _norm_space(str(item.get("reason") or ""))
            if entry_id not in rules or entry_id in by_id or not reason:
                continue
            qualifies = bool(item.get("qualifies"))
            doc_ids = [d for d in item.get("doc_ids") or [] if d in known_docs]
            if not qualifies and rules[entry_id].qualifies:
                backing = self._classification_quote(item, doc_ids, reason, facts_by_id, evidence)
                # Without a backing passage the proposal carries no document, so the engine keeps
                # the entry and asks the reviewer instead of removing it.
                doc_ids = [backing.doc_id] + [d for d in doc_ids if d != backing.doc_id] if backing else []
            by_id[entry_id] = EntryClassification(entry_id=entry_id, qualifies=qualifies, reason=reason, doc_ids=doc_ids)
        for entry_id, rule in rules.items():
            if not rule.qualifies or entry_id not in by_id:
                by_id[entry_id] = rule
        return [by_id[e.entry_id] for e in entries]

    def _classification_quote(
        self,
        item: dict[str, Any],
        doc_ids: list[str],
        reason: str,
        facts_by_id: dict[str, DocFacts],
        evidence: "_Evidence",
    ) -> Optional[EvidenceQuote]:
        """The verbatim passage (in one of the cited documents) that backs a proposed removal."""
        text = str(item.get("quote") or "")
        if not text.strip():
            return None
        try:
            page = int(item.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        for doc_id in doc_ids:
            q = EvidenceQuote(doc_id=doc_id, page=max(page, 1), quote=text)
            if evidence.verified(q, facts_by_id) and _statement_backed(reason, text):
                return q
        self.dropped_quotes += 1
        return None

    def draft_questions(self, adj: AdjustmentClaim, flags: list[Flag], facts: list[DocFacts]) -> list[str]:
        payload = {
            "adjustment": _claim_payload(adj),
            "flags": [
                {
                    "code": f.code.value,
                    "severity": f.severity.value,
                    "message": f.message,
                    "period_label": f.period_label,
                    "amount_impact": f.amount_impact,
                    "doc_ids": f.doc_ids,
                    "related_adj_ids": f.related_adj_ids,
                    "quotes": [q.quote for q in f.quotes],
                }
                for f in flags
            ],
            "documents": [
                {"doc_id": f.doc_id, "title": f.title, "doc_type": f.doc_type, "doc_date": f.doc_date}
                for f in facts
            ],
        }
        try:
            data = self._call("questions", payload, QUESTIONS_SCHEMA)
            questions = [_norm_space(str(q)) for q in data.get("questions") or []]
            # An empty list is a valid answer: the engine already asks one question per flag.
            return list(dict.fromkeys(q for q in questions if q))
        except Exception as exc:  # noqa: BLE001
            self._fallback("draft_questions", adj.adj_id, exc)
            return self.rules.draft_questions(adj, flags, facts)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

ENV_BASE_URL = "QOE_LLM_BASE_URL"
ENV_API_KEY = "QOE_LLM_API_KEY"
ENV_MODEL = "QOE_LLM_MODEL"


def get_ai(mode: str = "rules") -> EvidenceAI:
    """"rules" (default, offline) or "llm" / "llm:<model>" (OpenAI-compatible endpoint from the environment)."""
    choice = (mode or "rules").strip()
    if choice.lower() == "rules":
        return RuleBasedEvidenceAI()
    if choice.lower() == "llm" or choice.lower().startswith("llm:"):
        model = choice[4:].strip() if ":" in choice else os.environ.get(ENV_MODEL, "").strip()
        base_url = os.environ.get(ENV_BASE_URL, "").strip()
        api_key = os.environ.get(ENV_API_KEY, "").strip()
        missing = [
            name
            for name, value in ((ENV_BASE_URL, base_url), (ENV_API_KEY, api_key), (ENV_MODEL, model))
            if not value
        ]
        if missing:
            raise RuntimeError(
                "LLM mode needs these environment variables: "
                + ", ".join(missing)
                + f" (set {ENV_API_KEY}=EMPTY for a local server without auth), or use mode='rules'."
            )
        return OpenAICompatibleEvidenceAI(model=model, base_url=base_url, api_key=api_key)
    raise ValueError(f"unknown AI mode {mode!r}: expected 'rules', 'llm' or 'llm:<model>'")
