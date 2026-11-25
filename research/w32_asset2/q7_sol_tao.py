"""Q7 · SOL e TAO (descrittivo) + scheda di robustezza di TRX con il cancello di BTC (unico candidato di Q4/Q6).
SOL dalla versione completa (11/01/2021), TAO dal 29/07/2024 (2,3 anni: solo descrittivo). Rischio 10/15/25%; operazioni una per
una; IS/OOS; B&H; BTC W3.2 e B&H nello stesso periodo; segnale attuale. Uscite: out_q7.txt, trades_q7.csv."""
import pandas as pd
import lib as L
import q4

out, TR = [], []
def p(s=""): print(s, flush=True); out.append(s)

def trades_table(o, name, r):
    rows = []
    for t in L.otrades(o):
        rows.append(dict(asset=name, rischio=r, segnale=t["signal"], ingresso=t["entry"], verso=t["side"], px_in=round(t["entry_px"], 4),
                         esposizione=t["expo"], uscita=t.get("exit") or "aperta", px_out=round(t.get("exit_px") or t["last"], 4),
                         motivo=L.W.REASONS.get(t.get("reason", "open"), t.get("reason", "open")), mov_prezzo_pct=round(t["move"] * 100, 1),
                         pnl_pct=round(t["pnl"] * 100, 1)))
    return pd.DataFrame(rows)

def yearly(eq):
    e = eq.dropna(); y = e.resample("YE").last(); y0 = pd.concat([pd.Series([10000.0], index=[e.index[0]]), y])
    return " · ".join(f"{d.year} {v * 100:+.0f}%" for d, v in zip(y.index, y0.pct_change().dropna()))

def study(t, S, gate=None, label=None):
    f = L.cfeats(t); E = str(f.index[-1].date()); name = label or t
    p(f"\n===== {name} · dal {S} al {E} =====")
    b = L.bh(f, S, E, 0.002); p(f"Buy & hold: {b['fin']} $, CAGR {b['cagr']}%, DD {b['dd']}%, CAGR/DD {b['cd']}")
    fb = L.cfeats("BTC"); ob = L.csim(fb, S); mb = L.omet(ob); bb = L.bh(fb, S, E, 0.002)
    p(f"BTC stesso periodo: W3.2 {mb['fin']} $, DD {mb['dd']}%, {mb['n']} trade, WR {mb['wr']}%, CAGR/DD {mb['cd']} · B&H {bb['fin']} $, DD {bb['dd']}%")
    ps, kind = L.periods(S, E)
    for r in (0.10, 0.15, 0.25):
        o = L.csim(f, S, E, r=r, gate=gate); m = L.omet(o); hs = [L.omet(L.csim(f, a, e, r=r, gate=gate)) for a, e in ps]
        tr = L.otrades(o); lo = [x["pnl"] for x in tr if x["side"] == "long"]; sh = [x["pnl"] for x in tr if x["side"] == "short"]
        p(f"rischio {int(r * 100)}%: {m['fin']} $ (CAGR {m['cagr']}%), DD {m['dd']}%, {m['n']} trade, WR {m['wr']}%, CAGR/DD {m['cd']}, senza il migliore "
          f"{m['wo']} $ · {kind}: {hs[0]['ret']:+.0f}% (DD {hs[0]['dd']}) / {hs[1]['ret']:+.0f}% (DD {hs[1]['dd']}) · long {len(lo)} (vinti {sum(x > 0 for x in lo)}), "
          f"short {len(sh)} (vinti {sum(x > 0 for x in sh)})")
        if r == 0.25:
            p(f"   per anno: {yearly(o['equity'])}")
            d = trades_table(o, name, r); TR.append(d); p(d.drop(columns=["asset", "rischio"]).to_string(index=False))
            d["anno"] = d.ingresso.str[:4]
            g = d.groupby(["anno", "verso"]).pnl_pct.agg(["count", "sum"]).round(1); p("   somma dei risultati per anno e verso (punti %):\n" + g.to_string())
            w = o["weekly"].iloc[-1]; op = o["open"]
            reg = "long" if (w.close > w.sma and w.ema20 > o["weekly"].ema20.iloc[-2]) else ("short" if w.close < w.sma else "neutro")
            p(f"   segnale attuale (ultima domenica {o['weekly'].index[-1].date()}): chiusura {w.close:.4g}, SMA40 {w.sma:.4g}, EMA21 {w.ema21:.4g}, flusso {w.flow:.2f}, "
              f"regime ~{reg}; posizione: " + (f"{op['side']} dal {op['entry']} a {op['entry_px']}, ultimo {op['last']:.4g}, trailing {op['trail']:.4g}, "
                                                 f"risultato {op['pnl'] * 100:+.1f}%" if op else "flat") + f"; decisione in sospeso: {o['pending']}")
    return f

if __name__ == "__main__":
    study("SOL", "2021-01-11")
    study("SOL", "2021-01-11", gate=q4.GATE, label="SOL con cancello BTC (Q4)")
    study("TAO", "2024-07-29")
    # TRX con cancello BTC (Q4): robustezza oltre il PREREG
    study("TRX", "2020-06-01", gate=q4.GATE, label="TRX con cancello BTC (Q4)")
    f = L.cfeats("TRX")
    for a, e in (("2021-01-01", "2023-12-31"), ("2024-01-01", L.CEND), ("2021-01-01", L.CEND)):
        m = L.omet(L.csim(f, a, e, gate=q4.GATE)); b = L.bh(f, a, e, 0.002)
        p(f"TRX(Q4) {a}→{e}: {m['fin']} $, DD {m['dd']}%, {m['n']} trade, WR {m['wr']}%, CAGR/DD {m['cd']} (B&H {b['fin']} $, DD {b['dd']}%, C/DD {b['cd']})")
    for k in (2.0, 3.0):
        m = L.omet(L.csim(f, "2020-06-01", gate=q4.GATE, k=k)); p(f"TRX(Q4) trailing {k}: {m['fin']} $, DD {m['dd']}%, WR {m['wr']}%, CAGR/DD {m['cd']}")
    pd.concat(TR).to_csv(L.HERE / "trades_q7.csv", index=False)
    (L.HERE / "out_q7.txt").write_text("\n".join(out) + "\n")
