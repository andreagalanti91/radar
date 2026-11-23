"""Riquadro "Contesto" della dashboard: stato del mercato e della politica economica. CONTESTO, NON SEGNALE.

Lo studio research/previsionale2 (lezione 113) ha mostrato che regimi e politica economica descrivono il mercato ma non ne
anticipano la direzione: qui non ci sono probabilità, attese né medie storiche per fase, e nulla entra in W3.2.

Definizioni: le stesse di research/previsionale2/p2_data.py e p2_oggi.py.
- Trend: prezzo contro la media a 200 giorni e pendenza della media su 30 giorni → rialzo (sopra, media in salita), ribasso
  (sotto, media in discesa), laterale (gli altri casi; "misto" nello studio).
- Volatilità: deviazione standard a 30 giorni dei rendimenti logaritmici contro la propria mediana dei 365 giorni precedenti.
- Tasso Fed (DFF): in rialzo / in calo / fermo se la variazione a 126 giorni supera ±0,125 punti; ultima mossa = ultimo
  gradino di almeno 0,15 punti che resta nei giorni successivi (esclude le oscillazioni di fine mese del tasso effettivo).
- Bilancio (WALCL): in aumento / in calo oltre ±1% in 13 settimane (91 giorni), altrimenti stabile.
- Liquidità netta = WALCL − conto del Tesoro (WTREGEN) − reverse repo (RRPONTSYD): segno della variazione a 13 settimane.
- CPI annuo (CPIAUCSL): variazione su 12 mesi a un decimale; direzione = confronto con l'ultimo mese calcolabile prima
  (un mese non pubblicato, come 10/2025, lascia senza valore annuo anche lo stesso mese dell'anno dopo: si mostra l'ultimo
  calcolabile con il suo mese).
- Ritardi di pubblicazione (LAG, dallo studio): dal vivo FRED restituisce solo ciò che è già pubblicato, quindi si usa l'ultimo
  valore con la SUA data; i ritardi servono a stabilire quando un dato è "vecchio" (MAX_AGE = ritardo + cadenza + tolleranza).

Fonte: FRED fredgraph.csv (pubblico, senza chiave), al massimo una volta al giorno (UTC) per serie; cache in data/context.csv
(key, date, value, fetched). Fonte non raggiungibile → ultimo dato in cache con la sua data; mai eccezioni verso il giro.
Rete: prima `requests` (runner GitHub); se fallisce, `curl` (nel container requests può non attraversare il proxy locale).
Prossima riunione FOMC: report["banks"] (radar/news.fetch_central_banks); se manca, l'ultima data salvata in cache.
"""
from __future__ import annotations

import io
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import pandas as pd

FILE = "context.csv"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"
TIMEOUT = 20
HIST_DAYS = 1100         # 3 anni: ultima mossa del tasso, 13 mesi di CPI, 13 settimane di bilancio
SERIES = ("DFF", "WALCL", "WTREGEN", "RRPONTSYD", "CPIAUCSL", "VIXCLS")
LAG = {"DFF": 2, "WALCL": 2, "WTREGEN": 2, "RRPONTSYD": 1, "VIXCLS": 1}          # giorni, come nello studio
MAX_AGE = {"DFF": 7, "WALCL": 14, "WTREGEN": 14, "RRPONTSYD": 7, "VIXCLS": 7, "CPIAUCSL": 80, "BTC": 3}
RATE_DAYS, RATE_BAND = 126, 0.125
MOVE_MIN = 0.15
BAL_DAYS, BAL_BAND = 91, 1.0
NOTE = ("Contesto, non segnale: regimi e politica economica descrivono il mercato ma nei test non ne hanno anticipato la "
        "direzione (lezione 113). Decide W3.2.")
TREND = {"U": "rialzo", "D": "ribasso", "M": "laterale"}
VOL = {"A": "alta", "B": "bassa"}


# ------------------------------------------------------------------ formato
def _n(x: float, d: int = 1, sign: bool = False) -> str:
    s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def _dm(d, year: bool = False) -> str:
    return pd.Timestamp(d).strftime("%d/%m/%Y" if year else "%d/%m")


# ------------------------------------------------------------------ rete e cache
def http_text(url: str, params: dict, timeout: int = TIMEOUT) -> str:
    """Testo della risposta: requests, poi curl se requests fallisce (proxy locale). Solleva se falliscono entrambi."""
    try:
        import requests
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:  # noqa: BLE001
        first = e
    if not shutil.which("curl"):
        raise first
    p = subprocess.run(["curl", "-sS", "-f", "-L", "-m", str(timeout + 10), f"{url}?{urlencode(params)}"],
                       capture_output=True, text=True, timeout=timeout + 20)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError(f"requests: {type(first).__name__}; curl: codice {p.returncode} {p.stderr.strip()[:80]}")
    return p.stdout


def fetch_fred(sid: str, today: pd.Timestamp) -> pd.Series:
    start = (today - pd.Timedelta(days=HIST_DAYS)).date()
    d = pd.read_csv(io.StringIO(http_text(FRED, {"id": sid, "cosd": str(start)})))
    if sid not in d.columns:
        raise ValueError(f"FRED {sid}: risposta senza la colonna attesa")
    s = pd.to_numeric(d.set_index(d.columns[0])[sid], errors="coerce").dropna()   # "." e vuoti (mesi non pubblicati) scartati
    s.index = pd.to_datetime(s.index).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index()


def load_cache(path: Path) -> pd.DataFrame:
    cols = ["key", "date", "value", "fetched"]
    if not path.exists():
        return pd.DataFrame(columns=cols)
    try:
        d = pd.read_csv(path, dtype={"key": str, "fetched": str})
        d["date"] = pd.to_datetime(d["date"])
        return d[cols]
    except Exception as e:  # noqa: BLE001
        print(f"[contesto] cache {path.name} non leggibile ({e!r}): si riparte vuota")
        return pd.DataFrame(columns=cols)


def _series(cache: pd.DataFrame, key: str) -> pd.Series:
    c = cache[cache["key"] == key]
    if not len(c):
        return pd.Series(dtype=float)
    s = pd.Series(pd.to_numeric(c["value"], errors="coerce").values, index=pd.to_datetime(c["date"].values)).dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()


def refresh(cache: pd.DataFrame, today: pd.Timestamp, fetch=None) -> tuple[pd.DataFrame, dict]:
    """Riscarica le serie non ancora aggiornate oggi. Restituisce (cache, {serie: errore}). Dopo il primo errore le altre
    serie non si tentano in questo giro (la fonte è una sola: si evita di rallentare il giro orario) e si riprova al prossimo."""
    fetch = fetch_fred if fetch is None else fetch
    day, errors, down = str(today.date()), {}, None
    for sid in SERIES:
        done = cache.loc[cache["key"] == sid, "fetched"]
        if len(done) and str(done.max()) >= day:
            continue
        if down:
            errors[sid] = down
            continue
        try:
            s = fetch(sid, today)
            if s is None or not len(s):
                raise ValueError("nessuna riga")
            rows = pd.DataFrame({"key": sid, "date": s.index, "value": s.values, "fetched": day})
            cache = pd.concat([cache[cache["key"] != sid], rows], ignore_index=True)
            print(f"[contesto] {sid:9s} FRED: {len(s)} righe fino al {s.index.max().date()}")
        except Exception as e:  # noqa: BLE001
            down = errors[sid] = f"{type(e).__name__}: {str(e)[:100]}"
            print(f"[contesto] {sid} non scaricata ({down}): uso la cache")
    return cache, errors


# ------------------------------------------------------------------ calcoli (puri)
def _daily(s: pd.Series, end: pd.Timestamp | None = None) -> pd.Series:
    """Serie su calendario giornaliero, ultimo valore portato avanti (come avail() dello studio)."""
    end = s.index[-1] if end is None else max(end, s.index[-1])
    return s.reindex(pd.date_range(s.index[0], end)).ffill()


def market(close: pd.Series) -> dict | None:
    """Regime di trend e di volatilità all'ultima chiusura (p2_data.regimes). None se la storia non basta per il trend."""
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < 230:
        return None
    sma = close.rolling(200).mean()
    px, m, m30 = float(close.iloc[-1]), float(sma.iloc[-1]), float(sma.iloc[-31])
    t = "U" if (px > m and m > m30) else "D" if (px < m and m < m30) else "M"
    v = np.log(close).diff().rolling(30).std()
    med = v.shift(1).rolling(365).median().iloc[-1]
    vol = None if pd.isna(med) else ("A" if float(v.iloc[-1]) > float(med) else "B")
    return {"date": str(pd.Timestamp(close.index[-1]).date()), "close": round(px, 2), "trend": TREND[t], "trend_code": t,
            "sma200": round(m, 2), "dist_pct": round((px / m - 1) * 100, 1),
            "sma_slope": "in salita" if m > m30 else "in discesa" if m < m30 else "piatta",
            "vol": None if vol is None else VOL[vol], "vol_code": vol,
            "vol30_pct": round(float(v.iloc[-1]) * 100, 2), "vol_median_pct": None if pd.isna(med) else round(float(med) * 100, 2)}


def last_move(dff: pd.Series) -> dict | None:
    """Ultimo gradino del tasso effettivo: variazione giornaliera ≥ MOVE_MIN confermata dalle mediane dei 5 giorni prima e dopo."""
    s = _daily(dff)
    d = s.diff()
    for day in reversed(d.index[d.abs() >= MOVE_MIN]):
        i = s.index.get_loc(day)
        if i < 1:
            continue
        step = float(s.iloc[i:i + 5].median() - s.iloc[max(0, i - 5):i].median())
        if abs(step) >= MOVE_MIN:
            return {"date": str(day.date()), "change": round(step, 2)}
    return None


def rate(dff: pd.Series) -> dict | None:
    if dff is None or not len(dff):
        return None
    s = _daily(dff)
    out = {"value": round(float(s.iloc[-1]), 2), "date": str(dff.index[-1].date()), "direction": None, "change": None,
           "last_move": last_move(dff)}
    if len(s) > RATE_DAYS:
        ch = float(s.iloc[-1] - s.iloc[-1 - RATE_DAYS])
        out["change"] = round(ch, 2)
        out["direction"] = "in rialzo" if ch > RATE_BAND else "in calo" if ch < -RATE_BAND else "fermo"
    return out


def _chg13(s: pd.Series) -> float | None:
    return None if len(s) <= BAL_DAYS or not s.iloc[-1 - BAL_DAYS] else float((s.iloc[-1] / s.iloc[-1 - BAL_DAYS] - 1) * 100)


def balance(walcl: pd.Series) -> dict | None:
    if walcl is None or not len(walcl):
        return None
    ch = _chg13(_daily(walcl))
    return {"value_bn": round(float(walcl.iloc[-1]) / 1000, 0), "date": str(walcl.index[-1].date()),
            "chg13_pct": None if ch is None else round(ch, 2),
            "direction": None if ch is None else "in aumento" if ch > BAL_BAND else "in calo" if ch < -BAL_BAND else "stabile"}


def net_liquidity(walcl: pd.Series, tga: pd.Series, rrp: pd.Series) -> dict | None:
    """WALCL e WTREGEN in milioni, RRPONTSYD in miliardi (come nello studio: reverse repo mancante = 0)."""
    if walcl is None or tga is None or not len(walcl) or not len(tga):
        return None
    end = max(x.index[-1] for x in (walcl, tga, rrp) if x is not None and len(x))
    w, t = _daily(walcl, end), _daily(tga, end)
    r = _daily(rrp, end).reindex(w.index).fillna(0) if rrp is not None and len(rrp) else 0
    nl = (w - t.reindex(w.index) - r * 1000).dropna()
    if not len(nl):
        return None
    ch = _chg13(nl)
    return {"value_bn": round(float(nl.iloc[-1]) / 1000, 0), "date": str(min(walcl.index[-1], tga.index[-1]).date()),
            "chg13_pct": None if ch is None else round(ch, 2),
            "direction": None if ch is None else "in aumento" if ch >= 0.05 else "in calo" if ch <= -0.05 else "stabile"}


def cpi(c: pd.Series) -> dict | None:
    """CPI annuo dell'ultimo mese calcolabile e direzione rispetto al mese calcolabile precedente (p2_data.cpi_yoy)."""
    if c is None or len(c) < 13:
        return None
    c = c.copy()
    c.index = pd.to_datetime(c.index).to_period("M").to_timestamp()
    raw_last = c.index[-1]                                                       # ultimo mese pubblicato (per "dato vecchio")
    c = c.reindex(pd.date_range(c.index[0], c.index[-1], freq="MS"))            # mesi non pubblicati = NaN
    yoy = (c / c.shift(12) - 1).mul(100).round(1).dropna()
    if not len(yoy):
        return None
    out = {"yoy": float(yoy.iloc[-1]), "month": yoy.index[-1].strftime("%m/%Y"), "date": str(yoy.index[-1].date()),
           "published": str(raw_last.date()), "prev": None, "direction": None}
    if len(yoy) > 1:
        d = round(float(yoy.iloc[-1] - yoy.iloc[-2]), 1)
        out["prev"] = float(yoy.iloc[-2])
        out["direction"] = "in salita" if d > 0 else "in calo" if d < 0 else "ferma"
    return out


def next_fomc(banks: list | None, today: pd.Timestamp) -> str | None:
    days = sorted(b["date"] for b in (banks or []) if isinstance(b, dict) and b.get("bank") == "Fed" and b.get("date")
                  and pd.Timestamp(b["date"]) >= today)
    return days[0] if days else None


def _age(date: str, today: pd.Timestamp) -> int:
    return int((today - pd.Timestamp(date)).days)


def compose(mk: dict | None, fed: dict, fomc: str | None, today: pd.Timestamp, errors: dict | None = None) -> dict | None:
    """Righe del riquadro (al massimo 3 + dicitura fissa) e dettagli. Solo stato e direzioni: nessuna probabilità o attesa."""
    errors = errors or {}
    r, b, nl, c, vix = (fed.get(k) for k in ("rate", "balance", "net_liquidity", "cpi", "vix"))
    rows, det, old = [], [], []

    def stale(name: str, key: str, date: str | None):
        if date and (key in errors or _age(date, today) > MAX_AGE[key]):
            old.append(f"{name} (dato del {_dm(date)})")

    if mk:
        txt = f"{mk['trend']}, prezzo {_n(mk['dist_pct'], 1, True)}% dalla media a 200 giorni"
        if mk.get("vol"):
            txt += f" · volatilità {mk['vol']}"
        rows.append({"label": "Mercato", "text": txt})
        det.append({"label": "Trend", "value": mk["trend"],
                    "text": f"chiusura del {_dm(mk['date'])} a {_n(mk['close'], 0)} $, media a 200 giorni {_n(mk['sma200'], 0)} $ "
                            f"({_n(mk['dist_pct'], 1, True)}%), media {mk['sma_slope']} rispetto a 30 giorni fa"})
        if mk.get("vol"):
            det.append({"label": "Volatilità", "value": mk["vol"],
                        "text": f"30 giorni {_n(mk['vol30_pct'], 2)}% al giorno, mediana dell'ultimo anno {_n(mk['vol_median_pct'], 2)}%"})
        stale("BTC", "BTC", mk["date"])
    parts = []
    if r:
        mv = r.get("last_move")
        mvs = f"{_n(mv['change'], 2, True)} il {_dm(mv['date'], True)}" if mv else None
        parts.append(f"tasso {_n(r['value'], 2)}%" + (f" {r['direction']}" if r.get("direction") else "")
                     + (f" ({_n(mv['change'], 2, True)} il {_dm(mv['date'], _age(mv['date'], today) > 300)})" if mv else ""))
        det.append({"label": "Tasso Fed", "value": f"{_n(r['value'], 2)}%" + (f" · {r['direction']}" if r.get("direction") else ""),
                    "text": f"tasso effettivo del {_dm(r['date'])}"
                            + (f", {_n(r['change'], 2, True)} punti in {RATE_DAYS} giorni" if r.get("change") is not None else "")
                            + (f"; ultima mossa {mvs}" if mvs else "; nessuna mossa negli ultimi 3 anni")})
        stale("tasso", "DFF", r["date"])
    if b and b.get("direction"):
        parts.append(f"bilancio {b['direction']}")
        det.append({"label": "Bilancio Fed", "value": b["direction"],
                    "text": f"{_n(b['value_bn'], 0)} mld $ al {_dm(b['date'])}, {_n(b['chg13_pct'], 1, True)}% in 13 settimane"})
        stale("bilancio", "WALCL", b["date"])
    if nl and nl.get("direction"):
        parts.append(f"liquidità {nl['direction']}")
        det.append({"label": "Liquidità netta", "value": nl["direction"],
                    "text": f"{_n(nl['value_bn'], 0)} mld $ al {_dm(nl['date'])}, {_n(nl['chg13_pct'], 1, True)}% in 13 settimane "
                            "(bilancio − conto del Tesoro − reverse repo)"})
        if not (b and b.get("direction")):
            stale("liquidità netta", "WALCL", nl["date"])
    if parts:
        rows.append({"label": "Fed", "text": " · ".join(parts)})
    parts = []
    if c:
        parts.append(f"CPI annuo {_n(c['yoy'], 1)}%" + (f" {c['direction']}" if c.get("direction") else "") + f" ({c['month']})")
        det.append({"label": "Inflazione CPI", "value": f"{_n(c['yoy'], 1)}%" + (f" · {c['direction']}" if c.get("direction") else ""),
                    "text": f"variazione su 12 mesi, dato di {c['month']}" + (f" (mese prima {_n(c['prev'], 1)}%)" if c.get("prev") is not None else "")})
        if "CPIAUCSL" in errors or _age(c.get("published") or c["date"], today) > MAX_AGE["CPIAUCSL"]:
            old.append(f"CPI (dato di {c['month']})")
    if vix:
        parts.append(f"VIX {_n(vix['value'], 1)}")
        det.append({"label": "VIX", "value": _n(vix["value"], 1), "text": f"chiusura del {_dm(vix['date'])}"})
        stale("VIX", "VIXCLS", vix["date"])
    if fomc:
        days = _age(str(today.date()), pd.Timestamp(fomc))
        when = "oggi" if days == 0 else "domani" if days == 1 else f"fra {days} giorni"
        parts.append(f"FOMC {_dm(fomc)}")
        det.append({"label": "Prossima riunione Fed", "value": _dm(fomc, True), "text": f"decisione del FOMC {when}"})
    if parts:
        rows.append({"label": "Dati", "text": " · ".join(parts)})
    if not rows:
        return None
    warn = ("Fonte non raggiungibile o dato vecchio: " + ", ".join(old) + ".") if old else None
    return {"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "title": "Contesto",
            "rows": rows, "details": det, "warn": warn, "note": NOTE,
            "source": "Mercato: chiusure giornaliere BTC del radar. Fed, CPI e VIX: FRED (St. Louis Fed), al massimo una volta al giorno.",
            "market": mk, "fed": {**fed, "next_fomc": fomc}}


# ------------------------------------------------------------------ giro
def _btc(data_dir: Path) -> pd.Series:
    p = data_dir / "spot.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(p, index_col=0, parse_dates=True, usecols=["date", "close"])
    return pd.to_numeric(d["close"], errors="coerce").dropna()


def build(data_dir: Path, banks: list | None = None, fetch=None, now: pd.Timestamp | None = None) -> dict | None:
    """report["context"]. Mai eccezioni per una fonte caduta; None solo se non c'è alcun dato (nemmeno in cache)."""
    data_dir = Path(data_dir)
    today = pd.Timestamp(now).normalize() if now is not None else pd.Timestamp(datetime.now(timezone.utc).date())
    path = data_dir / FILE
    cache = load_cache(path)
    try:
        cache, errors = refresh(cache, today, fetch)
    except Exception as e:  # noqa: BLE001
        print(f"[contesto] aggiornamento non riuscito: {e!r}")
        errors = {s: "errore" for s in SERIES}
    fomc = None
    try:
        fomc = next_fomc(banks, today)
        if fomc:   # la data resta in cache per i giri in cui il calendario della Fed non risponde
            cache = pd.concat([cache[cache["key"] != "FOMC"], pd.DataFrame({"key": "FOMC", "date": [pd.Timestamp(fomc)],
                                                                             "value": 1.0, "fetched": str(today.date())})], ignore_index=True)
        else:
            f = _series(cache, "FOMC")
            f = f[f.index >= today]
            fomc = str(f.index[0].date()) if len(f) else None
    except Exception as e:  # noqa: BLE001
        print(f"[contesto] riunione FOMC non determinata: {e!r}")
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        cache.sort_values(["key", "date"]).assign(date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")) \
            .to_csv(path, index=False)
    except Exception as e:  # noqa: BLE001
        print(f"[contesto] cache non salvata: {e!r}")

    def soft(name, fn):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            print(f"[contesto] {name} non calcolato: {e!r}")
            return None
    s = {k: _series(cache, k) for k in SERIES}
    vx = s["VIXCLS"]
    fed = {"rate": soft("tasso", lambda: rate(s["DFF"])), "balance": soft("bilancio", lambda: balance(s["WALCL"])),
           "net_liquidity": soft("liquidità netta", lambda: net_liquidity(s["WALCL"], s["WTREGEN"], s["RRPONTSYD"])),
           "cpi": soft("CPI", lambda: cpi(s["CPIAUCSL"])),
           "vix": {"value": round(float(vx.iloc[-1]), 2), "date": str(vx.index[-1].date())} if len(vx) else None}
    mk = soft("regime di mercato", lambda: market(_btc(data_dir)))
    out = soft("riquadro", lambda: compose(mk, fed, fomc, today, errors))
    if out is None:
        print("[contesto] nessun dato disponibile")
    return out


if __name__ == "__main__":
    from .data import DATA_DIR
    from .news import fetch_central_banks
    print(json.dumps(build(DATA_DIR, banks=fetch_central_banks()), indent=1, ensure_ascii=False))
