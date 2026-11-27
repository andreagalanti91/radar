"""macd_sol · innesti MACD in W3.2 SENZA copiare né modificare radar/weekly.py: si avvolge weekly_bars (come w32_asset2/lib.csim).
W-F: filtro sugli ingressi; W-U: uscita aggiuntiva inserita nelle colonne di distribuzione (eseguita il lunedì come le altre).
Soglie in % del prezzo (conversione R4: P_IS SOL 32,11 $) o assolute in $ (solo SOL). PREREG.md §7."""
import sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "w32_asset2"))
import lib as L  # noqa: E402

P_IS = 32.11
PCT = dict(lo=-50 / P_IS * 100, hi=-3 / P_IS * 100, sell=10 / P_IS * 100)     # −155,7 / −9,34 / +31,1 (% del prezzo)
ABS = dict(lo=-50.0, hi=-3.0, sell=10.0)


def macd(c):
    m = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    return m, m.ewm(span=9, adjust=False).mean()


def sim(f, s, e=L.CEND, r=0.25, k=2.5, gate=None, mode=None, unit="pct"):
    """mode None = W3.2 invariata; 'F' = W-F; 'U' = W-U. unit 'pct' o 'abs'."""
    eng = L.W; orig = eng.weekly_bars; th = PCT if unit == "pct" else ABS
    def wb(ff, _o=orig):
        w = _o(ff)
        if mode:
            m, _ = macd(w["close"]); x = 100 * m / w["close"] if unit == "pct" else m
            if mode == "F":
                w["long"] = w["long"] & (x < th["sell"]); w["short"] = w["short"] & (x >= th["hi"])
            elif mode == "U":
                w["dist_long"] = w["dist_long"] | (x >= th["sell"]); w["dist_short"] = w["dist_short"] | (x <= th["lo"])
        return w
    eng.weekly_bars = wb
    try:
        return L.csim(f, s, e, r, k, gate)
    finally:
        eng.weekly_bars = orig


if __name__ == "__main__":      # verifica di riproduzione (solo numeri di riferimento già pubblicati)
    ref = {"BTC": ("2021-01-01", 84820), "ETH": ("2021-01-11", 39572), "SOL": ("2021-01-11", 80661)}
    for a, (s, v) in ref.items():
        f = L.cfeats(a); E = str(f.index[-1].date())
        x0 = L.omet(L.csim(f, s, E))["fin"]; x1 = L.omet(sim(f, s, E))["fin"]
        print(f"{a} dal {s}: lib.csim {x0:,.0f} $ · motore.sim senza innesto {x1:,.0f} $ · riferimento {v:,} $ · "
              f"{'OK' if round(x0) == round(x1) and abs(x1 - v) <= 1 else 'DIVERSO'}")
