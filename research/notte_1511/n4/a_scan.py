"""N4 · Parte A: probabilità condizionate (PREREG.md). Scansione delle celle 1–3 variabili, bootstrap a blocchi, BH, conferma OOS,
placebo a sfasamento circolare. Uso: python a_scan.py [th thd tag]  → a_celle<tag>.csv, a_top<tag>.csv, a_log<tag>.txt
"""
from __future__ import annotations

import itertools
import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from n4_data import BASE, VARS, build  # noqa: E402

HS = (7, 14, 30)
B, L = 2000, 30
IS_END, OOS_START = "2023-12-31", "2024-01-01"
NPLAC = 50


def ncdf(z):
    return 0.5 * (1 + np.vectorize(erf)(np.asarray(z) / sqrt(2)))


def cells(df: pd.DataFrame):
    names, cols = [], []
    for k in (1, 2, 3):
        for combo in itertools.combinations(VARS, k):
            bases = [BASE.get(v, v) for v in combo]
            if len(set(bases)) < k:
                continue
            sub = df[list(combo)]
            ok = sub.notna().all(axis=1).to_numpy()
            keys = sub.fillna("NA").astype(str).to_numpy()
            keys = np.array(["|".join(r) for r in keys])
            for lv in sorted(set(keys[ok])):
                names.append(" & ".join(f"{v}={x}" for v, x in zip(combo, lv.split("|"))))
                cols.append(ok & (keys == lv))
    return names, np.column_stack(cols)


def greedy(ix: np.ndarray, step: int) -> int:
    n, last = 0, -10**9
    for i in ix:
        if i - last >= step:
            n += 1; last = i
    return n


def n_ind(M: np.ndarray, mask: np.ndarray, step: int = 7) -> np.ndarray:
    out = np.zeros(M.shape[1], int)
    Mm = M & mask[:, None]
    for j in range(M.shape[1]):
        out[j] = greedy(np.flatnonzero(Mm[:, j]), step)
    return out


def boot_w(n: int, rng) -> np.ndarray:
    """Pesi del bootstrap a blocchi mobili: quante volte ogni giorno entra nella replica (n × B)."""
    nb = int(np.ceil(n / L))
    st = rng.integers(0, n - L + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(B, -1)[:, :n]
    W = np.zeros((n, B), np.float32)
    for b in range(B):
        W[:, b] = np.bincount(idx[b], minlength=n)
    return W


def stats(M: np.ndarray, R: np.ndarray, W: np.ndarray):
    """Per ogni orizzonte: n, media, P(>0), eccesso su base, z da errore bootstrap per media e P."""
    out = {}
    Mf = M.astype(np.float32)
    for k, h in enumerate(HS):
        r = R[:, k]
        v = ~np.isnan(r)
        rv = np.where(v, r, 0).astype(np.float32)
        pv = (rv > 0).astype(np.float32)
        vf = v.astype(np.float32)
        n = Mf.T @ vf
        mean = (Mf.T @ rv) / np.maximum(n, 1)
        pos = (Mf.T @ pv) / np.maximum(n, 1)
        bm, bp = rv[v].mean(), pv[v].mean()
        Wv = W * vf[:, None]
        cn = Mf.T @ Wv
        cm = (Mf.T @ (Wv * rv[:, None])) / np.maximum(cn, 1)
        cp = (Mf.T @ (Wv * pv[:, None])) / np.maximum(cn, 1)
        tot = Wv.sum(0)
        bmb = (Wv * rv[:, None]).sum(0) / tot
        bpb = (Wv * pv[:, None]).sum(0) / tot
        ex_b, exp_b = cm - bmb[None, :], cp - bpb[None, :]
        se, sep = ex_b.std(1), exp_b.std(1)
        lo_m, hi_m = np.percentile(cm, [2.5, 97.5], axis=1)
        lo_p, hi_p = np.percentile(cp, [2.5, 97.5], axis=1)
        out[h] = dict(n=n, mean=mean, pos=pos, base_m=bm, base_p=bp, ex=mean - bm, exp=pos - bp,
                      z=(mean - bm) / np.maximum(se, 1e-9), zp=(pos - bp) / np.maximum(sep, 1e-9),
                      lo_m=lo_m, hi_m=hi_m, lo_p=lo_p, hi_p=hi_p)
    return out


def bh(p: np.ndarray, q: float) -> np.ndarray:
    m = len(p)
    o = np.argsort(p)
    thr = q * np.arange(1, m + 1) / m
    ok = p[o] <= thr
    k = np.max(np.flatnonzero(ok)) + 1 if ok.any() else 0
    res = np.zeros(m, bool)
    res[o[:k]] = True
    return res


def pipeline(M, R, dates, elig, W_is, W_oos):
    ism = dates <= pd.Timestamp(IS_END)
    S_is = stats(M[ism][:, elig], R[ism], W_is)
    S_oos = stats(M[~ism][:, elig], R[~ism], W_oos)
    rows = []
    for h in HS:
        a, b = S_is[h], S_oos[h]
        for side in ("long", "short"):
            sg = 1 if side == "long" else -1
            z = sg * a["z"]
            p = 1 - ncdf(z)
            for j in range(len(z)):
                rows.append((h, side, j, p[j], z[j], sg * b["z"][j]))
    T = pd.DataFrame(rows, columns=["h", "side", "j", "p_is", "z_is", "z_oos"])
    T["fdr_is"] = bh(T["p_is"].to_numpy(), 0.10)
    return T, S_is, S_oos


def confirm(T, S_oos):
    """Criteri OOS (PREREG) su tutte le righe; prereg = BH-IS e conferma OOS; nominale = p IS < 0,05 e conferma OOS (secondaria)."""
    C = T.copy()
    pos = np.array([S_oos[h]["pos"][j] for h, j in zip(C.h, C.j)])
    mean = np.array([S_oos[h]["mean"][j] for h, j in zip(C.h, C.j)])
    basep = np.array([S_oos[h]["base_p"] for h in C.h])
    C["p_oos"] = 1 - ncdf(C["z_oos"].to_numpy())
    lg = C.side.to_numpy() == "long"
    C["oos_ok"] = (C.p_oos < 0.05) & np.where(lg, pos > basep, (mean < 0) & (pos < 0.5))
    C["conf"] = C.fdr_is & C.oos_ok
    C["nom"] = (C.p_is < 0.05) & C.oos_ok
    C["score"] = np.minimum(C.z_is, C.z_oos)
    C["fdr_oos"] = False
    if C.conf.any():
        C.loc[C.conf, "fdr_oos"] = bh(C.loc[C.conf, "p_oos"].to_numpy(), 0.10)
    return C


def summ(C):
    d = dict(cand=int(C.fdr_is.sum()), conf=int(C.conf.sum()))
    for sd in ("long", "short"):
        x = C[(C.side == sd) & C.nom]
        d[f"nom_{sd}"] = len(x)
        d[f"best_{sd}"] = float(x.score.max()) if len(x) else 0.0
    return d


def main(th=0.43, thd=0.5, tag="", placebo=True):
    df, _ = build(th, thd)
    df = df[df.index >= "2021-01-01"]
    names, M = cells(df)
    R = df[[f"r{h}" for h in HS]].to_numpy(float)
    dates = df.index
    ism = dates <= pd.Timestamp(IS_END)
    nf, ni, no = n_ind(M, np.ones(len(df), bool)), n_ind(M, ism), n_ind(M, ~ism)
    elig = (nf >= 40) & (ni >= 15) & (no >= 15)
    rng = np.random.default_rng(15112026)
    W_is, W_oos = boot_w(ism.sum(), rng), boot_w((~ism).sum(), rng)
    T, S_is, S_oos = pipeline(M, R, dates, elig, W_is, W_oos)
    C = confirm(T, S_oos)
    en = np.array(names)[elig]
    RS = summ(C)
    log = [f"celle totali {len(names)}, ammissibili {elig.sum()}, test IS {len(T)}, candidati BH-IS {RS['cand']}, "
           f"confermati OOS (preregistrato) {RS['conf']}, + BH-OOS {int(C.fdr_oos.sum())}",
           f"secondaria (p IS<0,05 nominale + conferma OOS): long {RS['nom_long']} (miglior min z {RS['best_long']:.2f}), "
           f"short {RS['nom_short']} (miglior min z {RS['best_short']:.2f})"]
    # tabella completa delle celle ammissibili
    S_full = stats(M[:, elig], R, boot_w(len(df), rng))
    rows = []
    for k, nm in enumerate(en):
        for h in HS:
            a, b, f_ = S_is[h], S_oos[h], S_full[h]
            rows.append(dict(cella=nm, h=h, n_ind7=int(nf[elig][k]), n=int(f_["n"][k]), P=f_["pos"][k], P_lo=f_["lo_p"][k], P_hi=f_["hi_p"][k],
                             media=f_["mean"][k], m_lo=f_["lo_m"][k], m_hi=f_["hi_m"][k], base_P=f_["base_p"], base_m=f_["base_m"],
                             P_is=a["pos"][k], m_is=a["mean"][k], z_is=a["z"][k], P_oos=b["pos"][k], m_oos=b["mean"][k], z_oos=b["z"][k],
                             n_is=int(a["n"][k]), n_oos=int(b["n"][k])))
    A = pd.DataFrame(rows)
    use = "conf" if C.conf.any() else "nom"
    conf = C[C[use]].copy()
    conf["cella"] = en[conf.j.astype(int)]
    A = A.merge(conf[["cella", "h", "side", "conf", "nom", "fdr_oos", "score"]], on=["cella", "h"], how="left")
    A.to_csv(HERE / f"a_celle{tag}.csv", index=False, float_format="%.5g")
    top = []
    for side in ("long", "short"):
        s = conf[conf.side == side].sort_values("score", ascending=False)
        seen = set()
        for _, r in s.iterrows():
            if r.cella in seen:
                continue
            seen.add(r.cella)
            top.append(dict(side=side, cella=r.cella, h=int(r.h), score=r.score, z_is=r.z_is, z_oos=r.z_oos,
                            prereg=bool(r.conf), bh_oos=bool(r.fdr_oos)))
            if len(seen) == 5:
                break
    TOP = pd.DataFrame(top)
    TOP.to_csv(HERE / f"a_top{tag}.csv", index=False, float_format="%.4g")
    # placebo globale
    if placebo:
        pl = []
        prng = np.random.default_rng(7)
        for it in range(NPLAC):
            k = int(prng.integers(180, len(df) - 180))
            Ms = np.roll(M, k, axis=0)
            nf_, ni_, no_ = n_ind(Ms, np.ones(len(df), bool)), n_ind(Ms, ism), n_ind(Ms, ~ism)
            el = (nf_ >= 40) & (ni_ >= 15) & (no_ >= 15)
            Tp, _, So = pipeline(Ms, R, dates, el, W_is, W_oos)
            Cp = confirm(Tp, So)
            pl.append(dict(shift=k, **summ(Cp)))
        P = pd.DataFrame(pl)
        P.to_csv(HERE / f"a_placebo{tag}.csv", index=False)
        log.append(f"placebo ({NPLAC} sfasamenti circolari): candidati BH-IS mediana {P.cand.median():.0f}, 95° {P.cand.quantile(.95):.0f}; "
                   f"confermati 95° {P.conf.quantile(.95):.0f} (reali {RS['conf']})")
        for sd in ("long", "short"):
            log.append(f"  {sd}: celle nominali placebo mediana {P[f'nom_{sd}'].median():.0f}, 95° {P[f'nom_{sd}'].quantile(.95):.0f} "
                       f"(reali {RS[f'nom_{sd}']}, quota placebo ≥ reali {np.mean(P[f'nom_{sd}'] >= RS[f'nom_{sd}']):.2f}); "
                       f"miglior min z placebo mediana {P[f'best_{sd}'].median():.2f}, 95° {P[f'best_{sd}'].quantile(.95):.2f} "
                       f"(reale {RS[f'best_{sd}']:.2f}, quota ≥ {np.mean(P[f'best_{sd}'] >= RS[f'best_{sd}']):.2f})")
    txt = "\n".join(log) + "\n\nTOP\n" + TOP.to_string()
    (HERE / f"a_log{tag}.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a:
        main(float(a[0]), float(a[1]), a[2], placebo=len(a) > 3)
    else:
        main()
