"""Punto 3: confronto v1 (dati di Radar) contro W3.2 (radar.weekly.simulate dal 2018, versione Radar e versione dell'utente).
Prerequisito: python s2_w32.py (scrive w32_radar_equity.csv, w32_radar_trades.csv). Uscita: risultati.txt + csv."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from common import V, IMP, HERE, radar_daily

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


D = radar_daily()
END = D.index[-1]
IDX = pd.date_range("2018-01-01", END, freq="D")
S = V.simulate(D)
EV = S["equity"].reindex(IDX).ffill()
TV = [{"verso": t["verso"], "entra": t["entra"], "esce": t["esce"], "r": t["risultato"]} for t in S["trades"]]
PV = S["pos"].reindex(IDX).fillna(0.0)                       # posizione attiva nel giorno (rendimento close t-1 -> t)

EW = pd.read_csv(HERE / "w32_radar_equity.csv", index_col=0, parse_dates=True)["w32_equity"].reindex(IDX).ffill()
tw = pd.read_csv(HERE / "w32_radar_trades.csv")
TW = [{"verso": r.verso, "entra": r.entra, "esce": None if pd.isna(r.esce) else r.esce, "r": r.sul_capitale} for r in tw.itertuples()]
EU = pd.read_csv(IMP / "w32_equity_2018_2026.csv", index_col=0, parse_dates=True)["w32_equity"].reindex(IDX).ffill()
tu = pd.read_csv(IMP / "w32_operazioni_2018_2026.csv")
TU = [{"verso": r.verso, "entra": r.entra, "esce": None if pd.isna(r.esce) else r.esce, "r": r.sul_capitale} for r in tu.itertuples()]
BH = D["close"].reindex(IDX).ffill()


def side(trades, idx=IDX):
    s = pd.Series(0.0, idx)
    for t in trades:
        a, b = pd.Timestamp(t["entra"]), pd.Timestamp(t["esce"]) if t["esce"] else idx[-1]
        s.loc[a:b] = 1.0 if t["verso"] == "long" else -1.0
    return s


PW = side(TW)
L12 = str((END - pd.Timedelta(days=365)).date())
PER = [("Tutto 2018→oggi", "2018-01-01", None), ("2018–2021 (soglie v1 scelte qui)", "2018-01-01", "2021-12-31"),
       ("2022–2026 (mai visto dalla v1)", "2022-01-01", None), ("Dal 2021", "2021-01-01", None), ("Ultimi 12 mesi", L12, None),
       ("2018–2020", "2018-01-01", "2020-12-31"), ("2021–2023", "2021-01-01", "2023-12-31"), ("2024–oggi", "2024-01-01", None)]


def met(eq, trades=None, a=None, b=None):
    e = eq.loc[a:b].dropna()
    e = e / e.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    x = e.pct_change().dropna()
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    o = {"fin": 10000 * float(e.iloc[-1]), "cagr": cagr, "dd": dd, "mar": cagr / abs(dd) if dd < 0 else np.nan,
         "sharpe": float(x.mean() / x.std() * math.sqrt(365)) if x.std() > 0 else np.nan}
    if trades is not None:
        lo, hi = str(e.index[0].date()), str(e.index[-1].date())
        r = np.array([t["r"] for t in trades if lo <= t["entra"] <= hi])
        o |= {"n": len(r), "wr": float((r > 0).mean()) if len(r) else np.nan, "worst": float(r.min()) if len(r) else np.nan}
    return o


def p5050(e1, e2, a=None, b=None):
    """50% e 50% a capitali separati, senza ribilanciamento, aperto all'inizio del periodo."""
    x, y = e1.loc[a:b], e2.loc[a:b]
    return 0.5 * x / x.iloc[0] + 0.5 * y / y.iloc[0]


def fmt(o):
    s = f"{o['fin']:>9,.0f} $ | CAGR {100*o['cagr']:6.1f}% | DD {100*o['dd']:6.1f}% | MAR {o['mar']:5.2f} | Sharpe {o['sharpe']:4.2f}"
    if "n" in o:
        s += f" | op {o['n']:2d} | vinte {100*o['wr']:3.0f}% | peggiore {100*o['worst']:6.1f}%" if o["n"] else " | op  0"
    return s


rows = []
say(f"Dati: v1 su data/spot.csv + funding.csv (+ btc_giornaliero.csv prima del 01/09/2019); W3.2 radar.weekly.simulate dal 2018. Fino al {END.date()}.")
for lab, a, b in PER:
    say(f"\n== {lab} ==")
    R = {"W3.2 (Radar)": met(EW, TW, a, b), "v1": met(EV, TV, a, b), "50/50 W3.2+v1": met(p5050(EW, EV, a, b), None),
         "B&H BTC": met(BH, None, a, b), "W3.2 (utente)": met(EU, TU, a, b), "50/50 W3.2ut+v1": met(p5050(EU, EV, a, b), None)}
    for k, o in R.items():
        say(f"  {k:<16} {fmt(o)}")
        rows.append({"periodo": lab, "strategia": k, **o})
pd.DataFrame(rows).to_csv(HERE / "tab_periodi.csv", index=False, float_format="%.5f")

say("\n== Anno per anno (rendimento) ==")
yrows = []
for y in sorted(set(IDX.year)):
    def yr(e):
        z = e[e.index.year <= y]
        prev = e[e.index.year < y]
        return float(z.iloc[-1] / (prev.iloc[-1] if len(prev) else e.iloc[0]) - 1)
    r = {"anno": y, "W3.2": yr(EW), "v1": yr(EV), "50/50": yr(0.5 * EW + 0.5 * EV), "B&H": yr(BH), "W3.2 utente": yr(EU)}
    yrows.append(r)
    say(f"  {y}: W3.2 {100*r['W3.2']:+6.1f}% | v1 {100*r['v1']:+6.1f}% | 50/50 (dal 2018) {100*r['50/50']:+6.1f}% | B&H {100*r['B&H']:+6.1f}% | W3.2 utente {100*r['W3.2 utente']:+6.1f}%")
pd.DataFrame(yrows).to_csv(HERE / "tab_anni.csv", index=False, float_format="%.4f")
say("  v1 meglio di W3.2 negli anni:", [r["anno"] for r in yrows if r["v1"] > r["W3.2"]])

say("\n== Senza le 3 operazioni migliori (prodotto dei risultati sul capitale) ==")
for lab, a in (("Tutto", "2018-01-01"), ("2022–2026", "2022-01-01"), ("Dal 2021", "2021-01-01")):
    for k, T in (("W3.2", TW), ("v1", TV), ("W3.2 utente", TU)):
        r = np.sort([t["r"] for t in T if t["entra"] >= a])[::-1]
        say(f"  {lab:<10} {k:<12} con tutte x{np.prod(1+r):6.2f} | senza le 3 migliori x{np.prod(1+r[3:]):5.2f} | senza la migliore x{np.prod(1+r[1:]):5.2f} | migliori {np.round(100*r[:3],1)}")

say("\n== Correlazione dei rendimenti giornalieri W3.2–v1 ==")
rw, rv, rb = EW.pct_change().fillna(0), EV.pct_change().fillna(0), BH.pct_change().fillna(0)
for lab, a, b in PER[:5]:
    say(f"  {lab:<34} {rw.loc[a:b].corr(rv.loc[a:b]):.2f}  (W3.2–BTC {rw.loc[a:b].corr(rb.loc[a:b]):.2f}, v1–BTC {rv.loc[a:b].corr(rb.loc[a:b]):.2f})")
mm = pd.concat([rw, rv], axis=1).resample("ME").apply(lambda z: (1 + z).prod() - 1)
say(f"  mensile, tutto: {mm.corr().iloc[0,1]:.2f}")

say("\n== Quando sono d'accordo (giorni 2018→oggi; rendimento composto nei giorni dello stato e annualizzato) ==")
acc = []
for lab, a in (("Tutto", "2018-01-01"), ("2022–2026", "2022-01-01")):
    pw, pv = PW.loc[a:], PV.loc[a:]
    st = [("Entrambe long", (pw > 0) & (pv > 0)), ("Entrambe short", (pw < 0) & (pv < 0)), ("Entrambe fuori", (pw == 0) & (pv == 0)),
          ("Solo W3.2 in posizione", (pw != 0) & (pv == 0)), ("Solo v1 in posizione", (pw == 0) & (pv != 0)), ("Versi opposti", pw * pv < 0)]
    say(f" [{lab}]")
    for s, m in st:
        n = int(m.sum())
        cum = lambda r: float((1 + r[m.reindex(r.index, fill_value=False)]).prod() - 1)
        ann = lambda r: (1 + cum(r)) ** (365 / n) - 1 if n > 30 else np.nan
        o = {"periodo": lab, "stato": s, "giorni": n, "quota": n / len(pw), "btc_cum": cum(rb.loc[a:]), "w32_cum": cum(rw.loc[a:]),
             "v1_cum": cum(rv.loc[a:]), "btc_ann": ann(rb.loc[a:]), "w32_ann": ann(rw.loc[a:]), "v1_ann": ann(rv.loc[a:])}
        acc.append(o)
        say(f"  {s:<24} {n:5d} g ({100*o['quota']:4.1f}%) | BTC {100*o['btc_cum']:+7.1f}% | W3.2 {100*o['w32_cum']:+7.1f}% | v1 {100*o['v1_cum']:+7.1f}%"
            + (f" | annuo BTC {100*o['btc_ann']:+6.0f}% W3.2 {100*o['w32_ann']:+6.0f}% v1 {100*o['v1_ann']:+6.0f}%" if n > 30 else ""))
pd.DataFrame(acc).to_csv(HERE / "tab_accordo.csv", index=False, float_format="%.4f")

# ---------------------------------------------------------------- robustezza descrittiva della v1 (soglie vicine, ritardo, placebo)
SC = S["score"]


def decide(sc, tl, ts, ex):
    x, out, cur = sc.to_numpy(), np.zeros(len(sc)), 0.0
    for i in range(len(x)):
        if np.isfinite(x[i]):
            if cur > 0 and x[i] < ex:
                cur = 0.0
            if cur < 0 and x[i] > -ex:
                cur = 0.0
            if cur == 0:
                cur = 1.0 if x[i] >= tl else -1.0 if x[i] <= -ts else 0.0
        out[i] = cur
    return pd.Series(out, sc.index)


assert decide(SC, V.TH_LONG, V.TH_SHORT, V.EXIT).equals(S["pos_decisa"])
say("\n== v1 con soglie vicine (solo descrittivo, NON per sceglierle). Voti a passi di 1/17 = 0,059 ==")
grid = []
for dl in (-0.10, -0.05, 0, 0.05, 0.10):
    for ds in (-0.10, -0.05, 0, 0.05, 0.10):
        for de in (-0.10, -0.05, 0, 0.05, 0.10):
            tl, ts, ex = V.TH_LONG + dl, min(1.0, V.TH_SHORT + ds), V.EXIT + de
            e = V.run(D, decide(SC, tl, ts, ex))["equity"].reindex(IDX).ffill()
            grid.append({"long": tl, "short": -ts, "uscita": ex, "fin_tutto": met(e)["fin"], "dd_tutto": met(e)["dd"],
                         "fin_2226": met(e, None, "2022-01-01")["fin"], "dd_2226": met(e, None, "2022-01-01")["dd"],
                         "fin_2021": met(e, None, "2021-01-01")["fin"], "uno_alla_volta": (dl != 0) + (ds != 0) + (de != 0) <= 1})
G = pd.DataFrame(grid)
G.to_csv(HERE / "tab_soglie_vicine.csv", index=False, float_format="%.4f")
w_t, w_22, w_21 = met(EW)["fin"], met(EW, None, "2022-01-01")["fin"], met(EW, None, "2021-01-01")["fin"]
for lab, g in (("125 combinazioni", G), ("una soglia alla volta (13)", G[G.uno_alla_volta])):
    say(f"  {lab}: tutto mediana {g.fin_tutto.median():,.0f} (min {g.fin_tutto.min():,.0f}, max {g.fin_tutto.max():,.0f}), DD mediano {100*g.dd_tutto.median():.1f}%"
        f" | 2022–26 mediana {g.fin_2226.median():,.0f} (min {g.fin_2226.min():,.0f}, max {g.fin_2226.max():,.0f}), DD mediano {100*g.dd_2226.median():.1f}%"
        f" | sopra W3.2: tutto {int((g.fin_tutto > w_t).sum())}/{len(g)}, 2022–26 {int((g.fin_2226 > w_22).sum())}/{len(g)}, dal 2021 {int((g.fin_2021 > w_21).sum())}/{len(g)}")
for r in G[G.uno_alla_volta].itertuples():
    say(f"    long {r.long:+.2f} short {r.short:+.2f} uscita {r.uscita:+.2f}: tutto {r.fin_tutto:>9,.0f} (DD {100*r.dd_tutto:5.1f}%) | 2022–26 {r.fin_2226:>8,.0f} (DD {100*r.dd_2226:5.1f}%)")

say("\n== v1 eseguita con ritardo (1 e 2 giorni) ==")
for k in (1, 2):
    e = V.run(D, S["pos_decisa"].shift(k).fillna(0))["equity"].reindex(IDX).ffill()
    say(f"  +{k} g: tutto {fmt(met(e))} | 2022–26 {met(e, None, '2022-01-01')['fin']:,.0f}")

say("\n== Placebo: posizione della v1 spostata in blocco nel tempo (stessi trade, stessi tempi in posizione, date casuali) ==")
rng = np.random.default_rng(20261125)
pos = S["pos_decisa"]
base = pos.loc["2018-01-01":].to_numpy()
pl = []
for k in range(1000):
    sh = int(rng.integers(60, len(base) - 60))
    p = pd.Series(0.0, pos.index)
    p.loc["2018-01-01":] = np.roll(base, sh)
    e = V.run(D, p)["equity"].reindex(IDX).ffill()
    pl.append((met(e)["fin"], met(e, None, "2022-01-01")["fin"], met(e)["dd"]))
pl = np.array(pl)
for j, (lab, act) in enumerate((("tutto", met(EV)["fin"]), ("2022–26", met(EV, None, "2022-01-01")["fin"]))):
    say(f"  {lab}: v1 {act:,.0f} | placebo mediana {np.median(pl[:, j]):,.0f}, 95° pct {np.percentile(pl[:, j], 95):,.0f} | p = {float((pl[:, j] >= act).mean()):.3f}")

open(HERE / "risultati.txt", "w").write("\n".join(OUT) + "\n")
