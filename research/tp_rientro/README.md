# Take profit a +10/15% e rientro su W3.2 · BTC · 22/11/2026

**Verdetto: nessuna variante batte W3.2.** 0/8 varianti preregistrate (PREREG 69dc968) superano i criteri. Il TP a +10/15% con
rientro porta 10.000 $ a 43–50k $ invece di 78.474 $, con DD uguale o peggiore. W3.2 resta invariata; nessuna modifica a radar/.

## Il trade short aperto (ingresso 16/11/2026 a 65.286 $, esposizione 0,97x, dati fino al 21/11)
- Minimo di BTC 55.130 $ il 21/11: guadagno massimo del movimento +15,6% (circa +15% sul capitale). Miglior chiusura
  58.952 $ (20/11, +9,7%). Ultima chiusura 60.216 $: +7,8% sul prezzo, +7,5% sul capitale.
- Trailing: 58.952 + 2,5 × 6.725 (ATR settimanale) = **75.764 $**, ancora sopra l'ingresso (stop iniziale 82.163 $).
- Perché non è uscito: W3.2 non ha take profit. Lo stop segue la miglior chiusura giornaliera (non il minimo) a 2,5 ATR
  settimanali, circa il 26% dal prezzo attuale. Le altre uscite (EMA21, distribuzione) si valutano solo alla chiusura della
  domenica. Un minimo intragiornaliero a −15% non cambia nulla per costruzione.

## La "costante": quanto guadagno W3.2 restituisce (MFE, `mfe.csv`)
| | Trade | Toccano +10% / +15% | MFE mediano | Uscita mediana | Restituito mediano | Quota restituita mediana |
|---|---|---|---|---|---|---|
| 2021+ | 13 | 13 / 12 | +36,3% | +13,9% | 20,8 punti | 62% |
| 2018–20 | 9 | 6 / 6 | +36,2% | +24,2% | 14,3 punti | 49% (vincenti 33%) |

Dal 2021 **tutti i 13 trade** hanno toccato +10% e 12 su 13 hanno toccato +15%. W3.2 restituisce in mediana circa il 60% del
massimo guadagno: somma dei MFE 525 punti, somma delle uscite 284 punti. Il prezzo di questa restituzione sono i trend lunghi:
2021-01 (MFE +76%, uscita +73%), 2023-10 (+49% / +41%), 2024-02 (+45% / +43%), 2024-09 (+72% / +34%). Un TP a +10/15% li avrebbe
chiusi tutti a +12%.

## Risultati (10.000 $, costi e rischio 25% come W3.2; IS e OOS ripartono da 10.000 $)
| Variante | Finale 2021+ | CAGR | DD | CAGR/DD | Trade | WR | Peggiore | IS fin. / CDD | OOS fin. / CDD | 2018–20 fin. / DD / CDD |
|---|---|---|---|---|---|---|---|---|---|---|
| **W3.2 (in uso)** | **78.474** | 42,0 | −21,1 | 1,990 | 13 | 92,3 | −4,1 | 33.477 / 2,574 | 23.488 / 1,639 | 25.142 / −37,3 / 0,966 |
| V1 TP 10% tutto, rientro A | 49.826 | 31,5 | −21,2 | 1,483 | 38 | 81,6 | −14,6 | 18.397 / 1,162 | 27.138 / 1,959 | 16.579 / −30,4 / 0,604 |
| V2 TP 12,5% tutto, A | 48.999 | 31,1 | −24,6 | 1,263 | 36 | 75,0 | −15,6 | 28.235 / 1,683 | 17.389 / 0,982 | 21.642 / −30,4 / 0,965 |
| V3 TP 15% tutto, A | 48.084 | 30,7 | −24,6 | 1,246 | 33 | 69,7 | −15,6 | 24.029 / 1,382 | 20.050 / 1,268 | 23.281 / −30,4 / 1,070 |
| V4 TP 10% metà | 48.683 | 30,9 | −14,3 | 2,160 | 13 | 100 | +2,8 | 23.825 / 3,536 | 20.457 / 1,975 | 17.275 / −30,4 / 0,657 |
| V5 TP 12,5% metà | 50.583 | 31,8 | −18,0 | 1,772 | 13 | 92,3 | −4,1 | 25.185 / 2,012 | 20.107 / 1,933 | 18.132 / −30,4 / 0,722 |
| V6 TP 15% metà | 56.280 | 34,2 | −18,0 | 1,906 | 13 | 92,3 | −4,1 | 26.612 / 2,153 | 21.172 / 2,107 | 19.025 / −30,4 / 0,786 |
| V7 TP 12,5% tutto, rientro B 5% | 42.724 | 28,1 | −24,6 | 1,140 | 38 | 76,3 | −15,9 | 24.726 / 1,434 | 17.314 / 0,993 | 25.104 / −30,4 / 1,181 |
| V8 trailing 1,5 ATRw dopo +10% | 52.553 | 32,7 | −32,0 | 1,021 | 19 | 73,7 | −15,6 | 27.293 / 1,530 | 19.294 / 0,804 | 23.443 / −31,3 / 1,051 |
| Buy & hold | 22.549 | 14,9 | −76,6 | 0,194 | — | — | — | 14.590 / 0,175 | 15.425 / 0,307 | 21.046 / −81,2 / 0,347 |

## Criteri (dettaglio in `risultati.txt`)
- C1 (IS e OOS migliori): solo V4. C2 (2018–20 non peggiore): V3, V7, V8. C3 (DD entro −30%): tutte tranne V8.
- C4 (non dipende da ≤ 2 trade): nessuna, perché la somma dei Δ per trade è negativa già con tutti i trade (da −33 a −61 punti log).
- Permutazione dei segni: p da 0,82 a 1,00 (soglia di Holm 0,006). Placebo con livello casuale 5–30%: p da 0,34 a 1,00.
  Il livello 10–15% non è migliore di un livello qualsiasi.
- Vicini: B 2,5% / 7,5% danno 46k / 33k $. Trailing k 1,25 dà 76k $ (DD −27,9%, OOS 1,115); k 1,75 e attivazione 7,5% / 12,5%
  danno 44–51k $ con DD oltre −31%.
- V4 (metà a +10%) è il caso più vicino: WR 100%, DD −14,3%, CAGR/DD 2,16. Però rende 30.000 $ in meno, peggiora il 2018–20
  (17k contro 25k) e il placebo non la distingue (p 0,34). Equivale a ridurre il rischio: W3 al 15% fa 42.630 $ con DD −13,9%
  (CAGR/DD ≈ 2,0).

## Perché il TP con rientro perde
Il TP incassa +12,4% (circa +7/12% sul capitale). Il rientro avviene però una o più settimane dopo, a prezzi peggiori e con un
nuovo stop a 2,5 ATR: i rientri finali dei trend chiudono a −9/−16% (2022-11 short −14%, 2025-01 long −16%, 2026-06 short −12%).
Il win rate sale (75–82%), ma le perdite diventano circa 4 volte più grandi della peggiore di W3.2 (−4,1%). Il rientro B
(entro 5% dall'uscita) aggiunge 6 rientri, di cui 3 in perdita (fino a −16%).

## Risposta all'utente
La costante c'è: ogni trade W3.2 dal 2021 è arrivato almeno a +10% (mediana +36%) e la strategia ne restituisce in mediana il
60% prima di uscire. È il costo dei pochi trend da +40/+75% che fanno quasi tutto il rendimento. Uscire a +10/15% e rientrare
alle condizioni riduce il capitale finale da 78k a 43–50k $ e non riduce il drawdown. L'uscita a metà a +10% abbassa il DD
(−14%) e porta il win rate al 100%, ma rende come W3 con rischio 15%: è una scelta di rischio, non un vantaggio. Per lo short
in corso la regola resta il trailing a 75.764 $ e la verifica alla chiusura settimanale.

## Metodo e limiti
Motore `tp_engine.py` (copia di radar.weekly con TP, rientro e trailing stretto), verificato al centesimo contro radar.weekly in
4 periodi e in 5 configurazioni degeneri. Dati congelati p2_nuovi fino al 15/11 (2018–20 su dati proxy). Il trade aperto è
ricostruito con i dati del tool fino al 21/11. Barre giornaliere: il TP e lo stop nello stesso giorno valgono come stop
(prudente). Esecuzione: `python3 tp_run.py` (~4 min) → `risultati.txt`, `varianti.csv`, `mfe.csv`, `trade_varianti.csv`,
`placebo.csv`. Nessuna deviazione dal PREREG.

## Lezione proposta per RESEARCH.md
**Lezione 109**: su W3.2 il take profit a +10/12,5/15% del prezzo d'ingresso, totale con rientro alla decisione settimanale
(A o B entro 5%) o a metà, e il trailing 1,5 ATRw dopo +10%, non migliorano nulla: 0/8 varianti passano (PREREG 69dc968);
finale 43–56k $ contro 78k, permutazione p ≥ 0,82, placebo sul livello p ≥ 0,34. Dal 2021 tutti i 13 trade toccano +10% (MFE
mediano +36%) e W3.2 restituisce in mediana il 62% del massimo guadagno: è il costo dei trend lunghi, non un difetto da
correggere. I rientri dopo il TP comprano tardi e perdono −9/−16%: il win rate sale, la perdita peggiore quadruplica. La metà a
+10% (WR 100%, DD −14%) equivale a rischiare meno (W3 al 15%). Non riproporre TP fissi in % sui trade settimanali.
