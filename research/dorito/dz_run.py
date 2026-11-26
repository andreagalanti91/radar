"""Dorito · risultati come da PREREG (commit 5c92dc0). Output in research/dorito/:
risultati.csv, criteri.csv, studio_evento.csv, w32_trade.csv, risultati.txt."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dz_engine import *  # noqa

RNG = np.random.default_rng(20261126)
NPL_S = NPL_W = 1000
NPL_E = 2000
OUT = []
txt = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); txt.append(s)

# ------------------------------------------------------------------ dati
d = daily(include_partial=False)  # fino al 25/11/2026
END = d.index[-1]
O, C = d.open.to_numpy(float), d.close.to_numpy(float)
FU = funding_series(d.index).to_numpy(float)  # 0 prima del 2020 e dopo il 21/11/2026
ix = lambda s: int(d.index.searchsorted(pd.Timestamp(s)))
PER = {"P1": ("2018-01-01", "2020-12-31"), "P2": ("2021-01-01", "2023-12-31"), "P3": ("2024-01-01", str(END.date())),
       "dal2018": ("2018-01-01", str(END.date())), "dal2021": ("2021-01-01", str(END.date())),
       "IS18-22": ("2018-01-01", "2022-12-31"), "OOS23-": ("2023-01-01", str(END.date()))}
BASE = (10, 40, True)
NEIGH = [(q, L, True) for L in (30, 40, 50) for q in (8, 10, 12) if (q, L) != (10, 40)]
GLAZ = (6, 30, False)
SIG = {}
def sig(tf, p):
    k = (tf, p)
    if k not in SIG:
        SIG[k] = daily_signal(d, tf, *p).to_numpy(int)
    return SIG[k]

def run_s(sg, mode, a, b, Oa=O, Ca=C, Fa=FU, index=None):
    index = d.index if index is None else index
    t0, t1 = int(index.searchsorted(pd.Timestamp(a))), int(index.searchsorted(pd.Timestamp(b), "right")) - 1
    cash, trs, eq = standalone(Oa, Ca, Fa, sg, mode, t0, t1)
    return metr(eq, (index[t1] - index[t0]).days + 1, trs)

def bh(a, b, Oa=O, Ca=C, index=None):
    index = d.index if index is None else index
    t0, t1 = int(index.searchsorted(pd.Timestamp(a))), int(index.searchsorted(pd.Timestamp(b), "right")) - 1
    return metr(buyhold(Oa, Ca, t0, t1), (index[t1] - index[t0]).days + 1)

STRAT = {"S1": (3, "long"), "S2": (3, "ls"), "S3": (1, "long"), "S4": (1, "ls")}

# ------------------------------------------------------------------ W3.2
rd = lambda n: pd.read_csv(os.path.join(ROOT, "research/p2_nuovi/data", n), index_col=0, parse_dates=True)
FR, FL = rd("f_repo.csv.gz"), rd("f_long.csv.gz")
WEND = "2026-11-15"
WPER = {"P1": (FL, "2018-01-01", "2020-12-31"), "P2": (FR, "2021-01-01", "2023-12-31"), "P3": (FR, "2024-01-01", WEND),
        "dal2021": (FR, "2021-01-01", WEND), "dal2018": (FL, "2018-01-01", WEND),
        "IS18-22": (FL, "2018-01-01", "2022-12-31"), "OOS23-": (FR, "2023-01-01", WEND)}
WSIM = {k: W32(f, en) for k, (f, st, en) in WPER.items()}
VARW = {"W1": ("exit", 3), "W2": ("exit", 1), "W3": ("filter", 3), "W4": ("filter", 1)}
def tri_for(sim, tf, p):
    return pd.Series(sig(tf, p), index=d.index).reindex(sim.idx).fillna(0).to_numpy(int)
def run_w(per, var=None, tf=3, p=BASE, window=30, tri=None):
    sim = WSIM[per]; st = WPER[per][1]
    if var is None:
        return sim.run(st)
    kind = VARW[var][0]
    tri = tri_for(sim, tf, p) if tri is None else tri
    return sim.run(st, kind, tri, window)

say("# Dorito · risultati (PREREG 5c92dc0) · dati giornalieri fino al", END.date(), "; W3.2 fino al", WEND)
wb = {k: run_w(k) for k in WPER}
wbm = {k: w_metr(v) for k, v in wb.items()}
say("Verifica W3.2 (copia): dal2021", wbm["dal2021"]["finale"], wbm["dal2021"]["dd"], "| P1", wbm["P1"]["finale"], wbm["P1"]["dd"],
    "(lorde dell'ultima commissione: 78.474 e 25.142 = originale; qui la posizione aperta a fine periodo è al netto dell'uscita)")

# ------------------------------------------------------------------ S1–S4 e buy & hold
BH = {k: bh(*v) for k, v in PER.items()}
for k, v in BH.items():
    OUT.append(dict(oggetto="buy&hold", periodo=k, **v))
for k, v in wbm.items():
    OUT.append(dict(oggetto="W3.2", periodo=k, **v))
SM = {}
for nm, (tf, mode) in STRAT.items():
    for k, (a, b) in PER.items():
        m = run_s(sig(tf, BASE), mode, a, b); SM[(nm, k)] = m
        OUT.append(dict(oggetto=nm, periodo=k, **m))
        g = run_s(sig(tf, GLAZ), mode, a, b)
        OUT.append(dict(oggetto=nm + "_glaz30/6", periodo=k, **g))
# vicini
NB = {}
for nm, (tf, mode) in STRAT.items():
    ok = 0
    for p in NEIGH:
        prof = all(run_s(sig(tf, p), mode, *PER[k])["finale"] > 10000 for k in ("P1", "P2", "P3"))
        ok += prof
    NB[nm] = ok
# placebo S: traslazione circolare della serie dei segnali sul 2018-01-01→fine, finale continuo
a0, a1 = ix("2018-01-01"), len(d) - 1
PS = {}
for nm, (tf, mode) in STRAT.items():
    sg = sig(tf, BASE).copy()
    seg = sg[a0:a1 + 1]; N = len(seg)
    real = standalone(O, C, FU, sg, mode, a0, a1, collect=False)[0]
    cnt = 0
    for _ in range(NPL_S):
        k = int(RNG.integers(60, N - 60))
        s2 = sg.copy(); s2[a0:a1 + 1] = np.roll(seg, k)
        cnt += standalone(O, C, FU, s2, mode, a0, a1, collect=False)[0] >= real
    PS[nm] = cnt / NPL_S

# ------------------------------------------------------------------ W1–W4
WM, WR = {}, {}
for v, (kind, tf) in VARW.items():
    for k in WPER:
        r = run_w(k, v, tf); WR[(v, k)] = r; WM[(v, k)] = w_metr(r)
        OUT.append(dict(oggetto=v, periodo=k, **WM[(v, k)]))
        g = w_metr(run_w(k, v, tf, GLAZ))
        OUT.append(dict(oggetto=v + "_glaz30/6", periodo=k, **g))

def units_ratio(base_tr, var_tr):
    """Per ogni trade W3.2 (unità), rapporto fra il composto dei trade della variante entrati nel suo intervallo e il suo."""
    spans = [(pd.Timestamp(t["entry"]), pd.Timestamp(t["exit"]) if t["exit"] != "aperta" else pd.Timestamp("2100-01-01"),
              1 + t["pnl"]) for t in base_tr]
    vp = [1.0] * len(spans); extra = []
    for t in var_tr:
        e = pd.Timestamp(t["entry"]); j = None
        for n_, (a, b, _) in enumerate(spans):
            if a <= e <= b: j = n_; break
        if j is None:
            prev = [n_ for n_, (a, b, _) in enumerate(spans) if a <= e]
            j = prev[-1] if prev else None
        if j is None: extra.append(1 + t["pnl"])
        else: vp[j] *= 1 + t["pnl"]
    rat = [vp[n_] / s[2] for n_, s in enumerate(spans)] + extra
    return np.array(rat)

WNB, WPL, W2B, TOUCH = {}, {}, {}, {}
for v, (kind, tf) in VARW.items():
    base_tr = wb["dal2021"]["trades"]; var_tr = WR[(v, "dal2021")]["trades"]
    rat = units_ratio(base_tr, var_tr)
    W2B[v] = float(np.prod(np.sort(rat)[:-2])) > 1.0  # senza le 2 unità che migliorano di più, ancora meglio di W3.2
    TOUCH[v] = [(base_tr[n_]["entry"], round(float(r_), 3)) for n_, r_ in enumerate(rat[:len(base_tr)]) if abs(r_ - 1) > 1e-9]
    s0 = wbm["dal2021"]["s"]
    grid = [(tf, p, 30) for p in NEIGH] + ([(tf, BASE, w_) for w_ in (15, 45, 60)] if kind == "filter" else [])
    WNB[v] = (sum(w_metr(run_w("dal2021", v, t_, p_, w_))["s"] > s0 for t_, p_, w_ in grid), len(grid))
    sim = WSIM["dal2021"]; tri = tri_for(sim, tf, BASE); t0 = int(sim.idx.searchsorted(pd.Timestamp("2021-01-01")))
    seg = tri[t0:]; N = len(seg); real = WM[(v, "dal2021")]["s"]; cnt = 0
    for _ in range(NPL_W):
        k = int(RNG.integers(60, N - 60)); t2 = tri.copy(); t2[t0:] = np.roll(seg, k)
        cnt += w_metr(run_w("dal2021", v, tri=t2))["s"] >= real
    WPL[v] = cnt / NPL_W
    for t in var_tr:
        OUT_T = dict(variante=v, **{kk: t[kk] for kk in ("signal", "entry", "exit", "side", "reason")}, pnl=round(t["pnl"] * 100, 2))
        TOUCH.setdefault(v + "_list", []).append(OUT_T)

# ------------------------------------------------------------------ Holm su 8
P = {**PS, **WPL}
order = sorted(P, key=P.get); holm = {}; alive = True
for r_, k in enumerate(order):
    thr = 0.05 / (8 - r_)
    alive = alive and P[k] <= thr; holm[k] = (thr, alive)

# ------------------------------------------------------------------ criteri
CR = []
for nm in STRAT:
    m = {k: SM[(nm, k)] for k in ("P1", "P2", "P3")}
    c1 = all(m[k]["finale"] > 10000 for k in m)
    c2 = all((m[k]["s"] if not np.isnan(m[k]["s"]) else -9) > BH[k]["s"] for k in m)
    c3 = all(m[k]["dd"] >= -35 for k in m)
    c4 = all((m[k]["senza2"] if not np.isnan(m[k]["senza2"]) else 0) > 10000 for k in m)
    c5 = SM[(nm, "dal2018")]["trade"] >= 8
    c6 = holm[nm][1]
    c7 = NB[nm] >= 6
    comp = SM[(nm, "dal2021")]["finale"] >= wbm["dal2021"]["finale"] and SM[(nm, "dal2021")]["dd"] >= wbm["dal2021"]["dd"]
    valid = all([c1, c2, c3, c4, c5, c6, c7])
    CR.append(dict(oggetto=nm, finale_gt_10k=c1, S_gt_BH=c2, DD_ge_m35=c3, senza2_gt_10k=c4, trade_ge_8=c5,
                   placebo_p=P[nm], holm_soglia=round(holm[nm][0], 4), holm_ok=c6, vicini_ok=f"{NB[nm]}/8", vicini_pass=c7,
                   competitiva_W32=comp,
                   esito="VALIDA" if valid else ("SU CARTA" if all([c1, c2, c3, c4, c5, c7]) else "NON VALIDA")))
for v in VARW:
    m = {k: WM[(v, k)] for k in ("P1", "P2", "P3")}; b = wbm
    c1 = m["P2"]["s"] > b["P2"]["s"] and m["P3"]["s"] > b["P3"]["s"] and m["P1"]["s"] >= b["P1"]["s"]
    c2 = all(m[k]["dd"] >= b[k]["dd"] - 1 for k in m)
    t, bt = WM[(v, "dal2021")], b["dal2021"]
    c3 = t["finale"] >= bt["finale"] or (t["dd"] >= bt["dd"] + 3 and t["finale"] >= 0.9 * bt["finale"])
    c4 = t["wr"] >= 70
    c5 = W2B[v]
    c6 = WNB[v][0] >= 0.75 * WNB[v][1]
    c7 = holm[v][1]
    ok = all([c1, c2, c3, c4, c5, c6, c7])
    CR.append(dict(oggetto=v, S_per_periodo=c1, DD_entro_1pt=c2, finale_o_DD_dal2021=c3, wr_ge_70=c4, senza2_meglio=c5,
                   vicini_ok=f"{WNB[v][0]}/{WNB[v][1]}", vicini_pass=c6, placebo_p=P[v], holm_soglia=round(holm[v][0], 4),
                   holm_ok=c7, esito="MIGLIORA" if ok else ("SU CARTA" if all([c1, c2, c3, c4, c5, c6]) else "NON MIGLIORA")))
CRd = pd.DataFrame(CR); CRd.to_csv("criteri.csv", index=False)

# ------------------------------------------------------------------ studio d'evento
EV = []; Pe = {}
def event_study(Oa, La, index, sg_by_tf, label):
    n = len(Oa); e0 = int(index.searchsorted(pd.Timestamp("2018-01-01")))
    for tfn, (sgd, closes) in sg_by_tf.items():
        for side, nm in ((1, "nero"), (-1, "rosso")):
            pos = [i for i in np.where(sgd == side)[0] if i >= e0]
            for h in (7, 30, 90):
                valid = [i for i in pos if i + 1 + h < n]
                if not valid: continue
                r = np.array([Oa[i + 1 + h] / Oa[i + 1] - 1 for i in valid])
                allr = np.array([Oa[j + 1 + h] / Oa[j + 1] - 1 for j in range(e0, n - 1 - h)])
                pool = [i for i in closes if e0 <= i < n - 1 - 90]
                pr = np.array([Oa[pool[0] + 1 + h] / Oa[pool[0] + 1] - 1])
                poolr = np.array([Oa[i + 1 + h] / Oa[i + 1] - 1 for i in pool])
                draws = RNG.choice(len(pool), size=(NPL_E, len(valid)), replace=True)
                pm = poolr[draws].mean(axis=1)
                p = float(((pm >= r.mean()) if side > 0 else (pm <= r.mean())).mean())
                row = dict(asset=label, tf=tfn, lato=nm, h=h, n=len(valid), media=round(r.mean() * 100, 2),
                           mediana=round(float(np.median(r)) * 100, 2), quota_pos=round(float((r > 0).mean()) * 100),
                           base_tutti_i_giorni=round(allr.mean() * 100, 2), p_placebo=p)
                if side > 0 and h == 30:
                    lows = [float(np.min(La[i + 1:i + 31]) < La_bar[tfn][i]) for i in valid]
                    row["quota_minimo_piu_basso_30g"] = round(np.mean(lows) * 100)
                EV.append(row)
                if label == "BTC" and tfn in ("1D", "3D"):
                    Pe[(tfn, nm, h)] = p

L = d.low.to_numpy(float)
def bar_lows(tf):
    b = resample_year(d, tf) if tf != 7 else resample(d, 7, 4)
    out = np.full(len(d), np.nan)
    for t in b.index:
        end = t + pd.Timedelta(days=int(b.loc[t, "n"]) - 1) if tf > 1 else t
        if end in d.index: out[d.index.get_loc(end)] = b.loc[t, "low"]
    return out, [i for i in range(len(d)) if not np.isnan(out[i])]
La_bar = {}; sgs = {}
for tf, nm in ((1, "1D"), (3, "3D"), (7, "1W")):
    lows, closes = bar_lows(tf); La_bar[nm] = lows
    if tf == 7:
        b = resample(d, 7, 4); s = lele(b, 10, 40); sw = pd.Series(0, index=d.index)
        for t, v in s[s != 0].items():
            end = t + pd.Timedelta(days=int(b.loc[t, "n"]) - 1)
            if end in sw.index: sw.loc[end] = v
        sgs[nm] = (sw.to_numpy(int), closes)
    else:
        sgs[nm] = (sig(tf, BASE), closes)
event_study(O, L, d.index, sgs, "BTC")
ordE = sorted(Pe, key=Pe.get); holmE = {}; alive = True
for r_, k in enumerate(ordE):
    alive = alive and Pe[k] <= 0.05 / (12 - r_); holmE[k] = alive
for row in EV:
    k = (row["tf"], row["lato"], row["h"])
    row["holm12_ok"] = holmE.get(k, "")

# ------------------------------------------------------------------ ETH (stessi parametri)
eth = pd.read_csv(os.path.join(ROOT, "research/w32_multi/data/ETH_spot_long.csv.gz"), parse_dates=["date"]).set_index("date")
eth = eth[["open", "high", "low", "close"]]
EO, EC, EL = (eth[k].to_numpy(float) for k in ("open", "close", "low"))
EF = funding_series(eth.index, "data/eth_funding.csv").to_numpy(float)
EEND = str(eth.index[-1].date())
EPER = {"P1": ("2018-01-01", "2020-12-31"), "P2": ("2021-01-01", "2023-12-31"), "P3": ("2024-01-01", EEND), "dal2021": ("2021-01-01", EEND)}
esig = daily_signal(eth, 3, *BASE).to_numpy(int)
for nm, mode in (("S1", "long"), ("S2", "ls")):
    for k, (a, b) in EPER.items():
        OUT.append(dict(oggetto="ETH_" + nm, periodo=k, **run_s(esig, mode, a, b, EO, EC, EF, eth.index)))
for k, (a, b) in EPER.items():
    OUT.append(dict(oggetto="ETH_buy&hold", periodo=k, **bh(a, b, EO, EC, eth.index)))
elows = np.full(len(eth), np.nan); eb = resample_year(eth, 3)
for t in eb.index:
    end = t + pd.Timedelta(days=int(eb.loc[t, "n"]) - 1)
    if end in eth.index: elows[eth.index.get_loc(end)] = eb.loc[t, "low"]
La_bar_btc = La_bar; La_bar = {"3D": elows}
event_study(EO, EL, eth.index, {"3D": (esig, [i for i in range(len(eth)) if not np.isnan(elows[i])])}, "ETH")
La_bar = La_bar_btc

# ------------------------------------------------------------------ salvataggi e sintesi
R = pd.DataFrame(OUT); R.to_csv("risultati.csv", index=False)
E = pd.DataFrame(EV); E.to_csv("studio_evento.csv", index=False)
pd.DataFrame(sum([TOUCH.get(v + "_list", []) for v in VARW], [])).to_csv("w32_trade.csv", index=False)
cols = ["finale", "rend", "dd", "s", "mar", "trade", "wr", "senza2"]
for per in ("dal2021", "dal2018", "P1", "P2", "P3", "IS18-22", "OOS23-"):
    say(f"\n## {per}")
    say(R[R.periodo == per].set_index("oggetto")[cols].to_string())
say("\n## Criteri"); say(CRd.T.to_string())
say("\nPlacebo p:", {k: P[k] for k in P}, "\nHolm:", {k: holm[k][1] for k in holm})
say("\nTrade W3.2 toccati (rapporto variante/W3.2 per unità, dal 2021):")
for v in VARW: say(v, TOUCH[v])
say("\n## Studio d'evento"); say(E.to_string(index=False))
open("risultati.txt", "w").write("\n".join(txt) + "\n")
