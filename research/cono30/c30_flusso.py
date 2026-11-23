"""Addendum (esplorativo): cono con deriva condizionata al flusso perp (d1 segno, d2 segno e forza) contro il metodo (b).
Uso: python3 research/cono30/c30_flusso.py → risultati_flusso.txt"""
import math
import os
import numpy as np
import pandas as pd
from c30_run import BLOCCO, DATI, EV, H, LIV, N_PATH, QUI, SEME, ece, sigma_serie

PER = [("2021-23", "2021-01-01", "2023-12-31"), ("2024-26", "2024-01-01", "2026-12-31"), ("2021-26", "2021-01-01", "2026-12-31")]


def main():
    d = pd.read_csv(DATI, usecols=["date", "open", "high", "low", "close", "pf14z"], parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    c, hi, lo = d["close"].values, d["high"].values, d["low"].values
    n = len(d)
    flow = d["pf14z"].rolling(3, min_periods=2).mean().shift(1).values
    r = np.full(n, np.nan); u = np.full(n, np.nan); dn = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1]); u[1:] = np.log(hi[1:] / c[:-1]); dn[1:] = np.log(lo[1:] / c[:-1])
    sig = sigma_serie(r); sprev = np.r_[np.nan, sig[:-1]]
    zr, zu, zd = r / sprev, u / sprev, dn / sprev
    primo = int(np.argmax(~np.isnan(zr)))
    fwd = np.full(n, np.nan); fwd[:n - H] = np.log(c[H:] / c[:-H]) / H
    st1 = np.where(np.isnan(flow), -1, (flow > 0).astype(int))
    st2 = np.where(np.isnan(flow), -1, np.where(flow > 0.5, 2, np.where(flow < -0.5, 0, 1)))
    fmax = np.full(n, np.nan); fmin = np.full(n, np.nan)
    for t in range(n - H):
        fmax[t] = hi[t + 1:t + H + 1].max(); fmin[t] = lo[t + 1:t + H + 1].min()
    rng = np.random.default_rng(SEME)
    t0 = int(np.searchsorted(d["date"].values, np.datetime64("2021-01-01")))
    lsu = np.log(1 + np.array(LIV)); lgiu = np.log(1 - np.array(LIV))
    righe = []
    for t in range(t0, n - H):
        s = sig[t]
        Zr, Zu, Zd = zr[primo:t + 1], zu[primo:t + 1], zd[primo:t + 1]
        m = Zr.mean()
        starts = rng.integers(0, len(Zr) - BLOCCO + 1, size=(N_PATH, H // BLOCCO))
        idx = (starts[:, :, None] + np.arange(BLOCCO)[None, None, :]).reshape(N_PATH, H)
        base = float(np.nanmean(r[1:t + 1]))
        drifts = {"b": base}
        for nome, st in (("d1", st1), ("d2", st2)):
            past = (st[:t - H + 1] == st[t]) & ~np.isnan(fwd[:t - H + 1])
            drifts[nome] = float(fwd[:t - H + 1][past].mean()) if st[t] >= 0 and past.sum() >= 60 else base
        riga = {"date": d["date"].iloc[t], "fc": c[t + H], "flow": flow[t]}
        pr0 = (Zr[idx] - m) * s; cum0 = np.cumsum(pr0, axis=1); prev0 = cum0 - pr0
        mx0, mn0 = prev0 + (Zu[idx] - m) * s, prev0 + (Zd[idx] - m) * s
        k = np.arange(H)[None, :]
        for nome, dr in drifts.items():
            mx = (mx0 + dr * (k + 1)).max(axis=1); mn = (mn0 + dr * (k + 1)).min(axis=1)
            q = np.quantile(cum0[:, -1] + dr * H, [0.10, 0.25, 0.75, 0.90])
            for kk, v in zip(("q10", "q25", "q75", "q90"), q):
                riga[f"{nome}_{kk}"] = c[t] * math.exp(v)
            riga[f"{nome}_drift30"] = dr * H
            for j, x in enumerate(LIV):
                riga[f"{nome}_su{int(x*100)}"] = float((mx >= lsu[j]).mean())
                riga[f"{nome}_giu{int(x*100)}"] = float((mn <= lgiu[j]).mean())
        for j, x in enumerate(LIV):
            riga[f"y_su{int(x*100)}"] = float(fmax[t] >= c[t] * (1 + x)); riga[f"y_giu{int(x*100)}"] = float(fmin[t] <= c[t] * (1 - x))
        righe.append(riga)
    P = pd.DataFrame(righe)
    out = []; w = out.append
    w(f"Variante flusso (esplorativa) · previsioni {P['date'].iloc[0].date()} → {P['date'].iloc[-1].date()} ({len(P)} giorni)")
    R = {}
    for m in ("b", "d1", "d2"):
        w(f"\n== {m} ==")
        for nome, da, a in PER:
            S = P[(P["date"] >= da) & (P["date"] <= a)]
            c50 = ((S["fc"] >= S[f"{m}_q25"]) & (S["fc"] <= S[f"{m}_q75"])).mean()
            c80 = ((S["fc"] >= S[f"{m}_q10"]) & (S["fc"] <= S[f"{m}_q90"])).mean()
            p = np.concatenate([S[f"{m}_{e}"].values for e in EV]); y = np.concatenate([S[f"y_{e}"].values for e in EV])
            bs = ((p - y) ** 2).mean(); ec = ece(p, y)[0]
            R[(m, nome)] = {"c50": c50, "c80": c80, "bs": bs, "ece": ec}
            w(f"{nome}: n {len(S)} · cop50 {c50:.1%} · cop80 {c80:.1%} · ECE tocco {ec:.1%} · Brier {bs:.4f} · deriva media a 30 g {S[f'{m}_drift30'].mean():+.1%} "
              f"(min {S[f'{m}_drift30'].min():+.1%}, max {S[f'{m}_drift30'].max():+.1%})")
    w("\n== Criterio dell'addendum ==")
    rng2 = np.random.default_rng(SEME + 2)
    passano = []
    for m in ("d1", "d2"):
        meglio = all(R[(m, pn)]["bs"] < R[("b", pn)]["bs"] for pn in ("2021-23", "2024-26"))
        cal = all(0.74 <= R[(m, pn)]["c80"] <= 0.86 and 0.44 <= R[(m, pn)]["c50"] <= 0.56 for pn in ("2021-23", "2024-26")) and R[(m, "2021-26")]["ece"] <= 0.05
        e1 = np.mean([(P[f"{m}_{e}"].values - P[f"y_{e}"].values) ** 2 for e in EV], axis=0)
        e0 = np.mean([(P[f"b_{e}"].values - P[f"y_{e}"].values) ** 2 for e in EV], axis=0)
        df = []
        for _ in range(1000):
            st = rng2.integers(0, len(P) - 60 + 1, len(P) // 60)
            ii = (st[:, None] + np.arange(60)[None, :]).ravel()
            df.append((e1[ii] - e0[ii]).mean())
        l95, h95 = np.percentile(df, [2.5, 97.5])
        w(f"{m}: Brier − Brier(b): 2021-23 {R[(m,'2021-23')]['bs'] - R[('b','2021-23')]['bs']:+.4f} · 2024-26 {R[(m,'2024-26')]['bs'] - R[('b','2024-26')]['bs']:+.4f} · "
          f"2021-26 {(e1 - e0).mean():+.4f} (IC 95% {l95:+.4f} / {h95:+.4f}) · migliora in entrambi: {'SÌ' if meglio else 'NO'} · calibrata: {'SÌ' if cal else 'NO'} "
          f"→ {'ADOTTABILE' if meglio and cal else 'NON adottata'}")
        if meglio and cal:
            passano.append(m)
    w("Esito: " + (f"adottabile {min(passano, key=lambda m: R[(m, '2021-26')]['bs'])}" if passano else "nessuna variante passa: la card usa il metodo base (b); flusso solo come riga descrittiva."))
    txt = "\n".join(out)
    open(os.path.join(QUI, "risultati_flusso.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
