"""Opzioni · fase 1 · test del motore (unittest). Uso: python3 research/opzioni_studio/op_test.py [-v]

1. Riproduzione delle 23 operazioni di storico_prezzi_veri.csv con il prezzatore provvisorio B0 (Black-76, iv_vera del CSV,
   contratto del CSV, date d'ingresso e d'uscita del CSV, esercizio 0,015% come nello studio dell'utente): casi "scadenza"
   entro 0,05 di moltiplicatore (il regolamento qui è l'apertura oraria Binance delle 08:00, lo studio usava un altro
   prezzo di Binance); scarto mediano relativo su tutte entro ±15% (soglia del PREREG). Tabella in cache/op_test_23.csv.
2. Test sintetici (prezzi inventati, nessun dato di mercato): costi, scadenza, U1–U5, straddle, una posizione per volta,
   DD giornaliero, placebo.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
import op_segnali as S  # noqa: E402

CSV = S.CSV_VERI


def riproduci_23() -> pd.DataFrame:
    f = S.frame()
    st = S.settle_0800()
    pz = E.PrezzatoreB0Provvisorio(CSV, f, st)
    days = pd.date_range("2018-01-01", f.index[-1])
    conf = E.Conf(exer=0.00015)   # lo studio dell'utente usava 0,015% di regolamento
    m = E.Motore(pz, conf, st)
    c = pd.read_csv(CSV)
    rows = []
    for _, r in c.iterrows():
        d0 = pd.Timestamp(r["entra"])
        usc = {}
        if r["esce"] != "aperta":
            d1 = pd.Timestamp(r["esce"])
            usc[d1] = "apertura" if d1.dayofweek == 0 else "chiusura"
        pi = E.Piano("eventi", {d0: 1 if r["verso"] == "long" else -1}, usc)
        res = m.simula(pi, days, start=str(d0.date()))
        t = res["trades"][0]
        rows.append({"n": r["n"], "verso": r["verso"], "entra": r["entra"], "esce": r["esce"], "esito_csv": r["esito"],
                     "esito_motore": t["motivo"], "mult_csv": round(r["mult"], 4), "mult_motore": round(t["mult"], 4),
                     "scarto": round(t["mult"] - r["mult"], 4),
                     "scarto_rel": round(t["mult"] / r["mult"] - 1, 4) if r["mult"] > 0 else (0.0 if t["mult"] == 0 else np.nan)})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "cache" / "op_test_23.csv", index=False)
    return out


class T23(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = riproduci_23()

    def test_scadenza(self):
        s = self.t[self.t["esito_csv"] == "scadenza"]
        self.assertEqual(len(s), 14)
        self.assertTrue((s["esito_motore"] == "scadenza").all())
        self.assertLessEqual(s["scarto"].abs().max(), 0.05, s.to_string())

    def test_mediana(self):
        self.assertLessEqual(abs(self.t["scarto_rel"].median()), 0.15)


# ------------------------------------------------------------------ prezzatore sintetico per i test
class Finto:
    """Spot inventato, scadenze ogni venerdì, vol costante, griglia 1000."""

    def __init__(self, spot: pd.Series, vol: float = 0.6):
        self.s, self.vol = spot, vol

    def scadenze(self, d):
        d = pd.Timestamp(d)
        return [d + pd.Timedelta(days=(4 - d.dayofweek) % 7 + 7 * k) for k in range(1, 12)]

    def strikes(self, d, e):
        S = self.spot(d)
        return [1000 * k for k in range(int(S / 1000) - 20, int(S / 1000) + 21)]

    def spot(self, d):
        return float(self.s[pd.Timestamp(d)])

    def iv(self, d, e, K, t):
        return self.vol, "finta"

    def prezzo(self, d, e, K, t):
        return E.black76(self.spot(d), K, E.anni(d, e), self.vol, t), "finta"


def finto(path: list[float], start="2020-01-06") -> tuple[Finto, pd.DatetimeIndex, pd.Series]:
    days = pd.date_range(start, periods=len(path))
    s = pd.Series(path, days, dtype=float)
    ext = pd.concat([s, pd.Series([path[-1]] * 60, pd.date_range(days[-1] + E.DAY, periods=60))])
    return Finto(ext), days, ext


class TSint(unittest.TestCase):
    def test_scadenza_e_costi(self):
        path = [50_000.0] * 10 + [60_000.0] * 50
        pz, days, st = finto(path)
        m = E.Motore(pz, E.Conf(giorni=30), st)
        r = m.simula(E.Piano("eventi", {days[0]: 1}, {}), days, str(days[0].date()))
        t = r["trades"][0]
        self.assertEqual(t["motivo"], "scadenza")
        g = t["legs"][0]
        self.assertEqual(g["K"], 50_000)
        self.assertEqual(g["exp"].dayofweek, 4)
        self.assertTrue(25 <= (g["exp"] - days[0]).days <= 35)
        unit = g["mid0"] * 1.03 + min(0.0003 * 50_000, 0.125 * g["mid0"])
        self.assertAlmostEqual(g["qty"] * unit, 500.0, places=6)
        val = g["qty"] * 10_000 - min(0.0002 * 60_000 * g["qty"], 0.125 * 10_000 * g["qty"])
        self.assertAlmostEqual(t["proceeds"], val, places=6)
        self.assertAlmostEqual(r["equity"].iloc[-1], 9_500 + val, places=4)

    def test_dd_giornaliero_e_spread(self):
        pz, days, st = finto([50_000.0] * 40)
        r = E.Motore(pz, E.Conf(), st).simula(E.Piano("eventi", {days[0]: 1}, {}), days, str(days[0].date()))
        e = r["equity"]
        self.assertLess(e.iloc[0], 10_000)            # spread e commissione già nel valore di liquidazione
        self.assertAlmostEqual(e.iloc[-1], 9_500, places=6)   # alla pari a scadenza: premio perso
        self.assertLessEqual(E.metriche(r)["dd"], -0.05 + 1e-9)

    def test_U1_U2_U3_U4(self):
        path = list(np.linspace(50_000, 75_000, 15)) + [75_000.0] * 45
        pz, days, st = finto(path)
        for u, mot in (("U1", "U1"), ("U2", "U2")):
            t = E.Motore(pz, E.Conf(uscita=u), st).simula(E.Piano("eventi", {days[0]: 1}, {}), days, str(days[0].date()))["trades"][0]
            self.assertEqual(t["motivo"], mot)
            self.assertGreaterEqual(t["mult"], {"U1": 2.0, "U2": 3.0}[u])
        t = E.Motore(pz, E.Conf(uscita="U3"), st).simula(E.Piano("eventi", {days[0]: 1}, {}), days, str(days[0].date()))["trades"][0]
        self.assertTrue(t["half_done"])
        self.assertEqual(t["motivo"], "scadenza")
        t = E.Motore(pz, E.Conf(uscita="U4"), st).simula(E.Piano("eventi", {days[0]: 1}, {}), days, str(days[0].date()))["trades"][0]
        self.assertEqual(t["motivo"], "U4")
        self.assertEqual((t["legs"][0]["exp"] - t["exit"]).days, 7)

    def test_U5_un_solo_rinnovo(self):
        path = list(np.linspace(50_000, 90_000, 120))
        pz, days, st = finto(path)
        ip = pd.Series(1, index=days)
        pi = E.Piano("eventi", {days[0]: 1}, {}, in_pos=ip)
        r = E.Motore(pz, E.Conf(uscita="U5"), st).simula(pi, days, str(days[0].date()))
        self.assertEqual(len(r["trades"]), 2)
        self.assertTrue(r["trades"][1].get("rinnovo"))
        self.assertEqual(r["trades"][1]["entry"], r["trades"][0]["exit"] + E.DAY)
        r0 = E.Motore(pz, E.Conf(uscita="U0"), st).simula(pi, days, str(days[0].date()))
        self.assertEqual(len(r0["trades"]), 1)

    def test_straddle_e_una_posizione(self):
        pz, days, st = finto([50_000.0] * 30 + [40_000.0] * 40)
        pi = E.Piano("settimanale", segnali={d: 2 for d in days if d.dayofweek == 0})
        r = E.Motore(pz, E.Conf(), st).simula(pi, days, str(days[0].date()))
        t = r["trades"][0]
        self.assertEqual(sorted(g["tipo"] for g in t["legs"]), ["C", "P"])
        self.assertEqual(t["legs"][0]["K"], t["legs"][1]["K"])
        self.assertAlmostEqual(t["legs"][0]["qty"], t["legs"][1]["qty"])
        for a, b in zip(r["trades"], r["trades"][1:]):   # nessuna sovrapposizione
            self.assertGreaterEqual(b["entry"], a["exit"])

    def test_contrario(self):
        pz, days, st = finto([50_000.0] * 60)
        mon = [d for d in days if d.dayofweek == 0]
        pi = E.Piano("settimanale", segnali={mon[0]: 1, mon[2]: -1})
        r = E.Motore(pz, E.Conf(), st).simula(pi, days, str(days[0].date()))
        self.assertEqual([t["lato"] for t in r["trades"]], [1, -1])
        self.assertEqual(r["trades"][0]["motivo"], "contrario")
        self.assertEqual(r["trades"][0]["exit"], mon[2])

    def test_placebo(self):
        rng = np.random.default_rng(1)
        path = list(50_000 * np.exp(np.cumsum(rng.normal(0, 0.03, 400))))
        pz, days, st = finto(path)
        mon = [d for d in days if d.dayofweek == 0]
        pi = E.Piano("eventi", {mon[0]: 1, mon[10]: -1, mon[25]: 1}, {mon[4]: "apertura", mon[14]: "apertura", mon[30]: "apertura"})
        m = E.Motore(pz, E.Conf(), st)
        r = m.simula(pi, days, str(days[0].date()))
        p = E.placebo(m, r, days, n=20, da=str(days[0].date()))
        self.assertEqual(len(p["finali"]), 20)
        self.assertTrue(0 <= p["p"] <= 1)


if __name__ == "__main__":
    t = riproduci_23()
    print(t.to_string(index=False))
    print(f"scarto mediano relativo: {t['scarto_rel'].median():+.2%} · casi scadenza: max |scarto| "
          f"{t[t['esito_csv'] == 'scadenza']['scarto'].abs().max():.4f}")
    unittest.main(argv=[sys.argv[0]] + sys.argv[1:], verbosity=2)
