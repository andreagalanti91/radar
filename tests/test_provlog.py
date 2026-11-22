"""Registro domenicale provvisori vs definitivi (radar/provlog.py). Niente rete."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar import provlog as pl

D = pd.Timestamp("2026-11-15")   # domenica


def frame(last=D, n=400, pf_last=-0.5, fund=-0.0005):
    idx = pd.date_range(end=last, periods=n, freq="D")
    c = np.linspace(90000, 60000, n)                  # discesa regolare: chiusura sotto la EMA 21
    f = pd.DataFrame({"open": c * 1.001, "high": c * 1.01, "low": c * 0.99, "close": c}, index=idx)
    f["pf14z"] = 0.3
    f.loc[f.index[-4:], "pf14z"] = pf_last           # gli ultimi giorni decidono il flusso
    f["funding"] = 0.0001
    f.loc[f.index[-7:], "funding"] = fund
    return f


def sources(f, perp_okx=0, fund_okx=0):
    p = pd.Series("binance", index=f.index)
    if perp_okx:
        p.iloc[-perp_okx:] = "okx"
    u = pd.Series("binance", index=f.index)
    if fund_okx:
        u.iloc[-fund_okx:] = "okx"
    return {"perp": pd.DataFrame({"source": p}), "funding": pd.DataFrame({"source": u})}


WCUR = {"history": {"trades": [{"signal": "2026-11-01", "entry": "2026-11-02", "exit": None, "side": "short",
                                "reason": "open"}]}}


class TestProvlog(unittest.TestCase):
    def test_funzioni(self):
        s = pd.Series("binance", index=pd.date_range("2026-11-01", "2026-11-14"))
        self.assertEqual(pl.window_src(s, pd.Timestamp("2026-11-14"), 14), "binance")
        self.assertEqual(pl.window_src(s, pd.Timestamp("2026-11-15"), 14), "okx")   # giorno mancante = provvisorio
        self.assertEqual(pl.decision_sunday(pd.Timestamp("2026-11-16")), D)
        self.assertEqual(pl.decision_sunday(D), D)
        self.assertEqual(pl.side_at(WCUR["history"]["trades"], "2026-11-15"), -1)
        self.assertEqual(pl.side_at(WCUR["history"]["trades"], "2026-11-01"), 0)

    def test_provvisorio_poi_definitivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            f = frame()
            out = pl.update(f, sources(f, perp_okx=2, fund_okx=7), WCUR, tmp, now=pd.Timestamp("2026-11-16 00:10"))
            self.assertEqual(out["rows"], 1)
            r = pd.read_csv(tmp / "provlog.csv").iloc[0]
            self.assertEqual(r["date"], "2026-11-15")
            self.assertEqual(r["decision_p"], "nessuna")       # short aperto, flusso < 0: nessuna uscita
            self.assertEqual(r["pf3_src"], "okx")
            self.assertEqual(r["fund7_src"], "okx")
            self.assertAlmostEqual(r["flow_p"], -0.5)
            self.assertAlmostEqual(r["m_fcold_p"], -0.0005 + 0.0003)
            self.assertTrue(pd.isna(r["flow_d"]))
            # secondo giro dello stesso giorno: nessun doppione
            self.assertEqual(pl.update(f, sources(f, 2, 7), WCUR, tmp, now=pd.Timestamp("2026-11-16 01:10"))["rows"], 1)
            # perp definitivo (archivio Binance) con flusso rivisto, funding ancora OKX: decisione non ancora ricalcolata
            g = frame(pf_last=0.4)
            out = pl.update(g, sources(g, 0, 7), WCUR, tmp, now=pd.Timestamp("2026-11-17 00:10"))
            r = pd.read_csv(tmp / "provlog.csv").iloc[0]
            self.assertAlmostEqual(r["flow_d"], 0.4)
            self.assertAlmostEqual(r["d_flow"], 0.9)
            self.assertTrue(pd.isna(r["decision_d"]))
            self.assertEqual(out["pending"], 1)
            # funding definitivo: con flusso > 0 e funding < −0,0003 lo short sarebbe uscito per distribuzione
            out = pl.update(g, sources(g, 0, 0), WCUR, tmp, now=pd.Timestamp("2026-12-02 00:10"))
            r = pd.read_csv(tmp / "provlog.csv").iloc[0]
            self.assertEqual(r["decision_d"], "uscita dist")
            self.assertTrue(bool(r["changed"]))
            self.assertEqual((out["complete"], out["changed"]), (1, 1))

    def test_non_registra_in_ritardo(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = frame(last=D + pd.Timedelta(days=3))
            out = pl.update(f, sources(f, 2, 7), WCUR, Path(tmp), now=pd.Timestamp("2026-11-19 00:10"))
            self.assertEqual(out["rows"], 0)
            self.assertFalse((Path(tmp) / "provlog.csv").exists())
            f = frame(last=D + pd.Timedelta(days=1))               # lunedì: registrata, segnata in ritardo
            pl.update(f, sources(f, 2, 7), WCUR, Path(tmp), now=pd.Timestamp("2026-11-17 00:10"))
            self.assertTrue(bool(pd.read_csv(Path(tmp) / "provlog.csv").iloc[0]["late"]))


if __name__ == "__main__":
    unittest.main()
