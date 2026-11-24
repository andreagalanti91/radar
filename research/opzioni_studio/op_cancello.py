"""Opzioni · fase 2 · CANCELLO (PREREG, ADDENDUM-1 punto 6): il motore con superficie.py riproduce le 23 operazioni di
storico_prezzi_veri.csv? Scarto mediano del moltiplicatore entro ±15%, altrimenti ci si ferma.

A · stesso contratto e stesse date del CSV, prezzi della superficie (12:00 UTC, F = prezzo Binance delle 12:00).
B · contratto scelto dal motore (venerdì quotato più vicino a 30 giorni, prezzo d'esercizio più vicino sulla griglia reale),
    date del CSV.
Più il finale di B0 (sequenza completa, 5%, uscite di W3.2 vere) dal 2018 e dal 2019, da confrontare con lo studio dell'utente
(≈ 50.642 $ dal 2018, ≈ 48.543 $ dal 2019). Uscita: cache/cancello_23.csv e testo su stdout (in risultati.txt da op_fase2).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
import op_segnali as S  # noqa: E402
from op_prezzatore import PrezzatoreSuperficie  # noqa: E402


class Forzato:
    """La superficie, ma con scadenza e prezzo d'esercizio del CSV nel giorno d'ingresso."""

    def __init__(self, base: PrezzatoreSuperficie, fissi: dict):
        self.b, self.f, self.ora = base, fissi, base.ora

    def scadenze(self, d):
        x = self.f.get(pd.Timestamp(d))
        return [x[0]] if x else self.b.scadenze(d)

    def strikes(self, d, e):
        x = self.f.get(pd.Timestamp(d))
        return [x[1]] if x else self.b.strikes(d, e)

    def __getattr__(self, k):
        return getattr(self.b, k)


FIN = (20, 50)   # ADDENDUM-2: finestra della regola in uso (radar/opzioni.py GG_MIN/GG_MAX); None = ciclo 1


def conto(m) -> float:
    """Conto composto da 10.000 $ con il 5% speso per operazione: 10.000 × Π(1 + 0,05 (mult − 1))."""
    return 10_000 * float(pd.Series(m).dropna().apply(lambda x: 1 + 0.05 * (x - 1)).prod())


def contratti() -> dict:
    c = pd.read_csv(S.CSV_VERI)
    out = {}
    for _, r in c.iterrows():
        _, e, K, t = r["contratto"].split("-")
        exp = pd.Timestamp(2000 + int(e[-2:]), E.PrezzatoreB0Provvisorio.MON[e[-5:-2]], int(e[:-5]))
        out[pd.Timestamp(r["entra"])] = (exp, float(K))
    return out


def per_operazione(pz, last, fin=None) -> pd.DataFrame:
    c = pd.read_csv(S.CSV_VERI)
    days = pd.date_range("2018-01-01", last)
    m = E.Motore(pz, E.Conf(exer=0.00015, finestra=fin))
    rows = []
    for _, r in c.iterrows():
        d0 = pd.Timestamp(r["entra"])
        usc = {}
        if r["esce"] != "aperta":
            d1 = pd.Timestamp(r["esce"])
            usc[d1] = "apertura" if d1.dayofweek == 0 else "chiusura"
        res = m.simula(E.Piano("eventi", {d0: 1 if r["verso"] == "long" else -1}, usc), days, str(d0.date()))
        if not res["trades"]:
            rows.append({"n": r["n"], "entra": r["entra"], "contratto_csv": r["contratto"], "contratto_motore": "saltata",
                         "esito": "saltata (nessun venerdì fra 20 e 50 giorni)", "mult_csv": round(r["mult"], 4),
                         "mult_motore": np.nan, "scarto_rel": np.nan, "giorni": np.nan, "qual_ingresso": None})
            continue
        t = res["trades"][0]
        g = t["legs"][0]
        rows.append({"n": r["n"], "entra": r["entra"], "contratto_csv": r["contratto"],
                     "contratto_motore": f"{g['exp'].date()} {g['K']:.0f}{g['tipo']}", "giorni": t["giorni_scad"],
                     "esito": t["motivo"], "mult_csv": round(r["mult"], 4), "mult_motore": round(t["mult"], 4),
                     "scarto_rel": round(t["mult"] / r["mult"] - 1, 4) if r["mult"] > 0 else (0.0 if t["mult"] == 0 else np.nan),
                     "qual_ingresso": g["qual"][0]})
    return pd.DataFrame(rows)


def main() -> list[str]:
    out = []
    last = S.frame().index[-1]
    base = PrezzatoreSuperficie()
    a = per_operazione(Forzato(base, contratti()), last)
    b = per_operazione(base, last, FIN)
    t = a.merge(b[["n", "contratto_motore", "giorni", "esito", "mult_motore", "scarto_rel"]], on="n", suffixes=("_A", "_B"))
    t.to_csv(HERE / "cache" / "cancello_23.csv", index=False)
    out.append("CANCELLO · 23 operazioni, moltiplicatore (incasso / spesa) contro storico_prezzi_veri.csv")
    out.append(t.to_string(index=False))
    mA, mB = a["scarto_rel"].median(), b["scarto_rel"].median()
    out.append(f"Scarto mediano relativo (prova del prezzatore, stesso contratto): A {mA:+.1%} · soglia ±15% "
               f"(B, contratto diverso, solo informativo: {mB:+.1%})")
    ch = a["n"] < 23
    out.append(f"Conto composto (5% per operazione, n. 1–22 chiuse): moltiplicatori veri del CSV {conto(a.loc[ch, 'mult_csv']):,.0f} $ · "
               f"motore sugli stessi contratti (A) {conto(a.loc[ch, 'mult_motore']):,.0f} $ · senza la n. 3: CSV "
               f"{conto(a.loc[ch & (a['n'] != 3), 'mult_csv']):,.0f} $, A {conto(a.loc[ch & (a['n'] != 3), 'mult_motore']):,.0f} $")
    okb = b["mult_motore"].notna() & (b["n"] < 23)
    out.append(f"B (contratto della regola 20–50 giorni, {int(okb.sum())} operazioni, saltate "
               f"{int(b['mult_motore'].isna().sum())}): conto composto {conto(b.loc[okb, 'mult_motore']):,.0f} $")
    out.append(f"Scarto mediano assoluto del moltiplicatore: A {(a['mult_motore'] - a['mult_csv']).abs().median():.3f} · "
               f"B {(b['mult_motore'] - b['mult_csv']).abs().median():.3f}")
    ok = abs(mA) <= 0.15
    out.append("CANCELLO " + ("SUPERATO" if ok else "NON SUPERATO: ci si ferma"))
    # B0 in sequenza (uscite vere di W3.2, n. 9 al 2021-01-04)
    tr = pd.read_csv(HERE / "cache" / "op_w32_trades.csv")
    days = pd.date_range("2018-01-01", last)
    pi = E.piano_w32(tr, days)
    for lab, da in (("dal 2018", "2018-01-01"), ("dal 2019", "2019-01-01")):
        r = E.Motore(base, E.Conf(finestra=FIN)).simula(pi, days, da)
        m = E.metriche(r)
        out.append(f"B0r {lab} (saltate {len(r['saltate'])}): 10.000 → {m['finale']:,.0f} $ · DD {m['dd']:.1%} · operazioni chiuse {m['n']} · "
                   f"in guadagno {m['quota_guadagno']:.0%}  (studio dell'utente: {'≈ 50.642' if da < '2019' else '≈ 48.543'} $, "
                   "fino al 23/11 e n. 9 tagliata al 31/12/2020)")
    print("\n".join(out))
    return out, ok


if __name__ == "__main__":
    main()
