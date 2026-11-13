"""Esecuzione dello studio squeeze (PREREG.md). Uso: python research/liq_squeeze/sq_run.py
Scrive risultati.txt, regole.csv, vicini.csv, sizing.csv, w3_dca.csv, trade_L1.csv, trade_L2.csv, trade_L3.csv, trade_S1.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_bt as B  # noqa: E402
from sq_bt import W  # noqa: E402

out = []
P = lambda s="": out.append(str(s)) or print(s, flush=True)
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)

cp = B.WORK / "casc.pkl"
if cp.exists() and len(pd.read_pickle(cp)[0]) == B.NB:
    CL, CS = pd.read_pickle(cp)
else:
    CL, CS = B.cascades("long"), B.cascades("short"); pd.to_pickle((CL, CS), cp)
R24 = B.r24()
IS_MASK = B.M.index < B.SPLIT

RULES = {"L1": (+1, "mkt", True), "L2": (+1, "dca", True), "L3": (+1, "dca", False), "S1": (-1, "dca", True)}


def signal(name, thr=0.5, rad=6, H=120, cw=72, pct=0.2, clean="or"):
    side, mode, need_clean = RULES[name]
    S = B.imbalance(rad)
    s = (S >= thr) if side > 0 else (S <= -thr)
    if need_clean:
        s = s & B.clean_flags("long" if side > 0 else "short", cw, pct, clean, CL if side > 0 else CS, rad)
    return s.fillna(False), side, mode, H


def run(name, **kw):
    s, side, mode, H = signal(name, **kw)
    return B.select(s, side, mode, H), s


def mom(sig, side, mode, H, which):
    """Momentum con la stessa frequenza di ore-segnale del IS. which '+' = nel verso del trade, '−' = contro."""
    fr = float(sig[IS_MASK].mean())
    r = R24
    up = (which == "+") == (side > 0)
    s = r >= r[IS_MASK].quantile(1 - fr) if up else r <= r[IS_MASK].quantile(fr)
    return B.select(s.fillna(False), side, mode, H)


def mean_ret(trs, a=None, b=None):
    x = [t["ret"] for t in trs if (a is None or t["T"] >= a) and (b is None or t["T"] < b)]
    return np.mean(x) if x else np.nan


def placebo_a(trs, side, mode, H, draws=1000, seed=1):
    D = B.all_trades(side, mode, H)
    pool = [t["ret"] for T, t in D.items() if T != "_n" and t and not t.get("nofill") and t["complete"]]
    pool = np.array(pool)
    g = np.random.default_rng(seed)
    n = len(trs)
    pl = np.array([g.choice(pool, n, replace=False).mean() for _ in range(draws)])
    obs = np.mean([t["ret"] for t in trs])
    return float((pl >= obs).mean()), float(pl.mean())


def placebo_b(sig, side, mode, H, obs, draws=200, seed=2):
    g = np.random.default_rng(seed)
    v = sig.to_numpy()
    pl = []
    for _ in range(draws):
        d = int(g.integers(30 * 24, 700 * 24))
        s2 = pd.Series(np.roll(v, d), sig.index)
        tr = B.select(s2, side, mode, H)
        pl.append(np.mean([t["ret"] for t in tr]) if tr else np.nan)
    pl = np.array(pl)
    return float(np.nanmean(pl >= obs)), float(np.nanmean(pl))


def row(lab, trs, extra=None):
    r = B.stats(trs, lab=lab); r.update(B.split_stats(trs, lab))
    if extra:
        r.update(extra)
    return r


def tr_df(trs):
    return pd.DataFrame([dict(segnale=str(t["T"]), lato="long" if t["side"] > 0 else "short", p=round(t["p"]), F=round(t["F"]), stop=round(t["stop"]),
                              T1=round(t["T1"]), T2=round(t["T2"]) if t["T2"] else None, riempito=round(t["filled"], 2),
                              prezzo_medio=round(sum(u[0] * u[2] for u in t["units"]) / max(1e-9, sum(u[0] for u in t["units"]))),
                              uscita=str(B.TI[min(t["exit"], B.NB - 1)]), esito=t["why"], ret_pct=round(t["ret"] * 100, 3), completo=t["complete"])
                         for t in trs])


# ------------------------------------------------------------------ W3 e W3-DCA
def w3_dca(ff, start):
    """W3 invariata (radar/weekly.simulate) e W3-DCA: metà a mercato come W3, metà su 3 limit fra p e F validi 24 ore (resto a
    mercato alla scadenza). Equity ricostruita giorno per giorno: la metà DCA ha prezzo medio Pd invece di P0."""
    r = W.simulate(ff, start)
    eq = r["equity"].astype(float)
    eq = eq[eq.index >= start]
    days = eq.index
    cl = ff["close"].reindex(days).to_numpy(float)
    new = eq.to_numpy().copy()
    mult, rows, last = 1.0, [], 0
    for t in r["trades"]:
        T = pd.Timestamp(t["entry"])
        side = 1 if t["side"] == "long" else -1
        P0 = float(t["entry_px"])
        i0 = days.searchsorted(T)
        i1 = days.searchsorted(pd.Timestamp(t["exit"])) if t.get("exit") else len(days) - 1
        new[last:i0] = mult * eq.to_numpy()[last:i0]
        if T not in B.M.index:
            continue
        g = B.geometry(T, side)
        if g is None:
            g = {"p": float(B.M.at[T, "p"]), "F": float(B.M.at[T, "p"]) * (0.97 if side > 0 else 1.03)}
        p, F = g["p"], g["F"]
        k = B.TI.searchsorted(T)
        lev = [p - (p - F) * x / 3 for x in (1, 2, 3)]
        px, nf = [], 0
        for L_ in lev:
            lo, hi = B.Ll[k:k + 24], B.Hh[k:k + 24]
            m_ = (lo <= L_ * (1 - B.THRU)) if side > 0 else (hi >= L_ * (1 + B.THRU))
            b = np.flatnonzero(m_)
            if len(b):
                nf += 1
                px.append(min(B.O[k + b[0]], L_) if side > 0 else max(B.O[k + b[0]], L_))
            else:
                px.append(B.O[min(k + 24, B.NB - 1)])
        Pd = float(np.mean(px))
        e0 = float(eq.iloc[i0 - 1]) if i0 > 0 else float(eq.iloc[0])
        lt = float(t["expo"])
        for i in range(i0, i1 + 1):
            ex = float(t["exit_px"]) if (i == i1 and t.get("exit")) else cl[i]
            diff = 0.5 * lt * e0 * ((ex / Pd - ex / P0) if side > 0 else (ex / P0 - ex / Pd))
            new[i] = mult * (eq.iloc[i] + diff)
        pnl_new = new[i1] / (mult * e0) - 1
        mult = new[i1] / float(eq.iloc[i1])
        last = i1 + 1
        rows.append(dict(ingresso=t["entry"], lato=t["side"], P_W3=round(P0), F=round(F), P_dca=round(Pd), diff_pct=round((Pd / P0 - 1) * 100, 2),
                         limit_riempiti=nf, pnl_W3=round(t["pnl"] * 100, 2), pnl_dca=round(pnl_new * 100, 2)))
    new[last:] = mult * eq.to_numpy()[last:]
    return eq, pd.Series(new, days), pd.DataFrame(rows)


def eqstats(e, lab):
    e = e / e.iloc[0] * 10000
    dd = float((e / e.cummax() - 1).min())
    rend = e.iloc[-1] / 10000 - 1
    return dict(regola=lab, finale=round(float(e.iloc[-1])), rend=round(rend * 100, 1), dd=round(dd * 100, 1), mar=round(rend / abs(dd), 2))


if __name__ == "__main__":
    P("== Studio squeeze · dati orari " + str(B.TI[0]) + " → " + str(B.TI[-1]) + f" · mappe {len(B.M)} ({B.M.index[0]} → {B.M.index[-1]})")
    P(f"Ore con cascata long valida {int(CL.sum())}, short {int(CS.sum())}")
    rows, TRS, SIGS = [], {}, {}
    for name in RULES:
        trs, s = run(name)
        TRS[name], SIGS[name] = trs, s
        side, mode, _ = RULES[name]
        P(f"\n-- {name}: ore-segnale {int(s.sum())} ({s.mean()*100:.2f}%), trade {len(trs)}")
        pa = placebo_a(trs, side, mode, 120)
        pb = placebo_b(s, side, mode, 120, np.mean([t["ret"] for t in trs]) if trs else np.nan)
        rows.append(row(name, trs, dict(p_placebo_ore=round(pa[0], 4), placebo_ore_media=round(pa[1] * 100, 3),
                                        p_placebo_mappe=round(pb[0], 4), placebo_mappe_media=round(pb[1] * 100, 3))))
        for wh in ("+", "−"):
            mt = mom(s, side, mode, 120, wh)
            rows.append(row(f"  {name} momentum {wh}", mt))
        tr_df(trs).to_csv(HERE / f"trade_{name}.csv", index=False)
    # pulizia sola (L2 senza S)
    c0 = B.clean_flags("long", 72, 0.2, "or", CL).fillna(False)
    rows.append(row("  pulizia sola (L2 senza S)", B.select(c0, 1, "dca", 120)))
    rows.append(B.bh())
    eqW, eqD, w3rows = w3_dca(B.f, "2021-01-01")
    rows.append(eqstats(eqW, "W3"))
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "regole.csv", index=False)
    P("\n== Regole e controlli (10k, 1x, costi e funding; media e PF per trade in %)")
    P(R.to_string(index=False))

    # periodi separati: capitale con i soli trade del periodo
    P("\n== Capitale per periodo (solo trade del periodo)")
    pr = []
    for name, trs in TRS.items():
        for lab, a, b in (("2021–23", None, B.SPLIT), ("2024→", B.SPLIT, None)):
            sub = [t for t in trs if (a is None or t["T"] >= a) and (b is None or t["T"] < b)]
            st = B.stats(sub, lab=name); st["periodo"] = lab; pr.append(st)
    P(pd.DataFrame(pr)[["regola", "periodo", "finale", "rend", "dd", "mar", "trade", "wr", "pf", "media"]].to_string(index=False))

    # vicini
    P("\n== Vicini (PF, media per trade %, trade; IS/OOS)")
    NBH = dict(thr=(0.3, 0.7), rad=(4, 8), H=(72, 168), cw=(48, 96), pct=(0.1, 0.3), clean=("casc", "pct"))
    vr = []
    for name in RULES:
        side, mode, need = RULES[name]
        for k, vals in NBH.items():
            if not need and k in ("cw", "pct", "clean"):
                continue
            for v in vals:
                trs, s = run(name, **{k: v})
                r = B.stats(trs, lab=f"{name} {k}={v}"); r.update(B.split_stats(trs, name)); vr.append(r)
    V = pd.DataFrame(vr); V.to_csv(HERE / "vicini.csv", index=False)
    P(V[["regola", "finale", "dd", "trade", "wr", "pf", "media", "media_IS", "media_OOS"]].to_string(index=False))
    for name in RULES:
        sub = V[V.regola.str.startswith(name + " ")]
        P(f"  {name}: vicini con PF > 1: {int((sub.pf > 1).sum())}/{len(sub)}")

    # sizing a rischio
    P("\n== Sizing a rischio fisso (nozionale = rischio / distanza dallo stop medio, max 1x)")
    w3t = W.simulate(B.f, "2021-01-01")["trades"]
    busy = pd.Series(False, B.M.index)
    for t in w3t:
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else B.M.index[-1] + pd.Timedelta(hours=1)
        busy[(busy.index >= a) & (busy.index < b)] = True
    flat = (~busy).to_dict()
    sz = []
    for name in ("L1", "L2", "S1"):
        side, mode, _ = RULES[name]
        for rk in (0.005, 0.01):
            def scale(t, rk=rk, mode=mode):
                pe = t["p"] if mode == "mkt" else t["p"] - (t["p"] - t["F"]) * 2 / 3
                return min(1.0, rk / abs(pe - t["stop"]) * pe)
            for lab, allow in (("sempre", None), ("solo W3 flat", flat)):
                trs = B.select(SIGS[name], side, mode, 120, allow=allow)
                r = B.stats(trs, scale=scale, lab=f"{name} rischio {rk*100:.1f}% {lab}"); sz.append(r)
    SZ = pd.DataFrame(sz); SZ.to_csv(HERE / "sizing.csv", index=False)
    P(SZ[["regola", "finale", "rend", "dd", "mar", "trade", "wr", "pf"]].to_string(index=False))

    # W3-DCA
    P("\n== W3 con metà a mercato e metà sulla fascia DCA (3 limit, 24h, resto a mercato)")
    wr_ = []
    IS = B.f[B.f.index <= "2023-12-31"]
    for lab, ff, st in (("2021→", B.f, "2021-01-01"), ("2021–23", IS, "2021-01-01"), ("2024→", B.f, "2024-01-01")):
        a, b, d = w3_dca(ff, st)
        wr_ += [dict(eqstats(a, "W3"), periodo=lab), dict(eqstats(b, "W3-DCA"), periodo=lab)]
        if lab == "2021→":
            d.to_csv(HERE / "w3_dca_trade.csv", index=False)
            P(d.to_string(index=False))
    WD = pd.DataFrame(wr_); WD.to_csv(HERE / "w3_dca.csv", index=False)
    P(WD.to_string(index=False))
    (HERE / "risultati.txt").write_text("\n".join(out) + "\n")
