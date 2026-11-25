"""Compone README.md da README_testo.md (testo scritto a mano) e dalle uscite dei calcoli (out_tabelle.txt, out_q*.txt, csv)."""
import re
import pandas as pd
from pathlib import Path
H = Path(__file__).resolve().parent
T = (H / "out_tabelle.txt").read_text()
sec = {}
for blk in T.split("\n### ")[1:]:
    title, body = blk.split("\n", 1); sec[title.strip()] = body.split("\n\n")[0].strip()
def find(key): return next(v for k, v in sec.items() if k.startswith(key))
def para(prefix): return next(l for l in T.splitlines() if l.startswith(prefix))
def it(x): return f"{x:,.0f}".replace(",", ".")

rep = {}
for k in ("Q1 · top 20 crypto di oggi", "Q1 · migliori 15 e peggiori 5", "Q2 · top 20 crypto al 29/12/2019", "Q2 · portafogli equipesati dal 01/06/2020",
          "Q3 · top 10 azioni di oggi", "Q3 · top 10 azioni a fine 2019", "Q4 · cancello BTC"):
    full = next(t for t in sec if t.startswith(k)); rep[k] = f"### {full}\n" + sec[full]
rep["Q1_SUMMARY"] = para("Q1 valutabili (79)").split(": ", 1)[1] + "  \nSolo top 200 di oggi: " + para("valutabili top 200 oggi").split(": ", 1)[1]
rep["Q2_SUMMARY"] = para("Q2 valutabili top 200 2020").split(": ", 1)[1]
rep["BREVI"] = para("Brevi").split(": ", 1)[1] + "; solo prezzo " + para("Solo prezzo").split(": ", 1)[1]
rep["Q3_SUMMARY"] = "\n- " + para("Azioni prezzo") + "\n- " + para("Azioni cmf20") + "\n- " + para("cmf20 contro")
rep["Q4_TXT"] = "\n".join("- " + l for l in (H / "out_q4.txt").read_text().strip().splitlines())
q5 = (H / "out_q5.txt").read_text()
rep["Q5_TXT"] = ("```\n" + "\n".join(l for l in q5.splitlines() if not l.startswith("(c)")).strip() + "\n```\n"
                 "Mediane di classe; `oos_15` = asset che passano i criteri 1–5 sul solo OOS. Il CAGR/DD quasi non cambia con il rischio "
                 "(lezione 101): la scelta fra le righe a 3,0 ATRw si decide al quarto decimale. Il DD sì: per le altcoin il rischio 10% porta "
                 "il DD mediano OOS da −52% a −25%, ma il rendimento scende con lui.")
d6 = pd.read_csv(H / "risultati_q6.csv")
rep["Q6_TAB"] = "\n".join(f"| {r.da} | {r.portafoglio} ({r.asset}) | {it(r.fin)} | {r.cagr}% | {r.dd} | {r.cd} | {r.trade} | {r.trade_anno} |" for r in d6.itertuples())
q8 = (H / "out_q8.txt").read_text().strip().splitlines(); rows = []
for l in q8:
    m = re.match(r"(\d{4}): idonee (\d+), scelte (\d+): (.*?) \| (.*)", l)
    if m:
        parts = dict(re.findall(r"(screener|BTC \+ ETH|tutte le idonee|solo BTC) ([^·]+)", m.group(5)))
        rows.append(f"| {m.group(1)} | {m.group(2)} | {m.group(4)} | {parts['screener'].strip()} | {parts['BTC + ETH'].strip()} | {parts['tutte le idonee'].strip()} | {parts['solo BTC'].strip()} |")
rep["Q8_TAB"] = "\n".join(rows)
comp = "\n".join(q8[q8.index(next(l for l in q8 if l.startswith("Conto composto"))):])
tq = pd.read_csv(H / "trades_q7.csv")
def ttab(name):
    x = tq[tq.asset == name]
    return ("| Segnale | Ingresso | Verso | Prezzo in | Esposizione | Uscita | Prezzo out | Motivo | Mossa del prezzo | Risultato sul capitale |\n|---|---|---|---|---|---|---|---|---|---|\n"
            + "\n".join(f"| {r.segnale} | {r.ingresso} | {r.verso} | {r.px_in:g} | {r.esposizione:.2f} | {r.uscita} | {r.px_out:g} | {r.motivo} | {r.mov_prezzo_pct:+.1f}% | {r.pnl_pct:+.1f}% |" for r in x.itertuples()))
rep["Q8_TXT"] = "```\n" + comp + "\n```\n" + (H / "q8_proposta.md").read_text()
rep["Q7_TXT"] = (H / "q7_testo.md").read_text().replace("{SOL_TRADES}", ttab("SOL")).replace("{TAO_TRADES}", ttab("TAO"))
txt = (H / "README_testo.md").read_text()
for k, v in rep.items():
    pat = "{" + k + "}"
    if pat not in txt:
        pat = next(m for m in re.findall(r"\{[^{}\n]+\}", txt) if k.startswith(m[1:-1]) or m[1:-1].startswith(k))
    txt = txt.replace(pat, v)
left = re.findall(r"^\{[^{}\n]+\}$", txt, flags=re.M)
assert not left, left
(H / "README.md").write_text(txt); print("README.md", len(txt.splitlines()), "righe")
