"""Strategy grid, flat-stake backtests at real prices, and honest out-of-sample evaluation.

Every strategy bets 1 unit per selected prop at the real price for the chosen side, at the
opening or closing line, using either one major book or the best line across books.
Pushes return the stake; props for players who sat out are void (refunded), as at the books.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd

from nbaprops import config

MARKET_GROUPS: dict[str, list[str]] = {m: [m] for m in config.ALL_MARKETS}
MARKET_GROUPS["core5"] = config.CORE_MARKETS
MARKET_GROUPS["all"] = config.ALL_MARKETS


def to_decimal(odds) -> np.ndarray:
    o = np.asarray(odds, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(o > 0, 1 + o / 100.0, 1 + 100.0 / np.abs(o))


def decimal_to_american(d: float) -> float:
    if not np.isfinite(d) or d <= 1:
        return np.nan
    return (d - 1) * 100 if d >= 2 else -100 / (d - 1)


@dataclass
class Signal:
    family: str
    variant: str
    params: str
    mask: np.ndarray
    bet_over: np.ndarray


def _fmt(**kw) -> str:
    return ",".join(f"{k}={v}" for k, v in kw.items())


def panel_arrays(df: pd.DataFrame, timing: str, line_q: dict[str, tuple[float, float]]) -> dict[str, np.ndarray]:
    a: dict[str, np.ndarray] = {}
    a["pnl_over"] = df[f"pnl_over_{timing}"].to_numpy(float)
    a["pnl_under"] = df[f"pnl_under_{timing}"].to_numpy(float)
    a["dec_over"] = to_decimal(df[f"odds_over_{timing}"])
    a["dec_under"] = to_decimal(df[f"odds_under_{timing}"])
    a["streak"] = df["streak"].to_numpy(int)
    a["mz"] = df["prev_margin_z"].to_numpy(float)
    a["ld"] = df[f"line_delta_z_{timing}"].to_numpy(float)
    for w in ("5", "10", "_season"):
        a[f"gap{w}"] = df[f"gap{w}_z_{timing}"].to_numpy(float)
    a["move"] = df["ref_move"].to_numpy(float)
    a["rest"] = df["rest_days"].to_numpy(float)
    a["home"] = df["home"].fillna(False).to_numpy(bool)
    a["prev_ot"] = df["prev_ot"].fillna(False).to_numpy(bool)
    a["prev_min_delta"] = df["prev_min_delta"].to_numpy(float)
    a["prev_starter"] = df["prev_starter"].fillna(False).to_numpy(bool)
    a["prev_known"] = df["prev_starter"].notna().to_numpy(bool)
    a["season_type"] = df["season_type"].to_numpy(int)
    a["abs_spread"] = np.abs(df["team_spread"].to_numpy(float))
    a["game_total"] = df["game_total"].to_numpy(float)
    a["games_prior"] = df["games_prior"].to_numpy(float)
    lo = df["market"].map(lambda m: line_q[m][0]).to_numpy(float)
    hi = df["market"].map(lambda m: line_q[m][1]).to_numpy(float)
    a["line_low"] = df["ref_line"].to_numpy(float) <= lo
    a["line_high"] = df["ref_line"].to_numpy(float) >= hi
    return a


def iter_signals(a: dict[str, np.ndarray], timing: str) -> Iterator[Signal]:
    n = len(a["pnl_over"])
    every, yes, no = np.ones(n, bool), np.ones(n, bool), np.zeros(n, bool)
    streak, mz = a["streak"], a["mz"]

    # Baselines: bet every over, or every under.
    yield Signal("baseline", "all_overs", "", every, yes)
    yield Signal("baseline", "all_unders", "", every, no)

    # The thesis (reversal) and its opposite (momentum): after k straight overs (unders),
    # optionally only when the last game beat the line by at least z standard deviations.
    for k in (1, 2, 3, 4, 5):
        for z in (0.0, 0.5, 1.0, 1.5, 2.0):
            after_over = streak >= k
            after_under = streak <= -k
            if z > 0:
                after_over = after_over & (mz >= z)
                after_under = after_under & (mz <= -z)
            for direction, m in (("both", after_over | after_under), ("after_overs", after_over), ("after_unders", after_under)):
                yield Signal("reversal", direction, _fmt(streak=k, margin_z=z), m, after_under)
                yield Signal("momentum", direction, _fmt(streak=k, margin_z=z), m, after_over)

    # How far the book moved this game's line from the last game's line (in player SDs).
    for x in (0.25, 0.5, 1.0):
        up, down = a["ld"] >= x, a["ld"] <= -x
        yield Signal("line_adjust", "fade", _fmt(z=x), up | down, down)
        yield Signal("line_adjust", "follow", _fmt(z=x), up | down, up)

    # Line far above/below the player's recent average: does the book overreact?
    for w in ("5", "10", "_season"):
        gap = a[f"gap{w}"]
        for x in (0.25, 0.5, 0.75, 1.0):
            hi, lo = gap >= x, gap <= -x
            label = w.strip("_")
            yield Signal("line_vs_avg", "fade", _fmt(window=label, z=x), hi | lo, lo)
            yield Signal("line_vs_avg", "follow", _fmt(window=label, z=x), hi | lo, hi)

    # Open -> close line movement is only known when betting at the close.
    if timing == "close":
        for x in (0.5, 1.0, 2.0):
            up, down = a["move"] >= x, a["move"] <= -x
            yield Signal("steam", "follow", _fmt(move=x), up | down, up)
            yield Signal("steam", "fade", _fmt(move=x), up | down, down)

    # Price-based: plus-money sides vs heavily juiced sides.
    for th in (2.0, 2.2):
        yield Signal("price", "plus_money_over", _fmt(min_decimal=th), a["dec_over"] >= th, yes)
        yield Signal("price", "plus_money_under", _fmt(min_decimal=th), a["dec_under"] >= th, no)
    for th in (1.67, 1.54):
        yield Signal("price", "juiced_over", _fmt(max_decimal=th), a["dec_over"] <= th, yes)
        yield Signal("price", "juiced_under", _fmt(max_decimal=th), a["dec_under"] <= th, no)

    # Context filters on top of the simplest versions of each idea.
    filters = {
        "back_to_back": a["rest"] == 1,
        "rested_3plus": a["rest"] >= 3,
        "home": a["home"],
        "away": ~a["home"],
        "prev_overtime": a["prev_ot"],
        "prev_minutes_spike": a["prev_min_delta"] >= 6,
        "prev_minutes_drop": a["prev_min_delta"] <= -6,
        "prev_starter": a["prev_known"] & a["prev_starter"],
        "prev_bench": a["prev_known"] & ~a["prev_starter"],
        "playoffs": a["season_type"] == 3,
        "regular_season": a["season_type"] == 2,
        "low_line": a["line_low"],
        "high_line": a["line_high"],
        "big_spread": a["abs_spread"] >= 10,
        "high_total": a["game_total"] >= 232,
        "low_total": a["game_total"] <= 220,
        "early_season": a["games_prior"] < 15,
        "late_season": a["games_prior"] >= 50,
    }
    bases = {
        "all_unders": (every, no),
        "all_overs": (every, yes),
        "reversal_after_over": (streak >= 1, no),
        "reversal_after_under": (streak <= -1, yes),
        "momentum_after_over": (streak >= 1, yes),
        "momentum_after_under": (streak <= -1, no),
    }
    for fname, f in filters.items():
        for bname, (m, side) in bases.items():
            yield Signal("context", f"{bname}|{fname}", "", m & f, side)


@dataclass
class GridResult:
    table: pd.DataFrame
    day_pnl: np.ndarray  # strategies x days
    day_n: np.ndarray
    days: np.ndarray  # date strings, aligned with the day axis
    day_season: np.ndarray
    seasons: list[int]


def clustered_t(day_p: np.ndarray, day_n: np.ndarray) -> tuple[float, float, float]:
    """ROI, its standard error clustered by game day, and the t statistic."""
    n = day_n.sum()
    if n == 0:
        return np.nan, np.nan, np.nan
    roi = day_p.sum() / n
    active = day_n > 0
    d = active.sum()
    if d < 2:
        return roi, np.nan, np.nan
    resid = day_p[active] - roi * day_n[active]
    se = np.sqrt((resid**2).sum() * d / (d - 1)) / n
    return roi, se, roi / se if se > 0 else np.nan


def run_grid(panels: dict[str, pd.DataFrame], holdout: int, line_q: dict[str, tuple[float, float]]) -> GridResult:
    all_days = np.array(sorted(set().union(*[set(p["game_date"].unique()) for p in panels.values()])))
    day_index = {d: i for i, d in enumerate(all_days)}
    seasons = sorted(set().union(*[set(p["season"].unique()) for p in panels.values()]))
    season_index = {s: i for i, s in enumerate(seasons)}
    day_season = np.zeros(len(all_days), dtype=int)
    for p in panels.values():
        day_season[p["game_date"].map(day_index).to_numpy()] = p["season"].to_numpy()

    rows, day_ps, day_ns = [], [], []
    D, S = len(all_days), len(seasons)
    train_days = day_season < holdout
    for mode, panel in panels.items():
        for group, markets in MARKET_GROUPS.items():
            sub = panel[panel["market"].isin(markets)]
            if sub.empty:
                continue
            day = sub["game_date"].map(day_index).to_numpy()
            sidx = sub["season"].map(season_index).to_numpy()
            for timing in ("open", "close"):
                a = panel_arrays(sub, timing, line_q)
                for sig in iter_signals(a, timing):
                    pnl = np.where(sig.bet_over, a["pnl_over"], a["pnl_under"])
                    dec = np.where(sig.bet_over, a["dec_over"], a["dec_under"])
                    m = sig.mask & ~np.isnan(pnl)
                    p = pnl[m]
                    if len(p) == 0:
                        continue
                    dp = np.bincount(day[m], weights=p, minlength=D)
                    dn = np.bincount(day[m], minlength=D).astype(float)
                    sp = np.bincount(sidx[m], weights=p, minlength=S)
                    sn = np.bincount(sidx[m], minlength=S)
                    roi, se, t = clustered_t(dp, dn)
                    tr_roi, _, tr_t = clustered_t(dp[train_days], dn[train_days])
                    te_roi, _, te_t = clustered_t(dp[~train_days], dn[~train_days])
                    wins, losses = int((p > 0).sum()), int((p < 0).sum())
                    row = {
                        "family": sig.family,
                        "variant": sig.variant,
                        "params": sig.params,
                        "market": group,
                        "timing": timing,
                        "book_mode": mode,
                        "bets": int(len(p)),
                        "wins": wins,
                        "losses": losses,
                        "pushes": int(len(p)) - wins - losses,
                        "hit_rate": wins / max(wins + losses, 1),
                        "avg_odds": decimal_to_american(float(np.mean(dec[m]))),
                        "breakeven": float(np.mean(1 / dec[m])),
                        "units": float(p.sum()),
                        "roi": roi,
                        "roi_se": se,
                        "t": t,
                        "train_bets": int(dn[train_days].sum()),
                        "train_roi": tr_roi,
                        "train_t": tr_t,
                        "test_bets": int(dn[~train_days].sum()),
                        "test_roi": te_roi,
                        "test_t": te_t,
                    }
                    for s, i in season_index.items():
                        row[f"bets_{s}"] = int(sn[i])
                        row[f"roi_{s}"] = sp[i] / sn[i] if sn[i] else np.nan
                    rows.append(row)
                    day_ps.append(dp.astype(np.float32))
                    day_ns.append(dn.astype(np.float32))
    table = pd.DataFrame(rows)
    table.insert(0, "strategy_id", np.arange(len(table)))
    return GridResult(table, np.vstack(day_ps), np.vstack(day_ns), all_days, day_season, seasons)


_BASES = {
    "all_unders": "Every under",
    "all_overs": "Every over",
    "reversal_after_over": "Under after an over",
    "reversal_after_under": "Over after an under",
    "momentum_after_over": "Over after an over",
    "momentum_after_under": "Under after an under",
}
_FILTERS = {
    "back_to_back": "on a back-to-back",
    "rested_3plus": "with 3+ days of rest",
    "home": "at home",
    "away": "on the road",
    "prev_overtime": "after an overtime game",
    "prev_minutes_spike": "after a minutes spike (6+ over his average)",
    "prev_minutes_drop": "after a minutes drop (6+ under his average)",
    "prev_starter": "if he started last game",
    "prev_bench": "if he came off the bench last game",
    "playoffs": "in the playoffs",
    "regular_season": "in the regular season",
    "low_line": "on low lines (bottom third)",
    "high_line": "on high lines (top third)",
    "big_spread": "when the spread is 10+",
    "high_total": "when the game total is 232+",
    "low_total": "when the game total is 220 or less",
    "early_season": "in his first 15 games",
    "late_season": "after his 50th game",
}


def describe(family: str, variant: str, params: str) -> str:
    """Plain-English name for a strategy."""
    kv = dict(x.split("=") for x in params.split(",")) if params else {}
    if family == "baseline":
        return _BASES[variant]
    if family in ("reversal", "momentum"):
        k, z = int(kv["streak"]), float(kv["margin_z"])
        run = "an over" if k == 1 else f"{k}+ straight overs"
        run_u = "an under" if k == 1 else f"{k}+ straight unders"
        size = f", last miss {z:g}+ SD" if z > 0 else ""
        if family == "reversal":
            both = "Opposite of last game's result" if k == 1 else f"Against a {k}+ game streak"
            parts = {"after_overs": f"Under after {run}", "after_unders": f"Over after {run_u}", "both": both}
        else:
            both = "Same as last game's result" if k == 1 else f"With a {k}+ game streak"
            parts = {"after_overs": f"Over after {run}", "after_unders": f"Under after {run_u}", "both": both}
        return parts[variant] + size
    if family == "line_adjust":
        return f"{variant.title()} a line move of {kv['z']}+ SD from last game"
    if family == "line_vs_avg":
        window = {"5": "5-game", "10": "10-game", "season": "season"}[kv["window"]]
        return f"{variant.title()} a line {kv['z']}+ SD from his {window} average"
    if family == "steam":
        return f"{variant.title()} an open-to-close move of {kv['move']}+"
    if family == "price":
        th = float(kv.get("min_decimal", kv.get("max_decimal", "nan")))
        odds = f"+{(th - 1) * 100:.0f}" if th >= 2 else f"−{100 / (th - 1):.0f}"
        side = "overs" if variant.endswith("over") else "unders"
        return f"Plus-money {side} ({odds} or longer)" if variant.startswith("plus") else f"Juiced {side} ({odds} or shorter)"
    if family == "context":
        base, filt = variant.split("|")
        return f"{_BASES[base]} {_FILTERS[filt]}"
    return f"{family}:{variant} {params}"


def strategy_label(r: pd.Series) -> str:
    market = config.MARKET_LABELS.get(r["market"], {"core5": "Core 5 stats", "all": "All prop markets"}.get(r["market"], r["market"]))
    timing = "opening line" if r["timing"] == "open" else "closing line"
    book = "best line" if r["book_mode"] == "best" else "single book"
    return f"{describe(r['family'], r['variant'], r['params'])} · {market} · {timing} · {book}"


def bh_fdr(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    """Benjamini-Hochberg: which hypotheses are discoveries at false discovery rate q."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    passed = np.zeros(len(p), bool)
    below = np.nonzero(ranked <= q)[0]
    if len(below):
        passed[order[: below.max() + 1]] = True
    return passed


def reality_check(day_pnl: np.ndarray, day_n: np.ndarray, cols: np.ndarray, rows: np.ndarray, n_boot: int = 1000, seed: int = 7) -> dict:
    """White's Reality Check (studentized, iid bootstrap over game days).

    Answers: after trying every strategy in `rows`, is the best ROI better than what the
    luckiest of that many zero-edge strategies would show? Uses only the days in `cols`.
    """
    P = day_pnl[np.ix_(rows, cols)].astype(np.float64)
    N = day_n[np.ix_(rows, cols)].astype(np.float64)
    tot_n = N.sum(axis=1)
    roi = P.sum(axis=1) / tot_n
    resid = P - roi[:, None] * N
    d = P.shape[1]
    se = np.sqrt((resid**2).sum(axis=1) * d / (d - 1)) / tot_n
    t_obs = roi / se
    rng = np.random.default_rng(seed)
    max_t = np.empty(n_boot)
    for b in range(n_boot):
        w = rng.multinomial(d, np.full(d, 1.0 / d)).astype(np.float64)
        with np.errstate(invalid="ignore", divide="ignore"):
            roi_b = (P @ w) / (N @ w)  # a strategy with no bets in a resample drops out
        max_t[b] = np.nanmax((roi_b - roi) / se)
    best = int(np.nanargmax(t_obs))
    return {
        "n_strategies": int(len(rows)),
        "best_row": int(rows[best]),
        "best_t": float(t_obs[best]),
        "best_roi": float(roi[best]),
        "p_value": float((max_t >= t_obs[best]).mean()),
        "null_max_t_95": float(np.quantile(max_t, 0.95)),
    }


def walk_forward(grid: GridResult, min_train_bets: int = 300, top_k: int = 10, min_test_bets: int = 30) -> pd.DataFrame:
    """For each season, pick strategies using only earlier seasons, then score them on that season.

    Candidates must also have bets in the scored season: a strategy can have none when the
    feed has no usable lines of its kind that season (ESPN BET's 2024-25 openers, say).
    """
    t = grid.table
    out = []
    for i, test in enumerate(grid.seasons):
        train = grid.seasons[:i]
        if not train:
            continue
        tr_cols = np.isin(grid.day_season, train)
        te_cols = grid.day_season == test
        tr_n = grid.day_n[:, tr_cols].sum(axis=1)
        tr_p = grid.day_pnl[:, tr_cols].sum(axis=1)
        te_n = grid.day_n[:, te_cols].sum(axis=1)
        te_p = grid.day_pnl[:, te_cols].sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            tr_roi = np.where((tr_n >= min_train_bets) & (te_n >= min_test_bets), tr_p / tr_n, -np.inf)
        for rule in ("best_train_roi", "best_train_t"):
            if rule == "best_train_roi":
                score = tr_roi
            else:
                score = np.full(len(t), -np.inf)
                for j in np.nonzero(np.isfinite(tr_roi))[0]:
                    score[j] = clustered_t(grid.day_pnl[j, tr_cols], grid.day_n[j, tr_cols])[2]
                score = np.nan_to_num(score, nan=-np.inf)
            picks = np.argsort(-score)[:top_k]
            picks = picks[np.isfinite(score[picks])]
            top1 = picks[0]
            out.append(
                {
                    "test_season": test,
                    "train_seasons": f"{train[0]}-{train[-1]}",
                    "rule": rule,
                    "pick": strategy_label(t.iloc[top1]),
                    "pick_train_roi": tr_p[top1] / tr_n[top1],
                    "pick_train_bets": int(tr_n[top1]),
                    "pick_test_roi": te_p[top1] / te_n[top1] if te_n[top1] else np.nan,
                    "pick_test_bets": int(te_n[top1]),
                    f"top{top_k}_test_roi": te_p[picks].sum() / te_n[picks].sum() if te_n[picks].sum() else np.nan,
                    f"top{top_k}_test_bets": int(te_n[picks].sum()),
                }
            )
    return pd.DataFrame(out)
