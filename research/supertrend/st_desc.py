"""supertrend · descrittivo (PREREG §3): cambi, durate, falsi cambi, rendimento dopo il cambio, tempo in rialzo, stato attuale."""
from __future__ import annotations
import numpy as np, pandas as pd
import st_lib as L

PER = {"2018-20": ("2018-01-01", "2020-12-31"), "2021-23": ("2021-01-01", "2023-12-31"), "2024-26": ("2024-01-01", L.END_DESC)}
HOR = (1, 3, 7, 14, 30)
BPD = {"4h": 6, "1D": 1, "1W": 1 / 7}

if __name__ == "__main__":
    a = L.load_4h(L.END_DESC); d = L.daily_from(a); w = L.weekly_from(d)
    bars = {"4h": a, "1D": d, "1W": w}
    c4 = a["close"]; t4 = a.index
    # rendimento in avanti a h giorni da ogni chiusura 4h (per data di chiusura della barra)
    close_time = t4 + pd.Timedelta(hours=4)
    cs = pd.Series(c4.to_numpy(), close_time)
    fwd = {h: pd.Series(cs.reindex(close_time + pd.Timedelta(days=h)).to_numpy() / cs.to_numpy() - 1, close_time) for h in HOR}
    rng = np.random.default_rng(20261123)
    rows, ev_rows, plac, state_rows, now = [], [], [], [], []
    for tf, b in bars.items():
        f = L.st_frame(b); dr = f["dir"].to_numpy()
        dur = {"4h": pd.Timedelta(hours=4), "1D": pd.Timedelta(days=1), "1W": pd.Timedelta(days=1)}[tf]
        ct = f.index + dur                                   # istante di chiusura della barra (1W: etichetta = domenica)
        flip = np.r_[False, dr[1:] != dr[:-1]]; flip[:10] = False
        fi = np.flatnonzero(flip)
        nxt = np.r_[fi[1:], len(dr)] - fi                    # durata del trend che comincia al cambio (in barre; l'ultimo è in corso)
        closed = np.r_[np.ones(len(fi) - 1, bool), False]
        ev = pd.DataFrame(dict(t=ct[fi], bar=f.index[fi], up=dr[fi] == -1, bars=nxt, closed=closed, close=f["close"].to_numpy()[fi]))
        for h in HOR:
            ev[f"r{h}"] = fwd[h].reindex(ev["t"]).to_numpy()
        ev["tf"] = tf; ev_rows.append(ev)
        state = pd.Series(dr, ct).reindex(close_time, method="ffill")
        for p, (s, e) in PER.items():
            s_, e_ = pd.Timestamp(s), pd.Timestamp(e) + pd.Timedelta(days=1)
            yrs = (e_ - s_).days / 365.25
            m = (ev["t"] > s_) & (ev["t"] <= e_); x = ev[m]
            mb = (ct > s_) & (ct <= e_)
            base = {h: fwd[h][(close_time > s_) & (close_time <= e_)].mean() for h in HOR}
            stp = state[(close_time > s_) & (close_time <= e_)]
            for side, g in (("rialzo", x[x["up"]]), ("ribasso", x[~x["up"]])):
                gc = g[g["closed"]]
                r = dict(tf=tf, periodo=p, verso=side, cambi=len(g), cambi_anno=len(g) / yrs,
                         durata_media_g=gc["bars"].mean() / BPD[tf] if len(gc) else np.nan, durata_mediana_g=gc["bars"].median() / BPD[tf] if len(gc) else np.nan,
                         durata_mediana_barre=gc["bars"].median() if len(gc) else np.nan,
                         falsi3=(gc["bars"] <= 3).mean() if len(gc) else np.nan, falsi10=(gc["bars"] <= 10).mean() if len(gc) else np.nan,
                         tempo=float(((dr[mb] == -1) if side == "rialzo" else (dr[mb] == 1)).mean()))
                for h in HOR:
                    r[f"r{h}"] = g[f"r{h}"].mean(); r[f"ecc{h}"] = g[f"r{h}"].mean() - base[h]; r[f"pos{h}"] = (g[f"r{h}"] > 0).mean()
                rows.append(r)
            for side, val in (("rialzo", -1), ("ribasso", 1)):
                mm = (stp == val).to_numpy()
                state_rows.append(dict(tf=tf, periodo=p, stato=side, quota=mm.mean(),
                                       **{f"r{h}": fwd[h].reindex(stp.index)[mm].mean() for h in (7, 30)},
                                       **{f"media{h}": base[h] for h in (7, 30)}))
        # placebo: traslazione circolare delle date dei cambi dentro ciascun periodo; eccesso medio sull'intero 2018–26
        for side in ("rialzo", "ribasso"):
            for h in (7, 30):
                real_num, real_n, sims = 0.0, 0, np.zeros(1000)
                for p, (s, e) in PER.items():
                    s_, e_ = pd.Timestamp(s), pd.Timestamp(e) + pd.Timedelta(days=1)
                    grid = fwd[h][(close_time > s_) & (close_time <= e_)]
                    g = grid.to_numpy(); mu = np.nanmean(g)
                    x = ev[(ev["t"] > s_) & (ev["t"] <= e_) & (ev["up"] == (side == "rialzo"))]
                    pos = grid.index.searchsorted(x["t"].to_numpy())
                    pos = pos[pos < len(g)]
                    v = g[pos]; real_num += np.nansum(v - mu); real_n += np.isfinite(v).sum()
                    sh = rng.integers(0, len(g), 1000)
                    sims += np.nansum(g[(pos[None, :] + sh[:, None]) % len(g)] - mu, axis=1)
                real = real_num / max(real_n, 1); sims = sims / max(real_n, 1)
                plac.append(dict(tf=tf, verso=side, h=h, n=real_n, eccesso=real, p=float((np.abs(sims) >= abs(real)).mean())))
        # stato attuale
        last = f.iloc[-1]; lf = ev.iloc[-1]
        now.append(dict(tf=tf, barra=str(f.index[-1]), direzione="rialzo" if last["dir"] == -1 else "ribasso", linea=last["st"], chiusura=last["close"],
                        distanza=last["st"] / last["close"] - 1, ultimo_cambio=str(lf["bar"]), prezzo_al_cambio=lf["close"],
                        barre_dal_cambio=int(lf["bars"]), da_allora=last["close"] / lf["close"] - 1, atr=last["atr"], altra_banda=last["lb"] if last["dir"] == 1 else last["ub"]))
    R = pd.DataFrame(rows); EV = pd.concat(ev_rows); PL = pd.DataFrame(plac); ST = pd.DataFrame(state_rows); NOW = pd.DataFrame(now)
    R.to_csv(L.HERE / "descrittivo.csv", index=False); EV.to_csv(L.HERE / "cambi.csv", index=False)
    PL.to_csv(L.HERE / "descrittivo_placebo.csv", index=False); ST.to_csv(L.HERE / "descrittivo_stato.csv", index=False)
    NOW.to_csv(L.HERE / "stato_attuale.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)
    with open(L.HERE / "descrittivo.txt", "w") as fh:
        for title, x in (("CAMBI PER PERIODO", R.round(3)), ("STATO → RENDIMENTO", ST.round(4)), ("PLACEBO (12 test, soglia 0,0042)", PL.round(4)),
                         ("STATO ATTUALE", NOW.round(4)), ("ULTIMI CAMBI 1D", EV[EV["tf"] == "1D"].tail(8).round(3)),
                         ("CAMBI 1W", EV[(EV["tf"] == "1W") & (EV["t"] > "2017-06-01")].round(3))):
            s = f"\n{title}\n{x.to_string()}"; print(s); print(s, file=fh)
