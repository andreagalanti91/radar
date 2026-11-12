"""Ciclo 1 · vicini, coerenza delle zone, analisi degli errori, W3 per periodo. Uso: python analisi.py > analisi.txt"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/home/user/radar/research/zeiierman")
from ztp import ztp, atr, load_daily, load_4h
from bt import simulate, metrics, PER, PER4, RULES, CAP, D

pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400)
df = load_daily(); z = ztp(df)

# 1) Vicini (uno alla volta, ±1 passo), totale dal 2021, 1x
NB = [("fl", 18), ("fl", 24), ("sl", 50), ("sl", 60), ("ml", 110), ("ml", 130), ("zn", 18), ("zn", 22), ("sn", 6), ("sn", 8)]
def neighbours(data, per, bpy, fd, configs, tf):
    rows = []; zs = {f"{k}={v}": ztp(data, **{k: v}) for k, v in NB}
    for r, side, stop in configs:
        fins = []
        for name, zz in zs.items():
            t, cv = simulate(data, zz, r, side, stop, 1.0, *per["tot"], fd); fins.append(round(cv.iloc[-1]))
        rows.append(dict(tf=tf, regola=r, lato="long" if side > 0 else "short", stop="2.5ATR" if stop else "no",
                         vicini_in_profitto=sum(f > CAP for f in fins), mediana=int(np.median(fins)), minimo=min(fins), massimo=max(fins)))
    return pd.DataFrame(rows)
cfg = [(r, s, st) for r in RULES for s in (1, -1) for st in (True, False) if not (r == "R2" and s == 1)]
print("== VICINI (10 per configurazione: fl 18/24, sl 50/60, ml 110/130, zn 18/22, sn 6/8), finale da 10k dal 2021 a 1x")
nb = pd.concat([neighbours(df, PER, 365, 1.0, cfg, "1D"),
                neighbours(load_4h(), PER4, 365 * 6, 6.0, [("R2v", 1, True), ("R2v", 1, False), ("R3", 1, False)], "4h")])
print(nb.to_string(index=False)); nb.to_csv(D + "vicini.csv", index=False)

# 2) Coerenza delle zone (1D dal 2021)
c = df.close; o = df.open; tz = z.tz
def fwd(mask, name):
    idx = np.where(mask & (df.index >= "2021-01-01"))[0]; idx = idx[idx + 1 < len(df)]
    r = {}
    for hzn in (7, 30, 60):
        v = [(c.iloc[i + hzn] / o.iloc[i + 1] - 1) * 100 for i in idx if i + hzn < len(df)]
        r[f"n{hzn}"] = len(v); r[f"med_{hzn}g"] = round(np.mean(v), 1) if v else np.nan; r[f"pos_{hzn}g_%"] = round(np.mean(np.array(v) > 0) * 100) if v else np.nan
    return dict(evento=name, **r)
prev = tz.shift()
ev = {
    "blu visiva: ingresso (tz<=-70)": (tz <= -70) & ~(prev <= -70),
    "blu visiva: rilascio (tz>-70)": (tz > -70) & (prev <= -70),
    "blu letterale: inizio (pz,tz<=-70)": z.blue & ~z.blue.shift(fill_value=False),
    "rossa visiva: ingresso (tz>=-30)": (tz >= -30) & ~(prev >= -30),
    "rossa visiva: rilascio (tz<-30)": (tz < -30) & (prev >= -30),
    "rossa letterale: inizio": z.red & ~z.red.shift(fill_value=False),
    "est autore: us (inizio esaurimento rosso)": z.us,
    "est autore: ubk (rilascio rosso)": z.ubk,
    "est autore: ls/lbk (blu)": z.ls | z.lbk,
}
base = fwd(pd.Series(True, index=df.index), "tutti i giorni (base)")
co = pd.DataFrame([base] + [fwd(m.to_numpy(), k) for k, m in ev.items()])
print("\n== COERENZA: rendimento medio % del prezzo (apertura del giorno dopo -> chiusura a 7/30/60 g) e % positivi")
print(co.to_string(index=False)); co.to_csv(D + "coerenza_eventi.csv", index=False)

def episodes(mask, gap=5):
    m = mask.to_numpy() & (df.index >= "2021-01-01"); eps = []; i = 0; n = len(m)
    while i < n:
        if m[i]:
            j = i
            while True:
                k = j + 1
                while k < n and not m[k] and k - j <= gap: k += 1
                if k < n and m[k] and k - j <= gap + 1: j = k
                else: break
            eps.append((i, j)); i = j + 1
        else: i += 1
    return eps
rows = []
for name, mask, s in (("blu", tz <= -70, 1), ("rossa", tz >= -30, -1)):
    for a, b in episodes(mask):
        e0 = c.iloc[a]; seg = df.iloc[a:b + 1]
        rows.append(dict(zona=name, inizio=df.index[a].date(), fine=df.index[b].date(), giorni=b - a + 1,
                         rend_prezzo_in_zona=round((c.iloc[b] / e0 - 1) * 100, 1),
                         min_vs_ingresso=round((seg.low.min() / e0 - 1) * 100, 1), max_vs_ingresso=round((seg.high.max() / e0 - 1) * 100, 1),
                         rend_30g_dopo_fine=round((c.iloc[min(b + 30, len(c) - 1)] / c.iloc[b] - 1) * 100, 1)))
ep = pd.DataFrame(rows)
print("\n== EPISODI DI ZONA VISIVA dal 2021 (gap <= 5 barre fusi); prezzo alla chiusura d'ingresso")
print(ep.to_string(index=False)); ep.to_csv(D + "episodi_zone.csv", index=False)
for name in ("blu", "rossa"):
    e = ep[ep.zona == name]
    print(f"{name}: {len(e)} episodi, durata mediana {e.giorni.median():.0f} g (max {e.giorni.max()}), rend. in zona mediano "
          f"{e.rend_prezzo_in_zona.median():+.1f}%, peggior escursione {'min' if name=='blu' else 'max'} "
          f"{(e.min_vs_ingresso.min() if name=='blu' else e.max_vs_ingresso.max()):+.1f}%")

# 3) Analisi degli errori: le 2 migliori del 1D per MAR + la migliore 4h
A1 = atr(df, 14)
def classify(t, data, A, side):
    out = []
    for _, r in t[t["pnl_%"] <= 0].iterrows():
        i = data.index.get_loc(r.ingresso); j = data.index.get_loc(r.uscita); sig = i - 1
        pre = side * (data.close.iloc[sig] - data.close.iloc[max(sig - 5, 0)]) / A[sig]
        seg = data.iloc[i:j + 1]
        mae = ((seg.low.min() / r.px_in - 1) * 100) if side > 0 else ((1 - seg.high.max() / r.px_in) * 100)
        if pre > 2: k = "ingresso tardivo"
        elif r.barre <= 10: k = "rilascio falso"
        elif r.barre > 30 and mae < -15: k = "zona lunga in trend forte"
        else: k = "laterale"
        out.append(dict(ingresso=r.ingresso.date(), uscita=r.uscita.date(), motivo=r.motivo, barre=r.barre, pnl=round(r["pnl_%"], 1),
                        mosso_prima_ATR=round(pre, 1), escursione_avversa=round(mae, 1), classe=k))
    return pd.DataFrame(out)
print("\n== ERRORI (trade perdenti, classificazione meccanica preregistrata)")
for tf, data, per, fd, r, side, stop in (("1D", df, PER, 1.0, "R1v", 1, True), ("1D", df, PER, 1.0, "R1v", -1, True),
                                          ("4h", load_4h(), PER4, 6.0, "R2v", 1, True)):
    zz = z if tf == "1D" else ztp(data); A = A1 if tf == "1D" else atr(data, 14)
    t, cv = simulate(data, zz, r, side, stop, 1.0, *per["tot"], fd)
    cl = classify(t, data, A, side)
    print(f"\n-- {tf} {r} {'long' if side>0 else 'short'} stop={stop}: {len(t)} trade, {len(cl)} perdenti")
    print(cl.to_string(index=False)); print(cl.classe.value_counts().to_string())
    cl.to_csv(f"{D}trades/errori_{tf}_{r}_{'long' if side>0 else 'short'}.csv", index=False)

# 4) W3 per periodo (dalla lista trade: rendimento composto per data d'ingresso)
w = pd.read_csv("/home/user/radar/research/weekly_w3_trades.csv", parse_dates=["ingresso"])
for p, (s, e) in PER.items():
    x = w[(w.ingresso >= s) & (w.ingresso <= e)]
    print(f"W3 {p}: {len(x)} trade, 10k -> {CAP*np.prod(1+x['pnl_capitale_%']/100):,.0f}")
