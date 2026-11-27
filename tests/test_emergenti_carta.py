"""Registro V3 sulla carta (radar/emergenti_carta.py, research/emergenti/PREREG-AVANTI-V3.md). Niente rete: file dello studio già
nel repository (w32_asset2/crypto/data, research/emergenti/data) e serie sintetiche. Coperti: lista 2026, segnali uguali a W3.2,
solo short, lista dell'anno, ingressi dal 30/11 (le aperte dello studio non contano), budget, massimo 5, quota, uscite di W3.2,
valore/DD/WR, soglie e stato "rivalutare", liste 2027, giro (nessuna richiesta prima dell'inizio, degrado su errore)."""
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from radar import emergenti_carta as EC
from radar import scanner as SC
from radar import weekly as W
from tests.test_scanner import FakeNet, feats_finte, seed_feats, serie

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "research" / "w32_asset2" / "crypto" / "data"
UTC = timezone.utc
TUTTI = {a: {"SOL", "XPL", "CHZ", "DN", "UP"} for a in range(2020, 2028)}


def lista(*tickers, anno=2026):
    return {str(anno): {"anno": anno, "fonte": "test", "data": "2025-11-16", "n": len(tickers), "monete": [{"ticker": t, "perp": f"{t}USDT"} for t in tickers]}}


def cand(t, i0, i1, v, aperta=False, pri=1.0, intra=False):
    return {"t": t, "sig": "2026-11-29", "ing": f"i{i0}", "usc": None if aperta else f"u{i1}", "px_in": 10.0, "px_out": None if aperta else 9.0,
            "ult": 9.5, "trail": 12.0, "k": 0.5, "motivo": "posizione aperta" if aperta else "trailing", "liq": False, "aperta": aperta,
            "i0": i0, "i1": i1, "v": np.asarray(v, float), "intra": intra, "pri": pri, "dati_fino": "2026-12-31"}


class TestLista(unittest.TestCase):
    def test_lista_2026_dallo_studio(self):
        l = EC.liste_statiche()["2026"]
        self.assertEqual((l["anno"], l["data"]), (2026, "2025-11-16"))      # istantanea più recente prima del 1/1/2026
        self.assertEqual(l, json.loads(json.dumps(EC.build_lista_studio(2026))))   # file = ricostruzione dai file dello studio
        self.assertTrue(all(101 <= m["rank"] <= 200 and m["perp"] for m in l["monete"]))
        self.assertEqual(l["n_lista"], 95)
        self.assertGreaterEqual(l["n"], 70)
        self.assertNotIn("HNT", {m["ticker"] for m in l["monete"]})        # perp chiuso: senza dati

    def test_lista_2027_da_coingecko_o_candidata(self):
        u = {"aggiornato": "2026-12-28", "monete": [{"ticker": "AAA", "rank_oggi": 150, "perp": "AAAUSDT", "fonte": "binance"},
                                                    {"ticker": "BBB", "rank_oggi": 90, "perp": "BBBUSDT", "fonte": "binance"},
                                                    {"ticker": "CCC", "rank_oggi": 120, "perp": None, "nd": "nessun perp"}]}
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / SC.UNIV_CACHE).write_text(json.dumps(u))
            reg = {}
            EC.aggiorna_liste(reg, date(2026, 12, 29), None, Path(d), static=lista("SOL"))
            self.assertEqual(reg["lista_candidata"]["anno"], 2027)
            self.assertEqual([m["ticker"] for m in reg["lista_candidata"]["monete"]], ["AAA"])   # solo 101–200 con dati
            av = EC.aggiorna_liste(reg, date(2027, 1, 1), None, Path(d), static=lista("SOL"))   # CoinGecko non provato/assente
            self.assertEqual(reg["liste"]["2027"]["data"], "2026-12-28")
            self.assertNotIn("lista_candidata", reg)
            self.assertFalse(av)
            EC.aggiorna_liste(reg, date(2027, 1, 8), None, Path(d), static=lista("SOL"))
            self.assertEqual(reg["liste"]["2027"]["data"], "2026-12-28")                       # congelata: non si riscrive
            self.assertEqual(EC.membri(EC.tutte_le_liste(reg, lista("SOL"))), {2026: {"SOL"}, 2027: {"AAA"}})
            senza = {}
            self.assertTrue(EC.aggiorna_liste(senza, date(2027, 1, 3), None, Path(d) / "x", static=lista("SOL")))   # avviso


class TestSegnali(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sol = seed_feats("SOL")

    def test_segnali_come_lo_studio_v3_sul_2026(self):
        """Candidati short dal 05/01/2026 = studio V3 (run.py, maschera "short": long spenti, short solo nelle domeniche con la
        moneta nella lista dell'anno, inizio max(2021, completa_da), storia completa) sulle monete della lista 2026 con i file
        dello studio w32_asset2 nel repository; il registro usa la finestra dello scanner (1000 giorni)."""
        E = EC.engine()
        d = ROOT / "research" / "emergenti" / "data"
        U = pd.read_csv(d / "universe.csv").set_index("ticker")
        CM = pd.read_csv(d / "counts_moneta.csv").set_index("ticker")
        memb = EC.membri(EC.liste_statiche())
        tick = [m["ticker"] for m in EC.liste_statiche()["2026"]["monete"] if (SEED / f"{m['ticker']}_perp.csv.gz").exists()]
        self.assertGreaterEqual(len(tick), 30)
        ref, mine = set(), set()
        for t in tick:
            xs = [SC._seed(t, k, SEED) for k in ("spot", "perp", "funding")]
            f = SC.feats(*(None if x is None else x[x.index >= SC.TRX_SINCE] for x in xs), fine=date(2026, 11, 24))
            w = E.weekly_bars(f)
            rk = lambda s: U.loc[t].get(f"rank_{(s + pd.Timedelta(days=1)).year}", np.nan)  # noqa: E731
            mem = pd.Series([bool(rk(s) == rk(s) and 100 < rk(s) <= 200) for s in w.index], index=w.index)
            s0 = max(pd.Timestamp("2021-01-01"), pd.Timestamp(CM.loc[t, "completa_da"]))
            o = E.simulate(f, start=str(s0.date()), allow_long=pd.Series(False, index=w.index), allow_short=mem, all_perp=True)
            ref |= {(t, x["signal"], x["entry"], x["exit"]) for x in E.all_trades(o) if x["entry"] >= "2026-01-05"}
            fw = f[f.index >= pd.Timestamp("2026-11-25") - pd.Timedelta(days=SC.WINDOW_DAYS)]
            mine |= {(t, x["signal"], x["entry"], x["exit"]) for x in EC.segnali(t, fw, memb, inizio="2026-01-05")[0]}
        self.assertGreater(len(ref), 40)
        # LUNC nei file di w32_asset2 parte dai prezzi di LUNA (2020, ~10.000 volte quelli di oggi): la EMA 21 settimanale sulla
        # storia completa ne porta ancora traccia nel 2026 (~2%) e l'uscita EMA cade una settimana dopo che con la finestra di
        # 1000 giorni del registro. Stesso segnale e stesso ingresso; con i dati di research/emergenti/data/coins coincide anche l'uscita
        diff = {x for x in mine ^ ref if x[0] == "LUNC"}
        self.assertEqual({x[:3] for x in diff}, {("LUNC", "2026-03-22", "2026-03-23")})
        self.assertEqual(mine - diff, ref - diff)
        v3 = pd.read_csv(d / "trades_V3.csv")
        presi = {(r.ticker, r.entry) for r in v3.itertuples() if r.entry >= "2026-01-05" and r.ticker in tick}
        self.assertTrue(presi)
        self.assertLessEqual(presi, {(t, e) for t, _, e, _ in mine})        # operazioni prese dallo studio nel 2026

    def test_short_mentre_w32_e_long(self):
        # ENS: con i long spenti lo short parte dal segnale del 13/11/2022; W3.2 com'è (long in corso) dal 20/11/2022
        f = seed_feats("ENS")
        o = W.simulate(f, start=EC.inizio_sim(f))
        w32 = {t["signal"] for t in o["trades"] if t["side"] == "short"}
        v3 = {t["signal"] for t in EC.segnali("ENS", f, {a: {"ENS"} for a in range(2020, 2028)}, inizio="2020-01-01")[0]}
        self.assertIn("2022-11-13", v3)
        self.assertNotIn("2022-11-13", w32)
        self.assertIn("2022-11-20", w32)
        mine, _ = EC.segnali("SOL", self.sol, TUTTI, inizio="2020-01-01")
        self.assertTrue(mine and all(t["side"] == "short" and t["expo"] <= 1 for t in mine))   # solo short, esposizione ≤ 1x

    def test_solo_short_e_lista_dell_anno(self):
        up = feats_finte(serie(drift=1.0, seed=2))
        o = W.simulate(up, start=EC.inizio_sim(up))
        self.assertTrue(any(t["side"] == "long" for t in o["trades"] + [o["open"]] if t))
        self.assertEqual(EC.segnali("UP", up, TUTTI, inizio="2020-01-01")[0], [])
        self.assertEqual(EC.segnali("SOL", self.sol, {2026: {"XPL"}}, inizio="2020-01-01")[0], [])   # fuori lista: niente
        solo25 = EC.segnali("SOL", self.sol, {2025: {"SOL"}}, inizio="2020-01-01")[0]
        self.assertTrue(solo25 and all(t["entry"].startswith("2025") for t in solo25))

    def test_ingressi_dal_30_11_aperte_dello_studio_escluse(self):
        # SOL short dal 09/11/2026 (studio w32_asset2); XPL e CHZ tra le 5 aperte di V3 al 24/11: non contano
        self.assertEqual(EC.segnali("SOL", self.sol, TUTTI)[0], [])
        self.assertEqual([t["entry"] for t in EC.segnali("SOL", self.sol, TUTTI, inizio="2026-11-01")[0]], ["2026-11-09"])
        liste = EC.liste_statiche()
        dati = {t: {"f": seed_feats(t), "perp": SC._seed(t, "perp", SEED)} for t in ("XPL", "CHZ", "PYTH", "FLOKI")}
        out = EC.calcola(dati, liste, date(2026, 11, 25), seed_feats("BTC"))
        self.assertEqual((out["posizioni"], out["chiuse"], out["valore"], out["stato"]), ([], [], EC.BUDGET, "in raccolta"))
        prima = EC.calcola(dati, liste, date(2026, 11, 25), None, inizio="2026-01-05")
        self.assertIn("XPL", {p["t"] for p in prima["posizioni"]})            # stessa moneta, con un inizio precedente sì

    def test_calcolo_completo_e_uscite_w32(self):
        raw = serie(drift=-1.0, seed=3, p0=50.0, end="2026-12-27")
        dn = feats_finte(raw)
        o = W.simulate(dn, start=EC.inizio_sim(dn))
        trs = [t for t in o["trades"] + [o["open"]] if t and t["side"] == "short"]
        self.assertTrue(trs)
        t0 = trs[-1]
        liste = lista("DN", anno=int(t0["entry"][:4]))
        out = EC.calcola({"DN": {"f": dn, "perp": raw}}, liste, date(2026, 12, 28), None, inizio=t0["entry"])
        self.assertEqual(len(out["chiuse"]) + len(out["posizioni"]), 1)
        r = (out["chiuse"] or out["posizioni"])[0]
        self.assertEqual(r["ing"], t0["entry"])
        if t0.get("exit"):
            self.assertEqual(r["usc"], t0["exit"])                            # uscita di W3.2
        else:
            self.assertEqual((r["trail"], r["ult"]), (SC._r(t0["trail"], 8), SC._r(float(dn["close"].iloc[-1]), 8)))
        self.assertEqual(r["quota"], 2000.0)                                  # 1/5 del budget
        self.assertAlmostEqual(out["valore"], EC.BUDGET + r["pnl_usd"], places=1)


class TestPortafoglio(unittest.TestCase):
    def test_massimo_5_quota_ed_esclusi(self):
        G = pd.date_range("2026-11-30", periods=10)
        cs = [cand(f"C{i}", 0, 4, [1.0, 1.0, 1.0, 1.0, 1.1], pri=10 - i) for i in range(7)]
        cs.append(cand("LATE", 6, 9, [1.0, 1.0, 1.0, 1.2], aperta=True))
        pf = EC.portafoglio(cs, G)
        self.assertEqual([c["t"] for c in pf["chiuse"]], ["C0", "C1", "C2", "C3", "C4"])   # priorità: volume a 90 giorni
        self.assertEqual({e["t"] for e in pf["esclusi"]}, {"C5", "C6"})                    # quote piene: registrati come esclusi
        self.assertTrue(all(c["quota"] == 2000.0 for c in pf["chiuse"]))
        self.assertTrue(all(abs(c["pnl"] - 10.0) < 1e-9 and abs(c["pnl_usd"] - 200.0) < 1e-6 for c in pf["chiuse"]))
        self.assertEqual(len(pf["aperte"]), 1)
        self.assertEqual(pf["aperte"][0]["quota"], 2200.0)                                 # 11.000 $ / 5 dopo le chiusure
        self.assertAlmostEqual(pf["eq"][-1], 11000 + 2200 * 0.2)
        self.assertAlmostEqual(pf["eq"][0], 10000)
        m = EC.metriche(pf["eq"], pf["chiuse"], G)
        self.assertEqual((m["n_chiuse"], m["wr"], m["stato"]), (5, 100.0, "in raccolta"))
        self.assertEqual(m["rendimento"], 14.4)

    def test_dd_wr_soglie_e_rivalutare(self):
        G = pd.date_range("2026-11-30", periods=4)
        eq = np.array([10000, 12000, 9000, 10500.0])
        ch = [{"pnl": 5.0}] * 11 + [{"pnl": -3.0}] * 9
        m = EC.metriche(eq, ch, G)
        self.assertEqual(m["dd"], -25.0)
        self.assertEqual((m["n_chiuse"], m["wr"], m["stato"]), (20, 55.0, "rivalutare"))
        self.assertTrue(m["verifica"]["dd"]["ok"] and m["verifica"]["wr"]["ok"] and m["verifica"]["rendimento"]["ok"])
        self.assertFalse(m["verifica"]["fase_btc_long"]["ok"])                 # nessun semestre con BTC long
        self.assertIn("si chiude", m["esito"])
        lungo = pd.date_range("2026-11-30", periods=200)
        eq2 = np.linspace(10000, 11000, 200)
        m2 = EC.metriche(eq2, ch, lungo, pd.Series(1, index=lungo))
        self.assertEqual(m2["verifica"]["fase_btc_long"]["giorni"], 200)
        self.assertIn("riconsiderare", m2["esito"])
        self.assertEqual(EC.metriche(eq2, ch[:19], lungo)["stato"], "in raccolta")   # meno di 20 chiuse
        self.assertEqual(EC.SOGLIE["min_chiuse"], 20)
        self.assertEqual((EC.SOGLIE["wr_min"], EC.SOGLIE["dd_min"], EC.SOGLIE["fase_btc_long_perdita_max"]), (50, -25, -10))


class TestGiro(unittest.TestCase):
    def test_prima_dell_inizio_nessuna_richiesta(self):
        net = FakeNet({}, {}, {}, fail=True)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            r = EC.giro(None, d, datetime(2026, 11, 27, 10, tzinfo=UTC), net=SC.Rete(net, pausa=0), cache=d / "c", seed_dir=None)
            self.assertFalse(net.calls)
            self.assertEqual((r["inizio"], r["budget"], r["posizioni"], r["chiuse"], r["stato"]), ("2026-11-30", 10000.0, [], [], "in raccolta"))
            self.assertEqual((r["lista"]["anno"], r["lista"]["n"]), (2026, EC.liste_statiche()["2026"]["n"]))
            self.assertEqual(r["soglie"]["min_chiuse"], 20)
            saved = json.loads((d / EC.FILE).read_text())
            self.assertEqual(saved["settimana"], "2026-11-22")
            for k in ("inizio", "budget", "aggiornato", "posizioni", "chiuse", "valore", "dd", "n_chiuse", "wr", "soglie", "stato", "lista"):
                self.assertIn(k, saved)

    def test_errore_di_rete_tiene_l_ultimo_stato(self):
        net = FakeNet({}, {}, {}, fail=True)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prev = dict(EC._vuoto(), settimana="2026-11-22", valore=10123.0, posizioni=[{"t": "XPL"}])
            (d / EC.FILE).write_text(json.dumps(prev))
            r = EC.giro(None, d, datetime(2026, 11, 30, 1, tzinfo=UTC), net=SC.Rete(net, max_err=3, pausa=0), cache=d / "c",
                        seed_dir=None, static=lista("AAA", "BBB", "CCC"))
            self.assertTrue(r["dati"]["ritardo"])
            self.assertEqual((r["valore"], r["posizioni"]), (10123.0, [{"t": "XPL"}]))
            self.assertEqual(json.loads((d / EC.FILE).read_text()), prev)      # file intatto

    def test_settimana_nuova_con_dati(self):
        raw = serie(drift=-1.0, seed=3, p0=50.0, end="2026-12-06")
        dn = feats_finte(raw)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            r = EC.giro(None, d, datetime(2026, 12, 7, 1, tzinfo=UTC), cache=d / "c", static=lista("DN"), dati={"DN": {"f": dn, "perp": raw}})
            self.assertEqual(r["settimana"], "2026-12-06")
            self.assertEqual(r["dati_fino"], "2026-12-06")
            self.assertEqual(r["posizioni"], [])                               # short di DN aperto da prima del 30/11: non conta
            self.assertEqual(len(r["serie"]["date"]), 7)
            again = EC.giro(None, d, datetime(2026, 12, 8, 1, tzinfo=UTC), cache=d / "c", static=lista("DN"), dati={})
            self.assertEqual(again["aggiornato"], r["aggiornato"])             # stessa settimana: nessun ricalcolo

    def test_nessun_ordine_ne_avviso(self):
        src = (ROOT / "radar" / "emergenti_carta.py").read_text()
        for bad in ("telegram", "send_message", "place_order", "requests.post"):
            self.assertNotIn(bad, src.lower())
        self.assertIn('mod("emergenti_carta").giro(f, DATA_DIR)', (ROOT / "radar" / "cli.py").read_text())


if __name__ == "__main__":
    unittest.main()
