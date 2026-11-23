"""Previsionale 2 · walk-forward dei modelli R, P, RP (+ PF, PF+P), metriche, soglia relativa, test, Holm su 16 (PREREG §4–5).
Riusa fc_models (logistica L2, standardizzazione) e fc_run (AUC, bootstrap a blocchi, Holm, regime W3.2) del primo ciclo.
Uso: python3 research/previsionale2/p2_run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import SETS, build, labels  # noqa: E402
from fc_data import PRICE  # noqa: E402
from fc_models import LAMS, TRAIN_START, fit_logit, logloss, pred_logit, scale, scaler  # noqa: E402
import fc_run as F1  # noqa: E402

PERIODS = {"2018-20*": ("2018-01-01", "2020-12-31"), "2021-23": ("2021-01-01", "2023-12-31"),
           "2024-26": ("2024-01-01", "2026-12-31"), "2021-26": ("2021-01-01", "2026-12-31")}
MAIN = ["R", "P", "RP"]
QLO, QHI, MINREL, MINBASE = 1 / 3, 2 / 3, 180, 60
P_CICLO1 = {("c1", 7, "M1"): 0.9474, ("c1", 7, "M2"): 0.4202, ("c1", 7, "M3"): 0.2350, ("c1", 7, "M4"): 0.7380,
            ("c1", 30, "M1"): 0.7515, ("c1", 30, "M2"): 0.5827, ("c1", 30, "M3"): 0.4599, ("c1", 30, "M4"): 0.5967}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def train(d: pd.DataFrame, y: pd.Series, h: int, D: pd.Timestamp) -> dict:
    """Righe t ≥ 2015 con t + h ≤ D − 1 (etichetta nota). λ scelto sull'ultimo 30% (embargo h), poi stima su tutto."""
    m = (d.index >= TRAIN_START) & (d.index + pd.Timedelta(days=h) <= D - pd.Timedelta(days=1)) & y.notna().to_numpy()
    m &= d[PRICE].notna().all(axis=1).to_numpy() & d["T"].notna().to_numpy()
    yy = y[m].to_numpy(float)
    n = len(yy)
    i70 = int(n * 0.7)
    tr, va = slice(0, max(i70 - h, 1)), slice(i70, n)
    T = d.loc[m, "T"].to_numpy()
    out = {"n": n, "base": float(yy.mean()),
           "base_T": {s: (float(yy[T == s].mean()) if (T == s).sum() >= MINBASE else float(yy.mean())) for s in "UDM"}}
    for name, cols in SETS.items():
        X = d.loc[m, cols].to_numpy(float)
        mu, sd = scaler(X[tr])
        Ztr, Zva = scale(X[tr], mu, sd), scale(X[va], mu, sd)
        ll = [logloss(yy[va], pred_logit(fit_logit(Ztr, yy[tr], lam), Zva)) for lam in LAMS]
        lam = LAMS[int(np.argmin(ll))]
        mu, sd = scaler(X)
        out[name] = {"mu": mu, "sd": sd, "lam": lam, "w": fit_logit(scale(X, mu, sd), yy, lam)}
    return out


def predict(mod: dict, d: pd.DataFrame) -> pd.DataFrame:
    r = pd.DataFrame(index=d.index)
    for name, cols in SETS.items():
        a = mod[name]
        r[name] = pred_logit(a["w"], scale(d[cols].to_numpy(float), a["mu"], a["sd"]))
    r["p0"] = mod["base"]
    r["p0c"] = d["T"].map(mod["base_T"]).to_numpy()
    return r


def walk_forward(d: pd.DataFrame, h: int, start: str = "2018-01-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    y = labels(d, h)
    ok = d[PRICE].notna().all(axis=1) & d["T"].notna()
    days = d.index[(d.index >= start) & ok.to_numpy()]
    rows, hist = [], []
    for D in pd.date_range(days[0].replace(day=1), days[-1], freq="MS"):
        mod = train(d, y, h, D)
        rec = {"D": D, "n": mod["n"], "base": mod["base"], **{f"base_{s}": mod["base_T"][s] for s in "UDM"}}
        for name, cols in SETS.items():
            rec[f"lam_{name}"] = mod[name]["lam"]
            rec.update({f"{name}:{c}": mod[name]["w"][1 + i] for i, c in enumerate(cols)})
        hist.append(rec)
        dd = days[(days >= D) & (days < D + pd.offsets.MonthBegin(1))]
        if len(dd):
            rows.append(predict(mod, d.loc[dd]))
    out = pd.concat(rows)
    out["y"] = y.reindex(out.index)
    out["T"], out["V"] = d["T"].reindex(out.index), d["V"].reindex(out.index)
    return out, pd.DataFrame(hist).set_index("D")


def rel_calls(p: pd.Series, T: pd.Series) -> pd.Series:
    """+1 su / −1 giù / 0 incerto: p(t) contro i percentili 67/33 delle previsioni PASSATE (< t) nello stesso stato T
    (minimo 180, altrimenti tutti gli stati; meno di 180 in tutto: incerto). Nessun esito usato."""
    pv, tv = p.to_numpy(), T.to_numpy()
    c = np.zeros(len(pv), int)
    for i in range(len(pv)):
        past = pv[:i][tv[:i] == tv[i]]
        if len(past) < MINREL:
            past = pv[:i]
        if len(past) < MINREL:
            continue
        lo, hi = np.quantile(past, [QLO, QHI])
        c[i] = 1 if pv[i] >= hi else (-1 if pv[i] <= lo else 0)
    return pd.Series(c, index=p.index)


def acc(c, y, m=None):
    m = (c != 0) if m is None else m
    return float(np.mean((c[m] > 0) == (y[m] > 0.5))) if m.any() else np.nan


def auc_shift_p(y, p, h):
    a0 = F1.auc(y, p)
    aa = np.array([F1.auc(np.roll(y, k), p) for k in range(2 * h, len(y) - 2 * h, 3)])
    return a0, float((1 + (aa >= a0 - 1e-12).sum()) / (1 + len(aa)))


def main() -> None:
    d = build()
    say(f"Dataset {d.index[0].date()} → {d.index[-1].date()}; regimi T dal 2015: {d.loc['2015':, 'T'].value_counts().to_dict()}, V: {d.loc['2015':, 'V'].value_counts().to_dict()}")
    reg = F1.w32_regime(d.index)
    rows, pv, verdict, add = [], dict(P_CICLO1), {}, {}
    for h in (7, 30):
        say(f"\n===== ORIZZONTE {h} giorni =====")
        w, hist = walk_forward(d, h)
        calls = {m: rel_calls(w[m], w["T"]) for m in SETS}
        for m in SETS:
            w[f"c_{m}"] = calls[m]
        w.to_csv(HERE / f"prob2_h{h}.csv", float_format="%.5f")
        hist.to_csv(HERE / f"coef2_h{h}.csv", float_format="%.5f")
        pers = np.sign(d[f"r{h}"]).reindex(w.index).fillna(0).astype(int)
        r3 = reg.reindex(w.index).fillna(0).astype(int)
        for pn, (a, b) in PERIODS.items():
            q = w[(w.index >= a) & (w.index <= b) & w["y"].notna()]
            y, n = q["y"].to_numpy(), len(q)
            bs0c, bs0 = float(np.mean((q["p0c"] - y) ** 2)), float(np.mean((q["p0"] - y) ** 2))
            rows.append(dict(h=h, periodo=pn, modello="base condizionata p0c", n_giorni=n, n_indip=round(n / h), base_su=y.mean(),
                             auc=F1.auc(y, q["p0c"]), brier=bs0c, bss_p0c=0.0, bss_p0=1 - bs0c / bs0))
            for m in SETS:
                p, c = q[m].to_numpy(), q[f"c_{m}"].to_numpy()
                cov = c != 0
                pe, w3 = pers.reindex(q.index).to_numpy(), r3.reindex(q.index).to_numpy()
                both = cov & (w3 != 0)
                alo, ahi = F1.boot_ci(lambda i: F1.auc(y[i], p[i]), n, h, 1000)
                e, e0 = (p - y) ** 2, (q["p0c"].to_numpy() - y) ** 2
                blo, bhi = F1.boot_ci(lambda i: 1 - e[i].mean() / e0[i].mean(), n, h, 1000)
                no, nn = F1.nonoverlap(c, y, h)
                rows.append(dict(h=h, periodo=pn, modello=m, n_giorni=n, n_indip=round(n / h), base_su=y.mean(),
                                 auc=F1.auc(y, p), auc_lo=alo, auc_hi=ahi, brier=e.mean(), bss_p0c=1 - e.mean() / e0.mean(), bss_lo=blo,
                                 bss_hi=bhi, bss_p0=1 - e.mean() / bs0, acc=acc(c, y), cop=cov.mean(), acc_nonsovr=no, n_nonsovr=nn,
                                 n_su=int((c > 0).sum()), acc_su=float(np.mean(y[c > 0])) if (c > 0).any() else np.nan,
                                 n_giu=int((c < 0).sum()), acc_giu=float(np.mean(1 - y[c < 0])) if (c < 0).any() else np.nan,
                                 r1_stessi=float(np.mean(y[cov])) if cov.any() else np.nan,
                                 r2_stessi=acc(pe, y, cov & (pe != 0)), acc_su_r2=acc(c, y, cov & (pe != 0)),
                                 r3_stessi=acc(w3, y, both), acc_su_r3=acc(c, y, both), n_r3=int(both.sum())))
        t = pd.DataFrame([r for r in rows if r["h"] == h])
        say(t.round(3).to_string(index=False))
        o = w[(w.index >= "2021-01-01") & w["y"].notna()]
        y = o["y"].to_numpy()
        say("  AUC 2021-26 e p dello sfasamento circolare:")
        for m in MAIN + ["PF", "PFP"]:
            a0, p = auc_shift_p(y, o[m].to_numpy(), h)
            say(f"    {m:<4} AUC {a0:.3f}  p {p:.4f}")
            if m in MAIN:
                pv[("c2", h, m)] = p
        # la politica aggiunge al flusso? ΔAUC (PF+P − PF)
        idx = F1.boot_idx(len(y), h, 1000)
        pa, pb = o["PFP"].to_numpy(), o["PF"].to_numpy()
        dd = np.array([F1.auc(y[i], pa[i]) - F1.auc(y[i], pb[i]) for i in idx])
        dd = dd[np.isfinite(dd)]
        per = {}
        for pn in ("2021-23", "2024-26"):
            a, b = PERIODS[pn]
            q = o[(o.index >= a) & (o.index <= b)]
            per[pn] = (F1.auc(q["y"], q["PF"]), F1.auc(q["y"], q["PFP"]))
        d0 = F1.auc(y, pa) - F1.auc(y, pb)
        p_add = float((1 + (dd <= 0).sum()) / (1 + len(dd)))
        pv[("c2", h, "PFP-PF")] = p_add
        add[h] = dict(per=per, d=d0, lo=float(np.percentile(dd, 2.5)), hi=float(np.percentile(dd, 97.5)), p=p_add)
        say(f"  POLITICA + FLUSSO contro FLUSSO: AUC PF/PF+P 2021-23 {per['2021-23'][0]:.3f}/{per['2021-23'][1]:.3f}, 2024-26 "
            f"{per['2024-26'][0]:.3f}/{per['2024-26'][1]:.3f}; ΔAUC 2021-26 {d0:+.3f} IC95 [{add[h]['lo']:+.3f}, {add[h]['hi']:+.3f}], p(Δ≤0) {p_add:.3f}")
        # idem per RP contro R (informativo)
        ra, rb = o["RP"].to_numpy(), o["R"].to_numpy()
        dr = np.array([F1.auc(y[i], ra[i]) - F1.auc(y[i], rb[i]) for i in idx])
        say(f"  (informativo) RP − R: ΔAUC {F1.auc(y, ra) - F1.auc(y, rb):+.3f} IC95 [{np.nanpercentile(dr, 2.5):+.3f}, {np.nanpercentile(dr, 97.5):+.3f}]")
        # AUC per stato di regime (informativo), calibrazione RP
        for s in "UMD":
            qs = o[o["T"] == s]
            say(f"  stato T={s}: n {len(qs)}, rialzi {qs['y'].mean():.3f}, base p0c media {qs['p0c'].mean():.3f}, AUC R {F1.auc(qs['y'], qs['R']):.3f} P {F1.auc(qs['y'], qs['P']):.3f} RP {F1.auc(qs['y'], qs['RP']):.3f} PF {F1.auc(qs['y'], qs['PF']):.3f}")
        for s in "AB":
            qs = o[o["V"] == s]
            say(f"  stato V={s}: n {len(qs)}, rialzi {qs['y'].mean():.3f}, AUC RP {F1.auc(qs['y'], qs['RP']):.3f}")
        cal = o.groupby(pd.qcut(o["RP"], 5, duplicates="drop"), observed=True).agg(p_media=("RP", "mean"), freq_su=("y", "mean"), n=("y", "size"))
        say("  Calibrazione RP per quintili (2021-26):\n" + cal.round(3).to_string())
        hh = hist[hist.index >= "2021-01-01"]
        cc = [c for c in hh.columns if c.startswith(("RP:", "P:", "R:", "PFP:", "PF:"))]
        co = pd.DataFrame({"media": hh[cc].mean(), "min": hh[cc].min(), "max": hh[cc].max(), "ultimo": hh[cc].iloc[-1],
                           "segno_stabile": (np.sign(hh[cc]) == np.sign(hh[cc].mean())).mean(),
                           "segno_2021_23": np.sign(hh.loc[:"2023-12-31", cc].mean()), "segno_2024_26": np.sign(hh.loc["2024-01-01":, cc].mean())})
        say("  Coefficienti standardizzati (riaddestramenti dal 2021):\n" + co.round(3).to_string())
        say("  λ scelti (conteggi dal 2021):", {m: hh[f"lam_{m}"].value_counts().to_dict() for m in SETS})
        say("  Base rate per regime nell'addestramento (inizio 2021 → ultimo):", hh[["base", "base_U", "base_D", "base_M"]].iloc[[0, -1]].round(3).to_dict("records"))
        g = t.set_index(["periodo", "modello"])
        for m in MAIN:
            ok = {}
            for pn in ("2021-23", "2024-26"):
                r = g.loc[(pn, m)]
                ok[pn] = dict(a=bool(r["auc"] >= 0.55), b=bool(r["bss_p0c"] > 0),
                              c=bool(r["cop"] >= 0.25 and r["acc"] > r["r1_stessi"] and r["acc_su_r2"] > r["r2_stessi"] and r["acc_su_r3"] > r["r3_stessi"]))
            verdict[(h, m)] = ok
    hp = F1.holm(pv)
    say("\n===== HOLM SUI 16 TEST DEI DUE CICLI =====")
    for k in pv:
        say(f"  {k[0]} h={k[1]:>2} {k[2]:<7} p = {pv[k]:.4f}   Holm = {hp[k]:.4f}")
    say("\n===== VERDETTO PREREGISTRATO =====")
    for (h, m), ok in verdict.items():
        abc = all(ok[p][k] for p in ok for k in "abc")
        dk = hp[("c2", h, m)] < 0.05
        say(f"  h={h:>2} {m:<3}: {'FUNZIONA' if abc and dk else ('NON DIMOSTRABILE' if abc else 'NON FUNZIONA')}   {ok}   (d) Holm<0,05: {dk}")
    for h, a in add.items():
        pos = all(v[1] > v[0] for v in a["per"].values())
        v = "AGGIUNGE" if pos and a["lo"] > 0 and hp[("c2", h, "PFP-PF")] < 0.05 else ("NON DIMOSTRABILE" if pos else "NON AGGIUNGE")
        say(f"  h={h:>2} politica sul flusso: {v}   ΔAUC {a['d']:+.3f} [{a['lo']:+.3f}, {a['hi']:+.3f}]")
    pd.DataFrame(rows).to_csv(HERE / "tabella2.csv", index=False, float_format="%.4f")
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
