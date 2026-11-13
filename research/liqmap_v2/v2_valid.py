"""Validazione liqmap v1 (50/50) contro v2 (flusso taker) sulle liquidazioni reali (PREREG.md). Uso: python research/liqmap_v2/v2_valid.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from radar import liqmap  # noqa: E402
import v2_data  # noqa: E402

K_DENSE, RNG, RNG_IMB = 8, 0.10, 0.05


def variants(h: pd.DataFrame) -> dict[str, pd.Series | None]:
    b = h["b"]
    return {"v1": None, "v2": b.clip(0.1, 0.9), "v2k": (0.5 + 3 * (b - 0.5)).clip(0.1, 0.9),
            "v2t": ((b + h["top"]) / 2).clip(0.1, 0.9)}


def map_at(h, T, share):
    win = h[(h.index >= T - pd.Timedelta(hours=liqmap.LOOKBACK_H)) & (h.index < T)]
    win = win.dropna(subset=["high", "low", "close", "oi_usd"])
    if len(win) < 400:
        return None
    x = win[["high", "low", "close", "oi_usd"]].copy()
    if share is not None:
        x["long_share"] = share.reindex(x.index)
    p = float(win["close"].iloc[-1])
    return p, liqmap.window(liqmap.build(x), p, RNG + 0.01)


def dense_share(w, p, ev):
    """M1 per lato: ($ reali nelle 8 fasce più dense, $ reali totali sul lato entro 10%)."""
    edges = lambda px: (px / np.sqrt(1 + liqmap.BIN), px * np.sqrt(1 + liqmap.BIN))
    out = {}
    for side, col, below in (("long", "long", True), ("short", "short", False)):
        x = w[(w["price"] < p) if below else (w["price"] > p)]
        x = x[(x["price"] / p - 1).abs() <= RNG]
        e = ev[(ev["side"] == side) & (((ev["price"] < p) & (ev["price"] >= p * (1 - RNG))) if below else
                                     ((ev["price"] > p) & (ev["price"] <= p * (1 + RNG))))]
        tot = float(e["usd"].sum())
        top = x[x[col] > 0].nlargest(K_DENSE, col)
        lo, hi = edges(top["price"].to_numpy())
        pr = e["price"].to_numpy()[:, None]
        hit = ((pr >= lo[None, :]) & (pr < hi[None, :])).any(axis=1) if len(top) else np.zeros(len(e), bool)
        out[side] = (float(e["usd"].to_numpy()[hit].sum()), tot)
        out[side + "_rel"] = top["price"].to_numpy() / p   # posizione relativa delle fasce dense (per il placebo)
    return out


def placebo(D, rel, liq, n=30, seed=7):
    """M1 con le fasce dense (posizioni relative) di un altro giorno a caso: stessa distribuzione delle distanze."""
    rng = np.random.default_rng(seed)
    days = list(D.index)
    res = {"long": [], "short": []}
    ev = {T: liq[(liq["time"] >= T) & (liq["time"] < T + pd.Timedelta(days=1))] for T in days}
    for _ in range(n):
        perm = rng.permutation(len(days))
        for side, below in (("long", True), ("short", False)):
            hit = tot = 0.0
            for i, T in enumerate(days):
                p, e = D.at[T, "p"], ev[T]
                e = e[(e["side"] == side) & (((e["price"] < p) & (e["price"] >= p * (1 - RNG))) if below else
                                            ((e["price"] > p) & (e["price"] <= p * (1 + RNG))))]
                r = rel[days[perm[i]]][side]
                lo, hi = r * p / np.sqrt(1 + liqmap.BIN), r * p * np.sqrt(1 + liqmap.BIN)
                pr = e["price"].to_numpy()[:, None]
                ok = ((pr >= lo[None, :]) & (pr < hi[None, :])).any(axis=1) if len(r) else np.zeros(len(e), bool)
                hit += float(e["usd"].to_numpy()[ok].sum()); tot += float(e["usd"].sum())
            res[side].append(hit / tot * 100 if tot else np.nan)
    return {s: (float(np.mean(v)), float(np.percentile(v, 95))) for s, v in res.items()}


def imb(w, p):
    k = (w["price"] / p - 1).abs() <= RNG_IMB
    return float(w.loc[k & (w["price"] > p), "short"].sum()), float(w.loc[k & (w["price"] < p), "long"].sum())


def run(h, liq, days, label):
    V = variants(h)
    rows, REL = [], {}
    for T in days:
        e1 = liq[(liq["time"] >= T) & (liq["time"] < T + pd.Timedelta(days=1))]
        e3 = liq[(liq["time"] >= T) & (liq["time"] < T + pd.Timedelta(days=3))]
        prev = h["close"].reindex([T - pd.Timedelta(hours=25), T - pd.Timedelta(hours=1)]).to_numpy()
        r = {"T": T, "mom": np.log(prev[1] / prev[0]) if np.all(prev > 0) else np.nan,
             "real1": np.log((e1.loc[e1.side == "short", "usd"].sum() + 1e4) / (e1.loc[e1.side == "long", "usd"].sum() + 1e4)),
             "real3": np.log((e3.loc[e3.side == "short", "usd"].sum() + 1e4) / (e3.loc[e3.side == "long", "usd"].sum() + 1e4))}
        for name, sh in V.items():
            m = map_at(h, T, sh)
            if m is None:
                break
            p, w = m
            ds = dense_share(w, p, e1)
            for s in ("long", "short"):
                r[f"{name}_{s}_hit"], r[f"{name}_{s}_tot"] = ds[s]
            r["p"] = p
            if name == "v1":
                REL[T] = {"long": ds["long_rel"], "short": ds["short_rel"]}
            s5, l5 = imb(w, p)
            r[f"{name}_pred"] = np.log((s5 + 1e5) / (l5 + 1e5))
            r[f"{name}_s5"], r[f"{name}_l5"] = s5, l5
        else:
            rows.append(r)
    D = pd.DataFrame(rows).set_index("T")
    D.to_csv(Path(__file__).resolve().parent / f"giorni_{label}.csv")
    D.attrs["rel"] = REL
    return D


def partial_spearman(x, y, z):
    rx, ry, rz = (pd.Series(v).rank().to_numpy() for v in (x, y, z))
    res = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    return stats.pearsonr(res(rx), res(ry))[0]


def report(D, names=("v1", "v2", "v2k", "v2t")):
    lines = []
    for name in names:
        parts = []
        for s in ("long", "short"):
            hit, tot = D[f"{name}_{s}_hit"], D[f"{name}_{s}_tot"]
            k = tot > 0
            parts.append(f"{s} pes {hit.sum() / tot.sum() * 100:5.1f}% / giorni {(hit[k] / tot[k]).mean() * 100:5.1f}%")
        ok = D[["mom", f"{name}_pred", "real1", "real3"]].dropna()
        c1 = stats.spearmanr(ok[f"{name}_pred"], ok["real1"])[0]
        c3 = stats.spearmanr(ok[f"{name}_pred"], ok["real3"])[0]
        cp = partial_spearman(ok[f"{name}_pred"], ok["real1"], ok["mom"])
        sh = (D[f"{name}_s5"] / (D[f"{name}_s5"] + D[f"{name}_l5"])).median() * 100
        lines.append(f"  {name:4s} M1 {parts[0]} | {parts[1]} | M2 rho1 {c1:+.3f} rho3 {c3:+.3f} parz.mom {cp:+.3f} | short/(s+l) ±5% med {sh:4.1f}%")
    return "\n".join(lines)


def okx_real():
    """Liquidazioni reali di novembre: data/liquidations.csv (OKX) + data/liq_events (multi-exchange), senza doppioni OKX."""
    a = pd.read_csv(ROOT / "data/liquidations.csv", parse_dates=["time"]).rename(columns={"liquidated": "side"})[["time", "side", "price", "usd"]]
    fr = [a]
    for p in sorted((ROOT / "data/liq_events").glob("20??-??.csv")):
        e = pd.read_csv(p)
        e = e[e["exchange"] != "okx"]
        fr.append(pd.DataFrame({"time": pd.to_datetime(e["ts"], unit="ms"), "side": e["side"], "price": e["price"], "usd": e["usd"]}))
    return pd.concat(fr).sort_values("time")


if __name__ == "__main__":
    h = v2_data.hourly()
    liq = v2_data.liq_cm()
    days = pd.date_range("2023-06-26", "2024-10-13", freq="D")
    D = run(h, liq, days, "cm")
    out = [f"Binance cm 2023-06-26 → 2024-10-13, giorni {len(D)}, $ liquidati {liq['usd'].sum() / 1e6:.0f} M",
           "TUTTO", report(D)]
    for lab, a, b in (("H1 2023-06-25 → 2024-02-15", "2023-06-25", "2024-02-15"), ("H2 2024-02-16 → 2024-10-14", "2024-02-16", "2024-10-14")):
        out += [lab, report(D.loc[a:b])]
    base = K_DENSE / (RNG / liqmap.BIN) * 100
    out.append(f"Riferimento: 8 fasce su ~{RNG / liqmap.BIN:.0f} per lato = {base:.0f}% se a caso")
    pl = placebo(D, D.attrs["rel"], liq)
    out.append("Placebo (fasce dense v1 di un altro giorno, stesse distanze; media e 95° pct su 30 permutazioni, pesato): "
               + " | ".join(f"{s} {m:.1f}% (p95 {q:.1f}%)" for s, (m, q) in pl.items()))
    nov = okx_real()
    Dn = run(h, nov, pd.date_range("2026-11-01", "2026-11-13", freq="D"), "nov")
    out += [f"Novembre 2026 (OKX + altri exchange, {len(Dn)} giorni, indicativo)", report(Dn)]
    txt = "\n".join(out)
    print(txt)
    (Path(__file__).resolve().parent / "risultati.txt").write_text(txt + "\n")
