# Stato — Swing settimanali su supporti/resistenze (TP e SL strutturali)

**Stato:** COMPLETATO
**Ultimo aggiornamento:** 2026-11-22
**Modello / effort usati:** Fable 5.2 · high (regia e motore), agente radar-review per la revisione critica

## Prompt originale
> Leggi memoria/00-inizia-qui/README.md e poi, in ordine, le cartelle memoria/01…05. Poi leggi stato/STATO-ingressi-uscite.md e
> research/ingressi_uscite/README.md. Ti chiedo di fare revisione della strategia. Approfondisci e analizza nuova strategia swing
> settimanali, gestione TP e SL basato su supporti/resistenze. Analizza te la versione migliore che performi di più. Capitale di
> partenza 10.000$. Apprendi, analizza, impara dai propri sbagli, fai revisioni critiche. Avvia ciclo di analisi. Fammi domande se
> hai dubbi.

Risposte successive dell'utente: "70/30 capitale. Nuova strategia facciamo solo i test su un file .md. Solo btc. Cogli gli swing non
importa il tempo seguendo la migliore strategia. Voglio la migliore strategia per rendere profittevole il mio trading. Sono un trader
settimanale, mantengo le posizioni per breve tempo. Colgo le occasioni, non mantengo posizioni per lungo tempo. Accolgo uno stoploss
del 5/10% prendo profitto in TP 10/15% oppure di più se c'è forza nel movimento. Analizza la migliore strategia." Poi: "Procedi".

## Scelte dell'utente
- Capitale 70/30: interpretato come 70% W3.1 + 30% swing su 10.000 $ (comunicato all'utente, non corretto). Anche swing sola su 10.000 $.
- Solo studio: W3.1 e tool non si toccano; risultati in un file .md in research/swing_sr/.
- Solo BTC. Durata libera. Stop 5–10% dal prezzo, oltre il livello; TP +10/15% o di più se c'è forza (parte con trailing).
- Default non contestati: criterio CAGR/DD con DD ≤ 20%; nessuna leva (long spot 1x, short perp 1x); autonomia A su PREREG e
  secondo ciclo; se una variante supera i criteri ci si ferma e si presentano i dati.

## Piano
- [x] 1. Apprendimento (lezioni 75–77, 95, 97, 105, nuova_strategia, n2)
- [x] 2. Motore + conteggio eventi (senza rendimenti) — conteggi.txt
- [x] 3. PREREG.md committato da solo — 854ebff
- [x] 4. Backtest: scelta su 2014–2020, giudizio su 2021–2026, placebo, vicini, portafoglio 70/30 — S* NON VALIDA
- [x] 5. Revisione critica (radar-review) — nessun errore bloccante, verdetto confermato
- [x] 6. Secondo ciclo — NON eseguito (nessun errore, nessuna ipotesi nuova; revisore contrario)
- [x] 7. README.md, lezione 106, memoria/02-ricerca/INDICE.md, commit e push su claude/swing-strategy-review-5g3jul

## Risultati e file prodotti
- Step 1: già provato e respinto: S/R su giornaliero/settimanale come segnale (75–77, 97), struttura S/R long-only settimanale
  (nuova_strategia N1: 7.726 $), swing 2–3 giorni a tempo (95), TP/stop in ATR su W3.1 (105). Non provato: swing giornalieri su
  livelli settimanali con stop 5–10% oltre il livello, TP 10/15%/livello successivo, parte con trailing, filtro di regime W3.1.

- Step 4 (`python3 research/swing_sr/sw_run.py`, ~30 s → risultati.txt, griglia.csv, trade_scelta.csv, placebo.csv, equity.csv):
  S* = X/R1/LS/SS/TSR (rottura, regime di prezzo, long+short, stop strutturale puro, TP al livello successivo): 2014–20 56.194 $,
  2021+ 10.000 → 5.626 $, DD −55,8%, 88 trade, WR 23%, PF 0,83; criteri 1–5 tutti falliti; placebo p 0,43. Solo 3/405 ammissibili
  nel 2014–20, nessuna positiva nel 2021+. Correlazione di rango 2014–20 / 2021+: −0,02. 111/405 positive nel 2021+, 0 sopra
  buy & hold (22.594 $) e W3.1 (27.190 $). Solo il regime R2 (condizioni W3.1) è positivo in mediana (10.618 $, 70% positive);
  la migliore a posteriori B/R2/LS/SF/TSR fa 21.611 $ (DD −19,6%, 20 trade) ma ingressi a caso nello stesso regime fanno
  16.487 $ in mediana (p 0,23). 70/30 con S*: 20.721 $; con la migliore a posteriori 25.516 $ (C/DD 1,784 < 1,903 di W3.1).

## Decisioni prese
- Lavoro svolto nella sessione principale invece che con due sottoagenti di ricerca: un solo motore, un solo file, meno rischio
  di divergenze (in autonomia). La revisione critica resta a un agente separato.
- Scelta dei parametri sul 2014–2020 e giudizio unico sul 2021–2026 (come research/nuova_strategia), per non scegliere sugli
  stessi dati su cui si giudica (in autonomia).

## Problemi aperti
- nessuno

## Come riprendere
**Prossima azione:** nessuna. Report: `research/swing_sr/README.md`. W3.1 e tool invariati.
Riepilogo finale: strategia swing non valida; 70/30 peggiora W3.1; lezione 106 in RESEARCH.md.
