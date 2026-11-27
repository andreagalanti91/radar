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
# long dello scanner (posizioni aperte al 24/11)
p("\nLONG DELLO SCANNER (posizione aperta nella simulazione per moneta, V1 senza lista dell'anno: vista di oggi)")
o = R.tradeset(s, e, {}, "both", view="oggi")
for t in ("JST", "PIEVERSE", "NIGHT", "BEAMX", "SENT"):
    x = [y for y in o if y["ticker"] == t and y["reason"] == "open"]
    if x:
        y = R.cands(x, R.K_W32)[0]; p(f"  {t}: ingresso {y['entry']} {y['side']}, d {y['d']:.2f}, esito per quota al 24/11 {y['pnl'] * 100:+.1f}%, BTC {'con' if y['btc'] > 0 else 'contro' if y['btc'] < 0 else 'flat'}")
    else: p(f"  {t}: nessuna posizione aperta nella vista (segnale del 22/11: ingresso lunedì 23/11, dati al 24/11)" )
(R.D / "out_extra.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))
