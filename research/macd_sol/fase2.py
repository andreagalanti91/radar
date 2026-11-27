"""macd_sol · FASE 2: esegue PREREG.md (commit a5f2206) senza modificarlo. Uscite: fase2_output.txt, risultati.csv, trades_*.csv.
Uso dalla radice: python3 -I research/macd_sol/fase2.py"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import conteggi as K  # noqa: E402
import motore as M  # noqa: E402
L = M.L
COST = 0.001; SLIP = 0.001
END = "2026-11-24"; FULL_S = "2020-12-06"   # decisione 06/12/2020, prima esecuzione 07/12/2020 (DEVIAZIONI.md n. 1)
IS_E, OOS_S, Y24 = "2022-12-31", "2023-01-01", "2024-01-01"
OUT, ROWS = [], []
def p(s=""):
    print(s, flush=True); OUT.append(str(s))

f, w = K.bars()                       # spot SOL congelato, candele W-SUN, MACD 12/26/9
c = w["close"]
tr_ = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
w["atr"] = tr_.ewm(alpha=1 / 14, adjust=False).mean()
cross_up = (w["line"] > w["sig"]) & (w["line"].shift() <= w["sig"].shift())
cross_dn = (w["line"] < w["sig"]) & (w["line"].shift() >= w["sig"].shift())

def band(s, lo, hi): return (s >= lo) & (s <= hi)
def rule(name, mult=1.0, sell=10.0):
    lo, hi = -50 * mult, -3 * mult
    if name == "R1": return band(w["line"], lo, hi), w["line"] >= sell
    if name == "R2": return cross_up & band(w["line"], lo, hi), w["line"] >= sell
    if name == "R3": return band(w["hist"], lo, hi), w["hist"] >= sell
    if name == "R4": return band(w["line_n"], lo, hi), w["line_n"] >= sell
    raise KeyError(name)

# ------------------------------------------------------------------ simulatore a sé (1x spot, tutto dentro/fuori)
O, H, Lo, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close")); IDX = f.index
def run(buy, sell, s, e=END, stop_pct=None, trail_k=None, sell2=None):
    i0, i1 = IDX.searchsorted(pd.Timestamp(s)), IDX.searchsorted(pd.Timestamp(e), "right")
    ok = w["ok"]; cash, units, pend, tr = 1.0, 0.0, None, None; trades, eq = [], []
    def close(px, i, why):
        nonlocal cash, units, tr
        cash = units * px * (1 - SLIP) * (1 - COST)
        tr.update(exit=str(IDX[i].date()), exit_px=round(px * (1 - SLIP), 4), reason=why, pnl=cash / tr["eq0"] - 1); trades.append(tr)
        units, tr = 0.0, None
    for i in range(i0, i1):
        d = IDX[i]
        if pend is not None:
            if pend[0] == "exit" and tr: close(O[i], i, pend[1])
            elif pend[0] == "enter" and not tr:
                px = O[i] * (1 + SLIP); eq0 = cash; units = cash * (1 - COST) / px; cash = 0.0; wk = pend[1]
                tr = dict(signal=str(pend[2].date()), entry=str(d.date()), side="long", entry_px=round(px, 4), expo=1.0, eq0=eq0,
                          best=O[i], curatr=float(wk["atr"]), stop=-np.inf)
                if stop_pct: tr["stop"] = O[i] * (1 - stop_pct)
                if trail_k: tr["stop"] = float(wk["close"] - trail_k * wk["atr"]); tr["stop0"] = tr["stop"]
            pend = None
        if tr:
            if trail_k: tr["stop"] = max(tr["stop"], tr["best"] - trail_k * tr["curatr"])
            if Lo[i] <= tr["stop"]:
                close(min(O[i], tr["stop"]), i, "stop" if (stop_pct or tr["stop"] == tr.get("stop0")) else "trailing")
            else:
                tr["best"] = max(tr["best"], C[i])
        eq.append(cash if not tr else units * C[i])
        if d.dayofweek == 6 and d in w.index and ok.loc[d]:
            if tr:
                tr["curatr"] = float(w.at[d, "atr"])
                why = "segnale" if sell.loc[d] else ("SMA40" if sell2 is not None and sell2.loc[d] else None)
                if why: pend = ("exit", why)
            elif buy.loc[d]: pend = ("enter", w.loc[d], d)
    e_ = pd.Series(eq, IDX[i0:i1]) * 10000
    opn = None
    if tr:
        opn = dict(tr, exit=None, exit_px=round(C[i1 - 1], 4), reason="aperta", pnl=units * C[i1 - 1] * (1 - SLIP) * (1 - COST) / tr["eq0"] - 1)
    return dict(equity=e_, trades=trades, open=opn)

def mets(o, s=None):
    opn = o["open"]; m = L.met(o["equity"], o["trades"], opn); cl = o["trades"]
    m["wr_cl"] = round(100 * np.mean([t["pnl"] > 0 for t in cl])) if cl else None; m["chiuse"] = len(cl)
    e = o["equity"]; m["expo"] = round(100 * float(np.mean([_inpos(o, d) for d in e.index[::7]])), 0) if len(e) else 0
    return m
def _inpos(o, d):
    for t in o["trades"] + ([o["open"]] if o["open"] else []):
        if pd.Timestamp(t["entry"]) <= d and (t["exit"] is None or d < pd.Timestamp(t["exit"])): return 1
    return 0
def sub(e, a, b):
    x = e[(e.index >= pd.Timestamp(a)) & (e.index <= pd.Timestamp(b))]
    if len(x) < 2: return None, None
    prev = e[e.index < pd.Timestamp(a)]; base = prev.iloc[-1] if len(prev) else x.iloc[0]
    xx = pd.concat([pd.Series([base]), x.reset_index(drop=True)])
    return round((x.iloc[-1] / base - 1) * 100, 1), round(float((xx / xx.cummax() - 1).min() * 100), 1)
def years(e):
    y = e.resample("YE").last(); y0 = pd.concat([pd.Series([e.iloc[0]]), y.reset_index(drop=True)])
    return {str(d.year): round(float(v * 100), 1) for d, v in zip(y.index, y0.pct_change().dropna())}
def all_tr(o): return o["trades"] + ([o["open"]] if o["open"] else [])

# placebo §5.8: stesso numero di trade e stesse durate (settimane), ingressi a lunedì casuali, senza sovrapposizioni
def placebo_fin(trs, s, e, n_iter=2000, seed=7, closes=None):
    Of, Cf, ix = (f["open"], f["close"], f.index) if closes is None else closes
    ix = ix[(ix >= pd.Timestamp(s)) & (ix <= pd.Timestamp(e))]; mons = ix[ix.dayofweek == 0]; N = len(mons)
    oo = Of.reindex(ix).to_numpy(float); cc = Cf.reindex(ix).to_numpy(float); pos = {d: k for k, d in enumerate(ix)}
    spec = []
    for t in trs:
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else ix[-1] + pd.Timedelta(days=1)
        spec.append((max(1, int(np.ceil((b - a).days / 7))), 1 if t.get("side", "long") == "long" else -1, t.get("expo", 1.0)))
    def val(starts, sp):
        v = 1.0
        for m0, (dw, sd, ex) in zip(starts, sp):
            a = pos[mons[m0]]; bm = m0 + dw
            px1 = oo[pos[mons[bm]]] if bm < N else cc[-1]
            r = (px1 * (1 - SLIP) / (oo[a] * (1 + SLIP)) - 1) * sd
            v *= (1 + ex * r) * (1 - COST) ** 2
        return v * 10000
    D = sum(x[0] for x in spec)
    if not spec or D > N: return None, 1.0
    rng = np.random.default_rng(seed); out = []
    for _ in range(n_iter):
        order = rng.permutation(len(spec)); sp = [spec[k] for k in order]
        cuts = np.sort(rng.integers(0, N - D + 1, len(sp))); gaps = np.diff(np.r_[0, cuts])
        starts, cpos = [], 0
        for gp, x in zip(gaps, sp): cpos += gp; starts.append(cpos); cpos += x[0]
        out.append(val(starts, sp))
    return np.array(out), None

def pval(actual_fin, sims):
    return (int((sims >= actual_fin).sum()) + 1) / (len(sims) + 1)

def tradelist(trs, name):
    rows, acct = [], 10000.0
    for k, t in enumerate(trs, 1):
        acct *= 1 + t["pnl"] * t.get("expo_acc", 1.0) if False else 1 + t["pnl"]
        rows.append(dict(n=k, entrata=t["entry"], prezzo_in=round(t["entry_px"], 2), uscita=t["exit"] or "aperta (24/11/2026)",
                         prezzo_out=round(t["exit_px"], 2), motivo=t["reason"], giorni=((pd.Timestamp(t["exit"]) if t["exit"] else IDX[-1]) - pd.Timestamp(t["entry"])).days,
                         risultato_pct=round(t["pnl"] * 100, 1), conto_dopo=round(acct)))
    d = pd.DataFrame(rows); d.to_csv(HERE / f"trades_{name}.csv", index=False); return d

def mdt(d):
    cols = list(d.columns); s = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    s += ["| " + " | ".join(str(x) for x in r) + " |" for r in d.itertuples(index=False)]; return "\n".join(s)

# ================================================================== 1. R1–R4 (+ stop descrittive)
bh_full = L.bh(f, "2020-12-07", END, COST + SLIP); bh21 = L.bh(f, "2021-01-01", END, COST + SLIP)
p(f"B&H SOL dal 07/12/2020: {bh_full['fin']:,} $, CAGR {bh_full['cagr']}%, DD {bh_full['dd']}%, CAGR/DD {bh_full['cd']}")
p(f"B&H SOL dal 01/01/2021: {bh21['fin']:,} $, DD {bh21['dd']}%, CAGR/DD {bh21['cd']}")
bh_e = L.bh_curve(f, "2020-12-07", END, COST + SLIP)
p(f"B&H sottoperiodi: IS {sub(bh_e, FULL_S, IS_E)} OOS {sub(bh_e, OOS_S, END)} 2024→ {sub(bh_e, Y24, END)}")
RES = {}; PV = {}
for R in ("R1", "R2", "R3", "R4"):
    b, s_ = rule(R); o = run(b, s_, FULL_S); m = mets(o); e = o["equity"]
    o21 = run(b, s_, "2021-01-01"); m21 = mets(o21)
    isr, isd = sub(e, FULL_S, IS_E); oosr, oosd = sub(e, OOS_S, END); r24, d24 = sub(e, Y24, END); r2123, _ = sub(e, FULL_S, "2023-12-31")
    nb = {}
    for lab, (mu, se) in {"banda×0,5": (0.5, 10), "banda×2": (2, 10), "vendita+5": (1, 5), "vendita+20": (1, 20)}.items():
        bb, ss = rule(R, mu, se); nb[lab] = mets(run(bb, ss, FULL_S))
    nb_ok = sum((x["cd"] or -9) > bh_full["cd"] for x in nb.values())
    sims, _ = placebo_fin(all_tr(o), FULL_S, END); pv = pval(m["fin"], sims) if sims is not None else 1.0; PV[R] = pv
    crit = dict(c1=(m["cd"] or -9) > bh_full["cd"], c2=m["dd"] >= -35, c3=(m["wr_cl"] or 0) >= 60,
                c4=all(x is not None and x > 0 for x in (isr, oosr, r24)), c5=m["n"] >= 8, c6=m["wo"] > 10000, c7=nb_ok >= 2)
    RES[R] = dict(o=o, m=m, crit=crit)
    st = mets(run(b, s_, FULL_S, stop_pct=0.20)); ost = run(b, s_, FULL_S, stop_pct=0.20)
    worst = min((t["pnl"] for t in all_tr(ost)), default=0)
    p(f"\n=== {R} · dal 07/12/2020 ===")
    p(f"{m['fin']:,} $ ({m['ret']:+}%), CAGR {m['cagr']}%, DD {m['dd']}%, CAGR/DD {m['cd']}, trade {m['n']} ({m['chiuse']} chiuse, WR chiuse {m['wr_cl']}%), "
      f"esposizione {m['expo']}%, senza il migliore {m['wo']:,} $")
    p(f"IS {isr}% (DD {isd}) · OOS {oosr}% (DD {oosd}) · 2021–23 {r2123}% · 2024→ {r24}% (DD {d24}) · anni {years(e)}")
    p(f"dal 01/01/2021: {m21['fin']:,} $, DD {m21['dd']}%, CAGR/DD {m21['cd']}, trade {m21['n']}")
    p("vicini: " + "; ".join(f"{k} {v['fin']:,} $ C/DD {v['cd']} ({v['n']} tr)" for k, v in nb.items()) + f" → sopra B&H {nb_ok}/4")
    p(f"placebo: mediana {np.median(sims) if sims is not None else None:,.0f} $, p {pv:.4f}")
    p(f"criteri {crit}")
    p(f"[{R}s con stop −20%, descrittiva] {st['fin']:,} $, DD {st['dd']}%, trade {st['n']}, WR chiuse {st['wr_cl']}%, peggior trade {worst*100:.1f}%")
    ROWS.append(dict(famiglia="R", variante=R, fin=m["fin"], ret=m["ret"], cagr=m["cagr"], dd=m["dd"], cd=m["cd"], n=m["n"], wr_cl=m["wr_cl"],
                     is_ret=isr, oos_ret=oosr, r24=r24, wo=m["wo"], vicini_ok=nb_ok, p=round(pv, 4), fin21=m21["fin"], dd21=m21["dd"],
                     stop_fin=st["fin"], stop_dd=st["dd"], stop_n=st["n"], stop_worst=round(worst * 100, 1), **crit))
tl = {R: tradelist(all_tr(RES[R]["o"]), R) for R in ("R1", "R2")}
for R in ("R1", "R2"): p(f"\nOperazioni {R}\n" + mdt(tl[R]))
# flip solo long (lezione 79) sulle stesse candele
of = run(cross_up, cross_dn, FULL_S); mf = mets(of); mf21 = mets(run(cross_up, cross_dn, "2021-01-01"))
p(f"\nRif. flip solo long: dal 07/12/2020 {mf['fin']:,} $, DD {mf['dd']}%, CAGR/DD {mf['cd']}, trade {mf['n']}, WR chiuse {mf['wr_cl']}% · dal 2021 {mf21['fin']:,} $, DD {mf21['dd']}%")
ROWS.append(dict(famiglia="rif", variante="flip solo long", fin=mf["fin"], dd=mf["dd"], cd=mf["cd"], n=mf["n"], wr_cl=mf["wr_cl"], fin21=mf21["fin"], dd21=mf21["dd"]))

# ================================================================== 2. innesti in W3.2
def wsim(fa, s, e, mode=None, unit="pct", k=2.5, gate=None, fn=None):
    if fn is None: return M.sim(fa, s, e, k=k, gate=gate, mode=mode, unit=unit)
    eng = L.W; orig = eng.weekly_bars
    def wb(ff, _o=orig): return fn(_o(ff))
    eng.weekly_bars = wb
    try: return L.csim(fa, s, e, 0.25, k, gate)
    finally: eng.weekly_bars = orig
def wm(o):
    m = L.omet(o); m["wr_cl"] = round(100 * np.mean([t["pnl"] > 0 for t in o["trades"]])) if o["trades"] else None; return m
def placebo_wf(fa, s, e, base, n_block, n_iter=2000, seed=7):
    trs = L.otrades(base); rng = np.random.default_rng(seed); out = []
    for _ in range(n_iter):
        pick = rng.choice(len(trs), n_block, replace=False)
        win = [(pd.Timestamp(trs[j]["signal"]), pd.Timestamp(trs[j]["exit"]) if trs[j].get("exit") else pd.Timestamp(e), trs[j]["side"]) for j in pick]
        def fn(ww, win=win):
            for a, b, sd in win:
                msk = (ww.index >= a) & (ww.index < b); col = "long" if sd == "long" else "short"; ww.loc[msk, col] = False
            return ww
        out.append(wm(wsim(fa, s, e, fn=fn))["cd_raw"] or -9)
    return np.array(out)
def placebo_wu(fa, s, e, base, n_exit, n_iter=2000, seed=7):
    trs = [t for t in L.otrades(base)]; rng = np.random.default_rng(seed); out = []
    for _ in range(n_iter):
        pick = rng.choice(len(trs), n_exit, replace=False); days = []
        for j in pick:
            t = trs[j]; a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else pd.Timestamp(e)
            sun = pd.date_range(a, b, freq="W-SUN"); sun = sun[sun < b - pd.Timedelta(days=1)]
            if len(sun): days.append((sun[rng.integers(len(sun))], t["side"]))
        def fn(ww, days=days):
            for d, sd in days:
                if d in ww.index: ww.loc[d, "dist_long" if sd == "long" else "dist_short"] = True
            return ww
        out.append(wm(wsim(fa, s, e, fn=fn))["cd_raw"] or -9)
    return np.array(out)

p("\n\n=== INNESTI IN W3.2 (rischio 25%, trailing 2,5 ATRw) ===")
fe_ = L.cfeats("ETH"); mETH = wm(wsim(fe_, "2021-01-11", str(fe_.index[-1].date())))
fS = L.cfeats("SOL"); ES = str(fS.index[-1].date()); bhS = L.bh(fS, "2021-01-11", ES, 0.002)
INN = {}
tests = [("BTC", "pct"), ("ETH", "pct"), ("SOL", "pct"), ("SOL", "abs")]
for a, u in tests:
    fa = L.cfeats(a); s = "2021-01-01" if a == "BTC" else "2021-01-11"; E = str(fa.index[-1].date())
    base = wsim(fa, s, E); mb = wm(base); bIS = wm(wsim(fa, s, IS_E)); bOOS = wm(wsim(fa, OOS_S, E))
    btr = {(t["entry"], t["side"]) for t in L.otrades(base)}
    for mode in ("F", "U"):
        key = f"W-{mode}{'%' if u == 'pct' else '$'} {a}"
        o = wsim(fa, s, E, mode, u); m = wm(o); mi = wm(wsim(fa, s, IS_E, mode, u)); mo = wm(wsim(fa, OOS_S, E, mode, u))
        vtr = {(t["entry"], t["side"]) for t in L.otrades(o)}
        if mode == "F": nchg = len(btr - vtr)
        else: nchg = sum(1 for t in L.otrades(o) if t.get("reason") == "dist" and (t["entry"], t["side"]) in btr) - sum(1 for t in L.otrades(base) if t.get("reason") == "dist")
        same = (round(m["fin"]) == round(mb["fin"])) and vtr == btr
        if same or nchg <= 0: pv = 1.0; sims = None
        else:
            sims = placebo_wf(fa, s, E, base, min(nchg, len(btr))) if mode == "F" else placebo_wu(fa, s, E, base, min(nchg, len(btr)))
            pv = pval(m["cd_raw"] or -9, sims)
        PV[key] = pv
        line = (f"{key}: {m['fin']:,} $ DD {m['dd']}% C/DD {m['cd']} trade {m['n']} WR chiuse {m['wr_cl']}% · base {mb['fin']:,} $ DD {mb['dd']}% C/DD {mb['cd']} WR {mb['wr_cl']}% · "
                f"IS {mi['cd']} (DD {mi['dd']}) vs {bIS['cd']} (DD {bIS['dd']}) · OOS {mo['cd']} (DD {mo['dd']}) vs {bOOS['cd']} (DD {bOOS['dd']}) · "
                f"trade cambiati {nchg} · identica alla base: {same} · placebo p {pv:.4f}")
        if a in ("BTC", "ETH"):
            serve = all((x["cd_raw"] or -9) > (y["cd_raw"] or -9) and x["dd"] >= y["dd"] - 2 for x, y in ((m, mb), (mi, bIS), (mo, bOOS))) and (m["wr_cl"] or 0) >= (mb["wr_cl"] or 0)
            crit = dict(migliora=serve)
        else:
            per = {k: wm(wsim(fa, x, y, mode, u)) for k, x, y in (("IS", s, IS_E), ("OOS", OOS_S, E), ("2024", Y24, E))}
            nk = {kk: wm(wsim(fa, s, E, mode, u, k=kk)) for kk in (2.0, 3.0)}
            crit = dict(c1=(m["cd"] or -9) > bhS["cd"] and (m["cd"] or -9) >= mETH["cd"], c2=m["dd"] >= -35, c3=(m["wr_cl"] or 0) >= 60,
                        c4=all(per[k]["ret"] > 0 for k in per), c5=m["n"] >= 8, c6=m["wo"] > 10000,
                        c7=all((nk[kk]["cd"] or -9) > bhS["cd"] for kk in nk))
            line += f" · IS {per['IS']['ret']}% OOS {per['OOS']['ret']}% 2024→ {per['2024']['ret']}% · senza migliore {m['wo']:,} $ · vicini k2/k3 C/DD {nk[2.0]['cd']}/{nk[3.0]['cd']}"
        p(line); p(f"   criteri {crit}")
        INN[key] = dict(m=m, crit=crit, same=same)
        ROWS.append(dict(famiglia="innesto", variante=key, fin=m["fin"], dd=m["dd"], cd=m["cd"], n=m["n"], wr_cl=m["wr_cl"], base_fin=mb["fin"],
                         base_dd=mb["dd"], base_cd=mb["cd"], is_cd=mi["cd"], is_base_cd=bIS["cd"], oos_cd=mo["cd"], oos_base_cd=bOOS["cd"],
                         cambiati=nchg, identica=same, p=round(pv, 4), **crit))
p(f"riferimenti SOL dal 11/01/2021: B&H C/DD {bhS['cd']} ({bhS['fin']:,} $), W3.2 ETH C/DD {mETH['cd']}")

# ================================================================== 3. candidati B (IS 11/01/2021 → 31/12/2022)
p("\n\n=== CANDIDATI B · scelta in IS ===")
S_IS = "2021-01-11"
isc = {R: mets(run(*rule(R), S_IS, IS_E)) for R in ("R1", "R2", "R3", "R4")}
p("R in IS: " + "; ".join(f"{R} C/DD {v['cd']} DD {v['dd']} trade {v['n']}" for R, v in isc.items()))
Rbest = max(isc, key=lambda R: (isc[R]["cd_raw"] if isc[R]["cd_raw"] is not None else -9, -isc[R]["n"]))
p(f"C1 usa {Rbest}")
sma40 = w["close"].rolling(40).mean()
def sma_rule(n):
    sm = w["close"].rolling(n).mean(); return cross_up & (w["close"] > sm), cross_dn, (w["close"] < sm)
gETH = None
def c2gate():
    import importlib
    esun = fe_.index[fe_.index.dayofweek == 6]; o = L.csim(fe_, "2020-06-01"); g = pd.Series(0, index=esun)
    for t in L.otrades(o):
        a_, sd = pd.Timestamp(t["entry"]), (1 if t["side"] == "long" else -1)
        b_ = pd.Timestamp(t["exit"]) if t.get("exit") else esun[-1] + pd.Timedelta(days=1)
        g[(g.index >= a_) & (g.index < b_)] = sd
        if pd.Timestamp(t["signal"]) in g.index: g[pd.Timestamp(t["signal"])] = sd
    return g
gETH = c2gate()
def cand(cn, s, e, k=2.5, n_sma=40):
    if cn == "C1": b, s_ = rule(Rbest); o = run(b, s_, s, e, trail_k=k); return o, mets(o)
    if cn == "C2": o = wsim(fS, s, e, "U", "abs", k=k, gate=gETH); m = wm(o); m["expo"] = None; m["chiuse"] = len(o["trades"]); return o, m
    if cn == "C3": b, s_, s2 = sma_rule(n_sma); o = run(b, s_, s, e, sell2=s2); return o, mets(o)
ISC = {}
for cn in ("C1", "C2", "C3"):
    o, m = cand(cn, S_IS, IS_E); ISC[cn] = m
    p(f"{cn} IS: {m['fin']:,} $, DD {m['dd']}%, C/DD {m['cd']}, trade {m['n']}, WR chiuse {m['wr_cl']}%")
elig = [cn for cn in ISC if ISC[cn]["dd"] >= -35 and ISC[cn]["n"] >= 1]
chosen = max(elig, key=lambda cn: ((ISC[cn]["cd_raw"] or -9), -ISC[cn]["n"])) if elig else None
p(f"ammessi {elig} → scelto {chosen}")
if chosen:
    Ecn = ES if chosen == "C2" else END
    o, m = cand(chosen, OOS_S, Ecn)
    bhO = L.bh(fS if chosen == "C2" else f, OOS_S, Ecn, (0.002 if chosen == "C2" else COST + SLIP))
    e = o["equity"]; r24, d24 = sub(e, Y24, Ecn)
    nbk = {"C1": [dict(k=2.0), dict(k=3.0)], "C2": [dict(k=2.0), dict(k=3.0)], "C3": [dict(n_sma=30), dict(n_sma=50)]}[chosen]
    nbm = [cand(chosen, OOS_S, Ecn, **kw)[1] for kw in nbk]
    trs = L.otrades(o) if chosen == "C2" else all_tr(o)
    closes = (fS["open"], fS["close"], fS.index) if chosen == "C2" else None
    sims, _ = placebo_fin(trs, OOS_S, Ecn, closes=closes); pv = pval(m["fin"], sims) if sims is not None else 1.0; PV["B " + chosen] = pv
    wrc = m["wr_cl"]
    crit = dict(c1=(m["cd"] or -9) > bhO["cd"], c2=m["dd"] >= -35, c3=(wrc or 0) >= 60, c4=m["ret"] > 0 and (r24 or -1) > 0,
                c5=m["n"] >= 6, c6=m["wo"] > 10000, c7=all((x["cd"] or -9) > bhO["cd"] for x in nbm))
    p(f"\n{chosen} OOS dal 01/01/2023: {m['fin']:,} $ ({m['ret']:+}%), CAGR {m['cagr']}%, DD {m['dd']}%, C/DD {m['cd']}, trade {m['n']}, WR chiuse {wrc}%, "
      f"senza il migliore {m['wo']:,} $ · 2024→ {r24}% (DD {d24}) · B&H OOS {bhO['fin']:,} $ C/DD {bhO['cd']} DD {bhO['dd']}")
    p(f"vicini {nbk}: " + "; ".join(f"{x['fin']:,} $ C/DD {x['cd']}" for x in nbm) + f" · placebo p {pv:.4f}")
    p(f"criteri {crit}")
    # descrittivo: stesso candidato sull'intero 11/01/2021 →
    of_, mf_ = cand(chosen, S_IS, Ecn)
    p(f"{chosen} descrittivo dal 11/01/2021: {mf_['fin']:,} $, DD {mf_['dd']}%, C/DD {mf_['cd']}, trade {mf_['n']}")
    if chosen == "C2":
        rows = []; acct = 10000.0
        for k_, t in enumerate(L.otrades(o), 1):
            acct *= 1 + t["pnl"]
            rows.append(dict(n=k_, lato=t["side"], entrata=t["entry"], prezzo_in=t["entry_px"], uscita=t.get("exit") or "aperta", prezzo_out=t.get("exit_px", round(t.get("last", 0), 2)),
                             motivo=t.get("reason", "aperta"), esposizione=t["expo"], risultato_pct=round(t["pnl"] * 100, 1), conto_dopo=round(acct)))
        d = pd.DataFrame(rows); d.to_csv(HERE / "trades_B.csv", index=False)
    else:
        d = tradelist(all_tr(o), "B")
    p(f"\nOperazioni candidato B ({chosen}, OOS)\n" + mdt(d))
    ROWS.append(dict(famiglia="B", variante=chosen, fin=m["fin"], dd=m["dd"], cd=m["cd"], n=m["n"], wr_cl=wrc, r24=r24, wo=m["wo"], p=round(pv, 4), **crit))
    for cn in ("C1", "C2", "C3"):
        ROWS.append(dict(famiglia="B-IS", variante=cn, fin=ISC[cn]["fin"], dd=ISC[cn]["dd"], cd=ISC[cn]["cd"], n=ISC[cn]["n"], wr_cl=ISC[cn]["wr_cl"]))

# ================================================================== 4. Holm m = 13
hm = L.holm(PV)
p(f"\nHolm (m = {len(PV)}): " + "; ".join(f"{k} p {v:.4f} {'passa' if hm[k] else 'no'}" for k, v in sorted(PV.items(), key=lambda x: x[1])))
pd.DataFrame(ROWS).to_csv(HERE / "risultati.csv", index=False)
(HERE / "fase2_output.txt").write_text("\n".join(OUT) + "\n")
