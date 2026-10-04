import numpy as np
import pandas as pd
import pytest

from nbaprops.backtest import bh_fdr, clustered_t, decimal_to_american, to_decimal
from nbaprops.build import _assign_sides, american_to_decimal, settle, side_pnl
from nbaprops.features import _prior_window, signed_streak
from nbaprops.ingest.boxscores import parse_summary
from nbaprops.ingest.props import american_to_int, trim_item


def test_american_odds_conversions():
    assert american_to_decimal([-110, 150, 100]) == pytest.approx([1.909090909, 2.5, 2.0])
    assert to_decimal([-200]) == pytest.approx([1.5])
    assert decimal_to_american(1.5) == pytest.approx(-200)
    assert decimal_to_american(2.5) == pytest.approx(150)
    assert american_to_int("Even") == 100
    assert american_to_int("+3000") == 3000
    assert american_to_int("-120") == -120
    assert american_to_int("OFF") is None


def test_settle_and_pnl():
    actual = np.array([10.0, 8.0, 9.0, np.nan])
    line = np.array([9.5, 9.5, 9.0, 9.5])
    played = np.array([True, True, True, False])
    res = settle(actual, line, played)
    assert list(res) == ["over", "under", "push", "void"]
    dec = american_to_decimal(np.array([-110.0, -110.0, -110.0, -110.0]))
    over = side_pnl(res, dec, "over")
    assert over[0] == pytest.approx(100 / 110)
    assert over[1] == -1.0
    assert over[2] == 0.0
    assert np.isnan(over[3])
    under = side_pnl(res, dec, "under")
    assert under[1] == pytest.approx(100 / 110) and under[0] == -1.0


def test_unlabeled_sides_follow_feed_order():
    # Labeled books always list Over then Under; unlabeled pairs are read the same way and
    # a lone alternate line stays unpaired.
    rows = [
        # game, book, athlete, market, line, side, idx
        ("g", "100", "a1", "pts", 20.5, None, 0),
        ("g", "100", "a1", "pts", 20.5, None, 1),
        ("g", "100", "a1", "pts", 25.5, None, 2),
        ("g", "58", "a2", "reb", 7.5, "over", 0),
        ("g", "58", "a2", "reb", 7.5, "under", 1),
    ]
    df = pd.DataFrame(rows, columns=["game_id", "book_id", "athlete_id", "market", "line_close", "side", "item_idx"])
    out = _assign_sides(df)
    pts = out[out["athlete_id"] == "a1"].sort_values("item_idx")
    assert list(pts["side"]) == ["over", "under"]
    assert pts["side_inferred"].all()
    assert 25.5 not in set(pts["line_close"])
    assert not out[out["athlete_id"] == "a2"]["side_inferred"].any()


def test_signed_streak_breaks_on_push_and_new_group():
    sign = pd.Series([1, 1, -1, -1, -1, 0, 1, 1])
    groups = pd.Series(["a"] * 6 + ["b"] * 2)
    assert list(signed_streak(sign, groups)) == [1, 2, -1, -2, -3, 0, 1, 2]


def test_prior_window_uses_only_earlier_games():
    v = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 10.0])
    g = pd.Series(["x"] * 6)
    mean3, sd3 = _prior_window(v, g, 3, 3)
    assert np.isnan(mean3.iloc[2])
    assert mean3.iloc[3] == pytest.approx(2.0)  # mean of 1,2,3 - excludes the current 4
    assert mean3.iloc[5] == pytest.approx(4.0)  # mean of 3,4,5
    assert sd3.iloc[5] == pytest.approx(1.0)
    season_mean, _ = _prior_window(v, g, None, 1)
    assert season_mean.iloc[5] == pytest.approx(3.0)


def test_clustered_t_and_fdr():
    day_p = np.array([1.0, -1.0, 0.9, 0.0])
    day_n = np.array([2.0, 1.0, 1.0, 0.0])
    roi, se, t = clustered_t(day_p, day_n)
    assert roi == pytest.approx(0.9 / 4)
    assert se > 0 and t == pytest.approx(roi / se)
    passed = bh_fdr(np.array([0.001, 0.02, 0.5, 0.9]), q=0.10)
    assert list(passed) == [True, True, False, False]


def test_trim_item_reads_espn_prop_bet():
    item = {
        "athlete": {"$ref": "http://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2024/athletes/3059318?lang=en"},
        "type": {"id": "1", "name": "Total Points"},
        "odds": {"american": {"value": "-120", "open": "-115"}, "total": {"value": "32.5", "open": "31.5"}},
        "current": {"over": {"american": "-120"}, "target": {"value": 32.5}},
        "open": {"over": {"american": "-115"}, "target": {"value": 31.5}},
        "lastUpdated": "2024-01-15T21:11Z",
    }
    assert trim_item(item) == ["3059318", "1", "Total Points", "over", "31.5", "32.5", "-115", "-120", "2024-01-15T21:11Z"]
    assert trim_item({"type": {"name": "Team Total Points"}}) is None


def test_parse_summary_box_score():
    s = {
        "id": "1",
        "period": None,
        "competitors": [{"id": "20", "homeAway": "home", "team": "PHI"}, {"id": "10", "homeAway": "away", "team": "HOU"}],
        "pickcenter": [{"provider": "X", "spread": -8.0, "total": 229.0}],
        "players": [
            {
                "team_id": "20",
                "team": "PHI",
                "blocks": [
                    {
                        "keys": ["minutes", "points", "fieldGoalsMade-fieldGoalsAttempted", "rebounds", "assists", "steals", "blocks"],
                        "athletes": [
                            {"id": "7", "name": "A", "starter": True, "dnp": False, "stats": ["36", "31", "11-20", "12", "6", "1", "2"]},
                            {"id": "8", "name": "B", "starter": False, "dnp": True, "stats": []},
                        ],
                    }
                ],
            }
        ],
    }
    game, rows = parse_summary(s)
    assert game["pregame_spread_home"] == -8.0 and game["pregame_total"] == 229.0
    a, b = rows
    assert a["pts"] == 31 and a["fgm"] == 11 and a["fga"] == 20 and a["home"] and a["opp_team"] == "HOU"
    assert b["dnp"]


def test_quarantine_drops_bad_closes_openers_and_placeholder_prices():
    from nbaprops.build import quarantine_bad_lines

    g = pd.DataFrame(
        {
            "season": [2023, 2023, 2025],
            "book_family": ["DraftKings", "MGM", "ESPN BET"],
            "line_open": [20.5, 20.5, 0.5],
            "line_close": [24.5, 20.5, 21.5],
            "over_open": [-110.0, -110.0, -5000.0],
            "under_open": [-110.0, -110.0, 750.0],
            "over_close": [-110.0, -110.0, -115.0],
            "under_close": [-110.0, -110.0, -105.0],
            "pnl_over_open": [0.9, 0.9, 0.02],
            "pnl_under_open": [-1.0, -1.0, -1.0],
            "pnl_over_close": [0.9, 0.9, -1.0],
            "pnl_under_close": [-1.0, -1.0, 0.95],
            "fair_over_open": [0.5, 0.5, 0.9],
            "fair_over_close": [0.5, 0.5, 0.52],
            "vig_close": [0.05, 0.05, 0.05],
            "result_open": ["over", "over", "over"],
            "result_close": ["over", "over", "under"],
        }
    )
    quality = pd.DataFrame(
        {
            "season": [2023, 2023, 2025],
            "book_family": ["DraftKings", "MGM", "ESPN BET"],
            "close_usable": [False, True, True],  # DraftKings 2022-23 close was an in-game line
            "open_usable": [True, True, True],
        }
    )
    out = quarantine_bad_lines(g, quality)
    dk, mgm, espn = out.iloc[0], out.iloc[1], out.iloc[2]
    assert np.isnan(dk["line_close"]) and dk["result_close"] == "no_close" and dk["line_open"] == 20.5
    assert mgm["line_close"] == 20.5 and mgm["result_close"] == "over"
    # -5000 / +750 is a placeholder opener even though the book-season passed
    assert np.isnan(espn["line_open"]) and espn["result_open"] == "no_open" and espn["line_close"] == 21.5


def test_bet_panel_single_book_and_line_shopping():
    from nbaprops.features import bet_panel

    base = {"game_id": "g", "athlete_id": "a", "market": "pts", "season": 2024, "season_type": 2, "game_date": "2024-01-01",
            "start_utc": "2024-01-01T00:00Z", "played": True, "actual": 21.0, "home": True}
    rows = [
        # MGM has the lowest line (good for overs), Caesars the highest (good for unders).
        {**base, "book_family": "MGM", "line_close": 20.5, "over_close": -120.0, "under_close": -100.0, "pnl_over_close": 0.833, "pnl_under_close": -1.0},
        {**base, "book_family": "Caesars", "line_close": 21.5, "over_close": -105.0, "under_close": -115.0, "pnl_over_close": -1.0, "pnl_under_close": 0.87},
        {**base, "book_family": "DraftKings", "line_close": 21.0, "over_close": -110.0, "under_close": -110.0, "pnl_over_close": 0.0, "pnl_under_close": 0.0},
    ]
    lines = pd.DataFrame(rows)
    for col in ("line_open", "over_open", "under_open", "pnl_over_open", "pnl_under_open"):
        lines[col] = np.nan  # no usable openers: only closing bets are possible
    best = bet_panel(lines, "best").iloc[0]
    assert best["line_over_close"] == 20.5 and best["book_over_close"] == "MGM"
    assert best["line_under_close"] == 21.5 and best["book_under_close"] == "Caesars"
    assert np.isnan(best["pnl_over_open"])
    single = bet_panel(lines, "single").iloc[0]
    assert single["book_over_close"] == "DraftKings" and single["line_under_close"] == 21.0
