"""dimensione · FASE 2 · D1–D4 come da PREREG.md (commit f558fb4), senza modificarlo. Deviazioni: DEVIAZIONI.md.
Uso: python -I research/dimensione/fase2.py   → fase2_output.txt, risultati.csv
"""
from __future__ import annotations

import sys
from itertools import chain
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import regole as R  # noqa: E402

END = R.END
CAP = 10000.0
INS0 = "2021-01-11"
SEED, NPLAC = 20261127, 5000
FR = {"BTC_L": R.frame("BTC", True), "BTC_T": R.frame("BTC", False), "ETH": R.frame("ETH", False)}
ASSET = {"BTC_L": "BTC", "BTC_T": "BTC", "ETH": "ETH"}
# (nome, frame, inizio, fine)
PER = {"BTC dal 2018": ("BTC_L", "2018-01-01", END), "BTC dal 2021": ("BTC_T", "2021-01-01", END),
       "ETH dal 2021": ("ETH", "2021-01-11", END),
       "BTC IS 2018-22": ("BTC_L", "2018-01-01", "2022-12-31"), "ETH IS 2021-22": ("ETH", "2021-01-11", "2022-12-31"),
       "BTC OOS 2023-": ("BTC_T", "2023-01-01", END), "ETH OOS 2023-": ("ETH", "2023-01-01", END),
       "BTC 2021-23": ("BTC_T", "2021-01-01", "2023-12-31"), "ETH 2021-23": ("ETH", "2021-01-11", "2023-12-31"),
       "BTC 2024-": ("BTC_T", "2024-01-01", END), "ETH 2024-": ("ETH", "2024-01-01", END)}
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)


def cut(fr, en):
    f = FR[fr]; return f[f.index <= en]


def met(o):
    e = o["equity"].dropna(); yrs = (e.index[-1] - e.index[0] + pd.Timedelta(days=1)).days / 365.25
    fin = float(e.iloc[-1]); dd = float((e / np.maximum(e.cummax(), CAP) - 1).min()); cg = (fin / CAP) ** (1 / yrs) - 1
    cl = np.array([t["pnl"] for t in o["trades"]])
    allp = np.array(list(cl) + ([o["open"]["pnl_close"]] if o["open"] else []))
    srt = np.sort(allp)[::-1]
    wo1 = CAP * np.prod(1 + srt[1:]) if len(srt) else CAP
    wo2 = CAP * np.prod(1 + srt[2:]) if len(srt) else CAP
    ret = fin / CAP - 1
    return dict(fin=round(fin), ret=round(100 * ret, 1), cagr=round(100 * cg, 1), dd=round(100 * dd, 1),
                cd=round(cg / abs(dd), 3) if dd < 0 else np.nan, mar=round(ret / abs(dd), 2) if dd < 0 else np.nan,
                n=len(allp), wr=round(100 * float((cl > 0).mean()), 1) if len(cl) else np.nan, wo1=round(wo1), wo2=round(wo2))


def port(ob, oe):
    idx = pd.date_range(INS0, END)
    tot = sum((o["equity"] / CAP).reindex(idx).ffill().fillna(1.0) for o in (ob, oe)) * CAP
    yrs = (idx[-1] - idx[0] + pd.Timedelta(days=1)).days / 365.25
    dd = float((tot / np.maximum(tot.cummax(), 2 * CAP) - 1).min()); cg = (tot.iloc[-1] / (2 * CAP)) ** (1 / yrs) - 1
    return dict(fin=round(float(tot.iloc[-1])), cagr=round(100 * cg, 1), dd=round(100 * dd, 1), cd=round(cg / abs(dd), 3))


def bh(fr, st, en=END):
    x = FR[fr]; x = x[(x.index >= st) & (x.index <= en)]
    e = CAP * 0.998 * x["close"] / (x["open"].iloc[0] * 1.0005)
    yrs = (e.index[-1] - e.index[0] + pd.Timedelta(days=1)).days / 365.25
    dd = float((e / np.maximum(e.cummax(), CAP) - 1).min()); cg = (e.iloc[-1] / CAP) ** (1 / yrs) - 1
    return dict(fin=round(float(e.iloc[-1])), ret=round(100 * (e.iloc[-1] / CAP - 1), 1), dd=round(100 * dd, 1), cd=round(cg / abs(dd), 3))


# ------------------------------------------------------------------ varianti
def conds(v, par):
    return {k: R.fattore(v, FR[k], ASSET[k], par) for k in FR}


def evaluate(v, par):
    """Metriche della variante (v None = W3.2) su tutti i periodi + insieme + operazioni toccate per periodo."""
    c = conds(v, par) if v else None
    lato = R.LATO[v] if v else 1
    r, nt = {}, {}
    for name, (fr, st, en) in PER.items():
        f = cut(fr, en)
        o = R.sim(f, st, cond=c[fr] if c else None, lato=lato)
        r[name] = met(o)
        nt[name] = len(R.toccate(R.sim(f, st), c[fr], lato)) if c else 0
    ob = R.sim(FR["BTC_T"], INS0, cond=c["BTC_T"] if c else None, lato=lato)
    oe = R.sim(FR["ETH"], INS0, cond=c["ETH"] if c else None, lato=lato)
    r["insieme"] = port(ob, oe)
    nt["insieme"] = sum(len(R.toccate(R.sim(FR[k], INS0), c[k], lato)) for k in ("BTC_T", "ETH")) if c else 0
    return r, nt


def crit1_ok(r, b, nt, name):
    if nt[name] == 0:
        return True                                               # periodo neutro (PREREG §5.1)
    return r[name]["cd"] > b[name]["cd"] and r[name]["dd"] >= b[name]["dd"]


def criteria(r, b, nt, nbs):
    c = {}
    for name in ("BTC dal 2018", "BTC dal 2021", "ETH dal 2021", "insieme"):
        c["1 " + name] = crit1_ok(r, b, nt, name)
    for name in ("BTC IS 2018-22", "ETH IS 2021-22", "BTC OOS 2023-", "ETH OOS 2023-"):
        c["2 " + name] = r[name]["cd"] >= b[name]["cd"]
    c["3 capitale insieme ≥ −5%"] = r["insieme"]["fin"] >= 0.95 * b["insieme"]["fin"]
    c["4 vicini"] = all(crit1_ok(x, b, xn, "insieme") and crit1_ok(x, b, xn, "BTC dal 2018")
                        and x["insieme"]["fin"] >= 0.95 * b["insieme"]["fin"] for x, xn in nbs)
    return c


# ------------------------------------------------------------------ placebo e concentrazione (dates = segnali da ridurre)
def ins_dates(db, de):
    ob = R.sim(FR["BTC_T"], INS0, dates=set(db)); oe = R.sim(FR["ETH"], INS0, dates=set(de))
    return port(ob, oe)


def _pl(args):
    return ins_dates(*args)["cd"]


def pools(lato):
    out = {}
    for k in ("BTC_T", "ETH"):
        o = R.sim(FR[k], INS0)
        tr = o["trades"] + ([o["open"]] if o["open"] else [])
        out[k] = [pd.Timestamp(t["signal"]) for t in tr if (t["side"] == "long") == (lato > 0)]
    return out


def touched_dates(v):
    c = conds(v, R.PAR[v]); lato = R.LATO[v]
    return {k: [pd.Timestamp(t["signal"]) for t in R.toccate(R.sim(FR[k], INS0), c[k], lato)] for k in ("BTC_T", "ETH")}


def holm(ps, a=0.05):
    order = sorted(ps, key=ps.get); ok, m, stop = {}, len(ps), False
    for i, k in enumerate(order):
        stop = stop or ps[k] > a / (m - i); ok[k] = not stop
    return ok


def row(lbl, x, n=None):
    s = f"{lbl:16s} {x['fin']:>9,} $ · rend {x.get('ret', '-')}% · CAGR {x['cagr']}% · DD {x['dd']}% · CAGR/DD {x['cd']:.2f}"
    if "n" in x:
        s += f" · MAR {x['mar']} · op {x['n']} · WR {x['wr']}% · senza migliore {x['wo1']:,} · senza 2 {x['wo2']:,}"
    return s + (f" · toccate {n}" if n is not None else "")


def main():
    base, _ = evaluate(None, None)
    p("=== W3.2 com'è ===")
    for k, x in base.items():
        p(row(k, x))
    for lbl, (fr, st) in {"BTC dal 2018": ("BTC_L", "2018-01-01"), "BTC dal 2021": ("BTC_T", "2021-01-01"),
                          "ETH dal 2021": ("ETH", "2021-01-11")}.items():
        p(f"Buy & hold {lbl}: {bh(fr, st)}")
    rng = np.random.default_rng(SEED)
    res, ps, rows = {}, {}, []
    with Pool(4) as pool:
        for v in ("D1", "D2", "D3", "D4"):
            r, nt = evaluate(v, R.PAR[v])
            nbs = [evaluate(v, q) for q in R.VICINI[v]]
            c = criteria(r, base, nt, nbs)
            # controllo: dates = cond
            td = touched_dates(v)
            chk = ins_dates(td["BTC_T"], td["ETH"])
            assert abs(chk["fin"] - r["insieme"]["fin"]) <= 1, (chk, r["insieme"])
            # concentrazione (§5.7): riporto a 0,25 una operazione alla volta
            conc = []
            for k in ("BTC_T", "ETH"):
                for d in td[k]:
                    db = [x for x in td["BTC_T"] if not (k == "BTC_T" and x == d)]
                    de = [x for x in td["ETH"] if not (k == "ETH" and x == d)]
                    conc.append((ins_dates(db, de)["cd"], k, str(d.date())))
            worst = min(conc) if conc else (r["insieme"]["cd"], "-", "-")
            c["7 non concentrato"] = worst[0] > base["insieme"]["cd"]
            # placebo (§5.5)
            pl = pools(R.LATO[v]); kb, ke = len(td["BTC_T"]), len(td["ETH"])
            jobs = []
            for _ in range(NPLAC):
                db = list(rng.choice(pl["BTC_T"], kb, replace=False)) if kb else []
                de = list(rng.choice(pl["ETH"], ke, replace=False)) if ke else []
                jobs.append(([pd.Timestamp(x) for x in db], [pd.Timestamp(x) for x in de]))
            vals = np.array(pool.map(_pl, jobs, chunksize=50))
            act = r["insieme"]["cd"]
            pv = (1 + int((vals >= act - 1e-12).sum())) / (NPLAC + 1)
            beat = float((vals > base["insieme"]["cd"]).mean()); med = float(np.median(vals))
            ps[v] = pv
            res[v] = (r, nt, nbs, c, pv, beat, med, worst, kb, ke, len(pl["BTC_T"]), len(pl["ETH"]))
            p(f"\n=== {v} (parametro {R.PAR[v]}) ===")
            for k, x in r.items():
                p(row(k, x, nt[k]))
            for q, (x, xn) in zip(R.VICINI[v], nbs):
                p(f"vicino {q}: insieme {x['insieme']['fin']:,} $ DD {x['insieme']['dd']} CAGR/DD {x['insieme']['cd']:.3f} · "
                  f"BTC 2018 CAGR/DD {x['BTC dal 2018']['cd']:.3f} DD {x['BTC dal 2018']['dd']} (toccate {xn['BTC dal 2018']}) · "
                  f"BTC 2021 {x['BTC dal 2021']['cd']:.3f} · ETH {x['ETH dal 2021']['cd']:.3f}")
            p(f"concentrazione: peggior ripristino {worst[1]} {worst[2]} → CAGR/DD insieme {worst[0]:.3f} (W3.2 {base['insieme']['cd']:.3f})")
            p(f"placebo: {kb}/{len(pl['BTC_T'])} BTC + {ke}/{len(pl['ETH'])} ETH ridotte a caso, {NPLAC} prove · p {pv:.4f} · "
              f"quota che batte W3.2 {100 * beat:.1f}% · mediana {med:.3f} · reale {act:.3f} · W3.2 {base['insieme']['cd']:.3f}")
            p("criteri: " + " · ".join(f"{k} {'sì' if ok else 'NO'}" for k, ok in c.items()))
    hk = holm(ps)
    p("\n=== VERDETTO ===")
    ok_v = []
    for v, (r, nt, nbs, c, pv, beat, med, worst, *_ ) in res.items():
        allc = all(c.values()); passa = allc and hk[v]
        if passa:
            ok_v.append(v)
        p(f"{v}: criteri {'tutti' if allc else 'falliti: ' + ', '.join(k for k, o in c.items() if not o)} · p {pv:.4f} Holm "
          f"{'sì' if hk[v] else 'no'} → {'PASSA' if passa else 'non passa'}")
        rows.append(dict(variante=v, passa=passa, p=pv, holm=hk[v], quota_batte=beat, mediana=med,
                         **{f"{k}_{m}": r[k][m] for k in r for m in ("fin", "dd", "cd")},
                         **{f"tocc_{k}": nt[k] for k in nt}, falliti=",".join(k for k, o in c.items() if not o)))
    if ok_v:
        best = max(ok_v, key=lambda v: res[v][0]["insieme"]["cd"])
        p(f"Scelta finale (PREREG §6): {best}")
    else:
        p("Scelta finale (PREREG §6): nessuna → W3.2 resta com'è")
    pd.DataFrame(rows).to_csv(HERE / "risultati.csv", index=False)
    (HERE / "fase2_output.txt").write_text("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
