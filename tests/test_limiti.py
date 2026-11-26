"""Allarme "fuori dal backtest" di W3.2 (radar/limiti.py): tre condizioni sul conto del modello e sulle operazioni vere,
un avviso per evento, marcatore solo a invio riuscito, HTML valido per Telegram, riga di stato della pagina Movimenti e
sezione "Reale contro modello". Niente rete: send finto."""
import tempfile
import unittest
from pathlib import Path

from radar import cli, limiti
from radar.dashboard import render
from test_telegram_formato import LIMIT, check_html, visible

ROOT = Path(__file__).resolve().parents[1]


def wcur(eq, trades=(), start="2026-10-20"):
    dates = [str(d.date()) for d in __import__("pandas").date_range(start, periods=len(eq))]
    return {"history": {"eq_dates": dates, "eq1": list(eq), "trades": list(trades)}}


def tr(sig, exit_, pnl, reason="trail", side="long"):
    return {"signal": sig, "entry": sig, "exit": exit_, "exit_px": 1.0 if exit_ else None, "reason": reason,
            "pnl_pct": pnl, "side": side}


def real(i, pnl_usd, asset="BTC"):
    return {"id": f"2026-12-0{i}-1", "strategy": "w2", "asset": asset, "side": "short", "exit": {"price": 1.0},
            "pnl_usd": pnl_usd, "entries": [{"price": 1.0, "time": "2026-12-01"}]}


class Sender:
    def __init__(self, ok=True):
        self.ok, self.msgs = ok, []

    def __call__(self, m):
        self.msgs.append(m)
        return 42 if self.ok else False


class TestCondizioni(unittest.TestCase):
    def test_limiti_ufficiali(self):
        self.assertEqual({k: limiti.LIMITS["BTC"][k] for k in ("dd_pct", "losses", "trade_pct")},
                         {"dd_pct": -21.1, "losses": 2, "trade_pct": -25.1})   # RAPPORTO-W32.md

    def test_calo_oltre_il_peggiore_storico(self):
        g = limiti.compute(wcur([1.0, 2.0, 1.6]), "BTC")        # −20%: dentro
        self.assertTrue(g["inside"])
        g = limiti.compute(wcur([1.0, 2.0, 1.57]), "BTC")       # −21,5%: fuori
        self.assertFalse(g["inside"])
        self.assertEqual(g["events"], ["dd:2026-10-21"])
        self.assertIn("−21,5%", g["why"][0])
        self.assertTrue(limiti.compute(wcur([1.0, 2.0, 1.57]), "ETH")["inside"])   # ETH: limite suo (−27,5%)

    def test_perdite_di_fila(self):
        t = [tr("2026-10-04", "2026-10-10", -3.0), tr("2026-10-18", "2026-10-25", -2.0)]
        self.assertTrue(limiti.compute(wcur([1.0], t), "BTC")["inside"])            # 2 = massimo storico: dentro
        t.append(tr("2026-11-01", "2026-11-08", -1.0))
        g = limiti.compute(wcur([1.0], t), "BTC")
        self.assertEqual(g["model"]["losses"], 3)
        self.assertEqual(g["events"], ["losses:2026-11-01"])
        t.append(tr("2026-11-15", "2026-11-22", 4.0))                                # una vincita interrompe la serie
        self.assertTrue(limiti.compute(wcur([1.0], t), "BTC")["inside"])
        old = [tr("2018-01-07", "2018-01-16", -25.1), tr("2018-04-29", "2018-05-14", -3.3), tr("2018-06-01", "2018-06-09", -1.0)]
        self.assertTrue(limiti.compute(wcur([1.0], old), "BTC")["inside"])           # serie tutta prima del vivo: non conta

    def test_singola_operazione(self):
        t = [tr("2026-11-01", "2026-11-08", -25.0)]
        self.assertTrue(limiti.compute(wcur([1.0], t), "BTC")["inside"])
        t = [tr("2026-11-01", "2026-11-08", -26.0)]
        self.assertEqual(limiti.compute(wcur([1.0], t), "BTC")["events"], ["trade:2026-11-01"])
        aperta = [tr("2026-11-15", None, -26.0, reason="open", side="short")]        # aperta, valutata alla chiusura
        g = limiti.compute(wcur([1.0], aperta), "BTC")
        self.assertEqual(g["events"], ["trade:2026-11-15"])
        self.assertIn("(aperta)", g["why"][0])

    def test_operazioni_vere(self):
        j = {"trades": [real(1, -3000), real(2, -2000), real(3, -1000)]}            # 30.000 $: tre perdite di fila
        g = limiti.compute(wcur([1.0]), "BTC", j)
        self.assertEqual(g["real"]["losses"], 3)
        self.assertIn("real_losses:2026-12-03-1", g["events"])
        g = limiti.compute(wcur([1.0]), "BTC", {"trades": [real(1, -8000)]})        # −26,7% del conto: operazione e calo
        self.assertIn("real_trade:2026-12-01-1", g["events"])
        self.assertIn("real_dd:inizio", g["events"])
        self.assertTrue(limiti.compute(wcur([1.0]), "ETH", {"trades": [real(1, -8000)]})["inside"])   # altro asset


class TestAvviso(unittest.TestCase):
    def test_un_avviso_per_evento_marcatore_solo_se_inviato(self):
        w, st = wcur([1.0, 2.0, 1.5]), {}
        ko = Sender(ok=False)
        limiti.update({"BTC": w}, st, send=ko)
        self.assertEqual(len(ko.msgs), 1)
        self.assertNotIn("sent", st["limiti"]["BTC"])                                # non confermato: si riprova
        ok = Sender()
        limiti.update({"BTC": w}, st, send=ok)
        limiti.update({"BTC": w}, st, send=ok)                                       # stesso evento: nessun doppione
        self.assertEqual(len(ok.msgs), 1)
        self.assertEqual(st["limiti"]["BTC"]["sent"], ["dd:2026-10-21"])
        w2 = wcur([1.0, 2.0, 1.5], [tr("2026-11-01", "2026-11-08", -30.0)])         # evento nuovo: un altro avviso
        limiti.update({"BTC": w2}, st, send=ok)
        self.assertEqual(len(ok.msgs), 2)
        self.assertIn("operazione peggiore del backtest", ok.msgs[1].splitlines()[0])
        self.assertEqual(limiti.update({"BTC": None, "ETH": None}, st, send=ok), {})

    def test_formato_del_bot(self):
        g = limiti.compute(wcur([1.0, 2.0, 1.5], [tr("2026-11-01", "2026-11-08", -1.0), tr("2026-11-09", "2026-11-12", -1.0),
                                                  tr("2026-11-15", "2026-11-20", -30.0)]), "BTC",
                           {"trades": [real(1, -9000)]})
        m = limiti.format_alarm(g, g["events"])
        errs, _ = check_html(m)
        self.assertEqual(errs, [])
        self.assertLess(len(m), LIMIT)
        first = m.splitlines()[0]
        self.assertTrue(first.startswith("🚨 <b>BTC · W3.2 fuori dal backtest: "), first)
        self.assertIn("calo oltre il peggiore del backtest", first)
        self.assertIn("<blockquote expandable>Non è un ordine: è il segnale che la strategia sta uscendo dai suoi limiti "
                      "storici; rivedere con calma.", m)
        self.assertIn("Limiti storici: calo −21,1% · perdite di fila 2 · peggiore operazione −25,1%", "\n".join(visible(m)))
        self.assertTrue(m.rstrip().endswith("Apri la dashboard</a>"))

    def test_riga_della_pagina(self):
        s = limiti.status({"BTC": wcur([1.0, 2.0, 1.8]), "ETH": None})
        self.assertEqual(list(s), ["BTC"])
        self.assertTrue(s["BTC"]["line"].startswith("Dentro i limiti storici · calo −10,0% (limite −21,1%)"))
        s = limiti.status({"BTC": wcur([1.0, 2.0, 1.5])})
        self.assertTrue(s["BTC"]["line"].startswith("Fuori: Calo del conto del modello"))

    def test_aggancio_nel_giro(self):
        src = (ROOT / "radar" / "cli.py").read_text()
        self.assertRegex(src, r'_soft\("limiti del backtest", lambda: _im\("\.limiti", __package__\)\.update\(\{"BTC": wcur, "ETH": ecur\}, st, journal\.load\(\)\)\)')
        self.assertIn('("limiti", limiti_out)', src)
        self.assertTrue(callable(cli._soft))


class TestPagina(unittest.TestCase):
    def _render(self, rep):
        out = Path(tempfile.mkdtemp()) / "index.html"
        render(rep, out, standalone=False)
        return out.read_text()

    def test_sezione_reale_contro_modello(self):
        T = (ROOT / "radar" / "dashboard_template.html").read_text()
        mov = T[T.index('<div class="view" id="v-movimenti"'):T.index('<div class="view" id="v-notizie"')]
        self.assertIn('id="rvmSec"', mov)
        self.assertLess(mov.index('id="rvmSec"'), mov.index('id="wkStatSec"'))   # in testa a Movimenti
        js = T[T.index("(function renderRvm()"):T.index("// ---- Posizioni · \"Ciclo on-chain\"")]
        for w in ("Nessuna operazione vera registrata.", "/entrato 65150 0,45 btc comm 14,7", "/uscito 59800 btc comm 13,5",
                  "/registro", "Dentro i limiti storici", "Fuori dai limiti storici", "Totale: l'esecuzione reale ha"):
            self.assertIn(w, js)

    def test_dati_nella_pagina(self):
        j = {"trades": [], "avg": {}}
        h = self._render({"date": "2026-11-26", "weekly": wcur([1.0, 2.0, 1.5]), "journal": j})
        self.assertIn('"rvm": {"rows": []', h)
        self.assertIn('"limiti": {"BTC"', h)
        self.assertIn("Fuori: Calo del conto del modello", h)


if __name__ == "__main__":
    unittest.main()
