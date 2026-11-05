"""Intraday · Ichimoku 4h (radar/intraday_ichi.py): indicatori, nessun lookahead, backtest coerente, eventi senza doppioni.
Dati sintetici (sempre) + cache data/intra/ (se presente) per i numeri della ricerca."""
import unittest

import numpy as np
import pandas as pd

from radar import intraday_ichi as I


def synth(n=1500, seed=1):
    rng = np.random.default_rng(seed)
    t = pd.date_range("2021-01-01", periods=n, freq="4h")
    # random walk con tendenze alterne: produce incroci Tenkan/Kijun in entrambi i versi
    drift = np.sin(np.arange(n) / 120) * 0.004
    c = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.012, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.001, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.006, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.006, n)))
    return pd.DataFrame(dict(open=o, high=h, low=l, close=c), index=pd.Index(t, name="t"))


class TestIntradayIchi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = synth()
        cls.tr = I.backtest(cls.d)
        for t in cls.tr:
            t["asset"] = "SYN"

    def test_indicatori(self):
        d, ind = self.d, I.indicators(self.d)
        k = 400
        self.assertAlmostEqual(ind.ten.iloc[k], (d.high.iloc[k - 8:k + 1].max() + d.low.iloc[k - 8:k + 1].min()) / 2)
        self.assertAlmostEqual(ind.kij.iloc[k], (d.high.iloc[k - 25:k + 1].max() + d.low.iloc[k - 25:k + 1].min()) / 2)
        j = k - 26   # la nube sotto la barra k è calcolata alla barra k-26
        self.assertAlmostEqual(ind.sa.iloc[k], (ind.ten.iloc[j] + ind.kij.iloc[j]) / 2)
        self.assertAlmostEqual(ind.sb.iloc[k], (d.high.iloc[j - 51:j + 1].max() + d.low.iloc[j - 51:j + 1].min()) / 2)
        self.assertTrue(np.isnan(ind.atr.iloc[12]) and not np.isnan(ind.atr.iloc[13]))

    def test_regola_e_nessun_lookahead(self):
        d, ind, s = self.d, I.indicators(self.d), I.signals(self.d)
        self.assertTrue((s == 1).sum() > 5 and (s == -1).sum() > 5)
        for k in np.flatnonzero(s)[:20]:
            up = s[k] > 0
            x, xp = ind.ten.iloc[k] - ind.kij.iloc[k], ind.ten.iloc[k - 1] - ind.kij.iloc[k - 1]
            self.assertTrue(x > 0 >= xp if up else x < 0 <= xp)
            cl = d.close.iloc[k]
            self.assertTrue(cl > max(ind.sa.iloc[k], ind.sb.iloc[k]) if up else cl < min(ind.sa.iloc[k], ind.sb.iloc[k]))
        # il segnale alla barra k non cambia se le barre successive vengono stravolte
        k = int(np.flatnonzero(s)[10])
        d2 = d.copy()
        d2.iloc[k + 1:, :] = d2.iloc[k + 1:, :].values * 3.0
        self.assertTrue((I.signals(d2)[:k + 1] == s[:k + 1]).all())
        self.assertTrue((I.signals(d.iloc[:k + 1]) == s[:k + 1]).all())

    def test_backtest_coerente(self):
        T = I.closed(self.tr)
        self.assertGreater(len(T), 10)
        idx = self.d.index
        for a, b in zip(T, T[1:]):
            self.assertGreaterEqual(b["entry_t"], a["exit_t"])            # una posizione alla volta
        for t in T:
            e = idx.get_loc(t["entry_t"])
            self.assertEqual(idx.get_loc(t["sig_t"]), e - 1)              # ingresso all'apertura dopo il segnale
            self.assertAlmostEqual(t["entry"], self.d.open.iloc[e])
            self.assertAlmostEqual(abs(t["target"] - t["entry"]), 3 * abs(t["entry"] - t["stop"]))
            self.assertAlmostEqual(abs(t["entry"] - t["stop"]), 2 * I.indicators(self.d).atr.iloc[e - 1])
            self.assertLessEqual(t["bars"], I.HOLD)
            if t["exit"] == "time":
                self.assertEqual(t["bars"], I.HOLD)
            if t["exit"] == "tgt":
                self.assertAlmostEqual(t["R"], (3 * t["d"] - 0.0016) / t["d"])
            if t["exit"] == "stop":
                self.assertLessEqual(t["R"], -1.0)
            self.assertAlmostEqual(t["R"], t["net"] / t["d"])
            self.assertEqual(t["a10"], -1.0 if t["liq"] else max(10 * t["net"], -1.0))
        # rischio fisso: con rischio 1% e leva mai limitata il conto composto è il prodotto di (1 + 1% x R)
        sm = I.simulate(self.tr, 200, 0.01)
        exp = 200 * np.prod([1 + 0.01 * t["R"] for t in T if 0.01 / t["d"] <= 10])
        if all(0.01 / t["d"] <= 10 for t in T):
            self.assertAlmostEqual(sm["final"], round(exp, 2), places=1)
        self.assertEqual(sm["n"], len(T))

    def test_barra_in_corso(self):
        d = self.d
        s = I.signals(d)
        k = int(np.flatnonzero(s)[-1])
        cut = d.iloc[:k + 1]
        tr = I.backtest(cut)                       # segnale sull'ultima barra chiusa: in attesa d'ingresso
        self.assertEqual(tr[-1]["exit"], "pending")
        tr2 = I.backtest(cut, d.iloc[k + 1:k + 2])  # barra in corso: ingresso alla sua apertura, mai uscita a tempo
        self.assertIn(tr2[-1]["exit"], ("open", "stop", "tgt"))
        self.assertAlmostEqual(tr2[-1]["entry"], d.open.iloc[k + 1])

    def test_eventi_senza_doppioni(self):
        d = self.d
        k = int(np.flatnonzero(I.signals(d))[-3])
        past = I.backtest(d.iloc[:k])
        msgs, st = I.diff_events({"SYN": past}, None, now=d.index[k - 1])
        self.assertEqual(msgs, [])                 # primo giro: si registra lo storico in silenzio
        cut = d.iloc[:k + 1]
        tr = I.backtest(cut, d.iloc[k + 1:k + 2])
        now = d.index[k] + I.BAR + pd.Timedelta(minutes=7)
        msgs, st = I.diff_events({"SYN": tr}, st, now=now, capital=200)
        self.assertEqual(len(msgs), 1)
        self.assertIn("NUOVO SEGNALE", msgs[0])
        self.assertIn("leva", msgs[0])
        msgs2, st = I.diff_events({"SYN": tr}, st, now=now)
        self.assertEqual(msgs2, [])                # stesso giro ripetuto: niente doppioni
        # uscita del trade: un solo messaggio
        full = I.backtest(d)
        t = next(x for x in full if x["sig_t"] == d.index[k])
        if t["exit"] in ("tgt", "stop", "time"):
            m3, st = I.diff_events({"SYN": full}, st, now=t["exit_t"] + pd.Timedelta(hours=1))
            self.assertTrue(any(("TARGET" in m or "STOP" in m or "TEMPO" in m) for m in m3))
            m4, st = I.diff_events({"SYN": full}, st, now=t["exit_t"] + pd.Timedelta(hours=2))
            self.assertEqual(m4, [])

    def test_sizing(self):
        s = I.sizing(0.05, 200, 0.01)
        self.assertAlmostEqual(s["notional"], 40)
        self.assertAlmostEqual(s["lev"], 0.2)
        self.assertTrue(I.sizing(0.001, 200, 0.02)["capped"])

    def test_vista_dashboard(self):
        v = I.asset_view("SYN", self.d, pd.DataFrame(), self.tr)
        s = v["series"]
        self.assertEqual(len(s["t"]), I.CHART_BARS)
        self.assertEqual(len(s["sa"]), I.CHART_BARS + 26)
        self.assertEqual(len(v["trades"]), len(self.tr))


@unittest.skipUnless(all((I.DIR / f"{a}_4h.csv").exists() for a in ("BTC", "SOL")), "cache data/intra assente")
class TestIntradayCache(unittest.TestCase):
    def test_numeri_ricerca(self):
        # fuori campione 2024+ come la ricerca (perp+funding): BTC 93 trade +0,13R, SOL 101 trade +0,32R. Spot senza funding: vicino.
        for a, n, r in (("BTC", 93, 0.13), ("SOL", 101, 0.32)):
            d = I.load(a)
            d = d[d.index < "2026-11-03"]
            T = [t for t in I.closed(I.backtest(d)) if t["entry_t"] >= pd.Timestamp("2024-01-01")]
            self.assertLess(abs(len(T) - n), 8, a)
            self.assertLess(abs(np.mean([t["R"] for t in T]) - r), 0.08, a)


if __name__ == "__main__":
    unittest.main()
