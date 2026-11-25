"""Pagina Scanner (radar/scanner.py): TRX sulla carta con il cancello di BTC e scanner settimanale di W3.2. Niente rete: serie
sintetiche servite da una rete finta (stessi formati di data-api.binance.vision, data.binance.vision e OKX) e i file dello studio
w32_asset2 già nel repository (estratto reale). Coperti: stato W3.2 e cancello, riproduzione di Q4 su TRX (87.198 $), registro in
avanti, degrado su errore di rete, ricalcolo solo a settimana nuova, pagina e menu della dashboard."""
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from radar import scanner as SC
from radar import weekly as W

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "research" / "w32_asset2" / "crypto" / "data"
UTC = timezone.utc


def serie(n=1100, end="2026-11-22", drift=1.0, seed=1, p0=10.0):
    """Spot sintetico giornaliero: trend accelerato (MACD che sale) con poco rumore; taker buy che cresce (flusso perp positivo)
    se drift > 0, che cala se drift < 0."""
    idx = pd.date_range(end=end, periods=n, freq="D")
    t = np.arange(n) / n
    rng = np.random.default_rng(seed)
    lp = np.log(p0) + drift * (0.4 * t + 1.6 * t ** 2) + rng.normal(0, 0.004, n).cumsum() * 0.2
    c = np.exp(lp)
    o = np.r_[c[0], c[:-1]]
    h, lo = np.maximum(o, c) * 1.01, np.minimum(o, c) * 0.99
    vol = np.full(n, 1000.0)
    share = 0.5 + 0.08 * drift * t + rng.normal(0, 0.003, n)
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": vol, "tbv": vol * share}, index=idx)


def zip_csv(text: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.csv", text)
    return b.getvalue()


def kl_rows(df):
    ms = df.index.as_unit("ms").astype("int64")
    return [[int(m), str(r.open), str(r.high), str(r.low), str(r.close), str(r.volume), int(m) + 86399999, "0", 1, str(r.tbv), "0", "0"]
            for m, r in zip(ms, df.itertuples())]


class FakeNet:
    """Rete finta: risponde come le fonti vere a partire da tabelle {simbolo: df} (spot, perp con prezzi grezzi, funding)."""

    def __init__(self, spot, perp, fund, fail=False):
        self.spot, self.perp, self.fund, self.fail, self.calls = spot, perp, fund, fail, []

    def __call__(self, url, params=None):
        self.calls.append(url)
        if self.fail:
            raise ConnectionError("rete giù")
        path = urlparse(url).path
        if url == SC.SPOT_API:
            df = self.spot.get(params["symbol"])
            if df is None:
                return json.dumps([]).encode()
            df = df[df.index >= pd.Timestamp(params["startTime"], unit="ms")].iloc[: params["limit"]]
            return json.dumps(kl_rows(df)).encode()
        if url == SC.OKX_FUND or url == SC.BITGET_FUND:
            return json.dumps({"code": "0", "data": []}).encode()
        name = path.rsplit("/", 1)[-1][:-4]
        if "/klines/" in path:
            sym, _, per = name.split("-", 2)
            df = self.perp.get(sym)
            if df is None:
                return None
            x = df[df.index.strftime("%Y-%m-%d" if "/daily/" in path else "%Y-%m") == per]
            if not len(x):
                return None
            head = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore\n"
            return zip_csv(head + "\n".join(",".join(map(str, r)) for r in kl_rows(x)))
        if "/fundingRate/" in path:
            sym, per = name.split("-fundingRate-")
            df = self.fund.get(sym)
            x = None if df is None else df[df.index.strftime("%Y-%m") == per]
            if x is None or not len(x):
                return None
            ms = x.index.as_unit("ms").astype("int64")
            return zip_csv("calc_time,funding_interval_hours,last_funding_rate\n" + "\n".join(f"{m},8,{v}" for m, v in zip(ms, x["funding"])))
        raise AssertionError(f"url inatteso {url}")


def universo_finto():
    return [{"ticker": "BTC", "nome": "Bitcoin", "classe": "valutabile", "spot": "BTCUSDT", "perp": "BTCUSDT", "div": 1, "okx": "BTC-USDT-SWAP",
             "bitget": "BTCUSDT", "scheda": {"q1": {"c": 5}, "q4": None}},
            {"ticker": "UPX", "nome": "Su", "classe": "valutabile", "spot": "UPXUSDT", "perp": "1000UPXUSDT", "div": 1000, "okx": None,
             "bitget": "UPXUSDT", "scheda": None},
            {"ticker": "DNX", "nome": "Giù", "classe": "breve", "spot": None, "perp": "DNXUSDT", "div": 1, "okx": "DNX-USDT-SWAP", "bitget": None,
             "scheda": None}]


def rete_finta(end="2026-11-29", fail=False):
    up, dn, btc = serie(end=end, drift=1.0, seed=2, p0=0.01), serie(end=end, drift=-1.0, seed=3, p0=50.0), serie(end=end, drift=1.0, seed=4, p0=20000)
    perp_up = up.copy()
    perp_up[["open", "high", "low", "close"]] *= 1000           # 1000UPXUSDT: prezzo grezzo × 1000
    fund = {s: pd.DataFrame({"funding": 0.0001}, index=x.index) for s, x in (("BTCUSDT", btc), ("1000UPXUSDT", up), ("DNXUSDT", dn))}
    return FakeNet({"BTCUSDT": btc, "UPXUSDT": up}, {"BTCUSDT": btc, "1000UPXUSDT": perp_up, "DNXUSDT": dn}, fund, fail), up, dn


def feats_finte(df):
    return SC.feats(df, df, pd.DataFrame({"funding": 0.0001}, index=df.index))


def seed_feats(t, fine="2026-11-24"):
    """Feature dai file dello studio con la storia dal 2019-09-01 (crypto/counts.py SINCE), come trx_giro."""
    xs = (SC._seed(t, k, SEED) for k in ("spot", "perp", "funding"))
    return SC.feats(*(x[x.index >= SC.TRX_SINCE] for x in xs), fine=date.fromisoformat(fine))


class TestDate(unittest.TestCase):
    def test_ultima_domenica(self):
        self.assertEqual(SC.ultima_domenica(datetime(2026, 11, 30, 0, 5, tzinfo=UTC)), date(2026, 11, 29))   # lunedì 00:05
        self.assertEqual(SC.ultima_domenica(datetime(2026, 11, 29, 23, 0, tzinfo=UTC)), date(2026, 11, 22))  # domenica non chiusa
        self.assertEqual(SC.ultima_domenica(datetime(2026, 11, 25, 12, 0, tzinfo=UTC)), date(2026, 11, 22))


class TestStatoW32(unittest.TestCase):
    def test_trend_sintetici(self):
        up = SC.stato_moneta(feats_finte(serie(drift=1.0, seed=2)), date(2026, 11, 22))
        self.assertEqual(up["lato"], "long")
        self.assertEqual((up["cond"]["px_sma"], up["cond"]["ema20"]), (1, 1))
        self.assertGreater(up["cond"]["flow"], 0)
        self.assertGreater(up["sett"], 0)
        self.assertLess(up["trail"], up["ult"])                  # trailing sotto il prezzo per un long
        dn = SC.stato_moneta(feats_finte(serie(drift=-1.0, seed=3, p0=50.0)), date(2026, 11, 22))
        self.assertEqual(dn["lato"], "short")
        self.assertEqual(dn["cond"]["regime"], "short")
        self.assertGreater(dn["trail"], dn["ult"])

    def test_storia_insufficiente_e_dati_fermi(self):
        self.assertIsNone(SC.stato_moneta(feats_finte(serie(n=200)), date(2026, 11, 22))["lato"])
        r = SC.stato_moneta(feats_finte(serie(end="2026-11-10")), date(2026, 11, 22))
        self.assertIsNone(r["lato"])
        self.assertIn("fermi", r["nd"])
        self.assertIsNone(SC.stato_moneta(None, date(2026, 11, 22))["lato"])

    def test_estratto_reale_sol_e_trx(self):
        # studio (README w32_asset2, 25/11/2026): SOL short dal 09/11; TRX flat
        f = seed_feats("SOL")
        s = SC.stato_moneta(f[f.index >= pd.Timestamp("2026-11-24") - pd.Timedelta(days=SC.WINDOW_DAYS)], date(2026, 11, 22))
        self.assertEqual((s["lato"], s["ing"]), ("short", "2026-11-09"))
        self.assertEqual(SC.stato_moneta(seed_feats("TRX"), date(2026, 11, 22))["lato"], "flat")

    def test_verso_btc(self):
        self.assertEqual(SC._verso_btc("long", "long"), "stesso")
        self.assertEqual(SC._verso_btc("short", "long"), "opposto")
        self.assertEqual(SC._verso_btc("short", "flat"), "BTC flat")
        self.assertIsNone(SC._verso_btc("flat", "long"))


class TestCancelloTRX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fb, cls.ft = seed_feats("BTC"), seed_feats("TRX")
        cls.gate = SC.cancello(cls.fb)

    def test_cancello_btc(self):
        g = self.gate
        self.assertEqual(int(g[pd.Timestamp("2026-11-08")]), 1)     # long dal 24/08, uscita il 09/11: la domenica 08/11 conta ancora
        self.assertEqual(int(g[pd.Timestamp("2026-11-15")]), -1)    # segnale short della domenica: vi entra quel giorno
        self.assertEqual(int(g[pd.Timestamp("2026-11-22")]), -1)
        self.assertTrue(set(g.unique()) <= {-1, 0, 1})

    def test_riproduce_q4(self):
        o = SC.simula_con_cancello(self.ft, self.gate)
        self.assertEqual(round(float(o["equity"].iloc[-1])), 87198)   # OSSERVAZIONE-TRX.md: 87.198 $ da 10.000, 12 trade
        self.assertEqual(len(o["trades"]) + bool(o["open"]), 12)
        self.assertEqual(W.weekly_bars.__qualname__, "weekly_bars")   # il motore torna quello originale
        self.assertFalse(any(t["side"] == "long" and self.gate.get(pd.Timestamp(t["signal"]), 0) <= 0 for t in o["trades"]))

    def test_registro_vuoto_al_25_11(self):
        o = SC.simula_con_cancello(self.ft, self.gate)
        reg = SC.aggiorna_registro(None, o, self.ft, self.gate, datetime(2026, 11, 25, tzinfo=UTC))
        self.assertEqual(reg["operazioni"], [])                      # niente prima del 25/11/2026
        self.assertEqual(reg["capitale_ora"], 10000.0)
        st = SC.stato_trx(o, self.ft, self.gate)
        self.assertEqual((st["lato"], st["btc"]), ("flat", "short"))
        self.assertIn("perche", st)


class TestRegistro(unittest.TestCase):
    def setUp(self):
        idx = pd.date_range("2026-11-20", "2027-01-20")
        self.f = pd.DataFrame({"open": np.linspace(0.30, 0.36, len(idx)), "close": np.linspace(0.301, 0.361, len(idx))}, index=idx)
        self.gate = pd.Series(1, index=idx[idx.dayofweek == 6])
        self.now = datetime(2027, 1, 20, tzinfo=UTC)

    def o(self, aperta_pnl=0.03, chiusa_pnl=0.10):
        base = dict(signal="2026-11-29", entry="2026-11-30", side="long", expo=1.0, market="spot")
        vecchia = dict(base, signal="2026-11-15", entry="2026-11-16", exit="2026-11-23", reason="ema", pnl=0.5, stop=0.2)
        chiusa = dict(base, exit="2026-12-14", reason="trail", pnl=chiusa_pnl, stop=0.33123)
        aperta = dict(base, signal="2026-12-27", entry="2026-12-28", trail=0.34567, last=0.35912, pnl=aperta_pnl)
        return {"trades": [vecchia, chiusa], "open": aperta, "pending": None}

    def test_prezzi_capitale_e_congelamento(self):
        reg = SC.aggiorna_registro(None, self.o(), self.f, self.gate, self.now)
        ops = reg["operazioni"]
        self.assertEqual([r["ingresso"] for r in ops], ["2026-11-30", "2026-12-28"])   # quella del 16/11 è prima del 25/11
        c = ops[0]
        self.assertEqual(c["stato"], "chiusa")
        self.assertAlmostEqual(c["prezzo_in"], round(float(self.f.loc["2026-11-30", "open"]) * 1.001, 5))
        self.assertNotEqual(c["prezzo_in"], round(c["prezzo_in"], 2))                    # 5 decimali, non 0,01
        px_exit = min(float(self.f.loc["2026-12-14", "open"]), 0.33123) * 0.999         # trailing: livello dello stop, slittamento
        self.assertAlmostEqual(c["prezzo_out"], round(px_exit, 5))
        self.assertEqual(c["motivo"], W.REASONS["trail"])
        self.assertEqual(c["esito_usd"], 1000.0)
        self.assertEqual(ops[1]["stato"], "aperta")
        self.assertEqual(ops[1]["capitale_prima"], 11000.0)
        self.assertEqual(reg["capitale_ora"], 11330.0)                                   # 11.000 × 1,03
        # giro dopo: la chiusa non si riscrive, l'aperta si aggiorna
        reg2 = SC.aggiorna_registro(reg, self.o(aperta_pnl=-0.02, chiusa_pnl=0.99), self.f, self.gate, self.now)
        self.assertEqual(reg2["operazioni"][0]["pnl_pct"], 10.0)
        self.assertEqual(reg2["operazioni"][1]["pnl_pct"], -2.0)
        self.assertEqual(reg2["capitale_ora"], 10780.0)
        # l'aperta sparisce dal calcolo (dati riscritti): resta con la nota
        o3 = self.o()
        o3["open"] = None
        reg3 = SC.aggiorna_registro(reg2, o3, self.f, self.gate, self.now)
        self.assertIn("da controllare", reg3["operazioni"][1]["nota"])

    def test_build_trx(self):
        reg = SC.aggiorna_registro(None, self.o(), self.f, self.gate, self.now)
        b = SC.build_trx(reg, datetime(2026, 11, 25, tzinfo=UTC))
        self.assertEqual(b["nota"], "sulla carta: nessun capitale, nessun ordine")
        self.assertEqual(b["rif"]["fin"], 87198)
        self.assertEqual(b["rif"]["senza_due_migliori"], 17017)
        self.assertEqual([v["data"] for v in b["valutazioni"]], ["2027-05-31", "2027-11-30"])
        self.assertEqual(b["chiuse"], 1)


class TestScannerGiro(unittest.TestCase):
    def test_download_calcolo_e_ricalcolo_solo_a_settimana_nuova(self):
        net, up, dn = rete_finta(end="2026-11-29")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            lun = datetime(2026, 11, 30, 0, 30, tzinfo=UTC)
            out = SC.giro(None, d / "data", lun, net=SC.Rete(net, pausa=0), cache=d / "c", universo=universo_finto(), seed_dir=None)
            self.assertEqual(out["settimana"], "2026-11-29")
            rows = {r["t"]: r for r in out["righe"]}
            self.assertEqual(rows["UPX"]["lato"], "long")
            self.assertEqual(rows["DNX"]["lato"], "short")
            self.assertEqual(rows["UPX"]["btc"], "stesso")
            self.assertEqual(rows["DNX"]["btc"], "opposto")
            self.assertAlmostEqual(rows["UPX"]["ult"], round(float(up["close"].iloc[-1]), 6))   # prezzo spot, non il perp × 1000
            self.assertAlmostEqual(rows["DNX"]["ult"], round(float(dn["close"].iloc[-1]), 6))   # senza spot: prezzo dal perp
            self.assertEqual(out["conteggi"], {"long": 2, "short": 1, "flat": 0, "nd": 0})
            self.assertFalse(out["provvisorio"])
            pc = pd.read_csv(d / "c" / "UPX_perp.csv.gz", index_col=0, parse_dates=True)
            self.assertAlmostEqual(float(pc["volume"].iloc[-1]), 1000.0 * 1000)                # scala dello studio: volume × 1000
            self.assertAlmostEqual(float(pc["close"].iloc[-1]), float(up["close"].iloc[-1]))  # prezzo / 1000
            saved = json.loads((d / "data" / "scanner.json").read_text())
            self.assertEqual(saved["settimana"], "2026-11-29")
            self.assertLess(len((d / "data" / "scanner.json").read_bytes()), 200_000)
            # stessa settimana, ore dopo: nessuna richiesta, risultato salvato
            n0 = len(net.calls)
            again = SC.giro(None, d / "data", datetime(2026, 12, 2, 15, tzinfo=UTC), net=SC.Rete(net, pausa=0), cache=d / "c",
                            universo=universo_finto(), seed_dir=None)
            self.assertEqual(len(net.calls), n0)
            self.assertEqual(again["calcolato"], out["calcolato"])
            # settimana nuova: si ricalcola, scaricando solo i giorni mancanti
            net2, _, _ = rete_finta(end="2026-12-06")
            nxt = SC.giro(None, d / "data", datetime(2026, 12, 7, 1, tzinfo=UTC), net=SC.Rete(net2, pausa=0), cache=d / "c",
                          universo=universo_finto(), seed_dir=None)
            self.assertEqual(nxt["settimana"], "2026-12-06")
            self.assertLess(len(net2.calls), len(net.calls) / 3)

    def test_provvisorio_si_ricalcola(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "scanner.json").write_text(json.dumps({"settimana": "2026-11-29", "provvisorio": True, "righe": []}))
            net = FakeNet({}, {}, {}, fail=True)
            r = SC.giro(None, d, datetime(2026, 11, 30, 5, tzinfo=UTC), net=SC.Rete(net, pausa=0), universo=universo_finto(), cache=d / "c", seed_dir=None)
            self.assertTrue(net.calls)                               # provvisorio entro 2 giorni: si riprova
            self.assertTrue(r["dati"]["ritardo"])
            net.calls.clear()
            SC.giro(None, d, datetime(2026, 12, 3, 5, tzinfo=UTC), net=SC.Rete(net, pausa=0), universo=universo_finto(), cache=d / "c", seed_dir=None)
            self.assertFalse(net.calls)                              # oltre 2 giorni: resta com'è


class TestDegradoRete(unittest.TestCase):
    def test_scanner_rete_giu_tiene_l_ultimo(self):
        net = FakeNet({}, {}, {}, fail=True)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prev = {"settimana": "2026-11-22", "righe": [{"t": "BTC", "lato": "short"}], "conteggi": {"short": 1}, "dati": {"ritardo": False}}
            (d / "scanner.json").write_text(json.dumps(prev))
            r = SC.giro(None, d, datetime(2026, 11, 30, 1, tzinfo=UTC), net=SC.Rete(net, max_err=5, pausa=0), universo=universo_finto() * 20,
                        cache=d / "c", seed_dir=None)
            self.assertEqual(r["righe"], prev["righe"])
            self.assertTrue(r["dati"]["ritardo"])
            self.assertIn("22/11/2026", r["dati"]["nota"])
            self.assertLessEqual(len(net.calls), 2 * 5 + 2 * SC.THREADS)   # tetto di errori: niente migliaia di richieste
            self.assertEqual(json.loads((d / "scanner.json").read_text()), prev)   # file salvato intatto
            r0 = SC.giro(None, d / "vuota", datetime(2026, 11, 30, 1, tzinfo=UTC), net=SC.Rete(net, max_err=5, pausa=0),
                         universo=universo_finto(), cache=d / "c", seed_dir=None)
            self.assertEqual(r0["righe"], [])
            self.assertTrue(r0["dati"]["ritardo"])
            self.assertIn("non riuscito", SC.ultimo(d)["dati"]["nota"] + r["dati"]["nota"])

    def test_trx_rete_giu(self):
        net = FakeNet({}, {}, {}, fail=True)
        fb = seed_feats("BTC")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            # senza cache né file dello studio: registro non aggiornato, nessuna eccezione
            r = SC.trx_giro(fb, d, datetime(2026, 11, 25, 10, tzinfo=UTC), net=SC.Rete(net, max_err=3, pausa=0), cache=d / "c", seed_dir=None)
            self.assertTrue(r["dati"]["ritardo"])
            self.assertEqual(r["operazioni"], [])
            # con i file dello studio come cache: si calcola sull'ultima cache, con l'avviso
            r = SC.trx_giro(fb, d, datetime(2026, 11, 25, 10, tzinfo=UTC), net=SC.Rete(net, max_err=3, pausa=0), cache=d / "c", seed_dir=SEED)
            self.assertTrue(r["dati"]["ritardo"])
            self.assertEqual(r["stato"]["lato"], "flat")
            self.assertEqual(r["dati_fino"], "2026-11-24")
            self.assertTrue((d / "trx_carta.json").exists())
            # stesso giorno: nessun ricalcolo, nessuna richiesta
            net.calls.clear()
            SC.trx_giro(fb, d, datetime(2026, 11, 25, 11, tzinfo=UTC), net=SC.Rete(net, pausa=0), cache=d / "c", seed_dir=SEED)
            self.assertFalse(net.calls)
            self.assertTrue(SC.trx_giro(None, d, datetime(2026, 11, 25, 11, tzinfo=UTC))["dati"]["ritardo"])   # BTC assente


class TestUniversoEPagina(unittest.TestCase):
    def test_universo_statico(self):
        u = json.loads(SC.UNIVERSO_FILE.read_text())
        m = {x["ticker"]: x for x in u["monete"]}
        self.assertEqual(u["n"], len(u["monete"]))
        self.assertGreater(u["n"], 100)
        self.assertTrue(all(x["bitget"] or x["okx"] for x in u["monete"]))   # operabili su Bitget o OKX
        self.assertEqual((m["PEPE"]["perp"], m["PEPE"]["div"]), ("1000PEPEUSDT", 1000))
        self.assertEqual(m["TRX"]["scheda"]["q4"]["fin"], 87198)
        self.assertTrue(m["TRX"]["scheda"]["q4"]["ok"])
        self.assertNotIn("NaN", SC.UNIVERSO_FILE.read_text())

    def test_pagina_e_avviso(self):
        from radar.dashboard import render
        T = (ROOT / "radar" / "dashboard_template.html").read_text()
        v = T[T.index('<div class="view" id="v-scanner"'):T.index("<!-- ============ GRAFICO")]
        self.assertIn(SC.AVVISO.split(". ", 1)[1], v.replace("<b>", "").replace("</b>", ""))   # avviso fisso nel markup
        self.assertIn('id="trxBody"', v)
        self.assertLess(v.index('id="trxBody"'), v.index('id="scBody"'))                    # TRX in alto
        self.assertIn("T.nota", T)                                                           # nota fissa di TRX in testa al blocco
        with tempfile.TemporaryDirectory() as t:
            html = render({"date": "2026-11-25", "price": 1.0, "scanner": {"settimana": "2026-11-22", "righe": []},
                           "trx_carta": SC.build_trx(SC._reg_vuoto(), datetime(2026, 11, 25, tzinfo=UTC))}, Path(t) / "i.html", standalone=False).read_text()
        self.assertIn('"nota": "sulla carta: nessun capitale, nessun ordine"', html)

    def test_giro_orario_in_cli(self):
        src = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('report["trx_carta"] = _soft("TRX sulla carta", lambda: mod("scanner").trx_giro(f, DATA_DIR))', src)
        self.assertIn('_soft("scanner settimanale", lambda: mod("scanner").giro(f, DATA_DIR))', src)
        self.assertIn('or _soft("scanner (ultimo salvato)", lambda: mod("scanner").ultimo(DATA_DIR))', src)
        self.assertIn(".scanner-cache/", (ROOT / ".gitignore").read_text())
        wf = (ROOT / ".github" / "workflows" / "daily.yml").read_text()
        self.assertIn("path: .scanner-cache", wf)
        self.assertIn("key: radar-scanner-${{ hashFiles('.scanner-cache/**') }}", wf)

    def test_nessun_avviso_ne_ordini(self):
        src = (ROOT / "radar" / "scanner.py").read_text()
        for w in ("telegram", "send(", "place_order", "api_key"):
            self.assertNotIn(w, src)


if __name__ == "__main__":
    unittest.main()
