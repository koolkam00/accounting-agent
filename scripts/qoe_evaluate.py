#!/usr/bin/env python3
"""Score QoE Evidence Review against the answer keys of a data split.

For every deal package under ``data/qoe/<split>/`` this runs a fresh review
(fixed run id and timestamp, so runs are reproducible), scores the tool's
first-pass proposals with ``qoe.evaluate.score``, and writes
``<out>/eval_<split>.json`` and ``<out>/eval_<split>.md``.

The scores are automated comparisons against synthetic answer keys, not
practitioner-timed results. Reviewer decisions are never part of the score.

Usage:
    uv run python scripts/qoe_evaluate.py --split dev
    uv run python scripts/qoe_evaluate.py --split all --ai rules --out reports/qoe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qoe.evaluate import GROUND_TRUTH_FILE, build_report, load_ground_truth, render_markdown, score

DATA_ROOT = ROOT / "data" / "qoe"
SPLITS = ("dev", "holdout")
# Fixed so that eval workpapers (and therefore the report) are byte-stable.
EVAL_CREATED_AT = "2026-01-01T00:00:00Z"


def deal_dirs(split: str, data_root: Path = DATA_ROOT) -> list[Path]:
    """Deal packages in a split that carry an answer key, in sorted order."""
    base = data_root / split
    if not base.is_dir():
        return []
    return sorted(
        d for d in base.iterdir() if d.is_dir() and (d / "deal.yaml").is_file() and (d / GROUND_TRUTH_FILE).is_file()
    )


def evaluate_split(split: str, ai_mode: str, data_root: Path | None = None) -> dict[str, Any]:
    from qoe.ai import get_ai
    from qoe.engine import run_review

    data_root = data_root if data_root is not None else DATA_ROOT
    splits = SPLITS if split == "all" else (split,)
    scores: list[dict[str, Any]] = []
    ai_name = ai_mode
    for s in splits:
        for deal_dir in deal_dirs(s, data_root):
            ai = get_ai(ai_mode)
            ai_name = ai.name
            wp = run_review(deal_dir, ai=ai, run_id=f"eval-{s}-{deal_dir.name}", created_at=EVAL_CREATED_AT)
            scores.append(score(wp, load_ground_truth(deal_dir)))
    return build_report(split, scores, ai_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev", "holdout", "all"), default="dev")
    parser.add_argument("--ai", choices=("rules", "llm"), default="rules")
    parser.add_argument("--out", type=Path, default=None, help="output directory (default: <project>/reports/qoe)")
    parser.add_argument(
        "--data-root", type=Path, default=None, help="folder holding dev/ and holdout/ (default: <project>/data/qoe)"
    )
    args = parser.parse_args(argv)

    data_root = args.data_root if args.data_root is not None else DATA_ROOT
    report = evaluate_split(args.split, args.ai, data_root)
    if not report["deals"]:
        print(f"No deal packages with {GROUND_TRUTH_FILE} under {data_root / args.split}.", file=sys.stderr)
        return 1

    out_dir = args.out if args.out is not None else ROOT / "reports" / "qoe"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"eval_{args.split}.json"
    md_path = out_dir / f"eval_{args.split}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")

    o = report["overall"]

    def pct(key: str) -> str:
        r = o[key]
        return "n/a" if r["rate"] is None else f"{r['rate'] * 100:.1f}% ({r['num']}/{r['den']})"

    print(
        f"Split {args.split}: {len(report['deals'])} deal(s), {o['n_adjustments']} adjustments, AI {report['ai_mode']}"
    )
    print(f"  False accept rate : {pct('false_accept_rate')}")
    print(f"  Missed challenges : {pct('missed_contradictions')}")
    print(f"  Treatment accuracy: {pct('treatment_accuracy')}")
    print(f"  Amount accuracy   : {pct('amount_accuracy')}")
    print(f"  Flag recall       : {pct('flag_recall')}")
    print(f"  Max EBITDA error  : {o['ebitda_error']['max_abs_error']}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print("Automated scores on synthetic data; not practitioner-timed results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
