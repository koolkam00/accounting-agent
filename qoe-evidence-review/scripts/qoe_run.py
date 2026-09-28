#!/usr/bin/env python3
"""Run a QoE evidence review on one deal package.

Writes ``<out>/<deal>/workpaper.json``, where ``<deal>`` is the deal id made
path-safe (``qoe.engine.deal_dir_name``): a deal id is input data and is never
used raw in a path. The reviewer's logs beside it are applied: decisions from
``review_log.jsonl`` (the bridge is rebuilt with the reviewer's final amounts,
from management's schedule in the deal package) and question status changes,
management responses and reviewer-raised questions from
``question_log.jsonl``, also when only the question log has entries.
``--xlsx`` exports the Excel workpaper beside it with the deal package's GL
detail and the question log, then recalculates a copy with LibreOffice (when
available) and reports the formula count, any formula errors, and the
Cover's Workbook checks. Prints a short console summary.

Exit status: 0 on success, 2 when --deal is not a deal package, 1 when the
exported workbook recalculates with formula errors or its Workbook checks
show a difference.

Usage:
    uv run python scripts/qoe_run.py --deal data/dev/meridian_mechanical --xlsx
    uv run python scripts/qoe_run.py --deal <dir> --ai llm --run-id r1 --created-at 2026-01-01T00:00:00Z
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qoe.money import D
from qoe.schemas import DealPackage, Severity, Treatment, Workpaper

REVIEW_LOG = "review_log.jsonl"
QUESTION_LOG = "question_log.jsonl"
DILIGENCE_SOURCE = "diligence"
TOP_FLAGS = 8
WORKBOOK_CHECKS = "Workbook checks"  # the Cover's overall check status (qoe.export_xlsx.workbook_check_status)
SOURCE_AGREEMENT = "Agreement to source data"  # the Cover line comparing management's own figures; informational
_SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}


_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _local_deal_dir_name(deal_id: str) -> str:
    """Fallback for ``qoe.engine.deal_dir_name`` (same rule): one safe path component, never a path,
    '.' or '..': unsafe characters become '_' and leading dots are dropped."""
    name = _UNSAFE_NAME.sub("_", (deal_id or "").strip()).lstrip(".")
    if not name.strip("_"):
        raise ValueError(f"deal_id {deal_id!r} has no characters usable in a directory name")
    return name


def deal_dir_name(deal_id: str) -> str:
    """The deal's workpaper directory / file-name token: ``qoe.engine.deal_dir_name`` when the
    engine provides it, else the same rule locally."""
    try:
        from qoe.engine import deal_dir_name as engine_name
    except ImportError:
        engine_name = None
    return (engine_name or _local_deal_dir_name)(deal_id)


def _deal_path(arg: str) -> Path:
    """A relative --deal resolves against the cwd first, then the project root."""
    p = Path(arg)
    if p.is_absolute() or p.exists():
        return p
    return ROOT / p


def _money(value: Optional[str]) -> str:
    if value is None or value == "":
        return "-"
    d = D(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"({abs(d):,})" if d < 0 else f"{d:,}"


def _row(wp: Workpaper, key: str) -> dict[str, str]:
    for row in wp.bridge.rows:
        if row.key == key:
            return row.amounts
    return {}


def summarize(wp: Workpaper) -> str:
    """Bridge headline, treatments, and the most severe flags."""
    labels = [p.label for p in wp.deal.periods]
    reviewed = {r.adj_id for r in wp.reviews}
    out: list[str] = []
    out.append(f"{wp.deal.target_name} [{wp.deal.deal_id}]  run {wp.run_id}  AI {wp.ai_mode}  tool {wp.tool_version}")
    if wp.deal.synthetic:
        out.append("SYNTHETIC deal package")
    out.append("")
    width = max([14, *(len(label) + 2 for label in labels)])
    out.append(f"{'EBITDA bridge (USD)':<44}" + "".join(f"{label:>{width}}" for label in labels))
    for key, label in (
        ("gl_ebitda", "Reported EBITDA (per GL)"),
        ("mgmt_reported_ebitda", "Reported EBITDA (per management)"),
        ("mgmt_adjusted_ebitda", "Management adjusted EBITDA"),
        ("diligence_adjusted_ebitda", "Diligence adjusted EBITDA"),
        ("pending", "Memo: pending information (excluded)"),
    ):
        amounts = _row(wp, key)
        if amounts:
            out.append(f"{label:<44}" + "".join(f"{_money(amounts.get(p)):>{width}}" for p in labels))
    out.append("")

    mgmt = [a for a in wp.assessments if a.source != DILIGENCE_SOURCE]
    items = [a for a in wp.assessments if a.source == DILIGENCE_SOURCE]
    counts = Counter(a.treatment for a in mgmt)
    out.append(
        "Tool treatments: "
        + ", ".join(f"{t.value} {counts.get(t, 0)}" for t in Treatment)
        + f"  (reviewed {len(reviewed & {a.adj_id for a in mgmt})}/{len(mgmt)})"
    )

    def line(a) -> str:
        claimed = " / ".join(_money(a.claimed.get(p)) for p in labels)
        proposed = " / ".join(_money(a.proposed.get(p)) for p in labels) if a.proposed else "pending"
        status = "reviewed" if a.adj_id in reviewed else "unreviewed"
        return (
            f"  {a.adj_id:<8} {a.treatment.value:<12} {a.confidence:<6} claimed {claimed}  ->  proposed {proposed}"
            f"  [{status}]  {a.title}"
        )

    out.extend(line(a) for a in mgmt)
    if items:
        out.append(
            f"Diligence-identified items (not on management's schedule): {len(items)}"
            f"  (reviewed {len(reviewed & {a.adj_id for a in items})}/{len(items)})"
        )
        out.extend(line(a) for a in items)
    out.append("")

    flags = [(a.adj_id, f) for a in wp.assessments for f in a.flags if f.severity != Severity.INFO]
    flags.sort(key=lambda item: _SEVERITY_ORDER[item[1].severity])
    out.append(f"Top flags ({len(flags)} warning/critical):")
    for adj_id, f in flags[:TOP_FLAGS]:
        out.append(f"  {f.severity.value:<8} {adj_id:<8} {f.code.value}: {f.message}")
    if len(flags) > TOP_FLAGS:
        out.append(f"  ... {len(flags) - TOP_FLAGS} more in the workpaper")
    issues = Counter(i.code.value for i in wp.reconciliation.issues)
    if issues:
        out.append("Data quality: " + ", ".join(f"{code} {n}" for code, n in sorted(issues.items())))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deal", required=True, help="deal package directory")
    parser.add_argument("--ai", choices=("rules", "llm"), default="rules")
    parser.add_argument("--out", type=Path, default=None, help="workpaper root (default: <project>/workpapers)")
    parser.add_argument("--xlsx", action="store_true", help="also export the Excel workpaper")
    parser.add_argument(
        "--no-recalc", action="store_true", help="skip the LibreOffice recalculation check of the exported workbook"
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--created-at", default=None, help="ISO 8601 timestamp to stamp on the run")
    args = parser.parse_args(argv)

    from qoe.ai import get_ai
    from qoe.engine import run_review, save_workpaper

    deal_dir = _deal_path(args.deal)
    if not (deal_dir / "deal.yaml").is_file():
        print(f"Not a deal package (no deal.yaml): {deal_dir}", file=sys.stderr)
        return 2
    out_root = args.out if args.out is not None else ROOT / "workpapers"

    wp = run_review(deal_dir, ai=get_ai(args.ai), run_id=args.run_id, created_at=args.created_at)
    try:
        safe_name = deal_dir_name(wp.deal.deal_id)
    except ValueError as exc:
        print(f"Cannot name the workpaper directory: {exc}", file=sys.stderr)
        return 2
    wp_dir = out_root / safe_name
    log_path = wp_dir / REVIEW_LOG
    question_path = wp_dir / QUESTION_LOG
    decisions: list = []
    questions: list = []
    if log_path.is_file() or question_path.is_file():
        from qoe.review_store import ReviewStore

        store = ReviewStore(log_path, question_path)
        decisions = store.all()
        questions = store.questions()
        for name, skipped in ((log_path.name, store.skipped_lines), (question_path.name, store.skipped_question_lines)):
            if skipped:
                print(f"Note: {name} line(s) {', '.join(map(str, skipped))} could not be read and were skipped "
                      "(the log is never rewritten).", file=sys.stderr)
    reviewed = bool(decisions or questions)
    pkg = _load_package(deal_dir) if reviewed or args.xlsx else None
    if reviewed:
        from qoe.review_store import apply_reviews

        wp = apply_reviews(wp, decisions, schedule=pkg.schedule if pkg is not None else None, question_log=questions)
    wp_path = save_workpaper(wp, out_root)
    if wp_path.parent.resolve() != wp_dir.resolve():
        print(f"Note: the workpaper was saved to {wp_path.parent}, not {wp_dir}; the logs and the workbook "
              f"are read from and written to {wp_dir}.", file=sys.stderr)

    print(summarize(wp))
    print("")
    print(f"Workpaper: {wp_path}")
    if decisions:
        print(f"Review log applied: {log_path} ({len(decisions)} decision(s))")
    if questions:
        print(f"Question log applied: {question_path} ({len(questions)} entr{'y' if len(questions) == 1 else 'ies'})")
    status = 0
    if args.xlsx:
        from qoe.export_xlsx import export_workpaper

        xlsx_path = export_workpaper(
            wp, wp_dir / f"QoE_Evidence_Review_{safe_name}.xlsx", pkg=pkg, question_log=questions
        )
        print(f"Excel workpaper: {xlsx_path}")
        if not args.no_recalc:
            status = _recalc_report(xlsx_path)
    return status


def _load_package(deal_dir: Path) -> Optional[DealPackage]:
    """The deal package for GL detail and management's schedule; None (with a note) if it cannot load."""
    from qoe.ingest import load_deal

    try:
        return load_deal(deal_dir)
    except Exception as exc:  # noqa: BLE001 - the review already ran; export without GL detail
        print(f"Note: deal package could not be reloaded ({type(exc).__name__}: {exc}); "
              "exporting without GL detail.", file=sys.stderr)
        return None


def _recalc_report(xlsx_path: Path) -> int:
    """Recalculate with LibreOffice and print the formula count, formula errors, and the Cover's
    check statuses; 1 if any formula errors or the Workbook checks show a difference.

    LibreOffice rewrites the file it recalculates, so it works on a temporary copy: the delivered
    workbook stays exactly as exported (Excel recalculates it on open). The check statuses are
    read from that recalculated copy.
    """
    import shutil
    import tempfile

    from qoe.export_xlsx import recalc_and_check

    checks: Optional[dict[str, Optional[str]]] = None
    check_error = ""
    with tempfile.TemporaryDirectory(prefix="qoe_recalc_") as tmp:
        copy = Path(tmp) / xlsx_path.name
        shutil.copy(xlsx_path, copy)
        result = recalc_and_check(copy, timeout=180)
        if result.get("status") != "skipped" and "error" not in result:
            try:
                from qoe.export_xlsx import workbook_check_status

                checks = workbook_check_status(copy)
            except Exception as exc:  # noqa: BLE001 - reporting only; the formula check above still stands
                check_error = f"{type(exc).__name__}: {exc}"
    if result.get("status") == "skipped":
        print(f"Recalculation skipped: {result.get('reason')}")
        return 0
    if "error" in result:
        print(f"Recalculation failed: {result['error']}", file=sys.stderr)
        return 1
    errors = int(result.get("total_errors", 0) or 0)
    print(f"Recalculated with LibreOffice: {result.get('total_formulas', 0)} formulas, {errors} formula error(s)")
    status = 0
    if errors:
        for kind, detail in sorted((result.get("error_summary") or {}).items()):
            where = detail.get("locations", [])[:5] if isinstance(detail, dict) else detail
            count = detail.get("count", "") if isinstance(detail, dict) else ""
            print(f"  {kind} {count}: {', '.join(map(str, where))}")
        status = 1
    if checks is None:
        print(f"Workbook checks: not read from the recalculated copy ({check_error or 'no Cover checks found'})")
        return status
    overall = checks.get(WORKBOOK_CHECKS)
    print(f"Workbook checks: {overall if overall is not None else 'no value after recalculation'}")
    source = [(area, value) for area, value in checks.items() if area.startswith(SOURCE_AGREEMENT)]
    for area, value in checks.items():
        if area != WORKBOOK_CHECKS and (area, value) not in source and value != "OK":
            print(f"  {area}: {value if value is not None else 'no value'}")
    for area, value in source:
        # Management's own figures vs the GL: a difference is in the source data (see Data Quality), not the workbook.
        print(f"{area}: {value if value is not None else 'no value'} (not a workbook check)")
    if overall != "OK":
        status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
