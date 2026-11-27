"""sol_ciclo · FASE 1 · A) rapporto descrittivo di W3.2 su SOL (replica di risultati già noti: research/w32_asset2 Q7).
Motore radar.weekly.simulate invariato (via research/w32_asset2/lib.py), dati congelati research/w32_asset2/crypto/data (fine 24/11/2026),
costi del motore (spot 0,1%, perp 0,05%, slittamento 0,1%) e funding reale dei perp Binance.
- Versione completa (flusso perp + funding): dal 2021-01-11 (primo lunedì con SMA40 e flusso calcolabili).
- Versione solo prezzo (descrittiva, = run_crypto.py "solo prezzo": ma_lib.s1_sim, W-SUN, 0,2%/lato, short 10% annuo): avvio 2020-04-10
  (primo dato spot); la SMA40 settimanale esiste solo da gennaio 2021, quindi il primo segnale possibile è comunque del 2021.
- Rischio allo stop 25/15/10%. Riferimenti nello stesso periodo: W3.2 BTC ed ETH (stesso motore, stessi dati congelati), B&H SOL/BTC/ETH.
Uscite: out_a.txt, trades_a.csv, equity_a.csv.gz, curva_a.svg. Nessuna variante V1–V3 qui."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "w32_asset2"))
import lib as L  # noqa: E402

S_FULL, S_PX = "2021-01-11", "2020-04-10"
OUT, TR, EQ = [], [], {}
RISKS = (0.25, 0.15, 0.10)
MOT = {"trail": "trailing", "stop": "stop iniziale", "ema": "EMA21", "dist": "distribuzione", "open": "aperta"}

def p(s=""):
    print(s, flush=True); OUT.append(s)

def px_sim(fp, a, e, r):
    fp = fp[fp.index <= pd.Timestamp(e)]
    return L.M.s1_sim(fp, a, e, risk=r, fee=0.002, short_cost=0.10, wb=L.M.s1_weekly(fp, "W-SUN"))

def px_met(o):
    return L.met(o["equity"], o["trades"], o["open"])

def px_trades(o, last):
    return o["trades"] + ([dict(o["open"], last=last)] if o["open"] else [])

def ddinfo(eq):
    e = eq.dropna(); dd = e / e.cummax() - 1; t = dd.idxmin(); pk = e[:t].idxmax()
    rec = e[t:][e[t:] >= e[pk]]
    return f"picco {pk.date()} → minimo {t.date()} ({dd.min() * 100:.1f}%), " + (f"recuperato il {rec.index[0].date()}" if len(rec) else "non ancora recuperato")

def yearly(eq):
    e = eq.dropna(); y = e.resample("YE").last(); y0 = pd.concat([pd.Series([e.iloc[0]], index=[e.index[0]]), y])
    return [(d.year, v) for d, v in zip(y.index, y0.pct_change().dropna())]

def table(trades, ver, r):
    rows, n = [], 0
    for t in trades:
        n += 1; op = not t.get("exit"); pn = t["pnl_close"] if (op and "pnl_close" in t) else t["pnl"]
        eq0 = t["eq0"] * 10000; ex = t.get("exit_px") if not op else t.get("last", t.get("exit_px"))
        d1 = pd.Timestamp(t["exit"]) if not op else pd.Timestamp(L.CEND)
        rows.append(dict(versione=ver, rischio=int(r * 100), n=n, lato=t["side"], segnale=t["signal"], entrata=t["entry"],
                         px_in=round(t["entry_px"], 2), esposizione=round(t["expo"], 3), uscita=t.get("exit") or f"aperta ({L.CEND})",
                         px_out=round(ex, 2), motivo=MOT.get(t.get("reason", "open"), t.get("reason")), giorni=(d1 - pd.Timestamp(t["entry"])).days,
                         mov_prezzo_pct=round(((ex / t["entry_px"] - 1) * (1 if t["side"] == "long" else -1)) * 100, 1),
                         pnl_conto_pct=round(pn * 100, 1), pnl_usd=round(eq0 * pn), conto_prima=round(eq0), conto_dopo=round(eq0 * (1 + pn))))
    return pd.DataFrame(rows)

def summary(name, m, tr_df, eq, b, extra=""):
    cl = tr_df[~tr_df.uscita.str.startswith("aperta")]; w = cl[cl.pnl_conto_pct > 0]
    gl = cl[cl.pnl_conto_pct > 0].pnl_conto_pct.sum(); ls = -cl[cl.pnl_conto_pct <= 0].pnl_conto_pct.sum()
    lo, sh = cl[cl.lato == "long"], cl[cl.lato == "short"]
    p(f"{name}: {m['fin']:,} $ ({m['ret']:+.0f}%, CAGR {m['cagr']}%), DD {m['dd']}%, CAGR/DD {m['cd']} · operazioni {len(cl)} chiuse + "
      f"{len(tr_df) - len(cl)} aperta, WR chiuse {len(w)}/{len(cl)} = {len(w) / len(cl) * 100:.0f}% (con l'aperta {m['wr']}%) · long {len(lo)} "
      f"(vinti {(lo.pnl_conto_pct > 0).sum()}), short {len(sh)} (vinti {(sh.pnl_conto_pct > 0).sum()}) · profit factor {gl / ls:.2f} · "
      f"senza il migliore {m['wo']:,} $ · B&H {b['fin']:,} $ (DD {b['dd']}%, C/DD {b['cd']}){extra}")
    p("   DD: " + ddinfo(eq)); p("   per anno: " + " · ".join(f"{y} {v * 100:+.0f}%" for y, v in yearly(eq)))

if __name__ == "__main__":
    f = L.cfeats("SOL"); E = str(f.index[-1].date()); fp = f[["open", "high", "low", "close"]]
    fb, fe = L.cfeats("BTC"), L.cfeats("ETH")
    p(f"SOL · dati spot dal {f.index[0].date()} (Binance; SOLBUSD fino all'11/08/2020), perp e funding dal 13–14/09/2020, fine {E}. "
      "Dal 2018 impossibile: SOL non esisteva sul mercato.")
    p(f"Verifica: BTC dal 2021-01-01 = {L.omet(L.csim(fb, '2021-01-01'))['fin']:,} $ (ufficiale 84.820 $)")
    bS = L.bh(f, S_FULL, E, 0.002); EQ["SOL_bh"] = L.bh_curve(f, S_FULL, E, 0.002)
    p(f"\n=== Riferimenti stesso periodo {S_FULL} → {E} (10.000 $, rischio 25%) ===")
    p(f"B&H SOL: {bS['fin']:,} $, CAGR {bS['cagr']}%, DD {bS['dd']}%, C/DD {bS['cd']}")
    REF = {}
    for nm, ff in (("BTC", fb), ("ETH", fe)):
        o = L.csim(ff, S_FULL, E); m = L.omet(o); b = L.bh(ff, S_FULL, E, 0.002); REF[nm] = (m, b); EQ[f"{nm}_w32"] = o["equity"]
        d = table(L.otrades(o), nm, 0.25); cl = d[~d.uscita.str.startswith("aperta")]
        p(f"W3.2 {nm}: {m['fin']:,} $, CAGR {m['cagr']}%, DD {m['dd']}%, C/DD {m['cd']}, {len(cl)} chiuse + {len(d) - len(cl)} aperta, "
          f"WR chiuse {(cl.pnl_conto_pct > 0).mean() * 100:.0f}% · B&H {nm} {b['fin']:,} $ (DD {b['dd']}%, C/DD {b['cd']})")
        for a, e in (("2021-01-11", "2023-12-31"), ("2024-01-01", E)):
            mm = L.omet(L.csim(ff, a, e)); p(f"   {nm} {a[:4]}–{e[:4]}: {mm['fin']:,} $, DD {mm['dd']}%")
        for r in (0.15, 0.10):
            mm = L.omet(L.csim(ff, S_FULL, E, r=r)); p(f"   {nm} rischio {int(r * 100)}%: {mm['fin']:,} $, DD {mm['dd']}%, C/DD {mm['cd']}")
    po = L.port([EQ["BTC_w32"], EQ["ETH_w32"]], S_FULL, E)[0]
    p(f"Conto unico BTC + ETH (capitali uguali e separati): {po}")

    p(f"\n=== A1 · W3.2 completa su SOL, dal {S_FULL} ===")
    for r in RISKS:
        o = L.csim(f, S_FULL, E, r=r); m = L.omet(o); d = table(L.otrades(o), "completa", r); TR.append(d); EQ[f"SOL_w32_r{int(r * 100)}"] = o["equity"]
        sp = []
        for lab, a, e in (("IS 2021–22", S_FULL, L.IS_END), ("OOS 2023→", L.OOS_START, E), ("2021–23", S_FULL, "2023-12-31"), ("2024→", "2024-01-01", E),
                          ("ultimi 12 mesi", "2025-11-25", E)):
            mm = L.omet(L.csim(f, a, e, r=r)); sp.append(f"{lab} {mm['ret']:+.0f}% (DD {mm['dd']})")
        summary(f"rischio {int(r * 100)}%", m, d, o["equity"], bS)
        p("   periodi (da flat): " + " · ".join(sp))
        if r == 0.25:
            m0 = L.omet(L.csim(f, "2021-01-10", E, r=r))
            p(f"   (sensibilità alla data) avvio domenica 2021-01-10, prima domenica calcolabile: {m0['fin']:,} $, DD {m0['dd']}% "
              "(il long entra il 2021-01-11 a 3,45 invece del 2021-01-18 a 3,83; convenzione w32_asset2 = lunedì dopo, 80.661 $)")
            for k in (2.0, 3.0):
                mk = L.omet(L.csim(f, S_FULL, E, r=r, k=k)); p(f"   (descrittivo) trailing {k}: {mk['fin']:,} $, DD {mk['dd']}%, WR {mk['wr']}%, C/DD {mk['cd']}")
            op = o["open"]
            p(f"   posizione aperta al {E}: {op['side']} dal {op['entry']} a {op['entry_px']}, ultimo {op['last']:.2f}, trailing {op['trail']:.2f}, "
              f"{op['pnl_close'] * 100:+.1f}% sul conto" if op else "   flat")
        p(d.drop(columns=["versione", "rischio"]).to_string(index=False))

    p(f"\n=== A2 · W3.2 solo prezzo su SOL (senza flusso perp, funding e distribuzione), avvio {S_PX} ===")
    for r in RISKS:
        o = px_sim(fp, S_PX, E, r); m = px_met(o); d = table(px_trades(o, float(fp["close"].iloc[-1])), "solo prezzo", r); TR.append(d); EQ[f"SOL_px_r{int(r * 100)}"] = o["equity"]
        b = L.bh(f, S_PX, E, 0.002); sp = []
        for lab, a, e in (("2020–22", S_PX, L.IS_END), ("2023→", L.OOS_START, E), ("2021–23", S_PX, "2023-12-31"), ("2024→", "2024-01-01", E)):
            mm = px_met(px_sim(fp, a, e, r)); sp.append(f"{lab} {mm['ret']:+.0f}% (DD {mm['dd']})")
        summary(f"solo prezzo rischio {int(r * 100)}%", m, d, o["equity"], b, extra=f" [B&H dal {S_PX}]")
        p("   periodi (da flat): " + " · ".join(sp))
        if r == 0.25: p(d.drop(columns=["versione", "rischio"]).to_string(index=False))
    ms = px_met(px_sim(fp, S_FULL, E, 0.25)); p(f"solo prezzo 25% dal {S_FULL} (stesso periodo della completa): {ms['fin']:,} $, DD {ms['dd']}%, {ms['n']} trade, WR {ms['wr']}%, C/DD {ms['cd']}")

    pd.concat(TR).to_csv(HERE / "trades_a.csv", index=False)
    eq = pd.DataFrame(EQ).sort_index(); eq.round(2).to_csv(HERE / "equity_a.csv.gz")
    # curva del conto (SVG semplice, scala logaritmica) dal 2021-01-11
    e = eq[eq.index >= S_FULL][["SOL_w32_r25", "SOL_w32_r15", "SOL_w32_r10", "SOL_px_r25", "SOL_bh", "BTC_w32", "ETH_w32"]].ffill()
    col = dict(SOL_w32_r25="#7b2cbf", SOL_w32_r15="#c77dff", SOL_w32_r10="#e0aaff", SOL_px_r25="#f4a261", SOL_bh="#999999", BTC_w32="#f7931a", ETH_w32="#3c6e71")
    Wd, Ht, pad = 1000, 480, 50; lo, hi = np.log10(e.min().min()), np.log10(e.max().max()); n = len(e)
    X = lambda i: pad + (Wd - 2 * pad) * i / (n - 1); Y = lambda v: Ht - pad - (Ht - 2 * pad) * (np.log10(v) - lo) / (hi - lo)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Ht}" font-family="sans-serif" font-size="11"><rect width="100%" height="100%" fill="white"/>']
    for v in (5000, 10000, 20000, 50000, 100000, 200000):
        if lo <= np.log10(v) <= hi: s.append(f'<line x1="{pad}" x2="{Wd - pad}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#eee"/><text x="2" y="{Y(v) + 4:.1f}">{v // 1000}k</text>')
    for yv in range(2021, 2027):
        i = e.index.searchsorted(pd.Timestamp(f"{yv}-01-01")); s.append(f'<text x="{X(i):.1f}" y="{Ht - 30}">{yv}</text>')
    for j, c in enumerate(e.columns):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(e[c].to_numpy()) if i % 3 == 0 or i == n - 1)
        s.append(f'<polyline fill="none" stroke="{col[c]}" stroke-width="1.6" points="{pts}"/><text x="{pad + 5}" y="{15 + 13 * j}" fill="{col[c]}">{c}: {e[c].iloc[-1]:,.0f} $</text>')
    s.append("</svg>"); (HERE / "curva_a.svg").write_text("\n".join(s))
    (HERE / "out_a.txt").write_text("\n".join(OUT) + "\n")
