"""Previsionale 2 · utilità per W3.2 (PREREG §6): 3 varianti. Motore research/p2_nuovi/p2_engine.simulate (nessuna modifica).
Riusa stats/delta_trades di research/previsionale/fc_w32.py. Uso: python3 research/previsionale2/p2_w32.py (dopo p2_run.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import build  # noqa: E402
import fc_w32 as F  # noqa: E402  (porta con sé p2_engine come F.E e radar.weekly come F.W)
from fc_data import frozen  # noqa: E402

E, W = F.E, F.W
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def hooks(kind: str, s: pd.Series) -> dict:
    g = lambda day: float(s.get(day, 0.0))  # noqa: E731
    if kind == "A":      # s = 1 se politica restrittiva (pol > 0 e nl13 < 0): nessun nuovo long
        return dict(allow=lambda side, day: not (side > 0 and g(day) > 0))
    if kind == "B":      # s = 1 se volatilità alta: esposizione all'ingresso dimezzata
        return dict(expo_fn=lambda side, wk, day: W.exposure(side, wk["close"], wk["atr"]) * (0.5 if g(day) > 0 else 1.0))
    if kind == "C":      # s = chiamata relativa a 30 giorni di RP (+1/−1/0): ingresso bloccato se contraria
        return dict(allow=lambda side, day: side * g(day) >= 0)
    raise ValueError(kind)


def main() -> None:
    f, fl = frozen()
    wb = W.weekly_bars(f)
    d = build()
    cond = {"A": ((d["pol"] > 0) & (d["nl13"] < 0)).astype(float), "B": (d["V"] == "A").astype(float),
            "C": pd.read_csv(HERE / "prob2_h30.csv", index_col=0, parse_dates=True)["c_RP"].astype(float)}
    names = {"A": "A · niente nuovi long con politica restrittiva", "B": "B · esposizione ×0,5 in alta volatilità", "C": "C · blocco se RP 30 g contrario"}
    base = E.simulate(f, wb=wb)
    sb = F.stats(base)
    c = f["close"][f.index >= "2021-01-01"]
    bh = 10000 * c / c.iloc[0]
    say(f"Buy & hold: {bh.iloc[-1]:,.0f} $, DD {(bh / bh.cummax() - 1).min():.1%}")
    say("Trade W3.2 e condizioni alla domenica del segnale (A restrittiva, B vol alta, C chiamata RP30):")
    for t in base["trades"]:
        day = pd.Timestamp(t["signal"])
        say(f"  {t['signal']} {t['side']:<5} pnl {t['pnl']:+.1%}  A {cond['A'].get(day, np.nan):.0f}  B {cond['B'].get(day, np.nan):.0f}  C {cond['C'].get(day, np.nan):+.0f}"
            f"  (pol {d['pol'].get(day, np.nan):+.2f}, nl13 {d['nl13'].get(day, np.nan):+.1f}%, T {d['T'].get(day)}, V {d['V'].get(day)})")
    rows = [dict(variante="W3.2", **sb, d_log=0.0, d_senza2=0.0, trade_cambiati=0, placebo_pct=np.nan, passa=None)]
    rng = np.random.default_rng(113)
    for k in "ABC":
        r = E.simulate(f, wb=wb, **hooks(k, cond[k]))
        st = F.stats(r)
        dl, d2, ch = F.delta_trades(r, base)
        s = cond[k][cond[k].index >= "2021-01-01"]
        mars = [F.stats(E.simulate(f, wb=wb, **hooks(k, pd.Series(np.roll(s.to_numpy(), int(j)), index=s.index))))["mar"]
                for j in rng.integers(60, len(s) - 60, size=200)]
        pct = float(np.mean(np.array(mars) < st["mar"]))
        ok = (st["mar"] > sb["mar"] and all(st[f"mar_{h}"] > sb[f"mar_{h}"] for h in F.HALVES) and st["dd"] >= -0.30 and st["wr"] >= 0.70
              and st["finale"] >= sb["finale"] and d2 > 0 and pct >= 0.95)
        rows.append(dict(variante=names[k], **st, d_log=dl, d_senza2=d2, trade_cambiati=ch, placebo_pct=pct, passa=bool(ok)))
        ev = [e for e in r["events"] if e["kind"] in ("blocked", "rebal")]
        say(f"{k}: giorni con condizione vera dal 2021 {np.mean(s != 0):.0%}; eventi {[(str(e['day'])[:10], e['kind'], e['side']) for e in ev][:14]} ({len(ev)})")
    t = pd.DataFrame(rows)
    say("\n" + t.round(3).to_string(index=False))
    t.to_csv(HERE / "w32_varianti2.csv", index=False, float_format="%.4f")
    b18 = E.simulate(fl, start="2018-01-01", end="2020-12-31")
    say(f"\n2018–20 (informativo): W3.2 {b18['equity'].iloc[-1]:,.0f} $, DD {(b18['equity'] / b18['equity'].cummax() - 1).min():.1%}, trade {len(b18['trades'])}")
    for k in "ABC":
        r = E.simulate(fl, start="2018-01-01", end="2020-12-31", **hooks(k, cond[k]))
        e = r["equity"]
        pn = [x["pnl"] for x in r["trades"]]
        say(f"  {k}: {e.iloc[-1]:,.0f} $, DD {(e / e.cummax() - 1).min():.1%}, trade {len(pn)}, WR {np.mean(np.array(pn) > 0) if pn else float('nan'):.0%}")
    (HERE / "risultati_w32.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
