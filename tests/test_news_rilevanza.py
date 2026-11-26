"""Sezione Notizie "per noi" (radar/news.py, dashboard_template.html): filtro di rilevanza, gruppi per tema, doppioni, eventi
fino alla chiusura della domenica (Python e la stessa regola nel browser, via node), degrado quando una fonte non risponde.
Niente rete."""
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from radar import news as N

T = (Path(__file__).resolve().parents[1] / "radar" / "dashboard_template.html").read_text()
NODE = shutil.which("node")
NOW = datetime(2026, 11, 25, 16, 30, tzinfo=timezone.utc)   # mercoledì


def it(title, source="CoinDesk", hours=1, summary=""):
    return {"source": source, "title": title, "link": "https://x/" + title[:20], "summary": summary,
            "date": (NOW - timedelta(hours=hours)).isoformat()}


class Rilevanza(unittest.TestCase):
    def test_asset_seguiti_e_tema(self):
        x = N.classify(it("Bitcoin ETFs near $5B in record monthly outflows"))
        self.assertEqual(x["assets"], ["BTC"])
        self.assertEqual(x["theme"], "etf")
        self.assertEqual(x["group"], "noi")
        self.assertEqual(x["rel"], 3 + 2 + 2)          # BTC nel titolo, ETF, "record outflows" parola forte
        self.assertTrue(any("BTC nel titolo" in w for w in x["why"]))
        for t, a in (("Tron (TRX) burns record fees", "TRX"), ("Solana validators vote on fees", "SOL"), ("Bittensor TAO halving nears", "TAO")):
            self.assertIn(a, N.classify(it(t))["assets"])

    def test_macro_conta_anche_senza_asset(self):
        x = N.classify(it("Fed's preferred inflation gauge lands with a December rate increase priced in"))
        self.assertEqual((x["theme"], x["group"]), ("macro", "noi"))
        self.assertEqual(N.classify(it("Gli USA propongono nuovi dazi nel 2026"))["group"], "noi")

    def test_fuori_tema(self):
        self.assertEqual(N.classify(it("XRP Could Drop to $0.80 Before November Ends"))["reason"], "altcoin minore")
        self.assertEqual(N.classify(it("HYPE drops 8% as Trump bump gives way to 40% slide"))["group"], "altre")
        self.assertEqual(N.classify(it("Take-Two Hits GTA 6 PC Port With DMCA"))["group"], "via")
        self.assertEqual(N.classify(it("Top 5 altcoins: price prediction for the next 100x"))["group"], "via")
        # parola comune scritta in minuscolo non è un altcoin ("near"), la sigla in maiuscolo sì
        self.assertNotIn("reason", N.classify(it("Bitcoin ETFs near record outflows")))

    def test_attacco_solo_se_tocca_un_grande_exchange(self):
        self.assertEqual(N.classify(it("Bithumb exchange hacked, withdrawals halted"))["group"], "noi")
        self.assertEqual(N.classify(it("Small DeFi protocol drained in exploit"))["group"], "altre")

    def test_sotto_soglia_resta_fra_le_altre(self):
        x = N.classify(it("Square's Bitcoin payments rollout: what people buy"))
        self.assertLess(x["rel"], N.SOGLIA)
        self.assertEqual(x["group"], "altre")


class Doppioni(unittest.TestCase):
    def test_stessa_notizia_da_piu_testate(self):
        raw = [it("Ukraine passes crypto market law, with $332 million revenue target", "The Block", 1),
               it("Ukraine Passes Law to Legalize and Tax Its Crypto Market From July 2027", "Decrypt", 2),
               it("Ukraine passes bill to legalize crypto and tax profits at 23%", "Cointelegraph", 3),
               it("Bitcoin price slumps below $57,500 as Nasdaq sinks", "Bitcoin Magazine", 2)]
        out = N.select(raw, now=NOW)
        self.assertEqual(len(out), 2)
        u = next(x for x in out if "Ukraine" in x["title"])
        self.assertEqual(u["source"], "The Block")                 # resta la più recente
        self.assertEqual(sorted(u["also"]), ["Cointelegraph", "Decrypt"])

    def test_notizie_diverse_non_si_uniscono(self):
        self.assertFalse(N.same_story("Bitcoin price slumps below $57,500 as Nasdaq sinks 4%",
                                      "Bitcoin slides toward worst month since 2022 as ETF outflows bite"))

    def test_ordine_e_eta(self):
        raw = [it("Ark sells $6.8 million in its own bitcoin ETF", hours=2), it("Fed rate decision: Powell signals hike", hours=5),
               it("Aave launches savings app", hours=1), it("Bitcoin ETFs saw record inflows", hours=200)]
        out = N.select(raw, now=NOW)
        self.assertEqual([x["group"] for x in out], ["noi", "noi", "altre"])   # "noi" prima, per punteggio
        self.assertGreaterEqual(out[0]["rel"], out[1]["rel"])
        self.assertNotIn("record inflows", " ".join(x["title"] for x in out))   # oltre 4 giorni: fuori
        self.assertTrue(all("summary" not in x for x in out))


CAL = [{"title": "Core PCE Price Index m/m", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "alto", "note": "n"},
       {"title": "CB Consumer Confidence", "country": "USD", "date": "2026-11-24T10:00:00-05:00", "impact": "medio", "note": ""},
       {"title": "Prelim GDP q/q", "country": "USD", "date": "2026-11-25T08:30:00-05:00", "impact": "alto", "note": ""},
       {"title": "Unemployment Claims", "country": "USD", "date": "2026-11-25T08:30:00-05:00", "impact": "medio", "note": ""},
       {"title": "Non-Farm Employment Change", "country": "USD", "date": "2026-12-04T08:30:00-05:00", "impact": "alto", "note": ""}]
BANKS = [{"bank": "Fed", "title": "FOMC · decisione sui tassi", "date": "2026-11-28", "time": "20:00", "impact": "alto", "note": ""},
         {"bank": "Fed", "title": "FOMC · decisione sui tassi e proiezioni", "date": "2026-12-09", "time": "20:00", "impact": "alto", "note": ""}]


class FinoAllaDomenica(unittest.TestCase):
    def test_chiusura(self):
        self.assertEqual(N.next_close(NOW).isoformat(), "2026-11-30T00:00:00+00:00")
        self.assertEqual(N.next_close(datetime(2026, 11, 29, 23, 59, tzinfo=timezone.utc)).isoformat(), "2026-11-30T00:00:00+00:00")
        self.assertEqual(N.next_close(datetime(2026, 11, 30, 0, 0, tzinfo=timezone.utc)).isoformat(), "2026-12-07T00:00:00+00:00")

    def test_eventi_in_ordine_fino_alla_chiusura(self):
        a = N.agenda(CAL, BANKS, NOW)
        names = [e["name"] for e in a["events"]]
        # da inizio giornata (ora italiana) alla chiusura: niente ieri, niente dopo domenica; a pari ora prima l'alto impatto
        self.assertEqual(names, ["PIL · trimestre", "Richieste di sussidio", "Inflazione PCE core · mese", "FOMC · decisione sui tassi"])
        self.assertEqual([e["past"] for e in a["events"]], [True, True, False, False])
        self.assertEqual(a["next_after"]["name"], "Occupazione USA (non agricola)")
        self.assertEqual(a["events"][-1]["at"], "2026-11-28T19:00:00+00:00")       # 20:00 italiane in ora solare

    def test_ora_legale_delle_banche(self):
        self.assertEqual(N.bank_at({"date": "2026-07-29", "time": "20:00"}), "2026-07-29T20:00:00+02:00")
        self.assertEqual(N.bank_at({"date": "2026-12-09", "time": "20:00"}), "2026-12-09T20:00:00+01:00")

    def test_nomi_in_italiano(self):
        self.assertEqual(N.event_name("Core PCE Price Index m/m"), "Inflazione PCE core · mese")
        self.assertEqual(N.event_name("Something New"), "Something New")
        rows = [{"title": "CPI m/m", "country": "USD", "date": "2026-12-10T08:30:00-05:00", "impact": "High"},
                {"title": "Bank Holiday", "country": "USD", "date": "2026-11-26T00:00:00-05:00", "impact": "Holiday"},
                {"title": "German ifo", "country": "EUR", "date": "2026-11-24T04:00:00-05:00", "impact": "Medium"}]
        out = N.parse_calendar(rows)
        self.assertEqual([e["name"] for e in out], ["Inflazione CPI · mese"])
        self.assertTrue(out[0]["note"])

    @unittest.skipUnless(NODE, "node non disponibile")
    def test_stessa_regola_nel_browser(self):
        js = T[T.index("// <agenda>"):T.index("// </agenda>")]
        banks = [dict(b, at=N.bank_at(b)) for b in BANKS]
        cal = [dict(c, name=N.event_name(c["title"])) for c in CAL]
        nows = [NOW, datetime(2026, 11, 24, 23, 30, tzinfo=timezone.utc), datetime(2026, 11, 29, 23, 30, tzinfo=timezone.utc),
                datetime(2026, 11, 30, 0, 0, tzinfo=timezone.utc)]
        code = js + f"""
const C = {json.dumps(cal)}, B = {json.dumps(banks)}, NS = {json.dumps([int(n.timestamp() * 1000) for n in nows])};
console.log(JSON.stringify(NS.map(n => {{ const a = agendaW(C, B, n); return {{ close: a.close, ev: a.events.map(e => [e.name, e.at, e.past]),
  after: a.next_after && a.next_after.name }}; }})));"""
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "a.js"
            p.write_text(code)
            r = subprocess.run([NODE, str(p)], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        for n, j in zip(nows, json.loads(r.stdout)):
            a = N.agenda(cal, banks, n)
            self.assertEqual(j["close"], int(datetime.fromisoformat(a["close"]).timestamp() * 1000))
            self.assertEqual(j["ev"], [[e["name"], int(datetime.fromisoformat(e["at"]).timestamp() * 1000), e["past"]] for e in a["events"]], n)
            self.assertEqual(j["after"], a["next_after"] and a["next_after"]["name"])


class Degrado(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / "news_cache.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_fonte_giu_ultimo_dato_con_avviso(self):
        good = [{"title": "CPI m/m", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "High"}]
        resp = mock.Mock(json=lambda: good, raise_for_status=lambda: None)
        with mock.patch.object(N.requests, "get", return_value=resp):
            first = N.fetch_calendar(cache=self.cache)
        self.assertTrue(first[0]["fetched"])
        self.assertNotIn("stale", first[0])
        with mock.patch.object(N.requests, "get", side_effect=OSError("giù")):
            again = N.fetch_calendar(cache=self.cache)
        self.assertEqual(again[0]["name"], "Inflazione CPI · mese")
        self.assertTrue(again[0]["stale"])
        self.assertEqual(again[0]["fetched"], first[0]["fetched"])
        self.assertFalse(N.status()["calendario"]["ok"])

    def test_senza_fonti_e_senza_cache_lista_vuota(self):
        with mock.patch.object(N, "_fetch", return_value=[]):
            self.assertEqual(N.fetch_news(cache=self.cache), [])
        self.assertFalse(self.cache.exists())
        with mock.patch.object(N.requests, "get", side_effect=OSError("giù")):
            self.assertEqual(N.fetch_calendar(cache=self.cache), [])
            self.assertEqual(N.fetch_central_banks(cache=self.cache), [])

    def test_notizie_scarse_usano_la_cache(self):
        now = datetime.now(timezone.utc)
        many = [{"source": f"S{i}", "title": f"Bitcoin story number {i} about {w}", "link": f"https://x/{i}", "summary": "",
                 "date": (now - timedelta(minutes=i)).isoformat()} for i, w in enumerate("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda".split())]
        with mock.patch.object(N, "_fetch", side_effect=lambda s, u: many if s == "CoinDesk" else []):
            ok = N.fetch_news(cache=self.cache)
        self.assertEqual(len(ok), 11)
        with mock.patch.object(N, "_fetch", side_effect=lambda s, u: many[:2] if s == "CoinDesk" else []):
            low = N.fetch_news(cache=self.cache)
        self.assertEqual(len(low), 11)
        self.assertTrue(all(x["stale"] for x in low))

    def test_pagina_mostra_aggiornamento_e_avviso(self):
        self.assertIn('id="nwSrc"', T)
        self.assertIn("Fonti aggiornate", T)
        self.assertIn("mostro l'ultimo dato salvato", T)
        self.assertIn("Riprova più tardi con il pulsante Aggiorna", T)


class Pagina(unittest.TestCase):
    def test_struttura(self):
        for s in ("Prima della decisione di domenica", "Notizie che toccano le posizioni", 'id="nwOther"', "Perché conta per noi"):
            self.assertIn(s, T)
        self.assertNotIn('<details class="calPast nwOther" id="nwOther" open', T)   # "Altre notizie" chiuse di default
        self.assertNotIn('id="newsSeg"', T)
        # Oggi: riassunto con link alla sezione Notizie, nessun pannello
        self.assertIn('location.hash = "#notizie"', T)
        self.assertIn('href="#notizie">Calendario e notizie per noi', T)


if __name__ == "__main__":
    unittest.main()
