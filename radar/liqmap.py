"""Mappa delle liquidazioni vicine di BTC (STIMA) + prezzi di liquidazione reali delle balene Hyperliquid.

Metodo standard delle "heatmap" di liquidazione, ricalcolato ogni ora:
1. per ogni ora degli ultimi LOOKBACK_H l'aumento di open interest (in $) è considerato posizioni nuove aperte al prezzo medio
   dell'ora, metà long e metà short, distribuite su leve tipiche (LEVERAGE, con margine di mantenimento MM);
2. ogni posizione ha un prezzo di liquidazione: long entry·(1 − 1/L + MM) sotto, short entry·(1 + 1/L − MM) sopra;
3. un livello sparisce quando il prezzo lo attraversa (quelle posizioni sono già state liquidate); quando l'OI scende tutte le
   posizioni aperte si riducono in proporzione (chiusure);
4. il risultato è una mappa in $ per fasce di prezzo dello 0,25%: sotto il prezzo i long da liquidare, sopra gli short.
Fonti: Binance USDT-M (OI a 5 minuti dall'archivio data.binance.vision, fino a ieri: l'API fapi è bloccata dagli USA) e OKX
BTC-USDT-SWAP (OI orario fino all'ora corrente). Le ore dopo la fine dell'archivio Binance si coprono con le candele spot
Binance (data-api.binance.vision, fino all'ora chiusa) e un OI Binance STIMATO dalle variazioni % dell'OI OKX (extend_oi):
la fonte dichiara sempre fin dove arriva l'OI vero ("oi_until") e quante ore sono stimate ("extended_h"). È una STIMA: leve e lati veri delle posizioni non sono pubblici.
Hyperliquid è l'unico exchange dove le posizioni sono pubbliche: per i conti più grandi (classifica) e i wallet seguiti da
whalebot si leggono i prezzi di liquidazione VERI delle posizioni BTC. Ogni ora radar/liqsnap.py registra in data/liqsnap/ i livelli
reali di Hyperliquid (tutti i conti ≥ $1M a rotazione) e Lighter, in fasce dello 0,25% (chiave "onchain" del risultato).
La ricerca (research/liquidazioni, lezione 81) non trova un vantaggio di trading nella mappa: è contesto, non segnale.
"""
from __future__ import annotations

import io
import json
import math
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import numpy as np
import pandas as pd
import requests

LEVERAGE = ((10, 0.30), (25, 0.30), (50, 0.25), (100, 0.15))   # leve tipiche dei perp e quota del nozionale
MM = 0.005           # margine di mantenimento (primo scaglione Binance/OKX ~0,4–0,5%)
BIN = 0.0025         # fasce dello 0,25%
LOOKBACK_H = 21 * 24  # 3 settimane di storia oraria
RANGE = 0.15         # mappa entro ±15% dal prezzo
SIG = 0.30           # cluster "significativo": almeno il 30% del più grande dello stesso lato entro ±10%
HL_API = "https://api.hyperliquid.xyz/info"
HL_LB = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
# wallet seguiti da github.com/andreagalanti91/whalebot (worker.js, WALLETS)
WHALEBOT = {
    "0x237152b038d88f4156a0cd71090462de7e3f0883": "Cluster-1", "0xbd1c84113c6deb5044be0c2221f9e9403811ff0e": "Cluster-2",
    "0xec7f9f5b31b8f5da6ac6c0973bbd496e16f9df39": "Cluster-3", "0xc7290b4b308431a985fa9e3e8a335c2f7650517c": "Ribassista",
    "0x9c16bc8f1104e4d2f72267eb981fa12de7cc4a6f": "Inversore", "0xbd334a55db91617545e8d1b09941e036ad8e4200": "Petroliere",
    "0x2d99fe0f36c1aebd28a1a2c0e82e8ca13c2ea351": "Rotatore",
}
TOP_ACCOUNTS = 80    # conti più grandi della classifica Hyperliquid da leggere (oltre a quelli di whalebot)
BIG_ACCOUNT_USD = 1e6  # conti della classifica coperti a rotazione dal registratore on-chain (radar/liqsnap.py)


# ------------------------------------------------------------------ funzioni pure (testate in tests/test_liqmap.py)
def liq_price(entry: float, lev: float, side: str, mm: float = MM) -> float:
    """Prezzo di liquidazione di una posizione isolata: long sotto l'ingresso, short sopra."""
    return entry * (1 - 1 / lev + mm) if side == "long" else entry * (1 + 1 / lev - mm)


def _bin(p, base: float) -> np.ndarray:
    return np.floor(np.log(np.asarray(p, float) / base) / math.log1p(BIN)).astype(int)


def build(h: pd.DataFrame, leverage=LEVERAGE, mm: float = MM, long_share: float = 0.5) -> dict:
    """Mappa delle liquidazioni stimate da candele orarie con open interest in $ (colonne high, low, close, oi_usd).

    Ritorna {"base", "long", "short"}: array in $ per fascia (fascia i = prezzi [base·(1+BIN)^i, base·(1+BIN)^(i+1))).
    I long liquidabili restano sotto il minimo più recente, gli short sopra il massimo più recente.
    """
    h = h[["high", "low", "close", "oi_usd"]].dropna()
    base = float(h["low"].min()) * 0.4
    n = int(_bin(float(h["high"].max()) * 2.2, base)) + 2
    L, S = np.zeros(n), np.zeros(n)
    hi, lo, cl, oi = (h[c].to_numpy(float) for c in ("high", "low", "close", "oi_usd"))
    bl, bh = _bin(lo, base), _bin(hi, base)
    tp = (hi + lo + cl) / 3
    tiers = [(lev, w, int(_bin(liq_price(1.0, lev, "long", mm) * 1.0, 1.0)), int(_bin(liq_price(1.0, lev, "short", mm), 1.0))) for lev, w in leverage]
    for i in range(1, len(h)):
        L[bl[i]:] = 0.0          # long con liquidazione sopra il minimo dell'ora: già liquidati
        S[:bh[i] + 1] = 0.0      # short con liquidazione sotto il massimo dell'ora: già liquidati
        d = oi[i] - oi[i - 1]
        if d < 0 and oi[i - 1] > 0:
            k = max(0.0, 1 + d / oi[i - 1]); L *= k; S *= k
        elif d > 0:
            e = int(_bin(tp[i], base))
            for lev, w, ol, os_ in tiers:
                jl, js = e + ol, e + os_
                if 0 <= jl < n and jl < bl[i]:
                    L[jl] += d * long_share * w
                if 0 <= js < n and js > bh[i]:
                    S[js] += d * (1 - long_share) * w
    return {"base": base, "long": L, "short": S}


def extend_oi(b: pd.DataFrame, ref: pd.DataFrame | None, max_h: int = 48) -> tuple[pd.DataFrame, dict]:
    """Prolunga l'OI di `b` (candele con oi_usd vuoto dopo la fine dell'archivio) con le variazioni % dell'OI di `ref`.

    oi_b(t) = oi_b(ultima ora vera) × oi_ref(t) / oi_ref(ultima ora vera); solo ore consecutive presenti in `ref`, al massimo
    `max_h`. Nessuna ora inventata: dove manca `ref` la serie si ferma. Ritorna (candele, info con "oi_until" e "extended_h").
    """
    b = b.dropna(subset=["high", "low", "close"])
    real = b["oi_usd"].dropna()
    if real.empty:
        raise ValueError("nessun open interest")
    last = real.index[-1]
    head, tail = b.loc[:last].dropna(), b.loc[b.index > last]
    info = {"oi_until": str(last), "extended_h": 0}
    if ref is None or not len(ref) or not len(tail) or last not in ref.index or not ref.at[last, "oi_usd"] > 0:
        return head, info
    est = ref["oi_usd"].reindex(tail.index) * (float(real.iloc[-1]) / float(ref.at[last, "oi_usd"]))
    gap = est.isna().to_numpy()
    n = min(int(gap.argmax()) if gap.any() else len(est), max_h)
    if n == 0:
        return head, info
    tail = tail.iloc[:n].copy()
    tail["oi_usd"] = est.iloc[:n].to_numpy()
    info.update(extended_h=n, extended_with="okx")
    return pd.concat([head, tail]), info


def window(m: dict, price: float, rng: float = RANGE) -> pd.DataFrame:
    """Fasce entro ±rng dal prezzo: prezzo medio della fascia, $ long (sotto) e short (sopra)."""
    n = len(m["long"])
    px = m["base"] * (1 + BIN) ** (np.arange(n) + 0.5)
    k = (px >= price * (1 - rng)) & (px <= price * (1 + rng))
    return pd.DataFrame({"price": px[k], "long": m["long"][k], "short": m["short"][k]})


def combine(maps: list[pd.DataFrame], ref: pd.DataFrame | None = None) -> pd.DataFrame:
    """Somma mappe di exchange diversi sulla griglia di `ref` (o della prima mappa): fasce ricampionate per prezzo."""
    maps = [x for x in maps if x is not None and len(x)]
    if not maps:
        return pd.DataFrame(columns=["price", "long", "short"])
    ref = (maps[0] if ref is None else ref)[["price"]].copy()
    edges = np.r_[ref["price"].to_numpy() / math.sqrt(1 + BIN), ref["price"].iloc[-1] * math.sqrt(1 + BIN)]
    out = np.zeros((len(ref), 2))
    for x in maps:
        j = np.searchsorted(edges, x["price"].to_numpy()) - 1
        ok = (j >= 0) & (j < len(ref))
        np.add.at(out, j[ok], x[["long", "short"]].to_numpy()[ok])
    ref["long"], ref["short"] = out[:, 0], out[:, 1]
    return ref.reset_index(drop=True)


def clusters(w: pd.DataFrame, price: float, side: str, rng: float = 0.10, sig: float = SIG) -> list[dict]:
    """Cluster di un lato (long sotto / short sopra): picchi della somma su 3 fasce, dal più vicino al più lontano.

    Ognuno ha prezzo, $ (somma delle 3 fasce), distanza % e "sig" (≥ sig × il più grande del lato entro ±rng).
    """
    col = "long" if side == "long" else "short"
    x = w[(w["price"] < price) if side == "long" else (w["price"] > price)]
    x = x[(x["price"] - price).abs() <= rng * price]
    if len(x) < 3 or x[col].sum() <= 0:
        return []
    v = x[col].to_numpy(float)
    band = np.convolve(v, np.ones(3), mode="same")
    peaks = [i for i in range(len(band)) if band[i] > 0 and (i == 0 or band[i] >= band[i - 1]) and (i == len(band) - 1 or band[i] > band[i + 1])]
    top = max(band[i] for i in peaks)
    out = [{"price": round(float(x["price"].iloc[i]), 0), "usd": round(float(band[i]), 0),
            "dist_pct": round((float(x["price"].iloc[i]) / price - 1) * 100, 2), "sig": bool(band[i] >= sig * top),
            "rel": round(float(band[i] / top), 2)} for i in peaks]
    return sorted(out, key=lambda o: abs(o["dist_pct"]))


def imbalance(w: pd.DataFrame, price: float, rng: float) -> dict:
    """$ di short liquidabili sopra e long sotto entro ±rng; squilibrio (short − long) / totale in %."""
    k = (w["price"] - price).abs() <= rng * price
    s, l = float(w.loc[k & (w["price"] > price), "short"].sum()), float(w.loc[k & (w["price"] < price), "long"].sum())
    return {"short_above": round(s, 0), "long_below": round(l, 0), "pct": round((s - l) / (s + l) * 100, 1) if s + l > 0 else 0.0}


def confluence(c: dict, levels: dict | None, pad: float = 0.005) -> str | None:
    """Nome del livello S/R (R1, S2, …) la cui zona, allargata dello 0,5%, contiene il cluster."""
    if not levels:
        return None
    for key, tag in (("resistances", "R"), ("supports", "S")):
        for i, o in enumerate(levels.get(key, [])):
            if o["lo"] * (1 - pad) <= c["price"] <= o["hi"] * (1 + pad):
                return f"{tag}{i + 1}"
    return None


def _nf(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _pc(x: float, d: int = 1) -> str:
    return (f"{x:+.{d}f}%").replace(".", ",").replace("-", "−")


def summarize(w: pd.DataFrame, price: float, levels: dict | None = None, whales: list | None = None) -> dict:
    """Riassunto per Oggi e per la pagina: cluster vicini, più grandi, squilibrio, confluenza con S/R, zona probabile, lettura."""
    up, dn = clusters(w, price, "short"), clusters(w, price, "long")
    for c in up + dn:
        c["sr"] = confluence(c, levels)
    na = next((c for c in up if c["sig"]), None)
    nb = next((c for c in dn if c["sig"]), None)
    big_a = max(up, key=lambda c: c["usd"], default=None)
    big_b = max(dn, key=lambda c: c["usd"], default=None)
    im5, im10 = imbalance(w, price, 0.05), imbalance(w, price, 0.10)
    # zona probabile: fra la prima barriera sopra (cluster significativo o resistenza di forza ≥ 3) e la prima sotto
    lv = levels or {}
    r3 = next((o for o in lv.get("resistances", []) if o.get("strength", 0) >= 3), None)
    s3 = next((o for o in lv.get("supports", []) if o.get("strength", 0) >= 3), None)
    hi_c = [x for x in ((na or {}).get("price"), (r3 or {}).get("price")) if x]
    lo_c = [x for x in ((nb or {}).get("price"), (s3 or {}).get("price")) if x]
    zone = {"lo": min(lo_c, key=lambda p: price - p) if lo_c else None, "hi": min(hi_c, key=lambda p: p - price) if hi_c else None}
    side = "sopra (short da liquidare)" if im5["pct"] > 0 else "sotto (long da liquidare)"
    txt = []
    if na or nb:
        near = min([c for c in (na, nb) if c], key=lambda c: abs(c["dist_pct"]))
        txt.append(f"Cluster significativo più vicino {'sopra' if near is na else 'sotto'} a {_nf(near['price'])} $ ({_pc(near['dist_pct'])})"
                   + (f", in confluenza con {near['sr']}" if near.get("sr") else "") + ".")
    if abs(im5["pct"]) >= 15:
        txt.append(f"Entro ±5% pesano di più le liquidazioni {side}: squilibrio {_pc(im5['pct'], 0)}.")
    else:
        txt.append(f"Entro ±5% liquidazioni sopra e sotto quasi in equilibrio ({_pc(im5['pct'], 0)}).")
    txt.append("Stima, non segnale: nei test dal 2021 il prezzo non raggiunge i cluster più spesso di un livello qualsiasi alla stessa "
               "distanza; lo squilibrio pesa solo sulle 12–24 ore (in gran parte momentum), non sui giorni (lezione 81).")
    return {"price": round(price, 0), "above": up[:8], "below": dn[:8], "nearest_above": na, "nearest_below": nb,
            "largest_above": big_a, "largest_below": big_b, "imb5": im5, "imb10": im10, "zone": zone, "read": " ".join(txt)}


def whale_levels(states: dict[str, dict], names: dict[str, str], price: float, coin: str = "BTC") -> list[dict]:
    """Posizioni BTC (DEX principale) dei conti Hyperliquid con il prezzo di liquidazione vero, dalla più vicina."""
    out = []
    for a, st in states.items():
        for ap in (st or {}).get("assetPositions", []):
            p = ap.get("position", {})
            if p.get("coin") != coin:
                continue
            sz = float(p.get("szi") or 0)
            if not sz:
                continue
            liq = float(p["liquidationPx"]) if p.get("liquidationPx") else None
            out.append({"who": names.get(a) or (a[:6] + "…" + a[-4:]), "addr": a, "side": "long" if sz > 0 else "short", "btc": round(abs(sz), 3),
                        "ntl": round(abs(sz) * price, 0), "entry": round(float(p.get("entryPx") or 0), 1), "liq": round(liq, 0) if liq else None,
                        "lev": (p.get("leverage") or {}).get("value"), "dist_pct": round((liq / price - 1) * 100, 1) if liq else None,
                        "upnl": round(float(p.get("unrealizedPnl") or 0), 0), "tracked": a in WHALEBOT})
    return sorted(out, key=lambda o: abs(o["dist_pct"]) if o["dist_pct"] is not None else 1e9)


def feed_summary(liq: pd.DataFrame, now: pd.Timestamp, events: int = 25) -> dict:
    """Liquidazioni reali raccolte (data/liquidations.csv, OKX): totali 1h/4h/24h/7g long vs short, barre orarie 72h, ultimi eventi."""
    liq = liq[liq["time"] <= now]
    tot = {}
    for k, hrs in (("1h", 1), ("4h", 4), ("24h", 24), ("7g", 168)):
        x = liq[liq["time"] > now - pd.Timedelta(hours=hrs)]
        tot[k] = {"long": round(float(x.loc[x["liquidated"] == "long", "usd"].sum()), 0),
                  "short": round(float(x.loc[x["liquidated"] == "short", "usd"].sum()), 0), "n": int(len(x))}
    x = liq[liq["time"] > now - pd.Timedelta(hours=72)].copy()
    x["h"] = x["time"].dt.floor("h")
    g = x.pivot_table(index="h", columns="liquidated", values="usd", aggfunc="sum").fillna(0)
    hours = [[str(t), round(float(r.get("long", 0)), 0), round(float(r.get("short", 0)), 0)] for t, r in g.iterrows()]
    last = liq.sort_values("time").tail(events).iloc[::-1]
    ev = [[str(t)[:19], s, round(float(b), 4), round(float(p), 1), round(float(u), 0)] for t, s, b, p, u in
          zip(last["time"], last["liquidated"], last["btc"], last["price"], last["usd"])]
    big = liq[liq["time"] > now - pd.Timedelta(days=7)].nlargest(5, "usd")
    return {"since": str(liq["time"].min())[:16] if len(liq) else None, "totals": tot, "hours": hours, "events": ev,
            "largest": [[str(t)[:16], s, round(float(u), 0), round(float(p), 1)] for t, s, u, p in zip(big["time"], big["liquidated"], big["usd"], big["price"])]}


# ------------------------------------------------------------------ dati (rete)
_s = requests.Session()


def _get(url, params=None, timeout=25):
    r = _s.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r


def okx_hourly(hours: int = LOOKBACK_H + 24) -> pd.DataFrame:
    """OKX BTC-USDT-SWAP: OI orario in $ (rubik) + candele orarie, fino all'ora corrente."""
    rows, end = [], None
    while len(rows) < hours:
        p = {"instId": "BTC-USDT-SWAP", "period": "1H", "limit": 100}
        if end:
            p["end"] = end
        d = _get("https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history", p).json().get("data") or []
        if not d:
            break
        rows += d; end = d[-1][0]; time.sleep(0.25)
    oi = pd.Series({pd.to_datetime(int(r[0]), unit="ms"): float(r[3]) for r in rows}).sort_index()
    ks, after = [], None
    while len(ks) < hours:
        p = {"instId": "BTC-USDT-SWAP", "bar": "1H", "limit": 100}
        if after:
            p["after"] = after
        d = _get("https://www.okx.com/api/v5/market/history-candles", p).json().get("data") or []
        if not d:
            break
        ks += d; after = d[-1][0]; time.sleep(0.15)
    k = pd.DataFrame([[pd.to_datetime(int(r[0]), unit="ms"), float(r[2]), float(r[3]), float(r[4])] for r in ks],
                     columns=["t", "high", "low", "close"]).drop_duplicates("t").set_index("t").sort_index()
    # OI rubik alle hh:00 = stato all'inizio dell'ora: si usa quello della candela successiva come OI alla chiusura (niente futuro)
    k["oi_usd"] = oi.shift(-1).reindex(k.index)
    return k.dropna().iloc[-hours:]


def binance_hourly(days: int = LOOKBACK_H // 24 + 1) -> pd.DataFrame:
    """Binance USDT-M: OI a 5 minuti dall'archivio giornaliero (fino a ieri) e candele orarie spot (data-api.binance.vision).
    Le candele arrivano fino all'ultima ora chiusa; dopo la fine dell'archivio oi_usd resta vuoto (vedi extend_oi)."""
    def day(d: date):
        try:
            r = _s.get(f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{d:%Y-%m-%d}.zip", timeout=30)
            if r.status_code != 200:
                return None
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                return pd.read_csv(z.open(z.namelist()[0]), usecols=["create_time", "sum_open_interest_value"])
        except Exception:  # noqa: BLE001
            return None
    today = pd.Timestamp.utcnow().tz_localize(None).normalize().date()
    with ThreadPoolExecutor(8) as ex:
        fr = [x for x in ex.map(day, [today - timedelta(days=i) for i in range(1, days + 2)]) if x is not None]
    if not fr:
        raise RuntimeError("archivio Binance non raggiungibile")
    m = pd.concat(fr)
    m["t"] = pd.to_datetime(m["create_time"])
    v = pd.to_numeric(m["sum_open_interest_value"], errors="coerce")
    oi = v.where(v > 0).groupby(m["t"].dt.floor("h")).last()   # ultimo valore dentro l'ora (≤ chiusura): nessun dato dal futuro
    start = int((pd.Timestamp(oi.index.min())).timestamp() * 1000)
    kl = _get("https://data-api.binance.vision/api/v3/klines", {"symbol": "BTCUSDT", "interval": "1h", "startTime": start, "limit": 1000}).json()
    now_ms = time.time() * 1000
    kl = [r for r in kl if int(r[6]) < now_ms]   # solo ore chiuse
    k = pd.DataFrame([[pd.to_datetime(r[0], unit="ms"), float(r[2]), float(r[3]), float(r[4])] for r in kl], columns=["t", "high", "low", "close"]).set_index("t")
    k["oi_usd"] = oi.reindex(k.index).ffill(limit=2)
    k.loc[k.index > oi.dropna().index.max(), "oi_usd"] = np.nan   # dopo l'archivio nessun OI vero (niente ffill)
    return k


def _hl(body: dict):
    for back in (2, 4, None):   # limite 1.200 di peso al minuto per IP: su 429 si aspetta e si riprova
        r = _s.post(HL_API, json=body, timeout=20)
        if r.status_code == 429 and back:
            time.sleep(back)
            continue
        r.raise_for_status()
        return r.json()


_LB: dict = {}   # classifica scaricata in questo processo (la usano anche radar/scout.py e la cache qui sotto)


def hl_leaderboard(max_age_s: float = 3600) -> list[dict]:
    """Classifica completa di Hyperliquid (~40 MB, ~48k conti), una sola volta per processo/ora."""
    if not _LB.get("rows") or time.time() - _LB["ts"] > max_age_s:
        rows = _get(HL_LB, timeout=90).json().get("leaderboardRows", [])
        _LB.update(rows=rows, ts=time.time())
    return _LB["rows"]


def hl_accounts(cache_path, max_age_h: float = 24) -> dict[str, str]:
    """Indirizzi da leggere: wallet di whalebot + i TOP_ACCOUNTS conti più grandi della classifica (cache giornaliera)."""
    names = dict(WHALEBOT)
    try:
        c = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    except Exception:  # noqa: BLE001
        c = {}
    if not c.get("ts") or time.time() - c["ts"] > max_age_h * 3600 or "big" not in c:
        try:
            rows = sorted(hl_leaderboard(), key=lambda r: -float(r.get("accountValue") or 0))
            # "big": tutti i conti ≥ $1M, letti a rotazione dal registratore radar/liqsnap.py
            c = {"ts": time.time(), "accounts": [[r["ethAddress"], r.get("displayName")] for r in rows[:TOP_ACCOUNTS]],
                 "big": [r["ethAddress"].lower() for r in rows if float(r.get("accountValue") or 0) >= BIG_ACCOUNT_USD]}
            cache_path.write_text(json.dumps(c))
        except Exception as e:  # noqa: BLE001
            print(f"[liqmap] classifica Hyperliquid non letta: {type(e).__name__}")
    for a, n in c.get("accounts", []):
        names.setdefault(a.lower(), n or None)
    return names


def hl_big(cache_path) -> list[str]:
    """Indirizzi della classifica con accountValue ≥ BIG_ACCOUNT_USD (dalla cache di hl_accounts)."""
    try:
        return list(json.loads(cache_path.read_text()).get("big", []))
    except Exception:  # noqa: BLE001
        return []


def hl_states(addrs: list[str]) -> dict[str, dict]:
    def one(a):
        try:
            return a, _hl({"type": "clearinghouseState", "user": a})
        except Exception:  # noqa: BLE001
            return a, None
    with ThreadPoolExecutor(6) as ex:
        return {a: s for a, s in ex.map(one, addrs) if s}


# ------------------------------------------------------------------ giro orario
def update(levels: dict | None, data_dir) -> dict:
    """Calcola la mappa (Binance + OKX), le balene Hyperliquid e i totali delle liquidazioni raccolte. Fallisce in modo morbido."""
    maps, src = [], {}
    price, okx = None, None
    now = pd.Timestamp.utcnow().tz_localize(None)
    for name, fn in (("okx", okx_hourly), ("binance", binance_hourly)):
        try:
            h = fn()
            info = {}
            if name == "okx":
                okx = h
                info = {"oi_until": str(h.index[-1]), "extended_h": 0}
            else:   # ore dopo la fine dell'archivio Binance: OI stimato dalle variazioni OKX (dichiarato in extended_h)
                h, info = extend_oi(h, okx)
            h = h.iloc[-LOOKBACK_H:]
            m = build(h)
            if price is None:
                price = float(h["close"].iloc[-1])
            asof = h.index[-1] + pd.Timedelta(hours=1)   # chiusura dell'ultima ora usata
            src[name] = {"ok": True, "until": str(h.index[-1]), "as_of": str(asof), "age_h": round((now - asof) / pd.Timedelta(hours=1), 1),
                         "hours": int(len(h)), "oi_usd": round(float(h["oi_usd"].iloc[-1]), 0), **info}
            if src[name]["age_h"] > 3:
                print(f"[liqmap] {name}: dati vecchi di {src[name]['age_h']} ore (fino a {asof})")
            if info.get("extended_h"):
                print(f"[liqmap] {name}: OI vero fino a {info['oi_until']}, {info['extended_h']} ore stimate con OKX")
            maps.append((name, m))
        except Exception as e:  # noqa: BLE001
            src[name] = {"ok": False, "error": type(e).__name__}
            print(f"[liqmap] {name} non disponibile: {e!r}")
    if not maps:
        raise RuntimeError("nessuna fonte per la mappa delle liquidazioni")
    if src.get("okx", {}).get("ok") and src.get("binance", {}).get("ok"):   # controllo di coerenza fra le fonti
        r = src["binance"]["oi_usd"] / src["okx"]["oi_usd"] if src["okx"]["oi_usd"] else float("nan")
        if not 0.5 <= r <= 20:
            print(f"[liqmap] OI Binance/OKX incoerente (rapporto {r:.2f}): controllare le fonti")
    ws = [window(m, price, RANGE + 0.02) for _, m in maps]
    w = combine(ws)
    w = w[(w["price"] - price).abs() <= RANGE * price].reset_index(drop=True)
    per = {name: combine([x], ref=w) for (name, _), x in zip(maps, ws)}   # stessa griglia: la pagina può sostituire una fonte dal vivo
    whales, n_acc, names, st = [], 0, {}, {}
    try:
        names = hl_accounts(data_dir / "hl_accounts.json")
        st = hl_states(list(names))
        n_acc = len(st)
        whales = whale_levels(st, names, price)
    except Exception as e:  # noqa: BLE001
        print(f"[liqmap] Hyperliquid non disponibile: {e!r}")
    onchain = None
    if names:   # registratore orario dei livelli di liquidazione reali (Hyperliquid + Lighter); names vuoto solo nei test
        try:
            from . import liqsnap
            onchain = liqsnap.record(data_dir, st, hl_big(data_dir / "hl_accounts.json"), price)
        except Exception as e:  # noqa: BLE001
            print(f"[liqmap] registratore on-chain non riuscito: {e!r}")
    out = summarize(w, price, levels, whales)
    out.update({
        "ts": str(pd.Timestamp.utcnow().tz_localize(None).floor("min")), "sources": src,
        # "as of" per fonte (chiusura dell'ultima ora usata) e fin dove arriva l'OI vero: etichette della pagina
        "as_of": {k: {"data": v["as_of"], "oi": v["oi_until"], "estimated_h": v["extended_h"]} for k, v in src.items() if v.get("ok")},
        "bins": [[round(p, 0), round(l, 0), round(s, 0)] for p, l, s in zip(w["price"], w["long"], w["short"])],
        "bins_src": {k: [[round(l, 0), round(s, 0)] for l, s in zip(x["long"], x["short"])] for k, x in per.items()},
        "whales": whales[:30], "whale_accounts": n_acc, "onchain": onchain,
        "params": {"leverage": [list(x) for x in LEVERAGE], "mm": MM, "bin_pct": BIN * 100, "lookback_days": LOOKBACK_H // 24},
    })
    try:
        lf = data_dir / "liquidations.csv"
        if lf.exists():
            liq = pd.read_csv(lf, parse_dates=["time"])
            out["feed"] = feed_summary(liq, pd.Timestamp.utcnow().tz_localize(None))
    except Exception as e:  # noqa: BLE001
        print(f"[liqmap] storico liquidazioni non letto: {e!r}")
    return out
