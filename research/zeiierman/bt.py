"""Ciclo 1 · backtest delle regole R1v, R1u, R2, R2v, R3, R4 (vedi PREREG.md). Uso: python bt.py"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/home/user/radar/research/zeiierman")
from ztp import ztp, atr, load_daily, load_4h

D = "/home/user/radar/research/zeiierman/"
FEE, K_ATR, CAP = 0.0008, 2.5, 10_000.0
FUND = pd.read_csv("/home/user/radar/data/funding.csv", parse_dates=["date"]).set_index("date")["funding"].fillna(0)
PER = {"tot": ("2021-01-01", "2026-11-11"), "IS": ("2021-01-01", "2023-12-31"), "OOS": ("2024-01-01", "2026-11-11")}
PER4 = {"tot": ("2022-03-01", "2026-11-11"), "IS": ("2022-03-01", "2023-12-31"), "OOS": ("2024-01-01", "2026-11-11")}
RULES = ["R1v", "R1u", "R2", "R2v", "R3", "R4"]


def cross_dn(x, th):  # x scende a <= th
    p = np.r_[np.nan, x[:-1]]; return (x <= th) & ~(p <= th) & ~np.isnan(p)
def cross_up(x, th):  # x sale a >= th
    p = np.r_[np.nan, x[:-1]]; return (x >= th) & ~(p >= th) & ~np.isnan(p)
def onset(b):
    b = np.asarray(b, bool); return b & ~np.r_[False, b[:-1]]


def signals(z, rule, side):
    """Restituisce (entry, exit, timecap) come array booleani valutati alla chiusura."""
    tz, pz = z.tz.to_numpy(), z.pz.to_numpy(); n = len(tz); cap = None
    if rule == "R1v":
        b, r = cross_dn(tz, -70), cross_up(tz, -30)
        en, ex = (b, r) if side > 0 else (r, b)
    elif rule == "R1u":
        b, r = onset(z.blue), onset(z.red)
        en, ex = (b, r) if side > 0 else (r, b)
    elif rule == "R2":
        en, ex = (z.lbk.to_numpy(), z.ubk.to_numpy()) if side > 0 else (z.ubk.to_numpy(), z.lbk.to_numpy()); cap = 30
    elif rule == "R2v":
        b_rel = (tz > -70) & (np.r_[np.nan, tz[:-1]] <= -70)
        r_rel = (tz < -30) & (np.r_[np.nan, tz[:-1]] >= -30)
        en, ex = (b_rel, r_rel) if side > 0 else (r_rel, b_rel)
    elif rule in ("R3", "R4"):
        st = (tz > -50) & (z.core.to_numpy() == 1) if side > 0 else (tz < -50) & (z.core.to_numpy() == -1)
        if rule == "R3": en, ex = onset(st), ~st
        else:
            x = z.xup.to_numpy() if side > 0 else z.xdn.to_numpy()
            en, ex = st & x, ~st
    return np.asarray(en, bool), np.asarray(ex, bool), cap


def simulate(df, z, rule, side, stop=True, lev=1.0, start=None, end=None, fund_div=1.0, entries=None):
    """Una posizione per volta. entries: override (lista di (i_entry, i_exit)) per il placebo."""
    idx = df.index; o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    A = atr(df, 14)
    en, ex, cap = signals(z, rule, side)
    fu = FUND.reindex(idx.normalize()).fillna(0).to_numpy() / fund_div
    i0 = idx.searchsorted(pd.Timestamp(start)); i1 = idx.searchsorted(pd.Timestamp(end) + pd.Timedelta(days=1)) - 1
    eq = CAP; pos = 0; trades = []; curve = np.full(i1 - i0 + 1, np.nan); pend_in = pend_out = False
    for i in range(i0, i1 + 1):
        # azioni all'apertura
        if pos and pend_out:
            px = o[i]; eq += pos * notional * (px / ep - 1) - FEE * notional * px / ep
            trades.append((idx[ie], idx[i], ep, px, "segnale", eq)); pos = 0
        if not pos and pend_in:
            ep, ie, pos = o[i], i, side; notional = lev * eq; eq -= FEE * notional
            stp = ep - side * K_ATR * A[i - 1] if stop else None
        pend_in = pend_out = False
        mtm = eq
        if pos:
            # stop intrabarra
            if stop and ((side > 0 and l[i] <= stp) or (side < 0 and h[i] >= stp)):
                px = min(o[i], stp) if side > 0 else max(o[i], stp)
                eq += pos * notional * (px / ep - 1) - FEE * notional * px / ep
                trades.append((idx[ie], idx[i], ep, px, "stop", eq)); pos = 0; mtm = eq
            else:
                eq -= side * notional * (c[i] / ep) * fu[i]  # funding: long paga, short incassa
                mtm = eq + pos * notional * (c[i] / ep - 1)
        curve[i - i0] = mtm
        if i == i1: break
        if pos:
            if ex[i] or (cap and i - ie + 1 >= cap): pend_out = True
        elif en[i] and not (i == i1):
            pend_in = True
    if pos:  # chiusura a fine periodo al close
        px = c[i1]; eq += pos * notional * (px / ep - 1) - FEE * notional * px / ep
        trades.append((idx[ie], idx[i1], ep, px, "fine", eq))
    t = pd.DataFrame(trades, columns=["ingresso", "uscita", "px_in", "px_out", "motivo", "capitale"])
    if len(t):
        prev = np.r_[CAP, t.capitale.to_numpy()[:-1]]; t["pnl_%"] = (t.capitale / prev - 1) * 100
        t["mov_%"] = side * (t.px_out / t.px_in - 1) * 100
        t["barre"] = [idx.get_loc(b) - idx.get_loc(a) + 1 for a, b in zip(t.ingresso, t.uscita)]
    return t, pd.Series(curve, idx[i0:i1 + 1])


def metrics(t, curve, bars_per_year=365):
    fin = curve.iloc[-1]; ret = (fin / CAP - 1) * 100; yrs = len(curve) / bars_per_year
    dd = float((curve / curve.cummax() - 1).min() * 100)
    cagr = ((fin / CAP) ** (1 / yrs) - 1) * 100 if fin > 0 else -100
    if len(t):
        g = t["pnl_%"]; pf = g[g > 0].sum() / max(-g[g < 0].sum(), 1e-9); wr = (g > 0).mean() * 100
        expo = t.barre.sum() / len(curve) * 100
    else: pf = wr = expo = np.nan
    return dict(trade=len(t), win=round(wr, 0) if len(t) else np.nan, finale=round(fin), rend=round(ret, 1), cagr=round(cagr, 1),
                dd=round(dd, 1), mar=round(ret / abs(dd), 2) if dd < 0 else np.nan, mar_cagr=round(cagr / abs(dd), 2) if dd < 0 else np.nan,
                pf=round(pf, 2) if len(t) else np.nan, espo=round(expo, 0) if len(t) else 0)


def bh(df, start, end):
    s = df.loc[start:end]; c = s.close / s.open.iloc[0] * CAP
    return dict(finale=round(c.iloc[-1]), rend=round((c.iloc[-1] / CAP - 1) * 100, 1), dd=round(float((c / c.cummax() - 1).min() * 100), 1),
                mar=round((c.iloc[-1] / CAP - 1) * 100 / abs(float((c / c.cummax() - 1).min() * 100)), 2))


def placebo(df, t, side, start, end, n=1000, fund_div=1.0, seed=7):
    """Stesse durate di trade e di pause, ordine casuale; rendimento open->open con costi e funding, senza stop."""
    idx = df.index; o = df.open.to_numpy(float); c = df.close.to_numpy(float)
    fu = FUND.reindex(idx.normalize()).fillna(0).to_numpy() / fund_div
    i0 = idx.searchsorted(pd.Timestamp(start)); i1 = idx.searchsorted(pd.Timestamp(end) + pd.Timedelta(days=1)) - 1
    if len(t) == 0: return np.nan
    ins = [idx.get_loc(a) for a in t.ingresso]; outs = [idx.get_loc(b) for b in t.uscita]
    dur = [b - a for a, b in zip(ins, outs)]  # barre fra apertura d'ingresso e apertura d'uscita
    gaps = [ins[0] - i0] + [ins[k] - outs[k - 1] for k in range(1, len(ins))] + [i1 + 1 - outs[-1]]
    gaps = [max(g, 0) for g in gaps]
    def ret_of(a, b):
        b = min(b, i1); pe = o[a]; px = o[b] if b <= i1 and b != a else c[i1]
        f = side * fu[a:b].sum() if b > a else 0
        return (1 + side * (px / pe - 1)) * (1 - FEE) ** 2 - f
    def total(order_d, order_g):
        k = i0 + order_g[0]; m = 1.0
        for j, d in enumerate(order_d):
            a = k; b = a + max(d, 1)
            if a > i1: break
            m *= ret_of(a, b); k = b + order_g[j + 1]
        return m
    real = t.capitale.iloc[-1] / CAP
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(n):
        if total(list(rng.permutation(dur)), list(rng.permutation(gaps))) >= real: cnt += 1
    return round((1 + cnt) / (n + 1), 3)


def top3_removed(t):
    if len(t) == 0: return np.nan
    g = t["pnl_%"].sort_values(ascending=False).iloc[3:]
    return round(CAP * np.prod(1 + g / 100))


if __name__ == "__main__":
    out = []; df = load_daily(); z = ztp(df)
    for tf, data, per, bpy, fd in (("1D", df, PER, 365, 1.0), ("4h", load_4h(), PER4, 365 * 6, 6.0)):
        zz = z if tf == "1D" else ztp(data)
        for p, (s, e) in per.items():
            b = bh(data, s, e); out.append(dict(tf=tf, regola="B&H", lato="long", stop="-", lev=1, periodo=p, trade=1, finale=b["finale"],
                                                rend=b["rend"], dd=b["dd"], mar=b["mar"]))
        for r in RULES:
            for side in (1, -1):
                for stop in (True, False):
                    for lev in (1.0, 2.0):
                        for p, (s, e) in per.items():
                            t, cv = simulate(data, zz, r, side, stop, lev, s, e, fd)
                            m = metrics(t, cv, bpy)
                            row = dict(tf=tf, regola=r, lato="long" if side > 0 else "short", stop="2.5ATR" if stop else "no", lev=int(lev), periodo=p, **m)
                            if p == "tot" and lev == 1.0:
                                row["senza_top3"] = top3_removed(t)
                                row["placebo_p"] = placebo(data, t, side, s, e, 1000, fd)
                                t.assign(regola=r, lato=row["lato"], stop=row["stop"]).to_csv(
                                    f"{D}trades/{tf}_{r}_{row['lato']}_{row['stop']}.csv", index=False)
                            out.append(row)
                            print(row, flush=True)
    pd.DataFrame(out).to_csv(D + "risultati_ciclo1.csv", index=False)
