"""Scout balene (radar/scout.py): solo funzioni pure, niente rete."""
import math
import unittest

from radar import scout as S

D = S.DAY


def port(pts, perp=None, month=None):
    """Risposta `portfolio` finta: pts = [(giorno, valore, pnl)]."""
    def win(p):
        return {"accountValueHistory": [[int(d * D), str(a)] for d, a, _ in p], "pnlHistory": [[int(d * D), str(x)] for d, _, x in p]}
    out = [["allTime", win(pts)], ["perpAllTime", win(perp or pts)]]
    if month:
        out.append(["month", win(month)])
    return out


def steady(days=400, step=14, growth=0.05, base=1e6, deposit_at=None, deposit=0.0):
    """Conto che cresce del 5% ogni 2 settimane, con un eventuale deposito (che non è rendimento)."""
    pts, av, pnl = [], base, 0.0
    for d in range(0, days + 1, step):
        if d:
            g = av * growth
            av += g
            pnl += g
            if deposit_at is not None and d == deposit_at:
                av += deposit
        pts.append((d, av, pnl))
    return pts


class MetricsTest(unittest.TestCase):
    def test_md_return_neutralizes_deposits(self):
        self.assertAlmostEqual(S.md_return(1e6, 0, 1.1e6, 1e5), 0.10)
        # deposito di 1M e guadagno di 100k: il rendimento è 100k su ~1,5M di capitale medio, non +110%
        r = S.md_return(1e6, 0, 2.1e6, 1e5)
        self.assertAlmostEqual(r, 1e5 / 1.5e6)
        self.assertEqual(S.md_return(10, 0, 20, 5), 0.0)   # conto quasi vuoto: nessun rendimento

    def test_steady_growth(self):
        now = 400 * D
        m = S.metrics(port(steady()), now)
        self.assertTrue(m["ok"])
        self.assertGreater(m["ret_1y"], 2.0)          # 1,05^26 ≈ 3,6x
        self.assertAlmostEqual(m["dd"], 0.0)
        self.assertGreater(m["r2"], 0.99)
        self.assertEqual(m["pos"], 1.0)
        self.assertAlmostEqual(m["perp_share"], 1.0)
        self.assertEqual(S.fails(dict(m, fund_pnl=0.0), S.TH0), [])

    def test_deposit_does_not_inflate_return(self):
        now = 400 * D
        a = S.metrics(port(steady()), now)
        b = S.metrics(port(steady(deposit_at=196, deposit=5e6)), now)
        self.assertAlmostEqual(a["ret_1y"], b["ret_1y"], delta=0.35)   # stesso trader, un deposito in mezzo
        self.assertAlmostEqual(b["dd"], 0.0)

    def test_drawdown_r2_underwater(self):
        idx = [1, 1.2, 0.9, 1.0, 1.3, 1.4]
        self.assertAlmostEqual(S.max_dd(idx), 0.25)
        ts = [0, 14, 28, 42, 56, 70]
        self.assertEqual(S.underwater_days(ts, idx), 42)   # dal massimo a 14 al recupero a 56
        self.assertEqual(S.underwater_days([0, 14, 28, 42], [1, 2, 1.5, 1.6]), 28)   # non ancora recuperato
        self.assertEqual(S.r2_log([0, 1, 2, 3], [1, 0.9, 0.8, 0.7]), 0.0)   # discesa regolare: non è crescita
        self.assertGreater(S.r2_log([0, 1, 2, 3], [1, 2, 4, 8]), 0.999)

    def test_month_history_raises_dd(self):
        now = 400 * D
        month = [(370, 2e6, 0), (380, 1.4e6, -6e5), (395, 2.2e6, 2e5)]   # buco a metà mese invisibile nei punti a 14 giorni
        m = S.metrics(port(steady(), month=month), now)
        self.assertAlmostEqual(m["dd"], 0.30, places=2)

    def test_history_gaps_and_perp_share(self):
        now = 400 * D
        pts = [(0, 1e6, 0), (300, 2e6, 1e6), (330, 2.1e6, 1.1e6), (400, 2.3e6, 1.3e6)]
        m = S.metrics(port(pts), now)
        self.assertIn("history", S.fails(m, S.TH0))   # buco di 300 giorni
        spot = S.metrics(port(steady(), perp=[(d, 1e5, 0) for d, _, _ in steady()]), now)
        self.assertIn("perp", S.fails(spot, S.TH0))    # PnL tutto da spot

    def test_funding(self):
        e = [{"delta": {"usdc": "-500"}}, {"delta": {"usdc": "200"}}]
        f = S.funding_stats(e, 10_000, 1e6)
        self.assertEqual(f["funding_cost"], 300)
        self.assertAlmostEqual(f["fund_pnl"], 0.03)
        self.assertTrue(math.isinf(S.funding_stats(e, -5, 1e6)["fund_pnl"]))
        self.assertEqual(S.funding_stats([{"delta": {"usdc": "50"}}], -5, 1e6)["fund_pnl"], 0.0)   # incassato


class FiltersScoreTest(unittest.TestCase):
    def good(self, **k):
        m = {"ok": True, "value": 2e6, "history_days": 500, "max_gap_days": 14, "negative": False, "active": True, "perp_share": 0.9,
             "ret_1y": 1.5, "dd": 0.15, "r2": 0.9, "pos": 0.7, "fund_pnl": 0.02, "check_ok": True}
        m.update(k)
        return m

    def test_filters_and_relaxation(self):
        self.assertEqual(S.fails(self.good(), S.TH0), [])
        self.assertEqual(S.fails(self.good(value=5e5, dd=0.4), S.TH0), ["value", "dd"])
        self.assertEqual(S.fails(self.good(fund_pnl=None), S.TH0), ["fund"])   # funding non verificato = non passa
        self.assertEqual(S.fails(self.good(check_ok=False), S.TH0), ["check"])
        self.assertIn("r2", S.fails(self.good(r2=0.7), S.thresholds(0)))
        self.assertNotIn("r2", S.fails(self.good(r2=0.7), S.thresholds(1)))
        self.assertEqual(S.thresholds(4), {"ret": 0.60, "dd": 0.35, "r2": 0.65, "fund": 0.20})

    def test_score_order(self):
        a = S.score(self.good())
        self.assertGreater(a, S.score(self.good(dd=0.28)))
        self.assertGreater(a, S.score(self.good(r2=0.78)))
        self.assertGreater(a, S.score(self.good(fund_pnl=0.12)))
        self.assertTrue(0 <= a <= 100)

    def test_hysteresis(self):
        ranked = [("a", 80), ("b", 70), ("c", 60), ("d", 65)]
        self.assertEqual(S.select(ranked, []), ["a", "b", "d"])
        self.assertEqual(S.select(ranked, ["a", "b", "c"]), ["a", "b", "c"])        # 65 < 60 × 1,15: resta c
        self.assertEqual(S.select(ranked + [("e", 75)], ["a", "b", "c"]), ["a", "e", "b"])   # 75 > 69: entra e
        self.assertEqual(S.select(ranked, ["x", "a", "b"]), ["a", "b", "d"])        # x non passa più i filtri: esce
        self.assertEqual(S.select([("a", 50)], ["a", "b"]), ["a"])

    def test_slots(self):
        self.assertEqual(S.slots(["a", "b", "c"], {}), {"a": 1, "b": 2, "c": 3})
        self.assertEqual(S.slots(["c", "d", "a"], {"a": 1, "b": 2, "c": 3}), {"a": 1, "c": 3, "d": 2})


class TrackTest(unittest.TestCase):
    def test_chain_and_learn(self):
        r, dd = S.chain_return([(1e6, 0), (1.2e6, 2e5), (0.9e6, -1e5), (1.1e6, 1e5)])
        self.assertAlmostEqual(r, 0.1, places=6)
        self.assertAlmostEqual(dd, 0.25, places=6)
        self.assertEqual(S.median([3, 1, None, 2]), 2)
        self.assertAlmostEqual(S.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        w, info = S.learn(S.WEIGHTS0, [[0.5, 0.5, 0.5, 0.5, 0.1]] * 5)
        self.assertFalse(info["applied"])                      # campione troppo piccolo: pesi fermi
        self.assertEqual(w, S.WEIGHTS0)
        obs = [[i / 40, 0.5, 0.5, 1 - i / 40, i / 100] for i in range(40)]   # calmar predice, funding al contrario
        w, info = S.learn(S.WEIGHTS0, obs)
        self.assertTrue(info["applied"])
        self.assertAlmostEqual(sum(w.values()), 1.0, places=3)
        self.assertGreater(w["calmar"], S.WEIGHTS0["calmar"])
        self.assertLess(w["fund"], S.WEIGHTS0["fund"])
        for k in w:
            self.assertLessEqual(abs(w[k] - S.WEIGHTS0[k]), S.LEARN_STEP + 0.02)

    def test_update_track_evaluates_horizon(self):
        lb0 = {"p": [1_000_000, 0], "q": [1_000_000, 0], "b": [1_000_000, 0]}
        t = S.update_track({}, "2026-01-01", lb0, [{"address": "p"}], [{"address": "q", "ret_1y": 1, "dd": 0.1, "r2": 0.9, "pos": 0.6, "fund_pnl": 0}], ["b"])
        self.assertEqual(len(t["cohorts"]), 1)
        lb1 = {"p": [1_200_000, 200_000], "q": [1_100_000, 100_000], "b": [1_000_000, 0]}
        t = S.update_track(t, "2026-01-08", lb1, [{"address": "p"}], [], ["b"])
        ev = t["cohorts"][0]["ev"]["7"]
        self.assertAlmostEqual(ev["pick_mean"], 0.2)
        self.assertAlmostEqual(ev["passed_med"], 0.1)
        self.assertAlmostEqual(ev["bench_med"], 0.0)
        s = S.track_summary(t)
        self.assertEqual(s["7"]["n"], 1)
        self.assertEqual(s["7"]["beat_bench"], 1.0)

    def test_prefilter(self):
        def row(a, av, roi_all, roi_m, vlm_m):
            return {"ethAddress": a, "accountValue": str(av), "windowPerformances": [
                ["allTime", {"pnl": str(av * roi_all), "roi": str(roi_all), "vlm": "1"}], ["month", {"pnl": "1", "roi": str(roi_m), "vlm": str(vlm_m)}]]}
        rows = [row("a", 2e6, 2, 0.1, 1e6), row("mm", 2e6, 2, 0.1, 5e8), row("lose", 2e6, -0.1, 0.1, 1e6),
                row("small", 5e5, 2, 0.1, 1e6), row("v", 3e6, -0.5, -0.5, 0), row("hlp", 9e7, 1, 0, 1)]
        c, rej = S.prefilter(rows, {"v"}, {"hlp"})
        self.assertEqual([x["address"] for x in c], ["v", "a"])
        self.assertEqual((rej["turnover"], rej["pnl_roi"], rej["system"]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
