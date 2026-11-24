"""tradera_test · rilevatore a regole del metodo di TraderA (fase 1). Solo numpy/pandas, nessun dato futuro.

Lato long (linea ribassista sui massimi); il lato short è lo stesso calcolo sul prezzo con il segno cambiato
(linea rialzista sui minimi). Decisioni alla chiusura della barra t, ingresso all'apertura di t+1.

1. Pivot: la barra i è un massimo se il suo massimo è il più alto delle barre i−PIV…i+PIV; noto alla chiusura di i+PIV.
2. Linea: A = il massimo-pivot più alto nelle WIN barre prima di B (e più alto di tutto ciò che c'è fra A e B);
   B = il pivot successivo (almeno GAP barre dopo A, più basso di A) che rende la linea A→B meno inclinata (inviluppo:
   nessun massimo-pivot fra A e B sta sopra la linea). Valida se nessuna chiusura fra A e la barra corrente è sopra la linea.
   Scade EXP barre dopo B.
3. Rottura: prima chiusura sopra la linea. Slancio: dopo la rottura il massimo deve superare la linea di MOM·ATR.
4. Ritest (entro K barre dalla rottura, dopo lo slancio): minimo ≤ linea + TOL·ATR e chiusura ≥ linea → segnale.
   Invalidazione: chiusura < linea − INV·ATR → setup chiuso (e "piano speculare", vedi 7).
5. Stop: minimo delle BASE barre prima della rottura (la base da cui parte la rottura) − MARG.
6. Obiettivo: il punto A (massimo precedente significativo da cui parte la linea). Filtro: R:R stimato ≥ RRMIN.
   Confluenza: EMA50 o EMA200 giornaliera entro CF·ATR dalla linea alla barra del ritest.
7. Piano speculare (g): se dopo lo slancio la chiusura torna sotto linea − INV·ATR, short all'apertura dopo; stop = massimo
   delle BASE barre precedenti + MARG; obiettivo = minimo fra B e la rottura (base della rottura).
Zone orizzontali: pivot settimanali (k = ZK) uniti in cluster se distano meno di ZW (in log) dal cluster; zona = [min, max]
dei punti, almeno ZN tocchi.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

P = dict(PIV=10, WIN=250, GAP=20, EXP=250, MOM=1.5, TOL=0.5, INV=1.0, K=40, CF=1.0, BASE=3, MARG=0.001, RRMIN=2.0,
         ZK=3, ZW=0.10, ZN=2)


def atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    H, L, C = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    pc = np.r_[C[0], C[:-1]]
    tr = np.maximum(H - L, np.maximum(abs(H - pc), abs(L - pc)))
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().to_numpy()


def emas(df: pd.DataFrame) -> dict:
    c = df["close"]
    return {n: c.ewm(span=n, adjust=False).mean().to_numpy() for n in (12, 26, 50, 200)}


def _pivots(x: np.ndarray, k: int) -> np.ndarray:
    n = len(x)
    out = np.zeros(n, bool)
    for i in range(k, n - k):
        if x[i] == x[i - k:i + k + 1].max():
            out[i] = True
    return out


def detect(df: pd.DataFrame, p: dict | None = None, sides=(1, -1), log_lines: bool = False) -> dict:
    """Ritorna dict(signals=[...], flips=[...], lines=[...], pending=[...]) con indici di barra e prezzi reali."""
    p = {**P, **(p or {})}
    O, H, L, C = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    A = atr(df)
    E = emas(df)
    n = len(C)
    sigs, flips, lines, pend = [], [], [], []
    brk = {1: np.full(n, np.nan), -1: np.full(n, np.nan)}   # valore della linea rotta mentre il setup è aperto (per WV1)
    for s in sides:
        Hs, Ls, Cs = (H, L, C) if s > 0 else (-L, -H, -C)
        piv = _pivots(Hs, p["PIV"])
        pidx = np.flatnonzero(piv)
        line = None       # dict(iA, pA, iB, pB, m)
        st = None         # setup dopo la rottura
        rebuild = False   # dopo la fine di un setup si ricostruisce la linea con i pivot già confermati
        for t in range(n):
            i = t - p["PIV"]
            if rebuild and st is None and line is None and i >= 0:
                conf = pidx[pidx <= i]
                i = int(conf[-1]) if len(conf) else -1
            rebuild = st is not None
            # --- 1-2. nuova linea dal pivot confermato oggi (o dall'ultimo confermato, dopo un setup)
            if st is None and i >= 0 and piv[i]:
                cand = pidx[(pidx >= i - p["WIN"]) & (pidx <= i - p["GAP"])]
                if len(cand):
                    iA = int(cand[np.argmax(Hs[cand])])
                    pA = Hs[iA]
                    if pA > Hs[i] and pA >= Hs[iA:i + 1].max():
                        bs = pidx[(pidx >= iA + p["GAP"]) & (pidx <= i)]
                        bs = bs[Hs[bs] < pA]
                        if len(bs):
                            m = (Hs[bs] - pA) / (bs - iA)
                            iB = int(bs[np.argmax(m)])
                            mm = float(m.max())
                            seg = np.arange(iA + 1, t + 1)
                            if np.all(Cs[seg] <= pA + mm * (seg - iA) + 1e-12):
                                new = dict(iA=iA, pA=pA, iB=iB, pB=Hs[iB], m=mm, side=s, t0=t)
                                if line is None or (new["iA"], new["iB"]) != (line["iA"], line["iB"]):
                                    line = new
                                    if log_lines:
                                        lines.append(dict(line))
            if line is not None and st is None:
                lv = line["pA"] + line["m"] * (t - line["iA"])
                if t - line["iB"] > p["EXP"]:
                    line = None
                elif Cs[t] > lv:
                    b0 = max(0, t - p["BASE"])
                    st = dict(line, ib=t, lv_b=lv, base=float(Ls[b0:t].min()), mx=Hs[t], slancio=False,
                              base_tgt=float(Ls[line["iB"]:t + 1].min()))
                    line = None
                    continue
            if st is not None:
                lv = st["pA"] + st["m"] * (t - st["iA"])
                a = A[t]
                if t - st["ib"] > p["K"]:
                    st = None
                    continue
                brk[s][t] = s * lv
                if st["slancio"] and Cs[t] < lv - p["INV"] * a:
                    # piano speculare: lato opposto, stop oltre l'estremo delle ultime BASE barre, obiettivo la base della rottura
                    hi = float(Hs[max(0, t - p["BASE"] + 1):t + 1].max())
                    ftgt, fstop = s * st["base_tgt"], s * (hi + abs(hi) * p["MARG"])
                    if (ftgt - C[t]) * (-s) > 0 and (fstop - C[t]) * (-s) < 0:   # obiettivo e stop dalla parte giusta
                        flips.append(dict(t=t, side=-s, lv=s * lv, stop=fstop, tgt=ftgt, close=C[t], ib=st["ib"],
                                          rr=(ftgt - C[t]) / (C[t] - fstop)))
                    st = None
                    continue
                if st["slancio"] and Ls[t] <= lv + p["TOL"] * a and Cs[t] >= lv:
                    stop = st["base"] - abs(st["base"]) * p["MARG"]
                    tgt = st["pA"]
                    rr = (tgt - Cs[t]) / (Cs[t] - stop) if Cs[t] > stop else -1
                    conf = min(abs(s * E[50][t] - lv), abs(s * E[200][t] - lv)) <= p["CF"] * a
                    sigs.append(dict(t=t, side=s, lv=s * lv, stop=s * stop, tgt=s * tgt, rr=rr, conf=bool(conf),
                                     ok=bool(rr >= p["RRMIN"]), close=C[t], ib=st["ib"], iA=st["iA"], iB=st["iB"],
                                     pA=s * st["pA"], pB=s * st["pB"], atr=a,
                                     e50=E[50][t], e200=E[200][t], e12=E[12][t], e26=E[26][t]))
                    st = None
                    continue
                if not st["slancio"] and st["mx"] >= lv + p["MOM"] * a:
                    st["slancio"] = True
                st["mx"] = max(st["mx"], Hs[t])
                if not st["slancio"] and st["mx"] >= lv + p["MOM"] * a:
                    st["slancio"] = True
        # stato finale: linea attiva o setup in attesa di ritest
        t = n - 1
        if st is not None:
            lv = st["pA"] + st["m"] * (t + 1 - st["iA"])
            pend.append(dict(kind="attesa ritest" if st["slancio"] else "rotta, senza slancio", side=s, lv_next=s * lv,
                             stop=s * (st["base"] - abs(st["base"]) * p["MARG"]), tgt=s * st["pA"], ib=st["ib"],
                             iA=st["iA"], iB=st["iB"], pA=s * st["pA"], pB=s * st["pB"]))
        elif line is not None:
            lv = line["pA"] + line["m"] * (t + 1 - line["iA"])
            pend.append(dict(kind="linea attiva", side=s, lv_next=s * lv, iA=line["iA"], iB=line["iB"], pA=s * line["pA"],
                             pB=s * line["pB"]))
    return dict(signals=sorted(sigs, key=lambda x: x["t"]), flips=sorted(flips, key=lambda x: x["t"]), lines=lines,
                pending=pend, atr=A, ema=E, brk=brk)


def zones(df: pd.DataFrame, upto=None, p: dict | None = None) -> list[dict]:
    """Zone orizzontali da pivot settimanali (W-FRI per le azioni, W-SUN per le crypto: si usa la settimana di calendario)."""
    p = {**P, **(p or {})}
    d = df if upto is None else df[df.index <= upto]
    w = d[["high", "low"]].resample("W").agg({"high": "max", "low": "min"}).dropna()
    k = p["ZK"]
    h, l = w["high"].to_numpy(float), w["low"].to_numpy(float)
    pts = []
    for i in range(k, len(w) - k):
        if h[i] == h[i - k:i + k + 1].max():
            pts.append((float(h[i]), w.index[i], "massimo"))
        if l[i] == l[i - k:i + k + 1].min():
            pts.append((float(l[i]), w.index[i], "minimo"))
    pts.sort()
    out, cur = [], []
    for x in pts:
        if cur and np.log(x[0] / cur[0][0]) > p["ZW"]:
            out.append(cur)
            cur = []
        cur.append(x)
    if cur:
        out.append(cur)
    res = []
    for c in out:
        if len(c) >= p["ZN"]:
            res.append(dict(lo=c[0][0], hi=c[-1][0], n=len(c), ruoli=sorted({x[2] for x in c}),
                            ultimo=max(x[1] for x in c).date()))
    return res
