"""Identifier validation for values that reach the filesystem."""

from __future__ import annotations

import re

CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def is_safe_case_id(case_id: str | None) -> bool:
    """True when ``case_id`` is safe to use as a single path segment."""
    if not case_id or ".." in case_id:
        return False
    return CASE_ID_PATTERN.match(case_id) is not None


def require_safe_case_id(case_id: str) -> str:
    if not is_safe_case_id(case_id):
        raise ValueError(
            "case_id must be 1-64 chars of [A-Za-z0-9._-], start alphanumeric, and contain no '..'"
        )
    return case_id
