"""Conteggi di osservazioni ed eventi SENZA alcun rendimento (lezione 98). Output: conteggi.txt.
I prezzi a 1 minuto servono qui solo a stabilire se un muro è stato toccato FRA due foto (definizione dell'evento),
mai per calcolare rendimenti successivi.
Uso: BS_WORK=<cache> python3 research/book_sentiment/bs_conteggi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bs_data as D  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def ac1(x):
    x = np.asarray(x, float)
    return float(np.corrcoef(x[:-1], x[1:])[0, 1]) if len(x) > 3 and np.std(x) > 0 else float("nan")


def runs(sign):
    s = np.asarray(sign)
    return int(1 + (s[1:] != s[:-1]).sum())


def dist(name, x):
    x = np.asarray(x, float)
    q = np.quantile(x, [0.05, 0.25, 0.5, 0.75, 0.95])
    say(f"  {name}: n {len(x)}  >0 {int((x > 0).sum())}  <0 {int((x < 0).sum())}  =0 {int((x == 0).sum())}  "
        f"quantili 5/25/50/75/95 {q[0]:+.3f} {q[1]:+.3f} {q[2]:+.3f} {q[3]:+.3f} {q[4]:+.3f}  autocorr(1) {ac1(x):+.2f}  "
        f"serie di segno {runs(np.sign(x))}")


def states(name, s, thr=D.THR):
    st = D.state(s, thr)
    chg = int(np.abs(np.diff(np.concatenate([[0], st]))).astype(bool).sum())
    say(f"  {name} soglia ±{thr}: rialzo {int((st == 1).sum())}  ribasso {int((st == -1).sum())}  neutro {int((st == 0).sum())}  "
        f"cambi di stato {chg}  serie {runs(st)}")


# =============================================================== A
say("=== INSIEME A · registro del book (data/orderbook.csv) + liquidazioni reali registrate ===")
b = D.book()
gap = b["t"].diff().dt.total_seconds().div(60).dropna()
say(f"foto: {len(b)} dal {b['t'].min()} al {b['t'].max()} UTC; giorni di calendario {b['t'].dt.normalize().nunique()}")
say("foto per giorno:", " ".join(f"{d:%d/%m}:{n}" for d, n in b.groupby(b['t'].dt.normalize()).size().items()))
say(f"intervallo fra foto (minuti): mediana {gap.median():.0f}, 90° {gap.quantile(.9):.0f}, max {gap.max():.0f}; "
    f"coppie consecutive ≤ 90 min: {int((gap <= 90).sum())}")
say(f"fonti del book a ±1% (src_1): {b['src_1'].value_counts().sort_index().to_dict()}; fonti totali {b['sources'].value_counts().to_dict()}")
say(f"profondità ±1% mediana: bid {b['bid_1'].median()/1e6:.0f} M$, ask {b['ask_1'].median()/1e6:.0f} M$")

ev = D.liq_live()
say("\nliquidazioni reali registrate (eventi):")
for ex, g in ev.groupby("exchange"):
    say(f"  {ex:10s} n {len(g):6d}  {g['t'].min():%d/%m %H:%M} → {g['t'].max():%d/%m %H:%M}  long {g.loc[g.side == 'long', 'usd'].sum()/1e6:8.1f} M$  "
        f"short {g.loc[g.side == 'short', 'usd'].sum()/1e6:8.1f} M$")
say("  (mancano Binance, Bybit, Hyperliquid: copertura stimata < 10% del totale di mercato, vedi research/liq_fasce)")

for w in (30, 60):
    p = D.panel_A(w)
    say(f"\nfinestra liquidazioni {w} minuti prima della foto:")
    say(f"  foto con ≥ 1 liquidazione: {int((p['liq_n'] > 0).sum())}/{len(p)}; con ≥ 100.000 $: {int(((p['liq_long'] + p['liq_short']) >= 1e5).sum())}; "
        f"con un solo lato (|L| = 1): {int((p['L'].abs() == 1).sum())}; $ mediani nella finestra {np.median(p['liq_long'] + p['liq_short']):,.0f}")
    dist("I (imb ±1%)", p["I"]) if w == 30 else None
    dist("L", p["L"])
    dist("S", p["S"])
    states("S", p["S"])
    for thr in (0.1, 0.3):
        states("S", p["S"], thr) if w == 30 else None
    if w == 30:
        states("I", p["I"]); states("L", p["L"])
        say(f"  correlazione I–L (Pearson) {np.corrcoef(p['I'], p['L'])[0, 1]:+.2f}; quota della varianza di S dovuta a L "
            f"{np.var(0.5 * p['L']) / np.var(p['S']):.0%}; segno di S = segno di L in {int((np.sign(p['S']) == np.sign(p['L'])).sum())}/{len(p)} foto")
        mid_t = p["t"].min() + (p["t"].max() - p["t"].min()) / 2
        for nm, g in (("metà 1", p[p["t"] <= mid_t]), ("metà 2", p[p["t"] > mid_t])):
            st = D.state(g["S"])
            say(f"  {nm} ({g['t'].min():%d/%m}–{g['t'].max():%d/%m}): foto {len(g)}, giorni {g['t'].dt.normalize().nunique()}, "
                f"rialzo {int((st == 1).sum())}, ribasso {int((st == -1).sum())}, neutro {int((st == 0).sum())}")
        pa = p

say(f"\nosservazioni indipendenti (insieme A): giorni {pa['t'].dt.normalize().nunique()}; blocchi di 4 ore "
    f"{pa['t'].dt.floor('4h').nunique()}; orizzonte 24h ≈ {int((pa['t'].max() - pa['t'].min()).total_seconds() // 86400)} finestre non sovrapposte")

# cascate reali nel registro (definizione di research/liq_fasce: ora ≥ 99,5° percentile e lato ≥ 75%; qui anche soglie fisse)
say("\ncascate di liquidazioni nel registro (griglia oraria, solo per contare):")
hh = ev.assign(h=ev["t"].dt.floor("h")).pivot_table(index="h", columns="side", values="usd", aggfunc="sum").fillna(0.0)
hh = hh.reindex(pd.date_range(hh.index.min(), hh.index.max(), freq="h")).fillna(0.0)
tot, share_long = hh.sum(axis=1), hh["long"] / hh.sum(axis=1).replace(0, np.nan)
for thr in (5e6, 10e6, 20e6):
    cl, cs = (tot >= thr) & (share_long >= 0.75), (tot >= thr) & (share_long <= 0.25)

    def epis(m):
        t = m[m].index
        return int(1 + (np.diff(t.values).astype("timedelta64[h]").astype(int) > 6).sum()) if len(t) else 0
    say(f"  ore con ≥ {thr/1e6:.0f} M$ e lato ≥ 75%: long {int(cl.sum())} (episodi a > 6 h {epis(cl)}), short {int(cs.sum())} (episodi {epis(cs)})")
q = tot.quantile(0.995)
say(f"  ore ≥ 99,5° percentile ({q/1e6:.1f} M$) e lato ≥ 75%: long {int(((tot >= q) & (share_long >= .75)).sum())}, short {int(((tot >= q) & (share_long <= .25)).sum())} su {len(tot)} ore")

# muri: registro per exchange e muro unico aggregato
say("\n=== MURI ===")
w = pd.read_csv(D.DATA / "book_walls.csv")
say(f"data/book_walls.csv (muri per exchange, top 3 per lato): {len(w)} righe, {w['ts'].nunique()} foto ({w['ts'].min()} → {w['ts'].max()}): "
    f"coppie di foto consecutive {max(0, w['ts'].nunique() - 1)}")
m1 = D.m1()
say(f"data/orderbook.csv: un solo muro per lato (fascia 0,05% più grande fra 0,1% e 2% dal mid, book aggregato).")
rows = []
for i in range(len(pa) - 1):
    a, c = pa.iloc[i], pa.iloc[i + 1]
    dt = (c["t"] - a["t"]).total_seconds() / 60
    if dt > 90:
        continue
    seg = m1[(m1.index > a["t"]) & (m1.index <= c["t"])]
    for side in ("bid", "ask"):
        px, usd = a[f"wall_{side}_px"], a[f"wall_{side}_usd"]
        if not (px > 0 and usd > 0) or seg.empty:
            continue
        big = usd >= 3 * a[f"{side}_1"] / 20                        # ≥ 3× la fascia media entro ±1% (come book_liq)
        touched = seg["low"].min() <= px if side == "bid" else seg["high"].max() >= px
        d1 = px / c["mid"] - 1
        inwin = (-0.02 <= d1 <= -0.001) if side == "bid" else (0.001 <= d1 <= 0.02)
        moved = abs(c[f"wall_{side}_px"] / px - 1) > 0.001           # il muro registrato dopo è a un altro livello
        drop = 1 - c[f"wall_{side}_usd"] / usd                       # se moved: il vecchio livello vale al più il nuovo massimo
        rows.append(dict(t=c["t"], side=side, big=big, touched=touched, inwin=inwin, moved=moved, drop=drop, dist=abs(a[f"wall_{side}_dist"])))
wl = pd.DataFrame(rows)
say(f"muri osservati in coppie di foto ≤ 90 min: {len(wl)} (bid {int((wl.side == 'bid').sum())}, ask {int((wl.side == 'ask').sum())}); "
    f"di cui ≥ 3× la fascia media: {int(wl.big.sum())}; distanza mediana dal prezzo {wl.dist.median():.3f}%")
base = wl[(~wl.touched) & wl.inwin & wl.moved]
say(f"  non toccati, ancora nella finestra registrabile, muro registrato dopo a un altro livello: {len(base)} "
    f"(bid {int((base.side == 'bid').sum())}, ask {int((base.side == 'ask').sum())})")
for nm, m in (("ritirato largo (nuovo massimo < vecchio muro)", base["drop"] > 0), ("ritirato −50%", base["drop"] >= 0.5), ("ritirato −70% (specifica)", base["drop"] >= 0.7)):
    g = base[m]
    say(f"  {nm}: {len(g)} (bid {int((g.side == 'bid').sum())}, ask {int((g.side == 'ask').sum())}); ≥ 3×: {int(g.big.sum())}; "
        f"giorni distinti {g.t.dt.normalize().nunique()}; entro 0,3% dal prezzo: {int((g.dist <= 0.3).sum())}")
wl.to_csv(HERE / "muri_coppie.csv", index=False)

# =============================================================== B
say("\n=== INSIEME B · archivio liquidazioni reali Binance COIN-M BTCUSD_PERP (solo L) ===")
e = D.cm_events()
pb = D.panel_B()
h1 = D.h1()
days = e["t"].dt.normalize().nunique()
say(f"eventi: {len(e)} dal {e['t'].min():%Y-%m-%d} al {e['t'].max():%Y-%m-%d}; giorni con file {days}; long {e.loc[e.side == 'long', 'usd'].sum()/1e6:.0f} M$, "
    f"short {e.loc[e.side == 'short', 'usd'].sum()/1e6:.0f} M$; evento mediano {e['usd'].median():,.0f} $")
say(f"ore: {len(pb)}; con ≥ 1 liquidazione nell'ora precedente {int(((pb.liq_long + pb.liq_short) > 0).sum())}; con ≥ 100.000 $ "
    f"{int(((pb.liq_long + pb.liq_short) >= 1e5).sum())}; candele orarie spot disponibili {int(pb['t'].isin(h1.index).sum())}")
dist("L (ora precedente)", pb["L"])
states("S = 0,5·L", pb["S"])
states("S = 0,5·L", pb["S"], 0.1)
states("S = 0,5·L", pb["S"], 0.3)
mid_t = pb["t"].min() + (pb["t"].max() - pb["t"].min()) / 2
for nm, g in (("metà 1", pb[pb["t"] <= mid_t]), ("metà 2", pb[pb["t"] > mid_t])):
    st = D.state(g["S"])
    say(f"  {nm} ({g['t'].min():%Y-%m-%d} → {g['t'].max():%Y-%m-%d}): ore {len(g)}, L>0 {int((g.L > 0).sum())}, L<0 {int((g.L < 0).sum())}, "
        f"rialzo {int((st == 1).sum())}, ribasso {int((st == -1).sum())}")
say(f"osservazioni indipendenti (insieme B): giorni {days}; finestre di 4 ore {len(pb) // 4}; ore con segnale non nullo {int((pb.L != 0).sum())}")

(HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")
