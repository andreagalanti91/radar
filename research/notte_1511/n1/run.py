"""N1 · W3 con candele settimanali ancorate a ciascun giorno. Copia fedele di radar.weekly (weekly_bars + simulate) con il
solo giorno di ancoraggio come parametro. Non modifica radar/. Uso: python research/notte_1511/n1/run.py"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "short_w2"))
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402
from radar import weekly as W  # noqa: E402

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
IT = dict(zip(DAYS, ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]))


def weekly_bars(f: pd.DataFrame, anchor: str) -> pd.DataFrame:
    rule = f"W-{anchor}"
    w = f[["open", "high", "low", "close"]].resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = W.live_flow(f).resample(rule).last()
    w["fund7"] = f["funding"].fillna(0).rolling(7).mean().resample(rule).last()
    c = w["close"]
    w["sma"] = c.rolling(W.SMA).mean()
    w["ema20"] = c.ewm(span=W.EMA_T, adjust=False).mean()
    w["ema21"] = c.ewm(span=W.EMA_X, adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / W.ATR_N, adjust=False).mean()
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    w["trend_age"] = above.groupby((above == 0).cumsum()).cumsum()
    m = c.ewm(span=W.MACD_P[0], adjust=False).mean() - c.ewm(span=W.MACD_P[1], adjust=False).mean()
    w["macd"], w["macd_sig"] = m, m.ewm(span=W.MACD_P[2], adjust=False).mean()
    w["f1_ok"] = (w["trend_age"] < W.OLD_TREND) | ((w["macd"] > w["macd_sig"]) & (w["macd"] > 0))
    w["long"] = (up & (c > w["ema21"]) & (w["flow"] > 0) & w["f1_ok"]).fillna(False)
    w["short"] = (dn & (c < w["ema21"]) & (w["flow"] < 0)).fillna(False)
    w["dist_long"] = ((w["fund7"] > W.FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < W.FUND_COLD) & (w["flow"] > 0)).fillna(False)
    return w[w.index <= f.index[-1]]


def simulate(f: pd.DataFrame, anchor: str = "SUN", start: str = "2021-01-01", end: str | None = None,
             capital: float = 10000.0) -> dict:
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= pd.Timestamp(end)]
    w = weekly_bars(f, anchor)
    dow = DAYS.index(anchor)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"], 1.0)
                fs = min(lt, 1.0) / lt if side > 0 else 0.0
                frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
                px = O[i] * (1 + W.SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), expo=round(lt, 3), eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == dow and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            pend = d + (wk, day) if d else None
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "open": None}
    if side:
        i = len(idx) - 1
        out["open"] = dict(tr, exit=None, reason="open", move=(C[i] / tr["entry_px"] - 1) * side,
                           pnl=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    return out


def stats(eq: pd.Series, trades: list[dict]) -> dict:
    e = eq / eq.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1]) ** (1 / yrs) - 1
    pn = np.array([t["pnl"] for t in trades]) if trades else np.zeros(0)
    best = float(pn.max()) if len(pn) else 0.0
    return dict(finale=float(eq.iloc[-1]), rend=float(e.iloc[-1] - 1) * 100, dd=dd * 100, cagr=cagr * 100,
                mar=cagr / abs(dd) if dd < 0 else np.nan, trade=len(pn),
                wr=float((pn > 0).mean() * 100) if len(pn) else np.nan,
                senza_migliore=float(eq.iloc[-1]) / (1 + best))


def run_one(f, anchor, start, end=None):
    r = simulate(f, anchor, start, end)
    tt = r["trades"] + ([r["open"]] if r["open"] else [])
    return stats(r["equity"], tt), r["equity"], tt


def main():
    import short_lab
    f = build_features(load_all())
    f = f[f["close"].notna()]
    fl = short_lab.load_long(f)
    last = f.index[-1].date()
    out = []
    # 0) controllo: riproduzione di radar.weekly.simulate (domenica)
    ref = W.simulate(f)
    m_ref = W.metrics(ref)
    mine = simulate(f, "SUN")
    same_eq = np.allclose(ref["equity"].to_numpy(), mine["equity"].to_numpy(), rtol=1e-12, atol=1e-6)
    same_tr = [(t["entry"], t["exit"]) for t in ref["trades"]] == [(t["entry"], t["exit"]) for t in mine["trades"]]
    out.append(f"Dati fino al {last}. Controllo radar.weekly.simulate (domenica): finale {ref['equity'].iloc[-1]:,.0f} $, "
               f"DD {m_ref['max_dd_pct']}%, trade {m_ref['n']}; copia N1: finale {mine['equity'].iloc[-1]:,.0f} $; "
               f"equity identica={same_eq}, trade identici={same_tr}")
    assert same_eq and same_tr, "la copia non riproduce radar.weekly"

    P = {"2021": (f, "2021-01-01", None), "IS": (f, "2021-01-01", "2023-12-31"), "OOS": (f, "2024-01-01", None),
         "1820": (fl, "2018-01-01", "2020-12-31")}
    rows, EQ, TR = [], {}, {}
    for a in DAYS:
        r = dict(giorno=IT[a])
        for k, (x, s, e) in P.items():
            m, eq, tt = run_one(x, a, s, e)
            if k == "2021":
                r.update({kk: m[kk] for kk in ("finale", "rend", "dd", "cagr", "mar", "trade", "wr", "senza_migliore")})
                EQ[a], TR[a] = eq, tt
            else:
                r.update({f"fin_{k}": m["finale"], f"dd_{k}": m["dd"], f"mar_{k}": m["mar"], f"n_{k}": m["trade"]})
        rows.append(r)
    d = pd.DataFrame(rows)

    # V8: media dei 7 ancoraggi (1/7 ciascuno, mai ribilanciati)
    def avg_row(name, x, s, e):
        eqs, ntr, wins = [], 0, []
        for a in DAYS:
            m, eq, tt = run_one(x, a, s, e)
            eqs.append(eq / 7)
            ntr += len(tt)
            wins += [t["pnl"] > 0 for t in tt]
        q = pd.concat(eqs, axis=1).ffill().sum(axis=1)
        e_ = q / q.iloc[0]
        yrs = (e_.index[-1] - e_.index[0]).days / 365.25
        dd = float((e_ / e_.cummax() - 1).min())
        cg = float(e_.iloc[-1]) ** (1 / yrs) - 1
        return dict(finale=float(q.iloc[-1]), rend=float(e_.iloc[-1] - 1) * 100, dd=dd * 100, cagr=cg * 100,
                    mar=cg / abs(dd), trade=ntr, wr=float(np.mean(wins) * 100)), q
    v8 = dict(giorno="media 7 ancoraggi (1/7 ciascuno)")
    for k, (x, s, e) in P.items():
        m, q = avg_row("v8", x, s, e)
        if k == "2021":
            v8.update(m)
            q.round(2).to_csv(HERE / "equity_media7.csv", header=["equity"])
        else:
            v8.update({f"fin_{k}": m["finale"], f"dd_{k}": m["dd"], f"mar_{k}": m["mar"], f"n_{k}": m["trade"]})

    # buy & hold
    def bh(x, s, e=None):
        c = x["close"][(x.index >= s) & ((x.index <= e) if e else True)]
        q = 10000 * c / c.iloc[0] * (1 - W.FEE_SPOT - W.SLIP) ** 2
        yrs = (q.index[-1] - q.index[0]).days / 365.25
        dd = float((q / q.cummax() - 1).min())
        cg = float(q.iloc[-1] / 10000) ** (1 / yrs) - 1
        return dict(finale=float(q.iloc[-1]), rend=(float(q.iloc[-1]) / 10000 - 1) * 100, dd=dd * 100, cagr=cg * 100,
                    mar=cg / abs(dd), trade=1, wr=np.nan)
    b = dict(giorno="buy & hold", **bh(f, "2021-01-01"))
    for k, (x, s, e) in P.items():
        if k != "2021":
            m = bh(x, s, e)
            b.update({f"fin_{k}": m["finale"], f"dd_{k}": m["dd"], f"mar_{k}": m["mar"], f"n_{k}": 1})
    full = pd.concat([d, pd.DataFrame([v8, b])], ignore_index=True)
    full.round(3).to_csv(HERE / "giorni.csv", index=False)
    # trade per giorno
    pd.DataFrame([dict(giorno=IT[a], **{k: t.get(k) for k in ("signal", "entry", "exit", "side", "expo", "entry_px",
                                                                 "exit_px", "reason", "pnl")}) for a in DAYS for t in TR[a]]
                 ).to_csv(HERE / "trade_giorni.csv", index=False)
    pd.DataFrame({IT[a]: EQ[a] for a in DAYS}).round(2).to_csv(HERE / "equity_giorni.csv")

    # sintesi
    def fmt(x):
        return f"{x:,.0f}".replace(",", ".")
    out.append("")
    out.append(f"{'giorno':<34}{'finale':>9}{'DD%':>7}{'CAGR%':>7}{'MAR':>6}{'trade':>6}{'WR%':>6}{'IS 21-23':>10}"
               f"{'OOS 24-':>9}{'18-20':>9}{'DD18-20':>8}{'senza top':>10}")
    for _, r in full.iterrows():
        out.append(f"{r['giorno']:<34}{fmt(r['finale']):>9}{r['dd']:>7.1f}{r['cagr']:>7.1f}{r['mar']:>6.2f}{int(r['trade']):>6}"
                   f"{r['wr']:>6.0f}{fmt(r['fin_IS']):>10}{fmt(r['fin_OOS']):>9}{fmt(r['fin_1820']):>9}{r['dd_1820']:>8.1f}"
                   f"{fmt(r['senza_migliore']) if pd.notna(r.get('senza_migliore')) else '':>10}")
    out.append("")
    for col, lab in (("finale", "finale 2021→"), ("dd", "DD 2021→"), ("mar", "MAR 2021→"), ("fin_IS", "IS 2021–23"),
                     ("fin_OOS", "OOS 2024→"), ("fin_1820", "2018–20"), ("dd_1820", "DD 2018–20"),
                     ("senza_migliore", "senza trade migliore")):
        v = d[col]
        sun = float(d.loc[d.giorno == "domenica", col].iloc[0])
        rank = int((v > sun).sum()) + 1   # 1 = migliore (valore più alto; per il DD il più alto è il meno profondo)
        pct = (v < sun).sum() / 6 * 100
        out.append(f"{lab:<22} media {v.mean():>10,.2f}  mediana {v.median():>10,.2f}  min {v.min():>10,.2f}  max {v.max():>10,.2f}"
                   f"  dev.st {v.std():>9,.2f}  CV {abs(v.std() / v.mean()) * 100:>5.1f}%  domenica {sun:>10,.2f} "
                   f"(posto {rank}/7, percentile {pct:.0f})")
    from scipy.stats import spearmanr
    rho = spearmanr(d["fin_IS"], d["fin_OOS"]).correlation
    rho2 = spearmanr(d["finale"], d["fin_1820"]).correlation
    out.append(f"Rango di Spearman IS/OOS sui 7 giorni: {rho:.2f}; 2021→ contro 2018–20: {rho2:.2f}")
    sun = d[d.giorno == "domenica"].iloc[0]
    out.append(f"Domenica / mediana finale 2021→: {sun['finale'] / d['finale'].median():.2f}; min / mediana: "
               f"{d['finale'].min() / d['finale'].median():.2f}")
    # quanto i giorni condividono i trade: date di ingresso entro 6 giorni dalla domenica
    s_entries = pd.to_datetime([t["entry"] for t in TR["SUN"]])
    for a in DAYS:
        en = pd.to_datetime([t["entry"] for t in TR[a]])
        common = sum(np.min(np.abs((s_entries - x).days)) <= 6 for x in en) if len(en) else 0
        out.append(f"  {IT[a]:<10} trade {len(en):>2}, di cui {common} con ingresso entro 6 giorni da un ingresso della domenica")
    txt = "\n".join(out)
    (HERE / "risultati.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
