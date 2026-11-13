"""Domande 1 e 4 (descrittive): la cascata del 12–13/11/2026 sulla mappa stimata, sugli S/R e sui livelli reali on-chain.
Uso: python research/liq_fasce/q1_q4_evento.py  → evento.txt, evento_fasce.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
from lf_data import hourly, map_at  # noqa: E402
from radar import levels, liqmap  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

ROOT = HERE.parents[1]
out = []
P = lambda s="": out.append(str(s)) or print(s)
nf = lambda x: f"{x:,.0f}".replace(",", ".")
h = hourly()
f = build_features(load_all())
ev = pd.read_csv(ROOT / "data/liq_events/2026-11.csv")
ev["t"] = pd.to_datetime(ev["ts"], unit="ms")

P("== Candele orarie 12/11 08:00 → ultima ora chiusa (UTC)")
x = h.loc["2026-11-12 08:00":, ["open", "high", "low", "close"]].copy()
x["ret%"] = (x["close"] / x["open"] - 1) * 100
r = ev[ev["t"] >= "2026-11-12 08:00"].groupby([ev["t"].dt.floor("h"), "side"])["usd"].sum().unstack().fillna(0) / 1e6
x = x.join(r.rename(columns={"long": "liq_long_M", "short": "liq_short_M"})).fillna(0)
P(x.round(2).to_string())

for name, T, lo_t, hi_t in (("Fase A (12/11 11:00–15:00)", pd.Timestamp("2026-11-12 11:00"), "2026-11-12 11:00", "2026-11-12 15:00"),
                            ("Fase B (13/11 00:00–05:00)", pd.Timestamp("2026-11-13 00:00"), "2026-11-13 00:00", "2026-11-13 05:00")):
    p, w, dn, up = map_at(h, T)
    seg = h.loc[lo_t:hi_t]
    low = float(seg["low"].min()); t_low = seg["low"].idxmin()
    lv = levels.compute(f[f.index < T.normalize()])
    P(f"\n== {name}: mappa stimata alla vigilia (ore fino a {T - pd.Timedelta(hours=1)}), prezzo {nf(p)}, minimo {nf(low)} alle {t_low}")
    P(f"   squilibrio ±5%: {liqmap.imbalance(w, p, 0.05)}; ±10%: {liqmap.imbalance(w, p, 0.10)}")
    rows = []
    for c in dn:
        c["sr"] = liqmap.confluence(c, lv)
        c["attraversata"] = low <= c["price"]
        rows.append(dict(fase=name[:6], lato="long sotto", **c))
    for c in up[:6]:
        c["sr"] = liqmap.confluence(c, lv)
        rows.append(dict(fase=name[:6], lato="short sopra", **c, attraversata=False))
    D = pd.DataFrame(rows)
    P(D[["lato", "price", "usd", "dist_pct", "rel", "sig", "sr", "attraversata"]].assign(usd=lambda d: (d.usd / 1e6).round(1)).to_string(index=False))
    tot = w[(w.price < p) & (w.price >= low)]["long"].sum()
    P(f"   long stimati fra {nf(low)} e {nf(p)}: ${tot / 1e6:,.0f}M (Binance USDT-M, stima)")
    P("   supporti (S/R della dashboard, dati giornalieri fino al giorno prima): " +
      "; ".join(f"S{i+1} {nf(s['lo'])}–{nf(s['hi'])} (forza {s['strength']}){' attraversato' if low <= s['hi'] else ''}" for i, s in enumerate(lv["supports"][:5])))
    P("   resistenze: " + "; ".join(f"R{i+1} {nf(s['lo'])}–{nf(s['hi'])}" for i, s in enumerate(lv["resistances"][:4])))
    D.to_csv(HERE / f"evento_fasce_{name[5]}.csv", index=False)

# Dopo: cosa resta sopra e sotto (mappa all'ultima ora chiusa)
T = h.index[-1] + pd.Timedelta(hours=1)
p, w, dn, up = map_at(h, T)
lv = levels.compute(f)
P(f"\n== Dopo la cascata: mappa con ore fino a {h.index[-1]} (OI {h.attrs.get('oi_info')}), prezzo {nf(p)}")
P("   fasce dense long sotto: " + "; ".join(f"{nf(c['price'])} ({c['dist_pct']:+.1f}%, ${c['usd']/1e6:.0f}M)" for c in dn if c["rel"] >= 0.3))
P("   fasce dense short sopra: " + "; ".join(f"{nf(c['price'])} ({c['dist_pct']:+.1f}%, ${c['usd']/1e6:.0f}M)" for c in up if c["rel"] >= 0.3))
P(f"   squilibrio ±5%: {liqmap.imbalance(w, p, 0.05)}")
P("   supporti: " + "; ".join(f"{nf(s['lo'])}–{nf(s['hi'])}" for s in lv["supports"][:4]) + " | resistenze: " + "; ".join(f"{nf(s['lo'])}–{nf(s['hi'])}" for s in lv["resistances"][:4]))

# Eventi reali per fascia di prezzo durante la cascata (6 exchange senza Binance/Bybit)
P("\n== Liquidazioni reali registrate (data/liq_events: OKX, Gate, Deribit, Kraken, dYdX, Lighter; NON Binance/Bybit)")
for a, b in (("2026-11-12 11:00", "2026-11-12 16:00"), ("2026-11-13 00:00", "2026-11-13 06:00")):
    e = ev[(ev["t"] >= a) & (ev["t"] < b)]
    P(f"   {a} → {b}: long ${e[e.side=='long'].usd.sum()/1e6:.1f}M, short ${e[e.side=='short'].usd.sum()/1e6:.1f}M; per exchange " +
      ", ".join(f"{k} {v/1e6:.1f}M" for k, v in e.groupby('exchange').usd.sum().items()))
    eb = e[e.side == "long"].groupby((e.price // 500) * 500)["usd"].sum() / 1e6
    P("     long per fascia di 500 $: " + ", ".join(f"{nf(k)} {v:.1f}M" for k, v in eb.sort_index(ascending=False).items() if v >= 0.5))

# Domanda 4: livelli reali on-chain prima e dopo
P("\n== Domanda 4 · livelli reali Hyperliquid + Lighter (data/liqsnap, conti ≥ $1M)")
S = pd.concat([pd.read_csv(ROOT / f"data/liqsnap/{x}_2026-11.csv.gz").assign(ex=x) for x in ("hl", "lighter")])
S["lo"] = S["mid"] * (1 + S["k"] * 0.0025)
S["hi"] = S["mid"] * (1 + (S["k"] + 1) * 0.0025)
for ts, low in (("2026-11-12T10:55", float(h.loc["2026-11-12 11:00":"2026-11-12 15:00", "low"].min())),
                ("2026-11-13T00:11", float(h.loc["2026-11-13 00:00":"2026-11-13 05:00", "low"].min()))):
    s = S[S.ts == ts]
    mid = float(s["mid"].iloc[0])
    lg = s[s.long_usd > 0]
    crossed = lg[lg.hi > low]
    P(f"   fotografia {ts} (mid {nf(mid)}), minimo successivo {nf(low)}: long liquidabili totali ±15% ${lg.long_usd.sum()/1e6:.0f}M; "
      f"nelle fasce attraversate ${crossed.long_usd.sum()/1e6:.1f}M (HL {crossed[crossed.ex=='hl'].long_usd.sum()/1e6:.1f}M, Lighter {crossed[crossed.ex=='lighter'].long_usd.sum()/1e6:.1f}M, posizioni {int(crossed.n_long.sum())})")
    big = lg.groupby(((lg.lo + lg.hi) / 2 // 250) * 250)["long_usd"].sum().sort_values(ascending=False).head(6) / 1e6
    P("     fasce long più grandi: " + ", ".join(f"{nf(k)} ${v:.1f}M{' (attraversata)' if k + 250 > low else ''}" for k, v in big.items()))
    sh = s[s.short_usd > 0].groupby(((s.lo + s.hi) / 2 // 250) * 250)["short_usd"].sum().sort_values(ascending=False).head(4) / 1e6
    P("     fasce short più grandi: " + ", ".join(f"{nf(k)} ${v:.1f}M" for k, v in sh.items()))
last = S[S.ts == S.ts.max()]
mid = float(last["mid"].iloc[0])
P(f"   ultima fotografia {S.ts.max()} (mid {nf(mid)}): long sotto entro −5% ${last[(last.lo >= mid*0.95)].long_usd.sum()/1e6:.1f}M, entro −10% ${last[(last.lo >= mid*0.90)].long_usd.sum()/1e6:.1f}M; "
  f"short sopra entro +5% ${last[(last.hi <= mid*1.05)].short_usd.sum()/1e6:.1f}M, entro +10% ${last[(last.hi <= mid*1.10)].short_usd.sum()/1e6:.1f}M")
(HERE / "evento.txt").write_text("\n".join(out) + "\n")
