#!/usr/bin/env python3
"""Load all fixture PO/receipt/vendor data into SQLite deterministically."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.database import init_db, reset_db
from app.erp_seed import seed_fixture_cases
from app.fixtures import case_dirs_in, default_case_roots
from app.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables")
    parser.add_argument("--database-url", default=None)
    parser.add_argument(
        "--fixture-root",
        action="append",
        dest="fixture_roots",
        default=None,
        help="Case directory parent (repeatable). Default: development+holdout.",
    )
    args = parser.parse_args()

    settings = get_settings()
    db_url = args.database_url or settings.database_url
    sf = reset_db(db_url) if args.reset else init_db(db_url)
    roots = [Path(r) for r in args.fixture_roots] if args.fixture_roots else default_case_roots()
    cases = case_dirs_in(roots)

    seed_fixture_cases(sf, cases)

    print(f"Initialized database at {db_url}")
    print(f"Loaded {len(cases)} cases")


if __name__ == "__main__":
    main()
