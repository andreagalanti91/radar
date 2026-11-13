"""Affidabilità degli alert W3 (senza rete, telegram.send finto): marcatura solo dopo invio riuscito, uscita annunciata
ed eseguita con chiavi separate, ingresso eseguito, trailing allo 0,5%, stop orario sul livello più protettivo,
segnali/uscite ritirati, heartbeat quotidiano, dati vecchi a 36 ore, fonti isolate in update_all, workflow."""
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from radar import weekly

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "daily.yml"
SIG = "2026-08-23"


def plan(stop=70000.0):
    return {"entry_est": 77000.0, "market": "spot", "expo": 1.0, "capital": 50000.0, "notional": 50000.0, "btc": 0.65,
            "stop": stop, "stop_pct": 9.1, "loss_usd": 4700.0, "trail_dist": 7000.0, "ema21": 74000.0}


def trade(exit_=None, exit_px=None, reason="open", entry="2026-08-24", pnl=-4.1, move=-3.9):
    return {"signal": SIG, "entry": entry, "side": "long", "market": "spot", "expo": 1.0, "entry_px": 77811.73,
            "exit": exit_, "exit_px": exit_px, "reason": reason, "move_pct": move, "pnl_pct": pnl}


def cur(status, date="2026-08-24", trades=(), **kw):
    c = {"date": date, "week": "2026-08-23", "price": 77000.0, "regime": "long", "ema21": 74000.0, "flow": 0.4,
         "f1_ok": True, "chart": {"c": [77000.0]}, "capital": 50000.0, "atr_w": 2800.0, "status": status,
         "history": {"trades": list(trades)}, "fund7": 0.0001}
    if status in ("segnale", "aperto", "uscita"):
        c.update(side="long", signal_date=SIG)
    if status == "segnale":
        c["plan"] = plan()
    if status in ("aperto", "uscita"):
        c.update(entry="2026-08-24", entry_px=77811.73, market="spot", expo=1.0, stop0=70000.0, trail=70000.0,
                 best=77000.0, move_pct=-1.0, pnl_pct=-1.0, notional=50000.0, btc=0.6426, dist_now=False)
    if status == "uscita":
        c.update(reason="ema", exit_date="2026-11-08")
    c.update(kw)
    return c


class Sender:
    """telegram.send finto: restituisce un message_id (o False se `fail`), registra i testi."""
    def __init__(self, fail=False):
        self.fail, self.texts = fail, []

    def __call__(self, text):
        self.texts.append(text)
        return False if self.fail else 1000 + len(self.texts)


class TestMarkOnlyIfSent(unittest.TestCase):
    def test_invio_fallito_si_riprova(self):
        c = cur("segnale")
        sent, st = weekly.send_events(c, {}, Sender(fail=True))
        self.assertEqual(sent, [])
        self.assertNotIn(SIG, st["notified"])                     # non marcato: si riprova
        s = Sender()
        sent, st = weekly.send_events(c, st, s)
        self.assertEqual([e["type"] for e in sent], ["w_signal"])
        self.assertIn(SIG, st["notified"])
        self.assertEqual(st["pending_signal"], SIG)
        sent, st = weekly.send_events(c, st, s)                    # già inviato: niente duplicati
        self.assertEqual(sent, [])

    def test_eccezione_in_send_non_marca(self):
        def boom(_):
            raise RuntimeError("rete")
        sent, st = weekly.send_events(cur("segnale"), {}, boom)
        self.assertEqual(sent, [])
        self.assertNotIn(SIG, st["notified"])

    def test_cli_weekly_alerts_e_stop_orario(self):
        from radar import cli
        c = cur("aperto", trades=[trade()])
        st = {"weekly": {"notified": [SIG], "entered": [SIG], "exit_announced": [], "exit_done": [],
                         "trail_notified": 70000.0, "trail_sig": SIG}}
        h = pd.DataFrame({"open": [71000.0], "high": [71000.0], "low": [69900.0], "close": [69950.0]})
        cli.weekly_alerts(c, st, Sender(fail=True), h=h)
        self.assertEqual(st.get("weekly_intraday_keys", []), [])  # allerta non confermata: chiave non salvata
        s = Sender()
        cli.weekly_alerts(c, st, s, h=h)
        self.assertEqual(len(st["weekly_intraday_keys"]), 1)
        self.assertIn("stop toccato", s.texts[-1])

    def test_telegram_send_restituisce_message_id(self):
        from radar import telegram
        resp = mock.Mock(ok=True, status_code=200)
        resp.json.return_value = {"ok": True, "result": {"message_id": 4242}}
        env = {"TELEGRAM_BOT_TOKEN": "x", "TELEGRAM_CHAT_ID": "y"}
        with mock.patch.dict("os.environ", env), mock.patch.object(telegram.requests, "post", return_value=resp), \
                mock.patch("builtins.print") as pr:
            self.assertEqual(telegram.send("ciao"), 4242)
            self.assertIn("[telegram] ok id=4242", pr.call_args[0][0])
        bad = mock.Mock(ok=False, status_code=400, text="Bad Request")
        with mock.patch.dict("os.environ", env), mock.patch.object(telegram.requests, "post", return_value=bad), \
                mock.patch("builtins.print"):
            self.assertFalse(telegram.send("ciao"))
        with mock.patch.dict("os.environ", env), mock.patch("builtins.print"), \
                mock.patch.object(telegram.requests, "post", side_effect=telegram.requests.ConnectionError("x")):
            self.assertFalse(telegram.send("ciao"))


class TestAnnouncedVsExecuted(unittest.TestCase):
    def test_uscita_annunciata_poi_eseguita(self):
        s = Sender()
        st = {"notified": [SIG], "entered": [SIG], "exit_announced": [], "exit_done": []}
        sent, st = weekly.send_events(cur("uscita", date="2026-11-08", trades=[trade()]), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_exit_next"])
        closed = trade("2026-11-09", 74776.59, "ema")
        sent, st = weekly.send_events(cur("nessuno", date="2026-11-09", trades=[closed]), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_exit"])   # conferma con prezzo reale e risultato
        self.assertIn("$74.777", s.texts[-1])
        self.assertIn("-4.10%", s.texts[-1])
        self.assertIn("ESEGUITA", s.texts[-1])
        self.assertIsNone(st["pending_exit"])
        self.assertEqual(weekly.send_events(cur("nessuno", date="2026-11-10", trades=[closed]), st, s)[0], [])

    def test_migrazione_vecchio_stato(self):
        """Stato reale del 10/11/2026: "exits" conteneva già il segnale (uscita solo annunciata): la conferma parte."""
        old = {"notified": [SIG], "exits": [SIG], "trail_notified": 71330.98, "status": "nessuno", "date": "2026-11-10"}
        closed = trade("2026-11-09", 74776.59, "ema")
        sent, st = weekly.send_events(cur("nessuno", date="2026-11-10", trades=[closed]), old, Sender())
        self.assertEqual([e["type"] for e in sent], ["w_exit"])
        self.assertIn(SIG, st["exit_done"])

    def test_uscita_vecchia_senza_messaggio(self):
        closed = trade("2026-09-01", 74776.59, "ema")
        st = {"notified": [SIG], "entered": [SIG], "exit_announced": [], "exit_done": []}
        sent, st = weekly.send_events(cur("nessuno", date="2026-11-10", trades=[closed]), st, Sender())
        self.assertEqual(sent, [])
        self.assertIn(SIG, st["exit_done"])

    def test_segnale_poi_ingresso_eseguito(self):
        s = Sender()
        sent, st = weekly.send_events(cur("segnale", date="2026-08-23"), {}, s)
        self.assertEqual([e["type"] for e in sent], ["w_signal"])
        sent, st = weekly.send_events(cur("aperto", date="2026-08-24", trades=[trade()]), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_entry"])
        self.assertIn("INGRESSO SETTIMANALE ESEGUITO", s.texts[-1])
        self.assertIn("$77.812", s.texts[-1])
        self.assertIsNone(st["pending_signal"])
        self.assertEqual(weekly.send_events(cur("aperto", date="2026-08-25", trades=[trade()]), st, s)[0], [])


class TestTrail(unittest.TestCase):
    def base(self):
        return {"notified": [SIG], "entered": [SIG], "exit_announced": [], "exit_done": [],
                "trail_notified": 70000.0, "trail_sig": SIG}

    def test_soglia_mezzo_percento(self):
        c = cur("aperto", trades=[trade()], price=80000.0, trail=70300.0)   # +300 < 0,5% di 80.000 = 400
        self.assertEqual(weekly.send_events(c, self.base(), Sender())[0], [])
        c = cur("aperto", trades=[trade()], price=80000.0, trail=70400.0)
        sent, st = weekly.send_events(c, self.base(), Sender())
        self.assertEqual([e["type"] for e in sent], ["w_trail"])
        self.assertEqual(st["trail_notified"], 70400.0)

    def test_stop_orario_sul_livello_piu_alto(self):
        c = cur("aperto", trades=[trade()], trail=70000.0)
        h = pd.DataFrame({"open": [72000.0], "high": [72000.0], "low": [70800.0], "close": [70900.0]})
        self.assertEqual(weekly.check_intraday(c, [], h)[0], [])               # modello 70.000: non toccato
        ev, keys = weekly.check_intraday(c, [], h, told=71000.0)              # comunicato 71.000 (più alto): toccato
        self.assertEqual(ev[0]["level"], 71000.0)
        self.assertIn("stop comunicato $71.000", weekly.format_intraday(ev))
        ev, _ = weekly.check_intraday(c, [], h.assign(low=69000.0), told=69500.0)   # modello più alto del comunicato
        self.assertEqual(ev[0]["level"], 70000.0)
        self.assertIn("stop del modello $70.000", weekly.format_intraday(ev))
        self.assertIsNone(weekly.told_level({"trail_notified": 1.0, "trail_sig": "altro"}, c))
        self.assertEqual(weekly.told_level(self.base(), c), 70000.0)


class TestRetract(unittest.TestCase):
    def test_segnale_ritirato(self):
        s = Sender()
        _, st = weekly.send_events(cur("segnale", date="2026-08-23"), {}, s)
        sent, st = weekly.send_events(cur("nessuno", date="2026-08-23", regime="neutro", flow=-0.2), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_retract"])
        self.assertIn("SEGNALE SETTIMANALE RITIRATO", s.texts[-1])
        self.assertIn("flusso perp ora -0.20σ", s.texts[-1])
        self.assertIsNone(st["pending_signal"])
        self.assertNotIn(SIG, st["notified"])
        self.assertEqual(weekly.send_events(cur("nessuno", date="2026-08-24"), st, s)[0], [])

    def test_ritiro_fallito_si_riprova(self):
        _, st = weekly.send_events(cur("segnale", date="2026-08-23"), {}, Sender())
        sent, st = weekly.send_events(cur("nessuno", date="2026-08-23"), st, Sender(fail=True))
        self.assertEqual(st["pending_signal"], SIG)
        sent, st = weekly.send_events(cur("nessuno", date="2026-08-23"), st, Sender())
        self.assertEqual([e["type"] for e in sent], ["w_retract"])

    def test_uscita_ritirata(self):
        s = Sender()
        st = {"notified": [SIG], "entered": [SIG], "exit_announced": [], "exit_done": [],
              "trail_notified": 70000.0, "trail_sig": SIG}
        _, st = weekly.send_events(cur("uscita", date="2026-11-08", trades=[trade()]), st, s)
        sent, st = weekly.send_events(cur("aperto", date="2026-11-08", trades=[trade()]), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_retract"])
        self.assertIn("USCITA SETTIMANALE RITIRATA", s.texts[-1])
        self.assertNotIn(SIG, st["exit_announced"])


class TestHeartbeatAndStale(unittest.TestCase):
    def test_heartbeat_una_volta_dopo_le_7(self):
        from radar import cli
        s, st = Sender(), {}
        early, t1, t2 = pd.Timestamp("2026-11-11 06:07"), pd.Timestamp("2026-11-11 07:07"), pd.Timestamp("2026-11-11 08:07")
        with mock.patch.dict("os.environ", {"RADAR_HEARTBEAT": "1"}):
            self.assertFalse(cli.heartbeat(cur("nessuno", regime="neutro"), st, early, "2026-11-10", [], s))
            self.assertFalse(cli.heartbeat(cur("nessuno"), st, t1, "2026-11-10", [], Sender(fail=True)))
            self.assertNotIn("heartbeat", st)                                    # invio fallito: si riprova
            self.assertTrue(cli.heartbeat(cur("nessuno", regime="neutro"), st, t1, "2026-11-10", [], s))
            self.assertFalse(cli.heartbeat(cur("nessuno"), st, t2, "2026-11-10", [], s))   # già inviato oggi
        self.assertEqual(len(s.texts), 1)
        self.assertIn("Radar · tutto ok: dati fino al 2026-11-10, ultimo giro 11/11 07:07 UTC", s.texts[0])
        self.assertIn("prossima decisione 2026-11-15", s.texts[0])
        self.assertIn("attenzione", weekly.format_heartbeat(None, "2026-11-08", "x", ["dati spot vecchi"], "2026-11-11"))
        self.assertEqual(weekly.next_decision("2026-11-15"), "2026-11-15")      # domenica: decisione stasera

    def test_dati_vecchi_36_ore(self):
        from radar.data import stale_sources
        d = {k: pd.DataFrame({"x": [1.0]}, index=pd.DatetimeIndex([pd.Timestamp("2026-11-09")])) for k in
             ("spot", "perp", "funding", "metrics")}
        # candela del 09/11 chiusa il 10/11 00:00: alle 11:00 dell'11/11 sono 35 ore, alle 13:00 37 ore
        self.assertEqual(stale_sources(d, pd.Timestamp("2026-11-11 11:00")), {})
        self.assertEqual(set(stale_sources(d, pd.Timestamp("2026-11-11 13:00"))), {"spot", "perp", "funding", "metrics"})

    def test_avvisi_fonti_una_volta_al_giorno(self):
        from radar import cli
        s, st, now = Sender(), {}, pd.Timestamp("2026-11-11 10:00")
        cli.source_alerts({"perp": "HTTPError", "fng": "Timeout"}, {"spot": "2026-11-08"}, st, now, "2026-11-08", s)
        self.assertEqual(len(s.texts), 2)
        self.assertIn("fonte perp non disponibile", s.texts[0])
        self.assertNotIn("fng", s.texts[0])                                     # fonte non W3: nessun avviso
        self.assertIn("W3 valutato sui dati fino al 2026-11-08", s.texts[1])
        cli.source_alerts({"perp": "HTTPError"}, {"spot": "2026-11-08"}, st, now, "2026-11-08", s)
        self.assertEqual(len(s.texts), 2)


class TestUpdateAllIsolation(unittest.TestCase):
    def frame(self, col="close"):
        return pd.DataFrame({col: [1.0]}, index=pd.DatetimeIndex([pd.Timestamp("2026-11-10")], name="date"))

    def patched(self, fails, cache=None):
        from radar import data
        names = ["spot", "spot_1h", "perp", "funding", "metrics", "fng", "taker_1h"]

        def fn(n):
            def f():
                if n in fails:
                    raise RuntimeError(f"{n} rotta")
                return self.frame("fng" if n == "fng" else "close")
            return f
        ps = [mock.patch.object(data, f"fetch_{n}", fn(n)) for n in names]
        ps.append(mock.patch.object(data, "_cached", lambda n: (cache or {}).get(n)))
        ps.append(mock.patch("builtins.print"))
        return ps

    def run_with(self, fails, cache=None):
        from radar import data
        errors = {}
        ps = self.patched(fails, cache)
        for p in ps:
            p.start()
        try:
            return data.update_all(errors=errors), errors
        finally:
            for p in ps:
                p.stop()

    def test_fonte_accessoria_rotta(self):
        out, err = self.run_with({"fng", "taker_1h"})
        self.assertEqual(set(err), {"fng", "taker_1h"})
        self.assertEqual(len(out["spot"]), 1)
        self.assertIn("fng", out["fng"].columns)                               # tabella vuota, niente dati inventati
        self.assertEqual(len(out["fng"]), 0)

    def test_fonte_w3_rotta_usa_la_cache(self):
        out, err = self.run_with({"perp"}, cache={"perp": self.frame()})
        self.assertIn("perp", err)
        self.assertEqual(len(out["perp"]), 1)
        with self.assertRaises(RuntimeError):                                   # niente dati né cache: si ferma
            self.run_with({"perp"})


class TestCorrezioniF3(unittest.TestCase):
    def test_b1_uscita_nessuna_allerta_stop(self):
        c = cur("uscita", date="2026-11-08", trades=[trade()])
        h = pd.DataFrame({"open": [74700.0], "high": [74800.0], "low": [69000.0], "close": [69500.0]})   # sotto il trailing
        self.assertEqual(weekly.check_intraday(c, [], h), ([], []))
        self.assertEqual(weekly.check_intraday(c, [], h, told=70000.0), ([], []))
        self.assertEqual(len(weekly.check_intraday(cur("aperto", trades=[trade()]), [], h)[0]), 1)   # aperto: invariato

    def test_b3_variabili_tolleranti(self):
        cases = {"0,5": 0.5, " 0.5 ": 0.5, "": 1.0, "   ": 1.0, "abc": 1.0, "-1": 1.0, "1": 1.0}
        for raw, exp in cases.items():
            with mock.patch.dict("os.environ", {"RADAR_WEEKLY_SHARE": raw}), mock.patch("builtins.print"):
                self.assertEqual(weekly._env_float("RADAR_WEEKLY_SHARE", 1.0), exp, raw)
        for raw, exp in {"50000,5": 50000.5, "50.000,5": 50000.5, "": 50000.0, "x": 50000.0}.items():
            with mock.patch.dict("os.environ", {"RADAR_CAPITAL": raw}), mock.patch("builtins.print"):
                self.assertEqual(weekly._env_float("RADAR_CAPITAL", 50000.0), exp, raw)
        import importlib
        try:
            with mock.patch.dict("os.environ", {"RADAR_WEEKLY_SHARE": "0,5", "RADAR_CAPITAL": ""}), \
                    mock.patch("builtins.print") as pr:
                importlib.reload(weekly)                                    # prima: ValueError all'import
                self.assertEqual((weekly.SHARE, weekly.CAPITAL), (0.5, 50000.0))
            with mock.patch.dict("os.environ", {"RADAR_WEEKLY_SHARE": "mezzo"}), mock.patch("builtins.print") as pr:
                importlib.reload(weekly)
                self.assertEqual(weekly.SHARE, 1.0)
                self.assertIn("RADAR_WEEKLY_SHARE", pr.call_args[0][0])     # messaggio nel log
        finally:
            importlib.reload(weekly)

    def test_b2_stato_perso_con_posizione_aperta(self):
        c = cur("aperto", date="2026-11-05", trades=[trade()])
        s = Sender(fail=True)
        sent, st = weekly.send_events(c, None, s)
        self.assertEqual(sent, [])
        self.assertNotIn("Da oggi il tool segue", s.texts[0])
        self.assertIn("Stato degli avvisi ripristinato", s.texts[0])
        self.assertIn("long aperto, stop $70.000", s.texts[0])
        s = Sender()
        sent, st = weekly.send_events(c, st, s)                             # invio fallito: l'avviso si ripropone
        self.assertEqual([e["type"] for e in sent], ["w_restore"])
        self.assertEqual(weekly.send_events(c, st, s)[0], [])
        # il giorno dopo l'uscita EMA arriva normalmente
        closed = trade("2026-11-09", 74776.59, "ema")
        sent, st = weekly.send_events(cur("nessuno", date="2026-11-09", trades=[closed]), st, s)
        self.assertEqual([e["type"] for e in sent], ["w_exit"])

    def test_b2_stato_perso_eventi_recenti(self):
        s = Sender()
        sent, st = weekly.send_events(cur("uscita", date="2026-11-08", trades=[trade()]), None, s)
        self.assertEqual([e["type"] for e in sent], ["w_restore", "w_exit_next"])
        recent = trade(entry="2026-11-03")                                  # ingresso di 5 giorni prima: si comunica
        sent, _ = weekly.send_events(cur("aperto", date="2026-11-08", trades=[recent], entry="2026-11-03"), None, Sender())
        self.assertEqual([e["type"] for e in sent], ["w_restore", "w_entry"])
        ev, _ = weekly.diff_events(cur("aperto", date="2026-10-30", trades=[trade()]), None)   # primo avvio vero
        self.assertEqual([e["type"] for e in ev], ["w_info"])

    def test_b12_stop_giorno_ingresso_come_backtest(self):
        c = cur("segnale", date="2026-08-23")                               # stop iniziale 70.000, trail_dist 7.000
        h = pd.DataFrame({"open": [78000.0], "high": [78100.0], "low": [70800.0], "close": [70900.0]})
        ev, _ = weekly.check_intraday(c, [], h)                             # max(70.000, 78.000 − 7.000) = 71.000
        self.assertEqual(ev[0]["level"], 71000.0)
        self.assertEqual(weekly.check_intraday(c, [], h.assign(open=76000.0))[0], [])   # 69.000 < 70.000: resta 70.000

    def test_b11_distribuzione_anteprima(self):
        txt = weekly.format_event({"type": "w_dist", "w": cur("aperto", fund7=0.001, flow=-0.3)})
        self.assertIn("anteprima", txt.lower())
        self.assertIn("se la settimana chiudesse oggi", txt)


class TestWorkflow(unittest.TestCase):
    def test_struttura(self):
        s = WF.read_text()
        self.assertIn("timeout-minutes: 20", s)
        self.assertLess(s.index("python -m radar.cli daily"), s.index("python -m radar.cli test"))
        self.assertIn("continue-on-error: true", s)
        self.assertIn("git pull --rebase", s)
        self.assertIn("for i in 1 2 3", s)
        self.assertIn("if: failure()", s)
        self.assertIn("workflow fallito", s)
        self.assertNotIn("set -x", s)


class TestTesti(unittest.TestCase):
    def test_numeri_w3(self):
        txt = weekly.format_event({"type": "w_signal", "w": cur("segnale")})
        self.assertIn("(W3)", txt)
        self.assertIn("13 trade dal 2021", txt)
        self.assertIn("−21%", txt)
        src = Path(weekly.__file__).read_text()
        for bad in ("42,6", "42.6", "circa 3 l'anno", "(W2)"):
            self.assertNotIn(bad, src)




class TestCapitaleMigliaia(unittest.TestCase):
    def test_punto_migliaia(self):
        import os
        from unittest import mock
        from radar import weekly
        for raw, exp in [("50.000", 50000.0), ("1.250.000", 1250000.0), ("0.5", 0.5), ("50000", 50000.0), ("50.000,5", 50000.5)]:
            with mock.patch.dict(os.environ, {"X_TEST": raw}):
                self.assertEqual(weekly._env_float("X_TEST", 1.0), exp, raw)

if __name__ == "__main__":
    unittest.main()
