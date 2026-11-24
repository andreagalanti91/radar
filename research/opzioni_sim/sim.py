"""Simulazione: quanto investire per opzione con budget totale 50.000 $, dal 2021.
Fonte: research/opzioni_import/storico_prezzi_veri.csv (prezzi veri Deribit; mult = valore finale / premio pagato).
Regole invariate (7 regole dello studio); cambia solo la spesa per operazione. Descrittivo: la quota NON va scelta qui."""
import csv, os
QUI = os.path.dirname(os.path.abspath(__file__))
R = [x for x in csv.DictReader(open(os.path.join(QUI, "..", "opzioni_import", "storico_prezzi_veri.csv"))) if x["entra"] >= "2021"]
B = 50000.0

def run(mode, v, rows):
    cap, peak, dd, worst, streak, ws, wins, spent = B, B, 0.0, 0.0, 0.0, 0.0, 0, 0.0
    for x in rows:
        stake = min(cap, v if mode == "fisso" else cap * v)
        pl = stake * (float(x["mult"]) - 1)
        spent += stake; cap += pl; wins += pl > 0
        worst = min(worst, pl / (cap - pl))
        streak = streak + pl if pl < 0 else 0.0; ws = min(ws, streak)
        peak = max(peak, cap); dd = min(dd, cap / peak - 1)
    return cap, dd, worst, ws, wins, spent

def w32(frac, rows):
    cap, peak, dd = B, B, 0.0
    for x in rows:
        cap *= 1 + float(x["w32"]) * frac; peak = max(peak, cap); dd = min(dd, cap / peak - 1)
    return cap, dd

def tab(rows, tit):
    out = [f"### {tit} ({len(rows)} operazioni)", "",
           "| Spesa per opzione | Finale | Guadagno | DD fra operazioni | Perdita peggiore | Serie peggiore di perdite | In guadagno |",
           "|---|---|---|---|---|---|---|"]
    for lab, m, v in [("1.000 $ fissi", "fisso", 1000), ("1.500 $ fissi", "fisso", 1500), ("2.000 $ fissi", "fisso", 2000),
                      ("2.500 $ fissi", "fisso", 2500), ("5.000 $ fissi", "fisso", 5000),
                      ("3% del conto", "pct", .03), ("4% del conto", "pct", .04), ("5% del conto", "pct", .05),
                      ("7,5% del conto", "pct", .075), ("10% del conto", "pct", .10)]:
        c, dd, w, ws, wi, sp = run(m, v, rows)
        out.append(f"| {lab} | {c:,.0f} $ | {c-B:+,.0f} $ | {dd*100:.1f}% | {w*100:.1f}% | {ws:,.0f} $ | {wi}/{len(rows)} |")
    for lab, f in [("W3.2 a metà dimensione", .5), ("W3.2 intera (rischio 25%)", 1.0)]:
        c, dd = w32(f, rows)
        out.append(f"| *{lab}* | {c:,.0f} $ | {c-B:+,.0f} $ | {dd*100:.1f}% | — | — | — |")
    return "\n".join(out).replace(",", ".").replace("2021. ", "2021, ")

chiuse = [x for x in R if x["esce"] != "aperta"]
print(tab(chiuse, "Dal 2021, operazioni chiuse")); print()
print(tab(chiuse[:-3] if False else [x for x in chiuse if x["entra"] < "2024"], "Solo 2021–2023")); print()
print(tab([x for x in chiuse if x["entra"] >= "2024"], "Solo 2024–2026")); print()
s = sorted(chiuse, key=lambda x: -float(x["mult"]))[3:]
print(tab([x for x in chiuse if x in s], "Dal 2021 senza le 3 operazioni migliori")); print()
print("mult:", [round(float(x["mult"]), 2) for x in chiuse])
