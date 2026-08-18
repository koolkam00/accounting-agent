"""Fixture case discovery and loading.

Every caller (scripts, tests, UI) resolves case directories, expected gold, and
canonical invoice text through here so the layout of `tests/fixtures` is
described in exactly one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.canonicalize import canonicalize_document
from app.jsonio import read_json
from app.pdf_text import extract_pdf_text
from app.settings import REPO_ROOT

FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures"
DEVELOPMENT_ROOT = FIXTURE_ROOT / "development"
HOLDOUT_ROOT = FIXTURE_ROOT / "holdout"
DIFFICULTY_ROOT = FIXTURE_ROOT / "difficulty"

SPLITS = ("development", "holdout")
DIFFICULTY_PACKS = ("easy", "medium", "hard")

CASE_PREFIX = "case_"


def split_root(split: str) -> Path:
    return FIXTURE_ROOT / split


def difficulty_root(difficulty: str) -> Path:
    return DIFFICULTY_ROOT / difficulty


def case_dirs(root: Path) -> list[Path]:
    """Sorted `case_*` directories directly under `root` (empty if missing)."""
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith(CASE_PREFIX))


def case_dirs_in(roots: list[Path]) -> list[Path]:
    cases: list[Path] = []
    for root in roots:
        cases.extend(case_dirs(root))
    return cases


def default_case_roots() -> list[Path]:
    return [split_root(split) for split in SPLITS]


def all_case_dirs(difficulty: Optional[str] = None) -> list[Path]:
    """Cases of one difficulty pack, or development+holdout when unspecified."""
    if difficulty:
        return case_dirs(difficulty_root(difficulty))
    return case_dirs_in(default_case_roots())


def case_dirs_by_split(difficulty: Optional[str] = None) -> dict[str, list[Path]]:
    """Map development/holdout to case dirs.

    Difficulty packs keep both splits in one directory and record the split in
    `expected.json`.
    """
    if difficulty:
        splits: dict[str, list[Path]] = {"development": [], "holdout": []}
        for case_dir in case_dirs(difficulty_root(difficulty)):
            split = load_expected(case_dir).get("split")
            splits["holdout" if split == "holdout" else "development"].append(case_dir)
        return splits
    return {split: case_dirs(split_root(split)) for split in SPLITS}


def find_case_dir(case_id: str) -> Path:
    """Locate a case by id across splits and difficulty packs."""
    candidates = [split_root(split) / case_id for split in SPLITS]
    candidates.extend(difficulty_root(pack) / case_id for pack in DIFFICULTY_PACKS)
    for path in candidates:
        if path.is_dir():
            return path
    raise FileNotFoundError(case_id)


def load_expected(case_dir: Path) -> dict[str, Any]:
    return read_json(case_dir / "expected.json")


def gold_extraction(expected: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Gold extraction JSON under either the current or the legacy key."""
    return expected.get("extraction") or expected.get("extracted_invoice")


def load_pdf_bytes(case_dir: Path) -> bytes:
    return (case_dir / "invoice.pdf").read_bytes()


def canonical_text_for_pdf(pdf_bytes: bytes) -> str:
    """Canonical text-layer string the model actually sees for a PDF."""
    pages = extract_pdf_text(pdf_bytes).pages
    return canonicalize_document(pdf_bytes, pages).canonical_text


def canonical_text_for_case(case_dir: Path) -> str:
    return canonical_text_for_pdf(load_pdf_bytes(case_dir))
