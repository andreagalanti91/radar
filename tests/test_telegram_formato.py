"""Formato dei messaggi Telegram (approvato il 25/11/2026, stato/telegram-preview/PROPOSTA.md): riga 1 con icona e azione,
numeri essenziali in vista, HTML ammesso da Telegram (tag bilanciati, solo tag della lista, escape dei valori dinamici),
lunghezza < 4096, riepilogo "Oggi" con la riga di salute, salute separata solo con problemi, avvisi sulle fonti dentro la
salute, nessun invio doppio a parità di stato. Nessuna rete: send finto."""
import re
import unittest
from html.parser import HTMLParser
from unittest import mock

import pandas as pd

from radar import cli, coherence, guard, telegram, weekly
from test_alerts import Sender, cur, trade

ALLOWED = {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "a", "code", "pre", "blockquote", "tg-spoiler", "span"}
LIMIT = 4096
DASH = '<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>'


class _Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.text = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in ALLOWED:
            self.errors.append(f"tag non ammesso <{tag}>")
        if tag == "a" and not a.get("href"):
            self.errors.append("<a> senza href")
        if tag == "blockquote" and set(a) - {"expandable"}:
            self.errors.append(f"attributi non ammessi in blockquote: {a}")
        if tag not in ("a", "blockquote") and a and not (tag in ("span", "code") and set(a) <= {"class"}):
            self.errors.append(f"attributi non ammessi in <{tag}>: {a}")
        if tag in self.stack and tag != "span":
            self.errors.append(f"<{tag}> annidato in se stesso")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"</{tag}> non bilanciato (aperti: {self.stack})")
        else:
            self.stack.pop()

    def handle_data(self, data):
        self.text.append(data)


def check_html(t: str) -> tuple[list[str], str]:
    """(errori, testo visibile). Telegram rifiuta tag fuori lista, tag non chiusi e '&' o '<' nudi."""
    p = _Check()
    p.feed(t)
    p.close()
    errs = list(p.errors) + ([f"tag non chiusi: {p.stack}"] if p.stack else [])
    if re.search(r"&(?!(lt|gt|amp|quot|#\d+);)", t):
        errs.append("& nudo (serve &amp;)")
    if re.search(r"<(?![a-z/])", t):
        errs.append("< nudo (serve &lt;)")
    return errs, "".join(p.text)


def visible(t: str) -> list[str]:
    return re.sub(r"<blockquote expandable>.*?</blockquote>", "", t, flags=re.S).splitlines()


def uscite(side="long", entry=77811.73, price=77000.0, trail=70000.0, cap=50000.0, pnl=-1.0):
    return weekly.exits_block(side, entry, price, price, trail, 2800.0, 74000.0, 1.0, cap, pnl, 0.0001, 0.4)


def eth(status, **kw):
    c = cur(status, **kw)
    c.update(asset="ETH", capital=10000.0, price=1700.0)
    c.pop("btc", None)
    if status in ("aperto", "uscita"):
        c.update(entry_px=2125.33, trail=2310.6, qty=6.9, notional=14700.0, side="short", pnl_pct=16.7, move_pct=20.7)
    return c


def all_messages() -> dict[str, str]:
    """Un testo per ogni tipo di messaggio, dalle funzioni vere."""
    w_open = cur("aperto", trades=[trade()], uscite=uscite())
    w_exit = cur("uscita")
    x_loss = trade("2026-11-09", 74776.59, "ema")
    x_win = dict(trade("2026-08-20", 73287.0, "trail", entry="2026-05-25", pnl=5.73, move=4.81), side="short")
    m = {
        "segnale": weekly.format_event({"type": "w_signal", "w": cur("segnale")}),
        "segnale_ritardo": weekly.format_event({"type": "w_signal", "w": w_open}),
        "ingresso": weekly.format_event({"type": "w_entry", "trade": trade(), "w": w_open}),
        "ingresso_chiuso": weekly.format_event({"type": "w_entry", "trade": x_loss, "w": cur("nessuno")}),
        "in_corso": weekly.format_event({"type": "w_info", "w": w_open}),
        "trailing": weekly.format_event({"type": "w_trail", "w": w_open, "old": 69000.0}),
        "distribuzione": weekly.format_event({"type": "w_dist", "w": dict(w_open, fund7=0.001, flow=-0.3)}),
        "uscita_annunciata": weekly.format_event({"type": "w_exit_next", "w": w_exit}),
        "uscita_perdita": weekly.format_event({"type": "w_exit", "trade": x_loss, "w": cur("nessuno")}),
        "uscita_profitto": weekly.format_event({"type": "w_exit", "trade": x_win, "w": cur("nessuno")}),
        "stop": weekly.format_intraday([{"level": 70000.0, "model": 70000.0, "told": None, "which": "modello", "side": "long",
                                         "asset": "BTC", "last": 69950.0, "time": "14:07 UTC"}], w_open),
        "segnale_annullato": weekly.format_event({"type": "w_retract", "kind": "signal", "w": cur("nessuno"), "key": "2026-08-23",
                                                  "side": "long", "why": "flusso <0 & regime neutro"}),
        "uscita_annullata": weekly.format_event({"type": "w_retract", "kind": "exit", "w": w_open, "key": "2026-08-23",
                                                 "side": "long", "why": "la chiusura non conferma più l'uscita"}),
        "ripristino": weekly.format_event({"type": "w_restore", "w": w_open, "last": x_loss}),
        "oggi": telegram.today_brief({"weekly": w_open, "weekly_eth": eth("aperto")}, "2026-11-25",
                                     telegram.health_line("2026-11-24", [], "2026-11-29")),
        "oggi_fuori": telegram.today_brief({"weekly": cur("nessuno", regime="neutro")}, "2026-11-25"),
        "salute_problemi": weekly.format_heartbeat(w_open, "2026-11-24", "25/11 07:10 UTC", ["fonte perp non disponibile (<html>)"],
                                                   "2026-11-25", {"ETH": eth("aperto")}),
        "salute_ok": weekly.format_heartbeat(w_open, "2026-11-24", "25/11 07:10 UTC", [], "2026-11-25", {"ETH": eth("aperto")}),
        "allarme": guard.format_alarm({"why": ["equity −16,2% dal massimo (soglia −15%)"], "since": "2026-10-31"}),
        "coerenza": coherence.format_alert(["dati spot: 2 giorni mancanti (2026-11-03, 2026-11-04)"]),
        "giro_interrotto": telegram.format_run_stopped("ConnectionError"),
        "w3_errore": telegram.format_w3_error("KeyError: '<close>' & co"),
        "test": telegram.format_test(),
    }
    return m


FIRST = {   # riga 1 attesa: icona + asset + azione (anteprima della notifica)
    "segnale": "🟢 <b>BTC · Nuovo LONG: entra lunedì all'apertura</b>",
    "segnale_ritardo": "🟢 <b>BTC · LONG già aperto dal 24/08 (segnale in ritardo)</b>",
    "ingresso": "🟢 <b>BTC · LONG aperto a $77.812</b>",
    "ingresso_chiuso": "🛑 <b>BTC · LONG aperto e già chiuso: −4,10%</b>",
    "in_corso": "🟢 <b>BTC · LONG in corso dal 24/08: non è un segnale nuovo</b>",
    "trailing": "🔔 <b>BTC · Uscita automatica alzata a $70.000</b>",
    "distribuzione": "⏳ <b>BTC · Possibile uscita dal LONG: decide domenica</b>",
    "uscita_annunciata": "🛑 <b>BTC · Chiudi il LONG lunedì all'apertura</b>",
    "uscita_perdita": "🛑 <b>BTC · LONG chiuso in perdita: −4,10%</b>",
    "uscita_profitto": "🎯 <b>BTC · SHORT chiuso in profitto: +5,73%</b>",
    "stop": "🛑 <b>BTC · Stop toccato: chiudi il LONG</b>",
    "segnale_annullato": "⚪ <b>BTC · Segnale LONG annullato: non entrare</b>",
    "uscita_annullata": "🟢 <b>BTC · Uscita annullata: tieni il LONG</b>",
    "ripristino": "⚠️ <b>BTC · Avvisi ripristinati: nessuna azione</b>",
    "oggi": "📋 <b>Oggi 25/11 · nessuna azione</b>",
    "oggi_fuori": "📋 <b>Oggi 25/11 · fuori dal mercato, nessuna azione</b>",
    "salute_problemi": "⚠️ <b>Radar · 1 problema tecnico</b>",
    "salute_ok": "✅ <b>Radar attivo · tutto ok</b>",
    "allarme": "⚠️ <b>BTC · Soglia d'allarme: rivedi la strategia</b>",
    "coerenza": "⚠️ <b>BTC · Dati da verificare prima della prossima decisione</b>",
    "giro_interrotto": "⚠️ <b>Problema tecnico: giro interrotto</b>",
    "w3_errore": "⚠️ <b>BTC · Segnale non calcolato in questo giro</b>",
    "test": "✅ <b>Radar · connessione riuscita</b>",
}
TRADING = {"segnale", "segnale_ritardo", "ingresso", "ingresso_chiuso", "in_corso", "trailing", "distribuzione",
           "uscita_annunciata", "uscita_perdita", "uscita_profitto", "stop", "segnale_annullato", "uscita_annullata",
           "ripristino", "oggi", "oggi_fuori", "allarme"}


class TestPrimaRiga(unittest.TestCase):
    def test_icona_e_azione(self):
        m = all_messages()
        self.assertEqual(set(m), set(FIRST))
        for k, t in m.items():
            first = t.split("\n")[0]
            self.assertEqual(first, FIRST[k], k)
            self.assertNotIn("RADAR SIGNAL", first, k)               # scelta 1: niente nome del bot né della strategia
            self.assertNotIn("W3.2", first, k)

    def test_link_dashboard_nei_messaggi_di_trading(self):
        for k, t in all_messages().items():
            if k in TRADING:
                self.assertEqual(t.split("\n")[-1], DASH, k)
            else:
                self.assertNotIn("Apri la dashboard", t, k)


class TestNumeri(unittest.TestCase):
    def test_numeri_essenziali(self):
        m = all_messages()
        v = {k: "\n".join(visible(t)) for k, t in m.items()}
        # segnale: entrata, importo, uscita in perdita (con la perdita stimata)
        self.assertIn("Entrata: ~<b>$77.000</b> a mercato, lun 24/08", v["segnale"])
        self.assertIn("Importo: $50.000 = 0,6500 BTC su $50.000", v["segnale"])
        self.assertIn("🛑 Uscita in perdita: $70.000 (circa −$4.700)", v["segnale"])
        # ingresso: prezzo reale, importo, risultato, uscita automatica
        self.assertIn("Importo: $50.000 = 0,6426 BTC su $50.000", v["ingresso"])
        self.assertIn("Prezzo ora: $77.000 · <b>−1,00%</b> (−$500)", v["ingresso"])
        self.assertIn("🛑 Uscita automatica: <b>$70.000</b>", v["ingresso"])
        # uscita automatica spostata: esito in $ se scatta (scelta 6), stesso dato della dashboard
        t = cur("aperto", uscite=uscite())["uscite"]["trail"]
        self.assertIn(f"🛑 Se scatta: {telegram.money(t['pct_cap'], t['usd'])}", v["trailing"])
        # stop toccato: esito al livello, calcolato come exits_block
        self.assertIn(f"Risultato a questo livello: {telegram.money(t['pct_cap'], t['usd'])}", v["stop"])
        # uscite eseguite: risultato in % sul capitale e in $
        self.assertIn("Risultato: <b>−4,10%</b> (−$2.050) del capitale", v["uscita_perdita"])
        self.assertIn("Risultato: <b>+5,73%</b> (+$2.865) del capitale", v["uscita_profitto"])
        self.assertIn("Risultato stimato: <b>−1,00%</b> (−$500)", v["uscita_annunciata"])
        # riepilogo: posizione, P&L in $ sul capitale dell'asset, uscita
        self.assertIn("🟢 <b>BTC long</b> · <b>−1,00%</b> (−$500)", v["oggi"])
        self.assertIn("🔴 <b>ETH short</b> · <b>+16,70%</b> (+$1.670)", v["oggi"])
        self.assertIn("uscita $70.000", v["oggi"])

    def test_dettagli_in_citazione_espandibile(self):
        m = all_messages()
        for k in ("segnale", "segnale_ritardo", "ingresso", "in_corso", "stop", "oggi", "allarme"):
            self.assertEqual(m[k].count("<blockquote expandable>"), 1, k)
        self.assertNotIn("Come si esce", "\n".join(visible(m["segnale"])))   # regole d'uscita solo nei dettagli
        self.assertIn("Come si esce", m["segnale"])

    def test_escape_dei_valori_dinamici(self):
        m = all_messages()
        self.assertIn("<i>flusso &lt;0 &amp; regime neutro</i>", m["segnale_annullato"])
        self.assertIn("<code>KeyError: '&lt;close&gt;' &amp; co</code>", m["w3_errore"])
        self.assertIn("• fonte perp non disponibile (&lt;html&gt;)", m["salute_problemi"])
        rep = {"macro": {"assets": [{"key": "spx", "close": 7000.0, "d1_pct": 1.0}], "flags": ["S&P 500 sotto la media"]}}
        t = telegram.today_brief(rep, "2026-11-25")
        self.assertIn("S&amp;P 500", t)
        self.assertEqual(check_html(t)[0], [])


class TestHtml(unittest.TestCase):
    def test_html_valido_e_lunghezza(self):
        for k, t in all_messages().items():
            errs, text = check_html(t)
            self.assertEqual(errs, [], f"{k}: {errs}\n{t}")
            self.assertLess(len(text), LIMIT, k)
            self.assertLess(len(t), LIMIT, k)

    def test_messaggio_piu_lungo_sotto_4096(self):
        """Caso peggiore: riepilogo con BTC ed ETH, contesto, mercati, livelli, 2 flag e una riga di salute con molti problemi."""
        from test_preview_today import PV
        pv = dict(PV, today=dict(PV["today"], items=PV["today"]["items"] + [
            {"key": "sf14z", "label": "", "value": "+0,39σ", "read": "terzile medio: spot quasi neutro", "reliability": ""},
            {"key": "oi7", "label": "", "value": "OI · +2,2%", "read": "", "reliability": ""},
            {"key": "liq24h", "label": "", "value": "long 0,0 M$ · short 0,0 M$", "read": "", "reliability": ""}]))
        macro = {"assets": [{"key": k, "close": 1234.5, "d1_pct": -1.0} for k in ("spx", "ndx", "gold", "usd", "vix")],
                 "flags": ["S&P 500 sotto la media a 200 giorni", "oro e dollaro divergono da 20 giorni"]}
        probs = [f"fonte fonte_{i} non disponibile (HTTPError: 503 Server Error: Service Unavailable for url)" for i in range(12)]
        t = telegram.today_brief({"preview": pv, "weekly": cur("aperto"), "weekly_eth": eth("aperto"), "macro": macro},
                                 "2026-11-25", telegram.health_line("2026-11-24", probs, "2026-11-29"))
        hb = weekly.format_heartbeat(cur("aperto"), "2026-11-24", "x", probs, "2026-11-25", {"ETH": eth("aperto")}, "nota")
        longest = max(list(all_messages().values()) + [t, hb], key=len)
        self.assertLess(len(longest), LIMIT)
        self.assertEqual(check_html(t)[0], [])
        self.assertEqual(check_html(hb)[0], [])


class TestSalute(unittest.TestCase):
    T7 = pd.Timestamp("2026-11-25 07:10")

    def setUp(self):
        p = mock.patch.dict("os.environ", {"RADAR_DAILY_BRIEF": "1", "RADAR_HEARTBEAT": "1"})
        p.start()
        self.addCleanup(p.stop)

    def test_salute_ok_accorpata_nel_riepilogo(self):
        st, s = {}, Sender()
        hl = cli.health("2026-11-24", [], self.T7)
        self.assertEqual(hl, "✅ Sistema ok · dati fino al 24/11 · decisione dom 29/11")
        self.assertTrue(cli.daily_brief({"weekly": cur("aperto")}, st, pd.Timestamp("2026-11-25 00:20"), "2026-11-24", s, health=hl))
        self.assertEqual(s.texts[0].split("\n")[-2], hl)                       # riga di salute in fondo, prima del link
        self.assertFalse(cli.heartbeat(cur("aperto"), st, self.T7, "2026-11-24", [], s))
        self.assertEqual(len(s.texts), 1)                                     # tutto ok: un solo messaggio al giorno
        self.assertEqual(st["heartbeat"], "2026-11-25")

    def test_salute_separata_con_problemi(self):
        st, s = {}, Sender()
        self.assertTrue(cli.heartbeat(cur("aperto"), st, self.T7, "2026-11-24", ["W3.2 ETH non calcolato"], s))
        self.assertTrue(s.texts[0].startswith("⚠️ <b>Radar · 1 problema tecnico</b>\n• W3.2 ETH non calcolato"))
        self.assertIn("⚠️ 1 problema tecnico: W3.2 ETH non calcolato", cli.health("2026-11-24", ["W3.2 ETH non calcolato"], self.T7))

    def test_avvisi_fonti_dentro_la_salute(self):
        st, s = {}, Sender()
        nw = pd.Timestamp("2026-11-25 03:10")
        errors, stale = {"perp": "HTTPError 503", "eth_funding": "Timeout"}, {"eth_spot": "2026-11-22"}
        self.assertTrue(cli.heartbeat(cur("aperto"), st, nw, "2026-11-24", [], s, others={"ETH": eth("aperto")},
                                      errors=errors, stale=stale))
        self.assertEqual(len(s.texts), 1)                                     # un solo messaggio, non tre
        t = s.texts[0]
        self.assertTrue(t.startswith("⚠️ <b>Radar · 3 problemi tecnici</b>"))
        for line in ("• fonte perp non disponibile (HTTPError 503)", "• fonte ETH funding non disponibile (Timeout)",
                     "• dati ETH spot vecchi (ultimo giorno 22/11)",
                     "Segnali calcolati sui dati fino al 24/11: decisioni possibili in ritardo.",
                     "🟢 BTC long · 🔴 ETH short · prossima decisione dom 29/11"):
            self.assertIn(line, t)
        self.assertFalse(hasattr(cli, "source_alerts"))                       # nessun avviso separato sulle fonti

    def test_nessun_invio_doppio_a_parita_di_stato(self):
        st, s = {}, Sender()
        errors, stale, pr = {"perp": "HTTPError"}, {"spot": "2026-11-22"}, ["W3.2 ETH non calcolato"]
        for h in range(0, 24):                                                # tutti i giri orari di un giorno
            now = pd.Timestamp("2026-11-25") + pd.Timedelta(hours=h, minutes=7)
            cli.heartbeat(cur("aperto"), st, now, "2026-11-24", pr, s, errors=errors, stale=stale)
            cli.daily_brief({"weekly": cur("aperto")}, st, now, "2026-11-24", s, health=cli.health("2026-11-24", pr, now,
                                                                                                    errors, stale))
        heads = [t.split("\n")[0] for t in s.texts]
        # 00:07 salute per le fonti (come gli avvisi sulle fonti di prima) + riepilogo; 07:07 controllo quotidiano con problemi
        self.assertEqual(heads.count("📋 <b>Oggi 25/11 · nessuna azione</b>"), 1)
        self.assertEqual(heads.count("⚠️ <b>Radar · 3 problemi tecnici</b>"), 2)
        self.assertEqual(len(s.texts), 3)
        n = len(s.texts)
        cli.heartbeat(cur("aperto"), st, pd.Timestamp("2026-11-25 23:59"), "2026-11-24", pr, s, errors=errors, stale=stale)
        self.assertEqual(len(s.texts), n)

    def test_eventi_w3_nessun_doppio(self):
        s = Sender()
        c = cur("aperto", trades=[trade()], uscite=uscite())
        sent, st = weekly.send_events(cur("segnale", date="2026-08-23"), {}, s)
        sent, st = weekly.send_events(c, st, s)
        n = len(s.texts)
        for _ in range(3):
            self.assertEqual(weekly.send_events(c, st, s)[0], [])
        self.assertEqual(len(s.texts), n)


if __name__ == "__main__":
    unittest.main()
