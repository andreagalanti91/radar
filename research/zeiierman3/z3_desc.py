"""zeiierman3 · descrittivo degli attraversamenti di −90 e −20 dal 2018 e caso di oggi. Uso: python3 z3_desc.py → descrittivo.txt"""
from __future__ import annotations
import numpy as np, pandas as pd
import z3_lib as Z

D = Z.HERE
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); OUT.append(s)


d, a = Z.load()
z1, z4 = Z.indicators(d), Z.indicators(a)


def events(df, z, line, bpd):
    """Eventi alla chiusura t; ingresso all'apertura t+1; rendimenti alla chiusura t+h giorni."""
    x = z[line].to_numpy(float); O, H, L, C = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    idx = df.index; n = len(x)
    kinds = {"scende sotto -90": Z.cross_below(x, -90), "risale sopra -90": Z.cross_above(x, -90),
             "sale sopra -20": Z.cross_above(x, -20), "scende sotto -20": Z.cross_below(x, -20)}
    rows = []
    t0 = idx.searchsorted(pd.Timestamp("2018-01-01"))
    for k, m in kinds.items():
        for t in np.flatnonzero(m):
            if t < t0 or t + 1 >= n:
                continue
            p0 = O[t + 1]
            r = dict(evento=k, data=idx[t], chiusura=round(C[t]), linea=round(x[t], 1))
            for h in (7, 30, 60):
                j = t + h * bpd
                r[f"r{h}"] = round((C[j] / p0 - 1) * 100, 1) if j < n else np.nan
            j60 = min(n, t + 1 + 60 * bpd)
            r["min60"] = round((L[t + 1:j60].min() / p0 - 1) * 100, 1)
            r["max60"] = round((H[t + 1:j60].max() / p0 - 1) * 100, 1)
            # durata in zona: fino al ritorno oltre la soglia
            th = -90 if "90" in k else -20
            below = "sotto" in k if "scende" in k else ("sotto" in k)
            if k == "scende sotto -90":
                back = np.flatnonzero(x[t + 1:] >= th)
            elif k == "sale sopra -20":
                back = np.flatnonzero(x[t + 1:] <= th)
            elif k == "risale sopra -90":
                back = np.flatnonzero(x[t + 1:] > -20)          # tempo fino all'uscita della regola (sopra −20)
            else:
                back = np.flatnonzero(x[t + 1:] < -90)          # tempo fino alla copertura R4 (sotto −90)
            dur = int(back[0]) + 1 if len(back) else np.nan
            r["durata_barre"] = dur
            r["durata_giorni"] = round(dur / bpd, 1) if dur == dur else np.nan
            if k == "scende sotto -90" and dur == dur:
                r["min_in_zona"] = round((L[t + 1:t + 1 + dur].min() / p0 - 1) * 100, 1)
            rows.append(r)
    ev = pd.DataFrame(rows).sort_values(["evento", "data"])
    return ev


def base(df, bpd):
    C = df.close.to_numpy(float); O = df.open.to_numpy(float)
    i0 = df.index.searchsorted(pd.Timestamp("2018-01-01"))
    out = {}
    for h in (7, 30, 60):
        j = np.arange(i0, len(C) - h * bpd - 1)
        out[f"r{h}"] = round(float(np.mean(C[j + h * bpd] / O[j + 1] - 1) * 100), 1)
        out[f"pos{h}"] = round(float(np.mean(C[j + h * bpd] / O[j + 1] - 1 > 0) * 100))
    return out


pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
say("# zeiierman3 · descrittivo (dal 01/01/2018, giornaliero UTC; rendimenti dall'apertura successiva al segnale)")
b1 = base(d, 1)
say("Base (tutti i giorni dal 2018):", b1)
allev = []
for line in ("tz", "pz", "cz"):
    ev = events(d, z1, line, 1); ev.insert(0, "linea_ind", line); allev.append(ev)
    g = ev.groupby("evento").agg(n=("r30", "size"), r7=("r7", "mean"), r30=("r30", "mean"), r60=("r60", "mean"),
                                 pos30=("r30", lambda s: (s.dropna() > 0).mean() * 100), min60_med=("min60", "median"),
                                 min60_peggiore=("min60", "min"), durata_med=("durata_giorni", "median")).round(1)
    say(f"\n## {line} 1D · sintesi per evento"); say(g.to_string())
    if line == "tz":
        say("\n## tz 1D · ogni evento"); say(ev.drop(columns="linea_ind").to_string(index=False))
pd.concat(allev).to_csv(D / "eventi_1d.csv", index=False)
b4 = base(a, 6)
ev4 = events(a, z4, "tz", 6)
ev4.to_csv(D / "eventi_4h_tz.csv", index=False)
g4 = ev4.groupby("evento").agg(n=("r30", "size"), r7=("r7", "mean"), r30=("r30", "mean"), r60=("r60", "mean"),
                               pos30=("r30", lambda s: (s.dropna() > 0).mean() * 100), min60_med=("min60", "median"),
                               durata_med=("durata_giorni", "median")).round(1)
say("\n## tz 4h · sintesi (base 4h:", b4, ")"); say(g4.to_string())

# ---------- oggi ----------
say("\n## Caso di oggi")
say("1D ultime 10 chiusure:\n" + pd.concat([d.close.round(0), z1[["tz", "pz", "cz", "core"]].round(1)], axis=1).tail(10).to_string())
say("4h ultime 8 candele (ora di apertura UTC):\n" + pd.concat([a.close.round(0), z4[["tz", "pz", "cz"]].round(1)], axis=1).tail(8).to_string())
for nm, z, df in (("1D", z1, d), ("4h", z4, a)):
    for rule, line, en, ex in (("R1", "tz", -90, -20), ("R2", "tz", -90, -20), ("R5", "tz", -70, -30)):
        if rule == "R5" and nm == "1D":
            continue
        e_, x_ = Z.rule_signals(z, rule, line, en, ex)
        last = np.flatnonzero(e_)[-1]
        say(f"{nm} {rule}: ultimo segnale d'ingresso alla chiusura {z.index[last]} (linea {z[line].iloc[last]:.1f}, chiusura "
            f"{df.close.iloc[last]:.0f}); oggi linea {z[line].iloc[-1]:.1f}")
open(D / "descrittivo.txt", "w").write("\n".join(OUT) + "\n")
