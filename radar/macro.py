"""Chiusura giornaliera multi-asset: CONTESTO descrittivo, non segnale (la posizione la decide W3.2).

Fonti (pubbliche, gratuite, raggiungibili sia dal container sia dai runner GitHub negli USA; verificate il 22/11/2026):
- S&P 500, Nasdaq Composite, VIX, Treasury 10 anni, dollaro (indice ampio della Fed, settimanale con ~1 settimana di ritardo):
  FRED, fredgraph.csv (serie SP500, NASDAQCOM, VIXCLS, DGS10, DTWEXBGS);
- oro: Kraken PAXGUSD (token Paxos coperto da oro fisico, quota l'oncia), riserva Hyperliquid xyz:GOLD (perp HIP-3);
- argento: Hyperliquid xyz:SILVER (perp HIP-3; nessuna fonte gratuita alternativa raggiungibile);
- BTC: data/spot.csv del radar (Binance spot).
Stooq non si usa: risponde con una verifica anti-bot (proof-of-work) e dal container la connessione è rifiutata.
Kraken e Hyperliquid quotano 24/7: si prendono solo le candele giornaliere chiuse (UTC).

Cache: data/macro.csv (key, date, close, source, fetched). Ogni asset si riscarica al massimo una volta al giorno (UTC); se la
fonte cade si usa la cache e la nota lo segnala ("dato del <data>"). Nessun dato inventato: senza cache l'asset manca.
Variazioni d1/d5/d20 su osservazioni (giorni di borsa), in % per i prezzi e in PUNTI per VIX e Treasury 10 anni.
"""
from __future__ import annotations

import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

FILE = "macro.csv"
TIMEOUT = 20
HIST_DAYS = 520          # finestra scaricata: ≥ 200 giorni di borsa per la media a 200
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"
KRAKEN = "https://api.kraken.com/0/public/OHLC"
HL = "https://api.hyperliquid.xyz/info"

VIX_HIGH = 34            # flag "VIX sopra 34"
VIX_REGIME = 25          # regime: VIX sotto/sopra 25
DIVERGE_MIN = 3.0        # BTC e S&P divergono: variazioni a 20 giorni di segno opposto, entrambe almeno del 3%
POINTS = ("vix", "us10y")
NOTE = "Contesto: la posizione la decide W3.2; i flag invitano a una revisione."
# (key, nome, giorni oltre i quali il dato è "vecchio" nei controlli di qualità)
ASSETS = [("btc", "BTC", 3), ("spx", "S&P 500", 5), ("ndx", "Nasdaq", 5), ("gold", "Oro", 4), ("silver", "Argento", 4),
          ("usd", "Dollaro (indice)", 14), ("vix", "VIX", 5), ("us10y", "Treasury 10 anni", 5)]


def _today() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(timezone.utc).date())


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").dropna()
    s = s[s > 0]
    s.index = pd.to_datetime(s.index).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index()


# ------------------------------------------------------------------ fonti (rete)
def _fred(sid: str) -> pd.Series:
    start = (_today() - pd.Timedelta(days=HIST_DAYS)).date()
    r = requests.get(FRED, params={"id": sid, "cosd": str(start)}, timeout=TIMEOUT)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    if sid not in d.columns:
        raise ValueError(f"FRED {sid}: risposta senza la colonna attesa")
    return _clean(d.set_index(d.columns[0])[sid])   # i giorni senza valore sono "." → scartati


def _kraken(pair: str) -> pd.Series:
    r = requests.get(KRAKEN, params={"pair": pair, "interval": 1440}, timeout=TIMEOUT)
    r.raise_for_status()
    b = r.json()
    if b.get("error"):
        raise ValueError(f"Kraken {pair}: {b['error']}")
    rows = next(v for k, v in b["result"].items() if k != "last")
    s = pd.Series({pd.Timestamp(int(x[0]), unit="s"): x[4] for x in rows})
    s = _clean(s)
    return s[s.index < _today()]                     # solo candele chiuse


def _hl(coin: str) -> pd.Series:
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    body = {"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d", "startTime": now - 400 * 86_400_000,
                                              "endTime": now}}
    for i in range(3):   # Hyperliquid limita le richieste (429), anche per i giri di liqmap/liqsnap: breve attesa e nuovo tentativo
        r = requests.post(HL, json=body, timeout=TIMEOUT)
        if r.status_code != 429 or i == 2:
            break
        time.sleep(5 * (i + 1))
    r.raise_for_status()
    rows = r.json() or []
    s = _clean(pd.Series({pd.Timestamp(int(x["t"]), unit="ms"): x["c"] for x in rows}))
    return s[s.index < _today()]


# key -> elenco ordinato di (etichetta della fonte, funzione): la prima che risponde vince
SOURCES = {
    "spx": [("FRED SP500", lambda: _fred("SP500"))],
    "ndx": [("FRED NASDAQCOM", lambda: _fred("NASDAQCOM"))],
    "vix": [("FRED VIXCLS", lambda: _fred("VIXCLS"))],
    "us10y": [("FRED DGS10", lambda: _fred("DGS10"))],
    "usd": [("FRED DTWEXBGS", lambda: _fred("DTWEXBGS"))],
    "gold": [("Kraken PAXGUSD", lambda: _kraken("PAXGUSD")), ("Hyperliquid xyz:GOLD", lambda: _hl("xyz:GOLD"))],
    "silver": [("Hyperliquid xyz:SILVER", lambda: _hl("xyz:SILVER"))],
}


# ------------------------------------------------------------------ cache
def load_cache(path: Path) -> pd.DataFrame:
    cols = ["key", "date", "close", "source", "fetched"]
    if not path.exists():
        return pd.DataFrame(columns=cols)
    try:
        d = pd.read_csv(path, dtype={"key": str, "source": str, "fetched": str})
        d["date"] = pd.to_datetime(d["date"])
        return d[cols]
    except Exception as e:  # noqa: BLE001
        print(f"[macro] cache {path.name} non leggibile ({e!r}): si riparte vuota")
        return pd.DataFrame(columns=cols)


def _series(cache: pd.DataFrame, key: str) -> pd.Series:
    c = cache[cache["key"] == key]
    return _clean(pd.Series(c["close"].values, index=c["date"].values)) if len(c) else pd.Series(dtype=float)


def refresh(cache: pd.DataFrame, today: str, sources: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Riscarica gli asset non ancora aggiornati oggi. Restituisce (cache nuova, {key: errore}) — le fonti cadute restano in
    cache con il loro `fetched` vecchio, così si riprova al giro dopo."""
    sources = SOURCES if sources is None else sources
    errors = {}
    for key, chain in sources.items():
        done = cache.loc[cache["key"] == key, "fetched"]
        if len(done) and str(done.max()) >= today:
            continue
        last = None
        for label, fn in chain:
            try:
                s = fn()
                if s is None or not len(s):
                    raise ValueError("nessuna riga")
                rows = pd.DataFrame({"key": key, "date": s.index, "close": s.values, "source": label, "fetched": today})
                cache = pd.concat([cache[cache["key"] != key], rows], ignore_index=True)
                last = None
                print(f"[macro] {key:6s} {label}: {len(s)} righe fino al {s.index.max().date()}")
                break
            except Exception as e:  # noqa: BLE001
                last = f"{label}: {type(e).__name__}: {str(e)[:100]}"
                print(f"[macro] {key:6s} fonte non disponibile ({last})")
        if last:
            errors[key] = last
    return cache, errors


# ------------------------------------------------------------------ calcoli (puri)
def _chg(s: pd.Series, n: int, points: bool) -> float | None:
    if len(s) <= n:
        return None
    a, b = float(s.iloc[-1 - n]), float(s.iloc[-1])
    return round(b - a, 2) if points else round((b / a - 1) * 100, 2)


def asset_row(key: str, name: str, s: pd.Series) -> dict | None:
    if s is None or not len(s):
        return None
    pts = key in POINTS
    ma = float(s.iloc[-200:].mean()) if len(s) >= 200 else None
    return {"key": key, "name": name, "close": round(float(s.iloc[-1]), 4), "d1_pct": _chg(s, 1, pts),
            "d5_pct": _chg(s, 5, pts), "d20_pct": _chg(s, 20, pts),
            "above_ma200": None if ma is None else bool(float(s.iloc[-1]) > ma), "date": str(s.index[-1].date())}


def regime(a: dict) -> dict:
    """Etichetta descrittiva da tre regole fisse: S&P sopra la media a 200, VIX sotto 25, dollaro in calo a 20 giorni."""
    spx, vix, usd = a.get("spx") or {}, a.get("vix") or {}, a.get("usd") or {}
    votes, parts = [], []
    if spx.get("above_ma200") is not None:
        votes.append(spx["above_ma200"])
        parts.append("S&P 500 " + ("sopra" if spx["above_ma200"] else "sotto") + " la media a 200 giorni")
    if vix.get("close") is not None:
        votes.append(vix["close"] < VIX_REGIME)
        parts.append(f"VIX {vix['close']:.1f} ({'sotto' if vix['close'] < VIX_REGIME else 'sopra'} {VIX_REGIME})".replace(".", ","))
    if usd.get("d20_pct") is not None:
        votes.append(usd["d20_pct"] < 0)
        parts.append(f"dollaro {'in discesa' if usd['d20_pct'] < 0 else 'in salita'} a 20 giorni "
                     f"({usd['d20_pct']:+.1f}%)".replace(".", ","))
    if len(votes) < 2:
        label = "non determinabile"
    elif all(votes):
        label = "rischio acceso"
    elif not any(votes):
        label = "rischio spento"
    else:
        label = "misto"
    detail = ("Descrittivo, regole fisse: " + "; ".join(parts) + ". Non è un segnale.") if parts else "Dati insufficienti."
    return {"label": label, "detail": detail}


def flags(a: dict, reg: dict, weekly: dict | None = None) -> list[str]:
    """Avvisi oggettivi che invitano a RIVEDERE strategia o posizione. Nessuna azione automatica."""
    out = []
    vix, spx, btc = a.get("vix") or {}, a.get("spx") or {}, a.get("btc") or {}
    if vix.get("close") is not None and vix["close"] > VIX_HIGH:
        out.append(f"VIX sopra {VIX_HIGH} ({vix['close']:.1f})".replace(".", ","))
    if spx.get("above_ma200") is False:
        out.append("S&P 500 sotto la media a 200 giorni")
    b, s = btc.get("d20_pct"), spx.get("d20_pct")
    if b is not None and s is not None and b * s < 0 and min(abs(b), abs(s)) >= DIVERGE_MIN:
        out.append(f"BTC e S&P 500 divergono a 20 giorni (BTC {b:+.1f}%, S&P {s:+.1f}%)".replace(".", ",").replace("-", "−"))
    w = weekly or {}
    side = w.get("side") if w.get("status") in ("aperto", "uscita") else None
    if (side == "long" and reg["label"] == "rischio spento") or (side == "short" and reg["label"] == "rischio acceso"):
        out.append(f"posizione W3 ({side}) contro il regime ({reg['label']})")
    return out


def quality(a: dict, today: pd.Timestamp) -> list[str]:
    """Controlli di qualità (solo log): dati vecchi e salti giornalieri anomali."""
    warn = []
    for key, name, max_age in ASSETS:
        x = a.get(key)
        if not x:
            warn.append(f"{name}: nessun dato")
            continue
        age = (today - pd.Timestamp(x["date"])).days
        if age > max_age:
            warn.append(f"{name}: ultimo dato del {x['date']} ({age} giorni)")
        if key not in POINTS and x["d1_pct"] is not None and abs(x["d1_pct"]) > 20:
            warn.append(f"{name}: variazione giornaliera anomala {x['d1_pct']:+.1f}%")
    return warn


def _btc(data_dir: Path) -> pd.Series:
    p = data_dir / "spot.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(p, index_col=0, parse_dates=True, usecols=["date", "close"])
    return _clean(d["close"]).iloc[-HIST_DAYS:]


def _weekly_state(data_dir: Path) -> dict | None:
    try:
        return json.loads((data_dir / "state.json").read_text()).get("weekly")
    except Exception:  # noqa: BLE001
        return None


def build(data_dir: Path, weekly: dict | None = None, sources: dict | None = None, now: pd.Timestamp | None = None) -> dict | None:
    """Chiusura multi-asset (schema usato dalla UI). Mai eccezioni per una fonte caduta; None se non c'è alcun dato."""
    data_dir = Path(data_dir)
    today = pd.Timestamp(now).normalize() if now is not None else _today()
    path = data_dir / FILE
    cache, errors = refresh(load_cache(path), str(today.date()), sources)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        cache.sort_values(["key", "date"]).assign(date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")) \
            .to_csv(path, index=False)
    except Exception as e:  # noqa: BLE001
        print(f"[macro] cache non salvata: {e!r}")
    a = {}
    for key, name, _ in ASSETS:
        try:
            s = _btc(data_dir) if key == "btc" else _series(cache, key)
            row = asset_row(key, name, s)
        except Exception as e:  # noqa: BLE001
            print(f"[macro] {name} non calcolato: {e!r}")
            row = None
        if row:
            a[key] = row
    if not a:
        print("[macro] nessun dato disponibile")
        return None
    for w in quality(a, today):
        print(f"[macro] controllo: {w}")
    reg = regime(a)
    wk = weekly if weekly is not None else _weekly_state(data_dir)
    names = dict((k, n) for k, n, _ in ASSETS)
    cached = [f"{names[k]} (dato del {pd.Timestamp(a[k]['date']).strftime('%d/%m')})" for k in errors if k in a]
    missing = [n for k, n, _ in ASSETS if k not in a]
    note = NOTE + (f" Fonte non raggiungibile, uso la cache: {', '.join(cached)}." if cached else "") \
        + (f" Non disponibili: {', '.join(missing)}." if missing else "")
    return {"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "assets": [a[k] for k, _, _ in ASSETS if k in a], "regime": reg, "flags": flags(a, reg, wk), "note": note}


def _num(x: float, d: int) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def telegram_lines(m: dict | None, max_flags: int = 2) -> list[str]:
    """Riga "Mercati: …" per il riepilogo giornaliero + al massimo `max_flags` righe di flag. Mai eccezioni."""
    try:
        if not m or not m.get("assets"):
            return []
        a = {x["key"]: x for x in m["assets"]}
        parts = []
        for key, lab, d in (("spx", "S&P", 0), ("ndx", "Nasdaq", 0), ("gold", "oro", 0), ("usd", "dollaro", 1), ("vix", "VIX", 1)):
            x = a.get(key)
            if not x or x.get("close") is None:
                continue
            ch = x.get("d1_pct")
            chs = "" if ch is None else (f" ({ch:+.1f})" if key in POINTS else f" ({ch:+.1f}%)").replace(".", ",").replace("-", "−")
            parts.append(f"{lab} {_num(x['close'], d)}{chs}")
        out = ["Mercati: " + " · ".join(parts)] if parts else []
        return out + [f"Da rivedere: {f}" for f in (m.get("flags") or [])[:max_flags]]
    except Exception as e:  # noqa: BLE001
        print(f"[macro] riga Telegram non composta: {e!r}")
        return []


if __name__ == "__main__":
    from .data import DATA_DIR
    print(json.dumps(build(DATA_DIR), indent=1, ensure_ascii=False))
