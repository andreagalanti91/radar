# Strategie: versioni e studi a confronto (aggiornato al 22/11/2026)

Tutti i numeri: BTC, 10.000 $ dal 01/01/2021 al 15/11/2026, 1x, costi inclusi, salvo dove indicato.

## Versioni della strategia principale (stessi segnali settimanali)

| Versione | Periodo d'uso | Rischio allo stop | 10.000 $ → | Drawdown | Trade | Win rate | 2018–20 (DD) | Stato |
|---|---|---|---|---|---|---|---|---|
| W2 + MACD, backtest originale | — | nessun tetto sui long | 118.628 $ | −22,7% | 14 | 93% | — | **non realizzabile** (look-ahead sul flusso) |
| W2 + MACD "come dal vivo" | 02–11/11 | nessun tetto sui long | ~103.000 $ | −22,7% | 14 | 93% | ~20.000 $ (−48%) | superata |
| W3 | 12–19/11 | 25% | 78.474 $ | −21,1% | 13 | 92% | 25.142 $ (−37,3%) | = W3.2 |
| W3.1 | 19–22/11 | 10% | 27.190 $ | −9,8% | 13 | 92% | 16.734 $ (−19,2%) | superata |
| **W3.2** | **dal 22/11** | **25%** | **78.474 $** | **−21,1%** | **13** | **92%** | **25.142 $ (−37,3%)** | **in uso** |
| **W3.2 su ETH** (capitale separato, 10.000 $) | **dal 22/11** | **25%** | **34.760 $** (al 10/11) | **−27,5%** | **15** | **60%** | — | **in uso** |

## Livelli di rischio provati (segnali W3)

| Rischio allo stop | 10.000 $ → | DD 2021+ | 2018–20 | DD 2018–20 |
|---|---|---|---|---|
| 10% | 27.190 $ | −9,8% | 16.734 $ | −19,2% |
| 15% | 42.630 $ | −13,9% | 20.621 $ | −26,3% |
| 20% | 61.054 $ | −17,7% | 24.725 $ | −32,3% |
| **25%** | **78.474 $** | **−21,1%** | **25.142 $** | **−37,3%** |
| 30% | 92.842 $ | −21,8% | 23.509 $ | −40,4% |

## Strategie alternative studiate (nessuna adottata)

| Studio | Data | Risultato | Esito | Lezione | Cartella |
|---|---|---|---|---|---|
| Swing breve su S/R settimanali, stop 5–10%, TP 10–15% (BTC) | 22/11 | 5.626 $, DD −55,8%, WR 23% | non valida; 70/30 con W3.1 peggiora | 106 | research/swing_sr |
| Stessa strategia su 15 asset (SPY, QQQ, oro, argento, petrolio, 10 azioni) | 22/11 | 0/15 validi, mediana 17,6k contro 70,2k buy & hold | non funziona | 107 | research/swing_sr_multi |
| Sentiment da order book + liquidazioni | 22/11 | 0/14 test, regola 10k → 6,9k in 16 giorni | descrittivo (pagina Book) | 108 | research/book_sentiment |
| TP +10/12,5/15% con rientro, trailing 1,5 ATR dopo +10% (su W3.2) | 22/11 | 43–56k $ contro 78,5k | nessuna adottata | 109 | research/tp_rientro |
| DCA, uscite a scaglioni, TP, stop, distribuzione su W3.1 | 22/11 | migliore variante sotto W3.1 | nessuna adottata | 105 | research/ingressi_uscite |
| W3.2 su ETH, SOL, S&P 500, Nasdaq, Dow, DAX, FTSE MIB, Nikkei, Russell, Euro Stoxx | 22/11 | ETH 34,8k (DD −27,5%); SOL 52,5k (DD −39,8%); indici 6,7–15,5k, tutti sotto il buy & hold | solo BTC (ETH al limite); ETH poi adottato con capitale separato per scelta dell'utente (22/11) | 110 | research/w32_multi |
| W3.2 sulle top 100 crypto (27 altcoin con perp e ≥ 3 anni) | 22/11 | passa solo ETH; mediana altcoin 8.344 $, DD −65% | solo BTC ed ETH | 111 | research/w32_top100 |
| W3.1 solo prezzo su 13 asset | 22/11 | 0/13 | solo BTC | 104 | research/multi_asset |
| Order book e liquidazioni come supporto | 22/11 | nessun supporto (15 giorni) | rifare 20/12 e 03/2027 | 105 | research/book_liq |
| Market maker (assorbimento, compressione) | 18/11 | perde dopo i costi | respinto | 98 | research/mm_assorbimento |
| Swing 2–3 giorni, macro, probabilità | 15/11 | 0/32, 0/5.790 | respinti | 95–97 | research/notte_1511 |
| Nuova strategia settimanale con volumi e S/R | 11/11 | 13.234 $, DD −56% | non funziona | — | research/nuova_strategia |
| Liquidazioni (calamita, fasce, squeeze, mappa v2) | 07–13/11 | nessun vantaggio | respinte | 72, 81, 92, 93 | research/liq_* |

Riferimento: tenere BTC dal 2021 = 22.594 $, drawdown −76,6%.
