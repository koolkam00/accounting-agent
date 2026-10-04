"""Download every sportsbook's player-prop lines that ESPN's odds feed kept for a game.

ESPN's core API (sports.core.api.espn.com) exposes, for each game and each sportsbook
("provider"), the prop markets that book posted: the opening line and price and the
last pregame line and price. Books seen in the feed include Caesars, DraftKings, MGM,
BetRivers (SugarHouse), PointsBet and ESPN BET.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from nbaprops import config
from nbaprops.http import NotFound, get_json, read_json_gz, write_json_gz

PROPS_DIR = config.RAW / "props"
ITEM_FIELDS = ["athlete_id", "type_id", "type", "side", "line_open", "line_close", "odds_open", "odds_close", "updated"]
_ATHLETE_RE = re.compile(r"/athletes/(\d+)")


def props_path(season: int, game_id: str) -> Path:
    return PROPS_DIR / str(season) / f"{game_id}.json.gz"


def _side(item: dict) -> str | None:
    for block in (item.get("current") or {}, item.get("open") or {}):
        if "over" in block:
            return "over"
        if "under" in block:
            return "under"
    return None


def trim_item(item: dict) -> list | None:
    ref = (item.get("athlete") or {}).get("$ref", "")
    m = _ATHLETE_RE.search(ref)
    if not m:
        return None  # team and game-level markets carry no athlete
    odds = item.get("odds") or {}
    total = odds.get("total") or {}
    american = odds.get("american") or {}
    line_close = total.get("value", ((item.get("current") or {}).get("target") or {}).get("value"))
    line_open = total.get("open", ((item.get("open") or {}).get("target") or {}).get("value"))
    type_ = item.get("type") or {}
    return [
        m.group(1),
        type_.get("id"),
        type_.get("name"),
        _side(item),
        line_open,
        line_close,
        american.get("open"),
        american.get("value"),
        item.get("lastUpdated"),
    ]


def _fetch_provider_items(game_id: str, provider_id: str) -> list[list]:
    items: list[list] = []
    page = 1
    while True:
        url = f"{config.ESPN_CORE}/events/{game_id}/competitions/{game_id}/odds/{provider_id}/propBets"
        try:
            data = get_json(url, {"limit": 1000, "page": page})
        except NotFound:
            break
        items.extend(t for it in data.get("items", []) if (t := trim_item(it)))
        if page >= int(data.get("pageCount") or 1):
            break
        page += 1
    return items


def fetch_props(season: int, game_id: str) -> str:
    path = props_path(season, game_id)
    if path.exists():
        return "cached"
    try:
        odds = get_json(f"{config.ESPN_CORE}/events/{game_id}/competitions/{game_id}/odds", {"limit": 100})
    except NotFound:
        odds = {"items": []}
    providers: dict[str, dict] = {}
    for it in odds.get("items", []):
        prov = it.get("provider") or {}
        pid, name = str(prov.get("id")), prov.get("name") or ""
        if "live" in name.lower() or pid in providers or pid in config.NO_PROP_PROVIDERS:
            continue  # in-game markets are not pregame closing lines
        items = _fetch_provider_items(game_id, pid)
        if items:
            providers[pid] = {"name": name, "items": items}
    write_json_gz(
        path,
        {
            "game_id": game_id,
            "season": season,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "fields": ITEM_FIELDS,
            "providers": providers,
            "game_odds": game_odds(odds),
        },
    )
    return "with_props" if providers else "no_props"


def game_odds(odds: dict) -> list[dict]:
    """Pregame spread / total / moneylines per book (spread is from the home team's side)."""
    out = []
    for it in odds.get("items", []):
        prov = it.get("provider") or {}
        name = prov.get("name") or ""
        if "live" in name.lower():
            continue
        home, away = it.get("homeTeamOdds") or {}, it.get("awayTeamOdds") or {}
        out.append(
            {
                "provider_id": str(prov.get("id")),
                "provider": name,
                "details": it.get("details"),
                "spread": it.get("spread"),
                "total": it.get("overUnder"),
                "home_ml": home.get("moneyLine"),
                "away_ml": away.get("moneyLine"),
                "home_favorite": home.get("favorite"),
            }
        )
    return out


def backfill_game_odds(schedule: pd.DataFrame, workers: int = 12) -> None:
    """Add game lines to props files written before game odds were captured."""
    todo = []
    for season_dir in sorted(PROPS_DIR.glob("*")):
        for path in season_dir.glob("*.json.gz"):
            doc = read_json_gz(path)
            if "game_odds" not in doc:
                todo.append((path, doc))
    print(f"[props] backfilling game odds for {len(todo)} games", flush=True)

    def work(item):
        path, doc = item
        gid = doc["game_id"]
        try:
            odds = get_json(f"{config.ESPN_CORE}/events/{gid}/competitions/{gid}/odds", {"limit": 100})
        except NotFound:
            odds = {"items": []}
        doc["game_odds"] = game_odds(odds)
        write_json_gz(path, doc)

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(work, todo))


def build_game_odds_table() -> pd.DataFrame:
    rows = []
    for season_dir in sorted(PROPS_DIR.glob("*")):
        for path in season_dir.glob("*.json.gz"):
            doc = read_json_gz(path)
            for o in doc.get("game_odds", []):
                rows.append({"game_id": doc["game_id"], **o})
    cols = ["game_id", "provider_id", "provider", "details", "spread", "total", "home_ml", "away_ml", "home_favorite"]
    return pd.DataFrame(rows, columns=cols)


def pull_props(schedule: pd.DataFrame, seasons: list[int], workers: int = 12) -> None:
    games = schedule[schedule["season"].isin(seasons) & schedule["completed"]]
    todo = [(int(s), g) for s, g in zip(games["season"], games["game_id"]) if not props_path(int(s), g).exists()]
    print(f"[props] {len(games)} completed games in scope, {len(todo)} to download", flush=True)
    counts: dict[str, int] = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(fetch_props, s, g): g for s, g in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                status = fut.result()
            except Exception as exc:
                status = "error"
                print(f"[props] {futures[fut]} failed: {exc}", flush=True)
            counts[status] = counts.get(status, 0) + 1
            if i % 500 == 0:
                print(f"[props] {i}/{len(todo)} {counts}", flush=True)
    print(f"[props] done {counts}", flush=True)


# ---------------------------------------------------------------------------- parsing


def american_to_int(x) -> float | None:
    if x is None:
        return None
    s = str(x).strip().upper()
    if s in ("EVEN", "EV", "PK"):
        return 100.0
    try:
        v = float(s.replace("+", ""))
    except ValueError:
        return None
    if -100 < v < 100:  # not a valid American price (OFF / suspended markets come through as junk)
        return None
    return v


def _float(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def build_props_table() -> pd.DataFrame:
    """One row per priced outcome: game x book x player x market x line x side (in feed order)."""
    rows = []
    for season_dir in sorted(PROPS_DIR.glob("*")):
        for path in season_dir.glob("*.json.gz"):
            doc = read_json_gz(path)
            fields = doc.get("fields", ITEM_FIELDS)
            for pid, prov in doc.get("providers", {}).items():
                for idx, raw in enumerate(prov["items"]):
                    it = dict(zip(fields, raw))
                    market, kind = config.PROP_TYPES.get(it["type"], (None, None))
                    rows.append(
                        (
                            doc["game_id"],
                            int(doc["season"]),
                            pid,
                            prov["name"],
                            it["athlete_id"],
                            it["type"],
                            market,
                            kind,
                            it["side"],
                            _float(it["line_open"]),
                            _float(it["line_close"]),
                            american_to_int(it["odds_open"]),
                            american_to_int(it["odds_close"]),
                            it["updated"],
                            idx,
                        )
                    )
    cols = [
        "game_id", "season", "book_id", "book", "athlete_id", "prop_type", "market", "kind", "side",
        "line_open", "line_close", "odds_open", "odds_close", "updated", "item_idx",
    ]
    return pd.DataFrame(rows, columns=cols)
