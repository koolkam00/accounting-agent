"""Run every test and backtest, and write the results to reports/."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from nbaprops import config
from nbaprops.backtest import bh_fdr, reality_check, run_grid, strategy_label, walk_forward
from nbaprops.features import bet_panel, build_features
from nbaprops import hypothesis as hyp

MIN_TRAIN_BETS = 300
MIN_SEASON_GAMES = 100


def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    games = pd.read_parquet(config.TABLES / "games.parquet")
    player_games = pd.read_parquet(config.TABLES / "player_games.parquet")
    lines = pd.read_parquet(config.TABLES / "prop_lines.parquet")
    return games, player_games, lines


def coverage_table(lines: pd.DataFrame) -> pd.DataFrame:
    g = lines.groupby(["season", "book_family"]).agg(games=("game_id", "nunique"), props=("market", "size"))
    return g.reset_index()


def run_analysis(holdout_season: int | None = None) -> dict:
    config.ensure_dirs()
    out = config.REPORTS
    games, player_games, lines = _load()
    lines = lines[lines["season_type"].isin(list(config.SEASON_TYPES))]
    # A season needs real coverage to be scored on its own (2021-22 has props for only
    # a handful of Finals-round games).
    games_per_season = lines.groupby("season")["game_id"].nunique()
    lines = lines[lines["season"].isin(games_per_season[games_per_season >= MIN_SEASON_GAMES].index)]
    seasons = sorted(lines["season"].unique())
    holdout = holdout_season or int(seasons[-1])
    print(f"[analyze] prop seasons {seasons}, holdout {holdout}", flush=True)

    feats = build_features(player_games, games, lines)
    feats.to_parquet(config.TABLES / "features.parquet", index=False)

    # 1) Direct tests of the thesis.
    thesis = hyp.thesis_table(feats)
    streaks = hyp.streak_table(feats)
    margins = hyp.margin_table(feats)
    adjust = hyp.adjustment_table(feats)
    by_season = hyp.season_table(feats)
    history = hyp.naive_line_history(player_games)
    quality = hyp.data_quality(lines)
    # Robustness: the same direct test against the consensus opening line only.
    thesis_open = hyp.thesis_table(build_features(player_games, games, lines, reference="open"))
    coverage = coverage_table(lines)
    line_quality = pd.read_parquet(config.TABLES / "line_quality.parquet")
    line_quality = line_quality[line_quality["season"].isin(seasons)]
    for name, df in {
        "thesis_by_market": thesis,
        "thesis_by_market_vs_open": thesis_open,
        "streaks": streaks,
        "margin_buckets": margins,
        "book_adjustment": adjust,
        "thesis_by_season": by_season,
        "naive_line_history": history,
        "line_accuracy": quality["line_accuracy"],
        "side_calibration": quality["side_calibration"],
        "coverage": coverage,
        "line_quality": line_quality,
    }.items():
        df.to_csv(out / f"{name}.csv", index=False)
    print(thesis.round(4).to_string(), flush=True)

    # 2) Strategy grid at real prices.
    key = ["game_id", "athlete_id", "market"]
    panels = {}
    for mode in ("single", "best"):
        panel = bet_panel(lines, mode)
        extra = [c for c in feats.columns if c not in panel.columns or c in key]
        panels[mode] = panel.merge(feats[extra], on=key, how="inner")
    train_feats = feats[feats["season"] < holdout]
    line_q = {m: tuple(train_feats.loc[train_feats["market"] == m, "ref_line"].quantile([1 / 3, 2 / 3])) for m in config.ALL_MARKETS if (feats["market"] == m).any()}
    streak_roi = pd.concat([hyp.streak_roi_table(panels["single"], t) for t in ("close", "open")], ignore_index=True)
    streak_roi.to_csv(out / "streak_roi.csv", index=False)
    grid = run_grid(panels, holdout, line_q)
    table = grid.table
    table["label"] = table.apply(strategy_label, axis=1)
    table["train_p"] = 1 - stats.norm.cdf(table["train_t"].fillna(-np.inf))
    eligible = (table["train_bets"] >= MIN_TRAIN_BETS).to_numpy()
    table["fdr_discovery_train"] = False
    table.loc[eligible, "fdr_discovery_train"] = bh_fdr(table.loc[eligible, "train_p"].to_numpy(), q=0.10)
    table.to_csv(out / "strategy_results.csv", index=False)

    train_cols = np.nonzero(grid.day_season < holdout)[0]
    rc = reality_check(grid.day_pnl, grid.day_n, train_cols, np.nonzero(eligible)[0])
    rc["best_label"] = table.loc[rc["best_row"], "label"]
    rc["best_test_roi"] = float(table.loc[rc["best_row"], "test_roi"])
    rc["best_test_bets"] = int(table.loc[rc["best_row"], "test_bets"])
    wf = walk_forward(grid, min_train_bets=MIN_TRAIN_BETS)
    wf.to_csv(out / "walk_forward.csv", index=False)

    leaderboard = (
        table[eligible & (table["test_bets"] >= 50)]
        .sort_values("train_roi", ascending=False)
        .head(25)[["label", "train_bets", "train_roi", "train_t", "test_bets", "test_roi", "roi", "bets"]]
    )
    print("\n[analyze] top strategies chosen on", f"<{holdout}", "and scored on", holdout, flush=True)
    print(leaderboard.round(4).to_string(index=False), flush=True)
    print("\n[analyze] reality check:", json.dumps(rc, indent=1), flush=True)
    print("\n[analyze] walk-forward:\n", wf.round(4).to_string(index=False), flush=True)

    summary = {
        "seasons": [int(s) for s in seasons],
        "holdout": holdout,
        "n_games_box": int(games["game_id"].nunique()),
        "n_player_games": int(len(player_games)),
        "n_box_seasons": int(player_games["season"].nunique()),
        "n_prop_games": int(lines["game_id"].nunique()),
        "n_prop_lines": int(len(lines)),
        "n_strategies": int(len(table)),
        "n_eligible": int(eligible.sum()),
        "n_fdr_discoveries": int(table["fdr_discovery_train"].sum()),
        "reality_check": rc,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float))

    from nbaprops.report import build_report

    build_report(summary)
    return summary
