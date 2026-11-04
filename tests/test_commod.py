"""Monitor materie prime (radar/commod.py) su una serie sintetica: niente rete, risultato serializzabile, alert con dedupe."""
import json
import unittest

import numpy as np
import pandas as pd


class TestCommod(unittest.TestCase):
    def test_sintetico(self):
        from radar import commod
        rng = np.random.default_rng(1)
        idx = pd.bdate_range("2020-01-01", "2026-10-30")
        c = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, len(idx))))
        d = pd.DataFrame({"open": c * (1 + rng.normal(0, .003, len(c))), "high": c * 1.01, "low": c * 0.99, "close": c}, idx)
        r = commod.evaluate("XAG", d)
        json.dumps({k: v for k, v in r.items()})
        self.assertTrue(r["supports"] or r["resistances"])
        m1, st = commod.diff_events(r, {})
        m2, st = commod.diff_events(r, st)
        self.assertEqual(m2, [])   # nessun doppione
