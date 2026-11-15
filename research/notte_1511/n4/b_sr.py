"""N4 · Parte B: tenuta di supporti e resistenze del tool (radar/levels.py) contro livelli casuali (PREREG.md).
Uso: python b_sr.py → b_eventi.csv (zone reali e casuali con esito), b_tenuta.csv (statistiche), b_log.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from n4_data import raw  # noqa: E402
from radar import levels  # noqa: E402

BUCKETS = [(0.0, 0.03, "0-3%"), (0.03, 0.08, "3-8%"), (0.08, 0.15, "8-15%")]
SCALES = {"D3": ("d", 0.03, 56, 30), "D6": ("d", 0.06, 56, 30), "W10": ("w", 0.10, 8, 12)}
NRAND, NB = 20, 2000


def bucket(dist):
    for a, b, lab in BUCKETS:
        if a <= dist < b:
            return lab
    return None


def outcome(H, L, C, t, lo, hi, side, x, n_touch, n_out):
    """Esito di una zona [lo, hi] vista alla barra t: 'hold' / 'break' / 'none' (non toccata) / 'cens' (dati finiti)."""
    n = len(C)
    end = t + n_touch
    if end >= n:
        return "cens"
    seg = L[t + 1:end + 1] <= hi if side == "S" else H[t + 1:end + 1] >= lo
    if not seg.any():
        return "none"
    tau = t + 1 + int(np.argmax(seg))
    if tau + n_out >= n:
        return "cens"
    for j in range(tau, tau + n_out + 1):
        if side == "S":
            brk, hold = C[j] <= lo * (1 - x), H[j] >= hi * (1 + x)
        else:
            brk, hold = C[j] >= hi * (1 + x), L[j] <= lo * (1 - x)
        if brk:
            return "break"
        if hold and j > tau:
            return "hold"
    return "unres"


def main():
    f = raw()
    w = f[["open", "high", "low", "close"]].resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w = w[w.index <= f.index[-1]]
    D = {k: f[k].to_numpy(float) for k in ("high", "low", "close")}
    Wk = {k: w[k].to_numpy(float) for k in ("high", "low", "close")}
    rng = np.random.default_rng(1511)
    snaps = [t for t in w.index if t >= pd.Timestamp("2021-01-03")]
    rows = []
    for t in snaps:
        lv = levels.compute(f[f.index <= t])
        px, atr = float(f.loc[t, "close"]), float(lv["atr"])
        it, iw = f.index.get_loc(t), w.index.get_loc(t)
        zs = []
        for z in lv["supports"] + lv["resistances"]:
            lo, hi = z["lo"] - 0.25 * atr, z["hi"] + 0.25 * atr
            side = "S" if z["kind"] == "supporto" else "R"
            if (side == "S" and hi >= px) or (side == "R" and lo <= px):
                continue
            dist = abs(z["price"] / px - 1)
            b = bucket(dist)
            if b is None:
                continue
            typ = "W" if z["weekly"] else ("V" if z["touches"] == 0 else "G")
            zs.append(dict(lo=lo, hi=hi, side=side, dist=dist, b=b, typ=typ, F=z.get("strength", 0) >= 4, real=1, mid=z["price"]))
            a_, b_ = [(a, bb) for a, bb, lab in BUCKETS if lab == b][0]
            k, tries = 0, 0
            while k < NRAND and tries < 500:      # zona reale traslata: il suo centro (pivot medio) a distanza casuale nella fascia
                tries += 1
                dd = rng.uniform(a_, b_)
                mid = px * (1 - dd) if side == "S" else px * (1 + dd)
                rlo, rhi = lo + (mid - z["price"]), hi + (mid - z["price"])
                if (side == "S" and rhi >= px) or (side == "R" and rlo <= px):
                    continue
                zs.append(dict(lo=rlo, hi=rhi, side=side, dist=dd, b=b, typ=typ, F=z.get("strength", 0) >= 4, real=0, mid=mid))
                k += 1
        for z in zs:
            r = dict(snap=t, **z)
            for sc, (tf, x, nt, no) in SCALES.items():
                A, i0 = (D, it) if tf == "d" else (Wk, iw)
                r[sc] = outcome(A["high"], A["low"], A["close"], i0, z["lo"], z["hi"], z["side"], x, nt, no)
            rows.append(r)
    E = pd.DataFrame(rows)
    E["month"] = E.snap.dt.to_period("M").astype(str)
    E["half"] = np.where(E.snap <= "2023-12-31", "2021-23", "2024-26")
    E.to_csv(HERE / "b_eventi.csv", index=False, float_format="%.6g")
    return E


def p_hold(x):
    t = x[x.isin(["hold", "break", "unres"])]
    return (t == "hold").sum(), len(t)


def analyse(E):
    out = []
    groups = [("tipo", t) for t in ("G", "W", "V", "F", "tutti")]
    months = np.array(sorted(E.month.unique()))
    rng = np.random.default_rng(3)
    BM = rng.integers(0, len(months), size=(NB, len(months)))
    for sc in SCALES:
        for side in ("S", "R"):
            for _, typ in groups:
                for b in [lab for *_, lab in BUCKETS] + ["tutte"]:
                    sel = (E.side == side)
                    if typ == "F":
                        sel &= E.F
                    elif typ != "tutti":
                        sel &= E.typ == typ
                    if b != "tutte":
                        sel &= E.b == b
                    X = E[sel]
                    if X.real.sum() == 0:
                        continue
                    rr = {}
                    for real in (1, 0):
                        Y = X[X.real == real]
                        h, n = p_hold(Y[sc])
                        touched = Y[sc].isin(["hold", "break", "unres"]).sum()
                        valid = (~Y[sc].isin(["cens"])).sum()
                        rr[real] = (h, n, touched / max(valid, 1))
                        for hf in ("2021-23", "2024-26"):
                            hh, nn = p_hold(Y[Y.half == hf][sc])
                            rr[(real, hf)] = hh / nn if nn else np.nan
                    # bootstrap a grappoli per mese
                    agg = X.assign(t=X[sc].isin(["hold", "break", "unres"]), hd=X[sc].eq("hold")).groupby(["month", "real"])[["t", "hd"]].sum()
                    T_ = agg["t"].unstack(fill_value=0).reindex(months, fill_value=0)
                    Hd = agg["hd"].unstack(fill_value=0).reindex(months, fill_value=0)
                    if 1 not in T_ or 0 not in T_:
                        continue
                    tr, hr, t0, h0 = (T_[1].to_numpy()[BM].sum(1), Hd[1].to_numpy()[BM].sum(1),
                                      T_[0].to_numpy()[BM].sum(1), Hd[0].to_numpy()[BM].sum(1))
                    diff = hr / np.maximum(tr, 1) - h0 / np.maximum(t0, 1)
                    pr = rr[1][0] / max(rr[1][1], 1)
                    p0 = rr[0][0] / max(rr[0][1], 1)
                    se = diff.std()
                    out.append(dict(scala=sc, lato="supporto" if side == "S" else "resistenza", tipo=typ, distanza=b,
                                    n_zone=int(X.real.sum()), n_tocchi=rr[1][1], P_tocco=rr[1][2], P_tocco_casuale=rr[0][2],
                                    P_tenuta=pr, P_tenuta_casuale=p0, diff=pr - p0, ic_lo=np.percentile(diff, 2.5), ic_hi=np.percentile(diff, 97.5),
                                    p=float(np.mean(diff <= 0)), z=(pr - p0) / se if se else np.nan,
                                    P_2123=rr[(1, "2021-23")], P0_2123=rr[(0, "2021-23")], P_2426=rr[(1, "2024-26")], P0_2426=rr[(0, "2024-26")]))
    S = pd.DataFrame(out)
    from math import erf, sqrt
    S["p_norm"] = [1 - 0.5 * (1 + erf(z / sqrt(2))) if pd.notna(z) else 1.0 for z in S.z]
    core = (S.tipo != "tutti") & (S.distanza != "tutte")
    S["bh"] = False
    p = S.loc[core, "p_norm"].to_numpy()
    o = np.argsort(p); m = len(p)
    ok = p[o] <= 0.10 * np.arange(1, m + 1) / m
    k = np.max(np.flatnonzero(ok)) + 1 if ok.any() else 0
    idx = S.index[core][o[:k]]
    S.loc[idx, "bh"] = True
    S["vantaggio"] = S.bh & (S["diff"] >= 0.05) & ((S.P_2123 - S.P0_2123) >= 0.03) & ((S.P_2426 - S.P0_2426) >= 0.03)
    S.to_csv(HERE / "b_tenuta.csv", index=False, float_format="%.4g")
    return S


if __name__ == "__main__":
    E = main() if "--cached" not in sys.argv else pd.read_csv(HERE / "b_eventi.csv", parse_dates=["snap"])
    S = analyse(E)
    core = S[(S.tipo != "tutti") & (S.distanza != "tutte")]
    log = [f"zone reali {int(E.real.sum())}, casuali {int((E.real == 0).sum())}; test BH {len(core)}; superano BH {int(core.bh.sum())}; "
           f"'vantaggio' (≥ +5 punti, BH, entrambe le metà ≥ +3) {int(S.vantaggio.sum())}"]
    pd.set_option("display.width", 250)
    cols = ["scala", "lato", "tipo", "distanza", "n_zone", "n_tocchi", "P_tocco", "P_tocco_casuale", "P_tenuta", "P_tenuta_casuale", "diff",
            "ic_lo", "ic_hi", "p_norm", "P_2123", "P0_2123", "P_2426", "P0_2426", "bh"]
    log.append(S[(S.distanza == "tutte")][cols].round(3).to_string())
    log.append(core.sort_values("p_norm")[cols].head(12).round(3).to_string())
    txt = "\n\n".join(log)
    (HERE / "b_log.txt").write_text(txt)
    print(txt)
