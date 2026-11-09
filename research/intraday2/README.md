# intraday2: shared data and backtest engine

This folder is for research only. It is not imported by `radar/` and it is not run by the workflows.

| file | purpose |
|---|---|
| `fetch_data.py` | downloads and builds `data/` (incremental; raw zips are cached outside the repo, `$INTRADAY2_RAW`) |
| `data/` | csv.gz, about 10 MB in total; `data_checks.txt` is the data-quality log from the last build |
| `engine.py` | loaders, backtest, metrics, IS/OOS split, placebo, neighbours |
| `test_engine.py` | exact tests on hand-made bars: `cd research/intraday2 && python3 -m unittest -q test_engine` |
| `strategies/example_ema_cross.py` | baseline plug-in (4h EMA cross); run it with `python3 research/intraday2/strategies/example_ema_cross.py` |

## Data (built 2026-11-09)

| file | source | coverage |
|---|---|---|
| `{SYM}_1h.csv.gz` | data.binance.vision `futures/um/monthly/klines/{SYM}/1h` (+ `daily/` for the current month) | BTC and ETH from 2020-09-01 00:00, SOL from 2020-09-14 07:00 (listing). All three end at 2026-11-07 23:00, because the daily file for 11-08 was not published yet |
| `{SYM}_funding.csv.gz` | data.binance.vision `futures/um/monthly/fundingRate`; for the current month, which is not yet published, OKX `public/funding-rate-history` (`source=okx`) | 2020-09 → 2026-11-09 08:00 |
| `{SYM}_metrics_1h.csv.gz` | data.binance.vision `futures/um/daily/metrics` (5m) | 2021-12-01 → 2026-11-08 |

Columns:
- **1h:** `ts` (bar open, UTC), `open`, `high`, `low`, `close`, `volume` (base), `quote_volume`, `trades`, `taker_buy_volume`, `taker_buy_quote`, `filled`.
- **funding:** `ts` (event time, floored to the hour), `rate`, `interval_h`, `source`.
- **metrics:** `oi`, `oi_value` (USDT), `top_acc_ls` (top-trader account L/S), `top_pos_ls` (top-trader position L/S), `glob_acc_ls` (global account L/S), `taker_ls` (taker buy/sell volume ratio). Each value is the last 5m sample of the hour. It is labelled with the bar it closes, so the value is known at that bar's close and causes no look-ahead.

Data checks (full log in `data/data_checks.txt`):
- **Gaps in the Binance archive:** 2026-10-28 is missing for all 3 symbols (24 bars; the daily file is missing too). SOL also misses 2022-02-26→02-28 (72 bars) and 2022-04-01→04-02 (48 bars). These bars were filled with OKX swap 1H OHLC and carry `filled=1`. Their volumes are NaN, because OKX volume is not comparable with Binance volume. After the fill there are 0 gaps.
- **Other checks:** no duplicates, time is monotonic, 0 OHLC inconsistencies, 1 zero-volume bar per asset.
- **Moves larger than 15% in one hour:** all are real events (2021-05-19, the FTX week of 2022-11, SOL in 2021). They were kept.
- **Funding interval:** 8h, except SOL in 2022-11 (99 events at 2h and 2 at 4h). There are 26 SOL rates with |rate| > 0.5%, also from 2022-11.
- **Metrics:** one 10h hole (2024-02-16). The three L/S ratios are NaN for 87% of 2022 (as published). `glob_acc_ls` is NaN for 5% of 2022 and `taker_ls` for 35% of 2022. Open interest (`oi`) is complete.
- **Not included:** liquidations. The `liquidationSnapshot` archive returns 404 and there is no cheap public history.

## Engine API

```python
import sys; sys.path.insert(0, "research/intraday2")
from engine import load_all, Exits, Sizing, Costs, backtest, split, report, placebo, neighbours

bars = load_all("4h")                 # {asset: DataFrame}; "1h" or any pandas freq ≥ 1h
def my_signals(b, n=20):              # decided at the bar CLOSE -> entry at NEXT open
    hi = b.high.rolling(n).max().shift()
    side = (b.close > hi).astype(int) - (b.close < b.low.rolling(n).min().shift()).astype(int)
    return pd.DataFrame({"side": side})   # optional columns: stop (price), stop_pct, max_bars, exit (bool)
ex = Exits(stop_atr=2, tp=[(1.5, .5), (3, .5)], tp_unit="R", be_after_tp1=True, trail_atr=None, time_bars=None)
sz = Sizing(mode="risk", risk_pct=0.01, leverage=3, allocation="equal", max_exposure=3)   # capital 10_000
res = backtest(bars, {a: my_signals(b) for a, b in bars.items()}, ex, sz, Costs(), start="2021-01-01")
print(report(res, "breakout"))        # metrics + per year / asset / side + exit reasons
res.trades; res.legs; res.daily      # trades table, partial fills, daily MTM equity
s = split(my_signals, {"n": 20}, ex, sz, bars=bars)       # {'IS': 2021-23, 'OOS': 2024->, 'ALL'}, fresh capital each
pl = placebo(res, bars, ex, sz, n=100); pl["pctl"]          # percentile of the real result among random entries
nb = neighbours(lambda p: backtest(bars, {a: my_signals(b, **p) for a, b in bars.items()}, ex, sz,
                start="2021-01-01"), {"n": 20}, grid={"n": [15, 18, 22, 25]})
```

### Exits

- **Stop:**
  - Set it with `stop_pct` (fraction of the entry price) or `stop_atr` (multiple of Wilder ATR(`atr_len`) at the signal bar).
  - A per-signal `stop` level, or a per-signal `stop_pct`, overrides both.
  - If a level sits on the wrong side of the entry price, the entry is skipped and counted in `info['skipped_invalid_stop']`.
- **Take-profits:** `tp=[(dist, frac), ...]`, with the distance unit set by `tp_unit` as `pct`, `R` or `atr`.
  - Fractions are fractions of the initial size.
  - If the fractions add up to less than 1, the rest is a runner. It is closed by the stop, the trail, the time exit or a signal.
- **Breakeven:** `be_after_tp1` moves the stop to breakeven after TP1, with optional `be_offset`.
- **Trailing stop:** `trail_atr` or `trail_pct`, measured from the highest high (or lowest low) since entry. It is updated at the bar close and is active from the next bar. With `trail_after_tp1`, trailing starts only once TP1 is filled.
- **Time exit:** `time_bars` (or the per-signal `max_bars`) exits at the open of bar entry+N.
- **Signal exits:** with `reverse_exit`, an opposite signal exits at the next open. With `reverse_entry`, the opposite position is opened at that same open. An `exit` column closes the position at the next open.

Intrabar order, which is conservative:
1. A gap through the stop fills at the open.
2. If the stop is touched, it fills at the stop. The stop always comes before any TP in the same bar.
3. TPs fill in order, at max(level, open).
4. If BE was armed in the bar and the low reaches the BE level, the rest exits at BE in that same bar (`be_same_bar=True`).

There is one position per asset. Signals that arrive while a position is open are ignored.

### Sizing

- **`fixed`:** notional = `leverage` × allocation.
- **`risk`:** notional = `risk_pct` × equity / (stop% + costs), capped at `leverage` × allocation.
- **Allocation:** `allocation="equal"` gives equity/3 per asset; `"shared"` gives the whole equity.
- **Caps:** `max_exposure` caps the sum of open notionals divided by equity; new trades are scaled down to fit, and dropped if less than `min_fill` of the intended size remains. `max_positions` caps the number of open positions.
- **Equity used:** sizing uses realised equity at entry (`compounding=False` uses the initial capital instead). `leverage` is also the isolated-margin leverage used for the liquidation price.

### Costs (defaults in `Costs`)

- **Fees and slippage:** taker fee 0.05% per side. Slippage 0.02% on entries, TP, time and signal exits; 0.05% on stop, BE and trailing exits.
- **Funding:** the real funding rate at each event × position notional at that bar's open. Longs pay positive rates. Funding is charged only if the position is open at the event time; an exit at the open of the event bar does not pay it.
- **Liquidation:**
  - Long liquidation price = E·(1 − 1/L + mmr), with mmr = 0.5%. A short is the mirror image.
  - If the adverse extreme reaches that price before the trade's own exit, the remaining slice loses its whole isolated margin (notional/L).
  - A stop that sits before the liquidation price fills first.

### Output

- **`res.trades`:** asset, side, signal/entry/exit times, entry (with costs), stop0, average exit, bars held, qty, notional, lev, fees, funding, pnl $, pnl % of equity, R (net PnL / initial risk $), tp_hits, reason (for example `tp1+be`), final, liq_px.
- **`res.legs`:** partial fills.
- **`metrics(res)`:** final, ret_pct, cagr, max_dd (on daily MTM), mar, trades, trades_per_month, win_rate, avg_win/avg_loss, pf, exp_R, time_in_mkt, fees, funding, liquidations.
- **`breakdown(res)`:** per-year, per-asset, long/short and exit-reason tables.

### Placebo and neighbours

- **`placebo(res, bars, exits, sizing, costs, n=100)`:**
  - Random entries, with the same count per asset, the same long/short mix and the same window.
  - Per-trade stop distances are resampled from the real trades, and the same `Exits` are used.
  - When the strategy is signal-exit driven (no TP or trail), holding times are resampled from the real trades too. Force this with `match_holding=True`.
  - Returns the runs and the percentile of the real metrics. Look at `runs.trades` against the real count.
- **`neighbours(run_fn, base, grid=None, rel=(.8,.9,1.1,1.2), mode="oat"|"full")`:**
  - Runs a one-at-a-time (or full cartesian) grid around the chosen parameters.
  - `df.attrs['share_pf_gt_1']` is the share of runs with PF > 1.

### Speed

Measured on this machine:
- Loading 3 assets: 0.7s for 1h, 0.8s for 4h.
- Full 2021→now backtest: about 0.4s on 1h with about 3,500 trades, and about 0.06s on 4h.
- Placebo: 50 runs on 4h take about 3.5s.

## Known limitations

- **Sizing equity:** sizing uses realised equity. MTM only enters the equity curve and the drawdown.
- **Skipped trades:** when the portfolio drops a trade (because of `max_positions` or `max_exposure`), phase 1 still treats it as occupying its asset, so a later signal on that asset during the skipped trade is not taken.
- **Funding for intrabar exits on 4h bars:** funding events inside a 4h bar (only possible with the non-8h intervals of SOL in 2022-11) count as if they happened at the bar open. Partial TP legs filled at a gap open still pay that bar's funding.
- **Liquidation model:** liquidation is a simple isolated-margin model with a flat mmr. It ignores tiered maintenance margin and mark-price vs last-price differences.
- **TP fills:** TPs fill at the level with taker costs. Manual execution from Telegram alerts may be slower; you can raise `slip` to test this.
- **Gaps in the data:** OKX-filled bars (`filled=1`) have NaN volumes, so strategies must handle NaN (for example with `fillna`) in volume features.
- **Missing metrics:** metrics (OI and L/S ratios) start in 2021-12, and the L/S ratios are mostly missing in 2022, so features that use them cannot be tested in-sample on 2021.
- **End of data:** positions still open at the end of the window are closed at the last close (reason `end`).
