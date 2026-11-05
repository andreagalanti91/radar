"""Short W2 · tutte le prove preregistrate (PREREG.md). Uso: python3 research/short_w2/run.py  → results.txt, trades_*.csv"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from short_lab import (HERE, P0, daily_s6, load_long, load_repo, metrics, short_cfg, short_rules, simulate,  # noqa: E402
                       weekly_bars)

RULES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]
END = None
SPLITS = {"2021-23": ("2021-01-01", "2023-12-31"), "2024-oggi": ("2024-01-01", None)}
OUT = []


def log(s=""):
    print(s)
    OUT.append(s)


def run(f, w, rule, size, longs, start="2021-01-01", end=None, p=P0, override=None):
    S = short_rules(w)
    ds = daily_s6(f, w) if rule == "S6" else None
    ent = None if rule == "S6" else S[rule]
    return simulate(f, w, ent, short_cfg(rule, p, size), longs=longs, start=start, end=end, daily_short=ds,
                    entry_override=override)


def row(name, m):
    return (f"{name:<16} {m['final']:>9,} {m['ret']:>8.1f} {m['dd']:>7.1f} {m['n']:>3} {str(m['wr']):>4} "
            f"{str(m['avg_w']):>6} {str(m['avg_l']):>6} {str(m['mar']):>6} {m['tim']:>4} {m['no_best']:>7.1f}")


HDR = f"{'regola':<16} {'finale $':>9} {'rend%':>8} {'DD%':>7} {'n':>3} {'WR':>4} {'+medio':>6} {'-medio':>6} {'MAR':>6} {'TiM':>4} {'-best%':>7}"


def episodes(f: pd.DataFrame) -> list:
    """Episodi ribassisti indipendenti: tratti di regime base (chiusura < SMA40w, EMA20w in calo) ≥ 8 settimane
    (fusi se separati da < 6 settimane), con il calo massimo dentro l'episodio."""
    w = weekly_bars(f)
    dn = w["dn"].fillna(False).to_numpy()
    ix = w.index
    segs, i = [], 0
    while i < len(dn):
        if dn[i]:
            j = i
            while j + 1 < len(dn) and dn[j + 1]:
                j += 1
            segs.append([i, j])
            i = j + 1
        else:
            i += 1
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < 6:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for a, b in merged:
        if b - a + 1 < 8:
            continue
        seg = w["close"].iloc[a:b + 1]
        pk = w["close"].iloc[max(0, a - 12):a + 1].max()
        out.append((str(ix[a].date()), str(ix[b].date()), b - a + 1, round((seg.min() / pk - 1) * 100)))
    return out


def main():
    f = load_repo()
    fl = load_long(f)
    w = weekly_bars(f)
    wl = weekly_bars(fl)
    log(f"Dati: spot {f.index[0].date()}→{f.index[-1].date()} · pf14z da {f['pf14z'].first_valid_index().date()} · "
        f"funding da {f['funding'].first_valid_index().date()} · OI/LS da {f['oi'].first_valid_index().date()} · "
        f"F&G da {f['fng'].first_valid_index().date()} · storia lunga da {fl.index[0].date()} (Bitstamp → Binance 2017-08-17)")
    log("Episodi ribassisti (regime base ≥ 8 sett.): " + "; ".join(f"{a}→{b} {n}s calo {d}%" for a, b, n, d in episodes(fl)))

    # ---- W2 così com'è (commissione perp 0,05% come in radar/weekly.py)
    S = short_rules(w)
    w2 = simulate(f, w, S["S0"], short_cfg("S0"), w2_short_fees=True)
    log("\n== W2 così com'è dal 2021 (riferimento)")
    log(HDR)
    log(row("W2 (tutto)", metrics(w2)))
    m = metrics(w2, "short")
    log(f"  short W2: n {m['n']}, WR {m['wr']}%, contributo composto {m['sum_pnl']}%, + medio {m['avg_w']}%")
    for t in w2["trades"]:
        if t["side"] == "short":
            log(f"   {t['entry']}→{t['exit']} expo {t['expo']} pnl {t['pnl']*100:+.1f}% ({t['reason']})")
    res = {}
    for size in ("R25", "1x"):
        log(f"\n== Standalone short dal 2021, size {size}")
        log(HDR)
        for r in RULES:
            x = run(f, w, r, size, False)
            res[(r, size, "solo")] = metrics(x)
            log(row(r, res[(r, size, "solo")]))
        log(f"\n== Combinato con i long W2 (short W2 sostituiti), size {size}")
        log(HDR)
        log(row("W2 così com'è", metrics(w2)))
        for r in RULES:
            x = run(f, w, r, size, True)
            res[(r, size, "combo")] = metrics(x)
            log(row(r + "+W2L", res[(r, size, "combo")]))
    # ---- split
    log("\n== Split (10.000 $ da capo in ogni periodo; 2018-20 su storia lunga, flusso = CVD spot proxy, funding 0)")
    log(f"{'regola':<14}" + "".join(f"{k:>34}" for k in ("2018-20", "2021-23", "2024-oggi")))
    per = {"2018-20": (fl, wl, "2018-01-01", "2020-12-31"), "2021-23": (f, w, "2021-01-01", "2023-12-31"),
           "2024-oggi": (f, w, "2024-01-01", None)}
    split = {}
    for size in ("R25", "1x"):
        for mode in ("solo", "combo"):
            for r in ["W2"] + RULES:
                cells = []
                for k, (ff, ww, a, b) in per.items():
                    if r == "W2":
                        Sx = short_rules(ww)
                        x = simulate(ff, ww, Sx["S0"], short_cfg("S0", size=size), longs=(mode == "combo"), start=a, end=b,
                                     w2_short_fees=True)
                    else:
                        x = run(ff, ww, r, size, mode == "combo", a, b)
                    m = metrics(x)
                    split[(r, size, mode, k)] = m
                    cells.append(f"{m['ret']:>8.1f}% DD{m['dd']:>6.1f} n{m['n']:>2} MAR{str(m['mar']):>6}")
                log(f"{r + ' ' + mode + ' ' + size:<14}" + "  ".join(f"{c:>32}" for c in cells))
    # ---- vicini (sulla famiglia S1/S2/S6, combinato R25, 2021-oggi e 2018-20)
    log("\n== Parametri vicini (combinato con long W2, R25): MAR 2021-oggi | MAR 2018-20")
    neigh = {"base": {}, "sma35": dict(sma=35), "sma45": dict(sma=45), "ema18": dict(ema_x=18), "ema24": dict(ema_x=24),
             "trail2": dict(trail=2.0, stop=2.0), "trail3": dict(trail=3.0, stop=3.0), "macd6": dict(macd=(6, 18, 4)),
             "macd10": dict(macd=(10, 26, 6))}
    nb = {}
    for r in ("S0", "S1", "S2", "S3", "S6", "S7"):
        cells = []
        for k, v in neigh.items():
            p = dict(P0, **v)
            wn, wln = weekly_bars(f, p), weekly_bars(fl, p)
            a = metrics(run(f, wn, r, "R25", True, p=p))
            b = metrics(run(fl, wln, r, "R25", True, "2018-01-01", "2020-12-31", p=p))
            nb[(r, k)] = (a["mar"], b["mar"], a["ret"], a["dd"])
            cells.append(f"{k}:{a['mar']}|{b['mar']}")
        log(f"{r}: " + "  ".join(cells))
    # ---- placebo: stessi numeri di ingressi a caso nelle settimane di regime base (flat), standalone R25 dal 2021
    log("\n== Placebo (500 prove: k ingressi casuali fra le settimane di regime base, stesse uscite di S1, standalone R25)")
    rng = np.random.default_rng(7)
    reg = w.index[w["dn"].fillna(False).to_numpy() & (w.index >= "2021-01-01")]
    for r in ("S0", "S1", "S2", "S3", "S4", "S6", "S7"):
        x = run(f, w, r, "R25", False)
        mr = metrics(x)
        k = max(1, mr["n"])
        sims = []
        for _ in range(500):
            pick = pd.Series(True, index=rng.choice(reg, size=min(k, len(reg)), replace=False))
            y = simulate(f, w, None, short_cfg("S7" if r == "S7" else "S1", size="R25"), longs=False, entry_override=pick)
            sims.append(metrics(y)["ret"])
        sims = np.array(sims)
        log(f"{r}: rend {mr['ret']}% vs placebo mediana {np.median(sims):.1f}% (p95 {np.percentile(sims, 95):.1f}%), "
            f"p = {(sims >= mr['ret']).mean():.3f}")
    json.dump({"res": {"|".join(k): v for k, v in res.items()}, "split": {"|".join(k): v for k, v in split.items()},
               "neigh": {"|".join(k): v for k, v in nb.items()}}, open(HERE / "results.json", "w"), indent=1)
    (HERE / "results.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
