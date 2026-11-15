"""N2 · swing BTC 2–3 giorni (notte 15/11/2026). Regole e soglie in PREREG.md (scritte prima dei risultati).
Uso: python3 run.py  (dalla cartella research/notte_1511/n2). Output: risultati.txt, configurazioni.csv, vicini.csv, trades.csv.
Legge radar/ solo in lettura (dati, feature, W3)."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/user/radar")
import numpy as np, pandas as pd
from radar import data as rdata, features as rfeat, weekly as rweek

OUT = "/home/user/radar/research/notte_1511/n2/"
D = "/home/user/radar/data/"
START, SPLIT = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
FEE, SLIP, CAP = 0.0008, 0.0005, 10000.0
NPLAC, NTEST = 5000, 32
rng = np.random.default_rng(15112026)

# ---------------- dati
perp = pd.read_csv(D + "perp.csv", index_col=0, parse_dates=True)
spot = pd.read_csv(D + "spot.csv", index_col=0, parse_dates=True)
fund = pd.read_csv(D + "funding.csv", index_col=0, parse_dates=True)["funding"]
met = pd.read_csv(D + "metrics.csv", index_col=0, parse_dates=True)
idx = perp.index.intersection(spot.index)
idx = idx[idx >= "2020-01-01"]
p, s = perp.loc[idx], spot.loc[idx]
O, H, L, C = (p[k].to_numpy(float) for k in ("open", "high", "low", "close"))
FU = fund.reindex(idx).fillna(0).to_numpy(float)
NI = len(idx)
t_start = idx.searchsorted(START)

def z(x, n):
    return (x - x.rolling(n, min_periods=n // 2).mean()) / x.rolling(n, min_periods=n // 2).std()

def rsi(c, n):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)

c = p["close"]
tr = pd.concat([p.high - p.low, (p.high - c.shift()).abs(), (p.low - c.shift()).abs()], axis=1).max(axis=1)
ATR = tr.ewm(alpha=1 / 14, adjust=False).mean()
sd = 2 * s.taker_buy_volume - s.volume                     # delta taker spot del giorno t (noto in tempo reale)
pdl = (2 * p.taker_buy_volume - p.volume).shift(1)         # delta taker perp di t−1 (archivio in ritardo)
ret1 = c.pct_change()
RSI2 = rsi(c, 2)
fz = z(fund.reindex(idx).fillna(0).rolling(3).sum(), 180)
oi = met["oi"].where(met["oi"] > 0).reindex(idx)
ozz = z(oi.pct_change(fill_method=None), 90).shift(1)      # variazione OI di t−1
ssh = z(s.taker_buy_volume / s.volume, 90)

# regime W3 (stesse definizioni di radar/weekly.py) e W3 stesso
f = rfeat.build_features(rdata.load_all())
f = f[f["close"].notna()]
w = rweek.weekly_bars(f)
up = (w.close > w.sma) & (w.ema20 > w.ema20.shift(1))
dn = (w.close < w.sma) & (w.sma < w.sma.shift(4)) & (w.ema20 < w.ema20.shift(1))
REG = pd.Series(np.where(up, 1, np.where(dn, -1, 0)), w.index).reindex(idx, method="ffill").fillna(0)
w3 = rweek.simulate(f)
w3eq = w3["equity"].reindex(idx[t_start:]).ffill()
w3ret = w3eq.pct_change().fillna(0)
W3IN = np.zeros(NI, bool)
for t in w3["trades"] + ([w3["open"]] if w3["open"] else []):
    a = idx.searchsorted(pd.Timestamp(t["entry"])); b = idx.searchsorted(pd.Timestamp(t["exit"])) if t.get("exit") else NI
    W3IN[a:b] = True

# ---------------- regole
def signals(rule, par):
    hi = lambda n: p.high.rolling(n).max().shift(1)
    lo = lambda n: p.low.rolling(n).min().shift(1)
    if rule == "A1":
        lg = (c > hi(par)) & (sd > 0) & (pdl > 0); sh = (c < lo(par)) & (sd < 0) & (pdl < 0)
    elif rule == "A2":
        lg = (c > hi(par)) & (REG == 1); sh = (c < lo(par)) & (REG == -1)
    elif rule == "B1":
        lg = (RSI2 < par) & (REG == 1); sh = (RSI2 > 100 - par) & (REG == -1)
    elif rule == "B2":
        lg = (RSI2 < par) & (REG != 1); sh = (RSI2 > 100 - par) & (REG != -1)
    elif rule == "B3":
        k, wn = par; mv = c - c.shift(wn)
        lg = mv < -k * ATR; sh = mv > k * ATR
    elif rule == "C1":
        lg = fz < -par; sh = fz > par
    elif rule == "C2":
        lg = (ozz > par) & (ret1 > 0) & (sd > 0); sh = (ozz > par) & (ret1 < 0) & (sd < 0)
    elif rule == "C3":
        lg = (ssh > par) & (pdl > 0); sh = (ssh < -par) & (pdl < 0)
    # primo giorno con tutti gli ingredienti disponibili (per il placebo)
    need = {"C2": ozz, "C1": fz, "C3": ssh}.get(rule, ATR)
    fv = max(t_start, int(np.argmax(need.notna().to_numpy())))
    return lg.fillna(False).to_numpy(), sh.fillna(False).to_numpy(), fv

MAIN = {"A1": 10, "A2": 20, "B1": 10, "B2": 10, "B3": (2.5, 3), "C1": 1.5, "C2": 1.5, "C3": 2.0}
NEIGH = {"A1": [7, 15], "A2": [15, 30], "B1": [5, 15], "B2": [5, 15], "B3": [(2.0, 3), (3.0, 3), (2.5, 2), (2.5, 4)],
         "C1": [1.0, 2.0], "C2": [1.0, 2.0], "C3": [1.5, 2.5]}
FAM = {"A1": "a", "A2": "a", "B1": "b", "B2": "b", "B3": "b", "C1": "c", "C2": "c", "C3": "c"}

# ---------------- motore
def trade(i, side, Hh, k, block=None):
    """Segnale alla chiusura di i, ingresso all'apertura di i+1. Ritorna (ret, exit_idx, path {giorno: valore relativo}, motivo)."""
    e = i + 1
    if e + Hh >= NI:
        return None
    pe = O[e] * (1 + SLIP * side); stop = O[e] - side * k * ATR.iat[i]
    path, cf = {}, 0.0
    for j in range(e, e + Hh):
        if block is not None and j > e and block[j]:                 # W3 entra: chiusura forzata all'apertura
            px = O[j] * (1 - SLIP * side); r = side * (px / pe - 1) - FEE - FEE * px / pe - cf
            path[j] = 1 + r; return r, j, path, "w3"
        if (side > 0 and L[j] <= stop) or (side < 0 and H[j] >= stop):
            px = (min(O[j], stop) if side > 0 else max(O[j], stop)) * (1 - SLIP * side)
            cf += side * FU[j]; r = side * (px / pe - 1) - FEE - FEE * px / pe - cf
            path[j] = 1 + r; return r, j, path, "stop"
        cf += side * FU[j]
        path[j] = 1 + side * (C[j] / pe - 1) - FEE - cf
    x = e + Hh
    px = O[x] * (1 - SLIP * side); r = side * (px / pe - 1) - FEE - FEE * px / pe - cf
    path[x] = 1 + r
    return r, x, path, "tempo"

def run(sig, side, Hh, k, fv, block=None):
    eq = np.full(NI, np.nan); val = CAP; nxt = fv; trades = []; i = fv
    eq[:fv] = CAP
    last = fv
    while i < NI:
        if i >= nxt and sig[i] and (block is None or not block[i + 1 if i + 1 < NI else i]):
            t = trade(i, side, Hh, k, block)
            if t is not None:
                r, x, path, why = t
                for j in range(last, i + 1):
                    if np.isnan(eq[j]): eq[j] = val
                for j, v in path.items(): eq[j] = val * v
                trades.append(dict(segnale=idx[i].date(), ingresso=idx[i + 1].date(), uscita=idx[x].date(), motivo=why, ret=r))
                val *= 1 + r; last = x + 1
                nxt = x - 1 if why == "tempo" else x
                i = max(i + 1, nxt); continue
        i += 1
    for j in range(last, NI):
        eq[j] = val
    return pd.Series(eq, idx).iloc[t_start:], trades

def pool(side, Hh, k, fv):
    out = []
    for i in range(fv, NI - Hh - 1):
        t = trade(i, side, Hh, k); out.append(t[0])
    return np.array(out)

POOL = {}

def stats(eq, trades):
    r = np.array([t["ret"] for t in trades]); n = len(r)
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    fin = float(eq.iloc[-1]); cagr = (fin / CAP) ** (1 / yrs) - 1
    dd = float((eq / eq.cummax() - 1).min())
    pf = lambda x: (x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.inf
    ent = np.array([pd.Timestamp(t["ingresso"]) for t in trades]) if n else np.array([])
    ris, roos = (r[ent < SPLIT], r[ent >= SPLIT]) if n else (r, r)
    top5 = CAP * np.prod(1 + np.sort(r)[:-5]) if n > 5 else np.nan
    return dict(finale=round(fin), rend=round((fin / CAP - 1) * 100, 1), dd=round(dd * 100, 1),
                mar=round(cagr / abs(dd), 2) if dd < 0 else np.nan, n=n, n_anno=round(n / yrs, 1),
                wr=round((r > 0).mean() * 100, 1) if n else np.nan, pf=round(pf(r), 2) if n else np.nan,
                medio=round(r.mean() * 100, 2) if n else np.nan,
                n_is=len(ris), pf_is=round(pf(ris), 2) if len(ris) else np.nan, rend_is=round((np.prod(1 + ris) - 1) * 100, 1),
                n_oos=len(roos), pf_oos=round(pf(roos), 2) if len(roos) else np.nan, rend_oos=round((np.prod(1 + roos) - 1) * 100, 1),
                senza_top5=round(top5) if n > 5 else np.nan)

def config(rule, par, side, Hh, k, placebo=False, combo=False):
    lg, sh, fv = signals(rule, par)
    sig = lg if side > 0 else sh
    eq, tr = run(sig, side, Hh, k, fv)
    st = stats(eq, tr)
    if placebo and st["n"]:
        key = (side, Hh, k, fv)
        if key not in POOL: POOL[key] = pool(side, Hh, k, fv)
        pl = rng.choice(POOL[key], size=(NPLAC, st["n"])).mean(axis=1)
        obs = np.mean([t["ret"] for t in tr])
        pv = (np.sum(pl >= obs) + 1) / (NPLAC + 1)
        st["p"] = round(pv, 4); st["p_corr"] = round(min(1, pv * NTEST), 3)
        st["placebo_medio"] = round(POOL[key].mean() * 100, 2)
    if combo:
        dr = eq.pct_change().fillna(0)
        st["corr_w3"] = round(float(dr.corr(w3ret)), 2)
        eqb, trb = run(sig, side, Hh, k, fv, block=W3IN)
        comb = CAP * (1 + w3ret + eqb.pct_change().fillna(0)).cumprod()
        yrs = (comb.index[-1] - comb.index[0]).days / 365.25
        cdd = float((comb / comb.cummax() - 1).min())
        st["w3_comb"] = round(float(comb.iloc[-1])); st["w3_comb_dd"] = round(cdd * 100, 1)
        st["w3_comb_mar"] = round(((comb.iloc[-1] / CAP) ** (1 / yrs) - 1) / abs(cdd), 2); st["n_comb"] = len(trb)
        # placebo della combinazione (informativo): ingressi casuali solo nei giorni in cui W3 è flat per tutta la tenuta
        key = (side, Hh, k, fv)
        if key not in POOL: POOL[key] = pool(side, Hh, k, fv)
        okd = np.array([not W3IN[i + 1:i + Hh + 2].any() for i in range(fv, NI - Hh - 1)])
        pf_ = POOL[key][okd]
        if len(trb):
            obs = np.mean([t["ret"] for t in trb])
            pl = rng.choice(pf_, size=(NPLAC, len(trb))).mean(axis=1)
            st["p_comb"] = round((np.sum(pl >= obs) + 1) / (NPLAC + 1), 3); st["medio_flat_caso"] = round(pf_.mean() * 100, 2)
            st["medio_comb"] = round(obs * 100, 2)
    return st, tr

# ---------------- esecuzione
lines = []
P = lambda *a: lines.append(" ".join(str(x) for x in a))
yrs = (idx[-1] - START).days / 365.25
bh = C[-1] / O[t_start] * CAP
bheq = pd.Series(C[t_start:] / O[t_start] * CAP, idx[t_start:]); bhdd = (bheq / bheq.cummax() - 1).min()
w3fin = float(w3eq.iloc[-1]); w3dd = float((w3eq / w3eq.cummax() - 1).min())
w3mar = ((w3fin / CAP) ** (1 / yrs) - 1) / abs(w3dd)
P(f"Dati {idx[t_start].date()} → {idx[-1].date()} ({yrs:.2f} anni). Buy & hold: {bh:,.0f} $ DD {bhdd*100:.1f}% MAR {((bh/CAP)**(1/yrs)-1)/abs(bhdd):.2f}")
P(f"W3 (radar/weekly.simulate): {w3fin:,.0f} $ DD {w3dd*100:.1f}% MAR {w3mar:.2f}; giorni flat {100*(1-W3IN[t_start:].mean()):.0f}%")

import os
if os.path.exists(OUT + "vicini.csv"): os.remove(OUT + "vicini.csv")
rows, allt = [], []
for rule, par in MAIN.items():
    for side in (1, -1):
        for Hh in (2, 3):
            st, tr = config(rule, par, side, Hh, 1.5, placebo=True, combo=True)
            # vicini
            nb = []
            for q in NEIGH[rule]:
                nb.append(config(rule, q, side, Hh, 1.5)[0])
            for k in (1.0, 2.0):
                nb.append(config(rule, par, side, Hh, k)[0])
            okn = [x for x in nb if x["n"] and x["pf_is"] > 1 and x["pf_oos"] > 1]
            sign = np.sign(st["rend"])
            flip = any(np.sign(x["rend"]) != sign for x in nb if x["n"])
            st["vicini_ok"] = f"{len(okn)}/{len(nb)}" + ("" if not flip else " segno≠")
            stable = len(okn) >= 0.75 * len(nb) and not flip
            c1 = st["rend_oos"] > 0; c2 = st["pf_is"] > 1.2 and st["pf_oos"] > 1.2; c3 = st.get("p_corr", 1) < 0.05
            c5 = st["n_is"] >= 20 and st["n_oos"] >= 20
            st["criteri"] = "".join("x" if b else "." for b in (c1, c2, c3, stable, c5))
            st["accettata"] = all((c1, c2, c3, stable, c5))
            name = f"{rule}{'L' if side > 0 else 'S'}{Hh}"
            rows.append(dict(config=name, famiglia=FAM[rule], regola=rule, lato="long" if side > 0 else "short", H=Hh, **st))
            for t in tr: allt.append(dict(config=name, **t))
            vrows = [dict(config=name, variante=v, **x) for v, x in zip([str(q) for q in NEIGH[rule]] + ["stop1.0", "stop2.0"], nb)]
            pd.DataFrame(vrows).to_csv(OUT + "vicini.csv", mode="a", header=not rows[:-1], index=False)

R = pd.DataFrame(rows)
R.to_csv(OUT + "configurazioni.csv", index=False)
pd.DataFrame(allt).to_csv(OUT + "trades.csv", index=False)
cols = ["config", "finale", "rend", "dd", "mar", "n", "n_anno", "wr", "pf", "medio", "n_is", "pf_is", "rend_is", "n_oos", "pf_oos",
        "rend_oos", "senza_top5", "p", "p_corr", "vicini_ok", "corr_w3", "w3_comb", "w3_comb_dd", "w3_comb_mar", "n_comb", "medio_comb", "medio_flat_caso", "p_comb", "criteri", "accettata"]
pd.set_option("display.width", 250)
P("\nCriteri (ordine): OOS>0 · PF>1,2 entrambe le metà · placebo p_corr<0,05 · vicini stabili · ≥20 trade per metà")
P(R[cols].to_string(index=False))
P("\nAccettate:", ", ".join(R[R.accettata].config) or "nessuna")
P("\nMigliori 6 per MAR (solo descrittivo):")
P(R.sort_values("mar", ascending=False)[cols[:17]].head(6).to_string(index=False))
open(OUT + "risultati.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
