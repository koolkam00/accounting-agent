#!/usr/bin/env python3
"""Write the QoE Evidence Review capacity / margin model to Excel.

Produces ``reports/qoe/commercial_model.xlsx`` with an Assumptions sheet
(inputs, legend, one ILLUSTRATIVE example set) and a Scenarios sheet built
entirely from formulas. Freed hours are capacity, not dollars; see
``qoe/commercial.py`` for how the four scenarios keep them apart.

By default "Your value" is blank, so the workbook shows no result until you
supply your own inputs and a *measured* time reduction:

    uv run python scripts/qoe_commercial_model.py
    uv run python scripts/qoe_commercial_model.py --inputs my_firm.yaml

``my_firm.yaml`` maps input keys (see ``qoe.commercial.INPUT_SPECS``) to a
number, or to ``{value: 0.35, source: "timed pilot, 3 engagements"}``.

The workbook is recalculated with LibreOffice through the xlsx skill's
``recalc.py`` (``--recalc-script`` or env ``QOE_XLSX_RECALC``; otherwise it is
searched for under ``~/.claude/skills``). The run fails on any formula error or
on any disagreement between the workbook and the Python model.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qoe.commercial import (
    LINES,
    SECTIONS,
    STATUS_AWAITING,
    CommercialInputs,
    compare_with_model,
    compute,
    read_back,
    status,
    write_workbook,
)

DEFAULT_OUT = ROOT / "reports" / "qoe" / "commercial_model.xlsx"
HEADLINE = (
    "hours_freed_per_year",
    "equivalent_engagements",
    "margin_lift_per_fixed_fee_engagement",
    "fixed_fee_margin_per_year",
    "hourly_net_margin_per_year",
    "redeployment_value_per_year",
    "hires_avoided",
    "hire_cost_avoided_per_year",
)


def load_inputs(path: Path) -> tuple[CommercialInputs, dict[str, str]]:
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    values: dict[str, object] = {}
    sources: dict[str, str] = {}
    for key, item in raw.items():
        if isinstance(item, dict):
            values[key] = item.get("value")
            if item.get("source"):
                sources[key] = str(item["source"])
        else:
            values[key] = item
    return CommercialInputs.from_mapping(values), sources


def find_recalc_script(explicit: Optional[Path]) -> Optional[Path]:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    env = os.environ.get("QOE_XLSX_RECALC")
    if env and Path(env).is_file():
        return Path(env)
    skills = Path.home() / ".claude" / "skills"
    if skills.is_dir():
        for candidate in sorted(skills.glob("**/xlsx/scripts/recalc.py")):
            return candidate
    return None


def calc_available() -> bool:
    """LibreOffice with its Calc component. Core alone cannot open xlsx, and recalc.py then hangs to its timeout."""
    exe = shutil.which("soffice")
    if exe is None:
        return False
    program = Path(exe).resolve().parent
    return any(program.glob("libsclo.*")) or any(program.parent.glob("Frameworks/libsclo*"))


def recalc(path: Path, script: Path, timeout: int = 90) -> dict:
    proc = subprocess.run(
        [sys.executable, str(script), str(path), str(timeout)],
        capture_output=True,
        text=True,
        timeout=timeout + 60,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": (proc.stderr or proc.stdout or f"recalc exited {proc.returncode}").strip()}


def _show(key: str, value: Optional[Decimal]) -> str:
    if value is None:
        return "n/a"
    line = next(ln for ln in LINES if ln.key == key)
    if line.number_format.startswith("0.0%"):
        return f"{(value * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"
    places = 2 if ".00" in line.number_format else 1 if ".0" in line.number_format else 0
    # Half-up, as Excel displays it (Python's default would show 682.5 as 682).
    shown = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"({abs(shown):,})" if shown < 0 else f"{shown:,}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out", type=Path, default=None, help="output xlsx (default: <project>/reports/qoe/commercial_model.xlsx)"
    )
    parser.add_argument("--inputs", type=Path, default=None, help="YAML with your firm's inputs (default: all blank)")
    parser.add_argument("--recalc-script", type=Path, default=None, help="path to the xlsx skill's recalc.py")
    parser.add_argument("--no-recalc", action="store_true", help="skip LibreOffice recalculation")
    args = parser.parse_args(argv)

    inputs, sources = load_inputs(args.inputs) if args.inputs else (CommercialInputs(), {})
    out = args.out if args.out is not None else DEFAULT_OUT
    rows = write_workbook(out, inputs, sources)
    yours = compute(inputs)
    example = compute(CommercialInputs.illustrative())

    print(f"Wrote {out}")
    print("Capacity is not value: freed salaried hours become value only when redeployed, when cost is")
    print("avoided, or when delivery economics change. Scenarios are alternatives; do not add them.")
    print("")
    your_status = status(inputs)
    print(
        f"Your inputs: {your_status}"
        + (" (no measured time reduction, so no result is shown)" if your_status == STATUS_AWAITING else "")
    )
    print(f"{'Headline line':<76}{'Your inputs':>14}{'ILLUSTRATIVE':>16}")
    for key in HEADLINE:
        line = next(ln for ln in LINES if ln.key == key)
        label = f"{line.ref} {line.label}"
        print(f"{label[:75]:<76}{_show(key, yours[key]):>14}{_show(key, example[key]):>16}")
    print("ILLUSTRATIVE figures use example inputs only; they are not a measured or forecast result.")
    print(f"Sections: {'; '.join(title for title, _ in SECTIONS.values())}")

    if args.no_recalc:
        print("Skipped recalculation; Excel will calculate formulas on open.")
        return 0
    if not calc_available():
        print("LibreOffice Calc not found; not recalculated. Excel will calculate formulas on open.")
        return 0
    script = find_recalc_script(args.recalc_script)
    if script is None:
        print("recalc.py not found (pass --recalc-script or set QOE_XLSX_RECALC); Excel will calculate on open.")
        return 0
    result = recalc(out, script)
    if "error" in result:
        print(f"Recalculation failed: {result['error']}", file=sys.stderr)
        return 1
    print(
        f"LibreOffice recalc: {result.get('status')}, {result.get('total_formulas')} formulas, "
        f"{result.get('total_errors')} errors"
    )
    if result.get("total_errors"):
        print(json.dumps(result.get("error_summary"), indent=2), file=sys.stderr)
        return 1
    cached = read_back(out, rows)
    problems = compare_with_model(cached["your"], yours) + compare_with_model(cached["illustrative"], example)
    if problems:
        print("Workbook disagrees with the Python model:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("Workbook values agree with the Python model (both columns).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
