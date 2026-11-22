"""Soglie d'allarme W3.1 dal vivo (radar/guard.py). Niente rete."""
import unittest

from radar import guard


def wcur(eq, trades=()):
    dates = [f"2026-11-{d:02d}" for d in range(1, len(eq) + 1)]
    return {"history": {"eq_dates": dates, "eq1": eq, "trades": list(trades)}}


def tr(sig, exit_, reason, pnl):
    return {"signal": sig, "entry": sig, "exit": exit_, "reason": reason, "pnl_pct": pnl, "side": "short"}


class TestGuard(unittest.TestCase):
    def test_drawdown(self):
        g = guard.compute(wcur([1.0, 1.2, 1.1, 1.0]), "2026-11-01")
        self.assertAlmostEqual(g["dd_pct"], -16.67, places=2)
        self.assertEqual(g["peak_date"], "2026-11-02")
        self.assertTrue(g["alarm"])
        g = guard.compute(wcur([1.0, 1.2, 1.1, 1.0]), "2026-11-03")   # dal vivo solo dal 03/11: −9%
        self.assertFalse(g["alarm"])
        self.assertEqual(g["thresholds"], {"dd_pct": -15.0, "stops_in_a_row": 2})

    def test_stop_consecutivi(self):
        t = [tr("2026-11-01", "2026-11-03", "stop", -9.0), tr("2026-11-04", "2026-11-06", "trail", -2.0)]
        g = guard.compute(wcur([1.0] * 10, t), "2026-11-01")
        self.assertEqual(g["stops_in_a_row"], 2)
        self.assertTrue(g["alarm"])
        t2 = t + [tr("2026-11-07", "2026-11-08", "trail", 5.0)]          # trailing in guadagno: la serie si interrompe
        self.assertEqual(guard.compute(wcur([1.0] * 10, t2), "2026-11-01")["stops_in_a_row"], 0)
        t3 = [tr("2026-11-01", "2026-11-03", "ema", -1.0), t[1]]
        self.assertEqual(guard.compute(wcur([1.0] * 10, t3), "2026-11-01")["stops_in_a_row"], 1)
        self.assertEqual(guard.compute(wcur([1.0] * 10, t), "2026-11-05")["stops_in_a_row"], 1)   # prima del vivo non conta

    def test_avviso_una_volta(self):
        w, st, msgs = wcur([1.0, 1.2, 1.0]), {}, []
        guard.update(w, st, send=lambda m: False)
        self.assertNotIn("sent", st["guard"])                             # non confermato: si riprova
        guard.update(w, st, send=lambda m: msgs.append(m) or True)
        guard.update(w, st, send=lambda m: msgs.append(m) or True)
        self.assertEqual(len(msgs), 1)
        self.assertIn("revisione consigliata e rischio dimezzato (decisione dell'utente)", msgs[0])
        self.assertTrue(st["guard"]["last"]["alarm"])
        self.assertIsNone(guard.update(None, st, send=lambda m: True))

    def test_inizio_dal_registro(self):
        j = {"trades": [{"strategy": "w2", "entries": [{"time": "2026-11-16 09:00"}]},
                        {"strategy": "v2", "entries": [{"time": "2026-11-01 09:00"}]}]}
        self.assertEqual(guard.live_start(j), "2026-11-16")
        self.assertEqual(guard.live_start({"trades": []}), guard.weekly.LIVE_START)


if __name__ == "__main__":
    unittest.main()
