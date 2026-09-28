"""Reconcile the GL to management's monthly P&L and reported EBITDA (SPEC §6).

Amounts are rolled up per month first and then aggregated to each analysis
period label, because periods overlap (a TTM period shares months with a
fiscal year). GL amounts are debit-positive, so net income is the negated sum
of every P&L entry and EBITDA adds back the interest, tax, depreciation and
amortization classes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from itertools import pairwise
from decimal import Decimal
from typing import Iterable

from qoe.gl_formats import is_fallback
from qoe.money import D, ZERO, fmt, q2
from qoe.periods import add_months, month_range, months_in
from qoe.schemas import (
    EBITDA_EXCLUDED_CLASSES,
    DataQualityCode,
    DataQualityIssue,
    DealPackage,
    EbitdaClass,
    EbitdaComponents,
    GLEntry,
    ManagementSchedule,
    ReconciliationItem,
    ReconciliationResult,
    Severity,
)

# A month is "partially missing" when it has entries in fewer than half of the
# accounts active in both neighbouring months; below this many accounts the
# test is too noisy to mean anything.
MISSING_PERIOD_MIN_BASE = 3
# Same account/amount/counterparty/memo at most this many days apart is a possible duplicate.
DUPLICATE_WINDOW_DAYS = 7

_COMPONENTS = ("pl_total", "interest", "taxes", "depreciation", "amortization")
_CLASS_COMPONENT = {
    EbitdaClass.INTEREST: "interest",
    EbitdaClass.TAXES: "taxes",
    EbitdaClass.DEPRECIATION: "depreciation",
    EbitdaClass.AMORTIZATION: "amortization",
}


def _money(value: Decimal) -> str:
    return f"{q2(value):,.2f}"


def _account_sort_key(number: str) -> tuple[int, int, str]:
    return (0, int(number), number) if number.isdigit() else (1, 0, number)


def _class_of(pkg: DealPackage, number: str) -> EbitdaClass:
    acct = pkg.accounts.get(number)
    # An account missing from pkg.accounts is treated as operating expense and
    # reported as UNMAPPED_ACCOUNT rather than silently dropped from EBITDA.
    return acct.ebitda_class if acct is not None else EbitdaClass.OPEX


def _pl_entries(pkg: DealPackage) -> list[GLEntry]:
    return [e for e in pkg.gl if _class_of(pkg, e.account) is not EbitdaClass.BALANCE_SHEET]


def _norm(text: str) -> str:
    return " ".join(text.split()).casefold()


# ---------------------------------------------------------------------------
# EBITDA from the GL
# ---------------------------------------------------------------------------


def _monthly_components(pkg: DealPackage) -> dict[str, dict[str, Decimal]]:
    out: dict[str, dict[str, Decimal]] = {}
    for e in _pl_entries(pkg):
        month = out.setdefault(e.period, {k: ZERO for k in _COMPONENTS})
        amount = D(e.amount)
        month["pl_total"] += amount
        component = _CLASS_COMPONENT.get(_class_of(pkg, e.account))
        if component is not None:
            month[component] += amount
    return out


def gl_ebitda(pkg: DealPackage) -> dict[str, EbitdaComponents]:
    """EBITDA recomputed from the GL for every analysis period label."""
    monthly = _monthly_components(pkg)
    result: dict[str, EbitdaComponents] = {}
    for period in pkg.meta.periods:
        totals = {k: ZERO for k in _COMPONENTS}
        for month in months_in(period):
            for k, v in monthly.get(month, {}).items():
                totals[k] += v
        net_income = -totals["pl_total"]
        ebitda = net_income + totals["interest"] + totals["taxes"] + totals["depreciation"] + totals["amortization"]
        result[period.label] = EbitdaComponents(
            net_income=fmt(net_income),
            interest=fmt(totals["interest"]),
            taxes=fmt(totals["taxes"]),
            depreciation=fmt(totals["depreciation"]),
            amortization=fmt(totals["amortization"]),
            ebitda=fmt(ebitda),
        )
    return result


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------


def find_duplicate_entries(gl: list[GLEntry]) -> list[list[str]]:
    """Groups of entry ids that look like the same transaction posted twice.

    Two entries match on account, amount and counterparty plus either the same
    non-empty doc number, or the same memo within 7 days. Groups are
    ordered by GL row, as are the ids within each group.
    """
    parent = {e.entry_id: e.entry_id for e in gl}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    by_doc: dict[tuple, list[GLEntry]] = defaultdict(list)
    by_memo: dict[tuple, list[GLEntry]] = defaultdict(list)
    for e in gl:
        amount = D(e.amount)
        if amount == 0:
            continue
        counterparty, memo, doc = _norm(e.counterparty), _norm(e.memo), _norm(e.doc_number)
        if doc:
            by_doc[(e.account, amount, counterparty, doc)].append(e)
        # With neither a name nor a memo there is nothing to say two postings are one event.
        if counterparty or memo:
            by_memo[(e.account, amount, counterparty, memo)].append(e)
    for group in by_doc.values():
        for other in group[1:]:
            union(group[0].entry_id, other.entry_id)
    for group in by_memo.values():
        ordered = sorted(group, key=lambda x: (x.date, x.source_row, x.entry_id))
        for a, b in pairwise(ordered):
            gap = (date.fromisoformat(b.date) - date.fromisoformat(a.date)).days
            if gap <= DUPLICATE_WINDOW_DAYS:
                union(a.entry_id, b.entry_id)

    order = {e.entry_id: (e.source_row, e.entry_id) for e in gl}
    groups: dict[str, list[str]] = defaultdict(list)
    for e in gl:
        groups[find(e.entry_id)].append(e.entry_id)
    out = [sorted(ids, key=order.__getitem__) for ids in groups.values() if len(ids) > 1]
    return sorted(out, key=lambda ids: order[ids[0]])


def _duplicate_issues(entries: list[GLEntry]) -> list[DataQualityIssue]:
    by_id = {e.entry_id: e for e in entries}
    issues = []
    for group in find_duplicate_entries(entries):
        es = [by_id[i] for i in group]
        first = es[0]
        amount = D(first.amount)
        same_doc = bool(first.doc_number) and all(_norm(e.doc_number) == _norm(first.doc_number) for e in es)
        basis = f"same doc # {first.doc_number}" if same_doc else f"same memo within {DUPLICATE_WINDOW_DAYS} days"
        rows = ", ".join(str(e.source_row) for e in es)
        dates = ", ".join(e.date for e in es)
        excess = amount * (len(es) - 1)
        issues.append(
            DataQualityIssue(
                code=DataQualityCode.DUPLICATE_GL_ENTRY,
                severity=Severity.WARNING,
                message=(
                    f"Possible duplicate posting in {first.account} {first.account_name}: {len(es)} entries of "
                    f"{_money(amount)} to {first.counterparty or '(no name)'} ({basis}; GL rows {rows}; dated {dates}). "
                    f"If duplicated, the GL double counts {_money(excess)}."
                ),
                month=first.period,
                account=first.account,
                amount=fmt(excess),
                entry_ids=group,
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Completeness checks
# ---------------------------------------------------------------------------


def _unmapped_issues(pkg: DealPackage, gl_used: set[str], pl_used: set[str]) -> list[DataQualityIssue]:
    used = gl_used | pl_used
    issues = []
    for acct in sorted(pkg.accounts.values(), key=lambda a: _account_sort_key(a.number)):
        if not is_fallback(acct):
            continue
        active = acct.number in used
        issues.append(
            DataQualityIssue(
                code=DataQualityCode.UNMAPPED_ACCOUNT,
                severity=Severity.WARNING if active else Severity.INFO,
                message=(
                    f"Account {acct.number} {acct.name} (type {acct.source_type or 'blank'!r}) matched no mapping rule: "
                    f"{acct.mapping_basis}. Confirm its EBITDA class"
                    + (" - it has activity in the period." if active else "; it has no activity.")
                ),
                account=acct.number,
            )
        )
    # P&L-only accounts have no GL activity to classify; coverage checks report them.
    for number in sorted(gl_used - set(pkg.accounts), key=_account_sort_key):
        issues.append(
            DataQualityIssue(
                code=DataQualityCode.UNMAPPED_ACCOUNT,
                severity=Severity.WARNING,
                message=f"Account {number} has GL activity but is not in the chart of accounts; treated as OPEX.",
                account=number,
            )
        )
    return issues


def _missing_period_issues(
    pkg: DealPackage, data_months: list[str], pl_entries: list[GLEntry]
) -> tuple[list[DataQualityIssue], set[str]]:
    """MISSING_PERIOD issues, plus the months whose GL activity is absent or incomplete."""
    in_range = set(data_months)
    gl_gaps: set[str] = set()
    entries_by_month = Counter(e.period for e in pkg.gl)
    active: dict[str, set[str]] = defaultdict(set)
    for e in pl_entries:
        active[e.period].add(e.account)
    pl_months = set(pkg.pl.months)
    issues = []
    for month in data_months:
        if entries_by_month[month] == 0:
            gl_gaps.add(month)
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.MISSING_PERIOD,
                    severity=Severity.CRITICAL,
                    message=f"The GL has no entries at all for {month}, which is inside the data range {data_months[0]}..{data_months[-1]}.",
                    month=month,
                )
            )
            continue
        neighbours = [n for n in (add_months(month, -1), add_months(month, 1)) if n in in_range and active.get(n)]
        if neighbours:
            base = set.intersection(*(active[n] for n in neighbours))
            present = len(active.get(month, set()) & base)
            if len(base) >= MISSING_PERIOD_MIN_BASE and present * 2 < len(base):
                gl_gaps.add(month)
                absent = sorted(base - active.get(month, set()), key=_account_sort_key)
                issues.append(
                    DataQualityIssue(
                        code=DataQualityCode.MISSING_PERIOD,
                        severity=Severity.WARNING,
                        message=(
                            f"{month} looks incomplete: only {present} of the {len(base)} accounts active in the "
                            f"neighbouring month(s) have GL entries (missing: {', '.join(absent[:12])}"
                            + (", ..." if len(absent) > 12 else "") + ")."
                        ),
                        month=month,
                    )
                )
        if month not in pl_months:
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.MISSING_PERIOD,
                    severity=Severity.WARNING,
                    message=f"Management's monthly P&L has no column for {month}; the GL cannot be reconciled for that month.",
                    month=month,
                )
            )
    for period in pkg.meta.periods:
        outside = [m for m in months_in(period) if m not in in_range]
        if outside:
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.MISSING_PERIOD,
                    severity=Severity.WARNING,
                    message=(
                        f"{period.label} includes {len(outside)} month(s) outside the GL data range "
                        f"({outside[0]}..{outside[-1]}); GL-derived amounts for it are incomplete."
                    ),
                    period_label=period.label,
                )
            )
    return issues, gl_gaps


# ---------------------------------------------------------------------------
# Management schedule
# ---------------------------------------------------------------------------


def _mgmt_reported(schedule: ManagementSchedule, labels: Iterable[str]) -> dict[str, str]:
    """Management's reported EBITDA by label; derived from its components if the row is absent."""
    out = {}
    for label in labels:
        if label in schedule.reported_ebitda:
            out[label] = fmt(schedule.reported_ebitda[label])
        elif label in schedule.net_income:
            parts = (schedule.net_income, schedule.interest, schedule.taxes, schedule.depreciation_amortization)
            out[label] = fmt(sum((D(p.get(label, 0)) for p in parts), ZERO))
    return out


def _arithmetic_issues(schedule: ManagementSchedule, labels: list[str], tol: Decimal) -> list[DataQualityIssue]:
    issues = []

    def check(label: str, what: str, stated: Decimal, computed: Decimal, how: str) -> None:
        diff = stated - computed
        if abs(diff) > tol:
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.MGMT_SCHEDULE_ARITHMETIC,
                    severity=Severity.WARNING,
                    message=(
                        f"{label}: management's {what} of {_money(stated)} does not foot to {how} "
                        f"= {_money(computed)} (difference {_money(diff)})."
                    ),
                    period_label=label,
                    amount=fmt(diff),
                )
            )

    for label in labels:
        reported = schedule.reported_ebitda.get(label)
        if reported is not None and label in schedule.net_income:
            parts = (schedule.net_income, schedule.interest, schedule.taxes, schedule.depreciation_amortization)
            computed = sum((D(p.get(label, 0)) for p in parts), ZERO)
            check(label, "reported EBITDA", D(reported), computed, "net income + interest + taxes + D&A")
        adj_sum = sum((D(a.amounts.get(label, 0)) for a in schedule.adjustments), ZERO)
        total = schedule.total_adjustments.get(label)
        if total is not None:
            check(label, "total adjustments", D(total), adj_sum, f"the sum of its {len(schedule.adjustments)} adjustments")
        adjusted = schedule.adjusted_ebitda.get(label)
        if adjusted is not None and reported is not None:
            base_total = D(total) if total is not None else adj_sum
            check(label, "adjusted EBITDA", D(adjusted), D(reported) + base_total, "reported EBITDA + total adjustments")
    return issues


# ---------------------------------------------------------------------------
# reconcile()
# ---------------------------------------------------------------------------


def reconcile(pkg: DealPackage) -> ReconciliationResult:
    """GL vs P&L by account-month, completeness checks, and GL-derived EBITDA."""
    meta = pkg.meta
    tol = D(meta.tolerance)
    labels = [p.label for p in meta.periods]
    data_months = month_range(meta.data_start, meta.data_end)
    in_range = set(data_months)
    pl_entries = _pl_entries(pkg)

    names: dict[str, str] = {}
    gl_by: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    gl_accounts: set[str] = set()
    for e in pl_entries:
        names.setdefault(e.account, e.account_name)
        if e.period in in_range:
            gl_by[(e.period, e.account)] += D(e.amount)
            gl_accounts.add(e.account)
    pl_by: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    pl_accounts: set[str] = set()
    for line in pkg.pl.lines:
        pl_accounts.add(line.account)
        names.setdefault(line.account, line.account_name)
        for month, amount in line.amounts.items():
            pl_by[(month, line.account)] += D(amount)
    for number, acct in pkg.accounts.items():
        names[number] = acct.name

    pl_months = set(pkg.pl.months)
    compared_months = [m for m in data_months if m in pl_months]
    accounts = sorted(pl_accounts | gl_accounts, key=_account_sort_key)

    issues: list[DataQualityIssue] = []
    issues += _unmapped_issues(pkg, {e.account for e in pl_entries}, pl_accounts)
    missing, gl_gaps = _missing_period_issues(pkg, data_months, pl_entries)
    issues += missing
    issues += _duplicate_issues(pl_entries)

    for number in accounts:
        pl_total = sum((pl_by[(m, number)] for m in compared_months), ZERO)
        gl_total = sum((gl_by[(m, number)] for m in data_months), ZERO)
        if number in gl_accounts and number not in pl_accounts:
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.GL_ACCOUNT_NOT_IN_PL,
                    severity=Severity.WARNING,
                    message=f"GL account {number} {names.get(number, '')} has activity of {_money(gl_total)} in the data range but is not on management's monthly P&L.",
                    account=number,
                    amount=fmt(gl_total),
                )
            )
        elif number in pl_accounts and number not in gl_accounts and pl_total != 0:
            issues.append(
                DataQualityIssue(
                    code=DataQualityCode.PL_ACCOUNT_NOT_IN_GL,
                    severity=Severity.WARNING,
                    message=f"P&L account {number} {names.get(number, '')} reports {_money(pl_total)} but has no GL entries in the data range.",
                    account=number,
                    amount=fmt(pl_total),
                )
            )

    items: list[ReconciliationItem] = []
    both_sides = pl_accounts & gl_accounts
    for month in compared_months:
        for number in accounts:
            gl_amount, pl_amount = gl_by[(month, number)], pl_by[(month, number)]
            variance = pl_amount - gl_amount
            within = abs(variance) <= tol
            items.append(
                ReconciliationItem(
                    month=month,
                    account=number,
                    account_name=names.get(number, ""),
                    gl_amount=fmt(gl_amount),
                    pl_amount=fmt(pl_amount),
                    variance=fmt(variance),
                    within_tolerance=within,
                )
            )
            # One-sided accounts and missing GL months are reported once above, not per cell.
            if not within and number in both_sides and month not in gl_gaps:
                if _class_of(pkg, number) in EBITDA_EXCLUDED_CLASSES:
                    effect = "below EBITDA, so no EBITDA effect"
                else:
                    effect = f"P&L EBITDA is {_money(abs(variance))} {'lower' if variance > 0 else 'higher'} than the GL"
                issues.append(
                    DataQualityIssue(
                        code=DataQualityCode.RECON_VARIANCE,
                        severity=Severity.WARNING,
                        message=(
                            f"{month} {number} {names.get(number, '')}: P&L {_money(pl_amount)} vs GL "
                            f"{_money(gl_amount)} (debit-positive); variance {_money(variance)} (P&L minus GL): {effect}."
                        ),
                        month=month,
                        account=number,
                        amount=fmt(variance),
                    )
                )

    compared = set(compared_months)
    for issue in missing:
        if issue.month in gl_gaps and issue.month in compared:
            effect = _pl_ebitda_effect(pkg, items, {issue.month})
            if abs(effect) > tol:
                issue.amount = fmt(effect)
                issue.message += (
                    f" Management's P&L for {issue.month} shows EBITDA {_money(abs(effect))} "
                    f"{'higher' if effect > 0 else 'lower'} than the GL."
                )

    ebitda = gl_ebitda(pkg)
    mgmt = _mgmt_reported(pkg.schedule, labels)
    for period in meta.periods:
        label = period.label
        if label not in mgmt:
            continue
        diff = D(mgmt[label]) - D(ebitda[label].ebitda)
        if abs(diff) <= tol:
            continue
        explained = _pl_ebitda_effect(pkg, items, set(months_in(period)))
        direction = "lower" if diff < 0 else "higher"
        tail = (
            f" GL-to-P&L variances in the period move P&L EBITDA by {_money(explained)}"
            + (", which explains the difference." if abs(explained - diff) <= tol else f", leaving {_money(diff - explained)} unexplained.")
        )
        issues.append(
            DataQualityIssue(
                code=DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL,
                severity=Severity.WARNING,
                message=(
                    f"{label}: management's reported EBITDA of {_money(D(mgmt[label]))} is {_money(abs(diff))} {direction} "
                    f"than EBITDA recomputed from the GL ({_money(D(ebitda[label].ebitda))})." + tail
                ),
                period_label=label,
                amount=fmt(diff),
            )
        )
    issues += _arithmetic_issues(pkg.schedule, labels, tol)

    return ReconciliationResult(
        items=items,
        issues=issues,
        gl_ebitda=ebitda,
        mgmt_reported_ebitda=mgmt,
        months_compared=len(compared_months),
        accounts_compared=len(accounts),
        variance_count=sum(1 for i in items if not i.within_tolerance),
    )


def _pl_ebitda_effect(pkg: DealPackage, items: list[ReconciliationItem], months: set[str]) -> Decimal:
    """EBITDA effect of P&L-vs-GL variances in the given months (variance is debit-positive)."""
    total = ZERO
    for item in items:
        if item.month in months and _class_of(pkg, item.account) not in EBITDA_EXCLUDED_CLASSES:
            total -= D(item.variance)
    return total

