"""Esegue PREREG.md (commit 32bcbba). Output: risultati.txt, eventi.csv, vicini.csv, varianti.csv, trade_delta.csv, hold.csv.
Uso: python3 fg_run.py"""
from __future__ import annotations

import itertools
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research" / "swing_sr"))
import fg_lib as G  # noqa: E402
import fg_engine as E  # noqa: E402
import sw_engine as S  # noqa: E402
from radar import weekly as W  # noqa: E402

SEED, NPERM, NPLA, D0 = 20261123, 5000, 500, 0.5
HS = (3, 7, 14)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


# ---------------------------------------------------------------- test evento
def fwd(f: pd.DataFrame) -> pd.DataFrame:
    c = f["close"]
    return pd.DataFrame({h: c.shift(-h) / c - 1 for h in HS})


def ev_days(s: pd.DataFrame, n: int, x: float, side: int) -> list:
    return G.first_days((s[f"up{n}"] >= x) if side > 0 else (s[f"dn{n}"] <= -x))


def perm_diff(val: np.ndarray, lab: np.ndarray, yr: np.ndarray, a: str, b: str, rng) -> tuple[float, float]:
    ok = ~np.isnan(val)
    val, lab, yr = val[ok], lab[ok], yr[ok]
    if (lab == a).sum() < 2 or (lab == b).sum() < 2:
        return np.nan, np.nan
    obs = val[lab == a].mean() - val[lab == b].mean()
    cnt = 0
    groups = [np.where(yr == y)[0] for y in np.unique(yr)]
    for _ in range(NPERM):
        l2 = lab.copy()
        for g in groups:
            l2[g] = lab[rng.permutation(g)]
        if (l2 == a).sum() == 0 or (l2 == b).sum() == 0:
            continue
        d = val[l2 == a].mean() - val[l2 == b].mean()
        cnt += abs(d) >= abs(obs) - 1e-12
    return float(obs), cnt / NPERM


def shift_p(r: np.ndarray, mask: np.ndarray, rng) -> tuple[float, float]:
    """Eccesso sulla media incondizionata e p (spostamento circolare della serie degli eventi)."""
    base = np.nanmean(r)
    obs = np.nanmean(r[mask]) - base
    n = len(r)
    ks = rng.integers(30, n - 30, size=NPERM)
    pl = np.array([np.nanmean(r[np.roll(mask, k)]) - base for k in ks])
    return float(obs), float((np.abs(pl) >= abs(obs) - 1e-12).mean())


def event_study(name: str, f0: pd.DataFrame, rows: list, neigh: list) -> dict:
    rng = np.random.default_rng(SEED)
    f = G.add_flows(f0)
    s = f[f.index >= G.START]
    fw = fwd(f).reindex(s.index)
    base = {h: float(fw[h].mean()) for h in HS}
    say(f"\n=== TEST EVENTO · {name} · {s.index[0].date()} → {s.index[-1].date()} · media incondizionata "
        + " ".join(f"{h}g {100 * base[h]:+.2f}%" for h in HS))
    h1 = s.index < pd.Timestamp(G.SPLIT)
    pv = {}

    def block(tag, days, lab, sign, pairs, prim=None):
        """days: eventi; lab: classe; sign: ±1 per evento (rendimento nel verso)."""
        days = pd.DatetimeIndex(days)
        lab, sign = np.asarray(lab), np.asarray(sign, float)
        yr = days.year.to_numpy()
        for c in ("perp", "spot", "misto"):
            m = lab == c
            row = dict(asset=name, test=tag, classe=c, n=int(m.sum()), n1=int((m & (days < G.SPLIT)).sum()))
            for h in HS:
                v = fw[h].reindex(days).to_numpy() * sign
                row[f"r{h}"] = round(100 * np.nanmean(v[m]), 2) if m.any() else np.nan
                row[f"ecc{h}"] = round(100 * (np.nanmean(v[m]) - (base[h] if (sign > 0).all() else 0.0)), 2) if m.any() else np.nan
            v7 = fw[7].reindex(days).to_numpy() * sign
            row["r7_m1"] = round(100 * np.nanmean(v7[m & (days < G.SPLIT)]), 2) if (m & (days < G.SPLIT)).any() else np.nan
            row["r7_m2"] = round(100 * np.nanmean(v7[m & (days >= G.SPLIT)]), 2) if (m & (days >= G.SPLIT)).any() else np.nan
            if (sign > 0).all() or (sign < 0).all():   # contro la media incondizionata (solo eventi a verso unico)
                mask = s.index.isin(days[m])
                e7, p7 = shift_p(fw[7].to_numpy(), mask, rng)
                row["ecc7_vs_media"], row["p_shift7"] = round(100 * e7, 2), round(p7, 4)
            rows.append(row)
        for a, b, key in pairs:
            res = {}
            for h in HS:
                v = fw[h].reindex(days).to_numpy() * sign
                res[h] = perm_diff(v, lab, yr, a, b, rng)
            v7 = fw[7].reindex(days).to_numpy() * sign
            m1, m2 = days < G.SPLIT, days >= G.SPLIT
            d1 = np.nanmean(v7[m1 & (lab == a)]) - np.nanmean(v7[m1 & (lab == b)])
            d2 = np.nanmean(v7[m2 & (lab == a)]) - np.nanmean(v7[m2 & (lab == b)])
            say(f"{tag}: {a} − {b}: " + " · ".join(f"{h}g {100 * res[h][0]:+.2f} pp (p {res[h][1]:.3f})" for h in HS)
                + f" · 7g metà 1 {100 * d1:+.2f} / metà 2 {100 * d2:+.2f} · n {int((lab == a).sum())}/{int((lab == b).sum())}")
            if key:
                pv[key] = dict(eff=100 * res[7][0], p=res[7][1], m1=100 * d1, m2=100 * d2, na=int((lab == a).sum()), nb=int((lab == b).sum()))

    # H1/H2 primario
    for side, lab_s, key in ((1, "rialzo", "T1"), (-1, "ribasso", "T2")):
        days = ev_days(s, 3, 0.05, side)
        lab = G.klass(f, 3, side, D0).reindex(days).to_numpy()
        block(f"{lab_s} N3 X5%", days, lab, np.ones(len(days)), [("perp", "spot", key)])
    # T3: rialzi "spot" contro la media
    r3 = [r for r in rows if r["asset"] == name and r["test"] == "rialzo N3 X5%" and r["classe"] == "spot"][0]
    days = pd.DatetimeIndex(ev_days(s, 3, 0.05, 1))
    lab = G.klass(f, 3, 1, D0).reindex(days).to_numpy()
    v7 = fw[7].reindex(days).to_numpy()
    sp = lab == "spot"
    pv["T3"] = dict(eff=r3["ecc7_vs_media"], p=r3["p_shift7"], m1=100 * (np.nanmean(v7[sp & (days < G.SPLIT)]) - float(fw[7][h1].mean())),
                    m2=100 * (np.nanmean(v7[sp & (days >= G.SPLIT)]) - float(fw[7][~h1].mean())), na=int(sp.sum()), nb=len(s))
    say(f"T3 rialzi 'spot' − media: 7g {pv['T3']['eff']:+.2f} pp (p {pv['T3']['p']:.3f}) · metà 1 {pv['T3']['m1']:+.2f} / metà 2 {pv['T3']['m2']:+.2f}")
    # H3 livello 20 giorni (e 10 descrittivo)
    for L, key in ((20, "T4"), (10, None)):
        dd, ll, sg = [], [], []
        for side in (1, -1):
            d = G.first_days((s["close"] > s[f"hi{L}"]) if side > 0 else (s["close"] < s[f"lo{L}"]))
            dd += d
            ll += list(G.klass(f, 3, side, D0).reindex(d).to_numpy())
            sg += [side] * len(d)
        o = np.argsort(pd.DatetimeIndex(dd))
        block(f"rottura {L}g (su+giù, nel verso)", [dd[i] for i in o], [ll[i] for i in o], [sg[i] for i in o], [("spot", "perp", key)])
        if L == 20:   # descrittivo per verso + conferma semplice
            for side, lb in ((1, "su"), (-1, "giù")):
                d = pd.DatetimeIndex([dd[i] for i in o if sg[i] == side])
                conf = (s.loc[d, "sz3"] * side > 0).to_numpy()
                v = fw[7].reindex(d).to_numpy() * side
                say(f"  rottura 20g {lb}: con spot (sz3 nel verso) n {int(conf.sum())} 7g {100 * np.nanmean(v[conf]):+.2f}% · senza n {int((~conf).sum())} "
                    f"7g {100 * np.nanmean(v[~conf]):+.2f}% (rendimento nel verso)")
    # H3 livello swing settimanale
    sg0 = S.signals(f0)
    idx0 = sg0["idx"]
    dd, ll, sg = [], [], []
    for side in (1, -1):
        cond = pd.Series(sg0["sig"][("X", side)], index=idx0)
        d = G.first_days(cond[cond.index >= G.START])
        dd += d
        ll += list(G.klass(f, 3, side, D0).reindex(d).to_numpy())
        sg += [side] * len(d)
    o = np.argsort(pd.DatetimeIndex(dd))
    block("rottura swing settimanale (su+giù, nel verso)", [dd[i] for i in o], [ll[i] for i in o], [sg[i] for i in o], [("spot", "perp", "T5")])
    # vicini
    for nm, n, x, d0, mode in (("N2 X5%", 2, 0.05, D0, "z"), ("N5 X5%", 5, 0.05, D0, "z"), ("N3 X4%", 3, 0.04, D0, "z"),
                               ("N3 X6%", 3, 0.06, D0, "z"), ("N3 X5% D0=1", 3, 0.05, 1.0, "z"), ("N3 X5% dollari", 3, 0.05, D0, "t")):
        for side, lb in ((1, "rialzo"), (-1, "ribasso")):
            days = pd.DatetimeIndex(ev_days(s, n, x, side))
            lab = (G.klass(f, n, side, d0) if mode == "z" else G.klass_trader(f, n, side)).reindex(days).to_numpy()
            v = fw[7].reindex(days).to_numpy()
            pm, sm = lab == "perp", lab == "spot"
            neigh.append(dict(asset=name, vicino=nm, lato=lb, n_perp=int(pm.sum()), n_spot=int(sm.sum()),
                              perp7=round(100 * np.nanmean(v[pm]), 2), spot7=round(100 * np.nanmean(v[sm]), 2),
                              diff7=round(100 * (np.nanmean(v[pm]) - np.nanmean(v[sm])), 2),
                              spot_ecc7=round(100 * (np.nanmean(v[sm]) - base[7]), 2)))
    return pv


# ---------------------------------------------------------------- varianti W3.2
def arrays(f0: pd.DataFrame) -> dict:
    x = f0[f0["close"].notna()]
    f = G.add_flows(x)
    n = len(f)
    C = f["close"].to_numpy(float)
    A = {}
    for k in (1, 3):
        pz, sz = f[f"pz{k}"].to_numpy(float), f[f"sz{k}"].to_numpy(float)
        A[f"agree{k}"] = ((pz > 0) & (sz > 0), (pz < 0) & (sz < 0))
        A[f"nd{k}"] = np.isnan(pz) | np.isnan(sz)
    ks, kb = G.klass(f, 3, -1, D0).to_numpy(), G.klass(f, 3, 1, D0).to_numpy()   # vendite / acquisti
    sz3 = f["sz3"].to_numpy(float)
    for L in (10, 20):
        dn, up = C < f[f"lo{L}"].to_numpy(float), C > f[f"hi{L}"].to_numpy(float)
        A[f"spot{L}"] = (dn & (ks == "spot"), up & (kb == "spot"))
        A[f"con{L}"] = (dn & (sz3 < 0) & (ks != "perp"), up & (sz3 > 0) & (kb != "perp"))
        A[f"any{L}"] = (dn, up)
    sg = S.signals(x)
    sup, res = np.full(n, np.nan), np.full(n, np.nan)
    for t in range(n):
        a = sg["act"][t]
        b, ab = a[a < C[t]], a[a > C[t]]
        if len(b) and b[-1] >= C[t] * 0.94:
            sup[t] = b[-1]
        if len(ab) and ab[0] <= C[t] * 1.06:
            res[t] = ab[0]
    A["level"] = (sup, res)
    return A


def variants(A: dict) -> dict:
    return {
        "E-in1 flusso 1g, K3": dict(ein=dict(agree=A["agree1"], nd=A["nd1"], K=3)),
        "E-in2 flusso 1g, K5": dict(ein=dict(agree=A["agree1"], nd=A["nd1"], K=5)),
        "E-in3 flusso 3g, K5": dict(ein=dict(agree=A["agree3"], nd=A["nd3"], K=5)),
        "E-in4 limite su livello": dict(ein=dict(level=A["level"], K=5)),
        "E-out1 tutto, L20, spot": dict(eout=dict(trig=A["spot20"], frac=1.0)),
        "E-out2 metà, L20, spot": dict(eout=dict(trig=A["spot20"], frac=0.5)),
        "E-out3 tutto, L10, spot": dict(eout=dict(trig=A["spot10"], frac=1.0)),
        "E-out4 tutto, L20, con spot": dict(eout=dict(trig=A["con20"], frac=1.0)),
        "controllo: ogni rottura 20g": dict(eout=dict(trig=A["any20"], frac=1.0)),
    }


def tl(r):
    return list(r["trades"]) + ([dict(r["open"], pnl=r["open"]["pnl_close"], exit=None)] if r["open"] else [])


def met(r):
    e = r["equity"] / r["equity"].iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    pn = np.array([t["pnl"] for t in tl(r)])
    return dict(final=round(10000 * float(e.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3), n=len(pn), wr=round(100 * float((pn > 0).mean()), 1),
                worst=round(100 * float(pn.min()), 1), wo_best=round(10000 * float(e.iloc[-1]) / (1 + pn.max())))


def bh(x, s, e):
    x = x[(x.index >= s) & ((x.index <= e) if e else True)]
    eq = x["close"] / (x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT))
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = float((eq / eq.cummax() - 1).min())
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1)
    return dict(final=round(10000 * float(eq.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1), cdd=round(cagr / abs(dd), 3))


def groups(rv, rb):
    bt, vt = tl(rb), tl(rv)
    out, used = {}, set()
    for b in bt:
        lo, hi = b["signal"], b["exit"] or "9999"
        lv = 0.0
        for j, v in enumerate(vt):
            if lo <= v["signal"] <= hi:
                lv += np.log1p(v["pnl"])
                used.add(j)
        out[b["signal"]] = lv - np.log1p(b["pnl"])
    for j, v in enumerate(vt):
        if j not in used:
            out["nuovo " + v["signal"]] = np.log1p(v["pnl"])
    return out


def signflip(x):
    x = np.array([v for v in x if abs(v) > 1e-9])
    m = len(x)
    if m == 0:
        return 1.0, 0
    s = np.array(list(itertools.product([1, -1], repeat=m))) @ np.abs(x)
    return float((s >= x.sum() - 1e-12).mean()), m


def study(name: str, x: dict, do_placebo: bool) -> tuple[list, dict, list]:
    """x: {periodo: (frame, start, end)}; il primo periodo è 'ALL'."""
    rows, pvals, deltas = [], {}, []
    arr = {id(fr): arrays(fr) for fr in {id(v[0]): v[0] for v in x.values()}.values()}
    base = {p: E.simulate(fr, None, start=s, end=e) for p, (fr, s, e) in x.items()}
    mb = {p: met(base[p]) for p in x}
    rows.append(dict(asset=name, variante="W3.2", **{f"{p}_{k}": v for p in x for k, v in mb[p].items()}))
    fr0, s0, e0 = x["ALL"]
    rows.append(dict(asset=name, variante="Buy & hold", **{f"{p}_{k}": v for p, (fr, s, e) in x.items() for k, v in bh(fr, s, e).items()}))
    idx = fr0[fr0["close"].notna()].index
    rng = np.random.default_rng(SEED)
    for vn in variants(arr[id(fr0)]):
        res = {p: E.simulate(fr, variants(arr[id(fr)])[vn], start=s, end=e) for p, (fr, s, e) in x.items()}
        m = {p: met(res[p]) for p in x}
        g = groups(res["ALL"], base["ALL"])
        dv = np.array(list(g.values()))
        p_sf, nz = signflip(dv)
        wo2 = float(np.sort(dv)[:-2].sum()) if len(dv) > 2 else float("nan")
        ra = res["ALL"]
        tv = tl(ra)
        n_delay = sum(1 for t in tv if t.get("delay", 0) > 0)
        n_lim = sum(1 for t in tv if t.get("limit"))
        n_early = sum(t.get("n_early", 0) for t in tv)
        row = dict(asset=name, variante=vn, **{f"{p}_{k}": v for p in x for k, v in m[p].items()},
                   sum_d=round(100 * float(dv.sum()), 1), sum_d_wo2=round(100 * wo2, 1), p_segni=round(p_sf, 4), n_mod=nz,
                   n_ritardati=n_delay, n_limite=n_lim, n_uscite=n_early)
        for k, v in g.items():
            deltas.append(dict(asset=name, variante=vn, segnale=k, d_log_pct=round(100 * v, 2)))
        # placebo
        if do_placebo and not vn.startswith("controllo"):
            cfg = variants(arr[id(fr0)])[vn]
            pl = []
            bt = tl(base["ALL"])
            for _ in range(NPLA):
                if "ein" in cfg and "level" not in cfg["ein"]:
                    c2 = dict(ein=dict(delays=list(rng.integers(0, cfg["ein"]["K"] + 1, size=60))))
                elif "ein" in cfg:
                    waited = sum(1 for t in tv if t.get("delay", 0) > 0 or t.get("limit"))
                    dl = np.zeros(len(tv) + 5, int)
                    pick = rng.choice(len(tv), size=min(waited, len(tv)), replace=False)
                    dl[pick] = rng.integers(0, 6, size=len(pick))
                    c2 = dict(ein=dict(delays=list(dl)))
                else:
                    force = {t["signal"]: t.get("n_early", 0) for t in tv}
                    span = {}
                    for t in bt:
                        a = idx.searchsorted(pd.Timestamp(t["entry"]))
                        b = idx.searchsorted(pd.Timestamp(t["exit"])) if t["exit"] else len(idx) - 1
                        span[t["signal"]] = (int(a), int(b))
                    c2 = dict(eout=dict(force=force, span=span, rng=rng, frac=cfg["eout"]["frac"]))
                pl.append(met(E.simulate(fr0, c2, start=s0, end=e0))["cdd"])
            pl = np.array(pl)
            row["p_placebo"] = round(float((pl >= m["ALL"]["cdd"] - 1e-9).mean()), 3)
            row["placebo_med_cdd"] = round(float(np.median(pl)), 3)
        # criteri
        if "IS" in x:
            c = dict(C1=m["IS"]["cdd"] > mb["IS"]["cdd"] and m["OOS"]["cdd"] > mb["OOS"]["cdd"],
                     C2=(m["L"]["cdd"] >= mb["L"]["cdd"] - 1e-9) if "L" in x else None,
                     C3=m["ALL"]["dd"] >= -30, C4=m["ALL"]["wr"] >= 70, C5=wo2 > 0)
            row.update(c)
        rows.append(row)
        pvals[vn] = p_sf
        say(f"{name} · {vn}: " + " | ".join(f"{p} {m[p]['final']} $ DD {m[p]['dd']} CDD {m[p]['cdd']} WR {m[p]['wr']}" for p in x)
            + f" | ΣΔ {row['sum_d']} (senza 2: {row['sum_d_wo2']}) p segni {p_sf:.3f} (m={nz}) rit {n_delay} lim {n_lim} usc {n_early}"
            + (f" placebo p {row.get('p_placebo')}" if "p_placebo" in row else ""))
        if ra["log"]:
            say("    " + "; ".join(f"{a[0]} {a[1]} {a[2]} @{a[3]}" for a in ra["log"][:40]))
        if n_delay or n_lim:
            say("    ingressi: " + "; ".join(f"{t['signal']}→{t['entry']} (+{t.get('delay', 0)}g{' limite' if t.get('limit') else ''}) @{t['entry_px']}" for t in tv))
    say(f"{name} · W3.2: " + " | ".join(f"{p} {mb[p]['final']} $ DD {mb[p]['dd']} CDD {mb[p]['cdd']} WR {mb[p]['wr']} n {mb[p]['n']}" for p in x))
    return rows, pvals, deltas


# ---------------------------------------------------------------- E-hold
def hold(name: str, f0: pd.DataFrame) -> list:
    f = G.add_flows(f0)
    r = G.w3(f0)
    rows = []
    for t in G.trades(r):
        sd = 1 if t["side"] == "long" else -1
        a = pd.Timestamp(t["entry"])
        b = pd.Timestamp(t["exit"]) if t["exit"] else f.index[-1]
        seg = f[(f.index >= a) & (f.index < b)]
        cond = (seg["dn3"] <= -0.05) if sd > 0 else (seg["up3"] >= 0.05)
        k = G.klass(f, 3, -sd, D0)
        xp = t.get("exit_px") or float(f["close"].iloc[-1])
        for d in G.first_days(cond):
            c0 = float(f.loc[d, "close"])
            prev = seg.loc[:d, "close"]
            best_prev = prev.max() if sd > 0 else prev.min()
            after = seg.loc[d:, "close"].iloc[1:]
            rec = bool(((after > best_prev) if sd > 0 else (after < best_prev)).any()) if len(after) else False
            i = f.index.get_loc(d)
            f7 = (float(f["close"].iloc[i + 7]) / c0 - 1) * sd if i + 7 < len(f) else np.nan
            rows.append(dict(asset=name, segnale=t["signal"], lato=t["side"], giorno=str(d.date()), classe=k[d],
                             contrario_pct=round(100 * float(seg.loc[d, "dn3"] if sd > 0 else seg.loc[d, "up3"]), 1),
                             pz3=round(float(f.loc[d, "pz3"]), 2), sz3=round(float(f.loc[d, "sz3"]), 2),
                             r7_verso_trade=round(100 * f7, 1) if np.isfinite(f7) else np.nan,
                             fino_uscita=round(100 * (xp / c0 - 1) * sd, 1), nuovo_estremo=rec,
                             motivo=t.get("reason", "aperto"), pnl_trade=round(100 * t["pnl"], 1)))
    return rows


def main():
    fb, fl, fe = G.btc(), G.btc_long(), G.eth()
    fl2 = fl.join(fb[["spot_delta", "perp_delta", "spot_vol", "perp_vol"]], how="left")
    ev_rows, neigh = [], []
    pv = event_study("BTC", fb, ev_rows, neigh)
    pv_e = event_study("ETH", fe, ev_rows, neigh)
    pd.DataFrame(ev_rows).to_csv(HERE / "eventi.csv", index=False)
    pd.DataFrame(neigh).to_csv(HERE / "vicini.csv", index=False)
    say("\nVicini (7 g): " + pd.DataFrame(neigh).to_string(index=False))

    say("\n=== VARIANTI SU W3.2 · BTC")
    rows, pvs, deltas = study("BTC", {"ALL": (fb, "2021-01-01", None), "IS": (fb, "2021-01-01", "2023-12-31"),
                                       "OOS": (fb, "2024-01-01", None), "L": (fl2, "2018-01-01", "2020-12-31")}, True)
    say("\n=== VARIANTI SU W3.2 · ETH (conferma esterna)")
    rows_e, _, deltas_e = study("ETH", {"ALL": (fe, "2021-01-01", None), "IS": (fe, "2021-01-01", "2023-12-31"),
                                         "OOS": (fe, "2024-01-01", None)}, False)
    pd.DataFrame(rows + rows_e).to_csv(HERE / "varianti.csv", index=False)
    pd.DataFrame(deltas + deltas_e).to_csv(HERE / "trade_delta.csv", index=False)

    # Holm su 13 test
    allp = {k: v["p"] for k, v in pv.items()}
    allp.update({k: v for k, v in pvs.items() if not k.startswith("controllo")})
    order = sorted(allp, key=lambda k: allp[k])
    say(f"\n=== HOLM su {len(allp)} test (α 0,05)")
    run = 0.0
    for i, k in enumerate(order):
        adj = min(1.0, (len(order) - i) * allp[k])
        run = max(run, adj)
        say(f"{k}: p {allp[k]:.4f} · soglia {0.05 / (len(order) - i):.4f} · p Holm {run:.3f}")
    say("\nTest evento BTC: " + str({k: {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()} for k, v in pv.items()}))
    say("Test evento ETH: " + str({k: {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()} for k, v in pv_e.items()}))

    hr = hold("BTC", fb) + hold("ETH", fe)
    h = pd.DataFrame(hr)
    h.to_csv(HERE / "hold.csv", index=False)
    say("\n=== E-HOLD · movimenti contrari ≥ 5% in 3 giorni dentro i trade W3.2")
    for a in ("BTC", "ETH"):
        for c in ("perp", "spot", "misto"):
            x = h[(h.asset == a) & (h.classe == c)]
            if len(x):
                say(f"{a} · {c}: n {len(x)} · 7 g nel verso del trade {x.r7_verso_trade.mean():+.1f}% (positivi {100 * (x.r7_verso_trade > 0).mean():.0f}%) · "
                    f"fino all'uscita {x.fino_uscita.mean():+.1f}% (positivi {100 * (x.fino_uscita > 0).mean():.0f}%) · nuovo estremo a favore {100 * x.nuovo_estremo.mean():.0f}% · "
                    f"in trade poi chiusi in perdita {int((x.pnl_trade < 0).sum())}")
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
