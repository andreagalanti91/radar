"""Dati provvisori di W3.2 (A1, research/dati_provvisori): funding dal premio Binance e volume OKX riscalato. Senza rete."""
import unittest
from datetime import date
from unittest import mock

import numpy as np
import pandas as pd

from radar import data


def _prem(start: str, minutes: int, value) -> pd.Series:
    idx = pd.date_range(start, periods=minutes, freq="1min")
    v = value(np.arange(minutes)) if callable(value) else np.full(minutes, value)
    return pd.Series(v, index=idx, dtype=float)


class TestFormulaPremio(unittest.TestCase):
    def test_premio_nella_fascia_da_lo_0_01(self):
        r = data.premium_funding_8h(_prem("2026-11-16 00:00", 480, -0.0002))
        self.assertAlmostEqual(r[pd.Timestamp("2026-11-16 08:00")], 0.0001, places=12)

    def test_premio_fuori_fascia(self):
        alto = data.premium_funding_8h(_prem("2026-11-16 00:00", 480, 0.002))
        basso = data.premium_funding_8h(_prem("2026-11-16 00:00", 480, -0.00045))   # come BTC a novembre 2026
        self.assertAlmostEqual(alto.iloc[0], 0.0015, places=12)                     # P − 0,05%
        self.assertAlmostEqual(basso.iloc[0], 0.00005, places=12)                   # P + 0,05%

    def test_pesi_crescenti(self):
        # metà periodo a 0,001, metà a 0,003: la media pesata 1..n pende verso la seconda metà
        r = data.premium_funding_8h(_prem("2026-11-16 00:00", 480, lambda i: np.where(i < 240, 0.001, 0.003)))
        k = np.arange(1, 481)
        p = (k * np.where(k <= 240, 0.001, 0.003)).sum() / k.sum()
        self.assertAlmostEqual(r.iloc[0], p - 0.0005, places=12)
        self.assertGreater(p, 0.002)

    def test_minuto_23_59_va_al_pagamento_delle_00(self):
        r = data.premium_funding_8h(_prem("2026-11-21 16:00", 480, 0.0))
        self.assertEqual(list(r.index), [pd.Timestamp("2026-11-22 00:00")])

    def test_periodo_incompleto_escluso(self):
        self.assertEqual(len(data.premium_funding_8h(_prem("2026-11-16 00:00", 300, 0.0))), 0)


class TestFundingProvvisorio(unittest.TestCase):
    def setUp(self):
        self.days = pd.date_range("2026-11-21", "2026-11-22")
        pays = pd.date_range("2026-11-21 00:00", "2026-11-22 16:00", freq="8h")
        self.okx = pd.Series(0.00002, index=pays)

    def test_domenica_al_lunedi_mattina(self):
        """Problema riprodotto: al giro del lunedì 00:07 il file di premio della domenica non c'è. Sabato tutto dal premio
        Binance; domenica il pagamento delle 00:00 dal premio (usa i premi del sabato), 08:00 e 16:00 da OKX."""
        prem = data.premium_funding_8h(_prem("2026-11-20 16:00", 480 * 4, -0.0002))   # fino a sab 24:00
        out = data.provisional_funding(prem, self.okx, self.days)
        self.assertEqual(out.at[pd.Timestamp("2026-11-21"), "source"], "premio")
        self.assertAlmostEqual(out.at[pd.Timestamp("2026-11-21"), "funding"], 0.0003, places=12)
        self.assertEqual(out.at[pd.Timestamp("2026-11-22"), "source"], "okx")
        self.assertAlmostEqual(out.at[pd.Timestamp("2026-11-22"), "funding"], 0.0001 + 2 * 0.00002, places=12)

    def test_pagamento_assente_ovunque_niente_riga(self):
        out = data.provisional_funding(pd.Series(dtype=float), self.okx.drop(pd.Timestamp("2026-11-22 16:00")), self.days)
        self.assertEqual(list(out.index), [pd.Timestamp("2026-11-21")])
        self.assertEqual(out["source"].iloc[0], "okx")

    def test_fetch_funding_senza_okx_ne_premio_resta_la_cache(self):
        cache = pd.DataFrame({"funding": [0.0003, 0.0001], "source": ["binance", "okx"]},
                             index=pd.DatetimeIndex(["2026-10-31", "2026-11-01"], name="date"))
        with mock.patch.object(data, "_today", return_value=date(2026, 11, 3)), \
                mock.patch.object(data, "_cache_last", return_value=date(2026, 11, 1)), \
                mock.patch.object(data, "_zip_csv", return_value=None), \
                mock.patch.object(data, "_get", side_effect=data.requests.ConnectionError("rete")), \
                mock.patch.object(data.pd, "read_csv", return_value=cache), \
                mock.patch.object(data, "_merge_cache") as merge, mock.patch("builtins.print"):
            out = data.fetch_funding()
        merge.assert_not_called()
        self.assertEqual(len(out), 2)


class TestVolumeOkx(unittest.TestCase):
    def test_rapporto_mediano(self):
        idx = pd.date_range("2026-10-01", periods=40)
        b = pd.DataFrame({"volume": np.full(40, 200.0), "source": ["binance"] * 38 + ["okx"] * 2}, index=idx)
        o = pd.DataFrame({"volume": np.full(40, 110.0)}, index=idx)
        o.iloc[-5, 0] = 1.0                                 # un giorno anomalo non sposta la mediana
        self.assertAlmostEqual(data.okx_volume_ratio(b, o), 200 / 110, places=9)

    def test_pochi_giorni_niente_correzione(self):
        idx = pd.date_range("2026-10-01", periods=5)
        self.assertIsNone(data.okx_volume_ratio(pd.DataFrame({"volume": [1.0] * 5}, index=idx),
                                                pd.DataFrame({"volume": [2.0] * 5}, index=idx)))


if __name__ == "__main__":
    unittest.main()
