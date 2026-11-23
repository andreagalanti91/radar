"""Previsionale · utilità per W3.2 (PREREG §7). Motore: research/p2_nuovi/p2_engine.simulate (copia verificata di
radar.weekly.simulate con agganci); nessuna modifica a radar/. Probabilità: M4 walk-forward (prob_h7.csv, prob_h30.csv).
Uso: python3 research/previsionale/fc_w32.py   (dopo fc_run.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
import p2_engine as E  # noqa: E402
from fc_data import frozen  # noqa: E402
from radar import weekly as W  # noqa: E402

LO, HI, SLO, SHI = 0.45, 0.55, 0.40, 0.60
HALVES = {"2021-23": ("2021-01-01", "2023-12-31"), "2024-26": ("2024-01-01", "2026-12-31")}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def state(p: float, side: int, lo=LO, hi=HI) -> int:
    """+1 concorda, −1 discorda, 0 neutro (o probabilità assente)."""
    if not np.isfinite(p):
        return 0
    up = 1 if p > hi else (-1 if p < lo else 0)
    return up * side


def make(kind: str, p: pd.Series, lo=LO, hi=HI, n=2, m=(1.25, 0.75), slo=SLO, shi=SHI) -> dict:
    g = lambda day: float(p.get(day, np.nan))  # noqa: E731
    if kind == "Fa":
        return dict(allow=lambda side, day: state(g(day), side, lo, hi) >= 0)
    if kind == "Fb":
        return dict(allow=lambda side, day: state(g(day), side, lo, hi) > 0)
    if kind == "D":
        def expo(side, wk, day):
            e, s = W.exposure(side, wk["close"], wk["atr"]), g(day)
            strong = np.isfinite(s) and ((side > 0 and s >= shi) or (side < 0 and s <= slo))
            mult = m[0] if strong else (m[1] if state(s, side, lo, hi) < 0 else 1.0)
            return min(1.0, mult * e)
        return dict(expo_fn=expo)
    if kind == "U":
        def rebal(side, wk, day, tr):
            if tr.get("_out"):
                return None
            days = [day - pd.Timedelta(days=7 * i) for i in range(n)]
            if all(d >= pd.Timestamp(tr["signal"]) and state(g(d), side, lo, hi) < 0 for d in days):
                tr["_out"] = True
                return 0.0
            return None
        return dict(rebal_fn=rebal)
    raise ValueError(kind)


def seg(eq: pd.Series, a: str, b: str) -> dict:
    e = eq[(eq.index >= a) & (eq.index <= b)]
    e0 = eq[eq.index < a].iloc[-1] if (eq.index < a).any() else 10000.0
    yrs = len(e) / 365.25
    cagr = (e.iloc[-1] / e0) ** (1 / yrs) - 1
    full = pd.concat([pd.Series([e0]), e])
    dd = float((full / full.cummax() - 1).min())
    return dict(cagr=cagr, dd=dd, mar=cagr / abs(dd) if dd < 0 else np.nan, fin=float(e.iloc[-1]))


def stats(r: dict) -> dict:
    eq, tr = r["equity"], r["trades"]
    a = seg(eq, "2021-01-01", "2026-12-31")
    pn = np.array([t["pnl"] for t in tr])
    out = dict(finale=a["fin"], rend=a["fin"] / 10000 - 1, dd=a["dd"], trade=len(tr), wr=float((pn > 0).mean()) if len(pn) else np.nan,
               cagr=a["cagr"], mar=a["mar"])
    for k, (x, y) in HALVES.items():
        out[f"mar_{k}"] = seg(eq, x, y)["mar"]
    return out


def delta_trades(r: dict, base: dict) -> tuple[float, float, int]:
    """Somma dei delta log-rendimento per trade (abbinati per data del segnale) e somma senza i 2 più favorevoli."""
    a = {t["signal"]: np.log1p(t["pnl"]) for t in r["trades"]}
    b = {t["signal"]: np.log1p(t["pnl"]) for t in base["trades"]}
    d = np.array([a.get(k, 0.0) - b.get(k, 0.0) for k in sorted(set(a) | set(b))])
    ch = int((np.abs(d) > 1e-9).sum())
    return float(d.sum()), float(np.sort(d)[:-2].sum()) if len(d) > 2 else 0.0, ch


def main() -> None:
    f, fl = frozen()
    wb = W.weekly_bars(f)
    P = {h: pd.read_csv(HERE / f"prob_h{h}.csv", index_col=0, parse_dates=True)["p4"] for h in (7, 30)}
    base = E.simulate(f, wb=wb)
    ref = W.simulate(f)
    say("Motore di ricerca = radar.weekly.simulate:", np.allclose(base["equity"].to_numpy(), ref["equity"].to_numpy(), atol=1e-6))
    sb = stats(base)
    c = f["close"][f.index >= "2021-01-01"]
    bh = 10000 * c / c.iloc[0]
    say(f"Buy & hold: {bh.iloc[-1]:,.0f} $, DD {(bh / bh.cummax() - 1).min():.1%}")
    sun = [d for d in wb.index if d >= pd.Timestamp("2021-01-01")]
    for h in (7, 30):
        s = P[h].reindex(sun)
        say(f"p{h} alle domeniche dal 2021: n {s.notna().sum()}, >55% {np.mean(s > HI):.0%}, <45% {np.mean(s < LO):.0%}, ≥60% {np.mean(s >= SHI):.0%}, ≤40% {np.mean(s <= SLO):.0%}")
    say("Trade W3.2 e probabilità alla domenica del segnale:")
    for t in base["trades"]:
        d = pd.Timestamp(t["signal"])
        say(f"  {t['signal']} {t['side']:<5} pnl {t['pnl']:+.1%}  p7 {P[7].get(d, np.nan):.3f}  p30 {P[30].get(d, np.nan):.3f}")
    rows = [dict(variante="W3.2", **sb, d_log=0.0, d_senza2=0.0, trade_cambiati=0, placebo_pct=np.nan)]
    rng = np.random.default_rng(112)
    VAR = [("F7a", "Fa", 7), ("F7b", "Fb", 7), ("F30a", "Fa", 30), ("F30b", "Fb", 30), ("D7", "D", 7), ("D30", "D", 30), ("U7", "U", 7), ("U30", "U", 30)]
    for name, kind, h in VAR:
        r = E.simulate(f, wb=wb, **make(kind, P[h]))
        st = stats(r)
        dl, d2, ch = delta_trades(r, base)
        p = P[h][P[h].index >= "2021-01-01"]
        mars = []
        for k in rng.integers(60, len(p) - 60, size=200):
            ps = pd.Series(np.roll(p.to_numpy(), int(k)), index=p.index)
            mars.append(stats(E.simulate(f, wb=wb, **make(kind, ps)))["mar"])
        pct = float(np.mean(np.array(mars) < st["mar"]))
        rows.append(dict(variante=name, **st, d_log=dl, d_senza2=d2, trade_cambiati=ch, placebo_pct=pct))
        ok = (st["mar"] > sb["mar"] and all(st[f"mar_{k}"] > sb[f"mar_{k}"] for k in HALVES) and st["dd"] >= -0.30 and st["wr"] >= 0.70
              and st["finale"] >= sb["finale"] and d2 > 0 and pct >= 0.95)
        rows[-1]["passa"] = bool(ok)
        ev = [e for e in r["events"] if e["kind"] in ("blocked", "rebal")]
        say(f"{name}: eventi {[(e['day'], e['kind'], e['side']) for e in ev][:12]}{' …' if len(ev) > 12 else ''} ({len(ev)})")
    t = pd.DataFrame(rows)
    say("\n" + t.round(3).to_string(index=False))
    t.to_csv(HERE / "w32_varianti.csv", index=False, float_format="%.4f")
    # 2018–20 informativo (probabilità walk-forward dal 2018; dati f_long)
    b18 = E.simulate(fl, start="2018-01-01", end="2020-12-31")
    say("\n2018–20 (informativo): W3.2", f"{b18['equity'].iloc[-1]:,.0f} $, DD {(b18['equity'] / b18['equity'].cummax() - 1).min():.1%}, trade {len(b18['trades'])}")
    for name, kind, h in VAR:
        r = E.simulate(fl, start="2018-01-01", end="2020-12-31", **make(kind, P[h]))
        e = r["equity"]
        pn = [x["pnl"] for x in r["trades"]]
        say(f"  {name}: {e.iloc[-1]:,.0f} $, DD {(e / e.cummax() - 1).min():.1%}, trade {len(pn)}, WR {np.mean(np.array(pn) > 0) if pn else float('nan'):.0%}")
    (HERE / "risultati_w32.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
