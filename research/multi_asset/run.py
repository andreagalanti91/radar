"""Multi-asset · fase 2: esegue il PREREG (commit 13b0e82) senza modifiche alle regole.
Uscite: risultati.txt, principali.csv, periodi.csv, robustezza.csv, placebo.csv, decenni.csv, dow.csv, btc.csv, panic.csv."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ma_lib as M  # noqa: E402
import p2_engine as E  # noqa: E402
from radar import weekly as W  # noqa: E402

OUT = M.HERE
CAP = 10000.0
NCONF = 415
ALPHA = 0.05 / NCONF
N_PLAC, N_FIRST, P_STOP = 20000, 2000, 0.01
BTC_FEE = W.FEE_SPOT + W.SLIP          # S2/S3 su BTC in spot: 0,1% + slippage 0,1% per lato
RNG = np.random.default_rng(20261122)
LINES: list[str] = []


def log(s=""):
    print(s, flush=True)
    LINES.append(s)


# ---------------------------------------------------------------- metriche
def mets(eq: pd.Series, pnls=None, inpos=None, stops=None) -> dict:
    eq = eq.dropna()
    e = eq / eq.iloc[0]
    yrs = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    dd = float((e / e.cummax() - 1).min())
    pn = np.array(pnls if pnls is not None else [], float)
    return dict(final=round(CAP * float(e.iloc[-1]), 0), ret=round(float(e.iloc[-1] - 1) * 100, 1), cagr=round(cagr * 100, 2),
                dd=round(dd * 100, 1), mar=(cagr / abs(dd)) if dd < 0 else np.inf, n=len(pn),
                wr=round(float((pn > 0).mean() * 100), 1) if len(pn) else None,
                inpos=round(float(inpos) * 100, 1) if inpos is not None else None,
                stop_avg=round(float(np.mean(stops)) * 100, 1) if stops else None, years=round(yrs, 1))


def bh(close: pd.Series, a, b, fee) -> pd.Series:
    c = close[(close.index >= pd.Timestamp(a)) & (close.index <= pd.Timestamp(b))].dropna()
    return c / c.iloc[0] * (1 - fee)


# ---------------------------------------------------------------- S2/S3: equity e rappresentazione
def ema_run(f: pd.DataFrame, vol, a, b, fee, mode="close", **kw):
    """Equity giornaliera dell'indicatore (alla chiusura o all'apertura del giorno dopo), trade, segmenti per il placebo."""
    fw = f[(f.index >= pd.Timestamp(a)) & (f.index <= pd.Timestamp(b))]
    tr = M.ema_vix(f["close"], vol, a, b, use_vix=vol is not None, **kw)
    idx, C, O = fw.index, fw["close"].to_numpy(float), fw["open"].to_numpy(float)
    N = len(idx)
    g, held = np.ones(N), np.zeros(N, bool)
    pn, seg = [], []
    for t in tr:
        e = idx.get_loc(t["entry"])
        op = t["exit"] is None
        x = N - 1 if op else idx.get_loc(t["exit"])
        if mode == "close":
            g[e] *= 1 - fee
            g[e + 1:x + 1] *= C[e + 1:x + 1] / C[e:x]
            if not op:
                g[x] *= 1 - fee
            held[e + 1:x + 1] = True
            pn.append(C[x] / C[e] * (1 - fee) ** (1 if op else 2) - 1)
            if x > e:
                seg.append((e + 1, x, 1.0))
        else:
            if e + 1 >= N:
                continue
            g[e + 1] *= (1 - fee) * C[e + 1] / O[e + 1]
            if op or x + 1 >= N:
                g[e + 2:] *= C[e + 2:] / C[e + 1:-1]
                held[e + 1:] = True
                pn.append(C[-1] / O[e + 1] * (1 - fee) - 1)
            else:
                g[e + 2:x + 1] *= C[e + 2:x + 1] / C[e + 1:x]
                g[x + 1] *= O[x + 1] / C[x] * (1 - fee)
                held[e + 1:x + 2] = True
                pn.append(O[x + 1] / O[e + 1] * (1 - fee) ** 2 - 1)
    eq = pd.Series(np.cumprod(g), idx)
    return dict(eq=eq, pnl=pn, inpos=held.mean(), seg=seg, idx=idx, trades=tr)


def s1_run(f, a, b, long_only, k=2.5, fee=M.FEE, wb=None, btc=False, short_cost=M.SHORT_COST):
    r = M.s1_btc(f, a, b, long_only=long_only, k=k) if btc else M.s1_sim(f, a, b, long_only=long_only, k=k, fee=fee, wb=wb,
                                                                          short_cost=short_cost)
    eq = r["equity"].dropna()
    idx = eq.index
    trs = r["trades"] + ([r["open"]] if r["open"] else [])
    pn = [t["pnl"] if t is not r["open"] else t.get("pnl_close", t["pnl"]) for t in trs]
    seg = []
    for t in trs:
        ia = idx.get_loc(pd.Timestamp(t["entry"]))
        if t.get("exit") is None:
            ib = len(idx) - 1
        else:
            ib = idx.get_loc(pd.Timestamp(t["exit"]))
            if t["reason"] in ("ema", "dist"):
                ib -= 1                               # uscita all'apertura: l'ultimo rendimento è quello del giorno prima
        sg = 1 if t["side"] == "long" else -1
        if ib >= ia:
            seg.append((ia, ib, sg * float(t["expo"])))
    stops = [t["pnl"] for t in r["trades"] if t["reason"] == "stop"]
    return dict(eq=eq, pnl=pn, inpos=float((r["expo"].reindex(idx).fillna(0) > 0).mean()), seg=seg, idx=idx, stops=stops)


# ---------------------------------------------------------------- placebo (rappresentazione a segmenti, chiusura→chiusura)
def seg_stat(r, starts, durs, vals, fee, sday, yrs):
    """CAGR/DD di P strategie (righe): segmenti [start, start+dur) con esposizione vals; costi per lato e costo short giornaliero."""
    P, n = starts.shape
    N = len(r)
    pos = np.zeros((P, N + 1))
    cst = np.zeros((P, N + 1))
    rows = np.arange(P)
    for j in range(n):
        s, d, v = starts[:, j], durs[:, j], vals[:, j]
        np.add.at(pos, (rows, s), v)
        np.add.at(pos, (rows, s + d), -v)
        np.add.at(cst, (rows, s), np.log1p(-fee * np.abs(v)))
        np.add.at(cst, (rows, s + d - 1), np.log1p(-fee * np.abs(v)))
    pos = np.cumsum(pos, axis=1)[:, :N]
    lr = np.log1p(pos * r[None, :]) + cst[:, :N] + np.where(pos < 0, np.log1p(pos * sday), 0.0)
    cs = np.cumsum(lr, axis=1)
    dd = np.exp(np.min(cs - np.maximum.accumulate(np.maximum(cs, 0.0), axis=1), axis=1)) - 1
    dd = np.minimum(dd, np.exp(np.minimum(cs.min(axis=1), 0)) - 1)
    cagr = np.exp(cs[:, -1] / yrs) - 1
    return np.where(dd < 0, cagr / np.abs(np.where(dd < 0, dd, -1)), np.inf)


def placebo(close: pd.Series, run: dict, fee, sday) -> tuple[float, float, int]:
    idx = run["idx"]
    c = close.reindex(idx).to_numpy(float)
    r = np.r_[0.0, c[1:] / c[:-1] - 1]
    seg = run["seg"]
    if len(seg) < 2:
        return np.nan, np.nan, 0
    N = len(r)
    yrs = (idx[-1] - idx[0]).days / 365.25
    a = np.array([s[0] for s in seg]); d = np.array([s[1] - s[0] + 1 for s in seg]); v = np.array([s[2] for s in seg])
    real = float(seg_stat(r, a[None], d[None], v[None], fee, sday, yrs)[0])
    G = N - d.sum()
    n = len(seg)
    hits, done = 0, 0
    while done < N_PLAC:
        P = min(max(int(4e6 // N), 20), N_PLAC - done)
        perm = np.argsort(RNG.random((P, n)), axis=1)
        dp, vp = d[perm], v[perm]
        u = np.sort(RNG.integers(0, G + 1, (P, n)), axis=1)
        st = u + np.cumsum(dp, axis=1) - dp
        hits += int((seg_stat(r, st, dp, vp, fee, sday, yrs) >= real).sum())
        done += P
        if done >= N_FIRST and (1 + hits) / (1 + done) > P_STOP:
            break
    return real, (1 + hits) / (1 + done), done


def drop_best(close, run, fee, sday):
    """CAGR/DD senza il trade migliore (nella rappresentazione a segmenti: il suo periodo diventa flat)."""
    seg = run["seg"]
    if len(seg) < 2:
        return np.nan
    idx = run["idx"]
    c = close.reindex(idx).to_numpy(float)
    r = np.r_[0.0, c[1:] / c[:-1] - 1]
    gains = [np.prod(1 + s[2] * r[s[0]:s[1] + 1]) for s in seg]
    keep = [s for j, s in enumerate(seg) if j != int(np.argmax(gains))]
    yrs = (idx[-1] - idx[0]).days / 365.25
    a = np.array([s[0] for s in keep])[None]; d = np.array([s[1] - s[0] + 1 for s in keep])[None]; v = np.array([s[2] for s in keep])[None]
    return float(seg_stat(r, a, d, v, fee, sday, yrs)[0])


# ---------------------------------------------------------------- per asset
RULES = ("S1 L/S", "S1 long", "S2", "S3")


def runner(name, f, vix, wb, rule, a, b, btc=False, fee=None, mode="close", **kw):
    fee_e = (BTC_FEE if btc else M.FEE) if fee is None else fee
    if rule == "S1 L/S":
        return s1_run(f, a, b, False, wb=wb, btc=btc, fee=fee_e, **kw)
    if rule == "S1 long":
        return s1_run(f, a, b, True, wb=wb, btc=btc, fee=fee_e, **kw)
    if rule == "S2":
        return ema_run(f, None, a, b, fee_e, mode, **kw)
    return ema_run(f, vix, a, b, fee_e, mode, **kw)


def mrow(run):
    return mets(run["eq"], run["pnl"], run["inpos"], run.get("stops"))


def fmt_mar(x):
    return "inf" if not np.isfinite(x) else f"{x:.2f}"


def eval_asset(name, f, vix, periods, end, btc=False, vol_lab="VIX", thr=34.0, nb_thr=(30.0, 38.0), do_plac=True,
               dow=False, rules=RULES):
    wb = None if btc else M.s1_weekly(f)
    fee_bh = BTC_FEE if btc else M.FEE
    out_main, out_per, out_rob, out_pl = [], [], [], []
    for rule in rules:
        need_vix = rule == "S3"
        st = pd.Timestamp("2021-01-01") if btc else M.test_start(f, need_vix)
        kw = dict(thr=thr) if rule == "S3" else {}
        run = runner(name, f, vix, wb, rule, st, end, btc=btc, **kw)
        m = mrow(run)
        mb = mets(bh(f["close"], st, end, fee_bh))
        rec = dict(asset=name, rule=rule + (f" {vol_lab}" if rule == "S3" and btc else ""), start=str(st.date()), **m,
                   bh_final=mb["final"], bh_cagr=mb["cagr"], bh_dd=mb["dd"], bh_mar=mb["mar"])
        # dal 2021
        if not btc:
            s21 = max(pd.Timestamp("2021-01-01"), st)
            r21 = runner(name, f, vix, wb, rule, s21, end, **kw)
            m21, b21 = mrow(r21), mets(bh(f["close"], s21, end, fee_bh))
            rec.update(final21=m21["final"], cagr21=m21["cagr"], dd21=m21["dd"], mar21=m21["mar"], n21=m21["n"],
                       bh_final21=b21["final"], bh_cagr21=b21["cagr"], bh_dd21=b21["dd"], bh_mar21=b21["mar"])
        # sottoperiodi
        wins, avail = 0, 0
        for p, (pa, pb) in periods.items():
            pa = max(pd.Timestamp(pa), st)
            if (pd.Timestamp(pb) - pa).days < 3 * 365 and not btc:
                continue
            rp = runner(name, f, vix, wb, rule, pa, pb, btc=btc, **kw)
            mp, bp = mrow(rp), mets(bh(f["close"], pa, pb, fee_bh))
            avail += 1
            win = mp["mar"] > bp["mar"]
            wins += win
            out_per.append(dict(asset=name, rule=rec["rule"], period=p, start=str(pa.date()), end=str(pb)[:10], final=mp["final"],
                                cagr=mp["cagr"], dd=mp["dd"], mar=mp["mar"], n=mp["n"], bh_final=bp["final"], bh_cagr=bp["cagr"],
                                bh_dd=bp["dd"], bh_mar=bp["mar"], win=win))
        rec.update(per_wins=wins, per_avail=avail, per_ok=(avail >= 2 and wins >= (2 if avail >= 2 else 99)))
        if dow:
            out_main.append(rec)
            continue
        # placebo
        sday = (M.SHORT_COST / 252) if not btc else 0.0
        if do_plac:
            t0 = time.time()
            real, p, nd = placebo(f["close"], run, BTC_FEE if btc else M.FEE, sday)
            out_pl.append(dict(asset=name, rule=rec["rule"], stat_seg=real, p=p, draws=nd, secs=round(time.time() - t0, 1)))
            rec.update(plac_p=p, plac_draws=nd)
        rec["funziona"] = bool(rec["per_ok"] and rec.get("plac_p", 1) < ALPHA and m["n"] >= 10)
        # robustezza (sul periodo intero, contro il buy & hold)
        rob = []
        if rule.startswith("S1"):
            for k in (2.0, 3.0):
                rr = s1_run(f, st, end, rule == "S1 long", k=k, wb=wb, btc=btc)
                rob.append(("vicino k=%.1f" % k, mrow(rr)["mar"]))
        else:
            nbs = [("EMA 150", dict(ema=150)), ("EMA 250", dict(ema=250))]
            if rule == "S3":
                nbs += [(f"{vol_lab} {nb_thr[0]}", dict(thr=nb_thr[0])), (f"{vol_lab} {nb_thr[1]}", dict(thr=nb_thr[1])),
                        ("orizzonte 40", dict(horizon=40)), ("orizzonte 80", dict(horizon=80))]
            for lab, extra in nbs:
                kk = dict(kw, **extra)
                rob.append(("vicino " + lab, mrow(runner(name, f, vix, wb, rule, st, end, btc=btc, **kk))["mar"]))
            ro = runner(name, f, vix, wb, rule, st, end, btc=btc, mode="open", **kw)
            rob.append(("apertura giorno dopo", mrow(ro)["mar"]))
        # costi doppi: 0,15% per lato (BTC: costi di W3.1 raddoppiati)
        if btc and rule.startswith("S1"):
            old = (W.FEE_SPOT, W.FEE_PERP, W.SLIP)
            W.FEE_SPOT, W.FEE_PERP, W.SLIP = 2 * old[0], 2 * old[1], 2 * old[2]
            rc = runner(name, f, vix, wb, rule, st, end, btc=True)
            W.FEE_SPOT, W.FEE_PERP, W.SLIP = old
        else:
            rc = runner(name, f, vix, wb, rule, st, end, btc=btc, fee=(2 * BTC_FEE if btc else 0.0015), **kw)
        rob.append(("costi doppi", mrow(rc)["mar"]))
        rob.append(("senza il trade migliore", drop_best(f["close"], run, BTC_FEE if btc else M.FEE, sday)))
        nbv = [x for lab, x in rob if lab.startswith("vicino")]
        oth = [x for lab, x in rob if not lab.startswith("vicino")]
        nb_ok = sum(x > mb["mar"] for x in nbv) >= int(np.ceil(len(nbv) * 2 / 3))
        rec["nb_pass"] = f"{sum(x > mb['mar'] for x in nbv)}/{len(nbv)}"
        rec["rob_ok"] = bool(nb_ok and all(x > mb["mar"] for x in oth))
        rec["robusta"] = bool(rec["funziona"] and rec["rob_ok"])
        for lab, x in rob:
            out_rob.append(dict(asset=name, rule=rec["rule"], check=lab, mar=x, bh_mar=mb["mar"], batte_bh=x > mb["mar"]))
        out_main.append(rec)
    return out_main, out_per, out_rob, out_pl


def decades(name, f, vix):
    wb = M.s1_weekly(f)
    out = []
    for d0 in range(1930, 2030, 10):
        for rule in RULES:
            st = max(pd.Timestamp(f"{d0}-01-01"), M.test_start(f, rule == "S3"))
            en = min(pd.Timestamp(f"{d0 + 9}-12-31"), pd.Timestamp(M.CUT))
            if (en - st).days < 3 * 365:
                continue
            m, b = mrow(runner(name, f, vix, wb, rule, st, en)), mets(bh(f["close"], st, en, M.FEE))
            out.append(dict(asset=name, decade=f"{d0}s", rule=rule, start=str(st.date()), final=m["final"], cagr=m["cagr"], dd=m["dd"],
                            mar=m["mar"], n=m["n"], bh_cagr=b["cagr"], bh_dd=b["dd"], bh_mar=b["mar"]))
    return out


# ---------------------------------------------------------------- BTC: W3.1 + panic
def panic(f, vol, thr, a, b, w31, horizon=60, ema=200):
    """Ingressi panic quando W3.1 è flat e senza ingresso in sospeso; uscita S3 (orizzonte, poi crossunder EMA) o all'ingresso W3.1."""
    fw = f[(f.index >= pd.Timestamp(a)) & (f.index <= pd.Timestamp(b))]
    c = f["close"]
    e200 = c.ewm(span=ema, adjust=False).mean()
    wk = W.weekly_bars(f)
    busy = pd.Series(False, index=f.index)
    trs = w31["trades"] + ([w31["open"]] if w31["open"] else [])
    for t in trs:
        busy.loc[pd.Timestamp(t["signal"]):pd.Timestamp(t.get("exit") or f.index[-1])] = True
    w_entries = sorted(pd.Timestamp(t["entry"]) for t in trs)
    v = vol.dropna()
    xd = v.index[((v > thr) & (v.shift() <= thr)).to_numpy()]
    xd = [fw.index[fw.index.searchsorted(d)] for d in xd if fw.index[0] <= d <= fw.index[-1]]
    out, cur_end = [], None
    for d in xd:
        if busy[d] or (cur_end is not None and d <= cur_end):
            continue
        i0 = fw.index.get_loc(d)
        nxt = [x for x in w_entries if x > d]
        stop_day = nxt[0] - pd.Timedelta(days=1) if nxt else fw.index[-1]
        kind, ex, why = "vix", None, "open"
        for j in range(i0 + 1, len(fw)):
            dj = fw.index[j]
            if dj > stop_day:
                ex, why = fw.index[j - 1], "ingresso W3.1"
                break
            if kind == "vix" and dj >= d + pd.Timedelta(days=horizon):
                if c[dj] > e200[dj]:
                    kind = "trend"
                else:
                    ex, why = dj, "orizzonte"
                    break
            elif kind == "trend" and c[dj] < e200[dj] and c[fw.index[j - 1]] >= e200[fw.index[j - 1]]:
                ex, why = dj, "crossunder EMA200"
                break
        if ex is None:
            ex, why = fw.index[-1], "aperto"
        wkl = wk[wk.index <= d].iloc[-1]
        expo = min(1.0, W.R_LONG / (W.STOP_K * wkl["atr"] / wkl["close"]))
        out.append(dict(entry=d, exit=ex, expo=expo, reason=why, px_in=float(c[d]), px_out=float(c[ex]),
                        move=float(c[ex] / c[d] - 1), pnl=float(expo * (c[ex] / c[d] - 1) - 2 * BTC_FEE * expo)))
        cur_end = ex
    eq = w31["equity"]
    rr = eq.pct_change().fillna(0)
    rb = c.pct_change().reindex(eq.index).fillna(0)
    add = pd.Series(0.0, index=eq.index)
    for t in out:
        m = (eq.index > t["entry"]) & (eq.index <= t["exit"])
        add[m] += t["expo"] * rb[m]
        for dd in (t["entry"], t["exit"]):
            if dd in add.index:
                add[dd] -= BTC_FEE * t["expo"]
    comb = (1 + rr + add).cumprod() * eq.iloc[0]
    return out, comb


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    vix = M.load_vix()
    btc = M.load_btc()
    dvol = btc["dvol"]["close"]
    MA, PE, RO, PL, DE, DW = [], [], [], [], [], []
    for name in M.MAIN:
        f = M.load(name)
        a, b_, c_, d_ = eval_asset(name, f, vix, M.PERIODS, M.CUT)
        MA += a; PE += b_; RO += c_; PL += d_
        DE += decades(name, f, vix)
        log(f"{name} fatto ({time.time() - t0:.0f}s)")
    # BTC
    f = btc["f"]
    for vol, lab, thr, nb in ((vix, "VIX", 34.0, (30.0, 38.0)), (dvol, "DVOL", 93.9, (89.6, 98.3))):
        rules = RULES if lab == "VIX" else ("S3",)
        a, b_, c_, d_ = eval_asset("BTC", f, vol, M.BTC_PERIODS, M.BTC_CUT, btc=True, vol_lab=lab, thr=thr, nb_thr=nb, rules=rules)
        MA += a; PE += b_; RO += c_; PL += d_
    log(f"BTC fatto ({time.time() - t0:.0f}s)")
    # Dow 2000 (controllo: solo criterio dei sottoperiodi)
    for name in M.DOW:
        f2 = M.load(name)
        a, b_, _, _ = eval_asset(name, f2, vix, M.PERIODS, M.CUT, do_plac=False, dow=True)
        DW += a; PE += b_
    log(f"Dow fatto ({time.time() - t0:.0f}s)")
    pd.DataFrame(MA).to_csv(OUT / "principali.csv", index=False)
    pd.DataFrame(PE).to_csv(OUT / "periodi.csv", index=False)
    pd.DataFrame(RO).to_csv(OUT / "robustezza.csv", index=False)
    pd.DataFrame(PL).to_csv(OUT / "placebo.csv", index=False)
    pd.DataFrame(DE).to_csv(OUT / "decenni.csv", index=False)
    pd.DataFrame(DW).to_csv(OUT / "dow.csv", index=False)

    # ---- BTC: W3.1 e panic
    BT, PN = [], []
    for lab, fr, a, b in (("2021+", f, "2021-01-01", M.BTC_CUT), ("2018-20", btc["fl"], "2018-01-01", "2020-12-31")):
        w31 = E.simulate(fr, start=a, end=b)
        mw = mets(w31["equity"], [t["pnl"] for t in w31["trades"]] + ([w31["open"]["pnl_close"]] if w31["open"] else []))
        BT.append(dict(period=lab, rule="W3.1", **mw))
        for vl, vol, thr in (("VIX 34", vix, 34.0), ("DVOL 93.9", dvol, 93.9)):
            if lab == "2018-20" and vl.startswith("DVOL"):
                continue
            trs, comb = panic(fr, vol, thr, a, b, w31)
            mc = mets(comb)
            BT.append(dict(period=lab, rule=f"W3.1 + panic {vl}", **mc, added=len(trs)))
            for t in trs:
                PN.append(dict(period=lab, vol=vl, entry=str(t["entry"].date()), exit=str(t["exit"].date()), reason=t["reason"],
                               expo=round(t["expo"], 3), px_in=round(t["px_in"], 0), px_out=round(t["px_out"], 0),
                               move_pct=round(t["move"] * 100, 1), pnl_pct_quota=round(t["pnl"] * 100, 2)))
            if lab == "2021+":
                for p, (pa, pb) in M.BTC_PERIODS.items():
                    wp = E.simulate(fr, start=pa, end=pb)
                    _, cp = panic(fr, vol, thr, pa, pb, wp)
                    BT.append(dict(period=p, rule=f"W3.1 + panic {vl}", **mets(cp)))
                    if vl == "VIX 34":
                        BT.append(dict(period=p, rule="W3.1", **mets(wp["equity"])))
    pd.DataFrame(BT).to_csv(OUT / "btc.csv", index=False)
    pd.DataFrame(PN).to_csv(OUT / "panic.csv", index=False)
    report(pd.DataFrame(MA), pd.DataFrame(PE), pd.DataFrame(RO), pd.DataFrame(PL), pd.DataFrame(DE), pd.DataFrame(DW),
           pd.DataFrame(BT), pd.DataFrame(PN))
    log(f"tempo totale {time.time() - t0:.0f}s")
    (OUT / "risultati.txt").write_text("\n".join(LINES) + "\n")


def report(MA, PE, RO, PL, DE, DW, BT, PN):
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    log()
    log(f"Soglia placebo corretta (Bonferroni, M={NCONF}): p < {ALPHA:.5f}")
    cols = ["asset", "rule", "start", "final", "cagr", "dd", "mar", "n", "wr", "inpos", "stop_avg", "bh_final", "bh_cagr", "bh_dd",
            "bh_mar", "per_wins", "per_avail", "plac_p", "nb_pass", "funziona", "robusta"]
    x = MA[cols].copy()
    for c in ("mar", "bh_mar"):
        x[c] = x[c].map(fmt_mar)
    log("PERIODO INTERO (10k, CAGR %, DD giornaliero %, CAGR/DD) contro buy & hold")
    log(x.to_string(index=False))
    log()
    c21 = ["asset", "rule", "final21", "cagr21", "dd21", "mar21", "n21", "bh_final21", "bh_cagr21", "bh_dd21", "bh_mar21"]
    y = MA[MA["asset"] != "BTC"][c21].copy()
    for c in ("mar21", "bh_mar21"):
        y[c] = y[c].map(fmt_mar)
    log("DAL 2021")
    log(y.to_string(index=False))
    log()
    z = PE[PE["asset"].isin(M.MAIN + ["BTC"])].copy()
    for c in ("mar", "bh_mar"):
        z[c] = z[c].map(fmt_mar)
    log("SOTTOPERIODI (A 2000–10, B 2011–20, C 2021–; BTC: 2021–22, 2023–24, 2025–)")
    log(z.to_string(index=False))
    log()
    log("ROBUSTEZZA (CAGR/DD sul periodo intero)")
    r = RO.copy()
    r["mar"] = r["mar"].map(fmt_mar); r["bh_mar"] = r["bh_mar"].map(fmt_mar)
    log(r.to_string(index=False))
    log()
    log("PLACEBO")
    log(PL.to_string(index=False))
    log()
    log("S&P 500 per decennio")
    d = DE[DE["asset"] == "SPX"].copy()
    for c in ("mar", "bh_mar"):
        d[c] = d[c].map(fmt_mar)
    log(d.to_string(index=False))
    log()
    log("CONTROLLO DOW 2000 (criterio dei sottoperiodi, senza placebo)")
    for rule in RULES:
        dw = DW[DW["rule"] == rule]
        sel = MA[(MA["rule"] == rule) & MA["asset"].isin(M.MAIN[3:])]
        idx = MA[(MA["rule"] == rule) & (MA["asset"] == "SPX")]
        log(f"  {rule:8s}: Dow 2000 passano {int(dw['per_ok'].sum())}/{len(dw)} ({dw['per_ok'].mean()*100:.0f}%); "
            f"10 azioni scelte {int(sel['per_ok'].sum())}/{len(sel)} ({sel['per_ok'].mean()*100:.0f}%); S&P 500 {bool(idx['per_ok'].iloc[0])}; "
            f"CAGR/DD mediano Dow {dw['mar'].median():.2f} vs B&H {dw['bh_mar'].median():.2f}")
    log()
    b = BT.copy()
    b["mar"] = b["mar"].map(fmt_mar)
    log("BTC: W3.1 e W3.1 + panic")
    log(b.to_string(index=False))
    log()
    log("Trade panic")
    log(PN.to_string(index=False))
    log()
    s1 = MA[(MA["rule"] == "S1 L/S") & (MA["asset"] != "BTC")]
    log(f"VERDETTO 'W3.1 è generale': V1 funziona su {int(s1['funziona'].sum())}/13 (serve >= 7) -> "
        f"{'SI' if s1['funziona'].sum() >= 7 else 'NO'}")
    for rule in MA["rule"].unique():
        ok = MA[(MA["rule"] == rule) & MA["funziona"]]["asset"].tolist()
        rb = MA[(MA["rule"] == rule) & MA["robusta"]]["asset"].tolist()
        log(f"  {rule:10s}: funziona su {ok or 'nessuno'}; robusta su {rb or 'nessuno'}")


if __name__ == "__main__":
    main()
