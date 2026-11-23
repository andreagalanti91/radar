"""Previsionale · walk-forward, metriche, riferimenti, test (PREREG §4–6). Scrive risultati.txt e i csv.
Uso: python3 research/previsionale/fc_run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from fc_data import ALL, PRICE, dataset, frozen  # noqa: E402
from fc_models import recalibrate, walk_forward  # noqa: E402
from radar import weekly as W  # noqa: E402

LO, HI = 0.45, 0.55
PERIODS = {"2018-20*": ("2018-01-01", "2020-12-31"), "2021-23": ("2021-01-01", "2023-12-31"),
           "2024-26": ("2024-01-01", "2026-12-31"), "2021-26": ("2021-01-01", "2026-12-31")}
MODELS = {"p1": "M1 LOGIT-P", "p2": "M2 LOGIT-T", "p3": "M3 CEPPI", "p4": "M4 MEDIA"}
RNG = np.random.default_rng(112)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def call(p):
    return np.where(p > HI, 1, np.where(p < LO, -1, 0))


def auc(y, p) -> float:
    y, p = np.asarray(y), np.asarray(p)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if not n1 or not n0:
        return np.nan
    r = pd.Series(p).rank().to_numpy()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def acc_cov(c, y):
    m = c != 0
    return (float(np.mean((c[m] > 0) == (y[m] > 0.5))) if m.any() else np.nan), float(m.mean())


def shift_p(c, y, h) -> float:
    """Permutazione per sfasamento circolare degli esiti (tutti gli sfasamenti fra 2h e N − 2h)."""
    a0, _ = acc_cov(c, y)
    if np.isnan(a0):
        return np.nan
    n = len(y)
    ks = range(2 * h, n - 2 * h)
    a = np.array([acc_cov(c, np.roll(y, k))[0] for k in ks])
    return float((1 + (a >= a0 - 1e-12).sum()) / (1 + len(a)))


def boot_idx(n, h, B=2000):
    L = max(30, 2 * h)
    nb = int(np.ceil(n / L))
    st = RNG.integers(0, n, size=(B, nb))
    return ((st[:, :, None] + np.arange(L)[None, None, :]) % n).reshape(B, -1)[:, :n]


def boot_ci(fn, n, h, B=2000):
    v = np.array([fn(i) for i in boot_idx(n, h, B)])
    v = v[np.isfinite(v)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def nonoverlap(c, y, h):
    a, n = [], []
    for ph in range(h):
        cc, yy = c[ph::h], y[ph::h]
        m = cc != 0
        if m.any():
            a.append(np.mean((cc[m] > 0) == (yy[m] > 0.5)))
            n.append(m.sum())
    return (float(np.mean(a)), float(np.mean(n))) if a else (np.nan, 0.0)


def w32_regime(idx: pd.DatetimeIndex) -> pd.Series:
    """Lato della posizione W3.2 alla chiusura di t (in posizione per ingresso ≤ t < uscita)."""
    f, fl = frozen()
    s = pd.Series(0, index=idx)
    for fr, st, en in ((fl[fl.index <= "2020-12-31"], "2018-01-01", "2020-12-31"), (f, W.START, None)):
        r = W.simulate(fr, start=st)
        for t in r["trades"] + ([r["open"]] if r.get("open") else []):
            sd = 1 if t["side"] == "long" else -1
            ex = pd.Timestamp(t["exit"]) - pd.Timedelta(days=1) if t.get("exit") else idx[-1]
            s[(s.index >= t["entry"]) & (s.index <= ex)] = sd
    return s


def holm(ps: dict) -> dict:
    ks = sorted(ps, key=lambda k: ps[k])
    out, mx = {}, 0.0
    for i, k in enumerate(ks):
        mx = max(mx, min(1.0, (len(ks) - i) * ps[k]))
        out[k] = mx
    return out


def table(d: pd.DataFrame, h: int, cols: dict, refs: dict) -> pd.DataFrame:
    rows = []
    for pn, (a, b) in PERIODS.items():
        q = d[(d.index >= a) & (d.index <= b) & d["y"].notna()]
        y = q["y"].to_numpy()
        n = len(q)
        for col, name in cols.items():
            p = q[col].to_numpy()
            c = call(p)
            ac, cv = acc_cov(c, y)
            lo, hi = boot_ci(lambda i: acc_cov(c[i], y[i])[0], n, h, 1000)
            no, nn = nonoverlap(c, y, h)
            bs, b0 = float(np.mean((p - y) ** 2)), float(np.mean((q["p0"].to_numpy() - y) ** 2))
            rows.append(dict(h=h, periodo=pn, modello=name, n_giorni=n, n_indip=round(n / h), base_su=round(y.mean(), 3),
                             acc=ac, acc_lo=lo, acc_hi=hi, cop=cv, acc_nonsovr=no, n_nonsovr=nn, auc=auc(y, p), brier=bs,
                             brier_skill=1 - bs / b0, acc_su=float(np.mean(y[c > 0] > .5)) if (c > 0).any() else np.nan,
                             n_su=int((c > 0).sum()), acc_giu=float(np.mean(y[c < 0] < .5)) if (c < 0).any() else np.nan,
                             n_giu=int((c < 0).sum())))
        for name, c in refs.items():
            cc = c.reindex(q.index).to_numpy()
            ac, cv = acc_cov(cc, y)
            no, nn = nonoverlap(cc, y, h)
            rows.append(dict(h=h, periodo=pn, modello=name, n_giorni=n, n_indip=round(n / h), base_su=round(y.mean(), 3),
                             acc=ac, cop=cv, acc_nonsovr=no, n_nonsovr=nn))
    return pd.DataFrame(rows)


def main() -> None:
    x = dataset()
    say(f"Dataset {x.index[0].date()} → {x.index[-1].date()}, {len(x)} giorni")
    reg = w32_regime(x.index)
    allt, pvals, verdict = [], {}, {}
    for h in (7, 30):
        d, hist = walk_forward(x, h)
        d.to_csv(HERE / f"prob_h{h}.csv", float_format="%.5f")
        hist.to_csv(HERE / f"coef_h{h}.csv", float_format="%.5f")
        refs = {"R1 sale sempre": pd.Series(1, index=d.index), "R2 persistenza": np.sign(x[f"r{h}"]).reindex(d.index).fillna(0).astype(int),
                "R3 regime W3.2": reg.reindex(d.index)}
        t = table(d, h, MODELS, refs)
        allt.append(t)
        say(f"\n===== ORIZZONTE {h} giorni =====")
        say(t.round(3).to_string(index=False))
        o = d[(d.index >= "2021-01-01") & d["y"].notna()]
        y = o["y"].to_numpy()
        for col, name in MODELS.items():
            pvals[(h, name)] = shift_p(call(o[col].to_numpy()), y, h)
        # AUC: sfasamento circolare
        for col, name in MODELS.items():
            p = o[col].to_numpy()
            a0 = auc(y, p)
            aa = np.array([auc(np.roll(y, k), p) for k in range(2 * h, len(y) - 2 * h, 3)])
            say(f"  AUC 2021-26 {name}: {a0:.3f}  p sfasamento {(1 + (aa >= a0).sum()) / (1 + len(aa)):.3f}")
        # confronto con i riferimenti sugli stessi giorni (M4)
        c4 = call(o["p4"].to_numpy())
        for name, c in refs.items():
            cc = c.reindex(o.index).to_numpy()
            m = (c4 != 0) & (cc != 0)
            if m.sum() < 30:
                continue
            a_m, a_r = np.mean((c4[m] > 0) == (y[m] > .5)), np.mean((cc[m] > 0) == (y[m] > .5))
            n = len(y)
            def diff(i):
                mm = m[i]
                return np.mean((c4[i][mm] > 0) == (y[i][mm] > .5)) - np.mean((cc[i][mm] > 0) == (y[i][mm] > .5)) if mm.any() else np.nan
            lo, hi = boot_ci(diff, n, h, 1000)
            say(f"  M4 contro {name} sugli stessi giorni ({int(m.sum())}): {a_m:.3f} contro {a_r:.3f}, diff {a_m - a_r:+.3f} IC95 [{lo:+.3f}, {hi:+.3f}]")
        # calibrazione per decili (M4, 2021-26)
        q = pd.qcut(o["p4"], 10, duplicates="drop")
        cal = o.groupby(q, observed=True).agg(p_media=("p4", "mean"), freq_su=("y", "mean"), n=("y", "size"))
        say("  Calibrazione M4 per decili (2021-26):")
        say(cal.round(3).to_string())
        cal.to_csv(HERE / f"calibrazione_h{h}.csv", float_format="%.4f")
        # coefficienti standardizzati di M2
        hh = hist[hist.index >= "2021-01-01"]
        co = pd.DataFrame({"2021-01": hist.loc["2021-01-01"], "2024-01": hist.loc["2024-01-01"], "ultimo": hist.iloc[-1],
                           "media": hh.mean(), "min": hh.min(), "max": hh.max(),
                           "segno_stabile": (np.sign(hh) == np.sign(hh.mean())).mean()}).loc[[f"b_{c}" for c in ALL] + [f"b1_{c}" for c in PRICE]]
        say("  Coefficienti standardizzati (b_ = M2, b1_ = M1), riaddestramenti dal 2021:")
        say(co.round(3).to_string())
        say("  Iperparametri scelti (conteggi dal 2021): λ1", hh["lam1"].value_counts().to_dict(), "λ2", hh["lam2"].value_counts().to_dict(),
            "k3", hh["k3"].value_counts().to_dict())
        # (b) aggiornato contro statico
        s, _ = walk_forward(x, h, start="2021-01-01", static="2021-01-01")
        say("  (b) Aggiornato (walk-forward) contro statico (addestrato una volta al 31/12/2020):")
        for pn in ("2021-23", "2024-26", "2021-26"):
            a, b = PERIODS[pn]
            for col, name in MODELS.items():
                qa = d[(d.index >= a) & (d.index <= b) & d["y"].notna()]
                qs = s.reindex(qa.index)
                yy = qa["y"].to_numpy()
                e_a, e_s = (qa[col].to_numpy() - yy) ** 2, (qs[col].to_numpy() - yy) ** 2
                lo, hi = boot_ci(lambda i: np.mean(e_a[i] - e_s[i]), len(yy), h, 1000)
                aa, ca = acc_cov(call(qa[col].to_numpy()), yy)
                as_, cs = acc_cov(call(qs[col].to_numpy()), yy)
                say(f"    {pn} {name}: Brier {e_a.mean():.4f} contro {e_s.mean():.4f} (diff {e_a.mean() - e_s.mean():+.4f}, IC95 [{lo:+.4f}, {hi:+.4f}]);"
                    f" acc {aa:.3f}/{as_:.3f}, cop {ca:.2f}/{cs:.2f}, AUC {auc(yy, qa[col]):.3f}/{auc(yy, qs[col]):.3f}")
        s.to_csv(HERE / f"prob_statico_h{h}.csv", float_format="%.5f")
        # (c) ricalibrazione
        say("  (c) Ricalibrazione di Platt sugli errori passati (M4): C1 espansiva, C2 ultimi 730 giorni")
        for nm, win in (("C1", None), ("C2", 730)):
            d[f"p4_{nm}"] = recalibrate(d, "p4", h, win)
            for pn in ("2021-23", "2024-26", "2021-26"):
                a, b = PERIODS[pn]
                q2 = d[(d.index >= a) & (d.index <= b) & d["y"].notna() & d[f"p4_{nm}"].notna()]
                yy = q2["y"].to_numpy()
                e_r, e_0 = (q2[f"p4_{nm}"].to_numpy() - yy) ** 2, (q2["p4"].to_numpy() - yy) ** 2
                lo, hi = boot_ci(lambda i: np.mean(e_r[i] - e_0[i]), len(yy), h, 1000)
                ar, cr = acc_cov(call(q2[f"p4_{nm}"].to_numpy()), yy)
                a0, c0 = acc_cov(call(q2["p4"].to_numpy()), yy)
                say(f"    {pn} {nm}: Brier {e_r.mean():.4f} contro {e_0.mean():.4f} grezzo (diff {e_r.mean() - e_0.mean():+.4f}, IC95 [{lo:+.4f}, {hi:+.4f}]);"
                    f" acc {ar:.3f}/{a0:.3f}, cop {cr:.2f}/{c0:.2f}, n {len(yy)}")
        d.to_csv(HERE / f"prob_h{h}.csv", float_format="%.5f")
        # verdetto preregistrato su M4
        g = t.set_index(["periodo", "modello"])
        ok = {}
        for pn in ("2021-23", "2024-26"):
            m4 = g.loc[(pn, "M4 MEDIA")]
            ok[pn] = dict(a=m4["acc"] >= 0.55, b=m4["cop"] >= 0.25, e=m4["auc"] > 0.5,
                          c=all(m4["acc"] > g.loc[(pn, r), "acc"] for r in refs))
        verdict[h] = ok
    hp = holm(pvals)
    say("\n===== SIGNIFICATIVITÀ (sfasamento circolare, 2021-26) e Holm sugli 8 test =====")
    for k in pvals:
        say(f"  h={k[0]:>2} {k[1]:<11} p = {pvals[k]:.4f}   Holm = {hp[k]:.4f}")
    say("\n===== VERDETTO PREREGISTRATO (M4) =====")
    for h, ok in verdict.items():
        d_ok = hp[(h, "M4 MEDIA")] < 0.05
        abe = all(ok[p][k] for p in ok for k in "abe")
        c_ok = all(ok[p]["c"] for p in ok)
        v = "FUNZIONA" if abe and c_ok and d_ok else ("NON DIMOSTRABILE" if abe else "NON FUNZIONA")
        say(f"  h={h}: {v}   criteri per periodo {ok}   (d) Holm<0,05: {d_ok}")
    pd.concat(allt).to_csv(HERE / "tabella.csv", index=False, float_format="%.4f")
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
