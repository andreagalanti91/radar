"""Quanto è affidabile il "movimento atteso" dalle opzioni? DVOL (Deribit, giornaliero dal 2021) contro movimento reale di BTC
a 7 e 28 giorni (data/spot.csv). Descrittivo: quota di casi dentro ±1σ e ±2σ (attesa teorica 68% e 95%)."""
import time, requests, pandas as pd, numpy as np
H = {"User-Agent": "radar-research/1.0"}
rows, end = [], int(time.time() * 1000)
while True:
    r = requests.get("https://www.deribit.com/api/v2/public/get_volatility_index_data", headers=H, timeout=30,
                     params=dict(currency="BTC", start_timestamp=1609459200000, end_timestamp=end, resolution="1D")).json()["result"]
    rows += r["data"]
    if not r.get("continuation") or not r["data"]: break
    end = r["continuation"]
dv = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c"]).drop_duplicates("t")
dv["d"] = pd.to_datetime(dv.t, unit="ms").dt.normalize(); dv = dv.set_index("d").c.sort_index()
dv.to_csv("dati/dvol_1d.csv")
sp = pd.read_csv("../../data/spot.csv"); dc = sp.columns[0]; cc = "close" if "close" in sp else sp.columns[4]
v = pd.to_numeric(sp[dc], errors="coerce")
sp[dc] = pd.to_datetime(v, unit="ms").dt.normalize() if v.notna().all() else pd.to_datetime(sp[dc].astype(str), utc=True).dt.tz_localize(None).dt.normalize()
px = sp.set_index(dc)[cc].astype(float).sort_index(); px = px[~px.index.duplicated()]
out = []
for n in (7, 28):
    df = pd.DataFrame({"iv": dv, "p": px}).dropna()
    df["r"] = np.log(px.shift(-n).reindex(df.index) / df.p)
    df["s"] = df.iv / 100 * np.sqrt(n / 365)
    df = df.dropna()
    z = (df.r / df.s).abs()
    for per, m in (("2021-2023", df.index < "2024"), ("2024-oggi", df.index >= "2024"), ("tutto", df.index == df.index)):
        zz = z[m]; rr = df.r[m]
        out.append(f"{n:>2} g {per:10s} n={len(zz):4d} dentro ±1σ {np.mean(zz<1)*100:4.0f}%  ±2σ {np.mean(zz<2)*100:4.0f}%  "
                   f"σ attesa mediana {df.s[m].median()*100:4.1f}%  |mov| reale mediano {rr.abs().median()*100:4.1f}%  rialzo {np.mean(rr>0)*100:3.0f}%")
open("calib.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out)); print(dv.index.min(), dv.index.max(), dv.iloc[-1])
