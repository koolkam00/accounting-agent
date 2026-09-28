"""Month and analysis-period helpers. Months are "YYYY-MM" strings."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from qoe.schemas import PeriodDef


def month_of(iso_date: str) -> str:
    return iso_date[:7]


def _ym(month: str) -> tuple[int, int]:
    y, m = month.split("-")
    return int(y), int(m)


def add_months(month: str, n: int) -> str:
    y, m = _ym(month)
    idx = y * 12 + (m - 1) + n
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_range(start: str, end: str) -> list[str]:
    """Inclusive list of months from start to end."""
    out: list[str] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur = add_months(cur, 1)
    return out


def months_in(period: PeriodDef) -> list[str]:
    return month_range(period.start, period.end)


def in_period(month: str, period: PeriodDef) -> bool:
    return period.start <= month <= period.end


def labels_for_month(month: str, periods: Iterable[PeriodDef]) -> list[str]:
    """Every analysis period containing the month (TTM overlaps a fiscal year)."""
    return [p.label for p in periods if in_period(month, p)]


def month_end(month: str) -> date:
    y, m = _ym(add_months(month, 1))
    return date.fromordinal(date(y, m, 1).toordinal() - 1)
