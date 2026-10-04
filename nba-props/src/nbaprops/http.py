"""Small HTTP layer: per-thread sessions, retries with backoff, and a global rate cap."""

from __future__ import annotations

import gzip
import json
import os
import random
import threading
import time
from pathlib import Path
from typing import Any

import requests

_local = threading.local()
_rate_lock = threading.Lock()
_next_slot = 0.0
MAX_RPS = float(os.environ.get("NBAPROPS_MAX_RPS", "25"))  # be a polite client of a free API
USER_AGENT = "nbaprops-research/0.1 (+historical prop-line study)"


class NotFound(Exception):
    """The resource does not exist (HTTP 404, or ESPN's JSON error body with code 404)."""


def _session() -> requests.Session:
    sess = getattr(_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        _local.session = sess
    return sess


def _wait_for_slot() -> None:
    global _next_slot
    with _rate_lock:
        now = time.monotonic()
        slot = max(now, _next_slot)
        _next_slot = slot + 1.0 / MAX_RPS
    delay = slot - time.monotonic()
    if delay > 0:
        time.sleep(delay)


def get_json(url: str, params: dict[str, Any] | None = None, retries: int = 6, timeout: float = 45.0) -> Any:
    """GET a JSON document, retrying throttling, server errors and dropped connections."""
    last_err: Exception | None = None
    for attempt in range(retries):
        _wait_for_slot()
        try:
            resp = _session().get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            last_err = exc
        else:
            if resp.status_code == 404:
                raise NotFound(url)
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = RuntimeError(f"HTTP {resp.status_code} for {resp.url}")
            elif resp.status_code >= 400:
                resp.raise_for_status()
            else:
                data = resp.json()
                if isinstance(data, dict) and isinstance(data.get("error"), dict) and data["error"].get("code") == 404:
                    raise NotFound(url)
                return data
        time.sleep(min(60.0, (2**attempt) + random.random()))
    raise RuntimeError(f"giving up on {url}: {last_err}")


def write_json_gz(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, separators=(",", ":"))
    tmp.replace(path)


def read_json_gz(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)
