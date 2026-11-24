"""Livelli di BTC: supporti, resistenze, medie, Fibonacci, liquidazioni e zone di coincidenza (report["livelli"]).

Portato da research/livelli_import/livelli.py (studio LIVELLI_BTC.md): definizioni e costanti invariate, cambia solo l'interfaccia
(liquidazioni da più fonti, probabilità di tocco dal cono, giro orario). È l'UNICA mappa dei livelli (motore unico): Oggi (card
"Livelli e probabilità a 30 giorni", forbice), Grafico (linee, fasce e tabella completa), Pre-analisi (radar/preview.py) e riepilogo
Telegram "Oggi" leggono solo report["livelli"]; il browser ricalcola distanze e probabilità sul prezzo live con "tocco" (cone.touch_grid). Ingresso: giornaliero con indice di date e colonne
open, high, low, close fino all'ultima chiusura COMPLETA (data/spot.csv tramite i caricatori del radar).

Definizioni (identiche allo studio LIVELLI_BTC.md):
- supporto = minimo di swing settimanale: il minimo della settimana è il più basso delle K settimane prima e dopo; è noto
  (confermato) K settimane dopo; resta attivo LIFE giorni e finché una chiusura giornaliera non scende sotto;
- resistenza = massimo di swing settimanale, specchiato;
- in più: minimo delle ultime 5 settimane (non ancora confermato), medie a 50/200 giorni e 40/200 settimane, ritracciamenti
  di Fibonacci 50/61,8/78,6% fra il minimo del ciclo (giugno 2022 – marzo 2023) e il massimo storico, livello storico 69.000 $
  (massimo del 2021, superato nel 2024: riferimento, NON resistenza attiva);
- zona = livelli consecutivi a meno di GAP l'uno dall'altro, almeno due.
I livelli sono CONTESTO, non segnali: nei test non danno un vantaggio d'ingresso. Nessun effetto su W3.2.

Liquidazioni (stime tranne le on-chain): cluster significativi della mappa stimata del tool (radar/liqmap.py, clusters),
livelli reali on-chain di Hyperliquid/Lighter (report["liqmap"]["onchain"], radar/liqsnap.py) e il file facoltativo
data/coinglass_levels.json compilato a mano (schema nel README; più vecchio di COINGLASS_MAX_DAYS giorni = ignorato e dichiarato).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

K, LIFE, GAP = 5, 365 * 3, 0.032
CICLO_MIN = ("2022-06-01", "2023-03-01")
STORICI = [(69000.0, "massimo del ciclo 2021, superato a marzo 2024: livello storico, non una resistenza attiva")]
CANDELE = 365                     # grafico dei Dettagli: ultimo anno
PER_LATO = 3                      # fasce di liquidazione per lato e per fonte (le più vicine al prezzo: la scala resta leggibile)
COINGLASS_FILE = "coinglass_levels.json"
COINGLASS_MAX_DAYS = 7            # oltre: il file è ignorato (la card lo dice)
FONTE_STIMA = "stima Radar (OI Binance+OKX)"
FONTE_ONCHAIN = "on-chain Hyperliquid/Lighter, reale"
NOTA = ("I livelli sono contesto, non un segnale: dopo la rottura di un supporto (15 casi dal 2018) il prezzo è sceso ancora "
        "di circa l'11% nel punto peggiore dei 14 giorni successivi, più o meno quanto dopo un qualsiasi forte calo, e in 6 casi "
        "su 15 è rientrato sopra il livello entro 5 giorni.")
NOTA_LIQ = "Le liquidazioni sono stime (mappa del tool, Coinglass), tranne quelle on-chain di Hyperliquid e Lighter, che sono posizioni reali."
NOTA_PROB = ("Probabilità di toccare il livello almeno una volta entro 30 giorni, calcolate dalla volatilità attuale e non dalla "
             "direzione: il tool non sa prevedere se BTC salirà o scenderà.")
DEF = ("Supporti e resistenze: minimi e massimi di swing settimanali (estremo delle 5 settimane prima e dopo, noti 5 settimane "
       "dopo), attivi per 3 anni e finché una chiusura giornaliera non li rompe; più il minimo delle ultime 5 settimane, non "
       "ancora confermato. Medie mobili e Fibonacci sono riportati perché molto seguiti, non perché testati.")


# ------------------------------------------------------------------ calcolo (funzioni pure, dallo studio)
def weekly(d: pd.DataFrame) -> pd.DataFrame:
    """Candele settimanali chiuse la domenica (solo settimane complete)."""
    w = d.resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return w[w.index <= d.index[-1]]


def swings(d: pd.DataFrame, k: int = K) -> list[dict]:
    """Massimi e minimi di swing settimanali con la data da cui sono noti."""
    w = weekly(d)
    hi, lo = w["high"].to_numpy(), w["low"].to_numpy()
    out = []
    for j in range(k, len(w) - k):
        conf = w.index[j + k] + pd.Timedelta(days=1)
        if lo[j] == lo[j - k:j + k + 1].min():
            out.append({"tipo": "supporto", "prezzo": float(lo[j]), "formato": w.index[j], "confermato": conf})
        if hi[j] == hi[j - k:j + k + 1].max():
            out.append({"tipo": "resistenza", "prezzo": float(hi[j]), "formato": w.index[j], "confermato": conf})
    return out


def attivi(d: pd.DataFrame, k: int = K, life: int = LIFE) -> list[dict]:
    """Supporti e resistenze di swing confermati, non scaduti e non ancora rotti da una chiusura giornaliera."""
    last, out = d.index[-1], []
    for s in swings(d, k):
        if s["confermato"] > last or s["confermato"] + pd.Timedelta(days=life) < last:
            continue
        seg = d.loc[s["confermato"]:, "close"]
        rotto = (seg < s["prezzo"]).any() if s["tipo"] == "supporto" else (seg > s["prezzo"]).any()
        if not rotto:
            out.append(s)
    return out


def _sma(s: pd.Series, n: int) -> float:
    return float(s.rolling(n).mean().iloc[-1])


def atr(d: pd.DataFrame, n: int = 14) -> float:
    c = d["close"]
    tr = pd.concat([d["high"] - d["low"], (d["high"] - c.shift()).abs(), (d["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / n, adjust=False).mean().iloc[-1])


def zone(livelli: list[dict], prezzo: float, gap: float = GAP) -> list[dict]:
    out, cur = [], []
    for x in sorted(livelli, key=lambda q: q["prezzo"]):
        if cur and x["prezzo"] / cur[-1]["prezzo"] - 1 > gap:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
        cur.append(x)
    if len(cur) >= 2:
        out.append(cur)
    res = []
    for z in out:
        per: dict[str, float] = {}
        for q in z:
            if q.get("usd"):
                per[q["fonte"]] = round(per.get(q["fonte"], 0.0) + q["usd"], 4)
        res.append({"da": z[0]["prezzo"], "a": z[-1]["prezzo"], "n": len(z),
                    "ruolo": "sopra" if z[0]["prezzo"] > prezzo else "sotto" if z[-1]["prezzo"] < prezzo else "a cavallo",
                    "tipi": sorted({q["tipo"] for q in z}), "liq": round(sum(q.get("usd", 0.0) for q in z), 2), "liq_fonti": per})
    return res


def _mld(b: float) -> str:
    """0,72 miliardi $ / 39 milioni $."""
    return f"{b:.2f} miliardi $".replace(".", ",") if b >= 0.1 else f"{max(1, round(b * 1000))} milioni $"


def build(d: pd.DataFrame, liq_long: list[tuple] | None = None, liq_short: list[tuple] | None = None, liq_fonte: str = "",
          ciclo_min: tuple[str, str] | None = CICLO_MIN, storici: list[tuple] | None = None,
          raggio: tuple[float, float] = (0.6, 1.6), candele: int = 420, liq: list[dict] | None = None) -> dict:
    """d: giornaliero fino all'ultima chiusura COMPLETA. liq_long / liq_short: [(prezzo, miliardi di $), ...] di una sola fonte
    (liq_fonte, stime); liq: righe di più fonti {"tipo": "liq_long"|"liq_short", "prezzo", "mld", "fonte", "reale"}.
    storici: [(prezzo, descrizione), ...] livelli di riferimento già superati. Ritorna prezzo, ATR, livelli ordinati dal più
    alto, zone e le ultime candele per il grafico."""
    d = d[["open", "high", "low", "close"]].dropna().sort_index()
    c, px, last = d["close"], float(d["close"].iloc[-1]), d.index[-1]
    wc = weekly(d)["close"]
    lv = [{"prezzo": s["prezzo"], "tipo": s["tipo"],
           "cosa": f"{'minimo' if s['tipo'] == 'supporto' else 'massimo'} di swing settimanale del {s['formato'].strftime('%m/%Y')}",
           "fonte": "prezzo", "confermato": str(s["confermato"].date())}
          for s in attivi(d)]
    rec = d.iloc[-35:]
    lv.append({"prezzo": float(rec["low"].min()), "tipo": "supporto", "provvisorio": True,
               "cosa": f"minimo delle ultime 5 settimane ({rec['low'].idxmin().strftime('%d/%m')}), non ancora confermato", "fonte": "prezzo"})
    if ciclo_min:
        ath, lo_c = float(d["high"].max()), float(d.loc[ciclo_min[0]:ciclo_min[1], "low"].min())
        for f_, nm in ((0.5, "50%"), (0.618, "61,8%"), (0.786, "78,6%")):
            lv.append({"prezzo": ath - f_ * (ath - lo_c), "tipo": "fibonacci",
                       "cosa": f"ritracciamento di Fibonacci {nm} dal minimo del ciclo al massimo storico", "fonte": "prezzo"})
    for nm, v in (("SMA 200 settimane", _sma(wc, 200)), ("SMA 40 settimane", _sma(wc, 40)), ("SMA 200 giorni", _sma(c, 200)), ("SMA 50 giorni", _sma(c, 50))):
        if np.isfinite(v):
            lv.append({"prezzo": v, "tipo": "media", "cosa": nm, "fonte": "prezzo"})
    for p, cosa in storici or []:
        lv.append({"prezzo": float(p), "tipo": "storico", "cosa": cosa, "fonte": "prezzo"})
    rows = [{"tipo": "liq_long", "prezzo": p, "mld": b, "fonte": liq_fonte, "reale": False} for p, b in liq_long or []]
    rows += [{"tipo": "liq_short", "prezzo": p, "mld": b, "fonte": liq_fonte, "reale": False} for p, b in liq_short or []]
    for r in rows + list(liq or []):
        b, lato = float(r["mld"]), "long" if r["tipo"] == "liq_long" else "short"
        lv.append({"prezzo": float(r["prezzo"]), "tipo": r["tipo"], "fonte": r["fonte"], "usd": b, "reale": bool(r.get("reale")),
                   "cosa": f"liquidazioni di {lato} {'reali' if r.get('reale') else 'stimate'}: {_mld(b)}"})
    lv = [x for x in lv if px * raggio[0] <= x["prezzo"] <= px * raggio[1]]
    for x in lv:
        x["ruolo"], x["dist"] = ("sopra" if x["prezzo"] > px else "sotto"), x["prezzo"] / px - 1
    lv.sort(key=lambda x: -x["prezzo"])
    return {"data": str(last.date()), "prezzo": px, "atr": atr(d), "livelli": lv, "zone": zone(lv, px), "liq_fonte": liq_fonte,
            "candele": [{"d": str(t.date()), "o": round(r.open), "h": round(r.high), "l": round(r.low), "c": round(r.close)}
                        for t, r in d.iloc[-candele:].iterrows()]}


# ------------------------------------------------------------------ candele per il grafico (sezione Grafico della dashboard)
def serie(f: pd.DataFrame) -> dict:
    """Giornaliero completo in forma compatta: t0 (prima data) + array o/h/l/c (dollari interi) e v (volume spot in BTC, intero).
    Date consecutive dal t0; se mancano giorni c'è anche l'array d delle date. 1D dal giornaliero, 1W e 1M aggregati nel browser."""
    d = f[["open", "high", "low", "close"]].dropna()
    vol = f["spot_vol"].reindex(d.index) if "spot_vol" in f else pd.Series(np.nan, index=d.index)
    full = pd.date_range(d.index[0], d.index[-1], freq="D")
    out = {"t0": str(d.index[0].date()), "n": int(len(d)),
           "o": [round(x) for x in d["open"]], "h": [round(x) for x in d["high"]], "l": [round(x) for x in d["low"]],
           "c": [round(x) for x in d["close"]], "v": [None if v != v else round(float(v)) for v in vol]}
    if len(full) != len(d):
        out["d"] = [str(t.date()) for t in d.index]
    return out


# ------------------------------------------------------------------ fonti delle liquidazioni
def coinglass(path: Path, now: pd.Timestamp | None = None, max_days: int = COINGLASS_MAX_DAYS) -> tuple[list[dict], dict]:
    """File facoltativo compilato a mano: {"data": "AAAA-MM-GG HH:MM", "long": [[prezzo, miliardi], ...], "short": [...]}.
    Ritorna (righe, stato). Stato: assente / valido / vecchio (oltre max_days: righe ignorate) / illeggibile. Mai eccezioni."""
    path = Path(path)
    if not path.is_file():
        return [], {"stato": "assente"}
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
        t = pd.Timestamp(str(j["data"]))
        fonte = f"Coinglass, {t.strftime('%d/%m/%Y %H:%M')}"
        rows = [{"tipo": tipo, "prezzo": float(p), "mld": float(b), "fonte": fonte, "reale": False}
                for key, tipo in (("long", "liq_long"), ("short", "liq_short")) for p, b in j.get(key) or []
                if float(p) > 0 and float(b) > 0]
    except Exception as e:  # noqa: BLE001
        print(f"[livelli] {path.name} illeggibile, ignorato: {e!r}")
        return [], {"stato": "illeggibile"}
    now = now if now is not None else pd.Timestamp.now(tz="Europe/Rome").tz_localize(None)
    age = (now - t) / pd.Timedelta(days=1)
    st = {"data": t.strftime("%Y-%m-%d %H:%M"), "fonte": fonte, "giorni": round(age, 1), "n": len(rows)}
    if age > max_days:
        return [], {**st, "stato": "vecchio"}
    return rows, {**st, "stato": "valido"}


def liq_inputs(report: dict | None, data_dir: Path | None = None, now: pd.Timestamp | None = None) -> tuple[list[dict], list[dict], dict]:
    """(righe per build, fonti presenti, stato del file Coinglass). Prima la mappa stimata del tool (cluster significativi
    di radar/liqmap.clusters, già nel report), poi i livelli reali on-chain, poi il file Coinglass."""
    lm = (report or {}).get("liqmap") or {}
    rows: list[dict] = []
    oc = lm.get("onchain") or {}
    for src, fonte, reale in ((lm, FONTE_STIMA, False), (oc, FONTE_ONCHAIN, True)):
        for key, tipo in (("below", "liq_long"), ("above", "liq_short")):
            cl = [o for o in src.get(key) or [] if isinstance(o, dict) and o.get("price") and o.get("usd") and (reale or o.get("sig"))]
            for o in sorted(cl, key=lambda o: abs(float(o["price"]) - float(src.get("price") or src.get("mid") or o["price"])))[:PER_LATO]:   # le più vicine
                rows.append({"tipo": tipo, "prezzo": float(o["price"]), "mld": float(o["usd"]) / 1e9, "fonte": fonte, "reale": reale})
    cg_rows, cg = coinglass(Path(data_dir) / COINGLASS_FILE, now) if data_dir is not None else ([], {"stato": "assente"})
    rows += cg_rows
    fonti = []
    for f in dict.fromkeys(r["fonte"] for r in rows):
        rr = [r for r in rows if r["fonte"] == f]
        when = cg.get("data") if f == cg.get("fonte") else lm.get("ts") if f == FONTE_STIMA else oc.get("ts")
        fonti.append({"fonte": f, "reale": rr[0]["reale"], "n": len(rr), "agg": when})
    return rows, fonti, cg


# ------------------------------------------------------------------ unione con il cono (probabilità di tocco a 30 giorni)
def add_probs(out: dict, probs: list[float], weekly: dict | None = None, trail_prob: float | None = None) -> dict:
    """Probabilità (0–100) per livello e per zona (bordo più vicino; 100 se la zona contiene il prezzo) e riga del trailing W3.2."""
    lv = out["livelli"]
    for x, p in zip(lv, probs):
        x["prob"] = None if p is None or p != p else round(p * 100)
    by = {x["prezzo"]: x.get("prob") for x in lv}
    for z in out["zone"]:
        z["prob"] = 100 if z["ruolo"] == "a cavallo" else by.get(z["da"] if z["ruolo"] == "sopra" else z["a"])
    w = weekly or {}
    if w.get("status") == "aperto" and (w.get("trail") or w.get("stop0")):
        tp, px = float(w.get("trail") or w.get("stop0")), out["prezzo"]
        lato = "short" if w.get("side") == "short" else "long"
        lv.append({"prezzo": tp, "tipo": "trailing", "fonte": "W3.2", "ruolo": "sopra" if tp > px else "sotto", "dist": tp / px - 1,
                   "cosa": f"{'trailing' if w.get('trail') else 'stop'} della posizione {lato} aperta, controllo orario",
                   "prob": None if trail_prob is None or trail_prob != trail_prob else round(trail_prob * 100)})
        lv.sort(key=lambda x: -x["prezzo"])
    return out


def compute(f: pd.DataFrame, report: dict | None = None, data_dir: Path | None = None, now: pd.Timestamp | None = None,
            n_paths: int | None = None) -> dict:
    """report["livelli"]: mappa dei livelli con fonti delle liquidazioni e probabilità di tocco dal cono (stessi cammini)."""
    from . import cone
    report = report or {}
    d = f[["open", "high", "low", "close"]].dropna()
    rows, fonti, cg = liq_inputs(report, data_dir, now)
    out = build(d, liq=rows, storici=STORICI, candele=CANDELE)
    w = report.get("weekly") or {}
    tp = float(w.get("trail") or w.get("stop0") or 0) if w.get("status") == "aperto" else 0.0
    prices = [x["prezzo"] for x in out["livelli"]] + ([tp] if tp > 0 else [])
    # probabilità di tocco dai quantili dei cammini del cono (cone.touch_grid): gli stessi numeri che la dashboard ricalcola sul
    # prezzo live con la stessa funzione in JS; alla chiusura coincidono con il calcolo del server
    grid = cone.touch_grid(cone.history(f), **({"n_paths": n_paths} if n_paths else {}))
    pr = [cone.grid_touch_prob(grid, out["prezzo"], x) for x in prices]
    add_probs(out, pr[:len(out["livelli"])], w, pr[-1] if tp > 0 else None)
    i80, i50 = cone.grid_interval(grid, out["prezzo"], 0.8), cone.grid_interval(grid, out["prezzo"], 0.5)
    for x in out["livelli"]:
        x["prezzo"], x["dist"] = round(x["prezzo"], 2), round(x["dist"], 5)
    for z in out["zone"]:
        z["da"], z["a"] = round(z["da"], 2), round(z["a"], 2)
    out.update({"atr": round(out["atr"], 1), "fonti_liq": fonti, "coinglass": cg, "nota": NOTA, "nota_liq": NOTA_LIQ, "definizioni": DEF,
                "orizzonte": cone.H, "tocco": grid, "i80": [round(i80[0]), round(i80[1])], "i50": [round(i50[0]), round(i50[1])],
                "nota_prob": NOTA_PROB, "serie": serie(f)})
    out.pop("liq_fonte", None)
    out.pop("candele", None)          # il grafico usa "serie" (tutto il giornaliero con i volumi)
    return out


if __name__ == "__main__":      # prova: python -m radar.livelli
    from .data import DATA_DIR, load_all
    from .features import build_features
    o = compute(build_features(load_all()), {}, DATA_DIR)
    print(json.dumps({k: v for k, v in o.items() if k != "candele"}, ensure_ascii=False, indent=1)[:3000])
