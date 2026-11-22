"""Pagina Book (radar/pages/book.html): funzioni pure fra CORE-START e CORE-END eseguite con node, più i testi obbligatori. Niente rete."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "radar" / "pages" / "book.html"
NODE = shutil.which("node")

JS = r"""
const BK = (function () { /*CORE*/; return BK; })();
const out = {};
const M = o => new Map(Object.entries(o).map(([k, v]) => [+k, v]));

// --- sincronizzazione Binance futures (U, u, pu) e spot (U, u)
let s = BK.newState(false);
BK.feed(s, { U: 90, u: 99, pu: 80, b: [["100", "9"]], a: [] });          // prima dello snapshot: in coda
BK.feed(s, { U: 100, u: 110, pu: 99, b: [["100", "2"]], a: [["101", "3"]] });
out.fut_snap = BK.applySnapshot(s, { lastUpdateId: 105, bids: [["100", "1"], ["99", "1"]], asks: [["101", "1"]] });
out.fut_synced = s.synced; out.fut_bid = s.bids.get(100); out.fut_ask = s.asks.get(101);
out.fut_next = BK.feed(s, { U: 111, u: 120, pu: 110, b: [["99", "0"]], a: [] });
out.fut_del = s.bids.has(99);
out.fut_gap = BK.feed(s, { U: 130, u: 140, pu: 125, b: [], a: [] });
out.fut_cleared = s.bids.size;
s = BK.newState(true);
BK.applySnapshot(s, { lastUpdateId: 105, bids: [["100", "1"]], asks: [["101", "1"]] });
out.spot_old = BK.feed(s, { U: 100, u: 105, b: [["100", "7"]], a: [] });
out.spot_first = BK.feed(s, { U: 104, u: 110, b: [["100", "2"]], a: [] });
out.spot_next = BK.feed(s, { U: 111, u: 112, b: [], a: [["101", "4"]] });
out.spot_gap = BK.feed(s, { U: 114, u: 115, b: [], a: [] });
s = BK.newState(false); BK.startLoose(s);                                  // senza snapshot: solo aggiornamenti
out.loose_first = BK.feed(s, { U: 5, u: 9, pu: 1, b: [["100", "1"]], a: [["101", "1"]] });
out.loose_gap = BK.feed(s, { U: 20, u: 30, pu: 15, b: [], a: [] });

// --- dollari per fascia, con livelli profondi (OKX: prezzi esatti; Hyperliquid: livelli larghi distribuiti)
let b = BK.binBook(M({ 60010: 1, 59990: 2 }), M({ 60030: 1, 60060: 0.5 }), { b: [[59800, 4, 100], [59990, 9, 0], [59700, 1, 0]], a: [[60200, 2, 100], [60040, 9, 0]] }, 25, 0.05);
out.bin_mid = b.mid;
out.bin_bid_2400 = b.bid.get(BK.idxOf(60010, 25)); out.bin_bid_2399 = b.bid.get(BK.idxOf(59990, 25));
out.bin_deep_spread = [59800, 59825, 59850, 59875].map(p => Math.round(b.bid.get(BK.idxOf(p, 25))));
out.bin_deep_exact = b.bid.get(BK.idxOf(59700, 25));
out.bin_ask_spread = [60100, 60125, 60150, 60175].map(p => Math.round(b.ask.get(BK.idxOf(p, 25))));
out.bin_no_double = b.ask.get(BK.idxOf(60040, 25));                         // 60040 è dentro il raggio del flusso live: non si somma
out.bin_empty = BK.binBook(new Map(), M({ 1: 1 }), null, 25, 0.05);

// --- muri: >= 3× la media e in rilievo sulle fasce vicine
const flat = (lo, hi, v) => { const m = new Map(); for (let i = lo; i < hi; i++) m.set(i, v); return m; };
let bid = flat(100, 150, 1e6), ask = flat(150, 200, 1e6);
ask.set(170, 8e6); bid.set(120, 5e6);
for (let i = 146; i < 154; i++) (i < 150 ? bid : ask).set(i, 6e6);          // altopiano a ridosso del prezzo: non è un muro
let w = BK.walls(bid, ask, 100, 200, 25, 3);
out.walls_ask = w.ask.map(x => x.px); out.walls_bid = w.bid.map(x => x.px);
out.heat = [BK.heat(2), BK.heat(3), BK.heat(5.5), BK.heat(8), BK.heat(20)];
out.fmt = [BK.fmtUsd(7350000), BK.fmtUsd(1910000), BK.fmtUsd(45000)];

// --- sentiment (specifica fissa)
let im = BK.imbalance(M({ 2399: 30, 2390: 10, 2300: 1000 }), M({ 2401: 10, 2500: 1000 }), 60000, 25, 0.01);
out.imb = [im.bid, im.ask, im.I];
const now = 1e12, W = 1800000;
let lb = BK.liqBalance([{ t: now - 1000, usd: 300, side: "short" }, { t: now - 2000, usd: 100, side: "long" }, { t: now - W - 1, usd: 9999, side: "long" }], now, W);
out.liq = [lb.long, lb.short, lb.L];
out.liq_none = BK.liqBalance([], now, W).L;
out.sent = [BK.sentiment(0.5, 0.5), BK.sentiment(0.4, 0), BK.sentiment(-0.2, -0.3), BK.sentiment(0.41, 0), BK.sentiment(-1, -1)].map(x => [+x.S.toFixed(3), x.label]);

// --- liquidazioni: lato della posizione liquidata e dollari
out.l_bin = BK.binanceLiq({ e: "forceOrder", E: 5, o: { s: "BTCUSDT", S: "SELL", q: "0.5", p: "59000", ap: "60000", z: "0.5", T: 7 } }, "BTCUSDT");
out.l_bin_other = BK.binanceLiq({ e: "forceOrder", o: { s: "ETHUSDT", S: "BUY", q: "1", p: "1", ap: "1", z: "1", T: 7 } }, "BTCUSDT").length;
out.l_byb = BK.bybitLiq({ topic: "allLiquidation.BTCUSDT", ts: 1, data: [{ T: 9, s: "BTCUSDT", S: "Buy", v: "0.2", p: "60000" }, { T: 9, s: "BTCUSDT", S: "Sell", v: "0.1", p: "60000" }] }, "BTCUSDT");
out.l_okx = BK.okxLiq({ data: [{ instFamily: "BTC-USDT", details: [{ side: "sell", posSide: "long", bkPx: "60000", sz: "150", ts: "11" }, { side: "buy", posSide: "short", bkPx: "60000", sz: "10", ts: "12" }] },
                               { instFamily: "ETH-USDT", details: [{ side: "sell", posSide: "long", bkPx: "1700", sz: "5", ts: "11" }] }] }, "BTC-USDT", 0.01);
out.l_okx_eth = BK.okxLiq({ data: [{ instFamily: "ETH-USDT", details: [{ side: "buy", posSide: "net", bkPx: "1700", sz: "20", ts: "11" }] }] }, "ETH-USDT", 0.1);

// --- muri nel tempo
function run(side, path, vanishAt, wallIdx) {          // prezzo per campione; il muro sparisce dal campione vanishAt
  const tr = BK.newTracker(), ev = [];
  path.forEach((mid, k) => {
    const im = BK.idxOf(mid, 25), bid = flat(im - 60, im, 1e6), ask = flat(im + 1, im + 61, 1e6);
    if (k < vanishAt) { const m = side === "ask" ? ask : bid; if (side === "ask" ? wallIdx > im : wallIdx < im) m.set(wallIdx, 9e6); }
    const prev = k ? path[k - 1] : mid;
    ev.push(...BK.trackWalls(tr, { t: k * 5000, mid, midLo: Math.min(mid, prev), midHi: Math.max(mid, prev), bid, ask, lo: im - 60, hi: im + 61, step: 25 }));
  });
  return ev.map(e => [e.side, e.px, e.out, e.usd]);
}
const wi = BK.idxOf(60500, 25);
out.tr_ritirato = run("ask", [60300, 60350, 60400, 60420, 60430, 60430, 60425, 60420, 60410, 60400], 6, wi);       // a 0,12% e poi sparisce senza essere toccato
out.tr_eseguito = run("ask", [60300, 60400, 60450, 60480, 60495, 60530, 60560, 60580, 60600], 99, wi);             // il prezzo lo attraversa
out.tr_lontano = run("ask", [59500, 59510, 59520, 59500, 59510, 59500, 59510, 59500, 59500], 5, wi);               // rimosso a 1,6% dal prezzo: nessun evento
out.tr_breve = run("ask", [60400, 60420, 60430, 60430, 60430, 60430], 2, wi);                                      // visto solo 2 campioni: nessun evento
out.tr_bid = run("bid", [60700, 60650, 60600, 60560, 60540, 60540, 60545, 60550, 60560, 60570], 6, wi - 1);        // muro in acquisto ritirato
out.tr_tardivo = run("ask", [60300, 60400, 60450, 60480, 60490, 60495, 60498, 60530, 60560, 60580], 6, wi);        // consumato al 100% e attraversato due campioni dopo

const E = (side, out_, n) => Array.from({ length: n }, (_, k) => ({ t: now - k * 1000, side, out: out_ }));
out.st_warn = BK.wallStats([...E("ask", "ritirato", 4), ...E("bid", "ritirato", 1), ...E("ask", "eseguito", 1), { t: now - W - 5, side: "bid", out: "ritirato" }], now, W);
out.st_none = BK.wallStats([...E("ask", "ritirato", 3), ...E("bid", "ritirato", 3)], now, W).warn;
out.st_exec = BK.wallStats([...E("bid", "ritirato", 3), ...E("bid", "eseguito", 5)], now, W).warn;
console.log(JSON.stringify(out));
"""


def core():
    m = re.search(r"/\*CORE-START.*?\*/(.*?)/\*CORE-END\*/", PAGE.read_text(), re.S)
    assert m, "blocco CORE non trovato"
    return m.group(1)


@unittest.skipUnless(NODE, "node non disponibile")
class TestBookCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([NODE, "-e", JS.replace("/*CORE*/", core())], capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise AssertionError(r.stderr[-2000:])
        cls.o = json.loads(r.stdout)

    def test_sync_binance(self):
        o = self.o
        self.assertEqual((o["fut_snap"], o["fut_synced"], o["fut_bid"], o["fut_ask"]), ("ok", True, 2, 3))
        self.assertEqual((o["fut_next"], o["fut_del"]), ("ok", False))
        self.assertEqual((o["fut_gap"], o["fut_cleared"]), ("resync", 0))          # salto di sequenza: si riparte dallo snapshot
        self.assertEqual((o["spot_old"], o["spot_first"], o["spot_next"], o["spot_gap"]), ("skip", "ok", "ok", "resync"))
        self.assertEqual((o["loose_first"], o["loose_gap"]), ("ok", "resync"))

    def test_fasce_in_dollari(self):
        o = self.o
        self.assertEqual(o["bin_mid"], 60020)
        self.assertEqual((o["bin_bid_2400"], o["bin_bid_2399"]), (60010, 2 * 59990))
        self.assertEqual(o["bin_deep_spread"], [59800] * 4)                         # 4 × 59.800 $ in 4 fasce da 25 $
        self.assertEqual(o["bin_deep_exact"], 59700)
        self.assertEqual(o["bin_ask_spread"], [30100] * 4)                          # 2 × 60.200 $ in 4 fasce
        self.assertEqual(o["bin_no_double"], 60030)
        self.assertIsNone(o["bin_empty"])

    def test_muri(self):
        o = self.o
        self.assertEqual(o["walls_ask"], [170 * 25])
        self.assertEqual(o["walls_bid"], [120 * 25])
        self.assertEqual(o["heat"], [0, 0, 0.5, 1, 1])
        self.assertEqual(o["fmt"], ["7,35M", "1,91M", "45k"])

    def test_sentiment_specifica_fissa(self):
        o = self.o
        self.assertEqual(o["imb"], [40, 10, 0.6])                                   # solo le fasce entro ±1%
        self.assertEqual(o["liq"], [100, 300, 0.5])
        self.assertEqual(o["liq_none"], 0)
        self.assertEqual(o["sent"], [[0.5, "pressione al rialzo"], [0.2, "neutro"], [-0.25, "pressione al ribasso"],
                                     [0.205, "pressione al rialzo"], [-1, "pressione al ribasso"]])

    def test_liquidazioni(self):
        o = self.o
        self.assertEqual(o["l_bin"], [{"t": 7, "px": 60000, "usd": 30000, "side": "long", "ex": "Binance"}])
        self.assertEqual(o["l_bin_other"], 0)
        self.assertEqual([(x["side"], x["usd"]) for x in o["l_byb"]], [("long", 12000), ("short", 6000)])
        self.assertEqual([(x["side"], x["usd"]) for x in o["l_okx"]], [("long", 90000), ("short", 6000)])   # 150 contratti × 0,01 BTC × 60.000
        self.assertEqual([(x["side"], x["usd"]) for x in o["l_okx_eth"]], [("short", 3400)])                # 20 × 0,1 ETH × 1.700

    def test_muri_ritirati_o_eseguiti(self):
        o = self.o
        self.assertEqual(o["tr_ritirato"], [["ask", 60500, "ritirato", 9e6]])
        self.assertEqual(o["tr_eseguito"], [["ask", 60500, "eseguito", 9e6]])
        self.assertEqual(o["tr_lontano"], [])
        self.assertEqual(o["tr_breve"], [])
        self.assertEqual(o["tr_bid"], [["bid", 60475, "ritirato", 9e6]])
        self.assertEqual(o["tr_tardivo"], [["ask", 60500, "eseguito", 9e6]])

    def test_avviso(self):
        o = self.o
        self.assertEqual(o["st_warn"], {"ask": {"rit": 4, "ese": 1}, "bid": {"rit": 1, "ese": 0}, "warn": "ask"})
        self.assertIsNone(o["st_none"])
        self.assertIsNone(o["st_exec"])


class TestBookPage(unittest.TestCase):
    def test_testi_e_registrazione(self):
        h = PAGE.read_text()
        self.assertIn("Indicatore descrittivo, non un segnale.", h)
        self.assertIn("Sotto 250.000 $ di liquidazioni in 30 minuti il punteggio non si calcola", h)
        self.assertIn("low: lg + sh > 0 && lg + sh < LIQ_MIN_USD", h)   # soglia come radar/orderbook.SENT_LIQ_MIN_USD
        self.assertIn("const LIQ_MIN_USD = 250000;", h)
        self.assertIn("storia dalla apertura della pagina", h)
        self.assertIn("Modalità demo", h)
        self.assertIn('id="v-book"', h)
        self.assertIn("window.PAGES.book", h)
        for url in ("fstream.binance.com", "stream.binance.com", "ws.okx.com", "stream.bybit.com", "ws-feed.exchange.coinbase.com", "api.hyperliquid.xyz"):
            self.assertIn(url, h)
        self.assertNotRegex(h, r"<script[^>]+src=")                                  # nessuna libreria esterna


if __name__ == "__main__":
    unittest.main()
