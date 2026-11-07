"""Motore del book di BTC (orario): fotografie dei book di più exchange, controlli dei dati, lettura e apprendimento ogni 4 ore.

Ogni giro (radar.cli daily, ogni ora):
1. scarica i book da fonti raggiungibili dai runner USA (Coinbase, Kraken, OKX perp e spot, Binance spot via data-api);
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


SOURCES = {"coinbase": _coinbase, "kraken": _kraken, "okx_perp": lambda: _okx("BTC-USDT-SWAP", 0.01),
           "okx_spot": lambda: _okx("BTC-USDT", 1.0), "binance_spot": _binance}


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
def snapshot() -> tuple[dict, dict]:
    now = time.time()
    raw, errs = {}, {}
    def one(kv):
        k, fn = kv
        try:
            return k, fn(), None
        except Exception as e:  # noqa: BLE001
            return k, None, f"non raggiungibile ({type(e).__name__})"
    with ThreadPoolExecutor(len(SOURCES)) as ex:
        for k, v, e in ex.map(one, SOURCES.items()):
            if v:
                raw[k] = v
            else:
                errs[k] = [e]
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
    return good, checks


def update(data_dir, now: pd.Timestamp | None = None) -> dict:
    """Foto, controlli, previsione salvata, apprendimento ogni 4 ore. Ritorna il blocco per la dashboard."""
    now = now or pd.Timestamp.utcnow().tz_localize(None)
    path, mpath = data_dir / "orderbook.csv", data_dir / "ob_model.json"
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    try:
        state = json.loads(mpath.read_text()) if mpath.exists() else {}
    except Exception:  # noqa: BLE001
        state = {}
    good, checks = snapshot()
    status = {k: ("ok" if not v else "; ".join(v)) for k, v in checks.items()}
    print(f"[orderbook] controlli: {status}")
    row = None
    if len(good) >= 2:
        agg, per = aggregate(good)
        row = {"ts": str(now.floor("s")), **agg, "sources": ",".join(sorted(good)), "dropped": ",".join(k for k in checks if checks[k])}
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
            "pred": pred, "checks": status, "track": state.get("track", {}), "learned": state.get("learned"),
            "model": {hz: {"n": (state.get("model") or {}).get(hz, {}).get("n", 0), "w": (state.get("model") or {}).get(hz, {}).get("w")} for hz in HORIZONS},
            "feats": FEATS, "rows": int(len(df)), "since": str(df["ts"].iloc[0]) if len(df) else None,
            "per_source": {k: {"mid": round(v["mid"], 1), "spread_bps": round(v["spread_bps"], 2), "imb_0.5": (round((v["bid_0.5"] - v["ask_0.5"]) / (v["bid_0.5"] + v["ask_0.5"]), 3) if v.get("bid_0.5") else None)} for k, v in per.items()}}
