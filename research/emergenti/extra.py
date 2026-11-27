"""emergenti · analisi descrittive dopo run.py (non giudicate): affermazione "i long sono in netto positivo" (tutti i segnali
long dei candidati V1, per anno e per gruppo), V3 per anno, V3 con leva (a posteriori, solo descrittivo), long dello scanner.
Scrive data/out_extra.txt."""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; sys.argv = ["x"]; sys.path.insert(0, str(HERE))
import run as R
L = []; p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
c = pd.read_csv(R.D / "trades_V1_tutti_candidati.csv"); c["anno"] = c.entry.str[:4]
def st(x):
    return f"n {len(x)}, WR {(x.pnl > 0).mean() * 100:.0f}%, media {x.pnl.mean() * 100:+.1f}%, mediana {x.pnl.median() * 100:+.1f}%, somma {x.pnl.sum() * 100:+.0f}% (per 1 $ di quota, size W3.2)"
p("SEGNALI CANDIDATI V1 (tutti, prima del tetto di 5 posizioni; esito per quota con la size di W3.2, costi 0,2%/lato)")
for side in ("long", "short"):
    x = c[c.side == side]; p(f"{side}: " + st(x))
    for a, g in x.groupby("anno"): p(f"  {a}: " + st(g))
    for b, lab in ((1, "con BTC"), (-1, "contro BTC"), (0, "BTC flat")): p(f"  {lab}: " + st(x[x.btc == b]))
    p("  storia < 52 settimane: " + st(x[x.sett < 52])); p("  storia >= 52 settimane: " + st(x[x.sett >= 52]))
    p("  ultimi 12 mesi (ingresso dal 24/11/2025): " + st(x[x.entry >= "2025-11-24"]))
for v in ("V2", "V3"):
    t = pd.read_csv(R.D / f"trades_{v}.csv"); t["anno"] = t.entry.str[:4]
    p(f"\n{v} operazioni eseguite (portafoglio): " + st(t))
    for a, g in t.groupby("anno"): p(f"  {a}: " + st(g))
# V3 con leva (a posteriori, descrittivo)
s, e = R.PER["intero"]; trs = R.tradeset(s, e, {}, "short")
for name, kf in (("V3 leva adattiva 2x", R.k_adapt(2)), ("V3 2x fisso", lambda tr: 2.0), ("V3 nozionale 1x", lambda tr: 1.0)):
    m = R.evaluate(R.cands(trs, kf), s, e)[0]; p(f"{name} (a posteriori): " + R.fmt(m))
for per in R.PER:
    m = R.evaluate(R.cs_for("short", {}, R.K_W32, *R.PER[per]), *R.PER[per])[0]; p(f"V3 {per}: " + R.fmt(m))
# V3: posizioni aperte, semestri, robustezza (richieste della revisione critica)
cs3 = R.cs_for("short", {}, R.K_W32, s, e); m3, eq3, tk3 = R.evaluate(cs3, s, e)
op = [x for x in tk3 if x["reason"] == "open"]
p(f"\nV3 finale {m3['fin']} $: posizioni aperte {len(op)} (ingressi {sorted(set(x['entry'] for x in op))}), valore non realizzato {sum(x['m'] * x['pnl'] for x in op):+.0f} $ su {m3['fin'] - 10000:+.0f} $")
x = pd.Series(eq3, index=R.G[R.G.searchsorted(pd.Timestamp(s)):][:len(eq3)])
sem = x.resample("6MS").last(); prev = pd.concat([pd.Series([10000.0]), sem.iloc[:-1]]).to_numpy()
p("V3 semestri (%): " + ", ".join(f"{d:%Y-%m} {(v / q - 1) * 100:+.1f}" for d, v, q in zip(sem.index, sem.to_numpy(), prev)))
top3 = {(y["ticker"], y["i0"]) for y in sorted(tk3, key=lambda y: -y["pnl"])[:3]}
p(f"V3 senza i 3 migliori: {R.evaluate([c for c in cs3 if (c['ticker'], c['i0']) not in top3], s, e)[0]['fin']} $")
p(f"V3 senza il 2021 (dal 2022-01-01): {R.evaluate(R.cs_for('short', {}, R.K_W32, '2022-01-01', e), '2022-01-01', e)[0]['fin']} $")
p(f"V3 OOS: WR {R.evaluate(R.cs_for('short', {}, R.K_W32, *R.PER['OOS']), *R.PER['OOS'])[0]['wr']}%")
# long dello scanner: simulazione per moneta senza liste (posizione W3.2 della moneta al 24/11)
import engine as E
p("\nLONG DELLO SCANNER (simulazione W3.2 per moneta senza liste, dati al 24/11, costi 0,2%/lato, esito per quota con la size di W3.2)")
for t in ("JST", "PIEVERSE", "NIGHT", "BEAMX", "SENT"):
    f = R.feats(t)[0]; o = E.simulate(f, start=R.CM.loc[t, "completa_da"], all_perp=True); tr = o["open"]
    if not tr: p(f"  {t}: nessuna posizione aperta"); continue
    tr = dict(tr, d=abs(tr["entry_px"] - tr["stop0"]) / tr["entry_px"], ticker=t, btc=0, vol90=0, sett=0, dates=f.index[tr["i_entry"]:tr["i_exit"] + 1])
    y = R.cands([tr], R.K_W32)[0]; prev_l = [z for z in o["trades"] if z["side"] == "long"]
    p(f"  {t}: in posizione long W3.2 dal {tr['entry']} (segnale {tr['signal']}) a {tr['entry_px']:.5g}, chiusura 24/11 {f.close.iloc[-1]:.5g} "
      f"({(f.close.iloc[-1] / tr['entry_px'] - 1) * 100:+.1f}%), stop iniziale −{tr['d'] * 100:.0f}%, esito per quota {y['pnl'] * 100:+.1f}%; long chiusi in passato {len(prev_l)}, vinti {sum(z['pnl'] > 0 for z in prev_l)}")
p("  Nota: JST è in posizione W3.2 da luglio; nello scanner del 22/11 compare fra i long ma non è un ingresso nuovo.")
(R.D / "out_extra.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))
