# Cono di probabilità a 30 giorni per BTC (volatilità, non direzione) · 23/11/2026 · PASSA un metodo su tre, di misura

**Verdetto (preregistrato: PREREG.md, commit 17b9a49, committato da solo prima di ogni risultato).**
Un cono costruito solo dalla volatilità corrente è calibrato fuori campione dal 2018: il metodo **(b) bootstrap a blocchi con
deriva storica** rispetta il criterio in tutti e tre i periodi. Gli altri due lo mancano di pochissimo (copertura del 50% nel
2024–26: 56,3% e 56,7% contro il limite di 56%). I tre metodi sono statisticamente indistinguibili: la scelta di (b) è quella
imposta dal criterio, non una prova che la deriva serva. **La card "Fra 30 giorni" si fa, con (b).**

| Metodo | Copertura 80% · 2018–20 / 2021–23 / 2024–26 | Copertura 50% · stessi periodi | Errore di calibrazione del tocco | Brier (rif. 0,1799) | Esito |
|---|---|---|---|---|---|
| a · bootstrap senza deriva | 78,8% / 79,4% / 78,4% | 52,3% / 50,0% / **56,3%** | 4,0 punti | 0,1753 (skill +2,6%) | NON calibrato (50% fuori di 0,3 punti) |
| **b · bootstrap con deriva storica** | 78,7% / 78,4% / 77,5% | 50,6% / 51,5% / 54,7% | 4,6 punti | 0,1761 (skill +2,1%) | **CALIBRATO · scelto** |
| c · lognormale | 75,6% / 78,6% / 77,9% | 51,6% / 50,4% / **56,7%** | 4,9 punti | 0,1754 (skill +2,5%) | NON calibrato |

Criterio: 80% fra 74% e 86% e 50% fra 44% e 56% in ciascun periodo; errore di calibrazione medio del tocco ≤ 5 punti (2018–26).
Metodo (b) sull'intero 2018–26 (3.211 giorni, 108 osservazioni non sovrapposte): **intervallo 80% centrato nel 78,2% dei casi**
(±4,0; 77,8% sulle sole non sovrapposte), intervallo 50% nel 52,2% (±4,8). Errore standard per periodo ≈ 7–8 punti.

## Cosa dice e cosa non dice
- **Dice** quanto può muoversi BTC in 30 giorni con la volatilità di oggi: due intervalli e la probabilità di toccare un livello.
- **Non dice la direzione.** La deriva di (b) è la crescita media storica di BTC dal 2014 (circa +3% in 30 giorni), uguale ogni
  giorno: non è un segnale. Con la deriva gli esiti cadono più spesso SOTTO l'intervallo 50% (26,6%) che sopra (21,2%); senza
  deriva (a) succede il contrario (20,0% / 27,2%): la deriva "vera" del periodo sta in mezzo e non è stimabile.
- **Il guadagno sulla frequenza storica è piccolo.** Brier skill del tocco +2,1% (IC 95% a blocchi −1,1% / +4,8%: comprende lo
  zero); nel 2018–20 il cono fa peggio del riferimento (−2,2%), nel 2021–23 +2,9%, nel 2024–26 +7,3%. Il cono è onesto
  (calibrato), non un vantaggio operativo.

## Affidabilità delle probabilità di tocco, metodo (b), 2018–26 (6 livelli insieme, decili)
| Prevista | 3% | 9% | 14% | 21% | 27% | 34% | 41% | 49% | 57% | 67% |
|---|---|---|---|---|---|---|---|---|---|---|
| Osservata | 7% | 11% | 12% | 17% | 23% | 27% | 30% | 47% | 53% | 58% |

Le probabilità alte sono un po' gonfiate (67% previsto → 58% osservato), le più basse un po' strette (3% → 7%: code grasse).
Per livello (prevista media → osservata): +10% 59,5 → 55,2 · −10% 47,2 → 45,1 · +20% 34,5 → 27,8 · −20% 21,9 → 20,4 ·
+30% 20,4 → 15,3 · −30% 9,2 → 7,5. Con la deriva i tocchi verso l'alto sono sovrastimati di 4–7 punti; quelli verso il basso
sono quasi giusti. Errore di calibrazione per periodo: 6,9 / 7,0 / 4,2 punti (il criterio vale sull'intero campione).

## Addendum esplorativo: deriva condizionata al flusso perp (ADDENDUM.md, commit 3049ee9) · NON adottata
Eseguito dopo aver visto i metodi base, su richiesta della regia. Deriva = rendimento medio passato a 30 giorni nello stesso
stato del flusso (pf14z, 3 giorni, ritardo di 1 giorno come W3.2), stimato walk-forward; stesse estrazioni casuali di (b).

| 2021–26 | Copertura 80% 21–23 / 24–26 | Copertura 50% 21–23 / 24–26 | Brier 21–23 / 24–26 | Δ Brier contro b (IC 95%) | Esito |
|---|---|---|---|---|---|
| b (base) | 78,2% / 78,1% | 51,2% / 55,9% | 0,1766 / 0,1404 | – | – |
| d1 · segno del flusso | 79,2% / 79,3% | 51,4% / **58,5%** | 0,1752 / 0,1384 | −0,0017 (−0,0045 / +0,0014) | NON adottata |
| d2 · segno e forza | 78,2% / 78,8% | 53,6% / **58,0%** | 0,1766 / 0,1381 | −0,0011 (−0,0048 / +0,0029) | NON adottata |

Il Brier migliora di un soffio in entrambi i periodi (1%, intervallo che comprende lo zero) ma la copertura del 50% nel 2024–26
esce dalla fascia. Nella card il flusso resta una riga descrittiva ("in vendita / in acquisto"), senza effetto sulle
probabilità. Liquidazioni: non testabili (16 mesi di dati reali su un mercato minore); solo riga descrittiva, marcata come stima.

## Metodo
Dati `research/p2_nuovi/data/f_long.csv.gz` (OHLC giornaliero 2014 → 15/11/2026). Per ogni giorno dal 01/01/2018 al 16/10/2026,
solo con i dati precedenti: σ² = ½ media(r², 30 giorni) + ½ media(r², 365 giorni); rendimenti storici (chiusura, massimo, minimo
sul giorno prima) divisi per la σ del giorno precedente, centrati, ricampionati in 3 blocchi di 10 giorni (2.000 cammini, seme
20261123) e riscalati alla σ di oggi; (b) aggiunge la media storica del rendimento giornaliero. Esito chiusura: prezzo a 30
giorni; esito tocco: massimo/minimo giornalieri entro 30 giorni a ±10/20/30%. Riferimento del Brier: frequenza storica
incondizionata dello stesso evento sulle finestre concluse prima di t. File: `c30_run.py` → `risultati.txt`, `copertura.csv`,
`brier.csv`, `affidabilita.csv`, `previsioni.csv.gz`; `c30_flusso.py` → `risultati_flusso.txt`.

## Limiti
- **Potenza**: ~36 osservazioni indipendenti per periodo. La fascia del criterio (±6 punti) è più stretta dell'errore standard
  (7–8): (b) passa e (a), (c) falliscono per differenze di decimi. Il dato solido è che tutti e tre stanno a 75–79% e 50–57%.
- **L'intervallo 80% è un po' stretto**: 78% e non 80% (in tutti i periodi sotto 80).
- **Code grasse e salti**: i movimenti estremi sono più frequenti del previsto nelle probabilità basse (3% → 7%).
- **Cambi di regime della volatilità**: σ è fissata al giorno della previsione; un crollo o un evento che la raddoppia nei 30
  giorni non è previsto (nel 2018–20, con marzo 2020, il cono non batte la frequenza storica).
- **Tocco** misurato su massimi/minimi giornalieri di una fonte: lo spike di una singola borsa può differire.
- **Nessun uso su W3.2**: il cono non cambia stop, trailing o decisioni.

## Uso nel tool
`radar/cone.py` (`report["cone"]`, card "Fra 30 giorni" in Oggi): stesso metodo (b) con 10.000 cammini e la storia 2014–08/2019
da `radar/cone_seed.csv`; `tests/test_cone.py` verifica che il modulo riproduca gli intervalli dello studio. Ogni previsione è
registrata in `data/cone_log.csv` e confrontata con il prezzo dopo 30 giorni: la copertura dal vivo si leggerà lì.
