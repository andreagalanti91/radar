"""Schema multi-timeframe del file dell'utente (1D direzione, 4H conferma, 1H ingresso) su BTC/ETH/SOL con costi da esecuzione manuale."""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "../intraday2")
import numpy as np, pandas as pd
from engine import Exits, Sizing, Costs, load_all, backtest, metrics
ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
def rsi(s, n=14):
    d = s.diff(); u = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean(); return 100 - 100 / (1 + u / dn)
def adx(b, n=14):
    h, l, c = b["high"], b["low"], b["close"]; tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = tr.ewm(alpha=1 / n, adjust=False).mean(); up, dn = h.diff(), -l.diff()
    p = 100 * up.where((up > dn) & (up > 0), 0.0).ewm(alpha=1 / n, adjust=False).mean() / a; m = 100 * dn.where((dn > up) & (dn > 0), 0.0).ewm(alpha=1 / n, adjust=False).mean() / a
    return (100 * (p - m).abs() / (p + m)).ewm(alpha=1 / n, adjust=False).mean()
def htf(b, rule):
    x = b.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(); return x
def down(s, idx): return s.shift(1).reindex(idx, method="ffill")       # ultimo valore di barra CHIUSA
def signals(b, use_4h=True, use_1h=True):
    c = b["close"]; d, h4 = htf(b, "1D"), htf(b, "4h")
    dm = ema(d.close, 12) - ema(d.close, 26)
    dl = (ema(d.close, 50) > ema(d.close, 200)) & (rsi(d.close) > 50) & (dm > ema(dm, 9)); ds = (ema(d.close, 50) < ema(d.close, 200)) & (rsi(d.close) < 50) & (dm < ema(dm, 9))
    hm = ema(h4.close, 12) - ema(h4.close, 26); ha = adx(h4) > 20
    hl = (hm > ema(hm, 9)) & (rsi(h4.close) > 50) & ha; hs = (hm < ema(hm, 9)) & (rsi(h4.close) < 50) & ha
    L, S = down(dl.astype(float), b.index) > 0, down(ds.astype(float), b.index) > 0
    if use_4h: L, S = L & (down(hl.astype(float), b.index) > 0), S & (down(hs.astype(float), b.index) > 0)
    day = b.index.floor("D"); tp = (b["high"] + b["low"] + c) / 3
    vw = (tp * b["volume"]).groupby(day).cumsum() / b["volume"].groupby(day).cumsum()
    obv = (np.sign(c.diff()).fillna(0) * b["volume"]).cumsum(); ob = obv > ema(obv, 20)
    if use_1h: tl, ts = (c > vw) & (c.shift() <= vw.shift()) & ob, (c < vw) & (c.shift() >= vw.shift()) & ~ob
    else: tl, ts = L & ~L.shift(fill_value=False), S & ~S.shift(fill_value=False)
    return pd.DataFrame({"side": (L & tl).astype(int) - (S & ts).astype(int)})
EX = {"E4 (stop 2 ATR, metà a +2R, pareggio, trailing 3 ATR)": Exits(stop_atr=2.0, tp=[(2.0, 0.5)], tp_unit="R", be_after_tp1=True, trail_atr=3.0, trail_after_tp1=True, reverse_exit=False, reverse_entry=False),
      "Costante 5%/10% dell'utente": Exits(stop_atr=2.0, tp=[(0.05, 0.5), (0.10, 0.5)], tp_unit="pct", be_after_tp1=True, reverse_exit=False, reverse_entry=False)}
SZ = Sizing(mode="risk", risk_pct=0.01, leverage=3, allocation="equal", max_exposure=3.0)
CO = {"costi base": Costs(), "esecuzione a mano (slippage 0,10%)": Costs(slip=0.001, slip_stop=0.0015)}
bars = load_all("1h"); rows = []
for assets in (["BTCUSDT"], list(bars)):
    B = {a: bars[a] for a in assets}
    for var, kw in (("1D+4H+1H (schema completo)", {}), ("1D+4H (ingresso al cambio di stato)", dict(use_1h=False)), ("1D+1H (senza conferma 4H)", dict(use_4h=False))):
        sg = {a: signals(B[a], **kw) for a in assets}
        for en, ex in EX.items():
            for cn, co in CO.items():
                if en.startswith("Costante") and cn != "costi base": continue
                r = {}
                for per, (s, e) in {"tot": ("2021-01-01", None), "is": ("2021-01-01", "2023-12-31"), "oos": ("2024-01-01", None)}.items():
                    r[per] = metrics(backtest(B, sg, ex, SZ, co, start=s, end=e))
                t = r["tot"]; rows.append(dict(asset="BTC" if len(assets) == 1 else "BTC+ETH+SOL", variante=var, uscita=en.split(" ")[0], costi=cn, finale=round(t["final"]), dd=round(t["max_dd"], 1),
                                               trade_mese=round(t["trades_per_month"], 1), wr=round(t.get("win_rate", 0)), pf=round(t.get("pf", 0), 2), R=round(t.get("exp_R", 0), 3),
                                               pf_2123=round(r["is"].get("pf", 0), 2), pf_24=round(r["oos"].get("pf", 0), 2), fin_24=round(r["oos"]["final"])))
d = pd.DataFrame(rows); d.to_csv("mtf_intraday.csv", index=False); pd.set_option("display.width", 250); print(d.to_string(index=False))
