"""Riepilogo giornaliero guidato dallo stato (radar.cli.brief_due, M4) e ripartenza del perp orario (radar.data.perp_restart, M7).
Funzioni pure, niente rete."""
import os
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from radar import cli
from radar.data import perp_restart

T = pd.Timestamp


class TestBrief(unittest.TestCase):
    def setUp(self):
        p = mock.patch.dict(os.environ, {"RADAR_DAILY_BRIEF": "1"})
        p.start()
        self.addCleanup(p.stop)

    def test_primo_giro_dopo_mezzanotte_una_volta(self):
        st = {}
        now = T("2026-11-13 00:05")
        self.assertTrue(cli.brief_due(st, now, "2026-11-12"))          # primo giro dopo le 00:00, dati fino a ieri
        self.assertFalse(cli.brief_due(st, now, "2026-11-11"))         # candela di ieri non ancora arrivata: si aspetta
        self.assertTrue(cli.brief_due(st, T("2026-11-13 06:10"), "2026-11-11"))   # dalle 06:00 parte comunque
        self.assertTrue(cli.brief_due(st, T("2026-11-13 14:00"), "2026-11-12"))   # nessun giro fino alle 14: parte alle 14

    def test_marker_e_interruttore(self):
        st, sent = {}, []
        now = T("2026-11-13 00:05")
        with mock.patch.object(cli.telegram, "daily_brief", lambda r: "testo"):
            self.assertFalse(cli.daily_brief({}, st, now, "2026-11-12", send=lambda m: False))   # Telegram non conferma
            self.assertNotIn("daily_brief", st)                                                # si riprova al giro dopo
            self.assertTrue(cli.daily_brief({}, st, now, "2026-11-12", send=lambda m: sent.append(m) or True))
            self.assertEqual(st["daily_brief"], "2026-11-13")
            self.assertFalse(cli.daily_brief({}, st, T("2026-11-13 01:05"), "2026-11-12", send=lambda m: sent.append(m) or True))
            self.assertEqual(sent, ["testo"])                                                  # una sola volta al giorno
            self.assertTrue(cli.brief_due(st, T("2026-11-14 00:03"), "2026-11-13"))           # il giorno dopo di nuovo
            with mock.patch.dict(os.environ, {"RADAR_DAILY_BRIEF": "0"}):
                self.assertFalse(cli.brief_due({}, now, "2026-11-12"))


class TestPerpRestart(unittest.TestCase):
    def frame(self, end="2026-11-13 17:00", hole=None, tail_nan_h=18):
        idx = pd.date_range("2026-09-01", end, freq="h")
        perp = np.ones(len(idx))
        perp[len(idx) - tail_nan_h:] = np.nan
        df = pd.DataFrame({"spot_vol": 1.0, "perp_vol": perp}, index=idx)
        if hole:
            df.loc[hole[0]:hole[1], "perp_vol"] = np.nan
        return df

    def test_buco_in_mezzo_si_recupera(self):
        now, t0 = T("2026-11-13 18:00"), T("2022-01-01")
        df = self.frame(hole=("2026-10-28 00:00", "2026-10-28 23:00"))
        self.assertEqual(perp_restart(df, now, t0), T("2026-10-28"))   # prima: ultimo perp − 1 giorno = 11/11, buco perso

    def test_senza_buchi_come_prima(self):
        now, t0 = T("2026-11-13 18:00"), T("2022-01-01")
        df = self.frame()
        self.assertEqual(perp_restart(df, now, t0), T("2026-11-11"))   # ultimo perp 12/11 23:00 − 1 giorno

    def test_buco_fuori_finestra_e_casi_limite(self):
        now, t0 = T("2026-11-13 18:00"), T("2022-01-01")
        df = self.frame(hole=("2026-09-10 00:00", "2026-09-10 23:00"))   # oltre 30 giorni: non si riscarica
        self.assertEqual(perp_restart(df, now, t0), T("2026-11-11"))   # ultimo perp 12/11 23:00 − 1 giorno
        self.assertEqual(perp_restart(None, now, t0), t0)
        empty = df.assign(perp_vol=np.nan)
        self.assertEqual(perp_restart(empty, now, t0), t0)


if __name__ == "__main__":
    unittest.main()
