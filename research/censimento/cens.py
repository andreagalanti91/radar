import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "../ta_settimanale"); sys.path.insert(0, "../nuova_strategia")
import numpy as np, pandas as pd, lib, ns
from radar import weekly as W
f, fl = lib.load(); wk = W.weekly_bars(fl)
w = fl[["open", "high", "low", "close", "volume"]].resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
w = w[w.index <= fl.index[-1]]; c, h, l, v = w["close"], w["high"], w["low"], w["volume"]
ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
def rsi(s, n=14):
    d = s.diff(); u = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean(); return 100 - 100 / (1 + u / dn)
tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
up, dn = h.diff(), -l.diff(); pdm = up.where((up > dn) & (up > 0), 0.0); mdm = dn.where((dn > up) & (dn > 0), 0.0)
pdi = 100 * pdm.ewm(alpha=1 / 14, adjust=False).mean() / atr; mdi = 100 * mdm.ewm(alpha=1 / 14, adjust=False).mean() / atr
adx = (100 * (pdi - mdi).abs() / (pdi + mdi)).ewm(alpha=1 / 14, adjust=False).mean()
def machine(enter, exit_):
    st, s = [], 0
    for a, b in zip(enter.fillna(False), exit_.fillna(False)):
        if s and b: s = 0
        elif not s and a: s = 1
        st.append(bool(s))
    return pd.Series(st, enter.index)
m12 = ema(c, 12) - ema(c, 26); sma20 = c.rolling(20).mean(); sd20 = c.rolling(20).std()
tp = (h + l + c) / 3; vwap = (tp * v).rolling(26).sum() / v.rolling(26).sum()
def poc(i, n=52, bins=40):
    if i < n: return np.nan
    cc, vv = c.iloc[i - n + 1:i + 1].to_numpy(), v.iloc[i - n + 1:i + 1].to_numpy()
    hist, edges = np.histogram(cc, bins=bins, weights=vv); k = hist.argmax(); return (edges[k] + edges[k + 1]) / 2
pocs = pd.Series([poc(i) for i in range(len(w))], w.index)
obv = (np.sign(c.diff()).fillna(0) * v).cumsum()
hi52, lo52 = h.rolling(52).max(), l.rolling(52).min()
ten, kij = (h.rolling(9).max() + l.rolling(9).min()) / 2, (h.rolling(26).max() + l.rolling(26).min()) / 2
spa, spb = ((ten + kij) / 2).shift(26), ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
r = rsi(c); sr = (r - r.rolling(14).min()) / (r.rolling(14).max() - r.rolling(14).min()); K = sr.rolling(3).mean(); D = K.rolling(3).mean()
dl = fl["close"]; e200 = dl.ewm(span=200, adjust=False).mean()
flow = fl["pf14z"].shift(1).resample("W-SUN").last().reindex(w.index)
fund = fl["funding"].fillna(0).rolling(7).mean().resample("W-SUN").last().reindex(w.index)
oi = f["oi"].resample("W-SUN").last().reindex(w.index) if "oi" in f else pd.Series(np.nan, w.index)
def fred(name):
    s = pd.read_csv(f"data/{name}.csv", index_col=0, parse_dates=True).iloc[:, 0]; s = pd.to_numeric(s, errors="coerce").dropna()
    return s.resample("W-SUN").last().reindex(w.index).ffill()          # venerdì: noto alla chiusura della domenica
ndx, spx, vix, dxy = fred("NASDAQCOM"), fred("SP500"), fred("VIXCLS"), fred("DTWEXBGS")
S = {"01 EMA 20/50": (c > ema(c, 20)) & (ema(c, 20) > ema(c, 50)), "01b EMA 200 giornaliera": (dl > e200).resample("W-SUN").last().reindex(w.index),
     "02 MACD": m12 > ema(m12, 9), "03 RSI 14": r > 50, "04 ADX": (adx > 20) & (pdi > mdi),
     "05 Bollinger": machine(c > sma20 + 2 * sd20, c < sma20), "06 ATR chandelier": c > c.rolling(22).max() - 3 * atr, "07 VWAP": c > vwap,
     "08 Volume Profile": c > pocs, "09 OBV": obv > ema(obv, 20), "10 CVD perp": flow > 0, "11 Fibonacci": c > lo52 + 0.618 * (hi52 - lo52),
     "12 Ichimoku": (c > pd.concat([spa, spb], axis=1).max(axis=1)) & (ten > kij), "13 Stochastic RSI": K > D,
     "14 Open Interest": (oi > oi.shift(4)) & (c > c.shift(4)), "15 Funding non caldo": fund < W.FUND_HOT,
     "I1 Nasdaq > SMA40": ndx > ndx.rolling(40).mean(), "I2 S&P 500 > SMA40": spx > spx.rolling(40).mean(), "I3 Dollaro < SMA40": dxy < dxy.rolling(40).mean(), "I4 VIX < 25": vix < 25}
PV = ["01 EMA 20/50", "01b EMA 200 giornaliera", "02 MACD", "03 RSI 14", "04 ADX", "05 Bollinger", "06 ATR chandelier", "07 VWAP", "08 Volume Profile", "09 OBV", "11 Fibonacci", "12 Ichimoku", "13 Stochastic RSI"]
score = pd.concat([S[k].astype(float) for k in PV], axis=1).mean(axis=1)
for th in (0.5, 0.6, 0.7): S[f"V voto ≥ {int(th * 100)}% (13 indicatori)"] = score >= th
S["V+ voto ≥ 60% e CVD perp > 0"] = (score >= 0.6) & (flow > 0)
S["M macro: Nasdaq su e dollaro giù"] = S["I1 Nasdaq > SMA40"] & S["I3 Dollaro < SMA40"]
w2, w2p = lib.sim_w2(fl, wk), lib.sim_w2(fl, wk, start="2018-01-01", end="2020-12-31"); m0, m0p = lib.met(w2), lib.met(w2p)
bh, bhp = lib.met(lib.bh(fl)), lib.met(lib.bh(fl, "2014-01-01", "2020-12-31"))
rows = []
for k, st in S.items():
    st = st.fillna(False).astype(bool); tgt = st.astype(int)
    a = lib.met(lib.sim_state(fl, tgt)); p = lib.met(lib.sim_state(fl, tgt, "2014-01-01", "2020-12-31")) if not k.startswith(("10", "14", "15", "V+")) else None
    g = lib.sim_w2(fl, wk, gate=st); gp = lib.sim_w2(fl, wk, start="2018-01-01", end="2020-12-31", gate=st); mg, mgp = lib.met(g), lib.met(gp)
    rows.append(dict(indicatore=k, solo_21=a["final"], dd_21=a["dd"], tr=a["n"], wr=a["wr"], solo_1420=p["final"] if p else None, dd_1420=p["dd"] if p else None,
                     w2f_21=mg["final"], w2f_dd=mg["dd"], camb="%d/%d" % lib.changed(w2, g), w2f_1820=mgp["final"], w2f_dd1820=mgp["dd"], camb_pre="%d/%d" % lib.changed(w2p, gp),
                     rialzista_ora=bool(st.iloc[-1])))
d = pd.DataFrame(rows); d.to_csv("censimento.csv", index=False); pd.set_option("display.width", 250)
print(d.to_string(index=False))
print(f"\nRiferimenti: buy&hold 2021→ {bh['final']} (DD {bh['dd']}) · 2014–20 {bhp['final']} (DD {bhp['dd']}) | W2 2021→ {m0['final']} (DD {m0['dd']}) · 2018–20 {m0p['final']} (DD {m0p['dd']})")
print("punteggio attuale (quota di indicatori rialzisti):", round(float(score.iloc[-1]), 2))
