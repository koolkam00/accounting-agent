"""Per player x game x market features, using only information available before tip-off.

The "reference line" for a player-game-market is the median closing line across books.
"Previous game" always means the player's previous game *played* in the same season, so
a game without a posted line breaks a streak rather than being skipped over.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nbaprops import config
from nbaprops.build import settle

SINGLE_BOOK_PREFERENCE = ["DraftKings", "ESPN BET", "MGM", "Caesars", "BetRivers", "PointsBet"]


def _prior_window(values: pd.Series, groups: pd.Series, window: int | None, min_periods: int) -> tuple[pd.Series, pd.Series]:
    """Mean and SD of the previous `window` values within each group (all previous if None)."""
    v = values.astype(float)
    g = groups
    filled = v.fillna(0.0)
    has = v.notna().astype(float)
    cs, cs2, cn = filled.groupby(g).cumsum(), (filled**2).groupby(g).cumsum(), has.groupby(g).cumsum()
    prev = [x.groupby(g).shift(1).fillna(0.0) for x in (cs, cs2, cn)]
    if window is None:
        s, s2, n = prev
    else:
        old = [x.groupby(g).shift(window + 1).fillna(0.0) for x in (cs, cs2, cn)]
        s, s2, n = (p - o for p, o in zip(prev, old))
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = s / n
        var = (s2 - n * mean**2) / (n - 1)
    ok = n >= min_periods
    return mean.where(ok), np.sqrt(var.clip(lower=0)).where(ok & (n >= 2))


def signed_streak(sign: pd.Series, groups: pd.Series) -> pd.Series:
    """Run length of identical non-zero signs ending at each row (+k overs, -k unders, 0 breaks)."""
    s = sign.fillna(0).astype(int)
    change = (s != s.groupby(groups).shift(1)) | (groups != groups.shift(1))
    run_id = change.cumsum()
    length = s.groupby(run_id).cumcount() + 1
    return (length * s).where(s != 0, 0)


def consensus_lines(lines: pd.DataFrame, reference: str = "close") -> pd.DataFrame:
    """Median line across books. The reference line is the close where any book has a
    usable close, otherwise the opener (or always the opener with reference="open");
    the open-to-close move is measured book by book."""
    lines = lines.assign(_move=lines["line_close"] - lines["line_open"])
    g = lines.groupby(["game_id", "athlete_id", "market"], sort=False)
    cons = g.agg(
        ref_close=("line_close", "median"),
        ref_line_open=("line_open", "median"),
        fair_close=("fair_over_close", "mean"),
        fair_open=("fair_over_open", "mean"),
        ref_move=("_move", "median"),
        n_books=("book_family", "nunique"),
    ).reset_index()
    if reference == "open":
        cons["ref_close"] = np.nan
        cons["fair_close"] = np.nan
    cons["ref_is_close"] = cons["ref_close"].notna()
    cons["ref_line"] = cons["ref_close"].fillna(cons["ref_line_open"])
    cons["ref_fair_over"] = cons["fair_close"].fillna(cons["fair_open"])
    return cons.drop(columns=["ref_close", "fair_close", "fair_open"])


def player_features(player_games: pd.DataFrame, games: pd.DataFrame, cons: pd.DataFrame, market: str) -> pd.DataFrame:
    parts = list(config.MARKET_FORMULAS[market])
    pg = player_games[player_games["played"]].merge(
        games[["game_id", "periods", "pregame_spread_home", "pregame_total"]], on="game_id", how="left"
    )
    pg = pg.sort_values(["athlete_id", "start_utc", "game_id"]).reset_index(drop=True)
    pg["stat"] = pg[parts].sum(axis=1, min_count=len(parts))
    pg = pg.merge(cons[cons["market"] == market].drop(columns="market"), on=["game_id", "athlete_id"], how="left")
    grp = pg["athlete_id"].astype(str) + "|" + pg["season"].astype(str)

    pg["ref_result"] = settle(pg["stat"].to_numpy(float), pg["ref_line"].to_numpy(float), np.ones(len(pg), bool))
    pg.loc[pg["ref_line"].isna(), "ref_result"] = None
    sign = pg["ref_result"].map({"over": 1, "under": -1}).fillna(0)
    margin = pg["stat"] - pg["ref_line"]

    out = pd.DataFrame({"game_id": pg["game_id"], "athlete_id": pg["athlete_id"], "market": market})
    for col in ("season", "season_type", "game_date", "name", "team"):
        out[col] = pg[col]
    out["stat"] = pg["stat"]
    out["ref_result"] = pg["ref_result"]
    shift = lambda s: s.groupby(grp).shift(1)  # noqa: E731 - value from the previous game played
    out["games_prior"] = pg.groupby(grp).cumcount()
    out["prev_stat"] = shift(pg["stat"])
    out["prev_ref_line"] = shift(pg["ref_line"])
    out["prev_result"] = shift(pg["ref_result"])
    out["prev_margin"] = shift(margin)
    out["streak"] = shift(signed_streak(sign, grp)).fillna(0).astype(int)
    for w in (5, 10):
        out[f"avg{w}"], _ = _prior_window(pg["stat"], grp, w, w)
    out["avg_season"], _ = _prior_window(pg["stat"], grp, None, 5)
    _, out["sd20"] = _prior_window(pg["stat"], grp, 20, 8)
    out["sd20"] = out["sd20"].where(out["sd20"] > 0)
    out["prev_margin_z"] = out["prev_margin"] / out["sd20"]
    out["margin_z"] = margin / out["sd20"]
    for timing, col in (("close", "ref_line"), ("open", "ref_line_open")):
        out[f"line_delta_{timing}"] = pg[col] - out["prev_ref_line"]
        out[f"line_delta_z_{timing}"] = out[f"line_delta_{timing}"] / out["sd20"]
        for w in ("5", "10", "_season"):
            avg = out[f"avg{w}"]
            out[f"gap{w}_z_{timing}"] = (pg[col] - avg) / out["sd20"]
    # Minutes: was last game's playing time unusual compared with his average before it?
    min_avg10, _ = _prior_window(pg["min"], grp, 10, 5)
    out["prev_min"] = shift(pg["min"])
    out["prev_min_delta"] = out["prev_min"] - shift(min_avg10)
    out["prev_ot"] = shift(pd.to_numeric(pg["periods"], errors="coerce") > 4)
    out["prev_starter"] = shift(pg["starter"])
    dates = pd.to_datetime(pg["game_date"])
    out["rest_days"] = (dates - dates.groupby(grp).shift(1)).dt.days
    spread = pd.to_numeric(pg["pregame_spread_home"], errors="coerce")
    out["team_spread"] = np.where(pg["home"], spread, -spread)
    out["game_total"] = pd.to_numeric(pg["pregame_total"], errors="coerce")
    return out


def build_features(player_games: pd.DataFrame, games: pd.DataFrame, lines: pd.DataFrame, reference: str = "close") -> pd.DataFrame:
    cons = consensus_lines(lines, reference)
    player_games = player_games[player_games["season"].isin(lines["season"].unique())]
    feats = [player_features(player_games, games, cons, m) for m in sorted(lines["market"].unique())]
    return pd.concat(feats, ignore_index=True).merge(cons, on=["game_id", "athlete_id", "market"], how="left")


def bet_panel(lines: pd.DataFrame, mode: str) -> pd.DataFrame:
    """One bettable row per game x player x market, priced separately at the open and the close.

    single: every bet goes to one major book, the first in SINGLE_BOOK_PREFERENCE that has a
            usable line at that time (a book whose close was dropped can't take a closing bet).
    best:   line shopping. The over takes the lowest line on offer, the under the highest,
            and ties go to the better price.
    """
    key = ["game_id", "athlete_id", "market"]
    base_cols = key + ["season", "season_type", "game_date", "start_utc", "played", "actual", "home"]
    out = lines[base_cols].drop_duplicates(key).set_index(key)
    rank = lines["book_family"].map({b: i for i, b in enumerate(SINGLE_BOOK_PREFERENCE)}).fillna(len(SINGLE_BOOK_PREFERENCE))
    for t in ("open", "close"):
        ok = lines[f"over_{t}"].notna() & lines[f"under_{t}"].notna() & lines[f"line_{t}"].notna()
        avail = lines[ok].assign(_r=rank[ok])
        if mode == "single":
            sel = avail.sort_values(key + ["_r"]).drop_duplicates(key).set_index(key)
            for side in ("over", "under"):
                out[f"line_{side}_{t}"] = sel[f"line_{t}"]
                out[f"odds_{side}_{t}"] = sel[f"{side}_{t}"]
                out[f"pnl_{side}_{t}"] = sel[f"pnl_{side}_{t}"]
                out[f"book_{side}_{t}"] = sel["book_family"]
            continue
        for side, line_ascending in (("over", True), ("under", False)):
            price = avail[f"{side}_{t}"]
            dec = np.where(price > 0, 1 + price / 100, 1 + 100 / price.abs())
            best = (
                avail.assign(_dec=dec)
                .sort_values(key + [f"line_{t}", "_dec"], ascending=[True, True, True, line_ascending, False])
                .drop_duplicates(key)
                .set_index(key)
            )
            out[f"line_{side}_{t}"] = best[f"line_{t}"]
            out[f"odds_{side}_{t}"] = best[f"{side}_{t}"]
            out[f"pnl_{side}_{t}"] = best[f"pnl_{side}_{t}"]
            out[f"book_{side}_{t}"] = best["book_family"]
    return out.reset_index()
