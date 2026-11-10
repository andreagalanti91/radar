"""W2 + MACD · migliorie M1–M9: tabella principale, split, 2018–20, vicini, pari DD, placebo. Uso: python3 run.py > results.txt"""
import random
from eng import *

f = load_repo()
fl = load_long(f)
r0 = W.simulate(f)
B = simulate(f)
assert [(a["entry"], a["exit"], a["entry_px"], a["exit_px"]) for a in r0["trades"]] == \
       [(a["entry"], a["exit"], a["entry_px"], a["exit_px"]) for a in B["trades"]]
assert np.allclose(r0["equity"].values, B["equity"].values, atol=1e-9)
print(f"Replica esatta della baseline: OK ({len(B['trades'])} trade, dati fino al {f.index[-1].date()})\n")


def m5(lv, young=True, macd=True):
    def fn(wk, d):
        ok = (wk["trend_age"] < 16 if young else True) and (wk["macd"] > wk["macd_sig"] if macd else True)
        return lv if ok else 1.0
    return fn


MAIN = {
    "W2 + MACD com'è": {},
    "M1 liquidità 3,5%": dict(idle=0.035),
    "M1 liquidità T-bill reali": dict(idle="tbill"),
    "M2a EMA21: 2 chiusure": dict(ema_n=2),
    "M2b EMA21: margine 0,5 ATR": dict(ema_buf=0.5),
    "M2c EMA21: chiusura giornaliera": dict(ema_daily=True),
    "M3a rientro rapido 6 sett.": dict(reentry_n=6),
    "M3b pausa 2 sett.": dict(cooldown=2),
    "M4 runner 3 ATR dopo +2R": dict(run_r=2, run_k=3.0),
    "M5 leva 1,3x regime migliore": dict(lev_fn=m5(1.3)),
    "M6 short D1 (senza flusso)": dict(short_noflow=True),
    "M7 R2 no ritest del top 1,5": dict(r2=1.5),
    "M9 trailing a cricchetto": dict(ratchet=True),
}
NEIGH = {
    "M1": {"3%": dict(idle=0.03), "4%": dict(idle=0.04)},
    "M2a": {"3 chiusure": dict(ema_n=3)},
    "M2b": {"0,25": dict(ema_buf=0.25), "1,0": dict(ema_buf=1.0)},
    "M3a": {"4 sett": dict(reentry_n=4), "8 sett": dict(reentry_n=8)},
    "M3b": {"1 sett": dict(cooldown=1), "4 sett": dict(cooldown=4)},
    "M4": {"3,5 ATR": dict(run_r=2, run_k=3.5), "4 ATR": dict(run_r=2, run_k=4.0), "1R": dict(run_r=1, run_k=3.0),
           "3R": dict(run_r=3, run_k=3.0)},
    "M5": {"1,5x": dict(lev_fn=m5(1.5)), "1,3x solo giovane": dict(lev_fn=m5(1.3, macd=False)),
           "1,3x solo MACD su": dict(lev_fn=m5(1.3, young=False)), "1,3x tutti i long": dict(lev_fn=lambda wk, d: 1.3)},
    "M6": {"D1+M9": dict(short_noflow=True, ratchet=True)},
    "M7": {"1,0": dict(r2=1.0), "2,0": dict(r2=2.0), "senza F1": dict(f1=False), "senza F1 + R2 1,5": dict(f1=False, r2=1.5)},
    "M9": {"trail 2,0+cricchetto": dict(ratchet=True, trail=2.0, stop=2.0), "trail 3,0+cricchetto": dict(ratchet=True, trail=3.0, stop=3.0),
           "trail 2,0 senza": dict(trail=2.0, stop=2.0), "trail 3,0 senza": dict(trail=3.0, stop=3.0)},
}
PER = {"2021-oggi": (f, "2021-01-01", None), "2021-23": (f, "2021-01-01", "2023-12-31"), "2024-oggi": (f, "2024-01-01", None),
       "2018-20": (fl, "2018-01-01", "2020-12-31")}
BASES = {k: simulate(ff, start=a, end=b) for k, (ff, a, b) in PER.items()}
BM = {k: metrics(v) for k, v in BASES.items()}


def row(name, kw, full=True):
    out = {}
    for k, (ff, a, b) in PER.items():
        r = simulate(ff, start=a, end=b, **kw)
        out[k] = (metrics(r), changed(BASES[k], r), r)
    m, ch, r = out["2021-oggi"]
    eqdd = ""
    if full:
        if abs(m["dd"] - BM["2021-oggi"]["dd"]) < 0.05:
            x, fb = 1.0, BM["2021-oggi"]["final"]
        else:
            x, fb = equal_dd_base(f, m["dd"])
        eqdd = f"{fb:>9,.0f} (x{x:.2f}) {100 * (m['final'] / fb - 1):+6.1f}%"
    s = (f"{name:<32}{m['final']:>10,.0f} {m['ret']:>+8.0f}% {m['dd']:>6.1f} {m['n']:>3} {m['wr']:>4.0f}% {m['mar']:>5.2f} "
         f"{ch[0]:>2}/{ch[1]:<2} {m['final_wo']:>9,.0f} | {eqdd} | ")
    for k in ("2021-23", "2024-oggi", "2018-20"):
        mm, cc, _ = out[k]
        s += f"{mm['ret']:>+6.0f}%/{mm['dd']:>5.1f}/{mm['mar']:>4.2f} ({cc[0]}/{cc[1]}) | "
    print(s)
    return out


HDR = (f"{'variante':<32}{'finale $':>10} {'rend.':>9} {'maxDD':>6} {'n':>3} {'WR':>5} {'MAR':>5} camb. {'senza best':>9} | "
       f"baseline a pari DD (leva)  diff | 2021-23 rend/DD/MAR (camb.) | 2024-oggi | 2018-20 (proxy) |")
print("== TABELLA PRINCIPALE dal 01/01/2021, 10.000 $, costi inclusi. MAR = CAGR/|maxDD giornaliero|. camb. = trade della baseline"
      " spariti / trade nuovi ==")
print(HDR)
b = bh(f)
print(f"{'Buy & hold BTC':<32}{b['final']:>10,.0f} {b['ret']:>+8.0f}% {b['dd']:>6.1f} {1:>3} {'':>5} {b['mar']:>5.2f}")
for k, (ff, a, bb) in PER.items():
    x = bh(ff, a, bb)
    print(f"   B&H {k}: {x['ret']:+.0f}% DD {x['dd']:.1f} MAR {x['mar']:.2f}")
RES = {}
for name, kw in MAIN.items():
    RES[name] = row(name, kw)
print("\n== VICINI ==")
print(HDR)
for g, d in NEIGH.items():
    for n, kw in d.items():
        RES[g + " " + n] = row(f"{g} · {n}", kw)

print("\n== TRADE DIVERSI DALLA BASELINE (2021-oggi) ==")
bk = {tkey(t): t for t in B["trades"]}
for name in MAIN:
    r = RES[name]["2021-oggi"][2]
    vk = {tkey(t): t for t in r["trades"]}
    gone, new = [bk[k] for k in bk if k not in vk], [vk[k] for k in vk if k not in bk]
    if gone or new:
        print(name)
        for t in gone:
            print(f"   − {t['side']:5} {t['entry']} → {t['exit']} {t['reason']:5} {t['pnl'] * 100:+6.1f}%")
        for t in new:
            print(f"   + {t['side']:5} {t['entry']} → {t['exit']} {t['reason']:5} {t['pnl'] * 100:+6.1f}% expo {t['expo']}")
    elif name.startswith("M5"):
        print(name, "· long a leva:", [(t["entry"], t["expo"], round(t["pnl"] * 100, 1)) for t in r["trades"] if t["expo"] > 1 and t["side"] == "long"])

print("\n== M1 · materialità ==")
for k, kw in (("3,5%", dict(idle=0.035)), ("T-bill", dict(idle="tbill")), ("3%", dict(idle=0.03)), ("4%", dict(idle=0.04))):
    r = simulate(f, **kw); m = metrics(r)
    flat = float((pd.Series([0]).size and 1) and 0)
    print(f"  {k}: finale {m['final']:,.0f} (+{m['final'] - BM['2021-oggi']['final']:,.0f} $, {100 * (m['final'] / BM['2021-oggi']['final'] - 1):+.1f}%), "
          f"CAGR {m['cagr']:.2f}% vs {BM['2021-oggi']['cagr']:.2f}% (+{m['cagr'] - BM['2021-oggi']['cagr']:.2f} punti), DD {m['dd']:.1f}")
e = B["equity"]; inpos = np.zeros(len(e), bool)
for t in B["trades"]:
    inpos |= (e.index >= t["entry"]) & (e.index < (t["exit"] or "2100"))
print(f"  giorni senza posizione dal 2021: {100 * (1 - inpos.mean()):.0f}% (long {100 * sum(((e.index >= t['entry']) & (e.index < t['exit'])).sum() for t in B['trades'] if t['side'] == 'long') / len(e):.0f}%, short il resto)")

print("\n== M8 · giorno di chiusura della candela settimanale (stesse regole) ==")
vals = []
for a in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"):
    s = f"  chiusura {a}: "
    for k, (ff, st, en) in PER.items():
        m = metrics(simulate(ff, start=st, end=en, anchor=a))
        s += f"{k} {m['final']:>9,.0f} $ DD {m['dd']:>5.1f} n {m['n']:>2} WR {m['wr']:>3.0f}% MAR {m['mar']:>4.2f} | "
        if k == "2021-oggi":
            vals.append((a, m["final"], m["dd"], m["mar"]))
    print(s)
fin = sorted(v[1] for v in vals)
print(f"  2021-oggi finale: min {fin[0]:,.0f} · mediana {fin[3]:,.0f} · max {fin[-1]:,.0f}; domenica = posto "
      f"{1 + sorted((v[1] for v in vals), reverse=True).index(vals[-1][1])}/7; MAR mediano {sorted(v[3] for v in vals)[3]:.2f}; "
      f"DD peggiore {min(v[2] for v in vals):.1f}")

print("\n== M5 · placebo (leva 1,3x su un sottoinsieme casuale di long, stessa numerosità; 1.000 prove) ==")
real = RES["M5 leva 1,3x regime migliore"]["2021-oggi"][0]
rr = RES["M5 leva 1,3x regime migliore"]["2021-oggi"][2]
longs = [t["signal"] for t in B["trades"] if t["side"] == "long"]
k = sum(1 for t in rr["trades"] if t["side"] == "long" and t["expo"] > 1)
random.seed(7)
pm, pf = [], []
for _ in range(1000):
    pick = set(random.sample(longs, k))
    m = metrics(simulate(f, lev_fn=lambda wk, d, pick=pick: 1.3 if str(d.date()) in pick else 1.0))
    pm.append(m["mar"]); pf.append(m["final"])
pm, pf = np.array(pm), np.array(pf)
print(f"  long a leva nella regola: {k} su {len(longs)}; reale MAR {real['mar']:.2f} finale {real['final']:,.0f}; placebo MAR mediano "
      f"{np.median(pm):.2f}, finale mediano {np.median(pf):,.0f}; p(MAR placebo ≥ reale) = {(pm >= real['mar']).mean():.3f}; "
      f"p(finale ≥ reale) = {(pf >= real['final']).mean():.3f}")

print("\n== M7 · 2018–2020 sui proxy: trade della baseline attuale (con F1) ==")
for nm, kw in (("con F1 (attuale)", {}), ("senza F1", dict(f1=False)), ("F1 + R2 1,5", dict(r2=1.5))):
    r = simulate(fl, start="2018-01-01", end="2020-12-31", **kw); m = metrics(r)
    print(f"  {nm}: {m['ret']:+.0f}% DD {m['dd']:.1f} n {m['n']} peggiore {m['worst']:.1f}%")
    if nm != "senza F1":
        for t in r["trades"]:
            print(f"      {t['side']:5} {t['entry']} → {t['exit']} {t['reason']:5} {t['pnl'] * 100:+6.1f}% età trend {t['age']}")
