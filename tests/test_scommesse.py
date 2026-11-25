"""Registro "scommesse" sulla carta (radar/scommesse.py, research/w32_asset2/REGISTRO-SCOMMESSE.md). Niente rete: righe dello
scanner costruite a mano e serie sintetiche. Coperti: ammissione (verso di BTC, esclusioni, operabilità, solo segnali dal
29/11/2026), importo fisso e costi, funding sugli short, uscita di W3.2, chiusura per dati fermi, registro vuoto, pagina."""
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from radar import scanner as SC
from radar import scommesse as SB
from radar import weekly as W
try:
    from test_scanner import serie          # python3 -m unittest discover -s tests
except ImportError:
    from tests.test_scanner import serie

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def riga(t="AAA", lato="long", sig="2026-11-29", g="long", bg=True, ok=False, evento="ingresso"):
    return {"t": t, "lato": lato, "sig": sig, "g": g, "bg": bg, "ok": ok, "evento": evento}


class TestAmmissione(unittest.TestCase):
    def test_regole(self):
        self.assertEqual(SB.ammissione(riga()), (True, True, ""))
        self.assertEqual(SB.ammissione(riga(lato="short", g="long"))[:2], (True, False))     # entra solo nel riferimento senza filtro
        self.assertEqual(SB.ammissione(riga(g="flat"))[:2], (True, False))
        self.assertFalse(SB.ammissione(riga(sig="2026-11-22"))[0])                           # prima del 29/11: non entra
        for t in ("BTC", "ETH", "TRX"):
            self.assertFalse(SB.ammissione(riga(t=t))[0])
        self.assertFalse(SB.ammissione(riga(bg=False, ok=False))[0])                         # non operabile
        self.assertTrue(SB.ammissione(riga(bg=False, ok=True))[0])
        self.assertFalse(SB.ammissione(riga(lato="flat"))[0])
        self.assertFalse(SB.ammissione({"t": "AAA", "lato": None})[0])                       # dati insufficienti

    def test_aggiungi_una_volta_e_solo_nuovi(self):
        reg = SB._vuoto()
        sc = {"righe": [riga(), riga(t="BBB", lato="short", g="long"), riga(t="OLD", sig="2026-11-15", evento=None), riga(t="ETH")]}
        u = {"AAA": {"ticker": "AAA", "perp": "AAAUSDT", "spot": "AAAUSDT", "div": 1, "fonte": "binance"}}
        self.assertEqual(SB.aggiungi(reg, sc, u), 2)
        self.assertEqual(SB.aggiungi(reg, sc, u), 0)                                          # chiave moneta|verso|segnale
        ops = {o["t"]: o for o in reg["operazioni"]}
        self.assertEqual(set(ops), {"AAA", "BBB"})
        self.assertEqual(ops["AAA"]["ing"], "2026-11-30")                                     # apertura del lunedì
        self.assertTrue(ops["AAA"]["filtro"])
        self.assertFalse(ops["BBB"]["filtro"])
        self.assertEqual(ops["AAA"]["c"]["perp"], "AAAUSDT")
        b = SB.build(reg, datetime(2026, 11, 30, tzinfo=UTC))
        self.assertEqual([o["t"] for o in b["operazioni"]], ["AAA"])                          # in pagina solo quelle nel verso di BTC
        self.assertEqual((b["filtro"]["n"], b["senza_filtro"]["n"]), (1, 2))


class TestRisultato(unittest.TestCase):
    def test_importo_fisso_e_costi(self):
        r = SB.risultato("long", 2.0, 2.2, None, "2026-11-30", "2026-12-14")
        self.assertAlmostEqual(r["pnl_usd"], round(100 * (0.10 - 0.001 * (1 + 1.1)), 2))     # +10% lordo, 0,10% per lato
        self.assertEqual(r["costi_usd"], 0.21)
        s = SB.risultato("short", 2.0, 1.8, None, "2026-11-30", "2026-12-14")
        self.assertAlmostEqual(s["pnl_usd"], round(100 * (0.10 - 0.001 * 1.9), 2))

    def test_funding_short(self):
        idx = pd.date_range("2026-11-28", "2026-12-10")
        f = pd.DataFrame({"open": 2.0, "close": 2.0, "funding": 0.0001}, index=idx)
        f.loc["2026-12-05", "funding"] = np.nan
        s = SB.risultato("short", 2.0, 2.0, f, "2026-11-30", "2026-12-07")                   # 7 giorni, uno senza funding
        self.assertAlmostEqual(s["funding_usd"], round(100 * 6 * 0.0001, 2))                  # short incassa il funding positivo
        self.assertEqual(s["funding_nd"], 1)
        self.assertEqual(SB.risultato("long", 2.0, 2.0, f, "2026-11-30", "2026-12-07")["funding_usd"], 0.0)   # long a pronti


def feats_trend_poi_crollo():
    """Trend al rialzo (ingresso long di W3.2) poi crollo: il trailing chiude l'operazione."""
    a = serie(n=1100, end="2026-11-01", drift=1.0, seed=2, p0=10.0)
    last = float(a["close"].iloc[-1])
    idx = pd.date_range("2026-11-02", periods=60, freq="D")
    c = last * np.exp(-np.linspace(0.01, 0.6, 60))
    o = np.r_[last, c[:-1]]
    b = pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.01, "low": np.minimum(o, c) * 0.99, "close": c, "volume": 1000.0, "tbv": 400.0}, index=idx)
    df = pd.concat([a, b])
    return SC.feats(df, df, pd.DataFrame({"funding": 0.0001}, index=df.index))


class TestValuta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = feats_trend_poi_crollo()
        w = W.weekly_bars(cls.f)
        okw = w[w["sma"].notna() & w["flow"].notna()]
        sim = W.simulate(cls.f, start=str((okw.index[0] + pd.Timedelta(days=1)).date()))
        cls.tr = next(t for t in sim["trades"][::-1] if t["side"] == "long" and t.get("exit"))

    def op(self):
        return {"k": "AAA|long|" + self.tr["signal"], "t": "AAA", "v": "long", "sig": self.tr["signal"], "ing": self.tr["entry"], "stato": "attesa", "filtro": True}

    def test_uscita_di_w32(self):
        o = SB.valuta(self.op(), self.f, date(2026, 12, 31))
        self.assertEqual(o["stato"], "chiusa")
        self.assertEqual(o["usc"], self.tr["exit"])
        self.assertAlmostEqual(o["px_in"], round(float(self.f.loc[self.tr["entry"], "open"]), 8))   # apertura del lunedì, senza slittamento
        self.assertAlmostEqual(o["px_out"], round(SB._px_uscita(self.f, self.tr), 8))
        self.assertEqual(o["pnl_usd"], SB.risultato("long", o["px_in"], o["px_out"], self.f, o["ing"], o["usc"])["pnl_usd"])
        self.assertEqual(o["motivo"], W.REASONS[self.tr["reason"]])

    def test_aperta_e_attesa(self):
        g = self.f[self.f.index < pd.Timestamp(self.tr["exit"])]
        o = SB.valuta(self.op(), g, g.index[-1].date() + pd.Timedelta(days=1).to_pytimedelta())
        self.assertEqual(o["stato"], "aperta")
        self.assertAlmostEqual(o["ult"], round(float(g["close"].iloc[-1]), 8))
        h = self.f[self.f.index < pd.Timestamp(self.tr["entry"])]
        self.assertEqual(SB.valuta(self.op(), h, date(2026, 1, 1))["stato"], "attesa")      # lunedì non ancora chiuso

    def test_dati_fermi(self):
        g = self.f[self.f.index < pd.Timestamp(self.tr["exit"])]
        o = SB.valuta(self.op(), g, g.index[-1].date() + pd.Timedelta(days=20).to_pytimedelta())
        self.assertEqual((o["stato"], o["motivo"]), ("chiusa", "dati fermi"))
        self.assertIn("ultimo prezzo disponibile", o["nota"])


class TestGiro(unittest.TestCase):
    def test_registro_vuoto(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            sc = {"settimana": "2026-11-22", "righe": [riga(sig="2026-11-15", evento=None), riga(t="BTC")]}
            b = SB.giro(sc, d, datetime(2026, 11, 25, 12, tzinfo=UTC), net=SC.Rete(lambda *a: (_ for _ in ()).throw(AssertionError("rete")), pausa=0),
                        universo={})
            self.assertEqual(b["operazioni"], [])
            self.assertEqual((b["filtro"]["n"], b["filtro"]["investito"], b["filtro"]["risultato_usd"]), (0, 0.0, 0))
            self.assertEqual(b["nota"], "sulla carta: nessun capitale, nessun ordine")
            self.assertEqual(b["inizio"], "2026-11-29")
            self.assertTrue((d / SB.FILE).exists())
            self.assertLess((d / SB.FILE).stat().st_size, 2000)
            # giro dopo: niente di nuovo, nessuna scrittura
            m = (d / SB.FILE).stat().st_mtime_ns
            SB.giro(sc, d, datetime(2026, 11, 25, 13, tzinfo=UTC), universo={})
            self.assertEqual((d / SB.FILE).stat().st_mtime_ns, m)

    def test_cli_e_pagina(self):
        src = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('report["scommesse"] = _soft("scommesse sulla carta", lambda: mod("scommesse").giro(report.get("scanner"), DATA_DIR))', src)
        self.assertLess(src.index('report["scanner"] = '), src.index('report["scommesse"] = '))
        T = (ROOT / "radar" / "dashboard_template.html").read_text()
        self.assertIn("B = R.scommesse", T)
        self.assertIn("Riferimento senza filtro di BTC", T)
        s = (ROOT / "radar" / "scommesse.py").read_text()
        for w in ("telegram", "send(", "place_order", "api_key"):
            self.assertNotIn(w, s)
        self.assertEqual((SB.IMPORTO, SB.COSTO, SB.INIZIO, SB.ESCLUSE), (100.0, 0.001, "2026-11-29", {"BTC", "ETH", "TRX"}))


if __name__ == "__main__":
    unittest.main()
