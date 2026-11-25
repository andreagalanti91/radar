"""W3.2 asset ciclo 2 · azioni · serie candidate di FLUSSO dai volumi giornalieri (Q3). Nessun rendimento.

Non sceglie la definizione (la fissa il PREREG): fornisce le serie standard, giornaliere e alla chiusura del venerdì (W-FRI).
Formule (OHLC rettificati: il rapporto (C-L)/(H-L) non dipende dal fattore di rettifica; volume Yahoo rettificato per frazionamenti):
  clv        = ((C-L) - (H-C)) / (H-L)            (0 se H == L)
  mfv        = clv × V                             (money flow volume)
  cmf20      = Σ20 mfv / Σ20 V                     Chaikin Money Flow 20 sedute, in [-1, 1]
  ad         = Σ mfv (cumulata dal primo dato)     Accumulation/Distribution line (livello: dipende dall'inizio, non confrontabile)
  ad_slope20 = pendenza dei minimi quadrati della linea A/D sulle ultime 20 sedute / media del volume 20 sedute
               (la semplice variazione (ad - ad[-20]) / Σ20 V coincide esattamente con cmf20, quindi non è una serie nuova)
  obv        = Σ sign(ΔC) × V                      On-Balance Volume (sulla chiusura rettificata)
  obv_slope20= pendenza della retta dei minimi quadrati di obv sulle ultime 20 sedute / media del volume 20 sedute
               (unità: volumi medi per seduta; > 0 accumulo, < 0 distribuzione)
  obv_chg20  = (obv - obv[-20]) / Σ20 V            variante semplice, in [-1, 1]
Settimanale: valore all'ultima seduta di ogni settimana W-FRI (la stessa seduta della decisione di ma_lib.s1_weekly) e cmf_w,
Chaikin "settimanale" sulle candele settimanali (Σ4 mfv_w / Σ4 V_w, 4 settimane ~ 20 sedute).
Qualità: sedute con volume 0 o mancante -> mfv 0 e contate in zero_vol; se le sedute valide nella finestra sono < 15 il valore è NaN.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

N = 20
MIN_VALID = 15


def daily(f: pd.DataFrame) -> pd.DataFrame:
    H, L, C = f["high"], f["low"], f["close"]
    V = f["volume"].astype(float)
    valid = V.notna() & (V > 0)
    V0 = V.where(valid, 0.0)
    rng = (H - L)
    clv = (((C - L) - (H - C)) / rng.where(rng > 0)).fillna(0.0)
    mfv = clv * V0
    sv = V0.rolling(N).sum()
    nvalid = valid.astype(int).rolling(N).sum()
    ok = (nvalid >= MIN_VALID) & (sv > 0)
    out = pd.DataFrame(index=f.index)
    out["cmf20"] = (mfv.rolling(N).sum() / sv).where(ok)
    ad = mfv.cumsum()
    out["ad"] = ad
    x = np.arange(N, dtype=float)
    x = x - x.mean()

    def slope(s: pd.Series) -> pd.Series:
        return s.rolling(N).apply(lambda y: float(np.dot(x, y - y.mean()) / np.dot(x, x)), raw=True)

    out["ad_slope20"] = (slope(ad) / (sv / N)).where(ok)
    obv = (np.sign(C.diff()).fillna(0.0) * V0).cumsum()
    out["obv"] = obv
    out["obv_slope20"] = (slope(obv) / (sv / N)).where(ok)
    out["obv_chg20"] = ((obv - obv.shift(N)) / sv).where(ok)
    out["volume"] = V
    out["zero_vol"] = (~valid).astype(int)
    return out


def weekly(f: pd.DataFrame, fl: pd.DataFrame | None = None, rule: str = "W-FRI") -> pd.DataFrame:
    fl = daily(f) if fl is None else fl
    cols = ["cmf20", "ad_slope20", "obv_slope20", "obv_chg20"]
    w = fl[cols].resample(rule).last()
    w["day"] = f["close"].resample(rule).apply(lambda s: s.index[-1] if len(s) else pd.NaT)
    wk = f[["high", "low", "close", "volume"]].resample(rule).agg({"high": "max", "low": "min", "close": "last", "volume": "sum"})
    rng = wk["high"] - wk["low"]
    clv = (((wk["close"] - wk["low"]) - (wk["high"] - wk["close"])) / rng.where(rng > 0)).fillna(0.0)
    mfv = clv * wk["volume"]
    w["cmf_w4"] = mfv.rolling(4).sum() / wk["volume"].rolling(4).sum().where(lambda s: s > 0)
    w["zero_vol"] = fl["zero_vol"].resample(rule).sum()
    return w.dropna(subset=["day"])
