"""Account classification for the generator (mirrors SPEC §3.4 mapping rules).

The generator needs each account's EBITDA class to compute the answer key
(GL-derived EBITDA) and management's reported EBITDA, and its normal balance
to write natural-sign amounts. It deliberately does not import qoe.gl_formats:
the answer key must not be derived from the code it is used to grade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from qoe.schemas import EbitdaClass

from .spec import AccountSpec

_INCOME_TYPES = {"income", "revenue", "sales", "other income", "otherincome"}
_TYPE_RULES: list[tuple[set[str], EbitdaClass]] = [
    ({"income", "revenue", "sales"}, EbitdaClass.REVENUE),
    ({"other income", "otherincome"}, EbitdaClass.OTHER_INCOME),
    ({"cost of goods sold", "cogs", "directcosts", "direct costs", "cost of sales"}, EbitdaClass.COGS),
    ({"expense", "expenses", "overheads", "overhead"}, EbitdaClass.OPEX),
    ({"other expense", "other expenses"}, EbitdaClass.OTHER_EXPENSE),
    ({"depreciatn", "depreciation"}, EbitdaClass.DEPRECIATION),
]
_INTEREST = re.compile(r"interest (expense|paid)|loan interest|interest income", re.I)
_DEPRECIATION = re.compile(r"depreciation", re.I)
_AMORTIZATION = re.compile(r"amortization", re.I)
_DEBT_WORDS = re.compile(r"loan|debt|financing", re.I)
_INCOME_TAX = re.compile(r"income tax", re.I)


@dataclass(frozen=True)
class AccountInfo:
    number: str
    name: str
    source_type: str
    detail_type: str
    ebitda_class: EbitdaClass
    rule_class: EbitdaClass  # what SPEC §3.4 rules alone would give (no override)
    credit_natural: bool

    @property
    def is_pl(self) -> bool:
        return self.ebitda_class != EbitdaClass.BALANCE_SHEET

    @property
    def label(self) -> str:
        return f"{self.number} {self.name}"


def type_class(source_type: str) -> EbitdaClass:
    t = source_type.strip().lower()
    for names, cls in _TYPE_RULES:
        if t in names:
            return cls
    return EbitdaClass.BALANCE_SHEET


def rule_class(name: str, source_type: str) -> EbitdaClass:
    by_type = type_class(source_type)
    if by_type == EbitdaClass.BALANCE_SHEET:
        return by_type
    if _INTEREST.search(name):
        return EbitdaClass.INTEREST
    if _DEPRECIATION.search(name):
        return EbitdaClass.DEPRECIATION
    if _AMORTIZATION.search(name):
        return EbitdaClass.INTEREST if _DEBT_WORDS.search(name) else EbitdaClass.AMORTIZATION
    if _INCOME_TAX.search(name):
        return EbitdaClass.TAXES
    return by_type


def build_accounts(specs: list[AccountSpec]) -> dict[str, AccountInfo]:
    out: dict[str, AccountInfo] = {}
    for a in specs:
        by_rule = rule_class(a.name, a.type)
        cls = EbitdaClass(a.ebitda_class) if a.ebitda_class else by_rule
        if a.natural is not None:
            credit = a.natural == "credit"
        else:
            credit = a.type.strip().lower() in _INCOME_TYPES or cls in (EbitdaClass.REVENUE, EbitdaClass.OTHER_INCOME)
        out[a.number] = AccountInfo(a.number, a.name, a.type, a.detail_type, cls, by_rule, credit)
    return out
