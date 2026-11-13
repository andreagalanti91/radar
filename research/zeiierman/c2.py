"""Ciclo 2 · P1a, P1b, P2a, P2b (long 1D) e P3 (W3 con esposizione ridotta). Regole in PREREG.md, sezione "Ciclo 2".
Uso: python c2.py > risultati_ciclo2.txt"""
import sys, inspect, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
sys.path.insert(0, "/home/user/radar"); sys.path.insert(0, "/home/user/radar/research/zeiierman")
sys.path.insert(0, "/home/user/radar/research/w2_migliorie")
from ztp import ztp, atr, load_daily
from bt import metrics, bh, placebo, top3_removed, FUND, FEE, K_ATR, CAP, PER, D
from radar import weekly as W
from eng import load_repo, load_long

pd.set_option("display.width", 230); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
df = load_daily(); Z0 = ztp(df)
NBZ = [("fl", 18), ("fl", 24), ("sl", 50), ("sl", 60), ("ml", 110), ("ml", 130)]
OUT = []


# ------------------------------------------------------------------------------------------------ segnali P1/P2
def w3_regime_ok(data):
    """Regime settimanale W3 non ribassista sull'ultima settimana W-SUN chiusa (≤ giorno del segnale)."""
    w = data[["close"]].resample("W-SUN").last(); c = w.close
    sma = c.rolling(40).mean(); e20 = c.ewm(span=20, adjust=False).mean()
    dn = (c < sma) & (sma < sma.shift(4)) & (e20 < e20.shift(1))
    s = (~dn).astype(float)
    s[sma.isna()] = np.nan
    # la candela W-SUN chiude la domenica: il valore è noto alla chiusura della domenica stessa
    return s.reindex(data.index, method="ffill").fillna(0).astype(bool).to_numpy()


def sigs(data, z, filt="sma", sma_n=200):
    tz = z.tz.to_numpy(); core = z.core.to_numpy(); p = np.r_[np.nan, tz[:-1]]
    b_rel = (tz > -70) & (p <= -70)
    r_in = (tz >= -30) & ~(p >= -30) & ~np.isnan(p)
    r_rel = (tz < -30) & (p >= -30)
    r3s = (tz < -50) & (core == -1)
    if filt == "sma":
        ok = (data.close > data.close.rolling(sma_n).mean()).to_numpy()
    else:
        ok = w3_regime_ok(data)
    en = b_rel & ok & (core != -1)
    return en, r3s, r_in, r_rel


def sim_p(data, z, rule, start, end, filt="sma", sma_n=200, stop=True):
    """rule: P1 (uscite stop/R3short), P2a (+ rilascio rosso), P2b (50% all'ingresso in rossa, resto al rilascio)."""
    idx = data.index; o, h, l, c = (data[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    A = atr(data, 14); en, r3s, r_in, r_rel = sigs(data, z, filt, sma_n)
    fu = FUND.reindex(idx.normalize()).fillna(0).to_numpy()
    i0 = idx.searchsorted(pd.Timestamp(start)); i1 = idx.searchsorted(pd.Timestamp(end) + pd.Timedelta(days=1)) - 1
    eq = CAP; pos = 0.0; trades = []; curve = np.full(i1 - i0 + 1, np.nan); act = None
    for i in range(i0, i1 + 1):
        if pos and act:
            frac = 1.0 if act[0] == "out" else 0.5
            px = o[i]; nq = notional * frac * (pos)  # nozionale all'ingresso della quota chiusa
            eq += nq * (px / ep - 1) - FEE * nq * px / ep
            pos -= frac * pos if act[0] == "half" else pos
            if act[0] == "half": half_done = True
            if pos <= 1e-9:
                trades.append((idx[ie], idx[i], ep, px, act[1], eq)); pos = 0
        if not pos and act and act[0] == "in":
            ep, ie, pos = o[i], i, 1.0; notional = eq; eq -= FEE * notional
            stp = ep - K_ATR * A[i - 1] if stop else None; seen_red = half_done = False
        act = None
        mtm = eq
        if pos:
            if stop and l[i] <= stp:
                px = min(o[i], stp); nq = notional * pos
                eq += nq * (px / ep - 1) - FEE * nq * px / ep
                trades.append((idx[ie], idx[i], ep, px, "stop", eq)); pos = 0; mtm = eq
            else:
                eq -= notional * pos * (c[i] / ep) * fu[i]
                mtm = eq + notional * pos * (c[i] / ep - 1)
        curve[i - i0] = mtm
        if i == i1: break
        if pos:
            if i > ie - 1 and r_in[i]: seen_red = True
            if r3s[i]: act = ("out", "R3short")
            elif rule in ("P2a", "P2b") and r_rel[i] and i >= ie: act = ("out", "rilascio rosso")
            elif rule == "P2b" and r_in[i] and not half_done and i >= ie: act = ("half", "metà in rossa")
        elif en[i]:
            act = ("in", None)
    if pos:
        px = c[i1]; nq = notional * pos; eq += nq * (px / ep - 1) - FEE * nq * px / ep
        trades.append((idx[ie], idx[i1], ep, px, "fine", eq))
    t = pd.DataFrame(trades, columns=["ingresso", "uscita", "px_in", "px_out", "motivo", "capitale"])
    if len(t):
        prev = np.r_[CAP, t.capitale.to_numpy()[:-1]]; t["pnl_%"] = (t.capitale / prev - 1) * 100
        t["mov_%"] = (t.px_out / t.px_in - 1) * 100
        t["barre"] = [idx.get_loc(b) - idx.get_loc(a) + 1 for a, b in zip(t.ingresso, t.uscita)]
    return t, pd.Series(curve, idx[i0:i1 + 1])


# ------------------------------------------------------------------------------------------------ W3 e P3 (motore radar/weekly.py)
f = load_repo(); fl = load_long(f)
src = inspect.getsource(W.simulate)
src = src.replace("def simulate(f: pd.DataFrame, start: str = START, capital: float = 10000.0, lev: float = 1.0) -> dict:",
                  "def simulate_x(f, start=START, capital=10000.0, lev=1.0, red=None, frac=0.5, end=None, log=None):\n"
                  "    f = f.loc[:end] if end else f")
# P3: aggiustamento della quantità all'apertura (prima dello stop), decisione alla chiusura del giorno prima
src = src.replace("            pend = None\n        if side:\n",
"""            pend = None
        if red is not None and side > 0 and i > 0:
            want = frac if red[i - 1] else 1.0
            if abs(want - tr.get("lvl", 1.0)) > 1e-9:
                px = O[i] * (1 - SLIP) if want < tr.get("lvl", 1.0) else O[i] * (1 + SLIP)
                eqo = cash + qty * px - cost
                tq = want * tr["expo"] * eqo / px
                dq = tq - qty
                if dq < 0:   # vendita: realizza il P&L della parte venduta (contabilità di weekly.simulate)
                    cash += -dq * (px - cost / qty) - abs(dq) * px * frate; cost = cost * tq / qty
                else:
                    cash -= dq * px * frate; cost += dq * px
                qty = tq; tr["lvl"] = want; tr["nadj"] = tr.get("nadj", 0) + 1
        if side:
""")
ns = dict(vars(W)); exec(src, ns); simx = ns["simulate_x"]


def red_state(data, z_kw=None, th=-50):
    z = ztp(data[["open", "high", "low", "close"]], **(z_kw or {}))
    return ((z.tz < th) & (z.core == -1)).to_numpy()


def run_w3(data, start, end=None, red=None, frac=0.5):
    r = simx(data, start=start, end=end, red=red, frac=frac)
    eq = r["equity"]; fin = float(eq.iloc[-1]); dd = float((eq / eq.cummax() - 1).min() * 100)
    tr = [dict(entry=t["entry"], exit=t["exit"], side=t["side"], pnl=round(t["pnl"] * 100, 2), nadj=t.get("nadj", 0)) for t in r["trades"]]
    if r["open"]:
        o = r["open"]; tr.append(dict(entry=o["entry"], exit="aperto", side=o["side"], pnl=round(o["pnl_close"] * 100, 2), nadj=o.get("nadj", 0)))
    return dict(fin=round(fin), dd=round(dd, 1), mar=round((fin / CAP - 1) * 100 / abs(dd), 2), trades=tr, eq=eq)


if __name__ == "__main__":
    END = "2026-11-11"
    fx = f.loc[:END]; flx = fl
    print("== VERIFICA MOTORE W3 (copia di radar/weekly.simulate, opzione P3 spenta)")
    b21 = run_w3(fx, "2021-01-01"); b18 = run_w3(flx, "2018-01-01", "2020-12-31")
    print(f"W3 dal 2021: {b21['fin']:,} DD {b21['dd']}%  (atteso 78.474, −21,1%) | 2018–20: {b18['fin']:,} DD {b18['dd']}% (atteso 25.142, −37,3%)")
    bIS = run_w3(fx, "2021-01-01", "2023-12-31"); bOOS = run_w3(fx, "2024-01-01")
    print(f"W3 IS 2021–23: {bIS['fin']:,} DD {bIS['dd']}% MAR {bIS['mar']} | OOS 2024→: {bOOS['fin']:,} DD {bOOS['dd']}% MAR {bOOS['mar']}")

    # ---------------- P1/P2
    print("\n== P1/P2 (long 1D, 1x, costi e funding, 10k per periodo)")
    rows = []
    bhs = {p: bh(df, s, e) for p, (s, e) in PER.items()}
    for p in PER: rows.append(dict(regola="B&H", periodo=p, finale=bhs[p]["finale"], rend=bhs[p]["rend"], dd=bhs[p]["dd"], mar=bhs[p]["mar"]))
    for p, x in (("tot", b21), ("IS", bIS), ("OOS", bOOS)):
        rows.append(dict(regola="W3", periodo=p, trade=len(x["trades"]), finale=x["fin"], rend=round((x["fin"] / CAP - 1) * 100, 1), dd=x["dd"], mar=x["mar"]))
    CF = {"P1a": ("P1", "sma"), "P1b": ("P1", "w3"), "P2a": ("P2a", "sma"), "P2b": ("P2b", "sma")}
    tl = {}
    for name, (rule, filt) in CF.items():
        for p, (s, e) in PER.items():
            t, cv = sim_p(df, Z0, rule, s, e, filt); m = metrics(t, cv)
            row = dict(regola=name, periodo=p, **m)
            if p == "tot":
                tl[name] = (t, cv)
                row["senza_top3"] = top3_removed(t); row["placebo_p"] = placebo(df, t, 1, s, e, 5000)
                t.to_csv(f"{D}trades/c2_{name}.csv", index=False)
            rows.append(row)
    res = pd.DataFrame(rows); print(res.to_string(index=False))
    res.to_csv(D + "risultati_ciclo2.csv", index=False)

    print("\n== VICINI P1/P2 (finale dal 2021; SMA 150/250 e ZTP fl/sl/ml ±; zn/sn non toccano le regole)")
    zs = {f"{k}={v}": ztp(df, **{k: v}) for k, v in NBZ}
    nrows = []
    for name, (rule, filt) in CF.items():
        fins = {}
        for k, zz in zs.items(): fins[k] = round(sim_p(df, zz, rule, *PER["tot"], filt)[1].iloc[-1])
        if filt == "sma":
            for n in (150, 250): fins[f"SMA{n}"] = round(sim_p(df, Z0, rule, *PER["tot"], filt, n)[1].iloc[-1])
        nrows.append(dict(regola=name, in_profitto=f"{sum(v > CAP for v in fins.values())}/{len(fins)}", mediana=int(np.median(list(fins.values()))), **fins))
    nb = pd.DataFrame(nrows); print(nb.to_string(index=False)); nb.to_csv(D + "vicini_ciclo2.csv", index=False)

    print("\n== P1: esposizione rispetto a W3 (giorni dal 2021)")
    w3e = b21["eq"]; r = simx(fx, start="2021-01-01")
    inw3 = pd.Series(0, index=fx.loc["2021-01-01":].index)
    for t in r["trades"] + ([r["open"]] if r["open"] else []):
        if t["side"] == "long": inw3.loc[t["entry"]:(t.get("exit") or END)] = 1
    for name in ("P1a", "P1b", "P2a"):
        t, _ = tl[name]; inp = pd.Series(0, index=inw3.index)
        for _, x in t.iterrows(): inp.loc[x.ingresso:x.uscita] = 1
        a, b = inp.loc[:END], inw3.loc[:END]
        phi = np.corrcoef(a, b)[0, 1]
        print(f"{name}: in posizione {a.mean()*100:.0f}% dei giorni; W3 long {b.mean()*100:.0f}%; phi {phi:.2f}; "
              f"giorni {name} con W3 long {((a == 1) & (b == 1)).sum() / max(a.sum(), 1) * 100:.0f}%; "
              f"trade {name} che iniziano con W3 già long {sum(inw3.get(x.ingresso, 0) for _, x in t.iterrows())}/{len(t)}")
    for name in ("P1a", "P2a", "P2b"):
        print(f"\n-- trade {name}"); print(tl[name][0].assign(**{"pnl_%": lambda d: d["pnl_%"].round(1), "mov_%": lambda d: d["mov_%"].round(1)}).to_string(index=False))

    # ---------------- P3
    print("\n== P3: W3 con esposizione 50% mentre tz < −50 e Core rosso (solo long)")
    RS, RL = red_state(fx), red_state(flx)
    prow = []
    def p3row(name, rs21, rs18, frac=0.5):
        a = run_w3(fx, "2021-01-01", red=rs21, frac=frac); i_ = run_w3(fx, "2021-01-01", "2023-12-31", red=rs21, frac=frac)
        o_ = run_w3(fx, "2024-01-01", red=rs21, frac=frac); l_ = run_w3(flx, "2018-01-01", "2020-12-31", red=rs18, frac=frac)
        return dict(regola=name, fin_21=a["fin"], dd_21=a["dd"], mar_21=a["mar"], mar_IS=i_["mar"], fin_IS=i_["fin"], mar_OOS=o_["mar"], fin_OOS=o_["fin"],
                    fin_1820=l_["fin"], dd_1820=l_["dd"], mar_1820=l_["mar"]), a, l_
    base_row = dict(regola="W3", fin_21=b21["fin"], dd_21=b21["dd"], mar_21=b21["mar"], mar_IS=bIS["mar"], fin_IS=bIS["fin"], mar_OOS=bOOS["mar"],
                    fin_OOS=bOOS["fin"], fin_1820=b18["fin"], dd_1820=b18["dd"], mar_1820=b18["mar"])
    prow.append(base_row)
    r0, p3a, p3l = p3row("P3 (tz<−50, 50%)", RS, RL); prow.append(r0)
    for th in (-45, -55):
        prow.append(p3row(f"vicino tz<{th}", red_state(fx, th=th), red_state(flx, th=th))[0])
    for fr in (0.25, 0.75):
        prow.append(p3row(f"sensibilità {int(fr*100)}%", RS, RL, fr)[0])
    for k, v in NBZ:
        prow.append(p3row(f"vicino {k}={v}", red_state(fx, {k: v}), red_state(flx, {k: v}))[0])
    p3 = pd.DataFrame(prow); print(p3.to_string(index=False)); p3.to_csv(D + "p3_ciclo2.csv", index=False)

    print("\n-- trade W3 modificati da P3 (P&L sul capitale, %)")
    tw = []
    for per, base, mod in (("2021→", b21, p3a), ("2018–20", b18, p3l)):
        for x, y in zip(base["trades"], mod["trades"]):
            assert x["entry"] == y["entry"]
            tw.append(dict(periodo=per, ingresso=x["entry"], uscita=x["exit"], lato=x["side"], W3=x["pnl"], P3=y["pnl"],
                           delta=round(y["pnl"] - x["pnl"], 2), cambi_esposizione=y["nadj"]))
    tw = pd.DataFrame(tw); print(tw.to_string(index=False)); tw.to_csv(D + "p3_trade_ciclo2.csv", index=False)
    t21 = tw[tw.periodo == "2021→"].sort_values("W3", ascending=False).head(3)
    print(f"3 trade migliori W3 dal 2021: P&L W3 {t21.W3.sum():.1f} → P3 {t21.P3.sum():.1f} ({(t21.P3.sum()/t21.W3.sum()-1)*100:+.1f}%); "
          f"per trade: {', '.join(f'{a} {(p/w-1)*100:+.1f}%' for a, w, p in zip(t21.ingresso, t21.W3, t21.P3))}")

    print("\n-- placebo P3: stato ridotto spostato in modo circolare (offset ≥ 60 g), 2000 spostamenti, metro MAR dal 2021")
    rng = np.random.default_rng(11); n = len(RS); real = r0["mar_21"]; cnt = 0; N = 2000; mars = []
    for _ in range(N):
        k = int(rng.integers(60, n - 60)); m = run_w3(fx, "2021-01-01", red=np.roll(RS, k))["mar"]; mars.append(m); cnt += m >= real
    print(f"MAR reale {real}; placebo mediana {np.median(mars):.2f}, 90° pct {np.percentile(mars, 90):.2f}; p = {(1 + cnt) / (N + 1):.4f}")
