"""Zeiierman Trend Pressure — porting del Pine v6 (research/zeiierman/zeiierman_trend_pressure.pine), parametri di default.

Semantica Pine rispettata:
- ta.highest/ta.lowest/ta.sma: finestra di k barre INCLUSA la barra corrente, na finché non ci sono k valori.
- ta.ema: alpha 2/(k+1), seme = SMA delle prime k barre valide (come la doc Pine), poi ricorsiva.
- nz(), math.max/min con na -> na (clp(na) = na), confronti con na -> false.
- stato `var` (ud, dd, tz, est, ucn, lcn) calcolato barra per barra.
- syminfo.mintick = 0.01 (BTCUSDT).
Uso: from ztp import ztp; z = ztp(df)  # df con colonne open, high, low, close (indice datetime)
"""
import numpy as np
import pandas as pd

MINTICK = 0.01
DEFAULTS = dict(fl=21, pl=9, ps=7, sl=55, ml=120, ts=5, db=9.0, zn=20, sn=7, rm=16, gw=0.65)


def ema(x, k):
    """ta.ema con seme SMA: primo valore = media delle prime k barre valide consecutive."""
    v = np.asarray(x, float); out = np.full(len(v), np.nan); a = 2.0 / (k + 1); prev = np.nan; run = 0
    for i, xi in enumerate(v):
        if np.isnan(prev):
            run = run + 1 if not np.isnan(xi) else 0
            if run >= k:
                prev = v[i - k + 1:i + 1].mean(); out[i] = prev
        else:
            prev = a * xi + (1 - a) * prev if not np.isnan(xi) else np.nan  # nz(sum[1]) non serve: nessun na dopo il seme
            out[i] = prev
    return out


def hi(x, k): return pd.Series(x).rolling(k, min_periods=k).max().to_numpy()
def lo(x, k): return pd.Series(x).rolling(k, min_periods=k).min().to_numpy()
def clp(v, a, b): return np.minimum(b, np.maximum(a, v))  # na -> na


def rma(x, k):
    v = np.asarray(x, float); out = np.full(len(v), np.nan); prev = np.nan; run = 0
    for i, xi in enumerate(v):
        if np.isnan(prev):
            run = run + 1 if not np.isnan(xi) else 0
            if run >= k: prev = v[i - k + 1:i + 1].mean(); out[i] = prev
        else:
            prev = (prev * (k - 1) + xi) / k; out[i] = prev
    return out


def atr(df, k=14):
    h, l, c = df.high.to_numpy(float), df.low.to_numpy(float), df.close.to_numpy(float)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.where(np.isnan(pc), h - l, np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)]))
    return rma(tr, k)


def ztp(df, fl=21, pl=9, ps=7, sl=55, ml=120, ts=5, db=9.0, zn=20, sn=7, rm=16, gw=0.65):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(c)
    sw, mw, th, rl, gl, gm = 0.18, 0.72, 0.92, 21, 112, 3

    def sm(v, k): return ema(v, k) if k > 1 else v

    def wr(k):
        hh, ll = hi(h, k), lo(l, k)
        return 100.0 * (c - hh) / np.maximum(hh - ll, MINTICK)

    def eff(k):
        d1 = np.abs(c - np.r_[np.nan, c[:-1]])
        p = pd.Series(d1).rolling(k, min_periods=k).mean().to_numpy() * k
        ck = np.r_[np.full(k, np.nan), c[:-k]]
        nn = np.abs(c - ck)
        return clp(nn / np.maximum(p, MINTICK), 0.0, 1.0)  # na se p o n sono na

    def stk(x, k):
        a, b = hi(x, k), lo(x, k)
        return -100.0 + 100.0 * (x - b) / np.maximum(a - b, 1e-10)

    def prs(k):
        hh, ll = hi(h, k), lo(l, k)
        rg = np.maximum(hh - ll, MINTICK); cr = np.maximum(h - l, MINTICK)
        bh0, bl0 = np.maximum(o, c), np.minimum(o, c)
        uw, lw = h - bh0, bl0 - l
        cl = (c - ll) / rg; mn = ((h + l + c) / 3.0 - ll) / rg
        bd = ((c - o) / cr + 1.0) * 0.5; wk = ((lw - uw) / cr + 1.0) * 0.5
        c5 = np.r_[np.full(5, np.nan), c[:-5]]; p5 = np.where(np.isnan(c5), c, c5)
        im = ((c - p5) / rg + 1.0) * 0.5
        return clp((cl * 0.42 + mn * 0.23 + bd * 0.13 + wk * 0.12 + im * 0.10) * 100.0, 0.0, 100.0)

    # Z-Pulse
    rF, rS, rM = wr(fl), wr(sl), wr(ml)
    rp = stk(rF, pl)
    pr = clp(rF * 0.72 + rp * 0.28, -100.0, 0.0)
    pz = sm(pr, ps)

    # Z-Trend
    fw = max(0.0, 1.0 - sw - mw)
    ws0 = fw + sw + mw
    cn = clp((rF * fw + rS * sw + rM * mw) / max(ws0, 1e-10), -100.0, 0.0)
    dsum = np.abs(rF - rS) + np.abs(rS - rM) + np.abs(rF - rM)
    ag = 1.0 - clp(dsum / 300.0, 0.0, 1.0)
    ef = np.nan_to_num(eff(sl), nan=0.0)
    ud = np.zeros(n); ddv = np.zeros(n)
    pu = pd_ = 0.0
    for i in range(n):
        x = cn[i]
        pu = min(1.0, pu * 0.93 + 0.07) if (not np.isnan(x) and x > -30.0) else pu * 0.94
        pd_ = min(1.0, pd_ * 0.93 + 0.07) if (not np.isnan(x) and x < -70.0) else pd_ * 0.94
        ud[i], ddv[i] = pu, pd_
    tg0 = clp(cn + db * (ud - ddv), -100.0, 0.0)
    tg = sm(tg0, 2)
    ba = 2.0 / (ts + 1.0)
    tz = np.full(n, np.nan); prev = np.nan
    for i in range(n):
        if np.isnan(prev):
            cur = tg[i]
        else:
            mac = rM[i]
            side = 1 if mac > -50.0 else (-1 if mac < -50.0 else 0)
            pull = (side == 1 and tg[i] < prev) or (side == -1 and tg[i] > prev)
            lk = min(0.97, max(0.0, 0.15 + ag[i] * ef[i] * th))
            pa = max(0.015, ba * (1.0 - lk)) if pull else max(ba * 0.75, 0.03)
            cur = min(0.0, max(-100.0, prev + pa * (tg[i] - prev))) if not np.isnan(tg[i]) else np.nan
            # nota: in Pine clp(na)=na; dopo il warm-up tg non è mai na
        tz[i] = cur; prev = cur

    # Pressure Core
    cp = ema(prs(rl), rm)
    cg = ema(prs(gl), gm)
    c0 = cg * gw + cp * (1.0 - gw)
    cz = c0 - 100.0
    core = np.where((c0 > 50) & (cg > 50), 1, np.where((c0 < 50) & (cg < 50), -1, 0))

    # Exhaustion state
    d = float(sn - 5)
    ez = float(clp(float(zn) - d * 4.0, 8.0, 42.0)); rb = float(clp(8.0 + d * 1.75, 1.0, 18.0))
    cf = 1 if sn <= 5 else 2 if sn <= 7 else 3 if sn <= 9 else 4
    fast = sn <= 2
    up, dn = -ez, -100.0 + ez
    ur, lr = up - rb, dn + rb
    est = np.zeros(n, int); ucn = lcn = 0; e = 0
    for i in range(n):
        p_, t_ = pz[i], tz[i]
        uc = (p_ >= up) and (t_ >= up)          # confronti con nan -> False
        lc = (p_ <= dn) and (t_ <= dn)
        ucn = ucn + 1 if uc else 0
        lcn = lcn + 1 if lc else 0
        ux = ((p_ < ur) or (t_ < ur)) if fast else ((p_ < ur) and (t_ < ur))
        lx = ((p_ > lr) or (t_ > lr)) if fast else ((p_ > lr) and (t_ > lr))
        if e == 0:
            if ucn >= cf: e = 1
            elif lcn >= cf: e = -1
        elif e == 1 and ux: e = 0
        elif e == -1 and lx: e = 0
        est[i] = e
    ep = np.r_[0, est[:-1]]
    pzp, tzp = np.r_[np.nan, pz[:-1]], np.r_[np.nan, tz[:-1]]
    out = pd.DataFrame(dict(
        pz=pz, tz=tz, cz=cz, c0=c0, cg=cg, cp=cp, core=core, est=est,
        us=(est == 1) & (ep != 1), ls=(est == -1) & (ep != -1),
        ubk=(est == 0) & (ep == 1), lbk=(est == 0) & (ep == -1),
        xup=(pz > tz) & (pzp <= tzp), xdn=(pz < tz) & (pzp >= tzp),
        # flag letterali (definizione dell'utente): entrambe le linee nella fascia
        red=(pz >= -30) & (pz <= 0) & (tz >= -30) & (tz <= 0),
        blue=(pz >= -100) & (pz <= -70) & (tz >= -100) & (tz <= -70),
        # zona visiva degli screenshot: il gradiente segue la sola Z-Trend
        vred=tz >= -30, vblue=tz <= -70,
    ), index=df.index)
    out.attrs.update(up=up, dn=dn, ur=ur, lr=lr, cf=cf)
    return out


def load_daily(path="/home/user/radar/data/spot.csv"):
    d = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    return d[["open", "high", "low", "close"]].astype(float)


def load_4h(path="/home/user/radar/data/spot_1h.csv"):
    d = pd.read_csv(path, parse_dates=["t"]).set_index("t")
    return d.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


if __name__ == "__main__":
    df = load_daily(); z = ztp(df)
    pd.set_option("display.width", 200)
    print(z[["pz", "tz", "cz", "core", "est", "red", "blue"]].tail(15).round(1))
