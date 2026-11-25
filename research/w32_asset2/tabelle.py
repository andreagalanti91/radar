"""Tabelle markdown per il README (da risultati_*.csv, eq_*.csv.gz). Scrive out_tabelle.txt. Nessun calcolo nuovo di strategia,
salvo p di Holm aggiustati e portafogli equipesati di Q2 (dalle equity già salvate)."""
import numpy as np, pandas as pd
import lib as L

out = []
def p(s=""): out.append(s)
def fmt(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)): return "–"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def padj(ps):
    s = ps.dropna().sort_values(); m = len(s); adj, run = {}, 0.0
    for i, (k, v) in enumerate(s.items()): run = max(run, min(1.0, (m - i) * v)); adj[k] = run
    return ps.index.map(lambda k: adj.get(k, np.nan))

HDR = "| Asset | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
def line(r, name, op):
    return (f"| {name} | {r.inizio} | {fmt(r.fin)} | {fmt(r.cagr, 1)}% | {fmt(r.dd, 1)} | {fmt(r.n)} | {fmt(r.wr)}% | {fmt(r.bh_fin)} · {fmt(r.bh_dd, 1)} · {fmt(r.bh_cd, 2)} | "
            f"{r.is_ret:+.0f}% / {r.oos_ret:+.0f}%{'' if r.split == 'IS/OOS' else ' (metà)'} | {r.falliti} | {'sì' if r.conferma is True else ('no' if r.conferma is False else '–')} | "
            f"{fmt(r.p, 4) if not pd.isna(r.p) else '–'} | {fmt(r.p_holm, 3) if not pd.isna(r.p_holm) else '–'} | {op} |")

# ---------------- crypto Q1/Q2
d = pd.read_csv(L.HERE / "risultati_crypto.csv"); v = d[d.classe == "valutabile"].copy()
for q, sel in (("q1", v), ("q2", v[v.rank_2020.notna()])):
    s = sel.set_index("ticker").p; d[f"p_holm_{q}"] = d.ticker.map(dict(zip(s.index, padj(s))))
cu = L.CU[L.CU.classe != "esclusa"]
def ctab(col, title, q):
    p(f"\n### {title}\n" + HDR)
    for x in cu.sort_values(col).dropna(subset=[col]).head(20).itertuples():
        r = d[d.ticker == x.ticker]; op = f"{'sì' if x.bitget_perp else 'no'}/{'sì' if x.okx_perp else 'no'}"
        name = f"{int(getattr(x, col))}. {x.simbolo}"
        if not len(r) or pd.isna(r.iloc[0].get("fin")):
            p(f"| {name} | – | {x.classe}: nessun dato W3.2 | | | | | | | | | | | {op} |"); continue
        r = r.iloc[0].copy(); r["p_holm"] = r[f"p_holm_{q}"]
        if r.versione == "solo prezzo" or x.classe == "breve": name += f" ({x.classe})"
        if r.versione == "solo prezzo": r["conferma"] = None
        p(line(r, name, op))
ctab("rank_oggi", "Q1 · top 20 crypto di oggi (CoinGecko 25/11/2026, dopo le esclusioni)", "q1")
ctab("rank_2020", "Q2 · top 20 crypto al 29/12/2019 (CMC, dopo le esclusioni)", "q2")
for q, sel in (("Q1 valutabili (79)", v), ("Q2 valutabili top 200 2020 (55)", v[v.rank_2020.notna()]), ("valutabili top 200 oggi (50)", v[v.rank_oggi.notna()])):
    a = sel[sel.ticker != "BTC"]
    p(f"\n{q}: altcoin {len(a)} · finale quartili {fmt(a.fin.quantile(.25))} / {fmt(a.fin.median())} / {fmt(a.fin.quantile(.75))} · DD mediano {fmt(a.dd.median(), 1)}"
      f" · WR mediano {fmt(a.wr.median())}% · CAGR/DD mediano {fmt(a.cd.median(), 2)} (B&H {fmt(a.bh_cd.median(), 2)}, B&H finale mediano {fmt(a.bh_fin.median())})"
      f" · c1 {int(a.c1.sum())}, c2 {int(a.c2.sum())}, c3 {int(a.c3.sum())}, c4 {int(a.c4.sum())}, c5 {int(a.c5.sum())} · 1–5 {int(a.passa15.sum())}"
      f" · 1–5+conferma {int((a.passa15 & a.conferma.fillna(False).astype(bool)).sum())} · p<0,05 {int((a.p < .05).sum())} · sopra 10.000 $ {int((a.fin > 10000).sum())}")
p("\n### Q1 · migliori 15 e peggiori 5 (79 valutabili, per CAGR/DD)\n" + HDR)
vv = d[d.classe == "valutabile"].sort_values("cd", ascending=False)
for part in (vv.head(15), vv.tail(5)):
    for r in part.itertuples():
        r2 = pd.Series(r._asdict()); r2["p_holm"] = r2["p_holm_q1"]
        p(line(r2, r.simbolo, f"{'sì' if r.bitget_perp else 'no'}/{'sì' if r.okx_perp else 'no'}"))
    p("| … |" + " |" * 13)
b = d[(d.classe == "breve") & d.fin.notna()]
p(f"\nBrevi (< 3 anni, descrittive): {len(b)} simulate · passano 1–5: {list(b[b.passa15.fillna(False).astype(bool)].simbolo)} · finale mediano {fmt(b.fin.median())}, DD mediano {fmt(b.dd.median(), 1)}")
s = d[d.versione == "solo prezzo"]
p(f"Solo prezzo (descrittive): {len(s)} · passano 1–5: {list(s[s.passa15.fillna(False).astype(bool)].simbolo)} · finale mediano {fmt(s.fin.median())}, DD mediano {fmt(s.dd.median(), 1)}")

# Q2 portafogli equipesati dal 2020-06-01
eq = pd.read_csv(L.HERE / "eq_crypto.csv.gz", index_col=0, parse_dates=True)
p("\n### Q2 · portafogli equipesati dal 01/06/2020 (capitali separati, liquidità prima dell'inizio)\n| Portafoglio | N | Finale | CAGR | DD | CAGR/DD |\n|---|---|---|---|---|---|")
for name, sel in (("valutabili top 200 2020", v[v.rank_2020.notna()]), ("valutabili top 200 oggi", v[v.rank_oggi.notna()]), ("tutte le 79 valutabili", v)):
    for kind in ("w", "bh"):
        m, _ = L.port([eq[f"{t}|{kind}"].dropna() for t in sel.ticker], "2020-06-01")
        p(f"| {'W3.2' if kind == 'w' else 'B&H'} {name} | {m['n']} | {fmt(m['fin'])} | {fmt(m['cagr'], 1)}% | {fmt(m['dd'], 1)} | {fmt(m['cd'], 2)} |")
for t in ("BTC", "ETH"):
    m, _ = L.port([eq[f"{t}|w"].dropna()], "2020-06-01"); p(f"| W3.2 solo {t} | 1 | {fmt(m['fin'])} | {fmt(m['cagr'], 1)}% | {fmt(m['dd'], 1)} | {fmt(m['cd'], 2)} |")

# ---------------- Q4
q4 = pd.read_csv(L.HERE / "risultati_q4.csv"); q4["p_holm"] = padj(q4.set_index("ticker").p).values if False else q4.ticker.map(dict(zip(q4.ticker, padj(q4.set_index("ticker").p))))
p("\n### Q4 · cancello BTC: top 20 oggi e 2020 (altcoin valutabili) + migliori per CAGR/DD\n" + HDR)
core = set(cu.sort_values("rank_oggi").head(20).ticker) | set(cu.sort_values("rank_2020").head(20).ticker)
x = q4[q4.ticker.isin(core) | (q4.cd >= q4.cd.quantile(0.85))].sort_values("cd", ascending=False)
for r in x.itertuples():
    r2 = pd.Series(r._asdict()); p(line(r2, r.simbolo + ("" if r.ticker in core else " (fuori nucleo)"), f"{'sì' if r.bitget_perp else 'no'}/{'sì' if r.okx_perp else 'no'}"))

# ---------------- Q3 azioni
a = pd.read_csv(L.HERE / "risultati_azioni.csv")
for vname in ("prezzo", "cmf20"):
    m = a.variante == vname; a.loc[m, "p_holm"] = a.loc[m, "yahoo"].map(dict(zip(a[m].yahoo, padj(a[m].set_index("yahoo").p))))
au = L.AU
def atab(col, title):
    p(f"\n### {title}\n" + HDR.replace("| Asset |", "| Titolo · variante |"))
    for x in au.sort_values(col).dropna(subset=[col]).head(10).itertuples():
        op = f"{'sì' if x.bitget == 'si' else 'no'}/{'sì' if x.okx == 'si' else 'no'}"
        r = a[a.yahoo == x.yahoo]
        if not len(r): p(f"| {int(getattr(x, col))}. {x.name} | – | meno di un anno di dati: non valutato | | | | | | | | | | | {op} |"); continue
        for rr in r.itertuples():
            p(line(pd.Series(rr._asdict()), f"{int(getattr(x, col))}. {x.name} · {rr.variante}", op))
atab("rank_today", "Q3 · top 10 azioni di oggi (CompaniesMarketcap 25/11/2026)")
atab("rank_2020", "Q3 · top 10 azioni a fine 2019")
for vname in ("prezzo", "cmf20"):
    s = a[a.variante == vname]
    p(f"\nAzioni {vname}: {len(s)} titoli · finale quartili {fmt(s.fin.quantile(.25))} / {fmt(s.fin.median())} / {fmt(s.fin.quantile(.75))} · DD mediano {fmt(s.dd.median(), 1)}"
      f" · WR mediano {fmt(s.wr.median())}% · CAGR/DD mediano {fmt(s.cd.median(), 2)} (B&H {fmt(s.bh_cd.median(), 2)}) · c1 {int(s.c1.sum())}, c2 {int(s.c2.sum())}, c3 {int(s.c3.sum())},"
      f" c4 {int(s.c4.sum())}, c5 {int(s.c5.sum())} · 1–5 {int(s.passa15.sum())} · p<0,05 {int((s.p < .05).sum())} · migliori per CAGR/DD: "
      + ", ".join(f"{r.name} {fmt(r.cd, 2)} (B&H {fmt(r.bh_cd, 2)}, DD {fmt(r.dd, 1)}, WR {fmt(r.wr)}%, falliti {r.falliti})" for r in s.sort_values("cd", ascending=False).head(6).itertuples()))
pa, pc = a[a.variante == "prezzo"].set_index("yahoo"), a[a.variante == "cmf20"].set_index("yahoo")
p(f"cmf20 contro solo prezzo (stesso titolo): CAGR/DD più alto in {int((pc.cd > pa.cd).sum())}/124, DD meno profondo in {int((pc.dd > pa.dd).sum())}/124, "
  f"mediana della differenza di CAGR/DD {fmt((pc.cd - pa.cd).median(), 2)}")
(L.HERE / "out_tabelle.txt").write_text("\n".join(out) + "\n"); print("\n".join(out))
