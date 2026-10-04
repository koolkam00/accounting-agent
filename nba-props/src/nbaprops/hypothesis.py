"""Direct statistical tests of the thesis: does an over make an under more likely next game?

All tests use one row per player-game-market, graded against the consensus (median)
closing line across books, so a prop posted at five books still counts once.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from nbaprops import config

BREAKEVEN_110 = 110 / 210  # win rate needed at -110 on both sides


def _ols_cluster(y: np.ndarray, X: np.ndarray, groups: np.ndarray):
    model = sm.OLS(y, sm.add_constant(X, has_constant="add"))
    return model.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})


def thesis_table(f: pd.DataFrame) -> pd.DataFrame:
    """Per market: base rates, conditional rates, and a player-clustered test of the difference."""
    rows = []
    for market in config.ALL_MARKETS:
        d = f[(f["market"] == market) & f["ref_result"].isin(["over", "under"])]
        if d.empty:
            continue
        cond = d[d["prev_result"].isin(["over", "under"])]
        under = (cond["ref_result"] == "under").to_numpy(float)
        prev_over = (cond["prev_result"] == "over").to_numpy(float)
        fit = _ols_cluster(under, prev_over, cond["athlete_id"].to_numpy())
        after_over = cond[cond["prev_result"] == "over"]
        after_under = cond[cond["prev_result"] == "under"]
        k = int((after_over["ref_result"] == "under").sum())
        n = len(after_over)
        mz = cond[["margin_z", "prev_margin_z"]].dropna()
        rows.append(
            {
                "market": market,
                "graded_props": len(d),
                "p_over": float((d["ref_result"] == "over").mean()),
                "p_under": float((d["ref_result"] == "under").mean()),
                "n_after_over": n,
                "p_under_after_over": k / n if n else np.nan,
                "n_after_under": len(after_under),
                "p_over_after_under": float((after_under["ref_result"] == "over").mean()) if len(after_under) else np.nan,
                # Effect of the previous result on P(under): positive = reversal, negative = momentum.
                "reversal_effect": float(fit.params[1]),
                "reversal_effect_se": float(fit.bse[1]),
                "reversal_p_value": float(fit.pvalues[1]),
                "p_beats_breakeven": float(stats.binomtest(k, n, BREAKEVEN_110, alternative="greater").pvalue) if n else np.nan,
                "residual_autocorr": float(np.corrcoef(mz["margin_z"], mz["prev_margin_z"])[0, 1]) if len(mz) > 2 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def streak_table(f: pd.DataFrame, max_k: int = 6) -> pd.DataFrame:
    d = f[f["ref_result"].isin(["over", "under"])]
    rows = []
    for market in config.ALL_MARKETS:
        dm = d[d["market"] == market]
        for k in range(1, max_k + 1):
            sel_o = dm["streak"] >= k if k == max_k else dm["streak"] == k
            sel_u = dm["streak"] <= -k if k == max_k else dm["streak"] == -k
            rows.append(
                {
                    "market": market,
                    "streak": f"{k}+" if k == max_k else str(k),
                    "n_after_over_streak": int(sel_o.sum()),
                    "p_under_after_over_streak": float((dm.loc[sel_o, "ref_result"] == "under").mean()) if sel_o.any() else np.nan,
                    "n_after_under_streak": int(sel_u.sum()),
                    "p_over_after_under_streak": float((dm.loc[sel_u, "ref_result"] == "over").mean()) if sel_u.any() else np.nan,
                }
            )
    return pd.DataFrame(rows)


def margin_table(f: pd.DataFrame) -> pd.DataFrame:
    """P(over next game) by how far the last game finished from its line, in player SDs."""
    d = f[f["ref_result"].isin(["over", "under"]) & f["prev_margin_z"].notna()].copy()
    bins = [-np.inf, -2, -1, -0.5, 0, 0.5, 1, 2, np.inf]
    labels = ["<-2", "-2..-1", "-1..-0.5", "-0.5..0", "0..0.5", "0.5..1", "1..2", ">2"]
    d["bucket"] = pd.cut(d["prev_margin_z"], bins=bins, labels=labels)
    g = d.groupby(["market", "bucket"], observed=True)
    out = g.agg(n=("ref_result", "size"), p_over_next=("ref_result", lambda s: (s == "over").mean())).reset_index()
    return out


def adjustment_table(f: pd.DataFrame) -> pd.DataFrame:
    """How books move the next line after a surprise, and whether that move over- or under-shoots.

    line_move_per_sd: SDs the consensus line moves per SD the player beat his last line by.
    next_margin_per_sd: SDs the next result lands above its line per SD of last surprise.
      ~0 means the books adjust correctly; < 0 means they overreact (supports the thesis);
      > 0 means they underreact (momentum).
    """
    rows = []
    for market in config.ALL_MARKETS:
        d = f[(f["market"] == market)][["prev_margin_z", "margin_z", "line_delta_z_close", "athlete_id"]].dropna()
        d = d[(d["prev_margin_z"].abs() < 6) & (d["margin_z"].abs() < 6)]
        if len(d) < 100:
            continue
        a = _ols_cluster(d["line_delta_z_close"].to_numpy(), d["prev_margin_z"].to_numpy(), d["athlete_id"].to_numpy())
        b = _ols_cluster(d["margin_z"].to_numpy(), d["prev_margin_z"].to_numpy(), d["athlete_id"].to_numpy())
        rows.append(
            {
                "market": market,
                "n": len(d),
                "line_move_per_sd": float(a.params[1]),
                "line_move_se": float(a.bse[1]),
                "next_margin_per_sd": float(b.params[1]),
                "next_margin_se": float(b.bse[1]),
                "next_margin_p_value": float(b.pvalues[1]),
            }
        )
    return pd.DataFrame(rows)


def season_table(f: pd.DataFrame) -> pd.DataFrame:
    d = f[f["ref_result"].isin(["over", "under"]) & f["prev_result"].isin(["over", "under"])]
    g = d.groupby(["market", "season"])
    return g.apply(
        lambda x: pd.Series(
            {
                "n": len(x),
                "p_under": (x["ref_result"] == "under").mean(),
                "p_under_after_over": (x.loc[x["prev_result"] == "over", "ref_result"] == "under").mean(),
                "p_over_after_under": (x.loc[x["prev_result"] == "under", "ref_result"] == "over").mean(),
            }
        ),
        include_groups=False,
    ).reset_index()


def naive_line_history(player_games: pd.DataFrame, window: int = 10, seed: int = 11) -> pd.DataFrame:
    """Every season since 2002-03, with the player's trailing average standing in for a line.

    No book sets lines this naively, so this is not a betting test. It shows whether the raw
    stats themselves alternate above/below normal. A placebo that shuffles game order within
    each player-season removes any real game-to-game pattern; real minus placebo is the
    serial dependence, net of the small mechanical effect of the average including the last game.
    """
    pg = player_games[player_games["played"] & player_games["season_type"].isin([2, 3])].copy()
    pg = pg.sort_values(["athlete_id", "start_utc"])
    rng = np.random.default_rng(seed)
    pg["_shuffle"] = rng.random(len(pg))
    rows = []
    for market in config.CORE_MARKETS:
        for placebo in (False, True):
            d = pg.sort_values(["athlete_id", "season", "_shuffle"]) if placebo else pg
            grp = d["athlete_id"].astype(str) + "|" + d["season"].astype(str)
            stat = d[market].astype(float)
            prior = stat.groupby(grp).transform(lambda s: s.shift(1).rolling(window, min_periods=window).mean())
            above = np.sign(stat - prior)
            prev = above.groupby(grp).shift(1)
            t = pd.DataFrame({"season": d["season"], "above": above, "prev": prev}).dropna()
            t = t[(t["above"] != 0) & (t["prev"] != 0)]
            for season, x in t.groupby("season"):
                rows.append(
                    {
                        "market": market,
                        "season": int(season),
                        "placebo": placebo,
                        "n": len(x),
                        "p_below": float((x["above"] < 0).mean()),
                        "p_below_after_above": float((x.loc[x["prev"] > 0, "above"] < 0).mean()),
                        "p_above_after_below": float((x.loc[x["prev"] < 0, "above"] > 0).mean()),
                    }
                )
    return pd.DataFrame(rows)


def data_quality(lines: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Checks that the feed means what we think: closing lines beat openers, and inferred
    over/under labels are calibrated (a flipped label would show a negative slope)."""
    d = lines[lines["result_close"].isin(["over", "under"])].copy()
    acc = (
        d.assign(err_open=(d["actual"] - d["line_open"]).abs(), err_close=(d["actual"] - d["line_close"]).abs(), moved=d["line_open"] != d["line_close"])
        .groupby(["season", "book_family"])
        .agg(props=("actual", "size"), mae_open=("err_open", "mean"), mae_close=("err_close", "mean"), share_line_moved=("moved", "mean"))
        .reset_index()
    )
    calib_rows = []
    for inferred, x in d.groupby("side_inferred"):
        x = x.dropna(subset=["fair_over_close"])
        y = (x["result_close"] == "over").astype(float)
        fit = sm.OLS(y.to_numpy(), sm.add_constant(x["fair_over_close"].to_numpy())).fit()
        calib_rows.append(
            {
                "sides": "inferred from feed order" if inferred else "labeled by the feed",
                "props": len(x),
                "calibration_slope": float(fit.params[1]),
                "slope_se": float(fit.bse[1]),
                "mean_fair_over": float(x["fair_over_close"].mean()),
                "actual_over_rate": float(y.mean()),
            }
        )
    return {"line_accuracy": acc, "side_calibration": pd.DataFrame(calib_rows)}
