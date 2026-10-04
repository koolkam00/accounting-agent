"""Discover every NBA game ESPN knows about by walking the scoreboard one day at a time."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from nbaprops import config
from nbaprops.http import get_json

SCHEDULE_PATH = config.TABLES / "schedule.parquet"
DONE_PATH = config.RAW / "scoreboard_days_done.json"


def _parse_event(ev: dict, day: date) -> dict | None:
    season = ev.get("season") or {}
    stype = season.get("type")
    if stype not in config.SEASON_TYPES:
        return None
    comp = (ev.get("competitions") or [{}])[0]
    teams = {c.get("homeAway"): c for c in comp.get("competitors", [])}
    home, away = teams.get("home"), teams.get("away")
    if not home or not away:
        return None
    if home["team"]["id"] not in config.NBA_TEAM_IDS or away["team"]["id"] not in config.NBA_TEAM_IDS:
        return None
    status = (ev.get("status") or {}).get("type") or {}
    notes = comp.get("notes") or []

    def score(c: dict) -> float | None:
        try:
            return float(c.get("score"))
        except (TypeError, ValueError):
            return None

    return {
        "game_id": str(ev["id"]),
        "season": int(season["year"]),
        "season_type": int(stype),
        "game_date": day.isoformat(),
        "start_utc": ev.get("date"),
        "status": status.get("name"),
        "completed": bool(status.get("completed")),
        "neutral_site": bool(comp.get("neutralSite")),
        "home_team_id": home["team"]["id"],
        "home_team": home["team"].get("abbreviation"),
        "away_team_id": away["team"]["id"],
        "away_team": away["team"].get("abbreviation"),
        "home_score": score(home),
        "away_score": score(away),
        "note": notes[0].get("headline") if notes else None,
    }


def _scan_day(day: date) -> tuple[date, list[dict]]:
    data = get_json(f"{config.ESPN_SITE}/scoreboard", {"dates": day.strftime("%Y%m%d"), "limit": 100})
    rows = [r for ev in data.get("events", []) if (r := _parse_event(ev, day))]
    return day, rows


def load_schedule() -> pd.DataFrame:
    if SCHEDULE_PATH.exists():
        return pd.read_parquet(SCHEDULE_PATH)
    return pd.DataFrame()


def update_schedule(start: date, end: date, workers: int = 16, refresh_days: int = 4) -> pd.DataFrame:
    """Scan [start, end]. Days already fully scanned are skipped, except the most recent ones."""
    config.ensure_dirs()
    done: set[str] = set(json.loads(DONE_PATH.read_text())) if DONE_PATH.exists() else set()
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=refresh_days)
    days = []
    d = start
    while d <= end:
        if d.isoformat() not in done or d >= cutoff:
            days.append(d)
        d += timedelta(days=1)
    print(f"[schedule] scanning {len(days)} days between {start} and {end}", flush=True)

    new_rows: list[dict] = []
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(_scan_day, day): day for day in days}
        for i, fut in enumerate(as_completed(futures), 1):
            day = futures[fut]
            try:
                _, rows = fut.result()
            except Exception as exc:  # leave the day unmarked so the next run retries it
                print(f"[schedule] {day} failed: {exc}", flush=True)
                continue
            new_rows.extend(rows)
            if day < cutoff and all(r["completed"] for r in rows):
                done.add(day.isoformat())
            if i % 500 == 0:
                print(f"[schedule] {i}/{len(days)} days, {len(new_rows)} games so far", flush=True)

    sched = load_schedule()
    if new_rows:
        new = pd.DataFrame(new_rows)
        if not sched.empty:
            sched = sched[~sched["game_id"].isin(new["game_id"])]
        sched = pd.concat([sched, new], ignore_index=True)
        sched = sched.sort_values(["start_utc", "game_id"]).reset_index(drop=True)
        sched.to_parquet(SCHEDULE_PATH, index=False)
    DONE_PATH.write_text(json.dumps(sorted(done)))
    print(f"[schedule] {len(sched)} games on file", flush=True)
    return sched
