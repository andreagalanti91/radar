# Rapporto ufficiale W3.2 · BTC · 25/11/2026

**Numero ufficiale da citare.** W3.2 su BTC, 10.000 $ a 1x, costi e funding inclusi, **dal 01/01/2021 al 24/11/2026:
84.820 $** (+748%, CAGR +43,7%), calo massimo giornaliero **−21,1%**, **13 operazioni chiuse, 12 vinte (92,3%)**, più lo short aperto
dal 16/11/2026 (+8,1% sul capitale). **Dal 01/01/2018: 242.755 $**, calo massimo **−37,3%**, **22 operazioni chiuse, 17 vinte (77,3%)**,
più lo stesso short aperto. BTC comprato e tenuto: 20.645 $ dal 2021 (calo −76,6%) e 43.536 $ dal 2018 (calo −81,2%).

**Sintesi.** I numeri diversi che circolano vengono tutti dallo stesso motore e dagli stessi segnali. Cambiano tre cose: la data
di partenza (da flat o con una posizione ereditata), la data di fine dei dati (la posizione aperta cambia valore ogni giorno) e il
conteggio della posizione aperta (insieme alle chiuse o a parte). Con la convenzione qui sotto il "dal 2021" coincide con la pagina
Movimenti del tool (84.820 $, −21,1%). L'unica differenza è il conteggio delle operazioni: il tool scrive "14 trade, 92,9%" perché
conta lo short aperto come operazione vinta. W3.2 non è stata modificata.

**Convenzione unica.** Motore `radar.weekly.simulate` invariato. Dati del repo (`data/` del ramo pubblicato, aggiornamento del
25/11/2026). Prima del 01/09/2019 si usa la storia lunga della ricerca (`research/p2_nuovi/data/f_long.csv.gz`: prezzi identici,
flusso stimato dal CVD spot fino all'11/04/2020). Regola: `data/` da solo dove basta (periodi dal 2021, identici al tool) e storia
lunga solo dove `data/` non arriva. Ogni periodo parte **da flat** il primo giorno indicato, con 10.000 $. **Data di fine: 24/11/2026**
(ultimo giorno chiuso). La posizione aperta è valutata all'ultima chiusura, come nel tool, ed è contata a parte. Calo massimo sulla
chiusura giornaliera. Sharpe sui rendimenti giornalieri ×√365, senza tasso privo di rischio. Rendimento/calo = CAGR / |calo massimo|.
Script e tabelle: `research/w32_ufficiale/` (`w32_ufficiale.py`, `tab_*.csv`, `risultati.txt`).

## 1. Regole di W3.2 in breve
- Candele settimanali chiuse (W-SUN): decisione la domenica alle 00:00 UTC, esecuzione il lunedì all'apertura.
- **Long**: chiusura sopra la SMA40 settimanale, EMA20 in salita, chiusura sopra la EMA21, flusso perp > 0. Nei trend vecchi
  (≥ 16 settimane sopra la SMA40) serve anche il MACD(8,21,5) sopra il segnale e sopra lo zero.
- **Short**: chiusura sotto la SMA40, SMA40 in calo su 4 settimane, EMA20 in calo, chiusura sotto la EMA21, flusso perp < 0.
- Flusso = media del pf14z degli ultimi 3 giorni disponibili alla decisione (lo stesso dato dal vivo e nel backtest).
- **Uscite**: trailing 2,5 ATR settimanali a cricchetto, chiusura settimanale oltre la EMA21, distribuzione (long: funding 7 giorni
  > 0,0009 e flusso < 0; short: funding < −0,0003 e flusso > 0).
- Long in spot 1x, short in perp. Esposizione con tetto di rischio: al massimo il 25% del capitale perso allo stop iniziale
  (2,5 ATR). Il resto resta in liquidità.

## 2. Risultati per periodo (10.000 $ da flat, fino al 24/11/2026)
| | Dal 2018 | **Dal 2021 (tool)** | 2018–2020 | 2021–2023 | 2024–oggi | Ultimi 12 mesi¹ |
|---|---|---|---|---|---|---|
| Capitale finale | 242.755 $ | **84.820 $** | 25.142 $ | 33.477 $ | 25.388 $ | 12.264 $ |
| Rendimento totale | +2.328% | **+748%** | +151% | +235% | +154% | +22,6% |
| Rendimento annuo | +43,1% | **+43,7%** | +36,0% | +49,6% | +37,9% | +22,7% |
| Calo massimo | −37,3% | **−21,1%** | −37,3% | −19,3% | −21,1% | −18,3% |
| Sharpe | 1,30 | 1,34 | 1,11 | 1,47 | 1,20 | 0,81 |
| Rendimento/calo | 1,16 | 2,07 | 0,97 | 2,57 | 1,79 | 1,24 |
| Operazioni chiuse + aperta | 22 + short | **13 + short** | 8 + long² | 6 + long³ | 6 + short | 3 + short |
| Win rate (chiuse) | 77,3% (17/22) | **92,3% (12/13)** | 50% (4/8) | 100% (6/6) | 83,3% (5/6) | 66,7% (2/3) |
| Profit factor | 8,3 | 59,2 | 2,6 | nessuna perdita | 24,9 | 4,3 |
| Guadagno medio | +25,8% | +20,2% | +31,1% | +16,7% | +20,4% | +8,8% |
| Perdita media | −10,6% | −4,1% | −12,2% | – | −4,1% | −4,1% |
| Migliore | +71,5% | +52,2% | +51,1% | +52,2% | +42,2% | +11,9% |
| Peggiore | −25,1% | −4,1% | −25,1% | +1,0% | −4,1% | −4,1% |
| Perdite di fila (max) | 2 | 1 | 2 | 0 | 1 | 1 |
| Durata media | 78 gg | 99 gg | 51 gg | 93 gg | 110 gg | 104 gg |
| Tempo in posizione | 53% | 60% | 39% | 57% | 63% | 88% |
| Win rate long | 75% (12/16) | 89% (8/9) | 50% (3/6) | 100% (4/4) | 75% (3/4) | 0% (0/1) |
| Win rate short | 83% (5/6) | 100% (4/4) | 50% (1/2) | 100% (2/2) | 100% (2/2) | 100% (2/2) |
| *BTC tenuto: finale* | *43.536 $* | *20.645 $* | *21.046 $* | *14.590 $* | *14.122 $* | *6.762 $* |
| *BTC tenuto: annuo / calo* | *+18,0% / −81,2%* | *+13,1% / −76,6%* | *+28,1% / −81,2%* | *+13,4% / −76,6%* | *+12,6% / −53,0%* | *−32,4% / −39,5%* |
| *BTC tenuto: Sharpe* | *0,58* | *0,50* | *0,72* | *0,52* | *0,49* | *−0,66* |

Risultati delle operazioni in % del capitale all'ingresso. ¹ Dal 25/11/2025, da flat. ² Long del 14/12/2020 aperto al 31/12/2020
(+50,6%). ³ Long del 23/10/2023 aperto al 31/12/2023 (+40,7%). BTC tenuto: comprato all'apertura del primo giorno, con commissione
e slittamento del motore.

## 3. Anno per anno (serie continua dal 01/01/2018)
| Anno | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026⁴ |
|---|---|---|---|---|---|---|---|---|---|
| W3.2 | −9,7% | +41,5% | +96,7% | +118,4% | +19,4% | +46,1% | +102,7% | +4,9% | +19,2% |
| Calo nell'anno | −30,4% | −19,5% | −23,3% | −13,8% | −13,4% | −18,3% | −11,9% | −18,7% | −18,3% |
| Operazioni chiuse nell'anno | 2 | 2 | 4 | 4 | 1 | 2 | 2 | 2 | 3 (+ short aperto) |
| BTC tenuto | −73,1% | +94,3% | +302,0% | +59,8% | −64,2% | +155,6% | +121,3% | −6,3% | −31,7% |

⁴ Fino al 24/11. Partendo da flat il 01/01/2021 (tool) il 2021 vale **+91,9%** invece di +118,4%: la serie continua eredita il long
del 14/12/2020, chiuso il 04/01/2021 a +71,5%. Dal 2022 le due serie coincidono. Il calo massimo dal 2018 (−37,3%) va dal 2018 al
2019 e quindi supera il calo del solo 2018.

## 4. Tutte le operazioni dal 2018 (serie continua)
| # | Verso | Segnale | Entrata | Uscita | Prezzo in | Prezzo out | Esposizione | Sul capitale | Motivo d'uscita |
|---|---|---|---|---|---|---|---|---|---|
| 1 | long | 07/01/2018 | 08/01/2018 | 16/01/2018 | 16.235 | 9.654 | 0,62 | −25,1% | trailing 2,5 ATR |
| 2 | long | 29/04/2018 | 30/04/2018 | 14/05/2018 | 9.426 | 8.671 | 0,40 | −3,3% | EMA 21 |
| 3 | short | 14/10/2018 | 15/10/2018 | 02/04/2019 | 6.333 | 4.551 | 0,59 | +16,6% | trailing 2,5 ATR |
| 4 | long | 12/05/2019 | 13/05/2019 | 27/06/2019 | 6.975 | 10.559 | 1,00 | +51,1% | trailing 2,5 ATR |
| 5 | long | 09/02/2020 | 10/02/2020 | 17/02/2020 | 10.162 | 9.901 | 0,93 | −2,6% | distribuzione |
| 6 | short | 15/03/2020 | 16/03/2020 | 27/04/2020 | 5.355 | 7.701 | 0,40 | −17,9% | EMA 21 |
| 7 | long | 03/05/2020 | 04/05/2020 | 03/08/2020 | 8.903 | 11.060 | 0,67 | +16,0% | distribuzione |
| 8 | long | 25/10/2020 | 26/10/2020 | 23/11/2020 | 13.043 | 18.395 | 1,00 | +40,8% | distribuzione |
| 9 | long | 13/12/2020 | 14/12/2020 | 04/01/2021 | 19.194 | 32.967 | 1,00 | +71,5% | distribuzione |
| 10 | long | 31/01/2021 | 01/02/2021 | 22/02/2021 | 33.126 | 57.355 | 0,72 | +52,1% | distribuzione |
| 11 | long | 01/08/2021 | 02/08/2021 | 27/09/2021 | 39.890 | 43.118 | 0,54 | +4,3% | EMA 21 |
| 12 | long | 03/10/2021 | 04/10/2021 | 08/11/2021 | 48.248 | 63.210 | 0,68 | +20,9% | distribuzione |
| 13 | short | 02/01/2022 | 03/01/2022 | 28/03/2022 | 47.239 | 46.875 | 0,64 | +1,0% | EMA 21 |
| 14 | short | 14/08/2022 | 15/08/2022 | 16/01/2023 | 24.281 | 20.894 | 0,56 | +8,3% | EMA 21 |
| 15 | long | 22/01/2023 | 23/01/2023 | 17/08/2023 | 22.729 | 25.966 | 0,95 | +13,3% | trailing 2,5 ATR |
| 16 | long | 22/10/2023 | 23/10/2023 | 01/01/2024 | 30.022 | 42.241 | 1,00 | +40,5% | distribuzione |
| 17 | long | 11/02/2024 | 12/02/2024 | 11/03/2024 | 48.348 | 68.887 | 1,00 | +42,2% | distribuzione |
| 18 | long | 22/09/2024 | 23/09/2024 | 26/02/2025 | 63.642 | 85.256 | 0,91 | +30,8% | trailing 2,5 ATR |
| 19 | long | 27/04/2025 | 28/04/2025 | 10/10/2025 | 93.843 | 104.715 | 0,99 | +11,3% | trailing 2,5 ATR |
| 20 | short | 30/11/2025 | 01/12/2025 | 27/04/2026 | 90.270 | 78.736 | 0,89 | +11,9% | EMA 21 |
| 21 | short | 24/05/2026 | 25/05/2026 | 20/08/2026 | 76.988 | 73.287 | 1,00 | +5,7% | trailing 2,5 ATR |
| 22 | long | 23/08/2026 | 24/08/2026 | 09/11/2026 | 77.812 | 74.777 | 1,00 | −4,1% | EMA 21 |
| – | **short** | 15/11/2026 | 16/11/2026 | **aperta** | 65.286 | 59.832 (24/11) | 0,97 | **+8,1%** | posizione aperta |

Long in spot, short in perp. Le operazioni 10–22 più la posizione aperta sono le "13 + 1" del tool (dal 2021). Nella serie del
tool partita da flat l'operazione 10 vale +52,2% (+52,1% qui): il riscaldamento dell'ATR parte da date diverse, vedi il riquadro.

## 5. Posizione aperta oggi (dati al 24/11/2026)
| | |
|---|---|
| Verso | **short** in perp, segnale del 15/11, entrata 16/11/2026 a **65.286 $**, esposizione 0,972 |
| Stop iniziale | 82.163 $ (rischio allo stop 25% del capitale) |
| Valore attuale | chiusura 59.832 $: −8,4% sul prezzo, **+8,1% sul capitale** (10.000 $ → 10.809 $ sulla posizione) |
| Uscita in perdita oggi | **trailing 75.764 $** (controllo ogni ora): −15,8% sul capitale. **Chiusura settimanale sopra la EMA21 74.273 $**: −13,6% |
| Uscita in profitto | **distribuzione** (funding 7 giorni < −0,0003 e flusso > 0, alla domenica): oggi non attiva (funding +0,00001, flusso −1,20). Uscendo al prezzo di oggi: circa +8,0% |
| Quando il trailing va in profitto | se il minimo di chiusura scende sotto 47.788 $ (−20,1% dal prezzo attuale) |
| Quando la EMA21 va in profitto | quando scende sotto l'entrata (65.286 $): circa 11 settimane a prezzo fermo |

Livelli dal blocco descrittivo del tool (`weekly.exits_block`), ricalcolati su 10.000 $. Oggi il tool li mostra sul capitale reale.

## 6. Robustezza essenziale (stessa convenzione)
| | Dal 2018 | Dal 2021 |
|---|---|---|
| Con tutte le operazioni (aperta inclusa) | 242.755 $ | 84.820 $ |
| Senza la migliore | 141.561 $ (×14,2) | 55.731 $ (×5,6) |
| Senza le 3 migliori | 61.569 $ (×6,2) | 27.895 $ (×2,8) |

Prodotto dei risultati sul capitale delle singole operazioni. Le migliori sono +71,5%, +52,1% e +51,1% dal 2018, e +52,2%, +42,2% e
+40,5% dal 2021.

| Rischio allo stop iniziale | Dal 2018: finale / calo | Dal 2021: finale / calo / rend./calo | 2018–2020: finale / calo |
|---|---|---|---|
| 10% (W3.1) | 50.802 $ / −19,2% | 28.070 $ / −9,8% / 1,96 | 16.734 $ / −19,2% |
| **25% (W3.2)** | **242.755 $ / −37,3%** | **84.820 $ / −21,1% / 2,07** | **25.142 $ / −37,3%** |
| 30% | 269.115 $ / −40,4% | 100.568 $ / −21,8% / 2,20 | 23.509 $ / −40,4% |

Stesse operazioni e stesso win rate a ogni livello di rischio: cambia solo l'esposizione. Dal 2021 nessuna operazione ha perso più
del 4,1%. Nel gennaio 2018 la prima operazione ha perso il 25,1%, cioè il rischio massimo previsto, uscendo sul trailing dopo
una settimana. Il calo dal 2018 riflette questo episodio.

## 7. Perché altri numeri sono diversi
> | Numero visto | Da dove viene | Con la convenzione ufficiale |
> |---|---|---|
> | **84.820 $**, −21,1% (tool, Movimenti) | dal 2021 da flat, dati al 24/11 | **coincide** (ufficiale) |
> | 14 trade, 92,9% vinti (tool) | lo short aperto è contato come operazione chiusa e vinta (`weekly.metrics`) | 13 chiuse, 92,3% (12/13) + 1 aperta |
> | 84.360 $ | stesso calcolo con dati al 21/11 (short a +7,5%, il 24/11 a +8,1%) | 84.820 $ al 24/11 |
> | 83.129 $ | stesso calcolo al 22/11 (BTC in rialzo: lo short scende a +5,9%) | idem |
> | 78.474 $ (13 trade) | dati congelati al 15/11, prima dell'ingresso short del 16/11 | idem |
> | 84.789 $ | dal 2021 calcolato sul frame lungo: l'ATR parte dal 2014 invece che dal 2019 (scarto 0,04%) | si usa il frame del tool |
> | 94.693 $ | tratto "dal 2021" della serie continua dal 2018 (al 21/11): parte con il long del 14/12/2020 già aperto, chiuso il 04/01/2021 a +71,5% | 96.554 $ al 24/11; non è il "dal 2021 da flat" |
> | 224.593 $ | serie continua dal 2018, dati al 15/11 | 242.755 $ al 24/11 |
> | 241.439 $ | serie continua dal 2018, dati al 21/11 (research/v1_confronto) | 242.755 $ al 24/11 |
> | 212.098 / 209.002 $ | backtest dell'utente: 2018–20 chiuso d'ufficio al 31/12/2020 (long a +50,4% invece di +71,5%), poi dal 2021 da flat; al 21/11 e al 22/11 | −12% rispetto alla serie continua; non si usa |
> | 25.142 $ (2018–2020) | da flat il 01/01/2018, long aperto valutato al 31/12/2020 | coincide (25.117 $ chiudendolo con la commissione) |
> | 22 operazioni, 77% (RAPPORTO v1) | dal 2018, solo chiuse | coincide: 22 chiuse, 77,3% + 1 aperta |
> | 23 operazioni (v1 README) | dal 2018, chiuse + aperta | 22 + 1 |

**Numero ufficiale da citare**: "W3.2 BTC, 10.000 $ dal 01/01/2021 al 24/11/2026: 84.820 $, calo massimo −21,1%, 13 operazioni
chiuse con il 92,3% vinte, più uno short aperto. Dal 01/01/2018: 242.755 $, calo −37,3%, 22 chiuse con il 77,3% vinte, più lo
short aperto." Il finale cambia ogni giorno finché lo short è aperto: va sempre citato con la data di fine. Il calo massimo, le
operazioni chiuse e il win rate cambiano solo quando un'operazione si chiude.

**Limiti.** Le regole di W3.2 sono state decise nel novembre 2026 guardando tutto il 2018–26: il dato fuori campione vero sono solo
le settimane dal vivo (dal 02/11/2026). Nel 2018 e fino all'11/04/2020 il flusso è stimato dal CVD spot, e fino al 2019 il funding
è assente (0). Con 13 e 22 operazioni le percentuali sono stime grossolane.
