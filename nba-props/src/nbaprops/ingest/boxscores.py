"""Download ESPN game summaries, keep the parts we need, and parse them into box-score rows."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from nbaprops import config
from nbaprops.http import NotFound, get_json, read_json_gz, write_json_gz

SUMMARY_DIR = config.RAW / "summary"


def summary_path(season: int, game_id: str) -> Path:
    return SUMMARY_DIR / str(season) / f"{game_id}.json.gz"


def trim_summary(d: dict) -> dict:
    """Keep the header, the player box score and the pregame game lines; drop plays, news, etc."""
    header = d.get("header") or {}
    comp = (header.get("competitions") or [{}])[0]
    status = comp.get("status") or {}
    players = []
    for team in (d.get("boxscore") or {}).get("players", []):
        blocks = []
        for block in team.get("statistics", []):
            athletes = []
            for a in block.get("athletes", []):
                ath = a.get("athlete") or {}
                athletes.append(
                    {
                        "id": ath.get("id"),
                        "name": ath.get("displayName"),
                        "pos": (ath.get("position") or {}).get("abbreviation"),
                        "starter": a.get("starter"),
                        "dnp": a.get("didNotPlay"),
                        "reason": a.get("reason"),
                        "ejected": a.get("ejected"),
                        "stats": a.get("stats") or [],
                    }
                )
            blocks.append({"keys": block.get("keys") or [], "athletes": athletes})
        players.append({"team_id": (team.get("team") or {}).get("id"), "team": (team.get("team") or {}).get("abbreviation"), "blocks": blocks})
    picks = []
    for p in d.get("pickcenter") or []:
        picks.append(
            {
                "provider": (p.get("provider") or {}).get("name"),
                "provider_id": (p.get("provider") or {}).get("id"),
                "spread": p.get("spread"),
                "total": p.get("overUnder"),
                "details": p.get("details"),
                "home_ml": (p.get("homeTeamOdds") or {}).get("moneyLine"),
                "away_ml": (p.get("awayTeamOdds") or {}).get("moneyLine"),
                "home_fav": (p.get("homeTeamOdds") or {}).get("favorite"),
            }
        )
    return {
        "id": header.get("id"),
        "season": header.get("season"),
        "date": comp.get("date"),
        "status": (status.get("type") or {}).get("name"),
        "period": status.get("period"),
        "competitors": [
            {"id": c.get("id"), "homeAway": c.get("homeAway"), "team": (c.get("team") or {}).get("abbreviation"), "score": c.get("score")}
            for c in comp.get("competitors", [])
        ],
        "players": players,
        "pickcenter": picks,
    }


def fetch_summary(season: int, game_id: str) -> str:
    path = summary_path(season, game_id)
    if path.exists():
        return "cached"
    try:
        data = get_json(f"{config.ESPN_SITE}/summary", {"event": game_id})
    except NotFound:
        write_json_gz(path, {"id": game_id, "missing": True})
        return "missing"
    write_json_gz(path, trim_summary(data))
    return "fetched"


def pull_boxscores(schedule: pd.DataFrame, seasons: list[int], workers: int = 16) -> None:
    games = schedule[schedule["season"].isin(seasons) & schedule["completed"]]
    todo = [(int(s), g) for s, g in zip(games["season"], games["game_id"]) if not summary_path(int(s), g).exists()]
    print(f"[boxscores] {len(games)} completed games in scope, {len(todo)} to download", flush=True)
    counts: dict[str, int] = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(fetch_summary, s, g): g for s, g in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                status = fut.result()
            except Exception as exc:
                status = "error"
                print(f"[boxscores] {futures[fut]} failed: {exc}", flush=True)
            counts[status] = counts.get(status, 0) + 1
            if i % 1000 == 0:
                print(f"[boxscores] {i}/{len(todo)} {counts}", flush=True)
    print(f"[boxscores] done {counts}", flush=True)


# ---------------------------------------------------------------------------- parsing

_STAT_FIELDS = {
    "minutes": "min",
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "steals": "stl",
    "blocks": "blk",
    "turnovers": "tov",
    "offensiveRebounds": "oreb",
    "defensiveRebounds": "dreb",
    "fouls": "pf",
    "plusMinus": "plus_minus",
}
_MADE_ATTEMPTED = {
    "fieldGoalsMade-fieldGoalsAttempted": ("fgm", "fga"),
    "threePointFieldGoalsMade-threePointFieldGoalsAttempted": ("fg3m", "fg3a"),
    "freeThrowsMade-freeThrowsAttempted": ("ftm", "fta"),
}


def _num(x) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if s in ("", "--", "-"):
        return None
    try:
        return float(s.replace("+", ""))
    except ValueError:
        return None


def parse_summary(s: dict) -> tuple[dict | None, list[dict]]:
    if s.get("missing"):
        return None, []
    comps = {c["homeAway"]: c for c in s.get("competitors", [])}
    home, away = comps.get("home"), comps.get("away")
    if not home or not away:
        return None, []
    game_id = str(s["id"])
    pick = next((p for p in s.get("pickcenter", []) if p.get("spread") is not None or p.get("total") is not None), None)
    game = {
        "game_id": game_id,
        "periods": s.get("period"),
        "pregame_spread_home": _num(pick.get("spread")) if pick else None,
        "pregame_total": _num(pick.get("total")) if pick else None,
        "pregame_line_source": pick.get("provider") if pick else None,
    }
    rows = []
    for team in s.get("players", []):
        team_id = team.get("team_id")
        is_home = team_id == home["id"]
        opp = away if is_home else home
        for block in team.get("blocks", []):
            keys = block.get("keys", [])
            for a in block.get("athletes", []):
                row = {
                    "game_id": game_id,
                    "athlete_id": str(a.get("id")),
                    "name": a.get("name"),
                    "pos": a.get("pos"),
                    "team_id": team_id,
                    "team": team.get("team"),
                    "opp_team_id": opp["id"],
                    "opp_team": opp.get("team"),
                    "home": is_home,
                    "starter": bool(a.get("starter")),
                    "dnp": bool(a.get("dnp")) or not a.get("stats"),
                    "dnp_reason": a.get("reason"),
                    "ejected": bool(a.get("ejected")),
                }
                stats = a.get("stats") or []
                for key, val in zip(keys, stats):
                    if key in _STAT_FIELDS:
                        row[_STAT_FIELDS[key]] = _num(val)
                    elif key in _MADE_ATTEMPTED:
                        made, att = _MADE_ATTEMPTED[key]
                        parts = str(val).split("-")
                        row[made] = _num(parts[0]) if len(parts) == 2 else None
                        row[att] = _num(parts[1]) if len(parts) == 2 else None
                rows.append(row)
    return game, rows


def build_box_tables(schedule: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    games, players = [], []
    for season_dir in sorted(SUMMARY_DIR.glob("*")):
        for path in season_dir.glob("*.json.gz"):
            game, rows = parse_summary(read_json_gz(path))
            if game:
                games.append(game)
                players.extend(rows)
    g = pd.DataFrame(games)
    p = pd.DataFrame(players)
    g = schedule.merge(g, on="game_id", how="inner")
    p = p.merge(g[["game_id", "season", "season_type", "game_date", "start_utc"]], on="game_id", how="inner")
    p["played"] = ~p["dnp"] & (p["min"].fillna(0) > 0)
    # ESPN's summary rarely carries the period count. Five players log 240 minutes in
    # regulation and 25 more per overtime, so infer overtimes from team minutes.
    team_min = p.groupby(["game_id", "team_id"])["min"].sum().groupby("game_id").max()
    est = (4 + ((team_min - 240) / 25).round()).clip(lower=4).rename("periods_est")
    g = g.merge(est, left_on="game_id", right_index=True, how="left")
    g["periods"] = pd.to_numeric(g["periods"], errors="coerce").fillna(g["periods_est"])
    return g.drop(columns="periods_est"), p
