"""Ledger synthesis: seeded background activity, planted rows, planted data-quality issues.

The ledger is the company's books. The GL export is the ledger minus any
planted missing month; management's monthly P&L is the ledger plus any planted
top-side entries. Every row carries a stable key so the answer key can refer
to rows by key and the writer can resolve keys to final source rows.

Money is Decimal throughout. Randomness comes from integer draws on RNGs
seeded per stream, so adding a stream never perturbs the others.
"""

from __future__ import annotations

import calendar
import fnmatch
import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from qoe.money import D, ZERO, q2
from qoe.periods import month_range
from qoe.schemas import EbitdaClass

from .accounts import AccountInfo
from .spec import AmountSpec, Counterparty, DealSpec, Schedule, Stream

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAME = [calendar.month_name[i] for i in range(1, 13)]
TEXT_FIELDS = ("key", "counterparty", "num", "memo", "txn_type")


class GenerationError(ValueError):
    """The spec is inconsistent; the message says what to fix in the YAML."""


@dataclass
class Txn:
    key: str
    date: date
    account: str
    txn_type: str  # generic (bill, invoice, journal, ...) or a literal source label
    counterparty: str
    num: str
    memo: str
    amount: Decimal  # debit-positive
    split: Optional[str]
    dimensions: dict[str, str]
    origin: str  # background | planted | duplicate
    seq: int
    in_gl: bool = True
    num_req: Optional[tuple[str, str, int, tuple[int, int]]] = None  # (state key, format, start, step)

    @property
    def month(self) -> str:
        return f"{self.date.year:04d}-{self.date.month:02d}"


@dataclass
class Ledger:
    txns: list[Txn]
    topside: dict[tuple[str, str], Decimal] = field(default_factory=dict)  # (month, account) -> amount
    duplicate_pairs: list[tuple[str, str]] = field(default_factory=list)  # (original key, duplicate key)

    def gl_txns(self) -> list[Txn]:
        return [t for t in self.txns if t.in_gl]

    def by_key(self) -> dict[str, Txn]:
        return {t.key: t for t in self.txns}


def sub_rng(seed: int, *parts: str) -> random.Random:
    digest = hashlib.sha256("|".join([str(seed), *parts]).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _ym(month: str) -> tuple[int, int]:
    y, m = month.split("-")
    return int(y), int(m)


def _months_between(start: str, month: str) -> int:
    (y0, m0), (y1, m1) = _ym(start), _ym(month)
    return (y1 - y0) * 12 + (m1 - m0)


def _day_date(month: str, day: int) -> date:
    y, m = _ym(month)
    last = calendar.monthrange(y, m)[1]
    return date(y, m, last if day == -1 else min(day, last))


def _adjust(d: date, mode: str) -> date:
    if mode == "none":
        return d
    step = -1 if mode == "prior" else 1
    while d.weekday() >= 5:
        d += timedelta(days=step)
    return d


def _business_days(month: str) -> list[date]:
    y, m = _ym(month)
    return [date(y, m, day) for day in range(1, calendar.monthrange(y, m)[1] + 1) if date(y, m, day).weekday() < 5]


def date_context(d: date, n: int = 1) -> dict[str, object]:
    prev = (d.replace(day=1) - timedelta(days=1))
    return {
        "yyyy": f"{d.year:04d}",
        "yy": f"{d.year % 100:02d}",
        "last_yyyy": f"{d.year - 1:04d}",
        "mm": f"{d.month:02d}",
        "dd": f"{d.day:02d}",
        "mon": MONTH_ABBR[d.month - 1],
        "month": MONTH_NAME[d.month - 1],
        "q": (d.month - 1) // 3 + 1,
        "n": n,
        "mdy": d.strftime("%m/%d/%Y"),
        "date": d.isoformat(),
        "prev_mon": MONTH_ABBR[prev.month - 1],
        "prev_month": MONTH_NAME[prev.month - 1],
        "prev_yyyy": f"{prev.year:04d}",
        "prev_month_end_mdy": prev.strftime("%m/%d/%Y"),
    }


def render(template: str, ctx: dict[str, object], where: str) -> str:
    try:
        return template.format_map(ctx)
    except (KeyError, IndexError, ValueError) as exc:
        raise GenerationError(f"{where}: cannot render {template!r}: {exc}") from exc


def round_to(value: Decimal, increment: Decimal) -> Decimal:
    return q2((value / increment).quantize(Decimal(1), rounding=ROUND_HALF_UP) * increment)


def _seasonality(amount: AmountSpec) -> list[Decimal]:
    if not amount.seasonality:
        return [Decimal(1)] * 12
    factors = [D(f) for f in amount.seasonality]
    mean = sum(factors, ZERO) / 12
    return [f / mean for f in factors]


def _slot_dates(month: str, sched: Schedule, rng: random.Random) -> list[date]:
    if sched.days is not None:
        dates = [_adjust(_day_date(month, d), sched.adjust) for d in sched.days]
    elif sched.count is not None:
        lo, hi = sched.count
        pool = _business_days(month)
        dates = sorted(rng.sample(pool, min(rng.randint(lo, hi), len(pool))))
    else:
        y, m = _ym(month)
        wanted = set(sched.weekdays or [])
        dates = [date(y, m, day) for day in range(1, calendar.monthrange(y, m)[1] + 1) if date(y, m, day).weekday() in wanted]
    return dates


def _weighted_pick(cps: list[Counterparty], rng: random.Random) -> Counterparty:
    total = sum(c.weight for c in cps)
    r = rng.randint(1, total)
    for c in cps:
        r -= c.weight
        if r <= 0:
            return c
    return cps[-1]


def _split_total(total: Decimal, weights: list[int]) -> list[Decimal]:
    wsum = Decimal(sum(weights))
    parts = [q2(total * Decimal(w) / wsum) for w in weights[:-1]]
    parts.append(total - sum(parts, ZERO))
    return parts


def _fixed_amount(stream: Stream, cp: Optional[Counterparty], d: date, data_start: str) -> Decimal:
    a = stream.amount
    if cp is not None and cp.amount is not None:
        base = D(cp.amount)
    elif a.by_year is not None:
        if d.year not in a.by_year:
            raise GenerationError(f"stream {stream.id}: amount.by_year has no {d.year}")
        base = D(a.by_year[d.year])
    else:
        base = D(a.fixed)
    if a.escalate_pct is not None:
        anchor_month = (cp.start if cp is not None and cp.start else None) or stream.start or data_start
        anchor = _day_date(anchor_month, 1)
        steps = sum(1 for y in range(anchor.year, d.year + 1) if anchor < date(y, a.escalate_month, 1) <= d)
        base = base * (1 + D(a.escalate_pct)) ** steps
    return q2(base)


def _active(cps: list[Counterparty], month: str) -> list[Counterparty]:
    return [c for c in cps if (c.start or "0000-00") <= month <= (c.end or "9999-99")]


class _Builder:
    def __init__(self, spec: DealSpec, accounts: dict[str, AccountInfo]):
        self.spec = spec
        self.accounts = accounts
        self.txns: list[Txn] = []
        self._seq = 0

    def next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def check_account(self, number: str, where: str) -> AccountInfo:
        acct = self.accounts.get(number)
        if acct is None:
            raise GenerationError(f"{where}: account {number} is not in the chart of accounts")
        if not acct.is_pl:
            raise GenerationError(f"{where}: account {number} is a balance-sheet account; the GL holds P&L accounts only")
        return acct

    def background(self, stream: Stream) -> None:
        spec = self.spec
        acct = self.check_account(stream.account, f"stream {stream.id}")
        direction = stream.direction or ("credit" if acct.credit_natural else "debit")
        sign = Decimal(1) if direction == "debit" else Decimal(-1)
        rng = sub_rng(spec.seed, "stream", stream.id)
        a = stream.amount
        season = _seasonality(a)
        first = max(spec.data_start, stream.start or spec.data_start)
        last = min(spec.data_end, stream.end or spec.data_end)
        memos = [stream.memo] if isinstance(stream.memo, str) else list(stream.memo)
        for month in month_range(first, last):
            y, m = _ym(month)
            if stream.schedule.months and m not in stream.schedule.months:
                continue
            dates = _slot_dates(month, stream.schedule, rng)
            active = _active(stream.counterparties, month)
            if not dates or (stream.counterparties and not active):
                continue
            rows: list[tuple[date, Optional[Counterparty], Decimal]] = []
            if stream.mode == "fixed":
                for d in dates:
                    for cp in active or [None]:
                        rows.append((d, cp, _fixed_amount(stream, cp, d, spec.data_start)))
            else:
                growth = (1 + D(a.growth)) ** (Decimal(_months_between(spec.data_start, month)) / 12)
                noise = Decimal(rng.randint(-10000, 10000)) / 10000 * D(a.noise)
                total = round_to(D(a.monthly) * season[m - 1] * growth * (1 + noise), D(a.round))
                spread = int(D(a.spread) * 1000)
                weights = [rng.randint(1000 - spread, 1000 + spread) for _ in dates]
                for d, part in zip(dates, _split_total(total, weights)):
                    rows.append((d, _weighted_pick(active, rng) if active else None, part))
            for n, (d, cp, amount) in enumerate(rows, start=1):
                if amount <= 0:
                    raise GenerationError(f"stream {stream.id}: non-positive row amount in {month}; reduce spread or noise")
                ctx = date_context(d, n)
                for name, options in sorted(stream.choices.items()):
                    ctx[name] = options[rng.randrange(len(options))]
                ctx["job"] = f"{d.year % 100:02d}-{rng.randint(1001, 1899):04d}"
                ctx["counterparty"] = cp.name if cp else ""
                options = memos
                if cp is not None and cp.memo is not None:
                    options = [cp.memo] if isinstance(cp.memo, str) else list(cp.memo)
                memo = render(options[rng.randrange(len(options))], ctx, f"stream {stream.id} memo")
                num_req = None
                if cp is not None and cp.num:
                    num_req = (f"cp:{cp.name}", cp.num, cp.seq_start, cp.seq_step)
                elif stream.num is not None:
                    state = f"seq:{stream.num.sequence}" if stream.num.sequence else f"stream:{stream.id}"
                    start = spec.sequences.get(stream.num.sequence, stream.num.start) if stream.num.sequence else stream.num.start
                    num_req = (state, stream.num.format, start, stream.num.step)
                self.txns.append(
                    Txn(
                        key=f"{stream.id}/{month}/{n}",
                        date=d,
                        account=stream.account,
                        txn_type=stream.txn_type,
                        counterparty=cp.name if cp else "",
                        num="",
                        memo=memo,
                        amount=sign * amount,
                        split=stream.split,
                        dimensions=dict(stream.dimensions),
                        origin="background",
                        seq=self.next_seq(),
                        num_req=num_req,
                    )
                )

    def planted(self) -> None:
        for p in self.spec.planted:
            self.check_account(p.account, f"planted {p.key}")
            if p.date is not None:
                dates = [(date.fromisoformat(p.date), 1)]
            else:
                rep = p.repeat
                dates = []
                for month in month_range(rep.start, rep.end):
                    if rep.months and _ym(month)[1] not in rep.months:
                        continue
                    for n, day in enumerate(rep.days, start=1):
                        dates.append((_adjust(_day_date(month, day), rep.adjust), n))
            for d, n in dates:
                ctx = date_context(d, n)
                where = f"planted {p.key}"
                self.txns.append(
                    Txn(
                        key=render(p.key, ctx, where),
                        date=d,
                        account=p.account,
                        txn_type=p.txn_type,
                        counterparty=render(p.counterparty, ctx, where),
                        num=render(p.num, ctx, where),
                        memo=render(p.memo, ctx, where),
                        amount=q2(D(p.amount)),
                        split=p.split,
                        dimensions=dict(p.dimensions),
                        origin="planted",
                        seq=self.next_seq(),
                    )
                )

    def assign_numbers(self) -> None:
        reserved = {t.num for t in self.txns if t.origin == "planted" and t.num}
        rng = sub_rng(self.spec.seed, "numbers")
        state: dict[str, int] = {}
        for t in sorted((t for t in self.txns if t.num_req), key=lambda t: (t.date, t.seq)):
            skey, fmt, start, step = t.num_req
            cur = state.get(skey)
            while True:
                cur = start if cur is None else cur + rng.randint(*step)
                num = render(fmt, {**date_context(t.date), "seq": cur}, f"number format {fmt!r}")
                if num not in reserved:
                    break
            state[skey] = cur
            t.num = num


def resolve_keys(patterns: list[str], keys: list[str], where: str) -> list[str]:
    """Expand key globs (fnmatch) in order; every pattern must match something."""
    out: list[str] = []
    seen: set[str] = set()
    for pat in patterns:
        hits = [k for k in keys if fnmatch.fnmatchcase(k, pat)]
        if not hits:
            raise GenerationError(f"{where}: key pattern {pat!r} matches no GL row")
        for k in hits:
            if k not in seen:
                seen.add(k)
                out.append(k)
    return out


def duplicate_groups(txns: list[Txn]) -> list[list[Txn]]:
    """Duplicate groups under SPEC §6: same account/amount/counterparty and doc number,
    or same account/amount/counterparty/memo within 7 days."""
    groups: list[list[Txn]] = []
    by_num: dict[tuple, list[Txn]] = defaultdict(list)
    by_memo: dict[tuple, list[Txn]] = defaultdict(list)
    for t in txns:
        base = (t.account, t.amount, t.counterparty.strip().lower())
        if t.num:
            by_num[(*base, t.num)].append(t)
        by_memo[(*base, t.memo.strip().lower())].append(t)
    groups.extend(g for g in by_num.values() if len(g) > 1)
    for g in by_memo.values():
        g = sorted(g, key=lambda t: (t.date, t.seq))
        cluster = [g[0]]
        for t in g[1:]:
            if (t.date - cluster[-1].date).days <= 7:
                cluster.append(t)
            else:
                if len(cluster) > 1:
                    groups.append(cluster)
                cluster = [t]
        if len(cluster) > 1:
            groups.append(cluster)
    return groups


def build_ledger(spec: DealSpec, accounts: dict[str, AccountInfo]) -> Ledger:
    b = _Builder(spec, accounts)
    for stream in spec.background:
        b.background(stream)
    b.planted()
    b.assign_numbers()
    ledger = Ledger(txns=b.txns)

    keys = [t.key for t in ledger.txns]
    dupes = sorted({k for k in keys if keys.count(k) > 1}) if len(keys) != len(set(keys)) else []
    if dupes:
        raise GenerationError(f"duplicate row keys: {dupes[:10]}")

    by_key = ledger.by_key()
    for dup in spec.data_quality.duplicates:
        orig = by_key.get(dup.of)
        if orig is None:
            raise GenerationError(f"data_quality.duplicates: no row with key {dup.of!r}")
        if dup.key in by_key:
            raise GenerationError(f"data_quality.duplicates: key {dup.key!r} already used")
        copy = replace(orig, key=dup.key, date=orig.date + timedelta(days=dup.days_later), origin="duplicate", seq=b.next_seq())
        ledger.txns.append(copy)
        ledger.duplicate_pairs.append((orig.key, dup.key))

    for mm in spec.data_quality.missing_gl_months:
        for t in ledger.txns:
            if t.month == mm.month and t.account not in mm.keep_accounts:
                t.in_gl = False

    for ts in spec.data_quality.topside:
        b.check_account(ts.account, "data_quality.topside")
        ledger.topside[(ts.month, ts.account)] = ledger.topside.get((ts.month, ts.account), ZERO) + q2(D(ts.amount))

    ledger.txns.sort(key=lambda t: (t.date, t.seq))
    _validate(spec, ledger)
    return ledger


def _validate(spec: DealSpec, ledger: Ledger) -> None:
    for t in ledger.txns:
        if not (spec.data_start <= t.month <= spec.data_end):
            raise GenerationError(f"row {t.key} dated {t.date} is outside {spec.data_start}..{spec.data_end}")
        for name in TEXT_FIELDS:
            value = getattr(t, name)
            if "\n" in value or "\r" in value:
                raise GenerationError(f"row {t.key}: newline in {name}")
        if t.amount == 0:
            raise GenerationError(f"row {t.key}: zero amount")
        if spec.gl_format == "xero_xlsx" and " - " in t.counterparty:
            raise GenerationError(f"row {t.key}: Xero contact names cannot contain ' - ' ({t.counterparty!r})")
    planted_dupes = {k for pair in ledger.duplicate_pairs for k in pair}
    for group in duplicate_groups(ledger.gl_txns()):
        if not any(t.key in planted_dupes for t in group):
            raise GenerationError(
                "unplanned duplicate GL rows (vary memo/amount or add a date to the memo): "
                + ", ".join(t.key for t in group)
            )


def pl_by_month(ledger: Ledger, accounts: dict[str, AccountInfo], include_topside: bool = True, gl_only: bool = False) -> dict[str, dict[str, Decimal]]:
    """account -> month -> debit-positive total."""
    out: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: ZERO))
    for t in ledger.txns:
        if gl_only and not t.in_gl:
            continue
        out[t.account][t.month] += t.amount
    if include_topside:
        for (month, account), amount in ledger.topside.items():
            out[account][month] += amount
    return {a: dict(m) for a, m in out.items()}


def ebitda_components(
    amounts: dict[str, dict[str, Decimal]], accounts: dict[str, AccountInfo], months: list[str]
) -> dict[str, Decimal]:
    """SPEC §6 EBITDA build over a set of months from debit-positive account totals."""
    wanted = set(months)
    comp = {k: ZERO for k in ("net_income", "interest", "taxes", "depreciation", "amortization")}
    for number, by_month in amounts.items():
        cls = accounts[number].ebitda_class
        total = sum((v for m, v in by_month.items() if m in wanted), ZERO)
        comp["net_income"] -= total
        if cls == EbitdaClass.INTEREST:
            comp["interest"] += total
        elif cls == EbitdaClass.TAXES:
            comp["taxes"] += total
        elif cls == EbitdaClass.DEPRECIATION:
            comp["depreciation"] += total
        elif cls == EbitdaClass.AMORTIZATION:
            comp["amortization"] += total
    comp["ebitda"] = comp["net_income"] + comp["interest"] + comp["taxes"] + comp["depreciation"] + comp["amortization"]
    return comp
