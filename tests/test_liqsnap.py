"""Registratore dei livelli di liquidazione reali (radar/liqsnap.py): solo funzioni pure, niente rete."""
import gzip
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar import liqsnap


def pos(side, liq, btc=1.0, acct="a", ts=100.0, ex="hl"):
    return {"ex": ex, "acct": acct, "side": side, "btc": btc, "entry": 70000.0, "liq": liq, "lev": 10, "ts": ts}


class TestLiqSnap(unittest.TestCase):
    def test_parse_hl_e_lighter(self):
        st = {"time": 1_794_000_000_000, "assetPositions": [
            {"position": {"coin": "BTC", "szi": "-2.5", "entryPx": "80000", "liquidationPx": "90000", "leverage": {"value": 10}}},
            {"position": {"coin": "BTC", "szi": "0"}},
            {"position": {"coin": "ETH", "szi": "5", "liquidationPx": "1000"}},
            {"position": {"coin": "BTC", "szi": "1", "entryPx": "80000", "liquidationPx": None}}]}
        p = liqsnap.parse_hl(st, "0xABC")
        self.assertEqual(len(p), 2)
        self.assertEqual((p[0]["side"], p[0]["btc"], p[0]["liq"], p[0]["acct"], p[0]["ts"]), ("short", 2.5, 90000.0, "0xabc", 1_794_000_000))
        self.assertIsNone(p[1]["liq"])
        lt = {"accounts": [{"index": 7, "positions": [
            {"symbol": "BTC", "sign": -1, "position": "600", "avg_entry_price": "70971.9", "liquidation_price": "93562.4", "initial_margin_fraction": "20.00"},
            {"symbol": "BTC", "sign": 1, "position": "0", "liquidation_price": "0"},
            {"symbol": "SUI", "sign": -1, "position": "10", "liquidation_price": "2"}]},
            {"index": 8, "positions": [{"symbol": "BTC", "sign": 1, "position": "3", "avg_entry_price": "70000", "liquidation_price": "0", "initial_margin_fraction": "33.33"}]}]}
        q = liqsnap.parse_lighter(lt, 5.0)
        self.assertEqual([(x["acct"], x["side"], x["liq"]) for x in q], [("7", "short", 93562.4), ("8", "long", None)])
        self.assertEqual(q[0]["lev"], 5.0)

    def test_controlli_lato_e_liq(self):
        self.assertIsNone(liqsnap.check(pos("long", 60000), 70000))
        self.assertIsNone(liqsnap.check(pos("short", 80000), 70000))
        self.assertEqual(liqsnap.check(pos("long", 71000), 70000), "wrong_side")    # long con liq sopra il prezzo
        self.assertEqual(liqsnap.check(pos("short", 69000), 70000), "wrong_side")   # short con liq sotto il prezzo
        self.assertEqual(liqsnap.check(pos("long", None), 70000), "no_liq")
        self.assertEqual(liqsnap.check(pos("long", 0), 70000), "no_liq")
        self.assertEqual(liqsnap.check(pos("long", 60000, btc=0), 70000), "bad")

    def test_doppioni(self):
        ps = [pos("long", 60000, acct="a", ts=1), pos("long", 61000, acct="a", ts=5), pos("short", 80000, acct="a", ts=2),
              pos("long", 60000, acct="a", ts=1, ex="lighter")]
        out, n = liqsnap.dedupe(ps)
        self.assertEqual(n, 1)
        self.assertEqual(len(out), 3)
        self.assertIn(61000, [p["liq"] for p in out if p["ex"] == "hl" and p["side"] == "long"])

    def test_fasce(self):
        mid = 100000.0
        self.assertEqual(liqsnap.bin_index(100000, mid), 0)
        self.assertEqual(liqsnap.bin_index(100249, mid), 0)
        self.assertEqual(liqsnap.bin_index(100250, mid), 1)
        self.assertEqual(liqsnap.bin_index(99999, mid), -1)
        self.assertEqual(liqsnap.bin_index(85000, mid), -60)
        ps = [pos("long", 95100, btc=2, acct="a"), pos("long", 95200, btc=1, acct="b"), pos("short", 103000, btc=1, acct="c"),
              pos("long", 80000, btc=1, acct="d"), pos("short", 99000, btc=1, acct="e"), pos("long", None, btc=1, acct="f")]
        b, st = liqsnap.bins(ps, mid)
        self.assertEqual(b[-20], [300000.0, 0.0, 2, 0])     # 95.100 e 95.200: stessa fascia −5,00% … −4,75%
        self.assertEqual(b[12], [0.0, 100000.0, 0, 1])
        self.assertEqual(len(b), 2)
        self.assertEqual(st["beyond_long"], 100000)         # −20%: fuori da ±15%
        self.assertEqual(st["wrong_side"], 1)
        self.assertEqual(st["no_liq_usd"], 100000)
        self.assertEqual(st["binned_long"], 300000); self.assertEqual(st["binned_short"], 100000)
        self.assertEqual(st["ntl_long"], 500000); self.assertEqual(st["positions"], 6)
        self.assertTrue(all(liqsnap.KMIN <= k <= liqsnap.KMAX for k in b))

    def test_cluster(self):
        mid = 100000.0
        b = {-20: [5e6, 0, 3, 0], -19: [1e6, 0, 1, 0], -4: [0.5e6, 0, 1, 0], 8: [0, 3e6, 0, 2], 30: [0, 1e6, 0, 1]}
        dn = liqsnap.clusters(b, mid, "long")
        self.assertEqual(len(dn), 1)                         # 0,5M sotto la soglia di $2M
        self.assertEqual(dn[0]["usd"], 6e6); self.assertEqual(dn[0]["n"], 4); self.assertLess(dn[0]["dist_pct"], 0)
        up = liqsnap.clusters(b, mid, "short")
        self.assertEqual([c["k"] for c in up], [8])          # $1M a +7,5%: sotto soglia
        s = liqsnap.summary(b, mid)
        self.assertEqual(s["nearest_above"]["k"], 8); self.assertEqual(s["largest_below"]["usd"], 6e6)
        self.assertEqual(liqsnap.clusters({}, mid, "long"), [])

    def test_rotazione_e_stato(self):
        addrs = [f"0x{i:040x}" for i in range(600)]
        groups = [liqsnap.rotation(addrs, h) for h in range(6)]
        self.assertEqual(sorted(a for g in groups for a in g), sorted(addrs))   # ogni conto in un solo gruppo, ogni 6 ore
        self.assertEqual(groups[0], liqsnap.rotation(addrs, 6))
        self.assertTrue(all(60 < len(g) < 140 for g in groups))
        now = 100000.0
        st = {"x": {"t": now - 3600, "p": [pos("long", 1)]}, "old": {"t": now - 8 * 3600, "p": [pos("long", 1)]},
              "gone": {"t": now - 60, "p": [pos("long", 1)]}}
        new, stale = liqsnap.merge_state(st, {"gone": [], "y": [pos("short", 2)]}, now)
        self.assertEqual(sorted(new), ["x", "y"]); self.assertEqual(stale, 1)
        h = liqsnap.hot({"a": {"p": [pos("long", 65000, btc=20)]}, "b": {"p": [pos("long", 65000, btc=1)]}, "c": {"p": [pos("long", 60000, btc=50)]},
                         "far": {"p": [pos("long", 30000, btc=500)]}, "noliq": {"p": [pos("long", None, btc=500)]}}, 70000)
        self.assertEqual(h, ["c", "a"])   # 1 BTC sotto $1M; liquidazioni lontane o assenti: bastano le letture a rotazione

    def test_file_gz_in_coda(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "hl_2026-11.csv.gz"
            hdr = ["ts", "mid", "k", "long_usd", "short_usd", "n_long", "n_short"]
            liqsnap.append_gz(f, liqsnap.snapshot_rows("2026-11-11T10:07", 70000, {-3: [1e6, 0, 1, 0]}), hdr)
            first = f.read_bytes()
            liqsnap.append_gz(f, liqsnap.snapshot_rows("2026-11-11T11:07", 70100, {5: [0, 2e6, 0, 2]}), hdr)
            self.assertTrue(f.read_bytes().startswith(first))   # si aggiunge in coda, il file non si riscrive
            x = pd.read_csv(f)
            self.assertEqual(list(x.columns), hdr); self.assertEqual(len(x), 2); self.assertEqual(list(x["k"]), [-3, 5])
            self.assertEqual(gzip.decompress(f.read_bytes()).decode().count("ts,mid"), 1)

    def test_ordine_e_budget(self):
        # prima i conti prioritari e i caldi, poi la rotazione; niente doppioni; esclusi quelli già letti da liqmap
        self.assertEqual(liqsnap.todo_list(["0xA", "b"], ["c", "b"], ["d", "a", "e"], skip=["E"]), ["0xa", "b", "c", "d", "a"])

        class Fake:   # sessione finta: nessuna rete
            n = 0

            def post(self, url, json=None, timeout=None):
                Fake.n += 1
                return type("R", (), {"status_code": 200, "raise_for_status": lambda s: None, "json": lambda s: {"ok": 1}})()
        hl = liqsnap._HL(session=Fake(), per_s=1000, deadline=0.0001)   # scadenza già passata: nessuna richiesta
        got, failed = hl.states(["x", "y"])
        self.assertEqual((got, failed, Fake.n), ({}, 2, 0))
        hl = liqsnap._HL(session=Fake(), per_s=1000, deadline=None)
        got, failed = hl.states(["x", "y"])
        self.assertEqual((len(got), failed), (2, 0))

    def test_una_fotografia_per_ora(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.assertFalse(liqsnap.done_this_hour(d, "2026-11-13T08"))
            (d / "hl_state.json").write_text('{"last_hour": "2026-11-13T08", "acc": {}}')
            self.assertFalse(liqsnap.done_this_hour(d, "2026-11-13T08"))   # manca Lighter: il giro autonomo la completa
            (d / "lighter_state.json").write_text('{"last_hour": "2026-11-13T08", "acc": {}}')
            self.assertTrue(liqsnap.done_this_hour(d, "2026-11-13T08"))
            self.assertFalse(liqsnap.done_this_hour(d, "2026-11-13T09"))



class TestUnicoScrittore(unittest.TestCase):
    """M5: con la catena oraria viva (chain_at < 2 h) il giro completo non legge né scrive data/liqsnap."""
    def test_chain_alive_e_view(self):
        import json
        import time
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.assertFalse(liqsnap.chain_alive(d))
            now = time.time()
            st = {"mid": 70000.0, "last_hour": "2026-11-13T10", "chain_at": int(now - 3600),
                  "acc": {"a": {"t": now - 600, "p": [pos("long", 63000, btc=10, ts=now - 600)]}}}
            (d / "hl_state.json").write_text(json.dumps(st))
            self.assertTrue(liqsnap.chain_alive(d, now))
            self.assertFalse(liqsnap.chain_alive(d, now + 2 * 3600))   # catena ferma da oltre 2 ore: il giro completo scrive
            before = sorted(p.name for p in d.iterdir())
            out = liqsnap.view(d, 70000.0)
            self.assertEqual(sorted(p.name for p in d.iterdir()), before)   # nessun file scritto
            self.assertTrue(out["hl"]["ok"])
            self.assertFalse(out["hl"]["recorded"])
            self.assertEqual(out["hl"]["holders"], 1)
            self.assertFalse(out["lighter"]["ok"] and out["lighter"].get("holders"))

    def test_record_in_sola_lettura_con_catena_viva(self):
        import json
        import time
        with tempfile.TemporaryDirectory() as root:
            d = Path(root) / "liqsnap"
            d.mkdir()
            (d / "hl_state.json").write_text(json.dumps({"mid": 70000.0, "chain_at": int(time.time()), "acc": {}}))
            orig = liqsnap._HL
            liqsnap._HL = None   # qualsiasi accesso alla rete fallirebbe
            try:
                out = liqsnap.record(root, None, [], 70000.0)
            finally:
                liqsnap._HL = orig
            self.assertIn("sola lettura", out["source"])
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["hl_state.json"])


def _gz(rows: str) -> bytes:
    return gzip.compress(rows.encode(), mtime=0)


class TestMergeFile(unittest.TestCase):
    def test_casi(self):
        base, mine, theirs = _gz("h\n1\n"), _gz("h\n1\n") + _gz("2\n"), _gz("h\n1\n") + _gz("3\n")
        out, _ = liqsnap.merge_file("data/liqsnap/hl_2026-11.csv.gz", base, mine, theirs)
        self.assertEqual(gzip.decompress(out).decode(), "h\n1\n3\n2\n")      # nessun membro perso
        self.assertEqual(liqsnap.merge_file("x.csv.gz", base, mine, base)[0], mine)
        self.assertEqual(liqsnap.merge_file("x.csv.gz", base, base, theirs)[0], theirs)
        # file nuovo creato da entrambi (primo giro del mese): una sola intestazione
        out, _ = liqsnap.merge_file("x.csv.gz", None, _gz("h\n2\n"), _gz("h\n3\n"))
        self.assertEqual(gzip.decompress(out).decode(), "h\n3\n2\n")
        out, _ = liqsnap.merge_file("c.csv", b"h\n1\n", b"h\n1\n2\n", b"h\n1\n3\n")
        self.assertEqual(out, b"h\n1\n3\n2\n")
        out, _ = liqsnap.merge_file("c.csv", None, b"h\n2\n", b"h\n3\n")
        self.assertEqual(out, b"h\n3\n2\n")
        # stato JSON cambiato da entrambi: la nostra versione (la più recente)
        self.assertEqual(liqsnap.merge_file("s.json", b"{}", b'{"a":1}', b'{"a":2}')[0], b'{"a":1}')
        self.assertIsNone(liqsnap.merge_file("s.json", b"{}", None, b"{}")[0])


class TestSyncRepo(unittest.TestCase):
    """Due scrittori sullo stesso .csv.gz (repo git locali, niente rete): dopo sync + push non si perde nessun membro gzip."""
    def git(self, cwd, *a):
        import subprocess
        return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    def clone(self, remote, dst):
        self.git(dst.parent, "clone", "-q", str(remote), dst.name)
        self.git(dst, "config", "user.name", "t")
        self.git(dst, "config", "user.email", "t@example.invalid")
        self.git(dst, "config", "commit.gpgsign", "false")

    def test_due_scrittori(self):
        import shutil
        if not shutil.which("git"):
            self.skipTest("git assente")
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            remote = t / "remote.git"
            self.git(t, "init", "-q", "--bare", "-b", "main", str(remote))
            a, b = t / "a", t / "b"
            self.clone(remote, a)
            self.git(a, "checkout", "-q", "-b", "main")
            f = Path("data/liqsnap/hl_2026-11.csv.gz")
            hdr = ["ts", "mid", "k", "long_usd", "short_usd", "n_long", "n_short"]
            (a / f.parent).mkdir(parents=True)
            liqsnap.append_gz(a / f, [["T0", 1, 0, 1, 1, 1, 1]], hdr)
            (a / "data/state.json").write_text('{"last_run": "0"}')
            self.git(a, "add", "-A")
            self.git(a, "commit", "-q", "-m", "base")
            self.git(a, "push", "-q", "-u", "origin", "main")
            self.clone(remote, b)
            # scrittore A (catena oraria): due fotografie, la seconda non ancora spinta quando B spinge
            liqsnap.append_gz(a / f, [["A1", 1, 0, 1, 1, 1, 1]], hdr)
            self.git(a, "commit", "-q", "-am", "A1")
            self.git(a, "push", "-q")
            liqsnap.append_gz(a / f, [["A2", 1, 0, 1, 1, 1, 1]], hdr)
            self.git(a, "commit", "-q", "-am", "A2")
            # scrittore B (giro completo, partito prima di A1): una fotografia + stato
            liqsnap.append_gz(b / f, [["B1", 1, 0, 1, 1, 1, 1]], hdr)
            (b / "data/state.json").write_text('{"last_run": "B"}')
            self.git(b, "commit", "-q", "-am", "B1")
            self.assertEqual(liqsnap.sync_repo(b), "merged")
            self.git(b, "push", "-q")
            self.assertEqual(liqsnap.sync_repo(a), "merged")
            self.git(a, "push", "-q")
            self.assertEqual(liqsnap.sync_repo(b), "ff")
            self.assertEqual(liqsnap.sync_repo(b), "same")
            for repo in (a, b):
                rows = pd.read_csv(repo / f)["ts"].tolist()
                self.assertEqual(sorted(rows), ["A1", "A2", "B1", "T0"], repo.name)
                self.assertEqual(len(rows), 4)   # un'intestazione sola, nessun doppione
                self.assertEqual((repo / "data/state.json").read_text(), '{"last_run": "B"}')
            # con -X theirs (vecchio metodo) lo stesso scenario perdeva righe: verifica che il rischio fosse reale
            c = t / "c"
            self.clone(remote, c)
            liqsnap.append_gz(c / f, [["C1", 1, 0, 1, 1, 1, 1]], hdr)
            self.git(c, "commit", "-q", "-am", "C1")
            liqsnap.append_gz(a / f, [["A3", 1, 0, 1, 1, 1, 1]], hdr)
            self.git(a, "commit", "-q", "-am", "A3")
            self.git(a, "push", "-q")
            self.git(c, "pull", "-q", "--rebase", "-X", "theirs")
            self.assertNotIn("A3", pd.read_csv(c / f)["ts"].tolist())


if __name__ == "__main__":
    unittest.main()
