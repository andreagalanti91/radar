"""dati_nuovi · FASE 2 · V1–V9 come da PREREG.md (commit ba77738), senza modificarlo. Deviazioni: DEVIAZIONI.md.
Uso: python -I research/dati_nuovi/fase2.py            (tabelle + criteri + placebo, scrive fase2_output.txt e risultati.csv)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fonti as F  # noqa: E402
import motore as M  # noqa: E402

END = M.END
CAP = 10000.0
FR = {"BTC_T": M.frame("BTC", False), "BTC_L": M.frame("BTC", True), "ETH": M.frame("ETH", False)}
BIN = {"BTC": FR["BTC_L"]["funding"], "ETH": FR["ETH"]["funding"]}
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)


# ------------------------------------------------------------------ varianti (PREREG §3)
def sig(v, asset, par=None):
    if v in ("V1", "V2"):
        return F.cot_signal(asset, par or 4)
    if v in ("V3", "V4"):
        return F.basis_signal(asset, par or 28)
    if v == "V5":
        hi, lo = par or (0.90, 0.10); return F.funding_signal(asset, BIN[asset], hi, lo)
    if v == "V6":
        a, b = par or (30, 60); return F.hash_signal(a, b)
    if v == "V7":
        return F.hash_signal_b(weeks=par or 8)
    if v == "V8":
        return F.cm_netflow_signal(asset, par or 7)
    if v == "V9":
        return F.cm_balance_signal(asset, par or 28)


VAR = {"V1": ("COT-A", "A", [3, 6]), "V2": ("COT-B", "B", [3, 6]), "V3": ("BASE-A", "A", [21, 42]), "V4": ("BASE-B", "B", [21, 42]),
       "V5": ("FUNDING-A", "A", [(0.85, 0.15), (0.95, 0.05)]), "V6": ("MINER-A", "A", [(25, 50), (35, 70)]),
       "V7": ("MINER-E", "E", [6, 12]), "V8": ("FLUSSI-A", "A", [5, 14]), "V9": ("SALDO-B", "B", [21, 42])}


# ------------------------------------------------------------------ simulazioni e metriche
def run(frame, start, end=END, s=None, mode=None):
    f = FR[frame]; f = f[f.index <= end]
    return M.sim(f, start, s, mode)


def met(o):
    e = o["equity"].dropna(); yrs = (e.index[-1] - e.index[0] + pd.Timedelta(days=1)).days / 365.25
    fin = float(e.iloc[-1]); dd = float((e / np.maximum(e.cummax(), CAP) - 1).min())
    cg = (fin / CAP) ** (1 / yrs) - 1
    cl = np.array([t["pnl"] for t in o["trades"]])
    allp = list(cl) + ([o["open"]["pnl_close"]] if o["open"] else [])
    wo = CAP * np.prod(1 + np.delete(np.array(allp), int(np.argmax(allp)))) if allp else CAP
    return dict(fin=round(fin), ret=round(100 * (fin / CAP - 1), 1), cagr=round(100 * cg, 1), dd=round(100 * dd, 1),
                cd=round(cg / abs(dd), 3) if dd < 0 else np.nan, n=len(allp), chiuse=len(cl),
                wr=round(100 * float((cl > 0).mean()), 1) if len(cl) else np.nan, wo=round(wo))


def port(o1, o2, start="2021-01-11"):
    idx = pd.date_range(start, END)
    tot = sum((o["equity"] / CAP).reindex(idx).ffill().fillna(1.0) for o in (o1, o2)) * CAP
    yrs = (idx[-1] - idx[0] + pd.Timedelta(days=1)).days / 365.25
    dd = float((tot / np.maximum(tot.cummax(), 2 * CAP) - 1).min()); cg = (tot.iloc[-1] / (2 * CAP)) ** (1 / yrs) - 1
    return dict(fin=round(float(tot.iloc[-1])), cagr=round(100 * cg, 1), dd=round(100 * dd, 1), cd=round(cg / abs(dd), 3))


def bh(frame, start, end=END):
    f = FR[frame]; x = f[(f.index >= start) & (f.index <= end)]
    e = CAP * 0.998 * x["close"] / (x["open"].iloc[0] * 1.0005)
    yrs = (e.index[-1] - e.index[0] + pd.Timedelta(days=1)).days / 365.25
    dd = float((e / np.maximum(e.cummax(), CAP) - 1).min()); cg = (e.iloc[-1] / CAP) ** (1 / yrs) - 1
    return dict(fin=round(float(e.iloc[-1])), cagr=round(100 * cg, 1), dd=round(100 * dd, 1), cd=round(cg / abs(dd), 3))


PER = {"BTC": [("dal 2018", "BTC_L", "2018-01-01", END), ("dal 2021", "BTC_T", "2021-01-01", END),
               ("IS 2018-22", "BTC_L", "2018-01-01", "2022-12-31"), ("OOS 2023-", "BTC_T", "2023-01-01", END),
               ("2024-", "BTC_T", "2024-01-01", END)],
       "ETH": [("dal 2021", "ETH", "2021-01-11", END), ("IS 2021-22", "ETH", "2021-01-11", "2022-12-31"),
               ("OOS 2023-", "ETH", "2023-01-01", END), ("2024-", "ETH", "2024-01-01", END)]}


def evaluate(sb, se, mode):
    """sb, se: segnali BTC/ETH (None = W3.2)."""
    r = {}
    for a, s in (("BTC", sb), ("ETH", se)):
        for name, fr, st, en in PER[a]:
            r[(a, name)] = met(run(fr, st, en, s, mode))
    r["insieme"] = port(run("BTC_T", "2021-01-11", END, sb, mode), run("ETH", "2021-01-11", END, se, mode))
    return r


def ins_cd(sb, se, mode):
    return port(run("BTC_T", "2021-01-11", END, sb, mode), run("ETH", "2021-01-11", END, se, mode))["cd"]


# ------------------------------------------------------------------ criteri (PREREG §5)
def crit(kind, r, b, nb):
    """nb: dict asset -> [cd dal 2021 dei due vicini]."""
    c = {}
    for a in ("BTC", "ETH"):
        x, y = r[(a, "dal 2021")], b[(a, "dal 2021")]
        isn, oosn = ("IS 2018-22" if a == "BTC" else "IS 2021-22"), "OOS 2023-"
        if kind == "A":
            c[a + " cd>"] = x["cd"] > y["cd"]
            c[a + " wr≥"] = x["wr"] >= y["wr"]
            c[a + " senza migliore≥"] = x["wo"] >= y["wo"]
        else:
            c[a + " più op."] = x["n"] > y["n"]
            c[a + " cd≥"] = x["cd"] >= y["cd"]
            c[a + " wr≥−5"] = x["wr"] >= y["wr"] - 5
        c[a + " dd≤+2"] = x["dd"] >= y["dd"] - 2
        if a == "BTC":
            c["BTC 2018 cd≥"] = r[("BTC", "dal 2018")]["cd"] >= b[("BTC", "dal 2018")]["cd"]
        c[a + " IS≥"] = r[(a, isn)]["cd"] >= b[(a, isn)]["cd"]
        c[a + " OOS≥"] = r[(a, oosn)]["cd"] >= b[(a, oosn)]["cd"]
        c[a + " vicini≥"] = all(v >= y["cd"] for v in nb[a])
    c["insieme"] = r["insieme"]["cd"] > b["insieme"]["cd"] if kind == "A" else r["insieme"]["cd"] >= b["insieme"]["cd"]
    return c


# ------------------------------------------------------------------ placebo (slittamento circolare di s, PREREG §5)
def roll(s, k):
    return pd.Series(np.roll(s.to_numpy(), 7 * k), index=s.index)


def _plac(args):
    sb, se, mode, k = args
    return ins_cd(roll(sb, k), roll(se, k), mode)


def placebo(sb, se, mode, act, pool):
    N = len(F.IDX) // 7
    ks = list(range(26, N - 26 + 1))
    vals = np.array(pool.map(_plac, [(sb, se, mode, k) for k in ks], chunksize=8))
    return (int((vals >= act).sum()) + 1) / (len(ks) + 1), len(ks), float(np.median(vals))


def holm(ps, a=0.05):
    order = sorted(ps, key=ps.get); ok, m, stop = {}, len(ps), False
    for i, k in enumerate(order):
        stop = stop or ps[k] > a / (m - i); ok[k] = not stop
    return ok


def fmt_row(lbl, x):
    return (f"{lbl:16s} fin {x['fin']:>9,} $ · rend {x.get('ret', ''):>7}% · CAGR {x['cagr']:>5}% · DD {x['dd']:>6}% · CAGR/DD "
            f"{x['cd']:.2f}" + (f" · op. {x['n']:>2} · WR chiuse {x['wr']}% · senza migliore {x['wo']:,} $" if "n" in x else ""))


def main():
    pd.set_option("display.width", 250)
    base = evaluate(None, None, None)
    p("=== W3.2 (verifica: BTC dal 2018 242.755, dal 2021 84.820; ETH 39.572) ===")
    for k, x in base.items():
        p(fmt_row(str(k), x))
    p("Buy & hold: BTC dal 2018 " + str(bh("BTC_L", "2018-01-01")) + " · BTC dal 2021 " + str(bh("BTC_T", "2021-01-01"))
      + " · ETH dal 2021 " + str(bh("ETH", "2021-01-11")))
    rows, ps, res = [], {}, {}
    with Pool(4) as pool:
        for v, (nm, kind, nbs) in VAR.items():
            sb, se = sig(v, "BTC"), sig(v, "ETH")
            r = evaluate(sb, se, kind)
            nb = {a: [met(run("BTC_T" if a == "BTC" else "ETH", "2021-01-01" if a == "BTC" else "2021-01-11", END,
                               sig(v, a, q), kind))["cd"] for q in nbs] for a in ("BTC", "ETH")}
            c = crit(kind, r, base, nb)
            pv, nk, med = placebo(sb, se, kind, r["insieme"]["cd"], pool)
            ps[v] = pv; res[v] = (nm, kind, r, c, nb, pv, nk, med)
            p(f"\n=== {v} {nm} (regola {kind}) ===")
            for k, x in r.items():
                p(fmt_row(str(k), x))
            p(f"vicini CAGR/DD dal 2021: BTC {nb['BTC']} (W3.2 {base[('BTC', 'dal 2021')]['cd']}) · ETH {nb['ETH']} (W3.2 {base[('ETH', 'dal 2021')]['cd']})")
            p("criteri: " + " · ".join(f"{k} {'sì' if ok else 'NO'}" for k, ok in c.items()))
            p(f"placebo: p esatto {pv:.4f} su {nk} slittamenti (mediana CAGR/DD insieme {med:.2f}, reale {r['insieme']['cd']:.2f})")
    hk = holm(ps)
    p("\n=== VERDETTO ===")
    for v, (nm, kind, r, c, nb, pv, nk, med) in res.items():
        allc = all(c.values())
        passa = allc and hk[v]
        p(f"{v} {nm:10s} {kind}: criteri {'tutti' if allc else 'falliti: ' + ', '.join(k for k, ok in c.items() if not ok)} · "
          f"placebo p {pv:.4f} Holm {'sì' if hk[v] else 'no'} → {'PASSA' if passa else 'non passa'}")
        rows.append(dict(variante=v, nome=nm, regola=kind, passa=passa, placebo_p=pv, holm=hk[v],
                         ins_fin=r["insieme"]["fin"], ins_cd=r["insieme"]["cd"], ins_dd=r["insieme"]["dd"],
                         **{f"{a}_{per}_{m}": r[(a, per)][m] for a in ("BTC", "ETH") for per, *_ in PER[a] for m in ("fin", "cd", "dd", "n", "wr", "wo")},
                         falliti=",".join(k for k, ok in c.items() if not ok)))
    pd.DataFrame(rows).to_csv(HERE / "risultati.csv", index=False)
    (HERE / "fase2_output.txt").write_text("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
