"""Motore del book di BTC (orario): fotografie dei book di più exchange, controlli dei dati, lettura e apprendimento ogni 4 ore.

Ogni giro (radar.cli daily, ogni ora):
1. scarica i book da fonti raggiungibili dai runner USA (Coinbase, Kraken, OKX perp e spot, Binance spot via data-api;
   Hyperliquid perp solo per i registri dei muri e del sentiment, LOG_ONLY; Binance futures e Bybit sono bloccati: 451/403);
2. CONTROLLI su ogni fonte: book non vuoto e ordinato, non incrociato, spread ≤ 15 bps, dati recenti (timestamp ≤ 120 s
   dove l'exchange lo dà), mid entro lo 0,3% dalla mediana delle altre fonti. Le fonti che falliscono si scartano e si registrano;
3. feature aggregate: profondità bid/ask in $ entro ±0,25/0,5/1/2%, squilibrio (bid − ask)/(bid + ask), muri più grandi entro ±2%
   e loro distanza, spread medio, microprezzo (scarto in bps dal mid del miglior livello pesato dalle quantità);
4. la previsione corrente (probabilità che il mid salga fra 1h e 4h) si salva NELLA STESSA RIGA, prima di conoscere l'esito:
   il registro è quindi tutto fuori campione;
5. ogni 4 ore (ora UTC multipla di 4 o ≥ 4 ore dall'ultimo apprendimento): valuta le previsioni salvate contro i rendimenti
   realizzati, confronta con due riferimenti ingenui (sempre "su" e momentum dell'ultima ora) e riaddestra una regressione
   logistica con forte regolarizzazione L2 sulle feature di squilibrio (data/ob_model.json).
Onestà: con una foto all'ora e poche settimane di dati il modello resta vicino a 0,5; il book cambia in secondi e una fotografia
oraria è un campione povero. Si mostra sempre l'accuratezza contro i riferimenti, con il numero di casi.

Registri per la validazione futura (sentiment e rilevatore di manipolazione), scritti a ogni giro:
- data/book_walls.csv: i 3 maggiori muri per lato e per exchange; al giro successivo ogni muro riceve l'ESITO (settle_walls):
  "eseguito" / "ritirato" / "presente" (+ "incerto", "non_verificabile", "scaduto"). APPROSSIMAZIONE GROSSOLANA: fra due foto
  orarie un muro può essere tolto e rimesso molte volte, spostato di una fascia o eseguito e ricostituito; "eseguito" vuol dire
  solo "il prezzo ha attraversato la fascia" (massimo/minimo delle candele da 1 minuto di una borsa spot, riportati sul
  prezzo della fonte), "ritirato" solo "alla foto dopo mancava ≥ 70% senza che il prezzo ci fosse arrivato";
- data/book_sentiment.csv: una riga per giro con I (squilibrio del book entro ±1%), L (squilibrio delle liquidazioni reali
  degli ultimi 30 minuti), S = 0,5·I + 0,5·L e i conteggi dei muri ritirati/eseguiti per lato (sentiment_row, log_sentiment).
  Specifica fissa: serve a verificare fra qualche settimana se S anticipa il rendimento dell'ora/del giorno successivo.
"""
from __future__ import annotations

import json
import math
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

BANDS = (0.25, 0.5, 1.0, 2.0)   # % dal mid
FEATS = ["imb_0.25", "imb_0.5", "imb_1", "imb_2", "micro_bps"]
MAX_SPREAD_BPS = 15.0
MAX_AGE_S = 120
MAX_MID_DEV = 0.003
WALL_BUCKET = 0.0005             # muri: livelli raggruppati in fasce dello 0,05%
WALL_MIN = 0.001
L2 = 4.0                         # regolarizzazione della logistica (forte: pochi dati)
MIN_TRAIN = 30                   # campioni etichettati prima di allontanarsi da 0,5
HORIZONS = {"1h": (50, 80), "4h": (210, 285)}   # minuti: finestra in cui cercare la foto "dopo"

_s = requests.Session()


# ------------------------------------------------------------------ fonti
def _coinbase():
    j = _s.get("https://api.exchange.coinbase.com/products/BTC-USD/book", params={"level": 2}, timeout=20).json()
    ts = pd.Timestamp(j["time"]).tz_convert(None).timestamp() if j.get("time") else None
    return [(float(p), float(q)) for p, q, *_ in j["bids"]], [(float(p), float(q)) for p, q, *_ in j["asks"]], ts


def _kraken():
    j = _s.get("https://api.kraken.com/0/public/Depth", params={"pair": "XBTUSD", "count": 500}, timeout=20).json()
    b = next(iter(j["result"].values()))
    ts = max(float(x[2]) for x in b["bids"][:20] + b["asks"][:20])   # ultimo aggiornamento fra i livelli migliori
    return [(float(p), float(q)) for p, q, _ in b["bids"]], [(float(p), float(q)) for p, q, _ in b["asks"]], ts


def _okx(inst: str, ct: float):
    j = _s.get("https://www.okx.com/api/v5/market/books-full", params={"instId": inst, "sz": 5000}, timeout=20).json()["data"][0]
    return [(float(p), float(q) * ct) for p, q, *_ in j["bids"]], [(float(p), float(q) * ct) for p, q, *_ in j["asks"]], float(j["ts"]) / 1000


def _binance():
    j = _s.get("https://data-api.binance.vision/api/v3/depth", params={"symbol": "BTCUSDT", "limit": 5000}, timeout=20).json()
    return [(float(p), float(q)) for p, q in j["bids"]], [(float(p), float(q)) for p, q in j["asks"]], None


def hl_step(px: float, sig: int) -> float:
    """Passo di prezzo dell'aggregazione Hyperliquid a `sig` cifre significative (60.738 $, 4 cifre → 10 $)."""
    return 10.0 ** (math.floor(math.log10(px)) - sig + 1)


def hl_merge(layers: list[tuple[list, float]], side: str) -> list[tuple[float, float]]:
    """Unisce più aggregazioni dello STESSO lato di un book Hyperliquid (dalla più fine alla più grossa; ognuna dà solo 20
    livelli) in un solo lato: i livelli fini dove ci sono, più lontano quelli grossi. Un livello aggregato di passo s al
    prezzo P copre [P, P+s) in acquisto (arrotondato in giù) e (P−s, P] in vendita (in su); della fascia a cavallo del bordo
    già coperto si tiene solo la quantità in più rispetto ai livelli fini. Le letture non sono simultanee: è una stima."""
    sgn = 1 if side == "bid" else -1          # in acquisto si scende, in vendita si sale
    out: list[tuple[float, float]] = []
    edge = None                                # bordo già coperto (prezzo più lontano dal mid)
    for levels, step in layers:
        if not levels:
            continue
        if edge is None:
            out += list(levels)
        else:
            for p, q in levels:
                near = p + sgn * step           # estremo della fascia verso il mid (p = estremo lontano)
                if (p - edge) * sgn >= 0:       # tutta dentro la parte già coperta
                    continue
                if (near - edge) * sgn <= 0:    # tutta oltre il bordo
                    out.append((p, q))
                    continue
                lo, hi = min(p, near), max(p, near)
                inside = sum(q0 for p0, q0 in out if (lo <= p0 < hi if side == "bid" else lo < p0 <= hi))
                if q - inside > 0:
                    out.append((p, q - inside))
        edge = min(p for p, _ in out) if side == "bid" else max(p for p, _ in out)
    return sorted(out, key=lambda x: -x[0] * sgn)


# fonti aggiunte per i soli registri (muri e sentiment): NON entrano nella foto data/orderbook.csv né nel modello 1h/4h, così
# la serie storica delle feature e i muri mostrati in dashboard restano confrontabili con i giri precedenti
LOG_ONLY = {"hyperliquid"}
HL_FINE, HL_COARSE = (5, 4), (5, 4, 3)   # cifre significative: fine = passi ≤ 0,02% (muri), grossa = fino a ~±3% (solo I)


def _hyperliquid():
    """Perpetuo BTC di Hyperliquid (API pubblica "info", l2Book: 20 livelli per lato a ogni aggregazione). Il book "fine"
    (5 e 4 cifre significative, ~±0,3% a 60.000 $) è quello usato per controlli, muri e fasce strette; la versione "grossa"
    (anche 3 cifre: passi da 100 $ fino a ~±3%) serve SOLO allo squilibrio I entro ±1% del registro del sentiment, come stima."""
    lay, ts = {}, None
    for sig in HL_COARSE:
        j = _s.post("https://api.hyperliquid.xyz/info", json={"type": "l2Book", "coin": "BTC", "nSigFigs": sig}, timeout=20).json()
        lay[sig] = [[(float(x["px"]), float(x["sz"])) for x in lv] for lv in j["levels"]]
        ts = min(ts, float(j["time"]) / 1000) if ts else float(j["time"]) / 1000
    px = lay[HL_COARSE[0]][0][0][0]

    def side(sigs, i):
        return hl_merge([(lay[g][i], hl_step(px, g)) for g in sigs], "bid" if i == 0 else "ask")
    return side(HL_FINE, 0), side(HL_FINE, 1), ts, {"coarse": (side(HL_COARSE, 0), side(HL_COARSE, 1))}


SOURCES = {"coinbase": _coinbase, "kraken": _kraken, "okx_perp": lambda: _okx("BTC-USDT-SWAP", 0.01),
           "okx_spot": lambda: _okx("BTC-USDT", 1.0), "binance_spot": _binance, "hyperliquid": _hyperliquid}


# ------------------------------------------------------------------ funzioni pure (tests/test_orderbook.py)
def book_features(bids, asks) -> dict:
    """Feature di un book: mid, spread, microprezzo, profondità e squilibrio per fascia (None se il book non copre la fascia)."""
    bp, bq = np.array([b[0] for b in bids]), np.array([b[1] for b in bids])
    ap, aq = np.array([a[0] for a in asks]), np.array([a[1] for a in asks])
    mid = (bp[0] + ap[0]) / 2
    micro = (bp[0] * aq[0] + ap[0] * bq[0]) / (aq[0] + bq[0])
    out = {"mid": mid, "spread_bps": (ap[0] - bp[0]) / mid * 1e4, "micro_bps": (micro - mid) / mid * 1e4,
           "cover_bid": (1 - bp[-1] / mid) * 100, "cover_ask": (ap[-1] / mid - 1) * 100}
    for b in BANDS:
        if out["cover_bid"] + 1e-9 >= b and out["cover_ask"] + 1e-9 >= b:
            bu = float((bp * bq)[bp >= mid * (1 - b / 100)].sum()); au = float((ap * aq)[ap <= mid * (1 + b / 100)].sum())
            out[f"bid_{b:g}"], out[f"ask_{b:g}"] = bu, au
        else:
            out[f"bid_{b:g}"] = out[f"ask_{b:g}"] = None
    return out


def check(name: str, bids, asks, ts, now: float, ref_mid: float | None = None) -> list[str]:
    """Problemi di una fonte (lista vuota = dati buoni)."""
    bad = []
    if len(bids) < 20 or len(asks) < 20:
        return ["book vuoto o troppo corto"]
    if any(bids[i][0] < bids[i + 1][0] for i in range(min(50, len(bids) - 1))) or any(asks[i][0] > asks[i + 1][0] for i in range(min(50, len(asks) - 1))):
        bad.append("livelli non ordinati")
    if bids[0][0] >= asks[0][0]:
        bad.append("book incrociato")
    mid = (bids[0][0] + asks[0][0]) / 2
    if (asks[0][0] - bids[0][0]) / mid * 1e4 > MAX_SPREAD_BPS:
        bad.append("spread anomalo")
    if ts is not None and now - ts > MAX_AGE_S:
        bad.append(f"dati vecchi ({now - ts:.0f} s)")
    if ref_mid and abs(mid / ref_mid - 1) > MAX_MID_DEV:
        bad.append(f"mid fuori dal consenso ({(mid / ref_mid - 1) * 100:+.2f}%)")
    return bad


def aggregate(books: dict[str, tuple]) -> dict:
    """Feature aggregate sulle fonti valide: profondità sommate per fascia (solo fonti che la coprono), muri, spread e microprezzo medi."""
    feats = {k: book_features(b, a) for k, (b, a) in books.items()}
    mid = float(np.median([f["mid"] for f in feats.values()]))
    out = {"mid": round(mid, 2), "spread_bps": round(float(np.mean([f["spread_bps"] for f in feats.values()])), 3),
           "micro_bps": round(float(np.mean([f["micro_bps"] for f in feats.values()])), 3), "n_src": len(feats)}
    for b in BANDS:
        bu = [f[f"bid_{b:g}"] for f in feats.values() if f[f"bid_{b:g}"] is not None]
        au = [f[f"ask_{b:g}"] for f in feats.values() if f[f"ask_{b:g}"] is not None]
        B, A = sum(bu), sum(au)
        out[f"bid_{b:g}"], out[f"ask_{b:g}"] = round(B, 0), round(A, 0)
        out[f"imb_{b:g}"] = round((B - A) / (B + A), 4) if B + A > 0 else None
        out[f"src_{b:g}"] = len(bu)
    # muri: livelli di tutte le fonti in fasce dello 0,05% fra ±0,1% e ±2% dal mid DI OGNI FONTE (USD e USDT non si mescolano),
    # il più grande per lato; la liquidità a ridosso del prezzo (< 0,1%) non conta come muro
    for side, idx in (("bid", 0), ("ask", 1)):
        acc: dict[int, float] = {}
        for k, bk in books.items():
            m0 = feats[k]["mid"]
            for p, q in bk[idx]:
                d = p / m0 - 1
                if WALL_MIN <= abs(d) <= 0.02:
                    acc[int(math.floor(d / WALL_BUCKET))] = acc.get(int(math.floor(d / WALL_BUCKET)), 0.0) + p * q
        if acc:
            k = max(acc, key=acc.get)
            px = mid * (1 + (k + 0.5) * WALL_BUCKET)
            out[f"wall_{side}_px"], out[f"wall_{side}_usd"], out[f"wall_{side}_dist"] = round(px, 0), round(acc[k], 0), round((px / mid - 1) * 100, 3)
    return out, feats


WALL_USD = 50.0                  # registro dei muri (data/book_walls.csv): fasce da 50 $ di prezzo
WALL_RANGE = 0.03                # entro ±3% dal mid della fonte
WALL_TOP = 3                     # i 3 maggiori cluster per lato e per exchange
WALL_BASE = ["ts", "exchange", "side", "price", "usd", "x_mean", "dist_pct", "cover_pct"]
# esito del muro, scritto dal giro SUCCESSIVO (approssimazione oraria, vedi settle_walls): outcome, ora e minuti trascorsi,
# $ nella stessa fascia alla foto dopo, % rimasta, minimo/massimo del prezzo nell'intervallo (riportati sulla fonte) e loro origine
WALL_OUT = ["outcome", "out_ts", "out_min", "usd_next", "remain_pct", "px_low", "px_high", "range_src"]
WALL_COLS = WALL_BASE + WALL_OUT


def book_walls(name: str, bids, asks, ts: str, band: float = WALL_USD, rng: float = WALL_RANGE, top: int = WALL_TOP) -> list[dict]:
    """I `top` maggiori cluster sopra (ask) e sotto (bid) il mid di UN book, in fasce di `band` $ entro ±rng. Per lato:
    prezzo = centro della fascia, usd = Σ prezzo·quantità, x_mean = usd / media delle fasce del lato (fasce vuote = 0,
    solo fino a dove arriva il book), dist_pct dal mid, cover_pct = copertura del book sul lato (≤ 3%)."""
    if not bids or not asks:
        return []
    mid = (bids[0][0] + asks[0][0]) / 2
    out = []
    for side, lv in (("bid", bids), ("ask", asks)):
        acc: dict[int, float] = {}
        for p, q in lv:
            if abs(p / mid - 1) <= rng:
                k = int(math.floor(p / band))
                acc[k] = acc.get(k, 0.0) + p * q
        if not acc:
            continue
        lo_k = int(math.floor(mid * (1 - rng) / band)) if side == "bid" else int(math.floor(mid / band))
        hi_k = int(math.floor(mid / band)) if side == "bid" else int(math.floor(mid * (1 + rng) / band))
        edge = min(p for p, _ in lv if abs(p / mid - 1) <= rng) if side == "bid" else max(p for p, _ in lv if abs(p / mid - 1) <= rng)
        ke = int(math.floor(edge / band))
        lo_k, hi_k = (max(lo_k, ke), hi_k) if side == "bid" else (lo_k, min(hi_k, ke))   # solo la parte coperta dal book
        mean = sum(acc.values()) / max(1, hi_k - lo_k + 1)
        cover = abs(edge / mid - 1) * 100
        for k in sorted(acc, key=acc.get, reverse=True)[:top]:
            px = (k + 0.5) * band
            out.append({"ts": ts, "exchange": name, "side": side, "price": round(px, 0), "usd": round(acc[k], 0),
                        "x_mean": round(acc[k] / mean, 2) if mean > 0 else None, "dist_pct": round((px / mid - 1) * 100, 3),
                        "cover_pct": round(cover, 2)})
    return out


DUP_MIN = 20                     # due giri a meno di 20 minuti: stesso giro, nessuna riga nuova
WALL_GONE = 0.70                 # "ritirato": alla foto dopo manca almeno il 70% dei $ della fascia
WALL_MAX_GAP_MIN = 360           # giro precedente più vecchio di 6 ore: esito "scaduto" (il confronto orario non ha più senso)
RANGE_MAX_BASIS = 0.005          # massimo/minimo riportati sul prezzo della fonte solo se la base è entro lo 0,5%
OUTCOMES = ("eseguito", "ritirato", "presente", "incerto", "non_verificabile", "scaduto")


def band_usd(levels, price: float, band: float = WALL_USD) -> float:
    """$ di un lato del book nella fascia [price − band/2, price + band/2) (la stessa di book_walls: price = centro)."""
    lo, hi = price - band / 2, price + band / 2
    return float(sum(p * q for p, q in levels if lo <= p < hi))


def settle_walls(prev: list[dict], books: dict, rng: dict | None, band: float = WALL_USD, gone: float = WALL_GONE) -> list[dict]:
    """Esito dei muri del giro PRECEDENTE (righe di book_walls) contro il book di adesso e il minimo/massimo dell'intervallo.

    `rng` = {"low", "high", "close", "src"} dalle candele (price_range) oppure None: allora si usano solo i due prezzi delle
    foto (range_src "solo_foto": i tocchi in mezzo NON si vedono). Minimo/massimo sono di una borsa spot: si riportano sul
    prezzo di ogni fonte con il rapporto mid della fonte / ultima chiusura (USD, USDT e perpetui hanno basi diverse).
    Per ogni muro (fascia di `band` $ centrata su price):
    - "eseguito": il prezzo ha attraversato tutta la fascia (minimo ≤ bordo basso per un bid, massimo ≥ bordo alto per un ask);
    - "ritirato": il prezzo NON ha raggiunto la fascia e nel book di adesso ne resta ≤ 30% (scomparso ≥ 70%);
    - "presente": ne resta > 30%;
    - "incerto": il prezzo è entrato nella fascia senza attraversarla e ne resta ≤ 30% (eseguito in parte o tolto: non si distingue);
    - "non_verificabile": la fonte adesso manca o il suo book non arriva più a quel prezzo, e il prezzo non l'ha attraversato.
    APPROSSIMAZIONE GROSSOLANA (due foto a un'ora di distanza): un muro tolto e rimesso risulta "presente", uno spostato di
    una fascia risulta "ritirato", uno eseguito e ricostituito resta "eseguito". Sono etichette da validare, non fatti."""
    out = []
    for r in prev:
        ex, side, px, usd0 = r["exchange"], r["side"], float(r["price"]), float(r["usd"])
        bk = books.get(ex)
        mid = (bk[0][0][0] + bk[1][0][0]) / 2 if bk and bk[0] and bk[1] else None
        try:
            mid0 = px / (1 + float(r["dist_pct"]) / 100)      # mid della fonte quando il muro è stato registrato
        except (KeyError, TypeError, ValueError):
            mid0 = None
        ends = [v for v in (mid0, mid) if v]
        lo = hi = None
        src = ""
        if rng and rng.get("low") and rng.get("high"):
            k = mid / rng["close"] if mid and rng.get("close") and abs(mid / rng["close"] - 1) <= RANGE_MAX_BASIS else 1.0
            lo, hi, src = min([rng["low"] * k] + ends), max([rng["high"] * k] + ends), rng.get("src") or "candele"
        elif ends:
            lo, hi, src = min(ends), max(ends), "solo_foto"
        b_lo, b_hi = px - band / 2, px + band / 2
        crossed = touched = False
        if lo is not None:
            crossed = lo <= b_lo if side == "bid" else hi >= b_hi
            touched = lo <= b_hi if side == "bid" else hi >= b_lo
        usd1 = None
        if bk and mid is not None:
            lv = bk[0] if side == "bid" else bk[1]
            covered = lv[-1][0] <= b_lo if side == "bid" else lv[-1][0] >= b_hi   # il book arriva fino in fondo alla fascia
            if covered or (mid < b_hi if side == "bid" else mid > b_lo):          # oppure il mid è già dentro/oltre la fascia
                usd1 = band_usd(lv, px, band)
        remain = usd1 / usd0 if usd1 is not None and usd0 > 0 else None
        if crossed:
            oc = "eseguito"
        elif remain is None or lo is None:
            oc = "non_verificabile"
        elif remain <= 1 - gone:
            oc = "incerto" if touched else "ritirato"
        else:
            oc = "presente"
        out.append({"outcome": oc, "usd_next": None if usd1 is None else round(usd1, 0),
                    "remain_pct": None if remain is None else round(remain * 100, 1),
                    "px_low": None if lo is None else round(lo, 1), "px_high": None if hi is None else round(hi, 1), "range_src": src})
    return out


def range_from_candles(candles: list[tuple], start_ms: float, end_ms: float, step_ms: float = 60_000, min_cover: float = 0.8) -> dict | None:
    """Minimo, massimo e ultima chiusura delle candele (t_apertura_ms, high, low, close) che toccano [start, end].
    None se non ce ne sono, se sono incoerenti o se coprono meno dell'80% dell'intervallo (dati incompleti: si passa alla riserva)."""
    sel = sorted(c for c in candles if c[0] + step_ms > start_ms and c[0] <= end_ms)
    if not sel or any(not (c[2] > 0 and c[1] >= c[2] and c[2] <= c[3] <= c[1]) for c in sel):
        return None
    if len({c[0] for c in sel}) * step_ms < min_cover * (end_ms - start_ms):
        return None
    return {"low": float(min(c[2] for c in sel)), "high": float(max(c[1] for c in sel)), "close": float(sel[-1][3]), "n": len(sel)}


def _candles_binance(a: int, b: int, step: int):
    j = _s.get("https://data-api.binance.vision/api/v3/klines", timeout=20,
               params={"symbol": "BTCUSDT", "interval": "1m" if step == 60 else "5m", "startTime": a - step * 1000, "endTime": b, "limit": 1000}).json()
    return [(int(c[0]), float(c[2]), float(c[3]), float(c[4])) for c in j]


def _candles_okx(a: int, b: int, step: int):
    out, after = [], b + 1
    for _ in range(3):   # 300 candele a pagina, dalla più recente
        j = _s.get("https://www.okx.com/api/v5/market/candles", timeout=20,
                   params={"instId": "BTC-USDT", "bar": "1m" if step == 60 else "5m", "after": after, "limit": 300}).json()["data"]
        out += [(int(c[0]), float(c[2]), float(c[3]), float(c[4])) for c in j]
        if not j or min(int(c[0]) for c in j) <= a - step * 1000:
            break
        after = min(int(c[0]) for c in j)
    return out


def _candles_coinbase(a: int, b: int, step: int):
    iso = lambda ms: pd.Timestamp(ms, unit="ms").strftime("%Y-%m-%dT%H:%M:%SZ")   # noqa: E731
    j = _s.get("https://api.exchange.coinbase.com/products/BTC-USD/candles", timeout=20,
               params={"granularity": step, "start": iso(a - step * 1000), "end": iso(b)}).json()
    return [(int(c[0]) * 1000, float(c[2]), float(c[1]), float(c[4])) for c in j]   # [t, low, high, open, close, volume]


CANDLE_SOURCES = {"binance_spot": _candles_binance, "okx_spot": _candles_okx, "coinbase": _candles_coinbase}


def price_range(start: pd.Timestamp, end: pd.Timestamp, data_dir=None, sources: dict | None = None) -> dict | None:
    """Minimo/massimo del prezzo spot fra due giri: candele da 1 minuto (5 minuti oltre le 4 ore) della prima fonte che
    risponde con dati completi (Binance spot via data-api, poi OKX spot, poi Coinbase: tutte raggiungibili dai runner USA);
    ultima riserva le candele orarie locali data/spot_1h.csv (intervallo più largo del vero, marcato "largo").
    None se nessuna fonte copre l'intervallo: chi chiama ripiega sui soli prezzi delle due foto e lo segna."""
    a, b = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    step = 60 if b - a <= 4 * 3_600_000 else 300
    for name, fn in (sources if sources is not None else CANDLE_SOURCES).items():
        try:
            r = range_from_candles(fn(a, b, step), a, b, step * 1000)
            if r:
                return {**r, "src": f"{name}_{step // 60}m"}
            print(f"[orderbook] candele {name}: assenti o incomplete per l'intervallo")
        except Exception as e:  # noqa: BLE001
            print(f"[orderbook] candele {name} non disponibili ({type(e).__name__})")
    try:
        if data_dir is not None and (data_dir / "spot_1h.csv").exists():
            h = pd.read_csv(data_dir / "spot_1h.csv").tail(48)
            c = [(int(pd.Timestamp(t).timestamp() * 1000), float(hi), float(lo), float(cl)) for t, hi, lo, cl in zip(h["t"], h["high"], h["low"], h["close"])]
            r = range_from_candles(c, a, b, 3_600_000)
            if r:
                return {**r, "src": "spot_1h_locale_largo"}
    except Exception as e:  # noqa: BLE001
        print(f"[orderbook] candele orarie locali non lette ({type(e).__name__})")
    return None


def _read_log(path, cols: list[str]) -> pd.DataFrame:
    """Registro CSV letto come testo (i valori già scritti non si riformattano), con le colonne mancanti aggiunte vuote
    (schema vecchio). File assente o vuoto: tabella vuota. Righe con `ts` non valido: SOLO quelle si scartano e si conservano
    in un file a parte dal nome unico (<nome>.scartate-<istante>), le righe buone restano. File illeggibile o senza colonna
    `ts`: messo da parte intero con nome unico, si riparte."""
    stamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%S%f")
    if path.exists() and path.stat().st_size > 0:
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            if "ts" not in df.columns:
                raise ValueError("colonna ts assente")
            bad = pd.to_datetime(df["ts"], errors="coerce").isna()
            if bad.any():
                side = path.with_name(f"{path.name}.scartate-{stamp}")
                df[bad].to_csv(side, index=False)
                print(f"[orderbook] {path.name}: {int(bad.sum())} righe con ts non valido scartate e conservate in {side.name}")
                df = df[~bad].reset_index(drop=True)
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:  # noqa: BLE001
            bad = path.with_name(f"{path.name}.illeggibile-{stamp}")
            path.replace(bad)
            print(f"[orderbook] {path.name} illeggibile ({e!r}): messo da parte in {bad.name}, il registro riparte")
    return pd.DataFrame({c: pd.Series(dtype=str) for c in cols})


def _write_log(path, df: pd.DataFrame):
    tmp = path.with_name(path.name + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)


def _txt(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v)


def update_walls(data_dir, books: dict, now: pd.Timestamp, range_fn=None) -> tuple[list[dict], dict | None]:
    """Un giro del registro data/book_walls.csv: (1) dà l'esito ai muri ancora senza esito (quelli del giro precedente,
    settle_walls; `range_fn(inizio, fine)` dà minimo/massimo dalle candele, None = solo i prezzi delle due foto); (2) aggiunge
    i muri di ogni fonte valida di questo giro. Niente doppioni: a meno di 20 minuti dall'ultimo giro non si scrive nulla.
    Ritorna (muri di adesso, riepilogo degli esiti o None se non c'era nulla da valutare / giro ripetuto)."""
    path = data_dir / "book_walls.csv"
    ts = str(now.floor("s"))
    rows = [r for k in sorted(books) for r in book_walls(k, books[k][0], books[k][1], ts)]
    if not rows:
        print("[orderbook] muri: nessuna fonte valida, nessun muro nuovo registrato")
    df = _read_log(path, WALL_COLS)
    t = pd.to_datetime(df["ts"]) if len(df) else pd.Series(dtype="datetime64[ns]")
    if len(df) and now - t.max() < pd.Timedelta(minutes=DUP_MIN):
        return rows, None
    summary = None
    pend = df.index[df["outcome"] == ""] if len(df) else []
    for t0 in sorted(set(t[pend])) if len(pend) else []:
        idx = [i for i in pend if t[i] == t0]
        gap = (now - t0).total_seconds() / 60
        if gap > WALL_MAX_GAP_MIN:
            res = [{"outcome": "scaduto"}] * len(idx)
        else:
            rng = None
            if range_fn is not None:
                try:
                    rng = range_fn(t0, now)
                except Exception as e:  # noqa: BLE001
                    print(f"[orderbook] minimo/massimo dell'intervallo non disponibile ({e!r}): solo i prezzi delle foto")
            res = settle_walls([df.loc[i].to_dict() for i in idx], books, rng)
        for i, o in zip(idx, res):
            for c in WALL_OUT:
                df.at[i, c] = _txt(o.get(c))
            df.at[i, "out_ts"], df.at[i, "out_min"] = ts, f"{gap:.0f}"
        counts = {s: {o: 0 for o in OUTCOMES} for s in ("bid", "ask")}
        for i, o in zip(idx, res):
            if df.at[i, "side"] in counts:
                counts[df.at[i, "side"]][o["outcome"]] += 1
        summary = {"ts_prev": str(t0), "gap_min": round(gap), "n": len(idx), "counts": counts,
                   "range_src": ",".join(sorted({o.get("range_src") or "" for o in res} - {""}))}
        print(f"[orderbook] esito di {len(idx)} muri del giro {t0} ({gap:.0f} min fa, approssimazione oraria): "
              + ", ".join(f"{s} {' '.join(f'{k}={v}' for k, v in c.items() if v)}" for s, c in counts.items()))
    if rows:
        df = pd.concat([df, pd.DataFrame([{c: _txt(r.get(c)) for c in WALL_COLS} for r in rows])], ignore_index=True)
    if rows or summary:
        _write_log(path, df[WALL_COLS + [c for c in df.columns if c not in WALL_COLS]])
    return rows, summary


def log_walls(data_dir, books: dict, now: pd.Timestamp, range_fn=None) -> list[dict]:
    """Come update_walls, ma ritorna solo i muri di adesso."""
    return update_walls(data_dir, books, now, range_fn)[0]


# ------------------------------------------------------------------ registro del sentiment (data/book_sentiment.csv)
SENT_BAND = 1.0                  # I: ±1% dal mid (specifica fissa)
SENT_LIQ_MIN = 30                # L: liquidazioni degli ultimi 30 minuti (specifica fissa)
SENT_LIQ_MIN_USD = 250_000       # sotto questo totale in 30 minuti L (e S) restano vuoti: segno instabile (revisione 22/11)
SENT_W = 0.5                     # S = 0,5·I + 0,5·L (specifica fissa)
LIQ_MAX_AGE_MIN = 10             # ultima raccolta delle liquidazioni (stesso giro, pochi secondi prima) più vecchia di 10 minuti:
                                 # la finestra di 30 minuti non sarebbe coperta → L (e S) restano vuoti, non 0
SENT_COLS = ["ts", "price", "I", "L", "S", "n_src", "sources", "bid_usd", "ask_usd", "liq_short_usd", "liq_long_usd", "liq_n",
             "liq_src", "liq_age_min", "pulled_bid", "pulled_ask", "filled_bid", "filled_ask", "still_bid", "still_ask",
             "walls_prev", "walls_gap_min", "range_src", "dropped", "note"]


def imbalance(books: dict, pct: float = SENT_BAND) -> dict:
    """I = (bid_usd − ask_usd)/(bid_usd + ask_usd) entro ±pct% dal mid, sul book aggregato: $ sommati sulle fonti, ognuna
    misurata dal PROPRIO mid (USD, USDT e perpetui non si mescolano). Entrano solo le fonti il cui book copre ±pct% su
    entrambi i lati (una fonte corta sposterebbe lo squilibrio). I = None se non resta nessuna fonte."""
    B = A = 0.0
    used, short = [], []
    for k in sorted(books):
        bids, asks = books[k][0], books[k][1]
        if not bids or not asks:
            short.append(k)
            continue
        mid = (bids[0][0] + asks[0][0]) / 2
        lo, hi = mid * (1 - pct / 100), mid * (1 + pct / 100)
        if bids[-1][0] > lo or asks[-1][0] < hi:
            short.append(k)
            continue
        B += sum(p * q for p, q in bids if p >= lo)
        A += sum(p * q for p, q in asks if p <= hi)
        used.append(k)
    return {"I": (B - A) / (B + A) if B + A > 0 else None, "bid_usd": B, "ask_usd": A, "sources": used, "short": short}


def liq_imbalance(events: list[dict], now_ms: float, minutes: int = SENT_LIQ_MIN) -> dict:
    """L = (liquidazioni short − liquidazioni long)/(somma) in $ negli ultimi `minutes` minuti; 0 se non ce ne sono.
    side = lato LIQUIDATO (radar/liqsources): short liquidati = acquisti forzati → L > 0."""
    sh = lg = 0.0
    n, exs = 0, set()
    for e in events:
        if 0 <= now_ms - e["ts"] <= minutes * 60_000 and e["side"] in ("long", "short"):
            n += 1
            exs.add(e["exchange"])
            if e["side"] == "short":
                sh += e["usd"]
            else:
                lg += e["usd"]
    return {"L": (sh - lg) / (sh + lg) if sh + lg > 0 else 0.0, "short_usd": sh, "long_usd": lg, "n": n, "exchanges": sorted(exs)}


def load_liq(data_dir, now: pd.Timestamp) -> dict:
    """Liquidazioni reali già raccolte dal giro (radar/liqsources: data/liq_events = REST di OKX, Gate, Deribit, Kraken,
    dYdX, Lighter; data/liq_stream = raccoglitore WebSocket Binance/Bybit, se attivo). Niente rete. Ritorna eventi, fonti
    con raccolta riuscita ed età in minuti dell'ultima raccolta (da coverage.csv); events = None se la raccolta manca o è
    più vecchia di 10 minuti: in quel caso L non si calcola (uno 0 sarebbe un dato inventato)."""
    from . import liqsources as ls
    ev_dir, st_dir = data_dir / "liq_events", data_dir / "liq_stream"
    now_ms = int(now.timestamp() * 1000)
    age, srcs = None, []
    try:
        cov = pd.read_csv(ev_dir / "coverage.csv", usecols=["run", "exchange", "stato"])
        last = cov[cov["run"] == cov["run"].iloc[-1]]
        age = (now - pd.Timestamp(last["run"].iloc[0]).tz_convert(None)).total_seconds() / 60
        srcs = sorted(last.loc[last["stato"] == "ok", "exchange"])
    except Exception as e:  # noqa: BLE001
        print(f"[orderbook] copertura delle liquidazioni non letta ({type(e).__name__})")
    if age is None or age > LIQ_MAX_AGE_MIN or not srcs:
        return {"events": None, "sources": srcs, "age_min": age}
    events = ls.load(2, ev_dir)
    try:
        st = ls.stream_status(st_dir, now_ms)
        if st and not st["stale"]:
            events = ls.merge(events, ls.load_stream(2, st_dir, now_ms))
            srcs = srcs + ["stream_ws"]
    except Exception as e:  # noqa: BLE001
        print(f"[orderbook] raccoglitore WebSocket delle liquidazioni non letto ({type(e).__name__})")
    return {"events": events, "sources": srcs, "age_min": age}


def sentiment_row(now: pd.Timestamp, books: dict, liq: dict | None, outcomes: dict | None, dropped=()) -> dict:
    """Riga del registro del sentiment (funzione pura). `books` = book validi del giro (per Hyperliquid la versione grossa),
    `liq` = load_liq (None o events None = liquidazioni non disponibili: L e S vuoti), `outcomes` = riepilogo di update_walls
    (None = nessun muro valutato in questo giro: conteggi vuoti, non 0)."""
    im = imbalance(books)
    mids = [(b[0][0][0] + b[1][0][0]) / 2 for b in books.values() if b[0] and b[1]]
    notes = []
    row = {c: None for c in SENT_COLS}
    row.update({"ts": str(now.floor("s")), "price": round(float(np.median(mids)), 2) if mids else None,
                "I": None if im["I"] is None else round(im["I"], 4), "n_src": len(im["sources"]), "sources": "+".join(im["sources"]),
                "bid_usd": round(im["bid_usd"], 0) if im["sources"] else None, "ask_usd": round(im["ask_usd"], 0) if im["sources"] else None,
                "dropped": "+".join(sorted(dropped))})
    if im["short"]:
        notes.append("book sotto ±1%: " + "+".join(im["short"]))
    if im["I"] is None:
        notes.append("nessun book utile: I non calcolato")
    if liq and liq.get("events") is not None:
        lq = liq_imbalance(liq["events"], now.timestamp() * 1000)
        tot = lq["short_usd"] + lq["long_usd"]
        if 0 < tot < SENT_LIQ_MIN_USD:   # importi piccoli: il segno di L salta da −1 a +1 per un solo evento (revisione 22/11)
            notes.append(f"liquidazioni sotto {SENT_LIQ_MIN_USD:,.0f} $ in 30 minuti: L e S non calcolati".replace(",", "."))
        row.update({"L": None if 0 < tot < SENT_LIQ_MIN_USD else round(lq["L"], 4), "liq_short_usd": round(lq["short_usd"], 0), "liq_long_usd": round(lq["long_usd"], 0),
                    "liq_n": lq["n"], "liq_src": "+".join(liq.get("sources") or [])})
    else:
        notes.append("liquidazioni non aggiornate: L non calcolato")
    if liq and liq.get("age_min") is not None:
        row["liq_age_min"] = round(liq["age_min"])
    if row["I"] is not None and row["L"] is not None:
        row["S"] = round(SENT_W * row["I"] + (1 - SENT_W) * row["L"], 4)
    if outcomes:
        c = outcomes["counts"]
        for side in ("bid", "ask"):
            row[f"pulled_{side}"], row[f"filled_{side}"], row[f"still_{side}"] = c[side]["ritirato"], c[side]["eseguito"], c[side]["presente"]
        row.update({"walls_prev": outcomes["n"], "walls_gap_min": outcomes["gap_min"], "range_src": outcomes.get("range_src")})
    row["note"] = "; ".join(notes)
    return row


def log_sentiment(data_dir, now: pd.Timestamp, books: dict, extra: dict | None = None, outcomes: dict | None = None,
                  checks: dict | None = None, liq: dict | None = None) -> dict | None:
    """Aggiunge una riga a data/book_sentiment.csv (niente doppioni entro 20 minuti: ritorna None). La riga si scrive anche
    se mancano il book o le liquidazioni (campi vuoti e nota): un giro senza dati resta visibile nel registro."""
    path = data_dir / "book_sentiment.csv"
    df = _read_log(path, SENT_COLS)
    if len(df) and now - pd.to_datetime(df["ts"]).max() < pd.Timedelta(minutes=DUP_MIN):
        return None
    bk = {k: ((extra or {}).get(k, {}).get("coarse") or v) for k, v in books.items()}   # Hyperliquid: book grosso fino a ±3%
    if liq is None:
        try:
            liq = load_liq(data_dir, now)
        except Exception as e:  # noqa: BLE001
            print(f"[orderbook] liquidazioni non lette ({e!r}): L non calcolato")
    row = sentiment_row(now, bk, liq, outcomes, [k for k, v in (checks or {}).items() if v])
    df = pd.concat([df, pd.DataFrame([{c: _txt(row.get(c)) for c in SENT_COLS}])], ignore_index=True)
    _write_log(path, df[SENT_COLS + [c for c in df.columns if c not in SENT_COLS]])
    print(f"[orderbook] sentiment: I={row['I']} L={row['L']} S={row['S']} fonti={row['n_src']} ({row['sources'] or 'nessuna'})"
          + (f" · {row['note']}" if row["note"] else ""))
    return row


def label(df: pd.DataFrame, horizon: str) -> pd.Series:
    """Rendimento del mid fra ogni foto e la prima foto nella finestra dell'orizzonte (NaN se manca)."""
    lo, hi = HORIZONS[horizon]
    t = pd.to_datetime(df["ts"]).to_numpy()
    mid = df["mid"].to_numpy(float)
    out = np.full(len(df), np.nan)
    j = 0
    for i in range(len(df)):
        a, b = t[i] + np.timedelta64(lo, "m"), t[i] + np.timedelta64(hi, "m")
        j = max(j, i + 1)
        while j < len(df) and t[j] < a:
            j += 1
        if j < len(df) and t[j] <= b:
            out[i] = mid[j] / mid[i] - 1
    return pd.Series(out, index=df.index)


def _X(df: pd.DataFrame, mu=None, sd=None):
    X = df[FEATS].astype(float).fillna(0.0).to_numpy()
    if mu is None:
        mu, sd = X.mean(0), X.std(0) + 1e-9
    return (X - mu) / sd, mu, sd


def fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = L2, iters: int = 25) -> np.ndarray:
    """Logistica con intercetta e penalità L2 (Newton). Pesi [b0, b1..bk]."""
    Z = np.c_[np.ones(len(X)), X]
    w = np.zeros(Z.shape[1])
    R = np.eye(Z.shape[1]) * l2; R[0, 0] = 1e-6
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Z @ w))
        g = Z.T @ (p - y) + R @ w
        H = Z.T @ (Z * (p * (1 - p))[:, None]) + R
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def predict(model: dict | None, row: dict) -> dict:
    """Probabilità di rialzo a 1h e 4h per una riga di feature (0,5 se il modello non c'è o ha pochi dati)."""
    out = {}
    for hz in HORIZONS:
        m = (model or {}).get(hz)
        if not m or m.get("n", 0) < MIN_TRAIN:
            out[hz] = 0.5
            continue
        x = np.array([float(row.get(f) or 0.0) for f in FEATS])
        z = (x - np.array(m["mu"])) / np.array(m["sd"])
        out[hz] = round(float(1 / (1 + math.exp(-(m["w"][0] + z @ np.array(m["w"][1:]))))), 4)
    return out


def evaluate(df: pd.DataFrame) -> dict:
    """Registro fuori campione: accuratezza delle previsioni salvate contro i riferimenti, per orizzonte."""
    res = {}
    mom = np.sign(df["mid"].astype(float).pct_change().fillna(0).to_numpy())   # momentum: segno del movimento dall'ultima foto
    for hz in HORIZONS:
        y = label(df, hz).to_numpy()
        p = pd.to_numeric(df.get(f"p_{hz}"), errors="coerce").to_numpy() if f"p_{hz}" in df else np.full(len(df), np.nan)
        k = ~np.isnan(y) & ~np.isnan(p)
        up = y[k] > 0
        n = int(k.sum())
        if not n:
            res[hz] = {"n": 0}
            continue
        act = np.abs(p[k] - 0.5) >= 0.02                          # il modello "prende posizione"
        hit = ((p[k] > 0.5) == up)
        mm = mom[k]
        res[hz] = {"n": n, "up_rate": round(float(up.mean()) * 100, 1),
                   "model_acc": round(float(hit[act].mean()) * 100, 1) if act.any() else None, "model_n": int(act.sum()),
                   "always_up_acc": round(float(up.mean()) * 100, 1),
                   "momentum_acc": round(float(((mm > 0) == up)[mm != 0].mean()) * 100, 1) if (mm != 0).any() else None,
                   "brier": round(float(np.mean((p[k] - up) ** 2)), 4), "brier_05": 0.25}
    return res


WORKS_MIN_N = 30                 # verdetto "funziona?": almeno 30 previsioni fuori campione in cui il modello prende posizione
WORKS_MARGIN = 3.0               # e accuratezza ≥ max(sempre su, momentum) + 3 punti


def verdict(track: dict) -> dict:
    """Il motore funziona? Sì solo se, su almeno un orizzonte, ha ≥ 30 previsioni fuori campione con posizione e batte
    entrambi i riferimenti (sempre su, momentum) di almeno 3 punti. La dashboard lo mostra solo in quel caso."""
    per, best = {}, None
    for hz in HORIZONS:
        t = (track or {}).get(hz) or {}
        n, acc, lab = int(t.get("model_n") or 0), t.get("model_acc"), int(t.get("n") or 0)
        base = max([v for v in (t.get("always_up_acc"), t.get("momentum_acc")) if v is not None], default=None)
        ok = n >= WORKS_MIN_N and acc is not None and base is not None and acc >= base + WORKS_MARGIN
        per[hz] = {"ok": bool(ok), "n": lab, "n_pos": n, "need": WORKS_MIN_N, "edge": round(acc - base, 1) if acc is not None and base is not None else None}
        if best is None or lab > best:
            best = lab
    return {"works": any(v["ok"] for v in per.values()), "n": best or 0, "need": WORKS_MIN_N, "margin": WORKS_MARGIN, "per": per}   # n = casi etichettati


def learn(df: pd.DataFrame) -> dict:
    """Riaddestra la logistica su tutte le foto con esito noto; ritorna il modello per orizzonte."""
    model = {}
    for hz in HORIZONS:
        y = label(df, hz)
        k = y.notna().to_numpy()
        n = int(k.sum())
        if n < 5:
            model[hz] = {"n": n}
            continue
        X, mu, sd = _X(df[k])
        w = fit_logistic(X, (y[k].to_numpy() > 0).astype(float))
        model[hz] = {"n": n, "w": [round(float(v), 5) for v in w], "mu": [float(v) for v in mu], "sd": [float(v) for v in sd]}
    return model


# ------------------------------------------------------------------ giro orario
def snapshot(sources: dict | None = None) -> tuple[dict, dict, dict]:
    """Scarica e controlla tutte le fonti in parallelo. Ritorna (book validi, problemi per fonte, extra per fonte).
    Una fonte che non risponde o non supera i controlli non ferma le altre: resta fuori e il motivo finisce in `checks`."""
    sources = sources or SOURCES
    now = time.time()
    raw, errs = {}, {}
    def one(kv):
        k, fn = kv
        try:
            return k, fn(), None
        except Exception as e:  # noqa: BLE001
            return k, None, f"non raggiungibile ({type(e).__name__})"
    extra = {}
    with ThreadPoolExecutor(len(sources)) as ex:
        for k, v, e in ex.map(one, sources.items()):
            if v:
                raw[k] = tuple(v[:3])
                if len(v) > 3 and v[3]:
                    extra[k] = v[3]
            else:
                errs[k] = [e or "risposta vuota"]
    mids = {k: (b[0][0] + a[0][0]) / 2 for k, (b, a, _) in raw.items() if b and a}
    checks, good = {}, {}
    for k, (b, a, ts) in raw.items():
        others = [m for j, m in mids.items() if j != k]
        ref = float(np.median(others)) if others else None
        bad = check(k, b, a, ts, now, ref)
        checks[k] = bad
        if not bad:
            good[k] = (b, a)
    checks.update(errs)
    return good, checks, {k: v for k, v in extra.items() if k in good}


def update(data_dir, now: pd.Timestamp | None = None) -> dict:
    """Foto, controlli, previsione salvata, apprendimento ogni 4 ore. Ritorna il blocco per la dashboard."""
    now = now or pd.Timestamp.utcnow().tz_localize(None)
    path, mpath = data_dir / "orderbook.csv", data_dir / "ob_model.json"
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    try:
        state = json.loads(mpath.read_text()) if mpath.exists() else {}
    except Exception:  # noqa: BLE001
        state = {}
    good, checks, extra = snapshot()
    status = {k: ("ok" if not v else "; ".join(v)) for k, v in checks.items()}
    print(f"[orderbook] controlli: {status}")
    walls, outcomes, sentiment = [], None, None
    try:   # registro dei muri per exchange (data/book_walls.csv) ed esito dei muri del giro prima: un errore non tocca la foto
        walls, outcomes = update_walls(data_dir, good, now, range_fn=lambda a, b: price_range(a, b, data_dir))
    except Exception as e:  # noqa: BLE001
        print(f"[orderbook] registro dei muri non scritto: {e!r}")
    try:   # registro del sentiment (data/book_sentiment.csv): isolato, non tocca foto e modello
        sentiment = log_sentiment(data_dir, now, good, extra, outcomes, checks)
    except Exception as e:  # noqa: BLE001
        print(f"[orderbook] registro del sentiment non scritto: {e!r}")
    row = None
    photo = {k: v for k, v in good.items() if k not in LOG_ONLY}
    if len(photo) >= 2:
        agg, per = aggregate(photo)
        row = {"ts": str(now.floor("s")), **agg, "sources": ",".join(sorted(photo)), "dropped": ",".join(k for k in checks if checks[k] and k not in LOG_ONLY)}
        row.update({f"p_{hz}": p for hz, p in predict(state.get("model"), agg).items()})
        last = pd.to_datetime(df["ts"]).max() if len(df) else None
        if last is None or (now - last) >= pd.Timedelta(minutes=20):   # giro doppio delle 00:30: niente doppioni
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(path, index=False)
    else:
        per = {}
        print("[orderbook] meno di 2 fonti valide: nessuna foto salvata")
    last_learn = pd.Timestamp(state["learned"]) if state.get("learned") else None
    if len(df) and (now.hour % 4 == 0 or last_learn is None or now - last_learn >= pd.Timedelta(hours=4)) and \
            (last_learn is None or now - last_learn >= pd.Timedelta(minutes=50)):
        state["model"] = learn(df)
        state["track"] = evaluate(df)
        state["learned"] = str(now.floor("s"))
        state.setdefault("history", []).append({"t": state["learned"], **{hz: state["track"][hz] for hz in HORIZONS}})
        state["history"] = state["history"][-60:]
        mpath.write_text(json.dumps(state, indent=1))
    cur = row or (df.iloc[-1].to_dict() if len(df) else {})
    pred = {hz: cur.get(f"p_{hz}") for hz in HORIZONS}
    return {"ts": cur.get("ts"), "mid": cur.get("mid"), "now": {k: cur.get(k) for k in cur if k.startswith(("imb_", "bid_", "ask_", "wall_", "spread", "micro", "n_src", "src_"))},
            "pred": pred, "checks": status, "track": state.get("track", {}), "verdict": verdict(state.get("track", {})), "learned": state.get("learned"),
            "model": {hz: {"n": (state.get("model") or {}).get(hz, {}).get("n", 0), "w": (state.get("model") or {}).get(hz, {}).get("w")} for hz in HORIZONS},
            "walls": walls, "wall_outcomes": outcomes, "sentiment": sentiment, "feats": FEATS, "rows": int(len(df)), "since": str(df["ts"].iloc[0]) if len(df) else None,
            "per_source": {k: {"mid": round(v["mid"], 1), "spread_bps": round(v["spread_bps"], 2), "imb_0.5": (round((v["bid_0.5"] - v["ask_0.5"]) / (v["bid_0.5"] + v["ask_0.5"]), 3) if v.get("bid_0.5") else None)} for k, v in per.items()}}
