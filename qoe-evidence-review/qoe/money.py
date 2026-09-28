"""Decimal helpers. Money never touches float."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Iterable, Mapping, Optional

ZERO = Decimal("0")
CENT = Decimal("0.01")

_STRIP = re.compile(r"[\s$, ]")


def D(value: object) -> Decimal:
    """Parse a money-ish value into Decimal.

    Accepts Decimal, int, str ("1,234.50", "$(1,234.50)", "-12", "(12)", "12-"),
    and float (converted via repr to avoid binary noise). Blank / None -> 0.
    """
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not money")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    s = _STRIP.sub("", str(value))
    if s in ("", "-", "--"):
        return ZERO
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative, s = True, s[1:-1]
    if s.endswith("-"):
        negative, s = True, s[:-1]
    if s.startswith("-"):
        negative, s = (not negative), s[1:]
    try:
        d = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"not a money value: {value!r}") from exc
    return -d if negative else d


def q2(d: Decimal) -> Decimal:
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(value: object) -> str:
    """Normalize to a 2-dp decimal string ("-0.00" collapses to "0.00")."""
    d = q2(D(value))
    if d == 0:
        d = abs(d)
    return format(d, "f")


def dsum(values: Iterable[object]) -> Decimal:
    total = ZERO
    for v in values:
        total += D(v)
    return total


def period_map(values: Mapping[str, object], labels: Optional[Iterable[str]] = None) -> dict[str, str]:
    """Normalize a {period_label: amount} mapping; missing labels become "0.00"."""
    keys = list(labels) if labels is not None else list(values.keys())
    return {k: fmt(values.get(k, ZERO)) for k in keys}


def within(a: object, b: object, tolerance: object = "1.00") -> bool:
    return abs(D(a) - D(b)) <= D(tolerance)
