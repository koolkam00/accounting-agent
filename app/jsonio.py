"""Deterministic JSON reading and writing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_json_if_exists(path: Path | str) -> Optional[Any]:
    p = Path(path)
    return read_json(p) if p.exists() else None


def read_jsonl(path: Path | str) -> list[Any]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def dumps_canonical(data: Any) -> str:
    """Compact, key-sorted, ASCII-only JSON. Stable input for hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path | str, data: Any, *, indent: int = 2, sort_keys: bool = True) -> Path:
    """Write pretty JSON with sorted keys and a trailing newline."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=indent, sort_keys=sort_keys) + "\n", encoding="utf-8")
    return p


def write_jsonl(path: Path | str, records: list[Any], *, sort_keys: bool = True) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=sort_keys) + "\n")
    return p
