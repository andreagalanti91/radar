"""Cono di probabilità a 30 giorni per BTC (card "Fra 30 giorni", report["cone"]).

NON è una previsione di direzione (lezioni 112–113: non prevedibile). È la dispersione attesa del prezzo calcolata dalla
volatilità corrente con il metodo scelto e calibrato in research/cono30 (PREREG 17b9a49): bootstrap a blocchi di 10 giorni dei
rendimenti giornalieri storici (chiusura, massimo, minimo) standardizzati e riscalati alla volatilità di oggi, con la sola
deriva media storica. Funzioni pure, solo numpy/pandas, seme fisso. Nessun effetto su W3.2.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

H = 30               # orizzonte in giorni
BLOCK = 10           # lunghezza dei blocchi del bootstrap
N_PATH = 10_000      # cammini (lo studio ne usava 2.000: stesso metodo, meno rumore fra un giro e l'altro)
SEED = 20261123
COVER80, COVER50 = 78, 52   # copertura reale 2018–26 degli intervalli 80% e 50% (research/cono30/README.md)
SEED_FILE = Path(__file__).with_name("cone_seed.csv")   # BTC giornaliero 2014 → 08/2019 (prima dell'archivio Binance)
LOG = "cone_log.csv"
LOG_COLS = ["date", "price", "lo80", "lo50", "hi50", "hi80", "target", "close30", "in50", "in80"]
TITLE = "Fra 30 giorni"
NOTE = ("Probabilità calcolate dalla volatilità attuale, non dalla direzione: il tool non sa prevedere se BTC salirà o scenderà "
        f"(lezioni 112–113). Affidabilità storica: intervallo 80% centrato nel {COVER80}% dei casi.")
MIN_DIST = 0.03      # supporto/resistenza a meno del 3% dal prezzo: esclusi (li tocca il rumore di una giornata)
ROUND_DIST = 0.05    # numeri tondi: almeno al 5% dal prezzo


# ------------------------------------------------------------------ calcolo (funzioni pure)
def sigma_series(r: np.ndarray) -> np.ndarray:
    """Volatilità giornaliera corrente: σ² = ½ media(r², 30 g) + ½ media(r², 365 g), giorni fino a t compreso."""
    r2 = pd.Series(np.asarray(r, dtype=float)) ** 2
    return np.sqrt(0.5 * r2.rolling(30).mean() + 0.5 * r2.rolling(365).mean()).to_numpy()


def prepare(ohlc: pd.DataFrame) -> dict:
    """Da OHLC giornaliero (colonne high, low, close; ordinato) → storia standardizzata, volatilità e deriva correnti."""
    c, hi, lo = (ohlc[k].to_numpy(dtype=float) for k in ("close", "high", "low"))
    if len(c) < 365 + BLOCK + 2:
        raise ValueError("storia troppo corta per il cono (servono almeno 377 giorni)")
    r, u, d = np.log(c[1:] / c[:-1]), np.log(hi[1:] / c[:-1]), np.log(lo[1:] / c[:-1])
    sig = sigma_series(r)
    sp = sig[:-1]                                   # σ del giorno prima: standardizza il rendimento del giorno dopo
    ok = ~np.isnan(sp)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = [np.where(sp[ok] > 0, x[1:][ok] / sp[ok], 0.0) for x in (r, u, d)]
    m = float(z[0].mean())
    return {"zr": z[0] - m, "zu": z[1] - m, "zd": z[2] - m, "sigma": float(sig[-1]), "drift": float(r.mean()), "price": float(c[-1])}


def simulate(zr, zu, zd, sigma: float, drift: float = 0.0, n_paths: int = N_PATH, seed: int = SEED, horizon: int = H,
             block: int = BLOCK) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cammini a blocchi. Restituisce (ln chiusura finale, ln massimo, ln minimo) rispetto al prezzo di partenza."""
    zr, zu, zd = (np.asarray(x, dtype=float) for x in (zr, zu, zd))
    nb = -(-horizon // block)
    starts = np.random.default_rng(seed).integers(0, len(zr) - block + 1, size=(n_paths, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_paths, nb * block)[:, :horizon]
    step = zr[idx] * sigma + drift
    cum = np.cumsum(step, axis=1)
    prev = cum - step
    return cum[:, -1], (prev + zu[idx] * sigma + drift).max(axis=1), (prev + zd[idx] * sigma + drift).min(axis=1)


def interval(end: np.ndarray, price: float, mass: float) -> tuple[float, float]:
    """Intervallo centrale (mass = 0,8 → quantili 10–90%) del prezzo di chiusura a fine orizzonte."""
    lo, hi = np.quantile(end, [(1 - mass) / 2, (1 + mass) / 2])
    return price * math.exp(lo), price * math.exp(hi)


def touch_prob(mx: np.ndarray, mn: np.ndarray, price: float, level: float) -> float:
    """Probabilità che il massimo (livello sopra il prezzo) o il minimo (sotto) tocchi il livello entro l'orizzonte."""
    if level <= 0 or price <= 0:
        return float("nan")
    k = math.log(level / price)
    return float((mx >= k).mean()) if k > 0 else float((mn <= k).mean()) if k < 0 else 1.0


def touch_probs(ohlc: pd.DataFrame, prices: list[float], n_paths: int = N_PATH, seed: int = SEED) -> list[float]:
    """Probabilità di toccare ciascun prezzo entro l'orizzonte con gli STESSI cammini del cono (stessa storia, stesso seme di
    compute): serve alla mappa dei livelli (radar/livelli.py). Il calcolo del cono non cambia."""
    ohlc = ohlc[["high", "low", "close"]].dropna()
    p = prepare(ohlc)
    _, mx, mn = simulate(p["zr"], p["zu"], p["zd"], p["sigma"], p["drift"], n_paths, seed)
    return [touch_prob(mx, mn, p["price"], float(x)) for x in prices]


def round_levels(price: float) -> list[float]:
    """Due numeri tondi: il primo sotto e il primo sopra il prezzo, distanti almeno il 5% (61.000 → 50.000 e 70.000)."""
    mag = 10 ** math.floor(math.log10(price))
    ratio = price / mag
    step = mag if ratio >= 4 else mag / 2 if ratio >= 2 else mag / 5
    below = math.floor(price * (1 - ROUND_DIST) / step) * step
    above = math.ceil(price * (1 + ROUND_DIST) / step) * step
    return [x for x in (below, above) if x > 0]


def pick_levels(price: float, weekly: dict | None, levels: dict | None) -> list[dict]:
    """Livelli scelti dal tool: trailing/stop della posizione W3.2 aperta, supporto e resistenza più vicini (ad almeno il 3%),
    due numeri tondi. Ordinati dal più alto al più basso."""
    out: list[dict] = []

    def add(label, px):
        try:
            px = float(px)
        except (TypeError, ValueError):
            return
        if not (px > 0) or abs(px / price - 1) < 0.002 or any(abs(px / o["price"] - 1) < 0.005 for o in out):
            return
        out.append({"label": label, "price": px})
    w = weekly or {}
    if w.get("status") == "aperto":
        add("Trailing W3.2" if w.get("trail") else "Stop W3.2", w.get("trail") or w.get("stop0"))
    lv = levels or {}
    for key, label, side in (("resistances", "Resistenza", 1), ("supports", "Supporto", -1)):
        near = sorted((o for o in lv.get(key) or [] if isinstance(o, dict) and o.get("price")
                       and (float(o["price"]) / price - 1) * side >= MIN_DIST), key=lambda o: abs(float(o["price"]) - price))
        if near:
            add(label, near[0]["price"])
    for px in round_levels(price):
        add("Numero tondo", px)
    return sorted(out, key=lambda o: -o["price"])


def _it(x: float, d: int = 0) -> str:
    return f"{abs(x):,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def describe(weekly: dict | None, liqmap: dict | None) -> list[dict]:
    """Righe SOLO descrittive (non entrano nel calcolo): flusso perp di W3.2 e fascia di liquidazione stimata più vicina.
    Il flusso come deriva del cono non ha passato il test (research/cono30/ADDENDUM.md); le liquidazioni non sono testabili."""
    out = []
    try:
        fl = float((weekly or {}).get("flow"))
        if fl == fl:
            out.append({"label": "Flusso perp", "text": f"in {'acquisto' if fl > 0 else 'vendita'} ({'+' if fl > 0 else '−'}{_it(fl, 1)})"})
    except (TypeError, ValueError):
        pass
    try:
        near = [o for o in ((liqmap or {}).get("nearest_above"), (liqmap or {}).get("nearest_below")) if isinstance(o, dict) and o.get("price")]
        if near:
            o = min(near, key=lambda o: abs(float(o.get("dist_pct") or 0)))
            dp = float(o.get("dist_pct") or 0)
            out.append({"label": "Liquidazioni", "text": f"fascia stimata più vicina a {_it(float(o['price']))} $ "
                                                         f"({'+' if dp > 0 else '−'}{_it(dp, 1)}%) · stima"})
    except (TypeError, ValueError):
        pass
    return out


def compute(ohlc: pd.DataFrame, weekly: dict | None = None, levels: dict | None = None, n_paths: int = N_PATH,
            seed: int = SEED) -> dict:
    """Blocco della card da OHLC giornaliero con indice di date. Stesso input → stesso output (seme fisso)."""
    ohlc = ohlc[["high", "low", "close"]].dropna()
    p = prepare(ohlc)
    price, date = p["price"], pd.Timestamp(ohlc.index[-1])
    end, mx, mn = simulate(p["zr"], p["zu"], p["zd"], p["sigma"], p["drift"], n_paths, seed)
    i80, i50 = interval(end, price, 0.8), interval(end, price, 0.5)
    rows = []
    for o in pick_levels(price, weekly, levels):
        pr = touch_prob(mx, mn, price, o["price"])
        rows.append({**o, "price": round(o["price"], 0), "side": "su" if o["price"] > price else "giu",
                     "dist_pct": round((o["price"] / price - 1) * 100, 1), "prob": round(pr * 100)})
    return {"title": TITLE, "asset": "BTC", "date": str(date.date()), "target": str((date + pd.Timedelta(days=H)).date()),
            "horizon": H, "price": round(price, 2),
            "i80": [round(i80[0], 0), round(i80[1], 0)], "i50": [round(i50[0], 0), round(i50[1], 0)],
            "vol30_pct": round(p["sigma"] * math.sqrt(H) * 100, 1), "drift30_pct": round((math.exp(p["drift"] * H) - 1) * 100, 1),
            "levels": rows, "note": NOTE, "cover80": COVER80, "cover50": COVER50,
            "method": ("Bootstrap a blocchi di 10 giorni dei rendimenti giornalieri di BTC dal 2015, riscalati alla volatilità di oggi "
                       "(metà ultimi 30 giorni, metà ultimo anno), con la sola crescita media storica. Calibrato sul 2018–26: "
                       f"l'intervallo 80% ha contenuto il prezzo nel {COVER80}% dei casi, quello 50% nel {COVER50}%. "
                       "Non prevede salti mai visti né cambi improvvisi di volatilità; contro la semplice frequenza storica il "
                       "guadagno di precisione è piccolo.")}


# ------------------------------------------------------------------ registro delle previsioni
def update_log(path: Path, cone: dict | None, close: pd.Series) -> dict:
    """Una riga per data (mai doppioni), esito a 30 giorni quando la chiusura della data obiettivo esiste. Mai eccezioni."""
    path = Path(path)
    try:
        try:
            log = pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=LOG_COLS)
            if list(log.columns) != LOG_COLS:
                raise ValueError("colonne inattese")
        except Exception as e:  # noqa: BLE001
            print(f"[cono] registro illeggibile, messo da parte: {e!r}")
            if not path.is_file():
                raise
            path.replace(path.with_suffix(".csv.bad"))
            log = pd.DataFrame(columns=LOG_COLS)
        log = log.fillna("").drop_duplicates("date", keep="first")
        if cone and cone["date"] not in set(log["date"]):
            row = {"date": cone["date"], "price": cone["price"], "lo80": cone["i80"][0], "lo50": cone["i50"][0],
                   "hi50": cone["i50"][1], "hi80": cone["i80"][1], "target": cone["target"], "close30": "", "in50": "", "in80": ""}
            log = pd.concat([log, pd.DataFrame([{k: str(v) for k, v in row.items()}])], ignore_index=True)
        cl = {str(pd.Timestamp(k).date()): float(v) for k, v in close.dropna().items()}
        for i, r in log.iterrows():
            if r["close30"] == "" and r["target"] in cl:
                c = cl[r["target"]]
                log.loc[i, ["close30", "in50", "in80"]] = [f"{c:.2f}", str(int(float(r["lo50"]) <= c <= float(r["hi50"]))),
                                                           str(int(float(r["lo80"]) <= c <= float(r["hi80"])))]
        log = log.sort_values("date").reset_index(drop=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        log.to_csv(path, index=False)
        done = log[log["in80"] != ""]
        return {"n": int(len(done)), "in80": int((done["in80"] == "1").sum()), "in50": int((done["in50"] == "1").sum())}
    except Exception as e:  # noqa: BLE001
        print(f"[cono] registro non aggiornato: {e!r}")
        return {"n": 0, "in80": 0, "in50": 0}


# ------------------------------------------------------------------ giro
def history(f: pd.DataFrame, seed_file: Path | None = SEED_FILE) -> pd.DataFrame:
    """Storia giornaliera per il bootstrap: 2014 → 08/2019 dal file fisso + il frame del radar (stessa serie dello studio)."""
    f = f[["high", "low", "close"]].dropna()
    try:
        s = pd.read_csv(seed_file, index_col=0, parse_dates=True)[["high", "low", "close"]] if seed_file else None
    except Exception as e:  # noqa: BLE001
        print(f"[cono] storia 2014–2019 non disponibile, uso solo i dati del radar: {e!r}")
        s = None
    if s is not None and len(f):
        f = pd.concat([s[s.index < f.index[0]], f])
    return f[~f.index.duplicated(keep="last")].sort_index()


def build(f: pd.DataFrame, report: dict | None = None, data_dir: Path | None = None) -> dict | None:
    """report["cone"]. None se il calcolo non è possibile; il registro non blocca mai la card."""
    report = report or {}
    cone = compute(history(f), report.get("weekly"), report.get("levels"))
    cone["context"] = describe(report.get("weekly"), report.get("liqmap"))
    cone["context_note"] = "Solo descrizione: flusso e liquidazioni non cambiano le probabilità (nei test non le migliorano in modo affidabile)."
    if data_dir is not None:
        cone["live"] = update_log(Path(data_dir) / LOG, cone, f["close"])
    return cone


if __name__ == "__main__":
    import json
    from .data import load_all
    from .features import build_features
    from .levels import compute as _lv
    _f = build_features(load_all())
    print(json.dumps(build(_f, {"levels": _lv(_f)}), indent=1, ensure_ascii=False))
