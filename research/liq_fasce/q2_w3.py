"""Domanda 2 (PREREG.md): ingresso di W3 con limit sulla fascia di liquidazioni long (R1), sulla confluenza fascia+supporto (R2),
presa parziale di metà sulla fascia di short sopra (R3); placebo (a) su tutti i giorni e (b) sui long W3.
Uso: python research/liq_fasce/q2_w3.py → risultati_q2.txt, q2_trades.csv, q2_varianti.csv, q2_giorni.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
from lf_data import daily_maps, hourly  # noqa: E402
from radar import levels, liqmap, weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

FEE_LMT, THRU = 0.0008, 0.0005
f = build_features(load_all()); f = f[f["close"].notna()]
h = hourly()
Z = daily_maps(h)
HO, HH, HL = h["open"], h["high"], h["low"]
_lv = {}


def supports(day):
    if day not in _lv:
        _lv[day] = levels.compute(f[f.index < day])
    return _lv[day]


def pick_long(day, sig=0.30, conf=False, stop0=None):
    if day not in Z.index:
        return None
    for c in Z.at[day, "dn"]:
        if c["rel"] < sig or (stop0 is not None and c["price"] <= stop0):
            continue
        if conf and not (liqmap.confluence(c, supports(day)) or "").startswith("S"):
            continue
        return c["price"]
    return None


def first_fill(t0, t1, L, side=+1):
    """Prima ora in [t0, t1) in cui il prezzo passa oltre L (buy: sotto; sell: sopra). Ritorna (ora, prezzo) o None."""
    if side > 0:
        lo = HL[(HL.index >= t0) & (HL.index < t1)]
        k = lo[lo <= L * (1 - THRU)]
        if len(k):
            t = k.index[0]; return t, min(float(HO[t]), L)
    else:
        hi = HH[(HH.index >= t0) & (HH.index < t1)]
        k = hi[hi >= L * (1 + THRU)]
        if len(k):
            t = k.index[0]; return t, max(float(HO[t]), L)
    return None


def sim(ff, start="2021-01-01", entry=None, partial=None, N=3, capital=10000.0):
    """Copia di radar/weekly.simulate (solo long a 1x come W3; short invariati) con due ganci:
    entry(day, wk) → livello limit (None = a mercato come W3), partial(day) → livello di vendita di metà."""
    w = W.weekly_bars(ff); idx = ff.index
    O, H_, L_, C = (ff[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = ff["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    lim = None   # ordine limit in attesa: dict(L, exp_i, wk, sig_day, n0)

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1, move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr); tr, qty, cost, side = None, 0.0, 0.0, 0

    def open_pos(sd, wk, px, fee, i, sig_day, how):
        nonlocal cash, qty, cost, side, tr, frate, fperp
        side = sd
        lt = W.exposure(side, wk["close"], wk["atr"], 1.0)
        fs = 1.0 if side > 0 else 0.0
        frate = fee if side > 0 else W.FEE_PERP
        fperp = 1 - fs
        q = side * lt * cash / px
        qty, cost = q, q * px
        cash -= abs(q) * px * frate
        tr = dict(signal=str(sig_day.date()), entry=str(idx[i].date()), side="long" if side > 0 else "short", entry_px=round(px, 2),
                  expo=round(lt, 3), eq0=cash + abs(q) * px * frate, stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]),
                  best=px if how != "market" else O[i], curatr=float(wk["atr"]), how=how, half=False)
        tr["stop"] = tr["stop0"]
        frate = W.FEE_SPOT if side > 0 else W.FEE_PERP   # l'uscita a mercato paga i costi del motore

    for i in range(t0, len(idx)):
        day = idx[i]
        filled_today = None
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side and lim is None:
                sd, wk = pend[1], pend[2]
                L = entry(day, wk) if (entry and sd > 0) else None
                if L is None:
                    open_pos(sd, wk, O[i] * (1 + W.SLIP * sd), W.FEE_SPOT if sd > 0 else W.FEE_PERP, i, pend[3], "market")
                else:
                    lim = dict(L=L, t0=day, exp=day + pd.Timedelta(days=N), wk=wk, sig=pend[3])
            pend = None
        if lim is not None and not side:
            if day >= lim["exp"]:
                open_pos(1, lim["wk"], O[i] * (1 + W.SLIP), W.FEE_SPOT, i, lim["sig"], "scadenza"); lim = None
            else:
                r = first_fill(max(day, lim["t0"]), day + pd.Timedelta(days=1), lim["L"], +1)
                if r:
                    open_pos(1, lim["wk"], r[1], FEE_LMT, i, lim["sig"], "limit"); filled_today = r[0]; lim = None
        if side:
            if side > 0 and partial and not tr["half"] and filled_today is None and day > pd.Timestamp(tr["entry"]):
                Lp = partial(day)
                if Lp:
                    r = first_fill(day, day + pd.Timedelta(days=1), Lp, -1)
                    if r:
                        q2 = qty / 2
                        cash += q2 * r[1] - cost / 2 - q2 * r[1] * FEE_LMT
                        qty -= q2; cost /= 2; tr["half"] = str(day.date()); tr["half_px"] = round(r[1], 0)
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            lo_i = float(HL[(HL.index > filled_today) & (HL.index < day + pd.Timedelta(days=1))].min()) if filled_today is not None else L_[i]
            if (side > 0 and lo_i <= stop) or (side < 0 and H_[i] >= stop):
                px = (min(O[i], stop) if side > 0 and filled_today is None else stop if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            if lim is not None and W._decide(wk, 1) is not None:     # W3 sarebbe già uscita: limit annullato, trade perso
                trades.append(dict(signal=str(lim["sig"].date()), entry=None, side="long", how="perso", pnl=0.0)); lim = None
            d = W._decide(wk, side)
            pend = d + (wk, day) if (d and lim is None) else None
    e = pd.Series(eq[t0:], idx[t0:]) * capital
    if side:
        i = len(idx) - 1
        trades.append(dict(tr, exit=None, reason="open", pnl=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1))
    return trades, e


def stats(trades, e):
    e1 = e / e.iloc[0]
    tot, dd = float(e1.iloc[-1] - 1), float((e1 / e1.cummax() - 1).min())
    tr = [t for t in trades if t.get("entry")]
    pn = np.array([t["pnl"] for t in tr])
    return dict(finale=round(float(e.iloc[-1])), rend=round(tot * 100, 1), dd=round(dd * 100, 1), trade=len(tr), wr=round(float((pn > 0).mean() * 100), 1),
                mar=round(tot / abs(dd), 2), persi=sum(t.get("how") == "perso" for t in trades))


def entry_rule(sig=0.30, conf=False, N=3, dist=None):
    def fn(day, wk):
        st0 = float(wk["close"] - W.STOP_K * wk["atr"])
        if dist is not None:
            p = float(Z.at[day, "price"]) if day in Z.index else None
            d = dist(day)
            return p * (1 - d) if p and d is not None and p * (1 - d) > st0 else None
        return pick_long(day, sig, conf, st0)
    fn.N = N
    return fn


def partial_rule(sig=0.30):
    def fn(day):
        if day not in Z.index:
            return None
        for c in Z.at[day, "up"]:
            if c["rel"] >= sig:
                return c["price"]
        return None
    return fn


def bh(ff, start):
    c = ff["close"][ff.index >= start]
    e = c / c.iloc[0] * 10000 * (1 - 0.002)
    return dict(finale=round(float(e.iloc[-1])), rend=round((e.iloc[-1] / 10000 - 1) * 100, 1), dd=round(float((e / e.cummax() - 1).min() * 100), 1),
                trade=1, wr=None, mar=round((e.iloc[-1] / 10000 - 1) / abs(float((e / e.cummax() - 1).min())), 2), persi=0)


def no_best(trades, e):
    """Capitale finale senza il trade migliore: capitale / (1 + pnl del migliore)."""
    pn = [t["pnl"] for t in trades if t.get("entry")]
    return round(float(e.iloc[-1]) / (1 + max(pn)))


if __name__ == "__main__":
    out = []
    P = lambda s="": out.append(str(s)) or print(s)
    IS = f[f.index <= "2023-12-31"]
    PER = {"2021→": (f, "2021-01-01"), "2021–23": (IS, "2021-01-01"), "2024→": (f, "2024-01-01")}
    VAR = {"W3": dict(), "R1 fascia N3": dict(entry=entry_rule()), "R1 N1": dict(entry=entry_rule(), N=1), "R1 N7": dict(entry=entry_rule(), N=7),
           "R1 sig0.2": dict(entry=entry_rule(sig=0.2)), "R1 sig0.5": dict(entry=entry_rule(sig=0.5)),
           "R2 confluenza N3": dict(entry=entry_rule(conf=True)), "R3 metà su fascia short": dict(partial=partial_rule()),
           "R3 sig0.5": dict(partial=partial_rule(0.5))}
    rows, TR = [], {}
    for name, kw in VAR.items():
        for per, (ff, st) in PER.items():
            tr, e = sim(ff, st, **kw)
            s = stats(tr, e); s.update(variante=name, periodo=per, senza_migliore=no_best(tr, e)); rows.append(s)
            if per == "2021→":
                TR[name] = tr
    for per, (ff, st) in PER.items():
        s = bh(ff, st); s.update(variante="Buy & hold", periodo=per, senza_migliore=None); rows.append(s)
    V = pd.DataFrame(rows)[["variante", "periodo", "finale", "rend", "dd", "mar", "trade", "wr", "persi", "senza_migliore"]]
    V.to_csv(HERE / "q2_varianti.csv", index=False)
    P("== Domanda 2 · W3 con ingresso limit sulle fasce / presa parziale (10k, 1x, costi inclusi)")
    P(V.to_string(index=False))
    # dettaglio dei long
    rows = []
    base = {t["signal"]: t for t in TR["W3"] if t["side"] == "long"}
    for name in ("R1 fascia N3", "R2 confluenza N3", "R3 metà su fascia short"):
        for t in TR[name]:
            if t["side"] != "long":
                continue
            b = base.get(t["signal"], {})
            rows.append(dict(variante=name, segnale=t["signal"], ingresso=t.get("entry"), come=t.get("how"), prezzo=t.get("entry_px"),
                             prezzo_W3=b.get("entry_px"), diff_prezzo_pct=round((t["entry_px"] / b["entry_px"] - 1) * 100, 2) if t.get("entry_px") and b else None,
                             metà=t.get("half"), prezzo_metà=t.get("half_px"), pnl_pct=round(t["pnl"] * 100, 2), pnl_W3_pct=round(b.get("pnl", np.nan) * 100, 2)))
    D = pd.DataFrame(rows); D.to_csv(HERE / "q2_trades.csv", index=False)
    P("\nLong W3 per variante (prezzo d'ingresso contro W3 a mercato):")
    P(D.to_string(index=False))
    for name in ("R1 fascia N3", "R2 confluenza N3"):
        d = D[D.variante == name]
        P(f"  {name}: riempiti {int((d.come == 'limit').sum())}/{len(d)}, a scadenza {int((d.come == 'scadenza').sum())}, a mercato {int((d.come == 'market').sum())}, "
          f"persi {int((d.come == 'perso').sum())}; prezzo medio contro W3 {d.diff_prezzo_pct.mean():+.2f}%")

    # placebo (a): tutti i giorni, vantaggio d'ingresso del limit sulla fascia contro distanze di altri giorni
    P("\n== Placebo (a): ogni giorno 2021–2026, limit 3 giorni sulla prima fascia densa long sotto contro mercato (costi inclusi)")
    days = [d for d in Z.index if d + pd.Timedelta(days=3) <= h.index[-1]]
    dist, P0, P3 = {}, {}, {}
    for d in days:
        c = next((c for c in Z.at[d, "dn"] if c["rel"] >= 0.30), None)
        if c and d in HO.index and d + pd.Timedelta(days=3) in HO.index:
            dist[d] = 1 - c["price"] / float(HO[d]); P0[d] = float(HO[d]); P3[d] = float(HO[d + pd.Timedelta(days=3)])
    dd_ = pd.Series(dist)
    dd_ = dd_[dd_ > 0]
    lows = {d: HL[(HL.index >= d) & (HL.index < d + pd.Timedelta(days=3))] for d in dd_.index}
    opens = {d: HO[(HO.index >= d) & (HO.index < d + pd.Timedelta(days=3))] for d in dd_.index}

    def adv(d, x):
        L = P0[d] * (1 - x)
        lo, op = lows[d].to_numpy(), opens[d].to_numpy()
        k = np.flatnonzero(lo <= L * (1 - THRU))
        ex = (min(op[k[0]], L) * (1 + FEE_LMT)) if len(k) else P3[d] * 1.002
        return P0[d] * 1.002 / ex - 1, bool(len(k))
    R = pd.DataFrame([dict(d=d, dist=x, **dict(zip(("adv", "fill"), adv(d, x)))) for d, x in dd_.items()]).set_index("d")
    R["fw28"] = [float(h["close"].asof(d + pd.Timedelta(days=28))) / P0[d] - 1 for d in R.index]
    R.to_csv(HERE / "q2_giorni.csv")
    rng = np.random.default_rng(11)
    for lab, sub in (("tutti", R), ("2021–23", R[R.index < "2024-01-01"]), ("2024→", R[R.index >= "2024-01-01"])):
        obs = sub["adv"].mean()
        pl = []
        dl = sub["dist"].to_numpy()
        for _ in range(300):
            sh = rng.permutation(dl)
            pl.append(np.mean([adv(d, x)[0] for d, x in zip(sub.index, sh)]))
        pl = np.array(pl)
        P(f"  {lab}: n {len(sub)}, distanza mediana {sub.dist.median()*100:.2f}%, riempiti {sub.fill.mean():.1%}, vantaggio medio {obs*100:+.3f}% "
          f"(placebo {pl.mean()*100:+.3f}%, percentile {(pl < obs).mean()*100:.0f}°)")
    # vantaggio condizionato: riempiti contro non riempiti (selezione avversa)
    P(f"  riempiti: vantaggio {R[R.fill].adv.mean()*100:+.2f}%, non riempiti {R[~R.fill].adv.mean()*100:+.2f}% (comprano dopo un rialzo)")

    # placebo (b): long W3 con distanze casuali dalla stessa distribuzione
    P("\n== Placebo (b): R1 con distanze casuali (stessa distribuzione delle fasce), 300 estrazioni, 2021→")
    dvals = dd_.to_numpy()
    fin = []
    for j in range(300):
        draws = {}
        r2 = np.random.default_rng(100 + j)
        def dist_fn(day, _d=draws, _r=r2):
            if day not in _d:
                _d[day] = float(_r.choice(dvals))
            return _d[day]
        tr, e = sim(f, "2021-01-01", entry=entry_rule(dist=dist_fn))
        fin.append(float(e.iloc[-1]))
    fin = np.array(fin)
    r1 = V[(V.variante == "R1 fascia N3") & (V.periodo == "2021→")].finale.iloc[0]
    P(f"  capitale con distanze casuali: mediana {np.median(fin):,.0f}, 5°–95° {np.percentile(fin,5):,.0f}–{np.percentile(fin,95):,.0f}; R1 {r1:,.0f} = {(fin < r1).mean()*100:.0f}° percentile; W3 78.474 = {(fin < 78474).mean()*100:.0f}°")
    # R3 placebo interno: metà venduta in un giorno casuale del trade allo stesso numero di tagli
    P("\n== Placebo R3: metà venduta a un livello casuale sopra (distanze delle fasce short), 300 estrazioni")
    up_d = np.array([c["dist_pct"] / 100 for d in Z.index for c in Z.at[d, "up"][:1]])
    fin = []
    for j in range(300):
        r3 = np.random.default_rng(500 + j)
        def pr(day, _r=r3):
            return float(Z.at[day, "price"]) * (1 + float(_r.choice(up_d))) if day in Z.index else None
        tr, e = sim(f, "2021-01-01", partial=pr)
        fin.append(float(e.iloc[-1]))
    fin = np.array(fin)
    r3v = V[(V.variante == "R3 metà su fascia short") & (V.periodo == "2021→")].finale.iloc[0]
    P(f"  capitale: mediana {np.median(fin):,.0f}, 5°–95° {np.percentile(fin,5):,.0f}–{np.percentile(fin,95):,.0f}; R3 {r3v:,.0f} = {(fin < r3v).mean()*100:.0f}° percentile")
    (HERE / "risultati_q2.txt").write_text("\n".join(out) + "\n")
