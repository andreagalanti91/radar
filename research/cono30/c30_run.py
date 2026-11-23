"""Cono a 30 giorni: studio di calibrazione preregistrato (PREREG.md). Solo numpy/pandas.
Uso: python3 research/cono30/c30_run.py  → risultati.txt, previsioni.csv.gz, copertura.csv, affidabilita.csv, brier.csv"""
import math
import os
import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "..", "p2_nuovi", "data", "f_long.csv.gz")
H, BLOCCO, N_PATH, SEME = 30, 10, 2000, 20261123
LIV = [0.10, 0.20, 0.30]
Z50, Z80 = 0.6744897501960817, 1.2815515655446004
PERIODI = [("2018-20", "2018-01-01", "2020-12-31"), ("2021-23", "2021-01-01", "2023-12-31"),
           ("2024-26", "2024-01-01", "2026-12-31"), ("2018-26", "2018-01-01", "2026-12-31")]
EV = [f"{s}{int(x*100)}" for x in LIV for s in ("su", "giu")]


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def carica():
    d = pd.read_csv(DATI, usecols=["date", "open", "high", "low", "close"], parse_dates=["date"])
    return d.sort_values("date").reset_index(drop=True)


def sigma_serie(r):
    """sigma_t^2 = 1/2 media(r^2, 30 g) + 1/2 media(r^2, 365 g), fino a t compreso."""
    r2 = pd.Series(r) ** 2
    return np.sqrt(0.5 * r2.rolling(30).mean() + 0.5 * r2.rolling(365).mean()).values


def previsioni(d):
    c, hi, lo = d["close"].values, d["high"].values, d["low"].values
    n = len(d)
    r = np.full(n, np.nan); u = np.full(n, np.nan); dn = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1]); u[1:] = np.log(hi[1:] / c[:-1]); dn[1:] = np.log(lo[1:] / c[:-1])
    sig = sigma_serie(r)
    sprev = np.r_[np.nan, sig[:-1]]
    zr, zu, zd = r / sprev, u / sprev, dn / sprev
    primo = int(np.argmax(~np.isnan(zr)))          # primo giorno con sigma_{s-1} definita
    # esiti
    fmax = np.full(n, np.nan); fmin = np.full(n, np.nan); fc = np.full(n, np.nan)
    for t in range(n - H):
        fmax[t] = hi[t + 1:t + H + 1].max(); fmin[t] = lo[t + 1:t + H + 1].min(); fc[t] = c[t + H]
    esito = {}
    for x in LIV:
        esito[f"su{int(x*100)}"] = np.where(np.isnan(fmax), np.nan, (fmax >= c * (1 + x)).astype(float))
        esito[f"giu{int(x*100)}"] = np.where(np.isnan(fmin), np.nan, (fmin <= c * (1 - x)).astype(float))
    rng = np.random.default_rng(SEME)
    t0 = int(np.searchsorted(d["date"].values, np.datetime64("2018-01-01")))
    lsu = np.log(1 + np.array(LIV)); lgiu = np.log(1 - np.array(LIV))
    righe = []
    for t in range(t0, n - H):
        s = sig[t]
        Zr, Zu, Zd = zr[primo:t + 1], zu[primo:t + 1], zd[primo:t + 1]
        m = Zr.mean()
        starts = rng.integers(0, len(Zr) - BLOCCO + 1, size=(N_PATH, H // BLOCCO))
        idx = (starts[:, :, None] + np.arange(BLOCCO)[None, None, :]).reshape(N_PATH, H)
        riga = {"date": d["date"].iloc[t], "close": c[t], "sigma": s, "fc": fc[t]}
        for nome, drift in (("a", 0.0), ("b", float(np.nanmean(r[1:t + 1])))):
            pr = (Zr[idx] - m) * s + drift
            cum = np.cumsum(pr, axis=1)
            prev = cum - pr
            mx = (prev + (Zu[idx] - m) * s + drift).max(axis=1)
            mn = (prev + (Zd[idx] - m) * s + drift).min(axis=1)
            q = np.quantile(cum[:, -1], [0.10, 0.25, 0.75, 0.90])
            for k, v in zip(("q10", "q25", "q75", "q90"), q):
                riga[f"{nome}_{k}"] = c[t] * math.exp(v)
            for j, x in enumerate(LIV):
                riga[f"{nome}_su{int(x*100)}"] = float((mx >= lsu[j]).mean())
                riga[f"{nome}_giu{int(x*100)}"] = float((mn <= lgiu[j]).mean())
        sd = s * math.sqrt(H)
        for k, z in (("q10", -Z80), ("q25", -Z50), ("q75", Z50), ("q90", Z80)):
            riga[f"c_{k}"] = c[t] * math.exp(z * sd)
        for j, x in enumerate(LIV):
            riga[f"c_su{int(x*100)}"] = 2 * (1 - phi(lsu[j] / sd))
            riga[f"c_giu{int(x*100)}"] = 2 * (1 - phi(-lgiu[j] / sd))
        # riferimento: frequenza storica incondizionata su finestre concluse entro t
        for e in EV:
            riga[f"ref_{e}"] = float(np.nanmean(esito[e][:t - H + 1]))
            riga[f"y_{e}"] = esito[e][t]
        righe.append(riga)
    return pd.DataFrame(righe)


def ece(p, y):
    o = np.argsort(p, kind="stable")
    tot, n, tab = 0.0, len(p), []
    for g in np.array_split(o, 10):
        pm, ym = p[g].mean(), y[g].mean()
        tot += len(g) / n * abs(pm - ym)
        tab.append((pm, ym, len(g)))
    return tot, tab


def main():
    d = carica()
    P = previsioni(d)
    P.to_csv(os.path.join(QUI, "previsioni.csv.gz"), index=False, float_format="%.6g")
    out = []
    w = out.append
    w(f"Cono 30 giorni · dati {d['date'].iloc[0].date()} → {d['date'].iloc[-1].date()} · previsioni {P['date'].iloc[0].date()} → "
      f"{P['date'].iloc[-1].date()} ({len(P)} giorni) · {N_PATH} cammini, blocchi {BLOCCO} g, seme {SEME}")
    cov_r, br_r, aff_r, esiti = [], [], [], {}
    for m in "abc":
        ok_cov = True
        w(f"\n== Metodo {m} ==")
        for nome, da, a in PERIODI:
            S = P[(P["date"] >= da) & (P["date"] <= a)]
            NO = S.iloc[::H]
            riga = {"metodo": m, "periodo": nome, "n": len(S), "n_indip": len(NO)}
            for liv, lo_, hi_ in ((50, "q25", "q75"), (80, "q10", "q90")):
                dentro = (S["fc"] >= S[f"{m}_{lo_}"]) & (S["fc"] <= S[f"{m}_{hi_}"])
                dn = (NO["fc"] >= NO[f"{m}_{lo_}"]) & (NO["fc"] <= NO[f"{m}_{hi_}"])
                p = dentro.mean()
                riga[f"cop{liv}"] = p; riga[f"se{liv}"] = math.sqrt(p * (1 - p) / len(NO))
                riga[f"cop{liv}_indip"] = dn.mean()
                riga[f"sotto{liv}"] = (S["fc"] < S[f"{m}_{lo_}"]).mean(); riga[f"sopra{liv}"] = (S["fc"] > S[f"{m}_{hi_}"]).mean()
            if nome != "2018-26" and not (0.74 <= riga["cop80"] <= 0.86 and 0.44 <= riga["cop50"] <= 0.56):
                ok_cov = False
            # tocco
            p = np.concatenate([S[f"{m}_{e}"].values for e in EV]); y = np.concatenate([S[f"y_{e}"].values for e in EV])
            ref = np.concatenate([S[f"ref_{e}"].values for e in EV])
            e_, tab = ece(p, y)
            riga["ece_tocco"] = e_
            bs, bref = ((p - y) ** 2).mean(), ((ref - y) ** 2).mean()
            cov_r.append(riga)
            br_r.append({"metodo": m, "periodo": nome, "brier": bs, "brier_rif": bref, "skill": 1 - bs / bref})
            w(f"{nome}: n {len(S)} (indip. {len(NO)}) · cop50 {riga['cop50']:.1%} ±{riga['se50']:.1%} [indip {riga['cop50_indip']:.1%}; "
              f"sotto {riga['sotto50']:.1%} sopra {riga['sopra50']:.1%}] · cop80 {riga['cop80']:.1%} ±{riga['se80']:.1%} "
              f"[indip {riga['cop80_indip']:.1%}; sotto {riga['sotto80']:.1%} sopra {riga['sopra80']:.1%}] · ECE tocco {e_:.1%} · "
              f"Brier {bs:.4f} (rif {bref:.4f}, skill {1 - bs / bref:+.1%})")
            if nome == "2018-26":
                for i, (pm, ym, k) in enumerate(tab):
                    aff_r.append({"metodo": m, "decile": i + 1, "prevista": pm, "osservata": ym, "n": k})
                # per livello
                for e in EV:
                    pe, ye = S[f"{m}_{e}"].values, S[f"y_{e}"].values
                    w(f"   {e}: prevista media {pe.mean():.1%} · osservata {ye.mean():.1%} · ECE {ece(pe, ye)[0]:.1%} · "
                      f"Brier {((pe - ye) ** 2).mean():.4f} (rif {((S[f'ref_{e}'].values - ye) ** 2).mean():.4f})")
                # IC skill con bootstrap a blocchi di 60 giorni
                rng = np.random.default_rng(SEME + 1)
                e1 = np.mean([(S[f"{m}_{e}"].values - S[f"y_{e}"].values) ** 2 for e in EV], axis=0)
                e0 = np.mean([(S[f"ref_{e}"].values - S[f"y_{e}"].values) ** 2 for e in EV], axis=0)
                nb = len(S) // 60
                sk = []
                for _ in range(1000):
                    st = rng.integers(0, len(S) - 60 + 1, nb)
                    ii = (st[:, None] + np.arange(60)[None, :]).ravel()
                    sk.append(1 - e1[ii].mean() / e0[ii].mean())
                lo_, hi_ = np.percentile(sk, [2.5, 97.5])
                w(f"   Brier skill totale IC 95% (blocchi 60 g): {lo_:+.1%} / {hi_:+.1%}")
                esiti[m] = {"cov": ok_cov, "ece": e_, "brier": bs, "cop80": riga["cop80"], "cop50": riga["cop50"]}
        w("   decili (prevista → osservata): " + " · ".join(f"{a_['prevista']:.0%}→{a_['osservata']:.0%}" for a_ in aff_r if a_["metodo"] == m))
    w("\n== Verdetto (criterio PREREG §6) ==")
    passano = []
    for m, e in esiti.items():
        ok = e["cov"] and e["ece"] <= 0.05
        w(f"{m}: copertura per periodo {'OK' if e['cov'] else 'NO'} · ECE tocco {e['ece']:.1%} ({'OK' if e['ece'] <= 0.05 else 'NO'}) · "
          f"Brier {e['brier']:.4f} → {'CALIBRATO' if ok else 'NON calibrato'}")
        if ok:
            passano.append(m)
    if passano:
        best = min(e["brier"] for m, e in esiti.items() if m in passano)
        scelto = [m for m in "cab" if m in passano and esiti[m]["brier"] <= best + 0.001][0]
        w(f"Scelto: {scelto} (cop80 2018-26 {esiti[scelto]['cop80']:.1%}, cop50 {esiti[scelto]['cop50']:.1%})")
    else:
        w("Nessun metodo calibrato: la card NON si fa.")
    pd.DataFrame(cov_r).to_csv(os.path.join(QUI, "copertura.csv"), index=False, float_format="%.4f")
    pd.DataFrame(br_r).to_csv(os.path.join(QUI, "brier.csv"), index=False, float_format="%.5f")
    pd.DataFrame(aff_r).to_csv(os.path.join(QUI, "affidabilita.csv"), index=False, float_format="%.4f")
    txt = "\n".join(out)
    open(os.path.join(QUI, "risultati.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
