"""Controlli prima dei risultati: (a) BTC dal 2021 = 78.474 $; (b) ETH dal 2021 = 34.760 $ (w32_top100);
(d) ma_lib.s1_sim con il filtro di azioni/count.py riproduce azioni/counts.csv (tutte le varianti, ingressi per titolo).
(c) è in q5.py (copia del motore con le costanti sostituite). Scrive out_checks.txt."""
import pandas as pd
import lib as L

out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); out.append(s)

for t, ref in (("BTC", 78474), ("ETH", 34760)):
    f = L.C.feats(t, pd.Timestamp("2026-11-10")); o = L.W.simulate(f, start="2021-01-01"); fin = round(float(o["equity"].iloc[-1]))
    p(f"({'a' if t == 'BTC' else 'b'}) {t} 2021-01-01 -> 2026-11-10, dati nuovi: {fin} $ (riferimento {ref}) ->", "OK" if fin == ref else "DIVERSO",
      f"; trade {len(o['trades']) + (1 if o['open'] else 0)}")
    if fin != ref:
        g = pd.read_csv(L.ROOT / "research/w32_top100/data" / f"{t}_perp.csv.gz", index_col=0, parse_dates=True)
        h = pd.read_csv(L.HERE / "crypto/data" / f"{t}_perp.csv.gz", index_col=0, parse_dates=True)
        j = g.join(h, rsuffix="_n", how="inner"); d = j[(j["tbv"] - j["tbv_n"]).abs() > 1e-6]
        p("   giorni con taker buy diverso fra w32_top100 e dati nuovi:", len(d), list(d.index.date[:5]))
    f2 = L.C.feats(t); o2 = L.W.simulate(f2, start="2021-01-01")
    p(f"    {t} 2021-01-01 -> 2026-11-24: {round(float(o2['equity'].iloc[-1]))} $")

# (d) conteggi azioni
c = pd.read_csv(L.HERE / "azioni" / "counts.csv"); CUT = "2026-11-20"; bad = []; nchk = 0
var = {"prezzo": None, **{k: k for k in L.FLOWS}}
for sym in c.yahoo.unique():
    f = L.aload(sym); f = f[f.index <= CUT]; wb, fw = L.abars(f); S = L.astart(f)
    for v, col in var.items():
        o = L.asim(f, wb, fw, col, S, CUT); n = len(o["trades"]) + (1 if o["open"] else 0)
        ref = c[(c.yahoo == sym) & (c.variant == v)].entries.iloc[0]; nchk += 1
        if n != ref: bad.append((sym, v, n, ref))
p(f"(d) ma_lib.s1_sim riproduce azioni/counts.csv: {nchk - len(bad)}/{nchk} righe identiche (titolo × variante, linee primarie e USA)", bad[:10])
(L.HERE / "out_checks.txt").write_text("\n".join(out) + "\n")
