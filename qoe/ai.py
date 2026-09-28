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
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Optional

from qoe.ai_base import (
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
    FlagCode,
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
_DATE_WINDOW_DAYS = 45

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
    removed remove eliminate eliminated ebitda fy ttm year years month months monthly annual annually gl account accounts
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
        ("amount_paid", r"amount paid|total paid|\bpaid\b|registration fee"),
        ("fee", r"\bfees?\b"),
    )
]
_MONTHLY_AFTER_RE = _lex(r"^\s*(?:per month|/\s?mo(?:nth)?\b|a month\b|each month|every month|monthly\b)", re.I)
_HOURLY_AFTER_RE = _lex(r"^\s*(?:per hour|/\s?h(?:ou)?r\b|an hour|hourly)", re.I)
_SETTLEMENT_AFTER_RE = _lex(r"^\s*\)?\s*\(?\s*(?:the\s+)?[\"“]settlement (?:amount|payment)", re.I)
_INSTALLMENT_WORD_RE = _lex(r"\binstall?ments?\b", re.I)
_MONTHLY_CUE_RE = _lex(r"per month|/\s?mo(?:nth)?\b|a month\b|each month|every month|\bmonthly\b", re.I)
_EXPLICIT_MONTHLY_TERM_RE = _lex(
    r"monthly (?:fee|subscription|charge|service fee|retainer|license|licence|dues|rent)", re.I
)

_AUTO_RENEW_RE = _lex(
    r"renews? automatically|automatically renew(?:s|ed)?|auto-?renew(?:s|al|ing)?|shall renew for (?:successive|additional)"
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
    r"|in full and final settlement|full and final|in full satisfaction",
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
    r"\bwe (?:plan|intend|expect|anticipate) to\b|\btargeting\b|\bplanned\b|\bwill be (?:eliminated|reduced|implemented)\b"
    r"|\bprojected\b|\bexpected to (?:save|reduce)\b|\bhave not (?:yet )?(?:started|begun|been)\b|\bnot yet\b",
    re.I,
)
_RECOVERY_RE = _lex(
    r"insurer (?:shall|will) pay|paid (?:directly )?by (?:the )?(?:insurer|carrier)|funded by (?:the )?(?:insurer|carrier)"
    r"|net (?:claim )?payment|deductible|proceeds|reimburse",
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
                      r"|insurance claim|explanation of benefits|certificate of insurance|policy (?:declarations|renewal)"),
        ("payroll", r"payroll (?:register|summary|journal|report)|pay ?stub|earnings statement|pay statement"),
        ("memo", r"\bmemo(?:randum)?\b"),
        ("invoice", r"\binvoice\b|\bbill\b|statement of account|\breceipt\b"),
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
    r"not (?:yet )?executed|unexecuted|for discussion purposes only|draft for discussion|subject to (?:further )?revision"
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
    """(kind, value) reference numbers introduced by a label ("Matter 2291", "Claim No. FL-24-1")."""
    out: list[tuple[str, str]] = []
    for m in _REF_RE.finditer(text):
        label = re.sub(r"\s+", " ", m.group("label").lower())
        value = m.group("val").rstrip(".:-/")
        marker = bool(m.group("marker"))
        if len(value) < 3 and not (marker and value.isdigit()):
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
    if nxt[:1].islower():
        return True
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
        found: Optional[tuple[int, str]] = None
        for i, line in enumerate(self.first_lines[:14]):
            if self._is_skippable(line):
                continue
            sub = _SUBJECT_RE.match(line)
            if sub:
                found = (i, sub.group("val").strip())
                break
            if _FIELD_LINE_RE.match(line) or len(line) > 110:
                continue
            if _TITLE_WORD_RE.search(line):
                found = (i, line.strip())
                break
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
        for i, line in enumerate(lines[:40]):
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
                # an agenda or itinerary often states its dates on a line of their own
                standalone = page is self.first and line in header_lines and not re.search(
                    r"[A-Za-z]{2,}", _MONTH_WORD_RE.sub("", text[line[0] : m.start()] + text[m.end() : line[1]])
                )
                if standalone or _SP_CUE_RE.search(text[max(s0, m.start() - 100) : m.start()]):
                    mo = _month_number(m.group("m"))
                    y = int(m.group("y"))
                    d1 = _safe_date(y, mo or 0, int(m.group("d1"))) if mo else None
                    d2 = _safe_date(y, mo or 0, int(m.group("d2"))) if mo else None
                    if d1 and d2 and d1 <= d2:
                        return d1.isoformat(), d2.isoformat()
            points: list[tuple[int, int, str, str]] = [(h.start, h.end, h.iso, h.iso) for h in dates]
            points += [(s, e, _iso_month_start(mo), _iso_month_end(mo)) for s, e, mo in _month_year_hits(text, dates)]
            points.sort()
            for a, b in zip(points, points[1:]):
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
            for s, e, mo in _month_year_hits(text, dates):
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
            key = (kind, text.lower())
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
                monthly = _MONTHLY_CUE_RE.search(sent)
                if monthly and not installment_ctx:
                    money = [h for h in _money_hits(text, s, e)]
                    explicit = _EXPLICIT_MONTHLY_TERM_RE.search(sent)
                    if money or explicit:
                        is_retainer = re.search(r"\bretainer\b", sent, re.I) is not None
                        kind = "retainer" if is_retainer else "monthly_fee"
                        if money:
                            # the amount nearest the monthly cue is the fee
                            cue_pos = s + monthly.start()
                            ms, me, _, _ = min(money, key=lambda h: abs(h[0] - cue_pos))
                            raw = text[ms:me]
                            desc = f"retainer of {raw} per month" if is_retainer else f"monthly fee of {raw}"
                        else:
                            desc = "monthly retainer (amount not stated)" if is_retainer else "monthly fee (amount not stated)"
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
                    if n and hits and hits[0].start == s + m.end():
                        start_d = date.fromisoformat(hits[0].iso)
                        end_d = _term_end(start_d, n, unit)
                        add(
                            "term_end",
                            f"term ends {end_d.isoformat()} ({n}-{unit.lower()} term commencing {start_d.isoformat()})",
                            page.quote(s + m.start(), hits[0].end),
                        )
                        break
                for m in _TERM_EXPIRY_RE.finditer(sent):
                    hits = _find_dates(text, s + m.end(), e)
                    if hits and hits[0].start == s + m.end():
                        add("term_end", f"term ends {hits[0].iso}", page.quote(s + m.start(), hits[0].end))
                        break
                if _TERM_WORD_RE.search(sent):
                    hits = _find_dates(text, s, e)
                    for a, b in zip(hits, hits[1:]):
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
    return AdjustmentIntent(
        adj_id=adj.adj_id,
        counterparties=_narrative_counterparties(title, description),
        keywords=_narrative_keywords(title, description),
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


def _near_doc_dates(entry: GLEntry, fact: DocFacts, days: int = _DATE_WINDOW_DAYS) -> bool:
    ed = _entry_date(entry)
    if ed is None:
        return False
    if fact.service_period_start and fact.service_period_end:
        try:
            s = date.fromisoformat(fact.service_period_start) - timedelta(days=15)
            e = date.fromisoformat(fact.service_period_end) + timedelta(days=days)
            if s <= ed <= e:
                return True
        except ValueError:
            pass
    for value in (fact.doc_date, fact.service_period_start, fact.service_period_end):
        if not value:
            continue
        try:
            if abs((date.fromisoformat(value) - ed).days) <= days:
                return True
        except ValueError:
            continue
    return False


def _within_event(entry: GLEntry, fact: DocFacts, *, before: int, after: int) -> bool:
    """Entry date inside the document's stated period (event or service dates), with slack days."""
    ed = _entry_date(entry)
    if ed is None or not (fact.service_period_start and fact.service_period_end):
        return False
    try:
        start = date.fromisoformat(fact.service_period_start) - timedelta(days=before)
        end = date.fromisoformat(fact.service_period_end) + timedelta(days=after)
    except ValueError:
        return False
    return start <= ed <= end


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
        if fact is None or not quote.quote.strip():
            return False
        return any(q.page == quote.page and quote.quote in q.quote for q in _fact_quotes(fact))


def _primary_refs(fact: DocFacts, evidence: _Evidence) -> list[str]:
    """The references a document is *about*: its own bill numbers and the first matter / claim / case it names.

    A letter for one matter often mentions another ("separate from Matter 1004"); those mentions must not
    tie the document to the other matter's entries.
    """
    doc = evidence.docs.get(fact.doc_id)
    known = {r.lower(): r for r in fact.reference_numbers}
    out: list[str] = []
    if doc is not None:
        first_event: Optional[str] = None
        for kind, value in _labeled_refs(doc.full_text):
            if kind in _EVENT_REF_KINDS:
                if first_event is None:
                    first_event = value
            elif kind not in ("reference",) and value not in out:
                out.append(value)
        if first_event is not None and first_event not in out:
            out.append(first_event)
        out.extend(r for r in fact.reference_numbers if _CODE_RE.fullmatch(r) and r not in out
                   and not any(r.lower() == v.lower() for _, v in _labeled_refs(doc.full_text)))
        return [known.get(r.lower(), r) for r in out]
    heading = f"{fact.title}\n{_filename_title(fact.doc_id)}"
    out = [r for r in fact.reference_numbers if _token_in(r, heading)]
    if not out and fact.reference_numbers:
        out = [fact.reference_numbers[0]]
    return out


def _tie_entries(
    fact: DocFacts,
    entries: list[GLEntry],
    evidence: _Evidence,
    mode: str,
) -> list[str]:
    """Entries a document's statement applies to; [] means the statement is not entry-specific.

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

    doc_text = evidence.text(fact)
    # Person names (the owner, the attendee) appear on personal and business items alike.
    person_tokens = {t for m in _INITIAL_NAME_RE.finditer(doc_text) for t in _name_tokens(m.group())}
    doc_tokens = _distinct_tokens(doc_text) - person_tokens
    chosen = list(ref_hits)
    for e in entries:
        if e in chosen:
            continue
        near = _near_doc_dates(e, fact)
        amount = bool(doc_amounts) and _amount_matches(e, doc_amounts)
        cp = cp_ok(e) is True
        memo_tokens = _distinct_tokens(e.memo) - {t for m in _INITIAL_NAME_RE.finditer(e.memo)
                                                   for t in _name_tokens(m.group())}
        shared = len(memo_tokens & doc_tokens)
        if mode == "statement":
            if amount and (near or cp) or (near and cp and shared >= 1):
                chosen.append(e)
        elif mode == "business":
            during = _within_event(e, fact, before=3, after=3)
            around = _within_event(e, fact, before=45, after=45)
            if during or (around and (shared or cp or amount)) or (near and shared):
                chosen.append(e)
    return [e.entry_id for e in entries if e in chosen]


# ---------------------------------------------------------------------------
# Rule-based contradictions
# ---------------------------------------------------------------------------

_NONRECURRING_CONFLICT = "Management describes the cost as one-time / non-recurring."
_PERSONAL_CONFLICT = "Management describes the cost as a personal (non-business) owner expense."


def _term_statement(term: TermFact, label: str) -> str:
    if term.kind == "monthly_fee":
        return f"{label} provides for a recurring {term.text}, which is not a one-time cost."
    if term.kind == "retainer":
        return f"{label} sets a standing {term.text}, an ongoing cost rather than a one-time charge."
    if term.kind == "auto_renew":
        return f"{label} renews automatically, so the cost continues beyond the claim period."
    if term.kind == "ongoing_services":
        return f"{label} provides for services that continue until terminated."
    return f"{label} commits the company to a multi-period term ({term.text})."


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
        label = _doc_label(fact)
        per_doc = 0
        if intent.asserts_nonrecurring and not intent.is_pro_forma:
            for q in fact.key_statements:
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
                statement = f"{label} describes the cost as recurring (\"{phrase}\")."
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
                if add(fact, term.quote, _term_statement(term, label), _NONRECURRING_CONFLICT, entry_ids):
                    per_doc += 1
        if intent.asserts_personal:
            for q in fact.key_statements:
                if per_doc >= 3:
                    break
                if not _BUSINESS_PURPOSE_RE.search(q.quote) or _PERSONAL_RE.search(q.quote):
                    continue
                entry_ids = _tie_entries(fact, entries, evidence, "business")
                statement = (
                    f"{label} records a business purpose for the expense (for example a conference, supplier or "
                    f"customer visit attended for the company)."
                )
                if add(fact, q, statement, _PERSONAL_CONFLICT, entry_ids):
                    per_doc += 1
        if intent.is_normalization and intent.normalized_amount:
            salaries = [a for a in fact.amounts if a.label == "base_salary"]
            if salaries and not any(within(a.amount, intent.normalized_amount) for a in salaries):
                a = salaries[0]
                add(
                    fact,
                    a.quote,
                    f"{label} states a base salary of {_usd(a.amount)}, not the {_usd(intent.normalized_amount)} "
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
                        f"{label} describes the change as planned, not completed.",
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


def _quote_excerpt(text: str, limit: int = 160) -> str:
    text = _norm_space(text)
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > 40 else limit].rstrip(" ,;:") + " …"


def _classify_personal(
    entries: list[GLEntry], facts: list[DocFacts], evidence: _Evidence
) -> list[EntryClassification]:
    business_docs = [
        (f, q) for f in facts for q in f.key_statements
        if _BUSINESS_PURPOSE_RE.search(q.quote) and not _PERSONAL_RE.search(q.quote)
    ]
    out: list[EntryClassification] = []
    for e in entries:
        personal = _PERSONAL_RE.search(e.memo)
        business = _BUSINESS_MEMO_RE.search(e.memo)
        if personal:
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=True,
                reason=f"Memo identifies the cost as personal (\"{personal.group()}\").",
            ))
            continue
        if business:
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"Memo shows a business purpose (\"{business.group()}\"), so it is not a personal expense.",
            ))
            continue
        tied = [(f, q) for f, q in business_docs if e.entry_id in _tie_entries(f, [e], evidence, "business")]
        if tied:
            fact, q = tied[0]
            out.append(EntryClassification(
                entry_id=e.entry_id, qualifies=False,
                reason=f"{_doc_label(fact)} documents a business purpose: \"{_quote_excerpt(q.quote)}\"",
                doc_ids=sorted({f.doc_id for f, _ in tied}),
            ))
            continue
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
    title_kw = {k for k in _narrative_keywords(adj.title, "") if k not in _WEAK_KEYWORDS}
    all_kw = {k for k in intent.keywords if k not in _WEAK_KEYWORDS and len(k) >= 4}
    primary = (title_kw & all_kw) or title_kw
    secondary = all_kw - primary
    for name in intent.counterparties:
        primary |= {t for t in _name_tokens(name) if len(t) >= 4 and t not in _GENERIC_WORDS}

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
    primary_by_doc = {f.doc_id: {r.lower() for r in _primary_refs(f, evidence)} for f in facts}
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
                reason=f"Linked to {_doc_label(recurring_doc)}, a standing arrangement ({term.text}), not the "
                f"claimed event.",
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
    return [decided[e.entry_id] for e in entries]


# ---------------------------------------------------------------------------
# Rule-based questions
# ---------------------------------------------------------------------------


def _claim_summary(adj: AdjustmentClaim) -> str:
    parts = [f"{label} {_usd(v)}" for label, v in adj.amounts.items() if D(v) != 0]
    return _join_words(parts) if parts else "no amount"


def _docs_phrase(flag: Flag, docs: dict[str, DocFacts], default: str = "The supporting document") -> str:
    labels: list[str] = []
    for doc_id in flag.doc_ids[:2]:
        fact = docs.get(doc_id)
        labels.append(f"the {_doc_label(fact)}" if fact and fact.title else doc_id)
    if not labels:
        return default
    text = " and ".join(labels)
    return text[:1].upper() + text[1:]


def _long_date(iso: Optional[str]) -> str:
    """'2024-07-01' -> 'July 1, 2024' for text written to management."""
    try:
        d = date.fromisoformat(iso or "")
    except ValueError:
        return iso or ""
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _term_phrase(term: TermFact) -> str:
    if term.kind in ("monthly_fee", "retainer"):
        return f"a {term.text}"
    if term.kind == "auto_renew":
        return "automatic renewal"
    if term.kind == "ongoing_services":
        return "services that continue until terminated"
    if term.kind == "term_end":
        m = re.search(r"\d{4}-\d{2}-\d{2}", term.text)
        return f"a term running to {_long_date(m.group())}" if m else term.text
    return term.text


def _join_words(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


_COUNT_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")


def _entries_phrase(n: int) -> str:
    count = _COUNT_WORDS[n] if 0 <= n < len(_COUNT_WORDS) else str(n)
    return f"{count} ledger entr{'y' if n == 1 else 'ies'}"


def _question_for(adj: AdjustmentClaim, flag: Flag, docs: dict[str, DocFacts]) -> str:
    ref = f"adjustment {adj.adj_id} ({adj.title})"
    ref_cap = ref[:1].upper() + ref[1:]
    period = flag.period_label
    in_period = f" in {period}" if period else ""
    claimed = adj.amounts.get(period or "", "")
    claimed_txt = f"the {_usd(claimed)} claimed" if claimed and D(claimed) != 0 else "the amount claimed"
    impact = _usd(flag.amount_impact) if flag.amount_impact and D(flag.amount_impact) != 0 else ""
    docs_txt = _docs_phrase(flag, docs)
    n_entries = len(flag.entry_ids)
    code = flag.code

    if code == FlagCode.NO_GL_SUPPORT:
        return (f"We could not find the costs behind {ref} in the general ledger (management claims "
                f"{_claim_summary(adj)}). "
                f"Please send the ledger detail (account, date, vendor and amount) for the entries that make up "
                f"this adjustment.")
    if code == FlagCode.PARTIAL_GL_SUPPORT:
        gap = f"{impact} " if impact else ""
        return (f"For {ref}, the ledger activity we could tie to this item{in_period} is {gap}less than "
                f"{claimed_txt}. Please send the entries that make up the full amount, or revise the adjustment.")
    if code == FlagCode.EXCESS_GL_ACTIVITY:
        return (f"The ledger shows more activity related to {ref}{in_period} than {claimed_txt}. Please confirm "
                f"which invoices management included and why the remaining entries were left out.")
    if code == FlagCode.NO_DOCUMENT_SUPPORT:
        portion = f"{impact} of" if impact else "part of"
        return (f"We have not received invoices or agreements supporting {portion} {ref}{in_period}. "
                f"Please provide the supporting documents for these costs.")
    if code == FlagCode.DOC_GL_AMOUNT_MISMATCH:
        which = f"the {_entries_phrase(n_entries)}" if n_entries > 1 else "the ledger entry"
        return (f"{docs_txt} shows a different amount from {which} it supports in {ref}. Please explain the "
                f"difference (for example a partial payment, a credit memo or a second invoice).")
    if code == FlagCode.PERIOD_MISMATCH:
        amount = f" {_usd(claimed)}" if claimed and D(claimed) != 0 else " an amount"
        return (f"{ref_cap} claims{amount}{in_period}, but the related ledger activity was recorded in a "
                f"different period. Please confirm when these costs were incurred and update the schedule if the "
                f"timing is wrong.")
    if code == FlagCode.OUT_OF_PERIOD:
        for doc_id in flag.doc_ids:
            fact = docs.get(doc_id)
            if fact and fact.service_period_start and fact.service_period_end:
                return (f"{_docs_phrase(flag.model_copy(update={'doc_ids': [doc_id]}), docs)} covers services "
                        f"from {_long_date(fact.service_period_start)} to {_long_date(fact.service_period_end)}, "
                        f"but the cost was recorded{in_period}. Please confirm the service period and explain how "
                        f"management reflected the portion that relates to an earlier period.")
        return (f"The costs in {ref} appear to relate to a different period from the one in which they were "
                f"recorded{in_period}. Please confirm the service period of the underlying invoices.")
    if code == FlagCode.RECURRING_PATTERN:
        amount = f"of {impact} " if impact else ""
        return (f"We see comparable costs {amount}in periods that {ref} does not cover. Please explain why "
                f"management considers this cost non-recurring and whether you expect it to continue after closing.")
    if code == FlagCode.CONTINUING_OBLIGATION:
        phrases: list[str] = []
        for doc_id in flag.doc_ids:
            fact = docs.get(doc_id)
            for term in fact.terms if fact else []:
                phrase = _term_phrase(term)
                if term.kind in RECURRING_TERM_KINDS and phrase not in phrases:
                    phrases.append(phrase)
        what = _join_words(phrases[:3]) if phrases else "an ongoing commitment"
        return (f"{docs_txt} provides for {what}. Please confirm whether this arrangement is still in place, what "
                f"it will cost after closing, and whether it can be terminated.")
    if code == FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT:
        related = _join_words([f"adjustment {r}" for r in flag.related_adj_ids]) or "another adjustment"
        subject = _entries_phrase(n_entries).capitalize() if n_entries else "Some of the entries"
        return (f"{subject} in {ref} {'is' if n_entries == 1 else 'are'} also included in {related}. Please "
                f"confirm which adjustment should carry them so they are not counted twice.")
    if code == FlagCode.ALREADY_EXCLUDED_FROM_EBITDA:
        return (f"The costs in {ref} are recorded in interest, tax, depreciation or amortization accounts, which "
                f"EBITDA already excludes. Please confirm whether any portion was recorded in operating expenses; "
                f"otherwise the adjustment counts these costs twice.")
    if code == FlagCode.OFFSETTING_RECOVERY:
        amount = f" of {impact}" if impact else ""
        return (f"The ledger shows a related recovery{amount}{in_period} (for example insurance proceeds) that "
                f"{ref} does not net off. Please confirm the amount and timing of all recoveries and whether any "
                f"further amounts are expected.")
    if code == FlagCode.CONTRADICTORY_EVIDENCE:
        if flag.quotes:
            excerpt = _quote_excerpt(flag.quotes[0].quote).rstrip(".")
            source = _docs_phrase(flag.model_copy(update={"doc_ids": [flag.quotes[0].doc_id]}), docs)
            return (f"{source} states \"{excerpt}\", which appears inconsistent with how management describes "
                    f"{ref}. Please explain how management reconciled this with the basis for the adjustment.")
        return (f"The documents for {ref} appear inconsistent with management's description of the item. "
                f"Please explain the basis for the adjustment.")
    if code == FlagCode.UNSIGNED_OR_DRAFT_SUPPORT:
        fact = next((docs[d] for d in flag.doc_ids if d in docs), None)
        if fact is not None and fact.is_draft and fact.is_signed is False:
            status = "is marked as a draft and is not signed"
        elif fact is not None and fact.is_draft:
            status = "is marked as a draft"
        elif fact is not None and fact.is_signed is False:
            status = "is not signed"
        else:
            status = "is unsigned or in draft form"
        subject = f"The copy of {docs_txt[:1].lower() + docs_txt[1:]}" if flag.doc_ids else f"The agreement supporting {ref}"
        return (f"{subject} we received {status}. Please provide the executed version, or confirm the agreed "
                f"terms and when they take effect.")
    if code == FlagCode.NORMALIZATION_BENCHMARK_MISSING:
        return (f"Please provide the basis for the normalized level used in {ref} (for example a compensation "
                f"survey or a signed agreement), and explain how payroll taxes and benefits were treated.")
    if code == FlagCode.PRO_FORMA_NOT_REALIZED:
        return (f"The ledger shows these costs continuing through the end of the data provided. Please provide "
                f"evidence that the change behind {ref} has happened or is committed (for example separation "
                f"letters or payroll changes), the one-time cost to achieve it, and whether any roles or costs will "
                f"be replaced.")
    if code == FlagCode.SIGN_ERROR:
        total = sum((D(v) for v in adj.amounts.values()), Decimal("0"))
        direction = "an add-back that increases EBITDA" if total >= 0 else "a deduction that reduces EBITDA"
        entries = f"the {_entries_phrase(n_entries)} behind it" if n_entries else "the underlying ledger entries"
        return (f"{ref_cap} is presented as {direction}, but {entries} point the other way. Please confirm the "
                f"direction of this adjustment.")
    if code == FlagCode.DUPLICATE_GL_ENTRY:
        subject = f"{_entries_phrase(n_entries).capitalize()} included in {ref}" if n_entries else f"Entries in {ref}"
        return (f"{subject} appear to have been posted twice. Please confirm whether this is a duplicate and, if "
                f"so, when and how it was reversed.")
    return f"Please explain the following point on {ref}: {flag.message}"


def _fact_questions(adj: AdjustmentClaim, facts: list[DocFacts]) -> list[str]:
    out: list[str] = []
    for fact in facts:
        if fact.doc_type == "settlement_agreement":
            dated = f" dated {_long_date(fact.doc_date)}" if fact.doc_date else ""
            out.append(
                f"The {_doc_label(fact)}{dated} resolves the matter behind adjustment {adj.adj_id} ({adj.title}). "
                f"Please confirm who funded the settlement (and that any insurer payment was received in full), and "
                f"whether any fees or obligations continue after the settlement."
            )
    return out


def _draft_questions_rules(adj: AdjustmentClaim, flags: list[Flag], facts: list[DocFacts]) -> list[str]:
    docs = {f.doc_id: f for f in facts}
    out: list[str] = []
    for flag in flags:
        q = _question_for(adj, flag, docs)
        if q and q not in out:
            out.append(q)
    for q in _fact_questions(adj, facts):
        if q not in out:
            out.append(q)
    return out


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
        return _draft_questions_rules(adj, flags, facts)


# ---------------------------------------------------------------------------
# OpenAI-compatible LLM implementation
# ---------------------------------------------------------------------------


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
                           "reason": {"type": "string"}, "doc_ids": {"type": "array", "items": {"type": "string"}}}),
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
        # a whole amount may be written without cents ("300,000"), but not as the start of "300,000.50"
        if re.search(rf"(?<![\d,.]){re.escape(written)}(?![\d,]|\.\d*[1-9])", quote):
            return True
    return False


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
        docs_by_id = {doc.doc_id: doc}
        full_text = doc.full_text
        full_lower = _norm_space(full_text).lower()
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

        amounts: list[AmountFact] = []
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
            label = str(item.get("label") or "line").strip().lower().replace(" ", "_") or "line"
            amounts.append(AmountFact(label=label, amount=amount, quote=q))
        terms: list[TermFact] = []
        for item in data.get("terms") or []:
            q = quote(item)
            if q is None:
                continue
            kind = str(item.get("kind") or "other")
            terms.append(TermFact(kind=kind if kind in TERM_KINDS else "other",
                                  text=_norm_space(str(item.get("text") or "")) or kind, quote=q))
        statements = [q for item in data.get("key_statements") or [] if (q := quote(item)) is not None]
        refs = [
            r for r in (_stated(x) for x in data.get("reference_numbers") or [])
            if r and r.lower() in full_text.lower()
        ]
        counterparty = _stated(data.get("counterparty"))
        if counterparty and _norm_space(counterparty).lower() not in full_lower:
            counterparty = None
        doc_type = str(data.get("doc_type") or "other")
        signed = data.get("is_signed")
        return DocFacts(
            doc_id=doc.doc_id,
            doc_type=doc_type if doc_type in DOC_TYPES else "other",
            title=_stated(data.get("title")) or _filename_title(doc.doc_id),
            counterparty=counterparty,
            doc_date=_iso_or_none(data.get("doc_date")),
            reference_numbers=list(dict.fromkeys(refs)),
            amounts=amounts,
            service_period_start=_iso_or_none(data.get("service_period_start")),
            service_period_end=_iso_or_none(data.get("service_period_end")),
            is_draft=bool(data.get("is_draft")),
            is_signed=signed if isinstance(signed, bool) else None,
            terms=terms,
            key_statements=statements,
            extractor=self.name,
            dropped_quotes=dropped,
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
            normalized = _stated(data.get("normalized_amount"))
            if normalized is not None:
                try:
                    normalized = fmt(abs(D(normalized)))
                except ValueError:
                    normalized = None
            if normalized is not None and not _amount_in_quote(normalized, narrative):
                normalized = None  # the model may not compute a level the narrative does not state
            months = [m for m in data.get("event_months") or [] if isinstance(m, str) and re.fullmatch(r"\d{4}-\d{2}", m)]
            event_type = str(data.get("event_type") or "other")
            return AdjustmentIntent(
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
        known_entries = {e.entry_id for e in entries}
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
            out.append(
                Contradiction(
                    doc_id=q.doc_id,
                    statement=statement,
                    quote=q,
                    conflicts_with=_norm_space(str(item.get("conflicts_with") or "")) or "management's explanation",
                    entry_ids=[x for x in item.get("entry_ids") or [] if x in known_entries],
                )
            )
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
        by_id: dict[str, EntryClassification] = {}
        for item in data.get("classifications") or []:
            entry_id = str(item.get("entry_id") or "")
            reason = _norm_space(str(item.get("reason") or ""))
            if entry_id not in {e.entry_id for e in entries} or entry_id in by_id or not reason:
                continue
            by_id[entry_id] = EntryClassification(
                entry_id=entry_id,
                qualifies=bool(item.get("qualifies")),
                reason=reason,
                doc_ids=[d for d in item.get("doc_ids") or [] if d in known_docs],
            )
        if any(e.entry_id not in by_id for e in entries):
            # rules need every entry to see the event group, then fill only the gaps
            for c in self.rules.classify_entries(adj, intent, entries, facts):
                by_id.setdefault(c.entry_id, c)
        return [by_id[e.entry_id] for e in entries]

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
            questions = list(dict.fromkeys(q for q in questions if q))
            if flags and not questions:
                raise ValueError("no questions returned for open flags")
            return questions
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
