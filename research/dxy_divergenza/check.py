"""Controllo descrittivo veloce (non preregistrato): divergenza ribassista RSI(14) giornaliera sul dollaro (DXY).
Evento = nuovo massimo di 60 giorni del DXY con RSI sotto il massimo RSI dei 60 giorni di almeno 2 punti, RSI del massimo
precedente > 65; un evento ogni 30 giorni. Dopo l'evento: DXY e BTC a 10/30/60 giorni contro un giorno qualsiasi."""
import pandas as pd, numpy as np, requests, os, sys
H = os.path.dirname(os.path.abspath(__file__))
def yahoo(sym):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}"
    j = requests.get(u, params={"range": "max", "interval": "1d"}, headers={"User-Agent": "research-client/1.0"}, timeout=60).json()["chart"]["result"][0]
    s = pd.Series(j["indicators"]["quote"][0]["close"], index=pd.to_datetime(j["timestamp"], unit="s").normalize()).dropna()
    return s[~s.index.duplicated()]
def yahoo_daily(sym):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}"
    out = []
    for a, b in [(946684800, 1420070400), (1420070400, 1800000000)]:   # 2000-2015, 2015-oggi: barre giornaliere
        j = requests.get(u, params={"period1": a, "period2": b, "interval": "1d"}, headers={"User-Agent": "research-client/1.0"}, timeout=60).json()["chart"]["result"][0]
        out.append(pd.Series(j["indicators"]["quote"][0]["close"], index=pd.to_datetime(j["timestamp"], unit="s").normalize()))
    s = pd.concat(out).dropna(); return s[~s.index.duplicated()].sort_index()
import io
d = pd.read_csv(os.path.join(H, "dollaro_fred.csv")); d.columns = ["date", "v"]; d = d[pd.to_numeric(d.v, errors="coerce").notna()]   # curl https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS; d.columns = ["date", "v"]; d = d[pd.to_numeric(d.v, errors="coerce").notna()]
dxy = pd.Series(d.v.astype(float).values, index=pd.to_datetime(d.date))   # indice ampio del dollaro (Fed), giornaliero
b = pd.read_csv(os.path.join(H, "..", "..", "data", "spot.csv")); btc = pd.Series(b.close.values, index=pd.to_datetime(b.date))
def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)
r = rsi(dxy); ev = []; last = None
for i in range(60, len(dxy)):
    w = dxy.iloc[i-60:i]; rw = r.iloc[i-60:i]
    if dxy.iloc[i] > w.max() and rw.max() > 65 and r.iloc[i] < rw.max() - 2:
        d = dxy.index[i]
        if last is None or (d - last).days > 30: ev.append(d); last = d
def fwd(s, d, h):
    a = s[s.index >= d]; t = s[s.index >= d + pd.Timedelta(days=h)]
    return np.nan if len(a) == 0 or len(t) == 0 or d < s.index[0] else t.iloc[0] / a.iloc[0] - 1
out = []
for nome, s, da in [("Dollaro dal 2006", dxy, "2006"), ("Dollaro dal 2019-09", dxy, "2019-09-01"), ("BTC dal 2019-09", btc, "2019-09-01")]:
    e = [d for d in ev if d >= pd.Timestamp(da)]
    row = [f"{nome}: {len(e)} eventi"]
    for h in (10, 30, 60):
        x = np.array([fwd(s, d, h) for d in e]); x = x[~np.isnan(x)]
        base = np.array([fwd(s, d, h) for d in s[s.index >= da].index[::5]]); base = base[~np.isnan(base)]
        if len(x): row.append(f"{h}g mediana {np.median(x)*100:+.1f}% (giù {np.mean(x<0)*100:.0f}%) · qualsiasi {np.median(base)*100:+.1f}% (giù {np.mean(base<0)*100:.0f}%)")
    out.append(" | ".join(row))
c = pd.concat([dxy.pct_change(), btc.pct_change()], axis=1, keys=["dxy", "btc"], sort=True).dropna()
c = c[c.index >= "2019-09-01"].resample("W").sum()
out.append(f"Correlazione settimanale dollaro-BTC dal 2019-09: {c.dxy.corr(c.btc):+.2f}; ultime 52 settimane: {c.dxy.iloc[-52:].corr(c.btc.iloc[-52:]):+.2f}")
out.append(f"Oggi: dollaro (FRED DTWEXBGS) {dxy.iloc[-1]:.2f} ({dxy.index[-1].date()}), RSI {r.iloc[-1]:.1f}; ultimi eventi: {[d.date().isoformat() for d in ev[-6:]]}")
open(os.path.join(H, "risultati.txt"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
