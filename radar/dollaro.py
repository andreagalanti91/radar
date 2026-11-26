"""Controllo "Dollaro" (DXY) accanto alla posizione aperta di BTC: CONTESTO descrittivo, non segnale. W3.2 non cambia.

Nasce dallo studio research/dxy_divergenza (26/11/2026): la divergenza ribassista RSI sul dollaro non ha dato un vantaggio
dimostrabile né sul dollaro né su BTC, e la correlazione settimanale dollaro–BTC è debole e inversa (−0,22 dal 2019). Qui serve
solo a leggere il vento del dollaro sulla posizione. Nessun avviso, nessun effetto su W3.2.

Fonti, in ordine: DXY giornaliero da Yahoo chart API (DX-Y.NYB, range=2y&interval=1d; con period1/period2 da qui non risponde);
ripiego sull'indice ampio del dollaro della Fed (FRED DTWEXBGS: altra scala, ~1 settimana di ritardo, dichiarato nella nota);
infine l'ultimo file salvato. Solo barre chiuse: la barra con la data di oggi (UTC) si scarta.

Cache: data/dollaro.csv (date, close, src) con gli ultimi 2 anni, riscritto solo se cambia. Si scarica quando l'ultima chiusura
è più vecchia dell'ultimo giorno feriale prima di oggi: in pratica una volta al giorno.

Divergenza: STESSA definizione di research/dxy_divergenza/check.py. Ribassista = nuovo massimo di 60 osservazioni del dollaro con
RSI(14) almeno 2 punti sotto il massimo RSI delle 60 precedenti, massimo RSI sopra 65; una ogni 30 giorni. Rialzista = specchio
(nuovo minimo di 60, RSI almeno 2 punti sopra il minimo RSI delle 60 precedenti, minimo RSI sotto 35).
Conferma: chiusura sotto la EMA20 E sotto il minimo dei 30 giorni precedenti (rialzista: sopra EMA20 e massimo di 30 giorni).
Una divergenza resta "da confermare" per 30 giorni dall'evento.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILE = "dollaro.csv"
YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB", "https://query2.finance.yahoo.com/v8/finance/chart/DX-Y.NYB")
UA = {"User-Agent": "Mozilla/5.0 (compatible; radar)"}   # come radar/vix.py: senza User-Agent Yahoo risponde 429
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"
KEEP_DAYS = 731            # ~2 anni salvati
CHART_DAYS = 183           # ~6 mesi nel grafico
WIN, GAP, RSI_HI, RSI_LO, RSI_GAP = 60, 30, 65, 35, 2
ACTIVE_DAYS = 30           # una divergenza non confermata resta "da confermare" per 30 giorni
LEVEL_DAYS = 30            # minimo/massimo dei 30 giorni precedenti
SRC_NAME = {"yahoo": "DXY (ICE, Yahoo)", "fred": "indice ampio del dollaro della Fed (FRED DTWEXBGS)"}
NOTE = "contesto, non cambia W3.2 (studio research/dxy_divergenza: nessun vantaggio dimostrabile)"
STATE_NAME = {"forte": "Dollaro forte", "indeb": "Dollaro in indebolimento (divergenza, da confermare)", "debole": "Dollaro debole"}
# risultati dello studio (research/dxy_divergenza/risultati.txt, 26/11/2026): mediana e % di casi in calo dopo la divergenza
# ribassista, contro un giorno qualsiasi. Il test li confronta col file dei risultati.
STUDY = {
    "rows": [
        {"k": "Dollaro dal 2006", "n": 50, "h": {"10": [0.3, 37, -0.0, 51], "30": [0.3, 39, -0.0, 50], "60": [0.2, 44, 0.1, 49]}},
        {"k": "Dollaro dal 2019-09", "n": 16, "h": {"10": [0.0, 47, 0.0, 50], "30": [0.5, 27, -0.1, 53], "60": [0.1, 43, 0.1, 48]}},
        {"k": "BTC dal 2019-09", "n": 16, "h": {"10": [-2.5, 60, 0.7, 48], "30": [-4.1, 53, 1.5, 45], "60": [5.7, 36, 4.4, 44]}},
    ],
    "corr_all": -0.22, "corr_52w": -0.27,
}


def _today() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(timezone.utc).date())


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").dropna()
    s = s[s > 0]
    s.index = pd.to_datetime(s.index).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index().rename("close")


def _http(url: str, params: dict) -> str:
    """requests con User-Agent; se fallisce, http_text di radar/context.py (requests poi curl)."""
    try:
        import requests
        r = requests.get(url, params=params, headers=UA, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception:  # noqa: BLE001
        from .context import http_text
        return http_text(url, params)


# ------------------------------------------------------------------ fonti
def fetch_yahoo(http=None) -> pd.Series:
    """DXY giornaliero (2 anni) da Yahoo. `http(url, params) -> testo` per i test."""
    res, err = [], None
    for url in YAHOO:                                  # query1, poi query2 (query1 a volte risponde 429)
        try:
            j = json.loads((http or _http)(url, {"range": "2y", "interval": "1d"}))
            res = (j.get("chart") or {}).get("result") or []
            if res:
                break
        except Exception as e:  # noqa: BLE001
            err = e
    if not res:
        raise err or RuntimeError("Yahoo: risposta senza dati")
    r = res[0]
    ts, close = r.get("timestamp") or [], ((r.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    off = int((r.get("meta") or {}).get("gmtoffset") or 0)   # data della seduta a New York
    s = _clean(pd.Series(close[:len(ts)], index=pd.to_datetime(np.array(ts[:len(close)]) + off, unit="s"), dtype=float))
    if len(s) < 100:
        raise RuntimeError(f"Yahoo: solo {len(s)} chiusure")
    return s


def fetch_fred(http=None, today: pd.Timestamp | None = None) -> pd.Series:
    """Indice ampio del dollaro della Fed (DTWEXBGS), 2 anni: altra scala del DXY, ~1 settimana di ritardo."""
    start = ((today or _today()) - pd.Timedelta(days=KEEP_DAYS)).date()
    d = pd.read_csv(io.StringIO((http or _http)(FRED, {"id": "DTWEXBGS", "cosd": str(start)})))
    if "DTWEXBGS" not in d.columns:
        raise ValueError("FRED DTWEXBGS: risposta senza la colonna attesa")
    s = _clean(d.set_index(d.columns[0])["DTWEXBGS"])
    if len(s) < 100:
        raise RuntimeError(f"FRED: solo {len(s)} osservazioni")
    return s


def _read(path: Path) -> tuple[pd.Series, str | None]:
    if not path.exists():
        return pd.Series(dtype=float, name="close"), None
    try:
        d = pd.read_csv(path, parse_dates=["date"])
        return _clean(d.set_index("date")["close"]), str(d["src"].iloc[-1]) if len(d) else None
    except Exception as e:  # noqa: BLE001
        print(f"[dollaro] {path.name} non leggibile ({e!r})")
        return pd.Series(dtype=float, name="close"), None


def _save(s: pd.Series, src: str, path: Path) -> bool:
    """Ultimi 2 anni; riscrive il file solo se il contenuto cambia."""
    s = s[s.index > s.index[-1] - pd.Timedelta(days=KEEP_DAYS)]
    buf = io.StringIO()
    pd.DataFrame({"date": s.index.strftime("%Y-%m-%d"), "close": s.round(4).to_numpy(), "src": src}).to_csv(buf, index=False)
    txt = buf.getvalue()
    if path.exists() and path.read_text() == txt:
        return False
    path.write_text(txt)
    return True


def _last_weekday_before(d: pd.Timestamp) -> pd.Timestamp:
    d = d - pd.Timedelta(days=1)
    while d.weekday() >= 5:
        d -= pd.Timedelta(days=1)
    return d


def load(data_dir: Path, http=None, today: pd.Timestamp | None = None) -> tuple[pd.Series, str, str | None]:
    """(chiusure, fonte "yahoo"/"fred", nota sulla fonte o None). Scarica solo se l'ultima chiusura è vecchia."""
    today = today or _today()
    path = Path(data_dir) / FILE
    cache, csrc = _read(path)
    if not cache.empty and cache.index[-1] >= _last_weekday_before(today):
        return cache, csrc or "yahoo", None
    errs = []
    try:
        s = fetch_yahoo(http)
        s = s[s.index < today]                         # solo barre chiuse
        _save(s, "yahoo", path)
        return s, "yahoo", None
    except Exception as e:  # noqa: BLE001
        errs.append(f"Yahoo {type(e).__name__}")
    if not cache.empty and csrc == "yahoo" and cache.index[-1] >= today - pd.Timedelta(days=5):
        return cache, "yahoo", f"Yahoo non risponde: DXY del {cache.index[-1]:%d/%m/%Y}"
    try:
        s = fetch_fred(http, today)
        if cache.empty or csrc == "fred":              # il file col DXY non si sovrascrive con l'indice della Fed
            _save(s, "fred", path)
        return s, "fred", (f"Yahoo non risponde: indice ampio della Fed (FRED DTWEXBGS), altra scala, con circa una settimana di "
                           f"ritardo (dato del {s.index[-1]:%d/%m/%Y})")
    except Exception as e:  # noqa: BLE001
        errs.append(f"FRED {type(e).__name__}")
    if cache.empty:
        raise RuntimeError("dollaro non disponibile: " + ", ".join(errs))
    return cache, csrc or "yahoo", f"Fonti non raggiungibili ({', '.join(errs)}): ultimo dato salvato del {cache.index[-1]:%d/%m/%Y}"


# ------------------------------------------------------------------ calcolo
def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """RSI di Wilder, come research/dxy_divergenza/check.py."""
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def divergences(s: pd.Series, r: pd.Series, kind: str = "bear") -> list[dict]:
    """Eventi di divergenza con la definizione di check.py (kind "bear"); "bull" è lo specchio.
    Ogni evento: data, chiusura e RSI dell'evento, data/chiusura/RSI del massimo (minimo) RSI precedente nella finestra."""
    out, last = [], None
    v, rv = s.to_numpy(), r.to_numpy()
    for i in range(WIN, len(s)):
        w, rw = v[i - WIN:i], rv[i - WIN:i]
        if kind == "bear":
            hit = v[i] > w.max() and rw.max() > RSI_HI and rv[i] < rw.max() - RSI_GAP
            j = i - WIN + int(np.nanargmax(rw)) if hit else None
        else:
            hit = v[i] < w.min() and rw.min() < RSI_LO and rv[i] > rw.min() + RSI_GAP
            j = i - WIN + int(np.nanargmin(rw)) if hit else None
        if hit:
            d = s.index[i]
            if last is None or (d - last).days > GAP:
                out.append({"date": d, "close": float(v[i]), "rsi": float(rv[i]),
                            "ref_date": s.index[j], "ref_close": float(v[j]), "ref_rsi": float(rv[j])})
                last = d
    return out


def _levels(s: pd.Series, i: int) -> tuple[float, float]:
    """Minimo e massimo delle chiusure dei 30 giorni (di calendario) prima dell'osservazione i, esclusa."""
    d = s.index[i]
    w = s[(s.index < d) & (s.index >= d - pd.Timedelta(days=LEVEL_DAYS))]
    return (float(w.min()), float(w.max())) if len(w) else (float(s.iloc[i]), float(s.iloc[i]))


def _confirmed(s: pd.Series, e20: pd.Series, ev: dict, kind: str) -> pd.Timestamp | None:
    """Primo giorno dopo l'evento con chiusura oltre la EMA20 e il minimo (massimo) dei 30 giorni precedenti."""
    for i in np.flatnonzero(s.index > ev["date"]):
        lo, hi = _levels(s, i)
        c = s.iloc[i]
        if (kind == "bear" and c < e20.iloc[i] and c < lo) or (kind == "bull" and c > e20.iloc[i] and c > hi):
            return s.index[i]
    return None


def _div_state(s, e20, evs, kind, d0) -> dict | None:
    if not evs:
        return None
    ev = evs[-1]
    conf = _confirmed(s, e20, ev, kind)
    age = (d0 - ev["date"]).days
    return {"date": ev["date"].strftime("%Y-%m-%d"), "ref_date": ev["ref_date"].strftime("%Y-%m-%d"),
            "close": round(ev["close"], 3), "rsi": round(ev["rsi"], 1), "ref_close": round(ev["ref_close"], 3),
            "ref_rsi": round(ev["ref_rsi"], 1), "days": age,
            "confirmed": conf.strftime("%Y-%m-%d") if conf is not None else None,
            "active": conf is None and age <= ACTIVE_DAYS}


def analyze(s: pd.Series) -> dict:
    """Stato del dollaro all'ultima chiusura: trend, RSI, divergenze, livelli di conferma, stato sintetico."""
    if len(s) < WIN + 20:
        raise RuntimeError(f"dollaro: solo {len(s)} chiusure")
    e20, e50, r = ema(s, 20), ema(s, 50), rsi(s)
    i, d0, c = len(s) - 1, s.index[-1], float(s.iloc[-1])
    lo30, hi30 = _levels(s, i)
    bear, bull = divergences(s, r, "bear"), divergences(s, r, "bull")
    db, du = _div_state(s, e20, bear, "bear", d0), _div_state(s, e20, bull, "bull", d0)
    E20, E50 = float(e20.iloc[-1]), float(e50.iloc[-1])
    sl20 = (E20 / float(e20.iloc[-6]) - 1) * 100       # pendenza: variazione della EMA in 5 sedute
    sl50 = (E50 / float(e50.iloc[-6]) - 1) * 100
    brk_dn, brk_up = c < E20 and c < lo30, c > E20 and c > hi30
    recent_conf = db and db["confirmed"] and (d0 - pd.Timestamp(db["confirmed"])).days <= ACTIVE_DAYS and c < E20
    if (c < E20 and c < E50) or brk_dn or recent_conf:
        state = "debole"
    elif db and db["active"]:
        state = "indeb"
    elif c >= E50:
        state = "forte"
    else:
        state = "debole"
    ch20 = (c / float(s.iloc[-21]) - 1) * 100 if len(s) > 20 else None
    return {"date": d0.strftime("%Y-%m-%d"), "close": round(c, 3), "ema20": round(E20, 3), "ema50": round(E50, 3),
            "above20": c > E20, "above50": c > E50, "slope20": round(sl20, 2), "slope50": round(sl50, 2),
            "rsi": round(float(r.iloc[-1]), 1), "lo30": round(lo30, 3), "hi30": round(hi30, 3),
            "ch20": None if ch20 is None else round(ch20, 2), "break_dn": bool(brk_dn), "break_up": bool(brk_up),
            "bear": db, "bull": du, "state": state, "state_name": STATE_NAME[state],
            "_bear_all": bear, "_bull_all": bull, "_e20": e20, "_e50": e50, "_rsi": r}


def _n(x: float, d: int = 2) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def frase(side: str | None, a: dict) -> str:
    """UNA frase per la posizione aperta di BTC (side long/short, None = flat). Priorità: divergenza da confermare (prima quella
    nel verso che aiuta la posizione), rottura dei livelli, stato. La nota NOTE si aggiunge sempre a parte (frase_completa)."""
    db, du = a.get("bear"), a.get("bull")
    x_dn = _n(min(a["ema20"], a["lo30"]))   # serve chiudere sotto ENTRAMBI: il livello che conta è il più basso
    x_up = _n(max(a["ema20"], a["hi30"]))
    if side == "short":
        if db and db["active"]:
            return f"Divergenza ribassista sul dollaro: da confermare sotto {x_dn}"
        if du and du["active"]:
            return f"Divergenza rialzista sul dollaro: da confermare sopra {x_up}"
        if a["break_dn"]:
            return "Dollaro in calo: vento contrario allo short, prudenza"
        if a["state"] == "forte":
            return "Dollaro forte: vento a favore dello short"
        return "Dollaro debole: vento contrario allo short"
    if side == "long":
        if du and du["active"]:
            return f"Divergenza rialzista sul dollaro: da confermare sopra {x_up}"
        if db and db["active"]:
            return f"Divergenza ribassista sul dollaro: da confermare sotto {x_dn}"
        if a["break_up"]:
            return "Dollaro in rialzo: vento contrario al long, prudenza"
        if a["state"] == "debole":
            return "Dollaro debole: vento a favore del long"
        return "Dollaro forte: vento contrario al long"
    if db and db["active"]:
        return f"Divergenza ribassista sul dollaro: da confermare sotto {x_dn}"
    if du and du["active"]:
        return f"Divergenza rialzista sul dollaro: da confermare sopra {x_up}"
    return f"{STATE_NAME[a['state']].split(' (')[0]}: nessuna posizione aperta su BTC"


def frase_completa(side: str | None, a: dict) -> str:
    return f"{frase(side, a)}. Solo {NOTE}."


def corr_52w(dxy: pd.Series, btc: pd.Series) -> float | None:
    """Correlazione settimanale dollaro–BTC delle ultime 52 settimane (stesso calcolo di check.py)."""
    if dxy.empty or btc.empty:
        return None
    c = pd.concat([dxy.pct_change(), btc.pct_change()], axis=1, keys=["dxy", "btc"], sort=True).dropna()
    c = c.resample("W").sum().iloc[-52:]
    if len(c) < 30:
        return None
    v = c["dxy"].corr(c["btc"])
    return None if pd.isna(v) else round(float(v), 2)


def _btc(data_dir: Path) -> pd.Series:
    p = Path(data_dir) / "spot.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(p, usecols=["date", "close"])
    return _clean(pd.Series(d["close"].to_numpy(), index=pd.to_datetime(d["date"])))


def build(data_dir: Path, side: str | None = None, http=None, today: pd.Timestamp | None = None) -> dict:
    """report["dollaro"]: stato, livelli, divergenze, serie di 6 mesi (chiusura, EMA20/50, RSI), studio, frase."""
    s, src, note = load(data_dir, http=http, today=today)
    a = analyze(s)
    d0 = s.index[-1]
    m = s.index > d0 - pd.Timedelta(days=CHART_DAYS)
    idx = s.index[m]
    pos = {d: k for k, d in enumerate(idx)}

    def marks(evs):   # divergenze che cadono nel grafico (evento e riferimento entrambi visibili)
        return [{"i": pos[e["date"]], "j": pos[e["ref_date"]], "date": e["date"].strftime("%Y-%m-%d")}
                for e in evs if e["date"] in pos and e["ref_date"] in pos]
    try:
        corr = corr_52w(s, _btc(data_dir)) if src == "yahoo" else None
    except Exception:  # noqa: BLE001
        corr = None
    out = {k: v for k, v in a.items() if not k.startswith("_")}
    out.update({
        "src": src, "src_name": SRC_NAME[src], "source_note": note, "side": side,
        "frase": frase(side, a), "note": NOTE,
        "series": {"d0": idx[0].strftime("%Y-%m-%d"), "d": [x.strftime("%Y-%m-%d") for x in idx],
                   "c": [round(float(x), 3) for x in s[m]], "e20": [round(float(x), 3) for x in a["_e20"][m]],
                   "e50": [round(float(x), 3) for x in a["_e50"][m]], "rsi": [round(float(x), 1) for x in a["_rsi"][m]],
                   "bear": marks(a["_bear_all"]), "bull": marks(a["_bull_all"])},
        "study": dict(STUDY, corr_now=corr),
    })
    return out


def side_of(weekly: dict | None) -> str | None:
    """Verso della posizione aperta di W3.2 su BTC (None se flat o in attesa d'ingresso)."""
    from .onchain import side_of as so
    return so(weekly)
