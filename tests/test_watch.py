"""Lista dei 3 wallet osservati, candidati dello scout e comandi Telegram di approvazione (radar/wallets.py, radar/scout.py)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from radar import journal
from radar import scout as S
from radar import wallets as W

A = lambda k: "0x" + k * 40   # noqa: E731


def watch_file(d: str) -> Path:
    p = Path(d) / "wallets_watch.json"
    w = W.default_watch()
    w["slots"] = [{"slot": 1, "address": A("1"), "name": "Uno", "status": "confermato", "score": 90.0},
                  {"slot": 2, "address": A("2"), "name": "Due", "status": "confermato", "score": 50.0},
                  {"slot": 3, "address": A("3"), "name": "Tre", "status": "provvisorio", "score": 80.0}]
    w["candidates"] = [{"id": "aaaa", "address": A("a"), "name": "Balena aaaa", "slot": 2, "vs_name": "Due", "score": 70.0,
                        "metrics": {"ret_1y": 1.5, "dd": 0.1}, "vs_metrics": {"ret_1y": 0.2}, "reason": "test"}]
    w["review"] = {"slot": 3, "note": "x", "options": [{"id": "bbbb", "address": A("b"), "name": "Bi", "score": 60.0}]}
    p.write_text(json.dumps(w))
    return p


class WatchListTest(unittest.TestCase):
    def test_default_and_always_three(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w.json"
            self.assertEqual([n for _, n in W.watched(p)], ["Principale", "Simile 1", "Simile 2"])
            p.write_text(json.dumps({"slots": [{"slot": 2, "address": A("c"), "name": "C"}, {"slot": 3, "address": "rotto", "name": "X"}]}))
            w = W.load_watch(p)
            self.assertEqual([x["slot"] for x in w["slots"]], [1, 2, 3])
            self.assertEqual(w["slots"][1]["address"], A("c"))
            self.assertEqual(w["slots"][2]["name"], "Simile 2")   # indirizzo non valido: torna il predefinito


class CandidateTest(unittest.TestCase):
    watch = [{"slot": 1, "address": A("1"), "name": "Uno", "score": 90.0, "fails": []},
             {"slot": 2, "address": A("2"), "name": "Due", "score": 50.0, "fails": ["dd"]},
             {"slot": 3, "address": A("3"), "name": "Tre", "score": 70.0, "fails": []}]

    def test_beats_margin_and_fails(self):
        w = self.watch
        self.assertIsNone(S.beats({"score": 80, "fails": []}, w[2]))            # +14%: sotto la soglia del 15%
        self.assertIn("+16%", S.beats({"score": 81.5, "fails": []}, w[2]))
        self.assertIn("non passa i filtri", S.beats({"score": 51, "fails": []}, w[1]))
        self.assertIsNone(S.beats({"score": 49, "fails": []}, w[1]))          # non passa, ma il candidato è peggiore
        self.assertIsNone(S.beats({"score": 99, "fails": ["ret"]}, w[1]))     # il candidato deve passare i filtri

    def test_pick_candidates(self):
        ranked = [{"address": A("1"), "score": 95, "fails": []},              # già osservato
                  {"address": A("a"), "score": 85, "fails": []},              # batte Tre (+21%) e Due (non passa)
                  {"address": A("b"), "score": 84, "fails": []},
                  {"address": A("c"), "score": 60, "fails": []},              # batte solo Due
                  {"address": A("d"), "score": 99, "fails": []}]              # scartato dall'utente
        out = S.pick_candidates(self.watch, ranked, dismissed={A("d")})
        self.assertEqual([(c["address"], c["slot"]) for c in out], [(A("a"), 2), (A("b"), 3), (A("c"), 2)])
        self.assertEqual(len(S.pick_candidates(self.watch, ranked * 3, n=3)), 3)
        self.assertEqual(S.pick_candidates([dict(x, fails=[], score=90) for x in self.watch], ranked), [])   # nessuno batte 90 del 15%

    def test_ids(self):
        self.assertEqual(S.cand_id("0x8bae3527e5", set()), "8bae")
        self.assertEqual(S.cand_id("0x8bae3527e5", {"8bae"}), "8bae35")

    def test_update_watch_notifies_only_new(self):
        m = lambda a, sc, f=(): {"address": a, "ok": True, "score": sc, "fails": list(f), "ret_1y": 1.0, "dd": 0.1, "r2": 0.9, "pos": 0.6, "value": 2e6, "fills_day": 3.0}   # noqa: E731
        by = {A("1"): m(A("1"), 90), A("2"): m(A("2"), 50, ["dd"]), A("3"): m(A("3"), 80), A("a"): m(A("a"), 85)}
        w = W.default_watch()
        w["slots"] = [{"slot": i, "address": A(str(i)), "name": f"S{i}"} for i in (1, 2, 3)]
        entry = lambda m: {"name": "x", "kind": "conto", "why": "", "curve": []}   # noqa: E731
        new = S.update_watch(w, by, [by[A("a")]], "2026-11-08", entry)
        self.assertEqual([(c["id"], c["slot"], c["vs_name"]) for c in new], [("aaaa", 2, "S2")])
        self.assertEqual(w["slots"][1]["fails"], ["drawdown alto"])
        new[0]["notified"] = "2026-11-08"
        self.assertEqual(S.update_watch(w, by, [by[A("a")]], "2026-11-09", entry), [])   # già notificato: niente messaggio
        self.assertEqual(w["candidates"][0]["first"], "2026-11-08")
        self.assertIn("/sostituisci 2 aaaa", W.candidate_text(w["candidates"][0]))


class CommandTest(unittest.TestCase):
    def test_not_ours(self):
        self.assertIsNone(W.command("/entrato 67000", "2026-11-08"))
        self.assertIsNone(W.command("ciao", "2026-11-08"))

    def test_replace_confirm_dismiss(self):
        with tempfile.TemporaryDirectory() as d:
            p = watch_file(d)
            self.assertIn("Balena aaaa", W.command("/candidati", "2026-11-08", p))
            self.assertIn("Formato", W.command("/sostituisci 4 aaaa", "2026-11-08", p))
            self.assertIn("Nessun candidato", W.command("/sostituisci 2 zzzz", "2026-11-08", p))
            r = W.command("/sostituisci@RadarBot 2 aaaa Nuova balena", "2026-11-08", p)
            self.assertIn("✅ Posto 2", r)
            w = W.load_watch(p)
            self.assertEqual((w["slots"][1]["address"], w["slots"][1]["name"]), (A("a"), "Nuova balena"))
            self.assertEqual(w["candidates"], [])
            self.assertEqual(w["history"][-1]["out"], [A("2"), "Due"])
            self.assertIn("Nessun candidato", W.command(f"/sostituisci 1 {A('a')}", "2026-11-08", p))   # già usato: non è più fra i candidati
            # alternativa del posto in revisione, per prefisso dell'indirizzo
            self.assertIn("✅ Posto 3", W.command("/sostituisci 3 0xbbbbbb", "2026-11-08", p))
            self.assertIsNone(W.load_watch(p)["review"])
            self.assertIn("1, 2 o 3", W.command("/conferma", "2026-11-08", p))

    def test_confirm_and_dismiss(self):
        with tempfile.TemporaryDirectory() as d:
            p = watch_file(d)
            self.assertIn("confermato", W.command("/conferma 3", "2026-11-08", p))
            w = W.load_watch(p)
            self.assertEqual(w["slots"][2]["status"], "confermato")
            self.assertIsNone(w["review"])
            self.assertIn("scartato", W.command("/scarta aaaa", "2026-11-08", p))
            w = W.load_watch(p)
            self.assertEqual((w["candidates"], w["dismissed"]), ([], {A("a"): "2026-11-08"}))
            self.assertIn("Uno", W.command("/osservati", "2026-11-08", p))

    def test_journal_routes_wallet_commands(self):
        with tempfile.TemporaryDirectory() as d:
            p = watch_file(d)
            with mock.patch.object(W, "WATCH", p):
                j = {"trades": [], "exchange": "bybit", "ref": {}}
                self.assertIn("✅ Posto 2", journal.handle("/sostituisci 2 aaaa", "2026-11-08 10:00:00", j, {}))
                self.assertIn("/candidati", journal.handle("/aiuto", "2026-11-08 10:00:00", j, {}))
                self.assertIn("Manca il prezzo", journal.handle("/entrato", "2026-11-08 10:00:00", j, {}))   # i comandi del registro restano
            self.assertEqual(W.load_watch(p)["slots"][1]["address"], A("a"))


if __name__ == "__main__":
    unittest.main()
