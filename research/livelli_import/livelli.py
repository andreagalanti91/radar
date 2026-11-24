"""Livelli di BTC: supporti, resistenze, medie, Fibonacci, liquidazioni e zone di coincidenza.

Modulo autonomo (solo pandas/numpy), pensato per essere copiato in radar/ (per esempio radar/livelli.py).
Ingresso: DataFrame giornaliero con indice di date e colonne open, high, low, close (come data/spot.csv del radar).
Uscita di build(): dizionario pronto per la dashboard (stesso schema di oggi.json in questa cartella).

Definizioni (identiche allo studio LIVELLI_BTC.md):
- supporto = minimo di swing settimanale: il minimo della settimana e' il piu' basso delle K settimane prima e dopo; e' noto
  (confermato) K settimane dopo; resta attivo LIFE giorni e finche' una chiusura giornaliera non scende sotto;
- resistenza = massimo di swing settimanale, specchiato;
- in piu': minimo delle ultime 5 settimane (non ancora confermato), medie a 50/200 giorni e 40/200 settimane, ritracciamenti
  di Fibonacci 50/61,8/78,6% fra il minimo del ciclo e il massimo storico, livelli storici passati a mano;
- zona = livelli consecutivi a meno di GAP l'uno dall'altro, almeno due.
I livelli sono CONTESTO, non segnali: nei test non danno un vantaggio d'ingresso.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

K, LIFE, GAP = 5, 365 * 3, 0.032


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
    return [{"da": z[0]["prezzo"], "a": z[-1]["prezzo"], "n": len(z),
             "ruolo": "sopra" if z[0]["prezzo"] > prezzo else "sotto" if z[-1]["prezzo"] < prezzo else "a cavallo",
             "tipi": sorted({q["tipo"] for q in z}), "liq": round(sum(q.get("usd", 0.0) for q in z), 2)} for z in out]


def build(d: pd.DataFrame, liq_long: list[tuple] | None = None, liq_short: list[tuple] | None = None, liq_fonte: str = "",
          ciclo_min: tuple[str, str] | None = ("2022-06-01", "2023-03-01"), storici: list[tuple] | None = None,
          raggio: tuple[float, float] = (0.6, 1.6), candele: int = 420) -> dict:
    """d: giornaliero fino all'ultima chiusura COMPLETA. liq_long / liq_short: [(prezzo, miliardi di $), ...] dalla mappa delle
    liquidazioni (stime). storici: [(prezzo, descrizione), ...] livelli di riferimento gia' superati (es. massimo del ciclo 2021).
    Ritorna prezzo, ATR, livelli ordinati dal piu' alto, zone e le ultime candele per il grafico."""
    d = d[["open", "high", "low", "close"]].dropna().sort_index()
    c, px, last = d["close"], float(d["close"].iloc[-1]), d.index[-1]
    wc = weekly(d)["close"]
    lv = [{"prezzo": s["prezzo"], "tipo": s["tipo"],
           "cosa": f"{'minimo' if s['tipo'] == 'supporto' else 'massimo'} di swing settimanale del {s['formato'].strftime('%m/%Y')}", "fonte": "prezzo"}
          for s in attivi(d)]
    rec = d.iloc[-35:]
    lv.append({"prezzo": float(rec["low"].min()), "tipo": "supporto",
               "cosa": f"minimo delle ultime 5 settimane ({rec['low'].idxmin().strftime('%d/%m')}), non ancora confermato", "fonte": "prezzo"})
    if ciclo_min:
        ath, lo_c = float(d["high"].max()), float(d.loc[ciclo_min[0]:ciclo_min[1], "low"].min())
        for f_, nm in ((0.5, "50%"), (0.618, "61,8%"), (0.786, "78,6%")):
            lv.append({"prezzo": ath - f_ * (ath - lo_c), "tipo": "fibonacci", "cosa": f"ritracciamento di Fibonacci {nm} dal minimo del ciclo al massimo storico", "fonte": "prezzo"})
    for nm, v in (("SMA 200 settimane", _sma(wc, 200)), ("SMA 40 settimane", _sma(wc, 40)), ("SMA 200 giorni", _sma(c, 200)), ("SMA 50 giorni", _sma(c, 50))):
        if np.isfinite(v):
            lv.append({"prezzo": v, "tipo": "media", "cosa": nm, "fonte": "prezzo"})
    for p, cosa in storici or []:
        lv.append({"prezzo": float(p), "tipo": "storico", "cosa": cosa, "fonte": "prezzo"})
    for p, b in liq_long or []:
        lv.append({"prezzo": float(p), "tipo": "liq_long", "cosa": f"liquidazioni di long stimate: {b:.2f} miliardi $".replace(".", ","), "fonte": liq_fonte, "usd": float(b)})
    for p, b in liq_short or []:
        lv.append({"prezzo": float(p), "tipo": "liq_short", "cosa": f"liquidazioni di short stimate: {b:.2f} miliardi $".replace(".", ","), "fonte": liq_fonte, "usd": float(b)})
    lv = [x for x in lv if px * raggio[0] <= x["prezzo"] <= px * raggio[1]]
    for x in lv:
        x["ruolo"], x["dist"] = ("sopra" if x["prezzo"] > px else "sotto"), x["prezzo"] / px - 1
    lv.sort(key=lambda x: -x["prezzo"])
    return {"data": str(last.date()), "prezzo": px, "atr": atr(d), "livelli": lv, "zone": zone(lv, px), "liq_fonte": liq_fonte,
            "candele": [{"d": str(t.date()), "o": round(r.open), "h": round(r.high), "l": round(r.low), "c": round(r.close)} for t, r in d.iloc[-candele:].iterrows()]}


if __name__ == "__main__":      # prova: python livelli.py btc_giornaliero.csv
    import json
    import sys
    df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "btc_giornaliero.csv", parse_dates=[0], index_col=0)
    o = build(df, liq_long=[(54145, 0.7487), (53312, 0.7117), (51368, 1.18), (50535, 0.9971)], liq_short=[(76915, 0.7208), (91076, 0.8396), (92742, 0.9299), (93853, 0.8866)],
              liq_fonte="Coinglass 24/11/2026 09:01", storici=[(69000, "massimo del ciclo 2021, superato a marzo 2024")])
    print(json.dumps({k: v for k, v in o.items() if k != "candele"}, ensure_ascii=False, indent=1)[:1500])
