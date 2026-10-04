"""Render reports/report.html from the CSVs that analyze.py writes.

The page is self-contained: data is embedded as JSON and drawn with a little vanilla
JS into SVG, so it opens offline and re-renders for any width and either theme. All
copy that depends on the numbers is generated here, so a rerun rewrites the story.
"""

from __future__ import annotations

import json
import math
from html import escape

import numpy as np
import pandas as pd

from nbaprops import config

BREAKEVEN = 110 / 210
GROUP_LABELS = {"core5": "Core 5 pooled", "all": "All markets pooled"}


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not math.isfinite(float(obj)) else round(float(obj), 6)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def season_label(s: int) -> str:
    return f"{s - 1}-{str(s)[-2:]}"


def pct(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def spct(x: float, d: int = 1) -> str:
    return f"{'+' if x >= 0 else '−'}{abs(x) * 100:.{d}f}%"


def pts(x: float, d: int = 1) -> str:
    return f"{abs(x) * 100:.{d}f}"


def signed(x: float, d: int = 3) -> str:
    return f"{'+' if x >= 0 else '−'}{abs(x):.{d}f}"


def join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def mlabel(m: str) -> str:
    return config.MARKET_LABELS.get(m, GROUP_LABELS.get(m, m))


def collect(summary: dict) -> dict:
    r = config.REPORTS
    thesis = pd.read_csv(r / "thesis_by_market.csv")
    thesis_open = pd.read_csv(r / "thesis_by_market_vs_open.csv")
    streak_roi = pd.read_csv(r / "streak_roi.csv")
    adjust = pd.read_csv(r / "book_adjustment.csv")
    history = pd.read_csv(r / "naive_line_history.csv")
    strategies = pd.read_csv(r / "strategy_results.csv")
    strategies["params"] = strategies["params"].fillna("")
    wf = pd.read_csv(r / "walk_forward.csv")
    coverage = pd.read_csv(r / "coverage.csv")
    quality = pd.read_csv(r / "line_quality.csv")
    calib = pd.read_csv(r / "side_calibration.csv")
    seasons = summary["seasons"]

    def pick(**kw) -> pd.DataFrame:
        m = np.ones(len(strategies), bool)
        for k, v in kw.items():
            m &= (strategies[k] == v).to_numpy()
        return strategies[m]

    def rows_for(df: pd.DataFrame, extra: list[str]) -> list[dict]:
        out = []
        for _, row in df.iterrows():
            rec = {"market": row["market"], "label": mlabel(row["market"]), **{k: row[k] for k in extra}}
            for s in seasons:
                rec[f"roi_{s}"] = row.get(f"roi_{s}")
                rec[f"bets_{s}"] = row.get(f"bets_{s}")
            out.append(rec)
        return out

    order = config.CORE_MARKETS + ["core5"] + [m for m in config.EXTRA_MARKETS] + ["all"]
    thesis_bets = pick(family="reversal", variant="both", params="streak=1,margin_z=0.0")
    thesis_bets = thesis_bets.assign(_o=thesis_bets["market"].map({m: i for i, m in enumerate(order)})).sort_values(["book_mode", "timing", "_o"], ascending=[False, True, True])
    baselines = pick(family="baseline")
    baselines = baselines.assign(_o=baselines["market"].map({m: i for i, m in enumerate(order)})).sort_values(["variant", "book_mode", "timing", "_o"], ascending=[False, False, True, True])

    eligible = strategies[strategies["train_bets"] >= 300]
    scatter = eligible[eligible["test_bets"] >= 100][["strategy_id", "label", "family", "train_roi", "test_roi", "train_bets", "test_bets"]]
    top = eligible[eligible["test_bets"] >= 50].sort_values("train_roi", ascending=False).head(15)
    robust = eligible[(eligible["test_bets"] >= 50) & (eligible["train_t"] >= 2.0)].sort_values("train_t", ascending=False).head(15)

    hist_rows = []
    for market, g in history.groupby("market"):
        real = g[~g["placebo"]].set_index("season")
        plac = g[g["placebo"]].set_index("season")
        for season in sorted(set(real.index) & set(plac.index)):
            hist_rows.append(
                {
                    "market": market,
                    "season": int(season),
                    "real": real.loc[season, "p_below_after_above"],
                    "placebo": plac.loc[season, "p_below_after_above"],
                    "diff": real.loc[season, "p_below_after_above"] - plac.loc[season, "p_below_after_above"],
                    "n": int(real.loc[season, "n"]),
                }
            )

    fdr = strategies[strategies["fdr_discovery_train"]]
    fdr_test = fdr[fdr["test_bets"] > 0]
    fdr_stats = {
        "n": int(len(fdr)),
        "n_best_open": int(((fdr["book_mode"] == "best") & (fdr["timing"] == "open")).sum()),
        "n_unders": int(fdr["label"].str.contains("under", case=False).sum()),
        "holdout_roi": float((fdr_test["test_roi"] * fdr_test["test_bets"]).sum() / fdr_test["test_bets"].sum()) if len(fdr_test) else None,
        "holdout_share_positive": float((fdr_test["test_roi"] > 0).mean()) if len(fdr_test) else None,
    }
    rc = summary["reality_check"]
    best = strategies.loc[strategies["strategy_id"] == rc["best_row"]].iloc[0]
    twin = pick(family=best["family"], variant=best["variant"], params=best["params"], market=best["market"], timing=best["timing"])
    twin = twin[twin["book_mode"] != best["book_mode"]]

    return _clean(
        {
            "summary": summary,
            "breakeven": BREAKEVEN,
            "seasons": seasons,
            "season_labels": {str(s): season_label(s) for s in range(2003, max(seasons) + 1)},
            "holdout": summary["holdout"],
            "thesis": thesis.assign(label=thesis["market"].map(mlabel)).to_dict("records"),
            "thesis_open": thesis_open.assign(label=thesis_open["market"].map(mlabel)).to_dict("records"),
            "streak_roi": streak_roi[streak_roi["timing"] == "close"].to_dict("records"),
            "adjust": adjust.assign(label=adjust["market"].map(mlabel)).to_dict("records"),
            "history": hist_rows,
            "thesis_bets": rows_for(thesis_bets, ["timing", "book_mode", "bets", "hit_rate", "breakeven", "roi", "units", "t"]),
            "baselines": rows_for(baselines, ["variant", "timing", "book_mode", "bets", "hit_rate", "breakeven", "roi"]),
            "scatter": scatter.assign(top=scatter["strategy_id"].isin(set(top["strategy_id"]))).drop(columns="strategy_id").to_dict("records"),
            "top": top[["label", "train_bets", "train_roi", "train_t", "test_bets", "test_roi"]].to_dict("records"),
            "robust": robust[["label", "train_bets", "train_roi", "train_t", "test_bets", "test_roi"]].to_dict("records"),
            "walk_forward": wf.to_dict("records"),
            "coverage": coverage.to_dict("records"),
            "quality": quality.to_dict("records"),
            "calibration": calib.to_dict("records"),
            "best": {"label": best["label"], "book_mode": best["book_mode"], "train_bets": best["train_bets"]},
            "fdr": fdr_stats,
            "best_twin": twin[["label", "train_roi", "train_bets", "test_roi", "test_bets"]].to_dict("records"),
            "n_books": int(coverage["book_family"].nunique()),
            "markets": config.ALL_MARKETS,
            "core": config.CORE_MARKETS,
            "labels": config.MARKET_LABELS,
        }
    )


def narrative(d: dict) -> dict:
    """The words that depend on the numbers."""
    th = {t["market"]: t for t in d["thesis"]}
    counting = [th[m] for m in ("pts", "reb", "ast") if m in th]
    tail = [th[m] for m in ("stl", "blk") if m in th]
    be = d["breakeven"]
    holdout = season_label(d["holdout"])
    first = season_label(d["seasons"][0])
    pre = season_label(d["holdout"] - 1)
    w: dict[str, str] = {}

    uo = [t["p_under_after_over"] for t in counting]
    uu = [t["p_under_after_under"] for t in counting]
    max_eff = max(abs(t["reversal_effect"]) for t in counting)
    sig = [t for t in counting if t["reversal_p_value"] < 0.05 and t["reversal_effect"] > 0]
    thesis_holds = bool(sig) and max(uo) > be
    w["verdict"] = "Some support" if thesis_holds else "No"
    w["answer"] = (
        f"{'Partly.' if thesis_holds else 'No.'} After a player goes over his line, the under hits {pct(min(uo))} to {pct(max(uo))} of the time "
        f"next game for points, rebounds and assists. After an under, it hits {pct(min(uu))} to {pct(max(uu))}. "
        f"Last game's result shifts the next one by less than {pts(max_eff)} percentage points."
    )
    tail_raw_neg = all(t["reversal_effect"] < 0 for t in tail)
    tail_adj_small = all(abs(t["price_adj_effect"]) < 0.015 for t in tail)
    if tail and tail_raw_neg and tail_adj_small:
        w["tail"] = (
            "Steals and blocks look like the opposite of the thesis in the raw numbers: unders hit less often after an over. "
            "The odds already account for that. Compared against each bet's own price, last game's result adds about nothing in any of the five stats."
        )
    else:
        w["tail"] = "Steals and blocks are compared against each bet's own price below, because their lines sit at 0.5 or 1.5 and are priced through the juice."

    tb = next((b for b in d["thesis_bets"] if b["market"] == "core5" and b["timing"] == "close" and b["book_mode"] == "single"), None)
    tb_best = next((b for b in d["thesis_bets"] if b["market"] == "core5" and b["timing"] == "open" and b["book_mode"] == "best"), None)
    w["slip"] = tb
    if tb:
        w["bet_line"] = (
            f"Betting it anyway on all five stats, against last game's result at a single book's closing line: {tb['bets']:,} bets, "
            f"a {pct(tb['hit_rate'])} hit rate against {pct(tb['breakeven'])} needed, and {spct(tb['roi'])} on every dollar staked."
        )
        if tb_best:
            w["bet_line"] += f" Shopping the best opening line across every book in the feed only trims the loss to {spct(tb_best['roi'])}."
    else:
        w["bet_line"] = ""

    adj = {a["market"]: a for a in d["adjust"]}
    c_adj = [adj[m] for m in ("pts", "reb", "ast") if m in adj]
    if c_adj:
        moves = [a["line_move_per_sd"] for a in c_adj]
        nxt = [a["next_margin_per_sd"] for a in c_adj]
        all_ns = all(a["next_margin_p_value"] > 0.05 for a in c_adj)
        w["adjust"] = (
            f"After a big game the books raise the next line by about {min(moves):.2f} to {max(moves):.2f} standard deviations for every SD the player beat his last line by. "
            f"For points, rebounds and assists the next result then lands right on the new line (slopes {signed(min(nxt))} to {signed(max(nxt))}"
            + (", none statistically different from zero)." if all_ns else ").")
            + " The thesis needs the books to overreact. They don't."
        )
        carry = [adj[m] for m in ("stl", "blk", "fg3m") if m in adj and adj[m]["next_margin_per_sd"] > 0 and adj[m]["next_margin_p_value"] < 0.05]
        if carry:
            w["adjust"] += " For " + join([mlabel(a["market"]).lower() for a in carry]) + ", results carry past the new line, the opposite of what the thesis needs (the odds, not the line, absorb most of it)."
    else:
        w["adjust"] = ""

    hist = [h for h in d["history"] if h["market"] in ("pts", "reb", "ast")]
    if hist:
        neg = sum(1 for h in hist if h["diff"] < 0)
        avg = float(np.mean([h["diff"] for h in hist]))
        n_seasons = len({h["season"] for h in hist})
        w["history"] = (
            f"In {neg} of {len(hist)} season-stat pairs across {n_seasons} seasons, the opposite of reversal shows up: an above-average game makes the next game "
            f"more likely to be above average too, by {pts(abs(avg))} percentage points on average for points, rebounds and assists. Roles and minutes carry over from game to game."
            if avg < 0
            else f"Raw stats do bounce back: after an above-average game, the next is below average {pts(avg)} points more often than chance, on average."
        )
    else:
        w["history"] = ""

    rc = d["summary"]["reality_check"]
    twin = d["best_twin"][0] if d["best_twin"] else None
    s = f"Across {d['summary']['n_strategies']:,} strategy variants, the best on {first} to {pre} was “{d['best']['label']}”: {spct(rc['best_roi'])} on {d['best']['train_bets']:,} bets. "
    if rc["p_value"] < 0.10:
        s += f"That is more than luck alone would produce from this many tries (Reality Check p = {rc['p_value']:.2f}). "
        if twin and d["best"]["book_mode"] == "best":
            s += f"But it depends on shopping every book's line: at a single book the same bet returned {spct(twin['train_roi'])} over the same seasons. "
    else:
        s += f"That is about what luck alone produces when you try this many ideas (Reality Check p = {rc['p_value']:.2f}). "
    s += f"On {holdout}, which it never saw, it returned {spct(rc['best_test_roi'])} on {rc['best_test_bets']:,} bets."
    fdr = d["fdr"]
    if fdr["n"] and fdr["holdout_roi"] is not None:
        same = fdr["n_best_open"]
        s += (
            f" {fdr['n']:,} strategies pass a 10% false-discovery screen on the earlier seasons"
            + (f", and {same:,} of them are versions of one bet: shopping every book's opening line" + (", mostly on unders." if fdr["n_unders"] > fdr["n"] / 2 else ".") if same >= 0.8 * fdr["n"] else ".")
            + f" Together they returned {spct(fdr['holdout_roi'])} on {holdout}, and {pct(fdr['holdout_share_positive'], 0)} of them made money."
        )
    w["search"] = s

    wf = d["walk_forward"]
    if wf:
        lost = sum(1 for r in wf if r["pick_test_roi"] is not None and r["pick_test_roi"] < 0)
        w["walk"] = f"In {lost} of {len(wf)} tries, the strategy that had worked best so far lost money the next season."
    else:
        w["walk"] = ""

    base = {(b["variant"], b["market"], b["timing"], b["book_mode"]): b for b in d["baselines"]}
    u = base.get(("all_unders", "core5", "close", "single"))
    o = base.get(("all_overs", "core5", "close", "single"))
    if u and o:
        w["base"] = (
            f"Unders lose less than overs: {spct(u['roi'])} against {spct(o['roi'])} at a single book's close across the five core stats. "
            "That's the familiar lean of prop markets, and it explains why every “bet the under after…” idea looks better than its “bet the over” twin. "
            + ("It still doesn't beat the vig at one book." if u["roi"] < 0 else "")
        )
    else:
        w["base"] = ""
    return w


PAGE_CSS = r"""
/* Layout: one reading column for prose, a wider column for figures; a graded bet slip up top. */
:root {
  --bg: #eef0ef;
  --card: #fcfcfb;
  --ink: #0b0b0b;
  --ink-2: #52514e;
  --muted: #6f6e69;
  --rule: #e1e0d9;
  --axis: #c3c2b7;
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --deemph: #b4b3ad;
  --good: #006300;
  --bad: #c22f2f;
  --slip: #fffefa;
  --font-display: "Barlow Condensed", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif;
  --font-body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --step-0: 1rem;
  --step-1: 1.3rem;
  --step-2: 1.85rem;
  --step-3: clamp(2.3rem, 6vw, 3.8rem);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0d0d0d; --card: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #9a9890;
    --rule: #2c2c2a; --axis: #4a4a46; --series-1: #3987e5; --series-2: #d95926; --deemph: #5c5b57;
    --good: #0ca30c; --bad: #e66767; --slip: #21211f; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0d0d0d; --card: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #9a9890;
  --rule: #2c2c2a; --axis: #4a4a46; --series-1: #3987e5; --series-2: #d95926; --deemph: #5c5b57;
  --good: #0ca30c; --bad: #e66767; --slip: #21211f; color-scheme: dark;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: var(--step-0); line-height: 1.55; }
.page { max-width: 68rem; margin: 0 auto; padding-inline: clamp(16px, 4vw, 40px); padding-block: 2.5rem 4rem; display: grid; gap: 3.25rem; }
.page > * { min-width: 0; }
.prose { max-width: 42rem; }
h1, h2, h3 { font-family: var(--font-display); text-wrap: balance; line-height: 1.05; margin: 0; }
h1 { font-size: var(--step-3); font-weight: 700; text-transform: uppercase; letter-spacing: 0.01em; }
h2 { font-size: var(--step-2); font-weight: 600; text-transform: uppercase; letter-spacing: 0.01em; }
h3 { font-size: var(--step-1); font-weight: 600; }
p { margin: 0; }
.eyebrow { font-family: var(--font-mono); font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.stack { display: grid; gap: 1rem; }
.stack > * { min-width: 0; }
.lede { font-size: 1.16rem; }
.muted { color: var(--ink-2); }
.small { font-size: 0.84rem; }
a { color: inherit; text-decoration-color: var(--series-2); text-underline-offset: 3px; }
code { font-family: var(--font-mono); font-size: 0.88em; }

.hero { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr); gap: 2.5rem; align-items: start; }
@media (max-width: 780px) { .hero { grid-template-columns: minmax(0, 1fr); } }
.slip { position: relative; background: var(--slip); border: 1px solid var(--rule); border-radius: 4px; padding: 1.5rem 1.4rem 1.25rem; font-family: var(--font-mono); font-size: 0.84rem;
  box-shadow: 0 12px 30px -20px rgba(0, 0, 0, 0.45); }
.slip::before, .slip::after { content: ""; position: absolute; left: 0; right: 0; height: 8px;
  background: radial-gradient(circle at 6px 0, var(--bg) 4.5px, transparent 5px) repeat-x; background-size: 12px 8px; }
.slip::before { top: -1px; }
.slip::after { bottom: -1px; transform: scaleY(-1); }
.slip .head { display: grid; gap: 0.15rem; margin-bottom: 0.7rem; padding-right: 5.5rem; }
.slip .title { font-family: var(--font-display); font-size: 1.35rem; font-weight: 600; text-transform: uppercase; line-height: 1.1; }
.slip .sub { color: var(--muted); font-size: 0.76rem; }
.slip .row { display: flex; justify-content: space-between; gap: 1rem; padding-block: 0.32rem; border-bottom: 1px dotted var(--axis); }
.slip .row:last-child { border-bottom: 0; }
.slip .k { color: var(--muted); }
.slip .v { font-variant-numeric: tabular-nums; text-align: right; }
.stamp { position: absolute; right: 1rem; top: 1.1rem; transform: rotate(-9deg); border: 2px solid var(--bad); color: var(--bad); border-radius: 4px;
  font-family: var(--font-display); font-weight: 700; font-size: 1.3rem; letter-spacing: 0.08em; padding: 0.05rem 0.55rem; text-transform: uppercase; }
.stamp.won { border-color: var(--good); color: var(--good); }

.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; }
.kpi { background: var(--card); padding: 1rem 1.1rem; display: grid; gap: 0.2rem; align-content: start; }
.kpi .label { font-size: 0.82rem; color: var(--ink-2); }
.kpi .value { font-family: var(--font-display); font-size: 2.05rem; font-weight: 600; line-height: 1; }
.kpi .note { font-size: 0.78rem; color: var(--muted); }

figure { margin: 0; background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 1.1rem 1.1rem 0.9rem; display: grid; gap: 0.75rem; min-width: 0; }
figcaption { display: grid; gap: 0.25rem; }
figcaption .t { font-weight: 600; }
figcaption .s { color: var(--ink-2); font-size: 0.88rem; }
.chart { width: 100%; min-width: 0; position: relative; }
.chart svg { display: block; width: 100%; height: auto; overflow: visible; }
.legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem; font-size: 0.84rem; color: var(--ink-2); }
.legend span { display: inline-flex; align-items: center; gap: 0.45rem; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.legend i.line { width: 16px; height: 2px; border-radius: 1px; }
.fig-foot { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem 1rem; flex-wrap: wrap; }
.toggle { font: inherit; font-size: 0.82rem; color: var(--ink-2); background: transparent; border: 1px solid var(--rule); border-radius: 999px; padding: 0.2rem 0.85rem; cursor: pointer; }
.toggle:hover { border-color: var(--axis); color: var(--ink); }
.toggle:focus-visible, summary:focus-visible, .row-hit:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }
.multiples { display: grid; grid-template-columns: repeat(auto-fit, minmax(14.5rem, 1fr)); gap: 1rem 1.25rem; }
.multiples .panel { min-width: 0; }
.multiples .panel h4 { margin: 0 0 0.25rem; font-size: 0.9rem; font-weight: 600; }

.ax text, .lbl { fill: var(--muted); font-family: var(--font-body); font-size: 11px; font-variant-numeric: tabular-nums; }
.lbl-ink { fill: var(--ink-2); font-family: var(--font-body); font-size: 12px; }
.grid line { stroke: var(--rule); stroke-width: 1; }
.base-line { stroke: var(--axis); stroke-width: 1; }
.ref-line { stroke: var(--ink-2); stroke-width: 1; }
.ref-text { fill: var(--ink-2); font-family: var(--font-body); font-size: 11px; }
.s1 { fill: var(--series-1); } .s2 { fill: var(--series-2); } .sd { fill: var(--deemph); }
.l1 { stroke: var(--series-1); stroke-width: 2; fill: none; stroke-linejoin: round; stroke-linecap: round; }
.l2 { stroke: var(--series-2); stroke-width: 2; fill: none; stroke-linejoin: round; stroke-linecap: round; }
.conn { stroke: var(--axis); stroke-width: 2; }
.ring { stroke: var(--card); stroke-width: 2; }
.whisk1 { stroke: var(--series-1); stroke-width: 2; } .whisk2 { stroke: var(--series-2); stroke-width: 2; }
.hit { fill: transparent; cursor: crosshair; }
.row-hit { fill: transparent; }
.row-hit:hover, .row-hit:focus { fill: var(--rule); fill-opacity: 0.5; }
.xhair { stroke: var(--axis); stroke-width: 1; }
#tip { position: fixed; z-index: 10; pointer-events: none; background: var(--card); color: var(--ink); border: 1px solid var(--rule); border-radius: 6px;
  padding: 0.5rem 0.65rem; font-size: 0.82rem; box-shadow: 0 8px 24px -12px rgba(0, 0, 0, 0.45); max-width: min(24rem, calc(100vw - 16px)); display: grid; gap: 0.2rem; }
#tip .h { color: var(--ink-2); font-size: 0.78rem; }
#tip .r { display: flex; align-items: center; gap: 0.45rem; }
#tip .r b { font-variant-numeric: tabular-nums; }
#tip .r i { display: inline-block; width: 12px; height: 2px; border-radius: 1px; flex: none; }

.tbl-wrap { overflow-x: auto; border: 1px solid var(--rule); border-radius: 6px; background: var(--card); max-height: 32rem; overflow-y: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
th, td { padding: 0.45rem 0.7rem; text-align: right; white-space: nowrap; border-bottom: 1px solid var(--rule); font-variant-numeric: tabular-nums; }
th:first-child, td:first-child { text-align: left; }
td.wrap { white-space: normal; min-width: 18rem; text-align: left; }
th { font-weight: 600; color: var(--ink-2); font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.04em; background: var(--card); position: sticky; top: 0; z-index: 1; }
tr:last-child td { border-bottom: 0; }
.pos { color: var(--good); } .neg { color: var(--bad); }
.flag { color: var(--bad); }

.cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); gap: 1.25rem; }
.cols > * { min-width: 0; }
.note-box { border-left: 3px solid var(--series-2); padding: 0.15rem 0 0.15rem 0.9rem; color: var(--ink-2); }
ul.method { margin: 0; padding-left: 1.2rem; display: grid; gap: 0.5rem; max-width: 46rem; }
pre { margin: 0; background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 0.9rem 1rem; overflow-x: auto; font-family: var(--font-mono); font-size: 0.84rem; }
details summary { cursor: pointer; color: var(--ink-2); }
@media (prefers-reduced-motion: no-preference) { .row-hit { transition: fill-opacity 120ms ease; } }
"""

PAGE_JS = r"""
const D = JSON.parse(document.getElementById('report-data').textContent);
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in (attrs || {})) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
function txt(parent, x, y, s, cls, anchor) { const t = el('text', { x, y, class: cls || 'lbl', 'text-anchor': anchor || 'start' }, parent); t.textContent = s; return t; }
const pct = (v, d = 1) => v == null ? '—' : (v * 100).toFixed(d) + '%';
const spct = (v, d = 1) => v == null ? '—' : (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(d) + '%';
const sp = (v, d = 1) => v == null ? '—' : (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(d);
const num = (v) => v == null ? '—' : Math.round(v).toLocaleString('en-US');
const fix = (v, d = 2) => v == null ? '—' : (v >= 0 ? '' : '−') + Math.abs(v).toFixed(d);
const pval = (v) => v == null ? '—' : v < 0.001 ? '<0.001' : v.toFixed(3);
const seasonLabel = (s) => D.season_labels[String(s)] || `${s - 1}-${String(s).slice(2)}`;
const label = (m) => D.labels[m] || ({ core5: 'Core 5 pooled', all: 'All markets pooled' })[m] || m;
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

const tip = document.getElementById('tip');
function showTip(evt, head, rows) {
  tip.replaceChildren();
  const h = document.createElement('div'); h.className = 'h'; h.textContent = head; tip.appendChild(h);
  for (const r of rows) {
    const d = document.createElement('div'); d.className = 'r';
    if (r.color) { const i = document.createElement('i'); i.style.background = r.color; d.appendChild(i); }
    const b = document.createElement('b'); b.textContent = r.value; d.appendChild(b);
    const s = document.createElement('span'); s.textContent = r.label; d.appendChild(s);
    tip.appendChild(d);
  }
  tip.hidden = false;
  const pad = 14, w = tip.offsetWidth, hh = tip.offsetHeight;
  let x = evt.clientX + pad, y = evt.clientY + pad;
  if (x + w > window.innerWidth - 8) x = evt.clientX - w - pad;
  if (y + hh > window.innerHeight - 8) y = evt.clientY - hh - pad;
  tip.style.left = Math.max(8, x) + 'px'; tip.style.top = Math.max(8, y) + 'px';
}
function hideTip() { tip.hidden = true; }
function focusTip(node, fn) {
  node.addEventListener('focus', () => { const b = node.getBoundingClientRect(); fn({ clientX: b.left + Math.min(b.width / 2, 260), clientY: b.top + b.height }); });
  node.addEventListener('blur', hideTip);
}

function scale(d0, d1, r0, r1) { const f = (v) => r0 + (v - d0) / (d1 - d0) * (r1 - r0); f.inv = (p) => d0 + (p - r0) / (r1 - r0) * (d1 - d0); return f; }
function ticks(lo, hi, n) {
  const span = hi - lo, raw = span / Math.max(1, n), mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) || 10 * mag;
  const out = []; for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

// Dumbbell: P(under) after an under vs after an over, per market
function drawDumbbell(host, rows) {
  host.replaceChildren();
  const W = Math.max(300, host.clientWidth), labelW = W < 520 ? 100 : 140, rowH = 30, top = 30, H = top + rows.length * rowH + 6;
  const vals = rows.flatMap((r) => [r.p_under_after_under, r.p_under_after_over]);
  const lo = Math.floor((Math.min(...vals) - 0.01) * 50) / 50, hi = Math.ceil((Math.max(...vals) + 0.01) * 50) / 50;
  const x = scale(lo, hi, labelW, W - 14);
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Chance of an under after an under and after an over, by market' }, host);
  const g = el('g', { class: 'grid' }, svg), ax = el('g', { class: 'ax' }, svg);
  for (const t of ticks(lo, hi, W < 520 ? 4 : 7)) { el('line', { x1: x(t), x2: x(t), y1: top - 6, y2: H - 4 }, g); txt(ax, x(t), top - 12, pct(t, 0), 'lbl', 'middle'); }
  rows.forEach((r, i) => {
    const y = top + i * rowH + rowH / 2;
    const hit = el('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, class: 'row-hit', tabindex: 0 }, svg);
    txt(svg, 0, y + 4, r.label, 'lbl-ink');
    el('line', { x1: x(r.p_under_after_under), x2: x(r.p_under_after_over), y1: y, y2: y, class: 'conn' }, svg);
    el('circle', { cx: x(r.p_under_after_under), cy: y, r: 5, class: 's1 ring' }, svg);
    el('circle', { cx: x(r.p_under_after_over), cy: y, r: 5, class: 's2 ring' }, svg);
    const show = (e) => showTip(e, r.label, [
      { value: pct(r.p_under_after_over), label: `under after an over (${num(r.n_after_over)} games)`, color: cssVar('--series-2') },
      { value: pct(r.p_under_after_under), label: `under after an under (${num(r.n_after_under)} games)`, color: cssVar('--series-1') },
      { value: sp(r.reversal_effect, 2) + ' pts', label: `difference (p = ${pval(r.reversal_p_value)})` },
    ]);
    hit.addEventListener('pointermove', show); hit.addEventListener('pointerleave', hideTip); focusTip(hit, show);
  });
}

// Coefficient plot: estimate +/- 1.96 SE per market
function drawCoef(host, rows, key, seKey, cls, title, opts) {
  host.replaceChildren();
  const o = opts || {};
  const W = Math.max(280, host.clientWidth), labelW = W < 420 ? 96 : 128, rowH = 28, top = 30, H = top + rows.length * rowH + (o.zeroNote ? 22 : 8);
  const fmt = o.fmt || ((v) => fix(v, 2));
  const lo0 = Math.min(0, ...rows.map((r) => r[key] - 1.96 * r[seKey])), hi0 = Math.max(0, ...rows.map((r) => r[key] + 1.96 * r[seKey]));
  const padv = (hi0 - lo0) * 0.08 || 0.01, x = scale(lo0 - padv, hi0 + padv, labelW, W - 14);
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': title }, host);
  const g = el('g', { class: 'grid' }, svg), ax = el('g', { class: 'ax' }, svg);
  const bottom = H - (o.zeroNote ? 18 : 4);
  for (const t of ticks(lo0 - padv, hi0 + padv, W < 420 ? 4 : 6)) { el('line', { x1: x(t), x2: x(t), y1: top - 6, y2: bottom }, g); txt(ax, x(t), top - 12, fmt(t), 'lbl', 'middle'); }
  el('line', { x1: x(0), x2: x(0), y1: top - 6, y2: bottom, class: 'ref-line' }, svg);
  if (o.zeroNote) txt(svg, Math.min(x(0) + 4, W - 4), H - 4, o.zeroNote, 'ref-text', x(0) + 4 > W - 160 ? 'end' : 'start');
  rows.forEach((r, i) => {
    const y = top + i * rowH + rowH / 2, a = r[key] - 1.96 * r[seKey], b = r[key] + 1.96 * r[seKey];
    const hit = el('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, class: 'row-hit', tabindex: 0 }, svg);
    txt(svg, 0, y + 4, r.label, 'lbl-ink');
    el('line', { x1: x(a), x2: x(b), y1: y, y2: y, class: cls === 's1' ? 'whisk1' : 'whisk2' }, svg);
    el('circle', { cx: x(r[key]), cy: y, r: 5, class: `${cls} ring` }, svg);
    const show = (e) => showTip(e, `${r.label} · ${title}`, [
      { value: fmt(r[key]), label: 'estimate', color: cssVar(cls === 's1' ? '--series-1' : '--series-2') },
      { value: `${fmt(a)} to ${fmt(b)}`, label: '95% interval' },
      { value: num(r.n || r.graded_props), label: 'player-games' },
    ]);
    hit.addEventListener('pointermove', show); hit.addEventListener('pointerleave', hideTip); focusTip(hit, show);
  });
}

// Small multiples of lines with a crosshair
function drawMultiples(host, panels, opts) {
  host.replaceChildren();
  const all = panels.flatMap((p) => p.series.flatMap((s) => s.points.map((q) => q.y))).filter((v) => v != null).concat(opts.refs || []);
  let lo = Math.min(...all), hi = Math.max(...all);
  if (opts.clip) { lo = Math.max(lo, opts.clip[0]); hi = Math.min(hi, opts.clip[1]); }
  const pad = (hi - lo) * 0.08 || 0.01;
  const boxes = panels.map((p) => {
    const wrap = document.createElement('div'); wrap.className = 'panel'; host.appendChild(wrap);
    const h4 = document.createElement('h4'); h4.textContent = p.title; wrap.appendChild(h4);
    const box = document.createElement('div'); box.className = 'chart'; wrap.appendChild(box);
    return box;
  });
  panels.forEach((p, pi) => {
    const box = boxes[pi];
    const W = Math.max(220, box.clientWidth || 260), H = opts.height || 170, L = 46, R = 10, T = 8, B = 24;
    const xs = p.series[0].points.map((q) => q.x);
    const x = scale(0, xs.length - 1, L, W - R), y = scale(lo - pad, hi + pad, H - B, T);
    const cy = (v) => y(Math.max(lo - pad, Math.min(hi + pad, v)));
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': p.title }, box);
    const g = el('g', { class: 'grid' }, svg), ax = el('g', { class: 'ax' }, svg);
    for (const t of ticks(lo - pad, hi + pad, 4)) { el('line', { x1: L, x2: W - R, y1: y(t), y2: y(t) }, g); txt(ax, L - 6, y(t) + 4, opts.fmt(t, 0), 'lbl', 'end'); }
    const every = Math.ceil(xs.length / (W < 300 ? 4 : 6));
    const tick = opts.xtick || opts.xfmt || String;
    xs.forEach((v, i) => { if (i % every === 0 || (i === xs.length - 1 && (xs.length - 1) % every > every / 2)) txt(ax, x(i), H - 6, tick(v), 'lbl', 'middle'); });
    for (const r of (opts.refs || [])) el('line', { x1: L, x2: W - R, y1: y(r), y2: y(r), class: 'ref-line' }, svg);
    p.series.forEach((s) => {
      const pts = s.points.map((q, i) => q.y == null ? null : [x(i), cy(q.y)]).filter(Boolean);
      if (pts.length > 1) el('path', { d: 'M' + pts.map((q) => q.join(',')).join('L'), class: s.cls === 's1' ? 'l1' : 'l2' }, svg);
      if (opts.dots !== false) pts.forEach((q) => el('circle', { cx: q[0], cy: q[1], r: 4, class: `${s.cls} ring` }, svg));
    });
    const xh = el('line', { x1: 0, x2: 0, y1: T, y2: H - B, class: 'xhair', visibility: 'hidden' }, svg);
    const hit = el('rect', { x: L - 6, y: T, width: W - L - R + 12, height: H - T - B, class: 'hit' }, svg);
    hit.addEventListener('pointermove', (e) => {
      const b = svg.getBoundingClientRect(), px = (e.clientX - b.left) * (W / b.width);
      const i = Math.max(0, Math.min(xs.length - 1, Math.round(x.inv(px))));
      xh.setAttribute('x1', x(i)); xh.setAttribute('x2', x(i)); xh.setAttribute('visibility', 'visible');
      showTip(e, `${p.title} · ${opts.xname} ${opts.xfmt ? opts.xfmt(xs[i]) : xs[i]}`, p.series.map((s) => ({
        value: s.points[i].y == null ? '—' : opts.fmt(s.points[i].y, 1), label: s.name + (s.points[i].n != null ? ` (${num(s.points[i].n)} ${opts.nname || 'n'})` : ''),
        color: cssVar(s.cls === 's1' ? '--series-1' : '--series-2'),
      })));
    });
    hit.addEventListener('pointerleave', () => { xh.setAttribute('visibility', 'hidden'); hideTip(); });
  });
}

// Scatter: ROI where a strategy was picked vs ROI on the holdout season
function drawScatter(host, pts) {
  host.replaceChildren();
  const W = Math.max(300, host.clientWidth), H = Math.min(470, Math.max(300, W * 0.62)), L = 54, R = 14, T = 12, B = 42;
  const lim = 0.3, clip = (v) => Math.max(-lim, Math.min(lim, v));
  const xs = pts.map((p) => clip(p.train_roi)), ys = pts.map((p) => clip(p.test_roi));
  const lo = Math.max(-lim, Math.min(-0.1, ...xs, ...ys)), hi = Math.min(lim, Math.max(0.1, ...xs, ...ys));
  const x = scale(lo, hi, L, W - R), y = scale(lo, hi, H - B, T);
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'ROI where each strategy was picked against ROI on the holdout season' }, host);
  const g = el('g', { class: 'grid' }, svg), ax = el('g', { class: 'ax' }, svg);
  for (const t of ticks(lo, hi, W < 480 ? 4 : 6)) {
    el('line', { x1: x(t), x2: x(t), y1: T, y2: H - B }, g); txt(ax, x(t), H - B + 16, spct(t, 0), 'lbl', 'middle');
    el('line', { x1: L, x2: W - R, y1: y(t), y2: y(t) }, g); txt(ax, L - 6, y(t) + 4, spct(t, 0), 'lbl', 'end');
  }
  el('line', { x1: x(0), x2: x(0), y1: T, y2: H - B, class: 'base-line' }, svg);
  el('line', { x1: L, x2: W - R, y1: y(0), y2: y(0), class: 'base-line' }, svg);
  el('line', { x1: x(lo), y1: y(lo), x2: x(hi), y2: y(hi), class: 'ref-line' }, svg);
  txt(svg, x(hi) - 4, y(hi) + 14, 'same ROI in both', 'ref-text', 'end');
  txt(ax, (L + W - R) / 2, H - 6, `ROI on ${seasonLabel(D.seasons[0])} to ${seasonLabel(D.holdout - 1)} (where it was picked)`, 'lbl', 'middle');
  const yl = txt(ax, 12, (T + H - B) / 2, `ROI on ${seasonLabel(D.holdout)}`, 'lbl', 'middle'); yl.setAttribute('transform', `rotate(-90 12 ${(T + H - B) / 2})`);
  const order = pts.map((p, i) => i).sort((a, b) => (pts[a].top ? 1 : 0) - (pts[b].top ? 1 : 0));
  for (const i of order) el('circle', { cx: x(xs[i]), cy: y(ys[i]), r: pts[i].top ? 4.5 : 2.2, class: pts[i].top ? 's2 ring' : 'sd' }, svg);
  const hit = el('rect', { x: L, y: T, width: W - L - R, height: H - T - B, class: 'hit' }, svg);
  hit.addEventListener('pointermove', (e) => {
    const b = svg.getBoundingClientRect(), px = (e.clientX - b.left) * (W / b.width), py = (e.clientY - b.top) * (H / b.height);
    let best = -1, bd = 576;
    for (let i = 0; i < pts.length; i++) { const dx = x(xs[i]) - px, dy = y(ys[i]) - py, d2 = dx * dx + dy * dy; if (d2 < bd) { bd = d2; best = i; } }
    if (best < 0) { hideTip(); return; }
    const p = pts[best];
    showTip(e, p.label, [
      { value: spct(p.train_roi), label: `where it was picked (${num(p.train_bets)} bets)` },
      { value: spct(p.test_roi), label: `${seasonLabel(D.holdout)} (${num(p.test_bets)} bets)` },
    ]);
  });
  hit.addEventListener('pointerleave', hideTip);
}

function table(host, cols, rows) {
  host.replaceChildren();
  const t = document.createElement('table'), thead = document.createElement('thead'), tr = document.createElement('tr');
  for (const c of cols) { const th = document.createElement('th'); th.textContent = c.h; th.scope = 'col'; tr.appendChild(th); }
  thead.appendChild(tr); t.appendChild(thead);
  const tb = document.createElement('tbody');
  for (const r of rows) {
    const row = document.createElement('tr');
    for (const c of cols) {
      const td = document.createElement('td'); td.textContent = c.f ? c.f(r) : r[c.k];
      const cls = c.cls ? c.cls(r) : ''; if (cls) td.className = cls; if (c.wrap) td.classList.add('wrap'); row.appendChild(td);
    }
    tb.appendChild(row);
  }
  t.appendChild(tb); host.appendChild(t);
}
const sign = (v) => v == null ? '' : v > 0 ? 'pos' : v < 0 ? 'neg' : '';
function wireToggles() {
  document.querySelectorAll('[data-toggle]').forEach((b) => {
    const target = document.getElementById(b.dataset.toggle);
    b.addEventListener('click', () => { target.hidden = !target.hidden; b.textContent = target.hidden ? 'Show table' : 'Hide table'; b.setAttribute('aria-expanded', String(!target.hidden)); });
  });
}

const byMarket = (rows) => D.markets.map((m) => rows.find((t) => t.market === m)).filter(Boolean);
const thesisRows = byMarket(D.thesis);

function renderCharts() {
  drawDumbbell(document.getElementById('c-dumbbell'), thesisRows);
  drawCoef(document.getElementById('c-priceadj'), thesisRows.filter((r) => r.price_adj_effect_se < 0.02), 'price_adj_effect', 'price_adj_effect_se', 's2',
    'edge over the odds after an over vs after an under', { fmt: (v) => Math.abs(v) < 1e-9 ? '0' : sp(v, 1) + ' pts', zeroNote: 'no effect' });
  const streakPanels = D.core.map((m) => {
    const rows = D.streak_roi.filter((s) => s.market === m);
    return { title: label(m), series: [
      { name: 'under after k straight overs', cls: 's2', points: rows.map((r) => ({ x: r.streak, y: r.roi_under_after_overs, n: r.bets_under_after_overs })) },
      { name: 'over after k straight unders', cls: 's1', points: rows.map((r) => ({ x: r.streak, y: r.roi_over_after_unders, n: r.bets_over_after_unders })) },
    ] };
  });
  drawMultiples(document.getElementById('c-streaks'), streakPanels, { fmt: (v, d = 0) => spct(v, d), refs: [0], xname: 'streak', nname: 'bets', clip: [-0.25, 0.15] });
  const adj = byMarket(D.adjust).filter((a) => a.market !== 'stocks');
  drawCoef(document.getElementById('c-move'), adj, 'line_move_per_sd', 'line_move_se', 's1', 'line move per SD of surprise', { fmt: (v) => fix(v, 2) });
  drawCoef(document.getElementById('c-next'), adj, 'next_margin_per_sd', 'next_margin_se', 's2', 'next result vs the new line, per SD', { fmt: (v) => fix(v, 2), zeroNote: 'books adjust exactly right' });
  const histPanels = D.core.map((m) => {
    const rows = D.history.filter((h) => h.market === m).sort((a, b) => a.season - b.season);
    return { title: label(m), series: [{ name: 'real minus shuffled order', cls: 's2', points: rows.map((r) => ({ x: r.season, y: r.diff, n: r.n })) }] };
  });
  drawMultiples(document.getElementById('c-history'), histPanels, { fmt: (v, d = 1) => sp(v, d) + ' pts', refs: [0], xname: 'season', nname: 'pairs', xfmt: (s) => seasonLabel(s), xtick: (s) => "'" + String(s).slice(2), dots: false, height: 150 });
  drawScatter(document.getElementById('c-scatter'), D.scatter);
}

function renderTables() {
  table(document.getElementById('t-dumbbell'), [
    { h: 'Market', f: (r) => r.label }, { h: 'Graded', f: (r) => num(r.graded_props) },
    { h: 'Under after over', f: (r) => pct(r.p_under_after_over) }, { h: 'Under after under', f: (r) => pct(r.p_under_after_under) },
    { h: 'Difference', f: (r) => sp(r.reversal_effect, 2), cls: (r) => sign(r.reversal_effect) }, { h: 'p', f: (r) => pval(r.reversal_p_value) },
    { h: 'Vs the odds', f: (r) => sp(r.price_adj_effect, 2), cls: (r) => sign(r.price_adj_effect) }, { h: 'p', f: (r) => pval(r.price_adj_p_value) },
  ], thesisRows);
  table(document.getElementById('t-open'), [
    { h: 'Market', f: (r) => r.label }, { h: 'Graded', f: (r) => num(r.graded_props) },
    { h: 'Under after over', f: (r) => pct(r.p_under_after_over) }, { h: 'Under after under', f: (r) => pct(r.p_under_after_under) },
    { h: 'Difference', f: (r) => sp(r.reversal_effect, 2), cls: (r) => sign(r.reversal_effect) }, { h: 'p', f: (r) => pval(r.reversal_p_value) },
    { h: 'Vs the odds', f: (r) => sp(r.price_adj_effect, 2), cls: (r) => sign(r.price_adj_effect) }, { h: 'p', f: (r) => pval(r.price_adj_p_value) },
  ], byMarket(D.thesis_open));
  table(document.getElementById('t-streaks'), [
    { h: 'Market', f: (r) => label(r.market) }, { h: 'Streak', k: 'streak' },
    { h: 'Under after overs: ROI', f: (r) => spct(r.roi_under_after_overs), cls: (r) => sign(r.roi_under_after_overs) }, { h: 'Bets', f: (r) => num(r.bets_under_after_overs) },
    { h: 'Over after unders: ROI', f: (r) => spct(r.roi_over_after_unders), cls: (r) => sign(r.roi_over_after_unders) }, { h: 'Bets', f: (r) => num(r.bets_over_after_unders) },
  ], D.streak_roi.filter((s) => D.core.includes(s.market)));
  table(document.getElementById('t-adjust'), [
    { h: 'Market', f: (r) => r.label }, { h: 'Player-games', f: (r) => num(r.n) },
    { h: 'Line move per SD', f: (r) => fix(r.line_move_per_sd, 3) }, { h: '± SE', f: (r) => fix(r.line_move_se, 3) },
    { h: 'Next result per SD', f: (r) => fix(r.next_margin_per_sd, 3) }, { h: '± SE', f: (r) => fix(r.next_margin_se, 3) }, { h: 'p', f: (r) => pval(r.next_margin_p_value) },
  ], byMarket(D.adjust));
  table(document.getElementById('t-history'), [
    { h: 'Market', f: (r) => label(r.market) }, { h: 'Season', f: (r) => seasonLabel(r.season) }, { h: 'Pairs', f: (r) => num(r.n) },
    { h: 'Below avg after above', f: (r) => pct(r.real) }, { h: 'Shuffled order', f: (r) => pct(r.placebo) }, { h: 'Difference', f: (r) => sp(r.diff, 2) + ' pts', cls: (r) => sign(r.diff) },
  ], D.history);
  const enough = (r, s) => (r['bets_' + s] || 0) >= 30;  // a handful of bets says nothing
  const roiCols = D.seasons.map((s) => ({ h: seasonLabel(s), f: (r) => enough(r, s) ? spct(r['roi_' + s]) : '—', cls: (r) => enough(r, s) ? sign(r['roi_' + s]) : '' }));
  const book = (r) => r.book_mode === 'best' ? 'best line' : 'single book';
  const when = (r) => r.timing === 'open' ? 'opening' : 'closing';
  table(document.getElementById('t-thesis-bets'), [
    { h: 'Market', f: (r) => r.label }, { h: 'Line', f: when }, { h: 'Book', f: book },
    { h: 'Bets', f: (r) => num(r.bets) }, { h: 'Hit rate', f: (r) => pct(r.hit_rate) }, { h: 'Needed', f: (r) => pct(r.breakeven) },
    { h: 'ROI', f: (r) => spct(r.roi), cls: (r) => sign(r.roi) }, { h: 'Units', f: (r) => fix(r.units, 0), cls: (r) => sign(r.units) }, ...roiCols,
  ], D.thesis_bets.filter((r) => D.core.includes(r.market) || r.market === 'core5' || r.market === 'all'));
  const stratCols = [
    { h: 'Strategy', k: 'label', wrap: true }, { h: 'Bets', f: (r) => num(r.train_bets) }, { h: 'ROI', f: (r) => spct(r.train_roi), cls: (r) => sign(r.train_roi) },
    { h: 't', f: (r) => fix(r.train_t, 1) }, { h: `${seasonLabel(D.holdout)} bets`, f: (r) => num(r.test_bets) }, { h: `${seasonLabel(D.holdout)} ROI`, f: (r) => spct(r.test_roi), cls: (r) => sign(r.test_roi) },
  ];
  table(document.getElementById('t-top'), stratCols, D.top);
  table(document.getElementById('t-robust'), stratCols, D.robust);
  table(document.getElementById('t-wf'), [
    { h: 'Season bet', f: (r) => seasonLabel(r.test_season) }, { h: 'Picked on', f: (r) => r.train_seasons.split('-').map(Number).map(seasonLabel).join(' to ') },
    { h: 'Picked by', f: (r) => r.rule === 'best_train_roi' ? 'highest ROI' : 'highest t-stat' }, { h: 'Strategy', k: 'pick', wrap: true },
    { h: 'ROI before', f: (r) => spct(r.pick_train_roi), cls: (r) => sign(r.pick_train_roi) }, { h: 'ROI that season', f: (r) => spct(r.pick_test_roi), cls: (r) => sign(r.pick_test_roi) },
    { h: 'Bets', f: (r) => num(r.pick_test_bets) }, { h: 'Top 10 that season', f: (r) => spct(r.top10_test_roi), cls: (r) => sign(r.top10_test_roi) },
  ], D.walk_forward);
  table(document.getElementById('t-scatter'), [
    { h: 'Strategy', k: 'label', wrap: true }, { h: 'Bets', f: (r) => num(r.train_bets) }, { h: 'ROI', f: (r) => spct(r.train_roi), cls: (r) => sign(r.train_roi) },
    { h: `${seasonLabel(D.holdout)} bets`, f: (r) => num(r.test_bets) }, { h: `${seasonLabel(D.holdout)} ROI`, f: (r) => spct(r.test_roi), cls: (r) => sign(r.test_roi) },
  ], [...D.scatter].sort((a, b) => b.train_roi - a.train_roi).slice(0, 300));
  table(document.getElementById('t-base'), [
    { h: 'Market', f: (r) => r.label }, { h: 'Bet', f: (r) => r.variant === 'all_unders' ? 'every under' : 'every over' }, { h: 'Line', f: when }, { h: 'Book', f: book },
    { h: 'Bets', f: (r) => num(r.bets) }, { h: 'Hit rate', f: (r) => pct(r.hit_rate) }, { h: 'Needed', f: (r) => pct(r.breakeven) }, { h: 'ROI', f: (r) => spct(r.roi), cls: (r) => sign(r.roi) }, ...roiCols,
  ], D.baselines.filter((r) => D.core.includes(r.market) || r.market === 'core5' || r.market === 'all'));
  const books = [...new Set(D.coverage.map((c) => c.book_family))].sort();
  const cov = D.seasons.map((s) => { const r = { season: s }; for (const b of books) { const c = D.coverage.find((x) => x.season === s && x.book_family === b); r[b] = c || null; } return r; });
  table(document.getElementById('t-coverage'), [{ h: 'Season', f: (r) => seasonLabel(r.season) }, ...books.map((b) => ({ h: b, f: (r) => r[b] ? `${num(r[b].props)} · ${num(r[b].games)} games` : '—' }))], cov);
  table(document.getElementById('t-quality'), [
    { h: 'Season', f: (r) => seasonLabel(r.season) }, { h: 'Book', k: 'book_family' }, { h: 'Props', f: (r) => num(r.props) },
    { h: 'Opener miss', f: (r) => pct(r.open_vs_trailing, 0) }, { h: 'Close miss', f: (r) => pct(r.close_vs_trailing, 0) }, { h: 'Close moved', f: (r) => pct(r.share_moved, 0) },
    { h: 'Problem', f: (r) => r.issue || 'none', cls: (r) => r.issue ? 'flag' : '' },
  ], D.quality);
  table(document.getElementById('t-calib'), [
    { h: 'Over/under labels', k: 'sides' }, { h: 'Props', f: (r) => num(r.props) }, { h: 'Slope', f: (r) => fix(r.calibration_slope, 2) },
    { h: '± SE', f: (r) => fix(r.slope_se, 2) }, { h: 'Implied over', f: (r) => pct(r.mean_fair_over) }, { h: 'Actual over', f: (r) => pct(r.actual_over_rate) },
  ], D.calibration);
}

renderTables();
renderCharts();
wireToggles();
let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(renderCharts, 150); });
"""


def build_body(d: dict, w: dict) -> str:
    s = d["summary"]
    rc = s["reality_check"]
    first, last, holdout = d["seasons"][0], d["seasons"][-1], d["holdout"]
    tb = w["slip"]
    slip = ""
    if tb:
        stamp = "Won" if tb["roi"] > 0 else "Lost"
        slip = f"""
    <aside class="slip" aria-label="The thesis, graded as a bet">
      <span class="stamp{' won' if tb['roi'] > 0 else ''}">{stamp}</span>
      <div class="head"><span class="title">Opposite of last game</span><span class="sub">PTS · REB · AST · STL · BLK · single book, closing line</span></div>
      <div class="row"><span class="k">Bets</span><span class="v">{tb['bets']:,}</span></div>
      <div class="row"><span class="k">Hit rate</span><span class="v">{pct(tb['hit_rate'])}</span></div>
      <div class="row"><span class="k">Needed to break even</span><span class="v">{pct(tb['breakeven'])}</span></div>
      <div class="row"><span class="k">Return on stake</span><span class="v">{spct(tb['roi'])}</span></div>
      <div class="row"><span class="k">Result at 1 unit a bet</span><span class="v">{tb['units']:+,.0f}u</span></div>
    </aside>"""
    data_json = json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
    return f"""<title>NBA Prop Reversion Study</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{PAGE_CSS}</style>
<main class="page">
  <header class="hero">
    <div class="stack">
      <p class="eyebrow">NBA player props · {season_label(first)} to {season_label(last)} · real sportsbook lines</p>
      <h1>Does an over predict an under?</h1>
      <p class="lede">{escape(w['answer'])}</p>
      <p class="muted">{escape(w['tail'])}</p>
    </div>{slip}
  </header>

  <section class="kpis" aria-label="Data used">
    <div class="kpi"><span class="label">Games with box scores</span><span class="value">{s['n_games_box']:,}</span><span class="note">{s['n_box_seasons']} seasons, 2002-03 on</span></div>
    <div class="kpi"><span class="label">Player box-score lines</span><span class="value">{s['n_player_games'] / 1e6:.2f}M</span><span class="note">every player, every game</span></div>
    <div class="kpi"><span class="label">Prop lines graded</span><span class="value">{s['n_prop_lines'] / 1e6:.2f}M</span><span class="note">{s['n_prop_games']:,} games · {d['n_books']} sportsbooks</span></div>
    <div class="kpi"><span class="label">Strategies backtested</span><span class="value">{s['n_strategies']:,}</span><span class="note">at the real odds</span></div>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>The direct test</h2>
      <p>Each player-game is graded once, against the median line across books (the closing line where the feed has a real one, otherwise the opener). Blue is how often the under hit when the player went under last game; orange, when he went over. If the thesis were right, every orange dot would sit well to the right of its blue dot.</p>
    </div>
    <figure>
      <figcaption><span class="t">Chance of an under next game, by last game's result</span><span class="s">Hover a row for counts and the significance test.</span></figcaption>
      <div class="legend"><span><i style="background:var(--series-2)"></i>after an over</span><span><i style="background:var(--series-1)"></i>after an under</span></div>
      <div class="chart" id="c-dumbbell"></div>
      <div class="fig-foot"><span class="muted small">Differences are tested with standard errors clustered by player.</span><button class="toggle" data-toggle="t-dumbbell-wrap" aria-expanded="false">Show table</button></div>
      <div class="tbl-wrap" id="t-dumbbell-wrap" hidden><div id="t-dumbbell"></div></div>
    </figure>
    <div class="prose stack">
      <p>Steals and blocks lines sit at 0.5 or 1.5 and are priced through the juice, so raw hit rates mix players the books price very differently. The fair comparison is against the odds: did unders beat their price-implied chance by more after an over than after an under?</p>
    </div>
    <figure>
      <figcaption><span class="t">Edge over the odds: after an over minus after an under</span><span class="s">Percentage points, with 95% intervals. Above zero would support the thesis.</span></figcaption>
      <div class="chart" id="c-priceadj"></div>
      <details><summary class="small">Same test against opening lines only</summary><div class="tbl-wrap" style="margin-top:.75rem"><div id="t-open"></div></div></details>
    </figure>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>Streaks</h2>
      <p>Maybe one over isn't enough and the bounce comes after a run. These panels bet against streaks of 1, 2, 3, 4, 5 and 6+ games at a single book's closing line. Long streaks are rare, so the right side of each panel rests on a few hundred bets.</p>
    </div>
    <figure>
      <figcaption><span class="t">Return on betting against a streak</span><span class="s">Return per dollar staked at the real odds; the rule marks break-even.</span></figcaption>
      <div class="legend"><span><i class="line" style="background:var(--series-2)"></i>under after k straight overs</span><span><i class="line" style="background:var(--series-1)"></i>over after k straight unders</span></div>
      <div class="multiples" id="c-streaks"></div>
      <div class="fig-foot"><span class="muted small">Returns below −25% or above +15% are drawn at the panel edge.</span><button class="toggle" data-toggle="t-streaks-wrap" aria-expanded="false">Show table</button></div>
      <div class="tbl-wrap" id="t-streaks-wrap" hidden><div id="t-streaks"></div></div>
    </figure>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>What the books do after a big game</h2>
      <p>{escape(w['adjust'])}</p>
    </div>
    <div class="cols">
      <figure>
        <figcaption><span class="t">How far the next line moves</span><span class="s">SDs per SD the player beat his last line by</span></figcaption>
        <div class="chart" id="c-move"></div>
      </figure>
      <figure>
        <figcaption><span class="t">Where the next result lands</span><span class="s">SDs above the new line per SD of last game's surprise</span></figcaption>
        <div class="chart" id="c-next"></div>
      </figure>
    </div>
    <div class="fig-foot"><span class="muted small">95% intervals, clustered by player. SD is the player's own, over his previous 20 games.</span><button class="toggle" data-toggle="t-adjust-wrap" aria-expanded="false">Show table</button></div>
    <div class="tbl-wrap" id="t-adjust-wrap" hidden><div id="t-adjust"></div></div>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>Twenty-four seasons of box scores</h2>
      <p>Prop lines only go back to {season_label(first)}. To see whether the stats themselves bounce back, this uses each player's trailing 10-game average as a stand-in line for every season since 2002-03. A placebo that shuffles game order within each player-season removes the small mechanical effect of the average including the last game. Above zero would mean stats really do fall back after an above-average game.</p>
      <p>{escape(w['history'])}</p>
      <p class="note-box">No book sets lines this naively. This section is about the stats, not about betting.</p>
    </div>
    <figure>
      <figcaption><span class="t">Below average next game after an above-average game: real minus shuffled</span><span class="s">Percentage points, by season</span></figcaption>
      <div class="multiples" id="c-history"></div>
      <div class="fig-foot"><span></span><button class="toggle" data-toggle="t-history-wrap" aria-expanded="false">Show table</button></div>
      <div class="tbl-wrap" id="t-history-wrap" hidden><div id="t-history"></div></div>
    </figure>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>The thesis as a bet</h2>
      <p>{escape(w['bet_line'])}</p>
      <p class="muted">Each row bets the opposite of the player's last result against his line: 1 unit a bet at the real price, pushes refunded, props for players who sat out void. “Needed” is the hit rate that breaks even at the prices actually taken.</p>
    </div>
    <div class="tbl-wrap"><div id="t-thesis-bets"></div></div>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>Searching every variation</h2>
      <p>{escape(w['search'])}</p>
      <p class="muted">Every strategy was ranked on {season_label(first)} to {season_label(holdout - 1)} and then scored on {season_label(holdout)}. A real edge would put points along the diagonal. Strategies that looked best on the past instead fall back to zero or below, which is what overfitting looks like.</p>
    </div>
    <section class="kpis" aria-label="Strategy search results">
      <div class="kpi"><span class="label">Variants tested</span><span class="value">{s['n_strategies']:,}</span><span class="note">{s['n_eligible']:,} with 300+ bets before {season_label(holdout)}</span></div>
      <div class="kpi"><span class="label">Best ROI before {season_label(holdout)}</span><span class="value">{spct(rc['best_roi'])}</span><span class="note">t = {rc['best_t']:.1f}</span></div>
      <div class="kpi"><span class="label">Same bet in {season_label(holdout)}</span><span class="value">{spct(rc['best_test_roi'])}</span><span class="note">{rc['best_test_bets']:,} bets it never saw</span></div>
      <div class="kpi"><span class="label">Reality Check p-value</span><span class="value">{rc['p_value']:.2f}</span><span class="note">{d['fdr']['n']:,} pass a 10% false-discovery screen; together {spct(d['fdr']['holdout_roi']) if d['fdr']['holdout_roi'] is not None else '—'} in {season_label(holdout)}</span></div>
    </section>
    <figure>
      <figcaption><span class="t">ROI where each strategy was picked vs. ROI on {season_label(holdout)}</span><span class="s">Every strategy with 300+ bets before and 100+ in {season_label(holdout)}. Orange: the 15 best before {season_label(holdout)}. ROIs past ±30% are drawn at the edge.</span></figcaption>
      <div class="chart" id="c-scatter"></div>
      <div class="fig-foot"><span></span><button class="toggle" data-toggle="t-scatter-wrap" aria-expanded="false">Show table</button></div>
      <div class="tbl-wrap" id="t-scatter-wrap" hidden><div id="t-scatter"></div></div>
    </figure>
    <h3>The 15 best before {season_label(holdout)}, and what happened next</h3>
    <div class="tbl-wrap"><div id="t-top"></div></div>
    <details>
      <summary>Ranked by t-statistic instead (steadier; t ≥ 2 required)</summary>
      <div class="tbl-wrap" style="margin-top:.75rem"><div id="t-robust"></div></div>
    </details>
    <h3>Walk-forward: pick each season using only the seasons before it</h3>
    <p class="muted prose">This is what “find the most profitable strategy and bet it” would actually have done. {escape(w['walk'])}</p>
    <div class="tbl-wrap"><div id="t-wf"></div></div>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>Baselines: every over, every under</h2>
      <p>{escape(w['base'])}</p>
    </div>
    <div class="tbl-wrap"><div id="t-base"></div></div>
  </section>

  <section class="stack">
    <div class="prose stack">
      <h2>The data</h2>
      <p>Box scores, schedules, game lines and player props all come from ESPN's public JSON APIs. For every game, the prop feed keeps each sportsbook's opening and last-recorded line and price. Players are matched to box scores by ESPN athlete id.</p>
    </div>
    <h3>Main prop lines by season and book</h3>
    <div class="tbl-wrap"><div id="t-coverage"></div></div>
    <div class="stack">
      <h3>Which lines can be trusted</h3>
      <p class="muted prose">Some of the feed's “closing” lines were recorded during the game, and one season's openers are full of placeholder prices. Each book-season is scored against a yardstick that knows nothing about the game: the player's trailing 10-game average. Real lines miss by about 93-98% as much as that average. A close that misses far less was captured in-game; an opener that misses more than the average is junk. Flagged lines are dropped, and the rest of that book-season is kept.</p>
      <div class="tbl-wrap"><div id="t-quality"></div></div>
    </div>
    <div class="stack">
      <h3>Inferred over/under labels</h3>
      <p class="muted prose">DraftKings' 2025-26 lines arrive without side labels, so they are read in the order every labeled book uses (over first, 99.98% of the time). A slope near 1 means the implied probabilities match what happened; flipped labels would give a negative slope.</p>
      <div class="tbl-wrap"><div id="t-calib"></div></div>
    </div>
  </section>

  <section class="stack">
    <h2>Method and limits</h2>
    <ul class="method">
      <li>“Previous game” is the player's previous game played in the same season. A game with no posted line breaks a streak.</li>
      <li>Strategies bet 1 unit at the real American odds. Pushes are refunded, and props for players who sat out are void.</li>
      <li>“Best line” takes the lowest line on offer for overs and the highest for unders, then the better price. It assumes every book's line was available at once, so treat it as an upper bound. “Single book” sends every bet to one major book.</li>
      <li>Opening-line bets use only what was known at the open. Closing-line bets may also use the open-to-close move.</li>
      <li>Coverage: four seasons of props. 2025-26 has props for only 400 of 1,322 games, because the feed kept DraftKings props for some games only after ESPN switched books in December 2025. FanDuel and offshore books are not in the feed, and there is no intraday line history.</li>
      <li>Results assume you could get the posted price. Books limit winning prop bettors quickly.</li>
    </ul>
    <pre>cd nba-props
.venv/bin/nbaprops pull      # resumable download from ESPN
.venv/bin/nbaprops build     # parse, grade, and quality-check every line
.venv/bin/nbaprops analyze   # tests, backtests, this report</pre>
  </section>
</main>
<div id="tip" role="tooltip" hidden></div>
<script type="application/json" id="report-data">{data_json}</script>
<script>{PAGE_JS}</script>
"""


def build_report(summary: dict) -> None:
    d = collect(summary)
    w = narrative(d)
    body = build_body(d, w)
    (config.DATA / "report_body.html").write_text(body)  # the page without a document wrapper, for publishing
    full = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
        + body
        + "\n</body>\n</html>\n"
    )
    (config.REPORTS / "report.html").write_text(full)
    md = [f"# Does an over predict an under? {w['verdict']}.", w["answer"], w["tail"], w["bet_line"], w["adjust"], w["history"], w["search"], w["walk"], w["base"]]
    (config.REPORTS / "summary.md").write_text("\n\n".join(x for x in md if x) + "\n")
    print(f"[report] wrote {config.REPORTS / 'report.html'}", flush=True)
