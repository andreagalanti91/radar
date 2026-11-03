"""Supporti e resistenze (radar/levels.py): zone ordinate, lati coerenti col prezzo, forza 1–5, zone strette."""
import unittest

from radar.data import DATA_DIR


@unittest.skipUnless((DATA_DIR / "spot.csv").exists(), "dati mancanti")
class TestLevels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import levels
        from radar.data import load_all
        from radar.features import build_features
        cls.L = levels.compute(build_features(load_all()))

    def test_lati_e_ordine(self):
        L, p = self.L, self.L["price"]
        self.assertTrue(L["supports"] and L["resistances"])
        self.assertTrue(all(o["price"] < p for o in L["supports"]))
        self.assertTrue(all(o["price"] > p for o in L["resistances"]))
        self.assertEqual([o["price"] for o in L["supports"]], sorted([o["price"] for o in L["supports"]], reverse=True))
        self.assertEqual([o["price"] for o in L["resistances"]], sorted(o["price"] for o in L["resistances"]))

    def test_forza_e_larghezza(self):
        for o in self.L["supports"] + self.L["resistances"]:
            self.assertIn(o["strength"], range(1, 6))
            self.assertLessEqual(o["hi"] - o["lo"], 2.0 * self.L["atr"] + 1)   # niente zone a catena
            self.assertTrue(o["lo"] <= o["price"] <= o["hi"] or o["touches"] == 0)
