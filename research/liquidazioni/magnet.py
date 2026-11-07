"""Test preregistrati (PREREG.md): calamita delle liquidazioni stimate, direzione, confluenza con S/R.

Uso: python research/liquidazioni/magnet.py [cartella_dati]
cartella_dati deve contenere metrics/BTCUSDT-metrics-AAAA-MM-GG.zip e k1h/BTCUSDT-1h-AAAA-MM(-GG).zip
(archivio pubblico data.binance.vision, futures/um); default /tmp/radar-work/liq/data. Risultati in risultati.txt.
"""
from __future__ import annotations

import glob
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import liqmap  # noqa: E402

D = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/radar-work/liq/data")
OUT = Path(__file__).with_name("risultati.txt")
CACHE = Path("/tmp/radar-work/liq/work/magnet_maps.pkl")
SPLIT = pd.Timestamp("2024-01-01")


def rd(p, cols=None):
    with zipfile.ZipFile(p) as z:
        return pd.read_csv(z.open(z.namelist()[0]), usecols=cols)


def hourly() -> pd.DataFrame:
    m = pd.concat([rd(p, ["create_time", "sum_open_interest_value"]) for p in sorted(glob.glob(str(D / "metrics/*.zip")))])
    m["t"] = pd.to_datetime(m["create_time"])
    v = pd.to_numeric(m["sum_open_interest_value"], errors="coerce")
    oi = v.where(v > 0).groupby(m["t"].dt.floor("h")).last()          # ultimo valore dentro l'ora: ≤ chiusura
    ks = []
    for p in sorted(glob.glob(str(D / "k1h/*.zip"))):
        k = rd(p)
        if not str(k.columns[0]).startswith("open"):
            with zipfile.ZipFile(p) as z:
                k = pd.read_csv(z.open(z.namelist()[0]), header=None)
            k = k.iloc[:, :6]; k.columns = ["open_time", "open", "high", "low", "close", "volume"]
        ks.append(k[["open_time", "high", "low", "close"]])
    k = pd.concat(ks)
    k["t"] = pd.to_datetime(pd.to_numeric(k["open_time"]), unit="ms")
    k = k.drop_duplicates("t").set_index("t").sort_index()[["high", "low", "close"]].astype(float)
    k["oi_usd"] = oi.reindex(k.index).ffill(limit=3)
    return k


def maps(h: pd.DataFrame) -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_pickle(CACHE)
    rows = []
    days = pd.date_range(h.index[0].normalize() + pd.Timedelta(days=22), h.index[-1].normalize(), freq="D")
    for d in days:
        win = h[(h.index >= d - pd.Timedelta(hours=liqmap.LOOKBACK_H)) & (h.index < d)].dropna()
        if len(win) < 400:
            continue
        p = float(win["close"].iloc[-1])
        w = liqmap.window(liqmap.build(win), p, 0.12)
        up, dn = liqmap.clusters(w, p, "short"), liqmap.clusters(w, p, "long")
        im = liqmap.imbalance(w, p, 0.05)
        rows.append({"date": d, "price": p, "up": [c for c in up if c["sig"]], "dn": [c for c in dn if c["sig"]], "imb": im["pct"]})
    Z = pd.DataFrame(rows).set_index("date")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    Z.to_pickle(CACHE)
    return Z


def main():
    h = hourly()
    Z = maps(h)
    hi, lo, t = h["high"].to_numpy(), h["low"].to_numpy(), h.index
    pos = {d: t.searchsorted(d) for d in Z.index}
    # massimo/minimo futuro relativo per orizzonte: tabella per il controllo a pari distanza
    H = {1: 24, 3: 72, 7: 168}
    mfe = {k: [] for k in H}
    for d, r in Z.iterrows():
        i = pos[d]
        for k, n in H.items():
            seg = slice(i, min(i + n, len(h)))
            mfe[k].append((hi[seg].max() / r["price"] - 1, 1 - lo[seg].min() / r["price"]))
    for k in H:
        Z[f"up{k}"], Z[f"dn{k}"] = zip(*mfe[k])
    out = []
    P = lambda s: out.append(s) or print(s)
    P(f"Giorni con mappa: {len(Z)} ({Z.index[0].date()} → {Z.index[-1].date()}); cluster sig. sopra in {Z['up'].map(bool).mean():.0%}, sotto in {Z['dn'].map(bool).mean():.0%}")
    P(f"Distanza mediana del cluster sig. più vicino: sopra {np.median([u[0]['dist_pct'] for u in Z['up'] if u]):.2f}%, sotto {np.median([u[0]['dist_pct'] for u in Z['dn'] if u]):.2f}%")
    # ---------------- T1
    P("\nT1 · calamita: tocco del cluster sig. più vicino entro H contro un livello alla stessa distanza (giorni qualsiasi)")
    for side, key in (("sopra", "up"), ("sotto", "dn")):
        for k in H:
            rows = []
            for j, (d, r) in enumerate(Z.iterrows()):
                if not r[key]:
                    continue
                dist = abs(r[key][0]["dist_pct"]) / 100
                col = Z[f"{key}{k}"].to_numpy()
                ctrl = (np.delete(col, j) >= dist).mean()
                rows.append((d, float(r[f"{key}{k}"] >= dist), ctrl))
            R = pd.DataFrame(rows, columns=["d", "hit", "ctrl"])
            def eff(x):
                return (x.hit.mean() - x.ctrl.mean()) * 100
            n, hits = len(R), int(R.hit.sum())
            pv = binomtest(hits, n, R.ctrl.mean()).pvalue
            a, b = R[R.d < SPLIT], R[R.d >= SPLIT]
            P(f"  {side} {k}g: n {n}, toccato {R.hit.mean():.1%}, controllo {R.ctrl.mean():.1%}, effetto {eff(R):+.1f} pt (p {pv:.3f}); P1 {eff(a):+.1f} · P2 {eff(b):+.1f}")
    # ---------------- T2
    P("\nT2 · direzione: con squilibrio ≥ 20% il prezzo tocca prima il lato più pesante più dell'atteso dalle distanze?")
    for k, n in H.items():
        rows = []
        for d, r in Z.iterrows():
            if not (r["up"] and r["dn"]) or abs(r["imb"]) < 20:
                continue
            A, B = r["up"][0]["price"], r["dn"][0]["price"]
            i = pos[d]
            seg_h, seg_l = hi[i:i + n], lo[i:i + n]
            ha, hb = np.argmax(seg_h >= A) if (seg_h >= A).any() else 10**9, np.argmax(seg_l <= B) if (seg_l <= B).any() else 10**9
            if ha == hb:      # nessuno dei due o stessa ora: escluso
                continue
            up_first = ha < hb
            da, db = A / r["price"] - 1, 1 - B / r["price"]
            exp_up = db / (da + db)
            heavy_up = r["imb"] > 0
            rows.append((d, float(up_first == heavy_up), exp_up if heavy_up else 1 - exp_up))
        R = pd.DataFrame(rows, columns=["d", "hit", "exp"])
        eff = lambda x: (x.hit.mean() - x.exp.mean()) * 100
        pv = binomtest(int(R.hit.sum()), len(R), R.exp.mean()).pvalue
        a, b = R[R.d < SPLIT], R[R.d >= SPLIT]
        P(f"  {k}g: n {len(R)}, lato pesante per primo {R.hit.mean():.1%}, atteso {R.exp.mean():.1%}, effetto {eff(R):+.1f} pt (p {pv:.3f}); P1 {eff(a):+.1f} · P2 {eff(b):+.1f}")
    # ---------------- T3
    P("\nT3 · confluenza con S/R: rimbalzo dopo il primo tocco di un cluster sig. (entro 7 giorni)")
    from radar import levels
    from radar.data import load_all
    from radar.features import build_features
    f = build_features(load_all())
    dly = h["close"].resample("D").last()
    rows = []
    for d, r in Z.iterrows():
        try:
            LV = levels.compute(f[f.index < d])
        except Exception:  # noqa: BLE001
            continue
        zones = LV["supports"] + LV["resistances"]
        i = pos[d]
        for key in ("up", "dn"):
            if not r[key]:
                continue
            L = r[key][0]["price"]
            seg = hi[i:i + 168] >= L if key == "up" else lo[i:i + 168] <= L
            if not seg.any():
                continue
            tt = t[i + int(np.argmax(seg))].normalize()
            nxt = dly[(dly.index >= tt) & (dly.index < tt + pd.Timedelta(days=3))]
            brk = (nxt > L * 1.005).any() if key == "up" else (nxt < L * 0.995).any()
            conf = any(z["lo"] * 0.995 <= L <= z["hi"] * 1.005 for z in zones)
            # S/R da solo: zona più vicina dello stesso lato toccata entro 7 giorni
            zz = LV["resistances"][:1] if key == "up" else LV["supports"][:1]
            sr = None
            if zz:
                Lz = zz[0]["price"]
                sg = hi[i:i + 168] >= Lz if key == "up" else lo[i:i + 168] <= Lz
                if sg.any():
                    tz = t[i + int(np.argmax(sg))].normalize()
                    nz = dly[(dly.index >= tz) & (dly.index < tz + pd.Timedelta(days=3))]
                    sr = float(not ((nz > Lz * 1.005).any() if key == "up" else (nz < Lz * 0.995).any()))
            rows.append((d, key, float(not brk), conf, sr))
    R = pd.DataFrame(rows, columns=["d", "side", "bounce", "conf", "sr"])
    c, nc = R[R.conf], R[~R.conf]
    obs = c.bounce.mean() - nc.bounce.mean()
    rng = np.random.default_rng(7)
    lab = R.conf.to_numpy()
    perm = []
    for _ in range(1000):
        s = rng.permutation(lab)
        perm.append(R.bounce[s].mean() - R.bounce[~s].mean())
    pv = (np.abs(perm) >= abs(obs)).mean()
    sp = lambda x: (x[x.conf].bounce.mean() - x[~x.conf].bounce.mean()) * 100
    P(f"  tocchi {len(R)}: confluenti {len(c)} rimbalzo {c.bounce.mean():.1%}, non confluenti {len(nc)} rimbalzo {nc.bounce.mean():.1%}, effetto {obs*100:+.1f} pt (perm. p {pv:.3f}); P1 {sp(R[R.d < SPLIT]):+.1f} · P2 {sp(R[R.d >= SPLIT]):+.1f}")
    s2 = R.dropna(subset=["sr"])
    P(f"  S/R da soli (zona più vicina toccata): n {len(s2)}, rimbalzo {s2.sr.mean():.1%}; cluster confluenti {c.bounce.mean():.1%}: differenza {(c.bounce.mean() - s2.sr.mean())*100:+.1f} pt")
    OUT.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
