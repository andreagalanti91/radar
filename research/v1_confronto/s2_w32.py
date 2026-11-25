"""Punto 2: W3.2 dal 2018 con radar.weekly.simulate (invariato) sul frame lungo della ricerca + dati di Radar,
confrontata con la versione dell'utente (w32_operazioni/equity_2018_2026.csv). Salva w32_radar_equity.csv e w32_radar_trades.csv."""
import sys

import numpy as np
import pandas as pd

from common import ROOT, IMP, HERE

sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
from p2_data import load  # noqa: E402
from radar import weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

FL = load()["fl"]
FV = build_features(load_all())
FV = FV[FV["close"].notna()]
# f_long congelato al 15/11 (prezzi identici a data/; pf14z stimato dal CVD spot dove manca il flusso perp, cioè fino all'11/04/2020)
# + i giorni successivi presi da build_features(data/), così la serie arriva all'ultimo giorno chiuso di Radar
F = pd.concat([FL, FV[FV.index > FL.index[-1]]]).sort_index()
assert (FV["pf14z"].reindex(FL.index).dropna() - FL["pf14z"].reindex(FV["pf14z"].dropna().index).reindex(FL.index).dropna()).abs().max() < 1e-9


def tlist(r):
    out = []
    for t in r["trades"] + ([dict(r["open"], exit=None, exit_px=None, reason="open", pnl=r["open"]["pnl_close"])] if r["open"] else []):
        out.append({"verso": t["side"], "segnale": t["signal"], "entra": t["entry"], "esce": t["exit"], "prezzo_in": t["entry_px"],
                    "prezzo_out": t["exit_px"], "esposizione": t["expo"], "sul_capitale": t["pnl"], "uscita": W.REASONS.get(t["reason"], t["reason"])})
    return out


def fin(eq, a=None, b=None):
    e = eq.loc[a:b]
    e = e / e.iloc[0]
    return round(10000 * float(e.iloc[-1])), round(100 * float((e / e.cummax() - 1).min()), 1)


if __name__ == "__main__":
    r = W.simulate(F, start="2018-01-01")
    eq = r["equity"] / r["equity"].iloc[0]
    tr = pd.DataFrame(tlist(r))
    eq.rename("w32_equity").to_csv(HERE / "w32_radar_equity.csv")
    tr.to_csv(HERE / "w32_radar_trades.csv", index=False)
    print("RADAR continua dal 2018 al", eq.index[-1].date(), ":", fin(eq), "| trade", len(tr))
    print("  al 15/11 (dati congelati della ricerca):", fin(eq, None, "2026-11-15"))
    r15 = W.simulate(FL, start="2018-01-01")
    print("  controllo: simulate su f_long congelato al 15/11:", round(float(r15["equity"].iloc[-1])), "(atteso 224.593)")
    r21 = W.simulate(FV, start="2021-01-01")
    print("  controllo: dal 2021 sui dati del tool:", round(float(r21["equity"].iloc[-1])), "trade", len(r21["trades"]) + bool(r21["open"]))
    print("  dal 2021 come segmento della serie continua:", fin(eq, "2021-01-01"))

    ue = pd.read_csv(IMP / "w32_equity_2018_2026.csv", index_col=0, parse_dates=True)["w32_equity"]
    ut = pd.read_csv(IMP / "w32_operazioni_2018_2026.csv")
    print("UTENTE:", fin(ue), "| trade", len(ut), "| fino al", ue.index[-1].date())
    print("  utente al 21/11:", fin(ue, None, "2026-11-21"), "| radar al 21/11:", fin(eq, None, "2026-11-21"))
    # versione "cucita" come l'utente: 2018-20 su frame lungo chiuso al 31/12/2020 + dal 2021 W.simulate(dati del tool)
    a = W.simulate(F[F.index <= "2020-12-31"], start="2018-01-01")
    ea = a["equity"] / a["equity"].iloc[0]
    if a["open"]:
        last = a["open"]
        ea.iloc[-1] = ea.iloc[-1] * (1 + last["pnl_close"]) / (1 + last["pnl"])   # chiusura d'ufficio con commissione
    eb = r21["equity"] / r21["equity"].iloc[0]
    stitched = pd.concat([ea, eb * ea.iloc[-1]])
    print("  ricostruzione 'cucita' al 31/12/2020 come l'utente:", fin(stitched), "| al 21/11", fin(stitched, None, "2026-11-21"))
    stitched.rename("w32_equity").to_csv(HERE / "w32_radar_cucita_equity.csv")

    # trade per trade
    m = ut.merge(tr, on=["verso", "entra"], how="outer", suffixes=("_u", "_r"), indicator=True).sort_values("entra")
    pd.set_option("display.width", 250)
    cols = ["verso", "entra", "esce_u", "esce_r", "prezzo_in_u", "prezzo_in_r", "prezzo_out_u", "prezzo_out_r", "esposizione_u", "esposizione_r",
            "sul_capitale_u", "sul_capitale_r", "_merge"]
    print(m[cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    # contributo per anno
    for y in range(2018, 2027):
        f = lambda e: float(e[e.index.year == y].iloc[-1] / (e[e.index.year < y].iloc[-1] if (e.index.year < y).any() else 1) - 1)
        print(y, "radar %+.1f%%  utente %+.1f%%  cucita %+.1f%%" % (100 * f(eq), 100 * f(ue), 100 * f(stitched)))
