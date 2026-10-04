"""Turn raw downloads into analysis tables.

Outputs (data/tables/):
  games.parquet         one row per game (with pregame spread/total and overtime periods)
  player_games.parquet  one row per player per game (box score)
  props_raw.parquet     every priced prop outcome ESPN kept, one row per side per line per book
  prop_lines.parquet    the main over/under line per game x book x player x market, graded
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nbaprops import config
from nbaprops.ingest.boxscores import build_box_tables
from nbaprops.ingest.props import build_game_odds_table, build_props_table
from nbaprops.ingest.schedule import load_schedule

# Several ESPN provider ids are the same sportsbook in different states. Collapse them
# to one "book" so consensus and line shopping never count a book twice.
BOOK_FAMILY = {
    "31": "Caesars", "38": "Caesars", "43": "Caesars", "45": "Caesars", "52": "Caesars", "57": "Caesars",
    "40": "DraftKings", "100": "DraftKings",
    "47": "MGM",
    "41": "BetRivers",
    "48": "PointsBet",
    "58": "ESPN BET",
    "50": "Betfair",
    "36": "Unibet",
}


def american_to_decimal(odds: pd.Series | np.ndarray) -> np.ndarray:
    o = np.asarray(odds, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(o > 0, 1 + o / 100.0, 1 + 100.0 / np.abs(o))


def settle(actual: np.ndarray, line: np.ndarray, played: np.ndarray) -> np.ndarray:
    """'over' / 'under' / 'push', or 'void' when the player did not play (books refund these)."""
    out = np.full(len(actual), "void", dtype=object)
    ok = played & ~np.isnan(actual) & ~np.isnan(line)
    out[ok & (actual > line)] = "over"
    out[ok & (actual < line)] = "under"
    out[ok & (actual == line)] = "push"
    return out


def side_pnl(result: np.ndarray, decimal_price: np.ndarray, side: str) -> np.ndarray:
    """Profit of a 1-unit bet on `side`; NaN when the bet would be void or there was no price."""
    win = result == side
    lose = (result != side) & np.isin(result, ["over", "under"])
    pnl = np.full(len(result), np.nan)
    pnl[win] = decimal_price[win] - 1
    pnl[lose] = -1.0
    pnl[result == "push"] = 0.0
    pnl[np.isnan(decimal_price)] = np.nan
    return pnl


def _assign_sides(ou: pd.DataFrame) -> pd.DataFrame:
    """Give unlabeled items a side. Every book that labels sides lists Over first and Under
    right after it, so unlabeled items that share a line are read in that same order."""
    ou = ou.sort_values(["game_id", "book_id", "item_idx"]).copy()
    unl = ou["side"].isna()
    key = ["game_id", "book_id", "athlete_id", "market", "line_close"]
    pos = ou[unl].groupby(key, sort=False).cumcount()
    size = ou[unl].groupby(key, sort=False)["item_idx"].transform("size")
    side = np.where(pos % 2 == 0, "over", "under")
    side = np.where((size % 2 == 1) & (pos == size - 1), None, side)  # dangling one-sided alt line
    ou.loc[unl, "side"] = side
    ou["side_inferred"] = unl
    ou["pair_no"] = 0
    ou.loc[unl, "pair_no"] = (pos // 2).to_numpy()
    return ou[ou["side"].notna()]


def pair_main_lines(props: pd.DataFrame) -> pd.DataFrame:
    ou = props[(props["kind"] == "ou") & props["market"].isin(list(config.MARKET_FORMULAS)) & props["line_close"].notna()].copy()
    ou["book_family"] = ou["book_id"].map(BOOK_FAMILY).fillna(ou["book"])

    # Keep one provider id per book family per game (the one with the most prices).
    sizes = ou.groupby(["game_id", "book_family", "book_id"]).size().rename("n").reset_index()
    sizes = sizes.sort_values(["game_id", "book_family", "n"], ascending=[True, True, False]).drop_duplicates(["game_id", "book_family"])
    ou = ou.merge(sizes[["game_id", "book_id"]], on=["game_id", "book_id"], how="inner")

    # Labeled books also list one-sided alternates without a side; a prop that has a
    # labeled pair uses it and ignores those.
    prop_key = ["game_id", "book_id", "athlete_id", "market"]
    has_labeled = ou[ou["side"].notna()].groupby(prop_key).size().rename("n_labeled").reset_index()
    ou = ou.merge(has_labeled, on=prop_key, how="left")
    ou = ou[ou["side"].notna() | ou["n_labeled"].isna()].drop(columns="n_labeled")
    n_lines = ou.groupby(prop_key)["line_close"].nunique().rename("n_lines").reset_index()

    ou = _assign_sides(ou)
    pair_key = prop_key + ["line_close", "pair_no"]
    over = ou[ou["side"] == "over"].drop_duplicates(pair_key)
    under = ou[ou["side"] == "under"].drop_duplicates(pair_key)
    keep = ["game_id", "season", "book_id", "book", "book_family", "athlete_id", "market", "line_close", "pair_no"]
    pairs = over[keep + ["line_open", "odds_open", "odds_close", "side_inferred", "updated"]].merge(
        under[pair_key + ["odds_open", "odds_close", "line_open"]], on=pair_key, suffixes=("_over", "_under")
    )
    pairs = pairs.rename(
        columns={
            "odds_open_over": "over_open", "odds_close_over": "over_close",
            "odds_open_under": "under_open", "odds_close_under": "under_close",
            "line_open_over": "line_open",
        }
    )
    pairs = pairs[pairs["over_close"].notna() & pairs["under_close"].notna()]

    # If a book offered several two-sided lines, the main one is the most balanced.
    dec_o, dec_u = american_to_decimal(pairs["over_close"]), american_to_decimal(pairs["under_close"])
    p_o, p_u = 1 / dec_o, 1 / dec_u
    pairs["fair_over_close"] = p_o / (p_o + p_u)
    pairs["vig_close"] = p_o + p_u - 1
    pairs["_balance"] = (pairs["fair_over_close"] - 0.5).abs()
    pairs = pairs.sort_values(prop_key + ["_balance", "vig_close"]).drop_duplicates(prop_key)
    pairs = pairs.merge(n_lines, on=prop_key, how="left")
    # An opening line that differs from the opening line on the under side is a feed glitch.
    pairs.loc[pairs["line_open"] != pairs["line_open_under"], ["line_open", "over_open", "under_open"]] = np.nan
    return pairs.drop(columns=["_balance", "pair_no", "line_open_under"]).reset_index(drop=True)


def grade_lines(lines: pd.DataFrame, player_games: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    stat_cols = sorted({c for parts in config.MARKET_FORMULAS.values() for c in parts})
    pg = player_games[["game_id", "athlete_id", "played", "min", "starter", "team", "opp_team", "home"] + stat_cols]
    df = lines.merge(pg, on=["game_id", "athlete_id"], how="left")
    df["played"] = df["played"].fillna(False).astype(bool)
    actual = np.full(len(df), np.nan)
    for market, parts in config.MARKET_FORMULAS.items():
        m = (df["market"] == market).to_numpy()
        actual[m] = df.loc[m, list(parts)].sum(axis=1, min_count=len(parts)).to_numpy()
    df["actual"] = actual
    df = df.drop(columns=stat_cols)
    played = df["played"].to_numpy()
    df["result_close"] = settle(actual, df["line_close"].to_numpy(dtype=float), played)
    df["result_open"] = settle(actual, df["line_open"].to_numpy(dtype=float), played)
    for timing in ("open", "close"):
        res = df[f"result_{timing}"].to_numpy()
        for side in ("over", "under"):
            df[f"pnl_{side}_{timing}"] = side_pnl(res, american_to_decimal(df[f"{side}_{timing}"]), side)
    dec_o, dec_u = american_to_decimal(df["over_open"]), american_to_decimal(df["under_open"])
    df["fair_over_open"] = (1 / dec_o) / (1 / dec_o + 1 / dec_u)
    g = games[["game_id", "season_type", "game_date", "start_utc", "periods", "pregame_spread_home", "pregame_total"]]
    return df.merge(g, on="game_id", how="left")


def pregame_game_lines(odds: pd.DataFrame) -> pd.DataFrame:
    """Median closing spread (home side) and total across books for each game."""
    if odds.empty:
        return pd.DataFrame(columns=["game_id", "pregame_spread_home", "pregame_total"])
    o = odds.copy()
    spread = pd.to_numeric(o["spread"], errors="coerce").abs()
    fav = o["home_favorite"]
    o["home_spread"] = np.where(fav == True, -spread, np.where(fav == False, spread, pd.to_numeric(o["spread"], errors="coerce")))  # noqa: E712
    o["total"] = pd.to_numeric(o["total"], errors="coerce")
    g = o.groupby("game_id").agg(pregame_spread_home=("home_spread", "median"), pregame_total=("total", "median"))
    return g.reset_index()


def build_all() -> None:
    config.ensure_dirs()
    sched = load_schedule()
    print(f"[build] schedule: {len(sched)} games", flush=True)
    games, player_games = build_box_tables(sched)
    lines_from_odds = pregame_game_lines(build_game_odds_table())
    games = games.merge(lines_from_odds, on="game_id", how="left", suffixes=("", "_odds"))
    for col in ("pregame_spread_home", "pregame_total"):
        games[col] = pd.to_numeric(games[col], errors="coerce").fillna(games[f"{col}_odds"])
    games = games.drop(columns=["pregame_spread_home_odds", "pregame_total_odds"])
    games.to_parquet(config.TABLES / "games.parquet", index=False)
    player_games.to_parquet(config.TABLES / "player_games.parquet", index=False)
    print(f"[build] box scores: {len(games)} games, {len(player_games)} player rows", flush=True)

    props = build_props_table()
    props.to_parquet(config.TABLES / "props_raw.parquet", index=False)
    print(f"[build] raw props: {len(props)} priced outcomes", flush=True)

    lines = pair_main_lines(props)
    graded = grade_lines(lines, player_games, games)
    graded.to_parquet(config.TABLES / "prop_lines.parquet", index=False)
    summary = graded.groupby(["season", "book_family"]).agg(props=("market", "size"), games=("game_id", "nunique"))
    print(f"[build] main prop lines: {len(graded)}\n{summary}", flush=True)
