"""Cascata di liquidazioni (radar/liqcascade.py): dati sintetici, niente rete."""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar import liqcascade as C
from radar import liqsnap

KEYS_ACTIVE = {"active", "side", "start_utc", "end_utc", "start_px", "end_px", "extreme_px", "move_pct", "crossed", "crossed_usd",
               "stopped_at", "next_below", "next_above", "onchain_gone_usd", "real_usd", "coverage_note", "note", "updated_utc"}
KEYS_IDLE = {"active", "next_below", "next_above", "note", "updated_utc"}
T0 = pd.Timestamp("2026-11-12 08:00")


def candles(path):
    """Candele orarie da una lista di prezzi di apertura (close = apertura dopo, minimi/massimi stretti)."""
    idx = pd.date_range(T0, periods=len(path) - 1, freq="h")
    o, c = path[:-1], path[1:]
    return pd.DataFrame({"open": o, "high": [max(a, b) * 1.001 for a, b in zip(o, c)],
                         "low": [min(a, b) * 0.999 for a, b in zip(o, c)], "close": c}, index=idx)


def flat_then_drop():
    # 16 ore piatte a 71.500 (08:00–23:00), poi 00:00–05:00 discesa a ~67.700, poi rimbalzo
    return candles([71500] * 16 + [71460, 71100, 70900, 70200, 68900, 68500, 67700, 68200, 69000, 69100])


LEVELS = {"supports": [{"lo": 66956, "hi": 70080, "price": 68500, "strength": 4}, {"lo": 62275, "hi": 65000, "price": 63600}],
          "resistances": [{"lo": 71997, "hi": 76000, "price": 74000, "strength": 5}]}
LIQMAP = {"price": 69000, "nearest_below": {"price": 66862, "usd": 7.1e7, "dist_pct": -3.1},
          "nearest_above": {"price": 72605, "usd": 2e7, "dist_pct": 5.2}}
VIGIL = {"ts": "2026-11-13 00:00", "price": 71460,
         "long": [[70499, 1.0e8, 1.0], [69624, 6.5e7, 0.64], [68932, 8.0e7, 0.79], [67907, 6.3e7, 0.62], [66731, 4.8e7, 0.48],
                  [66233, 2.6e7, 0.26]],
         "short": [[74109, 2.9e7, 0.29], [76172, 1.0e8, 1.0]]}
NOW = pd.Timestamp("2026-11-13 07:40")


class TestDetect(unittest.TestCase):
    def test_cascata_long(self):
        ev = C.detect(flat_then_drop(), NOW)
        self.assertEqual(ev["side"], "long")
        self.assertEqual(C._hfmt(ev["start"]), "2026-11-13 00:00")   # non le ore piatte prima (stessa apertura a meno di 0,25%)
        self.assertEqual(C._hfmt(ev["end"]), "2026-11-13 05:00")
        self.assertLess(ev["move_pct"], -5)

    def test_nessun_movimento(self):
        self.assertIsNone(C.detect(candles([70000 + (i % 3) * 100 for i in range(40)]), NOW))

    def test_movimento_troppo_lento(self):   # −4% in 20 ore: mai ≥ 3% in 8 ore
        self.assertIsNone(C.detect(candles([72000 * (1 - 0.002 * i) for i in range(21)]), NOW))

    def test_fuori_dalle_24_ore(self):
        self.assertIsNone(C.detect(flat_then_drop(), NOW + pd.Timedelta(hours=26)))

    def test_cascata_short(self):
        ev = C.detect(candles([70000] * 10 + [70000, 70500, 71500, 72800, 73000, 72900]), pd.Timestamp("2026-11-12 23:00"))
        self.assertEqual(ev["side"], "short")
        self.assertGreater(ev["move_pct"], 3)


class TestBuild(unittest.TestCase):
    def snaps(self, d):
        hdr = ["ts", "mid", "k", "long_usd", "short_usd", "n_long", "n_short"]
        f = d / "hl_2026-11.csv.gz"
        mid = 71400
        k = liqsnap.bin_index(68750, mid)
        liqsnap.append_gz(f, liqsnap.snapshot_rows("2026-11-13T00:11", mid, {k: [6.7e7, 0, 3, 0], -40: [1e7, 0, 1, 0]}), hdr)
        liqsnap.append_gz(f, liqsnap.snapshot_rows("2026-11-13T07:02", 69200, {liqsnap.bin_index(68750, 69200): [2e6, 0, 1, 0]}), hdr)
        return C.read_snaps(d, ["2026-11"])

    def test_cascata_completa(self):
        ev_ms = int(pd.Timestamp("2026-11-13 03:30").value // 10**6)
        events = [{"ts": ev_ms, "exchange": "okx", "side": "long", "usd": 5e6}, {"ts": ev_ms, "exchange": "gate", "side": "short", "usd": 1e5},
                  {"ts": ev_ms - 10 * 3_600_000, "exchange": "okx", "side": "long", "usd": 9e9}]   # fuori finestra
        with tempfile.TemporaryDirectory() as d:
            s = self.snaps(Path(d))
        out = C.build({"liqmap": LIQMAP, "levels": LEVELS}, flat_then_drop(), [VIGIL], s, events, NOW)
        self.assertEqual(set(out), KEYS_ACTIVE)
        self.assertTrue(out["active"]); self.assertEqual(out["side"], "long")
        self.assertEqual([b["px"] for b in out["crossed"]], [70499, 69624, 68932, 67907])   # 66.731 non toccata, 66.233 non densa
        self.assertEqual(out["crossed_usd"], 3.08e8)
        self.assertEqual(out["stopped_at"], {"kind": "supporto", "lo": 66956.0, "hi": 70080.0})
        self.assertEqual(out["next_below"]["sr"], {"lo": 66956.0, "hi": 70080.0})   # 66.862 a meno dell'1% dalla S1
        self.assertEqual(out["next_above"]["sr"], {"lo": 71997.0, "hi": 76000.0})
        self.assertEqual(out["onchain_gone_usd"], 6.5e7)   # 67M prima, 2M dopo; i 10M a −10% non sono fra estremo e partenza
        self.assertEqual(out["real_usd"], {"long": 5e6, "short": 1e5, "exchanges": 2})
        json.dumps(out)   # serializzabile per il report

    def test_movimento_senza_fasce_o_senza_vigilia(self):
        c = flat_then_drop()
        thin = dict(VIGIL, long=[[70499, 1e8, 1.0], [60000, 9e7, 0.9]])
        for maps in ([thin], [], [dict(VIGIL, ts="2026-11-12 06:00")]):   # 1 fascia sola, nessuna mappa, mappa troppo vecchia
            out = C.build({"liqmap": LIQMAP, "levels": LEVELS}, c, maps, None, None, NOW)
            self.assertEqual(set(out), KEYS_IDLE); self.assertFalse(out["active"])
            self.assertEqual(out["next_below"]["px"], 66862)

    def test_nessuna_cascata(self):
        out = C.build({"liqmap": LIQMAP, "levels": None}, candles([69000] * 30), [VIGIL], None, None, NOW)
        self.assertEqual(set(out), KEYS_IDLE)
        self.assertFalse(out["active"]); self.assertIsNone(out["next_below"]["sr"])

    def test_fermata_su_fascia_o_nessuno(self):
        ev = {"side": "long", "extreme_px": 66900.0, "start_px": 71460.0}
        self.assertEqual(C.stopped_at(ev, None, VIGIL)["kind"], "fascia")
        self.assertEqual(C.stopped_at(dict(ev, extreme_px=65500.0), None, VIGIL), {"kind": "nessuno", "lo": None, "hi": None})

    def test_dati_mancanti(self):
        self.assertIsNone(C.build({}, flat_then_drop(), [VIGIL], None, None, NOW))
        self.assertIsNone(C.build({"liqmap": LIQMAP}, None, [VIGIL], None, None, NOW))
        self.assertIsNone(C.build({"liqmap": LIQMAP}, pd.DataFrame(columns=["open", "high", "low", "close"]), [], None, None, NOW))
        with tempfile.TemporaryDirectory() as d:   # cartella vuota: nessun file, nessuna eccezione
            self.assertIsNone(C.update({}, d, now=NOW))
            self.assertIsNone(C.update(None, d, now=NOW))
            (Path(d) / "liqmap_prev.json").write_text("{rotto")
            self.assertIsNone(C.update({"liqmap": LIQMAP}, d, now=NOW))
        self.assertIsNone(C.onchain_gone(pd.DataFrame(), {"start": NOW, "end": NOW, "side": "long", "extreme_px": 1, "start_px": 2}))

    def test_update_salva_la_mappa(self):
        bins = [[69000 * (1 + 0.0025 * k), 1e6 if k < 0 else 0, 1e6 if k > 0 else 0] for k in range(-40, 40)]
        bins[20][1] = bins[21][1] = 5e7; bins[60][2] = 3e7
        lm = dict(LIQMAP, bins=bins, as_of={"okx": {"data": "2026-11-13 07:00:00"}}, ts="2026-11-13 07:38:00")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            candles([69000] * 30).rename_axis("t").to_csv(d / "spot_1h.csv")
            p = d / "liqmap_prev.json"
            p.write_text(json.dumps({"maps": [dict(VIGIL, ts="2026-11-11 10:00"), VIGIL]}))
            out = C.update({"liqmap": lm, "levels": LEVELS}, d, now=pd.Timestamp("2026-11-13 07:40"))
            self.assertIsNotNone(out)
            maps = json.loads(p.read_text())["maps"]
            self.assertEqual([m["ts"] for m in maps], ["2026-11-13 00:00", "2026-11-13 07:00"])   # oltre 36 ore: tolta
            self.assertTrue(any(abs(b[0] - bins[20][0]) < 400 for b in maps[-1]["long"]))
            C.update({"liqmap": lm}, d, now=pd.Timestamp("2026-11-13 07:50"))   # stesso "as of": nessun doppione
            self.assertEqual(len(json.loads(p.read_text())["maps"]), 2)


if __name__ == "__main__":
    unittest.main()
