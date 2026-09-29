#!/usr/bin/env python3
"""Turn reviewer corrections of tool errors into regression cases.

Reads ``workpaper.json`` and ``review_log.jsonl`` from a workpaper directory
(``workpapers/<deal_id>/``). Every decision whose correction type is a tool
error (TOOL_WRONG_LINK, TOOL_MISSED_EVIDENCE, TOOL_WRONG_AMOUNT,
TOOL_WRONG_FLAG, TOOL_WRONG_TREATMENT) is written to
``tests/regressions/<deal_id>__<adj_id>__<n>.json``: a pointer to the
inputs (deal dir, adj id), the tool's output, the reviewer's expected
treatment and amounts, the correction type and the rationale.

Judgment differences and new information are reviewer calls, not tool
defects: they are summarized on the console but never become cases.

Usage:
    uv run python scripts/qoe_corrections_to_evals.py --workpaper-dir workpapers/meridian_mechanical
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qoe.evaluate import regression_cases
from qoe.schemas import ReviewDecision, Workpaper

WORKPAPER_FILE = "workpaper.json"
REVIEW_LOG = "review_log.jsonl"
DEFAULT_OUT = ROOT / "tests" / "regressions"


def read_decisions(log_path: Path) -> list[ReviewDecision]:
    """Every decision in log order, via the review store when it is available."""
    try:
        from qoe.review_store import ReviewStore
    except ImportError:
        ReviewStore = None  # type: ignore[assignment,misc]
    if ReviewStore is not None:
        store = ReviewStore(log_path)
        decisions = list(store.all())
        skipped = getattr(store, "skipped_lines", [])
        if skipped:
            print(f"Warning: skipped unreadable review log line(s) {skipped} in {log_path}", file=sys.stderr)
        return decisions
    decisions: list[ReviewDecision] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            decisions.append(ReviewDecision.model_validate_json(line))
    return decisions


def _portable(path: Path) -> str:
    """Project-relative POSIX path when possible, so cases survive a repo move."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def find_deal_dir(deal_id: str, data_root: Path = ROOT / "data") -> Optional[Path]:
    if not data_root.is_dir():
        return None
    for split_dir in sorted(p for p in data_root.iterdir() if p.is_dir()):
        candidate = split_dir / deal_id
        if (candidate / "deal.yaml").is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--workpaper-dir", type=Path, required=True, help="directory holding workpaper.json and review_log.jsonl"
    )
    parser.add_argument(
        "--deal-dir",
        type=Path,
        default=None,
        help="deal package the workpaper came from (default: search data/*/<deal_id>)",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="regression case directory (default: <project>/tests/regressions)"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the summary without writing cases")
    args = parser.parse_args(argv)

    wp_path = args.workpaper_dir / WORKPAPER_FILE
    log_path = args.workpaper_dir / REVIEW_LOG
    if not wp_path.is_file():
        print(f"No {WORKPAPER_FILE} in {args.workpaper_dir}", file=sys.stderr)
        return 2
    wp = Workpaper.model_validate_json(wp_path.read_text(encoding="utf-8"))
    decisions = read_decisions(log_path) if log_path.is_file() else []

    deal_dir = args.deal_dir if args.deal_dir is not None else find_deal_dir(wp.deal.deal_id)
    cases, summary = regression_cases(wp, decisions, _portable(deal_dir) if deal_dir is not None else None)

    out_dir = args.out if args.out is not None else DEFAULT_OUT
    written: list[Path] = []
    if not args.dry_run and cases:
        out_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            path = out_dir / f"{case['case_id']}.json"
            path.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            written.append(path)

    print(f"Deal {wp.deal.deal_id}: {summary['decisions']} review decision(s) in {log_path}")
    for ctype, n in summary["by_correction_type"].items():
        print(f"  {ctype:<22} {n}")
    print(f"Tool-error regression cases: {len(cases)}" + (" (dry run, not written)" if args.dry_run else ""))
    for path in written:
        print(f"  wrote {path}")
    if args.dry_run:
        for case in cases:
            print(f"  {case['case_id']}")
    judgment = summary["judgment_and_new_information"]
    print(f"Judgment differences / new information (not regression cases): {len(judgment)}")
    for item in judgment:
        print(
            f"  {item['adj_id']:<8} {item['correction_type']:<20} tool {item['tool_treatment']} -> "
            f"reviewer {item['reviewer_treatment']}: {item['rationale']}"
        )
    if deal_dir is None:
        print("Note: deal package not found; cases carry deal_dir = null. Pass --deal-dir to record it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
