"""Tests for qoe.reconcile: GL vs P&L, completeness, duplicates, and GL-derived EBITDA."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

import pytest

from qoe.money import D, fmt
from qoe.reconcile import find_duplicate_entries, find_duplicate_groups, gl_ebitda, is_generic_doc_number, reconcile
from qoe.schemas import (
    Account,
    AdjustmentClaim,
    DataQualityCode,
    DealFiles,
    DealMeta,
    DealPackage,
    EbitdaClass,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PeriodDef,
    PLAccountLine,
    Severity,
)

# ---------------------------------------------------------------------------
# In-memory builders
# ---------------------------------------------------------------------------

_ROW = iter(range(10, 100000))

CLASSES = {
    "1000": ("Checking", EbitdaClass.BALANCE_SHEET),
    "4000": ("Service Revenue", EbitdaClass.REVENUE),
    "5000": ("Materials", EbitdaClass.COGS),
    "6100": ("Rent", EbitdaClass.OPEX),
    "6200": ("Insurance", EbitdaClass.OPEX),
    "6300": ("Software", EbitdaClass.OPEX),
    "6400": ("Legal", EbitdaClass.OPEX),
    "7000": ("Depreciation", EbitdaClass.DEPRECIATION),
    "7050": ("Amortization", EbitdaClass.AMORTIZATION),
    "8100": ("Interest Expense", EbitdaClass.INTEREST),
    "8150": ("Interest Income", EbitdaClass.INTEREST),
    "9000": ("Income Taxes", EbitdaClass.TAXES),
}


def entry(day: str, account: str, amount: str, counterparty: str = "", memo: str = "", doc: str = "", row: Optional[int] = None) -> GLEntry:
    source_row = row if row is not None else next(_ROW)
    return GLEntry(
        entry_id=f"GL-R{source_row}",
        date=day,
        period=day[:7],
        account=account,
        account_name=CLASSES.get(account, (account, None))[0],
        counterparty=counterparty,
        memo=memo,
        doc_number=doc,
        amount=fmt(amount),
        source_file="gl.csv",
        source_row=source_row,
    )


def accounts(extra: Optional[dict[str, Account]] = None) -> dict[str, Account]:
    out = {n: Account(number=n, name=name, source_type="", ebitda_class=cls, mapping_basis="type rule") for n, (name, cls) in CLASSES.items()}
    out.update(extra or {})
    return out


def pl_from_gl(gl: Iterable[GLEntry], months: list[str], tweaks: Optional[dict[tuple[str, str], str]] = None,
               accts: Optional[dict[str, Account]] = None) -> ManagementPL:
    """A P&L that agrees with the GL except for ``tweaks`` ((month, account) -> added amount)."""
    accts = accts or accounts()
    totals: dict[tuple[str, str], Decimal] = {}
    for e in gl:
        if accts.get(e.account) and accts[e.account].ebitda_class is EbitdaClass.BALANCE_SHEET:
            continue
        totals[(e.period, e.account)] = totals.get((e.period, e.account), Decimal(0)) + D(e.amount)
    for key, delta in (tweaks or {}).items():
        totals[key] = totals.get(key, Decimal(0)) + D(delta)
    numbers = sorted({a for _, a in totals})
    lines = [
        PLAccountLine(
            account=n,
            account_name=CLASSES.get(n, (n, None))[0],
            section="Income" if n.startswith("4") else "Expenses",
            amounts={m: fmt(totals.get((m, n), 0)) for m in months},
            source_row=i + 6,
        )
        for i, n in enumerate(numbers)
    ]
    return ManagementPL(source_file="pl.xlsx", months=months, lines=lines)


def package(gl: list[GLEntry], pl: ManagementPL, periods: list[tuple[str, str, str]], data: tuple[str, str],
            schedule: Optional[ManagementSchedule] = None, accts: Optional[dict[str, Account]] = None) -> DealPackage:
    labels = [p[0] for p in periods]
    meta = DealMeta(
        deal_id="unit",
        target_name="Unit Co (SYNTHETIC)",
        periods=[PeriodDef(label=lab, start=s, end=e) for lab, s, e in periods],
        data_start=data[0],
        data_end=data[1],
        files=DealFiles(gl="gl.csv", chart_of_accounts="coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
    )
    return DealPackage(
        deal_dir="unit",
        meta=meta,
        accounts=accts if accts is not None else accounts(),
        gl=gl,
        pl=pl,
        schedule=schedule or ManagementSchedule(source_file="adj.xlsx", period_labels=labels),
        documents=[],
    )


def steady_gl(months: list[str], skip: Iterable[str] = ()) -> list[GLEntry]:
    """Revenue, COGS and four expense accounts every month."""
    out = []
    for m in months:
        if m in skip:
            continue
        out += [
            entry(f"{m}-05", "4000", "-10000", "Acme", "Service"),
            entry(f"{m}-06", "5000", "3000", "Supply Co", "Materials"),
            entry(f"{m}-01", "6100", "2000", "Landlord", "Rent"),
            entry(f"{m}-02", "6200", "500", "Coastal Risk", "Premium"),
            entry(f"{m}-03", "6300", "250", "Brightline", "Subscription"),
            entry(f"{m}-28", "7000", "300", "", "Depreciation"),
        ]
    return out


def codes(issues) -> list[str]:
    return [i.code.value for i in issues]


# ---------------------------------------------------------------------------
# EBITDA from the GL
# ---------------------------------------------------------------------------


def test_gl_ebitda_adds_back_interest_taxes_da_over_overlapping_periods():
    months = ["2024-01", "2024-02", "2024-03", "2024-04"]
    gl = []
    for m in months:
        gl += [entry(f"{m}-05", "4000", "-1000"), entry(f"{m}-06", "6100", "400"), entry(f"{m}-28", "7000", "30")]
    gl += [
        entry("2024-02-28", "8100", "50"),  # interest expense
        entry("2024-02-28", "8150", "-5"),  # interest income nets inside interest
        entry("2024-03-31", "9000", "20"),
        entry("2024-04-30", "7050", "10"),
        entry("2024-01-15", "1000", "9999"),  # balance sheet: not P&L, not EBITDA
    ]
    pkg = package(gl, pl_from_gl(gl, months), [("P1", "2024-01", "2024-03"), ("P2", "2024-02", "2024-04")], ("2024-01", "2024-04"))
    result = gl_ebitda(pkg)
    assert list(result) == ["P1", "P2"]
    p1, p2 = result["P1"], result["P2"]
    assert (p1.net_income, p1.interest, p1.taxes, p1.depreciation, p1.amortization) == ("1645.00", "45.00", "20.00", "90.00", "0.00")
    assert (p2.net_income, p2.interest, p2.taxes, p2.depreciation, p2.amortization) == ("1635.00", "45.00", "20.00", "90.00", "10.00")
    # EBITDA is revenue less operating cost only: interest, tax and D&A never move it.
    assert p1.ebitda == p2.ebitda == "1800.00"
    assert reconcile(pkg).gl_ebitda == result


# ---------------------------------------------------------------------------
# GL vs P&L
# ---------------------------------------------------------------------------


def test_planted_pl_variance_is_the_only_issue():
    months = ["2024-01", "2024-02", "2024-03"]
    gl = steady_gl(months)
    pl = pl_from_gl(gl, months, {("2024-02", "6200"): "25000", ("2024-03", "6300"): "0.60"})
    recon = reconcile(package(gl, pl, [("Q1", "2024-01", "2024-03")], ("2024-01", "2024-03")))
    assert codes(recon.issues) == ["RECON_VARIANCE"]
    issue = recon.issues[0]
    assert (issue.month, issue.account, issue.amount, issue.severity) == ("2024-02", "6200", "25000.00", Severity.WARNING)
    assert "P&L EBITDA is 25,000.00 lower than the GL" in issue.message
    assert recon.months_compared == 3
    assert recon.accounts_compared == 6
    assert len(recon.items) == 18
    assert recon.variance_count == 1
    item = next(i for i in recon.items if (i.month, i.account) == ("2024-02", "6200"))
    assert (item.gl_amount, item.pl_amount, item.variance, item.within_tolerance) == ("500.00", "25500.00", "25000.00", False)
    small = next(i for i in recon.items if (i.month, i.account) == ("2024-03", "6300"))
    assert small.variance == "0.60" and small.within_tolerance


def test_account_coverage_is_reported_once_per_account():
    months = ["2024-01", "2024-02"]
    gl = steady_gl(months) + [entry("2024-01-20", "6400", "700", "Hollis", "Fees")]
    pl = pl_from_gl([e for e in gl if e.account != "6400"], months, {("2024-02", "5000"): "0"})
    pl.lines.append(PLAccountLine(account="6900", account_name="Office", section="Expenses",
                                  amounts={"2024-01": "40.00", "2024-02": "0.00"}, source_row=40))
    pl.lines.append(PLAccountLine(account="6950", account_name="Empty", section="Expenses",
                                  amounts={"2024-01": "0.00", "2024-02": "0.00"}, source_row=41))
    recon = reconcile(package(gl, pl, [("P", "2024-01", "2024-02")], ("2024-01", "2024-02")))
    assert codes(recon.issues) == ["GL_ACCOUNT_NOT_IN_PL", "PL_ACCOUNT_NOT_IN_GL"]
    gl_only, pl_only = recon.issues
    assert (gl_only.account, gl_only.amount) == ("6400", "700.00")
    assert (pl_only.account, pl_only.amount) == ("6900", "40.00")
    # Items still carry the one-sided amounts so monthly totals tie.
    assert any(i.account == "6400" and i.variance == "-700.00" for i in recon.items)


# ---------------------------------------------------------------------------
# Missing periods
# ---------------------------------------------------------------------------


def test_month_with_no_gl_entries_is_missing_period():
    months = ["2024-01", "2024-02", "2024-03", "2024-04"]
    full = steady_gl(months)
    gl = [e for e in full if e.period != "2024-03"]
    recon = reconcile(package(gl, pl_from_gl(full, months), [("P", "2024-01", "2024-04")], ("2024-01", "2024-04")))
    assert codes(recon.issues) == ["MISSING_PERIOD"]
    issue = recon.issues[0]
    assert (issue.month, issue.severity) == ("2024-03", Severity.CRITICAL)
    assert issue.amount == "4250.00"  # the P&L's March EBITDA, all missing from the GL
    # The P&L still shows March, so the items record the gap without one issue per account.
    assert sum(1 for i in recon.items if i.month == "2024-03" and not i.within_tolerance) == 6


def test_partially_posted_month_is_missing_period():
    months = ["2024-01", "2024-02", "2024-03"]
    full = steady_gl(months)
    gl = [e for e in full if e.period != "2024-02" or e.account in ("4000", "5000")]
    recon = reconcile(package(gl, pl_from_gl(full, months), [("P", "2024-01", "2024-03")], ("2024-01", "2024-03")))
    # One root cause, one issue: the four unposted accounts are not repeated as RECON_VARIANCEs.
    assert codes(recon.issues) == ["MISSING_PERIOD"]
    issue = recon.issues[0]
    assert (issue.month, issue.severity) == ("2024-02", Severity.WARNING)
    assert "only 2 of the 6 accounts" in issue.message
    assert "6100, 6200, 6300, 7000" in issue.message
    # 6100 + 6200 + 6300 unposted = 2,750 of operating cost the GL lacks (7000 is below EBITDA).
    assert issue.amount == "-2750.00"
    assert "shows EBITDA 2,750.00 lower than the GL" in issue.message
    assert sum(1 for i in recon.items if i.month == "2024-02" and not i.within_tolerance) == 4


def _partial(month: str) -> list[GLEntry]:
    """Only revenue and rent posted: the month's books are not closed."""
    return [entry(f"{month}-05", "4000", "-10000", "Acme", "Service"), entry(f"{month}-01", "6100", "2000", "Landlord", "Rent")]


def test_two_consecutive_incomplete_months_are_both_missing_period():
    """Each incomplete month must not become the other's baseline (mid-year Jun + Jul)."""
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = []
    for m in months:
        gl += _partial(m) if m in ("2024-06", "2024-07") else steady_gl([m])
    recon = reconcile(package(gl, pl_from_gl(steady_gl(months), months), [("FY", "2024-01", "2024-12")], ("2024-01", "2024-12")))
    missing = [i for i in recon.issues if i.code is DataQualityCode.MISSING_PERIOD]
    assert [i.month for i in missing] == ["2024-06", "2024-07"]
    assert all("only 2 of the 6 accounts" in i.message for i in missing)


@pytest.mark.parametrize("tail", [["2024-12"], ["2024-11", "2024-12"], ["2024-10", "2024-11", "2024-12"]])
def test_unclosed_tail_months_are_missing_period(tail: list[str]):
    """The last months of a TTM before close: the P&L comes from the same unclosed books, so only
    the completeness test can see them."""
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = []
    for m in months:
        gl += _partial(m) if m in tail else steady_gl([m])
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("FY", "2024-01", "2024-12")], ("2024-01", "2024-12")))
    assert [i.month for i in recon.issues if i.code is DataQualityCode.MISSING_PERIOD] == tail


def test_sporadic_accounts_do_not_make_a_complete_month_look_incomplete():
    """A quarterly account is not part of the monthly baseline."""
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = steady_gl(months) + [entry(f"{m}-15", "6400", "900", "Hollis", "Quarterly review") for m in ("2024-03", "2024-06", "2024-09", "2024-12")]
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("FY", "2024-01", "2024-12")], ("2024-01", "2024-12")))
    assert "MISSING_PERIOD" not in codes(recon.issues)


def test_pl_missing_month_and_period_outside_data_range():
    months = ["2024-01", "2024-02", "2024-03"]
    gl = steady_gl(months)
    pl = pl_from_gl(gl, ["2024-01", "2024-03"])
    recon = reconcile(package(gl, pl, [("P", "2024-01", "2024-04")], ("2024-01", "2024-03")))
    assert sorted((i.code.value, i.month or i.period_label) for i in recon.issues) == [
        ("MISSING_PERIOD", "2024-02"),
        ("MISSING_PERIOD", "P"),
    ]
    assert recon.months_compared == 2


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------


def test_find_duplicate_entries_rules():
    same_doc = [entry("2025-05-10", "6200", "18750", "Coastal Risk", "Premium", "CR-5521", row=101),
                entry("2025-05-13", "6200", "18750", "Coastal Risk", "Premium", "CR-5521", row=104)]
    same_memo = [entry("2025-06-01", "6400", "900", "Hollis", "Retainer June", row=201),
                 entry("2025-06-07", "6400", "900", "Hollis", "Retainer June", row=202)]
    eight_days = [entry(f"2025-07-{d:02d}", "6100", "150", "CleanCo", "Cleaning", row=300 + d) for d in (1, 9, 17)]
    seven_days = [entry("2025-10-01", "6100", "60", "Shred Co", "Shredding", row=801),
                  entry("2025-10-08", "6100", "60", "Shred Co", "Shredding", row=802)]
    different_vendor = [entry("2025-08-01", "6300", "99", "Vendor A", "Seat", "INV-1", row=401),
                        entry("2025-08-02", "6300", "99", "Vendor B", "Seat", "INV-1", row=402)]
    no_context = [entry("2025-08-05", "6300", "12", row=501), entry("2025-08-06", "6300", "12", row=502)]
    zero = [entry("2025-08-09", "6300", "0", "X", "Void", "V-1", row=601), entry("2025-08-09", "6300", "0", "X", "Void", "V-1", row=602)]
    # Same doc number on the same day twice, and again three months later: only the pair
    # within the 45-day document window is one document posted twice.
    triple = [entry("2025-09-01", "5000", "75", "Supply", "Filters", "S-9", row=703),
              entry("2025-09-01", "5000", "75", "Supply", "Filters", "S-9", row=701),
              entry("2025-12-01", "5000", "75", "supply ", "Filters", "s-9", row=702)]
    gl = same_doc + same_memo + eight_days + seven_days + different_vendor + no_context + zero + triple
    assert find_duplicate_entries(gl) == [
        ["GL-R101", "GL-R104"],
        ["GL-R201", "GL-R202"],
        ["GL-R701", "GL-R703"],
        ["GL-R801", "GL-R802"],
    ]
    assert [basis for _, basis in find_duplicate_groups(gl)] == ["doc", "memo", "doc", "memo"]


@pytest.mark.parametrize("doc", ["ACH", "ach", "EFT", "Debit", "DEBIT", "WIRE", "Wire Transfer", "CHK", "Auto Pay", "-", "N/A", "000", " "])
def test_generic_payment_references_never_form_doc_groups(doc: str):
    """A monthly bill whose Num is a payment-channel placeholder is not twelve postings of one document."""
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = [entry(f"{m}-01", "6100", "2000", "Palm River Properties", f"Rent {m}", doc=doc) for m in months]
    assert find_duplicate_entries(gl) == []
    # Two postings a few days apart with a placeholder Num: the placeholder proves nothing either.
    pair = [entry("2024-03-01", "6100", "2000", "Palm River Properties", "Rent March", doc=doc, row=11),
            entry("2024-03-04", "6100", "2000", "Palm River Properties", "Rent Mar", doc=doc, row=12)]
    assert find_duplicate_entries(pair) == []


def test_generic_doc_number_classification():
    for generic in ("ACH", "eft", "Debit", "WIRE", "chk", "Direct Debit", "EFT PMT", "--", "n/a", "0", "0000"):
        assert is_generic_doc_number(generic), generic
    for specific in ("CRI-25-0507", "10231", "ACH-004512", "CHK 1043", "INV-1", "S-9", "JE-12"):
        assert not is_generic_doc_number(specific), specific


def test_placeholder_doc_numbers_do_not_turn_a_memo_group_into_a_doc_group():
    """Same memo two days apart with Num "ACH": a memo-rule group, reported as such (stays a question)."""
    gl = [entry("2024-05-01", "6200", "900", "Coastal Risk", "Premium May", doc="ACH", row=21),
          entry("2024-05-03", "6200", "900", "Coastal Risk", "Premium May", doc="ACH", row=22)]
    assert find_duplicate_groups(gl) == [(["GL-R21", "GL-R22"], "memo")]
    months = ["2024-05"]
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("P", "2024-05", "2024-05")], ("2024-05", "2024-05")))
    issue = next(i for i in recon.issues if i.code is DataQualityCode.DUPLICATE_GL_ENTRY)
    assert "same memo within 7 days" in issue.message and "doc #" not in issue.message


def test_doc_number_groups_need_the_postings_within_45_days():
    near = [entry("2024-01-10", "6400", "5000", "Hollis", "Matter 2291", "25-0212", row=31),
            entry("2024-02-15", "6400", "5000", "Hollis", "Matter 2291 paid", "25-0212", row=32)]  # 36 days: bill, then paid as expense
    far = [entry("2024-01-10", "6400", "7000", "Hollis", "Matter 1004", "25-0415", row=41),
           entry("2024-03-15", "6400", "7000", "Hollis", "Matter 1004 again", "25-0415", row=42)]  # 65 days
    other_vendor = [entry("2024-04-01", "6400", "5000", "Baxter", "Fees", "25-0212", row=51)]
    assert find_duplicate_groups(near + far + other_vendor) == [(["GL-R31", "GL-R32"], "doc")]


def test_standing_reference_used_every_month_is_not_a_duplicate():
    """A lease number on every monthly rent bill (a standing reference, not a document number)."""
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = [entry(f"{m}-01", "6100", "2000", "Palm River Properties", f"Rent {m}", doc="LEASE-7") for m in months]
    assert find_duplicate_entries(gl) == []
    # The memo rule still catches a real double posting of one month's bill.
    gl.append(entry("2024-06-03", "6100", "2000", "Palm River Properties", "Rent 2024-06", doc="LEASE-7", row=990))
    groups = find_duplicate_groups(gl)
    assert len(groups) == 1 and groups[0][1] == "memo" and "GL-R990" in groups[0][0] and len(groups[0][0]) == 2


def test_memo_groups_are_anchored_to_the_first_posting_and_do_not_chain():
    chain = [entry("2024-03-01", "6400", "900", "V", "m", row=338), entry("2024-03-07", "6400", "900", "V", "m", row=339),
             entry("2024-03-13", "6400", "900", "V", "m", row=340)]
    # The 13th is 12 days after the 1st: it is not pulled in through the 7th.
    assert find_duplicate_entries(chain) == [["GL-R338", "GL-R339"]]


def test_weekly_recurring_charge_is_not_a_duplicate():
    from datetime import date, timedelta

    months = [f"2024-{m:02d}" for m in range(1, 13)]
    gl = steady_gl(months)
    d = date(2024, 1, 5)
    weekly = []
    while d.year == 2024:
        weekly.append(entry(d.isoformat(), "6400", "2500", "Harbor Staffing", "Weekly bookkeeping retainer"))
        d += timedelta(days=7)
    assert find_duplicate_entries(weekly) == []
    # Weekly with jitter (posted on varying weekdays) is still a recurring charge.
    jitter = [entry((date(2024, 1, 1) + timedelta(days=7 * k + (k % 3))).isoformat(), "6400", "800", "Cleaner", "Weekly cleaning")
              for k in range(20)]
    assert find_duplicate_entries(jitter) == []
    gl += weekly
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("FY", "2024-01", "2024-12")], ("2024-01", "2024-12")))
    assert "DUPLICATE_GL_ENTRY" not in codes(recon.issues)


def test_monthly_series_with_one_double_posting_is_still_found():
    gl = [entry(f"2024-{m:02d}-02", "6300", "250", "Brightline", "Subscription", row=600 + m) for m in range(1, 13)]
    gl.append(entry("2024-05-04", "6300", "250", "Brightline", "Subscription", row=699))
    assert find_duplicate_groups(gl) == [(["GL-R605", "GL-R699"], "memo")]


def test_duplicate_issue_lists_the_whole_group():
    months = ["2024-01", "2024-02"]
    gl = steady_gl(months) + [
        entry("2024-02-05", "6200", "1200", "Coastal Risk", "Annual rider", "CR-77", row=900),
        entry("2024-02-08", "6200", "1200", "Coastal Risk", "Annual rider", "CR-77", row=903),
    ]
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("P", "2024-01", "2024-02")], ("2024-01", "2024-02")))
    assert codes(recon.issues) == ["DUPLICATE_GL_ENTRY"]
    issue = recon.issues[0]
    assert issue.entry_ids == ["GL-R900", "GL-R903"]
    assert (issue.month, issue.account, issue.amount) == ("2024-02", "6200", "1200.00")
    assert "GL rows 900, 903" in issue.message


# ---------------------------------------------------------------------------
# Management schedule
# ---------------------------------------------------------------------------


def _schedule(labels: list[str], ni: dict, interest: dict, taxes: dict, da: dict, reported: dict, adjustments: list[dict],
              total: dict, adjusted: dict) -> ManagementSchedule:
    def s(d: dict) -> dict[str, str]:
        return {k: fmt(v) for k, v in d.items()}

    return ManagementSchedule(
        source_file="adj.xlsx",
        period_labels=labels,
        net_income=s(ni), interest=s(interest), taxes=s(taxes), depreciation_amortization=s(da),
        reported_ebitda=s(reported), total_adjustments=s(total), adjusted_ebitda=s(adjusted),
        adjustments=[AdjustmentClaim(adj_id=f"M-{i + 1:02d}", title="Adj", amounts=s(a), source_row=10 + i) for i, a in enumerate(adjustments)],
    )


def test_mgmt_reported_ebitda_differs_from_gl():
    months = ["2024-01", "2024-02", "2024-03"]
    gl = steady_gl(months)
    pl = pl_from_gl(gl, months, {("2024-03", "6100"): "25000"})
    periods = [("Q1", "2024-01", "2024-03"), ("Jan", "2024-01", "2024-01")]
    # GL EBITDA: (10000 - 3000 - 2000 - 500 - 250) = 4250 per month.
    sched = _schedule(
        ["Q1", "Jan"],
        ni={"Q1": "-13150", "Jan": "3950"}, interest={}, taxes={}, da={"Q1": "900", "Jan": "300"},
        reported={"Q1": "-12250", "Jan": "4250"},
        adjustments=[{"Q1": "100", "Jan": "0"}], total={"Q1": "100", "Jan": "0"}, adjusted={"Q1": "-12150", "Jan": "4250"},
    )
    recon = reconcile(package(gl, pl, periods, ("2024-01", "2024-03"), schedule=sched))
    assert recon.gl_ebitda["Q1"].ebitda == "12750.00"
    assert recon.mgmt_reported_ebitda == {"Q1": "-12250.00", "Jan": "4250.00"}
    differs = [i for i in recon.issues if i.code is DataQualityCode.MGMT_EBITDA_DIFFERS_FROM_GL]
    assert [(i.period_label, i.amount) for i in differs] == [("Q1", "-25000.00")]
    assert "25,000.00 lower" in differs[0].message
    assert "explains the difference" in differs[0].message
    assert codes(recon.issues) == ["RECON_VARIANCE", "MGMT_EBITDA_DIFFERS_FROM_GL"]


def test_mgmt_schedule_arithmetic_checks():
    months = ["2024-01"]
    gl = steady_gl(months)
    sched = _schedule(
        ["Jan"],
        ni={"Jan": "3950"}, interest={"Jan": "10"}, taxes={}, da={"Jan": "300"},
        reported={"Jan": "4250"},  # NI + I + T + DA = 4260: does not foot
        adjustments=[{"Jan": "100"}, {"Jan": "-40"}],
        total={"Jan": "70"},  # sum of adjustments is 60
        adjusted={"Jan": "4400"},  # reported + total = 4320
    )
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("Jan", "2024-01", "2024-01")], ("2024-01", "2024-01"), schedule=sched))
    arithmetic = [i for i in recon.issues if i.code is DataQualityCode.MGMT_SCHEDULE_ARITHMETIC]
    assert [(i.period_label, i.amount) for i in arithmetic] == [("Jan", "-10.00"), ("Jan", "10.00"), ("Jan", "80.00")]
    assert "reported EBITDA" in arithmetic[0].message and "total adjustments" in arithmetic[1].message
    assert codes(recon.issues) == ["MGMT_SCHEDULE_ARITHMETIC"] * 3


def test_reported_ebitda_derived_from_components_when_row_missing():
    months = ["2024-01"]
    gl = steady_gl(months)
    sched = _schedule(["Jan"], ni={"Jan": "3950"}, interest={}, taxes={}, da={"Jan": "300"}, reported={},
                      adjustments=[], total={}, adjusted={})
    recon = reconcile(package(gl, pl_from_gl(gl, months), [("Jan", "2024-01", "2024-01")], ("2024-01", "2024-01"), schedule=sched))
    assert recon.mgmt_reported_ebitda == {"Jan": "4250.00"}
    assert recon.issues == []


# ---------------------------------------------------------------------------
# Unmapped accounts
# ---------------------------------------------------------------------------


def test_unmapped_accounts_are_flagged_and_kept_in_ebitda():
    months = ["2024-01"]
    fallback = Account(number="6990", name="Clearing", source_type="Clearing", ebitda_class=EbitdaClass.OPEX,
                       mapping_basis="fallback: unrecognized account type 'Clearing'; defaulted to OPEX")
    accts = accounts({"6990": fallback})
    gl = steady_gl(months) + [entry("2024-01-09", "6990", "100", "X", "Misc"), entry("2024-01-09", "6995", "50", "Y", "Misc")]
    pkg = package(gl, pl_from_gl(gl, months, accts=accts), [("Jan", "2024-01", "2024-01")], ("2024-01", "2024-01"), accts=accts)
    recon = reconcile(pkg)
    unmapped = [i for i in recon.issues if i.code is DataQualityCode.UNMAPPED_ACCOUNT]
    assert [(i.account, i.severity) for i in unmapped] == [("6990", Severity.WARNING), ("6995", Severity.WARNING)]
    assert recon.gl_ebitda["Jan"].ebitda == "4100.00"  # 4250 less the 150 treated as OPEX


def test_reconcile_is_deterministic():
    months = ["2024-01", "2024-02"]
    gl = steady_gl(months) + [entry("2024-02-05", "6200", "1200", "Coastal", "Rider", "CR-1"), entry("2024-02-06", "6200", "1200", "Coastal", "Rider", "CR-1")]
    pkg = package(gl, pl_from_gl(gl, months, {("2024-01", "6100"): "5"}), [("P", "2024-01", "2024-02")], ("2024-01", "2024-02"))
    assert reconcile(pkg).model_dump_json() == reconcile(pkg).model_dump_json()


# ---------------------------------------------------------------------------
# Integration: the Meridian dev deal (skipped until the generator has run)
# ---------------------------------------------------------------------------


def _find_deal(deal_id: str) -> Optional[Path]:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / "dev" / deal_id
        if (candidate / "deal.yaml").is_file():
            return candidate
    return None


MERIDIAN = _find_deal("meridian_mechanical")
needs_meridian = pytest.mark.skipif(MERIDIAN is None, reason="data/dev/meridian_mechanical not generated")


@pytest.fixture(scope="module")
def meridian():
    from qoe.ingest import load_deal

    pkg = load_deal(MERIDIAN)
    return pkg, reconcile(pkg)


@needs_meridian
def test_meridian_reconciles_with_only_the_planted_issues(meridian):
    pkg, recon = meridian
    assert pkg.meta.gl_format in ("auto", "qbo_gl_csv")
    assert any("qbo_gl_csv" in n for n in pkg.ingest_notes)
    assert len(pkg.gl) > 1000
    assert recon.months_compared == 30

    by_code: dict[str, list] = {}
    for issue in recon.issues:
        by_code.setdefault(issue.code.value, []).append(issue)
    assert sorted(by_code) == ["DUPLICATE_GL_ENTRY", "MGMT_EBITDA_DIFFERS_FROM_GL", "RECON_VARIANCE"], [i.message for i in recon.issues]

    (dup,) = by_code["DUPLICATE_GL_ENTRY"]
    assert (dup.account, dup.month, len(dup.entry_ids)) == ("6200", "2025-05", 2)
    rows = {e.entry_id: e for e in pkg.gl}
    first, second = (rows[i] for i in dup.entry_ids)
    assert first.doc_number == second.doc_number and first.amount == second.amount

    (variance,) = by_code["RECON_VARIANCE"]
    assert (variance.month, variance.account, variance.amount) == ("2025-12", "6000", "25000.00")

    differs = {i.period_label: i.amount for i in by_code["MGMT_EBITDA_DIFFERS_FROM_GL"]}
    assert differs == {"FY2025": "-25000.00", "TTM Jun-26": "-25000.00"}
    assert D(recon.gl_ebitda["FY2025"].ebitda) > 0


@needs_meridian
def test_meridian_matches_answer_key(meridian):
    """GL EBITDA and planted data-quality issues agree with the answer key (read via qoe.evaluate only)."""
    evaluate = pytest.importorskip("qoe.evaluate")
    pkg, recon = meridian
    gt = evaluate.load_ground_truth(MERIDIAN)
    for label, amount in gt.gl_ebitda.items():
        assert recon.gl_ebitda[label].ebitda == fmt(amount), label
    for expected in gt.data_quality:
        matches = [
            i for i in recon.issues
            if i.code is expected.code
            and (expected.month is None or i.month == expected.month)
            and (expected.account is None or i.account == expected.account)
        ]
        assert matches, f"planted {expected.code.value} {expected.month} {expected.account} not detected"
        if expected.gl_rows and expected.code is DataQualityCode.DUPLICATE_GL_ENTRY:
            assert sorted(int(e.removeprefix("GL-R")) for e in matches[0].entry_ids) == sorted(expected.gl_rows)
