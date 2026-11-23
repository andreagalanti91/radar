"""ADDENDUM.md (commit 73583f7): regola "flip" dei livelli orizzontali. ESPLORATIVO. Output: flip.txt, flip_trade.csv.
Uso: python3 fg_flip.py"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research" / "swing_sr"))
import fg_lib as G  # noqa: E402
import fg_engine as E  # noqa: E402
import fg_run as R  # noqa: E402
import sw_engine as S  # noqa: E402
from radar import levels as LV  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

OUT = []
REF = "2026-10-07"


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def main():
    fb = G.btc()
    f = G.add_flows(fb)
    sg = S.signals(fb)
    idx = sg["idx"]
    ks = G.klass(f, 3, -1, 0.5)
    rng = np.random.default_rng(20261123)
    rows = []
    say("=== F1/F2 · short alla perdita del livello / sul ritest respinto · BTC 2021-01-01 → 2026-11-15 (10.000 $, 1x)")
    for nm, ent in (("F1 perdita del livello", "X"), ("F2 ritest respinto", "T")):
        r = S.simulate(sg, ent, "R0", "S", "SS", "TSR", "2021-01-01")
        m = S.metrics(r)
        h = [S.metrics(S.simulate(sg, ent, "R0", "S", "SS", "TSR", a, b)) for a, b in (("2021-01-01", "2023-12-31"), ("2024-01-01", None))]
        say(f"{nm}: finale {m['fin']} $ · DD {100 * m['dd']:.1f}% · trade {m['n']} · WR {100 * m['wr']:.0f}% · PF {m['pf']:.2f} · media {100 * m['avg']:+.2f}% · "
            f"peggiore {100 * m['worst']:.1f}% · durata mediana {m['days']:.0f} g · 2021–23 {h[0]['fin']} $ (PF {h[0]['pf']:.2f}) · 2024→ {h[1]['fin']} $ (PF {h[1]['pf']:.2f})")
        pn, lab = [], []
        for t in r["trades"]:
            sd = idx[t["i0"] - 1]   # giorno del segnale
            c = ks.get(sd, "nd")
            pn.append(t["pnl"]); lab.append(c)
            rows.append(dict(regola=nm, segnale=str(sd.date()), ingresso=str(t["entry"].date()), prezzo=round(t["entry_px"], 0), stop=round(t["stop"], 0),
                             obiettivo=round(t["tgt"], 0) if t["tgt"] else None, uscita=str(t["exit"].date()), motivo=t["reason"],
                             pnl_pct=round(100 * t["pnl"], 2), classe_vendita=c, sz3=round(float(f["sz3"].get(sd, np.nan)), 2)))
        pn, lab = np.array(pn), np.array(lab)
        for c in ("spot", "perp", "misto"):
            x = pn[lab == c]
            if len(x):
                say(f"   classe {c}: n {len(x)} · WR {100 * (x > 0).mean():.0f}% · media {100 * x.mean():+.2f}% · somma {100 * x.sum():+.1f}%")
        sp = lab == "spot"
        if sp.sum() >= 2 and (~sp).sum() >= 2:
            obs = pn[sp].mean() - pn[~sp].mean()
            pl = np.array([(lambda q: pn[q].mean() - pn[~q].mean())(rng.permutation(sp)) for _ in range(5000)])
            say(f"   F{1 if ent == 'X' else 2}s: spot − resto {100 * obs:+.2f} punti per trade · p {float((np.abs(pl) >= abs(obs)).mean()):.3f} (permutazione, bilaterale)")
            eq = 10000 * np.prod(1 + pn[sp])
            say(f"   solo segnali 'spot' (trade in sequenza, composto): {eq:.0f} $ con {int(sp.sum())} trade")
    pd.DataFrame(rows).to_csv(HERE / "flip_trade.csv", index=False)
    t26 = [r for r in rows if r["segnale"] >= "2026-08-01" and r["regola"].startswith("F1")]
    say("F1 nel calo del 2026: " + "; ".join(f"{r['segnale']} short @{r['prezzo']:.0f} → {r['motivo']} {r['uscita']} {r['pnl_pct']:+.1f}%" for r in t26))

    say("\n=== F3 · W3.2 con uscita alla perdita del livello swing (rientro come E-out)")
    per = {"ALL": (fb, "2021-01-01", None), "IS": (fb, "2021-01-01", "2023-12-31"), "OOS": (fb, "2024-01-01", None)}
    n = len(idx)
    xs, xl = sg["sig"][("X", -1)], sg["sig"][("X", 1)]
    kb = G.klass(f, 3, 1, 0.5).reindex(idx).to_numpy()
    kss = ks.reindex(idx).to_numpy()
    cfgs = {"F3 ogni perdita del livello": (xs, xl), "F3s solo guidata dallo spot": (xs & (kss == "spot"), xl & (kb == "spot"))}
    base = {p: R.met(E.simulate(fr, None, start=s, end=e)) for p, (fr, s, e) in per.items()}
    say("W3.2: " + " | ".join(f"{p} {base[p]['final']} $ DD {base[p]['dd']} CDD {base[p]['cdd']} WR {base[p]['wr']}" for p in per))
    for nm, trig in cfgs.items():
        res = {p: E.simulate(fr, dict(eout=dict(trig=trig, frac=1.0)), start=s, end=e) for p, (fr, s, e) in per.items()}
        m = {p: R.met(res[p]) for p in per}
        g = R.groups(res["ALL"], E.simulate(fb, None))
        dv = np.array(list(g.values()))
        say(f"{nm}: " + " | ".join(f"{p} {m[p]['final']} $ DD {m[p]['dd']} CDD {m[p]['cdd']} WR {m[p]['wr']}" for p in per)
            + f" | uscite {sum(1 for a in res['ALL']['log'] if a[1] == 'uscita')} · ΣΔ {100 * dv.sum():+.1f} · p segni {R.signflip(dv)[0]:.3f}")

    say("\n=== Livelli del trader contro i livelli oggettivi")
    lv = S.levels(fb)
    d = load_all()
    ff = build_features(d)
    ff = ff[ff["close"].notna()]
    for name, px in (("81,4k", 81400), ("74,4k", 74400), ("62,5k", 62500), ("60,3k", 60300), ("55,1k (minimo)", 55100), ("48k (obiettivo)", 48000)):
        prev = pd.Timestamp(REF)   # livelli noti a questa data (vigilia della prima perdita di 81,6k nel calo di ottobre)
        act = sorted(p for a, b, p in lv if a <= prev < b)
        near = min(act, key=lambda p: abs(p / px - 1)) if act else np.nan
        born = [str(a.date()) for a, b, p in lv if p == near][:1]
        z = LV.compute(ff[ff.index <= prev])
        allz = z["supports"] + z["resistances"]
        nz = min(allz, key=lambda o: abs(o["price"] / px - 1)) if allz else None
        say(f"{name}: al {REF} swing settimanale più vicino {near:.0f} ({100 * (near / px - 1):+.1f}%, noto dal {born[0] if born else '?'}) · "
            f"radar/levels zona più vicina {nz['price']:.0f} [{nz['lo']:.0f}–{nz['hi']:.0f}] ({100 * (nz['price'] / px - 1):+.1f}%, forza {nz.get('strength')})")
    (HERE / "flip.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
