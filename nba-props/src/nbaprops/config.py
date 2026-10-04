"""Paths, endpoints and the market dictionary shared by every stage of the pipeline."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("NBAPROPS_ROOT", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"
RAW = DATA / "raw"
TABLES = DATA / "tables"
REPORTS = ROOT / "reports"

ESPN_SITE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_CORE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"

# ESPN labels seasons by the year they end in: 2024 == the 2023-24 season.
FIRST_BOX_SEASON = 2003
# Player props show up in ESPN's odds feed from opening night of 2022-23. We start
# one season earlier so the pull itself confirms nothing older exists.
FIRST_PROP_SEASON = 2022

# 2 = regular season, 3 = playoffs, 5 = play-in. Preseason (1) and the All-Star
# break are excluded.
SEASON_TYPES = {2: "regular", 3: "playoffs", 5: "play-in"}

# Real NBA franchises carry ESPN team ids 1-30; All-Star and exhibition sides do not.
NBA_TEAM_IDS = {str(i) for i in range(1, 31)}

# ESPN prop "type" name -> (market key, kind). kind "ou" is a standard over/under
# line; "milestone" is an "X+" ladder; "q1" lines settle on the first quarter only.
PROP_TYPES: dict[str, tuple[str, str]] = {
    "Total Points": ("pts", "ou"),
    "Total Rebounds": ("reb", "ou"),
    "Total Assists": ("ast", "ou"),
    "Total Steals": ("stl", "ou"),
    "Total Blocks": ("blk", "ou"),
    "Total 3-Point Field Goals": ("fg3m", "ou"),
    "Total Turnovers": ("tov", "ou"),
    "Total Points, Rebounds, and Assists": ("pra", "ou"),
    "Total Points and Rebounds": ("pr", "ou"),
    "Total Points and Assists": ("pa", "ou"),
    "Total Assists and Rebounds": ("ra", "ou"),
    "Total Steals and Blocks": ("stocks", "ou"),
    "Total Field Goals Made (incl. overtime)": ("fgm", "ou"),
    "Points Milestones": ("pts", "milestone"),
    "Rebounds Milestones": ("reb", "milestone"),
    "Assists Milestones": ("ast", "milestone"),
    "Steals Milestones": ("stl", "milestone"),
    "Blocks Milestones": ("blk", "milestone"),
    "3-Point Field Goals Milestones": ("fg3m", "milestone"),
    "Points + Assists + Rebounds Milestones": ("pra", "milestone"),
    "Points + Rebounds Milestones": ("pr", "milestone"),
    "Points + Assists Milestones": ("pa", "milestone"),
    "Assists + Rebounds Milestones": ("ra", "milestone"),
    "Points Milestones - 1st Quarter": ("pts", "q1"),
    "Assists Milestones - 1st Quarter": ("ast", "q1"),
    "Rebounds Milestones - 1st Quarter": ("reb", "q1"),
}

# How each market settles from a box score line.
MARKET_FORMULAS: dict[str, tuple[str, ...]] = {
    "pts": ("pts",),
    "reb": ("reb",),
    "ast": ("ast",),
    "stl": ("stl",),
    "blk": ("blk",),
    "fg3m": ("fg3m",),
    "tov": ("tov",),
    "fgm": ("fgm",),
    "pra": ("pts", "reb", "ast"),
    "pr": ("pts", "reb"),
    "pa": ("pts", "ast"),
    "ra": ("reb", "ast"),
    "stocks": ("stl", "blk"),
}

# The five stats in the original thesis, then the extras the books also post.
CORE_MARKETS = ["pts", "reb", "ast", "stl", "blk"]
EXTRA_MARKETS = ["fg3m", "tov", "pra", "pr", "pa", "ra", "stocks"]
ALL_MARKETS = CORE_MARKETS + EXTRA_MARKETS

MARKET_LABELS = {
    "pts": "Points",
    "reb": "Rebounds",
    "ast": "Assists",
    "stl": "Steals",
    "blk": "Blocks",
    "fg3m": "3-pointers made",
    "tov": "Turnovers",
    "fgm": "Field goals made",
    "pra": "Pts+Reb+Ast",
    "pr": "Pts+Reb",
    "pa": "Pts+Ast",
    "ra": "Reb+Ast",
    "stocks": "Stl+Blk",
}


def ensure_dirs() -> None:
    for path in (RAW, TABLES, REPORTS):
        path.mkdir(parents=True, exist_ok=True)
