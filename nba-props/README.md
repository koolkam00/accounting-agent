# NBA prop reversion lab

Tests one betting thesis on real sportsbook lines:

> If a player goes **over** his prop line in one game, he goes **under** in the next
> (and vice versa), for points, rebounds, assists, steals and blocks.

It also backtests every variation of that idea, plus a few competing ones, at the
prices the books actually offered, and checks whether the best of them still works
on a season it was not chosen on.

The results live in [`reports/`](reports/). Open `reports/report.html` in a browser
for the full write-up with charts. Every CSV behind it is in the same folder, and
`reports/summary.md` has the short version.

## Results (2022-23 to 2025-26, 1.05M graded prop lines)

**The thesis does not hold.**

* After a player goes over his line, the under hits 51.0% to 52.8% of the time next game
  for points, rebounds and assists. After an under, it hits 51.3% to 52.2%. The
  difference is under 0.6 percentage points and not statistically significant
  (standard errors clustered by player). It is the same against opening lines only.
* Steals and blocks look like the opposite of the thesis in raw numbers. Their lines sit
  at 0.5 or 1.5 and the odds already account for it: compared against each bet's own
  price, last game's result adds nothing (+0.1 points for steals, −1.0 for blocks).
* Streaks don't change it. Betting the under after 1 to 6+ straight overs returns about
  −3% at a single book, the same as betting every under.
* The books move the next line about 0.10 SD per SD of surprise, and the next result
  lands right on the new line. The thesis needs them to overreact, and they don't.
* 24 seasons of box scores show the opposite of reversal. Against a player's own
  trailing average, an above-average game makes the next one *more* likely to be above
  average (in 72 of 72 season-stat pairs). Roles and minutes carry over.
* Betting the thesis on all five stats at a single book's close: 179,629 bets, 48.9%
  hit rate against 52.2% needed, −6.4% ROI. Shopping the best opening line across
  every book only trims it to −3.4%.

**No strategy survives out of sample.** Of 16,700 variants, the best on 2022-23 to
2024-25 was every rebounds under at the opening line, shopping every book (+3.6%, t = 6.7,
Reality Check p = 0.01). At a single book the same bet lost 0.8%, and on 2025-26 it lost
4.2%. All but three of the 128 strategies that pass a 10% false-discovery screen are
versions of that one bet (unders, opening line, best book); together they returned
−4.0% on 2025-26. In 6 of 6 walk-forward tries, the strategy that had worked best so far
lost money the next season.

Unders do lose less than overs everywhere (−3.4% vs −9.6% at a single book's close),
the familiar lean of prop markets, but not by enough to beat the vig at one book.

## Data (all free, no keys needed)

Everything comes from ESPN's public JSON APIs:

| What | Source | Coverage |
|---|---|---|
| Schedule | `site.api.espn.com/.../scoreboard?dates=YYYYMMDD` | every game since 2002-03 (regular season, play-in, playoffs) |
| Box scores | `site.api.espn.com/.../summary?event=ID` | every player in every game since 2002-03 |
| Player prop lines | `sports.core.api.espn.com/.../events/ID/competitions/ID/odds/{book}/propBets` | 2022-23 onward |
| Game lines (spread, total) | `sports.core.api.espn.com/.../odds` | 2022-23 onward |

The prop feed keeps, for each game and each sportsbook, every player prop that book
posted, with the **opening** line and price and the **last pregame** line and price.
Books seen in the feed:

| Season | Books with props |
|---|---|
| 2022-23 | Caesars, DraftKings, MGM, BetRivers, PointsBet |
| 2023-24 | Caesars, DraftKings, MGM, BetRivers, PointsBet, ESPN BET (from Nov 2023) |
| 2024-25 | ESPN BET |
| 2025-26 | ESPN BET, then DraftKings (ESPN switched partners in Dec 2025) |

2025-26 has props for only 400 of 1,322 games: after ESPN switched from ESPN BET to
DraftKings in December 2025, the feed kept DraftKings props for some games only.

Three things to know about the feed:

* **Sides.** Most books label each price "over" or "under". DraftKings' 2025-26 lines
  come unlabeled. Every labeled book lists the over first and the under right after it
  (99.98% of pairs), so unlabeled pairs are read in that order. Checked against results,
  the inferred labels are calibrated (slope 1.07 ± 0.07; a flipped label gives about −1).
* **Bad closes and openers.** The "current" value is meant to be the last pregame line,
  but some books' feeds recorded it during the game, and ESPN BET's 2024-25 openers are
  full of placeholders (0.5 points at −5000). `build` scores every book-season against
  a yardstick that knows nothing about the game, the player's trailing 10-game average.
  Real lines miss by 93-98% as much as that average. Closes that miss far less were
  captured in-game (2022-23 Caesars, DraftKings, PointsBet: 74-82%), a close identical
  to the opener was never updated (2022-23 MGM), and an opener that misses more than the
  average is junk (2024-25 ESPN BET: 104%). Those closes or openers are dropped and the
  rest of the book-season is kept. Prices beyond ±1000 are always dropped.
* **Snapshots.** ESPN BET's 2024-25 props often have an early and a final record; the
  latest one is used.

Players are joined to box scores by ESPN athlete id, so no name matching is involved.
A prop is **void** (stake refunded) when the player did not play, as at the books.

## How the thesis is tested

All tests grade each player-game-market once, against the median closing line across
books. "Previous game" means the player's previous game played in the same season,
so a game without a posted line breaks a streak rather than being skipped.

1. **Conditional rates.** P(under | over last game) against the overall under rate
   and the 52.4% you need to break even at −110 on both sides. A linear probability
   model with standard errors clustered by player tests the difference.
2. **Streaks.** P(under) after exactly 1, 2, 3, 4, 5 and 6+ straight overs (and the mirror).
3. **Size of the miss.** P(over next game) by how far the last game finished from its
   line, in the player's own standard deviations.
4. **What the books do.** How far the next line moves per SD of surprise, and whether
   the next result lands above or below that new line. A negative slope there means
   the books overreact, which is the only way the thesis can make money.
5. **24 seasons of box scores.** Uses the player's trailing 10-game average as a
   stand-in line, with a placebo that shuffles game order within each player-season
   to remove the small mechanical effect of the average including the last game.

## How strategies are backtested

* 1 unit flat stake per bet, at the real American odds, pushes refunded, voids skipped.
* Two ways to bet: **single book** (every bet goes to one major book, first of
  DraftKings, ESPN BET, MGM, Caesars, BetRivers, PointsBet that posted it) and **best
  line** (the over takes the lowest line on offer, the under the highest, and ties go
  to the better price).
* Two times to bet: at the **opening** line, using only what was known then, or at the
  **close**.
* Strategy families (12 markets, the core 5 pooled, and all markets pooled):
  * `baseline`: bet every over or every under
  * `reversal` (the thesis): bet against the last result after k straight overs or unders,
    optionally only after a miss of at least z SDs
  * `momentum`: the opposite of reversal
  * `line_adjust`: fade or follow a big move from the last game's line
  * `line_vs_avg`: fade or follow a line far from the player's 5-game, 10-game or season average
  * `steam`: fade or follow the open-to-close line move (close only)
  * `price`: plus-money sides, or heavily juiced sides
  * `context`: the simplest versions of the above, filtered by back-to-backs, rest, home
    or away, overtime or a minutes spike last game, starter or bench, playoffs, line size,
    big spreads, game totals, and early or late season
* **Out-of-sample discipline.** Strategies are ranked on the seasons before the holdout
  season (by default the latest), then scored on the holdout. A walk-forward run
  repeats that for every season. White's Reality Check asks whether the best in-sample
  strategy beats what the luckiest of that many zero-edge strategies would show, and
  Benjamini-Hochberg counts how many survive a 10% false discovery rate.

## Running it

Requires Python 3.11+.

```bash
cd nba-props
uv venv .venv && uv pip install -e ".[dev]" --python .venv/bin/python   # or: pip install -e ".[dev]"

.venv/bin/nbaprops pull       # ~1 hour the first time; resumable, cached under data/raw/
.venv/bin/nbaprops build      # parse raw files into data/tables/*.parquet
.venv/bin/nbaprops analyze    # tests + backtests, writes reports/
.venv/bin/python -m pytest    # unit tests
```

`pull` options: `--box-seasons 2003-2026 --prop-seasons 2022-2026 --workers 16`. Seasons are
named by the year they end in (2026 is 2025-26). Rerunning `pull` only fetches what is
missing, plus the last few days of the schedule. Set `NBAPROPS_MAX_RPS` to change the
request rate cap (default 25 per second).

## Layout

```
src/nbaprops/
  ingest/schedule.py    game discovery (per-day scoreboard)
  ingest/boxscores.py   game summaries -> box scores
  ingest/props.py       sportsbook prop lines and game lines from the odds feed
  build.py              pair over/under prices, grade every prop, drop bad lines, profit per side
  features.py           pregame-only features per player, game and market; bettable panels
  hypothesis.py         the direct statistical tests
  backtest.py           strategy grid, P&L, walk-forward, Reality Check, FDR
  analyze.py            runs everything, writes reports/
  report.py             the HTML report
```

## Limits

* Four seasons of prop lines, only one or two books per game after 2023-24, and only
  400 games with props in 2025-26. FanDuel and offshore books are not in ESPN's feed.
* "Best line" assumes every book's line was available at the same moment, which is
  optimistic for opening lines posted at different times. Treat it as an upper bound.
* Only opening and last-pregame prices are available, not the full line history.
* Results assume you could get down at the posted price. Books limit winning prop
  bettors quickly, so even a real edge would be hard to bet at size.
