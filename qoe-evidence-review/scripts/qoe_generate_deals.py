#!/usr/bin/env python3
"""Generate synthetic QoE deal packages from YAML deal specs.

    uv run python scripts/qoe_generate_deals.py --spec data/specs/meridian_mechanical.yaml --out data/dev
    uv run python scripts/qoe_generate_deals.py --all      # every spec, into data/<split>/

The spec format is documented in scripts/qoe_synth/SPEC_FORMAT.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from qoe_synth import GenerationError, generate_deal, load_spec  # noqa: E402
from qoe_synth import summarize  # noqa: E402

SPECS_DIR = ROOT / "data" / "specs"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--spec", type=Path, action="append", help="deal spec YAML (repeatable)")
    which.add_argument("--all", action="store_true", help=f"every *.yaml in {SPECS_DIR.relative_to(ROOT)}")
    parser.add_argument("--out", type=Path, help="output root (default: data/<split from spec>)")
    args = parser.parse_args(argv)

    spec_paths = sorted(SPECS_DIR.glob("*.yaml")) if args.all else args.spec
    if not spec_paths:
        parser.error(f"no specs found in {SPECS_DIR}")
    for path in spec_paths:
        try:
            spec = load_spec(path)
            out_root = args.out or (ROOT / "data" / spec.split)
            result = generate_deal(spec, out_root)
        except GenerationError as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            return 1
        print(summarize(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
