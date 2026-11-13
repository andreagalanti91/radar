"""Ultima cascata di liquidazioni (ultime 24 ore) e prossime fasce dense sotto/sopra. CONTESTO, non segnale (lezione 92).

Cascata = movimento ≥ MIN_MOVE (3%) in ≤ MAX_H (8) candele orarie che attraversa almeno MIN_CROSSED (2) fasce dense della
mappa stimata DELLA VIGILIA (radar/liqmap: fascia densa = cluster con rel ≥ liqmap.SIG, cioè ≥ 30% del più grande del lato
entro ±10%). Regole meccaniche (research/liq_fasce/README.md, studio del 13/11/2026):
- candele: data/spot_1h.csv (Binance spot, data-api.binance.vision: raggiungibile dai runner USA), solo ore chiuse;
- per ogni ora j il punto di partenza è l'apertura più alta (long) / più bassa (short) delle MAX_H ore fino a j; fra le ore con
  apertura entro una fascia (0,25%) da quell'estremo si prende la più vicina a j (inizio vero della discesa, non un massimo
  di qualche ora prima uguale a meno di rumore);
- le ore j consecutive con movimento ≥ 3% formano un episodio; la fine è l'ora dell'estremo (minimo per i long liquidati);
- vale l'episodio che finisce più di recente, se finisce nelle ultime 24 ore.
Mappa della vigilia: a ogni giro si salva in data/liqmap_prev.json una copia piccola della mappa (solo le fasce dense, ultime
KEEP_H ore); per una cascata iniziata all'ora S si usa l'ultima mappa con dati fino a S (non più vecchia di VIGIL_MAX_H ore).
Senza mappa della vigilia la cascata non si può verificare: active False e messaggio nel log (nessun dato inventato).
Livelli reali on-chain: data/liqsnap/{hl,lighter}_YYYY-MM.csv.gz, fotografia prima (≤ 20 minuti dopo l'inizio) e dopo (dalla
chiusura dell'ultima ora): $ di posizioni dal lato liquidato con liquidazione fra estremo e partenza, prima meno dopo.
Liquidazioni reali: data/liq_events (radar/liqsources: OKX, Gate, Deribit, Kraken, dYdX, Lighter) + data/liq_stream (Binance,
Bybit, OKX via WebSocket da radar/liqstream.py su una VM europea, solo se attivo).
"""
from __future__ import annotations

import gzip
import io
import json
from pathlib import Path

import pandas as pd
import requests

MIN_MOVE = 0.03
MAX_H = 8
MIN_CROSSED = 2
WINDOW_H = 24
BIN = 0.0025            # fascia della mappa (liqmap.BIN)
SIG = 0.30              # fascia densa (liqmap.SIG)
KEEP_H = 36             # ore di mappe salvate in liqmap_prev.json
VIGIL_MAX_H = 12        # mappa della vigilia al massimo 12 ore prima dell'inizio
SR_PAD = 0.005          # zona S/R allargata dello 0,5% (come liqmap.confluence)
SR_NEAR = 0.01          # S/R "vicina" a una fascia: entro l'1%
STOP_BAND = 0.0075      # estremo "fermato su una fascia": entro 3 fasce da una fascia densa non attraversata
SNAP_BEFORE_TOL_MIN = 20
SNAP_MAX_GAP_H = 6
STALE_H = 3
PREV_FILE = "liqmap_prev.json"
COVERAGE_NOTE = "I dati reali coprono solo una parte del mercato (Binance e Bybit esclusi)."
NOTE = "Contesto, non è un segnale (lezione 92)."


def _hfmt(t) -> str:
    return pd.Timestamp(t).strftime("%Y-%m-%d %H:00")


# ------------------------------------------------------------------ funzioni pure (tests/test_liqcascade.py)
def clean_candles(c: pd.DataFrame | None) -> pd.DataFrame | None:
    """Candele orarie valide (indice orario crescente, prezzi positivi e coerenti); None se mancano."""
    if c is None or not len(c):
        return None
    c = c[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()
    c = c[(c > 0).all(axis=1) & (c["high"] >= c[["open", "close", "low"]].max(axis=1)) & (c["low"] <= c[["open", "close"]].min(axis=1))]
    c = c[~c.index.duplicated(keep="last")].sort_index()
    return c if len(c) else None


def _episodes(c: pd.DataFrame, side: str, min_move: float, max_h: int) -> list[dict]:
    o, hi, lo = (c[k].to_numpy(float) for k in ("open", "high", "low"))
    cand = []
    for j in range(len(c)):
        a = max(0, j - max_h + 1)
        if side == "long":
            ref = max(o[a:j + 1])
            i = max(k for k in range(a, j + 1) if o[k] >= ref * (1 - BIN))
            m = lo[j] / o[i] - 1
            ok = m <= -min_move
        else:
            ref = min(o[a:j + 1])
            i = max(k for k in range(a, j + 1) if o[k] <= ref * (1 + BIN))
            m = hi[j] / o[i] - 1
            ok = m >= min_move
        if ok:
            cand.append((j, i))
    eps, cur = [], []
    for j, i in cand:
        if cur and j != cur[-1][0] + 1:
            eps.append(cur); cur = []
        cur.append((j, i))
    if cur:
        eps.append(cur)
    out = []
    for e in eps:
        j, i = (min if side == "long" else max)(e, key=lambda x: lo[x[0]] if side == "long" else hi[x[0]])
        a = max(0, j - max_h + 1)   # partenza ricalcolata sull'ora dell'estremo (stessa regola)
        if side == "long":
            ref = max(o[a:j + 1]); i = max(k for k in range(a, j + 1) if o[k] >= ref * (1 - BIN))
            ext = lo[j]
        else:
            ref = min(o[a:j + 1]); i = max(k for k in range(a, j + 1) if o[k] <= ref * (1 + BIN))
            ext = hi[j]
        out.append({"side": side, "i": i, "j": j, "start": c.index[i], "end": c.index[j], "start_px": float(o[i]),
                    "end_px": float(c["close"].iloc[j]), "extreme_px": float(ext), "move_pct": (ext / o[i] - 1) * 100})
    return out


def detect(c: pd.DataFrame, now: pd.Timestamp, min_move: float = MIN_MOVE, max_h: int = MAX_H, window_h: int = WINDOW_H) -> dict | None:
    """Ultimo movimento ≥ min_move in ≤ max_h ore finito nelle ultime window_h ore (candidato cascata), o None."""
    c = c[(c.index >= now - pd.Timedelta(hours=window_h + max_h)) & (c.index + pd.Timedelta(hours=1) <= now)]
    if len(c) < 2:
        return None
    eps = [e for s in ("long", "short") for e in _episodes(c, s, min_move, max_h)
           if e["end"] + pd.Timedelta(hours=1) > now - pd.Timedelta(hours=window_h)]
    if not eps:
        return None
    return max(eps, key=lambda e: (e["end"], abs(e["move_pct"])))


def dense_bands(bins: list, price: float, rng: float = 0.10) -> dict:
    """Fasce dense di una mappa liqmap (bins [[prezzo, long $, short $]]): {"long": [[px, usd, rel]], "short": [...]}."""
    from .liqmap import clusters
    w = pd.DataFrame(bins, columns=["price", "long", "short"]).astype(float)
    out = {}
    for side in ("long", "short"):
        cl = clusters(w, price, side, rng=rng, sig=SIG)
        out[side] = [[c["price"], c["usd"], c["rel"]] for c in cl if c["rel"] >= 0.2]
    return out


def vigil_map(maps: list[dict], start: pd.Timestamp, max_h: float = VIGIL_MAX_H) -> dict | None:
    """Ultima mappa con dati fino all'inizio della cascata (ts ≤ start), non più vecchia di max_h ore."""
    ok = [m for m in maps if pd.Timestamp(m["ts"]) <= start and start - pd.Timestamp(m["ts"]) <= pd.Timedelta(hours=max_h)]
    return max(ok, key=lambda m: m["ts"]) if ok else None


def crossed_bands(vmap: dict, ev: dict) -> list[dict]:
    """Fasce dense della vigilia dal lato liquidato fra partenza ed estremo (attraversate)."""
    if ev["side"] == "long":
        xs = [b for b in vmap.get("long", []) if b[2] >= SIG and ev["extreme_px"] <= b[0] < ev["start_px"]]
    else:
        xs = [b for b in vmap.get("short", []) if b[2] >= SIG and ev["start_px"] < b[0] <= ev["extreme_px"]]
    return [{"px": float(b[0]), "usd": float(b[1])} for b in sorted(xs, key=lambda b: abs(b[0] - ev["start_px"]))]


def _zones(levels: dict | None, kinds=("supports", "resistances")) -> list[tuple[str, dict]]:
    return [(k, z) for k in kinds for z in (levels or {}).get(k, []) or [] if z.get("lo") and z.get("hi")]


def stopped_at(ev: dict, levels: dict | None, vmap: dict | None) -> dict:
    """Dove si è fermata: zona S/R (allargata dello 0,5%) che contiene l'estremo, altrimenti una fascia densa della vigilia
    non attraversata entro lo 0,75%, altrimenti nessuno."""
    x = ev["extreme_px"]
    kind = "supports" if ev["side"] == "long" else "resistances"
    for _, z in _zones(levels, (kind,)):
        if z["lo"] * (1 - SR_PAD) <= x <= z["hi"] * (1 + SR_PAD):
            return {"kind": "supporto" if kind == "supports" else "resistenza", "lo": float(z["lo"]), "hi": float(z["hi"])}
    if vmap:
        bs = [b for b in vmap.get(ev["side"], []) if b[2] >= SIG and abs(b[0] / x - 1) <= STOP_BAND
              and (b[0] < x if ev["side"] == "long" else b[0] > x)]
        if bs:
            b = min(bs, key=lambda b: abs(b[0] - x))
            return {"kind": "fascia", "lo": round(b[0] * (1 - 1.5 * BIN), 0), "hi": round(b[0] * (1 + 1.5 * BIN), 0)}
    return {"kind": "nessuno", "lo": None, "hi": None}


def next_band(c: dict | None, price: float, levels: dict | None) -> dict | None:
    """Prossima fascia densa (cluster liqmap) con la zona S/R più vicina entro l'1%."""
    if not c or not c.get("price") or not price:
        return None
    px = float(c["price"])
    sr, best = None, None
    for _, z in _zones(levels):
        d = 0.0 if z["lo"] <= px <= z["hi"] else min(abs(px - z["lo"]), abs(px - z["hi"])) / px
        if d <= SR_NEAR and (best is None or d < best):
            best, sr = d, {"lo": float(z["lo"]), "hi": float(z["hi"])}
    return {"px": px, "usd": float(c.get("usd") or 0), "dist_pct": round((px / price - 1) * 100, 2), "sr": sr}


def read_snaps(d: Path, months: list[str]) -> pd.DataFrame:
    """Fotografie on-chain (radar/liqsnap) dei mesi indicati, tutte le borse: ts, ex, mid, k, long_usd, short_usd."""
    fr = []
    for ex in ("hl", "lighter"):
        for m in months:
            p = d / f"{ex}_{m}.csv.gz"
            if p.exists():
                fr.append(pd.read_csv(io.BytesIO(gzip.decompress(p.read_bytes()))).assign(ex=ex))
    if not fr:
        return pd.DataFrame(columns=["ts", "ex", "mid", "k", "long_usd", "short_usd"])
    s = pd.concat(fr, ignore_index=True)
    s["t"] = pd.to_datetime(s["ts"])
    return s


def onchain_gone(s: pd.DataFrame, ev: dict, step: float = BIN) -> float | None:
    """$ dal lato liquidato con liquidazione fra estremo e partenza: fotografia prima − fotografia dopo (per borsa, poi somma).
    None se manca la fotografia di Hyperliquid prima o dopo."""
    if s is None or not len(s):
        return None
    start = pd.Timestamp(ev["start"]); after_t = pd.Timestamp(ev["end"]) + pd.Timedelta(hours=1)
    lo, hi = sorted((ev["extreme_px"], ev["start_px"]))
    col = "long_usd" if ev["side"] == "long" else "short_usd"
    tot, have_hl = 0.0, False
    for ex, g in s.groupby("ex"):
        b = g[(g["t"] <= start + pd.Timedelta(minutes=SNAP_BEFORE_TOL_MIN)) & (g["t"] >= start - pd.Timedelta(hours=SNAP_MAX_GAP_H))]
        a = g[(g["t"] >= after_t) & (g["t"] <= after_t + pd.Timedelta(hours=SNAP_MAX_GAP_H))]
        if not len(b) or not len(a):
            continue
        val = []
        for x in (b[b["t"] == b["t"].max()], a[a["t"] == a["t"].min()]):
            blo, bhi = x["mid"] * (1 + x["k"] * step), x["mid"] * (1 + (x["k"] + 1) * step)
            val.append(float(x.loc[(bhi > lo) & (blo < hi), col].sum()))
        tot += val[0] - val[1]
        have_hl |= ex == "hl"
    return round(tot, 0) if have_hl else None


def real_liqs(events: list[dict], ev: dict) -> dict:
    """Liquidazioni reali registrate (radar/liqsources) fra l'inizio e la chiusura dell'ultima ora della cascata."""
    a = pd.Timestamp(ev["start"]).value // 10**6
    b = (pd.Timestamp(ev["end"]) + pd.Timedelta(hours=1)).value // 10**6
    x = [e for e in events or [] if a <= int(e["ts"]) < b]
    return {"long": round(sum(e["usd"] for e in x if e["side"] == "long"), 0),
            "short": round(sum(e["usd"] for e in x if e["side"] == "short"), 0),
            "exchanges": len({e["exchange"] for e in x})}


def save_map(path: Path, liqmap_out: dict | None, keep_h: int = KEEP_H) -> list[dict]:
    """Aggiunge la mappa di questo giro (solo le fasce dense) a liqmap_prev.json; tiene le ultime keep_h ore. Ritorna le mappe."""
    maps = load_maps(path)
    if liqmap_out and liqmap_out.get("bins") and liqmap_out.get("price"):
        asof = [v.get("data") for v in (liqmap_out.get("as_of") or {}).values() if v.get("data")]
        ts = _hfmt(max(pd.Timestamp(t) for t in asof)) if asof else _hfmt(pd.Timestamp(liqmap_out.get("ts")).floor("h"))
        price = float(liqmap_out["price"])
        entry = {"ts": ts, "price": round(price, 0), **dense_bands(liqmap_out["bins"], price)}
        maps = [m for m in maps if m["ts"] != ts] + [entry]
        last = max(pd.Timestamp(m["ts"]) for m in maps)
        maps = sorted((m for m in maps if last - pd.Timestamp(m["ts"]) <= pd.Timedelta(hours=keep_h)), key=lambda m: m["ts"])
        path.write_text('{"maps": [\n' + ",\n".join(json.dumps(m, separators=(",", ":")) for m in maps) + "\n]}\n")
    return maps


def load_maps(path: Path) -> list[dict]:
    try:
        return list(json.loads(path.read_text()).get("maps", [])) if path.exists() else []
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] {path.name} non leggibile ({type(e).__name__}): storico delle mappe ripartito da zero")
        return []


def build(report: dict, candles: pd.DataFrame | None, maps: list[dict], snaps: pd.DataFrame | None, events: list[dict] | None,
          now: pd.Timestamp) -> dict | None:
    """Risultato per la dashboard (schema fisso, vedi docstring del modulo). None se mancano candele o mappa attuale."""
    lm = (report or {}).get("liqmap")
    c = clean_candles(candles)
    if not lm or c is None:
        return None
    levels = report.get("levels")
    price = float(lm.get("price") or c["close"].iloc[-1])
    base = {"next_below": next_band(lm.get("nearest_below"), price, levels),
            "next_above": next_band(lm.get("nearest_above"), price, levels),
            "note": NOTE, "updated_utc": now.strftime("%Y-%m-%d %H:%M")}
    ev = detect(c, now)
    if ev is None:
        return {"active": False, **base}
    vm = vigil_map(maps, pd.Timestamp(ev["start"]))
    if vm is None:
        print(f"[cascata] movimento {ev['move_pct']:+.1f}% {_hfmt(ev['start'])}→{_hfmt(ev['end'])}: nessuna mappa della vigilia "
              f"salvata (data/{PREV_FILE}), cascata non verificabile")
        return {"active": False, **base}
    crossed = crossed_bands(vm, ev)
    if len(crossed) < MIN_CROSSED:
        print(f"[cascata] movimento {ev['move_pct']:+.1f}% {_hfmt(ev['start'])}→{_hfmt(ev['end'])}: attraversate {len(crossed)} "
              f"fasce dense della mappa delle {vm['ts']} (minimo {MIN_CROSSED}): non è una cascata")
        return {"active": False, **base}
    try:
        gone = onchain_gone(snaps, ev)
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] fotografie on-chain non lette: {e!r}")
        gone = None
    out = {"active": True, "side": ev["side"], "start_utc": _hfmt(ev["start"]), "end_utc": _hfmt(ev["end"]),
           "start_px": round(ev["start_px"], 1), "end_px": round(ev["end_px"], 1), "extreme_px": round(ev["extreme_px"], 1),
           "move_pct": round(ev["move_pct"], 2), "crossed": crossed, "crossed_usd": round(sum(b["usd"] for b in crossed), 0),
           "stopped_at": stopped_at(ev, levels, vm), "next_below": base["next_below"], "next_above": base["next_above"],
           "onchain_gone_usd": gone, "real_usd": real_liqs(events, ev), "coverage_note": COVERAGE_NOTE, "note": NOTE,
           "updated_utc": base["updated_utc"]}
    print(f"[cascata] {ev['side']} {out['start_utc']}→{out['end_utc']} {out['start_px']:,.0f}→{out['extreme_px']:,.0f} "
          f"({out['move_pct']:+.1f}%), {len(crossed)} fasce dense attraversate (${out['crossed_usd'] / 1e6:,.0f}M stimati, mappa "
          f"{vm['ts']}), fermata: {out['stopped_at']['kind']}, on-chain spariti "
          f"{'n.d.' if gone is None else f'${gone / 1e6:,.0f}M'}, reali long ${out['real_usd']['long'] / 1e6:,.1f}M "
          f"short ${out['real_usd']['short'] / 1e6:,.1f}M ({out['real_usd']['exchanges']} exchange)")
    return out


# ------------------------------------------------------------------ giro orario (file locali, nessuna rete)
def _candles(data_dir: Path) -> pd.DataFrame | None:
    p = data_dir / "spot_1h.csv"
    if not p.exists():
        return None
    c = pd.read_csv(p, parse_dates=["t"]).set_index("t")
    c = c.iloc[-(WINDOW_H + MAX_H + 48):]
    # spot_1h.csv contiene solo giorni chiusi (lo usa il backtest): le ore di oggi si leggono qui, solo ore chiuse
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params={"symbol": "BTCUSDT", "interval": "1h", "limit": WINDOW_H + MAX_H + 2}, timeout=15)
        rows = r.json() if r.ok else []
        if rows:
            h = pd.DataFrame([x[:5] for x in rows], columns=["t", "open", "high", "low", "close"])
            h["t"] = pd.to_datetime(pd.to_numeric(h["t"]), unit="ms")
            h = h.set_index("t").astype(float)
            h = h[h.index + pd.Timedelta(hours=1) <= pd.Timestamp.utcnow().tz_localize(None)]   # solo ore chiuse
            c = pd.concat([c[c.index < h.index[0]], h]) if len(h) else c
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] ore di oggi non lette ({type(e).__name__}): si usa solo data/spot_1h.csv")
    return c


def update(report: dict, data_dir, now: pd.Timestamp | None = None) -> dict | None:
    """Giro orario: salva la mappa di oggi in liqmap_prev.json e calcola la cascata. Fallisce in modo morbido (None)."""
    d = Path(data_dir)
    now = now or pd.Timestamp.utcnow().tz_localize(None)
    maps = load_maps(d / PREV_FILE)
    c = _candles(d)
    if c is None or not len(c):
        print("[cascata] candele orarie assenti (data/spot_1h.csv): niente da valutare")
    else:
        age = (now - (c.index[-1] + pd.Timedelta(hours=1))) / pd.Timedelta(hours=1)
        if age > WINDOW_H:
            print(f"[cascata] candele orarie ferme da {age:.0f} ore: niente da valutare")
            c = None
        elif age > STALE_H:
            print(f"[cascata] candele orarie vecchie di {age:.1f} ore (ultima {c.index[-1]})")
    if not (report or {}).get("liqmap"):
        print("[cascata] mappa delle liquidazioni assente in questo giro")
    snaps = None
    try:
        months = sorted({now.strftime("%Y-%m"), (now - pd.Timedelta(days=2)).strftime("%Y-%m")})
        snaps = read_snaps(d / "liqsnap", months)
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] fotografie on-chain non lette: {e!r}")
    events = None
    try:
        from .liqsources import load, load_stream, merge
        events = load(2, d / "liq_events")
        try:   # Binance/Bybit (raccoglitore WebSocket radar/liqstream.py su VM europea), se i file ci sono
            events = merge(events, load_stream(72, d / "liq_stream"))
        except Exception as e:  # noqa: BLE001
            print(f"[cascata] raccoglitore WebSocket non letto: {e!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] liquidazioni reali non lette: {e!r}")
    out = build(report, c, maps, snaps, events, now)
    try:   # dopo il calcolo: la mappa di questo giro serve alle cascate dei prossimi giri
        save_map(d / PREV_FILE, (report or {}).get("liqmap"))
    except Exception as e:  # noqa: BLE001
        print(f"[cascata] mappa non salvata in {PREV_FILE}: {e!r}")
    return out
