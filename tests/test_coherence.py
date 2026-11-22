"""Controlli di coerenza orari (radar/coherence.py): buchi nei dati di W3, storico W3.1 riscritto, decisione cambiata con i
dati definitivi. Solo avviso: un messaggio per evento, marcato solo se Telegram conferma. Niente rete."""
import unittest

import pandas as pd

from radar import coherence


def frame(days):
    return pd.DataFrame({"close": 1.0}, index=pd.to_datetime(days))


def tr(sig, entry, side="long", exit_=None, reason="open"):
    return {"signal": sig, "entry": entry, "side": side, "exit": exit_, "reason": reason}


def wcur(*trades):
    return {"history": {"trades": list(trades)}}


class Sender:
    def __init__(self, ok=True):
        self.ok, self.msgs = ok, []

    def __call__(self, text):
        self.msgs.append(text)
        return self.ok


class TestGaps(unittest.TestCase):
    def test_buchi_negli_ultimi_giorni(self):
        days = pd.date_range("2026-10-01", "2026-11-21", freq="D")
        full = {k: frame(days) for k in ("spot", "perp", "funding", "metrics")}
        self.assertEqual(coherence.gaps(full), {})
        d = dict(full, perp=frame(days.drop(pd.Timestamp("2026-11-10")).drop(pd.Timestamp("2026-11-11"))))
        self.assertEqual(coherence.gaps(d), {"perp": ["2026-11-10", "2026-11-11"]})
        # un buco più vecchio della finestra non conta; una fonte assente o vuota non è un buco (la segnalano altri avvisi)
        old = dict(full, spot=frame(days.drop(pd.Timestamp("2026-10-02"))))
        self.assertEqual(coherence.gaps(old, days=30), {})
        self.assertEqual(coherence.gaps({"spot": frame([])}), {})


class TestHistory(unittest.TestCase):
    def test_storico_riscritto(self):
        a = tr("2026-08-23", "2026-08-24", exit_="2026-11-09", reason="ema")
        b = tr("2026-11-15", "2026-11-16", side="short")
        prev = coherence.trades_sig(wcur(a, b))
        self.assertEqual(coherence.history_changes(prev, coherence.trades_sig(wcur(a, b))), [])
        # un trade aperto che si chiude e un trade nuovo sono normali
        b2 = tr("2026-11-15", "2026-11-16", side="short", exit_="2026-12-07", reason="trail")
        c = tr("2027-01-10", "2027-01-11")
        self.assertEqual(coherence.history_changes(prev, coherence.trades_sig(wcur(a, b2, c))), [])
        # un trade già visto che sparisce, cambia lato o cambia uscita: storico riscritto
        self.assertEqual(len(coherence.history_changes(prev, coherence.trades_sig(wcur(a)))), 1)
        self.assertIn("2026-11-15", coherence.history_changes(prev, coherence.trades_sig(wcur(a)))[0])
        a2 = tr("2026-08-23", "2026-08-24", exit_="2026-10-26", reason="trail")
        ch = coherence.history_changes(prev, coherence.trades_sig(wcur(a2, b)))
        self.assertEqual(len(ch), 1)
        self.assertIn("2026-08-23", ch[0])
        self.assertEqual(len(coherence.history_changes(prev, coherence.trades_sig(
            wcur(a, tr("2026-11-15", "2026-11-16", side="long"))))), 1)
        self.assertEqual(coherence.history_changes({}, prev), [])            # primo giro: nessun confronto


class TestUpdate(unittest.TestCase):
    def setUp(self):
        days = pd.date_range("2026-10-01", "2026-11-21", freq="D")
        self.d = {k: frame(days) for k in ("spot", "perp", "funding", "metrics")}
        self.a = tr("2026-08-23", "2026-08-24", exit_="2026-11-09", reason="ema")
        self.b = tr("2026-11-15", "2026-11-16", side="short")

    def test_tutto_coerente_nessun_messaggio(self):
        st, s = {}, Sender()
        out = coherence.update(self.d, wcur(self.a, self.b), {"last": []}, st, send=s)
        self.assertEqual((out["problems"], s.msgs), ([], []))
        self.assertEqual(set(st["coherence"]["trades"]), {"2026-08-23", "2026-11-15"})

    def test_un_avviso_per_evento(self):
        st, s = {}, Sender()
        coherence.update(self.d, wcur(self.a, self.b), None, st, send=s)
        prov = {"last": [{"date": "2026-11-15", "changed": True, "decision_p": "ingresso short", "decision_d": "nessuna"},
                         {"date": "2026-11-08", "changed": False, "decision_p": "uscita ema", "decision_d": "uscita ema"}]}
        d = dict(self.d, funding=self.d["funding"].drop(pd.Timestamp("2026-11-12")))
        out = coherence.update(d, wcur(self.a), prov, st, send=s)
        self.assertEqual(len(out["problems"]), 3)                           # buco, storico riscritto, decisione cambiata
        self.assertEqual(len(s.msgs), 1)
        for x in ("funding", "2026-11-12", "2026-11-15", "ingresso short", "nessuna", "Nessuna azione automatica"):
            self.assertIn(x, s.msgs[0])
        coherence.update(d, wcur(self.a), prov, st, send=s)                 # stessi eventi al giro dopo: nessun nuovo messaggio
        self.assertEqual(len(s.msgs), 1)

    def test_invio_fallito_si_riprova(self):
        st = {}
        coherence.update(self.d, wcur(self.a, self.b), None, st, send=Sender())
        bad, good = Sender(ok=False), Sender()
        coherence.update(self.d, wcur(self.a), None, st, send=bad)
        self.assertEqual(len(bad.msgs), 1)
        self.assertEqual(st["coherence"].get("sent", []), [])
        self.assertIn("2026-11-15", st["coherence"]["trades"])              # riferimento non aggiornato finché non avvisato
        coherence.update(self.d, wcur(self.a), None, st, send=good)
        self.assertEqual(len(good.msgs), 1)
        self.assertNotIn("2026-11-15", st["coherence"]["trades"])           # avvisato: il nuovo storico diventa il riferimento

    def test_dati_mancanti_non_rompe(self):
        st, s = {}, Sender()
        self.assertEqual(coherence.update({}, None, None, st, send=s)["problems"], [])
        self.assertEqual(s.msgs, [])


class TestCli(unittest.TestCase):
    def test_giro_orario_chiama_il_controllo(self):
        import inspect
        from radar import cli
        src = inspect.getsource(cli.daily)
        self.assertIn("coherence", src)
        self.assertLess(src.index("coherence"), src.index('_soft("heartbeat"'))   # i problemi entrano nel messaggio di salute


if __name__ == "__main__":
    unittest.main()
