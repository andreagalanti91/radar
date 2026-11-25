"""Ciclo on-chain di BTC (MVRV di CoinMetrics): CONTESTO descrittivo per la posizione aperta, non segnale.

Sostituto pubblico dell'indicatore UTXO P/L di CryptoQuant, studiato in research/utxo_pl (lezione 125): nessuna regola su W3.2
lo ha superato; qui serve solo a leggere in che fase del ciclo si trova il mercato. Nessun avviso, nessun effetto su W3.2.

Fonte: CoinMetrics community API, metrica CapMVRVCur (giornaliera, valore del giorno D disponibile il giorno D+1).
Zone come nello studio (definizione b): capitolazione = MVRV nel 10% più basso dei 1.460 giorni PRECEDENTI (escluso il giorno
stesso: solo passato), euforia = nel 10% più alto; riferimenti fissi 1,0 e 3,0 mostrati a parte.

Cache: data/mvrv.csv con gli ultimi ~5 anni (si riscrive solo se cambia). Si scarica quando l'ultimo dato è più vecchio di ieri
(UTC): in pratica una volta al giorno. Rete giù = cache + storia congelata dello studio (research/utxo_pl/mvrv.csv), con la nota.
Statistiche: dopo gli ingressi in zona dal 2016 (nuovo ingresso solo dopo almeno 30 giorni fuori zona), variazione del prezzo di
BTC dalla chiusura del giorno d'ingresso a 30 e 90 giorni. Prezzi del repo: data/spot.csv (dal 2019), prima
research/p2_nuovi/data/f_long.csv.gz (dal 2014). Episodi senza 90 giorni di dati restano fuori.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILE = "mvrv.csv"
STUDY = ROOT / "research" / "utxo_pl" / "mvrv.csv"
OLD_PRICES = ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz"
URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
WIN, Q = 1460, 0.10
KEEP_DAYS = 1830           # ~5 anni salvati in data/mvrv.csv
CHART_DAYS = 730           # ~2 anni nel grafico
STATS_FROM = "2016-01-01"
GAP = 30                   # giorni fuori zona perché un ingresso conti come nuovo
HORIZONS = (30, 90)
NOTE = "Sostituto pubblico (MVRV di CoinMetrics) dell'indicatore UTXO P/L di CryptoQuant; solo contesto, non cambia W3.2."
ZONE_NAME = {"cap": "Capitolazione", "norm": "Normale", "eup": "Euforia"}


def _today() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(timezone.utc).date())


# ------------------------------------------------------------------ dati
def fetch(http=None) -> pd.Series:
    """Tutta la serie MVRV di BTC dalla community API (paginata). `http(url, params) -> testo JSON` per i test."""
    import json
    if http is None:
        from .context import http_text as http
    p = dict(assets="btc", metrics="CapMVRVCur", frequency="1d", page_size=10000, start_time="2011-01-01")
    rows, tok = [], None
    for _ in range(20):
        j = json.loads(http(URL, dict(p, **({"next_page_token": tok} if tok else {}))))
        rows += j.get("data", [])
        tok = j.get("next_page_token")
        if not tok:
            break
    if not rows:
        raise RuntimeError("CoinMetrics: nessun dato")
    d = pd.DataFrame(rows)
    s = pd.Series(pd.to_numeric(d["CapMVRVCur"], errors="coerce").to_numpy(),
                  index=pd.to_datetime(d["time"]).dt.tz_localize(None).dt.normalize())
    return _clean(s)


def _clean(s: pd.Series) -> pd.Series:
    s = s.dropna()
    s = s[s > 0]
    s.index = pd.to_datetime(s.index).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index().rename("mvrv")


def _read(path: Path) -> pd.Series:
    if not path.exists():
        return pd.Series(dtype=float, name="mvrv")
    d = pd.read_csv(path, parse_dates=["date"])
    return _clean(d.set_index("date")["mvrv"])


def _save(s: pd.Series, path: Path) -> bool:
    """Salva gli ultimi ~5 anni; riscrive il file solo se il contenuto cambia."""
    s = s[s.index > s.index[-1] - pd.Timedelta(days=KEEP_DAYS)]
    buf = io.StringIO()
    pd.DataFrame({"date": s.index.strftime("%Y-%m-%d"), "mvrv": s.round(6).to_numpy()}).to_csv(buf, index=False)
    txt = buf.getvalue()
    if path.exists() and path.read_text() == txt:
        return False
    path.write_text(txt)
    return True


def load(data_dir: Path, http=None, today: pd.Timestamp | None = None, study: Path = STUDY) -> tuple[pd.Series, str | None]:
    """Serie completa e nota sulla fonte (None se il dato è fresco). Scarica solo se l'ultimo dato è più vecchio di ieri."""
    today = today or _today()
    path = Path(data_dir) / FILE
    cache = _read(path)
    note = None
    if cache.empty or cache.index[-1] < today - pd.Timedelta(days=1):
        try:
            full = fetch(http)
            _save(full, path)
            return full, None
        except Exception as e:  # noqa: BLE001
            note = f"CoinMetrics non risponde ({type(e).__name__}): dato del {cache.index[-1]:%d/%m/%Y}" if not cache.empty else None
            if cache.empty:
                raise
    base = _read(study) if study and Path(study).exists() else pd.Series(dtype=float, name="mvrv")
    full = _clean(pd.concat([base[~base.index.isin(cache.index)], cache]))
    return full, note


def prices(data_dir: Path, old: Path = OLD_PRICES) -> pd.Series:
    """Chiusure giornaliere di BTC dai dati del repo (data/spot.csv ha la precedenza sui prezzi congelati dello studio)."""
    parts = []
    if old and Path(old).exists():
        o = pd.read_csv(old, index_col=0, parse_dates=True)["close"]
        parts.append(o)
    sp = Path(data_dir) / "spot.csv"
    if sp.exists():
        s = pd.read_csv(sp, index_col="date", parse_dates=True)["close"]
        parts = [p[p.index < s.index[0]] for p in parts] + [s]
    if not parts:
        return pd.Series(dtype=float)
    return _clean(pd.concat(parts)).rename("close")


# ------------------------------------------------------------------ calcolo
def zones(m: pd.Series, win: int = WIN, q: float = Q) -> pd.DataFrame:
    """Soglie e zone con i soli `win` giorni PRECEDENTI (stessa definizione di research/utxo_pl/up_engine.zones)."""
    lo = m.rolling(win, min_periods=win).quantile(q).shift(1)
    hi = m.rolling(win, min_periods=win).quantile(1 - q).shift(1)
    z = pd.Series("norm", index=m.index)
    z[m <= lo] = "cap"
    z[m >= hi] = "eup"
    z[lo.isna()] = None
    return pd.DataFrame({"mvrv": m, "lo": lo, "hi": hi, "zone": z})


def since(z: pd.Series) -> pd.Timestamp:
    """Primo giorno della striscia continua che arriva all'ultimo giorno."""
    v = z.to_numpy()
    i = len(v) - 1
    while i > 0 and v[i - 1] == v[-1]:
        i -= 1
    return z.index[i]


def entries(z: pd.Series, zone: str, start: str = STATS_FROM, gap: int = GAP) -> list[pd.Timestamp]:
    """Ingressi in `zone`: giorni in zona senza altri giorni in zona nei `gap` giorni precedenti."""
    days = z.index[z == zone]
    out, last = [], None
    for d in days:
        if (last is None or (d - last).days > gap) and d >= pd.Timestamp(start):
            out.append(d)
        last = d
    return out


def stats(z: pd.Series, px: pd.Series, zone: str) -> dict:
    """Variazione di BTC a 30 e 90 giorni dopo ogni ingresso (chiusura del giorno d'ingresso → chiusura dopo h giorni)."""
    ev = entries(z, zone)
    res = {"n_entries": len(ev), "episodes": []}
    for d in ev:
        ep = {"date": d.strftime("%Y-%m-%d")}
        for h in HORIZONS:
            e = d + pd.Timedelta(days=h)
            ep[f"d{h}"] = round(float(px[e] / px[d] - 1) * 100, 1) if d in px.index and e in px.index else None
        res["episodes"].append(ep)
    for h in HORIZONS:
        r = [ep[f"d{h}"] for ep in res["episodes"] if ep[f"d{h}"] is not None]
        s = pd.Series(r, dtype=float)
        res[f"d{h}"] = ({"n": len(r), "median": round(float(s.median()), 1), "min": round(float(s.min()), 1),
                         "max": round(float(s.max()), 1), "up": int((s > 0).sum())} if r else {"n": 0})
    return res


def frase(side: str | None, zone: str) -> str:
    """UNA frase per la posizione aperta (side long/short, None = flat), basata sullo studio research/utxo_pl."""
    if zone == "cap":
        if side == "short":
            return ("Il mercato è in zona di capitolazione: storicamente vicino ai minimi di ciclo, il rischio di rimbalzo è più "
                    "alto. Nei test chiudere lo short per questo non ha migliorato W3.2 in modo dimostrabile (lezione 125): la "
                    "posizione resta gestita dalle regole di W3.2.")
        if side == "long":
            return ("Zona di capitolazione: storicamente i minimi di ciclo sono caduti qui, ma il fondo può durare mesi. Il long "
                    "resta gestito dalle regole di W3.2.")
        return "Zona di capitolazione: storicamente vicino ai minimi di ciclo. È contesto: gli ingressi li decide W3.2."
    if zone == "eup":
        if side == "long":
            return ("Il mercato è in zona di euforia, che spesso arriva all'inizio dei rally: nei test chiudere il long per questo "
                    "è stato dannoso (−15.000 $ dal 2021, lezione 125). La posizione resta gestita dalle regole di W3.2.")
        if side == "short":
            return ("Zona di euforia: storicamente i massimi di ciclo sono caduti qui, ma l'euforia può durare mesi. Lo short "
                    "resta gestito dalle regole di W3.2.")
        return "Zona di euforia: storicamente vicino ai massimi di ciclo. È contesto: gli ingressi li decide W3.2."
    return "Ciclo in zona normale: nessuna indicazione dall'indicatore; la posizione la gestisce W3.2."


def build(data_dir: Path, side: str | None = None, http=None, today: pd.Timestamp | None = None,
          study: Path = STUDY, old_prices: Path = OLD_PRICES) -> dict:
    """report["onchain"]: stato attuale, soglie, serie di 2 anni per il grafico, statistiche e frase per la posizione."""
    m, note = load(data_dir, http=http, today=today, study=study)
    Z = zones(m)
    Z = Z[Z["zone"].notna()]
    if Z.empty:
        raise RuntimeError("MVRV: meno di 4 anni di dati")
    last = Z.iloc[-1]
    d0 = Z.index[-1]
    cur = float(last["mvrv"])
    prev = m[m.index < d0].iloc[-WIN:]
    zone = last["zone"]
    px = prices(data_dir, old=old_prices)
    ch = Z[Z.index > d0 - pd.Timedelta(days=CHART_DAYS)]
    st = {k: stats(Z["zone"], px, k) for k in ("cap", "eup")}
    return {
        "date": d0.strftime("%Y-%m-%d"), "mvrv": round(cur, 4), "zone": zone, "zone_name": ZONE_NAME[zone],
        "since": since(Z["zone"]).strftime("%Y-%m-%d"),
        "lo": round(float(last["lo"]), 4), "hi": round(float(last["hi"]), 4), "fixed": [1.0, 3.0],
        "below_1": cur < 1.0, "above_3": cur > 3.0,
        "pctile": round(float((prev < cur).mean()) * 100, 1),
        "side": side, "frase": frase(side, zone), "stats": st,
        "series": {"d": [x.strftime("%Y-%m-%d") for x in ch.index], "v": [round(float(x), 4) for x in ch["mvrv"]],
                   "lo": [round(float(x), 4) for x in ch["lo"]], "hi": [round(float(x), 4) for x in ch["hi"]]},
        "source_note": note, "note": NOTE,
    }


def side_of(weekly: dict | None) -> str | None:
    """Verso della posizione aperta di W3.2 su BTC (None se flat o in attesa d'ingresso)."""
    if weekly and weekly.get("status") in ("aperto", "uscita") and weekly.get("side") in ("long", "short"):
        return weekly["side"]
    return None
