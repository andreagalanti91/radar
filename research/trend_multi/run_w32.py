"""trend_multi · combinazione descrittiva con W3.2 BTC (radar.weekly.simulate sui dati del repo). Uscita: risultati_w32.txt."""
import importlib.util, sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402
spec = importlib.util.spec_from_file_location("t10", ROOT / "research" / "top10_w3" / "run.py"); T10 = importlib.util.module_from_spec(spec); spec.loader.exec_module(T10)
import tm_lib as T
OUT = T.D.parent
fb, _ = T10.feats("BTC")
w = W.simulate(fb, "2021-01-01")["equity"]
log = [f"W3.2 BTC dal 2021: finale {w.iloc[-1]:,.0f} $ (atteso 78.474), dati fino al {w.index[-1].date()}"]
etf = pd.read_csv(OUT / "etf_equity.csv.gz", index_col=0, parse_dates=True); u2 = pd.read_csv(OUT / "u2_equity.csv.gz", index_col=0, parse_dates=True)
legs = {"ETF V1": etf["V1 LF 1/3/12 mens."], "ETF V2": etf["V2 LS 1/3/12 mens."], "60/40": etf["60/40 SPY/IEF"],
        "U2-V1": u2["U2-V1 LF 1/3/12"], "U2-V2": u2["U2-V2 LS 1/3/12"], "T-bill": etf["Liquidità (T-bill)"],
        "USDT 0%": etf["Liquidità (T-bill)"] * 0 + 1}
end = min(w.index[-1], etf.index[-1])
cal = pd.date_range("2021-01-01", end)
wd = (w / w.iloc[0]).reindex(cal).ffill()
def met(e):
    yrs = (e.index[-1] - e.index[0]).days / 365.25; c = e.iloc[-1] ** (1 / yrs) - 1; dd = (e / e.cummax() - 1).min()
    return f"finale {10000 * e.iloc[-1]:>8,.0f} $ | CAGR {c * 100:5.1f}% | DD {dd * 100:6.1f}% | CAGR/DD {c / abs(dd):.2f}"
log.append(f"{'W3.2 da sola':28s} {met(wd)}")
for n, e in legs.items():
    ed = e.loc[:end]; ed = (ed / ed.loc[:"2021-01-01"].iloc[-1]).reindex(cal).ffill().fillna(1.0)
    mw, me = wd.resample("ME").last().pct_change().dropna(), ed.resample("ME").last().pct_change().dropna()
    log.append(f"\n{n}: {met(ed)} | correlazione mensile con W3.2 {mw.corr(me):+.2f} ({len(mw)} mesi)")
    rw, re = wd.pct_change().fillna(0), ed.pct_change().fillna(0)
    for a in (0.7, 0.5, 0.3):
        eq, vw, ve = [], a, 1 - a
        for d in cal:
            vw *= 1 + rw[d]; ve *= 1 + re[d]; eq.append(vw + ve)
            if d.is_month_end:
                tot = vw + ve; vw, ve = a * tot, (1 - a) * tot
        log.append(f"  {int(a * 100)}% W3.2 / {int((1 - a) * 100)}% {n:7s}    {met(pd.Series(eq, cal))}")
print("\n".join(log)); (OUT / "risultati_w32.txt").write_text("\n".join(log))
