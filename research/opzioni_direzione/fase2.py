"""Opzioni e direzione · fase 2 · esecuzione del PREREG (commit 14cadc0). Uso: python3 fase2.py  (dentro research/opzioni_direzione/)

Prodotti: risultati.txt, test.csv (V1–V8 con Holm), vicini.csv, regole.csv, maxpain_osservazioni.csv, b0r_filtro.csv.
Deviazioni dichiarate in DEVIAZIONI.md.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

QUI = Path(__file__).resolve().parent
ROOT = QUI.parents[1]
OS = ROOT / "research" / "opzioni_studio"
D = QUI / "dati"
SEED = 20261127
N_PL = 10_000
IS_A, OOS_DA, LAST = "2023-12-31", "2024-01-01", "2026-11-21"
COST = 0.001
OUT: list[str] = []


def say(s=""):
    print(s, flush=True)
    OUT.append(str(s))


# ------------------------------------------------------------------ dati
def prezzi(cur):
    p = ROOT / "data" / ("spot.csv" if cur == "BTC" else "eth_spot.csv")
    x = pd.read_csv(p, index_col=0, parse_dates=True)
    fu = pd.read_csv(ROOT / "data" / ("funding.csv" if cur == "BTC" else "eth_funding.csv"), index_col=0, parse_dates=True)
    return x["close"], x["open"], fu["funding"].reindex(x.index).fillna(0.0)


def settimanale(cur):
    w = pd.read_csv(D / f"settimanale_{cur}.csv", index_col=0, parse_dates=True)
    c, _, _ = prezzi(cur)
    lc = np.log(c)
    lr = lc.diff()
    out = pd.DataFrame(index=w.index)
    for h in (7, 30):
        out[f"r{h}"] = (lc.shift(-h) - lc).reindex(w.index)
    for h in (7, 30):
        fut = pd.Series([lr.loc[d + pd.Timedelta(days=1): d + pd.Timedelta(days=h)] for d in w.index], index=w.index)
        out[f"rv{h}"] = [s.std() * math.sqrt(365) * 100 if len(s) == h else np.nan for s in fut]
    out["rv30p"] = [lr.loc[d - pd.Timedelta(days=29): d].std() * math.sqrt(365) * 100 for d in w.index]
    w = w.join(out)
    w["rr25n"] = w["rr25"] / w["iv_atm"]
    m, s = w["rr25"].rolling(52, min_periods=26).mean(), w["rr25"].rolling(52, min_periods=26).std()
    w["rr25z"] = (w["rr25"] - m) / s
    dv = pd.read_csv(D / f"dvol_{cur}_1D.csv")
    dv.index = pd.to_datetime(dv["t"].str[:10])
    dv = dv["close"]
    w["dvol_d14"] = np.log(w["dvol"] / dv.reindex(w.index - pd.Timedelta(days=14)).values)
    w["vrp"] = w["dvol"] / w["rv30p"]
    return w


# ------------------------------------------------------------------ statistica
def spearman(x, y):
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 10:
        return np.nan
    a, b = pd.Series(x[m]).rank().values, pd.Series(y[m]).rank().values
    return float(np.corrcoef(a, b)[0, 1])


def shift_p(x, y, sign, rng):
    """p a una coda nel verso `sign` con slittamento circolare dell'indicatore (k in [8, n-8])."""
    n = len(x)
    obs = sign * spearman(x, y)
    ks = rng.integers(8, n - 8 + 1, size=N_PL)
    cache = {}
    sims = np.empty(N_PL)
    for i, k in enumerate(ks):
        if k not in cache:
            cache[k] = sign * spearman(np.roll(x, k), y)
        sims[i] = cache[k]
    return (np.sum(sims >= obs) + 1) / (N_PL + 1), obs * sign


def holm(ps):
    ps = np.asarray(ps, float)
    o = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(run, 1.0)
    return adj


# ------------------------------------------------------------------ regole
def metr(eq: pd.Series, trades: list[float], cap=10_000.0):
    e = eq / eq.iloc[0] * cap if len(eq) else eq
    fin = float(e.iloc[-1])
    dd = float((e / e.cummax() - 1).min())
    ret = fin / cap - 1
    yrs = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
    cagr = (fin / cap) ** (1 / yrs) - 1
    t = np.array(trades)
    srt = np.sort(t)[::-1]
    return dict(finale=round(fin), rend=round(100 * ret, 1), dd=round(100 * dd, 1), n=len(t),
                wr=round(100 * float((t > 0).mean()), 0) if len(t) else np.nan,
                mar=round(ret / abs(dd), 2) if dd < 0 else np.nan, cagr_dd=round(cagr / abs(dd), 2) if dd < 0 else np.nan,
                senza1=round(fin / (1 + srt[0])) if len(t) >= 1 else np.nan,
                senza2=round(fin / np.prod(1 + srt[:2])) if len(t) >= 2 else np.nan)


def simula_pos(pos_w: pd.Series, close, fund, da, a):
    """pos_w: posizione decisa alla domenica D (indice) per i giorni D+1..D+7. Parte flat da 10.000 a `da`."""
    days = close.index[(close.index >= pd.Timestamp(da)) & (close.index <= pd.Timestamp(a))]
    pd_ = pos_w.reindex(pd.date_range(pos_w.index.min(), close.index.max())).ffill(limit=6).shift(1).fillna(0)
    pos = pd_.reindex(days).fillna(0).values
    r = (close / close.shift(1) - 1).reindex(days).values
    f = fund.reindex(days).fillna(0).values
    eq, cur, prev, trades, t_f = [], 1.0, 0.0, [], None
    base_day = days[0] - pd.Timedelta(days=1)
    for i in range(len(days)):
        p = pos[i]
        if p != prev:
            if prev != 0:
                cur *= 1 - COST
                t_f *= 1 - COST
                trades.append(t_f - 1)
                t_f = None
            if p != 0:
                cur *= 1 - COST
                t_f = 1 - COST
        g = 1 + p * r[i] + (f[i] if p < 0 else 0.0)
        cur *= g
        if p != 0:
            t_f *= g
        eq.append(cur)
        prev = p
    if t_f is not None:
        trades.append(t_f - 1)
    e = pd.Series([1.0] + eq, index=[base_day] + list(days)) * 10_000
    return e, trades


def pos_regola(x: pd.Series, sign, lo_q, hi_q, is_mask):
    z = sign * x
    lo, hi = z[is_mask].quantile(lo_q), z[is_mask].quantile(hi_q)
    p = pd.Series(0.0, index=x.index)
    p[z > hi] = 1.0
    p[z < lo] = -1.0
    return p


def per_periodi(fun):
    return {"IS": fun("2021-01-01", IS_A), "OOS": fun(OOS_DA, LAST), "dal 2021": fun("2021-01-01", LAST)}


def placebo_regola(pos_w, close, fund, rng):
    """Slittamento circolare delle posizioni settimanali dentro l'OOS; p sul MAR OOS."""
    po = pos_w[pos_w.index >= pd.Timestamp(OOS_DA) - pd.Timedelta(days=7)]
    po = po[po.index <= pd.Timestamp(LAST)]
    e, t = simula_pos(po, close, fund, OOS_DA, LAST)
    obs = metr(e, t)["mar"]
    n = len(po)
    ks = rng.integers(8, n - 8 + 1, size=N_PL)
    cache, sims = {}, np.empty(N_PL)
    for i, k in enumerate(ks):
        if k not in cache:
            ps = pd.Series(np.roll(po.values, k), index=po.index)
            e2, t2 = simula_pos(ps, close, fund, OOS_DA, LAST)
            m = metr(e2, t2)["mar"]
            cache[k] = -99 if m != m else m
        sims[i] = cache[k]
    return (np.sum(sims >= (obs if obs == obs else -99)) + 1) / (N_PL + 1)


# ------------------------------------------------------------------ riferimenti
def riferimenti():
    sys.path.insert(0, str(OS))
    sys.path.insert(0, str(ROOT))
    import op_segnali as S
    from radar import weekly as W
    f = S.frame()
    f = f[f.index <= LAST]
    out = {}
    for k, (da, a) in {"IS": ("2021-01-01", IS_A), "OOS": (OOS_DA, LAST), "dal 2021": ("2021-01-01", LAST)}.items():
        ff = f[f.index <= pd.Timestamp(a)]
        r = W.simulate(ff, start=da, capital=10_000.0, lev=1.0)
        tr = [t["pnl"] for t in r["trades"]]
        if r["open"]:
            tr.append(r["open"]["pnl_close"])
        e = r["equity"]
        e = pd.concat([pd.Series([10_000.0], [e.index[0] - pd.Timedelta(days=1)]), e])
        out[("W3.2", k)] = metr(e, tr)
        c = f["close"][(f.index >= pd.Timestamp(da)) & (f.index <= pd.Timestamp(a))]
        e = pd.concat([pd.Series([f["open"][c.index[0]]], [c.index[0] - pd.Timedelta(days=1)]), c])
        out[("Buy & hold", k)] = metr(e, [float(c.iloc[-1] / f["open"][c.index[0]] - 1)])
    return out


# ------------------------------------------------------------------ V7 massimo dolore
def v7_dati(col="mp7_28g", lag=7):
    m = pd.read_csv(D / "maxpain.csv", parse_dates=["scadenza"])
    h8 = pd.read_csv(OS / "cache" / "btc_0800.csv", index_col=0, parse_dates=True)["open_0800"]
    m["S"] = (m["scadenza"] - pd.Timedelta(days=lag)).map(h8)
    m["ST"] = m["scadenza"].map(h8)
    m["MP"] = m[col.replace("7", str(lag), 1)] if lag != 7 else m[col]
    L = m["S"] ** 2 / m["MP"]
    m["diff"] = np.abs(np.log(m["ST"] / L)) - np.abs(np.log(m["ST"] / m["MP"]))
    m["verso"] = (np.sign(np.log(m["ST"] / m["S"])) == np.sign(np.log(m["MP"] / m["S"]))).astype(float)
    m.loc[m["MP"] == m["S"], "verso"] = np.nan
    m["dist_pct"] = 100 * np.log(m["MP"] / m["S"])
    return m


def segni_p(d, rng):
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    obs = d.mean()
    sims = (rng.choice([-1, 1], size=(N_PL, len(d))) * d).mean(axis=1)
    return (np.sum(sims >= obs) + 1) / (N_PL + 1)


def placebo_strike(m, rng, lag=7):
    v = pd.read_csv(D / "vol_strike_campione.csv.gz")
    cand = []
    for _, r in m.iterrows():
        fino = (r["scadenza"] - pd.Timedelta(days=lag + 1))
        x = v[(v["scad"] == r["scadenza"].date().isoformat()) & (v["data"] <= fino.date().isoformat())
              & (v["data"] > (fino - pd.Timedelta(days=28)).date().isoformat())]
        ks = np.unique(x["K"].values)
        ks = ks[np.abs(np.log(ks / r["S"])) <= 0.15]
        cand.append(ks)
    obs = m["diff"].mean()
    sims = np.empty(N_PL)
    S, ST = m["S"].values, m["ST"].values
    for i in range(N_PL):
        K = np.array([rng.choice(c) for c in cand])
        L = S ** 2 / K
        sims[i] = np.mean(np.abs(np.log(ST / L)) - np.abs(np.log(ST / K)))
    return (np.sum(sims >= obs) + 1) / (N_PL + 1)


def v7_regola(m, fund, da, a):
    h = pd.read_csv(OS / "cache" / "btc_1h.csv", index_col=0, parse_dates=True)["open"]
    x = m[(m["scadenza"] - pd.Timedelta(days=7) >= pd.Timestamp(da)) & (m["scadenza"] <= pd.Timestamp(a) + pd.Timedelta(days=1))]
    punti, cap, trades = [(pd.Timestamp(da), 1.0)], 1.0, []
    for _, r in x.iterrows():
        p = 1.0 if r["MP"] > r["S"] else (-1.0 if r["MP"] < r["S"] else 0.0)
        if p == 0:
            continue
        t0, t1 = r["scadenza"] - pd.Timedelta(days=7) + pd.Timedelta(hours=8), r["scadenza"] + pd.Timedelta(hours=8)
        c0 = cap * (1 - COST)
        fu = 0.0
        for g in pd.date_range(t0.normalize() + pd.Timedelta(days=1), t1.normalize()):
            if g in h.index:
                fu += fund.get(g - pd.Timedelta(days=1), 0.0) if p < 0 else 0.0
                punti.append((g, c0 * (1 + p * (h[g] / r["S"] - 1) + fu)))
        fu += fund.get(t1.normalize(), 0.0) / 3 if p < 0 else 0.0
        fin = c0 * (1 + p * (r["ST"] / r["S"] - 1) + fu) * (1 - COST)
        trades.append(fin / cap - 1)
        cap = fin
        punti.append((t1, cap))
    e = pd.Series([v for _, v in punti], index=[t for t, _ in punti]) * 10_000
    e = e.groupby(level=0).last().sort_index()
    return e, trades


# ------------------------------------------------------------------ V8 B0r con filtro sul costo
def v8(w, thr_q_list=(0.75, 0.66, 0.90)):
    sys.path.insert(0, str(OS))
    import op_engine as E
    from op_prezzatore import PrezzatoreSuperficie
    PZ = PrezzatoreSuperficie()
    DAYS = pd.date_range("2018-01-01", LAST)
    tr = pd.read_csv(OS / "cache" / "op_w32_trades.csv")
    conf = E.Conf(finestra=(20, 50))
    isv = w.loc[(w.index <= IS_A), "vrp"].dropna()
    per = {"IS": ("2021-01-01", IS_A), "OOS": (OOS_DA, None), "dal 2021": ("2021-01-01", None)}
    res = {}

    def corri(t):
        piano = E.piano_w32(t, DAYS)
        return {k: E.Motore(PZ, conf).simula(piano, DAYS, da, a) for k, (da, a) in per.items()}

    res["B0r"] = corri(tr)
    vrp_sig = pd.to_datetime(tr["signal"]).map(w["vrp"])
    info = pd.DataFrame({"segnale": tr["signal"], "lato": tr["side"], "vrp": vrp_sig.round(3)})
    for q in thr_q_list:
        thr = float(isv.quantile(q))
        salta = (vrp_sig > thr).fillna(False)
        info[f"salta_q{int(q*100)}"] = salta
        res[f"filtro q{int(q*100)} (VRP > {thr:.2f})"] = corri(tr[~salta.values])
    return res, info, E


# ------------------------------------------------------------------ main
def main():
    rng = np.random.default_rng(SEED)
    W = {c: settimanale(c) for c in ("BTC", "ETH")}
    PX = {c: prezzi(c) for c in ("BTC", "ETH")}
    V = [("V1", "rr25", "r7"), ("V2", "rr25", "r30"), ("V3", "pc_vol", "r7"), ("V4", "pc_vol", "r30"),
         ("V5", "dvol_d7", "r30"), ("V6", "dvol", "rv30")]
    VIC = {"V1": [("rr25s", "r7"), ("rr25n", "r7"), ("rr25z", "r7")],
           "V2": [("rr25s", "r30"), ("rr25n", "r30"), ("rr25z", "r30")],
           "V3": [("pc_buy", "r7"), ("pc_camp7", "r7")], "V4": [("pc_buy", "r30"), ("pc_camp7", "r30")],
           "V5": [("dvol_d14", "r30"), ("dvol_d7", "r7")], "V6": [("dvol", "rv7")]}
    righe, vic_r = [], []
    w = W["BTC"]
    isb, oob = w.index <= IS_A, (w.index >= OOS_DA) & (w.index <= LAST)
    say("# Opzioni e direzione · fase 2 (PREREG 14cadc0)\n")
    say("## V1–V6: Spearman indicatore → misura futura (domeniche); p OOS a una coda nel verso IS, slittamento circolare")
    for v, x, y in V:
        r_is = spearman(w.loc[isb, x].values, w.loc[isb, y].values)
        s = 1.0 if r_is >= 0 else -1.0
        p_oos, r_oos = shift_p(w.loc[oob, x].values, w.loc[oob, y].values, s, rng)
        p_is2, _ = shift_p(w.loc[isb, x].values, w.loc[isb, y].values, s, rng)
        n_is = int((w.loc[isb, [x, y]].notna().all(axis=1)).sum())
        n_oos = int((w.loc[oob, [x, y]].notna().all(axis=1)).sum())
        we = W["ETH"]
        ie, oe = we.index <= IS_A, (we.index >= OOS_DA) & (we.index <= LAST)
        pe, re_ = shift_p(we.loc[oe, x].values, we.loc[oe, y].values, s, rng)
        re_is = spearman(we.loc[ie, x].values, we.loc[ie, y].values)
        vic_ok = []
        for xx, yy in VIC[v]:
            rv = spearman(w.loc[oob, xx].values, w.loc[oob, yy].values)
            rvi = spearman(w.loc[isb, xx].values, w.loc[isb, yy].values)
            vic_ok.append(np.sign(rv) == s)
            vic_r.append(dict(V=v, vicino=f"{xx} → {yy}", rho_IS=round(rvi, 3), rho_OOS=round(rv, 3), stesso_segno=bool(np.sign(rv) == s)))
        righe.append(dict(V=v, misura=f"{x} → {y}", n_IS=n_is, n_OOS=n_oos, rho_IS=round(r_is, 3), p_IS=round(p_is2, 4),
                          rho_OOS=round(r_oos, 3), p_OOS=round(p_oos, 4), ETH_rho_IS=round(re_is, 3), ETH_rho_OOS=round(re_, 3),
                          ETH_p=round(pe, 4), vicini_ok=f"{sum(vic_ok)}/{len(vic_ok)}", segno=int(s)))

    # V7
    m = v7_dati()
    m_is, m_oos = m[m["scadenza"] <= IS_A], m[m["scadenza"] >= OOS_DA]
    p7 = segni_p(m_oos["diff"], rng)
    p7_is = segni_p(m_is["diff"], rng)
    p7_str = placebo_strike(m_oos, rng)
    p7_str_all = placebo_strike(m, rng)
    vic7 = []
    for nome, mm in (("E−3 (28 g)", v7_dati("mp7_28g", 3)), ("E−7 cumulato", v7_dati("mp7_cum", 7))):
        mo = mm[mm["scadenza"] >= OOS_DA]
        vic7.append(mo["diff"].mean() > 0)
        vic_r.append(dict(V="V7", vicino=nome, rho_IS=round(mm.loc[mm["scadenza"] <= IS_A, "diff"].mean() * 100, 2),
                          rho_OOS=round(mo["diff"].mean() * 100, 2), stesso_segno=bool(mo["diff"].mean() > 0),
                          verso_OOS=round(100 * mo["verso"].mean(), 0)))
    righe.append(dict(V="V7", misura="convergenza a MP7 − specchio (punti %)", n_IS=len(m_is), n_OOS=len(m_oos),
                      rho_IS=round(100 * m_is["diff"].mean(), 2), p_IS=round(p7_is, 4), rho_OOS=round(100 * m_oos["diff"].mean(), 2),
                      p_OOS=round(p7, 4), ETH_rho_IS=np.nan, ETH_rho_OOS=np.nan, ETH_p=np.nan,
                      vicini_ok=f"{sum(vic7)}/{len(vic7)}", segno=1,
                      verso_IS=round(100 * m_is["verso"].mean(), 0), verso_OOS=round(100 * m_oos["verso"].mean(), 0),
                      p_strike_caso_OOS=round(p7_str, 4), p_strike_caso_tutto=round(p7_str_all, 4)))
    m.to_csv(QUI / "maxpain_osservazioni.csv", index=False)

    # V8
    res8, info8, E = v8(w)
    b = res8["B0r"]["OOS"]
    nome75 = [k for k in res8 if k.startswith("filtro q75")][0]
    f75 = res8[nome75]["OOS"]
    ta = {t["entry"]: math.log1p(t["ret"]) for t in b["trades"] if t.get("motivo") != "aperta"}
    tf = {t["entry"]: math.log1p(t["ret"]) for t in f75["trades"] if t.get("motivo") != "aperta"}
    dl = np.array([tf.get(k, 0.0) - ta[k] for k in sorted(ta)])
    if len(dl) and np.any(dl != 0):
        sims = (rng.choice([-1, 1], size=(N_PL, len(dl))) * dl).sum(axis=1)
        p8 = (np.sum(sims >= dl.sum()) + 1) / (N_PL + 1)
    else:
        p8 = 1.0
    righe.append(dict(V="V8", misura="B0r saltando VRP > q75 IS", n_IS=E.metriche(res8[nome75]["IS"]).get("n"),
                      n_OOS=E.metriche(f75).get("n"), p_OOS=round(p8, 4), segno=1,
                      vicini_ok="—", rho_IS=np.nan, rho_OOS=np.nan))
    T = pd.DataFrame(righe)
    T["p_Holm"] = holm(T["p_OOS"].values).round(4)
    T.to_csv(QUI / "test.csv", index=False)
    pd.DataFrame(vic_r).to_csv(QUI / "vicini.csv", index=False)
    say(T.to_string(index=False))
    say("\n## Vicini")
    say(pd.DataFrame(vic_r).to_string(index=False))

    # ---------------- regole
    say("\n## Regole operative (10.000 $, 1x, costi 0,10%/lato, funding sugli short)")
    ref = riferimenti()
    reg = []
    for (nome, per), mt in ref.items():
        reg.append(dict(regola=nome, asset="BTC", periodo=per, **mt))
    is_m = pd.Series(w.index <= IS_A, index=w.index)
    rngp = np.random.default_rng(SEED)
    for v, x, y in V[:5]:
        s = int(T.loc[T["V"] == v, "segno"].iloc[0])
        for cur in ("BTC", "ETH"):
            ww = W[cur]
            close, _, fund = PX[cur]
            ism = pd.Series(ww.index <= IS_A, index=ww.index)
            for qn, (lo, hi) in (("terzili", (1 / 3, 2 / 3)), ("quartili", (0.25, 0.75)), ("quintili", (0.2, 0.8))):
                pw = pos_regola(ww[x], s, lo, hi, ism)
                mets = per_periodi(lambda da, a: metr(*simula_pos(pw, close, fund, da, a)))
                pl = placebo_regola(pw, close, fund, rngp) if (qn == "terzili" and cur == "BTC") else np.nan
                for per, mt in mets.items():
                    reg.append(dict(regola=f"{v} {x} {qn}", asset=cur, periodo=per, **mt,
                                    placebo_p=pl if per == "OOS" else np.nan,
                                    tempo_long=round(float((pw[(ww.index >= (OOS_DA if per == 'OOS' else '2021-01-01'))] > 0).mean()), 2),
                                    tempo_short=round(float((pw[(ww.index >= (OOS_DA if per == 'OOS' else '2021-01-01'))] < 0).mean()), 2)))
    # V7 regola
    close, _, fund = PX["BTC"]
    for per, (da, a) in {"IS": ("2021-01-01", IS_A), "OOS": (OOS_DA, LAST), "dal 2021": ("2021-01-01", LAST)}.items():
        e, t = v7_regola(m, fund, da, a)
        reg.append(dict(regola="V7 verso il massimo dolore", asset="BTC", periodo=per, **metr(e, t)))
    # placebo V7: slittamento circolare dei segni fra le scadenze OOS
    mo = m[m["scadenza"] >= OOS_DA].reset_index(drop=True)
    e, t = v7_regola(mo, fund, OOS_DA, LAST)
    obs = metr(e, t)["mar"]
    n = len(mo)
    sg = np.sign(mo["MP"] - mo["S"]).values
    sims = rngp.integers(8, n - 8 + 1, size=N_PL)
    cache = {}
    vals = []
    for k in sims:
        if k not in cache:
            mm = mo.copy()
            mm["MP"] = mm["S"] * np.exp(0.01 * np.roll(sg, k))
            e2, t2 = v7_regola(mm, fund, OOS_DA, LAST)
            mt = metr(e2, t2)["mar"]
            cache[k] = -99 if mt != mt else mt
        vals.append(cache[k])
    p7r = (np.sum(np.array(vals) >= (obs if obs == obs else -99)) + 1) / (N_PL + 1)
    reg[-2]["placebo_p"] = p7r
    # V8 metriche
    for k, rr in res8.items():
        for per in ("IS", "OOS", "dal 2021"):
            mt = E.metriche(rr[per])
            reg.append(dict(regola=f"V8 {k}", asset="BTC", periodo=per, finale=mt.get("finale"), dd=round(100 * mt["dd"], 1),
                            n=mt.get("n"), wr=round(100 * (mt.get("quota_guadagno") or 0), 0), senza2=mt.get("senza_2_migliori"),
                            rend=round(100 * (mt["finale"] / 10_000 - 1), 1),
                            mar=round((mt["finale"] / 10_000 - 1) / abs(mt["dd"]), 2) if mt["dd"] < 0 else np.nan))
    R = pd.DataFrame(reg)
    R.to_csv(QUI / "regole.csv", index=False)
    info8.to_csv(QUI / "b0r_filtro.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_rows", 500, "display.max_columns", 30):
        say(R.to_string(index=False))
        say("\n## V8 · segnali e VRP")
        say(info8.to_string(index=False))

    # ---------------- descrittivi
    say("\n## Descrittivi")
    for cur in ("BTC", "ETH"):
        ww = W[cur]
        rt = (ww["dvol"] / ww["rv30"]).dropna()
        say(f"{cur}: DVOL / volatilità realizzata nei 30 g successivi: mediana {rt.median():.2f}, > 1 nel {100 * (rt > 1).mean():.0f}% "
            f"(IS {rt[rt.index <= IS_A].median():.2f}, OOS {rt[rt.index >= OOS_DA].median():.2f})")
    say(f"V7: |distanza MP7 − S7| mediana {m['dist_pct'].abs().median():.1f}%; MP7 sopra S7 in {100 * (m['MP'] > m['S']).mean():.0f}% delle scadenze")
    # scadenza di oggi (solo descrittiva)
    try:
        snap = json.load(open(ROOT / "research/opzioni_scadenze/dati/snap_20261127_0738.json"))
        s0 = [x for x in snap["scadenze"] if x["data"] == "2026-11-27"][0]
        r = requests.get("https://www.deribit.com/api/v2/public/get_delivery_prices",
                         params=dict(index_name="btc_usd", count=3), headers={"User-Agent": "research-client"}, timeout=30).json()
        dp = r["result"]["data"]
        say(f"Scadenza 27/11/2026 (descrittiva, fuori dal test): massimo dolore da OI vero alle 07:38 {s0['max_pain']:,.0f} $, indice "
            f"{snap['indice']:,.0f} $; regolamento Deribit {dp[0]}")
        mx = [x for x in snap['scadenze']][:3]
        v = pd.read_csv(D / "vol_strike_campione.csv.gz")
        sys.path.insert(0, str(QUI))
        import costruisci as C
        x = C.proxy(v, "2026-11-27", "2026-11-19", 28)
        h8 = pd.read_csv(OS / "cache" / "btc_0800.csv", index_col=0, parse_dates=True)["open_0800"]
        say(f"  proxy MP7 (28 g fino al 19/11) {C.max_pain(x):,.0f} $; S7 (20/11 08:00) {h8.get(pd.Timestamp('2026-11-20')):,.0f} $")
    except Exception as e:  # descrittivo: non blocca
        say(f"Scadenza 27/11: descrittivo non disponibile ({e})")
    (QUI / "risultati.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
