#!/usr/bin/env python3
"""Run a single fixture case through the pipeline (mock LLM by default)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import init_db
from app.fixtures import FIXTURE_ROOT, find_case_dir
from app.llm_client import MockLLMClient
from app.pipeline import run_case_dir
from app.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", choices=["evaluate", "create_draft"], default="evaluate")
    args = parser.parse_args()

    settings = get_settings()
    sf = init_db(settings.database_url)
    erp = LocalERPAdapter(sf)
    llm = MockLLMClient(fixture_root=FIXTURE_ROOT)
    case_dir = find_case_dir(args.case)
    result = run_case_dir(case_dir, erp=erp, llm=llm, mode=args.mode)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
