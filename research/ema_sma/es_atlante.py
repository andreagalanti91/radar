"""ema_sma · PARTE A · atlante descrittivo degli eventi sulle medie (PREREG §7). Scrive atlante.csv (per periodo) e atlante_sintesi.csv."""
import numpy as np, pandas as pd
import es_lib as L

HZ = (1, 3, 7, 14, 30)
PER = {"2018-20": ("2018-01-01", "2020-12-31"), "2021-23": ("2021-01-01", "2023-12-31"), "2024-26": ("2024-01-01", L.CUT)}
a = L.load_4h(); d = L.daily_from(a); w = L.weekly_from(d)
pc = pd.Series(a["close"].to_numpy(), a.index + pd.Timedelta(hours=4))        # chiusure 4h indicizzate all'ora di chiusura
FW = {h: (pc.reindex(pc.index + pd.Timedelta(days=h), method="ffill").to_numpy() / pc.to_numpy() - 1) for h in HZ}
for h in HZ:                                                                   # niente rendimenti oltre la fine dei dati
    FW[h][pc.index + pd.Timedelta(days=h) > pc.index[-1]] = np.nan
PIDX = {p: (pc.index.searchsorted(pd.Timestamp(x) + pd.Timedelta(hours=4)), pc.index.searchsorted(pd.Timestamp(y) + pd.Timedelta(hours=28))) for p, (x, y) in PER.items()}
UNC = {p: {h: np.nanmean(FW[h][i:j]) for h in HZ} for p, (i, j) in PIDX.items()}
UNCP = {p: {h: np.nanmean(FW[h][i:j] > 0) for h in HZ} for p, (i, j) in PIDX.items()}
EXC = {h: np.full(len(pc), np.nan) for h in HZ}                                # eccesso sulla media incondizionata del periodo
for p, (i, j) in PIDX.items():
    for h in HZ: EXC[h][i:j] = FW[h][i:j] - UNC[p][h]
CLOSE_OFF = {"4h": pd.Timedelta(hours=4), "1D": pd.Timedelta(days=1), "1W": pd.Timedelta(days=1)}
rng = np.random.default_rng(11)
SHIFTS = {p: rng.integers(1, j - i, size=1000) for p, (i, j) in PIDX.items()}
rows, synth = [], []


def runs(x):
    x = x.astype(int); return x.groupby((x == 0).cumsum()).cumsum()


def record(tf, ma, ev, times, opp=None, back=None):
    """times: istanti di chiusura dell'evento. opp: istanti dell'evento opposto (durata). back: (falso entro 3, entro 10) per evento."""
    pos = pc.index.searchsorted(times); ok = (pos < len(pc)) & (pc.index[np.minimum(pos, len(pc) - 1)] == times)
    pos = pos[ok]; times = times[ok]
    if back is not None: back = (back[0][ok], back[1][ok])
    s = dict(tf=tf, ma=ma, ev=ev); pool = {7: [], 30: []}; perm = {7: np.zeros(1000), 30: np.zeros(1000)}; nn = {7: 0, 30: 0}
    for p, (i, j) in PIDX.items():
        m = (pos >= i) & (pos < j); q = pos[m]; t = times[m]
        ind, last = 0, None
        for x in t:
            if last is None or (x - last).days >= 30: ind += 1; last = x
        r = dict(tf=tf, ma=ma, ev=ev, periodo=p, n=int(m.sum()), n_ind=ind)
        for h in HZ:
            f = FW[h][q]; f = f[~np.isnan(f)]
            r[f"med{h}"] = np.mean(f) if len(f) else np.nan; r[f"mdn{h}"] = np.median(f) if len(f) else np.nan
            r[f"ecc{h}"] = r[f"med{h}"] - UNC[p][h]; r[f"pos{h}"] = np.mean(f > 0) if len(f) else np.nan
        if opp is not None and len(t):
            k = np.searchsorted(opp, t, side="right"); dur = [(opp[x] - y).total_seconds() / 86400 for x, y in zip(k, t) if x < len(opp)]
            r["durata_g"] = np.median(dur) if dur else np.nan
        if back is not None and m.sum():
            r["falso3"], r["falso10"] = float(back[0][m].mean()), float(back[1][m].mean())
        rows.append(r)
        s[f"n_{p}"], s[f"ind_{p}"] = r["n"], ind
        for h in (7, 30):
            s[f"ecc{h}_{p}"] = r[f"ecc{h}"]; e = EXC[h][q]; pool[h].append(e[~np.isnan(e)])
            sh = i + (q[None, :] - i + SHIFTS[p][:, None]) % (j - i)
            ee = EXC[h][sh]; perm[h] += np.nansum(ee, axis=1); nn[h] += int((~np.isnan(e)).sum())
        s[f"pos30_{p}"] = r["pos30"]; s[f"durata_{p}"] = r.get("durata_g", np.nan); s[f"falso10_{p}"] = r.get("falso10", np.nan); s[f"falso3_{p}"] = r.get("falso3", np.nan)
    for h in (7, 30):
        x = np.concatenate(pool[h]); obs = x.mean() if len(x) else np.nan
        s[f"ecc{h}"] = obs; s[f"p{h}"] = float((np.abs(perm[h] / max(nn[h], 1)) >= abs(obs)).mean()) if len(x) else np.nan
    sg = [np.sign(s[f"ecc{h}_{p}"]) for h in (7, 30) for p in PER]
    s["ricorrente"] = bool(all(x == sg[0] and x != 0 for x in sg) and all(s[f"ind_{p}"] >= 5 for p in PER))
    s["segno"] = int(sg[0]) if s["ricorrente"] else 0
    synth.append(s)


for tf, b in (("4h", a), ("1D", d), ("1W", w)):
    c = b["close"]; ct = b.index + CLOSE_OFF[tf]; minq = 100 if tf == "1W" else 500
    mas = [(k, n) for k in L.KINDS for n in L.PERS] + ([("EMA", 21), ("SMA", 40)] if tf == "1W" else [])
    M = {x: L.ma(c, *x) for x in mas}
    for (k, n), m in M.items():
        nm = f"{k}{n}"; v = m.notna().to_numpy(); up = (c > m) & v; dn = (c < m) & v
        ru, rd = runs(up), runs(dn)
        below3 = dn[::-1].rolling(3, min_periods=1).max()[::-1].shift(-1).fillna(0).to_numpy() > 0      # una chiusura sotto nelle 3 barre successive
        below10 = dn[::-1].rolling(10, min_periods=1).max()[::-1].shift(-1).fillna(0).to_numpy() > 0
        above3 = up[::-1].rolling(3, min_periods=1).max()[::-1].shift(-1).fillna(0).to_numpy() > 0
        above10 = up[::-1].rolling(10, min_periods=1).max()[::-1].shift(-1).fillna(0).to_numpy() > 0
        xu = (up & dn.shift(1, fill_value=False) | (up & (ru == 1) & v)).to_numpy(); xd = (dn & (rd == 1)).to_numpy()
        record(tf, nm, "attraversa su", ct[xu], ct[xd], (below3[xu], below10[xu])); record(tf, nm, "attraversa giu", ct[xd], ct[xu], (above3[xd], above10[xd]))
        for N in (2, 3):
            eu, ed = (ru == N).to_numpy(), (rd == N).to_numpy()
            record(tf, nm, f"{N} chiusure sopra", ct[eu], None, (below3[eu], below10[eu])); record(tf, nm, f"{N} chiusure sotto", ct[ed], None, (above3[ed], above10[ed]))
        sl = np.sign(m - m.shift(5)); tu = ((sl > 0) & (sl.shift(1) < 0)).to_numpy(); td = ((sl < 0) & (sl.shift(1) > 0)).to_numpy()
        record(tf, nm, "pendenza gira su", ct[tu], ct[td]); record(tf, nm, "pendenza gira giu", ct[td], ct[tu])
        dist = c / m - 1; q95 = dist.expanding(minq).quantile(0.95).shift(1); q05 = dist.expanding(minq).quantile(0.05).shift(1)
        hi, lo = dist > q95, dist < q05
        record(tf, nm, "stiramento alto", ct[(hi & ~hi.shift(1, fill_value=False)).to_numpy()]); record(tf, nm, "stiramento basso", ct[(lo & ~lo.shift(1, fill_value=False)).to_numpy()])
        rt = ((ru.shift(1) >= 5) & (b["low"] <= m) & (c > m)).to_numpy(); rj = ((rd.shift(1) >= 5) & (b["high"] >= m) & (c < m)).to_numpy()
        record(tf, nm, "ritest tiene (da sopra)", ct[rt]); record(tf, nm, "ritest respinto (da sotto)", ct[rj])
    for k in L.KINDS:
        for f_, s_ in ((20, 50), (50, 200)):
            df = M[k, f_] - M[k, s_]; g = ((df > 0) & (df.shift(1) <= 0)).to_numpy(); dc = ((df < 0) & (df.shift(1) >= 0)).to_numpy()
            record(tf, f"{k}{f_}/{s_}", "incrocio rialzista", ct[g], ct[dc]); record(tf, f"{k}{f_}/{s_}", "incrocio ribassista", ct[dc], ct[g])

c4 = a["close"]; cd = d["close"]; cw = w["close"]
for k in L.KINDS:
    for n in (20, 50, 200):
        s4 = np.sign(c4 - L.ma(c4, k, n)).to_numpy(); sd = L.to4h(np.sign(cd - L.ma(cd, k, n)), a.index, "1D"); sw = L.to4h(np.sign(cw - L.ma(cw, k, n)), a.index, "1W")
        for lab, sgn in (("rialzista", 1), ("ribassista", -1)):
            st = pd.Series((s4 == sgn) & (sd == sgn) & (sw == sgn), a.index); ct = a.index + pd.Timedelta(hours=4)
            ent = (st & ~st.shift(1, fill_value=False)).to_numpy(); ext = (~st & st.shift(1, fill_value=False)).to_numpy()
            record("3 intervalli", f"{k}{n}", f"allineamento {lab}: ingresso", ct[ent], ct[ext])
            record("3 intervalli", f"{k}{n}", f"allineamento {lab}: stato", ct[st.to_numpy()])
            synth[-1]["quota_tempo"] = float(st.loc["2018":].mean())

A = pd.DataFrame(rows); Sx = pd.DataFrame(synth)
A.to_csv(L.HERE / "atlante.csv", index=False); Sx.to_csv(L.HERE / "atlante_sintesi.csv", index=False)
nt = int(Sx["p7"].notna().sum() + Sx["p30"].notna().sum())
print("eventi", len(Sx), "| test (2 orizzonti)", nt, "| soglia Bonferroni %.6f" % (0.05 / nt))
print("incondizionato:", {p: {h: round(v * 100, 2) for h, v in u.items()} for p, u in UNC.items()}, "positivi a 30g", {p: round(u[30], 3) for p, u in UNCP.items()})
print("ricorrenti", int(Sx.ricorrente.sum()), "su", len(Sx), "| attesi per caso (segni indipendenti, 2·0,5^6·quota con >=5 casi):", round(float((Sx[[f'ind_{p}' for p in PER]].min(axis=1) >= 5).sum()) / 32, 1))
print("p7<0,05:", int((Sx.p7 < 0.05).sum()), "p30<0,05:", int((Sx.p30 < 0.05).sum()), "| p<=0,001 (minimo ottenibile):", int((Sx.p7 <= 0.001).sum()), int((Sx.p30 <= 0.001).sum()))
