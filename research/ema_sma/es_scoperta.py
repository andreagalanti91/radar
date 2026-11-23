"""ema_sma · SCOPERTA (solo dati fino al 31/12/2023) e scelta meccanica (PREREG §5). Scrive scoperta.csv, famiglie.csv, scelta.json.
Con 'perm' : 200 serie rimescolate (caso_scoperta.csv). Con 'rc': White reality check."""
import json, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
import es_lib as L, es_engine as EN

A, B = L.PERIODS["scoperta 2021-23"]
G = L.grammar(); R = EN.rule_arrays(G); N = len(G)
PER = {20: 0, 50: 1, 100: 2, 200: 3}


def sprime(m):
    valid = (m["n"] >= 15) & (m["dd"] >= -0.35)
    return np.where(valid, m["S"], np.minimum(m["S"], 0.0)), valid.to_numpy()


def fam_scores(sp, valid):
    t = pd.DataFrame(dict(fam=G["fam"], sp=sp, v=valid))
    f = t.groupby("fam").agg(score=("sp", "median"), n=("sp", "size"), valid=("v", "mean"), best=("sp", "max"))
    f["ammessa"] = f["valid"] >= 0.5
    return f.sort_values("score", ascending=False)


def neighbours(sub):
    """Per ogni membro della famiglia: indici (posizioni in sub) dei vicini a una coordinata di distanza."""
    rows = sub[["ent", "xtype", "xtf", "xkind", "xpar", "xn"]].to_records(index=False)
    out = []
    for a in rows:
        nb = []
        for j, b in enumerate(rows):
            diff = [a[k] != b[k] for k in ("ent", "xtf", "xkind", "xpar", "xn")]
            if sum(diff) != 1: continue
            if diff[0] or diff[2] or diff[1]: nb.append(j); continue
            if diff[3]:
                if a["xtype"] == "C" and abs(PER[int(a["xpar"])] - PER[int(b["xpar"])]) == 1: nb.append(j)
                elif a["xtype"] == "X": nb.append(j)
                elif a["xtype"] == "A" and abs(float(a["xpar"]) - float(b["xpar"])) == 1: nb.append(j)
            elif diff[4] and abs(int(a["xn"]) - int(b["xn"])) == 1: nb.append(j)
        out.append(nb)
    return out


def choose(sp, valid):
    f = fam_scores(sp, valid); ok = f[f["ammessa"]]
    fam = (ok if len(ok) else f).index[0]
    sub = G[G["fam"] == fam]; s = sp[sub.index]; v = valid[sub.index]
    nbs = neighbours(sub)
    ns = np.array([np.median(np.r_[s[i], s[nb]]) for i, nb in enumerate(nbs)])
    cand = pd.DataFrame(dict(rule=sub.index, ns=ns, s=s, v=v)).sort_values(["v", "ns", "s"], ascending=False)
    return f, fam, int(cand.iloc[0]["rule"]), cand, bool(len(ok))


def real(cut=B):
    a = L.load_4h(cut); S = EN.signals(a)
    i0 = a.index.searchsorted(pd.Timestamp(EN.START)); isplit = a.index.searchsorted(pd.Timestamp(A))
    E1, d1, T1, st = EN.run(S, R, i0, isplit)
    E2, d2, T2, _ = EN.run(S, R, isplit, len(a), st)
    T1 = T1[T1[:, 2] < isplit - 1] if len(T1) else T1          # le posizioni aperte al confine proseguono nel secondo tratto
    return a, S, np.vstack([E1, E2]), d1.append(d2), np.vstack([T1, T2]), st, isplit


def one_perm(seed):
    a = L.load_4h(B); S0, st, isplit = one_perm.ctx
    ap = EN.permute(a, A, B, np.random.default_rng(seed)); S = EN.signals(ap)
    E, d, T, _ = EN.run(S, R, isplit, len(ap), st)
    base = one_perm.base
    m = EN.metrics(np.vstack([base, E]), pd.DatetimeIndex([pd.Timestamp(A) - pd.Timedelta(days=1)]).append(d), T, ap.index, A, B, N)
    sp, v = sprime(m); f = fam_scores(sp, v); ok = f[f["ammessa"]]
    bhm = EN.bh(S, A, B)
    return dict(seed=seed, max_sp=float(sp.max()), p95_sp=float(np.quantile(sp, 0.95)), med_sp=float(np.median(sp)),
                best_fam=float(ok["score"].max()) if len(ok) else float("nan"), best_fam_any=float(f["score"].max()),
                n_valid=int(v.sum()), pos=float((m["cagr"] > 0).mean()), bh_S=bhm["S"], beat_bh=float((m["S"] > bhm["S"]).mean()))


if __name__ == "__main__":
    t0 = time.time()
    a, S, E, days, T, st, isplit = real()
    m = EN.metrics(E, days, T, a.index, A, B, N)
    sp, valid = sprime(m); m["sp"], m["valid"] = sp, valid
    if "perm" in sys.argv:
        one_perm.ctx = (None, st, isplit); one_perm.base = E[days < A][-1][None, :]
        with Pool(4) as p:
            res = p.map(one_perm, range(1000, 1200), chunksize=5)
        pd.DataFrame(res).to_csv(L.HERE / "caso_scoperta.csv", index=False); print("perm", round(time.time() - t0)); sys.exit()
    bhm = EN.bh(S, A, B)
    f, fam, rule, cand, ammessa = choose(sp, valid)
    out = pd.concat([G, m], axis=1); out.to_csv(L.HERE / "scoperta.csv", index_label="rule")
    f.to_csv(L.HERE / "famiglie.csv"); cand.to_csv(L.HERE / "candidati_famiglia.csv", index=False)
    u = G[(G.side == "INV") & (G.reg == "G1") & (G.ent == "E0") & (G.xtf == "4h") & (G.xtype == "C") & (G.xkind == "EMA") & (G.xpar == "50") & (G.xn == 2)].index[0]
    json.dump(dict(famiglia=fam, ammessa=ammessa, regola=rule, descr=G.loc[rule].to_dict() | {}, utente=int(u), punteggio_famiglia=float(f.loc[fam, "score"]),
                   bh_scoperta=bhm), open(L.HERE / "scelta.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print("tempo", round(time.time() - t0), "s | regole", N, "| valide", int(valid.sum()), "| CAGR>0", round(float((m.cagr > 0).mean()), 3),
          "| S>B&H", round(float((m.S > bhm["S"]).mean()), 3))
    print("B&H scoperta", {k: round(v, 3) for k, v in bhm.items()})
    print(f.head(12).round(3).to_string())
    print("SCELTA famiglia", fam, "ammessa", ammessa, "regola", rule, G.loc[rule].to_dict())
    print(out.loc[[rule, u], ["side", "reg", "ent", "xtf", "xkind", "xpar", "xn", "fin", "cagr", "dd", "S", "n", "wr", "valid"]].round(3).to_string())
    print(cand.head(8).round(3).to_string())
    print("prime 15 regole valide:"); print(out[out.valid].sort_values("S", ascending=False).head(15)[["side", "reg", "ent", "xtf", "xtype", "xkind", "xpar", "xn", "fin", "cagr", "dd", "S", "n", "wr"]].round(3).to_string())
    if "rc" in sys.argv:
        e = E[days >= pd.Timestamp(A) - pd.Timedelta(days=1)].astype(float); lr = np.diff(np.log(e), axis=0)[:, valid]
        cd = S["daily"]["close"]; b = np.diff(np.log(cd[(cd.index >= pd.Timestamp(A) - pd.Timedelta(days=1)) & (cd.index <= B)].to_numpy()))
        rng = np.random.default_rng(7); n = len(lr); res = {}
        for name, x in (("zero", lr), ("bh", lr - b[:, None])):
            mu = x.mean(0); stat = np.sqrt(n) * mu.max(); cnt = 0; bs = []
            for _ in range(2000):
                ix = np.empty(n, int); ix[0] = rng.integers(n); jump = rng.random(n) < 1 / 10; rj = rng.integers(n, size=n)
                for q in range(1, n): ix[q] = rj[q] if jump[q] else (ix[q - 1] + 1) % n
                bs.append(np.sqrt(n) * (x[ix].mean(0) - mu).max())
            res[name] = dict(stat=float(stat), p=float((np.array(bs) >= stat).mean()), best_rule=int(np.flatnonzero(valid)[mu.argmax()]),
                             p_scelta=float((np.array(bs) >= np.sqrt(n) * mu[np.flatnonzero(valid) == rule].max()).mean()) if valid[rule] else None)
        json.dump(res, open(L.HERE / "rc_scoperta.json", "w"), indent=1); print("White RC", res)
