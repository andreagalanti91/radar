# STATO · Rapporto ufficiale W3.2 · avviato 25/11/2026

Stato: COMPLETATO (25/11/2026) · correzioni del tool applicate (13 chiuse + 1 aperta, rendimento annuo/DD 2,07), suite 522 test, deploy fatto

## Prompt originale
"Il rapporto dice 22 operazioni poi sul tool nei movimenti vedo 14. Ti chiedo di assestarmi i dati. Voglio un rapporto
ufficiale della strategia 3.2. Vedo discrepanza dei dati." (con screenshot del tool, Movimenti, e del RAPPORTO.md v1)

## Diagnosi
Periodi diversi (tool dal 01/01/2021 con posizione aperta; rapporto v1 "dal 2018" solo chiuse) e convenzioni diverse fra
studi (partenza da flat o con posizione già aperta; data di fine dei dati).

## Decisioni (convenzione ufficiale)
- Motore: radar.weekly.simulate invariato; dati del repo (data/ + storia lunga della ricerca prima del 09/2019).
- Partenza da flat il 1° gennaio dell'anno indicato; capitale 10.000 $; posizione aperta valutata all'ultima chiusura, contata
  a parte; data di fine unica e dichiarata.
- Numeri del tool = numeri del rapporto (dal 2021). W3.2 non si tocca.

## Prossima azione
Agente: rapporto ufficiale `memoria/01-strategia/RAPPORTO-W32.md` + controllo coerenza tool/README/memoria.

## Fatto
memoria/01-strategia/RAPPORTO-W32.md (numeri ufficiali al 24/11/2026: dal 2018 242.755 $, DD −37,3%, 22 chiuse + 1 aperta, WR 77,3%; dal 2021 84.820 $ = tool, 13 chiuse + 1 aperta, WR 92,3%); research/w32_ufficiale/; README.md e W3.2.md allineati; nota in STRATEGIE.md.

## Proposte per la dashboard (da approvare)
1. Movimenti: "13 chiuse (92,3%) + 1 aperta" invece di "14 trade, 92,9%" (weekly.metrics conta l'aperta come chiusa; anche la nota in dashboard_template.html ~riga 1444).
2. "Rend./DD" mostra rendimento totale/DD (35,4): usare CAGR/DD (2,07) o cambiare etichetta.
