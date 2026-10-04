"""Command line entry point: `nbaprops pull | build | analyze | all`."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone

from nbaprops import config


def _seasons(spec: str) -> list[int]:
    lo, _, hi = spec.partition("-")
    return list(range(int(lo), int(hi or lo) + 1))


def _current_season() -> int:
    today = datetime.now(timezone.utc).date()
    return today.year + 1 if today.month >= 9 else today.year


def cmd_pull(args: argparse.Namespace) -> None:
    from nbaprops.ingest.boxscores import pull_boxscores
    from nbaprops.ingest.props import pull_props
    from nbaprops.ingest.schedule import update_schedule

    box_seasons = _seasons(args.box_seasons)
    prop_seasons = _seasons(args.prop_seasons)
    start = date(min(box_seasons + prop_seasons) - 1, 9, 1)
    end = min(date(max(box_seasons + prop_seasons), 10, 31), datetime.now(timezone.utc).date())
    sched = update_schedule(start, end, workers=args.workers)
    if not args.skip_props:
        pull_props(sched, prop_seasons, workers=args.workers)
    if not args.skip_box:
        pull_boxscores(sched, box_seasons, workers=args.workers)


def cmd_build(args: argparse.Namespace) -> None:
    from nbaprops.build import build_all

    build_all()


def cmd_analyze(args: argparse.Namespace) -> None:
    from nbaprops.analyze import run_analysis

    run_analysis(holdout_season=args.holdout)


def main(argv: list[str] | None = None) -> None:
    config.ensure_dirs()
    cur = _current_season()
    parser = argparse.ArgumentParser(prog="nbaprops", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pull", help="download schedule, box scores and prop lines from ESPN")
    p.add_argument("--box-seasons", default=f"{config.FIRST_BOX_SEASON}-{cur}", help="e.g. 2003-2026 (ESPN season = year it ends)")
    p.add_argument("--prop-seasons", default=f"{config.FIRST_PROP_SEASON}-{cur}")
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--skip-box", action="store_true")
    p.add_argument("--skip-props", action="store_true")
    p.set_defaults(func=cmd_pull)

    b = sub.add_parser("build", help="parse raw downloads into analysis tables")
    b.set_defaults(func=cmd_build)

    a = sub.add_parser("analyze", help="hypothesis tests, strategy backtests, report")
    a.add_argument("--holdout", type=int, default=None, help="season kept out of strategy selection (default: latest)")
    a.set_defaults(func=cmd_analyze)

    allp = sub.add_parser("all", help="pull + build + analyze with defaults")
    allp.set_defaults(func=lambda a: (cmd_pull(parser.parse_args(["pull"])), cmd_build(a), cmd_analyze(parser.parse_args(["analyze"]))))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
